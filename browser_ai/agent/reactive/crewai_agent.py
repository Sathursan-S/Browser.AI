"""
CrewAI-based reactive agent implementation.

This module implements a reactive agent using CrewAI's multi-agent framework
for collaborative browser automation with specialized agent roles.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type, Union, Set
from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

try:
    from crewai import Agent as CrewAgent, Task, Crew
    from crewai.tools import BaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    # Fallback classes for when CrewAI is not available
    class CrewAgent:
        def __init__(self, *args, **kwargs):
            pass
    class Task:
        def __init__(self, *args, **kwargs):
            pass
    class Crew:
        def __init__(self, *args, **kwargs):
            pass
        def kickoff(self):
            return "CrewAI not available"
    class BaseTool:
        def __init__(self, *args, **kwargs):
            pass
    CREWAI_AVAILABLE = False

from browser_ai.agent.reactive.base_reactive import BaseReactiveAgent, ReactiveEvent
from browser_ai.agent.views import AgentOutput, ActionResult
from browser_ai.browser.views import BrowserState
from browser_ai.controller.registry.views import ActionModel

logger = logging.getLogger(__name__)


@dataclass
class AgentRole:
    """Definition of an agent role in the crew"""
    
    name: str
    role: str
    goal: str
    backstory: str
    tools: List[str]
    capabilities: List[str]
    priority: int = 0


class CrewTask(BaseModel):
    """Task definition for CrewAI agents"""
    
    description: str
    agent_role: str
    expected_output: str
    context: Optional[Dict[str, Any]] = None
    dependencies: List[str] = Field(default_factory=list)
    priority: int = 0
    timeout: Optional[float] = None


class BrowserTool(BaseTool):
    """Base tool for browser interactions in CrewAI"""
    
    def __init__(self, agent_ref, **kwargs):
        super().__init__(**kwargs)
        self.agent_ref = agent_ref
    
    def _execute(self, *args, **kwargs):
        """Execute the tool synchronously"""
        # This should be overridden by specific tools
        return self._aexecute(*args, **kwargs)
    
    async def _aexecute(self, *args, **kwargs):
        """Execute the tool asynchronously"""
        raise NotImplementedError


class NavigatorTool(BrowserTool):
    """Tool for navigation actions"""
    
    name: str = "navigator"
    description: str = "Navigate to URLs and manage browser tabs"
    
    async def _aexecute(self, action: str, url: Optional[str] = None, **kwargs):
        """Execute navigation actions"""
        
        if not self.agent_ref or not hasattr(self.agent_ref, 'browser_context'):
            return {"error": "Browser context not available"}
        
        try:
            if action == "navigate":
                if url:
                    # Use the browser context to navigate
                    await self.agent_ref.browser_context.session.page.goto(url)
                    return {"success": True, "action": "navigate", "url": url}
            
            elif action == "back":
                await self.agent_ref.browser_context.session.page.go_back()
                return {"success": True, "action": "back"}
            
            elif action == "refresh":
                await self.agent_ref.browser_context.session.page.reload()
                return {"success": True, "action": "refresh"}
            
            return {"error": f"Unknown navigation action: {action}"}
            
        except Exception as e:
            return {"error": str(e)}


class ExtractorTool(BrowserTool):
    """Tool for content extraction"""
    
    name: str = "extractor"
    description: str = "Extract content from web pages"
    
    async def _aexecute(self, extraction_type: str, selector: Optional[str] = None, **kwargs):
        """Execute extraction actions"""
        
        try:
            if extraction_type == "page_content":
                state = await self.agent_ref.browser_context.get_state()
                return {
                    "success": True,
                    "content": state.element_tree.get_clickable_elements_to_string() if state.element_tree else "",
                    "url": state.url,
                    "title": state.title
                }
            
            elif extraction_type == "element_text" and selector:
                # Extract specific element text
                page = self.agent_ref.browser_context.session.page
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    return {"success": True, "text": text, "selector": selector}
                else:
                    return {"error": f"Element not found: {selector}"}
            
            return {"error": f"Unknown extraction type: {extraction_type}"}
            
        except Exception as e:
            return {"error": str(e)}


class InteractorTool(BrowserTool):
    """Tool for element interactions"""
    
    name: str = "interactor"
    description: str = "Interact with web page elements"
    
    async def _aexecute(
        self, 
        action: str, 
        element_index: Optional[int] = None, 
        text: Optional[str] = None, 
        **kwargs
    ):
        """Execute interaction actions"""
        
        try:
            if not element_index:
                return {"error": "Element index required for interactions"}
            
            # Get available actions from the controller
            actions = []
            
            if action == "click":
                from browser_ai.controller.registry.actions.click_element import ClickElementAction
                action_instance = ClickElementAction()
                params = action_instance.ClickElementParams(index=element_index)
                action_model = self.agent_ref.ActionModel(click_element=params)
                actions.append(action_model)
            
            elif action == "input_text" and text:
                from browser_ai.controller.registry.actions.input_text import InputTextAction
                action_instance = InputTextAction()
                params = action_instance.InputTextParams(index=element_index, text=text)
                action_model = self.agent_ref.ActionModel(input_text=params)
                actions.append(action_model)
            
            if actions:
                results = await self.agent_ref.controller.multi_act(
                    actions,
                    self.agent_ref.browser_context
                )
                
                return {
                    "success": True,
                    "action": action,
                    "element_index": element_index,
                    "results": [r.model_dump() for r in results]
                }
            
            return {"error": f"Unknown interaction action: {action}"}
            
        except Exception as e:
            return {"error": str(e)}


class CrewAIReactiveAgent(BaseReactiveAgent):
    """
    Reactive agent implementation using CrewAI for multi-agent collaboration.
    
    This agent creates a crew of specialized agents that work together to
    accomplish browser automation tasks through role-based collaboration.
    
    Key features:
    - Multi-agent collaboration
    - Specialized agent roles (Navigator, Extractor, Interactor, Analyzer)
    - Task delegation and coordination
    - Parallel agent execution
    - Cross-agent communication
    """
    
    def __init__(
        self,
        task: str,
        llm: BaseChatModel,
        # CrewAI-specific parameters
        agent_roles: Optional[List[AgentRole]] = None,
        max_concurrent_agents: int = 3,
        enable_agent_memory: bool = True,
        cooperation_mode: str = "collaborative",  # or "hierarchical"
        **kwargs
    ):
        """
        Initialize the CrewAI reactive agent.
        
        Args:
            task: Task description
            llm: Language model to use
            agent_roles: Custom agent roles (uses defaults if None)
            max_concurrent_agents: Maximum agents to run concurrently
            enable_agent_memory: Enable memory sharing between agents
            cooperation_mode: Agent cooperation mode
            **kwargs: Additional arguments passed to parent
        """
        
        if not CREWAI_AVAILABLE:
            logger.error("CrewAI is not available. Please install it with: pip install crewai")
            raise ImportError("CrewAI is required for this agent implementation")
        
        super().__init__(task=task, llm=llm, **kwargs)
        
        self.agent_roles = agent_roles or self._get_default_roles()
        self.max_concurrent_agents = max_concurrent_agents
        self.enable_agent_memory = enable_agent_memory
        self.cooperation_mode = cooperation_mode
        
        # CrewAI components
        self.crew: Optional[Crew] = None
        self.crew_agents: Dict[str, CrewAgent] = {}
        self.crew_tasks: List[Task] = []
        self.agent_tools: Dict[str, List[BrowserTool]] = {}
        
        # Task coordination
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.agent_results: Dict[str, Any] = {}
        self.active_agents: Set[str] = set()
        
        # Initialize the crew
        self._initialize_crew()
        
        logger.info(f"Initialized CrewAI reactive agent with {len(self.agent_roles)} agents "
                   f"in {cooperation_mode} mode")
    
    def _get_default_roles(self) -> List[AgentRole]:
        """Get default agent roles for browser automation"""
        
        return [
            AgentRole(
                name="navigator",
                role="Web Navigator",
                goal="Navigate through websites efficiently and handle page transitions",
                backstory="You are an expert web navigator who knows how to efficiently "
                         "move through websites, handle different types of pages, and "
                         "manage browser state transitions.",
                tools=["navigator"],
                capabilities=["navigation", "url_handling", "tab_management"],
                priority=1
            ),
            AgentRole(
                name="extractor", 
                role="Content Extractor",
                goal="Extract and analyze content from web pages accurately",
                backstory="You are a specialist in web content extraction and analysis. "
                         "You can identify important information, parse complex layouts, "
                         "and extract data in structured formats.",
                tools=["extractor"],
                capabilities=["content_extraction", "data_parsing", "text_analysis"],
                priority=2
            ),
            AgentRole(
                name="interactor",
                role="Web Interactor", 
                goal="Interact with web page elements precisely and reliably",
                backstory="You are skilled at interacting with various web elements like "
                         "forms, buttons, links, and complex UI components. You understand "
                         "different interaction patterns and can handle dynamic content.",
                tools=["interactor"],
                capabilities=["element_interaction", "form_filling", "ui_automation"],
                priority=3
            ),
            AgentRole(
                name="analyzer",
                role="Task Analyzer",
                goal="Analyze task progress and coordinate agent activities",
                backstory="You are the strategic coordinator who understands the overall "
                         "task objectives and can break them down into smaller subtasks, "
                         "assign them to appropriate agents, and monitor progress.",
                tools=["analyzer"],
                capabilities=["task_analysis", "coordination", "progress_monitoring"],
                priority=0
            )
        ]
    
    def _initialize_crew(self) -> None:
        """Initialize the CrewAI crew and agents"""
        
        # Create tools for each agent
        self._create_agent_tools()
        
        # Create CrewAI agents
        for role in self.agent_roles:
            agent_tools = self.agent_tools.get(role.name, [])
            
            crew_agent = CrewAgent(
                role=role.role,
                goal=role.goal,
                backstory=role.backstory,
                tools=agent_tools,
                verbose=True,
                llm=self.llm,
                memory=self.enable_agent_memory
            )
            
            self.crew_agents[role.name] = crew_agent
        
        logger.debug(f"Created {len(self.crew_agents)} CrewAI agents")
    
    def _create_agent_tools(self) -> None:
        """Create browser tools for each agent"""
        
        for role in self.agent_roles:
            tools = []
            
            for tool_name in role.tools:
                if tool_name == "navigator":
                    tools.append(NavigatorTool(agent_ref=self))
                elif tool_name == "extractor":
                    tools.append(ExtractorTool(agent_ref=self))
                elif tool_name == "interactor":
                    tools.append(InteractorTool(agent_ref=self))
                elif tool_name == "analyzer":
                    # Analyzer uses multiple tools
                    tools.extend([
                        NavigatorTool(agent_ref=self),
                        ExtractorTool(agent_ref=self),
                        InteractorTool(agent_ref=self)
                    ])
            
            self.agent_tools[role.name] = tools
    
    async def reactive_step(self, step_info: Optional[Dict[str, Any]] = None) -> AgentOutput:
        """Execute a reactive step using CrewAI collaboration"""
        
        try:
            # Analyze current state and create tasks
            crew_tasks = await self._create_crew_tasks(step_info)
            
            # Execute tasks with the crew
            crew_results = await self._execute_crew_tasks(crew_tasks)
            
            # Process results and create agent output
            output = await self._process_crew_results(crew_results)
            
            return output
            
        except Exception as e:
            logger.error(f"Error in CrewAI step execution: {e}")
            
            # Attempt recovery through crew coordination
            try:
                recovery_output = await self._crew_recovery(e, step_info)
                if recovery_output:
                    return recovery_output
            except Exception as recovery_error:
                logger.error(f"Crew recovery failed: {recovery_error}")
            
            raise e
    
    async def _create_crew_tasks(self, step_info: Optional[Dict[str, Any]] = None) -> List[CrewTask]:
        """Create tasks for the crew based on current state"""
        
        # Get current browser state
        current_state = await self.browser_context.get_state()
        
        # Analyze what needs to be done
        tasks = []
        
        # Always start with analysis
        tasks.append(CrewTask(
            description=f"Analyze the current state and break down the task: {self.task}",
            agent_role="analyzer",
            expected_output="Task breakdown with specific steps and agent assignments",
            context={"current_state": current_state, "step_info": step_info},
            priority=0
        ))
        
        # Determine if we need navigation
        if step_info and step_info.get('requires_navigation'):
            tasks.append(CrewTask(
                description=f"Navigate to required page or handle page transitions",
                agent_role="navigator", 
                expected_output="Confirmation of navigation completion",
                dependencies=["analyzer"],
                priority=1
            ))
        
        # Check if content extraction is needed
        if 'extract' in self.task.lower() or 'find' in self.task.lower():
            tasks.append(CrewTask(
                description=f"Extract relevant content from the current page",
                agent_role="extractor",
                expected_output="Extracted content in structured format",
                dependencies=["analyzer"],
                priority=2
            ))
        
        # Check if interaction is needed
        if any(word in self.task.lower() for word in ['click', 'fill', 'submit', 'select']):
            tasks.append(CrewTask(
                description=f"Interact with page elements as needed",
                agent_role="interactor",
                expected_output="Confirmation of interactions completed",
                dependencies=["analyzer"],
                priority=3
            ))
        
        return tasks
    
    async def _execute_crew_tasks(self, crew_tasks: List[CrewTask]) -> Dict[str, Any]:
        """Execute tasks using the CrewAI crew"""
        
        # Convert CrewTask objects to CrewAI Task objects
        crewai_tasks = []
        
        for crew_task in crew_tasks:
            agent = self.crew_agents.get(crew_task.agent_role)
            
            if not agent:
                logger.warning(f"Agent not found for role: {crew_task.agent_role}")
                continue
            
            crewai_task = Task(
                description=crew_task.description,
                agent=agent,
                expected_output=crew_task.expected_output
            )
            
            crewai_tasks.append(crewai_task)
        
        # Create and execute the crew
        crew = Crew(
            agents=list(self.crew_agents.values()),
            tasks=crewai_tasks,
            verbose=True
        )
        
        # Execute crew tasks
        try:
            if hasattr(crew, 'kickoff_async'):
                result = await crew.kickoff_async()
            else:
                # Fallback to synchronous execution
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, crew.kickoff)
            
            # Emit crew execution event
            await self.emit_event("crewai", "crew_tasks_completed", {
                "task_count": len(crewai_tasks),
                "agents_involved": list(self.crew_agents.keys()),
                "result_type": type(result).__name__
            })
            
            return {"crew_result": result, "individual_results": {}}
            
        except Exception as e:
            logger.error(f"Error executing crew tasks: {e}")
            raise e
    
    async def _process_crew_results(self, crew_results: Dict[str, Any]) -> AgentOutput:
        """Process crew execution results into AgentOutput"""
        
        # Extract the main result
        main_result = crew_results.get("crew_result", "")
        
        # Create agent brain state
        from browser_ai.agent.views import AgentBrain
        
        brain_state = AgentBrain(
            page_summary="Processed by CrewAI multi-agent collaboration",
            evaluation_previous_goal="Success - Crew task execution completed",
            memory=f"Crew completed tasks with {len(self.crew_agents)} specialized agents",
            next_goal="Continue task execution based on crew analysis"
        )
        
        # Determine actions based on crew results
        actions = await self._extract_actions_from_results(crew_results)
        
        return self.AgentOutput(
            current_state=brain_state,
            action=actions
        )
    
    async def _extract_actions_from_results(self, crew_results: Dict[str, Any]) -> List[ActionModel]:
        """Extract concrete actions from crew results"""
        
        actions = []
        main_result = crew_results.get("crew_result", "")
        
        # Parse the crew result to determine actions
        # This is a simplified implementation - in practice, you'd have more
        # sophisticated result parsing based on your specific use case
        
        if isinstance(main_result, str):
            result_lower = main_result.lower()
            
            if "navigate to" in result_lower or "go to" in result_lower:
                # Extract URL if possible (simplified)
                import re
                url_match = re.search(r'https?://[^\s]+', main_result)
                if url_match:
                    from browser_ai.controller.registry.actions.go_to_url import GoToUrlAction
                    action_instance = GoToUrlAction()
                    params = action_instance.GoToUrlParams(url=url_match.group())
                    action_model = self.ActionModel(go_to_url=params)
                    actions.append(action_model)
            
            if "click" in result_lower:
                # This would need more sophisticated parsing in practice
                # For now, just create a placeholder action
                pass
            
            if "extract" in result_lower or "done" in result_lower:
                from browser_ai.controller.registry.actions.done import DoneAction
                action_instance = DoneAction()
                params = action_instance.DoneParams(text=main_result)
                action_model = self.ActionModel(done=params)
                actions.append(action_model)
        
        return actions
    
    async def _crew_recovery(self, error: Exception, step_info: Optional[Dict[str, Any]]) -> Optional[AgentOutput]:
        """Attempt recovery using crew coordination"""
        
        logger.info("Attempting crew-based recovery")
        
        try:
            # Create a recovery task for the analyzer
            recovery_task = CrewTask(
                description=f"Analyze the error and suggest recovery actions: {str(error)}",
                agent_role="analyzer",
                expected_output="Recovery strategy and specific actions to take",
                context={"error": str(error), "error_type": error.__class__.__name__, "step_info": step_info}
            )
            
            # Execute recovery task
            recovery_results = await self._execute_crew_tasks([recovery_task])
            
            # Process recovery results
            if recovery_results:
                return await self._process_crew_results(recovery_results)
            
        except Exception as recovery_error:
            logger.error(f"Crew recovery failed: {recovery_error}")
        
        return None
    
    # Recovery methods implementation
    
    async def get_recovery_action(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Determine recovery action using crew analysis"""
        
        # Use the analyzer agent to determine recovery
        analyzer_agent = self.crew_agents.get("analyzer")
        
        if analyzer_agent:
            try:
                # Create a recovery analysis task
                recovery_task = Task(
                    description=f"Analyze this error and suggest recovery: {str(error)}",
                    agent=analyzer_agent,
                    expected_output="Recovery action name (retry, navigate_back, refresh, etc.)"
                )
                
                # Execute the task
                crew = Crew(agents=[analyzer_agent], tasks=[recovery_task], verbose=False)
                
                if hasattr(crew, 'kickoff_async'):
                    result = await crew.kickoff_async()
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, crew.kickoff)
                
                # Parse result for recovery action
                if isinstance(result, str):
                    result_lower = result.lower()
                    if 'retry' in result_lower:
                        return 'crew_retry'
                    elif 'navigate' in result_lower or 'back' in result_lower:
                        return 'crew_navigate_back'
                    elif 'refresh' in result_lower:
                        return 'crew_refresh'
                    elif 'restart' in result_lower:
                        return 'crew_restart'
                
            except Exception as e:
                logger.error(f"Error in crew recovery analysis: {e}")
        
        return 'crew_retry'  # Default recovery
    
    async def execute_recovery_action(
        self, 
        action: str, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Execute recovery action using appropriate crew agent"""
        
        if action == 'crew_retry':
            await asyncio.sleep(1.0)  # Simple retry delay
        
        elif action == 'crew_navigate_back':
            navigator = self.crew_agents.get("navigator")
            if navigator:
                tool = NavigatorTool(agent_ref=self)
                await tool._aexecute("back")
        
        elif action == 'crew_refresh':
            navigator = self.crew_agents.get("navigator")
            if navigator:
                tool = NavigatorTool(agent_ref=self)
                await tool._aexecute("refresh")
        
        elif action == 'crew_restart':
            # Restart the crew coordination
            self._initialize_crew()
        
        logger.info(f"Executed crew recovery action: {action}")
    
    def get_crew_status(self) -> Dict[str, Any]:
        """Get current crew execution status"""
        
        return {
            "cooperation_mode": self.cooperation_mode,
            "total_agents": len(self.crew_agents),
            "active_agents": list(self.active_agents),
            "max_concurrent": self.max_concurrent_agents,
            "memory_enabled": self.enable_agent_memory,
            "agent_roles": [role.name for role in self.agent_roles],
            "pending_tasks": self.task_queue.qsize(),
            "agent_results": len(self.agent_results)
        }
    
    def get_agent_capabilities(self) -> Dict[str, List[str]]:
        """Get capabilities of each agent in the crew"""
        
        return {
            role.name: role.capabilities 
            for role in self.agent_roles
        }