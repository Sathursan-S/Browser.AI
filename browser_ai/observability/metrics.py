"""
Metrics Collection and Analysis for Browser.AI

Centralized metrics tracking integrated with Laminar for comprehensive observability.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from lmnr import Laminar

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Metrics for a single agent execution"""

    task: str
    session_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None

    # Task metrics
    total_steps: int = 0
    successful: bool = False
    error_count: int = 0

    # Action metrics
    total_actions: int = 0
    action_breakdown: Dict[str, int] = field(default_factory=dict)

    # Performance metrics
    total_duration_seconds: float = 0.0
    avg_step_duration: float = 0.0
    llm_calls: int = 0
    llm_total_latency: float = 0.0

    # Browser metrics
    pages_visited: int = 0
    unique_domains: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            "task": self.task,
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "total_steps": self.total_steps,
            "successful": self.successful,
            "error_count": self.error_count,
            "total_actions": self.total_actions,
            "action_breakdown": self.action_breakdown,
            "total_duration_seconds": self.total_duration_seconds,
            "avg_step_duration": self.avg_step_duration,
            "llm_calls": self.llm_calls,
            "llm_total_latency": self.llm_total_latency,
            "pages_visited": self.pages_visited,
            "unique_domains": self.unique_domains,
        }


class MetricsCollector:
    """
    Centralized metrics collection and reporting

    Features:
    - Real-time metrics tracking
    - Laminar integration
    - Aggregated statistics
    - Performance analysis
    """

    def __init__(self):
        self.active_sessions: Dict[str, AgentMetrics] = {}
        self.completed_sessions: List[AgentMetrics] = []

    def start_session(self, task: str, session_id: str) -> AgentMetrics:
        """Start tracking a new agent session"""
        metrics = AgentMetrics(
            task=task,
            session_id=session_id,
            started_at=datetime.now(),
        )

        self.active_sessions[session_id] = metrics

        # Track in Laminar
        Laminar.event(
            name="session.started",
            attributes={
                "task": task,
                "session_id": session_id,
                "timestamp": metrics.started_at.isoformat(),
            },
        )

        logger.info(f"Started metrics collection for session {session_id}")
        return metrics

    def record_step(self, session_id: str, step_number: int, duration: float):
        """Record a step execution"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return

        metrics = self.active_sessions[session_id]
        metrics.total_steps += 1

        # Update average duration
        if metrics.avg_step_duration == 0:
            metrics.avg_step_duration = duration
        else:
            metrics.avg_step_duration = (
                metrics.avg_step_duration * (metrics.total_steps - 1) + duration
            ) / metrics.total_steps

    def record_action(
        self,
        session_id: str,
        action_name: str,
        success: bool = True,
    ):
        """Record an action execution"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return

        metrics = self.active_sessions[session_id]
        metrics.total_actions += 1

        # Update action breakdown
        if action_name not in metrics.action_breakdown:
            metrics.action_breakdown[action_name] = 0
        metrics.action_breakdown[action_name] += 1

        if not success:
            metrics.error_count += 1

    def record_llm_call(self, session_id: str, latency: float):
        """Record an LLM call"""
        if session_id not in self.active_sessions:
            return

        metrics = self.active_sessions[session_id]
        metrics.llm_calls += 1
        metrics.llm_total_latency += latency

    def record_page_visit(self, session_id: str, url: str):
        """Record a page visit"""
        if session_id not in self.active_sessions:
            return

        metrics = self.active_sessions[session_id]
        metrics.pages_visited += 1

        # Extract domain
        from urllib.parse import urlparse

        domain = urlparse(url).netloc
        if domain and domain not in metrics.unique_domains:
            metrics.unique_domains.append(domain)

    def complete_session(
        self,
        session_id: str,
        successful: bool = True,
    ) -> Optional[AgentMetrics]:
        """Complete and finalize a session"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session {session_id} not found")
            return None

        metrics = self.active_sessions[session_id]
        metrics.completed_at = datetime.now()
        metrics.successful = successful
        metrics.total_duration_seconds = (
            metrics.completed_at - metrics.started_at
        ).total_seconds()

        # Move to completed
        self.completed_sessions.append(metrics)
        del self.active_sessions[session_id]

        # Track in Laminar
        Laminar.event(
            name="session.completed",
            attributes=metrics.to_dict(),
        )

        logger.info(f"Completed metrics collection for session {session_id}")
        return metrics

    def get_session_metrics(self, session_id: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific session"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]

        for metrics in self.completed_sessions:
            if metrics.session_id == session_id:
                return metrics

        return None

    def get_aggregated_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics across all completed sessions"""
        if not self.completed_sessions:
            return {"error": "No completed sessions"}

        total_sessions = len(self.completed_sessions)
        successful_sessions = sum(1 for m in self.completed_sessions if m.successful)

        avg_duration = (
            sum(m.total_duration_seconds for m in self.completed_sessions)
            / total_sessions
        )

        avg_steps = sum(m.total_steps for m in self.completed_sessions) / total_sessions

        avg_actions = (
            sum(m.total_actions for m in self.completed_sessions) / total_sessions
        )

        # Aggregate action breakdown
        all_actions = {}
        for metrics in self.completed_sessions:
            for action, count in metrics.action_breakdown.items():
                if action not in all_actions:
                    all_actions[action] = 0
                all_actions[action] += count

        stats = {
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "success_rate": successful_sessions / total_sessions,
            "avg_duration_seconds": avg_duration,
            "avg_steps_per_session": avg_steps,
            "avg_actions_per_session": avg_actions,
            "most_used_actions": sorted(
                all_actions.items(), key=lambda x: x[1], reverse=True
            )[:10],
        }

        # Track in Laminar
        Laminar.event(
            name="metrics.aggregated_stats",
            value=stats,
        )

        return stats

    def export_metrics(self, filepath: str):
        """Export all metrics to JSON file"""
        import json

        export_data = {
            "active_sessions": [m.to_dict() for m in self.active_sessions.values()],
            "completed_sessions": [m.to_dict() for m in self.completed_sessions],
            "aggregated_stats": self.get_aggregated_stats(),
        }

        with open(filepath, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Exported metrics to {filepath}")


# Global metrics collector instance
metrics_collector = MetricsCollector()
