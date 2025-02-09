// pages/index/index.js
Page({
  onLoad() {
    this.connectWebSocket()
  },

  connectWebSocket() {
    const ws = wx.connectSocket({
      url: 'wss://www.aiconnector.cn:3000/ws',
      success: () => console.log('WebSocket connected')
    })

    ws.onMessage(res => {
      const data = JSON.parse(res.data)
      this.handleMessage(data)
    })

    getApp().globalData.ws = ws
  },

  handleMessage(data) {
    switch (data.type) {
      case 'error':
        wx.showToast({ title: data.message, icon: 'none' })
        break
      // 其他消息处理在各自页面
    }
  },

  navigateToCreate() {
    wx.navigateTo({ url: '/pages/create/create' })
  },

  navigateToJoin() {
    wx.navigateTo({ url: '/pages/join/join' })
  }
})