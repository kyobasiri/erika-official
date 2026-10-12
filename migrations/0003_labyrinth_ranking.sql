-- ラビリンスのランキング（以前は KV の "labyrinth_ranking" に配列で保存していた）
-- 1回の登録 = 1行の INSERT にすることで、同時に登録されてもどちらかが消えることがない。
-- 既存の KV のランキングは、テーブルが空のときに _worker.js が自動で取り込む。
-- 適用: npx wrangler d1 migrations apply erika-words --remote

CREATE TABLE IF NOT EXISTS labyrinth_ranking (
  id          TEXT PRIMARY KEY,
  name        TEXT    NOT NULL,
  score       INTEGER NOT NULL,
  floor       INTEGER NOT NULL,
  avatar_url  TEXT    NOT NULL,
  ip_hash     TEXT,                -- 回数制限用（IP をハッシュ化したもの）。1日たつと消す
  created_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ranking_score ON labyrinth_ranking (score DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_ranking_ip ON labyrinth_ranking (ip_hash, created_at);
