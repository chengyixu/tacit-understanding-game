const app = getApp();

Page({
  data: {
    champion: null,
    myChampion: null,
    opponentChampion: null,
    tacitValue: 0,
    tacitLevel: '',
    eliminatedNouns: [],
    playerInfo: null,
    opponentInfo: null,
    calculationDetails: null,
    debugLog: [],
    showDebug: false
  },

  onLoad() {
    if (!app.globalData.roomId || !app.globalData.playerInfo) {
      wx.redirectTo({ url: '/pages/index/index' });
      return;
    }

    this.addDebugLog('Result page onLoad', {
      roomId: app.globalData.roomId,
      playerInfo: app.globalData.playerInfo,
      opponentInfo: app.globalData.opponentInfo
    });

    this.setData({
      playerInfo: app.globalData.playerInfo,
      opponentInfo: app.globalData.opponentInfo
    });

    app.setMessageCallback(this.handleMessage.bind(this));
    
    const requestData = {
      action: 'get_result',
      roomId: app.globalData.roomId,
      playerId: app.globalData.playerInfo.playerId
    };
    
    this.addDebugLog('Sending get_result request', requestData);
    
    app.sendMessage(requestData);
  },

  onShow() {
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onUnload() {
    app.clearMessageCallback();
  },

  addDebugLog(message, data = null) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
      time: timestamp,
      message: message,
      data: data ? JSON.stringify(data, null, 2) : null
    };
    
    const currentLog = this.data.debugLog || [];
    currentLog.push(logEntry);
    
    // Keep only last 50 entries
    if (currentLog.length > 50) {
      currentLog.shift();
    }
    
    this.setData({
      debugLog: currentLog
    });
    
    console.log(`[${timestamp}] ${message}`, data);
  },

  handleMessage(data) {
    this.addDebugLog('Result page received message', data);

    if (data.action === 'game_result') {
      const tacitLevel = this.getTacitLevel(data.tacitValue);
      
      this.addDebugLog('Processing game_result', {
        hasChampion: !!data.champion,
        hasMyChampion: !!data.myChampion,
        hasOpponentChampion: !!data.opponentChampion,
        championData: data.champion,
        myChampionData: data.myChampion,
        opponentChampionData: data.opponentChampion,
        tacitValue: data.tacitValue,
        hasCalculationDetails: !!data.calculationDetails,
        eliminatedCount: data.eliminatedNouns?.length || 0
      });
      
      // Log each field being set
      this.addDebugLog('My Champion', data.myChampion);
      this.addDebugLog('Opponent Champion', data.opponentChampion);
      this.addDebugLog('Legacy Champion', data.champion);
      this.addDebugLog('Calculation details', data.calculationDetails);
      this.addDebugLog('Eliminated nouns', data.eliminatedNouns);
      
      this.setData({
        champion: data.champion || data.myChampion,  // Fallback for compatibility
        myChampion: data.myChampion || data.champion,
        opponentChampion: data.opponentChampion,
        tacitValue: data.tacitValue,
        tacitLevel: tacitLevel,
        eliminatedNouns: data.eliminatedNouns || [],
        calculationDetails: data.calculationDetails || null
      });
      
      // Verify data was set
      this.addDebugLog('Data after setData', {
        champion: this.data.champion,
        hasCalculationDetails: !!this.data.calculationDetails,
        calculationDetailsType: typeof this.data.calculationDetails
      });
      
    } else if (data.action === 'error') {
      this.addDebugLog('ERROR received', data);
      
      wx.showToast({
        title: data.message || '获取结果失败',
        icon: 'none'
      });
    } else {
      this.addDebugLog('Unknown action received', data);
    }
  },

  getTacitLevel(value) {
    if (value >= 80) return '心有灵犀';
    if (value >= 60) return '默契十足';
    if (value >= 40) return '有点默契';
    if (value >= 20) return '略有分歧';
    return '各走各路';
  },

  playAgain() {
    wx.showModal({
      title: '再来一局',
      content: '是否与当前对手再玩一局？',
      confirmText: '继续',
      cancelText: '返回首页',
      success: (res) => {
        if (res.confirm) {
          app.sendMessage({
            action: 'play_again',
            roomId: app.globalData.roomId,
            playerId: app.globalData.playerInfo.playerId
          });
          
          wx.redirectTo({
            url: '/pages/waiting/waiting'
          });
        } else {
          this.backToHome();
        }
      }
    });
  },

  toggleDebug() {
    this.setData({
      showDebug: !this.data.showDebug
    });
  },

  backToHome() {
    app.sendMessage({
      action: 'leave_room',
      roomId: app.globalData.roomId,
      playerId: app.globalData.playerInfo.playerId
    });
    
    app.resetGameState();
    wx.redirectTo({
      url: '/pages/index/index'
    });
  },

  shareResult() {
    wx.showShareMenu({
      withShareTicket: true,
      menus: ['shareAppMessage', 'shareTimeline']
    });
  },

  onShareAppMessage() {
    return {
      title: `我和${this.data.opponentInfo.nickname}的默契度是${this.data.tacitValue}%！`,
      path: '/pages/index/index',
      imageUrl: ''
    };
  },

  onShareTimeline() {
    return {
      title: `默契小游戏：${this.data.tacitLevel}！`,
      query: '',
      imageUrl: ''
    };
  }
});