const app = getApp();

Page({
  data: {
    roomId: '',
    playerInfo: null,
    opponentInfo: null,
    isHost: false,
    isReady: false,
    countdown: 3,
    groupMode: false,
    maxPlayers: 2,
    allPlayers: [],
    currentPlayerCount: 1
  },

  onLoad() {
    if (!app.globalData.roomId || !app.globalData.playerInfo) {
      wx.redirectTo({ url: '/pages/index/index' });
      return;
    }

    const groupMode = app.globalData.groupMode || false;
    const maxPlayers = app.globalData.maxPlayers || 2;

    this.setData({
      roomId: app.globalData.roomId,
      playerInfo: app.globalData.playerInfo,
      isHost: app.globalData.isHost,
      groupMode: groupMode,
      maxPlayers: maxPlayers,
      allPlayers: [app.globalData.playerInfo]
    });

    app.setMessageCallback(this.handleMessage.bind(this));
    
    // Reconnect to room when page loads
    this.reconnectToRoom();
    
    // Server will send AI opponent info if test mode is enabled
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
        action: 'createRoom',
        roomId: app.globalData.roomId,
        playerInfo: app.globalData.playerInfo,
        challengeMode: app.globalData.challengeMode || false,
        challengeCategory: app.globalData.challengeCategory || null,
        testMode: app.globalData.testMode || false,  // Server handles AI creation
        groupMode: this.data.groupMode,
        maxPlayers: this.data.maxPlayers
      });
      // Server will automatically add AI player if testMode is true
    } else {
      // If guest, rejoin the room
      app.sendMessage({
        action: 'joinRoom',
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
    if (data.action === 'roomCreated' || data.action === 'joinedRoom') {
      console.log('Successfully reconnected to room');
      // Server handles AI player creation in test mode
      return;
    }

    if (data.action === 'roomUpdate') {
      console.log('Room update:', data);
      
      // In test mode, don't wait for players
      if (app.globalData.testMode && this.data.isHost) {
        this.setData({
          opponentInfo: { nickname: 'AI', playerId: 'ai' }
        });
        app.globalData.opponentInfo = { nickname: 'AI', playerId: 'ai' };
        setTimeout(() => this.startGame(), 1000);
        return;
      }
      
      // Update room status with players list
      if (data.players) {
        this.setData({
          allPlayers: data.players,
          currentPlayerCount: data.players.length
        });
        
        // In 2-player mode, find the opponent
        if (!this.data.groupMode && data.players.length === 2) {
          const opponent = data.players.find(p => p.playerId !== this.data.playerInfo.playerId);
          if (opponent && !this.data.opponentInfo) {
            this.setData({ opponentInfo: opponent });
            app.globalData.opponentInfo = opponent;
            
            wx.showToast({
              title: `${opponent.nickname} 加入了房间`,
              icon: 'success'
            });
            
            // Auto-start for host when opponent joins
            if (this.data.isHost) {
              setTimeout(() => this.startGame(), 1000);
            }
          }
        } else if (this.data.groupMode) {
          // In group mode, check if room is full
          if (this.data.currentPlayerCount >= this.data.maxPlayers && this.data.isHost) {
            setTimeout(() => this.startGame(), 1000);
          }
        }
      }
    } else if (data.action === 'player_joined') {
      console.log('Player joined:', data);
      const newPlayer = data.playerInfo;
      
      if (newPlayer && newPlayer.playerId !== this.data.playerInfo.playerId) {
        // Store AI player info if it's an AI
        if (newPlayer.playerId && newPlayer.playerId.startsWith('AI_')) {
          app.globalData.aiPlayer = newPlayer;
        }
        
        this.setData({
          opponentInfo: newPlayer,
          allPlayers: [this.data.playerInfo, newPlayer],
          currentPlayerCount: 2
        });
        
        app.globalData.opponentInfo = newPlayer;
        
        wx.showToast({
          title: `${newPlayer.nickname} 加入了房间`,
          icon: 'success'
        });
      }
    } else if (data.action === 'room_full') {
      console.log('Room full, opponent:', data.opponentInfo);
      
      if (this.data.groupMode) {
        // Group mode room full
        if (data.players) {
          this.setData({
            allPlayers: data.players,
            currentPlayerCount: data.players.length
          });
        }
      } else {
        this.setData({
          opponentInfo: data.opponentInfo
        });
        app.globalData.opponentInfo = data.opponentInfo;
      }
      
      // Auto-start for host when room is full
      if (this.data.isHost && !this.data.isReady) {
        console.log('Host auto-starting game...');
        setTimeout(() => this.startGame(), 1000);
      }
    } else if (data.action === 'gameStarting') {
      this.handleGameStarting();
    } else if (data.action === 'gameStarted') {
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
    // In test mode, wait for server to add AI player
    if (app.globalData.testMode) {
      if (!this.data.opponentInfo) {
        wx.showToast({
          title: '等待AI加入...',
          icon: 'loading',
          duration: 2000
        });
        // Server adds AI after 1 second, wait a bit more then retry
        setTimeout(() => {
          if (this.data.opponentInfo) {
            this.startGame();
          } else {
            wx.showToast({
              title: 'AI未就绪，请重试',
              icon: 'none'
            });
          }
        }, 1500);
        return;
      }
    } else if (this.data.groupMode) {
      // Group mode: check if we have enough players
      if (this.data.currentPlayerCount < this.data.maxPlayers) {
        wx.showToast({
          title: `等待更多玩家加入 (${this.data.currentPlayerCount}/${this.data.maxPlayers})`,
          icon: 'none'
        });
        return;
      }
    } else {
      // 2-player mode
      if (!this.data.opponentInfo) {
        wx.showToast({
          title: '等待对手加入',
          icon: 'none'
        });
        return;
      }
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