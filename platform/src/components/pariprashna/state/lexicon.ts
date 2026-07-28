/**
 * Paripraśna phase lexicon — STUB.
 *
 * SOURCING NOTE (read this before touching): the design plan (§7.8) puts the
 * canonical closed vocabulary at `platform/src/lib/pariprashna/lexicon.ts`,
 * owned by lane S-2. That path is OUTSIDE this lane's (C-1, "the renderer")
 * file scope (may_touch is limited to the pariprashna app route + this
 * component tree), and at the time this file was written S-2's worktree
 * (`Madhav-pb-1-s2`) had not yet created it. This is a minimal local
 * stand-in covering the strings the mockup and §7.8 specify, so the
 * renderer has something real to display. **S-2's `lib/pariprashna/lexicon.ts`
 * is the source of truth — when it lands, this file's exports should be
 * replaced with a re-export from it (or deleted and all imports repointed),
 * not merged/reconciled by hand.**
 *
 * The rule this table exists to enforce (§7.8): every activity/phase label
 * shown to a reader comes from this closed map. An engine capability with no
 * entry falls back to `CONSULTING THE CHART` — never a raw tool/asset name.
 */

export const BAND_PHASE_LABEL: Record<string, string> = {
  scope_resolution: 'Reading the question',
  session_recall: 'Recalling past readings',
  plan_compile: 'Composing the approach',
  whole_chart_read: 'Reading the whole chart',
  classical_corpus: 'Consulting the classics',
  dossier_full_coverage: 'Completing full coverage',
  synthesis: 'Composing the reading',
  grounding_gate: 'Verifying every claim',
  seal: 'Sealing',
}

export const RETRIEVAL_FACET_LABEL: Record<string, string> = {
  dasha_structure: 'Daśā structure',
  transit_windows: 'Transit windows',
  house_lordships: 'House & lordships',
  yogas_cross_checked: 'Yogas, cross-checked',
  strengths_dignities: 'Strengths & dignities',
  divisional_charts: 'Divisional charts',
  sensitive_degrees: 'Sensitive degrees',
  remedial_tradition: 'Remedial tradition',
}

export const SEAM_LABEL: Record<string, string> = {
  looking_further: 'Looking further —',
  reading_deeper: 'Reading deeper —',
  cross_checking: 'Cross-checking before concluding',
  reconsidering: 'Reconsidering —',
}

export const EDGE_STATE_LABEL: Record<string, string> = {
  clarification: 'A question first',
  open_window: 'Before I answer —',
  chart_rebuilt: 'The chart has been rebuilt — re-reading',
  reconnecting: 'Reconnecting…',
  resumed: 'Resumed — nothing lost',
  provider_busy: 'The model is busy — retrying',
  taking_long: 'Taking longer than usual…',
  served_within_limits: 'Served within limits',
  stopped: 'Stopped — kept what arrived',
  model_switch_queued: 'Will switch next turn',
  queue_wait: 'In line — starts in a moment',
}

/** §7.8 fallback: an unmapped engine capability renders this, never a raw id. */
export const FALLBACK_BAND_LABEL = 'Consulting the chart'

export function resolveBandLabel(labelKey: string): string {
  return BAND_PHASE_LABEL[labelKey] ?? FALLBACK_BAND_LABEL
}

export function resolveRetrievalFacet(facetKey: string): string {
  return RETRIEVAL_FACET_LABEL[facetKey] ?? 'Chart data'
}

export const SETTLED_BAND_TEMPLATE = (factorCount: number, classicalCount: number, elapsedLabel: string) =>
  classicalCount > 0
    ? `Grounded in ${factorCount} chart factors · ${classicalCount} classical sources · ${elapsedLabel}`
    : `Grounded in ${factorCount} chart factors · ${elapsedLabel}`
