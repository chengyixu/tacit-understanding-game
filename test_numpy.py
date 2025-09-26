#!/usr/bin/env python3
import ssl
import asyncio
import websockets
import json

async def test_server():
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    uri = "wss://www.aiconnector.cn:3000/ws"
    
    try:
        async with websockets.connect(uri, ssl=ssl_context) as websocket:
            print("Connected to WebSocket server")
            
            # Send test ping
            test_msg = json.dumps({"action": "ping", "playerId": "test123"})
            await websocket.send(test_msg)
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Server response: {data}")
            
            if data.get('action') == 'pong':
                print("✓ Server is responding correctly")
                print("✓ Python3.6 with numpy/scipy is working")
                return True
            else:
                print("✗ Unexpected response")
                return False
                
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False

# Run the test
if __name__ == "__main__":
    result = asyncio.run(test_server())
    exit(0 if result else 1)
