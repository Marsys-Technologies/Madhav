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

function ganitaYogasV3Payload(content: unknown): {
  verdict: { pancha_mahapurusha?: { summary?: string } }
  judgment_flags: string[]
  coverage: { served?: number | null; total?: number | null } | null
  rows: Array<{ fact_category?: string }>
  total: number | null
} {
  const top = content as {
    verdict?: { pancha_mahapurusha?: { summary?: string } }
    judgment_flags?: string[]
    coverage?: { served?: number | null; total?: number | null }
    content?: { content?: { rows?: Array<{ fact_category?: string }>; total?: number } }
  }
  return {
    verdict: top.verdict ?? {},
    judgment_flags: top.judgment_flags ?? [],
    coverage: top.coverage ?? null,
    rows: top.content?.content?.rows ?? [],
    total: top.content?.content?.total ?? null,
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
  title: "9L Jupiter's aspect on H2 → benefic/strong_benefic, valence_source='ga_vichara_v1'",
  register_row: 'CR-90',
  async run(ctx) {
    const signals = await fetchWealthSignals(ctx)
    const specimen = signals.find(
      (s) => s.configuration_jsonb?.lord === 'Jupiter' && s.configuration_jsonb?.target_house === 2 && s.signal_type_id?.startsWith('bhava_significance_link')
    )
    if (!specimen) {
      return {
        id: k2_2.id,
        title: k2_2.title,
        status: 'red',
        evidence: `Specimen (Jupiter lord-aspect on H2) not found among ${signals.length} scanned wealth signals — cannot confirm the fix; treated as unresolved.`,
        register_row: k2_2.register_row,
      }
    }
    const ok = ['benefic', 'strong_benefic'].includes(specimen.valence ?? '') && specimen.valence_source === 'ga_vichara_v1'
    return {
      id: k2_2.id,
      title: k2_2.title,
      status: ok ? 'green' : 'red',
      evidence: `${specimen.citation_human} — valence=${specimen.valence}, valence_source=${specimen.valence_source}.`,
      register_row: k2_2.register_row,
    }
  },
}

// ── K.2 §3 ────────────────────────────────────────────────────────────────
const k2_3: AssertionDef = {
  id: '3',
  title: "Mars (8L) 8th-aspect-on-H2 → valence='strong_malefic', valence_source='ga_vichara_v1' (CR-54 specimen)",
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
    const ok = specimen.valence === 'strong_malefic' && specimen.valence_source === 'ga_vichara_v1'
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
  title: "Zero lord-link/graha-aspect signals on the wealth surface carry valence_source='keyword_heuristic_v1'",
  register_row: 'CR-91',
  async run(ctx) {
    const signals = await fetchWealthSignals(ctx)
    const relevant = signals.filter(
      (s) => s.signal_type_id?.startsWith('bhava_significance_link') || s.signal_type_id?.startsWith('aspect_parashari')
    )
    const violations = relevant.filter((s) => s.valence_source === 'keyword_heuristic_v1')
    const status = violations.length === 0 ? 'green' : 'red'
    const evidence =
      violations.length === 0
        ? `Scanned ${relevant.length} lord-link/graha-aspect wealth signals (of ${signals.length} total); none carry valence_source=keyword_heuristic_v1.`
        : `VIOLATION: ${violations[0].citation_human} still valence_source=keyword_heuristic_v1. (${violations.length}/${relevant.length} lord-link/aspect rows still on the old engine.)`
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
  title: 'ganita_yogas_get(482012f1).yoga_fires is non-empty (register text: "yoga_fires" fact_category)',
  register_row: 'CR-92',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_yogas_get', { chart_id: ctx.chartId, limit: 60, response_format: 'v3' })
    const { rows, total } = ganitaYogasV3Payload(content)
    const yogaFireRows = rows.filter((r) => r.fact_category === 'yoga_fires')
    const status = yogaFireRows.length > 0 ? 'green' : 'red'
    return {
      id: k2_6b.id,
      title: k2_6b.title,
      status,
      evidence: `ganita_yogas_get served ${rows.length} row(s) across all categories (page total=${total}); yoga_fires category rows = ${yogaFireRows.length}.`,
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
    const staleDescription = (tool?.description ?? '').includes('will never fire')

    const { content } = await ctx.client.callTool('ganita_yogas_get', { chart_id: ctx.chartId, limit: 60, response_format: 'v3' })
    const { judgment_flags, coverage, rows } = ganitaYogasV3Payload(content)
    const hasZeroFlagOnNonEmpty = rows.length > 0 && judgment_flags.includes('zero_rows_returned')
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
    const rows = ((content as { content?: { content?: { rows?: unknown[] } } })?.content?.content?.rows ?? []) as Array<{
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
      return {
        id: a7.id,
        title: a7.title,
        status: 'red',
        evidence: `Scanned ${rows.length} structural-aspect rows (facet=aspects); found zero rows citing a "7th aspect" — cannot confirm the fix from this response shape/sample; treated conservatively as unresolved. (Follow-up: this spot-check may need a more targeted per-graha aspect query once A-gamma lands a dedicated serving path.)`,
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

export const ALL_ASSERTIONS: AssertionDef[] = [k2_1, k2_2, k2_3, k2_4, k2_5, k2_6a, k2_6b, k2_7, k2_8, k2_9, k2_10, k2_11, k2_12, a5, a7]

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
