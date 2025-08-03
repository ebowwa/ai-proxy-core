#!/usr/bin/env python3
"""
Test script for telemetry implementation
Run with: OTEL_EXPORTER_TYPE=console python test_telemetry.py
"""
import asyncio
import os
from ai_proxy_core import CompletionsHandler, GeminiLiveSession

# Set console exporter for testing
os.environ["OTEL_EXPORTER_TYPE"] = "console"
os.environ["OTEL_ENABLED"] = "true"


async def test_completions_telemetry():
    """Test request counting for completions"""
    print("\n=== Testing Completions Telemetry ===")
    
    handler = CompletionsHandler()
    
    # Test successful request
    try:
        response = await handler.create_completion(
            messages=[{"role": "user", "content": "Say hello in 3 words"}],
            model="gemini-1.5-flash",
            max_tokens=50
        )
        print(f"✅ Success response: {response['choices'][0]['message']['content'][:50]}...")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test error case (invalid model)
    try:
        await handler.create_completion(
            messages=[{"role": "user", "content": "Test"}],
            model="invalid-model-xyz"
        )
    except Exception as e:
        print(f"✅ Expected error caught: {type(e).__name__}")
    
    # Give time for metrics to export
    await asyncio.sleep(2)


async def test_session_telemetry():
    """Test session duration tracking"""
    print("\n=== Testing Session Duration Telemetry ===")
    
    session = GeminiLiveSession(
        model="models/gemini-2.0-flash-exp",
        enable_code_execution=True,
        enable_google_search=True
    )
    
    # Track when messages are received
    message_count = 0
    
    async def on_text(text):
        nonlocal message_count
        message_count += 1
        print(f"📝 Received text: {text[:50]}...")
    
    session.on_text = on_text
    
    try:
        # Start session
        await session.start()
        print("✅ Session started")
        
        # Send a message
        await session.send_text("Hello! Count to 3 please.")
        
        # Wait for response
        await asyncio.sleep(3)
        
        # Stop session (this will record duration)
        await session.stop()
        print(f"✅ Session stopped. Messages received: {message_count}")
        
    except Exception as e:
        print(f"❌ Session error: {e}")
        await session.stop()
    
    # Give time for metrics to export
    await asyncio.sleep(2)


async def main():
    """Run all telemetry tests"""
    print("🔬 AI Proxy Core Telemetry Test")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Please set GEMINI_API_KEY environment variable")
        return
    
    # Run tests
    await test_completions_telemetry()
    await test_session_telemetry()
    
    print("\n✅ Telemetry tests completed!")
    print("\nTo see metrics in production, set:")
    print("  OTEL_EXPORTER_TYPE=otlp")
    print("  OTEL_ENDPOINT=your-collector:4317")


if __name__ == "__main__":
    asyncio.run(main())