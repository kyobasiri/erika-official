<script setup lang="ts">
import StaticPageLayout from '../components/StaticPageLayout.vue'

const highlights = [
  {
    label: 'GPU',
    value: 'RTX 5090',
    detail: 'VRAM 32GB',
    description: '画像・動画生成の中心となる演算環境。',
  },
  {
    label: 'CPU',
    value: 'Ryzen 9 9950X',
    detail: 'AMD Ryzen',
    description: '生成処理、音楽制作、動画編集を支える。',
  },
  {
    label: 'MEMORY',
    value: '128GB',
    detail: '64GB × 2',
    description: '大規模なワークフローを扱うための容量。',
  },
]

const parts = [
  {
    category: 'GPU',
    name: 'Palit GeForce RTX 5090 GameRock 32GB',
    note: '高解像度のAI画像・動画生成を担当。',
    url: 'https://link.amazon/B032igmH2',
  },
  {
    category: 'CPU',
    name: 'AMD Ryzen 9 9950X',
    note: '並行作業や動画エンコード、楽曲制作を支える。',
    url: 'https://link.amazon/B0jcPiSpU',
  },
  {
    category: 'マザーボード',
    name: 'MSI PRO X870-P WIFI',
    note: '制作環境の基盤。',
    url: 'https://link.amazon/B0gghjti8',
  },
  {
    category: 'メモリ',
    name: 'Crucial DDR5 / 128GB（64GB × 2）',
    note: 'AIモデルや音源ライブラリの読み込みに使用。',
    // 元コードの型番表記と128GBの構成表記が一致していないため、
    // 型番・購入リンクは実機の確認後に設定してください。
    url: '',
  },
  {
    category: 'CPUクーラー',
    name: 'Noctua NH-D15-CH-BK',
    note: '長時間の制作処理に備えた空冷クーラー。',
    url: 'https://link.amazon/B0fkzM83p',
  },
  {
    category: 'ストレージ',
    name: 'ADATA LEGEND 860 2TB',
    note: 'モデル、画像、制作データの保存先。',
    url: 'https://link.amazon/B02OrdDNW',
  },
  {
    category: '電源',
    name: 'MSI MPG A1250GS / 1250W',
    note: '制作PCの電力供給を担う電源ユニット。',
    url: 'https://link.amazon/B09JoSewO',
  },
  {
    category: 'ケース',
    name: 'NZXT H7 Flow / White',
    note: '冷却と作業性を考慮したPCケース。',
    url: 'https://link.amazon/B0i0G3Eak',
  },
  {
    category: 'OS',
    name: 'Windows 11 Pro',
    note: '制作ツールを動かすメインOS。',
    url: '',
  },
]
</script>

<template>
  <StaticPageLayout
    eyebrow="HARDWARE"
    title="作品を生み出すPC"
    description="画像生成、動画制作、音楽制作。エリカの表現を支える制作環境。"
    image="/assets/images/spec.jpg"
  >
    <section class="highlights" aria-label="主要スペック">
      <div v-for="item in highlights" :key="item.label" class="highlight">
        <p class="eyebrow">{{ item.label }}</p>
        <h2>{{ item.value }}</h2>
        <p class="highlight-detail">{{ item.detail }}</p>
        <p class="highlight-description">{{ item.description }}</p>
      </div>
    </section>

    <section class="content-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">BUILD DETAILS</p>
          <h2 class="section-title">システム構成</h2>
        </div>
        <span class="muted">MAIN WORKSTATION</span>
      </div>

      <div class="parts-list">
        <div v-for="part in parts" :key="part.category" class="part-row">
          <div class="part-category">{{ part.category }}</div>

          <div class="part-content">
            <h3>{{ part.name }}</h3>
            <p>{{ part.note }}</p>
          </div>

          <a
            v-if="part.url"
            :href="part.url"
            target="_blank"
            rel="sponsored noopener noreferrer"
            class="part-link"
          >
            Amazonで詳細 ↗
          </a>
        </div>
      </div>
    </section>

    <section class="content-section panel">
      <p class="eyebrow">BUILD NOTE</p>
      <h2 class="section-title">余裕を持って、試行錯誤できる環境へ。</h2>

      <p class="body-text">
        AI生成の高速化と安定性を求め、制作環境の構成を見直しました。
        特にメモリは当初の構成から買い直し、
        128GB（64GB × 2）へ増強しています。
      </p>

      <p class="body-text">
        RTX 5090のVRAM 32GBと合わせ、ローカルLLMや
        大規模なComfyUIワークフローを扱うための環境を整えました。
        生成結果を見ながら調整を重ねられることを大切にしています。
      </p>
    </section>

    <p class="affiliate-note">
      ※Erika Projectは、Amazon.co.jpを宣伝しリンクすることによって
      サイトが紹介料を獲得できる手段を提供することを目的に設定された
      アフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。
    </p>

    <nav class="related-links" aria-label="関連ページ">
      <router-link to="/gear">音楽制作の機材を見る →</router-link>
      <router-link to="/gallery">この環境で生まれた作品を見る →</router-link>
    </nav>
  </StaticPageLayout>
</template>

<style scoped>
.highlights {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  margin-bottom: 48px;
}

.highlight {
  padding: 26px;
  border: 1px solid var(--line);
  border-top: 2px solid var(--accent);
  border-radius: 10px;
  background: var(--surface);
}

.highlight h2 {
  margin: 12px 0 6px;
  font-size: clamp(23px, 2.7vw, 32px);
  font-weight: 800;
  line-height: 1.3;
}

.highlight-detail {
  margin: 0;
  color: #e5c496;
  font-size: 13px;
}

.highlight-description {
  margin: 18px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.section-heading > span {
  font-size: 10px;
  letter-spacing: 0.12em;
}

.parts-list {
  border-top: 1px solid var(--line);
}

.part-row {
  display: grid;
  grid-template-columns: 140px minmax(0, 1fr) 125px;
  align-items: center;
  gap: 24px;
  padding: 22px 4px;
  border-bottom: 1px solid var(--line);
}

.part-category {
  color: var(--muted);
  font-size: 13px;
}

.part-content h3 {
  margin: 0 0 5px;
  font-size: 15px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.part-content p {
  margin: 0;
  color: var(--muted);
  font-size: 12px;
}

.part-link {
  justify-self: end;
  color: var(--accent);
  font-size: 12px;
}

.part-link:hover {
  text-decoration: underline;
}

.affiliate-note {
  margin: 28px 0 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.9;
}

@media (max-width: 767px) {
  .highlights {
    grid-template-columns: 1fr;
    gap: 14px;
    margin-bottom: 36px;
  }

  .highlight {
    padding: 22px;
  }

  .highlight h2 {
    font-size: 30px;
  }

  .highlight-description {
    margin-top: 12px;
  }

  .section-heading > span {
    display: none;
  }

  .part-row {
    grid-template-columns: 1fr;
    gap: 7px;
    padding-block: 20px;
  }

  .part-link {
    justify-self: start;
    margin-top: 6px;
  }
}
</style>