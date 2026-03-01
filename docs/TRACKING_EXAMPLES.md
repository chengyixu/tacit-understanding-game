# 📊 What You Can Track with the Monitoring Tools

## Yes! You can see EVERYTHING about player activity:

### 1. 👤 **When Players Enter**
```bash
# Track when players join rooms
python3 monitor_server.py --search "joined room"

# Example output:
2025-09-30 15:20:05 - INFO - Player 李四 joined room 607486
2025-09-30 15:21:12 - INFO - Player 张三 joined room 123456
```

### 2. ❓ **What Questions They Face**
```bash
# See the battles (questions) presented to each player
python3 monitor_server.py --search "Generated battle"

# Example output:
Generated battle for player abc123 round 1: champion=苹果 vs challenger=香蕉
Generated battle for player abc123 round 2: champion=苹果 vs challenger=橘子
Generated battle for player abc123 round 3: champion=橘子 vs challenger=西瓜
```

### 3. ✅ **What Choices They Made**
```bash
# Track player selections for each round
python3 monitor_server.py --search "submitted choice"

# Example output:
Player abc123 submitted choice for round 1: chose 苹果
Player abc123 submitted choice for round 2: chose 橘子
Player abc123 submitted choice for round 3: chose 橘子
```

### 4. 👋 **When They Left**
```bash
# Monitor disconnections and room exits
python3 monitor_server.py --search "left room\|disconnected"

# Example output:
2025-09-30 15:25:43 - INFO - Player 张三 left room 123456
2025-09-30 15:25:44 - INFO - WebSocket connection closed for player abc123
```

## 🎮 **Complete Game Session Tracking**

### Track Everything About a Specific Player
```bash
# By player nickname
python3 track_player_journey.py "张三"

# By player ID (even partial)
python3 track_player_journey.py "abc123"
```

**You'll see:**
- 📝 Registration time and initial nickname
- ✏️ Any nickname updates
- 🏠 Room creation or joining
- 🎮 Game start time
- ⚔️ All 9 rounds of questions (battles)
- ✅ Player's choice for each round
- 🏆 Game completion and tacit value score
- 👋 Disconnection time

### Track Everything in a Room
```bash
# Monitor all activity in room 123456
python3 monitor_server.py --search "Room 123456"
```

**You'll see:**
- Who created the room
- All players who joined
- When the game started
- Each round's progress
- Final results and tacit values
- When players left

## 🔍 **Real-Time Monitoring Examples**

### Watch Live Player Activity
```bash
# See everything happening right now
python3 monitor_server.py --follow

# Filter to just room/game events
python3 monitor_server.py --rooms

# Watch a specific player in real-time
python3 monitor_server.py --player "张三"
```

### Monitor Specific Events
```bash
# Just registrations
python3 monitor_server.py --search "Player registered"

# Just game completions
python3 monitor_server.py --search "Game complete"

# Just errors
python3 monitor_server.py --errors
```

## 📈 **Statistical Analysis**

```bash
# Get overall statistics
python3 monitor_server.py --stats

# Output includes:
- Total players registered
- Rooms created
- Games started/completed
- Error count
- Active rooms
- AI players created
```

## 🎯 **Specific Use Cases**

### Debug Why a Game Failed
```bash
# Find the room
python3 monitor_server.py --search "error.*Room 123456"

# Track both players
python3 track_player_journey.py "player1_id"
python3 track_player_journey.py "player2_id"
```

### Analyze Player Behavior Pattern
```bash
# Export a player's full history
python3 track_player_journey.py "张三" > zhangsan_history.txt

# Search for patterns
grep "chose:" zhangsan_history.txt
```

### Monitor Peak Usage Times
```bash
# See registrations by hour
python3 monitor_server.py --search "Player registered" | cut -d' ' -f2 | cut -d':' -f1 | sort | uniq -c
```

## 💡 **Pro Tips**

1. **Combine filters** for precise tracking:
   ```bash
   python3 monitor_server.py --search "Room 123456.*round.*complete"
   ```

2. **Save sessions** for later analysis:
   ```bash
   python3 monitor_server.py --follow > game_session_$(date +%Y%m%d).log
   ```

3. **Track multiple players** simultaneously:
   ```bash
   # Open multiple terminals
   python3 monitor_server.py --player "张三"  # Terminal 1
   python3 monitor_server.py --player "李四"  # Terminal 2
   ```

4. **Quick health check**:
   ```bash
   # One command to check everything
   python3 monitor_server.py --status && python3 monitor_server.py --stats
   ```

## 📝 **Log Entry Examples**

### Complete Player Journey
```
15:20:01 - Player registered: abc123def (张三)
15:20:05 - Player abc123def updated nickname to: 张三游戏达人
15:20:10 - Room 123456 created by player abc123def
15:20:15 - Player xyz789ghi joined room 123456
15:20:20 - Game started in room 123456
15:20:25 - Generated battle for player abc123def round 1: 苹果 vs 香蕉
15:20:30 - Player abc123def submitted choice for round 1: chose 苹果
[... rounds 2-8 ...]
15:23:45 - Generated battle for player abc123def round 9: 葡萄 vs 草莓
15:23:50 - Player abc123def submitted choice for round 9: chose 葡萄
15:24:00 - Game complete in room 123456, tacit value: 67%
15:24:05 - Player abc123def left room 123456
15:24:06 - WebSocket connection closed for player abc123def
```

## 🎨 **Visual Indicators in Logs**

The monitoring tools use colors and emojis to make logs easy to scan:
- 🔴 RED = Errors, disconnections
- 🟡 YELLOW = Warnings, round transitions
- 🟢 GREEN = Success, registrations, completions
- 🔵 BLUE = Game starts
- 🟣 MAGENTA = Room events
- 🟦 CYAN = Player joins, connections