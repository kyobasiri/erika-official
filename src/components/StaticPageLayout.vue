<script setup lang="ts">
defineProps<{
  eyebrow: string
  title: string
  description?: string
  image?: string
  narrow?: boolean
}>()
</script>

<template>
  <div class="static-page">
    <header class="page-header">
      <img
        v-if="image"
        :src="image"
        alt=""
        class="header-image"
        decoding="async"
      />
      <div class="header-shade"></div>

      <div class="page-width header-content">
        <nav class="breadcrumb" aria-label="パンくず">
          <router-link to="/">ホーム</router-link>
          <span aria-hidden="true">/</span>
          <span aria-current="page">{{ title }}</span>
        </nav>

        <p class="eyebrow">{{ eyebrow }}</p>
        <h1>{{ title }}</h1>
        <p v-if="description" class="page-description">
          {{ description }}
        </p>
      </div>
    </header>

    <main class="page-width page-body" :class="{ narrow }">
      <slot />
    </main>

    <footer class="page-footer">
      <div class="page-width footer-content">
        <router-link to="/" class="brand">ERIKA<span>.</span></router-link>

        <nav aria-label="関連ページ">
          <router-link to="/concept">Concept</router-link>
          <router-link to="/spec">PC環境</router-link>
          <router-link to="/gear">音楽機材</router-link>
          <router-link to="/privacy">Privacy</router-link>
          <router-link to="/contact">Contact</router-link>
        </nav>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.static-page {
  --accent: #f3a43b;
  --text: #f4f4f5;
  --muted: #aaaab4;
  --line: rgba(255, 255, 255, 0.12);
  --surface: #191b20;

  min-height: 100vh;
  background: #101113;
  color: var(--text);
  line-height: 1.8;
}

.static-page :deep(*) {
  box-sizing: border-box;
}

.static-page :deep(a) {
  text-decoration: none;
}

.static-page :deep(a:focus-visible),
.static-page :deep(button:focus-visible) {
  outline: 2px solid var(--accent);
  outline-offset: 5px;
}

.page-width {
  width: min(1100px, calc(100% - 64px));
  margin-inline: auto;
}

.page-header {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--line);
  background: #191b20;
}

.header-image,
.header-shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.header-image {
  object-fit: cover;
  object-position: center 35%;
}

.header-shade {
  background:
    linear-gradient(90deg, rgba(16, 17, 19, 0.96), rgba(16, 17, 19, 0.65)),
    linear-gradient(0deg, #101113, transparent);
}

.header-content {
  position: relative;
  padding-top: 104px;
  padding-bottom: 48px;
}

.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 32px;
  color: #b7b7c0;
  font-size: 12px;
}

.breadcrumb a {
  color: inherit;
}

.breadcrumb a:hover {
  color: var(--accent);
}

.eyebrow,
.static-page :deep(.eyebrow) {
  margin: 0 0 10px;
  color: var(--accent);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.page-header h1 {
  margin: 0;
  font-size: clamp(28px, 4vw, 44px);
  font-weight: 800;
  line-height: 1.4;
}

.page-description {
  max-width: 650px;
  margin: 18px 0 0;
  color: #c0c0c8;
  font-size: 14px;
}

.page-body {
  padding-top: 48px;
  padding-bottom: 72px;
}

.page-body.narrow {
  max-width: 780px;
}

.static-page :deep(.content-section + .content-section) {
  margin-top: 44px;
}

.static-page :deep(.section-title) {
  margin: 0 0 20px;
  font-size: 23px;
  font-weight: 700;
  line-height: 1.5;
}

.static-page :deep(.body-text) {
  margin: 0;
  color: #c9c9d1;
  font-size: 15px;
  line-height: 2;
  overflow-wrap: anywhere;
}

.static-page :deep(.body-text + .body-text) {
  margin-top: 16px;
}

.static-page :deep(.panel) {
  padding: 28px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: var(--surface);
}

.static-page :deep(.text-link) {
  color: var(--accent);
  text-decoration: underline;
  text-underline-offset: 4px;
}

.static-page :deep(.muted) {
  color: var(--muted);
}

.static-page :deep(.button) {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 12px 24px;
  border: 1px solid transparent;
  border-radius: 8px;
  background: var(--accent);
  color: #19130b;
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.static-page :deep(.button:hover) {
  background: #ffb956;
}

.static-page :deep(.button:disabled) {
  background: #34363e;
  color: #a6a6b0;
  cursor: not-allowed;
}

.static-page :deep(.related-links) {
  display: flex;
  flex-wrap: wrap;
  gap: 14px 24px;
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
}

.static-page :deep(.related-links a) {
  color: var(--accent);
  font-size: 14px;
}

.page-footer {
  padding: 28px 0;
  border-top: 1px solid var(--line);
  background: #0c0d0f;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
}

.brand {
  color: #fff;
  font-size: 26px;
  font-weight: 900;
  letter-spacing: -0.05em;
}

.brand span {
  color: var(--accent);
}

.footer-content nav {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 22px;
}

.footer-content nav a {
  color: var(--muted);
  font-size: 12px;
}

.footer-content nav a:hover {
  color: var(--text);
}

@media (max-width: 640px) {
  .page-width {
    width: calc(100% - 36px);
  }

  .header-content {
    padding-top: 90px;
    padding-bottom: 32px;
  }

  .breadcrumb {
    margin-bottom: 24px;
  }

  .page-body {
    padding-top: 32px;
    padding-bottom: 48px;
  }

  .static-page :deep(.panel) {
    padding: 22px 18px;
  }

  .static-page :deep(.section-title) {
    font-size: 21px;
  }

  .footer-content {
    align-items: flex-start;
    flex-direction: column;
    gap: 16px;
  }
}
</style>