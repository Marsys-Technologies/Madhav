/**
 * synthesis/instrument.ts — the Large-N Synthesis Instrument (WP-1.4 / LCA-15 / R-48)
 * ====================================================================================
 * The staged retrieval-with-aggregation instrument that composes N-hundred factors
 * WITHOUT a flat top-K wall. Four stages, in order:
 *
 *   (1) decompose(question)          → EvidenceContract          [intent.ts]
 *   (2) plan against PRE-AGGREGATED  → gestalt verdicts + CDLM linkage cells FIRST
 *   (3) map-reduce over families     → FamilyComposite[] under a RUNNING BUDGET
 *   (4) narrative + DERIVATION LEDGER → every claim → resolvable signal_ids/fact_ids
 *
 * THE FLAT-WALL ANTIDOTE (E4 proportionality). A naive path does
 * `SELECT … ORDER BY salience LIMIT 200` over 12,364 career signals — a flat wall that
 * is both un-composable and un-budgeted. This instrument instead:
 *   • reads the PRE-AGGREGATED gestalt verdict (1 row) before any atomic drill;
 *   • reads the PRE-AGGREGATED CDLM linkage cells (a handful) to plan cross-domain reach;
 *   • drills atomic signals ONLY per family, each capped at per_family_cap AND against a
 *     running whole-answer budget — so the total atomic rows served is bounded (≤ ~60)
 *     no matter how many tens of thousands of signals the families contain;
 *   • DISCLOSES every family it did not fully serve (total, more_available) — never dumps.
 *
 * HONEST DEGRADATION (B.10). Where a stage is thin today (native-chart contradictions=0
 * per LCA-6/WP-2.2; CDLM narrative seeds NULL), the instrument records a DISCLOSURE and
 * moves on — it never fabricates the missing depth. Those stages light up automatically
 * when WP-2.2 populates them at W3; no instrument change needed.
 */

import { decompose } from './intent'
import { RegistrySurfaceGateway, type SurfaceGateway } from './surface_gateway'
import {
  DEFAULT_BUDGET,
  type StageBudget,
  type EvidenceContract,
  type FamilyComposite,
  type LargeNAnswer,
  type NarrativeSection,
  type DerivationLedgerEntry,
  type PlanStep,
  type SignalExemplar,
} from './types'

export interface ComposeParams {
  chart_id: string
  question: string
  ayanamsha_id?: string
  budget?: Partial<StageBudget>
}

const DEFAULT_AYANAMSHA = 'lahiri_chitrapaksha'

/**
 * Compose a large-N answer for a compound question. `gateway` defaults to the registry
 * gateway (real served surfaces); tests inject a fake to control family sizes.
 */
export async function composeLargeN(
  params: ComposeParams,
  gateway: SurfaceGateway = new RegistrySurfaceGateway(),
): Promise<LargeNAnswer> {
  const chart_id = params.chart_id
  if (!chart_id) throw new Error('[synthesis] chart_id is required — no default chart')
  const ayanamsha_id = params.ayanamsha_id ?? DEFAULT_AYANAMSHA
  const budget: StageBudget = { ...DEFAULT_BUDGET, ...(params.budget ?? {}) }

  const plan: PlanStep[] = []
  const disclosures: string[] = []

  // ── (1) INTENT DECOMPOSITION ────────────────────────────────────────────────
  const contract: EvidenceContract = decompose(params.question)
  if (contract.decomposition_method === 'keyword_generic') {
    disclosures.push(
      `Question did not match a heavy-question template — decomposed generically to ` +
      `primary_domain="${contract.primary_domain}". Cross-domain reach may be shallow.`,
    )
  }

  // ── (2) PLAN AGAINST PRE-AGGREGATED SURFACES FIRST ──────────────────────────
  // Orientation: the whole-chart gestalt verdict map (pre-aggregated; 1 row).
  const orientation = await gateway.gestalt(chart_id, ayanamsha_id)
  plan.push({
    stage: 'orient',
    surface: 'query_chart_gestalt',
    kind: 'pre_aggregated',
    note: orientation.found
      ? 'Whole-chart gestalt verdict map consulted before any atomic drill (B.11).'
      : 'Gestalt row absent — orientation stage disclosed as thin.',
  })
  if (!orientation.found) {
    disclosures.push('bodha_chart_gestalt returned no row for this chart/ayanamsha — orientation stage thin.')
  }

  // ── (3) MAP-REDUCE OVER EVIDENCE FAMILIES WITH RUNNING BUDGET ───────────────
  const drillFamilies = contract.families.filter(f => f.role !== 'orientation')
  let remaining = budget.total_signal_rows
  const families: FamilyComposite[] = []
  let sawCrossDomainPlan = false

  for (const fam of drillFamilies) {
    // Per-family exemplar allowance = min(per-family cap, remaining running budget).
    const allowance = Math.max(0, Math.min(budget.per_family_cap, remaining))

    if (allowance === 0) {
      // Budget exhausted — DISCLOSE the family (its size, that more remains), never dump it.
      // We still ask the surface for the family's TOTAL (a cheap disclosed count) with cap 0
      // is not meaningful; instead we probe with cap=1 only to read the disclosed total, then
      // serve 0 exemplars. This keeps the answer honest without spending budget.
      const probe = await gateway.familyDrill(chart_id, ayanamsha_id, fam.domain, 1)
      families.push({
        family_key: fam.family_key,
        domain: fam.domain,
        role: fam.role,
        total_in_family: probe.total_in_family,
        served: 0,
        more_available: probe.total_in_family > 0,
        exemplars: [],
        linkages: probe.linkages,
        disposition: 'budget_exhausted',
        note: `Running signal budget (${budget.total_signal_rows}) exhausted before this family — ` +
          `disclosed (total=${probe.total_in_family}), not dumped. Recover via query_domain_reading(domain=${fam.domain}).`,
      })
      continue
    }

    const drill = await gateway.familyDrill(chart_id, ayanamsha_id, fam.domain, allowance)
    const served = Math.min(drill.exemplars.length, allowance)
    remaining -= served
    if (drill.linkages.length > 0) sawCrossDomainPlan = true

    const thin = drill.total_in_family === 0 && drill.exemplars.length === 0
    if (thin) {
      disclosures.push(`Family "${fam.family_key}" (domain=${fam.domain}) is thin — 0 signals served/disclosed.`)
    }

    families.push({
      family_key: fam.family_key,
      domain: fam.domain,
      role: fam.role,
      total_in_family: Math.max(drill.total_in_family, served),
      served,
      more_available: drill.total_in_family > served,
      exemplars: drill.exemplars.slice(0, served),
      linkages: drill.linkages,
      disposition: thin ? 'thin_stage_disclosed' : 'served',
      note: thin
        ? `Thin stage — deepens when WP-2.2 populates domain evidence at W3.`
        : `Served ${served} exemplar(s) of ${drill.total_in_family} in family (per_family_cap=${budget.per_family_cap}, ` +
          `remaining budget after=${remaining}).`,
    })
  }

  // Record the cross-domain plan step (pre-aggregated CDLM cells surfaced via the drills).
  plan.push({
    stage: 'plan_cross_domain',
    surface: 'query_domain_reading→bodha_cdlm_cells',
    kind: 'pre_aggregated',
    note: sawCrossDomainPlan
      ? 'CDLM cross-domain linkage cells consulted to plan cross-domain reach (pre-aggregated, not atomic).'
      : 'No CDLM cells surfaced — cross-domain plan thin.',
  })
  plan.push({
    stage: 'map_reduce_families',
    surface: 'query_domain_reading→ranked_signals',
    kind: 'atomic_drill',
    note: `Map-reduced ${families.length} families under a running budget of ${budget.total_signal_rows} ` +
      `atomic rows (per_family_cap=${budget.per_family_cap}). Never a flat top-K wall.`,
  })

  // ── (3b) DISPOSITOR CHAINS (pre-aggregated CGM paths) ───────────────────────
  const paths = await gateway.dispositorPaths(chart_id, ayanamsha_id, budget.dispositor_cap)
  plan.push({
    stage: 'dispositor',
    surface: 'query_cgm_paths',
    kind: 'pre_aggregated',
    note: paths.length > 0
      ? `Surfaced ${paths.length} dispositor-chain path(s) (pre-aggregated CGM).`
      : 'No dispositor paths surfaced — CGM path stage thin.',
  })
  if (paths.length === 0) disclosures.push('bodha_cgm_paths returned no paths — dispositor stage thin.')

  // ── (3c) TENSION (contradictions — honest degradation where 0) ──────────────
  const tension = await gateway.tension(chart_id, ayanamsha_id)
  plan.push({
    stage: 'tension',
    surface: 'query_contradictions',
    kind: 'pre_aggregated',
    note: `Contradiction stage: ${tension.contradiction_count} tension pair(s).`,
  })
  if (tension.contradiction_count === 0) {
    disclosures.push(
      'Contradiction stage thin: bodha_contradictions=0 for this chart (documented LCA-6/WP-2.2 ' +
      'native-chart motif-zero defect). Disclosed, NOT fabricated — lights up at W3.',
    )
  }

  // ── (4) NARRATIVE + DERIVATION LEDGER ───────────────────────────────────────
  const narrative = buildNarrative(contract, orientation, families, paths, tension)
  const derivation_ledger = narrative.flatMap(s => s.ledger)

  const families_fully_served = families.filter(f => f.disposition === 'served' && !f.more_available).length
  const families_disclosed = families.filter(f => f.disposition === 'budget_exhausted').length

  return {
    chart_id,
    ayanamsha_id,
    question: params.question,
    contract,
    plan,
    families,
    narrative,
    derivation_ledger,
    budget: {
      total_signal_rows_cap: budget.total_signal_rows,
      total_signal_rows_served: budget.total_signal_rows - remaining,
      families_fully_served,
      families_disclosed_not_dumped: families_disclosed,
    },
    disclosures,
  }
}

// ── narrative + ledger assembly ────────────────────────────────────────────────

function exemplarIds(exemplars: SignalExemplar[]): string[] {
  return exemplars.map(e => e.signal_id).filter(Boolean)
}
function exemplarFactIds(exemplars: SignalExemplar[]): string[] {
  return Array.from(new Set(exemplars.flatMap(e => e.constituent_fact_ids))).filter(Boolean)
}

function buildNarrative(
  contract: EvidenceContract,
  orientation: Awaited<ReturnType<SurfaceGateway['gestalt']>>,
  families: FamilyComposite[],
  paths: Awaited<ReturnType<SurfaceGateway['dispositorPaths']>>,
  tension: Awaited<ReturnType<SurfaceGateway['tension']>>,
): NarrativeSection[] {
  const sections: NarrativeSection[] = []

  // Section 1 — orientation verdict (grounded in the gestalt verdict signal_id).
  {
    const ledger: DerivationLedgerEntry[] = []
    const pd = contract.primary_domain
    const verdict = orientation.verdict_map[pd]
    let body: string
    if (verdict && verdict.signal_id) {
      body =
        `Whole-chart orientation for "${contract.question}": the pre-computed gestalt verdict for the ` +
        `primary domain "${pd}" is ${verdict.verdict_class} (confidence ${verdict.confidence}). ` +
        `This is the composition's frame; the family evidence below either corroborates or tensions it.`
      ledger.push({
        claim: `Primary-domain "${pd}" gestalt verdict = ${verdict.verdict_class} (conf ${verdict.confidence}).`,
        signal_ids: [verdict.signal_id],
        fact_ids: [],
        source_surface: 'query_chart_gestalt.domain_verdict_map_jsonb',
      })
    } else {
      body =
        `Whole-chart orientation for "${contract.question}": no pre-computed gestalt verdict was available ` +
        `for "${pd}" (orientation stage thin — disclosed, not fabricated).`
    }
    sections.push({ heading: 'Orientation (whole-chart verdict)', body, ledger })
  }

  // Section 2..N — one section per drilled family, each with its own ledger.
  for (const fam of families) {
    const ledger: DerivationLedgerEntry[] = []
    let body: string
    if (fam.disposition === 'budget_exhausted') {
      body =
        `Evidence family "${fam.family_key}" (${fam.role}) holds ${fam.total_in_family} signals but was ` +
        `reached after the running budget was spent. It is DISCLOSED, not dumped: drill via ` +
        `query_domain_reading(domain=${fam.domain}) to compose it fully.`
    } else if (fam.disposition === 'thin_stage_disclosed') {
      body =
        `Evidence family "${fam.family_key}" (${fam.role}) is thin (0 signals) — disclosed; deepens at W3.`
    } else {
      const linkNote = fam.linkages.length > 0
        ? ` Cross-domain linkage: ${fam.linkages
            .slice(0, 3)
            .map(l => `${l.domain_row}↔${l.domain_col} (${l.shared_signal_count} shared)`)
            .join(', ')}.`
        : ''
      body =
        `Evidence family "${fam.family_key}" (${fam.role}): ${fam.served} of ${fam.total_in_family} signals ` +
        `composed as a bounded family composite (more_available=${fam.more_available}).` + linkNote +
        (fam.exemplars[0]?.headline ? ` Lead factor: ${fam.exemplars[0].headline}.` : '')
      const sigIds = exemplarIds(fam.exemplars)
      if (sigIds.length > 0) {
        ledger.push({
          claim: `Family "${fam.family_key}" composed from ${fam.served} signals (of ${fam.total_in_family}).`,
          signal_ids: sigIds,
          fact_ids: exemplarFactIds(fam.exemplars),
          source_surface: 'query_domain_reading.ranked_signals',
        })
      }
    }
    sections.push({ heading: `Family — ${fam.family_key}`, body, ledger })
  }

  // Section — dispositor chains (structural spine).
  if (paths.length > 0) {
    const ledger: DerivationLedgerEntry[] = [{
      claim: `Structural dispositor spine: ${paths.length} chain path(s) bear on the answer.`,
      signal_ids: [],
      fact_ids: [],
      source_surface: 'query_cgm_paths',
    }]
    const finals = paths.filter(p => p.is_final_dispositor).length
    sections.push({
      heading: 'Dispositor spine (CGM paths)',
      body: `${paths.length} dispositor-chain path(s) surfaced (${finals} final-dispositor). ` +
        `These are the structural indirections the promise resolves through.`,
      ledger,
    })
  }

  // Section — tension (honest disclosure where 0).
  sections.push({
    heading: 'Tension / contradiction check',
    body: tension.contradiction_count > 0
      ? `${tension.contradiction_count} contradiction pair(s) bear on this question — the dissent check.`
      : `No contradiction pairs available for this chart (thin stage disclosed — LCA-6/WP-2.2; not fabricated).`,
    ledger: [],
  })

  return sections
}
