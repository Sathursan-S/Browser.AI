"""
Event Transport - Handles delivery of events to external systems

Provides transport layer abstraction following SOLID principles.
Separates event emission from event delivery mechanism.
"""

from abc import ABC, abstractmethod
from typing import Callable, Optional

from .schemas import BaseEvent


class IEventTransport(ABC):
    """
    Interface for event transport mechanisms
    
    Defines how events are delivered to external systems (WebSocket, HTTP, etc.)
    """

    @abstractmethod
    def send(self, event: BaseEvent) -> None:
        """
        Send an event to the transport destination
        
        Args:
            event: The event to send
        """
        pass

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the transport destination
        
        Returns:
            True if connected successfully
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the transport destination"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if transport is connected
        
        Returns:
            True if connected
        """
        pass


class EventTransport(IEventTransport):
    """
    Default event transport implementation
    
    Supports multiple transport backends (WebSocket, callbacks, etc.)
    """

    def __init__(
        self,
        socketio=None,
        namespace: Optional[str] = None,
        event_name: str = "event",
    ):
        """
        Initialize event transport
        
        Args:
            socketio: Flask-SocketIO instance for WebSocket transport
            namespace: WebSocket namespace
            event_name: Event name to emit on WebSocket
        """
        self.socketio = socketio
        self.namespace = namespace
        self.event_name = event_name
        self._connected = False
        self._callbacks: list[Callable[[BaseEvent], None]] = []

    def send(self, event: BaseEvent) -> None:
        """Send event via configured transports"""
        # Send via WebSocket if configured
        if self.socketio and self._connected:
            try:
                self.socketio.emit(
                    self.event_name, event.to_dict(), namespace=self.namespace
                )
            except Exception:
                # Don't let transport errors break event emission
                pass

        # Invoke registered callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception:
                pass

    def connect(self) -> bool:
        """Mark transport as connected"""
        self._connected = True
        return True

    def disconnect(self) -> None:
        """Mark transport as disconnected"""
        self._connected = False

    def is_connected(self) -> bool:
        """Check connection status"""
        return self._connected

    def add_callback(self, callback: Callable[[BaseEvent], None]) -> None:
        """
        Add a callback for event delivery
        
        Args:
            callback: Function to call when events are sent
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[BaseEvent], None]) -> None:
        """
        Remove a callback
        
        Args:
            callback: Callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)


class MultiTransport(IEventTransport):
    """
    Composite transport that sends events to multiple destinations
    
    Useful for broadcasting events to multiple channels simultaneously.
    """

    def __init__(self):
        self._transports: list[IEventTransport] = []

    def add_transport(self, transport: IEventTransport) -> None:
        """Add a transport to the list"""
        if transport not in self._transports:
            self._transports.append(transport)

    def remove_transport(self, transport: IEventTransport) -> None:
        """Remove a transport from the list"""
        if transport in self._transports:
            self._transports.remove(transport)

    def send(self, event: BaseEvent) -> None:
        """Send event to all transports"""
        for transport in self._transports:
            try:
                transport.send(event)
            except Exception:
                # Continue even if one transport fails
                pass

    def connect(self) -> bool:
        """Connect all transports"""
        all_connected = True
        for transport in self._transports:
            if not transport.connect():
                all_connected = False
        return all_connected

    def disconnect(self) -> None:
        """Disconnect all transports"""
        for transport in self._transports:
            try:
                transport.disconnect()
            except Exception:
                pass

    def is_connected(self) -> bool:
        """Check if at least one transport is connected"""
        return any(t.is_connected() for t in self._transports)
