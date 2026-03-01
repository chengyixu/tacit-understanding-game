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

import numpy as np

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
        self.word_sequence = []
        self.current_champion = None
        self.challenger_index = 1
        self.total_rounds = 0

class Room:
    def __init__(self, room_id, host_id):
        self.id = room_id
        self.host_id = host_id
        self.players = []  # Changed to list to maintain player order
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
        if player_id not in self.players:  # Avoid duplicates
            self.players.append(player_id)
            self.player_tournaments[player_id] = Tournament()
        
    def remove_player(self, player_id):
        if player_id in self.players:
            self.players.remove(player_id)
        if player_id in self.player_tournaments:
            del self.player_tournaments[player_id]
            
    def get_players_info(self):
        return [PLAYERS[pid].to_dict() for pid in self.players if pid in PLAYERS]

    def generate_word_pool(self):
        """Generate random word pool from word bank"""
        # EXCLUDE categories that are only for ending purposes
        EXCLUDED_CATEGORY_IDS = [11]  # "现代CP" category
        
        if self.challenge_mode and self.challenge_category:
            # Challenge mode: use specific category
            category = next((cat for cat in WORD_BANK['categories'] 
                            if cat['id'] == self.challenge_category['id']), None)
            if category:
                self.word_pool = category['words'][:10]  # Take first 10 words
                logger.info(f"Room {self.id}: Generated challenge mode word pool with category {category['name']}")
        else:
            # Normal mode: random selection (excluding certain categories)
            all_words = []
            for category in WORD_BANK['categories']:
                # Skip excluded categories (like "现代CP")
                if category.get('id') in EXCLUDED_CATEGORY_IDS:
                    logger.info(f"Skipping category '{category.get('name')}' (id: {category.get('id')}) - excluded from word pool")
                    continue
                all_words.extend(category['words'])
            
            if len(all_words) >= 10:
                self.word_pool = random.sample(all_words, 10)
                logger.info(f"Room {self.id}: Generated random word pool with 10 words (excluded {len(EXCLUDED_CATEGORY_IDS)} categories)")
            else:
                self.word_pool = all_words
                logger.warning(f"Room {self.id}: Not enough words in bank, using all {len(all_words)} words")

    def get_current_battle(self, player_id):
        """Get current battle for a player"""
        tournament = self.player_tournaments.get(player_id)
        if not tournament:
            return None
            
        if tournament.is_complete:
            return None

        total_rounds = getattr(tournament, 'total_rounds', 0)
        if tournament.current_round > total_rounds:
            return None

        battle = tournament.battles.get(tournament.current_round)
        if battle:
            return battle

        if not tournament.word_sequence:
            return None

        if tournament.current_champion is None:
            tournament.current_champion = tournament.word_sequence[0]

        if tournament.challenger_index >= len(tournament.word_sequence):
            return None

        champion = tournament.current_champion
        challenger = tournament.word_sequence[tournament.challenger_index]
        
        # Ensure we're using the correct champion
        if not champion:
            logger.error(f"No champion for player {player_id} in round {tournament.current_round}")
            return None

        battle = {
            'round': tournament.current_round,
            'noun1': champion,
            'noun2': challenger
        }
        tournament.battles[tournament.current_round] = battle
        try:
            champ_name = champion['name'] if isinstance(champion, dict) else str(champion)
            champ_id = champion['id'] if isinstance(champion, dict) else 'N/A'
            challenger_name = challenger['name'] if isinstance(challenger, dict) else str(challenger)
            challenger_id = challenger['id'] if isinstance(challenger, dict) else 'N/A'
            logger.info(f"Generated battle for player {player_id} round {tournament.current_round}: champion={champ_name} (id:{champ_id}) vs challenger={challenger_name} (id:{challenger_id})")
        except Exception as e:
            logger.warning(f"Error logging battle generation for player {player_id}: {e}")
        return battle

    def submit_choice(self, player_id, noun_id):
        """Submit a player's choice for current battle"""
        tournament = self.player_tournaments.get(player_id)
        if not tournament:
            logger.warning(f"submit_choice called for unknown player {player_id}")
            return False

        current_round = tournament.current_round
        current_battle = tournament.battles.get(current_round)
        if not current_battle:
            current_battle = self.get_current_battle(self.player_id)
        if not current_battle:
            logger.warning(f"submit_choice: no battle found for player {player_id} round {current_round}")
            return False

        # Record the player's selection
        self._record_choice(player_id, tournament, current_round, noun_id)

        # Auto-submit choices for AI players in test mode so games progress
        if self.is_test_mode and not player_id.startswith('ai_'):
            self._auto_submit_ai_choices(current_round)

        logger.info(f"Checking submissions after player {player_id} round {current_round}")

        if self._all_players_submitted(current_round):
            logger.info(f"All players submitted for round {current_round}, advancing")
            self._advance_players_from_round(current_round)
            self.send_round_responses()

        return True  # Still return True for success

    def _record_choice(self, player_id, tournament, current_round, noun_id):
        current_battle = tournament.battles.get(current_round)
        if not current_battle:
            return

        tournament.choices[current_round] = noun_id
        logger.info(f"Player {player_id} submitted choice for round {current_round}: {noun_id}")

        noun1 = current_battle.get('noun1')
        noun2 = current_battle.get('noun2')

        # Determine which word the player chose
        try:
            noun1_id = noun1['id'] if isinstance(noun1, dict) else None
            noun2_id = noun2['id'] if isinstance(noun2, dict) else None
            
            if noun1 and str(noun_id) == str(noun1_id):
                winner = noun1
                noun1_name = noun1['name'] if isinstance(noun1, dict) else str(noun1)
                logger.info(f"Player {player_id} chose {noun1_name} (noun1)")
            elif noun2 and str(noun_id) == str(noun2_id):
                winner = noun2
                noun2_name = noun2['name'] if isinstance(noun2, dict) else str(noun2)
                logger.info(f"Player {player_id} chose {noun2_name} (noun2)")
            else:
                logger.error(f"Player {player_id} choice {noun_id} doesn't match either option")
                winner = None
        except Exception as e:
            logger.error(f"Error recording choice for player {player_id}: {e}")
            winner = None

        if winner:
            try:
                winner_id = winner['id'] if isinstance(winner, dict) else winner
                current_battle['winnerNounId'] = winner_id
                current_battle['winnerNoun'] = winner
            except Exception as e:
                logger.error(f"Error setting winner for player {player_id}: {e}")

    def _auto_submit_ai_choices(self, current_round):
        for pid in list(self.players):
            if not pid.startswith('ai_'):
                continue

            tournament = self.player_tournaments.get(pid)
            if not tournament:
                continue

            if tournament.current_round != current_round:
                continue

            if current_round in tournament.choices:
                continue

            battle = tournament.battles.get(current_round)
            if not battle:
                battle = self.get_current_battle(pid)
            if not battle:
                continue

            noun1 = battle.get('noun1')
            noun2 = battle.get('noun2')

            options = [noun for noun in (noun1, noun2) if noun]
            if not options:
                continue

            selected = random.choice(options)
            try:
                selected_name = selected['name'] if isinstance(selected, dict) else str(selected)
                selected_id = selected['id'] if isinstance(selected, dict) else selected
                logger.info(f"AI player {pid} auto-selecting {selected_name} in round {current_round}")
                self._record_choice(pid, tournament, current_round, selected_id)
                logger.info(f"AI {pid} battle after choice: {tournament.battles[current_round]}")
            except Exception as e:
                logger.error(f"Error auto-selecting for AI {pid}: {e}")

    def _all_players_submitted(self, current_round):
        submissions = [
            current_round in t.choices
            for pid, t in self.player_tournaments.items()
            if pid in self.players and t.current_round == current_round
        ]

        all_submitted = bool(submissions) and all(submissions)
        logger.info(f"Round {current_round}: submissions={submissions}, all_submitted={all_submitted}")
        return all_submitted

    def _advance_players_from_round(self, current_round):
        for pid in list(self.players):
            tournament = self.player_tournaments.get(pid)
            if tournament and tournament.current_round == current_round:
                battle = tournament.battles.get(current_round)
                if battle:
                    winner = battle.get('winnerNoun')
                    try:
                        winner_name = winner['name'] if isinstance(winner, dict) else str(winner) if winner else 'None'
                        logger.info(f"Advancing player {pid} from round {current_round}, winner: {winner_name}")
                    except Exception as e:
                        logger.warning(f"Error logging winner for player {pid}: {e}")
                self.advance_to_next_round(pid)
    
    def send_round_responses(self):
        """Send appropriate responses to all players after round advancement"""
        global PLAYERS
        logger.info(f"send_round_responses invoked for room {self.id}")
        
        # Check if all tournaments are complete
        all_complete = all(t.is_complete for t in self.player_tournaments.values())
        
        if all_complete:
            logger.info("All tournaments complete - triggering game completion")
            # This will be handled by the WebSocketHandler
            return
        
        # Send next battle to all players
        for pid in self.players:
            if pid in PLAYERS and pid in self.player_tournaments:
                player = PLAYERS[pid]
                tournament = self.player_tournaments[pid]
                
                if player.websocket:
                    if tournament.is_complete:
                        response = {
                            'action': 'tournamentComplete',
                            'champion': tournament.champion
                        }
                        logger.info(f"Sending tournamentComplete to {pid}")
                    else:
                        current_battle = self.get_current_battle(pid)
                        response = {
                            'action': 'nextBattle',
                            'currentBattle': current_battle,
                            'currentRound': tournament.current_round,
                            'totalRounds': len(tournament.battles)
                        }
                        logger.info(f"Sending nextBattle round {tournament.current_round} to {pid} -> {current_battle}")
                    
                    try:
                        player.websocket.write_message(json.dumps(response))
                    except Exception as e:
                        logger.error(f"Error sending response to {pid}: {e}")

    def advance_to_next_round(self, player_id):
        """Advance player to next round"""
        tournament = self.player_tournaments.get(player_id)
        if not tournament:
            return
            
        current_battle = tournament.battles.get(tournament.current_round)
        if not current_battle or 'winnerNounId' not in current_battle:
            logger.warning(f"No winner found for player {player_id} round {tournament.current_round}")
            return
            
        winner_word = current_battle.get('winnerNoun')
        old_champion = tournament.current_champion

        if winner_word:
            try:
                winner_name = winner_word['name'] if isinstance(winner_word, dict) else str(winner_word)
                old_champ_name = old_champion['name'] if isinstance(old_champion, dict) else str(old_champion) if old_champion else 'None'
                logger.info(f"Player {player_id} round {tournament.current_round}: {winner_name} wins, replacing champion {old_champ_name}")
                tournament.current_champion = winner_word
                new_champ_name = tournament.current_champion['name'] if isinstance(tournament.current_champion, dict) else str(tournament.current_champion)
                logger.info(f"Player {player_id} new champion set to: {new_champ_name}")
            except Exception as e:
                logger.warning(f"Error logging winner for player {player_id} round {tournament.current_round}: {e}")
                tournament.current_champion = winner_word
        else:
            logger.error(f"No winner word for player {player_id} round {tournament.current_round}")

        tournament.challenger_index += 1
        tournament.current_round += 1
        
        # Log next challenger for debugging with type safety
        if tournament.challenger_index < len(tournament.word_sequence):
            next_challenger = tournament.word_sequence[tournament.challenger_index]
            try:
                champ_name = tournament.current_champion['name'] if isinstance(tournament.current_champion, dict) else str(tournament.current_champion) if tournament.current_champion else 'None'
                challenger_name = next_challenger['name'] if isinstance(next_challenger, dict) else str(next_challenger)
                logger.info(f"Player {player_id} next round {tournament.current_round}: champion={champ_name} vs challenger={challenger_name}")
            except Exception as e:
                logger.warning(f"Error logging next round for player {player_id}: {e}")

        total_rounds = getattr(tournament, 'total_rounds', len(tournament.word_sequence) - 1)

        if tournament.challenger_index >= len(tournament.word_sequence):
            total_rounds = min(total_rounds, tournament.current_round - 1)

        if tournament.current_round > total_rounds or tournament.challenger_index >= len(tournament.word_sequence):
            tournament.champion = winner_word if winner_word else tournament.current_champion
            tournament.is_complete = True
            try:
                champ_name = tournament.champion['name'] if isinstance(tournament.champion, dict) else str(tournament.champion) if tournament.champion else '未知'
                logger.info(f"Player {player_id} completed tournament with champion: {champ_name}")
            except Exception as e:
                logger.warning(f"Error logging tournament completion for player {player_id}: {e}")
            logger.info(f"Tournament state - round: {tournament.current_round}, complete: {tournament.is_complete}")
        else:
            # Clear cache for next round to force regeneration with new champion
            if tournament.current_round in tournament.battles:
                del tournament.battles[tournament.current_round]
            try:
                champ_name = tournament.current_champion['name'] if isinstance(tournament.current_champion, dict) else str(tournament.current_champion) if tournament.current_champion else 'None'
                logger.info(f"Player {player_id} advanced to round {tournament.current_round}, champion: {champ_name}")
            except Exception as e:
                logger.warning(f"Error logging round advancement for player {player_id}: {e}")

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
            elif action == 'updateNickname':
                self.handle_update_nickname(data)
            elif action == 'ping':
                self.write_message(json.dumps({'action': 'pong'}))
            elif action == 'leaveRoom':
                self.handle_leave_room(data)
            elif action == 'play_again':
                self.handle_play_again(data)
            elif action == 'requestGameState':
                self.handle_request_game_state(data)
            else:
                logger.warning(f"Unknown action: {action}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
    
    def handle_register(self, data):
        """Handle player registration or reconnection"""
        nickname = data.get('nickname', 'Anonymous')
        existing_player_id = data.get('playerId')
        
        # Check if this is a reconnection with existing player ID
        if existing_player_id and existing_player_id in PLAYERS:
            # Reconnecting existing player
            self.player_id = existing_player_id
            player = PLAYERS[existing_player_id]
            player.websocket = self  # Update WebSocket connection
            
            response = {
                'action': 'registered',
                'playerId': self.player_id,
                'nickname': player.nickname  # Keep existing nickname
            }
            self.write_message(json.dumps(response))
            logger.info(f"Player reconnected: {self.player_id} ({player.nickname})")
        else:
            # New player registration
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
    
    def handle_update_nickname(self, data):
        """Handle nickname update"""
        if not self.player_id or self.player_id not in PLAYERS:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Player not registered'
            }))
            return
            
        nickname = data.get('nickname', 'Anonymous')
        player = PLAYERS[self.player_id]
        player.nickname = nickname
        
        response = {
            'action': 'nicknameUpdated',
            'nickname': nickname
        }
        self.write_message(json.dumps(response))
        logger.info(f"Player {self.player_id} updated nickname to: {nickname}")
        
        # If player is in a room, broadcast the update to all room members
        if player.room_id:
            self.broadcast_room_update(player.room_id)
    
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
            room = ROOMS[room_id]
            # If this player is already the host, treat as reconnection
            if room.host_id == self.player_id:
                # Update test mode if provided
                test_mode = data.get('testMode', False)
                room.is_test_mode = test_mode
                logger.info(f"Reconnection - testMode: {test_mode}, room.is_test_mode: {room.is_test_mode}")
                
                # Check if we need to add AI player
                if test_mode:
                    # Check if AI already exists in room
                    has_ai = any(pid.startswith('ai_') for pid in room.players)
                    logger.info(f"Room {room_id} has AI: {has_ai}, players: {room.players}")
                    if not has_ai:
                        # Add AI player
                        ai_id = f"ai_{str(uuid.uuid4())[:8]}"
                        ai_player = Player(ai_id, "AI测试员")
                        ai_player.room_id = room_id
                        PLAYERS[ai_id] = ai_player
                        room.add_player(ai_id)
                        logger.info(f"AI player {ai_id} added to room {room_id} on reconnection")
                
                # Send room created response (for compatibility)
                response = {
                    'action': 'roomCreated',
                    'roomId': room_id,
                    'isHost': True
                }
                self.write_message(json.dumps(response))
                
                # Send room update with current players
                self.broadcast_room_update(room_id)
                logger.info(f"Host {self.player_id} reconnected to room {room_id} (testMode: {test_mode})")
                return
            else:
                # Someone else is trying to create a room with same ID
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
        
        # If test mode, automatically add AI player immediately
        if room.is_test_mode:
            # Add AI player directly
            ai_id = f"ai_{str(uuid.uuid4())[:8]}"
            ai_player = Player(ai_id, "AI测试员")
            ai_player.room_id = room_id
            PLAYERS[ai_id] = ai_player
            room.add_player(ai_id)
            logger.info(f"AI player {ai_id} added to room {room_id}")
            
            # Send room update after a short delay
            import tornado.ioloop
            tornado.ioloop.IOLoop.current().call_later(0.5, lambda: self.broadcast_room_update(room_id))
    
    def add_ai_player(self, room_id):
        """Add AI player to room for testing"""
        room = ROOMS.get(room_id)
        if not room:
            logger.warning(f"Cannot add AI player - room {room_id} not found")
            return
            
        # Check if AI already exists in room
        for player_id in room.players:
            if player_id.startswith('ai_'):
                logger.info(f"AI player already exists in room {room_id}")
                return
            
        ai_id = f"ai_{uuid.uuid4()[:8]}"
        ai_player = Player(ai_id, "AI测试员")
        ai_player.room_id = room_id
        PLAYERS[ai_id] = ai_player
        room.add_player(ai_id)
        
        logger.info(f"AI player {ai_id} added to room {room_id}")
        
        # Notify room update to all players
        self.broadcast_room_update(room_id)
    
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
            
        # Generate word pool for this game
        room.generate_word_pool()
        max_rounds = min(9, max(0, len(room.word_pool) - 1))

        # Initialize tournament state for each player with unique random sequences
        import time
        import hashlib
        
        # Create a unique random generator for each player
        base_seed = int(time.time() * 1)
        
        for idx, pid in enumerate(room.players):
            if pid not in room.player_tournaments:
                continue

            tournament = room.player_tournaments[pid]
            
            # Create a unique seed for this player using hash of player ID and base seed
            player_seed = int(hashlib.md5(f"{pid}_{base_seed}".encode()).hexdigest()[:8], 16)
            rng = random.Random(player_seed)
            
            # Generate unique sequence for this player
            sequence = rng.sample(room.word_pool, len(room.word_pool))
            tournament.word_sequence = sequence
            tournament.current_champion = sequence[0] if sequence else None
            tournament.challenger_index = 1
            tournament.total_rounds = max_rounds
            tournament.current_round = 1
            tournament.is_complete = max_rounds == 0
            tournament.battles = {}
            tournament.choices = {}
            tournament.champion = None
            
            # Safe logging with type checking
            try:
                if sequence:
                    first_word = sequence[0]['name'] if isinstance(sequence[0], dict) else str(sequence[0])
                    second_word = sequence[1]['name'] if len(sequence) > 1 and isinstance(sequence[1], dict) else str(sequence[1]) if len(sequence) > 1 else 'None'
                    logger.info(f"Player {pid} (seed: {player_seed}) sequence: first battle {first_word} vs {second_word}")
                    
                    seq_names = [w['name'] if isinstance(w, dict) else str(w) for w in sequence[:5]]
                    logger.info(f"Player {pid} full sequence: {seq_names}...")
            except Exception as e:
                logger.warning(f"Error logging sequence for player {pid}: {e}")

        room.game_started = True

        # Broadcast game start
        for pid in room.players:
            if pid in PLAYERS:
                p = PLAYERS[pid]
                if p.websocket:
                    current_battle = room.get_current_battle(pid)
                    
                    response = {
                        'action': 'gameStarted',
                        'wordPool': room.word_pool,
                        'currentBattle': current_battle,
                        'totalRounds': max_rounds
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
        
        
        # Send immediate confirmation to reduce loading time
        self.write_message(json.dumps({'action': 'choiceSubmitted', 'round': data.get('round')}))
        # Submit choice - responses are handled internally when all players submit
        success = room.submit_choice(self.player_id, noun_id)
        
        if success:
            # Check if game is complete after submission
            tournament = room.player_tournaments[self.player_id]
            logger.info(f"After submit_choice - Player {self.player_id} round: {tournament.current_round}, complete: {tournament.is_complete}")
            
            # If all tournaments are complete, handle game completion
            all_complete = all(t.is_complete for t in room.player_tournaments.values())
            if all_complete:
                logger.info("All players complete - sending game results")
                self.handle_game_complete(room)
    
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
            # Two-player mode - calculate single tacit value using matrix correlation
            tacit_value, calc_details = self.calculate_tacit_value(room)
            room.tacit_value = tacit_value
            
            # Send results to all players with perspective-adjusted details
            for pid in room.players:
                if pid in PLAYERS:
                    p = PLAYERS[pid]
                    tournament = room.player_tournaments.get(pid)
                    
                    # Get opponent's champion and ID
                    opponent_id = None
                    opponent_champion = None
                    for other_pid in room.players:
                        if other_pid != pid and other_pid in room.player_tournaments:
                            opponent_id = other_pid
                            opponent_champion = room.player_tournaments[other_pid].champion
                            break
                    
                    if p.websocket and tournament:
                        # Adjust calculation details for this player's perspective
                        adjusted_details = self._adjust_details_for_player(calc_details, pid, opponent_id, room.players)
                        
                        response = {
                            'action': 'gameComplete',
                            'groupMode': False,
                            'myChampion': tournament.champion,
                            'opponentChampion': opponent_champion,
                            'tacitValue': tacit_value,
                            'calculationDetails': adjusted_details
                        }
                        p.websocket.write_message(json.dumps(response))
        
        room.game_completed = True
        logger.info(f"Game completed in room {room.id}")
    
    def calculate_tacit_value(self, room):
        """Calculate tacit value between two players using preference matrix correlation"""
        logger.info("=" * 80)
        logger.info("开始计算默契值 (Starting Tacit Value Calculation)")
        logger.info("=" * 80)
        
        if len(room.players) != 2:
            logger.warning(f"Room {room.id} has {len(room.players)} players, need exactly 2 for tacit calculation")
            return 0, None

        player_ids = list(room.players)
        
        # For AI mode: ensure human player is always p1, AI is always p2
        # For PvP mode: maintain consistent order - host is p1, guest is p2
        if any(pid.startswith('ai_') for pid in player_ids):
            # AI mode
            if player_ids[0].startswith('ai_'):
                # Swap if AI is first
                p1_id, p2_id = player_ids[1], player_ids[0]
            else:
                p1_id, p2_id = player_ids[0], player_ids[1]
        else:
            # PvP mode - keep order as is (host first, guest second)
            p1_id, p2_id = player_ids[0], player_ids[1]
        
        player1 = PLAYERS.get(p1_id)
        player2 = PLAYERS.get(p2_id)
        logger.info(f"Player 1: {player1.nickname if player1 else 'Unknown'} ({p1_id[:8]}...)")
        logger.info(f"Player 2: {player2.nickname if player2 else 'Unknown'} ({p2_id[:8]}...)")
            
        t1 = room.player_tournaments.get(p1_id)
        t2 = room.player_tournaments.get(p2_id)

        if not t1 or not t2 or not room.word_pool:
            logger.error("Missing tournament data or word pool")
            return 0, None

        # Build word_ids list with type safety
        word_ids = []
        for w in room.word_pool:
            if isinstance(w, dict):
                word_ids.append(w['id'])
            else:
                # If it's a string or other type, use it directly
                word_ids.append(w)
        
        size = len(word_ids)
        id_to_idx = {word_id: idx for idx, word_id in enumerate(word_ids)}
        
        logger.info(f"Word pool size: {size} words")
        logger.info(f"Building preference matrices ({size}x{size})...")

        matrix1 = self._build_preference_matrix(t1, id_to_idx, size)
        matrix2 = self._build_preference_matrix(t2, id_to_idx, size)
        
        logger.info(f"Player 1 made {len(t1.choices)} choices")
        logger.info(f"Player 2 made {len(t2.choices)} choices")

        base_tacit_value, correlation, data_points = self._compute_matrix_correlation(matrix1, matrix2)

        # Check if both players have the same final champion
        champion1 = t1.champion
        champion2 = t2.champion
        
        same_champion = False
        champion_bonus = 0
        
        if champion1 and champion2:
            try:
                # Extract champion IDs for comparison
                champ1_id = champion1['id'] if isinstance(champion1, dict) else champion1
                champ2_id = champion2['id'] if isinstance(champion2, dict) else champion2
                champ1_name = champion1['name'] if isinstance(champion1, dict) else str(champion1)
                champ2_name = champion2['name'] if isinstance(champion2, dict) else str(champion2)
                
                if str(champ1_id) == str(champ2_id):
                    same_champion = True
                    champion_bonus = 15  # 15% bonus for same champion
                    logger.info("=" * 80)
                    logger.info(f"🏆 相同冠军奖励 (Same Champion Bonus)!")
                    logger.info(f"  Both players chose: {champ1_name}")
                    logger.info(f"  Bonus: +{champion_bonus}%")
                    logger.info("=" * 80)
                else:
                    logger.info("=" * 80)
                    logger.info(f"不同冠军 (Different Champions)")
                    logger.info(f"  Player 1 champion: {champ1_name}")
                    logger.info(f"  Player 2 champion: {champ2_name}")
                    logger.info("=" * 80)
            except Exception as e:
                logger.warning(f"Error comparing champions: {e}")
        
        # Apply bonus but cap at 100%
        final_tacit_value = min(100, base_tacit_value + champion_bonus)
        
        details = self._build_matrix_correlation_details(
            room,
            p1_id,
            p2_id,
            matrix1,
            matrix2,
            correlation,
            data_points,
            final_tacit_value,
            base_tacit_value,
            champion_bonus
        )
        
        logger.info("=" * 80)
        if champion_bonus > 0:
            logger.info(f"基础默契值 (Base Tacit): {base_tacit_value}%")
            logger.info(f"冠军奖励 (Champion Bonus): +{champion_bonus}%")
            logger.info(f"最终默契值 (Final Tacit Value): {final_tacit_value}%")
        else:
            logger.info(f"最终默契值 (Final Tacit Value): {final_tacit_value}%")
        logger.info("=" * 80)

        return final_tacit_value, details

    def _build_preference_matrix(self, tournament, id_to_idx, size):
        matrix = np.zeros((size, size))

        for round_num, battle in tournament.battles.items():
            if round_num not in tournament.choices:
                continue

            noun1 = battle.get('noun1')
            noun2 = battle.get('noun2')
            if not noun1 or not noun2:
                continue

            # Extract IDs with type safety
            if isinstance(noun1, dict):
                id1 = noun1.get('id')
            else:
                id1 = noun1
            
            if isinstance(noun2, dict):
                id2 = noun2.get('id')
            else:
                id2 = noun2
            
            if id1 not in id_to_idx or id2 not in id_to_idx:
                continue

            idx1 = id_to_idx[id1]
            idx2 = id_to_idx[id2]

            winner_id = tournament.choices[round_num]
            if str(winner_id) == str(id1):
                matrix[idx1][idx2] = 2
                matrix[idx2][idx1] = 1
            else:
                matrix[idx1][idx2] = 1
                matrix[idx2][idx1] = 2

        return matrix

    def _compute_matrix_correlation(self, matrix1, matrix2):
        logger.info("-" * 80)
        logger.info("计算矩阵相关性 (Computing Matrix Correlation)")
        logger.info("-" * 80)
        
        flat1 = matrix1.flatten()
        flat2 = matrix2.flatten()
        
        logger.info(f"Matrix 1 flattened size: {len(flat1)}")
        logger.info(f"Matrix 2 flattened size: {len(flat2)}")

        mask = (flat1 != 0) | (flat2 != 0)
        data_points = int(np.sum(mask))
        
        logger.info(f"Non-zero data points: {data_points}")

        if data_points < 2:
            logger.warning(f"Insufficient data points ({data_points} < 2), returning default tacit value 50.0")
            return 50.0, 0.0, data_points

        values1 = flat1[mask]
        values2 = flat2[mask]
        
        logger.info(f"Player 1 preference values: mean={np.mean(values1):.4f}, std={np.std(values1):.4f}")
        logger.info(f"Player 2 preference values: mean={np.mean(values2):.4f}, std={np.std(values2):.4f}")

        if np.allclose(values1, values2):
            raw_correlation = 1.0
            logger.info("Preferences are identical! Correlation = 1.0 (Perfect match)")
        else:
            std1 = np.std(values1)
            std2 = np.std(values2)

            if std1 == 0 or std2 == 0:
                raw_correlation = 0.0
                logger.info(f"Zero standard deviation detected (std1={std1:.4f}, std2={std2:.4f}), correlation = 0.0")
            else:
                raw_correlation = float(np.corrcoef(values1, values2)[0, 1])
                if np.isnan(raw_correlation):
                    raw_correlation = 0.0
                    logger.warning("Correlation is NaN, setting to 0.0")
                else:
                    logger.info(f"Pearson correlation coefficient: {raw_correlation:.4f}")

        # NEW ALGORITHM: Add 0.7 to raw correlation, then clamp between 0 and 1
        adjusted_correlation = raw_correlation + 0.7
        correlation = min(1.0, max(0.0, adjusted_correlation))
        base_tacit_value = round(correlation * 100)
        
        logger.info("-" * 80)
        logger.info("默契值计算公式 (Tacit Value Formula):")
        logger.info(f"  原始相关系数 (Raw Correlation): {raw_correlation:.4f}")
        logger.info(f"  调整后相关系数 (Adjusted): {raw_correlation:.4f} + 0.7 = {adjusted_correlation:.4f}")
        logger.info(f"  限制范围 (Clamped [0,1]): {correlation:.4f}")
        logger.info(f"  基础默契值 (Base Tacit value): {correlation:.4f} × 100 = {base_tacit_value}%")
        logger.info("-" * 80)
        
        return base_tacit_value, round(raw_correlation, 4), data_points

    def _build_matrix_correlation_details(self, room, p1_id, p2_id, matrix1, matrix2, correlation, data_points, tacit_value, base_tacit_value=None, champion_bonus=0):
        t1 = room.player_tournaments.get(p1_id)
        t2 = room.player_tournaments.get(p2_id)

        player1 = PLAYERS.get(p1_id)
        player2 = PLAYERS.get(p2_id)

        choices = []
        
        logger.info("-" * 80)
        logger.info("逐轮选择对比 (Round-by-Round Choice Comparison)")
        logger.info("-" * 80)

        if t1 and t2:
            for round_num in range(1, 10):
                if round_num in t1.choices and round_num in t2.choices:
                    # Get each player's individual battle
                    battle1 = t1.battles.get(round_num)
                    battle2 = t2.battles.get(round_num)
                    
                    if not battle1 or not battle2:
                        continue

                    # Player 1's battle
                    p1_noun1 = battle1.get('noun1')
                    p1_noun2 = battle1.get('noun2')
                    
                    # Player 2's battle  
                    p2_noun1 = battle2.get('noun1')
                    p2_noun2 = battle2.get('noun2')
                    
                    if not p1_noun1 or not p1_noun2 or not p2_noun1 or not p2_noun2:
                        continue

                    choice1 = t1.choices[round_num]
                    choice2 = t2.choices[round_num]

                    # Extract names and IDs with type safety
                    try:
                        p1_noun1_name = p1_noun1['name'] if isinstance(p1_noun1, dict) else str(p1_noun1)
                        p1_noun1_id = p1_noun1['id'] if isinstance(p1_noun1, dict) else p1_noun1
                        p1_noun2_name = p1_noun2['name'] if isinstance(p1_noun2, dict) else str(p1_noun2)
                        p1_noun2_id = p1_noun2['id'] if isinstance(p1_noun2, dict) else p1_noun2
                        
                        p2_noun1_name = p2_noun1['name'] if isinstance(p2_noun1, dict) else str(p2_noun1)
                        p2_noun1_id = p2_noun1['id'] if isinstance(p2_noun1, dict) else p2_noun1
                        p2_noun2_name = p2_noun2['name'] if isinstance(p2_noun2, dict) else str(p2_noun2)
                        p2_noun2_id = p2_noun2['id'] if isinstance(p2_noun2, dict) else p2_noun2
                        
                        # Determine what each player chose from their own battle
                        p1_choice = p1_noun1_name if str(choice1) == str(p1_noun1_id) else p1_noun2_name
                        p2_choice = p2_noun1_name if str(choice2) == str(p2_noun1_id) else p2_noun2_name

                        # Log the round comparison
                        logger.info(f"Round {round_num}:")
                        logger.info(f"  {player1.nickname if player1 else 'Player1'}: [{p1_noun1_name} vs {p1_noun2_name}] → {p1_choice}")
                        logger.info(f"  {player2.nickname if player2 else 'Player2'}: [{p2_noun1_name} vs {p2_noun2_name}] → {p2_choice}")

                        choices.append({
                            'round': round_num,
                            'player1_battle': f"{p1_noun1_name} vs {p1_noun2_name}",
                            'player2_battle': f"{p2_noun1_name} vs {p2_noun2_name}",
                            'player1_choice': p1_choice,
                            'player2_choice': p2_choice
                        })
                    except Exception as e:
                        logger.warning(f"Error building choice comparison for round {round_num}: {e}")
        
        logger.info("-" * 80)
        logger.info(f"Total rounds compared: {len(choices)}")
        logger.info("-" * 80)

        # Build calculation string
        if base_tacit_value is not None and champion_bonus > 0:
            calc_string = f"基础值 = {base_tacit_value}%, 冠军奖励 = +{champion_bonus}%, 最终默契值 = {tacit_value}%"
        else:
            calc_string = f"相关系数 = {abs(correlation):.4f}, 默契值 = {tacit_value}%"

        details = {
            'method': 'Matrix Correlation (默契值)',
            'calculation': calc_string,
            'correlation': correlation,
            'matrix_size': f"{matrix1.shape[0]}×{matrix1.shape[1]}",
            'data_points': data_points,
            'choices': choices,
            'player1': player1.nickname if player1 else None,
            'player2': player2.nickname if player2 else None,
            'baseTacitValue': base_tacit_value if base_tacit_value is not None else tacit_value,
            'championBonus': champion_bonus,
            'finalTacitValue': tacit_value
        }

        return details
    
    def _adjust_details_for_player(self, details, player_id, opponent_id, player_list):
        """Adjust calculation details to show from the perspective of the receiving player"""
        if not details or 'choices' not in details:
            return details
        
        # Create a deep copy to avoid modifying original
        import copy
        adjusted = copy.deepcopy(details)
        
        # Get the original order: first player in list is p1, second is p2
        if not player_list or len(player_list) < 2:
            return adjusted
            
        original_p1 = player_list[0]
        original_p2 = player_list[1]
        
        # If current player was originally p2, swap everything so they see themselves as "player1"
        if player_id == original_p2:
            # Swap player names
            adjusted['player1'] = details.get('player2')
            adjusted['player2'] = details.get('player1')
            
            # Swap choices in each round
            if 'choices' in adjusted:
                swapped_choices = []
                for choice in adjusted['choices']:
                    swapped_choices.append({
                        'round': choice['round'],
                        'player1_battle': choice.get('player2_battle'),
                        'player2_battle': choice.get('player1_battle'),
                        'player1_choice': choice.get('player2_choice'),
                        'player2_choice': choice.get('player1_choice')
                    })
                adjusted['choices'] = swapped_choices
        
        return adjusted
    
    def calculate_group_tacit_matrix(self, room):
        """Calculate tacit value matrix for group mode using preference matrix correlation"""
        player_ids = list(room.players)
        n_players = len(player_ids)
        
        # Initialize tacit matrix
        tacit_matrix = {}
        
        # Build word_ids list with type safety
        word_ids = []
        for w in room.word_pool:
            if isinstance(w, dict):
                word_ids.append(w['id'])
            else:
                word_ids.append(w)
        
        size = len(word_ids)
        id_to_idx = {word_id: idx for idx, word_id in enumerate(word_ids)}

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
                
                matrix1 = self._build_preference_matrix(t1, id_to_idx, size)
                matrix2 = self._build_preference_matrix(t2, id_to_idx, size)

                tacit_value, correlation, data_points = self._compute_matrix_correlation(matrix1, matrix2)
                tacit_matrix[p1_id][p2_id] = tacit_value
        
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
        
        room.calculation_details = {
            'method': 'Matrix Correlation (默契值)',
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
    
    def handle_request_game_state(self, data):
        """Handle request for current game state after reconnection"""
        if not self.player_id or self.player_id not in PLAYERS:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Player not registered'
            }))
            return
            
        player = PLAYERS[self.player_id]
        room_id = data.get('roomId')
        room = ROOMS.get(room_id)
        
        if not room:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Room not found'
            }))
            return
            
        if self.player_id not in room.players:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'You are not in this room'
            }))
            return
        
        # Re-attach WebSocket to player
        player.websocket = self
        player.room_id = room_id
        
        logger.info(f"Player {self.player_id} reconnected and requesting game state")
        
        # Send current game state
        if room.game_started and not room.game_completed:
            tournament = room.player_tournaments.get(self.player_id)
            if tournament:
                current_battle = room.get_current_battle(self.player_id)
                if current_battle:
                    response = {
                        'action': 'gameStateUpdate',
                        'currentBattle': current_battle,
                        'currentRound': tournament.current_round,
                        'totalRounds': 9,
                        'gameStarted': True
                    }
                    self.write_message(json.dumps(response))
                    logger.info(f"Sent game state to {self.player_id}: round {tournament.current_round}")
                elif tournament.is_complete:
                    # Game is complete, send to results
                    response = {
                        'action': 'gameAlreadyComplete',
                        'message': 'Game has already finished'
                    }
                    self.write_message(json.dumps(response))
                else:
                    response = {
                        'action': 'waitingForOpponent',
                        'message': 'Waiting for opponent to finish current round'
                    }
                    self.write_message(json.dumps(response))
        else:
            response = {
                'action': 'gameNotStarted',
                'message': 'Game has not started yet'
            }
            self.write_message(json.dumps(response))
    
    def handle_play_again(self, data):
        """Handle play again request - creates new room"""
        if not self.player_id or self.player_id not in PLAYERS:
            self.write_message(json.dumps({
                'action': 'error',
                'message': 'Player not registered'
            }))
            return
            
        player = PLAYERS[self.player_id]
        old_room_id = data.get('roomId')
        old_room = ROOMS.get(old_room_id)
        
        # Clean up old room state
        if old_room and self.player_id in old_room.players:
            old_room.remove_player(self.player_id)
            if len(old_room.players) == 0:
                del ROOMS[old_room_id]
                logger.info(f"Old room {old_room_id} deleted after play_again")
        
        # Create new room
        new_room_id = str(random.randint(100000, 999999))
        while new_room_id in ROOMS:
            new_room_id = str(random.randint(100000, 999999))
        
        room = Room(new_room_id, self.player_id)
        room.add_player(self.player_id)
        ROOMS[new_room_id] = room
        
        player.room_id = new_room_id
        player.is_host = True
        
        response = {
            'action': 'newRoomCreated',
            'roomId': new_room_id,
            'isHost': True
        }
        self.write_message(json.dumps(response))
        logger.info(f"Player {self.player_id} created new room {new_room_id} for play_again")
        
        # Send room update
        self.broadcast_room_update(new_room_id)
    
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
                    
                    # Give player 5 minutes to reconnect (mobile app switching)
                    tornado.ioloop.IOLoop.current().call_later(300, delayed_cleanup)
            
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
