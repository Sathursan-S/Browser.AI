#!/usr/bin/env python3
"""
MLOps Demo Script for Browser.AI

This script demonstrates the complete MLOps workflow including:
1. Configuration management
2. Model registration
3. Experiment creation and tracking
4. Model evaluation
5. Performance monitoring
6. Data management
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mlops import (
    ConfigManager,
    ModelRegistry,
    ExperimentTracker,
    ModelEvaluator,
    MetricsCollector,
    DataManager
)
from mlops.data_manager import ConversationRecord


def main():
    print("🚀 Browser.AI MLOps Demo")
    print("=" * 50)
    
    # 1. Configuration Management
    print("\n📋 1. Configuration Management")
    config_manager = ConfigManager()
    
    try:
        config = config_manager.load_config("development")
        print(f"✅ Loaded development configuration")
        print(f"   LLM Provider: {config.llm.provider}")
        print(f"   LLM Model: {config.llm.model}")
        print(f"   Temperature: {config.llm.temperature}")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # 2. Model Registry
    print("\n🏛️ 2. Model Registry")
    registry = ModelRegistry("demo_registry")
    
    # Register multiple models for comparison
    models = []
    for provider, model_name, temp in [
        ("openai", "gpt-4", 0.0),
        ("openai", "gpt-4", 0.1),
        ("anthropic", "claude-3", 0.0),
    ]:
        model_id = registry.register_model(
            name=f"BrowserAI_{provider}_{model_name.replace('-', '_')}",
            llm_provider=provider,
            llm_model=model_name,
            temperature=temp,
            version="1.0.0",
            description=f"{provider} {model_name} for browser automation"
        )
        models.append(model_id)
        print(f"✅ Registered model: {model_id[:12]}...")
    
    # 3. Experiment Tracking
    print("\n🧪 3. Experiment Tracking")
    tracker = ExperimentTracker("demo_experiments")
    
    experiment_results = []
    for i, model_id in enumerate(models):
        model_info = registry.get_model(model_id)
        exp_name = f"Model_Comparison_Experiment_{i+1}"
        
        # Create experiment
        exp_id = tracker.create_experiment(
            name=exp_name,
            description=f"Testing {model_info['llm_provider']}/{model_info['llm_model']}",
            llm_provider=model_info['llm_provider'],
            llm_model=model_info['llm_model'],
            temperature=model_info['temperature']
        )
        print(f"✅ Created experiment: {exp_name}")
        
        # Run simulated experiment
        run_id = tracker.start_run()
        
        # Simulate experiment execution
        import random
        success_rate = random.uniform(0.75, 0.95)
        completion_time = random.uniform(30, 120)
        
        for j in range(10):  # Simulate 10 tasks
            success = random.random() < success_rate
            tracker.log_action("click", success=success)
            tracker.log_conversation("user", f"Task {j+1}")
            tracker.log_metric("task_success", 1.0 if success else 0.0)
        
        tracker.complete_run(success=success_rate > 0.8)
        
        # Update model performance
        registry.update_model_performance(
            model_id=model_id,
            success_rate=success_rate,
            avg_completion_time=completion_time,
            cost_per_task=random.uniform(0.05, 0.20)
        )
        
        experiment_results.append({
            'model_id': model_id,
            'exp_id': exp_id,
            'success_rate': success_rate,
            'completion_time': completion_time
        })
        
        print(f"   Success Rate: {success_rate:.2%}")
        print(f"   Avg Time: {completion_time:.1f}s")
    
    # 4. Model Evaluation
    print("\n📊 4. Model Evaluation")
    evaluator = ModelEvaluator("demo_evaluations")
    
    # List available evaluation tasks
    tasks = evaluator.list_evaluation_tasks()
    print(f"✅ Available evaluation tasks: {len(tasks)}")
    for task in tasks[:3]:  # Show first 3
        print(f"   • {task.name} ({task.difficulty})")
    
    # Evaluate best performing model
    best_model = max(experiment_results, key=lambda x: x['success_rate'])
    if tasks:
        print(f"\n📈 Evaluating best model: {best_model['model_id'][:12]}...")
        
        eval_result = evaluator.evaluate_model(
            model_id=best_model['model_id'],
            task_id=tasks[0].task_id  # Use first task
        )
        
        print(f"✅ Evaluation completed:")
        print(f"   Task Success: {'✅' if eval_result.success else '❌'}")
        print(f"   Overall Score: {eval_result.overall_score:.2f}")
        print(f"   Efficiency Score: {eval_result.efficiency_score:.2f}")
    
    # 5. Performance Monitoring
    print("\n📊 5. Performance Monitoring")
    metrics = MetricsCollector("demo_metrics")
    
    # Simulate monitoring some tasks
    for i in range(3):
        task_id = metrics.start_task(f"demo_task_{i+1}")
        
        # Simulate task execution
        metrics.record_action("navigate", success=True, duration=2.1)
        metrics.record_action("click", success=True, duration=0.8)
        metrics.record_llm_call(tokens_used=random.randint(100, 300), cost=0.005)
        metrics.record_page_load("https://example.com", load_time=1.5)
        
        metrics.end_task(success=True)
    
    # Get performance summary
    summary = metrics.get_performance_summary(hours=1)
    print(f"✅ Performance Summary:")
    print(f"   Total Tasks: {summary.get('total_tasks', 0)}")
    print(f"   Success Rate: {summary.get('success_rate', 0):.2%}")
    print(f"   LLM Calls: {summary.get('llm_usage', {}).get('total_calls', 0)}")
    
    # 6. Data Management
    print("\n💾 6. Data Management")
    data_manager = DataManager("demo_data")
    
    # Store some conversation data
    conversations_stored = 0
    for i, result in enumerate(experiment_results):
        conversation = ConversationRecord(
            conversation_id=f"demo_conv_{i+1}",
            session_id=f"session_{i+1}",
            task_description=f"Browser automation task {i+1}",
            messages=[
                {"role": "user", "content": "Navigate to google.com"},
                {"role": "assistant", "content": "I'll help you navigate to Google."}
            ],
            success=result['success_rate'] > 0.8,
            completion_time_seconds=result['completion_time'],
            model_id=result['model_id'],
            quality_score=result['success_rate']
        )
        
        data_manager.store_conversation(conversation)
        conversations_stored += 1
    
    print(f"✅ Stored {conversations_stored} conversations")
    
    # Create data version
    version_id = data_manager.create_data_version(
        version_name="demo_dataset_v1",
        created_by="mlops_demo",
        description="Demo dataset for Browser.AI MLOps showcase"
    )
    print(f"✅ Created data version: {version_id[:12]}...")
    
    # 7. Model Comparison and Deployment
    print("\n🚀 7. Model Comparison & Deployment")
    
    # Compare all models
    comparison = registry.compare_models([r['model_id'] for r in experiment_results])
    
    print("📊 Model Comparison Results:")
    best_success = comparison['summary']['best_success_rate']
    best_speed = comparison['summary']['fastest_completion']
    best_cost = comparison['summary']['lowest_cost']
    
    if best_success['model_id']:
        print(f"   🏆 Best Success Rate: {best_success['model_id'][:12]}... ({best_success['value']:.2%})")
    if best_speed['model_id']:
        print(f"   ⚡ Fastest Completion: {best_speed['model_id'][:12]}... ({best_speed['value']:.1f}s)")
    if best_cost['model_id'] and best_cost['value'] < float('inf'):
        print(f"   💰 Lowest Cost: {best_cost['model_id'][:12]}... (${best_cost['value']:.3f})")
    
    # Deploy best overall model
    if best_success['model_id']:
        registry.deploy_model(
            model_id=best_success['model_id'],
            target="demo_production",
            status="production"
        )
        print(f"🚀 Deployed best model to production")
    
    # 8. Generate Report
    print("\n📋 8. Generate MLOps Report")
    
    # Get registry stats
    registry_stats = registry.get_registry_stats()
    data_stats = data_manager.get_storage_stats()
    
    print("📊 MLOps Summary Report:")
    print(f"   Models Registered: {registry_stats['total_models']}")
    print(f"   Experiments Run: {len(experiment_results)}")
    print(f"   Conversations Stored: {data_stats['total_conversations']}")
    print(f"   Data Storage: {data_stats['storage_usage_bytes'] / 1024:.1f} KB")
    print(f"   Production Models: {registry_stats['by_status'].get('production', 0)}")
    
    print("\n✅ MLOps Demo Complete!")
    print("=" * 50)
    print("\nNext Steps:")
    print("• Use the CLI: python -m mlops.cli --help")
    print("• View configurations: mlops/config/")
    print("• Check experiment data: demo_experiments/")
    print("• Review model registry: demo_registry/")
    print("• Explore monitoring: python -m mlops.cli monitor performance")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\n🎉 Demo completed successfully at {datetime.now()}")
        else:
            print(f"\n❌ Demo failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n⏹️ Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Demo crashed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)