import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AboutView from '../views/AboutView.vue'
import ConceptView from '../views/ConceptView.vue'
import PrivacyView from '../views/PrivacyView.vue' // ★追加
import ContactView from '../views/ContactView.vue'
import GearView from '../views/GearView.vue'
import SpecView from '../views/SpecView.vue'

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
  { path: '/spec', name: 'spec', component: SpecView },
  { path: '/privacy', name: 'privacy', component: PrivacyView }, // ★追加
  { path: '/contact', name: 'contact', component: ContactView }
  // 今後追加するページ
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router
