import type { WordEntry } from './types'

// 管理用 API の呼び出し。認証は Cloudflare Access のクッキーで行われる（同じサイトなので自動で送られる）。

export type WordStatus = 'draft' | 'published'

export interface AdminWord extends WordEntry {
  status: WordStatus
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export class AdminApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response
  try {
    res = await fetch(`/api/admin/words${path}`, { credentials: 'same-origin', ...init })
  } catch {
    throw new AdminApiError('通信できませんでした。電波の状態を確認してください。', 0)
  }
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new AdminApiError(data.error || `エラーが発生しました（${res.status}）`, res.status)
  return data as T
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body)
})

export const adminApi = {
  list: () => request<{ words: AdminWord[]; email: string }>(''),
  create: (word: Partial<AdminWord>) => request<{ word: AdminWord }>('', json('POST', word)),
  update: (id: string, word: Partial<AdminWord>) => request<{ word: AdminWord }>(`/${encodeURIComponent(id)}`, json('PUT', word)),
  remove: (id: string) => request<{ success: true }>(`/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  uploadImage: (id: string, blob: Blob, type: string) =>
    request<{ word: AdminWord }>(`/${encodeURIComponent(id)}/image`, { method: 'POST', headers: { 'Content-Type': type }, body: blob })
}
