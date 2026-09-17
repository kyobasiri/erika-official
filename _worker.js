export default {
    async fetch(request, env, ctx) {
        const url = new URL(request.url);
        const path = url.pathname;

        // --- CORS プレフライトリクエスト対応 ---
        const corsHeaders = {
            'Access-Control-Allow-Origin': '*', // 全許可。本番時はサイトのURLに制限推奨
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        };

        // ブラウザの仕様（OPTIONSリクエスト）への対応
        if (request.method === 'OPTIONS') {
            return new Response(null, { headers: corsHeaders });
        }

        try {
            // ==========================================
            // 1. アバター画像生成 (Workers AI + R2)
            // ==========================================
            if (path === '/api/generate-avatar' && request.method === 'POST') {
                const { prompt } = await request.json();

                // Workers AI (Fluxモデル) を呼び出し
                const imageResponse = await env.AI.run(
                    '@cf/black-forest-labs/flux-2-klein-4b',
                    { prompt: prompt }
                );

                // ファイル名を生成（タイムスタンプ + ランダム文字列）
                const fileName = `avatar-${Date.now()}-${Math.random().toString(36).substring(7)}.png`;

                // R2バケットへ画像を保存
                await env.R2_BUCKET.put(fileName, imageResponse, {
                    httpMetadata: { contentType: 'image/png' },
                });

                // フロントエンドからアクセスするためのURLを構築
                const avatarUrl = `${url.origin}/api/avatars/${fileName}`;

                return new Response(JSON.stringify({ avatarUrl }), { headers: corsHeaders });
            }

            // ==========================================
            // 2. R2画像の配信（フロントエンドでの表示用）
            // ==========================================
            if (path.startsWith('/api/avatars/') && request.method === 'GET') {
                const fileName = path.replace('/api/avatars/', '');

                // R2からオブジェクトを取得
                const object = await env.R2_BUCKET.get(fileName);

                if (!object) {
                    return new Response('Image Not Found', { status: 404, headers: corsHeaders });
                }

                // 画像データとしてブラウザに返すためのヘッダー設定
                const headers = new Headers(corsHeaders);
                object.writeHttpMetadata(headers);
                headers.set('etag', object.httpEtag);

                return new Response(object.body, { headers });
            }

            // ==========================================
            // 3. セーブデータの保存 (KV)
            // ==========================================
            if (path === '/api/save' && request.method === 'POST') {
                const body = await request.json();
                const saveKey = body.userId || 'save_data_default';

                await env.KV_BINDING.put(saveKey, JSON.stringify(body.data));
                return new Response(JSON.stringify({ success: true }), { headers: corsHeaders });
            }

            // ==========================================
            // 4. セーブデータの読み込み (KV)
            // ==========================================
            if (path === '/api/load' && request.method === 'GET') {
                const userId = url.searchParams.get('userId') || 'save_data_default';
                const data = await env.KV_BINDING.get(userId);

                if (!data) {
                    return new Response(JSON.stringify({ error: 'No save data found' }), { status: 404, headers: corsHeaders });
                }
                return new Response(data, { headers: corsHeaders });
            }

            // ==========================================
            // 5. 静的ファイルのフォールバック（超重要）
            // ==========================================
            // APIのパスに一致しないもの（index.htmlやrpg.htmlへのアクセスなど）は、
            // 通常のCloudflare Pagesのファイル配信処理に回します。
            return env.ASSETS.fetch(request);

        } catch (error) {
            console.error("Worker Error:", error);
            return new Response(JSON.stringify({ error: error.message }), {
                status: 500,
                headers: corsHeaders
            });
        }
    }
};