const app = getApp();

Page({
  data: {
    nickname: '',
    connectionStatus: '未连接',
    testMode: false  // AI test mode
  },

  onLoad() {
    this.checkConnection();
    app.resetGameState();
  },

  onShow() {
    this.checkConnection();
  },

  checkConnection() {
    if (app.globalData.wsConnected) {
      this.setData({ connectionStatus: '已连接' });
    } else {
      this.setData({ connectionStatus: '连接中...' });
      setTimeout(() => {
        if (app.globalData.wsConnected) {
          this.setData({ connectionStatus: '已连接' });
        }
      }, 1000);
    }
  },

  onNicknameInput(e) {
    this.setData({ nickname: e.detail.value });
  },

  createRoom() {
    if (!this.validateNickname()) return;

    app.globalData.playerInfo = {
      nickname: this.data.nickname,
      playerId: Date.now().toString()
    };
    
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

    app.globalData.playerInfo = {
      nickname: this.data.nickname,
      playerId: Date.now().toString()
    };

    wx.navigateTo({
      url: '/pages/join/join'
    });
  },

  enterChallenge() {
    if (!this.validateNickname()) return;

    app.globalData.playerInfo = {
      nickname: this.data.nickname,
      playerId: Date.now().toString()
    };
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