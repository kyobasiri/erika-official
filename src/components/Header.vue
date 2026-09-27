<script setup lang="ts">
import { ref } from 'vue'

// スマホ用メニューの開閉状態
const isMobileMenuOpen = ref(false)
// スマホ用GAMESメニューのアコーディオン開閉状態
const isMobileGamesOpen = ref(false)
</script>

<template>
  <header class="fixed top-0 left-0 w-full z-50 bg-black/60 backdrop-blur-md border-b border-white/10">
    <div class="container mx-auto px-4 h-16 flex items-center justify-between">
      
      <!-- ロゴ -->
      <router-link to="/" class="text-2xl font-black text-white tracking-widest drop-shadow-md">
        ERIKA<span class="text-erika">.</span>
      </router-link>

      <!-- PC用ナビゲーション -->
      <nav class="hidden md:flex items-center gap-6 lg:gap-8">
        
        <!-- ナビアイテム 1: Concept -->
        <div class="relative group">
          <router-link to="/concept" class="text-sm font-bold text-zinc-300 hover:text-erika-light transition-colors py-2">
            Concept
          </router-link>
          <div class="absolute top-full left-1/2 -translate-x-1/2 mt-3 px-3 py-1.5 bg-zinc-800 border border-zinc-700 text-xs text-white rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 whitespace-nowrap shadow-xl before:content-[''] before:absolute before:-top-1.5 before:left-1/2 before:-translate-x-1/2 before:border-4 before:border-transparent before:border-b-zinc-800 pointer-events-none">
            プロジェクトの想い
          </div>
        </div>

        <!-- ナビアイテム 2: Activities -->
        <div class="relative group">
          <router-link to="/blog" class="text-sm font-bold text-zinc-300 hover:text-erika-light transition-colors py-2">
            Activities
          </router-link>
          <div class="absolute top-full left-1/2 -translate-x-1/2 mt-3 px-3 py-1.5 bg-zinc-800 border border-zinc-700 text-xs text-white rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 whitespace-nowrap shadow-xl before:content-[''] before:absolute before:-top-1.5 before:left-1/2 before:-translate-x-1/2 before:border-4 before:border-transparent before:border-b-zinc-800 pointer-events-none">
            最新記事・観測日誌
          </div>
        </div>

        <!-- ナビアイテム 3: Gallery -->
        <div class="relative group">
          <router-link to="/gallery" class="text-sm font-bold text-zinc-300 hover:text-erika-light transition-colors py-2">
            Gallery
          </router-link>
          <div class="absolute top-full left-1/2 -translate-x-1/2 mt-3 px-3 py-1.5 bg-zinc-800 border border-zinc-700 text-xs text-white rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 whitespace-nowrap shadow-xl before:content-[''] before:absolute before:-top-1.5 before:left-1/2 before:-translate-x-1/2 before:border-4 before:border-transparent before:border-b-zinc-800 pointer-events-none">
            AIアート保管庫
          </div>
        </div>

        <!-- ナビアイテム 4: Gear -->
        <div class="relative group">
          <router-link to="/gear" class="text-sm font-bold text-zinc-300 hover:text-erika-light transition-colors py-2">
            Gear
          </router-link>
          <div class="absolute top-full left-1/2 -translate-x-1/2 mt-3 px-3 py-1.5 bg-zinc-800 border border-zinc-700 text-xs text-white rounded-md opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300 whitespace-nowrap shadow-xl before:content-[''] before:absolute before:-top-1.5 before:left-1/2 before:-translate-x-1/2 before:border-4 before:border-transparent before:border-b-zinc-800 pointer-events-none">
            使用機材・システム
          </div>
        </div>

        <!-- ナビアイテム 5: GAMES (ドロップダウンメニュー) -->
        <div class="relative group">
          <!-- 項目名 (クリック不可、ホバーでメニュー表示) -->
          <div class="text-sm font-bold text-erika hover:text-amber-300 transition-colors py-2 flex items-center gap-1 cursor-default">
            <span class="animate-pulse">▶</span> GAMES
            <!-- 下向き矢印アイコン（ホバーで回転） -->
            <svg class="w-4 h-4 transition-transform duration-300 group-hover:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
          </div>

          <!-- ドロップダウンの中身（透明な上部余白を入れてホバー切れを防ぐ） -->
          <div class="absolute top-full right-0 md:-left-4 pt-4 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-300">
            <div class="w-56 bg-zinc-800/95 backdrop-blur-md border border-zinc-700/80 rounded-xl shadow-2xl overflow-hidden flex flex-col py-2 relative before:content-[''] before:absolute before:-top-2 before:left-10 before:border-4 before:border-transparent before:border-b-zinc-700">
              
              <!-- ERIKA BEAT -->
              <router-link to="/beat" class="px-5 py-3 hover:bg-white/10 transition-colors flex flex-col group/item">
                <span class="text-sm font-bold text-amber-400 group-hover/item:text-amber-300">ERIKA BEAT</span>
                <span class="text-[10px] text-zinc-400 mt-0.5">YouTube同期リズムゲーム</span>
              </router-link>
              
              <!-- RPG Battle -->
              <router-link to="/rpg" class="px-5 py-3 hover:bg-white/10 transition-colors flex flex-col border-t border-zinc-700/50 group/item">
                <span class="text-sm font-bold text-zinc-200 group-hover/item:text-white">RPG Battle</span>
                <span class="text-[10px] text-zinc-400 mt-0.5">ブラウザRPG・エリカ討伐戦</span>
              </router-link>

              <!-- Memory Game -->
              <router-link to="/game" class="px-5 py-3 hover:bg-white/10 transition-colors flex flex-col border-t border-zinc-700/50 group/item">
                <span class="text-sm font-bold text-zinc-200 group-hover/item:text-white">Memory Game</span>
                <span class="text-[10px] text-zinc-400 mt-0.5">AIアート神経衰弱</span>
              </router-link>

            </div>
          </div>
        </div>
      </nav>

      <!-- スマホ用ハンバーガーボタン -->
      <button class="md:hidden text-white" @click="isMobileMenuOpen = !isMobileMenuOpen">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path v-if="!isMobileMenuOpen" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
          <path v-else stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
        </svg>
      </button>

    </div>

    <!-- スマホ用ドロップダウンメニュー -->
    <div v-if="isMobileMenuOpen" class="md:hidden bg-zinc-900 border-b border-white/10 shadow-xl pb-2">
      <nav class="flex flex-col px-4 py-4 space-y-4">
        <router-link to="/concept" class="text-zinc-300 hover:text-erika" @click="isMobileMenuOpen = false">
          <span class="font-bold">Concept</span> <span class="text-xs text-zinc-500 ml-2">プロジェクトの想い</span>
        </router-link>
        <router-link to="/blog" class="text-zinc-300 hover:text-erika" @click="isMobileMenuOpen = false">
          <span class="font-bold">Activities</span> <span class="text-xs text-zinc-500 ml-2">記事・観測日誌</span>
        </router-link>
        <router-link to="/gallery" class="text-zinc-300 hover:text-erika" @click="isMobileMenuOpen = false">
          <span class="font-bold">Gallery</span> <span class="text-xs text-zinc-500 ml-2">AIアート保管庫</span>
        </router-link>
        <router-link to="/gear" class="text-zinc-300 hover:text-erika" @click="isMobileMenuOpen = false">
          <span class="font-bold">Gear</span> <span class="text-xs text-zinc-500 ml-2">使用機材</span>
        </router-link>
        
        <!-- スマホ用 GAMES (アコーディオン) -->
        <div class="pt-2 border-t border-zinc-800">
          <button @click="isMobileGamesOpen = !isMobileGamesOpen" class="w-full flex items-center justify-between text-erika hover:text-amber-300 font-bold py-1 outline-none">
            <span class="flex items-center gap-2"><span class="animate-pulse">▶</span> GAMES</span>
            <!-- 矢印の回転 -->
            <svg class="w-5 h-5 transition-transform duration-300" :class="isMobileGamesOpen ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
          </button>
          
          <!-- 中身 -->
          <div v-show="isMobileGamesOpen" class="flex flex-col pl-5 mt-3 space-y-4 border-l-2 border-zinc-800 ml-2">
            <router-link to="/beat" class="text-amber-400 hover:text-amber-300" @click="isMobileMenuOpen = false">
              <span class="font-bold block">ERIKA BEAT</span> <span class="text-[10px] text-amber-500/70">リズムゲーム</span>
            </router-link>
            <router-link to="/rpg" class="text-zinc-300 hover:text-white" @click="isMobileMenuOpen = false">
              <span class="font-bold block">RPG Battle</span> <span class="text-[10px] text-zinc-500">エリカ討伐戦</span>
            </router-link>
            <router-link to="/game" class="text-zinc-300 hover:text-white" @click="isMobileMenuOpen = false">
              <span class="font-bold block">Memory Game</span> <span class="text-[10px] text-zinc-500">神経衰弱</span>
            </router-link>
          </div>
        </div>
      </nav>
    </div>
  </header>
</template>