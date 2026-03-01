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
    currentPlayerCount: 1,
    themeCategory: null
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
      allPlayers: [app.globalData.playerInfo],
      themeCategory: app.globalData.challengeCategory || app.globalData.selectedThemeCategory
    });

    app.setMessageCallback(this.handleMessage.bind(this));
    
    // ALWAYS reconnect to get the current room state
    this.reconnectToRoom();
    app.globalData.fromCreatePage = false;  // Reset flag
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
      const message = {
        action: 'createRoom',
        roomId: app.globalData.roomId,
        playerInfo: app.globalData.playerInfo,
        challengeMode: app.globalData.themeMode || false,  // Use themeMode to indicate category-specific mode
        challengeCategory: app.globalData.challengeCategory || null,
        groupMode: this.data.groupMode,
        maxPlayers: this.data.maxPlayers
      };
      
      console.log('[WAITING] Sending reconnect message:', message);
      app.sendMessage(message);
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
    if (data.action === 'roomCreated') {
      console.log('Successfully reconnected to room');
      // Don't return - still need to process roomUpdate that follows
      // return;
    }
    
    if (data.action === 'joinedRoom') {
      console.log('Successfully joined room');
      // Don't return - still need to process roomUpdate that follows
      // return;
    }

    if (data.action === 'roomUpdate') {
      console.log('Room update:', data);
      console.log('Players in update:', data.players);
      console.log('My playerInfo:', this.data.playerInfo);
      
      // Update room status with players list
      if (data.players) {
        this.setData({
          allPlayers: data.players,
          currentPlayerCount: data.players.length
        });
        
        // In 2-player mode, find the opponent
        if (!this.data.groupMode && data.players.length === 2) {
          const myPlayerId = (this.data.playerInfo && this.data.playerInfo.playerId)
            || (app.globalData.playerInfo && app.globalData.playerInfo.playerId);
          let opponent = null;

          if (myPlayerId) {
            opponent = data.players.find(p => p.playerId === myPlayerId ? false : true);
          }


          if (!opponent && data.players.length > 1) {
            opponent = data.players.find(p => p.playerId);
          }

          if (!myPlayerId && opponent) {
            console.warn('Player ID missing when processing room update, using opponent id only', opponent);
          }
          console.log('Found opponent:', opponent);
          console.log('Current opponentInfo:', this.data.opponentInfo);
          
          if (opponent) {
            // Always update opponent info when we find one
            this.setData({ opponentInfo: opponent });
            app.globalData.opponentInfo = opponent;
            console.log('Set opponent info to:', opponent);
            
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
      // Preserve initial game payload so game page can render instantly
      app.globalData.pendingGameData = data;
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
    } else if (data.action === 'newRoomCreated') {
      // Handle play_again response - new room created
      console.log('New room created for play_again:', data.roomId);
      app.globalData.roomId = data.roomId;
      app.globalData.isHost = data.isHost;
      this.setData({
        roomId: data.roomId,
        isHost: data.isHost,
        opponentInfo: null,
        allPlayers: [app.globalData.playerInfo],
        currentPlayerCount: 1
      });
      wx.showToast({
        title: '新房间已创建',
        icon: 'success'
      });
    } else if (data.action === 'error') {
      wx.showToast({
        title: data.message || '操作失败',
        icon: 'none'
      });
    }
  },

  startGame() {
    // Check if we have enough players
    if (this.data.groupMode) {
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
      action: 'startGame',
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
