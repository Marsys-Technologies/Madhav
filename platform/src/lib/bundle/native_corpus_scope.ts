/**
 * native_corpus_scope.ts — the chart-scoping authority for native-bound corpus
 * assets injected into a synthesis prompt (V3-E-016, CRITICAL).
 *
 * ── The defect this closes ────────────────────────────────────────────────
 * `CAPABILITY_MANIFEST.json` marks a subset of assets with `native_id`
 * ("abhisek"): CGM, MSR, CDLM, RM, UCN, LEL. These are not reference corpus —
 * they are ONE specific person's chart, read verbatim off the repo and joined
 * into the synthesis system prompt by `bundle_hydrator.ts` →
 * `synthesis_stage.ts:assembleSynthesisContext`. `bundle_hydrator` additionally
 * force-injects CGM as a FLOOR asset on every single turn.
 *
 * Nothing in that path had ever consulted the chart the turn was about. So a
 * turn about ANY chart — the synthetic operator-E2E chart, or any of the other
 * real people whose charts exist in production — received the native's own
 * ~79KB Chart Gestalt Map (his Moon nakshatra, his exact natal degree, his
 * birth date and birth place) in its system prompt. Live-reproduced on the
 * deployed web door: a synthetic-chart factual query answered with the native's
 * real Moon nakshatra and Lagna.
 *
 * ── Why the binding lives here and not in the database ────────────────────
 * `public.charts.native_id` looks like the natural join key and is NOT usable:
 * it is `VARCHAR(64) NOT NULL DEFAULT 'abhisek'` (migration 008), and every row
 * in production carries the default — including the synthetic test chart and
 * four other real people's charts. Keying authorization off that column would
 * admit the native's corpus for every chart in existence, i.e. it would encode
 * the bug as the fix. The binding below is therefore explicit, narrow, and
 * auditable in source.
 *
 * ── Discipline (CLAUDE.md §N.8, Earned-Signal) ────────────────────────────
 * The predicate answers the question it claims to answer: "is this specific
 * asset about this specific chart?" — not a proxy for it. It FAILS CLOSED: an
 * asset declaring a `native_id` this module has no binding for is inadmissible
 * everywhere, so adding a new native's corpus to the manifest without also
 * binding it here withholds it rather than broadcasting it.
 */

/**
 * native_id → the ONE chart_id whose subject that native's corpus describes.
 *
 * Adding an entry here is an authorization decision: it grants that chart's
 * turns access to that native's private corpus documents. Do not add a binding
 * without confirming the corpus genuinely describes that chart's subject.
 */
export const NATIVE_CORPUS_CHART_BINDINGS: Readonly<Record<string, string>> = Object.freeze({
  // Abhisek Mohanty — CLAUDE.md §B canonical chart_id. CGM/MSR/CDLM/RM/UCN/LEL
  // are all his chart, and only his.
  abhisek: '482012f1-710e-4a25-994a-93821f5871aa',
})

/** The manifest fields this module needs. Structurally typed so callers pass `AssetEntry` directly. */
export interface NativeScopableAsset {
  readonly canonical_id: string
  readonly native_id?: string | null
}

/**
 * True when an asset is bound to one specific native's chart (as opposed to
 * chart-agnostic reference material such as classical corpus or doctrine).
 */
export function isNativeScopedAsset(entry: NativeScopableAsset): boolean {
  return typeof entry.native_id === 'string' && entry.native_id.length > 0
}

export type ScopeDecision =
  | { admissible: true; reason: 'chart_agnostic' | 'native_binding_matches' }
  | { admissible: false; reason: 'native_binding_mismatch' | 'native_binding_unknown' }

/**
 * The scoping decision for one asset against one chart.
 *
 * - No `native_id` → chart-agnostic, admissible everywhere (unchanged behaviour).
 * - `native_id` bound to THIS chart → admissible (unchanged behaviour for the
 *   native's own chart; this fix does not narrow his own reading).
 * - `native_id` bound to a DIFFERENT chart → inadmissible. This is the leak.
 * - `native_id` with no binding at all → inadmissible (fail closed).
 */
export function decideAssetScope(entry: NativeScopableAsset, chartId: string): ScopeDecision {
  if (!isNativeScopedAsset(entry)) return { admissible: true, reason: 'chart_agnostic' }
  const boundChartId = NATIVE_CORPUS_CHART_BINDINGS[entry.native_id as string]
  if (boundChartId === undefined) return { admissible: false, reason: 'native_binding_unknown' }
  if (boundChartId === chartId) return { admissible: true, reason: 'native_binding_matches' }
  return { admissible: false, reason: 'native_binding_mismatch' }
}

/** Convenience predicate over {@link decideAssetScope}. */
export function isAssetAdmissibleForChart(entry: NativeScopableAsset, chartId: string): boolean {
  return decideAssetScope(entry, chartId).admissible
}
