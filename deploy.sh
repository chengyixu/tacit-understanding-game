#!/usr/bin/expect -f
# Simple deployment script for moqiyouxi backend

set timeout 30
set server_ip "43.137.34.201"
set username "root"
set password "0212Connect!"
set local_file "/Users/chengyixu/WeChatProjects/testchat/server0405.py"
set remote_file "/moqiyouxi_backend/server0405.py"

puts "Deploying moqiyouxi backend..."

# Copy the updated server file
spawn scp -o StrictHostKeyChecking=no $local_file $username@$server_ip:$remote_file
expect {
    "password:" {
        send "$password\r"
        expect eof
    }
}

# Restart the server
spawn ssh -o StrictHostKeyChecking=no $username@$server_ip
expect {
    "password:" {
        send "$password\r"
        expect "# "
    }
}

# Kill existing server process
send "pkill -9 -f server0405.py\r"
expect "# "
sleep 1

# Clear port if needed
send "fuser -k 3000/tcp 2>/dev/null\r"
expect "# "
sleep 1

# Start the server with Python 3.6 (has numpy/scipy)
send "cd /moqiyouxi_backend && nohup python3.6 server0405.py > server.log 2>&1 &\r"
expect "# "
sleep 3

# Check if server started
send "ps aux | grep server0405.py | grep -v grep\r"
expect "# "

# Show last few lines of log
send "tail -5 /moqiyouxi_backend/server.log\r"
expect "# "

send "exit\r"
expect eof

puts "Deployment complete!"