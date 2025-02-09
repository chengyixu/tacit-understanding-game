// pages/game/game.js
Page({
  data: {
    roomId: '', // 新增房间号
    players: [],
    score: 50,
    choices: null,
    currentChoice: null
  },

  onLoad() {
    const app = getApp()
    this.setData({
      roomId: app.globalData.roomId,
      players: app.globalData.players || []
    })
    this.app = app
    app.globalData.ws.onMessage(res => {
      const data = JSON.parse(res.data)
      this.handleMessage(data)
    })
  },

  handleMessage(data) {
    switch (data.type) {
      case 'game_started':
        this.setData({ 
          score: data.score,
          players: Object.keys(data.choices) // 更新玩家列表
        })
        break
      case 'result':
        this.setData({
          score: data.score,
          choices: data.choices,
          players: Object.keys(data.choices) // 保持玩家列表更新
        })
        wx.vibrateShort() // 添加振动反馈
        setTimeout(() => {
          this.setData({ choices: null })
          wx.showToast({ title: '请进行下一轮选择' })
        }, 3000)
        break
    }
  },

  makeChoice(e) {
    const choice = e.currentTarget.dataset.choice
    this.setData({ currentChoice: choice })
    
    this.app.globalData.ws.send({
      data: JSON.stringify({
        type: 'choice',
        choice: choice
      })
    })
  }
})