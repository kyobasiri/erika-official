<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

// 画像の全画面ビューアー。スワイプ・←→キー・ボタンで前後へ、Esc で閉じる。
export interface LightboxImage {
  src: string
  alt: string
}

const props = defineProps<{
  images: LightboxImage[]
  /** 表示中の番号。null なら閉じている */
  index: number | null
}>()
const emit = defineEmits<{ (e: 'update:index', value: number | null): void }>()

const open = computed(() => props.index !== null && props.images.length > 0)
const current = computed(() => (props.index !== null ? props.images[props.index] : undefined))
const dialog = ref<HTMLElement | null>(null)
let returnFocus: HTMLElement | null = null

function close() {
  emit('update:index', null)
}
function go(delta: number) {
  if (props.index === null || !props.images.length) return
  emit('update:index', (props.index + delta + props.images.length) % props.images.length)
}

function onKeydown(e: KeyboardEvent) {
  if (!open.value) return
  if (e.key === 'Escape') close()
  else if (e.key === 'ArrowRight') go(1)
  else if (e.key === 'ArrowLeft') go(-1)
  else return
  e.preventDefault()
}

// スワイプ（横に50px以上動かしたら前後へ）
let startX = 0
let startY = 0
let tracking = false
function onPointerDown(e: PointerEvent) {
  if (e.pointerType === 'mouse') return
  tracking = true
  startX = e.clientX
  startY = e.clientY
}
function onPointerUp(e: PointerEvent) {
  if (!tracking) return
  tracking = false
  const dx = e.clientX - startX
  const dy = e.clientY - startY
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) go(dx < 0 ? 1 : -1)
  else if (dy > 90 && Math.abs(dy) > Math.abs(dx)) close() // 下にスワイプで閉じる
}

// 前後の画像を先読みして、送ったときにすぐ出るようにする
function preload(i: number) {
  const img = props.images[(i + props.images.length) % props.images.length]
  if (img) new Image().src = img.src
}

let previousOverflow = ''
watch(open, async (isOpen) => {
  if (isOpen) {
    returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    window.addEventListener('keydown', onKeydown)
    await nextTick()
    dialog.value?.focus()
  } else {
    document.body.style.overflow = previousOverflow
    window.removeEventListener('keydown', onKeydown)
    returnFocus?.focus()
  }
})
watch(() => props.index, (i) => {
  if (i === null) return
  preload(i + 1)
  preload(i - 1)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  if (open.value) document.body.style.overflow = previousOverflow
})
</script>

<template>
  <Teleport to="body">
    <Transition name="lb">
      <div
        v-if="open && current"
        ref="dialog"
        class="lightbox"
        role="dialog"
        aria-modal="true"
        :aria-label="`画像 ${(index ?? 0) + 1} / ${images.length}`"
        tabindex="-1"
        @click.self="close"
        @pointerdown="onPointerDown"
        @pointerup="onPointerUp"
        @pointercancel="tracking = false"
      >
        <header class="lb-bar">
          <span class="lb-count">{{ (index ?? 0) + 1 }} / {{ images.length }}</span>
          <button class="lb-icon" aria-label="閉じる" @click="close">✕</button>
        </header>

        <figure class="lb-stage" @click.self="close">
          <img :key="current.src" :src="current.src" :alt="current.alt" class="lb-img" draggable="false">
          <figcaption v-if="current.alt" class="lb-caption">{{ current.alt }}</figcaption>
        </figure>

        <button v-if="images.length > 1" class="lb-nav prev" aria-label="前の画像" @click="go(-1)">‹</button>
        <button v-if="images.length > 1" class="lb-nav next" aria-label="次の画像" @click="go(1)">›</button>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(6, 6, 8, 0.96);
  display: flex;
  flex-direction: column;
  outline: none;
  touch-action: pan-y;
  user-select: none;
}
.lb-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  color: #d4d4d8;
  flex-shrink: 0;
}
.lb-count {
  font-size: 13px;
  letter-spacing: 0.12em;
  font-variant-numeric: tabular-nums;
}
.lb-icon {
  width: 44px;
  height: 44px;
  border-radius: 999px;
  font-size: 18px;
  color: #f4f4f5;
  background: rgba(255, 255, 255, 0.08);
}
.lb-stage {
  flex: 1;
  min-height: 0;
  margin: 0;
  padding: 0 16px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.lb-img {
  max-width: 100%;
  max-height: calc(100% - 3.5em);
  object-fit: contain;
  border-radius: 6px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
  animation: lb-in 0.25s ease-out;
}
.lb-caption {
  max-width: 46em;
  text-align: center;
  font-size: 13px;
  line-height: 1.7;
  color: #a1a1aa;
}
.lb-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 52px;
  height: 52px;
  border-radius: 999px;
  font-size: 32px;
  line-height: 1;
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(6px);
}
.lb-nav:hover { background: rgba(243, 156, 18, 0.35); }
.lb-nav.prev { left: 16px; }
.lb-nav.next { right: 16px; }
@media (max-width: 640px) {
  .lb-nav { display: none; } /* スマホはスワイプで操作 */
}
@keyframes lb-in {
  from { opacity: 0; transform: scale(0.98); }
  to { opacity: 1; transform: none; }
}
.lb-enter-active, .lb-leave-active { transition: opacity 0.2s ease; }
.lb-enter-from, .lb-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .lb-img { animation: none; }
}
</style>