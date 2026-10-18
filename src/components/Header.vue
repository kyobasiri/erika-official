<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

// ==========================================
// ヘッダーのメニュー
//   ・項目は下の配列で管理する（PC とスマホで同じものを使う）
//   ・GAMES は、マウスを乗せたときに加えて、クリック（タップ）でも開閉できる
//     （iPad など、マウスの無い端末でも開けるように）
// ==========================================

const navItems = [
  { to: '/concept', label: 'Concept', note: 'プロジェクトの想い' },
  { to: '/blog', label: 'Activities', note: '最新記事・観測日誌' },
  { to: '/gallery', label: 'Gallery', note: 'AIアート保管庫' },
  { to: '/words', label: 'Words', note: 'エリカの好きな言葉' },
  { to: '/gear', label: 'Gear', note: '使用機材・システム' },
]

const gameItems = [
  { to: '/beat', label: 'ERIKA BEAT', note: 'YouTube同期リズムゲーム', mobileNote: 'リズムゲーム', highlight: true },
  { to: '/rpg', label: 'RPG Battle', note: 'ブラウザRPG・エリカ討伐戦', mobileNote: 'エリカ討伐戦', highlight: false },
  { to: '/game', label: 'Memory Game', note: 'AIアート神経衰弱', mobileNote: '神経衰弱', highlight: false },
  { to: '/labyrinth', label: 'Labyrinth Escape', note: '迷宮からの脱出ゲーム', mobileNote: 'ダンジョン', highlight: false },
]

// スマホ用メニューの開閉状態
const isMobileMenuOpen = ref(false)
// スマホ用GAMESメニューのアコーディオン開閉状態
const isMobileGamesOpen = ref(false)
// PC用GAMESメニューを、クリックで開いているか（マウスを乗せたときは CSS の hover で開く）
const isGamesOpen = ref(false)
// GAMES メニュー全体（外側をクリックしたら閉じる判定に使う）
const gamesMenu = ref<HTMLElement | null>(null)

// ページを移動したら、開いているメニューをすべて閉じる
const route = useRoute()
watch(() => route.fullPath, () => {
  isMobileMenuOpen.value = false
  isGamesOpen.value = false
})

// GAMES メニューの外側をクリック（タップ）したら閉じる
function onDocumentClick(event: MouseEvent) {
  if (isGamesOpen.value && gamesMenu.value && !gamesMenu.value.contains(event.target as Node)) {
    isGamesOpen.value = false
  }
}
// Esc キーでも閉じる
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') isGamesOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <header class="fixed top-0 left-0 w-full z-50 bg-black/60 backdrop-blur-md border-b border-white/10">
    <div class="container mx-auto px-4 h-16 flex items-center justify-between">

      <!-- ロゴ -->
      <router-link to="/" class="text-2xl font-black text-white tracking-widest drop-shadow-md">
        ERIKA<span class="text-erika">.</span>
      </router-link>

      <!-- PC用ナビゲーション -->
      <nav class="hidden md:flex items-center gap-6 lg:gap-8" aria-label="メインメニュー">

        <!-- 通常の項目（マウスを乗せると説明が出る） -->
        <div v-for="item in navItems" :key="item.to" class="relative group">
          <router-link :to="item.to" class="text-sm font-bold text-zinc-300 hover:text-erika-light transition-colors py-2">
            {{ item.label }}
          </router-link>
          <div class="absolute top-full left-1/2 -translate-x-1/2 mt-3 px-3 py-1.5 bg-zinc-800 border border-zinc-700 text-xs text-white rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 whitespace-nowrap shadow-xl before:content-[''] before:absolute before:-top-1.5 before:left-1/2 before:-translate-x-1/2 before:border-4 before:border-transparent before:border-b-zinc-800 pointer-events-none">
            {{ item.note }}
          </div>
        </div>

        <!-- GAMES (ドロップダウンメニュー) -->
        <div ref="gamesMenu" class="relative group">
          <!-- クリック（タップ）でも開閉できるよう、ボタンにする -->
          <button
            type="button"
            class="text-sm font-bold text-erika hover:text-amber-300 transition-colors py-2 flex items-center gap-1"
            :aria-expanded="isGamesOpen"
            aria-haspopup="true"
            aria-controls="games-menu"
            @click="isGamesOpen = !isGamesOpen"
          >
            <span class="animate-pulse">▶</span> GAMES
            <!-- 下向き矢印アイコン（開いているときは回転） -->
            <svg
              class="w-4 h-4 transition-transform duration-300 group-hover:rotate-180"
              :class="isGamesOpen ? 'rotate-180' : ''"
              fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"
            ><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
          </button>

          <!-- ドロップダウンの中身（透明な上部余白を入れてホバー切れを防ぐ）。hover でもクリックでも開く -->
          <div
            id="games-menu"
            class="absolute top-full right-0 md:-left-4 pt-4 transition-all duration-300 group-hover:opacity-100 group-hover:visible"
            :class="isGamesOpen ? 'opacity-100 visible' : 'opacity-0 invisible'"
          >
            <div class="w-56 bg-zinc-800/95 backdrop-blur-md border border-zinc-700/80 rounded-xl shadow-2xl overflow-hidden flex flex-col py-2 relative before:content-[''] before:absolute before:-top-2 before:left-10 before:border-4 before:border-transparent before:border-b-zinc-700">
              <router-link
                v-for="(game, index) in gameItems"
                :key="game.to"
                :to="game.to"
                class="px-5 py-3 hover:bg-white/10 transition-colors flex flex-col group/item"
                :class="index > 0 ? 'border-t border-zinc-700/50' : ''"
              >
                <span
                  class="text-sm font-bold"
                  :class="game.highlight ? 'text-amber-400 group-hover/item:text-amber-300' : 'text-zinc-200 group-hover/item:text-white'"
                >{{ game.label }}</span>
                <span class="text-[10px] text-zinc-400 mt-0.5">{{ game.note }}</span>
              </router-link>
            </div>
          </div>
        </div>
      </nav>

      <!-- スマホ用ハンバーガーボタン -->
      <button
        type="button"
        class="md:hidden text-white"
        :aria-expanded="isMobileMenuOpen"
        :aria-label="isMobileMenuOpen ? 'メニューを閉じる' : 'メニューを開く'"
        @click="isMobileMenuOpen = !isMobileMenuOpen"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
          <path v-if="!isMobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>

    </div>

    <!-- スマホ用ドロップダウンメニュー（リンクを押したら閉じる。いま開いているページのリンクを押したときも閉じるように @click でも閉じる） -->
    <div v-if="isMobileMenuOpen" class="md:hidden bg-zinc-900 border-b border-white/10 shadow-xl pb-2">
      <nav class="flex flex-col px-4 py-4 space-y-4" aria-label="メインメニュー">
        <router-link v-for="item in navItems" :key="item.to" :to="item.to" class="text-zinc-300 hover:text-erika" @click="isMobileMenuOpen = false">
          <span class="font-bold">{{ item.label }}</span> <span class="text-xs text-zinc-500 ml-2">{{ item.note }}</span>
        </router-link>

        <!-- スマホ用 GAMES (アコーディオン) -->
        <div class="pt-2 border-t border-zinc-800">
          <button
            type="button"
            class="w-full flex items-center justify-between text-erika hover:text-amber-300 font-bold py-1 outline-none"
            :aria-expanded="isMobileGamesOpen"
            @click="isMobileGamesOpen = !isMobileGamesOpen"
          >
            <span class="flex items-center gap-2"><span class="animate-pulse">▶</span> GAMES</span>
            <!-- 矢印の回転 -->
            <svg class="w-5 h-5 transition-transform duration-300" :class="isMobileGamesOpen ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
          </button>

          <!-- 中身 -->
          <div v-show="isMobileGamesOpen" class="flex flex-col pl-5 mt-3 space-y-4 border-l-2 border-zinc-800 ml-2">
            <router-link
              v-for="game in gameItems"
              :key="game.to"
              :to="game.to"
              :class="game.highlight ? 'text-amber-400 hover:text-amber-300' : 'text-zinc-300 hover:text-white'"
              @click="isMobileMenuOpen = false"
            >
              <span class="font-bold block">{{ game.label }}</span>
              <span class="text-[10px]" :class="game.highlight ? 'text-amber-500/70' : 'text-zinc-500'">{{ game.mobileNote }}</span>
            </router-link>
          </div>
        </div>
      </nav>
    </div>
  </header>
</template>