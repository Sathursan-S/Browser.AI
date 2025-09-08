"""
Metrics collection and monitoring system for Browser.AI MLOps

This module provides comprehensive metrics collection including:
- Real-time performance monitoring
- Agent behavior metrics
- System resource usage
- Error tracking and analysis
- Custom metric definitions
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

try:
	import psutil
except ImportError:
	# Mock psutil for environments where it's not available
	class MockPsutil:
		@staticmethod
		def cpu_percent():
			return 15.0
		@staticmethod
		def virtual_memory():
			class MockMemory:
				percent = 25.0
				used = 2 * 1024**3  # 2GB
			return MockMemory()
		@staticmethod
		def disk_usage(path):
			class MockDisk:
				percent = 60.0
			return MockDisk()
		@staticmethod
		def net_io_counters():
			class MockNet:
				bytes_sent = 1024
				bytes_recv = 2048
			return MockNet()
	psutil = MockPsutil()

from pydantic import BaseModel, Field


class SystemMetrics(BaseModel):
	"""System resource metrics"""
	timestamp: datetime = Field(default_factory=datetime.now)
	cpu_percent: float
	memory_percent: float
	memory_used_gb: float
	disk_usage_percent: float
	network_sent_bytes: int = 0
	network_recv_bytes: int = 0


class AgentMetrics(BaseModel):
	"""Agent performance metrics"""
	timestamp: datetime = Field(default_factory=datetime.now)
	task_id: str
	
	# Task metrics
	task_duration_seconds: Optional[float] = None
	steps_completed: int = 0
	actions_performed: int = 0
	success: Optional[bool] = None
	
	# Action breakdown
	click_actions: int = 0
	type_actions: int = 0
	navigate_actions: int = 0
	scroll_actions: int = 0
	screenshot_actions: int = 0
	other_actions: int = 0
	
	# Error metrics
	errors_encountered: int = 0
	error_types: Dict[str, int] = Field(default_factory=dict)
	
	# LLM metrics
	llm_calls_made: int = 0
	total_tokens_used: int = 0
	total_cost: Optional[float] = None
	
	# Browser metrics
	page_load_times: List[float] = Field(default_factory=list)
	dom_complexity_scores: List[int] = Field(default_factory=list)
	
	# Custom metrics
	custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class ErrorMetric(BaseModel):
	"""Error tracking metric"""
	timestamp: datetime = Field(default_factory=datetime.now)
	task_id: str
	error_type: str
	error_message: str
	error_context: Dict[str, Any] = Field(default_factory=dict)
	severity: str = "medium"  # low, medium, high, critical
	resolved: bool = False


class MetricsCollector:
	"""Main metrics collection and monitoring system"""
	
	def __init__(self, storage_dir: str = "metrics", retention_days: int = 30):
		self.storage_dir = storage_dir
		self.retention_days = retention_days
		self.logger = logging.getLogger(__name__)
		
		# In-memory metric storage for real-time access
		self.system_metrics: List[SystemMetrics] = []
		self.agent_metrics: List[AgentMetrics] = []
		self.error_metrics: List[ErrorMetric] = []
		
		# Current task tracking
		self.current_task_id: Optional[str] = None
		self.current_task_start: Optional[datetime] = None
		self.current_task_metrics: Optional[AgentMetrics] = None
		
		# System monitoring
		self.last_network_stats = psutil.net_io_counters()
		
	def start_task(self, task_id: str) -> str:
		"""Start tracking metrics for a new task"""
		self.current_task_id = task_id
		self.current_task_start = datetime.now()
		self.current_task_metrics = AgentMetrics(task_id=task_id)
		
		self.logger.info(f"Started metrics tracking for task: {task_id}")
		return task_id
		
	def end_task(self, success: bool = True):
		"""End current task tracking"""
		if not self.current_task_metrics or not self.current_task_start:
			return
			
		# Calculate final metrics
		end_time = datetime.now()
		duration = (end_time - self.current_task_start).total_seconds()
		
		self.current_task_metrics.task_duration_seconds = duration
		self.current_task_metrics.success = success
		self.current_task_metrics.timestamp = end_time
		
		# Store the completed metrics
		self.agent_metrics.append(self.current_task_metrics)
		
		self.logger.info(f"Completed metrics tracking for task: {self.current_task_id}")
		
		# Reset current task
		self.current_task_id = None
		self.current_task_start = None
		self.current_task_metrics = None
		
	def record_action(
		self,
		action_type: str,
		success: bool = True,
		duration: Optional[float] = None,
		context: Optional[Dict] = None
	):
		"""Record an agent action"""
		if not self.current_task_metrics:
			return
			
		self.current_task_metrics.actions_performed += 1
		self.current_task_metrics.steps_completed += 1
		
		# Update action type counters
		action_field = f"{action_type.lower()}_actions"
		if hasattr(self.current_task_metrics, action_field):
			setattr(
				self.current_task_metrics, 
				action_field, 
				getattr(self.current_task_metrics, action_field) + 1
			)
		else:
			self.current_task_metrics.other_actions += 1
			
		# Record custom metrics
		if duration:
			if "action_durations" not in self.current_task_metrics.custom_metrics:
				self.current_task_metrics.custom_metrics["action_durations"] = []
			self.current_task_metrics.custom_metrics["action_durations"].append({
				"action_type": action_type,
				"duration": duration,
				"success": success,
				"timestamp": datetime.now().isoformat()
			})
			
		if context:
			if "action_contexts" not in self.current_task_metrics.custom_metrics:
				self.current_task_metrics.custom_metrics["action_contexts"] = []
			self.current_task_metrics.custom_metrics["action_contexts"].append({
				"action_type": action_type,
				"context": context,
				"timestamp": datetime.now().isoformat()
			})
			
	def record_llm_call(
		self,
		tokens_used: int,
		cost: Optional[float] = None,
		model: Optional[str] = None,
		response_time: Optional[float] = None
	):
		"""Record LLM API call metrics"""
		if not self.current_task_metrics:
			return
			
		self.current_task_metrics.llm_calls_made += 1
		self.current_task_metrics.total_tokens_used += tokens_used
		
		if cost:
			if self.current_task_metrics.total_cost is None:
				self.current_task_metrics.total_cost = 0
			self.current_task_metrics.total_cost += cost
			
		# Record detailed LLM metrics
		if "llm_calls" not in self.current_task_metrics.custom_metrics:
			self.current_task_metrics.custom_metrics["llm_calls"] = []
			
		call_details = {
			"timestamp": datetime.now().isoformat(),
			"tokens_used": tokens_used,
			"cost": cost,
			"model": model,
			"response_time": response_time
		}
		self.current_task_metrics.custom_metrics["llm_calls"].append(call_details)
		
	def record_page_load(self, url: str, load_time: float, dom_complexity: Optional[int] = None):
		"""Record page load metrics"""
		if not self.current_task_metrics:
			return
			
		self.current_task_metrics.page_load_times.append(load_time)
		
		if dom_complexity:
			self.current_task_metrics.dom_complexity_scores.append(dom_complexity)
			
		# Record detailed page metrics
		if "page_loads" not in self.current_task_metrics.custom_metrics:
			self.current_task_metrics.custom_metrics["page_loads"] = []
			
		page_details = {
			"timestamp": datetime.now().isoformat(),
			"url": url,
			"load_time": load_time,
			"dom_complexity": dom_complexity
		}
		self.current_task_metrics.custom_metrics["page_loads"].append(page_details)
		
	def record_error(
		self,
		error_type: str,
		error_message: str,
		context: Optional[Dict] = None,
		severity: str = "medium"
	):
		"""Record an error"""
		task_id = self.current_task_id or "unknown"
		
		error_metric = ErrorMetric(
			task_id=task_id,
			error_type=error_type,
			error_message=error_message,
			error_context=context or {},
			severity=severity
		)
		
		self.error_metrics.append(error_metric)
		
		# Update current task error count
		if self.current_task_metrics:
			self.current_task_metrics.errors_encountered += 1
			
			if error_type not in self.current_task_metrics.error_types:
				self.current_task_metrics.error_types[error_type] = 0
			self.current_task_metrics.error_types[error_type] += 1
			
		self.logger.error(f"Recorded error: {error_type} - {error_message}")
		
	def collect_system_metrics(self):
		"""Collect current system resource metrics"""
		# Get network stats
		current_net = psutil.net_io_counters()
		net_sent = current_net.bytes_sent - self.last_network_stats.bytes_sent
		net_recv = current_net.bytes_recv - self.last_network_stats.bytes_recv
		self.last_network_stats = current_net
		
		# Get other system metrics
		memory = psutil.virtual_memory()
		disk = psutil.disk_usage('/')
		
		system_metric = SystemMetrics(
			cpu_percent=psutil.cpu_percent(),
			memory_percent=memory.percent,
			memory_used_gb=memory.used / (1024**3),  # Convert to GB
			disk_usage_percent=disk.percent,
			network_sent_bytes=net_sent,
			network_recv_bytes=net_recv
		)
		
		self.system_metrics.append(system_metric)
		
		# Keep only recent metrics
		cutoff_time = datetime.now() - timedelta(hours=1)
		self.system_metrics = [m for m in self.system_metrics if m.timestamp > cutoff_time]
		
	def get_task_summary(self, task_id: str) -> Optional[Dict[str, Any]]:
		"""Get summary metrics for a specific task"""
		task_metrics = None
		for metric in self.agent_metrics:
			if metric.task_id == task_id:
				task_metrics = metric
				break
				
		if not task_metrics:
			return None
			
		return {
			"task_id": task_id,
			"duration": task_metrics.task_duration_seconds,
			"success": task_metrics.success,
			"steps_completed": task_metrics.steps_completed,
			"actions_performed": task_metrics.actions_performed,
			"errors_encountered": task_metrics.errors_encountered,
			"llm_calls": task_metrics.llm_calls_made,
			"total_tokens": task_metrics.total_tokens_used,
			"total_cost": task_metrics.total_cost,
			"avg_page_load_time": sum(task_metrics.page_load_times) / len(task_metrics.page_load_times) if task_metrics.page_load_times else None
		}
		
	def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
		"""Get performance summary for the last N hours"""
		cutoff_time = datetime.now() - timedelta(hours=hours)
		recent_metrics = [m for m in self.agent_metrics if m.timestamp > cutoff_time]
		recent_errors = [e for e in self.error_metrics if e.timestamp > cutoff_time]
		
		if not recent_metrics:
			return {"message": "No metrics available for the specified time period"}
			
		# Calculate success rate
		successful_tasks = sum(1 for m in recent_metrics if m.success)
		success_rate = successful_tasks / len(recent_metrics)
		
		# Calculate average metrics
		avg_duration = sum(m.task_duration_seconds or 0 for m in recent_metrics) / len(recent_metrics)
		avg_steps = sum(m.steps_completed for m in recent_metrics) / len(recent_metrics)
		total_errors = sum(m.errors_encountered for m in recent_metrics)
		
		# LLM usage
		total_llm_calls = sum(m.llm_calls_made for m in recent_metrics)
		total_tokens = sum(m.total_tokens_used for m in recent_metrics)
		total_cost = sum(m.total_cost or 0 for m in recent_metrics)
		
		# Error analysis
		error_types = {}
		for error in recent_errors:
			error_types[error.error_type] = error_types.get(error.error_type, 0) + 1
			
		return {
			"time_period_hours": hours,
			"total_tasks": len(recent_metrics),
			"success_rate": success_rate,
			"avg_task_duration": avg_duration,
			"avg_steps_per_task": avg_steps,
			"total_errors": total_errors,
			"error_rate": total_errors / len(recent_metrics),
			"llm_usage": {
				"total_calls": total_llm_calls,
				"total_tokens": total_tokens,
				"total_cost": total_cost,
				"avg_calls_per_task": total_llm_calls / len(recent_metrics),
				"avg_tokens_per_task": total_tokens / len(recent_metrics)
			},
			"error_breakdown": error_types
		}
		
	def get_system_health(self) -> Dict[str, Any]:
		"""Get current system health metrics"""
		if not self.system_metrics:
			self.collect_system_metrics()
			
		if not self.system_metrics:
			return {"status": "no_data"}
			
		latest = self.system_metrics[-1]
		
		# Determine health status
		health_status = "healthy"
		if latest.cpu_percent > 80 or latest.memory_percent > 80:
			health_status = "warning"
		if latest.cpu_percent > 95 or latest.memory_percent > 95:
			health_status = "critical"
			
		return {
			"status": health_status,
			"timestamp": latest.timestamp.isoformat(),
			"cpu_percent": latest.cpu_percent,
			"memory_percent": latest.memory_percent,
			"memory_used_gb": latest.memory_used_gb,
			"disk_usage_percent": latest.disk_usage_percent
		}
		
	def get_error_analysis(self, hours: int = 24) -> Dict[str, Any]:
		"""Analyze errors from the last N hours"""
		cutoff_time = datetime.now() - timedelta(hours=hours)
		recent_errors = [e for e in self.error_metrics if e.timestamp > cutoff_time]
		
		if not recent_errors:
			return {"message": "No errors in the specified time period"}
			
		# Group by error type
		error_groups = {}
		severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
		
		for error in recent_errors:
			if error.error_type not in error_groups:
				error_groups[error.error_type] = []
			error_groups[error.error_type].append(error)
			severity_counts[error.severity] += 1
			
		# Find most common errors
		most_common = sorted(
			error_groups.items(),
			key=lambda x: len(x[1]),
			reverse=True
		)[:5]
		
		return {
			"time_period_hours": hours,
			"total_errors": len(recent_errors),
			"unique_error_types": len(error_groups),
			"severity_breakdown": severity_counts,
			"most_common_errors": [
				{
					"error_type": error_type,
					"count": len(errors),
					"latest_message": errors[0].error_message
				}
				for error_type, errors in most_common
			],
			"unresolved_errors": len([e for e in recent_errors if not e.resolved])
		}
		
	def export_metrics(self, filepath: str, hours: int = 24):
		"""Export metrics to JSON file"""
		import json
		
		cutoff_time = datetime.now() - timedelta(hours=hours)
		
		export_data = {
			"export_timestamp": datetime.now().isoformat(),
			"time_period_hours": hours,
			"agent_metrics": [
				m.model_dump(mode='json') for m in self.agent_metrics 
				if m.timestamp > cutoff_time
			],
			"system_metrics": [
				m.model_dump(mode='json') for m in self.system_metrics
				if m.timestamp > cutoff_time
			],
			"error_metrics": [
				e.model_dump(mode='json') for e in self.error_metrics
				if e.timestamp > cutoff_time
			]
		}
		
		with open(filepath, 'w') as f:
			json.dump(export_data, f, indent=2, default=str)
			
		self.logger.info(f"Exported metrics to {filepath}")
		
	def cleanup_old_metrics(self):
		"""Remove metrics older than retention period"""
		cutoff_time = datetime.now() - timedelta(days=self.retention_days)
		
		old_agent_count = len(self.agent_metrics)
		old_system_count = len(self.system_metrics)
		old_error_count = len(self.error_metrics)
		
		self.agent_metrics = [m for m in self.agent_metrics if m.timestamp > cutoff_time]
		self.system_metrics = [m for m in self.system_metrics if m.timestamp > cutoff_time]
		self.error_metrics = [e for e in self.error_metrics if e.timestamp > cutoff_time]
		
		self.logger.info(
			f"Cleaned up old metrics: "
			f"agent ({old_agent_count} -> {len(self.agent_metrics)}), "
			f"system ({old_system_count} -> {len(self.system_metrics)}), "
			f"errors ({old_error_count} -> {len(self.error_metrics)})"
		)