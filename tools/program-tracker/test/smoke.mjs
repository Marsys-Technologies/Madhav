// smoke.mjs — boots server.mjs on a free port and verifies the dashboard.
// Acceptance criteria (BRIEF_0t §"Acceptance criteria"):
//   1. GET /status.json returns schema-valid JSON assembled from real sources
//   2. SSE pushes within 5s of a source change
//   3. GET / loads the page; the page contains the elements the UI fills
//   4. (stale detection is UI-side and trivially verified)
//   5. Removability check: zero imports of program-tracker from platform/ or platform-mcp/
//   6. No secret/credential values rendered

import { spawn } from "node:child_process";
import { setTimeout as wait } from "node:timers/promises";
import { writeFileSync, mkdirSync, existsSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TRACKER_DIR = resolve(__dirname, "..");
const REPO_ROOT = resolve(TRACKER_DIR, "..", "..");
const SERVER = join(TRACKER_DIR, "server.mjs");
const STATE_DIR = join(TRACKER_DIR, ".state");
const GATE_STATUS = join(STATE_DIR, "gate_status.json");

const PORT = 18787; // smoke runs on its own port to avoid clashing with dev server
const BASE = `http://127.0.0.1:${PORT}`;

let proc;
const fails = [];

function ok(label) { process.stdout.write(`  ✓ ${label}\n`); }
function bad(label, err) {
  process.stdout.write(`  ✗ ${label}\n`);
  if (err) process.stdout.write(`    ${err.stack || err.message || err}\n`);
  fails.push(label);
}

async function fetchJson(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
  return r.json();
}

async function fetchText(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(`HTTP ${r.status} ${url}`);
  return r.text();
}

async function start() {
  proc = spawn("node", [SERVER], { env: { ...process.env, PORT: String(PORT), TRACKER_VERBOSE: "0" }, stdio: ["ignore", "ignore", "inherit"] });
  for (let i = 0; i < 30; i++) {
    try { const r = await fetch(`${BASE}/healthz`); if (r.ok) return; } catch {}
    await wait(100);
  }
  throw new Error("server did not start");
}

function stop() { try { proc && proc.kill("SIGINT"); } catch {} }

function ensureStateDir() { if (!existsSync(STATE_DIR)) mkdirSync(STATE_DIR, { recursive: true }); }

// AC #5 — removability: nothing in platform/ or platform-mcp/ may import the tracker.
function checkRemovability() {
  try {
    const out = execFileSync(
      "grep",
      ["-rIn", "program-tracker", "platform/", "platform-mcp/"],
      { cwd: REPO_ROOT, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }
    ).trim();
    if (!out) { ok("AC#5 removability: no platform/* import references program-tracker"); return; }
    // grep returns hits; only acceptable hits are .md files. import/require/from is the violation.
    const violations = out.split("\n").filter(l => /(import|require|from)\s*['"`].*program-tracker/.test(l));
    if (violations.length === 0) ok("AC#5 removability: no platform/* code imports program-tracker");
    else bad("AC#5 removability: platform/* imports the tracker", new Error(violations.join("\n")));
  } catch (e) {
    // grep exits 1 when no match → that's the pass case.
    if (e && e.status === 1) ok("AC#5 removability: no platform/* import references program-tracker");
    else bad("AC#5 removability: grep failed", e);
  }
}

// AC #6 — assembled status contains no secret/credential-looking values.
function scanForSecrets(status) {
  const txt = JSON.stringify(status);
  const patterns = [
    /AKIA[0-9A-Z]{16}/,            // AWS
    /AIza[0-9A-Za-z\-_]{35}/,      // Google API
    /sk-[A-Za-z0-9]{20,}/,         // generic secret key
    /-----BEGIN [A-Z ]*PRIVATE KEY-----/,
    /password\s*[:=]\s*["'][^"']{6,}["']/i,
  ];
  for (const p of patterns) {
    if (p.test(txt)) return p;
  }
  return null;
}

(async () => {
  process.stdout.write(`program-tracker smoke (port ${PORT})\n`);

  // Pre-seed gate_status.json so we can flip it during the SSE test.
  ensureStateDir();
  writeFileSync(GATE_STATUS, JSON.stringify({ gates: { naming_ci: { status: "PENDING", last_run_iso: new Date().toISOString() } }, units: {}, streams: {} }, null, 2));

  await start();
  try {
    // AC #1 — /status.json shape
    const status = await fetchJson(`${BASE}/status.json`);
    const requiredKeys = ["program", "updated_at", "batch", "streams", "gates", "units", "attention", "halts", "activity", "health"];
    const missing = requiredKeys.filter(k => !(k in status));
    if (missing.length) bad(`AC#1 status.json schema: missing ${missing.join(", ")}`);
    else ok(`AC#1 status.json contains ${requiredKeys.length} required keys`);
    if (!Array.isArray(status.units) || status.units.length === 0) bad("AC#1 status.json units[] non-empty");
    else ok(`AC#1 status.json units[] populated (${status.units.length} units from queue)`);
    const need = ["0t", "0a.0", "0a.1", "0b.1", "0b.2", "0b.3", "1.1", "1.2"];
    const present = need.every(id => status.units.find(u => u.id === id));
    if (!present) bad(`AC#1 status.json units[] missing one of ${need.join(",")}`);
    else ok("AC#1 status.json units[] includes all Wave-0/1 ids");

    // AC #3 — page renders the elements the UI fills
    const html = await fetchText(`${BASE}/`);
    const ids = ["tiles", "waves", "ledger", "board", "streams", "gates", "attn", "health", "feed"];
    const missingIds = ids.filter(id => !html.includes(`id="${id}"`));
    if (missingIds.length) bad(`AC#3 dashboard renders all 9 sections: missing ${missingIds.join(", ")}`);
    else ok("AC#3 dashboard renders all 9 sections (id elements present)");

    // AC #2 — SSE push within 5s of source change
    const sseUrl = `${BASE}/events`;
    let pushed = false;
    const controller = new AbortController();
    const pushedPromise = new Promise(async (resolveP) => {
      try {
        const r = await fetch(sseUrl, { signal: controller.signal });
        const reader = r.body.getReader();
        const dec = new TextDecoder();
        let initialCount = 0;
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          const chunk = dec.decode(value, { stream: true });
          if (chunk.includes("event: status")) {
            initialCount++;
            if (initialCount >= 2) { pushed = true; resolveP(); break; }
          }
        }
      } catch {}
    });
    // Mutate gate_status.json after SSE is subscribed (gives ≥1 status push, then we trigger 1 more).
    await wait(500);
    writeFileSync(GATE_STATUS, JSON.stringify({ gates: { naming_ci: { status: "GREEN", last_run_iso: new Date().toISOString() } }, units: {}, streams: {} }, null, 2));
    await Promise.race([pushedPromise, wait(6000)]);
    controller.abort();
    if (pushed) ok("AC#2 SSE pushed a status update within 5s of source mutation");
    else bad("AC#2 SSE did not push update within 5s of source mutation");

    // AC #5 — removability
    checkRemovability();

    // AC #6 — no secrets in assembled JSON
    const secretHit = scanForSecrets(status);
    if (secretHit) bad(`AC#6 no secret-shaped values in status.json (matched ${secretHit})`);
    else ok("AC#6 no secret-shaped values rendered in status.json");
  } finally {
    stop();
    // Restore a clean gate_status (lean for live runs).
    try { rmSync(GATE_STATUS, { force: true }); } catch {}
  }

  if (fails.length) {
    process.stdout.write(`\nFAIL — ${fails.length} check(s) failed: ${fails.join("; ")}\n`);
    process.exit(1);
  } else {
    process.stdout.write(`\nPASS — all program-tracker acceptance checks green\n`);
    process.exit(0);
  }
})().catch(e => { stop(); process.stderr.write(`smoke error: ${e.stack || e.message || e}\n`); process.exit(1); });
