#!/usr/bin/env python3
"""
Launch script for Browser AI Desktop Chat Interface
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from chat_interface.desktop_app import main

if __name__ == "__main__":
    print("🚀 Starting Browser AI Desktop Chat Interface...")
    print("🖥️ The desktop application will open shortly")
    print("⚙️ Configure your LLM settings in the application")
    print("💬 Start chatting to control browser automation!")
    print("-" * 50)
    
    main()