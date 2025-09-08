"""
Browser AI GUI Package

This package provides web and desktop interfaces for Browser.AI automation.
Includes chat-style interfaces similar to GitHub Copilot for task management.
"""

try:
    from .event_adapter import EventAdapter, LogEvent, EventType, LogLevel
    from .config import ConfigManager
    
    # Web app requires Flask
    try:
        from .web_app import WebApp
        WEB_AVAILABLE = True
    except ImportError:
        WEB_AVAILABLE = False
        WebApp = None
    
    # Tkinter GUI requires tkinter (should be built-in)
    try:
        from .tkinter_gui import BrowserAIGUI
        DESKTOP_AVAILABLE = True
    except ImportError:
        DESKTOP_AVAILABLE = False
        BrowserAIGUI = None
    
    __all__ = ['EventAdapter', 'LogEvent', 'EventType', 'LogLevel', 'ConfigManager']
    
    if WEB_AVAILABLE:
        __all__.append('WebApp')
    if DESKTOP_AVAILABLE:
        __all__.append('BrowserAIGUI')

except ImportError as e:
    # Graceful degradation if dependencies are missing
    print(f"Warning: Browser AI GUI components not fully available: {e}")
    print("Install additional dependencies: pip install flask flask-socketio")
    
    __all__ = []