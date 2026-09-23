<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'

interface ReportRef {
  filename: string
  title: string
  date: string
}

const route = useRoute()
const reportId = ref('')
const compiledMarkdown = ref('<p class="text-zinc-400 animate-pulse">読み込み中...</p>')

const prevReport = ref<ReportRef | null>(null)
const nextReport = ref<ReportRef | null>(null)

const youtubeId = ref<string | null>(null)
const audioUrl = ref<string | null>(null)

const parseMarkdown = async (text: string) => {
  const xLinkRegex = /^[ \t]*https?:\/\/(?:x\.com|twitter\.com)\/([a-zA-Z0-9_]+\/status\/\d+)[^\s<]*[ \t]*$/gm
  text = text.replace(xLinkRegex, '\n\n<div class="flex justify-center my-6"><blockquote class="twitter-tweet" data-align="center"><a href="https://twitter.com/$1"></a></blockquote></div>\n\n')

  const ytNormalRegex = /^[ \t]*https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)[^\s<]*[ \t]*$/gm
  text = text.replace(ytNormalRegex, '\n\n<div class="relative pb-[56.25%] h-0 overflow-hidden w-full my-6 rounded-xl shadow-lg"><iframe src="https://www.youtube.com/embed/$1" class="absolute top-0 left-0 w-full h-full border-none" allowfullscreen></iframe></div>\n\n')

  return await marked.parse(text)
}

const loadTwitterWidget = () => {
  if (!document.getElementById('twitter-wjs')) {
    const script = document.createElement('script')
    script.id = 'twitter-wjs'
    script.src = 'https://platform.twitter.com/widgets.js'
    script.async = true
    script.charset = 'utf-8'
    document.head.appendChild(script)
  }
  setTimeout(() => {
    // @ts-ignore
    if (window.twttr && window.twttr.widgets) window.twttr.widgets.load()
  }, 500)
}

const fetchReportData = async () => {
  const id = route.query.id as string
  if (!id || !id.includes('-task-report')) {
    compiledMarkdown.value = '<p class="text-red-500 font-bold">指定された日誌は存在しないか、非公開に設定されています。</p>'
    return
  }

  reportId.value = id
  compiledMarkdown.value = '<p class="text-zinc-400 animate-pulse">読み込み中...</p>'
  prevReport.value = null
  nextReport.value = null
  youtubeId.value = null
  audioUrl.value = null

  // YouTube ID取得
  try {
    const ytRes = await fetch(`/reports/${id}-youtube.txt`)
    if (ytRes.ok) youtubeId.value = (await ytRes.text()).trim()
  } catch (e) {}

  // 音声取得
  const potentialAudioPath = `/assets/audio/${id}.wav`
  try {
    const audioRes = await fetch(potentialAudioPath, { method: 'HEAD' })
    if (audioRes.ok) audioUrl.value = potentialAudioPath
  } catch (e) {}

  // 前後の日誌を取得
  try {
    const reportsRes = await fetch(`/assets/public_reports.json?t=${new Date().getTime()}`)
    if (reportsRes.ok) {
      const allReports: ReportRef[] = await reportsRes.json()
      const reports = allReports.filter(r => r.filename.includes('-task-report'))
      const currentIndex = reports.findIndex(r => r.filename.replace('.md', '') === id)
      
      if (currentIndex !== -1) {
        if (currentIndex < reports.length - 1) prevReport.value = reports[currentIndex + 1]
        if (currentIndex > 0) nextReport.value = reports[currentIndex - 1]
      }
    }
  } catch (e) {
    console.error("List fetch failed", e)
  }

  // Markdown取得
  try {
    const response = await fetch(`/reports/${id}.md`)
    if (!response.ok) throw new Error('Not found')
    let text = await response.text()

    if (text.trim().toLowerCase().startsWith('<!doctype html>') || text.trim().toLowerCase().startsWith('<html')) {
      throw new Error('Markdownファイルが見つからず、index.htmlが返却されました。')
    }

    text = text.replace(/\r/g, '')
    compiledMarkdown.value = await parseMarkdown(text)

    nextTick(() => {
      loadTwitterWidget()
    })
  } catch (error: any) {
    console.error(error)
    compiledMarkdown.value = `<p class="text-red-400 font-bold">記事の読み込みに失敗しました。</p>`
  }
}

onMounted(() => {
  fetchReportData()
})

watch(
  () => route.query.id,
  (newId) => {
    if (newId) {
      fetchReportData()
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }
)
</script>

<template>
  <div class="bg-zinc-950 min-h-screen pt-24 pb-12">
    <div class="container mx-auto px-4 max-w-4xl">
      
      <!-- メディアエリア -->
      <div v-if="youtubeId" class="bg-zinc-900 border border-zinc-700 rounded-2xl p-4 md:p-6 text-center mb-8 shadow-lg">
        <p class="text-white text-sm font-bold mb-4">📺 エリカの観測日誌動画</p>
        <div class="relative pb-[56.25%] h-0 overflow-hidden w-full max-w-3xl mx-auto rounded-xl shadow-md">
          <iframe :src="'https://www.youtube.com/embed/' + youtubeId" class="absolute top-0 left-0 w-full h-full border-none" allowfullscreen></iframe>
        </div>
      </div>
      <div v-else-if="audioUrl" class="bg-zinc-900 border border-zinc-700 rounded-2xl p-4 md:p-6 text-center mb-8 shadow-lg">
        <p class="text-white text-sm font-bold mb-4">🎧 エリカの音声解説</p>
        <audio controls :src="audioUrl" class="w-full max-w-md mx-auto outline-none"></audio>
      </div>

      <!-- 記事本文エリア -->
      <div class="bg-black/60 backdrop-blur-md rounded-2xl p-6 md:p-10 border border-white/10 shadow-2xl mb-12">
        <div class="markdown-body" v-html="compiledMarkdown"></div>
      </div>

      <!-- ページネーション -->
      <nav class="flex flex-col md:flex-row justify-between items-center gap-6 border-t border-white/10 pt-10">
        <div class="w-full md:w-1/3 text-center md:text-left">
          <router-link v-if="nextReport" :to="`/todo-detail?id=${nextReport.filename.replace('.md', '')}`" 
                       class="inline-block w-full px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white transition-colors truncate">
            &laquo; 次の日誌へ
          </router-link>
          <span v-else class="inline-block w-full px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-600 cursor-not-allowed">
            &laquo; 次の日誌へ
          </span>
        </div>

        <div class="w-full md:w-1/3 text-center">
          <router-link to="/todo" class="inline-block px-8 py-3 rounded-full border border-cyan-500 text-cyan-400 hover:bg-cyan-500 hover:text-black transition-all font-bold">
            観測日誌一覧に戻る
          </router-link>
        </div>

        <div class="w-full md:w-1/3 text-center md:text-right">
          <router-link v-if="prevReport" :to="`/todo-detail?id=${prevReport.filename.replace('.md', '')}`" 
                       class="inline-block w-full px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white transition-colors truncate">
            前の日誌へ &raquo;
          </router-link>
          <span v-else class="inline-block w-full px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-600 cursor-not-allowed">
            前の日誌へ &raquo;
          </span>
        </div>
      </nav>
    </div>
  </div>
</template>

<style>
/* BlogViewと共通のMarkdown用スタイル。観測日誌用にアクセントカラーをシアンに変更しています */
.markdown-body h1 { font-size: 1.875rem; font-weight: 900; color: #fff; margin-bottom: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 0.5rem; }
.markdown-body h2 { font-size: 1.5rem; font-weight: 700; color: #06b6d4; margin-top: 2rem; margin-bottom: 1rem; }
.markdown-body h3 { font-size: 1.25rem; font-weight: 700; color: #e5e7eb; margin-top: 1.5rem; margin-bottom: 0.75rem; }
.markdown-body p { color: #d1d5db; line-height: 1.8; margin-bottom: 1.25rem; }
.markdown-body a { color: #60a5fa; text-decoration: underline; }
.markdown-body a:hover { color: #93c5fd; }
.markdown-body ul { list-style-type: disc; padding-left: 1.5rem; color: #d1d5db; margin-bottom: 1.25rem; }
.markdown-body ol { list-style-type: decimal; padding-left: 1.5rem; color: #d1d5db; margin-bottom: 1.25rem; }
.markdown-body blockquote { border-left: 4px solid #06b6d4; padding-left: 1rem; color: #9ca3af; font-style: italic; margin-bottom: 1.25rem; background-color: rgba(6,182,214,0.05); padding: 1rem; border-radius: 0 0.5rem 0.5rem 0; }
</style>