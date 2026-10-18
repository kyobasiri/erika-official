// ==========================================
// エリカの最新動画を返す Worker（erika-youtube-worker）
//
//   GET /  →  { "long": { id, title, published, isShort: false },
//               "short": { id, title, published, isShort: true } }
//   取れなかった方は { "error": "Not found" } になる（トップページは、そのとき固定の動画を出す）。
//
// しくみ
//   YouTube は、チャンネルごとに次の「自動の再生リスト」を持っている（チャンネルIDの先頭 UC を置き換える）。
//     UULF… … 通常の動画だけ（ショート・ライブ配信は入らない）
//     UUSH… … ショートだけ
//   その RSS（APIキー不要）を読んで、それぞれの一番新しい1本を返す。
//   以前は「チャンネル全体の新着（最大15本）」から通常の動画を探していたため、
//   ショートが15本続くと通常の動画が見つからず "Not found" になっていた。
//
//   ・RSS には限定公開・非公開の動画は載らない（日報の限定公開動画は出てこない）
//   ・結果は30分キャッシュする（YouTube へのアクセスを減らす）
//   ・YouTube が一時的に応答しないときは、最後に取れた結果（7日間保存）を返す
// ==========================================

const CHANNEL_ID = 'UCcLpUu88d6QTwZswJmOgtvw';
const CHANNEL_SUFFIX = CHANNEL_ID.slice(2); // 先頭の "UC" を除いた部分

const FEED_URL = (query) => `https://www.youtube.com/feeds/videos.xml?${query}`;
const LONG_FEED = FEED_URL(`playlist_id=UULF${CHANNEL_SUFFIX}`);
const SHORT_FEED = FEED_URL(`playlist_id=UUSH${CHANNEL_SUFFIX}`);
// 予備：チャンネル全体の新着（再生リストの RSS が使えなかったときだけ使う）
const CHANNEL_FEED = FEED_URL(`channel_id=${CHANNEL_ID}`);

const CACHE_SECONDS = 30 * 60;            // ふだんのキャッシュ（30分）
const LAST_GOOD_SECONDS = 7 * 24 * 60 * 60; // 予備に取っておく、最後に取れた結果（7日）
const FETCH_TIMEOUT_MS = 8000;

// 呼び出しを許可するサイト（公開してよい情報なので、ほかのサイトから読まれても困りはしないが、念のため絞る）
const ALLOWED_ORIGINS = [
    'https://erika.erikakataru.com',
    'https://erika-official.pages.dev',
    'http://localhost:5173',
    'http://localhost:4173',
];

const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/;

// ---------- RSS の読み取り ----------

// XML の文字参照（&amp; など）を元の文字に戻す
function decodeXml(text) {
    return text
        .replace(/&#x([0-9a-f]+);/gi, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
        .replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(parseInt(dec, 10)))
        .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&apos;/g, "'")
        .replace(/&amp;/g, '&');
}

function pick(xml, tag) {
    const m = new RegExp(`<${tag}>([\\s\\S]*?)</${tag}>`).exec(xml);
    return m ? decodeXml(m[1].trim()) : '';
}

// RSS から動画の一覧を取り出す（新しい順に並んでいる）
function parseFeed(xml) {
    const entries = [];
    for (const m of xml.matchAll(/<entry>([\s\S]*?)<\/entry>/g)) {
        const entry = m[1];
        const id = pick(entry, 'yt:videoId');
        if (!VIDEO_ID.test(id)) continue;
        const link = (/<link[^>]*href="([^"]+)"/.exec(entry) || [])[1] || '';
        entries.push({
            id,
            title: pick(entry, 'title'),
            published: pick(entry, 'published'),
            // チャンネル全体の RSS のときだけ使う目安（ショートはリンクが /shorts/ になっていることがある）
            linkIsShort: link.includes('/shorts/'),
        });
    }
    // 念のため、公開日の新しい順に並べ直す
    return entries.sort((a, b) => (b.published || '').localeCompare(a.published || ''));
}

async function fetchWithTimeout(url, init = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
    try {
        return await fetch(url, { ...init, signal: controller.signal });
    } finally {
        clearTimeout(timer);
    }
}

// RSS を取得して一覧にする。取れなかったら null
async function loadFeed(url) {
    try {
        const res = await fetchWithTimeout(url, { headers: { 'User-Agent': 'erika-youtube-worker' } });
        if (!res.ok) return null;
        return parseFeed(await res.text());
    } catch {
        return null;
    }
}

// その動画がショートかどうかを確かめる（予備の方法でだけ使う）。
// youtube.com/shorts/<id> は、ショートなら 200、通常の動画なら別のページへ転送（3xx）になる
async function isShortVideo(id) {
    try {
        const res = await fetchWithTimeout(`https://www.youtube.com/shorts/${id}`, { method: 'HEAD', redirect: 'manual' });
        return res.status === 200;
    } catch {
        return false;
    }
}

const toVideo = (entry, isShort) =>
    entry ? { id: entry.id, title: entry.title, published: entry.published, isShort } : { error: 'Not found' };

// ---------- 最新動画を調べる ----------

async function findLatestVideos() {
    const [longFeed, shortFeed] = await Promise.all([loadFeed(LONG_FEED), loadFeed(SHORT_FEED)]);

    let long = longFeed?.[0] ?? null;
    let short = shortFeed?.[0] ?? null;

    // 再生リストの RSS が取れなかった方だけ、チャンネル全体の新着から探す
    if (longFeed === null || shortFeed === null) {
        const channelFeed = (await loadFeed(CHANNEL_FEED)) ?? [];
        for (const entry of channelFeed) {
            if (long && short) break;
            const shortFlag = entry.linkIsShort || (await isShortVideo(entry.id));
            if (shortFlag && !short && shortFeed === null) short = entry;
            if (!shortFlag && !long && longFeed === null) long = entry;
        }
    }

    return { long: toVideo(long, false), short: toVideo(short, true) };
}

// ---------- レスポンス ----------

function corsHeaders(request) {
    const origin = request.headers.get('Origin') || '';
    const headers = { Vary: 'Origin' };
    if (ALLOWED_ORIGINS.includes(origin)) headers['Access-Control-Allow-Origin'] = origin;
    return headers;
}

function jsonResponse(data, request, cacheSeconds) {
    return new Response(JSON.stringify(data), {
        headers: {
            'Content-Type': 'application/json; charset=utf-8',
            'Cache-Control': `public, max-age=${cacheSeconds}`,
            ...corsHeaders(request),
        },
    });
}

export default {
    async fetch(request, env, ctx) {
        if (request.method === 'OPTIONS') {
            return new Response(null, {
                headers: { ...corsHeaders(request), 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Max-Age': '86400' },
            });
        }
        if (request.method !== 'GET') {
            return new Response(JSON.stringify({ error: 'Method Not Allowed' }), {
                status: 405, headers: { 'Content-Type': 'application/json; charset=utf-8', Allow: 'GET, OPTIONS' },
            });
        }

        // キャッシュは、呼び出し元のサイトに関係なく1つにする（CORS のヘッダーは返すときに付け直す）
        const cache = caches.default;
        const cacheKey = new Request(new URL('/__latest', request.url).toString());
        const lastGoodKey = new Request(new URL('/__last-good', request.url).toString());

        // ?refresh=1 を付けると、キャッシュを使わずに取り直す（動画を上げた直後の確認用）
        const refresh = new URL(request.url).searchParams.get('refresh') === '1';
        if (!refresh) {
            const cached = await cache.match(cacheKey);
            if (cached) return jsonResponse(await cached.json(), request, CACHE_SECONDS);
        }

        let data = await findLatestVideos();
        const complete = !data.long.error && !data.short.error;

        if (complete) {
            // 取れた結果を、ふだん用と予備用の両方に保存する
            const save = (key, seconds) => cache.put(key, new Response(JSON.stringify(data), {
                headers: { 'Content-Type': 'application/json', 'Cache-Control': `public, max-age=${seconds}` },
            }));
            ctx.waitUntil(Promise.all([save(cacheKey, CACHE_SECONDS), save(lastGoodKey, LAST_GOOD_SECONDS)]));
            return jsonResponse(data, request, CACHE_SECONDS);
        }

        // 一部でも取れなかったときは、最後に取れた結果で足りない方を埋める
        const lastGood = await cache.match(lastGoodKey);
        if (lastGood) {
            const previous = await lastGood.json();
            data = {
                long: data.long.error ? previous.long : data.long,
                short: data.short.error ? previous.short : data.short,
            };
        }
        // 取れなかった結果は短めにキャッシュする（すぐに取り直せるように）
        return jsonResponse(data, request, 5 * 60);
    },
};