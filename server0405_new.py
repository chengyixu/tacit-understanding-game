# Keep the same content but change port to 3001
import asyncio
import json
import ssl
import uuid
import random
import time
import tornado.ioloop
import tornado.web
import tornado.websocket
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load word bank from JSON file
try:
    with open('word_bank.json', 'r', encoding='utf-8') as f:
        WORD_BANK = json.load(f)
        logger.info(f"Successfully loaded word bank with {len(WORD_BANK.get('categories', []))} categories")
except FileNotFoundError:
    logger.error("word_bank.json not found. Creating empty word bank.")
    WORD_BANK = {"categories": []}
except json.JSONDecodeError as e:
    logger.error(f"Error parsing word_bank.json: {e}")
    WORD_BANK = {"categories": []}

# Global dictionaries to store connected players and rooms
PLAYERS = {}
ROOMS = {}

class Player:
    def __init__(self, player_id, nickname):
        self.id = player_id
        self.nickname = nickname
        self.room_id = None
        self.websocket = None
        self.is_host = False
        self.last_activity = datetime.now()
        
    def to_dict(self):
        return {
            'playerId': self.id,
            'nickname': self.nickname,
            'isHost': self.is_host
        }

class Tournament:
    def __init__(self):
        self.battles = {}
        self.choices = {}
        self.current_round = 1
        self.champion = None
        self.is_complete = False

class Room:
    def __init__(self, room_id, host_id):
        self.id = room_id
        self.host_id = host_id
        self.players = set()
        self.word_pool = []
        self.player_tournaments = {}
        self.game_started = False
        self.game_completed = False
        self.tacit_value = None
        self.is_test_mode = False
        self.created_at = datetime.now()
        self.group_mode = False
        self.max_players = 2
        self.tacit_matrix = {}
        self.challenge_mode = False
        self.challenge_category = None
        
    def add_player(self, player_id):
        self.players.add(player_id)
        self.player_tournaments[player_id] = Tournament()
        
    def remove_player(self, player_id):
        self.players.discard(player_id)
        if player_id in self.player_tournaments:
            del self.player_tournaments[player_id]
            
    def get_players_info(self):
        return [PLAYERS[pid].to_dict() for pid in self.players if pid in PLAYERS]

    def generate_word_pool(self):
        """Generate random word pool from word bank"""
        if self.challenge_mode and self.challenge_category:
            # Challenge mode: use specific category
            category = next((cat for cat in WORD_BANK['categories'] 
                            if cat['id'] == self.challenge_category['id']), None)
            if category:
                self.word_pool = category['words'][:10]  # Take first 10 words
                logger.info(f"Room {self.id}: Generated challenge mode word pool with category {category['name']}")
        else:
            # Normal mode: random selection
            all_words = []
            for category in WORD_BANK['categories']:
                all_words.extend(category['words'])
            
            if len(all_words) >= 10:
                self.word_pool = random.sample(all_words, 10)
                logger.info(f"Room {self.id}: Generated random word pool with 10 words")
            else:
                self.word_pool = all_words
                logger.warning(f"Room {self.id}: Not enough words in bank, using all {len(all_words)} words")

    def generate_tournament_battles(self):
        """Generate battle sequence for tournament"""
        if not self.word_pool:
            self.generate_word_pool()
            
        words = self.word_pool.copy()
        battles = {}
        round_num = 1
        
        while len(words) > 1:
            # Randomly pair words for this round
            random.shuffle(words)
            round_battles = []
            
            # Create pairs
            for i in range(0, len(words) - 1, 2):
                round_battles.append({
                    'round': round_num,
                    'noun1': words[i],
                    'noun2': words[i + 1]
                })
            
            # If odd number, last word gets a bye
            if len(words) % 2 == 1:
                round_battles.append({
                    'round': round_num,
                    'noun1': words[-1],
                    'noun2': None,  # Bye
                    'winnerNounId': words[-1]['id']  # Auto-advance
                })
            
            battles[round_num] = round_battles[0] if round_battles else None
            
            # Simulate advancing winners for structure
            # (actual winners determined by player choices)
            words = words[:len(words)//2 + len(words)%2]
            round_num += 1
        
        return battles

    def get_current_battle(self, player_id):
        """Get current battle for a player"""
        tournament = self.player_tournaments.get(player_id)
        if not tournament:
            return None
            
        # Return current round's battle
        return tournament.battles.get(tournament.current_round)

    def submit_choice(self, player_id, noun_id):
        """Submit a player's choice for current battle"""
        tournament = self.player_tournaments.get(player_id)
        if not tournament:
            return False
        
        current_battle = tournament.battles.get(tournament.current_round)
        if not current_battle:
            return False
            
        # Store the choice
        tournament.choices[tournament.current_round] = noun_id
        
        # Determine winner for this round
        if str(noun_id) == str(current_battle['noun1']['id']):
            winner = current_battle['noun1']
            loser = current_battle['noun2']
        else:
            winner = current_battle['noun2'] 
            loser = current_battle['noun1']
        
        current_battle['winnerNounId'] = winner['id']
        
        # Check if all players in room have submitted for this round
        all_submitted = all(
            t.current_round != tournament.current_round or 
            tournament.current_round in t.choices
            for pid, t in self.player_tournaments.items() 
            if pid in self.players
        )
        
        if all_submitted:
            # Move all players to next round
            for pid in self.players:
                if pid in self.player_tournaments:
                    t = self.player_tournaments[pid]
                    if t.current_round == tournament.current_round:
                        self.advance_to_next_round(pid)
        
        return True

    def advance_to_next_round(self, player_id):
        """Advance player to next round"""
        tournament = self.player_tournaments.get(player_id)
        if not tournament:
            return
            
        current_battle = tournament.battles.get(tournament.current_round)
        if not current_battle or 'winnerNounId' not in current_battle:
            return
            
        # Get the winner word
        winner_id = current_battle['winnerNounId']
        if str(winner_id) == str(current_battle['noun1']['id']):
            winner_word = current_battle['noun1']
        else:
            winner_word = current_battle['noun2']
        
        # Move to next round
        tournament.current_round += 1
        
        # Check if tournament is complete
        if tournament.current_round > 9 or tournament.current_round > len(tournament.battles):
            tournament.champion = winner_word
            tournament.is_complete = True
            logger.info(f"Player {player_id} completed tournament with champion: {winner_word['name']}")
        else:
            # Create next round battle with winner
            next_battle = tournament.battles.get(tournament.current_round)
            if next_battle:
                # Update the next battle with the advancing word
                # This is simplified - in a real tournament bracket this would be more complex
                pass

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True
    
    def open(self):
        logger.info("WebSocket connection opened")
        self.player_id = None
        
    def on_message(self, message):
        try:
            data = json.loads(message)
            action = data.get('action')
            
            logger.info(f"Received action: {action}, data: {data}")
            
            if action == 'register':
                self.handle_register(data)
            elif action == 'createRoom':
                self.handle_create_room(data)
            elif action == 'joinRoom':
                self.handle_join_room(data)
            elif action == 'startGame':
                self.handle_start_game(data)
            elif action == 'submitChoice':
                self.handle_submit_choice(data)
            elif action == 'ping':
                self.write_message(json.dumps({'action': 'pong'}))
            elif action == 'leaveRoom':
                self.handle_leave_room(data)
            else:
                logger.warning(f"Unknown action: {action}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    def handle_register(self, data):
        """Handle player registration"""
        nickname = data.get('nickname', 'Anonymous')
        self.player_id = str(uuid.uuid4())
        
        player = Player(self.player_id, nickname)
        player.websocket = self
        PLAYERS[self.player_id] = player
        
        response = {
            'action': 'registered',
            'playerId': self.player_id,
            'nickname': nickname
        }
        self.write_message(json.dumps(response))
        logger.info(f"Player registered: {self.player_id} ({nickname})")
    
    def handle_create_room(self, data):
        """Handle room creation"""
        if not self.player_id or self.player_id not in PLAYERS:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Player not registered'
            }))
            return
            
        # Use provided room ID or generate a new one
        room_id = data.get('roomId')
        if not room_id:
            room_id = self.generate_room_id()
        
        # Check if room already exists
        if room_id in ROOMS:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Room already exists'
            }))
            return
        
        # Create room
        room = Room(room_id, self.player_id)
        room.is_test_mode = data.get('testMode', False)
        room.group_mode = data.get('groupMode', False)
        room.max_players = data.get('maxPlayers', 2)
        room.challenge_mode = data.get('challengeMode', False)
        room.challenge_category = data.get('challengeCategory')
        
        ROOMS[room_id] = room
        
        # Add player to room
        player = PLAYERS[self.player_id]
        player.room_id = room_id
        player.is_host = True
        room.add_player(self.player_id)
        
        response = {
            'action': 'roomCreated',
            'roomId': room_id,
            'isHost': True,
            'groupMode': room.group_mode,
            'maxPlayers': room.max_players
        }
        self.write_message(json.dumps(response))
        logger.info(f"Room created: {room_id} by player {self.player_id}")
        
        # If test mode, automatically add AI player
        if room.is_test_mode:
            self.add_ai_player(room_id)
    
    def add_ai_player(self, room_id):
        """Add AI player to room for testing"""
        room = ROOMS.get(room_id)
        if not room:
            return
            
        ai_id = f"ai_{uuid.uuid4()}"
        ai_player = Player(ai_id, "AI测试员")
        ai_player.room_id = room_id
        PLAYERS[ai_id] = ai_player
        room.add_player(ai_id)
        
        # Notify room update
        self.broadcast_room_update(room_id)
        logger.info(f"AI player {ai_id} added to room {room_id}")
    
    def handle_join_room(self, data):
        """Handle joining a room"""
        if not self.player_id or self.player_id not in PLAYERS:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Player not registered'
            }))
            return
            
        room_id = data.get('roomId')
        room = ROOMS.get(room_id)
        
        if not room:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Room not found'
            }))
            return
            
        if room.game_started:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Game already started'
            }))
            return
            
        if len(room.players) >= room.max_players:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Room is full'
            }))
            return
            
        # Add player to room
        player = PLAYERS[self.player_id]
        player.room_id = room_id
        player.is_host = False
        room.add_player(self.player_id)
        
        response = {
            'action': 'joinedRoom',
            'roomId': room_id,
            'isHost': False,
            'groupMode': room.group_mode,
            'maxPlayers': room.max_players
        }
        self.write_message(json.dumps(response))
        
        # Broadcast room update to all players
        self.broadcast_room_update(room_id)
        logger.info(f"Player {self.player_id} joined room {room_id}")
    
    def handle_start_game(self, data):
        """Handle game start"""
        if not self.player_id or self.player_id not in PLAYERS:
            return
            
        player = PLAYERS[self.player_id]
        room = ROOMS.get(player.room_id)
        
        if not room or not player.is_host:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Not authorized to start game'
            }))
            return
            
        if room.group_mode and len(room.players) < room.max_players:
            self.write_message(json.dumps({
                'action': 'error',
                'message': f'Need {room.max_players} players to start'
            }))
            return
        elif not room.group_mode and len(room.players) < 2:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Need at least 2 players to start'
            }))
            return
            
        # Generate word pool and battles
        room.generate_word_pool()
        
        # Generate battles for each player
        for pid in room.players:
            if pid in room.player_tournaments:
                tournament = room.player_tournaments[pid]
                # Generate same words but potentially different battle order
                tournament.battles = room.generate_tournament_battles()
        
        room.game_started = True
        
        # Broadcast game start
        for pid in room.players:
            if pid in PLAYERS:
                p = PLAYERS[pid]
                if p.websocket:
                    tournament = room.player_tournaments[pid]
                    current_battle = tournament.battles.get(1)  # First round
                    
                    response = {
                        'action': 'gameStarted',
                        'wordPool': room.word_pool,
                        'currentBattle': current_battle,
                        'totalRounds': len(tournament.battles)
                    }
                    p.websocket.write_message(json.dumps(response))
        
        logger.info(f"Game started in room {room.id}")
    
    def handle_submit_choice(self, data):
        """Handle player's choice submission"""
        if not self.player_id or self.player_id not in PLAYERS:
            return
            
        player = PLAYERS[self.player_id]
        room = ROOMS.get(player.room_id)
        
        if not room or not room.game_started:
            return
            
        noun_id = data.get('nounId')
        success = room.submit_choice(self.player_id, noun_id)
        
        if success:
            tournament = room.player_tournaments[self.player_id]
            
            # Check if tournament is complete
            if tournament.is_complete:
                # Check if all players have completed
                all_complete = all(
                    t.is_complete for t in room.player_tournaments.values()
                )
                
                if all_complete:
                    self.handle_game_complete(room)
                else:
                    # Send completion status to this player
                    response = {
                        'action': 'tournamentComplete',
                        'champion': tournament.champion,
                        'waitingForOthers': True
                    }
                    self.write_message(json.dumps(response))
            else:
                # Send next battle
                current_battle = room.get_current_battle(self.player_id)
                response = {
                    'action': 'nextBattle',
                    'currentBattle': current_battle,
                    'currentRound': tournament.current_round,
                    'totalRounds': len(tournament.battles)
                }
                self.write_message(json.dumps(response))
                
                # Notify other players of progress
                self.broadcast_game_update(room)
    
    def handle_game_complete(self, room):
        """Handle game completion"""
        # For group mode, calculate tacit matrix
        if room.group_mode:
            self.calculate_group_tacit_matrix(room)
            
            # Send results to all players
            for pid in room.players:
                if pid in PLAYERS:
                    p = PLAYERS[pid]
                    tournament = room.player_tournaments.get(pid)
                    if p.websocket and tournament:
                        response = {
                            'action': 'gameComplete',
                            'groupMode': True,
                            'myChampion': tournament.champion,
                            'tacitMatrix': room.tacit_matrix,
                            'playerRankings': self.get_player_rankings(room)
                        }
                        p.websocket.write_message(json.dumps(response))
        else:
            # Two-player mode - calculate single tacit value
            tacit_value = self.calculate_tacit_value(room)
            room.tacit_value = tacit_value
            
            # Send results to all players
            for pid in room.players:
                if pid in PLAYERS:
                    p = PLAYERS[pid]
                    tournament = room.player_tournaments.get(pid)
                    
                    # Get opponent's champion
                    opponent_champion = None
                    for other_pid in room.players:
                        if other_pid != pid and other_pid in room.player_tournaments:
                            opponent_champion = room.player_tournaments[other_pid].champion
                            break
                    
                    if p.websocket and tournament:
                        response = {
                            'action': 'gameComplete',
                            'groupMode': False,
                            'myChampion': tournament.champion,
                            'opponentChampion': opponent_champion,
                            'tacitValue': tacit_value,
                            'calculationDetails': self.get_calculation_details(room)
                        }
                        p.websocket.write_message(json.dumps(response))
        
        room.game_completed = True
        logger.info(f"Game completed in room {room.id}")
    
    def calculate_tacit_value(self, room):
        """Calculate tacit value between two players"""
        if len(room.players) != 2:
            return 0
            
        player_ids = list(room.players)
        t1 = room.player_tournaments.get(player_ids[0])
        t2 = room.player_tournaments.get(player_ids[1])
        
        if not t1 or not t2:
            return 0
            
        # Count matching choices
        matching = 0
        total = 0
        
        for round_num in range(1, 10):
            if round_num in t1.choices and round_num in t2.choices:
                # Get the battle for this round
                battle = t1.battles.get(round_num)
                if battle:
                    # Check if both players chose the same word
                    choice1 = t1.choices[round_num]
                    choice2 = t2.choices[round_num]
                    
                    # Determine position (1 or 2) for each choice
                    pos1 = 1 if str(choice1) == str(battle['noun1']['id']) else 2
                    pos2 = 1 if str(choice2) == str(battle['noun1']['id']) else 2
                    
                    if pos1 == pos2:
                        matching += 1
                    total += 1
        
        if total == 0:
            return 0
            
        return int((matching / total) * 100)
    
    def get_calculation_details(self, room):
        """Get detailed calculation breakdown"""
        if len(room.players) != 2:
            return None
            
        player_ids = list(room.players)
        t1 = room.player_tournaments.get(player_ids[0])
        t2 = room.player_tournaments.get(player_ids[1])
        
        if not t1 or not t2:
            return None
            
        details = {
            'rounds': [],
            'totalMatches': 0,
            'totalRounds': 0
        }
        
        for round_num in range(1, 10):
            if round_num in t1.choices and round_num in t2.choices:
                battle = t1.battles.get(round_num)
                if battle:
                    choice1 = t1.choices[round_num]
                    choice2 = t2.choices[round_num]
                    
                    pos1 = 1 if str(choice1) == str(battle['noun1']['id']) else 2
                    pos2 = 1 if str(choice2) == str(battle['noun1']['id']) else 2
                    
                    is_match = pos1 == pos2
                    
                    details['rounds'].append({
                        'round': round_num,
                        'player1Choice': choice1,
                        'player2Choice': choice2,
                        'isMatch': is_match
                    })
                    
                    if is_match:
                        details['totalMatches'] += 1
                    details['totalRounds'] += 1
        
        return details
    
    def calculate_group_tacit_matrix(self, room):
        """Calculate tacit value matrix for group mode"""
        import numpy as np
        from scipy.stats import pearsonr
        
        player_ids = list(room.players)
        n_players = len(player_ids)
        
        # Initialize tacit matrix
        tacit_matrix = {}
        
        # Calculate pairwise tacit values
        for i in range(n_players):
            p1_id = player_ids[i]
            tacit_matrix[p1_id] = {}
            
            for j in range(n_players):
                p2_id = player_ids[j]
                
                if i == j:
                    # Perfect tacit with self
                    tacit_matrix[p1_id][p2_id] = 100
                    continue
                
                # Get tournaments for both players
                t1 = room.player_tournaments.get(p1_id)
                t2 = room.player_tournaments.get(p2_id)
                
                if not t1 or not t2:
                    tacit_matrix[p1_id][p2_id] = 0
                    continue
                
                # Build preference matrices
                word_ids = [w['id'] for w in room.word_pool]
                n = len(word_ids)
                id_to_idx = {word_id: idx for idx, word_id in enumerate(word_ids)}
                
                matrix1 = np.zeros((n, n))
                matrix2 = np.zeros((n, n))
                
                # Fill matrix for player 1
                for round_num, battle in t1.battles.items():
                    if round_num in t1.choices:
                        id1 = battle['noun1']['id']
                        id2 = battle['noun2']['id']
                        winner_id = t1.choices[round_num]
                        
                        idx1 = id_to_idx[id1]
                        idx2 = id_to_idx[id2]
                        
                        if str(winner_id) == str(id1):
                            matrix1[idx2][idx1] = 1
                            matrix1[idx1][idx2] = 2
                        else:
                            matrix1[idx1][idx2] = 1
                            matrix1[idx2][idx1] = 2
                
                # Fill matrix for player 2
                for round_num, battle in t2.battles.items():
                    if round_num in t2.choices:
                        id1 = battle['noun1']['id']
                        id2 = battle['noun2']['id']
                        winner_id = t2.choices[round_num]
                        
                        idx1 = id_to_idx[id1]
                        idx2 = id_to_idx[id2]
                        
                        if str(winner_id) == str(id1):
                            matrix2[idx2][idx1] = 1
                            matrix2[idx1][idx2] = 2
                        else:
                            matrix2[idx1][idx2] = 1
                            matrix2[idx2][idx1] = 2
                
                # Calculate correlation
                flat1 = matrix1.flatten()
                flat2 = matrix2.flatten()
                mask = (flat1 != 0) | (flat2 != 0)
                
                if np.sum(mask) >= 2:
                    correlation, _ = pearsonr(flat1[mask], flat2[mask])
                    tacit_value = (correlation + 1) * 50
                    tacit_value = max(0, min(100, tacit_value))
                else:
                    tacit_value = 50  # Default value
                
                tacit_matrix[p1_id][p2_id] = round(tacit_value, 1)
        
        # Store matrix in room
        room.tacit_matrix = tacit_matrix
        
        # Create ranking based on average tacit scores
        player_rankings = []
        for pid in player_ids:
            if pid in PLAYERS:
                scores = [tacit_matrix[pid][other] for other in player_ids if other != pid]
                avg_score = sum(scores) / len(scores) if scores else 0
                player_rankings.append({
                    'playerId': pid,
                    'nickname': PLAYERS[pid].nickname,
                    'averageTacit': round(avg_score, 1),
                    'scores': tacit_matrix[pid]
                })
        
        # Sort by average tacit score
        player_rankings.sort(key=lambda x: x['averageTacit'], reverse=True)
        
        calculation_details = {
            'playerCount': n_players,
            'totalComparisons': n_players * (n_players - 1),
            'matrix': tacit_matrix,
            'rankings': player_rankings
        }
        
        return tacit_matrix
    
    def get_player_rankings(self, room):
        """Get player rankings for group mode"""
        player_ids = list(room.players)
        rankings = []
        
        for pid in player_ids:
            if pid in PLAYERS and pid in room.tacit_matrix:
                scores = [room.tacit_matrix[pid][other] 
                         for other in player_ids if other != pid]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                rankings.append({
                    'playerId': pid,
                    'nickname': PLAYERS[pid].nickname,
                    'champion': room.player_tournaments[pid].champion if pid in room.player_tournaments else None,
                    'averageTacit': round(avg_score, 1)
                })
        
        rankings.sort(key=lambda x: x['averageTacit'], reverse=True)
        return rankings
    
    def handle_leave_room(self, data):
        """Handle player leaving room"""
        if not self.player_id or self.player_id not in PLAYERS:
            return
            
        player = PLAYERS[self.player_id]
        room = ROOMS.get(player.room_id)
        
        if room:
            room.remove_player(self.player_id)
            player.room_id = None
            player.is_host = False
            
            # If room is empty, delete it
            if len(room.players) == 0:
                del ROOMS[room.id]
                logger.info(f"Room {room.id} deleted (empty)")
            else:
                # Transfer host if needed
                if self.player_id == room.host_id:
                    new_host_id = next(iter(room.players))
                    room.host_id = new_host_id
                    if new_host_id in PLAYERS:
                        PLAYERS[new_host_id].is_host = True
                
                # Notify remaining players
                self.broadcast_room_update(room.id)
            
            response = {
                'action': 'leftRoom'
            }
            self.write_message(json.dumps(response))
            logger.info(f"Player {self.player_id} left room {room.id}")
    
    def broadcast_room_update(self, room_id):
        """Broadcast room update to all players in the room"""
        room = ROOMS.get(room_id)
        if not room:
            return
            
        update = {
            'action': 'roomUpdate',
            'players': room.get_players_info(),
            'roomId': room_id,
            'gameStarted': room.game_started
        }
        
        for player_id in room.players:
            if player_id in PLAYERS:
                player = PLAYERS[player_id]
                if player.websocket:
                    try:
                        player.websocket.write_message(json.dumps(update))
                    except Exception as e:
                        logger.error(f"Error broadcasting to player {player_id}: {e}")
    
    def broadcast_game_update(self, room):
        """Broadcast game progress update"""
        for pid in room.players:
            if pid in PLAYERS:
                player = PLAYERS[pid]
                tournament = room.player_tournaments.get(pid)
                if player.websocket and tournament:
                    try:
                        # Count completed players
                        completed_count = sum(1 for t in room.player_tournaments.values() if t.is_complete)
                        
                        update = {
                            'action': 'gameProgress',
                            'playersCompleted': completed_count,
                            'totalPlayers': len(room.players),
                            'currentRound': tournament.current_round,
                            'isComplete': tournament.is_complete
                        }
                        player.websocket.write_message(json.dumps(update))
                    except Exception as e:
                        logger.error(f"Error broadcasting game update to player {pid}: {e}")
    
    def generate_room_id(self):
        """Generate a unique 6-digit room ID"""
        while True:
            room_id = str(random.randint(100000, 999999))
            if room_id not in ROOMS:
                return room_id
    
    def on_close(self):
        """Handle WebSocket disconnection"""
        logger.info(f"WebSocket connection closed for player {self.player_id}")
        
        if self.player_id and self.player_id in PLAYERS:
            player = PLAYERS[self.player_id]
            
            # Handle room cleanup
            if player.room_id:
                room = ROOMS.get(player.room_id)
                if room:
                    # Don't immediately remove from room, mark as disconnected
                    # This allows for reconnection
                    import tornado.ioloop
                    
                    def delayed_cleanup():
                        # Check if player reconnected
                        if self.player_id in PLAYERS:
                            p = PLAYERS[self.player_id]
                            if not p.websocket:  # Still disconnected
                                room.remove_player(self.player_id)
                                del PLAYERS[self.player_id]
                                
                                if len(room.players) == 0:
                                    del ROOMS[player.room_id]
                                    logger.info(f"Room {player.room_id} deleted (empty)")
                                else:
                                    self.broadcast_room_update(player.room_id)
                                
                                logger.info(f"Player {self.player_id} removed after disconnect timeout")
                    
                    # Give player 30 seconds to reconnect
                    tornado.ioloop.IOLoop.current().call_later(30, delayed_cleanup)
            
            # Mark player as disconnected but don't delete yet
            player.websocket = None

def make_app():
    return tornado.web.Application([
        (r"/ws", WebSocketHandler),
        (r"/", MainHandler),
    ])

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("WebSocket Server Running on port 3001")

def cleanup_expired_rooms():
    """Clean up rooms that have been idle for too long"""
    now = datetime.now()
    expired_rooms = []
    
    for room_id, room in ROOMS.items():
        # Delete rooms older than 2 hours with no activity
        if (now - room.created_at) > timedelta(hours=2):
            # Check if any players are still connected
            has_active_players = any(
                pid in PLAYERS and PLAYERS[pid].websocket 
                for pid in room.players
            )
            
            if not has_active_players:
                expired_rooms.append(room_id)
    
    for room_id in expired_rooms:
        # Clean up players in the room
        room = ROOMS[room_id]
        for pid in list(room.players):
            if pid in PLAYERS:
                del PLAYERS[pid]
        
        del ROOMS[room_id]
        logger.info(f"Cleaned up expired room {room_id}")
    
    # Schedule next cleanup
    import tornado.ioloop
    tornado.ioloop.IOLoop.current().call_later(300, cleanup_expired_rooms)  # Every 5 minutes

if __name__ == "__main__":
    if not WORD_BANK.get('categories'):
        logger.warning("Word bank is empty. Server might not function correctly.")
        
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    # SSL certificate configuration - using panor.tech certificates
    CERTFILE = "/www/server/panel/vhost/cert/www.panor.tech/fullchain.pem" 
    KEYFILE = "/www/server/panel/vhost/cert/www.panor.tech/privkey.pem"
    
    try:
        ssl_ctx.load_cert_chain(
            certfile=CERTFILE,
            keyfile=KEYFILE
        )
        logger.info(f"Successfully loaded SSL certificate from {CERTFILE} and key from {KEYFILE}")
    except FileNotFoundError:
        logger.error(f"SSL Error: Certificate or Key file not found.")
        logger.error(f"Certfile: {os.path.abspath(CERTFILE)}")
        logger.error(f"Keyfile: {os.path.abspath(KEYFILE)}")
        logger.warning("Server will start without SSL (for local testing only).")
        ssl_ctx = None
    except ssl.SSLError as e:
        logger.error(f"SSL Error: Could not load certificate/key. Error: {e}")
        logger.warning("Server will start without SSL (for local testing only).")
        ssl_ctx = None
        
    app = make_app()
    port = 3001  # Changed to 3001 to avoid conflict
    
    if ssl_ctx:
        app.listen(port, ssl_options=ssl_ctx)
        logger.info(f"Server started on wss://www.panor.tech:{port}/ws")
    else:
        app.listen(port)
        logger.info(f"Server started on ws://47.117.176.214:{port}/ws (NO SSL)")
        
    # Start periodic cleanup task
    tornado.ioloop.IOLoop.current().call_later(60, cleanup_expired_rooms)
    
    tornado.ioloop.IOLoop.current().start()