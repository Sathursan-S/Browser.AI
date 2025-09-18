"""
Event Adapter for Browser.AI Log Streaming

This module provides a non-intrusive way to capture and stream logs
from the Browser.AI library without modifying its existing implementation.
"""

import logging
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from queue import Empty, Queue
from typing import Any, Callable, Dict, List, Optional


class LogLevel(Enum):
	"""Log levels for events"""

	DEBUG = 'DEBUG'
	INFO = 'INFO'
	WARNING = 'WARNING'
	ERROR = 'ERROR'
	RESULT = 'RESULT'


class EventType(Enum):
	"""Types of events that can be captured"""

	LOG = 'log'
	AGENT_START = 'agent_start'
	AGENT_STEP = 'agent_step'
	AGENT_ACTION = 'agent_action'
	AGENT_RESULT = 'agent_result'
	AGENT_COMPLETE = 'agent_complete'
	AGENT_ERROR = 'agent_error'
	AGENT_PAUSE = 'agent_pause'
	AGENT_RESUME = 'agent_resume'
	AGENT_STOP = 'agent_stop'


@dataclass
class LogEvent:
	"""Represents a log event"""

	timestamp: datetime
	level: LogLevel
	logger_name: str
	message: str
	event_type: EventType = EventType.LOG
	metadata: Optional[Dict[str, Any]] = None


class LogCapture(logging.Handler):
	"""Custom logging handler to capture Browser.AI logs"""

	def __init__(self, event_queue: Queue):
		super().__init__()
		self.event_queue = event_queue

	def emit(self, record: logging.LogRecord) -> None:
		"""Capture log record and convert to LogEvent"""
		try:
			# Determine event type based on log content
			event_type = self._determine_event_type(record)

			# Map logging levels to our LogLevel enum
			level_mapping = {
				logging.DEBUG: LogLevel.DEBUG,
				logging.INFO: LogLevel.INFO,
				logging.WARNING: LogLevel.WARNING,
				logging.ERROR: LogLevel.ERROR,
				35: LogLevel.RESULT,  # Custom RESULT level from Browser.AI
			}

			level = level_mapping.get(record.levelno, LogLevel.INFO)

			# Create log event
			event = LogEvent(
				timestamp=datetime.fromtimestamp(record.created),
				level=level,
				logger_name=record.name,
				message=self.format(record),
				event_type=event_type,
				metadata={'module': record.module, 'function': record.funcName, 'line': record.lineno},
			)

			# Add to queue (non-blocking)
			try:
				self.event_queue.put_nowait(event)
			except:
				pass  # Queue full, skip this event

		except Exception:
			# Don't let logging errors break the application
			pass

	def _determine_event_type(self, record: logging.LogRecord) -> EventType:
		"""Determine event type based on log record content"""
		message = record.getMessage().lower()

		if 'starting task' in message:
			return EventType.AGENT_START
		elif 'step' in message and '📍' in record.getMessage():
			return EventType.AGENT_STEP
		elif any(action in message for action in ['clicked', 'navigated', 'input', 'scrolled']):
			return EventType.AGENT_ACTION
		elif 'result' in message or 'extracted' in message:
			return EventType.AGENT_RESULT
		elif 'task completed' in message or '✅' in record.getMessage():
			return EventType.AGENT_COMPLETE
		elif 'error' in message or 'failed' in message or '❌' in record.getMessage():
			return EventType.AGENT_ERROR
		elif 'pausing' in message or '🔄' in record.getMessage():
			return EventType.AGENT_PAUSE
		elif 'resuming' in message or '▶️' in record.getMessage():
			return EventType.AGENT_RESUME
		elif 'stopping' in message or '⏹️' in record.getMessage():
			return EventType.AGENT_STOP

		return EventType.LOG


class EventAdapter:
	"""
	Non-intrusive event adapter for Browser.AI log streaming.

	This adapter captures logs from the Browser.AI library and provides
	a clean interface for real-time event streaming to GUI components.
	"""

	def __init__(self, max_events: int = 1000):
		self.max_events = max_events
		self.event_queue = Queue(maxsize=max_events)
		self.subscribers: List[Callable[[LogEvent], None]] = []
		self.log_capture = LogCapture(self.event_queue)
		self._running = False
		self._worker_thread: Optional[threading.Thread] = None
		self._browser_ai_logger: Optional[logging.Logger] = None

	def start(self) -> None:
		"""Start capturing Browser.AI logs"""
		if self._running:
			return

		# Get Browser.AI logger and add our handler
		self._browser_ai_logger = logging.getLogger('browser_ai')
		self._browser_ai_logger.addHandler(self.log_capture)

		# Start worker thread for event processing
		self._running = True
		self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
		self._worker_thread.start()

	def stop(self) -> None:
		"""Stop capturing logs"""
		if not self._running:
			return

		self._running = False

		# Remove our handler from Browser.AI logger
		if self._browser_ai_logger:
			self._browser_ai_logger.removeHandler(self.log_capture)

		# Wait for worker thread to finish
		if self._worker_thread:
			self._worker_thread.join(timeout=1.0)

	def subscribe(self, callback: Callable[[LogEvent], None]) -> None:
		"""Subscribe to log events"""
		if callback not in self.subscribers:
			self.subscribers.append(callback)

	def unsubscribe(self, callback: Callable[[LogEvent], None]) -> None:
		"""Unsubscribe from log events"""
		if callback in self.subscribers:
			self.subscribers.remove(callback)

	def get_recent_events(self, count: int = 50) -> List[LogEvent]:
		"""Get recent events (non-blocking)"""
		events = []
		try:
			while len(events) < count:
				event = self.event_queue.get_nowait()
				events.append(event)
		except Empty:
			pass
		return events

	def _process_events(self) -> None:
		"""Worker thread to process events and notify subscribers"""
		while self._running:
			try:
				# Get event with timeout
				event = self.event_queue.get(timeout=0.1)

				# Notify all subscribers
				for callback in self.subscribers[:]:  # Copy list to avoid issues during iteration
					try:
						callback(event)
					except Exception:
						# Don't let subscriber errors break the event loop
						pass

			except Empty:
				continue
			except Exception:
				break

	def emit_custom_event(
		self, event_type: EventType, message: str, level: LogLevel = LogLevel.INFO, metadata: Optional[Dict[str, Any]] = None
	) -> None:
		"""Emit a custom event (useful for GUI state changes)"""
		event = LogEvent(
			timestamp=datetime.now(),
			level=level,
			logger_name='browser_ai_gui',
			message=message,
			event_type=event_type,
			metadata=metadata or {},
		)

		# If not running, directly notify subscribers
		if not self._running:
			for callback in self.subscribers[:]:
				try:
					callback(event)
				except Exception:
					pass
		else:
			try:
				self.event_queue.put_nowait(event)
			except:
				pass  # Queue full

	def clear_events(self) -> None:
		"""Clear all pending events"""
		try:
			while True:
				self.event_queue.get_nowait()
		except Empty:
			pass
