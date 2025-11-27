"""
Web Application for Browser.AI GUI

Flask-based web application with WebSocket support for real-time log streaming
and chat-based task management.

Includes JARVIS voice conversation mode for natural language interaction.
"""

import asyncio
import os
import threading
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit

from .cdp_websocket_server import setup_cdp_websocket
from .config import ConfigManager
from .event_adapter import EventAdapter, LogEvent
from .services.task_manager import TaskManager
from .services.voice_conversation import VoiceConversationService
from .websocket_server import ExtensionWebSocketHandler, setup_extension_websocket


class WebApp:
    """Web application for Browser.AI GUI"""

    def __init__(
        self, config_manager: Optional[ConfigManager] = None, port: int = 5000
    ):
        self.port = port
        self.config_manager = config_manager or ConfigManager()
        self.event_adapter = EventAdapter()
        self.task_manager = TaskManager(self.config_manager, self.event_adapter)
        
        # Initialize JARVIS voice conversation service
        self.voice_service = VoiceConversationService(
            api_key=os.getenv("GEMINI_API_KEY"),
            on_task_ready=self._on_task_ready
        )

        # Create Flask app
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = "browser-ai-gui-secret-key"
        self.socketio = SocketIO(
            self.app, cors_allowed_origins="*", async_mode="threading"
        )

        # Setup routes
        self._setup_routes()
        self._setup_jarvis_routes()
        self._setup_socketio_events()

        # Setup WebSocket handler for Chrome extension (legacy)
        self.extension_handler: Optional[ExtensionWebSocketHandler] = (
            setup_extension_websocket(
                self.app, self.socketio, self.config_manager, self.event_adapter
            )
        )

        # Setup CDP WebSocket server for extension (new)
        self.cdp_handler = setup_cdp_websocket(
            self.app, self.socketio, self.config_manager, self.event_adapter
        )

        # Start event adapter
        self.event_adapter.start()
        self.event_adapter.subscribe(self._on_log_event)
    
    def _on_task_ready(self, task_plan):
        """Callback when JARVIS has prepared a task plan"""
        # Emit socket event for real-time update
        self.socketio.emit("task_ready", {
            "description": task_plan.description,
            "confidence": task_plan.confidence,
            "language": task_plan.language
        })

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def index():
            return render_template("index.html")

        @self.app.route("/static/<path:filename>")
        def static_files(filename):
            return send_from_directory("static", filename)

        @self.app.route("/api/config", methods=["GET"])
        def get_config():
            return jsonify(
                {
                    "llm": {
                        "provider": self.config_manager.llm_config.provider,
                        "model": self.config_manager.llm_config.model,
                        "temperature": getattr(
                            self.config_manager.llm_config, "temperature", 0.1
                        ),
                        "max_tokens": getattr(
                            self.config_manager.llm_config, "max_tokens", None
                        ),
                        "timeout": getattr(
                            self.config_manager.llm_config, "timeout", 30
                        ),
                        "base_url": getattr(
                            self.config_manager.llm_config, "base_url", None
                        ),
                        "has_api_key": bool(self.config_manager.llm_config.api_key),
                    },
                    "browser": {
                        "headless": self.config_manager.browser_config.headless,
                        "disable_security": self.config_manager.browser_config.disable_security,
                        "extra_args": getattr(
                            self.config_manager.browser_config, "extra_args", []
                        ),
                        "window_width": getattr(
                            self.config_manager.browser_config, "window_width", 1280
                        ),
                        "window_height": getattr(
                            self.config_manager.browser_config, "window_height", 720
                        ),
                    },
                    "agent": {
                        "use_vision": self.config_manager.agent_config.use_vision,
                        "max_failures": self.config_manager.agent_config.max_failures,
                        "max_steps": self.config_manager.agent_config.max_steps,
                        "retry_delay": getattr(
                            self.config_manager.agent_config, "retry_delay", 10
                        ),
                        "generate_gif": getattr(
                            self.config_manager.agent_config, "generate_gif", True
                        ),
                        "validate_output": getattr(
                            self.config_manager.agent_config, "validate_output", True
                        ),
                        "planner_llm": getattr(
                            self.config_manager.agent_config,
                            "planner_llm",
                            "gemini-2.5-flash-lite",
                        ),
                        "page_extraction_llm": getattr(
                            self.config_manager.agent_config,
                            "page_extraction_llm",
                            "gemini-2.5-flash-lite",
                        ),
                    },
                    "supported_providers": self.config_manager.get_supported_providers(),
                    "default_models": self.config_manager.get_default_models(),
                }
            )

        @self.app.route("/api/config", methods=["POST"])
        def update_config():
            data = request.get_json()

            try:
                if "llm" in data:
                    self.config_manager.update_llm_config(**data["llm"])
                if "browser" in data:
                    self.config_manager.update_browser_config(**data["browser"])
                if "agent" in data:
                    self.config_manager.update_agent_config(**data["agent"])

                # Validate configuration
                issues = self.config_manager.validate_config()

                return jsonify(
                    {
                        "success": True,
                        "message": "Configuration updated successfully",
                        "validation_issues": issues,
                    }
                )
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 400

        @self.app.route("/api/task/status", methods=["GET"])
        def task_status():
            return jsonify(self.task_manager.get_status())

        @self.app.route("/api/task/start", methods=["POST"])
        def start_task():
            data = request.get_json()
            task_description = data.get("task", "").strip()

            if not task_description:
                return (
                    jsonify(
                        {"success": False, "error": "Task description is required"}
                    ),
                    400,
                )

            # Run in thread to avoid blocking
            def run_start_task():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.task_manager.start_task(task_description))

            threading.Thread(target=run_start_task, daemon=True).start()

            return jsonify({"success": True, "message": "Starting task..."})

        @self.app.route("/api/task/stop", methods=["POST"])
        def stop_task():
            result = self.task_manager.stop_task()
            return jsonify(result)

        @self.app.route("/api/task/resume", methods=["POST"])
        def resume_task():
            print("DEBUG: Resume task endpoint called")
            result = self.task_manager.resume_task()
            print(f"DEBUG: Resume result: {result}")
            return jsonify(result)

        @self.app.route("/api/task/pause", methods=["POST"])
        def pause_task():
            result = self.task_manager.pause_task()
            return jsonify(result)

    def _setup_jarvis_routes(self):
        """Setup JARVIS voice conversation API routes"""

        @self.app.route("/jarvis")
        def jarvis_interface():
            """Serve the JARVIS voice conversation interface"""
            return render_template("jarvis.html")

        @self.app.route("/api/jarvis/session", methods=["POST"])
        def create_jarvis_session():
            """Create a new JARVIS conversation session"""
            data = request.get_json() or {}
            language = data.get("language", "en")
            
            try:
                session_id = self.voice_service.create_session(language=language)
                return jsonify({
                    "success": True,
                    "session_id": session_id,
                    "language": language,
                    "supported_languages": self.voice_service.get_supported_languages()
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/jarvis/start/<session_id>", methods=["POST"])
        def start_jarvis_conversation(session_id):
            """Start a conversation with JARVIS greeting"""
            try:
                message = self.voice_service.start_conversation(session_id)
                return jsonify({
                    "success": True,
                    "message": {
                        "role": message.role,
                        "content": message.content,
                        "language": message.language
                    }
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/jarvis/message", methods=["POST"])
        def process_jarvis_message():
            """Process a message in the JARVIS conversation"""
            data = request.get_json()
            session_id = data.get("session_id")
            message = data.get("message", "").strip()
            language = data.get("language")

            if not session_id:
                return jsonify({"success": False, "error": "Session ID required"}), 400
            
            if not message:
                return jsonify({"success": False, "error": "Message required"}), 400

            try:
                # Process message asynchronously
                def process_async():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    return loop.run_until_complete(
                        self.voice_service.process_voice_input(session_id, message, language)
                    )
                
                response, task_plan = process_async()
                
                result = {
                    "success": True,
                    "response": {
                        "role": response.role,
                        "content": response.content,
                        "language": response.language
                    }
                }
                
                if task_plan:
                    result["task_plan"] = {
                        "description": task_plan.description,
                        "is_ready": task_plan.is_ready,
                        "confidence": task_plan.confidence,
                        "clarifications_needed": task_plan.clarifications_needed
                    }
                
                return jsonify(result)
                
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/jarvis/language", methods=["POST"])
        def set_jarvis_language():
            """Change the conversation language"""
            data = request.get_json()
            session_id = data.get("session_id")
            language = data.get("language")

            if not session_id or not language:
                return jsonify({"success": False, "error": "Session ID and language required"}), 400

            try:
                success = self.voice_service.set_language(session_id, language)
                return jsonify({
                    "success": success,
                    "language": language if success else None
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/jarvis/execute", methods=["POST"])
        def execute_jarvis_task():
            """Execute a task planned by JARVIS"""
            data = request.get_json()
            # session_id can be used for logging/tracking in future
            _ = data.get("session_id")
            task = data.get("task")

            if not task:
                return jsonify({"success": False, "error": "Task description required"}), 400

            try:
                # Start the task using the task manager
                def run_start_task():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.task_manager.start_task(task))

                threading.Thread(target=run_start_task, daemon=True).start()
                
                return jsonify({
                    "success": True,
                    "message": "Task execution started",
                    "redirect": "/"  # Redirect to main interface
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/jarvis/history/<session_id>", methods=["GET"])
        def get_jarvis_history(session_id):
            """Get conversation history for a session"""
            try:
                history = self.voice_service.get_conversation_history(session_id)
                return jsonify({
                    "success": True,
                    "history": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "language": msg.language,
                            "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
                        }
                        for msg in history
                    ]
                })
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/jarvis/end/<session_id>", methods=["POST"])
        def end_jarvis_session(session_id):
            """End a JARVIS conversation session"""
            try:
                success = self.voice_service.end_session(session_id)
                return jsonify({"success": success})
            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api/jarvis/languages", methods=["GET"])
        def get_supported_languages():
            """Get list of supported languages"""
            return jsonify({
                "success": True,
                "languages": self.voice_service.get_supported_languages()
            })

    def _setup_socketio_events(self):
        """Setup SocketIO events"""

        @self.socketio.on("connect")
        def handle_connect():
            print(f"Client connected: {request.sid}")

            # Send recent events to new client
            recent_events = self.event_adapter.get_recent_events(50)
            for event in recent_events:
                emit("log_event", self._serialize_log_event(event))

        @self.socketio.on("disconnect")
        def handle_disconnect():
            print(f"Client disconnected: {request.sid}")

        @self.socketio.on("request_status")
        def handle_status_request():
            status = self.task_manager.get_status()
            emit("status_update", status)

        @self.socketio.on("resume_after_user_help")
        def handle_user_help_completed():
            """Handle user completing CAPTCHA or other manual intervention"""
            try:
                print("DEBUG: Socket resume_after_user_help called")
                result = self.task_manager.resume_task()
                print(f"DEBUG: Socket resume result: {result}")
                emit("user_help_response", result)
            except Exception as e:
                print(f"DEBUG: Socket resume error: {e}")
                emit("user_help_response", {"success": False, "error": str(e)})

    def _on_log_event(self, event: LogEvent):
        """Handle log events from event adapter"""
        # Broadcast to all connected clients
        self.socketio.emit("log_event", self._serialize_log_event(event))

    def _serialize_log_event(self, event: LogEvent) -> Dict[str, Any]:
        """Serialize log event for JSON transmission"""
        return {
            "timestamp": event.timestamp.isoformat(),
            "level": event.level.value,
            "logger_name": event.logger_name,
            "message": event.message,
            "event_type": event.event_type.value,
            "metadata": event.metadata or {},
        }

    def run(self, debug: bool = False):
        """Run the web application"""
        print(f"Starting Browser.AI Web GUI on http://localhost:{self.port}")
        print("Press Ctrl+C to stop")

        # Create templates directory if it doesn't exist
        templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        os.makedirs(templates_dir, exist_ok=True)

        # Create static directory if it doesn't exist
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        os.makedirs(static_dir, exist_ok=True)

        try:
            self.socketio.run(self.app, host="0.0.0.0", port=self.port, debug=debug)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.event_adapter.stop()


if __name__ == "__main__":
    app = WebApp()
    app.run(debug=True)
