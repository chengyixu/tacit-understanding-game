#!/usr/bin/env python3
"""
Real-time game dashboard for monitoring current game sessions
Shows active rooms, players, and recent events
"""

import paramiko
import time
import sys
import re
from datetime import datetime, timedelta
from collections import defaultdict

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
    CLEAR_SCREEN = '\033[2J\033[H'

class GameDashboard:
    def __init__(self):
        self.ssh = None
        self.active_rooms = {}
        self.recent_events = []
        self.player_count = 0
        self.connect()
    
    def connect(self):
        """Establish SSH connection"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                hostname=SERVER_CONFIG['hostname'],
                username=SERVER_CONFIG['username'],
                password=SERVER_CONFIG['password'],
                port=SERVER_CONFIG['port']
            )
        except Exception as e:
            print(f"{Colors.RED}Connection failed: {e}{Colors.RESET}")
            sys.exit(1)
    
    def parse_recent_logs(self, minutes=10):
        """Parse recent logs to build current state"""
        try:
            # Get recent logs (last N lines should cover last few minutes)
            cmd = f"tail -n 500 {SERVER_CONFIG['log_path']}"
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            logs = stdout.read().decode('utf-8').split('\n')
            
            self.active_rooms = {}
            self.recent_events = []
            players_seen = set()
            
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            for log in logs:
                if not log:
                    continue
                
                # Extract timestamp
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', log)
                if not timestamp_match:
                    continue
                
                timestamp_str = timestamp_match.group(1)
                try:
                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    continue
                
                # Only process recent logs
                if log_time < cutoff_time:
                    continue
                
                # Track recent events
                if len(self.recent_events) < 10:
                    self.recent_events.append({
                        'time': timestamp_str,
                        'message': log.split(' - ', 2)[-1] if ' - ' in log else log
                    })
                
                # Parse room creation
                room_match = re.search(r'Room (\d+) created', log)
                if room_match:
                    room_id = room_match.group(1)
                    self.active_rooms[room_id] = {
                        'status': 'waiting',
                        'players': [],
                        'created': timestamp_str,
                        'started': None,
                        'current_round': 0,
                        'completed': False
                    }
                
                # Parse player joining
                join_match = re.search(r'Player (\S+).*joined room (\d+)', log)
                if join_match:
                    player_id = join_match.group(1)
                    room_id = join_match.group(2)
                    if room_id in self.active_rooms:
                        nickname_match = re.search(r'\((.*?)\)', log)
                        nickname = nickname_match.group(1) if nickname_match else player_id[:8]
                        if nickname not in self.active_rooms[room_id]['players']:
                            self.active_rooms[room_id]['players'].append(nickname)
                        players_seen.add(player_id)
                
                # Parse game start
                start_match = re.search(r'Game started in room (\d+)', log)
                if start_match:
                    room_id = start_match.group(1)
                    if room_id in self.active_rooms:
                        self.active_rooms[room_id]['status'] = 'playing'
                        self.active_rooms[room_id]['started'] = timestamp_str
                
                # Parse round completion
                round_match = re.search(r'Room (\d+).*Round (\d+) complete', log)
                if round_match:
                    room_id = round_match.group(1)
                    round_num = int(round_match.group(2))
                    if room_id in self.active_rooms:
                        self.active_rooms[room_id]['current_round'] = round_num
                
                # Parse game completion
                complete_match = re.search(r'Game complete in room (\d+)', log)
                if complete_match:
                    room_id = complete_match.group(1)
                    if room_id in self.active_rooms:
                        self.active_rooms[room_id]['status'] = 'completed'
                        self.active_rooms[room_id]['completed'] = True
            
            self.player_count = len(players_seen)
            self.recent_events.reverse()  # Show newest first
            
        except Exception as e:
            print(f"{Colors.RED}Error parsing logs: {e}{Colors.RESET}")
    
    def render_dashboard(self):
        """Render the dashboard"""
        print(Colors.CLEAR_SCREEN)
        
        # Header
        print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.BOLD}? Ä¬ÆõÐ¡ÓÎÏ· - Live Game Dashboard{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*80}{Colors.RESET}")
        print(f"{Colors.WHITE}Server: {SERVER_CONFIG['hostname']} | Updated: {datetime.now().strftime('%H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*80}{Colors.RESET}\n")
        
        # Server stats
        print(f"{Colors.YELLOW}? Quick Stats (Last 10 min){Colors.RESET}")
        print(f"   Active Rooms: {Colors.BOLD}{len([r for r in self.active_rooms.values() if not r['completed']])}{Colors.RESET}")
        print(f"   Total Players: {Colors.BOLD}{self.player_count}{Colors.RESET}")
        print(f"   Completed Games: {Colors.BOLD}{len([r for r in self.active_rooms.values() if r['completed']])}{Colors.RESET}\n")
        
        # Active rooms
        active_rooms = [r for r_id, r in self.active_rooms.items() if not r['completed']]
        
        if active_rooms:
            print(f"{Colors.GREEN}? Active Rooms{Colors.RESET}")
            print(f"{Colors.CYAN}{'©¤'*80}{Colors.RESET}")
            
            for room_id, room in self.active_rooms.items():
                if room['completed']:
                    continue
                
                status_color = Colors.YELLOW if room['status'] == 'waiting' else Colors.BLUE
                status_icon = '?' if room['status'] == 'waiting' else '?'
                
                print(f"{status_icon} {Colors.BOLD}Room {room_id}{Colors.RESET} - {status_color}{room['status'].upper()}{Colors.RESET}")
                print(f"   Players: {', '.join(room['players']) if room['players'] else 'None'}")
                
                if room['status'] == 'playing':
                    print(f"   Round: {Colors.BOLD}{room['current_round']}/9{Colors.RESET}")
                    print(f"   Started: {room['started']}")
                
                print()
        else:
            print(f"{Colors.YELLOW}No active rooms in the last 10 minutes{Colors.RESET}\n")
        
        # Recent events
        if self.recent_events:
            print(f"{Colors.MAGENTA}? Recent Events (Last 10){Colors.RESET}")
            print(f"{Colors.CYAN}{'©¤'*80}{Colors.RESET}")
            for event in self.recent_events[:10]:
                # Color code events
                msg = event['message']
                if 'ERROR' in msg:
                    color = Colors.RED
                    icon = '?'
                elif 'created' in msg:
                    color = Colors.GREEN
                    icon = '?'
                elif 'joined' in msg:
                    color = Colors.CYAN
                    icon = '?'
                elif 'started' in msg:
                    color = Colors.BLUE
                    icon = '?'
                elif 'complete' in msg:
                    color = Colors.GREEN
                    icon = '?'
                else:
                    color = Colors.WHITE
                    icon = '?'
                
                # Truncate long messages
                if len(msg) > 60:
                    msg = msg[:57] + '...'
                
                print(f"{icon} {color}[{event['time']}]{Colors.RESET} {msg}")
            print()
        
        print(f"{Colors.CYAN}{'©¤'*80}{Colors.RESET}")
        print(f"{Colors.WHITE}Press Ctrl+C to exit | Refreshing every 3 seconds...{Colors.RESET}")
    
    def run(self, refresh_interval=3):
        """Run the dashboard with auto-refresh"""
        try:
            while True:
                self.parse_recent_logs()
                self.render_dashboard()
                time.sleep(refresh_interval)
        except KeyboardInterrupt:
            print(f"\n\n{Colors.YELLOW}Dashboard closed{Colors.RESET}")
        finally:
            if self.ssh:
                self.ssh.close()

def main():
    print(f"{Colors.GREEN}Connecting to server...{Colors.RESET}")
    dashboard = GameDashboard()
    print(f"{Colors.GREEN}Connected! Starting dashboard...{Colors.RESET}")
    time.sleep(1)
    dashboard.run()

if __name__ == "__main__":
    main()

