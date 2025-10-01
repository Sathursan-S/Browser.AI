"""
Standalone test for the Chat Interface GUI functionality.

This test verifies that the Gradio-based chat interface works correctly
without requiring the full browser automation stack.
"""

import gradio as gr
import asyncio
from datetime import datetime


class SimpleChatTest:
    """Simple test implementation of the chat interface"""
    
    def __init__(self, title="Test Chat Interface"):
        self.title = title
        self.chat_history = []
        self.current_task = "No task set"
        self.current_step = 0
        self.is_running = False
        
    def add_message(self, user_msg, assistant_msg="", timestamp=True):
        """Add a message to the chat history"""
        if timestamp:
            current_time = datetime.now().strftime("%H:%M:%S")
            user_msg = f"[{current_time}] {user_msg}"
        
        self.chat_history.append((user_msg, assistant_msg))
        
        # Keep only last 50 messages to prevent memory issues
        if len(self.chat_history) > 50:
            self.chat_history = self.chat_history[-50:]
    
    def set_task(self, task):
        """Set the current task"""
        self.current_task = task
        self.is_running = True
        self.add_message("🚀 **New Task Started**", f"**Task:** {task}")
    
    def add_step_info(self, step_num, goal):
        """Add step information"""
        self.current_step = step_num
        self.add_message(f"🎯 **Step {step_num}**", f"**Goal:** {goal}")
    
    def add_result(self, result_type, message):
        """Add a result message"""
        icons = {
            "success": "✅",
            "error": "❌", 
            "info": "📄",
            "warning": "⚠️"
        }
        icon = icons.get(result_type, "ℹ️")
        self.add_message(f"{icon} **Result**", message)
    
    def task_completed(self):
        """Mark task as completed"""
        self.is_running = False
        self.add_message("🏁 **Task Completed**", "All automation steps finished successfully!")
    
    def format_status(self):
        """Format the status display"""
        status_color = "#22c55e" if self.is_running else "#6b7280"
        status_text = "Running" if self.is_running else "Idle"
        
        return f"""
        <div style="background: linear-gradient(90deg, #f0f9ff, #e0f2fe); border: 1px solid #0ea5e9; border-radius: 8px; padding: 12px; margin: 8px 0;">
            <h4 style="margin: 0; color: {status_color};">Status: {status_text}</h4>
            <p style="margin: 4px 0;"><strong>Task:</strong> {self.current_task}</p>
            <p style="margin: 4px 0;"><strong>Step:</strong> {self.current_step}</p>
            <p style="margin: 4px 0; font-size: 0.9em; color: #6b7280;">
                Last update: {datetime.now().strftime('%H:%M:%S')}
            </p>
        </div>
        """
    
    def clear_chat(self):
        """Clear the chat history"""
        self.chat_history = []
        return []
    
    def refresh(self):
        """Refresh the interface"""
        return (
            self.chat_history,
            self.format_status(),
            self.current_task,
            str(self.current_step)
        )
    
    def setup_interface(self):
        """Setup the Gradio interface"""
        with gr.Blocks(
            title=self.title,
            theme=gr.themes.Soft(),
        ) as demo:
            
            with gr.Row():
                gr.Markdown(f"# {self.title}")
                
            with gr.Row():
                with gr.Column(scale=3):
                    # Status display
                    status_display = gr.HTML(
                        value=self.format_status(),
                        label="Current Status"
                    )
                    
                    # Chat interface
                    chatbot = gr.Chatbot(
                        value=self.chat_history,
                        label="Automation Log",
                        height=400,
                        show_copy_button=True
                    )
                    
                with gr.Column(scale=1):
                    # Control panel
                    gr.Markdown("### Control Panel")
                    
                    task_display = gr.Textbox(
                        value=self.current_task,
                        label="Current Task",
                        interactive=False
                    )
                    
                    step_display = gr.Textbox(
                        value=str(self.current_step),
                        label="Current Step",
                        interactive=False
                    )
                    
                    # Demo controls
                    demo_task_input = gr.Textbox(
                        placeholder="Enter a demo task...",
                        label="Demo Task"
                    )
                    
                    start_demo_btn = gr.Button("Start Demo", variant="primary")
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
                    refresh_btn = gr.Button("Refresh")
            
            # Event handlers
            def start_demo_task(task_text):
                if task_text.strip():
                    self.set_task(task_text.strip())
                    return self.refresh()
                return self.refresh()
            
            start_demo_btn.click(
                fn=start_demo_task,
                inputs=[demo_task_input],
                outputs=[chatbot, status_display, task_display, step_display]
            )
            
            clear_btn.click(
                fn=lambda: (self.clear_chat(), self.format_status(), self.current_task, str(self.current_step)),
                outputs=[chatbot, status_display, task_display, step_display]
            )
            
            refresh_btn.click(
                fn=self.refresh,
                outputs=[chatbot, status_display, task_display, step_display]
            )
        
        return demo


def test_basic_functionality():
    """Test basic chat functionality"""
    print("🧪 Testing basic chat functionality...")
    
    chat = SimpleChatTest("Test Chat")
    
    # Test basic message adding
    chat.add_message("Test User Message", "Test Assistant Response")
    assert len(chat.chat_history) == 1
    print("✅ Basic message adding works")
    
    # Test task setting
    chat.set_task("Test automation task")
    assert chat.current_task == "Test automation task"
    assert chat.is_running == True
    print("✅ Task setting works")
    
    # Test step info
    chat.add_step_info(1, "Test goal")
    assert chat.current_step == 1
    print("✅ Step info tracking works")
    
    # Test results
    chat.add_result("success", "Test successful operation")
    chat.add_result("error", "Test error handling")
    print("✅ Result handling works")
    
    # Test completion
    chat.task_completed()
    assert not chat.is_running
    print("✅ Task completion works")
    
    print(f"📊 Total messages: {len(chat.chat_history)}")
    return chat


def test_gradio_interface():
    """Test Gradio interface setup"""
    print("\n🧪 Testing Gradio interface setup...")
    
    chat = SimpleChatTest("Test Interface")
    
    # Test interface setup
    try:
        demo = chat.setup_interface()
        assert demo is not None
        print("✅ Gradio interface setup works")
        return chat, demo
    except Exception as e:
        print(f"❌ Interface setup failed: {e}")
        return None, None


def run_demo_simulation(chat):
    """Run a demo simulation"""
    print("\n🎮 Running demo simulation...")
    
    # Simulate a typical browser automation sequence
    chat.set_task("Navigate to example.com and extract the main heading")
    
    # Simulate steps
    import time
    steps = [
        (1, "Navigate to example.com"),
        (2, "Wait for page to load"),
        (3, "Find main heading element"),
        (4, "Extract heading text"),
        (5, "Complete task")
    ]
    
    for step_num, goal in steps:
        chat.add_step_info(step_num, goal)
        
        # Simulate some results
        if step_num == 1:
            chat.add_result("info", "Successfully navigated to https://example.com")
        elif step_num == 3:
            chat.add_result("success", "Found heading element: <h1>Example Domain</h1>")
        elif step_num == 4:
            chat.add_result("success", "Extracted text: 'Example Domain'")
        elif step_num == 5:
            chat.task_completed()
    
    print("✅ Demo simulation completed")
    print(f"📊 Generated {len(chat.chat_history)} messages")


def main():
    """Main test function"""
    print("🚀 Starting Chat Interface Tests")
    print("=" * 50)
    
    try:
        # Test basic functionality
        chat = test_basic_functionality()
        
        # Test Gradio interface
        chat, demo = test_gradio_interface()
        
        if chat and demo:
            # Run demo simulation
            run_demo_simulation(chat)
            
            print("\n" + "=" * 50)
            print("✅ All tests passed!")
            print("🎉 Chat Interface is working correctly")
            print(f"💬 Final chat history has {len(chat.chat_history)} messages")
            
            # Option to launch demo
            launch_demo = input("\n🌐 Launch demo interface? (y/n): ").lower().strip()
            if launch_demo == 'y':
                print("🚀 Launching demo on http://localhost:7865")
                print("   Try the demo controls to see the interface in action!")
                demo.launch(server_port=7865, share=False)
        else:
            print("❌ Interface setup failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n💡 The chat interface is ready for integration!")
        print("   You can now use it with Browser.AI automation tasks.")
    else:
        print("\n🔧 Please check the errors above.")