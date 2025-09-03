const app = getApp();

Page({
  data: {
    roomId: '',
    isJoining: false
  },

  onLoad() {
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onShow() {
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onUnload() {
    app.clearMessageCallback();
  },

  onRoomIdInput(e) {
    this.setData({ roomId: e.detail.value });
  },

  joinRoom() {
    if (!this.validateRoomId()) return;
    
    if (this.data.isJoining) return;
    
    this.setData({ isJoining: true });
    
    app.sendMessage({
      action: 'join_room',
      roomId: this.data.roomId,
      playerInfo: app.globalData.playerInfo
    });
    
    app.globalData.roomId = this.data.roomId;
    app.globalData.isHost = false;
  },

  validateRoomId() {
    if (!this.data.roomId) {
      wx.showToast({
        title: '请输入房间号',
        icon: 'none'
      });
      return false;
    }
    
    if (!/^\d{6}$/.test(this.data.roomId)) {
      wx.showToast({
        title: '房间号为6位数字',
        icon: 'none'
      });
      return false;
    }
    
    return true;
  },

  handleMessage(data) {
    console.log('Join page received:', data);
    
    if (data.action === 'joined_room') {
      this.setData({ isJoining: false });
      wx.redirectTo({
        url: '/pages/waiting/waiting'
      });
    } else if (data.action === 'error') {
      this.setData({ isJoining: false });
      wx.showToast({
        title: data.message || '加入失败',
        icon: 'none'
      });
    }
  },

  backToHome() {
    wx.redirectTo({
      url: '/pages/index/index'
    });
  }
});