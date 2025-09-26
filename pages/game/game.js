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
    
    // Game will start with gameStarted message from server
    // No need to request battle data
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

  selectNoun(e) {
    if (this.data.isProcessing || this.data.selectedNounId) {
      return;
    }

    const nounId = e.currentTarget.dataset.id;
    this.setData({
      selectedNounId: nounId,
      waitingForOpponent: true
    });

    app.sendMessage({
      action: 'submitChoice',
      roomId: this.data.roomId,
      playerId: this.data.playerInfo.playerId,
      round: this.data.currentBattle.round,
      nounId: nounId
    });

    wx.showToast({
      title: '等待对手选择...',
      icon: 'loading',
      duration: 10000
    });
  },


  // Next battle is automatically sent by server after submitChoice
});