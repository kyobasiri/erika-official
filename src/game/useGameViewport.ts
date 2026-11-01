/**
 * ERIKA ROCK ACTION: 画面サイズ・端末判定・全画面まわりの処理。
 *
 * - タッチ端末かどうか（画面幅ではなく「指で操作するか」で判定。iPad も対象）
 * - 横向きタッチ端末／全画面時は「大画面モード」（サイトのヘッダーを隠してゲームだけを表示）
 * - Canvas は論理解像度 800×450 のまま、表示サイズ × devicePixelRatio で高精細に描画
 */
import { computed, onMounted, onUnmounted, reactive, ref, watch, type Ref } from 'vue'

export const VIEW_W = 800
export const VIEW_H = 450
// 描画負荷の上限（横 1600px = 論理解像度の2倍まで）
const MAX_BACKING_WIDTH = 1600

interface ViewportRefs {
  shellRef: Ref<HTMLElement | null>
  stageRef: Ref<HTMLElement | null>
  canvasBoxRef: Ref<HTMLElement | null>
  canvasRef: Ref<HTMLCanvasElement | null>
}

export function useGameViewport({ shellRef, stageRef, canvasBoxRef, canvasRef }: ViewportRefs) {
  const coarseQuery = typeof window !== 'undefined' ? window.matchMedia('(pointer: coarse)') : null
  const isTouch = ref(!!coarseQuery?.matches)
  const viewport = reactive({ width: window.innerWidth, height: window.innerHeight })
  const isLandscape = computed(() => viewport.width > viewport.height)
  const isFullscreen = ref(false)
  const fullscreenSupported = !!(document.fullscreenEnabled && HTMLElement.prototype.requestFullscreen)

  // 横向きのタッチ端末、または全画面中は大画面モード
  const immersive = computed(() => isFullscreen.value || (isTouch.value && isLandscape.value))
  const fitSize = reactive({ width: VIEW_W, height: VIEW_H })
  const canvasDisplayHeight = ref(VIEW_H)
  // ゲーム画面が低い（スマホ）ときは、クリア画面などを画面全体に広げる
  const compactOverlay = computed(() => canvasDisplayHeight.value < 380)
  /** 1論理px あたりの実ピクセル数。描画開始時に ctx.setTransform に使う。 */
  const renderScale = ref(1)

  const updateFit = () => {
    const stage = stageRef.value
    if (immersive.value && stage) {
      const scale = Math.max(0.1, Math.min(stage.clientWidth / VIEW_W, stage.clientHeight / VIEW_H))
      fitSize.width = Math.floor(VIEW_W * scale)
      fitSize.height = Math.floor(VIEW_H * scale)
    }
    const box = canvasBoxRef.value
    const canvas = canvasRef.value
    if (!box || !canvas) return
    const cssWidth = box.clientWidth || VIEW_W
    canvasDisplayHeight.value = box.clientHeight || VIEW_H
    const dpr = Math.min(3, window.devicePixelRatio || 1)
    const backingWidth = Math.max(VIEW_W / 2, Math.min(MAX_BACKING_WIDTH, Math.round(cssWidth * dpr)))
    const scale = backingWidth / VIEW_W
    const w = Math.round(VIEW_W * scale)
    const h = Math.round(VIEW_H * scale)
    if (canvas.width !== w || canvas.height !== h) {
      canvas.width = w
      canvas.height = h
    }
    renderScale.value = scale
  }

  let resizeObserver: ResizeObserver | null = null
  const onResize = () => {
    viewport.width = window.innerWidth
    viewport.height = window.innerHeight
    requestAnimationFrame(updateFit)
  }
  const onCoarseChange = (e: MediaQueryListEvent) => { if (e.matches) isTouch.value = true }
  // タッチ対応PCなど：実際に指で触ったらタッチ操作UIを出す
  const onPointerDown = (e: PointerEvent) => { if (e.pointerType === 'touch') isTouch.value = true }
  const onFullscreenChange = () => {
    isFullscreen.value = !!document.fullscreenElement
    requestAnimationFrame(updateFit)
  }

  const toggleFullscreen = async () => {
    try {
      if (document.fullscreenElement) {
        await document.exitFullscreen()
        return
      }
      await (shellRef.value ?? document.documentElement).requestFullscreen({ navigationUI: 'hide' })
      // Android Chrome: 全画面中だけ横向きに固定できる（未対応ブラウザは無視）
      const orientation = screen.orientation as ScreenOrientation & { lock?: (o: string) => Promise<void> }
      if (isTouch.value && orientation?.lock) await orientation.lock('landscape').catch(() => {})
    } catch (error) {
      console.warn('[ERIKA] Fullscreen is not available.', error)
    }
  }

  // iPhone のノッチ／ホームバー領域を使えるようにする（このページの間だけ）
  const viewportMeta = document.querySelector<HTMLMetaElement>('meta[name="viewport"]')
  const originalViewport = viewportMeta?.content ?? ''

  watch(immersive, (on) => {
    document.documentElement.classList.toggle('erika-game-immersive', on)
    requestAnimationFrame(updateFit)
  })

  onMounted(() => {
    if (viewportMeta && !originalViewport.includes('viewport-fit')) {
      viewportMeta.content = `${originalViewport}, viewport-fit=cover`
    }
    document.documentElement.classList.toggle('erika-game-immersive', immersive.value)
    window.addEventListener('resize', onResize)
    window.addEventListener('orientationchange', onResize)
    window.addEventListener('pointerdown', onPointerDown, { capture: true, passive: true })
    document.addEventListener('fullscreenchange', onFullscreenChange)
    coarseQuery?.addEventListener('change', onCoarseChange)
    resizeObserver = new ResizeObserver(updateFit)
    if (stageRef.value) resizeObserver.observe(stageRef.value)
    if (canvasBoxRef.value) resizeObserver.observe(canvasBoxRef.value)
    updateFit()
  })

  onUnmounted(() => {
    if (viewportMeta) viewportMeta.content = originalViewport
    document.documentElement.classList.remove('erika-game-immersive')
    window.removeEventListener('resize', onResize)
    window.removeEventListener('orientationchange', onResize)
    window.removeEventListener('pointerdown', onPointerDown, { capture: true })
    document.removeEventListener('fullscreenchange', onFullscreenChange)
    coarseQuery?.removeEventListener('change', onCoarseChange)
    resizeObserver?.disconnect()
    if (document.fullscreenElement) void document.exitFullscreen().catch(() => {})
  })

  return {
    isTouch, isLandscape, immersive, isFullscreen, fullscreenSupported,
    toggleFullscreen, fitSize, compactOverlay, renderScale,
  }
}
