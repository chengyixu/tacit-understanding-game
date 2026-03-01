#!/bin/bash

# Quick game monitoring script
# Run this while testing your game

echo "🎮 默契小游戏 - Real-Time Monitor"
echo "================================"
echo ""
echo "Checking server status..."
python3 monitor_server.py --status
echo ""
echo "Starting live room activity monitoring..."
echo "Press Ctrl+C to stop"
echo ""
echo "================================"
echo ""

# Start monitoring room activity
python3 monitor_server.py --rooms

