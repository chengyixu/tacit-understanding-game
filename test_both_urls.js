// Test file to check both domain and IP connections
const app = getApp();

Page({
  data: {
    domainStatus: '未测试',
    ipStatus: '未测试',
    logs: []
  },

  onLoad() {
    this.addLog('Page loaded');
  },

  testDomain() {
    this.addLog('Testing domain: wss://www.panor.tech:3001/ws');
    this.testConnection('wss://www.panor.tech:3001/ws', 'domainStatus');
  },

  testIP() {
    this.addLog('Testing IP: wss://47.117.176.214:3001/ws');
    this.testConnection('wss://47.117.176.214:3001/ws', 'ipStatus');
  },

  testConnection(url, statusKey) {
    let ws = null;
    
    this.setData({ [statusKey]: '连接中...' });
    
    wx.connectSocket({
      url: url,
      success: (res) => {
        this.addLog(`✓ Connect request sent to ${url}`);
      },
      fail: (err) => {
        this.addLog(`✗ Failed to connect to ${url}: ${JSON.stringify(err)}`);
        this.setData({ [statusKey]: '连接失败' });
      }
    });

    wx.onSocketOpen(() => {
      this.addLog(`✓ WebSocket opened for ${url}`);
      this.setData({ [statusKey]: '已连接' });
      
      // Send test message
      wx.sendSocketMessage({
        data: JSON.stringify({ action: 'register' }),
        success: () => {
          this.addLog('✓ Register message sent');
        },
        fail: (err) => {
          this.addLog(`✗ Failed to send register: ${JSON.stringify(err)}`);
        }
      });
    });

    wx.onSocketMessage((res) => {
      this.addLog(`← Received: ${res.data}`);
    });

    wx.onSocketError((err) => {
      this.addLog(`✗ Socket error: ${JSON.stringify(err)}`);
      this.setData({ [statusKey]: '错误' });
    });

    wx.onSocketClose(() => {
      this.addLog('WebSocket closed');
      this.setData({ [statusKey]: '已关闭' });
    });
  },

  addLog(message) {
    const timestamp = new Date().toLocaleTimeString();
    const logs = this.data.logs;
    logs.push(`[${timestamp}] ${message}`);
    this.setData({ logs });
  },

  clearLogs() {
    this.setData({ logs: [] });
  }
});