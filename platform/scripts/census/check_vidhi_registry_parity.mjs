#!/usr/bin/env node
/**
 * check_vidhi_registry_parity.mjs — PARIŚODHANA B2 (Ω8 floor-wiring) anti-drift CI gate.
 * ================================================================================
 * The Vidhi registry has FOUR process-boundary copies of the same data:
 *   1. canonical TS      platform/src/lib/vidhi/registry_data.ts       (compiler reads this)
 *   2. generated mirror  platform-mcp/src/resources/vidhi/registry_data.ts   (codegen:vidhi — its
 *      own parity gate: vidhi_codegen_parity.test.ts — NOT re-checked here)
 *   3a. DB seed SQL      platform/migrations/462 + 466                  (what actually seeds prod)
 *   3b. DB seed Python   bg_vidhi_primitives.py / bg_vidhi_floors.py    (orchestrator seed writers)
 *
 * Copy 3b silently drifted to 37 primitives / 8 floors before B2 (a latent regression bomb: if the
 * orchestrator re-ran the writers they would overwrite the migration-462 seed and regress the live
 * registry). This gate keeps the canonical TS (1) and the Python DB-seed writers (3b) in lockstep,
 * so the bomb can never re-arm silently.
 *
 * ASSERTIONS (exit non-zero + printed diff on any failure):
 *   1. TS ↔ Python deep equality — the canonical TS dump (dump_vidhi_registry.ts) equals the union
 *      of the two Python writers' `--dump-json` output, normalized (recursive key-sort).
 *   2. TS ↔ Ω8-regen coverage — every floor_varga and every required family/primitive in
 *      REGENERATED_FLOORS_v1_0.json is present in the corresponding TS domain floor.
 *   3. The existing floor-coverage gate still passes (check_floor_coverage.mjs → 14/14, exit 0).
 *      Skippable in the unit test via VIDHI_PARITY_SKIP_COVERAGE=1.
 *
 * TESTABILITY (induced-drift test, vidhi_parity_gate.test.ts): the three dump sources and the regen
 * file can be pointed at fixture files via env, so a test can feed a mutated dump and assert exit 1:
 *   VIDHI_TS_DUMP_FILE / VIDHI_PY_PRIMS_FILE / VIDHI_PY_FLOORS_FILE / VIDHI_REGEN_FILE (file paths;
 *   when unset the gate shells the real dumps), and VIDHI_PARITY_SKIP_COVERAGE=1.
 *
 * USAGE: node platform/scripts/census/check_vidhi_registry_parity.mjs   (run from repo root or platform/)
 */
import { execFileSync } from 'node:child_process'
import { readFileSync, existsSync } from 'node:fs'
import { resolve, dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const PLATFORM = resolve(__dirname, '../..') // platform/
const REPO = resolve(PLATFORM, '..')
const SIDECAR = join(PLATFORM, 'python-sidecar')
const CAP_MAP = join(REPO, '00_ARCHITECTURE/llm_consumption_audit/capability_map')
const PY = process.env.PYTHON_BIN || 'python3'
const EXEC_OPTS = { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 }

/** Recursive object-key sort → a stable byte form for deep comparison independent of key order. */
function canon(v) {
  if (Array.isArray(v)) return v.map(canon)
  if (v && typeof v === 'object') {
    const o = {}
    for (const k of Object.keys(v).sort()) o[k] = canon(v[k])
    return o
  }
  return v
}
const eq = (a, b) => JSON.stringify(canon(a)) === JSON.stringify(canon(b))

function readOrShell(envVar, shellFn) {
  const f = process.env[envVar]
  if (f) {
    if (!existsSync(f)) throw new Error(`${envVar} points at a missing file: ${f}`)
    return JSON.parse(readFileSync(f, 'utf8'))
  }
  return shellFn()
}

const failures = []

// ── source dumps ────────────────────────────────────────────────────────────
const tsDump = readOrShell('VIDHI_TS_DUMP_FILE', () =>
  JSON.parse(execFileSync('npx', ['tsx', 'scripts/census/dump_vidhi_registry.ts'], { cwd: PLATFORM, ...EXEC_OPTS })))
const pyPrims = readOrShell('VIDHI_PY_PRIMS_FILE', () =>
  JSON.parse(execFileSync(PY, ['pipeline/orchestrator/writers/bg_vidhi_primitives.py', '--dump-json'], { cwd: SIDECAR, ...EXEC_OPTS })))
const pyFloors = readOrShell('VIDHI_PY_FLOORS_FILE', () =>
  JSON.parse(execFileSync(PY, ['pipeline/orchestrator/writers/bg_vidhi_floors.py', '--dump-json'], { cwd: SIDECAR, ...EXEC_OPTS })))

// ── ASSERTION 1: TS ↔ Python deep equality ─────────────────────────────────
{
  const tsP = tsDump.primitives ?? []
  const pyP = pyPrims.primitives ?? []
  if (tsP.length !== pyP.length) {
    failures.push(`[1] primitive COUNT differs: TS=${tsP.length} Python=${pyP.length}`)
  }
  const pyById = new Map(pyP.map((p) => [p.primitive_id, p]))
  for (const t of tsP) {
    const p = pyById.get(t.primitive_id)
    if (!p) { failures.push(`[1] primitive "${t.primitive_id}" present in TS, MISSING in Python`); continue }
    if (!eq(t, p)) failures.push(`[1] primitive "${t.primitive_id}" DIFFERS TS↔Python\n    TS: ${JSON.stringify(canon(t))}\n    PY: ${JSON.stringify(canon(p))}`)
  }
  for (const p of pyP) if (!tsP.find((t) => t.primitive_id === p.primitive_id)) failures.push(`[1] primitive "${p.primitive_id}" present in Python, MISSING in TS`)

  const tsF = tsDump.floors ?? []
  const pyF = pyFloors.floors ?? []
  if (tsF.length !== pyF.length) failures.push(`[1] floor COUNT differs: TS=${tsF.length} Python=${pyF.length}`)
  const pyByIntent = new Map(pyF.map((f) => [f.intent, f]))
  for (const t of tsF) {
    const f = pyByIntent.get(t.intent)
    if (!f) { failures.push(`[1] floor "${t.intent}" present in TS, MISSING in Python`); continue }
    if (!eq(t, f)) {
      // narrow to the first differing item for a readable diff
      let detail = ''
      const ti = t.floor_items ?? [], fi = f.floor_items ?? []
      if (ti.length !== fi.length) detail = ` (item count TS=${ti.length} PY=${fi.length})`
      else for (let j = 0; j < ti.length; j++) if (!eq(ti[j], fi[j])) { detail = `\n    TS item: ${JSON.stringify(canon(ti[j]))}\n    PY item: ${JSON.stringify(canon(fi[j]))}`; break }
      failures.push(`[1] floor "${t.intent}" DIFFERS TS↔Python${detail}`)
    }
  }
  for (const f of pyF) if (!tsF.find((t) => t.intent === f.intent)) failures.push(`[1] floor "${f.intent}" present in Python, MISSING in TS`)
}

// ── ASSERTION 2: TS ↔ Ω8-regen coverage ─────────────────────────────────────
{
  const regenPath = process.env.VIDHI_REGEN_FILE || join(CAP_MAP, 'REGENERATED_FLOORS_v1_0.json')
  const regen = JSON.parse(readFileSync(regenPath, 'utf8'))
  // JSON floor_tool → TS primitive_id (identity except the ayanamsha rename).
  const TOOL_TO_PRIMITIVE = { cross_ayanamsha_agreement: 'cross_ayanamsha_variation' }
  const mapTool = (t) => TOOL_TO_PRIMITIVE[t] ?? t
  const tsFloorByIntent = new Map((tsDump.floors ?? []).map((f) => [f.intent, f]))

  for (const dom of regen.domains ?? []) {
    const intent = dom.intent || `${dom.domain}_deepdive`
    const floor = tsFloorByIntent.get(intent)
    if (!floor) { failures.push(`[2] regen domain "${dom.domain}" has no TS floor "${intent}"`); continue }
    const items = floor.floor_items ?? []
    const primitiveIds = new Set(items.map((i) => i.primitive_id))
    const divisionalVargas = new Set(items.filter((i) => i.primitive_id === 'divisional_facts').map((i) => (i.args_override || {}).varga))

    for (const varga of dom.floor_vargas ?? []) {
      if (!divisionalVargas.has(varga)) failures.push(`[2] floor "${intent}" MISSING divisional_facts for floor_varga ${varga}`)
    }
    for (const fi of dom.floor_items ?? []) {
      if (fi.floor_tool === 'divisional_facts') continue // covered by the floor_vargas check
      const prim = mapTool(fi.floor_tool)
      if (!primitiveIds.has(prim)) failures.push(`[2] floor "${intent}" MISSING required family/primitive "${prim}" (regen floor_tool "${fi.floor_tool}")`)
    }
  }
}

// ── ASSERTION 3: the existing floor-coverage gate still passes (14/14) ────────
if (process.env.VIDHI_PARITY_SKIP_COVERAGE !== '1') {
  try {
    execFileSync('node', ['scripts/census/check_floor_coverage.mjs'], { cwd: PLATFORM, stdio: 'inherit' })
  } catch {
    failures.push('[3] floor-coverage gate (check_floor_coverage.mjs) did NOT pass — see its output above')
  }
}

// ── report ──────────────────────────────────────────────────────────────────
if (failures.length > 0) {
  console.error('\nVIDHI REGISTRY PARITY GATE: FAIL\n')
  for (const f of failures) console.error('  ✗ ' + f)
  console.error(`\n${failures.length} failure(s). The four Vidhi registry copies have drifted — ` +
    `re-run the codegen + re-generate the Python seed literals from platform/src/lib/vidhi/registry_data.ts ` +
    `(and migration 462/466) so all copies match, then re-run this gate.`)
  process.exit(1)
}
console.log('VIDHI REGISTRY PARITY GATE: PASS — canonical TS ↔ Python seed writers ↔ Ω8-regen coverage all in lockstep.')
process.exit(0)
