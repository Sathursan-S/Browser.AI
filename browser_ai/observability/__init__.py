"""
Browser.AI Observability Module

This module provides comprehensive observability for the Browser.AI agent system using Laminar.
Includes:
- Prompt management and versioning
- Evaluation framework for agent performance
- Metrics collection and analysis
- Trace utilities
"""

from browser_ai.observability.prompt_manager import PromptManager, PromptVersion
from browser_ai.observability.evaluators import (
    AgentEvaluator,
    TaskSuccessEvaluator,
    ActionAccuracyEvaluator,
    LatencyEvaluator,
)
from browser_ai.observability.metrics import MetricsCollector, AgentMetrics

__all__ = [
    "PromptManager",
    "PromptVersion",
    "AgentEvaluator",
    "TaskSuccessEvaluator",
    "ActionAccuracyEvaluator",
    "LatencyEvaluator",
    "MetricsCollector",
    "AgentMetrics",
]
