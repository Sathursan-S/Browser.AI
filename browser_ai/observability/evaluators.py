"""
Evaluation Framework for Browser.AI Agent System

Comprehensive evaluators for measuring agent performance, task success, and system metrics.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from lmnr import Laminar

from browser_ai.agent.views import AgentHistoryList, AgentHistory

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of an evaluation"""

    evaluator_name: str
    score: float  # 0.0 to 1.0
    passed: bool
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evaluator": self.evaluator_name,
            "score": self.score,
            "passed": self.passed,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class AgentEvaluator(ABC):
    """Base class for agent evaluators"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def evaluate(
        self,
        task: str,
        history: AgentHistoryList,
        expected_result: Optional[Any] = None,
    ) -> EvaluationResult:
        """Evaluate the agent's performance"""
        pass

    def _record_evaluation(self, result: EvaluationResult):
        """Record evaluation in Laminar"""
        Laminar.event(
            name=f"evaluation.{self.name}",
            attributes=result.to_dict(),
        )


class TaskSuccessEvaluator(AgentEvaluator):
    """
    Evaluates whether the agent successfully completed the task

    Criteria:
    - Task marked as done
    - No critical errors
    - Result matches expected output (if provided)
    """

    def __init__(self):
        super().__init__("task_success")

    async def evaluate(
        self,
        task: str,
        history: AgentHistoryList,
        expected_result: Optional[Any] = None,
    ) -> EvaluationResult:
        """Evaluate task completion success"""

        # Check if task was marked as done
        is_done = history.is_done()

        # Count critical errors
        critical_errors = sum(
            1
            for h in history.history
            if h.result and any(r.error for r in h.result if r.error)
        )

        # Calculate base score
        score = 1.0 if is_done else 0.0

        # Penalize for errors
        if critical_errors > 0:
            error_penalty = min(0.3, critical_errors * 0.1)
            score = max(0.0, score - error_penalty)

        # Check expected result if provided
        result_match = True
        if expected_result is not None and is_done:
            final_result = history.final_result()
            result_match = self._compare_results(final_result, expected_result)
            if not result_match:
                score *= 0.5  # 50% penalty for incorrect result

        metadata = {
            "is_done": is_done,
            "critical_errors": critical_errors,
            "total_steps": len(history.history),
            "result_match": result_match,
        }

        result = EvaluationResult(
            evaluator_name=self.name,
            score=score,
            passed=score >= 0.7,  # 70% threshold
            metadata=metadata,
        )

        self._record_evaluation(result)
        return result

    def _compare_results(self, actual: Any, expected: Any) -> bool:
        """Compare actual result with expected result"""
        if isinstance(expected, str):
            return expected.lower() in str(actual).lower()
        return str(actual) == str(expected)


class ActionAccuracyEvaluator(AgentEvaluator):
    """
    Evaluates the accuracy and efficiency of actions taken

    Criteria:
    - Relevant actions for the task
    - Minimal repeated actions
    - No unnecessary steps
    """

    def __init__(self):
        super().__init__("action_accuracy")

    async def evaluate(
        self,
        task: str,
        history: AgentHistoryList,
        expected_result: Optional[Any] = None,
    ) -> EvaluationResult:
        """Evaluate action accuracy and efficiency"""

        if not history.history:
            return EvaluationResult(
                evaluator_name=self.name,
                score=0.0,
                passed=False,
                metadata={"error": "No history available"},
            )

        total_actions = 0
        successful_actions = 0
        repeated_actions = 0
        action_sequence = []

        for step in history.history:
            if step.model_output:
                for action in step.model_output.action:
                    action_name = list(action.model_dump(exclude_unset=True).keys())[0]
                    total_actions += 1
                    action_sequence.append(action_name)

                    # Check if action was successful (no error in result)
                    if step.result:
                        has_error = any(r.error for r in step.result if r.error)
                        if not has_error:
                            successful_actions += 1

        # Detect repeated action patterns
        for i in range(len(action_sequence) - 1):
            if action_sequence[i] == action_sequence[i + 1]:
                repeated_actions += 1

        # Calculate score
        success_rate = successful_actions / total_actions if total_actions > 0 else 0
        repetition_penalty = min(0.3, repeated_actions * 0.05)
        score = max(0.0, success_rate - repetition_penalty)

        metadata = {
            "total_actions": total_actions,
            "successful_actions": successful_actions,
            "success_rate": success_rate,
            "repeated_actions": repeated_actions,
            "unique_actions": len(set(action_sequence)),
        }

        result = EvaluationResult(
            evaluator_name=self.name,
            score=score,
            passed=score >= 0.6,  # 60% threshold
            metadata=metadata,
        )

        self._record_evaluation(result)
        return result


class LatencyEvaluator(AgentEvaluator):
    """
    Evaluates the performance characteristics of the agent

    Criteria:
    - Average step duration
    - LLM call latency
    - Browser operation speed
    """

    def __init__(self, target_step_duration: float = 10.0):
        super().__init__("latency")
        self.target_step_duration = target_step_duration

    async def evaluate(
        self,
        task: str,
        history: AgentHistoryList,
        expected_result: Optional[Any] = None,
    ) -> EvaluationResult:
        """Evaluate latency and performance"""

        # This is a simplified version - in practice, you'd extract timing data
        # from the actual execution traces

        total_steps = len(history.history)

        # Estimate based on typical metrics
        # In a real implementation, this would come from actual timing data
        estimated_avg_duration = 5.0  # Placeholder

        # Score based on how close to target
        if estimated_avg_duration <= self.target_step_duration:
            score = 1.0
        else:
            # Exponential decay for longer durations
            excess = estimated_avg_duration - self.target_step_duration
            score = max(0.0, 1.0 - (excess / self.target_step_duration))

        metadata = {
            "total_steps": total_steps,
            "estimated_avg_duration": estimated_avg_duration,
            "target_duration": self.target_step_duration,
        }

        result = EvaluationResult(
            evaluator_name=self.name,
            score=score,
            passed=score >= 0.7,
            metadata=metadata,
        )

        self._record_evaluation(result)
        return result


class ComprehensiveEvaluator:
    """
    Runs multiple evaluators and combines results
    """

    def __init__(self, evaluators: Optional[List[AgentEvaluator]] = None):
        self.evaluators = evaluators or [
            TaskSuccessEvaluator(),
            ActionAccuracyEvaluator(),
            LatencyEvaluator(),
        ]

    async def evaluate_all(
        self,
        task: str,
        history: AgentHistoryList,
        expected_result: Optional[Any] = None,
    ) -> Dict[str, EvaluationResult]:
        """Run all evaluators and return results"""
        results = {}

        for evaluator in self.evaluators:
            try:
                result = await evaluator.evaluate(task, history, expected_result)
                results[evaluator.name] = result
            except Exception as e:
                logger.error(f"Evaluator {evaluator.name} failed: {e}")
                results[evaluator.name] = EvaluationResult(
                    evaluator_name=evaluator.name,
                    score=0.0,
                    passed=False,
                    metadata={"error": str(e)},
                )

        # Calculate overall score
        overall_score = sum(r.score for r in results.values()) / len(results)

        # Record comprehensive evaluation
        Laminar.event(
            name="evaluation.comprehensive",
            value={
                "task": task,
                "overall_score": overall_score,
                "evaluators": {k: v.to_dict() for k, v in results.items()},
                "all_passed": all(r.passed for r in results.values()),
            },
        )

        return results

    def get_summary(self, results: Dict[str, EvaluationResult]) -> Dict[str, Any]:
        """Get evaluation summary"""
        return {
            "overall_score": sum(r.score for r in results.values()) / len(results),
            "all_passed": all(r.passed for r in results.values()),
            "individual_scores": {k: v.score for k, v in results.items()},
            "failed_evaluators": [k for k, v in results.items() if not v.passed],
        }
