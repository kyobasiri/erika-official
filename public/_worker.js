export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);
        const path = url.pathname;
        const corsHeaders = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        };

        if (request.method === 'OPTIONS') {
            return new Response(null, { headers: corsHeaders });
        }

        try {
            // 1. アバター画像生成
            if (path === '/api/generate-avatar' && request.method === 'POST') {
                if (!env.AI) throw new Error("Cloudflare AI のバインディング (env.AI) が設定されていません。");
                if (!env.R2_BUCKET) throw new Error("R2 バケットのバインディング (env.R2_BUCKET) が設定されていません。");

                const { prompt } = await request.json();

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

                const avatarUrl = `${url.origin}/api/avatars/${fileName}`;
                return new Response(JSON.stringify({ avatarUrl }), { headers: corsHeaders });
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
                const body = await request.json();
                const saveKey = body.userId || 'save_data_default';
                await env.KV_BINDING.put(saveKey, JSON.stringify(body.data));
                return new Response(JSON.stringify({ success: true }), { headers: corsHeaders });
            }

            // 4. セーブデータの読み込み
            if (path === '/api/load' && request.method === 'GET') {
                if (!env.KV_BINDING) throw new Error("KV のバインディングが設定されていません。");
                const userId = url.searchParams.get('userId') || 'save_data_default';
                const data = await env.KV_BINDING.get(userId);

                if (!data) return new Response(JSON.stringify({ error: 'No save data found' }), { status: 404, headers: corsHeaders });
                return new Response(data, { headers: corsHeaders });
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