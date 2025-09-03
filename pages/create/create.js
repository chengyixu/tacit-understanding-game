const app = getApp();

Page({
  data: {
    roomId: '',
    isCreating: false
  },

  onLoad() {
    this.createRoom();
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onShow() {
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onUnload() {
    app.clearMessageCallback();
  },

  createRoom() {
    if (this.data.isCreating) return;
    
    this.setData({ isCreating: true });
    
    const roomId = this.generateRoomId();
    
    app.sendMessage({
      action: 'create_room',
      roomId: roomId,
      playerInfo: app.globalData.playerInfo,
      challengeMode: app.globalData.challengeMode || false,
      challengeCategory: app.globalData.challengeCategory || null,
      testMode: app.globalData.testMode || false  // Pass test mode flag
    });

    this.setData({ roomId: roomId });
    app.globalData.roomId = roomId;
    app.globalData.isHost = true;
  },

  generateRoomId() {
    return Math.floor(100000 + Math.random() * 900000).toString();
  },

  handleMessage(data) {
    console.log('Create page received:', data);
    
    if (data.action === 'room_created') {
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
      wx.showToast({
        title: '房间创建中...',
        icon: 'none'
      });
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