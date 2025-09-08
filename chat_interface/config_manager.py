"""
Configuration manager for Browser AI chat interface.

Handles LLM configuration, API keys, and application settings.
"""

import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GOOGLE = "google"
    FIREWORKS = "fireworks"
    AWS = "aws"


@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: int = 30
    extra_params: Optional[Dict[str, Any]] = None


@dataclass
class AppConfig:
    """Application configuration"""
    theme: str = "light"
    auto_save: bool = True
    log_level: str = "info"
    max_history_items: int = 100
    auto_scroll: bool = True
    show_timestamps: bool = True
    animate_status: bool = True


class ConfigManager:
    """
    Manages configuration for the Browser AI chat interface.
    Handles LLM settings, API keys, and application preferences.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            self.config_dir = Path.home() / ".browser_ai_chat"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        
        self._llm_configs: Dict[str, LLMConfig] = {}
        self._app_config = AppConfig()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load LLM configurations
                llm_configs_data = data.get('llm_configs', {})
                for name, config_data in llm_configs_data.items():
                    try:
                        config_data['provider'] = LLMProvider(config_data['provider'])
                        self._llm_configs[name] = LLMConfig(**config_data)
                    except Exception as e:
                        print(f"Error loading LLM config {name}: {e}")
                
                # Load app configuration
                app_config_data = data.get('app_config', {})
                self._app_config = AppConfig(**app_config_data)
                
            except Exception as e:
                print(f"Error loading config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration"""
        # Add default OpenAI config if API key is available
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self._llm_configs['openai_gpt4'] = LLMConfig(
                provider=LLMProvider.OPENAI,
                model="gpt-4o-mini",
                api_key=openai_key,
                temperature=0.1
            )
        
        # Add default Anthropic config if API key is available
        anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_key:
            self._llm_configs['claude'] = LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model="claude-3-sonnet-20241022",
                api_key=anthropic_key,
                temperature=0.1
            )
        
        # Add default Ollama config (no API key required)
        self._llm_configs['ollama_llama'] = LLMConfig(
            provider=LLMProvider.OLLAMA,
            model="llama3.2",
            base_url="http://localhost:11434",
            temperature=0.1
        )
        
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Convert LLMConfigs to serializable format
            llm_configs_data = {}
            for name, config in self._llm_configs.items():
                config_dict = asdict(config)
                config_dict['provider'] = config.provider.value
                llm_configs_data[name] = config_dict
            
            data = {
                'llm_configs': llm_configs_data,
                'app_config': asdict(self._app_config)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_llm_configs(self) -> Dict[str, LLMConfig]:
        """Get all LLM configurations"""
        return self._llm_configs.copy()
    
    def get_llm_config(self, name: str) -> Optional[LLMConfig]:
        """Get specific LLM configuration"""
        return self._llm_configs.get(name)
    
    def add_llm_config(self, name: str, config: LLMConfig):
        """Add or update LLM configuration"""
        self._llm_configs[name] = config
        self.save_config()
    
    def remove_llm_config(self, name: str) -> bool:
        """Remove LLM configuration"""
        if name in self._llm_configs:
            del self._llm_configs[name]
            self.save_config()
            return True
        return False
    
    def get_app_config(self) -> AppConfig:
        """Get application configuration"""
        return self._app_config
    
    def update_app_config(self, **kwargs):
        """Update application configuration"""
        for key, value in kwargs.items():
            if hasattr(self._app_config, key):
                setattr(self._app_config, key, value)
        self.save_config()
    
    def create_llm_instance(self, config: LLMConfig):
        """Create LLM instance from configuration"""
        try:
            if config.provider == LLMProvider.OPENAI:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model=config.model,
                    api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout=config.timeout,
                    **(config.extra_params or {})
                )
            
            elif config.provider == LLMProvider.ANTHROPIC:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=config.model,
                    api_key=config.api_key,
                    temperature=config.temperature,
                    max_tokens=config.max_tokens,
                    timeout=config.timeout,
                    **(config.extra_params or {})
                )
            
            elif config.provider == LLMProvider.OLLAMA:
                from langchain_ollama import ChatOllama
                return ChatOllama(
                    model=config.model,
                    base_url=config.base_url or "http://localhost:11434",
                    temperature=config.temperature,
                    **(config.extra_params or {})
                )
            
            else:
                raise ValueError(f"Unsupported LLM provider: {config.provider}")
                
        except ImportError as e:
            raise ImportError(f"Required package not installed for {config.provider}: {e}")
        except Exception as e:
            raise Exception(f"Error creating LLM instance: {e}")
    
    def test_llm_config(self, config: LLMConfig) -> bool:
        """Test LLM configuration by making a simple request"""
        try:
            llm = self.create_llm_instance(config)
            response = llm.invoke("Say 'Hello' if you can receive this message.")
            return "hello" in response.content.lower()
        except Exception as e:
            print(f"LLM test failed: {e}")
            return False
    
    def get_available_models(self, provider: LLMProvider) -> List[str]:
        """Get list of available models for a provider"""
        models = {
            LLMProvider.OPENAI: [
                "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", 
                "gpt-3.5-turbo", "gpt-3.5-turbo-16k"
            ],
            LLMProvider.ANTHROPIC: [
                "claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307", "claude-3-opus-20240229"
            ],
            LLMProvider.OLLAMA: [
                "llama3.2", "llama3.1", "llama3", "llama2", "codellama",
                "mistral", "mixtral", "phi3", "qwen2", "gemma2"
            ],
            LLMProvider.GOOGLE: [
                "gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"
            ],
            LLMProvider.FIREWORKS: [
                "accounts/fireworks/models/llama-v3p1-70b-instruct",
                "accounts/fireworks/models/llama-v3p1-8b-instruct"
            ]
        }
        
        return models.get(provider, [])