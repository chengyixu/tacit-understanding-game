#!/bin/bash

echo "Fixing syntax error on server..."

# SSH and fix the syntax error
sshpass -p '0212Connect!' ssh -o StrictHostKeyChecking=no root@47.117.176.214 << 'EOF'
cd /moqiyouxi_backend

# Fix the syntax error in line 740
sed -i "s/{\\\\'action\\\\': \\\\'choiceSubmitted\\\\', \\\\'round\\\\': data.get(\\\\'round\\\\')/{'action': 'choiceSubmitted', 'round': data.get('round')/g" server0405.py

# Verify the fix
echo "Line 740 after fix:"
sed -n '740p' server0405.py

# Restart the server
echo -e "\nStopping old server..."
pkill -f server0405.py || true
sleep 2

echo "Starting new server..."
nohup python3 server0405.py > server.log 2>&1 &

# Wait for server to start
sleep 3

# Check if server is running
if pgrep -f server0405.py > /dev/null; then
    echo -e "\n✅ Server restarted successfully!"
    echo -e "\nRecent server log:"
    tail -n 10 server.log
else
    echo -e "\n❌ Server failed to start!"
    echo -e "\nError log:"
    tail -n 30 server.log
fi

EOF

echo -e "\n✅ Fix completed!"