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
  target?: string; // TS2339 エラー解消用に追加
}

interface Song { title: string; artist?: string; embed_url?: string; share_url?: string; youtube_id?: string; }
interface HeardSong extends Song { seconds: number; firstFloor: number }
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
const equippedSkillIds = ref<string[]>([])
const availableSkills = computed(() => equippedSkillIds.value.map(id => allSkills.value.find(s => s.id === id)).filter((s): s is Skill => !!s))
const learnedSkills = computed(() => allSkills.value.filter(s => player.value.skills.includes(s.id)))
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
const activeCutin = ref<{ img: string, text: string, color: string } | null>(null)

const statList = [
  { key: 'maxHp', label: '最大HP (+10)' }, { key: 'maxMp', label: '最大MP (+5)' },
  { key: 'str', label: '力 (+1)' }, { key: 'mag', label: '魔力 (+1)' },
  { key: 'def', label: '防御 (+1)' }, { key: 'spd', label: '素早さ (+1)' },
  { key: 'luk', label: '運 (+1)' }
]

let disposed = false
let turnToken = 0
let musicToken = 0
let cutinToken = 0
const timers = new Set<ReturnType<typeof setTimeout>>()
const pendingWaits = new Map<ReturnType<typeof setTimeout>, () => void>()
let ytPlayer: any = null
let watchTimer: any = null

function schedule(callback: () => void, ms: number) {
  const id = setTimeout(() => { timers.delete(id); if (!disposed) callback() }, ms)
  timers.add(id)
  return id
}
function pause(ms: number) {
  return new Promise<void>(resolve => {
    const id = schedule(() => { pendingWaits.delete(id); resolve() }, ms / battleSpeed.value)
    pendingWaits.set(id, resolve)
  })
}
function cancelTurn() {
  turnToken++
  pendingWaits.forEach((resolve, id) => { clearTimeout(id); timers.delete(id); resolve() })
  pendingWaits.clear()
  activeCutin.value = null
  isProcessing.value = false
}

// --- ユーティリティ ---
const generateUUID = () => crypto.randomUUID()
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
  if (battleLogs.value.length > 100) battleLogs.value.shift()
  nextTick(() => {
    if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
  })
}

const triggerAnim = (target: any, type: string, text: string) => {
  target.animClass = type === 'damage' ? 'anim-damage' : type === 'magic' ? 'anim-magic' : type === 'guard' ? 'anim-guard' : 'anim-heal'
  target.popups.push({ id: Date.now() + Math.random(), text, type })
  schedule(() => { target.animClass = '' }, 400)
  schedule(() => { target.popups.shift() }, 800)
}

// --- タグ選択（クリア報酬） ---
const isTagSelected = (label: string) => selectedTags.value.some(t => t.label === label)
const toggleRewardTag = (label: string, prompt: string) => {
  const index = selectedTags.value.findIndex(t => t.label === label)
  if (index > -1) selectedTags.value.splice(index, 1)
  else selectedTags.value.push({ label, prompt })
}

// --- 演出関連 ---
const showCutin = (img: string, text: string, isEnemy = false) => {
  const token = ++cutinToken
  activeCutin.value = { img, text, color: isEnemy ? 'from-red-600/80' : 'from-blue-600/80' }
  schedule(() => { if (token === cutinToken) activeCutin.value = null }, 600 / battleSpeed.value)
}

const isScreenFlashing = ref(false)
const flashScreen = () => {
  isScreenFlashing.value = true
  schedule(() => { isScreenFlashing.value = false }, 300)
}


const systemNotification = ref<{ title: string, details: string[], type: 'success' | 'error' | 'bonus' } | null>(null)

let notificationToken = 0
const showNotification = (title: string, details: string[], type: 'success' | 'error' | 'bonus' = 'success') => {
  const token = ++notificationToken
  systemNotification.value = { title, details, type }
  if (type === 'bonus' || type === 'success') {
    playSE('heal') // 成功時はヒール音などを鳴らす
  } else if (type === 'error') {
    playSE('damage') // エラー時はダメージ音
  }
  schedule(() => { if (token === notificationToken) systemNotification.value = null }, 2600) // 読みやすい短い通知
}

// --- API連携 (セーブ/ロード) ---
const fetchWithTimeout = async (url: string, options: RequestInit = {}) => {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), 12000)
  try { return await fetch(url, { ...options, signal: controller.signal }) }
  finally { clearTimeout(timeout) }
}
const localSaveKey = 'erika_rpg_save_' + userId
const makeSaveData = () => JSON.parse(JSON.stringify({
  version: 2, savedAt: Date.now(), player: player.value, battleState: battleState.value,
  gameState: gameState.value, currentEnemies: currentEnemies.value, enemyImagesPool: enemyImagesPool.value,
  equippedSkillIds: equippedSkillIds.value, statPoints: statPoints.value, skillPoints: skillPoints.value,
  watchTime: watchTime.value, hasGot30sBonus: hasGot30sBonus.value, hasGot60sBonus: hasGot60sBonus.value,
  rewardChoices: rewardChoices.value, selectedSongId: selectedSongId.value, heardSongs: heardSongs.value,
  rewardGenCount: rewardGenCount.value, rewardImages: rewardImages.value, selectedTags: selectedTags.value,
  rewardGrantedFloors: rewardGrantedFloors.value, battleSpeed: battleSpeed.value,
  journeyTier: journeyTier.value, floorIntroOpen: floorIntroOpen.value,
  battleLogs: battleLogs.value
}))
const saveLocal = () => {
  if (gameState.value === 'charMake' || isProcessing.value) return
  try { localStorage.setItem(localSaveKey, JSON.stringify(makeSaveData())) }
  catch { showNotification('端末への保存に失敗', ['手動セーブでサーバーへ保存してください。'], 'error') }
}
const saveGame = async () => {
  if (isProcessing.value || isSaving.value) return
  saveLocal()
  isSaving.value = true
  try {
    const res = await fetchWithTimeout('/api/save', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, data: makeSaveData() }) })
    if (!res.ok) throw new Error('サーバー保存に失敗しました。')
    showNotification('セーブ完了', ['現在の画面・セットリスト・楽曲記録を保存しました。'])
  } catch (e: any) { showNotification('サーバー保存に失敗', [e.message, '端末内の自動保存からも再開できます。'], 'error') }
  finally { isSaving.value = false }
}
const loadGame = async () => {
  if (isLoading.value || !dataReady.value) return
  isLoading.value = true
  try {
    let local: any = null, remote: any = null
    try { local = JSON.parse(localStorage.getItem(localSaveKey) || 'null') } catch {}
    try { const res = await fetchWithTimeout(`/api/load?userId=${encodeURIComponent(userId!)}`); if (res.ok) remote = await res.json() } catch {}
    const data = local && (!remote || (local.savedAt || 0) >= (remote.savedAt || 0)) ? local : remote
    if (!data?.player || !data?.battleState) throw new Error('セーブデータが見つかりません。')
    cancelTurn(); destroyMusic()
    const cleanActor = (a: any) => ({ ...a, animClass: '', popups: [] })
    player.value = cleanActor({ ...player.value, ...data.player })
    player.value.mp = Math.max(0, Math.min(player.value.maxMp, player.value.mp))
    player.value.hp = Math.max(0, Math.min(player.value.maxHp, player.value.hp))
    player.value.skills = [...new Set<string>(player.value.skills)].filter(id => allSkills.value.some(s => s.id === id))
    battleState.value = { floor: Math.max(1, Math.min(10, data.battleState.floor)), enemyCount: data.battleState.enemyCount || 1, turn: data.battleState.turn || 1 }
    equippedSkillIds.value = [...new Set<string>(data.equippedSkillIds || player.value.skills.slice(0, 4))].filter(id => player.value.skills.includes(id)).slice(0, 4)
    statPoints.value = Math.max(0, data.statPoints || 0); skillPoints.value = Math.max(0, data.skillPoints || 0)
    watchTime.value = Math.min(60, Math.max(0, data.watchTime || 0))
    hasGot30sBonus.value = !!data.hasGot30sBonus; hasGot60sBonus.value = !!data.hasGot60sBonus
    rewardChoices.value = data.rewardChoices || []; selectedSongId.value = data.selectedSongId || ''
    heardSongs.value = data.heardSongs || []; rewardGrantedFloors.value = data.rewardGrantedFloors || []
    rewardGenCount.value = data.rewardGenCount || 0; rewardImages.value = data.rewardImages || []
    selectedTags.value = data.selectedTags || []; journeyTier.value = data.journeyTier || 'Very Hard'
    battleSpeed.value = data.battleSpeed === 1.5 ? 1.5 : 1
    floorIntroOpen.value = !!data.floorIntroOpen
    const states = ['battle', 'reward', 'gameover', 'gameclear']
    gameState.value = states.includes(data.gameState) ? data.gameState : 'battle'
    if (Array.isArray(data.enemyImagesPool)) enemyImagesPool.value = data.enemyImagesPool
    else await fetchGallery()
    if (data.version === 2 && data.currentEnemies?.length) currentEnemies.value = data.currentEnemies.map(cleanActor)
    else if (gameState.value === 'battle') startNextWave()
    battleLogs.value = data.battleLogs || []
    if (gameState.value === 'battle' && player.value.hp <= 0) gameState.value = 'gameover'
    if (gameState.value === 'reward') {
      if (!rewardChoices.value.length) chooseRewardSongs()
      await nextTick(); mountMusic('reward')
    }
    showNotification('探索を再開', [data.version === 2 ? '保存した場面から再開しました。' : '旧セーブを移行しました。未保存だった報酬ポイントは復元できません。'])
  } catch (e: any) { showNotification('ロード失敗', [e.message], 'error') }
  finally { isLoading.value = false }
}


// --- キャラメイク ---
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
  if (isGenerating.value || !dataReady.value || !charMakeSelections.value.classStats.initial_skills) return
  isGenerating.value = true
  try {
    if (!player.value.name.trim()) player.value.name = 'あなた'
    
    let finalStats = { ...charMakeSelections.value.classStats }
    charMakeSelections.value.bonusStats.forEach(bonus => {
      for (let key in bonus) finalStats[key] = (finalStats[key] || 0) + bonus[key]
    })
    Object.assign(player.value, finalStats)
    player.value.maxHp = Math.max(1, finalStats.hp)
    player.value.maxMp = Math.max(1, finalStats.mp)
    player.value.hp = player.value.maxHp
    player.value.mp = player.value.maxMp
    player.value.skills = [...(charMakeSelections.value.classStats.initial_skills || [])]
    equippedSkillIds.value = player.value.skills.slice(0, 4)

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
    floorIntroOpen.value = true
    saveLocal()

  } catch (e: any) {
    if (e.message === "NSFW") {
      showNotification('生成ブロック', ["AIのセーフティフィルターにブロックされました。", "別の要素を選んで再試行してください！"], 'error')
    } else {
      showNotification('アバター生成エラー', ["エラーが発生しました。", e.message], 'error')
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
    enemyImagesPool.value = shuffled(images)
  } catch (e) {}
}

const generateEnemy = (floor: number, type = 'normal'): Enemy => {
  const imgData = enemyImagesPool.value.pop() || { url: '/assets/images/gallery.jpg', name: '深淵のデッドロック エリカ' }
  // Normal: 1階あたり16ptを目安に成長。初階の連戦を短くし、後半は緩やかに増加。
  let baseHp = 42 + (floor - 1) * 24, baseStr = 8 + (floor - 1) * 2.8, baseDef = 4 + (floor - 1) * 1.5, baseSpd = 6 + (floor - 1) * 1.2

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
  battlePhase.value = 'コマンドを選択'
  battleState.value.turn = 1
  battleLogs.value = []
  player.value.buffs = { str: 0, mag: 0, def: 0, spd: 0 }
  player.value.isDefending = false
  player.value.stunTurns = 0
  showSkillMenu.value = false

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
    attacker.isDefending = true; triggerAnim(attacker, 'guard', 'GUARD')
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

    }

    // ★魔法や必殺技ならカットイン演出
    if (skill.type === 'ultimate' || skill.name === '痛恨の一撃！！') {
      if (!isAoE) showCutin(attacker.avatarUrl || attacker.imageUrl, skill.name, attacker !== player.value)
    }

    if (!isAoE) playSE(skill.type === 'attack_magic' || skill.type === 'ultimate' || skill.type === 'heal' || skill.type === 'buff' ? 'skill_magic' : 'skill_phys')

    if (skill.type === 'heal') {
      if (isAoE && defender !== attacker) return
      const amount = Math.min(attacker.maxHp - attacker.hp, Math.floor(attacker.maxHp * (skill.multiplier ?? 0.5)))
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
      dmg = Math.max(1, atkStat * (skill.multiplier ?? 1) - defStat * 0.5)
    }

    if (defender.isDefending) dmg *= 0.5
    const finalDamage = Math.max(1, Math.floor(dmg * (0.95 + Math.random() * 0.1)))
    addLog(`${defender.name || defender.enemyName} に ${finalDamage} のダメージ！`, 'damage')
    defender.hp = Math.max(0, defender.hp - finalDamage)
    triggerAnim(defender, isMagical ? 'magic' : 'damage', finalDamage.toString())
    playSE('damage')

    // ★プレイヤー被弾時に画面フラッシュ
    if (defender === player.value) flashScreen()
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

  // ★プレイヤー被弾時に画面フラッシュ
  if (defender === player.value) flashScreen()
}

const skillCostHp = (s: Skill) => s.cost_hp_percent ? Math.max(1, Math.floor(player.value.hp * s.cost_hp_percent / 100)) : 0
const skillUnavailable = (s: Skill): string => {
  if (isProcessing.value) return '行動中'
  if (floorIntroOpen.value) return '探索開始後に使用できます'
  if (!equippedSkillIds.value.includes(s.id)) return 'セットリスト未登録'
  if (s.condition) {
    const match = /^hp_under_(\d+)$/.exec(s.condition)
    if (!match || player.value.hp / player.value.maxHp * 100 > Number(match[1])) return `HP${match?.[1] || '?'}%以下で使用可能`
  }
  if (s.type === 'ultimate') { if (player.value.mp < 1) return 'MPが必要です' }
  else if ((s.cost_mp || 0) > player.value.mp) return 'MP不足'
  if (skillCostHp(s) >= player.value.hp) return 'HP不足'
  return ''
}
const skillCostLabel = (s: Skill) => s.type === 'ultimate' ? '全MP' : s.cost_hp_percent ? `HP ${skillCostHp(s)}` : `MP ${s.cost_mp || 0}`
const skillRole = (s: Skill) => ({ attack_physical: '物理', attack_magic: '魔法', heal: '回復', buff: '強化', debuff: '弱体', ultimate: '必殺' }[s.type] || s.type)
const markDefeated = () => {
  currentEnemies.value.forEach(e => {
    if (e.hp <= 0 && !e.isDead) { e.isDead = true; addLog(`${e.enemyName} を撃破！`, 'system'); playSE('defeat') }
  })
}
const executeAction = async (requestedAction: string | Skill) => {
  if (isProcessing.value || gameState.value !== 'battle' || floorIntroOpen.value || player.value.hp <= 0) return
  let action: string | Skill = requestedAction
  if (typeof action === 'object') {
    const canonical = allSkills.value.find(s => s.id === (requestedAction as Skill).id)
    if (!canonical) return
    action = canonical
    const reason = skillUnavailable(action)
    if (reason) { showNotification('使用できません', [reason], 'error'); return }
  } else if (!['attack', 'defend'].includes(action)) return
  const token = ++turnToken
  const active = () => !disposed && token === turnToken && gameState.value === 'battle'
  isProcessing.value = true; showSkillMenu.value = false
  try {
    addLog(`【ターン ${battleState.value.turn}】`, 'system')
    battlePhase.value = 'あなたの行動'
    if (player.value.stunTurns > 0) {
      player.value.stunTurns--; player.value.isDefending = false
      addLog(`${player.value.name} は動けない！`)
    } else {
      player.value.isDefending = action === 'defend'
      const target = currentEnemies.value[targetIndex.value]?.hp > 0 ? currentEnemies.value[targetIndex.value] : currentEnemies.value.find(e => e.hp > 0)
      if (!target) return
      if (typeof action === 'object') {
        player.value.hp -= skillCostHp(action)
        player.value.mp = action.type === 'ultimate' ? 0 : player.value.mp - (action.cost_mp || 0)
        if (action.target === 'all' && !['heal', 'buff'].includes(action.type)) {
          addLog(`${player.value.name} の ${action.name}！`)
          playSE(action.type === 'attack_physical' ? 'skill_phys' : 'skill_magic')
          if (action.type === 'ultimate') showCutin(player.value.avatarUrl, action.name)
          currentEnemies.value.filter(e => e.hp > 0).forEach(e => performAction(player.value, e, action, true))
        } else performAction(player.value, target, action)
      } else performAction(player.value, target, action)
    }
    await pause(650); if (!active()) return
    markDefeated()
    // 1体ずつ「行動→結果→次の敵」。倒した敵は回復・反撃しない。
    for (const enemy of currentEnemies.value) {
      if (enemy.isDead || enemy.hp <= 0 || player.value.hp <= 0) continue
      battlePhase.value = `${enemy.enemyName} の行動`
      actingEnemyId.value = enemy.id
      await pause(180); if (!active()) return
      processEnemyTurn(enemy, currentEnemies.value)
      await pause(650); if (!active()) return
      markDefeated()
    }
    actingEnemyId.value = ''
    if (player.value.hp <= 0) {
      addLog('力尽きた…。', 'system'); gameState.value = 'gameover'; battlePhase.value = '敗北'
    } else if (currentEnemies.value.every(e => e.isDead)) {
      battlePhase.value = 'WAVE CLEAR'; playSE('wave_clear')
      await pause(550); if (!active()) return
      if (battleState.value.floor === 10 && battleState.value.enemyCount === 5) {
        gameState.value = 'gameclear'; playSE('floor_clear')
        if (!selectedTags.value.length && rewardCategories.value['エリカ']?.['エリカ（統合・推奨）'])
          selectedTags.value = [{ label: 'エリカ（統合・推奨）', prompt: rewardCategories.value['エリカ']['エリカ（統合・推奨）'] }]
      } else if (battleState.value.enemyCount === 5) enterRewardRoom()
      else { battleState.value.enemyCount++; startNextWave() }
    } else {
      battleState.value.turn++; battlePhase.value = 'コマンドを選択'
      if (currentEnemies.value[targetIndex.value]?.isDead) targetIndex.value = currentEnemies.value.findIndex(e => !e.isDead)
    }
  } finally {
    if (token === turnToken) { isProcessing.value = false; actingEnemyId.value = ''; saveLocal() }
  }
}


const processEnemyTurn = (enemy: Enemy, allEnemies: Enemy[]) => {
  if (enemy.hp <= 0 || enemy.isDead) return
  enemy.isDefending = false
  let hasSkill = enemy.skillUses > 0
  let rand = Math.floor(Math.random() * 100)

  if (enemy.isCharging) {
    enemy.isCharging = false
    performAction(enemy, player.value, { id: 't', name: '痛恨の一撃！！', description: '', type: 'attack_physical', multiplier: 1.6 })
    return
  }

  if (!hasSkill) { performAction(enemy, player.value, rand < 80 ? 'attack' : 'defend'); return }

  if (enemy.traitName === 'エース') {
    if (rand < 50 && allEnemies.some(e => e.hp > 0 && e.hp < e.maxHp * 0.7)) {
      let target = allEnemies.find(e => e.hp > 0 && e.hp < e.maxHp * 0.7) || enemy
      let hurtAlly = allEnemies.find(e => e !== enemy && !e.isDead && e.hp > 0 && e.hp < e.maxHp * 0.5)
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
      enemy.buffs.str = Math.min(40, enemy.buffs.str + 20); triggerAnim(enemy, 'heal', 'ATK UP'); enemy.skillUses--
    } else performAction(enemy, player.value, 'attack')
  } else {
    performAction(enemy, player.value, 'attack') // 簡易化
  }
}

// --- 休憩所：30秒Normal / 60秒Easy。視聴時間は3曲をまたいで累積 ---
const enterRewardRoom = () => {
  destroyMusic(); gameState.value = 'reward'
  watchTime.value = 0; hasGot30sBonus.value = false; hasGot60sBonus.value = false
  player.value.hp = player.value.maxHp; player.value.mp = player.value.maxMp
  player.value.buffs = { str: 0, mag: 0, def: 0, spd: 0 }
  if (!rewardGrantedFloors.value.includes(battleState.value.floor)) {
    statPoints.value += 5; skillPoints.value += 1
    rewardGrantedFloors.value.push(battleState.value.floor)
  }
  chooseRewardSongs()
  nextTick(() => mountMusic('reward'))
}
const checkBonuses = () => {
  if (watchTime.value >= 30 && !hasGot30sBonus.value) {
    hasGot30sBonus.value = true; statPoints.value += 11; skillPoints.value += 1
    showNotification('Normalの成長報酬を獲得', ['合計16pt・スキル習得権2曲分（この階層）'])
    saveLocal()
  }
  if (watchTime.value >= 60 && !hasGot60sBonus.value) {
    hasGot60sBonus.value = true; statPoints.value += 8; skillPoints.value += 1
    showNotification('Easyの成長報酬を獲得', ['合計24pt・スキル習得権3曲分（この階層）'])
    saveLocal()
  }
}


const allocateStat = (key: string) => {
  if (gameState.value === 'reward' && statPoints.value > 0 && statList.some(s => s.key === key)) {
    if (key === 'maxHp') { player.value.maxHp += 10; player.value.hp += 10 }
    else if (key === 'maxMp') { player.value.maxMp += 5; player.value.mp += 5 }
    else player.value[key] += 1
    statPoints.value--; saveLocal()
  }
}

const unlearnedSkills = computed(() => allSkills.value.filter(s => !player.value.skills.includes(s.id) && (!s.min_floor || s.min_floor <= battleState.value.floor)))
const learnSelectedSkill = (skill: Skill) => {
  if (gameState.value === 'reward' && skillPoints.value > 0 && unlearnedSkills.value.some(s => s.id === skill.id)) {
    player.value.skills.push(skill.id); skillPoints.value--
    if (equippedSkillIds.value.length < 4) equippedSkillIds.value.push(skill.id)
    saveLocal()
    showNotification('スキル習得！', [`特技「${skill.name}」を習得しました！`], 'success')
  }
}

const goToNextFloor = () => {
  if (gameState.value !== 'reward' || !equippedSkillIds.value.length) return
  journeyTier.value = rewardTier.value
  destroyMusic()
  battleState.value.floor++; battleState.value.enemyCount = 1
  gameState.value = 'battle'; startNextWave(); floorIntroOpen.value = true; saveLocal()
}
const restartFloor = () => {
  cancelTurn(); destroyMusic()
  player.value.hp = player.value.maxHp; player.value.mp = player.value.maxMp
  battleState.value.enemyCount = 1; gameState.value = 'battle'
  startNextWave(); floorIntroOpen.value = true; saveLocal()
}
const resetGame = async () => {
  if (!window.confirm('この端末の冒険記録を消して、最初から始めますか？')) return
  destroyMusic(); cancelTurn()
  // 別IDに切り替え、旧サーバーセーブを誤って読み直さない。
  localStorage.removeItem(localSaveKey)
  localStorage.setItem('erika_rpg_userid', 'user_' + generateUUID())
  location.reload()
}


// --- クリア後の画像生成（NSFW対応） ---
const generateRewardImage = async () => {
  if (gameState.value !== 'gameclear' || isGeneratingReward.value || rewardGenCount.value >= 2) return
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
    rewardGenCount.value++; saveLocal()
  } catch (e: any) {
    if (e.message === "NSFW") {
      showNotification('生成ブロック', ["AIのセーフティフィルターにブロックされました。", "（健全な単語でも組み合わせで誤判定されることがあります）", "別の要素を選んで再試行してください！"], 'error')
    } else {
      showNotification('画像生成エラー', ["生成に失敗しました。", "詳細: " + e.message], 'error')
    }
  } finally {
    isGeneratingReward.value = false
  }
}

const charMakeCategories = computed(() => {
  const allowedKeys = ['顔・容姿', '髪型', '髪色', '瞳・眼鏡']
  let filtered: Record<string, Record<string, string>> = {}
  for (const key of allowedKeys) {
    if (rewardCategories.value[key]) {
      filtered[key] = rewardCategories.value[key]
    }
  }
  return filtered
})

const isCharMakeTagSelected = (label: string) => charMakeTags.value.some(t => t.label === label)
const toggleCharMakeTag = (label: string, prompt: string) => {
  const index = charMakeTags.value.findIndex(t => t.label === label)
  if (index > -1) charMakeTags.value.splice(index, 1)
  else charMakeTags.value.push({ label, prompt })
}

const statNames: Record<string, string> = { str: '攻撃', mag: '魔力', def: '防御', spd: '速度', luk: '運' }
const classLabel = computed(() => ({ Sawa: 'ボーカル＆ギター', Pee: 'ギタリスト', Shin: 'ドラマー', Jun: 'ベーシスト', busters: 'ファン' }[player.value.className] || player.value.className))
const dataReady = ref(false)
const dataError = ref('')
const battleSpeed = ref(1)
const battlePhase = ref('コマンドを選択')
const actingEnemyId = ref('')
const showFullLog = ref(false)
const floorIntroOpen = ref(false)
const setlistOpen = ref(false)
const skillFilter = ref('all')
const skillSearch = ref('')
const rewardGrantedFloors = ref<number[]>([])
const journeyTier = ref('Very Hard')
const rewardTier = computed(() => hasGot60sBonus.value ? 'Easy' : hasGot30sBonus.value ? 'Normal' : 'Very Hard')
const canEditSetlist = computed(() => gameState.value === 'reward' || (gameState.value === 'battle' && floorIntroOpen.value))
const visibleUnlearned = computed(() => unlearnedSkills.value.filter(s => (skillFilter.value === 'all' || s.type === skillFilter.value) && s.name.toLowerCase().includes(skillSearch.value.toLowerCase())))
const visibleLogs = computed(() => showFullLog.value ? battleLogs.value : battleLogs.value.slice(-2))
const toggleSetlist = (id: string) => {
  if (!canEditSetlist.value || !player.value.skills.includes(id)) return
  const index = equippedSkillIds.value.indexOf(id)
  if (index >= 0) equippedSkillIds.value.splice(index, 1)
  else if (equippedSkillIds.value.length < 4) equippedSkillIds.value.push(id)
  else { showNotification('セットリストは4曲まで', ['使わない曲を外してから追加してください。'], 'error'); return }
  saveLocal()
}
const beginFloor = () => {
  if (!equippedSkillIds.value.length) { setlistOpen.value = true; return }
  floorIntroOpen.value = false; setlistOpen.value = false; systemNotification.value = null; saveLocal()
}
const floorStories = [
  { title: 'まだ名前のない入口', intro: '扉の向こうから、誰かがチューニングする音が聞こえる。ここで必要なのは、完璧な準備より最初の一歩だ。', lines: ['靴音が静寂をほどいていく。', 'ポケットの中のピックを握り直した。', '二つの足音が、あなたの歩幅を試している。', '少しだけ、呼吸が整ってきた。', '扉の前で立ち止まる。始まりを終える時間だ。'], outro: '最初の扉を越えた。まだ知らない自分が、少しだけ前を歩いている。' },
  { title: '午前零時の留守番電話', intro: '再生されなかったメッセージが、廊下にこだまする。返事は言葉でなくてもいい。先へ進む足音で伝えよう。', lines: ['発信音だけが遠くに残る。', '伝えそびれた言葉を思い出した。', '二つの呼び出し音が重なる。', '今なら、違う返事ができる気がした。', '受話器の向こうで、誰かが息をひそめる。'], outro: '返事のない夜にも、確かに届くものがある。' },
  { title: '片道切符の待合室', intro: '時刻表には行き先だけが書かれている。出発時刻は、自分で決めるらしい。', lines: ['切符の角は少し丸くなっている。', '空席に荷物を置き、すぐに持ち直す。', '二本の線路が、同じ闇へ続いている。', '発車ベルはまだ鳴らない。', '最後の改札が、行く手をふさいだ。'], outro: '戻るための切符はない。それでも、歩き出せた。' },
  { title: '忘れ物だけの教室', intro: '机の上には、完成しなかった夢が並んでいる。一つだけ持って帰れるなら、何を選ぶだろう。', lines: ['消し跡の残るノートを見つけた。', '窓際の席には、誰も座っていない。', '二つの問いが、答えを待っている。', '正解のない問題を、そっと閉じた。', '最後のチャイムが鳴る。'], outro: '未完成のままでも、大切にしていい。' },
  { title: 'ノイズの向こうの声', intro: '周波数を合わせるたびに、違う誰かの声が混ざる。あなた自身の声は、まだちゃんと聞こえるだろうか。', lines: ['小さなノイズが耳の奥に残る。', '聞き覚えのある声が途切れた。', '二つの波形がぶつかり合う。', '音量を下げると、聞こえるものがあった。', '沈黙の直前、強い反応が走る。'], outro: '誰かの声を聞くことと、自分を失うことは違う。' },
  { title: '拍手のないステージ', intro: '客席は空だ。けれど、演奏をやめる理由にはならなかった。誰に届くかより、何を鳴らすか。', lines: ['床板が一度だけきしんだ。', 'マイクに触れず、深く息を吸う。', '二つの影がステージへ上がる。', '最後列まで届くつもりで、前を向いた。', '開演の合図は、自分で出す。'], outro: '拍手は聞こえなかった。それでも、確かに演奏した。' },
  { title: '書き直された地図', intro: 'ここまでの道が地図から消えている。覚えているなら、それで十分だ。次の道は、まだ誰も描いていない。', lines: ['折り目だけが、道の名残を示している。', '迷った場所に小さな印を付けた。', '二つの分かれ道が、また一つになる。', '地図を閉じても、足は止まらない。', '余白の中心で、行く手を阻む気配がする。'], outro: '迷った跡も、あなたの道になった。' },
  { title: '明日への未送信', intro: '未来の自分に宛てた手紙がある。読み終えるには、もう少し先へ進まなければならない。', lines: ['封筒には今日の日付が書かれていた。', '弱音のあとに、一行だけ希望が残る。', '二つのためらいを、胸の中でほどく。', '続きを書くために、ペンをしまった。', '差出人の名前が、ゆっくり浮かび上がる。'], outro: '返事は、明日のあなたに任せよう。' },
  { title: '最後のリハーサル', intro: 'やり直しは何度でもできる。けれど、この一回は今しかない。失敗を避けるより、鳴らしたい音を思い出そう。', lines: ['いつもの手順を、丁寧になぞる。', '少しのずれにも、意味がある。', '二つの緊張が、同時に迫ってくる。', 'もう一度だけ、弦を確かめた。', '準備は終わった。あとは踏み出すだけだ。'], outro: '完璧ではない。だからこそ、あなたの演奏だ。' },
  { title: 'アンコールのその先', intro: '終わりを迎えるために、ここまで来た。その先に何を持って帰るかは、あなたが決めていい。', lines: ['最初の一歩を思い出した。', '旅の途中で出会った音がよみがえる。', '二つの問いに、今度は迷わなかった。', '終わりの気配が、静かに近づいている。', '最後の扉。あなたのセットリストを、鳴らし切ろう。'], outro: '冒険は終わっても、耳に残った音楽は続いていく。' }
]
const floorStory = computed(() => floorStories[Math.max(0, Math.min(9, battleState.value.floor - 1))]!)
function shuffled<T>(items: T[]): T[] {
  const result = [...items]
  for (let i = result.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [result[i], result[j]] = [result[j]!, result[i]!] }
  return result
}

// 共通のYouTubeプレーヤー。3曲の選択と、クリア後の楽曲図鑑に使用。
const rewardChoices = ref<Song[]>([])
const selectedSongId = ref('')
const heardSongs = ref<HeardSong[]>([])
const musicError = ref('')
const musicLoading = ref(false)
const musicReady = ref(false)
const musicMode = ref<'reward' | 'library'>('reward')
const continuousPlay = ref(false)
const currentSong = computed(() => (musicMode.value === 'reward' ? rewardChoices.value : heardSongs.value).find(s => songId(s) === selectedSongId.value))
const songId = (song: Song): string => {
  if (song.youtube_id && /^[\w-]{11}$/.test(song.youtube_id)) return song.youtube_id
  try {
    const url = new URL(song.embed_url || song.share_url || '')
    const id = url.hostname === 'youtu.be' ? url.pathname.slice(1) : url.searchParams.get('v') || url.pathname.split('/').pop() || ''
    return /^[\w-]{11}$/.test(id) ? id : ''
  } catch { return '' }
}
const songLink = (song: Song) => `https://www.youtube.com/watch?v=${songId(song)}`
const listenedSeconds = (song: Song) => Math.floor(heardSongs.value.find(s => songId(s) === songId(song))?.seconds || 0)
const chooseRewardSongs = () => {
  const heard = new Set(heardSongs.value.map(songId))
  rewardChoices.value = [...shuffled(thePillowsSongs.value.filter(s => !heard.has(songId(s)))), ...shuffled(thePillowsSongs.value.filter(s => heard.has(songId(s))))].slice(0, 3)
  selectedSongId.value = rewardChoices.value[0] ? songId(rewardChoices.value[0]) : ''
}
let lastVideoTime = 0, lastWallTime = 0, musicCheckpoint = 0
const resetPlaybackClock = () => { lastVideoTime = Number(ytPlayer?.getCurrentTime?.() || 0); lastWallTime = performance.now() }
const sampleListening = () => {
  if (!musicReady.value || !ytPlayer) return
  const now = performance.now(), videoTime = Number(ytPlayer.getCurrentTime?.() || 0)
  const wallDelta = (now - lastWallTime) / 1000, videoDelta = videoTime - lastVideoTime
  lastWallTime = now; lastVideoTime = videoTime
  // 一時停止・バッファリング・非表示タブ・シークで報酬が増えないようにする。
  if (ytPlayer.getPlayerState?.() !== 1 || document.hidden || wallDelta <= 0 || wallDelta > 2.5 || videoDelta <= 0 || videoDelta > wallDelta * 2.2 + 0.4) return
  const seconds = Math.min(wallDelta, videoDelta)
  if (musicMode.value === 'reward' && gameState.value === 'reward') {
    const song = currentSong.value
    if (!song) return
    let record = heardSongs.value.find(s => songId(s) === selectedSongId.value)
    if (!record) { record = { ...song, seconds: 0, firstFloor: battleState.value.floor }; heardSongs.value.push(record); record = heardSongs.value[heardSongs.value.length - 1]! }
    record.seconds += seconds
    watchTime.value = Math.min(60, watchTime.value + seconds)
    checkBonuses()
    if (now - musicCheckpoint > 5000) { musicCheckpoint = now; saveLocal() }
  }
}
const destroyMusic = () => {
  sampleListening(); musicToken++
  clearInterval(watchTimer); watchTimer = null
  musicReady.value = false; musicLoading.value = false
  if (ytPlayer?.destroy) ytPlayer.destroy()
  ytPlayer = null
}
const youtubeApi = (): Promise<any> => {
  const w = window as any
  if (w.YT?.Player) return Promise.resolve(w.YT)
  if (w.__erikaYoutubeReady) return w.__erikaYoutubeReady
  w.__erikaYoutubeReady = new Promise((resolve, reject) => {
    const timeout = window.setTimeout(() => { w.__erikaYoutubeReady = null; reject(new Error('音楽プレーヤーの読み込みがタイムアウトしました。')) }, 15000)
    const previous = w.onYouTubeIframeAPIReady
    w.onYouTubeIframeAPIReady = () => { clearTimeout(timeout); try { previous?.() } finally { resolve(w.YT) } }
    let tag = document.querySelector<HTMLScriptElement>('script[src="https://www.youtube.com/iframe_api"]')
    if (!tag) { tag = document.createElement('script'); tag.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(tag) }
    tag.addEventListener('error', () => { clearTimeout(timeout); w.__erikaYoutubeReady = null; tag?.remove(); reject(new Error('音楽プレーヤーを読み込めません。通信状態を確認してください。')) }, { once: true })
  })
  return w.__erikaYoutubeReady
}
const mountMusic = async (mode: 'reward' | 'library', autoplay = false) => {
  destroyMusic(); musicMode.value = mode; musicError.value = ''
  const songs = mode === 'reward' ? rewardChoices.value : heardSongs.value
  if (!songs.length) { musicError.value = '再生できる曲がありません。'; return }
  if (!songs.some(s => songId(s) === selectedSongId.value)) selectedSongId.value = songId(songs[0]!)
  const token = musicToken; musicLoading.value = true
  try {
    await nextTick()
    const YT = await youtubeApi()
    if (disposed || token !== musicToken) return
    const host = document.getElementById(mode === 'reward' ? 'reward-music-host' : 'library-music-host')
    if (!host) { musicLoading.value = false; return }
    host.replaceChildren()
    const mount = document.createElement('div'); host.appendChild(mount)
    ytPlayer = new YT.Player(mount, {
      width: '100%', height: '100%', videoId: selectedSongId.value,
      playerVars: { playsinline: 1, origin: window.location.origin, controls: 1 },
      events: {
        onReady: (e: any) => {
          if (token !== musicToken || disposed) { e.target.destroy(); return }
          musicLoading.value = false; musicReady.value = true
          resetPlaybackClock(); watchTimer = setInterval(sampleListening, 250)
          if (autoplay) e.target.playVideo()
        },
        onStateChange: (e: any) => {
          if (token !== musicToken || disposed) return
          resetPlaybackClock()
          if (e.data === 0 && musicMode.value === 'library' && continuousPlay.value) playNextSong()
        },
        onError: () => { if (token === musicToken) { musicLoading.value = false; musicReady.value = false; musicError.value = 'この動画は埋め込み再生できません。別の曲を選ぶか、YouTubeで開いてください。' } },
        onAutoplayBlocked: () => { if (token === musicToken) musicError.value = '動画の再生ボタンを押してください。' }
      }
    })
  } catch (e: any) { if (token === musicToken) { musicLoading.value = false; musicError.value = e.message } }
}
const selectSong = (song: Song, mode: 'reward' | 'library') => {
  destroyMusic(); selectedSongId.value = songId(song); mountMusic(mode, true); saveLocal()
}
const playNextSong = () => {
  const index = heardSongs.value.findIndex(s => songId(s) === selectedSongId.value)
  if (index + 1 < heardSongs.value.length) selectSong(heardSongs.value[index + 1]!, 'library')
  else continuousPlay.value = false
}
const playAllSongs = () => {
  if (!heardSongs.value.length) return
  continuousPlay.value = true; selectSong(heardSongs.value[0]!, 'library')
}
const onVisibility = () => { resetPlaybackClock(); if (document.hidden) saveLocal() }
const onPageHide = () => { sampleListening(); saveLocal() }
const loadAssets = async () => {
  dataReady.value = false; dataError.value = ''
  try {
    const readJson = async (path: string) => { const res = await fetchWithTimeout(path); if (!res.ok) throw new Error(`${path} の読み込みに失敗しました。`); return res.json() }
    const [skills, songs, categories, questions] = await Promise.all([
      readJson('/assets/skills.json'), readJson('/assets/thepillows_releases_tab.json'), readJson('/assets/rpgclear.json'), readJson('/assets/charmake.json')
    ])
    if (disposed) return
    if (!Array.isArray(skills) || !skills.length || !Array.isArray(songs) || !questions.questions?.length) throw new Error('必要なJSONの形式が正しくありません。')
    // 旧JSONでも10階までに習得可能。9階の休憩所で最終技が揃う。
    const unlockFloor = (n: number) => n >= 18 ? 9 : n >= 13 ? 8 : Math.min(n, 9)
    allSkills.value = skills.map((s: Skill) => ({ ...s, min_floor: unlockFloor(s.min_floor || 1), ...(s.id === 'skill_mr_lostman' ? { multiplier: 0.5 } : {}) }))
    const unique = new Map<string, Song>()
    songs.forEach((song: Song) => { const id = songId(song); if (id && !unique.has(id)) unique.set(id, { ...song, title: song.title || '曲名未登録' }) })
    thePillowsSongs.value = [...unique.values()]
    rewardCategories.value = categories; charmakeQuestions.value = questions.questions
    dataReady.value = true
  } catch (e: any) { dataError.value = e.message }
}
onMounted(() => {
  loadAssets()
  document.addEventListener('visibilitychange', onVisibility)
  window.addEventListener('pagehide', onPageHide)
})
onUnmounted(() => {
  if (!isProcessing.value) saveLocal()
  destroyMusic(); disposed = true; cancelTurn()
  timers.forEach(clearTimeout); timers.clear()
  document.removeEventListener('visibilitychange', onVisibility)
  window.removeEventListener('pagehide', onPageHide)
})



</script>

<template>
  <div class="bg-zinc-950 min-h-screen pt-20 pb-12">
    <div v-if="systemNotification" 
         class="fixed top-4 left-1/2 -translate-x-1/2 z-[100] flex flex-col items-center justify-center pointer-events-none w-[90%] max-w-sm"
         v-motion
         :initial="{ opacity: 0, y: -40, scale: 0.9 }"
         :enter="{ opacity: 1, y: 0, scale: 1, transition: { type: 'spring', stiffness: 250, damping: 15 } }"
         :leave="{ opacity: 0, y: -20, scale: 0.9 }">
      <div class="bg-black/90 backdrop-blur-xl border-2 rounded-2xl p-3 text-center w-full relative overflow-hidden"
           :class="{
             'border-erika shadow-[0_0_40px_rgba(243,156,18,0.5)]': systemNotification.type === 'bonus' || systemNotification.type === 'success',
             'border-red-500 shadow-[0_0_40px_rgba(239,68,68,0.5)]': systemNotification.type === 'error'
           }">
        <div class="absolute inset-0 bg-gradient-to-t opacity-50"
             :class="systemNotification.type === 'error' ? 'from-red-500/20 to-transparent' : 'from-erika/20 to-transparent'"></div>
        
        <h3 class="relative text-base font-black mb-2 tracking-wider"
            :class="systemNotification.type === 'error' ? 'text-red-500 drop-shadow-[0_0_10px_rgba(239,68,68,1)]' : 'text-erika drop-shadow-[0_0_10px_rgba(243,156,18,1)]'">
          {{ systemNotification.title }}
        </h3>
        <div class="relative space-y-2">
          <p v-for="(text, idx) in systemNotification.details" :key="idx" 
             class="text-white text-sm font-bold bg-white/10 py-1 px-3 rounded-full inline-block border border-white/5">
            {{ text }}
          </p>
        </div>
      </div>
    </div>
    <!-- ナビゲーション -->
    <nav class="max-w-2xl mx-auto px-4 flex justify-between items-center mb-6">
      <router-link to="/" class="text-erika font-bold text-sm hover:underline">← Back to Top</router-link>
      <button v-if="gameState !== 'charMake'" 
              @click="saveGame" :disabled="isSaving || isProcessing"
              class="px-4 py-2 bg-blue-600 text-white text-xs font-bold rounded-full shadow-[0_0_15px_rgba(37,99,235,0.5)] hover:bg-blue-500 disabled:opacity-50">
        {{ isSaving ? '保存中...' : '💾 セーブ' }}
      </button>
    </nav>



    <!-- バトル等のメインエリア -->
    <div class="container mx-auto px-4 max-w-3xl transition-all duration-300 rounded-2xl"
         :class="{'shadow-[inset_0_0_100px_rgba(239,68,68,0.6)] border border-red-500': isScreenFlashing}">
      
      <!-- 1. キャラメイク画面 -->
      <div v-if="gameState === 'charMake'" class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-6 text-center">
        <h2 class="text-xl font-bold text-white mb-6">ダイブ設定（キャラクター作成）</h2>

        <p v-if="dataError" class="error-text" role="alert">{{ dataError }} <button class="small-button" @click="loadAssets">再試行</button></p>
        <p v-else-if="!dataReady" class="help-text">冒険のデータを読み込んでいます…</p>
        <div v-if="dataReady && !isGenerating">
          <div v-if="currentQuestionIndex === 0" class="mb-8 border-b border-white/10 pb-8">
            <button @click="loadGame" :disabled="isLoading || !dataReady" class="w-full py-3 bg-transparent border border-blue-500 text-blue-400 font-bold rounded-lg hover:bg-blue-500 hover:text-white transition-colors">
              {{ isLoading ? 'ロード中...' : '💾 続きから遊ぶ（端末・サーバーの新しい記録）' }}
            </button>
          </div>

          <div v-if="currentQuestionIndex < charmakeQuestions.length">
            <p class="help-text">STEP {{ currentQuestionIndex + 1 }} / {{ charmakeQuestions.length }}</p>
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
            <!-- アバター特徴選択と自由入力 -->
            <div class="mb-6 text-left">
              <label class="block text-sm font-bold text-white mb-2">アバターの特徴を選択してください（任意）</label>
              
              <!-- 選択済みタグ表示エリア -->
              <div class="bg-black/50 border border-dashed border-blue-500 rounded-xl p-4 min-h-[80px] mb-4 overflow-hidden">
                <p class="text-xs text-zinc-500 font-bold mb-3">【選んだ特徴（クリックで解除）】</p>
                <transition-group tag="div" class="flex flex-wrap gap-2"
                  enter-active-class="transition duration-300 ease-out"
                  enter-from-class="transform scale-95 opacity-0"
                  enter-to-class="transform scale-100 opacity-100"
                  leave-active-class="transition duration-200 ease-in"
                  leave-from-class="transform scale-100 opacity-100"
                  leave-to-class="transform scale-95 opacity-0 absolute">
                  <span v-for="tag in charMakeTags" :key="tag.label" 
                        @click="toggleCharMakeTag(tag.label, tag.prompt)"
                        class="px-3 py-1 bg-blue-600 text-white font-bold text-sm rounded-full cursor-pointer hover:bg-blue-500 transition-colors flex items-center gap-1 shadow-md">
                    {{ tag.label }}
                    <span class="text-zinc-900 hover:text-black font-black leading-none ml-1">&times;</span>
                  </span>
                </transition-group>
                <p v-if="charMakeTags.length === 0" class="text-sm text-zinc-600 mt-2">下のリストから要素を選んでください。</p>
              </div>

              <!-- カテゴリ別タグリスト -->
              <div class="max-h-64 overflow-y-auto pr-2 border-t border-white/10 pt-4 mb-6 custom-scrollbar">
                <div v-for="(prompts, category) in charMakeCategories" :key="category" class="mb-4">
                  <p class="font-bold text-blue-400 mb-2">{{ category }}</p>
                  <div class="flex flex-wrap gap-2">
                    <button v-for="(prompt, label) in prompts" :key="label"
                            @click="toggleCharMakeTag(label, prompt)"
                            class="px-3 py-1.5 border rounded-full text-sm transition-colors"
                            :class="isCharMakeTagSelected(label) ? 'hidden' : 'border-zinc-700 text-zinc-400 hover:bg-white/10 hover:text-white'">
                      {{ label }}
                    </button>
                  </div>
                </div>
              </div>

              <!-- 自由入力エリア -->
              <label class="block text-sm font-bold text-white mb-2">最後に、追加したい要素を自由に入力してください。</label>
              <textarea v-model="freeTextInput" placeholder="自由入力（任意）"
                        class="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-erika min-h-[100px] mb-4"></textarea>
            </div>
            <button @click="submitCharMake" class="w-full py-4 bg-erika text-black font-black text-lg rounded-full shadow-[0_0_20px_rgba(243,156,18,0.3)] hover:bg-erika-light hover:-translate-y-1 transition-all">
              アバターを生成してダイブする
            </button>
          </div>
        </div>
        
        <div v-if="isGenerating" class="py-12">
          <p class="text-erika font-bold mb-4 animate-pulse">アバターを生成中...</p>
          <div class="w-full bg-zinc-800 rounded-full h-2 overflow-hidden"><div class="bg-erika h-full w-full origin-left animate-[pulse_1s_infinite]"></div></div>
        </div>
      </div>

      <!-- 2. バトル：画像と現在の行動を中心に配置 -->
      <section v-if="gameState === 'battle'" class="battle-layout">
        <header class="floor-heading">
          <div><p class="eyebrow">FLOOR {{ battleState.floor }} / 10 · WAVE {{ battleState.enemyCount }} / 5</p><h2>{{ floorStory.title }}</h2></div>
          <button class="small-button" @click="battleSpeed = battleSpeed === 1 ? 1.5 : 1; saveLocal()">{{ battleSpeed }}× テンポ</button>
        </header>
        <p class="flavor-line">{{ floorStory.lines[battleState.enemyCount - 1] }}</p>
        <div v-if="floorIntroOpen" class="intro-panel">
          <p class="eyebrow">INTERLUDE · {{ journeyTier }}</p>
          <p>{{ floorStory.intro }}</p>
          <div class="button-row"><button class="small-button" @click="setlistOpen = true">セットリストを編成（{{ equippedSkillIds.length }}/4）</button><button class="primary-button" @click="beginFloor">探索を始める</button></div>
        </div>
        <div class="enemy-stage" :class="{ 'duo': currentEnemies.length > 1 }">
          <button v-for="(enemy, index) in currentEnemies" :key="enemy.id" class="enemy-card"
            :class="{ selected: targetIndex === index && !enemy.isDead, fallen: enemy.isDead, acting: actingEnemyId === enemy.id }"
            :disabled="enemy.isDead || isProcessing || floorIntroOpen" @click="targetIndex = index"
            :aria-label="`${enemy.enemyName}を対象に選択`" :aria-pressed="targetIndex === index">
            <div class="enemy-art" :class="enemy.animClass">
              <img :src="enemy.imageUrl" :alt="enemy.enemyName" @error="($event.target as HTMLImageElement).style.opacity = '0.25'">
              <span class="trait-label">{{ enemy.traitName }}</span>
              <span v-if="enemy.isDead" class="defeated-label">DEFEATED</span>
              <span v-else-if="targetIndex === index" class="target-label">TARGET</span>
              <div class="combat-floats" aria-hidden="true"><span v-for="popup in enemy.popups" :key="popup.id" :class="['combat-number', popup.type]">{{ popup.text }}</span></div>
              <div class="enemy-caption"><strong>{{ enemy.enemyName }}</strong><span>{{ enemy.hp }} / {{ enemy.maxHp }}</span></div>
            </div>
            <div class="health-track"><div :style="{ width: Math.max(0, enemy.hp / enemy.maxHp * 100) + '%' }"></div></div>
            <div class="status-row"><span v-if="enemy.isCharging">⚠ 力をためている</span><span v-if="enemy.isDefending">防御中</span><span v-for="(value, stat) in enemy.buffs" v-show="value !== 0" :key="stat">{{ statNames[stat] || stat }} {{ value > 0 ? '+' : '' }}{{ value }}%</span></div>
          </button>
        </div>
        <section class="battle-journal" aria-live="polite" aria-atomic="false">
          <div class="journal-heading"><strong>{{ isProcessing ? battlePhase : floorIntroOpen ? '探索の準備' : 'コマンドを選択' }}</strong><button class="text-button" @click="showFullLog = !showFullLog">{{ showFullLog ? '閉じる' : '戦闘ログ' }}</button></div>
          <div ref="logContainer" :class="{ 'expanded-log': showFullLog }"><p v-for="(log, i) in visibleLogs" :key="i" :class="log.colorClass">{{ log.text }}</p></div>
        </section>
        <div class="command-dock">
          <div class="player-strip">
            <div class="player-portrait" :class="player.animClass"><img :src="player.avatarUrl" :alt="player.name"><div class="combat-floats"><span v-for="popup in player.popups" :key="popup.id" :class="['combat-number', popup.type]">{{ popup.text }}</span></div></div>
            <div class="player-vitals"><strong>{{ player.name }} <small>{{ classLabel }}</small></strong>
              <div class="vital-line"><span>HP</span><div class="vital-track hp"><div :style="{ width: Math.max(0, player.hp/player.maxHp*100)+'%' }"></div></div><b>{{ player.hp }}/{{ player.maxHp }}</b></div>
              <div class="vital-line"><span>MP</span><div class="vital-track mp"><div :style="{ width: Math.max(0, player.mp/player.maxMp*100)+'%' }"></div></div><b>{{ player.mp }}/{{ player.maxMp }}</b></div>
            </div>
          </div>
          <div class="status-row"><span v-if="player.isDefending">防御中</span><span v-for="(value, stat) in player.buffs" v-show="value !== 0" :key="stat">{{ statNames[stat] || stat }} {{ value > 0 ? '+' : '' }}{{ value }}%</span></div>
          <div class="base-commands"><button :disabled="isProcessing || floorIntroOpen" @click="executeAction('attack')">通常攻撃</button><button :disabled="isProcessing || floorIntroOpen" @click="executeAction('defend')">防御 <small>被ダメ半減・MP回復</small></button></div>
          <p class="setlist-label">SETLIST · {{ availableSkills.length }}/4 <span>スキルはここから直接選択</span></p>
          <div class="skill-grid"><button v-for="skill in availableSkills" :key="skill.id" :disabled="!!skillUnavailable(skill)" @click="executeAction(skill)" :title="skill.description">
            <span class="skill-meta">{{ skillRole(skill) }} · {{ skill.target === 'all' ? '全体' : ['heal','buff'].includes(skill.type) ? '自身' : '単体' }} <b>{{ skillCostLabel(skill) }}</b></span>
            <strong>{{ skill.name }}</strong><small>{{ skillUnavailable(skill) || skill.description }}</small>
          </button></div>
        </div>
      </section>

      <!-- 3. 階層間の休憩所 -->
      <section v-if="gameState === 'reward'" class="rest-panel">
        <p class="eyebrow">INTERMISSION</p><h2>第 {{ battleState.floor }} 階層 クリア</h2>
        <p class="flavor-line">{{ floorStory.outro }}</p>
        <div class="reward-tier"><strong>{{ rewardTier }}</strong><span>この階層の成長：{{ hasGot60sBonus ? 24 : hasGot30sBonus ? 16 : 5 }}pt ／ 習得権 {{ hasGot60sBonus ? 3 : hasGot30sBonus ? 2 : 1 }}曲分</span></div>
        <p class="help-text">3曲から好きな曲を選べます。聴いた時間は曲を切り替えても合算されます。</p>
        <div class="song-choices"><button v-for="song in rewardChoices" :key="songId(song)" :class="{ chosen: selectedSongId === songId(song) }" @click="selectSong(song, 'reward')"><small>{{ selectedSongId === songId(song) ? '選択中' : '聴いてみる' }}</small><strong>{{ song.title }}</strong><span v-if="listenedSeconds(song)">今回の冒険で {{ listenedSeconds(song) }}秒</span></button></div>
        <div id="reward-music-host" class="music-player"></div>
        <p v-if="musicLoading" class="help-text">プレーヤーを準備しています…</p>
        <p v-if="musicError" role="alert" class="error-text">{{ musicError }} <button class="text-button" @click="mountMusic('reward')">再読み込み</button></p>
        <a v-if="currentSong && musicMode === 'reward'" :href="songLink(currentSong)" target="_blank" rel="noopener noreferrer" class="text-button">{{ currentSong.title }} ↗ YouTubeで開く</a>
        <div class="listening-progress"><div :style="{ width: watchTime/60*100+'%' }"></div></div>
        <div class="tier-steps"><span :class="{ reached: true }">0秒 · Very Hard<br>5pt / 1曲</span><span :class="{ reached: hasGot30sBonus }">30秒 · Normal<br>16pt / 2曲</span><span :class="{ reached: hasGot60sBonus }">60秒 · Easy<br>24pt / 3曲</span></div>
        <p class="help-text">累計 {{ Math.floor(watchTime) }}秒 / 60秒。未視聴でも進めます。外部YouTubeでの視聴は計測できません。</p>
        <div class="growth-box"><h3>ステータス強化 <span>残り {{ statPoints }}pt</span></h3><p class="help-text">獲得ポイントによって難易度が変わります。敵の強さは共通です。</p>
          <div class="stat-grid"><div v-for="stat in statList" :key="stat.key"><span>{{ stat.label }}<b>{{ player[stat.key] }}</b></span><button :disabled="statPoints <= 0" @click="allocateStat(stat.key)" :aria-label="`${stat.label}に1ポイント割り振る`">＋</button></div></div>
        </div>
        <div class="growth-box"><h3>セットリスト <span>{{ equippedSkillIds.length }}/4曲</span></h3><p class="help-text">習得済みの曲から、戦闘に持ち込む4曲を選びます。</p><div class="equipped-pills"><span v-for="s in availableSkills" :key="s.id">{{ s.name }}</span></div><button class="small-button" @click="setlistOpen = true">セットリストを編成</button></div>
        <div class="growth-box"><h3>新しい曲を習得 <span>残り {{ skillPoints }}曲分</span></h3>
          <div class="skill-search"><input v-model="skillSearch" placeholder="曲名で検索" aria-label="習得する曲を検索"><select v-model="skillFilter" aria-label="スキルの種類"><option value="all">すべて</option><option value="attack_physical">物理</option><option value="attack_magic">魔法</option><option value="heal">回復</option><option value="buff">強化</option><option value="debuff">弱体</option><option value="ultimate">必殺</option></select></div>
          <div class="learn-list"><div v-for="skill in visibleUnlearned" :key="skill.id"><div><small>{{ skillRole(skill) }} · {{ skill.target === 'all' ? '全体' : '単体／自身' }}</small><strong>{{ skill.name }}</strong><p>{{ skill.description }}</p></div><button class="small-button" :disabled="skillPoints <= 0" @click="learnSelectedSkill(skill)">習得</button></div><p v-if="!visibleUnlearned.length" class="help-text">該当する未習得の曲はありません。</p></div>
        </div>
        <button class="primary-button next-floor" :disabled="equippedSkillIds.length === 0" @click="goToNextFloor">{{ rewardTier }} の成長報酬で、次の階層へ →</button>
        <p v-if="statPoints || skillPoints" class="help-text">未使用の {{ statPoints }}pt・習得権 {{ skillPoints }}曲分は次の休憩所へ持ち越せます。</p>
      </section>

      <!-- 4. GameOver -->
      <div v-if="gameState === 'gameover'" class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center">
        <h2 class="text-4xl font-black mb-4 text-red-500">GAME OVER</h2>
        <p class="text-zinc-400 mb-6">力尽きてしまいました…。<br>ペナルティなしで現在の階層の最初からリトライできます。</p>
        <button @click="restartFloor" class="w-full py-4 bg-red-600 text-white font-bold rounded-full hover:bg-red-500 transition-colors shadow-lg">現在の階層からリトライ</button>
      </div>

      <!-- 5. Game Clear (完全復元版) -->
      <div v-if="gameState === 'gameclear'" class="bg-black/60 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center">
        <h2 class="clear-title text-2xl sm:text-4xl font-black mb-4 text-erika drop-shadow-[0_0_15px_rgba(243,156,18,0.8)]">CONGRATULATIONS!</h2>
        <p class="text-lg text-white font-bold mb-8">見事10階層を突破し、エリカを討伐しました！</p>

        <section class="growth-box music-library">
          <p class="eyebrow">YOUR DISCOVERIES</p><h3>旅で出会った楽曲図鑑 <span>{{ heardSongs.length }}曲</span></h3>
          <p class="help-text">休憩所で実際に再生した曲を、出会った順に記録しています。</p>
          <template v-if="heardSongs.length">
            <div class="button-row"><button class="primary-button" @click="playAllSongs">最初から順番に聴く</button><label class="help-text"><input v-model="continuousPlay" type="checkbox"> 続けて再生</label></div>
            <div id="library-music-host" class="music-player"></div>
            <p v-if="currentSong && musicMode === 'library'" class="help-text">{{ currentSong.title }}</p>
            <p v-if="musicLoading" class="help-text">プレーヤーを準備しています…</p>
            <p v-if="musicError" class="error-text" role="alert">{{ musicError }}</p>
            <div class="button-row"><button class="small-button" @click="playNextSong">次の曲</button><button class="small-button" @click="mountMusic('library', true)">再読み込み</button></div>
            <ol class="song-library-list"><li v-for="(song, index) in heardSongs" :key="songId(song)"><button @click="selectSong(song, 'library')" :class="{ chosen: selectedSongId === songId(song) && musicMode === 'library' }"><span>{{ String(index + 1).padStart(2, '0') }}</span><div><strong>{{ song.title }}</strong><small>第{{ song.firstFloor }}階層で発見 · {{ Math.floor(song.seconds) }}秒視聴</small></div><span>▶</span></button><a :href="songLink(song)" target="_blank" rel="noopener noreferrer" class="text-button">YouTube ↗</a></li></ol>
          </template>
          <p v-else class="help-text">今回は未視聴での踏破でした。Very Hardへの挑戦、お疲れさまでした。</p>
        </section>

        <!-- 画像生成報酬エリア -->
        <div class="bg-black/60 backdrop-blur-md border-2 border-erika rounded-2xl p-6 md:p-8 text-left shadow-[0_0_30px_rgba(243,156,18,0.2)] mb-8">
          <h3 class="text-2xl font-black text-erika text-center mb-2">🎁 クリア特典：エリカの記憶を具現化する</h3>
          <p class="text-sm text-zinc-400 text-center mb-6">
            旅の記憶を組み合わせて、あなただけのエリカの姿を描きます。<br>
            <strong class="text-erika">※生成できるのは2回までです。</strong>
          </p>

          <div v-if="rewardGenCount < 2">
            <!-- 選択タグエリア -->
            <div class="bg-black/50 border border-dashed border-erika rounded-xl p-4 min-h-[80px] mb-6">
              <p class="text-xs text-zinc-500 font-bold mb-3">【選んだ特徴（クリックで解除）】</p>
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

    <div v-if="setlistOpen && canEditSetlist" class="setlist-backdrop" @click.self="setlistOpen = false" @keydown.esc="setlistOpen = false">
      <section class="setlist-dialog" role="dialog" aria-modal="true" aria-labelledby="setlist-title" tabindex="-1">
        <div class="journal-heading"><h2 id="setlist-title">セットリスト {{ equippedSkillIds.length }}/4</h2><button class="small-button" @click="setlistOpen = false">閉じる</button></div>
        <p class="help-text">登録順にコマンドが並びます。入れ替えたい曲を外してから追加してください。</p>
        <div class="equipped-pills"><span v-for="(skill, i) in availableSkills" :key="skill.id">{{ i+1 }}. {{ skill.name }}</span></div>
        <div class="setlist-options"><button v-for="skill in learnedSkills" :key="skill.id" :class="{ chosen: equippedSkillIds.includes(skill.id) }" :aria-pressed="equippedSkillIds.includes(skill.id)" :disabled="!equippedSkillIds.includes(skill.id) && equippedSkillIds.length >= 4" @click="toggleSetlist(skill.id)"><div><small>{{ skillRole(skill) }} · {{ skill.target === 'all' ? '全体' : '単体／自身' }}</small><strong>{{ skill.name }}</strong><p>{{ skill.description }}</p></div><b>{{ equippedSkillIds.includes(skill.id) ? '登録済' : '追加' }}</b></button></div>
      </section>
    </div>

    <!-- スキルカットイン -->
    <div v-if="activeCutin" 
        class="fixed inset-x-0 top-1/3 z-50 flex items-center justify-center pointer-events-none"
        v-motion
        :initial="{ opacity: 0 }"
        :enter="{ opacity: 1 }"
        :leave="{ opacity: 0 }">
        <!-- 横帯グラデーション -->
        <div class="flex items-center gap-6 w-full py-4 px-10 bg-gradient-to-r to-transparent via-black/50"
            :class="activeCutin.color"
            v-motion
            :initial="{ x: -120, skewX: -8 }"
            :enter="{ x: 0, skewX: -8, transition: { duration: 160 } }"
            :leave="{ x: 120, opacity: 0 }">
            <img :src="activeCutin.img" class="w-16 h-16 md:w-24 md:h-24 object-cover rounded-full border-4 border-white shadow-[0_0_20px_rgba(255,255,255,0.8)]">
            <h2 class="text-xl md:text-3xl font-black text-white italic drop-shadow-[0_4px_10px_rgba(0,0,0,0.8)] tracking-wider">
            {{ activeCutin.text }}
            </h2>
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
/* Combat UI: keep art spacious and commands readable on touch screens. */
.battle-layout,.rest-panel{color:#e4e4e7;text-align:left}.floor-heading,.journal-heading,.button-row{display:flex;align-items:center;justify-content:space-between;gap:12px}.floor-heading h2,.rest-panel h2{font-size:clamp(20px,4vw,28px);font-weight:800;color:#fafafa;margin:4px 0}.eyebrow{font-size:10px;letter-spacing:.18em;font-weight:800;color:#f5b74e}.flavor-line{font-size:13px;line-height:1.9;color:#a1a1aa;margin:10px 0 18px}.small-button,.primary-button{border-radius:10px;padding:10px 14px;font-size:12px;font-weight:700;cursor:pointer;line-height:1.5}.small-button{background:#27272a;color:#f4f4f5;border:1px solid #52525b}.primary-button{background:#f4b64f;color:#18181b;border:1px solid #f4b64f}.text-button{color:#e8bb75;font-size:12px;text-decoration:underline;text-underline-offset:3px;cursor:pointer}.help-text{font-size:12px;line-height:1.8;color:#a1a1aa;margin:10px 0}.error-text{color:#fca5a5;font-size:13px;line-height:1.8;margin:10px 0}.intro-panel{padding:20px;background:#1e1c19;border:1px solid #806033;border-radius:16px;margin:12px 0 20px}.intro-panel>p:not(.eyebrow){font-size:14px;line-height:2;margin:12px 0 20px}.button-row{flex-wrap:wrap;justify-content:flex-start}.enemy-stage{display:grid;grid-template-columns:1fr;gap:14px}.enemy-stage.duo{grid-template-columns:repeat(2,minmax(0,1fr))}.enemy-card{display:block;text-align:left;background:#17171a;border:1px solid #38383e;border-radius:16px;overflow:hidden;min-width:0;color:#f4f4f5;transition:border-color .2s,opacity .3s,box-shadow .2s;padding:0}.enemy-card.selected{border-color:#f3b44e;box-shadow:0 0 0 2px #f3b44e33}.enemy-card.acting{border-color:#fb7185;box-shadow:0 0 22px #fb718544}.enemy-card.fallen{opacity:.3;filter:grayscale(1)}.enemy-art{position:relative;height:clamp(250px,46vh,480px);background:radial-gradient(ellipse at top,#343239,#121215);overflow:hidden}.enemy-art>img{width:100%;height:100%;object-fit:contain;display:block}.enemy-stage.duo .enemy-art{height:clamp(240px,38vh,410px)}.trait-label,.target-label,.defeated-label{position:absolute;top:12px;font-size:10px;letter-spacing:.08em;background:#111111bb;border:1px solid #ffffff33;border-radius:6px;padding:4px 8px}.trait-label{left:10px}.target-label{right:10px;background:#e8ad45;color:#141414;font-weight:900}.defeated-label{top:45%;left:50%;transform:translateX(-50%);font-weight:900;font-size:16px}.enemy-caption{position:absolute;bottom:0;left:0;right:0;padding:42px 14px 12px;background:linear-gradient(transparent,#09090bf0);display:flex;justify-content:space-between;align-items:flex-end;gap:8px}.enemy-caption strong{font-size:14px;line-height:1.5;overflow-wrap:anywhere}.enemy-caption>span{font-size:11px;color:#d4d4d8;white-space:nowrap}.health-track{height:5px;background:#3f252b}.health-track>div{height:100%;background:#e55e77;transition:width .25s}.status-row{display:flex;flex-wrap:wrap;gap:4px;min-height:12px;padding:6px 8px}.status-row>span{font-size:10px;color:#dfc99e;background:#ffffff09;border-radius:4px;padding:2px 6px}.battle-journal{background:#151518;border:1px solid #323237;border-radius:12px;padding:12px 16px;margin:14px 0}.journal-heading{margin-bottom:8px}.journal-heading>strong{font-size:12px;color:#e3c088}.battle-journal p{font-size:12px;line-height:1.7;min-height:20px}.expanded-log{max-height:210px;overflow-y:auto}.command-dock{position:relative;background:#111114f5;border:1px solid #444449;border-radius:18px;padding:14px;z-index:10;backdrop-filter:blur(16px);box-shadow:0 -10px 35px #0005;margin-top:12px}.player-strip{display:flex;gap:12px;align-items:center}.player-portrait{position:relative;width:50px;height:50px;flex-shrink:0}.player-portrait>img{width:100%;height:100%;object-fit:cover;border-radius:12px;border:1px solid #c89b52}.player-vitals{flex:1;min-width:0}.player-vitals>strong{font-size:12px;display:block;margin-bottom:6px}.player-vitals small{font-size:10px;color:#a1a1aa;margin-left:5px}.vital-line{display:flex;align-items:center;gap:8px;font-size:10px;margin:4px 0}.vital-line>span{width:20px}.vital-line>b{width:68px;text-align:right;font-variant-numeric:tabular-nums}.vital-track{flex:1;height:5px;background:#303035;border-radius:9px;overflow:hidden}.vital-track>div{height:100%;transition:width .25s}.vital-track.hp>div{background:#65c4a6}.vital-track.mp>div{background:#7caaf2}.base-commands,.skill-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.base-commands>button{background:#303038;border:1px solid #52525b;padding:9px;border-radius:9px;font-size:13px;font-weight:700}.base-commands small{font-weight:400;font-size:10px;color:#a1a1aa;margin-left:4px}.skill-grid>button{background:#1b2331;border:1px solid #394a66;color:#dce7f8;text-align:left;border-radius:10px;padding:9px 11px;min-height:76px}.skill-grid>button>strong{font-size:12px;display:block;line-height:1.4;overflow-wrap:anywhere}.skill-grid>button>small{font-size:10px;line-height:1.4;color:#a6b7d1;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;margin-top:3px}.skill-meta{font-size:9px;display:flex;justify-content:space-between;gap:4px;color:#a8bbda;margin-bottom:3px}.setlist-label{font-size:9px;letter-spacing:.1em;color:#bba77e;margin:10px 0 6px;display:flex;justify-content:space-between}.setlist-label>span{letter-spacing:0;color:#8b8b96}.combat-floats{position:absolute;inset:0;pointer-events:none;display:flex;justify-content:center;align-items:center;z-index:20}.combat-number{position:absolute;font-size:36px;font-weight:900;color:#fff;text-shadow:0 2px 4px #000,0 0 16px #000;animation:float-number .8s ease-out forwards}.combat-number.heal{color:#80ebba}.combat-number.magic{color:#b6a0ff}.combat-number.guard{color:#8ec5ff;font-size:22px}.rest-panel{padding:24px;background:#141416;border:1px solid #343438;border-radius:20px}.reward-tier{padding:16px;border:1px solid #76603c;background:#2b2419;border-radius:12px;display:flex;flex-wrap:wrap;align-items:center;gap:10px}.reward-tier>strong{font-size:22px;color:#f1c579}.reward-tier>span{font-size:12px;color:#d9c5a1}.song-choices{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:16px 0}.song-choices>button{padding:12px;text-align:left;background:#202024;border:1px solid #3f3f46;border-radius:10px;min-width:0}.song-choices strong{display:block;font-size:12px;line-height:1.5;overflow-wrap:anywhere;margin:4px 0}.song-choices small,.song-choices span{font-size:10px;color:#a1a1aa}.chosen{border-color:#e7b467!important;background:#342919!important;color:#f8d699!important}.music-player{width:100%;aspect-ratio:16/9;min-height:210px;background:#09090b;border-radius:12px;overflow:hidden;margin:12px 0}.music-player :deep(iframe){width:100%;height:100%;min-height:210px}.listening-progress{height:6px;background:#303035;border-radius:5px;overflow:hidden;margin-top:18px}.listening-progress>div{height:100%;background:#eabb72;transition:width .2s}.tier-steps{display:grid;grid-template-columns:repeat(3,1fr);font-size:11px;line-height:1.7;color:#71717a;margin:8px 0}.tier-steps>span:nth-child(2){text-align:center}.tier-steps>span:last-child{text-align:right}.tier-steps .reached{color:#ebc286}.growth-box{background:#1c1c20;border:1px solid #38383e;padding:18px;border-radius:14px;margin:20px 0;color:#e4e4e7;text-align:left}.growth-box h3{font-weight:700;font-size:15px;display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap}.growth-box h3>span{font-size:12px;color:#e5bd7e}.stat-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.stat-grid>div{display:flex;justify-content:space-between;align-items:center;padding:8px;background:#26262b;border-radius:8px}.stat-grid span{font-size:10px;color:#a1a1aa}.stat-grid b{display:block;font-size:15px;color:#eee}.stat-grid button{width:40px;height:40px;border:1px solid #547363;border-radius:8px;background:#284237;color:#beebd0;font-size:18px}.equipped-pills{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}.equipped-pills>span{font-size:11px;border:1px solid #6e5939;color:#ebc286;padding:6px 10px;border-radius:20px}.skill-search{display:flex;gap:8px;margin:14px 0}.skill-search input,.skill-search select{min-width:0;border:1px solid #52525b;background:#121214;color:#eee;border-radius:8px;padding:10px;font-size:12px}.skill-search input{flex:1}.learn-list{max-height:360px;overflow-y:auto}.learn-list>div{display:flex;align-items:center;gap:12px;justify-content:space-between;padding:12px 0;border-bottom:1px solid #ffffff0d}.learn-list>div>div{flex:1;min-width:0}.learn-list strong,.setlist-options strong{display:block;font-size:13px}.learn-list p,.setlist-options p{font-size:11px;color:#a1a1aa;line-height:1.6;margin:4px 0}.learn-list small,.setlist-options small{font-size:10px;color:#c5a678}.next-floor{width:100%;padding:16px}.setlist-backdrop{position:fixed;inset:0;background:#000b;backdrop-filter:blur(5px);z-index:90;display:flex;align-items:center;justify-content:center;padding:18px}.setlist-dialog{width:100%;max-width:620px;max-height:85dvh;overflow-y:auto;background:#18181b;border:1px solid #685439;border-radius:18px;padding:22px;color:#eee;box-shadow:0 20px 100px #0009}.setlist-dialog h2{font-size:20px;font-weight:800}.setlist-options{display:grid;gap:8px}.setlist-options>button{display:flex;justify-content:space-between;align-items:center;gap:12px;text-align:left;padding:14px;background:#252529;border:1px solid #45454b;border-radius:10px}.setlist-options b{font-size:11px;white-space:nowrap}.song-library-list{list-style:none;padding:0;margin:18px 0}.song-library-list li{padding:8px 0;border-bottom:1px solid #ffffff15}.song-library-list li>button{width:100%;display:flex;gap:12px;align-items:center;text-align:left;border:1px solid transparent;padding:12px;border-radius:8px}.song-library-list li>button>div{flex:1}.song-library-list strong{display:block;font-size:13px}.song-library-list small{display:block;font-size:10px;color:#a1a1aa;margin-top:5px}.song-library-list li>a{display:inline-block;margin-left:42px}.music-library{margin-bottom:28px}
button:disabled{cursor:not-allowed}.base-commands>button:disabled,.skill-grid>button:disabled,.small-button:disabled,.primary-button:disabled,.stat-grid button:disabled,.setlist-options>button:disabled{opacity:.4}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid #f3bc61;outline-offset:3px}.anim-magic{animation:magic-hit .42s ease-out}.anim-guard{animation:guard-glow .5s ease-out}
@keyframes float-number{0%{opacity:0;transform:translateY(15px) scale(.7)}20%{opacity:1;transform:translateY(0) scale(1.12)}75%{opacity:1}100%{opacity:0;transform:translateY(-45px) scale(1)}}
@keyframes magic-hit{0%,100%{filter:none}35%{filter:brightness(1.8) drop-shadow(0 0 18px #aa88ff)}}
@keyframes guard-glow{0%,100%{filter:none}40%{filter:drop-shadow(0 0 14px #80baff)}}
@media(max-width:540px){.command-dock{padding:10px;bottom:4px}.enemy-stage{gap:8px}.enemy-caption{padding:30px 9px 10px;flex-wrap:wrap;gap:3px}.enemy-caption strong{font-size:12px}.trait-label,.target-label{font-size:8px;padding:3px 5px;top:8px}.trait-label{left:6px}.target-label{right:6px}.rest-panel{padding:16px}.song-choices{grid-template-columns:1fr}.song-choices>button{padding:10px 12px}.song-choices strong{margin:2px 0}.growth-box{padding:14px}.base-commands small{display:block;margin:0}.floor-heading{align-items:flex-start}.floor-heading .small-button{font-size:10px;padding:7px;white-space:nowrap}.setlist-dialog{padding:16px}.skill-grid>button{min-height:82px;padding:8px}.music-library .button-row{gap:6px}}
@media(max-height:620px){.command-dock{position:static}}
@media(prefers-reduced-motion:reduce){.anim-damage,.anim-magic,.anim-guard,.combat-number{animation-duration:.01ms!important}.enemy-card,.health-track>div,.vital-track>div{transition:none}}

.clear-title{overflow-wrap:anywhere;line-height:1.3}
.song-library-list li>button>div{min-width:0;overflow-wrap:anywhere}
</style>