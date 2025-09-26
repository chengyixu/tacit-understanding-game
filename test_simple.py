import asyncio
import websockets
import json

async def test_basic():
    uri = "wss://www.panor.tech:3001/ws"
    
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri, timeout=5) as ws:
            print("Connected!")
            
            # Test register
            print("Sending register...")
            await ws.send(json.dumps({"action": "register"}))
            
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            print(f"Received: {data}")
            
            if data.get('action') == 'registered':
                print("✅ Registration successful!")
                return True
            else:
                print("❌ Unexpected response")
                return False
                
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_basic())
    if result:
        print("\n✅ WebSocket connection and registration working!")
    else:
        print("\n❌ Test failed")
