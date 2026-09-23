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