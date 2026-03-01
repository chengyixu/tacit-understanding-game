#!/usr/bin/expect -f
# Check server status and numpy/scipy availability

set timeout 30
set server_ip "43.137.34.201"
set username "root"
set password "0212Connect!"

puts "Checking server status..."

spawn ssh -o StrictHostKeyChecking=no $username@$server_ip
expect {
    "password:" {
        send "$password\r"
        expect "# "
    }
}

# Check which Python is running the server
send "ps aux | grep server0405\r"
expect "# "

# Check if numpy and scipy are installed for Python 3.6
puts "\n\nChecking numpy/scipy for python3.6..."
send "python3.6 -c 'import numpy; import scipy; print(\"numpy version:\", numpy.__version__); print(\"scipy version:\", scipy.__version__)'\r"
expect "# "

# Check server log for errors
puts "\n\nChecking server log..."
send "tail -20 /moqiyouxi_backend/server.log\r"
expect "# "

# Test direct import in server directory
puts "\n\nTesting import in server directory..."
send "cd /moqiyouxi_backend && python3.6 -c 'import numpy; from scipy.stats import pearsonr; print(\"Import successful!\")'\r"
expect "# "

send "exit\r"
expect eof

puts "Check complete!"