# -*- coding: utf-8 -*-
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

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage
ROOMS = {}
PLAYERS = {}
CONNECTIONS = {}

# Load word bank
WORD_BANK = {'categories': []}
WORD_BANK_FILE = os.path.join(os.path.dirname(__file__), "word_bank.json")

def load_word_bank():
    """Load word bank from JSON file"""
    global WORD_BANK
    try:
        with open(WORD_BANK_FILE, 'r', encoding='utf-8') as f:
            WORD_BANK = json.load(f)
        logger.info(f"Successfully loaded word bank with {len(WORD_BANK['categories'])} categories")
    except FileNotFoundError:
        logger.error(f"Word bank file '{WORD_BANK_FILE}' not found")
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from '{WORD_BANK_FILE}'")
    except Exception as e:
        logger.error(f"Error loading word bank: {e}")

load_word_bank()

class Room:
    def __init__(self, room_id, host_id):
        self.id = room_id
        self.host_id = host_id
        self.players = []
        self.game_started = False
        self.challenge_mode = False
        self.challenge_category = None
        self.test_mode = False  # AI test mode flag
        self.ai_player_id = None  # AI player ID
        self.word_pool = []  # The shared 10-word pool
        self.player_tournaments = {}  # Each player's individual tournament
        self.player_champions = {}  # Each player's final champion
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
    def update_activity(self):
        self.last_activity = datetime.now()
        
    def is_expired(self):
        # Room expires after 10 minutes of inactivity
        return datetime.now() - self.last_activity > timedelta(minutes=10)
        
    def to_dict(self):
        return {
            'id': self.id,
            'host_id': self.host_id,
            'players': self.players,
            'game_started': self.game_started,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }

class PlayerTournament:
    def __init__(self, player_id, word_pool):
        self.player_id = player_id
        self.remaining_words = word_pool.copy()  # Player's remaining words
        self.eliminated_words = []
        self.battles = {}  # Round -> battle data
        self.choices = {}  # Round -> chosen word
        self.champion = None
        self.current_round = 1  # Each player tracks their own round
        
class Player:
    def __init__(self, player_id, nickname, connection):
        self.id = player_id
        self.nickname = nickname
        self.connection = connection
        self.room_id = None
        self.is_host = False
        self.last_seen = datetime.now()
        
    def update_connection(self, connection):
        self.connection = connection
        self.last_seen = datetime.now()
        
    def to_dict(self):
        return {
            'playerId': self.id,
            'nickname': self.nickname
        }

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True
    
    def open(self):
        self.player = None
        logger.info("New WebSocket connection opened")
        
    def on_message(self, message):
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'ping':
                self.send_message({'action': 'pong'})
            elif action == 'create_room':
                self.handle_create_room(data)
            elif action == 'join_room':
                self.handle_join_room(data)
            elif action == 'reconnect':
                self.handle_reconnect(data)
            elif action == 'leave_room':
                self.handle_leave_room(data)
            elif action == 'start_game':
                self.handle_start_game(data)
            elif action == 'get_battle':
                self.handle_get_battle(data)
            elif action == 'select_noun':
                self.handle_select_noun(data)
            elif action == 'get_result':
                self.handle_get_result(data)
            elif action == 'play_again':
                self.handle_play_again(data)
            else:
                logger.warning(f"Unknown action: {action}")
                
        except json.JSONDecodeError:
            logger.error("Invalid JSON message")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self.send_error(str(e))
            
    def handle_create_room(self, data):
        room_id = str(data.get('roomId')).strip()
        player_info = data.get('playerInfo', {})
        challenge_mode = data.get('challengeMode', False)
        challenge_category = data.get('challengeCategory')
        test_mode = data.get('testMode', False)  # AI test mode
        
        logger.info(f"Create room request - ID: '{room_id}', Player: {player_info}")
        logger.info(f"Current rooms: {list(ROOMS.keys())}")
        
        if room_id in ROOMS:
            if ROOMS[room_id].is_expired():
                logger.info(f"Room {room_id} expired, creating new one")
                del ROOMS[room_id]
            else:
                # Check if this player is already in the room (reconnection)
                room = ROOMS[room_id]
                player_id = str(player_info.get('playerId'))
                
                if player_id in room.players:
                    # Player is reconnecting to their own room
                    logger.info(f"Player {player_id} reconnecting to their room {room_id}")
                    
                    # Update player connection
                    if player_id in PLAYERS:
                        player = PLAYERS[player_id]
                        player.update_connection(self)
                        self.player = player
                        CONNECTIONS[self] = player
                    
                    # Send room created response
                    self.send_message({
                        'action': 'room_created',
                        'roomId': room_id
                    })
                    
                    # If room is full (AI already joined), send opponent info
                    if len(room.players) == 2:
                        other_player_id = None
                        for p_id in room.players:
                            if p_id != player_id:
                                other_player_id = p_id
                                break
                        
                        if other_player_id and other_player_id in PLAYERS:
                            other = PLAYERS[other_player_id]
                            self.send_message({
                                'action': 'room_full',
                                'opponentInfo': other.to_dict()
                            })
                    return
                    
                elif len(room.players) < 2:
                    logger.info(f"Room {room_id} exists with {len(room.players)} players, treating as join")
                    # Redirect to join_room
                    self.handle_join_room(data)
                    return
                else:
                    logger.warning(f"Room {room_id} already exists and is full")
                    self.send_error("房间已满")
                    return
            
        player_id = str(player_info.get('playerId'))
        nickname = player_info.get('nickname', 'Unknown')
        
        if player_id in PLAYERS:
            player = PLAYERS[player_id]
            player.update_connection(self)
            logger.info(f"Player {nickname} reconnected")
        else:
            player = Player(player_id, nickname, self)
            PLAYERS[player_id] = player
            
        player.room_id = room_id
        player.is_host = True
        
        self.player = player
        CONNECTIONS[self] = player
        
        room = Room(room_id, player_id)
        room.players.append(player_id)
        room.challenge_mode = challenge_mode
        room.challenge_category = challenge_category
        room.test_mode = test_mode  # Store test mode flag
        ROOMS[room_id] = room
        
        logger.info(f"Room '{room_id}' created successfully by {nickname}")
        logger.info(f"Total rooms: {len(ROOMS)}, Room keys: {list(ROOMS.keys())}")
        logger.info(f"Player {player_id} added to PLAYERS, total players: {len(PLAYERS)}")
        logger.info(f"Player {player_id} connection set: {player.connection is not None}")
        
        self.send_message({
            'action': 'room_created',
            'roomId': room_id
        })
        
        # If test mode, automatically add AI player after a delay
        if test_mode:
            logger.info(f"Test mode enabled for room {room_id}, adding AI player")
            tornado.ioloop.IOLoop.current().call_later(1.0, 
                lambda: self.add_ai_player(room_id))
    
    def add_ai_player(self, room_id):
        """Add an AI player to the room for testing"""
        if room_id not in ROOMS:
            return
            
        room = ROOMS[room_id]
        if len(room.players) >= 2:
            return  # Room already full
            
        # Create AI player
        ai_player_id = f"AI_{uuid.uuid4().hex[:8]}"
        ai_nickname = "🤖 AI测试"
        
        # Create AI player object (no real connection)
        ai_player = Player(ai_player_id, ai_nickname, None)
        ai_player.room_id = room_id
        ai_player.is_host = False
        
        PLAYERS[ai_player_id] = ai_player
        room.players.append(ai_player_id)
        room.ai_player_id = ai_player_id
        
        logger.info(f"AI player {ai_player_id} joined room {room_id}")
        
        # Notify the human player
        host = PLAYERS.get(room.host_id)
        if host and host.connection:
            host.connection.send_message({
                'action': 'player_joined',
                'playerInfo': ai_player.to_dict()
            })
            host.connection.send_message({
                'action': 'room_full',
                'opponentInfo': ai_player.to_dict()
            })
        
    def handle_join_room(self, data):
        room_id = str(data.get('roomId')).strip()
        player_info = data.get('playerInfo', {})
        
        logger.info(f"Join room request - ID: '{room_id}', Player: {player_info}")
        logger.info(f"Available rooms: {list(ROOMS.keys())}")
        logger.info(f"Room ID type: {type(room_id)}, Room ID repr: {repr(room_id)}")
        
        if room_id not in ROOMS:
            logger.error(f"Room '{room_id}' not found")
            logger.error(f"Looking for: '{room_id}' in keys: {list(ROOMS.keys())}")
            # Debug: check each key
            for key in ROOMS.keys():
                logger.error(f"  Key: '{key}' == '{room_id}'? {key == room_id}")
            self.send_error("房间不存在")
            return
            
        room = ROOMS[room_id]
        room.update_activity()
        
        player_id = str(player_info.get('playerId'))
        nickname = player_info.get('nickname', 'Unknown')
        
        if player_id in room.players:
            logger.info(f"Player {nickname} reconnecting to room {room_id}")
            if player_id in PLAYERS:
                player = PLAYERS[player_id]
                player.update_connection(self)
            else:
                player = Player(player_id, nickname, self)
                PLAYERS[player_id] = player
            
            player.room_id = room_id
            self.player = player
            CONNECTIONS[self] = player
            
            self.send_message({
                'action': 'joined_room',
                'roomId': room_id
            })
            
            for p_id in room.players:
                if p_id != player_id and p_id in PLAYERS:
                    other_player = PLAYERS[p_id]
                    self.send_message({
                        'action': 'room_full',
                        'opponentInfo': other_player.to_dict()
                    })
            return
        
        if len(room.players) >= 2:
            logger.warning(f"Room {room_id} is full")
            self.send_error("房间已满")
            return
            
        if room.game_started:
            logger.warning(f"Game already started in room {room_id}")
            self.send_error("游戏已开始")
            return
        
        if player_id in PLAYERS:
            player = PLAYERS[player_id]
            player.update_connection(self)
        else:
            player = Player(player_id, nickname, self)
            PLAYERS[player_id] = player
            
        player.room_id = room_id
        player.is_host = False
        
        self.player = player
        CONNECTIONS[self] = player
        room.players.append(player_id)
        
        logger.info(f"{nickname} joined room {room_id} successfully. Players in room: {len(room.players)}")
        logger.info(f"Room {room_id} players: {room.players}")
        
        self.send_message({
            'action': 'joined_room',
            'roomId': room_id
        })
        
        # If room is now full, notify both players
        if len(room.players) == 2:
            logger.info(f"Room {room_id} is now full, notifying both players")
            logger.info(f"Host ID: {room.host_id}, Players in PLAYERS: {list(PLAYERS.keys())}")
            
            # Find the other player (not the one joining)
            other_player_id = None
            for p_id in room.players:
                if p_id != player_id:
                    other_player_id = p_id
                    break
            
            logger.info(f"Joining player: {player_id}, Other player: {other_player_id}")
            
            # Get the other player
            other_player = PLAYERS.get(other_player_id)
            
            if other_player:
                logger.info(f"Found other player: {other_player.nickname}, has connection: {other_player.connection is not None}")
                
                # Send to the other player (host) about this joining player
                if other_player.connection:
                    logger.info(f"Sending notifications to {other_player.nickname}")
                    other_player.connection.send_message({
                        'action': 'player_joined',
                        'playerInfo': player.to_dict()
                    })
                    other_player.connection.send_message({
                        'action': 'room_full',
                        'opponentInfo': player.to_dict()
                    })
                else:
                    logger.error(f"Other player {other_player.nickname} has no connection!")
            else:
                logger.error(f"Could not find other player with ID {other_player_id}")
                
            # Send to this joining player about the other player
            if other_player:
                self.send_message({
                    'action': 'room_full',
                    'opponentInfo': other_player.to_dict()
                })
            else:
                # Still send something so the joining player knows
                self.send_message({
                    'action': 'room_full',
                    'opponentInfo': {'nickname': 'Player 1', 'playerId': other_player_id or room.host_id}
                })
        else:
            logger.error(f"Host not found or not connected for room {room_id}")
            
    def handle_reconnect(self, data):
        room_id = str(data.get('roomId'))
        player_id = str(data.get('playerId'))
        
        logger.info(f"Reconnect request - Room: {room_id}, Player: {player_id}")
        
        if room_id not in ROOMS:
            logger.error(f"Room {room_id} not found for reconnection")
            self.send_error("房间不存在")
            return
            
        room = ROOMS[room_id]
        
        if player_id not in room.players:
            logger.error(f"Player {player_id} not in room {room_id}")
            self.send_error("您不在此房间中")
            return
            
        if player_id in PLAYERS:
            player = PLAYERS[player_id]
            player.update_connection(self)
            self.player = player
            CONNECTIONS[self] = player
            
            logger.info(f"Player {player_id} reconnected to room {room_id}")
            
            self.send_message({
                'action': 'reconnected',
                'roomId': room_id
            })
        else:
            logger.error(f"Player {player_id} not found in PLAYERS")
            
    def handle_leave_room(self, data):
        room_id = str(data.get('roomId'))
        player_id = str(data.get('playerId'))
        
        logger.info(f"Player {player_id} leaving room {room_id}")
        
        if room_id not in ROOMS:
            return
            
        room = ROOMS[room_id]
        room.update_activity()
        
        # Remove player from room
        if player_id in room.players:
            room.players.remove(player_id)
            logger.info(f"Player {player_id} left room {room_id}. Remaining players: {len(room.players)}")
            
        # Clear player's room association
        if player_id in PLAYERS:
            player = PLAYERS[player_id]
            player.room_id = None
            player.is_host = False
            
        # Notify other players
        for p_id in room.players:
            p = PLAYERS.get(p_id)
            if p and p.connection:
                p.connection.send_message({
                    'action': 'player_left',
                    'playerId': player_id
                })
                
        # Clean up empty room after some time
        if not room.players:
            logger.info(f"Room {room_id} is now empty, will expire after 10 minutes")
            
    def handle_start_game(self, data):
        room_id = str(data.get('roomId'))
        
        if room_id not in ROOMS:
            return
            
        room = ROOMS[room_id]
        room.update_activity()
        
        if len(room.players) < 2:
            return
            
        if room.game_started:
            return
            
        room.game_started = True
        # Each player tracks their own round, no room.current_round needed
        
        # Initialize shared word pool
        all_words = []
        
        if room.challenge_mode and room.challenge_category:
            category_id = room.challenge_category.get('id')
            for cat in WORD_BANK.get('categories', []):
                if cat['id'] == category_id:
                    all_words = cat['words']
                    break
        else:
            for cat in WORD_BANK.get('categories', []):
                all_words.extend(cat['words'])
                
        if len(all_words) >= 10:
            room.word_pool = random.sample(all_words, 10)
        else:
            room.word_pool = all_words.copy()
            
        # Add category names to words
        for noun in room.word_pool:
            for cat in WORD_BANK.get('categories', []):
                for word in cat['words']:
                    if word['id'] == noun['id']:
                        noun['category'] = cat['name']
                        break
        
        # Initialize each player's tournament
        for player_id in room.players:
            room.player_tournaments[player_id] = PlayerTournament(player_id, room.word_pool)
        
        logger.info(f"Game started in room {room_id} with word pool: {[n['name'] for n in room.word_pool]}")
        
        for player_id in room.players:
            player = PLAYERS.get(player_id)
            if player and player.connection:
                player.connection.send_message({
                    'action': 'game_starting'
                })
                
        tornado.ioloop.IOLoop.current().call_later(0.5, lambda: self.send_game_started(room))
        
    def send_game_started(self, room):
        for player_id in room.players:
            player = PLAYERS.get(player_id)
            if player and player.connection:
                player.connection.send_message({
                    'action': 'game_started'
                })
                
    def handle_get_battle(self, data):
        room_id = str(data.get('roomId'))
        player_id = str(data.get('playerId'))
        
        if room_id not in ROOMS:
            return
            
        room = ROOMS[room_id]
        room.update_activity()
        
        if player_id not in room.player_tournaments:
            logger.error(f"Player {player_id} has no tournament in room {room_id}")
            return
            
        tournament = room.player_tournaments[player_id]
        
        # Check if player's tournament ended
        if len(tournament.remaining_words) <= 1:
            if len(tournament.remaining_words) == 1:
                tournament.champion = tournament.remaining_words[0]
                room.player_champions[player_id] = tournament.champion
            
            self.send_message({
                'action': 'game_ended'
            })
            return
            
        # Get or create battle for this round
        if tournament.current_round not in tournament.battles:
            # Create new battle for this player
            if tournament.current_round == 1:
                # First round: random 2 words from pool
                battle_words = random.sample(tournament.remaining_words, 2)
            else:
                # Later rounds: previous winner vs random opponent
                prev_winner_id = tournament.choices.get(tournament.current_round - 1)
                if not prev_winner_id:
                    logger.error(f"No previous winner found for player {player_id} round {tournament.current_round}")
                    return
                    
                prev_winner = None
                for word in tournament.remaining_words:
                    if str(word['id']) == str(prev_winner_id):
                        prev_winner = word
                        break
                        
                if not prev_winner:
                    logger.error(f"Previous winner {prev_winner_id} not found in remaining words")
                    return
                    
                # Pick random opponent (not the previous winner)
                opponents = [w for w in tournament.remaining_words if w['id'] != prev_winner['id']]
                if not opponents:
                    logger.error(f"No opponents available for player {player_id}")
                    return
                    
                opponent = random.choice(opponents)
                battle_words = [prev_winner, opponent]
                random.shuffle(battle_words)  # Randomize display order
            
            tournament.battles[tournament.current_round] = {
                'noun1': battle_words[0],
                'noun2': battle_words[1]
            }
            
            logger.info(f"Player {player_id} round {tournament.current_round}: {battle_words[0]['name']} vs {battle_words[1]['name']}")
        
        battle = tournament.battles[tournament.current_round]
        
        self.send_message({
            'action': 'battle_data',
            'round': tournament.current_round,
            'battle': {
                'round': tournament.current_round,
                'noun1': battle['noun1'],
                'noun2': battle['noun2']
            }
        })
        
    def handle_select_noun(self, data):
        room_id = str(data.get('roomId'))
        player_id = str(data.get('playerId'))
        round_num = data.get('round')
        noun_id = str(data.get('nounId'))
        
        if room_id not in ROOMS:
            return
            
        room = ROOMS[room_id]
        room.update_activity()
        
        if player_id not in room.player_tournaments:
            return
            
        tournament = room.player_tournaments[player_id]
        
        # Record player's choice
        tournament.choices[round_num] = noun_id
        
        # Find the selected and eliminated words
        battle = tournament.battles[round_num]
        if str(battle['noun1']['id']) == noun_id:
            winner = battle['noun1']
            loser = battle['noun2']
        else:
            winner = battle['noun2']
            loser = battle['noun1']
            
        # Update player's remaining words
        tournament.remaining_words = [w for w in tournament.remaining_words if str(w['id']) != str(loser['id'])]
        tournament.eliminated_words.append(loser)
        
        logger.info(f"Player {player_id} round {round_num}: chose {winner['name']}, eliminated {loser['name']}")
        logger.info(f"Player {player_id} remaining words: {[w['name'] for w in tournament.remaining_words]}")
        
        # Notify other players that this player has selected
        for p_id in room.players:
            if p_id != player_id and p_id in PLAYERS:
                other = PLAYERS[p_id]
                if other.connection:
                    other.connection.send_message({
                        'action': 'opponent_selected'
                    })
        
        # If test mode and AI hasn't selected yet, make AI select
        if room.test_mode and room.ai_player_id:
            # First ensure AI has a battle for this round
            ai_tournament = room.player_tournaments.get(room.ai_player_id)
            if ai_tournament and ai_tournament.current_round not in ai_tournament.battles:
                # Create battle for AI (same logic as handle_get_battle)
                if ai_tournament.current_round == 1:
                    # First round: random 2 words
                    battle_words = random.sample(ai_tournament.remaining_words, 2)
                else:
                    # Later rounds: previous winner vs random opponent
                    prev_winner_id = ai_tournament.choices.get(ai_tournament.current_round - 1)
                    if prev_winner_id:
                        prev_winner = None
                        for word in ai_tournament.remaining_words:
                            if str(word['id']) == str(prev_winner_id):
                                prev_winner = word
                                break
                        if prev_winner:
                            opponents = [w for w in ai_tournament.remaining_words if w['id'] != prev_winner['id']]
                            if opponents:
                                opponent = random.choice(opponents)
                                battle_words = [prev_winner, opponent]
                                random.shuffle(battle_words)
                            else:
                                battle_words = None
                        else:
                            battle_words = None
                    else:
                        battle_words = None
                
                if battle_words:
                    ai_tournament.battles[ai_tournament.current_round] = {
                        'noun1': battle_words[0],
                        'noun2': battle_words[1]
                    }
                    logger.info(f"AI {room.ai_player_id} round {ai_tournament.current_round}: {battle_words[0]['name']} vs {battle_words[1]['name']}")
            
            # Now make AI selection
            self.make_ai_selection(room)
        
        # Check if both players have made choices for their current rounds
        all_chosen = True
        for p_id in room.players:
            if p_id in room.player_tournaments:
                p_tournament = room.player_tournaments[p_id]
                # Check if this player has chosen for their current round
                if p_tournament.current_round not in p_tournament.choices:
                    all_chosen = False
                    break
        
        if all_chosen:
            logger.info(f"All players have completed their current rounds")
            
            # Send battle results to all players
            for p_id in room.players:
                p = PLAYERS.get(p_id)
                if p and p.connection:
                    p_tournament = room.player_tournaments[p_id]
                    # Get this player's current round battle
                    current_round = p_tournament.current_round
                    p_battle = p_tournament.battles[current_round]
                    
                    # Find this player's winner and loser
                    chosen_id = p_tournament.choices[current_round]
                    if str(p_battle['noun1']['id']) == str(chosen_id):
                        p_winner = p_battle['noun1']
                        p_loser = p_battle['noun2']
                    else:
                        p_winner = p_battle['noun2']
                        p_loser = p_battle['noun1']
                    
                    # Move to next round for this player
                    if len(p_tournament.remaining_words) > 1 and current_round < 9:
                        p_tournament.current_round += 1
                        has_next = True
                    else:
                        has_next = False
                    
                    p.connection.send_message({
                        'action': 'battle_result',
                        'round': current_round,
                        'winnerNoun': p_winner,
                        'loserNoun': p_loser,
                        'hasNext': has_next
                    })
                    
                    logger.info(f"Player {p_id} completed round {current_round}, advancing to {p_tournament.current_round}")
            
            # After all players get their results, check if the game should end (PVP mode)
            all_finished = True
            for p_id in room.players:
                if p_id in room.player_tournaments:
                    p_tournament = room.player_tournaments[p_id]
                    if len(p_tournament.remaining_words) > 1:
                        all_finished = False
                        break
                    elif len(p_tournament.remaining_words) == 1 and not p_tournament.champion:
                        p_tournament.champion = p_tournament.remaining_words[0]
                        room.player_champions[p_id] = p_tournament.champion
                        logger.info(f"Player {p_id} champion: {p_tournament.champion['name']}")
            
            if all_finished:
                logger.info(f"All players finished their tournaments in room {room.id} (PVP mode)")
                # Send game_ended to all real players
                for p_id in room.players:
                    p = PLAYERS.get(p_id)
                    if p and p.connection:
                        p.connection.send_message({
                            'action': 'game_ended'
                        })
            
    def handle_get_result(self, data):
        room_id = str(data.get('roomId'))
        player_id = str(data.get('playerId'))
        
        logger.info(f"handle_get_result: room={room_id}, player={player_id}")
        
        if room_id not in ROOMS:
            logger.warning(f"Room {room_id} not found")
            self.send_message({
                'action': 'error',
                'message': 'Room not found',
                'code': 404
            })
            return
            
        room = ROOMS[room_id]
        room.update_activity()
        
        if player_id not in room.player_tournaments:
            logger.warning(f"Player {player_id} not in tournaments")
            self.send_message({
                'action': 'error',
                'message': 'Player tournament not found',
                'code': 404
            })
            return
            
        tournament = room.player_tournaments[player_id]
        
        # Get this player's champion
        if not tournament.champion and tournament.remaining_words:
            tournament.champion = tournament.remaining_words[0]
            room.player_champions[player_id] = tournament.champion
            logger.info(f"Player {player_id} champion set: {tournament.champion}")
        
        # Get opponent's champion
        opponent_champion = None
        opponent_id = None
        for p_id in room.players:
            if p_id != player_id:
                opponent_id = p_id
                if p_id in room.player_champions:
                    opponent_champion = room.player_champions[p_id]
                elif p_id in room.player_tournaments:
                    opp_tournament = room.player_tournaments[p_id]
                    if opp_tournament.champion:
                        opponent_champion = opp_tournament.champion
                    elif opp_tournament.remaining_words:
                        opponent_champion = opp_tournament.remaining_words[0]
                        room.player_champions[p_id] = opponent_champion
                break
        
        # Log champions for debugging
        logger.info(f"Player {player_id} champion: {tournament.champion}")
        logger.info(f"Opponent {opponent_id} champion: {opponent_champion}")
        
        # Calculate tacit value with details - MATRIX CORRELATION ONLY, NO FALLBACKS
        try:
            tacit_value, calculation_details = self.calculate_tacit_value_with_details(room)
            logger.info(f"Tacit value calculated: {tacit_value}, method: {calculation_details.get('method', 'unknown')}")
        except Exception as e:
            logger.error(f"Matrix correlation calculation failed: {e}")
            logger.error(f"NO FALLBACK - numpy/scipy is REQUIRED")
            tacit_value = 0
            calculation_details = {
                'error': str(e),
                'method': 'Matrix Correlation Failed - numpy/scipy Required', 
                'calculation': 'Error: numpy/scipy必须安装'
            }
        
        result_data = {
            'action': 'game_result',
            'myChampion': tournament.champion,
            'opponentChampion': opponent_champion,
            'champion': tournament.champion,  # Keep for backward compatibility
            'tacitValue': round(tacit_value, 1),
            'eliminatedNouns': tournament.eliminated_words,
            'calculationDetails': calculation_details
        }
        
        logger.info(f"Sending result to {player_id}: {result_data.get('action')}, champions: {bool(result_data.get('myChampion'))}, {bool(result_data.get('opponentChampion'))}")
        
        self.send_message(result_data)
        
    def calculate_tacit_value(self, room):
        import numpy as np
        from scipy.stats import pearsonr
        
        if len(room.players) < 2:
            return 0
            
        player_ids = list(room.players)
        if len(player_ids) < 2:
            return 0
            
        t1 = room.player_tournaments.get(player_ids[0])
        t2 = room.player_tournaments.get(player_ids[1])
        
        if not t1 or not t2:
            return 0
            
        # Build preference matrices for both players
        word_ids = [w['id'] for w in room.word_pool]
        n = len(word_ids)
        
        # Create index mapping
        id_to_idx = {word_id: idx for idx, word_id in enumerate(word_ids)}
        
        # Initialize matrices (0 = no competition, 1 = column wins, 2 = row wins)
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
                    # id1 wins over id2
                    matrix1[idx2][idx1] = 1  # column (id1) wins
                    matrix1[idx1][idx2] = 2  # row (id1) wins
                else:
                    # id2 wins over id1
                    matrix1[idx1][idx2] = 1  # column (id2) wins
                    matrix1[idx2][idx1] = 2  # row (id2) wins
                    
        # Fill matrix for player 2
        for round_num, battle in t2.battles.items():
            if round_num in t2.choices:
                id1 = battle['noun1']['id']
                id2 = battle['noun2']['id']
                winner_id = t2.choices[round_num]
                
                idx1 = id_to_idx[id1]
                idx2 = id_to_idx[id2]
                
                if str(winner_id) == str(id1):
                    # id1 wins over id2
                    matrix2[idx2][idx1] = 1  # column (id1) wins
                    matrix2[idx1][idx2] = 2  # row (id1) wins
                else:
                    # id2 wins over id1
                    matrix2[idx1][idx2] = 1  # column (id2) wins
                    matrix2[idx2][idx1] = 2  # row (id2) wins
        
        # Calculate correlation between flattened matrices
        flat1 = matrix1.flatten()
        flat2 = matrix2.flatten()
        
        # Only calculate correlation on non-zero positions (where battles occurred)
        # This gives a better measure of actual preference similarity
        mask = (flat1 != 0) | (flat2 != 0)
        
        if np.sum(mask) < 2:
            return 0
            
        try:
            # Calculate Pearson correlation
            correlation, _ = pearsonr(flat1[mask], flat2[mask])
            
            # Convert correlation (-1 to 1) to percentage (0 to 100)
            # correlation of 1 = 100% tacit value
            # correlation of 0 = 50% tacit value  
            # correlation of -1 = 0% tacit value
            tacit_value = (correlation + 1) * 50
            
            # Ensure value is between 0 and 100
            tacit_value = max(0, min(100, tacit_value))
            
            logger.info(f"Matrix correlation: {correlation:.3f}, Tacit value: {tacit_value:.1f}%")
            
            return tacit_value
            
        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            # Fallback to simple matching
            matches = 0
            total = 0
            for round_num in range(1, 10):
                if round_num in t1.choices and round_num in t2.choices:
                    total += 1
                    if t1.choices[round_num] == t2.choices[round_num]:
                        matches += 1
            return (matches / max(total, 1)) * 100
    
    def calculate_tacit_value_with_details(self, room):
        """Calculate tacit value using ONLY matrix correlation with numpy/scipy - NO FALLBACKS"""
        
        if len(room.players) < 2:
            raise ValueError("Need at least 2 players for tacit value calculation")
            
        player_ids = list(room.players)
        if len(player_ids) < 2:
            raise ValueError("Need at least 2 players for tacit value calculation")
            
        t1 = room.player_tournaments.get(player_ids[0])
        t2 = room.player_tournaments.get(player_ids[1])
        
        if not t1 or not t2:
            raise ValueError("Tournament data not found for players")
        
        # Matrix correlation with numpy/scipy - REQUIRED, NO FALLBACK
        import numpy as np
        from scipy.stats import pearsonr
        logger.info("Using numpy/scipy for matrix correlation - NO FALLBACK")
        
        # Build preference matrices for both players
        word_ids = [w['id'] for w in room.word_pool]
        n = len(word_ids)
        
        # Create index mapping
        id_to_idx = {word_id: idx for idx, word_id in enumerate(word_ids)}
        word_names = {w['id']: w['name'] for w in room.word_pool}
        
        # Initialize matrices (0 = no competition, 1 = column wins, 2 = row wins)
        matrix1 = np.zeros((n, n))
        matrix2 = np.zeros((n, n))
        
        # Collect choice details for transparency
        choice_details = []
        
        # Fill matrix for player 1
        for round_num, battle in t1.battles.items():
            if round_num in t1.choices:
                id1 = battle['noun1']['id']
                id2 = battle['noun2']['id']
                winner_id = t1.choices[round_num]
                
                idx1 = id_to_idx[id1]
                idx2 = id_to_idx[id2]
                
                choice_detail = {
                    'round': round_num,
                    'player1_battle': f"{word_names[id1]} vs {word_names[id2]}",
                    'player1_choice': word_names[int(winner_id)]
                }
                
                if str(winner_id) == str(id1):
                    # id1 wins over id2
                    matrix1[idx2][idx1] = 1  # column (id1) wins
                    matrix1[idx1][idx2] = 2  # row (id1) wins
                else:
                    # id2 wins over id1
                    matrix1[idx1][idx2] = 1  # column (id2) wins
                    matrix1[idx2][idx1] = 2  # row (id2) wins
                
                # Add player 2 data if available
                if round_num in t2.battles and round_num in t2.choices:
                    battle2 = t2.battles[round_num]
                    id2_1 = battle2['noun1']['id']
                    id2_2 = battle2['noun2']['id']
                    winner2_id = t2.choices[round_num]
                    
                    choice_detail['player2_battle'] = f"{word_names[id2_1]} vs {word_names[id2_2]}"
                    choice_detail['player2_choice'] = word_names[int(winner2_id)]
                    
                choice_details.append(choice_detail)
        
        # Fill matrix for player 2
        for round_num, battle in t2.battles.items():
            if round_num in t2.choices:
                id1 = battle['noun1']['id']
                id2 = battle['noun2']['id']
                winner_id = t2.choices[round_num]
                
                idx1 = id_to_idx[id1]
                idx2 = id_to_idx[id2]
                
                if str(winner_id) == str(id1):
                    # id1 wins over id2
                    matrix2[idx2][idx1] = 1  # column (id1) wins
                    matrix2[idx1][idx2] = 2  # row (id1) wins
                else:
                    # id2 wins over id1
                    matrix2[idx1][idx2] = 1  # column (id2) wins
                    matrix2[idx2][idx1] = 2  # row (id2) wins
        
        # Calculate correlation between flattened matrices
        flat1 = matrix1.flatten()
        flat2 = matrix2.flatten()
        
        # Only calculate correlation on non-zero positions (where battles occurred)
        mask = (flat1 != 0) | (flat2 != 0)
        
        if np.sum(mask) < 2:
            raise ValueError("Insufficient data points for correlation calculation")
        
        # Calculate Pearson correlation
        correlation, p_value = pearsonr(flat1[mask], flat2[mask])
        
        # Convert correlation (-1 to 1) to percentage (0 to 100)
        # correlation of 1 = 100% tacit value
        # correlation of 0 = 50% tacit value  
        # correlation of -1 = 0% tacit value
        tacit_value = (correlation + 1) * 50
        
        # Ensure value is between 0 and 100
        tacit_value = max(0, min(100, tacit_value))
        
        logger.info(f"Matrix correlation: {correlation:.3f}, Tacit value: {tacit_value:.1f}%")
        
        calculation_details = {
            'method': 'Matrix Correlation (Pearson)',
            'correlation': round(correlation, 3),
            'p_value': round(p_value, 4) if p_value else None,
            'formula': f"默契度 = (相关系数 + 1) × 50",
            'calculation': f"({correlation:.3f} + 1) × 50 = {tacit_value:.1f}%",
            'matrix_size': f"{n}×{n}",
            'data_points': int(np.sum(mask)),
            'choices': choice_details,
            'explanation': "使用皮尔逊相关系数分析两位玩家的选择偏好矩阵，相关系数越高表示选择模式越相似"
        }
        
        return tacit_value, calculation_details
        
    def handle_play_again(self, data):
        room_id = str(data.get('roomId'))
        
        if room_id not in ROOMS:
            return
            
        room = ROOMS[room_id]
        room.update_activity()
        
        # Reset game
        room.game_started = False
        # Each player tracks their own round
        room.word_pool = []
        room.player_tournaments = {}
        room.player_champions = {}
                
    def make_ai_selection(self, room):
        """Make automatic selection for AI player"""
        ai_id = room.ai_player_id
        if ai_id not in room.player_tournaments:
            return
            
        ai_tournament = room.player_tournaments[ai_id]
        current_round = ai_tournament.current_round
        
        # Check if AI already selected for this round
        if current_round in ai_tournament.choices:
            return
            
        # Get current battle
        if current_round not in ai_tournament.battles:
            return
            
        battle = ai_tournament.battles[current_round]
        
        # AI makes a random choice with a slight delay
        import tornado.ioloop
        
        def ai_select():
            # Random selection between the two nouns
            chosen_noun = random.choice([battle['noun1'], battle['noun2']])
            chosen_id = str(chosen_noun['id'])
            
            # Record AI's choice
            ai_tournament.choices[current_round] = chosen_id
            
            # Find winner and loser
            if str(battle['noun1']['id']) == chosen_id:
                winner = battle['noun1']
                loser = battle['noun2']
            else:
                winner = battle['noun2']
                loser = battle['noun1']
            
            # Update AI's remaining words
            ai_tournament.remaining_words = [w for w in ai_tournament.remaining_words if str(w['id']) != str(loser['id'])]
            ai_tournament.eliminated_words.append(loser)
            
            logger.info(f"AI {ai_id} round {current_round}: chose {winner['name']}, eliminated {loser['name']}")
            logger.info(f"AI {ai_id} remaining words: {[w['name'] for w in ai_tournament.remaining_words]}")
            
            # Trigger battle result check
            self.check_and_send_battle_results(room)
        
        # AI selects after 1 second delay (simulates thinking)
        tornado.ioloop.IOLoop.current().call_later(1.0, ai_select)
    
    def check_and_send_battle_results(self, room):
        """Check if all players have selected and send results"""
        # Check if both players have made choices for their current rounds
        all_chosen = True
        for p_id in room.players:
            if p_id in room.player_tournaments:
                p_tournament = room.player_tournaments[p_id]
                if p_tournament.current_round not in p_tournament.choices:
                    all_chosen = False
                    break
        
        if all_chosen:
            logger.info(f"All players have completed their current rounds")
            
            # Process battle results for all players (including AI)
            for p_id in room.players:
                p_tournament = room.player_tournaments[p_id]
                current_round = p_tournament.current_round
                p_battle = p_tournament.battles[current_round]
                
                # Find this player's winner and loser
                chosen_id = p_tournament.choices[current_round]
                if str(p_battle['noun1']['id']) == str(chosen_id):
                    p_winner = p_battle['noun1']
                    p_loser = p_battle['noun2']
                else:
                    p_winner = p_battle['noun2']
                    p_loser = p_battle['noun1']
                
                # Move to next round for this player
                if len(p_tournament.remaining_words) > 1 and current_round < 9:
                    p_tournament.current_round += 1
                    has_next = True
                else:
                    has_next = False
                
                logger.info(f"Player {p_id} completed round {current_round}, advancing to {p_tournament.current_round}")
                
                # Send message only to real players with connections
                p = PLAYERS.get(p_id)
                if p and p.connection:
                    p.connection.send_message({
                        'action': 'battle_result',
                        'round': current_round,
                        'winnerNoun': p_winner,
                        'loserNoun': p_loser,
                        'hasNext': has_next
                    })
                
                # If this is AI and it has next round, trigger AI to continue
                if p_id.startswith('AI_') and has_next:
                    # Create battle for AI's next round if not exists
                    next_round = p_tournament.current_round
                    if next_round not in p_tournament.battles:
                        if len(p_tournament.remaining_words) >= 2:
                            battle_words = random.sample(p_tournament.remaining_words, 2)
                            p_tournament.battles[next_round] = {
                                'round': next_round,
                                'noun1': battle_words[0],
                                'noun2': battle_words[1]
                            }
                            logger.info(f"Created battle for AI {p_id} round {next_round}: {battle_words[0]['name']} vs {battle_words[1]['name']}")
                    
                    # Trigger AI selection for next round with a delay
                    import tornado.ioloop
                    tornado.ioloop.IOLoop.current().call_later(1.5, lambda: self.trigger_ai_selection(room, p_id))
            
            # After all players get their results, check if the game should end
            all_finished = True
            for p_id in room.players:
                if p_id in room.player_tournaments:
                    p_tournament = room.player_tournaments[p_id]
                    if len(p_tournament.remaining_words) > 1:
                        all_finished = False
                        break
                    elif len(p_tournament.remaining_words) == 1 and not p_tournament.champion:
                        p_tournament.champion = p_tournament.remaining_words[0]
                        room.player_champions[p_id] = p_tournament.champion
                        logger.info(f"Player {p_id} champion: {p_tournament.champion['name']}")
            
            if all_finished:
                logger.info(f"All players finished their tournaments in room {room.id}")
                # Send game_ended to all real players
                for p_id in room.players:
                    p = PLAYERS.get(p_id)
                    if p and p.connection:
                        p.connection.send_message({
                            'action': 'game_ended'
                        })
    
    def send_message(self, data):
        try:
            message = json.dumps(data, ensure_ascii=False)
            self.write_message(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            
    def send_error(self, error):
        self.send_message({
            'action': 'error',
            'message': error
        })
        
    def on_close(self):
        logger.info("WebSocket connection closed")
        
        if self in CONNECTIONS:
            player = CONNECTIONS[self]
            logger.info(f"Player {player.nickname} (ID: {player.id}) disconnected")
            
            # Notify other players in the room about disconnect
            if player.room_id and player.room_id in ROOMS:
                room = ROOMS[player.room_id]
                for p_id in room.players:
                    if p_id != player.id and p_id in PLAYERS:
                        other = PLAYERS[p_id]
                        if other.connection and other.connection != self:
                            other.connection.send_message({
                                'action': 'player_disconnected',
                                'playerId': player.id
                            })
            
            # Don't remove player from room or PLAYERS - keep for reconnection
            # Just clear the connection
            player.connection = None
            del CONNECTIONS[self]
        
        logger.info(f"Active rooms: {list(ROOMS.keys())}, Active players: {len(PLAYERS)}")

class HealthHandler(tornado.web.RequestHandler):
    def get(self):
        uptime = time.time()
        mem_usage = os.popen('ps -p %d -o rss=' % os.getpid()).read().strip()
        
        self.write({
            "status": "ok",
            "uptimeSeconds": int(uptime),
            "rooms": len(ROOMS),
            "players": len(PLAYERS),
            "connections": len(CONNECTIONS),
            "memoryKB": int(mem_usage) if mem_usage else 0
        })
        
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        info = {
            "status": "running",
            "rooms": list(ROOMS.keys()),
            "active_rooms": len(ROOMS),
            "active_players": len(PLAYERS),
            "active_connections": len(CONNECTIONS),
            "room_details": [room.to_dict() for room in ROOMS.values()]
        }
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(info, ensure_ascii=False, indent=2))

def cleanup_expired_rooms():
    """Periodic task to clean up expired rooms"""
    expired_rooms = []
    for room_id, room in ROOMS.items():
        if room.is_expired() and not room.players:
            expired_rooms.append(room_id)
            
    for room_id in expired_rooms:
        del ROOMS[room_id]
        logger.info(f"Cleaned up expired room: {room_id}")
        
    tornado.ioloop.IOLoop.current().call_later(60, cleanup_expired_rooms)

def make_app():
    """Create Tornado application"""
    return tornado.web.Application([
        (r"/", IndexHandler),
        (r"/healthz", HealthHandler),
        (r"/ws", WebSocketHandler),
    ])

if __name__ == "__main__":
    if not WORD_BANK.get('categories'):
        logger.warning("Word bank is empty. Server might not function correctly.")
        
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    
    # SSL certificate configuration
    CERTFILE = "aiconnector.cn_bundle.pem" 
    KEYFILE = "aiconnector.cn.key"
    
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
    port = 3000
    
    if ssl_ctx:
        app.listen(port, ssl_options=ssl_ctx)
        logger.info(f"Server started on wss://www.aiconnector.cn:{port}/ws")
    else:
        app.listen(port)
        logger.info(f"Server started on ws://localhost:{port}/ws (NO SSL)")
        
    # Start periodic cleanup task
    tornado.ioloop.IOLoop.current().call_later(60, cleanup_expired_rooms)
    
    tornado.ioloop.IOLoop.current().start()