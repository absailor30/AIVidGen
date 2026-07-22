// Twisty! StoryVault — Telegram webhook bot.
//
// Deploy via the Cloudflare dashboard (Workers & Pages > Create Worker >
// paste this in the online editor > Deploy), then set these as Worker
// secrets (Settings > Variables > "Encrypt" for each):
//   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GH_DISPATCH_TOKEN,
//   SUPABASE_URL, SUPABASE_SERVICE_KEY
//
// After deploying, point Telegram at the worker's URL once:
//   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WORKER_URL>"

const REPO = "absailor30/AIVidGen";

export default {
  async fetch(request, env) {
    if (request.method !== "POST") return new Response("ok");

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("ok");
    }

    const msg = update.message;
    if (!msg || String(msg.chat?.id) !== env.TELEGRAM_CHAT_ID) {
      return new Response("ok");
    }

    const text = (msg.text || "").trim().toLowerCase();
    if (text === "/render" || text === "/run") {
      await triggerRender(env);
    } else if (text === "/status") {
      await reportStatus(env);
    }
    return new Response("ok");
  },
};

async function triggerRender(env) {
  const resp = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/story_render.yml/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`,
        Accept: "application/vnd.github+json",
        "User-Agent": "twisty-storyvault-bot",
      },
      body: JSON.stringify({ ref: "main" }),
    }
  );
  await sendTelegram(
    env,
    resp.status === 204
      ? "Render triggered — should be live on GitHub Actions within a minute."
      : `Failed to trigger render: ${resp.status} ${await resp.text()}`
  );
}

async function reportStatus(env) {
  const countResp = await fetch(
    `${env.SUPABASE_URL}/rest/v1/story_queue?select=id&claimed_at=is.null`,
    {
      headers: {
        apikey: env.SUPABASE_SERVICE_KEY,
        Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
        Prefer: "count=exact",
      },
    }
  );
  const contentRange = countResp.headers.get("content-range");
  const total = contentRange ? contentRange.split("/")[1] : "?";

  const runsResp = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/story_render.yml/runs?per_page=1`,
    {
      headers: {
        Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`,
        "User-Agent": "twisty-storyvault-bot",
      },
    }
  );
  const runs = (await runsResp.json()).workflow_runs || [];
  const last = runs[0]
    ? `${runs[0].status}/${runs[0].conclusion} at ${runs[0].created_at}`
    : "unknown";

  await sendTelegram(env, `Queue: ${total} unclaimed.\nLast render run: ${last}`);
}

async function sendTelegram(env, text) {
  await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text }),
  });
}
