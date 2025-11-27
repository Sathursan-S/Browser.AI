from flask_socketio import SocketIO
from ..core import EventHandler
from ..events import BaseEvent

class WebSocketEventHandler(EventHandler):
    def __init__(self, socketio: SocketIO, namespace: str):
        self.socketio = socketio
        self.namespace = namespace

    def handle(self, event: BaseEvent):
        self.socketio.emit('agent_event', event.model_dump(), namespace=self.namespace)
