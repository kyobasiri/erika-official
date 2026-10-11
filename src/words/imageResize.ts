// アップロード前に、ブラウザの中で画像を縮小して WebP にする。
// （サーバー側で変換しなくてよく、スマホで撮った大きな写真もそのまま選べる）

const MAX_WIDTH = 1200
const MAX_HEIGHT = 1800
const QUALITY = 0.86

export interface ResizedImage {
  blob: Blob
  type: 'image/webp' | 'image/jpeg'
  width: number
  height: number
}

function toBlob(canvas: HTMLCanvasElement, type: string, quality: number) {
  return new Promise<Blob | null>(resolve => canvas.toBlob(resolve, type, quality))
}

export async function resizeImage(file: File): Promise<ResizedImage> {
  if (!file.type.startsWith('image/')) throw new Error('画像ファイルを選んでください。')

  // iPhone の写真の向き（EXIF）も反映して読み込む
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
  const scale = Math.min(1, MAX_WIDTH / bitmap.width, MAX_HEIGHT / bitmap.height)
  const width = Math.round(bitmap.width * scale)
  const height = Math.round(bitmap.height * scale)

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  if (!ctx) throw new Error('画像を処理できませんでした。')
  ctx.imageSmoothingQuality = 'high'
  ctx.drawImage(bitmap, 0, 0, width, height)
  bitmap.close()

  // WebP に変換できないブラウザ（古い Safari など）では JPEG にする
  const webp = await toBlob(canvas, 'image/webp', QUALITY)
  if (webp && webp.type === 'image/webp') return { blob: webp, type: 'image/webp', width, height }

  const jpeg = await toBlob(canvas, 'image/jpeg', 0.9)
  if (!jpeg) throw new Error('画像を変換できませんでした。')
  return { blob: jpeg, type: 'image/jpeg', width, height }
}
