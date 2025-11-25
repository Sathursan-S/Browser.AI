#!/usr/bin/env python3
"""
Browser.AI Complete Project Launcher

This script handles the complete setup and launch of the Browser.AI project:
1. Launches Chrome in debug mode with remote debugging enabled
2. Builds the extension (in dev or production mode)
3. Starts the Browser.AI server
4. Optionally loads the extension in Chrome

Usage:
    python run_project.py                    # Run with defaults
    python run_project.py --dev              # Build extension in dev mode
    python run_project.py --port 5000        # Custom server port
    python run_project.py --skip-build       # Skip extension build
    python run_project.py --skip-chrome      # Don't launch Chrome
    python run_project.py --chrome-path "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import List, Optional


# Color codes for terminal output
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_header(message: str):
    """Print a styled header message"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(message: str):
    """Print a success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    """Print an error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    """Print an info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def print_warning(message: str):
    """Print a warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def find_chrome_path() -> Optional[str]:
    """Find Chrome executable path based on the operating system"""
    system = platform.system()

    common_paths = []
    if system == "Windows":
        common_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    elif system == "Darwin":  # macOS
        common_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        ]
    elif system == "Linux":
        common_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


def launch_chrome_debug_mode(
    chrome_path: str, user_data_dir: Optional[str] = None, debug_port: int = 9222
) -> Optional[subprocess.Popen]:
    """
    Launch Chrome in debug mode with remote debugging enabled

    Args:
        chrome_path: Path to Chrome executable
        user_data_dir: Custom user data directory (optional)
        debug_port: Port for remote debugging (default: 9222)

    Returns:
        subprocess.Popen object or None if failed
    """
    print_header("Launching Chrome in Debug Mode")

    if not os.path.exists(chrome_path):
        print_error(f"Chrome not found at: {chrome_path}")
        return None

    # Create user data directory if not specified
    if not user_data_dir:
        user_data_dir = os.path.join(
            os.path.expanduser("~"), ".browser_ai_chrome_profile"
        )

    # Ensure user data directory exists
    os.makedirs(user_data_dir, exist_ok=True)

    # Chrome launch arguments
    chrome_args = [
        chrome_path,
        f"--remote-debugging-port={debug_port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        # "--disable-extensions-except=<extension-path>",  # Will be added if extension exists
    ]

    try:
        print_info(f"Chrome path: {chrome_path}")
        print_info(f"Debug port: {debug_port}")
        print_info(f"User data dir: {user_data_dir}")

        # Launch Chrome as a separate process
        if platform.system() == "Windows":
            process = subprocess.Popen(
                chrome_args,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )

        print_success(f"Chrome launched successfully (PID: {process.pid})")
        print_info(f"Remote debugging available at: http://localhost:{debug_port}")

        # Wait a bit for Chrome to start
        time.sleep(3)

        return process

    except Exception as e:
        print_error(f"Failed to launch Chrome: {e}")
        return None


def check_nodejs_installed() -> bool:
    """Check if Node.js and npm/pnpm are installed"""
    try:
        # Check Node.js
        node_result = subprocess.run(
            ["node", "--version"], capture_output=True, text=True, timeout=5
        )
        if node_result.returncode != 0:
            return False

        print_info(f"Node.js version: {node_result.stdout.strip()}")

        # Check for pnpm (preferred) or npm
        try:
            pnpm_result = subprocess.run(
                ["pnpm", "--version"], capture_output=True, text=True, timeout=5
            )
            if pnpm_result.returncode == 0:
                print_info(f"pnpm version: {pnpm_result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass

        npm_result = subprocess.run(
            ["npm", "--version"], capture_output=True, text=True, timeout=5
        )
        if npm_result.returncode == 0:
            print_info(f"npm version: {npm_result.stdout.strip()}")
            return True

        return False

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def build_extension(extension_dir: Path, dev_mode: bool = False) -> bool:
    """
    Build the Browser.AI Chrome extension

    Args:
        extension_dir: Path to extension directory
        dev_mode: Whether to build in development mode

    Returns:
        True if build successful, False otherwise
    """
    print_header("Building Chrome Extension")

    if not extension_dir.exists():
        print_error(f"Extension directory not found: {extension_dir}")
        return False

    # Check if Node.js is installed
    if not check_nodejs_installed():
        print_error("Node.js and npm/pnpm are required to build the extension")
        print_info("Please install Node.js from: https://nodejs.org/")
        return False

    # Change to extension directory
    original_dir = os.getcwd()
    os.chdir(extension_dir)

    try:
        # Check if pnpm is available
        use_pnpm = shutil.which("pnpm") is not None
        package_manager = "pnpm" if use_pnpm else "npm"

        print_info(f"Using package manager: {package_manager}")

        # Install dependencies if node_modules doesn't exist
        if not (extension_dir / "node_modules").exists():
            print_info("Installing dependencies...")
            install_cmd = [package_manager, "install"]
            result = subprocess.run(install_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print_error("Failed to install dependencies")
                print_error(result.stderr)
                return False

            print_success("Dependencies installed")

        # Build the extension
        print_info(
            f"Building extension ({'dev' if dev_mode else 'production'} mode)..."
        )
        build_cmd = [package_manager, "run", "dev" if dev_mode else "build"]

        if dev_mode:
            # For dev mode, run in background
            print_info("Starting dev server in background...")
            _ = subprocess.Popen(
                build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            time.sleep(5)  # Wait for initial build
            print_success("Dev server started")
            return True
        else:
            # For production build, wait for completion
            result = subprocess.run(build_cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print_error("Build failed")
                print_error(result.stderr)
                return False

            print_success("Extension built successfully")

            # Check if build directory exists
            build_dir = extension_dir / "build"
            if build_dir.exists():
                print_info(f"Build output: {build_dir}")
                return True
            else:
                print_error("Build directory not found")
                return False

    except Exception as e:
        print_error(f"Build failed with error: {e}")
        return False
    finally:
        os.chdir(original_dir)


def start_browser_ai_server(
    port: int = 5000, debug: bool = False
) -> Optional[subprocess.Popen]:
    """
    Start the Browser.AI Flask server

    Args:
        port: Port to run server on
        debug: Whether to run in debug mode

    Returns:
        subprocess.Popen object or None if failed
    """
    print_header("Starting Browser.AI Server")

    try:
        # Check if Flask dependencies are installed
        try:
            import importlib.util

            flask_spec = importlib.util.find_spec("flask")
            socketio_spec = importlib.util.find_spec("flask_socketio")

            if not flask_spec or not socketio_spec:
                raise ImportError("Flask dependencies not found")
        except ImportError:
            print_warning("Flask dependencies not found, installing...")
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "flask",
                    "flask-socketio",
                    "eventlet",
                ],
                check=True,
            )
            print_success("Dependencies installed")

        # Start the server
        cmd = [sys.executable, "-m", "browser_ai_gui.main", "web", "--port", str(port)]

        if debug:
            cmd.append("--debug")

        print_info(f"Starting server on port {port}...")

        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )

        # Wait for server to start
        time.sleep(3)

        print_success(f"Server started successfully (PID: {process.pid})")
        print_info(f"Server URL: http://localhost:{port}")

        return process

    except Exception as e:
        print_error(f"Failed to start server: {e}")
        return None


def open_extension_management():
    """Open Chrome extension management page"""
    print_info("Opening Chrome extension management page...")
    time.sleep(2)
    webbrowser.open("chrome://extensions/")


def print_manual_extension_instructions(extension_path: Path):
    """Print instructions for manually loading the extension"""
    print_header("Extension Loading Instructions")
    print_info("To load the Browser.AI extension in Chrome:")
    print(f"  1. Open Chrome and go to: {Colors.BOLD}chrome://extensions/{Colors.ENDC}")
    print(
        f"  2. Enable {Colors.BOLD}'Developer mode'{Colors.ENDC} (toggle in top-right)"
    )
    print(f"  3. Click {Colors.BOLD}'Load unpacked'{Colors.ENDC}")
    print(f"  4. Select the directory: {Colors.BOLD}{extension_path}{Colors.ENDC}")
    print("  5. The extension should now appear in your browser\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Browser.AI Complete Project Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_project.py                    # Run with all defaults
  python run_project.py --dev              # Build extension in dev mode
  python run_project.py --port 8000        # Use custom port
  python run_project.py --skip-build       # Skip extension build
  python run_project.py --skip-chrome      # Don't launch Chrome
        """,
    )

    parser.add_argument(
        "--dev", action="store_true", help="Build extension in development mode"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port for Browser.AI server (default: 5000)",
    )
    parser.add_argument(
        "--debug-port",
        type=int,
        default=9222,
        help="Port for Chrome remote debugging (default: 9222)",
    )
    parser.add_argument(
        "--skip-build", action="store_true", help="Skip building the extension"
    )
    parser.add_argument(
        "--skip-chrome", action="store_true", help="Don't launch Chrome browser"
    )
    parser.add_argument(
        "--chrome-path", type=str, help="Custom path to Chrome executable"
    )
    parser.add_argument(
        "--server-debug", action="store_true", help="Run server in debug mode"
    )

    args = parser.parse_args()

    # Get project root directory
    project_root = Path(__file__).parent
    extension_dir = project_root / "browser_ai_extension" / "browse_ai"

    print_header("Browser.AI Project Launcher")
    print_info(f"Project root: {project_root}")
    print_info(f"Extension directory: {extension_dir}")

    processes: List[subprocess.Popen] = []

    try:
        # Step 1: Build Extension
        if not args.skip_build:
            if not build_extension(extension_dir, args.dev):
                print_error("Extension build failed")
                return 1
        else:
            print_warning("Skipping extension build")

        # Determine extension path for Chrome
        extension_path = extension_dir / "build" if not args.dev else extension_dir

        # Step 2: Launch Chrome in Debug Mode
        chrome_process = None
        if not args.skip_chrome:
            chrome_path = args.chrome_path or find_chrome_path()

            if chrome_path:
                chrome_process = launch_chrome_debug_mode(
                    chrome_path, debug_port=args.debug_port
                )
                if chrome_process:
                    processes.append(chrome_process)

                    # Show extension loading instructions
                    if extension_path.exists():
                        print_manual_extension_instructions(extension_path)

                        # Try to open extension management page
                        try:
                            open_extension_management()
                        except Exception:
                            pass
            else:
                print_error("Chrome executable not found")
                print_info("Please specify Chrome path with --chrome-path")
        else:
            print_warning("Skipping Chrome launch")

        # Step 3: Start Browser.AI Server
        server_process = start_browser_ai_server(args.port, args.server_debug)
        if server_process:
            processes.append(server_process)
        else:
            print_error("Failed to start Browser.AI server")
            return 1

        # Success summary
        print_header("Launch Complete!")
        print_success("All components started successfully")
        print("\n" + "=" * 60)
        print(f"{Colors.BOLD}Service Status:{Colors.ENDC}")
        print(
            f"  • Chrome Debug Mode: {Colors.OKGREEN}Running on port {args.debug_port}{Colors.ENDC}"
            if not args.skip_chrome
            else f"  • Chrome: {Colors.WARNING}Skipped{Colors.ENDC}"
        )
        print(
            f"  • Browser.AI Server: {Colors.OKGREEN}Running on http://localhost:{args.port}{Colors.ENDC}"
        )
        print(f"  • Extension: {Colors.OKGREEN}Ready to load{Colors.ENDC}")
        print("=" * 60 + "\n")

        print_info(f"Press {Colors.BOLD}Ctrl+C{Colors.ENDC} to stop all services\n")

        # Keep running and monitor server output
        if server_process:
            try:
                for line in server_process.stdout:
                    print(line.rstrip())
            except KeyboardInterrupt:
                pass

    except KeyboardInterrupt:
        print_warning("\n\nShutting down...")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1
    finally:
        # Cleanup: terminate all processes
        for process in processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print_success(f"Process {process.pid} terminated")
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

        print_success("All services stopped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
