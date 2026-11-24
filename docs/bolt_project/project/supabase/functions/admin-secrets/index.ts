const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { status: 200, headers: corsHeaders });
  try {
    const adminKey = req.headers.get("authorization")?.replace("Bearer ", "") ?? "";
    const expected = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
    if (!expected || adminKey !== expected) {
      return new Response(JSON.stringify({ error: "UNAUTHORIZED" }), { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } });
    }
    const body = await req.json().catch(() => ({}));
    const model = typeof body?.gemini_model === "string" ? body.gemini_model.trim() : "";
    if (!model || model.length > 80) {
      return new Response(JSON.stringify({ error: "BAD_REQUEST", detail: "gemini_model (string <=80 chars) required" }), { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } });
    }
    const resp = await fetch(`${Deno.env.get("SUPABASE_URL")}/functions/v1/secrets`, {
      method: "PATCH",
      headers: {
        Authorization: `Bearer ${Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ name: "GEMINI_MODEL", value: model }),
    });
    const ok = resp.ok;
    const text = await resp.text().catch(() => "");
    return new Response(JSON.stringify({ ok, status: resp.status, detail: ok ? "GEMINI_MODEL updated" : text.slice(0, 200) }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: "INTERNAL", detail: String(e).slice(0, 200) }), { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } });
  }
});
