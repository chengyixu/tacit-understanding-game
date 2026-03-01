# 🎮 Quick Monitoring Commands for Game Testing

## 🚀 Best Command for Starting a New Game

### **Option 1: Live Full Monitoring (Recommended)**
```bash
python3 monitor_server.py --follow
```
Shows ALL real-time activity with color-coded output. Press `Ctrl+C` to stop.

### **Option 2: Room Activity Only (Cleaner)**
```bash
python3 monitor_server.py --rooms
```
Filters to show only room creation, joining, game start/complete events.

### **Option 3: Split View (Advanced)**
Open two terminal windows:

**Terminal 1 - Room Activity:**
```bash
python3 monitor_server.py --rooms
```

**Terminal 2 - Errors (if any):**
```bash
python3 monitor_server.py --errors
```

---

## 📊 Quick Status Checks

### Check if Server is Running
```bash
python3 monitor_server.py --status
```

### Get Statistics
```bash
python3 monitor_server.py --stats
```

### Last 50 Lines
```bash
python3 monitor_server.py --tail 50
```

---

## 🔍 During Game Testing

### Track Your Player
```bash
python3 monitor_server.py --player "YourNickname"
```

### Track Specific Room
```bash
python3 monitor_server.py --search "Room 123456"
```
(Replace 123456 with your actual room number)

### Monitor Only Errors
```bash
python3 monitor_server.py --errors
```

---

## 🎯 Advanced: Player Journey Tracking

### After game ends, analyze complete journey:
```bash
python3 track_player_journey.py
```
Then choose option 1 and enter your player nickname or ID.

### Track entire room activity:
```bash
python3 track_player_journey.py
```
Then choose option 2 and enter your room ID.

---

## 🔧 Troubleshooting Commands

### Restart Server
```bash
python3 monitor_server.py --restart
```

### Clear Logs (if too cluttered)
```bash
python3 monitor_server.py --clear
```

---

## 💡 Recommended Workflow

1. **Before Starting Game:**
   ```bash
   python3 monitor_server.py --status
   ```

2. **During Game (Terminal 1):**
   ```bash
   python3 monitor_server.py --rooms
   ```

3. **Watch for Errors (Terminal 2 - optional):**
   ```bash
   python3 monitor_server.py --errors
   ```

4. **After Game - Full Analysis:**
   ```bash
   python3 track_player_journey.py
   ```

---

## 🎨 Log Color Codes

- 🔴 **RED** = Errors/Exceptions
- 🟡 **YELLOW** = Warnings
- 🟢 **GREEN** = Info messages
- 🔵 **BLUE/BOLD** = Game start/complete
- 🟣 **MAGENTA** = Room creation
- 🟦 **CYAN** = Player registration/joining

---

## 📝 Example Session

```bash
# Step 1: Check server status
python3 monitor_server.py --status

# Step 2: Start live monitoring
python3 monitor_server.py --rooms

# Step 3: Launch game on WeChat mini-program

# Step 4: Watch the logs in real-time

# Step 5: After game, analyze journey
python3 track_player_journey.py
```

