"""
Browser.AI Agent MLOps Integration Example

This module shows how to integrate the MLOps system with the actual Browser.AI agent
for production monitoring and experiment tracking.
"""

import logging
import time
from datetime import datetime
from typing import Optional

from browser_ai.agent.service import Agent  # Browser.AI agent
from browser_ai.browser.browser import Browser
from mlops import (
    ConfigManager,
    ExperimentTracker, 
    ModelRegistry,
    MetricsCollector,
    DataManager
)
from mlops.data_manager import ConversationRecord


class MLOpsIntegratedAgent:
    """
    Browser.AI Agent with integrated MLOps tracking
    
    This wrapper class adds comprehensive MLOps capabilities to the existing
    Browser.AI agent without modifying the core agent code.
    """
    
    def __init__(
        self,
        config_environment: str = "development",
        experiment_name: Optional[str] = None,
        model_id: Optional[str] = None
    ):
        """Initialize MLOps-integrated agent"""
        
        # Initialize MLOps components
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config(config_environment)
        
        self.experiment_tracker = ExperimentTracker()
        self.model_registry = ModelRegistry()
        self.metrics_collector = MetricsCollector()
        self.data_manager = DataManager()
        
        # Initialize Browser.AI components
        self.browser = Browser(
            headless=self.config.browser.headless,
            disable_security=self.config.browser.disable_security
        )
        
        # Initialize agent with MLOps configuration
        self.agent = Agent(
            browser=self.browser,
            llm_config={
                'provider': self.config.llm.provider,
                'model': self.config.llm.model,
                'temperature': self.config.llm.temperature
            }
        )
        
        # Set up experiment tracking if specified
        if experiment_name:
            self.experiment_id = self.experiment_tracker.create_experiment(
                name=experiment_name,
                description=f"Production run with {self.config.llm.provider}/{self.config.llm.model}",
                llm_provider=self.config.llm.provider,
                llm_model=self.config.llm.model,
                temperature=self.config.llm.temperature
            )
            self.run_id = self.experiment_tracker.start_run(self.experiment_id)
        else:
            self.experiment_id = None
            self.run_id = None
            
        # Set up model tracking
        if model_id:
            self.model_id = model_id
        else:
            # Register current configuration as a model
            self.model_id = self.model_registry.register_model(
                name=f"Production_{self.config.llm.provider}_{self.config.llm.model}",
                llm_provider=self.config.llm.provider,
                llm_model=self.config.llm.model,
                temperature=self.config.llm.temperature,
                version="auto",
                description="Auto-registered production model"
            )
            
        self.logger = logging.getLogger(__name__)
        self.current_task_id = None
        
    def run_task(
        self,
        task_description: str,
        max_steps: Optional[int] = None,
        session_id: Optional[str] = None
    ) -> dict:
        """
        Run a browser automation task with full MLOps tracking
        
        Args:
            task_description: Natural language description of the task
            max_steps: Maximum number of steps to attempt
            session_id: Optional session ID for grouping related tasks
            
        Returns:
            Dictionary containing task results and metrics
        """
        
        # Start task tracking
        task_id = f"task_{int(time.time())}"
        self.current_task_id = task_id
        
        self.metrics_collector.start_task(task_id)
        
        # Log task start
        if self.experiment_tracker.current_run:
            self.experiment_tracker.log_conversation(
                role="user", 
                content=task_description,
                metadata={"task_id": task_id, "session_id": session_id}
            )
        
        start_time = time.time()
        conversation_messages = [{"role": "user", "content": task_description}]
        
        try:
            # Execute the actual browser automation task
            self.logger.info(f"Starting task: {task_description}")
            
            # This would be the actual agent execution
            # For demo purposes, we'll simulate the execution
            result = self._simulate_agent_execution(task_description, max_steps or self.config.agent.max_steps)
            
            # Record successful completion
            completion_time = time.time() - start_time
            
            # Add agent response to conversation
            conversation_messages.append({
                "role": "assistant", 
                "content": result.get("agent_response", "Task completed successfully"),
                "metadata": result.get("metadata", {})
            })
            
            # Log metrics
            self._record_execution_metrics(result, completion_time)
            
            # Store conversation data
            self._store_conversation_data(
                task_id=task_id,
                session_id=session_id or "default",
                task_description=task_description,
                messages=conversation_messages,
                success=result["success"],
                completion_time=completion_time,
                steps_taken=result.get("steps_taken", 0)
            )
            
            # Update model performance
            self._update_model_performance(result, completion_time)
            
            # End task tracking
            self.metrics_collector.end_task(success=result["success"])
            
            self.logger.info(f"Task completed: {result['success']}")
            
            return {
                "success": result["success"],
                "task_id": task_id,
                "completion_time": completion_time,
                "steps_taken": result.get("steps_taken", 0),
                "agent_response": result.get("agent_response", ""),
                "metrics": self._get_task_metrics(task_id)
            }
            
        except Exception as e:
            # Record error
            completion_time = time.time() - start_time
            
            self.metrics_collector.record_error(
                error_type=type(e).__name__,
                error_message=str(e),
                severity="high"
            )
            
            if self.experiment_tracker.current_run:
                self.experiment_tracker.complete_run(
                    success=False, 
                    error_message=str(e)
                )
            
            self.metrics_collector.end_task(success=False)
            
            self.logger.error(f"Task failed: {e}")
            
            return {
                "success": False,
                "task_id": task_id,
                "completion_time": completion_time,
                "error": str(e),
                "metrics": self._get_task_metrics(task_id)
            }
    
    def _simulate_agent_execution(self, task_description: str, max_steps: int) -> dict:
        """
        Simulate agent execution for demo purposes
        In production, this would call the actual Browser.AI agent
        """
        import random
        
        # Simulate various actions
        actions = ["navigate", "click", "type", "scroll", "screenshot"]
        steps_taken = 0
        
        for step in range(random.randint(3, min(max_steps, 10))):
            action = random.choice(actions)
            success = random.random() > 0.1  # 90% success rate per action
            duration = random.uniform(0.5, 3.0)
            
            # Record action
            self.metrics_collector.record_action(action, success=success, duration=duration)
            
            if self.experiment_tracker.current_run:
                self.experiment_tracker.log_action(action, success=success)
            
            # Simulate page loads for navigate actions
            if action == "navigate":
                self.metrics_collector.record_page_load(
                    url="https://example.com",
                    load_time=random.uniform(1.0, 4.0),
                    dom_complexity=random.randint(100, 1000)
                )
            
            steps_taken += 1
            
            if not success and random.random() < 0.3:  # 30% chance to fail on error
                break
        
        # Simulate LLM calls
        for _ in range(random.randint(2, 5)):
            tokens_used = random.randint(50, 300)
            cost = tokens_used * 0.00002  # Rough cost estimate
            
            self.metrics_collector.record_llm_call(
                tokens_used=tokens_used,
                cost=cost,
                model=self.config.llm.model
            )
        
        # Determine overall success
        overall_success = random.random() > 0.2  # 80% task success rate
        
        return {
            "success": overall_success,
            "steps_taken": steps_taken,
            "agent_response": f"{'Successfully completed' if overall_success else 'Failed to complete'} task: {task_description}",
            "metadata": {
                "actions_performed": steps_taken,
                "llm_model": self.config.llm.model
            }
        }
    
    def _record_execution_metrics(self, result: dict, completion_time: float):
        """Record detailed execution metrics"""
        if self.experiment_tracker.current_run:
            self.experiment_tracker.log_metric("completion_time", completion_time)
            self.experiment_tracker.log_metric("steps_taken", result.get("steps_taken", 0))
            self.experiment_tracker.log_metric("success", 1.0 if result["success"] else 0.0)
    
    def _store_conversation_data(
        self,
        task_id: str,
        session_id: str,
        task_description: str,
        messages: list,
        success: bool,
        completion_time: float,
        steps_taken: int
    ):
        """Store conversation data for future analysis"""
        conversation = ConversationRecord(
            conversation_id=task_id,
            session_id=session_id,
            task_description=task_description,
            messages=messages,
            success=success,
            completion_time_seconds=completion_time,
            steps_taken=steps_taken,
            model_id=self.model_id,
            quality_score=0.9 if success else 0.3  # Simple quality scoring
        )
        
        self.data_manager.store_conversation(conversation)
    
    def _update_model_performance(self, result: dict, completion_time: float):
        """Update model performance metrics in registry"""
        # This would typically be done in batch, but for demo we update immediately
        current_model = self.model_registry.get_model(self.model_id)
        if current_model:
            # Simple running average update
            evaluations = current_model.get("total_evaluations", 0)
            current_success_rate = current_model.get("success_rate", 0.5)
            current_avg_time = current_model.get("avg_completion_time", 60.0)
            
            new_success_rate = (current_success_rate * evaluations + (1.0 if result["success"] else 0.0)) / (evaluations + 1)
            new_avg_time = (current_avg_time * evaluations + completion_time) / (evaluations + 1)
            
            self.model_registry.update_model_performance(
                model_id=self.model_id,
                success_rate=new_success_rate,
                avg_completion_time=new_avg_time,
                increment_evaluations=True
            )
    
    def _get_task_metrics(self, task_id: str) -> dict:
        """Get metrics summary for a specific task"""
        return self.metrics_collector.get_task_summary(task_id) or {}
    
    def get_performance_summary(self, hours: int = 24) -> dict:
        """Get performance summary for recent operations"""
        return self.metrics_collector.get_performance_summary(hours)
    
    def get_system_health(self) -> dict:
        """Get current system health status"""
        return self.metrics_collector.get_system_health()
    
    def complete_experiment(self, success: bool = True):
        """Complete current experiment if running"""
        if self.experiment_tracker.current_run:
            self.experiment_tracker.complete_run(success=success)
    
    def cleanup(self):
        """Cleanup resources"""
        if self.browser:
            # self.browser.close()  # Would close browser in production
            pass
        
        # Complete any running experiment
        self.complete_experiment()


def demo_integration():
    """Demonstrate the MLOps integration with Browser.AI agent"""
    
    print("🔗 Browser.AI Agent MLOps Integration Demo")
    print("=" * 60)
    
    # Initialize MLOps-integrated agent
    agent = MLOpsIntegratedAgent(
        config_environment="development",
        experiment_name="Production_Integration_Test"
    )
    
    # Run several browser automation tasks
    tasks = [
        "Navigate to google.com and search for 'browser automation'",
        "Go to example.com and take a screenshot",
        "Visit news.ycombinator.com and get the top story title"
    ]
    
    results = []
    
    for i, task in enumerate(tasks, 1):
        print(f"\n📋 Task {i}: {task}")
        
        result = agent.run_task(
            task_description=task,
            max_steps=10,
            session_id="demo_session"
        )
        
        results.append(result)
        
        # Print task results
        print(f"   {'✅' if result['success'] else '❌'} Status: {'Success' if result['success'] else 'Failed'}")
        print(f"   ⏱️ Time: {result['completion_time']:.1f}s")
        print(f"   🔢 Steps: {result['steps_taken']}")
        
        if result.get('error'):
            print(f"   ❌ Error: {result['error']}")
    
    # Show overall performance
    print(f"\n📊 Performance Summary:")
    summary = agent.get_performance_summary(hours=1)
    
    print(f"   Total Tasks: {summary.get('total_tasks', 0)}")
    print(f"   Success Rate: {summary.get('success_rate', 0):.2%}")
    print(f"   Avg Duration: {summary.get('avg_task_duration', 0):.1f}s")
    print(f"   LLM Calls: {summary.get('llm_usage', {}).get('total_calls', 0)}")
    
    # Show system health
    print(f"\n🏥 System Health:")
    health = agent.get_system_health()
    print(f"   Status: {health.get('status', 'unknown')}")
    print(f"   CPU: {health.get('cpu_percent', 0):.1f}%")
    print(f"   Memory: {health.get('memory_percent', 0):.1f}%")
    
    # Complete experiment and cleanup
    agent.complete_experiment(success=all(r['success'] for r in results))
    agent.cleanup()
    
    print(f"\n✅ Integration demo complete!")
    print(f"   Successful tasks: {sum(1 for r in results if r['success'])}/{len(results)}")
    
    return results


if __name__ == "__main__":
    try:
        demo_integration()
    except Exception as e:
        print(f"❌ Integration demo failed: {e}")
        import traceback
        traceback.print_exc()