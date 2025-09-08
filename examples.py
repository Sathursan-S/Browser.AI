#!/usr/bin/env python3
"""
Browser.AI GUI Examples

This script demonstrates how to run the Browser.AI GUI applications.
"""

import os
import sys
from pathlib import Path

# Add the Browser.AI directory to Python path
browser_ai_dir = Path(__file__).parent
sys.path.insert(0, str(browser_ai_dir))

from browser_ai_gui.main import main


def show_usage():
    """Show usage examples"""
    print("Browser.AI GUI Examples")
    print("=" * 50)
    print()
    print("Available interfaces:")
    print("  web      - Web-based chat interface (similar to ChatGPT)")
    print("  desktop  - Desktop GUI (similar to VS Code Copilot)")
    print()
    print("Usage examples:")
    print()
    print("1. Start web interface on default port (5000):")
    print("   python examples.py web")
    print()
    print("2. Start web interface on custom port:")
    print("   python examples.py web --port 8080")
    print()
    print("3. Start web interface in debug mode:")
    print("   python examples.py web --debug")
    print()
    print("4. Start desktop GUI:")
    print("   python examples.py desktop")
    print()
    print("5. Use custom configuration directory:")
    print("   python examples.py web --config-dir /path/to/config")
    print()
    print("Configuration:")
    print("- First run will create a configuration directory")
    print("- Default location: ~/.browser_ai_gui/")
    print("- Configure your LLM API keys in the settings")
    print()
    print("Supported LLM providers:")
    print("- OpenAI (requires OPENAI_API_KEY)")
    print("- Anthropic Claude (requires ANTHROPIC_API_KEY)")
    print("- Google Gemini (requires GOOGLE_API_KEY)")
    print("- Ollama (local, no API key needed)")
    print()
    print("Example tasks to try:")
    print("- 'Search for Python tutorials on Google'")
    print("- 'Go to GitHub and find trending Python repositories'")
    print("- 'Navigate to news.ycombinator.com and summarize top stories'")
    print("- 'Fill out a contact form on example.com'")
    print()


def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import flask
    except ImportError:
        missing_deps.append("flask")
    
    try:
        import flask_socketio
    except ImportError:
        missing_deps.append("flask-socketio")
    
    try:
        import tkinter
    except ImportError:
        missing_deps.append("tkinter (should be built into Python)")
    
    if missing_deps:
        print("Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print()
        print("Install missing dependencies:")
        print("  pip install flask flask-socketio")
        print()
        return False
    
    return True


def setup_demo_environment():
    """Setup demo environment with sample configuration"""
    print("Setting up demo environment...")
    
    # Create example .env file if it doesn't exist
    env_file = browser_ai_dir / ".env"
    if not env_file.exists():
        env_content = """# Browser.AI Configuration
# Add your API keys here

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Anthropic Claude  
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Google Gemini
GOOGLE_API_KEY=your_google_api_key_here

# Logging level (debug, info, result)
BROWSER_AI_LOGGING_LEVEL=info
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"Created example .env file: {env_file}")
        print("Please edit it with your actual API keys.")
    
    print("Demo environment ready!")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
        sys.exit(0)
    
    # Check dependencies
    if not check_dependencies():
        print("Please install missing dependencies first.")
        sys.exit(1)
    
    # Setup demo environment
    setup_demo_environment()
    
    # Run the main function
    sys.argv[0] = "browser_ai_gui"  # Replace script name for argparse
    main()