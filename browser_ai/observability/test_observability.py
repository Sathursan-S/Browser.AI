"""
Tests for Browser.AI Observability Module
"""

import asyncio
import pytest
from unittest.mock import MagicMock

from browser_ai.observability import (
    PromptManager,
    PromptType,
    PromptVersion,
    TaskSuccessEvaluator,
    ActionAccuracyEvaluator,
    MetricsCollector,
)
from browser_ai.agent.views import AgentHistoryList


class TestPromptManager:
    """Test prompt management"""

    def test_register_prompt(self):
        pm = PromptManager()

        prompt = pm.register_prompt(
            prompt_id="test_prompt",
            version="1.0.0",
            prompt_type=PromptType.SYSTEM,
            template="Hello {name}",
            variables=["name"],
        )

        assert isinstance(prompt, PromptVersion)
        assert prompt.prompt_id == "test_prompt"
        assert prompt.version == "1.0.0"

    def test_render_prompt(self):
        pm = PromptManager()

        pm.register_prompt(
            prompt_id="greeting",
            version="1.0.0",
            prompt_type=PromptType.SYSTEM,
            template="Hello {name}, you are {age} years old",
            variables=["name", "age"],
        )

        rendered = pm.render_prompt(
            prompt_id="greeting",
            name="Alice",
            age=30,
        )

        assert rendered == "Hello Alice, you are 30 years old"

    def test_missing_variable_raises_error(self):
        pm = PromptManager()

        pm.register_prompt(
            prompt_id="test",
            version="1.0.0",
            prompt_type=PromptType.SYSTEM,
            template="Hello {name}",
            variables=["name"],
        )

        with pytest.raises(ValueError, match="Missing required variable"):
            pm.render_prompt(prompt_id="test")

    def test_get_latest_version(self):
        pm = PromptManager()

        pm.register_prompt(
            prompt_id="versioned",
            version="1.0.0",
            prompt_type=PromptType.SYSTEM,
            template="V1",
            variables=[],
        )

        pm.register_prompt(
            prompt_id="versioned",
            version="2.0.0",
            prompt_type=PromptType.SYSTEM,
            template="V2",
            variables=[],
        )

        latest = pm.get_prompt("versioned")
        assert latest.version == "2.0.0"

    def test_activate_version(self):
        pm = PromptManager()

        pm.register_prompt(
            prompt_id="test",
            version="1.0.0",
            prompt_type=PromptType.SYSTEM,
            template="V1",
            variables=[],
        )

        pm.register_prompt(
            prompt_id="test",
            version="2.0.0",
            prompt_type=PromptType.SYSTEM,
            template="V2",
            variables=[],
            is_active=False,
        )

        # Activate v2.0.0
        pm.activate_version("test", "2.0.0")

        # Get should return v2.0.0 now
        latest = pm.get_prompt("test")
        assert latest.version == "2.0.0"


class TestMetricsCollector:
    """Test metrics collection"""

    def test_start_session(self):
        mc = MetricsCollector()

        metrics = mc.start_session(
            task="Test task",
            session_id="session-1",
        )

        assert metrics.task == "Test task"
        assert metrics.session_id == "session-1"
        assert metrics.total_steps == 0

    def test_record_action(self):
        mc = MetricsCollector()
        mc.start_session("Test", "session-1")

        mc.record_action("session-1", "search_google", success=True)
        mc.record_action("session-1", "search_google", success=True)
        mc.record_action("session-1", "click_element", success=True)

        metrics = mc.get_session_metrics("session-1")
        assert metrics.total_actions == 3
        assert metrics.action_breakdown["search_google"] == 2
        assert metrics.action_breakdown["click_element"] == 1

    def test_complete_session(self):
        mc = MetricsCollector()
        mc.start_session("Test", "session-1")

        # Add some data
        mc.record_action("session-1", "search", success=True)

        # Complete
        final = mc.complete_session("session-1", successful=True)

        assert final.successful is True
        assert final.completed_at is not None
        assert "session-1" not in mc.active_sessions
        assert len(mc.completed_sessions) == 1


class TestEvaluators:
    """Test evaluation framework"""

    @pytest.mark.asyncio
    async def test_task_success_evaluator(self):
        evaluator = TaskSuccessEvaluator()

        # Create mock history
        history = MagicMock(spec=AgentHistoryList)
        history.is_done.return_value = True
        history.history = []
        history.final_result.return_value = "Success"

        result = await evaluator.evaluate(
            task="Test task",
            history=history,
        )

        assert result.score > 0
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_action_accuracy_evaluator(self):
        evaluator = ActionAccuracyEvaluator()

        # Create mock history
        history = MagicMock(spec=AgentHistoryList)
        history.history = []

        result = await evaluator.evaluate(
            task="Test task",
            history=history,
        )

        # Should fail with no history
        assert result.score == 0.0
        assert result.passed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
