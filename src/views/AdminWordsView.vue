<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import WordCard from '../words/WordCard.vue'
import { adminApi, AdminApiError, type AdminWord, type WordStatus } from '../words/adminApi'
import { resizeImage } from '../words/imageResize'
import { commentToHtml } from '../words/commentFormat'
import {
  SOURCE_KIND_LABELS, TEMPLATE_LABELS, sourceLine,
  type BubbleShape, type BubbleTail, type SourceKind, type WordEntry, type WordTemplate
} from '../words/types'

// -----------------------------------------------------------------------------
// 状態
// -----------------------------------------------------------------------------
const words = ref<AdminWord[]>([])
const email = ref('')
const loading = ref(true)
const authProblem = ref<'' | 'login' | 'forbidden' | 'setup'>('')
const listError = ref('')
const statusFilter = ref<'all' | WordStatus>('all')
const mobilePane = ref<'list' | 'edit'>('list')

const saving = ref(false)
const uploading = ref(false)
const message = ref<{ text: string; kind: 'ok' | 'error' } | null>(null)
const replayKey = ref(0)

const templates = Object.keys(TEMPLATE_LABELS) as WordTemplate[]
const kinds = Object.keys(SOURCE_KIND_LABELS) as SourceKind[]
const SHAPES: { value: BubbleShape; label: string }[] = [
  { value: 'round', label: '普通' }, { value: 'shout', label: '叫び' },
  { value: 'thought', label: '心の声' }, { value: 'whisper', label: 'ささやき' }
]
const TAILS: { value: BubbleTail; label: string }[] = [
  { value: 'bottom-left', label: '左下' }, { value: 'bottom-right', label: '右下' },
  { value: 'left', label: '左' }, { value: 'right', label: '右' }, { value: 'none', label: 'なし' }
]

// 編集中のフォーム（保存済みの内容と比べて、未保存の変更を判定する）
interface Form extends Omit<AdminWord, 'createdAt' | 'updatedAt'> { tagsText: string }

const blankForm = (): Form => ({
  id: '',
  status: 'draft',
  sortOrder: 0,
  quote: '',
  speaker: '',
  source: { title: '', author: '', kind: 'manga', detail: '', url: '' },
  image: '',
  imageAlt: '',
  template: 'bubble',
  options: {
    fontScale: 1,
    focus: { x: 50, y: 40 },
    bubble: { x: 6, y: 6, width: 30, height: 30, shape: 'round', tail: 'bottom-right' }
  },
  comment: '',
  tags: [],
  tagsText: '',
  spoiler: false
})

const form = reactive<Form>(blankForm())
const savedSnapshot = ref(JSON.stringify(blankForm()))
const isNew = computed(() => !form.id)
const dirty = computed(() => JSON.stringify(form) !== savedSnapshot.value)
const editing = ref(false)

function fillForm(word: AdminWord | null) {
  const base = blankForm()
  const w = word ?? null
  Object.assign(form, base, w ? {
    ...w,
    speaker: w.speaker ?? '',
    source: { ...base.source, ...w.source },
    options: {
      ...base.options,
      ...w.options,
      focus: { ...base.options!.focus!, ...(w.options?.focus ?? {}) },
      bubble: { ...base.options!.bubble!, ...(w.options?.bubble ?? {}) }
    },
    comment: w.comment ?? '',
    tags: w.tags ?? [],
    tagsText: (w.tags ?? []).join('、')
  } : {})
  delete (form as Partial<AdminWord>).createdAt
  delete (form as Partial<AdminWord>).updatedAt
  savedSnapshot.value = JSON.stringify(form)
  message.value = null
}

// -----------------------------------------------------------------------------
// 読み込み
// -----------------------------------------------------------------------------
async function load() {
  loading.value = true
  listError.value = ''
  authProblem.value = ''
  try {
    const data = await adminApi.list()
    words.value = data.words
    email.value = data.email
  } catch (e) {
    if (e instanceof AdminApiError && e.status === 401) authProblem.value = 'login'
    else if (e instanceof AdminApiError && e.status === 403) authProblem.value = 'forbidden'
    else if (e instanceof AdminApiError && e.status === 503) { authProblem.value = 'setup'; listError.value = e.message }
    else listError.value = e instanceof Error ? e.message : '読み込みに失敗しました。'
  } finally {
    loading.value = false
  }
}

const visibleWords = computed(() =>
  statusFilter.value === 'all' ? words.value : words.value.filter(w => w.status === statusFilter.value)
)
const counts = computed(() => ({
  all: words.value.length,
  draft: words.value.filter(w => w.status === 'draft').length,
  published: words.value.filter(w => w.status === 'published').length
}))

function confirmDiscard() {
  return !editing.value || !dirty.value || window.confirm('保存していない変更があります。破棄してよいですか？')
}

function startNew() {
  if (!confirmDiscard()) return
  fillForm(null)
  editing.value = true
  mobilePane.value = 'edit'
}

function select(word: AdminWord) {
  if (form.id === word.id && editing.value) { mobilePane.value = 'edit'; return }
  if (!confirmDiscard()) return
  fillForm(word)
  editing.value = true
  mobilePane.value = 'edit'
}

function backToList() {
  mobilePane.value = 'list'
}

// -----------------------------------------------------------------------------
// プレビュー
// -----------------------------------------------------------------------------
const PLACEHOLDER = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" fill="#26262b"/>' +
  '<text x="200" y="250" fill="#8b8b96" font-size="22" text-anchor="middle" font-family="sans-serif">画像を選んでください</text></svg>'
)

const previewEntry = computed<WordEntry>(() => {
  const { tagsText: _t, status: _s, sortOrder: _o, ...rest } = form
  return {
    ...rest,
    id: form.id || 'preview',
    quote: form.quote || '言葉をここに\n入力してください',
    speaker: form.speaker || undefined,
    image: form.image || PLACEHOLDER,
    source: { ...form.source, title: form.source.title || '作品名' }
  } as WordEntry
})

// ひとことのプレビュー（公開ページと同じ変換）
const showCommentPreview = ref(false)
const commentPreviewHtml = computed(() => commentToHtml(form.comment))

const usesBubble = computed(() => form.template === 'bubble' || form.template === 'manga')
// 縦書きを切り替えられるのは吹き出し・漫画・文庫本（便箋は常に縦書き、ゲーム窓と歌詞カードは横書き）
const canVertical = computed(() => ['bubble', 'manga', 'bunko'].includes(form.template))
const isVertical = computed(() => form.options!.vertical ?? (form.template === 'manga' || form.template === 'bunko'))

function setVertical(value: boolean) {
  form.options!.vertical = value
}

// 吹き出しをドラッグで動かす
const previewBox = ref<HTMLElement | null>(null)
let drag: { startX: number; startY: number; x: number; y: number; w: number; h: number; id: number } | null = null

function onPreviewPointerDown(e: PointerEvent) {
  if (!usesBubble.value) return
  const bubbleEl = (e.target as HTMLElement).closest('.bubble-box') as HTMLElement | null
  const parent = bubbleEl?.offsetParent as HTMLElement | null
  if (!bubbleEl || !parent) return
  const rect = parent.getBoundingClientRect()
  const b = form.options!.bubble!
  drag = { startX: e.clientX, startY: e.clientY, x: b.x, y: b.y, w: rect.width, h: rect.height, id: e.pointerId }
  previewBox.value?.setPointerCapture(e.pointerId)
  e.preventDefault()
}
function onPreviewPointerMove(e: PointerEvent) {
  if (!drag || e.pointerId !== drag.id) return
  const b = form.options!.bubble!
  b.x = Math.round(Math.max(-5, Math.min(90, drag.x + (e.clientX - drag.startX) / drag.w * 100)) * 10) / 10
  b.y = Math.round(Math.max(-5, Math.min(90, drag.y + (e.clientY - drag.startY) / drag.h * 100)) * 10) / 10
}
function onPreviewPointerUp(e: PointerEvent) {
  if (drag && e.pointerId === drag.id) drag = null
}

// -----------------------------------------------------------------------------
// 画像
// -----------------------------------------------------------------------------
const fileInput = ref<HTMLInputElement | null>(null)

async function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  uploading.value = true
  message.value = null
  try {
    const resized = await resizeImage(file)
    // 新しい言葉はまず下書きとして保存し、IDを決めてから画像を送る
    if (isNew.value) {
      const saved = await saveCore('draft-for-image')
      if (!saved) return
    }
    const { word } = await adminApi.uploadImage(form.id, resized.blob, resized.type)
    form.image = word.image
    upsert(word)
    // 画像だけ保存済みになったので、スナップショットの画像も更新する
    const snap = JSON.parse(savedSnapshot.value)
    snap.image = word.image
    savedSnapshot.value = JSON.stringify(snap)
    flash(`画像をアップロードしました（${resized.width}×${resized.height}・${Math.round(resized.blob.size / 1024)}KB）`)
  } catch (err) {
    handleError(err)
  } finally {
    uploading.value = false
  }
}

// -----------------------------------------------------------------------------
// 保存・削除
// -----------------------------------------------------------------------------
function payload(statusOverride?: WordStatus): Partial<AdminWord> {
  const tags = form.tagsText.split(/[、,\s]+/).map(t => t.replace(/^#/, '').trim()).filter(Boolean)
  return {
    id: form.id || undefined,
    status: statusOverride ?? form.status,
    sortOrder: Number(form.sortOrder) || 0,
    quote: form.quote,
    speaker: form.speaker || undefined,
    source: { ...form.source },
    image: form.image,
    imageAlt: form.imageAlt,
    template: form.template,
    options: JSON.parse(JSON.stringify(form.options)),
    comment: form.comment,
    tags,
    spoiler: form.spoiler
  }
}

function upsert(word: AdminWord) {
  const i = words.value.findIndex(w => w.id === word.id)
  if (i >= 0) words.value.splice(i, 1, word)
  else words.value.unshift(word)
}

async function saveCore(mode: 'normal' | 'draft-for-image' = 'normal') {
  saving.value = true
  message.value = null
  try {
    const body = payload(mode === 'draft-for-image' && isNew.value ? 'draft' : undefined)
    const { word } = isNew.value ? await adminApi.create(body) : await adminApi.update(form.id, body)
    upsert(word)
    const keepTags = form.tagsText
    fillForm(word)
    if (mode === 'draft-for-image') form.tagsText = keepTags
    return word
  } catch (err) {
    handleError(err)
    return null
  } finally {
    saving.value = false
  }
}

async function save() {
  if (!form.quote.trim()) { flash('言葉を入力してください。', 'error'); return }
  const word = await saveCore()
  if (word) flash(word.status === 'published' ? '保存しました（公開中）' : '下書きとして保存しました')
}

async function togglePublish() {
  form.status = form.status === 'published' ? 'draft' : 'published'
  const word = await saveCore()
  if (word) flash(word.status === 'published' ? '公開しました' : '下書きに戻しました')
  else form.status = form.status === 'published' ? 'draft' : 'published'
}

async function remove() {
  if (isNew.value) { fillForm(null); editing.value = false; mobilePane.value = 'list'; return }
  if (!window.confirm(`「${form.quote.split('\n')[0]}」を削除します。元に戻せません。よろしいですか？`)) return
  try {
    await adminApi.remove(form.id)
    words.value = words.value.filter(w => w.id !== form.id)
    fillForm(null)
    editing.value = false
    mobilePane.value = 'list'
    flash('削除しました')
  } catch (err) {
    handleError(err)
  }
}

let flashTimer: ReturnType<typeof setTimeout> | null = null
function flash(text: string, kind: 'ok' | 'error' = 'ok') {
  message.value = { text, kind }
  if (flashTimer) clearTimeout(flashTimer)
  if (kind === 'ok') flashTimer = setTimeout(() => { message.value = null }, 3500)
}
function handleError(err: unknown) {
  if (err instanceof AdminApiError && err.status === 401) { authProblem.value = 'login'; return }
  flash(err instanceof Error ? err.message : '保存に失敗しました。', 'error')
}

function relogin() {
  window.location.reload()
}

// 未保存のまま閉じようとしたら確認する
function onBeforeUnload(e: BeforeUnloadEvent) {
  if (editing.value && dirty.value) { e.preventDefault(); e.returnValue = '' }
}

// Ctrl/⌘ + S で保存
function onKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's' && editing.value) {
    e.preventDefault()
    void save()
  }
}

// 検索エンジンに載せない
let robotsMeta: HTMLMetaElement | null = null
onMounted(() => {
  robotsMeta = document.createElement('meta')
  robotsMeta.name = 'robots'
  robotsMeta.content = 'noindex, nofollow'
  document.head.appendChild(robotsMeta)
  window.addEventListener('beforeunload', onBeforeUnload)
  window.addEventListener('keydown', onKeydown)
  void load()
})
onBeforeUnmount(() => {
  robotsMeta?.remove()
  window.removeEventListener('beforeunload', onBeforeUnload)
  window.removeEventListener('keydown', onKeydown)
})

// テンプレートを変えたら、アニメーションも見直せるよう再生し直す
watch(() => form.template, () => { replayKey.value++ })
</script>

<template>
  <div class="admin">
    <header class="admin-bar">
      <div>
        <p class="eyebrow">ADMIN</p>
        <h1>言葉の管理</h1>
      </div>
      <div class="bar-actions">
        <span v-if="email" class="who">{{ email }}</span>
        <router-link to="/words" class="ghost">公開ページ ↗</router-link>
        <button class="primary" :disabled="!!authProblem || loading" @click="startNew">＋ 新しい言葉</button>
      </div>
    </header>

    <!-- ログイン・設定の問題 -->
    <section v-if="authProblem" class="notice" role="alert">
      <template v-if="authProblem === 'login'">
        <h2>ログインが必要です</h2>
        <p>管理ページは Cloudflare Access で守られています。ページを読み込み直すと、ログイン画面が開きます。</p>
        <button class="primary" @click="relogin">ログインする</button>
      </template>
      <template v-else-if="authProblem === 'forbidden'">
        <h2>このアカウントでは管理できません</h2>
        <p>許可されたメールアドレスでログインし直してください。</p>
      </template>
      <template v-else>
        <h2>まだ準備ができていません</h2>
        <p>{{ listError }}</p>
        <p class="hint">D1 と Cloudflare Access の設定手順を参考に、wrangler.toml を設定してください。</p>
      </template>
    </section>

    <p v-else-if="loading" class="hint">読み込んでいます…</p>
    <p v-else-if="listError" class="notice error" role="alert">{{ listError }} <button class="ghost" @click="load">再試行</button></p>

    <div v-else class="workspace" :class="`pane-${mobilePane}`">
      <!-- 一覧 -->
      <aside class="list-pane">
        <div class="tabs" role="group" aria-label="状態で絞り込む">
          <button :class="{ active: statusFilter === 'all' }" @click="statusFilter = 'all'">すべて {{ counts.all }}</button>
          <button :class="{ active: statusFilter === 'draft' }" @click="statusFilter = 'draft'">下書き {{ counts.draft }}</button>
          <button :class="{ active: statusFilter === 'published' }" @click="statusFilter = 'published'">公開中 {{ counts.published }}</button>
        </div>
        <p v-if="!visibleWords.length" class="hint">まだありません。「＋ 新しい言葉」から追加できます。</p>
        <ul class="word-list">
          <li v-for="w in visibleWords" :key="w.id">
            <button :class="{ current: w.id === form.id && editing }" @click="select(w)">
              <span class="thumb">
                <img v-if="w.image" :src="w.image" alt="">
                <span v-else class="no-image">画像なし</span>
              </span>
              <span class="meta">
                <span class="badge" :class="w.status">{{ w.status === 'published' ? '公開中' : '下書き' }}</span>
                <strong>{{ w.quote.split('\n').join(' ') }}</strong>
                <small>{{ sourceLine(w) }} · {{ TEMPLATE_LABELS[w.template] }}</small>
              </span>
            </button>
          </li>
        </ul>
      </aside>

      <!-- 編集 -->
      <section v-if="editing" class="edit-pane">
        <div class="edit-head">
          <button class="ghost back" @click="backToList">← 一覧</button>
          <span class="badge" :class="form.status">{{ form.status === 'published' ? '公開中' : '下書き' }}</span>
          <span v-if="dirty" class="dirty">未保存の変更があります</span>
        </div>

        <div class="edit-grid">
          <!-- プレビュー -->
          <div class="preview-col">
            <div
              ref="previewBox"
              class="preview"
              :class="{ draggable: usesBubble }"
              @pointerdown="onPreviewPointerDown"
              @pointermove="onPreviewPointerMove"
              @pointerup="onPreviewPointerUp"
              @pointercancel="onPreviewPointerUp"
            >
              <WordCard :key="replayKey" :entry="previewEntry" animate />
            </div>
            <div class="preview-tools">
              <button class="ghost" @click="replayKey++">▶ アニメーションを再生</button>
              <span v-if="usesBubble" class="hint">吹き出しはドラッグで動かせます</span>
            </div>

            <fieldset class="block">
              <legend>テンプレート</legend>
              <div class="template-picker">
                <button v-for="t in templates" :key="t" :class="{ chosen: form.template === t }" :aria-pressed="form.template === t" @click="form.template = t">
                  <WordCard :entry="previewEntry" :template="t" />
                  <span>{{ TEMPLATE_LABELS[t] }}</span>
                </button>
              </div>
            </fieldset>
          </div>

          <!-- 入力 -->
          <div class="form-col">
            <fieldset class="block">
              <legend>言葉</legend>
              <label class="field">
                <span>言葉 <small>改行はそのまま反映されます</small></span>
                <textarea v-model="form.quote" rows="4" maxlength="1000" placeholder="心に残った言葉"></textarea>
              </label>
              <label class="field">
                <span>言った人 <small>任意</small></span>
                <input v-model="form.speaker" maxlength="100" placeholder="キャラクター名など">
              </label>
            </fieldset>

            <fieldset class="block">
              <legend>出典</legend>
              <div class="row">
                <label class="field">
                  <span>種類</span>
                  <select v-model="form.source.kind">
                    <option v-for="k in kinds" :key="k" :value="k">{{ SOURCE_KIND_LABELS[k] }}</option>
                  </select>
                </label>
                <label class="field grow">
                  <span>作品名</span>
                  <input v-model="form.source.title" maxlength="200" placeholder="作品名">
                </label>
              </div>
              <label class="field">
                <span>作者・作詞者など</span>
                <input v-model="form.source.author" maxlength="200">
              </label>
              <label class="field">
                <span>巻・話数・収録など <small>任意</small></span>
                <input v-model="form.source.detail" maxlength="200" placeholder="第3巻 第21話 など">
              </label>
              <label class="field">
                <span>公式ページのURL <small>任意</small></span>
                <input v-model="form.source.url" type="url" maxlength="500" placeholder="https://">
              </label>
            </fieldset>

            <fieldset class="block">
              <legend>画像</legend>
              <div class="image-row">
                <span class="thumb large">
                  <img v-if="form.image" :src="form.image" alt="">
                  <span v-else class="no-image">未設定</span>
                </span>
                <div class="image-actions">
                  <input ref="fileInput" type="file" accept="image/*" class="visually-hidden" @change="onFileChange">
                  <button class="primary" :disabled="uploading || saving" @click="fileInput?.click()">
                    {{ uploading ? 'アップロード中…' : form.image ? '画像を差し替える' : '画像を選ぶ' }}
                  </button>
                  <p class="hint">自動で縮小して WebP にします（横1200pxまで）。</p>
                </div>
              </div>
              <label class="field">
                <span>画像の説明 <small>公開に必要。読み上げや画像が出ないときに使われます</small></span>
                <input v-model="form.imageAlt" maxlength="300" placeholder="例：夕暮れの海辺で、エリカが向日葵を差し出している">
              </label>
              <div class="row">
                <label class="field grow">
                  <span>見せる位置（横） {{ form.options!.focus!.x }}%</span>
                  <input v-model.number="form.options!.focus!.x" type="range" min="0" max="100">
                </label>
                <label class="field grow">
                  <span>見せる位置（縦） {{ form.options!.focus!.y }}%</span>
                  <input v-model.number="form.options!.focus!.y" type="range" min="0" max="100">
                </label>
              </div>
            </fieldset>

            <fieldset class="block">
              <legend>見た目の調整</legend>
              <div class="row">
                <label class="field">
                  <span>差し色</span>
                  <input v-model="form.options!.accent" type="color">
                </label>
                <label class="field grow">
                  <span>文字の大きさ ×{{ (form.options!.fontScale ?? 1).toFixed(2) }}</span>
                  <input v-model.number="form.options!.fontScale" type="range" min="0.6" max="1.6" step="0.05">
                </label>
              </div>
              <label v-if="canVertical" class="check">
                <input type="checkbox" :checked="isVertical" @change="setVertical(($event.target as HTMLInputElement).checked)">
                縦書きにする
              </label>

              <template v-if="usesBubble">
                <div class="row">
                  <label class="field grow">
                    <span>吹き出しの形</span>
                    <select v-model="form.options!.bubble!.shape">
                      <option v-for="s in SHAPES" :key="s.value" :value="s.value">{{ s.label }}</option>
                    </select>
                  </label>
                  <label class="field grow">
                    <span>しっぽの向き</span>
                    <select v-model="form.options!.bubble!.tail">
                      <option v-for="t in TAILS" :key="t.value" :value="t.value">{{ t.label }}</option>
                    </select>
                  </label>
                </div>
                <div class="row">
                  <label class="field grow">
                    <span>位置（横） {{ form.options!.bubble!.x }}%</span>
                    <input v-model.number="form.options!.bubble!.x" type="range" min="-5" max="90" step="0.5">
                  </label>
                  <label class="field grow">
                    <span>位置（縦） {{ form.options!.bubble!.y }}%</span>
                    <input v-model.number="form.options!.bubble!.y" type="range" min="-5" max="90" step="0.5">
                  </label>
                </div>
              </template>

              <label v-if="form.template === 'lyric'" class="field">
                <span>曲名 <small>未入力なら作品名</small></span>
                <input v-model="form.options!.songTitle" maxlength="100">
              </label>
              <label v-if="form.template === 'game'" class="field">
                <span>名前欄 <small>未入力なら「エリカ」</small></span>
                <input v-model="form.options!.speakerName" maxlength="30">
              </label>
            </fieldset>

            <fieldset class="block">
              <legend>エリカのひとこと</legend>
              <label class="field">
                <span>なぜこの言葉が好きか <small>ページの主役になる文章です</small></span>
                <textarea v-model="form.comment" rows="10" maxlength="4000"></textarea>
              </label>
              <details class="format-help">
                <summary>書き方（改行・見出し・太字など）</summary>
                <ul>
                  <li>改行はそのまま改行になります。空行を入れると段落が分かれます</li>
                  <li><code>■ 見出し</code> の行は小見出しになります（□ ◆ も可）。<code># 見出し</code>（少し大きめ）、<code>## 見出し</code> も使えます</li>
                  <li><code>**太字**</code>、<code>- 箇条書き</code>、<code>&gt; 引用</code>、<code>[文字](https://…)</code> が使えます</li>
                </ul>
              </details>
              <button type="button" class="ghost small" :aria-expanded="showCommentPreview" @click="showCommentPreview = !showCommentPreview">
                {{ showCommentPreview ? 'プレビューを閉じる' : '公開ページでの見え方を確認する' }}
              </button>
              <!-- commentPreviewHtml は DOMPurify で無害化済み -->
              <div v-if="showCommentPreview" class="comment-preview" v-html="commentPreviewHtml || '<p>（まだ書かれていません）</p>'"></div>
            </fieldset>

            <fieldset class="block">
              <legend>その他</legend>
              <label class="field">
                <span>タグ <small>「、」かスペースで区切る</small></span>
                <input v-model="form.tagsText" placeholder="熱い、決意">
              </label>
              <div class="row">
                <label class="check grow">
                  <input v-model="form.spoiler" type="checkbox">
                  ネタバレを含む（一覧ではぼかす）
                </label>
                <label class="field">
                  <span>並び順 <small>大きいほど先頭</small></span>
                  <input v-model.number="form.sortOrder" type="number" step="1" class="narrow">
                </label>
              </div>
            </fieldset>
          </div>
        </div>

        <!-- 操作 -->
        <div class="actions">
          <button class="danger" :disabled="saving" @click="remove">{{ isNew ? '破棄' : '削除' }}</button>
          <span class="spacer"></span>
          <button class="ghost" :disabled="saving || uploading" @click="save">{{ saving ? '保存中…' : '保存' }}</button>
          <button class="primary" :disabled="saving || uploading" @click="togglePublish">
            {{ form.status === 'published' ? '下書きに戻す' : '公開する' }}
          </button>
        </div>
        <p v-if="message" class="toast" :class="message.kind" role="status">{{ message.text }}</p>
      </section>

      <section v-else class="edit-pane empty">
        <p class="hint">左の一覧から選ぶか、「＋ 新しい言葉」で追加します。</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.admin {
  --accent: #f3a43b;
  --line: rgba(255, 255, 255, 0.12);
  --surface: #18191d;
  --muted: #a1a1aa;
  min-height: 100vh;
  padding: 84px 16px 120px;
  background: #0e0f11;
  color: #f4f4f5;
}
.admin-bar {
  max-width: 1280px;
  margin: 0 auto 20px;
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}
.eyebrow { font-size: 11px; letter-spacing: 0.2em; color: var(--accent); margin: 0; }
h1 { font-size: 24px; font-weight: 800; margin: 2px 0 0; }
.bar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }
.who { font-size: 12px; color: var(--muted); }
.primary, .ghost, .danger {
  border-radius: 10px;
  padding: 9px 14px;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.4;
}
.primary { background: var(--accent); color: #141414; }
.ghost { border: 1px solid var(--line); color: #e4e4e7; }
.danger { border: 1px solid #7f1d1d; color: #fca5a5; }
button:disabled { opacity: 0.45; cursor: not-allowed; }
.notice {
  max-width: 640px;
  margin: 40px auto;
  padding: 24px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 14px;
}
.notice h2 { font-size: 18px; font-weight: 800; margin: 0 0 8px; }
.notice p { color: var(--muted); line-height: 1.8; }
.notice.error { color: #fca5a5; }
.hint { font-size: 12px; color: var(--muted); line-height: 1.7; }
.workspace {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}
.list-pane {
  position: sticky;
  top: 80px;
  max-height: calc(100vh - 100px);
  overflow-y: auto;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 12px;
}
.tabs { display: flex; gap: 6px; margin-bottom: 10px; }
.tabs button {
  flex: 1;
  padding: 6px 4px;
  font-size: 12px;
  border-radius: 8px;
  border: 1px solid var(--line);
  color: var(--muted);
}
.tabs button.active { background: #2a2b31; color: #fff; border-color: #52525b; }
.word-list { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
.word-list button {
  width: 100%;
  display: flex;
  gap: 10px;
  align-items: center;
  text-align: left;
  padding: 8px;
  border-radius: 10px;
  border: 1px solid transparent;
}
.word-list button:hover { background: #222329; }
.word-list button.current { border-color: var(--accent); background: #26221a; }
.thumb {
  flex-shrink: 0;
  width: 48px;
  aspect-ratio: 4 / 5;
  border-radius: 6px;
  overflow: hidden;
  background: #2a2b31;
  display: grid;
  place-items: center;
}
.thumb img { width: 100%; height: 100%; object-fit: cover; }
.thumb.large { width: 96px; }
.no-image { font-size: 10px; color: var(--muted); text-align: center; }
.meta { min-width: 0; display: grid; gap: 2px; }
.meta strong { font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.meta small { font-size: 11px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.badge {
  justify-self: start;
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 999px;
  border: 1px solid #52525b;
  color: var(--muted);
}
.badge.published { border-color: #15803d; color: #86efac; background: #052e1666; }
.edit-pane {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 16px 18px 0;
  min-width: 0;
}
.edit-pane.empty { padding: 40px; text-align: center; }
.edit-head { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; }
.back { display: none; }
.dirty { font-size: 12px; color: #fbbf24; }
.edit-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1fr);
  gap: 22px;
  align-items: start;
}
.preview-col { position: sticky; top: 80px; }
.preview { border-radius: 12px; box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5); }
.preview.draggable :deep(.bubble-box) { cursor: grab; touch-action: none; }
.preview.draggable :deep(.bubble-box:active) { cursor: grabbing; }
.preview-tools { display: flex; flex-wrap: wrap; align-items: center; gap: 10px; margin: 10px 0 4px; }
.block {
  border: 0;
  border-top: 1px solid var(--line);
  margin: 0;
  padding: 14px 0 6px;
}
.block legend { font-size: 13px; font-weight: 800; color: var(--accent); padding: 0 8px 0 0; }
.template-picker { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.template-picker button { display: grid; gap: 4px; text-align: center; font-size: 11px; color: var(--muted); border-radius: 10px; padding: 3px; border: 2px solid transparent; }
.template-picker button.chosen { border-color: var(--accent); color: #fff; font-weight: 700; }
.field { display: grid; gap: 5px; margin-bottom: 12px; font-size: 13px; }
.field > span small, .field small { font-size: 11px; color: var(--muted); font-weight: 400; margin-left: 6px; }
.field input:not([type='range']):not([type='color']), .field textarea, .field select {
  width: 100%;
  background: #0f1013;
  border: 1px solid #3f3f46;
  border-radius: 8px;
  padding: 9px 10px;
  color: #f4f4f5;
  font-size: 15px;
  line-height: 1.6;
}
.field textarea { resize: vertical; }
.field input[type='color'] { width: 48px; height: 38px; padding: 2px; background: none; border: 1px solid #3f3f46; border-radius: 8px; }
.field input[type='range'] { width: 100%; accent-color: var(--accent); }
.narrow { max-width: 110px; }
.row { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; }
.grow { flex: 1 1 180px; }
.check { display: flex; align-items: center; gap: 8px; font-size: 13px; margin-bottom: 12px; }
.check input { width: 18px; height: 18px; accent-color: var(--accent); }
.image-row { display: flex; gap: 14px; align-items: center; margin-bottom: 12px; }
.image-actions { display: grid; gap: 4px; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.actions {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px -18px 0;
  padding: 12px 18px;
  background: rgba(24, 25, 29, 0.96);
  border-top: 1px solid var(--line);
  border-radius: 0 0 14px 14px;
  backdrop-filter: blur(8px);
}
.spacer { flex: 1; }
.toast {
  position: fixed;
  left: 50%;
  bottom: 84px;
  transform: translateX(-50%);
  z-index: 70;
  max-width: calc(100% - 32px);
  padding: 10px 16px;
  border-radius: 10px;
  font-size: 13px;
  background: #14532d;
  color: #dcfce7;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}
.toast.error { background: #7f1d1d; color: #fee2e2; }
@media (max-width: 1100px) {
  .edit-grid { grid-template-columns: 1fr; }
  .preview-col { position: static; max-width: 460px; }
}
@media (max-width: 820px) {
  .workspace { grid-template-columns: 1fr; }
  .list-pane { position: static; max-height: none; }
  .pane-edit .list-pane { display: none; }
  .pane-list .edit-pane { display: none; }
  .back { display: inline-block; }
  .template-picker { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .preview-col { max-width: none; }
}
.format-help { font-size: 12px; color: var(--muted); margin: -4px 0 10px; }
.format-help summary { cursor: pointer; }
.format-help ul { margin: 6px 0 0; padding-left: 1.2em; list-style: disc; line-height: 1.9; }
.format-help code { background: #0f1013; border: 1px solid #3f3f46; border-radius: 4px; padding: 0 4px; font-size: 11px; }
.ghost.small { font-size: 12px; padding: 5px 10px; }
.comment-preview {
  margin-top: 10px;
  padding: 14px 16px;
  background: #1d1f25;
  border-left: 3px solid var(--accent);
  border-radius: 0 10px 10px 0;
  font-size: 14px;
  line-height: 2;
  overflow-wrap: anywhere;
}
.comment-preview :deep(p) { margin: 0 0 1em; }
.comment-preview :deep(> :last-child) { margin-bottom: 0; }
.comment-preview :deep(h1), .comment-preview :deep(h2), .comment-preview :deep(h3), .comment-preview :deep(h4) { margin: 1.4em 0 0.4em; font-size: 14px; font-weight: 800; color: #fff; }
.comment-preview :deep(h1) { font-size: 16px; }
.comment-preview :deep(:is(h1, h2, h3, h4)::before) { content: '■ '; color: var(--accent); }
.comment-preview :deep(> :is(h1, h2, h3, h4):first-child) { margin-top: 0; }
.comment-preview :deep(strong) { color: #fff; }
.comment-preview :deep(ul) { list-style: disc; padding-left: 1.4em; margin: 0 0 1em; }
.comment-preview :deep(ol) { list-style: decimal; padding-left: 1.4em; margin: 0 0 1em; }
.comment-preview :deep(blockquote) { margin: 0 0 1em; padding: 8px 12px; background: rgba(255, 255, 255, 0.04); border-radius: 8px; }
.comment-preview :deep(a) { color: var(--accent); text-decoration: underline; }
</style>
