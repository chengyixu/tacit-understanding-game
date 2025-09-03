# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a WeChat Mini Program called "默契小游戏" (Tacit Understanding Game) - a multiplayer word selection game where players compete through 9 elimination rounds to find their preferred words and calculate their tacit understanding percentage.

## Gameplay Description

### Game Flow
1. **Room Creation/Joining**: Players can either create a new room (generates 6-digit room ID) or join existing room
2. **Player Setup**: Enter nickname (max 10 chars) and wait for opponent
3. **Word Selection Battle**: 
   - Each game randomly generates 10 words from the word bank
   - Both players receive the SAME 10 words for fairness
   - Display sequence is randomized for each player
   - Players choose preferred word between 2 options each round
   - 9 elimination rounds total (10→9→8→...→2→1)
4. **Results**: Shows champion word and tacit understanding percentage

### Key Game Mechanics
- **Word Pool**: 10 words randomly selected from backend word bank per game session
- **Fairness**: Same word set for both players, only presentation order differs
- **Elimination**: Winner advances to next round, loser is eliminated
- **Synchronization**: Real-time WebSocket ensures simultaneous gameplay

## Development Commands

### WeChat Developer Tools
- **Build**: Use WeChat Developer Tools' built-in compilation (Ctrl/Cmd+B)
- **Preview**: Generate QR code for mobile testing 
- **Challenge Mode Testing**: Access "专项挑战" from index page for category-specific games

## Architecture Overview

### WebSocket State Management Pattern
The app uses a centralized WebSocket management pattern through `app.js`:
- Single persistent connection to `wss://www.aiconnector.cn:3000/ws`
- Backend server hosted at 43.137.34.201 (Tencent Cloud Light Application Server)
- Global state shared across pages via `getApp().globalData`
- Message callbacks registered per page using `app.setMessageCallback()`
- Auto-reconnection with 3-second retry on disconnect
- Race condition prevention using `isProcessing` flag in game logic

### Page Flow & State Transitions
```
Index → Create/Join/Challenge → Waiting → Game → Result
         ↑                                          ↓
         └──────────────────────────────────────────┘
```

Each page manages its lifecycle with WebSocket callbacks:
- `onLoad`: Register message callback
- `onShow`: Re-register callback (handles page navigation)
- `onUnload`: Clean up callback

### Game Architecture
The game page (`pages/game/game.js`) implements:

**Multiplayer Mode**:
- Real-time sync via WebSocket messages
- Server-driven battle data (`currentBattle`)
- State updates through `handleGameUpdate()`
- Server ensures both players have identical word sets

### Critical Data Structures

**Battle Data Format**:
```javascript
{
  round: 1-9,
  noun1: { id, name, categoryId },
  noun2: { id, name, categoryId },
  winnerNounId: null | id
}
```

**Player State**:
```javascript
{
  playerInfo: { nickname, playerId },
  roomId: "123456",  // 6-digit numeric
  isHost: boolean,
  challengeMode: boolean,
  challengeCategory: { id, name, icon }
}
```

## Key Implementation Patterns

### WebSocket Message Handling
All pages follow this pattern for message handling:
```javascript
onLoad() {
  const app = getApp();
  app.setMessageCallback(this.handleMessage.bind(this));
}

handleMessage(data) {
  switch(data.action) {
    case 'specific_action':
      // Handle with isProcessing flag to prevent race conditions
      break;
  }
}
```

### State Validation Before Navigation
Pages validate required state before rendering:
```javascript
onLoad() {
  const app = getApp();
  if (!app.globalData.roomId || !app.globalData.playerInfo) {
    wx.redirectTo({ url: '/pages/index/index' });
    return;
  }
}
```

## Challenge Mode Categories

10 predefined categories with exactly 10 words each:
1. 科技公司 (Tech Companies)
2. 餐饮品牌 (Restaurant Brands)
3. 歌手 (Singers)
4. 演员 (Actors)
5. 体育明星 (Sports Stars)
6. 电子产品 (Electronic Products)
7. 网络平台 (Online Platforms)
8. 游戏 (Games)
9. 动漫人物 (Anime Characters)
10. 城市 (Cities)

Words are stored in:
- **Production**: Backend server at `/moqiyouxi_backend/word_bank.json` (on server)

## Critical Files

**Frontend (Mini Program)**:
- `app.js`: WebSocket management, global state
- `pages/game/game.js`: Game logic, battle management
- `pages/waiting/waiting.js`: Room management, game start logic
- `pages/challenge/challenge.js`: Category selection, specialized room creation
- `utils/util.js`: `generateRandomRoomId()`, `getTacitLevel()`

**Backend (Deployed on Server)**:
- `/moqiyouxi_backend/server0405.py`: WebSocket server (deployed at 43.137.34.201)
- `/moqiyouxi_backend/word_bank.json`: Production word database with 100 words in 10 categories
- Local `server0405.py`: Reference copy for development

## 默契值 (Tacit Understanding Value) Calculation

The tacit understanding value measures how similar players' word preferences are:

### Calculation Method
Backend calculation in `server0405.py:calculate_tacit_value()`:
1. Collects choice positions (1 or 2) for each of 9 rounds
2. Counts same choices across all battles
3. Calculates: `(same_choices / total_valid_battles) * 100`

### Tacit Level Thresholds
Result page (`pages/result/result.js`):
- **≥80%**: 心有灵犀 (Telepathic Connection)
- **≥60%**: 默契十足 (Perfect Understanding)
- **≥40%**: 有点默契 (Some Understanding)
- **≥20%**: 略有分歧 (Slight Differences)
- **<20%**: 各走各路 (Different Paths)

Utility function (`utils/util.js:getTacitLevel()`):
- **≥90%**: 灵魂伴侣 (Soul Mates)
- **≥70%**: 默契十足 (Perfect Understanding)
- **≥50%**: 有些默契 (Some Understanding)
- **<50%**: 需要磨合 (Need More Practice)

## Data Validation Rules

- **Room ID**: 6-digit numeric string (validated with regex `/^\d{6}$/`)
- **Nickname**: Maximum 10 characters
- **Battle rounds**: Exactly 9 rounds
- **Player count**: Minimum 2 for multiplayer
- **Word selection**: 10 words per game, identical set for both players

## Project Configuration

**App ID**: `wxe66b1b9d4f62a1c2`
**WeChat Library**: 2.24.6
**URL Check**: Disabled for development
**ES6**: Enabled with compilation