# WeChat Mini Program Domain Whitelist Setup

## The Problem
WeChat blocks WebSocket connections to domains not in the whitelist, even with `urlCheck: false`.

Error: `"createSocketTask:fail wss url not in domain list"`

## Solution - Add Domain to Whitelist

### Option 1: WeChat Developer Console (Recommended)
1. Go to [WeChat Mini Program Console](https://mp.weixin.qq.com/)
2. Login with your developer account
3. Select your mini program (AppID: `wxe66b1b9d4f62a1c2`)
4. Navigate to: **开发 → 开发设置 → 服务器域名**
5. Click **修改** (Modify)
6. Add to **socket合法域名** (WebSocket Domain):
   ```
   wss://www.panor.tech
   ```
   OR if domain doesn't work, try:
   ```
   wss://47.117.176.214
   ```
7. Save and wait 5 minutes for changes to take effect

### Option 2: Development Mode Bypass
In WeChat Developer Tools:
1. Click **详情** (Details) in the top menu
2. Under **项目设置** (Project Settings)
3. Check ✅ **不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书**
4. This disables ALL domain checking (development only!)

### Option 3: Local Testing Mode
For testing without domain restrictions:
1. In WeChat Developer Tools
2. Click **预览** → **自定义编译条件**
3. Add compilation mode: **开发版**
4. This allows testing without domain restrictions

## After Whitelisting

Once domain is whitelisted:
1. Change back to domain URL in `app.js` and `pages/index/index.js`:
   ```javascript
   const wsUrl = 'wss://www.panor.tech:3001/ws';
   ```

2. Clear WeChat cache:
   - Developer Tools: **清缓存 → 清除全部缓存**
   
3. Rebuild project:
   - Developer Tools: **编译** (Cmd+B)

## Server Requirements

Your server already meets these requirements ✅:
- Valid SSL certificate for www.panor.tech
- Port 3001 is open
- WebSocket server is running

## Verification

After setup, the debug panel should show:
```
[时间] 开始连接...
[时间] URL: wss://www.panor.tech:3001/ws
[时间] 连接请求成功
[时间] Socket opened!
[时间] Register sent
[时间] Registered! ID: xxx
```

## Notes

- Domain changes can take 5-30 minutes to propagate
- IP addresses (47.117.176.214) may not work in production
- Always use domain names for production deployment
- The domain must match SSL certificate CN (www.panor.tech ✅)