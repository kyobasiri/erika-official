<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

// Cloudflare Pages は存在しないURLにも index.html を 200 で返すため、
// 検索エンジンにこのページを登録させないよう noindex を付ける（離れるときに外す）
let robotsMeta: HTMLMetaElement | null = null
let previousTitle = ''

onMounted(() => {
  previousTitle = document.title
  document.title = 'ページが見つかりません | Erika Official'
  robotsMeta = document.createElement('meta')
  robotsMeta.name = 'robots'
  robotsMeta.content = 'noindex'
  document.head.appendChild(robotsMeta)
})

onBeforeUnmount(() => {
  robotsMeta?.remove()
  robotsMeta = null
  document.title = previousTitle
})

const links = [
  { to: '/blog', label: 'ブログ', note: 'エリカの記事' },
  { to: '/gallery', label: 'ギャラリー', note: 'イラスト一覧' },
  { to: '/words', label: '好きな言葉', note: 'エリカが選んだ言葉' },
  { to: '/labyrinth', label: 'ゲーム', note: 'ラビリンスで遊ぶ' },
]
</script>

<template>
  <div class="bg-zinc-950 min-h-screen pt-24 pb-12 flex items-center">
    <div class="container mx-auto px-4 max-w-2xl">
      <div class="p-8 md:p-12 rounded-2xl bg-black/40 backdrop-blur-md border border-white/10 text-center">
        <p class="text-6xl md:text-7xl font-black text-erika tracking-widest mb-4">404</p>
        <h1 class="text-2xl md:text-3xl font-black text-white mb-6">ページが見つかりませんでした</h1>
        <p class="text-zinc-300 leading-relaxed mb-2">
          お探しのページは、移動したか削除された可能性があります。
        </p>
        <p class="text-zinc-500 text-sm mb-10 break-all">
          {{ route.fullPath }}
        </p>

        <router-link
          to="/"
          class="inline-block px-8 py-3 rounded-full border border-erika text-erika hover:bg-erika hover:text-black transition-all font-bold mb-10"
        >
          トップページへ戻る
        </router-link>

        <div class="grid grid-cols-2 gap-3 text-left">
          <router-link
            v-for="link in links"
            :key="link.to"
            :to="link.to"
            class="block px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-600 hover:bg-zinc-800 transition-colors"
          >
            <span class="block text-sm font-bold text-zinc-200">{{ link.label }}</span>
            <span class="block text-xs text-zinc-500">{{ link.note }}</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>
