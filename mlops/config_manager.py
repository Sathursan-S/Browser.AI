"""
Configuration management for Browser.AI MLOps

This module provides environment-specific configuration management including:
- Multi-environment configuration (dev, staging, prod)
- Model configuration templates
- Deployment configurations
- Feature flags and A/B testing settings
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
	"""LLM provider configuration"""
	provider: str
	model: str
	temperature: float = 0.1
	max_tokens: Optional[int] = None
	api_key_env: str
	timeout: int = 30
	max_retries: int = 3


class AgentConfig(BaseModel):
	"""Agent behavior configuration"""
	use_vision: bool = True
	max_steps: int = 100
	max_failures: int = 3
	step_delay: float = 1.0
	screenshot_on_error: bool = True
	dom_snapshot_frequency: int = 5


class BrowserConfig(BaseModel):
	"""Browser configuration"""
	headless: bool = True
	disable_security: bool = True
	window_size: tuple = (1920, 1080)
	user_agent: Optional[str] = None
	proxy: Optional[str] = None
	timeout: int = 30


class MonitoringConfig(BaseModel):
	"""Monitoring and metrics configuration"""
	enable_metrics: bool = True
	metrics_retention_days: int = 30
	enable_tracing: bool = True
	log_level: str = "INFO"
	export_metrics_interval: int = 3600  # seconds
	alert_thresholds: Dict[str, float] = Field(default_factory=lambda: {
		"error_rate": 0.1,
		"avg_completion_time": 300,
		"success_rate_min": 0.8
	})


class ExperimentConfig(BaseModel):
	"""Experiment tracking configuration"""
	enable_experiment_tracking: bool = True
	auto_log_conversations: bool = True
	auto_log_screenshots: bool = False
	auto_log_dom_snapshots: bool = False
	experiment_retention_days: int = 90


class DeploymentConfig(BaseModel):
	"""Deployment configuration"""
	environment: str
	version: str
	replicas: int = 1
	resources: Dict[str, str] = Field(default_factory=lambda: {
		"cpu": "1000m",
		"memory": "2Gi"
	})
	autoscaling: Dict[str, Any] = Field(default_factory=lambda: {
		"enabled": False,
		"min_replicas": 1,
		"max_replicas": 5,
		"target_cpu": 70
	})


class MLOpsConfig(BaseModel):
	"""Main MLOps configuration"""
	environment: str = "development"
	version: str = "1.0.0"
	
	# Core configurations
	llm: LLMConfig
	agent: AgentConfig = Field(default_factory=AgentConfig)
	browser: BrowserConfig = Field(default_factory=BrowserConfig)
	
	# MLOps configurations
	monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
	experiments: ExperimentConfig = Field(default_factory=ExperimentConfig)
	deployment: DeploymentConfig
	
	# Feature flags
	feature_flags: Dict[str, bool] = Field(default_factory=dict)
	
	# A/B testing
	ab_tests: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ConfigManager:
	"""Manages MLOps configurations across environments"""
	
	def __init__(self, config_dir: str = "mlops/config"):
		self.config_dir = Path(config_dir)
		self.config_dir.mkdir(parents=True, exist_ok=True)
		self.current_config: Optional[MLOpsConfig] = None
		
		# Create default configurations if they don't exist
		self._create_default_configs()
		
	def _create_default_configs(self):
		"""Create default configuration files for different environments"""
		
		environments = {
			"development": {
				"environment": "development",
				"llm": {
					"provider": "openai",
					"model": "gpt-4o-mini",
					"temperature": 0.1,
					"api_key_env": "OPENAI_API_KEY"
				},
				"browser": {
					"headless": False,  # Show browser in development
					"disable_security": True
				},
				"monitoring": {
					"log_level": "DEBUG",
					"enable_metrics": True
				},
				"deployment": {
					"environment": "development",
					"version": "dev",
					"replicas": 1
				},
				"feature_flags": {
					"enable_advanced_dom_analysis": True,
					"enable_conversation_memory": True,
					"enable_cost_optimization": False
				}
			},
			"staging": {
				"environment": "staging",
				"llm": {
					"provider": "openai",
					"model": "gpt-4",
					"temperature": 0.05,
					"api_key_env": "OPENAI_API_KEY"
				},
				"browser": {
					"headless": True,
					"disable_security": False
				},
				"monitoring": {
					"log_level": "INFO",
					"enable_metrics": True
				},
				"deployment": {
					"environment": "staging", 
					"version": "staging",
					"replicas": 2
				},
				"feature_flags": {
					"enable_advanced_dom_analysis": True,
					"enable_conversation_memory": True,
					"enable_cost_optimization": True
				},
				"ab_tests": {
					"prompt_optimization": {
						"enabled": True,
						"variants": ["standard", "detailed", "concise"],
						"traffic_split": [0.4, 0.3, 0.3],
						"success_metric": "task_completion_rate"
					}
				}
			},
			"production": {
				"environment": "production",
				"llm": {
					"provider": "openai",
					"model": "gpt-4",
					"temperature": 0.0,
					"api_key_env": "OPENAI_API_KEY",
					"timeout": 60,
					"max_retries": 3
				},
				"agent": {
					"use_vision": True,
					"max_steps": 50,  # More conservative in production
					"max_failures": 2,
					"step_delay": 2.0,
					"screenshot_on_error": True
				},
				"browser": {
					"headless": True,
					"disable_security": False,
					"timeout": 45
				},
				"monitoring": {
					"log_level": "WARNING",
					"enable_metrics": True,
					"export_metrics_interval": 1800,
					"alert_thresholds": {
						"error_rate": 0.05,
						"avg_completion_time": 180,
						"success_rate_min": 0.9
					}
				},
				"deployment": {
					"environment": "production",
					"version": "1.0.0",
					"replicas": 3,
					"autoscaling": {
						"enabled": True,
						"min_replicas": 2,
						"max_replicas": 10,
						"target_cpu": 60
					}
				},
				"feature_flags": {
					"enable_advanced_dom_analysis": True,
					"enable_conversation_memory": True,
					"enable_cost_optimization": True
				}
			}
		}
		
		for env_name, config_data in environments.items():
			config_file = self.config_dir / f"{env_name}.yaml"
			if not config_file.exists():
				with open(config_file, 'w') as f:
					yaml.dump(config_data, f, default_flow_style=False, indent=2)
					
	def load_config(self, environment: str) -> MLOpsConfig:
		"""Load configuration for specified environment"""
		config_file = self.config_dir / f"{environment}.yaml"
		
		if not config_file.exists():
			raise ValueError(f"Configuration file for environment '{environment}' not found")
			
		with open(config_file, 'r') as f:
			config_data = yaml.safe_load(f)
			
		# Validate and create config object
		self.current_config = MLOpsConfig(**config_data)
		return self.current_config
		
	def save_config(self, config: MLOpsConfig, environment: Optional[str] = None):
		"""Save configuration to file"""
		env_name = environment or config.environment
		config_file = self.config_dir / f"{env_name}.yaml"
		
		with open(config_file, 'w') as f:
			yaml.dump(config.model_dump(), f, default_flow_style=False, indent=2)
			
	def get_current_config(self) -> Optional[MLOpsConfig]:
		"""Get currently loaded configuration"""
		return self.current_config
		
	def update_feature_flag(self, flag_name: str, enabled: bool, environment: str):
		"""Update a feature flag for a specific environment"""
		config = self.load_config(environment)
		config.feature_flags[flag_name] = enabled
		self.save_config(config, environment)
		
	def create_ab_test(
		self,
		test_name: str,
		variants: List[str],
		traffic_split: List[float],
		success_metric: str,
		environment: str = "staging"
	):
		"""Create a new A/B test configuration"""
		if abs(sum(traffic_split) - 1.0) > 0.001:
			raise ValueError("Traffic split must sum to 1.0")
			
		if len(variants) != len(traffic_split):
			raise ValueError("Number of variants must match traffic split")
			
		config = self.load_config(environment)
		config.ab_tests[test_name] = {
			"enabled": True,
			"variants": variants,
			"traffic_split": traffic_split,
			"success_metric": success_metric,
			"created_at": "2024-01-01T00:00:00"  # Would use datetime.now() in real implementation
		}
		
		self.save_config(config, environment)
		
	def get_ab_test_variant(self, test_name: str, user_id: str) -> Optional[str]:
		"""Get A/B test variant for a user"""
		if not self.current_config or test_name not in self.current_config.ab_tests:
			return None
			
		test_config = self.current_config.ab_tests[test_name]
		if not test_config.get("enabled", False):
			return None
			
		# Simple hash-based assignment (in production, use proper A/B testing framework)
		import hashlib
		user_hash = int(hashlib.md5(f"{test_name}_{user_id}".encode()).hexdigest(), 16)
		hash_ratio = (user_hash % 1000) / 1000.0
		
		variants = test_config["variants"]
		traffic_split = test_config["traffic_split"]
		
		cumulative = 0
		for i, split in enumerate(traffic_split):
			cumulative += split
			if hash_ratio <= cumulative:
				return variants[i]
				
		return variants[-1]  # Fallback
		
	def validate_config(self, config: MLOpsConfig) -> List[str]:
		"""Validate configuration and return list of warnings/errors"""
		warnings = []
		
		# Validate API key environment variables
		api_key_env = config.llm.api_key_env
		if not os.getenv(api_key_env):
			warnings.append(f"API key environment variable '{api_key_env}' is not set")
			
		# Validate resource limits for production
		if config.environment == "production":
			if config.deployment.replicas < 2:
				warnings.append("Production environment should have at least 2 replicas")
				
			if config.monitoring.log_level == "DEBUG":
				warnings.append("Production environment should not use DEBUG log level")
				
			if not config.browser.headless:
				warnings.append("Production environment should use headless browser")
				
		# Validate A/B test configurations
		for test_name, test_config in config.ab_tests.items():
			if test_config.get("enabled", False):
				traffic_split = test_config.get("traffic_split", [])
				if abs(sum(traffic_split) - 1.0) > 0.001:
					warnings.append(f"A/B test '{test_name}' traffic split does not sum to 1.0")
					
		return warnings
		
	def export_config_template(self, output_file: str):
		"""Export configuration template for documentation"""
		template = {
			"environment": "ENVIRONMENT_NAME",
			"version": "VERSION_STRING",
			"llm": {
				"provider": "openai|anthropic|google|ollama",
				"model": "MODEL_NAME",
				"temperature": 0.1,
				"max_tokens": "OPTIONAL_INT",
				"api_key_env": "ENVIRONMENT_VARIABLE_NAME",
				"timeout": 30,
				"max_retries": 3
			},
			"agent": {
				"use_vision": True,
				"max_steps": 100,
				"max_failures": 3,
				"step_delay": 1.0,
				"screenshot_on_error": True,
				"dom_snapshot_frequency": 5
			},
			"browser": {
				"headless": True,
				"disable_security": False,
				"window_size": [1920, 1080],
				"user_agent": "OPTIONAL_STRING",
				"proxy": "OPTIONAL_PROXY_URL",
				"timeout": 30
			},
			"monitoring": {
				"enable_metrics": True,
				"metrics_retention_days": 30,
				"enable_tracing": True,
				"log_level": "INFO|DEBUG|WARNING|ERROR",
				"export_metrics_interval": 3600,
				"alert_thresholds": {
					"error_rate": 0.1,
					"avg_completion_time": 300,
					"success_rate_min": 0.8
				}
			},
			"experiments": {
				"enable_experiment_tracking": True,
				"auto_log_conversations": True,
				"auto_log_screenshots": False,
				"auto_log_dom_snapshots": False,
				"experiment_retention_days": 90
			},
			"deployment": {
				"environment": "ENVIRONMENT_NAME",
				"version": "VERSION_STRING", 
				"replicas": 1,
				"resources": {
					"cpu": "1000m",
					"memory": "2Gi"
				},
				"autoscaling": {
					"enabled": False,
					"min_replicas": 1,
					"max_replicas": 5,
					"target_cpu": 70
				}
			},
			"feature_flags": {
				"enable_advanced_dom_analysis": True,
				"enable_conversation_memory": True,
				"enable_cost_optimization": False
			},
			"ab_tests": {
				"example_test": {
					"enabled": False,
					"variants": ["variant_a", "variant_b"],
					"traffic_split": [0.5, 0.5],
					"success_metric": "task_completion_rate"
				}
			}
		}
		
		with open(output_file, 'w') as f:
			yaml.dump(template, f, default_flow_style=False, indent=2)
			
	def list_environments(self) -> List[str]:
		"""List available environment configurations"""
		return [f.stem for f in self.config_dir.glob("*.yaml") if f.is_file()]
		
	def clone_environment(self, source_env: str, target_env: str):
		"""Clone configuration from one environment to another"""
		source_config = self.load_config(source_env)
		source_config.environment = target_env
		
		# Update deployment config
		source_config.deployment.environment = target_env
		source_config.deployment.version = f"{target_env}-v1.0.0"
		
		self.save_config(source_config, target_env)