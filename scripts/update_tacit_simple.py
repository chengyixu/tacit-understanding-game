#!/usr/bin/env python3
import re

# Read the file
with open('server0405.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the _compute_matrix_correlation method and replace it
old_method_pattern = r'(def _compute_matrix_correlation\(self, matrix1, matrix2\):.*?)tacit_value = round\(max\(0\.0, min\(100\.0, \(correlation \+ 1\) \* 50\)\), 1\)\s+return tacit_value, round\(correlation, 4\), data_points'

new_method_end = '''        # Original calculation
        base_value = max(0.0, min(100.0, (correlation + 1) * 50))
        
        # Apply improvement formula: use power function to boost scores
        # This makes scores roughly 2.5x higher for low values while preserving high scores
        # Formula: (base_value/100)^0.4 * 100
        # This transforms: 10%->40%, 20%->53%, 30%->61%, 40%->68%, 50%->76%, 60%->82%, 70%->88%, 80%->93%, 100%->100%
        improved_value = min(100.0, (base_value / 100.0) ** 0.4 * 100.0)
        
        tacit_value = round(improved_value, 1)
        return tacit_value, round(correlation, 4), data_points'''

# First replacement - update the method
def replace_method(match):
    method_start = match.group(1)
    # Remove the old tacit_value calculation line
    method_start = re.sub(r'\s+tacit_value = round\(max\(0\.0, min\(100\.0, \(correlation \+ 1\) \* 50\)\), 1\)', '', method_start)
    return method_start + new_method_end

content = re.sub(old_method_pattern, replace_method, content, flags=re.DOTALL)

# Second replacement - update the details dictionary
old_details_pattern = r"(details = \{\s+'method': 'Matrix Correlation \(默契值\)',\s+'calculation': f\"默契值 = \(相关系数 \{correlation:.4f\} \+ 1\) × 50 = \{tacit_value:.1f\}%\")"

new_details_start = """        # Calculate base value for display
        base_value = max(0.0, min(100.0, (correlation + 1) * 50))
        
        details = {
            'method': 'Matrix Correlation (默契值)',
            'calculation': f"基础值 = (相关系数 {correlation:.4f} + 1) × 50 = {base_value:.1f}%, 改进值 = ({base_value:.1f}/100)^0.4 × 100 = {tacit_value:.1f}%\""""

content = re.sub(old_details_pattern, new_details_start, content)

# Also update the explanation line
old_explanation = "'explanation': '双方在全部词汇对战中的胜负偏好被映射为矩阵，通过计算两个偏好矩阵的相关系数得到最终默契值。'"
new_explanation = "'explanation': '双方在全部词汇对战中的胜负偏好被映射为矩阵，通过计算两个偏好矩阵的相关系数并应用改进公式得到最终默契值，使分数更加友好。'"

content = content.replace(old_explanation, new_explanation)

# Write the file back
with open('server0405.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated server0405.py with improved tacit value calculation!")