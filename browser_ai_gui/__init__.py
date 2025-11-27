"""
Browser AI GUI Package

This package provides web and desktop interfaces for Browser.AI automation.
Includes chat-style interfaces similar to GitHub Copilot for task management.

Now includes JARVIS voice conversation mode for natural language interaction
with multi-language support (English, Tamil, Sinhala).
"""

try:
	from .config import ConfigManager
	from .event_adapter import EventAdapter, EventType, LogEvent, LogLevel

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

	# Voice conversation service (JARVIS mode)
	try:
		from .services.voice_conversation import VoiceConversationService, JarvisPersona

		VOICE_AVAILABLE = True
	except ImportError:
		VOICE_AVAILABLE = False
		VoiceConversationService = None
		JarvisPersona = None

	__all__ = ['EventAdapter', 'LogEvent', 'EventType', 'LogLevel', 'ConfigManager']

	if WEB_AVAILABLE:
		__all__.append('WebApp')
	if DESKTOP_AVAILABLE:
		__all__.append('BrowserAIGUI')
	if VOICE_AVAILABLE:
		__all__.extend(['VoiceConversationService', 'JarvisPersona'])

except ImportError as e:
	# Graceful degradation if dependencies are missing
	print(f'Warning: Browser AI GUI components not fully available: {e}')
	print('Install additional dependencies: pip install flask flask-socketio')

	__all__ = []
