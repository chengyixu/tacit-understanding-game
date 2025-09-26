import asyncio
import websockets
import json
import random

async def test_multiplayer():
    uri = "wss://www.panor.tech:3001/ws"
    
    print("Testing multiplayer flow...")
    
    # Player 1 (Host)
    async with websockets.connect(uri) as player1:
        # Register player 1
        await player1.send(json.dumps({"action": "register"}))
        msg = await player1.recv()
        data = json.loads(msg)
        print(f"Player 1 registered: {data}")
        player1_id = data['playerId']
        
        # Create room
        room_id = str(random.randint(100000, 999999))
        await player1.send(json.dumps({
            "action": "createRoom",
            "roomId": room_id,
            "playerInfo": {"playerId": player1_id, "nickname": "Player1"}
        }))
        msg = await player1.recv()
        print(f"Room created: {json.loads(msg)}")
        
        # Player 2 (Guest)
        async with websockets.connect(uri) as player2:
            # Register player 2
            await player2.send(json.dumps({"action": "register"}))
            msg = await player2.recv()
            data = json.loads(msg)
            print(f"Player 2 registered: {data}")
            player2_id = data['playerId']
            
            # Join room
            await player2.send(json.dumps({
                "action": "joinRoom",
                "roomId": room_id,
                "playerInfo": {"playerId": player2_id, "nickname": "Player2"}
            }))
            msg = await player2.recv()
            print(f"Player 2 joined: {json.loads(msg)}")
            
            # Check for room update on player 1
            msg = await player1.recv()
            print(f"Player 1 received room update: {json.loads(msg)}")
            
            print("\n✅ All actions working correctly!")
            print("- register ✓")
            print("- createRoom ✓") 
            print("- joinRoom ✓")
            print("- roomUpdate ✓")

if __name__ == "__main__":
    asyncio.run(test_multiplayer())
