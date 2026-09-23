<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// --- 型定義 ---
interface GalleryImage {
  file: string;
  alt: string;
  enemy_name?: string;
}

interface GalleryCategory {
  name: string;
  images: GalleryImage[];
}

// --- 状態管理 ---
const route = useRoute()
const router = useRouter()

const galleryData = ref<GalleryCategory[]>([])
const currentCat = ref<string>('')
const selectedImg = ref<string | null>(null)

const INITIAL_LIMIT = 8
const LOAD_STEP = 8
const displayLimit = ref(INITIAL_LIMIT)

// カテゴリ一覧
const categories = computed(() => galleryData.value.map(c => c.name))

// ページネーション設定 (8個単位)
const catCurrentPage = ref(1)
const catsPerPage = 8

const catTotalPages = computed(() => Math.ceil(categories.value.length / catsPerPage))

const paginatedCategories = computed(() => {
  const start = (catCurrentPage.value - 1) * catsPerPage
  return categories.value.slice(start, start + catsPerPage)
})

// --- アクション ---
const prevCatPage = () => {
  if (catCurrentPage.value > 1) catCurrentPage.value--
}

const nextCatPage = () => {
  if (catCurrentPage.value < catTotalPages.value) catCurrentPage.value++
}

const goToCatPage = (page: number) => {
  catCurrentPage.value = page
}

const changeCategory = (cat: string) => {
  currentCat.value = cat
  window.scrollTo({ top: 0, behavior: 'smooth' })
  // URLのクエリパラメータも同期する
  router.replace({ query: { folder: cat } })
}

// カテゴリが切り替わったら表示枚数をリセット
watch(currentCat, () => {
  displayLimit.value = INITIAL_LIMIT
})

// 表示する画像の算出
const displayedImages = computed(() => {
  const currentData = galleryData.value.find(c => c.name === currentCat.value)
  if (!currentData || !currentData.images) return []
  return currentData.images.slice(0, displayLimit.value)
})

const hasMoreImages = computed(() => {
  const currentData = galleryData.value.find(c => c.name === currentCat.value)
  if (!currentData || !currentData.images) return false
  return displayLimit.value < currentData.images.length
})

const loadMore = () => {
  displayLimit.value += LOAD_STEP
}

// --- データ取得 ---
const fetchGallery = async () => {
  try {
    // キャッシュ回避のためクエリを付与
    const res = await fetch(`/assets/gallery.json?t=${new Date().getTime()}`)
    let data = await res.json()

    // 念のための後方互換性対応
    if (!Array.isArray(data)) {
      data = Object.keys(data).map(key => ({
        name: key,
        images: data[key]
      })).sort((a, b) => b.name.localeCompare(a.name))
    }

    galleryData.value = data

    // 初期フォルダの決定（URLクエリ優先）
    const targetFolder = route.query.folder as string

    if (targetFolder && categories.value.includes(targetFolder)) {
      currentCat.value = targetFolder
      const catIndex = categories.value.indexOf(targetFolder)
      catCurrentPage.value = Math.floor(catIndex / catsPerPage) + 1
    } else if (categories.value.length > 0) {
      currentCat.value = categories.value[0]
    }
  } catch (e) {
    console.error("Failed to load gallery data.", e)
  }
}

// --- モーダル制御 ---
const openModal = (cat: string, img: string) => {
  selectedImg.value = `/assets/images/gallery/${cat}/${img}`
  document.body.style.overflow = 'hidden' // 背景スクロールロック
}

const closeModal = () => {
  selectedImg.value = null
  document.body.style.overflow = '' // スクロールロック解除
}

onMounted(fetchGallery)
</script>

<template>
  <div class="bg-[url('/assets/images/erika-hero.jpg')] bg-fixed bg-cover bg-center min-h-screen pt-24 pb-20">
    <div class="container mx-auto px-4 max-w-6xl">
      <h1 class="text-4xl md:text-5xl font-black text-white text-center mb-12 drop-shadow-[0_4px_10px_rgba(0,0,0,0.5)]">
        ERIKA GALLERY
      </h1>

      <!-- 上部 フォルダナビゲーション -->
      <div v-if="categories.length > 0" class="mb-10 flex flex-col items-center z-10 relative">
        <div class="flex items-center justify-center gap-2 md:gap-4 bg-black/60 backdrop-blur-md p-2 rounded-full border border-white/10 shadow-lg max-w-full">
          <!-- 左ボタン -->
          <button @click="prevCatPage" :disabled="catCurrentPage === 1" 
                  class="w-8 h-8 md:w-10 md:h-10 shrink-0 flex items-center justify-center rounded-full bg-zinc-800 text-white hover:bg-zinc-700 disabled:opacity-30 transition-colors">
            ◀
          </button>

          <!-- カテゴリタブ -->
          <div class="flex gap-1 md:gap-2 overflow-x-auto hide-scrollbar scroll-smooth w-full max-w-[60vw] md:max-w-3xl px-2">
            <button v-for="cat in paginatedCategories" :key="cat" 
                    @click="changeCategory(cat)"
                    class="px-4 py-2 rounded-full text-xs md:text-sm font-bold transition-all whitespace-nowrap border border-transparent"
                    :class="currentCat === cat 
                      ? 'bg-erika text-black shadow-[0_0_15px_rgba(243,156,18,0.5)]' 
                      : 'text-zinc-400 hover:text-white hover:bg-white/10 hover:border-white/20'">
              {{ cat }}
            </button>
          </div>

          <!-- 右ボタン -->
          <button @click="nextCatPage" :disabled="catCurrentPage === catTotalPages" 
                  class="w-8 h-8 md:w-10 md:h-10 shrink-0 flex items-center justify-center rounded-full bg-zinc-800 text-white hover:bg-zinc-700 disabled:opacity-30 transition-colors">
            ▶
          </button>
        </div>
      </div>

      <!-- ギャラリーグリッド -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
        <div v-for="img in displayedImages" :key="img.file" 
             class="group rounded-xl overflow-hidden bg-black/40 backdrop-blur-sm border border-white/10 hover:border-erika/50 hover:shadow-[0_0_20px_rgba(243,156,18,0.3)] transition-all cursor-pointer relative"
             @click="openModal(currentCat, img.file)">
          <div class="aspect-[4/5] overflow-hidden bg-zinc-900">
            <!-- 擬似遅延ロード（loading="lazy"） -->
            <img :src="`/assets/images/gallery/${currentCat}/${img.file}`" :alt="img.alt" loading="lazy"
                 class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110">
          </div>
          <!-- ホバー時の情報レイヤー -->
          <div class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4">
            <div>
              <p class="text-[10px] text-erika-light font-bold mb-1">{{ currentCat }}</p>
              <p class="text-xs text-white line-clamp-2 leading-tight">{{ img.enemy_name || img.alt }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 続きを表示ボタン -->
      <div v-if="hasMoreImages" class="text-center mt-12 mb-12">
        <button @click="loadMore" 
                class="inline-block px-10 py-3 bg-[#f39c12] text-zinc-900 font-bold rounded-full shadow-[0_4px_15px_rgba(0,0,0,0.5)] hover:bg-[#f5b041] hover:shadow-[0_0_25px_rgba(243,156,18,0.5)] hover:-translate-y-1 transition-all">
          ▼ 続きを表示 (Load More)
        </button>
      </div>

      <!-- 下部 フォルダナビゲーション（上部と同じUIを再利用） -->
      <div v-if="categories.length > 0" class="mt-20 pt-10 border-t border-white/10">
        <p class="text-white text-center mb-6 font-medium">別のフォルダを見る</p>
        <div class="flex flex-col items-center">
          <div class="flex items-center justify-center gap-2 bg-black/40 backdrop-blur-md p-2 rounded-full border border-white/5">
             <button @click="prevCatPage" :disabled="catCurrentPage === 1" class="w-8 h-8 flex items-center justify-center rounded-full bg-zinc-800 text-white hover:bg-zinc-700 disabled:opacity-30 transition-colors">◀</button>
             <div class="flex gap-1 overflow-x-auto hide-scrollbar max-w-[60vw]">
                <button v-for="cat in paginatedCategories" :key="cat" @click="changeCategory(cat)"
                        class="px-3 py-1.5 rounded-full text-xs font-bold transition-all whitespace-nowrap"
                        :class="currentCat === cat ? 'bg-zinc-200 text-black' : 'text-zinc-500 hover:text-white hover:bg-white/10'">
                  {{ cat }}
                </button>
             </div>
             <button @click="nextCatPage" :disabled="catCurrentPage === catTotalPages" class="w-8 h-8 flex items-center justify-center rounded-full bg-zinc-800 text-white hover:bg-zinc-700 disabled:opacity-30 transition-colors">▶</button>
          </div>
        </div>
      </div>

    </div>

    <!-- 画像拡大モーダル -->
    <Transition name="fade">
      <div v-if="selectedImg" 
           class="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md p-2 md:p-6" 
           @click="closeModal">
        <div class="relative max-w-5xl max-h-full w-full flex justify-center items-center">
          <img :src="selectedImg" alt="Enlarged view" 
               class="max-w-full max-h-[90vh] object-contain rounded-lg shadow-[0_0_50px_rgba(0,0,0,0.8)]" 
               @click.stop>
          <button class="absolute top-0 right-0 md:-top-4 md:-right-4 w-12 h-12 flex items-center justify-center bg-black/50 hover:bg-erika text-white hover:text-black rounded-full text-2xl transition-all" 
                  @click="closeModal">
            &times;
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* 横スクロールバーを隠すユーティリティ */
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* VueのTransitionコンポーネント用アニメーション */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, backdrop-filter 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  backdrop-filter: blur(0px);
}
</style>