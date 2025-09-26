#!/usr/bin/env python3
import asyncio
import websockets
import ssl
import json

async def test_connection():
    uri = "wss://47.117.176.214:3001/ws"
    
    # Create SSL context that accepts self-signed certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print(f"✓ Connected to {uri}")
            
            # Test creating a room
            create_room_msg = {
                "action": "createRoom",
                "nickname": "TestUser"
            }
            await websocket.send(json.dumps(create_room_msg))
            print(f"→ Sent: {create_room_msg}")
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"← Received: {data}")
            
            if data.get("action") == "roomCreated":
                print(f"✓ Room created successfully! Room ID: {data.get('roomId')}")
            else:
                print(f"× Unexpected response: {data}")
                
    except Exception as e:
        print(f"× Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())