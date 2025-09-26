Page({
  data: {
    result: 'Not tested',
    log: ''
  },

  test1() {
    this.testUrl('wss://www.panor.tech:3001/ws');
  },

  test2() {
    this.testUrl('wss://panor.tech:3001/ws');
  },

  test3() {
    this.testUrl('wss://47.117.176.214:3001/ws');
  },

  testUrl(url) {
    this.addLog(`\n===== Testing: ${url} =====`);
    this.setData({ result: 'Testing...' });
    
    // Close any existing connection
    wx.closeSocket({
      complete: () => {
        this.addLog('Closed existing socket (if any)');
      }
    });
    
    // Wait a bit then connect
    setTimeout(() => {
      wx.connectSocket({
        url: url,
        success: (res) => {
          this.addLog(`✓ connectSocket success: ${JSON.stringify(res)}`);
          this.setData({ result: 'Connect request sent' });
        },
        fail: (err) => {
          this.addLog(`✗ connectSocket failed: ${JSON.stringify(err)}`);
          this.setData({ result: `Failed: ${err.errMsg}` });
        },
        complete: (res) => {
          this.addLog(`Complete: ${JSON.stringify(res)}`);
        }
      });
      
      wx.onSocketOpen(() => {
        this.addLog('✓✓ Socket OPENED!');
        this.setData({ result: '✓ Connected!' });
        
        // Try sending a message
        wx.sendSocketMessage({
          data: JSON.stringify({ action: 'register' }),
          success: () => {
            this.addLog('✓ Register sent');
          },
          fail: (err) => {
            this.addLog(`✗ Send failed: ${JSON.stringify(err)}`);
          }
        });
      });
      
      wx.onSocketMessage((res) => {
        this.addLog(`← Message: ${res.data}`);
      });
      
      wx.onSocketError((err) => {
        this.addLog(`✗✗ Socket ERROR: ${JSON.stringify(err)}`);
        this.setData({ result: `Error: ${err.errMsg}` });
      });
      
      wx.onSocketClose(() => {
        this.addLog('Socket closed');
      });
    }, 500);
  },

  addLog(msg) {
    const time = new Date().toLocaleTimeString();
    const log = this.data.log + `\n[${time}] ${msg}`;
    this.setData({ log });
  },

  clearLog() {
    this.setData({ 
      log: '',
      result: 'Cleared'
    });
  },

  onLoad() {
    this.addLog('Test page loaded');
    this.addLog('Ready to test different URLs');
  }
});