<template>
  <div class="relative w-full max-w-4xl mx-auto bg-slate-950 rounded-xl overflow-hidden shadow-2xl border border-slate-800 select-none font-sans">
    <!-- 上部ステータスUI -->
    <div class="absolute top-3 left-4 right-4 flex justify-between items-start pointer-events-none z-10">
      <!-- エリカHP & チャージ状態 -->
      <div class="flex items-center gap-3 bg-slate-900/85 px-4 py-2 rounded-lg border border-slate-700 backdrop-blur-sm">
        <div>
          <div class="flex justify-between items-center gap-4">
            <span class="text-xs font-extrabold text-pink-400 tracking-wider">ERIKA</span>
            <span class="text-xs font-mono text-slate-300">SCORE: {{ score }}</span>
          </div>
          <div class="w-36 h-3 bg-slate-800 rounded overflow-hidden mt-1 border border-slate-600">
            <div class="h-full bg-gradient-to-r from-pink-500 to-rose-400 transition-all duration-150" :style="{ width: `${playerHp}%` }"></div>
          </div>
        </div>
        <div class="px-2.5 py-1 rounded text-xs font-mono font-bold transition-colors"
             :class="chargeLevel === 2 ? 'bg-yellow-400 text-slate-950 animate-pulse' : chargeLevel === 1 ? 'bg-cyan-400 text-slate-950' : 'bg-slate-800 text-slate-400'">
          {{ chargeLevel === 2 ? 'MAX CHARGE!' : chargeLevel === 1 ? 'CHARGING...' : 'BUSTER READY' }}
        </div>
      </div>

      <!-- Cloud Run 通信ステータス ＆ ボスHP -->
      <div class="flex flex-col items-end gap-2">
        <div class="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-900/85 border border-slate-700 text-slate-300">
          Cloud Run API:
          <span :class="apiStatus === 'ONLINE' ? 'text-emerald-400 font-bold' : 'text-amber-400'">{{ apiStatus }}</span>
        </div>

        <div v-if="boss.active" class="bg-slate-900/90 px-4 py-2 rounded-lg border border-red-500/60 text-right">
          <div class="text-xs font-bold text-red-400 tracking-wider">{{ boss.name }}</div>
          <div class="w-44 h-3 bg-slate-800 rounded overflow-hidden mt-1 border border-slate-600">
            <div class="h-full bg-gradient-to-r from-red-600 to-amber-500 transition-all duration-150" :style="{ width: `${(boss.hp / boss.maxHp) * 100}%` }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ボス登場カットイン演出 -->
    <transition name="fade">
      <div v-if="cutin.visible" class="absolute inset-0 bg-black/80 flex items-center justify-center z-20 pointer-events-none">
        <div class="text-center p-6 border-y-2 border-pink-500 bg-slate-900/95 w-full">
          <div class="text-pink-400 text-xs font-mono tracking-widest mb-1">WARNING // BOSS ENCOUNTER</div>
          <div class="text-xl md:text-2xl font-bold text-white mb-2">「{{ cutin.quote }}」</div>
          <div class="text-xs text-slate-400">— {{ cutin.source }}</div>
        </div>
      </div>
    </transition>

    <!-- ステージクリア／ゲームオーバーオーバーレイ -->
    <div v-if="gameResult" class="absolute inset-0 bg-black/75 flex flex-col items-center justify-center z-20">
      <div class="text-4xl font-extrabold mb-2" :class="gameResult === 'CLEAR' ? 'text-yellow-400' : 'text-red-500'">
        {{ gameResult === 'CLEAR' ? 'STAGE CLEAR!!' : 'GAME OVER...' }}
      </div>
      <div class="text-slate-300 font-mono mb-6">FINAL SCORE: {{ score }}</div>
      <button @click="startStageFromCloudRun(currentStage + (gameResult === 'CLEAR' ? 1 : 0))"
              class="px-6 py-2.5 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded-lg shadow-lg transition">
        {{ gameResult === 'CLEAR' ? 'NEXT STAGE (Cloud Run生成)' : 'RETRY STAGE' }}
      </button>
    </div>

    <!-- メインゲームCanvas -->
    <canvas ref="canvasRef" width="800" height="450" class="block w-full h-auto bg-gradient-to-b from-slate-900 via-indigo-950 to-slate-900"></canvas>

    <!-- 操作パネル＆Cloud Runステージ開始ボタン -->
    <div class="bg-slate-900 px-4 py-3 flex flex-wrap justify-between items-center gap-2 text-xs text-slate-300 border-t border-slate-800">
      <div class="flex flex-wrap gap-3">
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">←</kbd> <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">→</kbd> 移動</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Z</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Space</kbd> ジャンプ（敵を踏める！）</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">X</kbd> ギターショット（長押しでチャージ）</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">C</kbd> スライディング</span>
      </div>
      <button @click="startStageFromCloudRun(1)" :disabled="isLoadingStage"
              class="px-4 py-1.5 bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 disabled:opacity-40 text-white font-bold rounded-md shadow transition">
        {{ isLoadingStage ? 'Cloud Run通信中...' : 'STAGE START (敵ウェーブ開始)' }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'

// ★ ご自身の Cloud Run の URL を設定してください
const API_BASE = import.meta.env.VITE_API_URL || 'https://erika-action-api-xxxxxxxxxx-an.a.run.app'

// ==========================================
// 物理・速度パラメータ設定（ここでいつでも微調整可能！）
// ==========================================
const PHYSICS = {
  MOVE_ACCEL: 0.45,       // 左右の加速度（従来の約2/3）
  MOVE_MAX_SPEED: 3.6,    // 左右の最高速度（従来の5.5 → 3.6へ2/3倍に減速）
  FRICTION: 0.82,         // 足を止めた時の滑りにくさ
  JUMP_VELOCITY: -4.8,    // ジャンプ初速（従来の-13.5 → -4.8へ約1/3倍に減速！）
  GRAVITY: 0.075,         // 重力（ジャンプ速度1/3でも同じ高さまでふんわり飛べるよう約1/9に調整）
  SLIDE_SPEED: 7.2,       // スライディング速度（従来の2/3）
  BOUNCE_VELOCITY: -4.4,  // 敵を踏んだ時の跳ね返り速度（1/3倍）
}

const canvasRef = ref<HTMLCanvasElement | null>(null)
const playerHp = ref(100)
const score = ref(0)
const chargeLevel = ref(0)
const apiStatus = ref<'WAKING UP...' | 'ONLINE' | 'LOCAL FALLBACK'>('WAKING UP...')
const isLoadingStage = ref(false)
const currentStage = ref(1)
const gameResult = ref<'CLEAR' | 'GAMEOVER' | null>(null)

const cutin = reactive({ visible: false, quote: '', source: '' })

// スプライト画像の管理（エリカ6枚 ＋ 敵7枚）
const sprites: Record<string, HTMLImageElement> = {}
const spritePaths: Record<string, string> = {
  idle: '/sprites/idle.png',
  run1: '/sprites/run1.png',
  run2: '/sprites/run2.png',
  shoot: '/sprites/shoot.png',
  jump: '/sprites/jump.png',
  jumpShoot: '/sprites/jump_shoot.png',
  soot: '/sprites/enemies/soot.png',
  lime: '/sprites/enemies/lime.png',
  jelly: '/sprites/enemies/jelly.png',
  note_ghost: '/sprites/enemies/note_ghost.png',
  turtle: '/sprites/enemies/turtle.png',
  mole: '/sprites/enemies/mole.png',
  hedgehog: '/sprites/enemies/hedgehog.png',
}

const loadAllSprites = async () => {
  await Promise.all(
    Object.entries(spritePaths).map(([key, src]) => new Promise<void>((resolve) => {
      const img = new Image()
      img.src = src
      img.onload = () => { sprites[key] = img; resolve() }
      img.onerror = () => resolve()
    }))
  )
}

const waitAsync = (ms: number, signal?: AbortSignal) => new Promise<void>((resolve, reject) => {
  const timer = setTimeout(resolve, ms)
  signal?.addEventListener('abort', () => {
    clearTimeout(timer)
    reject(new DOMException('Aborted', 'AbortError'))
  })
})

const GROUND_Y = 370
const player = {
  x: 120,
  y: GROUND_Y,
  vx: 0,
  vy: 0,
  facing: 1 as 1 | -1,
  onGround: true,
  shootPoseTimer: 0,
  isSliding: false,
  invincibleTimer: 0,
  scaleX: 1,
  scaleY: 1,
  runAnimTimer: 0
}

interface Bullet { x: number; y: number; vx: number; radius: number; damage: number; color: string; piercing?: boolean; isEnemy?: boolean }
interface Enemy {
  id: string; type: string; name: string
  x: number; y: number; vx: number; vy: number
  hp: number; maxHp: number; score: number
  stompable: boolean; spiky?: boolean; armored?: boolean; helmet?: boolean
  isHidden?: boolean; isCharging?: boolean; isStunned?: boolean
  baseY: number; abortController: AbortController
}

const bullets: Bullet[] = []
const enemies: Enemy[] = []
const afterimages: { x: number; y: number; facing: number; alpha: number; spriteKey: string }[] = []
let stageAbortController: AbortController | null = null

const boss = reactive({
  active: false, name: '', x: 650, y: GROUND_Y, vy: 0, hp: 100, maxHp: 100,
  state: 'IDLE' as 'IDLE' | 'CHARGING' | 'ATTACK',
  abortController: null as AbortController | null
})

// 万が一APIがブロック・オフラインの時でも7体の敵を生成するローカルフォールバック
const buildFallbackStageData = (stageNum: number) => {
  const catalog = [
    { type: 'soot', name: '煤玉モンスター', hp: 10, speed: 1.4, score: 100, stompable: true },
    { type: 'lime', name: 'ライム豆っこ', hp: 10, speed: 2.0, score: 150, stompable: true },
    { type: 'jelly', name: '桃色ゼリー', hp: 15, speed: 1.3, score: 200, stompable: true },
    { type: 'note_ghost', name: '音符のおばけ', hp: 15, speed: 1.6, score: 250, stompable: true },
    { type: 'turtle', name: 'ずんぐりカメ', hp: 35, speed: 0.8, score: 300, stompable: true, armored: true },
    { type: 'mole', name: '鉱夫モグラ', hp: 20, speed: 0.0, score: 350, stompable: false, helmet: true },
    { type: 'hedgehog', name: '赤いハリネズミ', hp: 25, speed: 4.2, score: 400, stompable: false, spiky: true },
  ]
  const waves = Array.from({ length: 7 }, (_, i) => ({
    id: `local_enemy_${i}`,
    spawn_delay_ms: 800 + i * 2600,
    ...catalog[i % catalog.length]
  }))
  return {
    stage: stageNum,
    enemy_waves: waves,
    boss: {
      boss_name: `SHADOW ERIKA // STAGE ${stageNum}`,
      hp: 120 + stageNum * 30,
      cutin_quote: { quote: '手探りでもただ前に進むしかない。いずれなんとかなるだろってな。', source: '『シャーマンキング』麻倉葉' }
    }
  }
}

const wakeUpCloudRunAsync = async () => {
  try {
    const res = await fetch(`${API_BASE}/api/health`)
    if (res.ok) apiStatus.value = 'ONLINE'
    else apiStatus.value = 'LOCAL FALLBACK'
  } catch {
    apiStatus.value = 'LOCAL FALLBACK'
  }
}

const startStageFromCloudRun = async (stageNum: number) => {
  isLoadingStage.value = true
  gameResult.value = null
  currentStage.value = stageNum
  playerHp.value = 100

  stageAbortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  enemies.length = 0
  bullets.length = 0
  boss.active = false
  boss.abortController?.abort()

  stageAbortController = new AbortController()
  const stageSignal = stageAbortController.signal

  let stageData: any
  try {
    const res = await fetch(`${API_BASE}/api/stage-start?stage=${stageNum}`)
    if (!res.ok) throw new Error('API Error')
    stageData = await res.json()
    apiStatus.value = 'ONLINE'
  } catch {
    // CORSエラーやオフライン時は自動的にローカルデータを使って敵を出す！
    apiStatus.value = 'LOCAL FALLBACK'
    stageData = buildFallbackStageData(stageNum)
  } finally {
    isLoadingStage.value = false
  }

  try {
    const wavePromises = stageData.enemy_waves.map((wave: any) => spawnEnemyWaveAsync(wave, stageSignal))
    await Promise.all(wavePromises)

    while (enemies.length > 0) {
      await waitAsync(500, stageSignal)
    }

    await startBossBattleAsync(stageData.boss, stageSignal)
  } catch {}
}

const spawnEnemyWaveAsync = async (wave: any, stageSignal: AbortSignal) => {
  await waitAsync(wave.spawn_delay_ms, stageSignal)

  const enemyAbort = new AbortController()
  stageSignal.addEventListener('abort', () => enemyAbort.abort())

  const isFlying = wave.type === 'note_ghost'
  const startY = isFlying ? 240 : GROUND_Y

  const enemy: Enemy = {
    id: wave.id,
    type: wave.type,
    name: wave.name,
    x: wave.type === 'mole' ? 500 + Math.random() * 180 : 830,
    y: startY,
    baseY: startY,
    vx: -wave.speed,
    vy: 0,
    hp: wave.hp,
    maxHp: wave.hp,
    score: wave.score,
    stompable: wave.stompable,
    spiky: wave.spiky,
    armored: wave.armored,
    helmet: wave.helmet,
    abortController: enemyAbort
  }
  enemies.push(enemy)

  const { signal } = enemyAbort
  try {
    if (enemy.type === 'hedgehog') {
      while (enemy.hp > 0) {
        enemy.vx = -1.5
        await waitAsync(1400, signal)
        enemy.vx = 0
        enemy.isCharging = true
        await waitAsync(650, signal)
        enemy.isCharging = false
        enemy.vx = -5.5 // ダッシュ速度もマイルドに調整
        await waitAsync(900, signal)
      }
    } else if (enemy.type === 'mole') {
      while (enemy.hp > 0) {
        enemy.isHidden = true
        await waitAsync(1600, signal)
        enemy.isHidden = false
        bullets.push({ x: enemy.x - 24, y: enemy.y - 28, vx: -4.2, radius: 8, damage: 12, color: '#f59e0b', isEnemy: true })
        await waitAsync(1500, signal)
      }
    } else if (enemy.type === 'jelly') {
      while (enemy.hp > 0) {
        // ゼリーのジャンプ速度も1/3に合わせて調整
        if (enemy.y >= GROUND_Y) enemy.vy = -3.8
        await waitAsync(1800, signal)
      }
    } else if (enemy.type === 'note_ghost') {
      while (enemy.hp > 0) {
        await waitAsync(2200, signal)
        bullets.push({ x: enemy.x - 20, y: enemy.y - 30, vx: -3.8, radius: 9, damage: 10, color: '#c084fc', isEnemy: true })
      }
    }
  } catch {}
}

const startBossBattleAsync = async (bossData: any, stageSignal: AbortSignal) => {
  cutin.quote = bossData.cutin_quote.quote
  cutin.source = bossData.cutin_quote.source
  cutin.visible = true
  await waitAsync(2400, stageSignal)
  cutin.visible = false

  boss.name = bossData.boss_name
  boss.maxHp = bossData.hp
  boss.hp = bossData.hp
  boss.x = 660
  boss.y = GROUND_Y
  boss.active = true

  boss.abortController = new AbortController()
  stageSignal.addEventListener('abort', () => boss.abortController?.abort())
  const { signal } = boss.abortController

  try {
    while (boss.active && boss.hp > 0) {
      boss.state = 'IDLE'
      await waitAsync(1300, signal)

      boss.state = 'CHARGING'
      await waitAsync(800, signal)

      boss.state = 'ATTACK'
      for (let i = 0; i < 3; i++) {
        bullets.push({ x: boss.x - 35, y: boss.y - 35 - i * 18, vx: -5.8, radius: 11, damage: 15, color: '#f43f5e', isEnemy: true })
        await waitAsync(260, signal)
      }

      boss.vy = -4.2 // ボスのジャンプもゆったりに調整
      await waitAsync(1600, signal)
    }
  } catch {}
}

let chargeAbort: AbortController | null = null

const startChargeAsync = async () => {
  chargeAbort?.abort()
  chargeAbort = new AbortController()
  try {
    await waitAsync(400, chargeAbort.signal)
    chargeLevel.value = 1
    await waitAsync(800, chargeAbort.signal)
    chargeLevel.value = 2
  } catch {}
}

const fireGuitarWave = (level: number) => {
  player.shootPoseTimer = 18
  const offsetX = player.facing * 42
  const offsetY = -38

  if (level === 0) {
    bullets.push({ x: player.x + offsetX, y: player.y + offsetY, vx: player.facing * 7.5, radius: 6, damage: 10, color: '#f472b6' })
  } else if (level === 1) {
    bullets.push({ x: player.x + offsetX, y: player.y + offsetY, vx: player.facing * 9.5, radius: 14, damage: 25, color: '#38bdf8' })
  } else {
    bullets.push({ x: player.x + offsetX, y: player.y + offsetY, vx: player.facing * 12, radius: 24, damage: 45, color: '#facc15', piercing: true })
    player.vx = -player.facing * 2.5
  }
}

const startSlideAsync = async () => {
  if (!player.onGround || player.isSliding) return
  player.isSliding = true
  player.vx = player.facing * PHYSICS.SLIDE_SPEED
  try {
    await waitAsync(320)
  } finally {
    player.isSliding = false
  }
}

const keys = new Set<string>()
const onKeyDown = (e: KeyboardEvent) => {
  if (['ArrowLeft', 'ArrowRight', 'Space', 'KeyZ', 'KeyX', 'KeyC'].includes(e.code)) e.preventDefault()
  if (keys.has(e.code)) return
  keys.add(e.code)

  if ((e.code === 'Space' || e.code === 'KeyZ') && player.onGround) {
    player.vy = PHYSICS.JUMP_VELOCITY
    player.onGround = false
    player.scaleX = 0.85; player.scaleY = 1.18
  }
  if (e.code === 'KeyX') {
    fireGuitarWave(0)
    startChargeAsync()
  }
  if (e.code === 'KeyC') startSlideAsync()
}

const onKeyUp = (e: KeyboardEvent) => {
  keys.delete(e.code)
  // ジャンプボタンを早く離した時の小ジャンプ減衰
  if ((e.code === 'Space' || e.code === 'KeyZ') && player.vy < -1.5) player.vy *= 0.45
  if (e.code === 'KeyX') {
    if (chargeLevel.value > 0) {
      const lv = chargeLevel.value
      chargeAbort?.abort()
      chargeLevel.value = 0
      fireGuitarWave(lv)
    } else {
      chargeAbort?.abort()
    }
  }
}

let animFrameId = 0
let lastFrameTime = performance.now()

const getPlayerSpriteKey = () => {
  if (!player.onGround) return player.shootPoseTimer > 0 ? 'jumpShoot' : 'jump'
  if (player.shootPoseTimer > 0) return 'shoot'
  if (Math.abs(player.vx) > 0.4) return Math.floor(player.runAnimTimer / 9) % 2 === 0 ? 'run1' : 'run2'
  return 'idle'
}

const damagePlayer = (amount: number) => {
  if (player.invincibleTimer > 0 || gameResult.value) return
  playerHp.value = Math.max(0, playerHp.value - amount)
  player.invincibleTimer = 50
  player.vy = -2.5
  if (playerHp.value <= 0) {
    gameResult.value = 'GAMEOVER'
    stageAbortController?.abort()
  }
}

const updateAndDraw = (now: number) => {
  animFrameId = requestAnimationFrame(updateAndDraw)

  // ★ 120Hz/144Hzモニターでも60FPS相当の速度を保つデルタタイム制御
  const elapsed = now - lastFrameTime
  if (elapsed < 15) return // 約60FPS上限に固定
  lastFrameTime = now

  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')!

  // --- プレイヤー移動（左右2/3速度）＆ジャンプ物理（1/3速度） ---
  if (!player.isSliding) {
    if (keys.has('ArrowLeft')) {
      player.vx = Math.max(player.vx - PHYSICS.MOVE_ACCEL, -PHYSICS.MOVE_MAX_SPEED)
      player.facing = -1
    } else if (keys.has('ArrowRight')) {
      player.vx = Math.min(player.vx + PHYSICS.MOVE_ACCEL, PHYSICS.MOVE_MAX_SPEED)
      player.facing = 1
    } else {
      player.vx *= PHYSICS.FRICTION
    }
  }
  player.x = Math.max(40, Math.min(760, player.x + player.vx))
  player.vy += PHYSICS.GRAVITY
  player.y += player.vy

  if (player.y >= GROUND_Y) {
    if (!player.onGround) { player.scaleX = 1.18; player.scaleY = 0.82 }
    player.y = GROUND_Y; player.vy = 0; player.onGround = true
  }
  player.scaleX += (1 - player.scaleX) * 0.18
  player.scaleY += (1 - player.scaleY) * 0.18
  if (player.shootPoseTimer > 0) player.shootPoseTimer--
  if (player.invincibleTimer > 0) player.invincibleTimer--
  if (Math.abs(player.vx) > 0.4) player.runAnimTimer++

  if (player.isSliding || chargeLevel.value === 2) {
    afterimages.push({ x: player.x, y: player.y, facing: player.facing, alpha: 0.4, spriteKey: getPlayerSpriteKey() })
  }

  // 背景と床の描画
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = '#1e1b4b'
  ctx.fillRect(0, GROUND_Y, canvas.width, canvas.height - GROUND_Y)
  ctx.strokeStyle = '#ec4899'
  ctx.lineWidth = 3
  ctx.beginPath(); ctx.moveTo(0, GROUND_Y); ctx.lineTo(canvas.width, GROUND_Y); ctx.stroke()

  // 残像描画
  for (let i = afterimages.length - 1; i >= 0; i--) {
    const aft = afterimages[i]
    aft.alpha -= 0.05
    if (aft.alpha <= 0) { afterimages.splice(i, 1); continue }
    drawSprite(ctx, sprites[aft.spriteKey], aft.x, aft.y, aft.facing, 96, 1, 1, aft.alpha, true)
  }

  // チャージオーラ描画
  if (chargeLevel.value > 0) {
    ctx.save()
    ctx.beginPath()
    const r = chargeLevel.value === 2 ? 48 + Math.sin(Date.now() * 0.03) * 6 : 36
    ctx.arc(player.x, player.y - 42, r, 0, Math.PI * 2)
    ctx.fillStyle = chargeLevel.value === 2 ? 'rgba(250, 204, 21, 0.28)' : 'rgba(56, 189, 248, 0.22)'
    ctx.fill()
    ctx.strokeStyle = chargeLevel.value === 2 ? '#facc15' : '#38bdf8'
    ctx.stroke()
    ctx.restore()
  }

  // エリカ描画
  if (player.invincibleTimer % 4 < 2) {
    const slideY = player.isSliding ? 0.72 : player.scaleY
    drawSprite(ctx, sprites[getPlayerSpriteKey()], player.x, player.y, player.facing, 96, player.scaleX, slideY, 1.0, false)
  }

  // --- 敵キャラ7種の更新・描画・マリオ踏み判定 ---
  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i]
    if (!e.isStunned) e.x += e.vx

    if (e.type === 'note_ghost') {
      e.y = e.baseY + Math.sin(Date.now() * 0.004 + i) * 32
    } else if (e.type !== 'mole') {
      e.vy += PHYSICS.GRAVITY
      e.y = Math.min(GROUND_Y, e.y + e.vy)
      if (e.y >= GROUND_Y) e.vy = 0
    }

    const shakeX = e.isCharging ? (Math.random() - 0.5) * 8 : 0
    const moleScaleY = e.isHidden ? 0.45 : 1.0
    const stunFlipY = e.isStunned ? -0.8 : moleScaleY
    drawSprite(ctx, sprites[e.type], e.x + shakeX, e.y, 1, 76, 1, stunFlipY, 1.0, false)

    // プレイヤーとの接触判定（マリオ踏み vs トゲ・体当たり）
    if (Math.abs(player.x - e.x) < 38 && Math.abs(player.y - e.y) < 42) {
      if (player.vy > 0 && player.y < e.y - 12) {
        if (e.spiky) {
          damagePlayer(15)
        } else if (e.stompable) {
          player.vy = PHYSICS.BOUNCE_VELOCITY
          player.scaleX = 1.22; player.scaleY = 0.78
          e.hp -= 20
          if (e.type === 'turtle' && e.hp > 0) e.isStunned = true
          if (e.hp <= 0) {
            score.value += e.score
            e.abortController.abort()
            enemies.splice(i, 1)
            continue
          }
        }
      } else if (!player.isSliding) {
        damagePlayer(12)
      }
    }

    if (e.x < -80) {
      e.abortController.abort()
      enemies.splice(i, 1)
    }
  }

  // --- ボスの更新＆描画 ---
  if (boss.active) {
    boss.vy += PHYSICS.GRAVITY
    boss.y = Math.min(GROUND_Y, boss.y + boss.vy)
    if (boss.y >= GROUND_Y) boss.vy = 0
    drawSprite(ctx, sprites['shoot'], boss.x, boss.y, -1, 108, 1, 1, 0.95, true)
  }

  // --- 弾の更新＆当たり判定 ---
  for (let i = bullets.length - 1; i >= 0; i--) {
    const b = bullets[i]
    b.x += b.vx

    ctx.save()
    ctx.beginPath()
    ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2)
    ctx.fillStyle = b.color
    ctx.shadowColor = b.color; ctx.shadowBlur = 10
    ctx.fill()
    ctx.restore()

    if (b.isEnemy) {
      if (Math.abs(b.x - player.x) < 24 && Math.abs(b.y - (player.y - 36)) < 32) {
        damagePlayer(b.damage)
        bullets.splice(i, 1)
        continue
      }
    } else {
      let hit = false
      for (let j = enemies.length - 1; j >= 0; j--) {
        const e = enemies[j]
        if (Math.abs(b.x - e.x) < 34 && Math.abs(b.y - (e.y - 32)) < 36) {
          if (e.isHidden && !b.piercing) {
            b.vx = -b.vx * 0.8; b.y -= 4
            break
          }
          const dmg = (e.armored && !b.piercing && !e.isStunned) ? Math.ceil(b.damage * 0.4) : b.damage
          e.hp -= dmg
          hit = true
          if (e.hp <= 0) {
            score.value += e.score
            e.abortController.abort()
            enemies.splice(j, 1)
          }
          if (!b.piercing) break
        }
      }
      if (hit && !b.piercing) { bullets.splice(i, 1); continue }

      if (boss.active && Math.abs(b.x - boss.x) < 40 && Math.abs(b.y - (boss.y - 45)) < 48) {
        boss.hp = Math.max(0, boss.hp - b.damage)
        if (!b.piercing) bullets.splice(i, 1)
        if (boss.hp <= 0) {
          boss.active = false
          boss.abortController?.abort()
          score.value += 1000
          gameResult.value = 'CLEAR'
        }
        continue
      }
    }

    if (b.x < -60 || b.x > canvas.width + 60) bullets.splice(i, 1)
  }
}

const drawSprite = (
  ctx: CanvasRenderingContext2D, img: HTMLImageElement | undefined,
  x: number, y: number, facing: number, size: number,
  scaleX: number, scaleY: number, alpha: number, tintShadow: boolean
) => {
  ctx.save()
  ctx.globalAlpha = alpha
  ctx.translate(x, y)
  ctx.scale(facing * scaleX, scaleY)
  if (img && img.complete && img.naturalWidth > 0) {
    if (tintShadow) ctx.filter = 'hue-rotate(190deg) brightness(1.25)'
    ctx.drawImage(img, -size / 2, -size + 6, size, size)
  } else {
    ctx.fillStyle = tintShadow ? '#38bdf8' : '#ec4899'
    ctx.fillRect(-size / 3, -size * 0.8, (size * 2) / 3, size * 0.8)
  }
  ctx.restore()
}

onMounted(async () => {
  await Promise.all([loadAllSprites(), wakeUpCloudRunAsync()])
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  lastFrameTime = performance.now()
  animFrameId = requestAnimationFrame(updateAndDraw)
  // ★ 画面を開いたら自動でステージ1の敵ウェーブを開始！
  startStageFromCloudRun(1)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  cancelAnimationFrame(animFrameId)
  stageAbortController?.abort()
  chargeAbort?.abort()
})
</script>