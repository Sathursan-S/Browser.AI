"""
Stuck Detection and User Intervention Module

Detects when the Browser.AI agent is stuck in a loop or unable to make progress,
and requests user assistance via the chatbot interface.
"""

import logging
import time
from collections import deque
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class StuckDetectionConfig:
    """Configuration for stuck detection"""
    # Maximum time (seconds) for a single step before considering stuck
    max_step_duration: int = 120
    
    # Number of similar actions to track
    action_history_size: int = 5
    
    # Threshold for considering actions as "similar" (0.0 to 1.0)
    similarity_threshold: float = 0.7
    
    # How many similar actions in a row indicate being stuck
    stuck_action_threshold: int = 3
    
    # Maximum time (seconds) without progress before asking for help
    max_time_without_progress: int = 300  # 5 minutes
    
    # Minimum time between help requests (to avoid spamming)
    min_help_request_interval: int = 60


@dataclass
class ActionRecord:
    """Record of an action taken by the agent"""
    action_name: str
    timestamp: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StuckReport:
    """Report generated when agent is detected as stuck"""
    is_stuck: bool
    reason: str
    attempted_actions: List[str]
    duration_seconds: float
    suggestion: str
    detailed_summary: str


class StuckDetector:
    """Detects when the agent is stuck and needs user intervention"""
    
    def __init__(self, config: Optional[StuckDetectionConfig] = None):
        self.config = config or StuckDetectionConfig()
        self.action_history: deque = deque(maxlen=self.config.action_history_size)
        self.task_start_time: Optional[float] = None
        self.last_progress_time: Optional[float] = None
        self.last_help_request_time: Optional[float] = None
        self.consecutive_similar_actions = 0
        self.current_step_start: Optional[float] = None
        self.step_count = 0
        self.failure_count = 0
        
    def reset(self):
        """Reset the detector for a new task"""
        self.action_history.clear()
        self.task_start_time = time.time()
        self.last_progress_time = time.time()
        self.last_help_request_time = None
        self.consecutive_similar_actions = 0
        self.current_step_start = None
        self.step_count = 0
        self.failure_count = 0
        logger.info("🔄 Stuck detector reset for new task")
        
    def start_step(self):
        """Mark the start of a new step"""
        self.current_step_start = time.time()
        self.step_count += 1
        
    def record_action(
        self, 
        action_name: str, 
        success: bool, 
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record an action taken by the agent"""
        record = ActionRecord(
            action_name=action_name,
            timestamp=time.time(),
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        self.action_history.append(record)
        
        if success:
            self.last_progress_time = time.time()
            self.consecutive_similar_actions = 0
            self.failure_count = 0
        else:
            self.failure_count += 1
            
        # Check for similar action patterns
        if len(self.action_history) >= 2:
            if self._are_actions_similar(self.action_history[-1], self.action_history[-2]):
                self.consecutive_similar_actions += 1
            else:
                self.consecutive_similar_actions = 0
                
    def record_progress(self):
        """Mark that meaningful progress was made"""
        self.last_progress_time = time.time()
        self.consecutive_similar_actions = 0
        self.failure_count = 0
        
    def check_if_stuck(self) -> StuckReport:
        """Check if the agent appears to be stuck and needs help"""
        current_time = time.time()
        
        # Check if we should even ask for help (cooldown period)
        if self.last_help_request_time:
            time_since_last_request = current_time - self.last_help_request_time
            if time_since_last_request < self.config.min_help_request_interval:
                return StuckReport(
                    is_stuck=False,
                    reason="Recent help request still in cooldown",
                    attempted_actions=[],
                    duration_seconds=0,
                    suggestion="",
                    detailed_summary=""
                )
        
        # Check 1: Step taking too long
        if self.current_step_start:
            step_duration = current_time - self.current_step_start
            if step_duration > self.config.max_step_duration:
                return self._create_stuck_report(
                    reason=f"Single step taking too long ({int(step_duration)}s)",
                    suggestion="The agent seems stuck on this action. Please provide guidance on what to do next."
                )
        
        # Check 2: Repeating similar actions
        if self.consecutive_similar_actions >= self.config.stuck_action_threshold:
            recent_actions = [r.action_name for r in list(self.action_history)[-3:]]
            return self._create_stuck_report(
                reason=f"Repeating similar actions: {', '.join(recent_actions)}",
                suggestion="The agent is stuck in a loop. What should it try differently?"
            )
        
        # Check 3: No progress for extended period
        if self.last_progress_time:
            time_without_progress = current_time - self.last_progress_time
            if time_without_progress > self.config.max_time_without_progress:
                return self._create_stuck_report(
                    reason=f"No progress for {int(time_without_progress)}s",
                    suggestion="The agent hasn't made progress in a while. Should it try a different approach?"
                )
        
        # Check 4: Too many consecutive failures
        if self.failure_count >= 3:
            return self._create_stuck_report(
                reason=f"Multiple consecutive failures ({self.failure_count})",
                suggestion="The current approach isn't working. What would you like the agent to try instead?"
            )
        
        return StuckReport(
            is_stuck=False,
            reason="Agent is making progress",
            attempted_actions=[],
            duration_seconds=0,
            suggestion="",
            detailed_summary=""
        )
    
    def _are_actions_similar(self, action1: ActionRecord, action2: ActionRecord) -> bool:
        """Check if two actions are similar enough to be considered repetitive"""
        # Same action name is a strong indicator
        if action1.action_name == action2.action_name:
            # Both failed - likely stuck
            if not action1.success and not action2.success:
                return True
            # Same error message - definitely stuck
            if action1.error_message and action1.error_message == action2.error_message:
                return True
        
        return False
    
    def _create_stuck_report(self, reason: str, suggestion: str) -> StuckReport:
        """Create a stuck report with detailed information"""
        self.last_help_request_time = time.time()
        
        attempted_actions = [
            f"{r.action_name} ({'✅' if r.success else '❌'})"
            for r in self.action_history
        ]
        
        duration = 0
        if self.task_start_time:
            duration = time.time() - self.task_start_time
        
        # Create detailed summary
        summary_parts = [
            f"🤔 **The agent appears to be stuck**",
            f"",
            f"**Issue:** {reason}",
            f"**Duration:** {int(duration)}s ({self.step_count} steps attempted)",
            f"",
            f"**Recent Actions:**"
        ]
        
        for i, record in enumerate(list(self.action_history)[-5:], 1):
            status = "✅ Success" if record.success else "❌ Failed"
            error_info = f" - {record.error_message}" if record.error_message else ""
            summary_parts.append(f"{i}. `{record.action_name}` - {status}{error_info}")
        
        summary_parts.extend([
            f"",
            f"**Question:** {suggestion}",
            f"",
            f"💡 You can:",
            f"- Provide specific guidance on what to try",
            f"- Ask the agent to skip this part and move on",
            f"- Request a summary of what was accomplished so far",
            f"- Stop the task if needed"
        ])
        
        detailed_summary = "\n".join(summary_parts)
        
        return StuckReport(
            is_stuck=True,
            reason=reason,
            attempted_actions=attempted_actions,
            duration_seconds=duration,
            suggestion=suggestion,
            detailed_summary=detailed_summary
        )
    
    def should_request_help(self) -> bool:
        """Quick check if we should request help without full report"""
        report = self.check_if_stuck()
        return report.is_stuck
