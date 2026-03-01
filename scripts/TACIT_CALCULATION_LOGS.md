# 默契值计算日志详解 (Tacit Value Calculation Logs)

## Overview
After applying the updated `server0405.py`, when you run `tail_logs.sh`, you will see detailed step-by-step calculation logs for the tacit value (默契值) computation.

## Example Log Output

When a game completes, you'll see logs like this:

```
================================================================================
开始计算默契值 (Starting Tacit Value Calculation)
================================================================================
Player 1: 张三 (87ee8e2a...)
Player 2: 李四 (2080644f...)
Word pool size: 10 words
Building preference matrices (10x10)...
Player 1 made 9 choices
Player 2 made 9 choices
--------------------------------------------------------------------------------
计算矩阵相关性 (Computing Matrix Correlation)
--------------------------------------------------------------------------------
Matrix 1 flattened size: 100
Matrix 2 flattened size: 100
Non-zero data points: 36
Player 1 preference values: mean=1.5000, std=0.5000
Player 2 preference values: mean=1.5278, std=0.5025
Pearson correlation coefficient: 0.7234
--------------------------------------------------------------------------------
默契值计算公式 (Tacit Value Formula):
  相关系数 (Correlation): 0.7234
  正相关系数 (Positive correlation): 0.7234
  分子 (Numerator): 2.5 × 0.7234 = 1.8085
  分母 (Denominator): 1.0 + 1.5 × 0.7234 = 2.0851
  基础值 (Base value): 1.8085 / 2.0851 = 0.8673
  默契值 (Tacit value): 0.8673 × 100 = 87%
--------------------------------------------------------------------------------
--------------------------------------------------------------------------------
逐轮选择对比 (Round-by-Round Choice Comparison)
--------------------------------------------------------------------------------
Round 1:
  张三: [奈雪的茶 vs 小米] → 奈雪的茶
  李四: [破五 vs 小米] → 小米
  Same choice: ✗ NO
Round 2:
  张三: [奈雪的茶 vs 沈阳] → 奈雪的茶
  李四: [小米 vs 小红书] → 小米
  Same choice: ✗ NO
Round 3:
  张三: [奈雪的茶 vs 小红书] → 小红书
  李四: [小米 vs 葛优] → 葛优
  Same choice: ✗ NO
Round 4:
  张三: [小红书 vs 何冰娇] → 小红书
  李四: [葛优 vs 奈雪的茶] → 奈雪的茶
  Same choice: ✗ NO
Round 5:
  张三: [小红书 vs 葛优] → 葛优
  李四: [奈雪的茶 vs 沈阳] → 奈雪的茶
  Same choice: ✗ NO
Round 6:
  张三: [葛优 vs 破五] → 葛优
  李四: [奈雪的茶 vs 小米粥] → 奈雪的茶
  Same choice: ✗ NO
Round 7:
  张三: [葛优 vs 和府捞面] → 葛优
  李四: [奈雪的茶 vs 和府捞面] → 奈雪的茶
  Same choice: ✗ NO
Round 8:
  张三: [葛优 vs 小米粥] → 葛优
  李四: [奈雪的茶 vs 何冰娇] → 奈雪的茶
  Same choice: ✗ NO
Round 9:
  张三: [葛优 vs 奈雪的茶] → 葛优
  李四: [奈雪的茶 vs 小红书] → 奈雪的茶
  Same choice: ✗ NO
--------------------------------------------------------------------------------
Total rounds compared: 9
Same choices: 0/9 rounds
Agreement rate: 0.0%
--------------------------------------------------------------------------------
================================================================================
最终默契值 (Final Tacit Value): 87%
================================================================================
```

## Log Sections Explained

### 1. **Calculation Header**
```
开始计算默契值 (Starting Tacit Value Calculation)
```
Shows when the tacit value calculation starts.

### 2. **Player Information**
```
Player 1: 张三 (87ee8e2a...)
Player 2: 李四 (2080644f...)
```
Shows the nicknames and player IDs involved in the calculation.

### 3. **Matrix Correlation Computation**
```
计算矩阵相关性 (Computing Matrix Correlation)
```
Shows:
- Matrix dimensions
- Number of data points
- Statistical measures (mean, standard deviation)
- Pearson correlation coefficient

### 4. **Formula Breakdown**
```
默契值计算公式 (Tacit Value Formula)
```
Shows the complete formula calculation step-by-step:
- **Correlation**: Raw correlation coefficient (-1 to 1)
- **Positive correlation**: max(0, correlation)
- **Numerator**: 2.5 × positive_corr
- **Denominator**: 1.0 + 1.5 × positive_corr
- **Base value**: numerator / denominator
- **Tacit value**: base_value × 100

### 5. **Round-by-Round Comparison**
```
逐轮选择对比 (Round-by-Round Choice Comparison)
```
For each round:
- Shows both players' battle pairs
- Shows what each player chose
- Indicates if they chose the same word (✓ YES / ✗ NO)

### 6. **Summary Statistics**
```
Total rounds compared: 9
Same choices: 3/9 rounds
Agreement rate: 33.3%
```
Shows overall agreement between players.

### 7. **Final Result**
```
最终默契值 (Final Tacit Value): 87%
```
The final tacit value percentage.

## How to View These Logs

### Real-time monitoring:
```bash
cd /Users/chengyixu/WeChatProjects/testchat/scripts
./tail_logs.sh
```

### Search for specific calculation:
```bash
ssh Panor
cd /moqiyouxi_backend
grep -A 100 "开始计算默契值" server.log | less
```

### View only formula calculations:
```bash
ssh Panor
cd /moqiyouxi_backend
grep "默契值计算公式" -A 8 server.log
```

## Notes

- All calculations are logged in real-time
- Logs include both Chinese and English for clarity
- The formula is transparent and can be verified
- Each game's calculation is separated by `====` lines for easy identification

