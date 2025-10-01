"""
Configuration Panel Component for Streamlit

Provides interface for configuring LLM settings and API keys.
"""

import streamlit as st
import requests
from typing import Dict, Any, List
import json


class ConfigPanel:
    """Configuration panel for LLM settings"""
    
    def __init__(self):
        # Initialize session state
        if 'current_config' not in st.session_state:
            st.session_state.current_config = None
        if 'config_valid' not in st.session_state:
            st.session_state.config_valid = False
    
    def render(self):
        """Render the configuration panel"""
        with st.expander("⚙️ Configuration", expanded=not st.session_state.config_valid):
            self._render_llm_config()
            self._render_browser_config()
            self._render_advanced_config()
            self._render_config_actions()
    
    def _render_llm_config(self):
        """Render LLM configuration section"""
        st.subheader("🧠 LLM Configuration")
        
        # Get available providers
        providers = self._get_providers()
        provider_names = [p['provider'] for p in providers]
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_provider = st.selectbox(
                "Provider",
                options=provider_names,
                index=0 if provider_names else None,
                help="Choose your LLM provider"
            )
        
        if selected_provider:
            provider_info = next(p for p in providers if p['provider'] == selected_provider)
            requirements = provider_info.get('requirements', {})
            
            with col2:
                models = requirements.get('models', [])
                selected_model = st.selectbox(
                    "Model",
                    options=models,
                    index=0 if models else None,
                    help="Choose the model to use"
                )
            
            # API Key configuration
            if requirements.get('api_key_required'):
                api_key = st.text_input(
                    f"{selected_provider.upper()} API Key",
                    type="password",
                    help=f"Enter your {selected_provider} API key"
                )
                
                if not api_key:
                    env_var = requirements.get('api_key_env', '')
                    st.info(f"💡 You can also set the environment variable: `{env_var}`")
            else:
                api_key = None
            
            # Base URL for providers like Ollama
            if requirements.get('base_url_required'):
                base_url = st.text_input(
                    "Base URL",
                    value=requirements.get('default_base_url', 'http://localhost:11434'),
                    help="Base URL for the LLM service"
                )
            else:
                base_url = None
            
            # Temperature setting
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
                help="Controls randomness in responses. 0 = deterministic, 1 = very random"
            )
            
            # Build LLM config
            llm_config = {
                'provider': selected_provider,
                'model': selected_model,
                'temperature': temperature
            }
            
            if api_key:
                llm_config['api_key'] = api_key
            if base_url:
                llm_config['base_url'] = base_url
            
            # Store in session state
            if 'current_config' not in st.session_state:
                st.session_state.current_config = {}
            
            st.session_state.current_config['llm'] = llm_config
    
    def _render_browser_config(self):
        """Render browser configuration section"""
        st.subheader("🌐 Browser Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_vision = st.checkbox(
                "Use Vision",
                value=True,
                help="Enable vision capabilities for screenshot analysis"
            )
        
        with col2:
            headless = st.checkbox(
                "Headless Mode",
                value=True,
                help="Run browser in headless mode (no GUI)"
            )
        
        browser_config = {
            'use_vision': use_vision,
            'headless': headless
        }
        
        if 'current_config' not in st.session_state:
            st.session_state.current_config = {}
        
        st.session_state.current_config['browser'] = browser_config
    
    def _render_advanced_config(self):
        """Render advanced configuration section"""
        with st.expander("🔧 Advanced Settings"):
            max_failures = st.number_input(
                "Max Failures",
                min_value=1,
                max_value=10,
                value=3,
                help="Maximum number of failures before giving up"
            )
            
            if 'current_config' not in st.session_state:
                st.session_state.current_config = {}
            
            st.session_state.current_config['max_failures'] = max_failures
    
    def _render_config_actions(self):
        """Render configuration action buttons"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Test Configuration", type="primary"):
                self._test_configuration()
        
        with col2:
            if st.button("💾 Save Configuration"):
                self._save_configuration()
        
        with col3:
            if st.button("🔄 Reset to Default"):
                self._reset_configuration()
        
        # Show configuration status
        if st.session_state.config_valid:
            st.success("✅ Configuration is valid and ready to use!")
        elif st.session_state.current_config:
            st.warning("⚠️ Please test your configuration before starting tasks")
    
    def _get_providers(self) -> List[Dict[str, Any]]:
        """Get available LLM providers from backend"""
        try:
            response = requests.get("http://localhost:8000/config/providers")
            if response.status_code == 200:
                return response.json()
            else:
                st.error("Failed to get providers from backend")
                return []
        except requests.exceptions.RequestException:
            st.error("Backend not available. Please start the backend server.")
            return []
    
    def _test_configuration(self):
        """Test the current configuration"""
        if not st.session_state.current_config:
            st.error("No configuration to test")
            return
        
        try:
            response = requests.post(
                "http://localhost:8000/config/test",
                json={'config': st.session_state.current_config}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    st.success("✅ Configuration test passed!")
                    st.session_state.config_valid = True
                else:
                    st.error(f"❌ Configuration test failed: {result.get('error', 'Unknown error')}")
                    st.session_state.config_valid = False
            else:
                st.error("Failed to test configuration")
                st.session_state.config_valid = False
                
        except requests.exceptions.RequestException as e:
            st.error(f"Error testing configuration: {str(e)}")
            st.session_state.config_valid = False
    
    def _save_configuration(self):
        """Save configuration (to session state for now)"""
        if st.session_state.current_config:
            # In a real app, this would save to a database or file
            st.success("💾 Configuration saved successfully!")
            st.json(st.session_state.current_config)
        else:
            st.error("No configuration to save")
    
    def _reset_configuration(self):
        """Reset configuration to default"""
        try:
            response = requests.get("http://localhost:8000/config/default")
            if response.status_code == 200:
                st.session_state.current_config = response.json()
                st.session_state.config_valid = False
                st.success("🔄 Configuration reset to default")
                st.rerun()
            else:
                st.error("Failed to get default configuration")
        except requests.exceptions.RequestException:
            st.error("Backend not available")
    
    def get_current_config(self) -> Dict[str, Any]:
        """Get the current configuration"""
        return st.session_state.get('current_config', {})
    
    def is_config_valid(self) -> bool:
        """Check if current configuration is valid"""
        return st.session_state.get('config_valid', False)