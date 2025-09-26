// Test WebSocket connectivity
Page({
  onLoad() {
    // Test 1: Direct IP connection
    this.testConnection('wss://47.117.176.214:3001/ws', 'IP直连');
    
    // Test 2: Domain connection after 3 seconds
    setTimeout(() => {
      this.testConnection('wss://www.panor.tech:3001/ws', '域名连接');
    }, 3000);
  },
  
  testConnection(url, name) {
    wx.showModal({
      title: '测试 ' + name,
      content: '尝试连接: ' + url,
      showCancel: false
    });
    
    wx.connectSocket({
      url: url,
      success: (res) => {
        wx.showModal({
          title: name + ' - 成功',
          content: '连接请求已发送',
          showCancel: false
        });
      },
      fail: (err) => {
        wx.showModal({
          title: name + ' - 失败',
          content: JSON.stringify(err),
          showCancel: false
        });
      }
    });
  }
});