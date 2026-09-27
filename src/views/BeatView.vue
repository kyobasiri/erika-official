<script setup lang="ts">
import {
  computed,
  onMounted,
  onUnmounted,
  ref,
  shallowRef,
  watch
} from 'vue'

type Difficulty = 'veryeasy' | 'easy' | 'normal' | 'hard'
type GameState = 'select' | 'loading' | 'countdown' | 'playing' | 'paused' | 'result'
type Judge = 'perfect' | 'great' | 'good' | 'miss'
type SongFilter = 'all' | 'favorite' | 'played' | 'unplayed' | 'fullcombo' | 'unfinished'

interface Song {
  id: string
  title: string
}

interface Note {
  id: number
  time: number
  lane: number
  hit: boolean
  miss: boolean
}

interface VisibleNote {
  id: number
  lane: number
  y: number
}

interface PlayRecord {
  bestAccuracy: number
  maxCombo: number
  fullCombo: boolean
  allPerfect: boolean
  playCount: number
  lastPlayedAt: string
  lastNoteCount: number
}

interface Settings {
  offset: number
  fallTime: number
  musicVolume: number
  seVolume: number
  effects: 'low' | 'normal' | 'high'
}

interface SaveData {
  version: 1
  records: Record<string, PlayRecord>
  favorites: string[]
  settings: Settings
}

interface Player {
  cueVideoById(options: { videoId: string; startSeconds: number }): void
  playVideo(): void
  pauseVideo(): void
  stopVideo(): void
  destroy(): void
  getCurrentTime(): number
  getDuration(): number
  getPlayerState(): number
  getPlaybackRate(): number
  setPlaybackRate(rate: number): void
  setVolume(volume: number): void
}

interface PlayerEvent {
  data: number
  target: Player
}

interface YouTubeAPI {
  Player: new (
    element: HTMLElement,
    options: {
      width: string
      height: string
      playerVars: Record<string, string | number>
      events: {
        onReady: (event: PlayerEvent) => void
        onStateChange: (event: PlayerEvent) => void
        onError: (event: PlayerEvent) => void
        onAutoplayBlocked: () => void
        onPlaybackRateChange: (event: PlayerEvent) => void
      }
    }
  ) => Player
}

type YouTubeWindow = Window & {
  YT?: YouTubeAPI
  onYouTubeIframeAPIReady?: () => void
  __erikaBeatApiPromise?: Promise<YouTubeAPI>
}

const STORAGE_KEY = 'erika-beat-save-musical-v3'
const DIFFICULTIES: Difficulty[] = [
  'veryeasy',
  'easy',
  'normal',
  'hard'
]
const JUDGE_LINE = 80
const PERFECT_MS = 50
const GREAT_MS = 100
const GOOD_MS = 200
const COUNTDOWN_MS = 3000

const defaultSettings: Settings = {
  offset: 0,
  fallTime: 1500,
  musicVolume: 50,
  seVolume: 30,
  effects: 'normal'
}

const gameState = ref<GameState>('select')
const songs = ref<Song[]>([])
const selectedSong = ref<Song | null>(null)
const difficulty = ref<Difficulty>('normal')
const searchText = ref('')
const songFilter = ref<SongFilter>('all')
const filterDifficulty = ref<Difficulty>('normal')
const songsLoading = ref(true)
const errorMessage = ref('')
const storageMessage = ref('')
const playerHost = ref<HTMLElement | null>(null)
const importInput = ref<HTMLInputElement | null>(null)

const settings = ref<Settings>({ ...defaultSettings })
const records = ref<Record<string, PlayRecord>>({})
const favorites = ref<string[]>([])

const visibleNotes = shallowRef<VisibleNote[]>([])
const totalNotes = ref(0)
const combo = ref(0)
const maxCombo = ref(0)
const score = ref<Record<Judge, number>>({
  perfect: 0,
  great: 0,
  good: 0,
  miss: 0
})

const fastCount = ref(0)
const slowCount = ref(0)
const meanTiming = ref(0)
const timingDeviation = ref(0)
const resultNewRecord = ref(false)
const previousBest = ref<number | null>(null)

const laneFlashes = ref([false, false])
const popup = ref<{
  id: number
  text: string
  color: string
  timing: string
} | null>(null)

const hitEffects = ref<Array<{
  id: number
  lane: number
  perfect: boolean
}>>([])

const activeCutin = ref<{
  id: number
  img: string
  text: string
  large: boolean
} | null>(null)

const countdown = ref(3)
const buffering = ref(false)
const autoplayBlocked = ref(false)
const loadingLabel = ref('準備中…')
const playbackSeconds = ref(0)
const durationSeconds = ref(0)

let player: Player | null = null
let playerReadyPromise: Promise<Player> | null = null
let rejectPlayerReady: ((error: Error) => void) | null = null
let cancelCue: (() => void) | null = null
let resolveCue: (() => void) | null = null

let disposed = false
let storageLoaded = false
let sessionId = 0
let sessionActive = false
let playbackRequested = false
let frameId = 0
let effectId = 0
let chartController: AbortController | null = null
let songsController: AbortController | null = null

let notes: Note[] = []
let laneNotes: Note[][] = [[], []]
let laneHeads = [0, 0]
let renderHead = 0
let previousRenderTime = -Infinity
let timingSamples: number[] = []
let consecutiveMisses = 0
let lastEncouragementAt = -Infinity

let lastMediaMs: number | null = null
let lastClockMs = 0
let clockWasPlaying = false

const timers = new Set<ReturnType<typeof setTimeout>>()
const flashTimers: Array<ReturnType<typeof setTimeout> | null> = [null, null]
let popupTimer: ReturnType<typeof setTimeout> | null = null
let cutinTimer: ReturnType<typeof setTimeout> | null = null
let loadingTimer: ReturnType<typeof setTimeout> | null = null

let sePool: HTMLAudioElement[] = []
let seIndex = 0

const judgedCount = computed(() =>
  score.value.perfect +
  score.value.great +
  score.value.good +
  score.value.miss
)

const earnedPoints = computed(() =>
  score.value.perfect * 100 +
  score.value.great * 50 +
  score.value.good * 10
)

const liveAccuracy = computed(() =>
  judgedCount.value > 0 ? earnedPoints.value / judgedCount.value : 0
)

const finalAccuracy = computed(() =>
  totalNotes.value > 0 ? earnedPoints.value / totalNotes.value : 0
)

const progressPercent = computed(() =>
  durationSeconds.value > 0
    ? Math.min(100, playbackSeconds.value / durationSeconds.value * 100)
    : 0
)

const fullCombo = computed(() =>
  totalNotes.value > 0 &&
  judgedCount.value === totalNotes.value &&
  score.value.miss === 0
)

const allPerfect = computed(() =>
  totalNotes.value > 0 && score.value.perfect === totalNotes.value
)

const showBoard = computed(() =>
  ['countdown', 'playing', 'paused'].includes(gameState.value) ||
  (gameState.value === 'loading' && totalNotes.value > 0)
)

const savedPlayedSongs = computed(() => {
  const ids = new Set(
    Object.entries(records.value)
      .filter(([, record]) => record.playCount > 0)
      .map(([key]) => key.split(':')[0])
  )
  return ids.size
})

const filteredSongs = computed(() => {
  const query = searchText.value.trim().toLocaleLowerCase()
  const favoriteSet = new Set(favorites.value)

  return songs.value.filter(song => {
    if (query && !song.title.toLocaleLowerCase().includes(query)) return false

    const record = getRecord(song.id, filterDifficulty.value)

    switch (songFilter.value) {
      case 'favorite':
        return favoriteSet.has(song.id)
      case 'played':
        return !!record?.playCount
      case 'unplayed':
        return !record?.playCount
      case 'fullcombo':
        return !!record?.fullCombo
      case 'unfinished':
        return !record?.fullCombo
      default:
        return true
    }
  })
})

const resultRank = computed(() => {
  if (allPerfect.value) {
    return {
      rank: 'S',
      text: 'オールパーフェクト！素晴らしいビートでした。',
      img: '/assets/images/s.webp'
    }
  }
  if (finalAccuracy.value >= 95 && fullCombo.value) {
    return {
      rank: 'S',
      text: '最高のセッションでしたね！',
      img: '/assets/images/s.webp'
    }
  }
  if (finalAccuracy.value >= 80) {
    return {
      rank: 'A',
      text: '安定していますね。流石です。',
      img: '/assets/images/a.webp'
    }
  }
  if (finalAccuracy.value >= 50) {
    return {
      rank: 'B',
      text: 'いいビートでした。次も楽しみにしています。',
      img: '/assets/images/b.webp'
    }
  }
  return {
    rank: 'C',
    text: 'お疲れ様です。ご自身のペースで楽しみましょう。',
    img: '/assets/images/c.webp'
  }
})

const suggestedOffset = computed(() => {
  const value = settings.value.offset + meanTiming.value
  return Math.max(-300, Math.min(300, Math.round(value / 5) * 5))
})

function later(callback: () => void, delay: number) {
  const timer = setTimeout(() => {
    timers.delete(timer)
    if (!disposed) callback()
  }, delay)
  timers.add(timer)
  return timer
}

function cancelTimer(timer: ReturnType<typeof setTimeout> | null) {
  if (timer === null) return
  clearTimeout(timer)
  timers.delete(timer)
}

function clearLoadingTimer() {
  cancelTimer(loadingTimer)
  loadingTimer = null
}

function cancelFrame() {
  cancelAnimationFrame(frameId)
  frameId = 0
}

function recordKey(id: string, diff: Difficulty) {
  return `${id}:${diff}`
}

function getRecord(id: string, diff: Difficulty) {
  return records.value[recordKey(id, diff)]
}

function isFavorite(id: string) {
  return favorites.value.includes(id)
}

function toggleFavorite(id: string) {
  favorites.value = isFavorite(id)
    ? favorites.value.filter(value => value !== id)
    : [...favorites.value, id]
  persistSave()
}

function isObject(value: unknown): value is Record<string, unknown> {
  return !!value && typeof value === 'object' && !Array.isArray(value)
}

function boundedNumber(
  value: unknown,
  fallback: number,
  minimum: number,
  maximum: number
) {
  return typeof value === 'number' && Number.isFinite(value)
    ? Math.max(minimum, Math.min(maximum, value))
    : fallback
}

function parseSettings(value: unknown): Settings {
  const source = isObject(value) ? value : {}

  return {
    offset: Math.round(boundedNumber(source.offset, 0, -300, 300)),
    fallTime: Math.round(boundedNumber(source.fallTime, 1500, 800, 2500)),
    musicVolume: Math.round(boundedNumber(source.musicVolume, 50, 0, 100)),
    seVolume: Math.round(boundedNumber(source.seVolume, 30, 0, 100)),
    effects: source.effects === 'low' || source.effects === 'high'
      ? source.effects
      : 'normal'
  }
}

function parseSave(value: unknown): SaveData {
  if (
    !isObject(value) ||
    value.version !== 1 ||
    !isObject(value.records) ||
    !Array.isArray(value.favorites)
  ) {
    throw new Error('ERIKA BEATの保存データではありません。')
  }

  const parsedRecords: Record<string, PlayRecord> = {}
  const entries = Object.entries(value.records)

  if (entries.length > 20000) {
    throw new Error('記録の件数が多すぎます。')
  }

  for (const [key, candidate] of entries) {
    if (
      !/^[A-Za-z0-9_-]{11}:(veryeasy|easy|normal|hard)$/.test(key) ||
      !isObject(candidate)
    ) {
      throw new Error('記録データの形式が不正です。')
    }

    const numericFields = [
      'bestAccuracy',
      'maxCombo',
      'playCount',
      'lastNoteCount'
    ]

    if (numericFields.some(field =>
      typeof candidate[field] !== 'number' ||
      !Number.isFinite(candidate[field]) ||
      (candidate[field] as number) < 0
    )) {
      throw new Error('記録に不正な数値が含まれています。')
    }

    if (
      (candidate.bestAccuracy as number) > 100 ||
      !Number.isInteger(candidate.maxCombo) ||
      !Number.isInteger(candidate.playCount) ||
      !Number.isInteger(candidate.lastNoteCount) ||
      (candidate.playCount as number) < 1 ||
      (candidate.lastNoteCount as number) < 1 ||
      (candidate.maxCombo as number) > 1000000 ||
      (candidate.lastNoteCount as number) > 1000000 ||
      (candidate.playCount as number) > 100000000 ||
      typeof candidate.fullCombo !== 'boolean' ||
      typeof candidate.allPerfect !== 'boolean' ||
      typeof candidate.lastPlayedAt !== 'string' ||
      !Number.isFinite(Date.parse(candidate.lastPlayedAt))
    ) {
      throw new Error('記録データの内容が不正です。')
    }

    parsedRecords[key] = {
      bestAccuracy: candidate.bestAccuracy as number,
      maxCombo: candidate.maxCombo as number,
      fullCombo: candidate.fullCombo || candidate.allPerfect,
      allPerfect: candidate.allPerfect,
      playCount: candidate.playCount as number,
      lastPlayedAt: new Date(candidate.lastPlayedAt).toISOString(),
      lastNoteCount: candidate.lastNoteCount as number
    }
  }

  if (
    value.favorites.length > 20000 ||
    value.favorites.some(id =>
      typeof id !== 'string' || !/^[A-Za-z0-9_-]{11}$/.test(id)
    )
  ) {
    throw new Error('お気に入りデータの形式が不正です。')
  }

  return {
    version: 1,
    records: parsedRecords,
    favorites: [...new Set(value.favorites as string[])],
    settings: parseSettings(value.settings)
  }
}

function buildSave(): SaveData {
  return {
    version: 1,
    records: records.value,
    favorites: favorites.value,
    settings: { ...settings.value }
  }
}

function persistSave() {
  if (!storageLoaded || disposed) return false

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(buildSave()))
    return true
  } catch {
    storageMessage.value =
      'ブラウザへ保存できませんでした。記録をJSONで書き出してください。'
    return false
  }
}

function loadSave() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const data = parseSave(JSON.parse(raw))
      records.value = data.records
      favorites.value = data.favorites
      settings.value = data.settings
    }
    storageLoaded = true
  } catch {
    storageMessage.value =
      '保存データを読み込めませんでした。既存データの上書きを停止しています。JSON読み込みで復元できます。'
    storageLoaded = false
  }
}

function exportSave() {
  const blob = new Blob(
    [JSON.stringify(buildSave(), null, 2)],
    { type: 'application/json' }
  )
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  const date = new Date().toISOString().replace(/[:.]/g, '-')

  anchor.href = url
  anchor.download = `erika-beat-save-${date}.json`
  document.body.appendChild(anchor)
  anchor.click()
  anchor.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

async function importSave(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''

  if (!file || gameState.value !== 'select') return

  try {
    if (file.size > 5 * 1024 * 1024) {
      throw new Error('読み込めるJSONは5MBまでです。')
    }

    const incoming = parseSave(JSON.parse(await file.text()))
    if (disposed || gameState.value !== 'select') return

    const merged = { ...records.value }

    for (const [key, imported] of Object.entries(incoming.records)) {
      const local = merged[key]

      if (!local) {
        merged[key] = imported
        continue
      }

      const latest = Date.parse(imported.lastPlayedAt) > Date.parse(local.lastPlayedAt)
        ? imported
        : local

      merged[key] = {
        bestAccuracy: Math.max(local.bestAccuracy, imported.bestAccuracy),
        maxCombo: Math.max(local.maxCombo, imported.maxCombo),
        fullCombo: local.fullCombo || imported.fullCombo,
        allPerfect: local.allPerfect || imported.allPerfect,
        // 同じバックアップを繰り返し読み込んでも回数を増やさない。
        playCount: Math.max(local.playCount, imported.playCount),
        lastPlayedAt: latest.lastPlayedAt,
        lastNoteCount: latest.lastNoteCount
      }
    }

    records.value = merged
    favorites.value = [...new Set([...favorites.value, ...incoming.favorites])]
    storageLoaded = true

    if (persistSave()) {
      storageMessage.value =
        '記録とお気に入りを統合しました。ベスト値・達成状態を保持し、完走回数は大きい方を採用しました。操作設定は現在の設定を維持しています。'
    }
  } catch (error) {
    storageMessage.value = error instanceof Error ? error.message : String(error)
  }
}

watch(settings, () => {
  persistSave()
  player?.setVolume(settings.value.musicVolume)
}, { deep: true })

function saveCompletedPlay() {
  if (!selectedSong.value || totalNotes.value === 0) return

  const key = recordKey(selectedSong.value.id, difficulty.value)
  const previous = records.value[key]
  const accuracy = finalAccuracy.value

  previousBest.value = previous?.bestAccuracy ?? null
  resultNewRecord.value =
    !previous || accuracy > previous.bestAccuracy + 0.000001

  records.value = {
    ...records.value,
    [key]: {
      bestAccuracy: Math.max(previous?.bestAccuracy ?? 0, accuracy),
      maxCombo: Math.max(previous?.maxCombo ?? 0, maxCombo.value),
      fullCombo: (previous?.fullCombo ?? false) || fullCombo.value,
      allPerfect: (previous?.allPerfect ?? false) || allPerfect.value,
      playCount: (previous?.playCount ?? 0) + 1,
      lastPlayedAt: new Date().toISOString(),
      lastNoteCount: totalNotes.value
    }
  }

  if (!storageLoaded) {
    storageMessage.value =
      '記録はこの画面内に保持しています。保存データの読み込みに問題があるため、JSONを書き出して保管してください。'
    return
  }

  persistSave()
}

function extractVideoId(value: unknown): string | null {
  if (typeof value !== 'string') return null

  try {
    const url = new URL(value)
    const host = url.hostname.toLowerCase()
    let id: string | null = null

    if (host === 'youtu.be') {
      id = url.pathname.split('/').filter(Boolean)[0] ?? null
    } else if (
      [
        'youtube.com',
        'www.youtube.com',
        'm.youtube.com',
        'youtube-nocookie.com',
        'www.youtube-nocookie.com'
      ].includes(host)
    ) {
      const parts = url.pathname.split('/').filter(Boolean)
      id = url.searchParams.get('v')
      if (!id && ['embed', 'shorts', 'live'].includes(parts[0] ?? '')) {
        id = parts[1] ?? null
      }
    }

    return id && /^[A-Za-z0-9_-]{11}$/.test(id) ? id : null
  } catch {
    return null
  }
}

function loadYouTubeAPI(): Promise<YouTubeAPI> {
  const win = window as YouTubeWindow

  if (win.YT?.Player) return Promise.resolve(win.YT)
  if (win.__erikaBeatApiPromise) return win.__erikaBeatApiPromise

  const promise = new Promise<YouTubeAPI>((resolve, reject) => {
    const previousCallback = win.onYouTubeIframeAPIReady
    let finished = false

    let script = document.querySelector<HTMLScriptElement>(
      'script[src="https://www.youtube.com/iframe_api"]'
    )
    const created = !script
    if (!script) script = document.createElement('script')
    const tag = script

    const cleanup = () => {
      clearTimeout(timeout)
      clearInterval(poll)
      tag.removeEventListener('error', onError)
      if (win.onYouTubeIframeAPIReady === onReady) {
        win.onYouTubeIframeAPIReady = previousCallback
      }
    }

    const finish = (error?: Error) => {
      if (finished || (!error && !win.YT?.Player)) return
      finished = true
      cleanup()

      if (error) {
        if (created) tag.remove()
        reject(error)
      } else {
        resolve(win.YT!)
      }
    }

    const onError = () =>
      finish(new Error('YouTube APIを読み込めませんでした。'))

    const onReady = () => {
      try {
        previousCallback?.()
      } finally {
        finish()
      }
    }

    const timeout = setTimeout(
      () => finish(new Error('YouTube APIの読み込みがタイムアウトしました。')),
      20000
    )
    const poll = setInterval(() => finish(), 100)

    win.onYouTubeIframeAPIReady = onReady
    tag.addEventListener('error', onError, { once: true })

    if (created) {
      tag.src = 'https://www.youtube.com/iframe_api'
      tag.async = true
      document.head.appendChild(tag)
    }

    finish()
  })

  win.__erikaBeatApiPromise = promise

  void promise.catch(() => {
    if (win.__erikaBeatApiPromise === promise) {
      delete win.__erikaBeatApiPromise
    }
  })

  return promise
}

async function ensurePlayer(): Promise<Player> {
  if (player) return player
  if (playerReadyPromise) return playerReadyPromise

  const pending = (async () => {
    const api = await loadYouTubeAPI()
    if (disposed || !playerHost.value) throw new Error('画面が閉じられました。')

    const mount = document.createElement('div')
    playerHost.value.replaceChildren(mount)

    return new Promise<Player>((resolve, reject) => {
      let instance: Player | null = null
      let settled = false

      const fail = (error: Error) => {
        if (settled) return
        settled = true
        clearTimeout(timeout)
        rejectPlayerReady = null
        instance?.destroy()
        reject(error)
      }

      const timeout = setTimeout(
        () => fail(new Error('プレーヤーの準備がタイムアウトしました。')),
        20000
      )

      rejectPlayerReady = fail

      try {
        instance = new api.Player(mount, {
          width: '100%',
          height: '100%',
          playerVars: {
            playsinline: 1,
            origin: window.location.origin,
            controls: 1,
            disablekb: 1
          },
          events: {
            onReady(event) {
              if (settled) return
              if (disposed) {
                fail(new Error('画面が閉じられました。'))
                return
              }

              settled = true
              clearTimeout(timeout)
              rejectPlayerReady = null
              player = event.target
              player.setVolume(settings.value.musicVolume)
              resolve(player)
            },
            onStateChange: handlePlayerState,
            onError(event) {
              const message = youtubeErrorMessage(event.data)
              if (!settled) fail(new Error(message))
              else if (sessionActive) failSession(message)
            },
            onAutoplayBlocked() {
              if (!sessionActive || !playbackRequested) return
              clearLoadingTimer()
              buffering.value = false
              autoplayBlocked.value = true
            },
            onPlaybackRateChange(event) {
              if (
                sessionActive &&
                playbackRequested &&
                Math.abs(event.data - 1) > 0.001
              ) {
                failSession('再生速度が変更されたため中断しました。等速で再プレイしてください。')
              }
            }
          }
        })
      } catch (error) {
        fail(error instanceof Error ? error : new Error(String(error)))
      }
    })
  })()

  playerReadyPromise = pending

  try {
    return await pending
  } finally {
    if (playerReadyPromise === pending) playerReadyPromise = null
  }
}

function youtubeErrorMessage(code: number) {
  const messages: Record<number, string> = {
    2: '動画IDまたは再生パラメーターが不正です。',
    5: 'この環境では動画を再生できません。',
    100: '動画が削除されているか、非公開です。',
    101: 'この動画は埋め込み再生が許可されていません。',
    150: 'この動画は埋め込み再生が許可されていません。',
    153: 'YouTubeが再生元を確認できません。Referer設定を確認してください。'
  }

  return messages[code] ?? `YouTube再生エラーが発生しました（${code}）。`
}

function resetEffects() {
  cancelTimer(popupTimer)
  cancelTimer(cutinTimer)
  flashTimers.forEach(cancelTimer)
  popupTimer = null
  cutinTimer = null
  flashTimers.fill(null)
  popup.value = null
  activeCutin.value = null
  hitEffects.value = []
  laneFlashes.value = [false, false]
}

function stopSession() {
  sessionActive = false
  playbackRequested = false
  cancelFrame()
  clearLoadingTimer()
  cancelCue?.()
  cancelCue = null
  resolveCue = null
  chartController?.abort()
  chartController = null
  buffering.value = false
  autoplayBlocked.value = false
  lastMediaMs = null
  clockWasPlaying = false
  resetEffects()

  try {
    player?.stopVideo()
  } catch {
    // プレーヤー破棄中などは無視する。
  }
}

function failSession(message: string) {
  sessionId++
  stopSession()
  visibleNotes.value = []
  errorMessage.value = message
  gameState.value = 'select'
}

function returnToSelect() {
  sessionId++
  stopSession()
  visibleNotes.value = []
  gameState.value = 'select'
}

function validateChart(
  data: unknown,
  songId: string,
  diff: Difficulty
): Note[] {
  if (!isObject(data) || !isObject(data.difficulties)) {
    throw new Error('譜面JSONの形式が不正です。')
  }
  if (data.id !== undefined && data.id !== songId) {
    throw new Error('動画IDと譜面IDが一致しません。')
  }

  const source = data.difficulties[diff]
  if (!Array.isArray(source) || !source.length || source.length > 1000000) {
    throw new Error(`${diff}の譜面がないか、ノーツ数が不正です。`)
  }

  const seen = new Set<string>()
  const parsed: Note[] = []

  for (const item of source) {
    if (
      !isObject(item) ||
      typeof item.time !== 'number' ||
      !Number.isFinite(item.time) ||
      item.time < 0 ||
      (item.lane !== 0 && item.lane !== 1)
    ) {
      throw new Error('譜面に不正な時刻またはレーンが含まれています。')
    }

    const key = `${item.time}:${item.lane}`
    if (seen.has(key)) continue
    seen.add(key)

    parsed.push({
      id: parsed.length,
      time: item.time,
      lane: item.lane,
      hit: false,
      miss: false
    })
  }

  return parsed.sort((a, b) => a.time - b.time || a.lane - b.lane)
}

function cueVideo(readyPlayer: Player, id: string) {
  return new Promise<void>((resolve, reject) => {
    let settled = false

    const finish = (error?: Error) => {
      if (settled) return
      settled = true
      clearTimeout(timeout)
      cancelCue = null
      resolveCue = null
      if (error) reject(error)
      else resolve()
    }

    const timeout = setTimeout(
      () => finish(new Error('動画の準備がタイムアウトしました。')),
      20000
    )

    cancelCue = () => finish(new Error('準備を中止しました。'))
    resolveCue = () => finish()

    try {
      readyPlayer.cueVideoById({ videoId: id, startSeconds: 0 })
    } catch (error) {
      finish(error instanceof Error ? error : new Error(String(error)))
    }
  })
}

async function startGame(song: Song, diff: Difficulty) {
  if (!['select', 'result'].includes(gameState.value)) return

  const token = ++sessionId
  stopSession()
  selectedSong.value = song
  difficulty.value = diff
  errorMessage.value = ''
  gameState.value = 'loading'
  loadingLabel.value = '譜面を読み込み中…'

  score.value = { perfect: 0, great: 0, good: 0, miss: 0 }
  combo.value = 0
  maxCombo.value = 0
  totalNotes.value = 0
  fastCount.value = 0
  slowCount.value = 0
  meanTiming.value = 0
  timingDeviation.value = 0
  resultNewRecord.value = false
  previousBest.value = null
  playbackSeconds.value = 0
  durationSeconds.value = 0
  visibleNotes.value = []

  notes = []
  laneNotes = [[], []]
  laneHeads = [0, 0]
  renderHead = 0
  previousRenderTime = -Infinity
  timingSamples = []
  consecutiveMisses = 0
  lastEncouragementAt = -Infinity

  const controller = new AbortController()
  chartController = controller
  const timeout = setTimeout(() => controller.abort(), 20000)

  try {
    let data: unknown

    try {
      const response = await fetch(
        `/assets/beatmaps/beatmap_${song.id}.json`,
        { signal: controller.signal }
      )

      if (!response.ok) {
        throw new Error(
          response.status === 404
            ? 'この曲の譜面はまだ用意されていません。'
            : `譜面を取得できませんでした（HTTP ${response.status}）。`
        )
      }

      data = await response.json()
    } finally {
      clearTimeout(timeout)
    }

    if (disposed || token !== sessionId) return
    const parsed = validateChart(data, song.id, diff)

    loadingLabel.value = 'YouTubeプレーヤーを準備中…'
    const readyPlayer = await ensurePlayer()
    if (disposed || token !== sessionId) return

    sessionActive = true
    readyPlayer.setVolume(settings.value.musicVolume)
    readyPlayer.setPlaybackRate(1)
    loadingLabel.value = '動画を準備中…'

    await cueVideo(readyPlayer, song.id)
    if (disposed || token !== sessionId) return

    if (document.hidden) {
      returnToSelect()
      return
    }

    notes = parsed
    totalNotes.value = notes.length
    laneNotes = [
      notes.filter(note => note.lane === 0),
      notes.filter(note => note.lane === 1)
    ]

    durationSeconds.value = readyPlayer.getDuration() || 0
    gameState.value = 'countdown'
    runCountdown(token)
  } catch (error) {
    if (disposed || token !== sessionId) return
    failSession(
      error instanceof Error && error.name === 'AbortError'
        ? '譜面の読み込みがタイムアウトしました。'
        : error instanceof Error ? error.message : String(error)
    )
  }
}

function runCountdown(token: number) {
  const start = performance.now()

  const tick = (now: number) => {
    if (disposed || token !== sessionId || !sessionActive) return

    const remaining = Math.max(0, COUNTDOWN_MS - (now - start))
    countdown.value = Math.max(1, Math.ceil(remaining / 1000))
    updateVisibleNotes(-remaining - settings.value.offset)

    if (remaining > 0) {
      frameId = requestAnimationFrame(tick)
    } else {
      frameId = 0
      gameState.value = 'loading'
      loadingLabel.value = '再生開始を待っています…'
      requestPlayback()
    }
  }

  frameId = requestAnimationFrame(tick)
}

function requestPlayback() {
  if (!sessionActive || !player) return
  if (document.hidden) {
    gameState.value = 'paused'
    return
  }

  playbackRequested = true
  autoplayBlocked.value = false
  buffering.value = true
  clearLoadingTimer()

  loadingTimer = later(() => {
    if (sessionActive && player?.getPlayerState() !== 1) {
      buffering.value = false
      autoplayBlocked.value = true
    }
  }, 12000)

  player.playVideo()
}

// 再生時刻を監視し、巻き戻し・早送りで記録が壊れるのを防ぐ。
// iframe時刻の更新揺らぎを考慮して、1.2秒の許容幅を持たせる。
function checkMediaClock(rawMs: number, nowPlaying: boolean) {
  const now = performance.now()

  if (lastMediaMs !== null) {
    const elapsed = clockWasPlaying ? Math.max(0, now - lastClockMs) : 0
    const delta = rawMs - lastMediaMs

    if (delta < -1200 || delta > elapsed + 1200) {
      failSession(
        '動画の再生位置が変更されたため中断しました。記録は保存していません。曲を選び直して再プレイしてください。'
      )
      return false
    }
  } else if (rawMs > 2000) {
    failSession('曲の先頭から再生できませんでした。もう一度お試しください。')
    return false
  }

  lastMediaMs = rawMs
  lastClockMs = now
  clockWasPlaying = nowPlaying
  return true
}

function handlePlayerState(event: PlayerEvent) {
  if (event.data === 5) resolveCue?.()

  if (!sessionActive || disposed) {
    if (event.data === 1) event.target.pauseVideo()
    return
  }

  if (event.data === 1) {
    if (!playbackRequested) {
      event.target.pauseVideo()
      return
    }

    if (document.hidden) {
      pauseGame()
      return
    }

    if (Math.abs(event.target.getPlaybackRate() - 1) > 0.001) {
      failSession('等速再生でプレイしてください。')
      return
    }

    if (!checkMediaClock(event.target.getCurrentTime() * 1000, true)) return

    clearLoadingTimer()
    autoplayBlocked.value = false
    buffering.value = false
    durationSeconds.value = event.target.getDuration() || 0
    gameState.value = 'playing'
    cancelFrame()
    frameId = requestAnimationFrame(updateGameLoop)
  } else if (event.data === 2 || event.data === 3) {
    cancelFrame()
    if (!playbackRequested) return
    if (!checkMediaClock(event.target.getCurrentTime() * 1000, false)) return

    if (event.data === 2) {
      buffering.value = false
      gameState.value = 'paused'
    } else {
      buffering.value = true
    }
  } else if (event.data === 0 && playbackRequested) {
    if (!checkMediaClock(event.target.getCurrentTime() * 1000, false)) return
    endGame()
  }
}

function pauseGame() {
  if (!sessionActive || !player || !playbackRequested) return
  cancelFrame()
  clearLoadingTimer()
  buffering.value = false
  gameState.value = 'paused'
  player.pauseVideo()
}

function handleVisibility() {
  if (!document.hidden) return
  if (gameState.value === 'countdown') {
    returnToSelect()
  } else if (sessionActive && playbackRequested) {
    pauseGame()
  }
}

function advanceLaneHead(lane: number) {
  const list = laneNotes[lane]
  while (
    laneHeads[lane] < list.length &&
    (list[laneHeads[lane]].hit || list[laneHeads[lane]].miss)
  ) {
    laneHeads[lane]++
  }
}

function processMisses(time: number) {
  let missed = 0

  for (let lane = 0; lane < 2; lane++) {
    advanceLaneHead(lane)
    const list = laneNotes[lane]

    while (laneHeads[lane] < list.length) {
      const note = list[laneHeads[lane]]
      if (time - note.time <= GOOD_MS) break

      note.miss = true
      score.value.miss++
      combo.value = 0
      consecutiveMisses++
      missed++
      advanceLaneHead(lane)
    }
  }

  if (missed > 0) {
    showPopup('MISS', 'text-red-400', '')

    if (
      consecutiveMisses >= 5 &&
      time - lastEncouragementAt >= 15000 &&
      settings.value.effects !== 'low'
    ) {
      lastEncouragementAt = time
      showCutin(
        '/assets/images/miss10.webp',
        '焦らず、曲をよく聴いてみましょう。',
        false
      )
    }
  }
}

function updateVisibleNotes(time: number) {
  if (time < previousRenderTime) renderHead = 0
  previousRenderTime = time

  while (
    renderHead < notes.length &&
    notes[renderHead].time < time - GOOD_MS
  ) {
    renderHead++
  }

  const visible: VisibleNote[] = []

  for (let i = renderHead; i < notes.length; i++) {
    const note = notes[i]
    if (note.time > time + settings.value.fallTime) break
    if (note.hit || note.miss) continue

    const y = JUDGE_LINE -
      (note.time - time) / settings.value.fallTime * JUDGE_LINE

    if (y >= 0 && y <= 100) {
      visible.push({ id: note.id, lane: note.lane, y })
    }
  }

  visibleNotes.value = visible
}

function updateGameLoop() {
  frameId = 0

  if (
    !sessionActive ||
    gameState.value !== 'playing' ||
    !player ||
    player.getPlayerState() !== 1
  ) return

  const rawMs = player.getCurrentTime() * 1000
  if (!checkMediaClock(rawMs, true)) return

  playbackSeconds.value = rawMs / 1000
  if (!durationSeconds.value) {
    durationSeconds.value = player.getDuration() || 0
  }

  const time = rawMs - settings.value.offset
  processMisses(time)
  updateVisibleNotes(time)
  frameId = requestAnimationFrame(updateGameLoop)
}

function hitLane(lane: number) {
  if (
    !sessionActive ||
    gameState.value !== 'playing' ||
    buffering.value ||
    !player ||
    player.getPlayerState() !== 1
  ) return

  const rawMs = player.getCurrentTime() * 1000
  if (!checkMediaClock(rawMs, true)) return

  const time = rawMs - settings.value.offset
  processMisses(time)
  triggerLaneFlash(lane)
  playSE()

  const list = laneNotes[lane]
  let target: Note | null = null
  let nearest = Infinity

  for (let i = laneHeads[lane]; i < list.length; i++) {
    const note = list[i]
    if (note.time > time + GOOD_MS) break
    if (note.hit || note.miss) continue

    const distance = Math.abs(note.time - time)
    if (distance <= GOOD_MS && distance < nearest) {
      nearest = distance
      target = note
    }
  }

  if (!target) return

  target.hit = true
  advanceLaneHead(lane)
  consecutiveMisses = 0
  combo.value++
  maxCombo.value = Math.max(maxCombo.value, combo.value)

  const delta = time - target.time
  timingSamples.push(delta)

  let timing = ''
  if (delta < -15) {
    fastCount.value++
    timing = 'FAST'
  } else if (delta > 15) {
    slowCount.value++
    timing = 'SLOW'
  }

  if (nearest <= PERFECT_MS) {
    score.value.perfect++
    showPopup('PERFECT', 'text-yellow-300', timing)
  } else if (nearest <= GREAT_MS) {
    score.value.great++
    showPopup('GREAT', 'text-emerald-300', timing)
  } else {
    score.value.good++
    showPopup('GOOD', 'text-blue-300', timing)
  }

  showHitEffect(lane, nearest <= PERFECT_MS)
  triggerComboCutin()
  updateVisibleNotes(time)
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.repeat || event.ctrlKey || event.altKey || event.metaKey) return

  const target = event.target
  if (
    target instanceof HTMLElement &&
    (
      target.matches('input, textarea, select, button') ||
      target.isContentEditable
    )
  ) return

  if (event.code === 'Escape') {
    if (gameState.value === 'playing') {
      event.preventDefault()
      pauseGame()
    }
    return
  }

  if (
    gameState.value !== 'playing' ||
    (event.code !== 'KeyF' && event.code !== 'KeyJ')
  ) return

  event.preventDefault()
  hitLane(event.code === 'KeyF' ? 0 : 1)
}

function handlePointer(event: PointerEvent, lane: number) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  event.preventDefault()
  hitLane(lane)
}

function triggerLaneFlash(lane: number) {
  cancelTimer(flashTimers[lane])
  laneFlashes.value[lane] = true
  flashTimers[lane] = later(() => {
    laneFlashes.value[lane] = false
    flashTimers[lane] = null
  }, 90)
}

function showPopup(text: string, color: string, timing: string) {
  cancelTimer(popupTimer)
  popup.value = { id: ++effectId, text, color, timing }
  popupTimer = later(() => {
    popup.value = null
    popupTimer = null
  }, 450)
}

function showHitEffect(lane: number, perfect: boolean) {
  if (settings.value.effects === 'low') return

  const id = ++effectId
  hitEffects.value = [
    ...hitEffects.value.slice(-11),
    { id, lane, perfect }
  ]

  later(() => {
    hitEffects.value = hitEffects.value.filter(effect => effect.id !== id)
  }, 450)
}

function showCutin(img: string, text: string, large: boolean) {
  if (settings.value.effects === 'low') return
  cancelTimer(cutinTimer)

  activeCutin.value = { id: ++effectId, img, text, large }
  cutinTimer = later(() => {
    activeCutin.value = null
    cutinTimer = null
  }, settings.value.effects === 'high' ? 2600 : 1800)
}

function triggerComboCutin() {
  const count = combo.value

  if (count === 50) {
    showCutin('/assets/images/50.webp', 'いいグルーヴです。', false)
  } else if (count === 100) {
    showCutin('/assets/images/100.webp', 'その調子です、管理人さん。', false)
  } else if (count === 200) {
    showCutin('/assets/images/200.webp', '最高のセッションですね！', true)
  } else if (count >= 300 && count % 100 === 0) {
    showCutin('/assets/images/300.webp', `${count}コンボ…！圧巻です。`, true)
  }
}

function playSE() {
  if (!sePool.length || settings.value.seVolume <= 0) return

  const audio = sePool[seIndex++ % sePool.length]

  try {
    audio.pause()
    audio.currentTime = 0
    audio.volume = settings.value.seVolume / 100
    void audio.play().catch(() => {})
  } catch {
    // SEの失敗ではゲームを止めない。
  }
}

function endGame() {
  if (!sessionActive) return

  for (const note of notes) {
    if (!note.hit && !note.miss) {
      note.miss = true
      score.value.miss++
    }
  }

  if (timingSamples.length > 0) {
    const mean =
      timingSamples.reduce((sum, value) => sum + value, 0) /
      timingSamples.length

    const variance =
      timingSamples.reduce((sum, value) => sum + (value - mean) ** 2, 0) /
      timingSamples.length

    meanTiming.value = mean
    timingDeviation.value = Math.sqrt(variance)
  }

  saveCompletedPlay()
  stopSession()
  visibleNotes.value = []
  gameState.value = 'result'
}

function retryGame() {
  if (selectedSong.value) {
    void startGame(selectedSong.value, difficulty.value)
  }
}

function applySuggestedOffset() {
  settings.value.offset = suggestedOffset.value
}

function formatTime(value: number) {
  const seconds = Math.max(0, Math.floor(value))
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`
}

function signed(value: number, digits = 1) {
  return `${value > 0 ? '+' : ''}${value.toFixed(digits)}`
}

function hideBrokenImage(event: Event) {
  if (event.target instanceof HTMLImageElement) {
    event.target.style.visibility = 'hidden'
  }
}

async function loadSongs() {
  songsController?.abort()
  const controller = new AbortController()
  songsController = controller
  songsLoading.value = true
  errorMessage.value = ''
  const timeout = setTimeout(() => controller.abort(), 20000)

  try {
    const response = await fetch('/assets/thepillows_releases_tab.json', {
      signal: controller.signal
    })

    if (!response.ok) {
      throw new Error(`曲リストを取得できませんでした（HTTP ${response.status}）。`)
    }

    const data: unknown = await response.json()
    if (!Array.isArray(data)) throw new Error('曲リストの形式が不正です。')
    if (disposed || songsController !== controller) return

    const unique = new Map<string, Song>()

    for (const item of data) {
      if (!isObject(item) || typeof item.title !== 'string') continue
      const id = extractVideoId(item.share_url) ?? extractVideoId(item.embed_url)
      if (id && !unique.has(id)) {
        unique.set(id, { id, title: item.title })
      }
    }

    songs.value = [...unique.values()]
    if (!songs.value.length) errorMessage.value = '有効な曲がありません。'
  } catch (error) {
    if (disposed || songsController !== controller) return
    errorMessage.value =
      error instanceof Error && error.name === 'AbortError'
        ? '曲リストの読み込みがタイムアウトしました。'
        : error instanceof Error ? error.message : String(error)
  } finally {
    clearTimeout(timeout)
    if (!disposed && songsController === controller) {
      songsLoading.value = false
    }
  }
}

onMounted(() => {
  loadSave()
  window.addEventListener('keydown', handleKeyDown)
  document.addEventListener('visibilitychange', handleVisibility)

  sePool = Array.from({ length: 6 }, () => {
    const audio = new Audio('/assets/se/attack.mp3')
    audio.preload = 'auto'
    return audio
  })

  void loadSongs()
})

onUnmounted(() => {
  disposed = true
  sessionId++
  window.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('visibilitychange', handleVisibility)
  songsController?.abort()
  stopSession()
  rejectPlayerReady?.(new Error('画面が閉じられました。'))
  rejectPlayerReady = null
  timers.forEach(clearTimeout)
  timers.clear()
  player?.destroy()
  player = null

  for (const audio of sePool) {
    audio.pause()
    audio.removeAttribute('src')
    audio.load()
  }

  sePool = []
})
</script>

<template>
  <div class="beat-page min-h-screen pt-24 pb-12 text-white select-none">
    <div class="max-w-5xl mx-auto px-4">
      <header class="text-center mb-7">
        <p class="text-xs tracking-[0.35em] text-amber-300 mb-2">
          FEEL THE MUSIC
        </p>
        <h1 class="text-4xl sm:text-5xl font-black tracking-tight">
          ERIKA BEAT
        </h1>
      </header>

      <div
        v-if="errorMessage"
        role="alert"
        class="mb-4 p-4 rounded-xl border border-red-400/40 bg-red-950/90 text-red-100"
      >
        {{ errorMessage }}
      </div>

      <div
        v-if="storageMessage"
        role="status"
        class="mb-4 p-4 rounded-xl border border-amber-300/30 bg-zinc-900 text-amber-100 text-sm"
      >
        {{ storageMessage }}
        <button
          class="ml-3 underline text-zinc-300"
          @click="storageMessage = ''"
        >
          閉じる
        </button>
      </div>

      <!-- 選曲 -->
      <section v-if="gameState === 'select'" class="panel p-4 sm:p-6">
        <div class="flex flex-wrap items-center justify-between gap-3 mb-5">
          <div>
            <h2 class="text-xl font-bold">曲を選ぶ</h2>
            <p class="text-xs text-zinc-400 mt-1">
              {{ savedPlayedSongs }}曲プレイ済み /
              お気に入り {{ favorites.length }}曲
            </p>
          </div>
          <div class="flex gap-2 text-xs">
            <button class="sub-button" @click="exportSave">記録を書き出す</button>
            <button class="sub-button" @click="importInput?.click()">
              記録を読み込む
            </button>
            <input
              ref="importInput"
              type="file"
              accept=".json,application/json"
              class="hidden"
              @change="importSave"
            >
          </div>
        </div>

        <details class="mb-5 rounded-xl bg-zinc-900/90 p-4">
          <summary class="cursor-pointer font-bold">
            プレイ設定・保存について
          </summary>

          <div class="grid sm:grid-cols-2 gap-5 mt-4 text-sm">
            <label>
              タイミング調整：{{ settings.offset }}ms
              <input
                v-model.number="settings.offset"
                type="range"
                min="-300"
                max="300"
                step="5"
                class="block w-full mt-2"
              >
              <span class="block text-xs text-zinc-400 mt-1">
                ＋でノーツと判定を音楽に対して遅らせます。
              </span>
            </label>

            <label>
              落下時間：{{ (settings.fallTime / 1000).toFixed(1) }}秒
              <input
                v-model.number="settings.fallTime"
                type="range"
                min="800"
                max="2500"
                step="100"
                class="block w-full mt-2"
              >
              <span class="block text-xs text-zinc-400 mt-1">
                短いほど速く落下します。
              </span>
            </label>

            <label>
              音楽音量：{{ settings.musicVolume }}%
              <input
                v-model.number="settings.musicVolume"
                type="range"
                min="0"
                max="100"
                class="block w-full mt-2"
              >
            </label>

            <label>
              効果音音量：{{ settings.seVolume }}%
              <input
                v-model.number="settings.seVolume"
                type="range"
                min="0"
                max="100"
                class="block w-full mt-2"
              >
            </label>

            <label>
              演出量
              <select v-model="settings.effects" class="form-control mt-2">
                <option value="low">控えめ</option>
                <option value="normal">標準</option>
                <option value="high">豪華</option>
              </select>
            </label>

            <div class="text-xs text-zinc-400 leading-relaxed">
              F・J または左右のレーンをタップ。Escで一時停止。<br>
              記録と設定は、この端末のブラウザに保存します。
              完走したプレイだけが記録対象です。<br>
              JSON読み込みではベスト記録とお気に入りを統合します。
            </div>
          </div>
        </details>

        <div class="grid sm:grid-cols-[1fr_auto_auto] gap-3 mb-4">
          <input
            v-model="searchText"
            type="search"
            placeholder="曲名を検索"
            aria-label="曲名を検索"
            class="form-control"
          >

          <select
            v-model="songFilter"
            aria-label="曲の絞り込み"
            class="form-control"
          >
            <option value="all">すべて</option>
            <option value="favorite">お気に入り</option>
            <option value="played">プレイ済み</option>
            <option value="unplayed">未プレイ</option>
            <option value="fullcombo">フルコンボ達成</option>
            <option value="unfinished">フルコンボ未達成</option>
          </select>

          <select
            v-model="filterDifficulty"
            aria-label="記録を絞り込む難易度"
            class="form-control"
          >
            <option value="veryeasy">Very Easyの記録</option>
            <option value="easy">Easyの記録</option>
            <option value="normal">Normalの記録</option>
            <option value="hard">Hardの記録</option>
          </select>
        </div>

        <p class="text-xs text-zinc-400 mb-3">
          {{ filteredSongs.length }}曲
          <span v-if="songFilter !== 'all' && songFilter !== 'favorite'">
            ／ {{ filterDifficulty }}の達成状況で絞り込み
          </span>
        </p>

        <p v-if="songsLoading" class="text-center py-10 text-zinc-300">
          曲リストを読み込み中…
        </p>

        <div v-else class="max-h-[60vh] overflow-y-auto space-y-3 pr-1">
          <article
            v-for="song in filteredSongs"
            :key="song.id"
            class="rounded-xl border border-zinc-700 bg-zinc-900/90 p-4"
          >
            <div class="flex items-start gap-3 mb-3">
              <button
                class="text-2xl shrink-0 leading-none"
                :class="isFavorite(song.id) ? 'text-amber-300' : 'text-zinc-600'"
                :aria-label="isFavorite(song.id) ? 'お気に入り解除' : 'お気に入り登録'"
                :aria-pressed="isFavorite(song.id)"
                @click="toggleFavorite(song.id)"
              >
                {{ isFavorite(song.id) ? '★' : '☆' }}
              </button>
              <h3 class="font-bold break-words min-w-0">{{ song.title }}</h3>
            </div>

            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <button
                v-for="diff in DIFFICULTIES"
                :key="diff"
                class="difficulty-button rounded-xl p-3 text-left border"
                :class="{
                  'border-teal-400/50 bg-teal-950/60': diff === 'veryeasy',
                  'border-emerald-600/50 bg-emerald-950/60': diff === 'easy',
                  'border-blue-600/50 bg-blue-950/60': diff === 'normal',
                  'border-red-600/50 bg-red-950/60': diff === 'hard'
                }"
                @click="startGame(song, diff)"
              >
                <span class="block font-black text-sm uppercase">
                  {{ diff === 'veryeasy' ? 'Very Easy' : diff }}
                </span>

                <template v-if="getRecord(song.id, diff)">
                  <span class="block text-xs mt-1">
                    {{ getRecord(song.id, diff)!.bestAccuracy.toFixed(2) }}%
                  </span>
                  <span
                    class="block text-[10px] sm:text-xs font-bold mt-1"
                    :class="getRecord(song.id, diff)!.fullCombo
                      ? 'text-amber-300'
                      : 'text-zinc-400'"
                  >
                    {{
                      getRecord(song.id, diff)!.allPerfect
                        ? 'ALL PERFECT'
                        : getRecord(song.id, diff)!.fullCombo
                          ? 'FULL COMBO'
                          : 'PLAYED'
                    }}
                  </span>
                  <span class="block text-[10px] text-zinc-400 mt-1">
                    完走 {{ getRecord(song.id, diff)!.playCount }}回
                  </span>
                </template>

                <span v-else class="block text-xs text-zinc-400 mt-2">
                  未プレイ
                </span>
              </button>
            </div>
          </article>

          <p v-if="!filteredSongs.length" class="text-center py-10 text-zinc-400">
            該当する曲がありません。
          </p>
        </div>

        <button
          v-if="!songsLoading && !songs.length"
          class="sub-button mt-3"
          @click="loadSongs"
        >
          曲リストを再読み込み
        </button>
      </section>

      <!-- プレイ情報 -->
      <div
        v-if="gameState !== 'select' && gameState !== 'result'"
        class="max-w-md mx-auto mb-3"
      >
        <p class="font-bold break-words">{{ selectedSong?.title }}</p>

        <div class="flex items-center justify-between gap-3 mt-2">
          <span class="text-xs uppercase text-zinc-300">
            {{ difficulty }} / {{ totalNotes }} NOTES
          </span>
          <div class="flex gap-2 text-xs">
            <button
              v-if="gameState === 'playing'"
              class="sub-button"
              @click="pauseGame"
            >
              一時停止
            </button>
            <button class="sub-button" @click="returnToSelect">
              選曲へ戻る
            </button>
          </div>
        </div>

        <div class="mt-3 h-1 bg-zinc-800 rounded-full overflow-hidden">
          <div
            class="h-full bg-amber-400"
            :style="{ width: `${progressPercent}%` }"
          ></div>
        </div>
        <div class="flex justify-between text-xs text-zinc-400 mt-1">
          <span>{{ formatTime(playbackSeconds) }}</span>
          <span>
            {{ durationSeconds > 0 ? formatTime(durationSeconds) : '--:--' }}
          </span>
        </div>
      </div>

      <p
        v-if="gameState === 'loading' && !showBoard"
        class="text-center py-14"
        role="status"
      >
        {{ loadingLabel }}
      </p>

      <!-- プレイ領域 -->
      <div v-if="showBoard" class="play-stage">
        <div class="game-board">
          <div
            class="absolute inset-y-0 left-0 w-1/2 bg-cyan-400/25 pointer-events-none"
            :class="laneFlashes[0] ? 'opacity-100' : 'opacity-0'"
          ></div>
          <div
            class="absolute inset-y-0 right-0 w-1/2 bg-pink-400/25 pointer-events-none"
            :class="laneFlashes[1] ? 'opacity-100' : 'opacity-0'"
          ></div>

          <div class="absolute inset-y-0 left-1/2 w-px bg-white/20"></div>

          <div class="absolute top-3 inset-x-0 text-center z-10 pointer-events-none">
            <p class="text-xs text-zinc-400">
              {{ judgedCount > 0 ? `${liveAccuracy.toFixed(1)}%` : '—' }}
              / MISS {{ score.miss }}
            </p>
            <div v-if="combo > 0" class="mt-2">
              <p class="text-5xl font-black">{{ combo }}</p>
              <p class="text-[10px] tracking-[0.3em] text-zinc-400">COMBO</p>
            </div>
          </div>

          <div
            v-for="note in visibleNotes"
            :key="note.id"
            class="note"
            :class="note.lane === 0 ? 'note-left' : 'note-right'"
            :style="{ top: `${note.y}%` }"
          ></div>

          <div
            class="absolute inset-x-0 h-1 bg-amber-300 shadow-[0_0_15px_#fbbf24] z-10 pointer-events-none"
            :style="{ top: `${JUDGE_LINE}%` }"
          ></div>

          <div
            v-for="effect in hitEffects"
            :key="effect.id"
            class="hit-effect"
            :class="{
              perfect: effect.perfect,
              lavish: settings.effects === 'high'
            }"
            :style="{
              left: effect.lane === 0 ? '25%' : '75%',
              top: `${JUDGE_LINE}%`,
              color: effect.lane === 0 ? '#67e8f9' : '#f9a8d4'
            }"
          >
            <span class="hit-ring"></span>
            <span
              v-if="settings.effects === 'high'"
              class="hit-ring hit-ring-delayed"
            ></span>
            <span
              v-for="particle in settings.effects === 'high' ? 8 : 4"
              :key="particle"
              class="hit-particle"
              :style="{
                '--angle': `${particle * (settings.effects === 'high' ? 45 : 90)}deg`
              }"
            ></span>
          </div>

          <div
            v-if="popup"
            :key="popup.id"
            class="judge-popup absolute top-[48%] inset-x-0 text-center pointer-events-none z-20"
          >
            <p class="text-4xl font-black italic" :class="popup.color">
              {{ popup.text }}
            </p>
            <p
              class="text-sm font-bold tracking-widest mt-1"
              :class="popup.timing === 'FAST' ? 'text-cyan-300' : 'text-orange-300'"
            >
              {{ popup.timing }}
            </p>
          </div>

          <div class="absolute inset-0 flex z-30 touch-none">
            <div
              class="lane-input text-cyan-300"
              @pointerdown="handlePointer($event, 0)"
              @contextmenu.prevent
            >
              <span>F / 左タップ</span>
            </div>
            <div
              class="lane-input text-pink-300"
              @pointerdown="handlePointer($event, 1)"
              @contextmenu.prevent
            >
              <span>J / 右タップ</span>
            </div>
          </div>

          <div
            v-if="gameState === 'countdown'"
            class="absolute inset-0 flex items-center justify-center z-40 pointer-events-none"
          >
            <span :key="countdown" class="countdown-number">
              {{ countdown }}
            </span>
          </div>

          <div
            v-if="gameState === 'paused' || gameState === 'loading' || buffering || autoplayBlocked"
            class="absolute inset-0 z-40 bg-black/80 flex flex-col items-center justify-center gap-5 px-6 text-center"
          >
            <p class="text-xl font-black">
              {{
                autoplayBlocked
                  ? '再生ボタンを押してください'
                  : gameState === 'paused'
                    ? 'PAUSED'
                    : '再生を準備中…'
              }}
            </p>

            <button
              v-if="gameState === 'paused' || autoplayBlocked"
              class="primary-button"
              @click="requestPlayback"
            >
              {{ gameState === 'paused' ? '再開する' : '再生する' }}
            </button>

            <p v-if="autoplayBlocked" class="text-sm text-zinc-300">
              開始できない場合は、下の動画プレーヤーから再生してください。
            </p>
          </div>
        </div>

        <!-- PCではレーン横、スマホでは上側の端に表示 -->
        <Transition name="cutin">
          <aside
            v-if="activeCutin && gameState === 'playing' && !buffering"
            :key="activeCutin.id"
            class="erika-cutin"
            :class="{
              'cutin-large': activeCutin.large,
              'cutin-lavish': settings.effects === 'high'
            }"
          >
            <div class="cutin-glow"></div>
            <img
              :src="activeCutin.img"
              alt=""
              class="cutin-image"
              @error="hideBrokenImage"
            >
            <p class="cutin-speech">{{ activeCutin.text }}</p>
          </aside>
        </Transition>
      </div>

      <!-- リザルト -->
      <section
        v-if="gameState === 'result'"
        class="panel relative max-w-xl mx-auto overflow-hidden p-6 text-center"
      >
        <img
          src="/assets/images/beatresult.webp"
          alt=""
          class="absolute inset-0 w-full h-full object-cover opacity-20 pointer-events-none"
          @error="hideBrokenImage"
        >

        <div class="relative">
          <h2 class="text-xl font-black text-amber-300 tracking-widest">
            SESSION RESULT
          </h2>
          <p class="text-sm mt-2 break-words">{{ selectedSong?.title }}</p>
          <p class="uppercase text-xs text-zinc-400 mt-1">{{ difficulty }}</p>

          <img
            :src="resultRank.img"
            alt=""
            class="w-28 h-28 object-cover rounded-full mx-auto my-4 border-2 border-amber-300"
            @error="hideBrokenImage"
          >

          <p
            class="text-7xl font-black italic"
            :class="{
              'text-yellow-300': resultRank.rank === 'S',
              'text-emerald-300': resultRank.rank === 'A',
              'text-blue-300': resultRank.rank === 'B',
              'text-zinc-300': resultRank.rank === 'C'
            }"
          >
            {{ resultRank.rank }}
          </p>

          <p
            v-if="fullCombo"
            class="clear-badge text-amber-300 font-black tracking-widest mt-3"
          >
            {{ allPerfect ? 'ALL PERFECT' : 'FULL COMBO' }}
          </p>

          <p v-if="resultNewRecord" class="text-pink-300 font-black mt-3">
            NEW RECORD
          </p>

          <p class="my-5 font-bold">{{ resultRank.text }}</p>

          <div class="grid grid-cols-2 gap-3 mb-4">
            <div class="result-card">
              <p class="text-xs text-zinc-400">ACCURACY</p>
              <p class="text-3xl font-black mt-1">
                {{ finalAccuracy.toFixed(2) }}<span class="text-sm">%</span>
              </p>
              <p
                v-if="previousBest !== null"
                class="text-xs mt-1"
                :class="finalAccuracy >= previousBest ? 'text-emerald-300' : 'text-zinc-400'"
              >
                以前のベスト比 {{ signed(finalAccuracy - previousBest, 2) }}pt
              </p>
            </div>

            <div class="result-card">
              <p class="text-xs text-zinc-400">MAX COMBO</p>
              <p class="text-3xl font-black mt-1">{{ maxCombo }}</p>
              <p class="text-xs text-zinc-400 mt-1">
                / {{ totalNotes }} NOTES
              </p>
            </div>
          </div>

          <div class="result-card grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            <div class="flex justify-between text-yellow-300">
              <span>Perfect</span><span>{{ score.perfect }}</span>
            </div>
            <div class="flex justify-between text-emerald-300">
              <span>Great</span><span>{{ score.great }}</span>
            </div>
            <div class="flex justify-between text-blue-300">
              <span>Good</span><span>{{ score.good }}</span>
            </div>
            <div class="flex justify-between text-red-300">
              <span>Miss</span><span>{{ score.miss }}</span>
            </div>
            <div class="flex justify-between text-cyan-300">
              <span>Fast</span><span>{{ fastCount }}</span>
            </div>
            <div class="flex justify-between text-orange-300">
              <span>Slow</span><span>{{ slowCount }}</span>
            </div>
          </div>

          <details
            v-if="score.perfect + score.great + score.good >= 20"
            class="result-card text-left mt-4 text-sm"
          >
            <summary class="cursor-pointer font-bold">タイミング分析</summary>

            <div class="mt-3 space-y-2 text-zinc-300">
              <p>
                平均：
                {{
                  Math.abs(meanTiming) < 1
                    ? 'ほぼ中央'
                    : `${Math.abs(meanTiming).toFixed(1)}ms ${meanTiming < 0 ? '早め' : '遅め'}`
                }}
              </p>
              <p>ばらつき：{{ timingDeviation.toFixed(1) }}ms</p>
              <p>現在の調整値：{{ settings.offset }}ms</p>
              <p>調整候補：{{ suggestedOffset }}ms</p>
              <p class="text-xs text-zinc-400 leading-relaxed">
                ヒットしたノーツからの推定です。押し方の癖も含むため、
                少しずつ変更して確認してください。
              </p>

              <button
                v-if="suggestedOffset !== settings.offset"
                class="sub-button"
                @click="applySuggestedOffset"
              >
                候補の値を設定する
              </button>
            </div>
          </details>

          <div class="flex flex-wrap justify-center gap-3 mt-6">
            <button class="primary-button" @click="retryGame">もう一度</button>
            <button class="sub-button" @click="returnToSelect">選曲へ戻る</button>
            <button class="sub-button" @click="exportSave">記録を書き出す</button>
          </div>
        </div>
      </section>

      <!-- 常設プレーヤー -->
      <div class="max-w-md mx-auto mt-6">
        <p class="text-xs text-zinc-400 mb-2">YouTube</p>
        <div
          ref="playerHost"
          class="youtube-host w-full bg-black rounded-xl overflow-hidden border border-white/15"
        ></div>
        <p
          v-if="gameState !== 'select' && gameState !== 'result'"
          class="text-[11px] text-zinc-500 mt-2"
        >
          プレイ中の早送り・巻き戻し・再生速度変更は中断扱いになります。
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.beat-page {
  background:
    linear-gradient(rgba(8, 8, 16, 0.76), rgba(8, 8, 16, 0.94)),
    url('/assets/images/erika-hero.jpg') center / cover fixed;
}

.panel {
  background: rgba(9, 9, 14, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 20px;
  backdrop-filter: blur(12px);
}

.form-control {
  display: block;
  width: 100%;
  padding: 11px 13px;
  border: 1px solid #52525b;
  border-radius: 10px;
  background: #18181b;
  color: white;
  min-width: 0;
}

.sub-button {
  padding: 9px 13px;
  border: 1px solid #52525b;
  border-radius: 10px;
  background: #27272a;
  color: white;
  font-weight: 700;
  transition: background 120ms ease;
}

.sub-button:hover {
  background: #3f3f46;
}

.primary-button {
  padding: 12px 25px;
  border-radius: 999px;
  background: #fbbf24;
  color: #18181b;
  font-weight: 900;
}

.primary-button:hover {
  background: #fcd34d;
}

.difficulty-button {
  transition: filter 120ms ease, transform 120ms ease;
}

.difficulty-button:hover {
  filter: brightness(1.25);
  transform: translateY(-1px);
}

.play-stage {
  position: relative;
  max-width: 448px;
  margin: 0 auto;
}

.game-board {
  position: relative;
  height: 65vh;
  min-height: 340px;
  overflow: hidden;
  border: 2px solid #52525b;
  border-radius: 16px;
  background:
    linear-gradient(90deg, rgba(8, 145, 178, 0.07), rgba(219, 39, 119, 0.07)),
    rgba(0, 0, 0, 0.94);
  box-shadow: 0 20px 70px rgba(0, 0, 0, 0.45);
}

.note {
  position: absolute;
  width: 50%;
  height: 15px;
  transform: translateY(-50%);
  border-radius: 999px;
  pointer-events: none;
  border: 1px solid rgba(255, 255, 255, 0.75);
}

.note-left {
  left: 0;
  background: #67e8f9;
  box-shadow: 0 0 13px rgba(103, 232, 249, 0.55);
}

.note-right {
  right: 0;
  background: #f9a8d4;
  box-shadow: 0 0 13px rgba(249, 168, 212, 0.55);
}

.lane-input {
  width: 50%;
  height: 100%;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding-bottom: 22px;
  font-weight: 700;
  touch-action: none;
}

.lane-input span {
  pointer-events: none;
}

.judge-popup {
  animation: judge-pop 150ms ease-out both;
  text-shadow: 0 3px 16px #000;
}

@keyframes judge-pop {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.92);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.countdown-number {
  font-size: 100px;
  font-weight: 900;
  text-shadow: 0 0 40px rgba(251, 191, 36, 0.45);
  animation: countdown-pop 230ms ease-out both;
}

@keyframes countdown-pop {
  from {
    transform: scale(1.35);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.hit-effect {
  position: absolute;
  z-index: 20;
  pointer-events: none;
}

.hit-ring {
  position: absolute;
  width: 56px;
  height: 20px;
  border: 2px solid currentColor;
  border-radius: 50%;
  box-shadow: 0 0 14px currentColor;
  animation: ring-expand 420ms ease-out forwards;
}

.hit-effect.perfect .hit-ring {
  border-width: 3px;
  filter: brightness(1.4);
}

.hit-ring-delayed {
  animation-delay: 60ms;
  opacity: 0;
}

@keyframes ring-expand {
  from {
    opacity: 1;
    transform: translate(-50%, -50%) scale(0.35);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -50%) scale(2.8);
  }
}

.hit-particle {
  position: absolute;
  width: 5px;
  height: 5px;
  background: currentColor;
  border-radius: 50%;
  animation: particle-fly 400ms ease-out forwards;
}

@keyframes particle-fly {
  from {
    opacity: 1;
    transform: rotate(var(--angle)) translateY(-5px) scale(1);
  }
  to {
    opacity: 0;
    transform: rotate(var(--angle)) translateY(-60px) scale(0.2);
  }
}

.erika-cutin {
  position: absolute;
  top: 15%;
  right: 5px;
  width: 140px;
  height: 230px;
  max-height: 42%;
  z-index: 25;
  pointer-events: none;
}

.cutin-glow {
  position: absolute;
  inset: 10% 0;
  border-radius: 50%;
  background: radial-gradient(
    ellipse,
    rgba(251, 191, 36, 0.2),
    transparent 70%
  );
}

.cutin-image {
  position: relative;
  width: 100%;
  height: 100%;
  object-fit: contain;
  object-position: center bottom;
  filter: drop-shadow(0 0 12px rgba(251, 191, 36, 0.25));
  mask-image: linear-gradient(#000 85%, transparent);
}

.cutin-speech {
  position: absolute;
  left: -20px;
  right: 0;
  bottom: 0;
  padding: 8px 10px;
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.88);
  font-size: 12px;
  font-weight: 800;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.cutin-large .cutin-glow {
  background: radial-gradient(
    ellipse,
    rgba(251, 191, 36, 0.4),
    transparent 70%
  );
}

.cutin-lavish .cutin-image {
  filter: drop-shadow(0 0 22px rgba(251, 191, 36, 0.6));
}

.cutin-enter-active,
.cutin-leave-active {
  transition: opacity 180ms ease, transform 220ms ease;
}

.cutin-enter-from,
.cutin-leave-to {
  opacity: 0;
  transform: translateX(35px);
}

.result-card {
  background: rgba(0, 0, 0, 0.58);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 13px;
  padding: 16px;
}

.clear-badge {
  animation: clear-appear 500ms ease-out both;
  text-shadow: 0 0 24px rgba(251, 191, 36, 0.5);
}

@keyframes clear-appear {
  from {
    opacity: 0;
    transform: scale(1.15);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.youtube-host {
  height: clamp(200px, 56.25vw, 252px);
  min-height: 200px;
}

.youtube-host :deep(iframe) {
  display: block;
  width: 100%;
  height: 100%;
  min-height: 200px;
  border: 0;
}

@media (min-width: 1000px) {
  .erika-cutin {
    top: 8%;
    right: -250px;
    width: 230px;
    height: 440px;
    max-height: 85%;
  }

  .cutin-large {
    width: 260px;
    right: -275px;
  }

  .cutin-speech {
    left: 0;
    font-size: 15px;
    padding: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .judge-popup,
  .countdown-number,
  .clear-badge {
    animation: none;
  }

  .hit-effect {
    display: none;
  }

  .cutin-enter-active,
  .cutin-leave-active,
  .difficulty-button {
    transition: none;
  }
}
</style>