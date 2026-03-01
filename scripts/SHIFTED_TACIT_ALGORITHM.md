# 偏移默契值算法 (Shifted Tacit Value Algorithm)

## 🎯 New Formula with +0.7 Shift

```python
Adjusted Correlation = Raw Correlation + 0.7
Clamped Correlation = min(1.0, max(0.0, Adjusted Correlation))
Base Tacit Value = Clamped Correlation × 100
Final Tacit Value = min(100, Base + Champion Bonus)
```

## 🤔 Why Add 0.7?

**Problem with absolute value:**
- Correlation = -0.8 → |−0.8| = 0.8 → 80% tacit ❌
- Correlation = +0.8 → |+0.8| = 0.8 → 80% tacit ❌
- **Both get same score, but opposite patterns shouldn't be equally good!**

**Solution with +0.7 shift:**
- Correlation = -0.8 → -0.8 + 0.7 = -0.1 → 0% tacit ✓ (bad)
- Correlation = +0.8 → +0.8 + 0.7 = 1.5 → 100% tacit ✓ (capped, excellent)
- **Positive correlations rewarded, negative correlations penalized!**

## 📊 Correlation Scale Comparison

| Raw Correlation | Old (Absolute) | New (+0.7 Shift) |
|-----------------|----------------|------------------|
| -1.0 (opposite) | 100% | 0% (clamped) |
| -0.8 | 80% | 0% (clamped) |
| -0.7 | 70% | 0% |
| -0.5752 | 58% | **12%** ✓ |
| -0.5 | 50% | 20% |
| -0.3 | 30% | 40% |
| 0.0 (random) | 0% | **70%** |
| +0.2 | 20% | 90% |
| +0.3 | 30% | 100% (capped) |
| +0.5 | 50% | 100% (capped) |
| +0.5752 | 58% | **100%** ✓ |
| +0.8 | 80% | 100% (capped) |
| +1.0 (perfect) | 100% | 100% (capped) |

## 📈 Key Ranges

### Negative Correlation (opposite patterns)
```
-1.0 to -0.7  → 0% base tacit (really bad)
-0.7 to -0.5  → 0-20% base tacit (poor)
-0.5 to -0.3  → 20-40% base tacit (below average)
```

### Low Positive Correlation (some randomness)
```
-0.3 to 0.0   → 40-70% base tacit (average)
0.0 to +0.3   → 70-100% base tacit (good to excellent)
```

### High Positive Correlation (strong agreement)
```
+0.3 to +1.0  → 100% base tacit (excellent, capped)
```

## 💡 Examples

### Example 1: Your Previous Game
```
Raw Correlation: -0.5752
Adjusted: -0.5752 + 0.7 = 0.1248
Clamped: 0.1248 (within 0-1 range)
Base Tacit: 0.1248 × 100 = 12%

Champions: Different
Bonus: 0%
Final Tacit Value: 12% ✓

OLD algorithm would give: 58% ❌
NEW algorithm gives: 12% ✓ (more accurate for negative correlation)
```

### Example 2: Good Positive Correlation
```
Raw Correlation: +0.5752
Adjusted: 0.5752 + 0.7 = 1.2752
Clamped: min(1.0, 1.2752) = 1.0
Base Tacit: 1.0 × 100 = 100%

Champions: Same
Bonus: +15%
Final Tacit Value: min(100, 115) = 100% ✓
```

### Example 3: Perfect Negative (Opposite)
```
Raw Correlation: -1.0
Adjusted: -1.0 + 0.7 = -0.3
Clamped: max(0, -0.3) = 0.0
Base Tacit: 0.0 × 100 = 0%

Champions: Different
Bonus: 0%
Final Tacit Value: 0% ✓

This is good! Completely opposite choices = 0% tacit
```

### Example 4: No Correlation (Random)
```
Raw Correlation: 0.0
Adjusted: 0.0 + 0.7 = 0.7
Clamped: 0.7
Base Tacit: 0.7 × 100 = 70%

Champions: Different
Bonus: 0%
Final Tacit Value: 70%

Random choices still get 70% base (neutral)
```

### Example 5: Moderate Positive
```
Raw Correlation: +0.4
Adjusted: 0.4 + 0.7 = 1.1
Clamped: min(1.0, 1.1) = 1.0
Base Tacit: 100%

Champions: Same
Bonus: +15%
Final Tacit Value: 100% (capped)
```

## 🔍 Log Output Example

```
================================================================================
开始计算默契值 (Starting Tacit Value Calculation)
================================================================================
Player 1: dbdb (f6c893c1...)
Player 2: 电饭锅 (2f09d7a7...)
Word pool size: 10 words
Building preference matrices (10x10)...
--------------------------------------------------------------------------------
计算矩阵相关性 (Computing Matrix Correlation)
--------------------------------------------------------------------------------
Non-zero data points: 32
Player 1 preference values: mean=0.8438, std=0.8333
Player 2 preference values: mean=0.8438, std=0.8333
Pearson correlation coefficient: -0.5752
--------------------------------------------------------------------------------
默契值计算公式 (Tacit Value Formula):
  原始相关系数 (Raw Correlation): -0.5752
  调整后相关系数 (Adjusted): -0.5752 + 0.7 = 0.1248
  限制范围 (Clamped [0,1]): 0.1248
  基础默契值 (Base Tacit value): 0.1248 × 100 = 12%
--------------------------------------------------------------------------------
================================================================================
不同冠军 (Different Champions)
  Player 1 champion: 深圳
  Player 2 champion: 赛博朋克2077
================================================================================
--------------------------------------------------------------------------------
Total rounds compared: 9
--------------------------------------------------------------------------------
================================================================================
最终默契值 (Final Tacit Value): 12%
================================================================================
```

## ✨ Benefits

1. **Penalizes Negative Correlation**: Opposite patterns get low scores
2. **Rewards Positive Correlation**: Good agreement gets high scores (often 100%)
3. **Fair for Random**: Zero correlation = 70% (neutral, not great but not terrible)
4. **Prevents Gaming**: Can't get high score by being consistently opposite
5. **Champion Bonus Still Works**: +15% for same winner

## 📊 Distribution

With this algorithm:
- **0-30%**: Poor tacit (negative correlations)
- **30-70%**: Average tacit (low/zero correlation)
- **70-100%**: Good tacit (positive correlations)
- **100% (with bonus)**: Excellent tacit (positive + same champion)

## 🚀 Ready to Deploy

File updated at:
```
/Users/chengyixu/WeChatProjects/testchat/scripts/server0405.py
```

Upload and restart! Now the algorithm properly distinguishes between positive and negative correlations! ✅

