"""
WebSocket Server for Browser.AI Extension

Provides WebSocket endpoints for Chrome extension to communicate with Browser.AI agent
and control t            self.browser = Browser(config=browser_config)

            # Reset stuck detector for new task
            self.stuck_detector.reset()

            # Create agent
            self.current_agent = Agent(
                task=task_description,
                llm=llm,
                browser=self.browser,
                use_vision=self.config_manager.agent_config.use_vision,
                max_failures=self.config_manager.agent_config.max_failures,
                retry_delay=self.config_manager.agent_config.retry_delay,
                generate_gif=False,  # Disable GIF generation for extension
                validate_output=self.config_manager.agent_config.validate_output,
                register_done_callback=self._on_agent_done,
                register_new_step_callback=self._on_agent_step,
            )

            self.current_task = task_description
            self.is_running = True
            self.is_paused = False  # Reset pause state when starting new task.
"""

import asyncio
import logging
import threading
from typing import Optional, Set

from flask import Flask
from flask_socketio import SocketIO, emit

from .config import ConfigManager
from .event_adapter import EventAdapter, EventType, LogEvent, LogLevel
from .chatbot_service import ChatbotService, ConversationMessage, ChatbotIntent
from .stuck_detector import StuckDetector, StuckDetectionConfig
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

        # Stuck detection
        self.stuck_detector = StuckDetector(StuckDetectionConfig())
        self.awaiting_user_help = False
        self.user_help_response: Optional[str] = None

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

            # Reset stuck detector for new task
            self.stuck_detector.reset()

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
                register_new_step_callback=self._on_agent_step,
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
                await self.browser.close()
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

    async def request_user_help(self, stuck_report) -> Optional[str]:
        """Request help from user when agent is stuck"""
        if not self.socketio:
            logger.warning("Cannot request user help: no socketio connection")
            return None

        self.awaiting_user_help = True
        self.user_help_response = None

        # Emit help request to the extension
        help_payload = {
            "reason": stuck_report.reason,
            "summary": stuck_report.detailed_summary,
            "attempted_actions": stuck_report.attempted_actions,
            "duration": int(stuck_report.duration_seconds),
            "suggestion": stuck_report.suggestion,
        }

        logger.info(f"🆘 Requesting user help: {stuck_report.reason}")

        # Emit to extension
        self.socketio.emit("agent_needs_help", help_payload, namespace="/extension")

        # Emit as chat message for conversational interface
        self.socketio.emit(
            "chat_response",
            {"message": stuck_report.detailed_summary, "isIntent": False},
            namespace="/extension",
        )

        # Wait for user response (with timeout)
        timeout = 300  # 5 minutes
        start_time = asyncio.get_event_loop().time()

        while self.awaiting_user_help and self.user_help_response is None:
            await asyncio.sleep(1)
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.warning("User help request timed out")
                self.awaiting_user_help = False
                return None

        response = self.user_help_response
        self.user_help_response = None
        self.awaiting_user_help = False

        return response

    def provide_help_response(self, response: str):
        """Called when user provides help response"""
        self.user_help_response = response
        logger.info(f"📝 User provided help: {response[:100]}...")

    def _on_agent_step(self, state, output, step_num):
        """Callback invoked after each agent step to check for stuck state"""
        # Start the step timer
        self.stuck_detector.start_step()

        # Record all actions from this step
        if hasattr(output, "action") and output.action:
            for action_dict in output.action:
                for action_name, action_params in action_dict.items():
                    # Determine if action was successful (simplified check)
                    success = not (hasattr(output, "error") and output.error)
                    error_msg = output.error if hasattr(output, "error") else None

                    self.stuck_detector.record_action(
                        action_name=action_name,
                        success=success,
                        error_message=error_msg,
                        metadata={"step": step_num},
                    )

        # Check if agent is stuck periodically (every 3 steps)
        if step_num % 3 == 0:
            stuck_report = self.stuck_detector.check_if_stuck()

            if stuck_report.is_stuck:
                logger.warning(f"🆘 Agent appears stuck: {stuck_report.reason}")

                # Request help asynchronously (don't block)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        asyncio.create_task(self.request_user_help(stuck_report))
                except RuntimeError:
                    # If no event loop, we can't request help
                    logger.warning("Cannot request help: no event loop available")


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

        # Initialize chatbot service
        api_key = (
            getattr(config_manager.llm_config.api_key, "_secret_value", None)
            if hasattr(config_manager.llm_config.api_key, "_secret_value")
            else config_manager.llm_config.api_key
        )
        self.chatbot = ChatbotService(api_key=api_key)
        logger.info("Chatbot service initialized for conversational task clarification")

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

        @self.socketio.on("chat_message", namespace="/extension")
        def handle_chat_message(data):
            """Handle chat message from user for intent clarification"""
            from flask import request

            session_id = request.sid
            user_message = data.get("message", "").strip()

            if not user_message:
                emit(
                    "chat_response",
                    {
                        "role": "assistant",
                        "content": "Please provide a message.",
                        "intent": None,
                    },
                )
                return

            # Process message through chatbot
            response_msg, intent = self.chatbot.process_message(
                session_id, user_message
            )

            # Prepare response
            response_data = {
                "role": response_msg.role,
                "content": response_msg.content,
                "intent": None,
            }

            # If intent is ready, include it
            if intent and intent.is_ready:
                response_data["intent"] = {
                    "task_description": intent.task_description,
                    "is_ready": intent.is_ready,
                    "confidence": intent.confidence,
                }

                logger.info(f"Chatbot clarified intent: {intent.task_description}")

                # Emit event indicating task is ready to start
                self.event_adapter.emit_custom_event(
                    EventType.AGENT_START,
                    f"Task clarified through conversation: {intent.task_description}",
                    LogLevel.INFO,
                    {"task": intent.task_description},
                )

            emit("chat_response", response_data)

        @self.socketio.on("start_clarified_task", namespace="/extension")
        def handle_start_clarified_task(data):
            """Handle starting a task that was clarified through chat"""
            task_description = data.get("task", "").strip()
            cdp_endpoint = data.get("cdp_endpoint", "")
            is_extension = data.get("is_extension", True)

            if not task_description:
                emit("error", {"message": "Task description is required"})
                return

            logger.info(f"Starting clarified task: {task_description}")

            # Use the same logic as start_task
            if is_extension or not cdp_endpoint or cdp_endpoint == "extension-proxy":
                # Start task without CDP connection
                def run_task():
                    asyncio.run(start_and_run())

                async def start_and_run():
                    result = await self.task_manager.start_task(task_description)
                    if result.success:
                        await self.task_manager.run_task()

                import threading

                task_thread = threading.Thread(target=run_task)
                task_thread.daemon = True
                self.task_manager.register_thread(task_thread)
                task_thread.start()

                emit("task_started", {"message": f"Starting task: {task_description}"})
                emit("status", self.task_manager.get_status().to_dict())
                return

            # Start task with CDP if available
            def run_task():
                asyncio.run(start_and_run())

            async def start_and_run():
                result = await self.task_manager.start_task_with_cdp(
                    task_description, cdp_endpoint
                )
                if result.success:
                    await self.task_manager.run_task()

            import threading

            task_thread = threading.Thread(target=run_task)
            task_thread.daemon = True
            self.task_manager.register_thread(task_thread)
            task_thread.start()

            emit("task_started", {"message": f"Starting task: {task_description}"})
            emit("status", self.task_manager.get_status().to_dict())

        @self.socketio.on("user_help_response", namespace="/extension")
        def handle_user_help_response(data):
            """Handle user's response to agent stuck help request"""
            response = data.get("response", "").strip()

            if not response:
                emit("error", {"message": "Please provide a response"})
                return

            logger.info(f"📬 Received user help response: {response[:100]}...")

            # Provide the response to task manager
            self.task_manager.provide_help_response(response)

            # Acknowledge receipt
            emit(
                "help_response_received",
                {"message": "Thank you! The agent will continue with your guidance."},
            )

            # Log the event
            self.event_adapter.emit_custom_event(
                EventType.AGENT_RESUME,
                f"User provided help: {response[:100]}...",
                LogLevel.INFO,
                {"help_response": response},
            )

        @self.socketio.on("reset_conversation", namespace="/extension")
        def handle_reset_conversation():
            """Handle conversation reset request"""
            from flask import request

            session_id = request.sid
            greeting = self.chatbot.reset_conversation(session_id)

            emit(
                "conversation_reset",
                {"role": greeting.role, "content": greeting.content},
            )

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
