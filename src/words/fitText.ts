// 文字数に合わせて、枠に収まるいちばん大きい文字サイズを求める（単位は cqw）。
//
// 1文字の幅を「全角 = 1、半角英数 = 0.55」として行ごとの必要な行数を数え、
// 行数 × 行の高さ が枠に収まる最大の文字サイズを探す。
// 縦書きのときは「行の長さ = 枠の高さ」「行を積む方向 = 枠の幅」として同じ計算をする。

export interface FitOptions {
  /** 1行の長さ（cqw）。縦書きなら枠の高さ */
  inline: number
  /** 行を積む方向の長さ（cqw）。縦書きなら枠の幅 */
  block: number
  /** 行の高さ（文字サイズに対する倍率） */
  lineHeight: number
  /** 字間（文字サイズに対する倍率。letter-spacing: 0.05em なら 0.05） */
  tracking: number
  max: number
  min: number
  /** 本文のほかに確保しておく行数（話者名の行など） */
  reserveLines?: number
}

function charWidth(ch: string): number {
  return /[ -~｡-ﾟ]/.test(ch) ? 0.55 : 1
}

function lineUnits(line: string): number {
  let n = 0
  for (const ch of line) n += charWidth(ch)
  return n
}

export function fitFontSize(text: string, opt: FitOptions): number {
  const lines = text.replace(/\r\n?/g, '\n').split('\n').map(lineUnits)
  // 禁則処理（句読点のぶら下げ・追い出し）で1行に入る文字が少し減るので、余裕を見る
  const usableInline = opt.inline * 0.94
  const fits = (size: number, allowWrap: boolean) => {
    const perLine = Math.max(1, Math.floor(usableInline / (size * (1 + opt.tracking))))
    let count = opt.reserveLines ?? 0
    for (const units of lines) {
      const needed = Math.max(1, Math.ceil(units / perLine))
      if (!allowWrap && needed > 1) return false
      count += needed
    }
    return count * size * opt.lineHeight <= opt.block
  }
  const largest = (allowWrap: boolean) => {
    for (let size = opt.max; size >= opt.min; size = Math.round((size - 0.05) * 100) / 100) {
      if (fits(size, allowWrap)) return size
    }
    return 0
  }
  const wrapped = largest(true) || opt.min
  // 自分で入れた改行どおりに1行ずつ収まる大きさが、あまり小さくならないならそちらを選ぶ
  // （「つ。」だけが次の行に送られる、のような見た目を避ける）
  const unwrapped = largest(false)
  return unwrapped >= wrapped * 0.8 ? unwrapped : wrapped
}

/** 文字列から決まった数を作る（ページ番号など、毎回同じ値にしたいもの用） */
export function stableNumber(seed: string, min: number, max: number): number {
  let h = 2166136261
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return min + (Math.abs(h) % (max - min + 1))
}
