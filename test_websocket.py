#!/usr/bin/env python3
"""
Test WebSocket connection script for Django Social Media
"""
import asyncio
import websockets
import json
import sys

async def test_websocket(url):
    """Connect to a WebSocket server and run a basic test"""
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url) as websocket:
            print("✅ Connected successfully!")
            
            # Wait for the initial connection message
            initial_msg = await websocket.recv()
            print(f"Received: {initial_msg}")
            
            # Send a test message
            test_command = {
                "command": "ping"
            }
            print(f"Sending: {json.dumps(test_command)}")
            await websocket.send(json.dumps(test_command))
            
            # Wait for a response (up to 5 seconds)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"Received response: {response}")
            except asyncio.TimeoutError:
                print("Timed out waiting for response")
            
            print("Test completed successfully!")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    websocket_url = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:8000/messages/"
    asyncio.run(test_websocket(websocket_url))
