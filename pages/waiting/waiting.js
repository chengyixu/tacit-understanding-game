const app = getApp();

Page({
  data: {
    roomId: '',
    playerInfo: null,
    opponentInfo: null,
    isHost: false,
    isReady: false,
    countdown: 3
  },

  onLoad() {
    if (!app.globalData.roomId || !app.globalData.playerInfo) {
      wx.redirectTo({ url: '/pages/index/index' });
      return;
    }

    this.setData({
      roomId: app.globalData.roomId,
      playerInfo: app.globalData.playerInfo,
      isHost: app.globalData.isHost
    });

    app.setMessageCallback(this.handleMessage.bind(this));
    
    // Reconnect to room when page loads
    this.reconnectToRoom();
  },

  onShow() {
    app.setMessageCallback(this.handleMessage.bind(this));
    
    // Also reconnect when page shows (returning from background)
    if (app.globalData.roomId && app.globalData.playerInfo) {
      this.reconnectToRoom();
    }
  },
  
  reconnectToRoom() {
    console.log('Reconnecting to room:', app.globalData.roomId);
    
    // If host, try to create/reconnect to room
    if (this.data.isHost) {
      app.sendMessage({
        action: 'create_room',
        roomId: app.globalData.roomId,
        playerInfo: app.globalData.playerInfo,
        challengeMode: app.globalData.challengeMode || false,
        challengeCategory: app.globalData.challengeCategory || null,
        testMode: app.globalData.testMode || false
      });
    } else {
      // If guest, rejoin the room
      app.sendMessage({
        action: 'join_room',
        roomId: app.globalData.roomId,
        playerInfo: app.globalData.playerInfo
      });
    }
  },

  onUnload() {
    app.clearMessageCallback();
  },

  handleMessage(data) {
    console.log('Waiting page received:', data);
    console.log('Current state - isHost:', this.data.isHost, 'opponentInfo:', this.data.opponentInfo);
    
    // Handle reconnection responses
    if (data.action === 'room_created' || data.action === 'joined_room') {
      console.log('Successfully reconnected to room');
      // Room reconnection successful, no need to show anything
      return;
    }

    if (data.action === 'player_joined') {
      console.log('Player joined:', data.playerInfo);
      this.setData({
        opponentInfo: data.playerInfo
      });
      app.globalData.opponentInfo = data.playerInfo;
      
      wx.showToast({
        title: `${data.playerInfo.nickname} 加入了房间`,
        icon: 'success'
      });

      if (this.data.isHost) {
        setTimeout(() => this.startGame(), 1000);
      }
    } else if (data.action === 'room_full') {
      console.log('Room full, opponent:', data.opponentInfo);
      this.setData({
        opponentInfo: data.opponentInfo
      });
      app.globalData.opponentInfo = data.opponentInfo;
      
      // Auto-start for host when room is full
      if (this.data.isHost && !this.data.isReady) {
        console.log('Host auto-starting game...');
        setTimeout(() => this.startGame(), 1000);
      }
    } else if (data.action === 'game_starting') {
      this.handleGameStarting();
    } else if (data.action === 'game_started') {
      wx.redirectTo({
        url: '/pages/game/game'
      });
    } else if (data.action === 'player_left') {
      this.setData({
        opponentInfo: null
      });
      app.globalData.opponentInfo = null;
      
      wx.showToast({
        title: '对手离开了房间',
        icon: 'none'
      });
    } else if (data.action === 'error') {
      wx.showToast({
        title: data.message || '操作失败',
        icon: 'none'
      });
    }
  },

  startGame() {
    if (!this.data.opponentInfo) {
      wx.showToast({
        title: '等待对手加入',
        icon: 'none'
      });
      return;
    }

    app.sendMessage({
      action: 'start_game',
      roomId: this.data.roomId
    });
  },

  handleGameStarting() {
    this.setData({ isReady: true, countdown: 3 });
    
    const timer = setInterval(() => {
      if (this.data.countdown > 1) {
        this.setData({
          countdown: this.data.countdown - 1
        });
      } else {
        clearInterval(timer);
        wx.redirectTo({
          url: '/pages/game/game'
        });
      }
    }, 1000);
  },

  leaveRoom() {
    wx.showModal({
      title: '确认离开',
      content: '确定要离开房间吗？',
      success: (res) => {
        if (res.confirm) {
          app.sendMessage({
            action: 'leave_room',
            roomId: this.data.roomId,
            playerId: this.data.playerInfo.playerId
          });
          
          app.resetGameState();
          wx.redirectTo({
            url: '/pages/index/index'
          });
        }
      }
    });
  }
});