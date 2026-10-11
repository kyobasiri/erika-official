<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import '@fontsource/dotgothic16/400.css'
import { sourceLine, type WordEntry } from '../types'

// テンプレート3：ゲームのテキスト窓。画面下のウィンドウに1文字ずつ表示する。
const props = defineProps<{ entry: WordEntry; animate?: boolean }>()

const o = computed(() => props.entry.options ?? {})
const focus = computed(() => `${o.value.focus?.x ?? 50}% ${o.value.focus?.y ?? 30}%`)
const chars = computed(() => [...props.entry.quote])

const shown = ref(chars.value.length)
let timer: ReturnType<typeof setInterval> | null = null

const reducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function stop() {
  if (timer) clearInterval(timer)
  timer = null
}

function start() {
  stop()
  if (!props.animate || reducedMotion()) {
    shown.value = chars.value.length
    return
  }
  shown.value = 0
  timer = setInterval(() => {
    shown.value++
    if (shown.value >= chars.value.length) stop()
  }, 70)
}

// クリック・タップで残りを一気に表示
function skip() {
  stop()
  shown.value = chars.value.length
}

watch(() => [props.entry.id, props.animate], start, { immediate: true })
onBeforeUnmount(stop)

const visibleText = computed(() => chars.value.slice(0, shown.value).join(''))
const done = computed(() => shown.value >= chars.value.length)
</script>

<template>
  <div class="tpl-game" :style="{ '--accent': o.accent ?? '#7dd3fc' }" @click="skip">
    <img class="art" :src="entry.image" :alt="entry.imageAlt" :style="{ objectPosition: focus }" loading="lazy" decoding="async">
    <div class="scan" aria-hidden="true"></div>
    <p class="hud">QUOTE · {{ entry.source.title }}</p>
    <div class="window">
      <span class="name">{{ o.speakerName ?? 'エリカ' }}</span>
      <!-- 読み上げ用には全文を渡し、見た目だけ1文字ずつ出す -->
      <p class="sr-only">{{ entry.quote }}</p>
      <p class="text" aria-hidden="true">{{ visibleText }}<span v-if="!done" class="caret">_</span></p>
      <p class="from">── {{ sourceLine(entry) }}</p>
      <span v-if="done" class="next" aria-hidden="true">▼</span>
    </div>
  </div>
</template>

<style scoped>
.tpl-game {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: #05060f;
  font-family: 'DotGothic16', monospace;
  cursor: pointer;
}
.art {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
/* うっすら走査線 */
.scan {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(transparent 0 0.5cqw, rgba(0, 0, 0, 0.12) 0.5cqw 0.75cqw);
  pointer-events: none;
}
.hud {
  position: absolute;
  top: 3.5%;
  right: 4%;
  margin: 0;
  padding: 1cqw 2.2cqw;
  font-size: 2.8cqw;
  letter-spacing: 0.14em;
  color: #fff;
  background: rgba(5, 8, 30, 0.72);
  border: 0.4cqw solid rgba(255, 255, 255, 0.85);
}
.window {
  position: absolute;
  left: 4%;
  right: 4%;
  bottom: 4%;
  min-height: 34%;
  padding: 6.5cqw 5cqw 4cqw;
  color: #fff;
  background: linear-gradient(rgba(16, 24, 72, 0.92), rgba(6, 10, 34, 0.94));
  border: 0.7cqw solid #fff;
  border-radius: 1.6cqw;
  box-shadow:
    inset 0 0 0 0.7cqw #1d2c78,
    0 1cqw 3cqw rgba(0, 0, 0, 0.6);
}
.name {
  position: absolute;
  top: -4.4cqw;
  left: 5%;
  padding: 1cqw 3.4cqw;
  font-size: 3.6cqw;
  letter-spacing: 0.2em;
  color: #0a0f2e;
  background: var(--accent);
  border: 0.6cqw solid #fff;
  border-radius: 1cqw;
}
.text {
  margin: 0;
  min-height: 3lh;
  font-size: calc(4.6cqw * var(--word-scale, 1));
  line-height: 1.75;
  letter-spacing: 0.06em;
  white-space: pre-line;
  text-shadow: 0.3cqw 0.3cqw 0 #000;
}
.caret {
  animation: blink 0.6s steps(1) infinite;
}
.from {
  margin: 2.4cqw 0 0;
  font-size: 3cqw;
  color: var(--accent);
  letter-spacing: 0.08em;
}
.next {
  position: absolute;
  right: 5%;
  bottom: 4cqw;
  font-size: 3.4cqw;
  color: var(--accent);
  animation: bob 0.9s ease-in-out infinite;
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}
@keyframes blink {
  50% { opacity: 0; }
}
@keyframes bob {
  50% { transform: translateY(0.8cqw); }
}
@media (prefers-reduced-motion: reduce) {
  .caret, .next { animation: none; }
}
</style>
