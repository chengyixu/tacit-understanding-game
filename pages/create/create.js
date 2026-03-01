const app = getApp();

Page({
  data: {
    roomId: '',
    isCreating: false,
    groupMode: false,
    maxPlayers: 2  // Changed default to 2 for 2-player mode
  },

  onLoad() {
    app.setMessageCallback(this.handleMessage.bind(this));
    // Create room immediately so room number shows
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
    
    // Don't create room yet - wait for user to click enter waiting room
    // this.createRoom();
  },
  
  selectPlayerCount(e) {
    const count = parseInt(e.currentTarget.dataset.count);
    this.setData({ maxPlayers: count });
    
    // Don't create room yet - wait for user to click enter waiting room
    // this.createRoom();
  },

  createRoom() {
    if (this.data.isCreating) return;
    
    this.setData({ isCreating: true });
    
    const roomId = this.data.roomId || this.generateRoomId();
    
    console.log('[CREATE] app.globalData:', app.globalData);
    
    const message = {
      action: 'createRoom',
      roomId: roomId,
      playerInfo: app.globalData.playerInfo,
      challengeMode: app.globalData.themeMode || false,  // Use themeMode to indicate category-specific mode
      challengeCategory: app.globalData.challengeCategory || null,
      groupMode: this.data.groupMode,
      maxPlayers: this.data.maxPlayers
    };
    
    console.log('[CREATE] Sending message:', message);
    app.sendMessage(message);

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
          app.globalData.fromCreatePage = true;  // Mark that we're coming from create page
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
    
    app.globalData.fromCreatePage = true;  // Mark that we're coming from create page
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