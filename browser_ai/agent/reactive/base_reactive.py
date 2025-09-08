"""
Base reactive agent implementation.

This module provides the foundation for reactive agent patterns,
building upon the existing Browser.AI Agent class while adding
reactive capabilities like event-driven execution and state management.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Type, Union

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from browser_ai.agent.service import Agent
from browser_ai.agent.views import AgentHistoryList, AgentOutput, ActionResult
from browser_ai.browser.browser import Browser
from browser_ai.browser.context import BrowserContext
from browser_ai.browser.views import BrowserState
from browser_ai.controller.service import Controller

logger = logging.getLogger(__name__)


class ReactiveEvent(BaseModel):
    """Represents an event in the reactive system"""
    
    event_type: str = Field(description="Type of the event")
    event_data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    timestamp: float = Field(description="Event timestamp")
    source: str = Field(description="Event source")
    priority: int = Field(default=0, description="Event priority")


class ReactiveState(BaseModel):
    """Enhanced state management for reactive agents"""
    
    current_state: BrowserState
    event_history: List[ReactiveEvent] = Field(default_factory=list)
    active_listeners: Dict[str, List[Callable]] = Field(default_factory=dict)
    state_changes: List[Dict[str, Any]] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class BaseReactiveAgent(Agent, ABC):
    """
    Base class for reactive agents that extends the Browser.AI Agent
    with event-driven capabilities and reactive patterns.
    
    This class maintains compatibility with the existing Agent interface
    while adding reactive features like:
    - Event-driven execution
    - State change notifications  
    - Asynchronous event handling
    - Enhanced error recovery
    """
    
    def __init__(
        self,
        task: str,
        llm: BaseChatModel,
        browser: Browser | None = None,
        browser_context: BrowserContext | None = None,
        controller: Controller = Controller(),
        # Reactive-specific parameters
        enable_event_system: bool = True,
        event_buffer_size: int = 1000,
        auto_recovery: bool = True,
        state_change_callback: Optional[Callable[[ReactiveState], None]] = None,
        **kwargs
    ):
        """
        Initialize the reactive agent.
        
        Args:
            task: Task description
            llm: Language model to use
            browser: Optional browser instance
            browser_context: Optional browser context
            controller: Controller for action execution
            enable_event_system: Enable reactive event system
            event_buffer_size: Maximum events to keep in buffer
            auto_recovery: Enable automatic error recovery
            state_change_callback: Callback for state changes
            **kwargs: Additional arguments passed to parent Agent
        """
        
        # Initialize parent Agent
        super().__init__(
            task=task,
            llm=llm,
            browser=browser,
            browser_context=browser_context,
            controller=controller,
            **kwargs
        )
        
        # Reactive-specific initialization
        self.enable_event_system = enable_event_system
        self.event_buffer_size = event_buffer_size
        self.auto_recovery = auto_recovery
        self.state_change_callback = state_change_callback
        
        # Internal reactive state
        self._reactive_state: Optional[ReactiveState] = None
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._event_loop_task: Optional[asyncio.Task] = None
        
        # Performance metrics
        self._metrics = {
            'events_processed': 0,
            'state_changes': 0,
            'recovery_actions': 0,
            'avg_response_time': 0.0
        }
        
        logger.info(f"Initialized {self.__class__.__name__} with reactive features")
    
    async def start_reactive_system(self) -> None:
        """Start the reactive event processing system"""
        if not self.enable_event_system:
            logger.info("Event system disabled")
            return
            
        logger.info("Starting reactive event system")
        self._running = True
        
        # Initialize reactive state
        current_browser_state = await self.browser_context.get_state()
        self._reactive_state = ReactiveState(current_state=current_browser_state)
        
        # Start event processing loop
        self._event_loop_task = asyncio.create_task(self._event_processing_loop())
        
        # Emit startup event
        await self.emit_event("system", "reactive_system_started", {
            "agent_type": self.__class__.__name__,
            "features": {
                "event_system": self.enable_event_system,
                "auto_recovery": self.auto_recovery,
                "event_buffer_size": self.event_buffer_size
            }
        })
    
    async def stop_reactive_system(self) -> None:
        """Stop the reactive event processing system"""
        logger.info("Stopping reactive event system")
        self._running = False
        
        if self._event_loop_task:
            self._event_loop_task.cancel()
            try:
                await self._event_loop_task
            except asyncio.CancelledError:
                pass
        
        # Emit shutdown event
        if self._reactive_state:
            await self.emit_event("system", "reactive_system_stopped", {
                "metrics": self._metrics,
                "events_processed": len(self._reactive_state.event_history)
            })
    
    async def emit_event(
        self, 
        source: str, 
        event_type: str, 
        event_data: Dict[str, Any], 
        priority: int = 0
    ) -> None:
        """Emit an event to the reactive system"""
        if not self.enable_event_system or not self._running:
            return
            
        import time
        event = ReactiveEvent(
            event_type=event_type,
            event_data=event_data,
            timestamp=time.time(),
            source=source,
            priority=priority
        )
        
        await self._event_queue.put(event)
    
    def subscribe_to_event(self, event_type: str, handler: Callable[[ReactiveEvent], None]) -> None:
        """Subscribe to specific event types"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug(f"Subscribed to event type: {event_type}")
    
    async def _event_processing_loop(self) -> None:
        """Main event processing loop"""
        logger.info("Event processing loop started")
        
        while self._running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                
                # Process event
                await self._process_event(event)
                
                # Update metrics
                self._metrics['events_processed'] += 1
                
                # Maintain event buffer size
                if self._reactive_state and len(self._reactive_state.event_history) > self.event_buffer_size:
                    self._reactive_state.event_history = self._reactive_state.event_history[-self.event_buffer_size:]
                
            except asyncio.TimeoutError:
                # No events to process, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                if self.auto_recovery:
                    await self._handle_event_error(e)
    
    async def _process_event(self, event: ReactiveEvent) -> None:
        """Process a single event"""
        logger.debug(f"Processing event: {event.event_type} from {event.source}")
        
        # Add to history
        if self._reactive_state:
            self._reactive_state.event_history.append(event)
        
        # Call registered handlers
        handlers = self._event_handlers.get(event.event_type, [])
        handlers.extend(self._event_handlers.get('*', []))  # Global handlers
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event.event_type}: {e}")
        
        # Handle system events
        await self._handle_system_event(event)
    
    async def _handle_system_event(self, event: ReactiveEvent) -> None:
        """Handle system-level events"""
        if event.event_type == "browser_state_changed":
            await self._handle_state_change(event)
        elif event.event_type == "action_completed":
            await self._handle_action_completion(event)
        elif event.event_type == "error_occurred":
            await self._handle_error_event(event)
    
    async def _handle_state_change(self, event: ReactiveEvent) -> None:
        """Handle browser state changes"""
        if not self._reactive_state:
            return
            
        # Update current state
        new_state = event.event_data.get('new_state')
        if new_state:
            old_state = self._reactive_state.current_state
            self._reactive_state.current_state = new_state
            
            # Track state change
            self._reactive_state.state_changes.append({
                'timestamp': event.timestamp,
                'old_url': getattr(old_state, 'url', None),
                'new_url': getattr(new_state, 'url', None),
                'change_type': event.event_data.get('change_type', 'unknown')
            })
            
            self._metrics['state_changes'] += 1
            
            # Notify callback
            if self.state_change_callback:
                try:
                    self.state_change_callback(self._reactive_state)
                except Exception as e:
                    logger.error(f"Error in state change callback: {e}")
    
    async def _handle_action_completion(self, event: ReactiveEvent) -> None:
        """Handle action completion events"""
        result = event.event_data.get('result')
        action = event.event_data.get('action')
        
        logger.debug(f"Action completed: {action} -> {result}")
        
        # Can be overridden by subclasses for specific handling
        await self.on_action_completed(action, result)
    
    async def _handle_error_event(self, event: ReactiveEvent) -> None:
        """Handle error events"""
        error = event.event_data.get('error')
        context = event.event_data.get('context', {})
        
        logger.warning(f"Error event: {error} in context: {context}")
        
        if self.auto_recovery:
            await self._attempt_recovery(error, context)
    
    async def _handle_event_error(self, error: Exception) -> None:
        """Handle errors in event processing"""
        self._metrics['recovery_actions'] += 1
        
        await self.emit_event("system", "event_processing_error", {
            "error": str(error),
            "error_type": error.__class__.__name__
        })
    
    async def _attempt_recovery(self, error: Exception, context: Dict[str, Any]) -> None:
        """Attempt to recover from errors"""
        recovery_action = await self.get_recovery_action(error, context)
        
        if recovery_action:
            logger.info(f"Attempting recovery action: {recovery_action}")
            try:
                await self.execute_recovery_action(recovery_action, error, context)
                self._metrics['recovery_actions'] += 1
            except Exception as recovery_error:
                logger.error(f"Recovery action failed: {recovery_error}")
    
    # Abstract methods to be implemented by subclasses
    
    @abstractmethod
    async def reactive_step(self, step_info: Optional[Dict[str, Any]] = None) -> AgentOutput:
        """
        Execute a reactive step with event-driven capabilities.
        
        This method should be implemented by subclasses to define
        their specific reactive execution pattern.
        """
        pass
    
    @abstractmethod
    async def get_recovery_action(
        self, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Determine recovery action for a given error.
        
        Returns the name of the recovery action to execute,
        or None if no recovery is possible.
        """
        pass
    
    @abstractmethod
    async def execute_recovery_action(
        self, 
        action: str, 
        error: Exception, 
        context: Dict[str, Any]
    ) -> None:
        """Execute a recovery action"""
        pass
    
    # Hook methods that can be overridden
    
    async def on_action_completed(self, action: Any, result: ActionResult) -> None:
        """Called when an action is completed"""
        pass
    
    async def on_state_changed(self, old_state: BrowserState, new_state: BrowserState) -> None:
        """Called when browser state changes"""
        pass
    
    async def on_event_received(self, event: ReactiveEvent) -> None:
        """Called when any event is received"""
        pass
    
    # Enhanced step method with reactive capabilities
    
    async def step(self, step_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Enhanced step method with reactive capabilities.
        
        This overrides the parent step method to add event emission
        and reactive state management.
        """
        
        # Emit step start event
        await self.emit_event("agent", "step_started", {
            "step_number": self.n_steps,
            "step_info": step_info
        })
        
        try:
            # Capture state before step
            old_state = await self.browser_context.get_state()
            
            # Execute reactive step
            output = await self.reactive_step(step_info)
            
            # Capture state after step  
            new_state = await self.browser_context.get_state()
            
            # Emit state change event if state changed
            if old_state.url != new_state.url or old_state.title != new_state.title:
                await self.emit_event("browser", "browser_state_changed", {
                    "old_state": old_state,
                    "new_state": new_state,
                    "change_type": "navigation" if old_state.url != new_state.url else "content"
                })
            
            # Call parent step method for standard processing
            await super().step(step_info)
            
            # Emit step completion event
            await self.emit_event("agent", "step_completed", {
                "step_number": self.n_steps - 1,
                "output": output
            })
            
        except Exception as e:
            # Emit error event
            await self.emit_event("agent", "step_error", {
                "step_number": self.n_steps,
                "error": str(e),
                "error_type": e.__class__.__name__
            })
            raise
    
    async def run(self, max_steps: int = 100) -> AgentHistoryList:
        """
        Enhanced run method with reactive system lifecycle management.
        """
        
        try:
            # Start reactive system
            await self.start_reactive_system()
            
            # Run the agent
            result = await super().run(max_steps)
            
            return result
            
        finally:
            # Stop reactive system
            await self.stop_reactive_system()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self._metrics,
            "reactive_state": {
                "events_in_history": len(self._reactive_state.event_history) if self._reactive_state else 0,
                "active_listeners": len(self._event_handlers),
                "state_changes": len(self._reactive_state.state_changes) if self._reactive_state else 0
            }
        }