"""
WebSocket Client for Streamlit

Simple WebSocket client for real-time communication with the backend.
Note: Streamlit has limitations with WebSocket connections, so this is a simplified implementation.
"""

import asyncio
import websockets
import json
import logging
from typing import Callable, Dict, Any, Optional
import threading
import time

logger = logging.getLogger(__name__)


class WebSocketClient:
    """Simple WebSocket client for real-time communication"""
    
    def __init__(self, uri: str = "ws://localhost:8000/ws"):
        self.uri = uri
        self.websocket = None
        self.running = False
        self.message_handlers: Dict[str, Callable] = {}
        self.connection_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    def on_message(self, message_type: str, handler: Callable):
        """Register a message handler"""
        self.message_handlers[message_type] = handler
    
    def connect(self) -> bool:
        """Connect to WebSocket server"""
        try:
            if not self.running:
                self.running = True
                self.connection_thread = threading.Thread(target=self._run_connection, daemon=True)
                self.connection_thread.start()
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from WebSocket server"""
        self.running = False
        if self.websocket:
            asyncio.run(self.websocket.close())
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Send a message to the server"""
        if self.websocket and not self.websocket.closed:
            try:
                asyncio.run(self.websocket.send(json.dumps(message)))
                return True
            except Exception as e:
                logger.error(f"Failed to send message: {e}")
                return False
        return False
    
    def _run_connection(self):
        """Run the WebSocket connection in a separate thread"""
        while self.running:
            try:
                asyncio.run(self._connect_and_listen())
            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    wait_time = min(2 ** self.reconnect_attempts, 30)  # Exponential backoff
                    logger.info(f"Reconnecting in {wait_time} seconds... (attempt {self.reconnect_attempts})")
                    time.sleep(wait_time)
                else:
                    logger.error("Max reconnection attempts reached. Giving up.")
                    self.running = False
    
    async def _connect_and_listen(self):
        """Connect and listen for messages"""
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                self.reconnect_attempts = 0  # Reset on successful connection
                logger.info(f"Connected to {self.uri}")
                
                # Send initial ping
                await websocket.send(json.dumps({"type": "ping"}))
                
                async for message in websocket:
                    if not self.running:
                        break
                        
                    try:
                        data = json.loads(message)
                        message_type = data.get('type')
                        
                        if message_type in self.message_handlers:
                            handler = self.message_handlers[message_type]
                            # Run handler in thread to avoid blocking
                            threading.Thread(
                                target=handler,
                                args=(data.get('data', {}),),
                                daemon=True
                            ).start()
                        
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON message: {message}")
                    except Exception as e:
                        logger.error(f"Error handling message: {e}")
                        
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            raise


class SimpleWebSocketClient:
    """Simplified WebSocket client for Streamlit"""
    
    def __init__(self):
        self.connected = False
        self.last_ping = time.time()
    
    def connect(self) -> bool:
        """Simulate connection (for testing without real WebSocket)"""
        self.connected = True
        self.last_ping = time.time()
        return True
    
    def disconnect(self):
        """Simulate disconnection"""
        self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected"""
        # Simulate connection timeout after 5 minutes
        if self.connected and time.time() - self.last_ping > 300:
            self.connected = False
        return self.connected
    
    def ping(self):
        """Send ping to keep connection alive"""
        if self.connected:
            self.last_ping = time.time()
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Simulate sending message"""
        if not self.connected:
            return False
        # In real implementation, this would send via WebSocket
        logger.info(f"Sending message: {message}")
        return True