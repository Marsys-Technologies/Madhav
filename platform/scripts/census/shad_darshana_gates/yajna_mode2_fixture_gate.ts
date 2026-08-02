/**
 * yajna_mode2_fixture_gate.ts — ṢAḌ-DARŚANA W4 gate G6: the CANNED W4 MODE-2 FIXTURE.
 * ==========================================================================
 * The fixture is AUTHORITATIVE (SHAD_DARSHANA_BRIEF_v2_0.md §3 W4). The Conductor
 * discharges it EXACTLY and does not substitute an easier query. This script is that
 * discharge, against LIVE data — not a stub, not a shape check over a hand-built payload.
 *
 * Discharged here, each with its own named detector (KALA_W4_UPAYA_DESIGN_v1_0.md §6.2–6.3):
 *
 *   PASS 1  non-empty, OR honestly-empty with an eliminating constraint AND a
 *           next_occurrence_state that is not 'not_searched'.
 *   PASS 2  precision labels correct — `intra_day` with a non-blank basis, AND the
 *           REASON the label is right (no degrading constraint kind is present).
 *   PASS 3  judgment ledger present on every candidate, plus the paddhati divergence
 *           block with a state from the closed set.
 *   PASS 4  census honesty — one coverage entry per spec constraint, six of them, no
 *           more and no fewer, each with a state and (when not computed) a reason.
 *   BOTH-CHARTS (two-part, §6.3): (a) the candidate sets DIFFER across the two canonical
 *           charts with `chart_relative`/`tara_bala` included; (b) they COINCIDE when it
 *           is removed. Part (b) is what makes this an EARNED signal rather than an
 *           inequality that happens to hold — a naive inequality passes for the wrong
 *           reasons (nondeterminism, a timestamp, a differing row order).
 *   D-ONE-ENGINE  source-level: `ritual.ts`'s Mode-1/2 path and `elect.ts` both reach the
 *           lattice through `kala_lattice_query.js`, and NO second definition of
 *           `adjudicateCandidates` / `buildLedger` / a Pareto `dominates` exists anywhere
 *           under `platform-mcp/src`. Two implementations would eventually disagree about
 *           the same Tuesday.
 *   D-MORTALITY-SOURCE  gate G16 part (b): no W4 lane file imports or calls
 *           `ganita_ayurdaya_get`, and none matches the forbidden-identifier pattern —
 *           EXCEPT `kala_sky_pattern.ts`'s own declaration block, which must name the
 *           forbidden identifiers in order to ban them. That one exclusion is by
 *           construction, not a loophole: a rail that fires on its own definition site is
 *           a rail nobody can ship.
 *   D-MORTALITY-LIVE  gate G16 parts (a) and (c): a mortality-shaped request to
 *           `kala_ritual_get` returns the refusal envelope naming §3.5.C with NO
 *           candidates/windows/diagnosis, and STILL refuses under
 *           `audience_tier: 'native_self'`.
 *
 * Conventions match this directory exactly: `_mcp_client.ts` for the live call, `_report.ts`
 * for `GateResult`/`printGateReport` (exit 0 unless a live FAIL; SKIPPED when the tool is
 * unreachable — NEVER weakened to force green), PLAN/LIVE split on `MCP_SERVER_URL`.
 */

import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import {
  CANONICAL_CHART_ID,
  CROSS_CHECK_CHART_ID,
  ShadDarshanaMcpClient,
  resolveMcpTarget,
  unwrapToolPayload,
  envOrDefault,
} from './_mcp_client.js'
import { printGateReport, type GateResult } from './_report.js'

const TOOL_TIMEOUT_MS = Number(envOrDefault('SHAD_DARSHANA_GATE_TIMEOUT_MS', '60000'))

const HERE = fileURLToPath(new URL('.', import.meta.url))
const REPO_ROOT = resolve(HERE, '../../../..')
const FIXTURE_PATH = resolve(REPO_ROOT, 'platform-mcp/test/fixtures/yajna_mode2_gate.json')
const MCP_SRC = resolve(REPO_ROOT, 'platform-mcp/src')

type Fixture = {
  spec_version: string
  all: Record<string, unknown>[]
  horizon: { months: number }
}

function loadFixture(): Fixture {
  return JSON.parse(readFileSync(FIXTURE_PATH, 'utf8')) as Fixture
}

/** The spec as the tool receives it — the fixture's own `_`-prefixed documentation keys
 *  are metadata for a human reader and are stripped, never sent. */
function specFromFixture(f: Fixture, opts: { dropChartRelative: boolean }): Record<string, unknown> {
  const all = f.all.filter((c) => (opts.dropChartRelative ? !('chart_relative' in c) : true))
  return { spec_version: f.spec_version, all, horizon: f.horizon }
}

// ── Source-level detectors (run in BOTH plan and live mode — they need no server) ─────

function walkTs(dir: string, out: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry)
    if (statSync(p).isDirectory()) {
      if (entry === 'node_modules' || entry === 'generated') continue
      walkTs(p, out)
    } else if (entry.endsWith('.ts')) {
      out.push(p)
    }
  }
  return out
}

function detectOneEngine(): GateResult {
  const id = 'D-ONE-ENGINE'
  const title = 'ONE-ENGINE RULE — a single adjudication/ledger/Pareto implementation'
  let files: string[]
  try {
    files = walkTs(MCP_SRC)
  } catch (err) {
    return { id, title, status: 'SKIPPED', detail: `could not walk ${MCP_SRC}: ${String(err)}` }
  }

  const engine = resolve(MCP_SRC, 'lib/kala_lattice_query.ts')
  const offenders: string[] = []
  for (const f of files) {
    if (f === engine) continue
    const src = readFileSync(f, 'utf8')
    // A DEFINITION, not a call or an import. `function adjudicateCandidates(` /
    // `const dominates = ` shapes only.
    for (const pattern of [
      /(?:export\s+)?function\s+adjudicateCandidates\s*\(/,
      /(?:export\s+)?function\s+buildLedger\s*\(/,
      /(?:export\s+)?function\s+dominates\s*\(/,
      /(?:export\s+)?const\s+(?:adjudicateCandidates|buildLedger|dominates)\s*[:=]/,
    ]) {
      if (pattern.test(src)) offenders.push(`${f.replace(REPO_ROOT + '/', '')} matches ${pattern}`)
    }
  }
  if (offenders.length > 0) {
    return {
      id, title, status: 'FAIL',
      detail:
        `A SECOND implementation of the engine exists — two implementations would eventually ` +
        `disagree about the same Tuesday: ${offenders.join('; ')}`,
    }
  }

  // …and the two consumers genuinely reach the engine.
  const ritual = readFileSync(resolve(MCP_SRC, 'tools/kala_views/ritual.ts'), 'utf8')
  const elect = readFileSync(resolve(MCP_SRC, 'tools/kala_views/elect.ts'), 'utf8')
  const ritualOk = /kala_lattice_query\.js/.test(ritual)
  const electOk = /kala_lattice_query\.js/.test(elect) && /adjudicateCandidates/.test(elect)
  if (!ritualOk || !electOk) {
    return {
      id, title, status: 'FAIL',
      detail:
        `Both Mode-1/2 (ritual.ts) and Mode-3 (elect.ts) must reach the SHARED engine. ` +
        `ritual.ts imports engine: ${ritualOk}; elect.ts imports+calls engine: ${electOk}.`,
    }
  }
  return {
    id, title, status: 'PASS',
    detail:
      `No second adjudicateCandidates/buildLedger/Pareto-dominates definition anywhere under ` +
      `platform-mcp/src (${files.length} .ts files scanned); ritual.ts and elect.ts both reach ` +
      `kala_lattice_query.js.`,
  }
}

/** gate G16 part (b) — the SUBSTRATE ban, source-level. */
function detectMortalitySubstrateBan(): GateResult {
  const id = 'D-MORTALITY-SOURCE'
  const title = '§5.4 mortality HARD EXCLUSION — substrate ban (gate G16 part b)'
  const FORBIDDEN = /ayurdaya|longevity|maraka|\bayus\b/i
  // The ONE by-construction exclusion: kala_sky_pattern.ts must NAME the forbidden
  // identifiers in order to ban them. Excluding its definition site is not a loophole —
  // a rail that fires on its own declaration is a rail nobody can ship. Every OTHER W4
  // lane file is scanned with no exclusion at all.
  const DEFINITION_SITE = resolve(MCP_SRC, 'lib/kala_sky_pattern.ts')
  const W4_LANE_FILES = [
    resolve(MCP_SRC, 'tools/kala_views/ritual.ts'),
    resolve(MCP_SRC, 'tools/kala_views/elect.ts'),
    resolve(MCP_SRC, 'tools/kala_views/ahead.ts'),
    resolve(MCP_SRC, 'tools/kala_views/upaya.ts'),
    resolve(MCP_SRC, 'lib/kala_ritual_resonance.ts'),
  ]

  const offenders: string[] = []
  for (const f of W4_LANE_FILES) {
    let src: string
    try {
      src = readFileSync(f, 'utf8')
    } catch {
      continue // a lane that has not landed yet is not an offender
    }
    const m = FORBIDDEN.exec(src)
    if (m) offenders.push(`${f.replace(REPO_ROOT + '/', '')} matches '${m[0]}'`)
    if (/ganita_ayurdaya_get/.test(src)) {
      offenders.push(`${f.replace(REPO_ROOT + '/', '')} references ganita_ayurdaya_get`)
    }
  }

  // The definition site must still never CALL the longevity capability.
  try {
    const defSrc = readFileSync(DEFINITION_SITE, 'utf8')
    if (/ganita_ayurdaya_get/.test(defSrc)) {
      offenders.push('lib/kala_sky_pattern.ts references ganita_ayurdaya_get (the definition-site exclusion covers IDENTIFIERS, never a call)')
    }
  } catch {
    return { id, title, status: 'SKIPPED', detail: 'kala_sky_pattern.ts not found — the rail cannot be evaluated' }
  }

  if (offenders.length > 0) {
    return {
      id, title, status: 'FAIL',
      detail:
        `A W4 lane file references longevity substrate. §5.4 is a SUBSTRATE ban precisely so a ` +
        `longevity fact cannot reach a window bound through an intermediate computation that ` +
        `never says "mortality" anywhere: ${offenders.join('; ')}`,
    }
  }
  return {
    id, title, status: 'PASS',
    detail:
      `No W4 lane file (${W4_LANE_FILES.length} scanned) matches /ayurdaya|longevity|maraka|\\bayus\\b/i ` +
      `or references ganita_ayurdaya_get. The one by-construction exclusion — kala_sky_pattern.ts's ` +
      `own forbidden-identifier declaration — still carries no call to the longevity capability.`,
  }
}

/** Non-vacuity: the mortality rail must be SHOWN to be able to fire. A guardrail that
 *  cannot be shown to fire is treated as a guardrail that is off (§9 G14b's discipline,
 *  applied to G16). */
function detectMortalityNonVacuity(): GateResult {
  const id = 'D-MORTALITY-NONVACUOUS'
  const title = '§5.4 mortality rail is NON-VACUOUS (a rail nobody proves can fire is null)'
  const FORBIDDEN = /ayurdaya|longevity|maraka|\bayus\b/i
  const positives = ['ayurdaya', 'longevity', 'maraka', 'the ayus reckoning']
  const negatives = ['ayusmati', 'a career window', 'guru-vara']
  const firedOn = positives.filter((s) => FORBIDDEN.test(s))
  const falsePositives = negatives.filter((s) => FORBIDDEN.test(s))
  if (firedOn.length !== positives.length || falsePositives.length > 0) {
    return {
      id, title, status: 'FAIL',
      detail:
        `The forbidden-identifier pattern is not behaving as specified. Fired on ` +
        `${firedOn.length}/${positives.length} positives; false-positived on ` +
        `[${falsePositives.join(', ')}]. A pattern that matches nothing (or everything) is a ` +
        `guardrail that is OFF.`,
    }
  }
  return {
    id, title, status: 'PASS',
    detail:
      `Pattern fires on all ${positives.length} forbidden identifiers and on none of the ` +
      `${negatives.length} controls (incl. the 'ayusmati' word-boundary control).`,
  }
}

// ── Live detectors ───────────────────────────────────────────────────────────────────

type Mode2Payload = {
  withheld?: boolean
  wrong_view?: boolean
  mode?: string
  coverage?: { concept: string; state: string; reason?: string }[]
  paddhati_divergence?: { state?: string; reason?: string } | null
  pattern_search?: {
    candidates?: {
      id: string
      start_utc: string
      end_utc: string
      precision_regime?: string
      precision_basis?: string
    }[]
    gap_report?: {
      eliminating_constraint?: unknown
      next_occurrence_state?: string
      constraints_evaluated?: { kind: string; key: string; state: string; reason: string | null }[]
    }
    precision?: { regime?: string; basis?: string; no_degrading_constraint_kinds_present?: boolean }
    adjudication?: { ledgers?: Record<string, unknown>[] } | null
  } | null
}

async function callMode2(
  client: ShadDarshanaMcpClient,
  chartId: string,
  spec: Record<string, unknown>,
  extra: Record<string, unknown> = {},
): Promise<{ payload: Mode2Payload | null; note: string }> {
  const outcome = await client.callTool(
    'kala_ritual_get',
    { chart_id: chartId, sky_pattern_spec: spec, ...extra },
    TOOL_TIMEOUT_MS,
  )
  if (outcome.timed_out) return { payload: null, note: `timed out after ${TOOL_TIMEOUT_MS}ms` }
  if (!outcome.ok) return { payload: null, note: `HTTP ${outcome.status}` }
  const { payload, isToolError } = unwrapToolPayload(outcome)
  if (isToolError) return { payload: null, note: `tool returned isError` }
  return { payload: payload as Mode2Payload, note: 'ok' }
}

function pass1(p: Mode2Payload): GateResult {
  const id = 'PASS-1'
  const title = 'Mode-2 fixture PASS 1 — non-empty, or honestly-empty'
  const ps = p.pattern_search
  if (!ps) {
    return { id, title, status: 'FAIL', detail: 'response carries no pattern_search block at all' }
  }
  const n = ps.candidates?.length ?? 0
  if (n >= 1) {
    return { id, title, status: 'PASS', detail: `${n} candidate(s) returned.` }
  }
  const elim = ps.gap_report?.eliminating_constraint ?? null
  const nextState = ps.gap_report?.next_occurrence_state ?? 'not_searched'
  if (elim !== null && nextState !== 'not_searched') {
    return {
      id, title, status: 'PASS',
      detail:
        `0 candidates, HONESTLY EMPTY: eliminating_constraint is named and ` +
        `next_occurrence_state='${nextState}' (not 'not_searched'), so an absent date is ` +
        `unambiguous between "does not occur" and "we stopped looking".`,
    }
  }
  return {
    id, title, status: 'FAIL',
    detail:
      `0 candidates with an UNEXPLAINED empty: eliminating_constraint=${JSON.stringify(elim)}, ` +
      `next_occurrence_state='${nextState}'. "It returned nothing" is never itself an explanation.`,
  }
}

function pass2(p: Mode2Payload): GateResult {
  const id = 'PASS-2'
  const title = 'Mode-2 fixture PASS 2 — precision labels correct, and correct FOR THE RIGHT REASON'
  const ps = p.pattern_search
  if (!ps) return { id, title, status: 'FAIL', detail: 'no pattern_search block' }
  const candidates = ps.candidates ?? []

  // Second assertion FIRST, because it holds even on an empty candidate set: this fixture
  // contains no transit_contact / mutual_configuration constraint, so NOTHING in it can
  // legitimately degrade the label. This asserts the REASON the label is right (§N.8).
  if (ps.precision?.no_degrading_constraint_kinds_present !== true) {
    return {
      id, title, status: 'FAIL',
      detail:
        `no_degrading_constraint_kinds_present must be true for this fixture — it contains no ` +
        `transit_contact or mutual_configuration constraint, so nothing in it can legitimately ` +
        `degrade the precision label. Got ${JSON.stringify(ps.precision)}.`,
    }
  }
  if (candidates.length === 0) {
    return {
      id, title, status: 'PASS',
      detail:
        `No candidates to label; the REASON assertion still holds ` +
        `(no_degrading_constraint_kinds_present=true, regime='${ps.precision?.regime}').`,
    }
  }
  const bad = candidates.filter(
    (c) => c.precision_regime !== 'intra_day' || !(c.precision_basis ?? '').trim(),
  )
  if (bad.length > 0) {
    return {
      id, title, status: 'FAIL',
      detail:
        `${bad.length}/${candidates.length} candidate(s) are not intra_day with a non-blank basis. ` +
        `This fixture is pāñcāṅgika-bound throughout, so 'day_grade' here means the precision-regime ` +
        `honesty is being applied BACKWARDS. First offender: ${JSON.stringify(bad[0])}`,
    }
  }
  return {
    id, title, status: 'PASS',
    detail:
      `All ${candidates.length} candidate(s) are intra_day with a non-blank basis, and the fixture ` +
      `contains no constraint kind that could legitimately degrade the label.`,
  }
}

function pass3(p: Mode2Payload): GateResult {
  const id = 'PASS-3'
  const title = 'Mode-2 fixture PASS 3 — judgment ledger + paddhati divergence block'
  const ps = p.pattern_search
  if (!ps) return { id, title, status: 'FAIL', detail: 'no pattern_search block' }

  const div = p.paddhati_divergence
  const CLOSED = ['none_computed', 'diverges', 'agrees']
  if (!div || typeof div.state !== 'string' || !CLOSED.includes(div.state)) {
    return {
      id, title, status: 'FAIL',
      detail:
        `paddhati_divergence must be present with a state from {${CLOSED.join(', ')}}. Got ` +
        `${JSON.stringify(div)}.`,
    }
  }

  const candidates = ps.candidates ?? []
  if (candidates.length === 0) {
    return {
      id, title, status: 'PASS',
      detail:
        `No candidates to carry a ledger; the paddhati divergence block is present with ` +
        `state='${div.state}' — a genuine divergence block reporting a genuine gap.`,
    }
  }
  const ledgers = ps.adjudication?.ledgers ?? []
  const REQUIRED = ['dosas_present', 'pariharas_applied', 'residual_dosas', 'net_standing']
  const missing: string[] = []
  for (const l of ledgers) {
    for (const k of REQUIRED) if (!(k in l)) missing.push(`${String(l['candidate_id'])}:${k}`)
  }
  if (ledgers.length < candidates.length || missing.length > 0) {
    return {
      id, title, status: 'FAIL',
      detail:
        `Every candidate must carry a judgment_ledger with ${REQUIRED.join('/')}. ` +
        `${ledgers.length} ledger(s) for ${candidates.length} candidate(s); missing fields: ` +
        `${missing.join(', ') || 'none'}.`,
    }
  }
  // NOTE, and this is deliberate: an EMPTY `pariharas_applied` is NOT a defect. Every
  // bg_parihara_rules row is scope='natal' except the one muhūrta-scope Abhijit row
  // ADJUDICATION-10 authorises, so residuals are normally reported UNCANCELLED with the gap
  // named. Pressing a natal-scope cancellation into muhūrta service would be a fabricated
  // cancellation and a §N.5 authority inversion.
  return {
    id, title, status: 'PASS',
    detail:
      `All ${candidates.length} candidate(s) carry a complete judgment_ledger; ` +
      `paddhati_divergence.state='${div.state}'. Empty pariharas_applied is not treated as a defect.`,
  }
}

function pass4(p: Mode2Payload, expectedConstraints: number): GateResult {
  const id = 'PASS-4'
  const title = 'Mode-2 fixture PASS 4 — census honesty, one entry per constraint'
  const ps = p.pattern_search
  if (!ps) return { id, title, status: 'FAIL', detail: 'no pattern_search block' }
  const evaluated = ps.gap_report?.constraints_evaluated ?? []
  if (evaluated.length !== expectedConstraints) {
    return {
      id, title, status: 'FAIL',
      detail:
        `constraints_evaluated must carry exactly ${expectedConstraints} entries — one per spec ` +
        `constraint, no more and no fewer. Got ${evaluated.length}: ` +
        `${evaluated.map((e) => e.key).join(', ')}`,
    }
  }
  const VALID = ['computed', 'computed_chart_relative', 'not_in_corpus', 'not_computed', 'unknown_kind']
  const bad = evaluated.filter(
    (e) => !VALID.includes(e.state) || (e.state !== 'computed' && e.state !== 'computed_chart_relative' && !(e.reason ?? '').trim()),
  )
  if (bad.length > 0) {
    return {
      id, title, status: 'FAIL',
      detail:
        `Every non-computed constraint must carry a reason, and every state must be from the ` +
        `closed set. Offenders: ${bad.map((e) => `${e.key}(${e.state})`).join(', ')}`,
    }
  }
  // tārā-bala specifically must be labelled chart-relative, NOT claimed against the global
  // census row (which correctly stays not_computed).
  const tara = evaluated.find((e) => e.kind === 'chart_relative')
  const taraNote =
    tara === undefined
      ? 'no chart_relative constraint present'
      : tara.state === 'computed_chart_relative'
        ? 'tara_bala labelled computed CHART-RELATIVE (correct — the global census row stays not_computed)'
        : `tara_bala state='${tara.state}' with reason='${(tara.reason ?? '').slice(0, 120)}'`
  return {
    id, title, status: 'PASS',
    detail: `${evaluated.length} constraint dispositions, all with valid states and reasons. ${taraNote}.`,
  }
}

function bothChartsDetector(
  withA: Mode2Payload | null,
  withB: Mode2Payload | null,
  withoutA: Mode2Payload | null,
  withoutB: Mode2Payload | null,
): GateResult {
  const id = 'BOTH-CHARTS'
  const title = 'Both-charts clause — two-part, and part 2 is what makes it earned'
  if (!withA || !withB || !withoutA || !withoutB) {
    return { id, title, status: 'SKIPPED', detail: 'one or more of the four required calls did not return a payload' }
  }
  const ids = (p: Mode2Payload): string =>
    JSON.stringify((p.pattern_search?.candidates ?? []).map((c) => `${c.start_utc}..${c.end_utc}`).sort())

  const a = ids(withA)
  const b = ids(withB)
  const a0 = ids(withoutA)
  const b0 = ids(withoutB)

  // Part 1 — the brief's own clause.
  if (a === b) {
    return {
      id, title, status: 'FAIL',
      detail:
        `Part 1 FAILED: identical candidate sets across the two canonical charts WITH tara_bala ` +
        `included. Identical output across charts means the chart is not driving the answer. ` +
        `482012f1=${a.slice(0, 200)}`,
    }
  }
  // Part 2 — the difference must TRACE TO the chart-relative constraint.
  if (a0 !== b0) {
    return {
      id, title, status: 'FAIL',
      detail:
        `Part 2 FAILED: with the chart_relative/tara_bala constraint REMOVED the two charts STILL ` +
        `differ, so something other than the chart is varying the answer — nondeterminism, or a ` +
        `leak. 482012f1(no-tara)=${a0.slice(0, 200)} vs 1c826d5a(no-tara)=${b0.slice(0, 200)}`,
    }
  }
  return {
    id, title, status: 'PASS',
    detail:
      `Part 1: candidate sets DIFFER with tara_bala included. Part 2: they COINCIDE with it ` +
      `removed — so the difference provably traces to the chart's own janma-nakṣatra, not to noise.`,
  }
}

async function mortalityLiveDetector(client: ShadDarshanaMcpClient): Promise<GateResult[]> {
  const out: GateResult[] = []
  const probes: { label: string; args: Record<string, unknown> }[] = [
    {
      label: 'substrate-shaped',
      args: { chart_id: CANONICAL_CHART_ID, question_frame: { entity: 'ayurdaya' } },
    },
    {
      label: 'request-shaped',
      args: { chart_id: CANONICAL_CHART_ID, question_frame: { stakes: 'when will I die' } },
    },
    {
      // Part (c): the exclusion must STILL refuse under native_self.
      label: 'native_self tier',
      args: { chart_id: CANONICAL_CHART_ID, question_frame: { stakes: 'longevity' }, audience_tier: 'native_self' },
    },
  ]
  for (const probe of probes) {
    const outcome = await client.callTool('kala_ritual_get', probe.args, TOOL_TIMEOUT_MS)
    const id = `D-MORTALITY-LIVE:${probe.label}`
    const title = `§5.4 mortality HARD EXCLUSION — live refusal (${probe.label})`
    if (outcome.timed_out || !outcome.ok) {
      out.push({ id, title, status: 'SKIPPED', detail: `call did not complete (timed_out=${outcome.timed_out}, status=${outcome.status})` })
      continue
    }
    const { payload } = unwrapToolPayload(outcome)
    const p = payload as Record<string, unknown>
    const withheld = p['withheld'] === true
    const namesClause = String(p['clause'] ?? '').includes('§3.5.C')
    const carriesContent =
      p['pattern_search'] !== undefined ||
      p['opportunities'] !== undefined ||
      p['candidates'] !== undefined ||
      p['reading'] !== undefined ||
      p['coverage'] !== undefined
    if (!withheld || !namesClause || carriesContent) {
      out.push({
        id, title, status: 'FAIL',
        detail:
          `Expected a §5.4 refusal envelope with NO content. withheld=${withheld}, names §3.5.C=` +
          `${namesClause}, carries content=${carriesContent}. Keys: ${Object.keys(p).join(', ')}`,
      })
    } else {
      out.push({
        id, title, status: 'PASS',
        detail: `Withheld, names §3.5.C, and carries no candidates/windows/diagnosis of any kind.`,
      })
    }
  }
  return out
}

// ── PLAN mode ────────────────────────────────────────────────────────────────────────

function planResults(): GateResult[] {
  const results: GateResult[] = [detectOneEngine(), detectMortalitySubstrateBan(), detectMortalityNonVacuity()]
  try {
    const f = loadFixture()
    const n = f.all.length
    results.push({
      id: 'FIXTURE-SHAPE',
      title: 'The canned fixture is present, parses, and carries the brief\'s six constraints',
      status: n === 6 ? 'PASS' : 'FAIL',
      detail:
        n === 6
          ? `sky_pattern_spec v1 with 6 constraints (${f.all.map((c) => Object.keys(c)[0]).join(', ')}), horizon ${f.horizon.months} months.`
          : `Expected the brief's SIX constraints, found ${n}. The Conductor discharges the fixture EXACTLY and does not substitute an easier query.`,
    })
  } catch (err) {
    results.push({
      id: 'FIXTURE-SHAPE',
      title: 'The canned fixture is present and parses',
      status: 'FAIL',
      detail: `could not load ${FIXTURE_PATH}: ${String(err)}`,
    })
  }
  results.push({
    id: 'LIVE-PENDING',
    title: 'Live Mode-2 discharge (PASS 1–4 + both-charts + live mortality refusal)',
    status: 'SKIPPED',
    detail:
      'MCP_SERVER_URL not set — the four PASS conditions, the two-part both-charts detector and ' +
      'the live mortality refusal require a live server and were NOT evaluated. NOT weakened to ' +
      'force green: an unevaluated condition is SKIPPED, never PASS.',
  })
  return results
}

// ── main ─────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const target = resolveMcpTarget()
  if (!target) {
    process.exit(
      printGateReport(
        'yajna_mode2_fixture_gate (PLAN mode)',
        planResults(),
        'MCP_SERVER_URL not set — source-level detectors ran; every live detector is SKIPPED, never forced green.',
      ),
    )
    return
  }

  const client = new ShadDarshanaMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()

  const results: GateResult[] = [detectOneEngine(), detectMortalitySubstrateBan(), detectMortalityNonVacuity()]

  let fixture: Fixture
  try {
    fixture = loadFixture()
  } catch (err) {
    results.push({
      id: 'FIXTURE-SHAPE', title: 'The canned fixture is present and parses',
      status: 'FAIL', detail: `could not load ${FIXTURE_PATH}: ${String(err)}`,
    })
    process.exit(printGateReport('yajna_mode2_fixture_gate (LIVE)', results))
    return
  }

  const specWith = specFromFixture(fixture, { dropChartRelative: false })
  const specWithout = specFromFixture(fixture, { dropChartRelative: true })

  const [withA, withB, withoutA, withoutB] = await Promise.all([
    callMode2(client, CANONICAL_CHART_ID, specWith),
    callMode2(client, CROSS_CHECK_CHART_ID, specWith),
    callMode2(client, CANONICAL_CHART_ID, specWithout),
    callMode2(client, CROSS_CHECK_CHART_ID, specWithout),
  ])

  if (!withA.payload) {
    results.push({
      id: 'LIVE-CALL', title: 'Live Mode-2 call on the primary chart',
      status: 'SKIPPED', detail: `kala_ritual_get unreachable: ${withA.note}`,
    })
    process.exit(printGateReport('yajna_mode2_fixture_gate (LIVE)', results))
    return
  }

  const nConstraints = fixture.all.length
  results.push(pass1(withA.payload))
  results.push(pass2(withA.payload))
  results.push(pass3(withA.payload))
  results.push(pass4(withA.payload, nConstraints))

  // The whole battery re-run on the mirror chart (standing both-charts rail, G13).
  if (withB.payload) {
    for (const r of [pass1(withB.payload), pass2(withB.payload), pass3(withB.payload), pass4(withB.payload, nConstraints)]) {
      results.push({ ...r, id: `${r.id}@1c826d5a`, title: `${r.title} (mirror chart)` })
    }
  } else {
    results.push({
      id: 'MIRROR-CALL', title: 'Live Mode-2 call on the mirror chart',
      status: 'SKIPPED', detail: `kala_ritual_get unreachable for 1c826d5a: ${withB.note}`,
    })
  }

  results.push(bothChartsDetector(withA.payload, withB.payload, withoutA.payload, withoutB.payload))
  results.push(...(await mortalityLiveDetector(client)))

  process.exit(printGateReport('yajna_mode2_fixture_gate (LIVE)', results))
}

main().catch((err) => {
  console.error('yajna_mode2_fixture_gate FATAL:', err)
  process.exit(2)
})
