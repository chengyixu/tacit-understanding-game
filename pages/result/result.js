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
      
      app.sendMessage(requestData);
    }
  },

  onShow() {
    app.setMessageCallback(this.handleMessage.bind(this));
  },

  onUnload() {
    app.clearMessageCallback();
  },

  handleMessage(data) {

    // Handle pre-loaded results from game page
    if (!data && app.globalData.gameResults) {
      data = app.globalData.gameResults;
    }

    if (data.action === 'gameComplete') {
      const groupMode = !!data.tacitMatrix || !!data.playerRankings;
      
      if (groupMode) {
        // Group mode result
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
        
        const tacitValue = typeof data.tacitValue === 'number'
          ? Number(data.tacitValue.toFixed(1))
          : Number(parseFloat(data.tacitValue || 0).toFixed(1));

        this.setData({
          champion: data.champion || data.myChampion,  // Fallback for compatibility
          myChampion: data.myChampion || data.champion,
          opponentChampion: data.opponentChampion,
          tacitValue: tacitValue,
          tacitLevel: tacitLevel,
          eliminatedNouns: data.eliminatedNouns || [],
          calculationDetails: data.calculationDetails || null
        });
      }
      
      // Generate famous pairs comparison
      this.generateFamousPairsComparison();
      
    } else if (data.action === 'error') {
      
      wx.showToast({
        title: data.message || '获取结果失败',
        icon: 'none'
      });
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
      content: '将创建新房间，请分享房间号给对手加入',
      confirmText: '创建新房间',
      cancelText: '返回首页',
      success: (res) => {
        if (res.confirm) {
          // Clear previous game state but keep player info
          const playerInfo = app.globalData.playerInfo;
          const themeMode = app.globalData.themeMode;
          const challengeCategory = app.globalData.challengeCategory;
          
          // Clear old room data
          app.globalData.roomId = null;
          app.globalData.opponentInfo = null;
          app.globalData.gameResults = null;
          app.globalData.pendingGameData = null;
          app.globalData.isHost = true;
          
          // Keep player info and theme settings
          app.globalData.playerInfo = playerInfo;
          app.globalData.themeMode = themeMode;
          app.globalData.challengeCategory = challengeCategory;
          
          // Navigate to create page to generate new room
          wx.redirectTo({
            url: '/pages/create/create'
          });
        } else {
          this.backToHome();
        }
      }
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
        name1: '霉霉',
        name2: '凯尔斯',
        description: '美国顶流CP',
        tacitScore: 95,
        category: '欧美明星'
      },
      {
        name1: '赞达亚',
        name2: '荷兰弟',
        description: '蜘蛛侠情缘',
        tacitScore: 92,
        category: '欧美明星'
      },
      {
        name1: '丁禹兮',
        name2: '虞书欣',
        description: '永夜星河CP',
        tacitScore: 88,
        category: '国剧CP'
      },
      {
        name1: '王鹤棣',
        name2: '赵露思',
        description: '珠帘玉幕CP',
        tacitScore: 85,
        category: '国剧CP'
      },
      {
        name1: '山田',
        name2: '市川',
        description: '动漫年度CP',
        tacitScore: 93,
        category: '动漫CP'
      },
      {
        name1: '锦史',
        name2: '猫猫',
        description: '药师少女CP',
        tacitScore: 87,
        category: '动漫CP'
      },
      {
        name1: '郭德纲',
        name2: '于谦',
        description: '相声黄金搭档',
        tacitScore: 90,
        category: '喜剧CP'
      },
      {
        name1: '汤姆',
        name2: '杰瑞',
        description: '经典相爱相杀',
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
