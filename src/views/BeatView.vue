<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// --- 型定義 ---
interface Song {
  title: string
  share_url?: string
}
interface Note {
  time: number
  lane: number
  hit?: boolean
  miss?: boolean
  y?: number
}

// --- 状態管理 ---
const gameState = ref<'select' | 'loading' | 'playing' | 'result'>('select')
const songs = ref<Song[]>([])
const selectedSong = ref<Song | null>(null)
const difficulty = ref<'easy' | 'normal' | 'hard'>('normal')

const currentNotes = ref<Note[]>([])
const combo = ref(0)
const maxCombo = ref(0)
const score = ref({ perfect: 0, great: 0, good: 0, miss: 0 })

// --- ゲーム定数 ---
const FALL_TIME_MS = 1500 // ノーツが画面上部から判定ラインに到達するまでの時間（ミリ秒）
const JUDGE_LINE_Y = 80   // 判定ラインの位置（画面上部から80%の位置）

const laneFlashes = ref([false, false])
interface Popup { id: number, text: string, color: string }
const popups = ref<Popup[]>([])

const activeCutin = ref<{ img: string, text: string } | null>(null)
const resultRank = ref({ rank: '', text: '', img: '' })

let ytPlayer: any = null
let animationFrameId: number = 0
let isGameRunning = false

// --- 初期化 ---
onMounted(async () => {
  try {
    const res = await fetch('/assets/thepillows_releases_tab.json')
    if (res.ok) songs.value = await res.json()
  } catch (e) {
    console.error("曲リストの取得に失敗しました", e)
  }

  // キーボード操作のイベントリスナー
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  stopGame()
})

// --- ゲーム開始処理 ---
const startGame = async (song: Song, diff: 'easy' | 'normal' | 'hard') => {
  selectedSong.value = song
  difficulty.value = diff
  gameState.value = 'loading'
  combo.value = 0
  maxCombo.value = 0
  score.value = { perfect: 0, great: 0, good: 0, miss: 0 }

  let ytId = song.share_url?.split('/').pop()
  if (ytId && ytId.includes('?')) {
    ytId = ytId.split('?')[0]
  }
  if (!ytId) return

  // 譜面のフェッチ
  try {
    // URLの末尾に時間を付与して、ブラウザのキャッシュを強制的に無効化する
    const fetchUrl = `/assets/beatmaps/beatmap_${ytId}.json?t=${new Date().getTime()}`
    console.log("フェッチするURL:", fetchUrl) // F12開発者ツールのConsole確認用

    const res = await fetch(fetchUrl)
    if (!res.ok) {
      throw new Error(`HTTPステータス: ${res.status} (${res.statusText})`)
    }
    const data = await res.json()
    
    currentNotes.value = JSON.parse(JSON.stringify(data.difficulties[diff]))
  } catch (e: any) {
    console.error("エラー詳細:", e)
    // エラーの理由をダイアログに詳細に表示する
    alert(`譜面データの読み込みに失敗しました。\n対象ID: beatmap_${ytId}.json\n詳細: ${e.message}`)
    gameState.value = 'select'
    return
  }

  initYouTubePlayer(ytId)
}

// カットイン表示関数
const showCutin = (img: string, text: string) => {
  activeCutin.value = { img, text }
  // 2.5秒後にスッと消す
  setTimeout(() => {
    activeCutin.value = null
  }, 2500)
}

const playSE = (seName: string) => {
  try {
    const audio = new Audio(`/assets/se/${seName}.mp3`)
    audio.currentTime = 0 // 連続で叩いた時にも音が鳴るようにリセット
    audio.volume = 0.5
    audio.play().catch(() => {})
  } catch (e) {}
}

const triggerLaneFlash = (lane: number) => {
  laneFlashes.value[lane] = true
  setTimeout(() => { laneFlashes.value[lane] = false }, 100)
}

const showPopup = (text: string, color: string) => {
  const id = Date.now() + Math.random()
  popups.value.push({ id, text, color })
  setTimeout(() => {
    popups.value = popups.value.filter(p => p.id !== id)
  }, 500)
}

// --- YouTube制御とゲームループ ---
const initYouTubePlayer = (ytId: string) => {
  if (ytPlayer && typeof ytPlayer.destroy === 'function') {
    ytPlayer.destroy()
  }

  const loadPlayer = () => {
    // @ts-ignore
    ytPlayer = new window.YT.Player('yt-bgm-player', {
      videoId: ytId,
      playerVars: { playsinline: 1, origin: window.location.origin, controls: 0 },
      events: {
        // ▼▼▼ ここを追加：プレーヤーの準備ができたら再生を開始する ▼▼▼
        onReady: (e: any) => {
          e.target.setVolume(50) // 音量はお好みで調整してください
          e.target.playVideo()
        },
        // ▲▲▲ ここまで追加 ▲▲▲
        onStateChange: (e: any) => {
          if (e.data === 1) { // PLAYING
            if (!isGameRunning) {
              gameState.value = 'playing'
              isGameRunning = true
              updateGameLoop()
            }
          } else if (e.data === 0) { // ENDED
            endGame()
          }
        }
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

const updateGameLoop = () => {
  if (!isGameRunning || !ytPlayer) return

  const currentTime = ytPlayer.getCurrentTime() * 1000

  currentNotes.value.forEach(note => {
    if (note.hit || note.miss) {
      note.y = 1000
      return
    }

    const timeDiff = note.time - currentTime
    const positionPercent = JUDGE_LINE_Y - (timeDiff / FALL_TIME_MS * JUDGE_LINE_Y)
    
    note.y = positionPercent

    if (timeDiff < -200) {
      note.miss = true
      combo.value = 0
      score.value.miss++
      showPopup('MISS', 'text-red-500')
      
      if (score.value.miss === 10) {
        showCutin('/assets/images/miss10.webp', '焦らなくて大丈夫ですよ。まずは曲をよく聴いてみましょう。')
      } else if (score.value.miss === 20) {
        showCutin('/assets/images/miss20.webp', '難しい譜面ですね。私がついていますから、ご自身のペースで。')
      } else if (score.value.miss === 30) {
        showCutin('/assets/images/miss30.webp', '指先、疲れていませんか？ クリアだけが音楽ではありませんよ。')
      }

    // 見逃し判定（通り過ぎた）
    if (timeDiff < -200) {
      note.miss = true
      combo.value = 0
      score.value.miss++
      showPopup('MISS', 'text-red-500') // MISSポップアップを追加
    }
  })

  animationFrameId = requestAnimationFrame(updateGameLoop)
}

const stopGame = () => {
  isGameRunning = false
  if (animationFrameId) cancelAnimationFrame(animationFrameId)
  if (ytPlayer && typeof ytPlayer.stopVideo === 'function') ytPlayer.stopVideo()
}

const endGame = () => {
  stopGame()
  
  // ランク計算
  const total = score.value.perfect + score.value.great + score.value.good + score.value.miss
  if (total === 0) {
    resultRank.value = { rank: 'C', text: 'お疲れ様です。次はノーツを叩いてみましょう。', img: '/assets/images/icon.png' }
  } else {
    // スコアの精度（Accuracy）を計算
    const accuracy = (score.value.perfect * 100 + score.value.great * 50 + score.value.good * 10) / (total * 100)
    
    if (accuracy >= 0.95 && score.value.miss === 0) {
      resultRank.value = { rank: 'S', text: 'パーフェクト！素晴らしいビートでした。', img: '/assets/images/s.webp' }
    } else if (accuracy >= 0.8) {
      resultRank.value = { rank: 'A', text: '安定していますね。流石です。', img: '/assets/images/a.webp' }
    } else if (accuracy >= 0.5) {
      resultRank.value = { rank: 'B', text: '悪くないセッションでした。次も期待しています。', img: '/assets/images/b.webp' }
    } else {
      resultRank.value = { rank: 'C', text: '少し指が疲れているのかもしれませんね。', img: '/assets/images/c.webp' }
    }
  }
  
  gameState.value = 'result'
}

// --- 入力判定 ---
const handleKeyDown = (e: KeyboardEvent) => {
  if (gameState.value !== 'playing') return
  if (e.key === 'f' || e.key === 'F') hitLane(0)
  if (e.key === 'j' || e.key === 'J') hitLane(1)
}

const hitLane = (lane: number) => {
  if (!ytPlayer) return
  const currentTime = ytPlayer.getCurrentTime() * 1000

  // 叩いた瞬間の演出（RPGのattack SEを仮置き）
  triggerLaneFlash(lane)
  playSE('attack')

  const targetNote = currentNotes.value.find(n => !n.hit && !n.miss && n.lane === lane && Math.abs(n.time - currentTime) < 200)
  
  if (targetNote) {
    targetNote.hit = true
    const diff = Math.abs(targetNote.time - currentTime)
    
    combo.value++
    if (combo.value > maxCombo.value) maxCombo.value = combo.value

    if (combo.value === 50) {
      showCutin('/assets/images/50.webp', 'いいグルーヴです、管理人さん。')
    } else if (combo.value === 100) {
      showCutin('/assets/images/100.webp', '指先、走っていませんか？ ビートを感じて。')
    } else if (combo.value === 200) {
      showCutin('/assets/images/200.webp', '最高のセッションですね！')
    } else if (combo.value >= 300 && combo.value % 100 === 0) {
      // 300以降は100コンボごとに現在のコンボ数をセリフに入れて労う
      showCutin('/assets/images/300.webp', `${combo.value}コンボ…！完全にゾーンに入っていますね、圧巻です。`)
    }

    // 精度に応じたポップアップとスコア加算
    if (diff < 50) {
      score.value.perfect++
      showPopup('PERFECT', 'text-yellow-400')
    } else if (diff < 100) {
      score.value.great++
      showPopup('GREAT', 'text-emerald-400')
    } else {
      score.value.good++
      showPopup('GOOD', 'text-blue-400')
    }
  }
}
</script>

<template>
  <div class="bg-[url('/assets/images/erika-hero.jpg')] bg-fixed bg-cover bg-center min-h-screen pt-24 pb-12 select-none">
    
    <!-- 隠しYouTubeプレイヤー -->
    <div id="yt-bgm-player" class="absolute -top-[9999px] -left-[9999px] w-[1px] h-[1px]"></div>

    <div class="container mx-auto px-4 max-w-4xl">
      <h1 class="text-4xl font-black text-white text-center mb-8 drop-shadow-md">ERIKA BEAT</h1>

      <!-- 1. 選曲画面 -->
      <div v-if="gameState === 'select'" class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-6">
        <h2 class="text-xl font-bold text-erika mb-4">曲を選ぶ</h2>
        <div class="max-h-[60vh] overflow-y-auto custom-scrollbar pr-2 space-y-2">
          <div v-for="song in songs" :key="song.title" class="p-4 bg-zinc-900 border border-zinc-700 rounded-xl flex flex-col md:flex-row justify-between items-center gap-4 hover:border-erika transition-colors">
            <p class="text-white font-bold truncate w-full">{{ song.title }}</p>
            <div class="flex gap-2 shrink-0">
              <button @click="startGame(song, 'easy')" class="px-4 py-2 bg-emerald-600 text-white text-xs font-bold rounded-full hover:bg-emerald-500">Easy</button>
              <button @click="startGame(song, 'normal')" class="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-full hover:bg-blue-500">Normal</button>
              <button @click="startGame(song, 'hard')" class="px-4 py-2 bg-red-600 text-white text-xs font-bold rounded-full hover:bg-red-500">Hard</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. ローディング画面 -->
      <div v-if="gameState === 'loading'" class="text-center py-20">
        <p class="text-erika text-xl font-bold animate-pulse">YouTubeと譜面を同期中...</p>
      </div>

      <!-- 3. ゲームプレイ画面 -->
      <div v-if="gameState === 'playing'" class="relative max-w-md mx-auto h-[65vh] bg-black/80 backdrop-blur-sm border-2 border-zinc-700 rounded-xl overflow-hidden shadow-2xl">

        <div class="absolute top-0 left-0 w-1/2 h-full bg-cyan-400/30 transition-opacity duration-75 pointer-events-none" :class="laneFlashes[0] ? 'opacity-100' : 'opacity-0'"></div>
        <div class="absolute top-0 right-0 w-1/2 h-full bg-pink-400/30 transition-opacity duration-75 pointer-events-none" :class="laneFlashes[1] ? 'opacity-100' : 'opacity-0'"></div>

        <div class="absolute top-1/3 left-1/2 -translate-x-1/2 z-30 pointer-events-none flex flex-col items-center justify-center w-full h-32">
          <div v-for="popup in popups" :key="popup.id"
               class="absolute font-black text-4xl md:text-5xl italic drop-shadow-[0_0_15px_rgba(0,0,0,0.8)]"
               :class="popup.color"
               v-motion
               :initial="{ y: 10, opacity: 0, scale: 0.5 }"
               :enter="{ y: -40, opacity: 1, scale: 1.2, transition: { type: 'spring', stiffness: 250, damping: 10, mass: 1 } }"
               :leave="{ opacity: 0, y: -60, transition: { duration: 200 } }">
            {{ popup.text }}
          </div>
        </div>

        <!-- コンボ表示 -->
        <div class="absolute top-10 left-0 w-full text-center z-10 opacity-50 pointer-events-none">
          <p class="text-4xl font-black text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.8)]">{{ combo > 0 ? combo : '' }}</p>
        </div>

        <div v-if="activeCutin" 
             class="absolute top-1/4 -right-2 md:right-0 z-40 flex items-center gap-4 bg-gradient-to-l from-black/90 via-black/70 to-transparent p-4 pr-6 rounded-l-full pointer-events-none"
             v-motion
             :initial="{ x: 300, opacity: 0 }"
             :enter="{ x: 0, opacity: 1, transition: { type: 'spring', stiffness: 200, damping: 20 } }"
             :leave="{ x: 300, opacity: 0, transition: { duration: 300 } }">
          <div class="text-right">
            <p class="text-white text-sm md:text-base font-black italic drop-shadow-[0_2px_5px_rgba(0,0,0,1)] whitespace-nowrap">{{ activeCutin.text }}</p>
          </div>
          <img :src="activeCutin.img" class="w-20 h-20 md:w-24 md:h-24 object-cover rounded-full border-4 border-erika shadow-[0_0_15px_rgba(243,156,18,0.8)]">
        </div>

        <!-- 判定ライン -->
        <div class="absolute w-full h-1 bg-erika shadow-[0_0_10px_rgba(243,156,18,1)] z-10" :style="`top: ${JUDGE_LINE_Y}%;`"></div>

        <!-- レーン区切り線 -->
        <div class="absolute top-0 left-1/2 w-px h-full bg-white/20"></div>

        <!-- ノーツ描画 -->
        <div v-for="(note, idx) in currentNotes" :key="idx">
          <div v-if="note.y !== undefined && note.y >= 0 && note.y <= 100"
               class="absolute w-1/2 h-4 rounded-full shadow-[0_0_15px_rgba(255,255,255,0.5)] transform -translate-y-1/2"
               :class="note.lane === 0 ? 'left-0 bg-cyan-400' : 'right-0 bg-pink-400'"
               :style="`top: ${note.y}%;`">
          </div>
        </div>

        <!-- タップエリア（スマホ用） -->
        <div class="absolute bottom-0 left-0 w-full h-1/5 flex z-20">
          <div class="w-1/2 h-full active:bg-cyan-400/30 flex justify-center items-center text-cyan-400 font-bold opacity-30" @touchstart.prevent="hitLane(0)" @mousedown="hitLane(0)">F / 左タップ</div>
          <div class="w-1/2 h-full active:bg-pink-400/30 flex justify-center items-center text-pink-400 font-bold opacity-30" @touchstart.prevent="hitLane(1)" @mousedown="hitLane(1)">J / 右タップ</div>
        </div>
      </div>

      <!-- 4. リザルト画面 -->
      <div v-if="gameState === 'result'" class="bg-black/80 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center max-w-md mx-auto relative overflow-hidden">
        
        <!-- 背景にうっすらエリカの画像を透かせる -->
        <img src="/assets/images/beatresult.webp" class="absolute inset-0 w-full h-full object-cover opacity-30 pointer-events-none mix-blend-luminosity">
        <div class="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent"></div>

        <div class="relative z-10">
          <h2 class="text-2xl font-black text-erika mb-2 tracking-widest">SESSION RESULT</h2>
          
          <p class="text-6xl font-black mb-4 drop-shadow-[0_0_20px_rgba(255,255,255,0.3)] italic"
             :class="{'text-yellow-400': resultRank.rank === 'S', 'text-emerald-400': resultRank.rank === 'A', 'text-blue-400': resultRank.rank === 'B', 'text-zinc-400': resultRank.rank === 'C'}">
            RANK {{ resultRank.rank }}
          </p>
          
          <p class="text-white font-bold mb-8 drop-shadow-md">「{{ resultRank.text }}」</p>
          
          <div class="space-y-2 mb-8 text-left max-w-[200px] mx-auto text-lg font-bold text-white bg-black/40 p-4 rounded-xl border border-white/10 backdrop-blur-md">
            <div class="flex justify-between"><span class="text-yellow-400">Perfect</span><span>{{ score.perfect }}</span></div>
            <div class="flex justify-between"><span class="text-emerald-400">Great</span><span>{{ score.great }}</span></div>
            <div class="flex justify-between"><span class="text-blue-400">Good</span><span>{{ score.good }}</span></div>
            <div class="flex justify-between"><span class="text-red-500">Miss</span><span>{{ score.miss }}</span></div>
            <div class="border-t border-zinc-700 my-2 pt-2 flex justify-between"><span class="text-erika">Max Combo</span><span>{{ maxCombo }}</span></div>
          </div>
          
          <button @click="gameState = 'select'" class="px-8 py-3 bg-zinc-800 border border-zinc-600 text-white font-bold rounded-full hover:bg-zinc-700 transition-colors shadow-lg hover:-translate-y-1">
            選曲へ戻る
          </button>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 2px; }
</style>