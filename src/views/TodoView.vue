<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Report {
  filename: string
  date: string
  title: string
}

const reports = ref<Report[]>([])
const currentPage = ref(1)
const itemsPerPage = 10

const totalPages = computed(() => Math.ceil(reports.value.length / itemsPerPage))

const paginatedReports = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage
  return reports.value.slice(start, start + itemsPerPage)
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
    const response = await fetch(`/assets/public_reports.json?t=${new Date().getTime()}`)
    if (!response.ok) throw new Error('Network response was not ok')
    const allReports: Report[] = await response.json()
    // -task-report (観測日誌) を含むものだけ抽出
    reports.value = allReports.filter(r => r.filename.includes('-task-report'))
  } catch (error) {
    console.error("日誌一覧の取得に失敗しました:", error)
  }
})
</script>

<template>
  <div class="bg-[url('/assets/images/erika-hero.jpg')] bg-fixed bg-cover bg-center min-h-screen pt-24 pb-12">
    <div class="container mx-auto px-4 max-w-4xl">
      <h1 class="text-4xl font-black text-white mb-2 drop-shadow-md">エリカの観測日誌</h1>
      <p class="text-zinc-400 mb-8">本日の技術検証テーマと解説動画</p>

      <div class="bg-black/60 backdrop-blur-md rounded-2xl p-6 md:p-8 border border-white/10 shadow-xl">
        <p v-if="reports.length === 0" class="text-zinc-400 animate-pulse">日誌データを読み込んでいます...</p>

        <!-- 記事リスト -->
        <div class="space-y-4">
          <div v-for="report in paginatedReports" :key="report.filename" 
               class="p-5 rounded-xl bg-white/5 border border-white/10 hover:border-cyan-500/50 hover:bg-white/10 transition-all duration-300">
            <router-link :to="`/todo-detail?id=${report.filename.replace('.md', '')}`" class="block group">
              <h2 class="text-lg md:text-xl font-bold text-white group-hover:text-cyan-400 transition-colors mb-2">
                {{ report.title }}
              </h2>
              <span class="inline-block px-2 py-1 bg-black text-zinc-300 text-xs rounded border border-zinc-800">Date: {{ report.date }}</span>
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
          <div class="flex gap-1 overflow-x-auto max-w-full pb-2 md:pb-0 hide-scrollbar">
            <button v-for="page in totalPages" :key="page" @click="goToPage(page)"
                    class="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold transition-colors shrink-0"
                    :class="page === currentPage ? 'bg-cyan-500 text-black' : 'bg-transparent text-zinc-400 hover:bg-white/10'">
              {{ page }}
            </button>
          </div>
        </nav>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hide-scrollbar::-webkit-scrollbar { display: none; }
.hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>