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
    showDebug: false,
    famousPairs: [],
    showFamousPairs: false,
    groupMode: false,
    allPlayers: [],
    pairwiseTacitScores: null
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
    
    // Check if results are already available (from game page)
    if (app.globalData.gameResults) {
      this.handleMessage(app.globalData.gameResults);
    } else {
      // Otherwise request results from server
      const requestData = {
        action: 'get_result',
        roomId: app.globalData.roomId,
        playerId: app.globalData.playerInfo.playerId
      };
      
      this.addDebugLog('Sending get_result request', requestData);
      
      app.sendMessage(requestData);
    }
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

    // Handle pre-loaded results from game page
    if (!data && app.globalData.gameResults) {
      data = app.globalData.gameResults;
      this.addDebugLog('Using pre-loaded game results', data);
    }

    if (data.action === 'gameComplete') {
      const groupMode = !!data.tacitMatrix || !!data.playerRankings;
      
      if (groupMode) {
        // Group mode result
        this.addDebugLog('Processing group_result', {
          allPlayers: data.allPlayers,
          pairwiseTacitScores: data.pairwiseTacitScores,
          myChampion: data.myChampion
        });
        
        this.setData({
          groupMode: true,
          allPlayers: data.allPlayers || [],
          pairwiseTacitScores: data.pairwiseTacitScores || {},
          myChampion: data.myChampion,
          champion: data.myChampion,
          eliminatedNouns: data.eliminatedNouns || [],
          calculationDetails: data.calculationDetails || null
        });
        
        // Process pairwise scores for display
        this.processPairwiseScores();
      } else {
        // 2-player mode result
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
      }
      
      // Generate famous pairs comparison
      this.generateFamousPairsComparison();
      
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
    // Roast Results based on tacit score
    if (value >= 95) return '💕 要不你们结婚吧，太配了';
    if (value >= 80) return '❤️ 心有灵犀，灵魂伴侣石锤了';
    if (value >= 70) return '😊 默契十足，可以考虑合租了';
    if (value >= 60) return '👍 很有默契，是真朋友了';
    if (value >= 50) return '🤝 还行吧，普通朋友水平';
    if (value >= 40) return '😅 有点默契，但还需要磨合';
    if (value >= 30) return '🤔 略有分歧，建议多交流';
    if (value >= 20) return '😬 塑料友谊石锤了';
    if (value >= 10) return '😱 各走各路吧，三观不合';
    if (value >= 5) return '💔 你们是仇人吗？建议检查下是不是玩反了';
    return '🙈 完全没默契，建议重新认识一下对方';
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
  
  processPairwiseScores() {
    // Process pairwise scores into a ranked list for display
    const scores = this.data.pairwiseTacitScores;
    const myId = this.data.playerInfo.playerId;
    const pairsList = [];
    
    // Extract all pairs with the current player
    for (let p1 in scores) {
      if (p1 === myId) {
        for (let p2 in scores[p1]) {
          const otherPlayer = this.data.allPlayers.find(p => p.playerId === p2);
          if (otherPlayer) {
            pairsList.push({
              playerName: otherPlayer.nickname,
              tacitScore: scores[p1][p2].tacit_value,
              tacitLevel: this.getTacitLevel(scores[p1][p2].tacit_value)
            });
          }
        }
      }
    }
    
    // Sort by tacit score descending
    pairsList.sort((a, b) => b.tacitScore - a.tacitScore);
    
    this.setData({
      myPairwiseScores: pairsList
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
    // Generate certificate before sharing
    this.generateCertificate(() => {
      wx.showShareMenu({
        withShareTicket: true,
        menus: ['shareAppMessage', 'shareTimeline']
      });
    });
  },
  
  generateCertificate(callback) {
    wx.showLoading({ title: '生成证书中...' });
    
    const ctx = wx.createCanvasContext('certificateCanvas', this);
    
    // Canvas dimensions
    const width = 375;
    const height = 500;
    
    // Background gradient effect
    const grd = ctx.createLinearGradient(0, 0, 0, height);
    grd.addColorStop(0, '#FFE5E5');
    grd.addColorStop(1, '#FFF0F0');
    ctx.setFillStyle(grd);
    ctx.fillRect(0, 0, width, height);
    
    // Certificate border
    ctx.setStrokeStyle('#FF6B6B');
    ctx.setLineWidth(3);
    ctx.strokeRect(15, 15, width - 30, height - 30);
    
    // Inner border
    ctx.setStrokeStyle('#FFB6C1');
    ctx.setLineWidth(1);
    ctx.strokeRect(25, 25, width - 50, height - 50);
    
    // Title
    ctx.setFillStyle('#FF1493');
    ctx.setFontSize(28);
    ctx.setTextAlign('center');
    ctx.fillText('默契证书', width / 2, 70);
    
    // Certificate icon
    ctx.setFontSize(50);
    ctx.fillText('💕', width / 2, 120);
    
    // Get certificate title based on tacit value
    const certificateTitle = this.getCertificateTitle(this.data.tacitValue);
    
    // Certificate title
    ctx.setFillStyle('#FF69B4');
    ctx.setFontSize(24);
    ctx.fillText(certificateTitle, width / 2, 170);
    
    // Player names
    ctx.setFillStyle('#333');
    ctx.setFontSize(18);
    ctx.fillText(`${this.data.playerInfo.nickname}`, width / 2 - 60, 210);
    ctx.fillText('&', width / 2, 210);
    ctx.fillText(`${this.data.opponentInfo.nickname}`, width / 2 + 60, 210);
    
    // Tacit value circle
    ctx.beginPath();
    ctx.arc(width / 2, 270, 45, 0, 2 * Math.PI);
    ctx.setFillStyle('#FFF');
    ctx.fill();
    ctx.setStrokeStyle('#FF6B6B');
    ctx.setLineWidth(3);
    ctx.stroke();
    
    // Tacit value text
    ctx.setFillStyle('#FF1493');
    ctx.setFontSize(32);
    ctx.fillText(`${this.data.tacitValue}%`, width / 2, 280);
    
    // Champions section
    if (this.data.myChampion || this.data.opponentChampion) {
      ctx.setFillStyle('#666');
      ctx.setFontSize(14);
      ctx.fillText('最终冠军词', width / 2, 340);
      
      if (this.data.myChampion) {
        ctx.setFillStyle('#FF69B4');
        ctx.setFontSize(16);
        ctx.fillText(`${this.data.playerInfo.nickname}: ${this.data.myChampion.name}`, width / 2, 365);
      }
      
      if (this.data.opponentChampion) {
        ctx.setFillStyle('#FF69B4');
        ctx.setFontSize(16);
        ctx.fillText(`${this.data.opponentInfo.nickname}: ${this.data.opponentChampion.name}`, width / 2, 385);
      }
    }
    
    // Date
    const date = new Date().toLocaleDateString('zh-CN');
    ctx.setFillStyle('#999');
    ctx.setFontSize(12);
    ctx.fillText(date, width / 2, 430);
    
    // QR code placeholder text
    ctx.setFillStyle('#666');
    ctx.setFontSize(10);
    ctx.fillText('扫码来挑战我们的默契度', width / 2, 460);
    
    // Save canvas to image
    ctx.draw(false, () => {
      setTimeout(() => {
        wx.canvasToTempFilePath({
          canvasId: 'certificateCanvas',
          success: (res) => {
            this.setData({ certificateImage: res.tempFilePath });
            wx.hideLoading();
            
            // Preview the certificate
            wx.previewImage({
              current: res.tempFilePath,
              urls: [res.tempFilePath]
            });
            
            if (callback) callback();
          },
          fail: (err) => {
            wx.hideLoading();
            console.error('Generate certificate failed:', err);
            wx.showToast({
              title: '证书生成失败',
              icon: 'none'
            });
            if (callback) callback();
          }
        }, this);
      }, 100);
    });
  },
  
  getCertificateTitle(value) {
    if (value >= 95) return '💑 灵魂伴侣';
    if (value >= 80) return '❤️ 心有灵犀';
    if (value >= 70) return '💕 默契拍档';
    if (value >= 60) return '🤝 好朋友';
    if (value >= 50) return '😊 有缘人';
    if (value >= 40) return '🤗 普通朋友';
    if (value >= 30) return '😅 需要磨合';
    if (value >= 20) return '😬 塑料姐妹花';
    if (value >= 10) return '💔 相爱相杀CP';
    return '🙈 陌生人';
  },
  
  generateFamousPairsComparison() {
    // Define famous pairs with preset tacit scores
    const famousPairs = [
      {
        name1: '刘备',
        name2: '关羽',
        description: '桃园三结义',
        tacitScore: 95,
        category: '历史兄弟'
      },
      {
        name1: '诸葛亮',
        name2: '周瑜',
        description: '既生瑜何生亮',
        tacitScore: 35,
        category: '宿敌'
      },
      {
        name1: '郭德纲',
        name2: '于谦',
        description: '相声黄金搭档',
        tacitScore: 92,
        category: '喜剧CP'
      },
      {
        name1: '罗密欧',
        name2: '朱丽叶',
        description: '莎士比亚经典',
        tacitScore: 88,
        category: '爱情传说'
      },
      {
        name1: '梁山伯',
        name2: '祝英台',
        description: '化蝶传说',
        tacitScore: 90,
        category: '爱情传说'
      },
      {
        name1: '孙悟空',
        name2: '唐僧',
        description: '师徒情深',
        tacitScore: 75,
        category: '师徒'
      },
      {
        name1: '福尔摩斯',
        name2: '华生',
        description: '最佳拍档',
        tacitScore: 93,
        category: '侦探搭档'
      },
      {
        name1: '汤姆',
        name2: '杰瑞',
        description: '相爱相杀',
        tacitScore: 65,
        category: '卡通CP'
      }
    ];
    
    // Sort famous pairs by how close they are to the player's tacit score
    const playerScore = this.data.tacitValue;
    const pairsWithDiff = famousPairs.map(pair => ({
      ...pair,
      difference: Math.abs(pair.tacitScore - playerScore),
      comparison: pair.tacitScore > playerScore ? '更默契' : 
                  pair.tacitScore < playerScore ? '不如你们' : '旗鼓相当'
    }));
    
    // Sort by similarity
    pairsWithDiff.sort((a, b) => a.difference - b.difference);
    
    // Get top 3 most similar pairs
    const topPairs = pairsWithDiff.slice(0, 3);
    
    this.setData({
      famousPairs: topPairs
    });
  },
  
  toggleFamousPairs() {
    this.setData({
      showFamousPairs: !this.data.showFamousPairs
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