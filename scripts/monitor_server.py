#!/usr/bin/env python3
"""
Advanced server monitoring script for 默契小游戏 backend
"""

import paramiko
import time
import sys
import re
from datetime import datetime
from typing import Optional
import argparse

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

class ServerMonitor:
    def __init__(self):
        self.ssh = None
        self.connect()
    
    def connect(self):
        """Establish SSH connection to server"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                hostname=SERVER_CONFIG['hostname'],
                username=SERVER_CONFIG['username'],
                password=SERVER_CONFIG['password'],
                port=SERVER_CONFIG['port']
            )
            print(f"{Colors.GREEN}✓ Connected to server{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}✗ Connection failed: {e}{Colors.RESET}")
            sys.exit(1)
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh:
            self.ssh.close()
            print(f"{Colors.YELLOW}Disconnected from server{Colors.RESET}")
    
    def colorize_log_line(self, line: str) -> str:
        """Add color to log lines based on content"""
        if 'ERROR' in line or 'Exception' in line:
            return f"{Colors.RED}{line}{Colors.RESET}"
        elif 'WARNING' in line:
            return f"{Colors.YELLOW}{line}{Colors.RESET}"
        elif 'INFO' in line:
            return f"{Colors.GREEN}{line}{Colors.RESET}"
        elif 'Player registered' in line or 'joined room' in line:
            return f"{Colors.CYAN}{line}{Colors.RESET}"
        elif 'Room' in line and 'created' in line:
            return f"{Colors.MAGENTA}{line}{Colors.RESET}"
        elif 'Game started' in line or 'Game complete' in line:
            return f"{Colors.BLUE}{Colors.BOLD}{line}{Colors.RESET}"
        return line
    
    def tail_logs(self, lines: int = 0, follow: bool = False, filter_pattern: Optional[str] = None):
        """Tail server logs with optional filtering"""
        try:
            if follow:
                cmd = f"tail -f {SERVER_CONFIG['log_path']}"
            else:
                cmd = f"tail -n {lines} {SERVER_CONFIG['log_path']}" if lines > 0 else f"cat {SERVER_CONFIG['log_path']}"
            
            if filter_pattern:
                cmd += f" | grep -E '{filter_pattern}'"
            
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            
            if follow:
                print(f"{Colors.CYAN}📡 Live monitoring (Ctrl+C to stop)...{Colors.RESET}\n")
                try:
                    for line in iter(stdout.readline, ""):
                        if line:
                            print(self.colorize_log_line(line.strip()))
                except KeyboardInterrupt:
                    print(f"\n{Colors.YELLOW}Monitoring stopped{Colors.RESET}")
            else:
                output = stdout.read().decode('utf-8')
                for line in output.split('\n'):
                    if line:
                        print(self.colorize_log_line(line))
        except Exception as e:
            print(f"{Colors.RED}Error reading logs: {e}{Colors.RESET}")
    
    def search_logs(self, pattern: str, context_lines: int = 2):
        """Search logs for specific pattern with context"""
        try:
            cmd = f"grep -C {context_lines} '{pattern}' {SERVER_CONFIG['log_path']} | tail -100"
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            output = stdout.read().decode('utf-8')
            
            if output:
                print(f"{Colors.CYAN}Search results for '{pattern}':{Colors.RESET}\n")
                for line in output.split('\n'):
                    if line:
                        if pattern.lower() in line.lower():
                            print(f"{Colors.BOLD}{self.colorize_log_line(line)}{Colors.RESET}")
                        else:
                            print(self.colorize_log_line(line))
            else:
                print(f"{Colors.YELLOW}No matches found for '{pattern}'{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Error searching logs: {e}{Colors.RESET}")
    
    def get_stats(self):
        """Get server and game statistics from logs"""
        try:
            print(f"{Colors.CYAN}📊 Server Statistics:{Colors.RESET}\n")
            
            # Count various events
            stats_commands = {
                'Total players registered': "grep -c 'Player registered' {log}",
                'Rooms created': "grep -c 'Room.*created' {log}",
                'Games started': "grep -c 'Game started' {log}",
                'Games completed': "grep -c 'Game complete' {log}",
                'Errors': "grep -c 'ERROR' {log}",
                'Active rooms (last hour)': "grep 'Room' {log} | tail -100 | grep -c 'created'",
                'WebSocket connections': "grep -c 'WebSocket.*opened' {log}",
                'AI players created': "grep -c 'AI player' {log}"
            }
            
            for stat_name, cmd_template in stats_commands.items():
                cmd = cmd_template.format(log=SERVER_CONFIG['log_path'])
                stdin, stdout, stderr = self.ssh.exec_command(cmd)
                count = stdout.read().decode('utf-8').strip()
                print(f"  {Colors.GREEN}•{Colors.RESET} {stat_name}: {Colors.BOLD}{count}{Colors.RESET}")
            
            # Get last error
            print(f"\n{Colors.RED}Last error:{Colors.RESET}")
            cmd = f"grep 'ERROR' {SERVER_CONFIG['log_path']} | tail -1"
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            last_error = stdout.read().decode('utf-8').strip()
            if last_error:
                print(f"  {last_error}")
            else:
                print(f"  {Colors.GREEN}No errors found{Colors.RESET}")
            
        except Exception as e:
            print(f"{Colors.RED}Error getting stats: {e}{Colors.RESET}")
    
    def monitor_rooms(self):
        """Monitor room activity in real-time"""
        print(f"{Colors.MAGENTA}🎮 Monitoring room activity...{Colors.RESET}\n")
        pattern = "Room|joined|left|Game started|Game complete"
        self.tail_logs(follow=True, filter_pattern=pattern)
    
    def monitor_errors(self):
        """Monitor errors and warnings in real-time"""
        print(f"{Colors.RED}⚠️  Monitoring errors and warnings...{Colors.RESET}\n")
        pattern = "ERROR|WARNING|Exception|Failed"
        self.tail_logs(follow=True, filter_pattern=pattern)
    
    def monitor_player(self, player_id: str):
        """Monitor specific player activity"""
        print(f"{Colors.CYAN}👤 Monitoring player: {player_id}{Colors.RESET}\n")
        self.tail_logs(follow=True, filter_pattern=player_id)
    
    def clear_logs(self):
        """Clear the log file (with confirmation)"""
        confirm = input(f"{Colors.RED}⚠️  Are you sure you want to clear the log file? (yes/no): {Colors.RESET}")
        if confirm.lower() == 'yes':
            cmd = f"echo 'Log cleared at {datetime.now()}' > {SERVER_CONFIG['log_path']}"
            self.ssh.exec_command(cmd)
            print(f"{Colors.GREEN}✓ Log file cleared{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}Operation cancelled{Colors.RESET}")
    
    def check_server_status(self):
        """Check if the game server is running"""
        try:
            cmd = "ps aux | grep server0405.py | grep -v grep"
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            output = stdout.read().decode('utf-8')
            
            if output:
                print(f"{Colors.GREEN}✓ Game server is running{Colors.RESET}")
                print(f"  Process info: {output.strip()}")
            else:
                print(f"{Colors.RED}✗ Game server is not running{Colors.RESET}")
                
            # Check port
            cmd = "netstat -tuln | grep :3001"
            stdin, stdout, stderr = self.ssh.exec_command(cmd)
            output = stdout.read().decode('utf-8')
            if output:
                print(f"{Colors.GREEN}✓ Port 3001 is listening{Colors.RESET}")
            else:
                print(f"{Colors.RED}✗ Port 3001 is not listening{Colors.RESET}")
                
        except Exception as e:
            print(f"{Colors.RED}Error checking status: {e}{Colors.RESET}")
    
    def restart_server(self):
        """Restart the game server"""
        confirm = input(f"{Colors.YELLOW}Restart game server? (yes/no): {Colors.RESET}")
        if confirm.lower() == 'yes':
            print(f"{Colors.YELLOW}Restarting server...{Colors.RESET}")
            cmd = "cd /moqiyouxi_backend && pkill -f server0405.py; nohup python3 server0405.py > server.log 2>&1 &"
            self.ssh.exec_command(cmd)
            time.sleep(2)
            self.check_server_status()

def main():
    parser = argparse.ArgumentParser(description='Monitor 默契小游戏 server')
    parser.add_argument('--tail', type=int, help='Show last N lines of log')
    parser.add_argument('--follow', '-f', action='store_true', help='Follow log in real-time')
    parser.add_argument('--search', type=str, help='Search for pattern in logs')
    parser.add_argument('--stats', action='store_true', help='Show server statistics')
    parser.add_argument('--rooms', action='store_true', help='Monitor room activity')
    parser.add_argument('--errors', action='store_true', help='Monitor errors only')
    parser.add_argument('--player', type=str, help='Monitor specific player')
    parser.add_argument('--status', action='store_true', help='Check server status')
    parser.add_argument('--restart', action='store_true', help='Restart game server')
    parser.add_argument('--clear', action='store_true', help='Clear log file')
    
    args = parser.parse_args()
    
    monitor = ServerMonitor()
    
    try:
        if args.tail:
            monitor.tail_logs(lines=args.tail)
        elif args.follow:
            monitor.tail_logs(follow=True)
        elif args.search:
            monitor.search_logs(args.search)
        elif args.stats:
            monitor.get_stats()
        elif args.rooms:
            monitor.monitor_rooms()
        elif args.errors:
            monitor.monitor_errors()
        elif args.player:
            monitor.monitor_player(args.player)
        elif args.status:
            monitor.check_server_status()
        elif args.restart:
            monitor.restart_server()
        elif args.clear:
            monitor.clear_logs()
        else:
            # Interactive menu
            print(f"{Colors.CYAN}{'='*50}{Colors.RESET}")
            print(f"{Colors.BOLD}   默契小游戏 Server Monitor{Colors.RESET}")
            print(f"{Colors.CYAN}{'='*50}{Colors.RESET}\n")
            
            while True:
                print("\nOptions:")
                print("1. Live monitoring")
                print("2. Show last 50 lines")
                print("3. Show statistics")
                print("4. Monitor rooms")
                print("5. Monitor errors")
                print("6. Search logs")
                print("7. Check server status")
                print("8. Restart server")
                print("9. Clear logs")
                print("0. Exit")
                
                choice = input(f"\n{Colors.CYAN}Choose option: {Colors.RESET}")
                
                if choice == '1':
                    monitor.tail_logs(follow=True)
                elif choice == '2':
                    monitor.tail_logs(lines=50)
                elif choice == '3':
                    monitor.get_stats()
                elif choice == '4':
                    monitor.monitor_rooms()
                elif choice == '5':
                    monitor.monitor_errors()
                elif choice == '6':
                    pattern = input("Enter search pattern: ")
                    monitor.search_logs(pattern)
                elif choice == '7':
                    monitor.check_server_status()
                elif choice == '8':
                    monitor.restart_server()
                elif choice == '9':
                    monitor.clear_logs()
                elif choice == '0':
                    break
                else:
                    print(f"{Colors.RED}Invalid option{Colors.RESET}")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
    finally:
        monitor.disconnect()

if __name__ == "__main__":
    main()