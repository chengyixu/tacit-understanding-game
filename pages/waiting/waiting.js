// pages/waiting/waiting.js
Page({
  data: {
    players: [],
    roomId: '', 
    showStart: false
  },

  onLoad() {
    const app = getApp()
    this.setData({ 
      roomId: app.globalData.roomId,
      players: this.data.players 
    })
    this.app = app
    app.globalData.ws.onMessage(res => {
      const data = JSON.parse(res.data)
      this.handleMessage(data)
    })
  },

  handleMessage(data) {
    switch (data.type) {
      case 'players_update':
        this.setData({ players: data.players })
        this.checkStartButton()
        break
      case 'game_started':
        wx.navigateTo({ url: '/pages/game/game' })
        break
    }
  },

  checkStartButton() {
    const app = getApp()
    this.setData({ showStart: app.globalData.isHost && this.data.players.length === 2 })
  },

  startGame() {
    this.app.globalData.ws.send({
      data: JSON.stringify({
        type: 'start',
        room_id: this.app.globalData.roomId
      })
    })
  }
})