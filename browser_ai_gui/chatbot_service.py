"""
Chatbot Service for Browser.AI Extension

Uses Gemini to have a conversation with the user to clarify their intent
before starting browser automation tasks.

Features a JARVIS-inspired persona with multi-language support (English, Tamil, Sinhala).

Now supports Pipecat for more realistic real-time voice conversations.
"""

import logging
import random
from typing import Dict, List, Optional, Tuple

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

# Optional Pipecat support
try:
    from .services.pipecat_voice_service import (
        PIPECAT_AVAILABLE,
        PipecatVoiceService,
        create_pipecat_voice_service,
    )
except ImportError:
    PIPECAT_AVAILABLE = False
    PipecatVoiceService = None
    create_pipecat_voice_service = None

logger = logging.getLogger(__name__)


class ConversationMessage(BaseModel):
    """Represents a single message in the conversation"""
    role: str  # 'user', 'assistant', or 'system'
    content: str
    timestamp: Optional[str] = None
    language: str = "en"  # Language code


class ChatbotIntent(BaseModel):
    """Represents the clarified user intent"""
    task_description: str
    is_ready: bool  # True if we have enough info to start automation
    confidence: float  # 0.0 to 1.0
    questions: List[str]  # Follow-up questions if not ready


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
   ✅ READY TO START
   TASK: [clear, specific task description]

Example responses:
"Good day! I'm JARVIS, your Browser.AI assistant. How may I assist you today?"
"Certainly, Sir. Before I proceed, may I ask what your budget preference is?"
"Very well. Allow me to summarize: You'd like me to find wireless headphones under $100 with noise cancellation. Shall I proceed?"

Remember: 
- ONE question at a time makes the conversation natural and less overwhelming
- The system will automatically detect user's location and find the best websites
- Your goal is to gather just enough info to create a clear task (product + budget + key features)""",

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
✅ தொடங்க தயார்
TASK: [தெளிவான பணி விளக்கம்]

நினைவில் கொள்ளுங்கள்: தமிழிலும் பேசலாம், ஆங்கிலத்திலும் பதிலளிக்கலாம்.""",

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
✅ ආරම්භ කිරීමට සූදානම්
TASK: [පැහැදිලි කාර්ය විස්තරය]

මතක තබාගන්න: සිංහලෙන් කතා කරන්න, ඉංග්‍රීසියෙන්ද පිළිතුරු දිය හැක."""
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
        greetings = cls.GREETINGS.get(language, cls.GREETINGS["en"])
        return random.choice(greetings)


class ChatbotService:
    """
    Conversational chatbot that clarifies user intent before automation.
    
    Features JARVIS-inspired persona with multi-language support.
    
    The chatbot:
    1. Asks clarifying questions about vague requests
    2. Confirms understanding of the task
    3. Only starts automation when confident about user intent
    """
    
    # Supported languages
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "ta": "தமிழ் (Tamil)",
        "si": "සිංහල (Sinhala)"
    }

    def __init__(self, api_key: Optional[str] = None, default_language: str = "en"):
        """Initialize chatbot with Gemini"""
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.session_languages: Dict[str, str] = {}  # Track language per session
        self.api_key = api_key
        self.default_language = default_language
        
        # Initialize Gemini
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=api_key,
                temperature=0.7,  # Slightly creative for conversational responses
                max_output_tokens=1000,
            )
            logger.info("JARVIS Chatbot initialized with Gemini")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.llm = None

    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages"""
        return self.SUPPORTED_LANGUAGES.copy()

    def set_language(self, session_id: str, language: str) -> bool:
        """Set the language for a session"""
        if language in self.SUPPORTED_LANGUAGES:
            self.session_languages[session_id] = language
            logger.info(f"Session {session_id} language set to: {language}")
            return True
        return False

    def get_language(self, session_id: str) -> str:
        """Get the language for a session"""
        return self.session_languages.get(session_id, self.default_language)

    def start_conversation(self, session_id: str, language: Optional[str] = None) -> ConversationMessage:
        """Start a new conversation session with JARVIS greeting"""
        self.conversations[session_id] = []
        
        # Set language for session
        lang = language or self.default_language
        if lang in self.SUPPORTED_LANGUAGES:
            self.session_languages[session_id] = lang
        else:
            lang = self.default_language
            self.session_languages[session_id] = lang
        
        greeting = ConversationMessage(
            role="assistant",
            content=JarvisPersona.get_greeting(lang),
            language=lang
        )
        
        self.conversations[session_id].append(greeting)
        return greeting

    def process_message(
        self, session_id: str, user_message: str, language: Optional[str] = None
    ) -> Tuple[ConversationMessage, Optional[ChatbotIntent]]:
        """
        Process a user message and return the chatbot's response.
        
        Args:
            session_id: Session identifier
            user_message: The user's message
            language: Optional language override
        
        Returns:
            Tuple of (chatbot response message, intent if ready to start task)
        """
        if session_id not in self.conversations:
            self.start_conversation(session_id, language)
        
        # Update language if provided
        if language and language in self.SUPPORTED_LANGUAGES:
            self.session_languages[session_id] = language
        
        lang = self.get_language(session_id)
        
        # Add user message to conversation
        user_msg = ConversationMessage(role="user", content=user_message, language=lang)
        self.conversations[session_id].append(user_msg)
        
        # Build conversation context for LLM with JARVIS persona
        system_prompt = JarvisPersona.get_system_prompt(lang)
        messages = [SystemMessage(content=system_prompt)]
        
        for msg in self.conversations[session_id]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        
        # Get response from Gemini
        try:
            if self.llm is None:
                raise Exception("JARVIS not initialized. Please check API key.")
            
            response = self.llm.invoke(messages)
            response_content = response.content
            
            # Parse response to check if task is ready
            intent = self._parse_intent(response_content)
            
            # Create response message
            assistant_msg = ConversationMessage(
                role="assistant",
                content=response_content,
                language=lang
            )
            
            self.conversations[session_id].append(assistant_msg)
            
            return assistant_msg, intent
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            # Sanitize error message to avoid exposing sensitive information
            safe_error = "connection issue" if "api" in str(e).lower() else "processing error"
            
            error_messages = {
                "en": (
                    f"❌ I apologize, Sir, but I encountered a {safe_error}.\n\n"
                    "Please try rephrasing your request or check the API configuration."
                ),
                "ta": (
                    f"❌ மன்னிக்கவும், ஒரு {safe_error} ஏற்பட்டது.\n\n"
                    "உங்கள் கோரிக்கையை மீண்டும் சொல்லவும் அல்லது API உள்ளமைவை சரிபார்க்கவும்."
                ),
                "si": (
                    f"❌ සමාවන්න, {safe_error}ක් ඇති විය.\n\n"
                    "කරුණාකර ඔබේ ඉල්ලීම නැවත පවසන්න හෝ API වින්‍යාසය පරීක්ෂා කරන්න."
                )
            }
            error_msg = ConversationMessage(
                role="assistant",
                content=error_messages.get(lang, error_messages["en"]),
                language=lang
            )
            self.conversations[session_id].append(error_msg)
            return error_msg, None

    def _parse_intent(self, response: str) -> Optional[ChatbotIntent]:
        """Parse the chatbot response to extract intent"""
        # Check if response indicates readiness to start
        if "✅ READY TO START" in response and "TASK:" in response:
            # Extract task description
            parts = response.split("TASK:")
            if len(parts) >= 2:
                task_lines = parts[1].strip().split("\n")
                task_description = task_lines[0].strip()
                
                return ChatbotIntent(
                    task_description=task_description,
                    is_ready=True,
                    confidence=0.9,
                    questions=[]
                )
        
        # Not ready yet - extract any questions
        questions = []
        lines = response.split("\n")
        for line in lines:
            if line.strip().startswith("-") or line.strip().startswith("•"):
                questions.append(line.strip().lstrip("-•").strip())
        
        return ChatbotIntent(
            task_description="",
            is_ready=False,
            confidence=0.3,
            questions=questions
        )

    def get_conversation_history(self, session_id: str) -> List[ConversationMessage]:
        """Get the conversation history for a session"""
        return self.conversations.get(session_id, [])

    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
        # Keep language preference

    def reset_conversation(self, session_id: str, language: Optional[str] = None) -> ConversationMessage:
        """Reset conversation and start fresh with JARVIS greeting"""
        # Preserve language if not specified
        lang = language or self.session_languages.get(session_id, self.default_language)
        self.clear_conversation(session_id)
        return self.start_conversation(session_id, lang)
