#!/bin/bash
# Browser.AI Project Launcher for Unix/Linux/macOS
# Quick start script that runs the Python launcher

echo "========================================"
echo "   Browser.AI Project Launcher"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.11+ from https://www.python.org/"
    exit 1
fi

# Run the main launcher script
echo "Starting Browser.AI..."
echo
python3 run_project.py "$@"

# Check exit code
if [ $? -ne 0 ]; then
    echo
    echo "ERROR: Browser.AI failed to start"
    read -p "Press Enter to continue..."
fi
