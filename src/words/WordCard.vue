<script setup lang="ts">
import { computed, defineAsyncComponent, type Component } from 'vue'
import type { WordEntry, WordTemplate } from './types'

// 言葉1件を、指定のテンプレートで描く。
// 大きさは親の幅に合わせて伸び縮みする（中身は cqw 単位なので、カードでも全画面でも同じ見た目）。
const props = defineProps<{
  entry: WordEntry
  /** 指定するとエントリーのテンプレートを上書きする（見比べ用） */
  template?: WordTemplate
  animate?: boolean
}>()

// テンプレートは、実際に使うものだけをあとから読み込む（defineAsyncComponent）。
// 各テンプレートは専用の日本語フォント（CSS だけで数百KB）を読み込むので、
// まとめて読み込むと、トップページなどの最初の表示がとても重くなるため。
// 一度読み込んだテンプレートは、次からはすぐに表示される。
const TEMPLATES: Record<WordTemplate, Component> = {
  bubble: defineAsyncComponent(() => import('./templates/WordBubble.vue')),
  manga: defineAsyncComponent(() => import('./templates/WordManga.vue')),
  game: defineAsyncComponent(() => import('./templates/WordGame.vue')),
  lyric: defineAsyncComponent(() => import('./templates/WordLyric.vue')),
  letter: defineAsyncComponent(() => import('./templates/WordLetter.vue')),
  bunko: defineAsyncComponent(() => import('./templates/WordBunko.vue'))
}

const component = computed(() => TEMPLATES[props.template ?? props.entry.template] ?? TEMPLATES.bubble)
const scale = computed(() => {
  const n = Number(props.entry.options?.fontScale)
  return Number.isFinite(n) && n > 0 ? Math.min(2, Math.max(0.3, n)) : 1
})
</script>

<template>
  <!-- 枠の大きさ（4:5）は先に決まっているので、テンプレートの読み込み中も画面がずれない -->
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
  /* テンプレートを読み込むまでの、ほんの一瞬だけ見える下地 */
  background: rgb(255 255 255 / 0.04);
}
</style>