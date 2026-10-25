<template>
  <div class="w-full max-w-4xl mx-auto bg-slate-950 rounded-xl overflow-hidden shadow-2xl border border-slate-800 select-none font-sans">
    <!-- ==================================================== -->
    <!-- 新設計：画面を邪魔しない上部独立ダッシュボードUI -->
    <!-- ==================================================== -->
    <div class="bg-slate-900 border-b border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between gap-4">
      <!-- 左側：ステージ・残機・HPバー・チャージ状態 -->
      <div class="flex items-center gap-4">
        <div class="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-center min-w-[76px]">
          <div class="text-[10px] font-mono text-slate-400">STAGE</div>
          <div class="text-lg font-black text-pink-400 leading-none">{{ currentStage }}</div>
        </div>

        <div>
          <div class="flex items-center gap-3 mb-1">
            <span class="text-xs font-extrabold text-white tracking-wider">ERIKA</span>
            <div class="flex items-center gap-0.5 text-rose-500 text-sm" title="残機">
              <span v-for="n in lives" :key="n">♥</span>
              <span v-if="lives === 0" class="text-xs text-slate-500">LAST</span>
            </div>
            <span class="text-xs font-mono text-slate-300 ml-2">HP {{ playerHp }}/{{ maxHp }}</span>
          </div>
          <div class="w-44 h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-700 p-0.5">
            <div class="h-full rounded-full bg-gradient-to-r from-pink-500 via-rose-400 to-emerald-400 transition-all duration-150"
                 :style="{ width: `${Math.min(100, (playerHp / maxHp) * 100)}%` }"></div>
          </div>
        </div>

        <!-- チャージ段階バッジ -->
        <div class="px-3 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all"
             :class="chargeLevel === 3 ? 'bg-gradient-to-r from-pink-500 via-yellow-400 to-cyan-400 text-slate-950 border-white animate-pulse' :
                     chargeLevel === 2 ? 'bg-yellow-400 text-slate-950 border-yellow-200' :
                     chargeLevel === 1 ? 'bg-cyan-400 text-slate-950 border-cyan-200' : 'bg-slate-950 text-slate-400 border-slate-800'">
          {{ chargeLevel === 3 ? 'FINAL CHARGE!!' : chargeLevel === 2 ? 'LV.2 PIERCE' : chargeLevel === 1 ? 'LV.1 CHARGE' : 'BUSTER READY' }}
        </div>
      </div>

      <!-- 中央：装備中パワーアップアイコン -->
      <div class="flex flex-wrap gap-1 text-[10px] font-mono">
        <span class="px-2 py-1 rounded border" :class="upgrades.doubleShot ? 'bg-pink-950/80 border-pink-500 text-pink-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">2-WAY</span>
        <span class="px-2 py-1 rounded border" :class="upgrades.groundShot ? 'bg-amber-950/80 border-amber-500 text-amber-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">GROUND</span>
        <span class="px-2 py-1 rounded border" :class="upgrades.options > 0 ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">OPT×{{ upgrades.options }}</span>
        <span class="px-2 py-1 rounded border" :class="upgrades.barrierHp > 0 ? 'bg-blue-950/80 border-blue-400 text-blue-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">SHIELD:{{ upgrades.barrierHp }}</span>
        <span class="px-2 py-1 rounded border bg-slate-950 border-slate-800 text-emerald-400">ATK×{{ upgrades.powerMultiplier.toFixed(2) }}</span>
      </div>

      <!-- 右側：スコア ＆ 進行度／ボスHP切り替え表示 -->
      <div class="min-w-[190px] text-right">
        <div class="text-xs font-mono text-amber-300 font-bold mb-1">SCORE: {{ score }}</div>
        <div v-if="!boss.active">
          <div class="flex justify-between text-[10px] font-mono text-slate-400 mb-0.5">
            <span>{{ fogGate.active ? 'FOG GATE READY' : 'PROGRESS' }}</span>
            <span class="text-cyan-400 font-bold">{{ Math.min(100, Math.floor(stageProgress)) }}%</span>
          </div>
          <div class="w-full h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
            <div class="h-full bg-gradient-to-r from-cyan-500 to-pink-500 transition-all duration-150"
                 :style="{ width: `${Math.min(100, stageProgress)}%` }"></div>
          </div>
        </div>
        <div v-else>
          <div class="flex justify-between text-[10px] font-mono text-red-400 font-bold mb-0.5">
            <span class="truncate max-w-[120px]">{{ boss.name }}</span>
            <span>{{ boss.hp }}/{{ boss.maxHp }}</span>
          </div>
          <div class="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-red-900">
            <div class="h-full bg-gradient-to-r from-red-600 via-orange-500 to-yellow-400 transition-all duration-100"
                 :style="{ width: `${(boss.hp / boss.maxHp) * 100}%` }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================================================== -->
    <!-- ゲーム画面領域（Canvas ＋ 演出オーバーレイ） -->
    <!-- ==================================================== -->
    <div class="relative">
      <!-- ① ロックマン風：ステージ開始カウントダウンオーバーレイ -->
      <transition name="fade">
        <div v-if="introState.active" class="absolute inset-0 flex flex-col items-center justify-center z-20 pointer-events-none bg-black/35">
          <div class="text-pink-400 font-mono text-sm tracking-widest mb-1 animate-pulse">MISSION START</div>
          <div class="text-4xl font-black text-white tracking-wider drop-shadow-lg">STAGE {{ currentStage }} // READY?</div>
          <div class="text-xs font-mono text-cyan-300 mt-2">TELEPORTING ERIKA...</div>
        </div>
      </transition>

      <!-- ② 白い霧（ダークソウル風）案内メッセージ -->
      <div v-if="fogGate.active && !boss.active && !cutin.visible"
           class="absolute top-6 left-1/2 -translate-x-1/2 z-10 pointer-events-none px-4 py-1.5 rounded-full bg-slate-900/90 border border-slate-500 text-xs font-bold shadow-lg"
           :class="enemies.length > 0 ? 'text-amber-300' : 'text-white animate-bounce'">
        {{ enemies.length > 0 ? `⚠️ 残りの敵をすべて倒してください（残り ${enemies.length} 体）` : '🌫️ 右端の「白い霧」に触れてボス部屋へ進む →' }}
      </div>

      <!-- ③ ボス登場カットイン演出 -->
      <transition name="fade">
        <div v-if="cutin.visible" class="absolute inset-0 bg-black/80 flex items-center justify-center z-20 pointer-events-none">
          <div class="text-center p-6 border-y-2 border-pink-500 bg-slate-900/95 w-full">
            <div class="text-pink-400 text-xs font-mono tracking-widest mb-1">WARNING // {{ cutin.bossName }}</div>
            <div class="text-xl md:text-2xl font-bold text-white mb-2">「{{ cutin.quote }}」</div>
            <div class="text-xs text-slate-400">— {{ cutin.source }}</div>
          </div>
        </div>
      </transition>

      <!-- ④ ダークソウル風：死亡時「YOU DIED」ブラックアウト演出 -->
      <transition name="fade">
        <div v-if="deathOverlay.active" class="absolute inset-0 bg-black/90 flex flex-col items-center justify-center z-30 pointer-events-none">
          <div class="w-full py-6 bg-gradient-to-r from-transparent via-black to-transparent border-y border-red-900/60 text-center">
            <div class="text-5xl md:text-6xl font-serif tracking-[0.25em] text-red-600 drop-shadow-[0_0_20px_rgba(220,38,38,0.8)]">
              YOU DIED
            </div>
            <div class="text-xs font-mono text-slate-400 mt-3 tracking-widest">
              {{ deathOverlay.message }}
            </div>
          </div>
        </div>
      </transition>

      <!-- ⑤ ボス撃破時：勝利ポーズ（ピースエリカ）＋ CONGRATULATIONS ＋ 花火＆ボーナス選択 -->
      <transition name="fade">
        <div v-if="gameResult === 'CLEAR'" class="absolute inset-0 bg-slate-950/75 flex flex-col items-center justify-center z-20 p-4">
          <div class="flex items-center gap-5 mb-3 bg-slate-900/90 px-6 py-3 rounded-2xl border border-yellow-400/60 shadow-2xl">
            <img src="/sprites/victory.png" alt="Victory Erika" class="w-24 h-24 object-contain drop-shadow-[0_0_12px_rgba(244,114,182,0.8)]" />
            <div>
              <div class="text-yellow-400 text-xs font-mono tracking-widest">STAGE {{ currentStage }} COMPLETE!!</div>
              <div class="text-2xl md:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-pink-400 to-cyan-300">
                CONGRATULATIONS!!
              </div>
              <div class="text-sm font-mono text-slate-200 mt-0.5">TOTAL SCORE: <span class="text-yellow-300 font-bold">{{ score }}</span></div>
            </div>
          </div>

          <div class="text-xs font-bold text-pink-300 mb-2">▼ クリアボーナス：強化する武装を1つ選んで次のステージへ ▼</div>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-2.5 w-full max-w-2xl">
            <button v-for="item in bonusChoices" :key="item.id"
                    @click="selectBonusAndNextStage(item.id)"
                    class="flex flex-col items-start p-2.5 rounded-lg border border-slate-700 bg-slate-900/95 hover:bg-pink-950/80 hover:border-pink-400 transition text-left group">
              <div class="text-xs font-bold text-pink-400 group-hover:text-yellow-300">{{ item.title }}</div>
              <div class="text-[11px] text-slate-300 mt-0.5">{{ item.desc }}</div>
            </button>
          </div>
        </div>
      </transition>

      <!-- ⑥ ゲームオーバー（残機ゼロ）画面 -->
      <div v-if="gameResult === 'GAMEOVER'" class="absolute inset-0 bg-black/90 flex flex-col items-center justify-center z-30">
        <div class="text-5xl font-serif tracking-[0.2em] text-red-600 mb-2">YOU DIED</div>
        <div class="text-slate-400 font-mono text-sm mb-6">FINAL SCORE: {{ score }} (REACHED STAGE {{ currentStage }})</div>
        <div class="flex gap-4">
          <button v-if="checkpointReachedBossGate" @click="retryFromCheckpoint"
                  class="px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg shadow-lg transition">
            ボス直前（白い霧）からコンティニュー
          </button>
          <button @click="resetFullGame"
                  class="px-5 py-2.5 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded-lg shadow-lg transition">
            STAGE 1 から再挑戦する
          </button>
        </div>
      </div>

      <!-- メインゲームCanvas -->
      <canvas ref="canvasRef" width="800" height="450" class="block w-full h-auto"></canvas>
    </div>

    <!-- ==================================================== -->
    <!-- 下部操作ガイド（十字キー上下対応＆ダッシュ表記） -->
    <!-- ==================================================== -->
    <div class="bg-slate-900 px-4 py-2.5 flex flex-wrap justify-between items-center gap-2 text-xs text-slate-300 border-t border-slate-800">
      <div class="flex flex-wrap gap-3">
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">←</kbd> <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">→</kbd> 移動</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">↑</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Z</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Space</kbd> ジャンプ</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">↓</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">C</kbd> ダッシュ</span>
        <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">X</kbd> 音符ショット（長押しチャージ）</span>
      </div>
      <button @click="resetFullGame" :disabled="isLoadingStage"
              class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-600 transition">
        STAGE 1 リスタート
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'

const API_BASE = import.meta.env.VITE_API_URL || 'https://erika-action-api-xxxxxxxxxx-an.a.run.app'

// 0.8倍スケール化＆地面を1/10（Y=408）へ下げて画面を広々させる設定
const GROUND_Y = 408
const CHAR_SCALE = 0.8 // 味方も敵も0.8倍サイズに統一！

const PHYSICS = {
  MOVE_ACCEL: 0.42,
  MOVE_MAX_SPEED: 3.5,
  FRICTION: 0.82,
  JUMP_VELOCITY: -4.7,
  GRAVITY: 0.075,
  DASH_SPEED: 6.8,
  BOUNCE_VELOCITY: -4.3,
}

const canvasRef = ref<HTMLCanvasElement | null>(null)
const maxHp = ref(100)
const playerHp = ref(100)
const lives = ref(3)
const score = ref(0)
const chargeLevel = ref(0)
const isLoadingStage = ref(false)
const currentStage = ref(1)
const stageProgress = ref(0)
const gameResult = ref<'CLEAR' | 'GAMEOVER' | null>(null)

// ボス直前（白い霧）のチェックポイント到達フラグ
const checkpointReachedBossGate = ref(false)

// ロックマン風ステージ開始演出ステート
const introState = reactive({ active: false, beamY: -50 })
// ダークソウル風白い霧ステート
const fogGate = reactive({ active: false, x: 765, transitioning: false })
// YOU DIED 演出ステート
const deathOverlay = reactive({ active: false, message: '' })

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
  { id: 'BARRIER', title: '🛡️ 音響フォースバリア', desc: '敵の弾や体当たりを3回まで無効化するシールドを展開！' },
  { id: 'CHARGE3', title: '⚡ ファイナルチャージ解放 (Lv.3)', desc: upgrades.maxChargeLevel >= 3 ? '取得済（選ぶと攻撃力+25%）' : '壁も貫通する3段階目の極太サウンドブラスター解放！' },
  { id: 'VITAL',   title: '💖 最大HP+30 ＆ 全回復 ＆ 1UP', desc: '最大体力を増やし、HP全回復＋残機を1つ増やす！' },
])

const cutin = reactive({ visible: false, bossName: '', quote: '', source: '' })

// マスタデータ（ボスHPを前回の4/5に調整＆新ボス5体追加で計11体！）
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
    { type: 'hedgehog',   name: '赤いハリネズミ', sprite: '/sprites/enemies/hedgehog.png',   hp: 55, speed: 3.6, score: 400, stompable: false, spiky: true,   wallAction: 'jump' },
  ],
  bosses: [
    { id: 'knight',    name: 'BLACK KNIGHT ERIKA', sprite: '/sprites/bosses/boss_knight.png',    baseHp: 960,  scale: 1.2, pattern: 'KNIGHT' },
    { id: 'concierge', name: 'KEY MASTER ERIKA',   sprite: '/sprites/bosses/boss_concierge.png', baseHp: 880,  scale: 1.2, pattern: 'CONCIERGE' },
    { id: 'yukata',    name: 'SUNFLOWER YUKATA',   sprite: '/sprites/bosses/boss_yukata.png',    baseHp: 920,  scale: 1.2, pattern: 'YUKATA' },
    { id: 'ivory',     name: 'IVORY COMMANDER',    sprite: '/sprites/bosses/boss_ivory.png',     baseHp: 950,  scale: 1.2, pattern: 'IVORY' },
    { id: 'tea',       name: 'MINT TEA MASTER',    sprite: '/sprites/bosses/boss_tea.png',       baseHp: 980,  scale: 1.2, pattern: 'TEA' },
    { id: 'kimono',    name: 'GRIMOIRE KIMONO',    sprite: '/sprites/bosses/boss_kimono.png',    baseHp: 1000, scale: 1.2, pattern: 'KIMONO' },
    { id: 'flower',    name: 'FLORA PRINCESS',     sprite: '/sprites/bosses/boss_flower.png',    baseHp: 1040, scale: 1.2, pattern: 'FLOWER' },
    { id: 'camellia',  name: 'CAMELLIA SHRINE',    sprite: '/sprites/bosses/boss_camellia.png',  baseHp: 1060, scale: 1.2, pattern: 'CAMELLIA' },
    { id: 'dress',     name: 'NAVY DRESS DIVA',    sprite: '/sprites/bosses/boss_dress.png',     baseHp: 1080, scale: 1.2, pattern: 'DRESS' },
    { id: 'gothic',    name: 'BLACK ROSE GOTHIC',  sprite: '/sprites/bosses/boss_gothic.png',    baseHp: 1150, scale: 1.2, pattern: 'GOTHIC' },
    { id: 'queen',     name: 'PEARL THRONE QUEEN', sprite: '/sprites/bosses/boss_queen.png',     baseHp: 1280, scale: 1.25,pattern: 'QUEEN' },
  ],
  stages: [
    { stage: 1, skyGradient: ['#0f172a', '#311042', '#701a75'], groundColor: '#1e1b4b', lineColor: '#ec4899', scrollSpeed: 1.4 },
    { stage: 2, skyGradient: ['#020617', '#0f2942', '#065f46'], groundColor: '#064e3b', lineColor: '#34d399', scrollSpeed: 1.6 },
    { stage: 3, skyGradient: ['#180404', '#450a0a', '#7c2d12'], groundColor: '#270909', lineColor: '#f97316', scrollSpeed: 1.8 },
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
    hurt: '/sprites/hurt.png',       // ★追加：ダメージのけぞり絵
    victory: '/sprites/victory.png', // ★追加：勝利ピース絵
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

const player = {
  x: 130, y: GROUND_Y, vx: 0, vy: 0, facing: 1 as 1 | -1,
  onGround: true, shootPoseTimer: 0, hurtPoseTimer: 0, isDashing: false, invincibleTimer: 0,
  scaleX: 1, scaleY: 1, runAnimTimer: 0, controlLocked: false
}
const positionHistory: { x: number; y: number }[] = []

interface Obstacle { x: number; y: number; w: number; h: number; type: 'wall' | 'platform' }
interface Pit { x: number; w: number }
const obstacles = ref<Obstacle[]>([])
const pits = ref<Pit[]>([])

const currentTheme = reactive({
  skyGradient: ['#0f172a', '#311042', '#701a75'],
  groundColor: '#1e1b4b',
  lineColor: '#ec4899',
  scrollSpeed: 1.4,
  enemyHue: 0,
  isScrolling: false,
})

interface Bullet {
  x: number; y: number; vx: number; vy: number; gravity?: number
  radius: number; damage: number; color: string
  noteSymbol: string; piercing?: boolean; isGroundCrawling?: boolean; isEnemy?: boolean
}
interface DropItem { x: number; y: number; vy: number; type: 'HEAL' | '1UP' | 'SCORE'; lifeTimer: number }
interface FloatingText { x: number; y: number; text: string; color: string; alpha: number }
interface FireworkParticle { x: number; y: number; vx: number; vy: number; color: string; alpha: number }
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
const floatingTexts: FloatingText[] = []
const fireworks: FireworkParticle[] = []
const enemies: Enemy[] = []
const afterimages: { x: number; y: number; facing: number; alpha: number; spriteKey: string }[] = []
let stageAbortController: AbortController | null = null
let screenShakeTimer = 0

const boss = reactive({
  active: false, id: 'knight', name: '', spriteKey: 'boss_knight',
  x: 660, y: GROUND_Y, vx: 0, vy: 0,
  hp: 960, maxHp: 960, scale: 1.2, pattern: 'KNIGHT',
  isFloating: false, warningLaserY: null as number | null, warningSpikeX: null as number | null,
  abortController: null as AbortController | null
})

const bgStars = Array.from({ length: 35 }, () => ({
  x: Math.random() * 800, y: Math.random() * 300, size: Math.random() * 2 + 1, speed: Math.random() * 0.3 + 0.1
}))
const bgBuildings = Array.from({ length: 16 }, (_, i) => ({
  x: i * 55, w: 42, h: 55 + (i * 37) % 105
}))
let bgScrollX = 0

// 花火を打ち上げるヘルパー関数
const spawnFireworkBurst = () => {
  const cx = 120 + Math.random() * 560
  const cy = 70 + Math.random() * 180
  const colors = ['#f472b6', '#facc15', '#38bdf8', '#4ade80', '#c084fc', '#fb7185']
  const color = colors[Math.floor(Math.random() * colors.length)]
  for (let i = 0; i < 28; i++) {
    const angle = (Math.PI * 2 * i) / 28
    const spd = 1.5 + Math.random() * 3.2
    fireworks.push({ x: cx, y: cy, vx: Math.cos(angle) * spd, vy: Math.sin(angle) * spd, color, alpha: 1.0 })
  }
}

// ====================================================
// 右端からギミック（落とし穴・空中床・壁）を生み出す非同期ジェネレーター
// ====================================================
const runGimmickSpawnerAsync = async (stageSignal: AbortSignal) => {
  try {
    while (currentTheme.isScrolling && stageProgress.value < 90) {
      const roll = Math.random()
      const spawnX = 840

      if (roll < 0.32) {
        const pitWidth = 125 + Math.random() * 40
        pits.value.push({ x: spawnX, w: pitWidth })
        obstacles.value.push({ x: spawnX + 15, y: GROUND_Y - 85, w: pitWidth - 25, h: 14, type: 'platform' })
      } else if (roll < 0.60) {
        const wallH = 44 + Math.random() * 22
        obstacles.value.push({ x: spawnX, y: GROUND_Y - wallH, w: 40, h: wallH, type: 'wall' })
      } else if (roll < 0.82) {
        obstacles.value.push({ x: spawnX - 90, y: GROUND_Y - 75, w: 70, h: 14, type: 'platform' })
        obstacles.value.push({ x: spawnX, y: GROUND_Y - 105, w: 42, h: 105, type: 'wall' })
      } else {
        pits.value.push({ x: spawnX + 20, w: 90 })
        obstacles.value.push({ x: spawnX, y: GROUND_Y - 70, w: 80, h: 14, type: 'platform' })
        obstacles.value.push({ x: spawnX + 95, y: GROUND_Y - 130, w: 85, h: 14, type: 'platform' })
      }
      await waitAsync(2400, stageSignal)
    }
  } catch {}
}

// ====================================================
// ★ ロックマン風：5秒間のステージ開始＆上空テレポート登場演出
// ====================================================
const playMegamanIntroAsync = async (stageSignal: AbortSignal) => {
  introState.active = true
  introState.beamY = -60
  player.controlLocked = true
  player.x = 130
  player.y = -60

  // 約2.2秒間：STAGE X READY 表示中に上空からテレポートビームが落下
  const steps = 35
  for (let i = 0; i <= steps; i++) {
    introState.beamY = (GROUND_Y * i) / steps
    player.y = introState.beamY
    await waitAsync(45, stageSignal)
  }
  player.y = GROUND_Y
  player.scaleX = 1.25; player.scaleY = 0.75 // 着地時のスクワッシュ演出
  await waitAsync(1800, stageSignal) // 合計約4.5〜5秒間の開始ターン
  introState.active = false
  player.controlLocked = false
}

// ステージ開始制御（fromBossGateCheckpoint = true なら白い霧の前から即再開！）
const startStageFromCloudRun = async (stageNum: number, fromBossGateCheckpoint = false) => {
  isLoadingStage.value = true
  gameResult.value = null
  currentStage.value = stageNum
  if (!fromBossGateCheckpoint) {
    stageProgress.value = 0
    checkpointReachedBossGate.value = false
  } else {
    stageProgress.value = 100
  }

  stageAbortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  enemies.length = 0; bullets.length = 0; dropItems.length = 0; fireworks.length = 0
  obstacles.value = []; pits.value = []
  boss.active = false; boss.warningLaserY = null; boss.warningSpikeX = null
  fogGate.active = false; fogGate.transitioning = false
  boss.abortController?.abort()

  const stg = masterData.stages[(stageNum - 1) % masterData.stages.length]
  currentTheme.skyGradient = stg.skyGradient
  currentTheme.groundColor = stg.groundColor
  currentTheme.lineColor = stg.lineColor
  currentTheme.scrollSpeed = stg.scrollSpeed + (stageNum - 1) * 0.1
  currentTheme.enemyHue = (stageNum - 1) * 55
  currentTheme.isScrolling = false

  player.x = 130; player.y = GROUND_Y; player.vx = 0; player.vy = 0; player.facing = 1

  stageAbortController = new AbortController()
  const stageSignal = stageAbortController.signal

  try {
    await fetch(`${API_BASE}/api/stage-start?stage=${stageNum}`)
  } catch {} finally {
    isLoadingStage.value = false
  }

  try {
    // 1. ロックマン風の上空テレポート登場演出を実行！
    await playMegamanIntroAsync(stageSignal)

    if (!fromBossGateCheckpoint) {
      // 2. 道中パート開始（強制スクロール＆ギミック生成）
      currentTheme.isScrolling = true
      runGimmickSpawnerAsync(stageSignal)

      const hpMul = 1 + (stageNum - 1) * 0.25
      const spdMul = 1 + Math.min(0.5, (stageNum - 1) * 0.07)

      let count = 0
      while (stageProgress.value < 96) {
        const tmpl = masterData.enemies[(count + stageNum) % masterData.enemies.length]
        spawnSingleEnemy({
          id: `stg${stageNum}_e${count}`,
          ...tmpl,
          hp: Math.round(tmpl.hp * hpMul),
          speed: tmpl.speed * spdMul
        }, stageSignal)
        count++
        stageProgress.value = Math.min(100, stageProgress.value + 12)
        await waitAsync(Math.max(1600, 2500 - stageNum * 120), stageSignal)
      }
    }

    // ====================================================
    // ★ 3. ボス部屋前：横スクロール停止 ＆ 右端に「白い霧（ダークソウル風）」出現！
    // ====================================================
    stageProgress.value = 100
    currentTheme.isScrolling = false
    checkpointReachedBossGate.value = true // チェックポイント記録（ボス戦でやられたらここから再開！）
    fogGate.active = true
    fogGate.x = 765
  } catch {}
}

// プレイヤーが敵を全滅させた状態で「白い霧」に触れた時のスクロール＆ボス登場遷移
const enterFogGateTransitionAsync = async () => {
  if (fogGate.transitioning || boss.active) return
  fogGate.transitioning = true
  player.controlLocked = true
  player.vx = 0

  const stageSignal = stageAbortController!.signal
  try {
    // 画面がスーッと右へスクロールして既存の床や穴が左へ流れ去り、エリカが左端定位置へ移動
    for (let i = 0; i < 45; i++) {
      obstacles.value.forEach(o => { o.x -= 12 })
      pits.value.forEach(p => { p.x -= 12 })
      player.x = Math.max(120, player.x - 13)
      bgScrollX = (bgScrollX + 8) % 55
      await waitAsync(20, stageSignal)
    }
    obstacles.value = [
      { x: 240, y: GROUND_Y - 75, w: 95, h: 14, type: 'platform' },
      { x: 460, y: GROUND_Y - 75, w: 95, h: 14, type: 'platform' }
    ]
    pits.value = []
    fogGate.active = false
    fogGate.transitioning = false

    const bossTmpl = masterData.bosses[(currentStage.value - 1) % masterData.bosses.length]
    const quoteObj = masterData.quotes[(currentStage.value - 1) % masterData.quotes.length]

    await startBossBattleAsync({
      ...bossTmpl,
      hp: Math.round(bossTmpl.baseHp * (1 + (currentStage.value - 1) * 0.2)),
      cutin_quote: quoteObj
    }, stageSignal)
  } catch {} finally {
    player.controlLocked = false
  }
}

const spawnSingleEnemy = (wave: any, stageSignal: AbortSignal) => {
  const enemyAbort = new AbortController()
  stageSignal.addEventListener('abort', () => enemyAbort.abort())

  const isFlying = wave.type === 'note_ghost'
  const startY = isFlying ? 230 : GROUND_Y

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
          enemy.vx = -1.4; await waitAsync(1300, signal)
          enemy.vx = 0; enemy.isCharging = true; await waitAsync(550, signal)
          enemy.isCharging = false
          enemy.vx = player.x < enemy.x ? -5.0 : 4.2
          await waitAsync(900, signal)
        }
      } else if (enemy.type === 'mole') {
        while (enemy.hp > 0) {
          enemy.isHidden = true; await waitAsync(1400, signal)
          enemy.isHidden = false
          const dir = player.x < enemy.x ? -1 : 1
          bullets.push({ x: enemy.x + dir * 18, y: enemy.y - 22, vx: dir * 4.4, vy: 0, radius: 7, damage: 14, color: '#f59e0b', noteSymbol: '●', isEnemy: true })
          await waitAsync(1300, signal)
        }
      } else if (enemy.type === 'jelly') {
        while (enemy.hp > 0) {
          if (enemy.vy === 0) enemy.vy = -3.8
          await waitAsync(1500, signal)
        }
      } else if (enemy.type === 'note_ghost') {
        while (enemy.hp > 0) {
          await waitAsync(1900, signal)
          const dx = player.x - enemy.x
          const dy = (player.y - 28) - (enemy.y - 20)
          const dist = Math.hypot(dx, dy) || 1
          bullets.push({
            x: enemy.x - 12, y: enemy.y - 20,
            vx: (dx / dist) * 4.0, vy: (dy / dist) * 4.0,
            radius: 8, damage: 12, color: '#c084fc', noteSymbol: '♪', isEnemy: true
          })
        }
      }
    } catch {}
  })()
}

// ====================================================
// ★ 全11体の「ちびエリカ・ボス」専用攻撃AI（新ボス5体対応！）
// ====================================================
const fireAimedShot = (fromX: number, fromY: number, speed: number, color: string, symbol = '♪', spreadRad = 0) => {
  const dx = player.x - fromX
  const dy = (player.y - 30) - fromY
  const baseAngle = Math.atan2(dy, dx) + spreadRad
  bullets.push({
    x: fromX, y: fromY,
    vx: Math.cos(baseAngle) * speed, vy: Math.sin(baseAngle) * speed,
    radius: 9, damage: 15, color, noteSymbol: symbol, isEnemy: true
  })
}

const startBossBattleAsync = async (bossData: any, stageSignal: AbortSignal) => {
  cutin.bossName = `${bossData.name} // STAGE ${currentStage.value}`
  cutin.quote = bossData.cutin_quote.quote
  cutin.source = bossData.cutin_quote.source
  cutin.visible = true
  await waitAsync(2200, stageSignal)
  cutin.visible = false
  player.controlLocked = false

  boss.id = bossData.id
  boss.name = bossData.name
  boss.spriteKey = `boss_${bossData.id}`
  boss.maxHp = bossData.hp
  boss.hp = bossData.hp
  boss.scale = bossData.scale
  boss.pattern = bossData.pattern
  boss.x = 660; boss.y = GROUND_Y; boss.vx = 0; boss.vy = 0
  boss.isFloating = false; boss.warningLaserY = null; boss.warningSpikeX = null
  boss.active = true

  boss.abortController = new AbortController()
  stageSignal.addEventListener('abort', () => boss.abortController?.abort())
  const { signal } = boss.abortController

  try {
    while (boss.active && boss.hp > 0) {
      if (boss.pattern === 'KNIGHT') {
        boss.vx = 0
        for (let i = 0; i < 2; i++) {
          bullets.push({ x: boss.x - 24, y: GROUND_Y - 10, vx: -5.8, vy: 0, radius: 11, damage: 16, color: '#ef4444', noteSymbol: '⚔', isGroundCrawling: true, isEnemy: true })
          fireAimedShot(boss.x - 20, boss.y - 36, 5.0, '#f87171', '♪')
          await waitAsync(450, signal)
        }
        boss.vy = -4.1; boss.vx = player.x < boss.x ? -5.8 : 5.8
        await waitAsync(900, signal)
        boss.vx = 0; await waitAsync(600, signal)

      } else if (boss.pattern === 'CONCIERGE') {
        const warpSpots = [660, 230, 450, 580]
        boss.x = warpSpots[Math.floor(Math.random() * warpSpots.length)]
        boss.vy = -3.2; await waitAsync(450, signal)
        for (let i = 0; i < 4; i++) {
          fireAimedShot(boss.x, boss.y - 35, 5.8, '#facc15', '🗝')
          await waitAsync(200, signal)
        }
        await waitAsync(850, signal)

      } else if (boss.pattern === 'YUKATA') {
        boss.vy = -4.9; boss.vx = player.x < boss.x ? -2.8 : 2.8
        await waitAsync(650, signal)
        boss.vx = 0
        for (let a = -3; a <= 3; a++) fireAimedShot(boss.x, boss.y - 35, 4.4, '#fbbf24', '✿', a * 0.24)
        await waitAsync(1100, signal)

      } else if (boss.pattern === 'IVORY') {
        // 🤺 【新ボス：象牙ジャケット】高速レイピア3連ステップ突進＆クロスショット
        for (let step = 0; step < 3; step++) {
          boss.vx = player.x < boss.x ? -6.5 : 6.5
          fireAimedShot(boss.x, boss.y - 35, 5.5, '#fef08a', '✦')
          await waitAsync(320, signal)
          boss.vx = 0; await waitAsync(220, signal)
        }
        boss.vy = -4.4; boss.vx = boss.x < 400 ? 4.5 : -4.5
        await waitAsync(900, signal); boss.vx = 0

      } else if (boss.pattern === 'TEA') {
        // ☕ 【新ボス：ミントチャイナ】山なりに跳ねるティーカップ弾＆癒やしの緑波
        for (let i = 0; i < 3; i++) {
          const dir = player.x < boss.x ? -1 : 1
          bullets.push({
            x: boss.x + dir * 20, y: boss.y - 45,
            vx: dir * (3.2 + i * 1.4), vy: -4.2, gravity: 0.08,
            radius: 11, damage: 15, color: '#34d399', noteSymbol: '☕', isEnemy: true
          })
          await waitAsync(280, signal)
        }
        boss.vy = -3.8; boss.vx = boss.x > 450 ? -3.2 : 3.2
        await waitAsync(1000, signal); boss.vx = 0

      } else if (boss.pattern === 'FLOWER') {
        // 🌸 【新ボス：花飾りドレス】空から降り注ぐフラワーシャワー弾幕
        boss.vy = -4.5; await waitAsync(600, signal)
        for (let i = 0; i < 6; i++) {
          bullets.push({
            x: 100 + i * 115 + (Math.random() * 30 - 15), y: 20,
            vx: (Math.random() - 0.5) * 1.2, vy: 2.8,
            radius: 10, damage: 14, color: '#f472b6', noteSymbol: '❀', isEnemy: true
          })
        }
        fireAimedShot(boss.x, boss.y - 35, 4.8, '#a7f3d0', '♪')
        await waitAsync(1200, signal)

      } else if (boss.pattern === 'CAMELLIA') {
        // 🌺 【新ボス：椿と正座】全方位の椿結界展開 ＆ 居合の一閃レーザー
        for (let a = 0; a < 8; a++) {
          const rad = (Math.PI * 2 * a) / 8
          bullets.push({
            x: boss.x, y: boss.y - 35,
            vx: Math.cos(rad) * 4.2, vy: Math.sin(rad) * 4.2,
            radius: 10, damage: 15, color: '#fb7185', noteSymbol: '🌺', isEnemy: true
          })
        }
        await waitAsync(650, signal)
        boss.warningLaserY = GROUND_Y - 26
        await waitAsync(600, signal)
        boss.warningLaserY = null
        const dir = player.x < boss.x ? -1 : 1
        for (let k = 0; k < 6; k++) {
          bullets.push({ x: boss.x + dir * 25, y: GROUND_Y - 26, vx: dir * 11, vy: 0, radius: 13, damage: 20, color: '#e11d48', noteSymbol: '━', isEnemy: true })
          await waitAsync(55, signal)
        }
        await waitAsync(950, signal)

      } else if (boss.pattern === 'GOTHIC') {
        // 🥀 【新ボス：黒薔薇ゴシック】エリカの足元から突き出す黒薔薇の茨＋ゴシック弾
        for (let i = 0; i < 3; i++) {
          boss.warningSpikeX = player.x
          await waitAsync(520, signal)
          const spikeX = boss.warningSpikeX
          boss.warningSpikeX = null
          if (spikeX !== null) {
            bullets.push({ x: spikeX, y: GROUND_Y, vx: 0, vy: -5.5, radius: 14, damage: 18, color: '#a855f7', noteSymbol: '🥀', isEnemy: true })
          }
          fireAimedShot(boss.x, boss.y - 35, 5.0, '#c084fc', '†')
          await waitAsync(350, signal)
        }
        boss.vy = -4.0; boss.vx = boss.x > 450 ? -3.8 : 3.8
        await waitAsync(900, signal); boss.vx = 0

      } else if (boss.pattern === 'KIMONO') {
        const heights = [GROUND_Y - 16, GROUND_Y - 60, GROUND_Y - 110]
        for (const h of heights) {
          const dir = player.x < boss.x ? -1 : 1
          bullets.push({ x: boss.x + dir * 20, y: h, vx: dir * 6.0, vy: 0, radius: 11, damage: 15, color: '#a855f7', noteSymbol: '۞', isEnemy: true })
          await waitAsync(260, signal)
        }
        if (enemies.length < 2) {
          const summonTmpl = masterData.enemies[Math.floor(Math.random() * 3)]
          spawnSingleEnemy({ ...summonTmpl, id: `summon_${Date.now()}` }, signal)
        }
        boss.vy = -3.8; boss.vx = boss.x > 450 ? -3.2 : 3.2
        await waitAsync(900, signal); boss.vx = 0

      } else if (boss.pattern === 'DRESS') {
        boss.isFloating = true; boss.vy = -2.4
        for (let i = 0; i < 5; i++) {
          fireAimedShot(boss.x, boss.y - 35, 5.0, '#38bdf8', '♬', Math.sin(i) * 0.3)
          await waitAsync(220, signal)
        }
        boss.vx = (player.x - boss.x) * 0.08
        await waitAsync(600, signal)
        boss.isFloating = false; boss.vx = 0; boss.vy = 6.0
        await waitAsync(600, signal)
        bullets.push({ x: boss.x - 18, y: GROUND_Y - 10, vx: -6.0, vy: 0, radius: 11, damage: 16, color: '#60a5fa', noteSymbol: '🌊', isGroundCrawling: true, isEnemy: true })
        bullets.push({ x: boss.x + 18, y: GROUND_Y - 10, vx: 6.0, vy: 0, radius: 11, damage: 16, color: '#60a5fa', noteSymbol: '🌊', isGroundCrawling: true, isEnemy: true })
        await waitAsync(900, signal)

      } else {
        for (let a = -2; a <= 2; a++) fireAimedShot(boss.x - 20, boss.y - 38, 4.6, '#f472b6', '○', a * 0.22)
        await waitAsync(700, signal)
        const targetY = Math.min(GROUND_Y - 22, Math.max(180, player.y - 25))
        boss.warningLaserY = targetY
        await waitAsync(650, signal)
        boss.warningLaserY = null
        const dir = player.x < boss.x ? -1 : 1
        for (let k = 0; k < 7; k++) {
          bullets.push({ x: boss.x + dir * 25, y: targetY, vx: dir * 11, vy: 0, radius: 14, damage: 20, color: '#fde047', noteSymbol: '★', isEnemy: true })
          await waitAsync(55, signal)
        }
        boss.vy = -3.8; boss.vx = boss.x > 450 ? -3.0 : 3.0
        await waitAsync(950, signal); boss.vx = 0
      }
    }
  } catch {}
}

const onEnemyDefeated = (e: Enemy) => {
  score.value += e.score
  e.abortController.abort()
  const roll = Math.random()
  if (roll < 0.07) dropItems.push({ x: e.x, y: e.y - 16, vy: -2.6, type: '1UP', lifeTimer: 450 })
  else if (roll < 0.38) dropItems.push({ x: e.x, y: e.y - 16, vy: -2.4, type: 'HEAL', lifeTimer: 450 })
  else if (roll < 0.65) dropItems.push({ x: e.x, y: e.y - 16, vy: -2.4, type: 'SCORE', lifeTimer: 450 })
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
  startStageFromCloudRun(currentStage.value + 1, false)
}

const retryFromCheckpoint = () => {
  lives.value = 3
  playerHp.value = maxHp.value
  startStageFromCloudRun(currentStage.value, true)
}

const resetFullGame = () => {
  score.value = 0; lives.value = 3; maxHp.value = 100; playerHp.value = 100
  upgrades.doubleShot = false; upgrades.groundShot = false; upgrades.options = 0
  upgrades.barrierHp = 0; upgrades.powerMultiplier = 1.0; upgrades.maxChargeLevel = 2
  startStageFromCloudRun(1, false)
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
    { speed: 7.5, radius: 8,  dmg: 12, color: '#f472b6', symbol: '♪', pierce: false },
    { speed: 9.5, radius: 12, dmg: 28, color: '#38bdf8', symbol: '♬', pierce: false },
    { speed: 12,  radius: 18, dmg: 52, color: '#facc15', symbol: '♪♬', pierce: true },
    { speed: 14,  radius: 24, dmg: 85, color: '#c084fc', symbol: '𝄞♪', pierce: true },
  ]
  const cfg = baseConfigs[level] || baseConfigs[0]

  bullets.push({
    x: originX, y: originY, vx: dir * cfg.speed, vy: 0,
    radius: cfg.radius, damage: Math.round(cfg.dmg * pMul), color: cfg.color, noteSymbol: cfg.symbol, piercing: cfg.pierce
  })

  if (upgrades.doubleShot) {
    bullets.push({
      x: originX, y: originY - 5, vx: dir * (cfg.speed * 0.8), vy: -cfg.speed * 0.55,
      radius: Math.max(7, cfg.radius * 0.8), damage: Math.round(cfg.dmg * 0.75 * pMul), color: '#fb7185', noteSymbol: '♪', piercing: cfg.pierce
    })
  }

  if (upgrades.groundShot && !isOption) {
    bullets.push({
      x: originX, y: originY + 10, vx: dir * 6.5, vy: 2.5,
      radius: 9, damage: Math.round(14 * pMul), color: '#fbbf24', noteSymbol: '━♪', isGroundCrawling: true
    })
  }
}

const fireGuitarWave = (level: number) => {
  player.shootPoseTimer = 18
  fireFromPosition(player.x + player.facing * 34, player.y - 30, level, false)
  for (let i = 1; i <= upgrades.options; i++) {
    const histIdx = Math.max(0, positionHistory.length - i * 14)
    const optPos = positionHistory[histIdx] || { x: player.x - player.facing * 28 * i, y: player.y }
    fireFromPosition(optPos.x, optPos.y - 28, Math.min(level, 1), true)
  }
  if (level >= 2) player.vx = -player.facing * 1.8
}

// ★ ダッシュアクション（旧スライディングから表記統一＆↓キー対応）
const startDashAsync = async () => {
  if (!player.onGround || player.isDashing || player.controlLocked) return
  player.isDashing = true
  player.vx = player.facing * PHYSICS.DASH_SPEED
  try { await waitAsync(280) } finally { player.isDashing = false }
}

// ====================================================
// ★ キーボード操作（↑キーでジャンプ、↓キーでダッシュ対応！）
// ====================================================
const keys = new Set<string>()
const onKeyDown = (e: KeyboardEvent) => {
  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Space', 'KeyZ', 'KeyX', 'KeyC'].includes(e.code)) {
    e.preventDefault()
  }
  if (keys.has(e.code) || player.controlLocked || deathOverlay.active) return
  keys.add(e.code)

  // ↑キー / Space / Z でジャンプ
  if ((e.code === 'ArrowUp' || e.code === 'Space' || e.code === 'KeyZ') && player.onGround) {
    player.vy = PHYSICS.JUMP_VELOCITY
    player.onGround = false
    player.scaleX = 0.85; player.scaleY = 1.18
  }
  // ↓キー / C でダッシュ
  if (e.code === 'ArrowDown' || e.code === 'KeyC') {
    startDashAsync()
  }
  // X で音符ショット
  if (e.code === 'KeyX') {
    fireGuitarWave(0)
    startChargeAsync()
  }
}

const onKeyUp = (e: KeyboardEvent) => {
  keys.delete(e.code)
  if ((e.code === 'ArrowUp' || e.code === 'Space' || e.code === 'KeyZ') && player.vy < -1.5) {
    player.vy *= 0.45
  }
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

// ★ ダメージ中は新しく追加した hurt.png（のけぞりモーション）を表示！
const getPlayerSpriteKey = () => {
  if (player.hurtPoseTimer > 0) return 'hurt'
  if (!player.onGround) return player.shootPoseTimer > 0 ? 'jumpShoot' : 'jump'
  if (player.shootPoseTimer > 0) return 'shoot'
  if (Math.abs(player.vx) > 0.4) return Math.floor(player.runAnimTimer / 9) % 2 === 0 ? 'run1' : 'run2'
  return 'idle'
}

// ====================================================
// ★ ダークソウル風「YOU DIED」演出 ＆ チェックポイントリスタート制御
// ====================================================
const triggerYouDiedSequenceAsync = async () => {
  if (deathOverlay.active || gameResult.value) return
  player.controlLocked = true
  stageAbortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  boss.abortController?.abort()

  lives.value--
  const resumeAtFog = boss.active || checkpointReachedBossGate.value
  deathOverlay.message = lives.value > 0
    ? (resumeAtFog ? 'ボス部屋前（白い霧）から再出撃します...' : 'ステージ初期地点から再出撃します...')
    : '残機がすべて失われました'
  deathOverlay.active = true

  await waitAsync(2600)
  deathOverlay.active = false

  if (lives.value > 0) {
    playerHp.value = maxHp.value
    // ボス戦中に死んだ場合はボス前の「白い霧」からリスタート！道中なら初期地点からリスタート！
    startStageFromCloudRun(currentStage.value, resumeAtFog)
  } else {
    gameResult.value = 'GAMEOVER'
  }
}

const damagePlayer = (amount: number) => {
  if (player.invincibleTimer > 0 || deathOverlay.active || gameResult.value || player.controlLocked) return
  if (upgrades.barrierHp > 0) {
    upgrades.barrierHp--; player.invincibleTimer = 40
    floatingTexts.push({ x: player.x, y: player.y - 50, text: 'SHIELD!', color: '#38bdf8', alpha: 1.0 })
    return
  }

  playerHp.value = Math.max(0, playerHp.value - amount)
  player.invincibleTimer = 60
  player.hurtPoseTimer = 28 // 約0.45秒間「ダメージのけぞりエリカ」を表示！
  player.vy = -2.6
  player.vx = -player.facing * 2.5
  screenShakeTimer = 10
  floatingTexts.push({ x: player.x, y: player.y - 55, text: `-${amount}`, color: '#ef4444', alpha: 1.0 })

  if (playerHp.value <= 0) {
    triggerYouDiedSequenceAsync()
  }
}

const isOverPit = (x: number): boolean => {
  return pits.value.some(p => x > p.x + 10 && x < p.x + p.w - 10)
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

  for (let i = obstacles.value.length - 1; i >= 0; i--) {
    obstacles.value[i].x -= scrollSpd
    if (obstacles.value[i].x + obstacles.value[i].w < -60) obstacles.value.splice(i, 1)
  }
  for (let i = pits.value.length - 1; i >= 0; i--) {
    pits.value[i].x -= scrollSpd
    if (pits.value[i].x + pits.value[i].w < -60) pits.value.splice(i, 1)
  }

  // プレイヤー移動更新
  if (!player.controlLocked && !deathOverlay.active) {
    if (!player.isDashing && player.hurtPoseTimer === 0) {
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
        if (nextX + 14 > obs.x && nextX - 14 < obs.x + obs.w) {
          if (player.x <= obs.x) nextX = obs.x - 14
          else nextX = obs.x + obs.w + 14
          player.vx = 0
        }
      }
    }
    if (nextX < 20) {
      nextX = 42; player.vy = -4.5; damagePlayer(18)
    }
    player.x = Math.min(775, nextX)

    // ★ 白い霧が有効かつ敵全滅時に右端（霧）へ触れたらボス部屋へスクロール突入！
    if (fogGate.active && !fogGate.transitioning && enemies.length === 0 && player.x >= fogGate.x - 24) {
      enterFogGateTransitionAsync()
    }
  }

  if (!introState.active) {
    player.vy += PHYSICS.GRAVITY
    player.y += player.vy
    let landed = false

    for (const obs of obstacles.value) {
      const withinX = player.x + 14 > obs.x && player.x - 14 < obs.x + obs.w
      if (withinX && player.vy >= 0 && prevY <= obs.y + 6 && player.y >= obs.y) {
        player.y = obs.y; player.vy = 0; landed = true
      }
    }

    if (!landed && !isOverPit(player.x) && player.y >= GROUND_Y && prevY <= GROUND_Y + 8) {
      player.y = GROUND_Y; player.vy = 0; landed = true
    }

    // 落とし穴に落ちた時も「YOU DIED」演出を発動！
    if (player.y > canvas.height + 30 && !deathOverlay.active) {
      playerHp.value = 0
      triggerYouDiedSequenceAsync()
    }

    if (landed) {
      if (!player.onGround) { player.scaleX = 1.18; player.scaleY = 0.82 }
      player.onGround = true
    } else {
      player.onGround = false
    }
  }

  positionHistory.push({ x: player.x, y: player.y })
  if (positionHistory.length > 40) positionHistory.shift()

  player.scaleX += (1 - player.scaleX) * 0.18
  player.scaleY += (1 - player.scaleY) * 0.18
  if (player.shootPoseTimer > 0) player.shootPoseTimer--
  if (player.hurtPoseTimer > 0) player.hurtPoseTimer--
  if (player.invincibleTimer > 0) player.invincibleTimer--
  if (Math.abs(player.vx) > 0.4) player.runAnimTimer++

  if (player.isDashing || chargeLevel.value >= 2) {
    afterimages.push({ x: player.x, y: player.y, facing: player.facing, alpha: 0.4, spriteKey: getPlayerSpriteKey() })
  }

  // ==========================================
  // 描画処理（画面シェイク対応）
  // ==========================================
  ctx.save()
  if (screenShakeTimer > 0) {
    screenShakeTimer--
    ctx.translate((Math.random() - 0.5) * 7, (Math.random() - 0.5) * 7)
  }

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

  // ★ 地面（高さ1/10＝42pxのスリムなステージ床）
  ctx.fillStyle = currentTheme.groundColor
  ctx.fillRect(0, GROUND_Y, canvas.width, canvas.height - GROUND_Y)
  ctx.strokeStyle = currentTheme.lineColor
  ctx.lineWidth = 3
  ctx.beginPath(); ctx.moveTo(0, GROUND_Y); ctx.lineTo(canvas.width, GROUND_Y); ctx.stroke()

  // 落とし穴の描画
  for (const pit of pits.value) {
    ctx.fillStyle = '#020617'
    ctx.fillRect(pit.x, GROUND_Y - 2, pit.w, canvas.height - GROUND_Y + 4)
    ctx.strokeStyle = '#ef4444'
    ctx.lineWidth = 2
    ctx.strokeRect(pit.x, GROUND_Y, pit.w, canvas.height - GROUND_Y)
  }

  // 壁・空中床の描画
  for (const obs of obstacles.value) {
    ctx.save()
    if (obs.type === 'wall') {
      ctx.fillStyle = '#1e293b'
      ctx.fillRect(obs.x, obs.y, obs.w, obs.h)
      ctx.strokeStyle = currentTheme.lineColor
      ctx.lineWidth = 2
      ctx.strokeRect(obs.x, obs.y, obs.w, obs.h)
    } else {
      ctx.fillStyle = '#334155'
      ctx.fillRect(obs.x, obs.y, obs.w, obs.h)
      ctx.fillStyle = '#38bdf8'
      ctx.fillRect(obs.x, obs.y, obs.w, 3)
    }
    ctx.restore()
  }

  // ★ ダークソウル風「白い霧の扉」の描画（右端で揺らめく白い霧）
  if (fogGate.active) {
    ctx.save()
    const fogGrad = ctx.createLinearGradient(fogGate.x - 25, 0, canvas.width, 0)
    fogGrad.addColorStop(0, 'rgba(255, 255, 255, 0)')
    fogGrad.addColorStop(0.5, enemies.length === 0 ? 'rgba(241, 245, 249, 0.78)' : 'rgba(148, 163, 184, 0.35)')
    fogGrad.addColorStop(1, 'rgba(255, 255, 255, 0.95)')
    ctx.fillStyle = fogGrad
    ctx.fillRect(fogGate.x - 25, 0, 60, GROUND_Y)

    // 霧の粒子アニメーション
    for (let i = 0; i < 6; i++) {
      const py = ((now * 0.06 + i * 68) % GROUND_Y)
      const px = fogGate.x + Math.sin(now * 0.005 + i) * 8
      ctx.beginPath()
      ctx.arc(px, GROUND_Y - py, 14, 0, Math.PI * 2)
      ctx.fillStyle = 'rgba(255, 255, 255, 0.35)'
      ctx.fill()
    }
    ctx.restore()
  }

  // 残像描画（0.8倍サイズ＝76px）
  const playerDrawSize = Math.round(96 * CHAR_SCALE)
  for (let i = afterimages.length - 1; i >= 0; i--) {
    const aft = afterimages[i]
    aft.alpha -= 0.05
    if (aft.alpha <= 0) { afterimages.splice(i, 1); continue }
    drawSprite(ctx, sprites[aft.spriteKey], aft.x, aft.y, aft.facing, playerDrawSize, 1, 1, aft.alpha, 190)
  }

  // オプション描画
  for (let i = 1; i <= upgrades.options; i++) {
    const histIdx = Math.max(0, positionHistory.length - i * 14)
    const optPos = positionHistory[histIdx] || { x: player.x - player.facing * 28 * i, y: player.y }
    const floatY = Math.sin(now * 0.008 + i) * 4
    ctx.save()
    ctx.beginPath()
    ctx.arc(optPos.x, optPos.y - 28 + floatY, 9, 0, Math.PI * 2)
    ctx.fillStyle = '#38bdf8'; ctx.shadowColor = '#38bdf8'; ctx.shadowBlur = 10; ctx.fill()
    ctx.fillStyle = '#0f172a'; ctx.font = 'bold 10px sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText('♪', optPos.x, optPos.y - 28 + floatY)
    ctx.restore()
  }

  // チャージオーラ
  if (chargeLevel.value > 0) {
    ctx.save()
    ctx.beginPath()
    const r = 26 + chargeLevel.value * 6 + Math.sin(now * 0.03) * 4
    ctx.arc(player.x, player.y - 34, r, 0, Math.PI * 2)
    ctx.fillStyle = chargeLevel.value === 3 ? 'rgba(192, 132, 252, 0.35)' : chargeLevel.value === 2 ? 'rgba(250, 204, 21, 0.28)' : 'rgba(56, 189, 248, 0.22)'
    ctx.fill()
    ctx.strokeStyle = chargeLevel.value === 3 ? '#e879f9' : chargeLevel.value === 2 ? '#facc15' : '#38bdf8'
    ctx.stroke()
    ctx.restore()
  }

  // ★ ロックマン風：開始時のテレポートビーム描画 vs エリカ本体描画
  if (introState.active && player.y < GROUND_Y - 4) {
    ctx.save()
    ctx.fillStyle = 'rgba(244, 114, 182, 0.85)'
    ctx.shadowColor = '#ec4899'; ctx.shadowBlur = 18
    ctx.fillRect(player.x - 6, 0, 12, player.y)
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(player.x - 2, 0, 4, player.y)
    ctx.restore()
  } else if (player.invincibleTimer % 4 < 2) {
    const dashScaleY = player.isDashing ? 0.74 : player.scaleY
    drawSprite(ctx, sprites[getPlayerSpriteKey()], player.x, player.y, player.facing, playerDrawSize, player.scaleX, dashScaleY, 1.0, 0)
  }

  if (upgrades.barrierHp > 0) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(player.x, player.y - 34, 38, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(56, 189, 248, ${0.35 + upgrades.barrierHp * 0.2})`
    ctx.lineWidth = 2.5; ctx.setLineDash([6, 5]); ctx.stroke()
    ctx.restore()
  }

  // ドロップアイテム更新
  for (let i = dropItems.length - 1; i >= 0; i--) {
    const item = dropItems[i]
    item.x -= scrollSpd
    item.vy += PHYSICS.GRAVITY
    if (!isOverPit(item.x)) item.y = Math.min(GROUND_Y - 10, item.y + item.vy)
    else item.y += item.vy
    item.lifeTimer--

    ctx.save()
    ctx.font = 'bold 15px sans-serif'; ctx.textAlign = 'center'
    const label = item.type === '1UP' ? '⭐1UP' : item.type === 'HEAL' ? '💚+HP' : '🎵'
    ctx.fillStyle = item.type === '1UP' ? '#facc15' : item.type === 'HEAL' ? '#4ade80' : '#f472b6'
    ctx.fillText(label, item.x, item.y)
    ctx.restore()

    if (Math.abs(player.x - item.x) < 28 && Math.abs((player.y - 24) - item.y) < 30) {
      if (item.type === '1UP') lives.value++
      else if (item.type === 'HEAL') playerHp.value = Math.min(maxHp.value, playerHp.value + 30)
      else score.value += 300
      floatingTexts.push({ x: item.x, y: item.y - 15, text: label, color: '#4ade80', alpha: 1.0 })
      dropItems.splice(i, 1)
      continue
    }
    if (item.lifeTimer <= 0 || item.y > canvas.height + 30) dropItems.splice(i, 1)
  }

  // 敵キャラ更新＆描画（0.8倍サイズ＝60px）
  const enemyDrawSize = Math.round(76 * CHAR_SCALE)
  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i]
    const prevEnemyY = e.y
    if (!e.isStunned) e.x += e.vx - scrollSpd * 0.65

    for (const obs of obstacles.value) {
      if (obs.type === 'wall' && e.y > obs.y + 6 && Math.abs(e.x - (obs.x + obs.w / 2)) < obs.w / 2 + 18) {
        if (e.wallAction === 'bounce') { e.vx = -e.vx; e.x += e.vx * 3 }
        else if (e.wallAction === 'jump' && e.vy === 0) e.vy = -4.2
      }
    }

    for (const pit of pits.value) {
      if (e.wallAction === 'jump' && e.vy === 0 && Math.abs(e.x - (pit.x + pit.w)) < 16) e.vy = -4.3
    }

    if (e.type === 'note_ghost') {
      e.y = e.baseY + Math.sin(now * 0.004 + i) * 28
    } else {
      e.vy += PHYSICS.GRAVITY
      e.y += e.vy
      for (const obs of obstacles.value) {
        if (e.x + 12 > obs.x && e.x - 12 < obs.x + obs.w && e.vy >= 0 && prevEnemyY <= obs.y + 6 && e.y >= obs.y) {
          e.y = obs.y; e.vy = 0
        }
      }
      if (!isOverPit(e.x) && e.y >= GROUND_Y && prevEnemyY <= GROUND_Y + 8) {
        e.y = GROUND_Y; e.vy = 0
      }
    }

    const shakeX = e.isCharging ? (Math.random() - 0.5) * 6 : 0
    const moleScaleY = e.isHidden ? 0.45 : 1.0
    const stunFlipY = e.isStunned ? -0.8 : moleScaleY
    const enemyFacing = e.vx > 0 ? -1 : 1
    drawSprite(ctx, sprites[e.type], e.x + shakeX, e.y, enemyFacing, enemyDrawSize, 1, stunFlipY, 1.0, e.hueRotate)

    if (e.hp < e.maxHp) {
      ctx.fillStyle = '#1e293b'; ctx.fillRect(e.x - 16, e.y - 62, 32, 4)
      ctx.fillStyle = '#f43f5e'; ctx.fillRect(e.x - 16, e.y - 62, 32 * (e.hp / e.maxHp), 4)
    }

    if (Math.abs(player.x - e.x) < 28 && Math.abs(player.y - e.y) < 34) {
      if (player.vy > 0 && player.y < e.y - 10) {
        if (e.spiky) {
          damagePlayer(15)
        } else if (e.stompable) {
          player.vy = PHYSICS.BOUNCE_VELOCITY
          player.scaleX = 1.22; player.scaleY = 0.78
          const stompDmg = Math.round(22 * upgrades.powerMultiplier)
          e.hp -= stompDmg
          floatingTexts.push({ x: e.x, y: e.y - 45, text: `${stompDmg}`, color: '#facc15', alpha: 1.0 })
          if (e.type === 'turtle' && e.hp > 0) e.isStunned = true
          if (e.hp <= 0) { onEnemyDefeated(e); enemies.splice(i, 1); continue }
        }
      } else if (!player.isDashing) {
        damagePlayer(14)
      }
    }

    if (e.x < -70 || e.y > canvas.height + 40) {
      e.abortController.abort()
      enemies.splice(i, 1)
    }
  }

  // ボスの更新＆描画（0.8倍スケール適用）
  if (boss.active) {
    boss.x = Math.max(80, Math.min(730, boss.x + boss.vx))
    if (boss.isFloating) {
      boss.y = Math.max(170, Math.min(270, boss.y + boss.vy))
    } else {
      boss.vy += PHYSICS.GRAVITY
      boss.y = Math.min(GROUND_Y, boss.y + boss.vy)
      if (boss.y >= GROUND_Y) boss.vy = 0
    }

    if (boss.warningLaserY !== null) {
      ctx.save()
      ctx.fillStyle = 'rgba(250, 204, 21, 0.25)'
      ctx.fillRect(0, boss.warningLaserY - 12, canvas.width, 24)
      ctx.strokeStyle = '#ef4444'; ctx.setLineDash([8, 5]); ctx.lineWidth = 2
      ctx.beginPath(); ctx.moveTo(0, boss.warningLaserY); ctx.lineTo(canvas.width, boss.warningLaserY); ctx.stroke()
      ctx.restore()
    }

    if (boss.warningSpikeX !== null) {
      ctx.save()
      ctx.fillStyle = 'rgba(168, 85, 247, 0.35)'
      ctx.fillRect(boss.warningSpikeX - 18, GROUND_Y - 90, 36, 90)
      ctx.restore()
    }

    const bossFacing = player.x > boss.x ? -1 : 1
    const bossDrawSize = Math.round(96 * CHAR_SCALE * boss.scale)
    drawSprite(ctx, sprites[boss.spriteKey], boss.x, boss.y, bossFacing, bossDrawSize, 1, 1, 1.0, 0)

    if (Math.abs(player.x - boss.x) < 34 && Math.abs(player.y - boss.y) < 46) {
      damagePlayer(18)
    }
  }

  // 音符弾の更新＆壁遮断
  for (let i = bullets.length - 1; i >= 0; i--) {
    const b = bullets[i]
    b.x += b.vx
    if (b.gravity) b.vy += b.gravity
    b.y += b.vy

    if (b.isGroundCrawling) {
      let surfaceY = GROUND_Y - 8
      for (const obs of obstacles.value) {
        if (b.x >= obs.x && b.x <= obs.x + obs.w) surfaceY = Math.min(surfaceY, obs.y - 8)
      }
      b.y = surfaceY
    } else if (b.gravity && b.y >= GROUND_Y - 8) {
      b.y = GROUND_Y - 8; b.vy = -3.2 // ティーカップ弾が床でバウンド！
    }

    let blockedByWall = false
    if (!b.piercing && !b.isGroundCrawling) {
      for (const obs of obstacles.value) {
        if (obs.type === 'wall' && b.x + b.radius > obs.x && b.x - b.radius < obs.x + obs.w && b.y + b.radius > obs.y && b.y - b.radius < obs.y + obs.h) {
          blockedByWall = true; break
        }
      }
    }
    if (blockedByWall) { bullets.splice(i, 1); continue }

    ctx.save()
    ctx.beginPath()
    ctx.arc(b.x, b.y, b.radius, 0, Math.PI * 2)
    ctx.fillStyle = b.color + '44'
    ctx.shadowColor = b.color; ctx.shadowBlur = 10
    ctx.fill()
    ctx.fillStyle = b.color
    ctx.font = `bold ${Math.max(13, b.radius * 1.3)}px sans-serif`
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'
    ctx.fillText(b.noteSymbol, b.x, b.y)
    ctx.restore()

    if (b.isEnemy) {
      if (Math.abs(b.x - player.x) < 18 && Math.abs(b.y - (player.y - 28)) < 26) {
        damagePlayer(b.damage)
        bullets.splice(i, 1)
        continue
      }
    } else {
      let hit = false
      for (let j = enemies.length - 1; j >= 0; j--) {
        const e = enemies[j]
        if (Math.abs(b.x - e.x) < 28 && Math.abs(b.y - (e.y - 26)) < 30) {
          if (e.isHidden && !b.piercing && !b.isGroundCrawling) {
            b.vx = -b.vx * 0.8; b.vy = -2; break
          }
          const dmg = (e.armored && !b.piercing && !e.isStunned) ? Math.ceil(b.damage * 0.4) : b.damage
          e.hp -= dmg; hit = true
          floatingTexts.push({ x: e.x, y: e.y - 42, text: `${dmg}`, color: b.piercing ? '#facc15' : '#ffffff', alpha: 1.0 })
          if (e.hp <= 0) { onEnemyDefeated(e); enemies.splice(j, 1) }
          if (!b.piercing) break
        }
      }
      if (hit && !b.piercing) { bullets.splice(i, 1); continue }

      if (boss.active && Math.abs(b.x - boss.x) < 36 && Math.abs(b.y - (boss.y - 38)) < 44) {
        boss.hp = Math.max(0, boss.hp - b.damage)
        floatingTexts.push({ x: boss.x + (Math.random() - 0.5) * 20, y: boss.y - 55, text: `${b.damage}`, color: b.piercing ? '#facc15' : '#f472b6', alpha: 1.0 })
        if (b.piercing) screenShakeTimer = 4
        if (!b.piercing) bullets.splice(i, 1)
        if (boss.hp <= 0) {
          boss.active = false; boss.warningLaserY = null; boss.warningSpikeX = null
          boss.abortController?.abort()
          score.value += 2000 * currentStage.value
          gameResult.value = 'CLEAR'
          // ★ ボス撃破時に祝福の打ち上げ花火を連続発射！
          for (let f = 0; f < 5; f++) setTimeout(spawnFireworkBurst, f * 350)
        }
        continue
      }
    }

    if (b.x < -60 || b.x > canvas.width + 60 || b.y < -60 || b.y > canvas.height + 60) {
      bullets.splice(i, 1)
    }
  }

  // フローティングダメージテキストの描画
  for (let i = floatingTexts.length - 1; i >= 0; i--) {
    const ft = floatingTexts[i]
    ft.y -= 1.0
    ft.alpha -= 0.03
    if (ft.alpha <= 0) { floatingTexts.splice(i, 1); continue }
    ctx.save()
    ctx.globalAlpha = ft.alpha
    ctx.font = 'bold 13px monospace'
    ctx.fillStyle = ft.color
    ctx.textAlign = 'center'
    ctx.fillText(ft.text, ft.x, ft.y)
    ctx.restore()
  }

  // ★ クリア時の打ち上げ花火パーティクル更新＆描画
  if (gameResult.value === 'CLEAR' && Math.random() < 0.05) spawnFireworkBurst()
  for (let i = fireworks.length - 1; i >= 0; i--) {
    const fw = fireworks[i]
    fw.x += fw.vx; fw.y += fw.vy; fw.vy += 0.04; fw.alpha -= 0.02
    if (fw.alpha <= 0) { fireworks.splice(i, 1); continue }
    ctx.save()
    ctx.globalAlpha = fw.alpha
    ctx.beginPath()
    ctx.arc(fw.x, fw.y, 3, 0, Math.PI * 2)
    ctx.fillStyle = fw.color; ctx.shadowColor = fw.color; ctx.shadowBlur = 8
    ctx.fill()
    ctx.restore()
  }

  ctx.restore()
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
    ctx.drawImage(img, -size / 2, -size + 5, size, size)
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
  startStageFromCloudRun(1, false)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  cancelAnimationFrame(animFrameId)
  stageAbortController?.abort()
  chargeAbort?.abort()
})
</script>