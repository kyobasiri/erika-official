// 「好きな言葉」ページのデータ型。
// いまは public/assets/words.json から読むが、将来は管理ページ（D1）から同じ形で返す。

export type WordTemplate = 'bubble' | 'manga' | 'game' | 'lyric' | 'letter'

export type SourceKind = 'manga' | 'anime' | 'game' | 'song' | 'movie' | 'book' | 'other'

export type BubbleShape = 'round' | 'shout' | 'thought' | 'whisper'

export type BubbleTail = 'bottom-left' | 'bottom-right' | 'left' | 'right' | 'none'

export interface BubbleOptions {
  /** 吹き出しの左上の位置（画像に対する %） */
  x: number
  y: number
  /** 横書きのときの幅（%）。縦書きのときは height を使う */
  width?: number
  height?: number
  shape?: BubbleShape
  tail?: BubbleTail
}

export interface WordOptions {
  /** アクセント色（テンプレートごとの差し色） */
  accent?: string
  /** 縦書きにするか */
  vertical?: boolean
  /** 画像のどこを中心に見せるか（object-position の %） */
  focus?: { x: number; y: number }
  /** 吹き出し・漫画テンプレートの吹き出し */
  bubble?: BubbleOptions
  /** 歌詞カードの曲名（未指定なら出典の作品名） */
  songTitle?: string
  /** ゲーム窓の名前欄（未指定なら「エリカ」） */
  speakerName?: string
  /** 言葉の文字の大きさ（1 が標準。0.7〜1.4 くらい） */
  fontScale?: number
}

export interface WordSource {
  title: string
  author?: string
  kind: SourceKind
  /** 巻・話数・収録など */
  detail?: string
  /** 公式ページなど */
  url?: string
}

export interface WordEntry {
  id: string
  /** 改行は \n */
  quote: string
  /** 作中で言った人（キャラクター名など） */
  speaker?: string
  source: WordSource
  image: string
  imageAlt: string
  template: WordTemplate
  options?: WordOptions
  /** エリカのひとこと解説（ページの主役になる文章） */
  comment?: string
  tags?: string[]
  spoiler?: boolean
  publishedAt?: string
}

export const SOURCE_KIND_LABELS: Record<SourceKind, string> = {
  manga: '漫画',
  anime: 'アニメ',
  game: 'ゲーム',
  song: '歌',
  movie: '映画',
  book: '本',
  other: 'その他'
}

export const TEMPLATE_LABELS: Record<WordTemplate, string> = {
  bubble: '吹き出し',
  manga: '漫画のコマ',
  game: 'ゲームの窓',
  lyric: '歌詞カード',
  letter: '便箋'
}

export const sourceLine = (entry: WordEntry) => {
  const { title, author } = entry.source
  return author ? `『${title}』${author}` : `『${title}』`
}
