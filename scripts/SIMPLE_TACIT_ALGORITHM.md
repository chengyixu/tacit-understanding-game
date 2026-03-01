# 简化的默契值算法 (Simplified Tacit Value Algorithm)

## 🎯 Super Simple Formula

```
Base Tacit Value = |correlation| × 100
Final Tacit Value = min(100, Base + Champion Bonus)
```

That's it! No complex formulas, just direct correlation to percentage.

## 📊 Examples

### Example 1: Your Game
```
Raw Correlation: -0.5752
Absolute Value: |-0.5752| = 0.5752
Base Tacit: 0.5752 × 100 = 57.52% ≈ 58%

Champions:
  Player 1: 深圳
  Player 2: 赛博朋克2077
  Different → Bonus = 0%

Final Tacit Value: 58% ✓
```

### Example 2: Same Champion
```
Raw Correlation: 0.65
Absolute Value: |0.65| = 0.65
Base Tacit: 0.65 × 100 = 65%

Champions:
  Player 1: 赛博朋克2077
  Player 2: 赛博朋克2077
  Same → Bonus = +15%

Final Tacit Value: min(100, 65 + 15) = 80% ✓
```

### Example 3: Perfect Correlation
```
Raw Correlation: 1.0
Absolute Value: |1.0| = 1.0
Base Tacit: 1.0 × 100 = 100%

Champions: Different
Final Tacit Value: 100% ✓
```

### Example 4: Perfect Negative Correlation
```
Raw Correlation: -1.0
Absolute Value: |-1.0| = 1.0
Base Tacit: 1.0 × 100 = 100%

Champions: Same
Bonus: +15%

Final Tacit Value: min(100, 100 + 15) = 100% ✓
```

## 📈 Correlation Scale

| Correlation | Base Tacit | With +15% Bonus |
|-------------|------------|-----------------|
| ±1.0 | 100% | 100% (capped) |
| ±0.9 | 90% | 100% (capped) |
| ±0.8 | 80% | 95% |
| ±0.7 | 70% | 85% |
| ±0.6 | 60% | 75% |
| ±0.5752 | 58% | 73% |
| ±0.5 | 50% | 65% |
| ±0.4 | 40% | 55% |
| ±0.3 | 30% | 45% |
| ±0.2 | 20% | 35% |
| ±0.1 | 10% | 25% |
| 0.0 | 0% | 15% |

## 🔍 What You'll See in Logs

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
  基础默契值 (Base Tacit value): 0.5752 × 100 = 58%
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
...
--------------------------------------------------------------------------------
Total rounds compared: 9
--------------------------------------------------------------------------------
================================================================================
最终默契值 (Final Tacit Value): 58%
================================================================================
```

## ✨ Key Points

1. **Direct Conversion**: Correlation directly becomes percentage
2. **Absolute Value**: Negative correlation treated same as positive
3. **Champion Bonus**: +15% if both pick same winner
4. **Always Capped**: Maximum 100%

## 🚀 Benefits

- **Simple**: Easy to understand and explain
- **Intuitive**: 0.5 correlation = 50% tacit makes sense
- **Fair**: Negative correlation still counts as connection
- **Rewarding**: Same champion gets recognition

## 📁 Ready to Deploy

File updated and ready at:
```
/Users/chengyixu/WeCatchProjects/testchat/scripts/server0405.py
```

Upload and restart your server!

