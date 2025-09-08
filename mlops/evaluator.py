"""
Model evaluator for Browser.AI MLOps

This module provides comprehensive model evaluation capabilities including:
- Automated model testing
- Performance benchmarking
- A/B testing framework
- Model validation
- Evaluation metrics calculation
"""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field


class EvaluationTask(BaseModel):
	"""Definition of an evaluation task"""
	task_id: str
	name: str
	description: str
	task_prompt: str
	expected_actions: List[Dict[str, Any]] = Field(default_factory=list)
	success_criteria: Dict[str, Any] = Field(default_factory=dict)
	timeout_seconds: int = 300
	tags: List[str] = Field(default_factory=list)
	difficulty: str = "medium"  # easy, medium, hard
	category: str = "general"


class EvaluationResult(BaseModel):
	"""Result of a model evaluation"""
	evaluation_id: str
	task_id: str
	model_id: str
	run_id: str
	timestamp: datetime = Field(default_factory=datetime.now)
	
	# Execution metrics
	success: bool
	completion_time_seconds: float
	steps_taken: int
	actions_performed: int
	
	# Quality metrics
	task_completion_score: float = 0.0  # 0-1 scale
	efficiency_score: float = 0.0       # 0-1 scale
	accuracy_score: float = 0.0         # 0-1 scale
	overall_score: float = 0.0          # 0-1 scale
	
	# Detailed results
	actions_trace: List[Dict[str, Any]] = Field(default_factory=list)
	error_messages: List[str] = Field(default_factory=list)
	warnings: List[str] = Field(default_factory=list)
	
	# LLM metrics
	llm_calls_made: int = 0
	total_tokens_used: int = 0
	estimated_cost: Optional[float] = None
	
	# Custom evaluation criteria
	custom_scores: Dict[str, float] = Field(default_factory=dict)
	evaluation_notes: Optional[str] = None


class BenchmarkSuite(BaseModel):
	"""Collection of evaluation tasks for benchmarking"""
	suite_id: str
	name: str
	description: str
	version: str = "1.0.0"
	created_at: datetime = Field(default_factory=datetime.now)
	tasks: List[EvaluationTask] = Field(default_factory=list)
	tags: List[str] = Field(default_factory=list)


class ModelEvaluator:
	"""Main model evaluation and benchmarking system"""
	
	def __init__(self, evaluation_dir: Union[str, Path] = "evaluations"):
		self.evaluation_dir = Path(evaluation_dir)
		self.evaluation_dir.mkdir(exist_ok=True)
		
		# Create subdirectories
		(self.evaluation_dir / "tasks").mkdir(exist_ok=True)
		(self.evaluation_dir / "results").mkdir(exist_ok=True)
		(self.evaluation_dir / "benchmarks").mkdir(exist_ok=True)
		
		self.logger = logging.getLogger(__name__)
		
		# Load default evaluation tasks
		self._load_default_tasks()
		
	def _load_default_tasks(self):
		"""Load default evaluation tasks"""
		default_tasks = [
			EvaluationTask(
				task_id="google_search",
				name="Google Search",
				description="Search for information on Google",
				task_prompt="Search for 'Python programming tutorial' on Google and find the first result",
				expected_actions=[
					{"type": "navigate", "url": "https://google.com"},
					{"type": "type", "text": "Python programming tutorial"},
					{"type": "click", "element": "search button"}
				],
				success_criteria={
					"must_visit_google": True,
					"must_perform_search": True,
					"min_steps": 3,
					"max_steps": 10
				},
				category="search",
				difficulty="easy"
			),
			EvaluationTask(
				task_id="form_filling",
				name="Form Filling",
				description="Fill out a contact form",
				task_prompt="Go to httpbin.org/forms/post and fill out the contact form with sample data",
				expected_actions=[
					{"type": "navigate", "url": "http://httpbin.org/forms/post"},
					{"type": "type", "field": "custname", "text": "John Doe"},
					{"type": "type", "field": "custtel", "text": "123-456-7890"},
					{"type": "type", "field": "custemail", "text": "john@example.com"},
					{"type": "click", "element": "submit"}
				],
				success_criteria={
					"must_fill_name": True,
					"must_fill_email": True,
					"must_submit_form": True,
					"max_steps": 15
				},
				category="forms",
				difficulty="medium"
			),
			EvaluationTask(
				task_id="navigation_test",
				name="Multi-page Navigation",
				description="Navigate through multiple pages",
				task_prompt="Visit example.com, then navigate to Wikipedia main page, then search for 'artificial intelligence'",
				expected_actions=[
					{"type": "navigate", "url": "http://example.com"},
					{"type": "navigate", "url": "https://wikipedia.org"},
					{"type": "type", "text": "artificial intelligence"},
					{"type": "click", "element": "search"}
				],
				success_criteria={
					"must_visit_example": True,
					"must_visit_wikipedia": True,
					"must_perform_search": True,
					"max_steps": 20
				},
				category="navigation",
				difficulty="hard"
			)
		]
		
		# Save default tasks
		for task in default_tasks:
			self.save_evaluation_task(task)
			
	def create_evaluation_task(
		self,
		name: str,
		description: str,
		task_prompt: str,
		expected_actions: Optional[List[Dict]] = None,
		success_criteria: Optional[Dict] = None,
		**kwargs
	) -> str:
		"""Create a new evaluation task"""
		task_id = f"{name.lower().replace(' ', '_')}_{int(time.time())}"
		
		task = EvaluationTask(
			task_id=task_id,
			name=name,
			description=description,
			task_prompt=task_prompt,
			expected_actions=expected_actions or [],
			success_criteria=success_criteria or {},
			**kwargs
		)
		
		self.save_evaluation_task(task)
		return task_id
		
	def save_evaluation_task(self, task: EvaluationTask):
		"""Save evaluation task to disk"""
		task_file = self.evaluation_dir / "tasks" / f"{task.task_id}.json"
		with open(task_file, 'w') as f:
			json.dump(task.model_dump(), f, indent=2, default=str)
			
	def load_evaluation_task(self, task_id: str) -> Optional[EvaluationTask]:
		"""Load evaluation task from disk"""
		task_file = self.evaluation_dir / "tasks" / f"{task_id}.json"
		if not task_file.exists():
			return None
			
		with open(task_file, 'r') as f:
			task_data = json.load(f)
			
		return EvaluationTask(**task_data)
		
	def list_evaluation_tasks(
		self, 
		category: Optional[str] = None,
		difficulty: Optional[str] = None,
		tags: Optional[List[str]] = None
	) -> List[EvaluationTask]:
		"""List available evaluation tasks with filters"""
		tasks = []
		
		for task_file in (self.evaluation_dir / "tasks").glob("*.json"):
			with open(task_file, 'r') as f:
				task_data = json.load(f)
			task = EvaluationTask(**task_data)
			
			# Apply filters
			if category and task.category != category:
				continue
			if difficulty and task.difficulty != difficulty:
				continue
			if tags and not any(tag in task.tags for tag in tags):
				continue
				
			tasks.append(task)
			
		return sorted(tasks, key=lambda x: x.name)
		
	def evaluate_model(
		self,
		model_id: str,
		task_id: str,
		agent_instance=None,
		custom_evaluator: Optional[callable] = None
	) -> EvaluationResult:
		"""Evaluate a model on a specific task"""
		
		# Load evaluation task
		task = self.load_evaluation_task(task_id)
		if not task:
			raise ValueError(f"Task {task_id} not found")
			
		# Create evaluation result
		result = EvaluationResult(
			evaluation_id=f"{model_id}_{task_id}_{int(time.time())}",
			task_id=task_id,
			model_id=model_id,
			run_id=f"eval_{int(time.time())}"
		)
		
		start_time = time.time()
		
		try:
			if agent_instance and hasattr(agent_instance, 'run'):
				# Use provided agent instance
				success, trace = self._run_agent_evaluation(agent_instance, task)
			elif custom_evaluator:
				# Use custom evaluator function
				success, trace = custom_evaluator(task)
			else:
				# Mock evaluation for demonstration
				success, trace = self._mock_evaluation(task)
				
			result.success = success
			result.completion_time_seconds = time.time() - start_time
			result.actions_trace = trace
			result.steps_taken = len(trace)
			result.actions_performed = len([a for a in trace if a.get('type') in ['click', 'type', 'navigate']])
			
			# Calculate scores
			self._calculate_evaluation_scores(result, task)
			
		except Exception as e:
			result.success = False
			result.completion_time_seconds = time.time() - start_time
			result.error_messages.append(str(e))
			self.logger.error(f"Evaluation failed: {e}")
			
		# Save result
		self._save_evaluation_result(result)
		
		return result
		
	def _run_agent_evaluation(self, agent, task: EvaluationTask) -> Tuple[bool, List[Dict]]:
		"""Run evaluation using actual Browser.AI agent"""
		try:
			# This would integrate with the actual Browser.AI agent
			# For now, return a mock implementation
			return self._mock_evaluation(task)
		except Exception as e:
			return False, [{"error": str(e)}]
			
	def _mock_evaluation(self, task: EvaluationTask) -> Tuple[bool, List[Dict]]:
		"""Mock evaluation for demonstration purposes"""
		import random
		
		# Simulate realistic evaluation results
		success_probability = {
			"easy": 0.85,
			"medium": 0.7,
			"hard": 0.55
		}.get(task.difficulty, 0.7)
		
		success = random.random() < success_probability
		
		# Generate mock action trace
		trace = []
		num_actions = random.randint(3, min(15, task.timeout_seconds // 10))
		
		for i in range(num_actions):
			action_type = random.choice(['navigate', 'click', 'type', 'scroll'])
			trace.append({
				"step": i + 1,
				"type": action_type,
				"success": random.random() > 0.1,
				"timestamp": time.time(),
				"details": f"Mock {action_type} action"
			})
			
		return success, trace
		
	def _calculate_evaluation_scores(self, result: EvaluationResult, task: EvaluationTask):
		"""Calculate evaluation scores based on results and criteria"""
		
		# Task completion score (0-1)
		if result.success:
			result.task_completion_score = 1.0
		else:
			# Partial credit based on steps completed vs expected
			expected_steps = len(task.expected_actions)
			if expected_steps > 0:
				result.task_completion_score = min(result.steps_taken / expected_steps, 0.8)
			else:
				result.task_completion_score = 0.3  # Some credit for attempting
				
		# Efficiency score (0-1) - based on completion time and steps
		max_steps = task.success_criteria.get("max_steps", 20)
		if result.steps_taken <= max_steps:
			step_efficiency = 1.0 - (result.steps_taken / max_steps) * 0.3
		else:
			step_efficiency = 0.7 - (result.steps_taken - max_steps) * 0.05
			
		time_efficiency = 1.0 if result.completion_time_seconds <= 60 else max(0.5, 1.0 - (result.completion_time_seconds - 60) / 240)
		result.efficiency_score = max(0, (step_efficiency + time_efficiency) / 2)
		
		# Accuracy score (0-1) - based on following expected actions
		successful_actions = len([a for a in result.actions_trace if a.get('success', False)])
		if result.actions_performed > 0:
			result.accuracy_score = successful_actions / result.actions_performed
		else:
			result.accuracy_score = 0
			
		# Overall score - weighted combination
		weights = {
			"completion": 0.5,
			"efficiency": 0.25,
			"accuracy": 0.25
		}
		
		result.overall_score = (
			result.task_completion_score * weights["completion"] +
			result.efficiency_score * weights["efficiency"] +
			result.accuracy_score * weights["accuracy"]
		)
		
	def _save_evaluation_result(self, result: EvaluationResult):
		"""Save evaluation result to disk"""
		result_file = self.evaluation_dir / "results" / f"{result.evaluation_id}.json"
		with open(result_file, 'w') as f:
			json.dump(result.model_dump(), f, indent=2, default=str)
			
	def run_benchmark_suite(
		self,
		model_id: str,
		suite_id: Optional[str] = None,
		task_filters: Optional[Dict] = None,
		agent_instance=None
	) -> Dict[str, Any]:
		"""Run a full benchmark suite against a model"""
		
		if suite_id:
			# Load specific benchmark suite
			tasks = self.load_benchmark_suite(suite_id).tasks
		else:
			# Use filtered task list
			tasks = self.list_evaluation_tasks(**(task_filters or {}))
			
		if not tasks:
			raise ValueError("No tasks found for evaluation")
			
		results = []
		start_time = time.time()
		
		for task in tasks:
			self.logger.info(f"Evaluating task: {task.name}")
			try:
				result = self.evaluate_model(model_id, task.task_id, agent_instance)
				results.append(result)
			except Exception as e:
				self.logger.error(f"Failed to evaluate task {task.name}: {e}")
				continue
				
		total_time = time.time() - start_time
		
		# Calculate benchmark summary
		successful_tasks = len([r for r in results if r.success])
		total_tasks = len(results)
		avg_score = sum(r.overall_score for r in results) / total_tasks if results else 0
		avg_completion_time = sum(r.completion_time_seconds for r in results) / total_tasks if results else 0
		
		# Category breakdown
		category_scores = {}
		for result in results:
			task = self.load_evaluation_task(result.task_id)
			if task:
				if task.category not in category_scores:
					category_scores[task.category] = []
				category_scores[task.category].append(result.overall_score)
				
		category_summary = {
			cat: sum(scores) / len(scores)
			for cat, scores in category_scores.items()
		}
		
		benchmark_result = {
			"model_id": model_id,
			"evaluation_timestamp": datetime.now().isoformat(),
			"total_time_seconds": total_time,
			"summary": {
				"total_tasks": total_tasks,
				"successful_tasks": successful_tasks,
				"success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
				"average_score": avg_score,
				"average_completion_time": avg_completion_time
			},
			"category_breakdown": category_summary,
			"detailed_results": [r.model_dump() for r in results]
		}
		
		# Save benchmark result
		benchmark_file = self.evaluation_dir / "results" / f"benchmark_{model_id}_{int(time.time())}.json"
		with open(benchmark_file, 'w') as f:
			json.dump(benchmark_result, f, indent=2, default=str)
			
		return benchmark_result
		
	def compare_models(self, model_ids: List[str], task_filters: Optional[Dict] = None) -> Dict[str, Any]:
		"""Compare multiple models on the same tasks"""
		
		# Get common tasks
		tasks = self.list_evaluation_tasks(**(task_filters or {}))
		if not tasks:
			raise ValueError("No tasks found for comparison")
			
		model_results = {}
		
		# Run evaluations for each model
		for model_id in model_ids:
			self.logger.info(f"Running comparison benchmark for model: {model_id}")
			benchmark_result = self.run_benchmark_suite(model_id, task_filters=task_filters)
			model_results[model_id] = benchmark_result
			
		# Create comparison analysis
		comparison = {
			"models_compared": model_ids,
			"comparison_timestamp": datetime.now().isoformat(),
			"tasks_evaluated": len(tasks),
			"model_rankings": {},
			"metric_comparison": {},
			"detailed_results": model_results
		}
		
		# Rank models by different metrics
		metrics = ["success_rate", "average_score", "average_completion_time"]
		for metric in metrics:
			model_scores = [
				(model_id, results["summary"][metric])
				for model_id, results in model_results.items()
			]
			
			# Sort by metric (lower is better for completion time)
			reverse_sort = metric != "average_completion_time"
			model_scores.sort(key=lambda x: x[1], reverse=reverse_sort)
			
			comparison["model_rankings"][metric] = [
				{"rank": i+1, "model_id": model_id, "value": value}
				for i, (model_id, value) in enumerate(model_scores)
			]
			
		return comparison
		
	def create_benchmark_suite(
		self,
		name: str,
		description: str,
		task_ids: List[str],
		version: str = "1.0.0"
	) -> str:
		"""Create a benchmark suite from existing tasks"""
		suite_id = f"{name.lower().replace(' ', '_')}_{version}"
		
		tasks = []
		for task_id in task_ids:
			task = self.load_evaluation_task(task_id)
			if task:
				tasks.append(task)
			else:
				self.logger.warning(f"Task {task_id} not found, skipping")
				
		suite = BenchmarkSuite(
			suite_id=suite_id,
			name=name,
			description=description,
			version=version,
			tasks=tasks
		)
		
		# Save benchmark suite
		suite_file = self.evaluation_dir / "benchmarks" / f"{suite_id}.json"
		with open(suite_file, 'w') as f:
			json.dump(suite.model_dump(), f, indent=2, default=str)
			
		self.logger.info(f"Created benchmark suite: {suite_id}")
		return suite_id
		
	def load_benchmark_suite(self, suite_id: str) -> Optional[BenchmarkSuite]:
		"""Load benchmark suite from disk"""
		suite_file = self.evaluation_dir / "benchmarks" / f"{suite_id}.json"
		if not suite_file.exists():
			return None
			
		with open(suite_file, 'r') as f:
			suite_data = json.load(f)
			
		return BenchmarkSuite(**suite_data)
		
	def get_model_performance_history(self, model_id: str) -> List[Dict[str, Any]]:
		"""Get historical performance data for a model"""
		results = []
		
		for result_file in (self.evaluation_dir / "results").glob("*.json"):
			with open(result_file, 'r') as f:
				result_data = json.load(f)
				
			# Check if this is a single evaluation result
			if result_data.get("model_id") == model_id and "task_id" in result_data:
				results.append(result_data)
			# Check if this is a benchmark result
			elif result_data.get("model_id") == model_id and "summary" in result_data:
				results.append({
					"timestamp": result_data["evaluation_timestamp"],
					"type": "benchmark",
					"summary": result_data["summary"]
				})
				
		return sorted(results, key=lambda x: x.get("timestamp", ""), reverse=True)