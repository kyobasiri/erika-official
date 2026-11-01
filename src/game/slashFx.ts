/**
 * 偃月サウンド薙ぎ払いのエフェクト。
 * 「光の刀身」が真上から前方へ一周し、その後ろに三日月形の残光が伸びる。
 * 判定（半径 radius の円）は従来どおりで、見た目だけを担当する。
 */
export interface SlashLook {
  radius: number
  timer: number
  maxTimer: number
  color: string
  canClearBullets: boolean
}

const TRAIL = 1.9 // 残光の長さ（ラジアン）
const SEGMENTS = 16

/** 刀身の先端座標を返す（火花を出すのに使う） */
export function drawCrescentSlash(
  ctx: CanvasRenderingContext2D, cx: number, cy: number, sw: SlashLook, facing: number,
): { tipX: number; tipY: number } {
  const progress = 1 - sw.timer / sw.maxTimer
  const dir = facing >= 0 ? 1 : -1
  // 真上(-90°)からスタートして、向いている方向へ振り下ろす
  const lead = -Math.PI / 2 + dir * progress * Math.PI * 2
  const fade = Math.min(1, sw.timer / 5)
  const R = sw.radius
  const thick = sw.canClearBullets ? 14 : 10

  ctx.save()
  ctx.translate(cx, cy)
  ctx.lineCap = 'round'

  // 三日月の残光（先端ほど太く明るい）
  const trailLen = Math.min(TRAIL, progress * Math.PI * 2 + 0.2)
  for (let k = 0; k < SEGMENTS; k++) {
    const t0 = k / SEGMENTS
    const t1 = (k + 1) / SEGMENTS
    const a0 = lead - dir * trailLen * (1 - t0)
    const a1 = lead - dir * trailLen * (1 - t1)
    ctx.beginPath()
    ctx.arc(0, 0, R - thick * 0.35 * (1 - t1), Math.min(a0, a1), Math.max(a0, a1))
    ctx.strokeStyle = sw.color
    ctx.globalAlpha = fade * Math.pow(t1, 1.6) * 0.8
    ctx.lineWidth = 2 + thick * t1
    ctx.stroke()
  }
  // 残光の芯（白）
  ctx.beginPath()
  const coreStart = lead - dir * trailLen * 0.35
  ctx.arc(0, 0, R, Math.min(coreStart, lead), Math.max(coreStart, lead))
  ctx.strokeStyle = '#ffffff'
  ctx.globalAlpha = fade * 0.85
  ctx.lineWidth = 2.2
  ctx.stroke()

  // 光の刀身
  ctx.rotate(lead)
  ctx.globalAlpha = fade
  ctx.shadowColor = sw.color
  ctx.shadowBlur = sw.canClearBullets ? 20 : 12
  const inner = R * 0.32
  const outer = R * 1.12
  ctx.beginPath()
  ctx.moveTo(inner, -2.6)
  ctx.lineTo(outer - 10, -3.2)
  ctx.quadraticCurveTo(outer + 2, -1.5, outer + 4, 0) // 切っ先
  ctx.quadraticCurveTo(outer - 6, 2.4, inner, 2.2)
  ctx.closePath()
  const blade = ctx.createLinearGradient(inner, 0, outer, 0)
  blade.addColorStop(0, sw.color)
  blade.addColorStop(0.45, '#ffffff')
  blade.addColorStop(1, '#ffffff')
  ctx.fillStyle = blade
  ctx.fill()
  ctx.shadowBlur = 0
  // 鍔（つば）と柄
  ctx.fillStyle = '#facc15'
  ctx.fillRect(inner - 2, -5, 3, 10)
  ctx.fillStyle = '#1e1b4b'
  ctx.fillRect(inner - 12, -2, 10, 4)

  ctx.restore()

  // Lv2以上チャージ（弾消し可能）のときは衝撃波リング
  if (sw.canClearBullets) {
    ctx.save()
    ctx.globalAlpha = fade * (1 - progress) * 0.7
    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.arc(cx, cy, R * (0.6 + progress * 0.55), 0, Math.PI * 2)
    ctx.stroke()
    ctx.restore()
  }

  return { tipX: cx + Math.cos(lead) * R * 1.1, tipY: cy + Math.sin(lead) * R * 1.1 }
}
