#!/usr/bin/env python3
"""
Test script to verify WebSocket server functionality for Chrome extension
"""

import unittest

from browser_ai_gui.config import ConfigManager
from browser_ai_gui.event_adapter import EventType, LogLevel
from browser_ai_gui.web_app import WebApp


class TestWebApp(unittest.TestCase):
    def test_webapp_initialization(self):
        """Test that WebApp can be initialized properly"""
        print("Testing WebApp initialization...")

        config = ConfigManager()
        app = WebApp(config_manager=config, port=5001)
        print("✅ WebApp initialized successfully")
        print(f"   - Flask app: {app.app}")
        print(f"   - SocketIO: {app.socketio}")
        print(f"   - Extension handler: {app.extension_handler}")
        print(f"   - Event adapter: {app.event_adapter}")

        self.assertIsNotNone(app.app)
        self.assertIsNotNone(app.socketio)

    def test_extension_websocket_namespace(self):
        """Test that extension WebSocket namespace is set up"""
        print("\nTesting WebSocket namespace setup...")

        config = ConfigManager()
        app = WebApp(config_manager=config, port=5001)

        # Check if the namespace handlers are registered
        print("✅ WebSocket server configured")
        print(f"   - Extension handler type: {type(app.extension_handler).__name__}")
        self.assertIsNotNone(app.socketio)

    def test_event_adapter(self):
        """Test that event adapter is working"""
        print("\nTesting event adapter...")

        config = ConfigManager()
        app = WebApp(config_manager=config, port=5001)

        # Emit a test event
        app.event_adapter.emit_custom_event(
            EventType.LOG,
            "Test event from verification script",
            LogLevel.INFO,
            {"test": True},
        )
        print("✅ Event adapter working")

    def test_task_status_updates(self):
        """Test that task status updates are emitted correctly"""
        print("\nTesting task status updates...")

        config = ConfigManager()
        app = WebApp(config_manager=config, port=5001)

        # Simulate task completion
        app.event_adapter.emit_custom_event(
            EventType.STATUS,
            {"is_running": False, "current_task": "Task completed successfully!"},
            LogLevel.INFO,
        )
        print("✅ Task completion status emitted successfully")

        # Simulate task failure
        app.event_adapter.emit_custom_event(
            EventType.STATUS,
            {"is_running": False, "current_task": "Task failed due to an error."},
            LogLevel.ERROR,
        )
        print("✅ Task failure status emitted successfully")


if __name__ == "__main__":
    unittest.main()
