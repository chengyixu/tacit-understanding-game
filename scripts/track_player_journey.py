#!/usr/bin/env python3
"""
Track a complete player journey through the game
Shows: registration, room entry, questions faced, choices made, game completion, and exit
"""

import paramiko
import sys
import re
from datetime import datetime

# Server configuration
SERVER_CONFIG = {
    'hostname': '47.117.176.214',
    'username': 'root',
    'password': '0212Connect!',
    'port': 22,
    'log_path': '/moqiyouxi_backend/server.log'
}

# ANSI color codes
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def track_player_journey(player_identifier):
    """Track complete journey of a player through the game"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=SERVER_CONFIG['hostname'],
        username=SERVER_CONFIG['username'],
        password=SERVER_CONFIG['password'],
        port=SERVER_CONFIG['port']
    )
    
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Tracking Player Journey: {player_identifier}{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    # Search for all logs related to this player
    cmd = f"grep -E '{player_identifier}' {SERVER_CONFIG['log_path']}"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    logs = stdout.read().decode('utf-8').split('\n')
    
    if not logs or logs == ['']:
        print(f"{Colors.RED}No logs found for player: {player_identifier}{Colors.RESET}")
        ssh.close()
        return
    
    # Parse and categorize events
    journey = {
        'registration': None,
        'nickname_update': None,
        'room_created': None,
        'room_joined': None,
        'game_started': None,
        'battles': [],
        'choices': [],
        'game_completed': None,
        'disconnected': None
    }
    
    for log in logs:
        if not log:
            continue
            
        # Extract timestamp
        timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log)
        timestamp = timestamp_match.group(1) if timestamp_match else 'Unknown'
        
        # Player registration
        if 'Player registered' in log:
            nickname_match = re.search(r'Player registered: .* \((.*?)\)', log)
            nickname = nickname_match.group(1) if nickname_match else 'Unknown'
            journey['registration'] = {
                'time': timestamp,
                'nickname': nickname,
                'log': log
            }
        
        # Nickname update
        elif 'updated nickname to' in log:
            nickname_match = re.search(r'updated nickname to: (.*)', log)
            nickname = nickname_match.group(1) if nickname_match else 'Unknown'
            journey['nickname_update'] = {
                'time': timestamp,
                'new_nickname': nickname,
                'log': log
            }
        
        # Room creation
        elif 'created by player' in log and player_identifier in log:
            room_match = re.search(r'Room (\d+) created', log)
            room_id = room_match.group(1) if room_match else 'Unknown'
            journey['room_created'] = {
                'time': timestamp,
                'room_id': room_id,
                'log': log
            }
        
        # Room joining
        elif 'joined room' in log:
            room_match = re.search(r'joined room (\d+)', log)
            room_id = room_match.group(1) if room_match else 'Unknown'
            journey['room_joined'] = {
                'time': timestamp,
                'room_id': room_id,
                'log': log
            }
        
        # Game started
        elif 'Game started' in log:
            journey['game_started'] = {
                'time': timestamp,
                'log': log
            }
        
        # Battle generation (questions faced)
        elif 'Generated battle for player' in log and player_identifier in log:
            # Extract round and nouns
            round_match = re.search(r'round (\d+)', log)
            champion_match = re.search(r'champion=([^(]+)', log)
            challenger_match = re.search(r'challenger=([^(]+)', log)
            
            battle = {
                'time': timestamp,
                'round': round_match.group(1) if round_match else 'Unknown',
                'champion': champion_match.group(1).strip() if champion_match else 'Unknown',
                'challenger': challenger_match.group(1).strip() if challenger_match else 'Unknown',
                'log': log
            }
            journey['battles'].append(battle)
        
        # Player choices
        elif 'submitted choice' in log or 'choice for round' in log:
            round_match = re.search(r'round (\d+)', log)
            choice_match = re.search(r'chose: ([^,]+)', log) or re.search(r'choice: ([^,]+)', log)
            
            choice = {
                'time': timestamp,
                'round': round_match.group(1) if round_match else 'Unknown',
                'selected': choice_match.group(1).strip() if choice_match else 'Unknown',
                'log': log
            }
            journey['choices'].append(choice)
        
        # Game completion
        elif 'Game complete' in log:
            tacit_match = re.search(r'tacit value: (\d+)', log)
            journey['game_completed'] = {
                'time': timestamp,
                'tacit_value': tacit_match.group(1) if tacit_match else 'Unknown',
                'log': log
            }
        
        # Disconnection
        elif 'WebSocket connection closed' in log or 'Player.*left room' in log:
            journey['disconnected'] = {
                'time': timestamp,
                'log': log
            }
    
    # Display the journey in chronological order
    if journey['registration']:
        print(f"{Colors.GREEN}📝 REGISTRATION{Colors.RESET}")
        print(f"   Time: {journey['registration']['time']}")
        print(f"   Initial nickname: {journey['registration']['nickname']}\n")
    
    if journey['nickname_update']:
        print(f"{Colors.YELLOW}✏️  NICKNAME UPDATE{Colors.RESET}")
        print(f"   Time: {journey['nickname_update']['time']}")
        print(f"   New nickname: {journey['nickname_update']['new_nickname']}\n")
    
    if journey['room_created']:
        print(f"{Colors.MAGENTA}🏠 ROOM CREATED{Colors.RESET}")
        print(f"   Time: {journey['room_created']['time']}")
        print(f"   Room ID: {journey['room_created']['room_id']}\n")
    elif journey['room_joined']:
        print(f"{Colors.MAGENTA}🚪 ROOM JOINED{Colors.RESET}")
        print(f"   Time: {journey['room_joined']['time']}")
        print(f"   Room ID: {journey['room_joined']['room_id']}\n")
    
    if journey['game_started']:
        print(f"{Colors.BLUE}🎮 GAME STARTED{Colors.RESET}")
        print(f"   Time: {journey['game_started']['time']}\n")
    
    if journey['battles']:
        print(f"{Colors.CYAN}⚔️  BATTLES FACED (Questions){Colors.RESET}")
        for battle in sorted(journey['battles'], key=lambda x: int(x['round']) if x['round'] != 'Unknown' else 0):
            print(f"   Round {battle['round']}: {Colors.BOLD}{battle['champion']}{Colors.RESET} vs {Colors.BOLD}{battle['challenger']}{Colors.RESET}")
    
    if journey['choices']:
        print(f"\n{Colors.CYAN}✅ PLAYER CHOICES{Colors.RESET}")
        for choice in sorted(journey['choices'], key=lambda x: int(x['round']) if x['round'] != 'Unknown' else 0):
            print(f"   Round {choice['round']}: Selected {Colors.BOLD}{choice['selected']}{Colors.RESET}")
    
    if journey['game_completed']:
        print(f"\n{Colors.GREEN}🏆 GAME COMPLETED{Colors.RESET}")
        print(f"   Time: {journey['game_completed']['time']}")
        print(f"   Tacit Value: {journey['game_completed']['tacit_value']}%\n")
    
    if journey['disconnected']:
        print(f"{Colors.RED}👋 DISCONNECTED{Colors.RESET}")
        print(f"   Time: {journey['disconnected']['time']}\n")
    
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    ssh.close()

def track_room_activity(room_id):
    """Track all activity in a specific room"""
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=SERVER_CONFIG['hostname'],
        username=SERVER_CONFIG['username'],
        password=SERVER_CONFIG['password'],
        port=SERVER_CONFIG['port']
    )
    
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}Room {room_id} Activity Log{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*70}{Colors.RESET}\n")
    
    # Get all logs for this room
    cmd = f"grep 'Room {room_id}' {SERVER_CONFIG['log_path']}"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    logs = stdout.read().decode('utf-8').split('\n')
    
    for log in logs:
        if not log:
            continue
        
        # Color code different events
        if 'created' in log:
            print(f"{Colors.MAGENTA}🏠 {log}{Colors.RESET}")
        elif 'joined' in log:
            print(f"{Colors.CYAN}👤 {log}{Colors.RESET}")
        elif 'Game started' in log:
            print(f"{Colors.BLUE}🎮 {log}{Colors.RESET}")
        elif 'Round' in log and 'complete' in log:
            print(f"{Colors.YELLOW}⏭️  {log}{Colors.RESET}")
        elif 'Game complete' in log:
            print(f"{Colors.GREEN}🏆 {log}{Colors.RESET}")
        elif 'left room' in log:
            print(f"{Colors.RED}👋 {log}{Colors.RESET}")
        else:
            print(f"   {log}")
    
    ssh.close()

def main():
    print(f"{Colors.BOLD}Player Journey Tracker{Colors.RESET}\n")
    print("Options:")
    print("1. Track player by ID or nickname")
    print("2. Track room activity")
    print("3. Exit\n")
    
    choice = input("Choose option (1-3): ")
    
    if choice == '1':
        player = input("Enter player ID or nickname: ")
        track_player_journey(player)
    elif choice == '2':
        room = input("Enter room ID: ")
        track_room_activity(room)
    elif choice == '3':
        sys.exit(0)
    else:
        print(f"{Colors.RED}Invalid choice{Colors.RESET}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line usage
        track_player_journey(sys.argv[1])
    else:
        # Interactive mode
        main()