<script setup lang="ts">
import { computed } from 'vue'
import '@fontsource/shippori-mincho/500.css'
import '@fontsource/shippori-mincho/700.css'
import { type WordEntry } from '../types'
import { artImageStyle } from '../artImage'

// テンプレート5：便箋。和紙に縦書きの明朝体、ポラロイド写真とはんこ。
const props = defineProps<{ entry: WordEntry; animate?: boolean }>()

const o = computed(() => props.entry.options ?? {})
// 画像の位置と拡大率（管理ページのスライダーで決める）
const imageStyle = computed(() => artImageStyle(o.value, 50))
</script>

<template>
  <div class="tpl-letter" :class="{ animate }" :style="{ '--accent': o.accent ?? '#9f1239' }">
    <div class="paper">
      <p class="quote">{{ entry.quote }}</p>
      <p class="from">
        <span class="title">『{{ entry.source.title }}』</span>
        <span v-if="entry.source.author">{{ entry.source.author }}</span>
        <span v-if="entry.speaker" class="speaker">{{ entry.speaker }}の言葉</span>
      </p>
    </div>

    <figure class="polaroid">
      <span class="tape" aria-hidden="true"></span>
      <span class="photo">
        <img :src="entry.image" :alt="entry.imageAlt" :style="imageStyle" loading="lazy" decoding="async">
      </span>
      <figcaption>エリカより</figcaption>
    </figure>

    <span class="seal" aria-hidden="true">エリカ</span>
  </div>
</template>

<style scoped>
.tpl-letter {
  --col: 9.2cqw;
  position: absolute;
  inset: 0;
  overflow: hidden;
  /* 和紙：繊維のすじと色むら */
  background:
    radial-gradient(ellipse at 15% 85%, rgba(160, 120, 70, 0.14), transparent 55%),
    radial-gradient(ellipse at 85% 10%, rgba(255, 255, 255, 0.6), transparent 50%),
    repeating-linear-gradient(13deg, rgba(110, 85, 50, 0.025) 0 0.15cqw, transparent 0.15cqw 1.7cqw, rgba(110, 85, 50, 0.02) 1.7cqw 1.8cqw, transparent 1.8cqw 4.3cqw),
    repeating-linear-gradient(-58deg, rgba(110, 85, 50, 0.02) 0 0.12cqw, transparent 0.12cqw 2.9cqw, rgba(110, 85, 50, 0.015) 2.9cqw 3cqw, transparent 3cqw 6.1cqw),
    #f7f2e7;
  font-family: 'Shippori Mincho', serif;
  color: #26201a;
}
.paper {
  position: absolute;
  top: 7%;
  right: 7%;
  bottom: 7%;
  left: 7%;
  border: 0.35cqw solid color-mix(in srgb, var(--accent) 45%, transparent);
  /* 縦の罫線（右から1列ずつ） */
  background: repeating-linear-gradient(to left, transparent 0 calc(var(--col) - 0.25cqw), color-mix(in srgb, var(--accent) 28%, transparent) calc(var(--col) - 0.25cqw) var(--col));
  padding: 6cqw 0;
  writing-mode: vertical-rl;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}
.quote {
  margin: 0;
  font-weight: 500;
  font-size: calc(5.6cqw * var(--word-scale, 1));
  /* 1行の幅＝罫線の間隔にそろえる */
  line-height: var(--col);
  letter-spacing: 0.22em;
  white-space: pre-line;
  padding-block-start: 1em;
}
.from {
  margin: 0;
  margin-inline-start: var(--col);
  padding-block-start: 30%;
  display: flex;
  flex-direction: column;
  font-weight: 700;
  font-size: 3.2cqw;
  line-height: calc(var(--col) * 0.62);
  letter-spacing: 0.24em;
  color: #4a3b2c;
}
.from .speaker {
  font-weight: 500;
  color: #7a6450;
}
.polaroid {
  position: absolute;
  left: 9%;
  bottom: 9%;
  width: 40%;
  margin: 0;
  padding: 2.2cqw 2.2cqw 6.5cqw;
  background: #fffdf8;
  box-shadow: 0 1.2cqw 2.8cqw rgba(60, 40, 20, 0.28), 0 0 0 0.2cqw rgba(0, 0, 0, 0.04);
  transform: rotate(-5deg);
  z-index: 2;
}
.photo {
  display: block;
  overflow: hidden;
}
.polaroid img {
  display: block;
  width: 100%;
  aspect-ratio: 1;
  object-fit: cover;
}
.polaroid figcaption {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 1.6cqw;
  text-align: center;
  font-size: 3cqw;
  letter-spacing: 0.3em;
  color: #5b4a3a;
}
.tape {
  position: absolute;
  top: -2.4cqw;
  left: 50%;
  width: 34%;
  height: 5cqw;
  transform: translateX(-50%) rotate(3deg);
  background: rgba(230, 215, 170, 0.75);
  box-shadow: 0 0.2cqw 0.6cqw rgba(0, 0, 0, 0.08);
}
.seal {
  position: absolute;
  left: 52%;
  bottom: 10%;
  padding: 1.2cqw 0.9cqw;
  writing-mode: vertical-rl;
  border: 0.5cqw solid var(--accent);
  border-radius: 1.2cqw;
  color: var(--accent);
  font-weight: 700;
  font-size: 3.2cqw;
  line-height: 1;
  letter-spacing: 0.1em;
  transform: rotate(6deg);
  opacity: 0.85;
}
.animate .quote {
  animation: ink 1.6s ease-out both;
}
.animate .polaroid {
  animation: drop 0.8s 0.5s cubic-bezier(0.2, 1.2, 0.4, 1) both;
}
.animate .seal {
  animation: stamp 0.35s 1.4s cubic-bezier(0.3, 1.8, 0.5, 1) both;
}
@keyframes ink {
  0% { opacity: 0; filter: blur(0.6cqw); }
  100% { opacity: 1; filter: none; }
}
@keyframes drop {
  0% { opacity: 0; transform: translateY(-8cqw) rotate(-14deg); }
  100% { opacity: 1; transform: rotate(-5deg); }
}
@keyframes stamp {
  0% { opacity: 0; transform: scale(1.8) rotate(6deg); }
  100% { opacity: 0.85; transform: scale(1) rotate(6deg); }
}
@media (prefers-reduced-motion: reduce) {
  .animate .quote, .animate .polaroid, .animate .seal { animation: none; }
}
</style>
