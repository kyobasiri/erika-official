<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'

interface ArticleRef {
  id: string
  title: string
}

const route = useRoute()
const articleId = ref('')
const compiledMarkdown = ref('<p class="text-zinc-400 animate-pulse">読み込み中...</p>')

const prevArticle = ref<ArticleRef | null>(null)
const nextArticle = ref<ArticleRef | null>(null)

// Markdown描画後に独自のスタイルを適用するためのラッパー関数
const parseMarkdown = async (text: string) => {
  const xLinkRegex = /^[ \t]*https?:\/\/(?:x\.com|twitter\.com)\/([a-zA-Z0-9_]+\/status\/\d+)[^\s<]*[ \t]*$/gm
  text = text.replace(xLinkRegex, '\n\n<div class="flex justify-center my-6"><blockquote class="twitter-tweet" data-align="center"><a href="https://twitter.com/$1"></a></blockquote></div>\n\n')

  const ytShortsRegex = /^[ \t]*https?:\/\/(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]+)[^\s<]*[ \t]*$/gm
  text = text.replace(ytShortsRegex, '\n\n<div class="max-w-[320px] mx-auto my-6 rounded-xl overflow-hidden shadow-lg"><div class="relative pb-[177.77%] h-0"><iframe src="https://www.youtube.com/embed/$1" class="absolute top-0 left-0 w-full h-full border-none" allowfullscreen></iframe></div></div>\n\n')

  const ytNormalRegex = /^[ \t]*https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)[^\s<]*[ \t]*$/gm
  text = text.replace(ytNormalRegex, '\n\n<div class="relative pb-[56.25%] h-0 overflow-hidden w-full my-6 rounded-xl shadow-lg"><iframe src="https://www.youtube.com/embed/$1" class="absolute top-0 left-0 w-full h-full border-none" allowfullscreen></iframe></div>\n\n')

  return await marked.parse(text)
}

// X(Twitter)のウィジェットを動的に読み込み・再レンダリングする関数
const loadTwitterWidget = () => {
  if (!document.getElementById('twitter-wjs')) {
    const script = document.createElement('script')
    script.id = 'twitter-wjs'
    script.src = 'https://platform.twitter.com/widgets.js'
    script.async = true
    script.charset = 'utf-8'
    document.head.appendChild(script)
  }
  
  // 既にスクリプトがある、または追加された直後にDOMをスキャンさせる
  setTimeout(() => {
    // @ts-ignore
    if (window.twttr && window.twttr.widgets) {
      // @ts-ignore
      window.twttr.widgets.load()
    }
  }, 500)
}

// 記事データを取得する関数（使い回せるように分離）
const fetchArticleData = async () => {
  const id = (route.query.id as string) || '001-test'
  articleId.value = id
  compiledMarkdown.value = '<p class="text-zinc-400 animate-pulse">読み込み中...</p>'
  prevArticle.value = null
  nextArticle.value = null

  // 1. 前後の記事情報を取得
  try {
    const articlesRes = await fetch(`/assets/articles.json?t=${new Date().getTime()}`)
    if (articlesRes.ok) {
      const articles: ArticleRef[] = await articlesRes.json()
      const currentIndex = articles.findIndex(a => a.id === id)
      if (currentIndex !== -1) {
        if (currentIndex < articles.length - 1) prevArticle.value = articles[currentIndex + 1]
        if (currentIndex > 0) nextArticle.value = articles[currentIndex - 1]
      }
    }
  } catch (e) {
    console.error("Articles list fetch failed", e)
  }

  // 2. Markdown本文を取得してパース
  try {
    const response = await fetch(`/articles/${id}.md`)
    if (!response.ok) throw new Error('記事が見つかりません')
    let text = await response.text()

    if (text.trim().toLowerCase().startsWith('<!doctype html>') || text.trim().toLowerCase().startsWith('<html')) {
      throw new Error('Markdownファイルが見つからず、index.htmlが返却されました。publicフォルダ内の配置を確認してください。')
    }

    text = text.replace(/\r/g, '')
    compiledMarkdown.value = await parseMarkdown(text)

    // DOM更新後にTwitterウィジェットを実行
    nextTick(() => {
      loadTwitterWidget()
    })
  } catch (error) {
    console.error(error)
    compiledMarkdown.value = `<p class="text-red-400 font-bold">記事の読み込みに失敗しました。</p>`
  }
}

// 初回マウント時に実行
onMounted(() => {
  fetchArticleData()
})

// URLのクエリパラメータ (?id=xxx) が変更されたら、再度フェッチ処理を走らせる
watch(
  () => route.query.id,
  (newId) => {
    if (newId) {
      fetchArticleData()
      window.scrollTo({ top: 0, behavior: 'smooth' }) // ページトップへスクロール
    }
  }
)
</script>

<template>
  <div class="bg-zinc-950 min-h-screen pt-24 pb-12">
    <div class="container mx-auto px-4 max-w-4xl">
      
      <!-- 記事本文エリア -->
      <div class="bg-black/60 backdrop-blur-md rounded-2xl p-6 md:p-10 border border-white/10 shadow-2xl mb-12">
        <!-- 
          v-htmlでレンダリングされるMarkdown要素にスタイルを当てるため、
          "prose" クラス（通常はTailwind Typographyプラグインが必要）の代わりに
          親要素から子要素へ直接スタイルを指定するカスタムクラス `markdown-body` を設定しています。
        -->
        <div class="markdown-body" v-html="compiledMarkdown"></div>
      </div>

      <!-- ページネーション（前後の記事） -->
      <nav class="flex flex-col md:flex-row justify-between items-center gap-6 border-t border-white/10 pt-10">
        <!-- 次の記事（新しい記事：配列の-1） -->
        <div class="w-full md:w-1/3 text-center md:text-left">
          <router-link v-if="nextArticle" :to="`/article?id=${nextArticle.id}`" 
                       class="inline-block w-full px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white transition-colors truncate">
            &laquo; 次の記事へ
          </router-link>
          <span v-else class="inline-block w-full px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-600 cursor-not-allowed">
            &laquo; 次の記事へ
          </span>
        </div>

        <div class="w-full md:w-1/3 text-center">
          <router-link to="/blog" class="inline-block px-8 py-3 rounded-full border border-erika text-erika hover:bg-erika hover:text-black transition-all font-bold">
            記事一覧に戻る
          </router-link>
        </div>

        <!-- 前の記事（古い記事：配列の+1） -->
        <div class="w-full md:w-1/3 text-center md:text-right">
          <router-link v-if="prevArticle" :to="`/article?id=${prevArticle.id}`" 
                       class="inline-block w-full px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-700 text-zinc-300 hover:bg-zinc-800 hover:text-white transition-colors truncate">
            前の記事へ &raquo;
          </router-link>
          <span v-else class="inline-block w-full px-4 py-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-600 cursor-not-allowed">
            前の記事へ &raquo;
          </span>
        </div>
      </nav>

    </div>
  </div>
</template>

<style>
/* Markdownから生成されたHTML用のスタイル */
.markdown-body h1 {
  font-size: 1.875rem;
  font-weight: 900;
  color: #fff;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  padding-bottom: 0.5rem;
}
.markdown-body h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f39c12; /* エリカカラー */
  margin-top: 2rem;
  margin-bottom: 1rem;
}
.markdown-body h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: #e5e7eb;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}
.markdown-body p {
  color: #d1d5db;
  line-height: 1.8;
  margin-bottom: 1.25rem;
}
.markdown-body a {
  color: #60a5fa;
  text-decoration: underline;
}
.markdown-body a:hover {
  color: #93c5fd;
}
.markdown-body ul {
  list-style-type: disc;
  padding-left: 1.5rem;
  color: #d1d5db;
  margin-bottom: 1.25rem;
}
.markdown-body ol {
  list-style-type: decimal;
  padding-left: 1.5rem;
  color: #d1d5db;
  margin-bottom: 1.25rem;
}
.markdown-body blockquote {
  border-left: 4px solid #f39c12;
  padding-left: 1rem;
  color: #9ca3af;
  font-style: italic;
  margin-bottom: 1.25rem;
  background-color: rgba(243,156,18,0.05);
  padding: 1rem;
  border-radius: 0 0.5rem 0.5rem 0;
}
</style>