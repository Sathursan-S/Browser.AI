#!/usr/bin/env python3
"""
Demo script for Browser AI Chat Interface

This script demonstrates the key features of the chat interface system.
"""

import asyncio
import time
from browser_ai import Agent
from chat_interface import LogEventListener, ConfigManager
from chat_interface.config_manager import LLMConfig, LLMProvider


async def demo_event_system():
    """Demonstrate the event listening system"""
    print("🎯 Demo: Event Listener System")
    print("=" * 50)
    
    # Create event listener
    listener = LogEventListener()
    listener.start_listening()
    
    # Set up event handlers
    def on_log(event):
        print(f"📋 [{event.timestamp.strftime('%H:%M:%S')}] {event.level.value.upper()}: {event.message}")
    
    def on_task_update(update):
        print(f"🎯 Task {update.task_id}: {update.status.value} (Step {update.step_number})")
        if update.result:
            print(f"✅ Result: {update.result[:100]}...")
    
    listener.subscribe_to_logs(on_log)
    listener.subscribe_to_tasks(on_task_update)
    
    print("✅ Event listener started and subscribed")
    
    # Simulate some events
    from chat_interface.event_listener import LogEvent, LogLevel, TaskStatus, TaskUpdate
    from datetime import datetime
    
    # Simulate log events
    test_event = LogEvent(
        timestamp=datetime.now(),
        level=LogLevel.INFO,
        message="Demo: Browser automation started",
        source="demo",
        task_status=TaskStatus.RUNNING
    )
    listener._emit_log_event(test_event)
    
    # Simulate task update
    test_update = TaskUpdate(
        task_id="demo-task-123",
        status=TaskStatus.RUNNING,
        step_number=1,
        total_steps=5,
        current_action="Navigating to website",
        result=None,
        error=None,
        timestamp=datetime.now()
    )
    listener._emit_task_update(test_update)
    
    print("✅ Demo events emitted")
    time.sleep(1)
    
    # Get recent events
    recent_events = listener.get_recent_events(10)
    print(f"📊 Retrieved {len(recent_events)} recent events")
    
    listener.stop_listening()
    print("🛑 Event listener stopped")
    print()


def demo_config_system():
    """Demonstrate the configuration system"""
    print("⚙️ Demo: Configuration Management")
    print("=" * 50)
    
    # Create config manager
    config = ConfigManager()
    
    # Show existing configs
    existing_configs = config.get_llm_configs()
    print(f"📋 Found {len(existing_configs)} existing LLM configurations:")
    
    for name, llm_config in existing_configs.items():
        print(f"  • {name}: {llm_config.provider.value} - {llm_config.model}")
    
    # Add a demo config (Ollama - no API key needed)
    demo_config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="llama3.2",
        base_url="http://localhost:11434",
        temperature=0.1
    )
    
    config.add_llm_config("demo_ollama", demo_config)
    print("✅ Added demo Ollama configuration")
    
    # Show app configuration
    app_config = config.get_app_config()
    print(f"🎨 App theme: {app_config.theme}")
    print(f"📝 Auto-save: {app_config.auto_save}")
    print(f"📊 Log level: {app_config.log_level}")
    
    # Update app config
    config.update_app_config(theme="dark", max_history_items=50)
    print("✅ Updated app configuration")
    
    # Show available models
    openai_models = config.get_available_models(LLMProvider.OPENAI)
    print(f"🤖 OpenAI models available: {len(openai_models)}")
    print(f"  Examples: {openai_models[:3]}")
    
    print()


def demo_integration():
    """Demonstrate Browser AI integration"""
    print("🔗 Demo: Browser AI Integration")  
    print("=" * 50)
    
    # This demo shows how the chat interface would integrate with Browser AI
    # without actually running browser automation (which requires display)
    
    print("🎯 Chat Interface Integration Points:")
    print("  1. Event Listener hooks into Browser AI logging")
    print("  2. Agent callbacks provide real-time updates")
    print("  3. Configuration manager handles LLM setup")
    print("  4. Web/Desktop apps provide user interfaces")
    
    print("\n🔄 Typical workflow:")
    print("  1. User configures LLM in interface")
    print("  2. User types natural language task")
    print("  3. System creates Browser AI Agent")
    print("  4. Agent runs with real-time callbacks")
    print("  5. Progress streamed to chat interface")
    print("  6. Results displayed with formatting")
    
    print("\n💬 Example chat interaction:")
    print("  User: 'Search for Python tutorials on Google'")
    print("  System: 🔄 Starting task execution...")
    print("  System: [12:34:56] 🔵 Step 1: Navigating to Google...")
    print("  System: [12:34:58] 🔵 Step 2: Searching for 'Python tutorials'...")
    print("  System: [12:35:02] 🟢 ✅ Task Completed")
    print("  System: Found 10 Python tutorial results on Google")
    
    print()


def demo_interfaces():
    """Demonstrate interface capabilities"""
    print("🖥️ Demo: Interface Features")
    print("=" * 50)
    
    print("🌐 Web Interface (Gradio):")
    print("  • Modern web-based chat UI")
    print("  • Real-time log streaming")
    print("  • LLM configuration panel")
    print("  • Auto-refreshing status updates")
    print("  • Mobile-responsive design")
    print("  • Launch: python launch_web.py")
    
    print("\n🖥️ Desktop Interface (Qt):")
    print("  • Native desktop application")
    print("  • Chat panel with message bubbles")
    print("  • Configuration sidebar")
    print("  • Real-time log display")
    print("  • System tray integration")
    print("  • Launch: python launch_desktop.py")
    
    print("\n🔧 Configuration Features:")
    print("  • Multiple LLM providers (OpenAI, Claude, Ollama)")
    print("  • API key management")
    print("  • Temperature and parameter controls")
    print("  • Configuration validation")
    print("  • Persistent storage")
    
    print("\n📊 Monitoring Features:")
    print("  • Real-time log streaming")
    print("  • Animated status indicators")
    print("  • Task progress tracking")
    print("  • Error handling and reporting")
    print("  • History management")
    
    print()


async def main():
    """Run all demonstrations"""
    print("🚀 Browser AI Chat Interface Demonstration")
    print("=" * 60)
    print()
    
    # Run demonstrations
    await demo_event_system()
    demo_config_system()
    demo_integration()
    demo_interfaces()
    
    print("✅ All demonstrations completed!")
    print("\n🎯 Next Steps:")
    print("1. Configure your LLM API keys")
    print("2. Launch the web or desktop interface")
    print("3. Start chatting to control browser automation")
    print("\nFor more information, see: chat_interface/README.md")


if __name__ == "__main__":
    asyncio.run(main())