"""
Command-line interface for Browser.AI MLOps

This module provides a comprehensive CLI for managing MLOps operations including:
- Experiment management
- Model evaluation and comparison
- Data versioning and management
- Configuration management
- Monitoring and reporting
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import click

from .config_manager import ConfigManager
from .data_manager import DataManager
from .evaluator import ModelEvaluator
from .experiment_tracker import ExperimentTracker
from .metrics import MetricsCollector
from .model_registry import ModelRegistry


@click.group()
@click.option('--config-dir', default='mlops/config', help='Configuration directory')
@click.option('--data-dir', default='mlops/data', help='Data directory')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config_dir, data_dir, verbose):
	"""Browser.AI MLOps Command Line Interface"""
	
	# Setup logging
	log_level = logging.DEBUG if verbose else logging.INFO
	logging.basicConfig(
		level=log_level,
		format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	)
	
	# Initialize components
	ctx.ensure_object(dict)
	ctx.obj['config_manager'] = ConfigManager(config_dir)
	ctx.obj['data_manager'] = DataManager(data_dir)
	ctx.obj['experiment_tracker'] = ExperimentTracker()
	ctx.obj['model_registry'] = ModelRegistry()
	ctx.obj['evaluator'] = ModelEvaluator()
	ctx.obj['metrics'] = MetricsCollector()


# Configuration Management Commands
@cli.group()
def config():
	"""Configuration management commands"""
	pass


@config.command()
@click.argument('environment')
@click.pass_context
def load(ctx, environment):
	"""Load configuration for environment"""
	config_manager = ctx.obj['config_manager']
	try:
		config = config_manager.load_config(environment)
		click.echo(f"✅ Loaded configuration for environment: {environment}")
		click.echo(f"LLM Provider: {config.llm.provider}")
		click.echo(f"LLM Model: {config.llm.model}")
		click.echo(f"Environment: {config.environment}")
	except Exception as e:
		click.echo(f"❌ Failed to load configuration: {e}")
		sys.exit(1)


@config.command()
@click.pass_context
def list_envs(ctx):
	"""List available environments"""
	config_manager = ctx.obj['config_manager']
	environments = config_manager.list_environments()
	
	click.echo("Available environments:")
	for env in environments:
		click.echo(f"  • {env}")


@config.command()
@click.argument('environment')
@click.pass_context
def validate(ctx, environment):
	"""Validate environment configuration"""
	config_manager = ctx.obj['config_manager']
	try:
		config = config_manager.load_config(environment)
		warnings = config_manager.validate_config(config)
		
		if not warnings:
			click.echo(f"✅ Configuration for {environment} is valid")
		else:
			click.echo(f"⚠️ Configuration warnings for {environment}:")
			for warning in warnings:
				click.echo(f"  • {warning}")
	except Exception as e:
		click.echo(f"❌ Configuration validation failed: {e}")
		sys.exit(1)


@config.command()
@click.argument('flag_name')
@click.argument('enabled', type=bool)
@click.argument('environment')
@click.pass_context
def set_feature_flag(ctx, flag_name, enabled, environment):
	"""Set a feature flag for an environment"""
	config_manager = ctx.obj['config_manager']
	try:
		config_manager.update_feature_flag(flag_name, enabled, environment)
		status = "enabled" if enabled else "disabled"
		click.echo(f"✅ Feature flag '{flag_name}' {status} for {environment}")
	except Exception as e:
		click.echo(f"❌ Failed to update feature flag: {e}")
		sys.exit(1)


# Experiment Management Commands
@cli.group()
def experiment():
	"""Experiment management commands"""
	pass


@experiment.command()
@click.argument('name')
@click.option('--description', help='Experiment description')
@click.option('--llm-provider', default='openai', help='LLM provider')
@click.option('--llm-model', default='gpt-4', help='LLM model')
@click.option('--temperature', default=0.1, help='Temperature setting')
@click.option('--tags', help='Comma-separated tags')
@click.pass_context
def create(ctx, name, description, llm_provider, llm_model, temperature, tags):
	"""Create a new experiment"""
	tracker = ctx.obj['experiment_tracker']
	
	tag_list = tags.split(',') if tags else []
	
	try:
		experiment_id = tracker.create_experiment(
			name=name,
			description=description,
			tags=tag_list,
			llm_provider=llm_provider,
			llm_model=llm_model,
			temperature=temperature
		)
		click.echo(f"✅ Created experiment: {experiment_id}")
		click.echo(f"Name: {name}")
		click.echo(f"LLM: {llm_provider}/{llm_model}")
	except Exception as e:
		click.echo(f"❌ Failed to create experiment: {e}")
		sys.exit(1)


@experiment.command()
@click.pass_context
def list(ctx):
	"""List all experiments"""
	tracker = ctx.obj['experiment_tracker']
	experiments = tracker.list_experiments()
	
	if not experiments:
		click.echo("No experiments found")
		return
		
	click.echo(f"Found {len(experiments)} experiments:")
	for exp in experiments:
		click.echo(f"  • {exp['experiment_id'][:8]}... - {exp['experiment_name']}")
		click.echo(f"    LLM: {exp['llm_provider']}/{exp['llm_model']}")
		click.echo(f"    Created: {exp['created_at'][:19]}")


@experiment.command()
@click.argument('experiment_ids', nargs=-1)
@click.pass_context
def compare(ctx, experiment_ids):
	"""Compare multiple experiments"""
	if len(experiment_ids) < 2:
		click.echo("❌ Please provide at least 2 experiment IDs to compare")
		sys.exit(1)
		
	tracker = ctx.obj['experiment_tracker']
	try:
		comparison = tracker.compare_experiments(list(experiment_ids))
		
		click.echo(f"📊 Experiment Comparison")
		click.echo(f"Total runs: {comparison['summary']['total_runs']}")
		click.echo(f"Average success rate: {comparison['summary']['average_success_rate']:.2%}")
		click.echo(f"Average completion time: {comparison['summary']['average_completion_time']:.1f}s")
		
		click.echo("\n📋 Individual Results:")
		for exp in comparison['experiments']:
			click.echo(f"  {exp['experiment_id'][:8]}...")
			click.echo(f"    Runs: {exp['total_runs']}")
			click.echo(f"    Success Rate: {exp['avg_success_rate']:.2%}")
			click.echo(f"    Avg Time: {exp['avg_completion_time']:.1f}s")
			
	except Exception as e:
		click.echo(f"❌ Failed to compare experiments: {e}")
		sys.exit(1)


# Model Management Commands
@cli.group()
def model():
	"""Model management commands"""
	pass


@model.command()
@click.argument('name')
@click.argument('llm_provider')
@click.argument('llm_model')
@click.option('--version', default='1.0.0', help='Model version')
@click.option('--description', help='Model description')
@click.option('--temperature', default=0.1, help='Temperature setting')
@click.option('--tags', help='Comma-separated tags')
@click.pass_context
def register(ctx, name, llm_provider, llm_model, version, description, temperature, tags):
	"""Register a new model"""
	registry = ctx.obj['model_registry']
	
	tag_list = tags.split(',') if tags else []
	
	try:
		model_id = registry.register_model(
			name=name,
			llm_provider=llm_provider,
			llm_model=llm_model,
			version=version,
			description=description,
			tags=tag_list,
			temperature=temperature
		)
		click.echo(f"✅ Registered model: {model_id}")
		click.echo(f"Name: {name} v{version}")
		click.echo(f"Provider: {llm_provider}/{llm_model}")
	except Exception as e:
		click.echo(f"❌ Failed to register model: {e}")
		sys.exit(1)


@model.command()
@click.option('--status', help='Filter by status')
@click.option('--provider', help='Filter by provider')
@click.pass_context
def list(ctx, status, provider):
	"""List registered models"""
	registry = ctx.obj['model_registry']
	
	filters = {}
	if status:
		filters['status'] = status
	if provider:
		filters['provider'] = provider
		
	models = registry.list_models(**filters)
	
	if not models:
		click.echo("No models found")
		return
		
	click.echo(f"Found {len(models)} models:")
	for model in models:
		click.echo(f"  • {model['model_id'][:12]}... - {model['name']} v{model['version']}")
		click.echo(f"    Provider: {model['llm_provider']}/{model['llm_model']}")
		click.echo(f"    Status: {model['status']}")
		if model.get('success_rate'):
			click.echo(f"    Success Rate: {model['success_rate']:.2%}")


@model.command()
@click.argument('model_ids', nargs=-1)
@click.pass_context
def compare(ctx, model_ids):
	"""Compare multiple models"""
	if len(model_ids) < 2:
		click.echo("❌ Please provide at least 2 model IDs to compare")
		sys.exit(1)
		
	registry = ctx.obj['model_registry']
	try:
		comparison = registry.compare_models(list(model_ids))
		
		click.echo("📊 Model Comparison")
		
		# Show best performers
		for metric, best in comparison['summary'].items():
			if best['model_id']:
				click.echo(f"Best {metric}: {best['model_id'][:8]}... ({best['value']})")
				
		click.echo("\n📋 Model Details:")
		for model in comparison['models']:
			click.echo(f"  {model['model_id'][:8]}... - {model['name']} v{model['version']}")
			click.echo(f"    Provider: {model['provider']}/{model['model']}")
			if model['success_rate']:
				click.echo(f"    Success Rate: {model['success_rate']:.2%}")
			if model['avg_completion_time']:
				click.echo(f"    Avg Time: {model['avg_completion_time']:.1f}s")
				
	except Exception as e:
		click.echo(f"❌ Failed to compare models: {e}")
		sys.exit(1)


@model.command()
@click.argument('model_id')
@click.argument('target')
@click.option('--status', default='production', help='Deployment status')
@click.pass_context
def deploy(ctx, model_id, target, status):
	"""Deploy a model"""
	registry = ctx.obj['model_registry']
	try:
		registry.deploy_model(model_id, target, status)
		click.echo(f"✅ Deployed model {model_id[:8]}... to {target}")
		click.echo(f"Status: {status}")
	except Exception as e:
		click.echo(f"❌ Failed to deploy model: {e}")
		sys.exit(1)


# Evaluation Commands
@cli.group()
def evaluate():
	"""Model evaluation commands"""
	pass


@evaluate.command()
@click.argument('model_id')
@click.argument('task_id')
@click.pass_context
def model(ctx, model_id, task_id):
	"""Evaluate a model on a specific task"""
	evaluator = ctx.obj['evaluator']
	try:
		result = evaluator.evaluate_model(model_id, task_id)
		
		click.echo(f"📊 Evaluation Results")
		click.echo(f"Model: {model_id[:12]}...")
		click.echo(f"Task: {task_id}")
		click.echo(f"Success: {'✅' if result.success else '❌'}")
		click.echo(f"Completion Time: {result.completion_time_seconds:.1f}s")
		click.echo(f"Steps Taken: {result.steps_taken}")
		click.echo(f"Overall Score: {result.overall_score:.2f}")
		click.echo(f"Task Completion: {result.task_completion_score:.2f}")
		click.echo(f"Efficiency: {result.efficiency_score:.2f}")
		click.echo(f"Accuracy: {result.accuracy_score:.2f}")
		
	except Exception as e:
		click.echo(f"❌ Evaluation failed: {e}")
		sys.exit(1)


@evaluate.command()
@click.argument('model_id')
@click.option('--category', help='Filter tasks by category')
@click.option('--difficulty', help='Filter tasks by difficulty')
@click.pass_context
def benchmark(ctx, model_id, category, difficulty):
	"""Run benchmark suite on a model"""
	evaluator = ctx.obj['evaluator']
	
	filters = {}
	if category:
		filters['category'] = category
	if difficulty:
		filters['difficulty'] = difficulty
		
	try:
		results = evaluator.run_benchmark_suite(model_id, task_filters=filters)
		
		click.echo(f"📊 Benchmark Results for {model_id[:12]}...")
		click.echo(f"Total Tasks: {results['summary']['total_tasks']}")
		click.echo(f"Successful Tasks: {results['summary']['successful_tasks']}")
		click.echo(f"Success Rate: {results['summary']['success_rate']:.2%}")
		click.echo(f"Average Score: {results['summary']['average_score']:.2f}")
		click.echo(f"Average Time: {results['summary']['average_completion_time']:.1f}s")
		
		if results['category_breakdown']:
			click.echo("\n📋 Category Breakdown:")
			for cat, score in results['category_breakdown'].items():
				click.echo(f"  {cat}: {score:.2f}")
				
	except Exception as e:
		click.echo(f"❌ Benchmark failed: {e}")
		sys.exit(1)


@evaluate.command()
@click.option('--category', help='Task category')
@click.option('--difficulty', help='Task difficulty')
@click.pass_context
def list_tasks(ctx, category, difficulty):
	"""List available evaluation tasks"""
	evaluator = ctx.obj['evaluator']
	
	filters = {}
	if category:
		filters['category'] = category
	if difficulty:
		filters['difficulty'] = difficulty
		
	tasks = evaluator.list_evaluation_tasks(**filters)
	
	if not tasks:
		click.echo("No tasks found")
		return
		
	click.echo(f"Found {len(tasks)} evaluation tasks:")
	for task in tasks:
		click.echo(f"  • {task.task_id} - {task.name}")
		click.echo(f"    Category: {task.category} | Difficulty: {task.difficulty}")
		click.echo(f"    Description: {task.description}")


# Data Management Commands
@cli.group()
def data():
	"""Data management commands"""
	pass


@data.command()
@click.argument('version_name')
@click.argument('created_by')
@click.option('--description', help='Version description')
@click.option('--days-back', default=30, help='Include data from last N days')
@click.option('--min-quality', type=float, help='Minimum quality score')
@click.pass_context
def create_version(ctx, version_name, created_by, description, days_back, min_quality):
	"""Create a new data version"""
	data_manager = ctx.obj['data_manager']
	
	# Set date filter
	date_from = datetime.now() - timedelta(days=days_back)
	
	filters = {'date_from': date_from}
	if min_quality:
		filters['min_quality_score'] = min_quality
		
	try:
		version_id = data_manager.create_data_version(
			version_name=version_name,
			created_by=created_by,
			description=description,
			conversation_filters=filters
		)
		click.echo(f"✅ Created data version: {version_id}")
		
		# Load and show statistics
		version = data_manager.load_data_version(version_id)
		if version:
			click.echo(f"Total conversations: {version.total_conversations}")
			click.echo(f"Success rate: {version.success_rate:.2%}")
			if version.avg_quality_score:
				click.echo(f"Average quality: {version.avg_quality_score:.2f}")
				
	except Exception as e:
		click.echo(f"❌ Failed to create data version: {e}")
		sys.exit(1)


@data.command()
@click.pass_context
def list_versions(ctx):
	"""List all data versions"""
	data_manager = ctx.obj['data_manager']
	versions = data_manager.list_data_versions()
	
	if not versions:
		click.echo("No data versions found")
		return
		
	click.echo(f"Found {len(versions)} data versions:")
	for version in versions:
		click.echo(f"  • {version.version_id} - {version.version_name}")
		click.echo(f"    Created: {version.created_at.strftime('%Y-%m-%d %H:%M')}")
		click.echo(f"    Conversations: {version.total_conversations}")
		click.echo(f"    Success Rate: {version.success_rate:.2%}")


@data.command()
@click.argument('version_id')
@click.argument('output_dir')
@click.option('--format', default='json', help='Export format (json, jsonl, csv)')
@click.option('--include-dom', is_flag=True, help='Include DOM snapshots')
@click.pass_context
def export(ctx, version_id, output_dir, format, include_dom):
	"""Export data version for training"""
	data_manager = ctx.obj['data_manager']
	try:
		data_manager.export_training_data(
			version_id=version_id,
			output_dir=output_dir,
			format=format,
			include_dom_snapshots=include_dom
		)
		click.echo(f"✅ Exported data version {version_id} to {output_dir}")
		click.echo(f"Format: {format}")
		if include_dom:
			click.echo("Included DOM snapshots")
	except Exception as e:
		click.echo(f"❌ Export failed: {e}")
		sys.exit(1)


@data.command()
@click.argument('baseline_version')
@click.argument('comparison_version')
@click.pass_context
def detect_drift(ctx, baseline_version, comparison_version):
	"""Detect data drift between versions"""
	data_manager = ctx.obj['data_manager']
	try:
		drift_analysis = data_manager.detect_data_drift(baseline_version, comparison_version)
		
		click.echo(f"📊 Data Drift Analysis")
		click.echo(f"Baseline: {baseline_version}")
		click.echo(f"Comparison: {comparison_version}")
		click.echo(f"Drift Detected: {'⚠️ Yes' if drift_analysis['drift_detected'] else '✅ No'}")
		
		if drift_analysis['significant_changes']:
			click.echo("\n📋 Significant Changes:")
			for change in drift_analysis['significant_changes']:
				click.echo(f"  • {change['metric']}: {change['change_percent']:+.1f}% ({change['direction']})")
				
		click.echo("\n📊 Metric Changes:")
		for metric, data in drift_analysis['metric_changes'].items():
			click.echo(f"  {metric}: {data['baseline']:.3f} → {data['comparison']:.3f} ({data['change_percent']:+.1f}%)")
			
	except Exception as e:
		click.echo(f"❌ Drift detection failed: {e}")
		sys.exit(1)


@data.command()
@click.pass_context
def stats(ctx):
	"""Show data storage statistics"""
	data_manager = ctx.obj['data_manager']
	stats = data_manager.get_storage_stats()
	
	click.echo("📊 Data Storage Statistics")
	click.echo(f"Total conversations: {stats['total_conversations']:,}")
	click.echo(f"Total DOM snapshots: {stats['total_dom_snapshots']:,}")
	click.echo(f"Total versions: {stats['total_versions']:,}")
	click.echo(f"Total storage: {stats['storage_usage_bytes'] / 1024**2:.1f} MB")
	
	click.echo("\n📁 Storage by type:")
	for data_type, size_bytes in stats['storage_by_type'].items():
		size_mb = size_bytes / 1024**2
		click.echo(f"  {data_type}: {size_mb:.1f} MB")


# Monitoring Commands
@cli.group()
def monitor():
	"""Monitoring and metrics commands"""
	pass


@monitor.command()
@click.option('--hours', default=24, help='Hours to analyze')
@click.pass_context
def performance(ctx, hours):
	"""Show performance summary"""
	metrics = ctx.obj['metrics']
	try:
		summary = metrics.get_performance_summary(hours)
		
		if 'message' in summary:
			click.echo(summary['message'])
			return
			
		click.echo(f"📊 Performance Summary ({hours}h)")
		click.echo(f"Total tasks: {summary['total_tasks']}")
		click.echo(f"Success rate: {summary['success_rate']:.2%}")
		click.echo(f"Average duration: {summary['avg_task_duration']:.1f}s")
		click.echo(f"Average steps: {summary['avg_steps_per_task']:.1f}")
		click.echo(f"Error rate: {summary['error_rate']:.2%}")
		
		click.echo(f"\n🤖 LLM Usage:")
		llm = summary['llm_usage']
		click.echo(f"Total calls: {llm['total_calls']:,}")
		click.echo(f"Total tokens: {llm['total_tokens']:,}")
		click.echo(f"Total cost: ${llm['total_cost']:.2f}")
		click.echo(f"Avg calls per task: {llm['avg_calls_per_task']:.1f}")
		
		if summary['error_breakdown']:
			click.echo(f"\n⚠️ Error Breakdown:")
			for error_type, count in summary['error_breakdown'].items():
				click.echo(f"  {error_type}: {count}")
				
	except Exception as e:
		click.echo(f"❌ Failed to get performance summary: {e}")
		sys.exit(1)


@monitor.command()
@click.pass_context
def health(ctx):
	"""Show system health status"""
	metrics = ctx.obj['metrics']
	health = metrics.get_system_health()
	
	status_icons = {
		"healthy": "✅",
		"warning": "⚠️",
		"critical": "❌",
		"no_data": "❓"
	}
	
	click.echo(f"🏥 System Health: {status_icons.get(health['status'], '❓')} {health['status'].upper()}")
	
	if health['status'] != 'no_data':
		click.echo(f"CPU: {health['cpu_percent']:.1f}%")
		click.echo(f"Memory: {health['memory_percent']:.1f}% ({health['memory_used_gb']:.1f}GB)")
		click.echo(f"Disk: {health['disk_usage_percent']:.1f}%")
		click.echo(f"Last updated: {health['timestamp']}")


@monitor.command()
@click.option('--hours', default=24, help='Hours to analyze')
@click.pass_context
def errors(ctx, hours):
	"""Analyze errors"""
	metrics = ctx.obj['metrics']
	try:
		error_analysis = metrics.get_error_analysis(hours)
		
		if 'message' in error_analysis:
			click.echo(error_analysis['message'])
			return
			
		click.echo(f"🚨 Error Analysis ({hours}h)")
		click.echo(f"Total errors: {error_analysis['total_errors']}")
		click.echo(f"Unique error types: {error_analysis['unique_error_types']}")
		click.echo(f"Unresolved errors: {error_analysis['unresolved_errors']}")
		
		click.echo(f"\n📊 Severity Breakdown:")
		for severity, count in error_analysis['severity_breakdown'].items():
			click.echo(f"  {severity}: {count}")
			
		if error_analysis['most_common_errors']:
			click.echo(f"\n🔥 Most Common Errors:")
			for error in error_analysis['most_common_errors']:
				click.echo(f"  • {error['error_type']}: {error['count']} occurrences")
				click.echo(f"    Latest: {error['latest_message']}")
				
	except Exception as e:
		click.echo(f"❌ Failed to analyze errors: {e}")
		sys.exit(1)


# Utility Commands
@cli.command()
@click.argument('output_file')
@click.option('--days', default=7, help='Days of data to include')
@click.pass_context
def generate_report(ctx, output_file, days):
	"""Generate comprehensive MLOps report"""
	
	# Collect data from all components
	config_manager = ctx.obj['config_manager']
	data_manager = ctx.obj['data_manager']
	model_registry = ctx.obj['model_registry']
	metrics = ctx.obj['metrics']
	
	try:
		report = {
			"report_generated": datetime.now().isoformat(),
			"report_period_days": days,
			"system_health": metrics.get_system_health(),
			"performance_summary": metrics.get_performance_summary(days * 24),
			"error_analysis": metrics.get_error_analysis(days * 24),
			"registry_stats": model_registry.get_registry_stats(),
			"data_storage_stats": data_manager.get_storage_stats(),
			"available_environments": config_manager.list_environments()
		}
		
		with open(output_file, 'w') as f:
			json.dump(report, f, indent=2, default=str)
			
		click.echo(f"✅ Generated report: {output_file}")
		
		# Show summary
		click.echo(f"\n📋 Report Summary:")
		click.echo(f"System Health: {report['system_health']['status']}")
		if 'total_tasks' in report['performance_summary']:
			click.echo(f"Tasks ({days}d): {report['performance_summary']['total_tasks']}")
			click.echo(f"Success Rate: {report['performance_summary']['success_rate']:.2%}")
		click.echo(f"Registered Models: {report['registry_stats']['total_models']}")
		click.echo(f"Total Conversations: {report['data_storage_stats']['total_conversations']:,}")
		
	except Exception as e:
		click.echo(f"❌ Failed to generate report: {e}")
		sys.exit(1)


if __name__ == '__main__':
	cli()