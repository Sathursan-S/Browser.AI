#!/usr/bin/env python3
"""
Simple example showing Browser AI chat interface integration.

This example demonstrates how to use the chat interface with Browser AI
for basic browser automation tasks.
"""

import asyncio
import os
from browser_ai import Agent, Browser
from chat_interface import LogEventListener, ConfigManager
from chat_interface.event_listener import TaskStatus
from chat_interface.config_manager import LLMConfig, LLMProvider


async def example_with_event_streaming():
    """Example of running Browser AI with real-time event streaming"""
    print("🌐 Browser AI Chat Integration Example")
    print("=" * 50)
    
    # Set up event listener for real-time updates
    event_listener = LogEventListener()
    event_listener.start_listening()
    
    # Subscribe to events
    def on_log_event(event):
        timestamp = event.timestamp.strftime("%H:%M:%S")
        status_icons = {
            "idle": "⚪", "running": "🔵", "paused": "🟡", 
            "completed": "🟢", "failed": "🔴"
        }
        icon = status_icons.get(event.task_status.value, "⚪")
        print(f"📋 [{timestamp}] {icon} {event.message}")
    
    def on_task_update(update):
        if update.current_action:
            print(f"🎯 Step {update.step_number}: {update.current_action}")
        if update.result:
            print(f"✅ Result: {update.result}")
        if update.error:
            print(f"❌ Error: {update.error}")
    
    event_listener.subscribe_to_logs(on_log_event)
    event_listener.subscribe_to_tasks(on_task_update)
    
    # Set up configuration
    config_manager = ConfigManager()
    
    # Check if we have any LLM configured
    llm_configs = config_manager.get_llm_configs()
    if not llm_configs:
        print("❌ No LLM configurations found!")
        print("📝 Please configure an LLM first:")
        print("   1. Set OPENAI_API_KEY environment variable, or")
        print("   2. Set ANTHROPIC_API_KEY environment variable, or")
        print("   3. Start Ollama server with: ollama serve")
        return
    
    # Use the first available LLM config
    config_name = list(llm_configs.keys())[0]
    llm_config = llm_configs[config_name]
    
    print(f"🤖 Using LLM: {config_name} ({llm_config.provider.value} - {llm_config.model})")
    
    try:
        # Create LLM instance
        llm = config_manager.create_llm_instance(llm_config)
        
        # Create browser (this would normally be visible)
        browser = Browser()
        
        # Define a simple task
        task = "Go to https://httpbin.org/get and extract the returned JSON data"
        
        print(f"📋 Task: {task}")
        print("🔄 Starting execution...")
        
        # Create agent with event callbacks
        agent = Agent(
            task=task,
            llm=llm,
            browser=browser,
            register_new_step_callback=event_listener.handle_agent_step,
            register_done_callback=event_listener.handle_agent_done,
            generate_gif=False  # Disable GIF for this example
        )
        
        # Set initial task status
        event_listener.set_task_status("example-task", TaskStatus.RUNNING, 0)
        
        # Run the agent
        history = await agent.run(max_steps=10)
        
        # Process results
        if history.history:
            last_result = history.history[-1]
            if last_result.result:
                for result in last_result.result:
                    if result.is_done:
                        print("\n🎉 Task completed successfully!")
                        print(f"📄 Final result: {result.extracted_content}")
                        break
                    elif result.error:
                        print(f"\n❌ Task failed: {result.error}")
                        break
        
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        print("💡 This might be because:")
        print("   • No display available (headless environment)")
        print("   • Browser not installed (run: playwright install)")
        print("   • Network connectivity issues")
        print("   • LLM API issues")
        
    finally:
        event_listener.stop_listening()
        if 'browser' in locals():
            await browser.close()


def example_config_setup():
    """Example of setting up LLM configurations"""
    print("\n⚙️ LLM Configuration Example")
    print("=" * 50)
    
    config_manager = ConfigManager()
    
    # Example: Add OpenAI configuration
    if os.getenv('OPENAI_API_KEY'):
        openai_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4o-mini",
            api_key=os.getenv('OPENAI_API_KEY'),
            temperature=0.1
        )
        config_manager.add_llm_config("openai_example", openai_config)
        print("✅ Added OpenAI configuration")
    
    # Example: Add Anthropic configuration  
    if os.getenv('ANTHROPIC_API_KEY'):
        claude_config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-sonnet-20241022",
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            temperature=0.1
        )
        config_manager.add_llm_config("claude_example", claude_config)
        print("✅ Added Anthropic Claude configuration")
    
    # Example: Add Ollama configuration (no API key needed)
    ollama_config = LLMConfig(
        provider=LLMProvider.OLLAMA,
        model="llama3.2",
        base_url="http://localhost:11434",
        temperature=0.1
    )
    config_manager.add_llm_config("ollama_example", ollama_config)
    print("✅ Added Ollama configuration")
    
    # Show all configurations
    all_configs = config_manager.get_llm_configs()
    print(f"\n📋 Total configurations: {len(all_configs)}")
    for name, config in all_configs.items():
        print(f"  • {name}: {config.provider.value} - {config.model}")


async def main():
    """Run the example"""
    print("🤖 Browser AI Chat Interface Integration Example")
    print("🔗 This demonstrates how the chat interface works with Browser AI")
    print("=" * 70)
    
    # Set up configurations
    example_config_setup()
    
    # Run browser automation with event streaming
    print("\n" + "=" * 70)
    await example_with_event_streaming()
    
    print("\n" + "=" * 70)
    print("✅ Example completed!")
    print("\n💡 To use the full chat interface:")
    print("   🌐 Web interface: python launch_web.py") 
    print("   🖥️ Desktop interface: python launch_desktop.py")
    print("\n📚 For more examples, see: chat_interface/README.md")


if __name__ == "__main__":
    asyncio.run(main())