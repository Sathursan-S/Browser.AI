"""
Web-based chat interface for Browser AI using Gradio.

Provides a GitHub Copilot-like chat interface for browser automation.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import threading
import time

import gradio as gr
from browser_ai import Agent, Browser

from .event_listener import LogEventListener, TaskStatus, LogEvent, TaskUpdate
from .config_manager import ConfigManager, LLMConfig, LLMProvider


class WebChatInterface:
    """Web-based chat interface for Browser AI"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.event_listener = LogEventListener()
        self.current_agent: Optional[Agent] = None
        self.current_browser: Optional[Browser] = None
        self.task_history: List[Dict[str, Any]] = []
        self.current_task_id: Optional[str] = None
        self.running_task = False
        
        # Start event listener
        self.event_listener.start_listening()
        
        # Subscribe to events for UI updates
        self.chat_messages: List[Dict[str, str]] = []  # List of message dicts with role/content
        self.log_buffer: List[str] = []
        
        self.event_listener.subscribe_to_logs(self._on_log_event)
        self.event_listener.subscribe_to_tasks(self._on_task_update)
    
    def _on_log_event(self, event: LogEvent):
        """Handle log events from the event listener"""
        timestamp = event.timestamp.strftime("%H:%M:%S")
        status_icon = {
            TaskStatus.IDLE: "⚪",
            TaskStatus.RUNNING: "🔵", 
            TaskStatus.PAUSED: "🟡",
            TaskStatus.COMPLETED: "🟢",
            TaskStatus.FAILED: "🔴"
        }.get(event.task_status, "⚪")
        
        log_message = f"[{timestamp}] {status_icon} {event.message}"
        self.log_buffer.append(log_message)
        
        # Keep only last 100 log messages
        if len(self.log_buffer) > 100:
            self.log_buffer.pop(0)
    
    def _on_task_update(self, update: TaskUpdate):
        """Handle task updates from the event listener"""
        if update.status == TaskStatus.COMPLETED:
            self.running_task = False
            if update.result:
                self.chat_messages.append({"role": "assistant", "content": f"✅ **Task Completed**\n\n{update.result}"})
        elif update.status == TaskStatus.FAILED:
            self.running_task = False
            error_msg = update.error or "Unknown error occurred"
            self.chat_messages.append({"role": "assistant", "content": f"❌ **Task Failed**\n\n{error_msg}"})
    
    def _get_available_llm_configs(self) -> List[str]:
        """Get list of available LLM configurations"""
        configs = self.config_manager.get_llm_configs()
        return list(configs.keys()) if configs else ["No LLM configured"]
    
    def _create_agent(self, llm_config_name: str, task: str) -> Agent:
        """Create Browser AI agent with selected configuration"""
        llm_config = self.config_manager.get_llm_config(llm_config_name)
        if not llm_config:
            raise ValueError(f"LLM configuration '{llm_config_name}' not found")
        
        # Create LLM instance
        llm = self.config_manager.create_llm_instance(llm_config)
        
        # Create browser if not exists
        if not self.current_browser:
            self.current_browser = Browser()
        
        # Create agent with callbacks
        agent = Agent(
            task=task,
            llm=llm,
            browser=self.current_browser,
            register_new_step_callback=self.event_listener.handle_agent_step,
            register_done_callback=self.event_listener.handle_agent_done,
            generate_gif=False  # Disable GIF generation for web interface
        )
        
        return agent
    
    async def _run_task(self, task: str, llm_config_name: str, max_steps: int = 20) -> str:
        """Run browser automation task"""
        try:
            self.running_task = True
            self.current_task_id = str(uuid.uuid4())
            
            # Set task status
            self.event_listener.set_task_status(
                self.current_task_id, 
                TaskStatus.RUNNING, 
                0
            )
            
            # Create agent
            self.current_agent = self._create_agent(llm_config_name, task)
            
            # Run task
            history = await self.current_agent.run(max_steps=max_steps)
            
            # Get final result
            if history.history and len(history.history) > 0:
                last_item = history.history[-1]
                if last_item.result and len(last_item.result) > 0:
                    final_result = last_item.result[-1]
                    if final_result.is_done:
                        return f"✅ Task completed successfully!\n\n**Result:** {final_result.extracted_content}"
                    elif final_result.error:
                        return f"❌ Task failed: {final_result.error}"
            
            return "✅ Task execution completed"
            
        except Exception as e:
            self.event_listener.set_task_status(
                self.current_task_id or "unknown",
                TaskStatus.FAILED,
                0
            )
            return f"❌ Error executing task: {str(e)}"
        finally:
            self.running_task = False
    
    def _process_chat_message(self, message: str, llm_config: str, history: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], str]:
        """Process chat message and return updated history"""
        if not message.strip():
            return history, ""
        
        if self.running_task:
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "⚠️ A task is already running. Please wait for it to complete."}
            ]
            return new_history, ""
        
        if llm_config == "No LLM configured":
            new_history = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": "⚠️ Please configure an LLM first."}
            ]
            return new_history, ""
        
        # Add user message to history
        new_history = history + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": "🔄 Starting task execution..."}
        ]
        
        # Start task execution in background
        self.current_task_id = str(uuid.uuid4())
        
        # Run task asynchronously
        def run_async_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self._run_task(message, llm_config, max_steps=20)
                )
                # Update the last message with result
                if new_history:
                    new_history[-1]["content"] = result
            except Exception as e:
                if new_history:
                    new_history[-1]["content"] = f"❌ Error: {str(e)}"
        
        # Start background task
        threading.Thread(target=run_async_task, daemon=True).start()
        
        return new_history, ""
    
    def _get_logs(self) -> str:
        """Get current logs as string"""
        if not self.log_buffer:
            return "No logs yet..."
        return "\n".join(self.log_buffer[-50:])  # Show last 50 logs
    
    def _add_llm_config(self, name: str, provider: str, model: str, api_key: str, 
                       base_url: str, temperature: float) -> str:
        """Add new LLM configuration"""
        if not name.strip():
            return "Error: Configuration name is required"
        
        try:
            provider_enum = LLMProvider(provider.lower())
        except ValueError:
            return f"Error: Unsupported provider '{provider}'"
        
        # Create configuration
        config = LLMConfig(
            provider=provider_enum,
            model=model,
            api_key=api_key if api_key.strip() else None,
            base_url=base_url if base_url.strip() else None,
            temperature=temperature
        )
        
        # Test configuration
        if not self.config_manager.test_llm_config(config):
            return "Error: Failed to connect to LLM. Please check your configuration."
        
        # Save configuration
        self.config_manager.add_llm_config(name, config)
        return f"✅ LLM configuration '{name}' added successfully!"
    
    def _get_current_status(self) -> str:
        """Get current task status"""
        if self.running_task:
            return f"🔄 **Status:** Running task '{self.current_task_id}'"
        else:
            return "⚪ **Status:** Idle"
    
    def create_interface(self) -> gr.Interface:
        """Create the Gradio interface"""
        
        with gr.Blocks(
            title="Browser AI Chat",
            theme=gr.themes.Soft(),
            css="""
            .chat-container { height: 500px; overflow-y: auto; }
            .logs-container { height: 300px; overflow-y: auto; font-family: monospace; }
            .status-container { padding: 10px; background-color: #f0f0f0; border-radius: 5px; }
            """
        ) as interface:
            
            gr.Markdown("# 🤖 Browser AI Chat Interface")
            gr.Markdown("Interact with browser automation through a conversational interface")
            
            with gr.Row():
                with gr.Column(scale=2):
                    # Chat interface
                    chatbot = gr.Chatbot(
                        value=[],
                        height=500,
                        label="Chat with Browser AI",
                        elem_classes=["chat-container"],
                        type="messages"  # Use modern message format
                    )
                    
                    with gr.Row():
                        msg_input = gr.Textbox(
                            placeholder="Describe what you want to do (e.g., 'Search for Python tutorials on Google')",
                            label="Your message",
                            scale=4
                        )
                        send_btn = gr.Button("Send", variant="primary")
                
                with gr.Column(scale=1):
                    # Configuration panel
                    gr.Markdown("## ⚙️ Configuration")
                    
                    llm_dropdown = gr.Dropdown(
                        choices=self._get_available_llm_configs(),
                        value=self._get_available_llm_configs()[0] if self._get_available_llm_configs() else None,
                        label="Select LLM",
                        interactive=True
                    )
                    
                    refresh_btn = gr.Button("🔄 Refresh", size="sm")
                    
                    # Status display
                    status_display = gr.Markdown(
                        value=self._get_current_status(),
                        elem_classes=["status-container"]
                    )
                    
                    # Logs display
                    gr.Markdown("## 📋 Logs")
                    logs_display = gr.Textbox(
                        value=self._get_logs(),
                        label="Real-time logs",
                        max_lines=15,
                        elem_classes=["logs-container"],
                        interactive=False
                    )
            
            # LLM Configuration Panel (collapsible)
            with gr.Accordion("🔧 Add New LLM Configuration", open=False):
                with gr.Row():
                    with gr.Column():
                        config_name = gr.Textbox(label="Configuration Name", placeholder="e.g., 'my_openai'")
                        provider_dropdown = gr.Dropdown(
                            choices=["openai", "anthropic", "ollama"],
                            label="Provider",
                            value="openai"
                        )
                        model_input = gr.Textbox(label="Model", placeholder="e.g., 'gpt-4o-mini'")
                    
                    with gr.Column():
                        api_key_input = gr.Textbox(
                            label="API Key", 
                            type="password", 
                            placeholder="Enter API key (leave empty for Ollama)"
                        )
                        base_url_input = gr.Textbox(
                            label="Base URL", 
                            placeholder="http://localhost:11434 (for Ollama)"
                        )
                        temperature_slider = gr.Slider(
                            minimum=0.0, 
                            maximum=2.0, 
                            value=0.1, 
                            step=0.1,
                            label="Temperature"
                        )
                
                add_config_btn = gr.Button("Add Configuration", variant="primary")
                config_result = gr.Markdown()
            
            # Event handlers
            def send_message(message, llm_config, history):
                return self._process_chat_message(message, llm_config, history)
            
            def refresh_llm_configs():
                return gr.Dropdown(choices=self._get_available_llm_configs())
            
            def update_logs():
                return self._get_logs()
            
            def update_status():
                return self._get_current_status()
            
            def add_config(name, provider, model, api_key, base_url, temperature):
                result = self._add_llm_config(name, provider, model, api_key, base_url, temperature)
                return result, gr.Dropdown(choices=self._get_available_llm_configs())
            
            # Wire up events
            send_btn.click(
                send_message,
                inputs=[msg_input, llm_dropdown, chatbot],
                outputs=[chatbot, msg_input]
            )
            
            msg_input.submit(
                send_message,
                inputs=[msg_input, llm_dropdown, chatbot],
                outputs=[chatbot, msg_input]
            )
            
            refresh_btn.click(
                refresh_llm_configs,
                outputs=[llm_dropdown]
            )
            
            add_config_btn.click(
                add_config,
                inputs=[config_name, provider_dropdown, model_input, api_key_input, base_url_input, temperature_slider],
                outputs=[config_result, llm_dropdown]
            )
            
            # Auto-refresh logs and status
            def refresh_logs_periodically():
                while True:
                    time.sleep(2)
                    yield update_logs()
            
            def refresh_status_periodically():
                while True:
                    time.sleep(1)
                    yield update_status()
            
            # Note: For production, use gr.Interface.load() with event handlers
            # instead of the deprecated 'every' parameter
        
        return interface
    
    def launch(self, **kwargs):
        """Launch the web interface"""
        interface = self.create_interface()
        return interface.launch(**kwargs)


def main():
    """Main entry point for web interface"""
    chat_interface = WebChatInterface()
    chat_interface.launch(
        share=False,
        server_name="0.0.0.0",
        server_port=7860,
        inbrowser=True
    )


if __name__ == "__main__":
    main()