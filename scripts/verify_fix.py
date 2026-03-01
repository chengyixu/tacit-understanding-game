#!/usr/bin/env python3
"""Verify the tournament fixes are working"""

import asyncio
import websockets
import json
import random

async def test_game():
    uri = "wss://www.panor.tech:3001/ws"
    
    print("Connecting to server...")
    
    # Connect two players
    async with websockets.connect(uri) as ws1, websockets.connect(uri) as ws2:
        
        # Register Player 1
        await ws1.send(json.dumps({'action': 'register', 'nickname': 'TestPlayer1'}))
        p1_reg = json.loads(await ws1.recv())
        p1_id = p1_reg['playerId']
        print(f"Player 1 registered: {p1_id[:8]}...")
        
        # Register AI (Player 2)
        room_id = str(random.randint(100000, 999999))
        
        # Create room with AI
        await ws1.send(json.dumps({'action': 'createRoom', 'isTestMode': True}))
        create_resp = json.loads(await ws1.recv())
        room_id = create_resp['roomId']
        print(f"Room created: {room_id}")
        
        # Wait for AI to join
        room_update = json.loads(await ws1.recv())
        print(f"AI joined, players: {room_update.get('playerCount', 0)}")
        
        # Start game
        await ws1.send(json.dumps({'action': 'startGame'}))
        
        # Get initial battles
        game_start = json.loads(await ws1.recv())
        if game_start['action'] == 'gameStarted':
            p1_battle = game_start.get('currentBattle')
            if p1_battle:
                print(f"\n=== ROUND 1 ===")
                print(f"Player 1 sees: {p1_battle['noun1']['name']} vs {p1_battle['noun2']['name']}")
                
                # Check server logs to see what AI got
                print(f"\nCheck server logs at 47.117.176.214:/moqiyouxi_backend/server.log")
                print(f"Look for lines with player IDs to see if they got different sequences")
        
        await ws1.close()

if __name__ == "__main__":
    print("Testing tournament fix...\n")
    asyncio.run(test_game())