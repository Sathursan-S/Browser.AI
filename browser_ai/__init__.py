from browser_ai.logging_config import setup_logging

setup_logging()

from browser_ai.agent.prompts import SystemPrompt as SystemPrompt
from browser_ai.agent.service import Agent as Agent
from browser_ai.agent.views import ActionModel as ActionModel
from browser_ai.agent.views import ActionResult as ActionResult
from browser_ai.agent.views import AgentHistoryList as AgentHistoryList
from browser_ai.browser.browser import Browser as Browser
from browser_ai.browser.browser import BrowserConfig as BrowserConfig
from browser_ai.browser.context import BrowserContextConfig
from browser_ai.controller.service import Controller as Controller
from browser_ai.dom.service import DomService as DomService

__all__ = [
	'Agent',
	'Browser',
	'BrowserConfig',
	'Controller',
	'DomService',
	'SystemPrompt',
	'ActionResult',
	'ActionModel',
	'AgentHistoryList',
	'BrowserContextConfig',
]
