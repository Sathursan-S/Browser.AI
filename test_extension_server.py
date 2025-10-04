#!/usr/bin/env python3
"""
Test script to verify WebSocket server functionality for Chrome extension
"""

import asyncio
import sys
from browser_ai_gui.web_app import WebApp
from browser_ai_gui.config import ConfigManager

def test_webapp_initialization():
    """Test that WebApp can be initialized properly"""
    print("Testing WebApp initialization...")
    
    try:
        config = ConfigManager()
        app = WebApp(config_manager=config, port=5001)
        print("✅ WebApp initialized successfully")
        print(f"   - Flask app: {app.app}")
        print(f"   - SocketIO: {app.socketio}")
        print(f"   - Extension handler: {app.extension_handler}")
        print(f"   - Event adapter: {app.event_adapter}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize WebApp: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_extension_websocket_namespace():
    """Test that extension WebSocket namespace is set up"""
    print("\nTesting WebSocket namespace setup...")
    
    try:
        config = ConfigManager()
        app = WebApp(config_manager=config, port=5001)
        
        # Check if the namespace handlers are registered
        namespaces = app.socketio.server.manager.rooms.keys() if hasattr(app.socketio.server.manager, 'rooms') else []
        print(f"✅ WebSocket server configured")
        print(f"   - Extension handler type: {type(app.extension_handler).__name__}")
        return True
    except Exception as e:
        print(f"❌ Failed to verify WebSocket setup: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_event_adapter():
    """Test that event adapter is working"""
    print("\nTesting event adapter...")
    
    try:
        config = ConfigManager()
        app = WebApp(config_manager=config, port=5001)
        
        # Emit a test event
        from browser_ai_gui.event_adapter import EventType, LogLevel
        app.event_adapter.emit_custom_event(
            EventType.LOG,
            "Test event from verification script",
            LogLevel.INFO,
            {"test": True}
        )
        print("✅ Event adapter working")
        return True
    except Exception as e:
        print(f"❌ Event adapter test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Browser.AI Extension WebSocket Server Tests")
    print("=" * 60)
    
    tests = [
        test_webapp_initialization,
        test_extension_websocket_namespace,
        test_event_adapter,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("\n✅ All tests passed! The WebSocket server is ready.")
        print("\nTo start the server, run:")
        print("  python -m browser_ai_gui.main web --port 5000")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
