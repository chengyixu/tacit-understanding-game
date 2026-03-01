App({
  globalData: {
    wsConnected: false,
    playerRegistered: false,
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
    // Immediate visual feedback
    wx.showToast({
      title: 'App启动中...',
      icon: 'loading',
      duration: 3000
    });
    
    // Start connection immediately
    this.connectWebSocket();
  },
  
  onShow() {
    // App returns to foreground - reconnect if needed
    console.log('App onShow - checking connection');
    if (!this.globalData.wsConnected) {
      console.log('WebSocket disconnected, reconnecting...');
      this.connectWebSocket();
    } else {
      // Send ping to ensure connection is alive
      this.sendMessage({ action: 'ping' });
    }
  },
  
  onHide() {
    // App goes to background
    console.log('App onHide - app going to background');
    // Don't close the connection, let the OS handle it
    // The server will maintain state for 5 minutes
  },

  connectWebSocket() {
    if (this.globalData.wsConnected) {
      return;
    }

    // Use domain (must be whitelisted in WeChat Mini Program console)
    const wsUrl = 'wss://www.panor.tech/moqi/ws';
    
    wx.connectSocket({
      url: wsUrl,
      success: () => {
        wx.showToast({
          title: '连接中...',
          icon: 'loading'
        });
      },
      fail: (err) => {
        wx.showToast({
          title: '连接失败',
          icon: 'none'
        });
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
      
      // Register player with server (nickname will be set later from index page)
      console.log('准备发送注册请求...');
      // If we already have a player ID, send it for reconnection
      const registerData = { action: 'register' };
      if (this.globalData.playerInfo && this.globalData.playerInfo.playerId) {
        registerData.playerId = this.globalData.playerInfo.playerId;
        console.log('Reconnecting with existing player ID:', registerData.playerId);
      }
      const registerMsg = JSON.stringify(registerData);
      console.log('注册消息:', registerMsg);
      wx.sendSocketMessage({
        data: registerMsg,
        success: () => {
          console.log('注册请求已发送成功');
        },
        fail: (err) => {
          console.error('注册请求发送失败:', err);
          console.error('失败详情:', JSON.stringify(err));
        }
      });
      
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
        
        // Handle player registration
        if (data.action === 'registered') {
          this.globalData.playerInfo = {
            playerId: data.playerId,
            nickname: data.nickname || 'Anonymous'
          };
          this.globalData.playerRegistered = true;
          console.log('玩家已注册:', this.globalData.playerInfo);
          if (this.globalData.messageCallback) {
            this.globalData.messageCallback(data);
          }
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
      this.globalData.playerRegistered = false;
      this.stopHeartbeat();
      this.scheduleReconnect();
    });

    wx.onSocketClose(() => {
      console.log('WebSocket连接关闭');
      this.globalData.wsConnected = false;
      this.globalData.playerRegistered = false;
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
    // Keep player registration including nickname
    // Nickname is maintained from index page input
    this.globalData.opponentInfo = null;
    this.globalData.isHost = false;
    this.globalData.challengeMode = false;
    this.globalData.challengeCategory = null;
    this.globalData.groupMode = false;
    this.globalData.maxPlayers = 2;
    this.globalData.pendingGameData = null;
  }
});
