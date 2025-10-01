"""
Task Manager for Browser.AI Chat Interface

Manages the execution of Browser.AI automation tasks with real-time status updates.
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging

# Import Browser.AI components
from browser_ai import Agent, Browser, Controller
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

from .event_adapter import event_adapter, LogEvent


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskInfo:
    """Information about a running task"""
    
    def __init__(self, task_id: str, description: str, config: Dict[str, Any]):
        self.task_id = task_id
        self.description = description
        self.config = config
        self.status = TaskStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.cancelled = False
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'description': self.description,
            'config': self.config,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error
        }


class TaskManager:
    """Manages Browser.AI automation tasks"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.agents: Dict[str, Agent] = {}
        
    def create_llm(self, config: Dict[str, Any]):
        """Create LLM instance based on configuration"""
        provider = config.get('provider', 'openai').lower()
        model = config.get('model', 'gpt-4')
        api_key = config.get('api_key')
        
        if provider == 'openai':
            return ChatOpenAI(
                model=model,
                openai_api_key=api_key,
                temperature=config.get('temperature', 0)
            )
        elif provider == 'anthropic':
            return ChatAnthropic(
                model=model,
                anthropic_api_key=api_key,
                temperature=config.get('temperature', 0)
            )
        elif provider == 'ollama':
            return ChatOllama(
                model=model,
                temperature=config.get('temperature', 0),
                base_url=config.get('base_url', 'http://localhost:11434')
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    async def create_task(self, description: str, config: Dict[str, Any]) -> str:
        """Create a new automation task"""
        task_id = str(uuid.uuid4())
        task_info = TaskInfo(task_id, description, config)
        self.tasks[task_id] = task_info
        
        await event_adapter.create_task_event(
            task_id, 
            "created", 
            {"description": description, "config": config}
        )
        
        return task_id
    
    async def start_task(self, task_id: str) -> bool:
        """Start a pending task"""
        if task_id not in self.tasks:
            return False
            
        task_info = self.tasks[task_id]
        if task_info.status != TaskStatus.PENDING:
            return False
        
        # Create the task coroutine
        task_coroutine = self._execute_task(task_id)
        task = asyncio.create_task(task_coroutine)
        self.running_tasks[task_id] = task
        
        task_info.status = TaskStatus.RUNNING
        task_info.started_at = datetime.now()
        
        await event_adapter.create_task_event(
            task_id,
            "started",
            {"description": task_info.description}
        )
        
        return True
    
    async def stop_task(self, task_id: str) -> bool:
        """Stop a running task"""
        if task_id not in self.running_tasks:
            return False
            
        task = self.running_tasks[task_id]
        task.cancel()
        
        task_info = self.tasks[task_id]
        task_info.cancelled = True
        task_info.status = TaskStatus.CANCELLED
        task_info.completed_at = datetime.now()
        
        del self.running_tasks[task_id]
        
        # Clean up agent if it exists
        if task_id in self.agents:
            agent = self.agents[task_id]
            # Close browser if it was created by this task
            if hasattr(agent, 'browser') and not agent.injected_browser:
                try:
                    await agent.browser.close()
                except:
                    pass
            del self.agents[task_id]
        
        await event_adapter.create_task_event(
            task_id,
            "cancelled",
            {"reason": "User requested stop"}
        )
        
        return True
    
    async def _execute_task(self, task_id: str):
        """Execute a Browser.AI automation task"""
        task_info = self.tasks[task_id]
        
        try:
            # Create LLM
            llm = self.create_llm(task_info.config['llm'])
            
            # Create browser with configuration
            browser_config = task_info.config.get('browser', {})
            browser = Browser()
            
            # Create agent
            agent = Agent(
                task=task_info.description,
                llm=llm,
                browser=browser,
                use_vision=browser_config.get('use_vision', True),
                max_failures=task_info.config.get('max_failures', 3)
            )
            
            self.agents[task_id] = agent
            
            await event_adapter.create_task_event(
                task_id,
                "agent_created",
                {"task": task_info.description}
            )
            
            # Execute the task
            result = await agent.run()
            
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.now()
            task_info.result = {
                'is_done': result.is_done,
                'extracted_content': result.extracted_content,
                'session_id': getattr(result, 'session_id', None)
            }
            
            await event_adapter.create_task_event(
                task_id,
                "completed",
                {
                    "success": result.is_done,
                    "result": task_info.result
                }
            )
            
        except asyncio.CancelledError:
            # Task was cancelled
            task_info.status = TaskStatus.CANCELLED
            task_info.completed_at = datetime.now()
            raise
            
        except Exception as e:
            task_info.status = TaskStatus.FAILED
            task_info.completed_at = datetime.now()
            task_info.error = str(e)
            
            await event_adapter.create_task_event(
                task_id,
                "failed",
                {"error": str(e)}
            )
            
        finally:
            # Clean up
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # Close browser if it was created by this task
            if task_id in self.agents:
                agent = self.agents[task_id]
                if hasattr(agent, 'browser') and not agent.injected_browser:
                    try:
                        await agent.browser.close()
                    except:
                        pass
                del self.agents[task_id]
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get information about a task"""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[TaskInfo]:
        """Get information about all tasks"""
        return list(self.tasks.values())
    
    def get_running_tasks(self) -> List[TaskInfo]:
        """Get information about currently running tasks"""
        return [
            task for task in self.tasks.values()
            if task.status == TaskStatus.RUNNING
        ]


# Global task manager instance
task_manager = TaskManager()