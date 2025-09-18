#!/usr/bin/env python3
"""
Browser.AI GUI Launcher

Smart launcher that handles dependencies and provides helpful guidance.
"""

import subprocess
import sys


def check_dependencies():
	"""Check if required dependencies are installed"""
	missing = []

	# Check basic Python requirements
	try:
		import browser_ai
	except ImportError:
		missing.append('browser_ai - Core Browser.AI library not available')

	# Check GUI dependencies
	try:
		import flask
	except ImportError:
		missing.append('flask - Required for web interface')

	try:
		import flask_socketio
	except ImportError:
		missing.append('flask-socketio - Required for real-time communication')

	try:
		import tkinter
	except ImportError:
		missing.append('tkinter - Required for desktop GUI (should be built into Python)')

	return missing


def install_gui_dependencies():
	"""Install GUI dependencies"""
	print('Installing GUI dependencies...')
	try:
		subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask', 'flask-socketio', 'eventlet'])
		return True
	except subprocess.CalledProcessError:
		return False


def show_help():
	"""Show help information"""
	print("""
Browser.AI GUI Launcher
=======================

Available interfaces:
  web      - Web-based chat interface
  desktop  - Desktop GUI (Tkinter-based)

Usage:
  python launch.py web [--port PORT] [--debug]
  python launch.py desktop [--config-dir DIR]

Examples:
  python launch.py web                    # Start web interface on port 5000
  python launch.py web --port 8080       # Start on custom port
  python launch.py web --debug           # Enable debug mode
  python launch.py desktop               # Start desktop GUI

Configuration:
- First run creates ~/.browser_ai_gui/ config directory
- Set API keys in the GUI settings panel
- Supported providers: OpenAI, Anthropic, Google, Ollama

Sample tasks to try:
- "Search for Python tutorials on Google"
- "Navigate to GitHub and find trending repositories"
- "Go to news website and summarize top stories"
""")


def main():
	"""Main launcher"""
	if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
		show_help()
		return

	# Check dependencies
	missing = check_dependencies()

	# Handle missing core Browser.AI
	if any('browser_ai' in dep for dep in missing):
		print('❌ Browser.AI core library not found!')
		print()
		print('This appears to be a development environment.')
		print('The GUI components need the Browser.AI library to function.')
		print()
		print('Solutions:')
		print('1. Install from PyPI: pip install browser-ai')
		print('2. Run from source: add Browser.AI to Python path')
		print('3. Install in development mode: pip install -e .')
		return 1

	# Handle missing GUI dependencies
	gui_deps_missing = [dep for dep in missing if 'flask' in dep]
	if gui_deps_missing and sys.argv[1] == 'web':
		print('📦 Installing missing web interface dependencies...')
		if install_gui_dependencies():
			print('✅ Dependencies installed successfully!')
		else:
			print('❌ Failed to install dependencies')
			print('Please run manually: pip install flask flask-socketio eventlet')
			return 1

	# Handle missing tkinter
	if any('tkinter' in dep for dep in missing) and sys.argv[1] == 'desktop':
		print('❌ Tkinter not available!')
		print()
		print('Tkinter should be included with Python installations.')
		print('Solutions:')
		print('- Linux: sudo apt-get install python3-tk')
		print('- macOS: Install Python from python.org')
		print('- Windows: Reinstall Python with tkinter option checked')
		print()
		print('Try the web interface instead: python launch.py web')
		return 1

	# Launch the appropriate interface
	interface = sys.argv[1]

	if interface == 'web':
		try:
			from browser_ai_gui.main import run_web_app

			# Replace sys.argv[0] for argparse
			sys.argv = ['browser-ai-web'] + sys.argv[2:]
			run_web_app()
		except ImportError as e:
			print(f'❌ Failed to import web app: {e}')
			return 1
		except KeyboardInterrupt:
			print('\n👋 Web interface stopped')
			return 0

	elif interface == 'desktop':
		try:
			from browser_ai_gui.main import run_tkinter_gui

			# Replace sys.argv[0] for argparse
			sys.argv = ['browser-ai-desktop'] + sys.argv[2:]
			run_tkinter_gui()
		except ImportError as e:
			print(f'❌ Failed to import desktop GUI: {e}')
			print('Try the web interface: python launch.py web')
			return 1
		except KeyboardInterrupt:
			print('\n👋 Desktop GUI stopped')
			return 0

	else:
		print(f'❌ Unknown interface: {interface}')
		print('Available: web, desktop')
		show_help()
		return 1


if __name__ == '__main__':
	try:
		exit_code = main()
		sys.exit(exit_code or 0)
	except Exception as e:
		print(f'❌ Unexpected error: {e}')
		import traceback

		traceback.print_exc()
		sys.exit(1)
