"""
Experiment tracking system for Browser.AI MLOps

This module provides comprehensive experiment tracking capabilities including:
- Experiment configuration logging
- Model parameter tracking
- Performance metrics recording
- Artifact storage
- Experiment comparison tools
"""

import json
import logging
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class ExperimentConfig(BaseModel):
	"""Configuration for an experiment"""
	experiment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
	experiment_name: str
	description: Optional[str] = None
	tags: List[str] = Field(default_factory=list)
	created_at: datetime = Field(default_factory=datetime.now)
	
	# LLM Configuration
	llm_provider: str
	llm_model: str
	temperature: float = 0.1
	max_tokens: Optional[int] = None
	
	# Agent Configuration  
	use_vision: bool = True
	max_steps: int = 100
	max_failures: int = 3
	
	# Browser Configuration
	headless: bool = True
	disable_security: bool = True
	timeout: int = 30
	
	# Custom parameters
	custom_params: Dict[str, Any] = Field(default_factory=dict)


class ExperimentResult(BaseModel):
	"""Results of an experiment"""
	experiment_id: str
	run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
	started_at: datetime = Field(default_factory=datetime.now)
	completed_at: Optional[datetime] = None
	status: str = "running"  # running, completed, failed
	
	# Performance metrics
	task_success_rate: Optional[float] = None
	average_completion_time: Optional[float] = None
	total_steps: Optional[int] = None
	error_count: Optional[int] = None
	
	# Detailed metrics
	step_success_rates: List[float] = Field(default_factory=list)
	action_types_used: Dict[str, int] = Field(default_factory=dict)
	failure_reasons: List[str] = Field(default_factory=list)
	
	# Artifacts
	conversation_log: List[Dict[str, Any]] = Field(default_factory=list)
	screenshots: List[str] = Field(default_factory=list)
	dom_snapshots: List[Dict[str, Any]] = Field(default_factory=list)
	
	# Custom metrics
	custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class ExperimentTracker:
	"""Main experiment tracking class"""
	
	def __init__(self, storage_dir: Union[str, Path] = "experiments"):
		self.storage_dir = Path(storage_dir)
		self.storage_dir.mkdir(exist_ok=True)
		self.logger = logging.getLogger(__name__)
		
		# Current experiment tracking
		self.current_experiment: Optional[ExperimentConfig] = None
		self.current_run: Optional[ExperimentResult] = None
		
	def create_experiment(
		self,
		name: str,
		description: Optional[str] = None,
		tags: Optional[List[str]] = None,
		**config_params
	) -> str:
		"""Create a new experiment"""
		config = ExperimentConfig(
			experiment_name=name,
			description=description,
			tags=tags or [],
			**config_params
		)
		
		self.current_experiment = config
		
		# Save experiment config
		experiment_dir = self.storage_dir / config.experiment_id
		experiment_dir.mkdir(exist_ok=True)
		
		config_file = experiment_dir / "config.json"
		with open(config_file, 'w') as f:
			json.dump(config.model_dump(), f, indent=2, default=str)
			
		self.logger.info(f"Created experiment: {config.experiment_id} - {name}")
		return config.experiment_id
		
	def start_run(self, experiment_id: Optional[str] = None) -> str:
		"""Start a new experiment run"""
		if experiment_id:
			# Load existing experiment
			self.load_experiment(experiment_id)
		
		if not self.current_experiment:
			raise ValueError("No active experiment. Create or load an experiment first.")
			
		self.current_run = ExperimentResult(
			experiment_id=self.current_experiment.experiment_id
		)
		
		self.logger.info(f"Started run: {self.current_run.run_id}")
		return self.current_run.run_id
		
	def log_metric(self, key: str, value: Any, step: Optional[int] = None):
		"""Log a metric for the current run"""
		if not self.current_run:
			raise ValueError("No active run. Start a run first.")
			
		if key not in self.current_run.custom_metrics:
			self.current_run.custom_metrics[key] = []
			
		metric_entry = {
			"value": value,
			"timestamp": datetime.now().isoformat(),
		}
		if step is not None:
			metric_entry["step"] = step
			
		self.current_run.custom_metrics[key].append(metric_entry)
		
	def log_conversation(self, role: str, content: str, metadata: Optional[Dict] = None):
		"""Log conversation message"""
		if not self.current_run:
			raise ValueError("No active run. Start a run first.")
			
		message = {
			"role": role,
			"content": content,
			"timestamp": datetime.now().isoformat(),
			"metadata": metadata or {}
		}
		self.current_run.conversation_log.append(message)
		
	def log_action(self, action_type: str, success: bool, details: Optional[Dict] = None):
		"""Log browser action"""
		if not self.current_run:
			raise ValueError("No active run. Start a run first.")
			
		# Update action counts
		if action_type not in self.current_run.action_types_used:
			self.current_run.action_types_used[action_type] = 0
		self.current_run.action_types_used[action_type] += 1
		
		# Log detailed action info
		action_log = {
			"action_type": action_type,
			"success": success,
			"timestamp": datetime.now().isoformat(),
			"details": details or {}
		}
		
		if "actions" not in self.current_run.custom_metrics:
			self.current_run.custom_metrics["actions"] = []
		self.current_run.custom_metrics["actions"].append(action_log)
		
	def log_screenshot(self, screenshot_path: str):
		"""Log screenshot artifact"""
		if not self.current_run:
			raise ValueError("No active run. Start a run first.")
			
		self.current_run.screenshots.append(screenshot_path)
		
	def log_dom_snapshot(self, dom_data: Dict[str, Any]):
		"""Log DOM snapshot"""
		if not self.current_run:
			raise ValueError("No active run. Start a run first.")
			
		snapshot = {
			"timestamp": datetime.now().isoformat(),
			"data": dom_data
		}
		self.current_run.dom_snapshots.append(snapshot)
		
	def complete_run(self, success: bool = True, error_message: Optional[str] = None):
		"""Complete the current run"""
		if not self.current_run:
			raise ValueError("No active run to complete.")
			
		self.current_run.completed_at = datetime.now()
		self.current_run.status = "completed" if success else "failed"
		
		if error_message:
			self.current_run.failure_reasons.append(error_message)
			
		# Calculate summary metrics
		self._calculate_summary_metrics()
		
		# Save run results
		self._save_run_results()
		
		self.logger.info(f"Completed run: {self.current_run.run_id} - Status: {self.current_run.status}")
		
	def _calculate_summary_metrics(self):
		"""Calculate summary metrics from detailed logs"""
		if not self.current_run:
			return
			
		# Calculate task success rate
		actions = self.current_run.custom_metrics.get("actions", [])
		if actions:
			successful_actions = sum(1 for a in actions if a.get("success", False))
			self.current_run.task_success_rate = successful_actions / len(actions)
			
		# Calculate completion time
		if self.current_run.completed_at and self.current_run.started_at:
			duration = (self.current_run.completed_at - self.current_run.started_at).total_seconds()
			self.current_run.average_completion_time = duration
			
		# Count total steps
		self.current_run.total_steps = len(actions)
		
		# Count errors
		self.current_run.error_count = len(self.current_run.failure_reasons)
		
	def _save_run_results(self):
		"""Save run results to disk"""
		if not self.current_experiment or not self.current_run:
			return
			
		experiment_dir = self.storage_dir / self.current_experiment.experiment_id
		runs_dir = experiment_dir / "runs"
		runs_dir.mkdir(exist_ok=True)
		
		run_file = runs_dir / f"{self.current_run.run_id}.json"
		with open(run_file, 'w') as f:
			json.dump(self.current_run.model_dump(), f, indent=2, default=str)
			
	def load_experiment(self, experiment_id: str):
		"""Load an existing experiment"""
		experiment_dir = self.storage_dir / experiment_id
		config_file = experiment_dir / "config.json"
		
		if not config_file.exists():
			raise ValueError(f"Experiment {experiment_id} not found")
			
		with open(config_file, 'r') as f:
			config_data = json.load(f)
			
		self.current_experiment = ExperimentConfig(**config_data)
		self.logger.info(f"Loaded experiment: {experiment_id}")
		
	def list_experiments(self) -> List[Dict[str, Any]]:
		"""List all experiments"""
		experiments = []
		
		for experiment_dir in self.storage_dir.iterdir():
			if experiment_dir.is_dir():
				config_file = experiment_dir / "config.json"
				if config_file.exists():
					with open(config_file, 'r') as f:
						config = json.load(f)
					experiments.append(config)
					
		return sorted(experiments, key=lambda x: x['created_at'], reverse=True)
		
	def get_experiment_results(self, experiment_id: str) -> List[Dict[str, Any]]:
		"""Get all runs for an experiment"""
		experiment_dir = self.storage_dir / experiment_id
		runs_dir = experiment_dir / "runs"
		
		if not runs_dir.exists():
			return []
			
		results = []
		for run_file in runs_dir.glob("*.json"):
			with open(run_file, 'r') as f:
				result = json.load(f)
			results.append(result)
			
		return sorted(results, key=lambda x: x['started_at'], reverse=True)
		
	def compare_experiments(self, experiment_ids: List[str]) -> Dict[str, Any]:
		"""Compare multiple experiments"""
		comparison = {
			"experiments": [],
			"summary": {
				"total_runs": 0,
				"average_success_rate": 0,
				"average_completion_time": 0
			}
		}
		
		total_success_rate = 0
		total_completion_time = 0
		total_experiments = 0
		
		for exp_id in experiment_ids:
			results = self.get_experiment_results(exp_id)
			if not results:
				continue
				
			# Calculate experiment averages
			success_rates = [r.get('task_success_rate', 0) for r in results if r.get('task_success_rate') is not None]
			completion_times = [r.get('average_completion_time', 0) for r in results if r.get('average_completion_time') is not None]
			
			exp_summary = {
				"experiment_id": exp_id,
				"total_runs": len(results),
				"avg_success_rate": sum(success_rates) / len(success_rates) if success_rates else 0,
				"avg_completion_time": sum(completion_times) / len(completion_times) if completion_times else 0,
				"completed_runs": len([r for r in results if r.get('status') == 'completed'])
			}
			
			comparison["experiments"].append(exp_summary)
			
			if success_rates:
				total_success_rate += exp_summary["avg_success_rate"]
				total_completion_time += exp_summary["avg_completion_time"]
				total_experiments += 1
			comparison["summary"]["total_runs"] += len(results)
			
		if total_experiments > 0:
			comparison["summary"]["average_success_rate"] = total_success_rate / total_experiments
			comparison["summary"]["average_completion_time"] = total_completion_time / total_experiments
			
		return comparison