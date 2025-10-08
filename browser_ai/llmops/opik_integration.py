"""
Opik LLMOps integration for Browser.AI

This module provides evaluating, testing, and monitoring capabilities using Opik.
It works alongside the existing LMNR observability setup.
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Union
from functools import wraps
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class OpikConfig:
    """Configuration for Opik integration"""
    
    def __init__(
        self,
        project_name: str = "browser-ai",
        api_key: Optional[str] = None,
        workspace: Optional[str] = None,
        enabled: bool = True,
        tags: Optional[List[str]] = None
    ):
        self.project_name = project_name
        self.api_key = api_key
        self.workspace = workspace
        self.enabled = enabled
        self.tags = tags or []

class OpikTracer:
    """Opik tracer for monitoring agent execution"""
    
    def __init__(self, config: OpikConfig):
        self.config = config
        self.traces: List[Dict] = []
        self.active_trace: Optional[Dict] = None
        self.evaluations: List[Dict] = []
        
    def start_trace(
        self, 
        name: str, 
        input_data: Optional[Dict] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """Start a new trace"""
        if not self.config.enabled:
            return ""
            
        trace_id = str(uuid.uuid4())
        trace = {
            "id": trace_id,
            "name": name,
            "input": input_data or {},
            "metadata": metadata or {},
            "start_time": datetime.utcnow().isoformat(),
            "spans": [],
            "tags": self.config.tags.copy()
        }
        
        self.traces.append(trace)
        self.active_trace = trace
        
        logger.debug(f"Opik: Started trace '{name}' with ID {trace_id}")
        return trace_id
        
    def end_trace(
        self,
        trace_id: str,
        output_data: Optional[Dict] = None,
        feedback_scores: Optional[Dict[str, float]] = None
    ):
        """End a trace"""
        if not self.config.enabled:
            return
            
        trace = self._find_trace(trace_id)
        if trace:
            trace["output"] = output_data or {}
            trace["end_time"] = datetime.utcnow().isoformat()
            trace["feedback_scores"] = feedback_scores or {}
            
            # Calculate duration
            start = datetime.fromisoformat(trace["start_time"])
            end = datetime.fromisoformat(trace["end_time"])
            trace["duration_ms"] = int((end - start).total_seconds() * 1000)
            
            logger.debug(f"Opik: Ended trace {trace_id}")
            
            if trace == self.active_trace:
                self.active_trace = None
                
    def log_span(
        self,
        name: str,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        span_type: str = "general",
        trace_id: Optional[str] = None
    ):
        """Log a span within a trace"""
        if not self.config.enabled:
            return
            
        target_trace = self.active_trace
        if trace_id:
            target_trace = self._find_trace(trace_id)
            
        if target_trace:
            span = {
                "id": str(uuid.uuid4()),
                "name": name,
                "type": span_type,
                "input": input_data or {},
                "output": output_data or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            target_trace["spans"].append(span)
            logger.debug(f"Opik: Logged span '{name}' in trace {target_trace['id']}")
    
    def _find_trace(self, trace_id: str) -> Optional[Dict]:
        """Find trace by ID"""
        return next((trace for trace in self.traces if trace["id"] == trace_id), None)

class OpikEvaluator:
    """Opik evaluator for LLM performance evaluation"""
    
    def __init__(self, config: OpikConfig):
        self.config = config
        self.evaluation_results: List[Dict] = []
        
    def evaluate_task_completion(
        self,
        task_description: str,
        agent_output: Any,
        expected_outcome: Optional[str] = None,
        success_criteria: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """Evaluate if a task was completed successfully"""
        if not self.config.enabled:
            return {}
            
        scores = {}
        
        # Basic completion check
        if hasattr(agent_output, 'is_done'):
            scores["task_completed"] = 1.0 if agent_output.is_done else 0.0
        
        # Success criteria evaluation
        if success_criteria and hasattr(agent_output, 'extracted_content'):
            content = str(agent_output.extracted_content).lower()
            criteria_met = sum(1 for criterion in success_criteria 
                             if criterion.lower() in content)
            scores["criteria_fulfillment"] = criteria_met / len(success_criteria)
        
        # Error rate
        if hasattr(agent_output, 'error'):
            scores["error_free"] = 0.0 if agent_output.error else 1.0
        
        evaluation = {
            "id": str(uuid.uuid4()),
            "task_description": task_description,
            "expected_outcome": expected_outcome,
            "scores": scores,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": {
                "success_criteria": success_criteria,
                "agent_output_type": type(agent_output).__name__
            }
        }
        
        self.evaluation_results.append(evaluation)
        logger.info(f"Opik: Evaluated task with scores: {scores}")
        return scores
        
    def evaluate_step_efficiency(
        self,
        step_number: int,
        action_type: str,
        execution_time_ms: float,
        success: bool
    ) -> Dict[str, float]:
        """Evaluate efficiency of individual steps"""
        if not self.config.enabled:
            return {}
            
        scores = {
            "step_success": 1.0 if success else 0.0,
            "efficiency_score": max(0.0, 1.0 - (execution_time_ms / 10000.0))  # Penalty for slow steps
        }
        
        evaluation = {
            "id": str(uuid.uuid4()),
            "step_number": step_number,
            "action_type": action_type,
            "execution_time_ms": execution_time_ms,
            "scores": scores,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.evaluation_results.append(evaluation)
        return scores

class OpikMonitor:
    """Opik monitor for real-time LLM operations monitoring"""
    
    def __init__(self, config: OpikConfig):
        self.config = config
        self.metrics: Dict[str, List] = {
            "llm_calls": [],
            "action_executions": [],
            "errors": [],
            "performance": []
        }
        
    def track_llm_call(
        self,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost: Optional[float] = None,
        latency_ms: Optional[float] = None
    ):
        """Track LLM API calls"""
        if not self.config.enabled:
            return
            
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "model_name": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "cost": cost,
            "latency_ms": latency_ms
        }
        
        self.metrics["llm_calls"].append(metric)
        logger.debug(f"Opik: Tracked LLM call to {model_name}")
        
    def track_action_execution(
        self,
        action_name: str,
        success: bool,
        duration_ms: float,
        error_message: Optional[str] = None
    ):
        """Track action execution metrics"""
        if not self.config.enabled:
            return
            
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_name": action_name,
            "success": success,
            "duration_ms": duration_ms,
            "error_message": error_message
        }
        
        self.metrics["action_executions"].append(metric)
        
        if not success:
            self.metrics["errors"].append(metric)
            
        logger.debug(f"Opik: Tracked action execution '{action_name}' - {'success' if success else 'failed'}")
        
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics for monitoring"""
        if not self.config.enabled:
            return {}
            
        llm_calls = self.metrics["llm_calls"]
        actions = self.metrics["action_executions"]
        errors = self.metrics["errors"]
        
        summary = {
            "total_llm_calls": len(llm_calls),
            "total_tokens": sum(call.get("total_tokens", 0) for call in llm_calls),
            "total_cost": sum(call.get("cost", 0) for call in llm_calls if call.get("cost")),
            "average_llm_latency": (
                sum(call.get("latency_ms", 0) for call in llm_calls) / len(llm_calls)
                if llm_calls else 0
            ),
            "total_actions": len(actions),
            "successful_actions": len([a for a in actions if a["success"]]),
            "error_rate": len(errors) / len(actions) if actions else 0,
            "average_action_duration": (
                sum(action["duration_ms"] for action in actions) / len(actions)
                if actions else 0
            )
        }
        
        return summary

class OpikLLMOps:
    """Main Opik LLMOps integration class"""
    
    def __init__(self, config: Optional[OpikConfig] = None):
        self.config = config or OpikConfig()
        self.tracer = OpikTracer(self.config)
        self.evaluator = OpikEvaluator(self.config)
        self.monitor = OpikMonitor(self.config)
        
        if self.config.enabled:
            logger.info(f"Opik LLMOps initialized for project: {self.config.project_name}")
        else:
            logger.info("Opik LLMOps disabled")
    
    def trace_agent_execution(self, func: Callable) -> Callable:
        """Decorator to trace agent execution"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not self.config.enabled:
                return await func(*args, **kwargs)
                
            # Extract agent instance and task info
            agent = args[0] if args else None
            task_name = getattr(agent, 'task', 'Unknown Task') if agent else 'Unknown Task'
            
            trace_id = self.tracer.start_trace(
                name=f"agent_execution_{func.__name__}",
                input_data={"task": task_name, "function": func.__name__},
                metadata={"agent_type": type(agent).__name__ if agent else "Unknown"}
            )
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                
                # Evaluate task completion
                if hasattr(result, 'history') and result.history:
                    last_step = result.history[-1] if result.history else None
                    if last_step and hasattr(last_step, 'result'):
                        scores = self.evaluator.evaluate_task_completion(
                            task_description=task_name,
                            agent_output=last_step.result
                        )
                        
                        self.tracer.end_trace(
                            trace_id,
                            output_data={"steps_completed": len(result.history)},
                            feedback_scores=scores
                        )
                    else:
                        self.tracer.end_trace(trace_id)
                else:
                    self.tracer.end_trace(trace_id)
                
                return result
                
            except Exception as e:
                self.tracer.end_trace(
                    trace_id,
                    output_data={"error": str(e)},
                    feedback_scores={"error_free": 0.0}
                )
                raise
                
        return wrapper
    
    def trace_action_execution(self, func: Callable) -> Callable:
        """Decorator to trace action execution"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not self.config.enabled:
                return await func(*args, **kwargs)
                
            action_name = func.__name__
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                duration_ms = (time.time() - start_time) * 1000
                success = not (hasattr(result, 'error') and result.error)
                
                self.tracer.log_span(
                    name=action_name,
                    input_data={"args_count": len(args), "kwargs_keys": list(kwargs.keys())},
                    output_data={"success": success},
                    span_type="action"
                )
                
                self.monitor.track_action_execution(
                    action_name=action_name,
                    success=success,
                    duration_ms=duration_ms,
                    error_message=getattr(result, 'error', None) if hasattr(result, 'error') else None
                )
                
                # Evaluate step efficiency
                self.evaluator.evaluate_step_efficiency(
                    step_number=getattr(args[0], 'n_steps', 0) if args else 0,
                    action_type=action_name,
                    execution_time_ms=duration_ms,
                    success=success
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                self.tracer.log_span(
                    name=action_name,
                    input_data={"args_count": len(args), "kwargs_keys": list(kwargs.keys())},
                    output_data={"error": str(e)},
                    span_type="action"
                )
                
                self.monitor.track_action_execution(
                    action_name=action_name,
                    success=False,
                    duration_ms=duration_ms,
                    error_message=str(e)
                )
                
                raise
                
        return wrapper
    
    def export_data(self) -> Dict[str, Any]:
        """Export all collected data for analysis"""
        if not self.config.enabled:
            return {}
            
        return {
            "traces": self.tracer.traces,
            "evaluations": self.evaluator.evaluation_results,
            "metrics_summary": self.monitor.get_summary_metrics(),
            "raw_metrics": self.monitor.metrics,
            "config": {
                "project_name": self.config.project_name,
                "enabled": self.config.enabled,
                "tags": self.config.tags
            }
        }