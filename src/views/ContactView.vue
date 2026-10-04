<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import StaticPageLayout from '../components/StaticPageLayout.vue'

interface CaptchaApi {
  render(
    container: HTMLElement,
    options: {
      sitekey: string
      theme: 'dark'
      callback: (token: string) => void
      'expired-callback': () => void
      'error-callback': () => void
    },
  ): number
  reset(widgetId: number): void
}

type CaptchaWindow = Window & {
  grecaptcha?: CaptchaApi
}

const SITE_KEY = '6LegrJMsAAAAAJ5ALtqSJd7AINVSqap87BZNrbZp'
const FORM_URL =
  'https://docs.google.com/forms/d/e/1FAIpQLScjbg11HZ7jRnpuJjkrZ-CzgOslB48Bvec-E7lJj3PJ8xwsIg/viewform'

const captchaContainer = ref<HTMLDivElement | null>(null)
const isFormEnabled = ref(false)
const captchaLoading = ref(true)
const captchaError = ref('')

let widgetId: number | null = null
let timer: ReturnType<typeof setInterval> | null = null
let disposed = false

function stopTimer() {
  if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
}

function getCaptchaApi() {
  return (window as CaptchaWindow).grecaptcha
}

function renderCaptcha(): boolean {
  if (disposed) return true
  if (widgetId !== null) return true

  const api = getCaptchaApi()

  if (!api || typeof api.render !== 'function' || !captchaContainer.value) {
    return false
  }

  try {
    widgetId = api.render(captchaContainer.value, {
      sitekey: SITE_KEY,
      theme: 'dark',

      callback: () => {
        if (disposed) return
        isFormEnabled.value = true
        captchaError.value = ''
      },

      'expired-callback': () => {
        if (disposed) return
        isFormEnabled.value = false
      },

      'error-callback': () => {
        if (disposed) return
        isFormEnabled.value = false
        captchaError.value =
          '認証に失敗しました。通信状態をご確認のうえ、再認証してください。'
      },
    })

    captchaLoading.value = false
    return true
  } catch {
    return false
  }
}

function startCaptcha() {
  stopTimer()
  captchaLoading.value = true
  captchaError.value = ''
  isFormEnabled.value = false

  const api = getCaptchaApi()

  if (widgetId !== null && api) {
    try {
      api.reset(widgetId)
      captchaLoading.value = false
    } catch {
      captchaLoading.value = false
      captchaError.value = '認証を再開できませんでした。ページを再読み込みしてください。'
    }
    return
  }

  const existingScript = document.querySelector<HTMLScriptElement>(
    'script[src*="google.com/recaptcha/api.js"], script[src*="recaptcha.net/recaptcha/api.js"]',
  )

  if (!existingScript) {
    const script = document.createElement('script')
    script.id = 'recaptcha-script'
    script.src = 'https://www.google.com/recaptcha/api.js?render=explicit'
    script.async = true
    script.defer = true
    document.head.appendChild(script)
  }

  if (renderCaptcha()) return

  const startedAt = Date.now()

  timer = setInterval(() => {
    if (renderCaptcha()) {
      stopTimer()
      return
    }

    if (Date.now() - startedAt > 15000) {
      stopTimer()
      captchaLoading.value = false
      captchaError.value =
        '認証を読み込めませんでした。通信状態をご確認のうえ、ページを再読み込みしてください。'
    }
  }, 150)
}

onMounted(startCaptcha)

onBeforeUnmount(() => {
  disposed = true
  stopTimer()

  if (widgetId !== null) {
    try {
      getCaptchaApi()?.reset(widgetId)
    } catch {
      // 画面離脱時に読み込みが中断された場合
    }
  }
})
</script>

<template>
  <StaticPageLayout
    eyebrow="CONTACT"
    title="お問い合わせ"
    description="サイトやプロジェクトへのご質問、ご意見はこちらから。"
    narrow
  >
    <div class="contact-content">
      <section class="contact-main panel">
        <p class="eyebrow">GET IN TOUCH</p>
        <h2 class="section-title">エリカ・プロジェクトへのご連絡</h2>

        <p class="body-text">
          当サイトやプロジェクトに関するご質問、ご意見などがございましたら、
          専用フォームよりお気軽にお問い合わせください。
        </p>

        <div class="contact-steps">
          <div class="step-label">
            <span class="step-number">1</span>
            <h3>認証を行ってください</h3>
          </div>

          <div class="captcha-area">
            <div ref="captchaContainer"></div>
          </div>

          <div class="captcha-status" aria-live="polite">
            <p v-if="captchaLoading">認証を読み込んでいます…</p>

            <div v-else-if="captchaError" class="captcha-error">
              <p>{{ captchaError }}</p>
              <button
                v-if="widgetId !== null"
                type="button"
                class="retry-button"
                @click="startCaptcha"
              >
                再認証する
              </button>
            </div>

            <p v-else-if="isFormEnabled" class="verified">
              認証が完了しました。フォームを開けます。
            </p>

            <p v-else>上のチェックボックスで認証してください。</p>
          </div>

          <div class="step-label second-step">
            <span class="step-number">2</span>
            <h3>専用フォームを開く</h3>
          </div>

          <a
            v-if="isFormEnabled"
            :href="FORM_URL"
            target="_blank"
            rel="noopener noreferrer"
            class="button form-button"
          >
            お問い合わせフォームを開く ↗
          </a>

          <button
            v-else
            type="button"
            class="button form-button"
            disabled
          >
            認証するとフォームを開けます
          </button>

          <p class="external-note">
            Googleフォームが新しいタブで開きます。
          </p>
        </div>
      </section>

      <section class="contact-notes" aria-labelledby="notes-title">
        <h2 id="notes-title">お問い合わせの前に</h2>

        <ul>
          <li>
            内容によっては、ご返信までにお時間をいただく場合や、
            お答えできない場合がございます。
          </li>
          <li>
            ご入力いただいた個人情報は、お問い合わせへの回答や
            必要なご連絡のためにのみ利用します。
          </li>
          <li>
            営業・セールスなどのご案内については、
            返信を控えさせていただく場合がございます。
          </li>
        </ul>

        <router-link to="/privacy" class="text-link">
          プライバシーポリシーを確認する →
        </router-link>
      </section>
    </div>
  </StaticPageLayout>
</template>

<style scoped>
.contact-content {
  max-width: 660px;
  margin-inline: auto;
}

.contact-main .section-title {
  font-size: 23px;
}

.contact-steps {
  margin-top: 30px;
  padding-top: 26px;
  border-top: 1px solid var(--line);
}

.step-label {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-number {
  display: inline-flex;
  width: 27px;
  height: 27px;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(243, 164, 59, 0.4);
  border-radius: 50%;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
}

.step-label h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.captcha-area {
  max-width: 100%;
  min-height: 78px;
  margin-top: 20px;
  overflow-x: auto;
}

.captcha-status {
  margin-top: 12px;
  color: var(--muted);
  font-size: 12px;
}

.captcha-status p {
  margin: 0;
}

.captcha-status .verified {
  color: #86d6ad;
}

.captcha-error {
  color: #f1b08b;
}

.retry-button {
  margin-top: 10px;
  padding: 6px 0;
  border: 0;
  background: transparent;
  color: var(--accent);
  font: inherit;
  text-decoration: underline;
  cursor: pointer;
}

.second-step {
  margin-top: 30px;
}

.form-button {
  width: 100%;
  margin-top: 18px;
  text-align: center;
}

.external-note {
  margin: 12px 0 0;
  color: var(--muted);
  font-size: 12px;
  text-align: center;
}

.contact-notes {
  padding: 28px 4px 0;
}

.contact-notes h2 {
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 600;
}

.contact-notes ul {
  display: grid;
  gap: 12px;
  margin: 0 0 20px;
  padding-left: 20px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.9;
}

.contact-notes .text-link {
  font-size: 13px;
}
</style>