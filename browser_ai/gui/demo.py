#!/usr/bin/env python3
"""
Browser.AI Chat Interface Demo

This script demonstrates the Browser.AI Chat Interface GUI functionality
with a realistic simulation of browser automation workflow.

Run this script to see how the chat interface displays logs, steps, and results
in real-time during browser automation tasks.
"""

import asyncio
import time
import threading
from datetime import datetime

try:
    from browser_ai.gui.chat_interface import BrowserAIChat
    FULL_INTEGRATION = True
except ImportError:
    print("⚠️ Full Browser.AI not available. Using standalone demo...")
    FULL_INTEGRATION = False
    
    # Standalone version
    import gradio as gr
    from test_simple_gui import SimpleChatTest as BrowserAIChat


class BrowserAutomationDemo:
    """Simulated browser automation with real-time GUI updates"""
    
    def __init__(self):
        if FULL_INTEGRATION:
            self.chat_gui = BrowserAIChat(
                title="Browser.AI Demo - Real-time Automation Chat",
                port=7866
            )
        else:
            # Standalone version doesn't have port parameter
            self.chat_gui = BrowserAIChat("Browser.AI Demo - Real-time Automation Chat")
        self.is_running = False
        
    def setup_and_launch_gui(self):
        """Setup and launch the GUI"""
        print("🚀 Setting up Browser.AI Chat Interface...")
        
        if hasattr(self.chat_gui, 'launch'):
            self.chat_gui.launch(share=False, debug=False)
        else:
            # Fallback for standalone demo
            demo = self.chat_gui.setup_interface()
            demo.launch(server_port=7866, share=False, prevent_thread_lock=True)
        
        print("✅ GUI launched at http://localhost:7866")
        return self.chat_gui
    
    async def simulate_browser_automation(self):
        """Simulate a realistic browser automation workflow"""
        print("\n🎯 Starting simulated browser automation...")
        
        # Set the task
        task = "Navigate to a news website, find trending articles, and extract headlines"
        self.chat_gui.set_task(task)
        print(f"📋 Task: {task}")
        
        await asyncio.sleep(1)
        
        # Step 1: Navigate to website
        self.chat_gui.add_step_info(1, "Navigate to example-news.com", [])
        await asyncio.sleep(2)
        
        # Simulate browser state update
        if hasattr(self.chat_gui, 'add_browser_state'):
            mock_state = type('MockState', (), {
                'url': 'https://example-news.com',
                'title': 'Example News - Latest Headlines',
                'selector_map': {str(i): f'element_{i}' for i in range(15)}
            })()
            self.chat_gui.add_browser_state(mock_state)
        else:
            self.chat_gui.add_result("info", "Page loaded: https://example-news.com")
        
        await asyncio.sleep(1)
        
        # Step 2: Find trending section
        self.chat_gui.add_step_info(2, "Locate trending articles section", [
            {"scroll": {"direction": "down"}},
            {"click_element": {"index": 5}}
        ])
        await asyncio.sleep(2)
        
        self.chat_gui.add_result("success", "Found trending section with 12 articles")
        await asyncio.sleep(1)
        
        # Step 3: Extract headlines
        self.chat_gui.add_step_info(3, "Extract article headlines", [
            {"extract_content": {"goal": "Get all article headlines"}},
            {"scroll": {"direction": "down"}}
        ])
        await asyncio.sleep(3)
        
        # Simulate extracted content
        headlines = [
            "Breaking: Major Tech Conference Announces AI Breakthroughs",
            "Climate Summit Reaches Historic Agreement",
            "Sports: Championship Finals Set for This Weekend",
            "Economy: Market Shows Strong Recovery Signs",
            "Health: New Study Reveals Important Findings"
        ]
        
        headlines_text = "\n".join([f"• {headline}" for headline in headlines])
        self.chat_gui.add_result("success", f"Extracted {len(headlines)} headlines:\n{headlines_text}")
        await asyncio.sleep(1)
        
        # Step 4: Analyze content
        self.chat_gui.add_step_info(4, "Analyze and categorize headlines", [])
        await asyncio.sleep(2)
        
        categories = {
            "Technology": 1,
            "Environment": 1, 
            "Sports": 1,
            "Economy": 1,
            "Health": 1
        }
        
        analysis = "\n".join([f"• {cat}: {count} article(s)" for cat, count in categories.items()])
        self.chat_gui.add_result("info", f"Content analysis:\n{analysis}")
        await asyncio.sleep(1)
        
        # Step 5: Complete task
        self.chat_gui.add_step_info(5, "Finalize and export results", [
            {"extract_content": {"goal": "Create summary report"}}
        ])
        await asyncio.sleep(1)
        
        # Task completion
        if hasattr(self.chat_gui, 'task_completed'):
            mock_history = type('MockHistory', (), {'history': [None] * 5})()
            self.chat_gui.task_completed(mock_history)
        else:
            self.chat_gui.task_completed()
        
        final_summary = f"""
**Automation Summary:**
• Successfully navigated to example-news.com
• Located and analyzed trending articles section  
• Extracted {len(headlines)} article headlines
• Categorized content into {len(categories)} topics
• Generated comprehensive report

**Headlines Found:**
{headlines_text}

✅ Task completed successfully in 5 steps!
        """.strip()
        
        self.chat_gui.add_result("success", final_summary)
        
        print("✅ Simulated automation completed!")
        return headlines
    
    async def run_interactive_demo(self):
        """Run interactive demo with user controls"""
        print("\n🎮 Interactive Demo Mode")
        print("Available commands:")
        print("  start - Start automation simulation")
        print("  step <n> <goal> - Add a custom step") 
        print("  result <type> <message> - Add a result (success/error/info)")
        print("  task <description> - Set a new task")
        print("  quit - Exit demo")
        
        while True:
            try:
                command = input("\nDemo> ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "start":
                    await self.simulate_browser_automation()
                elif command.startswith("step "):
                    parts = command.split(" ", 2)
                    if len(parts) >= 3:
                        try:
                            step_num = int(parts[1])
                            goal = parts[2]
                            self.chat_gui.add_step_info(step_num, goal, [])
                            print(f"✅ Added step {step_num}: {goal}")
                        except ValueError:
                            print("❌ Invalid step number")
                elif command.startswith("result "):
                    parts = command.split(" ", 2)
                    if len(parts) >= 3:
                        result_type = parts[1]
                        message = parts[2]
                        self.chat_gui.add_result(result_type, message)
                        print(f"✅ Added {result_type} result: {message[:50]}...")
                elif command.startswith("task "):
                    task = command[5:]
                    self.chat_gui.set_task(task)
                    print(f"✅ Set new task: {task}")
                elif command == "help":
                    print("Available commands: start, step, result, task, quit")
                else:
                    print("❓ Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("👋 Demo ended")


async def main():
    """Main demo function"""
    print("=" * 60)
    print("🎨 Browser.AI Chat Interface Demo")
    print("=" * 60)
    
    demo = BrowserAutomationDemo()
    
    # Launch GUI
    demo.setup_and_launch_gui()
    
    print("\n📱 GUI is now running! Open http://localhost:7866 to see the interface")
    print("   The chat will show real-time updates as automation runs...")
    
    # Wait a moment for GUI to fully load
    await asyncio.sleep(3)
    
    # Choose demo mode
    print("\n🎮 Demo Modes:")
    print("1. Automated simulation (runs predefined automation sequence)")
    print("2. Interactive mode (control the demo manually)")
    print("3. Just keep GUI running (no simulation)")
    
    try:
        choice = input("Choose mode (1-3): ").strip()
        
        if choice == "1":
            print("\n🤖 Running automated simulation...")
            await demo.simulate_browser_automation()
            
            print("\n💡 Simulation completed! Check the GUI at http://localhost:7866")
            print("   The chat shows the complete automation workflow.")
            
            # Keep GUI running
            print("\nPress Ctrl+C to stop the demo...")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Demo stopped")
                
        elif choice == "2":
            await demo.run_interactive_demo()
            
        elif choice == "3":
            print("\n🌐 GUI is running at http://localhost:7866")
            print("   You can interact with the interface manually.")
            print("\nPress Ctrl+C to stop...")
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Demo stopped")
        else:
            print("❓ Invalid choice. Keeping GUI running...")
            
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
    except Exception as e:
        print(f"❌ Demo error: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()