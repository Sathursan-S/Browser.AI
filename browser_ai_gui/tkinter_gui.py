"""
Tkinter GUI for Browser.AI

Desktop GUI that mimics GitHub Copilot chat interface in VS Code
with real-time log streaming and task management.
"""

import asyncio
import threading
import time
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox, font
from typing import Optional, Dict, Any
import queue

from .config import ConfigManager
from .event_adapter import EventAdapter, LogEvent, EventType, LogLevel


class ScrollableText(Frame):
    """Scrollable text widget with better performance"""
    
    def __init__(self, parent, **kwargs):
        Frame.__init__(self, parent)
        
        # Create text widget with scrollbar
        self.text = Text(self, wrap=WORD, state=DISABLED, **kwargs)
        self.scrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack widgets
        self.text.pack(side=LEFT, fill=BOTH, expand=True)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        
    def append_text(self, text: str, tag: Optional[str] = None):
        """Append text to the widget"""
        self.text.config(state=NORMAL)
        self.text.insert(END, text + '\n', tag)
        self.text.config(state=DISABLED)
        self.text.see(END)
        
    def clear(self):
        """Clear all text"""
        self.text.config(state=NORMAL)
        self.text.delete(1.0, END)
        self.text.config(state=DISABLED)


class ConfigDialog:
    """Configuration dialog for LLM settings"""
    
    def __init__(self, parent, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager
        self.result = None
        
        # Create dialog window
        self.dialog = Toplevel(parent)
        self.dialog.title("Configuration")
        self.dialog.geometry("400x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.load_current_config()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (400 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"400x500+{x}+{y}")
        
    def setup_ui(self):
        """Setup the configuration UI"""
        # Main frame with padding
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=BOTH, expand=True)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=BOTH, expand=True, pady=(0, 10))
        
        # LLM Configuration Tab
        llm_frame = ttk.Frame(notebook)
        notebook.add(llm_frame, text="LLM Settings")
        
        # LLM Provider
        ttk.Label(llm_frame, text="Provider:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.provider_var = StringVar()
        provider_combo = ttk.Combobox(llm_frame, textvariable=self.provider_var, state="readonly")
        provider_combo['values'] = self.config_manager.get_supported_providers()
        provider_combo.grid(row=0, column=1, sticky=EW, padx=5, pady=5)
        provider_combo.bind('<<ComboboxSelected>>', self.on_provider_change)
        
        # Model
        ttk.Label(llm_frame, text="Model:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.model_var = StringVar()
        self.model_combo = ttk.Combobox(llm_frame, textvariable=self.model_var, state="readonly")
        self.model_combo.grid(row=1, column=1, sticky=EW, padx=5, pady=5)
        
        # API Key
        ttk.Label(llm_frame, text="API Key:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.api_key_var = StringVar()
        ttk.Entry(llm_frame, textvariable=self.api_key_var, show="*").grid(row=2, column=1, sticky=EW, padx=5, pady=5)
        
        # Temperature
        ttk.Label(llm_frame, text="Temperature:").grid(row=3, column=0, sticky=W, padx=5, pady=5)
        self.temperature_var = DoubleVar()
        temp_scale = ttk.Scale(llm_frame, from_=0.0, to=2.0, variable=self.temperature_var, 
                              orient=HORIZONTAL, length=200)
        temp_scale.grid(row=3, column=1, sticky=EW, padx=5, pady=5)
        
        # Temperature value label
        self.temp_label = ttk.Label(llm_frame, text="0.1")
        self.temp_label.grid(row=3, column=2, padx=5, pady=5)
        temp_scale.bind("<Motion>", self.update_temp_label)
        
        # Configure grid weights
        llm_frame.columnconfigure(1, weight=1)
        
        # Browser Configuration Tab
        browser_frame = ttk.Frame(notebook)
        notebook.add(browser_frame, text="Browser Settings")
        
        self.headless_var = BooleanVar()
        ttk.Checkbutton(browser_frame, text="Headless Mode", variable=self.headless_var).pack(anchor=W, pady=5)
        
        self.disable_security_var = BooleanVar()
        ttk.Checkbutton(browser_frame, text="Disable Security", variable=self.disable_security_var).pack(anchor=W, pady=5)
        
        # Agent Configuration Tab
        agent_frame = ttk.Frame(notebook)
        notebook.add(agent_frame, text="Agent Settings")
        
        self.use_vision_var = BooleanVar()
        ttk.Checkbutton(agent_frame, text="Use Vision", variable=self.use_vision_var).pack(anchor=W, pady=5)
        
        # Max Steps
        steps_frame = ttk.Frame(agent_frame)
        steps_frame.pack(fill=X, pady=5)
        ttk.Label(steps_frame, text="Max Steps:").pack(side=LEFT)
        self.max_steps_var = IntVar()
        ttk.Entry(steps_frame, textvariable=self.max_steps_var, width=10).pack(side=RIGHT)
        
        # Max Failures
        failures_frame = ttk.Frame(agent_frame)
        failures_frame.pack(fill=X, pady=5)
        ttk.Label(failures_frame, text="Max Failures:").pack(side=LEFT)
        self.max_failures_var = IntVar()
        ttk.Entry(failures_frame, textvariable=self.max_failures_var, width=10).pack(side=RIGHT)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=X, pady=5)
        
        ttk.Button(button_frame, text="Save", command=self.save_config).pack(side=RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=RIGHT, padx=5)
        ttk.Button(button_frame, text="Test Connection", command=self.test_connection).pack(side=LEFT, padx=5)
        
    def on_provider_change(self, event=None):
        """Handle provider selection change"""
        provider = self.provider_var.get()
        default_models = self.config_manager.get_default_models()
        
        if provider in default_models:
            self.model_combo['values'] = default_models[provider]
            if default_models[provider]:
                self.model_var.set(default_models[provider][0])
    
    def update_temp_label(self, event=None):
        """Update temperature label"""
        self.temp_label.config(text=f"{self.temperature_var.get():.2f}")
    
    def load_current_config(self):
        """Load current configuration into dialog"""
        config = self.config_manager
        
        # LLM settings
        self.provider_var.set(config.llm_config.provider)
        self.on_provider_change()  # Update model options
        self.model_var.set(config.llm_config.model)
        self.api_key_var.set(config.llm_config.api_key)
        self.temperature_var.set(config.llm_config.temperature)
        self.update_temp_label()
        
        # Browser settings
        self.headless_var.set(config.browser_config.headless)
        self.disable_security_var.set(config.browser_config.disable_security)
        
        # Agent settings
        self.use_vision_var.set(config.agent_config.use_vision)
        self.max_steps_var.set(config.agent_config.max_steps)
        self.max_failures_var.set(config.agent_config.max_failures)
    
    def test_connection(self):
        """Test LLM connection"""
        try:
            # Temporarily update config with dialog values
            original_config = dict(vars(self.config_manager.llm_config))
            
            self.config_manager.update_llm_config(
                provider=self.provider_var.get(),
                model=self.model_var.get(),
                api_key=self.api_key_var.get(),
                temperature=self.temperature_var.get()
            )
            
            # Try to create LLM instance
            llm = self.config_manager.get_llm_instance()
            messagebox.showinfo("Test Result", "Connection test successful!")
            
        except Exception as e:
            messagebox.showerror("Test Failed", f"Connection test failed:\n{str(e)}")
            
            # Restore original config
            for key, value in original_config.items():
                setattr(self.config_manager.llm_config, key, value)
    
    def save_config(self):
        """Save configuration"""
        try:
            # Update configuration
            self.config_manager.update_llm_config(
                provider=self.provider_var.get(),
                model=self.model_var.get(),
                api_key=self.api_key_var.get(),
                temperature=self.temperature_var.get()
            )
            
            self.config_manager.update_browser_config(
                headless=self.headless_var.get(),
                disable_security=self.disable_security_var.get()
            )
            
            self.config_manager.update_agent_config(
                use_vision=self.use_vision_var.get(),
                max_steps=self.max_steps_var.get(),
                max_failures=self.max_failures_var.get()
            )
            
            # Validate configuration
            issues = self.config_manager.validate_config()
            if issues:
                messagebox.showwarning("Configuration Issues", 
                                     "Configuration saved but has issues:\n" + "\n".join(issues))
            else:
                messagebox.showinfo("Success", "Configuration saved successfully!")
            
            self.result = "save"
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")
    
    def cancel(self):
        """Cancel configuration"""
        self.result = "cancel"
        self.dialog.destroy()


class TaskManager:
    """Manages Browser.AI tasks in Tkinter context"""
    
    def __init__(self, config_manager: ConfigManager, event_adapter: EventAdapter):
        self.config_manager = config_manager
        self.event_adapter = event_adapter
        self.current_agent = None
        self.current_task = None
        self.is_running = False
        self.task_thread = None
    
    def start_task(self, task_description: str, callback: Optional[callable] = None):
        """Start a Browser.AI task"""
        if self.is_running:
            if callback:
                callback(False, "Task already running")
            return
        
        def run_task():
            try:
                # Import Browser.AI components
                from browser_ai import Agent, Browser, BrowserConfig
                
                # Create LLM instance
                llm = self.config_manager.get_llm_instance()
                
                # Create browser config
                browser_config_dict = self.config_manager.get_browser_config_dict()
                browser_config = BrowserConfig(**browser_config_dict)
                browser = Browser(config=browser_config)
                
                # Create agent
                self.current_agent = Agent(
                    task=task_description,
                    llm=llm,
                    browser=browser,
                    use_vision=self.config_manager.agent_config.use_vision,
                    max_failures=self.config_manager.agent_config.max_failures,
                    retry_delay=self.config_manager.agent_config.retry_delay,
                    generate_gif=self.config_manager.agent_config.generate_gif,
                    validate_output=self.config_manager.agent_config.validate_output
                )
                
                self.current_task = task_description
                self.is_running = True
                
                # Emit start event
                self.event_adapter.emit_custom_event(
                    EventType.AGENT_START,
                    f"Starting task: {task_description}",
                    LogLevel.INFO,
                    {"task": task_description}
                )
                
                if callback:
                    callback(True, "Task started successfully")
                
                # Run agent
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.current_agent.run(max_steps=self.config_manager.agent_config.max_steps)
                )
                
                self.event_adapter.emit_custom_event(
                    EventType.AGENT_COMPLETE,
                    "Task completed successfully",
                    LogLevel.INFO,
                    {"result": str(result)}
                )
                
            except Exception as e:
                self.event_adapter.emit_custom_event(
                    EventType.AGENT_ERROR,
                    f"Task failed: {str(e)}",
                    LogLevel.ERROR,
                    {"error": str(e)}
                )
                
                if callback:
                    callback(False, f"Task failed: {str(e)}")
                    
            finally:
                self.is_running = False
                self.current_agent = None
                self.current_task = None
        
        self.task_thread = threading.Thread(target=run_task, daemon=True)
        self.task_thread.start()
    
    def stop_task(self):
        """Stop current task"""
        if self.current_agent and self.is_running:
            self.current_agent.stop()
            self.event_adapter.emit_custom_event(
                EventType.AGENT_STOP,
                "Task stopped by user",
                LogLevel.INFO
            )
    
    def pause_task(self):
        """Pause current task"""
        if self.current_agent and self.is_running:
            self.current_agent.pause()
            self.event_adapter.emit_custom_event(
                EventType.AGENT_PAUSE,
                "Task paused by user",
                LogLevel.INFO
            )
    
    def resume_task(self):
        """Resume current task"""
        if self.current_agent and self.is_running:
            self.current_agent.resume()
            self.event_adapter.emit_custom_event(
                EventType.AGENT_RESUME,
                "Task resumed by user",
                LogLevel.INFO
            )


class BrowserAIGUI:
    """Main Tkinter GUI for Browser.AI"""
    
    def __init__(self):
        self.root = Tk()
        self.root.title("Browser.AI Assistant")
        self.root.geometry("1200x800")
        
        # Initialize components
        self.config_manager = ConfigManager()
        self.event_adapter = EventAdapter()
        self.task_manager = TaskManager(self.config_manager, self.event_adapter)
        
        # Event queue for thread-safe GUI updates
        self.event_queue = queue.Queue()
        
        # Setup GUI
        self.setup_styles()
        self.setup_ui()
        self.setup_event_handling()
        
        # Start event adapter
        self.event_adapter.start()
        self.event_adapter.subscribe(self.on_log_event)
        
        # Start event processing
        self.process_events()
    
    def setup_styles(self):
        """Setup custom styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Chat.TFrame', background='#1e1e1e')
        style.configure('Sidebar.TFrame', background='#252526')
        style.configure('Header.TLabel', background='#2d2d30', foreground='#cccccc', 
                       font=('Segoe UI', 12, 'bold'))
        style.configure('Status.TLabel', background='#252526', foreground='#cccccc')
    
    def setup_ui(self):
        """Setup the main UI"""
        # Configure root
        self.root.configure(bg='#1e1e1e')
        
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=HORIZONTAL)
        main_container.pack(fill=BOTH, expand=True)
        
        # Left sidebar
        self.setup_sidebar(main_container)
        
        # Right chat area
        self.setup_chat_area(main_container)
        
        # Configure paned window
        main_container.add(self.sidebar_frame, weight=0)
        main_container.add(self.chat_frame, weight=1)
    
    def setup_sidebar(self, parent):
        """Setup the left sidebar"""
        self.sidebar_frame = ttk.Frame(parent, style='Sidebar.TFrame', width=300)
        self.sidebar_frame.pack_propagate(False)
        
        # Header
        header_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        header_frame.pack(fill=X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="Browser.AI Assistant", 
                 style='Header.TLabel').pack(anchor=W)
        
        # Status indicator
        status_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        status_frame.pack(fill=X, padx=10, pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="● Stopped", 
                                    style='Status.TLabel', foreground='#dc3545')
        self.status_label.pack(anchor=W)
        
        # Control buttons
        button_frame = ttk.Frame(self.sidebar_frame)
        button_frame.pack(fill=X, padx=10, pady=5)
        
        self.pause_btn = ttk.Button(button_frame, text="Pause", 
                                   command=self.pause_task, state=DISABLED)
        self.pause_btn.pack(side=LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", 
                                  command=self.stop_task, state=DISABLED)
        self.stop_btn.pack(side=LEFT, padx=5)
        
        # Configuration button
        ttk.Button(button_frame, text="Config", 
                  command=self.open_config).pack(side=RIGHT)
        
        # Separator
        ttk.Separator(self.sidebar_frame, orient=HORIZONTAL).pack(fill=X, pady=10)
        
        # Current task info
        ttk.Label(self.sidebar_frame, text="Current Task:", 
                 style='Status.TLabel').pack(anchor=W, padx=10, pady=(0, 5))
        
        self.task_label = ttk.Label(self.sidebar_frame, text="None", 
                                   style='Status.TLabel', wraplength=280)
        self.task_label.pack(anchor=W, padx=10, pady=(0, 10))
        
        # Log viewer (collapsible)
        log_frame = ttk.LabelFrame(self.sidebar_frame, text="Recent Logs", padding=5)
        log_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = ScrollableText(log_frame, height=15, font=('Consolas', 8))
        self.log_text.pack(fill=BOTH, expand=True)
        
        # Configure log text tags
        self.setup_log_tags()
    
    def setup_chat_area(self, parent):
        """Setup the right chat area"""
        self.chat_frame = ttk.Frame(parent, style='Chat.TFrame')
        
        # Chat header
        chat_header = ttk.Frame(self.chat_frame)
        chat_header.pack(fill=X, padx=20, pady=(10, 0))
        
        ttk.Label(chat_header, text="Browser Automation Chat", 
                 style='Header.TLabel').pack(anchor=W)
        
        # Chat messages area
        messages_frame = ttk.Frame(self.chat_frame)
        messages_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        self.chat_text = ScrollableText(messages_frame, font=('Segoe UI', 10), 
                                       bg='#1e1e1e', fg='#cccccc', 
                                       selectbackground='#264f78')
        self.chat_text.pack(fill=BOTH, expand=True)
        
        # Configure chat text tags
        self.setup_chat_tags()
        
        # Initial welcome message
        self.add_chat_message("Hello! I'm your Browser.AI assistant. I can help you automate web tasks.\n\n"
                            "To get started:\n"
                            "1. Configure your LLM settings using the Config button\n"
                            "2. Describe what you'd like me to do in the input below\n"
                            "3. I'll execute the task and keep you updated with real-time progress",
                            "system")
        
        # Chat input area
        input_frame = ttk.Frame(self.chat_frame)
        input_frame.pack(fill=X, padx=20, pady=(0, 20))
        
        # Input text area
        input_container = ttk.Frame(input_frame)
        input_container.pack(fill=X, pady=(0, 10))
        
        self.input_text = Text(input_container, height=3, wrap=WORD, 
                              font=('Segoe UI', 10), bg='#3c3c3c', 
                              fg='#cccccc', insertbackground='#cccccc')
        input_scroll = ttk.Scrollbar(input_container, command=self.input_text.yview)
        self.input_text.configure(yscrollcommand=input_scroll.set)
        
        self.input_text.pack(side=LEFT, fill=BOTH, expand=True)
        input_scroll.pack(side=RIGHT, fill=Y)
        
        # Send button
        self.send_btn = ttk.Button(input_frame, text="Send Task", 
                                  command=self.send_message)
        self.send_btn.pack(anchor=E)
        
        # Bind Enter key
        self.input_text.bind('<Control-Return>', lambda e: self.send_message())
    
    def setup_log_tags(self):
        """Setup tags for log text formatting"""
        text_widget = self.log_text.text
        
        text_widget.tag_configure('DEBUG', foreground='#8e8e8e')
        text_widget.tag_configure('INFO', foreground='#4fc3f7')
        text_widget.tag_configure('WARNING', foreground='#ffb74d')
        text_widget.tag_configure('ERROR', foreground='#f48fb1')
        text_widget.tag_configure('RESULT', foreground='#81c784')
    
    def setup_chat_tags(self):
        """Setup tags for chat text formatting"""
        text_widget = self.chat_text.text
        
        # Configure fonts
        default_font = font.nametofont("TkDefaultFont")
        bold_font = default_font.copy()
        bold_font.configure(weight="bold")
        
        text_widget.tag_configure('user_header', foreground='#28a745', font=bold_font)
        text_widget.tag_configure('user_message', foreground='#cccccc', lmargin1=20, lmargin2=20)
        
        text_widget.tag_configure('system_header', foreground='#0e639c', font=bold_font)
        text_widget.tag_configure('system_message', foreground='#cccccc', lmargin1=20, lmargin2=20)
        
        text_widget.tag_configure('error_header', foreground='#dc3545', font=bold_font)
        text_widget.tag_configure('error_message', foreground='#f48fb1', lmargin1=20, lmargin2=20)
        
        text_widget.tag_configure('action_header', foreground='#ffc107', font=bold_font)
        text_widget.tag_configure('action_message', foreground='#cccccc', lmargin1=20, lmargin2=20)
    
    def setup_event_handling(self):
        """Setup event handling for GUI updates"""
        pass
    
    def process_events(self):
        """Process events from queue (thread-safe GUI updates)"""
        try:
            while True:
                event = self.event_queue.get_nowait()
                event()  # Execute the event function
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_events)
    
    def on_log_event(self, event: LogEvent):
        """Handle log event (called from background thread)"""
        # Queue GUI update for thread safety
        def update_gui():
            # Add to log text
            timestamp = event.timestamp.strftime("%H:%M:%S")
            log_line = f"[{timestamp}] {event.message}"
            self.log_text.append_text(log_line, event.level.value)
            
            # Update status and chat based on event type
            if event.event_type == EventType.AGENT_START:
                self.update_status(True, "Running", event.metadata.get('task', 'Unknown Task'))
                self.add_chat_message(f"🚀 Starting task: {event.message}", "system")
                
            elif event.event_type == EventType.AGENT_COMPLETE:
                self.update_status(False, "Completed", None)
                self.add_chat_message("✅ Task completed successfully!", "system")
                
            elif event.event_type == EventType.AGENT_ERROR:
                self.update_status(False, "Error", None)
                self.add_chat_message(f"❌ Error: {event.message}", "error")
                
            elif event.event_type == EventType.AGENT_ACTION:
                self.add_chat_message(f"🛠️ {event.message}", "action")
                
            elif event.event_type == EventType.AGENT_RESULT:
                self.add_chat_message(f"📄 {event.message}", "system")
                
            elif event.event_type == EventType.AGENT_PAUSE:
                self.update_status(True, "Paused", self.task_manager.current_task)
                self.add_chat_message("⏸️ Task paused", "system")
                
            elif event.event_type == EventType.AGENT_RESUME:
                self.update_status(True, "Running", self.task_manager.current_task)
                self.add_chat_message("▶️ Task resumed", "system")
                
            elif event.event_type == EventType.AGENT_STOP:
                self.update_status(False, "Stopped", None)
                self.add_chat_message("⏹️ Task stopped", "system")
        
        self.event_queue.put(update_gui)
    
    def add_chat_message(self, message: str, msg_type: str = "system"):
        """Add message to chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Message header
        if msg_type == "user":
            header = f"[{timestamp}] You:\n"
            header_tag = "user_header"
            message_tag = "user_message"
        elif msg_type == "error":
            header = f"[{timestamp}] Error:\n"
            header_tag = "error_header"
            message_tag = "error_message"
        elif msg_type == "action":
            header = f"[{timestamp}] Action:\n"
            header_tag = "action_header"
            message_tag = "action_message"
        else:
            header = f"[{timestamp}] Browser.AI:\n"
            header_tag = "system_header"
            message_tag = "system_message"
        
        # Add to chat
        self.chat_text.append_text(header, header_tag)
        self.chat_text.append_text(message + "\n", message_tag)
    
    def update_status(self, is_running: bool, status_text: str, current_task: Optional[str]):
        """Update status display"""
        if is_running:
            color = '#28a745' if status_text == "Running" else '#ffc107'
            self.status_label.config(text=f"● {status_text}", foreground=color)
            self.pause_btn.config(state=NORMAL)
            self.stop_btn.config(state=NORMAL)
            self.send_btn.config(state=DISABLED)
        else:
            self.status_label.config(text=f"● {status_text}", foreground='#dc3545')
            self.pause_btn.config(state=DISABLED)
            self.stop_btn.config(state=DISABLED)
            self.send_btn.config(state=NORMAL)
        
        # Update task label
        if current_task:
            self.task_label.config(text=current_task)
        else:
            self.task_label.config(text="None")
    
    def send_message(self):
        """Send chat message and start task"""
        message = self.input_text.get(1.0, END).strip()
        if not message:
            return
        
        # Clear input
        self.input_text.delete(1.0, END)
        
        # Add to chat
        self.add_chat_message(message, "user")
        
        # Start task
        def task_callback(success: bool, result: str):
            if not success:
                def show_error():
                    self.add_chat_message(f"Failed to start task: {result}", "error")
                self.event_queue.put(show_error)
        
        self.task_manager.start_task(message, task_callback)
    
    def pause_task(self):
        """Pause current task"""
        self.task_manager.pause_task()
    
    def stop_task(self):
        """Stop current task"""
        self.task_manager.stop_task()
    
    def open_config(self):
        """Open configuration dialog"""
        dialog = ConfigDialog(self.root, self.config_manager)
        self.root.wait_window(dialog.dialog)
    
    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.event_adapter.stop()


def main():
    """Main entry point for Tkinter GUI"""
    app = BrowserAIGUI()
    app.run()


if __name__ == "__main__":
    main()