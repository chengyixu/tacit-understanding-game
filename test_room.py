import asyncio
import websockets
import json
import random

async def test_room():
    uri = "wss://www.panor.tech:3001/ws"
    
    try:
        print("Testing room creation and joining...")
        
        # Connect player 1
        async with websockets.connect(uri, timeout=5) as ws1:
            print("\n1. Registering Player 1...")
            await ws1.send(json.dumps({"action": "register"}))
            msg = await asyncio.wait_for(ws1.recv(), timeout=5)
            player1_data = json.loads(msg)
            player1_id = player1_data['playerId']
            print(f"   Player 1 ID: {player1_id}")
            
            # Create room
            room_id = str(random.randint(100000, 999999))
            print(f"\n2. Creating room {room_id}...")
            await ws1.send(json.dumps({
                "action": "createRoom",
                "roomId": room_id,
                "playerInfo": {"playerId": player1_id, "nickname": "Host"}
            }))
            msg = await asyncio.wait_for(ws1.recv(), timeout=5)
            room_data = json.loads(msg)
            print(f"   Response: {room_data.get('action')}")
            
            if room_data.get('action') != 'roomCreated':
                print(f"   ❌ Expected 'roomCreated', got: {room_data}")
                return False
            
            # Connect player 2
            async with websockets.connect(uri, timeout=5) as ws2:
                print("\n3. Registering Player 2...")
                await ws2.send(json.dumps({"action": "register"}))
                msg = await asyncio.wait_for(ws2.recv(), timeout=5)
                player2_data = json.loads(msg)
                player2_id = player2_data['playerId']
                print(f"   Player 2 ID: {player2_id}")
                
                # Join room
                print(f"\n4. Player 2 joining room {room_id}...")
                await ws2.send(json.dumps({
                    "action": "joinRoom",
                    "roomId": room_id,
                    "playerInfo": {"playerId": player2_id, "nickname": "Guest"}
                }))
                msg = await asyncio.wait_for(ws2.recv(), timeout=5)
                join_data = json.loads(msg)
                print(f"   Response: {join_data.get('action')}")
                
                if join_data.get('action') != 'joinedRoom':
                    print(f"   ❌ Expected 'joinedRoom', got: {join_data}")
                    return False
                
                # Check for room update
                print("\n5. Checking for roomUpdate to Player 1...")
                msg = await asyncio.wait_for(ws1.recv(), timeout=5)
                update_data = json.loads(msg)
                print(f"   Response: {update_data.get('action')}")
                
                if update_data.get('action') == 'roomUpdate':
                    print(f"   Players in room: {len(update_data.get('players', []))}")
                    return True
                else:
                    print(f"   ❌ Expected 'roomUpdate', got: {update_data}")
                    return False
                
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_room())
    if result:
        print("\n✅ Room creation and joining working correctly!")
        print("   - createRoom → roomCreated ✓")
        print("   - joinRoom → joinedRoom ✓")
        print("   - Automatic roomUpdate broadcast ✓")
    else:
        print("\n❌ Room test failed")
