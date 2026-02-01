// functions/api/status.js
export async function onRequest(context) {
    // ステップ2で設定した変数名「KV_DATA」を使用
    const status = await context.env.KV_DATA.get("status");

    return new Response(JSON.stringify({ status: status || "OFFLINE" }), {
        headers: { "Content-Type": "application/json" }
    });
}