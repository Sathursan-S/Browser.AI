"""
MLOps framework for Browser.AI

This module provides MLOps capabilities for the Browser.AI project including:
- Experiment tracking
- Model management and registry
- Performance monitoring
- Data versioning
- Model evaluation metrics
"""

from .experiment_tracker import ExperimentTracker
from .model_registry import ModelRegistry
from .metrics import MetricsCollector
from .evaluator import ModelEvaluator

__version__ = "1.0.0"
__all__ = [
    "ExperimentTracker",
    "ModelRegistry", 
    "MetricsCollector",
    "ModelEvaluator"
]