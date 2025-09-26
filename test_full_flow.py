#!/usr/bin/env python3
import asyncio
import websockets
import ssl
import json

async def test_full_connection():
    uri = "wss://www.panor.tech:3001/ws"
    
    # Create SSL context that accepts self-signed certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print(f"✓ Connected to {uri}")
            
            # Step 1: Register player
            register_msg = {
                "action": "register"
            }
            await websocket.send(json.dumps(register_msg))
            print(f"→ Sent: {register_msg}")
            
            response = await websocket.recv()
            data = json.loads(response)
            print(f"← Received: {data}")
            
            if data.get("action") == "registered":
                player_id = data.get("playerId")
                print(f"✓ Player registered! ID: {player_id}")
                
                # Step 2: Create room with registered player
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
                    print(f"× Room creation failed: {data}")
            else:
                print(f"× Registration failed: {data}")
                
    except Exception as e:
        print(f"× Connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_connection())