<script setup lang="ts">
// TypeScriptで受け取るプロパティ（引数）の型を定義
defineProps<{
  to: string
  title: string
  desc: string
}>()
</script>

<template>
  <router-link :to="to" class="block h-full p-8 rounded-2xl bg-black/40 backdrop-blur-md border border-white/10 transition-all duration-300 hover:-translate-y-1 hover:border-erika/50 hover:shadow-[0_0_30px] hover:shadow-erika/15 relative overflow-hidden group">
    <div class="absolute left-0 top-0 w-1 h-full bg-erika opacity-0 transition-opacity duration-300 group-hover:opacity-100"></div>
    <p class="text-2xl md:text-3xl font-black text-erika mb-3 group-hover:text-erika-light transition-colors">{{ title }}</p>
    <p class="text-zinc-400 text-sm md:text-base">{{ desc }}</p>
  </router-link>
</template>
