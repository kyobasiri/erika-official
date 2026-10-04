// functions/api/ranking.ts

// KVからランキングを取得する処理 (GETリクエスト)
export const onRequestGet = async (context: any) => {
    const { env } = context;
    try {
        // KV_BINDING から "labyrinth_ranking" というキーでデータを取得
        const data = await env.KV_BINDING.get("labyrinth_ranking");
        const rankings = data ? JSON.parse(data) : [];

        return new Response(JSON.stringify(rankings), {
            headers: { "Content-Type": "application/json" },
            status: 200,
        });
    } catch (error) {
        console.error("GET Error:", error);
        return new Response(JSON.stringify({ error: "ランキングの取得に失敗しました" }), {
            headers: { "Content-Type": "application/json" },
            status: 500,
        });
    }
};

// KVへスコアを保存する処理 (POSTリクエスト)
export const onRequestPost = async (context: any) => {
    const { request, env } = context;
    try {
        // フロントエンドから送られてきたデータを受け取る
        const newScore = await request.json();

        // 既存のランキングデータを取得
        const data = await env.KV_BINDING.get("labyrinth_ranking");
        let rankings = data ? JSON.parse(data) : [];

        // 新しいスコアを追加
        rankings.push({
            name: newScore.name || "名無しの冒険者",
            score: newScore.score || 0,
            floor: newScore.floor || 1,
            avatarUrl: newScore.avatarUrl || "/assets/images/icon.png",
            date: new Date().toISOString()
        });

        // スコアの高い順に並び替え (降順)
        rankings.sort((a: any, b: any) => b.score - a.score);

        // データが大きくなりすぎないよう、上位50件だけ残す
        rankings = rankings.slice(0, 50);

        // KVに保存し直す
        await env.KV_BINDING.put("labyrinth_ranking", JSON.stringify(rankings));

        return new Response(JSON.stringify({ success: true }), {
            headers: { "Content-Type": "application/json" },
            status: 200,
        });
    } catch (error) {
        console.error("POST Error:", error);
        return new Response(JSON.stringify({ error: "スコアの保存に失敗しました" }), {
            headers: { "Content-Type": "application/json" },
            status: 500,
        });
    }
};