import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AboutView from '../views/AboutView.vue'
import ConceptView from '../views/ConceptView.vue'
import PrivacyView from '../views/PrivacyView.vue' // ★追加
import ContactView from '../views/ContactView.vue'
import GearView from '../views/GearView.vue'
import SpecView from '../views/SpecView.vue'
import GalleryView from '../views/GalleryView.vue' // ★追加
import BlogView from '../views/BlogView.vue' // ★追加
import ArticleView from '../views/ArticleView.vue' // ★追加
import GameView from '../views/GameView.vue'
import TodoView from '../views/TodoView.vue'
import TodoDetailView from '../views/TodoDetailView.vue'
import ReportsView from '../views/ReportsView.vue'
import ReportDetailView from '../views/ReportDetailView.vue'
import RpgView from '../views/RpgView.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/about', // ★追加
    name: 'about',
    component: AboutView
  },
  { path: '/concept', name: 'concept', component: ConceptView },
  { path: '/gear', name: 'gear', component: GearView },
  { path: '/game', name: 'game', component: GameView },
  { path: '/spec', name: 'spec', component: SpecView },
  { path: '/blog', name: 'blog', component: BlogView },
  { path: '/todo', name: 'todo', component: TodoView },
  { path: '/rpg', name: 'rpg', component: RpgView },
  { path: '/reports', name: 'reports', component: ReportsView },
  { path: '/report-detail', name: 'report-detail', component: ReportDetailView },
  { path: '/todo-detail', name: 'todo-detail', component: TodoDetailView },
  { path: '/article', name: 'article', component: ArticleView },
  { path: '/gallery', name: 'gallery', component: GalleryView }, // ★追加
  { path: '/privacy', name: 'privacy', component: PrivacyView }, // ★追加
  { path: '/contact', name: 'contact', component: ContactView }
  // 今後追加するページ
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
