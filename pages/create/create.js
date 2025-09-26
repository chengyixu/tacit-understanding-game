const app = getApp();

Page({
  data: {
    roomId: '',
    isCreating: false,
    groupMode: false,
    maxPlayers: 3
  },

  onLoad() {
    app.setMessageCallback(this.handleMessage.bind(this));
    // Create room with default settings (2-player mode)
    this.createRoom();
  },

  onShow() {
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onUnload() {
    app.clearMessageCallback();
  },

  toggleGroupMode(e) {
    const mode = e.currentTarget.dataset.mode === 'true';
    this.setData({ 
      groupMode: mode,
      maxPlayers: mode ? 3 : 2
    });
    
    // Re-create room with new settings
    this.createRoom();
  },
  
  selectPlayerCount(e) {
    const count = parseInt(e.currentTarget.dataset.count);
    this.setData({ maxPlayers: count });
    
    // Re-create room with new player count
    this.createRoom();
  },

  createRoom() {
    if (this.data.isCreating) return;
    
    this.setData({ isCreating: true });
    
    const roomId = this.data.roomId || this.generateRoomId();
    
    app.sendMessage({
      action: 'createRoom',
      roomId: roomId,
      playerInfo: app.globalData.playerInfo,
      challengeMode: app.globalData.challengeMode || false,
      challengeCategory: app.globalData.challengeCategory || null,
      testMode: app.globalData.testMode || false,  // Pass test mode flag
      groupMode: this.data.groupMode,
      maxPlayers: this.data.maxPlayers
    });

    this.setData({ roomId: roomId });
    app.globalData.roomId = roomId;
    app.globalData.isHost = true;
    app.globalData.groupMode = this.data.groupMode;
    app.globalData.maxPlayers = this.data.maxPlayers;
  },

  generateRoomId() {
    return Math.floor(100000 + Math.random() * 900000).toString();
  },

  handleMessage(data) {
    console.log('Create page received:', data);
    
    if (data.action === 'roomCreated') {
      this.setData({ isCreating: false });
      wx.showToast({
        title: '房间创建成功',
        icon: 'success'
      });
    } else if (data.action === 'error') {
      this.setData({ isCreating: false });
      wx.showToast({
        title: data.message || '创建失败',
        icon: 'none'
      });
    }
  },

  copyRoomId() {
    wx.setClipboardData({
      data: this.data.roomId,
      success: () => {
        wx.showToast({
          title: '房间号已复制',
          icon: 'success'
        });
      }
    });
  },

  enterWaitingRoom() {
    if (!this.data.roomId) {
      // Create room first if not created yet
      this.createRoom();
      // Wait a bit for room creation
      setTimeout(() => {
        if (this.data.roomId) {
          wx.redirectTo({
            url: '/pages/waiting/waiting'
          });
        } else {
          wx.showToast({
            title: '房间创建失败',
            icon: 'none'
          });
        }
      }, 500);
      return;
    }
    
    wx.redirectTo({
      url: '/pages/waiting/waiting'
    });
  },

  backToHome() {
    wx.redirectTo({
      url: '/pages/index/index'
    });
  }
});