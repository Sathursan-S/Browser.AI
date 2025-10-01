"""
Main Streamlit Application for Browser.AI Chat Interface

GitHub Copilot-like interface for Browser.AI automation with real-time updates.
"""

import streamlit as st
import sys
from pathlib import Path
import time

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import components
from components.chat_interface import ChatInterface
from components.config_panel import ConfigPanel
from components.status_display import StatusDisplay
from utils.websocket_client import SimpleWebSocketClient

# Page configuration
st.set_page_config(
    page_title="Browser.AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    
    .stChatMessage {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.5rem;
    }
    
    .stChatMessage[data-testid="user-message"] {
        background-color: #f0f2f6;
        border-left: 4px solid #1f77b4;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background-color: #ffffff;
        border-left: 4px solid #2ca02c;
    }
    
    .status-running {
        color: #ff6b35;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.ws_client = SimpleWebSocketClient()
        st.session_state.last_backend_check = 0


def check_backend_connection():
    """Check if backend is running"""
    current_time = time.time()
    
    # Check only every 30 seconds
    if current_time - st.session_state.last_backend_check > 30:
        st.session_state.last_backend_check = current_time
        
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            st.session_state.backend_available = response.status_code == 200
        except:
            st.session_state.backend_available = False


def render_header():
    """Render application header"""
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <h1>🤖 Browser.AI Assistant</h1>
            <p style="color: #666; margin: 0;">Intelligent Web Automation with Real-time Chat</p>
        </div>
        """, unsafe_allow_html=True)


def render_backend_status():
    """Render backend connection status"""
    if hasattr(st.session_state, 'backend_available'):
        if st.session_state.backend_available:
            st.success("🟢 Backend Connected")
        else:
            st.error("🔴 Backend Unavailable - Please start the backend server")
            st.code("cd chat_interface/backend && python main.py")
            st.stop()
    else:
        st.warning("🟡 Checking backend connection...")


def main():
    """Main application function"""
    initialize_session_state()
    check_backend_connection()
    
    render_header()
    render_backend_status()
    
    # Initialize components
    config_panel = ConfigPanel()
    status_display = StatusDisplay()
    chat_interface = ChatInterface(st.session_state.ws_client)
    
    # Main layout
    main_col, sidebar_col = st.columns([3, 1])
    
    with main_col:
        # Configuration panel (collapsible)
        config_panel.render()
        
        # Chat interface (main content)
        chat_interface.render()
    
    with sidebar_col:
        # Status display in sidebar
        status_display.render()
    
    # Navigation tabs at bottom
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "📋 Logs", "📚 History"])
    
    with tab1:
        # Main chat is rendered above
        st.info("💡 **Tips:**\n"
               "- Describe what you want to automate in natural language\n"
               "- Be specific about the website and actions needed\n"
               "- Use the stop button to cancel running tasks\n"
               "- Check the sidebar for real-time status updates")
    
    with tab2:
        # Detailed logs view
        status_display.render_detailed_logs()
    
    with tab3:
        # Task history view
        status_display.render_task_history()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧹 Clear Chat"):
            chat_interface.clear_chat()
    
    with col2:
        if st.button("🔄 Refresh Status"):
            st.rerun()
    
    with col3:
        st.markdown("*Powered by Browser.AI*")
    
    # Auto-refresh for real-time updates (every 10 seconds)
    if st.session_state.get('task_running', False):
        time.sleep(10)
        st.rerun()


if __name__ == "__main__":
    main()