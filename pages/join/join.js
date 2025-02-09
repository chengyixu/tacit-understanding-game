// pages/join/join.js
Page({
  data: {
    roomId: '',
    nickname: ''
  },

  formSubmit(e) {
    let roomId = e.detail.value.roomId.trim().toLowerCase(); // 去除空格并转小写
    let nickname = e.detail.value.nickname.trim();
    console.log('尝试加入房间号:', roomId) 
    if (!roomId || !nickname) return
    
    const app = getApp()
    app.globalData.roomId = roomId
    app.globalData.nickname = nickname
  
    app.globalData.ws.send({
      data: JSON.stringify({
        type: 'join',
        room_id: roomId,
        nickname: nickname
      }),
      success: () => wx.navigateTo({ url: '/pages/waiting/waiting' })
    })
  }
})