<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// --- 型定義 ---
type GameState = 'title' | 'charmake' | 'explore' | 'event' | 'slot' | 'gameover' | 'clear' | 'dice_battle'
type Direction = 0 | 1 | 2 | 3 // 0:北, 1:東, 2:南, 3:西

interface Player {
  name: string
  avatarUrl: string
  hp: number
  maxHp: number
  timeLeft: number
  coins: number
  x: number
  y: number
  dir: Direction
}


interface Song { embed_url?: string; share_url?: string; youtube_id?: string; title: string }

interface EventDef {
  id: string
  title: string
  text: string
  type: 'positive' | 'negative' | 'gamble'
  effectType: string
  effectValue: number
}

// --- 状態管理 ---
const gameState = ref<GameState>('title')
const currentFloor = ref(1)
const visitedGrid = ref<boolean[][]>([])

// モードと難易度の設定
const gameMode = ref<'oneshot' | 'endless'>('oneshot')
const difficulty = ref<'easy' | 'normal' | 'hard'>('normal')

// 1回クリアモードの目標階層
const targetFloor = computed(() => {
  if (gameMode.value === 'endless') return Infinity
  if (difficulty.value === 'easy') return 3
  if (difficulty.value === 'normal') return 5
  return 10 // hard
})

const player = ref<Player>({
  name: '名無しのハッカー', avatarUrl: '/assets/images/icon.png',
  hp: 100, maxHp: 100, timeLeft: 120, coins: 0, x: 1, y: 1, dir: 1
})

const logMessages = ref<string[]>(['システムへのアクセスを待機中...'])
const activeEvent = ref<{ image: string, def: EventDef } | null>(null)

const eventPool = ref<EventDef[]>([])

// JSONを読み込む関数
async function fetchEvents() {
  try {
    const res = await fetch(`/assets/labyrinth_events.json?t=${new Date().getTime()}`)
    if (res.ok) {
      eventPool.value = await res.json()
    }
  } catch (e) {
    console.error('イベントデータの読み込みに失敗しました')
  }
}

// --- BGM制御 (the pillows) ---
const thePillowsSongs = ref<Song[]>([])
let bgmPlayer: any = null

async function loadSongsAndInitBGM() {
  try {
    const res = await fetch('/assets/thepillows_releases_tab.json')
    if (res.ok) thePillowsSongs.value = await res.json()
  } catch (e) {}

  if (thePillowsSongs.value.length === 0) return
  const randomSong = thePillowsSongs.value[Math.floor(Math.random() * thePillowsSongs.value.length)]
  let targetId = 'xUboS2Fw1-o'
  if (randomSong.embed_url) targetId = randomSong.embed_url.split('/').pop() || targetId

  const loadPlayer = () => {
    // @ts-ignore
    bgmPlayer = new window.YT.Player('bgm-player', {
      videoId: targetId,
      playerVars: { playsinline: 1, loop: 1, playlist: targetId },
      events: {
        onReady: (e: any) => { e.target.setVolume(20) }
      }
    })
  }

  // @ts-ignore
  if (!window.YT) {
    const tag = document.createElement('script')
    tag.src = "https://www.youtube.com/iframe_api"
    document.head.appendChild(tag)
    // @ts-ignore
    window.onYouTubeIframeAPIReady = loadPlayer
  } else {
    loadPlayer()
  }
}

// --- タイトル＆ランキング ---
const rankings = ref<any[]>([])
const finalScore = ref(0)

async function fetchRankings() {
  try {
    const res = await fetch('/api/ranking')
    if (res.ok) rankings.value = await res.json()
    else throw new Error()
  } catch (e) {
    rankings.value = [
      { name: 'インフラエンジニア', score: 15400, floor: 12 },
      { name: '名無しのピロウズ', score: 12200, floor: 9 },
      { name: 'ストレンジカメレオン', score: 9800, floor: 7 },
    ]
  }
}

// --- キャラメイク ---
const charName = ref('')
const charGender = ref('girl') // 'girl' または 'boy' （AIはgirl/boyの方が精度が高いため）
const charHairColor = ref('black')
const charHairStyle = ref('bob')
const charClass = ref('knight')
const isGenerating = ref(false)

async function startDive() {
  player.value.name = charName.value.trim() || '名無しの冒険者'
  isGenerating.value = true
  
  try {
    // 職業ごとのプロンプト定義
    const classPrompts: Record<string, string> = {
      knight: 'in heavy armor, holding a sword, dark dungeon background',
      mage: 'holding a glowing staff, wearing robes, magical aura',
      thief: 'with a dagger, hooded cloak, stealthy stance',
      cleric: 'holding a holy symbol, divine light'
    }
    
    // 選択肢を組み合わせた詳細なプロンプトを作成
    const basePrompt = 'masterpiece, best quality, ultra_detailed, very aesthetic, illustration, 1person, solo'
    const prompt = `${basePrompt}, 1 ${charGender.value}, ${charHairColor.value} hair, ${charHairStyle.value} hair, fantasy RPG, ${classPrompts[charClass.value]}`
    
    const res = await fetch('/api/generate-avatar', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    })
    const data = await res.json()
    if (data.avatarUrl) player.value.avatarUrl = data.avatarUrl
  } catch (e) {
    console.error('アバター生成失敗。デフォルトを使用します。')
  } finally {
        isGenerating.value = false
    
        // 難易度に応じた初期ステータス設定（HPを半分に）
        if (gameMode.value === 'endless') {
            player.value.maxHp = 50; player.value.timeLeft = 120;
        } else {
            if (difficulty.value === 'easy') { player.value.maxHp = 75; player.value.timeLeft = 180; }
            else if (difficulty.value === 'normal') { player.value.maxHp = 50; player.value.timeLeft = 120; }
            else if (difficulty.value === 'hard') { player.value.maxHp = 40; player.value.timeLeft = 90; }
        }
    
        player.value.hp = player.value.maxHp
        player.value.coins = 0
        currentFloor.value = 1
        mapGrid.value = generateMaze(1)
    
        playRandomBGM() // BGMを再生
        startTimer()    // リアルタイムタイマー開始
    
        logMessages.value = ['システムにダイブしました。探索を開始します。']
        gameState.value = 'explore'
    }
}

// --- マップ＆移動ロジック ---
const mapGrid = ref<number[][]>([])
const dirOffsets = [[0, -1], [1, 0], [0, 1], [-1, 0]] // 北, 東, 南, 西
// --- 状態管理 --- にタイマーとダイスバトル用の状態を追加
let timerInterval: number | null = null

const diceState = ref({
  enemyName: '',
  enemyImage: '',
  playerDice: 0,
  enemyDice: 0,
  message: '',
  rolling: false
})

// ギャラリー画像のプール（敵の名前も保持）
const galleryImagesPool = ref<{url: string, enemyName: string}[]>([])


function generateMaze(floor: number) {
  const size = Math.min(31, 15 + Math.floor(floor) * 4) // 以前より広く
  const maze = Array.from({ length: size }, () => Array(size).fill(1))
  
  function dig(x: number, y: number) {
    maze[y][x] = 0
    const dirs = [[0, -2], [2, 0], [0, 2], [-2, 0]].sort(() => Math.random() - 0.5)
    for (const [dx, dy] of dirs) {
      const nx = x + dx, ny = y + dy
      if (nx > 0 && nx < size - 1 && ny > 0 && ny < size - 1 && maze[ny][nx] === 1) {
        maze[y + dy / 2][x + dx / 2] = 0
        dig(nx, ny)
      }
    }
  }
  dig(1, 1)

  let eventCount = floor + 2
  while (eventCount > 0) {
    const rx = Math.floor(Math.random() * (size - 2)) + 1
    const ry = Math.floor(Math.random() * (size - 2)) + 1
    if (maze[ry][rx] === 0 && !(rx === 1 && ry === 1)) {
      maze[ry][rx] = 2; eventCount--
    }
  }

  for (let y = size - 2; y > 0; y--) {
    for (let x = size - 2; x > 0; x--) {
      if (maze[y][x] === 0 || maze[y][x] === 2) {
        maze[y][x] = 3; return maze
      }
    }
  }
  visitedGrid.value = Array.from({ length: size }, () => Array(size).fill(false))
  visitedGrid.value[1][1] = true
  return maze
}

function getCell(x: number, y: number) {
  if (y < 0 || y >= mapGrid.value.length || x < 0 || x >= mapGrid.value[0].length) return 1
  return mapGrid.value[y][x]
}

const frontCell = computed(() => getCell(player.value.x + dirOffsets[player.value.dir][0], player.value.y + dirOffsets[player.value.dir][1]))

function addLog(msg: string) {
  logMessages.value.unshift(msg)
  if (logMessages.value.length > 5) logMessages.value.pop()
}

function turnLeft() { player.value.dir = ((player.value.dir + 3) % 4) as Direction }
function turnRight() { player.value.dir = ((player.value.dir + 1) % 4) as Direction }

function moveForward() {
  if (frontCell.value === 1) return
  player.value.x += dirOffsets[player.value.dir][0]
  player.value.y += dirOffsets[player.value.dir][1]
  player.value.hp -= 1 
  
  // ▼ この1行を追加（移動したマスをミニマップで明るくする）
  visitedGrid.value[player.value.y][player.value.x] = true

  if (player.value.hp <= 0) {
    triggerGameOver()
    return
  }
  checkCurrentCell()
}

const sightLimit = computed(() => {
  let limit = 3 // 最大3マス先まで描画
  for (let d = 0; d <= 3; d++) {
    const cx = player.value.x + dirOffsets[player.value.dir][0] * d
    const cy = player.value.y + dirOffsets[player.value.dir][1] * d
    if (getCell(cx, cy) === 1) {
      limit = d // 壁があったらそこを限界にする
      break
    }
  }
  return limit
})

function checkCurrentCell() {
  const cell = mapGrid.value[player.value.y][player.value.x]
  if (cell === 2) {
    triggerEvent()
    mapGrid.value[player.value.y][player.value.x] = 0
  } else if (cell === 3) {
    if (gameMode.value === 'oneshot' && currentFloor.value >= targetFloor.value) {
      triggerClear()
    } else {
      addLog(`第${currentFloor.value}層を突破！ エリカ・スロットへ移行します。`)
      gameState.value = 'slot'
    }
  }
}

// --- Focus Mode ---
const isFocusing = ref(false)
function useFocusMode() {
  if (player.value.timeLeft <= 10) { addLog('残り時間が少なくて集中できません！'); return }
  isFocusing.value = true
  addLog('the pillowsの曲に没入した...（HP回復）')
  if (bgmPlayer && typeof bgmPlayer.setVolume === 'function') bgmPlayer.setVolume(60)
  
  setTimeout(() => {
    player.value.timeLeft -= 10
    player.value.hp = Math.min(player.value.maxHp, player.value.hp + 40)
    isFocusing.value = false
    if (bgmPlayer && typeof bgmPlayer.setVolume === 'function') bgmPlayer.setVolume(20)
  }, 1500)
}

// --- スロット ---
const slotImages = ['/assets/images/s.webp', '/assets/images/a.webp', '/assets/images/b.webp', '/assets/images/c.webp']
const reels = ref([
  { img: slotImages[0], interval: 0 as any, isSpinning: false },
  { img: slotImages[1], interval: 0 as any, isSpinning: false },
  { img: slotImages[2], interval: 0 as any, isSpinning: false }
])
const slotMessage = ref('コインを消費してスロットを回せます。')
const isAllStopped = computed(() => reels.value.every(r => !r.isSpinning))

async function fetchGalleryImages() {
  try {
    const res = await fetch(`/assets/gallery.json?t=${new Date().getTime()}`)
    if (res.ok) {
      const data = await res.json()
      const images: {url: string, enemyName: string}[] = []
      data.forEach((folder: any) => {
        folder.images.forEach((img: any) => {
          images.push({
            url: `/assets/images/gallery/${folder.name}/${img.file}`,
            enemyName: img.enemy_name && img.enemy_name !== "ネームレス エリカ" ? img.enemy_name : "正体不明のデータ"
          })
        })
      })
      galleryImagesPool.value = images
    }
  } catch (e) {
    console.error('ギャラリー画像の読み込みに失敗しました')
  }
}

// --- BGM制御関数 ---
function playRandomBGM() {
  if (thePillowsSongs.value.length === 0 || !bgmPlayer) return
  const randomSong = thePillowsSongs.value[Math.floor(Math.random() * thePillowsSongs.value.length)]
  let targetId = 'xUboS2Fw1-o'
  if (randomSong.embed_url) targetId = randomSong.embed_url.split('/').pop() || targetId
  else if (randomSong.share_url) targetId = randomSong.share_url.split('/').pop() || targetId

  bgmPlayer.loadVideoById(targetId)
}

function stopBGM() {
  if (bgmPlayer && typeof bgmPlayer.pauseVideo === 'function') {
    bgmPlayer.pauseVideo()
  }
}

// --- タイマー制御 ---
function startTimer() {
  if (timerInterval) clearInterval(timerInterval)
  timerInterval = window.setInterval(() => {
    if (['explore', 'event', 'slot', 'dice_battle'].includes(gameState.value)) {
      player.value.timeLeft -= 1
      if (player.value.timeLeft <= 0) {
        player.value.timeLeft = 0
        triggerGameOver()
      }
    }
  }, 1000)
}

function stopTimer() {
  if (timerInterval) clearInterval(timerInterval)
}

// --- 終了・クリア処理 ---
function triggerGameOver() {
  gameState.value = 'gameover'
  stopBGM()
  stopTimer()
  addLog('システムから切断されました。')
}

function triggerClear() {
  gameState.value = 'clear'
  stopBGM()
  stopTimer()
  addLog('最終階層を突破！ システムの掌握に成功しました。')
}

function triggerEvent() {
  const isEnemyEncounter = Math.random() > 0.5 // 50%で敵エンカウント

  if (isEnemyEncounter && galleryImagesPool.value.length > 0) {
    const randomEnemy = galleryImagesPool.value[Math.floor(Math.random() * galleryImagesPool.value.length)]
    diceState.value = {
      enemyName: randomEnemy.enemyName,
      enemyImage: randomEnemy.url,
      playerDice: 0,
      enemyDice: 0,
      message: `${randomEnemy.enemyName} が立ち塞がった！`,
      rolling: false
    }
    gameState.value = 'dice_battle'
    addLog(`[遭遇] ${randomEnemy.enemyName}`)
  } else if (eventPool.value.length > 0) {
    gameState.value = 'event'
    player.value.coins += 1
    const randomEvent = eventPool.value[Math.floor(Math.random() * eventPool.value.length)]
    
    let eventImage = '/assets/images/erika-hero.jpg'
    if (galleryImagesPool.value.length > 0) {
      eventImage = galleryImagesPool.value[Math.floor(Math.random() * galleryImagesPool.value.length)].url
    }
    activeEvent.value = { image: eventImage, def: randomEvent }
    addLog(`[遭遇] ${randomEvent.title}`)
  }
}

function rollDice() {
  if (diceState.value.rolling) return
  diceState.value.rolling = true
  diceState.value.message = 'サイコロを振っています...'
  
  setTimeout(() => {
    // 1〜6の目をランダムに出す
    const pDice = Math.floor(Math.random() * 6) + 1
    const eDice = Math.floor(Math.random() * 6) + 1
    
    diceState.value.playerDice = pDice
    diceState.value.enemyDice = eDice
    
    // 敵の目がそのままダメージになる
    player.value.hp -= eDice
    addLog(`ダイス勝負！ あなた:${pDice} 敵:${eDice} => ${eDice}のダメージ！`)
    
    if (player.value.hp <= 0) {
      diceState.value.message = `HPが0になった...`
      setTimeout(() => triggerGameOver(), 1500)
      return
    }

    if (pDice > eDice) {
      diceState.value.message = `勝利！ 道が開けた！`
      setTimeout(() => {
        gameState.value = 'explore'
        diceState.value.rolling = false
      }, 1500)
    } else {
      diceState.value.message = `引き分け、または敗北... もう一度振れ！`
      diceState.value.rolling = false
    }
  }, 1000)
}

// 効果を適用する関数
function applyEventEffect(def: EventDef) {
  const p = player.value
  const val = def.effectValue

  switch (def.effectType) {
    case 'heal_hp_fixed':
      p.hp = Math.min(p.maxHp, p.hp + val)
      addLog(`HPが ${val} 回復した。`)
      break
    case 'sub_hp_percent':
      const dmg = Math.floor(p.maxHp * (val / 100))
      p.hp -= dmg
      addLog(`システム負荷によりHPを ${dmg} 失った。`)
      break
    case 'add_time_fixed':
      p.timeLeft += val
      addLog(`制限時間が ${val}秒 延長された。`)
      break
    case 'sub_time_fixed':
      p.timeLeft -= val
      addLog(`トラップにより制限時間を ${val}秒 失った。`)
      break
    case 'warp_forward':
      p.x += dirOffsets[p.dir][0] * val
      p.y += dirOffsets[p.dir][1] * val
      addLog(`空間をスキップして ${val}マス 前進した。`)
      break
    case 'random_hp_or_damage':
      if (Math.random() > 0.5) {
        p.hp = p.maxHp
        addLog(`管理者権限の取得に成功！HPが全回復した。`)
      } else {
        p.hp -= val
        addLog(`アクセス拒否！カウンター攻撃でHPを ${val} 失った。`)
      }
      break
    default:
      console.warn('不明な effectType です:', def.effectType)
  }
}

function closeEvent() {
  if (activeEvent.value) {
    // 変更：関数を実行するのではなく、applyEventEffectに渡す
    applyEventEffect(activeEvent.value.def)
  }
  activeEvent.value = null
  gameState.value = 'explore'
  
  // 死亡またはタイムアップ判定
  if (player.value.hp <= 0 || player.value.timeLeft <= 0) {
    gameState.value = 'gameover'
  }
}

function startSlot() {
  if (player.value.coins <= 0) { slotMessage.value = 'コインが足りません！'; return }
  player.value.coins -= 1
  slotMessage.value = 'タイミングを見計らってストップ！'
  reels.value.forEach(reel => {
    reel.isSpinning = true
    reel.interval = setInterval(() => { reel.img = slotImages[Math.floor(Math.random() * slotImages.length)] }, 50)
  })
}

function stopReel(index: number) {
  const reel = reels.value[index]
  if (!reel.isSpinning) return
  clearInterval(reel.interval)
  reel.isSpinning = false
  if (isAllStopped.value) evaluateSlot()
}

function evaluateSlot() {
  const [r1, r2, r3] = reels.value.map(r => r.img)
  if (r1 === r2 && r2 === r3) {
    slotMessage.value = '🎉 JACKPOT!! HP全回復 ＆ 制限時間+30秒！'
    player.value.hp = player.value.maxHp
    player.value.timeLeft += 30
  } else if (r1 === r2 || r2 === r3 || r1 === r3) {
    slotMessage.value = '✨ 小当り！ HP+20 ＆ 制限時間+10秒'
    player.value.hp = Math.min(player.value.maxHp, player.value.hp + 20)
    player.value.timeLeft += 10
  } else {
    slotMessage.value = 'ハズレ... でも少しだけ時間回復(+5秒)'
    player.value.timeLeft += 5
  }
}

function proceedToNextFloor() {
  currentFloor.value++
  player.value.x = 1; player.value.y = 1; player.value.dir = 1
  mapGrid.value = generateMaze(currentFloor.value)
  slotMessage.value = 'コインを消費してスロットを回せます。'
  gameState.value = 'explore'
  addLog(`第${currentFloor.value}層へ到達。さらに深く潜ります。`)
  
  playRandomBGM() // 次の曲へ切り替え
}
// --- ゲームオーバー ---
async function submitScore(isClear = false) {
  // クリアボーナス
  let clearBonus = 0
  if (isClear) {
    if (difficulty.value === 'easy') clearBonus = 3000
    if (difficulty.value === 'normal') clearBonus = 5000
    if (difficulty.value === 'hard') clearBonus = 10000
  }
  
  finalScore.value = (currentFloor.value * 1000) + (player.value.coins * 200) + Math.max(0, player.value.timeLeft) * 10 + clearBonus
  
  try {
    await fetch('/api/ranking', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: player.value.name, score: finalScore.value, floor: currentFloor.value, avatarUrl: player.value.avatarUrl })
    })
  } catch (e) {}
  await fetchRankings()
  gameState.value = 'title'
}

onMounted(() => {
  fetchRankings()
  loadSongsAndInitBGM()
  fetchEvents()
  fetchGalleryImages()
})

onUnmounted(() => {
  if (bgmPlayer && typeof bgmPlayer.destroy === 'function') bgmPlayer.destroy()
})
</script>

<template>
  <div class="bg-zinc-950 min-h-screen text-white font-mono flex flex-col pt-16">
    <!-- 隠しYouTubeプレイヤー -->
    <div id="bgm-player" class="absolute -top-[9999px] -left-[9999px] w-[1px] h-[1px] overflow-hidden"></div>

    <!-- 1. TITLE SCREEN -->
    <!-- 1. TITLE SCREEN -->
    <div v-if="gameState === 'title'" class="absolute inset-0 bg-zinc-950 flex flex-col items-center p-4 md:p-6 z-30 overflow-y-auto">
      <div class="w-full max-w-md flex flex-col items-center py-6 md:py-10">
        <h1 class="text-4xl md:text-6xl font-black text-erika mb-2 tracking-widest drop-shadow-[0_0_15px_rgba(243,156,18,0.5)] text-center">ERIKA LABYRINTH</h1>
        <p class="text-zinc-400 mb-8 tracking-[0.3em] text-sm md:text-base">Cyber Dungeon Explorer</p>

        <!-- モード＆難易度選択 -->
        <div class="bg-black/60 border border-zinc-700 p-4 rounded-2xl mb-6 w-full flex flex-col gap-4 shadow-xl">
          <div class="flex bg-zinc-900 rounded-lg p-1">
            <button @click="gameMode = 'oneshot'" :class="gameMode === 'oneshot' ? 'bg-erika text-black shadow-md' : 'text-zinc-400 hover:text-white'" class="flex-1 py-2 font-bold rounded-md transition-all text-sm md:text-base">1回クリア</button>
            <button @click="gameMode = 'endless'" :class="gameMode === 'endless' ? 'bg-erika text-black shadow-md' : 'text-zinc-400 hover:text-white'" class="flex-1 py-2 font-bold rounded-md transition-all text-sm md:text-base">エンドレス</button>
          </div>
          
          <div v-if="gameMode === 'oneshot'" class="flex gap-2">
            <button @click="difficulty = 'easy'" :class="difficulty === 'easy' ? 'bg-cyan-500 text-black shadow-md' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'" class="flex-1 py-2 rounded-lg font-bold text-xs md:text-sm transition-all">Easy<br><span class="text-[10px]">3 Floor</span></button>
            <button @click="difficulty = 'normal'" :class="difficulty === 'normal' ? 'bg-emerald-500 text-black shadow-md' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'" class="flex-1 py-2 rounded-lg font-bold text-xs md:text-sm transition-all">Normal<br><span class="text-[10px]">5 Floor</span></button>
            <button @click="difficulty = 'hard'" :class="difficulty === 'hard' ? 'bg-red-500 text-white shadow-md' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'" class="flex-1 py-2 rounded-lg font-bold text-xs md:text-sm transition-all">Hard<br><span class="text-[10px]">10 Floor</span></button>
          </div>
          <div v-else class="text-center py-2 text-sm text-amber-400 font-bold">
            限界まで潜り続けるサバイバルモード
          </div>
        </div>

        <!-- ★スタートボタン -->
        <button @click="gameState = 'charmake'" class="w-full py-4 bg-erika text-black font-black text-xl rounded-full shadow-[0_0_20px_rgba(243,156,18,0.5)] hover:bg-amber-400 hover:-translate-y-1 transition-all mb-8">
          DIVE INTO SYSTEM
        </button>

        <!-- TOP 5 ランキングボード -->
        <div class="bg-zinc-900/80 backdrop-blur-md border border-zinc-700 w-full p-6 rounded-2xl shadow-xl">
          <h2 class="text-xl font-bold text-white mb-4 border-b border-zinc-700 pb-2 text-center">TOP HACKERS</h2>
          <div class="space-y-3">
            <div v-for="(rank, i) in rankings" :key="i" class="flex justify-between items-center bg-black/50 p-3 rounded-lg border border-zinc-800">
              <div class="flex items-center gap-3">
                <span class="text-erika font-black w-4 text-lg">{{ i + 1 }}</span>
                <span class="font-bold text-zinc-200 truncate max-w-[120px]">{{ rank.name }}</span>
              </div>
              <div class="text-right shrink-0">
                <p class="text-sm font-black text-amber-400">{{ rank.score }} pts</p>
                <p class="text-[10px] text-zinc-500">Floor {{ rank.floor }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 2. CHARMAKE SCREEN -->
    <div v-else-if="gameState === 'charmake'" class="absolute inset-0 bg-zinc-950 flex flex-col items-center justify-center p-6 z-30">
        <h2 class="text-3xl font-black text-white mb-8 tracking-widest">INITIALIZE AVATAR</h2>
        
        <div class="w-full max-w-md bg-zinc-900/80 backdrop-blur-md p-6 rounded-2xl border border-zinc-700 shadow-xl mb-8">
            <label class="block text-sm font-bold text-zinc-400 mb-2">HACKER NAME</label>
            <input v-model="charName" type="text" placeholder="名無しの冒険者" class="w-full bg-black border border-zinc-700 rounded-lg px-4 py-3 text-white mb-6 focus:border-erika outline-none transition-colors">

            <div class="grid grid-cols-2 gap-4 mb-4">
                <div>
                    <label class="block text-sm font-bold text-zinc-400 mb-2">性別</label>
                    <select v-model="charGender" class="w-full bg-black border border-zinc-700 rounded-lg p-3 text-white outline-none focus:border-erika">
                    <option value="girl">女性</option>
                    <option value="boy">男性</option>
                    </select>
                </div>
            <div>
                <label class="block text-sm font-bold text-zinc-400 mb-2">髪色</label>
                <select v-model="charHairColor" class="w-full bg-black border border-zinc-700 rounded-lg p-3 text-white outline-none focus:border-erika">
                <option value="black">黒</option>
                <option value="blonde">金</option>
                <option value="silver">銀/白</option>
                <option value="red">赤</option>
                <option value="blue">青</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-bold text-zinc-400 mb-2">髪型</label>
                <select v-model="charHairStyle" class="w-full bg-black border border-zinc-700 rounded-lg p-3 text-white outline-none focus:border-erika">
                <option value="short">ショート</option>
                <option value="bob">ボブ</option>
                <option value="long">ロング</option>
                <option value="ponytail">ポニーテール</option>
                </select>
            </div>
            <div>
                <label class="block text-sm font-bold text-zinc-400 mb-2">職業</label>
                <select v-model="charClass" class="w-full bg-black border border-zinc-700 rounded-lg p-3 text-white outline-none focus:border-erika">
                <option value="knight">騎士 (Knight)</option>
                <option value="mage">魔術師 (Mage)</option>
                <option value="thief">盗賊 (Thief)</option>
                <option value="cleric">聖職者 (Cleric)</option>
                </select>
            </div>
        </div>

        <button @click="startDive" :disabled="isGenerating" class="px-10 py-4 bg-amber-600 text-white font-black text-xl rounded-full shadow-[0_0_20px_rgba(217,119,6,0.5)] hover:bg-amber-500 disabled:opacity-50 transition-all flex items-center gap-2">
            <span v-if="isGenerating" class="animate-spin">🌀</span>
            {{ isGenerating ? 'GENERATING...' : 'GENERATE & DIVE' }}
        </button>
    </div>
</div>

    <!-- ゲーム中ヘッダー -->
    <header v-if="['explore', 'event', 'slot', 'dice_battle'].includes(gameState)" class="bg-zinc-900 border-b border-zinc-700 p-4 flex justify-between items-center shadow-lg z-10">
      <div>
        <p class="text-sm text-zinc-400">FLOOR {{ currentFloor }}</p>
        <p class="font-bold flex items-center gap-2">
          <img :src="player.avatarUrl" class="w-6 h-6 rounded-full border border-zinc-500 object-cover">
          {{ player.name }}
        </p>
      </div>
      <div class="flex gap-4 md:gap-6 text-right">
        <div>
          <p class="text-xs text-zinc-400">TIME</p>
          <p class="text-lg md:text-xl font-black" :class="player.timeLeft < 30 ? 'text-red-400 animate-pulse' : 'text-cyan-400'">{{ player.timeLeft }}s</p>
        </div>
        <div>
          <p class="text-xs text-zinc-400">HP</p>
          <p class="text-lg md:text-xl font-black text-emerald-400">{{ player.hp }} / {{ player.maxHp }}</p>
        </div>
        <div>
          <p class="text-xs text-zinc-400">COIN</p>
          <p class="text-lg md:text-xl font-black text-amber-400">{{ player.coins }}</p>
        </div>
      </div>
    </header>

    <main v-if="['explore', 'event', 'slot', 'dice_battle'].includes(gameState)" class="flex-grow relative flex flex-col">
      
      <!-- 3. EXPLORE SCREEN (3D View) -->
      <div v-if="gameState === 'explore'" class="flex-grow flex flex-col justify-between relative bg-black overflow-hidden">
        
        <!-- ダンジョン描画エリア -->
        <div class="absolute inset-0 flex items-center justify-center bg-zinc-950">
          <!-- 床（暗い石畳を表現するグラデーション） -->
          <div class="absolute inset-0 bg-gradient-to-t from-zinc-800 to-black opacity-50" style="transform: perspective(500px) rotateX(60deg); transform-origin: bottom;"></div>
          
          <div class="relative w-full max-w-lg aspect-square flex items-center justify-center perspective-[800px]">
            <template v-for="depth in [3, 2, 1, 0]" :key="depth">
              
              <!-- ミニマップ（画面右上） -->
              <div class="absolute top-4 right-4 w-32 h-32 bg-black/80 border border-stone-500 rounded-lg p-1 z-20 shadow-[0_0_15px_rgba(0,0,0,0.8)]">
                <div v-for="(row, y) in mapGrid" :key="y" class="flex" :style="{ height: `${100 / mapGrid.length}%` }">
                    <div v-for="(cell, x) in row" :key="x" class="flex-1" :class="{
                        'bg-amber-500 shadow-[0_0_5px_#f59e0b] z-10': x === player.x && y === player.y, // プレイヤー現在地
                        'bg-cyan-500': cell === 3 && visitedGrid[y]?.[x], // ゴール
                        'bg-yellow-400': cell === 2 && visitedGrid[y]?.[x], // イベント
                        'bg-stone-500': cell === 1 && visitedGrid[y]?.[x], // 壁
                        'bg-stone-800': cell === 0 && visitedGrid[y]?.[x], // 通路
                        'bg-transparent': !visitedGrid[y]?.[x] // 未踏破
                        }">
                    </div>
                </div>
              </div>

              <!-- 視界限界（sightLimit）より奥のオブジェクトは描画しない -->
              <template v-if="depth <= sightLimit">
                <!-- ゴール（次の階層へ） -->
                <div v-if="getCell(player.x + dirOffsets[player.dir][0] * depth, player.y + dirOffsets[player.dir][1] * depth) === 3"
                     class="absolute flex items-end justify-center transition-all duration-300"
                     :style="{ zIndex: 11 - depth, transform: `scale(${1 - depth * 0.2}) translateY(${depth * 10}px)` }">
                  <img src="/assets/images/door.webp" class="w-32 h-48 object-contain drop-shadow-[0_0_20px_rgba(0,0,0,0.8)]" alt="Door">
                </div>

                <!-- イベント（宝箱） -->
                <div v-if="getCell(player.x + dirOffsets[player.dir][0] * depth, player.y + dirOffsets[player.dir][1] * depth) === 2"
                     class="absolute flex items-center justify-center transition-all duration-300 animate-bounce"
                     :style="{ zIndex: 11 - depth, transform: `scale(${1 - depth * 0.2}) translateY(${depth * 20}px)` }">
                  <img src="/assets/images/treasure.webp" class="w-24 h-24 object-contain drop-shadow-[0_0_15px_#f59e0b]" alt="Treasure">
                </div>
              </template>

              <!-- 前方の壁（行き止まり: deadend.webp） -->
              <div v-if="getCell(player.x + dirOffsets[player.dir][0] * depth, player.y + dirOffsets[player.dir][1] * depth) === 1" 
                   class="absolute bg-stone-800 bg-cover bg-center border-2 border-stone-950 flex items-center justify-center shadow-[inset_0_0_50px_rgba(0,0,0,0.9)] transition-all duration-300"
                   :style="{ backgroundImage: 'url(/assets/images/deadend.webp)', width: `${100 - depth * 25}%`, height: `${100 - depth * 25}%`, zIndex: 10 - depth }">
              </div>
              
              <!-- 左の壁（通路の壁: stone_wall.webp） -->
              <div v-if="getCell(player.x + dirOffsets[player.dir][0] * depth + dirOffsets[(player.dir+3)%4][0], player.y + dirOffsets[player.dir][1] * depth + dirOffsets[(player.dir+3)%4][1]) === 1"
                   class="absolute left-0 bg-stone-700 bg-cover bg-center border-y-2 border-r-2 border-stone-950 shadow-[inset_0_0_50px_rgba(0,0,0,0.7)] transition-all duration-300"
                   :style="{ backgroundImage: 'url(/assets/images/stone_wall.webp)', width: `${15}%`, height: `${100 - depth * 25}%`, transform: `perspective(500px) rotateY(60deg) translateZ(-${depth * 100}px)`, transformOrigin: 'left', zIndex: 10 - depth }">
              </div>
              
              <!-- 右の壁（通路の壁: stone_wall.webp） -->
              <div v-if="getCell(player.x + dirOffsets[player.dir][0] * depth + dirOffsets[(player.dir+1)%4][0], player.y + dirOffsets[player.dir][1] * depth + dirOffsets[(player.dir+1)%4][1]) === 1"
                   class="absolute right-0 bg-stone-700 bg-cover bg-center border-y-2 border-l-2 border-stone-950 shadow-[inset_0_0_50px_rgba(0,0,0,0.7)] transition-all duration-300"
                   :style="{ backgroundImage: 'url(/assets/images/stone_wall.webp)', width: `${15}%`, height: `${100 - depth * 25}%`, transform: `perspective(500px) rotateY(-60deg) translateZ(-${depth * 100}px)`, transformOrigin: 'right', zIndex: 10 - depth }">
              </div>

            </template>
          </div>
        </div>

        <!-- コントローラー（アバター常時表示＋石造り風UI） -->
        <div class="relative bg-zinc-900 border-t-4 border-stone-700 p-2 z-20 shadow-[0_-10px_20px_rgba(0,0,0,0.8)]">
          <div class="max-w-2xl mx-auto flex gap-4">
            
            <!-- アバター＆ステータス表示 -->
            <div class="flex-1 bg-black border-2 border-stone-600 rounded-lg p-2 flex items-center gap-3">
              <img :src="player.avatarUrl" alt="Avatar" class="w-16 h-16 md:w-20 md:h-20 rounded-md border border-stone-500 object-cover">
              <div class="flex-1">
                <p class="font-bold text-white text-sm md:text-base truncate">{{ player.name }}</p>
                <div class="w-full bg-red-950 h-3 rounded-full mt-1 border border-red-900 overflow-hidden">
                  <div class="bg-red-500 h-full transition-all duration-300" :style="{ width: `${(player.hp / player.maxHp) * 100}%` }"></div>
                </div>
                <p class="text-xs text-red-300 mt-1">HP: {{ player.hp }} / {{ player.maxHp }}</p>
              </div>
            </div>

            <!-- 十字キーコントローラー -->
            <div class="w-40 md:w-48 grid grid-cols-3 gap-1">
              <div class="col-start-2">
                <button @click="moveForward" :disabled="frontCell === 1" class="w-full h-10 md:h-12 bg-stone-700 hover:bg-stone-600 border border-stone-500 rounded font-bold disabled:opacity-30 active:translate-y-1 transition-all">▲</button>
              </div>
              <div class="col-start-1 row-start-2">
                <button @click="turnLeft" class="w-full h-10 md:h-12 bg-stone-700 hover:bg-stone-600 border border-stone-500 rounded font-bold active:translate-y-1 transition-all">◀</button>
              </div>
              <div class="col-start-2 row-start-2 flex items-center justify-center">
                <button @click="useFocusMode" :disabled="isFocusing || player.timeLeft <= 10" class="w-full h-full bg-stone-800 text-amber-500 border border-amber-700 rounded text-xs font-bold hover:bg-amber-900 transition-all flex flex-col items-center justify-center">
                  <span>集中</span>
                </button>
              </div>
              <div class="col-start-3 row-start-2">
                <button @click="turnRight" class="w-full h-10 md:h-12 bg-stone-700 hover:bg-stone-600 border border-stone-500 rounded font-bold active:translate-y-1 transition-all">▶</button>
              </div>
            </div>

          </div>
        </div>
      </div>

      <!-- 4. EVENT SCREEN の画像サイズを修正 -->
      <div v-else-if="gameState === 'event' && activeEvent" class="absolute inset-0 bg-black/90 flex flex-col p-6 z-20">
        <h2 class="text-2xl font-black text-center text-erika mb-4">SYSTEM INTERCEPT</h2>
        <div class="flex-grow flex items-center justify-center p-4">
            <!-- ↓画像を max-h-48 md:max-h-64 object-contain に変更 -->
            <img :src="activeEvent.image" alt="Erika" class="max-w-full max-h-48 md:max-h-64 rounded-lg border-2 border-white/20 shadow-[0_0_30px_rgba(243,156,18,0.3)] object-contain">
        </div>
        <div class="bg-zinc-900 border border-zinc-700 p-4 rounded-xl mt-4">
            <p class="font-bold text-lg mb-2" :class="activeEvent.def.type === 'positive' ? 'text-emerald-400' : 'text-red-400'">{{ activeEvent.def.title }}</p>
            <p class="text-zinc-300 mb-4 text-sm md:text-base">{{ activeEvent.def.text }}</p>
            <button @click="closeEvent" class="w-full py-3 bg-erika text-black font-bold rounded-lg hover:bg-amber-400">受け入れる</button>
        </div>
      </div>

      <!-- 新規追加：DICE BATTLE SCREEN -->
      <div v-else-if="gameState === 'dice_battle'" class="absolute inset-0 bg-black/95 flex flex-col p-6 z-20">
        <h2 class="text-2xl font-black text-center text-red-500 mb-2">SYSTEM INTERCEPT</h2>
        <p class="text-center font-bold mb-4">{{ diceState.message }}</p>
        
        <div class="flex-grow flex flex-col items-center justify-center gap-4">
            <!-- 画像はスクロールしなくて済むサイズに制限 -->
            <img :src="diceState.enemyImage" alt="Enemy" class="max-w-full max-h-40 md:max-h-56 rounded-lg border-2 border-red-500/50 shadow-[0_0_30px_rgba(239,68,68,0.3)] object-contain">
            <p class="text-xl font-bold text-red-400">{{ diceState.enemyName }}</p>
            
            <div class="flex justify-center gap-8 w-full max-w-sm mt-4">
            <div class="text-center">
                <p class="text-zinc-400 text-sm mb-1">あなた</p>
                <div class="w-16 h-16 bg-zinc-800 border-2 border-cyan-500 rounded-lg flex items-center justify-center text-3xl font-black text-cyan-400">
                {{ diceState.playerDice || '?' }}
                </div>
            </div>
            <div class="text-center">
                <p class="text-zinc-400 text-sm mb-1">敵</p>
                <div class="w-16 h-16 bg-zinc-800 border-2 border-red-500 rounded-lg flex items-center justify-center text-3xl font-black text-red-400">
                {{ diceState.enemyDice || '?' }}
                </div>
            </div>
            </div>
        </div>
        
        <div class="mt-6 w-full max-w-sm mx-auto">
            <button @click="rollDice" :disabled="diceState.rolling" class="w-full py-4 bg-red-600 text-white font-black text-xl rounded-lg hover:bg-red-500 disabled:opacity-50 transition-all">
            サイコロを振る
            </button>
        </div>
      </div>

      <!-- 5. SLOT SCREEN -->
      <div v-else-if="gameState === 'slot'" class="absolute inset-0 bg-zinc-900 flex flex-col items-center justify-center p-6 z-20">
        <h2 class="text-4xl font-black text-erika mb-2 drop-shadow-[0_0_10px_rgba(243,156,18,0.5)]">ERIKA SLOTS</h2>
        <p class="text-zinc-400 font-bold mb-6">所持コイン: <span class="text-2xl text-amber-400">{{ player.coins }}</span> 枚</p>

        <div class="bg-black border border-zinc-700 w-full max-w-md p-4 rounded-xl mb-8 text-center font-bold min-h-[4rem] flex items-center justify-center">
          {{ slotMessage }}
        </div>

        <div class="flex gap-4 mb-8">
          <div v-for="(reel, index) in reels" :key="index" class="flex flex-col items-center gap-4">
            <div class="w-24 h-24 md:w-32 md:h-32 bg-black border-4 rounded-xl overflow-hidden shadow-[0_0_20px_rgba(0,0,0,0.8)]" :class="reel.isSpinning ? 'border-erika' : 'border-zinc-600'">
              <img :src="reel.img" alt="Slot Image" class="w-full h-full object-cover" :class="{ 'opacity-80 blur-[2px]': reel.isSpinning }">
            </div>
            <button @click="stopReel(index)" :disabled="!reel.isSpinning" class="w-full py-2 bg-zinc-800 text-white font-bold rounded-lg border border-zinc-600 hover:bg-zinc-700 disabled:opacity-30">STOP</button>
          </div>
        </div>

        <div class="flex flex-col gap-4 w-full max-w-sm mt-4">
          <button @click="startSlot" :disabled="player.coins <= 0 || !isAllStopped" class="w-full py-4 bg-erika text-black font-black text-xl rounded-full shadow-[0_0_15px_rgba(243,156,18,0.4)] hover:bg-amber-400 disabled:opacity-30 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:shadow-none transition-all">
            スロットを回す (1 Coin)
          </button>
          <button @click="proceedToNextFloor" :disabled="!isAllStopped" class="w-full py-3 bg-zinc-800 text-white font-bold rounded-full border border-zinc-600 hover:bg-zinc-700 transition-colors">
            次の階層へ進む ▶
          </button>
        </div>
      </div>
    </main>

    <!-- テキストログ -->
    <footer v-if="['explore', 'event', 'slot'].includes(gameState)" class="bg-black border-t border-zinc-800 p-2 h-24 overflow-y-hidden text-xs text-zinc-500 font-mono">
      <div v-for="(log, i) in logMessages" :key="log + i" :class="i === 0 ? 'text-zinc-200 typewriter-log' : 'opacity-60'">
        > {{ log }}
      </div>
    </footer>

    <!-- Focus Mode エフェクト -->
    <div v-if="isFocusing" class="absolute inset-0 bg-cyan-900/30 backdrop-blur-sm pointer-events-none z-50 flex items-center justify-center">
      <p class="text-3xl font-black text-cyan-300 animate-pulse drop-shadow-[0_0_10px_cyan]">Listening to the pillows...</p>
    </div>

    <!-- 6. GAMEOVER SCREEN -->
    <div v-if="gameState === 'gameover'" class="absolute inset-0 bg-red-950/90 backdrop-blur-sm flex flex-col items-center justify-center p-6 z-50">
      <h2 class="text-6xl font-black text-red-500 mb-4 drop-shadow-[0_0_20px_rgba(239,68,68,0.8)]">SYSTEM DOWN</h2>
      <p class="text-zinc-300 text-lg mb-8">コネクションが切断されました...</p>

      <div class="bg-black/80 border border-red-900/50 p-8 rounded-2xl w-full max-w-md mb-8 text-center shadow-2xl">
        <img :src="player.avatarUrl" class="w-24 h-24 mx-auto rounded-full border-4 border-zinc-700 mb-4 object-cover">
        <p class="font-bold text-xl mb-4 text-white">{{ player.name }}</p>
        <div class="grid grid-cols-2 gap-4 text-left border-t border-zinc-800 pt-4">
          <p class="text-zinc-400">到達階層:</p><p class="font-black text-white text-right">Floor {{ currentFloor }}</p>
          <p class="text-zinc-400">収集コイン:</p><p class="font-black text-amber-400 text-right">{{ player.coins }} 枚</p>
          <p class="text-zinc-400">最終スコア:</p><p class="font-black text-cyan-400 text-right text-2xl">{{ (currentFloor * 1000) + (player.coins * 200) + Math.max(0, player.timeLeft) }} pts</p>
        </div>
      </div>

      <button @click="submitScore()" class="px-10 py-4 bg-red-600 text-white font-black rounded-full hover:bg-red-500 shadow-[0_0_20px_rgba(239,68,68,0.5)] transition-all hover:-translate-y-1">
        スコアを記録してタイトルへ
      </button>
    </div>

    <!-- 7. GAMECLEAR SCREEN -->
    <div v-if="gameState === 'clear'" class="absolute inset-0 bg-blue-950/90 backdrop-blur-sm flex flex-col items-center justify-center p-6 z-50">
      <h2 class="text-5xl md:text-6xl font-black text-cyan-400 mb-2 drop-shadow-[0_0_20px_rgba(34,211,238,0.8)] text-center animate-bounce">SYSTEM HACKED!</h2>
      <p class="text-zinc-300 text-lg mb-8 font-bold">全階層の掌握に成功しました</p>

      <div class="bg-black/80 border border-cyan-900/50 p-6 md:p-8 rounded-2xl w-full max-w-md mb-8 text-center shadow-[0_0_30px_rgba(34,211,238,0.2)]">
        <img :src="player.avatarUrl" class="w-24 h-24 mx-auto rounded-full border-4 border-cyan-500 mb-4 object-cover">
        <p class="font-bold text-xl mb-4 text-white">{{ player.name }}</p>
        
        <div class="space-y-2 text-left border-t border-zinc-800 pt-4 text-sm md:text-base">
          <div class="flex justify-between"><span class="text-zinc-400">クリア難易度:</span><span class="font-black text-white uppercase">{{ difficulty }}</span></div>
          <div class="flex justify-between"><span class="text-zinc-400">残りタイムボーナス:</span><span class="font-black text-white">{{ Math.max(0, player.timeLeft) }}s × 10</span></div>
          <div class="flex justify-between"><span class="text-zinc-400">未使用コインボーナス:</span><span class="font-black text-amber-400">{{ player.coins }}枚 × 200</span></div>
          <div class="flex justify-between mt-4 pt-4 border-t border-zinc-800"><span class="text-cyan-400 font-bold">TOTAL SCORE:</span><span class="font-black text-cyan-400 text-2xl">{{ (currentFloor * 1000) + (player.coins * 200) + (Math.max(0, player.timeLeft) * 10) + (difficulty === 'easy' ? 3000 : difficulty === 'normal' ? 5000 : 10000) }} pts</span></div>
        </div>
      </div>

      <button @click="submitScore()" class="px-10 py-4 bg-red-600 text-white font-black rounded-full hover:bg-red-500 shadow-[0_0_20px_rgba(239,68,68,0.5)] transition-all hover:-translate-y-1">
        スコアを記録してタイトルへ
      </button>
    </div>
  </div>
</template>

<style scoped>
/* 3Dグリッドの奥行きによる変形を表現 */
@keyframes wallSlide { 
  0% { transform: perspective(500px) rotateY(60deg) translateZ(0); }
  100% { transform: perspective(500px) rotateY(60deg) translateZ(-100px); }
}
.wall-back {
  animation: wallSlide 0.5s forwards;
}

/* タイプライターエフェクト */
.typewriter-log {
  overflow: hidden;
  white-space: nowrap;
  animation: typing 0.5s steps(40, end);
}

@keyframes typing {
  from { width: 0; }
  to { width: 100%; }
}
</style>