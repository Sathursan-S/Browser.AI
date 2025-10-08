#!/usr/bin/env python3
"""
Simple test script to verify Opik LLMOps integration works correctly
"""

import asyncio
import logging
from browser_ai.llmops import OpikConfig, OpikLLMOps, BrowserAITestSuite, TestScenario

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_opik_config():
    """Test OpikConfig creation and configuration"""
    logger.info("Testing OpikConfig...")
    
    config = OpikConfig(
        project_name="test-project",
        enabled=True,
        tags=["test", "integration"]
    )
    
    assert config.project_name == "test-project"
    assert config.enabled == True
    assert "test" in config.tags
    
    logger.info("✅ OpikConfig test passed")

def test_opik_llmops():
    """Test OpikLLMOps functionality"""
    logger.info("Testing OpikLLMOps...")
    
    config = OpikConfig(project_name="test", enabled=True)
    llmops = OpikLLMOps(config)
    
    # Test tracer
    trace_id = llmops.tracer.start_trace("test_trace", {"input": "test"})
    assert trace_id != ""
    
    llmops.tracer.log_span("test_span", {"action": "test"}, {"result": "success"})
    llmops.tracer.end_trace(trace_id, {"output": "test_complete"})
    
    # Test evaluator
    scores = llmops.evaluator.evaluate_step_efficiency(1, "test_action", 100.0, True)
    assert "step_success" in scores
    assert scores["step_success"] == 1.0
    
    # Test monitor
    llmops.monitor.track_action_execution("test_action", True, 150.0)
    summary = llmops.monitor.get_summary_metrics()
    assert summary["total_actions"] == 1
    
    # Test data export
    export_data = llmops.export_data()
    assert "traces" in export_data
    assert "evaluations" in export_data
    assert "metrics_summary" in export_data
    
    logger.info("✅ OpikLLMOps test passed")

def test_test_framework():
    """Test the testing framework"""
    logger.info("Testing BrowserAITestSuite...")
    
    config = OpikConfig(project_name="test-suite", enabled=True)
    test_suite = BrowserAITestSuite(config, results_dir="/tmp/test_results")
    
    # Create test scenario
    scenario = TestScenario(
        name="test_scenario",
        task_description="Test task",
        success_criteria=["test", "success"],
        max_steps=5
    )
    
    test_suite.add_scenario(scenario)
    assert len(test_suite.scenarios) == 1
    assert test_suite.scenarios[0].name == "test_scenario"
    
    logger.info("✅ BrowserAITestSuite test passed")

class MockAgentResult:
    """Mock agent result for testing"""
    def __init__(self, is_done=True, error=None, extracted_content="test content"):
        self.is_done = is_done
        self.error = error
        self.extracted_content = extracted_content

class MockAgentHistory:
    """Mock agent history for testing"""
    def __init__(self, result):
        self.result = result

class MockAgentHistoryList:
    """Mock agent history list for testing"""
    def __init__(self, results):
        self.history = [MockAgentHistory(result) for result in results]

def test_evaluation():
    """Test evaluation functionality"""
    logger.info("Testing evaluation...")
    
    config = OpikConfig(project_name="test-eval", enabled=True)
    llmops = OpikLLMOps(config)
    
    # Test successful task evaluation
    mock_result = MockAgentResult(is_done=True, error=None, extracted_content="test success content")
    scores = llmops.evaluator.evaluate_task_completion(
        "Test task",
        mock_result,
        success_criteria=["test", "success"]
    )
    
    assert scores["task_completed"] == 1.0
    assert scores["error_free"] == 1.0
    assert scores["criteria_fulfillment"] == 1.0  # Both "test" and "success" found
    
    # Test failed task evaluation
    mock_result_failed = MockAgentResult(is_done=False, error="Test error", extracted_content="failure")
    scores_failed = llmops.evaluator.evaluate_task_completion(
        "Test task",
        mock_result_failed,
        success_criteria=["test", "success"]
    )
    
    assert scores_failed["task_completed"] == 0.0
    assert scores_failed["error_free"] == 0.0
    
    logger.info("✅ Evaluation test passed")

def test_disabled_config():
    """Test behavior when Opik is disabled"""
    logger.info("Testing disabled configuration...")
    
    config = OpikConfig(project_name="test", enabled=False)
    llmops = OpikLLMOps(config)
    
    # Operations should not crash when disabled
    trace_id = llmops.tracer.start_trace("test", {})
    assert trace_id == ""
    
    llmops.tracer.end_trace("fake_id", {})
    llmops.monitor.track_action_execution("test", True, 100.0)
    
    scores = llmops.evaluator.evaluate_task_completion("test", MockAgentResult())
    assert scores == {}
    
    export_data = llmops.export_data()
    assert export_data == {}
    
    logger.info("✅ Disabled configuration test passed")

def main():
    """Run all tests"""
    logger.info("Starting Opik LLMOps integration tests...")
    logger.info("=" * 50)
    
    try:
        test_opik_config()
        test_opik_llmops()
        test_test_framework()
        test_evaluation()
        test_disabled_config()
        
        logger.info("=" * 50)
        logger.info("🎉 All tests passed! Opik LLMOps integration is working correctly.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)