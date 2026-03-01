# 默契小游戏 - Quick Start

## 📁 Project Structure
```
/WeChatProjects/testchat/
├── pages/          # WeChat mini-program pages
├── utils/          # Utility functions
├── scripts/        # Backend monitoring & deployment scripts
├── docs/           # Documentation
├── logs/           # Log files
├── app.js          # Main app entry
└── QUICK_START.md  # This file
```

## 🎮 Monitor Backend (Real-time)

```bash
# Quick start - Full real-time logs
./monitor.sh

# OR use these alternatives:

# Live dashboard with stats
python3 scripts/game_dashboard.py

# Room activity only
python3 scripts/monitor_server.py --rooms

# All monitoring options
python3 scripts/monitor_server.py
```

## 📊 After Game Analysis

```bash
# Track player journey
python3 scripts/track_player_journey.py
```

## 🔧 Server Management

```bash
# Check server status
python3 scripts/monitor_server.py --status

# View statistics
python3 scripts/monitor_server.py --stats
```

## 📚 Documentation

- `README.md` - Main project documentation
- `CLAUDE.md` - Detailed project notes
- `docs/` - All other guides and documentation

