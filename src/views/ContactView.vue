<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isFormEnabled = ref(false)

onMounted(() => {
  // グローバル関数としてreCAPTCHAのコールバックを定義
  window.enableFormLink = () => {
    isFormEnabled.value = true
  }

  // reCAPTCHAのスクリプトを動的に読み込む
  if (!document.getElementById('recaptcha-script')) {
    const script = document.createElement('script')
    script.id = 'recaptcha-script'
    script.src = 'https://www.google.com/recaptcha/api.js'
    script.async = true
    script.defer = true
    document.head.appendChild(script)
  }
})

onUnmounted(() => {
  // 画面移動時に不要になったコールバックを削除
  delete window.enableFormLink
})
</script>

<template>
  <div class="bg-[url('/assets/images/erika-hero.jpg')] bg-fixed bg-cover bg-center min-h-screen pt-24 pb-12">
    <div class="container mx-auto px-4 max-w-4xl">
      <div class="p-8 md:p-12 rounded-2xl bg-black/40 backdrop-blur-md border border-white/10">
        <h1 class="text-4xl font-black text-white mb-8">お問い合わせ</h1>

        <div class="text-zinc-300 leading-relaxed mb-8">
          <p class="text-lg mb-6">
            当サイト「erikakataru.com」やプロジェクトに関するご質問、ご意見などがございましたら、下記の専用フォームよりお気軽にお問い合わせください。
          </p>

          <div class="p-6 rounded-xl bg-black border border-zinc-800">
            <h3 class="text-lg font-bold text-white mb-3">【注意事項】</h3>
            <ul class="list-disc list-inside space-y-2 text-sm text-zinc-400">
              <li>お問い合わせの内容によっては、ご返信までにお時間をいただく場合や、お答えできない場合がございます。</li>
              <li>ご入力いただいた個人情報は、お問い合わせに対する回答や必要なご連絡のためにのみ利用し、プライバシーポリシーに則り適切に管理いたします。</li>
              <li>営業・セールスなどのご案内については、返信を控えさせていただく場合がございます。あらかじめご了承ください。</li>
            </ul>
          </div>
        </div>

        <div class="text-center my-10 min-h-[150px]">
          <div class="inline-block mb-4">
            <!-- reCAPTCHAウィジェット -->
            <div class="g-recaptcha" data-sitekey="6LegrJMsAAAAAJ5ALtqSJd7AINVSqap87BZNrbZp" data-callback="enableFormLink"></div>
          </div>

          <div v-if="isFormEnabled" class="mt-4 transition-all duration-300">
            <a href="https://docs.google.com/forms/d/e/1FAIpQLScjbg11HZ7jRnpuJjkrZ-CzgOslB48Bvec-E7lJj3PJ8xwsIg/viewform"
               target="_blank" rel="noopener noreferrer"
               class="inline-block px-8 py-3 bg-[#2ecc71] text-zinc-900 font-bold rounded-full transition-transform hover:scale-105">
              Googleフォームを開く
            </a>
          </div>
        </div>

        <p class="text-center text-sm text-zinc-500 mb-8">
          ※クリックすると、外部サイト（Google Forms）が新しいタブで開きます。
        </p>

      </div>
    </div>
  </div>
</template>
