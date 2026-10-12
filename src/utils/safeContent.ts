import DOMPurify from 'dompurify'
import { marked } from 'marked'

// ==========================================
// Markdown → HTML の無害化と、静的ファイルの取得まわりの共通処理
// ==========================================

// 埋め込みを許可する iframe は YouTube の埋め込みだけ
const ALLOWED_IFRAME_SRC = /^https:\/\/(?:www\.)?youtube(?:-nocookie)?\.com\/embed\/[A-Za-z0-9_-]+(?:\?[^"'<>\s]*)?$/

DOMPurify.addHook('afterSanitizeAttributes', (node) => {
  // 許可していない iframe は src を消して空にする（中身は読み込まれない）
  if (node.tagName === 'IFRAME') {
    const src = node.getAttribute('src') || ''
    if (!ALLOWED_IFRAME_SRC.test(src)) node.removeAttribute('src')
  }
  // 別タブで開くリンクは、開いた先から元のページを操作されないようにする
  if (node.tagName === 'A' && node.getAttribute('target') === '_blank') {
    node.setAttribute('rel', 'noopener noreferrer')
  }
})

/** HTML から script・イベント属性（onerror 等）・javascript: URL などを取り除く */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ADD_TAGS: ['iframe'],
    ADD_ATTR: ['allowfullscreen', 'target'],
  })
}

/** Markdown を HTML にして、無害化したものを返す */
export function markdownToSafeHtml(text: string, options: { breaks?: boolean } = {}): string {
  const html = marked.parse(text, { gfm: true, breaks: options.breaks ?? false, async: false }) as string
  return sanitizeHtml(html)
}

/**
 * 日報・観測日誌用：X と YouTube の URL だけの行を埋め込みに変えてから、Markdown を安全な HTML にする。
 * （埋め込み用の HTML もまとめて無害化を通る。YouTube の iframe だけは残す）
 */
export function reportMarkdownToSafeHtml(text: string): string {
  const xLinkRegex = /^[ \t]*https?:\/\/(?:x\.com|twitter\.com)\/([a-zA-Z0-9_]+\/status\/\d+)[^\s<]*[ \t]*$/gm
  text = text.replace(xLinkRegex, '\n\n<div class="flex justify-center my-6"><blockquote class="twitter-tweet" data-align="center"><a href="https://twitter.com/$1"></a></blockquote></div>\n\n')

  const ytNormalRegex = /^[ \t]*https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]+)[^\s<]*[ \t]*$/gm
  text = text.replace(ytNormalRegex, '\n\n<div class="relative pb-[56.25%] h-0 overflow-hidden w-full my-6 rounded-xl shadow-lg"><iframe src="https://www.youtube.com/embed/$1" class="absolute top-0 left-0 w-full h-full border-none" allowfullscreen></iframe></div>\n\n')

  return markdownToSafeHtml(text)
}

// ==========================================
// 静的ファイルの取得
// Cloudflare Pages は、存在しないファイルを要求されると index.html を 200 で返す（SPA の動き）。
// そのため「200 が返った = ファイルがある」とは言えないので、中身の種類で判定する。
// ==========================================

function isHtmlResponse(res: Response): boolean {
  return (res.headers.get('Content-Type') || '').toLowerCase().includes('text/html')
}

function looksLikeHtml(text: string): boolean {
  return /^\s*<(?:!doctype|html)/i.test(text)
}

/** テキストファイルを取得する。無い場合（404 や index.html が返った場合）は null */
export async function fetchStaticText(url: string, init?: RequestInit): Promise<string | null> {
  try {
    const res = await fetch(url, init)
    if (!res.ok || isHtmlResponse(res)) return null
    const text = await res.text()
    return looksLikeHtml(text) ? null : text
  } catch {
    return null
  }
}

/** 音声などのファイルが本当にあるかを確認する（HEAD で、Content-Type が期待どおりか見る） */
export async function staticFileExists(url: string, expectedTypePrefix: string): Promise<boolean> {
  try {
    const res = await fetch(url, { method: 'HEAD' })
    if (!res.ok) return false
    const type = (res.headers.get('Content-Type') || '').toLowerCase()
    return type.startsWith(expectedTypePrefix)
  } catch {
    return false
  }
}

/** YouTube の動画 ID（11文字）として正しいか */
export function isYoutubeId(value: string): boolean {
  return /^[A-Za-z0-9_-]{11}$/.test(value)
}

/** 日報のファイル名（拡張子なし）として正しいか。例: 20261011-task-report / 20260923-report */
export function isReportId(value: string): boolean {
  return /^\d{8}(?:-[a-z]+)*-report$/.test(value)
}
