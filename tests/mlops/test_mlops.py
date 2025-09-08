"""
Tests for Browser.AI MLOps system

This module contains comprehensive tests for all MLOps components including:
- Experiment tracking
- Model registry
- Metrics collection
- Data management
- Configuration management
"""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mlops.config_manager import ConfigManager, MLOpsConfig
from mlops.data_manager import ConversationRecord, DataManager
from mlops.evaluator import EvaluationTask, ModelEvaluator
from mlops.experiment_tracker import ExperimentTracker
from mlops.metrics import MetricsCollector
from mlops.model_registry import ModelRegistry


@pytest.fixture
def temp_dir():
	"""Create a temporary directory for tests"""
	with tempfile.TemporaryDirectory() as tmpdir:
		yield tmpdir


@pytest.fixture
def config_manager(temp_dir):
	"""Create a ConfigManager instance for testing"""
	return ConfigManager(config_dir=str(Path(temp_dir) / "config"))


@pytest.fixture
def experiment_tracker(temp_dir):
	"""Create an ExperimentTracker instance for testing"""
	return ExperimentTracker(storage_dir=str(Path(temp_dir) / "experiments"))


@pytest.fixture
def model_registry(temp_dir):
	"""Create a ModelRegistry instance for testing"""
	return ModelRegistry(registry_dir=str(Path(temp_dir) / "registry"))


@pytest.fixture
def data_manager(temp_dir):
	"""Create a DataManager instance for testing"""
	return DataManager(data_dir=str(Path(temp_dir) / "data"))


@pytest.fixture
def metrics_collector():
	"""Create a MetricsCollector instance for testing"""
	return MetricsCollector(storage_dir="test_metrics")


@pytest.fixture
def model_evaluator(temp_dir):
	"""Create a ModelEvaluator instance for testing"""
	return ModelEvaluator(evaluation_dir=str(Path(temp_dir) / "evaluations"))


class TestConfigManager:
	"""Test configuration management functionality"""
	
	def test_create_default_configs(self, config_manager):
		"""Test that default configurations are created"""
		environments = config_manager.list_environments()
		assert "development" in environments
		assert "staging" in environments
		assert "production" in environments
		
	def test_load_config(self, config_manager):
		"""Test loading configuration for an environment"""
		config = config_manager.load_config("development")
		assert isinstance(config, MLOpsConfig)
		assert config.environment == "development"
		assert config.llm.provider == "openai"
		
	def test_feature_flag_management(self, config_manager):
		"""Test feature flag operations"""
		config_manager.update_feature_flag("test_flag", True, "development")
		config = config_manager.load_config("development")
		assert config.feature_flags.get("test_flag") is True
		
	def test_ab_test_creation(self, config_manager):
		"""Test A/B test configuration"""
		config_manager.create_ab_test(
			test_name="test_ab",
			variants=["control", "treatment"],
			traffic_split=[0.5, 0.5],
			success_metric="conversion_rate",
			environment="staging"
		)
		
		config = config_manager.load_config("staging")
		assert "test_ab" in config.ab_tests
		assert config.ab_tests["test_ab"]["enabled"] is True
		
	def test_config_validation(self, config_manager):
		"""Test configuration validation"""
		config = config_manager.load_config("production")
		warnings = config_manager.validate_config(config)
		
		# Should have warnings about missing API keys
		assert len(warnings) > 0
		assert any("API key" in warning for warning in warnings)


class TestExperimentTracker:
	"""Test experiment tracking functionality"""
	
	def test_create_experiment(self, experiment_tracker):
		"""Test experiment creation"""
		exp_id = experiment_tracker.create_experiment(
			name="Test Experiment",
			description="A test experiment",
			llm_provider="openai",
			llm_model="gpt-4"
		)
		
		assert exp_id is not None
		assert experiment_tracker.current_experiment is not None
		assert experiment_tracker.current_experiment.experiment_name == "Test Experiment"
		
	def test_run_management(self, experiment_tracker):
		"""Test experiment run management"""
		# Create experiment first
		exp_id = experiment_tracker.create_experiment(
			name="Test Run",
			llm_provider="openai",
			llm_model="gpt-4"
		)
		
		# Start run
		run_id = experiment_tracker.start_run()
		assert run_id is not None
		assert experiment_tracker.current_run is not None
		
		# Log some metrics
		experiment_tracker.log_metric("accuracy", 0.85)
		experiment_tracker.log_conversation("user", "Hello")
		experiment_tracker.log_action("click", True)
		
		# Complete run
		experiment_tracker.complete_run(success=True)
		assert experiment_tracker.current_run.status == "completed"
		
	def test_experiment_comparison(self, experiment_tracker):
		"""Test comparing multiple experiments"""
		# Create two experiments with runs
		exp1_id = experiment_tracker.create_experiment(
			name="Experiment 1",
			llm_provider="openai",
			llm_model="gpt-4"
		)
		
		run1_id = experiment_tracker.start_run()
		experiment_tracker.log_metric("success_rate", 0.8)
		experiment_tracker.complete_run(success=True)
		
		exp2_id = experiment_tracker.create_experiment(
			name="Experiment 2",
			llm_provider="anthropic",
			llm_model="claude-3"
		)
		
		run2_id = experiment_tracker.start_run()
		experiment_tracker.log_metric("success_rate", 0.9)
		experiment_tracker.complete_run(success=True)
		
		# Compare experiments
		comparison = experiment_tracker.compare_experiments([exp1_id, exp2_id])
		
		assert "experiments" in comparison
		assert "summary" in comparison
		assert len(comparison["experiments"]) == 2


class TestModelRegistry:
	"""Test model registry functionality"""
	
	def test_register_model(self, model_registry):
		"""Test model registration"""
		model_id = model_registry.register_model(
			name="TestModel",
			llm_provider="openai",
			llm_model="gpt-4",
			version="1.0.0",
			temperature=0.1
		)
		
		assert model_id is not None
		
		# Retrieve model
		model = model_registry.get_model(model_id)
		assert model is not None
		assert model["name"] == "TestModel"
		assert model["llm_provider"] == "openai"
		
	def test_model_versioning(self, model_registry):
		"""Test creating model versions"""
		# Register initial model
		model_id = model_registry.register_model(
			name="VersionedModel",
			llm_provider="openai",
			llm_model="gpt-4",
			version="1.0.0"
		)
		
		# Create new version
		new_model_id = model_registry.create_model_version(
			model_id=model_id,
			new_version="1.1.0",
			changelog="Improved prompts",
			temperature=0.05
		)
		
		assert new_model_id != model_id
		
		new_model = model_registry.get_model(new_model_id)
		assert new_model["version"] == "1.1.0"
		assert new_model["temperature"] == 0.05
		
	def test_model_deployment(self, model_registry):
		"""Test model deployment"""
		model_id = model_registry.register_model(
			name="DeployModel",
			llm_provider="openai",
			llm_model="gpt-4",
			version="1.0.0"
		)
		
		model_registry.deploy_model(model_id, target="production")
		
		model = model_registry.get_model(model_id)
		assert model["status"] == "production"
		assert model["deployment_target"] == "production"
		
	def test_model_comparison(self, model_registry):
		"""Test comparing multiple models"""
		# Register two models
		model1_id = model_registry.register_model(
			name="Model1",
			llm_provider="openai",
			llm_model="gpt-4",
			version="1.0.0"
		)
		
		model2_id = model_registry.register_model(
			name="Model2",
			llm_provider="anthropic",
			llm_model="claude-3",
			version="1.0.0"
		)
		
		# Update performance metrics
		model_registry.update_model_performance(model1_id, success_rate=0.85, avg_completion_time=120)
		model_registry.update_model_performance(model2_id, success_rate=0.90, avg_completion_time=100)
		
		# Compare models
		comparison = model_registry.compare_models([model1_id, model2_id])
		
		assert "models" in comparison
		assert "summary" in comparison
		assert comparison["summary"]["best_success_rate"]["model_id"] == model2_id
		assert comparison["summary"]["fastest_completion"]["model_id"] == model2_id


class TestDataManager:
	"""Test data management functionality"""
	
	def test_store_conversation(self, data_manager):
		"""Test storing conversation records"""
		conversation = ConversationRecord(
			conversation_id="test_conv_1",
			session_id="session_1",
			task_description="Test task",
			messages=[
				{"role": "user", "content": "Hello"},
				{"role": "assistant", "content": "Hi there"}
			],
			success=True,
			completion_time_seconds=45.0,
			steps_taken=5
		)
		
		filepath = data_manager.store_conversation(conversation)
		assert filepath is not None
		assert Path(filepath).exists()
		
		# Retrieve conversation
		retrieved = data_manager.get_conversation("test_conv_1")
		assert retrieved is not None
		assert retrieved.conversation_id == "test_conv_1"
		assert retrieved.success is True
		
	def test_data_versioning(self, data_manager):
		"""Test data version creation"""
		# Store some conversations first
		for i in range(5):
			conversation = ConversationRecord(
				conversation_id=f"conv_{i}",
				session_id="session_1",
				task_description=f"Task {i}",
				success=i % 2 == 0,  # Alternate success/failure
				quality_score=0.8 + i * 0.05
			)
			data_manager.store_conversation(conversation)
			
		# Create data version
		version_id = data_manager.create_data_version(
			version_name="test_version",
			created_by="test_user",
			description="Test data version"
		)
		
		assert version_id is not None
		
		# Load version
		version = data_manager.load_data_version(version_id)
		assert version is not None
		assert version.version_name == "test_version"
		assert version.total_conversations == 5
		
	def test_data_export(self, data_manager, temp_dir):
		"""Test data export functionality"""
		# Store conversation
		conversation = ConversationRecord(
			conversation_id="export_test",
			session_id="session_1",
			task_description="Export test task",
			messages=[{"role": "user", "content": "Test"}],
			success=True
		)
		data_manager.store_conversation(conversation)
		
		# Create version
		version_id = data_manager.create_data_version(
			version_name="export_version",
			created_by="test_user"
		)
		
		# Export data
		output_dir = Path(temp_dir) / "export"
		data_manager.export_training_data(version_id, str(output_dir), format="json")
		
		# Check exported file exists
		export_file = output_dir / f"{version_id}_training_data.json"
		assert export_file.exists()
		
		with open(export_file) as f:
			data = json.load(f)
		assert "conversations" in data
		assert len(data["conversations"]) == 1
		
	def test_data_drift_detection(self, data_manager):
		"""Test data drift detection"""
		# Create baseline version with good performance
		for i in range(10):
			conversation = ConversationRecord(
				conversation_id=f"baseline_{i}",
				session_id="session_1",
				task_description=f"Task {i}",
				success=True,  # All successful
				completion_time_seconds=30.0
			)
			data_manager.store_conversation(conversation)
			
		baseline_version = data_manager.create_data_version(
			version_name="baseline",
			created_by="test_user"
		)
		
		# Create comparison version with degraded performance
		for i in range(10):
			conversation = ConversationRecord(
				conversation_id=f"comparison_{i}",
				session_id="session_1",
				task_description=f"Task {i}",
				success=i < 7,  # 70% success rate
				completion_time_seconds=45.0  # Slower
			)
			data_manager.store_conversation(conversation)
			
		comparison_version = data_manager.create_data_version(
			version_name="comparison",
			created_by="test_user"
		)
		
		# Detect drift
		drift_analysis = data_manager.detect_data_drift(baseline_version, comparison_version)
		
		assert drift_analysis["drift_detected"] is True
		assert len(drift_analysis["significant_changes"]) > 0


class TestMetricsCollector:
	"""Test metrics collection functionality"""
	
	def test_task_tracking(self, metrics_collector):
		"""Test task metrics tracking"""
		task_id = metrics_collector.start_task("test_task_1")
		assert task_id == "test_task_1"
		assert metrics_collector.current_task_id == task_id
		
		# Record some actions
		metrics_collector.record_action("click", success=True, duration=1.5)
		metrics_collector.record_action("type", success=True, duration=2.0)
		metrics_collector.record_llm_call(tokens_used=150, cost=0.003)
		
		# End task
		metrics_collector.end_task(success=True)
		
		# Check stored metrics
		assert len(metrics_collector.agent_metrics) == 1
		task_metrics = metrics_collector.agent_metrics[0]
		assert task_metrics.task_id == task_id
		assert task_metrics.success is True
		assert task_metrics.actions_performed == 2
		assert task_metrics.llm_calls_made == 1
		assert task_metrics.total_tokens_used == 150
		
	def test_performance_summary(self, metrics_collector):
		"""Test performance summary generation"""
		# Create some test metrics
		for i in range(3):
			task_id = f"task_{i}"
			metrics_collector.start_task(task_id)
			metrics_collector.record_action("click", success=i < 2)  # 2/3 success
			metrics_collector.record_llm_call(tokens_used=100, cost=0.002)
			metrics_collector.end_task(success=i < 2)
			
		summary = metrics_collector.get_performance_summary(hours=1)
		
		assert summary["total_tasks"] == 3
		assert abs(summary["success_rate"] - 2/3) < 0.01  # ~67% success
		assert summary["llm_usage"]["total_calls"] == 3
		assert summary["llm_usage"]["total_tokens"] == 300
		
	def test_error_tracking(self, metrics_collector):
		"""Test error tracking and analysis"""
		# Start a task and record errors
		metrics_collector.start_task("error_test_task")
		metrics_collector.record_error(
			error_type="timeout",
			error_message="Operation timed out",
			severity="high"
		)
		metrics_collector.record_error(
			error_type="element_not_found",
			error_message="Could not find element",
			severity="medium"
		)
		metrics_collector.end_task(success=False)
		
		# Analyze errors
		error_analysis = metrics_collector.get_error_analysis(hours=1)
		
		assert error_analysis["total_errors"] == 2
		assert error_analysis["unique_error_types"] == 2
		assert error_analysis["severity_breakdown"]["high"] == 1
		assert error_analysis["severity_breakdown"]["medium"] == 1


class TestModelEvaluator:
	"""Test model evaluation functionality"""
	
	def test_evaluation_task_creation(self, model_evaluator):
		"""Test creating evaluation tasks"""
		task_id = model_evaluator.create_evaluation_task(
			name="Test Task",
			description="A test evaluation task",
			task_prompt="Navigate to google.com and search for Python",
			success_criteria={"must_visit_google": True},
			difficulty="easy"
		)
		
		assert task_id is not None
		
		# Load task
		task = model_evaluator.load_evaluation_task(task_id)
		assert task is not None
		assert task.name == "Test Task"
		assert task.difficulty == "easy"
		
	def test_model_evaluation(self, model_evaluator):
		"""Test evaluating a model on a task"""
		# Create a test task
		task_id = model_evaluator.create_evaluation_task(
			name="Mock Task",
			description="Mock evaluation task",
			task_prompt="Test prompt",
			difficulty="easy"
		)
		
		# Evaluate model (will use mock evaluation)
		result = model_evaluator.evaluate_model(
			model_id="test_model_123",
			task_id=task_id
		)
		
		assert result is not None
		assert result.model_id == "test_model_123"
		assert result.task_id == task_id
		assert 0 <= result.overall_score <= 1
		assert result.completion_time_seconds > 0
		
	def test_benchmark_suite(self, model_evaluator):
		"""Test running a benchmark suite"""
		# Use default tasks that are created automatically
		tasks = model_evaluator.list_evaluation_tasks()
		assert len(tasks) >= 3  # Should have default tasks
		
		# Run benchmark on a subset
		benchmark_result = model_evaluator.run_benchmark_suite(
			model_id="benchmark_test_model",
			task_filters={"difficulty": "easy"}
		)
		
		assert "summary" in benchmark_result
		assert "total_tasks" in benchmark_result["summary"]
		assert benchmark_result["summary"]["total_tasks"] >= 1
		
	@patch('mlops.evaluator.ModelEvaluator._mock_evaluation')
	def test_evaluation_scoring(self, mock_evaluation, model_evaluator):
		"""Test evaluation scoring logic"""
		# Mock a successful evaluation
		mock_evaluation.return_value = (True, [
			{"step": 1, "type": "navigate", "success": True},
			{"step": 2, "type": "click", "success": True},
			{"step": 3, "type": "type", "success": True}
		])
		
		task_id = model_evaluator.create_evaluation_task(
			name="Scoring Test",
			description="Test scoring",
			task_prompt="Test",
			success_criteria={"max_steps": 5}
		)
		
		result = model_evaluator.evaluate_model("scoring_model", task_id)
		
		# Should have high scores for successful task
		assert result.success is True
		assert result.task_completion_score == 1.0
		assert result.overall_score > 0.7  # Should be high for successful completion


class TestIntegration:
	"""Integration tests for the complete MLOps system"""
	
	def test_end_to_end_workflow(self, temp_dir):
		"""Test a complete end-to-end MLOps workflow"""
		# Initialize all components
		config_manager = ConfigManager(config_dir=str(Path(temp_dir) / "config"))
		model_registry = ModelRegistry(registry_dir=str(Path(temp_dir) / "registry"))
		experiment_tracker = ExperimentTracker(storage_dir=str(Path(temp_dir) / "experiments"))
		evaluator = ModelEvaluator(evaluation_dir=str(Path(temp_dir) / "evaluations"))
		
		# 1. Load configuration
		config = config_manager.load_config("development")
		assert config is not None
		
		# 2. Register a model
		model_id = model_registry.register_model(
			name="E2E_Test_Model",
			llm_provider=config.llm.provider,
			llm_model=config.llm.model,
			temperature=config.llm.temperature
		)
		assert model_id is not None
		
		# 3. Create experiment
		exp_id = experiment_tracker.create_experiment(
			name="E2E Test Experiment",
			description="End-to-end test",
			llm_provider=config.llm.provider,
			llm_model=config.llm.model
		)
		assert exp_id is not None
		
		# 4. Run evaluation
		tasks = evaluator.list_evaluation_tasks()
		if tasks:
			task_id = tasks[0].task_id
			evaluation_result = evaluator.evaluate_model(model_id, task_id)
			assert evaluation_result is not None
			
			# 5. Update model performance
			model_registry.update_model_performance(
				model_id=model_id,
				success_rate=evaluation_result.overall_score,
				avg_completion_time=evaluation_result.completion_time_seconds
			)
			
			# 6. Verify model was updated
			updated_model = model_registry.get_model(model_id)
			assert updated_model["success_rate"] == evaluation_result.overall_score
			
		# 7. Get registry stats
		stats = model_registry.get_registry_stats()
		assert stats["total_models"] >= 1
		
	def test_cli_integration(self, temp_dir):
		"""Test CLI integration with core components"""
		from mlops.cli import cli
		from click.testing import CliRunner
		
		# Test CLI commands
		runner = CliRunner()
		
		# Test config list command
		with runner.isolated_filesystem():
			result = runner.invoke(cli, ['--config-dir', temp_dir, 'config', 'list-envs'])
			assert result.exit_code == 0
			assert 'development' in result.output
			
		# Test model registry command
		with runner.isolated_filesystem():
			result = runner.invoke(cli, [
				'--config-dir', temp_dir,
				'model', 'register',
				'CLI_Test_Model',
				'openai',
				'gpt-4',
				'--version', '1.0.0'
			])
			assert result.exit_code == 0
			assert 'Registered model' in result.output


if __name__ == "__main__":
	pytest.main([__file__, "-v"])