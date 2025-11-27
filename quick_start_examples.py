#!/usr/bin/env python3
"""
Browser.AI Quick Start Examples

Run these commands to start Browser.AI in different configurations.
"""

import subprocess
import sys


def run_command(description, command):
    """Print and optionally run a command"""
    print(f"\n{'='*70}")
    print(f"Example: {description}")
    print(f"{'='*70}")
    print(f"Command: {' '.join(command)}\n")

    response = input("Run this command? (y/n): ").strip().lower()
    if response == "y":
        subprocess.run(command)
    else:
        print("Skipped.\n")


def main():
    """Show common usage examples"""
    print(
        """
╔═══════════════════════════════════════════════════════════════════╗
║                  Browser.AI Quick Start Examples                  ║
╔═══════════════════════════════════════════════════════════════════╝
║
║  This script demonstrates common ways to launch Browser.AI
║
╚═══════════════════════════════════════════════════════════════════╝
"""
    )

    examples = [
        (
            "Standard Launch (Recommended for first-time users)",
            [sys.executable, "run_project.py"],
            """
            • Builds extension in production mode
            • Launches Chrome with debugging enabled
            • Starts server on port 5000
            • Opens extension management page
            """,
        ),
        (
            "Development Mode (Hot reload for extension)",
            [sys.executable, "run_project.py", "--dev"],
            """
            • Extension rebuilds automatically on code changes
            • Faster iteration during development
            • Server runs in production mode
            """,
        ),
        (
            "Server Only (Working on backend)",
            [sys.executable, "run_project.py", "--skip-chrome", "--skip-build"],
            """
            • Starts only the Flask server
            • No Chrome launch
            • No extension build
            • Great for backend development
            """,
        ),
        (
            "Full Debug Mode (Maximum verbosity)",
            [sys.executable, "run_project.py", "--dev", "--server-debug"],
            """
            • Extension in dev mode
            • Server in debug mode with auto-reload
            • Detailed logging everywhere
            """,
        ),
        (
            "Custom Ports (Avoid conflicts)",
            [
                sys.executable,
                "run_project.py",
                "--port",
                "8080",
                "--debug-port",
                "9223",
            ],
            """
            • Server on port 8080
            • Chrome debugging on port 9223
            • Useful if default ports are occupied
            """,
        ),
        (
            "Production Build Test",
            [sys.executable, "run_project.py", "--skip-chrome"],
            """
            • Builds production extension
            • Starts server
            • No Chrome launch (load extension manually)
            • Test production build before deployment
            """,
        ),
    ]

    for i, (description, command, details) in enumerate(examples, 1):
        print(f"\n{i}. {description}")
        print(f"   Command: {' '.join(command)}")
        print(f"   Details:{details}")

    print("\n" + "=" * 70)
    choice = input("\nSelect an example to run (1-6, or 'q' to quit): ").strip()

    if choice == "q":
        print("Exiting...")
        return

    try:
        index = int(choice) - 1
        if 0 <= index < len(examples):
            description, command, _ = examples[index]
            print(f"\n{description}")
            print(f"Running: {' '.join(command)}\n")
            subprocess.run(command)
        else:
            print("Invalid choice")
    except ValueError:
        print("Invalid choice")


if __name__ == "__main__":
    main()
