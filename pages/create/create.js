// pages/create/create.js
Page({
  data: {
    roomId: '',
    nickname: '',
    players: []
  },

  formSubmit(e) {
    const { roomId, nickname } = e.detail.value
    if (!roomId || !nickname) return
    
    const app = getApp()
    app.globalData.roomId = roomId
    app.globalData.nickname = nickname
    app.globalData.isHost = true

    app.globalData.ws.send({
      data: JSON.stringify({
        type: 'create',
        room_id: roomId,
        nickname: nickname
      }),
      success: () => wx.navigateTo({ url: '/pages/waiting/waiting' })
    })
  }
})