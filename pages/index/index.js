const app = getApp();

Page({
  data: {
    nickname: '',
    connectionStatus: '未连接'
  },

  onLoad() {
    app.resetGameState();
    this.initializeSocketHandlers();
    this.checkConnection();
  },

  initializeSocketHandlers() {
    app.setMessageCallback(this.handleSocketMessage.bind(this));

    if (!app.globalData.wsConnected) {
      app.connectWebSocket();
    }
  },

  handleSocketMessage(data) {
    if (data.action === 'registered') {
      this.setData({ connectionStatus: '已连接' });
      wx.showToast({
        title: '连接成功',
        icon: 'success'
      });
    }
  },

  onShow() {
    this.initializeSocketHandlers();
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

  createRoom() {
    if (!this.validateNickname()) return;

    // Keep the registered player ID, just update nickname
    if (app.globalData.playerRegistered && app.globalData.playerInfo) {
      app.globalData.playerInfo.nickname = this.data.nickname;
      
      // Update nickname on server
      app.sendMessage({
        action: 'updateNickname',
        nickname: this.data.nickname
      });
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
      url: '/pages/create/create'
    });
  },

  joinRoom() {
    if (!this.validateNickname()) return;

    // Keep the registered player ID, just update nickname
    if (app.globalData.playerRegistered && app.globalData.playerInfo) {
      app.globalData.playerInfo.nickname = this.data.nickname;
      
      // Update nickname on server
      app.sendMessage({
        action: 'updateNickname',
        nickname: this.data.nickname
      });
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

  enterThemeSelection() {
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
    
    // Set theme mode flag
    app.globalData.themeMode = true;

    wx.navigateTo({
      url: '/pages/theme/theme'
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
