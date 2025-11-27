"""
Verify Log Streaming Fix

This script verifies that LogEvent objects created by event_adapter
are compatible with the protocol and can be properly serialized.
"""

import sys
from datetime import datetime

# Test import of protocol types
print("Testing protocol imports...")
try:
    from browser_ai_gui.protocol import (
        LogEvent as ProtocolLogEvent,
        LogLevel,
        EventType,
    )

    print("✅ Protocol imports successful")
except Exception as e:
    print(f"❌ Protocol import failed: {e}")
    sys.exit(1)

# Test that event_adapter uses protocol types
print("\nTesting event_adapter uses protocol types...")
try:
    from browser_ai_gui.event_adapter import (
        LogEvent as AdapterLogEvent,
        LogLevel as AdapterLogLevel,
        EventType as AdapterEventType,
    )

    # Verify they're the same classes
    if AdapterLogEvent is ProtocolLogEvent:
        print("✅ event_adapter uses protocol LogEvent (same class)")
    else:
        print("❌ event_adapter has different LogEvent class!")
        sys.exit(1)

    if AdapterLogLevel is LogLevel:
        print("✅ event_adapter uses protocol LogLevel (same class)")
    else:
        print("❌ event_adapter has different LogLevel class!")
        sys.exit(1)

    if AdapterEventType is EventType:
        print("✅ event_adapter uses protocol EventType (same class)")
    else:
        print("❌ event_adapter has different EventType class!")
        sys.exit(1)

except Exception as e:
    print(f"❌ event_adapter import failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test LogEvent creation with protocol-compatible types
print("\nTesting LogEvent creation...")
try:
    event = ProtocolLogEvent(
        timestamp=datetime.now().isoformat(),
        level=LogLevel.INFO.value,
        logger_name="test",
        message="Test message",
        event_type=EventType.LOG.value,
        metadata={"test": True},
    )
    print(f"✅ LogEvent created: {event}")

    # Test serialization
    event_dict = event.to_dict()
    print(f"✅ LogEvent serialized: {event_dict}")

    # Verify types
    assert isinstance(
        event.timestamp, str
    ), f"timestamp should be str, got {type(event.timestamp)}"
    assert isinstance(event.level, str), f"level should be str, got {type(event.level)}"
    assert isinstance(
        event.event_type, str
    ), f"event_type should be str, got {type(event.event_type)}"
    print("✅ All types are protocol-compatible (strings)")

except Exception as e:
    print(f"❌ LogEvent creation/serialization failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test that enum values are correctly used
print("\nTesting enum value conversion...")
try:
    # Simulate what LogCapture.emit() does
    level_enum = LogLevel.INFO
    event_type_enum = EventType.AGENT_START

    event = ProtocolLogEvent(
        timestamp=datetime.now().isoformat(),
        level=level_enum.value,  # Convert enum to string
        logger_name="browser_ai",
        message="Starting task",
        event_type=event_type_enum.value,  # Convert enum to string
        metadata={},
    )

    event_dict = event.to_dict()

    # Verify the values match what TypeScript expects
    assert (
        event_dict["level"] == "INFO"
    ), f"Expected 'INFO', got '{event_dict['level']}'"
    assert (
        event_dict["event_type"] == "agent_start"
    ), f"Expected 'agent_start', got '{event_dict['event_type']}'"
    print(
        f"✅ Enum values correctly converted: level={event_dict['level']}, event_type={event_dict['event_type']}"
    )

except Exception as e:
    print(f"❌ Enum conversion failed: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("🎉 All verification tests passed!")
print("=" * 60)
print("\nThe log streaming fix is working correctly:")
print("- event_adapter imports protocol types (single source of truth)")
print("- LogEvent uses string types compatible with JSON/WebSocket")
print("- Enum values are correctly converted to strings")
print("- LogEvent.to_dict() produces protocol-compatible dictionaries")
