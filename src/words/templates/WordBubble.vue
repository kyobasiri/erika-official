<script setup lang="ts">
import { computed } from 'vue'
import '@fontsource/zen-maru-gothic/700.css'
import BubbleBox from '../BubbleBox.vue'
import { sourceLine, type WordEntry } from '../types'

// テンプレート1：吹き出し（基本）。画像の上に吹き出しを自由に置く。
const props = defineProps<{ entry: WordEntry; animate?: boolean }>()

const o = computed(() => props.entry.options ?? {})
const bubble = computed(() => o.value.bubble ?? { x: 6, y: 6, width: 42, shape: 'round' as const, tail: 'bottom-right' as const })
const focus = computed(() => `${o.value.focus?.x ?? 50}% ${o.value.focus?.y ?? 50}%`)
</script>

<template>
  <div class="tpl-bubble" :class="{ animate }" :style="{ '--accent': o.accent ?? '#f4b63f' }">
    <img class="art" :src="entry.image" :alt="entry.imageAlt" :style="{ objectPosition: focus }" loading="lazy" decoding="async">
    <div class="shade" aria-hidden="true"></div>
    <BubbleBox :bubble="bubble" :vertical="o.vertical" class="pop">
      <p class="quote">{{ entry.quote }}</p>
    </BubbleBox>
    <p class="source"><span class="mark" aria-hidden="true"></span>{{ sourceLine(entry) }}</p>
  </div>
</template>

<style scoped>
.tpl-bubble {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: #111;
  font-family: 'Zen Maru Gothic', sans-serif;
}
.art {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.shade {
  position: absolute;
  inset: auto 0 0 0;
  height: 22%;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.55));
}
.quote {
  margin: 0;
  font-weight: 700;
  font-size: calc(5.6cqw * var(--word-scale, 1));
  line-height: 1.55;
  letter-spacing: 0.04em;
  white-space: pre;
}
.source {
  position: absolute;
  left: 5%;
  bottom: 4%;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 1.6cqw;
  font-size: 3.2cqw;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.06em;
  text-shadow: 0 0.3cqw 1cqw rgba(0, 0, 0, 0.6);
}
.mark {
  width: 4.5cqw;
  height: 0.6cqw;
  background: var(--accent);
  border-radius: 1cqw;
}
.animate .pop {
  animation: bubble-pop 0.55s cubic-bezier(0.2, 1.4, 0.4, 1) both;
  transform-origin: 70% 100%;
}
@keyframes bubble-pop {
  0% { transform: scale(0.6); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .animate .pop { animation: none; }
}
</style>
