<script setup lang="ts">
import { computed } from 'vue'
import '@fontsource/shippori-mincho/500.css'
import '@fontsource/shippori-mincho/700.css'
import { type WordEntry } from '../types'
import { artImageStyle } from '../artImage'
import { fitFontSize, stableNumber } from '../fitText'

// テンプレート6：文庫本のページ。長めの言葉（〜250字ほど）向け。
// 文字数に合わせて文字の大きさを自動で決める。縦書き（標準）と横書きを選べる。
const props = defineProps<{ entry: WordEntry; animate?: boolean }>()

const o = computed(() => props.entry.options ?? {})
// 画像の位置と拡大率（管理ページのスライダーで決める）
const imageStyle = computed(() => artImageStyle(o.value, 50))
const vertical = computed(() => o.value.vertical ?? true)

// 本文の枠（cqw）。下の CSS の .body の大きさと合わせること
const BOX = {
  vertical: { width: 84, height: 66 },
  horizontal: { width: 84, height: 63 }
}

const fontSize = computed(() => {
  const box = vertical.value ? BOX.vertical : BOX.horizontal
  return fitFontSize(props.entry.quote, {
    inline: vertical.value ? box.height : box.width,
    block: vertical.value ? box.width : box.height,
    lineHeight: 1.85,
    tracking: 0.06,
    max: 6.4,
    min: 3,
    reserveLines: props.entry.speaker ? 1.2 : 0
  })
})

const folio = computed(() => stableNumber(props.entry.id, 12, 286))
</script>

<template>
  <div
    class="tpl-bunko"
    :class="{ animate, vertical, horizontal: !vertical }"
    :style="{ '--accent': o.accent ?? '#7c2d12', '--fit': `${fontSize}cqw` }"
  >
    <header class="running-head">
      <span class="head-title">{{ entry.source.title }}</span>
      <span v-if="entry.source.author" class="head-author">{{ entry.source.author }}</span>
    </header>

    <div class="body">
      <p class="quote">{{ entry.quote }}</p>
      <p v-if="entry.speaker" class="by">――{{ entry.speaker }}</p>
    </div>

    <figure class="plate">
      <span class="photo">
        <img :src="entry.image" :alt="entry.imageAlt" :style="imageStyle" loading="lazy" decoding="async">
      </span>
    </figure>

    <footer class="folio">
      <span>{{ folio }}</span>
    </footer>

    <span class="ribbon" aria-hidden="true"></span>
  </div>
</template>

<style scoped>
.tpl-bunko {
  position: absolute;
  inset: 0;
  overflow: hidden;
  color: #2a241d;
  font-family: 'Shippori Mincho', serif;
  /* 文庫の本文用紙：少し黄みのある紙と、綴じ側（右）の影 */
  background:
    linear-gradient(to left, rgba(90, 65, 35, 0.22), rgba(90, 65, 35, 0.06) 3.5%, transparent 9%),
    radial-gradient(ellipse at 30% 20%, rgba(255, 255, 255, 0.5), transparent 60%),
    radial-gradient(ellipse at 80% 100%, rgba(160, 120, 70, 0.14), transparent 55%),
    repeating-linear-gradient(0deg, rgba(120, 95, 60, 0.018) 0 0.12cqw, transparent 0.12cqw 0.9cqw),
    #f4eedf;
}

/* --- 柱（ページ上の作品名） --- */
.running-head {
  position: absolute;
  top: 4.4cqw;
  left: 8cqw;
  right: 8cqw;
  display: flex;
  justify-content: space-between;
  gap: 3cqw;
  padding-bottom: 1.2cqw;
  border-bottom: 0.2cqw solid rgba(60, 45, 30, 0.35);
  font-size: 2.5cqw;
  font-weight: 500;
  letter-spacing: 0.18em;
  color: #6b5a46;
  white-space: nowrap;
}
.head-title {
  overflow: hidden;
  text-overflow: ellipsis;
}
.head-title::before { content: '『'; }
.head-title::after { content: '』'; }
.head-author {
  flex-shrink: 0;
}

/* --- 本文 --- */
.body {
  position: absolute;
  left: 8cqw;
  width: 84cqw;
  overflow: hidden;
}
.quote {
  margin: 0;
  font-weight: 500;
  font-size: calc(var(--fit) * var(--word-scale, 1));
  line-height: 1.85;
  letter-spacing: 0.06em;
  white-space: pre-line;
  text-align: justify;
  line-break: strict;
  hanging-punctuation: allow-end;
  font-feature-settings: 'palt' 0;
}
.by {
  margin: 0;
  font-weight: 700;
  font-size: calc(var(--fit) * 0.72 * var(--word-scale, 1));
  line-height: 1.85;
  letter-spacing: 0.12em;
  text-align: end;
  color: #5b4a39;
}

/* --- 挿絵 --- */
.plate {
  position: absolute;
  left: 8cqw;
  right: 8cqw;
  margin: 0;
  padding: 1cqw;
  background: #fbf8f0;
  border: 0.25cqw solid rgba(60, 45, 30, 0.45);
  box-shadow: 0 0 0 0.8cqw #f4eedf, 0 0 0 1cqw rgba(60, 45, 30, 0.25);
}
.photo {
  display: block;
  width: 100%;
  height: 100%;
  overflow: hidden;
}
.plate img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: saturate(0.9) contrast(1.02);
}

/* --- ノンブル（ページ番号） --- */
.folio {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 3.2cqw;
  text-align: center;
  font-size: 2.4cqw;
  letter-spacing: 0.2em;
  color: #6b5a46;
}

/* --- しおり紐（本文にかからないよう、右の余白に垂らす） --- */
.ribbon {
  position: absolute;
  top: -1cqw;
  right: 3.4cqw;
  width: 2.2cqw;
  height: 30cqw;
  background: linear-gradient(90deg, color-mix(in srgb, var(--accent) 80%, #000), var(--accent) 45%, color-mix(in srgb, var(--accent) 85%, #000));
  clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 92%, 0 100%);
  box-shadow: 0 0.4cqw 0.8cqw rgba(0, 0, 0, 0.2);
  opacity: 0.92;
}

/* 縦書き：本文が上、挿絵が下 */
.vertical .body {
  top: 10.5cqw;
  height: 66cqw;
  writing-mode: vertical-rl;
}
.vertical .plate {
  top: 80cqw;
  height: 34cqw;
}

/* 横書き：挿絵が上、本文が下 */
.horizontal .plate {
  top: 11.5cqw;
  height: 34cqw;
}
.horizontal .body {
  top: 52cqw;
  height: 63cqw;
}
.horizontal .ribbon {
  right: auto;
  left: 3.4cqw;
}

/* --- アニメーション：文字が紙に浮かび上がる --- */
.animate .quote {
  animation: reveal-v 1.8s cubic-bezier(0.3, 0.6, 0.3, 1) both;
}
.animate.horizontal .quote {
  animation-name: reveal-h;
}
.animate .by {
  animation: fade 0.8s 1.5s ease-out both;
}
.animate .plate {
  animation: fade 1s 0.2s ease-out both;
}
.animate .ribbon {
  animation: ribbon 0.9s 0.6s cubic-bezier(0.2, 1.3, 0.4, 1) both;
}
@keyframes reveal-v {
  0% { clip-path: inset(0 0 0 100%); opacity: 0.2; }
  100% { clip-path: inset(0 0 0 0); opacity: 1; }
}
@keyframes reveal-h {
  0% { clip-path: inset(0 0 100% 0); opacity: 0.2; }
  100% { clip-path: inset(0 0 0 0); opacity: 1; }
}
@keyframes fade {
  0% { opacity: 0; }
  100% { opacity: 1; }
}
@keyframes ribbon {
  0% { transform: translateY(-60%); }
  100% { transform: none; }
}
@media (prefers-reduced-motion: reduce) {
  .animate .quote, .animate .by, .animate .plate, .animate .ribbon { animation: none; }
}
</style>
