"""
Web Application for Browser.AI GUI

Flask-based web application with WebSocket support for real-time log streaming
and chat-based task management.
"""

import asyncio
import os
import threading
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit

from .config import ConfigManager
from .event_adapter import EventAdapter, EventType, LogEvent, LogLevel


class TaskManager:
	"""Manages Browser.AI task execution"""

	def __init__(self, config_manager: ConfigManager, event_adapter: EventAdapter):
		self.config_manager = config_manager
		self.event_adapter = event_adapter
		self.current_agent = None
		self.current_task = None
		self.is_running = False
		self.task_thread = None

	async def start_task(self, task_description: str) -> Dict[str, Any]:
		"""Start a new Browser.AI task"""
		if self.is_running:
			return {'success': False, 'error': 'Task already running'}

		try:
			# Import Browser.AI components
			from browser_ai import Agent, Browser, BrowserConfig

			# Create LLM instance
			llm = self.config_manager.get_llm_instance()

			# Create browser config
			browser_config_dict = self.config_manager.get_browser_config_dict()
			browser_config = BrowserConfig(**browser_config_dict)
			browser = Browser(config=browser_config)

			# Create agent
			self.current_agent = Agent(
				task=task_description,
				llm=llm,
				browser=browser,
				use_vision=self.config_manager.agent_config.use_vision,
				max_failures=self.config_manager.agent_config.max_failures,
				retry_delay=self.config_manager.agent_config.retry_delay,
				generate_gif=self.config_manager.agent_config.generate_gif,
				validate_output=self.config_manager.agent_config.validate_output,
			)

			self.current_task = task_description
			self.is_running = True

			# Emit custom event
			self.event_adapter.emit_custom_event(
				EventType.AGENT_START, f'Starting task: {task_description}', LogLevel.INFO, {'task': task_description}
			)

			# Run agent in separate thread
			def run_agent():
				try:
					loop = asyncio.new_event_loop()
					asyncio.set_event_loop(loop)
					result = loop.run_until_complete(self.current_agent.run(max_steps=self.config_manager.agent_config.max_steps))

					self.event_adapter.emit_custom_event(
						EventType.AGENT_COMPLETE, 'Task completed successfully', LogLevel.INFO, {'result': str(result)}
					)

				except Exception as e:
					self.event_adapter.emit_custom_event(
						EventType.AGENT_ERROR, f'Task failed: {str(e)}', LogLevel.ERROR, {'error': str(e)}
					)
				finally:
					self.is_running = False
					self.current_agent = None
					self.current_task = None

			self.task_thread = threading.Thread(target=run_agent, daemon=True)
			self.task_thread.start()

			return {'success': True, 'message': 'Task started successfully'}

		except Exception as e:
			self.is_running = False
			return {'success': False, 'error': str(e)}

	def stop_task(self) -> Dict[str, Any]:
		"""Stop the current task"""
		if not self.is_running or not self.current_agent:
			return {'success': False, 'error': 'No task running'}

		try:
			self.current_agent.stop()
			self.event_adapter.emit_custom_event(EventType.AGENT_STOP, 'Task stopped by user', LogLevel.INFO)
			return {'success': True, 'message': 'Task stopped successfully'}
		except Exception as e:
			return {'success': False, 'error': str(e)}

	def pause_task(self) -> Dict[str, Any]:
		"""Pause the current task"""
		if not self.is_running or not self.current_agent:
			return {'success': False, 'error': 'No task running'}

		try:
			self.current_agent.pause()
			self.event_adapter.emit_custom_event(EventType.AGENT_PAUSE, 'Task paused by user', LogLevel.INFO)
			return {'success': True, 'message': 'Task paused successfully'}
		except Exception as e:
			return {'success': False, 'error': str(e)}

	def resume_task(self) -> Dict[str, Any]:
		"""Resume the current task"""
		if not self.is_running or not self.current_agent:
			return {'success': False, 'error': 'No task running'}

		try:
			self.current_agent.resume()
			self.event_adapter.emit_custom_event(EventType.AGENT_RESUME, 'Task resumed by user', LogLevel.INFO)
			return {'success': True, 'message': 'Task resumed successfully'}
		except Exception as e:
			return {'success': False, 'error': str(e)}

	def get_status(self) -> Dict[str, Any]:
		"""Get current task status"""
		return {'is_running': self.is_running, 'current_task': self.current_task, 'has_agent': self.current_agent is not None}


class WebApp:
	"""Web application for Browser.AI GUI"""

	def __init__(self, config_manager: Optional[ConfigManager] = None, port: int = 5000):
		self.port = port
		self.config_manager = config_manager or ConfigManager()
		self.event_adapter = EventAdapter()
		self.task_manager = TaskManager(self.config_manager, self.event_adapter)

		# Create Flask app
		self.app = Flask(__name__)
		self.app.config['SECRET_KEY'] = 'browser-ai-gui-secret-key'
		self.socketio = SocketIO(self.app, cors_allowed_origins='*')

		# Setup routes
		self._setup_routes()
		self._setup_socketio_events()

		# Start event adapter
		self.event_adapter.start()
		self.event_adapter.subscribe(self._on_log_event)

	def _setup_routes(self):
		"""Setup Flask routes"""

		@self.app.route('/')
		def index():
			return render_template('index.html')

		@self.app.route('/static/<path:filename>')
		def static_files(filename):
			return send_from_directory('static', filename)

		@self.app.route('/api/config', methods=['GET'])
		def get_config():
			return jsonify(
				{
					'llm': {
						'provider': self.config_manager.llm_config.provider,
						'model': self.config_manager.llm_config.model,
						'temperature': self.config_manager.llm_config.temperature,
						'has_api_key': bool(self.config_manager.llm_config.api_key),
					},
					'browser': {
						'headless': self.config_manager.browser_config.headless,
						'disable_security': self.config_manager.browser_config.disable_security,
					},
					'agent': {
						'use_vision': self.config_manager.agent_config.use_vision,
						'max_failures': self.config_manager.agent_config.max_failures,
						'max_steps': self.config_manager.agent_config.max_steps,
					},
					'supported_providers': self.config_manager.get_supported_providers(),
					'default_models': self.config_manager.get_default_models(),
				}
			)

		@self.app.route('/api/config', methods=['POST'])
		def update_config():
			data = request.get_json()

			try:
				if 'llm' in data:
					self.config_manager.update_llm_config(**data['llm'])
				if 'browser' in data:
					self.config_manager.update_browser_config(**data['browser'])
				if 'agent' in data:
					self.config_manager.update_agent_config(**data['agent'])

				# Validate configuration
				issues = self.config_manager.validate_config()

				return jsonify({'success': True, 'message': 'Configuration updated successfully', 'validation_issues': issues})
			except Exception as e:
				return jsonify({'success': False, 'error': str(e)}), 400

		@self.app.route('/api/task/status', methods=['GET'])
		def task_status():
			return jsonify(self.task_manager.get_status())

		@self.app.route('/api/task/start', methods=['POST'])
		def start_task():
			data = request.get_json()
			task_description = data.get('task', '').strip()

			if not task_description:
				return jsonify({'success': False, 'error': 'Task description is required'}), 400

			# Run in thread to avoid blocking
			def run_start_task():
				loop = asyncio.new_event_loop()
				asyncio.set_event_loop(loop)
				loop.run_until_complete(self.task_manager.start_task(task_description))

			threading.Thread(target=run_start_task, daemon=True).start()

			return jsonify({'success': True, 'message': 'Starting task...'})

		@self.app.route('/api/task/stop', methods=['POST'])
		def stop_task():
			result = self.task_manager.stop_task()
			return jsonify(result)

		@self.app.route('/api/task/pause', methods=['POST'])
		def pause_task():
			result = self.task_manager.pause_task()
			return jsonify(result)

		@self.app.route('/api/task/resume', methods=['POST'])
		def resume_task():
			result = self.task_manager.resume_task()
			return jsonify(result)

	def _setup_socketio_events(self):
		"""Setup SocketIO events"""

		@self.socketio.on('connect')
		def handle_connect():
			print(f'Client connected: {request.sid}')

			# Send recent events to new client
			recent_events = self.event_adapter.get_recent_events(50)
			for event in recent_events:
				emit('log_event', self._serialize_log_event(event))

		@self.socketio.on('disconnect')
		def handle_disconnect():
			print(f'Client disconnected: {request.sid}')

		@self.socketio.on('request_status')
		def handle_status_request():
			status = self.task_manager.get_status()
			emit('status_update', status)

	def _on_log_event(self, event: LogEvent):
		"""Handle log events from event adapter"""
		# Broadcast to all connected clients
		self.socketio.emit('log_event', self._serialize_log_event(event))

	def _serialize_log_event(self, event: LogEvent) -> Dict[str, Any]:
		"""Serialize log event for JSON transmission"""
		return {
			'timestamp': event.timestamp.isoformat(),
			'level': event.level.value,
			'logger_name': event.logger_name,
			'message': event.message,
			'event_type': event.event_type.value,
			'metadata': event.metadata or {},
		}

	def run(self, debug: bool = False):
		"""Run the web application"""
		print(f'Starting Browser.AI Web GUI on http://localhost:{self.port}')
		print('Press Ctrl+C to stop')

		# Create templates directory if it doesn't exist
		templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
		os.makedirs(templates_dir, exist_ok=True)

		# Create static directory if it doesn't exist
		static_dir = os.path.join(os.path.dirname(__file__), 'static')
		os.makedirs(static_dir, exist_ok=True)

		try:
			self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=debug)
		except KeyboardInterrupt:
			print('\nShutting down...')
		finally:
			self.event_adapter.stop()


if __name__ == '__main__':
	app = WebApp()
	app.run(debug=True)
