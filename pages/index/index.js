const app = getApp();

Page({
  data: {
    nickname: '',
    connectionStatus: '未连接',
    testMode: false,  // AI test mode
    debugInfo: ''  // Debug information
  },

  onLoad() {
    // Direct connection attempt without relying on app.js
    this.directConnect();
    this.checkConnection();
    app.resetGameState();
  },
  
  directConnect() {
    // Try connecting directly from index page
    this.addDebug('开始连接...');
    
    // Use the working URL confirmed by testing
    const wsUrl = 'wss://www.panor.tech:3001/ws';
    this.addDebug('URL: ' + wsUrl);
    this.addDebug('连接中...');
    
    wx.connectSocket({
      url: wsUrl,
      success: (res) => {
        this.setData({ connectionStatus: '发送连接请求' });
        this.addDebug('连接请求成功: ' + JSON.stringify(res));
      },
      fail: (err) => {
        this.setData({ connectionStatus: '连接请求失败' });
        this.addDebug('连接失败: ' + JSON.stringify(err));
      },
      complete: (res) => {
        this.addDebug('Complete: ' + JSON.stringify(res));
      }
    });
    
    wx.onSocketOpen(() => {
      app.globalData.wsConnected = true;
      this.setData({ connectionStatus: '连接打开，注册中...' });
      this.addDebug('Socket opened!');
      
      // Send register message
      wx.sendSocketMessage({
        data: JSON.stringify({ action: 'register' }),
        success: () => {
          this.setData({ connectionStatus: '注册已发送' });
          this.addDebug('Register sent');
        },
        fail: (err) => {
          this.setData({ connectionStatus: '注册失败' });
          this.addDebug('Register fail: ' + JSON.stringify(err));
        }
      });
    });
    
    wx.onSocketMessage((res) => {
      this.addDebug('Message: ' + res.data);
      try {
        const data = JSON.parse(res.data);
        if (data.action === 'registered') {
          app.globalData.playerInfo = {
            playerId: data.playerId,
            nickname: data.nickname || 'Anonymous'
          };
          app.globalData.playerRegistered = true;
          this.setData({ connectionStatus: '已连接' });
          this.addDebug('Registered! ID: ' + data.playerId);
          wx.showToast({
            title: '连接成功',
            icon: 'success'
          });
        }
      } catch (e) {
        this.addDebug('Parse error: ' + e);
      }
    });
    
    wx.onSocketError((err) => {
      this.setData({ connectionStatus: '连接错误' });
      this.addDebug('Socket error: ' + JSON.stringify(err));
      wx.showToast({
        title: 'Socket错误',
        icon: 'none'
      });
    });
    
    wx.onSocketClose(() => {
      app.globalData.wsConnected = false;
      app.globalData.playerRegistered = false;
      this.setData({ connectionStatus: '连接已断开' });
      this.addDebug('Socket closed');
    });
  },

  onShow() {
    this.checkConnection();
  },

  checkConnection() {
    if (app.globalData.wsConnected && app.globalData.playerRegistered) {
      this.setData({ connectionStatus: '已连接' });
    } else {
      this.setData({ connectionStatus: '连接中...' });
      // Check multiple times as registration takes time
      let checkCount = 0;
      const checkInterval = setInterval(() => {
        checkCount++;
        if (app.globalData.wsConnected && app.globalData.playerRegistered) {
          this.setData({ connectionStatus: '已连接' });
          clearInterval(checkInterval);
        } else if (checkCount >= 10) {  // Try for 5 seconds (10 * 500ms)
          // If still not connected after 5 seconds, try reconnecting
          if (!app.globalData.wsConnected) {
            this.setData({ connectionStatus: '重新连接中...' });
            app.connectWebSocket();
            // Give it another 3 seconds
            setTimeout(() => {
              if (app.globalData.wsConnected && app.globalData.playerRegistered) {
                this.setData({ connectionStatus: '已连接' });
              } else {
                this.setData({ connectionStatus: '连接失败' });
              }
            }, 3000);
          } else if (!app.globalData.playerRegistered) {
            // WebSocket connected but not registered, send register again
            wx.sendSocketMessage({
              data: JSON.stringify({ action: 'register' }),
              fail: () => {
                this.setData({ connectionStatus: '连接失败' });
              }
            });
            setTimeout(() => {
              if (app.globalData.playerRegistered) {
                this.setData({ connectionStatus: '已连接' });
              } else {
                this.setData({ connectionStatus: '连接失败' });
              }
            }, 1000);
          }
          clearInterval(checkInterval);
        }
      }, 500);
    }
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value });
  },
  
  addDebug(msg) {
    const timestamp = new Date().toLocaleTimeString();
    const current = this.data.debugInfo;
    this.setData({
      debugInfo: current + '\n[' + timestamp + '] ' + msg
    });
  },
  
  clearDebug() {
    this.setData({ debugInfo: '' });
  },

  manualConnect() {
    // Reset and retry
    wx.closeSocket({
      success: () => {
        wx.showToast({
          title: '重置连接',
          icon: 'none'
        });
      }
    });
    
    // Reset state
    app.globalData.wsConnected = false;
    app.globalData.playerRegistered = false;
    
    // Wait a bit then reconnect
    setTimeout(() => {
      this.directConnect();
    }, 500);
  },

  createRoom() {
    if (!this.validateNickname()) return;

    // Keep the registered player ID, just update nickname
    if (app.globalData.playerRegistered && app.globalData.playerInfo) {
      app.globalData.playerInfo.nickname = this.data.nickname;
    } else {
      console.error('Player not registered with server');
      wx.showToast({
        title: '请等待连接完成',
        icon: 'none'
      });
      this.checkConnection();
      return;
    }
    
    // Store test mode preference
    app.globalData.testMode = this.data.testMode;

    wx.navigateTo({
      url: '/pages/create/create'
    });
  },
  
  toggleTestMode(e) {
    this.setData({ testMode: e.detail.value });
    console.log('Test mode:', e.detail.value ? 'ON' : 'OFF');
  },

  joinRoom() {
    if (!this.validateNickname()) return;

    // Keep the registered player ID, just update nickname
    if (app.globalData.playerRegistered && app.globalData.playerInfo) {
      app.globalData.playerInfo.nickname = this.data.nickname;
    } else {
      console.error('Player not registered with server');
      wx.showToast({
        title: '请等待连接完成',
        icon: 'none'
      });
      this.checkConnection();
      return;
    }

    wx.navigateTo({
      url: '/pages/join/join'
    });
  },

  enterChallenge() {
    if (!this.validateNickname()) return;

    // Keep the registered player ID, just update nickname
    if (app.globalData.playerRegistered && app.globalData.playerInfo) {
      app.globalData.playerInfo.nickname = this.data.nickname;
    } else {
      console.error('Player not registered with server');
      wx.showToast({
        title: '请等待连接完成',
        icon: 'none'
      });
      this.checkConnection();
      return;
    }
    app.globalData.challengeMode = true;

    wx.navigateTo({
      url: '/pages/challenge/challenge'
    });
  },

  validateNickname() {
    if (!this.data.nickname) {
      wx.showToast({
        title: '请输入昵称',
        icon: 'none'
      });
      return false;
    }
    if (this.data.nickname.length > 10) {
      wx.showToast({
        title: '昵称最多10个字符',
        icon: 'none'
      });
      return false;
    }
    return true;
  }
});