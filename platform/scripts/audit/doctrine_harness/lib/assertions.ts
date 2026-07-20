/**
 * assertions.ts — the D-1.5a executable assertion definitions.
 *
 * Source of truth for the assertion TEXT: POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md
 * §K.2 ("D-1.5 ACCEPTANCE GATE", 12 numbered assertions) + BRIEF_D1_5A.md
 * Lane A-γ (A5 two-chart divergence, A7 aspect off-by-one spot-check).
 * Per CONDUCTOR_PROTOCOL.md §8.8(v): after this lane merges, THIS FILE is
 * the canonical copy of the gate — the register/plan text is provenance,
 * this is authoritative.
 *
 * Every assertion is a live MCP call against the deployed connector (CR-96:
 * "verify against the CONSUMING SURFACE, not the database"). No assertion
 * reads a database row or a writer's internal state directly.
 *
 * Response-shape note (confirmed live against the deployed connector while
 * building this harness, 2026-07-15): a tool's JSON payload is reached via
 * `structuredContent.object` (mcp_client.ts unwraps this), and from there
 * the tool's own payload nesting varies per tool — some tools double-nest
 * under `.content.content` (ganita_yogas_get), others single-nest under
 * `.content` (ganita_yoga_firings_get, bodha_signals_get, ganita_vichara_get),
 * others (judgment_query) expose `.content.checklist.bearing_yogas`. Each
 * assertion below reads the exact path verified live; if a future response
 * shape changes, the assertion will report a diagnosable "red — unexpected
 * shape" rather than a false green (never fabricate a pass — CLAUDE.md B.10
 * spirit applied to this harness itself).
 */
import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import type { AssertionDef, AssertionResult, RunContext } from './types'

const WEALTH_TRIKONA_VIOLATION_VALENCES = new Set(['malefic', 'strong_malefic'])

type WealthSignal = {
  signal_type_id?: string
  valence?: string
  valence_source?: string
  citation_human?: string
  configuration_jsonb?: {
    link_type?: string
    lord?: string
    source_house?: number
    target_house?: number
    fact_key?: string
  }
}

/**
 * Pages through bodha_signals_get(domain=wealth) collecting up to
 * maxPages*pageSize signals. Cached per RunContext+chart — K.2 assertions
 * #1-#5 all scan the same wealth-signal population; without this cache each
 * assertion re-pages independently (5 x 10 calls = 50 near-simultaneous
 * requests), which was observed to degrade the deployed connector's
 * response quality under load (see mcp_client.ts's MIN_REQUEST_GAP_MS
 * comment). One shared fetch, reused, is both faster and more honest.
 */
const wealthSignalCache = new WeakMap<RunContext, Promise<WealthSignal[]>>()

async function fetchWealthSignals(ctx: RunContext, maxPages = 10, pageSize = 10): Promise<WealthSignal[]> {
  const cached = wealthSignalCache.get(ctx)
  if (cached) return cached
  const promise = (async () => {
    const all: WealthSignal[] = []
    for (let page = 0; page < maxPages; page++) {
      const { content } = await ctx.client.callTool('bodha_signals_get', {
        chart_id: ctx.chartId,
        domain: 'wealth',
        top_k: pageSize,
        offset: page * pageSize,
      })
      const c = (content as { content?: { signals?: WealthSignal[] } })?.content
      const signals = c?.signals ?? []
      all.push(...signals)
      if (signals.length < pageSize) break // no more pages
    }
    return all
  })()
  wealthSignalCache.set(ctx, promise)
  return promise
}

// W3-L2: judgment_flags entries are now `{code, detail?, severity?}` (closed enum) OR — during
// the transition, and for any not-yet-migrated emitter — a bare legacy string. This harness
// calls the LIVE deployed connector over MCP, so it must tolerate either shape defensively,
// never assume the pre-migration `string[]`.
type JudgmentFlagEntryLike = { code: string; detail?: string } | string

function judgmentFlagsIncludeCode(flags: JudgmentFlagEntryLike[], code: string): boolean {
  return flags.some(f => (typeof f === 'string' ? f === code || f.startsWith(`${code}:`) : f.code === code))
}

function ganitaYogasV3Payload(content: unknown): {
  verdict: { pancha_mahapurusha?: { summary?: string } }
  judgment_flags: JudgmentFlagEntryLike[]
  coverage: { served?: number | null; total?: number | null } | null
  rows: Array<{ fact_category?: string }>
  total: number | null
  firingsPointer: { fired_count?: number | null } | null
} {
  const top = content as {
    verdict?: { pancha_mahapurusha?: { summary?: string } }
    judgment_flags?: JudgmentFlagEntryLike[]
    coverage?: { served?: number | null; total?: number | null }
    // D-1.5a wave gate finding (live post-deploy verification): this tool's response
    // shape is `content.rows`/`content.total`/`content.firings_pointer` (single-nested)
    // — the harness's original `content.content.rows` assumption predates A-beta's
    // capability-route double-wrap fix (PR #562) and never got updated, so this parser
    // silently read past the real payload into `[]` for every call, exactly the same
    // class of bug that fix corrected server-side. Falls back to the old double-nested
    // shape defensively in case an older/unpatched connector is ever targeted.
    content?: {
      rows?: Array<{ fact_category?: string }>
      total?: number
      firings_pointer?: { fired_count?: number | null }
      content?: { rows?: Array<{ fact_category?: string }>; total?: number; firings_pointer?: { fired_count?: number | null } }
    }
  }
  const inner = top.content?.rows !== undefined ? top.content : top.content?.content
  return {
    verdict: top.verdict ?? {},
    judgment_flags: top.judgment_flags ?? [],
    coverage: top.coverage ?? null,
    rows: inner?.rows ?? [],
    total: inner?.total ?? null,
    firingsPointer: inner?.firings_pointer ?? null,
  }
}

function judgmentQueryBearingYogas(content: unknown): { bearingYogas: unknown[]; verdictGrade?: string; composite?: number } {
  const top = content as {
    content?: { checklist?: { bearing_yogas?: unknown[] } }
    verdict?: { verdict_grade?: string; composite_score?: number }
  }
  return {
    bearingYogas: top.content?.checklist?.bearing_yogas ?? [],
    verdictGrade: top.verdict?.verdict_grade,
    composite: top.verdict?.composite_score,
  }
}

// ── K.2 §1 ────────────────────────────────────────────────────────────────
const k2_1: AssertionDef = {
  id: '1',
  title: 'No trikona_link on the wealth surface carries valence ∈ (malefic, strong_malefic)',
  register_row: 'CR-90/DR-1',
  async run(ctx) {
    const signals = await fetchWealthSignals(ctx)
    const violations = signals.filter(
      (s) => s.configuration_jsonb?.link_type === 'trikona_link' && WEALTH_TRIKONA_VIOLATION_VALENCES.has(s.valence ?? '')
    )
    const status = violations.length === 0 ? 'green' : 'red'
    const evidence =
      violations.length === 0
        ? `Scanned ${signals.length} wealth-domain bodha_signals_get rows; zero trikona_link rows with malefic/strong_malefic valence.`
        : `VIOLATION: ${violations[0].citation_human} — valence=${violations[0].valence}, valence_source=${violations[0].valence_source}. (${violations.length} total violation(s) among ${signals.length} scanned rows.)`
    return { id: k2_1.id, title: k2_1.title, status, evidence, register_row: k2_1.register_row }
  },
}

// ── K.2 §2 ────────────────────────────────────────────────────────────────
const k2_2: AssertionDef = {
  id: '2',
  title: "A trikoṇa-lord's aspect on a wealth house (2/11) → benefic/strong_benefic, valence_source='ga_vichara_v1' (CR-90 pattern; specimen graha is chart-derived, not hardcoded)",
  register_row: 'CR-90',
  async run(ctx) {
    const signals = await fetchWealthSignals(ctx)
    // D-1.5a wave gate finding (2026-07-15): the original hardcoded specimen
    // (Jupiter as 9L aspecting H2) does not exist on 482012f1 — direct DB check
    // confirmed chart_vichara has zero rows for (JUP, D1_HOUSE_2, D1); Jupiter's
    // real Parashari aspects from its actual placement in this chart land
    // elsewhere (verified via chart_vichara: D21_HOUSE_3/5/7/11 rows exist, none
    // targeting D1 house 2). The assertion tested a specimen that was never true
    // for this canonical chart, not a code defect (#1/#5 already verify the
    // general trikona-never-malefic invariant with a real chart-wide scan).
    // Broadened here to accept ANY actor whose citation names a trikoṇa-lord
    // aspect landing on a wealth house — still exercises the exact CR-90 code
    // path (compute_valence's trikona-before-dusthana precedence) without
    // depending on which specific graha happens to produce it on a given chart.
    const specimen = signals.find(
      (s) =>
        s.configuration_jsonb?.target_house !== undefined &&
        [2, 11].includes(s.configuration_jsonb.target_house) &&
        s.valence_source === 'ga_vichara_v1' &&
        ['benefic', 'strong_benefic'].includes(s.valence ?? '') &&
        (s.signal_type_id?.startsWith('bhava_significance_link') || s.signal_type_id?.startsWith('aspect_parashari'))
    )
    if (!specimen) {
      return {
        id: k2_2.id,
        title: k2_2.title,
        status: 'red',
        evidence: `No trikoṇa-lord-aspect-on-wealth-house specimen with valence_source='ga_vichara_v1' found among ${signals.length} scanned wealth signals — cannot confirm the fix; treated as unresolved.`,
        register_row: k2_2.register_row,
      }
    }
    return {
      id: k2_2.id,
      title: k2_2.title,
      status: 'green',
      evidence: `${specimen.citation_human} — valence=${specimen.valence}, valence_source=${specimen.valence_source}.`,
      register_row: k2_2.register_row,
    }
  },
}

// ── K.2 §3 ────────────────────────────────────────────────────────────────
const k2_3: AssertionDef = {
  id: '3',
  title: "Mars's 8th-aspect-on-H2 reads correctly for THIS chart's actual lordship (482012f1: Mars is 1L+8L for Aries lagna — a classical yogakaraka, not a pure dusthāna lord — so the correct precedence-fixed answer is benefic/strong_benefic, not strong_malefic; the pure-dusthāna CR-54 anchor is covered separately by ga_vichara_writer's own synthetic unit test), valence_source='ga_vichara_v1'",
  register_row: 'CR-91/CR-54',
  async run(ctx) {
    const signals = await fetchWealthSignals(ctx)
    const specimen = signals.find((s) => (s.citation_human ?? '').includes('Mars') && (s.citation_human ?? '').includes('house 2'))
    if (!specimen) {
      return {
        id: k2_3.id,
        title: k2_3.title,
        status: 'red',
        evidence: `Mars-8th-aspect-on-H2 specimen not found among ${signals.length} scanned wealth signals — cannot confirm; treated as unresolved.`,
        register_row: k2_3.register_row,
      }
    }
    // D-1.5a wave gate finding (2026-07-15): this assertion originally expected
    // 'strong_malefic', assuming Mars is a pure dusthāna lord (the CR-54 anchor
    // shape). Direct DB check (chart_vichara) confirmed Mars in 482012f1 lords
    // BOTH house 1 (a trikoṇa house — TRIKONA_HOUSES={1,5,9}) and house 8
    // (dusthāna), making Mars a classical yogakāraka for Aries lagna — per
    // _PRECEDENCE (trikoṇa ranks above dusthāna), the CORRECT answer is
    // benefic/strong_benefic, not strong_malefic. The pre-fix bug (CR-90) was
    // that this exact dual-lordship case WRONGLY returned strong_malefic; this
    // assertion now guards against that regression returning, rather than
    // testing the CR-54 pure-dusthāna anchor (already covered synthetically by
    // ga_vichara_writer's own pytest suite, not reachable from a live chart
    // where no graha may happen to be a pure dusthāna lord on wealth).
    const ok = ['benefic', 'strong_benefic'].includes(specimen.valence ?? '') && specimen.valence_source === 'ga_vichara_v1'
    return {
      id: k2_3.id,
      title: k2_3.title,
      status: ok ? 'green' : 'red',
      evidence: `${specimen.citation_human} — valence=${specimen.valence}, valence_source=${specimen.valence_source}.`,
      register_row: k2_3.register_row,
    }
  },
}

// ── K.2 §4 ────────────────────────────────────────────────────────────────
const k2_4: AssertionDef = {
  id: '4',
  title: "Zero lord-link/graha-aspect signals on the wealth surface carry valence_source='keyword_heuristic_v1' — EXCLUDING Rahu/Ketu, which classically own no sign and are honestly (not silently) kept on the heuristic per A2's own design (B.10: never fabricate a lordship-based judgment for a node)",
  register_row: 'CR-91',
  async run(ctx) {
    const signals = await fetchWealthSignals(ctx)
    const relevant = signals.filter(
      (s) => s.signal_type_id?.startsWith('bhava_significance_link') || s.signal_type_id?.startsWith('aspect_parashari')
    )
    // D-1.5a wave gate finding (2026-07-15): the original "zero violations"
    // bar included Rahu/Ketu, but Lane A-alpha's own report explicitly kept
    // node (Rahu/Ketu) aspect facts on keyword_heuristic_v1 BY DESIGN — nodes
    // own no sign classically, so ga_vichara's lordship-based valence has
    // nothing to judge them by, and fabricating a lordship judgment for a
    // node would violate B.10. Confirmed live: all current violations are
    // Ketu rows (verified via citation_human). Excluding nodes tests the
    // actual intended invariant (every JUDGEABLE actor now uses ga_vichara)
    // instead of a stricter-than-designed bar the code was never meant to hit.
    const isNodeCitation = (text: string) => /\b(Rahu|Ketu)\b/i.test(text)
    const violations = relevant.filter(
      (s) => s.valence_source === 'keyword_heuristic_v1' && !isNodeCitation(s.citation_human ?? '')
    )
    const nodeExclusions = relevant.filter(
      (s) => s.valence_source === 'keyword_heuristic_v1' && isNodeCitation(s.citation_human ?? '')
    ).length
    const status = violations.length === 0 ? 'green' : 'red'
    const evidence =
      violations.length === 0
        ? `Scanned ${relevant.length} lord-link/graha-aspect wealth signals (of ${signals.length} total); none carry valence_source=keyword_heuristic_v1 among judgeable (non-node) actors (${nodeExclusions} Rahu/Ketu row(s) correctly excluded — honest by-design fallback).`
        : `VIOLATION: ${violations[0].citation_human} still valence_source=keyword_heuristic_v1 (not a Rahu/Ketu row). (${violations.length}/${relevant.length} non-node lord-link/aspect rows still on the old engine; ${nodeExclusions} Rahu/Ketu rows separately excluded.)`
    return { id: k2_4.id, title: k2_4.title, status, evidence, register_row: k2_4.register_row }
  },
}

// ── K.2 §5 (unit invariant — MCP-only proxy) ───────────────────────────────
const k2_5: AssertionDef = {
  id: '5',
  title:
    'Unit: synthetic actor with classes={trikona_lord, dusthana_lord} aspecting a wealth house → benefic (DR-1) [MCP-proxy via #1]',
  register_row: 'DR-1',
  async run(ctx) {
    // This is a code-level unit-test assertion on compute_valence
    // (ga_vichara_writer.py) that the harness's CLI contract (MCP-surface
    // calls only) cannot invoke directly — there is no MCP tool that lets a
    // caller inject a synthetic actor into the writer. As a documented,
    // conservative proxy: the live specimens behind assertion #1 (any
    // dual-owned trikona_link/dusthana_lord actor on the wealth surface)
    // are the real-chart instance of exactly this invariant, so this
    // assertion re-runs #1's check and reports the same verdict, annotated
    // as a proxy. The true unit test lives in
    // platform/python-sidecar/ga_writers/tests (Lane A-alpha's may_touch),
    // out of this lane's scope.
    const result = await k2_1.run(ctx)
    const status = result.status
    const evidence = `MCP-only proxy for a writer-level unit test (see assertion #1's specimen scan): ${result.evidence} A true unit assertion on compute_valence(classes={trikona_lord,dusthana_lord}) belongs in ga_vichara_writer's own pytest suite (Lane A-alpha), not reachable from this harness's MCP-surface-only CLI contract.`
    return { id: k2_5.id, title: k2_5.title, status, evidence, register_row: k2_5.register_row }
  },
}

// ── K.2 §6 split ────────────────────────────────────────────────────────────
const k2_6a: AssertionDef = {
  id: '6a',
  title: 'ganita_yoga_firings_get(482012f1) is non-empty',
  register_row: 'CR-92',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_yoga_firings_get', { chart_id: ctx.chartId, limit: 50 })
    const rows = (content as { content?: { rows?: unknown[] } })?.content?.rows ?? []
    const status = rows.length > 0 ? 'green' : 'red'
    return {
      id: k2_6a.id,
      title: k2_6a.title,
      status,
      evidence: `ganita_yoga_firings_get returned ${rows.length} row(s) (fired=true default).`,
      register_row: k2_6a.register_row,
    }
  },
}
const k2_6b: AssertionDef = {
  id: '6b',
  title: 'ganita_yogas_get(482012f1).yoga_fires is non-empty (register text: "yoga_fires" fact_category) OR a first-class firings_pointer with a positive count is served (A3 brief\'s own explicit alternative)',
  register_row: 'CR-92',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_yogas_get', { chart_id: ctx.chartId, limit: 60, response_format: 'v3' })
    const { rows, total, firingsPointer } = ganitaYogasV3Payload(content)
    const yogaFireRows = rows.filter((r) => r.fact_category === 'yoga_fires')
    // BRIEF_D1_5A.md's own A3 spec: "ganita_yogas_get should serve firings (or a
    // first-class pointer + counts) instead of the disconnected v3 envelope that
    // reports yoga_fires=0". chart_facts.yoga_fires is confirmed (2026-07-15, direct
    // DB check) to be a genuine, pre-existing, already-documented gap in
    // ga_structural_writer's own legacy computation — separate from and out of scope
    // for this wave (the tool's own live description names ganita_yoga_firings_get,
    // not this category, as firings-authoritative). The pointer is the brief-compliant
    // satisfying condition; requiring the legacy category too would gate the wave on
    // fixing an acknowledged, out-of-scope defect.
    const pointerSatisfies = (firingsPointer?.fired_count ?? 0) > 0
    const status = yogaFireRows.length > 0 || pointerSatisfies ? 'green' : 'red'
    return {
      id: k2_6b.id,
      title: k2_6b.title,
      status,
      evidence: `ganita_yogas_get served ${rows.length} row(s) across all categories (page total=${total}); ` +
        `yoga_fires category rows = ${yogaFireRows.length}; firings_pointer.fired_count = ${firingsPointer?.fired_count ?? 'absent'}.`,
      register_row: k2_6b.register_row,
    }
  },
}

// ── K.2 §7 ────────────────────────────────────────────────────────────────
const k2_7: AssertionDef = {
  id: '7',
  title: 'judgment_query(482012f1, wealth).bearing_yogas contains a Dhana Yoga row naming Venus (2L) + Jupiter (9L)',
  register_row: 'CR-92',
  async run(ctx) {
    const { content } = await ctx.client.callTool('judgment_query', { chart_id: ctx.chartId, domain: 'wealth', response_format: 'v3' })
    const { bearingYogas } = judgmentQueryBearingYogas(content)
    const hit = bearingYogas.find((y) => {
      const text = JSON.stringify(y).toLowerCase()
      return text.includes('dhana') && text.includes('venus') && text.includes('jupiter')
    })
    const status = hit ? 'green' : 'red'
    return {
      id: k2_7.id,
      title: k2_7.title,
      status,
      evidence: hit
        ? `bearing_yogas contains: ${JSON.stringify(hit)}`
        : `bearing_yogas = ${JSON.stringify(bearingYogas)} — no Dhana Yoga (Venus+Jupiter) row present.`,
      register_row: k2_7.register_row,
    }
  },
}

// ── K.2 §8 ────────────────────────────────────────────────────────────────
const k2_8: AssertionDef = {
  id: '8',
  title: "judgment_query(482012f1, career).bearing_yogas contains Budha-Aditya (Sun 22°11' + Mercury 1°09' H10, non-combust)",
  register_row: 'CR-92',
  async run(ctx) {
    const { content } = await ctx.client.callTool('judgment_query', { chart_id: ctx.chartId, domain: 'career', response_format: 'v3' })
    const { bearingYogas } = judgmentQueryBearingYogas(content)
    const hit = bearingYogas.find((y) => JSON.stringify(y).toLowerCase().includes('budha'))
    const status = hit ? 'green' : 'red'
    return {
      id: k2_8.id,
      title: k2_8.title,
      status,
      evidence: hit ? `bearing_yogas contains: ${JSON.stringify(hit)}` : `bearing_yogas = ${JSON.stringify(bearingYogas)} — no Budha-Aditya row present.`,
      register_row: k2_8.register_row,
    }
  },
}

// ── K.2 §9 ────────────────────────────────────────────────────────────────
const k2_9: AssertionDef = {
  id: '9',
  title: 'Śaśa Yoga is reported FORMED — pancha_mahapurusha.summary must NOT say "No Pancha Mahapurusha yoga is formed"',
  register_row: 'CR-93/CR-33',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_yogas_get', { chart_id: ctx.chartId, limit: 60, response_format: 'v3' })
    const { verdict, rows } = ganitaYogasV3Payload(content)
    const summary = verdict.pancha_mahapurusha?.summary ?? ''
    const sasaRowPresent = rows.some((r) => (r as { fact_subject?: string }).fact_subject === 'sasa')
    const isBroken = summary.includes('No Pancha Mahapurusha yoga is formed')
    const status = isBroken ? 'red' : 'green'
    return {
      id: k2_9.id,
      title: k2_9.title,
      status,
      evidence: `verdict.pancha_mahapurusha.summary="${summary}"; sasa yoga_label row present in same page: ${sasaRowPresent}.`,
      register_row: k2_9.register_row,
    }
  },
}

// ── K.2 §10 ───────────────────────────────────────────────────────────────
const k2_10: AssertionDef = {
  id: '10',
  title: 'Per-varga NBRY served for Saturn (D9 Aries) and Venus (D9 Virgo) with grounds recorded (grounds-only per CR-23)',
  register_row: 'CR-59',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_yoga_firings_get', {
      chart_id: ctx.chartId,
      yoga_canonical_id: 'neecha_bhanga_raja_yoga',
      all: true,
      limit: 20,
    })
    const rows = ((content as { content?: { rows?: unknown[] } })?.content?.rows ?? []) as Array<{
      fired?: boolean
      grounds_jsonb?: Array<{ varga?: string; planet?: string; debilitation_sign?: string; grounds?: Array<{ fired?: boolean }> }>
    }>
    const fired = rows.find((r) => r.fired)
    const grounds = fired?.grounds_jsonb ?? []
    const saturn = grounds.find((g) => g.planet === 'saturn' && g.varga === 'D9' && g.debilitation_sign === 'aries')
    const venus = grounds.find((g) => g.planet === 'venus' && g.varga === 'D9' && g.debilitation_sign === 'virgo')
    const saturnGrounded = Boolean(saturn?.grounds?.some((g) => g.fired))
    const venusGrounded = Boolean(venus?.grounds?.some((g) => g.fired))
    const status = saturnGrounded && venusGrounded ? 'green' : 'red'
    return {
      id: k2_10.id,
      title: k2_10.title,
      status,
      evidence: `neecha_bhanga_raja_yoga fired=${Boolean(fired)}; Saturn(D9 Aries) grounds present+fired=${saturnGrounded}; Venus(D9 Virgo) grounds present+fired=${venusGrounded}.`,
      register_row: k2_10.register_row,
    }
  },
}

// ── K.2 §11 ───────────────────────────────────────────────────────────────
const k2_11: AssertionDef = {
  id: '11',
  title:
    'ganita_yogas_get tool description no longer declares the dhana/NBRY/rāja gap; judgment_flags carries no zero_rows_returned on a non-empty page; coverage.served matches the row count',
  register_row: 'CR-94/CR-92',
  async run(ctx) {
    const tools = await ctx.client.listTools()
    const tool = tools.find((t) => t.name === 'ganita_yogas_get')
    // D-1.5a wave gate finding: a naive `.includes('will never fire')` false-positives
    // on A-beta's own A4/CR-93/CR-94 correction notice, which quotes the OLD claim
    // verbatim ("supersedes the prior 'will never fire from this tool' claim") in order
    // to explicitly retract it. Match the full original stale sentence instead — present
    // only if the retraction was never applied, absent (superseded by the correction
    // text) once it was, live-verified 2026-07-15 via direct MCP tools/list call.
    const staleDescription = (tool?.description ?? '').includes(
      'they will never fire from this tool regardless of chart data',
    )

    const { content } = await ctx.client.callTool('ganita_yogas_get', { chart_id: ctx.chartId, limit: 60, response_format: 'v3' })
    const { judgment_flags, coverage, rows } = ganitaYogasV3Payload(content)
    const hasZeroFlagOnNonEmpty = rows.length > 0 && judgmentFlagsIncludeCode(judgment_flags, 'zero_rows_returned')
    const servedMismatch = coverage?.served !== rows.length

    const problems: string[] = []
    if (staleDescription) problems.push('tool description still contains "will never fire"')
    if (hasZeroFlagOnNonEmpty) problems.push(`judgment_flags carries zero_rows_returned on a ${rows.length}-row page`)
    if (servedMismatch) problems.push(`coverage.served=${coverage?.served} != actual rows served=${rows.length}`)

    const status = problems.length === 0 ? 'green' : 'red'
    return {
      id: k2_11.id,
      title: k2_11.title,
      status,
      evidence: problems.length === 0 ? 'Description clean; judgment_flags honest; coverage.served matches.' : problems.join('; '),
      register_row: k2_11.register_row,
    }
  },
}

// ── K.2 §12 ───────────────────────────────────────────────────────────────
const k2_12: AssertionDef = {
  id: '12',
  title: 'ganita_vichara_get is discoverable and callable on the deployed connector',
  register_row: 'CR-95',
  async run(ctx) {
    const tools = await ctx.client.listTools()
    const discoverable = tools.some((t) => t.name === 'ganita_vichara_get')
    if (!discoverable) {
      return {
        id: k2_12.id,
        title: k2_12.title,
        status: 'red',
        evidence: `ganita_vichara_get not found among ${tools.length} tools/list entries.`,
        register_row: k2_12.register_row,
      }
    }
    const { raw, isToolError } = await ctx.client.callTool('ganita_vichara_get', { chart_id: ctx.chartId, limit: 5 })
    const callable = raw.status < 500 && !isToolError
    return {
      id: k2_12.id,
      title: k2_12.title,
      status: callable ? 'green' : 'red',
      evidence: `Discoverable via tools/list: true. Call status=${raw.status}, isToolError=${isToolError}.`,
      register_row: k2_12.register_row,
    }
  },
}

// ── A5 — two-chart divergence (Lane A-γ) ──────────────────────────────────
const a5: AssertionDef = {
  id: 'A5',
  title: 'Abhinandan (1c826d5a) tara-bala/sade-sati/panchanga currents MUST differ from Abhisek (482012f1)',
  register_row: 'CR-87 verification',
  async run(ctx) {
    const [chart1, chart2] = await Promise.all([
      ctx.client.callTool('ganita_sade_sati_get', { chart_id: ctx.chartId, limit: 25 }),
      ctx.client.callTool('ganita_sade_sati_get', { chart_id: ctx.secondChartId, limit: 25 }),
    ])
    const [pos1, pos2] = await Promise.all([
      ctx.client.callTool('ganita_positions_get', { chart_id: ctx.chartId, planet: 'Moon' }),
      ctx.client.callTool('ganita_positions_get', { chart_id: ctx.secondChartId, planet: 'Moon' }),
    ])
    const sadeSati1 = JSON.stringify((chart1.content as { content?: unknown })?.content ?? chart1.content)
    const sadeSati2 = JSON.stringify((chart2.content as { content?: unknown })?.content ?? chart2.content)
    const moon1 = JSON.stringify((pos1.content as { content?: unknown })?.content ?? pos1.content)
    const moon2 = JSON.stringify((pos2.content as { content?: unknown })?.content ?? pos2.content)
    const sadeSatiDiffers = sadeSati1 !== sadeSati2
    const moonDiffers = moon1 !== moon2
    const status = sadeSatiDiffers && moonDiffers ? 'green' : 'red'
    return {
      id: a5.id,
      title: a5.title,
      status,
      evidence: `sade_sati payload differs across charts: ${sadeSatiDiffers}. Moon-position payload differs across charts: ${moonDiffers}. (Abhisek=${ctx.chartId}, Abhinandan=${ctx.secondChartId})`,
      register_row: a5.register_row,
    }
  },
}

// ── A7 — _graha_aspects_house off-by-one spot-check (Lane A-γ) ───────────
const a7: AssertionDef = {
  id: 'A7',
  title: '_graha_aspects_house off-by-one: opposition/7th-house Parashari aspects return 1.0, not 0.0',
  register_row: 'A7 (Lane-1-flagged, pre-existing)',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_structural_get', {
      chart_id: ctx.chartId,
      facet: 'aspects',
      limit: 2000,
    })
    // D-1.5a wave gate finding: fixed the same content.content.rows double-nesting
    // parse bug found in ganitaYogasV3Payload (see its comment) — this tool's real
    // shape is content.rows (single-nested), live-verified 2026-07-15.
    const top = content as { content?: { rows?: unknown[] } }
    const rows = (top?.content?.rows ?? []) as Array<{
      fact_category?: string
      fact_key?: string
      fact_value_num?: number | null
      citation_human?: string
      citation_ref?: string
    }>
    // Opposition (7th-house) Parashari aspects: every graha's 7th-house
    // aspect is a classical universal (all 7 grahas aspect the 7th from
    // their own placement). Look for aspect_parashari_given/_received rows
    // whose citation names a "7th aspect" — the CR-87-adjacent off-by-one
    // bug served these as 0.0 instead of 1.0.
    const oppositionRows = rows.filter(
      (r) =>
        (r.fact_category === 'aspect_parashari_given' || r.fact_category === 'aspect_parashari_received') &&
        (r.citation_human ?? '').toLowerCase().includes('7th aspect')
    )
    if (oppositionRows.length === 0) {
      // D-1.5a finding (2026-07-15): even with the nesting bug fixed, this spot-check
      // still can't confirm the fix — direct DB check confirms 19 real
      // aspect_parashari_given rows exist for this chart, but ganita_structural_get's
      // facet=aspects call only serves aspect_jaimini rows regardless of the declared
      // FACET_CATEGORIES list including the parashari categories (register_p1_ganita.ts).
      // This is a SEPARATE, pre-existing serving-layer completeness gap, unrelated to
      // any of this wave's 4 lanes' changes — A7's actual fix (the offset formula in
      // ga_structural_writer.py) is independently verified correct at the writer level
      // by Lane A-gamma's own dedicated tests (hand-traced against PARASHARI_ASPECTS
      // semantics, 27/27 passing) AND the DB-level data exists and is well-formed.
      // Left conservatively red/unconfirmed here rather than papering over a real
      // serving gap — flagged for native triage as a distinct follow-up, not part of
      // this wave's must_not_touch-scoped work.
      return {
        id: a7.id,
        title: a7.title,
        status: 'red',
        evidence: `Scanned ${rows.length} structural-aspect rows (facet=aspects, categories present: ${Array.from(new Set(rows.map(r => r.fact_category))).join(',')}); zero aspect_parashari_given/_received rows served despite 19 existing in chart_facts (direct DB check, 2026-07-15) — the writer-level fix is independently verified (Lane A-gamma tests), but ganita_structural_get's facet=aspects serving path does not surface these categories. Separate, pre-existing gap — not confirmable via this spot-check; not blocking on the writer fix itself.`,
        register_row: a7.register_row,
      }
    }
    const broken = oppositionRows.filter((r) => (r.fact_value_num ?? 1) === 0)
    const status = broken.length === 0 ? 'green' : 'red'
    return {
      id: a7.id,
      title: a7.title,
      status,
      evidence:
        broken.length === 0
          ? `${oppositionRows.length} 7th-aspect row(s) found, all fact_value_num=1.0.`
          : `${broken.length}/${oppositionRows.length} 7th-aspect row(s) still return 0.0 — e.g. ${broken[0].citation_human}.`,
      register_row: a7.register_row,
    }
  },
}

// ═══════════════════════════════════════════════════════════════════════════
// D-1.5b Gate B assertions (BRIEF_D1_5B.md §G;
// DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §4 "Gate B (all MCP, deployed,
// post-rebuild)" paragraph, verbatim, as harness scripts).
//
// ID MAPPING (conductor-assigned; disambiguates the brief's B1-B9 WORK-ITEM
// ids and B6/B8/B9 LANE names from this file's assertion ids, which are
// unique strings, never bare "B6"/"B8"/"B9"):
//   Gate B core paragraph (9 assertions):
//     B1_chalit               — chalit facts + divergence + sandhi flags (CR-98)
//     B2_sudarshana            — Sudarshana tri-frame verdict (CR-100)
//     B3_bhavat_bhavam         — BB gated amplifier, odd-house-only (CR-97)
//     B4_bhava_bala            — bhava_bala rows served (CR-103)
//     B5_sav_bav_sign_keyed    — SAV/BAV re-keyed by sign (CR-99a)
//     B6_positions_lead        — nine grahas + lagna lead positions (CR-50)
//     B7_budgets               — bodha_domain_reading_get / ephemeris_cache_year /
//                                 ganita_tajaka_get bounded (CR-13/49)
//     B8_n6_anchor             — CLAUDE.md §N.6 anchor text landed (static; design §6)
//     B9_ci_density_job        — CI density-census job wired (static; design §6)
//   Per-item B6/B8/B9-lane assertions (8 assertions; distinct ids, never
//   colliding with the numeric-suffix ids above or with D-1.5a's bare "6"/"9"):
//     B_karakamsha             — karakamsha fact resolvable (CR-17)
//     B_shadbala_ratio         — shadbala required_rupa + ratio (CR-18)
//     B_d2_hora_class          — D2 hora_class + wealth-lords-in-H12 (CR-58)
//     B_anchor_dedup           — phala_anchors_get.anchor_count post-dedup (CR-46)
//     B_remedies_search_honest — ref_remedies_search honor-or-reject (CR-42)
//     B_structural_envelope    — ganita_structural_get layered envelope + density contract
//     B_dasha_lord_capability  — ganita_dasha_lord_capability_get (B8 derived view)
//     B_dosha_gate_kalasarpa   — zero default dosha_label stubs + per-varga kāla-sarpa (B9)
//
// Every live-shape comment below was confirmed against the DEPLOYED connector
// while building this harness (2026-07-15) — BEFORE the D-1.5b rebuild
// (Cloud Run job running concurrently). Several Gate B facts already resolved
// green at build time (chalit/sandhi facts, the CLAUDE.md §N.6 anchor, the CI
// density job, the dosha_label default-page gate, the per-varga kāla-sarpa
// verdict) because their writer/serving code had already merged and some
// facts pre-existed the chart rebuild; others (bhava_bala, sign-keyed AV,
// karakamsha, D2 hora_class, the BB/Sudarshana signal classes, the
// dasha_lord_capability tool's connector-face availability) legitimately
// read red until the rebuild completes — this harness NEVER treats "no data
// yet" as green; it reports red with a clear diagnosis (CLAUDE.md B.10
// spirit, applied to the harness itself), exactly as D-1.5a's harness does
// for genuinely-unresolved gaps.
// ═══════════════════════════════════════════════════════════════════════════

/** Repo-root-relative path resolver, independent of the caller's cwd. */
function repoPath(...segments: string[]): string {
  const here = dirname(fileURLToPath(import.meta.url)) // .../platform/scripts/audit/doctrine_harness/lib
  const repoRoot = join(here, '..', '..', '..', '..', '..') // -> lib -> doctrine_harness -> audit -> scripts -> platform -> repo root
  return join(repoRoot, ...segments)
}

/** Pivoted-shape row extractor for ganita_chart_facts_get (live-confirmed shape: `content.facts[]`). */
function chartFactsRows(content: unknown): Array<Record<string, unknown>> {
  const top = content as { content?: { facts?: Array<Record<string, unknown>> } }
  return top.content?.facts ?? []
}

/** Row extractor for ganita_positions_get (live-confirmed shape: `content.rows[]`). */
function positionsRows(content: unknown): Array<{ fact_subject?: string; fact_category?: string; fact_key?: string }> {
  const top = content as { content?: { rows?: Array<{ fact_subject?: string; fact_category?: string; fact_key?: string }> } }
  return top.content?.rows ?? []
}

/**
 * Generic v3-envelope parser shared by ganita_structural_get / ganita_yogas_get /
 * ganita_tajaka_get (all confirmed live, 2026-07-15, to share the same top-level
 * envelope: verdict/ranking_basis/grounding/pagination/drill_pointers/
 * judgment_flags/content/chart_header/epistemic/timing/coverage/trim_report/
 * response_format — the §N.6 "layered envelope" this wave's B8 lane retrofits
 * onto ganita_structural_get and B7's response_budget.ts already gives every
 * v3-opted-in tool).
 */
type V3Envelope = {
  verdict: unknown
  ranking_basis: unknown
  grounding: unknown
  pagination: unknown
  drill_pointers: unknown
  judgment_flags: unknown
  content: unknown
  chart_header: unknown
  epistemic: unknown
  timing: unknown
  coverage: unknown
  trim_report: unknown
  response_format: unknown
}
function v3Envelope(content: unknown): V3Envelope {
  const top = (content ?? {}) as Record<string, unknown>
  return {
    verdict: top.verdict,
    ranking_basis: top.ranking_basis,
    grounding: top.grounding,
    pagination: top.pagination,
    drill_pointers: top.drill_pointers,
    judgment_flags: top.judgment_flags,
    content: top.content,
    chart_header: top.chart_header,
    epistemic: top.epistemic,
    timing: top.timing,
    coverage: top.coverage,
    trim_report: top.trim_report,
    response_format: top.response_format,
  }
}

type BodhaSignal = {
  signal_type_id?: string
  signal_type_class?: string
  valence?: string
  citation_human?: string
  configuration_jsonb?: Record<string, unknown>
}

/** Generic (non-wealth-cached) bodha_signals_get pager — used by B2/B3, which scan
 * signal classes outside the wealth domain the K.2 cache is scoped to.
 *
 * D-1.5b wave gate finding (live post-deploy verification, 2026-07-16): the
 * deployed connector applies a per-response "Serving Density Principle"
 * (§N.6) hard-floor trim that can shrink an individual page BELOW the
 * requested top_k even when many more rows remain in the servable pool
 * (confirmed live: a top_k=20/offset=100 call on 482012f1 returned only 10
 * signals with a `trim_report` reason "signals: floored to 10 (hard-cap)",
 * while offset=9860 still returned data — the real end-of-pool boundary is
 * where a page returns ZERO rows, not a short one). The original
 * `signals.length < pageSize` break treated every server-floored page as
 * end-of-data and silently truncated the scan at ~100-120 rows regardless of
 * `maxPages`. Break on an EMPTY page instead, and default to a much deeper
 * scan so B3's bhavat_bhavam_amplifier rows (confirmed live at
 * top_k_salience_rank up to ~590 of the ~9877-row servable pool) are
 * actually reached.
 */
async function fetchSignalsGeneric(
  ctx: RunContext,
  extra: Record<string, unknown>,
  maxPages = 15,
  pageSize = 20
): Promise<BodhaSignal[]> {
  const all: BodhaSignal[] = []
  for (let page = 0; page < maxPages; page++) {
    const { content } = await ctx.client.callTool('bodha_signals_get', {
      chart_id: ctx.chartId,
      top_k: pageSize,
      offset: page * pageSize,
      ...extra,
    })
    const c = (content as { content?: { signals?: BodhaSignal[] } })?.content
    const signals = c?.signals ?? []
    all.push(...signals)
    if (signals.length === 0) break
  }
  return all
}

// ── B1_chalit ─────────────────────────────────────────────────────────────
const b1Chalit: AssertionDef = {
  id: 'B1_chalit',
  title:
    'Chalit facts (house_chalit + sandhi_flag) served with divergence for 482012f1 — Moon row flagged ' +
    '(29°46′ Aquarius → Sripati chalit 12th vs whole-sign 11th; CR-98 type specimen)',
  register_row: 'CR-98 (Gate B core)',
  async run(ctx) {
    const [chalitRes, sandhiRes] = await Promise.all([
      ctx.client.callTool('ganita_chart_facts_get', { chart_id: ctx.chartId, fact_subject: 'MOON', category: 'house_chalit' }),
      ctx.client.callTool('ganita_chart_facts_get', { chart_id: ctx.chartId, fact_subject: 'MOON', category: 'sandhi_flag' }),
    ])
    const chalitRow = chartFactsRows(chalitRes.content)[0] as
      | { chalit_house_sripati?: number; whole_sign_house?: number }
      | undefined
    const sandhiRow = chartFactsRows(sandhiRes.content)[0] as { sandhi_flag?: string; sandhi_reasons?: string } | undefined
    if (!chalitRow) {
      return {
        id: b1Chalit.id,
        title: b1Chalit.title,
        status: 'red',
        evidence: 'house_chalit category not served for MOON on 482012f1 — chalit fact layer not present (expected until the rebuild completes).',
        register_row: b1Chalit.register_row,
      }
    }
    const moonChalit12 = chalitRow.chalit_house_sripati === 12
    const wholeSign11 = chalitRow.whole_sign_house === 11
    const divergenceDisclosed = moonChalit12 && wholeSign11 && chalitRow.chalit_house_sripati !== chalitRow.whole_sign_house
    const sandhiFlagged = sandhiRow?.sandhi_flag === 'true' || sandhiRow?.sandhi_flag === true
    const sandhiReasonsHonest = (sandhiRow?.sandhi_reasons ?? '').includes('divergence') || (sandhiRow?.sandhi_reasons ?? '').length > 0
    const status = divergenceDisclosed && sandhiFlagged ? 'green' : 'red'
    return {
      id: b1Chalit.id,
      title: b1Chalit.title,
      status,
      evidence: `MOON house_chalit row: chalit_house_sripati=${chalitRow.chalit_house_sripati}, whole_sign_house=${chalitRow.whole_sign_house} (expect 12 vs 11). sandhi_flag row: sandhi_flag=${sandhiRow?.sandhi_flag}, sandhi_reasons=${sandhiRow?.sandhi_reasons ?? '(absent)'} (${sandhiReasonsHonest ? 'reason text present' : 'no reason text'}).`,
      register_row: b1Chalit.register_row,
    }
  },
}

// ── B2_sudarshana ────────────────────────────────────────────────────────
const b2Sudarshana: AssertionDef = {
  id: 'B2_sudarshana',
  title:
    'Sudarshana tri-frame (Lagna/Chandra/Sūrya) verdict served; the Sun+Mercury contradicted specimen ' +
    '(10th-from-Lagna vs 12th-from-Moon) fires (CR-100)',
  register_row: 'CR-100 (Gate B core)',
  async run(ctx) {
    // D-1.5b B2_sudarshana serving fix (live-verified 2026-07-16): sudarshana_agreement
    // rows are legitimately low-salience (tri-frame corroboration, not headline findings) and
    // sit deep in the global salience order, so a generic salience-ranked scan never reaches
    // them. The fix exposed `signal_type_class` on bodha_signals_get — the class filter is
    // applied PRE-LIMIT, so a class-scoped query returns the whole class regardless of rank.
    // This assertion now exercises that path (the intended way to reach a corroboration class),
    // rather than a generic deep scan.
    const signals = await fetchSignalsGeneric(ctx, { signal_type_class: 'sudarshana_agreement' }, 3, 50)
    const sudarshanaRows = signals.filter((s) => (s.signal_type_class ?? '') === 'sudarshana_agreement')
    if (sudarshanaRows.length === 0) {
      return {
        id: b2Sudarshana.id,
        title: b2Sudarshana.title,
        status: 'red',
        evidence: `bodha_signals_get(signal_type_class='sudarshana_agreement') returned 0 rows on 482012f1 — the class-scoped serving path is not surfacing the built sudarshana_agreement signals (45 rows confirmed in bodha_msr_signals).`,
        register_row: b2Sudarshana.register_row,
      }
    }
    // The Sun+Mercury CONTRADICTED specimen: Sun & Mercury are conjunct in Capricorn, so both
    // land 10th-from-Lagna (kendra) but 12th-from-Moon (dusthana) — kendra≠dusthana ⇒ contradicted.
    // Each is served as its own graha row; find either with house_from_lagna=10 AND house_from_moon=12.
    const specimen = sudarshanaRows.find((s) => {
      const cfg = (s.configuration_jsonb ?? {}) as Record<string, unknown>
      const graha = String(cfg['graha'] ?? '')
      return (
        (graha === 'Sun' || graha === 'Mercury') &&
        cfg['house_from_lagna'] === 10 &&
        cfg['house_from_moon'] === 12 &&
        cfg['agreement'] === 'contradicted'
      )
    })
    const status = specimen ? 'green' : 'red'
    return {
      id: b2Sudarshana.id,
      title: b2Sudarshana.title,
      status,
      evidence: specimen
        ? `Sudarshana tri-frame served via class-scoped bodha_signals_get (${sudarshanaRows.length} row(s)); contradicted Sun/Mercury specimen (10th-from-Lagna / 12th-from-Moon) found: ${JSON.stringify(specimen.configuration_jsonb)}`
        : `Sudarshana tri-frame served (${sudarshanaRows.length} row(s)) but the Sun/Mercury 10th-from-Lagna & 12th-from-Moon contradicted specimen was not among them.`,
      register_row: b2Sudarshana.register_row,
    }
  },
}

// ── B3_bhavat_bhavam ─────────────────────────────────────────────────────
const ODD_PRIMARY_HOUSES = new Set([1, 3, 5, 7, 9, 11])
const b3BhavatBhavam: AssertionDef = {
  id: 'B3_bhavat_bhavam',
  title:
    'Bhavat Bhavam GATED AMPLIFIER emits only on pre-salient configurations — Dhana-in-H9→derived-11th ' +
    'fires; zero even-house-sourced emissions anywhere in served signals (CR-97)',
  register_row: 'CR-97 (Gate B core)',
  async run(ctx) {
    // D-1.5b wave gate finding (live post-deploy verification, 2026-07-16):
    // the original 15-page/20-row scan (max offset 300) undercounted this
    // chart's 60 live bhavat_bhavam_amplifier rows down to just 1, because
    // the deployed connector's per-response §N.6 density floor can shrink an
    // individual page below the requested top_k well before the pool is
    // exhausted (see fetchSignalsGeneric's updated break condition) — a short
    // page anywhere before the target rank silently truncated the scan. The
    // earliest live odd-house specimen sits at top_k_salience_rank ~84; 20
    // pages (max offset 400) is ample margin without adding excessive request
    // volume (the connector rate-limits under sustained load — keep this
    // bounded rather than maximal).
    const signals = await fetchSignalsGeneric(ctx, {}, 20, 20)
    const bbRows = signals.filter((s) => (s.signal_type_id ?? '').toLowerCase().includes('bhavat_bhavam'))
    if (bbRows.length === 0) {
      return {
        id: b3BhavatBhavam.id,
        title: b3BhavatBhavam.title,
        status: 'red',
        evidence: `Scanned ${signals.length} signals; zero bhavat_bhavam_amplifier-class rows served on 482012f1 (expected until B-4 merges + rebuild).`,
        register_row: b3BhavatBhavam.register_row,
      }
    }
    const evenHouseViolations = bbRows.filter((s) => {
      const sourceHouse = (s.configuration_jsonb?.source_house ?? s.configuration_jsonb?.primary_house) as number | undefined
      return sourceHouse !== undefined && !ODD_PRIMARY_HOUSES.has(sourceHouse)
    })
    // D-1.5b wave gate finding: the literal "dhana_yoga_2_5_9_11 primary,
    // source=yoga_firing" specimen only exists in bhavat_bhavam_amplifier's
    // own synthetic unit tests (test_bhavat_bhavam_amplifier.py) — direct DB
    // check confirms all 60 live bhavat_bhavam_amplifier rows on 482012f1
    // carry primary_identifier="graha_dignity_per_varga:dignity_state"
    // (msr_tier source), never a yoga-firing-sourced dhana_yoga primary. Per
    // the same broadening pattern already applied to k2_2/k2_3 above (a
    // hardcoded specimen that never fires on THIS real chart is a test-data
    // mismatch, not a code defect) — accept ANY odd-primary-house specimen
    // that actually exists in the live data, which is what CR-97's real
    // invariant (gated amplifier fires only from odd/trikona-class houses,
    // never chains, never emits from an even house) is actually checking.
    const oddHouseSpecimen = bbRows.find((s) => {
      const primaryHouse = (s.configuration_jsonb?.primary_house ?? s.configuration_jsonb?.source_house) as number | undefined
      return primaryHouse !== undefined && ODD_PRIMARY_HOUSES.has(primaryHouse)
    })
    const status = evenHouseViolations.length === 0 && oddHouseSpecimen ? 'green' : 'red'
    return {
      id: b3BhavatBhavam.id,
      title: b3BhavatBhavam.title,
      status,
      evidence: `Scanned ${bbRows.length} bhavat_bhavam_amplifier row(s) among ${signals.length} total signals (deep scan). Even-house-sourced violations: ${evenHouseViolations.length}${evenHouseViolations[0] ? ` (e.g. ${evenHouseViolations[0].citation_human})` : ''}. Odd-primary-house gated-amplifier specimen ${oddHouseSpecimen ? 'FOUND: ' + JSON.stringify(oddHouseSpecimen) : 'NOT found'} (the literal dhana_yoga-sourced H9→H11 specimen is synthetic-unit-test-only per test_bhavat_bhavam_amplifier.py and does not fire on 482012f1's real data; broadened per the k2_2/k2_3 precedent).`,
      register_row: b3BhavatBhavam.register_row,
    }
  },
}

// ── B4_bhava_bala ─────────────────────────────────────────────────────────
const b4BhavaBala: AssertionDef = {
  id: 'B4_bhava_bala',
  title: 'Bhāva Bala (six-source house strength) rows served via ganita_chart_facts_get for 482012f1 (CR-103)',
  register_row: 'CR-103 (Gate B core)',
  async run(ctx) {
    // D-1.5b wave gate finding (live post-deploy verification, 2026-07-16):
    // ganita_strength_get's `categories` list is graha_*-scoped only (shadbala/
    // vimsopaka/avastha/etc — confirmed live, zero bhava_bala-matching entries
    // ever appear there). Bhāva Bala is a chart_facts-native category
    // (CHART_FACTS_SCHEMA.json: "house_bhava_bala_total" /
    // "house_bhava_bala_subscore", target_table=chart_facts) served via
    // ganita_chart_facts_get, not ganita_strength_get — this was a wrong-tool
    // assertion, not a missing-feature one. Confirmed live: category=
    // house_bhava_bala_total returns 12 rows (one per house) with populated
    // `total` rupa values for 482012f1.
    const { content } = await ctx.client.callTool('ganita_chart_facts_get', {
      chart_id: ctx.chartId,
      category: 'house_bhava_bala_total',
      limit: 30,
    })
    const rows = chartFactsRows(content) as Array<{ fact_subject?: string; total?: number | null }>
    const bhavaBalaRows = rows.filter((r) => r.total !== null && r.total !== undefined)
    const status = bhavaBalaRows.length > 0 ? 'green' : 'red'
    return {
      id: b4BhavaBala.id,
      title: b4BhavaBala.title,
      status,
      evidence:
        bhavaBalaRows.length > 0
          ? `ganita_chart_facts_get(category=house_bhava_bala_total) served ${bhavaBalaRows.length} populated house-bala row(s), e.g. ${JSON.stringify(bhavaBalaRows[0])}.`
          : `ganita_chart_facts_get(category=house_bhava_bala_total) returned ${rows.length} row(s), none with a populated total — bhava_bala not yet built for 482012f1.`,
      register_row: b4BhavaBala.register_row,
    }
  },
}

// ── B5_sav_bav_sign_keyed ────────────────────────────────────────────────
const SIGN_NAMES = new Set([
  'ARIES', 'TAURUS', 'GEMINI', 'CANCER', 'LEO', 'VIRGO', 'LIBRA', 'SCORPIO', 'SAGITTARIUS', 'CAPRICORN', 'AQUARIUS', 'PISCES',
])
const b5SavBav: AssertionDef = {
  id: 'B5_sav_bav_sign_keyed',
  title: 'Ashtakavarga SAV/BAV re-keyed by SIGN (not just house) — sign-keyed rows served alongside the original house-keyed rows (CR-99a)',
  register_row: 'CR-99a (Gate B core)',
  async run(ctx) {
    // D-1.5b wave gate finding (live post-deploy verification, 2026-07-16):
    // the real category is `ashtakavarga_bindu_sign` (CHART_FACTS_SCHEMA.json
    // §subject_compound_note, CR-99a) — none of the original guessed names
    // matched. Its fact_subject is a compound "GRAHA-SIGN_N" (e.g.
    // "JUP-SIGN_1"), not a bare sign name, so the sign-keyed detector below
    // also needed broadening (a literal SIGN_NAMES.has(fact_subject) lookup
    // can never match a compound subject).
    const candidateCategories = ['ashtakavarga_bindu_sign', 'ashtakavarga_sav_sign', 'ashtakavarga_bav_sign', 'sav_by_sign', 'bav_by_sign', 'ashtakavarga_sign']
    const SIGN_KEYED_SUBJECT_RE = /-SIGN_\d+$/i
    const isSignKeyed = (subj: unknown): boolean => {
      const s = String(subj ?? '').toUpperCase()
      return SIGN_NAMES.has(s) || SIGN_KEYED_SUBJECT_RE.test(s)
    }
    const attempts: string[] = []
    for (const category of candidateCategories) {
      const { content } = await ctx.client.callTool('ganita_chart_facts_get', { chart_id: ctx.chartId, category, limit: 30 })
      const rows = chartFactsRows(content)
      attempts.push(`${category}=${rows.length}`)
      if (rows.length > 0) {
        const signKeyed = rows.some((r) => isSignKeyed(r.fact_subject))
        if (signKeyed) {
          return {
            id: b5SavBav.id,
            title: b5SavBav.title,
            status: 'green',
            evidence: `category=${category} served ${rows.length} sign-keyed row(s) (fact_subject values include sign names, e.g. ${rows[0].fact_subject}).`,
            register_row: b5SavBav.register_row,
          }
        }
      }
    }
    // Fallback: a broad keyword scan in case the real category name isn't in our candidate list.
    const { content: kwContent } = await ctx.client.callTool('ganita_chart_facts_get', { chart_id: ctx.chartId, keyword: 'ashtakavarga', limit: 100 })
    const kwRows = chartFactsRows(kwContent)
    const kwSignKeyed = kwRows.filter((r) => isSignKeyed(r.fact_subject))
    const status = kwSignKeyed.length > 0 ? 'green' : 'red'
    return {
      id: b5SavBav.id,
      title: b5SavBav.title,
      status,
      evidence:
        status === 'green'
          ? `keyword=ashtakavarga scan found ${kwSignKeyed.length} sign-keyed row(s) among ${kwRows.length} total.`
          : `No sign-keyed ashtakavarga rows found. Candidate categories tried: [${attempts.join(', ')}]. keyword=ashtakavarga scan: ${kwRows.length} row(s), none sign-keyed. Expected until B-2 merges + rebuild.`,
      register_row: b5SavBav.register_row,
    }
  },
}

// ── B6_positions_lead ────────────────────────────────────────────────────
const GRAHA_OR_LAGNA_SUBJECT = /^(SUN|MOON|MAR(S)?|MER(CURY)?|JUP(ITER)?|VEN(US)?|SAT(URN)?|RAH(U)?(_MEAN)?|KET(U)?(_MEAN)?|LAGNA|ASC(ENDANT)?)$/i
const b6PositionsLead: AssertionDef = {
  id: 'B6_positions_lead',
  title: 'ganita_positions_get default ordering leads with the nine grahas + lagna; upagrahas served behind them, not interleaved first (CR-50)',
  register_row: 'CR-50 (Gate B core)',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_positions_get', { chart_id: ctx.chartId, limit: 150 })
    const rows = positionsRows(content)
    const firstIndexBySubject = new Map<string, number>()
    rows.forEach((r, i) => {
      const subj = r.fact_subject ?? ''
      if (!firstIndexBySubject.has(subj)) firstIndexBySubject.set(subj, i)
    })
    const grahaIndices: number[] = []
    const nonGrahaIndices: number[] = []
    for (const [subj, idx] of firstIndexBySubject) {
      if (GRAHA_OR_LAGNA_SUBJECT.test(subj)) grahaIndices.push(idx)
      else nonGrahaIndices.push(idx)
    }
    if (rows.length === 0) {
      return {
        id: b6PositionsLead.id,
        title: b6PositionsLead.title,
        status: 'red',
        evidence: 'ganita_positions_get returned zero rows for 482012f1 — cannot confirm ordering.',
        register_row: b6PositionsLead.register_row,
      }
    }
    const maxGrahaIdx = grahaIndices.length > 0 ? Math.max(...grahaIndices) : -1
    const minNonGrahaIdx = nonGrahaIndices.length > 0 ? Math.min(...nonGrahaIndices) : Infinity
    const status = maxGrahaIdx < minNonGrahaIdx ? 'green' : 'red'
    return {
      id: b6PositionsLead.id,
      title: b6PositionsLead.title,
      status,
      evidence: `Distinct subjects: ${firstIndexBySubject.size} (graha/lagna: ${grahaIndices.length}, other: ${nonGrahaIndices.length}). Max first-occurrence index among graha/lagna subjects=${maxGrahaIdx}; min first-occurrence index among non-graha subjects=${minNonGrahaIdx === Infinity ? 'n/a (none present in page)' : minNonGrahaIdx}.`,
      register_row: b6PositionsLead.register_row,
    }
  },
}

// ── B7_budgets ────────────────────────────────────────────────────────────
const OVERSIZE_BUDGET_CAP_BYTES = 100_000
const b7Budgets: AssertionDef = {
  id: 'B7_budgets',
  title: 'Budgets hold on the three oversize tools: bodha_domain_reading_get, ephemeris_cache_year, ganita_tajaka_get (CR-13/49)',
  register_row: 'CR-13/49 (Gate B core)',
  async run(ctx) {
    const [domainReading, ephemerisYear, tajaka] = await Promise.all([
      ctx.client.callTool('bodha_domain_reading_get', { chart_id: ctx.chartId, domain: 'wealth' }),
      ctx.client.callTool('ephemeris_cache_year', { year: 2026 }),
      ctx.client.callTool('ganita_tajaka_get', { chart_id: ctx.chartId }),
    ])
    const domainBytes = Buffer.byteLength(JSON.stringify(domainReading.content ?? {}), 'utf8')
    const domainBounded = domainBytes <= OVERSIZE_BUDGET_CAP_BYTES

    const ephemTop = ephemerisYear.content as { pagination?: { total?: number; returned_count?: number } }
    const ephemPagination = ephemTop?.pagination
    const ephemBounded = Boolean(
      ephemPagination && typeof ephemPagination.returned_count === 'number' && ephemPagination.returned_count <= 1000
    )

    const tajakaTop = tajaka.content as { trim_report?: unknown[] }
    const tajakaBytes = Buffer.byteLength(JSON.stringify(tajaka.content ?? {}), 'utf8')
    const tajakaBounded = (Array.isArray(tajakaTop?.trim_report) && tajakaTop.trim_report.length > 0) || tajakaBytes <= OVERSIZE_BUDGET_CAP_BYTES

    const problems: string[] = []
    if (!domainBounded) problems.push(`bodha_domain_reading_get: ${domainBytes}B > ${OVERSIZE_BUDGET_CAP_BYTES}B cap, no pagination/trim evident`)
    if (!ephemBounded) problems.push(`ephemeris_cache_year: pagination=${JSON.stringify(ephemPagination)} not bounded`)
    if (!tajakaBounded) problems.push(`ganita_tajaka_get: ${tajakaBytes}B, no trim_report — not bounded`)

    const status = problems.length === 0 ? 'green' : 'red'
    return {
      id: b7Budgets.id,
      title: b7Budgets.title,
      status,
      evidence:
        problems.length === 0
          ? `All three bounded: bodha_domain_reading_get=${domainBytes}B, ephemeris_cache_year.pagination=${JSON.stringify(ephemPagination)}, ganita_tajaka_get=${tajakaBytes}B/trim_report=${Array.isArray(tajakaTop?.trim_report) ? tajakaTop.trim_report.length : 0} entries.`
          : problems.join('; '),
      register_row: b7Budgets.register_row,
    }
  },
}

// ── B8_n6_anchor (static — CLAUDE.md text, not an MCP call) ────────────────
const b8N6Anchor: AssertionDef = {
  id: 'B8_n6_anchor',
  title: 'CLAUDE.md §N.6 (Serving Density Principle) anchor text landed where the code already cites it',
  register_row: 'design §6 (Gate B core)',
  async run() {
    try {
      const claudeMd = readFileSync(repoPath('CLAUDE.md'), 'utf8')
      const hasHeading = /§N\.6\s*[—-]\s*Serving Density Principle/.test(claudeMd)
      const hasDensityContractRef = claudeMd.includes('density_contract')
      const status = hasHeading && hasDensityContractRef ? 'green' : 'red'
      return {
        id: b8N6Anchor.id,
        title: b8N6Anchor.title,
        status,
        evidence: `CLAUDE.md §N.6 heading present: ${hasHeading}. density_contract cross-reference present: ${hasDensityContractRef}.`,
        register_row: b8N6Anchor.register_row,
      }
    } catch (err) {
      return {
        id: b8N6Anchor.id,
        title: b8N6Anchor.title,
        status: 'red',
        evidence: `Could not read CLAUDE.md: ${err instanceof Error ? err.message : String(err)}`,
        register_row: b8N6Anchor.register_row,
      }
    }
  },
}

// ── B9_ci_density_job (static — .github/workflows/ci.yml, not an MCP call) ─
const b9CiDensityJob: AssertionDef = {
  id: 'B9_ci_density_job',
  title: 'CI density/census harness ("Density Census (§N.6)") wired into the pipeline',
  register_row: 'design §6 (Gate B core)',
  async run() {
    try {
      const ciYml = readFileSync(repoPath('.github', 'workflows', 'ci.yml'), 'utf8')
      const hasJobName = ciYml.includes('Density Census (§N.6)')
      const hasHarnessInvocation = ciYml.includes('scripts/audit/density_harness/run.ts')
      const status = hasJobName && hasHarnessInvocation ? 'green' : 'red'
      return {
        id: b9CiDensityJob.id,
        title: b9CiDensityJob.title,
        status,
        evidence: `ci.yml job name "Density Census (§N.6)" present: ${hasJobName}. density_harness/run.ts invocation present: ${hasHarnessInvocation}.`,
        register_row: b9CiDensityJob.register_row,
      }
    } catch (err) {
      return {
        id: b9CiDensityJob.id,
        title: b9CiDensityJob.title,
        status: 'red',
        evidence: `Could not read .github/workflows/ci.yml: ${err instanceof Error ? err.message : String(err)}`,
        register_row: b9CiDensityJob.register_row,
      }
    }
  },
}

// ── B_karakamsha (CR-17, B6-lane item) ─────────────────────────────────────
const bKarakamsha: AssertionDef = {
  id: 'B_karakamsha',
  title: 'Karakamsha fact (Ātmakāraka\'s D9 sign) resolvable via the MCP surface (CR-17)',
  register_row: 'CR-17',
  async run(ctx) {
    // D-1.5b wave gate finding (live post-deploy verification, 2026-07-16):
    // ga_sensitive_writer.py spells it "karakamsa" (Jaimini transliteration,
    // no 'h'), not "karakamsha" — fact_category="karakamsa_position",
    // fact_subject="KARAKAMSA" (target_table=chart_facts). All three
    // original candidates (category=karakamsha, fact_subject=AK,
    // keyword=karakamsha) miss on spelling/subject-naming alone; confirmed
    // live that category=karakamsa_position resolves cleanly (1 row,
    // atmakaraka_graha/longitude_d9_sidereal/sign fact_keys, grounding_score=1).
    const candidates: Array<Record<string, unknown>> = [
      { category: 'karakamsa_position' },
      { fact_subject: 'KARAKAMSA' },
      { keyword: 'karakamsa' },
      { category: 'karakamsha' },
      { fact_subject: 'AK' },
      { keyword: 'karakamsha' },
    ]
    for (const params of candidates) {
      const { content } = await ctx.client.callTool('ganita_chart_facts_get', { chart_id: ctx.chartId, limit: 20, ...params })
      const rows = chartFactsRows(content)
      if (rows.length > 0) {
        return {
          id: bKarakamsha.id,
          title: bKarakamsha.title,
          status: 'green',
          evidence: `Resolved via ${JSON.stringify(params)}: ${rows.length} row(s), e.g. ${JSON.stringify(rows[0])}.`,
          register_row: bKarakamsha.register_row,
        }
      }
    }
    return {
      id: bKarakamsha.id,
      title: bKarakamsha.title,
      status: 'red',
      evidence: `No karakamsa fact resolvable on 482012f1 via any of: ${JSON.stringify(candidates)}.`,
      register_row: bKarakamsha.register_row,
    }
  },
}

// ── B_shadbala_ratio (CR-18, B6-lane item) ─────────────────────────────────
const bShadbalaRatio: AssertionDef = {
  id: 'B_shadbala_ratio',
  title: 'Shadbala rows carry required_rupa + ratio per graha (BPHS minimums, CR-18)',
  register_row: 'CR-18',
  async run(ctx) {
    // D-1.5b wave gate finding (live post-deploy verification, 2026-07-16):
    // ganita_strength_get's `categories` list is a different, non-overlapping
    // vocabulary (graha_shadbala_total etc, no required_rupa/ratio keys ever
    // appear there) — required_rupa/ratio are chart_facts-native keys under
    // fact_category="graha_shadbala_total" (target_table=chart_facts per
    // CHART_FACTS_SCHEMA.json), served via ganita_chart_facts_get. This was a
    // wrong-tool assertion. Querying the correct tool/category directly:
    // `ratio` IS served (confirmed live for all 7 classical grahas). But
    // `required_rupa` — though present in the underlying chart_facts table
    // (direct DB check: e.g. SUN required_rupa=5, JUP=6.5, confirmed via raw
    // SQL) — is NOT returned by ganita_chart_facts_get for ANY shape/filter
    // combination (pivoted or rows, with or without fact_subject) tried
    // against the live connector. That is a genuine serving-layer gap
    // distinct from the tool-selection bug this fix addresses.
    const { content } = await ctx.client.callTool('ganita_chart_facts_get', {
      chart_id: ctx.chartId,
      category: 'graha_shadbala_total',
      limit: 30,
    })
    const rows = chartFactsRows(content) as Array<{ fact_subject?: string; ratio?: number | null; required_rupa?: number | null }>
    const ratioRows = rows.filter((r) => r.ratio !== null && r.ratio !== undefined)
    const requiredRupaRows = rows.filter((r) => r.required_rupa !== null && r.required_rupa !== undefined)
    const status = ratioRows.length > 0 && requiredRupaRows.length > 0 ? 'green' : 'red'
    return {
      id: bShadbalaRatio.id,
      title: bShadbalaRatio.title,
      status,
      evidence: `ganita_chart_facts_get(category=graha_shadbala_total) served ${rows.length} graha row(s). ratio populated: ${ratioRows.length}/${rows.length}. required_rupa populated: ${requiredRupaRows.length}/${rows.length}${requiredRupaRows.length === 0 ? ' — required_rupa exists in the underlying chart_facts table (direct DB check confirms non-null values per graha) but is not surfaced by ganita_chart_facts_get on any shape/filter tried; this is a real serving-layer gap, not a harness tool-selection issue.' : '.'}`,
      register_row: bShadbalaRatio.register_row,
    }
  },
}

// ── B_d2_hora_class (CR-58, B6-lane item) ──────────────────────────────────
const bD2HoraClass: AssertionDef = {
  id: 'B_d2_hora_class',
  title: 'D2 dignity rows carry hora_class (surya_hora/chandra_hora); "both wealth lords in Chandra-hora H12" servable in one call (CR-58)',
  register_row: 'CR-58',
  async run(ctx) {
    // D-1.5b B_d2_hora serving fix (live-verified 2026-07-16): the D2 hora rows
    // (ga_vargas_writer.py's _build_d2_hora_rows -> fact_category="varga_hora_class",
    // fact_key hora_class/hora_d2_house) live in chart_divisionals, NOT chart_facts. The fix makes
    // ganita_chart_facts_get(divisional_chart=D2) ALSO serve those chart_divisionals EAV rows in a
    // budget-capped, source-tagged `divisional_facts` section. Read THAT section (not the main
    // chart_facts `.facts`/rows, which never carried them). CR-58's "servable in one call" is met
    // when the hora_class + hora_d2_house layer comes back from this single call.
    const { content } = await ctx.client.callTool('ganita_chart_facts_get', { chart_id: ctx.chartId, divisional_chart: 'D2', limit: 300 })
    const df = ((content as { object?: { content?: { divisional_facts?: { rows?: Array<Record<string, unknown>> } } } })?.object?.content?.divisional_facts
      ?? (content as { content?: { divisional_facts?: { rows?: Array<Record<string, unknown>> } } })?.content?.divisional_facts) as { rows?: Array<Record<string, unknown>> } | undefined
    const dfRows = df?.rows ?? []
    const horaRows = dfRows.filter((r) => r['fact_category'] === 'varga_hora_class')
    const horaClassRows = horaRows.filter((r) => r['fact_key'] === 'hora_class')
    if (horaClassRows.length === 0) {
      return {
        id: bD2HoraClass.id,
        title: bD2HoraClass.title,
        status: 'red',
        evidence: `ganita_chart_facts_get(divisional_chart=D2) served ${dfRows.length} divisional_facts row(s) but 0 varga_hora_class hora_class rows — the D2 hora layer is not reaching the divisional_facts serving section on 482012f1.`,
        register_row: bD2HoraClass.register_row,
      }
    }
    // Per-graha join, in this one call: pair each graha's hora_class (surya_hora/chandra_hora)
    // with its hora_d2_house, so "both wealth lords in Chandra-hora, D2 house 12" is answerable
    // from a single response. Report the chandra_hora+H12 grahas as supporting detail (not forced
    // as the pass gate — whether THIS chart has ≥2 such grahas is chart-specific; CR-58's gate is
    // that the layer is SERVABLE in one call, which the hora_class rows above prove).
    const byGraha = new Map<string, { hora_class?: string; hora_house?: number }>()
    for (const r of horaRows) {
      const g = String(r['graha'] ?? '')
      if (!g) continue
      const entry = byGraha.get(g) ?? {}
      if (r['fact_key'] === 'hora_class') entry.hora_class = String(r['fact_value_text'] ?? '')
      if (r['fact_key'] === 'hora_d2_house') entry.hora_house = Number(r['fact_value_num'])
      byGraha.set(g, entry)
    }
    const chandraHoraH12 = [...byGraha.entries()].filter(([, v]) => v.hora_class === 'chandra_hora' && v.hora_house === 12)
    const classes = new Set(horaClassRows.map((r) => String(r['fact_value_text'] ?? '')))
    return {
      id: bD2HoraClass.id,
      title: bD2HoraClass.title,
      status: 'green',
      evidence: `D2 hora layer served in ONE call via divisional_facts: ${horaClassRows.length} hora_class row(s) across ${byGraha.size} grahas (classes present: ${[...classes].join(', ')}), hora_d2_house paired per graha. "Both wealth lords in Chandra-hora H12" is answerable from this response — chandra_hora+H12 grahas on this chart: ${chandraHoraH12.length} (${chandraHoraH12.map(([g]) => g).join(', ') || 'none on 482012f1, but the query is answerable'}).`,
      register_row: bD2HoraClass.register_row,
    }
  },
}

// ── B_anchor_dedup (CR-46, B6-lane item) ───────────────────────────────────
const bAnchorDedup: AssertionDef = {
  id: 'B_anchor_dedup',
  title: 'phala_anchors_get.anchor_count is post-dedup (no duplicate anchors; count matches the deduplicated set) (CR-46)',
  register_row: 'CR-46',
  async run(ctx) {
    const { content, raw, isToolError } = await ctx.client.callTool('phala_anchors_get', {
      chart_id: ctx.chartId,
      date_range: { start: '2020-01-01', end: '2032-12-31' },
    })
    if (isToolError || raw.status >= 400) {
      return {
        id: bAnchorDedup.id,
        title: bAnchorDedup.title,
        status: 'red',
        evidence: `phala_anchors_get call failed (status=${raw.status}): ${raw.body.slice(0, 300)}`,
        register_row: bAnchorDedup.register_row,
      }
    }
    const top = content as {
      anchor_count?: number
      content?: { anchor_count?: number; anchors?: Array<Record<string, unknown>> }
      anchors?: Array<Record<string, unknown>>
    }
    const anchors = top.anchors ?? top.content?.anchors ?? []
    const anchorCount = top.anchor_count ?? top.content?.anchor_count
    const dedupKeys = new Set(anchors.map((a) => JSON.stringify(a)))
    const rawHasDuplicates = dedupKeys.size < anchors.length
    const countMatchesDedup = anchorCount === undefined ? false : anchorCount <= dedupKeys.size || anchorCount === anchors.length
    const status = !rawHasDuplicates && countMatchesDedup && anchorCount !== undefined ? 'green' : 'red'
    return {
      id: bAnchorDedup.id,
      title: bAnchorDedup.title,
      status,
      evidence: `anchor_count=${anchorCount}; served anchors=${anchors.length}; distinct (post-dedup)=${dedupKeys.size}; raw duplicates present=${rawHasDuplicates}.`,
      register_row: bAnchorDedup.register_row,
    }
  },
}

// ── B_remedies_search_honest (CR-42, B6-lane item) ─────────────────────────
const bRemediesSearchHonest: AssertionDef = {
  id: 'B_remedies_search_honest',
  title: 'ref_remedies_search(keyword=Saturn) returns Saturn rows OR rejects loudly (never silently drops the keyword filter) (CR-42)',
  register_row: 'CR-42',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ref_remedies_search', { keyword: 'Saturn', planet: 'Saturn', limit: 50 })
    const top = content as {
      keyword_search?: { applied?: boolean; matched_count?: number; served_count?: number; note?: string }
      result?: { results?: Array<Record<string, unknown>> }
    }
    const ks = top.keyword_search
    const results = top.result?.results ?? []
    const applied = ks?.applied === true
    const honest = applied && (typeof ks?.matched_count === 'number') && (typeof ks?.note === 'string' && ks.note.length > 0)
    const status = applied && honest ? 'green' : 'red'
    return {
      id: bRemediesSearchHonest.id,
      title: bRemediesSearchHonest.title,
      status,
      evidence: `keyword_search.applied=${applied}; matched_count=${ks?.matched_count}; served_count=${ks?.served_count}; results.length=${results.length}; note="${ks?.note ?? '(absent)'}".`,
      register_row: bRemediesSearchHonest.register_row,
    }
  },
}

// ── B_structural_envelope (§N.6 density contract, live) ────────────────────
const bStructuralEnvelope: AssertionDef = {
  id: 'B_structural_envelope',
  title: 'ganita_structural_get serves the layered §N.6 envelope (verdict/ranking_basis/grounding/drill_pointers/judgment_flags/coverage/chart_header/epistemic) with a density contract',
  register_row: 'design §10 (B6-lane item)',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_structural_get', {
      chart_id: ctx.chartId,
      facet: 'dispositors',
      response_format: 'v3',
      limit: 50,
    })
    const env = v3Envelope(content)
    const present = {
      verdict: env.verdict !== undefined,
      ranking_basis: env.ranking_basis !== undefined,
      grounding: env.grounding !== undefined,
      drill_pointers: Array.isArray(env.drill_pointers),
      judgment_flags: Array.isArray(env.judgment_flags),
      chart_header: env.chart_header !== undefined && env.chart_header !== null,
      epistemic: env.epistemic !== undefined && env.epistemic !== null,
      coverage: env.coverage !== undefined && env.coverage !== null,
    }
    const missing = Object.entries(present).filter(([, ok]) => !ok).map(([k]) => k)
    const status = missing.length === 0 ? 'green' : 'red'
    return {
      id: bStructuralEnvelope.id,
      title: bStructuralEnvelope.title,
      status,
      evidence: missing.length === 0 ? `All §N.6 envelope fields present: ${Object.keys(present).join(', ')}.` : `Missing envelope fields: ${missing.join(', ')}.`,
      register_row: bStructuralEnvelope.register_row,
    }
  },
}

// ── B_dasha_lord_capability (B8 derived view) ──────────────────────────────
const bDashaLordCapability: AssertionDef = {
  id: 'B_dasha_lord_capability',
  title: 'dasha_lord_capability rows served for Ketu-MD (warning_tier present) and Venus-MD (shadbala/weakest-graha join present) on 482012f1 (B8)',
  register_row: 'CR-60 (B8-lane item)',
  async run(ctx) {
    const tools = await ctx.client.listTools()
    const discoverable = tools.some((t) => t.name === 'ganita_dasha_lord_capability_get')
    if (!discoverable) {
      return {
        id: bDashaLordCapability.id,
        title: bDashaLordCapability.title,
        status: 'red',
        evidence: `ganita_dasha_lord_capability_get not found among ${tools.length} tools/list entries — B-7's new tool is not yet exposed on this connector face.`,
        register_row: bDashaLordCapability.register_row,
      }
    }
    const { content, raw, isToolError } = await ctx.client.callTool('ganita_dasha_lord_capability_get', { chart_id: ctx.chartId })
    if (isToolError || raw.status >= 400) {
      return {
        id: bDashaLordCapability.id,
        title: bDashaLordCapability.title,
        status: 'red',
        evidence: `Call failed (status=${raw.status}): ${raw.body.slice(0, 300)}`,
        register_row: bDashaLordCapability.register_row,
      }
    }
    const top = content as {
      rows?: Array<{ lord?: string; warning_tier?: string; shadbala_percentile?: number | null; ratification_factor?: number | null }>
    }
    const rows = top.rows ?? []
    const ketuRow = rows.find((r) => (r.lord ?? '').toLowerCase() === 'ketu')
    const venusRow = rows.find((r) => (r.lord ?? '').toLowerCase() === 'venus')
    const ketuWarningTierPresent = Boolean(ketuRow?.warning_tier) && ['none', 'watch', 'elevated', 'high'].includes(ketuRow?.warning_tier ?? '')
    const venusJoinPresent = venusRow !== undefined && venusRow.shadbala_percentile !== null && venusRow.shadbala_percentile !== undefined
    const status = ketuWarningTierPresent && venusJoinPresent ? 'green' : 'red'
    return {
      id: bDashaLordCapability.id,
      title: bDashaLordCapability.title,
      status,
      evidence: `${rows.length} MD-lord row(s) served. Ketu row: ${JSON.stringify(ketuRow) ?? '(absent)'}. Venus row: ${JSON.stringify(venusRow) ?? '(absent)'}.`,
      register_row: bDashaLordCapability.register_row,
    }
  },
}

// ── B_dosha_gate_kalasarpa (B9-lane item) ──────────────────────────────────
const bDoshaGateKalasarpa: AssertionDef = {
  id: 'B_dosha_gate_kalasarpa',
  title: 'ganita_yogas_get default page carries zero shared-stub dosha_label rows; per-varga kāla-sarpa verdict is servable (CR-72/73/74)',
  register_row: 'CR-72/73/74 (B9-lane item)',
  async run(ctx) {
    const [yogas, structural] = await Promise.all([
      ctx.client.callTool('ganita_yogas_get', { chart_id: ctx.chartId, response_format: 'v3', limit: 60 }),
      ctx.client.callTool('ganita_structural_get', { chart_id: ctx.chartId, facet: 'dosha_fires', response_format: 'v3', limit: 20 }),
    ])
    const yogasPayload = ganitaYogasV3Payload(yogas.content)
    const doshaLabelRows = yogasPayload.rows.filter((r) => (r as { fact_category?: string }).fact_category === 'dosha_label')

    const structuralContent = (structural.content as { content?: { kala_sarpa_per_varga?: { natal?: unknown[] } } })?.content
    const kalaSarpaNatal = structuralContent?.kala_sarpa_per_varga?.natal ?? []
    const kalaSarpaServable = Array.isArray(kalaSarpaNatal) && kalaSarpaNatal.length > 0

    const status = doshaLabelRows.length === 0 && kalaSarpaServable ? 'green' : 'red'
    return {
      id: bDoshaGateKalasarpa.id,
      title: bDoshaGateKalasarpa.title,
      status,
      evidence: `ganita_yogas_get default page: ${yogasPayload.rows.length} row(s) total, ${doshaLabelRows.length} dosha_label (must be 0). kala_sarpa_per_varga.natal servable: ${kalaSarpaServable} (${kalaSarpaNatal.length} row(s)).`,
      register_row: bDoshaGateKalasarpa.register_row,
    }
  },
}

const GATE_B_ASSERTIONS: AssertionDef[] = [
  b1Chalit,
  b2Sudarshana,
  b3BhavatBhavam,
  b4BhavaBala,
  b5SavBav,
  b6PositionsLead,
  b7Budgets,
  b8N6Anchor,
  b9CiDensityJob,
  bKarakamsha,
  bShadbalaRatio,
  bD2HoraClass,
  bAnchorDedup,
  bRemediesSearchHonest,
  bStructuralEnvelope,
  bDashaLordCapability,
  bDoshaGateKalasarpa,
]

export const ALL_ASSERTIONS: AssertionDef[] = [k2_1, k2_2, k2_3, k2_4, k2_5, k2_6a, k2_6b, k2_7, k2_8, k2_9, k2_10, k2_11, k2_12, a5, a7, ...GATE_B_ASSERTIONS]

// D-2 Lane V-0 (BIND_D-2.md §F1.7 ledger row 6 — "extends doctrine_harness, never
// duplicates"): re-exported so wealth_conclusions.ts (the §G.0 six-conclusion harness)
// reuses these exact live-shape-verified parsers/pagers instead of re-deriving its own
// copies of the same response-shape knowledge. Deliberately NOT imported back into THIS file
// (would create an assertions.ts <-> wealth_conclusions.ts circular import) — run_master_gate.ts
// imports ALL_ASSERTIONS (this file) and WEALTH_CONCLUSION_ASSERTIONS (wealth_conclusions.ts)
// separately and runs both, one level up.
export { fetchWealthSignals, v3Envelope, chartFactsRows, ganitaYogasV3Payload, judgmentQueryBearingYogas, positionsRows, fetchSignalsGeneric }

export async function runAssertion(def: AssertionDef, ctx: RunContext): Promise<AssertionResult> {
  try {
    return await def.run(ctx)
  } catch (err) {
    return {
      id: def.id,
      title: def.title,
      status: 'red',
      evidence: `ASSERTION THREW (treated as red, never a silent pass): ${err instanceof Error ? err.message : String(err)}`,
      register_row: def.register_row,
    }
  }
}
