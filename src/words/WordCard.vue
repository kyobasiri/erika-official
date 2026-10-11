<script setup lang="ts">
import { computed, type Component } from 'vue'
import WordBubble from './templates/WordBubble.vue'
import WordManga from './templates/WordManga.vue'
import WordGame from './templates/WordGame.vue'
import WordLyric from './templates/WordLyric.vue'
import WordLetter from './templates/WordLetter.vue'
import type { WordEntry, WordTemplate } from './types'

// 言葉1件を、指定のテンプレートで描く。
// 大きさは親の幅に合わせて伸び縮みする（中身は cqw 単位なので、カードでも全画面でも同じ見た目）。
const props = defineProps<{
  entry: WordEntry
  /** 指定するとエントリーのテンプレートを上書きする（見比べ用） */
  template?: WordTemplate
  animate?: boolean
}>()

const TEMPLATES: Record<WordTemplate, Component> = {
  bubble: WordBubble,
  manga: WordManga,
  game: WordGame,
  lyric: WordLyric,
  letter: WordLetter
}

const component = computed(() => TEMPLATES[props.template ?? props.entry.template] ?? WordBubble)
const scale = computed(() => {
  const n = Number(props.entry.options?.fontScale)
  return Number.isFinite(n) && n > 0 ? Math.min(2, Math.max(0.5, n)) : 1
})
</script>

<template>
  <div class="word-card" :style="{ '--word-scale': scale }">
    <component :is="component" :entry="entry" :animate="animate" />
  </div>
</template>

<style scoped>
.word-card {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 5;
  container-type: inline-size;
  overflow: hidden;
  border-radius: 12px;
  isolation: isolate;
}
</style>
