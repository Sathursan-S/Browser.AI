"""
WebSocket Server for Browser.AI Extension

Provides WebSocket endpoints for Chrome extension to communicate with Browser.AI agent
and control the browser via CDP.
"""

import asyncio
import logging
import threading
from typing import Optional, Set

from flask import Flask
from flask_socketio import SocketIO, emit

from .config import ConfigManager
from .event_adapter import EventAdapter, EventType, LogEvent, LogLevel
from .protocol import (
    ActionResult,
    StartTaskPayload,
    TaskStatus,
    create_action_result,
    create_task_status,
)
from browser_ai.agent.views import AgentHistoryList

logger = logging.getLogger(__name__)


class ExtensionTaskManager:
    """Manages Browser.AI tasks initiated from Chrome extension"""

    def __init__(
        self,
        config_manager: ConfigManager,
        event_adapter: EventAdapter,
        socketio: Optional[SocketIO] = None,
    ):
        self.config_manager = config_manager
        self.event_adapter = event_adapter
        self.socketio = socketio
        self.current_agent = None
        self.current_task = None
        self.is_running = False
        self.is_paused = False
        self.task_future: Optional[asyncio.Future] = None
        self.task_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._finalized = False
        self._finalize_lock = threading.Lock()
        self.browser = None
        self.cdp_endpoint = None

    def register_thread(self, thread: threading.Thread) -> None:
        """Register the thread running the agent so we can join/track it."""
        self.task_thread = thread
        self._stop_event.clear()

    async def start_task_with_cdp(
        self, task_description: str, cdp_endpoint: str
    ) -> ActionResult:
        """Start a new Browser.AI task using CDP connection to existing browser"""
        if self.is_running:
            return create_action_result(False, error="Task already running")

        try:
            # Import Browser.AI components
            from browser_ai import Agent, Browser, BrowserConfig

            # Create LLM instance
            llm = self.config_manager.get_llm_instance()

            # Create browser config with CDP connection
            self.cdp_endpoint = cdp_endpoint
            browser_config = BrowserConfig(
                cdp_url=cdp_endpoint, headless=False, disable_security=False
            )

            self.browser = Browser(config=browser_config)

            # Create agent
            self.current_agent = Agent(
                task=task_description,
                llm=llm,
                browser=self.browser,
                use_vision=self.config_manager.agent_config.use_vision,
                max_failures=self.config_manager.agent_config.max_failures,
                retry_delay=self.config_manager.agent_config.retry_delay,
                generate_gif=True,  # Enable GIF generation for extension
                validate_output=self.config_manager.agent_config.validate_output,
                register_done_callback=self._on_agent_done,
            )

            self.current_task = task_description
            self.is_running = True
            self.is_paused = False  # Reset pause state when starting new task

            # Emit custom event
            self.event_adapter.emit_custom_event(
                EventType.AGENT_START,
                f"Starting task: {task_description}",
                LogLevel.INFO,
                {"task": task_description, "cdp_endpoint": cdp_endpoint},
            )

            return create_action_result(True, message="Task started successfully")

        except Exception as e:
            logger.error(f"Failed to start task with CDP: {str(e)}", exc_info=True)
            self.is_running = False

            # Emit custom event to indicate failure
            self.event_adapter.emit_custom_event(
                EventType.AGENT_ERROR,
                f"Failed to start task: {str(e)}",
                LogLevel.ERROR,
                {"error": str(e)},
            )
            return create_action_result(False, error=str(e))

    async def start_task(self, task_description: str) -> ActionResult:
        """Start a new Browser.AI task with a new browser instance (for extension mode)"""
        if self.is_running:
            return create_action_result(False, error="Task already running")

        try:
            # Import Browser.AI components
            from browser_ai import Agent, Browser, BrowserConfig

            # Create LLM instance
            llm = self.config_manager.get_llm_instance()

            # Create browser config without CDP (new browser instance)
            browser_config = BrowserConfig(
                headless=False,
                disable_security=True,
                cdp_url="http://localhost:9222",
            )

            self.browser = Browser(config=browser_config)
            self.cdp_endpoint = "http://localhost:9222"

            # Create agent
            self.current_agent = Agent(
                task=task_description,
                llm=llm,
                browser=self.browser,
                use_vision=self.config_manager.agent_config.use_vision,
                max_failures=self.config_manager.agent_config.max_failures,
                retry_delay=self.config_manager.agent_config.retry_delay,
                generate_gif=True,  # Enable GIF generation for extension
                validate_output=self.config_manager.agent_config.validate_output,
                register_done_callback=self._on_agent_done,
            )

            self.current_task = task_description
            self.is_running = True
            self.is_paused = False  # Reset pause state when starting new task

            # Emit custom event
            self.event_adapter.emit_custom_event(
                EventType.AGENT_START,
                f"Starting task: {task_description}",
                LogLevel.INFO,
                {"task": task_description, "mode": "extension"},
            )

            return create_action_result(True, message="Task started successfully")

        except Exception as e:
            logger.error(f"Failed to start task: {str(e)}", exc_info=True)
            self.is_running = False
            # Emit custom event to indicate failure
            self.event_adapter.emit_custom_event(
                EventType.AGENT_ERROR,
                f"Failed to start task: {str(e)}",
                LogLevel.ERROR,
                {"error": str(e)},
            )

            return create_action_result(False, error=str(e))

    async def run_task(self):
        """Run the current agent task"""
        if not self.current_agent:
            return

        try:
            self.is_running = True
            self.is_paused = False
            # Broadcast initial running status
            try:
                if self.socketio:
                    self.socketio.emit(
                        "status", self.get_status().to_dict(), namespace="/extension"
                    )
            except Exception:
                logger.exception("Failed to emit initial running status")
            history: AgentHistoryList = await self.current_agent.run(
                max_steps=self.config_manager.agent_config.max_steps
            )

            # Emit completion event (structured)
            try:
                self.event_adapter.emit_custom_event(
                    EventType.AGENT_COMPLETE,
                    "Task completed",
                    LogLevel.INFO,
                    {"result": str(history)},
                )
            except Exception:
                logger.exception("Failed to emit AGENT_COMPLETE event")

            # Finalize and cleanup based on history
            await self._finalize_task(history)
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}", exc_info=True)
            try:
                self.event_adapter.emit_custom_event(
                    EventType.AGENT_ERROR,
                    f"Task failed: {str(e)}",
                    LogLevel.ERROR,
                    {"error": str(e)},
                )
            except Exception:
                logger.exception("Failed to emit AGENT_ERROR event")

            # Ensure finalize is called for cleanup
            try:
                await self._finalize_task(None)
            except Exception:
                logger.exception("Error during finalize after exception")

    async def _finalize_task(self, history: Optional[AgentHistoryList]):
        """Centralized cleanup after agent finishes or errors.

        Emits structured task_result and final status to clients and performs cleanup.
        """
        # Ensure status flags are cleared before emitting
        self.is_running = False
        self.is_paused = False

        # Prevent double-finalize
        with self._finalize_lock:
            if self._finalized:
                self.socketio.emit(
                    "status", self.get_status().to_dict(), namespace="/extension"
                )
                logger.debug("_finalize_task called but already finalized; skipping")
                return
            self._finalized = True

        # Determine success
        success = False
        if history is not None:
            try:
                success = getattr(history, "is_done", lambda: False)()
            except Exception:
                success = False

        # Emit task_result to clients
        try:
            payload = {
                "task": self.current_task,
                "success": bool(success),
                "history": str(history) if history is not None else None,
            }
            if self.socketio:
                self.socketio.emit("task_result", payload, namespace="/extension")
                self.socketio.emit(
                    "status", self.get_status().to_dict(), namespace="/extension"
                )
            else:
                emit("task_result", payload)
                emit("status", self.get_status().to_dict())
        except Exception:
            logger.exception("Failed to emit final task_result/status")

        # Also publish via event adapter for internal logging
        try:
            if success:
                print("Task completed successfully")
                # self.event_adapter.emit_custom_event(
                #     EventType.AGENT_COMPLETE,
                #     "Task completed successfully",
                #     LogLevel.INFO,
                #     {"task": self.current_task},
                # )
            else:
                self.event_adapter.emit_custom_event(
                    EventType.AGENT_ERROR,
                    "Task ended without success",
                    LogLevel.WARNING,
                    {"task": self.current_task},
                )
        except Exception:
            logger.exception("Failed to emit final event via event_adapter")

        # Ensure browser closed (best-effort)
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                logger.exception("Failed to close browser during finalize")

        # Clear current task and agent
        self.current_task = None
        self.current_agent = None

        # Clear finalized flag for next task
        self._finalized = False

        logger.info("Task finalized")

    def _on_agent_done(self, history: AgentHistoryList):
        """Callback passed to Agent to notify manager that the run finished.

        This callback may be invoked inside the Agent's async context. We schedule
        the async finalize on the running loop when possible, otherwise run it in
        a background thread.
        """
        try:
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # no running loop in this thread
                loop = None

            if loop and loop.is_running():
                # schedule coroutine in the current loop
                asyncio.ensure_future(self._finalize_task(history))
            else:
                # schedule in a new thread with its own loop
                def _run():
                    try:
                        asyncio.run(self._finalize_task(history))
                    except Exception:
                        logger.exception("Unhandled exception in _on_agent_done runner")

                t = threading.Thread(target=_run, daemon=True)
                # register thread so lifecycle tracking remains consistent
                self.register_thread(t)
                t.start()
        except Exception:
            logger.exception("Error handling agent done callback")

    def stop_task(self) -> ActionResult:
        """Stop the current task"""
        if not self.is_running or not self.current_agent:
            return create_action_result(False, error="No task running")

        try:
            self.current_agent.stop()
            self.is_paused = False  # Reset pause state
            self.event_adapter.emit_custom_event(
                EventType.AGENT_STOP, "Task stopped by user", LogLevel.INFO
            )
            # Attempt a short join of the background thread to allow it to finish cleanup
            try:
                if self.task_thread and self.task_thread.is_alive():
                    self.task_thread.join(timeout=2)
                    if self.task_thread.is_alive():
                        logger.warning(
                            "Task thread did not exit after stop() within timeout"
                        )
            except Exception:
                logger.exception("Error while joining task thread after stop")
            return create_action_result(True, message="Task stopped successfully")
        except Exception as e:
            return create_action_result(False, error=str(e))

    def pause_task(self) -> ActionResult:
        """Pause the current task"""
        if not self.is_running or not self.current_agent:
            return create_action_result(False, error="No task running")

        try:
            self.current_agent.pause()
            self.is_paused = True  # Track pause state
            self.event_adapter.emit_custom_event(
                EventType.AGENT_PAUSE, "Task paused by user", LogLevel.INFO
            )
            return create_action_result(True, message="Task paused successfully")
        except Exception as e:
            return create_action_result(False, error=str(e))

    def resume_task(self) -> ActionResult:
        """Resume the current task"""
        if not self.is_running or not self.current_agent:
            return create_action_result(False, error="No task to resume")

        try:
            self.current_agent.resume()
            self.is_paused = False  # Track pause state
            self.event_adapter.emit_custom_event(
                EventType.AGENT_RESUME, "Task resumed by user", LogLevel.INFO
            )
            return create_action_result(True, message="Task resumed successfully")
        except Exception as e:
            return create_action_result(False, error=str(e))

    def get_status(self) -> TaskStatus:
        """Get current task status"""
        return create_task_status(
            is_running=self.is_running,
            current_task=self.current_task,
            has_agent=self.current_agent is not None,
            is_paused=self.is_paused,
            cdp_endpoint=self.cdp_endpoint,
        )


class ExtensionWebSocketHandler:
    """Handles WebSocket connections from Chrome extension"""

    def __init__(
        self,
        socketio: SocketIO,
        config_manager: ConfigManager,
        event_adapter: EventAdapter,
    ):
        self.socketio = socketio
        self.config_manager = config_manager
        self.event_adapter = event_adapter
        # Pass socketio into the task manager so it can emit from background threads
        self.task_manager = ExtensionTaskManager(
            config_manager, event_adapter, socketio
        )
        self.connected_clients: Set[str] = set()

        # Setup WebSocket event handlers
        self._setup_handlers()

    def _setup_handlers(self):
        """Setup SocketIO event handlers for extension"""

        @self.socketio.on("extension_connect", namespace="/extension")
        def handle_extension_connect():
            """Handle extension client connection"""
            from flask import request

            client_id = request.sid
            self.connected_clients.add(client_id)
            logger.info(f"Extension client connected: {client_id}")

            # Send current status
            status = self.task_manager.get_status()
            emit("status", status.to_dict())

            # Send recent events
            recent_events = self.event_adapter.get_recent_events(50)
            for event in recent_events:
                emit("log_event", event.to_dict())

        @self.socketio.on("disconnect", namespace="/extension")
        def handle_extension_disconnect():
            """Handle extension client disconnection"""
            from flask import request

            client_id = request.sid
            if client_id in self.connected_clients:
                self.connected_clients.remove(client_id)
            logger.info(f"Extension client disconnected: {client_id}")

        @self.socketio.on("start_task", namespace="/extension")
        def handle_start_task(data):
            """Handle task start request from extension"""
            payload = StartTaskPayload.from_dict(data)

            if not payload.task:
                emit("error", {"message": "Task description is required"})
                return

            # For extension mode, we can't use CDP, so use regular browser mode
            if (
                payload.is_extension
                or not payload.cdp_endpoint
                or payload.cdp_endpoint == "extension-proxy"
            ):
                # Start task without CDP connection
                def run_task():
                    asyncio.run(start_and_run())

                async def start_and_run():
                    result = await self.task_manager.start_task(payload.task)
                    if result.success:
                        await self.task_manager.run_task()

                import threading

                task_thread = threading.Thread(target=run_task)
                task_thread.daemon = True
                # register thread so manager can join/track it
                self.task_manager.register_thread(task_thread)
                task_thread.start()
                emit(
                    "task_started", {"message": "Task is starting in extension mode..."}
                )
                emit("status", self.task_manager.get_status().to_dict())
                return

            if not payload.cdp_endpoint:
                emit("error", {"message": "CDP endpoint is required"})
                return

            # Start task with CDP connection for non-extension mode
            def run_task():
                asyncio.run(start_and_run())

            async def start_and_run():
                result = await self.task_manager.start_task_with_cdp(
                    payload.task, payload.cdp_endpoint
                )
                if result.success:
                    await self.task_manager.run_task()

            import threading

            task_thread = threading.Thread(target=run_task)
            task_thread.daemon = True
            # register thread so manager can join/track it
            self.task_manager.register_thread(task_thread)
            task_thread.start()

            emit("task_started", {"message": "Task is starting..."})

        @self.socketio.on("stop_task", namespace="/extension")
        def handle_stop_task():
            """Handle task stop request from extension"""
            result = self.task_manager.stop_task()
            emit("task_action_result", result.to_dict())
            # Broadcast updated status to all clients
            status = self.task_manager.get_status()
            self.socketio.emit("status", status.to_dict(), namespace="/extension")

        @self.socketio.on("pause_task", namespace="/extension")
        def handle_pause_task():
            """Handle task pause request from extension"""
            result = self.task_manager.pause_task()
            emit("task_action_result", result.to_dict())
            # Broadcast updated status to all clients
            status = self.task_manager.get_status()
            self.socketio.emit("status", status.to_dict(), namespace="/extension")

        @self.socketio.on("resume_task", namespace="/extension")
        def handle_resume_task():
            """Handle task resume request from extension"""
            result = self.task_manager.resume_task()
            emit("task_action_result", result.to_dict())
            # Broadcast updated status to all clients
            status = self.task_manager.get_status()
            self.socketio.emit("status", status.to_dict(), namespace="/extension")

        @self.socketio.on("get_status", namespace="/extension")
        def handle_get_status():
            """Handle status request from extension"""
            status = self.task_manager.get_status()
            emit("status", status.to_dict())

    def broadcast_event(self, event: LogEvent):
        """Broadcast event to all connected extension clients"""
        self.socketio.emit("log_event", event.to_dict(), namespace="/extension")


def setup_extension_websocket(
    app: Flask,
    socketio: SocketIO,
    config_manager: ConfigManager,
    event_adapter: EventAdapter,
) -> ExtensionWebSocketHandler:
    """Setup WebSocket handlers for Chrome extension"""
    handler = ExtensionWebSocketHandler(socketio, config_manager, event_adapter)

    # Subscribe to event adapter to broadcast to extension clients
    event_adapter.subscribe(handler.broadcast_event)

    return handler
