"""
Model Registry for Browser.AI MLOps

This module provides model management and versioning capabilities including:
- LLM model configuration storage
- Model version tracking
- Model performance comparison
- Model deployment management
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ModelMetadata(BaseModel):
	"""Metadata for a registered model"""
	model_id: str
	name: str
	version: str
	description: Optional[str] = None
	tags: List[str] = Field(default_factory=list)
	created_at: datetime = Field(default_factory=datetime.now)
	created_by: Optional[str] = None
	
	# Model configuration
	llm_provider: str  # openai, anthropic, google, ollama
	llm_model: str     # gpt-4, claude-3, gemini-pro, etc.
	temperature: float = 0.1
	max_tokens: Optional[int] = None
	system_prompt: Optional[str] = None
	
	# Performance metrics (populated after evaluation)
	success_rate: Optional[float] = None
	avg_completion_time: Optional[float] = None
	cost_per_task: Optional[float] = None
	total_evaluations: int = 0
	
	# Deployment information
	status: str = "registered"  # registered, staging, production, archived
	deployment_target: Optional[str] = None
	last_deployed: Optional[datetime] = None
	
	# Custom metadata
	custom_fields: Dict[str, Any] = Field(default_factory=dict)


class ModelVersion(BaseModel):
	"""Specific version of a model"""
	version_id: str
	model_id: str
	version: str
	parent_version: Optional[str] = None
	changelog: Optional[str] = None
	created_at: datetime = Field(default_factory=datetime.now)
	
	# Configuration diff from parent
	config_changes: Dict[str, Any] = Field(default_factory=dict)
	
	# Performance comparison with parent
	performance_delta: Dict[str, float] = Field(default_factory=dict)


class ModelRegistry:
	"""Central registry for managing LLM models and configurations"""
	
	def __init__(self, registry_dir: Union[str, Path] = "model_registry"):
		self.registry_dir = Path(registry_dir)
		self.registry_dir.mkdir(exist_ok=True)
		
		# Create subdirectories
		(self.registry_dir / "models").mkdir(exist_ok=True)
		(self.registry_dir / "versions").mkdir(exist_ok=True)
		(self.registry_dir / "artifacts").mkdir(exist_ok=True)
		
		self.logger = logging.getLogger(__name__)
		
	def register_model(
		self,
		name: str,
		llm_provider: str,
		llm_model: str,
		version: str = "1.0.0",
		description: Optional[str] = None,
		tags: Optional[List[str]] = None,
		**config_params
	) -> str:
		"""Register a new model configuration"""
		
		# Generate model ID
		model_id = f"{name}_{version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		
		metadata = ModelMetadata(
			model_id=model_id,
			name=name,
			version=version,
			description=description,
			tags=tags or [],
			llm_provider=llm_provider,
			llm_model=llm_model,
			**config_params
		)
		
		# Save model metadata
		model_file = self.registry_dir / "models" / f"{model_id}.json"
		with open(model_file, 'w') as f:
			json.dump(metadata.model_dump(), f, indent=2, default=str)
			
		self.logger.info(f"Registered model: {model_id} - {name} v{version}")
		return model_id
		
	def create_model_version(
		self,
		model_id: str,
		new_version: str,
		changelog: Optional[str] = None,
		**config_changes
	) -> str:
		"""Create a new version of an existing model"""
		
		# Load parent model
		parent_model = self.get_model(model_id)
		if not parent_model:
			raise ValueError(f"Model {model_id} not found")
			
		# Create new model with updated configuration
		new_model_data = parent_model.copy()
		new_model_data.update(config_changes)
		new_model_data["version"] = new_version
		new_model_data["created_at"] = datetime.now()
		
		# Generate new model ID
		new_model_id = f"{parent_model['name']}_{new_version}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		new_model_data["model_id"] = new_model_id
		
		# Save new model
		new_metadata = ModelMetadata(**new_model_data)
		model_file = self.registry_dir / "models" / f"{new_model_id}.json"
		with open(model_file, 'w') as f:
			json.dump(new_metadata.model_dump(), f, indent=2, default=str)
			
		# Create version tracking record
		version = ModelVersion(
			version_id=f"{new_model_id}_version",
			model_id=new_model_id,
			version=new_version,
			parent_version=parent_model["version"],
			changelog=changelog,
			config_changes=config_changes
		)
		
		version_file = self.registry_dir / "versions" / f"{version.version_id}.json"
		with open(version_file, 'w') as f:
			json.dump(version.model_dump(), f, indent=2, default=str)
			
		self.logger.info(f"Created model version: {new_model_id} v{new_version}")
		return new_model_id
		
	def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
		"""Get model metadata by ID"""
		model_file = self.registry_dir / "models" / f"{model_id}.json"
		
		if not model_file.exists():
			return None
			
		with open(model_file, 'r') as f:
			return json.load(f)
			
	def list_models(
		self, 
		status: Optional[str] = None,
		provider: Optional[str] = None,
		tags: Optional[List[str]] = None
	) -> List[Dict[str, Any]]:
		"""List all registered models with optional filters"""
		models = []
		
		for model_file in (self.registry_dir / "models").glob("*.json"):
			with open(model_file, 'r') as f:
				model_data = json.load(f)
				
			# Apply filters
			if status and model_data.get("status") != status:
				continue
			if provider and model_data.get("llm_provider") != provider:
				continue
			if tags and not any(tag in model_data.get("tags", []) for tag in tags):
				continue
				
			models.append(model_data)
			
		return sorted(models, key=lambda x: x["created_at"], reverse=True)
		
	def update_model_performance(
		self,
		model_id: str,
		success_rate: Optional[float] = None,
		avg_completion_time: Optional[float] = None,
		cost_per_task: Optional[float] = None,
		increment_evaluations: bool = True
	):
		"""Update model performance metrics"""
		model_data = self.get_model(model_id)
		if not model_data:
			raise ValueError(f"Model {model_id} not found")
			
		# Update performance metrics
		if success_rate is not None:
			model_data["success_rate"] = success_rate
		if avg_completion_time is not None:
			model_data["avg_completion_time"] = avg_completion_time
		if cost_per_task is not None:
			model_data["cost_per_task"] = cost_per_task
		if increment_evaluations:
			model_data["total_evaluations"] = model_data.get("total_evaluations", 0) + 1
			
		# Save updated model
		model_file = self.registry_dir / "models" / f"{model_id}.json"
		with open(model_file, 'w') as f:
			json.dump(model_data, f, indent=2, default=str)
			
		self.logger.info(f"Updated performance metrics for model: {model_id}")
		
	def deploy_model(
		self,
		model_id: str,
		target: str,
		status: str = "production"
	):
		"""Deploy a model to a specific target"""
		model_data = self.get_model(model_id)
		if not model_data:
			raise ValueError(f"Model {model_id} not found")
			
		# Update deployment information
		model_data["status"] = status
		model_data["deployment_target"] = target
		model_data["last_deployed"] = datetime.now().isoformat()
		
		# Save updated model
		model_file = self.registry_dir / "models" / f"{model_id}.json"
		with open(model_file, 'w') as f:
			json.dump(model_data, f, indent=2, default=str)
			
		self.logger.info(f"Deployed model {model_id} to {target} with status {status}")
		
	def archive_model(self, model_id: str):
		"""Archive a model"""
		self.deploy_model(model_id, target=None, status="archived")
		
	def compare_models(self, model_ids: List[str]) -> Dict[str, Any]:
		"""Compare multiple models"""
		comparison = {
			"models": [],
			"summary": {
				"best_success_rate": {"model_id": None, "value": 0},
				"fastest_completion": {"model_id": None, "value": float('inf')},
				"lowest_cost": {"model_id": None, "value": float('inf')}
			}
		}
		
		for model_id in model_ids:
			model_data = self.get_model(model_id)
			if not model_data:
				continue
				
			model_summary = {
				"model_id": model_id,
				"name": model_data.get("name"),
				"version": model_data.get("version"),
				"provider": model_data.get("llm_provider"),
				"model": model_data.get("llm_model"),
				"success_rate": model_data.get("success_rate"),
				"avg_completion_time": model_data.get("avg_completion_time"),
				"cost_per_task": model_data.get("cost_per_task"),
				"total_evaluations": model_data.get("total_evaluations", 0)
			}
			
			comparison["models"].append(model_summary)
			
			# Update best metrics
			if model_summary["success_rate"] and model_summary["success_rate"] > comparison["summary"]["best_success_rate"]["value"]:
				comparison["summary"]["best_success_rate"] = {"model_id": model_id, "value": model_summary["success_rate"]}
				
			if model_summary["avg_completion_time"] and model_summary["avg_completion_time"] < comparison["summary"]["fastest_completion"]["value"]:
				comparison["summary"]["fastest_completion"] = {"model_id": model_id, "value": model_summary["avg_completion_time"]}
				
			if model_summary["cost_per_task"] and model_summary["cost_per_task"] < comparison["summary"]["lowest_cost"]["value"]:
				comparison["summary"]["lowest_cost"] = {"model_id": model_id, "value": model_summary["cost_per_task"]}
				
		return comparison
		
	def get_model_history(self, model_name: str) -> List[Dict[str, Any]]:
		"""Get version history for a model name"""
		versions = []
		
		# Get all models with the same name
		all_models = self.list_models()
		model_versions = [m for m in all_models if m.get("name") == model_name]
		
		# Get version tracking records
		for version_file in (self.registry_dir / "versions").glob("*.json"):
			with open(version_file, 'r') as f:
				version_data = json.load(f)
			versions.append(version_data)
			
		return sorted(versions, key=lambda x: x["created_at"], reverse=True)
		
	def export_model_config(self, model_id: str, export_path: str):
		"""Export model configuration for deployment"""
		model_data = self.get_model(model_id)
		if not model_data:
			raise ValueError(f"Model {model_id} not found")
			
		# Create deployment configuration
		deployment_config = {
			"model_metadata": model_data,
			"deployment_config": {
				"llm_provider": model_data["llm_provider"],
				"llm_model": model_data["llm_model"],
				"temperature": model_data["temperature"],
				"max_tokens": model_data.get("max_tokens"),
				"system_prompt": model_data.get("system_prompt")
			},
			"exported_at": datetime.now().isoformat(),
			"exported_by": "model_registry"
		}
		
		export_file = Path(export_path)
		export_file.parent.mkdir(parents=True, exist_ok=True)
		
		with open(export_file, 'w') as f:
			json.dump(deployment_config, f, indent=2, default=str)
			
		self.logger.info(f"Exported model {model_id} to {export_path}")
		
	def import_model_config(self, import_path: str) -> str:
		"""Import model configuration from file"""
		with open(import_path, 'r') as f:
			config_data = json.load(f)
			
		model_metadata = config_data["model_metadata"]
		
		# Generate new model ID to avoid conflicts
		original_name = model_metadata["name"]
		model_id = f"{original_name}_imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
		model_metadata["model_id"] = model_id
		model_metadata["created_at"] = datetime.now().isoformat()
		
		# Save imported model
		model_file = self.registry_dir / "models" / f"{model_id}.json"
		with open(model_file, 'w') as f:
			json.dump(model_metadata, f, indent=2, default=str)
			
		self.logger.info(f"Imported model as {model_id}")
		return model_id
		
	def cleanup_old_models(self, keep_versions: int = 5):
		"""Cleanup old model versions, keeping only the most recent ones"""
		models_by_name = {}
		
		# Group models by name
		for model in self.list_models():
			name = model["name"]
			if name not in models_by_name:
				models_by_name[name] = []
			models_by_name[name].append(model)
			
		# Sort by creation date and keep only recent versions
		for name, models in models_by_name.items():
			sorted_models = sorted(models, key=lambda x: x["created_at"], reverse=True)
			
			# Archive older versions
			for model in sorted_models[keep_versions:]:
				if model["status"] not in ["production", "staging"]:
					self.archive_model(model["model_id"])
					self.logger.info(f"Archived old model version: {model['model_id']}")
					
	def get_registry_stats(self) -> Dict[str, Any]:
		"""Get registry statistics"""
		all_models = self.list_models()
		
		stats = {
			"total_models": len(all_models),
			"by_status": {},
			"by_provider": {},
			"by_performance": {
				"evaluated_models": 0,
				"avg_success_rate": 0,
				"avg_completion_time": 0
			},
			"recent_activity": {
				"models_created_last_7_days": 0,
				"models_deployed_last_7_days": 0
			}
		}
		
		# Count by status and provider
		evaluated_models = []
		for model in all_models:
			status = model.get("status", "unknown")
			provider = model.get("llm_provider", "unknown")
			
			stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
			stats["by_provider"][provider] = stats["by_provider"].get(provider, 0) + 1
			
			if model.get("success_rate") is not None:
				evaluated_models.append(model)
				
		# Calculate performance averages
		if evaluated_models:
			stats["by_performance"]["evaluated_models"] = len(evaluated_models)
			stats["by_performance"]["avg_success_rate"] = sum(m["success_rate"] for m in evaluated_models) / len(evaluated_models)
			
			completion_times = [m["avg_completion_time"] for m in evaluated_models if m.get("avg_completion_time")]
			if completion_times:
				stats["by_performance"]["avg_completion_time"] = sum(completion_times) / len(completion_times)
				
		return stats