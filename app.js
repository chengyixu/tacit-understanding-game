App({
  globalData: {
    ws: null,
    checkConnection() {
      if (!this.ws || this.ws.readyState !== 1) {
        wx.showToast({ title: '连接已断开，正在重连...', icon: 'none' })
        this.connectWebSocket()
      }
    }
  }
})