/**
 * YouTube を BGM として流す（ラビリンスと同じ仕組み）。
 * 曲リストは /assets/thepillows_releases_tab.json。見えない iframe プレイヤーで再生する。
 */

interface Song { embed_url?: string; share_url?: string; youtube_id?: string; title?: string }
interface BGMPlayer {
  setVolume: (volume: number) => void
  loadVideoById: (id: string) => void
  pauseVideo: () => void
  playVideo: () => void
  destroy: () => void
}
interface YouTubeAPI {
  Player: new (element: string | HTMLElement, options: {
    videoId: string
    playerVars: Record<string, string | number>
    events: {
      onReady: (event: { target: BGMPlayer }) => void
      onStateChange?: (event: { data: number; target: BGMPlayer }) => void
    }
  }) => BGMPlayer
}
interface YouTubeWindow extends Window {
  YT?: YouTubeAPI
  onYouTubeIframeAPIReady?: () => void
}

const FALLBACK_VIDEO_ID = 'xUboS2Fw1-o'

export function getVideoId(song?: Song): string {
  if (!song) return FALLBACK_VIDEO_ID
  if (song.youtube_id && /^[\w-]{11}$/.test(song.youtube_id)) return song.youtube_id
  for (const source of [song.embed_url, song.share_url]) {
    if (!source) continue
    if (/^[\w-]{11}$/.test(source)) return source
    try {
      const url = new URL(source)
      const parts = url.pathname.split('/').filter(Boolean)
      const candidate = url.hostname === 'youtu.be' ? parts[0]
        : ['embed', 'shorts', 'live'].includes(parts[0]) ? parts[1]
        : url.searchParams.get('v')
      if (candidate && /^[\w-]{11}$/.test(candidate)) return candidate
    } catch { /* 次の候補へ */ }
  }
  return FALLBACK_VIDEO_ID
}

// ボス戦の曲（ステージ曲のランダム選曲からは除外する）
export const BOSS_SONGS: Song[] = [
  { title: 'White Ash', youtube_id: '8PUwW3di0Xw' },
  { title: 'Sleepy Head', youtube_id: 'IEr_G_9LBA8' },
  { title: 'Come Down', youtube_id: '8R9aMgpcbgw' },
]
export const FINAL_BOSS_SONG: Song = { title: 'Advice', youtube_id: 'Le9Mh-s74FU' }

export function createYoutubeBgm(elementId: string, onTitle?: (title: string) => void) {
  let stageSongs: Song[] = []
  let player: BGMPlayer | null = null
  let ready = false
  let disposed = false
  let wantPlaying = false
  let current: { id: string; title: string; loop: boolean } | null = null
  let needsLoad = false // current をまだプレイヤーに読み込んでいない
  let volume = 12 // 効果音の方がはっきり聞こえる程度に控えめ
  let previousReady: (() => void) | undefined

  const bossIds = new Set([...BOSS_SONGS, FINAL_BOSS_SONG].map(s => getVideoId(s)))
  const pickStage = () => {
    const pool = stageSongs.filter(s => !bossIds.has(getVideoId(s)))
    const list = pool.length ? pool : stageSongs
    return list.length ? list[Math.floor(Math.random() * list.length)] : undefined
  }

  const start = (song: Song | undefined, loop: boolean) => {
    current = { id: getVideoId(song), title: song?.title ?? '', loop }
    onTitle?.(current.title)
    wantPlaying = true
    needsLoad = true
    flush()
  }
  // プレイヤーの準備ができていれば、予約中の曲を流す
  const flush = () => {
    if (!player || !ready || !wantPlaying || !current) return
    player.setVolume(volume)
    if (needsLoad) { player.loadVideoById(current.id); needsLoad = false }
    else player.playVideo()
  }

  const create = () => {
    const w = window as YouTubeWindow
    if (disposed || player || !w.YT?.Player || !document.getElementById(elementId)) return
    player = new w.YT.Player(elementId, {
      videoId: current?.id ?? getVideoId(pickStage()),
      playerVars: { playsinline: 1, controls: 0, disablekb: 1 },
      events: {
        onReady: (e) => {
          if (disposed) return
          ready = true
          e.target.setVolume(volume)
          flush()
        },
        // 曲が終わったら：ボス曲はループ、ステージ曲は次の曲をランダムで
        onStateChange: (e) => {
          if (e.data !== 0 || !wantPlaying || !current) return
          if (current.loop) { needsLoad = true; flush() }
          else start(pickStage(), false)
        },
      },
    })
  }

  const init = async () => {
    try {
      const res = await fetch('/assets/thepillows_releases_tab.json')
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) stageSongs = data
      }
    } catch (error) {
      console.warn('[ERIKA] BGM list unavailable.', error)
    }
    if (disposed) return
    const w = window as YouTubeWindow
    if (w.YT?.Player) { create(); return }
    previousReady = w.onYouTubeIframeAPIReady
    w.onYouTubeIframeAPIReady = () => {
      try { previousReady?.() } finally { create() }
    }
    if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
      const tag = document.createElement('script')
      tag.src = 'https://www.youtube.com/iframe_api'
      document.head.appendChild(tag)
    }
  }

  return {
    init,
    /** ステージ曲をランダムで新しく流す */
    playStage() { start(pickStage(), false) },
    /** ボス曲（ループ）。final=true は最終ボス専用曲 */
    playBoss(final: boolean) {
      start(final ? FINAL_BOSS_SONG : BOSS_SONGS[Math.floor(Math.random() * BOSS_SONGS.length)], true)
    },
    /** 一時停止からの再開（止まっていた場合は新しいステージ曲） */
    resume() {
      if (!current) { start(pickStage(), false); return }
      wantPlaying = true
      flush()
    },
    next() { start(pickStage(), false) },
    pause() { if (player && ready) player.pauseVideo() },
    stop() {
      wantPlaying = false
      current = null
      needsLoad = false
      if (player && ready) player.pauseVideo()
    },
    setVolume(v: number) {
      volume = Math.max(0, Math.min(100, Math.round(v)))
      if (player && ready) player.setVolume(volume)
    },
    get playing() { return wantPlaying },
    get hasTrack() { return !!current },
    dispose() {
      disposed = true
      wantPlaying = false
      try { player?.destroy() } catch { /* already gone */ }
      player = null
      const w = window as YouTubeWindow
      if (previousReady !== undefined) w.onYouTubeIframeAPIReady = previousReady
    },
  }
}
