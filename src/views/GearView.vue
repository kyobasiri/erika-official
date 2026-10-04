<script setup lang="ts">
import StaticPageLayout from '../components/StaticPageLayout.vue'

const groups = [
  {
    id: 'composition',
    label: 'COMPOSITION',
    title: '作曲と音づくり',
    description: 'アイデアを形にするソフトウェアと、演奏・入力のための道具。',
    items: [
      {
        category: 'DAW / COMPOSITION',
        name: 'Ableton Live Lite / Scaler 3',
        description:
          '楽曲構成とビートメイクを支える制作環境。操作と理論支援を組み合わせ、アイデアを形にします。',
        url: '',
        status: '',
      },
      {
        category: 'VIRTUAL INSTRUMENTS',
        name: 'NI Komplete 15 Select / Electric Storm Deluxe',
        description:
          '動画のサウンドや楽曲制作に使用する音源ライブラリ。表現に合わせて音色を選んでいます。',
        url: 'https://link.amazon/B0iOlSdAK',
        status: '',
      },
      {
        category: 'MIDI CONTROLLER',
        name: 'M-Audio Oxygen Pro Mini',
        description:
          'メロディの打ち込みやDAWの操作に使う、コンパクトなMIDIキーボード。',
        url: 'https://link.amazon/B05u8ciEE',
        status: '',
      },
    ],
  },
  {
    id: 'recording',
    label: 'RECORDING',
    title: '録音を支える機材',
    description: '声や楽器の音を、制作環境へ。',
    items: [
      {
        category: 'AUDIO INTERFACE',
        name: 'SSL2 MkⅡ',
        description:
          'Solid State Logicのオーディオインターフェース。マイクや楽器の録音に使用します。',
        url: 'https://link.amazon/B01I2n5wZ',
        status: '',
      },
      {
        category: 'CONDENSER MICROPHONE',
        name: 'Audio-Technica AT2035',
        description:
          'ボーカルや楽器の収音に使うコンデンサーマイク。音の質感や空気感を取り込むための一本。',
        url: 'https://link.amazon/B0fkzM83p',
        status: '',
      },
    ],
  },
  {
    id: 'guitar',
    label: 'GUITAR & AMP',
    title: 'ギターで広げる表現',
    description:
      '制作環境への統合とサウンド調整を進めている機材。今後の作品での活用を目指しています。',
    items: [
      {
        category: 'GUITAR',
        name: 'Squier / Affinity Telecaster Thinline',
        description:
          'Fホールを持つセミホロウボディのギター。リズムギターへの活用を予定しています。',
        url: 'https://link.amazon/B01pZ4MRW',
        status: '導入・調整中',
      },
      {
        category: 'GUITAR',
        name: 'SCHECTER / AR-06-2H',
        description:
          '2ハムバッカーを搭載したギター。リードパートなど、表現の幅を広げるための一本。',
        url: 'https://link.amazon/B0gWyDvH1',
        status: '導入・調整中',
      },
      {
        category: 'AMP & CAB',
        name: 'BOSS / IR-2',
        description:
          'ギターのアンプサウンドをDAWへつなぐ機材。演奏とPCでの制作環境を結びます。',
        url: 'https://link.amazon/B0dZFHDgr',
        status: '導入・調整中',
      },
    ],
  },
]

// 既存ページのAT2035リンクを維持
groups[1].items[1].url = 'https://link.amazon/B0cxjbKcN'
</script>

<template>
  <StaticPageLayout
    eyebrow="SOUND GEAR"
    title="音をつくる道具"
    description="作曲、録音、ギター。エリカの音楽制作を支える機材たち。"
    image="/assets/images/gear.jpg"
  >
    <nav class="category-nav" aria-label="機材の分類">
      <a v-for="group in groups" :key="group.id" :href="`#${group.id}`">
        {{ group.title }} <span aria-hidden="true">↓</span>
      </a>
    </nav>

    <section
      v-for="group in groups"
      :id="group.id"
      :key="group.id"
      class="gear-section"
      :aria-labelledby="`${group.id}-title`"
    >
      <div class="group-heading">
        <p class="eyebrow">{{ group.label }}</p>
        <h2 :id="`${group.id}-title`" class="section-title">
          {{ group.title }}
        </h2>
        <p class="body-text">{{ group.description }}</p>
      </div>

      <div class="gear-list">
        <article v-for="item in group.items" :key="item.name" class="gear-item">
          <div class="gear-meta">
            <span class="gear-category">{{ item.category }}</span>
            <span v-if="item.status" class="status">{{ item.status }}</span>
          </div>

          <h3>{{ item.name }}</h3>
          <p>{{ item.description }}</p>

          <a
            v-if="item.url"
            :href="item.url"
            target="_blank"
            rel="sponsored noopener noreferrer"
            class="gear-link"
          >
            Amazonで詳細を見る ↗
          </a>
        </article>
      </div>
    </section>

    <p class="affiliate-note">
      ※Erika Projectは、Amazon.co.jpを宣伝しリンクすることによって
      サイトが紹介料を獲得できる手段を提供することを目的に設定された
      アフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。
    </p>

    <nav class="related-links" aria-label="関連ページ">
      <router-link to="/spec">制作PCを見る →</router-link>
      <router-link to="/concept">プロジェクトの想い →</router-link>
    </nav>
  </StaticPageLayout>
</template>

<style scoped>
.category-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 44px;
}

.category-nav a {
  display: inline-flex;
  align-items: center;
  gap: 20px;
  min-height: 44px;
  padding: 9px 18px;
  border: 1px solid var(--line);
  border-radius: 7px;
  color: var(--text);
  font-size: 13px;
}

.category-nav a:hover {
  border-color: var(--accent);
}

.category-nav span {
  color: var(--accent);
}

.gear-section {
  display: grid;
  grid-template-columns: minmax(0, 0.8fr) minmax(0, 1.6fr);
  gap: 48px;
  padding-block: 36px;
  border-top: 1px solid var(--line);
  scroll-margin-top: 90px;
}

.group-heading .body-text {
  font-size: 13px;
}

.gear-list {
  display: grid;
  gap: 16px;
}

.gear-item {
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: var(--surface);
}

.gear-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.gear-category {
  color: var(--accent);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.status {
  padding: 3px 9px;
  border: 1px solid rgba(243, 164, 59, 0.25);
  border-radius: 4px;
  color: #e8bc7e;
  font-size: 10px;
}

.gear-item h3 {
  margin: 0 0 12px;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.6;
}

.gear-item p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.9;
}

.gear-link {
  display: inline-block;
  margin-top: 18px;
  color: var(--accent);
  font-size: 12px;
}

.gear-link:hover {
  text-decoration: underline;
}

.affiliate-note {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.9;
}

@media (max-width: 767px) {
  .category-nav {
    gap: 8px;
    margin-bottom: 28px;
  }

  .category-nav a {
    gap: 10px;
    padding-inline: 12px;
    font-size: 12px;
  }

  .gear-section {
    grid-template-columns: 1fr;
    gap: 22px;
    padding-block: 28px;
  }

  .gear-item {
    padding: 20px;
  }
}
</style>