# AI Mode Test Guide

## Fixed Issues
1. **Room number display**: Room number now shows immediately on create page
2. **AI player addition**: Server now properly adds AI player on reconnection
3. **TestMode persistence**: Test mode value properly saved to globalData

## Test Steps

### 1. Clear Previous State
- Force close the mini program completely
- Re-open WeChat Developer Tools
- Click "编译" to recompile

### 2. Test Flow
1. **Index Page**:
   - Enter nickname (e.g., "测试用户")
   - Toggle "AI测试模式" ON
   - Click "创建房间"

2. **Create Page**:
   - Room number should display immediately (6 digits)
   - Keep default "双人对战" selected
   - Click "进入等待室"

3. **Waiting Room**:
   - You should see yourself listed
   - Within 1-2 seconds, "AI测试员" should appear
   - Game should auto-start after AI joins

### 3. Check Console Logs
Look for these key logs:
- `[CREATE] Creating room with testMode: true`
- `[CREATE] Sending message: {... testMode: true ...}`
- `[WAITING] testMode value: true`
- `[WAITING] Host reconnecting with testMode: true`

### 4. Server Logs
On server (47.117.176.214), check `/moqiyouxi_backend/server.log`:
```bash
tail -f /moqiyouxi_backend/server.log | grep -E "testMode|AI|ai_"
```

Should see:
- `Reconnection - testMode: True`
- `AI player ai_XXXX added to room XXXXXX`

## Troubleshooting

If AI doesn't appear:
1. Check browser console for errors
2. Verify testMode is true in logs
3. Check server is running: `ps aux | grep server0405.py`
4. Check server logs for errors

## Key Code Changes

### 1. Index.js
```javascript
toggleTestMode(e) {
  const testMode = e.detail.value;
  this.setData({ testMode: testMode });
  app.globalData.testMode = testMode;  // CRITICAL: Save to global
}
```

### 2. Server Reconnection Logic
```python
# Now checks testMode on reconnection and adds AI if missing
if test_mode:
    has_ai = any(pid.startswith('ai_') for pid in room.players)
    if not has_ai:
        # Add AI player
```

## Current Status
- Server deployed: PID 1558511
- Running on: wss://www.panor.tech:3001/ws
- All fixes applied and tested