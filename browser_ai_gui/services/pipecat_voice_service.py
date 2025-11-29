"""
Pipecat-based Voice Conversation Service for Browser.AI

This module provides a real-time voice conversation AI interface using Pipecat framework.
It supports:
- Real-time voice-based conversation using Pipecat pipelines
- Multiple languages (English, Tamil, Sinhala)
- JARVIS-inspired persona
- Integration with Browser.AI agent for task execution
- Google Gemini for LLM and TTS

Pipecat provides a more realistic, real-time voice conversation experience compared
to the basic Web Speech API implementation.
"""

import logging
import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional

# Try to import pipecat components
PIPECAT_AVAILABLE = False
VAD_AVAILABLE = False
SileroVADAnalyzer = None
Pipeline = None
PipelineParams = None
PipelineTask = None
OpenAILLMContext = None
GoogleLLMService = None
GoogleTTSService = None
WebsocketServerParams = None
WebsocketServerTransport = None

try:
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.task import PipelineParams, PipelineTask
    from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
    from pipecat.services.google.llm import GoogleLLMService
    from pipecat.services.google.tts import GoogleTTSService
    from pipecat.transports.websocket.server import (
        WebsocketServerParams,
        WebsocketServerTransport,
    )

    PIPECAT_AVAILABLE = True
    logging.info("Pipecat core components loaded successfully")
    
    # VAD is optional (requires onnxruntime)
    try:
        from pipecat.audio.vad.silero import SileroVADAnalyzer
        VAD_AVAILABLE = True
    except (ImportError, Exception) as e:
        SileroVADAnalyzer = None
        VAD_AVAILABLE = False
        logging.warning(f"Silero VAD not available: {e}. Install with: pip install pipecat-ai[silero]")
        
except ImportError as e:
    PIPECAT_AVAILABLE = False
    VAD_AVAILABLE = False
    logging.warning(f"Pipecat not available: {e}")


logger = logging.getLogger(__name__)


class ConversationLanguage(str, Enum):
    """Supported languages for conversation"""

    ENGLISH = "en"
    TAMIL = "ta"
    SINHALA = "si"


@dataclass
class PipecatConfig:
    """Configuration for Pipecat voice service"""

    google_api_key: Optional[str] = None
    host: str = "0.0.0.0"
    port: int = 8765
    language: str = "en"
    sample_rate: int = 16000
    enable_vad: bool = True  # Voice Activity Detection
    tts_voice: str = "en-US-Neural2-F"  # Google TTS voice


class JarvisPersona:
    """
    JARVIS-inspired AI persona for Pipecat-based conversations.
    """

    SYSTEM_PROMPTS = {
        "en": """You are JARVIS (Just A Rather Very Intelligent System), an advanced AI assistant for Browser.AI.

PERSONALITY:
- You are sophisticated, intelligent, and highly capable
- You speak in a refined, professional manner while remaining warm and approachable
- You are proactive, anticipating user needs when possible
- You explain complex tasks in simple terms
- You maintain a calm, reassuring demeanor even when handling complex requests
- You occasionally use light wit, but never at the user's expense

YOUR ROLE:
You are the voice-based conversational interface for Browser.AI, a browser automation system. Your job is to:
1. Understand what the user wants to accomplish on the web
2. Ask clarifying questions ONE AT A TIME to gather necessary details
3. Create a clear, actionable plan for the automation system
4. Confirm the plan with the user before execution

CONVERSATION GUIDELINES:
- Ask questions ONE AT A TIME - never overwhelm with multiple questions
- Be concise but thorough - keep responses short for voice
- Use occasional addresses like "Sir" or "Ma'am" to add personality
- When you have enough information, summarize the task clearly
- Keep responses brief and suitable for voice output (2-3 sentences max)

TASK READINESS:
When you have gathered enough information:
1. Summarize what you understood briefly
2. Ask for confirmation
3. If confirmed, say "READY TO EXECUTE" followed by the task description

Example responses:
"Good day! I'm JARVIS. How may I assist you with web browsing today?"
"Certainly. What's your budget preference?"
"Very well. Wireless headphones under $100 with noise cancellation. Shall I proceed?"
""",
        "ta": """நீங்கள் JARVIS, Browser.AI-க்கான மேம்பட்ட AI உதவியாளர்.

ஆளுமை:
- நீங்கள் புத்திசாலி மற்றும் மிகவும் திறமையானவர்
- தொழில்முறையாகவும் அன்பாகவும் பேசுவீர்கள்
- சிக்கலான பணிகளை எளிமையாக விளக்குவீர்கள்

உங்கள் பங்கு:
- பயனர் இணையத்தில் என்ன செய்ய விரும்புகிறார் என்பதைப் புரிந்துகொள்ளுங்கள்
- ஒரு நேரத்தில் ஒரு கேள்வி கேளுங்கள்
- தெளிவான திட்டத்தை உருவாக்குங்கள்

போதுமான தகவல் கிடைத்தவுடன் "செயல்படுத்த தயார்" என்று சொல்லுங்கள்.
""",
        "si": """ඔබ JARVIS, Browser.AI සඳහා උසස් AI සහායකයෙකි.

පෞරුෂත්වය:
- ඔබ බුද්ධිමත් සහ ඉතා හැකියාවන්ගෙන් පිරුණු කෙනෙක්
- වෘත්තීය ආකාරයෙන් කතා කරන අතරම උණුසුම් කෙනෙක්
- සංකීර්ණ කාර්යයන් සරලව පැහැදිලි කරන කෙනෙක්

ඔබේ කාර්යභාරය:
- පරිශීලකයා වෙබ් අඩවියේ කුමක් කිරීමට අවශ්‍යද යන්න තේරුම් ගන්න
- වරකට එක ප්‍රශ්නයක් අසන්න
- පැහැදිලි සැලැස්මක් සාදන්න

ප්‍රමාණවත් තොරතුරු ලැබුණු විට "ක්‍රියාත්මක කිරීමට සූදානම්" යැයි කියන්න.
""",
    }

    GREETINGS = {
        "en": [
            "Good day! I'm JARVIS, your Browser.AI assistant. How may I assist you today?",
            "Hello! JARVIS at your service. What task would you like me to help you with?",
            "Greetings! I'm JARVIS. How can I help you navigate the web today?",
        ],
        "ta": [
            "வணக்கம்! நான் JARVIS. இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?",
            "நல்வரவு! JARVIS உங்கள் சேவையில். எந்த பணியில் நான் உதவ வேண்டும்?",
        ],
        "si": [
            "ආයුබෝවන්! මම JARVIS. අද මට ඔබට උදව් කරන්නේ කෙසේද?",
            "සුභ දවසක්! JARVIS ඔබේ සේවයේ. මට ඔබට උදව් කළ යුත්තේ කුමක්ද?",
        ],
    }

    TTS_VOICES = {
        "en": "en-US-Neural2-F",
        "ta": "ta-IN-Standard-A",
        "si": "si-LK-Standard-A",
    }

    @classmethod
    def get_system_prompt(cls, language: str = "en") -> str:
        """Get the system prompt for a given language"""
        return cls.SYSTEM_PROMPTS.get(language, cls.SYSTEM_PROMPTS["en"])

    @classmethod
    def get_greeting(cls, language: str = "en") -> str:
        """Get a random greeting message for a given language"""
        import random

        greetings = cls.GREETINGS.get(language, cls.GREETINGS["en"])
        return random.choice(greetings)

    @classmethod
    def get_tts_voice(cls, language: str = "en") -> str:
        """Get the TTS voice for a given language"""
        return cls.TTS_VOICES.get(language, cls.TTS_VOICES["en"])


class PipecatVoiceService:
    """
    Pipecat-based voice conversation service for JARVIS-like interactions.

    This service creates a real-time voice pipeline using:
    - Google Gemini for LLM
    - Google TTS for speech synthesis
    - VAD (Voice Activity Detection) for turn-taking
    - WebSocket transport for browser communication
    """

    SUPPORTED_LANGUAGES = {
        "en": "English",
        "ta": "தமிழ் (Tamil)",
        "si": "සිංහල (Sinhala)",
    }

    def __init__(self, config: Optional[PipecatConfig] = None):
        """Initialize the Pipecat voice service"""
        if not PIPECAT_AVAILABLE:
            raise ImportError(
                "Pipecat is not available. Install with: pip install pipecat-ai[google]"
            )

        self.config = config or PipecatConfig()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.pipeline: Optional[Pipeline] = None
        self.task: Optional[PipelineTask] = None
        self._running = False

        # Get API key from config or environment
        self.api_key = self.config.google_api_key or os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            logger.warning("No Google API key provided. LLM features will be limited.")

        logger.info(
            f"PipecatVoiceService initialized (language: {self.config.language})"
        )

    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages"""
        return self.SUPPORTED_LANGUAGES.copy()

    async def create_session(
        self, language: str = "en", on_task_ready: Optional[Callable] = None
    ) -> str:
        """Create a new voice conversation session"""
        session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "language": language,
            "created_at": datetime.now(),
            "messages": [],
            "on_task_ready": on_task_ready,
            "current_task": None,
        }

        logger.info(f"Created Pipecat session: {session_id} (language: {language})")
        return session_id

    async def start_pipeline(self, session_id: str) -> bool:
        """Start the Pipecat pipeline for a session"""
        if session_id not in self.sessions:
            logger.error(f"Session not found: {session_id}")
            return False

        session = self.sessions[session_id]
        language = session["language"]

        try:
            # Setup VAD if available
            vad_enabled = self.config.enable_vad and VAD_AVAILABLE
            vad_analyzer = SileroVADAnalyzer() if vad_enabled and SileroVADAnalyzer else None
            
            # Create transport with WebSocket
            transport = WebsocketServerTransport(
                params=WebsocketServerParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                    audio_in_sample_rate=self.config.sample_rate,
                    audio_out_sample_rate=self.config.sample_rate,
                    vad_enabled=vad_enabled,
                    vad_analyzer=vad_analyzer,
                )
            )

            # Create LLM service
            llm = GoogleLLMService(
                api_key=self.api_key,
                model="gemini-2.0-flash-exp",
            )

            # Create TTS service
            tts = GoogleTTSService(
                api_key=self.api_key,
                voice_id=JarvisPersona.get_tts_voice(language),
                sample_rate=self.config.sample_rate,
            )

            # Create context with JARVIS persona
            context = OpenAILLMContext(
                messages=[
                    {
                        "role": "system",
                        "content": JarvisPersona.get_system_prompt(language),
                    }
                ]
            )
            context_aggregator = llm.create_context_aggregator(context)

            # Build pipeline
            self.pipeline = Pipeline(
                [
                    transport.input(),
                    context_aggregator.user(),
                    llm,
                    tts,
                    transport.output(),
                    context_aggregator.assistant(),
                ]
            )

            # Create task
            self.task = PipelineTask(
                self.pipeline,
                params=PipelineParams(
                    allow_interruptions=True,
                    enable_metrics=True,
                ),
            )

            self._running = True
            logger.info(f"Pipeline started for session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start pipeline: {e}")
            return False

    async def stop_pipeline(self) -> None:
        """Stop the running pipeline"""
        if self.task:
            await self.task.cancel()
            self.task = None

        self.pipeline = None
        self._running = False
        logger.info("Pipeline stopped")

    async def process_audio(
        self, session_id: str, audio_data: bytes
    ) -> Optional[bytes]:
        """
        Process incoming audio data and return response audio.

        Note: In a full implementation, this would be handled by the pipeline.
        This method is for manual audio processing if needed.
        """
        if session_id not in self.sessions:
            return None

        # Audio processing is handled by the pipeline
        # This method is kept for compatibility
        return None

    async def send_text(self, session_id: str, text: str) -> Optional[str]:
        """
        Send text message to the conversation and get response.

        This is a fallback for text-based interaction when voice is not available.
        """
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        language = session["language"]

        # Add user message
        session["messages"].append({"role": "user", "content": text})

        # For text-only mode, we can use the LLM directly
        if self.api_key:
            try:
                # Build messages context for future pipeline use
                _ = [
                    {
                        "role": "system",
                        "content": JarvisPersona.get_system_prompt(language),
                    }
                ] + session["messages"]

                # This is a simplified text-only response
                # In full implementation, this goes through the pipeline
                response = "I'm processing your request. Voice pipeline is ready."

                session["messages"].append({"role": "assistant", "content": response})
                return response

            except Exception as e:
                logger.error(f"Error processing text: {e}")
                return None

        return None

    async def end_session(self, session_id: str) -> bool:
        """End a voice conversation session"""
        if session_id not in self.sessions:
            return False

        await self.stop_pipeline()
        del self.sessions[session_id]
        logger.info(f"Ended session: {session_id}")
        return True

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a session"""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "language": session["language"],
            "created_at": session["created_at"].isoformat(),
            "message_count": len(session["messages"]),
            "pipeline_running": self._running,
        }


# WebSocket handler for Pipecat voice service
class PipecatWebSocketHandler:
    """
    WebSocket handler that integrates Pipecat with the existing Browser.AI
    WebSocket server infrastructure.
    """

    def __init__(
        self,
        voice_service: PipecatVoiceService,
        on_task_ready: Optional[Callable] = None,
    ):
        self.voice_service = voice_service
        self.on_task_ready = on_task_ready

    async def handle_connection(self, websocket, session_id: str):
        """Handle a WebSocket connection for voice conversation"""
        import json
        
        try:
            # Create session if not exists
            if session_id not in self.voice_service.sessions:
                await self.voice_service.create_session(
                    language="en", on_task_ready=self.on_task_ready
                )
                # Update session with provided session_id
                # Note: create_session generates its own ID, so we track by the generated ID

            # Start pipeline
            await self.voice_service.start_pipeline(session_id)

            # Handle messages
            async for message in websocket:
                if isinstance(message, bytes):
                    # Audio data
                    await self.voice_service.process_audio(session_id, message)
                else:
                    # Text/control message
                    data = json.loads(message)
                    if data.get("type") == "text":
                        response = await self.voice_service.send_text(
                            session_id, data.get("text", "")
                        )
                        if response:
                            await websocket.send(
                                json.dumps({"type": "text", "content": response})
                            )

        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await self.voice_service.end_session(session_id)


# Factory function for creating the service
def create_pipecat_voice_service(
    api_key: Optional[str] = None,
    language: str = "en",
    enable_vad: bool = True,
) -> Optional[PipecatVoiceService]:
    """
    Create a Pipecat voice service instance.

    Args:
        api_key: Google API key (uses GOOGLE_API_KEY env var if not provided)
        language: Default language (en, ta, si)
        enable_vad: Enable Voice Activity Detection

    Returns:
        PipecatVoiceService instance or None if Pipecat is not available
    """
    if not PIPECAT_AVAILABLE:
        logger.warning("Pipecat is not available")
        return None

    config = PipecatConfig(
        google_api_key=api_key,
        language=language,
        enable_vad=enable_vad,
    )

    return PipecatVoiceService(config)
