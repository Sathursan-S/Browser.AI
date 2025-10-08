"""
Configuration Manager for Browser.AI Chat Interface

Manages LLM configurations, API keys, and application settings.
"""

import os
from typing import Dict, Any, Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings
from enum import Enum
import json


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class BrowserAISettings(BaseSettings):
    """Application settings"""
    
    # API Settings
    host: str = Field(default="localhost", env="CHAT_INTERFACE_HOST")
    port: int = Field(default=8000, env="CHAT_INTERFACE_PORT")
    debug: bool = Field(default=False, env="CHAT_INTERFACE_DEBUG")
    
    # Browser.AI Settings
    browser_ai_logging_level: str = Field(default="info", env="BROWSER_AI_LOGGING_LEVEL")
    
    # Default LLM Settings
    default_llm_provider: str = Field(default="openai", env="DEFAULT_LLM_PROVIDER")
    default_llm_model: str = Field(default="gpt-4", env="DEFAULT_LLM_MODEL")
    default_temperature: float = Field(default=0.0, env="DEFAULT_TEMPERATURE")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")
    
    # Ollama Settings
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    
    class Config:
        env_file = ".env"


class ConfigManager:
    """Manages configuration for the chat interface"""
    
    def __init__(self):
        self.settings = BrowserAISettings()
        self.user_configs: Dict[str, Dict[str, Any]] = {}
        
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'llm': {
                'provider': self.settings.default_llm_provider,
                'model': self.settings.default_llm_model,
                'temperature': self.settings.default_temperature,
                'api_key': self._get_api_key(self.settings.default_llm_provider)
            },
            'browser': {
                'use_vision': True,
                'headless': True
            },
            'max_failures': 3
        }
    
    def _get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider"""
        if provider == LLMProvider.OPENAI:
            return self.settings.openai_api_key
        elif provider == LLMProvider.ANTHROPIC:
            return self.settings.anthropic_api_key
        return None
    
    def validate_llm_config(self, config: Dict[str, Any]) -> bool:
        """Validate LLM configuration"""
        llm_config = config.get('llm', {})
        provider = llm_config.get('provider')
        
        if not provider:
            return False
            
        if provider not in [e.value for e in LLMProvider]:
            return False
        
        # Check if API key is provided for external providers
        if provider in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
            api_key = llm_config.get('api_key')
            if not api_key:
                # Try to get from settings
                api_key = self._get_api_key(provider)
                if not api_key:
                    return False
        
        return True
    
    def get_available_models(self, provider: str) -> List[str]:
        """Get available models for a provider"""
        model_map = {
            LLMProvider.OPENAI: [
                "gpt-4",
                "gpt-4-turbo", 
                "gpt-4-turbo-preview",
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k"
            ],
            LLMProvider.ANTHROPIC: [
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
                "claude-2.1",
                "claude-2.0"
            ],
            LLMProvider.OLLAMA: [
                "llama2",
                "llama2:13b",
                "llama2:70b",
                "codellama",
                "mistral",
                "neural-chat",
                "starling-lm"
            ]
        }
        
        return model_map.get(provider, [])
    
    def save_user_config(self, user_id: str, config: Dict[str, Any]) -> bool:
        """Save user configuration"""
        if not self.validate_llm_config(config):
            return False
            
        self.user_configs[user_id] = config
        return True
    
    def get_user_config(self, user_id: str) -> Dict[str, Any]:
        """Get user configuration or default"""
        return self.user_configs.get(user_id, self.get_default_config())
    
    def get_provider_requirements(self, provider: str) -> Dict[str, Any]:
        """Get requirements for a specific provider"""
        requirements = {
            LLMProvider.OPENAI: {
                "api_key_required": True,
                "api_key_env": "OPENAI_API_KEY",
                "supports_vision": True,
                "models": self.get_available_models(LLMProvider.OPENAI)
            },
            LLMProvider.ANTHROPIC: {
                "api_key_required": True, 
                "api_key_env": "ANTHROPIC_API_KEY",
                "supports_vision": True,
                "models": self.get_available_models(LLMProvider.ANTHROPIC)
            },
            LLMProvider.OLLAMA: {
                "api_key_required": False,
                "base_url_required": True,
                "default_base_url": self.settings.ollama_base_url,
                "supports_vision": False,
                "models": self.get_available_models(LLMProvider.OLLAMA)
            }
        }
        
        return requirements.get(provider, {})
    
    def test_llm_connection(self, config: Dict[str, Any]) -> bool:
        """Test LLM connection (basic validation)"""
        # This would ideally test actual connection
        # For now, just validate configuration
        return self.validate_llm_config(config)
    
    def export_config(self, user_id: str) -> str:
        """Export user configuration as JSON"""
        config = self.get_user_config(user_id)
        # Remove sensitive information
        safe_config = config.copy()
        if 'llm' in safe_config and 'api_key' in safe_config['llm']:
            safe_config['llm']['api_key'] = '***HIDDEN***'
        
        return json.dumps(safe_config, indent=2)
    
    def import_config(self, user_id: str, config_json: str) -> bool:
        """Import user configuration from JSON"""
        try:
            config = json.loads(config_json)
            return self.save_user_config(user_id, config)
        except (json.JSONDecodeError, KeyError):
            return False


# Global configuration manager instance
config_manager = ConfigManager()