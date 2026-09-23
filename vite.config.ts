import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite' // ← これを追加

export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(), // ← これを追加
  ],
  build: {
    outDir: 'dist', // ← これを追加
    emptyOutDir: true,
  }
})
