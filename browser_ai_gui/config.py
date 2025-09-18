"""
Configuration Management for Browser.AI GUI

Handles LLM configuration, API keys, and other settings.
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
	raise ValueError('GEMINI_API_KEY is not set')


@dataclass
class LLMConfig:
	"""Configuration for Language Model"""

	provider: str = 'google'  # openai, anthropic, ollama, google, etc.
	model: str = 'gemini-2.5-flash-lite'
	api_key: str = SecretStr(api_key)
	base_url: Optional[str] = None  # For custom endpoints
	temperature: float = 0.1
	max_tokens: Optional[int] = None
	timeout: int = 30


@dataclass
class BrowserConfig:
	"""Configuration for browser settings"""

	headless: bool = False
	disable_security: bool = True
	extra_args: List[str] = None

	def __post_init__(self):
		if self.extra_args is None:
			self.extra_args = ['--disable-blink-features=AutomationControlled']


@dataclass
class AgentConfig:
	"""Configuration for agent behavior"""

	use_vision: bool = True
	max_failures: int = 3
	retry_delay: int = 10
	max_steps: int = 100
	generate_gif: bool = True
	validate_output: bool = False


@dataclass
class GUIConfig:
	"""Configuration for GUI appearance and behavior"""

	theme: str = 'dark'  # dark, light
	font_family: str = 'Consolas'
	font_size: int = 10
	max_log_entries: int = 1000
	auto_scroll: bool = True
	show_timestamps: bool = True
	animate_typing: bool = True
	typing_speed: int = 50  # characters per second


class ConfigManager:
	"""Manages configuration for Browser.AI GUI"""

	def __init__(self, config_dir: Optional[str] = None):
		if config_dir is None:
			config_dir = os.path.join(os.path.expanduser('~'), '.browser_ai_gui')

		self.config_dir = Path(config_dir)
		self.config_dir.mkdir(exist_ok=True)
		self.config_file = self.config_dir / 'config.json'

		# Initialize with defaults
		self.llm_config = LLMConfig()
		self.browser_config = BrowserConfig()
		self.agent_config = AgentConfig()
		self.gui_config = GUIConfig()

		# Load existing config
		self.load_config()

	def load_config(self) -> None:
		"""Load configuration from file"""
		if not self.config_file.exists():
			return

		try:
			with open(self.config_file, 'r') as f:
				config_data = json.load(f)

			# Update configurations
			if 'llm' in config_data:
				self.llm_config = LLMConfig(**config_data['llm'])
			if 'browser' in config_data:
				self.browser_config = BrowserConfig(**config_data['browser'])
			if 'agent' in config_data:
				self.agent_config = AgentConfig(**config_data['agent'])
			if 'gui' in config_data:
				self.gui_config = GUIConfig(**config_data['gui'])

		except Exception as e:
			print(f'Error loading config: {e}')

	def save_config(self) -> None:
		"""Save configuration to file"""
		config_data = {
			'llm': asdict(self.llm_config),
			'browser': asdict(self.browser_config),
			'agent': asdict(self.agent_config),
			'gui': asdict(self.gui_config),
		}

		try:
			with open(self.config_file, 'w') as f:
				json.dump(config_data, f, indent=2)
		except Exception as e:
			print(f'Error saving config: {e}')

	def get_llm_instance(self):
		"""Create LLM instance based on current configuration"""
		try:
			if self.llm_config.provider == 'openai':
				from langchain_openai import ChatOpenAI

				kwargs = {
					'model': self.llm_config.model,
					'temperature': self.llm_config.temperature,
					'timeout': self.llm_config.timeout,
				}

				if self.llm_config.api_key:
					kwargs['api_key'] = self.llm_config.api_key
				if self.llm_config.base_url:
					kwargs['base_url'] = self.llm_config.base_url
				if self.llm_config.max_tokens:
					kwargs['max_tokens'] = self.llm_config.max_tokens

				return ChatOpenAI(**kwargs)

			elif self.llm_config.provider == 'anthropic':
				from langchain_anthropic import ChatAnthropic

				kwargs = {
					'model': self.llm_config.model,
					'temperature': self.llm_config.temperature,
					'timeout': self.llm_config.timeout,
				}

				if self.llm_config.api_key:
					kwargs['api_key'] = self.llm_config.api_key
				if self.llm_config.max_tokens:
					kwargs['max_tokens'] = self.llm_config.max_tokens

				return ChatAnthropic(**kwargs)

			elif self.llm_config.provider == 'ollama':
				from langchain_ollama import ChatOllama

				kwargs = {
					'model': self.llm_config.model,
					'temperature': self.llm_config.temperature,
				}

				if self.llm_config.base_url:
					kwargs['base_url'] = self.llm_config.base_url

				return ChatOllama(**kwargs)

			elif self.llm_config.provider == 'google':
				from langchain_google_genai import ChatGoogleGenerativeAI

				kwargs = {
					'model': self.llm_config.model,
					'temperature': self.llm_config.temperature,
				}

				if self.llm_config.api_key:
					kwargs['google_api_key'] = self.llm_config.api_key
				if self.llm_config.max_tokens:
					kwargs['max_output_tokens'] = self.llm_config.max_tokens

				return ChatGoogleGenerativeAI(**kwargs)

			else:
				raise ValueError(f'Unsupported LLM provider: {self.llm_config.provider}')

		except ImportError as e:
			raise ImportError(f'Required package not installed for {self.llm_config.provider}: {e}')
		except Exception as e:
			raise Exception(f'Error creating LLM instance: {e}')

	def get_browser_config_dict(self) -> Dict[str, Any]:
		"""Get browser configuration as dictionary for Browser.AI"""
		return {
			'headless': self.browser_config.headless,
			'disable_security': self.browser_config.disable_security,
			'extra_chromium_args': self.browser_config.extra_args,
		}

	def update_llm_config(self, **kwargs) -> None:
		"""Update LLM configuration"""
		for key, value in kwargs.items():
			if hasattr(self.llm_config, key):
				setattr(self.llm_config, key, value)
		self.save_config()

	def update_browser_config(self, **kwargs) -> None:
		"""Update browser configuration"""
		for key, value in kwargs.items():
			if hasattr(self.browser_config, key):
				setattr(self.browser_config, key, value)
		self.save_config()

	def update_agent_config(self, **kwargs) -> None:
		"""Update agent configuration"""
		for key, value in kwargs.items():
			if hasattr(self.agent_config, key):
				setattr(self.agent_config, key, value)
		self.save_config()

	def update_gui_config(self, **kwargs) -> None:
		"""Update GUI configuration"""
		for key, value in kwargs.items():
			if hasattr(self.gui_config, key):
				setattr(self.gui_config, key, value)
		self.save_config()

	def get_supported_providers(self) -> List[str]:
		"""Get list of supported LLM providers"""
		return ['openai', 'anthropic', 'ollama', 'google']

	def get_default_models(self) -> Dict[str, List[str]]:
		"""Get default models for each provider"""
		return {
			'openai': ['gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
			'anthropic': ['claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
			'ollama': ['llama2', 'codellama', 'mistral', 'dolphin-mistral'],
			'google': ['gemini-2.5-flash-lite', 'gemini-pro', 'gemini-pro-vision'],
		}

	def validate_config(self) -> List[str]:
		"""Validate current configuration and return list of issues"""
		issues = []

		# Check API key for cloud providers
		if self.llm_config.provider in ['openai', 'anthropic', 'google']:
			if not self.llm_config.api_key:
				issues.append(f'API key required for {self.llm_config.provider}')

		# Check model availability
		default_models = self.get_default_models()
		if self.llm_config.provider in default_models:
			if self.llm_config.model not in default_models[self.llm_config.provider]:
				issues.append(f"Unknown model '{self.llm_config.model}' for {self.llm_config.provider}")

		# Check temperature range
		if not 0 <= self.llm_config.temperature <= 2:
			issues.append('Temperature should be between 0 and 2')

		return issues
