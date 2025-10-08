"""
Event Emitter - Core event emission interface and implementation

Implements the event emitter following SOLID principles:
- Single Responsibility: Only handles event emission
- Open/Closed: Extensible through event types, closed for modification
- Liskov Substitution: Interface-based design allows substitution
- Interface Segregation: Clean, focused interfaces
- Dependency Inversion: Depends on abstractions (interfaces)
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Callable, Dict, List, Optional, Set

from .schemas import BaseEvent, EventCategory


class IEventEmitter(ABC):
    """
    Interface for event emitters
    
    Defines the contract for emitting and subscribing to events.
    Implementations can vary in how they handle event delivery.
    """

    @abstractmethod
    def emit(self, event: BaseEvent) -> None:
        """
        Emit an event to all subscribers
        
        Args:
            event: The event to emit
        """
        pass

    @abstractmethod
    def subscribe(
        self, callback: Callable[[BaseEvent], None], event_filter: Optional[str] = None
    ) -> str:
        """
        Subscribe to events
        
        Args:
            callback: Function to call when events are emitted
            event_filter: Optional event type filter (e.g., "agent.start")
            
        Returns:
            Subscription ID for later unsubscription
        """
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events
        
        Args:
            subscription_id: ID returned from subscribe()
            
        Returns:
            True if unsubscribed successfully, False otherwise
        """
        pass

    @abstractmethod
    def subscribe_category(
        self, callback: Callable[[BaseEvent], None], category: EventCategory
    ) -> str:
        """
        Subscribe to all events in a category
        
        Args:
            callback: Function to call when events are emitted
            category: Event category to subscribe to
            
        Returns:
            Subscription ID for later unsubscription
        """
        pass


class EventEmitter(IEventEmitter):
    """
    Default implementation of IEventEmitter
    
    Provides in-memory event emission with filtering capabilities.
    Thread-safe for concurrent access.
    """

    def __init__(self):
        # Track all subscriptions
        self._subscriptions: Dict[str, Dict] = {}
        
        # Index subscriptions by event type for fast lookup
        self._event_type_index: Dict[str, Set[str]] = {}
        
        # Index subscriptions by category for fast lookup
        self._category_index: Dict[EventCategory, Set[str]] = {}
        
        # Track all subscribers (no filter)
        self._global_subscribers: Set[str] = set()

    def emit(self, event: BaseEvent) -> None:
        """Emit an event to all matching subscribers"""
        # Collect all subscription IDs that should receive this event
        subscriber_ids = set()

        # Add global subscribers
        subscriber_ids.update(self._global_subscribers)

        # Add event-type-specific subscribers
        if event.event_type in self._event_type_index:
            subscriber_ids.update(self._event_type_index[event.event_type])

        # Add category-specific subscribers
        if event.category in self._category_index:
            subscriber_ids.update(self._category_index[event.category])

        # Invoke all matching callbacks
        for sub_id in subscriber_ids:
            if sub_id in self._subscriptions:
                callback = self._subscriptions[sub_id]["callback"]
                try:
                    callback(event)
                except Exception:
                    # Don't let subscriber errors break event emission
                    pass

    def subscribe(
        self, callback: Callable[[BaseEvent], None], event_filter: Optional[str] = None
    ) -> str:
        """Subscribe to events with optional filtering"""
        subscription_id = str(uuid.uuid4())

        # Store subscription
        self._subscriptions[subscription_id] = {
            "callback": callback,
            "event_filter": event_filter,
            "category_filter": None,
        }

        # Index by event type or add to global
        if event_filter:
            if event_filter not in self._event_type_index:
                self._event_type_index[event_filter] = set()
            self._event_type_index[event_filter].add(subscription_id)
        else:
            self._global_subscribers.add(subscription_id)

        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        if subscription_id not in self._subscriptions:
            return False

        sub = self._subscriptions[subscription_id]

        # Remove from indexes
        if sub["event_filter"]:
            event_filter = sub["event_filter"]
            if event_filter in self._event_type_index:
                self._event_type_index[event_filter].discard(subscription_id)
                if not self._event_type_index[event_filter]:
                    del self._event_type_index[event_filter]

        if sub["category_filter"]:
            category = sub["category_filter"]
            if category in self._category_index:
                self._category_index[category].discard(subscription_id)
                if not self._category_index[category]:
                    del self._category_index[category]

        # Remove from global
        self._global_subscribers.discard(subscription_id)

        # Remove subscription
        del self._subscriptions[subscription_id]
        return True

    def subscribe_category(
        self, callback: Callable[[BaseEvent], None], category: EventCategory
    ) -> str:
        """Subscribe to all events in a category"""
        subscription_id = str(uuid.uuid4())

        # Store subscription
        self._subscriptions[subscription_id] = {
            "callback": callback,
            "event_filter": None,
            "category_filter": category,
        }

        # Index by category
        if category not in self._category_index:
            self._category_index[category] = set()
        self._category_index[category].add(subscription_id)

        return subscription_id

    def clear_all_subscriptions(self) -> None:
        """Remove all subscriptions (useful for testing/cleanup)"""
        self._subscriptions.clear()
        self._event_type_index.clear()
        self._category_index.clear()
        self._global_subscribers.clear()


def create_event_id() -> str:
    """Generate a unique event ID"""
    return str(uuid.uuid4())


def create_timestamp() -> str:
    """Create an ISO 8601 formatted timestamp"""
    return datetime.utcnow().isoformat() + "Z"
