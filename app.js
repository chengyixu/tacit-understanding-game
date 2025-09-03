App({
  globalData: {
    wsConnected: false,
    reconnectTimer: null,
    heartbeatTimer: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 10,
    messageCallback: null,
    roomId: null,
    playerInfo: null,
    opponentInfo: null,
    isHost: false,
    challengeMode: false,
    challengeCategory: null
  },

  onLaunch() {
    this.connectWebSocket();
  },

  connectWebSocket() {
    if (this.globalData.wsConnected) {
      return;
    }

    wx.connectSocket({
      url: 'wss://www.aiconnector.cn:3000/ws',
      success: () => {
        console.log('WebSocket连接请求发送成功');
      },
      fail: (err) => {
        console.error('WebSocket连接请求失败:', err);
        this.scheduleReconnect();
      }
    });

    wx.onSocketOpen(() => {
      console.log('WebSocket连接已打开');
      this.globalData.wsConnected = true;
      this.globalData.reconnectAttempts = 0;
      
      if (this.globalData.reconnectTimer) {
        clearTimeout(this.globalData.reconnectTimer);
        this.globalData.reconnectTimer = null;
      }
      
      // Send ping to keep connection alive
      this.startHeartbeat();
    });

    wx.onSocketMessage((res) => {
      try {
        const data = JSON.parse(res.data);
        console.log('收到消息:', data);
        
        if (data.action === 'pong') {
          // Heartbeat response
          return;
        }
        
        if (this.globalData.messageCallback) {
          this.globalData.messageCallback(data);
        }
      } catch (error) {
        console.error('解析消息失败:', error);
      }
    });

    wx.onSocketError((err) => {
      console.error('WebSocket错误:', err);
      this.globalData.wsConnected = false;
      this.stopHeartbeat();
    });

    wx.onSocketClose(() => {
      console.log('WebSocket连接关闭');
      this.globalData.wsConnected = false;
      this.stopHeartbeat();
      this.scheduleReconnect();
    });
  },
  
  startHeartbeat() {
    this.stopHeartbeat();
    this.globalData.heartbeatTimer = setInterval(() => {
      if (this.globalData.wsConnected) {
        this.sendMessage({ action: 'ping' });
      }
    }, 30000); // Send ping every 30 seconds
  },
  
  stopHeartbeat() {
    if (this.globalData.heartbeatTimer) {
      clearInterval(this.globalData.heartbeatTimer);
      this.globalData.heartbeatTimer = null;
    }
  },

  scheduleReconnect() {
    if (this.globalData.reconnectAttempts >= this.globalData.maxReconnectAttempts) {
      console.error('达到最大重连次数，停止重连');
      wx.showToast({
        title: '连接失败，请检查网络',
        icon: 'none'
      });
      return;
    }

    if (this.globalData.reconnectTimer) {
      return;
    }

    this.globalData.reconnectAttempts++;
    const delay = Math.min(3000 * this.globalData.reconnectAttempts, 30000);
    
    console.log(`将在${delay/1000}秒后重连，第${this.globalData.reconnectAttempts}次尝试`);
    
    this.globalData.reconnectTimer = setTimeout(() => {
      this.globalData.reconnectTimer = null;
      this.connectWebSocket();
    }, delay);
  },

  sendMessage(data) {
    if (!this.globalData.wsConnected) {
      console.error('WebSocket未连接');
      wx.showToast({
        title: '连接中断，请重试',
        icon: 'none'
      });
      this.connectWebSocket();
      return false;
    }

    wx.sendSocketMessage({
      data: JSON.stringify(data),
      success: () => {
        console.log('消息发送成功:', data);
      },
      fail: (err) => {
        console.error('消息发送失败:', err);
        wx.showToast({
          title: '发送失败，请重试',
          icon: 'none'
        });
      }
    });
    return true;
  },

  setMessageCallback(callback) {
    this.globalData.messageCallback = callback;
  },

  clearMessageCallback() {
    this.globalData.messageCallback = null;
  },

  resetGameState() {
    this.globalData.roomId = null;
    this.globalData.playerInfo = null;
    this.globalData.opponentInfo = null;
    this.globalData.isHost = false;
    this.globalData.challengeMode = false;
    this.globalData.challengeCategory = null;
  }
});