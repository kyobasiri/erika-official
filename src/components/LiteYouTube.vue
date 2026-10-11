<script setup lang="ts">
import { ref } from 'vue'

// YouTube を「押したときだけ」読み込む。最初はサムネイルだけなので、ページが軽くなる。
const props = defineProps<{
  id: string
  title?: string
  /** ショート動画（縦長） */
  vertical?: boolean
}>()

const playing = ref(false)
const thumbFailed = ref(false)
const thumb = `https://i.ytimg.com/vi/${props.id}/${props.vertical ? 'oar2' : 'hqdefault'}.jpg`
const fallbackThumb = `https://i.ytimg.com/vi/${props.id}/hqdefault.jpg`
</script>

<template>
  <div class="lite-yt" :class="{ vertical }">
    <iframe
      v-if="playing"
      :src="`https://www.youtube-nocookie.com/embed/${id}?autoplay=1&playsinline=1&rel=0`"
      :title="title || 'YouTube 動画'"
      allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
      allowfullscreen
    ></iframe>
    <button v-else class="poster" :aria-label="`${title || '動画'}を再生`" @click="playing = true">
      <img :src="thumbFailed ? fallbackThumb : thumb" alt="" loading="lazy" @error="thumbFailed = true">
      <span class="play" aria-hidden="true">
        <svg viewBox="0 0 68 48"><path d="M66.5 7.7a8.6 8.6 0 0 0-6-6C55.2.3 34 .3 34 .3s-21.2 0-26.5 1.4a8.6 8.6 0 0 0-6 6C.1 13 .1 24 .1 24s0 11 1.4 16.3a8.6 8.6 0 0 0 6 6c5.3 1.4 26.5 1.4 26.5 1.4s21.2 0 26.5-1.4a8.6 8.6 0 0 0 6-6C67.9 35 67.9 24 67.9 24s0-11-1.4-16.3z" fill="#ff0033"/><path d="M45 24 27 14v20z" fill="#fff"/></svg>
      </span>
      <span v-if="title" class="caption">{{ title }}</span>
    </button>
  </div>
</template>

<style scoped>
.lite-yt {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 14px;
  overflow: hidden;
  background: #000;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45);
}
.lite-yt.vertical {
  aspect-ratio: 9 / 16;
  max-width: 340px;
  margin-inline: auto;
}
iframe {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.poster {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  cursor: pointer;
}
.poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease, filter 0.4s ease;
  filter: brightness(0.85);
}
.poster:hover img,
.poster:focus-visible img {
  transform: scale(1.03);
  filter: brightness(1);
}
.play {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
}
.play svg {
  width: 68px;
  height: 48px;
  filter: drop-shadow(0 4px 12px rgba(0, 0, 0, 0.5));
}
.caption {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 28px 16px 12px;
  text-align: left;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.75));
}
</style>