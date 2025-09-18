"""
Main entry points for Browser.AI GUI applications
"""

import argparse
import sys
from pathlib import Path

# Add the parent directory to path so we can import browser_ai
sys.path.insert(0, str(Path(__file__).parent.parent))

from browser_ai_gui.config import ConfigManager
from browser_ai_gui.tkinter_gui import BrowserAIGUI
from browser_ai_gui.web_app import WebApp


def run_web_app():
	"""Run the web application"""
	parser = argparse.ArgumentParser(description='Browser.AI Web GUI')
	parser.add_argument('--port', type=int, default=5000, help='Port to run on (default: 5000)')
	parser.add_argument('--debug', action='store_true', help='Run in debug mode')
	parser.add_argument('--config-dir', help='Configuration directory')

	args = parser.parse_args()

	config_manager = ConfigManager(args.config_dir) if args.config_dir else ConfigManager()
	app = WebApp(config_manager, args.port)
	app.run(debug=args.debug)


def run_tkinter_gui():
	"""Run the Tkinter desktop GUI"""
	parser = argparse.ArgumentParser(description='Browser.AI Desktop GUI')
	parser.add_argument('--config-dir', help='Configuration directory')

	args = parser.parse_args()

	# Initialize config manager
	if args.config_dir:
		config_manager = ConfigManager(args.config_dir)
	else:
		config_manager = ConfigManager()

	# Create and run GUI
	app = BrowserAIGUI()
	app.config_manager = config_manager  # Replace default config manager
	app.run()


def main():
	"""Main entry point with interface selection"""
	parser = argparse.ArgumentParser(description='Browser.AI GUI Applications')
	parser.add_argument('interface', choices=['web', 'desktop'], help='Interface type (web or desktop)')
	parser.add_argument('--port', type=int, default=5000, help='Port for web interface (default: 5000)')
	parser.add_argument('--debug', action='store_true', help='Run web interface in debug mode')
	parser.add_argument('--config-dir', help='Configuration directory')

	args = parser.parse_args()

	config_manager = ConfigManager(args.config_dir) if args.config_dir else ConfigManager()

	if args.interface == 'web':
		print(f'Starting Browser.AI Web Interface on port {args.port}')
		app = WebApp(config_manager, args.port)
		app.run(debug=args.debug)
	elif args.interface == 'desktop':
		print('Starting Browser.AI Desktop Interface')
		app = BrowserAIGUI()
		app.config_manager = config_manager
		app.run()


if __name__ == '__main__':
	main()
