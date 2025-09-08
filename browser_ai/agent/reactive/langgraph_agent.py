"""
LangGraph-based reactive agent implementation.

This module implements a reactive agent using LangGraph's state graph capabilities
for managing complex browser interaction workflows with conditional logic and
parallel execution.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, TypedDict, Union

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage

try:
    from langgraph.graph import END, START, StateGraph
    from langgraph.graph.message import MessageGraph
    from langgraph.prebuilt import ToolNode
    LANGGRAPH_AVAILABLE = True
except ImportError:
    # Fallback for when LangGraph is not available
    class StateGraph:
        def __init__(self, *args, **kwargs):
            pass
        def add_node(self, *args, **kwargs):
            pass
        def add_edge(self, *args, **kwargs):
            pass
        def add_conditional_edges(self, *args, **kwargs):
            pass
        def compile(self):
            return MockCompiledGraph()
    
    class MockCompiledGraph:
        def invoke(self, state):
            return state
        async def ainvoke(self, state):
            return state
    
    END = "END"
    START = "START"
    ToolNode = None
    MessageGraph = None
    LANGGRAPH_AVAILABLE = False
from pydantic import BaseModel, Field

from browser_ai.agent.reactive.base_reactive import BaseReactiveAgent, ReactiveEvent
from browser_ai.agent.views import AgentOutput, ActionResult
from browser_ai.browser.views import BrowserState
from browser_ai.controller.registry.views import ActionModel

logger = logging.getLogger(__name__)


class GraphState(TypedDict):
    """State definition for the LangGraph workflow"""
    
    # Core state
    messages: List[BaseMessage]
    browser_state: BrowserState
    current_goal: str
    task_progress: Dict[str, Any]
    
    # Execution state
    actions_to_execute: List[ActionModel]
    last_action_result: Optional[ActionResult]
    retry_count: int
    
    # Control flow
    next_node: Optional[str]
    should_continue: bool
    error_context: Optional[Dict[str, Any]]
    
    # Reactive state
    pending_events: List[ReactiveEvent]
    state_changes: List[Dict[str, Any]]


class LangGraphReactiveAgent(BaseReactiveAgent):
    """
    Reactive agent implementation using LangGraph for workflow management.
    
    This agent uses LangGraph's state graph capabilities to create complex,
    conditional workflows for browser automation with reactive event handling.
    
    Key features:
    - State-based workflow execution
    - Conditional branching based on browser state
    - Parallel action execution
    - Event-driven state transitions
    - Automatic error recovery paths
    """
    
    def __init__(
        self,
        task: str,
        llm: BaseChatModel,
        # LangGraph-specific parameters
        enable_parallel_execution: bool = False,
        max_parallel_actions: int = 3,
        enable_conditional_flow: bool = True,
        recovery_strategies: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize the LangGraph reactive agent.
        
        Args:
            task: Task description
            llm: Language model to use
            enable_parallel_execution: Enable parallel action execution
            max_parallel_actions: Maximum actions to execute in parallel
            enable_conditional_flow: Enable conditional workflow branching
            recovery_strategies: List of recovery strategies to use
            **kwargs: Additional arguments passed to parent
        """
        
        super().__init__(task=task, llm=llm, **kwargs)
        
        if not LANGGRAPH_AVAILABLE:
            logger.warning("LangGraph is not available. Some features will be limited.")
            logger.warning("Install with: pip install langgraph>=0.5.4")
        
        self.enable_parallel_execution = enable_parallel_execution
        self.max_parallel_actions = max_parallel_actions
        self.enable_conditional_flow = enable_conditional_flow
        self.recovery_strategies = recovery_strategies or ['retry', 'alternative_path', 'human_intervention']
        
        # LangGraph components
        self.workflow_graph: Optional[StateGraph] = None
        self.compiled_graph = None
        
        # Workflow state
        self.graph_state: Optional[GraphState] = None
        
        # Build the workflow graph
        self._build_workflow_graph()
        
        logger.info(f"Initialized LangGraph reactive agent with features: "
                   f"parallel={enable_parallel_execution}, "
                   f"conditional={enable_conditional_flow}")
    
    def _build_workflow_graph(self) -> None:
        """Build the LangGraph workflow"""
        
        # Create the state graph
        self.workflow_graph = StateGraph(GraphState)
        
        # Add nodes
        self.workflow_graph.add_node("analyze_state", self._analyze_state_node)
        self.workflow_graph.add_node("plan_actions", self._plan_actions_node)
        self.workflow_graph.add_node("execute_actions", self._execute_actions_node)
        self.workflow_graph.add_node("evaluate_results", self._evaluate_results_node)
        self.workflow_graph.add_node("handle_errors", self._handle_errors_node)
        self.workflow_graph.add_node("process_events", self._process_events_node)
        
        if self.enable_parallel_execution:
            self.workflow_graph.add_node("parallel_executor", self._parallel_executor_node)
        
        # Add edges
        self.workflow_graph.add_edge(START, "analyze_state")
        self.workflow_graph.add_edge("analyze_state", "process_events")
        self.workflow_graph.add_edge("process_events", "plan_actions")
        
        if self.enable_parallel_execution:
            self.workflow_graph.add_edge("plan_actions", "parallel_executor")
            self.workflow_graph.add_edge("parallel_executor", "evaluate_results")
        else:
            self.workflow_graph.add_edge("plan_actions", "execute_actions")
            self.workflow_graph.add_edge("execute_actions", "evaluate_results")
        
        # Conditional edges for flow control
        if self.enable_conditional_flow:
            self.workflow_graph.add_conditional_edges(
                "evaluate_results",
                self._should_continue_or_error,
                {
                    "continue": "analyze_state",
                    "error": "handle_errors",
                    "complete": END
                }
            )
            
            self.workflow_graph.add_conditional_edges(
                "handle_errors",
                self._recovery_decision,
                {
                    "retry": "analyze_state",
                    "alternative": "plan_actions",
                    "escalate": END
                }
            )
        else:
            # Simple linear flow
            self.workflow_graph.add_edge("evaluate_results", END)
        
        # Compile the graph
        self.compiled_graph = self.workflow_graph.compile()
        
        logger.debug("LangGraph workflow compiled successfully")
    
    async def reactive_step(self, step_info: Optional[Dict[str, Any]] = None) -> AgentOutput:
        """Execute a reactive step using the LangGraph workflow"""
        
        # Initialize graph state if needed
        if not self.graph_state:
            await self._initialize_graph_state()
        
        # Update step info
        if step_info:
            self.graph_state['task_progress'].update(step_info)
        
        # Run the workflow
        try:
            # Execute the compiled graph
            result = await self._run_graph_step()
            
            # Extract agent output from graph state
            output = await self._extract_agent_output()
            
            return output
            
        except Exception as e:
            logger.error(f"Error in LangGraph step execution: {e}")
            
            # Handle error through graph if possible
            self.graph_state['error_context'] = {
                'error': str(e),
                'error_type': e.__class__.__name__,
                'step_info': step_info
            }
            
            # Try error handling node
            try:
                error_result = await self._handle_errors_node(self.graph_state)
                if error_result.get('recovery_action'):
                    return await self._extract_agent_output()
            except Exception as recovery_error:
                logger.error(f"Error recovery failed: {recovery_error}")
            
            raise e
    
    async def _initialize_graph_state(self) -> None:
        """Initialize the graph state"""
        
        current_state = await self.browser_context.get_state()
        
        self.graph_state = {
            'messages': self.message_manager.get_messages(),
            'browser_state': current_state,
            'current_goal': self.task,
            'task_progress': {
                'step_number': self.n_steps,
                'completed_actions': 0,
                'total_actions': 0
            },
            'actions_to_execute': [],
            'last_action_result': self._last_result[0] if self._last_result else None,
            'retry_count': 0,
            'next_node': None,
            'should_continue': True,
            'error_context': None,
            'pending_events': [],
            'state_changes': []
        }
    
    async def _run_graph_step(self) -> Dict[str, Any]:
        """Run a single step of the graph workflow"""
        
        # Use async invoke if available, otherwise use regular invoke
        if hasattr(self.compiled_graph, 'ainvoke'):
            result = await self.compiled_graph.ainvoke(self.graph_state)
        else:
            # Run in thread pool for synchronous graphs
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self.compiled_graph.invoke, self.graph_state)
        
        # Update internal state
        self.graph_state.update(result)
        
        return result
    
    async def _extract_agent_output(self) -> AgentOutput:
        """Extract AgentOutput from graph state"""
        
        # Get the current reasoning from the last message or generate it
        if self.graph_state['messages']:
            last_message = self.graph_state['messages'][-1]
            reasoning_content = last_message.content if hasattr(last_message, 'content') else ""
        else:
            reasoning_content = "Processing browser state..."
        
        # Create agent brain state
        from browser_ai.agent.views import AgentBrain
        
        brain_state = AgentBrain(
            page_summary=f"Current URL: {self.graph_state['browser_state'].url}",
            evaluation_previous_goal="Success - LangGraph workflow step completed",
            memory=f"Completed {self.graph_state['task_progress']['completed_actions']} actions",
            next_goal=self.graph_state['current_goal']
        )
        
        # Get actions to execute
        actions = self.graph_state.get('actions_to_execute', [])
        if not actions:
            # Create a default action if none specified
            actions = []  # Let the controller handle empty actions
        
        return self.AgentOutput(
            current_state=brain_state,
            action=actions
        )
    
    # Graph node implementations
    
    async def _analyze_state_node(self, state: GraphState) -> Dict[str, Any]:
        """Analyze current browser state"""
        
        logger.debug("Executing analyze_state node")
        
        # Get current browser state
        current_state = await self.browser_context.get_state()
        
        # Update state
        state['browser_state'] = current_state
        
        # Emit state analysis event
        await self.emit_event("langgraph", "state_analyzed", {
            "url": current_state.url,
            "title": current_state.title,
            "elements_count": len(current_state.element_tree.clickable_elements) if current_state.element_tree else 0
        })
        
        return state
    
    async def _plan_actions_node(self, state: GraphState) -> Dict[str, Any]:
        """Plan actions based on current state"""
        
        logger.debug("Executing plan_actions node")
        
        try:
            # Use the parent's get_next_action method to get reasoning and actions
            messages = self.message_manager.get_messages()
            agent_output = await self.get_next_action(messages)
            
            # Extract actions
            state['actions_to_execute'] = agent_output.action
            state['current_goal'] = agent_output.current_state.next_goal
            
            # Update task progress
            state['task_progress']['total_actions'] = len(agent_output.action)
            
            # Emit planning event
            await self.emit_event("langgraph", "actions_planned", {
                "action_count": len(agent_output.action),
                "goal": agent_output.current_state.next_goal
            })
            
        except Exception as e:
            logger.error(f"Error in action planning: {e}")
            state['error_context'] = {
                'node': 'plan_actions',
                'error': str(e),
                'error_type': e.__class__.__name__
            }
        
        return state
    
    async def _execute_actions_node(self, state: GraphState) -> Dict[str, Any]:
        """Execute planned actions"""
        
        logger.debug("Executing execute_actions node")
        
        actions = state.get('actions_to_execute', [])
        
        if not actions:
            logger.warning("No actions to execute")
            return state
        
        try:
            # Execute actions through the controller
            results = await self.controller.multi_act(
                actions,
                self.browser_context,
                page_extraction_llm=self.page_extraction_llm,
                sensitive_data=self.sensitive_data
            )
            
            # Update state with results
            state['last_action_result'] = results[-1] if results else None
            state['task_progress']['completed_actions'] += len(actions)
            
            # Emit execution event
            await self.emit_event("langgraph", "actions_executed", {
                "action_count": len(actions),
                "results_count": len(results),
                "success": all(not r.error for r in results if r)
            })
            
        except Exception as e:
            logger.error(f"Error in action execution: {e}")
            state['error_context'] = {
                'node': 'execute_actions',
                'error': str(e),
                'error_type': e.__class__.__name__,
                'actions': [a.model_dump() for a in actions]
            }
        
        return state
    
    async def _parallel_executor_node(self, state: GraphState) -> Dict[str, Any]:
        """Execute actions in parallel"""
        
        logger.debug("Executing parallel_executor node")
        
        actions = state.get('actions_to_execute', [])
        
        if not actions:
            return state
        
        # Split actions into batches for parallel execution
        batches = [
            actions[i:i + self.max_parallel_actions] 
            for i in range(0, len(actions), self.max_parallel_actions)
        ]
        
        all_results = []
        
        try:
            for batch in batches:
                # Execute batch in parallel
                tasks = [
                    self._execute_single_action(action, state)
                    for action in batch
                ]
                
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                all_results.extend(batch_results)
            
            # Update state
            successful_results = [r for r in all_results if not isinstance(r, Exception)]
            state['last_action_result'] = successful_results[-1] if successful_results else None
            state['task_progress']['completed_actions'] += len(successful_results)
            
            # Emit parallel execution event
            await self.emit_event("langgraph", "parallel_execution_completed", {
                "total_actions": len(actions),
                "successful": len(successful_results),
                "failed": len(actions) - len(successful_results),
                "batches": len(batches)
            })
            
        except Exception as e:
            logger.error(f"Error in parallel execution: {e}")
            state['error_context'] = {
                'node': 'parallel_executor',
                'error': str(e),
                'error_type': e.__class__.__name__
            }
        
        return state
    
    async def _execute_single_action(self, action: ActionModel, state: GraphState) -> ActionResult:
        """Execute a single action (for parallel execution)"""
        
        try:
            results = await self.controller.multi_act(
                [action],
                self.browser_context,
                page_extraction_llm=self.page_extraction_llm,
                sensitive_data=self.sensitive_data
            )
            return results[0] if results else ActionResult(error="No result returned")
            
        except Exception as e:
            return ActionResult(error=str(e))
    
    async def _evaluate_results_node(self, state: GraphState) -> Dict[str, Any]:
        """Evaluate action results and determine next steps"""
        
        logger.debug("Executing evaluate_results node")
        
        last_result = state.get('last_action_result')
        
        if last_result:
            if last_result.is_done:
                state['should_continue'] = False
                await self.emit_event("langgraph", "task_completed", {
                    "result": last_result.extracted_content
                })
            elif last_result.error:
                state['error_context'] = {
                    'node': 'evaluate_results',
                    'error': last_result.error,
                    'action_error': True
                }
                await self.emit_event("langgraph", "action_error_detected", {
                    "error": last_result.error
                })
            else:
                state['should_continue'] = True
        
        return state
    
    async def _process_events_node(self, state: GraphState) -> Dict[str, Any]:
        """Process pending reactive events"""
        
        logger.debug("Executing process_events node")
        
        # Process any pending events from the reactive system
        if self._reactive_state and self._reactive_state.event_history:
            # Get recent events that haven't been processed
            recent_events = [
                event for event in self._reactive_state.event_history[-10:]
                if event.source != 'langgraph'  # Avoid processing our own events
            ]
            
            state['pending_events'] = recent_events
            
            # React to important events
            for event in recent_events:
                if event.event_type == "browser_state_changed":
                    # Update our browser state
                    new_browser_state = event.event_data.get('new_state')
                    if new_browser_state:
                        state['browser_state'] = new_browser_state
                
                elif event.event_type == "user_intervention":
                    # Handle user interventions
                    user_action = event.event_data.get('action')
                    if user_action == 'pause':
                        state['should_continue'] = False
        
        return state
    
    async def _handle_errors_node(self, state: GraphState) -> Dict[str, Any]:
        """Handle errors with recovery strategies"""
        
        logger.debug("Executing handle_errors node")
        
        error_context = state.get('error_context')
        
        if not error_context:
            return state
        
        error = error_context.get('error', '')
        error_type = error_context.get('error_type', 'Unknown')
        
        # Determine recovery strategy
        recovery_action = await self.get_recovery_action(
            Exception(error), 
            error_context
        )
        
        if recovery_action:
            logger.info(f"Applying recovery action: {recovery_action}")
            
            try:
                await self.execute_recovery_action(recovery_action, Exception(error), error_context)
                
                # Clear error context after successful recovery
                state['error_context'] = None
                state['retry_count'] = state.get('retry_count', 0) + 1
                
                await self.emit_event("langgraph", "error_recovered", {
                    "recovery_action": recovery_action,
                    "error_type": error_type,
                    "retry_count": state['retry_count']
                })
                
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {recovery_error}")
                state['error_context']['recovery_failed'] = str(recovery_error)
        
        return state
    
    # Conditional edge functions
    
    def _should_continue_or_error(self, state: GraphState) -> str:
        """Determine if workflow should continue, handle error, or complete"""
        
        if state.get('error_context'):
            return "error"
        
        if not state.get('should_continue', True):
            return "complete"
        
        last_result = state.get('last_action_result')
        if last_result and last_result.is_done:
            return "complete"
        
        return "continue"
    
    def _recovery_decision(self, state: GraphState) -> str:
        """Decide on recovery strategy"""
        
        error_context = state.get('error_context', {})
        retry_count = state.get('retry_count', 0)
        
        if retry_count >= 3:
            return "escalate"
        
        error_type = error_context.get('error_type', '')
        
        if 'timeout' in error_type.lower() or 'rate' in error_type.lower():
            return "retry"
        
        if 'validation' in error_type.lower():
            return "alternative"
        
        return "retry"
    
    # Recovery methods implementation
    
    async def get_recovery_action(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Determine recovery action for LangGraph workflows"""
        
        error_type = context.get('error_type', '').lower()
        node = context.get('node', '')
        
        if 'timeout' in error_type or 'rate' in error_type:
            return 'retry_with_delay'
        
        if 'validation' in error_type:
            return 'regenerate_plan'
        
        if node == 'execute_actions':
            return 'retry_actions'
        
        if node == 'plan_actions':
            return 'simplify_plan'
        
        return 'retry' if 'retry' in self.recovery_strategies else None
    
    async def execute_recovery_action(
        self, 
        action: str, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Execute recovery action for LangGraph workflows"""
        
        if action == 'retry_with_delay':
            await asyncio.sleep(2.0)  # Wait before retry
        
        elif action == 'regenerate_plan':
            # Clear current actions and force replanning
            if self.graph_state:
                self.graph_state['actions_to_execute'] = []
        
        elif action == 'retry_actions':
            # Reset action execution state
            if self.graph_state:
                self.graph_state['last_action_result'] = None
        
        elif action == 'simplify_plan':
            # Reduce the number of actions in the plan
            if self.graph_state and self.graph_state.get('actions_to_execute'):
                actions = self.graph_state['actions_to_execute']
                self.graph_state['actions_to_execute'] = actions[:1]  # Keep only first action
        
        logger.info(f"Executed recovery action: {action}")
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow execution status"""
        
        if not self.graph_state:
            return {"status": "not_initialized"}
        
        return {
            "status": "running" if self.graph_state.get('should_continue', True) else "completed",
            "current_goal": self.graph_state.get('current_goal'),
            "task_progress": self.graph_state.get('task_progress', {}),
            "retry_count": self.graph_state.get('retry_count', 0),
            "has_errors": bool(self.graph_state.get('error_context')),
            "pending_events": len(self.graph_state.get('pending_events', [])),
            "actions_queued": len(self.graph_state.get('actions_to_execute', []))
        }