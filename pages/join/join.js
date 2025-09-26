const app = getApp();

Page({
  data: {
    roomId: '',
    isJoining: false
  },

  onLoad() {
    console.log('Join page onLoad - setting message callback');
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onShow() {
    console.log('Join page onShow - resetting message callback');
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
    
    const joinData = {
      action: 'joinRoom',
      roomId: this.data.roomId,
      playerInfo: app.globalData.playerInfo
    };
    
    console.log('Sending join request:', joinData);
    wx.showToast({
      title: `加入房间 ${this.data.roomId}...`,
      icon: 'loading',
      duration: 10000
    });
    
    const sent = app.sendMessage(joinData);
    console.log('Message sent result:', sent);
    
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
    
    // Add visible debug info
    wx.showToast({
      title: `收到: ${data.action}`,
      icon: 'none',
      duration: 2000
    });
    
    if (data.action === 'joinedRoom') {
      console.log('Received joinedRoom, redirecting...');
      this.setData({ isJoining: false });
      wx.redirectTo({
        url: '/pages/waiting/waiting'
      });
    } else if (data.action === 'error') {
      console.log('Received error:', data.message);
      this.setData({ isJoining: false });
      wx.showToast({
        title: data.message || '加入失败',
        icon: 'none'
      });
    } else {
      console.log('Unexpected action:', data.action);
    }
  },

  backToHome() {
    wx.redirectTo({
      url: '/pages/index/index'
    });
  }
});