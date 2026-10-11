# 好きな言葉ページ（/words）の管理ページ 設定手順

管理ページ `https://erika.erikakataru.com/admin/words` を使えるようにするための設定です。
作業はすべて Cloudflare のダッシュボードと、PC のターミナル（このリポジトリのフォルダ）で行います。所要時間は20〜30分ほどです。

## 全体像

| 役割 | 使うもの | 状態 |
|---|---|---|
| 言葉のデータ | D1（データベース） | **新しく作る** |
| 画像 | R2（`erika-rpg-assets` バケットの `words/` 以下） | 既存のものを共用。設定不要 |
| ログイン | Cloudflare Access（Zero Trust） | **新しく設定する** |
| API | `public/_worker.js` | 実装済み |

---

## 1. D1 データベースを作る

```bash
npx wrangler login                      # 初回のみ。ブラウザで Cloudflare にログイン
npx wrangler d1 create erika-words
```

表示された `database_id`（長い英数字）を控えます。

## 2. wrangler.toml を設定する

`wrangler.toml` の末尾にある「4. 好きな言葉」の `[[d1_databases]]` のコメント（`#`）を外し、`database_id` に 1 の値を入れます。
（`[vars]` は 4 で埋めるので、まだコメントのままで構いません）

```toml
[[d1_databases]]
binding = "DB"
database_name = "erika-words"
database_id = "1 で控えた ID"
migrations_dir = "migrations"
```

## 3. テーブルを作る（マイグレーション）

```bash
npx wrangler d1 migrations apply erika-words --remote
```

- `0001_words.sql` … テーブルを作成
- `0002_sample_drafts.sql` … 試作で使ったサンプル5件を **下書き** として登録（公開はされません。不要なら管理ページで削除してください）

## 4. Cloudflare Access でログインを設定する

### 4-1. Zero Trust を有効にする（初回のみ）
1. Cloudflare ダッシュボードで **Zero Trust** を開く
2. チーム名を決める（例：`erika`）。これが `erika.cloudflareaccess.com` になります
3. プランは **Free**（50ユーザーまで無料）。※無料プランでも支払い方法の入力を求められますが、請求はされません

### 4-2. 管理ページ用のアプリを作る
1. Zero Trust → **Access** → **Applications** → **Add an application** → **Self-hosted**
2. アプリ名：`Erika 言葉の管理`
3. **Public hostname** を2つ追加
   - `erika.erikakataru.com` ／ パス `admin`
   - `erika.erikakataru.com` ／ パス `api/admin`
   - （任意）`erika-official.pages.dev` にも同じ2つ。追加しなくても、Worker 側の検証で `pages.dev` からの操作は拒否されます
4. **Policy**：Action = **Allow**、Include = **Emails** に自分のメールアドレス
5. ログイン方法は既定の **One-time PIN**（メールに届くコードでログイン）で十分です。Google アカウントでログインしたい場合は Settings → Authentication で追加できます
6. 保存したら、アプリの概要に表示される **Application Audience (AUD) Tag** を控えます

## 5. ログイン設定を wrangler.toml に入れる

`[vars]` のコメントを外して埋めます。（どれも秘密情報ではないので、リポジトリに入れて大丈夫です）

```toml
[vars]
ACCESS_TEAM_DOMAIN = "erika.cloudflareaccess.com"   # 4-1 のチーム名
ACCESS_AUD = "4-2 で控えた AUD Tag"
ADMIN_EMAILS = "自分のメールアドレス"               # 複数ならカンマ区切り
```

## 6. デプロイして確認

1. main に push（GitHub Actions がビルドして Cloudflare Pages にデプロイします）
2. `https://erika.erikakataru.com/admin/words` を開く → Access のログイン画面 → メールのコードでログイン
3. 一覧にサンプルの下書き5件が出れば成功です
4. 言葉を作って「公開する」を押すと、`/words` に表示されます

---

## うまくいかないとき

| 症状 | 原因と対処 |
|---|---|
| 管理ページに「まだ準備ができていません」 | `wrangler.toml` の `[vars]` か `[[d1_databases]]` が未設定。5 と 2 を確認 |
| 「ログインの確認に失敗しました」 | `ACCESS_AUD` か `ACCESS_TEAM_DOMAIN` の値の違い。AUD Tag をコピーし直す |
| 「このアカウントには管理権限がありません」 | `ADMIN_EMAILS` とログインしたメールアドレスが違う |
| `/words` が「読み込めませんでした」 | D1 が未設定、またはマイグレーション未実行（2・3） |
| デプロイが失敗する | `database_id` が正しくない（作成前の値のまま、など） |

## 仕組みのメモ

- 公開API：`GET /api/words`（公開中だけ）、`GET /api/words-images/<key>`（画像）
- 管理API：`/api/admin/words`（一覧・作成）、`/api/admin/words/<id>`（更新・削除）、`/api/admin/words/<id>/image`（画像）
- 管理APIは、Access のログイン証明（JWT）を Worker でも検証し、さらに自サイトからの書き込みだけを受け付けます
- 画像はブラウザで横1200pxまでに縮小して WebP にしてから送ります（6MBまで）
