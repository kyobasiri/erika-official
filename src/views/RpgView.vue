<script setup lang="ts">
import { ref, computed, onMounted, nextTick, onUnmounted } from 'vue'

// --- 型定義 ---
interface Player {
  name: string; className: string; avatarUrl: string;
  hp: number; maxHp: number; mp: number; maxMp: number;
  str: number; mag: number; def: number; spd: number; luk: number;
  skills: string[]; buffs: Record<string, number>;
  animClass: string; popups: any[]; isDefending: boolean; stunTurns: number;
  [key: string]: any;
}

interface Enemy {
  id: string; enemyName: string; imageUrl: string;
  hp: number; maxHp: number; str: number; def: number; spd: number;
  traitName: string; buffs: Record<string, number>;
  isDead: boolean; animClass: string; popups: any[];
  skillUses: number; isCharging: boolean; isDefending: boolean;
}

interface Skill {
  id: string; name: string; description: string; type: string;
  cost_mp?: number; cost_hp_percent?: number; multiplier?: number;
  isPercent?: number; isSureHit?: boolean; ignoreDef?: boolean; hitRate?: number;
  effect_percent?: Record<string, number>; condition?: string; min_floor?: number;
}

interface Song { embed_url?: string; share_url?: string; youtube_id?: string; }
interface Tag { label: string; prompt: string; }

// --- 状態管理 ---
const gameState = ref<'charMake' | 'battle' | 'reward' | 'gameover' | 'gameclear'>('charMake')
const isProcessing = ref(false)
const isGenerating = ref(false)
const isSaving = ref(false)
const isLoading = ref(false)
const logContainer = ref<HTMLElement | null>(null)

const battleState = ref({ floor: 1, enemyCount: 1, turn: 1 })
const showSkillMenu = ref(false)
const targetIndex = ref(0)

const allSkills = ref<Skill[]>([])
const availableSkills = ref<Skill[]>([])
const thePillowsSongs = ref<Song[]>([])
const enemyImagesPool = ref<{name: string, url: string}[]>([])
const currentEnemies = ref<Enemy[]>([])
const battleLogs = ref<{text: string, colorClass: string}[]>([])

// --- キャラメイク関連 ---
const charmakeQuestions = ref<any[]>([])
const currentQuestionIndex = ref(0)
const charMakeSelections = ref({
  classStats: {} as any, className: '', bonusStats: [] as any[], promptFragments: [] as string[]
})
const freeTextInput = ref('')
const charMakeTags = ref<Tag[]>([])
const rewardCategories = ref<Record<string, Record<string, string>>>({})

// --- プレイヤー情報 ---
const player = ref<Player>({
  name: 'あなた', className: '不明', avatarUrl: '/assets/images/icon.png',
  hp: 100, maxHp: 100, mp: 20, maxMp: 20,
  str: 10, mag: 10, def: 10, spd: 10, luk: 10,
  skills: [], buffs: { str: 0, mag: 0, def: 0, spd: 0 },
  animClass: '', popups: [], isDefending: false, stunTurns: 0
})

const skillPoints = ref(0)

// --- 報酬関連 ---
const watchTime = ref(0)
const statPoints = ref(0)
const hasGot30sBonus = ref(false)
const hasGot60sBonus = ref(false)
const rewardGenCount = ref(0)
const isGeneratingReward = ref(false)
const rewardImages = ref<string[]>([])
const selectedTags = ref<Tag[]>([])
const rewardBasePrompt = "masterpiece, best quality, ultra_detailed, absurdres, very aesthetic, delicate lines,"

const statList = [
  { key: 'maxHp', label: '最大HP (+10)' }, { key: 'maxMp', label: '最大MP (+5)' },
  { key: 'str', label: '力 (+1)' }, { key: 'mag', label: '魔力 (+1)' },
  { key: 'def', label: '防御 (+1)' }, { key: 'spd', label: '素早さ (+1)' },
  { key: 'luk', label: '運 (+1)' }
]

let bgmPlayer: any = null
let ytPlayer: any = null
let watchTimer: any = null

// --- ユーティリティ ---
const generateUUID = () => 'xxxx-xxxx-xxxx-xxxx'.replace(/[x]/g, () => (Math.random() * 16 | 0).toString(16))
let userId = localStorage.getItem('erika_rpg_userid')
if (!userId) {
  userId = 'user_' + generateUUID()
  localStorage.setItem('erika_rpg_userid', userId)
}

const playSE = (seName: string) => {
  try {
    const audio = new Audio(`/assets/se/${seName}.mp3`)
    audio.volume = 0.5
    audio.play().catch(() => {})
  } catch (e) {}
}

const addLog = (text: string, type = 'normal') => {
  let colorClass = 'text-zinc-400'
  if (type === 'damage') colorClass = 'text-red-400'
  if (type === 'heal') colorClass = 'text-emerald-400'
  if (type === 'system') colorClass = 'text-erika'

  battleLogs.value.push({ text, colorClass })
  nextTick(() => {
    if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
  })
}

const triggerAnim = (target: any, type: string, text: string) => {
  target.animClass = type === 'damage' ? 'anim-damage anim-shake' : 'anim-heal'
  target.popups.push({ id: Date.now() + Math.random(), text, type })
  setTimeout(() => { target.animClass = '' }, 400)
  setTimeout(() => { target.popups.shift() }, 800)
}

// --- タグ選択（キャラメイク＆クリア報酬） ---
const isCharMakeTagSelected = (label: string) => charMakeTags.value.some(t => t.label === label)
const toggleCharMakeTag = (label: string, prompt: string) => {
  const index = charMakeTags.value.findIndex(t => t.label === label)
  if (index > -1) charMakeTags.value.splice(index, 1)
  else charMakeTags.value.push({ label, prompt })
}

const isTagSelected = (label: string) => selectedTags.value.some(t => t.label === label)
const toggleRewardTag = (label: string, prompt: string) => {
  const index = selectedTags.value.findIndex(t => t.label === label)
  if (index > -1) selectedTags.value.splice(index, 1)
  else selectedTags.value.push({ label, prompt })
}

// --- BGM制御 ---
const initAndPlayBGM = () => {
  if (thePillowsSongs.value.length === 0) return
  const randomSong = thePillowsSongs.value[Math.floor(Math.random() * thePillowsSongs.value.length)]
  let targetVideoId = 'xUboS2Fw1-o'
  if (randomSong.embed_url) targetVideoId = randomSong.embed_url.split('/').pop() || targetVideoId
  else if (randomSong.share_url) targetVideoId = randomSong.share_url.split('/').pop() || targetVideoId

  const loadBGMPlayer = () => {
    // @ts-ignore
    bgmPlayer = new window.YT.Player('battle-bgm-player', {
      videoId: targetVideoId,
      playerVars: { playsinline: 1, loop: 1, playlist: targetVideoId, origin: window.location.origin },
      events: { onReady: (e: any) => { e.target.setVolume(30); e.target.playVideo() } }
    })
  }

  // @ts-ignore
  if (!window.YT) {
    const tag = document.createElement('script')
    tag.src = "https://www.youtube.com/iframe_api"
    document.head.appendChild(tag)
    // @ts-ignore
    window.onYouTubeIframeAPIReady = loadBGMPlayer
  } else {
    if (bgmPlayer && typeof bgmPlayer.destroy === 'function') bgmPlayer.destroy()
    loadBGMPlayer()
  }
}

const stopBGM = () => {
  if (bgmPlayer && typeof bgmPlayer.stopVideo === 'function') bgmPlayer.stopVideo()
}

// --- API連携 (セーブ/ロード) ---
const saveGame = async () => {
  isSaving.value = true
  try {
    const saveData = {
      userId,
      data: { player: player.value, battleState: { floor: battleState.value.floor, enemyCount: battleState.value.enemyCount } }
    }
    const res = await fetch('/api/save', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(saveData)
    })
    if (!res.ok) throw new Error("APIエラー")
    addLog("セーブが完了しました。", "system")
  } catch (e) {
    alert("セーブに失敗しました。")
  } finally {
    isSaving.value = false
  }
}

const loadGame = async () => {
  isLoading.value = true
  try {
    const res = await fetch(`/api/load?userId=${userId}`)
    if (!res.ok) throw new Error("セーブデータが見つかりません。")
    const data = await res.json()
    player.value = data.player
    battleState.value.floor = data.battleState.floor
    battleState.value.enemyCount = data.battleState.enemyCount || 1
    await fetchGallery()
    gameState.value = 'battle'
    startNextWave()
    addLog(`第 ${battleState.value.floor} 階層 (WAVE ${battleState.value.enemyCount}) から探索を再開した！`, 'system')
    initAndPlayBGM()
  } catch (e: any) {
    alert(e.message)
  } finally {
    isLoading.value = false
  }
}

// --- キャラメイク ---
const charMakeCategories = computed(() => {
  const allowedKeys = ['顔・容姿', '髪型', '髪色', '瞳・眼鏡']
  let filtered: any = {}
  for (const key of allowedKeys) {
    if (rewardCategories.value[key]) filtered[key] = rewardCategories.value[key]
  }
  return filtered
})

const selectOption = (option: any) => {
  const qType = charmakeQuestions.value[currentQuestionIndex.value].type
  if (qType === 'class') {
    charMakeSelections.value.classStats = { ...option.stats, initial_skills: option.initial_skills }
    player.value.className = option.class_id
  } else if (qType === 'bonus') {
    charMakeSelections.value.bonusStats.push(option.stats_bonus)
  } else if (qType === 'visual') {
    charMakeSelections.value.promptFragments.push(option.prompt_fragment)
  }
  currentQuestionIndex.value++
}

const submitCharMake = async () => {
  isGenerating.value = true
  try {
    if (!player.value.name.trim()) player.value.name = 'あなた'
    
    let finalStats = { ...charMakeSelections.value.classStats }
    charMakeSelections.value.bonusStats.forEach(bonus => {
      for (let key in bonus) finalStats[key] = (finalStats[key] || 0) + bonus[key]
    })
    Object.assign(player.value, finalStats)
    player.value.hp = player.value.maxHp
    player.value.mp = player.value.maxMp
    player.value.skills = charMakeSelections.value.classStats.initial_skills || []

    const promptFragments = charMakeSelections.value.promptFragments.join(', ')
    const tagPrompts = charMakeTags.value.map(t => t.prompt).join(', ')
    const finalPromptArray = ["A portrait of a RPG character"]
    if (promptFragments) finalPromptArray.push(promptFragments)
    if (tagPrompts) finalPromptArray.push(tagPrompts)
    if (freeTextInput.value) finalPromptArray.push(freeTextInput.value)
    finalPromptArray.push("masterpiece, best quality")

    const res = await fetch('/api/generate-avatar', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: finalPromptArray.join(', ') })
    })
    const data = await res.json().catch(() => ({}))

    if (!res.ok) {
      if (data.error === "NSFW_ERROR" || (data.error && data.error.includes('8007'))) throw new Error("NSFW")
      throw new Error(data.error || "画像生成APIエラー")
    }
    
    player.value.avatarUrl = data.avatarUrl
    await fetchGallery()
    gameState.value = 'battle'
    startNextWave()
    addLog(`「${player.value.className}」の姿で異世界にダイブした！`, 'system')
    initAndPlayBGM()

  } catch (e: any) {
    if (e.message === "NSFW") {
      alert("AIのセーフティフィルターにブロックされました。\n別の要素を選んで再試行してください！")
    } else {
      alert("アバター生成エラーが発生しました。\n" + e.message)
    }
  } finally {
    isGenerating.value = false
  }
}

// --- バトルロジック ---
const fetchGallery = async () => {
  try {
    const res = await fetch(`/assets/gallery.json?t=${new Date().getTime()}`)
    const data = await res.json()
    let images: any[] = []
    data.forEach((folder: any) => {
      folder.images.forEach((img: any) => {
        images.push({ name: img.enemy_name || '暴走したAI エリカ', url: `/assets/images/gallery/${folder.name}/${img.file}` })
      })
    })
    enemyImagesPool.value = images.sort(() => 0.5 - Math.random())
  } catch (e) {}
}

const generateEnemy = (floor: number, type = 'normal'): Enemy => {
  const imgData = enemyImagesPool.value.pop() || { url: '/assets/images/gallery.jpg', name: '深淵のデッドロック エリカ' }
  let baseHp = 60 + (floor - 1) * 35, baseStr = 10 + (floor - 1) * 4, baseDef = 5 + (floor - 1) * 3, baseSpd = 8 + (floor - 1) * 3

  if (type === 'boss') { baseHp *= 1.5; baseStr *= 1.2; baseDef *= 0.9 }
  else if (type === 'midboss') { baseHp *= 0.6; baseStr *= 0.75; baseDef *= 0.8 }

  const traits = [
    { id: 'all_rounder', name: 'エース', mult: { hp: 1.2, str: 1.2, def: 1.2, spd: 1.2 } },
    { id: 'fighter', name: 'ファイター', mult: { hp: 1.4, str: 1.3, def: 0.5, spd: 1.0 } },
    { id: 'iron_soldier', name: '鋼鉄兵', mult: { hp: 1.0, str: 1.0, def: 1.9, spd: 0.5 } },
    { id: 'berserker', name: 'ベルセルク', mult: { hp: 0.5, str: 1.9, def: 0.7, spd: 1.0 } },
    { id: 'thief', name: 'シーフ', mult: { hp: 1.0, str: 0.6, def: 1.0, spd: 2.1 } }
  ]
  const trait = traits[Math.floor(Math.random() * traits.length)]

  return {
    id: Math.random().toString(36).substring(7),
    enemyName: imgData.name, imageUrl: imgData.url,
    maxHp: Math.floor(baseHp * trait.mult.hp), hp: Math.floor(baseHp * trait.mult.hp),
    str: Math.floor(baseStr * trait.mult.str), def: Math.floor(baseDef * trait.mult.def), spd: Math.floor(baseSpd * trait.mult.spd),
    traitName: trait.name, buffs: { str: 0, mag: 0, def: 0, spd: 0 },
    isDead: false, animClass: '', popups: [], skillUses: 3, isCharging: false, isDefending: false
  }
}

const startNextWave = () => {
  battleState.value.turn = 1
  battleLogs.value = []
  availableSkills.value = allSkills.value.filter(s => player.value.skills.includes(s.id))

  if (battleState.value.enemyCount === 5) {
    currentEnemies.value = [generateEnemy(battleState.value.floor, 'boss'), generateEnemy(battleState.value.floor, 'boss')]
    targetIndex.value = 0
    addLog(`強大な反応... 2体のボスがあらわれた！！`, 'system')
    playSE('boss_appear')
  } else if (battleState.value.enemyCount === 3) {
    currentEnemies.value = [generateEnemy(battleState.value.floor, 'midboss'), generateEnemy(battleState.value.floor, 'midboss')]
    targetIndex.value = 0
    addLog(`周囲の空気が変わった... 中ボスが2体あらわれた！`, 'system')
    playSE('enemy_appear')
  } else {
    currentEnemies.value = [generateEnemy(battleState.value.floor, 'normal')]
    targetIndex.value = 0
    addLog(`${currentEnemies.value[0].enemyName} があらわれた！`, 'system')
    playSE('enemy_appear')
  }
}

const getStat = (actor: any, statName: string) => Math.max(1, Math.floor((actor[statName] || 0) * (1 + (actor.buffs[statName] || 0) / 100)))

const performAction = (attacker: any, defender: any, action: string | Skill, isAoE = false) => {
  if (attacker.hp <= 0) return

  if (action === 'defend') {
    if (!isAoE) addLog(`${attacker.name || attacker.enemyName} は身を守っている。`)
    if (attacker.mp !== undefined) {
      const recoverMp = Math.max(5, Math.floor(attacker.maxMp * 0.2))
      attacker.mp = Math.min(attacker.maxMp, attacker.mp + recoverMp)
      addLog(`MPが ${recoverMp} 回復した！`, 'heal')
    }
    return
  }

  if (typeof action === 'object') {
    const skill = action
    if (skill.hitRate && Math.random() * 100 > skill.hitRate) {
      addLog(`${attacker.name || attacker.enemyName} の ${skill.name} は外れた！`)
      return
    }
    if (!isAoE) {
      addLog(`${attacker.name || attacker.enemyName} の ${skill.name}！`)
      if (skill.cost_mp) attacker.mp -= skill.cost_mp
      if (skill.cost_hp_percent) attacker.hp -= Math.floor(attacker.maxHp * (skill.cost_hp_percent / 100))
    }

    playSE(skill.type === 'attack_magic' || skill.type === 'ultimate' || skill.type === 'heal' || skill.type === 'buff' ? 'skill_magic' : 'skill_phys')

    if (skill.type === 'heal') {
      if (isAoE && defender !== attacker) return
      const amount = Math.floor(attacker.maxHp * ((skill.multiplier || 0.5)))
      attacker.hp = Math.min(attacker.maxHp, attacker.hp + amount)
      addLog(`${attacker.name || attacker.enemyName} のHPが ${amount} 回復した！`, 'heal')
      triggerAnim(attacker, 'heal', `+${amount}`)
      return
    }

    if (skill.type === 'buff' || skill.type === 'debuff') {
      const target = skill.type === 'buff' ? attacker : defender
      if (skill.effect_percent) {
        for (const [stat, val] of Object.entries(skill.effect_percent)) {
          target.buffs[stat] = Math.min(40, Math.max(-40, (target.buffs[stat] || 0) + val))
        }
      }
      addLog(`${target.name || target.enemyName} のステータスが変化した！`, 'system')
      triggerAnim(target, 'heal', 'UP/DOWN')
      return
    }

    const isMagical = skill.type === 'attack_magic' || skill.type === 'ultimate'
    if (!skill.isSureHit && !isMagical) {
      const evadeRate = Math.min(40, Math.max(0, (getStat(defender, 'spd') - getStat(attacker, 'spd')) * 2))
      if (Math.random() * 100 < evadeRate) {
        addLog(`${defender.name || defender.enemyName} は攻撃をかわした！`)
        return
      }
    }

    let dmg = 0
    if (skill.isPercent) {
      dmg = Math.max(1, Math.floor(defender.hp * (skill.isPercent / 100)))
    } else {
      const atkStat = isMagical ? getStat(attacker, 'mag') : getStat(attacker, 'str')
      const defStat = (skill.type === 'ultimate' || skill.ignoreDef || isMagical) ? 0 : getStat(defender, 'def')
      dmg = Math.max(1, (atkStat - defStat * 0.5)) * (skill.multiplier || 1.0)
    }

    if (defender.isDefending) dmg *= 0.5
    const finalDamage = Math.max(1, Math.floor(dmg * (0.95 + Math.random() * 0.1)))
    addLog(`${defender.name || defender.enemyName} に ${finalDamage} のダメージ！`, 'damage')
    defender.hp = Math.max(0, defender.hp - finalDamage)
    triggerAnim(defender, 'damage', finalDamage.toString())
    playSE('damage')
    return
  }

  // 通常攻撃
  addLog(`${attacker.name || attacker.enemyName} の攻撃！`)
  playSE('attack')
  const evadeRate = Math.min(40, Math.max(0, (getStat(defender, 'spd') - getStat(attacker, 'spd')) * 2))
  if (Math.random() * 100 < evadeRate) {
    addLog(`${defender.name || defender.enemyName} は攻撃をかわした！`)
    return
  }
  const isCrit = (Math.random() * 100) < (5 + (attacker.luk || 0) * 0.5)
  if (isCrit) addLog('会心の一撃！！', 'damage')
  
  let dmg = getStat(attacker, 'str')
  if (!isCrit) dmg -= (getStat(defender, 'def') * 0.5)
  else dmg *= 1.5
  if (defender.isDefending) dmg *= 0.5

  const finalDamage = Math.max(1, Math.floor(dmg * (0.95 + Math.random() * 0.1)))
  addLog(`${defender.name || defender.enemyName} に ${finalDamage} のダメージ！`, 'damage')
  defender.hp = Math.max(0, defender.hp - finalDamage)
  triggerAnim(defender, 'damage', finalDamage.toString())
  playSE('damage')
}

const executeAction = (playerAction: string | Skill) => {
  isProcessing.value = true
  addLog(`\n【ターン ${battleState.value.turn}】`)

  const processEnemiesAndEndTurn = () => {
    setTimeout(() => {
      currentEnemies.value.forEach(enemy => { if (!enemy.isDead) processEnemyTurn(enemy, currentEnemies.value) })
      
      setTimeout(() => {
        let isAnyEnemyDefeated = false
        currentEnemies.value.forEach(e => { if (e.hp <= 0 && !e.isDead) { e.isDead = true; isAnyEnemyDefeated = true; } })
        if (isAnyEnemyDefeated) playSE('defeat')

        if (currentEnemies.value.every(e => e.isDead)) {
          addLog(`敵を撃破した！`, 'system')
          if (battleState.value.floor >= 10 && battleState.value.enemyCount >= 5) {
            addLog(`【討伐完了】全てのエリカを鎮めた...！`, 'system')
            playSE('floor_clear')
            setTimeout(() => stopBGM(), 3000)
            setTimeout(() => { gameState.value = 'gameclear'; isProcessing.value = false }, 3000)
          } else if (battleState.value.enemyCount < 5) {
            playSE('wave_clear')
            battleState.value.enemyCount++
            setTimeout(() => { startNextWave(); isProcessing.value = false }, 1500)
          } else {
            addLog(`階層クリア！！`, 'system')
            playSE('floor_clear')
            setTimeout(() => { enterRewardRoom(); isProcessing.value = false }, 1500)
          }
        } else if (player.value.hp <= 0) {
          addLog(`力尽きた...`, 'system')
          stopBGM()
          gameState.value = 'gameover'
          isProcessing.value = false
        } else {
          battleState.value.turn++
          isProcessing.value = false
        }
      }, 1000)
    }, 1000)
  }

  if (player.value.stunTurns > 0) {
    addLog(`${player.value.name} は転んでいて動けない！！`, 'damage')
    player.value.stunTurns--
    player.value.isDefending = false
    processEnemiesAndEndTurn()
    return
  }

  player.value.isDefending = playerAction === 'defend'
  
  if (typeof playerAction === 'object' && playerAction.target === 'all') {
    addLog(`${player.value.name} の ${playerAction.name}！`)
    if (playerAction.cost_mp) player.value.mp -= playerAction.cost_mp
    if (playerAction.cost_hp_percent) player.value.hp -= Math.floor(player.value.maxHp * (playerAction.cost_hp_percent / 100))
    currentEnemies.value.forEach(enemy => { if (!enemy.isDead) performAction(player.value, enemy, playerAction, true) })
  } else {
    let tIdx = targetIndex.value
    if (currentEnemies.value[tIdx].isDead) tIdx = currentEnemies.value.findIndex(e => !e.isDead)
    performAction(player.value, currentEnemies.value[tIdx], playerAction, false)
  }
  processEnemiesAndEndTurn()
}

const processEnemyTurn = (enemy: Enemy, allEnemies: Enemy[]) => {
  if (enemy.hp <= 0 || enemy.isDead) return
  let hasSkill = enemy.skillUses > 0
  let rand = Math.floor(Math.random() * 100)

  if (enemy.isCharging) {
    enemy.isCharging = false
    performAction(enemy, player.value, { id: 't', name: '痛恨の一撃！！', description: '', type: 'attack_physical', multiplier: 1.6 })
    return
  }

  if (!hasSkill) { performAction(enemy, player.value, rand < 80 ? 'attack' : 'defend'); return }

  if (enemy.traitName === 'エース') {
    if (rand < 50) {
      let target = enemy
      let hurtAlly = allEnemies.find(e => e !== enemy && !e.isDead && e.hp < e.maxHp * 0.5)
      if (hurtAlly) target = hurtAlly
      addLog(`${enemy.enemyName} の エリカヒール！！`)
      let healAmount = Math.floor(target.maxHp * 0.3)
      target.hp = Math.min(target.maxHp, target.hp + healAmount)
      addLog(`${target.enemyName} のHPが ${healAmount} 回復した！`, 'heal')
      triggerAnim(target, 'heal', `+${healAmount}`)
      playSE('skill_magic')
      enemy.skillUses--
    } else if (rand < 80) {
      performAction(enemy, player.value, { id: 's', name: 'エリカスペシャル！！', description: '', type: 'attack_magic', isPercent: 20 })
      enemy.skillUses--
    } else performAction(enemy, player.value, 'attack')
  } else if (enemy.traitName === 'ファイター') {
    if (rand < 30) {
      addLog(`${enemy.enemyName} は 力をためている！！`, 'system')
      enemy.isCharging = true; enemy.skillUses--
    } else if (rand < 60) {
      let cost = Math.floor(enemy.maxHp * 0.3)
      if (enemy.hp > cost) {
        addLog(`${enemy.enemyName} の エリカハンマー！！`)
        enemy.hp -= cost; triggerAnim(enemy, 'damage', `-${cost}`)
        performAction(enemy, player.value, { id:'h', name: 'エリカハンマー！！', description:'', type: 'attack_physical', multiplier: 1.5 })
        enemy.skillUses--
      } else performAction(enemy, player.value, 'attack')
    } else if (rand < 80) {
      addLog(`${enemy.enemyName} は 自身の攻撃力を上げた！！`, 'system')
      enemy.buffs.str += 20; triggerAnim(enemy, 'heal', 'ATK UP'); enemy.skillUses--
    } else performAction(enemy, player.value, 'attack')
  } else {
    performAction(enemy, player.value, 'attack') // 簡易化
  }
}

// --- 報酬部屋とクリア特典の画像生成 ---
const enterRewardRoom = () => {
  stopBGM()
  gameState.value = 'reward'
  watchTime.value = 0; hasGot30sBonus.value = false; hasGot60sBonus.value = false
  player.value.hp = player.value.maxHp; player.value.mp = player.value.maxMp
  statPoints.value += 5
  nextTick(initYouTubePlayer)
}

const initYouTubePlayer = () => {
  const randomSong = thePillowsSongs.value[Math.floor(Math.random() * thePillowsSongs.value.length)]
  let targetVideoId = 'xUboS2Fw1-o'
  if (randomSong.embed_url) targetVideoId = randomSong.embed_url.split('/').pop() || targetVideoId
  else if (randomSong.share_url) targetVideoId = randomSong.share_url.split('/').pop() || targetVideoId

  const loadPlayer = () => {
    // @ts-ignore
    ytPlayer = new window.YT.Player('youtube-player', {
      videoId: targetVideoId, playerVars: { playsinline: 1, origin: window.location.origin },
      events: { onStateChange: (e: any) => {
        if (e.data === 1) { // PLAYING
          if (!watchTimer) watchTimer = setInterval(() => { watchTime.value++; checkBonuses() }, 1000)
        } else { clearInterval(watchTimer); watchTimer = null }
      }}
    })
  }

  // @ts-ignore
  if (!window.YT) {
    const tag = document.createElement('script'); tag.src = "https://www.youtube.com/iframe_api"
    document.head.appendChild(tag)
    // @ts-ignore
    window.onYouTubeIframeAPIReady = loadPlayer
  } else loadPlayer()
}

const checkBonuses = () => {
  if (watchTime.value >= 30 && !hasGot30sBonus.value) {
    hasGot30sBonus.value = true; skillPoints.value += 1; statPoints.value += 8
    alert(`30秒視聴達成！\nスキル習得権 ＋1\nステータスポイント ＋8pt`)
  }
  if (watchTime.value >= 60 && !hasGot60sBonus.value) {
    hasGot60sBonus.value = true; skillPoints.value += 1; statPoints.value += 15
    alert(`60秒視聴達成（特大ボーナス）！\nスキル習得権 ＋1\nステータスポイント ＋15pt`)
  }
}

const allocateStat = (key: string) => {
  if (statPoints.value > 0) {
    if (key === 'maxHp') { player.value.maxHp += 10; player.value.hp += 10 }
    else if (key === 'maxMp') { player.value.maxMp += 5; player.value.mp += 5 }
    else player.value[key] += 1
    statPoints.value--
  }
}

const unlearnedSkills = computed(() => allSkills.value.filter(s => !player.value.skills.includes(s.id) && (!s.min_floor || s.min_floor <= battleState.value.floor)))
const learnSelectedSkill = (skill: Skill) => {
  if (skillPoints.value > 0) {
    player.value.skills.push(skill.id); skillPoints.value--
    availableSkills.value = allSkills.value.filter(s => player.value.skills.includes(s.id))
    alert(`特技「${skill.name}」を習得しました！`)
  }
}

const goToNextFloor = () => {
  if (ytPlayer && typeof ytPlayer.destroy === 'function') ytPlayer.destroy()
  clearInterval(watchTimer); watchTimer = null
  battleState.value.floor++; battleState.value.enemyCount = 1
  gameState.value = 'battle'; startNextWave(); initAndPlayBGM()
}

const restartFloor = () => {
  player.value.hp = player.value.maxHp; player.value.mp = player.value.maxMp; player.value.buffs = { str: 0, mag: 0, def: 0, spd: 0 }
  battleState.value.enemyCount = 1; gameState.value = 'battle'
  startNextWave(); addLog(`第 ${battleState.value.floor} 階層の最初からやり直す！`, 'system'); initAndPlayBGM()
}

const resetGame = () => {
  localStorage.removeItem('erika_rpg_save_' + userId)
  location.reload()
}

// --- クリア後の画像生成（NSFW対応） ---
const generateRewardImage = async () => {
  if (rewardGenCount.value >= 2) return
  isGeneratingReward.value = true

  const promptsOnly = selectedTags.value.map(t => t.prompt)
  const finalPrompt = [rewardBasePrompt, ...promptsOnly].join(', ')

  try {
    const res = await fetch('/api/generate-avatar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: finalPrompt })
    })
    
    const data = await res.json().catch(() => ({}))

    if (!res.ok) {
      if (data.error === "NSFW_ERROR" || (data.error && data.error.includes('8007'))) {
        throw new Error("NSFW")
      }
      throw new Error(data.error || "画像生成に失敗しました")
    }

    rewardImages.value.unshift(data.avatarUrl)
    rewardGenCount.value++
  } catch (e: any) {
    if (e.message === "NSFW") {
      alert("AIのセーフティフィルターにブロックされてしまいました。\n（健全な単語でも組み合わせによって誤判定されることがあります）\nお手数ですが、別の要素を選んで再試行してください！")
    } else {
      alert("画像の生成に失敗しました。\n詳細: " + e.message)
    }
  } finally {
    isGeneratingReward.value = false
  }
}

onMounted(async () => {
  try { const res = await fetch('/assets/skills.json'); allSkills.value = await res.json() } catch(e){}
  try { const res = await fetch('/assets/thepillows_releases_tab.json'); thePillowsSongs.value = await res.json() } catch(e){}
  try { const res = await fetch('/assets/rpgclear.json'); rewardCategories.value = await res.json() } catch(e){}
  try {
    const res = await fetch('/assets/charmake.json?t=' + new Date().getTime())
    charmakeQuestions.value = (await res.json()).questions
  } catch(e) {}
})

onUnmounted(() => { stopBGM(); if (bgmPlayer && bgmPlayer.destroy) bgmPlayer.destroy(); if (ytPlayer && ytPlayer.destroy) ytPlayer.destroy() })
</script>

<template>
  <div class="bg-zinc-950 min-h-screen pt-20 pb-12">
    <!-- ナビゲーション -->
    <nav class="max-w-2xl mx-auto px-4 flex justify-between items-center mb-6">
      <router-link to="/" class="text-erika font-bold text-sm hover:underline">← Back to Top</router-link>
      <button v-if="gameState === 'reward' || gameState === 'battle'" 
              @click="saveGame" :disabled="isSaving"
              class="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-full shadow-[0_0_15px_rgba(37,99,235,0.5)] hover:bg-blue-500 disabled:opacity-50">
        {{ isSaving ? '保存中...' : '💾 セーブ' }}
      </button>
    </nav>

    <!-- 隠しオーディオ -->
    <div id="battle-bgm-player" class="absolute -top-[9999px] -left-[9999px] w-[1px] h-[1px]"></div>

    <div class="container mx-auto px-4 max-w-xl">
      
      <!-- 1. キャラメイク画面 -->
      <div v-if="gameState === 'charMake'" class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-6 text-center">
        <h2 class="text-xl font-bold text-white mb-6">ダイブ設定（キャラクター作成）</h2>

        <div v-if="!isGenerating">
          <div v-if="currentQuestionIndex === 0" class="mb-8 border-b border-white/10 pb-8">
            <button @click="loadGame" :disabled="isLoading" class="w-full py-3 bg-transparent border border-blue-500 text-blue-400 font-bold rounded-lg hover:bg-blue-500 hover:text-white transition-colors">
              {{ isLoading ? 'ロード中...' : '💾 続きから遊ぶ (ロード)' }}
            </button>
          </div>

          <div v-if="currentQuestionIndex < charmakeQuestions.length">
            <p class="text-lg text-white font-bold mb-6">{{ charmakeQuestions[currentQuestionIndex].text }}</p>
            <div class="space-y-3">
              <button v-for="(option, idx) in charmakeQuestions[currentQuestionIndex].options" :key="idx"
                      @click="selectOption(option)"
                      class="w-full text-left p-4 bg-zinc-900 border border-zinc-700 rounded-xl hover:border-erika transition-colors">
                <strong class="text-white block">{{ option.label }}</strong>
                <p class="text-xs text-zinc-400 mt-1" v-if="option.description">{{ option.description }}</p>
              </button>
            </div>
          </div>

          <div v-else>
            <div class="mb-6 text-left">
              <label class="block text-sm font-bold text-white mb-2">あなたの名前を教えてください。</label>
              <input type="text" v-model="player.name" placeholder="名前を入力（未入力なら「あなた」）"
                     class="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-erika">
            </div>
            <button @click="submitCharMake" class="w-full py-4 bg-erika text-black font-black text-lg rounded-full shadow-[0_0_20px_rgba(243,156,18,0.3)] hover:bg-erika-light hover:-translate-y-1 transition-all">
              アバターを生成してダイブする
            </button>
          </div>
        </div>
        
        <div v-else class="py-12">
          <p class="text-erika font-bold mb-4 animate-pulse">アバターを生成中...</p>
          <div class="w-full bg-zinc-800 rounded-full h-2 overflow-hidden"><div class="bg-erika h-full w-full origin-left animate-[pulse_1s_infinite]"></div></div>
        </div>
      </div>

      <!-- 2. バトル画面 -->
      <div v-if="gameState === 'battle'">
        <div class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-4 mb-4 text-center">
          <p class="text-xs text-zinc-400 mb-4 border-b border-zinc-800 pb-2">
            第 {{ battleState.floor }} 階層 - 
            <span v-if="battleState.enemyCount === 5" class="text-red-500 font-bold">WAVE 5 (BOSS)</span>
            <span v-else>WAVE {{ battleState.enemyCount }} / 5</span>
          </p>
          
          <div class="flex justify-center gap-4">
            <div v-for="(enemy, index) in currentEnemies" :key="enemy.id" v-show="!enemy.isDead"
                 @click="targetIndex = index"
                 class="relative p-2 rounded-xl transition-all cursor-pointer"
                 :class="targetIndex === index ? 'ring-2 ring-erika shadow-[0_0_15px_rgba(243,156,18,0.5)]' : ''">
              
              <div v-for="popup in enemy.popups" :key="popup.id" class="popup-text" :class="{'text-emerald-400': popup.type === 'heal', 'text-red-500': popup.type === 'damage'}">
                {{ popup.text }}
              </div>
              
              <p class="text-red-500 font-bold text-[10px] mb-1">【特性】{{ enemy.traitName }}</p>
              <img :src="enemy.imageUrl" :class="enemy.animClass" class="w-32 h-32 object-cover rounded-lg border-2 border-zinc-700 mx-auto mb-2">
              <p class="text-xs text-white font-bold mb-1 truncate w-32">{{ enemy.enemyName }}</p>
              <div class="w-full bg-zinc-800 rounded-full h-1.5"><div class="bg-red-500 h-full rounded-full transition-all" :style="{ width: (enemy.hp/enemy.maxHp*100)+'%' }"></div></div>
            </div>
          </div>
        </div>

        <div class="bg-black/80 border border-zinc-700 rounded-xl p-4 mb-4">
          <div class="h-32 overflow-y-auto scroll-smooth text-xs space-y-1 custom-scrollbar" ref="logContainer">
            <p v-for="(log, index) in battleLogs" :key="index" :class="[log.colorClass, index === battleLogs.length - 1 ? 'font-bold text-sm border-l-2 border-erika pl-2 bg-erika/10 py-1' : 'opacity-70']">
              {{ log.text }}
            </p>
          </div>
        </div>

        <div class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-4 mb-4 flex items-center gap-4">
          <div class="relative shrink-0 w-20 h-20">
            <div v-for="popup in player.popups" :key="popup.id" class="popup-text" :class="{'text-emerald-400': popup.type === 'heal', 'text-red-500': popup.type === 'damage'}">{{ popup.text }}</div>
            <img :src="player.avatarUrl" :class="player.animClass" class="w-full h-full object-cover rounded-full border-2 border-erika shadow-[0_0_10px_rgba(243,156,18,0.4)]">
          </div>
          <div class="flex-grow">
            <div class="flex justify-between text-xs font-bold text-white mb-1"><span>{{ player.name }} ({{ player.className }})</span><span>HP {{ player.hp }}/{{ player.maxHp }}</span></div>
            <div class="w-full bg-zinc-800 rounded-full h-1.5 mb-3"><div class="bg-emerald-500 h-full rounded-full transition-all" :style="{ width: (player.hp/player.maxHp*100)+'%' }"></div></div>
            <div class="flex justify-between text-xs font-bold text-blue-400 mb-1"><span>MP</span><span>{{ player.mp }}/{{ player.maxMp }}</span></div>
            <div class="w-full bg-zinc-800 rounded-full h-1.5"><div class="bg-blue-500 h-full rounded-full transition-all" :style="{ width: (player.mp/player.maxMp*100)+'%' }"></div></div>
          </div>
        </div>

        <div v-if="!showSkillMenu" class="grid grid-cols-2 gap-2">
          <button @click="executeAction('attack')" :disabled="isProcessing" class="py-3 bg-red-600/80 text-white font-bold rounded-lg hover:bg-red-500 disabled:opacity-50">物理攻撃</button>
          <button @click="showSkillMenu = true" :disabled="isProcessing" class="py-3 bg-emerald-600/80 text-white font-bold rounded-lg hover:bg-emerald-500 disabled:opacity-50">特技・魔法</button>
          <button @click="executeAction('defend')" :disabled="isProcessing" class="col-span-2 py-3 bg-zinc-800 border border-zinc-600 text-zinc-300 font-bold rounded-lg hover:bg-zinc-700 disabled:opacity-50">防御 (MP回復)</button>
        </div>

        <div v-else class="space-y-2">
          <button @click="showSkillMenu = false" class="w-full py-2 bg-transparent border border-zinc-600 text-zinc-400 rounded-lg hover:bg-zinc-800 mb-2 text-sm">戻る</button>
          <button v-for="skill in availableSkills" :key="skill.id" @click="() => { showSkillMenu=false; executeAction(skill) }" class="w-full text-left p-3 bg-blue-900/40 border border-blue-500/50 rounded-lg hover:bg-blue-800/60 transition-colors">
            <div class="flex justify-between font-bold text-blue-300"><span>{{ skill.name }}</span><span class="text-xs">MP: {{ skill.cost_mp || 0 }}</span></div>
            <p class="text-xs text-blue-200/70 mt-1">{{ skill.description }}</p>
          </button>
        </div>
      </div>

      <!-- 3. セーフエリア (Reward) -->
      <div v-if="gameState === 'reward'" class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-6 text-center">
        <h2 class="text-2xl font-black text-erika mb-6">第 {{ battleState.floor - 1 }} 階層 クリア！</h2>
        
        <div class="relative pb-[56.25%] h-0 rounded-xl overflow-hidden border border-zinc-700 mb-6">
          <div id="youtube-player" class="absolute top-0 left-0 w-full h-full"></div>
        </div>

        <div class="bg-erika/10 border border-erika rounded-xl p-4 mb-6">
          <p class="text-erika font-bold mb-2">🎵 視聴ボーナス: {{ watchTime }} 秒</p>
          <div class="w-full bg-zinc-900 rounded-full h-2 mb-4"><div class="bg-erika h-full rounded-full transition-all duration-1000" :style="{ width: Math.min(watchTime/60*100, 100)+'%' }"></div></div>
          <p v-if="watchTime < 30" class="text-xs text-blue-400">あと {{ 30 - watchTime }} 秒でスキル権＋ステータスpt獲得！</p>
          <p v-else-if="watchTime < 60" class="text-xs text-red-400">あと {{ 60 - watchTime }} 秒で特大ボーナス！</p>
          <p v-else class="text-xs text-emerald-400 font-bold">最大ボーナス獲得済み！</p>
        </div>

        <div class="bg-zinc-900 rounded-xl p-4 mb-4 text-left">
          <p class="text-white text-sm font-bold mb-3">残りポイント: <span class="text-erika text-lg">{{ statPoints }}</span></p>
          <div class="grid grid-cols-2 gap-2">
            <div v-for="stat in statList" :key="stat.key" class="flex justify-between items-center bg-white/5 p-2 rounded border border-white/5">
              <div><p class="text-[10px] text-zinc-400">{{ stat.label }}</p><p class="text-sm text-white font-bold">{{ player[stat.key] }}</p></div>
              <button @click="allocateStat(stat.key)" :disabled="statPoints <= 0" class="w-6 h-6 rounded-full bg-emerald-500 text-black font-black text-xs disabled:opacity-30">+</button>
            </div>
          </div>
        </div>

        <div class="bg-zinc-900 rounded-xl p-4 mb-8 text-left">
          <p class="text-white text-sm font-bold mb-3">スキル習得権: <span class="text-blue-400 text-lg">{{ skillPoints }}</span></p>
          <div v-for="skill in unlearnedSkills" :key="skill.id" class="flex justify-between items-center bg-white/5 p-3 rounded mb-2 border border-white/5">
            <div><p class="text-sm text-white font-bold">{{ skill.name }}</p><p class="text-[10px] text-zinc-400">{{ skill.description }}</p></div>
            <button @click="learnSelectedSkill(skill)" :disabled="skillPoints <= 0" class="px-3 py-1 bg-blue-500 text-white text-xs font-bold rounded disabled:opacity-30">習得</button>
          </div>
        </div>

        <button @click="goToNextFloor" class="w-full py-4 bg-red-600 text-white font-black text-lg rounded-full shadow-lg hover:bg-red-500 transition-colors">
          次の階層へ進む
        </button>
      </div>

      <!-- 4. GameOver -->
      <div v-if="gameState === 'gameover'" class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center">
        <h2 class="text-4xl font-black mb-4 text-red-500">GAME OVER</h2>
        <p class="text-zinc-400 mb-6">力尽きてしまいました…。<br>ペナルティなしで現在の階層の最初からリトライできます。</p>
        <button @click="restartFloor" class="w-full py-4 bg-red-600 text-white font-bold rounded-full hover:bg-red-500 transition-colors shadow-lg">現在の階層からリトライ</button>
      </div>

      <!-- 5. Game Clear (完全復元版) -->
      <div v-if="gameState === 'gameclear'" class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center">
        <h2 class="text-4xl font-black mb-4 text-erika drop-shadow-[0_0_15px_rgba(243,156,18,0.8)]">CONGRATULATIONS!</h2>
        <p class="text-lg text-white font-bold mb-8">見事10階層を突破し、エリカを討伐しました！</p>

        <!-- 画像生成報酬エリア -->
        <div class="bg-black/60 backdrop-blur-md border-2 border-erika rounded-2xl p-6 md:p-8 text-left shadow-[0_0_30px_rgba(243,156,18,0.2)] mb-8">
          <h3 class="text-2xl font-black text-erika text-center mb-2">🎁 クリア特典：エリカの記憶を具現化する</h3>
          <p class="text-sm text-zinc-400 text-center mb-6">
            Cloudflare Workers AI (Flux) の力を使って、あなただけのエリカの姿を生成できます。<br>
            <strong class="text-erika">※生成できるのは2回までです。</strong>
          </p>

          <div v-if="rewardGenCount < 2">
            <!-- 選択タグエリア -->
            <div class="bg-black/50 border border-dashed border-erika rounded-xl p-4 min-h-[80px] mb-6">
              <p class="text-xs text-zinc-500 font-bold mb-3">【組み込まれるプロンプト（クリックで解除）】</p>
              <div class="flex flex-wrap gap-2">
                <span v-for="tag in selectedTags" :key="tag.label" 
                      @click="toggleRewardTag(tag.label, tag.prompt)"
                      class="px-3 py-1 bg-erika text-zinc-900 font-bold text-sm rounded-full cursor-pointer hover:bg-erika-light transition-colors flex items-center gap-1 shadow-md">
                  {{ tag.label }}
                  <span class="text-zinc-800 hover:text-black font-black leading-none ml-1">&times;</span>
                </span>
                <p v-if="selectedTags.length === 0" class="text-sm text-zinc-600">下のリストから要素を選んでください。</p>
              </div>
            </div>

            <!-- タグリスト -->
            <div class="max-h-64 overflow-y-auto pr-2 border-t border-white/10 pt-6 mb-8 custom-scrollbar">
              <div v-for="(prompts, category) in rewardCategories" :key="category" class="mb-6">
                <p class="font-bold text-erika mb-3">{{ category }}</p>
                <div class="flex flex-wrap gap-2">
                  <button v-for="(prompt, label) in prompts" :key="label"
                          @click="toggleRewardTag(label, prompt)"
                          class="px-3 py-1.5 border rounded-full text-sm transition-colors"
                          :class="isTagSelected(label) ? 'hidden' : 'border-zinc-700 text-zinc-400 hover:bg-white/10 hover:text-white'">
                    {{ label }}
                  </button>
                </div>
              </div>
            </div>

            <div class="text-center">
              <button @click="generateRewardImage" :disabled="isGeneratingReward || selectedTags.length === 0"
                      class="px-8 py-4 bg-erika text-black font-black rounded-full shadow-[0_4px_15px_rgba(243,156,18,0.4)] hover:bg-erika-light disabled:opacity-50 disabled:cursor-not-allowed transition-all">
                {{ isGeneratingReward ? '具現化中...' : `画像を生成する (残り ${2 - rewardGenCount} 回)` }}
              </button>
            </div>
            <div v-if="isGeneratingReward" class="w-full bg-zinc-800 rounded-full h-2 mt-4 overflow-hidden">
              <div class="bg-erika h-full w-full origin-left animate-[pulse_1s_infinite]"></div>
            </div>
          </div>
          <div v-else class="text-center py-6">
            <p class="text-red-500 font-bold">規定の生成回数（2回）に達しました。</p>
          </div>

          <!-- 生成結果 -->
          <div v-if="rewardImages.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-8">
            <div v-for="(img, idx) in rewardImages" :key="idx" class="text-center">
              <img :src="img" class="w-full aspect-square object-cover rounded-xl border-2 border-erika shadow-[0_0_15px_rgba(243,156,18,0.4)] mb-3">
              <a :href="img" target="_blank" class="block w-full py-2 bg-zinc-800 text-white text-sm font-bold rounded-lg hover:bg-zinc-700 transition-colors">
                拡大して保存
              </a>
            </div>
          </div>
        </div>

        <button @click="resetGame" class="w-full py-4 bg-zinc-800 text-white font-bold rounded-full mt-2 border border-zinc-600 hover:bg-zinc-700 transition-colors">
          最初からダイブし直す
        </button>
      </div>

    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 2px; }

.anim-damage { animation: shake 0.4s cubic-bezier(.36,.07,.19,.97) both; filter: brightness(2) sepia(1) hue-rotate(-50deg) saturate(5); }
.anim-heal { filter: brightness(1.5) drop-shadow(0 0 10px #2ecc71); transition: filter 0.4s; }

@keyframes shake {
  10%, 90% { transform: translate3d(-2px, 0, 0); }
  20%, 80% { transform: translate3d(3px, 0, 0); }
  30%, 50%, 70% { transform: translate3d(-5px, 0, 0); }
  40%, 60% { transform: translate3d(5px, 0, 0); }
}

.popup-text {
  position: absolute; top: 10px; left: 50%; transform: translateX(-50%);
  font-weight: 900; font-size: 1.5rem; text-shadow: 0 0 5px #000;
  animation: floatUp 0.8s ease-out forwards; z-index: 10; pointer-events: none;
}
@keyframes floatUp {
  0% { opacity: 1; transform: translate(-50%, 0) scale(1); }
  100% { opacity: 0; transform: translate(-50%, -30px) scale(1.2); }
}
</style>