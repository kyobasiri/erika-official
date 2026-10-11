<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import StaticPageLayout from '../components/StaticPageLayout.vue'
import WordCard from '../words/WordCard.vue'
import {
  SOURCE_KIND_LABELS, TEMPLATE_LABELS, sourceLine,
  type SourceKind, type WordEntry, type WordTemplate
} from '../words/types'

const route = useRoute()
const router = useRouter()

const words = ref<WordEntry[]>([])
const loading = ref(true)
const loadError = ref('')
const kindFilter = ref<'all' | SourceKind>('all')

async function loadWords() {
  loading.value = true
  loadError.value = ''
  try {
    // 管理ページ（D1）の API から読む。
    // 開発中（npm run dev）は API が無いので、同梱のサンプルを使う。本番ではサンプルを出さない。
    let data: unknown = null
    try {
      const res = await fetch('/api/words')
      if (res.ok) data = await res.json()
    } catch {
      // 下で扱う
    }
    if (!Array.isArray(data) && !import.meta.env.DEV) throw new Error('API から読み込めませんでした')
    if (!Array.isArray(data)) {
      const res = await fetch('/assets/words.json', { cache: 'no-cache' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      data = await res.json()
    }
    if (!Array.isArray(data)) throw new Error('形式が正しくありません')
    words.value = data as WordEntry[]
  } catch {
    loadError.value = '言葉を読み込めませんでした。時間をおいて再度お試しください。'
  } finally {
    loading.value = false
  }
}

const kinds = computed(() => {
  const present = new Set(words.value.map(w => w.source.kind))
  return (Object.keys(SOURCE_KIND_LABELS) as SourceKind[]).filter(k => present.has(k))
})

const visibleWords = computed(() =>
  kindFilter.value === 'all' ? words.value : words.value.filter(w => w.source.kind === kindFilter.value)
)

// --- 詳細表示（?id= と同期） ---
const selectedId = computed(() => (typeof route.query.id === 'string' ? route.query.id : ''))
const selected = computed(() => words.value.find(w => w.id === selectedId.value) ?? null)
const selectedIndex = computed(() => visibleWords.value.findIndex(w => w.id === selectedId.value))
const compareMode = ref(false)
const templates = Object.keys(TEMPLATE_LABELS) as WordTemplate[]
const spoilerOpen = ref(false)
const dialog = ref<HTMLElement | null>(null)
let returnFocus: HTMLElement | null = null

function open(entry: WordEntry) {
  returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
  router.push({ query: { ...route.query, id: entry.id } })
}

function close() {
  const { id: _id, ...rest } = route.query
  router.push({ query: rest })
}

function step(delta: number) {
  const list = visibleWords.value
  if (!list.length || selectedIndex.value < 0) return
  const next = list[(selectedIndex.value + delta + list.length) % list.length]!
  router.replace({ query: { ...route.query, id: next.id } })
}

watch(selected, async (entry, previous) => {
  compareMode.value = false
  spoilerOpen.value = false
  document.body.style.overflow = entry ? 'hidden' : ''
  if (entry && !previous) {
    await nextTick()
    dialog.value?.focus()
  } else if (!entry && previous) {
    returnFocus?.focus()
  }
})

function onKeydown(event: KeyboardEvent) {
  if (!selected.value) return
  if (event.key === 'Escape') close()
  else if (event.key === 'ArrowRight') step(1)
  else if (event.key === 'ArrowLeft') step(-1)
}

onMounted(() => {
  void loadWords()
  window.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <StaticPageLayout
    eyebrow="WORDS"
    title="エリカの好きな言葉"
    description="漫画、アニメ、ゲーム、歌、本。心に残った言葉を、一枚ずつ。"
  >
    <p class="intro">
      ここに並べているのは、エリカが何度も思い出してしまう言葉たちです。
      一つひとつに、なぜ好きなのかを書き添えています。作品名をきっかけに、ぜひ原作にも触れてみてください。
    </p>

    <div v-if="kinds.length > 1" class="filters" role="group" aria-label="出典の種類で絞り込む">
      <button :class="{ active: kindFilter === 'all' }" :aria-pressed="kindFilter === 'all'" @click="kindFilter = 'all'">すべて</button>
      <button v-for="k in kinds" :key="k" :class="{ active: kindFilter === k }" :aria-pressed="kindFilter === k" @click="kindFilter = k">
        {{ SOURCE_KIND_LABELS[k] }}
      </button>
    </div>

    <p v-if="loading" class="state">読み込んでいます…</p>
    <p v-else-if="loadError" class="state error" role="alert">{{ loadError }} <button class="retry" @click="loadWords">再試行</button></p>

    <p v-else-if="!words.length" class="state">まだ言葉はありません。これから少しずつ増えていきます。</p>

    <ul v-else class="grid">
      <li v-for="w in visibleWords" :key="w.id">
        <button class="tile" @click="open(w)" :aria-label="`${w.source.title}の言葉を開く`">
          <div class="tile-art" :class="{ blurred: w.spoiler }">
            <WordCard :entry="w" />
          </div>
          <span v-if="w.spoiler" class="spoiler-badge">ネタバレ注意</span>
          <span class="tile-meta">
            <span class="kind">{{ SOURCE_KIND_LABELS[w.source.kind] }}</span>
            <span class="title">{{ sourceLine(w) }}</span>
          </span>
        </button>
      </li>
    </ul>

    <!-- 詳細 -->
    <div v-if="selected" class="overlay" @click.self="close">
      <section ref="dialog" class="dialog" role="dialog" aria-modal="true" :aria-label="`${selected.source.title}の言葉`" tabindex="-1">
        <button class="close" aria-label="閉じる" @click="close">×</button>

        <div class="detail">
          <div class="detail-art">
            <div v-if="selected.spoiler && !spoilerOpen" class="spoiler-cover">
              <p>『{{ selected.source.title }}』のネタバレを含みます</p>
              <button @click="spoilerOpen = true">表示する</button>
            </div>
            <WordCard v-else :key="selected.id" :entry="selected" animate />
          </div>

          <div class="detail-text">
            <p class="eyebrow">{{ SOURCE_KIND_LABELS[selected.source.kind] }} · {{ TEMPLATE_LABELS[selected.template] }}</p>
            <h2>{{ sourceLine(selected) }}</h2>
            <p v-if="selected.speaker || selected.source.detail" class="detail-sub">
              <span v-if="selected.speaker">{{ selected.speaker }}の言葉</span>
              <span v-if="selected.source.detail">{{ selected.source.detail }}</span>
            </p>

            <div v-if="selected.comment" class="comment">
              <p class="comment-label">エリカのひとこと</p>
              <p>{{ selected.comment }}</p>
            </div>

            <p v-if="selected.tags?.length" class="tags">
              <span v-for="t in selected.tags" :key="t">#{{ t }}</span>
            </p>
            <a v-if="selected.source.url" :href="selected.source.url" target="_blank" rel="noopener noreferrer" class="official">公式ページ ↗</a>

            <div class="nav-row">
              <button @click="step(-1)">← 前の言葉</button>
              <button @click="step(1)">次の言葉 →</button>
            </div>

            <button class="compare-toggle" :aria-expanded="compareMode" @click="compareMode = !compareMode">
              {{ compareMode ? 'テンプレートの見比べを閉じる' : 'この言葉をほかのテンプレートで見比べる' }}
            </button>
          </div>
        </div>

        <div v-if="compareMode" class="compare">
          <figure v-for="t in templates" :key="t" :class="{ current: t === selected.template }">
            <WordCard :entry="selected" :template="t" />
            <figcaption>{{ TEMPLATE_LABELS[t] }}<span v-if="t === selected.template">（使用中）</span></figcaption>
          </figure>
        </div>
      </section>
    </div>
  </StaticPageLayout>
</template>

<style scoped>
.intro {
  max-width: 46em;
  color: var(--muted);
  margin: 0 0 28px;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 24px;
}
.filters button {
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
}
.filters button.active {
  border-color: var(--accent);
  color: #111;
  background: var(--accent);
  font-weight: 700;
}
.state {
  color: var(--muted);
}
.state.error {
  color: #fca5a5;
}
.retry {
  text-decoration: underline;
  color: var(--accent);
}
.grid {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 28px 22px;
}
.tile {
  position: relative;
  display: block;
  width: 100%;
  text-align: left;
  border-radius: 14px;
}
.tile-art {
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.45);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.tile:hover .tile-art,
.tile:focus-visible .tile-art {
  transform: translateY(-4px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(243, 164, 59, 0.5);
}
.tile-art.blurred {
  filter: blur(10px) brightness(0.7);
}
.spoiler-badge {
  position: absolute;
  top: 40%;
  left: 50%;
  transform: translateX(-50%);
  padding: 6px 12px;
  background: #111c;
  border: 1px solid var(--accent);
  border-radius: 999px;
  font-size: 12px;
  color: var(--accent);
}
.tile-meta {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-top: 12px;
  font-size: 13px;
}
.tile-meta .kind {
  flex-shrink: 0;
  font-size: 11px;
  color: var(--accent);
  border: 1px solid rgba(243, 164, 59, 0.5);
  border-radius: 4px;
  padding: 0 6px;
}
.tile-meta .title {
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
/* --- 詳細 --- */
.overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  background: rgba(5, 5, 8, 0.82);
  backdrop-filter: blur(6px);
  overflow-y: auto;
  padding: 72px 16px 40px;
}
.dialog {
  position: relative;
  width: min(1040px, 100%);
  margin: 0 auto;
  background: #16171b;
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 28px;
  outline: none;
}
.close {
  position: absolute;
  top: 10px;
  right: 14px;
  width: 40px;
  height: 40px;
  font-size: 26px;
  color: var(--muted);
}
.detail {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(0, 1fr);
  gap: 32px;
  align-items: start;
}
.detail-art {
  position: relative;
}
.spoiler-cover {
  aspect-ratio: 4 / 5;
  display: grid;
  place-content: center;
  gap: 14px;
  text-align: center;
  border-radius: 12px;
  background: #0d0e11;
  border: 1px dashed var(--line);
  color: var(--muted);
}
.spoiler-cover button {
  justify-self: center;
  padding: 8px 18px;
  border-radius: 999px;
  background: var(--accent);
  color: #111;
  font-weight: 700;
}
.eyebrow {
  font-size: 11px;
  letter-spacing: 0.18em;
  color: var(--accent);
  margin: 0 0 6px;
}
.detail-text h2 {
  font-size: clamp(20px, 3vw, 26px);
  font-weight: 800;
  margin: 0;
  line-height: 1.5;
}
.detail-sub {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 14px;
  color: var(--muted);
  font-size: 13px;
  margin: 6px 0 0;
}
.comment {
  margin: 22px 0;
  padding: 18px 20px;
  background: #1d1f25;
  border-left: 3px solid var(--accent);
  border-radius: 0 10px 10px 0;
}
.comment-label {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
  margin: 0 0 6px;
}
.comment p:last-child {
  margin: 0;
  line-height: 2;
  font-size: 15px;
}
.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: var(--muted);
}
.official {
  display: inline-block;
  color: var(--accent);
  font-size: 13px;
  margin-top: 4px;
}
.nav-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 24px;
}
.nav-row button,
.compare-toggle {
  padding: 9px 14px;
  border-radius: 10px;
  border: 1px solid var(--line);
  color: var(--text);
  font-size: 13px;
}
.compare-toggle {
  width: 100%;
  margin-top: 12px;
  border-style: dashed;
  color: var(--muted);
}
.compare {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
}
.compare figure {
  margin: 0;
}
.compare figcaption {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: var(--muted);
}
.compare .current figcaption {
  color: var(--accent);
  font-weight: 700;
}
@media (max-width: 860px) {
  .detail { grid-template-columns: 1fr; }
  .dialog { padding: 20px 16px; }
  .compare { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
