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

export function createYoutubeBgm(elementId: string, onTitle?: (title: string) => void) {
  let songs: Song[] = []
  let player: BGMPlayer | null = null
  let ready = false
  let disposed = false
  let wantPlaying = false
  let pendingId: string | null = null
  let volume = 25
  let previousReady: (() => void) | undefined

  const pick = () => songs.length ? songs[Math.floor(Math.random() * songs.length)] : undefined

  const playRandom = () => {
    const song = pick()
    const id = getVideoId(song)
    onTitle?.(song?.title ?? '')
    if (!player || !ready) { pendingId = id; return }
    player.setVolume(volume)
    player.loadVideoById(id)
  }

  const create = () => {
    const w = window as YouTubeWindow
    if (disposed || player || !w.YT?.Player || !document.getElementById(elementId)) return
    const first = pick()
    player = new w.YT.Player(elementId, {
      videoId: getVideoId(first),
      playerVars: { playsinline: 1, controls: 0, disablekb: 1 },
      events: {
        onReady: (e) => {
          if (disposed) return
          ready = true
          e.target.setVolume(volume)
          if (wantPlaying) {
            if (pendingId) { e.target.loadVideoById(pendingId); pendingId = null }
            else { onTitle?.(first?.title ?? ''); e.target.playVideo() }
          }
        },
        // 曲が終わったら次の曲をランダムで流す
        onStateChange: (e) => { if (e.data === 0 && wantPlaying) playRandom() },
      },
    })
  }

  const init = async () => {
    try {
      const res = await fetch('/assets/thepillows_releases_tab.json')
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) songs = data
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
    /** 再生開始（初回はランダム選曲、2回目以降は続きから） */
    play() {
      if (wantPlaying && ready) { player?.playVideo(); return }
      const first = !wantPlaying && !pendingId
      wantPlaying = true
      if (!player || !ready) { if (first) playRandom(); return }
      player.setVolume(volume)
      player.playVideo()
    },
    next() { wantPlaying = true; playRandom() },
    pause() {
      if (player && ready) player.pauseVideo()
    },
    stop() {
      wantPlaying = false
      pendingId = null
      if (player && ready) player.pauseVideo()
    },
    setVolume(v: number) {
      volume = Math.max(0, Math.min(100, Math.round(v)))
      if (player && ready) player.setVolume(volume)
    },
    get playing() { return wantPlaying },
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
