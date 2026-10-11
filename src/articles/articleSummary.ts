// トップページ用：記事の Markdown から「表紙・画像・書き出し」だけを軽く取り出す。
// 記事ページの parseArticle.ts は Markdown 変換ライブラリを使うので、トップでは読み込まない。

export interface ArticleSummary {
    /** 記事内の画像ファイル名（登場順） */
    images: string[]
    /** 表紙（0.webp があればそれ、なければ最初の画像） */
    cover: string
    /** 本文の書き出し（数行をつないだもの） */
    excerpt: string
}

const IMAGE = /\[\[([a-zA-Z0-9_.-]+\.(?:jpe?g|png|webp|gif))\]\]/gi
const SKIP_LINE = /^\s*(#|\[\[|https?:\/\/|Listening\s*[:：]|「)/i

export function summarizeArticle(source: string, maxLines = 3): ArticleSummary {
    const text = source.replace(/\r/g, '')
    const images = Array.from(text.matchAll(IMAGE), m => m[1]!)
    const cover = images.includes('0.webp') ? '0.webp' : (images[0] ?? '')

    const lines: string[] = []
    for (const raw of text.split('\n')) {
        const line = raw.trim()
        if (!line || SKIP_LINE.test(line)) {
            if (lines.length && /^\s*(\[\[|https?:\/\/)/.test(line)) break // 最初の画像・リンクまでを書き出しとする
            continue
        }
        lines.push(line)
        if (lines.length >= maxLines) break
    }
    return { images, cover, excerpt: lines.join(' ') }
}

/** 記事ID（20261009 など）→ 2026.10.09 */
export function articleDateLabel(id: string) {
    const m = id.match(/^(\d{4})(\d{2})(\d{2})/)
    return m ? { label: `${m[1]}.${m[2]}.${m[3]}`, iso: `${m[1]}-${m[2]}-${m[3]}` } : null
}

/** 「エモーショナルエリカ | エリカ ギャラリー#230」→ 作品名・シリーズ・番号 */
export function splitArticleTitle(title: string) {
    const [main = title, series = ''] = title.split(/\s*[|｜]\s*/)
    const number = (series.match(/#\s*(\d+)/) || [])[1] ?? ''
    return { main, series, number }
}