#!/bin/bash

echo "Connecting to server to fix issues..."

# SSH and fix both issues
sshpass -p '0212Connect!' ssh -o StrictHostKeyChecking=no root@47.117.176.214 << 'EOF'
cd /moqiyouxi_backend

# Backup current file
cp server0405.py server0405.py.backup_$(date +%Y%m%d_%H%M%S)

# First, let's find where the tacit_value calculation actually is
echo "Finding tacit_value calculation line..."
grep -n "tacit_value = round(max" server0405.py

# Create Python script to fix the issues
cat > fix_server.py << 'PYTHON'
import re

# Read the server file
with open('server0405.py', 'r', encoding='utf-8') as f:
    content = f.read()

print("Fixing tacit value calculation...")

# Fix 1: Find and fix the tacit value formula wherever it is
# Look for the malformed calculation and fix it
patterns_to_fix = [
    # Pattern 1: Missing proper parentheses grouping
    (r'tacit_value = round\(max\(0\.0, min\(100\.0, \(\(correlation \+ 1\) \* 50\)\)\*\*0\.4\*100\)\), 1\)',
     'tacit_value = round(max(0.0, min(100.0, ((correlation + 1) * 50) ** 0.4 * 100)), 1)'),
    # Pattern 2: Alternative format that might exist
    (r'tacit_value = round\(max\(0\.0, min\(100\.0, \(\(correlation \+ 1\) \* 50\)\*\*0\.4\*100\)\), 1\)',
     'tacit_value = round(max(0.0, min(100.0, ((correlation + 1) * 50) ** 0.4 * 100)), 1)'),
    # Pattern 3: Space variations
    (r'tacit_value\s*=\s*round\(max\(0\.0,\s*min\(100\.0,\s*\(\(correlation\s*\+\s*1\)\s*\*\s*50\)\)\s*\*\*\s*0\.4\s*\*\s*100\)\),\s*1\)',
     'tacit_value = round(max(0.0, min(100.0, ((correlation + 1) * 50) ** 0.4 * 100)), 1)')
]

fixed = False
for pattern, replacement in patterns_to_fix:
    if re.search(pattern, content):
        content = re.sub(pattern, replacement, content)
        fixed = True
        print(f"Fixed tacit_value calculation with pattern: {pattern[:50]}...")
        break

if not fixed:
    print("Warning: Could not find exact tacit_value pattern to fix")
    print("Searching for any tacit_value calculation line...")
    # Try a more general approach
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'tacit_value = round(max' in line and '**0.4*100' in line:
            print(f"Found tacit_value on line {i+1}: {line}")
            # Fix the formula - ensure proper parentheses
            lines[i] = '        tacit_value = round(max(0.0, min(100.0, ((correlation + 1) * 50) ** 0.4 * 100)), 1)'
            content = '\n'.join(lines)
            fixed = True
            print(f"Fixed line {i+1}")
            break

# Also update the calculation display
print("Updating calculation display...")
old_calc_patterns = [
    r"'calculation': f\"默契值 = \(相关系数 \{correlation:\.4f\} \+ 1\) × 50 = \{tacit_value:\.1f\}%\",",
    r"'calculation': f\".*?tacit_value.*?\","
]

for pattern in old_calc_patterns:
    if re.search(pattern, content):
        content = re.sub(
            pattern,
            "'calculation': f\"基础值 = (相关系数 {correlation:.4f} + 1) × 50 = {((correlation + 1) * 50):.1f}%, 默契值 = {((correlation + 1) * 50):.1f}^0.4 × 100 = {tacit_value:.1f}%\",",
            content
        )
        print("Updated calculation display")
        break

print("Adding immediate response for choice submission...")

# Fix 2: Add immediate response after choice submission
# Find the handle_submit_choice method
pattern = r'(def handle_submit_choice\(self, data\):.*?\n.*?noun_id = data\.get\(\'nounId\'\)\s*\n)'
if re.search(pattern, content, flags=re.DOTALL):
    # Check if we already have choiceSubmitted
    if 'choiceSubmitted' not in content:
        replacement = r'\1        \n        # Send immediate confirmation to reduce loading time\n        self.write_message(json.dumps({\'action\': \'choiceSubmitted\', \'round\': data.get(\'round\')}))\n'
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        print("Added immediate response for choice submission")
    else:
        print("Immediate response already exists")
else:
    print("Warning: Could not find handle_submit_choice pattern")

# Write the fixed content back
with open('server0405.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nServer file fixed successfully!")

# Verify the fixes
print("\n=== Verification ===")
print("\nSearching for tacit_value calculation:")
with open('server0405.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines, start=1):
        if 'tacit_value = round' in line:
            print(f"Line {i}: {line.strip()}")
            
print("\nSearching for choiceSubmitted:")
with open('server0405.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines, start=1):
        if 'choiceSubmitted' in line:
            print(f"Line {i}: {line.strip()}")
            break
PYTHON

# Run the fix script
python3 fix_server.py

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

echo -e "\n✅ Script completed!"