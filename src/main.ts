import { createApp } from 'vue'
import './style.css' // Tailwindを読み込んでいるCSS
import App from './App.vue'
import router from './router'

const app = createApp(App)

app.use(router)
app.mount('#app')
