<template>
  <div class="rock-action-page min-h-screen pt-24 pb-12 bg-zinc-950 text-zinc-200 select-none font-sans">
    <div class="w-full max-w-4xl mx-auto px-4">
      <!-- ページタイトルヘッダー（他ゲーム画面と統一） -->
      <header class="text-center mb-5">
        <p class="text-xs tracking-[0.35em] text-amber-400 mb-1 font-mono">
          SCROLLING ACTION &amp; SHOOTING
        </p>
        <h1 class="text-3xl sm:text-4xl font-black tracking-tight text-white">
          ERIKA ROCK ACTION
        </h1>
      </header>

      <div class="bg-slate-950 rounded-xl overflow-hidden shadow-2xl border border-slate-800">
        <!-- ==================================================== -->
        <!-- 上部独立ダッシュボードUI -->
        <!-- ==================================================== -->
        <div class="bg-slate-900 border-b border-slate-800 px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center gap-3">
            <div class="bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 text-center min-w-[82px]">
              <div class="text-[10px] font-mono" :class="loopCount > 1 ? 'text-amber-400 font-bold' : 'text-slate-400'">
                {{ loopCount > 1 ? `LOOP ${loopCount} EX` : 'STAGE' }}
              </div>
              <div class="text-lg font-black text-pink-400 leading-none">{{ currentStage }}</div>
            </div>

            <div>
              <div class="flex items-center gap-3 mb-1">
                <span class="text-xs font-extrabold text-white tracking-wider">ERIKA</span>
                <div class="flex items-center gap-0.5 text-rose-500 text-sm">
                  <span v-for="n in lives" :key="n">♥</span>
                  <span v-if="lives === 0" class="text-xs text-slate-500">LAST</span>
                </div>
                <span class="text-xs font-mono text-slate-300 ml-1">HP {{ playerHp }}/{{ maxHp }}</span>
              </div>
              <div class="w-40 h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-700 p-0.5">
                <div class="h-full rounded-full bg-gradient-to-r from-pink-500 via-rose-400 to-emerald-400 transition-all duration-150"
                     :style="{ width: `${Math.min(100, (playerHp / maxHp) * 100)}%` }"></div>
              </div>
            </div>

            <div class="px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all"
                 :class="chargeLevel === 3 ? 'bg-gradient-to-r from-pink-500 via-yellow-400 to-cyan-400 text-slate-950 border-white animate-pulse' :
                         chargeLevel === 2 ? 'bg-yellow-400 text-slate-950 border-yellow-200' :
                         chargeLevel === 1 ? 'bg-cyan-400 text-slate-950 border-cyan-200' : 'bg-slate-950 text-slate-400 border-slate-800'">
              {{ chargeLevel === 3 ? 'FINAL CHARGE!!' : chargeLevel === 2 ? 'LV.2 PIERCE' : chargeLevel === 1 ? 'LV.1 CHARGE' : 'BUSTER READY' }}
            </div>
          </div>

          <!-- 装備中パワーアップ -->
          <div class="flex flex-wrap gap-1 text-[10px] font-mono">
            <span class="px-2 py-1 rounded border" :class="upgrades.doubleShotLv > 0 ? 'bg-pink-950/80 border-pink-500 text-pink-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">
              2-WAY Lv.{{ upgrades.doubleShotLv }}
            </span>
            <span class="px-2 py-1 rounded border" :class="upgrades.slashLv > 0 ? 'bg-amber-950/80 border-amber-500 text-amber-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">
              SLASH Lv.{{ upgrades.slashLv }}
            </span>
            <span class="px-2 py-1 rounded border" :class="upgrades.options > 0 ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">
              OPT×{{ upgrades.options }}
            </span>
            <span class="px-2 py-1 rounded border" :class="upgrades.barrierHp > 0 ? 'bg-blue-950/80 border-blue-400 text-blue-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">
              SHIELD:{{ upgrades.barrierHp }}
            </span>
            <span class="px-2 py-1 rounded border bg-slate-950 border-slate-800 text-emerald-400">
              ATK×{{ upgrades.powerMultiplier.toFixed(2) }}
            </span>
          </div>

          <!-- スコア ＆ 進行度／ボスHP -->
          <div class="min-w-[195px] text-right">
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
                <span class="truncate max-w-[125px]">{{ boss.name }}</span>
                <span>{{ boss.hp }}/{{ boss.maxHp }}</span>
              </div>
              <div class="w-full h-2.5 bg-slate-950 rounded-full overflow-hidden border border-red-900">
                <div class="h-full bg-gradient-to-r from-red-600 via-orange-500 to-yellow-400 transition-all duration-100"
                     :style="{ width: `${(boss.hp / boss.maxHp) * 100}%` }"></div>
              </div>
              <div v-if="boss.hasShield && boss.shieldState !== 'UNARMED'" class="mt-1">
                <div class="flex justify-between text-[9px] font-mono text-amber-300">
                  <span>SUNFLOWER SHIELD</span>
                  <span>{{ boss.shieldHp }}/{{ boss.maxShieldHp }}</span>
                </div>
                <div class="w-full h-1.5 bg-slate-950 rounded-full overflow-hidden border border-amber-600">
                  <div class="h-full bg-gradient-to-r from-amber-400 to-cyan-300 transition-all duration-100"
                       :style="{ width: `${(boss.shieldHp / boss.maxShieldHp) * 100}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ==================================================== -->
        <!-- ゲーム画面領域（Canvas ＋ 演出オーバーレイ） -->
        <!-- ==================================================== -->
        <div class="relative">
          <!-- ① ロックマン風：ステージ開始カウントダウン -->
          <transition name="fade">
            <div v-if="introState.active" class="absolute inset-0 flex flex-col items-center justify-center z-20 pointer-events-none bg-black/25">
              <div class="text-pink-400 font-mono text-xs tracking-widest mb-1">
                {{ loopCount > 1 ? `LOOP ${loopCount} // EXTREME BARRAGE MODE` : 'MISSION START' }}
              </div>
              <div class="text-4xl font-black text-white tracking-wider drop-shadow-lg">STAGE {{ currentStage }} // READY!</div>
              <div class="text-xs font-mono text-cyan-300 mt-1">{{ currentTheme.themeName }}</div>
            </div>
          </transition>

          <!-- ② 白い霧（ダークソウル風）案内メッセージ -->
          <div v-if="fogGate.active && !boss.active && !cutin.visible"
               class="absolute top-5 left-1/2 -translate-x-1/2 z-10 pointer-events-none px-4 py-1.5 rounded-full bg-slate-900/90 border border-slate-500 text-xs font-bold shadow-lg"
               :class="enemies.length > 0 ? 'text-amber-300' : 'text-white animate-bounce'">
            {{ enemies.length > 0 ? `⚠️ 残りの敵をすべて倒してください（残り ${enemies.length} 体）` : '🌫️ 右端の「白い霧」に触れてボス部屋へ進む →' }}
          </div>

          <!-- ③ ボス登場時：ボスへのズームイン紹介バナー -->
          <transition name="fade">
            <div v-if="cutin.visible" class="absolute inset-x-0 bottom-6 flex justify-center z-20 pointer-events-none">
              <div class="px-8 py-4 rounded-xl border-2 border-pink-500 bg-slate-950/90 shadow-2xl text-center max-w-xl w-full mx-4">
                <div class="text-pink-400 text-xs font-mono tracking-widest mb-0.5">
                  WARNING // {{ loopCount > 1 ? `LOOP ${loopCount} EX BOSS` : 'BOSS ENCOUNTER' }}
                </div>
                <div class="text-2xl font-black text-yellow-300 tracking-wide mb-1">BOSS: {{ cutin.bossName }}</div>
                <div class="text-sm font-bold text-white">「{{ cutin.quote }}」</div>
                <div class="text-[11px] text-slate-400 mt-0.5">— {{ cutin.source }}</div>
              </div>
            </div>
          </transition>

          <!-- ④ ダークソウル風：「YOU DIED」ブラックアウト演出 -->
          <transition name="fade">
            <div v-if="deathOverlay.active" class="absolute inset-0 bg-black/85 flex flex-col items-center justify-center z-30 pointer-events-none">
              <div class="w-full py-6 bg-gradient-to-r from-transparent via-black to-transparent border-y border-red-900/60 text-center">
                <div class="text-5xl md:text-6xl font-serif tracking-[0.25em] text-red-600 drop-shadow-[0_0_20px_rgba(220,38,38,0.8)]">
                  YOU DIED
                </div>
                <div class="text-xs font-mono text-slate-300 mt-3 tracking-widest">
                  {{ deathOverlay.message }}
                </div>
              </div>
            </div>
          </transition>

          <!-- ⑤ クリアボーナス選択画面（攻撃倍率均一+5%・HP+10調整版） -->
          <transition name="fade">
            <div v-if="gameResult === 'CLEAR'" class="absolute inset-0 bg-slate-950/80 flex flex-col items-center justify-center z-20 p-4">
              <div class="flex items-center gap-5 mb-3 bg-slate-900/95 px-6 py-3 rounded-2xl border border-yellow-400/60 shadow-2xl">
                <img src="/sprites/victory.png" alt="Victory Erika" class="w-20 h-20 object-contain drop-shadow-[0_0_12px_rgba(244,114,182,0.8)]" />
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

          <!-- ⑥ ゲームオーバー画面 -->
          <div v-if="gameResult === 'GAMEOVER'" class="absolute inset-0 bg-black/90 flex flex-col items-center justify-center z-30">
            <img src="/sprites/down.png" alt="Down Erika" class="w-28 h-28 object-contain mb-2 opacity-90" />
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
        <!-- 下部操作ガイド -->
        <!-- ==================================================== -->
        <div class="bg-slate-900 px-4 py-2.5 flex flex-wrap justify-between items-center gap-2 text-xs text-slate-300 border-t border-slate-800">
          <div class="flex flex-wrap gap-3">
            <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">←</kbd> <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">→</kbd> 移動</span>
            <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">↑</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Z</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">Space</kbd> ジャンプ</span>
            <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">↓</kbd> / <kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">C</kbd> ダッシュ</span>
            <span><kbd class="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-600">X</kbd> 音符ショット＆薙ぎ払い（Lv2以上チャージで敵弾消去！）</span>
          </div>
          <div class="flex gap-2">
            <router-link to="/" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition">
              TOPへ戻る
            </router-link>
            <button @click="resetFullGame" :disabled="isLoadingStage"
                    class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-600 transition">
              STAGE 1 リスタート
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'

const API_BASE = import.meta.env.VITE_API_URL || 'https://erika-action-api-xxxxxxxxxx-an.a.run.app'

const GROUND_Y = 408
const CHAR_SCALE = 0.8

const BOSS_ARENA = {
  LEFT: 65,
  RIGHT: 735,
  TOP: 95,
  BOTTOM: GROUND_Y
}

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
const loopCount = computed(() => Math.floor((currentStage.value - 1) / 12) + 1)
const stageProgress = ref(0)
const gameResult = ref<'CLEAR' | 'GAMEOVER' | null>(null)

const checkpointReachedBossGate = ref(false)
const introState = reactive({ active: false, beamY: -50 })
const fogGate = reactive({ active: false, x: 765, transitioning: false })
const deathOverlay = reactive({ active: false, message: '' })

const camera = reactive({
  zoom: 1.0,
  targetZoom: 1.0,
  focusX: 400,
  focusY: 225,
  targetX: 400,
  targetY: 225
})

const upgrades = reactive({
  doubleShotLv: 0,
  slashLv: 0,
  options: 0,
  barrierHp: 0,
  powerMultiplier: 1.0,
  maxChargeLevel: 2,
})

// ★ ボーナス選択：すべて均一に「攻撃力+5%」、体力アップは「最大HP+10」へ適正化！
const bonusChoices = computed(() => [
  {
    id: 'DOUBLE',
    title: `🎵 2方向デュアルショット (${upgrades.doubleShotLv}/2)`,
    desc: upgrades.doubleShotLv === 0 ? 'Lv1: 斜め上45度へ同時に通常音符弾を発射！' :
          upgrades.doubleShotLv === 1 ? 'Lv2強化: チャージ段階に応じた強化弾を斜め上にも発射！' : '最大Lv達成（選ぶと攻撃力+5%）'
  },
  {
    id: 'SLASH',
    title: `⚔️ 偃月サウンド薙ぎ払い (${upgrades.slashLv}/2)`,
    desc: upgrades.slashLv === 0 ? 'Lv1: 周囲を一周する光の剣で斬り払う（敵弾は消せません）' :
          upgrades.slashLv === 1 ? 'Lv2強化: チャージLv2以上で敵弾を斬り払い消去可能に！' : '最大Lv達成（選ぶと攻撃力+5%）'
  },
  {
    id: 'OPTION',
    title: `🛰️ サウンド・オプション (${upgrades.options}/2)`,
    desc: upgrades.options < 2 ? 'エリカの後ろを追従し、同時に音符を撃つスピーカーを追加！' : '最大数達成（選ぶと攻撃力+5%）'
  },
  {
    id: 'BARRIER',
    title: '🛡️ 音響フォースバリア (+5% ATK)',
    desc: '敵の弾や体当たりを3回まで無効化するシールドを展開＋攻撃力+5%！'
  },
  {
    id: 'CHARGE3',
    title: '⚡ ファイナルチャージ解放 (Lv.3)',
    desc: upgrades.maxChargeLevel >= 3 ? '取得済（選ぶと攻撃力+5%）' : '3段階目の極太ブラスター解放（薙ぎ払いLv2で弾吸収回復！）'
  },
  {
    id: 'VITAL',
    title: '💖 最大HP+10 ＆ HP回復 ＆ 1UP',
    desc: '最大体力を+10増やし、HP全回復＋残機を1つ増やす！'
  },
])

const cutin = reactive({ visible: false, bossName: '', quote: '', source: '' })

// ★ マスタデータ：中盤〜後半、そして2周目のフル装備に耐えうるよう基礎HPをしっかり底上げ！
let masterData: any = {
  quotes: [
    { quote: '手探りでもただ前に進むしかない。いずれなんとかなるだろってな。', source: '『シャーマンキング』麻倉葉' },
    { quote: 'お前が信じる、お前を信じろ！', source: '『天元突破グレンラガン』カミナ' },
    { quote: '覚悟とは！！暗闇の荒野に！！進むべき道を切り開く事だッ！', source: '『ジョジョの奇妙な冒険 第5部』ジョルノ' },
    { quote: '音楽は鳴り止まない。僕らが歩き続ける限り。', source: 'ERIKA OBSERVATION LOG' }
  ],
  enemies: [
    { type: 'soot',       name: '煤玉モンスター', sprite: '/sprites/enemies/soot.png',       hp: 26, speed: 1.3, score: 100, stompable: true,  wallAction: 'bounce' },
    { type: 'lime',       name: 'ライム豆っこ',   sprite: '/sprites/enemies/lime.png',       hp: 30, speed: 1.8, score: 150, stompable: true,  wallAction: 'jump' },
    { type: 'jelly',      name: '桃色ゼリー',     sprite: '/sprites/enemies/jelly.png',      hp: 42, speed: 1.2, score: 200, stompable: true,  wallAction: 'jump' },
    { type: 'note_ghost', name: '音符のおばけ',   sprite: '/sprites/enemies/note_ghost.png', hp: 36, speed: 1.5, score: 250, stompable: true,  wallAction: 'fly' },
    { type: 'turtle',     name: 'ずんぐりカメ',   sprite: '/sprites/enemies/turtle.png',     hp: 80, speed: 0.8, score: 300, stompable: true,  armored: true, wallAction: 'bounce' },
    { type: 'mole',       name: '鉱夫モグラ',     sprite: '/sprites/enemies/mole.png',       hp: 55, speed: 0.0, score: 350, stompable: false, helmet: true,  wallAction: 'stay' },
    { type: 'hedgehog',   name: '赤いハリネズミ', sprite: '/sprites/enemies/hedgehog.png',   hp: 68, speed: 3.5, score: 400, stompable: false, spiky: true,   wallAction: 'jump' },
  ],
  bosses: [
    { id: 'knight',    name: 'BLACK KNIGHT ERIKA',    sprite: '/sprites/bosses/boss_knight.png',    baseHp: 620,  scale: 1.2, pattern: 'KNIGHT' },
    { id: 'concierge', name: 'KEY MASTER ERIKA',      sprite: '/sprites/bosses/boss_concierge.png', baseHp: 880,  scale: 1.2, pattern: 'CONCIERGE' },
    { id: 'yukata',    name: 'SUNFLOWER YUKATA',      sprite: '/sprites/bosses/boss_yukata.png',    baseHp: 1050, scale: 1.2, pattern: 'YUKATA' },
    { id: 'ivory',     name: 'IVORY COMMANDER',       sprite: '/sprites/bosses/boss_ivory.png',     baseHp: 1200, scale: 1.2, pattern: 'IVORY' },
    { id: 'tea',       name: 'MINT TEA MASTER',       sprite: '/sprites/bosses/boss_tea.png',       baseHp: 1350, scale: 1.2, pattern: 'TEA' },
    { id: 'kimono',    name: 'GRIMOIRE KIMONO',       sprite: '/sprites/bosses/boss_kimono.png',    baseHp: 1500, scale: 1.2, pattern: 'KIMONO' },
    { id: 'flower',    name: 'FLORA PRINCESS',        sprite: '/sprites/bosses/boss_flower.png',    baseHp: 1680, scale: 1.2, pattern: 'FLOWER' },
    { id: 'camellia',  name: 'CAMELLIA SHRINE',       sprite: '/sprites/bosses/boss_camellia.png',  baseHp: 1850, scale: 1.2, pattern: 'CAMELLIA' },
    { id: 'dress',     name: 'NAVY DRESS DIVA',       sprite: '/sprites/bosses/boss_dress.png',     baseHp: 2050, scale: 1.2, pattern: 'DRESS' },
    { id: 'gothic',    name: 'BLACK ROSE GOTHIC',     sprite: '/sprites/bosses/boss_gothic.png',    baseHp: 2250, scale: 1.2, pattern: 'GOTHIC' },
    { id: 'queen',     name: 'PEARL THRONE QUEEN',    sprite: '/sprites/bosses/boss_queen.png',     baseHp: 2500, scale: 1.25,pattern: 'QUEEN' },
    {
      id: 'sunflower',
      name: 'EMPRESS ERIKA // SUNFLOWER AEGIS',
      sprite: '/sprites/bosses/boss_sunflower_shield.png',
      spriteCracked: '/sprites/bosses/boss_sunflower_cracked.png',
      spriteUnarmed: '/sprites/bosses/boss_sunflower_unarmed.png',
      baseHp: 3200,
      scale: 4.1,
      pattern: 'SUNFLOWER_FINAL',
      isGiantFinalBoss: true
    }
  ],
  stages: [
    { stage: 1, themeName: 'SUNSET HIGHWAY',        skyGradient: ['#0f172a', '#311042', '#701a75'], groundColor: '#1e1b4b', lineColor: '#ec4899', scrollSpeed: 1.4,  bgStyle: 'CITY' },
    { stage: 2, themeName: 'CYBER NEON LABYRINTH',  skyGradient: ['#020617', '#064e3b', '#047857'], groundColor: '#022c22', lineColor: '#34d399', scrollSpeed: 1.52, bgStyle: 'CYBER' },
    { stage: 3, themeName: 'CRIMSON AMPLIFIER',     skyGradient: ['#180404', '#450a0a', '#9a3412'], groundColor: '#270909', lineColor: '#f97316', scrollSpeed: 1.62, bgStyle: 'PILLARS' },
    { stage: 4, themeName: 'DEEP PEARL OCEAN',      skyGradient: ['#020617', '#0c4a6e', '#0284c7'], groundColor: '#082f49', lineColor: '#38bdf8', scrollSpeed: 1.72, bgStyle: 'OCEAN' },
    { stage: 5, themeName: 'GOLDEN CATHEDRAL',      skyGradient: ['#1c1917', '#422006', '#a16207'], groundColor: '#292524', lineColor: '#facc15', scrollSpeed: 1.82, bgStyle: 'CATHEDRAL' },
    { stage: 6, themeName: 'GOTHIC BLOOD MOON',     skyGradient: ['#090414', '#2e1065', '#4c0519'], groundColor: '#1e1b4b', lineColor: '#c084fc', scrollSpeed: 1.92, bgStyle: 'GOTHIC' },
  ]
}

const loadMasterJsonAsync = async () => {
  try {
    const res = await fetch('/data/game-master.json')
    if (res.ok) {
      const json = await res.json()
      if (json.bosses && json.bosses.length >= 12) masterData = json
    }
  } catch {}
}

const sprites: Record<string, HTMLImageElement> = {}
const loadAllSprites = async () => {
  const paths: Record<string, string> = {
    idle: '/sprites/idle.png', run1: '/sprites/run1.png', run2: '/sprites/run2.png',
    shoot: '/sprites/shoot.png', jump: '/sprites/jump.png', jumpShoot: '/sprites/jump_shoot.png',
    hurt: '/sprites/hurt.png',
    victory: '/sprites/victory.png',
    down: '/sprites/down.png',
  }
  masterData.enemies.forEach((e: any) => { paths[e.type] = e.sprite })
  masterData.bosses.forEach((b: any) => {
    paths[`boss_${b.id}`] = b.sprite
    paths[`boss_${b.id}_hurt`] = `/sprites/bosses/boss_${b.id}_hurt.png`
    paths[`boss_${b.id}_down`] = `/sprites/bosses/boss_${b.id}_down.png`
    if (b.spriteCracked) paths[`boss_${b.id}_cracked`] = b.spriteCracked
    if (b.spriteUnarmed) paths[`boss_${b.id}_unarmed`] = b.spriteUnarmed
  })

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
  onGround: true, coyoteTimer: 0,
  shootPoseTimer: 0, hurtPoseTimer: 0, isDashing: false,
  isDown: false, isVictory: false, invincibleTimer: 0,
  scaleX: 1, scaleY: 1, runAnimTimer: 0, controlLocked: false
}
const positionHistory: { x: number; y: number }[] = []

interface Obstacle { x: number; y: number; w: number; h: number; type: 'wall' | 'platform' }
interface Pit { x: number; w: number }
const obstacles = ref<Obstacle[]>([])
const pits = ref<Pit[]>([])

const currentTheme = reactive({
  themeName: 'SUNSET HIGHWAY',
  skyGradient: ['#0f172a', '#311042', '#701a75'],
  groundColor: '#1e1b4b',
  lineColor: '#ec4899',
  bgStyle: 'CITY',
  scrollSpeed: 1.4,
  enemyHue: 0,
  isScrolling: false,
})

interface Bullet {
  x: number; y: number; vx: number; vy: number; gravity?: number
  radius: number; damage: number; color: string
  noteSymbol: string; piercing?: boolean; isGroundCrawling?: boolean; isEnemy?: boolean
}
interface SlashWave {
  radius: number
  damage: number
  angle: number
  timer: number
  maxTimer: number
  color: string
  canClearBullets: boolean // ★ Lv2以上チャージ時のみ敵弾を消去できるフラグ
  absorbHeal: boolean      // ★ Lv3ファイナルチャージ時は消した弾でHP微回復
  hitIds: Set<string>
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
const activeSlashes: SlashWave[] = []
const dropItems: DropItem[] = []
const floatingTexts: FloatingText[] = []
const fireworks: FireworkParticle[] = []
const enemies: Enemy[] = []
const afterimages: { x: number; y: number; facing: number; alpha: number; spriteKey: string }[] = []
let stageAbortController: AbortController | null = null
let screenShakeTimer = 0

// ★ 盾の状態を表す型（型チェックで使い回すため名前を付けて定義）
type ShieldState = 'INTACT' | 'CRACKED' | 'UNARMED'

const boss = reactive({
  active: false, id: 'knight', name: '', spriteKey: 'boss_knight',
  x: 640, y: GROUND_Y, vx: 0, vy: 0,
  hp: 620, maxHp: 620, scale: 1.2, pattern: 'KNIGHT',
  hurtTimer: 0, isDefeated: false, flashAlpha: 0,
  hasShield: false,
  shieldState: 'INTACT' as ShieldState,
  shieldHp: 500, maxShieldHp: 500,
  isFloating: false, warningLaserY: null as number | null, warningSpikeX: null as number | null,
  abortController: null as AbortController | null
})

// ★ 盾の「現在の」状態を取得する関数
// await の待ち時間中に別処理（applyDamageToBoss）が盾を割ることがあるため、
// 直接 boss.shieldState を比較するとTypeScriptが「さっきUNARMEDではないと確認済み」と
// 誤って型を絞り込んでしまう。関数経由で読むことで毎回最新の値として扱わせる。
const getShieldState = (): ShieldState => boss.shieldState

const bgStars = Array.from({ length: 38 }, () => ({
  x: Math.random() * 800, y: Math.random() * 300, size: Math.random() * 2.2 + 1, speed: Math.random() * 0.3 + 0.1
}))
const bgBuildings = Array.from({ length: 16 }, (_, i) => ({
  x: i * 55, w: 42, h: 55 + (i * 37) % 115
}))
let bgScrollX = 0

const spawnFireworkBurst = (customX?: number, customY?: number) => {
  const cx = customX ?? (120 + Math.random() * 560)
  const cy = customY ?? (70 + Math.random() * 180)
  const colors = ['#f472b6', '#facc15', '#38bdf8', '#4ade80', '#c084fc', '#fb7185']
  const color = colors[Math.floor(Math.random() * colors.length)]
  for (let i = 0; i < 28; i++) {
    const angle = (Math.PI * 2 * i) / 28
    const spd = 1.5 + Math.random() * 3.2
    fireworks.push({ x: cx, y: cy, vx: Math.cos(angle) * spd, vy: Math.sin(angle) * spd, color, alpha: 1.0 })
  }
}

// ====================================================
// ★ フル装備を前提とした難易度＆HPスケーリング（2周目は大幅強化！）
// ====================================================
const getDifficultyMultipliers = (stageNum: number) => {
  const loops = Math.floor((stageNum - 1) / 12) // 0: 1周目, 1: 2周目(STAGE 13〜)
  const stageInLoop = (stageNum - 1) % 12
  // 2周目以降は全武装が揃っている前提のため、基礎倍率を 2.8倍（さらに周回ごとに1.8倍）へ引き上げ！
  const loopHpBoost = loops > 0 ? 2.8 * Math.pow(1.8, loops - 1) : 1.0
  const enemyHpMul = (1 + stageInLoop * 0.22) * loopHpBoost
  const bossHpMul = stageNum === 1 ? 1.0 : (1 + stageInLoop * 0.18) * loopHpBoost
  const spdMul = (1 + Math.min(0.45, stageInLoop * 0.05)) * (loops > 0 ? 1.22 : 1.0)
  return { enemyHpMul, bossHpMul, spdMul, extraBarrage: loops }
}

const runGimmickSpawnerAsync = async (stageSignal: AbortSignal) => {
  try {
    while (currentTheme.isScrolling && stageProgress.value < 92) {
      const roll = Math.random()
      const spawnX = 840

      if (roll < 0.30) {
        const pitWidth = 120 + Math.random() * 35
        pits.value.push({ x: spawnX, w: pitWidth })
        obstacles.value.push({ x: spawnX + 15, y: GROUND_Y - 82, w: pitWidth - 25, h: 14, type: 'platform' })
      } else if (roll < 0.58) {
        const wallH = 44 + Math.random() * 22
        obstacles.value.push({ x: spawnX, y: GROUND_Y - wallH, w: 40, h: wallH, type: 'wall' })
      } else if (roll < 0.80) {
        obstacles.value.push({ x: spawnX - 90, y: GROUND_Y - 72, w: 72, h: 14, type: 'platform' })
        obstacles.value.push({ x: spawnX, y: GROUND_Y - 102, w: 42, h: 102, type: 'wall' })
      } else {
        pits.value.push({ x: spawnX + 20, w: 85 })
        obstacles.value.push({ x: spawnX, y: GROUND_Y - 68, w: 80, h: 14, type: 'platform' })
        obstacles.value.push({ x: spawnX + 95, y: GROUND_Y - 125, w: 85, h: 14, type: 'platform' })
      }
      await waitAsync(2200, stageSignal)
    }
  } catch {}
}

const playMegamanIntroAsync = async (stageSignal: AbortSignal) => {
  introState.active = true
  introState.beamY = -60
  player.controlLocked = true
  player.isDown = false
  player.isVictory = false
  player.x = 130
  player.y = -60
  camera.targetZoom = 1.0; camera.zoom = 1.0

  const steps = 20
  for (let i = 0; i <= steps; i++) {
    introState.beamY = (GROUND_Y * i) / steps
    player.y = introState.beamY
    await waitAsync(25, stageSignal)
  }
  player.y = GROUND_Y
  player.scaleX = 1.25; player.scaleY = 0.75
  await waitAsync(800, stageSignal)
  introState.active = false
  player.controlLocked = false
}

const startStageFromCloudRun = async (stageNum: number, fromBossGateCheckpoint = false) => {
  isLoadingStage.value = true
  gameResult.value = null
  currentStage.value = stageNum
  player.isDown = false
  player.isVictory = false
  camera.targetZoom = 1.0; camera.zoom = 1.0

  if (!fromBossGateCheckpoint) {
    stageProgress.value = 0
    checkpointReachedBossGate.value = false
  } else {
    stageProgress.value = 100
  }

  stageAbortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  enemies.length = 0; bullets.length = 0; activeSlashes.length = 0; dropItems.length = 0; fireworks.length = 0
  obstacles.value = []; pits.value = []
  boss.active = false; boss.isDefeated = false; boss.flashAlpha = 0
  boss.warningLaserY = null; boss.warningSpikeX = null
  fogGate.active = false; fogGate.transitioning = false
  boss.abortController?.abort()

  const stg = masterData.stages[(stageNum - 1) % masterData.stages.length]
  currentTheme.themeName = stg.themeName
  currentTheme.skyGradient = stg.skyGradient
  currentTheme.groundColor = stg.groundColor
  currentTheme.lineColor = stg.lineColor
  currentTheme.bgStyle = stg.bgStyle || 'CITY'
  currentTheme.scrollSpeed = stg.scrollSpeed + Math.min(0.6, (stageNum - 1) * 0.06)
  currentTheme.enemyHue = (stageNum - 1) * 45
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
    await playMegamanIntroAsync(stageSignal)

    if (!fromBossGateCheckpoint) {
      currentTheme.isScrolling = true
      runGimmickSpawnerAsync(stageSignal)

      const { enemyHpMul, spdMul } = getDifficultyMultipliers(stageNum)

      let count = 0
      while (stageProgress.value < 96) {
        const tmpl = masterData.enemies[(count + stageNum) % masterData.enemies.length]
        spawnSingleEnemy({
          id: `stg${stageNum}_e${count}`,
          ...tmpl,
          hp: Math.round(tmpl.hp * enemyHpMul),
          speed: tmpl.speed * spdMul
        }, stageSignal)

        if (stageProgress.value > 40 && count % (loopCount.value > 1 ? 2 : 3) === 0) {
          const subTmpl = masterData.enemies[(count + 2) % masterData.enemies.length]
          setTimeout(() => {
            if (!stageSignal.aborted && currentTheme.isScrolling) {
              spawnSingleEnemy({
                id: `stg${stageNum}_sub_${count}`,
                ...subTmpl,
                hp: Math.round(subTmpl.hp * enemyHpMul),
                speed: subTmpl.speed * spdMul
              }, stageSignal)
            }
          }, 650)
        }

        count++
        stageProgress.value = Math.min(100, stageProgress.value + 7.5)
        await waitAsync(Math.max(1350, 2150 - (stageNum % 12) * 85), stageSignal)
      }
    }

    stageProgress.value = 100
    currentTheme.isScrolling = false
    pits.value = []
    for (let i = enemies.length - 1; i >= 0; i--) {
      const e = enemies[i]
      if (e.x < 15 || e.x > 785 || e.y > GROUND_Y + 8) {
        e.abortController.abort()
        enemies.splice(i, 1)
      }
    }
    checkpointReachedBossGate.value = true
    fogGate.active = true
    fogGate.x = 765
  } catch {}
}

const enterFogGateTransitionAsync = async () => {
  if (fogGate.transitioning || boss.active) return
  fogGate.transitioning = true
  player.controlLocked = true
  player.vx = 0

  const stageSignal = stageAbortController!.signal
  try {
    for (let i = 0; i < 42; i++) {
      obstacles.value.forEach(o => { o.x -= 13 })
      pits.value.forEach(p => { p.x -= 13 })
      player.x = Math.max(120, player.x - 13)
      bgScrollX = (bgScrollX + 8) % 55
      await waitAsync(20, stageSignal)
    }
    obstacles.value = [
      { x: 220, y: GROUND_Y - 75, w: 95, h: 14, type: 'platform' },
      { x: 460, y: GROUND_Y - 75, w: 95, h: 14, type: 'platform' }
    ]
    pits.value = []
    fogGate.active = false
    fogGate.transitioning = false

    const bossTmpl = masterData.bosses[(currentStage.value - 1) % masterData.bosses.length]
    const quoteObj = masterData.quotes[(currentStage.value - 1) % masterData.quotes.length]
    const { bossHpMul } = getDifficultyMultipliers(currentStage.value)

    await startBossBattleAsync({
      ...bossTmpl,
      hp: Math.round(bossTmpl.baseHp * bossHpMul),
      cutin_quote: quoteObj
    }, stageSignal)
  } catch {} finally {
    player.controlLocked = false
  }
}

// ====================================================
// ★ ザコ敵AI：2周目以降（loopCount > 1）は攻撃アルゴリズム・弾数が進化！
// ====================================================
const spawnSingleEnemy = (wave: any, stageSignal: AbortSignal) => {
  const enemyAbort = new AbortController()
  stageSignal.addEventListener('abort', () => enemyAbort.abort())

  const isFlying = wave.type === 'note_ghost'
  const startY = isFlying ? 235 : GROUND_Y
  const isExLoop = loopCount.value > 1

  const enemy: Enemy = {
    id: wave.id, type: wave.type, name: wave.name,
    x: 825, y: startY, baseY: startY,
    vx: -wave.speed, vy: 0,
    hp: wave.hp, maxHp: wave.hp, score: wave.score * loopCount.value,
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
          enemy.vx = -1.4; await waitAsync(isExLoop ? 950 : 1300, signal)
          enemy.vx = 0; enemy.isCharging = true; await waitAsync(isExLoop ? 400 : 550, signal)
          enemy.isCharging = false
          enemy.vx = player.x < enemy.x ? (isExLoop ? -5.8 : -4.8) : 4.2
          // 2周目は突進開始時にトゲ弾も前方に飛ばす！
          if (isExLoop) {
            bullets.push({ x: enemy.x - 15, y: enemy.y - 20, vx: -6.2, vy: 0, radius: 7, damage: 14, color: '#ef4444', noteSymbol: '✦', isEnemy: true })
          }
          await waitAsync(900, signal)
        }
      } else if (enemy.type === 'mole') {
        while (enemy.hp > 0) {
          enemy.isHidden = true; await waitAsync(isExLoop ? 1100 : 1400, signal)
          enemy.isHidden = false
          const dir = player.x < enemy.x ? -1 : 1
          bullets.push({ x: enemy.x + dir * 18, y: enemy.y - 22, vx: dir * 4.4, vy: 0, radius: 7, damage: 13, color: '#f59e0b', noteSymbol: '●', isEnemy: true })
          // 2周目は斜め上にもう1発石礫を同時発射！
          if (isExLoop) {
            bullets.push({ x: enemy.x + dir * 18, y: enemy.y - 28, vx: dir * 3.8, vy: -2.2, gravity: 0.06, radius: 7, damage: 13, color: '#f59e0b', noteSymbol: '●', isEnemy: true })
          }
          await waitAsync(1250, signal)
        }
      } else if (enemy.type === 'jelly') {
        while (enemy.hp > 0) {
          if (enemy.vy === 0) enemy.vy = -3.8
          await waitAsync(isExLoop ? 1150 : 1500, signal)
        }
      } else if (enemy.type === 'note_ghost') {
        while (enemy.hp > 0) {
          await waitAsync(isExLoop ? 1500 : 1900, signal)
          const dx = player.x - enemy.x
          const dy = (player.y - 28) - (enemy.y - 20)
          const baseAngle = Math.atan2(dy, dx)
          // 1周目は自機狙い1発、2周目は3方向扇状（3-Way）音符弾に進化！
          const spreads = isExLoop ? [-0.22, 0, 0.22] : [0]
          for (const sp of spreads) {
            bullets.push({
              x: enemy.x - 12, y: enemy.y - 20,
              vx: Math.cos(baseAngle + sp) * 4.0, vy: Math.sin(baseAngle + sp) * 4.0,
              radius: 8, damage: 12, color: '#c084fc', noteSymbol: '♪', isEnemy: true
            })
          }
        }
      }
    } catch {}
  })()
}

// ====================================================
// ★ 全12ボスAI：2周目以降（extra > 0）は弾数増加・連射強化・隙短縮！
// ====================================================
const fireAimedShot = (fromX: number, fromY: number, speed: number, color: string, symbol = '♪', spreadRad = 0, dmg = 14) => {
  const dx = player.x - fromX
  const dy = (player.y - 30) - fromY
  const baseAngle = Math.atan2(dy, dx) + spreadRad
  bullets.push({
    x: fromX, y: fromY,
    vx: Math.cos(baseAngle) * speed, vy: Math.sin(baseAngle) * speed,
    radius: 9, damage: dmg, color, noteSymbol: symbol, isEnemy: true
  })
}

const startBossBattleAsync = async (bossData: any, stageSignal: AbortSignal) => {
  boss.id = bossData.id
  boss.name = bossData.name
  boss.spriteKey = `boss_${bossData.id}`
  boss.maxHp = bossData.hp
  boss.hp = bossData.hp
  boss.scale = bossData.scale
  boss.pattern = bossData.pattern
  boss.x = bossData.isGiantFinalBoss ? 630 : 640
  boss.y = GROUND_Y
  boss.vx = 0; boss.vy = 0
  boss.hurtTimer = 0; boss.isDefeated = false; boss.flashAlpha = 0
  boss.isFloating = false; boss.warningLaserY = null; boss.warningSpikeX = null

  if (bossData.isGiantFinalBoss) {
    boss.hasShield = true
    boss.shieldState = 'INTACT'
    boss.maxShieldHp = Math.round(bossData.hp * 0.48)
    boss.shieldHp = boss.maxShieldHp
  } else {
    boss.hasShield = false
    boss.shieldState = 'UNARMED'
  }

  boss.active = true
  player.controlLocked = true

  camera.targetX = boss.x
  camera.targetY = bossData.isGiantFinalBoss ? GROUND_Y - 140 : GROUND_Y - 45
  camera.targetZoom = bossData.isGiantFinalBoss ? 1.35 : 1.85
  cutin.bossName = bossData.name
  cutin.quote = bossData.cutin_quote.quote
  cutin.source = bossData.cutin_quote.source
  cutin.visible = true

  await waitAsync(2200, stageSignal)

  cutin.visible = false
  camera.targetZoom = 1.0
  camera.targetX = 400
  camera.targetY = 225
  player.controlLocked = false

  boss.abortController = new AbortController()
  stageSignal.addEventListener('abort', () => boss.abortController?.abort())
  const { signal } = boss.abortController

  ;(async () => {
    try {
      while (boss.active && boss.hp > 0 && !boss.isDefeated) {
        await waitAsync(12000, signal)
        if (boss.active && !boss.isDefeated && playerHp.value < maxHp.value) {
          dropItems.push({ x: 180 + Math.random() * 340, y: 80, vy: 0.5, type: 'HEAL', lifeTimer: 600 })
        }
      }
    } catch {}
  })()

  // ★ 周回ごとの弾幕追加数（1周目は0、2周目は+1、3周目は+2...）
  const extra = loopCount.value - 1
  const cooldownScale = extra > 0 ? 0.75 : 1.0

  try {
    while (boss.active && boss.hp > 0 && !boss.isDefeated) {
      if (boss.pattern === 'SUNFLOWER_FINAL') {
        if (boss.shieldState !== 'UNARMED') {
          for (let w = 0; w < 3; w++) {
            if (getShieldState() === 'UNARMED') break
            const count = 2 + extra
            for (let c = 0; c < count; c++) {
              const offset = (c - (count - 1) / 2) * 0.25
              fireAimedShot(boss.x - 75, boss.y - 160, 4.0 + extra * 0.4, '#facc15', '🌻', offset, 16)
            }
            await waitAsync(900 * cooldownScale, signal)
          }
          const prevShieldState: ShieldState = getShieldState()
          boss.shieldState = 'UNARMED'
          floatingTexts.push({ x: boss.x - 40, y: boss.y - 220, text: 'SHIELD DOWN!! CHANCE!', color: '#38bdf8', alpha: 1.0 })
          await executeSunflowerFierceAttackAsync(signal, extra)
          if (boss.shieldHp > 0) boss.shieldState = prevShieldState
        } else {
          await executeSunflowerFierceAttackAsync(signal, extra)
          await waitAsync(1050 * cooldownScale, signal)
        }

      } else if (boss.pattern === 'KNIGHT') {
        boss.vx = 0
        for (let k = 0; k < 1 + extra; k++) {
          bullets.push({ x: boss.x - 24, y: GROUND_Y - 10, vx: -4.4 - extra * 0.8, vy: 0, radius: 10, damage: 13, color: '#ef4444', noteSymbol: '⚔', isGroundCrawling: true, isEnemy: true })
          await waitAsync(320, signal)
        }
        for (let a = -extra; a <= extra; a++) {
          fireAimedShot(boss.x - 20, boss.y - 36, 4.2 + extra * 0.5, '#f87171', '♪', a * 0.2, 13)
        }
        await waitAsync(550 * cooldownScale, signal)
        boss.vy = -3.8; boss.vx = player.x < boss.x ? -4.4 - extra * 0.6 : 4.4 + extra * 0.6
        await waitAsync(800, signal)
        boss.vx = 0; await waitAsync(1050 * cooldownScale, signal)

      } else if (boss.pattern === 'CONCIERGE') {
        const warpSpots = [640, 220, 440, 560]
        boss.x = warpSpots[Math.floor(Math.random() * warpSpots.length)]
        boss.vy = -3.0; await waitAsync(450 * cooldownScale, signal)
        const shots = 3 + extra * 2 // 2周目は5連射！
        for (let i = 0; i < shots; i++) {
          fireAimedShot(boss.x, boss.y - 35, 5.2 + extra * 0.5, '#facc15', '🗝', (Math.random() - 0.5) * (extra * 0.15))
          await waitAsync(210 * cooldownScale, signal)
        }
        await waitAsync(950 * cooldownScale, signal)

      } else if (boss.pattern === 'YUKATA') {
        boss.vx = boss.x > 400 ? -2.4 : 2.4
        if (boss.y >= GROUND_Y - 2) boss.vy = -4.5
        await waitAsync(600, signal)
        boss.vx = 0
        const spreadRange = 2 + extra // 1周目は5方向、2周目は7方向花火！
        for (let a = -spreadRange; a <= spreadRange; a++) {
          fireAimedShot(boss.x, boss.y - 35, 4.1 + extra * 0.4, '#fbbf24', '✿', a * 0.24)
        }
        await waitAsync(1200 * cooldownScale, signal)

      } else if (boss.pattern === 'IVORY') {
        const dashes = 2 + extra
        for (let step = 0; step < dashes; step++) {
          boss.vx = player.x < boss.x ? -5.4 : 5.4
          fireAimedShot(boss.x, boss.y - 35, 5.0, '#fef08a', '✦')
          if (extra > 0) fireAimedShot(boss.x, boss.y - 35, 5.0, '#fef08a', '✦', -0.25)
          await waitAsync(310, signal)
          boss.vx = 0; await waitAsync(260 * cooldownScale, signal)
        }
        if (boss.y >= GROUND_Y - 2) boss.vy = -4.0
        boss.vx = boss.x < 400 ? 4.0 : -4.0
        await waitAsync(800, signal); boss.vx = 0; await waitAsync(550 * cooldownScale, signal)

      } else if (boss.pattern === 'TEA') {
        const cups = 3 + extra * 2 // 2周目は5個のバウンドティーカップ！
        for (let i = 0; i < cups; i++) {
          const dir = player.x < boss.x ? -1 : 1
          bullets.push({
            x: boss.x + dir * 20, y: boss.y - 45,
            vx: dir * (2.6 + i * 1.0), vy: -4.1, gravity: 0.08,
            radius: 10, damage: 14, color: '#34d399', noteSymbol: '☕', isEnemy: true
          })
          await waitAsync(250 * cooldownScale, signal)
        }
        if (boss.y >= GROUND_Y - 2) boss.vy = -3.6
        boss.vx = boss.x > 450 ? -3.0 : 3.0
        await waitAsync(950 * cooldownScale, signal); boss.vx = 0

      } else if (boss.pattern === 'FLOWER') {
        if (boss.y >= GROUND_Y - 2) boss.vy = -4.2
        await waitAsync(580, signal)
        const petals = 5 + extra * 2
        for (let i = 0; i < petals; i++) {
          bullets.push({
            x: 90 + (i * (620 / petals)) + (Math.random() * 20 - 10), y: 40,
            vx: (Math.random() - 0.5) * 1.2, vy: 2.6 + extra * 0.4,
            radius: 10, damage: 14, color: '#f472b6', noteSymbol: '❀', isEnemy: true
          })
        }
        fireAimedShot(boss.x, boss.y - 35, 4.6, '#a7f3d0', '♪')
        if (extra > 0) fireAimedShot(boss.x, boss.y - 35, 4.6, '#a7f3d0', '♪', 0.22)
        await waitAsync(1200 * cooldownScale, signal)

      } else if (boss.pattern === 'CAMELLIA') {
        const ringCount = 8 + extra * 4 // 2周目は12方向全方位結界！
        for (let a = 0; a < ringCount; a++) {
          const rad = (Math.PI * 2 * a) / ringCount
          bullets.push({
            x: boss.x, y: boss.y - 35,
            vx: Math.cos(rad) * (3.9 + extra * 0.4), vy: Math.sin(rad) * (3.9 + extra * 0.4),
            radius: 10, damage: 15, color: '#fb7185', noteSymbol: '🌺', isEnemy: true
          })
        }
        await waitAsync(650 * cooldownScale, signal)
        boss.warningLaserY = GROUND_Y - 26
        await waitAsync(600 * cooldownScale, signal)
        boss.warningLaserY = null
        const dir = player.x < boss.x ? -1 : 1
        for (let k = 0; k < 5 + extra * 2; k++) {
          bullets.push({ x: boss.x + dir * 25, y: GROUND_Y - 26, vx: dir * 10.5, vy: 0, radius: 13, damage: 18, color: '#e11d48', noteSymbol: '━', isEnemy: true })
          await waitAsync(55, signal)
        }
        await waitAsync(950 * cooldownScale, signal)

      } else if (boss.pattern === 'GOTHIC') {
        const spikes = 2 + extra
        for (let i = 0; i < spikes; i++) {
          boss.warningSpikeX = player.x
          await waitAsync(520 * cooldownScale, signal)
          const spikeX = boss.warningSpikeX
          boss.warningSpikeX = null
          if (spikeX !== null) {
            bullets.push({ x: spikeX, y: GROUND_Y, vx: 0, vy: -5.4, radius: 13, damage: 16, color: '#a855f7', noteSymbol: '🥀', isEnemy: true })
            if (extra > 0) {
              bullets.push({ x: spikeX - 45, y: GROUND_Y, vx: 0, vy: -5.0, radius: 11, damage: 15, color: '#a855f7', noteSymbol: '🥀', isEnemy: true })
              bullets.push({ x: spikeX + 45, y: GROUND_Y, vx: 0, vy: -5.0, radius: 11, damage: 15, color: '#a855f7', noteSymbol: '🥀', isEnemy: true })
            }
          }
          fireAimedShot(boss.x, boss.y - 35, 4.8, '#c084fc', '†')
          await waitAsync(380 * cooldownScale, signal)
        }
        if (boss.y >= GROUND_Y - 2) boss.vy = -3.8
        boss.vx = boss.x > 450 ? -3.4 : 3.4
        await waitAsync(900 * cooldownScale, signal); boss.vx = 0

      } else if (boss.pattern === 'KIMONO') {
        const heights = [GROUND_Y - 16, GROUND_Y - 60, GROUND_Y - 110]
        for (const h of heights) {
          const dir = player.x < boss.x ? -1 : 1
          bullets.push({ x: boss.x + dir * 20, y: h, vx: dir * (5.5 + extra * 0.8), vy: 0, radius: 11, damage: 15, color: '#a855f7', noteSymbol: '۞', isEnemy: true })
          await waitAsync(250 * cooldownScale, signal)
        }
        if (enemies.length < 1 + extra) {
          const summonTmpl = masterData.enemies[Math.floor(Math.random() * 3)]
          spawnSingleEnemy({ ...summonTmpl, id: `summon_${Date.now()}` }, signal)
        }
        if (boss.y >= GROUND_Y - 2) boss.vy = -3.6
        boss.vx = boss.x > 450 ? -3.0 : 3.0
        await waitAsync(900 * cooldownScale, signal); boss.vx = 0

      } else if (boss.pattern === 'DRESS') {
        boss.isFloating = true; boss.vy = -2.2
        const notesCount = 4 + extra * 2
        for (let i = 0; i < notesCount; i++) {
          fireAimedShot(boss.x, boss.y - 35, 4.8 + extra * 0.4, '#38bdf8', '♬', Math.sin(i) * 0.3)
          await waitAsync(220 * cooldownScale, signal)
        }
        boss.vx = (player.x - boss.x) * 0.075
        await waitAsync(580, signal)
        boss.isFloating = false; boss.vx = 0; boss.vy = 5.8
        await waitAsync(580, signal)
        bullets.push({ x: boss.x - 18, y: GROUND_Y - 10, vx: -5.4 - extra, vy: 0, radius: 11, damage: 16, color: '#60a5fa', noteSymbol: '🌊', isGroundCrawling: true, isEnemy: true })
        bullets.push({ x: boss.x + 18, y: GROUND_Y - 10, vx: 5.4 + extra, vy: 0, radius: 11, damage: 16, color: '#60a5fa', noteSymbol: '🌊', isGroundCrawling: true, isEnemy: true })
        await waitAsync(950 * cooldownScale, signal)

      } else {
        const spread = 2 + extra
        for (let a = -spread; a <= spread; a++) fireAimedShot(boss.x - 20, boss.y - 38, 4.5 + extra * 0.4, '#f472b6', '○', a * 0.2)
        await waitAsync(700 * cooldownScale, signal)
        const targetY = Math.min(GROUND_Y - 22, Math.max(180, player.y - 25))
        boss.warningLaserY = targetY
        await waitAsync(620 * cooldownScale, signal)
        boss.warningLaserY = null
        const dir = player.x < boss.x ? -1 : 1
        for (let k = 0; k < 6 + extra * 2; k++) {
          bullets.push({ x: boss.x + dir * 25, y: targetY, vx: dir * 10.5, vy: 0, radius: 13, damage: 19, color: '#fde047', noteSymbol: '★', isEnemy: true })
          await waitAsync(55, signal)
        }
        if (boss.y >= GROUND_Y - 2) boss.vy = -3.6
        boss.vx = boss.x > 450 ? -2.8 : 2.8
        await waitAsync(950 * cooldownScale, signal); boss.vx = 0
      }
    }
  } catch {}
}

const executeSunflowerFierceAttackAsync = async (signal: AbortSignal, extra: number) => {
  const spread = 2 + extra
  for (let wave = 0; wave < 2 + extra; wave++) {
    for (let a = -spread; a <= spread; a++) {
      fireAimedShot(boss.x - 45, boss.y - 185, 4.9 + extra * 0.4, '#f59e0b', '🌻', a * 0.22 + wave * 0.1, 17)
    }
    await waitAsync(480, signal)
  }
  const flares = 4 + extra
  for (let i = 0; i < flares; i++) {
    bullets.push({
      x: 100 + i * (500 / flares), y: 30,
      vx: 0, vy: 3.5 + extra * 0.4,
      radius: 12, damage: 17, color: '#fde047', noteSymbol: '☀', isEnemy: true
    })
  }
  await waitAsync(700, signal)
  const laserY = player.y > GROUND_Y - 40 ? GROUND_Y - 24 : GROUND_Y - 95
  boss.warningLaserY = laserY
  await waitAsync(600, signal)
  boss.warningLaserY = null
  for (let k = 0; k < 7 + extra * 2; k++) {
    bullets.push({ x: boss.x - 50, y: laserY, vx: -11, vy: 0, radius: 14, damage: 22, color: '#facc15', noteSymbol: '★', isEnemy: true })
    await waitAsync(50, signal)
  }
  await waitAsync(850, signal)
}

const triggerStageClearSequenceAsync = async () => {
  if (boss.isDefeated || player.isVictory || gameResult.value) return
  boss.isDefeated = true
  boss.vx = 0; boss.vy = 0
  boss.warningLaserY = null; boss.warningSpikeX = null
  boss.abortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  enemies.length = 0
  bullets.length = 0

  screenShakeTimer = 14
  await waitAsync(1300)

  for (let i = 1; i <= 10; i++) {
    boss.flashAlpha = i / 10
    await waitAsync(40)
  }
  spawnFireworkBurst(boss.x, boss.y - 45)
  boss.active = false
  boss.flashAlpha = 0

  score.value += 2500 * currentStage.value
  player.isVictory = true
  player.vx = 0
  player.hurtPoseTimer = 0
  camera.targetX = player.x
  camera.targetY = player.y - 35
  camera.targetZoom = 1.85

  for (let f = 1; f <= 6; f++) {
    setTimeout(() => spawnFireworkBurst(player.x + (Math.random() - 0.5) * 220, player.y - 60 - Math.random() * 80), f * 280)
  }

  await waitAsync(2100)
  camera.targetZoom = 1.0
  gameResult.value = 'CLEAR'
}

const onEnemyDefeated = (e: Enemy) => {
  score.value += e.score
  e.abortController.abort()
  const roll = Math.random()
  if (roll < 0.08) dropItems.push({ x: e.x, y: e.y - 16, vy: -2.6, type: '1UP', lifeTimer: 450 })
  else if (roll < 0.42) dropItems.push({ x: e.x, y: e.y - 16, vy: -2.4, type: 'HEAL', lifeTimer: 450 })
  else if (roll < 0.68) dropItems.push({ x: e.x, y: e.y - 16, vy: -2.4, type: 'SCORE', lifeTimer: 450 })
}

// ====================================================
// ★ クリアボーナス適用：攻撃倍率の上昇はすべて均一「+5% (+0.05)」、最大HPは「+10」
// ====================================================
const selectBonusAndNextStage = (choiceId: string) => {
  if (choiceId === 'DOUBLE') {
    if (upgrades.doubleShotLv < 2) upgrades.doubleShotLv++
    else upgrades.powerMultiplier = Math.round((upgrades.powerMultiplier + 0.05) * 100) / 100
  } else if (choiceId === 'SLASH') {
    if (upgrades.slashLv < 2) upgrades.slashLv++
    else upgrades.powerMultiplier = Math.round((upgrades.powerMultiplier + 0.05) * 100) / 100
  } else if (choiceId === 'OPTION') {
    if (upgrades.options < 2) upgrades.options++
    else upgrades.powerMultiplier = Math.round((upgrades.powerMultiplier + 0.05) * 100) / 100
  } else if (choiceId === 'BARRIER') {
    upgrades.barrierHp = 3
    upgrades.powerMultiplier = Math.round((upgrades.powerMultiplier + 0.05) * 100) / 100
  } else if (choiceId === 'CHARGE3') {
    if (upgrades.maxChargeLevel >= 3) {
      upgrades.powerMultiplier = Math.round((upgrades.powerMultiplier + 0.05) * 100) / 100
    }
    upgrades.maxChargeLevel = 3
  } else if (choiceId === 'VITAL') {
    maxHp.value += 10 // +30 → +10 へ調整
    playerHp.value = maxHp.value
    lives.value++
  }
  playerHp.value = Math.min(maxHp.value, playerHp.value + 30)
  startStageFromCloudRun(currentStage.value + 1, false)
}

const retryFromCheckpoint = () => {
  lives.value = 3
  playerHp.value = maxHp.value
  startStageFromCloudRun(currentStage.value, true)
}

const resetFullGame = () => {
  score.value = 0; lives.value = 3; maxHp.value = 100; playerHp.value = 100
  upgrades.doubleShotLv = 0; upgrades.slashLv = 0; upgrades.options = 0
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

// ====================================================
// ★ ショット＆偃月薙ぎ払い（Lv.2以上チャージ時のみ弾消し発動！）
// ====================================================
const fireFromPosition = (originX: number, originY: number, level: number, isOption = false) => {
  const pMul = (isOption ? 0.55 : 1.0) * upgrades.powerMultiplier
  const dir = player.facing

  const baseConfigs = [
    { speed: 7.5, radius: 8,  dmg: 14, color: '#f472b6', symbol: '♪', pierce: false },
    { speed: 9.5, radius: 12, dmg: 28, color: '#38bdf8', symbol: '♬', pierce: false },
    { speed: 12,  radius: 18, dmg: 50, color: '#facc15', symbol: '♪♬', pierce: true },
    { speed: 14,  radius: 24, dmg: 76, color: '#c084fc', symbol: '𝄞♪', pierce: true },
  ]
  const cfg = baseConfigs[level] || baseConfigs[0]

  bullets.push({
    x: originX, y: originY, vx: dir * cfg.speed, vy: 0,
    radius: cfg.radius, damage: Math.round(cfg.dmg * pMul), color: cfg.color, noteSymbol: cfg.symbol, piercing: cfg.pierce
  })

  if (upgrades.doubleShotLv > 0) {
    const upCfg = upgrades.doubleShotLv >= 2 ? cfg : baseConfigs[0]
    bullets.push({
      x: originX, y: originY - 5,
      vx: dir * (upCfg.speed * 0.75), vy: -upCfg.speed * 0.65,
      radius: upCfg.radius, damage: Math.round(upCfg.dmg * pMul),
      color: upCfg.color, noteSymbol: upCfg.symbol, piercing: upCfg.pierce
    })
  }

  // ★ 偃月サウンド薙ぎ払い：
  // 通常連打では敵弾は消せず、Slash Lv.2 かつ 2段階目（Lv.2）以上チャージした時のみ敵弾を斬り払える！
  if (upgrades.slashLv > 0 && !isOption) {
    const effectiveLv = upgrades.slashLv >= 2 ? level : 0
    const slashRadius = 54 + effectiveLv * 18
    const slashDmg = Math.round((22 + effectiveLv * 22) * upgrades.powerMultiplier)
    const slashColors = ['#fbbf24', '#38bdf8', '#facc15', '#e879f9']
    const canClear = upgrades.slashLv >= 2 && level >= 2 // ★ Lv2チャージ以上でのみ弾消し発動！
    activeSlashes.push({
      radius: slashRadius,
      damage: slashDmg,
      angle: 0,
      timer: 15 + effectiveLv * 4,
      maxTimer: 15 + effectiveLv * 4,
      color: slashColors[effectiveLv] || '#fbbf24',
      canClearBullets: canClear,
      absorbHeal: canClear && level >= 3, // Lv3ファイナルチャージ時は弾を斬るとHP+2回復！
      hitIds: new Set<string>()
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
}

const startDashAsync = async () => {
  if (!player.onGround || player.isDashing || player.controlLocked || player.isDown || player.isVictory) return
  player.isDashing = true
  player.vx = player.facing * PHYSICS.DASH_SPEED
  try { await waitAsync(280) } finally { player.isDashing = false }
}

const keys = new Set<string>()
const onKeyDown = (e: KeyboardEvent) => {
  if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Space', 'KeyZ', 'KeyX', 'KeyC'].includes(e.code)) {
    e.preventDefault()
  }
  if (keys.has(e.code) || player.controlLocked || deathOverlay.active || player.isDown || player.isVictory) return
  keys.add(e.code)

  if ((e.code === 'ArrowUp' || e.code === 'Space' || e.code === 'KeyZ') && (player.onGround || player.coyoteTimer > 0)) {
    player.vy = PHYSICS.JUMP_VELOCITY
    player.onGround = false
    player.coyoteTimer = 0
    player.scaleX = 0.85; player.scaleY = 1.18
  }
  if (e.code === 'ArrowDown' || e.code === 'KeyC') {
    startDashAsync()
  }
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

const getPlayerSpriteKey = () => {
  if (player.isDown) return 'down'
  if (player.isVictory) return 'victory'
  if (player.hurtPoseTimer > 0) return 'hurt'
  if (!player.onGround) return player.shootPoseTimer > 0 ? 'jumpShoot' : 'jump'
  if (player.shootPoseTimer > 0) return 'shoot'
  if (Math.abs(player.vx) > 0.4) return Math.floor(player.runAnimTimer / 9) % 2 === 0 ? 'run1' : 'run2'
  return 'idle'
}

const getBossActiveSpriteKey = (): string => {
  if (boss.isDefeated) {
    const downKey = `boss_${boss.id}_down`
    if (sprites[downKey]) return downKey
    if (boss.hasShield && sprites[`boss_${boss.id}_unarmed`]) return `boss_${boss.id}_unarmed`
    return boss.spriteKey
  }
  if (boss.hurtTimer > 0) {
    const hurtKey = `boss_${boss.id}_hurt`
    if (sprites[hurtKey]) return hurtKey
  }
  if (boss.hasShield) {
    if (boss.shieldState === 'INTACT') return `boss_${boss.id}`
    if (boss.shieldState === 'CRACKED') return `boss_${boss.id}_cracked`
    return `boss_${boss.id}_unarmed`
  }
  return boss.spriteKey
}

const applyDamageToBoss = (rawDamage: number, isPiercing = false) => {
  if (!boss.active || boss.isDefeated) return

  if (boss.hasShield && boss.shieldState !== 'UNARMED') {
    boss.shieldHp = Math.max(0, boss.shieldHp - rawDamage)
    floatingTexts.push({ x: boss.x - 55, y: boss.y - 160 + (Math.random() - 0.5) * 30, text: `GUARD -${rawDamage}`, color: '#38bdf8', alpha: 1.0 })

    if (boss.shieldHp <= 0) {
      boss.shieldState = 'UNARMED'
      screenShakeTimer = 14
      spawnFireworkBurst(boss.x - 50, boss.y - 150)
      floatingTexts.push({ x: boss.x - 40, y: boss.y - 210, text: 'SHIELD BREAK!!', color: '#facc15', alpha: 1.0 })
    } else if (boss.shieldHp <= boss.maxShieldHp * 0.5 && boss.shieldState === 'INTACT') {
      boss.shieldState = 'CRACKED'
      screenShakeTimer = 8
      floatingTexts.push({ x: boss.x - 40, y: boss.y - 190, text: 'SHIELD CRACKED!', color: '#fbbf24', alpha: 1.0 })
    }
    return
  }

  boss.hp = Math.max(0, boss.hp - rawDamage)
  boss.hurtTimer = 14
  floatingTexts.push({
    x: boss.x + (Math.random() - 0.5) * 24,
    y: boss.y - (boss.hasShield ? 180 : 55),
    text: `${rawDamage}`,
    color: isPiercing ? '#facc15' : '#f472b6',
    alpha: 1.0
  })
  if (isPiercing) screenShakeTimer = 5
  if (boss.hp <= 0) {
    triggerStageClearSequenceAsync()
  }
}

const triggerYouDiedSequenceAsync = async (fellInPit = false) => {
  if (deathOverlay.active || player.isDown || gameResult.value) return
  player.controlLocked = true
  player.isDown = true
  player.vx = 0
  chargeAbort?.abort()
  chargeLevel.value = 0

  stageAbortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  boss.abortController?.abort()

  if (!fellInPit) {
    await waitAsync(1100)
  }

  lives.value--
  const resumeAtFog = boss.active || checkpointReachedBossGate.value
  deathOverlay.message = lives.value > 0
    ? (resumeAtFog ? 'ボス部屋前（白い霧）から再出撃します...' : 'ステージ初期地点から再出撃します...')
    : '残機がすべて失われました'
  deathOverlay.active = true

  await waitAsync(2400)
  deathOverlay.active = false

  if (lives.value > 0) {
    playerHp.value = maxHp.value
    startStageFromCloudRun(currentStage.value, resumeAtFog)
  } else {
    gameResult.value = 'GAMEOVER'
  }
}

const damagePlayer = (amount: number) => {
  if (player.invincibleTimer > 0 || deathOverlay.active || player.isDown || player.isVictory || gameResult.value || player.controlLocked) return
  if (upgrades.barrierHp > 0) {
    upgrades.barrierHp--; player.invincibleTimer = 55
    floatingTexts.push({ x: player.x, y: player.y - 50, text: 'SHIELD!', color: '#38bdf8', alpha: 1.0 })
    return
  }

  playerHp.value = Math.max(0, playerHp.value - amount)
  player.invincibleTimer = 82
  player.hurtPoseTimer = 24
  screenShakeTimer = 8
  floatingTexts.push({ x: player.x, y: player.y - 55, text: `-${amount}`, color: '#ef4444', alpha: 1.0 })

  if (playerHp.value <= 0) {
    triggerYouDiedSequenceAsync(false)
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

  camera.zoom += (camera.targetZoom - camera.zoom) * 0.12
  camera.focusX += (camera.targetX - camera.focusX) * 0.12
  camera.focusY += (camera.targetY - camera.focusY) * 0.12

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

  if (!player.controlLocked && !deathOverlay.active && !player.isDown && !player.isVictory) {
    if (!player.isDashing) {
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
          if (player.x <= obs.x) {
            nextX = obs.x - 14
            if (nextX < 28) {
              player.y = obs.y; player.vy = -3.5; nextX = obs.x + obs.w / 2
            }
          } else {
            nextX = obs.x + obs.w + 14
          }
          player.vx = 0
        }
      }
    }
    player.x = Math.max(28, Math.min(775, nextX))

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

    if (!landed && !isOverPit(player.x) && player.y >= GROUND_Y && prevY <= GROUND_Y + 10) {
      player.y = GROUND_Y; player.vy = 0; landed = true
    }

    if (player.y > canvas.height + 30 && !deathOverlay.active && !player.isDown) {
      playerHp.value = 0
      triggerYouDiedSequenceAsync(true)
    }

    if (landed) {
      if (!player.onGround) { player.scaleX = 1.16; player.scaleY = 0.84 }
      player.onGround = true
      player.coyoteTimer = 6
    } else {
      player.onGround = false
      if (player.coyoteTimer > 0) player.coyoteTimer--
    }
  }

  positionHistory.push({ x: player.x, y: player.y })
  if (positionHistory.length > 40) positionHistory.shift()

  player.scaleX += (1 - player.scaleX) * 0.18
  player.scaleY += (1 - player.scaleY) * 0.18
  if (player.shootPoseTimer > 0) player.shootPoseTimer--
  if (player.hurtPoseTimer > 0) player.hurtPoseTimer--
  if (player.invincibleTimer > 0) player.invincibleTimer--
  if (boss.hurtTimer > 0) boss.hurtTimer--
  if (Math.abs(player.vx) > 0.4) player.runAnimTimer++

  if (player.isDashing || chargeLevel.value >= 2) {
    afterimages.push({ x: player.x, y: player.y, facing: player.facing, alpha: 0.4, spriteKey: getPlayerSpriteKey() })
  }

  // ==========================================
  // 描画開始
  // ==========================================
  ctx.save()
  if (Math.abs(camera.zoom - 1.0) > 0.01) {
    ctx.translate(canvas.width / 2, canvas.height / 2)
    ctx.scale(camera.zoom, camera.zoom)
    ctx.translate(-camera.focusX, -camera.focusY)
  }
  if (screenShakeTimer > 0) {
    screenShakeTimer--
    ctx.translate((Math.random() - 0.5) * 6, (Math.random() - 0.5) * 6)
  }

  const skyGrad = ctx.createLinearGradient(0, 0, 0, GROUND_Y)
  skyGrad.addColorStop(0, currentTheme.skyGradient[0])
  skyGrad.addColorStop(0.5, currentTheme.skyGradient[1])
  skyGrad.addColorStop(1, currentTheme.skyGradient[2])
  ctx.fillStyle = skyGrad
  ctx.fillRect(-100, -100, canvas.width + 200, canvas.height + 200)

  ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'
  bgStars.forEach(s => {
    s.x = (s.x - (s.speed + scrollSpd * 0.2) + 800) % 800
    if (currentTheme.bgStyle === 'OCEAN') {
      ctx.beginPath(); ctx.arc(s.x, (s.y - now * 0.02 + 300) % 300, s.size + 1, 0, Math.PI * 2); ctx.strokeStyle = 'rgba(125, 211, 252, 0.4)'; ctx.stroke()
    } else {
      ctx.fillRect(s.x, s.y, s.size, s.size)
    }
  })

  if (currentTheme.bgStyle === 'GOTHIC') {
    ctx.save()
    ctx.beginPath(); ctx.arc(640, 110, 52, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(225, 29, 72, 0.35)'; ctx.shadowColor = '#e11d48'; ctx.shadowBlur = 25; ctx.fill()
    ctx.restore()
  }

  bgScrollX = (bgScrollX + scrollSpd * 0.4) % 55
  ctx.fillStyle = 'rgba(15, 23, 42, 0.55)'
  bgBuildings.forEach((b, idx) => {
    const bx = (b.x - bgScrollX + 880) % 880 - 55
    if (currentTheme.bgStyle === 'CATHEDRAL' || currentTheme.bgStyle === 'GOTHIC') {
      ctx.beginPath()
      ctx.moveTo(bx, GROUND_Y)
      ctx.lineTo(bx, GROUND_Y - b.h)
      ctx.lineTo(bx + b.w / 2, GROUND_Y - b.h - 28)
      ctx.lineTo(bx + b.w, GROUND_Y - b.h)
      ctx.lineTo(bx + b.w, GROUND_Y)
      ctx.fill()
    } else if (currentTheme.bgStyle === 'CYBER') {
      const dynH = 40 + Math.abs(Math.sin(now * 0.004 + idx)) * 90
      ctx.fillRect(bx, GROUND_Y - dynH, b.w - 8, dynH)
    } else {
      ctx.fillRect(bx, GROUND_Y - b.h, b.w, b.h)
    }
  })

  ctx.fillStyle = currentTheme.groundColor
  ctx.fillRect(-100, GROUND_Y, canvas.width + 200, canvas.height - GROUND_Y + 100)
  ctx.strokeStyle = currentTheme.lineColor
  ctx.lineWidth = 3
  ctx.beginPath(); ctx.moveTo(-100, GROUND_Y); ctx.lineTo(canvas.width + 100, GROUND_Y); ctx.stroke()

  if (boss.active) {
    ctx.save()
    ctx.strokeStyle = 'rgba(244, 63, 94, 0.35)'
    ctx.lineWidth = 3; ctx.setLineDash([8, 6])
    ctx.beginPath()
    ctx.moveTo(20, 0); ctx.lineTo(20, GROUND_Y)
    ctx.moveTo(780, 0); ctx.lineTo(780, GROUND_Y)
    ctx.stroke()
    ctx.restore()
  }

  for (const pit of pits.value) {
    ctx.fillStyle = '#020617'
    ctx.fillRect(pit.x, GROUND_Y - 2, pit.w, canvas.height - GROUND_Y + 4)
    ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 2
    ctx.strokeRect(pit.x, GROUND_Y, pit.w, canvas.height - GROUND_Y)
  }

  for (const obs of obstacles.value) {
    ctx.save()
    if (obs.type === 'wall') {
      ctx.fillStyle = '#1e293b'
      ctx.fillRect(obs.x, obs.y, obs.w, obs.h)
      ctx.strokeStyle = currentTheme.lineColor; ctx.lineWidth = 2
      ctx.strokeRect(obs.x, obs.y, obs.w, obs.h)
    } else {
      ctx.fillStyle = '#334155'
      ctx.fillRect(obs.x, obs.y, obs.w, obs.h)
      ctx.fillStyle = '#38bdf8'
      ctx.fillRect(obs.x, obs.y, obs.w, 3)
    }
    ctx.restore()
  }

  if (fogGate.active) {
    ctx.save()
    const fogGrad = ctx.createLinearGradient(fogGate.x - 25, 0, canvas.width, 0)
    fogGrad.addColorStop(0, 'rgba(255, 255, 255, 0)')
    fogGrad.addColorStop(0.5, enemies.length === 0 ? 'rgba(241, 245, 249, 0.78)' : 'rgba(148, 163, 184, 0.35)')
    fogGrad.addColorStop(1, 'rgba(255, 255, 255, 0.95)')
    ctx.fillStyle = fogGrad
    ctx.fillRect(fogGate.x - 25, 0, 60, GROUND_Y)

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

  const playerDrawSize = Math.round(96 * CHAR_SCALE)
  for (let i = afterimages.length - 1; i >= 0; i--) {
    const aft = afterimages[i]
    aft.alpha -= 0.05
    if (aft.alpha <= 0) { afterimages.splice(i, 1); continue }
    drawSprite(ctx, sprites[aft.spriteKey], aft.x, aft.y, aft.facing, playerDrawSize, 1, 1, aft.alpha, 190)
  }

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

  if (chargeLevel.value > 0 && !player.isDown) {
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

  if (introState.active && player.y < GROUND_Y - 4) {
    ctx.save()
    ctx.fillStyle = 'rgba(244, 114, 182, 0.85)'
    ctx.shadowColor = '#ec4899'; ctx.shadowBlur = 18
    ctx.fillRect(player.x - 6, 0, 12, player.y)
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(player.x - 2, 0, 4, player.y)
    ctx.restore()
  } else if (player.isDown || player.isVictory || player.invincibleTimer % 4 < 2) {
    const dashScaleY = player.isDashing ? 0.74 : player.scaleY
    const drawFacing = player.isVictory ? 1 : player.facing
    drawSprite(ctx, sprites[getPlayerSpriteKey()], player.x, player.y, drawFacing, playerDrawSize, player.scaleX, dashScaleY, 1.0, 0)
  }

  // ==========================================
  // ★ 偃月サウンド薙ぎ払い（canClearBullets = true の時のみ敵弾を消去！）
  // ==========================================
  for (let i = activeSlashes.length - 1; i >= 0; i--) {
    const sw = activeSlashes[i]
    sw.timer--
    sw.angle += (Math.PI * 2) / sw.maxTimer
    const cx = player.x
    const cy = player.y - 30

    ctx.save()
    ctx.translate(cx, cy)
    ctx.rotate(sw.angle * player.facing)
    ctx.beginPath()
    ctx.arc(0, 0, sw.radius, -0.4, Math.PI * 1.35)
    ctx.strokeStyle = sw.color
    ctx.lineWidth = sw.canClearBullets ? 9 : 6
    ctx.shadowColor = sw.color; ctx.shadowBlur = sw.canClearBullets ? 18 : 10
    ctx.stroke()
    ctx.restore()

    // ★ Lv2チャージ以上（canClearBullets === true）の時だけ敵弾を斬り払える！
    if (sw.canClearBullets) {
      for (let bIdx = bullets.length - 1; bIdx >= 0; bIdx--) {
        const b = bullets[bIdx]
        if (b.isEnemy && Math.hypot(b.x - cx, b.y - cy) < sw.radius + b.radius) {
          bullets.splice(bIdx, 1)
          score.value += 50
          if (sw.absorbHeal && playerHp.value < maxHp.value) {
            playerHp.value = Math.min(maxHp.value, playerHp.value + 2)
          }
        }
      }
    }

    for (let eIdx = enemies.length - 1; eIdx >= 0; eIdx--) {
      const e = enemies[eIdx]
      if (!sw.hitIds.has(e.id) && Math.hypot(e.x - cx, (e.y - 26) - cy) < sw.radius + 22) {
        sw.hitIds.add(e.id)
        e.hp -= sw.damage
        floatingTexts.push({ x: e.x, y: e.y - 45, text: `SLASH ${sw.damage}!`, color: sw.color, alpha: 1.0 })
        if (e.hp <= 0) {
          onEnemyDefeated(e); enemies.splice(eIdx, 1)
        }
      }
    }

    if (boss.active && !boss.isDefeated && !sw.hitIds.has('BOSS')) {
      const bossCenterY = boss.hasShield ? boss.y - 140 : boss.y - 38
      const hitDist = boss.hasShield ? sw.radius + 55 : sw.radius + 34
      if (Math.hypot(boss.x - cx, bossCenterY - cy) < hitDist) {
        sw.hitIds.add('BOSS')
        applyDamageToBoss(sw.damage, true)
      }
    }

    if (sw.timer <= 0) activeSlashes.splice(i, 1)
  }

  if (upgrades.barrierHp > 0 && !player.isDown) {
    ctx.save()
    ctx.beginPath()
    ctx.arc(player.x, player.y - 34, 38, 0, Math.PI * 2)
    ctx.strokeStyle = `rgba(56, 189, 248, ${0.35 + upgrades.barrierHp * 0.2})`
    ctx.lineWidth = 2.5; ctx.setLineDash([6, 5]); ctx.stroke()
    ctx.restore()
  }

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

    if (!player.isDown && Math.abs(player.x - item.x) < 28 && Math.abs((player.y - 24) - item.y) < 30) {
      if (item.type === '1UP') lives.value++
      else if (item.type === 'HEAL') playerHp.value = Math.min(maxHp.value, playerHp.value + 25)
      else score.value += 300
      floatingTexts.push({ x: item.x, y: item.y - 15, text: label, color: '#4ade80', alpha: 1.0 })
      dropItems.splice(i, 1)
      continue
    }
    if (item.lifeTimer <= 0 || item.y > canvas.height + 30) dropItems.splice(i, 1)
  }

  const enemyDrawSize = Math.round(76 * CHAR_SCALE)
  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i]
    const prevEnemyY = e.y
    if (!e.isStunned) e.x += e.vx - scrollSpd * 0.65

    if (fogGate.active && e.x < 35 && e.vx < 0) e.vx = -e.vx
    else if (fogGate.active && e.x > 730 && e.vx > 0) e.vx = -e.vx

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

    if (!player.isDown && !player.isVictory && Math.abs(player.x - e.x) < 28 && Math.abs(player.y - e.y) < 34) {
      if (player.vy > 0 && player.y < e.y - 10) {
        if (e.spiky) {
          damagePlayer(14)
        } else if (e.stompable) {
          player.vy = PHYSICS.BOUNCE_VELOCITY
          player.scaleX = 1.22; player.scaleY = 0.78
          const stompDmg = Math.round(24 * upgrades.powerMultiplier)
          e.hp -= stompDmg
          floatingTexts.push({ x: e.x, y: e.y - 45, text: `${stompDmg}`, color: '#facc15', alpha: 1.0 })
          if (e.type === 'turtle' && e.hp > 0) e.isStunned = true
          if (e.hp <= 0) { onEnemyDefeated(e); enemies.splice(i, 1); continue }
        }
      } else if (!player.isDashing) {
        damagePlayer(12)
      }
    }

    if (e.x < -40 || e.x > 870 || e.y > GROUND_Y + 25) {
      e.abortController.abort()
      enemies.splice(i, 1)
    }
  }

  if (boss.active) {
    if (!boss.isDefeated) {
      boss.x += boss.vx
      if (boss.x <= BOSS_ARENA.LEFT) {
        boss.x = BOSS_ARENA.LEFT
        if (boss.vx < 0) boss.vx = -boss.vx * 0.5
      } else if (boss.x >= BOSS_ARENA.RIGHT) {
        boss.x = BOSS_ARENA.RIGHT
        if (boss.vx > 0) boss.vx = -boss.vx * 0.5
      }

      if (boss.isFloating) {
        boss.y += boss.vy
        if (boss.y < 160) { boss.y = 160; boss.vy = 0 }
        if (boss.y > 265) { boss.y = 265; boss.vy = 0 }
      } else {
        boss.vy += PHYSICS.GRAVITY
        boss.y += boss.vy
        if (boss.y < BOSS_ARENA.TOP) { boss.y = BOSS_ARENA.TOP; if (boss.vy < 0) boss.vy = 0 }
        if (boss.y >= BOSS_ARENA.BOTTOM) { boss.y = BOSS_ARENA.BOTTOM; boss.vy = 0 }
      }
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
    const activeBossKey = getBossActiveSpriteKey()

    ctx.save()
    if (boss.flashAlpha > 0) {
      ctx.filter = `brightness(${1 + boss.flashAlpha * 5}) opacity(${1 - boss.flashAlpha * 0.7})`
    } else if (boss.hurtTimer > 0 && !sprites[`boss_${boss.id}_hurt`]) {
      ctx.filter = 'brightness(1.8)'
    }
    drawSprite(ctx, sprites[activeBossKey], boss.x, boss.y, bossFacing, bossDrawSize, 1, 1, 1.0, 0)
    ctx.restore()

    const contactW = boss.hasShield ? 55 : 32
    const contactH = boss.hasShield ? 260 : 44
    if (!boss.isDefeated && !player.isDown && !player.isVictory &&
        Math.abs(player.x - boss.x) < contactW && player.y > boss.y - contactH && player.y <= boss.y + 10) {
      damagePlayer(16)
    }
  }

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
      b.y = GROUND_Y - 8; b.vy = -3.2
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
      if (!player.isDown && !player.isVictory && Math.abs(b.x - player.x) < 17 && Math.abs(b.y - (player.y - 28)) < 25) {
        damagePlayer(b.damage)
        bullets.splice(i, 1)
        continue
      }
    } else {
      let hit = false
      for (let j = enemies.length - 1; j >= 0; j--) {
        const e = enemies[j]
        if (Math.abs(b.x - e.x) < 28 && Math.abs(b.y - (e.y - 26)) < 30) {
          if (e.isHidden && !b.piercing) {
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

      if (boss.active && !boss.isDefeated) {
        const hitW = boss.hasShield ? 68 : 36
        const hitTop = boss.hasShield ? boss.y - 290 : boss.y - 75
        if (Math.abs(b.x - boss.x) < hitW && b.y >= hitTop && b.y <= boss.y) {
          applyDamageToBoss(b.damage, !!b.piercing)
          if (!b.piercing || (boss.hasShield && boss.shieldState !== 'UNARMED')) {
            bullets.splice(i, 1)
          }
          continue
        }
      }
    }

    if (b.x < -60 || b.x > canvas.width + 60 || b.y < -60 || b.y > canvas.height + 60) {
      bullets.splice(i, 1)
    }
  }

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

  if ((player.isVictory || gameResult.value === 'CLEAR') && Math.random() < 0.06) spawnFireworkBurst()
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