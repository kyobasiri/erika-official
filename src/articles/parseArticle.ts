import { marked } from 'marked'

// 記事の Markdown を、見せ方ごとの「ブロック」に分ける。
// 書き方はこれまでどおり（[[1.webp]]、URL を1行で書く、Listening: など）で、変換はここで行う。

export interface ArticleImage {
    file: string
    src: string
    alt: string
    /** 記事内の全画像の中での順番（全画面表示で使う） */
    index: number
}

export type ArticleBlock =
    | { type: 'markdown'; html: string }
    | { type: 'gallery'; images: ArticleImage[] }
    | { type: 'image'; image: ArticleImage }
    | { type: 'x'; url: string }
    | { type: 'youtube'; id: string; vertical: boolean }
    | { type: 'music'; id: string; artist: string; title: string }
    | { type: 'channel'; url: string }
    | { type: 'quote'; text: string }

export interface ParsedArticle {
    title: string
    /** 「|」より前（作品名） */
    mainTitle: string
    /** 「|」より後（シリーズ名） */
    series: string
    /** シリーズの通し番号（#230 など） */
    seriesNumber: string
    blocks: ArticleBlock[]
    images: ArticleImage[]
    tags: string[]
}

const IMAGE_LINE = /^\s*\[\[([a-zA-Z0-9_.-]+\.(?:jpe?g|png|webp|gif))\]\]\s*$/i
const X_LINE = /^\s*(https?:\/\/(?:x\.com|twitter\.com)\/[a-zA-Z0-9_]+\/status\/\d+)\S*\s*$/i
const SHORTS_LINE = /^\s*https?:\/\/(?:www\.)?youtube\.com\/shorts\/([a-zA-Z0-9_-]{6,})\S*\s*$/i
const VIDEO_LINE = /^\s*https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{6,})\S*\s*$/i
const CHANNEL_LINE = /^\s*(https?:\/\/(?:www\.)?youtube\.com\/(?:channel\/|@|c\/)[^\s]+)\s*$/i
const LISTENING_LINE = /^\s*(?:Listening|Now\s*Listening|BGM)\s*[:：]\s*(.+?)\s*$/i
const QUOTE_LINE = /^\s*「(.+)」\s*$/
const HASHTAG_LINE = /^\s*(#[^\s#]+\s*)+$/

// 「the pillows Robotman」→ アーティストと曲名に分ける
const KNOWN_ARTISTS = ['the pillows', 'The Pillows', 'THE PILLOWS']
function splitMusicLabel(label: string) {
    const artist = KNOWN_ARTISTS.find(a => label.startsWith(a + ' '))
    if (artist) return { artist: 'the pillows', title: label.slice(artist.length).trim() }
    const dash = label.split(/\s+[-–—\/]\s+/)
    if (dash.length === 2) return { artist: dash[0]!.trim(), title: dash[1]!.trim() }
    return { artist: '', title: label }
}

export function parseArticle(
    source: string,
    options: { imageBase: string; altFor?: (file: string) => string | undefined }
): ParsedArticle {
    const lines = source.replace(/\r/g, '').split('\n')

    // タイトル（最初の # 見出し）
    let title = ''
    const titleIndex = lines.findIndex(l => /^#\s+/.test(l))
    if (titleIndex >= 0) {
        title = lines[titleIndex]!.replace(/^#\s+/, '').trim()
        lines.splice(titleIndex, 1)
    }
    const [mainTitle = title, series = ''] = title.split(/\s*[|｜]\s*/)
    const seriesNumber = (series.match(/#\s*(\d+)/) || [])[1] ?? ''

    // 末尾のハッシュタグ行
    const tags: string[] = []
    while (lines.length) {
        const last = lines[lines.length - 1]!
        if (!last.trim()) { lines.pop(); continue }
        if (HASHTAG_LINE.test(last)) {
            tags.unshift(...last.trim().split(/\s+/).map(t => t.replace(/^#/, '')).filter(Boolean))
            lines.pop()
            continue
        }
        break
    }

    const blocks: ArticleBlock[] = []
    const images: ArticleImage[] = []
    let textBuffer: string[] = []
    let imageGroup: ArticleImage[] = []

    const flushText = () => {
        const text = textBuffer.join('\n').trim()
        textBuffer = []
        if (text) blocks.push({ type: 'markdown', html: marked.parse(text, { breaks: true, gfm: true, async: false }) as string })
    }
    const flushImages = () => {
        if (imageGroup.length === 1) blocks.push({ type: 'image', image: imageGroup[0]! })
        else if (imageGroup.length > 1) blocks.push({ type: 'gallery', images: imageGroup })
        imageGroup = []
    }
    const pushSpecial = (block: ArticleBlock) => {
        flushImages()
        flushText()
        blocks.push(block)
    }

    for (const line of lines) {
        const image = line.match(IMAGE_LINE)
        if (image) {
            flushText()
            const file = image[1]!
            const item: ArticleImage = {
                file,
                src: `${options.imageBase}/${file}`,
                alt: options.altFor?.(file) || 'エリカのイラスト',
                index: images.length
            }
            images.push(item)
            imageGroup.push(item)
            continue
        }
        // 画像の連続の間の空行は、まとまりを切らない
        if (!line.trim() && imageGroup.length) continue
        flushImages()

        const x = line.match(X_LINE)
        if (x) { pushSpecial({ type: 'x', url: x[1]! }); continue }

        const shorts = line.match(SHORTS_LINE)
        if (shorts) { pushSpecial({ type: 'youtube', id: shorts[1]!, vertical: true }); continue }

        const video = line.match(VIDEO_LINE)
        if (video) {
            // 直前の行が「Listening: 曲名」なら、音楽カードにする
            let lastTextIndex = textBuffer.length - 1
            while (lastTextIndex >= 0 && !textBuffer[lastTextIndex]!.trim()) lastTextIndex--
            const listening = lastTextIndex >= 0 ? textBuffer[lastTextIndex]!.match(LISTENING_LINE) : null
            if (listening) {
                textBuffer.splice(lastTextIndex)
                pushSpecial({ type: 'music', id: video[1]!, ...splitMusicLabel(listening[1]!) })
            } else {
                pushSpecial({ type: 'youtube', id: video[1]!, vertical: false })
            }
            continue
        }

        const channel = line.match(CHANNEL_LINE)
        if (channel) { pushSpecial({ type: 'channel', url: channel[1]! }); continue }

        const quote = line.match(QUOTE_LINE)
        if (quote) { pushSpecial({ type: 'quote', text: quote[1]! }); continue }

        textBuffer.push(line)
    }
    flushImages()
    flushText()

    return { title, mainTitle, series, seriesNumber, blocks, images, tags }
}

// ギャラリーの説明文（AIが作ったもの）の後始末。gallery_gen.py の clean_model_text / looks_broken と同じ考え方。
// 使えない説明文なら空文字を返す（呼び出し側で既定の説明に置き換える）。
const BROKEN_WORDS = ['記述してください', '思考', '提供されていない', '添付されていない', 'できません', '申し訳',
    'アップロード', '提案', 'alt属性', 'キャプション', '画像の分析', '以下の']
export function cleanAlt(raw: string | undefined): string {
    let text = (raw ?? '').replace(/<\|?\/?[A-Za-z_][\w-]*\|?>/g, '')
    const attr = text.match(/alt\s*[=:]\s*["']?([^"'>\n`}]+)/)
    if (attr) text = attr[1]!
    text = text.replace(/```html|```|`|\*\*/g, '').replace(/[\r\n]/g, '').trim()
    text = text.replace(/^[^\u3040-\u30ff\u3400-\u9fff\uff10-\uff5a「『（]+/, '')
    text = text.replace(/^.{1,3}。(?=.{8,})/, '').replace(/}+$/, '').trim()
    const asciiLetters = (text.match(/[A-Za-z]/g) ?? []).length
    const broken =
        text.length < 8 || text.length > 90 ||
        BROKEN_WORDS.some(w => text.includes(w)) ||
        /[<>[\]*]|https?:\/\/|\.jp\b|\.com\b/.test(text) ||
        asciiLetters > text.length * 0.3
    return broken ? '' : text
}

// 記事ID（20261009 など）から日付を作る
export function articleDate(id: string) {
    const m = id.match(/^(\d{4})(\d{2})(\d{2})/)
    return m ? { label: `${m[1]}.${m[2]}.${m[3]}`, iso: `${m[1]}-${m[2]}-${m[3]}` } : null
}