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
    waitingForOpponent: false,
    
    // Swipe animation states
    swipeX: 0,
    swipeRotation: 0,
    swipeDirection: '',
    overlayOpacity: 0,
    startX: 0,
    startY: 0,
    
    // AI test mode
    testMode: false
  },

  onLoad() {
    if (!app.globalData.roomId || !app.globalData.playerInfo) {
      wx.redirectTo({ url: '/pages/index/index' });
      return;
    }

    // Set up virtual AI player if in test mode
    if (app.globalData.testMode && !app.globalData.aiPlayer) {
      app.globalData.aiPlayer = {
        playerId: 'ai-' + Date.now(),
        nickname: 'AI对手',
        isAI: true
      };
      app.globalData.opponentInfo = app.globalData.aiPlayer;
    }

    this.setData({
      roomId: app.globalData.roomId,
      playerInfo: app.globalData.playerInfo,
      opponentInfo: app.globalData.opponentInfo,
      testMode: app.globalData.testMode || false
    });

    app.setMessageCallback(this.handleMessage.bind(this));
    
    // Server handles AI behavior in test mode
  },

  onShow() {
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onUnload() {
    app.clearMessageCallback();
  },

  handleMessage(data) {
    console.log('Game page received:', data);

    if (this.data.isProcessing) {
      console.log('Already processing, ignoring message');
      return;
    }

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

  // Touch event handlers for swipe gestures
  onTouchStart(e) {
    if (this.data.isProcessing || this.data.selectedNounId) {
      return;
    }
    
    this.setData({
      startX: e.touches[0].clientX,
      startY: e.touches[0].clientY
    });
  },
  
  onTouchMove(e) {
    if (this.data.isProcessing || this.data.selectedNounId) {
      return;
    }
    
    const deltaX = e.touches[0].clientX - this.data.startX;
    const rotation = deltaX * 0.1; // Slight rotation based on swipe
    
    // Determine swipe direction
    let direction = '';
    let opacity = 0;
    
    if (Math.abs(deltaX) > 30) {
      direction = deltaX > 0 ? 'right' : 'left';
      opacity = Math.min(Math.abs(deltaX) / 150, 1);
    }
    
    this.setData({
      swipeX: deltaX,
      swipeRotation: rotation,
      swipeDirection: direction,
      overlayOpacity: opacity
    });
  },
  
  onTouchEnd(e) {
    if (this.data.isProcessing || this.data.selectedNounId) {
      return;
    }
    
    const threshold = 100;
    
    if (Math.abs(this.data.swipeX) > threshold) {
      // Swipe is significant enough to select
      if (this.data.swipeX < 0) {
        this.selectOption('A');
      } else {
        this.selectOption('B');
      }
    } else {
      // Reset position
      this.setData({
        swipeX: 0,
        swipeRotation: 0,
        swipeDirection: '',
        overlayOpacity: 0
      });
    }
  },
  
  // Quick select buttons
  quickSelectA() {
    if (!this.data.isProcessing && !this.data.selectedNounId) {
      this.animateSelection('left', () => this.selectOption('A'));
    }
  },
  
  quickSelectB() {
    if (!this.data.isProcessing && !this.data.selectedNounId) {
      this.animateSelection('right', () => this.selectOption('B'));
    }
  },
  
  animateSelection(direction, callback) {
    const targetX = direction === 'left' ? -300 : 300;
    const rotation = direction === 'left' ? -20 : 20;
    
    this.setData({
      swipeX: targetX,
      swipeRotation: rotation,
      swipeDirection: direction,
      overlayOpacity: 1
    });
    
    setTimeout(callback, 300);
  },
  
  selectOption(option) {
    if (this.data.isProcessing || this.data.selectedNounId) {
      return;
    }
    
    const nounId = option === 'A' ? 
      this.data.currentBattle.noun1.id : 
      this.data.currentBattle.noun2.id;
    
    this.setData({
      selectedNounId: nounId,
      waitingForOpponent: !this.data.testMode,
      isProcessing: true
    });
    
    app.sendMessage({
      action: 'submitChoice',
      roomId: this.data.roomId,
      playerId: this.data.playerInfo.playerId,
      round: this.data.currentBattle.round,
      nounId: nounId
    });
    
    if (!this.data.testMode) {
      wx.showToast({
        title: '等待对手选择...',
        icon: 'loading',
        duration: 10000
      });
    } else {
      // In test mode, simulate AI choice after a short delay
      this.simulateAIChoice();
    }
    
    // Reset swipe position after selection
    setTimeout(() => {
      this.setData({
        swipeX: 0,
        swipeRotation: 0,
        swipeDirection: '',
        overlayOpacity: 0
      });
    }, 400);
  },
  
  // AI test mode functions
  initAIMode() {
    console.log('Initializing AI test mode with virtual player:', app.globalData.aiPlayer);
    // Virtual AI player is created and ready
    // Server handles word selection from production word bank
    // AI will make choices like a real human player
    this.aiReactionTime = {
      min: 800,   // Minimum thinking time (ms)
      max: 3000   // Maximum thinking time (ms)
    };
  },
  
  simulateAIChoice() {
    // In test mode, we don't actually control the AI - the server does
    // The server will automatically make choices for the AI player
    console.log('Server is handling AI player choices');
    
    // Just wait for server to send next battle after AI makes its choice
    // The server has built-in AI logic for test mode
  },

  selectNoun(e) {
    // Legacy function for compatibility
    const nounId = e.currentTarget.dataset.id;
    const option = nounId === this.data.currentBattle.noun1.id ? 'A' : 'B';
    this.selectOption(option);
  },

  // Next battle is automatically sent by server after submitChoice
});