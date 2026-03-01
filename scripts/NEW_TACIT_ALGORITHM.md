# 新默契值算法 (New Tacit Value Algorithm)

## 🎯 Changes Made

### 1. ❌ Removed Agreement Rate
- Removed all "Agreement rate" calculations and logging
- Removed "Same choice: ✓ YES / ✗ NO" indicators
- Simplified to focus on correlation-based tacit value

### 2. ✅ Use Absolute Value of Correlation
**Old Algorithm:**
```python
positive_corr = max(0.0, correlation)  # Negative becomes 0
```

**New Algorithm:**
```python
correlation = abs(raw_correlation)  # Negative becomes positive
```

**Why this matters:**
- **Before**: Correlation of -0.5752 → 0.0 → Tacit value = 0%
- **After**: Correlation of -0.5752 → 0.5752 → Tacit value = 36%

Even if players make opposite choices, there's still a pattern/connection!

### 3. 🏆 Champion Bonus (15%)
If both players end with the **same final champion word**, add +15% bonus:

```python
if same_champion:
    champion_bonus = 15
    final_tacit_value = min(100, base_tacit_value + champion_bonus)
```

**Example:**
- Base tacit value: 87%
- Same champion (赛博朋克2077): +15%
- Final tacit value: min(100, 102) = 100% ✓

## 📊 New Calculation Flow

```
1. Calculate Pearson Correlation → raw_correlation (-1 to 1)
2. Use Absolute Value → correlation = abs(raw_correlation)
3. Apply Formula:
   - numerator = 2.5 × correlation
   - denominator = 1.0 + 1.5 × correlation
   - base_tacit = (numerator / denominator) × 100
4. Check Champions:
   - If same: bonus = +15%
   - If different: bonus = 0%
5. Final Tacit Value = min(100, base_tacit + bonus)
```

## 📝 Example Calculation

### Your Game Example:

**Input:**
- Raw Correlation: -0.5752 (negative!)
- Player 1 Champion: 深圳
- Player 2 Champion: 赛博朋克2077

**Old Algorithm:**
```
Positive correlation: max(0, -0.5752) = 0.0
Numerator: 2.5 × 0.0 = 0.0
Denominator: 1.0 + 1.5 × 0.0 = 1.0
Base value: 0.0 / 1.0 = 0.0
Tacit value: 0% ❌
```

**New Algorithm:**
```
Absolute correlation: abs(-0.5752) = 0.5752
Numerator: 2.5 × 0.5752 = 1.4380
Denominator: 1.0 + 1.5 × 0.5752 = 1.8628
Base value: 1.4380 / 1.8628 = 0.7719
Base tacit: 0.7719 × 100 = 77%

Champion check:
  Player 1: 深圳
  Player 2: 赛博朋克2077
  Same? NO → Bonus = 0%

Final Tacit Value: 77% ✓
```

### Same Champion Example:

**Input:**
- Raw Correlation: 0.65
- Player 1 Champion: 赛博朋克2077
- Player 2 Champion: 赛博朋克2077

**Calculation:**
```
Absolute correlation: abs(0.65) = 0.65
Numerator: 2.5 × 0.65 = 1.625
Denominator: 1.0 + 1.5 × 0.65 = 1.975
Base value: 1.625 / 1.975 = 0.8228
Base tacit: 82%

Champion check:
  Both chose: 赛博朋克2077
  Same? YES → Bonus = +15%

Final Tacit Value: min(100, 82 + 15) = 97% ✓
```

## 🔍 What You'll See in Logs

### New Log Format:

```
================================================================================
开始计算默契值 (Starting Tacit Value Calculation)
================================================================================
Player 1: hfhdn (87ee8e2a...)
Player 2: 电饭锅 (2080644f...)
Word pool size: 10 words
Building preference matrices (10x10)...
Player 1 made 9 choices
Player 2 made 9 choices
--------------------------------------------------------------------------------
计算矩阵相关性 (Computing Matrix Correlation)
--------------------------------------------------------------------------------
Matrix 1 flattened size: 100
Matrix 2 flattened size: 100
Non-zero data points: 32
Player 1 preference values: mean=0.8438, std=0.8333
Player 2 preference values: mean=0.8438, std=0.8333
Pearson correlation coefficient: -0.5752
--------------------------------------------------------------------------------
默契值计算公式 (Tacit Value Formula):
  原始相关系数 (Raw Correlation): -0.5752
  绝对值相关系数 (Absolute Correlation): 0.5752
  分子 (Numerator): 2.5 × 0.5752 = 1.4380
  分母 (Denominator): 1.0 + 1.5 × 0.5752 = 1.8628
  基础值 (Base value): 1.4380 / 1.8628 = 0.7719
  基础默契值 (Base Tacit value): 0.7719 × 100 = 77%
--------------------------------------------------------------------------------
================================================================================
不同冠军 (Different Champions)
  Player 1 champion: 深圳
  Player 2 champion: 赛博朋克2077
================================================================================
--------------------------------------------------------------------------------
逐轮选择对比 (Round-by-Round Choice Comparison)
--------------------------------------------------------------------------------
Round 1:
  hfhdn: [蜜蜂 vs Spotify] → Spotify
  电饭锅: [哈弗 vs 悟空] → 哈弗
Round 2:
  hfhdn: [Spotify vs 包子] → Spotify
  电饭锅: [哈弗 vs 端午节] → 端午节
...
--------------------------------------------------------------------------------
Total rounds compared: 9
--------------------------------------------------------------------------------
================================================================================
最终默契值 (Final Tacit Value): 77%
================================================================================
```

### With Champion Bonus:

```
================================================================================
🏆 相同冠军奖励 (Same Champion Bonus)!
  Both players chose: 赛博朋克2077
  Bonus: +15%
================================================================================
...
================================================================================
基础默契值 (Base Tacit): 82%
冠军奖励 (Champion Bonus): +15%
最终默契值 (Final Tacit Value): 97%
================================================================================
```

## ✨ Key Improvements

1. **No More 0% for Negative Correlation**
   - Negative correlation still shows a pattern
   - -0.5752 correlation → 77% tacit value (instead of 0%)

2. **Reward Same Champion**
   - +15% bonus when both players pick the same winner
   - Encourages alignment on final choice

3. **Cleaner Logs**
   - Removed confusing "agreement rate"
   - Focus on correlation and champion match
   - Clear distinction between base value and final value

4. **Always Capped at 100%**
   - `min(100, base + bonus)` ensures valid percentage

## 🚀 Deploy

The updated file is ready at:
```
/Users/chengyixu/WeChatProjects/testchat/scripts/server0405.py
```

Upload to server and restart!

