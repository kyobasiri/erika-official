<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Article {
  id: string
  title: string
}

const articles = ref<Article[]>([])
const currentPage = ref(1)
const itemsPerPage = 10

const totalPages = computed(() => Math.ceil(articles.value.length / itemsPerPage))

const paginatedArticles = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return articles.value.slice(start, start + itemsPerPage)
})

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const goToPage = (page: number) => {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(async () => {
  try {
    const response = await fetch(`/assets/articles.json?t=${new Date().getTime()}`)
    if (!response.ok) throw new Error('Network response was not ok')
    articles.value = await response.json()
  } catch (error) {
    console.error("記事一覧の取得に失敗しました:", error)
  }
})
</script>

<template>
  <div class="bg-[url('/assets/images/erika-hero.jpg')] bg-fixed bg-cover bg-center min-h-screen pt-24 pb-12">
    <div class="container mx-auto px-4 max-w-4xl">
      <h1 class="text-4xl font-black text-white mb-2 drop-shadow-md">エリカの活動記録</h1>
      <p class="text-zinc-400 mb-8">Activities & Blogs</p>

      <div class="bg-black/60 backdrop-blur-md rounded-2xl p-6 md:p-8 border border-white/10 shadow-xl">
        <p v-if="articles.length === 0" class="text-zinc-400 animate-pulse">記事を読み込んでいます...</p>

        <!-- 記事リスト -->
        <div class="space-y-4">
          <div v-for="article in paginatedArticles" :key="article.id" 
               class="p-5 rounded-xl bg-white/5 border border-white/10 hover:border-erika/50 hover:bg-white/10 transition-all duration-300">
            <router-link :to="`/article?id=${article.id}`" class="block group">
              <h2 class="text-lg md:text-xl font-bold text-blue-400 group-hover:text-erika-light transition-colors mb-2">
                {{ article.title }}
              </h2>
              <p class="text-xs text-zinc-500 font-mono">File: {{ article.id }}.md</p>
            </router-link>
          </div>
        </div>

        <!-- ページネーション -->
        <nav v-if="totalPages > 1" class="mt-10 flex flex-col md:flex-row items-center justify-center gap-4">
          <div class="flex gap-2">
            <button @click="prevPage" :disabled="currentPage === 1" 
                    class="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-50 transition-colors font-bold text-sm">
              前のページ
            </button>
            <button @click="nextPage" :disabled="currentPage === totalPages" 
                    class="px-4 py-2 rounded-lg bg-zinc-800 text-zinc-300 hover:bg-zinc-700 disabled:opacity-50 transition-colors font-bold text-sm">
              次のページ
            </button>
          </div>
          <div class="flex gap-1 overflow-x-auto max-w-full pb-2 md:pb-0">
            <button v-for="page in totalPages" :key="page" @click="goToPage(page)"
                    class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold transition-colors"
                    :class="page === currentPage ? 'bg-erika text-black' : 'bg-transparent text-zinc-400 hover:bg-white/10'">
              {{ page }}
            </button>
          </div>
        </nav>
      </div>

    </div>
  </div>
</template>