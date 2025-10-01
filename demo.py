#!/usr/bin/env python3
"""
Demo script to test Browser.AI GUI components

This script tests the event adapter and configuration systems
without requiring full Browser.AI dependencies.
"""

import threading
import time

from browser_ai_gui.config import ConfigManager
from browser_ai_gui.event_adapter import EventAdapter, EventType, LogEvent, LogLevel


def test_event_adapter():
	"""Test the event adapter system"""
	print('Testing Event Adapter...')

	adapter = EventAdapter()
	events_received = []

	def handle_event(event: LogEvent):
		events_received.append(event)
		print(f'[{event.level.value}] {event.event_type.value}: {event.message}')

	adapter.subscribe(handle_event)

	# Emit some test events
	adapter.emit_custom_event(EventType.AGENT_START, 'Starting demo task', LogLevel.INFO, {'task': 'Demo automation task'})

	adapter.emit_custom_event(EventType.AGENT_ACTION, 'Clicking button with index 5', LogLevel.INFO)

	adapter.emit_custom_event(EventType.AGENT_RESULT, 'Extracted content: Sample data from webpage', LogLevel.RESULT)

	adapter.emit_custom_event(EventType.AGENT_COMPLETE, 'Task completed successfully', LogLevel.INFO)

	# Wait a bit for events to process
	time.sleep(0.5)

	print(f'Received {len(events_received)} events')
	assert len(events_received) == 4, 'Should receive 4 events'
	print('✅ Event Adapter test passed')
	print()


def test_config_manager():
	"""Test the configuration manager"""
	print('Testing Configuration Manager...')

	config = ConfigManager()

	# Test default values
	assert config.llm_config.provider == 'openai'
	assert config.llm_config.model == 'gpt-4-turbo'
	assert config.browser_config.headless == False
	assert config.agent_config.use_vision == True

	# Test updating configuration
	config.update_llm_config(provider='anthropic', model='claude-3-sonnet-20240229', temperature=0.2)

	assert config.llm_config.provider == 'anthropic'
	assert config.llm_config.model == 'claude-3-sonnet-20240229'
	assert config.llm_config.temperature == 0.2

	# Test validation
	issues = config.validate_config()
	print(f'Validation issues: {issues}')

	# Test supported providers
	providers = config.get_supported_providers()
	assert 'openai' in providers
	assert 'anthropic' in providers

	print('✅ Configuration Manager test passed')
	print()


def test_logging_integration():
	"""Test integration with Python logging"""
	print('Testing Logging Integration...')

	import logging

	# Setup Browser.AI style logger
	logger = logging.getLogger('browser_ai.test')
	logger.setLevel(logging.INFO)

	adapter = EventAdapter()
	adapter.start()

	events_received = []

	def handle_event(event: LogEvent):
		events_received.append(event)
		print(f'Captured log: [{event.level.value}] {event.message}')

	adapter.subscribe(handle_event)

	# Send some log messages
	logger.info('📍 Step 1')
	logger.info("🔍 Searched for 'test query' in Google")
	logger.info('🖱️ Clicked button with index 3')
	logger.info('📄 Result: Task completed successfully')

	# Wait for events to process
	time.sleep(0.5)
	adapter.stop()

	print(f'Captured {len(events_received)} log events')
	print('✅ Logging Integration test passed')
	print()


def simulate_browser_ai_session():
	"""Simulate a Browser.AI automation session"""
	print('Simulating Browser.AI Session...')

	adapter = EventAdapter()
	config = ConfigManager()

	events_log = []

	def log_event(event: LogEvent):
		events_log.append(event)
		timestamp = event.timestamp.strftime('%H:%M:%S')
		print(f'[{timestamp}] {event.event_type.value}: {event.message}')

	adapter.subscribe(log_event)

	# Simulate task execution
	def simulate_task():
		time.sleep(0.5)
		adapter.emit_custom_event(EventType.AGENT_START, '🚀 Starting task: Search for Python tutorials', LogLevel.INFO)

		time.sleep(1)
		adapter.emit_custom_event(EventType.AGENT_STEP, '📍 Step 1', LogLevel.INFO)

		time.sleep(0.5)
		adapter.emit_custom_event(EventType.AGENT_ACTION, '🔗 Navigated to https://google.com', LogLevel.INFO)

		time.sleep(0.5)
		adapter.emit_custom_event(EventType.AGENT_ACTION, "⌨️ Input 'Python tutorials' into search box", LogLevel.INFO)

		time.sleep(0.5)
		adapter.emit_custom_event(EventType.AGENT_ACTION, '🖱️ Clicked search button', LogLevel.INFO)

		time.sleep(1)
		adapter.emit_custom_event(EventType.AGENT_RESULT, '📄 Extracted top 5 search results', LogLevel.RESULT)

		time.sleep(0.5)
		adapter.emit_custom_event(EventType.AGENT_COMPLETE, '✅ Task completed successfully', LogLevel.INFO)

	# Run simulation in background thread
	thread = threading.Thread(target=simulate_task)
	thread.start()
	thread.join()

	time.sleep(0.5)  # Wait for final events

	print(f'\nSession completed with {len(events_log)} events')
	print('✅ Browser.AI Session simulation passed')
	print()


def main():
	"""Run all tests"""
	print('Browser.AI GUI Components - Demo & Test')
	print('=' * 50)
	print()

	try:
		test_event_adapter()
		test_config_manager()
		test_logging_integration()
		simulate_browser_ai_session()

		print('🎉 All tests passed!')
		print()
		print('Next steps:')
		print('1. Install GUI dependencies: pip install flask flask-socketio')
		print('2. Run web interface: python examples.py web')
		print('3. Run desktop GUI: python examples.py desktop')

	except Exception as e:
		print(f'❌ Test failed: {e}')
		import traceback

		traceback.print_exc()


if __name__ == '__main__':
	main()
