/**
 * 毎フレーム重い処理（shadowBlur・fillText・ctx.filter）をキャッシュ化して、
 * スマホでも 60fps を保ちやすくするためのユーティリティ。
 */

// 弾（光る円＋音符記号）を一度だけ描いて使い回す。2倍解像度で作って高DPIでも滲ませない。
const GLYPH_SCALE = 2
const GLOW = 10
const glyphCache = new Map<string, HTMLCanvasElement>()

export function getBulletGlyph(symbol: string, color: string, radius: number): HTMLCanvasElement {
  const key = `${symbol}|${color}|${radius}`
  const cached = glyphCache.get(key)
  if (cached) return cached

  const fontSize = Math.max(13, radius * 1.3)
  const font = `bold ${fontSize}px sans-serif`
  const measure = document.createElement('canvas').getContext('2d')!
  measure.font = font
  const textWidth = measure.measureText(symbol).width
  const half = Math.ceil(Math.max(radius, textWidth / 2, fontSize / 2) + GLOW + 2)

  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = half * 2 * GLYPH_SCALE
  const ctx = canvas.getContext('2d')!
  ctx.scale(GLYPH_SCALE, GLYPH_SCALE)
  ctx.translate(half, half)
  ctx.shadowColor = color
  ctx.shadowBlur = GLOW
  ctx.beginPath()
  ctx.arc(0, 0, radius, 0, Math.PI * 2)
  ctx.fillStyle = color + '44'
  ctx.fill()
  ctx.fillStyle = color
  ctx.font = font
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(symbol, 0, 0)

  if (glyphCache.size > 300) glyphCache.clear()
  glyphCache.set(key, canvas)
  return canvas
}

export function drawBulletGlyph(ctx: CanvasRenderingContext2D, symbol: string, color: string, radius: number, x: number, y: number) {
  const glyph = getBulletGlyph(symbol, color, radius)
  const size = glyph.width / GLYPH_SCALE
  ctx.drawImage(glyph, x - size / 2, y - size / 2, size, size)
}

// 色相を回した敵スプライト。ctx.filter を毎フレーム使うと重いので、色ごとに1回だけ作る。
const tintCache = new Map<string, HTMLCanvasElement>()
const supportsCanvasFilter = (() => {
  try {
    const ctx = document.createElement('canvas').getContext('2d')
    return !!ctx && 'filter' in ctx
  } catch {
    return false
  }
})()

export function getTintedSprite(key: string, img: HTMLImageElement, hueRotateDeg: number): HTMLImageElement | HTMLCanvasElement {
  const hue = ((Math.round(hueRotateDeg) % 360) + 360) % 360
  if (hue === 0 || !supportsCanvasFilter || !img.complete || !img.naturalWidth) return img
  const cacheKey = `${key}|${hue}`
  const cached = tintCache.get(cacheKey)
  if (cached) return cached
  const canvas = document.createElement('canvas')
  canvas.width = img.naturalWidth
  canvas.height = img.naturalHeight
  const ctx = canvas.getContext('2d')!
  ctx.filter = `hue-rotate(${hue}deg) saturate(1.3)`
  ctx.drawImage(img, 0, 0)
  tintCache.set(cacheKey, canvas)
  return canvas
}
