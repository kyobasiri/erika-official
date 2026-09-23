<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>

<template>
  <header class="fixed top-0 left-0 w-full z-50 bg-black/50 backdrop-blur-md border-b border-white/10 transition-all">
    <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
      <!-- ブランドロゴ（トップへ戻る） -->
      <router-link to="/" class="text-xl font-black text-white tracking-wider hover:text-erika transition-colors">
        ERIKA<span class="text-erika">.</span>
      </router-link>

      <!-- ナビゲーション / 戻る導線 -->
      <nav class="flex items-center gap-6 text-xs md:text-sm font-medium">
        <router-link to="/about" class="text-zinc-400 hover:text-white transition-colors" :class="{ 'text-erika': route.path === '/about' }">About</router-link>
        <router-link to="/gear" class="text-zinc-400 hover:text-white transition-colors" :class="{ 'text-erika': route.path === '/gear' }">Gear</router-link>
        <router-link to="/spec" class="text-zinc-400 hover:text-white transition-colors" :class="{ 'text-erika': route.path === '/spec' }">Spec</router-link>
        <router-link to="/contact" class="text-zinc-400 hover:text-white transition-colors" :class="{ 'text-erika': route.path === '/contact' }">Contact</router-link>

        <router-link v-if="route.path !== '/'" to="/" class="hidden sm:inline-flex items-center gap-1 px-4 py-1.5 rounded-full bg-white/10 hover:bg-white/20 text-white text-xs transition-colors">
          <span>← TOP</span>
        </router-link>
      </nav>
    </div>
  </header>
</template>
