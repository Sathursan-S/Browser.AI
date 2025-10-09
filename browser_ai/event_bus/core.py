import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List, Optional, Set, Union

from .events import BaseEvent

# --- Configure basic logging for the module ---
logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """
    Abstract Base Class for all event handlers (Subscribers/Strategies).
    Any class that processes events should inherit from this.
    """
    @property
    def name(self) -> str:
        """A friendly name for the handler, defaults to the class name."""
        return self.__class__.__name__

    @abstractmethod
    def handle(self, event: BaseEvent):
        """
        The core method to process an event.
        This can be a standard synchronous method or an async coroutine.
        """
        pass


class EventManager:
    """
    Orchestrates event emission to handlers subscribed to specific topics.
    Implemented as a Singleton to provide a single, global event bus for the application.
    """
    _instance: Optional["EventManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        # A dictionary mapping a topic to a list of handlers for that topic.
        self._sync_subscriptions: Dict[str, List[EventHandler]] = defaultdict(list)
        self._async_subscriptions: Dict[str, List[EventHandler]] = defaultdict(list)
        self._loop: Union[asyncio.AbstractEventLoop, None] = None
        self._initialized = True
        logger.info("EventManager Singleton initialized.")

    def _get_running_loop(self) -> asyncio.AbstractEventLoop:
        """Safely gets the current running asyncio event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                logger.warning("No running asyncio event loop found.")
                raise
        return self._loop

    def subscribe(self, topic: str, handler: EventHandler):
        """
        Subscribes a handler to a specific topic.
        A handler can be subscribed to multiple topics.
        Use topic='*' to subscribe to ALL topics.
        """
        subscriptions = self._async_subscriptions if inspect.iscoroutinefunction(handler.handle) else self._sync_subscriptions
        if handler not in subscriptions[topic]:
            subscriptions[topic].append(handler)
            logger.info(f"Subscribed handler '{handler.name}' to topic '{topic}'")

    def unsubscribe(self, topic: str, handler: EventHandler):
        """Unsubscribes a handler from a specific topic."""
        subscriptions = self._async_subscriptions if inspect.iscoroutinefunction(handler.handle) else self._sync_subscriptions
        try:
            subscriptions[topic].remove(handler)
            logger.info(f"Unsubscribed handler '{handler.name}' from topic '{topic}'")
        except ValueError:
            logger.warning(f"Could not unsubscribe handler '{handler.name}' from topic '{topic}'. Not found.")

    def _get_handlers_for_topic(self, topic: str) -> Set[EventHandler]:
        """Gathers all unique handlers for a topic, including wildcard '*' subscribers."""
        handlers: Set[EventHandler] = set()
        
        # Add topic-specific handlers
        handlers.update(self._sync_subscriptions.get(topic, []))
        handlers.update(self._async_subscriptions.get(topic, []))

        # Add wildcard handlers
        handlers.update(self._sync_subscriptions.get('*', []))
        handlers.update(self._async_subscriptions.get('*', []))
        
        return handlers

    async def publish_async(self, topic: str, event: BaseEvent):
        """Asynchronously publishes an event to all handlers subscribed to its topic."""
        if event.topic != topic:
            logger.warning(f"Event topic mismatch! Publishing to '{topic}' but event's topic is '{event.topic}'.")

        logger.info(f"--- Publishing event '{event.name}' to topic '{topic}' (async) ---")
        handlers = self._get_handlers_for_topic(topic)
        
        sync_handlers = [h for h in handlers if not inspect.iscoroutinefunction(h.handle)]
        async_handlers = [h for h in handlers if inspect.iscoroutinefunction(h.handle)]

        for handler in sync_handlers:
            self._safe_handle(handler, event)

        async_tasks = [self._safe_async_handle(handler, event) for handler in async_handlers]
        if async_tasks:
            await asyncio.gather(*async_tasks)

    def publish(self, topic: str, event: BaseEvent):
        """Synchronously publishes an event to its topic. Async handlers are fire-and-forget."""
        if event.topic != topic:
            logger.warning(f"Event topic mismatch! Publishing to '{topic}' but event's topic is '{event.topic}'.")
            
        logger.info(f"--- Publishing event '{event.name}' to topic '{topic}' (sync) ---")
        handlers = self._get_handlers_for_topic(topic)

        sync_handlers = [h for h in handlers if not inspect.iscoroutinefunction(h.handle)]
        async_handlers = [h for h in handlers if inspect.iscoroutinefunction(h.handle)]

        for handler in sync_handlers:
            self._safe_handle(handler, event)
            
        try:
            loop = self._get_running_loop()
            for handler in async_handlers:
                loop.create_task(self._safe_async_handle(handler, event))
        except RuntimeError:
            logger.warning("Cannot schedule async handlers: no event loop found.")

    def _safe_handle(self, handler: EventHandler, event: BaseEvent):
        """Safely executes a synchronous handler, catching and logging any exceptions."""
        try:
            handler.handle(event)
        except Exception as e:
            logger.error(f"Error in sync handler {handler.name} for event {event.name}: {e}", exc_info=True)

    async def _safe_async_handle(self, handler: EventHandler, event: BaseEvent):
        """Safely executes an asynchronous handler, catching and logging any exceptions."""
        try:
            await handler.handle(event)
        except Exception as e:
            logger.error(f"Error in async handler {handler.name} for event {event.name}: {e}", exc_info=True)
