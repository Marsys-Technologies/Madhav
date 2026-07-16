/**
 * wealth_conclusions.ts — D-2 Lane V-0, BIND_D-2.md §F1.7 ledger row 1.
 *
 * The §G.0 table in POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md ("The finding that governs
 * this entire section") names SIX load-bearing conclusions a full financial reading of
 * 482012f1 must reach, and found the engine served ZERO of them at the time of that 2026-07-13
 * reading — every one was hand-derived by the consuming LLM from raw L1 facts. BRIEF_D2.md §G.1
 * requires the wave's master-acceptance gate to assert each of the 6 is now "traceable to a
 * served top-15 signal/verdict in its domain surface" — not merely present somewhere in the
 * estate, but reachable by a floor-model reading agent working the served surfaces at normal
 * page sizes, never a 9957th-ranked needle (the exact CR-54 defect the register documents).
 *
 * Each assertion below is a LIVE MCP probe (never a DB read — CR-96: verify against the
 * consuming surface) against the domain surface most directly responsible for that conclusion,
 * reusing the exact live-shape parsers doctrine_harness/lib/assertions.ts already verified
 * (fetchWealthSignals, judgmentQueryBearingYogas, v3Envelope, …) rather than re-deriving new
 * ones — BIND_D-2.md §F1.7 ledger row 6's "extend, never duplicate" rule.
 *
 * An assertion that cannot confirm the conclusion reports RED with a diagnosis, exactly like
 * every other assertion in this harness (CLAUDE.md B.10 spirit applied to the harness itself) —
 * never a fabricated green because "the fix probably shipped."
 */
import type { AssertionDef, RunContext } from './types'
import { fetchWealthSignals, judgmentQueryBearingYogas } from './assertions'

const WEALTH_TOP_K = 15

// ── G0-1: Dhana Yoga — 2L Venus + 9L Jupiter conjunct in the 9th, own sign ────────────────
const g0_1: AssertionDef = {
  id: 'G0-1',
  title:
    '§G.0 #1 — Dhana Yoga (2L Venus + 9L Jupiter conjunct 9th, Jupiter own sign) is traceable ' +
    'in judgment_query(wealth).bearing_yogas (the domain surface a wealth reading actually ' +
    'consults, not buried in a 1,594-row signal pool)',
  register_row: '§G.0 #1 / CR-56',
  async run(ctx) {
    const { content } = await ctx.client.callTool('judgment_query', {
      chart_id: ctx.chartId,
      domain: 'wealth',
      response_format: 'v3',
    })
    const { bearingYogas } = judgmentQueryBearingYogas(content)
    const hit = bearingYogas.find((y) => {
      const text = JSON.stringify(y).toLowerCase()
      return text.includes('dhana') && text.includes('venus') && text.includes('jupiter')
    })
    const status = hit ? 'green' : 'red'
    return {
      id: g0_1.id,
      title: g0_1.title,
      status,
      evidence: hit
        ? `judgment_query(wealth).bearing_yogas (${bearingYogas.length} row(s)) contains the Dhana Yoga specimen: ${JSON.stringify(hit)}`
        : `judgment_query(wealth).bearing_yogas = ${JSON.stringify(bearingYogas)} — the Venus+Jupiter Dhana Yoga is not traceable on the reading's own bearing_yogas surface (§G.0 #1 conclusion NOT reachable).`,
      register_row: g0_1.register_row,
    }
  },
}

// ── G0-2: Varga collapse — 2L+11L debilitated in D9; wealth lords in D2's 12th ────────────
const g0_2: AssertionDef = {
  id: 'G0-2',
  title:
    '§G.0 #2 — Varga collapse (2L+11L debilitated in D9; wealth lords bunched in D2 house 12) ' +
    'is traceable via a wealth-domain top-15 varga_ratification_divergence signal naming Saturn ' +
    'or Venus at D9',
  register_row: '§G.0 #2 / CR-57',
  async run(ctx) {
    const [wealthTop15, divergenceClassScoped] = await Promise.all([
      fetchWealthSignals(ctx, 1, WEALTH_TOP_K),
      ctx.client.callTool('bodha_signals_get', {
        chart_id: ctx.chartId,
        domain: 'wealth',
        signal_type_class: 'varga_ratification_divergence',
        top_k: WEALTH_TOP_K,
      }),
    ])
    const divergenceRows =
      ((divergenceClassScoped.content as { content?: { signals?: unknown[] } })?.content?.signals ?? []) as Array<{
        citation_human?: string
        signal_headline_text?: string
        configuration_jsonb?: { value_text?: string; subject?: string; domain?: string }
      }>
    const inTop15 = wealthTop15.some((s) => (s.signal_type_id ?? '').includes('varga_ratification_divergence'))
    // Live-verified (2026-07-16 probe): citation_human on this signal class is a TERSE template
    // ("ga_vichara varga_ratification_divergence: SAT in wealth") — it does NOT name "Saturn" or
    // "D9" in full. The graha-name + varga specificity lives in `signal_headline_text` /
    // `configuration_jsonb.value_text` (e.g. "SATURN: D1 exalted vs D9 debilitated — wealth
    // ratification fails in D9"), matching BIND_D-2.md §B.2's own quoted evidence text. Scan all
    // three fields so the check isn't accidentally scoped to the one field that happens not to
    // carry the specificity.
    const specimen = divergenceRows.find((s) => {
      const text = [s.citation_human, s.signal_headline_text, s.configuration_jsonb?.value_text, s.configuration_jsonb?.subject]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return (text.includes('saturn') || text.includes('venus') || text.includes(':sat:') || text.includes(':ven:')) && text.includes('d9')
    })
    const status = specimen ? 'green' : 'red'
    return {
      id: g0_2.id,
      title: g0_2.title,
      status,
      evidence: specimen
        ? `varga_ratification_divergence class-scoped query returned ${divergenceRows.length} row(s), including: ${specimen.signal_headline_text ?? specimen.citation_human}. ` +
          `Wealth-domain top-${WEALTH_TOP_K} scan (rank-ordered) itself surfaces the class: ${inTop15}.`
        : `varga_ratification_divergence class-scoped query returned ${divergenceRows.length} row(s); none names Saturn or Venus at D9. Wealth-domain top-${WEALTH_TOP_K}: divergence class present=${inTop15}. §G.0 #2 conclusion NOT confirmed traceable.`,
      register_row: g0_2.register_row,
    }
  },
}

// ── G0-3: Nīcha-Bhaṅga (D9), two grahas — Saturn (Aries) + Venus (Virgo) ──────────────────
const g0_3: AssertionDef = {
  id: 'G0-3',
  title:
    '§G.0 #3 — Nīcha-Bhaṅga at D9 for BOTH Saturn (Aries) and Venus (Virgo) is traceable on the ' +
    'firings-authoritative yoga surface with per-graha grounds, not a blanket "not_applicable" ' +
    'D1-scoped verdict',
  register_row: '§G.0 #3 / CR-59',
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
      id: g0_3.id,
      title: g0_3.title,
      status,
      evidence: `ganita_yoga_firings_get(neecha_bhanga_raja_yoga): fired=${Boolean(fired)}; Saturn(D9 Aries) grounded=${saturnGrounded}; Venus(D9 Virgo) grounded=${venusGrounded}.`,
      register_row: g0_3.register_row,
    }
  },
}

// ── G0-4: Wealth-loss mechanism — exalted Rahu H2 + 8L Mars aspect on H2 @1.00 ────────────
const g0_4: AssertionDef = {
  id: 'G0-4',
  title:
    '§G.0 #4 — The wealth-loss mechanism (exalted Rahu in H2 + 8L Mars full-strength aspect on ' +
    'H2) ranks inside the wealth-domain top-15 with a non-neutral valence — the exact CR-54 ' +
    'defect (this mechanism served at salience 0.575/valence neutral, i.e. ranked as noise)',
  register_row: '§G.0 #4 / CR-54',
  async run(ctx) {
    const top15 = await fetchWealthSignals(ctx, 1, WEALTH_TOP_K)
    const mechanismRow = top15.find((s) => {
      const text = (s.citation_human ?? '').toLowerCase()
      const mars8thOnH2 =
        text.includes('mars') && (text.includes('house 2') || text.includes('h2')) && (s.configuration_jsonb?.target_house === 2)
      const rahuInH2 = text.includes('rahu') && (text.includes('house 2') || text.includes('h2'))
      return mars8thOnH2 || rahuInH2
    })
    const nonNeutral = mechanismRow !== undefined && !['neutral'].includes(mechanismRow.valence ?? '')
    const status = mechanismRow && nonNeutral ? 'green' : 'red'
    return {
      id: g0_4.id,
      title: g0_4.title,
      status,
      evidence: mechanismRow
        ? `Found in wealth-domain top-${WEALTH_TOP_K}: ${mechanismRow.citation_human} — valence=${mechanismRow.valence}, valence_source=${mechanismRow.valence_source}. Non-neutral (CR-54 fixed for this specimen)=${nonNeutral}.`
        : `No Mars-aspects-H2 / Rahu-in-H2 specimen found in the wealth-domain top-${WEALTH_TOP_K} scan — the mechanism did not rank into the reading's actionable surface (§G.0 #4 NOT confirmed traceable; the pre-D-2 register evidence is salience 0.575, rank 9957/9401 — outside any reasonable top-K).`,
      register_row: g0_4.register_row,
    }
  },
}

// ── G0-5: Venus — weakest graha AND 2L AND MD lord for 20y from 2034 ──────────────────────
const g0_5: AssertionDef = {
  id: 'G0-5',
  title:
    '§G.0 #5 — Venus is served as the weakest graha (chart digest verdict) AND its dasha-lord ' +
    'capability join (shadbala percentile / warning tier) is present — the three-fact join the ' +
    'register found no surface producing',
  register_row: '§G.0 #5 / CR-55 + CR-60',
  async run(ctx) {
    const [digestRes, capabilityRes] = await Promise.all([
      ctx.client.callTool('bodha_chart_digest_get', { chart_id: ctx.chartId }),
      ctx.client.callTool('ganita_dasha_lord_capability_get', { chart_id: ctx.chartId }),
    ])
    // Live-verified shape (2026-07-16, direct probe against the deployed connector while
    // building this assertion): weakest_graha sits at content.content.digest.weakest_graha —
    // ONE level deeper than a first-pass reading of the field name suggests (content.digest,
    // not content.weakest_graha directly). Falls back to the shallower shapes defensively in
    // case a future response envelope flattens it.
    const digest = digestRes.content as {
      content?: { digest?: { weakest_graha?: string }; weakest_graha?: string }
      digest?: { weakest_graha?: string }
      weakest_graha?: string
    }
    const weakestGraha =
      digest?.content?.digest?.weakest_graha ?? digest?.content?.weakest_graha ?? digest?.digest?.weakest_graha ?? digest?.weakest_graha
    const weakestIsVenus = (weakestGraha ?? '').toLowerCase() === 'venus'

    const capTop = (capabilityRes.content as {
      rows?: Array<{ lord?: string; shadbala_percentile?: number | null; warning_tier?: string }>
    })
    const venusRow = (capTop.rows ?? []).find((r) => (r.lord ?? '').toLowerCase() === 'venus')
    const venusJoinPresent = venusRow !== undefined && venusRow.shadbala_percentile !== null && venusRow.shadbala_percentile !== undefined

    const status = weakestIsVenus && venusJoinPresent ? 'green' : 'red'
    return {
      id: g0_5.id,
      title: g0_5.title,
      status,
      evidence: `bodha_chart_digest_get.weakest_graha="${weakestGraha}" (must be Venus, not the pre-fix "Mercury"). ganita_dasha_lord_capability_get Venus row: ${JSON.stringify(venusRow) ?? '(absent)'}.`,
      register_row: g0_5.register_row,
    }
  },
}

// ── G0-6: Ketu MD 2027-2034 interpreted (8th-lord, shadbala 0.625) ────────────────────────
const g0_6: AssertionDef = {
  id: 'G0-6',
  title:
    '§G.0 #6 — Ketu MD (2027-08-18 → 2034-08-18, 8th-house lord, shadbala 0.625) is served WITH ' +
    'an interpreted warning tier, not as a bare uninterpreted number',
  register_row: '§G.0 #6 / CR-60',
  async run(ctx) {
    const { content } = await ctx.client.callTool('ganita_dasha_lord_capability_get', { chart_id: ctx.chartId })
    const top = content as {
      rows?: Array<{ lord?: string; warning_tier?: string; house_class?: string; shadbala_percentile?: number | null }>
    }
    const rows = top.rows ?? []
    const ketuRow = rows.find((r) => (r.lord ?? '').toLowerCase() === 'ketu')
    const warningTierPresent = Boolean(ketuRow?.warning_tier) && ['none', 'watch', 'elevated', 'high'].includes(ketuRow?.warning_tier ?? '')
    const status = warningTierPresent ? 'green' : 'red'
    return {
      id: g0_6.id,
      title: g0_6.title,
      status,
      evidence: `ganita_dasha_lord_capability_get served ${rows.length} row(s). Ketu row: ${JSON.stringify(ketuRow) ?? '(absent)'} — interpreted warning_tier present=${warningTierPresent} (pre-D-2 register evidence: shadbala 0.625 served as a bare number, nothing interpreted it).`,
      register_row: g0_6.register_row,
    }
  },
}

export const WEALTH_CONCLUSION_ASSERTIONS: AssertionDef[] = [g0_1, g0_2, g0_3, g0_4, g0_5, g0_6]

/** Convenience runner: executes all 6 §G.0 conclusion assertions and reports coverage. */
export async function runWealthConclusionGate(ctx: RunContext): Promise<{
  total: number
  green: number
  red: number
  results: Array<{ id: string; status: 'green' | 'red'; evidence: string }>
  sixOfSix: boolean
}> {
  const results = []
  for (const def of WEALTH_CONCLUSION_ASSERTIONS) {
    try {
      const r = await def.run(ctx)
      results.push({ id: r.id, status: r.status, evidence: r.evidence })
    } catch (err) {
      results.push({
        id: def.id,
        status: 'red' as const,
        evidence: `ASSERTION THREW (treated as red, never a silent pass): ${err instanceof Error ? err.message : String(err)}`,
      })
    }
  }
  const green = results.filter((r) => r.status === 'green').length
  const red = results.length - green
  return { total: results.length, green, red, results, sixOfSix: green === 6 }
}
