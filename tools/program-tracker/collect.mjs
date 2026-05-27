// collect.mjs — assemble program_status.json from canonical sources.
// Sources (all read-only; emitters write to gate_status.json):
//   - 00_ARCHITECTURE/CONDUCTOR/modernization/session_queue.yaml
//   - 00_ARCHITECTURE/CONDUCTOR/modernization/PROGRAM_STATE.md
//   - 00_ARCHITECTURE/CONDUCTOR/modernization/CONDUCTOR_LOG.md
//   - 00_ARCHITECTURE/CONDUCTOR/modernization/CONDUCTOR_HALT_LOG.md
//   - tools/program-tracker/.state/gate_status.json   (each gate check writes here)
//   - git (worktree HEADs, recent main commits)
//
// No external npm deps. YAML is parsed by shelling out to python3 -c 'import yaml...'
// using the project .venv (PyYAML 6+ confirmed). If python3/yaml absent, falls back
// to a tiny inline parser that handles this specific queue file shape.

import { execFileSync, spawnSync } from "node:child_process";
import { readFileSync, existsSync, statSync, mkdirSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = resolve(__dirname, "..", "..");
export const TRACKER_DIR = __dirname;
export const STATE_DIR = join(TRACKER_DIR, ".state");
export const GATE_STATUS_PATH = join(STATE_DIR, "gate_status.json");

const QUEUE_PATH = join(REPO_ROOT, "00_ARCHITECTURE/CONDUCTOR/modernization/session_queue.yaml");
const PROGRAM_STATE_PATH = join(REPO_ROOT, "00_ARCHITECTURE/CONDUCTOR/modernization/PROGRAM_STATE.md");
const CONDUCTOR_LOG_PATH = join(REPO_ROOT, "00_ARCHITECTURE/CONDUCTOR/modernization/CONDUCTOR_LOG.md");
const HALT_LOG_PATH = join(REPO_ROOT, "00_ARCHITECTURE/CONDUCTOR/modernization/CONDUCTOR_HALT_LOG.md");

// Plain-language descriptions per unit id. Keeps the UI ledger human-readable
// when an entry doesn't carry its own description. Kept in sync with §3b of the
// 0t brief: "one-line plain-language description of what it delivers."
const UNIT_META = {
  "0t":  { g: "Setup",                              t: "Program tracker",                    d: "The live dashboard — progress, what's done, what's stuck." },
  "0a.0":{ g: "Wave 0a · naming hygiene",           t: "Naming guardrail",                   d: "CI check that enforces consistent names so the cleanup can't drift back." },
  "0a.1":{ g: "Wave 0a · naming hygiene",           t: "Tidy the web addresses",             d: "Rename consume→consult; merge the duplicate panchang URLs into one." },
  "0b.1":{ g: "Wave 0b · close known holes",        t: "Citation check on the new chat",     d: "New adapter chat path enforces sources/citations like the old one did — quality hole closed." },
  "0b.2":{ g: "Wave 0b · close known holes",        t: "Remove leaked passwords",            d: "Strip hardcoded DB passwords from scripts; add a scanner — security hole closed." },
  "0b.3":{ g: "Wave 0b · close known holes",        t: "Retire the Gemini rules",            d: "Delete dead Gemini co-working governance so it stops complicating changes." },
  "1.1": { g: "Wave 1 · the calculation engine",    t: "Engine skeleton",                    d: "Start the in-house Jagannatha-Hora-equivalent calculator + test harness." },
  "1.2": { g: "Wave 1 · the calculation engine",    t: "Prove it matches JH (gate G1)",      d: "Engine reproduces JH exactly for your chart — the foundation. Blocked: needs the JH pin." },
  "2b":  { g: "Wave 2 · rebuild data + multi-user", t: "One tool definition",                d: "Single shared definition for every tool (web + MCP) — no more maintaining everything twice." },
  "2c":  { g: "Wave 2 · rebuild data + multi-user", t: "Multi-user + sharing",               d: "Split owner-vs-subject, add chart sharing, one access-control brain." },
  "2d":  { g: "Wave 2 · rebuild data + multi-user", t: "Command Center",                     d: "Super-admin control panel to flip gates and data sources at runtime." },
  "2a":  { g: "Wave 2 · rebuild data + multi-user", t: "Rebuild your chart data",            d: "Use the engine to regenerate all chart data as pure facts. Blocked: needs G1." },
  "3.dejudge":                  { g: "Wave 3 · converge tools + cut over", t: "Remove hidden scoring",          d: "Strip buried filters/weights from the tools — the model decides, not the tool." },
  "3.gateway_pipeline_isolation":{ g: "Wave 3 · converge tools + cut over", t: "Tool gateway + split pipelines", d: "Build the gateway; cleanly separate the two chat pipelines so each can evolve alone." },
  "3.tool_asset_recon":         { g: "Wave 3 · converge tools + cut over", t: "Tool ↔ asset reconciliation",    d: "Re-map every tool to the NEW data assets — full coverage, no redundancy, no orphans (gate G6).", neu: true },
  "3.cutover":                  { g: "Wave 3 · converge tools + cut over", t: "Switch over to the new data",    d: "Build new alongside old, validate, swap, keep old as a backup. Blocked: needs engine + data." },
  "3.consult_nav":              { g: "Wave 3 · converge tools + cut over", t: "New navigation + pages",         d: "Role-gated nav and the per-chart Profile / Build / Consult / Panchang pages." },
  "3.tier_excision":            { g: "Wave 3 · converge tools + cut over", t: "Remove the old tier system",     d: "Delete audience-tiers and the Deep/Study/Brief selector — access is now role + sharing." },
  "3.legacy_delete":            { g: "Wave 3 · converge tools + cut over", t: "Delete the old chat pipeline",   d: "Remove the legacy single-pass pipeline once the new one is at full parity." },
  "4.scale_and_close":          { g: "Wave 4 · scale, observe, seal",       t: "Scale, observe, seal",           d: "SQL upgrade + Memorystore + CDN/Armor + observability + eval re-baseline + red-team." },
};

// Friendly gate labels for the UI gate-chip strip.
const GATE_UI = ["naming_ci", "jh_oracle_pinned", "G1_jh_parity", "G2_authz_live", "G3_contract", "G4_no_native_lit", "G5b_onfinish", "G6_tool_coverage"];
const GATE_UI_LABEL = {
  naming_ci: "naming_ci", jh_oracle_pinned: "jh_oracle", G1_jh_parity: "G1", G2_authz_live: "G2",
  G3_contract: "G3", G4_no_native_lit: "G4", G5b_onfinish: "G5b", G6_tool_coverage: "G6",
};

const WAVE_BUCKETS = ["0-support", "0a", "0b", "1", "2", "3", "4"];
const WAVE_UI = ["0a", "0b", "1", "2", "3", "4"]; // header strip

// ── helpers ────────────────────────────────────────────────────────────────
function safeReadFile(p) { try { return readFileSync(p, "utf8"); } catch { return ""; } }
function ensureStateDir() { try { mkdirSync(STATE_DIR, { recursive: true }); } catch {} }

function git(args, cwd = REPO_ROOT) {
  try {
    return execFileSync("git", args, { cwd, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] }).trim();
  } catch { return ""; }
}

// Minimal-but-faithful YAML loader for our queue file. Prefers python3+PyYAML
// (deterministic), falls back to an inline parser for the queue shape.
function loadQueue() {
  const raw = safeReadFile(QUEUE_PATH);
  if (!raw) return { units: [], gates: {}, streams: {} };
  // Try python3 with PyYAML (project .venv has it, but any python3 with pyyaml works).
  const candidates = [
    join(REPO_ROOT, ".venv/bin/python3"),
    "python3",
    "python",
  ];
  for (const py of candidates) {
    try {
      const r = spawnSync(py, ["-c", "import yaml, json, sys; print(json.dumps(yaml.safe_load(sys.stdin)))"], {
        input: raw, encoding: "utf8",
      });
      if (r.status === 0 && r.stdout) {
        const parsed = JSON.parse(r.stdout);
        if (parsed && typeof parsed === "object") return normalizeQueue(parsed);
      }
    } catch {}
  }
  return normalizeQueue(parseQueueYAML(raw));
}

function normalizeQueue(q) {
  // PyYAML parses unquoted `1.1` / `1.2` as floats; coerce to string ids
  // and normalize blockedBy entries that may also be float-typed deps.
  const units = (Array.isArray(q.units) ? q.units : []).map(u => {
    const out = { ...u };
    if (out.id != null) out.id = String(out.id);
    if (out.wave != null) out.wave = String(out.wave);
    if (Array.isArray(out.blockedBy)) out.blockedBy = out.blockedBy.map(b => String(b));
    return out;
  });
  return {
    program: q.program || "PLATFORM_MODERNIZATION",
    streams: q.streams || {},
    gates: q.gates || {},
    units,
  };
}

// Tiny YAML fallback parser. Tailored to the queue file's shape: top-level
// scalars, a `streams:` map of objects, a `gates:` map of objects, and a
// `units:` list of objects with simple keys and one-line list/map values.
// Not a general YAML parser — used only when python3/yaml is unavailable.
function parseQueueYAML(raw) {
  const lines = raw.split("\n").map(l => l.replace(/\t/g, "  "));
  const obj = { program: "PLATFORM_MODERNIZATION", streams: {}, gates: {}, units: [] };
  let section = null; // 'streams' | 'gates' | 'units'
  let currentUnit = null;
  for (let i = 0; i < lines.length; i++) {
    const ln = lines[i].replace(/#.*$/, "").trimEnd();
    if (!ln.trim()) continue;
    const indent = ln.match(/^ */)[0].length;
    const body = ln.trim();
    if (indent === 0) {
      const m = body.match(/^([\w-]+):\s*(.*)$/);
      if (m) {
        if (m[1] === "streams" || m[1] === "gates" || m[1] === "units") { section = m[1]; currentUnit = null; }
        else { section = null; obj[m[1]] = stripQuotes(m[2]); }
      }
      continue;
    }
    if (section === "streams" && indent === 2) {
      const m = body.match(/^([A-Z]):\s*\{(.*)\}\s*$/);
      if (m) obj.streams[m[1]] = parseInlineMap(m[2]);
      continue;
    }
    if (section === "gates" && indent === 2) {
      const m = body.match(/^([\w_]+):\s*\{(.*)\}\s*$/);
      if (m) obj.gates[m[1]] = parseInlineMap(m[2]);
      continue;
    }
    if (section === "units") {
      if (indent === 2 && body.startsWith("- id:")) {
        currentUnit = { id: stripQuotes(body.replace(/^- id:\s*/, "")) };
        obj.units.push(currentUnit);
        continue;
      }
      if (currentUnit && indent >= 4) {
        const m = body.match(/^([\w_]+):\s*(.*)$/);
        if (m) {
          const key = m[1];
          let val = m[2];
          if (val.startsWith("[") && val.endsWith("]")) {
            val = val.slice(1, -1).split(",").map(s => stripQuotes(s.trim())).filter(Boolean);
          } else {
            val = stripQuotes(val);
          }
          currentUnit[key] = val;
        }
      }
    }
  }
  return obj;
}

function stripQuotes(s) {
  s = String(s ?? "").trim();
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) return s.slice(1, -1);
  return s;
}

function parseInlineMap(s) {
  const out = {};
  let depth = 0, buf = "", pairs = [];
  for (const ch of s) {
    if (ch === "{" || ch === "[") depth++;
    if (ch === "}" || ch === "]") depth--;
    if (ch === "," && depth === 0) { pairs.push(buf); buf = ""; } else buf += ch;
  }
  if (buf.trim()) pairs.push(buf);
  for (const p of pairs) {
    const idx = p.indexOf(":");
    if (idx < 0) continue;
    const k = p.slice(0, idx).trim();
    const v = p.slice(idx + 1).trim();
    out[k] = stripQuotes(v);
  }
  return out;
}

// gate_status.json schema: { [gate_id]: { status: "green"|"red"|"pending", last_run_iso: "...", note?: "..." } }
function readGateStatus() {
  ensureStateDir();
  if (!existsSync(GATE_STATUS_PATH)) return {};
  try { return JSON.parse(readFileSync(GATE_STATUS_PATH, "utf8")) || {}; } catch { return {}; }
}

function readProgramState() {
  const txt = safeReadFile(PROGRAM_STATE_PATH);
  const out = { current_batch: 1, batch_label: "wave 0 + engine scaffold · 3 streams", last_green: { A: "none", B: "none", C: "none" }, open_halts: [] };
  const batchMatch = txt.match(/Current batch:\*\*\s*Batch\s*(\d+)/i);
  if (batchMatch) out.current_batch = parseInt(batchMatch[1], 10);
  const lastGreen = txt.match(/Last green per stream:\*\*\s*A=([^\s·]+)\s*·\s*B=([^\s·]+)\s*·\s*C=([^\s.]+)/);
  if (lastGreen) out.last_green = { A: lastGreen[1], B: lastGreen[2], C: lastGreen[3] };
  return out;
}

function readHaltLog() {
  const txt = safeReadFile(HALT_LOG_PATH);
  // "## Open halts" → next section ("## ") cuts. Each entry begins with "- ".
  const open = txt.split(/^##\s+Open halts\s*$/m)[1] || "";
  const cut = open.split(/^##\s+/m)[0] || "";
  const lines = cut.split("\n").map(l => l.trim()).filter(l => l.startsWith("-") && !l.toLowerCase().includes("none"));
  return lines.map(l => ({ type: "halt_queue", reason: l.replace(/^[-_*\s]+/, "").trim(), opened_at: null, resolved: false }));
}

function readActivityTail() {
  const txt = safeReadFile(CONDUCTOR_LOG_PATH);
  const events = [];
  // Pull lines that look like timestamped activity, newest first.
  const re = /(\d{1,2}:\d{2}\s*\w+)\s*·\s*(.+)/g;
  let m;
  while ((m = re.exec(txt)) !== null) {
    events.push({ ts: m[1], detail: m[2].replace(/[`*_]/g, "").trim() });
  }
  return events.slice(-12).reverse();
}

function gitHeadSha(branch) { return git(["rev-parse", "--short", branch]); }

function streamHead(stream) {
  // Worktree path convention from execution plan §4 + KICKOFF: ../Madhav<StreamA|B|C>
  const branch = `prog/stream-${stream.toLowerCase()}`;
  return gitHeadSha(branch);
}

function mainHeadSha() { return gitHeadSha("main"); }

function mainCherryPicks(maxN = 20) {
  const log = git(["log", "--oneline", `-n${maxN}`, "main"]);
  if (!log) return [];
  return log.split("\n").map(line => {
    const m = line.match(/^(\S+)\s+(.+)$/);
    return m ? { sha: m[1], subject: m[2] } : null;
  }).filter(Boolean);
}

// ── core assembly ──────────────────────────────────────────────────────────
export async function collect() {
  const queue = loadQueue();
  const gateStatus = readGateStatus();
  const programState = readProgramState();
  const halts = readHaltLog();
  const cherryPicks = mainCherryPicks();

  // Per-unit status resolution.
  const unitStatusById = {};
  for (const u of queue.units) {
    const id = u.id;
    const gs = gateStatus.units && gateStatus.units[id];
    let s = "pending";
    if (gs && gs.status) s = gs.status;
    else if (Array.isArray(u.blockedBy) && u.blockedBy.length > 0) {
      // If any blocking gate is not green → blocked; else eligible.
      const blocked = u.blockedBy.some(dep => {
        if (queue.gates && queue.gates[dep]) {
          const live = (gateStatus.gates && gateStatus.gates[dep]) || queue.gates[dep];
          return (live.status || "PENDING").toUpperCase() !== "GREEN";
        }
        // It's a unit dep: blocked if that unit isn't done/merged.
        const dep_s = unitStatusById[dep];
        return !(dep_s === "done");
      });
      s = blocked ? "blocked" : "eligible";
    } else {
      s = "eligible";
    }
    unitStatusById[id] = s;
  }
  // Overlay 0t state — collect.mjs runs => tracker is up => 0t is "done"
  // unless gate_status.json explicitly says otherwise.
  if (!unitStatusById["0t"] || unitStatusById["0t"] === "pending" || unitStatusById["0t"] === "eligible") {
    unitStatusById["0t"] = "done";
  }

  // Gate strip (UI shape).
  const gates_ui = GATE_UI.map(g => {
    const live = (gateStatus.gates && gateStatus.gates[g]) || (queue.gates && queue.gates[g]) || { status: "PENDING" };
    const status = String(live.status || "PENDING").toLowerCase();
    let s = "pend";
    if (status === "green") s = "green";
    else if (status === "red") s = "red";
    return { id: GATE_UI_LABEL[g], s, last_run: live.last_run_iso || null, note: live.note || null };
  });

  // Stream board (UI shape).
  const streams_ui = ["A", "B", "C"].map(id => {
    const branch = `prog/stream-${id.toLowerCase()}`;
    const head = streamHead(id);
    const currentUnit = (gateStatus.streams && gateStatus.streams[id] && gateStatus.streams[id].current_unit) || "idle";
    const lastGreen = (programState.last_green && programState.last_green[id]) || "none";
    const state = currentUnit === "idle" ? "idle" : (gateStatus.streams && gateStatus.streams[id] && gateStatus.streams[id].state) || "idle";
    return { id, branch, state, unit: currentUnit, last: lastGreen, head_sha: head || null };
  });

  // Units (UI shape).
  const units_ui = queue.units.map(u => {
    const meta = UNIT_META[u.id] || { g: `Wave ${u.wave || "?"}`, t: u.id, d: "" };
    const s = unitStatusById[u.id] || "pending";
    const ui_s = (s === "done" || s === "merged") ? "done"
      : (s === "running" || s === "in_progress") ? "running"
      : (s === "blocked") ? "blocked"
      : (s === "eligible") ? "pending"  // eligible renders as pending circle (not yet started)
      : "pending";
    const out = { id: u.id, wave: u.wave || null, g: meta.g, t: meta.t, d: meta.d, s: ui_s, blockedBy: u.blockedBy || [] };
    if (meta.neu) out.neu = true;
    return out;
  });

  // Attention/blockers strip.
  const attention = [];
  const jhGate = (gateStatus.gates && gateStatus.gates.jh_oracle_pinned) || (queue.gates && queue.gates.jh_oracle_pinned) || {};
  if ((jhGate.status || "RED").toUpperCase() === "RED") {
    attention.push({
      title: "JH-oracle input required",
      detail: "Pin JH version + ayanamsha → platform/python-sidecar/natal_engine/fixtures/jh_oracle.json. Blocks unit 1.2 and gate G1.",
      severity: "blocker",
    });
  }

  // Activity feed (newest first).
  const activityRaw = readActivityTail();
  const activity = activityRaw.map(a => ({ i: "commit", c: "var(--muted)", t: a.detail, ts: a.ts, ago: a.ts }));
  for (const cp of cherryPicks.slice(0, 6)) {
    activity.unshift({ i: "up", c: "var(--blue)", t: cp.subject, sha: cp.sha, ago: "" });
  }

  // Health strip.
  const health = {
    tests: gateStatus.health?.tests || "n/a",
    coverage: gateStatus.health?.coverage || "—",
    smoke: gateStatus.health?.smoke || "n/a",
    error_rate: gateStatus.health?.error_rate || "—",
    prod_revision: gateStatus.health?.prod_revision || "none",
  };

  // Aggregate counts → progress.
  const total = units_ui.length;
  const done = units_ui.filter(x => x.s === "done").length;
  const running = units_ui.filter(x => x.s === "running").length;
  const blocked = units_ui.filter(x => x.s === "blocked").length;
  const pending = total - done - running - blocked;
  const greenGates = gates_ui.filter(g => g.s === "green").length;

  // Final status object — superset of (a) UI MOCK shape and (b) the schema in
  // BRIEF_0t §"program_status.json". The UI consumes only the keys it needs.
  return {
    program: queue.program || "PLATFORM_MODERNIZATION",
    updated_at: new Date().toISOString(),
    batch: programState.current_batch,
    batch_label: programState.batch_label,
    current_batch: programState.current_batch,
    percent_complete: total ? Math.round((done / total) * 100) : 0,
    counts: { total, done, running, blocked, pending, gates_total: gates_ui.length, gates_green: greenGates },
    streams: streams_ui,
    gates: gates_ui,
    units: units_ui,
    attention,
    halts,
    activity,
    health: { ...health, tests_pass: health.tests === "passing" },
    main_head: mainHeadSha(),
    cherry_picks: cherryPicks,
    sources: {
      queue: QUEUE_PATH.replace(REPO_ROOT + "/", ""),
      program_state: PROGRAM_STATE_PATH.replace(REPO_ROOT + "/", ""),
      gate_status: GATE_STATUS_PATH.replace(REPO_ROOT + "/", ""),
      halt_log: HALT_LOG_PATH.replace(REPO_ROOT + "/", ""),
    },
  };
}

// File-modtime fingerprint used by the SSE loop to push on change.
export function sourcesFingerprint() {
  const paths = [QUEUE_PATH, PROGRAM_STATE_PATH, CONDUCTOR_LOG_PATH, HALT_LOG_PATH, GATE_STATUS_PATH];
  return paths.map(p => existsSync(p) ? statSync(p).mtimeMs : 0).join(":");
}
