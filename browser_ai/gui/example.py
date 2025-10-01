"""
Example script demonstrating the Browser.AI Chat Interface GUI.

This script shows how to use the new chat interface functionality
with browser automation.
"""

import asyncio
import os
from browser_ai import create_agent_with_gui, run_agent_with_gui

# Example using create_agent_with_gui (manual control)
async def example_manual_control():
    """Example of manual control with GUI"""
    print("🚀 Starting Browser.AI with Chat Interface (Manual Control)")
    
    # This would typically use a real LLM - using a mock for demo
    class MockLLM:
        def __init__(self):
            pass
        
        async def ainvoke(self, messages):
            # Mock response for demonstration
            class MockResponse:
                content = '{"current_state": {"page_summary": "Demo page", "evaluation_previous_goal": "Starting demo", "memory": "Demo started", "next_goal": "Demo navigation"}, "action": [{"click_element": {"index": 1}}]}'
                tool_calls = []
            return MockResponse()
    
    # Create agent with GUI
    agent, chat_gui = create_agent_with_gui(
        task="Navigate to example.com and extract the main heading",
        llm=MockLLM(),
        gui_port=7860,
        gui_title="Browser.AI Demo - Manual Control"
    )
    
    print("✅ GUI launched! Open http://localhost:7860 in your browser")
    print("   The chat interface will show automation progress in real-time")
    
    # Simulate some manual updates to demonstrate the GUI
    await asyncio.sleep(2)
    
    # You can manually add messages for demonstration
    chat_gui.add_message("📱 Demo Mode", "This is a demonstration of the chat interface")
    chat_gui.add_message("🔧 Setup Complete", "Ready for browser automation")
    
    # In real usage, you would run: await agent.run(max_steps=10)
    print("💡 In real usage, call: await agent.run(max_steps=10)")
    print("💡 The GUI will stay active and show all automation steps")
    
    return agent, chat_gui

# Example using run_agent_with_gui (automated)  
async def example_automated():
    """Example of automated run with GUI"""
    print("🚀 Starting Browser.AI with Chat Interface (Automated)")
    
    # Mock LLM for demo purposes
    class MockLLM:
        async def ainvoke(self, messages):
            class MockResponse:
                content = '{"current_state": {"page_summary": "Demo", "evaluation_previous_goal": "Success", "memory": "Task completed", "next_goal": "done"}, "action": [{"done": {"extracted_content": "Demo completed successfully"}}]}'
                tool_calls = []
            return MockResponse()
    
    # This will create agent, launch GUI, and run automation
    history = await run_agent_with_gui(
        task="Demo task - extract content from example.com", 
        llm=MockLLM(),
        max_steps=5,
        gui_port=7861,  # Different port to avoid conflicts
        gui_title="Browser.AI Demo - Automated"
    )
    
    print("✅ Automation completed!")
    print(f"📊 Total steps: {len(history.history)}")
    
    return history

def print_usage_instructions():
    """Print usage instructions for the GUI"""
    print("\n" + "="*60)
    print("🎨 Browser.AI Chat Interface GUI - Usage Instructions")
    print("="*60)
    print()
    print("1. 📦 Import the GUI functions:")
    print("   from browser_ai import create_agent_with_gui, run_agent_with_gui, BrowserAIChat")
    print()
    print("2. 🚀 Quick Start - Automated Run:")
    print("   history = await run_agent_with_gui(")
    print("       task='Your automation task',")
    print("       llm=your_llm_instance,")
    print("       gui_port=7860")
    print("   )")
    print()
    print("3. 🔧 Manual Control:")
    print("   agent, gui = create_agent_with_gui(")
    print("       task='Your task',") 
    print("       llm=your_llm_instance")
    print("   )")
    print("   history = await agent.run(max_steps=10)")
    print()
    print("4. 🎯 GUI Features:")
    print("   • Real-time automation progress")
    print("   • Formatted step-by-step logs")
    print("   • Action results and extracted content")
    print("   • Error tracking and debugging info") 
    print("   • Browser state updates")
    print("   • Task completion status")
    print()
    print("5. 🌐 Access the GUI:")
    print("   Open http://localhost:7860 in your browser")
    print("   The interface will update automatically as automation runs")
    print()
    print("="*60)

if __name__ == "__main__":
    print_usage_instructions()
    
    # Choose which example to run
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        print("\n🎮 Running demo examples...")
        
        # Run manual control example
        asyncio.run(example_manual_control())
        
        # Wait a bit before running automated example
        print("\nPress Enter to run automated example...")
        input()
        
        # Run automated example
        asyncio.run(example_automated())
    else:
        print("\n💡 To run the demos, use: python gui_example.py demo")
        print("   Make sure you have the required LLM setup first!")