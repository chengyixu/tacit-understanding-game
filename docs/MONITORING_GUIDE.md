# 📊 Server Monitoring Guide for 默契小游戏

This guide explains how to monitor the backend server logs and status for the game.

## 🚀 Quick Start

### Option 1: Python Monitor (Recommended)

```bash
# Check if server is running
python3 monitor_server.py --status

# Live monitoring
python3 monitor_server.py --follow

# Show last 100 lines
python3 monitor_server.py --tail 100

# Show statistics
python3 monitor_server.py --stats

# Monitor room activity only
python3 monitor_server.py --rooms

# Monitor errors only
python3 monitor_server.py --errors

# Search for specific pattern
python3 monitor_server.py --search "player_id_here"

# Monitor specific player
python3 monitor_server.py --player "张三"

# Interactive mode (menu-driven)
python3 monitor_server.py
```

### Option 2: Bash Script

```bash
# Make executable (first time only)
chmod +x monitor_server_logs.sh

# Run the script
./monitor_server_logs.sh
```

## 📋 Features

### Python Monitor (`monitor_server.py`)

#### Color-coded Log Output
- 🔴 **RED**: Errors and exceptions
- 🟡 **YELLOW**: Warnings
- 🟢 **GREEN**: Info messages
- 🔵 **BLUE**: Game starts/completes
- 🟣 **MAGENTA**: Room creation
- 🟦 **CYAN**: Player registration/joining

#### Command-line Options
| Option | Description |
|--------|-------------|
| `--status` | Check if game server is running |
| `--follow` or `-f` | Live monitoring (like `tail -f`) |
| `--tail N` | Show last N lines |
| `--stats` | Display server statistics |
| `--rooms` | Monitor room activity only |
| `--errors` | Monitor errors and warnings only |
| `--player NAME` | Monitor specific player activity |
| `--search PATTERN` | Search for pattern in logs |
| `--restart` | Restart the game server |
| `--clear` | Clear the log file |

#### Interactive Mode
Run without arguments for menu-driven interface:
```bash
python3 monitor_server.py
```

### Bash Script (`monitor_server_logs.sh`)

Provides a simple menu-driven interface with options:
1. Live tail (follow new logs)
2. Last 50 lines
3. Last 100 lines
4. Search for errors
5. Search for specific player
6. View full log file
7. Clear log file
8. Monitor WebSocket connections

## 🔧 Prerequisites

### For Python Monitor
```bash
# Install paramiko if not already installed
pip3 install paramiko
```

### For Bash Script
```bash
# Install sshpass (macOS)
brew install hudochenkov/sshpass/sshpass

# Or use the Python monitor which doesn't need sshpass
```

## 📊 Understanding Log Entries

### Common Log Patterns

#### Player Registration
```
2025-09-29 10:15:23 - INFO - Player registered: abc123def (张三)
```

#### Room Creation
```
2025-09-29 10:15:30 - INFO - Room 123456 created by player abc123def
```

#### Player Joining Room
```
2025-09-29 10:15:45 - INFO - Player xyz789ghi joined room 123456
```

#### Game Start
```
2025-09-29 10:16:00 - INFO - Game started in room 123456 with 2 players
```

#### Round Completion
```
2025-09-29 10:16:30 - INFO - Room 123456: Round 3 complete
```

#### Game Completion
```
2025-09-29 10:20:00 - INFO - Game complete in room 123456, tacit value: 78%
```

#### Errors
```
2025-09-29 10:21:00 - ERROR - Room not found: 999999
```

## 🔍 Troubleshooting

### Server Not Running
If the monitor shows the server is not running:
```bash
# Option 1: Use the monitor's restart feature
python3 monitor_server.py --restart

# Option 2: SSH manually and restart
ssh root@47.117.176.214
cd /moqiyouxi_backend
pkill -f server0405.py
nohup python3 server0405.py > server.log 2>&1 &
```

### Connection Issues
If you can't connect to the server:
1. Check your internet connection
2. Verify server IP hasn't changed: `47.117.176.214`
3. Ensure port 22 (SSH) is accessible

### Log File Too Large
If the log file becomes too large:
```bash
# Clear logs using monitor
python3 monitor_server.py --clear

# Or manually
ssh root@47.117.176.214
echo "Log cleared at $(date)" > /moqiyouxi_backend/server.log
```

## 📈 Statistics Explained

When using `--stats`, you'll see:

- **Total players registered**: All unique players who connected
- **Rooms created**: Total rooms created since last log clear
- **Games started**: Games that began playing
- **Games completed**: Games that finished all 9 rounds
- **Errors**: Total error count
- **Active rooms**: Recent room activity
- **WebSocket connections**: Total WebSocket connections opened
- **AI players created**: AI players spawned for test mode

## 🎮 Monitoring Game Sessions

### Track a Full Game Session
```bash
# Find a room ID in recent logs
python3 monitor_server.py --tail 50

# Then monitor that specific room
python3 monitor_server.py --search "Room 123456"
```

### Monitor Player Experience
```bash
# Track a specific player's journey
python3 monitor_server.py --player "player_nickname_or_id"
```

### Debug Issues
```bash
# See only errors and warnings
python3 monitor_server.py --errors

# Search for specific error patterns
python3 monitor_server.py --search "ERROR.*timeout"
```

## 🔐 Security Notes

- Server credentials are stored in the scripts
- Keep these files secure and don't share them publicly
- Consider using SSH keys instead of passwords for production
- The monitoring scripts have read-only access except for log clearing and server restart

## 💡 Tips

1. **Use filters**: When monitoring live, filter to reduce noise
2. **Check stats regularly**: Quick way to spot anomalies
3. **Monitor during testing**: Keep logs open while testing new features
4. **Save important logs**: Redirect output to file for later analysis
   ```bash
   python3 monitor_server.py --tail 1000 > logs_backup.txt
   ```

## 🆘 Help

For more information about the game server:
- Check `CLAUDE.md` for project documentation
- Server code: `/moqiyouxi_backend/server0405.py`
- Word database: `/moqiyouxi_backend/word_bank.json`