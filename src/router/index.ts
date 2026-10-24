import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { nextTick } from 'vue'
import HomeView from '../views/HomeView.vue'

// ==========================================
// ページの一覧
//   ・トップページ（HomeView）だけは最初から読み込む（一番最初に開かれることが多いため）
//   ・それ以外は () => import(...) にして、そのページを開いたときに初めて読み込む
//     → ゲームなどの大きなページや、そのページだけで使うフォントの CSS を、
//       最初の表示でまとめて読み込まなくて済む
//   ・meta.title はブラウザのタブに出るページ名（下の afterEach で設定する）
// ==========================================

// タイトルの末尾につけるサイト名
const SITE_NAME = 'Erika Official'
// トップページなど、meta.title が無いときのタイトル
const DEFAULT_TITLE = 'Erika Official | AI Art & Music'

declare module 'vue-router' {
  interface RouteMeta {
    /** ブラウザのタブに出すページ名（「ページ名 | Erika Official」になる） */
    title?: string
  }
}

const routes: Array<RouteRecordRaw> = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/about', name: 'about', component: () => import('../views/AboutView.vue'), meta: { title: '運営者情報' } },
  { path: '/concept', name: 'concept', component: () => import('../views/ConceptView.vue'), meta: { title: 'プロジェクトの想い' } },
  { path: '/gear', name: 'gear', component: () => import('../views/GearView.vue'), meta: { title: '音をつくる道具' } },
  { path: '/spec', name: 'spec', component: () => import('../views/SpecView.vue'), meta: { title: '作品を生み出すPC' } },
  { path: '/blog', name: 'blog', component: () => import('../views/BlogView.vue'), meta: { title: 'エリカの活動記録' } },
  // 記事ページは、読み込んだ記事のタイトルを ArticleView 側で設定する（それまでの仮のタイトル）
  { path: '/article', name: 'article', component: () => import('../views/ArticleView.vue'), meta: { title: '記事' } },
  { path: '/gallery', name: 'gallery', component: () => import('../views/GalleryView.vue'), meta: { title: 'ギャラリー' } },
  { path: '/words', name: 'words', component: () => import('../views/WordsView.vue'), meta: { title: 'エリカの好きな言葉' } },
  { path: '/todo', name: 'todo', component: () => import('../views/TodoView.vue'), meta: { title: 'エリカの観測日誌' } },
  { path: '/todo-detail', name: 'todo-detail', component: () => import('../views/TodoDetailView.vue'), meta: { title: '観測日誌' } },
  { path: '/reports', name: 'reports', component: () => import('../views/ReportsView.vue'), meta: { title: 'エリカの日報' } },
  { path: '/report-detail', name: 'report-detail', component: () => import('../views/ReportDetailView.vue'), meta: { title: '日報' } },
  // ゲーム
  { path: '/game', name: 'game', component: () => import('../views/GameView.vue'), meta: { title: 'Memory Game' } },
  { path: '/rpg', name: 'rpg', component: () => import('../views/RpgView.vue'), meta: { title: 'エリカ討伐戦' } },
  { path: '/beat', name: 'beat', component: () => import('../views/BeatView.vue'), meta: { title: 'ERIKA BEAT' } },
  { path: '/labyrinth', name: 'labyrinth', component: () => import('../views/LabyrinthView.vue'), meta: { title: 'エリカの迷宮' } },
  { path: '/rock-action', name: 'rock-action', component: () => import('../views/ErikaRockAction.vue'), meta: { title: 'ERIKA ROCK ACTION' } },
  // 規約・お問い合わせ
  { path: '/privacy', name: 'privacy', component: () => import('../views/PrivacyView.vue'), meta: { title: 'プライバシーポリシー' } },
  { path: '/contact', name: 'contact', component: () => import('../views/ContactView.vue'), meta: { title: 'お問い合わせ' } },
  // 管理ページ（自分しか使わない）
  { path: '/admin/words', name: 'admin-words', component: () => import('../views/AdminWordsView.vue'), meta: { title: '好きな言葉の管理' } },
  // どのルートにも当てはまらないURL（必ず一番最後に置く）
  { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue'), meta: { title: 'ページが見つかりません' } }
]

// 固定ヘッダー（高さ 64px）に隠れないよう、#見出し へ飛ぶときに少し上をあける
const HEADER_OFFSET = 80

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  // ページを移動したときのスクロール位置
  scrollBehavior(to, from, savedPosition) {
    // ブラウザの「戻る」「進む」のときは、前に見ていた位置に戻す
    if (savedPosition) return savedPosition
    // URL に #見出し があれば、その見出しへ
    if (to.hash) return { el: to.hash, top: HEADER_OFFSET, behavior: 'smooth' }
    // 同じページの中で ?id= などが変わっただけのとき（言葉の詳細を開く、ギャラリーのフォルダを切り替える など）は動かさない
    if (to.path === from.path) return false
    // それ以外（別のページへ移動）は、いちばん上から表示する
    return { top: 0 }
  }
})

// 正規のURL（canonical）に使うサイトのアドレス。
// pages.dev のアドレスで開かれても、検索エンジンには本番のアドレスを伝える
const SITE_URL = 'https://erika.erikakataru.com'

// canonical の <link> を書き換える（index.html に1つ置いてある。無ければ作る）
function setCanonical(fullPath: string) {
  let link = document.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!link) {
    link = document.createElement('link')
    link.rel = 'canonical'
    document.head.appendChild(link)
  }
  // #見出し は除く。?id= は記事や日誌を見分けるのに必要なので残す
  link.href = SITE_URL + fullPath.split('#')[0]
}

// ページを移動したら、ブラウザのタブのタイトルと canonical を変える
router.afterEach((to) => {
  const title = to.meta.title ? `${to.meta.title} | ${SITE_NAME}` : DEFAULT_TITLE
  // 前のページが閉じるとき（onBeforeUnmount）にタイトルを元に戻すページがあるため、
  // 画面の切り替えが終わってから設定する（先に設定すると、戻されて上書きされてしまう）
  void nextTick(() => {
    document.title = title
  })
  setCanonical(to.fullPath)
})

export default router