<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

// -----------------------------------------------------------------------------
// 型定義
// -----------------------------------------------------------------------------

type GameState =
  | 'title'
  | 'charmake'
  | 'explore'
  | 'event'
  | 'slot'
  | 'gameover'
  | 'clear'
  | 'dice_battle'

type Direction = 0 | 1 | 2 | 3
type Difficulty = 'easy' | 'normal' | 'hard'
type CharacterClass = 'knight' | 'mage' | 'thief' | 'cleric'

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

interface Song {
  embed_url?: string
  share_url?: string
  youtube_id?: string
  title?: string
}

interface EventDef {
  id: string
  title: string
  text: string
  type: 'positive' | 'negative' | 'gamble'
  effectType: string
  effectValue: number
}

interface Ranking {
  name: string
  score: number
  floor: number
  avatarUrl?: string
}

interface GalleryFolder {
  name: string
  images: {
    file: string
    enemy_name?: string
  }[]
}

interface GalleryImage {
  url: string
  enemyName: string
}

interface Reel {
  img: string
  interval: number | null
  isSpinning: boolean
}

interface BGMPlayer {
  setVolume: (volume: number) => void
  loadVideoById: (id: string) => void
  pauseVideo: () => void
  destroy: () => void
}

interface YouTubeAPI {
  Player: new (
    element: string,
    options: {
      videoId: string
      playerVars: Record<string, string | number>
      events: {
        onReady: (event: { target: BGMPlayer }) => void
      }
    }
  ) => BGMPlayer
}

interface YouTubeWindow extends Window {
  YT?: YouTubeAPI
  onYouTubeIframeAPIReady?: () => void
}

const DEFAULT_AVATAR = '/assets/images/icon.png'
const DEFAULT_EVENT_IMAGE = '/assets/images/erika-hero.jpg'
const FALLBACK_VIDEO_ID = 'xUboS2Fw1-o'

const dirOffsets: readonly (readonly [number, number])[] = [
  [0, -1],
  [1, 0],
  [0, 1],
  [-1, 0]
]

const directionArrows = ['↑', '→', '↓', '←']
const directionNames = ['北', '東', '南', '西']

function getOffset(dir: number): readonly [number, number] {
  return dirOffsets[dir] ?? [0, -1]
}

// -----------------------------------------------------------------------------
// 状態管理
// -----------------------------------------------------------------------------

const gameState = ref<GameState>('title')
const gameMode = ref<'oneshot' | 'endless'>('oneshot')
const difficulty = ref<Difficulty>('normal')
const currentFloor = ref(1)

const targetFloor = computed(() => {
  if (gameMode.value === 'endless') return Infinity
  return { easy: 3, normal: 5, hard: 10 }[difficulty.value]
})

const player = ref<Player>({
  name: '名無しのハッカー',
  avatarUrl: DEFAULT_AVATAR,
  hp: 100,
  maxHp: 100,
  timeLeft: 120,
  coins: 0,
  x: 1,
  y: 1,
  dir: 1
})

const isPlaying = computed(() =>
  ['explore', 'event', 'slot', 'dice_battle'].includes(gameState.value)
)

const hpPercentage = computed(() =>
  Math.max(
    0,
    Math.min(100, (player.value.hp / Math.max(1, player.value.maxHp)) * 100)
  )
)

const logMessages = ref<string[]>(['システムへのアクセスを待機中...'])
const mapGrid = ref<number[][]>([])
const visitedGrid = ref<boolean[][]>([])
const eventPool = ref<EventDef[]>([])
const galleryImagesPool = ref<GalleryImage[]>([])
const activeEvent = ref<{ image: string; def: EventDef } | null>(null)

const isFocusing = ref(false)
const isGenerating = ref(false)
const isSubmittingScore = ref(false)
const scoreSubmitError = ref('')

let disposed = false
let gameSessionId = 0
let timerInterval: number | null = null
let avatarController: AbortController | null = null
const pendingTimeouts = new Set<number>()

function addLog(message: string) {
  logMessages.value.unshift(message)
  if (logMessages.value.length > 5) logMessages.value.pop()
}

function scheduleGameAction(action: () => void, delay: number) {
  const sessionId = gameSessionId

  const id = window.setTimeout(() => {
    pendingTimeouts.delete(id)
    if (disposed || sessionId !== gameSessionId) return
    action()
  }, delay)

  pendingTimeouts.add(id)
}

function stopTimer() {
  if (timerInterval !== null) {
    window.clearInterval(timerInterval)
    timerInterval = null
  }
}

function clearGameTimers() {
  gameSessionId++
  stopTimer()

  pendingTimeouts.forEach(id => window.clearTimeout(id))
  pendingTimeouts.clear()

  reels.value.forEach(reel => {
    if (reel.interval !== null) window.clearInterval(reel.interval)
    reel.interval = null
    reel.isSpinning = false
  })

  isFocusing.value = false
  diceState.value.rolling = false
}

function startTimer() {
  stopTimer()

  timerInterval = window.setInterval(() => {
    // 文章・画像・戦闘演出を楽しめるよう、探索中だけ時間を減らす。
    if (gameState.value !== 'explore' || isFocusing.value) return

    player.value.timeLeft = Math.max(0, player.value.timeLeft - 1)
    if (player.value.timeLeft <= 0) triggerGameOver()
  }, 1000)
}

// -----------------------------------------------------------------------------
// データ読み込み
// -----------------------------------------------------------------------------

async function fetchEvents() {
  try {
    const res = await fetch('/assets/labyrinth_events.json')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const data = await res.json()
    if (!disposed && Array.isArray(data)) {
      eventPool.value = data
    }
  } catch (error) {
    console.error('イベントデータの読み込みに失敗しました。', error)
  }
}

async function fetchGalleryImages() {
  try {
    const res = await fetch('/assets/gallery.json')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const data: GalleryFolder[] = await res.json()
    if (disposed || !Array.isArray(data)) return

    const images: GalleryImage[] = []

    for (const folder of data) {
      if (!Array.isArray(folder.images)) continue

      for (const img of folder.images) {
        images.push({
          url: `/assets/images/gallery/${folder.name}/${img.file}`,
          enemyName:
            img.enemy_name && img.enemy_name !== 'ネームレス エリカ'
              ? img.enemy_name
              : '正体不明のデータ'
        })
      }
    }

    galleryImagesPool.value = images
  } catch (error) {
    console.error('ギャラリー画像の読み込みに失敗しました。', error)
  }
}

function randomItem<T>(items: readonly T[]): T | undefined {
  return items[Math.floor(Math.random() * items.length)]
}

// -----------------------------------------------------------------------------
// BGM
// -----------------------------------------------------------------------------

const thePillowsSongs = ref<Song[]>([])
let bgmPlayer: BGMPlayer | null = null
let bgmReady = false
let pendingVideoId: string | null = null
let youtubeReadyCallback: (() => void) | null = null
let previousYoutubeReadyCallback: (() => void) | undefined

function getVideoId(song?: Song): string {
  if (!song) return FALLBACK_VIDEO_ID

  if (song.youtube_id && /^[\w-]{11}$/.test(song.youtube_id)) {
    return song.youtube_id
  }

  for (const source of [song.embed_url, song.share_url]) {
    if (!source) continue
    if (/^[\w-]{11}$/.test(source)) return source

    try {
      const url = new URL(source)
      const parts = url.pathname.split('/').filter(Boolean)
      let candidate: string | null | undefined

      if (url.hostname === 'youtu.be') {
        candidate = parts[0]
      } else if (
        parts[0] === 'embed' ||
        parts[0] === 'shorts' ||
        parts[0] === 'live'
      ) {
        candidate = parts[1]
      } else {
        candidate = url.searchParams.get('v')
      }

      if (candidate && /^[\w-]{11}$/.test(candidate)) return candidate
    } catch {
      // 次のURL候補を試す。
    }
  }

  return FALLBACK_VIDEO_ID
}

function createBGMPlayer() {
  const ytWindow = window as YouTubeWindow
  if (disposed || bgmPlayer || !ytWindow.YT?.Player) return

  bgmPlayer = new ytWindow.YT.Player('bgm-player', {
    videoId: getVideoId(randomItem(thePillowsSongs.value)),
    playerVars: {
      playsinline: 1
    },
    events: {
      onReady: event => {
        if (disposed) return

        bgmReady = true
        event.target.setVolume(20)

        if (pendingVideoId && isPlaying.value) {
          event.target.loadVideoById(pendingVideoId)
          pendingVideoId = null
        }
      }
    }
  })
}

async function loadSongsAndInitBGM() {
  try {
    const res = await fetch('/assets/thepillows_releases_tab.json')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const data = await res.json()
    if (disposed) return
    if (Array.isArray(data)) thePillowsSongs.value = data
  } catch (error) {
    console.error('楽曲データの読み込みに失敗しました。', error)
  }

  if (disposed || thePillowsSongs.value.length === 0) return

  const ytWindow = window as YouTubeWindow

  if (ytWindow.YT?.Player) {
    createBGMPlayer()
    return
  }

  previousYoutubeReadyCallback = ytWindow.onYouTubeIframeAPIReady
  youtubeReadyCallback = () => {
    try {
      previousYoutubeReadyCallback?.()
    } finally {
      createBGMPlayer()
    }
  }
  ytWindow.onYouTubeIframeAPIReady = youtubeReadyCallback

  if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
    const tag = document.createElement('script')
    tag.src = 'https://www.youtube.com/iframe_api'
    document.head.appendChild(tag)
  }
}

function playRandomBGM() {
  const song = randomItem(thePillowsSongs.value)
  if (!song) return

  const id = getVideoId(song)

  if (!bgmPlayer || !bgmReady) {
    pendingVideoId = id
    return
  }

  bgmPlayer.setVolume(20)
  bgmPlayer.loadVideoById(id)
}

function setBGMVolume(volume: number) {
  if (bgmPlayer && bgmReady) bgmPlayer.setVolume(volume)
}

function stopBGM() {
  pendingVideoId = null
  if (bgmPlayer && bgmReady) bgmPlayer.pauseVideo()
}

// -----------------------------------------------------------------------------
// ランキング・スコア
// -----------------------------------------------------------------------------

const rankings = ref<Ranking[]>([])
const rankingError = ref('')

const clearBonus = computed(() => {
  if (gameState.value !== 'clear') return 0
  return { easy: 3000, normal: 5000, hard: 10000 }[difficulty.value]
})

const displayedScore = computed(
  () =>
    currentFloor.value * 1000 +
    player.value.coins * 200 +
    Math.max(0, player.value.timeLeft) * 10 +
    clearBonus.value
)

async function fetchRankings() {
  rankingError.value = ''

  try {
    const res = await fetch('/api/ranking')
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const data = await res.json()
    if (disposed) return
    if (!Array.isArray(data)) throw new Error('ランキング形式が不正です。')

    rankings.value = data.slice(0, 5)
  } catch (error) {
    if (disposed) return
    rankingError.value = 'ランキングを取得できませんでした。'
    console.error(error)
  }
}

async function submitScore() {
  if (
    isSubmittingScore.value ||
    !['gameover', 'clear'].includes(gameState.value)
  ) return

  isSubmittingScore.value = true
  scoreSubmitError.value = ''

  try {
    const res = await fetch('/api/ranking', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: player.value.name,
        score: displayedScore.value,
        floor: currentFloor.value,
        avatarUrl: player.value.avatarUrl
      })
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    if (disposed) return

    await fetchRankings()
    if (!disposed) gameState.value = 'title'
  } catch (error) {
    if (!disposed) {
      scoreSubmitError.value =
        'スコアを登録できませんでした。通信状態を確認して再試行してください。'
    }
    console.error(error)
  } finally {
    if (!disposed) isSubmittingScore.value = false
  }
}

// -----------------------------------------------------------------------------
// キャラクター作成
// -----------------------------------------------------------------------------

const charName = ref('')
const charGender = ref('girl')
const charHairColor = ref('black')
const charHairStyle = ref('bob')
const charClass = ref<CharacterClass>('knight')

async function startDive() {
  if (isGenerating.value || gameState.value !== 'charmake') return

  clearGameTimers()
  stopBGM()

  const sessionId = gameSessionId
  isGenerating.value = true
  scoreSubmitError.value = ''
  activeEvent.value = null

  player.value.name = charName.value.trim() || '名無しの冒険者'
  player.value.avatarUrl = DEFAULT_AVATAR

  avatarController?.abort()
  const controller = new AbortController()
  avatarController = controller

  try {
    const classPrompts: Record<CharacterClass, string> = {
      knight: 'in heavy armor, holding a sword, dark dungeon background',
      mage: 'holding a glowing staff, wearing robes, magical aura',
      thief: 'with a dagger, hooded cloak, stealthy stance',
      cleric: 'holding a holy symbol, divine light'
    }

    const basePrompt =
      'masterpiece, best quality, ultra_detailed, very aesthetic, illustration, 1person, solo'

    const prompt =
      `${basePrompt}, 1 ${charGender.value}, ` +
      `${charHairColor.value} hair, ${charHairStyle.value} hair, ` +
      `fantasy RPG, ${classPrompts[charClass.value]}`

    const res = await fetch('/api/generate-avatar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
      signal: controller.signal
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const data = await res.json()

    if (
      !disposed &&
      sessionId === gameSessionId &&
      typeof data.avatarUrl === 'string' &&
      data.avatarUrl
    ) {
      player.value.avatarUrl = data.avatarUrl
    }
  } catch (error) {
    if (!controller.signal.aborted) {
      console.error('アバター生成失敗。デフォルト画像を使用します。', error)
    }
  } finally {
    if (avatarController === controller) avatarController = null
    isGenerating.value = false
  }

  if (disposed || sessionId !== gameSessionId) return

  if (gameMode.value === 'endless') {
    player.value.maxHp = 50
    player.value.timeLeft = 120
  } else {
    const settings = {
      easy: { hp: 75, time: 180 },
      normal: { hp: 50, time: 120 },
      hard: { hp: 40, time: 90 }
    }[difficulty.value]

    player.value.maxHp = settings.hp
    player.value.timeLeft = settings.time
  }

  player.value.hp = player.value.maxHp
  player.value.coins = 0
  player.value.x = 1
  player.value.y = 1
  player.value.dir = 1

  currentFloor.value = 1
  mapGrid.value = generateMaze(1)
  revealNearbyCells()

  diceState.value = {
    enemyName: '',
    enemyImage: '',
    playerDice: 0,
    enemyDice: 0,
    message: '',
    rolling: false
  }

  reels.value.forEach((reel, index) => {
    reel.img = slotImages[index] ?? slotImages[0]
  })
  slotMessage.value = 'コインを消費してスロットを回せます。'

  logMessages.value = ['システムにダイブしました。探索を開始します。']
  gameState.value = 'explore'

  playRandomBGM()
  startTimer()
}

// -----------------------------------------------------------------------------
// 3D演出：サイドウォール
// -----------------------------------------------------------------------------
function sideWallStyle(depth: number, side: 'left' | 'right') {
  const near = depth * 12.5
  const far = (depth + 1) * 12.5

  const points =
    side === 'left'
      ? [
          `${near}% ${near}%`,
          `${far}% ${far}%`,
          `${far}% ${100 - far}%`,
          `${near}% ${100 - near}%`
        ]
      : [
          `${100 - near}% ${near}%`,
          `${100 - far}% ${far}%`,
          `${100 - far}% ${100 - far}%`,
          `${100 - near}% ${100 - near}%`
        ]

  const darkness = Math.min(0.65, 0.12 + depth * 0.15)

  return {
    clipPath: `polygon(${points.join(', ')})`,
    backgroundColor: '#292524',
    backgroundImage:
      `linear-gradient(rgba(0, 0, 0, ${darkness}), rgba(0, 0, 0, ${darkness})), ` +
      'url("/assets/images/stone_wall.webp")',
    backgroundRepeat: 'no-repeat, repeat',
    backgroundSize: '100% 100%, 128px 128px',
    zIndex: depthLayer(depth, 1)
  }
}

function frontWallStyle(depth: number) {
  const inset = depth * 12.5

  return {
    top: `${inset}%`,
    right: `${inset}%`,
    bottom: `${inset}%`,
    left: `${inset}%`,
    zIndex: depthLayer(depth, 3)
  }
}

// -----------------------------------------------------------------------------
// 迷路生成・移動・ミニマップ
// -----------------------------------------------------------------------------

function generateMaze(floor: number): number[][] {
  const size = Math.min(31, 15 + Math.floor(floor) * 4)
  const maze: number[][] = Array.from(
    { length: size },
    () => Array<number>(size).fill(1)
  )

  const read = (x: number, y: number) => maze[y]?.[x] ?? 1
  const write = (x: number, y: number, value: number) => {
    const row = maze[y]
    if (row && x >= 0 && x < row.length) row[x] = value
  }

  function dig(x: number, y: number) {
    write(x, y, 0)

    const dirs: [number, number][] = [
      [0, -2],
      [2, 0],
      [0, 2],
      [-2, 0]
    ]

    for (let i = dirs.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      const a = dirs[i]!
      dirs[i] = dirs[j]!
      dirs[j] = a
    }

    for (const [dx, dy] of dirs) {
      const nx = x + dx
      const ny = y + dy

      if (
        nx > 0 && nx < size - 1 &&
        ny > 0 && ny < size - 1 &&
        read(nx, ny) === 1
      ) {
        write(x + dx / 2, y + dy / 2, 0)
        dig(nx, ny)
      }
    }
  }

  dig(1, 1)

  const passages: { x: number; y: number }[] = []

  for (let y = 1; y < size - 1; y++) {
    for (let x = 1; x < size - 1; x++) {
      if (read(x, y) === 0 && !(x === 1 && y === 1)) {
        passages.push({ x, y })
      }
    }
  }

  const exit = passages.pop()
  if (exit) write(exit.x, exit.y, 3)

  for (let i = passages.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    const a = passages[i]!
    passages[i] = passages[j]!
    passages[j] = a
  }

  const eventCount = Math.min(
    passages.length,
    Math.max(8, Math.round(passages.length * 0.10))
  )
  for (const cell of passages.slice(0, eventCount)) {
    write(cell.x, cell.y, 2)
  }

  // 出口の配置後も必ず初期化する。
  visitedGrid.value = Array.from(
    { length: size },
    () => Array<boolean>(size).fill(false)
  )

  const startRow = visitedGrid.value[1]
  if (startRow) startRow[1] = true

  return maze
}

function getCell(x: number, y: number): number {
  return mapGrid.value[y]?.[x] ?? 1
}

function revealNearbyCells() {
  const { x, y } = player.value
  const cells: [number, number][] = [
    [x, y],
    [x, y - 1],
    [x + 1, y],
    [x, y + 1],
    [x - 1, y]
  ]

  for (const [cx, cy] of cells) {
    const row = visitedGrid.value[cy]
    if (row && cx >= 0 && cx < row.length) row[cx] = true
  }
}

const frontCell = computed(() => {
  const [dx, dy] = getOffset(player.value.dir)
  return getCell(player.value.x + dx, player.value.y + dy)
})

function turnLeft() {
  if (gameState.value !== 'explore' || isFocusing.value) return
  player.value.dir = ((player.value.dir + 3) % 4) as Direction
}

function turnRight() {
  if (gameState.value !== 'explore' || isFocusing.value) return
  player.value.dir = ((player.value.dir + 1) % 4) as Direction
}

function moveForward() {
  if (
    gameState.value !== 'explore' ||
    isFocusing.value ||
    frontCell.value === 1
  ) return

  const [dx, dy] = getOffset(player.value.dir)
  player.value.x += dx
  player.value.y += dy
  player.value.hp = Math.max(0, player.value.hp - 1)

  revealNearbyCells()

  if (player.value.hp <= 0) {
    triggerGameOver()
    return
  }

  checkCurrentCell()
}

function viewCell(depth: number, side = 0): number {
  const [dx, dy] = getOffset(player.value.dir)
  const [sx, sy] = getOffset((player.value.dir + 1) % 4)

  return getCell(
    player.value.x + dx * depth + sx * side,
    player.value.y + dy * depth + sy * side
  )
}

const sightLimit = computed(() => {
  for (let depth = 0; depth <= 3; depth++) {
    if (viewCell(depth) === 1) return depth
  }
  return 3
})

function checkCurrentCell() {
  const cell = getCell(player.value.x, player.value.y)

  if (cell === 2) {
    const row = mapGrid.value[player.value.y]

    if (row) {
      row[player.value.x] = 0
    }

    triggerEvent()
    return
  }

  if (cell !== 3) return

  if (
    gameMode.value === 'oneshot' &&
    currentFloor.value >= targetFloor.value
  ) {
    // 最終階層では実際の残り時間でクリアスコアを計算する。
    triggerClear()
    return
  }

  addLog(`第${currentFloor.value}層を突破！`)

  // 次の階層に向けて時間を回復する。
  // スロット前に回復するので、その後の時間ボーナスも残る。
  restoreFloorTime()

  slotMessage.value =
    '階層突破！コインを使って次の探索に備えられます。'

  gameState.value = 'slot'
}

const hpWarningClass = computed(() => {
  if (!isPlaying.value) return ''

  if (hpPercentage.value <= 25) {
    return 'hp-warning--critical'
  }

  if (hpPercentage.value <= 50) {
    return 'hp-warning--low'
  }

  return ''
})

// -----------------------------------------------------------------------------
// 集中モード
// -----------------------------------------------------------------------------

function useFocusMode() {
  if (gameState.value !== 'explore' || isFocusing.value) return

  if (player.value.hp >= player.value.maxHp) {
    addLog('HPは十分に回復しています。')
    return
  }

  if (player.value.timeLeft <= 10) {
    addLog('残り時間が少なくて集中できません！')
    return
  }

  isFocusing.value = true
  player.value.timeLeft -= 10
  setBGMVolume(60)
  addLog('the pillowsの曲に没入した...（時間10秒を消費してHP回復）')

  scheduleGameAction(() => {
    if (gameState.value === 'explore') {
      player.value.hp = Math.min(player.value.maxHp, player.value.hp + 40)
    }

    isFocusing.value = false
    setBGMVolume(20)
  }, 1500)
}

const floorTimeLimit = computed(() => {
  if (gameMode.value === 'endless') return 120

  return {
    easy: 180,
    normal: 120,
    hard: 90
  }[difficulty.value]
})

function restoreFloorTime() {
  const before = player.value.timeLeft

  player.value.timeLeft = Math.max(
    before,
    floorTimeLimit.value
  )

  const recovered = player.value.timeLeft - before

  if (recovered > 0) {
    addLog(
      `階層突破ボーナス！時間が${recovered}秒回復しました。`
    )
  }
}

// -----------------------------------------------------------------------------
// イベント
// -----------------------------------------------------------------------------

function triggerEvent() {
  const enemy = randomItem(galleryImagesPool.value)
  const event = randomItem(eventPool.value)

  if (enemy && (Math.random() > 0.5 || !event)) {
    diceState.value = {
      enemyName: enemy.enemyName,
      enemyImage: enemy.url,
      playerDice: 0,
      enemyDice: 0,
      message: `${enemy.enemyName} が立ち塞がった！`,
      rolling: false
    }

    gameState.value = 'dice_battle'
    addLog(`[遭遇] ${enemy.enemyName}`)
    return
  }

  if (event) {
    player.value.coins += 1
    activeEvent.value = {
      image: randomItem(galleryImagesPool.value)?.url ?? DEFAULT_EVENT_IMAGE,
      def: event
    }

    gameState.value = 'event'
    addLog(`[遭遇] ${event.title}`)
    return
  }

  player.value.coins += 1
  addLog('残されたデータからコインを1枚見つけた。')
}

function applyEventEffect(def: EventDef) {
  const p = player.value
  const val = Number(def.effectValue)

  if (!Number.isFinite(val)) {
    addLog('イベントの効果データが不正です。')
    return
  }

  switch (def.effectType) {
    case 'heal_hp_fixed':
      p.hp = Math.max(0, Math.min(p.maxHp, p.hp + val))
      addLog(`HPが ${val} 回復した。`)
      break

    case 'sub_hp_percent': {
      const damage = Math.floor(p.maxHp * (val / 100))
      p.hp = Math.max(0, p.hp - damage)
      addLog(`システム負荷によりHPを ${damage} 失った。`)
      break
    }

    case 'add_time_fixed':
      p.timeLeft = Math.max(0, p.timeLeft + val)
      addLog(`制限時間が ${val}秒 延長された。`)
      break

    case 'sub_time_fixed':
      p.timeLeft = Math.max(0, p.timeLeft - val)
      addLog(`トラップにより制限時間を ${val}秒 失った。`)
      break

    case 'warp_forward': {
      const steps = Math.min(
        Math.max(0, Math.floor(val)),
        mapGrid.value.length
      )
      const [dx, dy] = getOffset(p.dir)
      let moved = 0

      for (let i = 0; i < steps; i++) {
        const nx = p.x + dx
        const ny = p.y + dy
        const cell = getCell(nx, ny)

        if (cell === 1) break

        p.x = nx
        p.y = ny
        moved++
        revealNearbyCells()

        if (cell === 2 || cell === 3) break
      }

      addLog(
        moved > 0
          ? `空間をスキップして ${moved}マス 前進した。`
          : '前方が壁のため、ワープできなかった。'
      )
      break
    }

    case 'random_hp_or_damage':
      if (Math.random() > 0.5) {
        p.hp = p.maxHp
        addLog('管理者権限の取得に成功！HPが全回復した。')
      } else {
        p.hp = Math.max(0, p.hp - val)
        addLog(`アクセス拒否！カウンター攻撃でHPを ${val} 失った。`)
      }
      break

    default:
      console.warn('不明な effectType:', def.effectType)
      break
  }
}

function closeEvent() {
  if (gameState.value !== 'event' || !activeEvent.value) return

  const def = activeEvent.value.def

  // 先に消すことで、同じイベントの二重適用を防ぐ。
  activeEvent.value = null

  // イベントの効果は必ず適用する。
  applyEventEffect(def)

  if (player.value.hp <= 0 || player.value.timeLeft <= 0) {
    triggerGameOver()
    return
  }

  gameState.value = 'explore'

  // ワープ先が出口やイベントなら、その処理へ進む。
  if (def.effectType === 'warp_forward') {
    checkCurrentCell()
  }
}

// -----------------------------------------------------------------------------
// ダイス戦
// -----------------------------------------------------------------------------

const diceState = ref({
  enemyName: '',
  enemyImage: '',
  playerDice: 0,
  enemyDice: 0,
  message: '',
  rolling: false
})

function rollDice() {
  if (gameState.value !== 'dice_battle' || diceState.value.rolling) return

  diceState.value.rolling = true
  diceState.value.playerDice = 0
  diceState.value.enemyDice = 0
  diceState.value.message = 'サイコロを振っています...'

  scheduleGameAction(() => {
    if (gameState.value !== 'dice_battle') return

    const pDice = Math.floor(Math.random() * 6) + 1
    const eDice = Math.floor(Math.random() * 6) + 1

    diceState.value.playerDice = pDice
    diceState.value.enemyDice = eDice

    if (pDice > eDice) {
      player.value.coins += 1
      diceState.value.message = '勝利！ 無傷で突破！ コインを1枚獲得！'
      addLog(`ダイス勝利！ あなた:${pDice} 敵:${eDice} / コイン+1`)

      scheduleGameAction(() => {
        if (gameState.value !== 'dice_battle') return
        diceState.value.rolling = false
        gameState.value = 'explore'
      }, 900)

      return
    }

    if (pDice === eDice) {
      diceState.value.message = '引き分け！ ダメージなし。もう一度勝負！'
      diceState.value.rolling = false
      addLog(`ダイス引き分け！ あなた:${pDice} 敵:${eDice}`)
      return
    }

    player.value.hp = Math.max(0, player.value.hp - eDice)
    diceState.value.message =
      `敗北！ ${eDice}ダメージ。再挑戦するか、コインで突破できます。`
    addLog(`ダイス敗北！ あなた:${pDice} 敵:${eDice} / HP-${eDice}`)

    if (player.value.hp <= 0) {
      triggerGameOver()
      return
    }

    diceState.value.rolling = false
  }, 700)
}

function escapeDiceBattle() {
  if (
    gameState.value !== 'dice_battle' ||
    diceState.value.rolling ||
    player.value.coins < 1
  ) return

  player.value.coins -= 1
  addLog('コインを1枚消費して敵を突破した。')
  gameState.value = 'explore'
}

// -----------------------------------------------------------------------------
// スロット
// -----------------------------------------------------------------------------

const slotImages = [
  '/assets/images/s.webp',
  '/assets/images/a.webp',
  '/assets/images/b.webp',
  '/assets/images/c.webp'
] as const

const reels = ref<Reel[]>([
  { img: slotImages[0], interval: null, isSpinning: false },
  { img: slotImages[1], interval: null, isSpinning: false },
  { img: slotImages[2], interval: null, isSpinning: false }
])

const slotMessage = ref('コインを消費してスロットを回せます。')
const isAllStopped = computed(() =>
  reels.value.every(reel => !reel.isSpinning)
)

function startSlot() {
  if (gameState.value !== 'slot' || !isAllStopped.value) return

  if (player.value.coins <= 0) {
    slotMessage.value = 'コインが足りません！'
    return
  }

  player.value.coins -= 1
  slotMessage.value = 'タイミングを見計らってストップ！'

  reels.value.forEach(reel => {
    if (reel.interval !== null) window.clearInterval(reel.interval)

    reel.isSpinning = true
    reel.interval = window.setInterval(() => {
      reel.img = randomItem(slotImages) ?? slotImages[0]
    }, 50)
  })
}

function stopReel(index: number) {
  if (gameState.value !== 'slot') return

  const reel = reels.value[index]
  if (!reel?.isSpinning) return

  if (reel.interval !== null) window.clearInterval(reel.interval)
  reel.interval = null
  reel.isSpinning = false

  if (isAllStopped.value) evaluateSlot()
}

function evaluateSlot() {
  const [r1, r2, r3] = reels.value.map(reel => reel.img)
  if (!r1 || !r2 || !r3) return

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

function depthLayer(depth: number, offset = 0) {
  return 100 - depth * 10 + offset
}

function sceneObjectStyle(depth: number, verticalOffset: number) {
  return {
    zIndex: depthLayer(depth, 2),
    transform:
      `scale(${1 - depth * 0.2}) ` +
      `translateY(${depth * verticalOffset}px)`
  }
}

function proceedToNextFloor() {
  if (gameState.value !== 'slot' || !isAllStopped.value) return

  currentFloor.value++
  player.value.x = 1
  player.value.y = 1
  player.value.dir = 1

  mapGrid.value = generateMaze(currentFloor.value)
  revealNearbyCells()

  slotMessage.value = 'コインを消費してスロットを回せます。'
  gameState.value = 'explore'
  addLog(`第${currentFloor.value}層へ到達。さらに深く潜ります。`)

  playRandomBGM()
}

// -----------------------------------------------------------------------------
// 終了処理
// -----------------------------------------------------------------------------

function triggerGameOver() {
  if (gameState.value === 'gameover' || gameState.value === 'clear') return

  player.value.hp = Math.max(0, player.value.hp)
  player.value.timeLeft = Math.max(0, player.value.timeLeft)
  gameState.value = 'gameover'
  activeEvent.value = null
  scoreSubmitError.value = ''

  clearGameTimers()
  stopBGM()
  addLog('システムから切断されました。')
}

function triggerClear() {
  if (gameState.value === 'gameover' || gameState.value === 'clear') return

  gameState.value = 'clear'
  activeEvent.value = null
  scoreSubmitError.value = ''

  clearGameTimers()
  stopBGM()
  addLog('最終階層を突破！ システムの掌握に成功しました。')
}

function horizontalSurfaceStyle(
  depth: number,
  surface: 'floor' | 'ceiling'
) {
  const near = depth * 12.5
  const far = (depth + 1) * 12.5

  const points =
    surface === 'floor'
      ? [
          `${near}% ${100 - near}%`,
          `${far}% ${100 - far}%`,
          `${100 - far}% ${100 - far}%`,
          `${100 - near}% ${100 - near}%`
        ]
      : [
          `${near}% ${near}%`,
          `${100 - near}% ${near}%`,
          `${100 - far}% ${far}%`,
          `${far}% ${far}%`
        ]

  const darkness = Math.min(
    0.85,
    (surface === 'floor' ? 0.12 : 0.4) + depth * 0.16
  )

  return {
    clipPath: `polygon(${points.join(', ')})`,
    zIndex: depthLayer(depth),
    '--surface-darkness': String(darkness),
    '--tile-size': `${Math.max(16, 64 - depth * 14)}px`
  }
}

// -----------------------------------------------------------------------------
// ライフサイクル
// -----------------------------------------------------------------------------

onMounted(() => {
  void fetchRankings()
  void loadSongsAndInitBGM()
  void fetchEvents()
  void fetchGalleryImages()
})

onUnmounted(() => {
  disposed = true
  avatarController?.abort()
  avatarController = null

  clearGameTimers()
  stopBGM()

  if (bgmPlayer) {
    bgmPlayer.destroy()
    bgmPlayer = null
  }
  bgmReady = false

  const ytWindow = window as YouTubeWindow
  if (
    youtubeReadyCallback &&
    ytWindow.onYouTubeIframeAPIReady === youtubeReadyCallback
  ) {
    if (previousYoutubeReadyCallback) {
      ytWindow.onYouTubeIframeAPIReady = previousYoutubeReadyCallback
    } else {
      delete ytWindow.onYouTubeIframeAPIReady
    }
  }
})
</script>

<template>
  <div class="labyrinth-root bg-zinc-950 text-white font-mono flex flex-col pt-16">
    <div
      id="bgm-player"
      class="absolute -top-[9999px] -left-[9999px] w-[1px] h-[1px] overflow-hidden"
    ></div>

    <!-- タイトル -->
    <div
      v-if="gameState === 'title'"
      class="absolute inset-0 bg-zinc-950 flex flex-col items-center p-4 md:p-6 z-30 overflow-y-auto"
    >
      <div class="w-full max-w-md flex flex-col items-center py-6 md:py-10">
        <h1
          class="text-4xl md:text-6xl font-black text-erika mb-2 tracking-widest drop-shadow-[0_0_15px_rgba(243,156,18,0.5)] text-center"
        >
          ERIKA LABYRINTH
        </h1>
        <p class="text-zinc-400 mb-8 tracking-[0.3em] text-sm md:text-base text-center">
          Cyber Dungeon Explorer
        </p>

        <div
          class="bg-black/60 border border-zinc-700 p-4 rounded-2xl mb-6 w-full flex flex-col gap-4 shadow-xl"
        >
          <div class="flex bg-zinc-900 rounded-lg p-1">
            <button
              @click="gameMode = 'oneshot'"
              :class="gameMode === 'oneshot' ? 'bg-erika text-black shadow-md' : 'text-zinc-400 hover:text-white'"
              class="flex-1 py-2 font-bold rounded-md transition-all text-sm md:text-base"
            >
              1回クリア
            </button>
            <button
              @click="gameMode = 'endless'"
              :class="gameMode === 'endless' ? 'bg-erika text-black shadow-md' : 'text-zinc-400 hover:text-white'"
              class="flex-1 py-2 font-bold rounded-md transition-all text-sm md:text-base"
            >
              エンドレス
            </button>
          </div>

          <div v-if="gameMode === 'oneshot'" class="flex gap-2">
            <button
              @click="difficulty = 'easy'"
              :class="difficulty === 'easy' ? 'bg-cyan-500 text-black shadow-md' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'"
              class="flex-1 py-2 rounded-lg font-bold text-xs md:text-sm transition-all"
            >
              Easy<br><span class="text-[10px]">3 Floor</span>
            </button>
            <button
              @click="difficulty = 'normal'"
              :class="difficulty === 'normal' ? 'bg-emerald-500 text-black shadow-md' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'"
              class="flex-1 py-2 rounded-lg font-bold text-xs md:text-sm transition-all"
            >
              Normal<br><span class="text-[10px]">5 Floor</span>
            </button>
            <button
              @click="difficulty = 'hard'"
              :class="difficulty === 'hard' ? 'bg-red-500 text-white shadow-md' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'"
              class="flex-1 py-2 rounded-lg font-bold text-xs md:text-sm transition-all"
            >
              Hard<br><span class="text-[10px]">10 Floor</span>
            </button>
          </div>

          <div v-else class="text-center py-2 text-sm text-amber-400 font-bold">
            限界まで潜り続けるサバイバルモード
          </div>

          <p class="text-xs text-zinc-400 leading-relaxed">
            移動でHPを消費します。集中で時間10秒をHPに変換できます。
            イベント・戦闘・スロット中は時間が止まります。
          </p>
        </div>

        <button
          @click="gameState = 'charmake'"
          class="w-full py-4 bg-erika text-black font-black text-xl rounded-full shadow-[0_0_20px_rgba(243,156,18,0.5)] hover:bg-amber-400 hover:-translate-y-1 transition-all mb-8"
        >
          DIVE INTO SYSTEM
        </button>

        <div
          class="bg-zinc-900/80 backdrop-blur-md border border-zinc-700 w-full p-6 rounded-2xl shadow-xl"
        >
          <h2 class="text-xl font-bold text-white mb-4 border-b border-zinc-700 pb-2 text-center">
            TOP HACKERS
          </h2>

          <p v-if="rankingError" class="text-sm text-amber-300 text-center">
            {{ rankingError }}
          </p>
          <p v-else-if="rankings.length === 0" class="text-sm text-zinc-400 text-center">
            ランキングはまだありません。
          </p>

          <div class="space-y-3">
            <div
              v-for="(rank, i) in rankings"
              :key="`${i}-${rank.name}`"
              class="flex justify-between items-center bg-black/50 p-3 rounded-lg border border-zinc-800"
            >
              <div class="flex items-center gap-3 min-w-0">
                <span class="text-erika font-black w-4 text-lg">{{ i + 1 }}</span>
                <span class="font-bold text-zinc-200 truncate max-w-[120px]">
                  {{ rank.name }}
                </span>
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

    <!-- キャラクター作成 -->
    <div
      v-else-if="gameState === 'charmake'"
      class="absolute inset-0 bg-zinc-950 flex flex-col items-center p-6 z-30 overflow-y-auto"
    >
      <div class="w-full max-w-md my-auto py-6">
        <h2 class="text-3xl font-black text-white mb-8 tracking-widest text-center">
          INITIALIZE AVATAR
        </h2>

        <div
          class="bg-zinc-900/80 backdrop-blur-md p-6 rounded-2xl border border-zinc-700 shadow-xl"
        >
          <label for="hacker-name" class="block text-sm font-bold text-zinc-400 mb-2">
            HACKER NAME
          </label>
          <input
            id="hacker-name"
            v-model="charName"
            :disabled="isGenerating"
            type="text"
            maxlength="40"
            placeholder="名無しの冒険者"
            class="w-full bg-black border border-zinc-700 rounded-lg px-4 py-3 text-white mb-6 focus:border-erika outline-none transition-colors"
          >

          <fieldset :disabled="isGenerating" class="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label for="char-gender" class="block text-sm font-bold text-zinc-400 mb-2">
                性別
              </label>
              <select
                id="char-gender"
                v-model="charGender"
                class="w-full bg-black border border-zinc-700 rounded-lg p-3 text-white outline-none focus:border-erika"
              >
                <option value="girl">女性</option>
                <option value="boy">男性</option>
              </select>
            </div>
            <div>
              <label for="char-hair-color" class="block text-sm font-bold text-zinc-400 mb-2">
                髪色
              </label>
              <select
                id="char-hair-color"
                v-model="charHairColor"
                class="w-full bg-black border border-zinc-700 rounded-lg p-3 text-white outline-none focus:border-erika"
              >
                <option value="black">黒</option>
                <option value="blonde">金</option>
                <option value="silver">銀/白</option>
                <option value="red">赤</option>
                <option value="blue">青</option>
              </select>
            </div>
            <div>
              <label for="char-hair-style" class="block text-sm font-bold text-zinc-400 mb-2">
                髪型
              </label>
              <select
                id="char-hair-style"
                v-model="charHairStyle"
                class="w-full bg-black border border-zinc-700 rounded-lg p-3 text-white outline-none focus:border-erika"
              >
                <option value="short">ショート</option>
                <option value="bob">ボブ</option>
                <option value="long">ロング</option>
                <option value="ponytail">ポニーテール</option>
              </select>
            </div>
            <div>
              <label for="char-class" class="block text-sm font-bold text-zinc-400 mb-2">
                職業
              </label>
              <select
                id="char-class"
                v-model="charClass"
                class="w-full bg-black border border-zinc-700 rounded-lg p-3 text-white outline-none focus:border-erika"
              >
                <option value="knight">騎士 (Knight)</option>
                <option value="mage">魔術師 (Mage)</option>
                <option value="thief">盗賊 (Thief)</option>
                <option value="cleric">聖職者 (Cleric)</option>
              </select>
            </div>
          </fieldset>

          <button
            @click="startDive"
            :disabled="isGenerating"
            class="w-full px-4 py-4 bg-amber-600 text-white font-black text-lg rounded-full shadow-[0_0_20px_rgba(217,119,6,0.5)] hover:bg-amber-500 disabled:opacity-50 transition-all flex justify-center items-center gap-2"
          >
            <span v-if="isGenerating" class="animate-spin">🌀</span>
            {{ isGenerating ? 'GENERATING...' : 'GENERATE & DIVE' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ゲーム中ヘッダー -->
    <header
      v-if="isPlaying"
      class="shrink-0 bg-zinc-900 border-b border-zinc-700 p-3 md:p-4 flex justify-between items-center gap-3 shadow-lg z-10"
    >
      <div class="min-w-0">
        <p class="text-sm text-zinc-400">
          FLOOR {{ currentFloor }}
          <span v-if="gameMode === 'oneshot'"> / {{ targetFloor }}</span>
        </p>
        <p class="font-bold flex items-center gap-2">
          <img
            :src="player.avatarUrl"
            alt="Avatar"
            class="w-6 h-6 rounded-full border border-zinc-500 object-cover"
          >
          <span class="truncate">{{ player.name }}</span>
        </p>
      </div>

      <div class="flex gap-3 md:gap-6 text-right shrink-0">
        <div>
          <p class="text-xs text-zinc-400">
            TIME
            <span v-if="gameState !== 'explore' || isFocusing" class="text-amber-300">
              ⏸
            </span>
          </p>
          <p
            class="text-lg md:text-xl font-black"
            :class="player.timeLeft < 30 ? 'text-red-400 animate-pulse' : 'text-cyan-400'"
          >
            {{ player.timeLeft }}s
          </p>
        </div>
        <div>
          <p class="text-xs text-zinc-400">HP</p>
          <p class="text-lg md:text-xl font-black text-emerald-400">
            {{ player.hp }} / {{ player.maxHp }}
          </p>
        </div>
        <div>
          <p class="text-xs text-zinc-400">COIN</p>
          <p class="text-lg md:text-xl font-black text-amber-400">
            {{ player.coins }}
          </p>
        </div>
      </div>
    </header>

    <main v-if="isPlaying" class="flex-1 min-h-0 relative flex flex-col">
      <!-- 探索 -->
      <div
        v-if="gameState === 'explore'"
        class="flex-1 min-h-0 flex flex-col bg-black overflow-hidden"
      >
        <div class="relative flex-1 min-h-0 overflow-hidden flex items-center justify-center bg-zinc-950">

          <div class="dungeon-scene relative w-full max-w-lg aspect-square flex items-center justify-center">
            <template v-for="depth in [3, 2, 1, 0]" :key="depth">
              <template v-if="depth <= sightLimit">
                <template v-if="viewCell(depth) !== 1">
                    <div
                        class="dungeon-surface dungeon-floor"
                        :style="horizontalSurfaceStyle(depth, 'floor')"
                    ></div>

                    <div
                        class="dungeon-surface dungeon-ceiling"
                        :style="horizontalSurfaceStyle(depth, 'ceiling')"
                    ></div>
                </template>
                <div
                  v-if="viewCell(depth) === 3"
                  class="absolute flex items-end justify-center transition-all duration-300"
                  :style="sceneObjectStyle(depth, 10)"
                >
                  <img
                    src="/assets/images/door.webp"
                    class="w-32 h-48 object-contain drop-shadow-[0_0_15px_rgba(0,0,0,0.8)]"
                    alt="出口"
                  >
                </div>

                <div
                  v-if="viewCell(depth) === 2"
                  class="absolute flex items-center justify-center transition-all duration-300"
                  :style="sceneObjectStyle(depth, 20)"
                >
                  <img
                    src="/assets/images/treasure.webp"
                    class="w-24 h-24 object-contain animate-bounce drop-shadow-[0_0_15px_#f59e0b]"
                    alt="イベント"
                  >
                </div>

                <div
                    v-if="viewCell(depth) === 1"
                    class="dungeon-front-wall"
                    :style="frontWallStyle(depth)"
                    >
                    <img
                        src="/assets/images/deadend.webp"
                        alt="行き止まり"
                        class="dungeon-front-wall__image"
                        draggable="false"
                    >
                </div>

                <!-- 左側の壁 -->
                <div
                    v-if="viewCell(depth, -1) === 1"
                    class="absolute inset-0 pointer-events-none"
                    :style="sideWallStyle(depth, 'left')"
                ></div>

                <div
                    v-if="viewCell(depth, 1) === 1"
                    class="absolute inset-0 pointer-events-none"
                    :style="sideWallStyle(depth, 'right')"
                ></div>
              </template>
            </template>
          </div>

          <!-- ミニマップは奥行きループの外で1回だけ描画 -->
          <div class="absolute top-3 right-3 z-20">
            <p class="text-right text-xs text-amber-300 mb-1">
              {{ directionNames[player.dir] }} {{ directionArrows[player.dir] }}
            </p>
            <div
              class="w-32 h-32 bg-black/85 border border-stone-500 rounded-lg p-1 shadow-[0_0_15px_rgba(0,0,0,0.8)]"
            >
              <div
                v-for="(row, y) in mapGrid"
                :key="y"
                class="flex"
                :style="{ height: `${100 / mapGrid.length}%` }"
              >
                <div
                  v-for="(cell, x) in row"
                  :key="x"
                  class="relative flex-1 flex items-center justify-center"
                  :class="
                    x === player.x && y === player.y
                      ? 'bg-amber-500 z-10'
                      : !visitedGrid[y]?.[x]
                        ? 'bg-transparent'
                        : cell === 3
                          ? 'bg-cyan-500'
                          : cell === 2
                            ? 'bg-yellow-400'
                            : cell === 1
                              ? 'bg-stone-500'
                              : 'bg-stone-800'
                  "
                >
                  <span
                    v-if="x === player.x && y === player.y"
                    class="absolute text-white text-[11px] leading-none font-black drop-shadow"
                  >
                    {{ directionArrows[player.dir] }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作パネル -->
        <div class="relative shrink-0 bg-zinc-900 border-t-4 border-stone-700 p-2 z-20">
          <div class="max-w-2xl mx-auto flex gap-2 md:gap-4">
            <div class="flex-1 min-w-0 bg-black border-2 border-stone-600 rounded-lg p-2 flex items-center gap-2 md:gap-3">
              <img
                :src="player.avatarUrl"
                alt="Avatar"
                class="w-12 h-12 md:w-20 md:h-20 rounded-md border border-stone-500 object-cover shrink-0"
              >
              <div class="flex-1 min-w-0">
                <p class="font-bold text-white text-sm md:text-base truncate">
                  {{ player.name }}
                </p>
                <div class="w-full bg-red-950 h-3 rounded-full mt-1 border border-red-900 overflow-hidden">
                  <div
                    class="bg-red-500 h-full transition-all duration-300"
                    :style="{ width: `${hpPercentage}%` }"
                  ></div>
                </div>
                <p class="text-xs text-red-300 mt-1">
                  HP: {{ player.hp }} / {{ player.maxHp }}
                </p>
              </div>
            </div>

            <div class="w-32 md:w-48 shrink-0 grid grid-cols-3 gap-1">
              <button
                @click="moveForward"
                :disabled="frontCell === 1 || isFocusing"
                aria-label="前進"
                class="col-start-2 w-full h-10 md:h-12 bg-stone-700 hover:bg-stone-600 border border-stone-500 rounded font-bold disabled:opacity-30 active:translate-y-1 transition-all"
              >
                ▲
              </button>
              <button
                @click="turnLeft"
                :disabled="isFocusing"
                aria-label="左を向く"
                class="col-start-1 row-start-2 w-full h-10 md:h-12 bg-stone-700 hover:bg-stone-600 border border-stone-500 rounded font-bold disabled:opacity-30 active:translate-y-1 transition-all"
              >
                ◀
              </button>
              <button
                @click="useFocusMode"
                :disabled="isFocusing || player.timeLeft <= 10 || player.hp >= player.maxHp"
                title="時間10秒を消費してHPを40回復"
                class="col-start-2 row-start-2 bg-stone-800 text-amber-500 border border-amber-700 rounded text-xs font-bold hover:bg-amber-900 disabled:opacity-30 transition-all"
              >
                集中
              </button>
              <button
                @click="turnRight"
                :disabled="isFocusing"
                aria-label="右を向く"
                class="col-start-3 row-start-2 w-full h-10 md:h-12 bg-stone-700 hover:bg-stone-600 border border-stone-500 rounded font-bold disabled:opacity-30 active:translate-y-1 transition-all"
              >
                ▶
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- イベント -->
      <div
        v-else-if="gameState === 'event' && activeEvent"
        class="absolute inset-0 bg-black/90 flex flex-col p-4 md:p-6 z-20 overflow-y-auto"
      >
        <h2 class="text-2xl font-black text-center text-erika mb-2">
          SYSTEM INTERCEPT
        </h2>
        <p class="text-xs text-center text-amber-300 mb-3">探索タイマー停止中</p>

        <div class="flex-1 flex items-center justify-center p-2">
          <img
            :src="activeEvent.image"
            alt="Erika"
            class="max-w-full max-h-48 md:max-h-64 rounded-lg border-2 border-white/20 shadow-[0_0_30px_rgba(243,156,18,0.3)] object-contain"
          >
        </div>

        <div class="shrink-0 bg-zinc-900 border border-zinc-700 p-4 rounded-xl mt-4">
          <p
            class="font-bold text-lg mb-2"
            :class="
              activeEvent.def.type === 'positive'
                ? 'text-emerald-400'
                : activeEvent.def.type === 'gamble'
                  ? 'text-amber-400'
                  : 'text-red-400'
            "
          >
            {{ activeEvent.def.title }}
          </p>
          <p class="text-zinc-300 mb-4 text-sm md:text-base">
            {{ activeEvent.def.text }}
          </p>
          <button
            @click="closeEvent"
            class="w-full py-3 bg-erika text-black font-bold rounded-lg hover:bg-amber-400"
          >
            確認して進む
          </button>
        </div>
      </div>

      <!-- ダイス戦 -->
      <div
        v-else-if="gameState === 'dice_battle'"
        class="absolute inset-0 bg-black/95 flex flex-col p-4 md:p-6 z-20 overflow-y-auto"
      >
        <h2 class="text-2xl font-black text-center text-red-500 mb-2">
          SYSTEM INTERCEPT
        </h2>
        <p class="text-center font-bold mb-2" aria-live="polite">
          {{ diceState.message }}
        </p>
        <p class="text-xs text-center text-amber-300 mb-3">探索タイマー停止中</p>

        <div class="flex-1 flex flex-col items-center justify-center gap-3">
          <img
            :src="diceState.enemyImage"
            alt="Enemy"
            class="max-w-full max-h-40 md:max-h-56 rounded-lg border-2 border-red-500/50 shadow-[0_0_30px_rgba(239,68,68,0.3)] object-contain"
          >
          <p class="text-xl font-bold text-red-400">{{ diceState.enemyName }}</p>

          <div class="flex justify-center gap-8 w-full max-w-sm">
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

        <div class="shrink-0 mt-4 w-full max-w-sm mx-auto space-y-3">
          <p class="text-center text-xs text-zinc-400">
            勝利：無傷＋コイン1枚 ／ 引き分け：ダメージなし
          </p>
          <button
            @click="rollDice"
            :disabled="diceState.rolling"
            class="w-full py-3 bg-red-600 text-white font-black text-xl rounded-lg hover:bg-red-500 disabled:opacity-50 transition-all"
          >
            {{ diceState.rolling ? '判定中...' : 'サイコロを振る' }}
          </button>
          <button
            @click="escapeDiceBattle"
            :disabled="diceState.rolling || player.coins < 1"
            class="w-full py-3 bg-zinc-800 text-amber-300 font-bold rounded-lg border border-amber-700 hover:bg-zinc-700 disabled:opacity-40 transition-all"
          >
            コイン1枚で突破する（所持 {{ player.coins }}枚）
          </button>
        </div>
      </div>

      <!-- スロット -->
      <div
        v-else-if="gameState === 'slot'"
        class="absolute inset-0 bg-zinc-900 flex flex-col items-center p-4 md:p-6 z-20 overflow-y-auto"
      >
        <div class="my-auto w-full max-w-md flex flex-col items-center py-4">
          <h2 class="text-4xl font-black text-erika mb-2 drop-shadow-[0_0_10px_rgba(243,156,18,0.5)]">
            ERIKA SLOTS
          </h2>
          <p class="text-zinc-400 font-bold mb-2">
            所持コイン:
            <span class="text-2xl text-amber-400">{{ player.coins }}</span> 枚
          </p>
          <p class="text-xs text-amber-300 mb-4">探索タイマー停止中</p>

          <div
            class="bg-black border border-zinc-700 w-full p-4 rounded-xl mb-6 text-center font-bold min-h-[4rem]"
            aria-live="polite"
          >
            {{ slotMessage }}
          </div>

          <div class="flex gap-2 md:gap-4 mb-6">
            <div
              v-for="(reel, index) in reels"
              :key="index"
              class="flex flex-col items-center gap-3"
            >
              <div
                class="w-20 h-20 md:w-28 md:h-28 bg-black border-4 rounded-xl overflow-hidden shadow-[0_0_20px_rgba(0,0,0,0.8)]"
                :class="reel.isSpinning ? 'border-erika' : 'border-zinc-600'"
              >
                <img
                  :src="reel.img"
                  alt="Slot Image"
                  class="w-full h-full object-cover"
                  :class="{ 'opacity-80 blur-[2px]': reel.isSpinning }"
                >
              </div>
              <button
                @click="stopReel(index)"
                :disabled="!reel.isSpinning"
                class="w-full py-2 bg-zinc-800 text-white font-bold rounded-lg border border-zinc-600 hover:bg-zinc-700 disabled:opacity-30"
              >
                STOP
              </button>
            </div>
          </div>

          <div class="flex flex-col gap-4 w-full max-w-sm">
            <button
              @click="startSlot"
              :disabled="player.coins <= 0 || !isAllStopped"
              class="w-full py-4 bg-erika text-black font-black text-xl rounded-full shadow-[0_0_15px_rgba(243,156,18,0.4)] hover:bg-amber-400 disabled:opacity-30 disabled:bg-zinc-800 disabled:text-zinc-500 disabled:shadow-none transition-all"
            >
              スロットを回す (1 Coin)
            </button>
            <button
              @click="proceedToNextFloor"
              :disabled="!isAllStopped"
              class="w-full py-3 bg-zinc-800 text-white font-bold rounded-full border border-zinc-600 hover:bg-zinc-700 disabled:opacity-30 transition-colors"
            >
              次の階層へ進む ▶
            </button>
          </div>
        </div>
      </div>
    </main>

    <!-- ログ -->
    <footer v-if="isPlaying" class="game-log">
        <div class="game-log__heading">
            <span>探索ログ</span>
            <span class="game-log__hint">最新の出来事が上に表示されます</span>
        </div>

        <div class="game-log__entries">
            <div
            v-for="(log, i) in logMessages"
            :key="`${i}-${log}`"
            class="game-log__entry"
            :class="{ 'game-log__entry--latest': i === 0 }"
            >
            <span class="game-log__marker" aria-hidden="true">
                {{ i === 0 ? '▶' : '・' }}
            </span>

            <span>{{ log }}</span>
            </div>
        </div>
    </footer>

    <!-- 集中モード -->
    <div
      v-if="isFocusing"
      class="absolute inset-0 bg-cyan-900/30 backdrop-blur-sm z-40 flex items-center justify-center p-6"
    >
      <p class="text-2xl md:text-3xl text-center font-black text-cyan-300 animate-pulse drop-shadow-[0_0_10px_cyan]">
        Listening to the pillows...
      </p>
    </div>

    <!-- ゲームオーバー -->
    <div
      v-if="gameState === 'gameover'"
      class="absolute inset-0 bg-red-950/90 backdrop-blur-sm flex flex-col items-center p-6 z-50 overflow-y-auto"
    >
      <div class="my-auto py-6 w-full max-w-md flex flex-col items-center">
        <h2 class="text-4xl md:text-6xl font-black text-red-500 mb-4 drop-shadow-[0_0_20px_rgba(239,68,68,0.8)] text-center">
          SYSTEM DOWN
        </h2>
        <p class="text-zinc-300 text-lg mb-8 text-center">
          コネクションが切断されました...
        </p>

        <div class="bg-black/80 border border-red-900/50 p-6 rounded-2xl w-full mb-6 text-center shadow-2xl">
          <img
            :src="player.avatarUrl"
            alt="Avatar"
            class="w-24 h-24 mx-auto rounded-full border-4 border-zinc-700 mb-4 object-cover"
          >
          <p class="font-bold text-xl mb-4 text-white">{{ player.name }}</p>
          <div class="grid grid-cols-2 gap-4 text-left border-t border-zinc-800 pt-4">
            <p class="text-zinc-400">到達階層:</p>
            <p class="font-black text-white text-right">Floor {{ currentFloor }}</p>
            <p class="text-zinc-400">収集コイン:</p>
            <p class="font-black text-amber-400 text-right">{{ player.coins }} 枚</p>
            <p class="text-zinc-400">残り時間:</p>
            <p class="font-black text-white text-right">{{ player.timeLeft }}秒 × 10</p>
            <p class="text-zinc-400">最終スコア:</p>
            <p class="font-black text-cyan-400 text-right text-2xl">
              {{ displayedScore }} pts
            </p>
          </div>
        </div>

        <p v-if="scoreSubmitError" class="text-red-200 text-sm mb-4 text-center" role="alert">
          {{ scoreSubmitError }}
        </p>
        <button
          @click="submitScore"
          :disabled="isSubmittingScore"
          class="w-full px-6 py-4 bg-red-600 text-white font-black rounded-full hover:bg-red-500 shadow-[0_0_20px_rgba(239,68,68,0.5)] transition-all hover:-translate-y-1 disabled:opacity-50"
        >
          {{ isSubmittingScore ? '記録中...' : 'スコアを記録してタイトルへ' }}
        </button>
      </div>
    </div>

    <!-- クリア -->
    <div
      v-if="gameState === 'clear'"
      class="absolute inset-0 bg-blue-950/90 backdrop-blur-sm flex flex-col items-center p-6 z-50 overflow-y-auto"
    >
      <div class="my-auto py-6 w-full max-w-md flex flex-col items-center">
        <h2 class="text-4xl md:text-6xl font-black text-cyan-400 mb-2 drop-shadow-[0_0_20px_rgba(34,211,238,0.8)] text-center animate-bounce">
          SYSTEM HACKED!
        </h2>
        <p class="text-zinc-300 mb-8 font-bold text-center">
          全階層の掌握に成功しました
        </p>

        <div class="bg-black/80 border border-cyan-900/50 p-6 rounded-2xl w-full mb-6 text-center shadow-[0_0_30px_rgba(34,211,238,0.2)]">
          <img
            :src="player.avatarUrl"
            alt="Avatar"
            class="w-24 h-24 mx-auto rounded-full border-4 border-cyan-500 mb-4 object-cover"
          >
          <p class="font-bold text-xl mb-4 text-white">{{ player.name }}</p>

          <div class="space-y-3 text-left border-t border-zinc-800 pt-4 text-sm md:text-base">
            <div class="flex justify-between gap-3">
              <span class="text-zinc-400">クリア難易度:</span>
              <span class="font-black text-white uppercase">{{ difficulty }}</span>
            </div>
            <div class="flex justify-between gap-3">
              <span class="text-zinc-400">階層ボーナス:</span>
              <span class="font-black text-white">{{ currentFloor }} × 1000</span>
            </div>
            <div class="flex justify-between gap-3">
              <span class="text-zinc-400">残りタイムボーナス:</span>
              <span class="font-black text-cyan-400">{{ player.timeLeft }}s × 10</span>
            </div>
            <div class="flex justify-between gap-3">
              <span class="text-zinc-400">未使用コインボーナス:</span>
              <span class="font-black text-amber-400">{{ player.coins }}枚 × 200</span>
            </div>
            <div class="flex justify-between gap-3">
              <span class="text-zinc-400">クリアボーナス:</span>
              <span class="font-black text-emerald-400">{{ clearBonus }} pts</span>
            </div>
            <div class="flex justify-between items-center gap-3 mt-4 pt-4 border-t border-zinc-800">
              <span class="text-cyan-400 font-bold">TOTAL SCORE:</span>
              <span class="font-black text-cyan-400 text-2xl">{{ displayedScore }} pts</span>
            </div>
          </div>
        </div>

        <p v-if="scoreSubmitError" class="text-red-200 text-sm mb-4 text-center" role="alert">
          {{ scoreSubmitError }}
        </p>
        <button
          @click="submitScore"
          :disabled="isSubmittingScore"
          class="w-full px-6 py-4 bg-red-600 text-white font-black rounded-full hover:bg-red-500 shadow-[0_0_20px_rgba(239,68,68,0.5)] transition-all hover:-translate-y-1 disabled:opacity-50"
        >
          {{ isSubmittingScore ? '記録中...' : 'スコアを記録してタイトルへ' }}
        </button>
      </div>
    </div>
  </div>
  <div
    v-if="hpWarningClass"
    class="hp-warning"
    :class="hpWarningClass"
    aria-hidden="true"
  ></div>
</template>

<style scoped>
.labyrinth-root {
  position: relative;
  height: 100vh;
  height: 100dvh;
  min-height: 480px;
  overflow: hidden;
}

.hp-warning {
  position: absolute;
  inset: 0;
  z-index: 45;
  pointer-events: none;

  background:
    radial-gradient(
      ellipse at top left,
      var(--warning-corner) 0%,
      transparent 65%
    ) top left / 38% 38% no-repeat,
    radial-gradient(
      ellipse at top right,
      var(--warning-corner) 0%,
      transparent 65%
    ) top right / 38% 38% no-repeat,
    radial-gradient(
      ellipse at bottom left,
      var(--warning-corner) 0%,
      transparent 65%
    ) bottom left / 38% 38% no-repeat,
    radial-gradient(
      ellipse at bottom right,
      var(--warning-corner) 0%,
      transparent 65%
    ) bottom right / 38% 38% no-repeat;

  box-shadow: inset 0 0 28px var(--warning-edge);
}

.hp-warning--low {
  --warning-corner: rgba(249, 115, 22, 0.48);
  --warning-edge: rgba(249, 115, 22, 0.28);
}

.hp-warning--critical {
  --warning-corner: rgba(239, 68, 68, 0.65);
  --warning-edge: rgba(239, 68, 68, 0.42);
}

.dungeon-scene {
  perspective: 800px;
}

button {
  touch-action: manipulation;
}

button:disabled {
  cursor: not-allowed;
}

.game-log {
  flex-shrink: 0;
  height: 132px;
  padding: 8px 12px;
  background: #09090b;
  border-top: 1px solid #52525b;
}

.game-log__heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  color: #f4f4f5;
  font-size: 12px;
  font-weight: 700;
}

.game-log__hint {
  color: #a1a1aa;
  font-size: 10px;
  font-weight: 400;
}

.game-log__entries {
  height: calc(100% - 24px);
  overflow-y: auto;
  scrollbar-gutter: stable;
}

.game-log__entry {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 5px 8px;
  color: #d4d4d8;
  font-size: 13px;
  line-height: 1.6;
  overflow-wrap: anywhere;
}

.game-log__entry--latest {
  color: #fff7ed;
  background: #292018;
  border-left: 3px solid #f59e0b;
  border-radius: 4px;
  font-weight: 700;
}

.game-log__marker {
  flex-shrink: 0;
  color: #f59e0b;
}

.dungeon-front-wall {
  position: absolute;
  overflow: hidden;
  background: #292524;
  pointer-events: none;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.5);
}

.dungeon-front-wall__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

/* ダンジョン内の前後関係を、この要素の中に閉じ込める。
   ミニマップや操作パネルより壁が前に出るのを防ぐ。 */
.dungeon-scene {
  isolation: isolate;
}

.dungeon-surface {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-color: #44403c;

  background-image:
    linear-gradient(
      rgba(0, 0, 0, var(--surface-darkness)),
      rgba(0, 0, 0, var(--surface-darkness))
    ),
    repeating-linear-gradient(
      0deg,
      transparent 0,
      transparent calc(var(--tile-size) - 2px),
      #1c1917 calc(var(--tile-size) - 2px),
      #1c1917 var(--tile-size)
    ),
    repeating-linear-gradient(
      90deg,
      transparent 0,
      transparent calc(var(--tile-size) - 2px),
      #1c1917 calc(var(--tile-size) - 2px),
      #1c1917 var(--tile-size)
    );
}

.dungeon-ceiling {
  background-color: #292524;
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation: none !important;
    transition: none !important;
  }
}
</style>