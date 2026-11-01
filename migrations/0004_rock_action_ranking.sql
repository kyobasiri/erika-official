-- ERIKA ROCK ACTION の全国ランキング（ラビリンスと同じ仕組み）
-- 適用: npx wrangler d1 migrations apply erika-words --remote

CREATE TABLE IF NOT EXISTS rock_action_ranking (
  id          TEXT PRIMARY KEY,
  name        TEXT    NOT NULL,
  score       INTEGER NOT NULL,
  stage       INTEGER NOT NULL,   -- 到達ステージ
  ip_hash     TEXT,               -- 回数制限用（IP をハッシュ化したもの）。1日たつと消す
  created_at  TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_rock_ranking_score ON rock_action_ranking (score DESC, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_rock_ranking_ip ON rock_action_ranking (ip_hash, created_at);
