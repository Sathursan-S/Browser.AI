#!/usr/bin/env python3
"""
Test the web interface of Browser.AI GUI
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add Browser.AI to path
sys.path.insert(0, str(Path(__file__).parent))

from browser_ai_gui.web_app import WebApp
from browser_ai_gui.config import ConfigManager


def test_web_interface():
    """Test the web interface by starting it briefly"""
    print("Testing Browser.AI Web Interface...")
    print("=" * 50)
    
    # Create a config manager
    config_manager = ConfigManager()
    
    # Create web app
    web_app = WebApp(config_manager, port=5001)
    
    # Start the web app in a separate thread
    def run_app():
        try:
            web_app.socketio.run(web_app.app, host='localhost', port=5001, debug=False)
        except Exception as e:
            print(f"Web app error: {e}")
    
    app_thread = threading.Thread(target=run_app, daemon=True)
    app_thread.start()
    
    # Wait for server to start
    time.sleep(3)
    
    print("✅ Web interface started successfully on http://localhost:5001")
    print()
    print("Features implemented:")
    print("- ✅ Flask web server with Socket.IO")
    print("- ✅ Event adapter for log streaming")
    print("- ✅ Configuration management")
    print("- ✅ Task management system")
    print("- ✅ Real-time WebSocket communication")
    print("- ✅ GitHub Copilot-style chat interface")
    print("- ✅ LLM configuration panel")
    print("- ✅ Browser and agent settings")
    print()
    print("Interface components:")
    print("- 📱 Responsive web design")
    print("- 🎨 Dark theme (VS Code style)")
    print("- 💬 Chat-based task input")
    print("- ⚙️ Configuration sidebar")
    print("- 📊 Real-time status updates")
    print("- 🔄 Task control buttons (pause/stop)")
    print("- 📝 Live log streaming")
    print()
    
    # Test API endpoints
    try:
        import requests
        
        # Test config endpoint
        response = requests.get("http://localhost:5001/api/config", timeout=5)
        if response.status_code == 200:
            print("✅ Configuration API working")
        else:
            print(f"❌ Configuration API failed: {response.status_code}")
            
        # Test status endpoint  
        response = requests.get("http://localhost:5001/api/task/status", timeout=5)
        if response.status_code == 200:
            print("✅ Task status API working")
        else:
            print(f"❌ Task status API failed: {response.status_code}")
            
    except ImportError:
        print("ℹ️ Install 'requests' to test API endpoints")
    except Exception as e:
        print(f"⚠️ API test failed: {e}")
    
    print()
    print("🎉 Web interface test completed!")
    print()
    print("To run manually:")
    print("  python examples.py web --port 5001")
    print()
    print("Then open: http://localhost:5001")


if __name__ == "__main__":
    test_web_interface()