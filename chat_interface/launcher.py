#!/usr/bin/env python3

"""
Browser.AI Chat Interface Launcher

Quick launcher script to start the backend and optionally open the GUI.
"""

import subprocess
import sys
import time
import webbrowser
from pathlib import Path
import argparse
import signal
import os

def main():
    parser = argparse.ArgumentParser(description='Launch Browser.AI Chat Interface')
    parser.add_argument('--backend-only', action='store_true', 
                       help='Start only the backend server')
    parser.add_argument('--streamlit', action='store_true',
                       help='Start Streamlit GUI after backend')
    parser.add_argument('--web-app', action='store_true',
                       help='Start backend and open web app in browser')
    parser.add_argument('--port', type=int, default=8000,
                       help='Backend server port (default: 8000)')
    parser.add_argument('--host', default='localhost',
                       help='Backend server host (default: localhost)')
    
    args = parser.parse_args()
    
    # Change to the correct directory
    script_dir = Path(__file__).parent
    backend_dir = script_dir / 'backend'
    streamlit_dir = script_dir / 'streamlit_gui'
    
    print("🚀 Starting Browser.AI Chat Interface...")
    
    # Set environment variables
    env = os.environ.copy()
    env['CHAT_INTERFACE_HOST'] = args.host
    env['CHAT_INTERFACE_PORT'] = str(args.port)
    
    try:
        # Start backend
        print(f"\n📡 Starting backend server on {args.host}:{args.port}...")
        backend_process = subprocess.Popen([
            sys.executable, 'main.py'
        ], cwd=backend_dir, env=env)
        
        # Wait a bit for backend to start
        time.sleep(3)
        
        if args.backend_only:
            print(f"✅ Backend server started at http://{args.host}:{args.port}")
            print("Press Ctrl+C to stop the server...")
            backend_process.wait()
            
        elif args.streamlit:
            print("\n🎨 Starting Streamlit GUI...")
            streamlit_process = subprocess.Popen([
                sys.executable, '-m', 'streamlit', 'run', 'main.py', 
                '--server.headless', 'true'
            ], cwd=streamlit_dir)
            
            print("✅ Services started:")
            print(f"   - Backend: http://{args.host}:{args.port}")
            print(f"   - Streamlit GUI: http://localhost:8501")
            
            def signal_handler(sig, frame):
                print("\n🛑 Shutting down services...")
                backend_process.terminate()
                streamlit_process.terminate()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            
            try:
                backend_process.wait()
            except KeyboardInterrupt:
                signal_handler(None, None)
                
        elif args.web_app:
            print("\n🌐 Opening web app in browser...")
            time.sleep(1)  # Give backend a moment to fully start
            webbrowser.open(f"http://{args.host}:{args.port}/app")
            
            print("✅ Services started:")
            print(f"   - Backend: http://{args.host}:{args.port}")
            print(f"   - Web App: http://{args.host}:{args.port}/app")
            print("\nPress Ctrl+C to stop the server...")
            
            try:
                backend_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Shutting down server...")
                backend_process.terminate()
        
        else:
            # Default: start backend and show options
            print("✅ Backend server started!")
            print(f"\n🌐 Available interfaces:")
            print(f"   - Web App: http://{args.host}:{args.port}/app")
            print(f"   - API Docs: http://{args.host}:{args.port}/docs")
            print(f"   - Health Check: http://{args.host}:{args.port}/health")
            print(f"\n🎨 To start Streamlit GUI:")
            print(f"   python launcher.py --streamlit")
            print(f"\nPress Ctrl+C to stop the server...")
            
            try:
                backend_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 Shutting down server...")
                backend_process.terminate()
                
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()