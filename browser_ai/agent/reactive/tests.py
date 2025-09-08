"""
Simple tests for the reactive agents implementation.

These tests validate basic functionality without requiring external dependencies.
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any, Optional

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from browser_ai.agent.reactive.base_reactive import BaseReactiveAgent, ReactiveEvent, ReactiveState
from browser_ai.agent.views import AgentOutput, ActionResult


class MockLLM:
    """Mock LLM for testing"""
    def __init__(self):
        self.model_name = "mock-llm"
        self.__class__.__name__ = "MockLLM"
    
    async def ainvoke(self, messages):
        return Mock(content="Mock response")


class MockBrowserContext:
    """Mock browser context for testing"""
    
    def __init__(self):
        self.session = Mock()
    
    async def get_state(self):
        mock_state = Mock()
        mock_state.url = "https://example.com"
        mock_state.title = "Test Page"
        mock_state.element_tree = Mock()
        mock_state.element_tree.clickable_elements = []
        mock_state.screenshot = None
        return mock_state
    
    async def close(self):
        pass


class TestReactiveAgent(BaseReactiveAgent):
    """Test implementation of BaseReactiveAgent"""
    
    async def reactive_step(self, step_info: Optional[Dict[str, Any]] = None) -> AgentOutput:
        from browser_ai.agent.views import AgentBrain
        
        brain = AgentBrain(
            page_summary="Test page summary",
            evaluation_previous_goal="Success",
            memory="Test memory",
            next_goal="Test goal"
        )
        
        return self.AgentOutput(
            current_state=brain,
            action=[]
        )
    
    async def get_recovery_action(self, error: Exception, context: Dict[str, Any]) -> Optional[str]:
        return "retry"
    
    async def execute_recovery_action(self, action: str, error: Exception, context: Dict[str, Any]) -> None:
        pass


class TestReactiveAgents:
    """Test cases for reactive agents"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.mock_llm = MockLLM()
        self.mock_browser_context = MockBrowserContext()
    
    async def test_base_reactive_agent_initialization(self):
        """Test BaseReactiveAgent initialization"""
        
        agent = TestReactiveAgent(
            task="Test task",
            llm=self.mock_llm,
            browser_context=self.mock_browser_context,
            enable_event_system=True
        )
        
        assert agent.task == "Test task"
        assert agent.enable_event_system is True
        assert agent.auto_recovery is True
        assert agent._running is False
        assert len(agent._event_handlers) == 0
    
    async def test_event_system_lifecycle(self):
        """Test event system start/stop lifecycle"""
        
        agent = TestReactiveAgent(
            task="Test task",
            llm=self.mock_llm,
            browser_context=self.mock_browser_context,
            enable_event_system=True
        )
        
        # Start reactive system
        await agent.start_reactive_system()
        assert agent._running is True
        assert agent._reactive_state is not None
        
        # Stop reactive system
        await agent.stop_reactive_system()
        assert agent._running is False
    
    async def test_event_emission_and_processing(self):
        """Test event emission and processing"""
        
        agent = TestReactiveAgent(
            task="Test task",
            llm=self.mock_llm,
            browser_context=self.mock_browser_context,
            enable_event_system=True
        )
        
        # Start reactive system
        await agent.start_reactive_system()
        
        # Emit test event
        await agent.emit_event("test", "test_event", {"data": "test"})
        
        # Give event processing loop time to run
        await asyncio.sleep(0.1)
        
        # Check event was processed
        assert len(agent._reactive_state.event_history) > 0
        
        # Stop system
        await agent.stop_reactive_system()
    
    async def test_event_subscription(self):
        """Test event subscription and handling"""
        
        agent = TestReactiveAgent(
            task="Test task",
            llm=self.mock_llm,
            browser_context=self.mock_browser_context,
            enable_event_system=True
        )
        
        # Subscribe to events
        handled_events = []
        
        def event_handler(event):
            handled_events.append(event)
        
        agent.subscribe_to_event("test_event", event_handler)
        
        # Start system and emit event
        await agent.start_reactive_system()
        await agent.emit_event("test", "test_event", {"data": "test"})
        
        # Give processing time
        await asyncio.sleep(0.1)
        
        # Check event was handled
        assert len(handled_events) > 0
        assert handled_events[0].event_type == "test_event"
        
        await agent.stop_reactive_system()
    
    async def test_reactive_step_execution(self):
        """Test reactive step execution"""
        
        agent = TestReactiveAgent(
            task="Test task",
            llm=self.mock_llm,
            browser_context=self.mock_browser_context,
            enable_event_system=True
        )
        
        # Start system
        await agent.start_reactive_system()
        
        # Execute reactive step
        output = await agent.reactive_step({"test": "data"})
        
        # Verify output
        assert output is not None
        assert output.current_state.page_summary == "Test page summary"
        assert output.current_state.next_goal == "Test goal"
        
        await agent.stop_reactive_system()
    
    async def test_error_recovery(self):
        """Test error recovery functionality"""
        
        agent = TestReactiveAgent(
            task="Test task", 
            llm=self.mock_llm,
            browser_context=self.mock_browser_context,
            auto_recovery=True
        )
        
        # Test recovery action determination
        recovery_action = await agent.get_recovery_action(
            ValueError("Test error"),
            {"context": "test"}
        )
        
        assert recovery_action == "retry"
        
        # Test recovery execution
        await agent.execute_recovery_action(
            "retry",
            ValueError("Test error"),
            {"context": "test"}
        )
        # Should complete without error
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        
        agent = TestReactiveAgent(
            task="Test task",
            llm=self.mock_llm,
            browser_context=self.mock_browser_context
        )
        
        metrics = agent.get_metrics()
        
        assert "events_processed" in metrics
        assert "state_changes" in metrics
        assert "recovery_actions" in metrics
        assert "reactive_state" in metrics
    
    async def test_disabled_event_system(self):
        """Test behavior when event system is disabled"""
        
        agent = TestReactiveAgent(
            task="Test task",
            llm=self.mock_llm,
            browser_context=self.mock_browser_context,
            enable_event_system=False
        )
        
        # Start system (should do nothing)
        await agent.start_reactive_system()
        assert agent._running is False
        
        # Emit event (should do nothing)
        await agent.emit_event("test", "test_event", {})
        # Should complete without error


def test_reactive_event_creation():
    """Test ReactiveEvent model"""
    
    event = ReactiveEvent(
        event_type="test",
        event_data={"key": "value"},
        timestamp=123456.789,
        source="test_source",
        priority=1
    )
    
    assert event.event_type == "test"
    assert event.event_data["key"] == "value"
    assert event.timestamp == 123456.789
    assert event.source == "test_source"
    assert event.priority == 1


def test_reactive_state_creation():
    """Test ReactiveState model"""
    
    mock_browser_state = Mock()
    mock_browser_state.url = "https://example.com"
    
    state = ReactiveState(
        current_state=mock_browser_state,
        event_history=[],
        active_listeners={},
        state_changes=[]
    )
    
    assert state.current_state == mock_browser_state
    assert len(state.event_history) == 0
    assert len(state.active_listeners) == 0
    assert len(state.state_changes) == 0


if __name__ == "__main__":
    print("Running reactive agents tests...")
    
    # Create test instance
    test_class = TestReactiveAgents()
    test_class.setup_method()
    
    # Run async tests manually
    async def run_tests():
        try:
            print("Testing agent initialization...")
            await test_class.test_base_reactive_agent_initialization()
            print("✓ Agent initialization test passed")
            
            print("Testing event system lifecycle...")
            await test_class.test_event_system_lifecycle()
            print("✓ Event system lifecycle test passed")
            
            print("Testing event emission...")
            await test_class.test_event_emission_and_processing()
            print("✓ Event emission test passed")
            
            print("Testing event subscription...")
            await test_class.test_event_subscription()
            print("✓ Event subscription test passed")
            
            print("Testing reactive step...")
            await test_class.test_reactive_step_execution()
            print("✓ Reactive step test passed")
            
            print("Testing error recovery...")
            await test_class.test_error_recovery()
            print("✓ Error recovery test passed")
            
            print("Testing disabled event system...")
            await test_class.test_disabled_event_system()
            print("✓ Disabled event system test passed")
            
            print("Testing metrics...")
            test_class.test_metrics_collection()
            print("✓ Metrics test passed")
            
            print("Testing reactive event creation...")
            test_reactive_event_creation()
            print("✓ ReactiveEvent test passed")
            
            print("Testing reactive state creation...")
            test_reactive_state_creation()
            print("✓ ReactiveState test passed")
            
            print("\n🎉 All tests passed! ✓")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    # Run the tests
    success = asyncio.run(run_tests())
    if not success:
        exit(1)