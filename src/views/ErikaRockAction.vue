<template>
  <div class="relative w-full max-w-4xl mx-auto bg-slate-950 rounded-xl overflow-hidden shadow-2xl border border-slate-800 select-none font-sans">
    <!-- 上部ステータスUI -->
    <div class="absolute top-3 left-4 right-4 flex justify-between items-start pointer-events-none z-10">
      <div class="flex flex-col gap-1.5 bg-slate-900/90 px-4 py-2.5 rounded-lg border border-slate-700 backdrop-blur-sm shadow-lg">
        <!-- 残機 & スコア & ステージ進行度 -->
        <div class="flex items-center gap-4 text-xs">
          <span class="font-extrabold text-pink-400 tracking-wider">STAGE {{ currentStage }}</span>
          <span class="font-bold text-rose-400 flex items-center gap-1">
            ERIKA <span v-for="n in lives" :key="n" class="text-sm">♥</span>
          </span>
          <span class="font-mono text-slate-300">SCORE: {{ score }}</span>
        </div>

        <!-- HPゲージ ＆ チャージ表示 -->
        <div class="flex items-center gap-3">
          <div>
            <div class="flex justify-between text-[11px] font-mono text-slate-200 mb-0.5">
              <span>HP</span>
              <span class="font-bold">{{ playerHp }} / {{ maxHp }}</span>
            </div>
            <div class="w-40 h-3.5 bg-slate-800 rounded overflow-hidden border border-slate-600">
              <div class="h-full bg-gradient-to-r from-pink-500 via-rose-400 to-emerald-400 transition-all duration-150"
                   :style="{ width: `${Math.min(100, (playerHp / maxHp) * 100)}%` }"></div>
            </div>
          </div>

          <div class="px-2.5 py-1 rounded text-xs font-mono font-bold transition-colors"
               :class="chargeLevel === 3 ? 'bg-gradient-to-r from-pink-500 via-yellow-400 to-cyan-400 text-slate-950 animate-pulse' :
                       chargeLevel === 2 ? 'bg-yellow-400 text-slate-950 animate-pulse' :
                       chargeLevel === 1 ? 'bg-cyan-400 text-slate-950' : 'bg-slate-800 text-slate-400'">
            {{ chargeLevel === 3 ? 'FINAL CHARGE!!' : chargeLevel === 2 ? 'LV.2 PIERCE!' : chargeLevel === 1 ? 'LV.1 CHARGE' : 'NOTE BUSTER' }}
          </div>
        </div>

        <!-- グラディウス風・装備一覧 -->
        <div class="flex flex-wrap gap-1.5 mt-0.5 text-[10px] font-mono">
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.doubleShot ? 'bg-pink-600 text-white font-bold' : 'bg-slate-800 text-slate-500'">2-WAY</span>
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.groundShot ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-500'">GROUND</span>
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.options > 0 ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-500'">OPTION×{{ upgrades.options }}</span>
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.barrierHp > 0 ? 'bg-blue-500 text-white font-bold' : 'bg-slate-800 text-slate-500'">BARRIER:{{ upgrades.barrierHp }}</span>
          <span class="px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400">ATK×{{ upgrades.powerMultiplier.toFixed(2) }}</span>
        </div>
      </div>

      <!-- 右上：道中進行度ゲージ ＆ ボスHP（8倍耐久！） -->
      <div class="flex flex-col items-end gap-2">
        <div class="bg-slate-900/90 px-3 py-1.5 rounded-lg border border-slate-700 text-right">
          <div class="text-[10px] font-mono text-slate-400 flex justify-between gap-4">
            <span>STAGE PROGRESS</span>
            <span class="text-cyan-400 font-bold">{{ Math.min(100, Math.floor(stageProgress)) }}%</span>
          </div>
          <div class="w-40 h-2 bg-slate-800 rounded overflow-hidden mt-1">
            <div class="h-full bg-gradient-to-r from-cyan-500 to-pink-500 transition-all duration-150"
                 :style="{ width: `${Math.min(100, stageProgress)}%` }"></div>
          </div>
        </div>

        <div v-if="boss.active" class="bg-slate-900/95 px-4 py-2.5 rounded-lg border-2 border-red-500/80 text-right shadow-xl">
          <div class="text-xs font-extrabold text-red-400 tracking-wider">{{ boss.name }}</div>
          <div class="text-xs font-mono text-amber-300 font-bold">HP: {{ boss.hp }} / {{ boss.maxHp }}</div>
          <div class="w-48 h-3.5 bg-slate-800 rounded overflow-hidden mt-1 border border-slate-600">
            <div class="h-full bg-gradient-to-r from-red-600 via-orange-500 to-yellow-400 transition-all duration-100"
                 :style="{ width: `${(boss.hp / boss.maxHp) * 100}%` }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ボス登場カットイン演出 -->
    <transition name="fade">
      <div v-if="cutin.visible" class="absolute inset-0 bg-black/80 flex items-center justify-center z-20 pointer-events-none">
        <div class="text-center p-6 border-y-2 border-pink-500 bg-slate-900/95 w-full">
          <div class="text-pink-400 text-xs font-mono tracking-widest mb-1">WARNING // {{ cutin.bossName }}</div>
          <div class="text-xl md:text-2xl font-bold text-white mb-2">「{{ cutin.quote }}」</div>
          <div class="text-xs text-slate-400">— {{ cutin.source }}</div>
        </div>
      </div>
    </transition>

    <!-- ステージクリアボーナス選択画面 -->
    <div v-if="gameResult === 'CLEAR'" class="absolute inset-0 bg-slate-950/90 flex flex-col items-center justify-center z-20 p-6">
      <div class="text-yellow-400 text-xs font-mono tracking-widest mb-1">STAGE {{ currentStage }} CLEAR BONUS!!</div>
      <div class="text-2xl md:text-3xl font-extrabold text-white mb-4">パワーアップ武装を1つ選択してください</div>

      <div class="grid grid-cols-2 md:grid-cols-3 gap-3 w-full max-w-2xl mb-4">
        <button v-for="item in bonusChoices" :key="item.id"
                @click="selectBonusAndNextStage(item.id)"
                class="flex flex-col items-start p-3 rounded-lg border border-slate-700 bg-slate-900 hover:bg-pink-950/60 hover:border-pink-500 transition text-left group">
          <div class="text-sm font-bold text-pink-400 group-hover:text-yellow-300">{{ item.title }}</div>
          <div class="text-xs text-slate-300 mt-1">{{ item.desc }}</div>
        </button>
      </div>
    </div>

    <!-- ゲームオーバー画面 -->
    <div v-if="gameResult === 'GAMEOVER'" class="absolute inset-0 bg-black/85 flex flex-col items-center justify-center z-20">
      <div class="text-4xl font-extrabold text-red-500 mb-2">GAME OVER</div>
      <div class="text-slate-300 font-mono mb-6">FINAL SCORE: {{ score }} (STAGE {{ currentStage }})</div>
      <button @click="resetFullGame"
              class="px-6 py-2.5 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded-lg shadow-lg transition">
        STAGE 1 から再挑戦する
      </button>
    </div>

    <!-- メインゲームCanvas -->
    <canvas ref="canvasRef" width="800" height="450" class="block w-full h-auto"></canvas>

    <!-- 下部操作ガイド -->
    <div class="bg-slate-900 px-4 py-3 flex flex-wrap justify-between items-center gap-2 text-xs text-slate-300 border-t border-slate-800">
      <div class="flex flex-wrap gap-3">
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">←</kbd> <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">→</kbd> 移動</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Z</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Space</kbd> ジャンプ（穴・壁越え・踏みつけ）</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">X</kbd> 音符ショット（Lv.2以上で壁貫通！）</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">C</kbd> スライディング</span>
      </div>
      <button @click="resetFullGame" :disabled="isLoadingStage"
              class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-600 transition">
        最初からリスタート
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'

// ★ ご自身の Cloud Run URL
const API_BASE = import.meta.env.VITE_API_URL || 'https://erika-action-api-xxxxxxxxxx-an.a.run.app'

const PHYSICS = {
  MOVE_ACCEL: 0.45,
  MOVE_MAX_SPEED: 3.6,
  FRICTION: 0.82,
  JUMP_VELOCITY: -4.8,
  GRAVITY: 0.075,
  SLIDE_SPEED: 7.0,
  BOUNCE_VELOCITY: -4.4,
}

const canvasRef = ref<HTMLCanvasElement | null>(null)
const maxHp = ref(100)
const playerHp = ref(100)
const lives = ref(3)
const score = ref(0)
const chargeLevel = ref(0)
const isLoadingStage = ref(false)
const currentStage = ref(1)
const stageProgress = ref(0) // 0〜100%（100%で強制スクロール停止＆ボス出現！）
const gameResult = ref<'CLEAR' | 'GAMEOVER' | null>(null)

const upgrades = reactive({
  doubleShot: false,
  groundShot: false,
  options: 0,
  barrierHp: 0,
  powerMultiplier: 1.0,
  maxChargeLevel: 2,
})

const bonusChoices = computed(() => [
  { id: 'DOUBLE',  title: '🎵 2方向デュアルショット', desc: upgrades.doubleShot ? '取得済（選ぶと攻撃力+20%）' : '前方と斜め上45度へ同時に音符弾を発射！' },
  { id: 'GROUND',  title: '🔊 グランド・リップル弾', desc: upgrades.groundShot ? '取得済（選ぶと攻撃力+20%）' : '地面や壁の上を這う重低音レーザーを追加発射！' },
  { id: 'OPTION',  title: `🛰️ サウンド・オプション (${upgrades.options}/2)`, desc: 'エリカの後ろを追従し、同時に音符を撃つスピーカーを追加！' },
  { id: 'BARRIER', title: '🛡️ 音響フォースバリア', desc: '敵の弾や体当たりを3回まで無効化するバリアを展開！' },
  { id: 'CHARGE3', title: '⚡ ファイナルチャージ解放 (Lv.3)', desc: upgrades.maxChargeLevel >= 3 ? '取得済（選ぶと攻撃力+25%）' : '壁も貫通する3段階目の極太サウンドブラスター解放！' },
  { id: 'VITAL',   title: '💖 最大HP+30 ＆ 全回復 ＆ 1UP', desc: '最大体力を増やし、HP全回復＋残機を1つ増やす！' },
])

const cutin = reactive({ visible: false, bossName: '', quote: '', source: '' })

// マスタデータ（敵HP約2倍・6人のちびエリカボスHP約8倍！）
let masterData: any = {
  quotes: [
    { quote: '手探りでもただ前に進むしかない。いずれなんとかなるだろってな。', source: '『シャーマンキング』麻倉葉' },
    { quote: 'お前が信じる、お前を信じろ！', source: '『天元突破グレンラガン』カミナ' },
    { quote: '覚悟とは！！暗闇の荒野に！！進むべき道を切り開く事だッ！', source: '『ジョジョの奇妙な冒険 第5部』ジョルノ' },
  ],
  enemies: [
    { type: 'soot',       name: '煤玉モンスター', sprite: '/sprites/enemies/soot.png',       hp: 22, speed: 1.3, score: 100, stompable: true,  wallAction: 'bounce' },
    { type: 'lime',       name: 'ライム豆っこ',   sprite: '/sprites/enemies/lime.png',       hp: 25, speed: 1.8, score: 150, stompable: true,  wallAction: 'jump' },
    { type: 'jelly',      name: '桃色ゼリー',     sprite: '/sprites/enemies/jelly.png',      hp: 35, speed: 1.2, score: 200, stompable: true,  wallAction: 'jump' },
    { type: 'note_ghost', name: '音符のおばけ',   sprite: '/sprites/enemies/note_ghost.png', hp: 30, speed: 1.5, score: 250, stompable: true,  wallAction: 'fly' },
    { type: 'turtle',     name: 'ずんぐりカメ',   sprite: '/sprites/enemies/turtle.png',     hp: 65, speed: 0.8, score: 300, stompable: true,  armored: true, wallAction: 'bounce' },
    { type: 'mole',       name: '鉱夫モグラ',     sprite: '/sprites/enemies/mole.png',       hp: 45, speed: 0.0, score: 350, stompable: false, helmet: true,  wallAction: 'stay' },
    { type: 'hedgehog',   name: '赤いハリネズミ', sprite: '/sprites/enemies/hedgehog.png',   hp: 55, speed: 3.8, score: 400, stompable: false, spiky: true,   wallAction: 'jump' },
  ],
  bosses: [
    { id: 'knight',    name: 'BLACK KNIGHT ERIKA', sprite: '/sprites/bosses/boss_knight.png',    baseHp: 1200, scale: 1.25, pattern: 'KNIGHT' },
    { id: 'concierge', name: 'KEY MASTER ERIKA',   sprite: '/sprites/bosses/boss_concierge.png', baseHp: 1100, scale: 1.25, pattern: 'CONCIERGE' },
    { id: 'yukata',    name: 'SUNFLOWER YUKATA',   sprite: '/sprites/bosses/boss_yukata.png',    baseHp: 1150, scale: 1.25, pattern: 'YUKATA' },
    { id: 'kimono',    name: 'GRIMOIRE KIMONO',    sprite: '/sprites/bosses/boss_kimono.png',    baseHp: 1250, scale: 1.25, pattern: 'KIMONO' },
    { id: 'dress',     name: 'NAVY DRESS DIVA',    sprite: '/sprites/bosses/boss_dress.png',     baseHp: 1350, scale: 1.28, pattern: 'DRESS' },
    { id: 'queen',     name: 'PEARL THRONE QUEEN', sprite: '/sprites/bosses/boss_queen.png',     baseHp: 1600, scale: 1.35, pattern: 'QUEEN' },
  ],
  stages: [
    { stage: 1, skyGradient: ['#0f172a', '#311042', '#701a75'], groundColor: '#1e1b4b', lineColor: '#ec4899', scrollSpeed: 1.45 },
    { stage: 2, skyGradient: ['#020617', '#0f2942', '#065f46'], groundColor: '#064e3b', lineColor: '#34d399', scrollSpeed: 1.7 },
    { stage: 3, skyGradient: ['#180404', '#450a0a', '#7c2d12'], groundColor: '#270909', lineColor: '#f97316', scrollSpeed: 1.95 },
  ]
}

const loadMasterJsonAsync = async () => {
  try {
    const res = await fetch('/assets/game-master.json')
    if (res.ok) masterData = await res.json()
  } catch {}
}

const sprites: Record<string, HTMLImageElement> = {}
const loadAllSprites = async () => {
  const paths: Record<string, string> = {
    idle: '/sprites/idle.png', run1: '/sprites/run1.png', run2: '/sprites/run2.png',
    shoot: '/sprites/shoot.png', jump: '/sprites/jump.png', jumpShoot: '/sprites/jump_shoot.png',
  }
  masterData.enemies.forEach((e: any) => { paths[e.type] = e.sprite })
  masterData.bosses.forEach((b: any) => { paths[`boss_${b.id}`] = b.sprite })

  await Promise.all(
    Object.entries(paths).map(([key, src]) => new Promise<void>((resolve) => {
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
  x: 140, y: GROUND_Y, vx: 0, vy: 0, facing: 1 as 1 | -1,
  onGround: true, shootPoseTimer: 0, isSliding: false, invincibleTimer: 0,
  scaleX: 1, scaleY: 1, runAnimTimer: 0
}
const positionHistory: { x: number; y: number }[] = []

// ★ 右端から流れてくるステージギミック（壁・空中床・落とし穴）
interface Obstacle { x: number; y: number; w: number; h: number; type: 'wall' | 'platform' }
interface Pit { x: number; w: number } // 地面の落とし穴
const obstacles = ref<Obstacle[]>([])
const pits = ref<Pit[]>([])

const currentTheme = reactive({
  skyGradient: ['#0f172a', '#311042', '#701a75'],
  groundColor: '#1e1b4b',
  lineColor: '#ec4899',
  scrollSpeed: 1.45,
  enemyHue: 0,
  isScrolling: true,
})

interface Bullet {
  x: number; y: number; vx: number; vy: number
  radius: number; damage: number; color: string
  noteSymbol: string; piercing?: boolean; isGroundCrawling?: boolean; isEnemy?: boolean
}
interface DropItem { x: number; y: number; vy: number; type: 'HEAL' | '1UP' | 'SCORE'; lifeTimer: number }
interface Enemy {
  id: string; type: string; name: string
  x: number; y: number; vx: number; vy: number
  hp: number; maxHp: number; score: number
  stompable: boolean; spiky?: boolean; armored?: boolean; helmet?: boolean
  wallAction: 'jump' | 'bounce' | 'fly' | 'stay'
  isHidden?: boolean; isCharging?: boolean; isStunned?: boolean
  hueRotate: number; baseY: number; abortController: AbortController
}

const bullets: Bullet[] = []
const dropItems: DropItem[] = []
const enemies: Enemy[] = []
const afterimages: { x: number; y: number; facing: number; alpha: number; spriteKey: string }[] = []
let stageAbortController: AbortController | null = null

const boss = reactive({
  active: false, id: 'knight', name: '', spriteKey: 'boss_knight',
  x: 660, y: GROUND_Y, vx: 0, vy: 0,
  hp: 1200, maxHp: 1200, scale: 1.25, pattern: 'KNIGHT',
  isFloating: false, warningLaserY: null as number | null,
  abortController: null as AbortController | null
})

const bgStars = Array.from({ length: 35 }, () => ({
  x: Math.random() * 800, y: Math.random() * 260, size: Math.random() * 2 + 1, speed: Math.random() * 0.3 + 0.1
}))
const bgBuildings = Array.from({ length: 16 }, (_, i) => ({
  x: i * 55, w: 42, h: 60 + (i * 37) % 110
}))
let bgScrollX = 0

// ====================================================
// 右端からギミック（落とし穴＋空中床、高い壁＋ステップ）を生み出す非同期ジェネレーター
// ====================================================
const runGimmickSpawnerAsync = async (stageSignal: AbortSignal) => {
  try {
    while (currentTheme.isScrolling && stageProgress.value < 92) {
      const roll = Math.random()
      const spawnX = 840

      if (roll < 0.32) {
        // パターンA：【広い落とし穴 ＋ その上に乗れる空中床】（空中床を渡らないと落ちる！）
        const pitWidth = 135 + Math.random() * 45
        pits.value.push({ x: spawnX, w: pitWidth })
        obstacles.value.push({ x: spawnX + 20, y: 275, w: pitWidth - 30, h: 16, type: 'platform' })
      } else if (roll < 0.60) {
        // パターンB：【ジャンプで飛び越えるアンプ壁】
        const wallH = 50 + Math.random() * 25
        obstacles.value.push({ x: spawnX, y: GROUND_Y - wallH, w: 46, h: wallH, type: 'wall' })
      } else if (roll < 0.82) {
        // パターンC：【直接ジャンプでは越えられない高い壁 ＋ 手前の空中ステップ床】
        obstacles.value.push({ x: spawnX - 95, y: 285, w: 75, h: 16, type: 'platform' })
        obstacles.value.push({ x: spawnX, y: GROUND_Y - 115, w: 48, h: 115, type: 'wall' })
      } else {
        // パターンD：【2段の空中足場 ＋ 下に小落とし穴】
        pits.value.push({ x: spawnX + 20, w: 95 })
        obstacles.value.push({ x: spawnX, y: 290, w: 85, h: 16, type: 'platform' })
        obstacles.value.push({ x: spawnX + 100, y: 225, w: 90, h: 16, type: 'platform' })
      }

      await waitAsync(2400, stageSignal)
    }
  } catch {}
}

// ステージ開始制御
const startStageFromCloudRun = async (stageNum: number) => {
  isLoadingStage.value = true
  gameResult.value = null
  currentStage.value = stageNum
  stageProgress.value = 0

  stageAbortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  enemies.length = 0; bullets.length = 0; dropItems.length = 0
  obstacles.value = []; pits.value = []
  boss.active = false; boss.warningLaserY = null
  boss.abortController?.abort()

  const stg = masterData.stages[(stageNum - 1) % masterData.stages.length]
  currentTheme.skyGradient = stg.skyGradient
  currentTheme.groundColor = stg.groundColor
  currentTheme.lineColor = stg.lineColor
  currentTheme.scrollSpeed = stg.scrollSpeed + (stageNum - 1) * 0.12
  currentTheme.enemyHue = (stageNum - 1) * 55
  currentTheme.isScrolling = true

  player.x = 140; player.y = GROUND_Y; player.vx = 0; player.vy = 0

  stageAbortController = new AbortController()
  const stageSignal = stageAbortController.signal

  try {
    await fetch(`${API_BASE}/api/stage-start?stage=${stageNum}`)
  } catch {} finally {
    isLoadingStage.value = false
  }

  // ギミック生成タスクを非同期起動
  runGimmickSpawnerAsync(stageSignal)

  // 敵の耐久力をステージ進行に合わせてさらに強化
  const hpMul = 1 + (stageNum - 1) * 0.3
  const spdMul = 1 + Math.min(0.6, (stageNum - 1) * 0.08)

  try {
    // 進行度が100%になるまで右端から敵を送り込む
    let count = 0
    while (stageProgress.value < 95) {
      const tmpl = masterData.enemies[(count + stageNum) % masterData.enemies.length]
      spawnSingleEnemy({
        id: `stg${stageNum}_e${count}`,
        ...tmpl,
        hp: Math.round(tmpl.hp * hpMul),
        speed: tmpl.speed * spdMul
      }, stageSignal)
      count++
      stageProgress.value = Math.min(100, stageProgress.value + 11)
      await waitAsync(Math.max(1600, 2600 - stageNum * 140), stageSignal)
    }

    stageProgress.value = 100
    // ボス部屋到達！スクロールを止めて残りの雑魚がいなくなるのを少し待つ
    await waitAsync(1500, stageSignal)
    currentTheme.isScrolling = false
    pits.value = [] // ボス戦中は落とし穴を塞ぐ

    const bossTmpl = masterData.bosses[(stageNum - 1) % masterData.bosses.length]
    const quoteObj = masterData.quotes[(stageNum - 1) % masterData.quotes.length]

    await startBossBattleAsync({
      ...bossTmpl,
      hp: Math.round(bossTmpl.baseHp * (1 + (stageNum - 1) * 0.25)),
      cutin_quote: quoteObj
    }, stageSignal)
  } catch {}
}

const spawnSingleEnemy = (wave: any, stageSignal: AbortSignal) => {
  const enemyAbort = new AbortController()
  stageSignal.addEventListener('abort', () => enemyAbort.abort())

  const isFlying = wave.type === 'note_ghost'
  const startY = isFlying ? 200 : GROUND_Y

  const enemy: Enemy = {
    id: wave.id, type: wave.type, name: wave.name,
    x: 830, y: startY, baseY: startY,
    vx: -wave.speed, vy: 0,
    hp: wave.hp, maxHp: wave.hp, score: wave.score,
    stompable: wave.stompable, spiky: wave.spiky, armored: wave.armored, helmet: wave.helmet,
    wallAction: wave.wallAction || 'jump',
    hueRotate: currentTheme.enemyHue,
    abortController: enemyAbort
  }
  enemies.push(enemy)

  const { signal } = enemyAbort
  ;(async () => {
    try {
      if (enemy.type === 'hedgehog') {
        while (enemy.hp > 0) {
          enemy.vx = -1.4
          await waitAsync(1300, signal)
          enemy.vx = 0; enemy.isCharging = true
          await waitAsync(550, signal)
          enemy.isCharging = false
          // エリカがいる向きへ高速スピンダッシュ！
          enemy.vx = player.x < enemy.x ? -5.2 : 4.5
          await waitAsync(900, signal)
        }
      } else if (enemy.type === 'mole') {
        while (enemy.hp > 0) {
          enemy.isHidden = true
          await waitAsync(1400, signal)
          enemy.isHidden = false
          const dir = player.x < enemy.x ? -1 : 1
          bullets.push({ x: enemy.x + dir * 20, y: enemy.y - 26, vx: dir * 4.5, vy: 0, radius: 8, damage: 14, color: '#f59e0b', noteSymbol: '●', isEnemy: true })
          await waitAsync(1300, signal)
        }
      } else if (enemy.type === 'jelly') {
        while (enemy.hp > 0) {
          if (enemy.vy === 0) enemy.vy = -3.9
          await waitAsync(1500, signal)
        }
      } else if (enemy.type === 'note_ghost') {
        while (enemy.hp > 0) {
          await waitAsync(1900, signal)
          // エリカの位置を狙って音符弾を発射！
          const dx = player.x - enemy.x
          const dy = (player.y - 35) - (enemy.y - 25)
          const dist = Math.hypot(dx, dy) || 1
          bullets.push({
            x: enemy.x - 15, y: enemy.y - 25,
            vx: (dx / dist) * 4.2, vy: (dy / dist) * 4.2,
            radius: 9, damage: 12, color: '#c084fc', noteSymbol: '♪', isEnemy: true
          })
        }
      }
    } catch {}
  })()
}

// ====================================================
// ★ 6人の「ちびエリカ・ボス」専用ガチバトルAIルーチン
// ====================================================
const fireAimedShot = (fromX: number, fromY: number, speed: number, color: string, symbol = '♪', spreadRad = 0) => {
  const dx = player.x - fromX
  const dy = (player.y - 36) - fromY
  const baseAngle = Math.atan2(dy, dx) + spreadRad
  bullets.push({
    x: fromX, y: fromY,
    vx: Math.cos(baseAngle) * speed, vy: Math.sin(baseAngle) * speed,
    radius: 11, damage: 16, color, noteSymbol: symbol, isEnemy: true
  })
}

const startBossBattleAsync = async (bossData: any, stageSignal: AbortSignal) => {
  // ボス戦では壁だけ消して空中床は残す（ボス攻撃をかわす足場として活用！）
  obstacles.value = obstacles.value.filter(o => o.type === 'platform')

  cutin.bossName = `${bossData.name} // STAGE ${currentStage.value}`
  cutin.quote = bossData.cutin_quote.quote
  cutin.source = bossData.cutin_quote.source
  cutin.visible = true
  await waitAsync(2400, stageSignal)
  cutin.visible = false

  boss.id = bossData.id
  boss.name = bossData.name
  boss.spriteKey = `boss_${bossData.id}`
  boss.maxHp = bossData.hp
  boss.hp = bossData.hp
  boss.scale = bossData.scale
  boss.pattern = bossData.pattern
  boss.x = 650; boss.y = GROUND_Y; boss.vx = 0; boss.vy = 0
  boss.isFloating = false; boss.warningLaserY = null
  boss.active = true

  boss.abortController = new AbortController()
  stageSignal.addEventListener('abort', () => boss.abortController?.abort())
  const { signal } = boss.abortController

  try {
    while (boss.active && boss.hp > 0) {
      if (boss.pattern === 'KNIGHT') {
        // ⚔️ 【1. 黒鎧剣士エリカ】高速斬撃ダッシュ ＆ 地面を這う剣気波＋自機狙い
        boss.vx = 0
        for (let i = 0; i < 2; i++) {
          bullets.push({ x: boss.x - 30, y: GROUND_Y - 12, vx: -6.2, vy: 0, radius: 14, damage: 18, color: '#ef4444', noteSymbol: '⚔', isGroundCrawling: true, isEnemy: true })
          fireAimedShot(boss.x - 25, boss.y - 45, 5.2, '#f87171', '♪')
          await waitAsync(450, signal)
        }
        // エリカへ向かってジャンプ斬り突進！
        boss.vy = -4.2
        boss.vx = player.x < boss.x ? -6.2 : 6.2
        await waitAsync(950, signal)
        boss.vx = 0
        await waitAsync(600, signal)

      } else if (boss.pattern === 'CONCIERGE') {
        // 🗝️ 【2. コンシェルジュエリカ】瞬間移動ワープ ＆ 5連ロックオン狙撃
        const warpSpots = [660, 220, 440, 580]
        boss.x = warpSpots[Math.floor(Math.random() * warpSpots.length)]
        boss.vy = -3.2
        await waitAsync(450, signal)
        for (let i = 0; i < 5; i++) {
          fireAimedShot(boss.x, boss.y - 42, 6.0, '#facc15', '🗝')
          await waitAsync(180, signal)
        }
        await waitAsync(850, signal)

      } else if (boss.pattern === 'YUKATA') {
        // 🌻 【3. ひまわり浴衣エリカ】大ジャンプ花火拡散弾 ＆ ステップ移動
        boss.vy = -5.1
        boss.vx = player.x < boss.x ? -3.0 : 3.0
        await waitAsync(650, signal)
        boss.vx = 0
        // 空中頂点で7方向のひまわり花火弾幕を展開！
        for (let a = -3; a <= 3; a++) {
          fireAimedShot(boss.x, boss.y - 40, 4.6, '#fbbf24', '✿', a * 0.24)
        }
        await waitAsync(1100, signal)

      } else if (boss.pattern === 'KIMONO') {
        // 📖 【4. 古書着物エリカ】高さ3段の時間差結界弾 ＆ 使い魔モンスター召喚！
        const heights = [GROUND_Y - 18, GROUND_Y - 65, GROUND_Y - 120]
        for (const h of heights) {
          const dir = player.x < boss.x ? -1 : 1
          bullets.push({ x: boss.x + dir * 25, y: h, vx: dir * 6.5, vy: 0, radius: 13, damage: 16, color: '#a855f7', noteSymbol: '۞', isEnemy: true })
          await waitAsync(280, signal)
        }
        // 画面内の雑魚が1体以下なら古書から使い魔を召喚！
        if (enemies.length < 2) {
          const summonTmpl = masterData.enemies[Math.floor(Math.random() * 3)]
          spawnSingleEnemy({ ...summonTmpl, id: `summon_${Date.now()}` }, signal)
        }
        boss.vy = -3.8
        boss.vx = boss.x > 450 ? -3.5 : 3.5
        await waitAsync(900, signal)
        boss.vx = 0

      } else if (boss.pattern === 'DRESS') {
        // 👗 【5. ネイビードレスエリカ】空中ワルツ浮遊＋波状弾幕＋頭上急降下プレス
        boss.isFloating = true
        boss.vy = -2.5
        for (let i = 0; i < 6; i++) {
          fireAimedShot(boss.x, boss.y - 40, 5.2, '#38bdf8', '♬', Math.sin(i) * 0.3)
          await waitAsync(220, signal)
        }
        // プレイヤーの頭上付近へ高速移動して急降下プレス！
        boss.vx = (player.x - boss.x) * 0.08
        await waitAsync(600, signal)
        boss.isFloating = false
        boss.vx = 0; boss.vy = 6.5 // 急降下！
        await waitAsync(600, signal)
        // 着地衝撃波を左右に発射
        bullets.push({ x: boss.x - 20, y: GROUND_Y - 12, vx: -6.5, vy: 0, radius: 13, damage: 18, color: '#60a5fa', noteSymbol: '🌊', isGroundCrawling: true, isEnemy: true })
        bullets.push({ x: boss.x + 20, y: GROUND_Y - 12, vx: 6.5, vy: 0, radius: 13, damage: 18, color: '#60a5fa', noteSymbol: '🌊', isGroundCrawling: true, isEnemy: true })
        await waitAsync(900, signal)

      } else {
        // 👑 【6. 真珠玉座の女王エリカ】5方向バブル＋予兆付き極太ロイヤルレーザー！
        for (let a = -2; a <= 2; a++) {
          fireAimedShot(boss.x - 25, boss.y - 45, 4.8, '#f472b6', '○', a * 0.22)
        }
        await waitAsync(700, signal)
        // エリカの現在Y座標にレーザー予兆ラインを表示！
        const targetY = Math.min(GROUND_Y - 24, Math.max(180, player.y - 30))
        boss.warningLaserY = targetY
        await waitAsync(650, signal) // この0.65秒の間にジャンプかスライディングで避ける！
        boss.warningLaserY = null
        const dir = player.x < boss.x ? -1 : 1
        for (let k = 0; k < 8; k++) {
          bullets.push({ x: boss.x + dir * 30, y: targetY, vx: dir * 11.5, vy: 0, radius: 16, damage: 22, color: '#fde047', noteSymbol: '★', isEnemy: true })
          await waitAsync(55, signal)
        }
        boss.vy = -4.0
        boss.vx = boss.x > 450 ? -3.2 : 3.2
        await waitAsync(950, signal)
        boss.vx = 0
      }
    }
  } catch {}
}

const onEnemyDefeated = (e: Enemy) => {
  score.value += e.score
  e.abortController.abort()
  const roll = Math.random()
  if (roll < 0.07) dropItems.push({ x: e.x, y: e.y - 20, vy: -2.8, type: '1UP', lifeTimer: 450 })
  else if (roll < 0.38) dropItems.push({ x: e.x, y: e.y - 20, vy: -2.5, type: 'HEAL', lifeTimer: 450 })
  else if (roll < 0.65) dropItems.push({ x: e.x, y: e.y - 20, vy: -2.5, type: 'SCORE', lifeTimer: 450 })
}

const selectBonusAndNextStage = (choiceId: string) => {
  if (choiceId === 'DOUBLE') {
    if (upgrades.doubleShot) upgrades.powerMultiplier += 0.2
    upgrades.doubleShot = true
  } else if (choiceId === 'GROUND') {
    if (upgrades.groundShot) upgrades.powerMultiplier += 0.2
    upgrades.groundShot = true
  } else if (choiceId === 'OPTION') {
    if (upgrades.options < 2) upgrades.options++
    else upgrades.powerMultiplier += 0.2
  } else if (choiceId === 'BARRIER') {
    upgrades.barrierHp = 3
  } else if (choiceId === 'CHARGE3') {
    if (upgrades.maxChargeLevel >= 3) upgrades.powerMultiplier += 0.25
    upgrades.maxChargeLevel = 3
  } else if (choiceId === 'VITAL') {
    maxHp.value += 30
    playerHp.value = maxHp.value
    lives.value++
  }
  playerHp.value = Math.min(maxHp.value, playerHp.value + 35)
  startStageFromCloudRun(currentStage.value + 1)
}

const resetFullGame = () => {
  score.value = 0; lives.value = 3; maxHp.value = 100; playerHp.value = 100
  upgrades.doubleShot = false; upgrades.groundShot = false; upgrades.options = 0
  upgrades.barrierHp = 0; upgrades.powerMultiplier = 1.0; upgrades.maxChargeLevel = 2
  startStageFromCloudRun(1)
}

let chargeAbort: AbortController | null = null
const startChargeAsync = async () => {
  chargeAbort?.abort()
  chargeAbort = new AbortController()
  try {
    await waitAsync(400, chargeAbort.signal)
    chargeLevel.value = 1
    await waitAsync(750, chargeAbort.signal)
    chargeLevel.value = 2
    if (upgrades.maxChargeLevel >= 3) {
      await waitAsync(900, chargeAbort.signal)
      chargeLevel.value = 3
    }
  } catch {}
}

const fireFromPosition = (originX: number, originY: number, level: number, isOption = false) => {
  const pMul = (isOption ? 0.6 : 1.0) * upgrades.powerMultiplier
  const dir = player.facing

  const baseConfigs = [
    { speed: 7.5, radius: 9,  dmg: 12, color: '#f472b6', symbol: '♪', pierce: false },
    { speed: 9.5, radius: 14, dmg: 28, color: '#38bdf8', symbol: '♬', pierce: false },
    { speed: 12,  radius: 22, dmg: 52, color: '#facc15', symbol: '♪♬', pierce: true },
    { speed: 14,  radius: 30, dmg: 85, color: '#c084fc', symbol: '𝄞♪', pierce: true },
  ]
  const cfg = baseConfigs[level] || baseConfigs[0]

  bullets.push({
    x: originX, y: originY, vx: dir * cfg.speed, vy: 0,
    radius: cfg.radius, damage: Math.round(cfg.dmg * pMul), color: cfg.color, noteSymbol: cfg.symbol, piercing: cfg.pierce
  })

  if (upgrades.doubleShot) {
    bullets.push({
      x: originX, y: originY - 6, vx: dir * (cfg.speed * 0.8), vy: -cfg.speed * 0.55,
      radius: Math.max(8, cfg.radius * 0.8), damage: Math.round(cfg.dmg * 0.75 * pMul), color: '#fb7185', noteSymbol: '♪', piercing: cfg.pierce
    })
  }

  if (upgrades.groundShot && !isOption) {
    bullets.push({
      x: originX, y: originY + 12, vx: dir * 6.5, vy: 2.5,
      radius: 10, damage: Math.round(14 * pMul), color: '#fbbf24', noteSymbol: '━♪', isGroundCrawling: true
    })
  }
}

const fireGuitarWave = (level: number) => {
  player.shootPoseTimer = 18
  fireFromPosition(player.x + player.facing * 42, player.y - 38, level, false)
  for (let i = 1; i <= upgrades.options; i++) {
    const histIdx = Math.max(0, positionHistory.length - i * 14)
    const optPos = positionHistory[histIdx] || { x: player.x - player.facing * 35 * i, y: player.y }
    fireFromPosition(optPos.x, optPos.y - 35, Math.min(level, 1), true)
  }
  if (level >= 2) player.vx = -player.facing * 2.0
}

const startSlideAsync = async () => {
  if (!player.onGround || player.isSliding) return
  player.isSliding = true
  player.vx = player.facing * PHYSICS.SLIDE_SPEED
  try { await waitAsync(300) } finally { player.isSliding = false }
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
  if (e.code === 'KeyX') { fireGuitarWave(0); startChargeAsync() }
  if (e.code === 'KeyC') startSlideAsync()
}

const onKeyUp = (e: KeyboardEvent) => {
  keys.delete(e.code)
  if ((e.code === 'Space' || e.code === 'KeyZ') && player.vy < -1.5) player.vy *= 0.45
  if (e.code === 'KeyX') {
    if (chargeLevel.value > 0) {
      const lv = chargeLevel.value
      chargeAbort?.abort(); chargeLevel.value = 0
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
  if (upgrades.barrierHp > 0) {
    upgrades.barrierHp--; player.invincibleTimer = 40; return
  }
  playerHp.value = Math.max(0, playerHp.value - amount)
  player.invincibleTimer = 55
  player.vy = -2.5

  if (playerHp.value <= 0) {
    lives.value--
    if (lives.value > 0) {
      playerHp.value = maxHp.value
      player.invincibleTimer = 110
      player.vy = -4.2
    } else {
      gameResult.value = 'GAMEOVER'
      stageAbortController?.abort()
    }
  }
}

// 座標 x が落とし穴の上かどうか判定するヘルパー
const isOverPit = (x: number): boolean => {
  return pits.value.some(p => x > p.x + 12 && x < p.x + p.w - 12)
}

const updateAndDraw = (now: number) => {
  animFrameId = requestAnimationFrame(updateAndDraw)
  const elapsed = now - lastFrameTime
  if (elapsed < 15) return
  lastFrameTime = now

  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')!

  const scrollSpd = currentTheme.isScrolling ? currentTheme.scrollSpeed : 0
  const prevY = player.y

  // ==========================================
  // 1. 強制横スクロールによるギミック（壁・床・落とし穴）の移動
  // ==========================================
  for (let i = obstacles.value.length - 1; i >= 0; i--) {
    obstacles.value[i].x -= scrollSpd
    if (obstacles.value[i].x + obstacles.value[i].w < -60) obstacles.value.splice(i, 1)
  }
  for (let i = pits.value.length - 1; i >= 0; i--) {
    pits.value[i].x -= scrollSpd
    if (pits.value[i].x + pits.value[i].w < -60) pits.value.splice(i, 1)
  }

  // ==========================================
  // 2. プレイヤー移動・壁押し出し・落とし穴落下判定
  // ==========================================
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

  let nextX = player.x + player.vx
  for (const obs of obstacles.value) {
    if (obs.type === 'wall' && player.y > obs.y + 6) {
      if (nextX + 18 > obs.x && nextX - 18 < obs.x + obs.w) {
        if (player.x <= obs.x) nextX = obs.x - 18 // 流れてくる壁に左へ押される！
        else nextX = obs.x + obs.w + 18
        player.vx = 0
      }
    }
  }
  // 壁に押されて画面左端に挟まれたらダメージ＆緊急ジャンプ脱出
  if (nextX < 22) {
    nextX = 45; player.vy = -4.8; damagePlayer(20)
  }
  player.x = Math.min(765, nextX)

  // 縦物理＆空中床・壁の上・地面への着地（落とし穴の上では地面に着地せず落ちる！）
  player.vy += PHYSICS.GRAVITY
  player.y += player.vy
  let landed = false

  for (const obs of obstacles.value) {
    const withinX = player.x + 16 > obs.x && player.x - 16 < obs.x + obs.w
    if (withinX && player.vy >= 0 && prevY <= obs.y + 6 && player.y >= obs.y) {
      player.y = obs.y; player.vy = 0; landed = true
    }
  }

  if (!landed && !isOverPit(player.x) && player.y >= GROUND_Y && prevY <= GROUND_Y + 8) {
    player.y = GROUND_Y; player.vy = 0; landed = true
  }

  // ★ 落とし穴に落下した時の処理（残機-1して上から復帰！）
  if (player.y > canvas.height + 35) {
    lives.value--
    if (lives.value > 0) {
      playerHp.value = maxHp.value
      player.x = 140; player.y = 120; player.vx = 0; player.vy = 0
      player.invincibleTimer = 110
    } else {
      gameResult.value = 'GAMEOVER'
      stageAbortController?.abort()
    }
  }

  if (landed) {
    if (!player.onGround) { player.scaleX = 1.18; player.scaleY = 0.82 }
    player.onGround = true
  } else {
    player.onGround = false
  }

  positionHistory.push({ x: player.x, y: player.y })
  if (positionHistory.length > 40) positionHistory.shift()

  player.scaleX += (1 - player.scaleX) * 0.18
  player.scaleY += (1 - player.scaleY) * 0.18
  if (player.shootPoseTimer > 0) player.shootPoseTimer--
  if (player.invincibleTimer > 0) player.invincibleTimer--
  if (Math.abs(player.vx) > 0.4) player.runAnimTimer++

  if (player.isSliding || chargeLevel.value >= 2) {
    afterimages.push({ x: player.x, y: player.y, facing: player.facing, alpha: 0.4, spriteKey: getPlayerSpriteKey() })
  }

  // ==========================================
  // 3. 背景・落とし穴・壁・空中床の描画
  // ==========================================
  const skyGrad = ctx.createLinearGradient(0, 0, 0, GROUND_Y)
  skyGrad.addColorStop(0, currentTheme.skyGradient[0])
  skyGrad.addColorStop(0.5, currentTheme.skyGradient[1])
  skyGrad.addColorStop(1, currentTheme.skyGradient[2])
  ctx.fillStyle = skyGrad
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'
  bgStars.forEach(s => {
    s.x = (s.x - (s.speed + scrollSpd * 0.2) + 800) % 800
    ctx.fillRect(s.x, s.y, s.size, s.size)
  })

  bgScrollX = (bgScrollX + scrollSpd * 0.4) % 55
  ctx.fillStyle = 'rgba(15, 23, 42, 0.55)'
  bgBuildings.forEach(b => {
    const bx = (b.x - bgScrollX + 880) % 880 - 55
    ctx.fillRect(bx, GROUND_Y - b.h, b.w, b.h)
  })

  // 地面の描画
  ctx.fillStyle = currentTheme.groundColor
  ctx.fillRect(0, GROUND_Y, canvas.width, canvas.height - GROUND_Y)
  ctx.strokeStyle = currentTheme.lineColor
  ctx.lineWidth = 3
  ctx.beginPath(); ctx.moveTo(0, GROUND_Y); ctx.lineTo(canvas.width, GROUND_Y); ctx.stroke()

  // ★ 落とし穴（Pit）の切り抜き描画
  for (const pit of pits.value) {
    ctx.fillStyle = '#020617'
    ctx.fillRect(pit.x, GROUND_Y - 2, pit.w, canvas.height - GROUND_Y + 4)
    ctx.strokeStyle = '#ef4444'
    ctx.lineWidth = 2
    ctx.strokeRect(pit.x, GROUND_Y, pit.w, canvas.height - GROUND_Y)
  }

  // 壁（Wall）と空中床（Platform）の描画
  for (const obs of obstacles.value) {
    ctx.save()
    if (obs.type === 'wall') {
      ctx.fillStyle = '#1e293b'
      ctx.fillRect(obs.x, obs.y, obs.w, obs.h)
      ctx.strokeStyle = currentTheme.lineColor
      ctx.lineWidth = 2
      ctx.strokeRect(obs.x, obs.y, obs.w, obs.h)
      ctx.fillStyle = '#0f172a'
      ctx.beginPath()
      ctx.arc(obs.x + obs.w / 2, obs.y + obs.h / 2, obs.w * 0.28, 0, Math.PI * 2)
      ctx.fill()
    } else {
      ctx.fillStyle = '#334155'
      ctx.fillRect(obs.x, obs.y, obs.w, obs.h)
      ctx.fillStyle = '#38bdf8'
      ctx.fillRect(obs.x, obs.y, obs.w, 4)
    }
    ctx.restore()
  }

  // 残像＆オプション＆エリカ本体描画
  for (let i = afterimages.length - 1; i >= 0; i--) {
    const aft = afterimages[i]
    aft.alpha -= 0.05
    if (aft.alpha <= 0) { afterimages.splice(i, 1); continue }
    drawSprite(ctx, sprites[aft.spriteKey], aft.x, aft.y, aft.facing, 96, 1, 1, aft.alpha, 190)
  }

  for (let i = 1; i <= upgrades.options; i++) {
    const histIdx = Math.max(0, positionHistory.length - i * 14)
    const optPos = positionHistory[histIdx] || { x: player.x - player.facing * 35 * i, y: player.y }
    const floatY = Math.sin(now * 0.008 + i) * 5
    ctx.save()
    ctx.beginPath()
    ctx.arc(optPos.x, optPos.y - 35 + floatY, 11, 0, Math.PI * 2)
    ctx.fillStyle = '#38bdf8'; ctx.shadowColor = '#38bdf8'; ctx.shadowBlur = 12; ctx.fill()
    ctx.fillStyle = '#0f172a'; ctx.font = 'bold 11px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText('♪', optPos.x, optPos.y - 35 + floatY)
    ctx.restore()
  }

  if (chargeLevel.value > 0) {
    ctx.save()
    ctx.beginPath()
    const r = 32 + chargeLevel.value * 8 + Math.sin(now * 0.03) * 5
    ctx.arc(player.x, player.y - 42, r, 0, Math.PI * 2)
    ctx.fillStyle = chargeLevel.value === 3 ? 'rgba(192, 132, 252, 0.35)' : chargeLevel.value === 2 ? 'rgba(250, 204, 21, 0.28)' : 'rgba(56, 189, 248, 0.22)'
    ctx.fill()
    ctx.strokeStyle = chargeLevel.value === 3 ? '#e879f9' : chargeLevel.value === 2 ? '#facc15' : '#38bdf8'
    ctx.stroke()
    ctx.restore()
  }

  if (player.invincibleTimer % 4 < 2) {
    const slideY = player.isSliding ? 0.72 : player.scaleY
    drawSprite(ctx, sprites[getPlayerSpriteKey()], player.x, player.y, player.facing, 96, player.scaleX, slideY, 1.0, 0)
  }

  if (upgrades.barrierHp > 0) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(player.x, player.y - 42, 46, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(56, 189, 248, ${0.35 + upgrades.barrierHp * 0.2})`
    ctx.lineWidth = 3; ctx.setLineDash([8, 6]); ctx.stroke()
    ctx.restore()
  }

  // ドロップアイテム更新
  for (let i = dropItems.length - 1; i >= 0; i--) {
    const item = dropItems[i]
    item.x -= scrollSpd
    item.vy += PHYSICS.GRAVITY
    if (!isOverPit(item.x)) item.y = Math.min(GROUND_Y - 12, item.y + item.vy)
    else item.y += item.vy
    item.lifeTimer--

    ctx.save()
    ctx.font = 'bold 18px sans-serif'; ctx.textAlign = 'center'
    const label = item.type === '1UP' ? '⭐1UP' : item.type === 'HEAL' ? '💚+HP' : '🎵'
    ctx.fillStyle = item.type === '1UP' ? '#facc15' : item.type === 'HEAL' ? '#4ade80' : '#f472b6'
    ctx.fillText(label, item.x, item.y)
    ctx.restore()

    if (Math.abs(player.x - item.x) < 34 && Math.abs((player.y - 30) - item.y) < 36) {
      if (item.type === '1UP') lives.value++
      else if (item.type === 'HEAL') playerHp.value = Math.min(maxHp.value, playerHp.value + 30)
      else score.value += 300
      dropItems.splice(i, 1)
      continue
    }
    if (item.lifeTimer <= 0 || item.y > canvas.height + 30) dropItems.splice(i, 1)
  }

  // ==========================================
  // 4. 敵キャラの更新（壁でジャンプ or 引き返し、落とし穴へ落下！）
  // ==========================================
  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i]
    const prevEnemyY = e.y
    if (!e.isStunned) e.x += e.vx - scrollSpd * 0.65

    // ★ 敵が壁や落とし穴に遭遇した時のギミック反応！
    for (const obs of obstacles.value) {
      if (obs.type === 'wall' && e.y > obs.y + 8 && Math.abs(e.x - (obs.x + obs.w / 2)) < obs.w / 2 + 22) {
        if (e.wallAction === 'bounce') {
          // カメや煤玉は壁に当たるとくるっと引き返す！
          e.vx = -e.vx
          e.x += e.vx * 3
        } else if (e.wallAction === 'jump' && e.vy === 0) {
          // 豆っこやハリネズミはジャンプして壁を飛び越える！
          e.vy = -4.3
        }
      }
    }

    // 落とし穴の手前でジャンプできる敵は飛び越える
    for (const pit of pits.value) {
      if (e.wallAction === 'jump' && e.vy === 0 && Math.abs(e.x - (pit.x + pit.w)) < 18) {
        e.vy = -4.4
      }
    }

    if (e.type === 'note_ghost') {
      e.y = e.baseY + Math.sin(now * 0.004 + i) * 32
    } else {
      e.vy += PHYSICS.GRAVITY
      e.y += e.vy
      // 空中床や壁の上への着地
      for (const obs of obstacles.value) {
        if (e.x + 14 > obs.x && e.x - 14 < obs.x + obs.w && e.vy >= 0 && prevEnemyY <= obs.y + 6 && e.y >= obs.y) {
          e.y = obs.y; e.vy = 0
        }
      }
      // 落とし穴の上でなければ地面に着地
      if (!isOverPit(e.x) && e.y >= GROUND_Y && prevEnemyY <= GROUND_Y + 8) {
        e.y = GROUND_Y; e.vy = 0
      }
    }

    const shakeX = e.isCharging ? (Math.random() - 0.5) * 8 : 0
    const moleScaleY = e.isHidden ? 0.45 : 1.0
    const stunFlipY = e.isStunned ? -0.8 : moleScaleY
    const enemyFacing = e.vx > 0 ? -1 : 1 // 右へ引き返す時は絵を反転
    drawSprite(ctx, sprites[e.type], e.x + shakeX, e.y, enemyFacing, 76, 1, stunFlipY, 1.0, e.hueRotate)

    // 敵の頭上にミニHPバーを表示（耐久力が上がった手応えを可視化！）
    if (e.hp < e.maxHp) {
      ctx.fillStyle = '#1e293b'; ctx.fillRect(e.x - 20, e.y - 78, 40, 5)
      ctx.fillStyle = '#f43f5e'; ctx.fillRect(e.x - 20, e.y - 78, 40 * (e.hp / e.maxHp), 5)
    }

    if (Math.abs(player.x - e.x) < 36 && Math.abs(player.y - e.y) < 42) {
      if (player.vy > 0 && player.y < e.y - 12) {
        if (e.spiky) {
          damagePlayer(15)
        } else if (e.stompable) {
          player.vy = PHYSICS.BOUNCE_VELOCITY
          player.scaleX = 1.22; player.scaleY = 0.78
          e.hp -= Math.round(22 * upgrades.powerMultiplier)
          if (e.type === 'turtle' && e.hp > 0) e.isStunned = true
          if (e.hp <= 0) {
            onEnemyDefeated(e); enemies.splice(i, 1); continue
          }
        }
      } else if (!player.isSliding) {
        damagePlayer(14)
      }
    }

    if (e.x < -80 || e.y > canvas.height + 50) {
      e.abortController.abort()
      enemies.splice(i, 1)
    }
  }

  // ==========================================
  // 5. 6人の「ちびエリカ・ボス」の更新＆描画
  // ==========================================
  if (boss.active) {
    boss.x = Math.max(90, Math.min(720, boss.x + boss.vx))
    if (boss.isFloating) {
      boss.y = Math.max(160, Math.min(260, boss.y + boss.vy))
    } else {
      boss.vy += PHYSICS.GRAVITY
      boss.y = Math.min(GROUND_Y, boss.y + boss.vy)
      if (boss.y >= GROUND_Y) boss.vy = 0
    }

    // 女王エリカのロイヤルレーザー予兆ライン描画
    if (boss.warningLaserY !== null) {
      ctx.save()
      ctx.fillStyle = 'rgba(250, 204, 21, 0.28)'
      ctx.fillRect(0, boss.warningLaserY - 14, canvas.width, 28)
      ctx.strokeStyle = '#ef4444'; ctx.setLineDash([10, 6]); ctx.lineWidth = 2
      ctx.beginPath(); ctx.moveTo(0, boss.warningLaserY); ctx.lineTo(canvas.width, boss.warningLaserY); ctx.stroke()
      ctx.restore()
    }

    // ボスはプレイヤーの方を向く
    const bossFacing = player.x > boss.x ? -1 : 1
    drawSprite(ctx, sprites[boss.spriteKey], boss.x, boss.y, bossFacing, 96 * boss.scale, 1, 1, 1.0, 0)

    if (Math.abs(player.x - boss.x) < 42 && Math.abs(player.y - boss.y) < 58) {
      damagePlayer(20)
    }
  }

  // ==========================================
  // 6. 音符弾の更新 ＆ 壁（Wall）による遮断判定！
  // ==========================================
  for (let i = bullets.length - 1; i >= 0; i--) {
    const b = bullets[i]
    b.x += b.vx
    b.y += b.vy

    if (b.isGroundCrawling) {
      let surfaceY = GROUND_Y - 10
      for (const obs of obstacles.value) {
        if (b.x >= obs.x && b.x <= obs.x + obs.w) surfaceY = Math.min(surfaceY, obs.y - 10)
      }
      b.y = surfaceY
    }

    // ★ 壁（Wall）に当たった弾は貫通属性（Lv.2以上）でない限り遮断されて消える！
    let blockedByWall = false
    if (!b.piercing && !b.isGroundCrawling) {
      for (const obs of obstacles.value) {
        if (obs.type === 'wall' && b.x + b.radius > obs.x && b.x - b.radius < obs.x + obs.w && b.y + b.radius > obs.y && b.y - b.radius < obs.y + obs.h) {
          blockedByWall = true
          break
        }
      }
    }
    if (blockedByWall) { bullets.splice(i, 1); continue }

    ctx.save()
    ctx.beginPath()
    ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2)
    ctx.fillStyle = b.color + '44'
    ctx.shadowColor = b.color; ctx.shadowBlur = 12
    ctx.fill()
    ctx.fillStyle = b.color
    ctx.font = `bold ${Math.max(15, b.radius * 1.3)}px sans-serif`
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText(b.noteSymbol, b.x, b.y)
    ctx.restore()

    if (b.isEnemy) {
      if (Math.abs(b.x - player.x) < 22 && Math.abs(b.y - (player.y - 36)) < 32) {
        damagePlayer(b.damage)
        bullets.splice(i, 1)
        continue
      }
    } else {
      let hit = false
      for (let j = enemies.length - 1; j >= 0; j--) {
        const e = enemies[j]
        if (Math.abs(b.x - e.x) < 34 && Math.abs(b.y - (e.y - 32)) < 36) {
          if (e.isHidden && !b.piercing && !b.isGroundCrawling) {
            b.vx = -b.vx * 0.8; b.vy = -2; break
          }
          const dmg = (e.armored && !b.piercing && !e.isStunned) ? Math.ceil(b.damage * 0.4) : b.damage
          e.hp -= dmg; hit = true
          if (e.hp <= 0) {
            onEnemyDefeated(e); enemies.splice(j, 1)
          }
          if (!b.piercing) break
        }
      }
      if (hit && !b.piercing) { bullets.splice(i, 1); continue }

      if (boss.active && Math.abs(b.x - boss.x) < 46 && Math.abs(b.y - (boss.y - 48)) < 56) {
        boss.hp = Math.max(0, boss.hp - b.damage)
        if (!b.piercing) bullets.splice(i, 1)
        if (boss.hp <= 0) {
          boss.active = false; boss.warningLaserY = null
          boss.abortController?.abort()
          score.value += 2000 * currentStage.value
          gameResult.value = 'CLEAR'
        }
        continue
      }
    }

    if (b.x < -60 || b.x > canvas.width + 60 || b.y < -60 || b.y > canvas.height + 60) {
      bullets.splice(i, 1)
    }
  }
}

const drawSprite = (
  ctx: CanvasRenderingContext2D, img: HTMLImageElement | undefined,
  x: number, y: number, facing: number, size: number,
  scaleX: number, scaleY: number, alpha: number, hueRotateDeg: number
) => {
  ctx.save()
  ctx.globalAlpha = alpha
  ctx.translate(x, y)
  ctx.scale(facing * scaleX, scaleY)
  if (img && img.complete && img.naturalWidth > 0) {
    if (hueRotateDeg !== 0) ctx.filter = `hue-rotate(${hueRotateDeg}deg) saturate(1.3)`
    ctx.drawImage(img, -size / 2, -size + 6, size, size)
  } else {
    ctx.fillStyle = hueRotateDeg ? '#38bdf8' : '#ec4899'
    ctx.fillRect(-size / 3, -size * 0.8, (size * 2) / 3, size * 0.8)
  }
  ctx.restore()
}

onMounted(async () => {
  await loadMasterJsonAsync()
  await loadAllSprites()
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  lastFrameTime = performance.now()
  animFrameId = requestAnimationFrame(updateAndDraw)
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