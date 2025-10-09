#!/usr/bin/env python3
"""
Test script to verify the config API fix
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from browser_ai_gui.config import ConfigManager


def test_config_api():
    """Test that the config API works without AttributeError"""

    print("Testing ConfigManager initialization...")
    config_manager = ConfigManager()

    print("Testing LLM config access...")
    print(f"Provider: {config_manager.llm_config.provider}")
    print(f"Model: {config_manager.llm_config.model}")
    print(
        f"Temperature: {getattr(config_manager.llm_config, 'temperature', 'NOT_FOUND')}"
    )
    print(
        f"Max tokens: {getattr(config_manager.llm_config, 'max_tokens', 'NOT_FOUND')}"
    )
    print(f"Timeout: {getattr(config_manager.llm_config, 'timeout', 'NOT_FOUND')}")

    print("\nTesting Browser config access...")
    print(f"Headless: {config_manager.browser_config.headless}")
    print(f"Disable security: {config_manager.browser_config.disable_security}")
    print(
        f"Extra args: {getattr(config_manager.browser_config, 'extra_args', 'NOT_FOUND')}"
    )

    print("\nTesting Agent config access...")
    print(f"Use vision: {config_manager.agent_config.use_vision}")
    print(f"Max failures: {config_manager.agent_config.max_failures}")
    print(f"Max steps: {config_manager.agent_config.max_steps}")

    print("\n✅ Config API test completed successfully!")


if __name__ == "__main__":
    test_config_api()
