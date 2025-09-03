const app = getApp();

Page({
  data: {
    categories: [
      { id: 1, name: '科技公司', icon: '💻' },
      { id: 2, name: '餐饮品牌', icon: '🍔' },
      { id: 3, name: '歌手', icon: '🎤' },
      { id: 4, name: '演员', icon: '🎬' },
      { id: 5, name: '体育明星', icon: '⚽' },
      { id: 6, name: '电子产品', icon: '📱' },
      { id: 7, name: '网络平台', icon: '🌐' },
      { id: 8, name: '游戏', icon: '🎮' },
      { id: 9, name: '动漫人物', icon: '🦸' },
      { id: 10, name: '城市', icon: '🏙️' }
    ],
    selectedCategory: null
  },

  onLoad() {
    if (!app.globalData.playerInfo) {
      wx.redirectTo({ url: '/pages/index/index' });
      return;
    }
  },

  selectCategory(e) {
    const category = e.currentTarget.dataset.category;
    this.setData({
      selectedCategory: category
    });
    
    app.globalData.challengeCategory = category;
    
    wx.showModal({
      title: '专项挑战',
      content: `选择了"${category.name}"类别，确定开始挑战吗？`,
      confirmText: '开始',
      cancelText: '重选',
      success: (res) => {
        if (res.confirm) {
          this.createChallengeRoom();
        } else {
          this.setData({
            selectedCategory: null
          });
          app.globalData.challengeCategory = null;
        }
      }
    });
  },

  createChallengeRoom() {
    wx.navigateTo({
      url: '/pages/create/create'
    });
  },

  backToHome() {
    app.globalData.challengeMode = false;
    app.globalData.challengeCategory = null;
    wx.redirectTo({
      url: '/pages/index/index'
    });
  }
});