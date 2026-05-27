#!/usr/bin/env node
// emit_gate.mjs — atomic writer for tracker/.state/gate_status.json.
// Sub-agents use this to flip a gate or a unit; tracker SSE pushes within ~2s.
//
// Examples:
//   node tools/program-tracker/emit_gate.mjs gate naming_ci GREEN
//   node tools/program-tracker/emit_gate.mjs unit 0a.0 done a1b2c3d
//   node tools/program-tracker/emit_gate.mjs stream A running 0a.0
//   node tools/program-tracker/emit_gate.mjs health prod_revision amjis-web-00425-abc

import { readFileSync, writeFileSync, existsSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const STATE_DIR = join(__dirname, ".state");
const FILE = join(STATE_DIR, "gate_status.json");

function load() {
  if (!existsSync(STATE_DIR)) mkdirSync(STATE_DIR, { recursive: true });
  if (!existsSync(FILE)) return { gates: {}, units: {}, streams: {}, health: {} };
  try { return JSON.parse(readFileSync(FILE, "utf8")) || { gates:{},units:{},streams:{},health:{} }; }
  catch { return { gates:{},units:{},streams:{},health:{} }; }
}

function save(obj) {
  obj.updated_at_iso = new Date().toISOString();
  writeFileSync(FILE, JSON.stringify(obj, null, 2) + "\n");
}

const [, , kind, key, ...rest] = process.argv;
if (!kind || !key) {
  console.error("usage: emit_gate.mjs <gate|unit|stream|health> <key> <args...>");
  process.exit(2);
}
const state = load();
const now = new Date().toISOString();

switch (kind) {
  case "gate": {
    const status = (rest[0] || "PENDING").toUpperCase();
    const note = rest.slice(1).join(" ") || null;
    state.gates[key] = { status, last_run_iso: now, note: note || (state.gates[key]?.note ?? null) };
    break;
  }
  case "unit": {
    const status = (rest[0] || "pending").toLowerCase();
    const sha = rest[1] || null;
    const prev = state.units[key] || {};
    state.units[key] = { ...prev, status, merged_to_main: status === "done" ? true : (prev.merged_to_main ?? false), commit_sha: sha || prev.commit_sha || null, updated_at_iso: now };
    break;
  }
  case "stream": {
    const status = rest[0] || "idle";
    const unit = rest[1] || "idle";
    state.streams[key] = { state: status, current_unit: unit, updated_at_iso: now };
    break;
  }
  case "health": {
    state.health = { ...(state.health || {}), [key]: rest.join(" ") };
    break;
  }
  default:
    console.error(`unknown kind: ${kind}`);
    process.exit(2);
}
save(state);
console.log(`emitted ${kind} ${key} = ${JSON.stringify(rest)}`);
