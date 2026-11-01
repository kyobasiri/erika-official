<template>
  <div class="rock-action-page bg-zinc-950 text-zinc-200 select-none font-sans"
       :class="immersive ? 'is-immersive' : 'min-h-screen pt-20 sm:pt-24 pb-8 sm:pb-12'">
    <div :class="immersive ? '' : 'w-full max-w-4xl mx-auto px-2 sm:px-4'">
      <!-- ページタイトルヘッダー（他ゲーム画面と統一） -->
      <header v-if="!immersive" class="text-center mb-3 sm:mb-5">
        <p class="hidden sm:block text-xs tracking-[0.35em] text-amber-400 mb-1 font-mono">
          SCROLLING ACTION &amp; SHOOTING
        </p>
        <h1 class="text-2xl sm:text-4xl font-black tracking-tight text-white">
          ERIKA ROCK ACTION
        </h1>
        <p v-if="isTouch && !isLandscape" class="mt-1.5 text-[11px] text-cyan-300">
          📱 端末を横向きにすると大画面モードで遊べます
        </p>
      </header>

      <div ref="shellRef" class="game-shell"
           :class="immersive
             ? 'fixed inset-0 z-[60] flex flex-col bg-black'
             : 'bg-slate-950 rounded-xl overflow-hidden shadow-2xl border border-slate-800'"
           @contextmenu.prevent>
        <!-- ==================================================== -->
        <!-- 上部ダッシュボードUI（狭い画面・大画面モードでは1〜2行に圧縮） -->
        <!-- ==================================================== -->
        <div class="hud bg-slate-900 border-b border-slate-800 flex items-center"
             :class="immersive
               ? 'flex-nowrap gap-2 sm:gap-3 px-2 py-1 safe-x'
               : 'flex-wrap justify-between gap-x-3 gap-y-2 px-2.5 sm:px-4 py-2 sm:py-2.5'">
          <div class="flex items-center gap-2 sm:gap-3 min-w-0">
            <div class="bg-slate-950 rounded-lg border border-slate-800 text-center shrink-0"
                 :class="immersive ? 'px-2 py-0.5 min-w-[58px]' : 'px-2 sm:px-3 py-1 sm:py-1.5 min-w-[64px] sm:min-w-[82px]'">
              <div class="text-[9px] sm:text-[10px] font-mono" :class="loopCount > 1 ? 'text-amber-400 font-bold' : 'text-slate-400'">
                {{ loopCount > 1 ? `LOOP ${loopCount} EX` : 'STAGE' }}
              </div>
              <div class="font-black text-pink-400 leading-none" :class="immersive ? 'text-base' : 'text-base sm:text-lg'">{{ currentStage }}</div>
            </div>

            <div class="min-w-0">
              <div class="flex items-center gap-2 sm:gap-3 mb-1">
                <span class="hidden sm:inline text-xs font-extrabold text-white tracking-wider">ERIKA</span>
                <div class="flex items-center gap-0.5 text-rose-500 text-xs sm:text-sm leading-none">
                  <template v-if="lives <= 5"><span v-for="n in lives" :key="n">♥</span></template>
                  <span v-else>♥×{{ lives }}</span>
                  <span v-if="lives === 0" class="text-[10px] text-slate-500">LAST</span>
                </div>
                <span class="text-[10px] sm:text-xs font-mono text-slate-300 whitespace-nowrap">HP {{ playerHp }}/{{ maxHp }}</span>
              </div>
              <div class="h-2.5 sm:h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-700 p-0.5"
                   :class="immersive ? 'w-24 sm:w-36' : 'w-28 sm:w-40'">
                <div class="h-full rounded-full bg-gradient-to-r from-pink-500 via-rose-400 to-emerald-400 transition-all duration-150"
                     :class="playerHp <= maxHp * 0.25 ? 'animate-pulse' : ''"
                     :style="{ width: `${Math.min(100, (playerHp / maxHp) * 100)}%` }"></div>
              </div>
            </div>

            <div class="px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all whitespace-nowrap"
                 :class="[chargeBadgeClass, immersive ? 'hidden lg:block' : 'hidden sm:block']">
              {{ chargeLevel === 3 ? 'FINAL CHARGE!!' : chargeLevel === 2 ? 'LV.2 PIERCE' : chargeLevel === 1 ? 'LV.1 CHARGE' : 'BUSTER READY' }}
            </div>
          </div>

          <!-- API is intentionally visible, including offline fallback. -->
          <div class="flex items-center gap-1.5 text-[10px] font-mono px-2 py-1 rounded-lg border shrink-0"
               :class="[cloudStatus === 'ONLINE' ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300' :
                 cloudStatus === 'CONNECTING' ? 'bg-amber-950/70 border-amber-700 text-amber-300' :
                 'bg-slate-950 border-slate-700 text-slate-400', immersive ? 'hidden xl:flex' : 'hidden sm:flex']"
               role="status" aria-live="polite" :title="cloudStatus === 'ONLINE' ? 'CLOUD RUN' : cloudStatus">
            <span class="inline-block h-1.5 w-1.5 rounded-full"
                  :class="cloudStatus === 'ONLINE' ? 'bg-emerald-400' : cloudStatus === 'CONNECTING' ? 'bg-amber-400 animate-pulse' : 'bg-slate-500'"></span>
            <span class="hidden sm:inline">{{ cloudStatus === 'ONLINE' ? 'CLOUD RUN' : cloudStatus === 'CONNECTING' ? 'CONNECTING' : 'LOCAL MODE' }}</span>
            <span v-if="cloudWaveCount" class="hidden sm:inline opacity-70">/ {{ cloudWaveCount }} WAVES</span>
            <span v-if="stagePlanVersion === 2" class="opacity-60">v2</span>
          </div>

          <!-- 装備中パワーアップ -->
          <div class="flex-wrap gap-1 text-[10px] font-mono"
               :class="immersive ? 'hidden 2xl:flex' : 'flex order-last sm:order-none flex-1 sm:flex-none'">
            <span class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded border" :class="upgrades.doubleShotLv > 0 ? 'bg-pink-950/80 border-pink-500 text-pink-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">
              2-WAY Lv.{{ upgrades.doubleShotLv }}
            </span>
            <span class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded border" :class="upgrades.slashLv > 0 ? 'bg-amber-950/80 border-amber-500 text-amber-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">
              SLASH Lv.{{ upgrades.slashLv }}
            </span>
            <span class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded border" :class="upgrades.options > 0 ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">
              OPT×{{ upgrades.options }}
            </span>
            <span class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded border" :class="upgrades.barrierHp > 0 ? 'bg-blue-950/80 border-blue-400 text-blue-300 font-bold' : 'bg-slate-950 border-slate-800 text-slate-600'">
              SHIELD:{{ upgrades.barrierHp }}
            </span>
            <span class="px-1.5 sm:px-2 py-0.5 sm:py-1 rounded border bg-slate-950 border-slate-800 text-emerald-400">
              ATK×{{ upgrades.powerMultiplier.toFixed(2) }}
            </span>
          </div>

          <!-- スコア ＆ 進行度／ボスHP -->
          <div class="text-right flex-1 min-w-[120px]" :class="immersive ? 'max-w-[300px] ml-auto' : 'sm:flex-none sm:min-w-[195px]'">
            <div class="flex justify-end items-baseline gap-2 text-[11px] sm:text-xs font-mono mb-0.5 sm:mb-1">
              <span v-if="bestScore > 0" class="text-slate-500 hidden sm:inline">BEST {{ bestScore }}</span>
              <span class="text-amber-300 font-bold">SCORE: {{ score }}</span>
            </div>
            <div v-if="!boss.active">
              <div class="flex justify-between text-[9px] sm:text-[10px] font-mono text-slate-400 mb-0.5">
                <span>{{ fogGate.active ? 'FOG GATE READY' : 'PROGRESS' }}</span>
                <span class="text-cyan-400 font-bold">{{ Math.min(100, Math.floor(stageProgress)) }}%</span>
              </div>
              <div class="w-full h-1.5 sm:h-2 bg-slate-950 rounded-full overflow-hidden border border-slate-800">
                <div class="h-full bg-gradient-to-r from-cyan-500 to-pink-500 transition-all duration-150"
                     :style="{ width: `${Math.min(100, stageProgress)}%` }"></div>
              </div>
            </div>
            <div v-else>
              <div class="flex justify-between gap-2 text-[9px] sm:text-[10px] font-mono text-red-400 font-bold mb-0.5">
                <span class="truncate">{{ boss.name }}</span>
                <span class="shrink-0">{{ boss.hp }}/{{ boss.maxHp }}</span>
              </div>
              <div class="w-full h-2 sm:h-2.5 bg-slate-950 rounded-full overflow-hidden border border-red-900">
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

          <!-- タッチ端末・大画面モード用のコンパクトなシステムボタン -->
          <div class="flex items-center gap-1.5 shrink-0"
               :class="immersive ? '' : 'order-last sm:order-none'">
            <button v-if="isTouch" type="button" class="hud-btn hud-btn--wide" :class="autoFire ? 'is-on' : ''"
                    :aria-label="autoFire ? 'オート射撃：ON（タップで手動に切替）' : 'オート射撃：OFF（タップでオートに切替）'"
                    @click="toggleAutoFire">{{ autoFire ? 'AUTO' : 'MAN' }}</button>
            <button type="button" class="hud-btn" :class="sound.bgm ? 'is-on' : 'is-off'"
                    :aria-label="sound.bgm ? 'BGMをオフ' : 'BGMをオン'" :title="bgmTitle ? `♪ ${bgmTitle}` : 'BGM'"
                    @click="toggleBgm">♫</button>
            <button type="button" class="hud-btn" :class="sound.sfx ? 'is-on' : 'is-off'"
                    :aria-label="sound.sfx ? '効果音をオフ' : '効果音をオン'"
                    @click="toggleSfx">{{ sound.sfx ? '🔊' : '🔇' }}</button>
            <template v-if="immersive || isTouch">
              <button type="button" class="hud-btn" :aria-label="manualPaused ? '再開' : '一時停止'"
                      @click="toggleManualPause">{{ manualPaused ? '▶' : 'Ⅱ' }}</button>
              <button v-if="fullscreenSupported" type="button" class="hud-btn"
                      :aria-label="isFullscreen ? '全画面を終了' : '全画面で遊ぶ'"
                      @click="toggleFullscreen">{{ isFullscreen ? '🗗' : '⛶' }}</button>
            </template>
          </div>
        </div>

        <!-- ==================================================== -->
        <!-- ゲーム画面領域（Canvas ＋ 演出オーバーレイ） -->
        <!-- ==================================================== -->
        <div ref="stageRef" class="relative"
             :class="immersive ? 'flex-1 min-h-0 flex items-start justify-center overflow-hidden' : ''">
          <div ref="canvasBoxRef" class="canvas-box relative @container"
               :class="immersive ? '' : 'w-full aspect-video'"
               :style="immersive ? { width: `${fitSize.width}px`, height: `${fitSize.height}px` } : undefined">
            <div v-if="isLoadingStage" class="absolute inset-0 z-30 bg-slate-950/85 flex items-center justify-center"
                 role="status" aria-live="polite">
              <div class="text-center px-4">
                <div class="text-cyan-300 text-[10px] @md:text-xs font-mono tracking-[0.25em] animate-pulse">STAGE DATA SYNC</div>
                <div class="text-xl @md:text-2xl font-black text-white mt-1 @md:mt-2">STAGE {{ currentStage }}</div>
                <div class="text-[10px] @md:text-xs text-slate-400 mt-1 @md:mt-2">Cloud Run 接続確認中／ローカルモードでも続行できます</div>
              </div>
            </div>

            <div v-if="isPaused && !gameResult" class="absolute inset-0 z-40 flex items-center justify-center bg-slate-950/85"
                 role="status" aria-live="polite">
              <div class="text-center text-white px-4">
                <div class="text-2xl @md:text-3xl font-black tracking-widest">PAUSED</div>
                <div class="mt-1 @md:mt-2 text-[11px] @md:text-xs text-slate-300">
                  {{ windowInactive ? '画面に戻ると再開します' : isTouch ? '再開ボタンでゲームに戻ります' : 'Pキー／再開ボタンでゲームに戻ります' }}
                </div>
                <div v-if="sound.bgm && bgmTitle && !windowInactive" class="mt-2 text-[11px] text-cyan-300">
                  ♪ {{ bgmTitle }}
                  <button type="button" class="ml-2 underline text-slate-300" @click="nextBgm">次の曲 ▶▶</button>
                </div>
                <div v-if="!windowInactive" class="mt-3 @md:mt-4 flex flex-wrap justify-center gap-2">
                  <button type="button" @click="toggleManualPause"
                          class="px-4 py-2 bg-pink-600 hover:bg-pink-500 rounded-lg font-bold text-sm">▶ 再開する</button>
                  <button type="button" @click="resetFullGame" :disabled="isLoadingStage"
                          class="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-600 text-sm">STAGE 1 から</button>
                  <router-link to="/" class="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-600 text-sm">TOPへ</router-link>
                </div>
              </div>
            </div>

            <!-- ① ロックマン風：ステージ開始カウントダウン -->
            <transition name="fade">
              <div v-if="introState.active" class="absolute inset-0 flex flex-col items-center justify-center z-20 pointer-events-none bg-black/25 px-2">
                <div class="text-pink-400 font-mono text-[10px] @md:text-xs tracking-widest mb-1">
                  {{ loopCount > 1 ? `LOOP ${loopCount} // EXTREME BARRAGE MODE` : 'MISSION START' }}
                </div>
                <div class="text-2xl @md:text-3xl @2xl:text-4xl font-black text-white tracking-wider drop-shadow-lg text-center">STAGE {{ currentStage }} // READY!</div>
                <div class="text-[10px] @md:text-xs font-mono text-cyan-300 mt-1">{{ currentTheme.themeName }}</div>
              </div>
            </transition>

            <!-- ② 白い霧（ダークソウル風）案内メッセージ -->
            <div v-if="fogGate.active && !boss.active && !cutin.visible"
                 class="absolute top-2 @md:top-5 left-1/2 -translate-x-1/2 z-10 pointer-events-none px-3 @md:px-4 py-1 @md:py-1.5 rounded-full bg-slate-900/90 border border-slate-500 text-[10px] @md:text-xs font-bold shadow-lg whitespace-nowrap"
                 :class="enemies.length > 0 ? 'text-amber-300' : 'text-white animate-bounce'">
              {{ enemies.length > 0 ? `⚠️ 残りの敵をすべて倒してください（残り ${enemies.length} 体）` : '🌫️ 右端の「白い霧」に触れてボス部屋へ進む →' }}
            </div>

            <!-- ③ ボス登場時：ボスへのズームイン紹介バナー -->
            <transition name="fade">
              <div v-if="cutin.visible" class="absolute inset-x-0 bottom-2 @md:bottom-6 flex justify-center z-20 pointer-events-none">
                <div class="px-4 py-2 @md:px-8 @md:py-4 rounded-xl border-2 border-pink-500 bg-slate-950/90 shadow-2xl text-center max-w-xl w-full mx-2 @md:mx-4">
                  <div class="text-pink-400 text-[9px] @md:text-xs font-mono tracking-widest mb-0.5">
                    WARNING // {{ loopCount > 1 ? `LOOP ${loopCount} EX BOSS` : 'BOSS ENCOUNTER' }}
                  </div>
                  <div class="text-base @md:text-xl @2xl:text-2xl font-black text-yellow-300 tracking-wide mb-0.5 @md:mb-1">BOSS: {{ cutin.bossName }}</div>
                  <div class="text-[11px] @md:text-sm font-bold text-white">「{{ cutin.quote }}」</div>
                  <div class="text-[9px] @md:text-[11px] text-slate-400 mt-0.5">— {{ cutin.source }}</div>
                </div>
              </div>
            </transition>

            <!-- ④ ダークソウル風：「YOU DIED」ブラックアウト演出 -->
            <transition name="fade">
              <div v-if="deathOverlay.active" class="absolute inset-0 bg-black/85 flex flex-col items-center justify-center z-30 pointer-events-none">
                <div class="w-full py-4 @md:py-6 bg-gradient-to-r from-transparent via-black to-transparent border-y border-red-900/60 text-center">
                  <div class="text-4xl @md:text-5xl @2xl:text-6xl font-serif tracking-[0.25em] text-red-600 drop-shadow-[0_0_20px_rgba(220,38,38,0.8)]">
                    YOU DIED
                  </div>
                  <div class="text-[10px] @md:text-xs font-mono text-slate-300 mt-2 @md:mt-3 tracking-widest">
                    {{ deathOverlay.message }}
                  </div>
                </div>
              </div>
            </transition>

            <!-- メインゲームCanvas（論理解像度800×450・端末のピクセル密度に合わせて高精細描画） -->
            <canvas ref="canvasRef" width="800" height="450" class="block w-full h-full"
                    aria-label="ERIKA ROCK ACTION ゲーム画面"></canvas>
          </div>

          <!-- 大画面モード：画面の左右下にバーチャルパッドを重ねる -->
          <div v-if="isTouch && immersive" class="touch-overlay absolute inset-x-0 bottom-0 flex items-end justify-between pointer-events-none safe-x safe-b">
            <div class="pointer-events-auto p-2">
              <div class="move-pad move-pad--overlay" role="group" aria-label="左右移動パッド"
                   @pointerdown.prevent="onPadDown" @pointermove.prevent="onPadMove"
                   @pointerup.prevent="onPadUp" @pointercancel="onPadUp" @lostpointercapture="onPadUp">
                <span class="move-pad__arrow" :class="padDir === -1 ? 'is-on' : ''">◀</span>
                <span class="move-pad__arrow" :class="padDir === 1 ? 'is-on' : ''">▶</span>
              </div>
            </div>
            <div class="pointer-events-auto p-2 action-cluster action-cluster--overlay" :class="autoFire ? 'is-solo' : ''">
              <button v-for="control in visibleTouchActions" :key="control.code" type="button"
                      :aria-label="control.label" class="action-btn" :class="actionButtonClass(control.code)"
                      @pointerdown.prevent="pressTouch(control.code, $event)"
                      @pointerup.prevent="releaseTouch(control.code)"
                      @pointercancel="releaseTouch(control.code)"
                      @lostpointercapture="releaseTouch(control.code)">
                <span class="action-btn__icon">{{ control.symbol }}</span>
                <span class="action-btn__label">{{ control.short }}</span>
              </button>
            </div>
          </div>

          <!-- ⑤ クリアボーナス選択画面（小さい画面では画面全体に表示） -->
          <transition name="fade">
            <div v-if="gameResult === 'CLEAR'"
                 class="result-overlay bg-slate-950/90 flex flex-col items-center z-[70] p-3 sm:p-4 overflow-y-auto"
                 :class="compactOverlay ? 'fixed inset-0 justify-start sm:justify-center safe-x safe-b' : 'absolute inset-0 justify-center'">
              <div class="flex items-center gap-3 sm:gap-5 mb-2 sm:mb-3 bg-slate-900/95 px-4 sm:px-6 py-2 sm:py-3 rounded-2xl border border-yellow-400/60 shadow-2xl">
                <img :src="playerArt.victory" alt="Victory Erika" @error="onArtError($event, '/sprites/victory.png')"
                     class="w-12 h-12 sm:w-20 sm:h-20 object-contain drop-shadow-[0_0_12px_rgba(244,114,182,0.8)]" />
                <div>
                  <div class="text-yellow-400 text-[10px] sm:text-xs font-mono tracking-widest">STAGE {{ currentStage }} COMPLETE!!</div>
                  <div class="text-xl md:text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-yellow-300 via-pink-400 to-cyan-300">
                    CONGRATULATIONS!!
                  </div>
                  <div class="text-xs sm:text-sm font-mono text-slate-200 mt-0.5">TOTAL SCORE: <span class="text-yellow-300 font-bold">{{ score }}</span></div>
                </div>
              </div>

              <div class="text-[11px] sm:text-xs font-bold text-pink-300 mb-2 text-center">▼ クリアボーナス：強化する武装を1つ選んで次のステージへ ▼</div>
              <div class="grid gap-2 sm:gap-2.5 w-full max-w-2xl"
                   :class="compactOverlay && isLandscape ? 'grid-cols-3' : 'grid-cols-2 md:grid-cols-3'">
                <button v-for="item in bonusChoices" :key="item.id" type="button"
                        @click="selectBonusAndNextStage(item.id)"
                        class="flex flex-col items-start p-2 sm:p-2.5 rounded-lg border border-slate-700 bg-slate-900/95 hover:bg-pink-950/80 hover:border-pink-400 active:bg-pink-950 transition text-left group">
                  <div class="text-[11px] sm:text-xs font-bold text-pink-400 group-hover:text-yellow-300">{{ item.title }}</div>
                  <div class="text-[10px] sm:text-[11px] text-slate-300 mt-0.5 leading-snug">{{ item.desc }}</div>
                </button>
              </div>
            </div>
          </transition>

          <!-- ⑥ ゲームオーバー画面 -->
          <div v-if="gameResult === 'GAMEOVER'"
               class="result-overlay bg-black/90 flex flex-col items-center z-[70] p-4 overflow-y-auto text-center"
               :class="(compactOverlay || isTouch) ? 'fixed inset-0 safe-x safe-b' : 'absolute inset-0'">
            <div class="my-auto w-full flex flex-col items-center">
            <img :src="playerArt.down" alt="Down Erika" @error="onArtError($event, '/sprites/down.png')"
                 class="w-16 h-16 sm:w-24 sm:h-24 object-contain mb-1 opacity-90" />
            <div class="text-4xl sm:text-5xl font-serif tracking-[0.2em] text-red-600 mb-1 sm:mb-2">YOU DIED</div>
            <div class="text-slate-400 font-mono text-xs sm:text-sm">FINAL SCORE: {{ score }} (REACHED STAGE {{ currentStage }})</div>
            <div class="font-mono text-xs mt-1 mb-4 sm:mb-6" :class="isNewRecord ? 'text-yellow-300 font-bold animate-pulse' : 'text-slate-500'">
              {{ isNewRecord ? '★ NEW RECORD! ★' : `BEST: ${bestScore} (STAGE ${bestStage})` }}
            </div>
            <!-- 全国ランキングへ登録 -->
            <form class="w-full max-w-md mb-4 flex flex-col items-center gap-2" @submit.prevent="submitScore">
              <div v-if="!scoreSubmitted" class="flex w-full gap-2">
                <input v-model="playerName" type="text" maxlength="20" placeholder="名前（20文字まで）"
                       class="flex-1 min-w-0 px-3 py-2 rounded-lg bg-slate-900 border border-slate-600 text-white text-sm select-text"
                       aria-label="ランキングに載せる名前" />
                <button type="submit" :disabled="isSubmittingScore || score <= 0"
                        class="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-bold text-sm whitespace-nowrap">
                  {{ isSubmittingScore ? '送信中…' : '全国ランキングに登録' }}
                </button>
              </div>
              <p v-if="scoreSubmitMessage" class="text-xs" :class="scoreSubmitted ? 'text-emerald-300' : 'text-amber-300'">{{ scoreSubmitMessage }}</p>
            </form>
            <div class="w-full max-w-md mb-4 text-left">
              <div class="text-[11px] font-mono tracking-widest text-pink-300 mb-1 text-center">TOP ROCKERS</div>
              <p v-if="rankingError" class="text-xs text-amber-300 text-center">{{ rankingError }}</p>
              <p v-else-if="rankings.length === 0" class="text-xs text-slate-500 text-center">ランキングはまだありません</p>
              <ol v-else class="space-y-1 max-h-40 overflow-y-auto pr-1">
                <li v-for="(r, i) in rankings" :key="`${i}-${r.name}-${r.score}`"
                    class="flex items-center gap-2 text-xs bg-slate-900/80 border border-slate-800 rounded px-2 py-1">
                  <span class="w-5 font-black" :class="i === 0 ? 'text-yellow-300' : i < 3 ? 'text-pink-300' : 'text-slate-500'">{{ i + 1 }}</span>
                  <span class="flex-1 truncate text-slate-200">{{ r.name }}</span>
                  <span class="text-slate-500 font-mono">ST.{{ r.stage }}</span>
                  <span class="text-amber-300 font-mono font-bold">{{ r.score }}</span>
                </li>
              </ol>
            </div>
            <div class="flex flex-col sm:flex-row gap-2 sm:gap-4">
              <button v-if="checkpointReachedBossGate" type="button" @click="retryFromCheckpoint"
                      class="px-5 py-2.5 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded-lg shadow-lg transition text-sm sm:text-base">
                ボス直前（白い霧）からコンティニュー
              </button>
              <button type="button" @click="resetFullGame"
                      class="px-5 py-2.5 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded-lg shadow-lg transition text-sm sm:text-base">
                STAGE 1 から再挑戦する
              </button>
            </div>
            </div>
          </div>
        </div>

        <!-- ==================================================== -->
        <!-- スマホ・タブレット縦向き：画面下のゲームパッド -->
        <!-- 指をスライドしても左右が切り替わる移動パッド＋マルチタッチ対応ボタン -->
        <!-- ==================================================== -->
        <div v-if="isTouch && !immersive" class="touch-panel bg-slate-900/95 border-t border-slate-700 px-3 pt-3 pb-2 safe-b">
          <div class="flex items-end justify-between gap-3">
            <div class="move-pad" role="group" aria-label="左右移動パッド"
                 @pointerdown.prevent="onPadDown" @pointermove.prevent="onPadMove"
                 @pointerup.prevent="onPadUp" @pointercancel="onPadUp" @lostpointercapture="onPadUp">
              <span class="move-pad__arrow" :class="padDir === -1 ? 'is-on' : ''">◀</span>
              <span class="move-pad__arrow" :class="padDir === 1 ? 'is-on' : ''">▶</span>
            </div>
            <div class="action-cluster" :class="autoFire ? 'is-solo' : ''">
              <button v-for="control in visibleTouchActions" :key="control.code" type="button"
                      :aria-label="control.label" class="action-btn" :class="actionButtonClass(control.code)"
                      @pointerdown.prevent="pressTouch(control.code, $event)"
                      @pointerup.prevent="releaseTouch(control.code)"
                      @pointercancel="releaseTouch(control.code)"
                      @lostpointercapture="releaseTouch(control.code)">
                <span class="action-btn__icon">{{ control.symbol }}</span>
                <span class="action-btn__label">{{ control.short }}</span>
              </button>
            </div>
          </div>
          <div class="text-[10px] text-slate-400 text-center mt-2">
            <template v-if="autoFire">ショットは自動（チャージも自動で発射）／ パッドを同じ向きに2回タップでダッシュ</template>
            <template v-else>パッドはスライドで左右切替 ／ SHOT長押し→離してチャージ攻撃</template>
          </div>
        </div>

        <!-- 下部操作ガイド（大画面モードでは非表示：HUD右端のボタンで操作） -->
        <!-- ==================================================== -->
        <div v-if="!immersive" class="bg-slate-900 px-3 sm:px-4 py-2.5 flex flex-wrap justify-between items-center gap-2 text-xs text-slate-300 border-t border-slate-800">
          <div v-if="!isTouch" class="flex flex-wrap gap-x-3 gap-y-1">
            <span><kbd class="kbd">←</kbd> <kbd class="kbd">→</kbd> 移動</span>
            <span><kbd class="kbd">↑</kbd> / <kbd class="kbd">Z</kbd> / <kbd class="kbd">Space</kbd> ジャンプ</span>
            <span><kbd class="kbd">↓</kbd> / <kbd class="kbd">C</kbd> ダッシュ</span>
            <span><kbd class="kbd">X</kbd> 音符ショット＆薙ぎ払い（Lv2以上チャージで敵弾消去！）</span>
            <span v-if="bestScore > 0" class="text-slate-500 font-mono">BEST {{ bestScore }} / STAGE {{ bestStage }}</span>
          </div>
          <div class="flex flex-wrap gap-2" :class="isTouch ? 'w-full justify-center' : ''">
            <button v-if="!isTouch" type="button" @click="toggleManualPause"
                    class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-600">
              {{ manualPaused ? '▶ 再開' : 'Ⅱ 一時停止 (P)' }}
            </button>
            <button v-if="!isTouch && fullscreenSupported" type="button" @click="toggleFullscreen"
                    class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-600">
              ⛶ 全画面
            </button>
            <router-link to="/" class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-700 transition">
              TOPへ戻る
            </router-link>
            <button type="button" @click="resetFullGame" :disabled="isLoadingStage"
                    class="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-600 transition">
              STAGE 1 リスタート
            </button>
          </div>
        </div>
      </div>

      <!-- 全国ランキング（通常表示のときだけページ下に表示） -->
      <section v-if="!immersive" class="mt-6 bg-slate-900/80 border border-slate-800 rounded-xl p-4">
        <div class="flex items-center justify-between mb-2">
          <h2 class="text-sm font-black tracking-widest text-pink-300">TOP ROCKERS <span class="text-[10px] text-slate-500 font-mono">全国ランキング</span></h2>
          <button type="button" class="text-[11px] text-slate-400 hover:text-white" @click="fetchRankings">↻ 更新</button>
        </div>
        <p v-if="rankingError" class="text-xs text-amber-300">{{ rankingError }}</p>
        <p v-else-if="rankings.length === 0" class="text-xs text-slate-500">ランキングはまだありません。ゲームオーバー時に登録できます。</p>
        <ol v-else class="grid sm:grid-cols-2 gap-x-4 gap-y-1">
          <li v-for="(r, i) in rankings" :key="`p-${i}-${r.name}-${r.score}`" class="flex items-center gap-2 text-xs border-b border-slate-800 py-1">
            <span class="w-5 font-black" :class="i === 0 ? 'text-yellow-300' : i < 3 ? 'text-pink-300' : 'text-slate-500'">{{ i + 1 }}</span>
            <span class="flex-1 truncate text-slate-200">{{ r.name }}</span>
            <span class="text-slate-500 font-mono">STAGE {{ r.stage }}</span>
            <span class="text-amber-300 font-mono font-bold w-20 text-right">{{ r.score }}</span>
          </li>
        </ol>
      </section>
    </div>
    <!-- BGM（YouTube）用の見えないプレイヤー -->
    <div class="fixed -top-[9999px] -left-[9999px] w-px h-px overflow-hidden" aria-hidden="true">
      <div id="rock-bgm-player"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onUnmounted } from 'vue'
import { measureSprite, drawFittedSprite } from '../game/spriteRenderer'
import { useGameViewport, VIEW_W, VIEW_H } from '../game/useGameViewport'
import { drawBulletGlyph, getTintedSprite } from '../game/renderCache'
import { drawGround, drawPit, drawWallObstacle, drawPlatform, getBuilding } from '../game/stageArt'
import { playSfx, unlockAudio, setSfxEnabled, setSfxVolume, suspendAudio, resumeAudio, type SfxName } from '../game/sfx'
import { createYoutubeBgm } from '../game/youtubeBgm'
import { drawCrescentSlash } from '../game/slashFx'

// ====================================================
// 画面レイアウト（スマホ・タブレット対応）
// ====================================================
const shellRef = ref<HTMLElement | null>(null)
const stageRef = ref<HTMLElement | null>(null)
const canvasBoxRef = ref<HTMLElement | null>(null)
const canvasRef = ref<HTMLCanvasElement | null>(null)
const {
  isTouch, isLandscape, immersive, isFullscreen, fullscreenSupported,
  toggleFullscreen, fitSize, compactOverlay, renderScale,
} = useGameViewport({ shellRef, stageRef, canvasBoxRef, canvasRef })

// 軽量WebP（tools/optimize_sprites.py で生成）を優先し、無ければ元のPNGを読む
const toOptimizedUrl = (url: string) => /^\/sprites\/.+\.png$/i.test(url) ? url.replace(/\.png$/i, '.webp') : url
const playerArt = { victory: toOptimizedUrl('/sprites/victory.png'), down: toOptimizedUrl('/sprites/down.png') }
const onArtError = (event: Event, fallback: string) => {
  const img = event.target as HTMLImageElement
  if (!img.src.endsWith(fallback)) img.src = fallback
}

// 振動フィードバック（Android等の対応端末のみ。iPhoneでは何もしない）
const vibrate = (pattern: number | number[]) => {
  if (!isTouch.value || typeof navigator.vibrate !== 'function') return
  try { navigator.vibrate(pattern) } catch { /* 非対応 */ }
}

// ====================================================
// サウンド設定（効果音・BGM）。端末に保存。
// ====================================================
const SOUND_KEY = 'erika-rock-action:sound'
const loadSound = () => {
  try {
    const raw = JSON.parse(localStorage.getItem(SOUND_KEY) || 'null')
    if (raw && typeof raw === 'object') return { sfx: raw.sfx !== false, bgm: raw.bgm !== false }
  } catch { /* 破損データは無視 */ }
  return { sfx: true, bgm: true }
}
const sound = reactive(loadSound())
const saveSound = () => { try { localStorage.setItem(SOUND_KEY, JSON.stringify(sound)) } catch { /* 保存不可 */ } }
setSfxEnabled(sound.sfx)
setSfxVolume(0.45)
const bgmTitle = ref('')
const bgm = createYoutubeBgm('rock-bgm-player', (title) => { bgmTitle.value = title })
let audioUnlocked = false
// スマホは「最初のタップ／キー入力」でしか音を出せないため、そこで解錠して BGM を開始
const onFirstGesture = () => {
  if (audioUnlocked) return
  audioUnlocked = true
  unlockAudio()
  if (sound.bgm && !isPaused.value) bgm.play()
}
const toggleSfx = () => {
  sound.sfx = !sound.sfx
  setSfxEnabled(sound.sfx)
  saveSound()
  unlockAudio()
  playSfx('select')
}
const toggleBgm = () => {
  sound.bgm = !sound.bgm
  saveSound()
  audioUnlocked = true
  if (sound.bgm) bgm.play()
  else bgm.stop()
}
const nextBgm = () => { if (sound.bgm) bgm.next() }

// ====================================================
// 全国ランキング（ラビリンスと同じ仕組み：/api/rock-ranking）
// ====================================================
interface RockRanking { name: string; score: number; stage: number }
const NAME_KEY = 'erika-rock-action:name'
const rankings = ref<RockRanking[]>([])
const rankingError = ref('')
const playerName = ref((() => { try { return localStorage.getItem(NAME_KEY) || '' } catch { return '' } })())
const isSubmittingScore = ref(false)
const scoreSubmitted = ref(false)
const scoreSubmitMessage = ref('')
const fetchRankings = async () => {
  rankingError.value = ''
  try {
    const res = await fetch('/api/rock-ranking', { signal: lifecycleAbort.signal })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    const data = await res.json()
    if (!Array.isArray(data)) throw new Error('bad ranking payload')
    rankings.value = data.slice(0, 10)
  } catch (error) {
    if (lifecycleAbort.signal.aborted) return
    rankingError.value = 'ランキングを取得できませんでした。'
    console.warn('[ERIKA] ranking unavailable', error)
  }
}
const submitScore = async () => {
  if (isSubmittingScore.value || scoreSubmitted.value || gameResult.value !== 'GAMEOVER') return
  isSubmittingScore.value = true
  scoreSubmitMessage.value = ''
  const name = playerName.value.trim().slice(0, 20)
  try { localStorage.setItem(NAME_KEY, name) } catch { /* 保存不可 */ }
  try {
    const res = await fetch('/api/rock-ranking', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, score: score.value, stage: currentStage.value }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data?.error || `HTTP ${res.status}`)
    scoreSubmitted.value = true
    scoreSubmitMessage.value = Number.isFinite(data?.rank) ? `全国 ${data.rank} 位で登録しました！` : '登録しました！'
    playSfx('oneUp')
    await fetchRankings()
  } catch (error) {
    scoreSubmitMessage.value = error instanceof Error && error.message && !error.message.startsWith('HTTP')
      ? error.message : '登録できませんでした。通信状態を確認して再試行してください。'
  } finally {
    isSubmittingScore.value = false
  }
}

// ベストスコア（端末内に保存）
const BEST_KEY = 'erika-rock-action:best'
const loadBest = (): { score: number; stage: number } => {
  try {
    const raw = JSON.parse(localStorage.getItem(BEST_KEY) || 'null')
    if (raw && Number.isFinite(raw.score) && Number.isFinite(raw.stage)) return { score: raw.score, stage: raw.stage }
  } catch { /* 破損データは無視 */ }
  return { score: 0, stage: 0 }
}
const initialBest = loadBest()
const bestScore = ref(initialBest.score)
const bestStage = ref(initialBest.stage)
const isNewRecord = ref(false)
const commitBestScore = () => {
  if (score.value <= bestScore.value) return
  bestScore.value = score.value
  bestStage.value = currentStage.value
  isNewRecord.value = true
  try { localStorage.setItem(BEST_KEY, JSON.stringify({ score: bestScore.value, stage: bestStage.value })) } catch { /* 保存不可 */ }
}

// The API is optional. A missing URL is explicit OFFLINE mode, not a dummy request.
const API_BASE = (import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '')
const cloudStatus = ref<'CONNECTING' | 'ONLINE' | 'OFFLINE'>('CONNECTING')
const cloudWaveCount = ref(0)
const stagePlanVersion = ref<number | null>(null)


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

const maxHp = ref(100)
const playerHp = ref(100)
const lives = ref(3)
const score = ref(0)
const chargeLevel = ref(0)
const chargeBadgeClass = computed(() =>
  chargeLevel.value === 3 ? 'bg-gradient-to-r from-pink-500 via-yellow-400 to-cyan-400 text-slate-950 border-white animate-pulse' :
  chargeLevel.value === 2 ? 'bg-yellow-400 text-slate-950 border-yellow-200' :
  chargeLevel.value === 1 ? 'bg-cyan-400 text-slate-950 border-cyan-200' : 'bg-slate-950 text-slate-400 border-slate-800')
const isLoadingStage = ref(false)
// 手動一時停止・ウィンドウ非アクティブを分離。フォーカス復帰でも手動停止は解除しない。
const manualPaused = ref(false)
const windowInactive = ref(false)
const isPaused = computed(() => manualPaused.value || windowInactive.value)

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
    desc: upgrades.options < 2 ? 'エリカの後ろを追従するスピーカーを追加！チャージ弾も一緒に撃つ（威力60%）' : '最大数達成（選ぶと攻撃力+5%）'
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

// User-edited master JSON can be partial: merge by stable IDs rather than
// silently rejecting the file if it has fewer than 12 bosses.
const mergeCatalog = (defaults: any[], overrides: any[], idKey: string) => {
  const byId = new Map(defaults.map(item => [item[idKey], { ...item }]))
  for (const item of overrides) {
    if (item && item[idKey] !== undefined && byId.has(item[idKey])) {
      byId.set(item[idKey], { ...byId.get(item[idKey]), ...item })
    }
  }
  return Array.from(byId.values())
}

const loadMasterJsonAsync = async (signal: AbortSignal) => {
  try {
    const res = await fetch('/assets/game-master.json', { cache: 'no-cache', signal })
    if (!res.ok) return
    const json = await res.json()
    if (signal.aborted || !json || typeof json !== 'object') return
    masterData = {
      ...masterData,
      quotes: Array.isArray(json.quotes) && json.quotes.length ? json.quotes : masterData.quotes,
      enemies: Array.isArray(json.enemies) ? mergeCatalog(masterData.enemies, json.enemies, 'type') : masterData.enemies,
      bosses: Array.isArray(json.bosses) ? mergeCatalog(masterData.bosses, json.bosses, 'id') : masterData.bosses,
      stages: Array.isArray(json.stages) ? mergeCatalog(masterData.stages, json.stages, 'stage') : masterData.stages,
    }
  } catch (error) {
    if (!signal.aborted) console.warn('[ERIKA] Could not load master data; using built-in defaults.', error)
  }
}

interface StageWave {
  id: string
  type: string
  spawn_delay_ms: number
  hp: number
  speed: number
}
interface BossStageData {
  id: string
  name: string
  hp: number
  pattern: string
  scale: number
  isGiantFinalBoss?: boolean
  cutin_quote: { quote: string; source: string }
}
interface StagePlan {
  stage: number
  enemy_waves: StageWave[]
  boss: BossStageData
  plan_version: number
}

let activeStagePlan: StagePlan | null = null

const buildOfflineStagePlan = (stageNum: number): StagePlan => {
  const { enemyHpMul, spdMul, bossHpMul } = getDifficultyMultipliers(stageNum)
  const count = 14 + Math.min(8, Math.floor((stageNum - 1) / 3) + Math.floor((stageNum - 1) / 12))
  const waves: StageWave[] = []
  let spawnAt = 900
  for (let i = 0; i < count; i++) {
    const template = masterData.enemies[(i * 3 + stageNum + Math.floor(i / 4)) % masterData.enemies.length]
    spawnAt += 1450 + (i * 113 + stageNum * 73) % 420
    waves.push({
      id: `offline-${stageNum}-${i}`, type: template.type,
      spawn_delay_ms: spawnAt,
      hp: Math.max(1, Math.round(template.hp * enemyHpMul)),
      speed: template.speed * spdMul
    })
  }
  const bossTemplate = masterData.bosses[(stageNum - 1) % masterData.bosses.length]
  return {
    stage: stageNum, plan_version: 0, enemy_waves: waves,
    boss: {
      ...bossTemplate,
      hp: Math.max(1, Math.round(bossTemplate.baseHp * bossHpMul)),
      cutin_quote: masterData.quotes[(stageNum - 1) % masterData.quotes.length],
    }
  }
}

const requestStagePlan = async (stageNum: number, stageSignal: AbortSignal): Promise<StagePlan> => {
  const offline = buildOfflineStagePlan(stageNum)
  if (!API_BASE) {
    cloudStatus.value = 'OFFLINE'
    return offline
  }

  cloudStatus.value = 'CONNECTING'
  const controller = new AbortController()
  const abortRequest = () => controller.abort()
  stageSignal.addEventListener('abort', abortRequest, { once: true })
  const timeout = window.setTimeout(() => controller.abort(), 5500)
  try {
    const response = await fetch(`${API_BASE}/api/stage-start?stage=${stageNum}`, {
      signal: controller.signal,
      headers: { Accept: 'application/json' },
    })
    if (!response.ok) throw new Error(`HTTP ${response.status}`)
    const data: unknown = await response.json()
    if (!data || typeof data !== 'object') throw new Error('Bad stage payload')
    const raw = data as Record<string, any>
    if (raw.stage !== stageNum || raw.plan_version !== 2 ||
        !Array.isArray(raw.enemy_waves) || raw.enemy_waves.length < 1 || raw.enemy_waves.length > 50 ||
        !raw.boss || raw.boss.id !== offline.boss.id ||
        !Number.isFinite(raw.boss.hp) || raw.boss.hp < 1 ||
        typeof raw.boss.cutin_quote?.quote !== 'string' || typeof raw.boss.cutin_quote?.source !== 'string') {
      throw new Error('Stage payload validation failed')
    }
    let previousDelay = 0
    const waves: StageWave[] = raw.enemy_waves.map((w: any, index: number) => {
      const source = masterData.enemies.find((e: any) => e.type === w.type)
      if (!source || !Number.isFinite(w.spawn_delay_ms) || !Number.isFinite(w.hp) ||
          !Number.isFinite(w.speed) || w.spawn_delay_ms < previousDelay ||
          w.spawn_delay_ms > 120000 || w.hp < 1 || w.speed < 0) {
        throw new Error(`Invalid wave ${index}`)
      }
      previousDelay = w.spawn_delay_ms
      return {
        id: `stage${stageNum}-wave${index}`, type: source.type,
        spawn_delay_ms: Math.round(w.spawn_delay_ms),
        hp: Math.round(w.hp), speed: Math.min(12, w.speed)
      }
    })
    if (stageSignal.aborted) throw new DOMException('Aborted', 'AbortError')
    cloudStatus.value = 'ONLINE'
    return {
      stage: stageNum, plan_version: 2, enemy_waves: waves,
      boss: {
        ...offline.boss, hp: Math.round(raw.boss.hp),
        cutin_quote: {
          quote: raw.boss.cutin_quote.quote.slice(0, 160),
          source: raw.boss.cutin_quote.source.slice(0, 100),
        },
      },
    }
  } catch (error) {
    if (stageSignal.aborted) throw error
    console.warn('[ERIKA] Cloud Run unavailable; switching to local stage plan.', error)
    cloudStatus.value = 'OFFLINE'
    return offline
  } finally {
    window.clearTimeout(timeout)
    stageSignal.removeEventListener('abort', abortRequest)
  }
}

const sprites: Record<string, HTMLImageElement> = {}
const spriteUrls: Record<string, string> = {}
const pendingSpriteLoads = new Map<string, Promise<void>>()
const lifecycleAbort = new AbortController()
let componentDisposed = false

// 起動時はプレイヤー/雑魚敵のみ先読み。ボス画像は各ステージ開始時に3状態まとめて先読みする。
const buildSpriteCatalog = () => {
  Object.assign(spriteUrls, {
    idle: '/sprites/idle.png', run1: '/sprites/run1.png', run2: '/sprites/run2.png',
    shoot: '/sprites/shoot.png', jump: '/sprites/jump.png', jumpShoot: '/sprites/jump_shoot.png',
    hurt: '/sprites/hurt.png', victory: '/sprites/victory.png', down: '/sprites/down.png',
  })
  masterData.enemies.forEach((e: any) => { spriteUrls[e.type] = e.sprite })
  masterData.bosses.forEach((b: any) => {
    spriteUrls[`boss_${b.id}`] = b.sprite
    spriteUrls[`boss_${b.id}_hurt`] = `/sprites/bosses/boss_${b.id}_hurt.png`
    spriteUrls[`boss_${b.id}_down`] = `/sprites/bosses/boss_${b.id}_down.png`
    if (b.spriteCracked) spriteUrls[`boss_${b.id}_cracked`] = b.spriteCracked
    if (b.spriteUnarmed) spriteUrls[`boss_${b.id}_unarmed`] = b.spriteUnarmed
  })
}

const preloadSprite = (key: string, signal: AbortSignal): Promise<void> => {
  if (sprites[key] || !spriteUrls[key] || signal.aborted || componentDisposed) return Promise.resolve()
  const existing = pendingSpriteLoads.get(key)
  if (existing) return existing.then(() => {
    if (!sprites[key] && !signal.aborted && !componentDisposed) return preloadSprite(key, signal)
  })

  const promise = new Promise<void>((resolve) => {
    const image = new Image()
    let finished = false
    let loadTimeout = 0
    const finish = (success: boolean) => {
      if (finished) return
      finished = true
      window.clearTimeout(loadTimeout)
      signal.removeEventListener('abort', onAbort)
      lifecycleAbort.signal.removeEventListener('abort', onAbort)
      image.onload = null
      image.onerror = null
      if (success && !componentDisposed && !signal.aborted && !lifecycleAbort.signal.aborted) {
        measureSprite(image)
        sprites[key] = image
      }
      resolve()
    }
    const onAbort = () => {
      // onloadが後から届いても新しいステージの素材を汚染しない。
      image.src = ''
      finish(false)
    }
    image.onload = () => finish(true)
    signal.addEventListener('abort', onAbort, { once: true })
    lifecycleAbort.signal.addEventListener('abort', onAbort, { once: true })
    if (signal.aborted || lifecycleAbort.signal.aborted) { onAbort(); return }
    // WebP → 元PNG の順に試す（WebP未生成の新規画像でもそのまま動く）
    const original = spriteUrls[key]
    const optimized = toOptimizedUrl(original)
    image.onerror = optimized !== original
      ? () => { image.onerror = () => finish(false); image.src = original }
      : () => finish(false)
    image.decoding = 'async'
    image.src = optimized
    loadTimeout = window.setTimeout(() => {
      image.src = ''
      finish(false)
    }, 10000)
  })
  pendingSpriteLoads.set(key, promise)
  void promise.finally(() => { if (pendingSpriteLoads.get(key) === promise) pendingSpriteLoads.delete(key) })
  return promise
}

const preloadSpriteKeys = (keys: string[], signal: AbortSignal) =>
  Promise.all(keys.map(key => preloadSprite(key, signal))).then(() => undefined)

const preloadBossSprites = async (bossId: string, signal: AbortSignal) => {
  const keys = [`boss_${bossId}`, `boss_${bossId}_hurt`, `boss_${bossId}_down`]
  if (bossId === 'sunflower') keys.push('boss_sunflower_cracked', 'boss_sunflower_unarmed')
  await preloadSpriteKeys(keys, signal)
  // The unarmed pose is optional. All bosses are expected to have HURT/DOWN.
  if (!signal.aborted && !componentDisposed) {
    for (const key of [`boss_${bossId}`, `boss_${bossId}_hurt`, `boss_${bossId}_down`]) {
      if (!sprites[key]) console.warn(`[ERIKA] Missing sprite: ${spriteUrls[key] ?? key}`)
    }
  }
}

// 非同期の敵出現・攻撃・演出を「ゲーム時間」で進める。
// setTimeoutではタブ非アクティブ中も時間が進み、復帰後に進行が飛んでいた。
interface GameWait {
  remainingMs: number
  resolve: () => void
  reject: (reason: Error) => void
  signal?: AbortSignal
  onAbort: () => void
}
const gameWaits = new Set<GameWait>()
const settleGameWait = (timer: GameWait, abort: boolean) => {
  if (!gameWaits.delete(timer)) return
  timer.signal?.removeEventListener('abort', timer.onAbort)
  lifecycleAbort.signal.removeEventListener('abort', timer.onAbort)
  if (abort) timer.reject(new DOMException('Aborted', 'AbortError'))
  else timer.resolve()
}
const advanceGameWaits = (ms: number) => {
  for (const timer of Array.from(gameWaits)) {
    timer.remainingMs -= ms
    if (timer.remainingMs <= 0) settleGameWait(timer, false)
  }
}
const waitAsync = (ms: number, signal?: AbortSignal) => new Promise<void>((resolve, reject) => {
  if (componentDisposed || lifecycleAbort.signal.aborted || signal?.aborted) {
    reject(new DOMException('Aborted', 'AbortError'))
    return
  }
  const timer: GameWait = {
    remainingMs: Math.max(0, ms), resolve, reject,
    signal, onAbort: () => settleGameWait(timer, true)
  }
  gameWaits.add(timer)
  signal?.addEventListener('abort', timer.onAbort, { once: true })
  lifecycleAbort.signal.addEventListener('abort', timer.onAbort, { once: true })
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
  hitTargets?: Set<string> // Charged shots can hit each target only once.
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
  isHidden?: boolean; isCharging?: boolean; isStunned?: boolean; stunTimer?: number
  hueRotate: number; baseY: number; abortController: AbortController
}

const bullets: Bullet[] = []
const activeSlashes: SlashWave[] = []
const dropItems: DropItem[] = []
const floatingTexts: FloatingText[] = []
const fireworks: FireworkParticle[] = []
const enemies: Enemy[] = []
const afterimages: { x: number; y: number; facing: number; alpha: number; spriteKey: string }[] = []
interface ImpactParticle {
  x: number; y: number; vx: number; vy: number
  life: number; maxLife: number; color: string; size: number
}
const impactParticles: ImpactParticle[] = []
// Bounded, game-time-driven particles: they never trigger extra network calls or timers.
const spawnImpact = (x: number, y: number, color: string, count = 9, power = 2.7) => {
  for (let i = 0; i < count; i++) {
    const a = (i / count) * Math.PI * 2 + Math.random() * 0.25
    const speed = power * (0.45 + Math.random() * 0.65)
    impactParticles.push({
      x, y, vx: Math.cos(a) * speed, vy: Math.sin(a) * speed,
      life: 14 + Math.floor(Math.random() * 14), maxLife: 28,
      color, size: 1.3 + Math.random() * 2.3,
    })
  }
  if (impactParticles.length > 180) impactParticles.splice(0, impactParticles.length - 180)
}
let stageAbortController: AbortController | null = null
let screenShakeTimer = 0

// ★ 盾の状態を表す型（型チェックで使い回すため名前を付けて定義）
type ShieldState = 'INTACT' | 'CRACKED' | 'UNARMED'

const boss = reactive({
  active: false, id: 'knight', name: '', spriteKey: 'boss_knight',
  x: 640, y: GROUND_Y, vx: 0, vy: 0,
  hp: 620, maxHp: 620, scale: 1.2, pattern: 'KNIGHT',
  hurtTimer: 0, isDefeated: false, flashAlpha: 0,
  defeatTicks: 0, defeatFacing: 1,
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
let groundScrollX = 0

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
  const loopHpBoost = loops > 0 ? 2.8 * Math.pow(1.8, Math.min(20, loops - 1)) : 1.0
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
  chargeAbort?.abort()
  chargeLevel.value = 0
  keys.clear()
  deathOverlay.active = false
  player.controlLocked = true
  player.onGround = true
  player.coyoteTimer = 0
  player.isDashing = false
  player.invincibleTimer = 0
  player.hurtPoseTimer = 0
  activeStagePlan = null
  cloudWaveCount.value = 0
  stagePlanVersion.value = null
  enemies.forEach(e => e.abortController.abort())
  enemies.length = 0; bullets.length = 0; activeSlashes.length = 0; dropItems.length = 0; fireworks.length = 0
  impactParticles.length = 0; afterimages.length = 0; floatingTexts.length = 0
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

  let plan: StagePlan
  try {
    plan = await requestStagePlan(stageNum, stageSignal)
  } catch {
    if (stageSignal.aborted) return
    plan = buildOfflineStagePlan(stageNum)
    cloudStatus.value = 'OFFLINE'
  } finally {
    if (!stageSignal.aborted) isLoadingStage.value = false
  }
  if (stageSignal.aborted || componentDisposed) return
  // ボスの通常・被弾・撃破素材を同じステージのロード画面で先読み。
  isLoadingStage.value = true
  try {
    await preloadBossSprites(plan.boss.id, stageSignal)
  } finally {
    if (!stageSignal.aborted && !componentDisposed) isLoadingStage.value = false
  }
  if (stageSignal.aborted || componentDisposed) return
  activeStagePlan = plan
  cloudWaveCount.value = plan.enemy_waves.length
  stagePlanVersion.value = plan.plan_version

  try {
    await playMegamanIntroAsync(stageSignal)

    if (!fromBossGateCheckpoint) {
      currentTheme.isScrolling = true
      runGimmickSpawnerAsync(stageSignal)

      // Spawn order and timing now come from Cloud Run, with the identical
      // StageWave contract supplied by the offline fallback.
      let lastSpawnAt = 0
      for (const wave of plan.enemy_waves) {
        await waitAsync(Math.max(0, wave.spawn_delay_ms - lastSpawnAt), stageSignal)
        lastSpawnAt = wave.spawn_delay_ms
        const template = masterData.enemies.find((e: any) => e.type === wave.type)
        if (!template) continue
        spawnSingleEnemy({
          ...template, id: wave.id, hp: wave.hp, speed: wave.speed
        }, stageSignal)
        stageProgress.value = Math.min(96, (lastSpawnAt / plan.enemy_waves[plan.enemy_waves.length - 1].spawn_delay_ms) * 96)
      }
      await waitAsync(900, stageSignal)
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
      groundScrollX += 13
      await waitAsync(20, stageSignal)
    }
    obstacles.value = [
      { x: 220, y: GROUND_Y - 75, w: 95, h: 14, type: 'platform' },
      { x: 460, y: GROUND_Y - 75, w: 95, h: 14, type: 'platform' }
    ]
    pits.value = []
    fogGate.active = false
    fogGate.transitioning = false

    const plannedBoss = activeStagePlan?.stage === currentStage.value
      ? activeStagePlan.boss : buildOfflineStagePlan(currentStage.value).boss
    await startBossBattleAsync(plannedBoss, stageSignal)
  } catch {} finally {
    // A previous stage must never unlock a newer stage's intro.
    if (stageAbortController?.signal === stageSignal && !stageSignal.aborted) {
      player.controlLocked = false
    }
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
  boss.defeatTicks = 0; boss.defeatFacing = 1
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
  playSfx('warning')

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
        playSfx('warning')
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
          playSfx('warning')
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
        playSfx('warning')
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
  playSfx('warning')
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
  const stageSignal = stageAbortController?.signal
  if (!stageSignal || stageSignal.aborted) return
  boss.isDefeated = true
  boss.defeatTicks = 0
  boss.defeatFacing = player.x > boss.x ? -1 : 1
  boss.hurtTimer = 0
  boss.vx = 0; boss.vy = 0
  spawnImpact(boss.x, boss.y - (boss.hasShield ? 115 : 56), '#facc15', 26, 5.4)
  boss.warningLaserY = null; boss.warningSpikeX = null
  boss.abortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  enemies.length = 0
  bullets.length = 0

  try {
    screenShakeTimer = 14
    playSfx('bossDown')
    // Keep the illustrated DOWN pose on screen before the final dissolve.
    await waitAsync(1550, stageSignal)
    for (let i = 1; i <= 8; i++) {
      boss.flashAlpha = i / 8
      await waitAsync(45, stageSignal)
    }
    spawnFireworkBurst(boss.x, boss.y - 45)
    boss.active = false
    boss.flashAlpha = 0

    score.value += 2500 * currentStage.value
    commitBestScore()
    vibrate([40, 40, 80])
    player.isVictory = true
    player.vx = 0
    player.hurtPoseTimer = 0
    camera.targetX = player.x
    camera.targetY = player.y - 35
    camera.targetZoom = 1.85

    // 花火もゲーム時間で制御する。ポーズ中にタイマーが進むのを防ぐ。
    void (async () => {
      try {
        for (let f = 1; f <= 6; f++) {
          await waitAsync(280, stageSignal)
          spawnFireworkBurst(player.x + (Math.random() - 0.5) * 220, player.y - 60 - Math.random() * 80)
        }
      } catch { /* ステージ変更/終了によるキャンセル */ }
    })()

    await waitAsync(2100, stageSignal)
    camera.targetZoom = 1.0
    gameResult.value = 'CLEAR'
    playSfx('clear')
  } catch {
    // Restart/unmount aborts the victory animation without touching the new run.
  }
}

const onEnemyDefeated = (e: Enemy) => {
  playSfx('enemyDown')
  score.value += e.score
  spawnImpact(e.x, e.y - 30, '#facc15', 12, 3.1)
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
  scoreSubmitted.value = false
  scoreSubmitMessage.value = ''
  runVersion++
  lives.value = 3
  playerHp.value = maxHp.value
  startStageFromCloudRun(currentStage.value, true)
}

const resetFullGame = () => {
  manualPaused.value = false
  isNewRecord.value = false
  scoreSubmitted.value = false
  scoreSubmitMessage.value = ''
  runVersion++
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
    playSfx('charge1')
    await waitAsync(750, chargeAbort.signal)
    chargeLevel.value = 2
    playSfx('charge2')
    if (upgrades.maxChargeLevel >= 3) {
      await waitAsync(900, chargeAbort.signal)
      chargeLevel.value = 3
      playSfx('charge3')
    }
  } catch {}
}

// ====================================================
// ★ ショット＆偃月薙ぎ払い（Lv.2以上チャージ時のみ弾消し発動！）
// ====================================================
const fireFromPosition = (originX: number, originY: number, level: number, isOption = false, allowSlash = true) => {
  const pMul = (isOption ? 0.6 : 1.0) * upgrades.powerMultiplier
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
  if (upgrades.slashLv > 0 && !isOption && allowSlash) {
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

const fireGuitarWave = (level: number, allowSlash = true) => {
  playSfx(level >= 1 ? 'chargeShot' : 'shot')
  if (allowSlash && upgrades.slashLv > 0) playSfx('slash')
  player.shootPoseTimer = 18
  spawnImpact(player.x + player.facing * 36, player.y - 31,
    level >= 2 ? '#facc15' : '#f9a8d4', level >= 2 ? 10 : 4, level >= 2 ? 3.1 : 1.3)
  fireFromPosition(player.x + player.facing * 34, player.y - 30, level, false, allowSlash)
  for (let i = 1; i <= upgrades.options; i++) {
    const histIdx = Math.max(0, positionHistory.length - i * 14)
    const optPos = positionHistory[histIdx] || { x: player.x - player.facing * 28 * i, y: player.y }
    // オプションもチャージ段階をそのまま反映（威力は本体の60%）
    fireFromPosition(optPos.x, optPos.y - 28, level, true)
  }
}

const startDashAsync = async () => {
  if (!player.onGround || player.isDashing || player.controlLocked || player.isDown || player.isVictory) return
  player.isDashing = true
  playSfx('dash')
  player.vx = player.facing * PHYSICS.DASH_SPEED
  try { await waitAsync(280, stageAbortController?.signal) } catch {} finally { player.isDashing = false }
}

const keys = new Set<string>()
const gameKeyCodes = ['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Space', 'KeyZ', 'KeyX', 'KeyC']
const MOVE_CODES = ['ArrowLeft', 'ArrowRight']
// 右手側のボタン配置：DASH(小) / SHOT(大) / JUMP(大)
const touchActions = [
  { code: 'KeyC', symbol: '»', short: 'DASH', label: 'ダッシュ' },
  { code: 'KeyX', symbol: '♪', short: 'SHOT', label: '音符ショット（長押しでチャージ）' },
  { code: 'KeyZ', symbol: '▲', short: 'JUMP', label: 'ジャンプ' },
]
const pressedTouch = reactive(new Set<string>())

// ====================================================
// スマホ用オート射撃：ショットは自動連射＋自動チャージ、ボタンはジャンプだけ
//   ・通常弾を一定間隔で自動発射
//   ・裏でチャージが溜まり、最大段階に達したら自動でチャージ弾を発射
//   ・ダッシュは移動パッドの2回タップ（同じ向き）
// ====================================================
const AUTO_KEY = 'erika-rock-action:auto-fire'
const autoFirePref = ref(localStorage.getItem(AUTO_KEY) !== 'off')
const autoFire = computed(() => isTouch.value && autoFirePref.value)
const toggleAutoFire = () => {
  autoFirePref.value = !autoFirePref.value
  try { localStorage.setItem(AUTO_KEY, autoFirePref.value ? 'on' : 'off') } catch { /* 保存不可 */ }
  resetInputState()
  playSfx('select')
}
const visibleTouchActions = computed(() => autoFire.value ? touchActions.filter(a => a.code === 'KeyZ') : touchActions)
const AUTO_SHOT_INTERVAL = 13 // フレーム（約0.2秒ごと）
// 手動チャージ(400/1150/2050ms)より少し遅め：連射しながら溜まるぶんのバランス調整
const AUTO_CHARGE_FRAMES = [36, 105, 185]
let autoShotTimer = 0
let autoChargeFrames = 0
let autoShotCount = 0
const canAct = () => !isPaused.value && !player.controlLocked && !deathOverlay.active &&
  !player.isDown && !player.isVictory && !gameResult.value && !isLoadingStage.value
const autoFireTick = () => {
  if (!autoFire.value) return
  if (!canAct()) {
    if (autoChargeFrames > 0) { autoChargeFrames = 0; chargeLevel.value = 0 }
    autoShotTimer = 10
    return
  }
  if (--autoShotTimer <= 0) {
    autoShotTimer = AUTO_SHOT_INTERVAL
    autoShotCount++
    // 薙ぎ払いは通常弾4発に1回（毎発だと画面がうるさいため）＋チャージ弾では毎回
    fireGuitarWave(0, autoShotCount % 4 === 0)
  }
  autoChargeFrames++
  const maxLv = upgrades.maxChargeLevel
  const lv = AUTO_CHARGE_FRAMES.filter((f, i) => i < maxLv && autoChargeFrames >= f).length
  if (lv !== chargeLevel.value) {
    chargeLevel.value = lv
    if (lv > 0) playSfx(`charge${lv}` as SfxName)
  }
  if (lv >= maxLv && autoChargeFrames >= AUTO_CHARGE_FRAMES[maxLv - 1] + 8) {
    fireGuitarWave(lv)
    chargeLevel.value = 0
    autoChargeFrames = 0
    autoShotTimer = AUTO_SHOT_INTERVAL
  }
}
let lastPadTap = { dir: 0, at: 0 }
const actionButtonClass = (code: string) => {
  const classes = [`action-btn--${code === 'KeyZ' ? 'jump' : code === 'KeyX' ? 'shot' : 'dash'}`]
  if (pressedTouch.has(code)) classes.push('is-pressed')
  if (code === 'KeyX' && chargeLevel.value > 0) classes.push(`is-charge-${chargeLevel.value}`)
  return classes
}

// 移動パッド：押した位置／スライドした位置で左右を決める（親指を離さず切り返せる）
const padDir = ref<-1 | 0 | 1>(0)
let padPointerId: number | null = null
const updatePadFromEvent = (e: PointerEvent) => {
  const el = e.currentTarget as HTMLElement | null
  if (!el) return
  const rect = el.getBoundingClientRect()
  const dx = e.clientX - (rect.left + rect.width / 2)
  const dead = rect.width * 0.06
  const next: -1 | 0 | 1 = Math.abs(dx) < dead ? padDir.value : dx < 0 ? -1 : 1
  if (next !== padDir.value) {
    padDir.value = next
    if (next !== 0) vibrate(6)
  }
}
const registerPadTap = () => {
  if (padDir.value === 0) return
  const t = performance.now()
  if (lastPadTap.dir === padDir.value && t - lastPadTap.at < 300) {
    player.facing = padDir.value
    pressControl('KeyC'); releaseControl('KeyC')
    lastPadTap = { dir: 0, at: 0 }
  } else {
    lastPadTap = { dir: padDir.value, at: t }
  }
}
const onPadDown = (e: PointerEvent) => {
  if (padPointerId !== null && padPointerId !== e.pointerId) return
  padPointerId = e.pointerId
  ;(e.currentTarget as HTMLElement).setPointerCapture?.(e.pointerId)
  padDir.value = 0
  updatePadFromEvent(e)
  registerPadTap()
}
const onPadMove = (e: PointerEvent) => {
  if (e.pointerId === padPointerId) updatePadFromEvent(e)
}
const onPadUp = (e?: PointerEvent) => {
  if (e && padPointerId !== null && e.pointerId !== padPointerId) return
  padPointerId = null
  padDir.value = 0
}
const isMoveHeld = (dir: -1 | 1) =>
  keys.has(dir === -1 ? 'ArrowLeft' : 'ArrowRight') || padDir.value === dir

const pressControl = (code: string) => {
  if (keys.has(code)) return
  // 移動キーは演出中でも「押しっぱなし」を覚えておき、操作可能になった瞬間から動けるようにする
  if (MOVE_CODES.includes(code)) {
    if (!isPaused.value) keys.add(code)
    return
  }
  if (isPaused.value || player.controlLocked || deathOverlay.active ||
      player.isDown || player.isVictory || gameResult.value || isLoadingStage.value) return
  keys.add(code)
  if ((code === 'ArrowUp' || code === 'Space' || code === 'KeyZ') && (player.onGround || player.coyoteTimer > 0)) {
    player.vy = PHYSICS.JUMP_VELOCITY
    player.onGround = false
    player.coyoteTimer = 0
    player.scaleX = 0.85; player.scaleY = 1.18
    spawnImpact(player.x, player.y - 3, '#94a3b8', 6, 1.5)
    playSfx('jump')
  }
  if (code === 'ArrowDown' || code === 'KeyC') startDashAsync()
  if (code === 'KeyX') {
    fireGuitarWave(0)
    startChargeAsync()
  }
}
const releaseControl = (code: string) => {
  if (!keys.has(code)) return
  keys.delete(code)
  if ((code === 'ArrowUp' || code === 'Space' || code === 'KeyZ') && player.vy < -1.5) {
    player.vy *= 0.45
  }
  if (code === 'KeyX') {
    const level = chargeLevel.value
    chargeAbort?.abort()
    chargeLevel.value = 0
    if (level > 0 && !player.controlLocked && !player.isDown && !gameResult.value) {
      fireGuitarWave(level)
    }
  }
}
const onKeyDown = (e: KeyboardEvent) => {
  if (e.code === 'KeyP') {
    const el = e.target
    if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement ||
        (el instanceof HTMLElement && el.isContentEditable)) return
    e.preventDefault()
    if (!e.repeat) toggleManualPause()
    return
  }
  if (!gameKeyCodes.includes(e.code)) return
  const el = e.target
  if (el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement ||
      (el instanceof HTMLElement && el.isContentEditable)) return
  e.preventDefault()
  // ステージ開始時に keys がリセットされても、押しっぱなしの移動キーはリピートで復帰させる
  if (!e.repeat || MOVE_CODES.includes(e.code)) pressControl(e.code)
}
const onKeyUp = (e: KeyboardEvent) => releaseControl(e.code)
const pressTouch = (code: string, event: PointerEvent) => {
  const element = event.currentTarget
  if (element instanceof HTMLElement) element.setPointerCapture?.(event.pointerId)
  pressedTouch.add(code)
  vibrate(8)
  pressControl(code)
}
const releaseTouch = (code: string) => {
  if (!pressedTouch.has(code)) return
  pressedTouch.delete(code)
  releaseControl(code)
}
const resetInputState = () => {
  keys.clear()
  pressedTouch.clear()
  onPadUp()
  chargeAbort?.abort()
  chargeLevel.value = 0
  autoChargeFrames = 0
}
const toggleManualPause = () => {
  manualPaused.value = !manualPaused.value
  resetInputState()
}
const onWindowBlur = () => {
  windowInactive.value = true
  resetInputState()
}
const onWindowFocus = () => { windowInactive.value = document.hidden }
const onVisibilityChange = () => {
  windowInactive.value = document.hidden
  if (document.hidden) resetInputState()
}

let animFrameId = 0
let gameTimeMs = 0
let lastFrameTime = performance.now()
let frameAccumulator = 0
const FRAME_MS = 1000 / 60
const animationLoop = (now: number) => {
  if (componentDisposed) return
  animFrameId = requestAnimationFrame(animationLoop)
  if (isPaused.value) {
    lastFrameTime = now
    frameAccumulator = 0
    return
  }
  frameAccumulator += Math.min(100, Math.max(0, now - lastFrameTime))
  lastFrameTime = now
  let steps = 0
  while (frameAccumulator >= FRAME_MS && steps < 5) {
    gameTimeMs += FRAME_MS
    advanceGameWaits(FRAME_MS)
    autoFireTick()
    updateAndDraw(gameTimeMs)
    frameAccumulator -= FRAME_MS
    steps++
  }
  if (steps >= 5) frameAccumulator = 0
}

const getPlayerSpriteKey = () => {
  if (player.isDown) return 'down'
  if (player.isVictory) return 'victory'
  if (player.hurtPoseTimer > 0) return 'hurt'
  if (!player.onGround) return player.shootPoseTimer > 0 ? 'jumpShoot' : 'jump'
  if (player.shootPoseTimer > 0) return 'shoot'
  if (Math.abs(player.vx) > 0.4) return Math.floor(player.runAnimTimer / 9) % 2 === 0 ? 'run1' : 'run2'
  return 'idle'
}

// Visual-only sizing, independent of hitboxes and Cloud Run boss statistics.
// DOWN art is often wide (even in a square transparent PNG), so cap its width.
interface BossDrawProfile { normalH: number; normalW: number; downW: number; downH: number; downX?: number }
const BOSS_DRAW: Record<string, BossDrawProfile> = {
  knight:    { normalH: 108, normalW: 115, downW: 177, downH: 85 },
  concierge: { normalH: 105, normalW: 110, downW: 172, downH: 82 },
  yukata:    { normalH: 104, normalW: 108, downW: 174, downH: 82 },
  ivory:     { normalH: 110, normalW: 116, downW: 178, downH: 85 },
  tea:       { normalH: 113, normalW: 111, downW: 174, downH: 85 },
  kimono:    { normalH: 110, normalW: 115, downW: 183, downH: 85 },
  flower:    { normalH: 115, normalW: 121, downW: 194, downH: 88 },
  camellia:  { normalH: 109, normalW: 115, downW: 185, downH: 85 },
  dress:     { normalH: 118, normalW: 121, downW: 190, downH: 85 },
  gothic:    { normalH: 119, normalW: 125, downW: 190, downH: 88 },
  queen:     { normalH: 125, normalW: 132, downW: 205, downH: 90 },
  sunflower: { normalH: 290, normalW: 300, downW: 242, downH: 114, downX: -12 },
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
    // Unarmed画像が未配置の場合はHURT画像を代用して、透明な四角形表示を防ぐ。
    if (sprites[`boss_${boss.id}_unarmed`]) return `boss_${boss.id}_unarmed`
    if (sprites[`boss_${boss.id}_hurt`]) return `boss_${boss.id}_hurt`
    return boss.spriteKey
  }
  return boss.spriteKey
}

const applyDamageToBoss = (rawDamage: number, isPiercing = false) => {
  if (!boss.active || boss.isDefeated) return

  if (boss.hasShield && boss.shieldState !== 'UNARMED') {
    boss.shieldHp = Math.max(0, boss.shieldHp - rawDamage)
    playSfx('guard')
    floatingTexts.push({ x: boss.x - 55, y: boss.y - 160 + (Math.random() - 0.5) * 30, text: `GUARD -${rawDamage}`, color: '#38bdf8', alpha: 1.0 })
    spawnImpact(boss.x - 55, boss.y - 140, '#67e8f9', 5, 2.4)

    if (boss.shieldHp <= 0) {
      boss.shieldState = 'UNARMED'
      playSfx('shieldBreak')
      spawnImpact(boss.x - 46, boss.y - 125, '#facc15', 32, 5.2)
      screenShakeTimer = 14
      spawnFireworkBurst(boss.x - 50, boss.y - 150)
      floatingTexts.push({ x: boss.x - 40, y: boss.y - 210, text: 'SHIELD BREAK!!', color: '#facc15', alpha: 1.0 })
    } else if (boss.shieldHp <= boss.maxShieldHp * 0.5 && boss.shieldState === 'INTACT') {
      boss.shieldState = 'CRACKED'
      spawnImpact(boss.x - 42, boss.y - 130, '#67e8f9', 14, 3.5)
      screenShakeTimer = 8
      floatingTexts.push({ x: boss.x - 40, y: boss.y - 190, text: 'SHIELD CRACKED!', color: '#fbbf24', alpha: 1.0 })
    }
    return
  }

  boss.hp = Math.max(0, boss.hp - rawDamage)
  playSfx('bossHit')
  boss.hurtTimer = 14
  spawnImpact(boss.x, boss.y - (boss.hasShield ? 66 : 48), isPiercing ? '#facc15' : '#f472b6', isPiercing ? 16 : 9, isPiercing ? 4 : 2.7)
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

let runVersion = 0
const triggerYouDiedSequenceAsync = async (fellInPit = false) => {
  const capturedVersion = runVersion
  if (deathOverlay.active || player.isDown || gameResult.value) return
  player.controlLocked = true
  player.isDown = true
  playSfx('death')
  player.vx = 0
  chargeAbort?.abort()
  chargeLevel.value = 0

  stageAbortController?.abort()
  enemies.forEach(e => e.abortController.abort())
  boss.abortController?.abort()

  if (!fellInPit) { try { await waitAsync(1100) } catch { return } }
  if (capturedVersion !== runVersion) return

  lives.value--
  const resumeAtFog = boss.active || checkpointReachedBossGate.value
  deathOverlay.message = lives.value > 0
    ? (resumeAtFog ? 'ボス部屋前（白い霧）から再出撃します...' : 'ステージ初期地点から再出撃します...')
    : '残機がすべて失われました'
  deathOverlay.active = true

  try { await waitAsync(2400) } catch { return }
  if (capturedVersion !== runVersion) return
  deathOverlay.active = false

  if (lives.value > 0) {
    playerHp.value = maxHp.value
    startStageFromCloudRun(currentStage.value, resumeAtFog)
  } else {
    commitBestScore()
    gameResult.value = 'GAMEOVER'
    void fetchRankings()
  }
}

const damagePlayer = (amount: number) => {
  if (player.invincibleTimer > 0 || deathOverlay.active || player.isDown || player.isVictory || gameResult.value || player.controlLocked) return
  if (upgrades.barrierHp > 0) {
    upgrades.barrierHp--; player.invincibleTimer = 55
    playSfx('barrier')
    spawnImpact(player.x, player.y - 34, '#38bdf8', 10, 3.0)
    floatingTexts.push({ x: player.x, y: player.y - 50, text: 'SHIELD!', color: '#38bdf8', alpha: 1.0 })
    return
  }

  playerHp.value = Math.max(0, playerHp.value - amount)
  playSfx('playerHit')
  vibrate(amount >= 16 ? 45 : 25)
  player.invincibleTimer = 82
  player.hurtPoseTimer = 24
  spawnImpact(player.x, player.y - 40, '#fb7185', 12, 3.4)
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

  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  // 以降はすべて論理座標 800×450 で描画（実ピクセルへの拡大はここで一括）
  ctx.setTransform(renderScale.value, 0, 0, renderScale.value, 0, 0)
  ctx.imageSmoothingQuality = 'high'

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
      if (isMoveHeld(-1)) {
        player.vx = Math.max(player.vx - PHYSICS.MOVE_ACCEL, -PHYSICS.MOVE_MAX_SPEED)
        player.facing = -1
      } else if (isMoveHeld(1)) {
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

    if (player.y > VIEW_H + 30 && !deathOverlay.active && !player.isDown) {
      playerHp.value = 0
      triggerYouDiedSequenceAsync(true)
    }

    if (landed) {
      if (!player.onGround) {
        player.scaleX = 1.16; player.scaleY = 0.84
        spawnImpact(player.x, player.y - 2, '#94a3b8', 7, 1.7)
      }
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
    ctx.translate(VIEW_W / 2, VIEW_H / 2)
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
  ctx.fillRect(-100, -100, VIEW_W + 200, VIEW_H + 200)

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
  groundScrollX += scrollSpd
  const style = currentTheme.bgStyle
  bgBuildings.forEach((b, idx) => {
    const bx = (b.x - bgScrollX + 880) % 880 - 55
    if (style === 'CYBER') {
      // サイバーは音量メーターのように伸び縮みするビル
      const dynH = 40 + Math.abs(Math.sin(now * 0.004 + idx)) * 90
      ctx.fillStyle = 'rgba(15, 23, 42, 0.55)'
      ctx.fillRect(bx, GROUND_Y - dynH, b.w - 8, dynH)
      ctx.fillStyle = 'rgba(52, 211, 153, 0.35)'
      for (let y = GROUND_Y - dynH + 4; y < GROUND_Y - 4; y += 8) ctx.fillRect(bx + 4, y, b.w - 16, 3)
    } else {
      const img = getBuilding(style, b.w, b.h, idx)
      ctx.drawImage(img, bx, GROUND_Y - b.h - 30, b.w, b.h + 30)
    }
  })

  drawGround(ctx, style, currentTheme.groundColor, currentTheme.lineColor, GROUND_Y, VIEW_W, VIEW_H, groundScrollX)

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
    drawPit(ctx, style, currentTheme.lineColor, pit.x, pit.w, GROUND_Y, VIEW_H, now)
  }

  for (const obs of obstacles.value) {
    if (obs.type === 'wall') drawWallObstacle(ctx, style, currentTheme.lineColor, obs.x, obs.y, obs.w, obs.h)
    else drawPlatform(ctx, style, currentTheme.lineColor, obs.x, obs.y, obs.w, obs.h)
  }

  if (fogGate.active) {
    ctx.save()
    const fogGrad = ctx.createLinearGradient(fogGate.x - 25, 0, VIEW_W, 0)
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
  // Player sprite poses share a visible bottom anchor. The wide DOWN pose is
  // fitted by WIDTH, not stretched into the same square as the standing pose.
  const drawPlayerPose = (key: string, x: number, y: number, facing: number, alpha = 1) => {
    const isDown = key === 'down'
    const img = sprites[key]
    if (!img) { drawSprite(ctx, img, x, y, facing, playerDrawSize, 1, 1, alpha, 0); return }
    drawFittedSprite(ctx, img, x, y, facing, {
      maxHeight: isDown ? 64 : (key === 'victory' ? 82 : 78),
      maxWidth: isDown ? 148 : 98,
      scaleX: isDown ? 1 : player.scaleX,
      scaleY: isDown ? 1 : (player.isDashing ? 0.74 : player.scaleY),
      opacity: alpha,
    })
  }
  for (let i = afterimages.length - 1; i >= 0; i--) {
    const aft = afterimages[i]
    aft.alpha -= 0.05
    if (aft.alpha <= 0) { afterimages.splice(i, 1); continue }
    ctx.save()
    ctx.filter = 'hue-rotate(190deg) saturate(1.5)'
    drawPlayerPose(aft.spriteKey, aft.x, aft.y, aft.facing, aft.alpha)
    ctx.restore()
  }

  for (let i = 1; i <= upgrades.options; i++) {
    const histIdx = Math.max(0, positionHistory.length - i * 14)
    const optPos = positionHistory[histIdx] || { x: player.x - player.facing * 28 * i, y: player.y }
    const floatY = Math.sin(now * 0.008 + i) * 4
    ctx.save()
    const optColor = chargeLevel.value === 3 ? '#e879f9' : chargeLevel.value === 2 ? '#facc15' : '#38bdf8'
    if (chargeLevel.value > 0) {
      // チャージ中はオプションも光をまとう
      ctx.beginPath()
      ctx.arc(optPos.x, optPos.y - 28 + floatY, 13 + chargeLevel.value * 2 + Math.sin(now * 0.03 + i) * 2, 0, Math.PI * 2)
      ctx.strokeStyle = optColor; ctx.lineWidth = 1.5; ctx.globalAlpha = 0.7; ctx.stroke(); ctx.globalAlpha = 1
    }
    ctx.beginPath()
    ctx.arc(optPos.x, optPos.y - 28 + floatY, 9, 0, Math.PI * 2)
    ctx.fillStyle = optColor; ctx.shadowColor = optColor; ctx.shadowBlur = 10; ctx.fill()
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
    if (player.onGround && !player.isDown) {
      ctx.save()
      ctx.fillStyle = 'rgba(0, 0, 0, 0.25)'
      ctx.beginPath(); ctx.ellipse(player.x, player.y + 1, 24, 3.7, 0, 0, Math.PI * 2); ctx.fill()
      ctx.restore()
    }
    const drawFacing = player.isVictory ? 1 : player.facing
    drawPlayerPose(getPlayerSpriteKey(), player.x, player.y, drawFacing)
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

    // 光の刀身＋三日月の残光（見た目のみ。判定は下の円判定のまま）
    const tip = drawCrescentSlash(ctx, cx, cy, sw, player.facing)
    if (sw.timer % 2 === 0) spawnImpact(tip.tipX, tip.tipY, sw.timer % 4 === 0 ? '#ffffff' : sw.color, 1, 1.4)

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
      playSfx(item.type === '1UP' ? 'oneUp' : 'item')
      if (item.type === '1UP') lives.value++
      else if (item.type === 'HEAL') playerHp.value = Math.min(maxHp.value, playerHp.value + 25)
      else score.value += 300
      floatingTexts.push({ x: item.x, y: item.y - 15, text: label, color: '#4ade80', alpha: 1.0 })
      dropItems.splice(i, 1)
      continue
    }
    if (item.lifeTimer <= 0 || item.y > VIEW_H + 30) dropItems.splice(i, 1)
  }

  const enemyDrawSize = Math.round(76 * CHAR_SCALE)
  for (let i = enemies.length - 1; i >= 0; i--) {
    const e = enemies[i]
    const prevEnemyY = e.y
    if (e.stunTimer && e.stunTimer > 0) {
      e.stunTimer--
      if (e.stunTimer <= 0) e.isStunned = false
    }
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
    const enemyImg = sprites[e.type]
    const enemySprite = enemyImg ? getTintedSprite(e.type, enemyImg, e.hueRotate) : undefined
    // 色替えはキャッシュ済みなので filter は不要（画像未読込時は代替の矩形を青で描く）
    drawSprite(ctx, enemySprite, e.x + shakeX, e.y, enemyFacing, enemyDrawSize, 1, stunFlipY, 1.0,
      enemySprite ? 0 : e.hueRotate || 1)

    if (e.hp < e.maxHp) {
      ctx.fillStyle = '#1e293b'; ctx.fillRect(e.x - 16, e.y - 62, 32, 4)
      ctx.fillStyle = '#f43f5e'; ctx.fillRect(e.x - 16, e.y - 62, 32 * (e.hp / e.maxHp), 4)
    }

    const enemyHitHalfWidth = e.type === 'hedgehog' ? 40 : 28
    if (!player.isDown && !player.isVictory && Math.abs(player.x - e.x) < enemyHitHalfWidth && Math.abs(player.y - e.y) < 34) {
      if (player.vy > 0 && player.y < e.y - 10) {
        if (e.spiky) {
          damagePlayer(14)
        } else if (e.stompable) {
          player.vy = PHYSICS.BOUNCE_VELOCITY
          playSfx('stomp')
          player.scaleX = 1.22; player.scaleY = 0.78
          const stompDmg = Math.round(24 * upgrades.powerMultiplier)
          e.hp -= stompDmg
          floatingTexts.push({ x: e.x, y: e.y - 45, text: `${stompDmg}`, color: '#facc15', alpha: 1.0 })
          if (e.type === 'turtle' && e.hp > 0) { e.isStunned = true; e.stunTimer = 85 }
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
      ctx.fillRect(0, boss.warningLaserY - 12, VIEW_W, 24)
      ctx.strokeStyle = '#ef4444'; ctx.setLineDash([8, 5]); ctx.lineWidth = 2
      ctx.beginPath(); ctx.moveTo(0, boss.warningLaserY); ctx.lineTo(VIEW_W, boss.warningLaserY); ctx.stroke()
      ctx.restore()
    }

    if (boss.warningSpikeX !== null) {
      ctx.save()
      ctx.fillStyle = 'rgba(168, 85, 247, 0.35)'
      ctx.fillRect(boss.warningSpikeX - 18, GROUND_Y - 90, 36, 90)
      ctx.restore()
    }

    const bossFacing = boss.isDefeated ? boss.defeatFacing : (player.x > boss.x ? -1 : 1)
    const activeBossKey = getBossActiveSpriteKey()
    const profile = BOSS_DRAW[boss.id] ?? BOSS_DRAW.knight
    const isDownPose = boss.isDefeated && !!sprites[`boss_${boss.id}_down`]
    const isUnarmed = boss.hasShield && boss.shieldState === 'UNARMED'
    const bossHeight = isDownPose ? profile.downH : isUnarmed ? 132 : profile.normalH
    const bossWidth = isDownPose ? profile.downW : isUnarmed ? 139 : profile.normalW
    const bossFloor = boss.isDefeated
      ? boss.y + (GROUND_Y - boss.y) * Math.min(1, boss.defeatTicks / 18)
      : boss.y
    if (boss.isDefeated && boss.defeatTicks < 18) boss.defeatTicks++

    ctx.save()
    // Ground shadow and hit feedback provide motion without replacing the art.
    ctx.beginPath()
    ctx.ellipse(boss.x, GROUND_Y + 1, isDownPose ? 59 : (boss.hasShield && !isUnarmed ? 78 : 33), 5, 0, 0, Math.PI * 2)
    ctx.fillStyle = 'rgba(0, 0, 0, 0.28)'; ctx.fill()
    if (boss.flashAlpha > 0) {
      ctx.filter = `brightness(${1 + boss.flashAlpha * 3.0}) opacity(${1 - boss.flashAlpha * 0.65})`
    } else if (boss.hurtTimer > 0 && !sprites[`boss_${boss.id}_hurt`]) {
      ctx.filter = 'brightness(1.6)'
    }
    if (sprites[activeBossKey]) {
      drawFittedSprite(ctx, sprites[activeBossKey], boss.x, bossFloor, bossFacing, {
        maxHeight: bossHeight, maxWidth: bossWidth,
        offsetX: isDownPose ? (profile.downX ?? 0) : 0,
      })
    } else {
      // Missing custom sprite: preserve the v2 fallback, do not crash.
      drawSprite(ctx, undefined, boss.x, bossFloor, bossFacing, bossHeight, 1, 1, 1, 0)
    }
    ctx.restore()
    if (boss.hurtTimer > 0 && !boss.isDefeated) {
      const centerY = boss.y - (isUnarmed ? 64 : boss.hasShield ? 130 : 48)
      const radius = 15 + (14 - boss.hurtTimer) * 2.2
      ctx.save()
      ctx.beginPath(); ctx.arc(boss.x, centerY, radius, 0, Math.PI * 2)
      ctx.strokeStyle = `rgba(250, 204, 21, ${0.48 * boss.hurtTimer / 14})`
      ctx.lineWidth = 2.4; ctx.stroke(); ctx.restore()
    }

    // 盾破壊後は生身のエリカ用の接触判定へ縮小する。
    const shieldVisible = boss.hasShield && boss.shieldState !== 'UNARMED'
    const contactW = shieldVisible ? 55 : 32
    const contactH = shieldVisible ? 260 : 44
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

    // 光る弾は事前描画したキャッシュを貼るだけ（shadowBlur を毎フレーム使わない）
    drawBulletGlyph(ctx, b.noteSymbol, b.color, b.radius, b.x, b.y)

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
        const hitHalfWidth = e.type === 'hedgehog' ? 40 : 28
        if (Math.abs(b.x - e.x) < hitHalfWidth && Math.abs(b.y - (e.y - 26)) < 30 &&
            !b.hitTargets?.has(e.id)) {
          if (e.isHidden && !b.piercing) {
            b.vx = -b.vx * 0.8; b.vy = -2; break
          }
          const dmg = (e.armored && !b.piercing && !e.isStunned) ? Math.ceil(b.damage * 0.4) : b.damage
          e.hp -= dmg; hit = true
          playSfx('enemyHit')
          if (b.piercing) (b.hitTargets ??= new Set()).add(e.id)
          floatingTexts.push({ x: e.x, y: e.y - 42, text: `${dmg}`, color: b.piercing ? '#facc15' : '#ffffff', alpha: 1.0 })
          if (e.hp <= 0) { onEnemyDefeated(e); enemies.splice(j, 1) }
          if (!b.piercing) break
        }
      }
      if (hit && !b.piercing) { bullets.splice(i, 1); continue }

      if (boss.active && !boss.isDefeated) {
        // 盾がUNARMEDなら見た目も当たり判定も小さくする。
        const shieldVisible = boss.hasShield && boss.shieldState !== 'UNARMED'
        const hitW = shieldVisible ? 68 : 36
        const hitTop = shieldVisible ? boss.y - 290 : boss.y - 75
        if (Math.abs(b.x - boss.x) < hitW && b.y >= hitTop && b.y <= boss.y &&
            !b.hitTargets?.has('BOSS')) {
          if (b.piercing) (b.hitTargets ??= new Set()).add('BOSS')
          applyDamageToBoss(b.damage, !!b.piercing)
          if (!b.piercing || (boss.hasShield && boss.shieldState !== 'UNARMED')) {
            bullets.splice(i, 1)
          }
          continue
        }
      }
    }

    if (b.x < -60 || b.x > VIEW_W + 60 || b.y < -60 || b.y > VIEW_H + 60) {
      bullets.splice(i, 1)
    }
  }

  for (let i = impactParticles.length - 1; i >= 0; i--) {
    const p = impactParticles[i]
    p.x += p.vx; p.y += p.vy; p.vy += 0.11
    p.vx *= 0.94; p.life--
    if (p.life <= 0) { impactParticles.splice(i, 1); continue }
    ctx.save()
    ctx.globalAlpha = Math.max(0, p.life / p.maxLife)
    ctx.fillStyle = p.color
    ctx.beginPath(); ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2); ctx.fill()
    ctx.restore()
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
  ctx: CanvasRenderingContext2D, img: HTMLImageElement | HTMLCanvasElement | undefined,
  x: number, y: number, facing: number, size: number,
  scaleX: number, scaleY: number, alpha: number, hueRotateDeg: number
) => {
  ctx.save()
  ctx.globalAlpha = alpha
  ctx.translate(x, y)
  ctx.scale(facing * scaleX, scaleY)
  const ready = img instanceof HTMLCanvasElement ? img.width > 0 : !!img && img.complete && img.naturalWidth > 0
  if (img && ready) {
    if (hueRotateDeg !== 0) ctx.filter = `hue-rotate(${hueRotateDeg}deg) saturate(1.3)`
    // Preserve the portrait / landscape ratio of the supplied PNG artwork.
    const w0 = img instanceof HTMLCanvasElement ? img.width : img.naturalWidth
    const h0 = img instanceof HTMLCanvasElement ? img.height : img.naturalHeight
    const width = size * Math.min(2.0, w0 / h0)
    ctx.drawImage(img, -width / 2, -size + 5, width, size)
  } else {
    ctx.fillStyle = hueRotateDeg ? '#38bdf8' : '#ec4899'
    ctx.fillRect(-size / 3, -size * 0.8, (size * 2) / 3, size * 0.8)
  }
  ctx.restore()
}

// 一時停止中は BGM・効果音も止める
watch(isPaused, (paused) => {
  if (paused) { bgm.pause(); suspendAudio() }
  else { resumeAudio(); if (sound.bgm && audioUnlocked) bgm.play() }
})

onMounted(async () => {
  window.addEventListener('pointerdown', onFirstGesture, { capture: true })
  window.addEventListener('keydown', onFirstGesture, { capture: true })
  void bgm.init()
  void fetchRankings()
  await loadMasterJsonAsync(lifecycleAbort.signal)
  if (lifecycleAbort.signal.aborted) return
  buildSpriteCatalog()
  await preloadSpriteKeys([
    'idle', 'run1', 'run2', 'shoot', 'jump', 'jumpShoot', 'hurt', 'victory', 'down',
    ...masterData.enemies.map((e: any) => e.type),
  ], lifecycleAbort.signal)
  if (lifecycleAbort.signal.aborted) return
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('keyup', onKeyUp)
  window.addEventListener('blur', onWindowBlur)
  window.addEventListener('focus', onWindowFocus)
  document.addEventListener('visibilitychange', onVisibilityChange)
  windowInactive.value = document.hidden
  lastFrameTime = performance.now()
  frameAccumulator = 0
  animFrameId = requestAnimationFrame(animationLoop)
  void startStageFromCloudRun(1, false)
})

onUnmounted(() => {
  componentDisposed = true
  window.removeEventListener('pointerdown', onFirstGesture, { capture: true })
  window.removeEventListener('keydown', onFirstGesture, { capture: true })
  bgm.dispose()
  suspendAudio()
  lifecycleAbort.abort()
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('keyup', onKeyUp)
  window.removeEventListener('blur', onWindowBlur)
  window.removeEventListener('focus', onWindowFocus)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  resetInputState()
  runVersion++
  cancelAnimationFrame(animFrameId)
  stageAbortController?.abort()
  chargeAbort?.abort()
})
</script>
<style scoped>
/* ------- 共通 ------- */
.fade-enter-active,
.fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

.game-shell,
.game-shell * {
  -webkit-touch-callout: none;
  -webkit-tap-highlight-color: transparent;
}
.game-shell canvas,
.touch-panel,
.touch-overlay { touch-action: none; }
.game-shell button { touch-action: manipulation; }

.kbd {
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  border: 1px solid rgb(71 85 105);
  background: rgb(30 41 59);
}

.hud-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  border: 1px solid rgb(71 85 105);
  background: rgb(30 41 59);
  color: rgb(226 232 240);
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1;
}
.hud-btn:active { background: rgb(51 65 85); }
.hud-btn--wide { width: auto; padding: 0 0.45rem; font-size: 0.65rem; letter-spacing: 0.05em; }
.hud-btn.is-on { border-color: rgb(34 211 238); color: rgb(165 243 252); }
.hud-btn.is-off { opacity: 0.55; }
.action-cluster.is-solo { grid-template-columns: auto; }
.action-cluster.is-solo .action-btn--jump { width: 5.25rem; height: 5.25rem; margin-bottom: 0; }

/* iPhone のノッチ・ホームバーを避ける */
.safe-x {
  padding-left: max(0.5rem, env(safe-area-inset-left));
  padding-right: max(0.5rem, env(safe-area-inset-right));
}
.safe-b { padding-bottom: max(0.5rem, env(safe-area-inset-bottom)); }
.is-immersive .hud { padding-top: max(0.25rem, env(safe-area-inset-top)); }

/* ------- 移動パッド ------- */
.move-pad {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 9.5rem;
  height: 4.5rem;
  padding: 0 0.85rem;
  border-radius: 2.25rem;
  border: 1px solid rgb(14 116 144);
  background: linear-gradient(90deg, rgb(30 41 59), rgb(15 23 42) 50%, rgb(30 41 59));
  box-shadow: inset 0 2px 8px rgb(0 0 0 / 0.5);
}
.move-pad::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 22%;
  bottom: 22%;
  width: 1px;
  background: rgb(51 65 85);
}
.move-pad__arrow {
  font-size: 1.4rem;
  font-weight: 900;
  color: rgb(148 163 184);
  transition: color 0.08s, transform 0.08s;
}
.move-pad__arrow.is-on {
  color: rgb(103 232 249);
  transform: scale(1.2);
  text-shadow: 0 0 10px rgb(34 211 238 / 0.8);
}
.move-pad--overlay {
  background: rgb(15 23 42 / 0.45);
  border-color: rgb(103 232 249 / 0.45);
  backdrop-filter: blur(2px);
}

/* ------- アクションボタン（JUMP/SHOT大・DASH小） ------- */
.action-cluster {
  display: grid;
  grid-template-columns: auto auto auto;
  align-items: end;
  gap: 0.6rem;
}
.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 9999px;
  border: 2px solid rgb(190 24 93);
  background: rgb(30 41 59);
  color: #fff;
  user-select: none;
  transition: transform 0.06s, background-color 0.08s, box-shadow 0.12s;
}
.action-btn__icon { font-size: 1.35rem; font-weight: 900; line-height: 1; }
.action-btn__label { font-size: 0.55rem; font-weight: 700; letter-spacing: 0.08em; opacity: 0.8; margin-top: 2px; }
.action-btn--jump, .action-btn--shot { width: 4.25rem; height: 4.25rem; }
.action-btn--dash { width: 3.1rem; height: 3.1rem; border-color: rgb(14 116 144); margin-bottom: 0.25rem; }
.action-btn--dash .action-btn__icon { font-size: 1.1rem; }
.action-btn--jump { border-color: rgb(16 185 129); margin-bottom: 1.6rem; }
.action-btn.is-pressed { transform: scale(0.92); background: rgb(131 24 67); }
.action-btn--jump.is-pressed { background: rgb(6 95 70); }
.action-btn--dash.is-pressed { background: rgb(21 94 117); }
/* チャージ段階をボタンの光り方で表示 */
.action-btn--shot.is-charge-1 { box-shadow: 0 0 0 3px rgb(34 211 238 / 0.8), 0 0 14px rgb(34 211 238 / 0.7); }
.action-btn--shot.is-charge-2 { box-shadow: 0 0 0 3px rgb(250 204 21 / 0.9), 0 0 18px rgb(250 204 21 / 0.8); }
.action-btn--shot.is-charge-3 { box-shadow: 0 0 0 4px rgb(232 121 249 / 0.95), 0 0 24px rgb(232 121 249 / 0.9); animation: charge-pulse 0.35s ease-in-out infinite alternate; }
@keyframes charge-pulse { to { box-shadow: 0 0 0 6px rgb(250 204 21 / 0.95), 0 0 30px rgb(34 211 238 / 0.9); } }

.action-cluster--overlay .action-btn {
  background: rgb(15 23 42 / 0.45);
  backdrop-filter: blur(2px);
}
.action-cluster--overlay .action-btn.is-pressed { background: rgb(131 24 67 / 0.7); }

/* 低い画面（横向きスマホ）ではボタンを少し小さく */
@media (max-height: 430px) {
  .move-pad { width: 8.5rem; height: 4rem; }
  .action-btn--jump, .action-btn--shot { width: 3.75rem; height: 3.75rem; }
  .action-btn--dash { width: 2.75rem; height: 2.75rem; }
  .action-btn--jump { margin-bottom: 1.2rem; }
  .action-cluster { gap: 0.45rem; }
}
</style>

<style>
/* 大画面モード中はページ自体をスクロールさせない（サイト共通ヘッダーの上に重ねる） */
html.erika-game-immersive,
html.erika-game-immersive body {
  overflow: hidden;
  overscroll-behavior: none;
}
</style>
