<script setup lang="ts">
import StaticPageLayout from '../components/StaticPageLayout.vue'

const contents = [
  { id: 'personal-information', title: '個人情報の利用目的' },
  { id: 'advertising', title: '広告の配信について' },
  { id: 'analytics', title: 'アクセス解析ツールについて' },
  { id: 'disclaimer', title: '免責事項' },
  { id: 'copyright', title: '著作権について' },
]
</script>

<template>
  <StaticPageLayout
    eyebrow="PRIVACY POLICY"
    title="プライバシーポリシー"
    description="当サイトにおける情報の取り扱いについて。"
    narrow
  >
    <nav class="contents panel" aria-label="目次">
      <p class="eyebrow">CONTENTS</p>
      <ol>
        <li v-for="item in contents" :key="item.id">
          <a :href="`#${item.id}`">{{ item.title }}</a>
        </li>
      </ol>
    </nav>

    <!-- 本文は既存ページの記載を維持 -->
    <div class="policy-body">
      <section id="personal-information">
        <span class="section-number">01</span>
        <h2 class="section-title">個人情報の利用目的</h2>
        <p class="body-text">
          当サイトでは、お問い合わせの際などに名前やメールアドレス等の
          個人情報をご入力いただく場合がございます。
        </p>
        <p class="body-text">
          取得した個人情報は、お問い合わせに対する回答や必要な情報を
          電子メールなどでご連絡する場合に利用させていただくものであり、
          これらの目的以外では利用いたしません。
        </p>
      </section>

      <section id="advertising">
        <span class="section-number">02</span>
        <h2 class="section-title">広告の配信について</h2>
        <p class="body-text">
          当サイトは、第三者配信の広告サービス
          「Google AdSense（グーグルアドセンス）」を利用しています
          （※審査通過後に有効化されます）。
        </p>
        <p class="body-text">
          広告配信事業者は、ユーザーの興味に応じた広告を表示するために
          Cookie（クッキー）を使用することがあります。
        </p>
        <p class="body-text">
          Cookieを無効にする設定およびGoogleアドセンスに関する詳細は、
          <a
            href="https://policies.google.com/technologies/ads?gl=jp"
            target="_blank"
            rel="noopener noreferrer"
            class="text-link"
          >広告 – ポリシーと規約 – Google</a>
          をご確認ください。
        </p>
      </section>

      <section id="analytics">
        <span class="section-number">03</span>
        <h2 class="section-title">アクセス解析ツールについて</h2>
        <p class="body-text">
          当サイトでは、Googleによるアクセス解析ツール
          「Googleアナリティクス」を利用しています。
        </p>
        <p class="body-text">
          このGoogleアナリティクスはトラフィックデータの収集のために
          Cookieを使用しています。トラフィックデータは匿名で収集されており、
          個人を特定するものではありません。
        </p>
      </section>

      <section id="disclaimer">
        <span class="section-number">04</span>
        <h2 class="section-title">免責事項</h2>
        <p class="body-text">
          当サイトからのリンクやバナーなどで移動したサイトで提供される
          情報、サービス等について一切の責任を負いません。
        </p>
        <p class="body-text">
          また当サイトのコンテンツ・情報について、できる限り正確な情報を
          提供するように努めておりますが、正確性や安全性を保証するものではありません。
          情報が古くなっていることもございます。
        </p>
        <p class="body-text">
          当サイトに掲載された内容によって生じた損害等の一切の責任を
          負いかねますのでご了承ください。
        </p>
      </section>

      <section id="copyright">
        <span class="section-number">05</span>
        <h2 class="section-title">著作権について</h2>
        <p class="body-text">
          当サイトで掲載している文章や画像などにつきましては、
          無断転載することを禁止します。当サイト内のAI生成画像
          （エリカのキャラクター画像等）および文章の著作権・肖像権等は
          当サイト管理人に帰属します。
        </p>
      </section>
    </div>

    <p class="policy-date">策定日：2026年3月23日</p>

    <nav class="related-links" aria-label="関連ページ">
      <router-link to="/contact">お問い合わせ →</router-link>
      <router-link to="/">ホームへ戻る →</router-link>
    </nav>
  </StaticPageLayout>
</template>

<style scoped>
.contents {
  margin-bottom: 40px;
}

.contents ol {
  display: grid;
  gap: 9px;
  margin: 16px 0 0;
  padding-left: 22px;
  color: var(--muted);
  font-size: 14px;
}

.contents a {
  color: #d7d7df;
}

.contents a:hover {
  color: var(--accent);
}

.policy-body section {
  padding-block: 30px;
  border-top: 1px solid var(--line);
  scroll-margin-top: 90px;
}

.section-number {
  display: block;
  margin-bottom: 10px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.1em;
}

.policy-body .section-title {
  font-size: 21px;
}

.policy-date {
  margin: 24px 0 0;
  color: var(--muted);
  font-size: 12px;
}
</style>