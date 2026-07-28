/**
 * Paripraśna Build — PB-1 (DHĀRĀ), Lane S-2: the closed reader-facing lexicon.
 * ============================================================================
 *
 * While a turn streams, the UI shows a "working band" — a plain-language label
 * of what the engine is doing right now (e.g. "Consulting the chart — Daśā
 * structure"). This module is the CLOSED, EXHAUSTIVE vocabulary for that band.
 *
 * HARD RULE: nothing outside this module may ever be rendered as a band/activity
 * label. No internal tool name, asset id (`ga_`/`bo_`/`ka_`/`ph_`/`mi_`/`bg_`
 * prefixed), table name, or layer name ("L0"–"L5") may leak to the reader. This
 * file makes that leak structurally impossible by being the ONLY source of
 * strings a server-side resolver is allowed to emit:
 *
 *   registry capability (`register.reader_label`) ──▶ resolveReaderLabel() ──▶
 *   a string drawn EXCLUSIVELY from this module (or FALLBACK_READER_LABEL)
 *
 * DESIGN PRINCIPLE (native-ruled, PB-1 kickoff): the SERVER resolves
 * `label_key` -> display string. The CLIENT renders strings verbatim and
 * carries NO mapping table of its own — a client-side copy of this map could
 * drift out of sync with a future edit here and leak. C-1 (a later lane) builds
 * the client and imports this module directly; it does not re-author labels.
 *
 * VOICE RULES:
 *  - present-participle verbs ("Consulting", "Composing", "Verifying" — not
 *    "Consult"/"Consulted").
 *  - no first person ("I"/"we"/"my") anywhere in the lexicon.
 *  - Sanskrit is used ONLY as a facet name that IS the object being consulted
 *    (e.g. "Daśā structure") — never as a stand-in for an internal asset id.
 *  - every string below is authored in natural (sentence) case. The CLIENT
 *    applies `text-transform: uppercase` + letter-spacing at render time
 *    (tracked-caps styling) — do NOT upper-case strings in this module; doing
 *    so would fight the client's CSS and break the "just data" contract.
 *
 * This module is pure data + pure functions. It imports nothing from the
 * retrieval registry, the chat route, or platform-mcp — it has zero knowledge
 * of *when* a label is shown, only *what* the closed vocabulary of labels is.
 */

// ─────────────────────────────────────────────────────────────────────────────
// 1. Band-level phases — one at a time, in order, each label flips in place
//    at constant height.
// ─────────────────────────────────────────────────────────────────────────────

/** Stable identifiers for the ten band-level phases, in their fixed order. */
export type BandPhaseId =
  | 'scope_resolution'
  | 'session_recall'
  | 'plan_compile'
  | 'whole_chart_read'
  | 'retrieval'
  | 'classical_corpus'
  | 'full_coverage'
  | 'synthesis'
  | 'grounding_gate'
  | 'seal'

export interface BandPhaseSpec {
  id: BandPhaseId
  /** 1-based position in the fixed band sequence. */
  order: number
  /** The base label (natural case; client upper-cases). */
  label: string
  /** True if this phase's label may append a runtime-computed suffix. */
  suffixable: boolean
  /** One-line description of what the suffix carries, if `suffixable`. */
  suffix_note?: string
}

/**
 * The ten band-level phases in fixed order. `retrieval` (phase 5) does not
 * carry a single static label — see `RETRIEVAL_FACET_LABELS` below for its
 * closed set of facet-qualified renderings.
 */
export const BAND_PHASES: readonly BandPhaseSpec[] = [
  { id: 'scope_resolution', order: 1, label: 'Reading the question', suffixable: false },
  { id: 'session_recall', order: 2, label: 'Recalling past readings', suffixable: false },
  {
    id: 'plan_compile',
    order: 3,
    label: 'Composing the approach',
    suffixable: true,
    suffix_note: 'May append "· N steps" once the step count is known.',
  },
  { id: 'whole_chart_read', order: 4, label: 'Reading the whole chart', suffixable: false },
  {
    id: 'retrieval',
    order: 5,
    label: 'Consulting the chart',
    suffixable: true,
    suffix_note:
      'ALWAYS rendered as "Consulting the chart — ⟨facet⟩"; see RETRIEVAL_FACET_LABELS ' +
      'and DIVISIONAL_CHART_LABELS for the closed set of valid ⟨facet⟩ values.',
  },
  { id: 'classical_corpus', order: 6, label: 'Consulting the classics', suffixable: false },
  {
    id: 'full_coverage',
    order: 7,
    label: 'Completing full coverage',
    suffixable: true,
    suffix_note: 'May append "· NN%" progress.',
  },
  {
    id: 'synthesis',
    order: 8,
    label: 'Composing the reading',
    suffixable: true,
    suffix_note:
      'Reasoning-token models add a collapsed "Deliberating" row with a token count ' +
      '(see SYNTHESIS_DELIBERATING_LABEL below); this is a child row, not a suffix on ' +
      'this label itself.',
  },
  {
    id: 'grounding_gate',
    order: 9,
    label: 'Verifying every claim',
    suffixable: true,
    suffix_note: 'May append "· 14/14" as citations validate (n = validated, m = total).',
  },
  {
    id: 'seal',
    order: 10,
    label: 'Sealing',
    suffixable: false,
    suffix_note:
      'Flips in place to SEAL_COMPLETE_LABEL ("Grounded in ⟨n⟩ sources · ⟨t⟩s") once ' +
      'persistence completes — see renderSealCompleteLabel().',
  },
] as const

/** The collapsed child row shown under `synthesis` for reasoning-token models. */
export const SYNTHESIS_DELIBERATING_LABEL = 'Deliberating'

/** Format the phase-3 label with an optional known step count. */
export function renderPlanCompileLabel(stepCount?: number): string {
  const base = BAND_PHASES[2].label
  return typeof stepCount === 'number' && stepCount > 0 ? `${base} · ${stepCount} steps` : base
}

/** Format the phase-7 label with an optional coverage percentage (0-100). */
export function renderFullCoverageLabel(percent?: number): string {
  const base = BAND_PHASES[6].label
  if (typeof percent !== 'number') return base
  const clamped = Math.max(0, Math.min(100, Math.round(percent)))
  return `${base} · ${clamped}%`
}

/** Format the phase-8 deliberating child row with a token count. */
export function renderDeliberatingLabel(tokenCount: number): string {
  return `${SYNTHESIS_DELIBERATING_LABEL} · ${Math.max(0, Math.round(tokenCount))} tokens`
}

/** Format the phase-9 label with optional validated/total citation counts. */
export function renderGroundingGateLabel(validated?: number, total?: number): string {
  const base = BAND_PHASES[8].label
  if (typeof validated !== 'number' || typeof total !== 'number') return base
  return `${base} · ${validated}/${total}`
}

/** Format the phase-10 "sealed" flip-state label. */
export function renderSealCompleteLabel(sourceCount: number, elapsedSeconds: number): string {
  const n = Math.max(0, Math.round(sourceCount))
  const t = Math.max(0, Math.round(elapsedSeconds))
  return `Grounded in ${n} sources · ${t}s`
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. Retrieval facets (band phase 5) — "Consulting the chart — ⟨facet⟩"
// ─────────────────────────────────────────────────────────────────────────────

/** The closed set of facet keys for band phase 5's per-family retrieval label. */
export type RetrievalFacetKey =
  | 'dasha_structure'
  | 'transit_windows'
  | 'house_lordships'
  | 'yogas_cross_checked'
  | 'strengths_dignities'
  | 'divisional_charts'
  | 'sensitive_degrees'
  | 'remedial_tradition'

/** Plain-language facet names, in natural case, keyed by RetrievalFacetKey. */
export const RETRIEVAL_FACET_NAMES: Readonly<Record<RetrievalFacetKey, string>> = {
  dasha_structure: 'Daśā structure',
  transit_windows: 'Transit windows',
  house_lordships: 'House & lordships',
  yogas_cross_checked: 'Yogas, cross-checked',
  strengths_dignities: 'Strengths & dignities',
  divisional_charts: 'Divisional charts',
  sensitive_degrees: 'Sensitive degrees',
  remedial_tradition: 'Remedial tradition',
} as const

/** Render the full band-5 label for a given facet: "Consulting the chart — ⟨facet⟩". */
export function renderRetrievalLabel(facet: RetrievalFacetKey): string {
  return `${BAND_PHASES[4].label} — ${RETRIEVAL_FACET_NAMES[facet]}`
}

/**
 * The closed set of every fully-rendered band-5 label (one per facet). This is
 * the set a registry capability's `register.reader_label` is drawn from when
 * the capability belongs to the `divisional_charts` facet's GENERIC form —
 * capabilities for a SPECIFIC divisional chart use `DIVISIONAL_CHART_LABELS`
 * (below) instead of `divisional_charts`'s generic name.
 */
export const RETRIEVAL_FACET_LABELS: ReadonlySet<string> = new Set(
  (Object.keys(RETRIEVAL_FACET_NAMES) as RetrievalFacetKey[]).map(renderRetrievalLabel)
)

/**
 * Divisional-chart (varga) plain names — "may append plain names like 'the
 * marriage chart'/'the career chart' when a specific divisional applies"
 * (band-5 spec). Keyed by the varga's D-number (the standard shorthand used
 * across the L1 divisionals asset, e.g. chart_divisionals.varga = 'D9'), NOT
 * by any internal asset id. A varga absent from this map falls back to the
 * generic `divisional_charts` facet name above — this map is illustrative
 * coverage of the vargas an interpretive career/timing/health floor actually
 * names by domain, not a claim that every classical varga has a colloquial name.
 */
export const DIVISIONAL_CHART_LABELS: Readonly<Record<string, string>> = {
  D1: 'the birth chart',
  D2: 'the wealth chart',
  D3: 'the siblings chart',
  D4: 'the property chart',
  D6: 'the health chart',
  D7: 'the children chart',
  D9: 'the marriage chart',
  D10: 'the career chart',
  D12: 'the parents chart',
  D16: 'the vehicles chart',
  D20: 'the spiritual-practice chart',
  D24: 'the education chart',
  D30: 'the adversities chart',
  D60: 'the fine-grained karma chart',
} as const

/**
 * Render the band-5 label for a specific varga, falling back to the generic
 * "Divisional charts" facet name when the varga has no colloquial mapping
 * (e.g. an unlisted or malformed varga code) or is omitted entirely.
 */
export function renderDivisionalLabel(vargaCode?: string): string {
  const name = vargaCode ? DIVISIONAL_CHART_LABELS[vargaCode.toUpperCase()] : undefined
  return `${BAND_PHASES[4].label} — ${name ?? RETRIEVAL_FACET_NAMES.divisional_charts}`
}

/** The closed set of every fully-rendered per-varga band-5 label. */
export const DIVISIONAL_CHART_RETRIEVAL_LABELS: ReadonlySet<string> = new Set(
  Object.keys(DIVISIONAL_CHART_LABELS).map((code) => renderDivisionalLabel(code))
)

// ─────────────────────────────────────────────────────────────────────────────
// 3. Seam lexicon — pass boundaries on adaptive multi-pass turns
// ─────────────────────────────────────────────────────────────────────────────

export type SeamKey = 'looking_further' | 'reading_deeper' | 'cross_checking' | 'reconsidering'

/** Fixed seam phrases (pass-boundary labels), in natural case. */
export const SEAM_LABELS: Readonly<Record<SeamKey, string>> = {
  looking_further: 'Looking further —',
  reading_deeper: 'Reading deeper —',
  cross_checking: 'Cross-checking before concluding',
  reconsidering: 'Reconsidering —',
} as const

// ─────────────────────────────────────────────────────────────────────────────
// 4. Edge / exception states — each a fixed lexicon entry
// ─────────────────────────────────────────────────────────────────────────────

export type EdgeStateKey =
  | 'clarification_needed'
  | 'open_prediction_window'
  | 'chart_rebuilt'
  | 'network_drop'
  | 'network_resumed'
  | 'provider_busy'
  | 'timeout_20s'
  | 'capped_partial'
  | 'user_stopped'
  | 'model_switch_queued'
  | 'queue_wait'

/** Static (non-parameterized) edge/exception labels. */
export const EDGE_STATE_LABELS: Readonly<Record<Exclude<EdgeStateKey,
  'capped_partial' | 'model_switch_queued'>, string>> = {
  clarification_needed: 'A question first',
  open_prediction_window: 'Before I answer —',
  chart_rebuilt: 'The chart has been rebuilt — re-reading',
  network_drop: 'Reconnecting…',
  network_resumed: 'Resumed — nothing lost',
  provider_busy: 'The model is busy — retrying',
  timeout_20s: 'Taking longer than usual…',
  user_stopped: 'Stopped — kept what arrived',
  queue_wait: 'In line — starts in a moment',
} as const

/** Cost/coverage cap trips (partial): "Served within limits — ⟨n⟩ of ⟨m⟩ steps". */
export function renderCappedPartialLabel(stepsCompleted: number, stepsTotal: number): string {
  const n = Math.max(0, Math.round(stepsCompleted))
  const m = Math.max(0, Math.round(stepsTotal))
  return `Served within limits — ${n} of ${m} steps`
}

/** Mid-turn model switch queued: "Will switch to ⟨model⟩ next turn". `model` MUST be a
 *  reader-facing model name (e.g. "Opus"), never a raw model id/slug. */
export function renderModelSwitchQueuedLabel(modelDisplayName: string): string {
  return `Will switch to ${modelDisplayName} next turn`
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. Fallback + closed-set validation
// ─────────────────────────────────────────────────────────────────────────────

/**
 * The fallback reader label. ANY capability without a mapped `reader_label`
 * (i.e. its registry descriptor's `register.reader_label` is unset, OR is set
 * to a string that is not a member of this module's closed lexicon) renders
 * this string instead — NEVER its raw uri/asset-id/table/layer name.
 */
export const FALLBACK_READER_LABEL = 'Retrieved — chart data'

/**
 * Every STATIC, fully-rendered string a registry capability may legally set as
 * its `register.reader_label` (band phases 4 and 6, plus the generic band-5
 * facet renderings and the per-varga band-5 renderings). Band phases with
 * runtime-only suffixes (3, 7, 8's deliberating child, 9, 10) and the seam /
 * edge-state lexicons are turn-scoped UI state, not something a capability
 * descriptor declares statically — they are exported above for the future
 * client/route consumer (C-1 and later lanes), not for registry validation.
 */
export const STATIC_REGISTRY_READER_LABELS: ReadonlySet<string> = new Set<string>([
  BAND_PHASES.find((p) => p.id === 'whole_chart_read')!.label, // 'Reading the whole chart'
  BAND_PHASES.find((p) => p.id === 'classical_corpus')!.label, // 'Consulting the classics'
  ...RETRIEVAL_FACET_LABELS,
  ...DIVISIONAL_CHART_RETRIEVAL_LABELS,
])

/**
 * The full closed lexicon: every string this module can ever produce, static
 * or as a template. Used by the leak-proofing tests (tests/pariprashna/) to
 * assert the vocabulary is genuinely exhaustive and that no capability's
 * `register.reader_label` value falls outside it.
 */
export const CLOSED_LEXICON_STRINGS: ReadonlySet<string> = new Set<string>([
  ...BAND_PHASES.map((p) => p.label),
  SYNTHESIS_DELIBERATING_LABEL,
  ...RETRIEVAL_FACET_LABELS,
  ...DIVISIONAL_CHART_RETRIEVAL_LABELS,
  ...Object.values(SEAM_LABELS),
  ...Object.values(EDGE_STATE_LABELS),
  FALLBACK_READER_LABEL,
])

/**
 * A capability shape narrow enough for `resolveReaderLabel` — matches the
 * relevant slice of `CapabilityDescriptor` (registry/types.ts) without
 * importing it, keeping this module dependency-free.
 */
export interface ReaderLabelSource {
  uri: string
  register?: {
    reader_label?: string
  }
}

/**
 * Resolve a capability's reader-facing working-band label.
 *
 * Contract:
 *  - if `register.reader_label` is set AND is a member of the closed static
 *    lexicon (`STATIC_REGISTRY_READER_LABELS`), return it verbatim;
 *  - otherwise (unset, OR set to something outside the closed lexicon — e.g. a
 *    future edit typo'd a bespoke string inline on a descriptor instead of
 *    drawing from this module) fire `onUnmapped` (a CI-visible warning by
 *    default) and return `FALLBACK_READER_LABEL`.
 *
 * This function NEVER returns `capability.uri`, `capability.register?.reader_label`
 * verbatim-but-unvalidated, or any derivative of either — the fallback path is
 * the only exit when the declared value isn't provably safe.
 */
export function resolveReaderLabel(
  capability: ReaderLabelSource,
  onUnmapped: (message: string, uri: string) => void = defaultUnmappedWarning
): string {
  const declared = capability.register?.reader_label

  if (declared !== undefined) {
    if (STATIC_REGISTRY_READER_LABELS.has(declared)) {
      return declared
    }
    onUnmapped(
      `capability "${capability.uri}" declares register.reader_label "${declared}" which is ` +
        'NOT a member of the closed lexicon (STATIC_REGISTRY_READER_LABELS in ' +
        'src/lib/pariprashna/lexicon.ts). Falling back to FALLBACK_READER_LABEL. Fix the ' +
        'typo or add the string to the closed lexicon — never author a bespoke label inline ' +
        'on a capability descriptor.',
      capability.uri
    )
    return FALLBACK_READER_LABEL
  }

  onUnmapped(
    `no reader_label mapped for capability "${capability.uri}" — falling back to the generic ` +
      'reader label. Expected for capabilities outside the acharya-grade interpretive floor; ' +
      'if this capability SHOULD show a working-band label, add register.reader_label drawn ' +
      'from src/lib/pariprashna/lexicon.ts.',
    capability.uri
  )
  return FALLBACK_READER_LABEL
}

/** Default `onUnmapped` handler: a CI-visible console warning, tagged for grep-ability. */
function defaultUnmappedWarning(message: string, _uri: string): void {
  // eslint-disable-next-line no-console
  console.warn(`[pariprashna/lexicon] ${message}`)
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. Leak-proofing guard — defense in depth, independent of the closed-set check
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Regex patterns that must NEVER match any string in the closed lexicon, any
 * rendered label, or any capability's declared `register.reader_label`. This
 * is a second, independent line of defense (beyond "is it in the closed set")
 * that directly encodes the leak categories the brief names: asset ids,
 * table names, layer names.
 */
export const INTERNAL_LEAK_PATTERNS: readonly RegExp[] = [
  /\b(?:ga|bo|ka|ph|mi|bg)_[a-z][a-z0-9_]*\b/i, // asset ids: ga_*, bo_*, ka_*, ph_*, mi_*, bg_*
  /\bL[0-5]\b/, // layer names: L0..L5
  /\bmarsys:\/\//i, // capability URIs
  /\b(?:chart_facts|chart_dashas|chart_divisionals|bodha_\w*|kala_\w*|phala_\w*|mimamsa_\w*)\b/i, // table names
  /\b(?:get|query|compute)_[a-z][a-z0-9_]*\b/i, // tool-name-shaped identifiers (prefix form: get_dashas)
  /\b[a-z][a-z0-9_]*_(?:get|query|compute)\b/i, // tool-name-shaped identifiers (suffix form: ganita_yogas_get)
] as const

/**
 * True if `label` is free of every internal-leak pattern above. Tests use this
 * against the full CLOSED_LEXICON_STRINGS set (must always be true) and
 * against real registry `register.reader_label` values (must always be true).
 */
export function isLeakFree(label: string): boolean {
  return !INTERNAL_LEAK_PATTERNS.some((pattern) => pattern.test(label))
}
