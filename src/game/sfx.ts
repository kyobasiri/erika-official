/**
 * ERIKA ROCK ACTION 効果音（Web Audio API で合成。音声ファイル不要）
 *
 * 後から音声素材に差し替えたい場合は、public/sfx/<名前>.mp3 などを置き、
 * SFX_FILES に登録すれば、その音だけファイル再生に切り替わる。
 */

export type SfxName =
  | 'shot' | 'charge1' | 'charge2' | 'charge3' | 'chargeShot' | 'slash'
  | 'jump' | 'dash' | 'stomp' | 'enemyHit' | 'enemyDown' | 'bossHit' | 'guard'
  | 'shieldBreak' | 'playerHit' | 'barrier' | 'item' | 'oneUp' | 'bossDown'
  | 'clear' | 'death' | 'warning' | 'select'

// 例: { shot: '/sfx/shot.mp3' }  ← 素材を用意したらここに追加
const SFX_FILES: Partial<Record<SfxName, string>> = {}

let ctx: AudioContext | null = null
let master: GainNode | null = null
let noiseBuffer: AudioBuffer | null = null
const fileBuffers = new Map<SfxName, AudioBuffer>()
let enabled = true
let volume = 0.5
const lastPlayed = new Map<SfxName, number>()

const getCtx = (): AudioContext | null => {
  if (ctx) return ctx
  const AC = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
  if (!AC) return null
  ctx = new AC()
  master = ctx.createGain()
  master.gain.value = volume
  // 音割れ防止
  const comp = ctx.createDynamicsCompressor()
  comp.threshold.value = -12
  comp.ratio.value = 6
  master.connect(comp).connect(ctx.destination)
  const len = ctx.sampleRate * 0.5
  noiseBuffer = ctx.createBuffer(1, len, ctx.sampleRate)
  const data = noiseBuffer.getChannelData(0)
  for (let i = 0; i < len; i++) data[i] = Math.random() * 2 - 1
  void loadFiles()
  return ctx
}

const loadFiles = async () => {
  for (const [name, url] of Object.entries(SFX_FILES) as [SfxName, string][]) {
    try {
      const res = await fetch(url)
      if (!res.ok || !ctx) continue
      fileBuffers.set(name, await ctx.decodeAudioData(await res.arrayBuffer()))
    } catch { /* 合成音のまま */ }
  }
}

/** スマホでは「ユーザー操作の中で」1回呼ぶ必要がある */
export function unlockAudio() {
  const c = getCtx()
  if (c && c.state === 'suspended') void c.resume()
}

export function setSfxEnabled(on: boolean) { enabled = on }
export function setSfxVolume(v: number) {
  volume = Math.max(0, Math.min(1, v))
  if (master) master.gain.value = volume
}
export function suspendAudio() { if (ctx && ctx.state === 'running') void ctx.suspend() }
export function resumeAudio() { if (ctx && ctx.state === 'suspended') void ctx.resume() }

type Wave = OscillatorType
const tone = (c: AudioContext, out: AudioNode, t: number, type: Wave, f0: number, f1: number, dur: number, gain: number) => {
  const o = c.createOscillator()
  const g = c.createGain()
  o.type = type
  o.frequency.setValueAtTime(f0, t)
  o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur)
  g.gain.setValueAtTime(0.0001, t)
  g.gain.exponentialRampToValueAtTime(gain, t + 0.008)
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
  o.connect(g).connect(out)
  o.start(t)
  o.stop(t + dur + 0.02)
}
const noise = (c: AudioContext, out: AudioNode, t: number, dur: number, gain: number, filterFreq: number, type: BiquadFilterType = 'lowpass', freqEnd?: number) => {
  if (!noiseBuffer) return
  const src = c.createBufferSource()
  src.buffer = noiseBuffer
  const f = c.createBiquadFilter()
  f.type = type
  f.frequency.setValueAtTime(filterFreq, t)
  if (freqEnd) f.frequency.exponentialRampToValueAtTime(freqEnd, t + dur)
  const g = c.createGain()
  g.gain.setValueAtTime(gain, t)
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur)
  src.connect(f).connect(g).connect(out)
  src.start(t)
  src.stop(t + dur + 0.02)
}
const arpeggio = (c: AudioContext, out: AudioNode, t: number, notes: number[], step: number, type: Wave, gain: number, len = step * 1.6) => {
  notes.forEach((f, i) => tone(c, out, t + i * step, type, f, f * 1.002, len, gain))
}

// 同じ音が1フレームに何十回も鳴らないよう最小間隔を設ける（ms）
const MIN_INTERVAL: Partial<Record<SfxName, number>> = {
  shot: 45, enemyHit: 40, bossHit: 55, guard: 60, stomp: 50, item: 60,
}

export function playSfx(name: SfxName) {
  if (!enabled) return
  const c = getCtx()
  if (!c || !master || c.state !== 'running') return
  const nowMs = performance.now()
  const gap = MIN_INTERVAL[name]
  if (gap && nowMs - (lastPlayed.get(name) ?? 0) < gap) return
  lastPlayed.set(name, nowMs)

  const file = fileBuffers.get(name)
  if (file) {
    const src = c.createBufferSource()
    src.buffer = file
    src.connect(master)
    src.start()
    return
  }

  const t = c.currentTime + 0.005
  const out = master
  switch (name) {
    case 'shot': // ピック弾き風
      tone(c, out, t, 'square', 1320, 660, 0.07, 0.07)
      tone(c, out, t, 'triangle', 1980, 990, 0.05, 0.04)
      break
    case 'charge1': tone(c, out, t, 'sine', 440, 880, 0.18, 0.08); break
    case 'charge2': arpeggio(c, out, t, [660, 880], 0.06, 'triangle', 0.09); break
    case 'charge3': arpeggio(c, out, t, [784, 988, 1175, 1568], 0.045, 'square', 0.05); break
    case 'chargeShot': // パワーコード風
      tone(c, out, t, 'sawtooth', 220, 110, 0.35, 0.12)
      tone(c, out, t, 'sawtooth', 330, 165, 0.35, 0.09)
      noise(c, out, t, 0.25, 0.25, 3000, 'lowpass', 400)
      break
    case 'slash':
      noise(c, out, t, 0.22, 0.35, 900, 'bandpass', 5200)
      tone(c, out, t, 'sine', 1800, 3200, 0.16, 0.03)
      break
    case 'jump': tone(c, out, t, 'square', 330, 660, 0.12, 0.05); break
    case 'dash': noise(c, out, t, 0.18, 0.2, 600, 'bandpass', 2400); break
    case 'stomp':
      tone(c, out, t, 'square', 520, 1040, 0.08, 0.07)
      tone(c, out, t + 0.06, 'square', 780, 1560, 0.08, 0.06)
      break
    case 'enemyHit': tone(c, out, t, 'square', 260, 180, 0.05, 0.05); break
    case 'enemyDown':
      noise(c, out, t, 0.2, 0.25, 2000, 'lowpass', 200)
      tone(c, out, t, 'square', 600, 120, 0.18, 0.06)
      break
    case 'bossHit':
      tone(c, out, t, 'square', 180, 90, 0.08, 0.08)
      noise(c, out, t, 0.06, 0.18, 2500)
      break
    case 'guard': tone(c, out, t, 'triangle', 1800, 1700, 0.09, 0.07); tone(c, out, t, 'sine', 2700, 2600, 0.12, 0.04); break
    case 'shieldBreak':
      noise(c, out, t, 0.6, 0.45, 6000, 'highpass', 800)
      arpeggio(c, out, t, [1568, 1175, 880, 659], 0.05, 'triangle', 0.08)
      break
    case 'playerHit':
      tone(c, out, t, 'sawtooth', 300, 70, 0.25, 0.12)
      noise(c, out, t, 0.15, 0.2, 1200)
      break
    case 'barrier': tone(c, out, t, 'sine', 900, 1400, 0.2, 0.09); break
    case 'item': arpeggio(c, out, t, [988, 1319], 0.06, 'square', 0.05); break
    case 'oneUp': arpeggio(c, out, t, [659, 784, 1319, 1047, 1175, 1568], 0.07, 'square', 0.05); break
    case 'bossDown':
      for (let i = 0; i < 5; i++) noise(c, out, t + i * 0.16, 0.35, 0.4, 1800 - i * 200, 'lowpass', 120)
      tone(c, out, t, 'sawtooth', 160, 40, 1.0, 0.12)
      break
    case 'clear': arpeggio(c, out, t, [523, 659, 784, 1047, 784, 1047, 1319], 0.11, 'square', 0.06, 0.2); break
    case 'death':
      arpeggio(c, out, t, [440, 415, 392, 370, 349], 0.14, 'triangle', 0.1, 0.25)
      tone(c, out, t + 0.7, 'sine', 110, 55, 1.0, 0.12)
      break
    case 'warning':
      tone(c, out, t, 'square', 880, 880, 0.12, 0.05)
      tone(c, out, t + 0.16, 'square', 880, 880, 0.12, 0.05)
      break
    case 'select': tone(c, out, t, 'square', 1175, 1568, 0.08, 0.05); break
  }
}
