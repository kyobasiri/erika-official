<script setup lang="ts">
</script>

<template>
  <div class="bg-[url('/assets/images/spec.jpg')] bg-fixed bg-cover bg-center min-h-screen pt-24 pb-12">
    <div class="container mx-auto px-4 max-w-6xl">
      <h1 class="text-4xl md:text-5xl font-black text-white text-center mb-12 drop-shadow-[0_4px_10px_rgba(0,0,0,0.5)]">HARDWARE SPEC</h1>

      <div class="p-8 rounded-2xl bg-black/60 backdrop-blur-md border border-white/10 mb-12">
        <h2 class="text-xl font-bold text-erika mb-4">SE's Build Note</h2>
        <p class="text-zinc-300 leading-relaxed">
          Erika Projectの心臓部。AI生成のさらなる高速化と安定性を求め、構成を再考しました。<br>
          特にメモリ周りは当初の予定から<strong class="text-white">「128GB（64GB×2）」へと買い直し、フル増設</strong>。
          RTX 5090の圧倒的なVRAMと合わせ、ローカルLLMや大規模なComfyUIワークフローを余裕をもって回せる環境を構築しています。
        </p>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div class="p-6 rounded-2xl bg-black/60 backdrop-blur-md border border-emerald-500/30 h-full">
          <span class="inline-block px-3 py-1 text-xs font-bold text-emerald-900 bg-emerald-400 rounded-full mb-3">GPU (Graphics Card)</span>
          <h3 class="text-lg font-bold text-white mb-2">Palit GeForce RTX 5090 GameRock 32GB</h3>
          <p class="text-sm text-zinc-400 mb-4">驚異のVRAM 32GBを搭載。エリカの高解像度画像や動画生成を極限まで高速化する、本プロジェクト最大にして最強のコア・エンジン。</p>
        </div>
        <div class="p-6 rounded-2xl bg-black/60 backdrop-blur-md border border-rose-500/30 h-full">
          <span class="inline-block px-3 py-1 text-xs font-bold text-rose-900 bg-rose-400 rounded-full mb-3">CPU</span>
          <h3 class="text-lg font-bold text-white mb-2">AMD Ryzen 9 9950X</h3>
          <p class="text-sm text-zinc-400 mb-4">圧倒的なマルチスレッド性能で、AI画像生成の裏側から楽曲制作、動画エンコードまで、あらゆるクリエイティブタスクを支えるメインブレイン。</p>
        </div>
        <div class="p-6 rounded-2xl bg-black/60 backdrop-blur-md border border-white/10 h-full">
          <span class="inline-block px-3 py-1 text-xs font-bold text-zinc-300 bg-zinc-800 rounded-full mb-3">Motherboard</span>
          <h3 class="text-lg font-bold text-white mb-2">MSI PRO X870-P WIFI</h3>
          <p class="text-sm text-zinc-400 mb-4">最新世代のRyzenとRTX 5090のポテンシャルを最大限に引き出し、長時間の過酷な負荷にも耐えうる堅牢なマザーボード。</p>
        </div>
        <div class="p-6 rounded-2xl bg-black/60 backdrop-blur-md border border-white/10 h-full">
          <span class="inline-block px-3 py-1 text-xs font-bold text-zinc-300 bg-zinc-800 rounded-full mb-3">Memory (RAM)</span>
          <h3 class="text-lg font-bold text-white mb-2">Crucial DDR5-6000 64GB (CP2K32G60C40U5W)</h3>
          <p class="text-sm text-zinc-400 mb-4">高速なDDR5メモリを大容量64GB（32GB×2）搭載。巨大な音源ライブラリやAIモデルの読み込みをボトルネックなく処理する。</p>
        </div>
        <div class="p-6 rounded-2xl bg-black/60 backdrop-blur-md border border-white/10 h-full">
          <span class="inline-block px-3 py-1 text-xs font-bold text-zinc-300 bg-zinc-800 rounded-full mb-3">CPU Cooler</span>
          <h3 class="text-lg font-bold text-white mb-2">Noctua NH-D15-CH-BK</h3>
          <p class="text-sm text-zinc-400 mb-4">空冷最強の呼び声高いNoctua製ハイエンドクーラーの漆黒モデル。長時間のAI生成でもCPUを確実に冷却し、静音性も両立。</p>
        </div>
        <div class="p-6 rounded-2xl bg-black/60 backdrop-blur-md border border-white/10 h-full">
          <span class="inline-block px-3 py-1 text-xs font-bold text-zinc-300 bg-zinc-800 rounded-full mb-3">Storage (SSD)</span>
          <h3 class="text-lg font-bold text-white mb-2">ADATA LEGEND 860 2TB</h3>
          <p class="text-sm text-zinc-400 mb-4">高速なデータアクセスを可能にするGen4 M.2 SSD。膨大な画像データやプロジェクトファイルの保存先として活躍。</p>
        </div>
        <div class="p-6 rounded-2xl bg-black/60 backdrop-blur-md border border-white/10 h-full">
          <span class="inline-block px-3 py-1 text-xs font-bold text-zinc-300 bg-zinc-800 rounded-full mb-3">Power Supply</span>
          <h3 class="text-lg font-bold text-white mb-2">MSI MPG A1250GS (1250W)</h3>
          <p class="text-sm text-zinc-400 mb-4">RTX 5090というモンスターGPUに安定した電力を供給する、1250Wの大容量・高耐久なATX3.1対応電源ユニット。</p>
        </div>
        <div class="p-6 rounded-2xl bg-black/60 backdrop-blur-md border border-white/10 h-full">
          <span class="inline-block px-3 py-1 text-xs font-bold text-zinc-800 bg-zinc-300 rounded-full mb-3">PC Case</span>
          <h3 class="text-lg font-bold text-white mb-2">NZXT H7Flow (White)</h3>
          <p class="text-sm text-zinc-400 mb-4">優れたエアフローでハイエンドパーツの熱を効率よく逃がす、美しくミニマルなデザインのPCケース。</p>
        </div>
      </div>


    </div>
  </div>
</template>
