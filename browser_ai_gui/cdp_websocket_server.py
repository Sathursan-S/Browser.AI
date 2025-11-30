"""
CDP WebSocket Server for Browser.AI Extension

Provides a dedicated WebSocket server for Chrome extension to control
browser context via Chrome DevTools Protocol (CDP).

This server acts as a proxy between the Chrome extension and the browser context,
allowing the extension to send CDP commands and receive responses through WebSocket.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from flask import Flask
from flask_socketio import Namespace, SocketIO, emit

from .config import ConfigManager
from .event_adapter import EventAdapter, EventType, LogEvent, LogLevel

logger = logging.getLogger(__name__)


@dataclass
class CDPCommand:
    """CDP command from extension"""

    command_id: str
    tab_id: int
    method: str
    params: Optional[Dict[str, Any]] = None


@dataclass
class CDPResponse:
    """CDP response to extension"""

    command_id: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class CDPBrowserContextManager:
    """Manages browser context connections via CDP for extension tabs"""

    def __init__(self, config_manager: ConfigManager, event_adapter: EventAdapter):
        self.config_manager = config_manager
        self.event_adapter = event_adapter

        # Map of tab_id -> Browser instance
        self.tab_browsers: Dict[int, Any] = {}

        # Map of tab_id -> BrowserContext instance
        self.tab_contexts: Dict[int, Any] = {}

        # Map of tab_id -> active Agent instance
        self.tab_agents: Dict[int, Any] = {}

        # Track active tasks per tab
        self.active_tasks: Dict[int, str] = {}

        # Track command responses
        self.pending_commands: Dict[str, asyncio.Future] = {}

    async def attach_to_tab(self, tab_id: int, cdp_url: str) -> Dict[str, Any]:
        """Attach to a browser tab via CDP"""
        try:
            # Import Browser.AI components
            from browser_ai import Browser, BrowserConfig

            # Create browser config with CDP connection
            browser_config = BrowserConfig(
                cdp_url=cdp_url, headless=False, disable_security=False
            )

            # Create browser instance for this tab
            browser = Browser(config=browser_config)

            # Store the browser instance
            self.tab_browsers[tab_id] = browser

            logger.info(f"Attached to tab {tab_id} via CDP: {cdp_url}")

            self.event_adapter.emit_custom_event(
                EventType.AGENT_START,
                f"Attached to browser tab {tab_id}",
                LogLevel.INFO,
                {"tab_id": tab_id, "cdp_url": cdp_url},
            )

            return {
                "success": True,
                "message": f"Successfully attached to tab {tab_id}",
                "tab_id": tab_id,
            }

        except Exception as e:
            logger.error(f"Failed to attach to tab {tab_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "tab_id": tab_id}

    async def detach_from_tab(self, tab_id: int) -> Dict[str, Any]:
        """Detach from a browser tab"""
        try:
            # Stop any active task
            if tab_id in self.tab_agents:
                # TODO: Stop the agent gracefully
                del self.tab_agents[tab_id]

            # Close browser context
            if tab_id in self.tab_contexts:
                # Context cleanup handled by browser
                del self.tab_contexts[tab_id]

            # Close browser instance
            if tab_id in self.tab_browsers:
                # Browser cleanup
                del self.tab_browsers[tab_id]

            if tab_id in self.active_tasks:
                del self.active_tasks[tab_id]

            logger.info(f"Detached from tab {tab_id}")

            return {
                "success": True,
                "message": f"Successfully detached from tab {tab_id}",
                "tab_id": tab_id,
            }

        except Exception as e:
            logger.error(f"Failed to detach from tab {tab_id}: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e), "tab_id": tab_id}

    async def send_cdp_command(self, cdp_command: CDPCommand) -> CDPResponse:
        """Send a CDP command to the browser context"""
        try:
            tab_id = cdp_command.tab_id

            # Check if we have a browser for this tab
            if tab_id not in self.tab_browsers:
                return CDPResponse(
                    command_id=cdp_command.command_id,
                    success=False,
                    error=f"No browser attached to tab {tab_id}",
                )

            browser = self.tab_browsers[tab_id]

            # Get the playwright browser
            playwright_browser = await browser.get_playwright_browser()

            # Get the first context (CDP connection should have one)
            contexts = playwright_browser.contexts
            if not contexts:
                return CDPResponse(
                    command_id=cdp_command.command_id,
                    success=False,
                    error="No browser context available",
                )

            context = contexts[0]

            # Get the first page from context
            pages = context.pages
            if not pages:
                return CDPResponse(
                    command_id=cdp_command.command_id,
                    success=False,
                    error="No page available in context",
                )

            page = pages[0]

            # Send CDP command via Playwright's CDP session
            cdp_session = await context.new_cdp_session(page)
            result = await cdp_session.send(
                cdp_command.method, cdp_command.params or {}
            )

            logger.debug(
                f"CDP command {cdp_command.method} executed successfully for tab {tab_id}"
            )

            return CDPResponse(
                command_id=cdp_command.command_id, success=True, result=result
            )

        except Exception as e:
            logger.error(
                f"Failed to execute CDP command {cdp_command.method} for tab {cdp_command.tab_id}: {str(e)}",
                exc_info=True,
            )
            return CDPResponse(
                command_id=cdp_command.command_id, success=False, error=str(e)
            )

    async def start_task_on_tab(
        self, tab_id: int, task_description: str
    ) -> Dict[str, Any]:
        """Start a Browser.AI task on a specific tab"""
        try:
            if tab_id not in self.tab_browsers:
                return {
                    "success": False,
                    "error": f"No browser attached to tab {tab_id}",
                }

            if tab_id in self.active_tasks:
                return {
                    "success": False,
                    "error": f"Task already running on tab {tab_id}",
                }

            # Import Browser.AI Agent
            from browser_ai import Agent

            # Create LLM instance
            llm = self.config_manager.get_llm_instance()

            browser = self.tab_browsers[tab_id]

            # Create agent for this tab
            agent = Agent(
                task=task_description,
                llm=llm,
                browser=browser,
                use_vision=self.config_manager.agent_config.use_vision,
                max_failures=self.config_manager.agent_config.max_failures,
                retry_delay=self.config_manager.agent_config.retry_delay,
                generate_gif=False,  # Disable GIF generation for extension
                validate_output=self.config_manager.agent_config.validate_output,
            )

            self.tab_agents[tab_id] = agent
            self.active_tasks[tab_id] = task_description

            logger.info(f"Started task on tab {tab_id}: {task_description}")

            self.event_adapter.emit_custom_event(
                EventType.AGENT_START,
                f"Starting task on tab {tab_id}: {task_description}",
                LogLevel.INFO,
                {"tab_id": tab_id, "task": task_description},
            )

            return {
                "success": True,
                "message": "Task started successfully",
                "tab_id": tab_id,
                "task": task_description,
            }

        except Exception as e:
            logger.error(
                f"Failed to start task on tab {tab_id}: {str(e)}", exc_info=True
            )
            return {"success": False, "error": str(e), "tab_id": tab_id}

    async def run_task_on_tab(self, tab_id: int) -> Dict[str, Any]:
        """Execute the agent task on a specific tab"""
        try:
            if tab_id not in self.tab_agents:
                return {"success": False, "error": f"No agent found for tab {tab_id}"}

            agent = self.tab_agents[tab_id]

            # Run the agent
            result = await agent.run(
                max_steps=self.config_manager.agent_config.max_steps
            )

            # Clean up after completion
            del self.tab_agents[tab_id]
            del self.active_tasks[tab_id]

            logger.info(f"Task completed on tab {tab_id}")

            self.event_adapter.emit_custom_event(
                EventType.AGENT_COMPLETE,
                f"Task completed on tab {tab_id}",
                LogLevel.INFO,
                {"tab_id": tab_id, "result": str(result)},
            )

            return {
                "success": True,
                "message": "Task completed successfully",
                "tab_id": tab_id,
                "result": str(result),
            }

        except Exception as e:
            logger.error(f"Failed to run task on tab {tab_id}: {str(e)}", exc_info=True)

            # Clean up on error
            if tab_id in self.tab_agents:
                del self.tab_agents[tab_id]
            if tab_id in self.active_tasks:
                del self.active_tasks[tab_id]

            return {"success": False, "error": str(e), "tab_id": tab_id}

    def get_tab_status(self, tab_id: int) -> Dict[str, Any]:
        """Get status of a specific tab"""
        return {
            "tab_id": tab_id,
            "is_attached": tab_id in self.tab_browsers,
            "has_agent": tab_id in self.tab_agents,
            "current_task": self.active_tasks.get(tab_id),
            "is_running": tab_id in self.active_tasks,
        }


class CDPWebSocketNamespace(Namespace):
    """WebSocket namespace for CDP extension communication"""

    def __init__(
        self,
        namespace: str,
        cdp_manager: CDPBrowserContextManager,
        event_adapter: EventAdapter,
    ):
        super().__init__(namespace)
        self.cdp_manager = cdp_manager
        self.event_adapter = event_adapter
        self.connected_clients: Set[str] = set()

    def on_connect(self):
        """Handle client connection"""
        from flask import request

        client_id = request.sid
        self.connected_clients.add(client_id)
        logger.info(f"CDP Extension client connected: {client_id}")
        emit("connected", {"client_id": client_id})

    def on_disconnect(self):
        """Handle client disconnection"""
        from flask import request

        client_id = request.sid
        if client_id in self.connected_clients:
            self.connected_clients.remove(client_id)
        logger.info(f"CDP Extension client disconnected: {client_id}")

    def on_attach_tab(self, data):
        """Handle tab attachment request"""
        tab_id = data.get("tab_id")
        cdp_url = data.get("cdp_url")

        if not tab_id:
            emit("error", {"message": "Tab ID is required"})
            return

        if not cdp_url:
            emit("error", {"message": "CDP URL is required"})
            return

        # Attach in background thread
        def run_attach():
            asyncio.run(attach_and_respond())

        async def attach_and_respond():
            result = await self.cdp_manager.attach_to_tab(tab_id, cdp_url)
            emit("attach_result", result)

        import threading

        thread = threading.Thread(target=run_attach)
        thread.daemon = True
        thread.start()

    def on_detach_tab(self, data):
        """Handle tab detachment request"""
        tab_id = data.get("tab_id")

        if not tab_id:
            emit("error", {"message": "Tab ID is required"})
            return

        # Detach in background thread
        def run_detach():
            asyncio.run(detach_and_respond())

        async def detach_and_respond():
            result = await self.cdp_manager.detach_from_tab(tab_id)
            emit("detach_result", result)

        import threading

        thread = threading.Thread(target=run_detach)
        thread.daemon = True
        thread.start()

    def on_send_cdp_command(self, data):
        """Handle CDP command from extension"""
        command_id = data.get("command_id", str(uuid.uuid4()))
        tab_id = data.get("tab_id")
        method = data.get("method")
        params = data.get("params", {})

        if not tab_id or not method:
            emit(
                "cdp_response",
                {
                    "command_id": command_id,
                    "success": False,
                    "error": "Tab ID and method are required",
                },
            )
            return

        cdp_command = CDPCommand(
            command_id=command_id, tab_id=tab_id, method=method, params=params
        )

        # Execute command in background thread
        def run_command():
            asyncio.run(execute_and_respond())

        async def execute_and_respond():
            response = await self.cdp_manager.send_cdp_command(cdp_command)
            emit(
                "cdp_response",
                {
                    "command_id": response.command_id,
                    "success": response.success,
                    "result": response.result,
                    "error": response.error,
                },
            )

        import threading

        thread = threading.Thread(target=run_command)
        thread.daemon = True
        thread.start()

    def on_start_task(self, data):
        """Handle task start request"""
        tab_id = data.get("tab_id")
        task = data.get("task")

        if not tab_id or not task:
            emit("error", {"message": "Tab ID and task are required"})
            return

        # Start and run task in background thread
        def run_task():
            asyncio.run(start_and_run())

        async def start_and_run():
            # Start task
            start_result = await self.cdp_manager.start_task_on_tab(tab_id, task)
            emit("task_started", start_result)

            if start_result["success"]:
                # Run the task
                run_result = await self.cdp_manager.run_task_on_tab(tab_id)
                emit("task_completed", run_result)

        import threading

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

    def on_get_tab_status(self, data):
        """Handle tab status request"""
        tab_id = data.get("tab_id")

        if not tab_id:
            emit("error", {"message": "Tab ID is required"})
            return

        status = self.cdp_manager.get_tab_status(tab_id)
        emit("tab_status", status)

    def broadcast_log_event(self, event: LogEvent):
        """Broadcast log event to all connected clients"""
        if not self.connected_clients:
            return

        event_data = {
            "timestamp": event.timestamp,
            "level": event.level.value,
            "message": event.message,
            "event_type": event.event_type.value,
            "metadata": event.metadata or {},
        }

        emit("log_event", event_data, namespace=self.namespace, broadcast=True)


def setup_cdp_websocket(
    app: Flask,
    socketio: SocketIO,
    config_manager: ConfigManager,
    event_adapter: EventAdapter,
) -> CDPWebSocketNamespace:
    """Setup CDP WebSocket server for extension"""

    # Create CDP manager
    cdp_manager = CDPBrowserContextManager(config_manager, event_adapter)

    # Create and register namespace
    cdp_namespace = CDPWebSocketNamespace("/cdp", cdp_manager, event_adapter)
    socketio.on_namespace(cdp_namespace)

    # Subscribe to event adapter to broadcast logs
    event_adapter.subscribe(cdp_namespace.broadcast_log_event)

    logger.info("CDP WebSocket server initialized on /cdp namespace")

    return cdp_namespace
