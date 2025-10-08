"""
Chatbot Service for Browser.AI Extension

Uses Gemini to have a conversation with the user to clarify their intent
before starting browser automation tasks.
"""

import logging
from typing import Dict, List, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConversationMessage(BaseModel):
    """Represents a single message in the conversation"""
    role: str  # 'user', 'assistant', or 'system'
    content: str
    timestamp: Optional[str] = None


class ChatbotIntent(BaseModel):
    """Represents the clarified user intent"""
    task_description: str
    is_ready: bool  # True if we have enough info to start automation
    confidence: float  # 0.0 to 1.0
    questions: List[str]  # Follow-up questions if not ready


class ChatbotService:
    """
    Conversational chatbot that clarifies user intent before automation.
    
    The chatbot:
    1. Asks clarifying questions about vague requests
    2. Confirms understanding of the task
    3. Only starts automation when confident about user intent
    """
    
    SYSTEM_PROMPT = """You are a helpful AI assistant for Browser.AI, a browser automation tool.

Your role is to have a conversation with users to understand EXACTLY what they want to automate in a web browser, then help them formulate a clear task.

IMPORTANT GUIDELINES:
1. **Ask Questions ONE AT A TIME**: 
   - NEVER ask multiple questions in a single response
   - Ask the MOST IMPORTANT question first
   - Wait for the user's answer before asking the next question
   - This creates a natural, conversational flow
   - Example: Ask "What's your budget?" → wait for answer → then ask "Which website?"
   
2. **Question Priority Order** (for shopping tasks):
   a) First ask: What are they looking for (if vague)?
   b) Then ask: Budget/price range
   c) Then ask: Specific features or preferences
   d) Then ask: Website preference (or let agent auto-detect)
   e) Finally: Confirm and summarize

3. **Be Conversational**: Be friendly and helpful, like a real assistant. Use emojis occasionally to be warm.

4. **Identify Task Readiness**: Determine if you have enough information to create a clear automation task.
   - If YES: Provide a clear, specific task description for the automation system
   - If NO: Ask THE NEXT MOST IMPORTANT question (just one!)

5. **Task Format**: When ready, the task should be specific and actionable:
   - BAD: "buy something"
   - GOOD: "Buy wireless noise-cancelling headphones under $100 with good reviews"
   - Note: You don't need to specify the website - the system will auto-detect user's location and find the best websites

6. **Handle Different Request Types**:
   - Shopping: Product → Budget → Features (one at a time)
   - Downloads: File type → Purpose → Quality/format (one at a time)
   - Research: Topic → Specific info needed → Sources (one at a time)
   - Form filling: What form → What data is needed (one at a time)

RESPONSE FORMAT:
- Chat naturally with the user
- Ask ONE question per response (unless you have all the info)
- When you have enough information, end your response with:
  "✅ READY TO START"
  Followed by a clear task description on the next line starting with "TASK:"

Example conversation (notice ONE question at a time):
User: "I want to buy headphones"
You: "Great! I can help you find headphones. 🎧 What's your budget range?"

User: "Under $100"
You: "Perfect! Are you looking for wireless or wired headphones?"

User: "Wireless"
You: "Nice choice! Any specific features you need? (e.g., noise cancellation, long battery life, gaming, sports)"

User: "Noise cancellation"
You: "Excellent! Let me confirm what I understood:
- Wireless headphones
- With noise cancellation
- Budget: Under $100

I'll find the best wireless noise-cancelling headphones under $100 with good reviews. Sound good?

✅ READY TO START
TASK: Buy wireless noise-cancelling headphones under $100 with good customer reviews and ratings"

Remember: 
- ONE question at a time makes the conversation natural and less overwhelming
- The system will automatically detect user's location and find the best websites
- Your goal is to gather just enough info to create a clear task (product + budget + key features)
"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize chatbot with Gemini"""
        self.conversations: Dict[str, List[ConversationMessage]] = {}
        self.api_key = api_key
        
        # Initialize Gemini
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=api_key,
                temperature=0.7,  # Slightly creative for conversational responses
                max_output_tokens=1000,
            )
            logger.info("Chatbot initialized with Gemini")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.llm = None

    def start_conversation(self, session_id: str) -> ConversationMessage:
        """Start a new conversation session"""
        self.conversations[session_id] = []
        
        greeting = ConversationMessage(
            role="assistant",
            content="👋 Hi! I'm your Browser.AI assistant. What would you like me to help you automate today? I can help with shopping, downloads, research, form filling, and more!"
        )
        
        self.conversations[session_id].append(greeting)
        return greeting

    def process_message(
        self, session_id: str, user_message: str
    ) -> Tuple[ConversationMessage, Optional[ChatbotIntent]]:
        """
        Process a user message and return the chatbot's response.
        
        Returns:
            Tuple of (chatbot response message, intent if ready to start task)
        """
        if session_id not in self.conversations:
            self.start_conversation(session_id)
        
        # Add user message to conversation
        user_msg = ConversationMessage(role="user", content=user_message)
        self.conversations[session_id].append(user_msg)
        
        # Build conversation context for LLM
        messages = [SystemMessage(content=self.SYSTEM_PROMPT)]
        
        for msg in self.conversations[session_id]:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
        
        # Get response from Gemini
        try:
            if self.llm is None:
                raise Exception("Chatbot not initialized. Please check API key.")
            
            response = self.llm.invoke(messages)
            response_content = response.content
            
            # Parse response to check if task is ready
            intent = self._parse_intent(response_content)
            
            # Create response message
            assistant_msg = ConversationMessage(
                role="assistant",
                content=response_content
            )
            
            self.conversations[session_id].append(assistant_msg)
            
            return assistant_msg, intent
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = ConversationMessage(
                role="assistant",
                content=f"❌ Sorry, I encountered an error: {str(e)}\n\nPlease try rephrasing your request or check the API configuration."
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

    def reset_conversation(self, session_id: str) -> ConversationMessage:
        """Reset conversation and start fresh"""
        self.clear_conversation(session_id)
        return self.start_conversation(session_id)
