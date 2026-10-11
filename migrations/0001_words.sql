-- エリカの好きな言葉（/words）のテーブル
-- 適用: npx wrangler d1 migrations apply erika-words --remote

CREATE TABLE IF NOT EXISTS words (
  id            TEXT PRIMARY KEY,
  status        TEXT    NOT NULL DEFAULT 'draft',   -- draft（下書き） / published（公開）
  quote         TEXT    NOT NULL,                   -- 言葉。改行は \n
  speaker       TEXT,                               -- 作中で言った人
  source_title  TEXT    NOT NULL DEFAULT '',
  source_author TEXT,
  source_kind   TEXT    NOT NULL DEFAULT 'other',   -- manga / anime / game / song / movie / book / other
  source_detail TEXT,                               -- 巻・話数・収録など
  source_url    TEXT,                               -- 公式ページなど
  image_url     TEXT,                               -- 表示に使う画像のURL
  image_key     TEXT,                               -- R2 に保存した画像のキー（削除用）
  image_alt     TEXT    NOT NULL DEFAULT '',
  template      TEXT    NOT NULL DEFAULT 'bubble',  -- bubble / manga / game / lyric / letter
  options       TEXT    NOT NULL DEFAULT '{}',      -- テンプレートの調整値（JSON）
  comment       TEXT,                               -- エリカのひとこと
  tags          TEXT    NOT NULL DEFAULT '[]',      -- タグ（JSON 配列）
  spoiler       INTEGER NOT NULL DEFAULT 0,
  sort_order    INTEGER NOT NULL DEFAULT 0,         -- 大きいほど一覧の先頭
  created_at    TEXT    NOT NULL,
  updated_at    TEXT    NOT NULL,
  published_at  TEXT
);

CREATE INDEX IF NOT EXISTS idx_words_public ON words (status, sort_order DESC, published_at DESC);
