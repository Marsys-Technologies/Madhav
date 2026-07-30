/**
 * kala_uncertainty.ts — ṢAḌ-DARŚANA W1 item 24-lite (SHAD_DARSHANA_BRIEF_v2_0.md §3 W1
 * "24-lite (Sūkṣma boundaries as intervals — propagation formula; full budget W2)"; design
 * authority KALA_SIX_VIEWS_DESIGN_v2_0.md §A.1 "The Sūkṣma consequence" + §A.6 "The
 * uncertainty budget", registry item 24: "Uncertainty-budget propagation (birth-time ×
 * ayanāṁśa → boundary intervals below PD; robustness vector on every claim)".
 * ==========================================================================
 * PURE interval math only — no network calls, no astrological computation, B.10-clean.
 * Callers (the six view facades) fetch the already-computed daśā-boundary row (chart_dashas
 * via `marsys://tool/L1/get_dashas`) and hand this file the row's own `duration_days` +
 * boundary instant; this file only computes the interval bound around it.
 *
 * ══════════════════════════════════════════════════════════════════════════════════════
 * WHAT "below PD" MEANS (grounding the scope, not inventing it):
 * `ga_dashas_writer.py`'s daśā hierarchy is MD (Mahā, level_n=1) → AD (Antar, level_n=2) →
 * PD (Pratyantar, level_n=3) → Sūkṣma (level_n=4) — and STOPS THERE by design ("CRITICAL
 * OVERRIDE 1: DEPTH = 4-level Sukshma... ZERO level_n=5" — no Prāṇa-daśā row exists for any
 * chart). KALA_SIX_VIEWS_DESIGN_v2_0.md §A.1: "At MD level the induced error is weeks
 * against periods of years — negligible. At Sūkṣma level the error exceeds the period
 * length. Therefore: error propagation is mandatory below PD." Level_n=4 (Sūkṣma) is
 * therefore the ONLY currently-computed level "below PD" (level_n=3) — this file's scope.
 *
 * WHAT THIS FILE IS NOT (W1-lite scope discipline — the brief is explicit that 24-lite is a
 * "documented, simple interval convention... not a fabricated number", and that the REAL
 * birth-time × ayanāṁśa error-propagation model is item 24-FULL, W2, gated on the synthetic
 * reference cohort (item 22) + the field (E1) that do not exist yet):
 *   - It does NOT compute birth-time uncertainty or cross-ayanāṁśa boundary drift (that is
 *     the real model §A.1 describes — a W2 job requiring the cohort/field substrate).
 *   - It does NOT claim statistical coverage (e.g. "95% CI") — the bound below is a
 *     documented placeholder convention, not a probability interval, and is labeled as such
 *     on every served value so no caller can mistake it for the W2 model's output.
 *
 * ── THE LITE-V0 CONVENTION (stated explicitly, per the brief's own requirement) ──────────
 * For a Sūkṣma-level (level_n=4) daśā boundary instant (its own `start_iso` or `end_iso`,
 * already computed and stored in `chart_dashas`), the served interval is symmetric:
 *   lower_bound = instant − (this Sūkṣma period's own duration_days / 2)
 *   upper_bound = instant + (this Sūkṣma period's own duration_days / 2)
 * Rationale: the next-finer classical subdivision (Prāṇa-daśā) is never computed for any
 * chart (the depth cap above), so the honest statement this file can make is "the boundary
 * is exact to Sūkṣma granularity; a further, uncomputed subdivision could in principle place
 * the felt transition anywhere within this Sūkṣma period's own span around the reported
 * instant." Using the period's OWN duration (already in the DB — no new computation) keeps
 * the bound proportional to how coarse or fine that particular period already is, without
 * inventing a new statistical model. This is intentionally a coarser (more conservative)
 * bound than the real error-propagation model will produce at W2 — see the convention
 * string itself, which every served interval carries verbatim for auditability.
 */

export const SUKSHMA_INTERVAL_CONVENTION_ID = 'lite_v0_half_own_duration'

export const SUKSHMA_INTERVAL_CONVENTION_TEXT =
  'lite-v0 placeholder (item 24-lite, SHAD_DARSHANA_BRIEF_v2_0.md W1): symmetric interval of ' +
  '± half of this Sūkṣma period\'s OWN duration_days, centered on the boundary instant. This ' +
  'is NOT the birth-time/ayanāṁśa error-propagation model (KALA_SIX_VIEWS_DESIGN_v2_0.md ' +
  '§A.1/§A.6, item 24-full) — that model lands at W2 once the synthetic reference cohort ' +
  '(item 22) and the field (E1) exist. This lite bound instead reflects the honest, already-' +
  'true fact that the next-finer classical subdivision (Prāṇa-daśā, level_n=5) is NEVER ' +
  'computed for any chart by design (ga_dashas_writer.py "CRITICAL OVERRIDE 1... ZERO ' +
  'level_n=5") — so the true transition instant, refined one level further, could fall ' +
  'anywhere within this Sūkṣma period\'s own span around the reported boundary. A ' +
  'probability/confidence-level claim (e.g. "95% CI") would be a fabrication at this tier — ' +
  'this is a documented convention, not a statistical estimate.'

export type SukshmaBoundaryEdge = 'start' | 'end'

export interface SukshmaBoundaryInterval {
  level_name: 'sukshma'
  system_id: string
  lord_graha: string
  edge: SukshmaBoundaryEdge
  instant_iso: string
  lower_bound_iso: string
  upper_bound_iso: string
  half_span_days: number
  convention_id: typeof SUKSHMA_INTERVAL_CONVENTION_ID
  convention: string
}

/**
 * Builds the lite-v0 interval for one Sūkṣma-level boundary instant. Pure function — no
 * network, no randomness, deterministic given the same inputs (a `chart_dashas` row's own
 * already-computed `duration_days` + the boundary's own already-computed ISO instant).
 *
 * `durationDays` must be the SŪKṢMA PERIOD'S OWN duration (its `duration_days` column,
 * already computed by `ga_dashas_writer.py` — never re-derived here), not any ancestor
 * period's span — the convention above is specific about which duration anchors the bound.
 */
export function buildSukshmaBoundaryInterval(params: {
  systemId: string
  lordGraha: string
  edge: SukshmaBoundaryEdge
  instantIso: string
  durationDays: number
}): SukshmaBoundaryInterval | null {
  const instantMs = new Date(params.instantIso).getTime()
  if (Number.isNaN(instantMs) || !Number.isFinite(params.durationDays) || params.durationDays <= 0) {
    return null
  }
  const halfSpanDays = params.durationDays / 2
  const halfSpanMs = halfSpanDays * 86_400_000
  return {
    level_name: 'sukshma',
    system_id: params.systemId,
    lord_graha: params.lordGraha,
    edge: params.edge,
    instant_iso: params.instantIso,
    lower_bound_iso: new Date(instantMs - halfSpanMs).toISOString(),
    upper_bound_iso: new Date(instantMs + halfSpanMs).toISOString(),
    half_span_days: Math.round(halfSpanDays * 1000) / 1000,
    convention_id: SUKSHMA_INTERVAL_CONVENTION_ID,
    convention: SUKSHMA_INTERVAL_CONVENTION_TEXT,
  }
}

/** Builds BOTH edges (start + end) for one Sūkṣma-level `chart_dashas` row in one call —
 *  the shape a view facade actually wants ("this period's entry AND exit, each honestly
 *  bounded"). Returns an empty array (never a fabricated entry) for any edge whose instant
 *  or duration is missing/invalid. */
export function buildSukshmaBoundaryIntervals(row: {
  system_id: string
  lord_graha: string
  start_iso: string | null | undefined
  end_iso: string | null | undefined
  duration_days: number | string | null | undefined
}): SukshmaBoundaryInterval[] {
  const durationDays =
    typeof row.duration_days === 'string' ? Number(row.duration_days) : (row.duration_days ?? NaN)
  const out: SukshmaBoundaryInterval[] = []
  if (row.start_iso) {
    const iv = buildSukshmaBoundaryInterval({
      systemId: row.system_id, lordGraha: row.lord_graha, edge: 'start', instantIso: row.start_iso, durationDays,
    })
    if (iv) out.push(iv)
  }
  if (row.end_iso) {
    const iv = buildSukshmaBoundaryInterval({
      systemId: row.system_id, lordGraha: row.lord_graha, edge: 'end', instantIso: row.end_iso, durationDays,
    })
    if (iv) out.push(iv)
  }
  return out
}
