<script setup lang="ts">
import { computed } from 'vue'
import '@fontsource/dela-gothic-one/400.css'
import '@fontsource/shippori-mincho/700.css'
import BubbleBox from '../BubbleBox.vue'
import { type WordEntry } from '../types'

// テンプレート2：漫画のコマ。白黒の大ゴマに集中線、縦書きの叫び吹き出し、下にナレーション枠。
const props = defineProps<{ entry: WordEntry; animate?: boolean }>()

const o = computed(() => props.entry.options ?? {})
const vertical = computed(() => o.value.vertical ?? true)
const bubble = computed(() => o.value.bubble ?? { x: 8, y: 8, height: 44, shape: 'shout' as const, tail: 'none' as const })
const focus = computed(() => `${o.value.focus?.x ?? 50}% ${o.value.focus?.y ?? 50}%`)
</script>

<template>
  <div class="tpl-manga" :class="{ animate }">
    <div class="mg-panel mg-main">
      <img class="art" :src="entry.image" :alt="entry.imageAlt" :style="{ objectPosition: focus }" loading="lazy" decoding="async">
      <div class="tone" aria-hidden="true"></div>
      <div class="speed" aria-hidden="true"></div>
      <BubbleBox :bubble="bubble" :vertical="vertical" class="slam">
        <p class="quote">{{ entry.quote }}</p>
      </BubbleBox>
      <span v-if="entry.speaker" class="speaker">{{ entry.speaker }}</span>
    </div>
    <div class="mg-panel mg-narration">
      <p class="caption">
        <span class="title">『{{ entry.source.title }}』</span>
        <span v-if="entry.source.author" class="author">{{ entry.source.author }}</span>
      </p>
    </div>
  </div>
</template>

<style scoped>
.tpl-manga {
  position: absolute;
  inset: 0;
  background: #fbfaf7;
  padding: 3.4cqw;
  display: grid;
  grid-template-rows: 1fr 17%;
  gap: 2.6cqw;
}
.mg-panel {
  position: relative;
  overflow: hidden;
  border: 0.9cqw solid #111;
  background: #fff;
}
.mg-main {
  /* コマの下辺を少し傾けて動きを出す */
  clip-path: polygon(0 0, 100% 0, 100% 100%, 0 94%);
}
.art {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  /* 暗い画像でも白黒の漫画らしく見えるよう、明るめに持ち上げる */
  filter: grayscale(1) brightness(1.55) contrast(1.25);
}
/* スクリーントーン */
.tone {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, rgba(0, 0, 0, 0.55) 28%, transparent 30%);
  background-size: 1.3cqw 1.3cqw;
  mix-blend-mode: multiply;
  opacity: 0.28;
}
/* 集中線（画面の外側だけに出す） */
.speed {
  position: absolute;
  inset: -20%;
  background: repeating-conic-gradient(from 0deg at 50% 50%, rgba(0, 0, 0, 0.85) 0deg 0.35deg, transparent 0.35deg 2.6deg);
  -webkit-mask-image: radial-gradient(ellipse at center, transparent 42%, rgba(0, 0, 0, 0.9) 72%);
  mask-image: radial-gradient(ellipse at center, transparent 42%, rgba(0, 0, 0, 0.9) 72%);
  opacity: 0.4;
}
.quote {
  margin: 0;
  font-family: 'Dela Gothic One', sans-serif;
  font-size: calc(6.6cqw * var(--word-scale, 1));
  line-height: 1.32;
  letter-spacing: 0.08em;
  white-space: pre;
}
.speaker {
  position: absolute;
  right: 4%;
  bottom: 9%;
  padding: 0.8cqw 2.2cqw;
  background: #111;
  color: #fff;
  font-family: 'Shippori Mincho', serif;
  font-weight: 700;
  font-size: 3cqw;
  letter-spacing: 0.2em;
}
.mg-narration {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4cqw;
}
.caption {
  margin: 0;
  font-family: 'Shippori Mincho', serif;
  font-weight: 700;
  color: #111;
  display: flex;
  flex-direction: column;
  gap: 0.6cqw;
}
.caption .title {
  font-size: 4.6cqw;
  letter-spacing: 0.1em;
}
.caption .author {
  font-size: 3cqw;
  letter-spacing: 0.3em;
  padding-left: 1.2em;
}
.animate .slam {
  animation: slam 0.45s cubic-bezier(0.3, 1.6, 0.5, 1) both;
}
.animate .speed {
  animation: speed-in 0.5s ease-out both;
}
@keyframes slam {
  0% { transform: scale(1.6) rotate(-6deg); opacity: 0; }
  100% { transform: scale(1) rotate(0); opacity: 1; }
}
@keyframes speed-in {
  0% { opacity: 0; transform: scale(1.3); }
  100% { opacity: 0.4; transform: scale(1); }
}
@media (prefers-reduced-motion: reduce) {
  .animate .slam, .animate .speed { animation: none; }
}
</style>
