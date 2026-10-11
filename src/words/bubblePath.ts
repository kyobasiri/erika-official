import type { BubbleShape, BubbleTail } from './types'

// 吹き出しの形を SVG のパスで作る（viewBox 0 0 100 100 に描き、要素の大きさに合わせて伸ばす）

const round = 'M 2 50 A 48 46 0 1 1 98 50 A 48 46 0 1 1 2 50 Z'

const TAILS: Record<Exclude<BubbleTail, 'none'>, string> = {
  'bottom-left': 'M 24 84 L 40 91 L 8 120 Z',
  'bottom-right': 'M 60 91 L 76 84 L 92 120 Z',
  left: 'M 7 38 L 9 60 L -18 58 Z',
  right: 'M 93 38 L 91 60 L 118 58 Z'
}

// 叫び：ギザギザ。毎回同じ形になるよう、乱数ではなく決まった揺らぎを使う
function spiky(points = 26) {
  const coords: string[] = []
  for (let i = 0; i < points; i++) {
    const angle = (i / points) * Math.PI * 2
    const outer = i % 2 === 0
    const wobble = outer ? 1 + 0.06 * Math.sin(i * 1.7) : 0.82 + 0.04 * Math.cos(i * 2.3)
    const rx = 49 * wobble
    const ry = 47 * wobble
    coords.push(`${(50 + Math.cos(angle) * rx).toFixed(2)} ${(50 + Math.sin(angle) * ry).toFixed(2)}`)
  }
  return `M ${coords.join(' L ')} Z`
}

const circle = (cx: number, cy: number, r: number) =>
  `M ${cx - r} ${cy} a ${r} ${r} 0 1 0 ${r * 2} 0 a ${r} ${r} 0 1 0 ${-r * 2} 0 Z`

// 心の声：ふわふわの雲。楕円の周りに円を並べ、中心を大きな楕円で埋める
function cloud() {
  const parts = ['M 10 50 A 40 38 0 1 1 90 50 A 40 38 0 1 1 10 50 Z']
  const n = 11
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2
    parts.push(circle(50 + Math.cos(a) * 38, 50 + Math.sin(a) * 36, 14 + (i % 3)))
  }
  return parts.join(' ')
}

// 心の声のしっぽは小さな丸を連ねる
const THOUGHT_TAILS: Record<Exclude<BubbleTail, 'none'>, string> = {
  'bottom-left': circle(20, 98, 6) + ' ' + circle(10, 112, 3.6),
  'bottom-right': circle(80, 98, 6) + ' ' + circle(90, 112, 3.6),
  left: circle(-4, 62, 6) + ' ' + circle(-16, 70, 3.6),
  right: circle(104, 62, 6) + ' ' + circle(116, 70, 3.6)
}

export function bubblePath(shape: BubbleShape = 'round', tail: BubbleTail = 'bottom-left') {
  if (shape === 'thought') {
    return cloud() + (tail === 'none' ? '' : ' ' + THOUGHT_TAILS[tail])
  }
  const body = shape === 'shout' ? spiky() : round
  return body + (tail === 'none' ? '' : ' ' + TAILS[tail])
}
