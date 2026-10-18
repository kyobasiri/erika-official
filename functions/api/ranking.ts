export const onRequestGet: PagesFunction = async (context) => {
    try {
        const env = context.env as { KV_BINDING: KVNamespace }
        const raw = await env.KV_BINDING.get("erika_labyrinth_ranking")
        const ranking = raw ? JSON.parse(raw) : []

        return new Response(JSON.stringify(ranking), {
            headers: { "Content-Type": "application/json" },
        })
    } catch (err: any) {
        return new Response(JSON.stringify({ error: err.message || "Internal Server Error" }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
        })
    }
}

export const onRequestPost: PagesFunction = async (context) => {
    try {
        const env = context.env as { KV_BINDING: KVNamespace }
        const body = await context.request.json() as { name?: string; score?: number; time?: string }

        if (!body || typeof body.score !== 'number') {
            return new Response(JSON.stringify({ error: "Invalid score data" }), {
                status: 400,
                headers: { "Content-Type": "application/json" },
            })
        }

        const raw = await env.KV_BINDING.get("erika_labyrinth_ranking")
        let ranking: Array<{ name: string; score: number; time: string }> = raw ? JSON.parse(raw) : []

        // 新しいスコアを追加してスコア順（高い順）に並び替え、上位50件を保持
        ranking.push({
            name: (body.name || "名無しのエリカ").slice(0, 20),
            score: body.score,
            time: body.time || new Date().toISOString()
        })

        ranking.sort((a, b) => b.score - a.score)
        ranking = ranking.slice(0, 50)

        await env.KV_BINDING.put("erika_labyrinth_ranking", JSON.stringify(ranking))

        return new Response(JSON.stringify({ success: true, ranking }), {
            headers: { "Content-Type": "application/json" },
        })
    } catch (err: any) {
        return new Response(JSON.stringify({ error: err.message || "Internal Server Error" }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
        })
    }
}