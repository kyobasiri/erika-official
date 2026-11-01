/**
 * ERIKA ROCK ACTION ステージ美術（床テクスチャ・障害物・足場・落とし穴・背景ビル）
 *
 * すべてコードで描いて、オフスクリーン Canvas にキャッシュする（画像素材なし・毎フレームは貼るだけ）。
 * ステージの bgStyle ごとに見た目が変わる:
 *   CITY      … アスファルト道路 ／ ギターアンプのスタック ／ 照明トラス
 *   CYBER     … 回路基板の床 ／ ネオンのサーバータワー ／ ホログラム足場
 *   PILLARS   … ライブステージの床板 ／ 巨大スピーカー ／ 照明付きトラス
 *   OCEAN     … 砂地と貝 ／ サンゴ岩 ／ 流木
 *   CATHEDRAL … 大理石のタイル ／ 金装飾の柱 ／ 大理石の張り出し
 *   GOTHIC    … 石畳 ／ 十字架の墓石 ／ 鉄の格子足場
 */

export type StageStyle = 'CITY' | 'CYBER' | 'PILLARS' | 'OCEAN' | 'CATHEDRAL' | 'GOTHIC'
const S = 2 // キャッシュの解像度倍率（高DPIでも粗くならない）

const cache = new Map<string, HTMLCanvasElement>()
const makeCanvas = (w: number, h: number, draw: (ctx: CanvasRenderingContext2D) => void) => {
  const c = document.createElement('canvas')
  c.width = Math.max(1, Math.ceil(w * S))
  c.height = Math.max(1, Math.ceil(h * S))
  const ctx = c.getContext('2d')!
  ctx.scale(S, S)
  draw(ctx)
  return c
}
const cached = (key: string, w: number, h: number, draw: (ctx: CanvasRenderingContext2D) => void) => {
  let c = cache.get(key)
  if (!c) {
    if (cache.size > 400) cache.clear()
    c = makeCanvas(w, h, draw)
    cache.set(key, c)
  }
  return c
}

// 位置から決まる疑似乱数（毎回同じ模様になる）
const rand = (seed: number) => {
  let s = Math.floor(seed * 9301 + 49297) % 233280
  return () => { s = (s * 9301 + 49297) % 233280; return s / 233280 }
}
const normStyle = (style: string): StageStyle =>
  (['CITY', 'CYBER', 'PILLARS', 'OCEAN', 'CATHEDRAL', 'GOTHIC'].includes(style) ? style : 'CITY') as StageStyle

// ====================================================
// 床（横に繰り返すタイル）
// ====================================================
export const GROUND_TILE_W = 96

function drawGroundTile(ctx: CanvasRenderingContext2D, style: StageStyle, base: string, line: string, h: number) {
  const w = GROUND_TILE_W
  const g = ctx.createLinearGradient(0, 0, 0, h)
  g.addColorStop(0, base)
  g.addColorStop(1, '#020617')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, w, h)
  const r = rand(style.length * 17)

  switch (style) {
    case 'CITY': {
      // 歩道の縁石＋アスファルト＋車線の破線
      ctx.fillStyle = 'rgba(148,163,184,0.18)'
      ctx.fillRect(0, 0, w, 7)
      ctx.fillStyle = 'rgba(15,23,42,0.6)'
      for (let x = 0; x < w; x += 24) ctx.fillRect(x, 0, 1.5, 7)
      for (let i = 0; i < 40; i++) {
        ctx.fillStyle = `rgba(255,255,255,${0.03 + r() * 0.05})`
        ctx.fillRect(r() * w, 9 + r() * (h - 9), 1.2, 1.2)
      }
      ctx.fillStyle = line
      ctx.globalAlpha = 0.55
      ctx.fillRect(14, 22, 34, 3)
      ctx.globalAlpha = 1
      break
    }
    case 'CYBER': {
      // 回路パターン
      ctx.strokeStyle = 'rgba(52,211,153,0.35)'
      ctx.lineWidth = 1
      ctx.beginPath()
      ctx.moveTo(0, 12); ctx.lineTo(30, 12); ctx.lineTo(40, 22); ctx.lineTo(70, 22); ctx.lineTo(78, 14); ctx.lineTo(w, 14)
      ctx.moveTo(10, h); ctx.lineTo(10, 30); ctx.lineTo(22, 30)
      ctx.moveTo(60, h); ctx.lineTo(60, 32); ctx.lineTo(86, 32)
      ctx.stroke()
      ctx.fillStyle = '#6ee7b7'
      for (const [x, y] of [[40, 22], [70, 22], [22, 30], [86, 32]]) {
        ctx.beginPath(); ctx.arc(x, y, 2, 0, Math.PI * 2); ctx.fill()
      }
      ctx.strokeStyle = 'rgba(52,211,153,0.12)'
      for (let x = 0; x <= w; x += 16) { ctx.beginPath(); ctx.moveTo(x, 4); ctx.lineTo(x, h); ctx.stroke() }
      break
    }
    case 'PILLARS': {
      // ライブステージの黒い床板＋ガムテープのバミリ
      ctx.fillStyle = 'rgba(0,0,0,0.35)'
      for (let x = 0; x < w; x += 32) ctx.fillRect(x, 0, 1.5, h)
      ctx.fillStyle = 'rgba(255,255,255,0.04)'
      for (let x = 0; x < w; x += 32) ctx.fillRect(x + 2, 0, 28, 2)
      ctx.fillStyle = 'rgba(251,146,60,0.65)'
      ctx.fillRect(56, 16, 12, 3); ctx.fillRect(60.5, 12, 3, 11)
      // 床を這うケーブル
      ctx.strokeStyle = 'rgba(15,15,15,0.9)'; ctx.lineWidth = 2.2
      ctx.beginPath(); ctx.moveTo(0, 30); ctx.bezierCurveTo(30, 24, 50, 38, w, 30); ctx.stroke()
      break
    }
    case 'OCEAN': {
      // 砂の波紋・小石・貝
      ctx.fillStyle = 'rgba(253,230,138,0.13)'
      ctx.fillRect(0, 0, w, h)
      ctx.strokeStyle = 'rgba(186,230,253,0.22)'; ctx.lineWidth = 1.2
      for (let y = 8; y < h; y += 9) {
        ctx.beginPath()
        for (let x = 0; x <= w; x += 4) ctx.lineTo(x, y + Math.sin((x / w) * Math.PI * 4 + y) * 1.6)
        ctx.stroke()
      }
      for (let i = 0; i < 6; i++) {
        ctx.fillStyle = `rgba(226,232,240,${0.15 + r() * 0.2})`
        ctx.beginPath(); ctx.ellipse(r() * w, 6 + r() * (h - 8), 2 + r() * 2, 1.4, 0, 0, Math.PI * 2); ctx.fill()
      }
      ctx.fillStyle = 'rgba(251,207,232,0.55)'
      ctx.beginPath(); ctx.arc(72, 26, 4, Math.PI, 0); ctx.fill()
      break
    }
    case 'CATHEDRAL': {
      // 白黒大理石の市松＋金の縁
      const size = 24
      for (let x = 0; x < w; x += size) {
        for (let y = 4; y < h; y += size) {
          const dark = ((x / size) + Math.floor(y / size)) % 2 === 0
          ctx.fillStyle = dark ? 'rgba(41,37,36,0.85)' : 'rgba(231,229,228,0.22)'
          ctx.fillRect(x, y, size, size)
        }
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.12)'; ctx.lineWidth = 0.8
      ctx.beginPath(); ctx.moveTo(4, 10); ctx.quadraticCurveTo(14, 18, 20, 26); ctx.moveTo(52, 6); ctx.lineTo(66, 24); ctx.stroke()
      ctx.fillStyle = 'rgba(250,204,21,0.7)'
      ctx.fillRect(0, 0, w, 4)
      break
    }
    case 'GOTHIC': {
      // 石畳と苔
      const rows = [4, 18, 32]
      rows.forEach((y, row) => {
        const off = row % 2 ? 16 : 0
        for (let x = -off; x < w; x += 32) {
          ctx.fillStyle = `rgba(${70 + r() * 30},${60 + r() * 20},${90 + r() * 30},0.55)`
          ctx.beginPath()
          ctx.roundRect(x + 1.5, y + 1, 29, 12, 3)
          ctx.fill()
        }
      })
      ctx.fillStyle = 'rgba(74,222,128,0.18)'
      ctx.beginPath(); ctx.ellipse(40, 16, 8, 2, 0, 0, Math.PI * 2); ctx.fill()
      break
    }
  }
}

export function getGroundTile(styleName: string, base: string, line: string, h: number) {
  const style = normStyle(styleName)
  return cached(`ground|${style}|${base}|${line}|${h}`, GROUND_TILE_W, h, (ctx) => drawGroundTile(ctx, style, base, line, h))
}

/** 床を描く（scrollX でテクスチャが流れる） */
export function drawGround(
  ctx: CanvasRenderingContext2D, styleName: string, base: string, line: string,
  groundY: number, viewW: number, viewH: number, scrollX: number,
) {
  const h = Math.ceil(viewH - groundY + 40)
  const tile = getGroundTile(styleName, base, line, h)
  const off = ((scrollX % GROUND_TILE_W) + GROUND_TILE_W) % GROUND_TILE_W
  for (let x = -GROUND_TILE_W - off; x < viewW + GROUND_TILE_W; x += GROUND_TILE_W) {
    ctx.drawImage(tile, x, groundY, GROUND_TILE_W, h)
  }
  // 床の縁：細い光の線＋ふんわりした光
  const glow = ctx.createLinearGradient(0, groundY - 10, 0, groundY + 6)
  glow.addColorStop(0, 'rgba(0,0,0,0)')
  glow.addColorStop(1, hexToRgba(line, 0.28))
  ctx.fillStyle = glow
  ctx.fillRect(-100, groundY - 10, viewW + 200, 16)
  ctx.fillStyle = line
  ctx.fillRect(-100, groundY - 1, viewW + 200, 2)
}

// ====================================================
// 落とし穴：赤線ではなく「崖の断面」と「底なしの闇」
// ====================================================
export function drawPit(
  ctx: CanvasRenderingContext2D, styleName: string, line: string,
  x: number, w: number, groundY: number, viewH: number, time: number,
) {
  const depth = viewH - groundY + 40
  // 見えている範囲（床〜画面下）で闇から色の気配へ
  const g = ctx.createLinearGradient(0, groundY, 0, viewH)
  g.addColorStop(0, '#000000')
  g.addColorStop(0.55, '#03030a')
  g.addColorStop(1, hexToRgba(line, 0.4))
  ctx.fillStyle = g
  ctx.fillRect(x, groundY - 1, w, depth)

  // 崖の断面（左右の壁）
  const edge = ctx.createLinearGradient(x, 0, x + 10, 0)
  edge.addColorStop(0, 'rgba(148,163,184,0.35)')
  edge.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = edge
  ctx.fillRect(x, groundY, 10, depth)
  const edgeR = ctx.createLinearGradient(x + w, 0, x + w - 10, 0)
  edgeR.addColorStop(0, 'rgba(148,163,184,0.35)')
  edgeR.addColorStop(1, 'rgba(0,0,0,0)')
  ctx.fillStyle = edgeR
  ctx.fillRect(x + w - 10, groundY, 10, depth)

  // 縁の角を少し欠けさせる
  ctx.fillStyle = '#000'
  ctx.beginPath()
  ctx.moveTo(x - 1, groundY - 1); ctx.lineTo(x + 6, groundY - 1); ctx.lineTo(x - 1, groundY + 6); ctx.fill()
  ctx.beginPath()
  ctx.moveTo(x + w + 1, groundY - 1); ctx.lineTo(x + w - 6, groundY - 1); ctx.lineTo(x + w + 1, groundY + 6); ctx.fill()

  // 底から舞い上がる光の粒（危険の気配をさりげなく）
  const style = normStyle(styleName)
  const color = style === 'OCEAN' ? 'rgba(186,230,253,' : hexToRgba(line, 1).replace(/[\d.]+\)$/, '')
  for (let i = 0; i < 4; i++) {
    const px = x + 12 + ((i * 37 + Math.floor(x)) % Math.max(1, w - 24))
    const life = ((time * 0.0006 + i * 0.27) % 1)
    const py = groundY + depth - life * depth * 0.8
    ctx.fillStyle = `${color}${(0.5 * (1 - life)).toFixed(2)})`
    ctx.fillRect(px, py, 2, 2)
  }
}

// ====================================================
// 障害物（壁）
// ====================================================
function drawWall(ctx: CanvasRenderingContext2D, style: StageStyle, w: number, h: number, line: string) {
  const r = rand(w * 31 + h * 7)
  switch (style) {
    case 'CITY': {
      // ギターアンプのスタック
      const heads = h > 70 ? 2 : 1
      const cabH = (h - 14) / heads
      for (let i = 0; i < heads; i++) {
        const y = 14 + i * cabH
        ctx.fillStyle = '#111114'
        ctx.beginPath(); ctx.roundRect(0, y, w, cabH - 1, 3); ctx.fill()
        ctx.strokeStyle = hexToRgba(line, 0.9); ctx.lineWidth = 1.2
        ctx.strokeRect(2, y + 2, w - 4, cabH - 5)
        // グリルの格子
        ctx.fillStyle = '#2a2622'
        ctx.fillRect(5, y + 5, w - 10, cabH - 11)
        ctx.strokeStyle = 'rgba(255,255,255,0.06)'; ctx.lineWidth = 0.7
        for (let gx = 7; gx < w - 5; gx += 3) { ctx.beginPath(); ctx.moveTo(gx, y + 5); ctx.lineTo(gx - 4, y + cabH - 6); ctx.stroke() }
      }
      // ヘッド部（ツマミ付き）
      ctx.fillStyle = '#1c1917'
      ctx.beginPath(); ctx.roundRect(-1, 0, w + 2, 14, 3); ctx.fill()
      ctx.fillStyle = '#d6b36a'
      ctx.fillRect(2, 3, w - 4, 8)
      ctx.fillStyle = '#111'
      for (let k = 0; k < 4; k++) { ctx.beginPath(); ctx.arc(7 + k * ((w - 14) / 3), 7, 2, 0, Math.PI * 2); ctx.fill() }
      break
    }
    case 'CYBER': {
      ctx.fillStyle = '#04120d'
      ctx.fillRect(0, 0, w, h)
      ctx.strokeStyle = '#34d399'; ctx.lineWidth = 1.5
      ctx.shadowColor = '#34d399'; ctx.shadowBlur = 6
      ctx.strokeRect(1.5, 1.5, w - 3, h - 3)
      ctx.shadowBlur = 0
      for (let y = 6; y < h - 4; y += 7) {
        ctx.fillStyle = 'rgba(52,211,153,0.15)'
        ctx.fillRect(5, y, w - 10, 4)
        ctx.fillStyle = r() > 0.4 ? '#6ee7b7' : '#f472b6'
        ctx.fillRect(w - 10, y + 1, 2.5, 2)
      }
      break
    }
    case 'PILLARS': {
      // 巨大スピーカー（ウーファー2発）
      ctx.fillStyle = '#18181b'
      ctx.beginPath(); ctx.roundRect(0, 0, w, h, 4); ctx.fill()
      ctx.strokeStyle = 'rgba(249,115,22,0.8)'; ctx.lineWidth = 1.4
      ctx.strokeRect(1.5, 1.5, w - 3, h - 3)
      const cones = Math.max(1, Math.floor(h / (w * 0.95)))
      for (let i = 0; i < cones; i++) {
        const cy = (h / cones) * (i + 0.5)
        const rad = Math.min(w, h / cones) * 0.38
        const cg = ctx.createRadialGradient(w / 2, cy, 1, w / 2, cy, rad)
        cg.addColorStop(0, '#52525b'); cg.addColorStop(0.35, '#18181b'); cg.addColorStop(0.9, '#27272a'); cg.addColorStop(1, '#f97316')
        ctx.fillStyle = cg
        ctx.beginPath(); ctx.arc(w / 2, cy, rad, 0, Math.PI * 2); ctx.fill()
      }
      break
    }
    case 'OCEAN': {
      // サンゴ岩
      const g = ctx.createLinearGradient(0, 0, w, 0)
      g.addColorStop(0, '#0e7490'); g.addColorStop(0.5, '#155e75'); g.addColorStop(1, '#083344')
      ctx.fillStyle = g
      ctx.beginPath()
      ctx.moveTo(0, h); ctx.lineTo(2, h * 0.3); ctx.quadraticCurveTo(w * 0.2, -2, w * 0.55, 3)
      ctx.quadraticCurveTo(w, 6, w - 2, h * 0.35); ctx.lineTo(w, h); ctx.closePath(); ctx.fill()
      for (let i = 0; i < 7; i++) {
        ctx.fillStyle = `rgba(${200 + r() * 55},${120 + r() * 80},${150 + r() * 60},0.55)`
        ctx.beginPath(); ctx.arc(4 + r() * (w - 8), 8 + r() * (h - 12), 1.5 + r() * 2.5, 0, Math.PI * 2); ctx.fill()
      }
      ctx.strokeStyle = 'rgba(56,189,248,0.55)'; ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(4, h * 0.3); ctx.quadraticCurveTo(w * 0.25, 1, w * 0.55, 4); ctx.stroke()
      break
    }
    case 'CATHEDRAL': {
      // 大理石の柱＋金の柱頭
      const g = ctx.createLinearGradient(0, 0, w, 0)
      g.addColorStop(0, '#a8a29e'); g.addColorStop(0.35, '#f5f5f4'); g.addColorStop(1, '#78716c')
      ctx.fillStyle = g
      ctx.fillRect(4, 8, w - 8, h - 14)
      ctx.strokeStyle = 'rgba(68,64,60,0.35)'; ctx.lineWidth = 1
      for (let x = 9; x < w - 6; x += 6) { ctx.beginPath(); ctx.moveTo(x, 10); ctx.lineTo(x, h - 7); ctx.stroke() }
      ctx.fillStyle = '#ca8a04'
      ctx.fillRect(0, 0, w, 8); ctx.fillRect(1, h - 6, w - 2, 6)
      ctx.fillStyle = '#fde047'
      ctx.fillRect(0, 0, w, 2); ctx.fillRect(1, h - 6, w - 2, 1.5)
      break
    }
    case 'GOTHIC': {
      // 十字架付きの墓石
      ctx.fillStyle = '#3f3a4a'
      ctx.beginPath()
      ctx.moveTo(0, h); ctx.lineTo(0, 14); ctx.quadraticCurveTo(w / 2, -4, w, 14); ctx.lineTo(w, h); ctx.closePath(); ctx.fill()
      ctx.fillStyle = 'rgba(255,255,255,0.06)'
      ctx.fillRect(3, 16, 4, h - 18)
      ctx.fillStyle = '#c084fc'
      ctx.fillRect(w / 2 - 1.5, 12, 3, Math.min(20, h * 0.4))
      ctx.fillRect(w / 2 - 6, 18, 12, 3)
      ctx.strokeStyle = 'rgba(0,0,0,0.5)'; ctx.lineWidth = 1
      ctx.beginPath(); ctx.moveTo(w * 0.7, h * 0.45); ctx.lineTo(w * 0.62, h * 0.6); ctx.lineTo(w * 0.75, h * 0.72); ctx.stroke()
      ctx.fillStyle = 'rgba(74,222,128,0.35)'
      ctx.beginPath(); ctx.ellipse(w * 0.3, h - 3, 9, 3, 0, 0, Math.PI * 2); ctx.fill()
      break
    }
  }
}

export function drawWallObstacle(ctx: CanvasRenderingContext2D, styleName: string, line: string, x: number, y: number, w: number, h: number) {
  const style = normStyle(styleName)
  const W = Math.round(w), H = Math.round(h)
  const img = cached(`wall|${style}|${line}|${W}|${H}`, W, H, (c) => drawWall(c, style, W, H, line))
  // 足元の影
  ctx.fillStyle = 'rgba(0,0,0,0.35)'
  ctx.beginPath(); ctx.ellipse(x + w / 2, y + h, w * 0.65, 3, 0, 0, Math.PI * 2); ctx.fill()
  ctx.drawImage(img, x, y, w, h)
}

// ====================================================
// 足場（platform）
// ====================================================
function drawPlatformArt(ctx: CanvasRenderingContext2D, style: StageStyle, w: number, h: number, line: string) {
  switch (style) {
    case 'CITY':
    case 'PILLARS': {
      // 照明トラス
      const col = style === 'PILLARS' ? '#d4d4d8' : '#94a3b8'
      ctx.strokeStyle = col; ctx.lineWidth = 1.6
      ctx.strokeRect(1, 1, w - 2, h - 2)
      ctx.lineWidth = 1
      ctx.beginPath()
      for (let x = 1; x < w - 2; x += 10) { ctx.moveTo(x, 1); ctx.lineTo(x + 10, h - 1); ctx.moveTo(x + 10, 1); ctx.lineTo(x, h - 1) }
      ctx.stroke()
      ctx.fillStyle = col
      ctx.fillRect(0, 0, w, 2.5)
      // ぶら下がるライト
      for (let x = 12; x < w - 6; x += 30) {
        ctx.fillStyle = '#18181b'; ctx.fillRect(x - 3, h - 1, 6, 5)
        ctx.fillStyle = style === 'PILLARS' ? '#fb923c' : line
        ctx.fillRect(x - 2, h + 3, 4, 1.5)
      }
      break
    }
    case 'CYBER': {
      ctx.fillStyle = 'rgba(16,185,129,0.25)'
      ctx.fillRect(0, 0, w, h)
      ctx.strokeStyle = '#6ee7b7'; ctx.lineWidth = 1.2
      ctx.strokeRect(0.5, 0.5, w - 1, h - 1)
      ctx.fillStyle = 'rgba(167,243,208,0.35)'
      for (let y = 3; y < h; y += 3) ctx.fillRect(2, y, w - 4, 0.8)
      ctx.fillStyle = '#a7f3d0'; ctx.fillRect(0, 0, w, 2)
      break
    }
    case 'OCEAN': {
      // 流木
      const g = ctx.createLinearGradient(0, 0, 0, h)
      g.addColorStop(0, '#a16207'); g.addColorStop(1, '#422006')
      ctx.fillStyle = g
      ctx.beginPath(); ctx.roundRect(0, 1, w, h - 2, h / 2); ctx.fill()
      ctx.strokeStyle = 'rgba(0,0,0,0.35)'; ctx.lineWidth = 0.8
      ctx.beginPath(); ctx.moveTo(6, h * 0.4); ctx.lineTo(w * 0.6, h * 0.45); ctx.moveTo(w * 0.3, h * 0.7); ctx.lineTo(w - 6, h * 0.65); ctx.stroke()
      ctx.fillStyle = 'rgba(34,197,94,0.6)'
      ctx.fillRect(w * 0.7, h - 2, 3, 5); ctx.fillRect(w * 0.2, h - 2, 2, 4)
      break
    }
    case 'CATHEDRAL': {
      ctx.fillStyle = '#e7e5e4'
      ctx.fillRect(0, 0, w, h)
      ctx.fillStyle = '#ca8a04'
      ctx.fillRect(0, 0, w, 3); ctx.fillRect(0, h - 3, w, 3)
      ctx.fillStyle = 'rgba(120,113,108,0.5)'
      for (let x = 8; x < w; x += 16) { ctx.beginPath(); ctx.arc(x, h / 2, 2.2, 0, Math.PI * 2); ctx.fill() }
      break
    }
    case 'GOTHIC': {
      // 鉄の格子
      ctx.fillStyle = '#1e1b2e'
      ctx.fillRect(0, 0, w, h)
      ctx.strokeStyle = '#7c3aed'; ctx.lineWidth = 1
      ctx.strokeRect(0.5, 0.5, w - 1, h - 1)
      ctx.beginPath()
      for (let x = 6; x < w; x += 7) { ctx.moveTo(x, 1); ctx.lineTo(x, h - 1) }
      ctx.stroke()
      ctx.fillStyle = '#a78bfa'; ctx.fillRect(0, 0, w, 2)
      break
    }
  }
}

export function drawPlatform(ctx: CanvasRenderingContext2D, styleName: string, line: string, x: number, y: number, w: number, h: number) {
  const style = normStyle(styleName)
  const W = Math.round(w), H = Math.round(h)
  // ライトが下にはみ出すので、少し高めに作る
  const img = cached(`plat|${style}|${line}|${W}|${H}`, W, H + 6, (c) => drawPlatformArt(c, style, W, H, line))
  ctx.drawImage(img, x, y, w, h + 6)
}

// ====================================================
// 背景のビル（窓明かり付き）
// ====================================================
export function getBuilding(styleName: string, w: number, h: number, seed: number) {
  const style = normStyle(styleName)
  const H = Math.round(h)
  return cached(`bld|${style}|${w}|${H}|${seed}`, w, H + 30, (ctx) => {
    const r = rand(seed + 1)
    const top = 30
    ctx.fillStyle = 'rgba(15, 23, 42, 0.62)'
    if (style === 'CATHEDRAL' || style === 'GOTHIC') {
      ctx.beginPath()
      ctx.moveTo(0, H + top); ctx.lineTo(0, top); ctx.lineTo(w / 2, top - 28); ctx.lineTo(w, top); ctx.lineTo(w, H + top); ctx.fill()
      // ステンドグラス風の窓
      const glass = style === 'GOTHIC' ? 'rgba(225,29,72,' : 'rgba(250,204,21,'
      for (let y = top + 12; y < H + top - 14; y += 26) {
        ctx.fillStyle = `${glass}${(0.18 + r() * 0.3).toFixed(2)})`
        ctx.beginPath(); ctx.roundRect(w / 2 - 5, y, 10, 16, [5, 5, 0, 0]); ctx.fill()
      }
      return
    }
    if (style === 'OCEAN') {
      // 海底の岩柱と海藻のシルエット
      ctx.fillStyle = 'rgba(8, 47, 73, 0.7)'
      ctx.beginPath()
      ctx.moveTo(0, H + top)
      ctx.quadraticCurveTo(w * 0.05, top + H * 0.3, w * 0.35, top + 4)
      ctx.quadraticCurveTo(w * 0.6, top - 6, w * 0.8, top + H * 0.25)
      ctx.quadraticCurveTo(w, top + H * 0.6, w, H + top)
      ctx.fill()
      ctx.strokeStyle = 'rgba(20, 184, 166, 0.35)'; ctx.lineWidth = 2
      for (let k = 0; k < 2; k++) {
        const kx = w * (0.25 + k * 0.45)
        ctx.beginPath(); ctx.moveTo(kx, H + top)
        for (let y = H + top; y > top + H * 0.35; y -= 6) ctx.lineTo(kx + Math.sin(y * 0.15 + k) * 3, y)
        ctx.stroke()
      }
      return
    }
    ctx.fillRect(0, top, w, H)
    // 窓
    const warm = style === 'PILLARS'
    for (let y = top + 6; y < H + top - 6; y += 9) {
      for (let x = 5; x < w - 5; x += 8) {
        if (r() < 0.55) continue
        ctx.fillStyle = warm ? `rgba(251,146,60,${(0.15 + r() * 0.35).toFixed(2)})` : `rgba(253,224,171,${(0.12 + r() * 0.35).toFixed(2)})`
        ctx.fillRect(x, y, 4, 4.5)
      }
    }
    // 屋上のアンテナ
    if (r() > 0.5) { ctx.fillRect(w * 0.7, top - 10, 1.5, 10); ctx.fillStyle = '#ef4444'; ctx.fillRect(w * 0.7 - 1, top - 12, 3.5, 2.5) }
  })
}

export function hexToRgba(hex: string, alpha: number) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim())
  if (!m) return `rgba(236,72,153,${alpha})`
  const n = parseInt(m[1], 16)
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${alpha})`
}
