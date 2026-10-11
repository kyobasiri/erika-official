// ==========================================
// セーブデータ用の設定
// ==========================================
// セーブデータは必ずこのプレフィックス付きのキーに保存する。
// (以前は userId をそのままキーにしていたため、"labyrinth_ranking" などの
//  既存キーを外部から上書きできてしまっていた)
const SAVE_KEY_PREFIX = 'save:';
// RpgView が発行する ID は 'user_' + crypto.randomUUID()。
// 'user_' 始まりに限定することで、ランキング等のキーとは衝突しない。
const USER_ID_PATTERN = /^user_[A-Za-z0-9-]{8,64}$/;
// セーブには敵画像プール(ギャラリー全件)が含まれるため余裕を持たせる。KV の上限は 25MiB。
const MAX_SAVE_BYTES = 5 * 1024 * 1024;
// 最後に保存してから180日で自動的に消える（「最初から始める」で放置されたセーブが残り続けないように）
const SAVE_TTL_SECONDS = 180 * 24 * 60 * 60;

// ==========================================
// アバター生成の制限 (R2 の容量・書き込み回数を抑えるため)
// 値は Pages の環境変数で上書きできる。
// ==========================================
const DEFAULT_AVATAR_LIMIT_PER_IP_HOUR = 15; // 1つのIPあたり 1時間に生成できる枚数
const DEFAULT_AVATAR_LIMIT_PER_DAY = 300;    // サイト全体で 1日(JST)に生成できる枚数
const MAX_PROMPT_LENGTH = 2048;              // flux-1-schnell のプロンプト上限
const RATE_LIMIT_KEY_PREFIX = 'ratelimit:avatar:';

// ==========================================
// ラビリンスのランキング: ありえないスコアを弾くための上限
// ==========================================
const MAX_RANKING_FLOOR = 999;
const MAX_SCORE_PER_FLOOR = 35000;
const MAX_CLEAR_BONUS = 10000;

function readLimit(value, fallback) {
    const n = Number.parseInt(value, 10);
    return Number.isSafeInteger(n) && n > 0 ? n : fallback;
}

// IPアドレスはそのまま保存せず、ハッシュ化した先頭だけをキーに使う
async function hashIp(ip) {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(ip));
    return [...new Uint8Array(digest)]
        .slice(0, 12)
        .map((b) => b.toString(16).padStart(2, '0'))
        .join('');
}

function jstStamp(date = new Date()) {
    // 例: "2026-10-11T22" (JST)
    return new Date(date.getTime() + 9 * 60 * 60 * 1000).toISOString().slice(0, 13);
}

async function readCounter(kv, key) {
    const n = Number.parseInt((await kv.get(key)) || '0', 10);
    return Number.isSafeInteger(n) && n > 0 ? n : 0;
}

// ==========================================
// 好きな言葉（/words）の API
//   公開:  GET  /api/words                    公開中の言葉の一覧
//          GET  /api/words-images/<key>       R2 の画像を配信
//   管理:  GET  /api/admin/words              下書きを含む全件
//          POST /api/admin/words              新規作成
//          PUT  /api/admin/words/<id>         更新
//          DELETE /api/admin/words/<id>       削除（画像も削除）
//          POST /api/admin/words/<id>/image   画像のアップロード（本文に画像そのもの）
//   管理APIは Cloudflare Access で保護し、ここでも Access の JWT を検証する（失敗したら拒否）。
//   必要な設定: D1 バインディング DB、R2 バインディング R2_BUCKET、
//              環境変数 ACCESS_TEAM_DOMAIN（例: yourteam.cloudflareaccess.com）、ACCESS_AUD、ADMIN_EMAILS（任意）
// ==========================================
const WORD_TEMPLATES = ['bubble', 'manga', 'game', 'lyric', 'letter'];
const WORD_KINDS = ['manga', 'anime', 'game', 'song', 'movie', 'book', 'other'];
const WORD_ID_PATTERN = /^[a-z0-9][a-z0-9-]{1,62}$/;
const WORD_IMAGE_KEY_PATTERN = /^[a-z0-9][a-z0-9-]{1,80}\.(webp|jpg|png)$/;
const WORD_IMAGE_PREFIX = 'words/';
const WORD_IMAGE_TYPES = { 'image/webp': 'webp', 'image/jpeg': 'jpg', 'image/png': 'png' };
const MAX_WORD_IMAGE_BYTES = 6 * 1024 * 1024;

const jsonHeadersNoCors = { 'Content-Type': 'application/json; charset=utf-8' };
const wordsJson = (data, status = 200, extra = {}) =>
    new Response(JSON.stringify(data), { status, headers: { ...jsonHeadersNoCors, ...extra } });

// --- Cloudflare Access の JWT 検証 ---
let accessJwksCache = { team: '', keys: [], fetchedAt: 0 };

function base64UrlToBytes(value) {
    const b64 = value.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(value.length / 4) * 4, '=');
    return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
}
function base64UrlToJson(value) {
    return JSON.parse(new TextDecoder().decode(base64UrlToBytes(value)));
}
function readCookie(request, name) {
    const cookie = request.headers.get('Cookie') || '';
    for (const part of cookie.split(';')) {
        const [k, ...rest] = part.trim().split('=');
        if (k === name) return rest.join('=');
    }
    return '';
}
async function getAccessKeys(team, force = false) {
    const fresh = Date.now() - accessJwksCache.fetchedAt < 60 * 60 * 1000;
    if (!force && accessJwksCache.team === team && fresh && accessJwksCache.keys.length) return accessJwksCache.keys;
    const res = await fetch(`https://${team}/cdn-cgi/access/certs`);
    if (!res.ok) throw new Error('Access の公開鍵を取得できませんでした');
    const data = await res.json();
    accessJwksCache = { team, keys: Array.isArray(data.keys) ? data.keys : [], fetchedAt: Date.now() };
    return accessJwksCache.keys;
}
async function verifyAccess(request, env) {
    const team = (env.ACCESS_TEAM_DOMAIN || '').replace(/^https?:\/\//, '').replace(/\/$/, '');
    const aud = env.ACCESS_AUD || '';
    if (!team || !aud) return { ok: false, status: 503, error: '管理ページのログイン設定（ACCESS_TEAM_DOMAIN / ACCESS_AUD）がまだありません。' };

    const token = request.headers.get('Cf-Access-Jwt-Assertion') || readCookie(request, 'CF_Authorization');
    if (!token) return { ok: false, status: 401, error: 'ログインが必要です。' };

    try {
        const [h, p, s] = token.split('.');
        if (!h || !p || !s) throw new Error('形式が不正');
        const header = base64UrlToJson(h);
        const payload = base64UrlToJson(p);
        if (header.alg !== 'RS256') throw new Error('未対応の署名');

        let keys = await getAccessKeys(team);
        let jwk = keys.find((k) => k.kid === header.kid);
        if (!jwk) { keys = await getAccessKeys(team, true); jwk = keys.find((k) => k.kid === header.kid); }
        if (!jwk) throw new Error('鍵が見つからない');

        const key = await crypto.subtle.importKey('jwk', jwk, { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' }, false, ['verify']);
        const valid = await crypto.subtle.verify('RSASSA-PKCS1-v1_5', key, base64UrlToBytes(s), new TextEncoder().encode(`${h}.${p}`));
        if (!valid) throw new Error('署名が一致しない');

        const now = Math.floor(Date.now() / 1000);
        const auds = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
        if (!auds.includes(aud)) throw new Error('aud が一致しない');
        if (payload.iss !== `https://${team}`) throw new Error('iss が一致しない');
        if (typeof payload.exp !== 'number' || payload.exp < now) throw new Error('期限切れ');
        if (typeof payload.nbf === 'number' && payload.nbf > now + 60) throw new Error('まだ有効でない');

        const allowed = (env.ADMIN_EMAILS || '').split(',').map((e) => e.trim().toLowerCase()).filter(Boolean);
        const email = String(payload.email || '').toLowerCase();
        if (allowed.length && !allowed.includes(email)) return { ok: false, status: 403, error: 'このアカウントには管理権限がありません。' };

        return { ok: true, email };
    } catch (error) {
        console.warn('Access JWT verification failed:', error.message);
        return { ok: false, status: 401, error: 'ログインの確認に失敗しました。ページを再読み込みしてください。' };
    }
}

// --- 入力の検証と、行 ⇔ エントリーの変換 ---
const str = (v, max) => (typeof v === 'string' ? v.trim().slice(0, max) : '');
const optStr = (v, max) => { const s = str(v, max); return s || null; };

function sanitizeWordInput(body) {
    const errors = [];
    const source = body && typeof body.source === 'object' && body.source ? body.source : {};
    const quote = typeof body.quote === 'string' ? body.quote.replace(/\r\n?/g, '\n').trim().slice(0, 1000) : '';
    if (!quote) errors.push('言葉を入力してください。');

    const kind = WORD_KINDS.includes(source.kind) ? source.kind : 'other';
    const template = WORD_TEMPLATES.includes(body.template) ? body.template : 'bubble';
    const status = body.status === 'published' ? 'published' : 'draft';

    let options = body.options && typeof body.options === 'object' && !Array.isArray(body.options) ? body.options : {};
    const optionsJson = JSON.stringify(options);
    if (optionsJson.length > 4000) { errors.push('テンプレートの設定が大きすぎます。'); options = {}; }

    const tags = Array.isArray(body.tags)
        ? [...new Set(body.tags.map((t) => str(t, 30)).filter(Boolean))].slice(0, 10)
        : [];

    let sourceUrl = optStr(source.url, 500);
    if (sourceUrl && !/^https?:\/\//.test(sourceUrl)) { errors.push('公式ページのURLは http(s):// から始めてください。'); sourceUrl = null; }

    // 画像URLは、自分の R2 か、サイト内の静的ファイルだけを許可する
    let imageUrl = optStr(body.image, 300);
    if (imageUrl && !/^\/(api\/words-images|assets)\//.test(imageUrl)) imageUrl = null;

    const value = {
        status, quote,
        speaker: optStr(body.speaker, 100),
        source_title: str(source.title, 200),
        source_author: optStr(source.author, 200),
        source_kind: kind,
        source_detail: optStr(source.detail, 200),
        source_url: sourceUrl,
        image_url: imageUrl,
        image_alt: str(body.imageAlt, 300),
        template,
        options: JSON.stringify(options),
        comment: optStr(typeof body.comment === 'string' ? body.comment.replace(/\r\n?/g, '\n') : '', 4000),
        tags: JSON.stringify(tags),
        spoiler: body.spoiler ? 1 : 0,
        sort_order: Number.isSafeInteger(body.sortOrder) ? Math.max(-100000, Math.min(100000, body.sortOrder)) : 0,
    };

    if (status === 'published') {
        if (!value.source_title) errors.push('公開するには作品名が必要です。');
        if (!value.image_url) errors.push('公開するには画像が必要です。');
        if (!value.image_alt) errors.push('公開するには画像の説明（代替テキスト）が必要です。');
    }
    return { value, errors };
}

function parseJson(text, fallback) {
    try { const v = JSON.parse(text); return v ?? fallback; } catch { return fallback; }
}

function rowToEntry(row, includeAdmin = false) {
    const entry = {
        id: row.id,
        quote: row.quote,
        ...(row.speaker ? { speaker: row.speaker } : {}),
        source: {
            title: row.source_title,
            ...(row.source_author ? { author: row.source_author } : {}),
            kind: row.source_kind,
            ...(row.source_detail ? { detail: row.source_detail } : {}),
            ...(row.source_url ? { url: row.source_url } : {}),
        },
        image: row.image_url || '',
        imageAlt: row.image_alt || '',
        template: row.template,
        options: parseJson(row.options, {}),
        ...(row.comment ? { comment: row.comment } : {}),
        tags: parseJson(row.tags, []),
        spoiler: !!row.spoiler,
        ...(row.published_at ? { publishedAt: row.published_at } : {}),
    };
    if (includeAdmin) {
        Object.assign(entry, { status: row.status, sortOrder: row.sort_order, createdAt: row.created_at, updatedAt: row.updated_at });
    }
    return entry;
}

function newWordId() {
    return `w-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

async function readJsonBody(request) {
    const type = request.headers.get('Content-Type') || '';
    if (!type.includes('application/json')) throw Object.assign(new Error('JSON で送信してください。'), { status: 415 });
    const text = await request.text();
    if (text.length > 64 * 1024) throw Object.assign(new Error('送信データが大きすぎます。'), { status: 413 });
    try { return JSON.parse(text); } catch { throw Object.assign(new Error('JSON の形式が正しくありません。'), { status: 400 }); }
}

async function handleWordsApi(request, env, ctx, url) {
    const path = url.pathname;
    const method = request.method;

    try {
        // ---- 公開：画像 ----
        if (path.startsWith('/api/words-images/')) {
            if (method !== 'GET' && method !== 'HEAD') return wordsJson({ error: 'Method Not Allowed' }, 405);
            if (!env.R2_BUCKET) return wordsJson({ error: 'R2 が設定されていません。' }, 503);
            const key = decodeURIComponent(path.slice('/api/words-images/'.length));
            if (!WORD_IMAGE_KEY_PATTERN.test(key)) return wordsJson({ error: 'Not Found' }, 404);
            const object = await env.R2_BUCKET.get(WORD_IMAGE_PREFIX + key);
            if (!object) return wordsJson({ error: 'Not Found' }, 404);
            const headers = new Headers();
            object.writeHttpMetadata(headers);
            headers.set('etag', object.httpEtag);
            // キーは毎回新しく作るので、長くキャッシュしてよい
            headers.set('Cache-Control', 'public, max-age=31536000, immutable');
            return new Response(method === 'HEAD' ? null : object.body, { headers });
        }

        // ---- 公開：一覧 ----
        if (path === '/api/words') {
            if (method !== 'GET') return wordsJson({ error: 'Method Not Allowed' }, 405);
            if (!env.DB) return wordsJson({ error: 'words_db_not_configured' }, 503);
            const { results } = await env.DB.prepare(
                "SELECT * FROM words WHERE status = 'published' ORDER BY sort_order DESC, published_at DESC, created_at DESC"
            ).all();
            return wordsJson(results.map((r) => rowToEntry(r)), 200, { 'Cache-Control': 'public, max-age=60', 'Access-Control-Allow-Origin': '*' });
        }

        // ---- 管理 ----
        if (!path.startsWith('/api/admin/words')) return wordsJson({ error: 'Not Found' }, 404);

        const auth = await verifyAccess(request, env);
        if (!auth.ok) return wordsJson({ error: auth.error }, auth.status);

        // 書き込みは自サイトのページからだけ（他サイトからの送信を防ぐ）
        if (method !== 'GET' && request.headers.get('Origin') !== url.origin) {
            return wordsJson({ error: '外部サイトからは操作できません。' }, 403);
        }
        if (!env.DB) return wordsJson({ error: 'D1（DB）が設定されていません。' }, 503);

        const rest = path.slice('/api/admin/words'.length); // '' | '/<id>' | '/<id>/image'
        const [, id = '', sub = ''] = rest.split('/');
        const now = new Date().toISOString();

        if (rest === '' || rest === '/') {
            if (method === 'GET') {
                const { results } = await env.DB.prepare('SELECT * FROM words ORDER BY updated_at DESC').all();
                return wordsJson({ words: results.map((r) => rowToEntry(r, true)), email: auth.email }, 200, { 'Cache-Control': 'no-store' });
            }
            if (method === 'POST') {
                const body = await readJsonBody(request);
                const { value, errors } = sanitizeWordInput(body);
                if (errors.length) return wordsJson({ error: errors.join(' ') }, 400);
                const wordId = WORD_ID_PATTERN.test(body.id || '') ? body.id : newWordId();
                const exists = await env.DB.prepare('SELECT 1 FROM words WHERE id = ?').bind(wordId).first();
                if (exists) return wordsJson({ error: 'そのIDはすでに使われています。' }, 409);
                await env.DB.prepare(
                    `INSERT INTO words (id, status, quote, speaker, source_title, source_author, source_kind, source_detail, source_url,
                       image_url, image_key, image_alt, template, options, comment, tags, spoiler, sort_order, created_at, updated_at, published_at)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
                ).bind(wordId, value.status, value.quote, value.speaker, value.source_title, value.source_author, value.source_kind,
                    value.source_detail, value.source_url, value.image_url, value.image_alt, value.template, value.options, value.comment,
                    value.tags, value.spoiler, value.sort_order, now, now, value.status === 'published' ? now : null).run();
                const row = await env.DB.prepare('SELECT * FROM words WHERE id = ?').bind(wordId).first();
                return wordsJson({ word: rowToEntry(row, true) }, 201);
            }
            return wordsJson({ error: 'Method Not Allowed' }, 405);
        }

        if (!WORD_ID_PATTERN.test(id)) return wordsJson({ error: 'Not Found' }, 404);
        const current = await env.DB.prepare('SELECT * FROM words WHERE id = ?').bind(id).first();
        if (!current) return wordsJson({ error: '言葉が見つかりません。' }, 404);

        // 画像のアップロード
        if (sub === 'image') {
            if (method !== 'POST') return wordsJson({ error: 'Method Not Allowed' }, 405);
            if (!env.R2_BUCKET) return wordsJson({ error: 'R2 が設定されていません。' }, 503);
            const type = (request.headers.get('Content-Type') || '').split(';')[0].trim();
            const ext = WORD_IMAGE_TYPES[type];
            if (!ext) return wordsJson({ error: 'WebP・JPEG・PNG の画像を送ってください。' }, 415);
            const declared = Number(request.headers.get('Content-Length') || 0);
            if (declared > MAX_WORD_IMAGE_BYTES) return wordsJson({ error: '画像が大きすぎます（6MBまで）。' }, 413);
            const data = await request.arrayBuffer();
            if (!data.byteLength || data.byteLength > MAX_WORD_IMAGE_BYTES) return wordsJson({ error: '画像が大きすぎるか、空です（6MBまで）。' }, 413);

            const key = `${id}-${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}.${ext}`;
            await env.R2_BUCKET.put(WORD_IMAGE_PREFIX + key, data, { httpMetadata: { contentType: type } });
            await env.DB.prepare('UPDATE words SET image_url = ?, image_key = ?, updated_at = ? WHERE id = ?')
                .bind(`/api/words-images/${key}`, key, now, id).run();
            if (current.image_key && current.image_key !== key) ctx.waitUntil(env.R2_BUCKET.delete(WORD_IMAGE_PREFIX + current.image_key));
            const row = await env.DB.prepare('SELECT * FROM words WHERE id = ?').bind(id).first();
            return wordsJson({ word: rowToEntry(row, true) });
        }
        if (sub) return wordsJson({ error: 'Not Found' }, 404);

        if (method === 'PUT') {
            const body = await readJsonBody(request);
            const { value, errors } = sanitizeWordInput(body);
            if (errors.length) return wordsJson({ error: errors.join(' ') }, 400);
            // 画像はアップロードAPIで変える。ここでは既存の画像を保つ（静的画像の指定だけは許可）
            const imageUrl = current.image_key ? current.image_url : value.image_url;
            if (value.status === 'published' && !imageUrl) return wordsJson({ error: '公開するには画像が必要です。' }, 400);
            const publishedAt = value.status === 'published' ? (current.published_at || now) : current.published_at;
            await env.DB.prepare(
                `UPDATE words SET status = ?, quote = ?, speaker = ?, source_title = ?, source_author = ?, source_kind = ?, source_detail = ?,
                   source_url = ?, image_url = ?, image_alt = ?, template = ?, options = ?, comment = ?, tags = ?, spoiler = ?, sort_order = ?,
                   updated_at = ?, published_at = ? WHERE id = ?`
            ).bind(value.status, value.quote, value.speaker, value.source_title, value.source_author, value.source_kind, value.source_detail,
                value.source_url, imageUrl, value.image_alt, value.template, value.options, value.comment, value.tags, value.spoiler,
                value.sort_order, now, publishedAt, id).run();
            const row = await env.DB.prepare('SELECT * FROM words WHERE id = ?').bind(id).first();
            return wordsJson({ word: rowToEntry(row, true) });
        }

        if (method === 'DELETE') {
            await env.DB.prepare('DELETE FROM words WHERE id = ?').bind(id).run();
            if (current.image_key && env.R2_BUCKET) ctx.waitUntil(env.R2_BUCKET.delete(WORD_IMAGE_PREFIX + current.image_key));
            return wordsJson({ success: true });
        }

        return wordsJson({ error: 'Method Not Allowed' }, 405);
    } catch (error) {
        if (error && error.status) return wordsJson({ error: error.message }, error.status);
        console.error('Words API Error:', error);
        return wordsJson({ error: '処理中にエラーが発生しました。' }, 500);
    }
}

export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);
        const path = url.pathname;
        const corsHeaders = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        };

        // 0. 好きな言葉の API（管理用には CORS を付けないので、OPTIONS より先に振り分ける）
        if (path === '/api/words' || path.startsWith('/api/words-images/') || path.startsWith('/api/admin/')) {
            return handleWordsApi(request, env, ctx, url);
        }

        if (request.method === 'OPTIONS') {
            return new Response(null, { headers: corsHeaders });
        }

        try {
            // 1. アバター画像生成
            if (path === '/api/generate-avatar' && request.method === 'POST') {
                if (!env.AI) throw new Error("Cloudflare AI のバインディング (env.AI) が設定されていません。");
                if (!env.R2_BUCKET) throw new Error("R2 バケットのバインディング (env.R2_BUCKET) が設定されていません。");
                if (!env.KV_BINDING) throw new Error("KV のバインディングが設定されていません。");

                const jsonHeaders = { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' };
                const errorResponse = (status, error, extraHeaders = {}) =>
                    new Response(JSON.stringify({ error }), {
                        status,
                        headers: { ...jsonHeaders, ...extraHeaders },
                    });

                // 自サイトのページからの呼び出しのみ受け付ける。
                // (ブラウザは POST の fetch に必ず Origin を付ける。curl 等での偽装は可能なので、
                //  本命の防御は下のレート制限)
                if (request.headers.get('Origin') !== url.origin) {
                    return errorResponse(403, '外部サイトからの画像生成はできません。');
                }

                let body;
                try {
                    body = await request.json();
                } catch {
                    return errorResponse(400, 'JSON形式で送信してください。');
                }
                const prompt = typeof body?.prompt === 'string' ? body.prompt.trim() : '';
                if (!prompt) return errorResponse(400, 'プロンプトが空です。');
                if (prompt.length > MAX_PROMPT_LENGTH) {
                    return errorResponse(400, `プロンプトが長すぎます（${MAX_PROMPT_LENGTH}文字まで）。要素を減らしてください。`);
                }

                // --- レート制限 (KV のカウンター。厳密ではないが上限の目安として十分) ---
                const perIpLimit = readLimit(env.AVATAR_LIMIT_PER_IP_HOUR, DEFAULT_AVATAR_LIMIT_PER_IP_HOUR);
                const perDayLimit = readLimit(env.AVATAR_LIMIT_PER_DAY, DEFAULT_AVATAR_LIMIT_PER_DAY);
                const stamp = jstStamp();
                const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
                const ipKey = `${RATE_LIMIT_KEY_PREFIX}ip:${await hashIp(ip)}:${stamp}`;
                const dayKey = `${RATE_LIMIT_KEY_PREFIX}day:${stamp.slice(0, 10)}`;

                const [ipCount, dayCount] = await Promise.all([
                    readCounter(env.KV_BINDING, ipKey),
                    readCounter(env.KV_BINDING, dayKey),
                ]);
                if (dayCount >= perDayLimit) {
                    return errorResponse(429, '本日の画像生成枠を使い切りました。明日また遊びに来てください。', { 'Retry-After': '3600' });
                }
                if (ipCount >= perIpLimit) {
                    return errorResponse(429, '画像生成の回数が上限に達しました。1時間ほど時間をおいてから再度お試しください。', { 'Retry-After': '3600' });
                }

                const imageResponse = await env.AI.run(
                    '@cf/black-forest-labs/flux-1-schnell',
                    { prompt: prompt }
                );

                let imgData;
                // Base64文字列が含まれるJSONか、直接のバイナリデータかを判定
                if (imageResponse && imageResponse.image) {
                    const b64 = imageResponse.image.replace(/^data:image\/\w+;base64,/, "");
                    const binaryString = atob(b64);
                    imgData = Uint8Array.from(binaryString, (m) => m.codePointAt(0));
                } else {
                    imgData = imageResponse; // 生データの場合はそのまま扱う
                }

                const fileName = `avatar-${Date.now()}-${Math.random().toString(36).substring(7)}.jpeg`;

                await env.R2_BUCKET.put(fileName, imgData, {
                    httpMetadata: { contentType: 'image/jpeg' },
                });

                // R2 に保存できた分だけ数える (NSFW 等で失敗した試行は数えない)
                ctx.waitUntil(Promise.all([
                    env.KV_BINDING.put(ipKey, String(ipCount + 1), { expirationTtl: 2 * 60 * 60 }),
                    env.KV_BINDING.put(dayKey, String(dayCount + 1), { expirationTtl: 2 * 24 * 60 * 60 }),
                ]));

                const avatarUrl = `${url.origin}/api/avatars/${fileName}`;
                return new Response(JSON.stringify({ avatarUrl }), { headers: jsonHeaders });
            }

            // 2. R2画像の配信
            if (path.startsWith('/api/avatars/') && request.method === 'GET') {
                if (!env.R2_BUCKET) throw new Error("R2 バケットのバインディングが設定されていません。");
                const fileName = path.replace('/api/avatars/', '');
                const object = await env.R2_BUCKET.get(fileName);

                if (!object) return new Response('Image Not Found', { status: 404, headers: corsHeaders });

                const headers = new Headers(corsHeaders);
                object.writeHttpMetadata(headers);
                headers.set('etag', object.httpEtag);
                return new Response(object.body, { headers });
            }

            // 3. セーブデータの保存
            if (path === '/api/save' && request.method === 'POST') {
                if (!env.KV_BINDING) throw new Error("KV のバインディングが設定されていません。");
                const jsonHeaders = { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' };
                const errorResponse = (status, error) =>
                    new Response(JSON.stringify({ error }), { status, headers: jsonHeaders });

                const declaredLength = Number(request.headers.get('Content-Length') || 0);
                if (declaredLength > MAX_SAVE_BYTES) return errorResponse(413, 'セーブデータが大きすぎます。');

                const text = await request.text();
                if (new TextEncoder().encode(text).byteLength > MAX_SAVE_BYTES) {
                    return errorResponse(413, 'セーブデータが大きすぎます。');
                }

                let body;
                try {
                    body = JSON.parse(text);
                } catch {
                    return errorResponse(400, 'JSON形式で送信してください。');
                }

                const userId = body?.userId;
                if (typeof userId !== 'string' || !USER_ID_PATTERN.test(userId)) {
                    return errorResponse(400, 'ユーザーIDが不正です。');
                }
                if (!body.data || typeof body.data !== 'object' || Array.isArray(body.data)) {
                    return errorResponse(400, 'セーブデータの形式が不正です。');
                }

                await env.KV_BINDING.put(SAVE_KEY_PREFIX + userId, JSON.stringify(body.data), { expirationTtl: SAVE_TTL_SECONDS });
                return new Response(JSON.stringify({ success: true }), { headers: jsonHeaders });
            }

            // 4. セーブデータの読み込み
            if (path === '/api/load' && request.method === 'GET') {
                if (!env.KV_BINDING) throw new Error("KV のバインディングが設定されていません。");
                const jsonHeaders = { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' };
                const userId = url.searchParams.get('userId') || '';
                if (!USER_ID_PATTERN.test(userId)) {
                    return new Response(JSON.stringify({ error: 'ユーザーIDが不正です。' }), { status: 400, headers: jsonHeaders });
                }

                const saveKey = SAVE_KEY_PREFIX + userId;
                let data = await env.KV_BINDING.get(saveKey);

                // 旧形式 (userId そのものがキー) のセーブが残っていれば新しいキーへ移す。
                // userId は 'user_' 始まりに限定済みなので、ランキング等のキーを読むことはない。
                if (!data) {
                    const legacy = await env.KV_BINDING.get(userId);
                    if (legacy) {
                        data = legacy;
                        ctx.waitUntil(
                            env.KV_BINDING.put(saveKey, legacy, { expirationTtl: SAVE_TTL_SECONDS }).then(() => env.KV_BINDING.delete(userId))
                        );
                    }
                }

                if (!data) return new Response(JSON.stringify({ error: 'No save data found' }), { status: 404, headers: jsonHeaders });
                return new Response(data, { headers: jsonHeaders });
            }

            // 5. ランキングAPI
            if (path === '/api/ranking') {
                const jsonHeaders = {
                    ...corsHeaders,
                    'Content-Type': 'application/json; charset=utf-8',
                    'Cache-Control': 'no-store',
                };

                const jsonResponse = (data, status = 200) =>
                    new Response(JSON.stringify(data), {
                        status,
                        headers: jsonHeaders,
                    });

                if (!['GET', 'POST'].includes(request.method)) {
                    return new Response(
                        JSON.stringify({ error: 'Method Not Allowed' }),
                        {
                            status: 405,
                            headers: {
                                ...jsonHeaders,
                                Allow: 'GET, POST, OPTIONS',
                            },
                        }
                    );
                }

                if (!env.KV_BINDING) {
                    return jsonResponse({
                        error: 'KV_BINDING が設定されていません。',
                    }, 500);
                }

                const rankingKey = 'labyrinth_ranking';

                try {
                    // POSTの入力は、保存データを変更する前に確認する。
                    let newEntry = null;

                    if (request.method === 'POST') {
                        let body;

                        try {
                            body = await request.json();
                        } catch {
                            return jsonResponse({
                                error: 'JSON形式で送信してください。',
                            }, 400);
                        }

                        if (!body || typeof body !== 'object' || Array.isArray(body)) {
                            return jsonResponse({
                                error: '送信データが不正です。',
                            }, 400);
                        }

                        if (
                            !Number.isSafeInteger(body.score) ||
                            body.score < 0 ||
                            !Number.isSafeInteger(body.floor) ||
                            body.floor < 1
                        ) {
                            return jsonResponse({
                                error: 'スコアまたは階層が不正です。',
                            }, 400);
                        }

                        // スコアはブラウザ側で計算しているため、明らかにありえない値だけ弾く。
                        // 1階層あたりの上限の目安:
                        //   階層 1000 + コイン(イベント最大約45マス×200) + 残り時間(回復・延長・スロット込みで約2300秒×10)
                        //   ≒ 33000 → 余裕を見て 35000。これに最大クリアボーナス 10000 を足す。
                        if (
                            body.floor > MAX_RANKING_FLOOR ||
                            body.score > body.floor * MAX_SCORE_PER_FLOOR + MAX_CLEAR_BONUS
                        ) {
                            return jsonResponse({
                                error: 'スコアが範囲外のため登録できません。',
                            }, 400);
                        }

                        newEntry = {
                            name:
                                typeof body.name === 'string'
                                    ? body.name.trim().slice(0, 40) || '名無しの冒険者'
                                    : '名無しの冒険者',
                            score: body.score,
                            floor: body.floor,
                            avatarUrl:
                                typeof body.avatarUrl === 'string' && body.avatarUrl
                                    ? body.avatarUrl
                                    : '/assets/images/icon.png',
                            date: new Date().toISOString(),
                        };
                    }

                    const stored = await env.KV_BINDING.get(rankingKey);
                    const rankings = stored ? JSON.parse(stored) : [];

                    if (!Array.isArray(rankings)) {
                        throw new Error('保存済みランキングが配列ではありません。');
                    }

                    if (newEntry) {
                        rankings.push(newEntry);
                    }

                    rankings.sort((a, b) => b.score - a.score);
                    const topRankings = rankings.slice(0, 50);

                    if (request.method === 'GET') {
                        return jsonResponse(topRankings);
                    }

                    await env.KV_BINDING.put(
                        rankingKey,
                        JSON.stringify(topRankings)
                    );

                    return jsonResponse({ success: true });
                } catch (error) {
                    console.error('Ranking API Error:', error);

                    return jsonResponse({
                        error:
                            request.method === 'GET'
                                ? 'ランキングの取得に失敗しました。'
                                : 'スコアの保存に失敗しました。',
                    }, 500);
                }
            }

            // 5. 静的ファイルのフォールバック
            return env.ASSETS.fetch(request);

        } catch (error) {
            console.error("Worker Error:", error);
            const errMsg = error.message || error.toString();

            if (errMsg.includes('8007') || errMsg.includes('NSFW')) {
                return new Response(JSON.stringify({ error: "NSFW_ERROR" }), {
                    status: 400, // 不正なリクエストとして返す
                    headers: corsHeaders
                });
            }

            // それ以外の通常のエラー
            return new Response(JSON.stringify({ error: errMsg }), {
                status: 500,
                headers: corsHeaders
            });
        }
    }
};