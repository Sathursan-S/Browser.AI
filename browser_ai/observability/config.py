"""
Laminar Configuration for Browser.AI

Centralized configuration for Laminar observability.
"""

import logging
import os
from typing import Optional

from lmnr import Laminar

logger = logging.getLogger(__name__)


class LaminarConfig:
    """Configuration manager for Laminar integration"""

    def __init__(self):
        self.project_api_key: Optional[str] = None
        self.enabled: bool = True
        self.trace_sample_rate: float = 1.0  # 1.0 = 100% sampling
        self.log_level: str = "INFO"

    def initialize_from_env(self):
        """Initialize configuration from environment variables"""

        # Get API key
        self.project_api_key = os.getenv("LMNR_PROJECT_API_KEY")

        if not self.project_api_key:
            logger.warning(
                "LMNR_PROJECT_API_KEY not set. Tracing will be disabled. "
                "Get your API key from https://www.lmnr.ai/"
            )
            self.enabled = False
            return

        # Get optional configuration
        self.enabled = os.getenv("LMNR_ENABLED", "true").lower() == "true"

        sample_rate_str = os.getenv("LMNR_TRACE_SAMPLE_RATE", "1.0")
        try:
            self.trace_sample_rate = float(sample_rate_str)
        except ValueError:
            logger.warning(
                f"Invalid LMNR_TRACE_SAMPLE_RATE: {sample_rate_str}, using 1.0"
            )
            self.trace_sample_rate = 1.0

        self.log_level = os.getenv("LMNR_LOG_LEVEL", "INFO").upper()

        # Initialize Laminar
        if self.enabled:
            try:
                Laminar.initialize(project_api_key=self.project_api_key)
                logger.info(
                    f"Laminar initialized successfully "
                    f"(sampling: {self.trace_sample_rate * 100:.0f}%)"
                )
            except Exception as e:
                logger.error(f"Failed to initialize Laminar: {e}")
                self.enabled = False

    def is_enabled(self) -> bool:
        """Check if Laminar is enabled"""
        return self.enabled

    def should_trace(self) -> bool:
        """Determine if current operation should be traced based on sampling"""
        if not self.enabled:
            return False

        if self.trace_sample_rate >= 1.0:
            return True

        import random

        return random.random() < self.trace_sample_rate


# Global configuration instance
laminar_config = LaminarConfig()

# Auto-initialize from environment on import
laminar_config.initialize_from_env()
