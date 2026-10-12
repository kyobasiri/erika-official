<script setup lang="ts">
import { computed } from 'vue'
import '@fontsource/zen-kurenaido/400.css'
import '@fontsource/shippori-mincho/600.css'
import { type WordEntry } from '../types'
import { artImageStyle } from '../artImage'
import { fitFontSize } from '../fitText'

// テンプレート4：歌詞カード。紙のカードにジャケット写真とレコード、手書き風の歌詞を1行ずつ。
const props = defineProps<{ entry: WordEntry; animate?: boolean }>()

const o = computed(() => props.entry.options ?? {})
// 画像の位置と拡大率（管理ページのスライダーで決める）
const imageStyle = computed(() => artImageStyle(o.value, 50))
const lines = computed(() => props.entry.quote.split('\n'))
const title = computed(() => o.value.songTitle ?? props.entry.source.title)
// 歌詞の行数・長さに合わせて文字の大きさを決める（標準は 5cqw。長い行が多いと小さくなる）
const fontSize = computed(() => fitFontSize(props.entry.quote, {
  inline: 84, block: 34, lineHeight: 1.75, tracking: 0.08, max: 5, min: 2.6
}))
</script>

<template>
  <div class="tpl-lyric" :class="{ animate }" :style="{ '--accent': o.accent ?? '#c2410c', '--fit': `${fontSize}cqw` }">
    <div class="sleeve">
      <div class="record" aria-hidden="true"><span class="label"></span></div>
      <div class="jacket">
        <img :src="entry.image" :alt="entry.imageAlt" :style="imageStyle" loading="lazy" decoding="async">
      </div>
      <p class="memo" aria-hidden="true">♪ エリカのお気に入り</p>
    </div>

    <div class="sheet">
      <p class="track"><span>SIDE A</span>{{ title }}</p>
      <p class="sr-only">{{ entry.quote }}</p>
      <div class="lyrics" aria-hidden="true">
        <p v-for="(line, i) in lines" :key="i" :style="{ animationDelay: `${0.35 + i * 0.55}s` }">{{ line }}</p>
      </div>
      <p class="credit">
        <span>{{ entry.source.author }}</span>
        <span v-if="entry.source.detail">{{ entry.source.detail }}</span>
      </p>
    </div>
  </div>
</template>

<style scoped>
.tpl-lyric {
  position: absolute;
  inset: 0;
  overflow: hidden;
  color: #2b2118;
  /* 生成りの紙。細かい繊維とわずかな色むら */
  background:
    radial-gradient(ellipse at 20% 10%, rgba(255, 255, 255, 0.55), transparent 55%),
    radial-gradient(ellipse at 90% 95%, rgba(150, 110, 60, 0.18), transparent 60%),
    repeating-linear-gradient(83deg, rgba(120, 90, 50, 0.035) 0 0.3cqw, transparent 0.3cqw 1.4cqw),
    #f1e8d8;
  display: grid;
  grid-template-rows: 54% 1fr;
}
.sleeve {
  position: relative;
}
.jacket {
  position: absolute;
  left: 7%;
  top: 7%;
  width: 56%;
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 0.6cqw;
  box-shadow: 0 1.4cqw 3cqw rgba(60, 35, 10, 0.35), 0 0 0 0.3cqw rgba(0, 0, 0, 0.08);
  z-index: 2;
}
.jacket img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
/* ジャケットから半分のぞくレコード */
.record {
  position: absolute;
  left: 34%;
  top: 9%;
  width: 52%;
  aspect-ratio: 1;
  border-radius: 50%;
  background:
    radial-gradient(circle, transparent 0 15%, rgba(255, 255, 255, 0.06) 15.5% 16%, transparent 16.5%),
    repeating-radial-gradient(circle, #111 0 0.45cqw, #1c1c1c 0.45cqw 0.7cqw),
    #111;
  box-shadow: 0 1cqw 2.4cqw rgba(0, 0, 0, 0.35);
  z-index: 1;
}
.record::after {
  /* 光の反射 */
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: conic-gradient(from 30deg, transparent 0 20%, rgba(255, 255, 255, 0.12) 25%, transparent 32% 70%, rgba(255, 255, 255, 0.08) 75%, transparent 82%);
}
.label {
  position: absolute;
  inset: 33%;
  border-radius: 50%;
  background: radial-gradient(circle, #f1e8d8 0 9%, var(--accent) 10%);
}
.animate .record {
  animation: slide-out 0.9s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
.sheet {
  position: relative;
  padding: 0 8% 6%;
}
.track {
  margin: 0 0 2.4cqw;
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 1cqw 2.4cqw;
  font-family: 'Shippori Mincho', serif;
  font-weight: 600;
  font-size: 5.4cqw;
  letter-spacing: 0.16em;
}
.track span {
  font-family: 'Zen Kurenaido', sans-serif;
  font-size: 2.6cqw;
  letter-spacing: 0.2em;
  color: var(--accent);
  border: 0.3cqw solid var(--accent);
  padding: 0.2cqw 1.4cqw;
  border-radius: 2cqw;
}
.lyrics p {
  margin: 0;
  font-family: 'Zen Kurenaido', sans-serif;
  font-size: calc(var(--fit, 5cqw) * var(--word-scale, 1));
  line-height: 1.75;
  letter-spacing: 0.08em;
}
.animate .lyrics p {
  animation: line-in 0.8s ease-out both;
}
.credit {
  margin: 2.6cqw 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0 3cqw;
  font-family: 'Shippori Mincho', serif;
  font-weight: 600;
  font-size: 2.8cqw;
  letter-spacing: 0.12em;
  color: #6b5641;
}
/* 曲名と重ならないよう、ジャケットの右下・レコードの下の余白に置く */
.memo {
  position: absolute;
  right: 4%;
  bottom: 0.6cqw;
  z-index: 3;
  white-space: nowrap;
  margin: 0;
  font-family: 'Zen Kurenaido', sans-serif;
  font-size: 3.2cqw;
  color: var(--accent);
  transform: rotate(-4deg);
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
@keyframes line-in {
  0% { opacity: 0; transform: translateY(1.2cqw); filter: blur(0.4cqw); }
  100% { opacity: 1; transform: none; filter: none; }
}
@keyframes slide-out {
  0% { transform: translateX(-30%) rotate(-40deg); }
  100% { transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .animate .lyrics p, .animate .record { animation: none; }
}
</style>
