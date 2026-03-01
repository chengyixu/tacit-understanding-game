#!/bin/bash

# Server connection details
SERVER_IP="47.117.176.214"
SERVER_USER="root"
SERVER_PASS="0212Connect!"
LOG_PATH="/moqiyouxi_backend/server.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=========================================="
echo "   默契小游戏 Server Log Monitor"
echo "=========================================="
echo ""

# Function to show menu
show_menu() {
    echo "Choose monitoring option:"
    echo "1) Live tail (follow new logs)"
    echo "2) Last 50 lines"
    echo "3) Last 100 lines"
    echo "4) Search for errors"
    echo "5) Search for specific player"
    echo "6) View full log file"
    echo "7) Clear log file (caution!)"
    echo "8) Monitor WebSocket connections"
    echo "9) Exit"
}

# Main monitoring function
monitor_logs() {
    case $1 in
        1)
            echo -e "${GREEN}Starting live log monitoring...${NC}"
            echo "Press Ctrl+C to stop"
            echo ""
            sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
                "tail -f $LOG_PATH" | while read line; do
                    # Color code different log levels
                    if [[ $line == *"ERROR"* ]]; then
                        echo -e "${RED}$line${NC}"
                    elif [[ $line == *"WARNING"* ]]; then
                        echo -e "${YELLOW}$line${NC}"
                    elif [[ $line == *"INFO"* ]]; then
                        echo -e "${GREEN}$line${NC}"
                    else
                        echo "$line"
                    fi
                done
            ;;
        2)
            echo -e "${GREEN}Last 50 lines:${NC}"
            sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
                "tail -n 50 $LOG_PATH"
            ;;
        3)
            echo -e "${GREEN}Last 100 lines:${NC}"
            sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
                "tail -n 100 $LOG_PATH"
            ;;
        4)
            echo -e "${RED}Searching for errors:${NC}"
            sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
                "grep -i 'error\\|exception\\|failed' $LOG_PATH | tail -50"
            ;;
        5)
            echo -n "Enter player ID or nickname to search: "
            read search_term
            echo -e "${GREEN}Searching for '$search_term':${NC}"
            sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
                "grep -i '$search_term' $LOG_PATH | tail -50"
            ;;
        6)
            echo -e "${GREEN}Full log file (press q to quit):${NC}"
            sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
                "less $LOG_PATH"
            ;;
        7)
            echo -e "${RED}WARNING: This will clear the log file!${NC}"
            echo -n "Are you sure? (yes/no): "
            read confirm
            if [ "$confirm" = "yes" ]; then
                sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
                    "echo '' > $LOG_PATH && echo 'Log cleared at $(date)' > $LOG_PATH"
                echo "Log file cleared."
            else
                echo "Operation cancelled."
            fi
            ;;
        8)
            echo -e "${BLUE}Monitoring WebSocket connections:${NC}"
            sshpass -p "$SERVER_PASS" ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" \
                "tail -f $LOG_PATH | grep -E 'WebSocket|connected|disconnected|registered|Player'"
            ;;
        9)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
}

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo -e "${RED}sshpass is not installed!${NC}"
    echo "Install it with: brew install hudochenkov/sshpass/sshpass"
    exit 1
fi

# Main loop
while true; do
    show_menu
    echo -n "Enter your choice: "
    read choice
    echo ""
    monitor_logs $choice
    echo ""
    echo "Press Enter to continue..."
    read
    clear
done