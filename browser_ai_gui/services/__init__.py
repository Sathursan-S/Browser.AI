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

# Optional Pipecat voice service (requires pipecat-ai)
try:
	from .pipecat_voice_service import (
		PipecatVoiceService,
		PipecatConfig,
		create_pipecat_voice_service,
		PIPECAT_AVAILABLE,
	)
	__all__.extend(['PipecatVoiceService', 'PipecatConfig', 'create_pipecat_voice_service', 'PIPECAT_AVAILABLE'])
except ImportError:
	PipecatVoiceService = None
	PipecatConfig = None
	create_pipecat_voice_service = None
	PIPECAT_AVAILABLE = False
