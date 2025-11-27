"""
Browser AI GUI Services Package

Contains task management, voice conversation, and other services.
"""

from .task_manager import TaskManager

__all__ = ['TaskManager']

# Optional voice service (requires additional dependencies)
try:
	from .voice_conversation import JarvisPersona, VoiceConversationService
	__all__.extend(['VoiceConversationService', 'JarvisPersona'])
except ImportError:
	VoiceConversationService = None
	JarvisPersona = None
