// Twisty! StoryVault — Telegram control bot + scheduler.
//
// Deploy via the Cloudflare dashboard (Workers & Pages > Create Worker >
// paste this in the online editor > Deploy), then set these as Worker
// secrets (Settings > Variables > "Encrypt" for each):
//   TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GH_DISPATCH_TOKEN,
//   SUPABASE_URL, SUPABASE_SERVICE_KEY, GROQ_API_KEY
//
// GH_DISPATCH_TOKEN needs, on this repo: "Actions: read and write" (to
// dispatch runs and read logs) and "Variables: read and write" (so /model
// and /fix can repoint GROQ_MODEL). Without the Variables scope everything
// else still works — /model and /fix report the missing permission.
//
// GROQ_API_KEY is the same key the workflow uses. It powers /models and
// /fix, which ask Groq directly which models it currently serves.
//
// After deploying, point Telegram at the worker's URL once:
//   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WORKER_URL>"

const REPO = "absailor30/AIVidGen";
const WORKFLOW = "story_render.yml";              // 9:16 Shorts + Reels
const WORKFLOW_LONG = "story_render_long.yml";    // 16:9 10-minute, YouTube only

// Cron expressions that should fire the LONG workflow. Everything else fires
// the short one. Add the matching trigger in the Cloudflare dashboard too —
// listing it here alone does nothing.
const LONG_CRONS = new Set(["30 21 * * *"]);      // 03:00 IST, off-peak

// Preference order when /fix picks a replacement model: bigger/better first,
// filtered against what Groq actually serves at that moment.
const MODEL_PREFERENCE = [
  "llama-3.3-70b-versatile",
  "openai/gpt-oss-120b",
  "moonshotai/kimi-k2-instruct",
  "openai/gpt-oss-20b",
  "llama-3.1-8b-instant",
];

// A dispatch is skipped if a run was already created this recently. Cloudflare
// can invoke scheduled() more than once for the same slot (and a retried
// Telegram webhook delivery can double a /render), which previously produced
// duplicate runs and duplicate "Render triggered" messages.
const DUPLICATE_WINDOW_MS = 10 * 60 * 1000;

export default {
  // Telegram webhook — instant commands.
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

    // Never let an exception escape: an error response makes Telegram retry
    // the same update, which is one way a single command becomes four.
    try {
      await handleCommand(env, (msg.text || "").trim());
    } catch (e) {
      await sendTelegram(env, `Command failed: ${e.message}`);
    }
    return new Response("ok");
  },

  // Cloudflare Cron Triggers — reliable on-time scheduling (GitHub's own cron
  // lags 1-3hrs on free tier). Configure these 4 cron expressions in the
  // Cloudflare dashboard (Worker > Settings > Triggers > Cron Triggers):
  //   0 3 * * *    (08:30 IST)   0 7 * * *   (12:30 IST)
  //   15 11 * * *  (16:45 IST)   0 15 * * *  (20:30 IST)
  async scheduled(event, env, ctx) {
    // Which workflow a slot fires is decided by the cron expression, so the
    // long-form slot cannot accidentally queue a Short (or vice versa).
    const workflow = LONG_CRONS.has(event.cron) ? WORKFLOW_LONG : WORKFLOW;
    // Scheduled renders are silent unless something goes wrong — the video
    // appearing on the channel is the success signal. Only failures ping.
    ctx.waitUntil(triggerRender(env, { announce: false, workflow }));
  },
};

async function handleCommand(env, rawText) {
  // Strip a trailing @BotName, which Telegram appends in group chats.
  const [word, ...rest] = rawText.split(/\s+/);
  const cmd = word.toLowerCase().replace(/@.*$/, "");
  const arg = rest.join(" ").trim();

  switch (cmd) {
    case "/render":
    case "/run":
      return triggerRender(env, { announce: true });
    case "/renderlong":
      return triggerRender(env, { announce: true, workflow: WORKFLOW_LONG });
    case "/status":
      return reportStatus(env);
    case "/logs":
      return reportLogs(env);
    case "/models":
      return listModels(env);
    case "/model":
      return arg ? setModel(env, arg) : showModel(env);
    case "/fix":
      return autoFix(env);
    case "/help":
    case "/start":
      return sendTelegram(env, HELP);
    default:
      if (cmd.startsWith("/")) {
        return sendTelegram(env, `Unknown command ${cmd}.\n\n${HELP}`);
      }
  }
}

const HELP = `Twisty! StoryVault controls

/status  - queue depth, last run, current model
/render  - render and post one Short now
/renderlong - render and post one 10-min long-form video now
/logs    - tail the last run's log
/models  - list the models Groq currently serves
/model   - show the pinned model
/model <name> - pin a specific model
/fix     - diagnose and self-repair a retired model
/help    - this message`;

// --- actions ---------------------------------------------------------------

async function triggerRender(env, { announce, workflow = WORKFLOW }) {
  const label = workflow === WORKFLOW_LONG ? "Long-form render" : "Render";
  // Guard against duplicate invocations (a repeated cron firing, a retried
  // webhook delivery, or an impatient second /render) starting a second run.
  const recent = await recentRun(env, workflow);
  if (recent) {
    const agoMin = Math.round((Date.now() - Date.parse(recent.created_at)) / 60000);
    if (announce) {
      await sendTelegram(
        env,
        `${label} already running: run #${recent.run_number} started ${agoMin}m ago (${recent.status}). Not starting a second one.`
      );
    }
    return;
  }

  const resp = await gh(env, `/actions/workflows/${workflow}/dispatches`, {
    method: "POST",
    body: JSON.stringify({ ref: "main" }),
  });

  if (resp.status === 204) {
    if (announce) {
      await sendTelegram(env, `${label} triggered — should be live on GitHub Actions within a minute.`);
    }
  } else {
    // Always announce a failure to dispatch, scheduled or not.
    await sendTelegram(env, `Failed to trigger ${label.toLowerCase()}: ${resp.status} ${await resp.text()}`);
  }
}

async function reportStatus(env) {
  const [shortQueue, longQueue, shortRun, longRun, model] = await Promise.all([
    queueDepth(env, "short"),
    queueDepth(env, "long"),
    latestRun(env),
    latestRun(env, WORKFLOW_LONG),
    getModel(env).catch((e) => `unreadable (${e.message})`),
  ]);

  const fmt = (run) =>
    run
      ? `#${run.run_number} ${run.status}/${run.conclusion || "-"} at ${run.created_at}`
      : "none found";

  // A green run over an empty queue is the exact shape of the week-long
  // outage: everything reports success while nothing is published.
  const warnings = [];
  if (shortRun && shortRun.conclusion === "success" && shortQueue === 0) {
    warnings.push("short: last run was green but the queue is empty — generation is producing nothing.");
  }
  if (longRun && longRun.conclusion === "success" && longQueue === 0) {
    warnings.push("long: last run was green but the queue is empty — generation is producing nothing.");
  }

  await sendTelegram(
    env,
    `Short (9:16, YT+IG)\n  queue: ${shortQueue} unclaimed\n  last run: ${fmt(shortRun)}\n\n` +
      `Long (16:9, YT only)\n  queue: ${longQueue} unclaimed\n  last run: ${fmt(longRun)}\n\n` +
      `Model: ${model || "(unpinned — using fallback chain)"}` +
      (warnings.length ? `\n\nWarning:\n- ${warnings.join("\n- ")}` : "")
  );
}

async function reportLogs(env) {
  const run = await latestRun(env);
  if (!run) return sendTelegram(env, "No runs found.");

  const jobsResp = await gh(env, `/actions/runs/${run.id}/jobs`);
  const jobs = (await jobsResp.json()).jobs || [];
  if (!jobs.length) return sendTelegram(env, `Run #${run.run_number} has no jobs yet.`);

  // Single-job logs come back as plain text (the whole-run endpoint is a zip,
  // which a Worker cannot usefully unpack).
  const logResp = await gh(env, `/actions/jobs/${jobs[0].id}/logs`);
  if (!logResp.ok) {
    return sendTelegram(env, `Could not read logs: ${logResp.status} (logs expire after ~90 days).`);
  }
  const text = await logResp.text();
  const tail = text.slice(-2500);

  const failed = jobs[0].steps?.filter((s) => s.conclusion === "failure").map((s) => s.name) || [];
  const header =
    `Run #${run.run_number} — ${run.status}/${run.conclusion || "-"}` +
    (failed.length ? `\nFailed steps: ${failed.join(", ")}` : "");

  await sendTelegram(env, `${header}\n\n${tail}`);
}

async function listModels(env) {
  const models = await groqModels(env);
  if (!models.length) return sendTelegram(env, "Groq returned no models.");
  const pinned = await getModel(env).catch(() => null);
  const lines = models.map((m) => (m === pinned ? `* ${m}  <- pinned` : `  ${m}`));
  await sendTelegram(env, `Groq currently serves ${models.length} models:\n\n${lines.join("\n")}`);
}

async function showModel(env) {
  const model = await getModel(env);
  await sendTelegram(
    env,
    model
      ? `Pinned model: ${model}\n\nUse /model <name> to change it, or /models to see what Groq serves.`
      : "No model pinned — the generator walks its built-in fallback chain.\n\nUse /model <name> to pin one."
  );
}

async function setModel(env, name) {
  // Reject a name Groq does not serve, rather than discovering it at 3am.
  const models = await groqModels(env);
  if (models.length && !models.includes(name)) {
    return sendTelegram(
      env,
      `Groq does not serve "${name}". Run /models to see the current list.`
    );
  }
  await putModel(env, name);
  await sendTelegram(env, `Pinned model: ${name}\n\nSend /render to try it now.`);
}

async function autoFix(env) {
  await sendTelegram(env, "Checking...");

  const [queue, models, pinned] = await Promise.all([
    queueDepth(env),
    groqModels(env),
    getModel(env).catch(() => null),
  ]);

  if (!models.length) {
    return sendTelegram(
      env,
      "Groq returned no models — that points at the API key or an outage, not the model name. Check GROQ_API_KEY."
    );
  }

  // The pinned model still exists, so a retired model is not the problem.
  if (pinned && models.includes(pinned)) {
    return sendTelegram(
      env,
      `Model "${pinned}" is still served by Groq, so this is not a retired-model problem.\n` +
        `Queue: ${queue} unclaimed. Check /logs for the real error.`
    );
  }

  const pick = MODEL_PREFERENCE.find((m) => models.includes(m)) || models[0];
  await putModel(env, pick);
  await sendTelegram(
    env,
    (pinned
      ? `Pinned model "${pinned}" is no longer served by Groq.`
      : "No model was pinned.") + `\n\nRepointed to: ${pick}\nTriggering a render to confirm...`
  );
  await triggerRender(env, { announce: true });
}

// --- helpers ---------------------------------------------------------------

function gh(env, path, init = {}) {
  return fetch(`https://api.github.com/repos/${REPO}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`,
      Accept: "application/vnd.github+json",
      "User-Agent": "twisty-storyvault-bot",
      ...(init.headers || {}),
    },
  });
}

async function latestRun(env, workflow = WORKFLOW) {
  const resp = await gh(env, `/actions/workflows/${workflow}/runs?per_page=1`);
  if (!resp.ok) return null;
  return ((await resp.json()).workflow_runs || [])[0] || null;
}

// A run created inside the duplicate window, or still going, whichever applies.
async function recentRun(env, workflow = WORKFLOW) {
  const resp = await gh(env, `/actions/workflows/${workflow}/runs?per_page=5`);
  if (!resp.ok) return null;
  const runs = (await resp.json()).workflow_runs || [];
  return (
    runs.find(
      (r) =>
        r.status !== "completed" ||
        Date.now() - Date.parse(r.created_at) < DUPLICATE_WINDOW_MS
    ) || null
  );
}

async function queueDepth(env, variant = "short") {
  const resp = await fetch(
    `${env.SUPABASE_URL}/rest/v1/story_queue?select=id&claimed_at=is.null&variant=eq.${variant}`,
    {
      headers: {
        apikey: env.SUPABASE_SERVICE_KEY,
        Authorization: `Bearer ${env.SUPABASE_SERVICE_KEY}`,
        Prefer: "count=exact",
      },
    }
  );
  const range = resp.headers.get("content-range");
  const total = range ? parseInt(range.split("/")[1], 10) : NaN;
  return Number.isNaN(total) ? "?" : total;
}

async function groqModels(env) {
  const resp = await fetch("https://api.groq.com/openai/v1/models", {
    headers: { Authorization: `Bearer ${env.GROQ_API_KEY}` },
  });
  if (!resp.ok) return [];
  const data = (await resp.json()).data || [];
  // Whisper/TTS/guard models cannot write stories — keep chat models only.
  return data
    .map((m) => m.id)
    .filter((id) => !/whisper|tts|guard|embed/i.test(id))
    .sort();
}

async function getModel(env) {
  const resp = await gh(env, "/actions/variables/GROQ_MODEL");
  if (resp.status === 404) return null; // not pinned
  if (!resp.ok) throw new Error(`GitHub ${resp.status} reading GROQ_MODEL — token needs "Variables: read"`);
  return (await resp.json()).value;
}

async function putModel(env, value) {
  // Update if it exists, create if it does not.
  let resp = await gh(env, "/actions/variables/GROQ_MODEL", {
    method: "PATCH",
    body: JSON.stringify({ name: "GROQ_MODEL", value }),
  });
  if (resp.status === 404) {
    resp = await gh(env, "/actions/variables", {
      method: "POST",
      body: JSON.stringify({ name: "GROQ_MODEL", value }),
    });
  }
  if (!resp.ok && resp.status !== 204) {
    throw new Error(
      `GitHub ${resp.status} writing GROQ_MODEL — token needs "Variables: read and write"`
    );
  }
}

async function sendTelegram(env, text) {
  // Telegram hard-caps a message at 4096 chars; split rather than lose the tail.
  for (let i = 0; i < text.length; i += 4000) {
    await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chat_id: env.TELEGRAM_CHAT_ID, text: text.slice(i, i + 4000) }),
    });
  }
}
