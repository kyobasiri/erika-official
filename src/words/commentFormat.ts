import { markdownToSafeHtml } from '../utils/safeContent'

// 「エリカのひとこと」の書き方
//
//   ・改行はそのまま改行になる。空行を入れると段落が分かれる
//   ・「■ 見出し」「□ 見出し」「◆ 見出し」の行は小見出しになる（Markdown の ## / ### も使える）
//   ・Markdown が使える：**太字**、- 箇条書き、1. 番号付き、> 引用、[文字](URL)
//   ・HTML は無害化される（script やイベント属性は消える）

const HEADING_MARK = /^[ \t　]*[■□◆◇●][ \t　]*(.+?)[ \t　]*$/

/** ■ などで始まる行を Markdown の見出しにする。前後に空行も入れて、段落と分ける */
function normalizeComment(text: string): string {
  return text
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map(line => {
      const m = line.match(HEADING_MARK)
      return m ? `\n### ${m[1]}\n` : line
    })
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

/** ひとことを、表示用の安全な HTML にする */
export function commentToHtml(text: string | undefined): string {
  if (!text?.trim()) return ''
  return markdownToSafeHtml(normalizeComment(text), { breaks: true })
}

/** 一覧やトップページの抜粋用に、Markdown の記号を取り除いたプレーンテキストにする */
export function commentToPlainText(text: string | undefined): string {
  if (!text) return ''
  return text
    .replace(/\r\n?/g, '\n')
    .split('\n')
    .map(line => line
      .replace(HEADING_MARK, '$1')
      .replace(/^\s*#{1,6}\s+/, '')
      .replace(/^\s*>\s?/, '')
      .replace(/^\s*(?:[-*+]|\d+\.)\s+/, '・'))
    .join('\n')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/(\*\*|__)(.+?)\1/g, '$2')
    .replace(/(^|[^*])\*(?!\s)([^*\n]+)\*/g, '$1$2')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}
