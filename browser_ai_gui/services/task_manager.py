import asyncio
import threading
from typing import Any, Dict

from browser_ai_gui.config import ConfigManager
from browser_ai_gui.event_adapter import EventAdapter, EventType, LogLevel


class TaskManager:
    """Manages Browser.AI task execution"""

    def __init__(self, config_manager: ConfigManager, event_adapter: EventAdapter):
        self.config_manager = config_manager
        self.event_adapter = event_adapter
        self.current_agent = None
        self.current_task = None
        self.is_running = False
        self.task_thread = None

    async def start_task(self, task_description: str) -> Dict[str, Any]:
        """Start a new Browser.AI task"""
        if self.is_running:
            return {"success": False, "error": "Task already running"}

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
                validate_output=self.config_manager.agent_config.validate_output,
            )

            self.current_task = task_description
            self.is_running = True

            # Emit custom event
            self.event_adapter.emit_custom_event(
                EventType.AGENT_START,
                f"Starting task: {task_description}",
                LogLevel.INFO,
                {"task": task_description},
            )

            # Run agent in separate thread
            def run_agent():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        self.current_agent.run(
                            max_steps=self.config_manager.agent_config.max_steps
                        )
                    )

                    # self.event_adapter.emit_custom_event(
                    #     EventType.AGENT_COMPLETE,
                    #     f"Task completed successfully",
                    #     LogLevel.INFO,
                    #     {"result": str(result)},
                    # )

                except Exception as e:
                    self.event_adapter.emit_custom_event(
                        EventType.AGENT_ERROR,
                        f"Task failed: {str(e)}",
                        LogLevel.ERROR,
                        {"error": str(e)},
                    )
                finally:
                    # Only clean up if the task is actually done or stopped
                    if self.current_agent and (
                        getattr(self.current_agent, "is_stopped", lambda: False)()
                        or not self.is_running
                    ):
                        print("Task completed or stopped - cleaning up agent reference")
                        self.is_running = False
                        self.current_agent = None
                        self.current_task = None
                    else:
                        print("Agent still running or paused - keeping reference")

            self.task_thread = threading.Thread(target=run_agent, daemon=True)
            self.task_thread.start()

            return {"success": True, "message": "Task started successfully"}

        except Exception as e:
            self.is_running = False
            return {"success": False, "error": str(e)}

    def stop_task(self) -> Dict[str, Any]:
        """Stop the current task"""
        if not self.is_running or not self.current_agent:
            return {"success": False, "error": "No task running"}

        try:
            self.current_agent.stop()
            self.event_adapter.emit_custom_event(
                EventType.AGENT_STOP, "Task stopped by user", LogLevel.INFO
            )
            return {"success": True, "message": "Task stopped successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def pause_task(self) -> Dict[str, Any]:
        """Pause the current task"""
        if not self.is_running or not self.current_agent:
            return {"success": False, "error": "No task running"}

        try:
            self.current_agent.pause()
            self.event_adapter.emit_custom_event(
                EventType.AGENT_PAUSE, "Task paused by user", LogLevel.INFO
            )
            return {"success": True, "message": "Task paused successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def resume_task(self) -> Dict[str, Any]:
        """Resume the current task"""
        print(
            f"Resume task called - is_running: {self.is_running}, has_agent: {self.current_agent is not None}"
        )

        if not self.is_running:
            return {"success": False, "error": "No task currently running"}

        if not self.current_agent:
            return {"success": False, "error": "No agent available to resume"}

        try:
            print(f"Calling resume on agent: {id(self.current_agent)}")
            self.current_agent.resume()
            self.event_adapter.emit_custom_event(
                EventType.AGENT_RESUME, "Task resumed by user", LogLevel.INFO
            )
            return {"success": True, "message": "Task resumed successfully"}
        except Exception as e:
            print(f"Error resuming task: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Get current task status"""
        return {
            "is_running": self.is_running,
            "current_task": self.current_task,
            "has_agent": self.current_agent is not None,
        }
