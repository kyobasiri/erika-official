<script setup lang="ts">
import { computed } from 'vue'
import { bubblePath } from './bubblePath'
import type { BubbleOptions } from './types'

// 画像の上に置く吹き出し。位置と大きさは画像に対する % で指定する。
const props = defineProps<{
  bubble: BubbleOptions
  vertical?: boolean
}>()

const d = computed(() => bubblePath(props.bubble.shape ?? 'round', props.bubble.tail ?? 'bottom-left'))

const style = computed(() => {
  const b = props.bubble
  return {
    left: `${b.x}%`,
    top: `${b.y}%`,
    // 改行は入力どおりに出し、吹き出しは文字に合わせて広がる。指定値は最小の大きさ。
    ...(props.vertical
      ? { minHeight: `${b.height ?? 30}%` }
      : { minWidth: `${b.width ?? 30}%` })
  }
})
</script>

<template>
  <div class="bubble-box" :class="[`shape-${bubble.shape ?? 'round'}`, { vertical }]" :style="style">
    <svg class="bubble-svg" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <path class="bubble-stroke" :d="d" />
      <path class="bubble-fill" :d="d" />
    </svg>
    <div class="bubble-text"><slot /></div>
  </div>
</template>

<style scoped>
.bubble-box {
  position: absolute;
  width: max-content;
  max-width: 92%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
}
.bubble-box.vertical {
  writing-mode: vertical-rl;
  max-width: none;
  max-height: 92%;
}
.bubble-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow: visible;
}
.bubble-stroke {
  fill: none;
  stroke: var(--bubble-line, #111);
  /* 内側の半分は白で塗りつぶされるので、見える線の太さはこの半分 */
  stroke-width: calc(var(--bubble-weight, 0.7cqw) * 2);
  stroke-linejoin: round;
  vector-effect: non-scaling-stroke;
}
.bubble-fill {
  fill: var(--bubble-paper, #fff);
  stroke: none;
}
.shape-whisper .bubble-stroke {
  stroke-dasharray: 1.4cqw 1.1cqw;
  stroke-linecap: round;
}
.shape-shout .bubble-stroke {
  stroke-linejoin: miter;
}
/* 余白はカード幅基準（cqw）。楕円の内側に文字が収まるよう、文字の塊の約2割を左右・上下に取る */
.bubble-text {
  position: relative;
  white-space: pre;
  padding: 6.5cqw 7.5cqw;
  text-align: center;
  color: var(--bubble-ink, #111);
}
.vertical .bubble-text {
  padding: 7.5cqw 6.5cqw;
  text-align: start;
}
.shape-thought .bubble-text {
  padding: 8cqw 9cqw;
}
.shape-shout .bubble-text {
  padding: 9cqw 10cqw;
}
.shape-shout.vertical .bubble-text {
  padding: 10cqw 9cqw;
}
</style>
