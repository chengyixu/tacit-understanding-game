const app = getApp();

Page({
  data: {
    roomId: '',
    playerInfo: null,
    opponentInfo: null,
    currentBattle: null,
    selectedNounId: null,
    isProcessing: false,
    battleHistory: [],
    roundProgress: 0,
    totalRounds: 9,
    waitingForOpponent: false
  },

  onLoad() {
    if (!app.globalData.roomId || !app.globalData.playerInfo) {
      wx.redirectTo({ url: '/pages/index/index' });
      return;
    }

    this.setData({
      roomId: app.globalData.roomId,
      playerInfo: app.globalData.playerInfo,
      opponentInfo: app.globalData.opponentInfo
    });

    app.setMessageCallback(this.handleMessage.bind(this));
    
    // If waiting room already received the game payload, hydrate immediately
    if (app.globalData.pendingGameData) {
      this.handleGameStarted(app.globalData.pendingGameData);
      app.globalData.pendingGameData = null;
    }
  },

  onShow() {
    app.setMessageCallback(this.handleMessage.bind(this));
    
    // Reconnect and request current game state when returning from background
    if (app.globalData.roomId && app.globalData.playerInfo && this.data.currentBattle) {
      console.log('Game page onShow - checking connection');
      
      // Check WebSocket connection
      if (!app.globalData.wsConnected) {
        wx.showToast({
          title: '重新连接中...',
          icon: 'loading'
        });
        
        // Wait for connection then request game state
        setTimeout(() => {
          this.requestGameState();
        }, 1000);
      } else {
        // Connection is alive, request current state if we're in a game
        if (this.data.currentRound > 0) {
          this.requestGameState();
        }
      }
    }
  },
  
  onHide() {
    // Page goes to background
    console.log('Game page onHide');
  },
  
  requestGameState() {
    // Request current game state from server
    console.log('Requesting current game state');
    app.sendMessage({
      action: 'requestGameState',
      roomId: app.globalData.roomId,
      playerId: app.globalData.playerInfo.playerId,
      currentRound: this.data.currentRound
    });
  },

  onUnload() {
    app.clearMessageCallback();
  },

  handleMessage(data) {
    console.log('Game page received:', data);

    switch(data.action) {
      case 'gameStarted':
        this.handleGameStarted(data);
        break;
      case 'battle_data':
        this.handleBattleData(data);
        break;
      case 'nextBattle':
        this.handleNextBattle(data);
        break;
      case 'gameProgress':
        this.handleGameProgress(data);
        break;
      case 'tournamentComplete':
        this.handleTournamentComplete(data);
        break;
      case 'gameComplete':
        this.handleGameComplete(data);
        break;
      case 'gameStateUpdate':
        // Restore game state after reconnection
        console.log('Restored game state:', data);
        if (data.currentBattle) {
          this.setData({
            currentBattle: data.currentBattle,
            currentRound: data.currentRound,
            totalRounds: data.totalRounds || 9
          });
          wx.showToast({
            title: '已恢复游戏',
            icon: 'success'
          });
        }
        break;
      case 'gameAlreadyComplete':
        // Game finished while disconnected
        wx.redirectTo({
          url: '/pages/result/result'
        });
        break;
      case 'waitingForOpponent':
        wx.showToast({
          title: '等待对手完成',
          icon: 'loading',
          duration: 2000
        });
        break;
      case 'gameNotStarted':
        wx.redirectTo({
          url: '/pages/waiting/waiting'
        });
        break;
      case 'choiceSubmitted':
        // Confirmation that choice was received by server
        console.log('Choice confirmed by server for round', data.round);
        // Immediately hide loading toast when choice is confirmed
        wx.hideToast();
        // Show a shorter waiting message
        wx.showToast({
          title: '等待对手...',
          icon: 'loading',
          duration: 2000
        });
        break;
      case 'error':
        this.handleError(data);
        break;
    }
  },

  handleGameStarted(data) {
    console.log('Game started with data:', data);
    const progress = 0;
    
    this.setData({
      currentBattle: data.currentBattle,
      totalRounds: data.totalRounds || 9,
      roundProgress: progress,
      selectedNounId: null,
      waitingForOpponent: false,
      isProcessing: false
    });
    
    // Request first battle from server
    if (!data.currentBattle) {
      app.sendMessage({
        action: 'getBattle',
        roomId: this.data.roomId,
        playerId: this.data.playerInfo.playerId
      });
    }
  },
  
  handleBattleData(data) {
    console.log('Battle data received:', data);
    const progress = ((data.currentRound - 1) / this.data.totalRounds) * 100;
    
    this.setData({
      currentBattle: data.currentBattle,
      roundProgress: progress,
      selectedNounId: null,
      waitingForOpponent: false,
      isProcessing: false
    });
  },
  
  handleNextBattle(data) {
    console.log('Received nextBattle, hiding loading toast');
    
    // Immediately hide any loading toast
    wx.hideToast();
    
    const progress = ((data.currentRound - 1) / this.data.totalRounds) * 100;
    
    this.setData({
      currentBattle: data.currentBattle,
      roundProgress: progress,
      selectedNounId: null,
      waitingForOpponent: false,
      isProcessing: false
    });
  },
  
  handleGameProgress(data) {
    console.log('Game progress update:', data);
    // Handle progress updates from other players
    if (data.allCompleted) {
      wx.redirectTo({
        url: '/pages/result/result'
      });
    }
  },


  handleTournamentComplete(data) {
    console.log('Tournament complete:', data);
    
    // Hide any existing loading toast
    wx.hideToast();
    
    this.setData({
      isProcessing: false,
      waitingForOpponent: true
    });
    // Player's tournament is complete, waiting for others
    if (data.waitingForOthers) {
      wx.showToast({
        title: '等待其他玩家完成...',
        icon: 'loading',
        duration: 60000
      });
    }
  },

  handleGameComplete(data) {
    console.log('Game complete:', data);
    
    // Immediately hide any loading toast
    wx.hideToast();
    
    this.setData({
      isProcessing: false,
      waitingForOpponent: false
    });
    // Store results in app global data for result page
    app.globalData.gameResults = data;
    wx.redirectTo({
      url: '/pages/result/result'
    });
  },

  handleError(data) {
    this.setData({
      isProcessing: false,
      waitingForOpponent: false
    });
    
    wx.showToast({
      title: data.message || '操作失败',
      icon: 'none'
    });
  },

  selectOption(event) {
    if (this.data.isProcessing || !this.data.currentBattle) {
      return;
    }

    const nounId = event && event.currentTarget ? event.currentTarget.dataset.id : null;
    if (!nounId) {
      return;
    }

    this.setData({
      selectedNounId: nounId,
      waitingForOpponent: !this.data.testMode,
      isProcessing: true
    });
    
    console.log(`Submitting choice for round ${this.data.currentBattle.round}: ${nounId}`);
    
    app.sendMessage({
      action: 'submitChoice',
      roomId: this.data.roomId,
      playerId: this.data.playerInfo.playerId,
      round: this.data.currentBattle.round,
      nounId: nounId
    });

    if (!this.data.testMode) {
      wx.showToast({
        title: '提交中...',
        icon: 'loading',
        duration: 50  // Short duration since server responds immediately
      });
    }
  },

  // Next battle is automatically sent by server after submitChoice
});
