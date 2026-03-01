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
      { id: 10, name: '城市', icon: '🏙️' },
      { id: 11, name: '现代CP', icon: '💑' },
      { id: 12, name: '美食', icon: '🍜' },
      { id: 13, name: '汽车品牌', icon: '🚗' },
      { id: 14, name: '电影', icon: '🎬' },
      { id: 15, name: '运动项目', icon: '🏃' },
      { id: 16, name: '学科', icon: '📚' },
      { id: 17, name: '节日', icon: '🎉' },
      { id: 18, name: '颜色', icon: '🎨' },
      { id: 19, name: '动物', icon: '🐾' }
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
    
    // Store the selected category
    app.globalData.selectedThemeCategory = category;
    app.globalData.themeMode = true;
    app.globalData.challengeCategory = category;  // Reuse the same field for backend compatibility
    
    wx.showModal({
      title: '自选主题',
      content: `已选择"${category.name}"主题，确定创建房间吗？`,
      confirmText: '创建房间',
      cancelText: '重选',
      success: (res) => {
        if (res.confirm) {
          this.createThemeRoom();
        } else {
          this.setData({
            selectedCategory: null
          });
          app.globalData.selectedThemeCategory = null;
          app.globalData.challengeCategory = null;
        }
      }
    });
  },

  createThemeRoom() {
    // Navigate to create page which will handle room creation
    wx.navigateTo({
      url: '/pages/create/create'
    });
  },

  backToHome() {
    app.globalData.themeMode = false;
    app.globalData.selectedThemeCategory = null;
    app.globalData.challengeCategory = null;
    wx.redirectTo({
      url: '/pages/index/index'
    });
  }
});