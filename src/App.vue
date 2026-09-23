<template>
  <div class="min-h-screen bg-zinc-950 text-zinc-300">
    <Header />
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import Header from './components/Header.vue';
</script>

<style>
/* 全体共通のスタイル（リセットCSSや背景色など）があればここに書きます */
body {
  margin: 0;
  font-family: sans-serif;
  background-color: #f8f9fa;
}
</style>
