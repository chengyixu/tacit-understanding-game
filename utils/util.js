const formatTime = date => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return `${[year, month, day].map(formatNumber).join('/')} ${[hour, minute, second].map(formatNumber).join(':')}`
}

const formatNumber = n => {
  n = n.toString()
  return n[1] ? n : `0${n}`
}

const generateRandomRoomId = () => {
  return Math.floor(100000 + Math.random() * 900000).toString()
}

const getTacitLevel = (value) => {
  if (value >= 90) return '灵魂伴侣'
  if (value >= 70) return '默契十足'
  if (value >= 50) return '有些默契'
  return '需要磨合'
}

const validateRoomId = (roomId) => {
  return /^\d{6}$/.test(roomId)
}

const shuffleArray = (array) => {
  const newArray = [...array]
  for (let i = newArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[newArray[i], newArray[j]] = [newArray[j], newArray[i]]
  }
  return newArray
}

module.exports = {
  formatTime,
  generateRandomRoomId,
  getTacitLevel,
  validateRoomId,
  shuffleArray
}