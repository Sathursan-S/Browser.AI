"""
Qt desktop chat interface for Browser AI.

Provides a GitHub Copilot-like desktop chat interface for browser automation.
"""

import sys
import asyncio
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QSplitter, QTabWidget,
    QComboBox, QLabel, QGroupBox, QFormLayout, QSlider,
    QScrollArea, QFrame, QProgressBar, QStatusBar, QMessageBox,
    QDialog, QDialogButtonBox, QSpinBox, QCheckBox
)
from PySide6.QtCore import (
    Qt, QTimer, Signal, QObject, QThread, Slot,
    QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import QFont, QTextCursor, QPalette, QColor

from browser_ai import Agent, Browser

from .event_listener import LogEventListener, TaskStatus, LogEvent, TaskUpdate
from .config_manager import ConfigManager, LLMConfig, LLMProvider


class ChatMessage(QWidget):
    """Custom widget for chat messages"""
    
    def __init__(self, message: str, is_user: bool = True, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.setup_ui(message)
    
    def setup_ui(self, message: str):
        layout = QHBoxLayout(self)
        
        # Create message container
        message_frame = QFrame()
        message_frame.setFrameStyle(QFrame.Box)
        message_layout = QVBoxLayout(message_frame)
        
        # Style based on sender
        if self.is_user:
            message_frame.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 1px solid #1976d2;
                    border-radius: 10px;
                    margin: 5px;
                    padding: 8px;
                }
            """)
            layout.addStretch()
            layout.addWidget(message_frame)
        else:
            message_frame.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border: 1px solid #616161;
                    border-radius: 10px;
                    margin: 5px;
                    padding: 8px;
                }
            """)
            layout.addWidget(message_frame)
            layout.addStretch()
        
        # Add message text
        message_text = QTextEdit()
        message_text.setPlainText(message)
        message_text.setReadOnly(True)
        message_text.setMaximumHeight(100)
        message_text.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        message_text.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        message_layout.addWidget(message_text)


class LogWidget(QWidget):
    """Custom widget for displaying logs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.logs = []
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Logs display
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }
        """)
        
        layout.addWidget(QLabel("Real-time Logs:"))
        layout.addWidget(self.log_text)
    
    def add_log(self, message: str):
        """Add new log message"""
        self.logs.append(message)
        if len(self.logs) > 100:  # Keep only last 100 logs
            self.logs.pop(0)
        
        # Update display
        self.log_text.setPlainText("\n".join(self.logs))
        
        # Scroll to bottom
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)


class StatusWidget(QWidget):
    """Widget for displaying task status"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        self.status_label = QLabel("Status: Idle")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 8px;
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                font-weight: bold;
            }
        """)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
    
    def update_status(self, status: str, show_progress: bool = False):
        """Update status display"""
        self.status_label.setText(f"Status: {status}")
        self.progress_bar.setVisible(show_progress)
        
        # Color coding
        if "Running" in status:
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background-color: #e3f2fd;
                    border: 1px solid #1976d2;
                    border-radius: 5px;
                    font-weight: bold;
                    color: #1976d2;
                }
            """)
        elif "Completed" in status:
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 5px;
                    font-weight: bold;
                    color: #4caf50;
                }
            """)
        elif "Failed" in status:
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 5px;
                    font-weight: bold;
                    color: #f44336;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    background-color: #f0f0f0;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-weight: bold;
                }
            """)


class LLMConfigDialog(QDialog):
    """Dialog for adding/editing LLM configurations"""
    
    def __init__(self, config_manager: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Add LLM Configuration")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., 'my_openai'")
        form_layout.addRow("Configuration Name:", self.name_edit)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["google", "openai", "anthropic", "ollama"])
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        form_layout.addRow("Provider:", self.provider_combo)
        
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g., 'gemini-2.5-flash-lite'")
        form_layout.addRow("Model:", self.model_edit)
        
        # Set Google as default and trigger placeholder update
        self.provider_combo.setCurrentText("google")
        self.on_provider_changed("google")
        
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter API key (leave empty for Ollama)")
        form_layout.addRow("API Key:", self.api_key_edit)
        
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("http://localhost:11434 (for Ollama)")
        form_layout.addRow("Base URL:", self.base_url_edit)
        
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 20)
        self.temperature_slider.setValue(1)
        self.temperature_label = QLabel("0.1")
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(str(v / 10.0))
        )
        
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temperature_slider)
        temp_layout.addWidget(self.temperature_label)
        form_layout.addRow("Temperature:", temp_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_config(self) -> Optional[LLMConfig]:
        """Get LLM configuration from form"""
        if not self.name_edit.text().strip():
            return None
        
        try:
            provider = LLMProvider(self.provider_combo.currentText().lower())
        except ValueError:
            return None
        
        return LLMConfig(
            provider=provider,
            model=self.model_edit.text().strip(),
            api_key=self.api_key_edit.text().strip() or None,
            base_url=self.base_url_edit.text().strip() or None,
            temperature=self.temperature_slider.value() / 10.0
        )
    
    def get_name(self) -> str:
        """Get configuration name"""
        return self.name_edit.text().strip()
    
    def on_provider_changed(self, provider_text: str):
        """Update model placeholder when provider changes"""
        placeholders = {
            "google": "e.g., 'gemini-2.5-flash-lite'",
            "openai": "e.g., 'gpt-4o-mini'",
            "anthropic": "e.g., 'claude-3-sonnet-20240229'",
            "ollama": "e.g., 'qwen2.5-coder:0.5b'"
        }
        self.model_edit.setPlaceholderText(placeholders.get(provider_text.lower(), "Enter model name"))


class DesktopChatInterface(QMainWindow):
    """Qt desktop chat interface for Browser AI"""
    
    # Signal for thread-safe UI updates
    chat_message_signal = Signal(str, bool)  # message, is_user
    log_message_signal = Signal(str)  # message
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.event_listener = LogEventListener()
        self.current_agent: Optional[Agent] = None
        self.current_browser: Optional[Browser] = None
        self.current_task_id: Optional[str] = None
        self.running_task = False
        
        # Connect signal to slot
        self.chat_message_signal.connect(self.add_chat_message)
        self.log_message_signal.connect(self.add_log_safe)
        
        # Start event listener
        self.event_listener.start_listening()
        self.event_listener.subscribe_to_logs(self.on_log_event)
        self.event_listener.subscribe_to_tasks(self.on_task_update)
        
        self.setup_ui()
        self.setup_timers()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("Browser AI Chat Interface")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Chat
        chat_panel = self.create_chat_panel()
        splitter.addWidget(chat_panel)
        
        # Right panel - Configuration and logs
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter sizes
        splitter.setSizes([700, 500])
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_chat_panel(self) -> QWidget:
        """Create chat panel"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Title
        title_label = QLabel("🤖 Browser AI Chat")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Chat display
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.chat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText(
            "Describe what you want to do (e.g., 'Search for Python tutorials on Google')"
        )
        self.message_input.returnPressed.connect(self.send_message)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_task)
        self.stop_button.setEnabled(False)  # Initially disabled
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)
        
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.stop_button)
        
        layout.addLayout(input_layout)
        
        return panel
    
    def create_right_panel(self) -> QWidget:
        """Create right panel with configuration and logs"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Configuration section
        config_group = QGroupBox("⚙️ Configuration")
        config_layout = QVBoxLayout(config_group)
        
        # LLM selection
        llm_layout = QHBoxLayout()
        llm_layout.addWidget(QLabel("LLM:"))
        
        self.llm_combo = QComboBox()
        self.update_llm_combo()
        llm_layout.addWidget(self.llm_combo)
        
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.clicked.connect(self.update_llm_combo)
        llm_layout.addWidget(refresh_btn)
        
        config_layout.addLayout(llm_layout)
        
        # Add LLM config button
        add_llm_btn = QPushButton("Add LLM Configuration")
        add_llm_btn.clicked.connect(self.show_llm_config_dialog)
        config_layout.addWidget(add_llm_btn)
        
        # Status widget
        self.status_widget = StatusWidget()
        config_layout.addWidget(self.status_widget)
        
        layout.addWidget(config_group)
        
        # Logs section
        self.log_widget = LogWidget()
        layout.addWidget(self.log_widget)
        
        return panel
    
    def setup_timers(self):
        """Setup update timers"""
        # Timer for updating logs and status
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_ui)
        self.update_timer.start(1000)  # Update every second
    
    @Slot(LogEvent)
    def on_log_event(self, event: LogEvent):
        """Handle log events"""
        timestamp = event.timestamp.strftime("%H:%M:%S")
        status_icon = {
            TaskStatus.IDLE: "⚪",
            TaskStatus.RUNNING: "🔵", 
            TaskStatus.PAUSED: "🟡",
            TaskStatus.COMPLETED: "🟢",
            TaskStatus.FAILED: "🔴"
        }.get(event.task_status, "⚪")
        
        log_message = f"[{timestamp}] {status_icon} {event.message}"
        self.log_message_signal.emit(log_message)
    
    @Slot(TaskUpdate)
    def on_task_update(self, update: TaskUpdate):
        """Handle task updates"""
        if update.status == TaskStatus.COMPLETED:
            self.running_task = False
            if update.result:
                self.add_chat_message(f"✅ Task Completed\n\n{update.result}", is_user=False)
            self.status_widget.update_status("Completed")
            # Reset button states
            self.stop_button.setEnabled(False)
            self.send_button.setEnabled(True)
            self.message_input.setEnabled(True)
            
        elif update.status == TaskStatus.FAILED:
            self.running_task = False
            error_msg = update.error or "Unknown error occurred"
            self.add_chat_message(f"❌ Task Failed\n\n{error_msg}", is_user=False)
            self.status_widget.update_status("Failed")
            # Reset button states
            self.stop_button.setEnabled(False)
            self.send_button.setEnabled(True)
            self.message_input.setEnabled(True)
            
        elif update.status == TaskStatus.RUNNING:
            self.status_widget.update_status(f"Running (Step {update.step_number})", True)
    
    def update_ui(self):
        """Update UI elements"""
        if self.running_task:
            if not self.status_widget.progress_bar.isVisible():
                self.status_widget.update_status("Running", True)
        else:
            if self.status_widget.progress_bar.isVisible():
                self.status_widget.update_status("Idle")
    
    def update_llm_combo(self):
        """Update LLM configuration combo box"""
        configs = list(self.config_manager.get_llm_configs().keys())
        self.llm_combo.clear()
        
        if configs:
            self.llm_combo.addItems(configs)
        else:
            self.llm_combo.addItem("No LLM configured")
    
    def show_llm_config_dialog(self):
        """Show LLM configuration dialog"""
        dialog = LLMConfigDialog(self.config_manager, self)
        
        if dialog.exec() == QDialog.Accepted:
            config = dialog.get_config()
            name = dialog.get_name()
            
            if config and name:
                # Test configuration
                if self.config_manager.test_llm_config(config):
                    self.config_manager.add_llm_config(name, config)
                    self.update_llm_combo()
                    QMessageBox.information(
                        self, "Success", 
                        f"LLM configuration '{name}' added successfully!"
                    )
                else:
                    QMessageBox.warning(
                        self, "Error", 
                        "Failed to connect to LLM. Please check your configuration."
                    )
    
    def add_log_safe(self, message: str):
        """Thread-safe method to add log message"""
        self.log_widget.add_log(message)
    
    def add_chat_message_safe(self, message: str, is_user: bool = True):
        """Thread-safe method to add chat message"""
        self.chat_message_signal.emit(message, is_user)
    
    def add_chat_message(self, message: str, is_user: bool = True):
        """Add message to chat display"""
        # Remove stretch to add message
        self.chat_layout.takeAt(self.chat_layout.count() - 1)
        
        # Add message widget
        message_widget = ChatMessage(message, is_user)
        self.chat_layout.addWidget(message_widget)
        
        # Add stretch back
        self.chat_layout.addStretch()
        
        # Scroll to bottom
        QTimer.singleShot(100, self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        """Scroll chat to bottom"""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def send_message(self):
        """Send chat message"""
        message = self.message_input.text().strip()
        if not message:
            return
        
        if self.running_task:
            QMessageBox.warning(
                self, "Task Running", 
                "A task is already running. Please wait for it to complete."
            )
            return
        
        llm_config_name = self.llm_combo.currentText()
        if llm_config_name == "No LLM configured":
            QMessageBox.warning(
                self, "No LLM", 
                "Please configure an LLM first."
            )
            return
        
        # Add user message to chat
        self.add_chat_message(message, is_user=True)
        self.message_input.clear()
        
        # Start task execution
        self.run_task_async(message, llm_config_name)
        
        # Enable stop button and disable send button and input
        self.stop_button.setEnabled(True)
        self.send_button.setEnabled(False)
        self.message_input.setEnabled(False)
    
    def stop_task(self):
        """Stop the currently running task"""
        if not self.running_task or not self.current_agent:
            return
        
        try:
            # Stop the agent
            self.current_agent.stop()
            
            # Update UI
            self.chat_message_signal.emit("⏹️ Task stopped by user", False)
            
            # Reset state
            self.running_task = False
            self.current_task_id = None
            
            # Update button states
            self.stop_button.setEnabled(False)
            self.send_button.setEnabled(True)
            self.message_input.setEnabled(True)
            
        except Exception as e:
            self.chat_message_signal.emit(f"❌ Error stopping task: {str(e)}", False)
    
    def run_task_async(self, task: str, llm_config_name: str):
        """Run task asynchronously"""
        self.running_task = True
        self.current_task_id = str(uuid.uuid4())
        
        def run_task():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.run_browser_task(task, llm_config_name)
                )
                # Task completed, result will be handled by task update callback
            except Exception as e:
                # Use thread-safe method to update UI
                self.chat_message_signal.emit(f"❌ Error: {str(e)}", False)
                self.running_task = False
                # Reset button states on error
                self.stop_button.setEnabled(False)
                self.send_button.setEnabled(True)
                self.message_input.setEnabled(True)
        
        # Start task in background thread
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
        
        # Add placeholder message using thread-safe method
        self.chat_message_signal.emit("🔄 Starting task execution...", False)
    
    async def run_browser_task(self, task: str, llm_config_name: str) -> str:
        """Run browser automation task"""
        try:
            # Set task status
            self.event_listener.set_task_status(
                self.current_task_id, 
                TaskStatus.RUNNING, 
                0
            )
            
            # Get LLM config
            llm_config = self.config_manager.get_llm_config(llm_config_name)
            if not llm_config:
                raise ValueError(f"LLM configuration '{llm_config_name}' not found")
            
            # Create LLM instance
            llm = self.config_manager.create_llm_instance(llm_config)
            
            # Create browser if not exists
            if not self.current_browser:
                self.current_browser = Browser()
            
            # Create agent
            self.current_agent = Agent(
                task=task,
                llm=llm,
                browser=self.current_browser,
                register_new_step_callback=self.event_listener.handle_agent_step,
                register_done_callback=self.event_listener.handle_agent_done,
                generate_gif=False
            )
            
            # Run task
            history = await self.current_agent.run(max_steps=20)
            
            # Get result
            if history.history and len(history.history) > 0:
                last_item = history.history[-1]
                if last_item.result and len(last_item.result) > 0:
                    final_result = last_item.result[-1]
                    if final_result.is_done:
                        return f"✅ Task completed successfully!\n\n{final_result.extracted_content}"
                    elif final_result.error:
                        return f"❌ Task failed: {final_result.error}"
            
            return "✅ Task execution completed"
            
        except Exception as e:
            self.event_listener.set_task_status(
                self.current_task_id or "unknown",
                TaskStatus.FAILED,
                0
            )
            raise e
        finally:
            self.running_task = False


def main():
    """Main entry point for desktop app"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show main window
    window = DesktopChatInterface()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()