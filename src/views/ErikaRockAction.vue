<template>
  <div class="relative w-full max-w-4xl mx-auto bg-slate-950 rounded-xl overflow-hidden shadow-2xl border border-slate-800 select-none font-sans">
    <!-- 上部ステータスUI（残機・明確なHP数値・武装アイコン・ボスHP） -->
    <div class="absolute top-3 left-4 right-4 flex justify-between items-start pointer-events-none z-10">
      <div class="flex flex-col gap-1.5 bg-slate-900/90 px-4 py-2.5 rounded-lg border border-slate-700 backdrop-blur-sm shadow-lg">
        <!-- 残機 & スコア & ステージ表示 -->
        <div class="flex items-center gap-4 text-xs">
          <span class="font-extrabold text-pink-400 tracking-wider">STAGE {{ currentStage }}</span>
          <span class="font-bold text-rose-400 flex items-center gap-1">
            ERIKA <span v-for="n in lives" :key="n" class="text-sm">♥</span>
          </span>
          <span class="font-mono text-slate-300">SCORE: {{ score }}</span>
        </div>

        <!-- HPゲージ（数値明記）＆ チャージインジケーター -->
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
            {{ chargeLevel === 3 ? 'FINAL CHARGE!!' : chargeLevel === 2 ? 'LV.2 CHARGE!' : chargeLevel === 1 ? 'LV.1 CHARGE' : 'NOTE BUSTER' }}
          </div>
        </div>

        <!-- グラディウス風・現在装備中のパワーアップ表示 -->
        <div class="flex flex-wrap gap-1.5 mt-0.5 text-[10px] font-mono">
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.doubleShot ? 'bg-pink-600 text-white font-bold' : 'bg-slate-800 text-slate-500'">2-WAY</span>
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.groundShot ? 'bg-amber-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-500'">GROUND</span>
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.options > 0 ? 'bg-cyan-500 text-slate-950 font-bold' : 'bg-slate-800 text-slate-500'">OPTION×{{ upgrades.options }}</span>
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.barrierHp > 0 ? 'bg-blue-500 text-white font-bold' : 'bg-slate-800 text-slate-500'">BARRIER:{{ upgrades.barrierHp }}</span>
          <span class="px-1.5 py-0.5 rounded" :class="upgrades.maxChargeLevel === 3 ? 'bg-purple-500 text-white font-bold' : 'bg-slate-800 text-slate-500'">MAX-LV.{{ upgrades.maxChargeLevel }}</span>
          <span class="px-1.5 py-0.5 rounded bg-slate-800 text-emerald-400">ATK×{{ upgrades.powerMultiplier.toFixed(2) }}</span>
        </div>
      </div>

      <!-- 右上：Cloud Run 状態 ＆ ボスHP -->
      <div class="flex flex-col items-end gap-2">
        <div class="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-900/85 border border-slate-700 text-slate-300">
          API: <span :class="apiStatus === 'ONLINE' ? 'text-emerald-400 font-bold' : 'text-amber-400'">{{ apiStatus }}</span>
        </div>

        <div v-if="boss.active" class="bg-slate-900/90 px-4 py-2 rounded-lg border border-red-500/70 text-right shadow-lg">
          <div class="text-xs font-bold text-red-400 tracking-wider">{{ boss.name }}</div>
          <div class="text-[10px] font-mono text-slate-300">{{ boss.hp }} / {{ boss.maxHp }}</div>
          <div class="w-44 h-3 bg-slate-800 rounded overflow-hidden mt-0.5 border border-slate-600">
            <div class="h-full bg-gradient-to-r from-red-600 to-amber-500 transition-all duration-150"
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

    <!-- ★ グラディウス風・ステージクリアボーナス（武装強化セレクト画面） -->
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
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Z</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Space</kbd> ジャンプ（壁越え・踏みつけ）</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">X</kbd> 音符ショット（長押しで多段階チャージ）</span>
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

// ★ ご自身の Cloud Run の URL を設定してください
const API_BASE = import.meta.env.VITE_API_URL || 'https://erika-action-api-xxxxxxxxxx-an.a.run.app'

const PHYSICS = {
  MOVE_ACCEL: 0.45,
  MOVE_MAX_SPEED: 3.6,
  FRICTION: 0.82,
  JUMP_VELOCITY: -4.8,
  GRAVITY: 0.075,
  SLIDE_SPEED: 7.2,
  BOUNCE_VELOCITY: -4.4,
}

const canvasRef = ref<HTMLCanvasElement | null>(null)
const maxHp = ref(100)
const playerHp = ref(100)
const lives = ref(3) // 残機設定（初期3機）
const score = ref(0)
const chargeLevel = ref(0)
const apiStatus = ref<'WAKING UP...' | 'ONLINE' | 'JSON MASTER'>('WAKING UP...')
const isLoadingStage = ref(false)
const currentStage = ref(1)
const gameResult = ref<'CLEAR' | 'GAMEOVER' | null>(null)

// グラディウス風・エリカバスター武装強化ステート
const upgrades = reactive({
  doubleShot: false,     // 2方向ショット（前方＋斜め上）
  groundShot: false,     // 地面を這う音波弾
  options: 0,            // 追従するミニスピーカーオプション数（最大2）
  barrierHp: 0,          // バリア耐久値
  powerMultiplier: 1.0,  // 攻撃力倍率
  maxChargeLevel: 2,     // 最大チャージ段階（初期2 → ボーナスで3解放）
})

const bonusChoices = computed(() => [
  { id: 'DOUBLE',  title: '🎵 2方向デュアルショット', desc: upgrades.doubleShot ? '取得済（選ぶと攻撃力+15%）' : '前方と斜め上45度へ同時に音符弾を発射！' },
  { id: 'GROUND',  title: '🔊 グランド・リップル弾', desc: upgrades.groundShot ? '取得済（選ぶと攻撃力+15%）' : '地面や壁に沿って這う低音レーザーを追加発射！' },
  { id: 'OPTION',  title: `🛰️ サウンド・オプション (${upgrades.options}/2)`, desc: 'エリカの後ろを追従し、同時に音符を撃つスピーカーを追加！' },
  { id: 'BARRIER', title: '🛡️ 音響フォースバリア', desc: '敵の弾や体当たりを3回まで無効化するバリアを展開！' },
  { id: 'CHARGE3', title: '⚡ ファイナルチャージ解放 (Lv.3)', desc: upgrades.maxChargeLevel >= 3 ? '取得済（選ぶと攻撃力+20%）' : '3段階目の極太虹色サウンドブラスターを解放！' },
  { id: 'VITAL',   title: '💖 最大HP+30 ＆ 全回復 ＆ 1UP', desc: '最大体力を増やし、HP全回復＋残機を1つ増やす！' },
])

const cutin = reactive({ visible: false, bossName: '', quote: '', source: '' })

// 外出しJSON（game-master.json）の保持データ（未配置でも動くデフォルト値付き）
let masterData: any = {
  quotes: [
    { quote: '手探りでもただ前に進むしかない。いずれなんとかなるだろってな。', source: '『シャーマンキング』麻倉葉' },
    { quote: 'お前が信じる、お前を信じろ！', source: '『天元突破グレンラガン』カミナ' },
  ],
  enemies: [
    { type: 'soot',       name: '煤玉モンスター', sprite: '/sprites/enemies/soot.png',       hp: 10, speed: 1.4, score: 100, stompable: true },
    { type: 'lime',       name: 'ライム豆っこ',   sprite: '/sprites/enemies/lime.png',       hp: 12, speed: 2.0, score: 150, stompable: true },
    { type: 'jelly',      name: '桃色ゼリー',     sprite: '/sprites/enemies/jelly.png',      hp: 18, speed: 1.3, score: 200, stompable: true },
    { type: 'note_ghost', name: '音符のおばけ',   sprite: '/sprites/enemies/note_ghost.png', hp: 15, speed: 1.6, score: 250, stompable: true },
    { type: 'turtle',     name: 'ずんぐりカメ',   sprite: '/sprites/enemies/turtle.png',     hp: 35, speed: 0.9, score: 300, stompable: true,  armored: true },
    { type: 'mole',       name: '鉱夫モグラ',     sprite: '/sprites/enemies/mole.png',       hp: 25, speed: 0.0, score: 350, stompable: false, helmet: true },
    { type: 'hedgehog',   name: '赤いハリネズミ', sprite: '/sprites/enemies/hedgehog.png',   hp: 28, speed: 4.0, score: 400, stompable: false, spiky: true },
  ],
  bosses: [
    { id: 'shadow_erika', name: 'SHADOW ERIKA',     spriteKey: 'shoot',      baseHp: 140, hueRotate: 190, scale: 1.15, pattern: 'STANDARD' },
    { id: 'king_turtle',  name: 'FORTRESS TURTLE',  spriteKey: 'turtle',     baseHp: 200, hueRotate: 290, scale: 1.65, pattern: 'HEAVY_STAMP' },
    { id: 'sonic_hedge',  name: 'CRIMSON OVERDRIVE',spriteKey: 'hedgehog',   baseHp: 170, hueRotate: 50,  scale: 1.55, pattern: 'SPEED_RUSH' },
    { id: 'phantom_note', name: 'SYMPHONY PHANTOM', spriteKey: 'note_ghost', baseHp: 160, hueRotate: 130, scale: 1.6,  pattern: 'BARRAGE' },
  ],
  stages: [
    {
      stage: 1, themeName: 'SUNSET HIGHWAY', skyGradient: ['#0f172a', '#311042', '#701a75'], groundColor: '#1e1b4b', lineColor: '#ec4899', enemyHue: 0,
      obstacles: [{ x: 270, y: 325, w: 45, h: 45, type: 'wall' }, { x: 420, y: 275, w: 120, h: 18, type: 'platform' }]
    },
    {
      stage: 2, themeName: 'CYBER NEON LABYRINTH', skyGradient: ['#020617', '#0f2942', '#065f46'], groundColor: '#064e3b', lineColor: '#34d399', enemyHue: 110,
      obstacles: [{ x: 230, y: 310, w: 45, h: 60, type: 'wall' }, { x: 360, y: 250, w: 100, h: 18, type: 'platform' }, { x: 510, y: 320, w: 45, h: 50, type: 'wall' }]
    },
    {
      stage: 3, themeName: 'CRIMSON AMPLIFIER', skyGradient: ['#180404', '#450a0a', '#7c2d12'], groundColor: '#270909', lineColor: '#f97316', enemyHue: 220,
      obstacles: [{ x: 210, y: 300, w: 50, h: 70, type: 'wall' }, { x: 320, y: 235, w: 90, h: 18, type: 'platform' }, { x: 460, y: 295, w: 50, h: 75, type: 'wall' }]
    }
  ]
}

const loadMasterJsonAsync = async () => {
  try {
    const res = await fetch('/assets/game-master.json')
    if (res.ok) masterData = await res.json()
  } catch {
    // JSON未配置でも内蔵のmasterDataでそのまま動作
  }
}

const sprites: Record<string, HTMLImageElement> = {}
const loadAllSprites = async () => {
  const basePaths: Record<string, string> = {
    idle: '/sprites/idle.png', run1: '/sprites/run1.png', run2: '/sprites/run2.png',
    shoot: '/sprites/shoot.png', jump: '/sprites/jump.png', jumpShoot: '/sprites/jump_shoot.png',
  }
  masterData.enemies.forEach((e: any) => { basePaths[e.type] = e.sprite })
  await Promise.all(
    Object.entries(basePaths).map(([key, src]) => new Promise<void>((resolve) => {
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
  x: 100, y: GROUND_Y, vx: 0, vy: 0, facing: 1 as 1 | -1,
  onGround: true, shootPoseTimer: 0, isSliding: false, invincibleTimer: 0,
  scaleX: 1, scaleY: 1, runAnimTimer: 0
}

// オプション（追従スピーカー）用にエリカの過去の移動軌跡を記録
const positionHistory: { x: number; y: number }[] = []

// ステージ障害物（ジャンプで越える壁・乗れる空中床）
interface Obstacle { x: number; y: number; w: number; h: number; type: 'wall' | 'platform' }
const obstacles = ref<Obstacle[]>([])
const currentTheme = reactive({
  skyGradient: ['#0f172a', '#311042', '#701a75'],
  groundColor: '#1e1b4b',
  lineColor: '#ec4899',
  enemyHue: 0
})

// 音符弾・ドロップアイテム・敵・ボスの型定義
interface Bullet {
  x: number; y: number; vx: number; vy: number
  radius: number; damage: number; color: string
  noteSymbol: string; piercing?: boolean; isGroundCrawling?: boolean; isEnemy?: boolean
}
interface DropItem {
  x: number; y: number; vy: number; type: 'HEAL' | '1UP' | 'SCORE'; lifeTimer: number
}
interface Enemy {
  id: string; type: string; name: string
  x: number; y: number; vx: number; vy: number
  hp: number; maxHp: number; score: number
  stompable: boolean; spiky?: boolean; armored?: boolean; helmet?: boolean
  isHidden?: boolean; isCharging?: boolean; isStunned?: boolean
  hueRotate: number; baseY: number; abortController: AbortController
}

const bullets: Bullet[] = []
const dropItems: DropItem[] = []
const enemies: Enemy[] = []
const afterimages: { x: number; y: number; facing: number; alpha: number; spriteKey: string }[] = []
let stageAbortController: AbortController | null = null

const boss = reactive({
  active: false, name: '', spriteKey: 'shoot', x: 660, y: GROUND_Y, vx: 0, vy: 0,
  hp: 100, maxHp: 100, hueRotate: 190, scale: 1.15, pattern: 'STANDARD',
  state: 'IDLE' as 'IDLE' | 'CHARGING' | 'ATTACK',
  abortController: null as AbortController | null
})

// 背景用の星空＆イコライザービル群データ
const bgStars = Array.from({ length: 35 }, () => ({
  x: Math.random() * 800, y: Math.random() * 260, size: Math.random() * 2 + 1, speed: Math.random() * 0.3 + 0.1
}))
const bgBuildings = Array.from({ length: 16 }, (_, i) => ({
  x: i * 55, w: 42, h: 60 + (i * 37) % 110
}))
let bgScrollX = 0

const wakeUpCloudRunAsync = async () => {
  try {
    const res = await fetch(`${API_BASE}/api/health`)
    if (res.ok) apiStatus.value = 'ONLINE'
    else apiStatus.value = 'JSON MASTER'
  } catch {
    apiStatus.value = 'JSON MASTER'
  }
}

// ステージの地形・背景・難易度をセットアップして開始
const startStageFromCloudRun = async (stageNum: number) => {
  isLoadingStage.value = true
  gameResult.value = null
  currentStage.value = stageNum

  stageAbortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  enemies.length = 0
  bullets.length = 0
  dropItems.length = 0
  boss.active = false
  boss.abortController?.abort()

  // ステージ見た目の適用（ステージが進むほど敵の色相が変化し、壁も変化）
  const stageTemplate = masterData.stages[(stageNum - 1) % masterData.stages.length]
  currentTheme.skyGradient = stageTemplate.skyGradient
  currentTheme.groundColor = stageTemplate.groundColor
  currentTheme.lineColor = stageTemplate.lineColor
  currentTheme.enemyHue = (stageNum - 1) * 55 // ステージごとに敵の色が変化！
  obstacles.value = JSON.parse(JSON.stringify(stageTemplate.obstacles))

  // プレイヤー位置を左端へ戻す
  player.x = 90; player.y = GROUND_Y; player.vx = 0; player.vy = 0

  stageAbortController = new AbortController()
  const stageSignal = stageAbortController.signal

  // Cloud Run API からの取得を試みつつ、JSONのカスタム敵＆ボス定義とマージする
  try {
    const res = await fetch(`${API_BASE}/api/stage-start?stage=${stageNum}`)
    if (res.ok) apiStatus.value = 'ONLINE'
  } catch {
    apiStatus.value = 'JSON MASTER'
  } finally {
    isLoadingStage.value = false
  }

  // ステージ番号に応じた難易度スケーリング（敵の数・HP・スピードが上昇！）
  const enemyCount = 6 + stageNum * 2
  const hpMultiplier = 1 + (stageNum - 1) * 0.25
  const speedMultiplier = 1 + Math.min(0.6, (stageNum - 1) * 0.08)

  const waves = Array.from({ length: enemyCount }, (_, i) => {
    const template = masterData.enemies[(i + stageNum) % masterData.enemies.length]
    return {
      id: `stage_${stageNum}_enemy_${i}`,
      spawn_delay_ms: 800 + i * Math.max(1500, 2600 - stageNum * 150),
      ...template,
      hp: Math.round(template.hp * hpMultiplier),
      speed: template.speed * speedMultiplier,
    }
  })

  // ステージごとに異なるボスをJSONから選出
  const bossTemplate = masterData.bosses[(stageNum - 1) % masterData.bosses.length]
  const quoteObj = masterData.quotes[(stageNum - 1) % masterData.quotes.length]

  try {
    const wavePromises = waves.map(w => spawnEnemyWaveAsync(w, stageSignal))
    await Promise.all(wavePromises)

    while (enemies.length > 0) {
      await waitAsync(500, stageSignal)
    }

    await startBossBattleAsync({
      boss_name: `${bossTemplate.name} // Lv.${stageNum}`,
      spriteKey: bossTemplate.spriteKey,
      hp: Math.round(bossTemplate.baseHp * hpMultiplier),
      hueRotate: bossTemplate.hueRotate,
      scale: bossTemplate.scale,
      pattern: bossTemplate.pattern,
      cutin_quote: quoteObj
    }, stageSignal)
  } catch {}
}

const spawnEnemyWaveAsync = async (wave: any, stageSignal: AbortSignal) => {
  await waitAsync(wave.spawn_delay_ms, stageSignal)

  const enemyAbort = new AbortController()
  stageSignal.addEventListener('abort', () => enemyAbort.abort())

  const isFlying = wave.type === 'note_ghost'
  const startY = isFlying ? 210 : GROUND_Y

  const enemy: Enemy = {
    id: wave.id, type: wave.type, name: wave.name,
    x: wave.type === 'mole' ? 540 + Math.random() * 160 : 830,
    y: startY, baseY: startY, vx: -wave.speed, vy: 0,
    hp: wave.hp, maxHp: wave.hp, score: wave.score,
    stompable: wave.stompable, spiky: wave.spiky, armored: wave.armored, helmet: wave.helmet,
    hueRotate: currentTheme.enemyHue,
    abortController: enemyAbort
  }
  enemies.push(enemy)

  const { signal } = enemyAbort
  try {
    if (enemy.type === 'hedgehog') {
      while (enemy.hp > 0) {
        enemy.vx = -1.5
        await waitAsync(1400, signal)
        enemy.vx = 0; enemy.isCharging = true
        await waitAsync(600, signal)
        enemy.isCharging = false; enemy.vx = -5.5
        await waitAsync(900, signal)
      }
    } else if (enemy.type === 'mole') {
      while (enemy.hp > 0) {
        enemy.isHidden = true
        await waitAsync(1500, signal)
        enemy.isHidden = false
        bullets.push({ x: enemy.x - 24, y: enemy.y - 28, vx: -4.2, vy: 0, radius: 8, damage: 12, color: '#f59e0b', noteSymbol: '●', isEnemy: true })
        await waitAsync(1400, signal)
      }
    } else if (enemy.type === 'jelly') {
      while (enemy.hp > 0) {
        if (enemy.y >= GROUND_Y) enemy.vy = -3.9
        await waitAsync(1700, signal)
      }
    } else if (enemy.type === 'note_ghost') {
      while (enemy.hp > 0) {
        await waitAsync(2000, signal)
        bullets.push({ x: enemy.x - 20, y: enemy.y - 30, vx: -3.8, vy: 0.6, radius: 9, damage: 10, color: '#c084fc', noteSymbol: '♪', isEnemy: true })
      }
    }
  } catch {}
}

// 敵撃破時のアイテムドロップ判定（体力回復・1UP・スコア）
const onEnemyDefeated = (e: Enemy) => {
  score.value += e.score
  e.abortController.abort()

  const roll = Math.random()
  if (roll < 0.06) {
    // 6%で「1UP（残機アップ）」ドロップ！
    dropItems.push({ x: e.x, y: e.y - 20, vy: -2.8, type: '1UP', lifeTimer: 450 })
  } else if (roll < 0.35) {
    // 29%で「ハート（HP+25回復）」ドロップ！
    dropItems.push({ x: e.x, y: e.y - 20, vy: -2.5, type: 'HEAL', lifeTimer: 450 })
  } else if (roll < 0.60) {
    // 25%で「ボーナス音符」ドロップ
    dropItems.push({ x: e.x, y: e.y - 20, vy: -2.5, type: 'SCORE', lifeTimer: 450 })
  }
}

// 多彩なボス戦AI（JSONで定義した4種のボスパターンに対応）
const startBossBattleAsync = async (bossData: any, stageSignal: AbortSignal) => {
  // ボス戦では邪魔な壁を撤去して広く戦えるようにする（空中床だけ残す）
  obstacles.value = obstacles.value.filter(o => o.type === 'platform')

  cutin.bossName = bossData.boss_name
  cutin.quote = bossData.cutin_quote.quote
  cutin.source = bossData.cutin_quote.source
  cutin.visible = true
  await waitAsync(2400, stageSignal)
  cutin.visible = false

  boss.name = bossData.boss_name
  boss.spriteKey = bossData.spriteKey
  boss.maxHp = bossData.hp
  boss.hp = bossData.hp
  boss.hueRotate = bossData.hueRotate
  boss.scale = bossData.scale
  boss.pattern = bossData.pattern
  boss.x = 660; boss.y = GROUND_Y; boss.vx = 0; boss.vy = 0
  boss.active = true

  boss.abortController = new AbortController()
  stageSignal.addEventListener('abort', () => boss.abortController?.abort())
  const { signal } = boss.abortController

  try {
    while (boss.active && boss.hp > 0) {
      boss.state = 'IDLE'; boss.vx = 0
      await waitAsync(1100, signal)

      boss.state = 'CHARGING'
      await waitAsync(700, signal)

      boss.state = 'ATTACK'
      if (boss.pattern === 'SPEED_RUSH') {
        // 高速突進型ボス（クリムゾン・ハリネズミ）
        boss.vx = -6.5
        await waitAsync(800, signal)
        boss.vx = 5.5
        await waitAsync(900, signal)
        boss.vx = 0
      } else if (boss.pattern === 'HEAVY_STAMP') {
        // 大ジャンプ踏み潰し＋全方位弾（フォートレス・タートル）
        boss.vy = -5.2
        await waitAsync(1200, signal)
        for (let angle = -2; angle <= 0; angle++) {
          bullets.push({ x: boss.x - 30, y: boss.y - 25, vx: -5, vy: angle * 1.2, radius: 12, damage: 18, color: '#a855f7', noteSymbol: '♬', isEnemy: true })
        }
      } else {
        // 3連音符バラージ＋ジャンプ（シャドウエリカ / シンフォニーファントム）
        for (let i = 0; i < 3; i++) {
          bullets.push({ x: boss.x - 35, y: boss.y - 35 - i * 18, vx: -5.8, vy: (i - 1) * 0.6, radius: 11, damage: 15, color: '#f43f5e', noteSymbol: '♪', isEnemy: true })
          await waitAsync(240, signal)
        }
        boss.vy = -4.2
        await waitAsync(1400, signal)
      }
    }
  } catch {}
}

// ステージクリア時のボーナス選択処理
const selectBonusAndNextStage = (choiceId: string) => {
  if (choiceId === 'DOUBLE') {
    if (upgrades.doubleShot) upgrades.powerMultiplier += 0.15
    upgrades.doubleShot = true
  } else if (choiceId === 'GROUND') {
    if (upgrades.groundShot) upgrades.powerMultiplier += 0.15
    upgrades.groundShot = true
  } else if (choiceId === 'OPTION') {
    if (upgrades.options < 2) upgrades.options++
    else upgrades.powerMultiplier += 0.15
  } else if (choiceId === 'BARRIER') {
    upgrades.barrierHp = 3
  } else if (choiceId === 'CHARGE3') {
    if (upgrades.maxChargeLevel >= 3) upgrades.powerMultiplier += 0.2
    upgrades.maxChargeLevel = 3
  } else if (choiceId === 'VITAL') {
    maxHp.value += 30
    playerHp.value = maxHp.value
    lives.value++
  }
  // 体力も少し回復して次のステージへ！
  playerHp.value = Math.min(maxHp.value, playerHp.value + 30)
  startStageFromCloudRun(currentStage.value + 1)
}

const resetFullGame = () => {
  score.value = 0
  lives.value = 3
  maxHp.value = 100
  playerHp.value = 100
  upgrades.doubleShot = false
  upgrades.groundShot = false
  upgrades.options = 0
  upgrades.barrierHp = 0
  upgrades.powerMultiplier = 1.0
  upgrades.maxChargeLevel = 2
  startStageFromCloudRun(1)
}

// 多段階チャージショット（Lv.1 → Lv.2 → Lv.3）
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

// ★ 音符バスター発射（2方向・地面這い弾・オプション連動対応！）
const fireFromPosition = (originX: number, originY: number, level: number, isOption = false) => {
  const pMul = (isOption ? 0.6 : 1.0) * upgrades.powerMultiplier
  const dir = player.facing

  const baseConfigs = [
    { speed: 7.5, radius: 9,  dmg: 10, color: '#f472b6', symbol: '♪', pierce: false },
    { speed: 9.5, radius: 14, dmg: 25, color: '#38bdf8', symbol: '♬', pierce: false },
    { speed: 12,  radius: 22, dmg: 45, color: '#facc15', symbol: '♪♬', pierce: true },
    { speed: 14,  radius: 30, dmg: 75, color: '#c084fc', symbol: '𝄞♪', pierce: true }, // Lv.3 ファイナルチャージ！
  ]
  const cfg = baseConfigs[level] || baseConfigs[0]

  // 1. 正面への音符ショット
  bullets.push({
    x: originX, y: originY, vx: dir * cfg.speed, vy: 0,
    radius: cfg.radius, damage: Math.round(cfg.dmg * pMul), color: cfg.color, noteSymbol: cfg.symbol, piercing: cfg.pierce
  })

  // 2. グラディウス風：DOUBLE（斜め上45度への対空音符ショット）
  if (upgrades.doubleShot) {
    bullets.push({
      x: originX, y: originY - 6, vx: dir * (cfg.speed * 0.8), vy: -cfg.speed * 0.55,
      radius: Math.max(8, cfg.radius * 0.8), damage: Math.round(cfg.dmg * 0.75 * pMul), color: '#fb7185', noteSymbol: '♪', piercing: cfg.pierce
    })
  }

  // 3. グラディウス風：RIPPLE（地面を這う重低音ショット）
  if (upgrades.groundShot && !isOption) {
    bullets.push({
      x: originX, y: originY + 12, vx: dir * 6.5, vy: 2.5,
      radius: 10, damage: Math.round(12 * pMul), color: '#fbbf24', noteSymbol: '━♪', isGroundCrawling: true
    })
  }
}

const fireGuitarWave = (level: number) => {
  player.shootPoseTimer = 18
  const offsetX = player.facing * 42
  const offsetY = -38
  fireFromPosition(player.x + offsetX, player.y + offsetY, level, false)

  // オプション（追従スピーカー）からも同時に音符を発射！
  for (let i = 1; i <= upgrades.options; i++) {
    const histIdx = Math.max(0, positionHistory.length - i * 14)
    const optPos = positionHistory[histIdx] || { x: player.x - player.facing * 35 * i, y: player.y }
    fireFromPosition(optPos.x, optPos.y - 35, Math.min(level, 1), true)
  }

  if (level >= 2) player.vx = -player.facing * 2.2
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

// ダメージ＆バリア防御＆残機消費ロジック
const damagePlayer = (amount: number) => {
  if (player.invincibleTimer > 0 || gameResult.value) return

  // バリアがあればダメージを完全無効化！
  if (upgrades.barrierHp > 0) {
    upgrades.barrierHp--
    player.invincibleTimer = 40
    return
  }

  playerHp.value = Math.max(0, playerHp.value - amount)
  player.invincibleTimer = 55
  player.vy = -2.5

  // HPが0になったら残機を1つ減らしてその場で復活！
  if (playerHp.value <= 0) {
    lives.value--
    if (lives.value > 0) {
      playerHp.value = maxHp.value
      player.invincibleTimer = 110 // 復活時は長めの無敵時間
      player.vy = -4.0
    } else {
      gameResult.value = 'GAMEOVER'
      stageAbortController?.abort()
    }
  }
}

const updateAndDraw = (now: number) => {
  animFrameId = requestAnimationFrame(updateAndDraw)

  const elapsed = now - lastFrameTime
  if (elapsed < 15) return
  lastFrameTime = now

  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')!

  const prevY = player.y

  // --- プレイヤーの横移動と壁（Wall）の衝突判定 ---
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

  let nextX = Math.max(40, Math.min(760, player.x + player.vx))
  for (const obs of obstacles.value) {
    if (obs.type === 'wall' && player.y > obs.y + 4) {
      // ジャンプしないと越えられない壁の横ブロック判定
      if (nextX + 18 > obs.x && nextX - 18 < obs.x + obs.w) {
        if (player.vx > 0) nextX = obs.x - 18
        else if (player.vx < 0) nextX = obs.x + obs.w + 18
        player.vx = 0
      }
    }
  }
  player.x = nextX

  // --- 縦移動（重力）と地面・壁の上・空中床への着地判定 ---
  player.vy += PHYSICS.GRAVITY
  player.y += player.vy
  let landed = false

  for (const obs of obstacles.value) {
    const withinX = player.x + 16 > obs.x && player.x - 16 < obs.x + obs.w
    if (withinX && player.vy >= 0 && prevY <= obs.y + 4 && player.y >= obs.y) {
      player.y = obs.y
      player.vy = 0
      landed = true
    }
  }

  if (player.y >= GROUND_Y) {
    player.y = GROUND_Y
    player.vy = 0
    landed = true
  }

  if (landed) {
    if (!player.onGround) { player.scaleX = 1.18; player.scaleY = 0.82 }
    player.onGround = true
  } else {
    player.onGround = false
  }

  // オプション追従用の履歴更新
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
  // 1. ステージ背景＆地面＆障害物（壁・床）の描画
  // ==========================================
  const skyGrad = ctx.createLinearGradient(0, 0, 0, GROUND_Y)
  skyGrad.addColorStop(0, currentTheme.skyGradient[0])
  skyGrad.addColorStop(0.5, currentTheme.skyGradient[1])
  skyGrad.addColorStop(1, currentTheme.skyGradient[2])
  ctx.fillStyle = skyGrad
  ctx.fillRect(0, 0, canvas.width, GROUND_Y)

  // 星のスクロール
  ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'
  bgStars.forEach(s => {
    s.x = (s.x - s.speed + 800) % 800
    ctx.fillRect(s.x, s.y, s.size, s.size)
  })

  // 遠景のイコライザー都市シルエット
  bgScrollX = (bgScrollX + 0.3) % 55
  ctx.fillStyle = 'rgba(15, 23, 42, 0.55)'
  bgBuildings.forEach(b => {
    const bx = (b.x - bgScrollX + 880) % 880 - 55
    ctx.fillRect(bx, GROUND_Y - b.h, b.w, b.h)
  })

  // 地面とサイバーグリッド
  ctx.fillStyle = currentTheme.groundColor
  ctx.fillRect(0, GROUND_Y, canvas.width, canvas.height - GROUND_Y)
  ctx.strokeStyle = currentTheme.lineColor
  ctx.lineWidth = 3
  ctx.beginPath(); ctx.moveTo(0, GROUND_Y); ctx.lineTo(canvas.width, GROUND_Y); ctx.stroke()

  // ジャンプで越える壁（アンプブロック）と空中床の描画
  for (const obs of obstacles.value) {
    ctx.save()
    if (obs.type === 'wall') {
      ctx.fillStyle = '#1e293b'
      ctx.fillRect(obs.x, obs.y, obs.w, obs.h)
      ctx.strokeStyle = currentTheme.lineColor
      ctx.lineWidth = 2
      ctx.strokeRect(obs.x, obs.y, obs.w, obs.h)
      // スピーカー風の網目模様
      ctx.fillStyle = '#0f172a'
      ctx.beginPath()
      ctx.arc(obs.x + obs.w / 2, obs.y + obs.h / 2, obs.w * 0.3, 0, Math.PI * 2)
      ctx.fill()
    } else {
      // 空中プラットフォーム（音符バー）
      ctx.fillStyle = '#334155'
      ctx.fillRect(obs.x, obs.y, obs.w, obs.h)
      ctx.fillStyle = currentTheme.lineColor
      ctx.fillRect(obs.x, obs.y, obs.w, 4)
    }
    ctx.restore()
  }

  // 残像描画
  for (let i = afterimages.length - 1; i >= 0; i--) {
    const aft = afterimages[i]
    aft.alpha -= 0.05
    if (aft.alpha <= 0) { afterimages.splice(i, 1); continue }
    drawSprite(ctx, sprites[aft.spriteKey], aft.x, aft.y, aft.facing, 96, 1, 1, aft.alpha, 190)
  }

  // グラディウス風「オプション（追従ミニスピーカー）」の描画
  for (let i = 1; i <= upgrades.options; i++) {
    const histIdx = Math.max(0, positionHistory.length - i * 14)
    const optPos = positionHistory[histIdx] || { x: player.x - player.facing * 35 * i, y: player.y }
    const floatY = Math.sin(now * 0.008 + i) * 5
    ctx.save()
    ctx.beginPath()
    ctx.arc(optPos.x, optPos.y - 35 + floatY, 11, 0, Math.PI * 2)
    ctx.fillStyle = '#38bdf8'
    ctx.shadowColor = '#38bdf8'; ctx.shadowBlur = 12
    ctx.fill()
    ctx.fillStyle = '#0f172a'
    ctx.font = 'bold 11px sans-serif'
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText('♪', optPos.x, optPos.y - 35 + floatY)
    ctx.restore()
  }

  // チャージオーラ描画
  if (chargeLevel.value > 0) {
    ctx.save()
    ctx.beginPath()
    const r = 32 + chargeLevel.value * 8 + Math.sin(now * 0.03) * 5
    ctx.arc(player.x, player.y - 42, r, 0, Math.PI * 2)
    ctx.fillStyle = chargeLevel.value === 3 ? 'rgba(192, 132, 252, 0.35)' : chargeLevel.value === 2 ? 'rgba(250, 204, 21, 0.28)' : 'rgba(56, 189, 248, 0.22)'
    ctx.fill()
    ctx.lineWidth = 2
    ctx.strokeStyle = chargeLevel.value === 3 ? '#e879f9' : chargeLevel.value === 2 ? '#facc15' : '#38bdf8'
    ctx.stroke()
    ctx.restore()
  }

  // エリカ本体の描画
  if (player.invincibleTimer % 4 < 2) {
    const slideY = player.isSliding ? 0.72 : player.scaleY
    drawSprite(ctx, sprites[getPlayerSpriteKey()], player.x, player.y, player.facing, 96, player.scaleX, slideY, 1.0, 0)
  }

  // グラディウス風「バリア（音響シールド）」の描画
  if (upgrades.barrierHp > 0) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(player.x, player.y - 42, 46, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(56, 189, 248, ${0.35 + upgrades.barrierHp * 0.2})`
    ctx.lineWidth = 3
    ctx.setLineDash([8, 6])
    ctx.stroke()
    ctx.restore()
  }

  // ==========================================
  // 2. ドロップアイテム（回復・1UP・スコア）の更新＆取得判定
  // ==========================================
  for (let i = dropItems.length - 1; i >= 0; i--) {
    const item = dropItems[i]
    item.vy += PHYSICS.GRAVITY
    item.y = Math.min(GROUND_Y - 12, item.y + item.vy)
    item.lifeTimer--

    ctx.save()
    ctx.font = 'bold 18px sans-serif'
    ctx.textAlign = 'center'
    const label = item.type === '1UP' ? '⭐1UP' : item.type === 'HEAL' ? '💚+HP' : '🎵'
    ctx.fillStyle = item.type === '1UP' ? '#facc15' : item.type === 'HEAL' ? '#4ade80' : '#f472b6'
    ctx.fillText(label, item.x, item.y)
    ctx.restore()

    // エリカが触れたら取得！
    if (Math.abs(player.x - item.x) < 34 && Math.abs((player.y - 30) - item.y) < 36) {
      if (item.type === '1UP') lives.value++
      else if (item.type === 'HEAL') playerHp.value = Math.min(maxHp.value, playerHp.value + 25)
      else score.value += 300
      dropItems.splice(i, 1)
      continue
    }
    if (item.lifeTimer <= 0) dropItems.splice(i, 1)
  }

  // ==========================================
  // 3. 敵キャラの更新（壁を自動でジャンプして越える！）
  // ==========================================
  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i]
    if (!e.isStunned) e.x += e.vx

    // 敵が壁（Wall）に近づいたら自動でジャンプして乗り越える
    for (const obs of obstacles.value) {
      if (obs.type === 'wall' && Math.abs(e.x - (obs.x + obs.w)) < 14 && e.y >= GROUND_Y) {
        e.vy = -3.9
      }
    }

    if (e.type === 'note_ghost') {
      e.y = e.baseY + Math.sin(now * 0.004 + i) * 32
    } else if (e.type !== 'mole') {
      e.vy += PHYSICS.GRAVITY
      e.y = Math.min(GROUND_Y, e.y + e.vy)
      if (e.y >= GROUND_Y) e.vy = 0
    }

    const shakeX = e.isCharging ? (Math.random() - 0.5) * 8 : 0
    const moleScaleY = e.isHidden ? 0.45 : 1.0
    const stunFlipY = e.isStunned ? -0.8 : moleScaleY
    drawSprite(ctx, sprites[e.type], e.x + shakeX, e.y, 1, 76, 1, stunFlipY, 1.0, e.hueRotate)

    if (Math.abs(player.x - e.x) < 36 && Math.abs(player.y - e.y) < 42) {
      if (player.vy > 0 && player.y < e.y - 12) {
        if (e.spiky) {
          damagePlayer(15)
        } else if (e.stompable) {
          player.vy = PHYSICS.BOUNCE_VELOCITY
          player.scaleX = 1.22; player.scaleY = 0.78
          e.hp -= Math.round(20 * upgrades.powerMultiplier)
          if (e.type === 'turtle' && e.hp > 0) e.isStunned = true
          if (e.hp <= 0) {
            onEnemyDefeated(e)
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
    boss.x = Math.max(120, Math.min(720, boss.x + boss.vx))
    boss.vy += PHYSICS.GRAVITY
    boss.y = Math.min(GROUND_Y, boss.y + boss.vy)
    if (boss.y >= GROUND_Y) boss.vy = 0

    drawSprite(ctx, sprites[boss.spriteKey], boss.x, boss.y, boss.spriteKey === 'shoot' ? -1 : 1, 96 * boss.scale, 1, 1, 0.95, boss.hueRotate)

    if (Math.abs(player.x - boss.x) < 42 && Math.abs(player.y - boss.y) < 55) {
      damagePlayer(18)
    }
  }

  // ==========================================
  // 4. 音符弾の更新＆描画（♪ / ♬ / 地面這い弾）
  // ==========================================
  for (let i = bullets.length - 1; i >= 0; i--) {
    const b = bullets[i]
    b.x += b.vx
    b.y += b.vy

    // 地面を這う弾（GROUND RIPPLE）は常に床や障害物の上を滑る
    if (b.isGroundCrawling) {
      let surfaceY = GROUND_Y - 10
      for (const obs of obstacles.value) {
        if (b.x >= obs.x && b.x <= obs.x + obs.w) {
          surfaceY = Math.min(surfaceY, obs.y - 10)
        }
      }
      b.y = surfaceY
    }

    // 音符シンボルの描画
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
            b.vx = -b.vx * 0.8; b.vy = -2
            break
          }
          const dmg = (e.armored && !b.piercing && !e.isStunned) ? Math.ceil(b.damage * 0.4) : b.damage
          e.hp -= dmg
          hit = true
          if (e.hp <= 0) {
            onEnemyDefeated(e)
            enemies.splice(j, 1)
          }
          if (!b.piercing) break
        }
      }
      if (hit && !b.piercing) { bullets.splice(i, 1); continue }

      if (boss.active && Math.abs(b.x - boss.x) < 44 && Math.abs(b.y - (boss.y - 45)) < 52) {
        boss.hp = Math.max(0, boss.hp - b.damage)
        if (!b.piercing) bullets.splice(i, 1)
        if (boss.hp <= 0) {
          boss.active = false
          boss.abortController?.abort()
          score.value += 1000 * currentStage.value
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
    if (hueRotateDeg !== 0) {
      ctx.filter = `hue-rotate(${hueRotateDeg}deg) saturate(1.3)`
    }
    ctx.drawImage(img, -size / 2, -size + 6, size, size)
  } else {
    ctx.fillStyle = hueRotateDeg ? '#38bdf8' : '#ec4899'
    ctx.fillRect(-size / 3, -size * 0.8, (size * 2) / 3, size * 0.8)
  }
  ctx.restore()
}

onMounted(async () => {
  await loadMasterJsonAsync()
  await Promise.all([loadAllSprites(), wakeUpCloudRunAsync()])
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