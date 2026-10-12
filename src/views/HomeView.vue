<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import LiteYouTube from '../components/LiteYouTube.vue'
import ImageLightbox from '../components/ImageLightbox.vue'
import WordCard from '../words/WordCard.vue'
import { SOURCE_KIND_LABELS, type WordEntry } from '../words/types'
import { commentToPlainText } from '../words/commentFormat'
import { articleDateLabel, splitArticleTitle, summarizeArticle, type ArticleSummary } from '../articles/articleSummary'

// トップページ：エリカ →（流れる画像）→ 最新記事 → 今日の言葉 → 遊ぶ → 最新の動画 → フッター
// 各セクションの主役は1つだけ。続きはそれぞれの一覧ページへ。

interface Article {
  id: string
  title: string
}

interface Video {
  id: string
  title: string
}

const games = [
  { to: '/labyrinth', title: 'エリカの迷宮', category: 'DUNGEON', description: '一歩ずつ、未知の奥へ。', accent: '#a78bfa' },
  { to: '/beat', title: 'ERIKA BEAT', category: 'RHYTHM', description: '音楽に合わせて、リズムを刻む。', accent: '#22d3ee' },
  { to: '/rpg', title: 'エリカ討伐戦', category: 'RPG', description: '楽曲を力に変えて挑む。', accent: '#fb923c' },
  { to: '/game', title: 'Memory Game', category: 'CARD', description: '同じ絵柄を見つけよう。', accent: '#f472b6' },
]

const socialLinks = [
  { name: 'X', href: 'https://twitter.com/erikakataru' },
  { name: 'YouTube', href: 'https://youtube.com/channel/UCcLpUu88d6QTwZswJmOgtvw' },
  { name: 'note', href: 'https://note.com/erikakataru' },
  { name: 'Instagram', href: 'https://www.instagram.com/erikakataru/' },
  { name: 'Bluesky', href: 'https://bsky.app/profile/erikakataru.bsky.social' },
  { name: 'pixiv', href: 'https://www.pixiv.net/users/118819771' },
]

const footerGroups = [
  {
    label: 'CONTENTS',
    links: [
      { to: '/gallery', name: 'ギャラリー' },
      { to: '/blog', name: '記事一覧' },
      { to: '/words', name: '好きな言葉' },
      { to: '/todo', name: '観測日誌' },
    ],
  },
  {
    label: 'PROJECT',
    links: [
      { to: '/concept', name: 'プロジェクトの想い' },
      { to: '/spec', name: '作品を生み出すPC' },
      { to: '/gear', name: '音をつくる道具' },
    ],
  },
]

const CHANNEL_URL = 'https://youtube.com/channel/UCcLpUu88d6QTwZswJmOgtvw'

const controller = new AbortController()
let disposed = false

// ---------- 最新記事 ----------
const article = ref<Article | null>(null)
const articleSummary = ref<ArticleSummary | null>(null)
const articleState = ref<'loading' | 'ready' | 'empty' | 'error'>('loading')

const articleTitle = computed(() => splitArticleTitle(article.value?.title ?? ''))
const articleDate = computed(() => (article.value ? articleDateLabel(article.value.id) : null))
const articleImageBase = computed(() => `/assets/images/gallery/${article.value?.id.split('-')[0] ?? ''}`)
const articleCover = computed(() => {
  const file = articleSummary.value?.cover
  return file ? `${articleImageBase.value}/${file}` : `${articleImageBase.value}/0.webp`
})
// 表紙以外から3枚を小さく見せる
const articleThumbs = computed(() =>
  (articleSummary.value?.images ?? [])
    .filter(f => f !== articleSummary.value?.cover)
    .slice(0, 3)
    .map(f => `${articleImageBase.value}/${f}`),
)
const articleImageCount = computed(() => articleSummary.value?.images.length ?? 0)
const coverFailed = ref(false)

async function fetchLatestArticle() {
  articleState.value = 'loading'
  try {
    const response = await fetch('/assets/articles.json', { signal: controller.signal, cache: 'no-cache' })
    if (!response.ok) throw new Error('記事一覧を取得できませんでした')
    const data: unknown = await response.json()
    if (!Array.isArray(data)) throw new Error('形式が正しくありません')
    const latest = data.find(
      (a): a is Article => !!a && typeof a === 'object' && typeof a.id === 'string' && typeof a.title === 'string',
    )
    if (disposed) return
    if (!latest) {
      articleState.value = 'empty'
      return
    }
    article.value = latest
    articleState.value = 'ready'

    // 本文から表紙と書き出しを取る（失敗しても表紙は 0.webp で出す）
    const md = await fetch(`/articles/${encodeURIComponent(latest.id)}.md`, { signal: controller.signal })
      .then(r => (r.ok ? r.text() : ''))
      .catch(() => '')
    if (!disposed && md) articleSummary.value = summarizeArticle(md)
  } catch {
    if (!disposed) articleState.value = 'error'
  }
}

// ---------- 今日の言葉（登録された言葉からランダムに1枚） ----------
const words = ref<WordEntry[]>([])
const word = ref<WordEntry | null>(null)

async function fetchWords() {
  let data: unknown = null
  try {
    const res = await fetch('/api/words', { signal: controller.signal })
    if (res.ok) data = await res.json()
  } catch {
    // 下で扱う
  }
  // 開発中（npm run dev）は API が無いので、同梱のサンプルを使う。本番ではサンプルを出さない。
  if (!Array.isArray(data) && import.meta.env.DEV) {
    try {
      const res = await fetch('/assets/words.json', { cache: 'no-cache', signal: controller.signal })
      if (res.ok) data = await res.json()
    } catch {
      // 出さない
    }
  }
  if (disposed || !Array.isArray(data)) return
  // ネタバレ注意の言葉はトップには出さない
  words.value = (data as WordEntry[]).filter(w => w && typeof w.id === 'string' && !w.spoiler)
  pickWord()
}

function pickWord() {
  const pool = words.value.filter(w => w.id !== word.value?.id)
  const list = pool.length ? pool : words.value
  word.value = list.length ? list[Math.floor(Math.random() * list.length)]! : null
}

// ---------- 流れる画像（最新5記事の目玉の画像からランダムに） ----------
// featured.json は gallery_gen.py が作る。ファイル名が数字だけの画像（0 を除く）の一覧。
interface StripImage {
  src: string
  alt: string
}

const STRIP_PER_ROW = 8
/** 最新から何記事分のギャラリーを対象にするか */
const STRIP_ARTICLES = 5
const stripRows = ref<StripImage[][]>([])
const stripImages = computed(() => stripRows.value.flat())
const stripIndex = ref<number | null>(null)
const stripEl = ref<HTMLElement | null>(null)
const rowEls = ref<HTMLElement[]>([])
const stripStatic = ref(false)

async function fetchStrip() {
  try {
    const res = await fetch('/assets/featured.json', { signal: controller.signal })
    if (!res.ok) return
    const data: unknown = await res.json()
    if (disposed || !data || typeof data !== 'object' || Array.isArray(data)) return

    // フォルダ名（日付）の新しい順に並べて、最新の5記事分だけを使う。
    // ※ "20261009" のような数字のキーは、JSON を読むと古い順に並び替わってしまうので、ここで並べ直す。
    const latest = Object.entries(data as Record<string, unknown>)
      .filter(([folder, files]) => /^[\w-]+$/.test(folder) && Array.isArray(files) && files.length > 0)
      .sort(([a], [b]) => (a < b ? 1 : a > b ? -1 : 0))
      .slice(0, STRIP_ARTICLES)

    const all: StripImage[] = []
    for (const [folder, files] of latest as [string, unknown[]][]) {
      const date = articleDateLabel(folder)?.label
      for (const file of files) {
        if (typeof file !== 'string' || !/^\d+\.(?:webp|png|jpe?g)$/i.test(file) || /^0+\./.test(file)) continue
        all.push({
          src: `/assets/images/gallery/${folder}/${file}`,
          alt: date ? `エリカのイラスト（${date}）` : 'エリカのイラスト',
        })
      }
    }
    // ランダムに選ぶ（Fisher–Yates の途中まで）
    const count = Math.min(all.length, STRIP_PER_ROW * 2)
    for (let i = 0; i < count; i++) {
      const j = i + Math.floor(Math.random() * (all.length - i))
      ;[all[i], all[j]] = [all[j]!, all[i]!]
    }
    const picked = all.slice(0, count)
    if (picked.length < 4) return // 少なすぎるときは出さない
    const half = Math.ceil(picked.length / 2)
    stripRows.value = [picked.slice(0, half), picked.slice(half)]
    await nextTick()
    setupStripMotion()
  } catch {
    // 出さない
  }
}

function openStrip(row: number, index: number) {
  stripIndex.value = (row === 0 ? 0 : stripRows.value[0]!.length) + index
}

// 縦スクロールに合わせて、上の段は右へ・下の段は左へずらす（画面は止めない）
let stripVisible = false
let rafId = 0
let observer: IntersectionObserver | null = null
const reduceMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function updateStrip() {
  rafId = 0
  const el = stripEl.value
  if (!el) return
  const rect = el.getBoundingClientRect()
  const vh = window.innerHeight || 1
  // 帯が画面の下から入ってきたとき 0、上へ抜けるとき 1
  const progress = Math.min(1, Math.max(0, (vh - rect.top) / (vh + rect.height)))
  rowEls.value.forEach((row, i) => {
    const max = Math.max(0, row.scrollWidth - el.clientWidth)
    const p = i === 0 ? progress : 1 - progress
    row.style.transform = `translate3d(${-max * (1 - p)}px, 0, 0)`
  })
}

function requestStripUpdate() {
  if (stripVisible && !rafId) rafId = requestAnimationFrame(updateStrip)
}

function setupStripMotion() {
  if (!stripEl.value) return
  if (reduceMotion) {
    stripStatic.value = true // 動きを減らす設定なら、指で横にスクロールする帯にする
    return
  }
  observer?.disconnect()
  observer = new IntersectionObserver(([entry]) => {
    stripVisible = !!entry?.isIntersecting
    requestStripUpdate()
  })
  observer.observe(stripEl.value)
  window.addEventListener('scroll', requestStripUpdate, { passive: true })
  window.addEventListener('resize', requestStripUpdate, { passive: true })
  stripVisible = true
  updateStrip()
}

// ---------- 最新の動画 ----------
const latestVideo = ref<Video>({ id: 'kx8JnJVu89I', title: 'アルバムレビュー' })

function isVideo(value: unknown): value is Video {
  if (!value || typeof value !== 'object') return false
  const video = value as Record<string, unknown>
  return typeof video.id === 'string' && /^[a-zA-Z0-9_-]{11}$/.test(video.id) && typeof video.title === 'string'
}

async function fetchLatestVideo() {
  try {
    const response = await fetch('https://erika-youtube-worker.kyobasiri.workers.dev', { signal: controller.signal })
    if (!response.ok) return
    const data = await response.json()
    if (disposed || !data || typeof data !== 'object') return
    if (isVideo(data.long)) latestVideo.value = data.long
  } catch {
    // 取得できない場合は設定済みの動画を表示
  }
}

onMounted(() => {
  void fetchStrip()
  void fetchLatestArticle()
  void fetchWords()
  void fetchLatestVideo()
})

onBeforeUnmount(() => {
  disposed = true
  controller.abort()
  observer?.disconnect()
  if (rafId) cancelAnimationFrame(rafId)
  window.removeEventListener('scroll', requestStripUpdate)
  window.removeEventListener('resize', requestStripUpdate)
})
</script>

<template>
  <div class="erika-home">
    <!-- エリカ -->
    <section class="hero page-width" aria-labelledby="home-title">
      <div class="hero-copy">
        <p class="eyebrow">ART · MUSIC · PLAY</p>
        <h1 id="home-title">ERIKA<span>.</span></h1>
        <p class="hero-lead">
          音楽から生まれる感動を、<br />
          イラストと遊びの世界へ。
        </p>
        <div class="hero-actions">
          <router-link to="/gallery" class="button button-primary">
            ギャラリーを見る <span aria-hidden="true">→</span>
          </router-link>
          <router-link to="/words" class="button button-secondary">
            好きな言葉 <span aria-hidden="true">→</span>
          </router-link>
        </div>
        <router-link to="/concept" class="concept-link">
          このプロジェクトについて <span aria-hidden="true">→</span>
        </router-link>
      </div>

      <div class="hero-art">
        <img src="/assets/images/erika-hero.jpg" alt="エリカのメインビジュアル" fetchpriority="high" decoding="async" />
      </div>
    </section>

    <!-- 流れる画像（最新5記事の目玉の画像からランダムに16枚） -->
    <section
      v-if="stripRows.length"
      ref="stripEl"
      class="art-strip"
      :class="{ 'is-static': stripStatic }"
      aria-label="エリカのイラスト"
    >
      <div
        v-for="(row, r) in stripRows"
        :key="r"
        :ref="el => { if (el) rowEls[r] = el as HTMLElement }"
        class="strip-row"
      >
        <button
          v-for="(image, i) in row"
          :key="image.src"
          type="button"
          class="strip-item"
          :aria-label="`${image.alt}を拡大表示`"
          @click="openStrip(r, i)"
        >
          <img :src="image.src" :alt="image.alt" loading="lazy" decoding="async" draggable="false" />
        </button>
      </div>
    </section>

    <!-- 最新記事 -->
    <section class="section page-width" aria-labelledby="article-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">LATEST ARTICLE</p>
          <h2 id="article-title">最新の記事</h2>
        </div>
        <router-link to="/blog" class="text-link">記事一覧 <span aria-hidden="true">→</span></router-link>
      </div>

      <div aria-live="polite">
        <div v-if="articleState === 'loading'" class="article-card is-skeleton" aria-label="記事を読み込んでいます">
          <span class="article-cover"></span>
          <span class="article-body">
            <span class="sk-line w40"></span>
            <span class="sk-line w80 tall"></span>
            <span class="sk-line w60"></span>
          </span>
        </div>

        <div v-else-if="articleState === 'error'" class="status-box">
          <p>記事を読み込めませんでした。</p>
          <button type="button" class="text-link retry-button" @click="fetchLatestArticle">再読み込み</button>
        </div>

        <p v-else-if="articleState === 'empty'" class="status-box">現在、掲載されている記事はありません。</p>

        <router-link
          v-else-if="article"
          :to="{ path: '/article', query: { id: article.id } }"
          class="article-card"
        >
          <span class="article-cover">
            <img
              v-if="!coverFailed"
              :src="articleCover"
              :alt="`${articleTitle.main}の表紙`"
              loading="lazy"
              decoding="async"
              @error="coverFailed = true"
            />
            <span v-else class="cover-fallback" aria-hidden="true">ERIKA</span>
          </span>

          <span class="article-body">
            <span class="article-meta">
              <span v-if="articleTitle.number" class="badge">GALLERY #{{ articleTitle.number }}</span>
              <time v-if="articleDate" :datetime="articleDate.iso">{{ articleDate.label }}</time>
            </span>

            <span class="article-heading">{{ articleTitle.main }}</span>
            <span v-if="articleTitle.series" class="article-series">{{ articleTitle.series }}</span>
            <span v-if="articleSummary?.excerpt" class="article-excerpt">{{ articleSummary.excerpt }}</span>

            <span v-if="articleThumbs.length" class="article-thumbs" aria-hidden="true">
              <img v-for="src in articleThumbs" :key="src" :src="src" alt="" loading="lazy" decoding="async" />
              <span v-if="articleImageCount > articleThumbs.length + 1" class="thumb-more">
                +{{ articleImageCount - articleThumbs.length - 1 }}
              </span>
            </span>

            <span class="article-action">記事を読む <span aria-hidden="true">→</span></span>
          </span>
        </router-link>
      </div>
    </section>

    <!-- 今日の言葉（公開中の言葉が無いときは出さない） -->
    <section v-if="word" class="section words-section" aria-labelledby="words-title">
      <div class="page-width">
        <div class="section-heading">
          <div>
            <p class="eyebrow">WORDS</p>
            <h2 id="words-title">心に残っている言葉</h2>
          </div>
          <router-link to="/words" class="text-link">言葉の一覧 <span aria-hidden="true">→</span></router-link>
        </div>

        <div class="word-feature">
          <router-link
            :to="{ path: '/words', query: { id: word.id } }"
            class="word-frame"
            :aria-label="`『${word.source.title}』の言葉を詳しく見る`"
          >
            <Transition name="word-fade" mode="out-in">
              <WordCard :key="word.id" :entry="word" animate />
            </Transition>
          </router-link>

          <div class="word-info">
            <p class="word-kind">{{ SOURCE_KIND_LABELS[word.source.kind] ?? '' }}</p>
            <p class="word-source">『{{ word.source.title }}』</p>
            <p v-if="word.speaker || word.source.author" class="word-speaker">
              {{ word.speaker || word.source.author }}
            </p>
            <!-- ひとことは Markdown なので、記号を外した文章を抜粋として見せる -->
            <p v-if="word.comment" class="word-comment">{{ commentToPlainText(word.comment) }}</p>

            <div class="word-actions">
              <button v-if="words.length > 1" type="button" class="button button-secondary" @click="pickWord">
                もう一枚 <span aria-hidden="true">↻</span>
              </button>
              <router-link :to="{ path: '/words', query: { id: word.id } }" class="text-link">
                この言葉について <span aria-hidden="true">→</span>
              </router-link>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 遊ぶ -->
    <section id="games" class="section page-width" aria-labelledby="games-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">PLAY</p>
          <h2 id="games-title">エリカの世界で遊ぶ</h2>
        </div>
      </div>

      <div class="games-grid">
        <router-link
          v-for="game in games"
          :key="game.to"
          :to="game.to"
          class="game-tile"
          :style="{ '--game-accent': game.accent }"
        >
          <span class="game-category">{{ game.category }}</span>
          <span class="game-title">{{ game.title }}</span>
          <span class="game-desc">{{ game.description }}</span>
          <span class="game-arrow" aria-hidden="true">→</span>
        </router-link>
      </div>
    </section>

    <!-- 最新の動画 -->
    <section class="section page-width" aria-labelledby="video-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">VIDEO</p>
          <h2 id="video-title">最新の動画</h2>
        </div>
        <a :href="CHANNEL_URL" target="_blank" rel="noopener noreferrer" class="text-link">
          YouTubeチャンネル <span aria-hidden="true">↗</span>
        </a>
      </div>

      <div class="video-feature">
        <LiteYouTube :key="latestVideo.id" :id="latestVideo.id" :title="latestVideo.title" />
        <div class="video-caption">
          <a
            :href="`https://www.youtube.com/watch?v=${latestVideo.id}`"
            target="_blank"
            rel="noopener noreferrer"
            class="text-link"
          >
            YouTubeで見る <span aria-hidden="true">↗</span>
          </a>
        </div>
      </div>
    </section>

    <ImageLightbox v-model:index="stripIndex" :images="stripImages" />

    <!-- フッター -->
    <footer class="site-footer">
      <div class="page-width">
        <div class="footer-top">
          <div class="footer-brand-block">
            <p class="footer-brand">ERIKA<span>.</span></p>
            <p class="footer-description">アートと音楽、制作の続きを。</p>
            <nav class="social-links" aria-label="SNS">
              <a v-for="social in socialLinks" :key="social.name" :href="social.href" target="_blank" rel="noopener noreferrer">
                {{ social.name }} <span aria-hidden="true">↗</span>
              </a>
            </nav>
          </div>

          <nav v-for="group in footerGroups" :key="group.label" class="footer-group" :aria-label="group.label">
            <p class="footer-label">{{ group.label }}</p>
            <router-link v-for="link in group.links" :key="link.to" :to="link.to">{{ link.name }}</router-link>
          </nav>
        </div>

        <div class="footer-bottom">
          <p>© {{ new Date().getFullYear() }} Erika Project.</p>
          <nav aria-label="サイト情報">
            <router-link to="/privacy">Privacy Policy</router-link>
            <router-link to="/contact">Contact</router-link>
          </nav>
        </div>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.erika-home {
  --page-bg: #101113;
  --surface: #181a1e;
  --surface-2: #141518;
  --accent: #f3a43b;
  --text: #f4f4f5;
  --muted: #a6a6af;
  --line: rgba(255, 255, 255, 0.1);

  min-height: 100vh;
  overflow-x: clip;
  background: var(--page-bg);
  color: var(--text);
  line-height: 1.7;
}

.erika-home * {
  box-sizing: border-box;
}

.erika-home a {
  text-decoration: none;
  color: inherit;
}

.erika-home button {
  font: inherit;
  cursor: pointer;
}

.erika-home a:focus-visible,
.erika-home button:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 5px;
}

.page-width {
  width: min(1160px, calc(100% - 64px));
  margin-inline: auto;
}

.section {
  padding-block: 64px;
  scroll-margin-top: 96px;
}

.eyebrow {
  display: block;
  margin: 0 0 10px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
}

/* ---------- エリカ ---------- */
.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
  padding-top: 112px;
  padding-bottom: 32px;
}

.hero h1 {
  margin: 0 0 20px;
  font-size: clamp(76px, 8.5vw, 120px);
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.065em;
}

.hero h1 span,
.footer-brand span {
  color: var(--accent);
}

.hero-lead {
  margin: 0;
  font-size: clamp(21px, 2.3vw, 29px);
  font-weight: 700;
  line-height: 1.65;
  letter-spacing: 0.025em;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 32px;
}

.button {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 12px 22px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: transparent;
  color: var(--text);
  font-size: 14px;
  font-weight: 700;
  transition: background 0.2s, transform 0.2s;
}

.button:hover {
  transform: translateY(-2px);
}

.button-primary {
  background: var(--accent);
  color: #19130b !important;
}

.button-primary:hover {
  background: #ffb956;
}

.button-secondary {
  border-color: rgba(255, 255, 255, 0.2);
}

.button-secondary:hover {
  background: rgba(255, 255, 255, 0.06);
}

.concept-link {
  display: inline-flex;
  gap: 16px;
  margin-top: 24px;
  color: var(--muted) !important;
  font-size: 13px;
}

.concept-link:hover {
  color: var(--text) !important;
}

.hero-art {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: #191a1e;
}

.hero-art > img {
  display: block;
  width: 100%;
  height: clamp(380px, 43vw, 540px);
  object-fit: contain;
}

/* ---------- 流れる画像 ---------- */
.art-strip {
  display: grid;
  gap: clamp(10px, 1.4vw, 18px);
  padding-block: 40px 24px;
  overflow: hidden;
}

.strip-row {
  display: flex;
  gap: clamp(10px, 1.4vw, 18px);
  width: max-content;
  padding-inline: clamp(16px, 4vw, 48px);
  will-change: transform;
}

.strip-row:nth-child(2) {
  margin-left: clamp(40px, 8vw, 120px); /* 2段目は少しずらして、格子に見えないように */
}

.strip-item {
  flex: none;
  width: clamp(130px, 15vw, 220px);
  aspect-ratio: 4 / 5;
  padding: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
}

.strip-item img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease, filter 0.3s;
  filter: brightness(0.92);
}

.strip-item:hover img {
  transform: scale(1.04);
  filter: brightness(1.04);
}

/* 動きを減らす設定のとき：指で横にスクロール */
.art-strip.is-static .strip-row {
  width: auto;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}

.art-strip.is-static .strip-item {
  scroll-snap-align: start;
}

/* ---------- 見出し ---------- */
.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 26px;
}

.section-heading h2 {
  margin: 0;
  font-size: clamp(23px, 3vw, 31px);
  font-weight: 700;
  line-height: 1.4;
  letter-spacing: 0.025em;
}

.text-link {
  color: var(--accent) !important;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.text-link:hover {
  text-decoration: underline;
  text-underline-offset: 4px;
}

.status-box {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 0;
  padding: 28px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--surface);
  color: var(--muted);
  font-size: 14px;
}

.status-box p {
  margin: 0;
}

.retry-button {
  padding: 0;
  border: 0;
  background: none;
}

/* ---------- 最新記事 ---------- */
.article-card {
  display: grid;
  grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 16px;
  background: var(--surface);
  transition: border-color 0.25s, transform 0.25s;
}

.article-card:not(.is-skeleton):hover {
  border-color: rgba(243, 164, 59, 0.55);
  transform: translateY(-3px);
}

.article-cover {
  position: relative;
  display: block;
  aspect-ratio: 4 / 5;
  overflow: hidden;
  background: #0c0d0f;
}

.article-cover img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: 50% 25%;
  transition: transform 0.6s ease;
}

.article-card:hover .article-cover img {
  transform: scale(1.03);
}

.cover-fallback {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: rgba(255, 255, 255, 0.12);
  font-size: 48px;
  font-weight: 900;
  letter-spacing: -0.05em;
}

.article-body {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
  min-width: 0;
  padding: clamp(28px, 4vw, 56px);
}

.article-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  color: var(--muted);
  font-size: 12px;
  letter-spacing: 0.12em;
  font-variant-numeric: tabular-nums;
}

.badge {
  padding: 4px 10px;
  border: 1px solid rgba(243, 164, 59, 0.5);
  border-radius: 999px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
}

.article-heading {
  display: block;
  font-size: clamp(28px, 3.6vw, 44px);
  font-weight: 800;
  line-height: 1.3;
  letter-spacing: 0.01em;
  text-wrap: balance;
  word-break: keep-all;
  overflow-wrap: anywhere;
}

.article-series {
  margin-top: -6px;
  color: var(--muted);
  font-size: 13px;
}

.article-excerpt {
  display: -webkit-box;
  overflow: hidden;
  color: #c9c9d1;
  font-size: 14px;
  line-height: 1.9;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
  line-clamp: 3;
}

.article-thumbs {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

.article-thumbs img,
.thumb-more {
  width: 64px;
  height: 80px;
  border: 1px solid var(--line);
  border-radius: 8px;
  object-fit: cover;
  background: #0c0d0f;
}

.thumb-more {
  display: grid;
  place-items: center;
  color: var(--muted);
  font-size: 13px;
  font-weight: 700;
}

.article-action {
  display: inline-flex;
  gap: 12px;
  margin-top: 8px;
  color: var(--accent);
  font-size: 14px;
  font-weight: 700;
}

/* 読み込み中の形 */
.is-skeleton .article-cover,
.sk-line {
  background: linear-gradient(90deg, #1d1f24 0%, #25272d 50%, #1d1f24 100%);
  background-size: 200% 100%;
  animation: shimmer 1.4s linear infinite;
}

.sk-line {
  display: block;
  height: 14px;
  border-radius: 6px;
}

.sk-line.tall { height: 36px; }
.sk-line.w40 { width: 40%; }
.sk-line.w60 { width: 60%; }
.sk-line.w80 { width: 80%; }

@keyframes shimmer {
  to { background-position: -200% 0; }
}

/* ---------- 今日の言葉 ---------- */
.words-section {
  border-block: 1px solid var(--line);
  background:
    radial-gradient(60% 80% at 20% 10%, rgba(243, 164, 59, 0.08), transparent 70%),
    var(--surface-2);
}

.word-feature {
  display: grid;
  grid-template-columns: minmax(0, 420px) minmax(0, 1fr);
  gap: clamp(28px, 5vw, 72px);
  align-items: center;
}

.word-frame {
  display: block;
  border-radius: 14px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.45);
  transition: transform 0.25s;
}

.word-frame:hover {
  transform: translateY(-3px) rotate(-0.4deg);
}

.word-info {
  min-width: 0;
}

.word-kind {
  margin: 0 0 6px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.word-source {
  margin: 0;
  font-size: clamp(20px, 2.4vw, 26px);
  font-weight: 700;
  line-height: 1.5;
}

.word-speaker {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 14px;
}

.word-comment {
  position: relative;
  margin: 24px 0 0;
  padding-left: 18px;
  border-left: 2px solid rgba(243, 164, 59, 0.6);
  color: #d4d4d8;
  font-size: 15px;
  line-height: 2;
  white-space: pre-line;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 6;
  line-clamp: 6;
}

.word-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 20px;
  margin-top: 32px;
}

.word-fade-enter-active,
.word-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.word-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.word-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ---------- 遊ぶ ---------- */
.games-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.game-tile {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 150px;
  padding: 22px 22px 20px;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 12px;
  background:
    radial-gradient(120% 90% at 100% 0%, color-mix(in srgb, var(--game-accent) 16%, transparent), transparent 60%),
    var(--surface);
  transition: transform 0.2s, border-color 0.2s;
}

.game-tile:hover {
  transform: translateY(-3px);
  border-color: var(--game-accent);
}

.game-category {
  color: var(--game-accent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.game-title {
  font-size: 17px;
  font-weight: 700;
}

.game-desc {
  color: var(--muted);
  font-size: 13px;
}

.game-arrow {
  margin-top: auto;
  padding-top: 10px;
  color: var(--game-accent);
  font-weight: 700;
  transition: transform 0.2s;
}

.game-tile:hover .game-arrow {
  transform: translateX(4px);
}

/* ---------- 最新の動画 ---------- */
.video-feature {
  max-width: 880px;
}

.video-caption {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 20px;
  margin-top: 14px;
}

/* ---------- フッター ---------- */
.site-footer {
  margin-top: 32px;
  padding: 48px 0 28px;
  border-top: 1px solid var(--line);
  background: #0c0d0f;
}

.footer-top {
  display: grid;
  grid-template-columns: minmax(0, 2fr) repeat(2, minmax(0, 1fr));
  gap: 40px;
}

.footer-brand {
  margin: 0;
  font-size: 32px;
  font-weight: 900;
  letter-spacing: -0.055em;
}

.footer-description {
  margin: 5px 0 0;
  color: var(--muted);
  font-size: 12px;
}

.social-links {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 20px;
  margin-top: 20px;
}

.social-links a {
  padding-block: 6px;
  color: #d4d4d8;
  font-size: 13px;
}

.social-links a:hover {
  color: var(--accent);
}

.social-links span {
  color: #7d7d86;
  font-size: 10px;
}

.footer-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-label {
  margin: 0 0 4px;
  color: #7d7d86;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.footer-group a {
  padding-block: 3px;
  color: #d4d4d8;
  font-size: 13px;
}

.footer-group a:hover {
  color: var(--accent);
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-top: 36px;
  padding-top: 22px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 11px;
}

.footer-bottom p {
  margin: 0;
}

.footer-bottom nav {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
}

.footer-bottom a {
  color: var(--muted);
}

.footer-bottom a:hover {
  color: var(--text);
}

/* ---------- タブレット ---------- */
@media (max-width: 1023px) {
  .hero {
    gap: 40px;
  }

  .games-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .word-feature {
    grid-template-columns: minmax(0, 340px) minmax(0, 1fr);
  }
}

/* ---------- スマホ ---------- */
@media (max-width: 767px) {
  .page-width {
    width: calc(100% - 32px);
  }

  .section {
    padding-block: 48px;
  }

  .hero {
    grid-template-columns: 1fr;
    gap: 28px;
    padding-top: 88px;
  }

  .hero-art {
    order: -1;
  }

  .hero-art > img {
    height: min(110vw, 460px);
  }

  .hero h1 {
    font-size: clamp(64px, 20vw, 88px);
  }

  .hero-actions .button {
    flex: 1 1 140px;
    gap: 10px;
    padding-inline: 14px;
    white-space: nowrap;
  }

  .article-card {
    grid-template-columns: 1fr;
  }

  .article-cover {
    aspect-ratio: 4 / 3;
  }

  .article-body {
    padding: 24px 20px 26px;
  }

  .article-thumbs img,
  .thumb-more {
    width: 56px;
    height: 70px;
  }

  .word-feature {
    grid-template-columns: 1fr;
  }

  .word-frame {
    width: min(100%, 400px);
    margin-inline: auto;
  }

  .games-grid {
    gap: 12px;
  }

  .game-tile {
    min-height: 132px;
    padding: 18px 16px 16px;
  }

  .game-desc {
    font-size: 12px;
  }

  .footer-top {
    grid-template-columns: 1fr 1fr;
    gap: 32px 24px;
  }

  .footer-brand-block {
    grid-column: 1 / -1;
  }

  .footer-bottom {
    flex-direction: column;
    gap: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .erika-home *,
  .erika-home *::before,
  .erika-home *::after {
    animation: none !important;
    transition: none !important;
  }
}
</style>
