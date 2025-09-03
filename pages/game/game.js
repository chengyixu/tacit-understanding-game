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
    
    app.sendMessage({
      action: 'get_battle',
      roomId: app.globalData.roomId,
      playerId: app.globalData.playerInfo.playerId
    });
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
      case 'battle_data':
        this.handleBattleData(data);
        break;
      case 'opponent_selected':
        this.handleOpponentSelected(data);
        break;
      case 'battle_result':
        this.handleBattleResult(data);
        break;
      case 'game_ended':
        this.handleGameEnded(data);
        break;
      case 'error':
        this.handleError(data);
        break;
    }
  },

  handleBattleData(data) {
    const progress = ((data.round - 1) / this.data.totalRounds) * 100;
    
    this.setData({
      currentBattle: data.battle,
      roundProgress: progress,
      selectedNounId: null,
      waitingForOpponent: false,
      isProcessing: false
    });
  },

  handleOpponentSelected(data) {
    this.setData({
      waitingForOpponent: true
    });
    
    wx.showToast({
      title: '对手已选择',
      icon: 'none',
      duration: 1000
    });
  },

  handleBattleResult(data) {
    wx.hideToast();
    
    const history = this.data.battleHistory;
    history.push({
      round: data.round,
      winner: data.winnerNoun,
      loser: data.loserNoun
    });
    
    this.setData({
      battleHistory: history,
      currentBattle: null,
      selectedNounId: null,
      waitingForOpponent: false,
      isProcessing: false
    });

    wx.showToast({
      title: `${data.winnerNoun.name} 胜出！`,
      icon: 'none',
      duration: 1500
    });

    setTimeout(() => {
      if (data.hasNext) {
        this.requestNextBattle();
      }
    }, 1500);
  },

  handleGameEnded(data) {
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
      action: 'select_noun',
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


  requestNextBattle() {
    app.sendMessage({
      action: 'get_battle',
      roomId: this.data.roomId,
      playerId: this.data.playerInfo.playerId
    });
  }
});