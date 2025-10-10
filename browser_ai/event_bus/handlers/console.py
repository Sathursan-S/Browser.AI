import logging

from ..core import EventHandler
from ..events import BaseEvent

logger = logging.getLogger(__name__)


class ConsoleHandler(EventHandler):
    """A simple handler strategy that prints event details to the console."""

    def handle(self, event: BaseEvent):
        """Logs the received event information."""
        logger.info(
            f"[{self.name}] Received Event on topic '{event.topic}':\n"
            f"{event.model_dump_json(indent=2)}\n"
        )
