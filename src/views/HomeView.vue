<template>
<!-- 背景画像をここで指定。パスは public フォルダ基準の絶対パス -->
<div class="bg-[url('/assets/images/erika-hero.jpg')] bg-fixed bg-cover bg-center min-h-screen">

  <!-- トップセクション -->
  <section class="relative min-h-[80vh] flex flex-col items-center justify-center py-20 overflow-hidden z-10">
    <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] md:w-[700px] h-[400px] md:h-[700px] bg-erika/10 rounded-full blur-[100px] pointer-events-none -z-10"></div>
    <div class="container mx-auto px-4 text-center">
      <p class="text-xs md:text-sm font-bold text-erika-light uppercase tracking-[0.5em] mb-4">
        AI Artist & Album Reviewer
      </p>
      <h1 class="text-7xl md:text-8xl lg:text-9xl font-black text-white tracking-tighter mb-8 drop-shadow-[0_0_20px_rgba(255,255,255,0.2)]">
        ERIKA.
      </h1>
      <div class="mt-8">
        <p class="text-zinc-400 text-sm mb-6">このプロジェクトの背景にある想い</p>
        <router-link to="/concept" class="inline-block px-8 py-3 rounded-full border border-white/10 bg-white/5 backdrop-blur-md text-white font-medium transition-all duration-300 hover:bg-white/10 hover:border-white/30 hover:shadow-[0_0_20px] hover:shadow-white/20 hover:-translate-y-1">
          Concept
        </router-link>
      </div>
    </div>
  </section>

  <!-- 活動記録セクション -->
  <section class="py-16 md:py-24 relative z-10">
    <div class="container mx-auto px-4 max-w-6xl">
      <div class="mb-16">
        <div class="flex flex-col md:flex-row justify-between items-end mb-8">
          <div>
            <h2 class="text-3xl font-black text-erika mb-2">Activities</h2>
            <p class="text-zinc-400 text-sm">エリカの活動記録（最新記事）</p>
          </div>
          <a href="/blog" class="hidden md:inline-flex items-center text-sm font-bold text-zinc-400 hover:text-erika-light transition-colors">
            すべての記事を読む <span class="ml-1">→</span>
          </a>
        </div>

        <div v-if="recentArticles.length === 0" class="text-zinc-500 animate-pulse flex items-center gap-3 py-8">
          <svg class="animate-spin h-5 w-5 text-erika" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          記事を読み込んでいます...
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div v-for="article in recentArticles" :key="article.id" class="group">
            <a :href="`/article?id=${article.id}`" class="flex flex-col h-full p-6 rounded-2xl bg-black/40 backdrop-blur-md border border-white/10 transition-all duration-300 hover:-translate-y-1 hover:border-erika/50 hover:shadow-[0_0_20px_rgba(243,156,18,0.15)] relative overflow-hidden">
              <div class="absolute left-0 top-0 w-1 h-full bg-erika opacity-0 transition-opacity duration-300 group-hover:opacity-100"></div>
              <h3 class="text-lg font-bold text-white mb-4 line-clamp-2 group-hover:text-erika-light transition-colors leading-relaxed">
                {{ article.title }}
              </h3>
              <p class="text-xs text-zinc-500 mt-auto font-mono">{{ article.id }}</p>
            </a>
          </div>
        </div>
      </div>

      <!-- 観測日誌バナー -->
      <div class="relative overflow-hidden rounded-3xl bg-zinc-900/80 backdrop-blur-md border border-white/10 p-8 md:p-12 text-center shadow-[0_0_30px_rgba(0,0,0,0.5)]">
        <div class="absolute top-0 right-0 -mr-20 -mt-20 w-64 h-64 bg-cyan-500/10 rounded-full blur-[80px] pointer-events-none"></div>
        <div class="absolute bottom-0 left-0 -ml-20 -mb-20 w-64 h-64 bg-erika/10 rounded-full blur-[80px] pointer-events-none"></div>
        <div class="relative z-10">
          <span class="inline-block px-3 py-1 mb-4 text-xs font-bold text-cyan-400 bg-cyan-400/10 rounded-full border border-cyan-400/20">
            Tech Log
          </span>
          <h3 class="text-2xl md:text-3xl font-black text-white mb-4">📝 エリカの観測日誌</h3>
          <p class="text-zinc-400 text-sm md:text-base mb-8 max-w-xl mx-auto leading-relaxed">
            Google ToDoのタスクを活用した、本日の技術検証テーマと解説動画を毎日お届けしています。
          </p>
          <a href="/todo" class="inline-flex items-center px-8 py-3 text-sm font-bold text-zinc-900 bg-zinc-100 rounded-full transition-all duration-300 hover:bg-white hover:shadow-[0_0_20px_rgba(255,255,255,0.3)] hover:-translate-y-1">
            観測日誌一覧を見る
          </a>
        </div>
      </div>
    </div>
  </section>

  <!-- メインメニューカードセクション (コンポーネント化) -->
  <section class="py-12 md:py-20 relative z-10">
    <div class="container mx-auto px-4 max-w-6xl">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <MenuCard to="/gear" title="Music Gear" desc="Squier & BOSS IR-2." />
        <MenuCard to="/spec" title="PC Hardware" desc="RTX 5090 / 128GB RAM." />
        <MenuCard to="/gallery" title="Gallery" desc="AI Art Archive." />
        <MenuCard to="/game" title="Memory Game" desc="AI Art Match." />
        <MenuCard to="/rpg" title="RPG Battle" desc="エリカ討伐戦" />
      </div>
    </div>
  </section>

  <!-- 最新レビューセクション -->
  <section class="py-16 md:py-24 relative z-10">
    <div class="container mx-auto px-4 max-w-6xl">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        <div class="lg:col-span-7">
          <h2 class="text-3xl font-black text-erika mb-1">Latest Review</h2>
          <p class="text-zinc-400 text-sm mb-6">最新のアルバムレビュー</p>
          <div class="rounded-2xl overflow-hidden bg-black/40 backdrop-blur-md border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.5)]">
            <div class="aspect-video relative w-full bg-black">
              <iframe class="absolute top-0 left-0 w-full h-full" :src="`https://www.youtube.com/embed/${latestVideo.long.id}`" title="Main Review" frameborder="0" allowfullscreen></iframe>
            </div>
            <div class="p-5 bg-white/5 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <p class="text-white font-medium truncate w-full">{{ latestVideo.long.title }}</p>
              <a :href="`https://www.youtube.com/watch?v=${latestVideo.long.id}`" target="_blank" class="shrink-0 px-5 py-2 text-sm font-bold text-erika-light border border-erika/50 rounded-full transition-all duration-300 hover:bg-erika/10 hover:shadow-[0_0_15px_rgba(243,156,18,0.2)]">
                ▶ Watch on YouTube
              </a>
            </div>
          </div>
        </div>
        <div class="lg:col-span-5">
          <h2 class="text-3xl font-black text-erika mb-1">Daily Shorts</h2>
          <p class="text-zinc-400 text-sm mb-6">毎日更新中！</p>
          <div class="max-w-[320px] mx-auto rounded-[24px] overflow-hidden bg-black/40 backdrop-blur-md border border-white/10 shadow-[0_0_30px_rgba(0,0,0,0.5)] transition-transform duration-300 hover:-translate-y-2">
            <div class="aspect-[9/16] relative w-full bg-black">
              <iframe class="absolute top-0 left-0 w-full h-full" :src="`https://www.youtube.com/embed/${latestVideo.short.id}`" title="Shorts" frameborder="0" allowfullscreen></iframe>
            </div>
            <div class="p-4 bg-white/5 text-center">
              <p class="text-zinc-300 text-sm mb-3 line-clamp-2">{{ latestVideo.short.title }}</p>
              <a :href="`https://www.youtube.com/shorts/${latestVideo.short.id}`" target="_blank" class="inline-block px-6 py-2 text-sm font-bold text-zinc-900 bg-zinc-100 rounded-full transition-all duration-300 hover:bg-white hover:shadow-[0_0_15px_rgba(255,255,255,0.4)]">
                📱 Open Shorts
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <!-- リンク集セクション -->
  <section class="py-16 md:py-24 relative z-10 border-t border-white/10">
    <div class="container mx-auto px-4 max-w-4xl text-center">
      <h3 class="text-3xl font-black text-white mb-4 drop-shadow-[0_0_15px_rgba(255,255,255,0.2)]">Connect
        with Project</h3>
      <p class="text-zinc-400 text-sm md:text-base mb-12 max-w-2xl mx-auto leading-relaxed">
        エリカが描く新しい世界や、制作の裏側にある試行錯誤。<br class="hidden md:block">
        リスペクトの表現を、リアルタイムで発信しています。
      </p>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
        <a href="https://twitter.com/erikakataru" target="_blank"
          class="group flex flex-col justify-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-300 hover:bg-white/10 hover:border-zinc-400 hover:shadow-[0_0_15px] hover:shadow-white/10 hover:-translate-y-1">
          <p class="text-xs text-zinc-400 mb-2">【毎日更新】最新のAIアートと制作の断片</p>
          <div class="flex items-center justify-between">
            <span class="text-lg font-bold text-white group-hover:text-zinc-200">X (Twitter)</span>
            <span class="text-zinc-600 group-hover:text-white transition-colors duration-300">↗</span>
          </div>
        </a>
        <a href="https://youtube.com/channel/UCcLpUu88d6QTwZswJmOgtvw" target="_blank"
          class="group flex flex-col justify-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-300 hover:bg-white/10 hover:border-erika/50 hover:shadow-[0_0_15px] hover:shadow-erika/15 hover:-translate-y-1">
          <p class="text-xs text-zinc-400 mb-2">【Main】独自の視点で語るメインチャンネル</p>
          <div class="flex items-center justify-between">
            <span class="text-lg font-bold text-white group-hover:text-erika-light transition-colors">YouTube Channel</span>
            <span class="text-zinc-600 group-hover:text-erika-light transition-colors duration-300">↗</span>
          </div>
        </a>
        <a href="https://note.com/erikakataru" target="_blank"
          class="group flex flex-col justify-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-300 hover:bg-white/10 hover:border-emerald-500/50 hover:shadow-[0_0_15px] hover:shadow-emerald-500/15 hover:-translate-y-1">
          <p class="text-xs text-zinc-400 mb-2">【毎日更新】制作の裏側にある思考を綴るログ</p>
          <div class="flex items-center justify-between">
            <span class="text-lg font-bold text-white group-hover:text-emerald-400 transition-colors">note</span>
            <span class="text-zinc-600 group-hover:text-emerald-400 transition-colors duration-300">↗</span>
          </div>
        </a>
        <a href="https://www.instagram.com/erikakataru/" target="_blank"
          class="group flex flex-col justify-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-300 hover:bg-white/10 hover:border-pink-500/50 hover:shadow-[0_0_15px] hover:shadow-pink-500/15 hover:-translate-y-1">
          <p class="text-xs text-zinc-400 mb-2">【毎日更新】ビジュアル重視のタイムライン</p>
          <div class="flex items-center justify-between">
            <span class="text-lg font-bold text-white group-hover:text-pink-400 transition-colors">Instagram</span>
            <span class="text-zinc-600 group-hover:text-pink-400 transition-colors duration-300">↗</span>
          </div>
        </a>
        <a href="https://bsky.app/profile/erikakataru.bsky.social" target="_blank"
          class="group flex flex-col justify-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-300 hover:bg-white/10 hover:border-blue-500/50 hover:shadow-[0_0_15px] hover:shadow-blue-500/15 hover:-translate-y-1">
          <p class="text-xs text-zinc-400 mb-2">【毎日更新】新たな発信とコミュニティ形成</p>
          <div class="flex items-center justify-between">
            <span class="text-lg font-bold text-white group-hover:text-blue-400 transition-colors">Bluesky</span>
            <span class="text-zinc-600 group-hover:text-blue-400 transition-colors duration-300">↗</span>
          </div>
        </a>
        <a href="https://www.pixiv.net/users/118819771" target="_blank"
          class="group flex flex-col justify-center p-6 rounded-2xl bg-white/5 border border-white/10 backdrop-blur-md transition-all duration-300 hover:bg-white/10 hover:border-cyan-500/50 hover:shadow-[0_0_15px] hover:shadow-cyan-500/15 hover:-translate-y-1">
          <p class="text-xs text-zinc-400 mb-2">【Archive】高解像度アートの集積・保管庫</p>
          <div class="flex items-center justify-between">
            <span class="text-lg font-bold text-white group-hover:text-cyan-400 transition-colors">Pixiv</span>
            <span class="text-zinc-600 group-hover:text-cyan-400 transition-colors duration-300">↗</span>
          </div>
        </a>
      </div>

      <div class="mt-8">
        <a href="https://lit.link/erikakataru" target="_blank"
          class="inline-block text-xs text-zinc-500 hover:text-zinc-300 transition-colors border-b border-transparent hover:border-zinc-500 pb-1">
          旧まとめページ (Lit.Link) はこちら
        </a>
      </div>
    </div>
  </section>

  <!-- フッター -->
  <footer class="bg-black py-12 border-t border-white/10 relative z-10">
    <div class="container mx-auto px-4 text-center">
      <p class="text-zinc-500 text-sm mb-4">&copy; 2026 Erika Project. Managed by In-house SE.</p>
      <div class="flex justify-center gap-4 text-sm text-zinc-600 mb-12">
        <router-link to="/about" class="hover:text-zinc-300 transition-colors">About</router-link>
        <span class="text-zinc-800">|</span>
        <router-link to="/privacy" class="hover:text-zinc-300 transition-colors">Privacy Policy</router-link>
        <span class="text-zinc-800">|</span>
        <router-link to="/contact" class="hover:text-zinc-300 transition-colors">Contact</router-link>
      </div>
    </div>
  </footer>
</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import MenuCard from '../components/MenuCard.vue';

// TypeScriptの型定義（APIから受け取るデータの形を明記）
interface Article {
  id: string;
  title: string;
}

const status = ref('CHECKING...');
const recentArticles = ref<Article[]>([]);
const MANAGER_URL = "https://manager.erikakataru.com";
let intervalId: ReturnType<typeof setInterval> | null = null;

const latestVideo = ref({
  long: { id: 'kx8JnJVu89I', title: 'Latest Review' },
  short: { id: 'PKHHj8DaxXs', title: 'Latest Short' }
});

const YOUTUBE_WORKER_URL = "https://erika-youtube-worker.kyobasiri.workers.dev";

const fetchLatestVideo = async () => {
  try {
    const res = await fetch(YOUTUBE_WORKER_URL);
    if (res.ok) {
      const data = await res.json();
      if (data.long && !data.long.error) latestVideo.value.long = data.long;
      if (data.short && !data.short.error) latestVideo.value.short = data.short;
    }
  } catch (e) {
    console.error("YouTube sync failed", e);
  }
};

const checkStatus = async () => {
  try {
    const response = await fetch(`${MANAGER_URL}/api/status`);
    if (response.ok) {
      const data = await response.json();
      status.value = data.running ? 'ONLINE' : 'OFFLINE';
    } else {
      status.value = 'OFFLINE';
    }
  } catch (e) {
    status.value = 'OFFLINE';
  }
};

const fetchRecentArticles = async () => {
  try {
    // publicフォルダに配置したアセットは '/' から始まる絶対パスでアクセスします
    const response = await fetch(`/assets/articles.json?t=${new Date().getTime()}`);
    if (response.ok) {
      const allArticles = await response.json();
      recentArticles.value = allArticles.slice(0, 3);
    }
  } catch (error) {
    console.error("記事データの取得に失敗しました:", error);
  }
};

onMounted(() => {
  checkStatus();
  intervalId = setInterval(checkStatus, 5000);
  fetchLatestVideo();
  fetchRecentArticles();
});

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId);
});
</script>

<style scoped>
  /* 先ほどApp.vueにあったstyleをそのままここに貼ります */
</style>
