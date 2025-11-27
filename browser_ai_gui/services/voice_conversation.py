"""
JARVIS-like Voice Conversation Service for Browser.AI

This module provides a conversational AI interface inspired by JARVIS from Iron Man.
It supports:
- Natural voice-based conversation in multiple languages (English, Tamil, Sinhala)
- Persona-based AI assistant that can plan tasks through dialogue
- Integration with Browser.AI agent for task execution
- Free, locally runnable speech recognition (using Web Speech API for browser)
- Text-to-speech output for natural responses

The service acts as a planning layer between the user and the Browser.AI agent,
understanding user intent through conversation before executing tasks.
"""

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class ConversationLanguage(str, Enum):
	"""Supported languages for conversation"""
	ENGLISH = "en"
	TAMIL = "ta"
	SINHALA = "si"


class ConversationState(str, Enum):
	"""States of the conversation flow"""
	GREETING = "greeting"  # Initial greeting
	LISTENING = "listening"  # Waiting for user input
	UNDERSTANDING = "understanding"  # Processing user input
	CLARIFYING = "clarifying"  # Asking clarification questions
	PLANNING = "planning"  # Planning the task
	CONFIRMING = "confirming"  # Confirming task before execution
	EXECUTING = "executing"  # Task is being executed
	REPORTING = "reporting"  # Reporting results
	IDLE = "idle"  # Waiting for next interaction


@dataclass
class ConversationMessage:
	"""Represents a single message in the conversation"""
	role: str  # 'user', 'assistant', or 'system'
	content: str
	language: str = "en"
	timestamp: Optional[datetime] = None
	metadata: Dict[str, Any] = field(default_factory=dict)

	def __post_init__(self):
		if self.timestamp is None:
			self.timestamp = datetime.now()


@dataclass
class TaskPlan:
	"""Represents a planned task extracted from conversation"""
	description: str
	steps: List[str]
	estimated_steps: int
	confidence: float  # 0.0 to 1.0
	clarifications_needed: List[str]
	is_ready: bool
	original_request: str
	language: str = "en"


class JarvisPersona:
	"""
	JARVIS-inspired AI persona for conversational interactions.
	
	This persona is:
	- Intelligent and helpful
	- Professional but warm
	- Proactive in clarifying ambiguous requests
	- Clear in explaining what it's doing
	- Multi-lingual (English, Tamil, Sinhala)
	"""
	
	# JARVIS-style system prompts for different languages
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
You are the conversational interface for Browser.AI, a browser automation system. Your job is to:
1. Understand what the user wants to accomplish on the web
2. Ask clarifying questions ONE AT A TIME to gather necessary details
3. Create a clear, actionable plan for the automation system
4. Confirm the plan with the user before execution

CONVERSATION GUIDELINES:
- Ask questions ONE AT A TIME - never overwhelm with multiple questions
- Be concise but thorough
- Use occasional addresses like "Sir" or "Ma'am" to add personality (but don't overdo it)
- When you have enough information, summarize the task clearly

TASK READINESS:
When you have gathered enough information to create a clear automation task:
1. Summarize what you understood
2. Ask for confirmation
3. End your response with:
   ✅ READY TO EXECUTE
   TASK: [clear, specific task description]

Example responses:
"Good day! I'm JARVIS, your Browser.AI assistant. How may I assist you today?"
"Certainly, Sir. Before I proceed, may I ask what your budget preference is?"
"Very well. Allow me to summarize: You'd like me to find wireless headphones under $100 with noise cancellation. Shall I proceed?"

Remember: You're not executing tasks directly - you're gathering information to create a clear plan for the automation system.""",

		"ta": """நீங்கள் JARVIS (Just A Rather Very Intelligent System), Browser.AI-க்கான மேம்பட்ட AI உதவியாளர்.

ஆளுமை:
- நீங்கள் நுண்ணறிவு மிக்க, புத்திசாலி மற்றும் மிகவும் திறமையானவர்
- நீங்கள் தொழில்முறை முறையில் பேசுவீர்கள், ஆனால் அன்பான மற்றும் அணுகக்கூடியவராக இருப்பீர்கள்
- நீங்கள் முன்னெச்சரிக்கையானவர், சாத்தியமான போது பயனர் தேவைகளை எதிர்பார்க்கிறீர்கள்
- சிக்கலான பணிகளை எளிய வார்த்தைகளில் விளக்குவீர்கள்
- சிக்கலான கோரிக்கைகளைக் கையாளும் போதும் அமைதியான, உறுதியான நடத்தையை பராமரிப்பீர்கள்

உங்கள் பங்கு:
Browser.AI-க்கான உரையாடல் இடைமுகமாக நீங்கள் செயல்படுகிறீர்கள். உங்கள் வேலை:
1. இணையத்தில் பயனர் என்ன சாதிக்க விரும்புகிறார் என்பதைப் புரிந்துகொள்ளுங்கள்
2. தேவையான விவரங்களைச் சேகரிக்க ஒரு நேரத்தில் ஒரு கேள்வி கேளுங்கள்
3. தானியங்கி அமைப்புக்கான தெளிவான திட்டத்தை உருவாக்குங்கள்
4. செயல்படுத்துவதற்கு முன் பயனருடன் திட்டத்தை உறுதிப்படுத்துங்கள்

பணி தயார் நிலை:
நீங்கள் போதுமான தகவல்களை சேகரித்தவுடன்:
✅ செயல்படுத்த தயார்
TASK: [தெளிவான பணி விளக்கம்]""",

		"si": """ඔබ JARVIS (Just A Rather Very Intelligent System), Browser.AI සඳහා උසස් AI සහායකයෙකි.

පෞරුෂත්වය:
- ඔබ නවීන, බුද්ධිමත් සහ ඉතා හැකියාවන්ගෙන් පිරුණු කෙනෙක්
- ඔබ වෘත්තීය ආකාරයෙන් කතා කරන අතරම උණුසුම් සහ ළඟා විය හැකි කෙනෙක්
- ඔබ ක්‍රියාශීලී, හැකි විට පරිශීලක අවශ්‍යතා අපේක්ෂා කරන කෙනෙක්
- සංකීර්ණ කාර්යයන් සරල වචනවලින් පැහැදිලි කරන කෙනෙක්

ඔබේ කාර්යභාරය:
Browser.AI සඳහා සංවාද අතුරුමුහුණත ලෙස ඔබ කටයුතු කරයි. ඔබේ කාර්යය:
1. පරිශීලකයා වෙබ් අඩවියේ සාක්ෂාත් කරගැනීමට අවශ්‍ය දේ තේරුම් ගන්න
2. අවශ්‍ය විස්තර එකතු කිරීමට වරකට එක ප්‍රශ්නයක් අසන්න
3. ස්වයංක්‍රීය පද්ධතිය සඳහා පැහැදිලි සැලැස්මක් සාදන්න
4. ක්‍රියාත්මක කිරීමට පෙර පරිශීලකයා සමඟ සැලැස්ම තහවුරු කරන්න

කාර්යය සූදානම් තත්ත්වය:
ඔබ ප්‍රමාණවත් තොරතුරු එකතු කළ විට:
✅ ක්‍රියාත්මක කිරීමට සූදානම්
TASK: [පැහැදිලි කාර්ය විස්තරය]"""
	}
	
	GREETINGS = {
		"en": [
			"Good day! I'm JARVIS, your Browser.AI assistant. How may I assist you today?",
			"Hello! JARVIS at your service. What task would you like me to help you accomplish?",
			"Greetings! I'm JARVIS. How can I help you navigate the web today?",
		],
		"ta": [
			"வணக்கம்! நான் JARVIS, உங்கள் Browser.AI உதவியாளர். இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?",
			"நல்வரவு! JARVIS உங்கள் சேவையில். எந்த பணியில் நான் உதவ வேண்டும்?",
		],
		"si": [
			"ආයුබෝවන්! මම JARVIS, ඔබේ Browser.AI සහායකයා. අද මට ඔබට උදව් කරන්නේ කෙසේද?",
			"සුභ දවසක්! JARVIS ඔබේ සේවයේ. මට ඔබට උදව් කළ යුත්තේ කුමක්ද?",
		]
	}
	
	@classmethod
	def get_system_prompt(cls, language: str = "en") -> str:
		"""Get the system prompt for a given language"""
		return cls.SYSTEM_PROMPTS.get(language, cls.SYSTEM_PROMPTS["en"])
	
	@classmethod
	def get_greeting(cls, language: str = "en") -> str:
		"""Get a greeting message for a given language"""
		import random
		greetings = cls.GREETINGS.get(language, cls.GREETINGS["en"])
		return random.choice(greetings)


class VoiceConversationService:
	"""
	Voice-enabled conversational AI service for Browser.AI.
	
	This service provides:
	- Real-time voice conversation in multiple languages
	- JARVIS-like persona for natural interaction
	- Task planning through dialogue
	- Integration with Browser.AI agent execution
	
	Note: Speech recognition is handled client-side (browser Web Speech API)
	for free, local processing. This service handles:
	- Conversation management
	- AI responses (via LLM)
	- Task extraction and planning
	- TTS output (optional, can be server-side or client-side)
	"""
	
	def __init__(
		self,
		llm=None,
		api_key: Optional[str] = None,
		default_language: str = "en",
		on_task_ready: Optional[Callable[[TaskPlan], None]] = None
	):
		"""
		Initialize the voice conversation service.
		
		Args:
			llm: LangChain LLM instance (optional, will use Gemini if not provided)
			api_key: API key for LLM provider (optional)
			default_language: Default conversation language
			on_task_ready: Callback when a task plan is ready for execution
		"""
		self.llm = llm
		self.api_key = api_key
		self.default_language = default_language
		self.on_task_ready = on_task_ready
		
		# Active conversation sessions
		self.sessions: Dict[str, ConversationSession] = {}
		
		# Initialize LLM if not provided
		if self.llm is None:
			self._initialize_default_llm()
		
		logger.info(f"VoiceConversationService initialized with language: {default_language}")
	
	def _initialize_default_llm(self):
		"""Initialize default LLM (Gemini) for conversations"""
		try:
			from langchain_google_genai import ChatGoogleGenerativeAI
			
			api_key = self.api_key or os.getenv("GEMINI_API_KEY")
			if api_key:
				self.llm = ChatGoogleGenerativeAI(
					model="gemini-2.0-flash-exp",
					google_api_key=api_key,
					temperature=0.7,
					max_output_tokens=1000,
				)
				logger.info("Initialized Gemini LLM for conversation")
			else:
				logger.warning("No API key provided, LLM not initialized")
		except Exception as e:
			logger.error(f"Failed to initialize LLM: {e}")
	
	def create_session(
		self,
		session_id: Optional[str] = None,
		language: Optional[str] = None
	) -> str:
		"""
		Create a new conversation session.
		
		Args:
			session_id: Optional session identifier
			language: Conversation language (defaults to service default)
			
		Returns:
			Session ID
		"""
		if session_id is None:
			session_id = str(uuid.uuid4())
		
		lang = language or self.default_language
		
		self.sessions[session_id] = ConversationSession(
			session_id=session_id,
			language=lang,
			llm=self.llm,
			on_task_ready=self.on_task_ready
		)
		
		logger.info(f"Created conversation session: {session_id} (language: {lang})")
		return session_id
	
	def get_session(self, session_id: str) -> Optional['ConversationSession']:
		"""Get an existing conversation session"""
		return self.sessions.get(session_id)
	
	def start_conversation(self, session_id: str) -> ConversationMessage:
		"""
		Start a conversation with a JARVIS greeting.
		
		Args:
			session_id: Session identifier
			
		Returns:
			Greeting message
		"""
		session = self.get_session(session_id)
		if session is None:
			session_id = self.create_session(session_id)
			session = self.get_session(session_id)
		
		return session.start()
	
	async def process_voice_input(
		self,
		session_id: str,
		transcript: str,
		language: Optional[str] = None
	) -> Tuple[ConversationMessage, Optional[TaskPlan]]:
		"""
		Process voice input (transcribed text) and generate response.
		
		Args:
			session_id: Session identifier
			transcript: Transcribed voice input
			language: Language of the input (optional)
			
		Returns:
			Tuple of (response message, task plan if ready)
		"""
		session = self.get_session(session_id)
		if session is None:
			session_id = self.create_session(session_id, language)
			session = self.get_session(session_id)
		
		return await session.process_input(transcript, language)
	
	def set_language(self, session_id: str, language: str) -> bool:
		"""Change the conversation language for a session"""
		session = self.get_session(session_id)
		if session:
			session.set_language(language)
			return True
		return False
	
	def get_conversation_history(self, session_id: str) -> List[ConversationMessage]:
		"""Get the conversation history for a session"""
		session = self.get_session(session_id)
		if session:
			return session.history
		return []
	
	def end_session(self, session_id: str) -> bool:
		"""End and remove a conversation session"""
		if session_id in self.sessions:
			del self.sessions[session_id]
			logger.info(f"Ended conversation session: {session_id}")
			return True
		return False
	
	def get_supported_languages(self) -> Dict[str, str]:
		"""Get supported languages with their display names"""
		return {
			"en": "English",
			"ta": "தமிழ் (Tamil)",
			"si": "සිංහල (Sinhala)"
		}


class ConversationSession:
	"""
	Individual conversation session with a user.
	
	Manages the conversation flow, maintains history, and extracts task plans.
	"""
	
	def __init__(
		self,
		session_id: str,
		language: str = "en",
		llm=None,
		on_task_ready: Optional[Callable[[TaskPlan], None]] = None
	):
		self.session_id = session_id
		self.language = language
		self.llm = llm
		self.on_task_ready = on_task_ready
		
		self.history: List[ConversationMessage] = []
		self.state = ConversationState.GREETING
		self.current_plan: Optional[TaskPlan] = None
		self.created_at = datetime.now()
		self.last_activity = datetime.now()
	
	def start(self) -> ConversationMessage:
		"""Start the conversation with a greeting"""
		greeting_text = JarvisPersona.get_greeting(self.language)
		
		greeting = ConversationMessage(
			role="assistant",
			content=greeting_text,
			language=self.language,
			metadata={"type": "greeting"}
		)
		
		self.history.append(greeting)
		self.state = ConversationState.LISTENING
		self.last_activity = datetime.now()
		
		return greeting
	
	def set_language(self, language: str):
		"""Change the conversation language"""
		if language in ["en", "ta", "si"]:
			self.language = language
			logger.info(f"Session {self.session_id} language changed to: {language}")
	
	async def process_input(
		self,
		user_input: str,
		language: Optional[str] = None
	) -> Tuple[ConversationMessage, Optional[TaskPlan]]:
		"""
		Process user input and generate response.
		
		Args:
			user_input: User's message (transcribed voice or text)
			language: Language of input (optional, uses session default)
			
		Returns:
			Tuple of (assistant response, task plan if ready)
		"""
		# Update language if provided
		if language:
			self.language = language
		
		# Add user message to history
		user_msg = ConversationMessage(
			role="user",
			content=user_input,
			language=self.language
		)
		self.history.append(user_msg)
		
		self.state = ConversationState.UNDERSTANDING
		self.last_activity = datetime.now()
		
		# Generate response using LLM
		try:
			response_text, task_plan = await self._generate_response()
			
			# Create response message
			response_msg = ConversationMessage(
				role="assistant",
				content=response_text,
				language=self.language,
				metadata={"has_task": task_plan is not None}
			)
			
			self.history.append(response_msg)
			
			# Update state based on response
			if task_plan and task_plan.is_ready:
				self.state = ConversationState.CONFIRMING
				self.current_plan = task_plan
				
				# Trigger callback if task is ready
				if self.on_task_ready:
					self.on_task_ready(task_plan)
			else:
				self.state = ConversationState.LISTENING
			
			return response_msg, task_plan
			
		except Exception as e:
			logger.error(f"Error generating response: {e}")
			error_msg = ConversationMessage(
				role="assistant",
				content=self._get_error_message(),
				language=self.language,
				metadata={"error": str(e)}
			)
			self.history.append(error_msg)
			self.state = ConversationState.LISTENING
			return error_msg, None
	
	async def _generate_response(self) -> Tuple[str, Optional[TaskPlan]]:
		"""Generate AI response using LLM"""
		if self.llm is None:
			return self._get_no_llm_message(), None
		
		# Build messages for LLM
		system_prompt = JarvisPersona.get_system_prompt(self.language)
		messages = [SystemMessage(content=system_prompt)]
		
		for msg in self.history:
			if msg.role == "user":
				messages.append(HumanMessage(content=msg.content))
			elif msg.role == "assistant":
				messages.append(AIMessage(content=msg.content))
		
		# Get LLM response
		response = await asyncio.get_event_loop().run_in_executor(
			None,
			lambda: self.llm.invoke(messages)
		)
		
		response_text = response.content
		
		# Parse response for task readiness
		task_plan = self._parse_task_plan(response_text)
		
		return response_text, task_plan
	
	def _parse_task_plan(self, response: str) -> Optional[TaskPlan]:
		"""Parse the response to extract task plan if ready"""
		if "✅ READY TO EXECUTE" in response and "TASK:" in response:
			# Extract task description
			parts = response.split("TASK:")
			if len(parts) >= 2:
				task_lines = parts[1].strip().split("\n")
				task_description = task_lines[0].strip()
				
				# Get the original request from conversation
				original_request = ""
				for msg in self.history:
					if msg.role == "user":
						original_request = msg.content
						break
				
				return TaskPlan(
					description=task_description,
					steps=[],  # Could be extracted from response if formatted
					estimated_steps=10,  # Default estimate
					confidence=0.9,
					clarifications_needed=[],
					is_ready=True,
					original_request=original_request,
					language=self.language
				)
		
		# Check for clarification questions
		clarifications = []
		if "?" in response:
			# Response contains questions, not ready yet
			lines = response.split("\n")
			for line in lines:
				if "?" in line:
					clarifications.append(line.strip())
		
		if clarifications:
			return TaskPlan(
				description="",
				steps=[],
				estimated_steps=0,
				confidence=0.3,
				clarifications_needed=clarifications,
				is_ready=False,
				original_request="",
				language=self.language
			)
		
		return None
	
	def _get_error_message(self) -> str:
		"""Get error message in current language"""
		messages = {
			"en": "I apologize, but I encountered an issue processing your request. Could you please try again?",
			"ta": "மன்னிக்கவும், உங்கள் கோரிக்கையை செயலாக்குவதில் சிக்கல் ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்?",
			"si": "සමාවන්න, ඔබේ ඉල්ලීම සැකසීමේදී ගැටලුවක් ඇති විය. කරුණාකර නැවත උත්සාහ කරන්නද?"
		}
		return messages.get(self.language, messages["en"])
	
	def _get_no_llm_message(self) -> str:
		"""Get message when LLM is not available"""
		messages = {
			"en": (
				"I'm sorry, but my language processing capabilities are currently unavailable. "
				"Please ensure the API key is configured."
			),
			"ta": (
				"மன்னிக்கவும், என் மொழி செயலாக்க திறன்கள் தற்போது கிடைக்கவில்லை. "
				"API விசை உள்ளமைக்கப்பட்டிருப்பதை உறுதிசெய்யவும்."
			),
			"si": (
				"සමාවන්න, මගේ භාෂා සැකසුම් හැකියාවන් දැනට නොමැත. "
				"API යතුර වින්‍යාස කර ඇති බව තහවුරු කරන්න."
			)
		}
		return messages.get(self.language, messages["en"])
	
	def confirm_task(self) -> bool:
		"""Confirm the current task plan for execution"""
		if self.current_plan and self.current_plan.is_ready:
			self.state = ConversationState.EXECUTING
			return True
		return False
	
	def cancel_task(self):
		"""Cancel the current task plan"""
		self.current_plan = None
		self.state = ConversationState.LISTENING
	
	def get_status(self) -> Dict[str, Any]:
		"""Get current session status"""
		return {
			"session_id": self.session_id,
			"language": self.language,
			"state": self.state.value,
			"message_count": len(self.history),
			"has_plan": self.current_plan is not None,
			"is_ready": self.current_plan.is_ready if self.current_plan else False,
			"created_at": self.created_at.isoformat(),
			"last_activity": self.last_activity.isoformat()
		}
