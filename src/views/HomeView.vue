<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

interface Article {
  id: string
  title: string
}

interface Video {
  id: string
  title: string
}

interface FeaturedImage {
  src: string
  alt: string
}

const featuredImages: FeaturedImage[] = [
  {
    src: '/assets/images/featured/erika-pick-01.webp',
    alt: 'エリカのセレクトイラスト 01',
  },
  {
    src: '/assets/images/featured/erika-pick-02.webp',
    alt: 'エリカのセレクトイラスト 02',
  },
  {
    src: '/assets/images/featured/erika-pick-03.webp',
    alt: 'エリカのセレクトイラスト 03',
  },
  {
    src: '/assets/images/featured/erika-pick-04.webp',
    alt: 'エリカのセレクトイラスト 04',
  },
]

const games = [
  {
    to: '/labyrinth',
    number: '01',
    title: 'エリカの迷宮',
    category: 'DUNGEON',
    description: '一歩ずつ、未知の奥へ。迷宮を探索する冒険へ。',
    accent: '#a78bfa',
  },
  {
    to: '/beat',
    number: '02',
    title: 'ERIKA BEAT',
    category: 'RHYTHM',
    description: '音楽に合わせて、リズムを刻む。',
    accent: '#22d3ee',
  },
  {
    to: '/rpg',
    number: '03',
    title: 'エリカ討伐戦',
    category: 'RPG',
    description: '楽曲を力に変えて、エリカとの戦いに挑む。',
    accent: '#fb923c',
  },
  {
    to: '/game',
    number: '04',
    title: 'Memory Game',
    category: 'CARD',
    description: 'イラストを覚えて、同じ絵柄を見つけよう。',
    accent: '#f472b6',
  },
]

const projectLinks = [
  {
    to: '/concept',
    label: 'CONCEPT',
    title: 'プロジェクトの想い',
    description: '受け取った感動を、AIの翼で返したい。',
  },
  {
    to: '/spec',
    label: 'HARDWARE',
    title: '作品を生み出すPC',
    description: 'RTX 5090・Ryzen 9 9950X・128GB RAM。',
  },
  {
    to: '/gear',
    label: 'SOUND GEAR',
    title: '音をつくる道具',
    description: '楽曲制作を支える機材と制作環境。',
  },
]

const socialLinks = [
  { name: 'X', href: 'https://twitter.com/erikakataru' },
  {
    name: 'YouTube',
    href: 'https://youtube.com/channel/UCcLpUu88d6QTwZswJmOgtvw',
  },
  { name: 'note', href: 'https://note.com/erikakataru' },
  { name: 'Instagram', href: 'https://www.instagram.com/erikakataru/' },
  { name: 'Bluesky', href: 'https://bsky.app/profile/erikakataru.bsky.social' },
  { name: 'pixiv', href: 'https://www.pixiv.net/users/118819771' },
]

const recentArticles = ref<Article[]>([])
const articlesLoading = ref(true)
const articlesError = ref(false)

const latestVideo = ref<{ long: Video; short: Video }>({
  long: { id: 'kx8JnJVu89I', title: 'アルバムレビュー' },
  short: { id: 'PKHHj8DaxXs', title: 'エリカのShorts' },
})

const controller = new AbortController()
let disposed = false

function isVideo(value: unknown): value is Video {
  if (!value || typeof value !== 'object') return false

  const video = value as Record<string, unknown>

  return (
    typeof video.id === 'string' &&
    /^[a-zA-Z0-9_-]{11}$/.test(video.id) &&
    typeof video.title === 'string'
  )
}

async function fetchLatestVideo() {
  try {
    const response = await fetch(
      'https://erika-youtube-worker.kyobasiri.workers.dev',
      { signal: controller.signal },
    )

    if (!response.ok) return

    const data = await response.json()
    if (disposed || !data || typeof data !== 'object') return

    if (isVideo(data.long)) latestVideo.value.long = data.long
    if (isVideo(data.short)) latestVideo.value.short = data.short
  } catch {
    // 取得できない場合は設定済みの動画を表示
  }
}

async function fetchRecentArticles() {
  articlesLoading.value = true
  articlesError.value = false

  try {
    const response = await fetch('/assets/articles.json', {
      signal: controller.signal,
      cache: 'no-cache',
    })

    if (!response.ok) throw new Error('記事の取得に失敗しました')

    const data: unknown = await response.json()
    if (!Array.isArray(data)) throw new Error('記事の形式が不正です')
    if (disposed) return

    recentArticles.value = data
      .filter(
        (article): article is Article =>
          !!article &&
          typeof article === 'object' &&
          typeof article.id === 'string' &&
          typeof article.title === 'string',
      )
      .slice(0, 3)
  } catch {
    if (!disposed) articlesError.value = true
  } finally {
    if (!disposed) articlesLoading.value = false
  }
}

// 一押し画像の拡大表示
const selectedImage = ref<FeaturedImage | null>(null)
const naturalSize = ref(false)
const imageLoading = ref(false)
const imageFailed = ref(false)

const lightbox = ref<HTMLDivElement | null>(null)
const lightboxStage = ref<HTMLDivElement | null>(null)
const closeButton = ref<HTMLButtonElement | null>(null)

let returnFocusTo: HTMLElement | null = null
let previousBodyOverflow: string | null = null

async function openImage(image: FeaturedImage) {
  returnFocusTo =
    document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null

  previousBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'

  naturalSize.value = false
  imageLoading.value = true
  imageFailed.value = false
  selectedImage.value = image

  await nextTick()
  closeButton.value?.focus()
}

function restoreBodyScroll() {
  if (previousBodyOverflow !== null) {
    document.body.style.overflow = previousBodyOverflow
    previousBodyOverflow = null
  }
}

function closeImage() {
  selectedImage.value = null
  naturalSize.value = false
  restoreBodyScroll()
  returnFocusTo?.focus()
  returnFocusTo = null
}

async function toggleImageSize() {
  if (imageLoading.value || imageFailed.value) return

  naturalSize.value = !naturalSize.value
  await nextTick()

  if (lightboxStage.value) {
    lightboxStage.value.scrollTop = 0
    lightboxStage.value.scrollLeft = 0
  }
}

function handleImageError() {
  imageLoading.value = false
  imageFailed.value = true
}

function handleLightboxKey(event: KeyboardEvent) {
  if (!selectedImage.value) return

  if (event.key === 'Escape') {
    event.preventDefault()
    closeImage()
    return
  }

  if (event.key !== 'Tab' || !lightbox.value) return

  const focusable = Array.from(
    lightbox.value.querySelectorAll<HTMLElement>(
      'button:not([disabled]), a[href], [tabindex="0"]',
    ),
  )

  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (!first || !last) return

  const active = document.activeElement
  const isInside = lightbox.value.contains(active)

  if (event.shiftKey && (active === first || !isInside)) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && (active === last || !isInside)) {
    event.preventDefault()
    first.focus()
  }
}

onMounted(() => {
  void fetchRecentArticles()
  void fetchLatestVideo()
  document.addEventListener('keydown', handleLightboxKey, true)
})

onBeforeUnmount(() => {
  disposed = true
  controller.abort()
  restoreBodyScroll()
  document.removeEventListener('keydown', handleLightboxKey, true)
})
</script>

<template>
  <div class="erika-home">
    <!-- メインビジュアル -->
    <section class="hero page-width" aria-labelledby="home-title">
      <div class="hero-copy">
        <p class="eyebrow">ART · MUSIC · PLAY</p>

        <h1 id="home-title">ERIKA<span>.</span></h1>

        <p class="hero-lead">
          音楽から生まれる感動を、<br />
          イラストと遊びの世界へ。
        </p>

        <p class="hero-description">
          AIキャラクター「エリカ」と描く、<br />
          アート、音楽、ゲームのプロジェクト。
        </p>

        <div class="hero-actions">
          <a href="#featured" class="button button-primary">
            作品を見る <span aria-hidden="true">↗</span>
          </a>
          <a href="#games" class="button button-secondary">
            ゲームで遊ぶ <span aria-hidden="true">↓</span>
          </a>
        </div>

        <router-link to="/concept" class="concept-link">
          このプロジェクトについて <span aria-hidden="true">→</span>
        </router-link>
      </div>

      <div class="hero-art">
        <img
          src="/assets/images/erika-hero.jpg"
          alt="エリカのメインビジュアル"
          fetchpriority="high"
          decoding="async"
        />
        <div class="hero-art-caption">
          <span>ERIKA PROJECT</span>
          <span>AI ART & MUSIC</span>
        </div>
      </div>
    </section>

    <!-- ゲーム -->
    <section id="games" class="section page-width" aria-labelledby="games-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">PLAY</p>
          <h2 id="games-title">エリカの世界で遊ぶ</h2>
        </div>
        <p class="section-description">気になる世界へ、ここから。</p>
      </div>

      <div class="games-grid">
        <router-link
          v-for="game in games"
          :key="game.to"
          :to="game.to"
          class="game-card"
          :style="{ '--game-accent': game.accent }"
        >
          <div class="game-art" aria-hidden="true">
            <span class="game-number">{{ game.number }}</span>
            <span class="game-category">{{ game.category }}</span>
          </div>
          <div class="game-copy">
            <h3>{{ game.title }}</h3>
            <p>{{ game.description }}</p>
            <span class="game-action">
              遊ぶ <span aria-hidden="true">→</span>
            </span>
          </div>
        </router-link>
      </div>
    </section>

    <!-- 一押し作品 -->
    <section
      id="featured"
      class="section page-width"
      aria-labelledby="featured-title"
    >
      <div class="section-heading">
        <div>
          <p class="eyebrow">SELECTED ARTWORKS</p>
          <h2 id="featured-title">今、見てほしい4枚</h2>
        </div>
        <router-link to="/gallery" class="text-link">
          ギャラリーを見る <span aria-hidden="true">→</span>
        </router-link>
      </div>

      <div class="featured-grid">
        <button
          v-for="(image, index) in featuredImages"
          :key="image.src"
          type="button"
          class="artwork"
          :aria-label="`${image.alt}を拡大表示`"
          aria-haspopup="dialog"
          @click="openImage(image)"
        >
          <span class="artwork-image">
            <img
              :src="image.src"
              :alt="image.alt"
              width="1824"
              height="2304"
              loading="lazy"
              decoding="async"
            />
            <span class="artwork-open" aria-hidden="true">拡大 ↗</span>
          </span>
          <span class="artwork-caption">
            <span>ERIKA / SELECTED</span>
            <span>0{{ index + 1 }}</span>
          </span>
        </button>
      </div>

      <p class="section-note">
        画像をクリックすると拡大できます。
      </p>
    </section>

    <!-- 最新の発信 -->
    <section class="section updates-section" aria-labelledby="updates-title">
      <div class="page-width">
        <div class="section-heading">
          <div>
            <p class="eyebrow">LATEST STORIES</p>
            <h2 id="updates-title">音楽と、日々の記録</h2>
          </div>
        </div>

        <div class="updates-grid">
          <!-- レビューはHome上で再生可能 -->
          <div class="review-panel">
            <div class="subheading">
              <h3>最新のアルバムレビュー</h3>
              <span>REVIEW</span>
            </div>

            <div class="review-player">
              <iframe
                :key="latestVideo.long.id"
                :src="`https://www.youtube.com/embed/${latestVideo.long.id}`"
                :title="latestVideo.long.title"
                loading="lazy"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowfullscreen
                referrerpolicy="strict-origin-when-cross-origin"
              ></iframe>
            </div>

            <div class="review-caption">
              <p>{{ latestVideo.long.title }}</p>
              <a
                :href="`https://www.youtube.com/watch?v=${latestVideo.long.id}`"
                target="_blank"
                rel="noopener noreferrer"
                class="text-link"
              >
                YouTubeで見る ↗
              </a>
            </div>
          </div>

          <aside class="activity-panel" aria-labelledby="activity-title">
            <div class="subheading">
              <h3 id="activity-title">活動記録</h3>
              <router-link to="/blog" class="text-link">
                一覧 →
              </router-link>
            </div>

            <div aria-live="polite">
              <p v-if="articlesLoading" class="article-status">
                記事を読み込んでいます…
              </p>

              <div v-else-if="articlesError" class="article-status">
                <p>記事を読み込めませんでした。</p>
                <button
                  type="button"
                  class="text-link retry-button"
                  @click="fetchRecentArticles"
                >
                  再読み込み
                </button>
              </div>

              <p v-else-if="recentArticles.length === 0" class="article-status">
                現在、掲載されている記事はありません。
              </p>

              <div v-else class="article-list">
                <router-link
                  v-for="(article, index) in recentArticles"
                  :key="article.id"
                  :to="{ path: '/article', query: { id: article.id } }"
                  class="article-link"
                >
                  <span class="article-number">0{{ index + 1 }}</span>
                  <span class="article-title">{{ article.title }}</span>
                  <span class="article-arrow" aria-hidden="true">↗</span>
                </router-link>
              </div>
            </div>

            <router-link to="/todo" class="journal-link">
              <div>
                <span class="eyebrow">TECH LOG</span>
                <h3>エリカの観測日誌</h3>
                <p>技術検証と、日々の発見を記録。</p>
              </div>
              <span aria-hidden="true">→</span>
            </router-link>
          </aside>
        </div>

        <!-- Shortsはコンパクトに -->
        <a
          :href="`https://www.youtube.com/shorts/${latestVideo.short.id}`"
          target="_blank"
          rel="noopener noreferrer"
          class="shorts-link"
        >
          <img
            :src="`https://i.ytimg.com/vi/${latestVideo.short.id}/mqdefault.jpg`"
            alt=""
            width="320"
            height="180"
            loading="lazy"
            decoding="async"
          />
          <div class="shorts-copy">
            <span class="eyebrow">LATEST SHORT</span>
            <p>{{ latestVideo.short.title }}</p>
          </div>
          <span class="shorts-action">Shortsを見る ↗</span>
        </a>
      </div>
    </section>

    <!-- プロジェクト紹介 -->
    <section class="section page-width" aria-labelledby="project-title">
      <div class="section-heading">
        <div>
          <p class="eyebrow">BEHIND THE PROJECT</p>
          <h2 id="project-title">作品の、その向こう側</h2>
        </div>
      </div>

      <div class="project-grid">
        <router-link
          v-for="item in projectLinks"
          :key="item.to"
          :to="item.to"
          class="project-link"
        >
          <span class="eyebrow">{{ item.label }}</span>
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
          <span class="project-arrow" aria-hidden="true">↗</span>
        </router-link>
      </div>
    </section>

    <!-- SNS・フッター -->
    <footer class="site-footer">
      <div class="page-width">
        <div class="footer-top">
          <div>
            <p class="footer-brand">ERIKA<span>.</span></p>
            <p class="footer-description">アートと音楽、制作の続きを。</p>
          </div>

          <nav class="social-links" aria-label="SNS">
            <a
              v-for="social in socialLinks"
              :key="social.name"
              :href="social.href"
              target="_blank"
              rel="noopener noreferrer"
            >
              {{ social.name }} <span aria-hidden="true">↗</span>
            </a>
          </nav>
        </div>

        <div class="footer-bottom">
          <p>© {{ new Date().getFullYear() }} Erika Project.</p>
          <nav aria-label="サイト情報">
            <router-link to="/concept">Concept</router-link>
            <router-link to="/privacy">Privacy Policy</router-link>
            <router-link to="/contact">Contact</router-link>
          </nav>
        </div>
      </div>
    </footer>

    <!-- 画像拡大 -->
    <Teleport to="body">
      <div
        v-if="selectedImage"
        ref="lightbox"
        class="erika-lightbox"
        role="dialog"
        aria-modal="true"
        aria-labelledby="lightbox-title"
        aria-describedby="lightbox-help"
        @click.self="closeImage"
      >
        <header class="lightbox-toolbar">
          <div class="lightbox-heading">
            <p id="lightbox-title">{{ selectedImage.alt }}</p>
            <p id="lightbox-help">
              {{
                naturalSize
                  ? '原寸表示中・スクロールして細部を確認できます'
                  : '画像または原寸表示ボタンで拡大できます'
              }}
            </p>
          </div>

          <div class="lightbox-controls">
            <button
              type="button"
              :disabled="imageLoading || imageFailed"
              :aria-pressed="naturalSize"
              @click="toggleImageSize"
            >
              {{ naturalSize ? '全体表示' : '原寸表示' }}
            </button>
            <button
              ref="closeButton"
              type="button"
              aria-label="画像を閉じる"
              @click="closeImage"
            >
              閉じる ×
            </button>
          </div>
        </header>

        <div
          ref="lightboxStage"
          class="lightbox-stage"
          :class="{ 'is-natural': naturalSize }"
          tabindex="0"
          aria-label="拡大画像表示領域"
          @click.self="closeImage"
        >
          <p v-if="imageFailed" class="lightbox-message" role="status">
            画像を読み込めませんでした。
          </p>

          <div
            v-else
            class="lightbox-canvas"
            @click.self="closeImage"
          >
            <p
              v-if="imageLoading"
              class="lightbox-message"
              role="status"
            >
              画像を読み込んでいます…
            </p>
            <img
              :key="selectedImage.src"
              :src="selectedImage.src"
              :alt="selectedImage.alt"
              class="lightbox-image"
              :class="{ 'is-loading': imageLoading }"
              draggable="false"
              @load="imageLoading = false"
              @error="handleImageError"
              @click.stop="toggleImageSize"
            />
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.erika-home {
  --page-bg: #101113;
  --surface: #181a1e;
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

.erika-home *,
.erika-lightbox * {
  box-sizing: border-box;
}

.erika-home a {
  text-decoration: none;
}

.erika-home button,
.erika-lightbox button {
  font: inherit;
}

.erika-home a:focus-visible,
.erika-home button:focus-visible,
.erika-lightbox button:focus-visible,
.lightbox-stage:focus-visible {
  outline: 2px solid #f3a43b;
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

.hero {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
  padding-top: 112px;
  padding-bottom: 48px;
}

.hero-copy {
  padding-block: 24px;
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
  margin: 0 0 20px;
  font-size: clamp(21px, 2.3vw, 29px);
  font-weight: 700;
  line-height: 1.65;
  letter-spacing: 0.025em;
}

.hero-description {
  margin: 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.95;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 30px;
}

.button {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  gap: 20px;
  padding: 12px 22px;
  border: 1px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 700;
  transition: background 0.2s, transform 0.2s;
}

.button:hover {
  transform: translateY(-2px);
}

.button-primary {
  background: var(--accent);
  color: #19130b;
}

.button-primary:hover {
  background: #ffb956;
}

.button-secondary {
  border-color: rgba(255, 255, 255, 0.2);
  color: var(--text);
}

.button-secondary:hover {
  background: rgba(255, 255, 255, 0.06);
}

.concept-link {
  display: inline-flex;
  gap: 16px;
  margin-top: 24px;
  color: var(--muted);
  font-size: 13px;
}

.concept-link:hover {
  color: var(--text);
}

.hero-art {
  position: relative;
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

.hero-art-caption {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 13px 18px;
  border-top: 1px solid var(--line);
  color: #b2b2bb;
  font-size: 9px;
  letter-spacing: 0.15em;
}

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

.section-description,
.section-note {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.section-note {
  margin-top: 16px;
}

.text-link {
  color: var(--accent);
  font-size: 13px;
  font-weight: 600;
}

.text-link:hover {
  text-decoration: underline;
  text-underline-offset: 4px;
}

.games-grid,
.featured-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20px;
}

.game-card {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
  color: var(--text);
  transition: transform 0.2s, border-color 0.2s;
}

.game-card:hover {
  transform: translateY(-4px);
  border-color: var(--game-accent);
}

.game-art {
  position: relative;
  display: flex;
  height: 132px;
  align-items: end;
  padding: 20px;
  overflow: hidden;
  border-bottom: 1px solid var(--line);
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.04), transparent),
    #141519;
}

.game-art::after {
  position: absolute;
  right: -28px;
  top: -62px;
  width: 180px;
  height: 180px;
  border: 1px solid var(--game-accent);
  border-radius: 50%;
  opacity: 0.25;
  content: '';
}

.game-number {
  position: absolute;
  right: 14px;
  bottom: -25px;
  color: var(--game-accent);
  font-size: 98px;
  font-weight: 900;
  line-height: 1.4;
  opacity: 0.15;
}

.game-category {
  color: var(--game-accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.game-copy {
  padding: 20px;
}

.game-copy h3 {
  margin: 0 0 10px;
  font-size: 17px;
  font-weight: 700;
}

.game-copy p {
  min-height: 3.4em;
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.game-action {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 22px;
  color: var(--game-accent);
  font-size: 13px;
  font-weight: 600;
}

.artwork {
  min-width: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.artwork-image {
  position: relative;
  display: block;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
}

.artwork-image img {
  display: block;
  width: 100%;
  height: auto;
  aspect-ratio: 1824 / 2304;
  object-fit: contain;
  transition: filter 0.2s;
}

.artwork:hover img {
  filter: brightness(1.06);
}

.artwork-open {
  position: absolute;
  right: 10px;
  bottom: 10px;
  padding: 5px 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 5px;
  background: rgba(0, 0, 0, 0.65);
  color: #fff;
  font-size: 11px;
}

.artwork-caption {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 12px;
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.1em;
}

.updates-section {
  margin-top: 24px;
  border-block: 1px solid var(--line);
  background: #141518;
}

.updates-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.8fr) minmax(0, 1fr);
  gap: 36px;
  align-items: start;
}

.subheading {
  display: flex;
  min-height: 30px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.subheading h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.subheading > span {
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.12em;
}

.review-player {
  overflow: hidden;
  width: 100%;
  aspect-ratio: 16 / 9;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #000;
}

.review-player iframe {
  display: block;
  width: 100%;
  height: 100%;
  border: 0;
}

.review-caption {
  display: flex;
  flex-wrap: wrap;
  align-items: start;
  justify-content: space-between;
  gap: 12px;
  padding-top: 15px;
}

.review-caption p {
  flex: 1 1 240px;
  margin: 0;
  font-size: 14px;
  overflow-wrap: anywhere;
}

.review-caption a {
  flex-shrink: 0;
}

.article-status {
  padding-block: 24px;
  color: var(--muted);
  font-size: 13px;
}

.retry-button {
  margin-top: 10px;
  padding: 0;
  border: 0;
  background: none;
  cursor: pointer;
}

.article-link {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr) 14px;
  gap: 10px;
  align-items: start;
  padding: 17px 0;
  border-bottom: 1px solid var(--line);
  color: var(--text);
}

.article-link:first-child {
  border-top: 1px solid var(--line);
}

.article-number,
.article-arrow {
  padding-top: 3px;
  color: var(--muted);
  font-size: 11px;
}

.article-title {
  display: -webkit-box;
  overflow: hidden;
  font-size: 14px;
  line-height: 1.7;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.article-link:hover .article-title {
  color: var(--accent);
}

.journal-link {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 22px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: 9px;
  background: var(--surface);
  color: var(--text);
}

.journal-link:hover {
  border-color: rgba(243, 164, 59, 0.45);
}

.journal-link .eyebrow {
  margin-bottom: 5px;
  font-size: 9px;
}

.journal-link h3 {
  margin: 0 0 5px;
  font-size: 15px;
  font-weight: 600;
}

.journal-link p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
}

.shorts-link {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
  color: var(--text);
}

.shorts-link > img {
  width: 112px;
  height: 63px;
  flex-shrink: 0;
  border-radius: 6px;
  object-fit: cover;
}

.shorts-copy {
  min-width: 0;
  flex: 1;
}

.shorts-copy .eyebrow {
  margin-bottom: 5px;
  font-size: 9px;
}

.shorts-copy p {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  font-size: 13px;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.shorts-action {
  color: var(--muted);
  font-size: 12px;
}

.shorts-link:hover .shorts-action {
  color: var(--accent);
}

.project-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 24px;
}

.project-link {
  position: relative;
  padding: 24px 30px 24px 0;
  border-top: 1px solid var(--line);
  color: var(--text);
}

.project-link .eyebrow {
  font-size: 10px;
}

.project-link h3 {
  margin: 0 0 8px;
  font-size: 17px;
  font-weight: 600;
}

.project-link p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.project-arrow {
  position: absolute;
  right: 0;
  top: 25px;
  color: var(--muted);
}

.project-link:hover h3,
.project-link:hover .project-arrow {
  color: var(--accent);
}

.site-footer {
  margin-top: 16px;
  padding: 42px 0 28px;
  border-top: 1px solid var(--line);
  background: #0c0d0f;
}

.footer-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 32px;
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
  justify-content: flex-end;
  gap: 12px 22px;
}

.social-links a {
  padding-block: 7px;
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

.footer-bottom {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  margin-top: 32px;
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

/* 拡大表示：Teleport先にもscopedスタイルは適用されます */
.erika-lightbox {
  position: fixed;
  z-index: 9999;
  inset: 0;
  display: flex;
  flex-direction: column;
  background: rgba(6, 7, 9, 0.96);
  color: #f4f4f5;
}

.lightbox-toolbar {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  background: #111216;
}

.lightbox-heading {
  min-width: 0;
}

.lightbox-heading p {
  margin: 0;
  font-size: 13px;
}

.lightbox-heading p + p {
  margin-top: 4px;
  color: #aaaab4;
  font-size: 11px;
}

.lightbox-controls {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
}

.lightbox-controls button {
  min-height: 44px;
  padding: 8px 14px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  border-radius: 6px;
  background: #22242a;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}

.lightbox-controls button:hover {
  background: #30323a;
}

.lightbox-controls button:disabled {
  opacity: 0.45;
  cursor: default;
}

.lightbox-stage {
  position: relative;
  min-height: 0;
  flex: 1;
  overflow: auto;
  overscroll-behavior: contain;
  padding: 20px;
  scrollbar-color: #62626d #17181d;
}

.lightbox-canvas {
  position: relative;
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
}

.lightbox-image {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
  flex-shrink: 0;
  object-fit: contain;
  cursor: zoom-in;
}

.lightbox-image.is-loading {
  opacity: 0;
}

.lightbox-stage.is-natural .lightbox-canvas {
  width: max-content;
  height: max-content;
  min-width: 100%;
  min-height: 100%;
}

.lightbox-stage.is-natural .lightbox-image {
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  cursor: zoom-out;
}

.lightbox-message {
  position: absolute;
  top: 50%;
  left: 50%;
  margin: 0;
  transform: translate(-50%, -50%);
  color: #c7c7d0;
  font-size: 14px;
  text-align: center;
}

@media (max-width: 1023px) {
  .hero {
    gap: 32px;
  }

  .games-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .game-art {
    height: 110px;
  }

  .game-copy p {
    min-height: 0;
  }

  .updates-grid {
    gap: 26px;
    grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr);
  }

  .footer-top {
    align-items: start;
  }
}

@media (max-width: 767px) {
  .page-width {
    width: calc(100% - 36px);
  }

  .section {
    padding-block: 40px;
    scroll-margin-top: 80px;
  }

  .hero {
    grid-template-columns: 1fr;
    gap: 26px;
    padding-top: 92px;
    padding-bottom: 22px;
  }

  .hero-copy {
    padding: 0;
  }

  .hero h1 {
    font-size: 80px;
    margin-bottom: 18px;
  }

  .hero-lead {
    font-size: 23px;
    margin-bottom: 14px;
  }

  .hero-description {
    font-size: 13px;
  }

  .hero-actions {
    margin-top: 24px;
  }

  .button {
    padding-inline: 18px;
    gap: 14px;
  }

  .concept-link {
    margin-top: 18px;
  }

  .hero-art > img {
    height: auto;
    max-height: 440px;
    object-fit: contain;
  }

  .section-heading {
    flex-wrap: wrap;
    align-items: start;
    gap: 12px;
    margin-bottom: 22px;
  }

  .section-heading h2 {
    font-size: 23px;
  }

  .section-description {
    width: 100%;
  }

  .games-grid,
  .featured-grid {
    gap: 14px;
  }

  .featured-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    row-gap: 24px;
  }

  .game-art {
    height: 95px;
    padding: 14px;
  }

  .game-category {
    font-size: 10px;
  }

  .game-number {
    font-size: 78px;
  }

  .game-copy {
    padding: 16px 14px;
  }

  .game-copy h3 {
    font-size: 15px;
  }

  .game-copy p {
    min-height: 5.1em;
    font-size: 12px;
  }

  .game-action {
    margin-top: 16px;
  }

  .artwork-caption {
    font-size: 8px;
    letter-spacing: 0.06em;
  }

  .updates-section {
    margin-top: 10px;
  }

  .updates-grid {
    grid-template-columns: 1fr;
    gap: 34px;
  }

  .shorts-link {
    flex-wrap: wrap;
    gap: 12px;
  }

  .shorts-link > img {
    width: 96px;
    height: 54px;
  }

  .shorts-action {
    width: 100%;
    text-align: right;
  }

  .project-grid {
    grid-template-columns: 1fr;
    gap: 0;
  }

  .project-link {
    padding-block: 22px;
  }

  .footer-top,
  .footer-bottom {
    flex-direction: column;
    gap: 22px;
  }

  .social-links {
    justify-content: flex-start;
    gap: 8px 22px;
  }

  .lightbox-toolbar {
    align-items: start;
    flex-direction: column;
    gap: 12px;
    padding: 12px 16px;
  }

  .lightbox-controls {
    width: 100%;
    justify-content: flex-end;
  }

  .lightbox-stage {
    padding: 12px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .erika-home *,
  .erika-lightbox * {
    transition: none !important;
    scroll-behavior: auto !important;
  }
}
</style>