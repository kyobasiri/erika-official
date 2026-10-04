<script setup lang="ts">
import StaticPageLayout from '../components/StaticPageLayout.vue'

const chapters = [
  {
    number: '01',
    title: 'the pillowsへのリスペクト',
    paragraphs: [
      '現在、このプロジェクトの核となっているのは、the pillowsの楽曲群です。彼らの鳴らすオルタナティヴ・ロックの衝動、孤独に寄り添う歌詞の世界観。それらをただ消費するだけでなく、自分なりの視点で再解釈し、視覚化・具現化したい。',
      'そのための表現インターフェースとして生まれたのが、AIキャラクター「エリカ」です。',
    ],
  },
  {
    number: '02',
    title: '依代としての「エリカ」',
    paragraphs: [
      'エリカは、私が愛する作品たちへの「ファンレター」であり、リスペクトの象徴です。',
      '画像生成AIやComfyUI、楽曲制作環境を駆使し、音楽から受け取った感動をエリカの表情や色彩に変換していく。それは、一人のファンによる「推し活」の形でもあります。',
    ],
  },
  {
    number: '03',
    title: '技術と情熱の融合',
    paragraphs: [
      'SEとしてシステム構築に携わる一方で、この表現のためにAMD Ryzen 9 9950XとRTX 5090を搭載した制作環境を整えました。',
      '複雑なワークフローや音響解析も、原典への愛をより深く表現するための手段です。同時に、このプロジェクトは、進化するAIを学び、実際の作品づくりに取り入れていく実験の場でもあります。',
    ],
  },
  {
    number: '04',
    title: '終わらない航海',
    paragraphs: [
      '今はthe pillowsの世界を旅していますが、この航海はこれからも続きます。大好きな漫画の1コマ、忘れられないゲームの1シーン。それらをエリカというレンズを通すことで、新しい光を当てていく。',
      '「好き」という感情を、テクノロジーで増幅し、世界に発信する。それが「エリカ・プロジェクト」の本質です。',
    ],
  },
]
</script>

<template>
  <StaticPageLayout
    eyebrow="CONCEPT"
    title="プロジェクトの想い"
    description="音楽や物語から受け取った感動を、自分なりの表現へ。"
    image="/assets/images/erika-hero.jpg"
  >
    <section class="concept-intro">
      <div class="intro-copy">
        <p class="eyebrow">WHY WE CREATE</p>
        <h2>
          受け取った感動を、<br />
          AIの翼で返したい。
        </h2>
        <p class="body-text">
          このプロジェクトは、私がこれまでの人生で救われ、
          心を揺さぶられてきた音楽や漫画、ゲームといった
          素晴らしいコンテンツへの「恩返し」から始まりました。
        </p>
      </div>

      <figure class="intro-image">
        <img
          src="/assets/images/erika-hero.jpg"
          alt="プロジェクトの表現を担うAIキャラクター、エリカ"
          decoding="async"
        />
        <figcaption>ERIKA — ART, MUSIC & TECHNOLOGY</figcaption>
      </figure>
    </section>

    <div class="chapters">
      <section
        v-for="chapter in chapters"
        :key="chapter.number"
        class="chapter"
      >
        <span class="chapter-number">{{ chapter.number }}</span>

        <div>
          <h2 class="section-title">{{ chapter.title }}</h2>
          <p
            v-for="paragraph in chapter.paragraphs"
            :key="paragraph"
            class="body-text"
          >
            {{ paragraph }}
          </p>
        </div>
      </section>
    </div>

    <nav class="related-links" aria-label="作品と制作環境">
      <router-link to="/gallery">作品を見る →</router-link>
      <router-link to="/spec">制作PCを見る →</router-link>
      <router-link to="/gear">音楽機材を見る →</router-link>
    </nav>
  </StaticPageLayout>
</template>

<style scoped>
.concept-intro {
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(0, 0.8fr);
  align-items: center;
  gap: 56px;
  margin-bottom: 64px;
}

.intro-copy h2 {
  margin: 0 0 26px;
  font-size: clamp(26px, 3.4vw, 38px);
  font-weight: 800;
  line-height: 1.65;
}

.intro-image {
  margin: 0;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
}

.intro-image img {
  display: block;
  width: 100%;
  height: 360px;
  object-fit: contain;
}

.intro-image figcaption {
  padding: 12px 16px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 9px;
  letter-spacing: 0.13em;
}

.chapters {
  max-width: 880px;
  margin-inline: auto;
}

.chapter {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 24px;
  padding-block: 34px;
  border-top: 1px solid var(--line);
}

.chapter-number {
  color: var(--accent);
  font-size: 30px;
  font-weight: 800;
  line-height: 1.4;
}

@media (max-width: 767px) {
  .concept-intro {
    grid-template-columns: 1fr;
    gap: 28px;
    margin-bottom: 36px;
  }

  .intro-image img {
    height: auto;
    max-height: 400px;
  }

  .chapter {
    grid-template-columns: 36px minmax(0, 1fr);
    gap: 14px;
    padding-block: 28px;
  }

  .chapter-number {
    font-size: 23px;
  }
}
</style>