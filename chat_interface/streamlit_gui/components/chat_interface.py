"""
Chat Interface Component for Streamlit

Provides GitHub Copilot-like chat interface for Browser.AI automation.
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..utils.websocket_client import WebSocketClient


class ChatMessage:
    """Represents a chat message"""
    
    def __init__(self, content: str, is_user: bool, timestamp: datetime = None):
        self.content = content
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()
        self.id = f"{self.timestamp.timestamp()}_{('user' if is_user else 'assistant')}"


class ChatInterface:
    """Main chat interface component"""
    
    def __init__(self, websocket_client: WebSocketClient):
        self.ws_client = websocket_client
        
        # Initialize session state
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        if 'current_task_id' not in st.session_state:
            st.session_state.current_task_id = None
        if 'task_running' not in st.session_state:
            st.session_state.task_running = False
    
    def render(self):
        """Render the chat interface"""
        st.title("🤖 Browser.AI Assistant")
        st.markdown("*Describe your web automation task and I'll help you execute it.*")
        
        # Chat container
        chat_container = st.container()
        
        with chat_container:
            self._render_messages()
        
        # Input area
        self._render_input_area()
        
        # Status area
        self._render_status_area()
    
    def _render_messages(self):
        """Render chat messages"""
        for message in st.session_state.chat_messages:
            with st.chat_message("user" if message.is_user else "assistant"):
                st.write(message.content)
                st.caption(f"*{message.timestamp.strftime('%H:%M:%S')}*")
    
    def _render_input_area(self):
        """Render the input area"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.chat_input(
                "Describe your automation task...",
                disabled=st.session_state.task_running
            )
        
        with col2:
            if st.session_state.task_running:
                if st.button("🛑 Stop", type="secondary"):
                    self._stop_current_task()
            else:
                # Placeholder for consistency
                st.empty()
        
        if user_input and not st.session_state.task_running:
            self._handle_user_input(user_input)
    
    def _render_status_area(self):
        """Render task status area"""
        if st.session_state.task_running:
            with st.container():
                st.markdown("---")
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown("**Status:**")
                
                with col2:
                    # Animated status indicator
                    status_placeholder = st.empty()
                    with status_placeholder.container():
                        st.markdown("🔄 **Running automation task...**")
                        st.progress(0.5)  # Indeterminate progress
    
    def _handle_user_input(self, user_input: str):
        """Handle user input"""
        # Add user message to chat
        user_message = ChatMessage(user_input, is_user=True)
        st.session_state.chat_messages.append(user_message)
        
        # Show assistant thinking
        thinking_message = ChatMessage("🤔 Processing your request...", is_user=False)
        st.session_state.chat_messages.append(thinking_message)
        
        # Start the task
        try:
            task_id = self._start_automation_task(user_input)
            if task_id:
                st.session_state.current_task_id = task_id
                st.session_state.task_running = True
                
                # Update thinking message
                st.session_state.chat_messages[-1].content = (
                    f"✅ Starting automation task: {user_input}\n\n"
                    f"**Task ID:** `{task_id}`\n"
                    f"**Status:** Running\n\n"
                    f"I'll keep you updated with real-time progress..."
                )
            else:
                st.session_state.chat_messages[-1].content = (
                    "❌ Sorry, I couldn't start the automation task. "
                    "Please check your configuration and try again."
                )
        
        except Exception as e:
            st.session_state.chat_messages[-1].content = (
                f"❌ Error starting task: {str(e)}"
            )
        
        st.rerun()
    
    def _start_automation_task(self, description: str) -> Optional[str]:
        """Start an automation task"""
        try:
            # Get current configuration
            config = st.session_state.get('current_config')
            if not config:
                st.error("Please configure your LLM settings first")
                return None
            
            # Send task creation request via WebSocket
            message = {
                'type': 'start_task',
                'description': description,
                'config': config
            }
            
            # This would typically be async, but for Streamlit we'll use the REST API
            import requests
            response = requests.post(
                f"http://localhost:8000/tasks/create",
                json={
                    'description': description,
                    'config': config
                }
            )
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data['task_id']
                
                # Start the task
                start_response = requests.post(f"http://localhost:8000/tasks/{task_id}/start")
                if start_response.status_code == 200:
                    return task_id
            
            return None
            
        except Exception as e:
            st.error(f"Error starting task: {str(e)}")
            return None
    
    def _stop_current_task(self):
        """Stop the current running task"""
        if st.session_state.current_task_id:
            try:
                import requests
                response = requests.post(
                    f"http://localhost:8000/tasks/{st.session_state.current_task_id}/stop"
                )
                
                if response.status_code == 200:
                    st.session_state.task_running = False
                    st.session_state.current_task_id = None
                    
                    # Add stop message
                    stop_message = ChatMessage("🛑 Task stopped by user", is_user=False)
                    st.session_state.chat_messages.append(stop_message)
                    
                    st.rerun()
                else:
                    st.error("Failed to stop task")
            
            except Exception as e:
                st.error(f"Error stopping task: {str(e)}")
    
    def add_log_message(self, log_data: Dict[str, Any]):
        """Add a log message from WebSocket"""
        level = log_data.get('level', 'INFO')
        message = log_data.get('message', '')
        logger_name = log_data.get('logger_name', '')
        
        # Create formatted log message
        if level == 'ERROR':
            emoji = "❌"
        elif level == 'WARNING':
            emoji = "⚠️"
        elif level == 'INFO':
            emoji = "ℹ️"
        else:
            emoji = "📋"
        
        formatted_message = f"{emoji} **{level}** [{logger_name}]\n{message}"
        
        log_message = ChatMessage(formatted_message, is_user=False)
        st.session_state.chat_messages.append(log_message)
    
    def handle_task_completed(self, task_data: Dict[str, Any]):
        """Handle task completion"""
        st.session_state.task_running = False
        st.session_state.current_task_id = None
        
        success = task_data.get('success', False)
        result = task_data.get('result', {})
        
        if success:
            completion_message = ChatMessage(
                f"✅ **Task completed successfully!**\n\n"
                f"**Result:** {result.get('extracted_content', 'Task completed')}\n"
                f"**Status:** {result.get('is_done', 'Done')}",
                is_user=False
            )
        else:
            error = task_data.get('error', 'Unknown error')
            completion_message = ChatMessage(
                f"❌ **Task failed**\n\n"
                f"**Error:** {error}",
                is_user=False
            )
        
        st.session_state.chat_messages.append(completion_message)
        st.rerun()
    
    def clear_chat(self):
        """Clear chat history"""
        st.session_state.chat_messages = []
        st.session_state.current_task_id = None
        st.session_state.task_running = False
        st.rerun()