"""
LLMOps module for Browser.AI

This module provides comprehensive LLMOps capabilities including:
- Evaluation of LLM performance and task completion
- Testing workflows and automation scenarios  
- Monitoring of agent execution and metrics
- Integration with observability platforms (LMNR, Opik)
"""

from .opik_integration import OpikConfig, OpikLLMOps, OpikTracer, OpikEvaluator, OpikMonitor
from .test_framework import BrowserAITestSuite, TestScenario, TestResult, create_sample_scenarios

__all__ = [
    'OpikConfig',
    'OpikLLMOps', 
    'OpikTracer',
    'OpikEvaluator',
    'OpikMonitor',
    'BrowserAITestSuite',
    'TestScenario',
    'TestResult',
    'create_sample_scenarios'
]