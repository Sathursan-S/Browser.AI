#!/usr/bin/env python3
"""
Launch script for Browser AI Web Chat Interface
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat_interface.web_app import main

if __name__ == "__main__":
    print("🚀 Starting Browser AI Web Chat Interface...")
    print("📝 The web interface will open in your browser")
    print("⚙️ Configure your LLM settings in the web interface")
    print("💬 Start chatting to control browser automation!")
    print("-" * 50)
    
    main()