#!/usr/bin/env tsx
/**
 * specificity_gate_v0.ts — ṢAḌ-DARŚANA specificity gate, HARD criterion (W2).
 * (Filename keeps the historical `_v0` from the W0.6 skeleton era so workflow and doc
 * references stay stable; the criterion inside is the W2 HARD gate, not the skeleton.)
 *
 * DESIGN AUTHORITY: SHAD_DARSHANA_BRIEF_v2_0.md §3 W2 gate ("specificity gate
 * HARD-green") · KALA_W2_FIELD_DESIGN_v1_0.md §10 ("cohort charts; composer templates
 * must vary") · KALA_SUPREME_ELEVATION_v1_0.md §5 E3 — "any sentence template whose
 * output is invariant across charts is filler and FAILS the build." A reading that would
 * serve unchanged for a different chart is generic astrology — the CLAUDE.md §L cardinal
 * sin.
 *
 * ── THE HARD CRITERION (what this gate measures, exactly) ────────────────────────────
 * For every registered kala_* view, pairwise across all reachable built charts:
 *   S1  FAIL if two different charts' composed reading text is byte-identical.
 *   S2  FAIL if the two texts become identical after masking chart-specific tokens
 *       (chart_ids, chart/native display names, digit runs). This is the template test:
 *       a reading that differs from another chart's ONLY by name/number substitution is
 *       one template with slots — filler, per E3.
 *   S3  FAIL if two different charts' readings ground themselves in literally the same
 *       non-empty evidence fact-id set. (Limited power by construction: fact_ids are
 *       chart-scoped in this system, so they usually differ trivially — S3 catches only
 *       the gross case of shared/hardcoded evidence. Stated, not oversold.)
 *   S4  WARN (reported, not gated) when the masked-sentence-template Jaccard overlap of
 *       a pair is ≥ SPECIFICITY_TEMPLATE_OVERLAP_WARN (default 0.8): heavy scaffold
 *       sharing worth eyes, but legitimately shared section headers make a hard gate at
 *       this cohort size (~5-6 built charts) dishonest.
 *
 * WHAT THIS CANNOT MEASURE (honest limits):
 *   - Semantic genericity expressed with varied wording (two paraphrases of the same
 *     generic claim pass S1/S2). Detecting that requires the full-cohort statistical
 *     battery below.
 *   - Name-substitution templates where the gate could not learn the chart's display
 *     name (masking then cannot normalize the name slot; S2 may miss). Aliases are
 *     collected from catalog_charts_list rows AND from chart_header-like objects inside
 *     each payload to minimize this window.
 *   - FULL-COHORT STATISTICAL GATING IS DEFERRED: production has `bg_synthetic_cohort`
 *     (10,000 synthetic charts) + `bg_synthetic_cohort_md`, but those charts are NOT
 *     built, served charts — no chart_facts/kala_* rows exist for them and they cannot
 *     be queried through MCP. UNBLOCK: run the orchestrator per-chart build (L1→L3+)
 *     for a sampled sub-cohort and surface them via catalog_charts_list; then this gate
 *     can gate template variance statistically over the cohort. Until then it gates
 *     pairwise over ALL built charts in the system (currently ~5-6), which is real,
 *     not padded.
 *
 * ── NON-VACUITY (§N.8 Earned-Signal) ─────────────────────────────────────────────────
 * Every invocation (PLAN and LIVE) runs embedded fixture self-checks: a deliberately
 * generic pair (name/number-swap template) MUST FAIL S2, a byte-identical pair MUST
 * FAIL S1, a shared-evidence pair MUST FAIL S3, and a genuinely chart-specific pair
 * MUST PASS. If the comparator ever stops rejecting the generic fixture, the gate
 * itself FAILS — it can never silently go soft. The vitest battery
 * (`__tests__/specificity_gate_hard.test.ts`) additionally proves the script-level
 * exit-1 path end-to-end.
 *
 * ── MODES ────────────────────────────────────────────────────────────────────────────
 *   PLAN mode (no MCP_SERVER_URL) — NO LONGER "exit 0 always". It verifies, and FAILS
 *     on violation of, everything checkable without a live server:
 *       (a) registration census: all 8 kala_* views statically registered (detector now
 *           resolves `server.tool(TOOL_NAME, …)` const-identifier registration — the
 *           false negative that retired this gate is fixed, see
 *           _kala_tool_registration.ts);
 *       (b) the fixture self-checks above (criterion arithmetic).
 *     Live pairwise comparison is reported SKIPPED with the reason.
 *   LIVE mode (MCP_SERVER_URL [+ MCP_BEARER]) — everything PLAN does, plus: discovers
 *     ALL built charts via catalog_charts_list (canonical + cross-check always included,
 *     capped at SPECIFICITY_GATE_MAX_COHORT=12 as an anti-runaway bound, not a target),
 *     calls every registered kala_* view once per chart, and applies S1–S4 pairwise.
 *
 * Run (plan mode, from `platform/`):
 *   npx tsx scripts/census/shad_darshana_gates/specificity_gate_v0.ts
 * Run (live mode, from `platform/`):
 *   MCP_SERVER_URL=https://<mcp-host>/mcp MCP_BEARER=<token> \
 *     npx tsx scripts/census/shad_darshana_gates/specificity_gate_v0.ts
 */
import {
  ShadDarshanaMcpClient,
  resolveMcpTarget,
  unwrapToolPayload,
  envOrDefault,
  DEFAULT_TOOL_TIMEOUT_MS,
  CANONICAL_CHART_ID,
  CROSS_CHECK_CHART_ID,
} from './_mcp_client'
import { printGateReport, type GateResult } from './_report'
import { SHAD_DARSHANA_EIGHT_TOOLS, collectShadDarshanaRegistration, isKalaToolRegistered } from './_kala_tool_registration'

const TOOL_TIMEOUT_MS = Number(envOrDefault('SPECIFICITY_GATE_TOOL_TIMEOUT_MS', String(DEFAULT_TOOL_TIMEOUT_MS)))
const MIN_GAP_MS = Number(envOrDefault('SPECIFICITY_GATE_MIN_GAP_MS', '300'))
// Anti-runaway bound on live calls (8 tools × N charts), NOT a cohort target: all built
// charts in the system (~5-6 today) fit under it. Raise via env when the built population
// grows past it.
const MAX_COHORT_SIZE = Number(envOrDefault('SPECIFICITY_GATE_MAX_COHORT', '12'))
const TEMPLATE_OVERLAP_WARN = Number(envOrDefault('SPECIFICITY_TEMPLATE_OVERLAP_WARN', '0.8'))

const DEFERRED_COHORT_NOTE =
  'DEFERRED (named unblocker): full-cohort statistical gating over bg_synthetic_cohort (10,000 synthetic charts) requires those ' +
  'charts to be BUILT and SERVED — no chart_facts/kala_* rows exist for them and they are not reachable through MCP. Unblock by ' +
  'running the orchestrator per-chart build for a sampled sub-cohort and surfacing it via catalog_charts_list. Until then this ' +
  'gate applies the S1-S4 criterion pairwise over ALL built charts in the system.'

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// ── The comparator (exported, unit-tested) ────────────────────────────────────────────

export type ReadingSample = {
  chart_id: string
  text: string
  /** Evidence fact-ids the reading grounds itself in (collected from the payload). */
  fact_ids: string[]
  /** Chart-specific tokens beyond the chart_id to mask: display/native names etc. */
  aliases: string[]
}

export type PairVerdict = {
  pass: boolean
  criterion: 'S1_BYTE_IDENTICAL' | 'S2_MASKED_IDENTICAL' | 'S3_IDENTICAL_EVIDENCE' | null
  /** Jaccard overlap of masked sentence templates, 0..1 (S4 signal). */
  template_overlap: number
  detail: string
}

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Masks chart-specific tokens (aliases, longest first, case-insensitive) and digit runs,
 *  then collapses whitespace — what remains is the sentence TEMPLATE. */
export function maskChartSpecificTokens(text: string, aliases: string[]): string {
  let out = text
  const tokens = [...new Set(aliases.filter((a) => a && a.trim().length >= 3))].sort((x, y) => y.length - x.length)
  for (const token of tokens) {
    out = out.replace(new RegExp(escapeRegExp(token), 'gi'), '⟨CHART⟩')
  }
  out = out.replace(/\d+(?:[.,:]\d+)*/g, '#')
  return out.replace(/\s+/g, ' ').trim()
}

function splitSentences(text: string): string[] {
  return text
    .split(/(?<=[.!?])\s+|\n+/)
    .map((s) => s.trim())
    .filter((s) => s.length > 0)
}

/** Jaccard overlap of the two texts' masked sentence-template sets (0..1). */
export function sentenceTemplateOverlap(textA: string, textB: string, aliases: string[]): number {
  const a = new Set(splitSentences(textA).map((s) => maskChartSpecificTokens(s, aliases)))
  const b = new Set(splitSentences(textB).map((s) => maskChartSpecificTokens(s, aliases)))
  if (a.size === 0 || b.size === 0) return 0
  let shared = 0
  for (const s of a) if (b.has(s)) shared++
  const union = a.size + b.size - shared
  return union === 0 ? 0 : shared / union
}

function setsEqual(a: Set<string>, b: Set<string>): boolean {
  if (a.size !== b.size) return false
  for (const x of a) if (!b.has(x)) return false
  return true
}

/** The HARD pairwise criterion — see the file header for exactly what S1–S3 measure. */
export function compareReadingPair(a: ReadingSample, b: ReadingSample): PairVerdict {
  const aliasUnion = [
    ...a.aliases,
    ...b.aliases,
    a.chart_id,
    b.chart_id,
    a.chart_id.slice(0, 8),
    b.chart_id.slice(0, 8),
  ]
  const overlap = sentenceTemplateOverlap(a.text, b.text, aliasUnion)

  if (a.text === b.text) {
    return {
      pass: false,
      criterion: 'S1_BYTE_IDENTICAL',
      template_overlap: overlap,
      detail: `Byte-identical reading text across charts ${a.chart_id.slice(0, 8)} and ${b.chart_id.slice(0, 8)}. First 200 chars: ${a.text.slice(0, 200)}`,
    }
  }

  const maskedA = maskChartSpecificTokens(a.text, aliasUnion)
  const maskedB = maskChartSpecificTokens(b.text, aliasUnion)
  if (maskedA === maskedB) {
    return {
      pass: false,
      criterion: 'S2_MASKED_IDENTICAL',
      template_overlap: overlap,
      detail:
        `Reading differs ONLY by chart-name/number substitution between ${a.chart_id.slice(0, 8)} and ${b.chart_id.slice(0, 8)} — ` +
        `one template with slots (E3 filler). Masked template (first 200 chars): ${maskedA.slice(0, 200)}`,
    }
  }

  const factsA = new Set(a.fact_ids)
  const factsB = new Set(b.fact_ids)
  if (factsA.size > 0 && factsB.size > 0 && setsEqual(factsA, factsB)) {
    return {
      pass: false,
      criterion: 'S3_IDENTICAL_EVIDENCE',
      template_overlap: overlap,
      detail: `Identical non-empty evidence fact-id set (${factsA.size} ids) across charts ${a.chart_id.slice(0, 8)} and ${b.chart_id.slice(0, 8)} — readings for different charts grounded in literally the same evidence rows.`,
    }
  }

  return {
    pass: true,
    criterion: null,
    template_overlap: overlap,
    detail: `Structurally distinct (template_overlap=${overlap.toFixed(2)}).`,
  }
}

// ── Non-vacuity fixtures + self-checks (run on EVERY invocation) ─────────────────────

export const NON_VACUITY_FIXTURES: Record<string, { a: ReadingSample; b: ReadingSample; must: 'FAIL' | 'PASS'; expect_criterion: PairVerdict['criterion'] }> = {
  byte_identical_pair: {
    a: { chart_id: 'fixture-aaaa-1111', text: 'Saturn presses the tenth house; consolidation, not expansion, is the season.', fact_ids: [], aliases: [] },
    b: { chart_id: 'fixture-bbbb-2222', text: 'Saturn presses the tenth house; consolidation, not expansion, is the season.', fact_ids: [], aliases: [] },
    must: 'FAIL',
    expect_criterion: 'S1_BYTE_IDENTICAL',
  },
  generic_name_swap_pair: {
    a: {
      chart_id: 'fixture-aaaa-1111',
      text: 'For Abhisek, the current Saturn dasha (7.2 years remaining) demands discipline; Abhisek should expect career consolidation through 2028.',
      fact_ids: ['fx:a1'],
      aliases: ['Abhisek'],
    },
    b: {
      chart_id: 'fixture-bbbb-2222',
      text: 'For Abhinandan, the current Saturn dasha (3.4 years remaining) demands discipline; Abhinandan should expect career consolidation through 2031.',
      fact_ids: ['fx:b1'],
      aliases: ['Abhinandan'],
    },
    must: 'FAIL',
    expect_criterion: 'S2_MASKED_IDENTICAL',
  },
  shared_evidence_pair: {
    a: { chart_id: 'fixture-aaaa-1111', text: 'Jupiter return in the tenth brings visibility; the lagna lord carries it.', fact_ids: ['fx:1', 'fx:2'], aliases: [] },
    b: { chart_id: 'fixture-bbbb-2222', text: 'Venus antardasha softens the seventh; partnership themes dominate this window.', fact_ids: ['fx:2', 'fx:1'], aliases: [] },
    must: 'FAIL',
    expect_criterion: 'S3_IDENTICAL_EVIDENCE',
  },
  chart_specific_pair: {
    a: {
      chart_id: 'fixture-aaaa-1111',
      text: 'Aries lagna with Saturn in the tenth: Sade Sati third phase compresses career risk into Q3; the Capricorn stellium answers with structure.',
      fact_ids: ['fx:a1', 'fx:a2'],
      aliases: ['Abhisek'],
    },
    b: {
      chart_id: 'fixture-bbbb-2222',
      text: 'Cancer lagna, Moon-Jupiter gajakesari from the fourth: home and mother themes dominate; the Venus antardasha opens a property window before December.',
      fact_ids: ['fx:b1', 'fx:b2'],
      aliases: ['Abhinandan'],
    },
    must: 'PASS',
    expect_criterion: null,
  },
}

/** Runs the comparator against the embedded fixtures. Any disagreement is a FAIL of the
 *  GATE ITSELF — the mechanism §N.8 requires so this gate can never silently go soft. */
export function runFixtureSelfChecks(): GateResult[] {
  const results: GateResult[] = []
  for (const [name, fx] of Object.entries(NON_VACUITY_FIXTURES)) {
    const verdict = compareReadingPair(fx.a, fx.b)
    const behaved = fx.must === 'FAIL' ? !verdict.pass && verdict.criterion === fx.expect_criterion : verdict.pass
    results.push({
      id: `specificity-selftest:${name}`,
      title: `Non-vacuity self-check: ${name} must ${fx.must}${fx.expect_criterion ? ` (${fx.expect_criterion})` : ''}`,
      status: behaved ? 'PASS' : 'FAIL',
      detail: behaved
        ? `Comparator behaved: ${fx.must} via ${verdict.criterion ?? 'no criterion (clean pass)'}.`
        : `COMPARATOR LOST ITS TEETH: expected ${fx.must}/${fx.expect_criterion ?? 'clean'}, got pass=${verdict.pass} criterion=${verdict.criterion}. ${verdict.detail}`,
    })
  }
  return results
}

// ── Payload extraction (LIVE mode) ───────────────────────────────────────────────────

/**
 * Best-effort extraction of the composed reading text from a kala_* envelope payload.
 * Walks the plausible locations (`reading.full_text`, `reading.thesis` +
 * `reading.verdict.statement`, top-level `full_text`) rather than assuming one fixed
 * shape. Returns null, never a fabricated string, when nothing textual is found.
 */
export function extractReadingText(payload: unknown): string | null {
  if (typeof payload !== 'object' || payload === null) return null
  const obj = payload as Record<string, unknown>
  const reading = obj['reading']
  if (typeof reading === 'object' && reading !== null) {
    const r = reading as Record<string, unknown>
    if (typeof r['full_text'] === 'string' && r['full_text'].length > 0) return r['full_text']
    const parts: string[] = []
    if (typeof r['thesis'] === 'string') parts.push(r['thesis'])
    const verdict = r['verdict']
    if (typeof verdict === 'object' && verdict !== null && typeof (verdict as Record<string, unknown>)['statement'] === 'string') {
      parts.push((verdict as Record<string, unknown>)['statement'] as string)
    }
    if (parts.length > 0) return parts.join(' ')
  }
  if (typeof obj['full_text'] === 'string' && obj['full_text'].length > 0) return obj['full_text']
  return null
}

const FACT_KEY_RE = /^(fact_ids?|fact_keys?|constituent_facts?|evidence_fact_ids?)$/
const NAME_KEY_RE = /^(name|native_name|chart_name|display_name|label)$/

/** Recursively collects evidence fact-ids (any key matching FACT_KEY_RE) and
 *  chart-name aliases (name-like keys on objects that ALSO carry a chart_id-like key —
 *  the chart_header shape — so unrelated `name` fields (yogas, windows) are NOT
 *  over-masked into false S2 positives). */
export function collectFactIdsAndAliases(payload: unknown): { fact_ids: string[]; aliases: string[] } {
  const factIds = new Set<string>()
  const aliases = new Set<string>()
  const walk = (node: unknown): void => {
    if (Array.isArray(node)) {
      for (const item of node) walk(item)
      return
    }
    if (typeof node !== 'object' || node === null) return
    const obj = node as Record<string, unknown>
    const hasChartId = typeof obj['chart_id'] === 'string' || typeof obj['chartId'] === 'string'
    for (const [key, value] of Object.entries(obj)) {
      if (FACT_KEY_RE.test(key)) {
        if (typeof value === 'string' && value.length > 0) factIds.add(value)
        else if (Array.isArray(value)) for (const v of value) if (typeof v === 'string' && v.length > 0) factIds.add(v)
      }
      if (hasChartId && NAME_KEY_RE.test(key) && typeof value === 'string' && value.trim().length >= 3) {
        aliases.add(value.trim())
        for (const word of value.trim().split(/\s+/)) if (word.length >= 3) aliases.add(word)
      }
      walk(value)
    }
  }
  walk(payload)
  return { fact_ids: [...factIds], aliases: [...aliases] }
}

// ── Registration census (both modes; FAIL-capable) ───────────────────────────────────

function registrationResults(): GateResult[] {
  const registration = collectShadDarshanaRegistration()
  const results: GateResult[] = []
  for (const tool of SHAD_DARSHANA_EIGHT_TOOLS) {
    const files = registration[tool]
    results.push({
      id: `specificity-registration:${tool}`,
      title: `Registration census — ${tool}`,
      status: files.length > 0 ? 'PASS' : 'FAIL',
      detail:
        files.length > 0
          ? `Statically registered in: ${files.join(', ')}`
          : 'NOT statically registered under platform-mcp/src/tools (literal AND same-file-const identifier forms both checked). All 8 views merged at W0.4 — an unregistered view here is a regression, not a pending sibling lane.',
    })
  }
  return results
}

// ── PLAN mode ────────────────────────────────────────────────────────────────────────

function planResults(): GateResult[] {
  const results: GateResult[] = [...registrationResults(), ...runFixtureSelfChecks()]
  results.push({
    id: 'specificity-live-comparison',
    title: 'Live pairwise S1-S4 comparison across built charts',
    status: 'SKIPPED',
    detail: 'PLAN mode — no MCP_SERVER_URL set, live calls not possible. Registration census + non-vacuity criterion arithmetic above are still gated (FAIL-capable) in this mode.',
  })
  results.push({
    id: 'specificity-full-cohort',
    title: 'Full-cohort statistical gating (10k bg_synthetic_cohort)',
    status: 'SKIPPED',
    detail: DEFERRED_COHORT_NOTE,
  })
  return results
}

// ── LIVE mode ────────────────────────────────────────────────────────────────────────

type CohortChart = { chart_id: string; aliases: string[] }

/** Discovers ALL built charts: the two canonical charts always, plus every chart
 *  surfaced by `catalog_charts_list`, bounded by MAX_COHORT_SIZE (anti-runaway bound,
 *  not a target). Never fabricates chart ids — a small cohort is reported honestly. */
async function discoverCohort(client: ShadDarshanaMcpClient): Promise<{ charts: CohortChart[]; note: string }> {
  const charts: CohortChart[] = [
    { chart_id: CANONICAL_CHART_ID, aliases: [] },
    { chart_id: CROSS_CHECK_CHART_ID, aliases: [] },
  ]
  const outcome = await client.callTool('catalog_charts_list', {}, TOOL_TIMEOUT_MS)
  if (outcome.timed_out || !outcome.ok) {
    return { charts, note: `catalog_charts_list unreachable (status=${outcome.status}, timed_out=${outcome.timed_out}) — cohort = the 2 canonical charts only.` }
  }
  const { payload, isToolError } = unwrapToolPayload(outcome)
  if (isToolError || typeof payload !== 'object' || payload === null) {
    return { charts, note: 'catalog_charts_list returned a tool error or non-object payload — cohort = the 2 canonical charts only.' }
  }
  const obj = payload as Record<string, unknown>
  const rows = Array.isArray(obj['charts']) ? (obj['charts'] as unknown[]) : Array.isArray(obj['items']) ? (obj['items'] as unknown[]) : []
  for (const c of rows) {
    if (typeof c !== 'object' || c === null) continue
    const row = c as Record<string, unknown>
    const id = row['chart_id']
    if (typeof id !== 'string' || id.length === 0) continue
    const aliases: string[] = []
    for (const [key, value] of Object.entries(row)) {
      if (NAME_KEY_RE.test(key) && typeof value === 'string' && value.trim().length >= 3) {
        aliases.push(value.trim())
        for (const word of value.trim().split(/\s+/)) if (word.length >= 3) aliases.push(word)
      }
    }
    const existing = charts.find((x) => x.chart_id === id)
    if (existing) {
      existing.aliases.push(...aliases)
    } else if (charts.length < MAX_COHORT_SIZE) {
      charts.push({ chart_id: id, aliases })
    }
  }
  return {
    charts,
    note:
      charts.length >= MAX_COHORT_SIZE
        ? `cohort hit the anti-runaway bound of ${MAX_COHORT_SIZE} — raise SPECIFICITY_GATE_MAX_COHORT if the built population outgrew it.`
        : `cohort = ALL ${charts.length} built chart(s) reachable via catalog_charts_list (bound ${MAX_COHORT_SIZE} not hit). Honest, not padded.`,
  }
}

async function liveResults(client: ShadDarshanaMcpClient): Promise<GateResult[]> {
  const results: GateResult[] = [...registrationResults(), ...runFixtureSelfChecks()]
  const registration = collectShadDarshanaRegistration()
  const { charts, note } = await discoverCohort(client)
  results.push({
    id: 'specificity-cohort',
    title: 'Built-chart cohort discovery',
    status: charts.length >= 2 ? 'PASS' : 'FAIL',
    detail: `${note} chart_ids=${JSON.stringify(charts.map((c) => c.chart_id))}`,
  })
  results.push({
    id: 'specificity-full-cohort',
    title: 'Full-cohort statistical gating (10k bg_synthetic_cohort)',
    status: 'SKIPPED',
    detail: DEFERRED_COHORT_NOTE,
  })

  for (const tool of SHAD_DARSHANA_EIGHT_TOOLS) {
    if (!isKalaToolRegistered(tool, registration)) {
      // Already a FAIL row from registrationResults(); no live call to attempt.
      continue
    }

    const samples: ReadingSample[] = []
    let hadHardFailure = false
    let hadSoftIssue = false
    const perChartNotes: string[] = []

    for (const chart of charts) {
      const outcome = await client.callTool(tool, { chart_id: chart.chart_id }, TOOL_TIMEOUT_MS)
      await sleep(MIN_GAP_MS)
      if (outcome.timed_out || outcome.status >= 500) {
        hadHardFailure = true
        perChartNotes.push(`${chart.chart_id.slice(0, 8)}: HARD FAIL (timed_out=${outcome.timed_out}, status=${outcome.status})`)
        continue
      }
      if (!outcome.ok) {
        hadSoftIssue = true
        perChartNotes.push(`${chart.chart_id.slice(0, 8)}: HTTP ${outcome.status} (arg-schema mismatch is possible, not a specificity verdict)`)
        continue
      }
      const { payload, isToolError } = unwrapToolPayload(outcome)
      if (isToolError) {
        hadSoftIssue = true
        perChartNotes.push(`${chart.chart_id.slice(0, 8)}: tool-level error`)
        continue
      }
      const text = extractReadingText(payload)
      if (text == null || text.trim().length === 0) {
        hadSoftIssue = true
        perChartNotes.push(`${chart.chart_id.slice(0, 8)}: no reading text found in payload`)
        continue
      }
      const { fact_ids, aliases } = collectFactIdsAndAliases(payload)
      samples.push({ chart_id: chart.chart_id, text, fact_ids, aliases: [...chart.aliases, ...aliases] })
    }

    if (hadHardFailure) {
      results.push({ id: `specificity:${tool}`, title: `Specificity — ${tool}`, status: 'FAIL', detail: `Live infra failure: ${perChartNotes.join('; ')}` })
      continue
    }
    if (samples.length < 2) {
      results.push({
        id: `specificity:${tool}`,
        title: `Specificity — ${tool}`,
        status: hadSoftIssue ? 'WARN' : 'SKIPPED',
        detail: `Could not compare ≥2 charts' reading text (got ${samples.length}). ${perChartNotes.join('; ')}`,
      })
      continue
    }

    const failures: string[] = []
    let maxOverlap = 0
    let maxOverlapPair = ''
    let pairs = 0
    for (let i = 0; i < samples.length; i++) {
      for (let j = i + 1; j < samples.length; j++) {
        const verdict = compareReadingPair(samples[i]!, samples[j]!)
        pairs++
        if (verdict.template_overlap > maxOverlap) {
          maxOverlap = verdict.template_overlap
          maxOverlapPair = `${samples[i]!.chart_id.slice(0, 8)}×${samples[j]!.chart_id.slice(0, 8)}`
        }
        if (!verdict.pass) failures.push(`[${verdict.criterion}] ${verdict.detail}`)
      }
    }

    if (failures.length > 0) {
      results.push({ id: `specificity:${tool}`, title: `Specificity — ${tool}`, status: 'FAIL', detail: `FILLER DETECTED (E3) in ${failures.length}/${pairs} pair(s): ${failures.join(' | ')}` })
    } else if (maxOverlap >= TEMPLATE_OVERLAP_WARN) {
      results.push({
        id: `specificity:${tool}`,
        title: `Specificity — ${tool}`,
        status: 'WARN',
        detail: `S1-S3 clean across ${pairs} pair(s) / ${samples.length} charts, but masked-sentence-template overlap ${maxOverlap.toFixed(2)} (pair ${maxOverlapPair}) ≥ ${TEMPLATE_OVERLAP_WARN} — heavy scaffold sharing, reported not gated (see file header for why).`,
      })
    } else {
      results.push({
        id: `specificity:${tool}`,
        title: `Specificity — ${tool}`,
        status: 'PASS',
        detail: `Chart-specific across ${samples.length} charts / ${pairs} pair(s); max template_overlap=${maxOverlap.toFixed(2)}${maxOverlapPair ? ` (${maxOverlapPair})` : ''}. ${perChartNotes.length > 0 ? `Notes: ${perChartNotes.join('; ')}` : ''}`,
      })
    }
  }
  return results
}

// ── Entry ────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const target = resolveMcpTarget()
  if (!target) {
    process.exit(printGateReport(
      'specificity_gate (HARD criterion, PLAN mode)',
      planResults(),
      'MCP_SERVER_URL not set — PLAN mode: registration census + non-vacuity self-checks are GATED (FAIL-capable); live pairwise comparison skipped.',
    ))
    return
  }

  const client = new ShadDarshanaMcpClient(target.baseUrl, target.bearer, TOOL_TIMEOUT_MS)
  await client.init()
  process.exit(printGateReport('specificity_gate (HARD criterion, LIVE)', await liveResults(client)))
}

// Run only when invoked as a script (tsx/node), never on vitest import.
if (process.argv[1] && /specificity_gate_v0\.(ts|mts|cts|js|mjs|cjs)$/.test(process.argv[1])) {
  main().catch((err) => {
    console.error('specificity_gate FATAL:', err)
    process.exit(2)
  })
}
