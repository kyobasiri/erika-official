/**
 * Sprite drawing utility for ERIKA ROCK ACTION.
 * Trims transparent padding once at load time; all poses are positioned from
 * the visible artwork's bottom edge without changing the collision boxes.
 */
export interface SpriteCrop { sx: number; sy: number; sw: number; sh: number }
export interface SpriteLayout { width: number; height: number }
export interface SpriteDrawOptions {
  maxHeight: number
  maxWidth: number
  offsetX?: number
  offsetY?: number
  opacity?: number
  scaleX?: number
  scaleY?: number
}

const crops = new WeakMap<HTMLImageElement, SpriteCrop>()
const SAMPLE = 192

// Sample the alpha channel once; ignore barely visible compression / antialias
// pixels so a fallen character on a square transparent PNG is not tiny.
export function measureSprite(img: HTMLImageElement): void {
  if (!img.complete || img.naturalWidth === 0 || crops.has(img)) return
  try {
    const canvas = document.createElement('canvas')
    canvas.width = SAMPLE
    canvas.height = SAMPLE
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) return
    ctx.clearRect(0, 0, SAMPLE, SAMPLE)
    ctx.drawImage(img, 0, 0, SAMPLE, SAMPLE)
    const pixels = ctx.getImageData(0, 0, SAMPLE, SAMPLE).data
    let minX = SAMPLE, minY = SAMPLE, maxX = -1, maxY = -1
    for (let y = 0; y < SAMPLE; y++) {
      for (let x = 0; x < SAMPLE; x++) {
        if (pixels[(y * SAMPLE + x) * 4 + 3] < 48) continue
        minX = Math.min(minX, x); minY = Math.min(minY, y)
        maxX = Math.max(maxX, x); maxY = Math.max(maxY, y)
      }
    }
    if (maxX < minX || maxY < minY) return
    const left = Math.max(0, minX - 2)
    const top = Math.max(0, minY - 2)
    const right = Math.min(SAMPLE, maxX + 3)
    const bottom = Math.min(SAMPLE, maxY + 3)
    crops.set(img, {
      sx: left / SAMPLE * img.naturalWidth,
      sy: top / SAMPLE * img.naturalHeight,
      sw: (right - left) / SAMPLE * img.naturalWidth,
      sh: (bottom - top) / SAMPLE * img.naturalHeight,
    })
  } catch {
    // If alpha sampling fails (e.g. security restriction), draw the full PNG.
  }
}

export function layoutSprite(crop: SpriteCrop, maxWidth: number, maxHeight: number): SpriteLayout {
  const ratio = crop.sw / crop.sh
  if (!(ratio > 0) || !(maxWidth > 0) || !(maxHeight > 0)) return { width: 0, height: 0 }
  const height = Math.min(maxHeight, maxWidth / ratio)
  return { width: height * ratio, height }
}

export function drawFittedSprite(
  ctx: CanvasRenderingContext2D,
  img: HTMLImageElement | undefined,
  x: number, bottomY: number, facing: number,
  options: SpriteDrawOptions,
): void {
  if (!img || !img.complete || !img.naturalWidth) return
  const crop = crops.get(img) ?? { sx: 0, sy: 0, sw: img.naturalWidth, sh: img.naturalHeight }
  const { width, height } = layoutSprite(crop, options.maxWidth, options.maxHeight)
  if (width <= 0 || height <= 0) return
  ctx.save()
  ctx.translate(x + (options.offsetX ?? 0), bottomY + (options.offsetY ?? 0))
  ctx.scale(facing * (options.scaleX ?? 1), options.scaleY ?? 1)
  ctx.globalAlpha *= options.opacity ?? 1
  ctx.drawImage(img, crop.sx, crop.sy, crop.sw, crop.sh, -width / 2, -height, width, height)
  ctx.restore()
}
