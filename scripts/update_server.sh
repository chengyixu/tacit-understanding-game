#!/bin/bash

# SSH into server and update the tacit value calculation
ssh root@47.117.176.214 << 'EOF'
cd /moqiyouxi_backend

# Create backup
cp server0405.py server0405.py.backup

# Update the _compute_matrix_correlation function
python3 << 'PYTHON'
import re

# Read the file
with open('server0405.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the _compute_matrix_correlation method
pattern = r'def _compute_matrix_correlation\(self, matrix1, matrix2\):.*?return tacit_value, round\(correlation, 4\), data_points'

new_method = '''def _compute_matrix_correlation(self, matrix1, matrix2):
        flat1 = matrix1.flatten()
        flat2 = matrix2.flatten()

        mask = (flat1 != 0) | (flat2 != 0)
        data_points = int(np.sum(mask))

        if data_points < 2:
            return 50.0, 0.0, data_points

        values1 = flat1[mask]
        values2 = flat2[mask]

        if np.allclose(values1, values2):
            correlation = 1.0
        else:
            std1 = np.std(values1)
            std2 = np.std(values2)

            if std1 == 0 or std2 == 0:
                correlation = 0.0
            else:
                correlation = float(np.corrcoef(values1, values2)[0, 1])
                if np.isnan(correlation):
                    correlation = 0.0

        # Original calculation
        base_value = max(0.0, min(100.0, (correlation + 1) * 50))
        
        # Apply improvement formula: use power function to boost scores
        # This makes scores roughly 2.5x higher for low values while preserving high scores
        # Formula: (base_value/100)^0.4 * 100
        # This transforms: 10%->40%, 20%->53%, 30%->61%, 40%->68%, 50%->76%, 60%->82%, 70%->88%, 80%->93%, 100%->100%
        improved_value = min(100.0, (base_value / 100.0) ** 0.4 * 100.0)
        
        tacit_value = round(improved_value, 1)
        return tacit_value, round(correlation, 4), data_points'''

# Replace the method
content = re.sub(pattern, new_method, content, flags=re.DOTALL)

# Also update the details calculation
details_pattern = r"details = \{[\s\S]*?'explanation':.*?\n        \}"

new_details = """        # Calculate base value for display
        base_value = max(0.0, min(100.0, (correlation + 1) * 50))
        
        details = {
            'method': 'Matrix Correlation (默契值)',
            'calculation': f"基础值 = (相关系数 {correlation:.4f} + 1) × 50 = {base_value:.1f}%, 改进值 = ({base_value:.1f}/100)^0.4 × 100 = {tacit_value:.1f}%",
            'correlation': correlation,
            'matrix_size': f"{matrix1.shape[0]}×{matrix1.shape[1]}",
            'data_points': data_points,
            'choices': choices,
            'player1': player1.nickname if player1 else None,
            'player2': player2.nickname if player2 else None,
            'explanation': '双方在全部词汇对战中的胜负偏好被映射为矩阵，通过计算两个偏好矩阵的相关系数并应用改进公式得到最终默契值，使分数更加友好。'
        }"""

content = re.sub(details_pattern, new_details, content)

# Write back
with open('server0405.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully")
PYTHON

# Restart the server
echo "Restarting server..."
pkill -f server0405.py || true
sleep 2
nohup python3 server0405.py > server.log 2>&1 &
echo "Server restarted"

EOF