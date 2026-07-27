/**
 * bodha_l1_linkage.ts — ŚODHANA T2 (MC-001 freshness stamp).
 *
 * Every Bodha-derived response is grounded in an L1 (Gaṇita) build via each
 * signal's `constituent_facts_array`, whose members are `chart_facts.fact_id`
 * values. L1's `fact_id` is `sha256(category|subject|key|chart|ayanamsha|BUILD_ID)`
 * — it embeds the L1 build_id. So when L1 is rebuilt (delete-then-insert), every
 * prior fact_id changes and a Bodha build made against the OLD L1 build is left
 * pointing at fact_ids that no longer exist (the live MC-001 defect: 100% of
 * 71,430 constituent refs orphaned on chart 482012f1).
 *
 * This module produces a machine-readable freshness stamp that ANY Bodha-serving
 * tool can attach so a caller can tell, without reading `bodha_quality_get`,
 * whether the served Bodha layer still resolves against live L1:
 *
 *   bodha_l1_linkage: { built_against_hash, live_hash, fresh }
 *
 *   built_against_hash — the L1 build_id the served Bodha rows resolve to (the
 *                        build they were computed against). `null` when the served
 *                        rows resolve to no live L1 build (their source build was
 *                        replaced and is gone — a stale/orphaned linkage).
 *   live_hash          — the L1 build_id currently live for the chart.
 *   fresh              — built_against_hash === live_hash AND resolution is intact.
 *
 * Design: a pure stamp core (`makeBodhaL1Linkage`) plus a resolver
 * (`resolveBodhaL1Linkage`) that takes an injected `LinkageProbe` — the small set
 * of chart-scoped facts it needs (live L1 build + constituent-resolution sample).
 * Dependency injection keeps this module decoupled from any particular DB/HTTP
 * path and fully unit-testable; concrete probes are supplied by callers that have
 * a query surface (a `query_chart_facts` primitive, a pg pool, etc.).
 */

export interface BodhaL1Linkage {
  built_against_hash: string | null
  live_hash: string | null
  fresh: boolean
  /** Fraction (0..100) of sampled constituent refs that resolve against live L1. */
  constituent_resolution_pct: number | null
  /** Human note; present when NOT fresh so the caller can surface the reason. */
  note?: string
}

/** The chart-scoped facts the freshness decision needs, gathered by the caller. */
export interface LinkageProbe {
  /** Current live L1 build_id for the chart (from chart_facts). null if no L1 build. */
  liveL1BuildId: string | null
  /**
   * Constituent-resolution sample: how many sampled Bodha constituent fact_ids
   * resolve against the LIVE chart_facts, and how many were sampled.
   * resolved/sampled === 1 → linkage intact; === 0 → fully orphaned.
   */
  sampledConstituentRefs: number
  resolvedConstituentRefs: number
  /**
   * The L1 build_id the resolving constituents point to, when derivable
   * (all live chart_facts share one build_id, so any resolving ref implies it).
   * null when nothing resolves.
   */
  resolvedToL1BuildId: string | null
}

/** Fraction of constituent refs that must resolve for the linkage to be `fresh`. */
export const FRESH_RESOLUTION_THRESHOLD = 0.99

/**
 * Pure freshness decision from a gathered probe. No I/O.
 */
export function makeBodhaL1Linkage(probe: LinkageProbe): BodhaL1Linkage {
  const { liveL1BuildId, sampledConstituentRefs, resolvedConstituentRefs, resolvedToL1BuildId } = probe

  const resolutionPct = sampledConstituentRefs > 0
    ? (resolvedConstituentRefs / sampledConstituentRefs) * 100
    : null

  // Intact when (nearly) every sampled ref resolves AND the build it resolves to
  // matches the live build. `built_against_hash` is the build the served rows
  // resolve to — null when nothing resolves (source build replaced & gone).
  const resolutionOk =
    sampledConstituentRefs > 0 &&
    resolvedConstituentRefs / sampledConstituentRefs >= FRESH_RESOLUTION_THRESHOLD

  const builtAgainstHash = resolutionOk ? resolvedToL1BuildId : (resolvedConstituentRefs > 0 ? resolvedToL1BuildId : null)
  const fresh = resolutionOk && builtAgainstHash != null && builtAgainstHash === liveL1BuildId

  const linkage: BodhaL1Linkage = {
    built_against_hash: builtAgainstHash,
    live_hash: liveL1BuildId,
    fresh,
    constituent_resolution_pct: resolutionPct == null ? null : Math.round(resolutionPct * 100) / 100,
  }

  if (!fresh) {
    if (sampledConstituentRefs === 0) {
      linkage.note = 'No Bodha constituent refs sampled — freshness indeterminate.'
    } else if (resolvedConstituentRefs === 0) {
      linkage.note =
        'STALE: 0% of sampled Bodha constituent refs resolve against live L1 — the Bodha layer ' +
        'was built against an L1 build that has since been replaced (delete-then-insert rebuild). ' +
        'Served Bodha groundings do not resolve to live chart_facts. See MC-001 / bodha_quality_get.'
    } else {
      linkage.note =
        `PARTIAL: ${linkage.constituent_resolution_pct}% of sampled Bodha constituent refs resolve ` +
        'against live L1; the Bodha layer is partially stale relative to the current L1 build.'
    }
  }

  return linkage
}

/** Async probe supplier — a caller-provided function that gathers a LinkageProbe. */
export type LinkageProbeSupplier = (chartId: string) => Promise<LinkageProbe>

/**
 * Resolve the freshness stamp for a chart. Thin async wrapper over an injected
 * probe supplier; the supplier owns the actual DB/primitive queries.
 */
export async function resolveBodhaL1Linkage(
  chartId: string,
  probeSupplier: LinkageProbeSupplier,
): Promise<BodhaL1Linkage> {
  try {
    const probe = await probeSupplier(chartId)
    return makeBodhaL1Linkage(probe)
  } catch (err) {
    return {
      built_against_hash: null,
      live_hash: null,
      fresh: false,
      constituent_resolution_pct: null,
      note: `bodha_l1_linkage probe failed: ${err instanceof Error ? err.message : String(err)}`,
    }
  }
}
