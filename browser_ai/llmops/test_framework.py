"""
LLMOps Testing Framework for Browser.AI

This module provides comprehensive testing capabilities for Browser.AI workflows,
including evaluation of agent performance, task completion rates, and quality metrics.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime
from pathlib import Path

from browser_ai.llmops.opik_integration import OpikConfig, OpikLLMOps

logger = logging.getLogger(__name__)

class TestScenario:
    """Represents a single test scenario for Browser.AI automation"""
    
    def __init__(
        self,
        name: str,
        task_description: str,
        expected_outcome: Optional[str] = None,
        success_criteria: Optional[List[str]] = None,
        max_steps: int = 50,
        timeout_seconds: int = 300,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.task_description = task_description
        self.expected_outcome = expected_outcome
        self.success_criteria = success_criteria or []
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds
        self.metadata = metadata or {}

class TestResult:
    """Represents the result of a test scenario execution"""
    
    def __init__(
        self,
        scenario: TestScenario,
        success: bool,
        duration_seconds: float,
        steps_taken: int,
        extracted_content: str = "",
        error_message: Optional[str] = None,
        evaluation_scores: Optional[Dict[str, float]] = None,
        agent_history: Optional[Any] = None
    ):
        self.scenario = scenario
        self.success = success
        self.duration_seconds = duration_seconds
        self.steps_taken = steps_taken
        self.extracted_content = extracted_content
        self.error_message = error_message
        self.evaluation_scores = evaluation_scores or {}
        self.agent_history = agent_history
        self.timestamp = datetime.utcnow().isoformat()

class BrowserAITestSuite:
    """Test suite for evaluating Browser.AI workflows"""
    
    def __init__(
        self,
        opik_config: Optional[OpikConfig] = None,
        results_dir: str = "./test_results"
    ):
        self.opik_llmops = OpikLLMOps(opik_config) if opik_config else None
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.scenarios: List[TestScenario] = []
        self.results: List[TestResult] = []
        
    def add_scenario(self, scenario: TestScenario):
        """Add a test scenario to the suite"""
        self.scenarios.append(scenario)
        logger.info(f"Added test scenario: {scenario.name}")
        
    def add_scenarios_from_file(self, file_path: str):
        """Load test scenarios from a JSON file"""
        with open(file_path, 'r') as f:
            scenarios_data = json.load(f)
            
        for scenario_data in scenarios_data:
            scenario = TestScenario(
                name=scenario_data["name"],
                task_description=scenario_data["task_description"],
                expected_outcome=scenario_data.get("expected_outcome"),
                success_criteria=scenario_data.get("success_criteria", []),
                max_steps=scenario_data.get("max_steps", 50),
                timeout_seconds=scenario_data.get("timeout_seconds", 300),
                metadata=scenario_data.get("metadata", {})
            )
            self.add_scenario(scenario)
            
    async def run_scenario(
        self,
        scenario: TestScenario,
        agent_factory: Callable[[str], Any],  # Function that creates an agent for the task
        **agent_kwargs
    ) -> TestResult:
        """Run a single test scenario"""
        logger.info(f"Running test scenario: {scenario.name}")
        
        start_time = time.time()
        try:
            # Create agent for this scenario
            agent = agent_factory(scenario.task_description, **agent_kwargs)
            
            # Run the agent with timeout
            result = await asyncio.wait_for(
                agent.run(max_steps=scenario.max_steps),
                timeout=scenario.timeout_seconds
            )
            
            duration = time.time() - start_time
            
            # Evaluate the result
            success = self._evaluate_scenario_success(scenario, result)
            
            # Extract content and error information
            extracted_content = ""
            error_message = None
            
            if result.history:
                last_step = result.history[-1]
                if hasattr(last_step, 'result'):
                    if hasattr(last_step.result, 'extracted_content'):
                        extracted_content = str(last_step.result.extracted_content)
                    if hasattr(last_step.result, 'error'):
                        error_message = last_step.result.error
            
            # Get evaluation scores from Opik if available
            evaluation_scores = {}
            if self.opik_llmops:
                evaluation_scores = self.opik_llmops.evaluator.evaluate_task_completion(
                    task_description=scenario.task_description,
                    agent_output=result.history[-1].result if result.history else None,
                    expected_outcome=scenario.expected_outcome,
                    success_criteria=scenario.success_criteria
                )
            
            test_result = TestResult(
                scenario=scenario,
                success=success,
                duration_seconds=duration,
                steps_taken=len(result.history),
                extracted_content=extracted_content,
                error_message=error_message,
                evaluation_scores=evaluation_scores,
                agent_history=result
            )
            
            logger.info(f"Scenario '{scenario.name}' completed - Success: {success}, Duration: {duration:.2f}s")
            return test_result
            
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            test_result = TestResult(
                scenario=scenario,
                success=False,
                duration_seconds=duration,
                steps_taken=0,
                error_message=f"Test timed out after {scenario.timeout_seconds} seconds"
            )
            logger.warning(f"Scenario '{scenario.name}' timed out")
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = TestResult(
                scenario=scenario,
                success=False,
                duration_seconds=duration,
                steps_taken=0,
                error_message=str(e)
            )
            logger.error(f"Scenario '{scenario.name}' failed with error: {e}")
            return test_result
    
    def _evaluate_scenario_success(self, scenario: TestScenario, agent_result: Any) -> bool:
        """Evaluate if a scenario was successful"""
        
        # Check if agent completed successfully
        if not agent_result.history:
            return False
            
        last_step = agent_result.history[-1]
        if not hasattr(last_step, 'result'):
            return False
            
        result = last_step.result
        
        # Check if task was marked as done
        if hasattr(result, 'is_done') and not result.is_done:
            return False
            
        # Check if there were errors
        if hasattr(result, 'error') and result.error:
            return False
            
        # Check success criteria if provided
        if scenario.success_criteria and hasattr(result, 'extracted_content'):
            content = str(result.extracted_content).lower()
            for criterion in scenario.success_criteria:
                if criterion.lower() not in content:
                    return False
                    
        return True
    
    async def run_all_scenarios(
        self,
        agent_factory: Callable[[str], Any],
        **agent_kwargs
    ) -> List[TestResult]:
        """Run all test scenarios in the suite"""
        logger.info(f"Running {len(self.scenarios)} test scenarios")
        
        results = []
        for scenario in self.scenarios:
            result = await self.run_scenario(scenario, agent_factory, **agent_kwargs)
            results.append(result)
            self.results.append(result)
            
        self._save_results(results)
        return results
    
    def _save_results(self, results: List[TestResult]):
        """Save test results to file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        results_file = self.results_dir / f"test_results_{timestamp}.json"
        
        results_data = []
        for result in results:
            result_data = {
                "scenario_name": result.scenario.name,
                "task_description": result.scenario.task_description,
                "success": result.success,
                "duration_seconds": result.duration_seconds,
                "steps_taken": result.steps_taken,
                "extracted_content": result.extracted_content,
                "error_message": result.error_message,
                "evaluation_scores": result.evaluation_scores,
                "timestamp": result.timestamp,
                "scenario_metadata": result.scenario.metadata
            }
            results_data.append(result_data)
            
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
            
        logger.info(f"Test results saved to {results_file}")
    
    def generate_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """Generate a comprehensive test report"""
        total_scenarios = len(results)
        successful_scenarios = sum(1 for r in results if r.success)
        failed_scenarios = total_scenarios - successful_scenarios
        
        success_rate = successful_scenarios / total_scenarios if total_scenarios > 0 else 0
        
        total_duration = sum(r.duration_seconds for r in results)
        average_duration = total_duration / total_scenarios if total_scenarios > 0 else 0
        
        total_steps = sum(r.steps_taken for r in results)
        average_steps = total_steps / total_scenarios if total_scenarios > 0 else 0
        
        # Aggregate evaluation scores if available
        aggregated_scores = {}
        score_counts = {}
        
        for result in results:
            for score_name, score_value in result.evaluation_scores.items():
                if score_name not in aggregated_scores:
                    aggregated_scores[score_name] = 0
                    score_counts[score_name] = 0
                aggregated_scores[score_name] += score_value
                score_counts[score_name] += 1
        
        for score_name in aggregated_scores:
            aggregated_scores[score_name] /= score_counts[score_name]
        
        report = {
            "summary": {
                "total_scenarios": total_scenarios,
                "successful_scenarios": successful_scenarios,
                "failed_scenarios": failed_scenarios,
                "success_rate": success_rate,
                "total_duration_seconds": total_duration,
                "average_duration_seconds": average_duration,
                "total_steps": total_steps,
                "average_steps_per_scenario": average_steps
            },
            "evaluation_scores": aggregated_scores,
            "failed_scenarios": [
                {
                    "name": r.scenario.name,
                    "error": r.error_message,
                    "duration": r.duration_seconds
                }
                for r in results if not r.success
            ],
            "performance_metrics": {
                "fastest_scenario": min(results, key=lambda r: r.duration_seconds).scenario.name if results else None,
                "slowest_scenario": max(results, key=lambda r: r.duration_seconds).scenario.name if results else None,
                "most_steps": max(results, key=lambda r: r.steps_taken).scenario.name if results else None,
                "least_steps": min(results, key=lambda r: r.steps_taken).scenario.name if results else None,
            }
        }
        
        return report
    
    def print_report(self, results: List[TestResult]):
        """Print a formatted test report to console"""
        report = self.generate_report(results)
        
        print("\n" + "="*80)
        print("BROWSER.AI LLMOPS TEST REPORT")
        print("="*80)
        
        summary = report["summary"]
        print(f"\n📊 SUMMARY")
        print(f"   Total Scenarios: {summary['total_scenarios']}")
        print(f"   Successful: {summary['successful_scenarios']} ({summary['success_rate']:.1%})")
        print(f"   Failed: {summary['failed_scenarios']}")
        print(f"   Average Duration: {summary['average_duration_seconds']:.2f}s")
        print(f"   Average Steps: {summary['average_steps_per_scenario']:.1f}")
        
        if report["evaluation_scores"]:
            print(f"\n📈 EVALUATION SCORES")
            for score_name, score_value in report["evaluation_scores"].items():
                print(f"   {score_name}: {score_value:.3f}")
        
        if report["failed_scenarios"]:
            print(f"\n❌ FAILED SCENARIOS")
            for failed in report["failed_scenarios"]:
                print(f"   • {failed['name']}: {failed['error']}")
        
        performance = report["performance_metrics"]
        print(f"\n⚡ PERFORMANCE")
        print(f"   Fastest: {performance['fastest_scenario']}")
        print(f"   Slowest: {performance['slowest_scenario']}")
        print(f"   Most Steps: {performance['most_steps']}")
        print(f"   Least Steps: {performance['least_steps']}")
        
        print("\n" + "="*80)

def create_sample_scenarios() -> List[TestScenario]:
    """Create sample test scenarios for Browser.AI"""
    return [
        TestScenario(
            name="google_search_basic",
            task_description="Go to Google and search for 'OpenAI'",
            success_criteria=["openai", "results"],
            max_steps=10
        ),
        TestScenario(
            name="wikipedia_navigation",
            task_description="Navigate to Wikipedia and search for 'Machine Learning', then click on the first result",
            success_criteria=["machine learning", "wikipedia"],
            max_steps=15
        ),
        TestScenario(
            name="form_filling",
            task_description="Go to a contact form and fill it with name 'Test User' and email 'test@example.com'",
            success_criteria=["test user", "test@example.com"],
            max_steps=20
        )
    ]