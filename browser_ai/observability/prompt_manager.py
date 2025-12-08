"""
Prompt Management for Browser.AI

Centralized prompt registry with versioning, A/B testing, and Laminar integration.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from lmnr import Laminar

logger = logging.getLogger(__name__)


class PromptType(str, Enum):
    """Types of prompts in the system"""

    SYSTEM = "system"
    PLANNER = "planner"
    ACTION = "action"
    EXTRACTION = "extraction"
    VALIDATION = "validation"


@dataclass
class PromptVersion:
    """A versioned prompt template"""

    prompt_id: str
    version: str
    prompt_type: PromptType
    template: str
    variables: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True

    def render(self, **kwargs) -> str:
        """Render the prompt with provided variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise ValueError(
                f"Missing required variable '{missing_var}' for prompt {self.prompt_id} v{self.version}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            "prompt_id": self.prompt_id,
            "version": self.version,
            "prompt_type": self.prompt_type.value,
            "template": self.template,
            "variables": self.variables,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "is_active": self.is_active,
        }


class PromptManager:
    """
    Centralized prompt management with versioning and A/B testing

    Features:
    - Version control for all prompts
    - A/B testing support
    - Laminar integration for tracking
    - Rollback capabilities
    """

    def __init__(self):
        self.prompts: Dict[str, Dict[str, PromptVersion]] = {}
        self._initialize_default_prompts()

    def _initialize_default_prompts(self):
        """Initialize default prompts from existing system"""
        # System prompt
        self.register_prompt(
            prompt_id="agent_system",
            version="1.0.0",
            prompt_type=PromptType.SYSTEM,
            template="""You are an AI agent controlling a web browser to complete tasks.
Task: {task}

You must respond with valid JSON containing your current state assessment and next actions.
Follow the action descriptions carefully and only use available actions.

Available actions:
{action_description}

Maximum actions per step: {max_actions_per_step}""",
            variables=["task", "action_description", "max_actions_per_step"],
            metadata={"description": "Main agent system prompt"},
        )

        # Planner prompt
        self.register_prompt(
            prompt_id="agent_planner",
            version="1.0.0",
            prompt_type=PromptType.PLANNER,
            template="""Based on the current task progress, create a high-level plan for the next steps.

Task: {task}
Current Progress: {progress}
Current Page: {current_url}

Provide a structured plan with:
1. Immediate next goal
2. Expected challenges
3. Alternative approaches
4. Success criteria""",
            variables=["task", "progress", "current_url"],
            metadata={"description": "Strategic planning prompt"},
        )

        # Extraction prompt
        self.register_prompt(
            prompt_id="content_extraction",
            version="1.0.0",
            prompt_type=PromptType.EXTRACTION,
            template="""Extract the following information from the page content:

Goal: {goal}

Page Content:
{page_content}

Provide the extracted information in a structured format.""",
            variables=["goal", "page_content"],
            metadata={"description": "Content extraction prompt"},
        )

    def register_prompt(
        self,
        prompt_id: str,
        version: str,
        prompt_type: PromptType,
        template: str,
        variables: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        is_active: bool = True,
    ) -> PromptVersion:
        """Register a new prompt version"""
        if prompt_id not in self.prompts:
            self.prompts[prompt_id] = {}

        prompt_version = PromptVersion(
            prompt_id=prompt_id,
            version=version,
            prompt_type=prompt_type,
            template=template,
            variables=variables,
            metadata=metadata or {},
            is_active=is_active,
        )

        self.prompts[prompt_id][version] = prompt_version

        logger.info(f"Registered prompt {prompt_id} v{version}")

        # Track in Laminar
        Laminar.event(
            name="prompt_registered",
            attributes={
                "prompt_id": prompt_id,
                "version": version,
                "type": prompt_type.value,
            },
        )

        return prompt_version

    def get_prompt(
        self,
        prompt_id: str,
        version: Optional[str] = None,
    ) -> PromptVersion:
        """Get a specific prompt version or the latest active version"""
        if prompt_id not in self.prompts:
            raise ValueError(f"Prompt {prompt_id} not found")

        if version:
            if version not in self.prompts[prompt_id]:
                raise ValueError(f"Prompt {prompt_id} v{version} not found")
            return self.prompts[prompt_id][version]

        # Get latest active version
        active_versions = [p for p in self.prompts[prompt_id].values() if p.is_active]

        if not active_versions:
            raise ValueError(f"No active versions found for prompt {prompt_id}")

        # Sort by version and return latest
        return sorted(active_versions, key=lambda p: p.version, reverse=True)[0]

    def render_prompt(
        self, prompt_id: str, version: Optional[str] = None, **kwargs
    ) -> str:
        """Get and render a prompt with variables"""
        prompt = self.get_prompt(prompt_id, version)
        rendered = prompt.render(**kwargs)

        # Track usage in Laminar
        Laminar.event(
            name="prompt_rendered",
            value={
                "prompt_id": prompt_id,
                "version": prompt.version,
                "type": prompt.prompt_type.value,
            },
        )

        return rendered

    def list_versions(self, prompt_id: str) -> List[PromptVersion]:
        """List all versions of a prompt"""
        if prompt_id not in self.prompts:
            return []
        return list(self.prompts[prompt_id].values())

    def activate_version(self, prompt_id: str, version: str):
        """Activate a specific prompt version and deactivate others"""
        if prompt_id not in self.prompts or version not in self.prompts[prompt_id]:
            raise ValueError(f"Prompt {prompt_id} v{version} not found")

        # Deactivate all versions
        for v in self.prompts[prompt_id].values():
            v.is_active = False

        # Activate target version
        self.prompts[prompt_id][version].is_active = True

        logger.info(f"Activated prompt {prompt_id} v{version}")

        Laminar.event(
            name="prompt_version_activated",
            value={
                "prompt_id": prompt_id,
                "version": version,
            },
        )

    def export_prompts(self, filepath: str):
        """Export all prompts to JSON file"""
        export_data = {}
        for prompt_id, versions in self.prompts.items():
            export_data[prompt_id] = {
                version: prompt.to_dict() for version, prompt in versions.items()
            }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported prompts to {filepath}")

    def import_prompts(self, filepath: str):
        """Import prompts from JSON file"""
        with open(filepath, "r") as f:
            import_data = json.load(f)

        for prompt_id, versions in import_data.items():
            for version, data in versions.items():
                self.register_prompt(
                    prompt_id=data["prompt_id"],
                    version=data["version"],
                    prompt_type=PromptType(data["prompt_type"]),
                    template=data["template"],
                    variables=data["variables"],
                    metadata=data.get("metadata", {}),
                    is_active=data.get("is_active", True),
                )

        logger.info(f"Imported prompts from {filepath}")


# Global prompt manager instance
prompt_manager = PromptManager()
