<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import '@fontsource/shippori-mincho/600.css'
import ImageLightbox from '../components/ImageLightbox.vue'
import LiteYouTube from '../components/LiteYouTube.vue'
import { articleDate, cleanAlt, parseArticle, type ArticleBlock, type ParsedArticle } from '../articles/parseArticle'

interface ArticleRef { id: string; title: string }
interface GalleryFolder { name: string; images: { file: string; alt?: string }[] }

const route = useRoute()
const articleId = ref('')
const article = ref<ParsedArticle | null>(null)
const loading = ref(true)
const loadError = ref('')
const prevArticle = ref<ArticleRef | null>(null)
const nextArticle = ref<ArticleRef | null>(null)
const galleryFolders = ref<GalleryFolder[]>([])
const lightboxIndex = ref<number | null>(null)
const expanded = ref<Set<number>>(new Set())
const copied = ref(false)

// 画像が多いまとまりは、最初はこの枚数だけ見せる
const COLLAPSE_AFTER = 12

const date = computed(() => articleDate(articleId.value))
const folderOf = (id: string) => galleryFolders.value.find(g => g.name === id.split('-')[0])
const coverOf = (id: string) => {
  const folder = folderOf(id)
  if (!folder?.images?.length) return ''
  const cover = folder.images.find(i => i.file === '0.webp') ?? folder.images[0]!
  return `/assets/images/gallery/${folder.name}/${cover.file}`
}

const cover = computed(() => coverOf(articleId.value) || article.value?.images[0]?.src || '')
const coverIndex = computed(() => article.value?.images.findIndex(i => i.src === cover.value) ?? -1)
const lightboxImages = computed(() => article.value?.images.map(i => ({ src: i.src, alt: i.alt })) ?? [])

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url, { cache: 'no-cache' })
    return res.ok ? ((await res.json()) as T) : null
  } catch {
    return null
  }
}

async function load() {
  const id = typeof route.query.id === 'string' ? route.query.id : ''
  articleId.value = id
  loading.value = true
  loadError.value = ''
  article.value = null
  expanded.value = new Set()
  lightboxIndex.value = null
  prevArticle.value = null
  nextArticle.value = null

  if (!id) {
    loadError.value = '記事が指定されていません。'
    loading.value = false
    return
  }

  const [articles, galleries, text] = await Promise.all([
    fetchJson<ArticleRef[]>('/assets/articles.json'),
    fetchJson<GalleryFolder[]>('/assets/gallery.json'),
    fetch(`/articles/${encodeURIComponent(id)}.md`).then(async r => (r.ok ? r.text() : null)).catch(() => null)
  ])
  if (id !== articleId.value) return // 読み込み中に別の記事へ移動した

  galleryFolders.value = Array.isArray(galleries) ? galleries : []
  if (Array.isArray(articles)) {
    const i = articles.findIndex(a => a.id === id)
    if (i >= 0) {
      prevArticle.value = articles[i + 1] ?? null // 古い記事
      nextArticle.value = articles[i - 1] ?? null // 新しい記事
    }
  }

  // 記事ファイルが無いと index.html が返ってくるので、それも「見つからない」として扱う
  if (!text || /^\s*<(!doctype|html)/i.test(text)) {
    loadError.value = '記事が見つかりませんでした。'
    loading.value = false
    return
  }

  const folder = folderOf(id)
  // AIが作った説明文は崩れていることがあるので、掃除してから使う（使えないものは既定の説明になる）
  const altMap = new Map((folder?.images ?? []).map(img => [img.file, cleanAlt(img.alt)]))
  article.value = parseArticle(text, {
    imageBase: `/assets/images/gallery/${id.split('-')[0]}`,
    altFor: file => altMap.get(file)
  })
  document.title = `${article.value.mainTitle} | Erika Official`
  loading.value = false

  await nextTick()
  if (article.value.blocks.some(b => b.type === 'x')) loadTwitterWidget()
}

// X（旧Twitter）の埋め込み
function loadTwitterWidget() {
  const w = window as unknown as { twttr?: { widgets?: { load: () => void } } }
  if (w.twttr?.widgets) { w.twttr.widgets.load(); return }
  if (document.getElementById('twitter-wjs')) return
  const script = document.createElement('script')
  script.id = 'twitter-wjs'
  script.src = 'https://platform.twitter.com/widgets.js'
  script.async = true
  script.charset = 'utf-8'
  document.head.appendChild(script)
}

function visibleImages(block: Extract<ArticleBlock, { type: 'gallery' }>, i: number) {
  return expanded.value.has(i) || block.images.length <= COLLAPSE_AFTER + 4
    ? block.images
    : block.images.slice(0, COLLAPSE_AFTER)
}
function expand(i: number) {
  expanded.value = new Set(expanded.value).add(i)
}

// 共有
const shareUrl = computed(() => (typeof window !== 'undefined' ? window.location.href : ''))
const xShareHref = computed(() =>
  `https://x.com/intent/post?text=${encodeURIComponent(article.value?.title ?? '')}&url=${encodeURIComponent(shareUrl.value)}`
)
async function copyLink() {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    window.prompt('このURLをコピーしてください', shareUrl.value)
  }
}

// 読んだ位置のバー
const progress = ref(0)
function onScroll() {
  const max = document.documentElement.scrollHeight - window.innerHeight
  progress.value = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0
}

onMounted(() => {
  void load()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  document.title = 'Erika Official | AI Art & Music'
})
watch(() => route.query.id, (id, old) => {
  if (id && id !== old) {
    void load()
    window.scrollTo({ top: 0 })
  }
})
</script>

<template>
  <div class="article-page">
    <div class="progress" :style="{ transform: `scaleX(${progress})` }" aria-hidden="true"></div>

    <p v-if="loading" class="state">記事を読み込んでいます…</p>
    <div v-else-if="loadError" class="state">
      <p>{{ loadError }}</p>
      <router-link to="/blog" class="pill">記事一覧へ</router-link>
    </div>

    <article v-else-if="article">
      <!-- 冒頭 -->
      <header class="hero">
        <div v-if="cover" class="hero-bg" :style="{ backgroundImage: `url(${cover})` }" aria-hidden="true"></div>
        <div class="hero-inner">
          <div class="hero-text">
            <nav class="crumbs" aria-label="パンくず">
              <router-link to="/">ホーム</router-link><span>/</span><router-link to="/blog">Activities</router-link>
            </nav>
            <p class="series">
              <span v-if="article.seriesNumber" class="badge">GALLERY #{{ article.seriesNumber }}</span>
              <time v-if="date" :datetime="date.iso">{{ date.label }}</time>
            </p>
            <h1>{{ article.mainTitle }}</h1>
            <p v-if="article.series" class="series-name">{{ article.series }}</p>
            <p class="meta">
              <span v-if="article.images.length">画像 {{ article.images.length }}枚</span>
              <span v-if="article.tags.length">#{{ article.tags[0] }}</span>
            </p>
          </div>
          <button
            v-if="cover"
            class="hero-cover"
            :disabled="coverIndex < 0"
            :aria-label="coverIndex >= 0 ? '表紙の画像を大きく見る' : undefined"
            @click="coverIndex >= 0 && (lightboxIndex = coverIndex)"
          >
            <img :src="cover" :alt="article.images[coverIndex]?.alt || article.mainTitle" fetchpriority="high">
          </button>
        </div>
      </header>

      <!-- 本文 -->
      <div class="body">
        <template v-for="(block, i) in article.blocks" :key="i">
          <div v-if="block.type === 'markdown'" class="prose" v-html="block.html"></div>

          <section v-else-if="block.type === 'gallery'" class="gallery-block" :aria-label="`画像 ${block.images.length}枚`">
            <p class="gallery-head"><span>{{ block.images.length }} IMAGES</span>タップで大きく見られます</p>
            <ul class="masonry">
              <li v-for="img in visibleImages(block, i)" :key="img.file">
                <button @click="lightboxIndex = img.index" :aria-label="`${img.alt}（大きく見る）`">
                  <img :src="img.src" :alt="img.alt" loading="lazy" decoding="async">
                </button>
              </li>
            </ul>
            <button v-if="visibleImages(block, i).length < block.images.length" class="more" @click="expand(i)">
              残り {{ block.images.length - visibleImages(block, i).length }}枚を見る
            </button>
          </section>

          <figure v-else-if="block.type === 'image'" class="single">
            <button @click="lightboxIndex = block.image.index" :aria-label="`${block.image.alt}（大きく見る）`">
              <img :src="block.image.src" :alt="block.image.alt" loading="lazy" decoding="async">
            </button>
            <figcaption v-if="block.image.alt">{{ block.image.alt }}</figcaption>
          </figure>

          <div v-else-if="block.type === 'x'" class="embed x-embed">
            <p class="embed-label">X に投稿したエリカ</p>
            <blockquote class="twitter-tweet" data-theme="dark" data-align="center" data-dnt="true">
              <a :href="block.url" target="_blank" rel="noopener noreferrer">X で投稿を見る ↗</a>
            </blockquote>
          </div>

          <div v-else-if="block.type === 'youtube'" class="embed" :class="{ narrow: block.vertical }">
            <p class="embed-label">{{ block.vertical ? 'SHORTS' : 'VIDEO' }}</p>
            <LiteYouTube :id="block.id" :vertical="block.vertical" />
          </div>

          <section v-else-if="block.type === 'music'" class="music">
            <div class="music-text">
              <p class="music-label"><span class="eq" aria-hidden="true"><i></i><i></i><i></i></span>NOW LISTENING</p>
              <p class="music-title">{{ block.title }}</p>
              <p v-if="block.artist" class="music-artist">{{ block.artist }}</p>
            </div>
            <LiteYouTube :id="block.id" :title="`${block.artist} ${block.title}`.trim()" />
          </section>

          <blockquote v-else-if="block.type === 'quote'" class="pull-quote">
            <p>{{ block.text }}</p>
          </blockquote>

          <a v-else-if="block.type === 'channel'" :href="block.url" target="_blank" rel="noopener noreferrer" class="channel">
            <span class="yt-icon" aria-hidden="true">
              <svg viewBox="0 0 68 48"><path d="M66.5 7.7a8.6 8.6 0 0 0-6-6C55.2.3 34 .3 34 .3s-21.2 0-26.5 1.4a8.6 8.6 0 0 0-6 6C.1 13 .1 24 .1 24s0 11 1.4 16.3a8.6 8.6 0 0 0 6 6c5.3 1.4 26.5 1.4 26.5 1.4s21.2 0 26.5-1.4a8.6 8.6 0 0 0 6-6C67.9 35 67.9 24 67.9 24s0-11-1.4-16.3z" fill="#ff0033"/><path d="M45 24 27 14v20z" fill="#fff"/></svg>
            </span>
            <span class="channel-text">
              <small>YouTube</small>
              <strong>エリカが好き勝手に語るチャンネル</strong>
              <span>声のついた、動くエリカに会いに行く</span>
            </span>
            <span class="channel-go" aria-hidden="true">→</span>
          </a>
        </template>

        <!-- 末尾 -->
        <footer class="article-foot">
          <ul v-if="article.tags.length" class="tags">
            <li v-for="t in article.tags" :key="t">#{{ t }}</li>
          </ul>
          <div class="share">
            <a :href="xShareHref" target="_blank" rel="noopener noreferrer" class="pill">X で共有</a>
            <button class="pill" @click="copyLink">{{ copied ? 'コピーしました' : 'リンクをコピー' }}</button>
            <router-link v-if="folderOf(articleId)" :to="`/gallery?folder=${articleId.split('-')[0]}`" class="pill">ギャラリーで見る</router-link>
          </div>
        </footer>
      </div>

      <!-- 前後の記事 -->
      <nav class="pager" aria-label="前後の記事">
        <router-link v-if="nextArticle" :to="`/article?id=${nextArticle.id}`" class="pager-card">
          <img v-if="coverOf(nextArticle.id)" :src="coverOf(nextArticle.id)" alt="" loading="lazy">
          <span><small>← 新しい記事</small><strong>{{ nextArticle.title }}</strong></span>
        </router-link>
        <span v-else class="pager-card empty"></span>
        <router-link v-if="prevArticle" :to="`/article?id=${prevArticle.id}`" class="pager-card right">
          <img v-if="coverOf(prevArticle.id)" :src="coverOf(prevArticle.id)" alt="" loading="lazy">
          <span><small>前の記事 →</small><strong>{{ prevArticle.title }}</strong></span>
        </router-link>
        <span v-else class="pager-card empty"></span>
      </nav>
      <p class="back"><router-link to="/blog" class="pill accent">記事一覧に戻る</router-link></p>
    </article>

    <ImageLightbox v-model:index="lightboxIndex" :images="lightboxImages" />
  </div>
</template>

<style scoped>
.article-page {
  --accent: #f39c12;
  --ink: #f4f4f5;
  --muted: #a1a1aa;
  --line: rgba(255, 255, 255, 0.1);
  min-height: 100vh;
  background: #0b0b0d;
  color: var(--ink);
  padding-bottom: 72px;
}
.progress {
  position: fixed;
  top: 64px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent);
  transform-origin: left;
  z-index: 40;
  pointer-events: none;
}
.state {
  padding: 160px 16px;
  text-align: center;
  color: var(--muted);
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  border-radius: 999px;
  border: 1px solid var(--line);
  color: var(--ink);
  font-size: 13px;
  font-weight: 700;
  transition: border-color 0.2s, background 0.2s;
}
.pill:hover { border-color: rgba(243, 156, 18, 0.6); background: rgba(243, 156, 18, 0.08); }
.pill.accent { border-color: var(--accent); color: var(--accent); }

/* ---- 冒頭 ---- */
.hero {
  position: relative;
  overflow: hidden;
  padding: 112px 16px 56px;
  border-bottom: 1px solid var(--line);
}
.hero-bg {
  position: absolute;
  inset: -40px;
  background-size: cover;
  background-position: center 30%;
  filter: blur(40px) saturate(1.2);
  opacity: 0.35;
  transform: scale(1.1);
}
.hero::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(11, 11, 13, 0.3) 0%, #0b0b0d 100%);
}
.hero-inner {
  position: relative;
  z-index: 1;
  max-width: 1080px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(0, 0.65fr);
  gap: 48px;
  align-items: center;
}
.crumbs { display: flex; gap: 8px; font-size: 12px; color: var(--muted); margin-bottom: 20px; }
.crumbs a:hover { color: var(--ink); }
.series { display: flex; align-items: center; gap: 12px; margin: 0 0 14px; font-size: 13px; color: #d4d4d8; letter-spacing: 0.08em; }
.badge { padding: 4px 10px; border-radius: 6px; background: var(--accent); color: #141414; font-weight: 900; font-size: 11px; letter-spacing: 0.14em; }
h1 {
  margin: 0;
  font-size: clamp(32px, 5vw, 56px);
  line-height: 1.2;
  font-weight: 900;
  letter-spacing: 0.02em;
  /* 日本語は単語の途中で折れやすいので、均等割り（balance）はしない */
  text-wrap: pretty;
  overflow-wrap: anywhere;
}
.series-name { margin: 14px 0 0; font-size: 15px; color: #d4d4d8; letter-spacing: 0.1em; }
.meta { display: flex; flex-wrap: wrap; gap: 8px 16px; margin: 22px 0 0; font-size: 12px; color: var(--muted); }
.hero-cover {
  justify-self: end;
  width: min(100%, 380px);
  aspect-ratio: 4 / 5;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 30px 80px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.08);
  transform: rotate(1.5deg);
  transition: transform 0.4s ease;
}
.hero-cover:not(:disabled):hover { transform: rotate(0) scale(1.02); }
.hero-cover img { width: 100%; height: 100%; object-fit: cover; display: block; }

/* ---- 本文 ---- */
.body {
  max-width: 720px;
  margin: 0 auto;
  padding: 48px 16px 0;
}
.prose { font-size: 16px; line-height: 2; color: #d4d4d8; }
.prose :deep(p) { margin: 0 0 1.1em; }
.prose :deep(a) { color: #fbbf24; text-decoration: underline; text-underline-offset: 3px; overflow-wrap: anywhere; }
.prose :deep(h2) { font-size: 22px; font-weight: 800; color: var(--ink); margin: 2.2em 0 0.8em; padding-left: 12px; border-left: 3px solid var(--accent); }
.prose :deep(h3) { font-size: 18px; font-weight: 800; color: var(--ink); margin: 1.8em 0 0.6em; }
.prose :deep(ul), .prose :deep(ol) { padding-left: 1.4em; margin: 0 0 1.4em; }
.prose :deep(ul) { list-style: disc; }
.prose :deep(ol) { list-style: decimal; }
.prose :deep(blockquote) { margin: 1.6em 0; padding: 12px 18px; border-left: 3px solid var(--accent); background: rgba(243, 156, 18, 0.06); border-radius: 0 10px 10px 0; color: #e4e4e7; }
.prose :deep(img) { max-width: 100%; border-radius: 12px; }

.gallery-block {
  /* 本文より広く使う */
  width: min(1080px, calc(100vw - 32px));
  margin: 32px 0 48px;
  position: relative;
  left: 50%;
  transform: translateX(-50%);
}
.gallery-head { display: flex; align-items: baseline; gap: 12px; margin: 0 0 14px; font-size: 12px; color: var(--muted); }
.gallery-head span { font-weight: 900; color: var(--accent); letter-spacing: 0.16em; }
.masonry { list-style: none; padding: 0; margin: 0; columns: 4 220px; column-gap: 12px; }
.masonry li { break-inside: avoid; margin-bottom: 12px; }
.masonry button,
.single button {
  display: block;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  background: #18181b;
  cursor: zoom-in;
}
.masonry img { width: 100%; height: auto; display: block; transition: transform 0.5s ease, opacity 0.3s; }
.masonry button:hover img,
.masonry button:focus-visible img { transform: scale(1.04); }
.more {
  display: block;
  margin: 8px auto 0;
  padding: 12px 28px;
  border-radius: 999px;
  border: 1px solid var(--accent);
  color: var(--accent);
  font-weight: 700;
  font-size: 14px;
}
.more:hover { background: var(--accent); color: #141414; }

.single { margin: 32px auto 40px; max-width: 520px; }
.single img { width: 100%; height: auto; display: block; }
.single figcaption { margin-top: 10px; font-size: 12px; color: var(--muted); text-align: center; line-height: 1.7; }

.embed { margin: 28px 0 40px; }
.embed.narrow { max-width: 360px; margin-inline: auto; }
.embed-label { margin: 0 0 10px; font-size: 11px; font-weight: 900; letter-spacing: 0.2em; color: var(--muted); }
.x-embed :deep(.twitter-tweet) {
  margin: 0 auto !important;
}
/* 埋め込みが読み込めないときに見えるリンク */
.x-embed blockquote {
  margin: 0;
  padding: 18px 20px;
  border-radius: 14px;
  border: 1px solid var(--line);
  background: #141418;
}
.x-embed blockquote a { color: var(--ink); font-weight: 700; }

.music {
  margin: 40px 0;
  padding: 22px;
  border-radius: 20px;
  background: linear-gradient(135deg, #1c1712 0%, #121214 70%);
  border: 1px solid rgba(243, 156, 18, 0.25);
  display: grid;
  gap: 18px;
}
.music-label { display: flex; align-items: center; gap: 10px; margin: 0; font-size: 11px; font-weight: 900; letter-spacing: 0.24em; color: var(--accent); }
.eq { display: inline-flex; gap: 2px; align-items: flex-end; height: 12px; }
.eq i { width: 3px; background: var(--accent); border-radius: 1px; animation: eq 1s ease-in-out infinite; }
.eq i:nth-child(2) { animation-delay: 0.2s; }
.eq i:nth-child(3) { animation-delay: 0.4s; }
@keyframes eq { 0%, 100% { height: 3px; } 50% { height: 12px; } }
.music-title { margin: 6px 0 0; font-size: clamp(24px, 4vw, 32px); font-weight: 900; line-height: 1.2; }
.music-artist { margin: 4px 0 0; font-size: 14px; color: #d4d4d8; letter-spacing: 0.08em; }

.pull-quote {
  margin: 44px 0 20px;
  padding: 8px 0 8px 28px;
  position: relative;
  border-left: 2px solid var(--accent);
}
.pull-quote::before {
  content: '“';
  position: absolute;
  left: 10px;
  top: -34px;
  font-family: 'Shippori Mincho', serif;
  font-size: 72px;
  color: rgba(243, 156, 18, 0.45);
  line-height: 1;
}
.pull-quote p {
  margin: 0;
  font-family: 'Shippori Mincho', serif;
  font-weight: 600;
  font-size: clamp(19px, 3vw, 24px);
  line-height: 1.9;
  color: var(--ink);
}

.channel {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 40px 0;
  padding: 18px 20px;
  border-radius: 18px;
  background: #141418;
  border: 1px solid var(--line);
  transition: border-color 0.2s, transform 0.2s;
}
.channel:hover { border-color: rgba(255, 0, 51, 0.6); transform: translateY(-2px); }
.yt-icon svg { width: 44px; height: 32px; display: block; }
.channel-text { flex: 1; display: grid; gap: 2px; }
.channel-text small { font-size: 11px; color: var(--muted); letter-spacing: 0.14em; }
.channel-text strong { font-size: 16px; }
.channel-text span { font-size: 12px; color: var(--muted); }
.channel-go { font-size: 22px; color: var(--muted); }

.article-foot { margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--line); }
.tags { list-style: none; padding: 0; margin: 0 0 20px; display: flex; flex-wrap: wrap; gap: 8px; }
.tags li { font-size: 12px; color: #d4d4d8; padding: 4px 10px; border-radius: 999px; background: #18181b; }
.share { display: flex; flex-wrap: wrap; gap: 10px; }

/* ---- 前後の記事 ---- */
.pager {
  max-width: 1080px;
  margin: 64px auto 0;
  padding: 0 16px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.pager-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px;
  border-radius: 16px;
  background: #141418;
  border: 1px solid var(--line);
  min-width: 0;
  transition: border-color 0.2s;
}
.pager-card:hover { border-color: rgba(243, 156, 18, 0.5); }
.pager-card.right { flex-direction: row-reverse; text-align: right; }
.pager-card.empty { visibility: hidden; }
.pager-card img { width: 64px; aspect-ratio: 4 / 5; object-fit: cover; border-radius: 10px; flex-shrink: 0; }
.pager-card span { display: grid; gap: 4px; min-width: 0; }
.pager-card small { font-size: 11px; color: var(--muted); letter-spacing: 0.1em; }
.pager-card strong { font-size: 14px; line-height: 1.5; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.back { text-align: center; margin: 32px 0 0; }

@media (max-width: 820px) {
  .hero { padding-top: 96px; }
  .hero-inner { grid-template-columns: 1fr; gap: 28px; }
  .hero-cover { justify-self: center; width: min(78%, 340px); }
  .pager { grid-template-columns: 1fr; }
  .pager-card.right { flex-direction: row; text-align: left; }
  .masonry { columns: 2; column-gap: 8px; }
  .masonry li { margin-bottom: 8px; }
}
@media (prefers-reduced-motion: reduce) {
  .eq i { animation: none; height: 8px; }
}
</style>