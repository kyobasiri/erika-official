import type { WordOptions } from './types'

// 言葉カードの画像の見せ方（位置と拡大率）を、各テンプレート共通のスタイルにする。
//
//   focus … 画像のどこを中心に見せるか（%）。拡大したときは、この点を中心に大きくなる
//   zoom  … 拡大率（1 = 枠いっぱい、最大 4）
//
// object-position だけだと、画像と枠の縦横比が同じとき（正方形の画像を正方形の枠に入れるなど）
// 位置を変えても動かないので、拡大（scale）と組み合わせて、どの画像でも位置を動かせるようにしている。

const clamp = (n: number, min: number, max: number) => Math.min(max, Math.max(min, n))

export const ZOOM_MIN = 1
export const ZOOM_MAX = 4

export function artImageStyle(options: WordOptions | undefined, fallbackY = 50) {
  const x = clamp(Number(options?.focus?.x ?? 50), 0, 100)
  const y = clamp(Number(options?.focus?.y ?? fallbackY), 0, 100)
  const zoomValue = Number(options?.zoom)
  const zoom = Number.isFinite(zoomValue) ? clamp(zoomValue, ZOOM_MIN, ZOOM_MAX) : 1
  return {
    objectPosition: `${x}% ${y}%`,
    transformOrigin: `${x}% ${y}%`,
    ...(zoom !== 1 ? { transform: `scale(${zoom})` } : {})
  }
}
