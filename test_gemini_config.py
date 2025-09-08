#!/usr/bin/env python3
"""
Test script to verify Gemini configuration is working
"""

import os
from chat_interface.config_manager import ConfigManager, LLMProvider

def test_gemini_config():
    """Test that Gemini configuration loads correctly"""
    print("Testing Gemini configuration...")

    # Check if API key is available
    google_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')
    if not google_key:
        print("❌ No GOOGLE_API_KEY or GEMINI_API_KEY found in environment")
        return False

    print(f"✅ Found API key: {google_key[:10]}...")

    # Create config manager
    config_manager = ConfigManager()

    # Check if Gemini config was created
    configs = config_manager.get_llm_configs()
    gemini_config = configs.get('gemini_pro')

    if not gemini_config:
        print("❌ Gemini configuration not found")
        return False

    print(f"✅ Gemini config found: {gemini_config.model} ({gemini_config.provider.value})")

    # Test creating LLM instance
    try:
        llm = config_manager.create_llm_instance(gemini_config)
        print("✅ Gemini LLM instance created successfully")
    except Exception as e:
        print(f"❌ Failed to create Gemini LLM instance: {e}")
        return False

    # Test simple inference
    try:
        response = llm.invoke("Say 'Hello from Gemini!'")
        print(f"✅ Gemini test response: {response.content[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_gemini_config()
    if success:
        print("\n🎉 Gemini configuration is working correctly!")
    else:
        print("\n❌ Gemini configuration has issues.")
