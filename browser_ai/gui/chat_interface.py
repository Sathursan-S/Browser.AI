"""
Browser.AI Chat Interface

A Gradio-based chat interface for displaying browser automation logs,
current steps, and outputs in real-time.
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

import gradio as gr

from browser_ai.agent.views import AgentOutput, ActionResult, AgentHistoryList
from browser_ai.browser.views import BrowserState

logger = logging.getLogger(__name__)


class BrowserAIChat:
	"""
	A chat interface GUI for Browser.AI that displays logs and automation progress.
	
	This class creates a Gradio-based web interface that shows:
	- Current automation task
	- Step-by-step progress with goals and actions
	- Action results and extracted content
	- Error messages and debugging information
	- Browser state updates
	"""
	
	def __init__(self, title: str = "Browser.AI Automation Chat", port: int = 7860):
		self.title = title
		self.port = port
		self.chat_history: List[Tuple[str, str]] = []
		self.current_task: str = ""
		self.current_step: int = 0
		self.is_running: bool = False
		
		# Thread-safe event handling
		self._update_queue = asyncio.Queue()
		self._interface = None
		self._demo = None
		
	def setup_interface(self):
		"""Setup the Gradio interface"""
		with gr.Blocks(
			title=self.title,
			theme=gr.themes.Soft(),
			css="""
			.chat-container { 
				height: 600px !important; 
				overflow-y: auto !important; 
			}
			.status-box {
				background: linear-gradient(90deg, #f0f9ff, #e0f2fe);
				border: 1px solid #0ea5e9;
				border-radius: 8px;
				padding: 12px;
				margin: 8px 0;
			}
			.step-info {
				background: #f8fafc;
				border-left: 4px solid #3b82f6;
				padding: 12px;
				margin: 8px 0;
			}
			.error-box {
				background: #fef2f2;
				border: 1px solid #ef4444;
				border-radius: 8px;
				padding: 12px;
				margin: 8px 0;
			}
			.success-box {
				background: #f0fdf4;
				border: 1px solid #22c55e;
				border-radius: 8px;
				padding: 12px;
				margin: 8px 0;
			}
			"""
		) as demo:
			self._demo = demo
			
			with gr.Row():
				gr.Markdown(f"# {self.title}")
				
			with gr.Row():
				with gr.Column(scale=3):
					# Current Status
					self.status_display = gr.HTML(
						value=self._format_status("No task running", 0, False),
						label="Current Status"
					)
					
					# Chat Interface
					self.chatbot = gr.Chatbot(
						value=self.chat_history,
						label="Automation Log",
						height=500,
						elem_classes=["chat-container"],
						show_copy_button=True,
						type="tuples"  # Use tuples format for compatibility
					)
					
					# Input area (for future enhancements like user commands)
					with gr.Row():
						self.msg_input = gr.Textbox(
							placeholder="Monitor automation progress...",
							scale=4,
							interactive=False
						)
						self.send_btn = gr.Button("Send", scale=1, interactive=False)
				
				with gr.Column(scale=1):
					# Control Panel
					gr.Markdown("### Control Panel")
					
					self.task_display = gr.Textbox(
						value="No task set",
						label="Current Task",
						interactive=False,
						lines=2
					)
					
					self.step_display = gr.Textbox(
						value="0",
						label="Current Step",
						interactive=False
					)
					
					self.clear_btn = gr.Button("Clear Chat", variant="secondary")
					
					# Auto-refresh checkbox
					self.auto_refresh = gr.Checkbox(
						value=True,
						label="Auto-refresh",
						info="Automatically update interface"
					)
					
					# Manual refresh button
					self.refresh_btn = gr.Button("Refresh", variant="primary")
			
			# Event handlers
			self.clear_btn.click(
				fn=self._clear_chat,
				outputs=[self.chatbot]
			)
			
			self.refresh_btn.click(
				fn=self._manual_refresh,
				outputs=[self.chatbot, self.status_display, self.task_display, self.step_display]
			)
		
		return demo
	
	def _format_status(self, task: str, step: int, is_running: bool) -> str:
		"""Format the status display"""
		status_color = "#22c55e" if is_running else "#6b7280"
		status_text = "Running" if is_running else "Idle"
		
		return f"""
		<div class="status-box">
			<h4 style="margin: 0; color: {status_color};">Status: {status_text}</h4>
			<p style="margin: 4px 0;"><strong>Task:</strong> {task}</p>
			<p style="margin: 4px 0;"><strong>Step:</strong> {step}</p>
			<p style="margin: 4px 0; font-size: 0.9em; color: #6b7280;">
				Last update: {datetime.now().strftime('%H:%M:%S')}
			</p>
		</div>
		"""
	
	def _clear_chat(self):
		"""Clear the chat history"""
		self.chat_history = []
		return []
	
	def _manual_refresh(self):
		"""Manual refresh of the interface"""
		return (
			self.chat_history,
			self._format_status(self.current_task, self.current_step, self.is_running),
			self.current_task,
			str(self.current_step)
		)
	
	def add_message(self, user_msg: str, assistant_msg: str = "", timestamp: bool = True):
		"""Add a message to the chat history"""
		if timestamp:
			current_time = datetime.now().strftime("%H:%M:%S")
			user_msg = f"[{current_time}] {user_msg}"
		
		self.chat_history.append((user_msg, assistant_msg))
		
		# Keep only last 100 messages to prevent memory issues
		if len(self.chat_history) > 100:
			self.chat_history = self.chat_history[-100:]
	
	def add_step_info(self, step_num: int, goal: str, actions: List[Any] = None):
		"""Add step information to the chat"""
		actions_str = ""
		if actions:
			actions_str = "\n".join([f"  • {self._format_action(action)}" for action in actions[:3]])
			if len(actions) > 3:
				actions_str += f"\n  • ... and {len(actions) - 3} more actions"
		
		user_msg = f"🎯 **Step {step_num}**\n**Goal:** {goal}"
		assistant_msg = f"**Actions to perform:**\n{actions_str}" if actions_str else "Analyzing page..."
		
		self.add_message(user_msg, assistant_msg)
		self.current_step = step_num
	
	def add_action_result(self, result: ActionResult):
		"""Add action result to the chat"""
		if result.is_done:
			user_msg = "✅ **Task Completed**"
			assistant_msg = f"**Result:** {result.extracted_content}" if result.extracted_content else "Task finished successfully!"
			self.add_message(user_msg, assistant_msg)
		elif result.error:
			user_msg = "❌ **Action Error**"
			assistant_msg = f"**Error:** {result.error[:300]}{'...' if len(result.error) > 300 else ''}"
			self.add_message(user_msg, assistant_msg)
		elif result.extracted_content:
			user_msg = "📄 **Content Extracted**"
			assistant_msg = f"**Content:** {result.extracted_content[:500]}{'...' if len(result.extracted_content) > 500 else ''}"
			self.add_message(user_msg, assistant_msg)
	
	def add_browser_state(self, state: BrowserState):
		"""Add browser state information to the chat"""
		user_msg = f"🌐 **Page Update**\n**URL:** {state.url}"
		assistant_msg = f"**Title:** {state.title}\n**Elements:** {len(state.selector_map) if state.selector_map else 0} interactive elements found"
		self.add_message(user_msg, assistant_msg)
	
	def _format_action(self, action: Any) -> str:
		"""Format an action for display"""
		if hasattr(action, 'model_dump'):
			action_dict = action.model_dump(exclude_unset=True)
		else:
			action_dict = dict(action) if hasattr(action, 'items') else str(action)
		
		# Get the action type (first key in the dict)
		if isinstance(action_dict, dict) and action_dict:
			action_type = list(action_dict.keys())[0]
			action_params = action_dict[action_type]
			
			if action_type == 'click_element':
				return f"Click element at index {action_params.get('index', 'unknown')}"
			elif action_type == 'type_text':
				return f"Type text: '{action_params.get('text', '')[:50]}...'"
			elif action_type == 'scroll':
				return f"Scroll {action_params.get('direction', 'down')}"
			elif action_type == 'go_to_url':
				return f"Navigate to: {action_params.get('url', 'unknown')}"
			elif action_type == 'extract_content':
				return f"Extract content: {action_params.get('goal', 'content')}"
			else:
				return f"{action_type}: {str(action_params)[:50]}"
		
		return str(action_dict)[:50]
	
	def set_task(self, task: str):
		"""Set the current task"""
		self.current_task = task
		self.is_running = True
		user_msg = "🚀 **New Task Started**"
		assistant_msg = f"**Task:** {task}"
		self.add_message(user_msg, assistant_msg)
	
	def task_completed(self, history: AgentHistoryList):
		"""Mark task as completed"""
		self.is_running = False
		user_msg = "🏁 **Automation Completed**"
		assistant_msg = f"Task finished after {len(history.history)} steps"
		self.add_message(user_msg, assistant_msg)
	
	def launch(self, share: bool = False, debug: bool = False):
		"""Launch the Gradio interface"""
		if self._interface is None:
			self._interface = self.setup_interface()
		
		logger.info(f"Launching Browser.AI Chat Interface on port {self.port}")
		return self._interface.launch(
			server_port=self.port,
			share=share,
			debug=debug,
			prevent_thread_lock=True,
			show_error=True
		)
	
	# Callback methods for Agent integration
	def step_callback(self, state: BrowserState, output: AgentOutput, step_num: int):
		"""Callback method for Agent step updates"""
		try:
			# Add step information
			actions = output.action if output else []
			goal = output.current_state.next_goal if output and output.current_state else "Processing..."
			
			self.add_step_info(step_num, goal, actions)
			
			# Add page evaluation if available
			if output and output.current_state:
				evaluation = output.current_state.evaluation_previous_goal
				memory = output.current_state.memory
				
				if evaluation and "Success" in evaluation:
					user_msg = "✅ **Goal Achieved**"
					assistant_msg = f"**Evaluation:** {evaluation}\n**Memory:** {memory}"
					self.add_message(user_msg, assistant_msg, timestamp=False)
				elif evaluation and "Failed" in evaluation:
					user_msg = "⚠️ **Goal Status**"
					assistant_msg = f"**Evaluation:** {evaluation}\n**Memory:** {memory}"
					self.add_message(user_msg, assistant_msg, timestamp=False)
		
		except Exception as e:
			logger.error(f"Error in step callback: {e}")
	
	def done_callback(self, history: AgentHistoryList):
		"""Callback method for Agent completion"""
		try:
			self.task_completed(history)
		except Exception as e:
			logger.error(f"Error in done callback: {e}")


def create_agent_with_gui(
	task: str,
	llm,
	gui_port: int = 7860,
	gui_title: str = "Browser.AI Automation Chat",
	**agent_kwargs
) -> Tuple['Agent', BrowserAIChat]:
	"""
	Create an Agent with integrated GUI chat interface.
	
	Args:
		task: The automation task description
		llm: The language model to use
		gui_port: Port for the GUI (default: 7860)
		gui_title: Title for the GUI window
		**agent_kwargs: Additional arguments passed to Agent constructor
		
	Returns:
		Tuple of (Agent instance, BrowserAIChat instance)
	"""
	from browser_ai.agent.service import Agent
	
	# Create the chat interface
	chat_gui = BrowserAIChat(title=gui_title, port=gui_port)
	
	# Create the agent with GUI callbacks
	agent = Agent(
		task=task,
		llm=llm,
		register_new_step_callback=chat_gui.step_callback,
		register_done_callback=chat_gui.done_callback,
		**agent_kwargs
	)
	
	# Set the task in GUI
	chat_gui.set_task(task)
	
	# Launch the GUI
	chat_gui.launch()
	
	return agent, chat_gui


async def run_agent_with_gui(
	task: str,
	llm,
	max_steps: int = 100,
	gui_port: int = 7860,
	gui_title: str = "Browser.AI Automation Chat",
	**agent_kwargs
):
	"""
	Run an Agent with GUI chat interface.
	
	This is a convenience function that creates an agent with GUI
	and runs the automation task.
	
	Args:
		task: The automation task description
		llm: The language model to use  
		max_steps: Maximum steps for the agent
		gui_port: Port for the GUI (default: 7860)
		gui_title: Title for the GUI window
		**agent_kwargs: Additional arguments passed to Agent constructor
		
	Returns:
		AgentHistoryList with the execution history
	"""
	agent, chat_gui = create_agent_with_gui(
		task=task,
		llm=llm,
		gui_port=gui_port,
		gui_title=gui_title,
		**agent_kwargs
	)
	
	try:
		# Run the automation
		history = await agent.run(max_steps=max_steps)
		return history
	finally:
		# Keep GUI running after completion
		logger.info("Agent completed. GUI will remain active for monitoring.")