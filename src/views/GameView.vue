<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

// --- 型定義 ---
interface Card {
  id: string
  pairId: number
  url: string
  isFlipped: boolean
  isMatched: boolean
}
interface Tag {
  label: string
  prompt: string
}
interface Song {
  embed_url?: string
  share_url?: string
  youtube_id?: string
}

// --- 状態管理 ---
const galleryData = ref<any[]>([])
const uniqueImages = ref<string[]>([])
const cards = ref<Card[]>([])
const flippedCards = ref<Card[]>([])
const matchedPairs = ref(0)
const mistakes = ref(0)
const isLocked = ref(false)
const isLoading = ref(true)
const gameState = ref<'memorize' | 'playing' | 'gameover' | 'clear'>('memorize')

// --- BGM関連 ---
const thePillowsSongs = ref<Song[]>([])
let bgmPlayer: any = null

// --- 報酬関連 ---
const hasGeneratedReward = ref(false)
const isGeneratingReward = ref(false)
const rewardImageUrl = ref<string | null>(null)
const freeTextInput = ref('')
const rewardCategories = ref<Record<string, Record<string, string>>>({})
const selectedTags = ref<Tag[]>([])

// --- BGM制御 ---
const initAndPlayBGM = () => {
  if (thePillowsSongs.value.length === 0) return

  const randomSong = thePillowsSongs.value[Math.floor(Math.random() * thePillowsSongs.value.length)]
  let targetVideoId = 'xUboS2Fw1-o'
  if (randomSong.embed_url) targetVideoId = randomSong.embed_url.split('/').pop() || targetVideoId
  else if (randomSong.share_url) targetVideoId = randomSong.share_url.split('/').pop() || targetVideoId

  const loadBGMPlayer = () => {
    // @ts-ignore
    bgmPlayer = new window.YT.Player('bgm-player', {
      videoId: targetVideoId,
      playerVars: { playsinline: 1, loop: 1, playlist: targetVideoId },
      events: {
        onReady: (event: any) => {
          event.target.setVolume(20)
          event.target.playVideo()
        }
      }
    })
  }

  // @ts-ignore
  if (!window.YT) {
    const tag = document.createElement('script')
    tag.src = "https://www.youtube.com/iframe_api"
    const firstScriptTag = document.getElementsByTagName('script')[0]
    firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag)
    // @ts-ignore
    window.onYouTubeIframeAPIReady = loadBGMPlayer
  } else {
    // 既存のプレイヤーがあれば破棄して作り直す
    if (bgmPlayer && typeof bgmPlayer.destroy === 'function') {
      bgmPlayer.destroy()
    }
    loadBGMPlayer()
  }
}

const stopBGM = () => {
  if (bgmPlayer && typeof bgmPlayer.stopVideo === 'function') {
    bgmPlayer.stopVideo()
  }
}

// --- 報酬画像生成 ---
const isTagSelected = (label: string) => selectedTags.value.some(t => t.label === label)

const toggleRewardTag = (label: string, prompt: string) => {
  const index = selectedTags.value.findIndex(t => t.label === label)
  if (index > -1) {
    selectedTags.value.splice(index, 1)
  } else {
    selectedTags.value.push({ label, prompt })
  }
}

const generateRewardImage = async () => {
  if (hasGeneratedReward.value) return
  isGeneratingReward.value = true

  const basePrompt = "masterpiece, best quality, ultra_detailed, very aesthetic"
  const promptsOnly = selectedTags.value.map(t => t.prompt)
  const finalPromptArray = [basePrompt, ...promptsOnly]
  if (freeTextInput.value) finalPromptArray.push(freeTextInput.value)
  const finalPrompt = finalPromptArray.join(', ')

  try {
    const res = await fetch('/api/generate-avatar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: finalPrompt })
    })
    if (!res.ok) throw new Error("画像生成に失敗しました")
    const data = await res.json()
    rewardImageUrl.value = data.avatarUrl
    hasGeneratedReward.value = true
  } catch (e) {
    console.error(e)
    alert("画像の生成に失敗しました。時間をおいて再試行してください。")
  } finally {
    isGeneratingReward.value = false
  }
}

// --- ゲームロジック ---
const initGame = () => {
  stopBGM()
  matchedPairs.value = 0
  mistakes.value = 0
  flippedCards.value = []
  isLocked.value = true
  gameState.value = 'memorize'
  hasGeneratedReward.value = false
  rewardImageUrl.value = null
  freeTextInput.value = ''
  selectedTags.value = []

  let allImages: string[] = []
  galleryData.value.forEach(folder => {
    folder.images.forEach((img: any) => {
      allImages.push(`/assets/images/gallery/${folder.name}/${img.file}`)
    })
  })

  const selectedImages = allImages.sort(() => 0.5 - Math.random()).slice(0, 8)
  uniqueImages.value = selectedImages

  let deck: Card[] = []
  selectedImages.forEach((url, index) => {
    deck.push({ id: `${index}a`, pairId: index, url, isFlipped: true, isMatched: false })
    deck.push({ id: `${index}b`, pairId: index, url, isFlipped: true, isMatched: false })
  })

  cards.value = deck.sort(() => 0.5 - Math.random())

  setTimeout(() => {
    cards.value.forEach(card => card.isFlipped = false)
    gameState.value = 'playing'
    isLocked.value = false
    initAndPlayBGM()
  }, 3000)
}

const flipCard = (card: Card) => {
  if (isLocked.value || card.isFlipped || card.isMatched || gameState.value !== 'playing') return

  card.isFlipped = true
  flippedCards.value.push(card)

  if (flippedCards.value.length === 2) {
    checkMatch()
  }
}

const checkMatch = () => {
  isLocked.value = true
  const [card1, card2] = flippedCards.value

  if (card1.pairId === card2.pairId) {
    card1.isMatched = true
    card2.isMatched = true
    matchedPairs.value++
    flippedCards.value = []

    if (matchedPairs.value === 8) {
      stopBGM()
      setTimeout(() => { gameState.value = 'clear' }, 500)
    } else {
      isLocked.value = false
    }
  } else {
    mistakes.value++
    if (mistakes.value >= 4) {
      stopBGM()
      setTimeout(() => { gameState.value = 'gameover' }, 800)
    } else {
      setTimeout(() => {
        card1.isFlipped = false
        card2.isFlipped = false
        flippedCards.value = []
        isLocked.value = false
      }, 1000)
    }
  }
}

onMounted(async () => {
  try {
    const res = await fetch(`/assets/gallery.json?t=${new Date().getTime()}`)
    galleryData.value = await res.json()
    initGame()
  } catch (e) {
    console.error("Gallery data fetch failed", e)
  } finally {
    isLoading.value = false
  }

  try {
    const res = await fetch('/assets/thepillows_releases_tab.json')
    if (res.ok) thePillowsSongs.value = await res.json()
  } catch (e) {}

  try {
    const res = await fetch('/assets/rpgclear.json')
    if (res.ok) rewardCategories.value = await res.json()
  } catch (e) {}
})

// 他のページに遷移する際にBGMを止める
onUnmounted(() => {
  stopBGM()
  if (bgmPlayer && typeof bgmPlayer.destroy === 'function') {
    bgmPlayer.destroy()
  }
})
</script>

<template>
  <div class="bg-zinc-950 min-h-screen pt-24 pb-12">
    <!-- 画面外に配置するBGM用プレイヤー -->
    <div id="bgm-player" class="absolute -top-[9999px] -left-[9999px] w-[1px] h-[1px] overflow-hidden"></div>

    <div class="container mx-auto px-4 text-center max-w-4xl">
      <h1 class="text-4xl md:text-5xl font-black text-white mb-8 drop-shadow-md">ERIKA MEMORY</h1>

      <div v-if="isLoading" class="text-erika animate-pulse my-12 text-lg font-bold">
        ギャラリーデータを読み込んでいます...
      </div>

      <div v-else>
        <!-- ステータス表示 -->
        <div class="bg-black/40 backdrop-blur-md border border-white/10 rounded-2xl p-6 mb-8 max-w-2xl mx-auto shadow-lg">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <p class="text-xs text-zinc-400 font-bold mb-1">揃ったペア</p>
              <p class="text-3xl font-black text-white">{{ matchedPairs }} <span class="text-lg text-zinc-500">/ 8</span></p>
            </div>
            <div>
              <p class="text-xs text-zinc-400 font-bold mb-1">お手つき制限</p>
              <p class="text-3xl font-black" :class="mistakes >= 3 ? 'text-red-500' : 'text-erika'">
                {{ mistakes }} <span class="text-lg text-zinc-500">/ 4</span>
              </p>
            </div>
          </div>
        </div>

        <div v-if="gameState === 'memorize'" class="bg-erika/20 border border-erika text-erika-light p-4 rounded-xl max-w-2xl mx-auto mb-8 font-bold animate-pulse">
          配置を覚えてください！ (3秒後に裏返ります)
        </div>

        <!-- ゲームボード -->
        <div v-show="gameState !== 'clear'" class="memory-game max-w-xl mx-auto">
          <div v-for="card in cards" :key="card.id" 
               class="memory-card" 
               :class="{ 'is-flipped': card.isFlipped, 'opacity-0': card.isMatched }"
               @click="flipCard(card)">
            <div class="card-inner">
              <div class="card-face card-front bg-zinc-800 border-2 border-zinc-600 text-erika font-black text-4xl flex items-center justify-center rounded-xl shadow-md">
                E
              </div>
              <div class="card-face card-back rounded-xl overflow-hidden border-2 border-erika shadow-[0_0_15px_rgba(243,156,18,0.5)]">
                <img :src="card.url" alt="Gallery Image" class="w-full h-full object-cover">
              </div>
            </div>
          </div>
        </div>

        <!-- ゲームオーバー表示 -->
        <div v-if="gameState === 'gameover'" class="bg-red-500/20 border border-red-500 text-red-200 p-8 rounded-2xl max-w-2xl mx-auto mt-8 shadow-[0_0_30px_rgba(239,68,68,0.3)]">
          <h2 class="text-3xl font-black mb-2">Game Over...</h2>
          <p class="mb-6">お手つきが4回に達しました。</p>
          <button @click="initGame" class="px-8 py-3 bg-red-600 text-white font-bold rounded-full hover:bg-red-500 transition-colors shadow-lg hover:-translate-y-1">
            リトライする
          </button>
        </div>

        <!-- クリア表示 -->
        <div v-if="gameState === 'clear'" class="max-w-3xl mx-auto mt-8">
          <h2 class="text-5xl font-black text-erika mb-4 drop-shadow-[0_0_20px_rgba(243,156,18,0.8)] animate-bounce">
            Clear!!
          </h2>
          <p class="mb-8 text-white font-bold text-lg">見事すべての記憶を取り戻しました！</p>

          <!-- スライダー演出 -->
          <div class="overflow-hidden whitespace-nowrap mb-12 relative h-32 rounded-xl border border-white/10">
            <div class="inline-block animate-marquee h-full">
              <template v-for="loop in 2" :key="loop">
                <img v-for="img in uniqueImages" :key="img + loop" :src="img" class="h-full w-24 object-cover inline-block mx-1 rounded shadow-md border border-zinc-700">
              </template>
            </div>
          </div>

          <!-- 画像生成報酬 -->
          <div class="bg-black/60 backdrop-blur-md border-2 border-erika rounded-2xl p-6 md:p-8 text-left shadow-[0_0_30px_rgba(243,156,18,0.2)] mb-10">
            <h3 class="text-2xl font-black text-erika text-center mb-2">🎁 クリア特典：記憶の具現化</h3>
            <p class="text-sm text-zinc-400 text-center mb-8">
              クリアの記念に、Cloudflare Workers AIの力で新しい姿を1枚生成できます。
            </p>

            <div v-if="!hasGeneratedReward">
              <!-- 選択タグエリア -->
              <div class="bg-black/50 border border-dashed border-erika rounded-xl p-4 min-h-[80px] mb-6">
                <p class="text-xs text-zinc-500 font-bold mb-3">【組み込まれるプロンプト（クリックで解除）】</p>
                <div class="flex flex-wrap gap-2">
                  <span v-for="tag in selectedTags" :key="tag.label" 
                        @click="toggleRewardTag(tag.label, tag.prompt)"
                        class="px-3 py-1 bg-erika text-zinc-900 font-bold text-sm rounded-full cursor-pointer hover:bg-erika-light transition-colors flex items-center gap-1 shadow-md">
                    {{ tag.label }}
                    <span class="text-zinc-800 hover:text-black font-black leading-none ml-1">&times;</span>
                  </span>
                  <p v-if="selectedTags.length === 0" class="text-sm text-zinc-600">下のリストから要素を選んでください。</p>
                </div>
              </div>

              <!-- タグリスト -->
              <div class="max-h-64 overflow-y-auto pr-2 border-t border-white/10 pt-6 mb-8 custom-scrollbar">
                <div v-for="(prompts, category) in rewardCategories" :key="category" class="mb-6">
                  <p class="font-bold text-erika mb-3">{{ category }}</p>
                  <div class="flex flex-wrap gap-2">
                    <button v-for="(prompt, label) in prompts" :key="label"
                            @click="toggleRewardTag(label, prompt)"
                            class="px-3 py-1.5 border rounded-full text-sm transition-colors"
                            :class="isTagSelected(label) ? 'hidden' : 'border-zinc-700 text-zinc-400 hover:bg-white/10 hover:text-white'">
                      {{ label }}
                    </button>
                  </div>
                </div>
              </div>

              <div class="mb-6">
                <label class="block text-xs font-bold text-zinc-500 mb-2">自由入力（任意）</label>
                <input type="text" v-model="freeTextInput" placeholder="自由に入力できます"
                       class="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-erika transition-colors">
              </div>

              <div class="text-center">
                <button @click="generateRewardImage" :disabled="isGeneratingReward || (selectedTags.length === 0 && !freeTextInput)"
                        class="px-8 py-4 bg-erika text-black font-black rounded-full shadow-[0_4px_15px_rgba(243,156,18,0.4)] hover:bg-erika-light disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                  {{ isGeneratingReward ? '具現化中...' : '画像を生成する (1回のみ)' }}
                </button>
              </div>
            </div>

            <!-- 生成結果 -->
            <div v-else class="text-center py-6">
              <p class="text-emerald-400 font-black text-xl mb-6">生成完了！</p>
              <img :src="rewardImageUrl!" class="w-full max-w-sm mx-auto rounded-xl border-4 border-erika shadow-[0_0_30px_rgba(243,156,18,0.5)] object-cover mb-6">
              <a :href="rewardImageUrl!" target="_blank" class="inline-block px-6 py-2 bg-zinc-800 text-white font-bold rounded-full hover:bg-zinc-700 transition-colors">
                拡大して保存
              </a>
            </div>
          </div>

          <button @click="initGame" class="px-10 py-4 bg-zinc-800 text-white font-black text-lg rounded-full hover:bg-zinc-700 border border-zinc-600 shadow-xl transition-all hover:-translate-y-1">
            次の記憶（別の画像）に挑戦する
          </button>
        </div>

        <!-- プレイ中のリセットボタン -->
        <div v-if="gameState === 'playing'" class="mt-10">
          <button @click="initGame" class="px-6 py-2 bg-zinc-900 border border-zinc-700 text-zinc-400 text-sm font-bold rounded-full hover:bg-zinc-800 hover:text-white transition-colors">
            リセットして引き直す
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* カスタムスクロールバー */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

/* カードゲームのグリッドと3Dアニメーション */
.memory-game {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  perspective: 1000px;
}
@media (max-width: 640px) {
  .memory-game {
    gap: 8px;
  }
}

.memory-card {
  aspect-ratio: 4/5;
  cursor: pointer;
  position: relative;
  transition: transform 0.2s, opacity 0.5s ease-out;
  transform-style: preserve-3d;
}

.memory-card:active {
  transform: scale(0.97);
}

.card-inner {
  width: 100%;
  height: 100%;
  position: relative;
  transition: transform 0.6s cubic-bezier(0.4, 0.0, 0.2, 1);
  transform-style: preserve-3d;
}

.memory-card.is-flipped .card-inner {
  transform: rotateY(180deg);
}

.card-face {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.card-back {
  transform: rotateY(180deg);
}

/* クリア時の無限スクロールアニメーション */
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
.animate-marquee {
  animation: marquee 20s linear infinite;
}
</style>