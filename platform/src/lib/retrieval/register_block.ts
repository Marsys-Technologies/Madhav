/**
 * register_block.ts — THE ENVELOPE REGISTER + READING-CONTRACT + SIGNAL-READER-TEXT
 * (Retrieval Plane Elevation W3 "One Envelope", Lane W3-L3; C-3 in the master brief §E)
 * =====================================================================================
 * Design source: RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §"R-2 — One Envelope" item 3:
 *   "register block rides in the envelope, every internal token — fact_ids, drill URIs,
 *    flag codes, epistemic grades — gets a plain-language label adjacent to it; a compact
 *    reading_contract header block, one generated paragraph telling the consuming model how
 *    to read grades/coverage/flags."
 * and master brief §E "W3" item 3: "register block + reading_contract + signal_reader_text
 * editorial pass (C-3; generate draft reader text per signal class, flag for native polish
 * post-campaign)".
 *
 * WHY THIS EXISTS (plan §1.2 finding "No `register` block exists (A-18 unbuilt)"): a v3
 * envelope is dense with internal tokens a foreign consuming LLM cannot decode from the wire
 * alone — MSR signal-class codes (`composite_state`, `karaka_alignment`, …), `SIG.MSR.NNN`
 * signal ids, `marsys://` drill URIs, judgment-flag codes (`karaka_unresolved: …`), and the
 * closed epistemic-grade vocabulary (`single_pass_signal`, `ganita_fact`, …). The register
 * block puts a plain-language label ADJACENT to every such token that actually appears in the
 * response, so "the careless reader still gets the label" (handoff §7.2's loud-failure goal).
 *
 * §N.6 (Serving Density Principle) COMPLIANCE: the reading_contract is GENERATED from the
 * response's actual content shape — a sparse/floored response and a fully-grounded response
 * produce visibly different paragraphs (see buildReadingContract). It never lets a catalog-only
 * row read as a confirmed finding (it emits the explicit `catalog_only_rows_present` caution
 * when such rows are detected) and never substitutes a hollow envelope for an honest empty gap
 * (it names the epistemic grade + the judgment_flags honestly, including `floored_null`).
 *
 * ADDITIVE-ONLY: everything here is consumed via NEW optional envelope fields
 * (`register` / `reading_contract` / `signal_reader_text` on V3Envelope). No legacy field
 * changes; a consumer that ignores these fields is byte-unaffected on the fields it reads.
 */

import type { EpistemicGrade, DrillPointerType, PactStage } from './envelope'

// ── Token-kind taxonomy (the generic register-entry shape) ─────────────────────

/**
 * The kind of internal token a register entry labels. Deliberately a GENERIC open-ish
 * union (per the W3-L2 coordination note in the lane brief): a parallel lane is landing a
 * closed judgment-flag-code enum, and the register block must be ABLE to label ANY of their
 * codes without hardcoding them — so `flag` is a generic kind and flag labels can be injected
 * at build time (see `flag_labels` on BuildRegisterBlockParams). The kinds:
 *   - `signal_class`   — an MSR `signal_type_class` code (composite_state, yoga, dosha, …)
 *   - `signal_ref`     — a `SIG.MSR.NNN` signal-id reference token
 *   - `epistemic_grade`— one of the 7 closed epistemic-grade tokens
 *   - `drill_uri`      — a `marsys://…` capability/drill URI (labelled by its family segment)
 *   - `flag`           — a judgment-flag code (generic; label injectable by W3-L2's enum)
 *   - `pact_stage`     — a PACT-chain stage marker on a drill pointer
 *   - `pointer_type`   — a typed drill-pointer classical-move code
 */
export type RegisterTokenKind =
  | 'signal_class'
  | 'signal_ref'
  | 'epistemic_grade'
  | 'drill_uri'
  | 'flag'
  | 'pact_stage'
  | 'pointer_type'

/**
 * One register entry: an internal token, its plain-language label, and the token kind.
 * `token` is the exact literal as it appears in the envelope content (so a consumer can
 * string-match it); `label` is a short human/LLM-readable gloss; `kind` classifies it.
 */
export interface RegisterEntry {
  token: string
  label: string
  kind: RegisterTokenKind
}

// ── Canonical label maps (the plain-language glossary source) ──────────────────

/**
 * MSR signal-class labels — enumerated from the LIVE `bodha_msr_signals.signal_type_class`
 * column (19 distinct classes as of 2026-07-20; the migration-325 schema comment is stale).
 * Each label is a compact gloss of what the class MEANS to a reading model. The longer
 * reader-facing paragraphs live in SIGNAL_READER_TEXT below.
 */
export const SIGNAL_CLASS_LABELS: Record<string, string> = {
  composite_state:
    'Composite planetary-state signal (dignity + house + aspect + strength rolled into one graded factor).',
  karaka_alignment: 'Significator (karaka) alignment — how a matter’s natural significator is placed and supported.',
  sade_sati: 'Sade Sati / Saturn-transit-over-Moon phase signal.',
  varga_pattern: 'Divisional-chart (varga) pattern — promise seen in the operative sub-chart (D9, D10, …).',
  panchanga: 'Panchanga (five-limb calendar) signal — tithi / vara / nakshatra / yoga / karana of the birth moment.',
  tradition_specific: 'Tradition-specific rule signal (a reading confined to a named classical school/system).',
  annual: 'Annual (varshaphala / Tajaka) signal keyed to a solar-return year.',
  parivartana: 'Parivartana (mutual sign-exchange) between two grahas’ dispositors.',
  configuration: 'Multi-graha configuration / geometry signal (a named placement pattern).',
  yoga: 'Yoga signal — a named benefic/combinatorial planetary combination.',
  dosha: 'Dosha signal — a named affliction/blemish planetary combination.',
  bhavat_bhavam_amplifier: 'Bhavat-bhavam amplifier — a house judged from itself (Nth-from-Nth) reinforcing a matter.',
  nakshatra_semantic: 'Nakshatra-semantic signal — meaning drawn from the lunar-mansion symbolism.',
  sudarshana_agreement: 'Sudarshana agreement — concurrence of the Lagna, Chandra and Surya vantage charts.',
  varga_ratification_divergence:
    'Varga ratification/divergence — whether the divisional chart confirms or contradicts the rasi promise.',
  arudha: 'Arudha (perceived-image) signal — the projected/manifest reflection of a house.',
  special_lagna: 'Special-lagna signal (Arudha Lagna, Hora Lagna, Ghati Lagna, Bhava Lagna, …).',
  dhana_axis: 'Dhana-axis signal — the wealth-house (2nd/11th and lords) configuration.',
  vargottama_amplification: 'Vargottama amplification — a graha in the same sign in rasi and navamsa, strengthening it.',
}

/**
 * DRAFT reader text, one short paragraph per MSR signal class, telling a reading model what
 * that class MEANS and how much epistemic weight to give it. Enumerated 1:1 with the live
 * `bodha_msr_signals.signal_type_class` values (19 classes).
 *
 * ⚠️ NATIVE-POLISH-PENDING (master brief §E "W3" item 3, verbatim: "generate draft reader
 * text per signal class, flag for native polish post-campaign"). This is GENERATED DRAFT
 * prose — a scaffold that makes the field structurally complete and non-empty — NOT a claim
 * of final acharya-grade wording (CLAUDE.md §J). The native editorial pass replaces this map
 * in a later wave; the taxonomy/coverage is what this lane commits to, the exact wording is not.
 */
export const SIGNAL_READER_TEXT: Record<string, string> = {
  composite_state:
    'DRAFT (native-polish-pending). A composite-state signal fuses a graha’s dignity, house placement, aspects and computed strength into a single graded factor. Read it as the workhorse layer of the chart: most rows are of this class. Weigh it by its epistemic grade and verification status, not by its raw count — a large composite-state population is breadth, not confirmation.',
  karaka_alignment:
    'DRAFT (native-polish-pending). A karaka-alignment signal reports how the natural significator of a matter (e.g. Jupiter for children, Venus for spouse) is itself placed and supported. Treat it as a second, significator-frame reading that must AGREE with the house-frame reading before a promise is called confirmed.',
  sade_sati:
    'DRAFT (native-polish-pending). A sade-sati signal marks the ~7.5-year Saturn transit over the Moon and its flanking signs. Read it as a timing/pressure phase, not a fixed birth promise — its bearing is on WHEN a matter is stressed, not WHETHER it is promised.',
  varga_pattern:
    'DRAFT (native-polish-pending). A varga-pattern signal reads the promise in an operative divisional chart (D9 for marriage/dharma, D10 for career, …). Treat it as the ratification layer: a rasi promise the relevant varga does not echo is weaker than its rasi row alone suggests.',
  panchanga:
    'DRAFT (native-polish-pending). A panchanga signal draws on the five calendrical limbs of the birth moment (tithi, vara, nakshatra, yoga, karana). Read it as constitutional temperament grounding rather than an event predictor.',
  tradition_specific:
    'DRAFT (native-polish-pending). A tradition-specific signal is confined to a named classical school or system and may not generalise. Read it as school-scoped: cite the tradition, and do not silently merge it with mainstream Parashari findings.',
  annual:
    'DRAFT (native-polish-pending). An annual signal is keyed to a solar-return (varshaphala / Tajaka) year. Read it as a one-year overlay on the natal promise — it modulates timing within a year, it does not restate the lifetime promise.',
  parivartana:
    'DRAFT (native-polish-pending). A parivartana signal reports a mutual sign-exchange between two grahas’ dispositors, linking their houses. Read it as a structural bridge: the two houses’ fortunes become coupled, for better or worse depending on the exchange type.',
  configuration:
    'DRAFT (native-polish-pending). A configuration signal names a multi-graha geometry or placement pattern. Read it as a structural feature of the chart to be corroborated by dignity/strength before it carries predictive weight.',
  yoga:
    'DRAFT (native-polish-pending). A yoga signal names a benefic/combinatorial planetary combination. IMPORTANT: an MSR yoga-class row is a catalog-level match — confirm it against the firings-authoritative surface (ganita_yoga_firings) before reading it as an active, cross-verified yoga rather than a mere pattern present.',
  dosha:
    'DRAFT (native-polish-pending). A dosha signal names an affliction/blemish combination. As with yoga, an MSR dosha row is catalog-level: check for cancellation (bhanga) and confirm firing before reading it as an operative affliction.',
  bhavat_bhavam_amplifier:
    'DRAFT (native-polish-pending). A bhavat-bhavam-amplifier signal judges a house from itself (the Nth house from the Nth), reinforcing a matter when both vantages agree. Read it as an amplifier, not an independent promise.',
  nakshatra_semantic:
    'DRAFT (native-polish-pending). A nakshatra-semantic signal draws meaning from lunar-mansion symbolism (deity, gana, symbol). Read it as qualitative colouring of a placement, not a quantitative strength term.',
  sudarshana_agreement:
    'DRAFT (native-polish-pending). A sudarshana-agreement signal reports concurrence across the Lagna, Chandra and Surya vantage charts. Read HIGH agreement as a robustness/confidence multiplier and disagreement as a flag to re-judge from the dissenting frame.',
  varga_ratification_divergence:
    'DRAFT (native-polish-pending). A varga-ratification/divergence signal states whether the divisional chart confirms or contradicts the rasi promise. Read a DIVERGENCE as a demotion of confidence and a pointer to re-check the matter in the varga.',
  arudha:
    'DRAFT (native-polish-pending). An arudha signal reports the projected/perceived image of a house (how a matter APPEARS to the world), distinct from its literal placement. Read it as the perception layer, kept separate from material reality.',
  special_lagna:
    'DRAFT (native-polish-pending). A special-lagna signal reads a matter from a non-standard ascendant (Arudha, Hora, Ghati, Bhava Lagna, …). Read it as an additional vantage, corroborating or qualifying the rasi-Lagna reading.',
  dhana_axis:
    'DRAFT (native-polish-pending). A dhana-axis signal reports the wealth-house configuration (2nd/11th houses and their lords). Read it as the material-resource layer, to be timed against the operative dasha before any wealth-timing claim.',
  vargottama_amplification:
    'DRAFT (native-polish-pending). A vargottama-amplification signal marks a graha occupying the same sign in the rasi and the navamsa, strengthening its significations. Read it as a strength amplifier on whatever that graha already promises.',
}

/** The closed epistemic-grade vocabulary (mirrors envelope.ts EpistemicGrade), plain-labelled. */
export const EPISTEMIC_GRADE_LABELS: Record<EpistemicGrade, string> = {
  ganita_fact: 'Deterministic L1 chart fact — computed, not interpreted; treat as ground truth.',
  verified_signal: 'Cross-verified signal (≥50% of rows two-pass verified) — a confirmed reading.',
  single_pass_signal: 'Single-pass signal (<50% verified) — a candidate reading awaiting cross-verification; not confirmed.',
  classical_contested: 'Classically contested — sources disagree; present both sides, do not resolve silently.',
  calibrated_posterior: 'Calibrated posterior — an empirically calibrated probability from accrued outcome data.',
  structural_prior: 'Structural prior — a structural (uncalibrated) estimate; no outcome data yet backs the number.',
  floored_null: 'Floored null — no supporting data; the honest empty result, NOT a negative finding.',
}

/** PACT-chain stage labels (mirrors envelope.ts PactStage). */
export const PACT_STAGE_LABELS: Record<PactStage, string> = {
  promise: 'PACT stage 1 — PROMISE: the checklist verdict that a matter is natally promised.',
  confirmation: 'PACT stage 2 — CONFIRMATION: the operative-varga check ratifying the promise.',
  activation: 'PACT stage 3 — ACTIVATION: which dasha period carries/activates the promise.',
  trigger: 'PACT stage 4 — TRIGGER: the transit gate that fires an activated promise in-window.',
}

/** Typed drill-pointer classical-move labels (mirrors envelope.ts DrillPointerType). */
export const POINTER_TYPE_LABELS: Record<DrillPointerType, string> = {
  confirm_in_varga: 'Next step: confirm the promise in the operative divisional chart.',
  check_from_moon: 'Next step: re-judge the same matter from the Chandra (Moon) frame (Sudarshana).',
  check_bhanga: 'Next step: check for a cancellation / near-miss (bhanga) on a bearing yoga or dosha.',
  opposing_yoga: 'Next step: a yoga/dosha of OPPOSITE valence also bears on this matter — weigh it.',
  karaka_condition: 'Next step: examine the significator (karaka) graha’s own condition directly.',
  dasha_of_promise: 'Next step: locate which dasha period carries/activates the promise.',
  transit_gate: 'Next step: check current/upcoming transits gating an already-activated promise.',
  dispositor_chain: 'Next step: follow the lord-of-the-lord (dispositor) indirection one level deeper.',
  tail_dissent: 'Next step: the mandatory dissent / tail-check step of the investigation protocol.',
  other: 'Next step outside the closed classical-move vocabulary (see the pointer hint).',
}

/**
 * `marsys://` drill-URI FAMILY labels. A drill URI is `marsys://<primitive>/<segment>/<name>`;
 * we label by the `<primitive>/<segment>` family (layer or role) rather than enumerating every
 * leaf, so any URI in the estate resolves to a family label. Keyed by the family prefix.
 */
export const DRILL_URI_FAMILY_LABELS: Record<string, string> = {
  'tool/L0': 'L0 Brahmagyan tool — classical-text / reference retrieval.',
  'tool/L1': 'L1 Ganita tool — deterministic chart-fact lookup.',
  'tool/L2': 'L2 Bodha tool — interpreted signal / synthesis surface.',
  'tool/L3': 'L3 Kala tool — time-keyed (dasha / transit / muhurta) surface.',
  'tool/L4': 'L4 Phala tool — predictive outlook / anchor surface.',
  'tool/L5': 'L5 Mimamsa tool — calibration / trust-metadata surface.',
  'tool/L-DOMAIN': 'Life-domain assessment umbrella (career / health / marriage / wealth).',
  'tool/L-JUDGMENT': 'Judgment-query surface — checklist verdict with grounding.',
  'tool/L-PACT': 'PACT-chain query surface — promise → confirmation → activation → trigger.',
  'tool/L-TIMING': 'Timing surface — yoga activation by dasha.',
  'tool/synergy': 'Cross-layer synergy synthesizer.',
  'tool/channel': 'Channel / routing surface.',
  'tool/synthesis': 'Cross-layer synthesis surface.',
  'tool/maro': 'MARO adapter/profile surface.',
  'tool/router': 'Router surface.',
  'resource/asset-registry': 'Asset-registry resource — build-catalog metadata.',
  'resource/ephemeris-cache': 'Ephemeris-cache resource — precomputed positions.',
  'resource/sutravali': 'Sutravali resource — classical-rule corpus.',
  'resource/catalog': 'Capability-catalog resource.',
  'prompt/intent-classify': 'Intent-classification prompt.',
}

// ── Token detection ────────────────────────────────────────────────────────────

const SIG_MSR_RE = /SIG\.MSR\.[0-9]+/g
const MARSYS_URI_RE = /marsys:\/\/[A-Za-z0-9/_-]+/g

/** Extract the `<primitive>/<segment>` family key from a marsys:// URI, or null. */
export function drillUriFamily(uri: string): string | null {
  const m = uri.match(/^marsys:\/\/([A-Za-z0-9-]+)\/([A-Za-z0-9-]+)/)
  if (!m) return null
  return `${m[1]}/${m[2]}`
}

// ── Register-block builder ─────────────────────────────────────────────────────

export interface BuildRegisterBlockParams {
  /** The assembled v3 content (any shape); deep-scanned for signal-class + SIG.MSR + marsys tokens. */
  content?: unknown
  /** The response's epistemic grade (labelled if present). */
  epistemicGrade?: EpistemicGrade | null
  /** judgment_flags array; each entry’s code (prefix before ':') is labelled as a `flag`. */
  judgmentFlags?: string[]
  /** drill_pointers; their pointer_type / pact_stage / instrument URIs are labelled. */
  drillPointers?: Array<{ instrument?: string; pointer_type?: string; pact_stage?: string }>
  /**
   * Injected flag-code labels (W3-L2 coordination): a map from a flag code to its plain-language
   * label. Any judgment-flag code present in the response that also appears here is labelled from
   * this map; codes not here still get a generic labelled entry (so no token is left unlabelled).
   */
  flag_labels?: Record<string, string>
  /** Extra caller-supplied entries appended verbatim (escape hatch; e.g. bespoke tokens). */
  register_extra?: RegisterEntry[]
}

/**
 * Build the register block: scan the response for internal tokens that ACTUALLY APPEAR and
 * emit one labelled entry per distinct token. Response-scoped by construction — it never
 * dumps the whole glossary, only the tokens this response uses (plan §R-2: "adjacent to it").
 */
export function buildRegisterBlock(params: BuildRegisterBlockParams): RegisterEntry[] {
  const entries = new Map<string, RegisterEntry>() // keyed by `${kind}:${token}` for dedupe
  const add = (token: string, label: string, kind: RegisterTokenKind) => {
    const key = `${kind}:${token}`
    if (!entries.has(key)) entries.set(key, { token, label, kind })
  }

  const json = params.content === undefined ? '' : safeStringify(params.content)

  // signal-class tokens: any known class code appearing anywhere in the content.
  for (const [cls, label] of Object.entries(SIGNAL_CLASS_LABELS)) {
    // match as a whole-word token to avoid substring false positives.
    const re = new RegExp(`(?<![A-Za-z0-9_])${cls}(?![A-Za-z0-9_])`)
    if (re.test(json)) add(cls, label, 'signal_class')
  }

  // SIG.MSR.NNN signal-id references.
  for (const m of json.matchAll(SIG_MSR_RE)) {
    add(m[0], `MSR signal reference ${m[0]} — resolve via bodha_signals_get for its constituent L1 facts.`, 'signal_ref')
  }

  // marsys:// drill URIs (from content AND from drill_pointer instruments).
  const uriSources = [json, ...(params.drillPointers ?? []).map(p => p.instrument ?? '')]
  for (const src of uriSources) {
    for (const m of src.matchAll(MARSYS_URI_RE)) {
      const fam = drillUriFamily(m[0])
      const label = (fam && DRILL_URI_FAMILY_LABELS[fam]) || 'Internal drill URI — a capability to call for the next step.'
      add(m[0], label, 'drill_uri')
    }
  }

  // epistemic grade.
  if (params.epistemicGrade) {
    add(params.epistemicGrade, EPISTEMIC_GRADE_LABELS[params.epistemicGrade], 'epistemic_grade')
  }

  // judgment-flag codes.
  for (const raw of params.judgmentFlags ?? []) {
    const code = flagCode(raw)
    if (!code) continue
    const injected = params.flag_labels?.[code]
    add(code, injected ?? `Judgment flag — an honest coverage/resolution disclosure (${code}); see the flag text for detail.`, 'flag')
  }

  // pointer_type + pact_stage on drill pointers.
  for (const p of params.drillPointers ?? []) {
    if (p.pointer_type && p.pointer_type in POINTER_TYPE_LABELS) {
      add(p.pointer_type, POINTER_TYPE_LABELS[p.pointer_type as DrillPointerType], 'pointer_type')
    }
    if (p.pact_stage && p.pact_stage in PACT_STAGE_LABELS) {
      add(p.pact_stage, PACT_STAGE_LABELS[p.pact_stage as PactStage], 'pact_stage')
    }
  }

  const out = Array.from(entries.values())
  if (params.register_extra) out.push(...params.register_extra)
  return out
}

/** The flag CODE is the token before the first ':' (e.g. `karaka_unresolved: Jupiter` → `karaka_unresolved`). */
function flagCode(raw: string): string | null {
  if (!raw) return null
  const idx = raw.indexOf(':')
  return (idx >= 0 ? raw.slice(0, idx) : raw).trim() || null
}

/** JSON.stringify that never throws on cycles (best-effort token scan). */
function safeStringify(v: unknown): string {
  const seen = new WeakSet()
  try {
    return JSON.stringify(v, (_k, val) => {
      if (typeof val === 'object' && val !== null) {
        if (seen.has(val as object)) return undefined
        seen.add(val as object)
      }
      return val
    }) ?? ''
  } catch {
    return String(v)
  }
}

// ── reading_contract generator ─────────────────────────────────────────────────

export interface BuildReadingContractParams {
  epistemicGrade?: EpistemicGrade | null
  /** 0..1 fraction of two-pass-verified rows in this response, if computed. */
  verifiedFraction?: number | null
  /** grounding fact_ids present in this response (used to say whether the verdict is grounded). */
  groundingFactCount?: number
  /** coverage: served vs total for the family this response slices (drives the completeness sentence). */
  coverage?: { served: number; total: number | null } | null
  /** more rows exist beyond this page (pagination.more_available). */
  moreAvailable?: boolean
  /** judgment_flags present (drives the honest-gap sentence). */
  judgmentFlags?: string[]
  /** TRUE if the response contains catalog-only rows (e.g. requires_pass / catalog_only markers). */
  hasCatalogOnlyRows?: boolean
  /** whether the response carries a density_contract declaration on its capability. */
  hasDensityContract?: boolean
  /** distinct register-entry kinds present (drives the "how to read tokens" sentence). */
  registerKinds?: RegisterTokenKind[]
}

/**
 * Generate the reading_contract: a SINGLE paragraph telling the consuming LLM how to read
 * THIS response's grades/coverage/flags/register. GENERATED from the response's content shape
 * — a fully-grounded confirmed response and a sparse/floored one produce visibly different
 * paragraphs (§N.6: density signaling is data, not narration; the contract must not be static
 * boilerplate). Never lets a catalog-only row read as confirmed; never papers over an empty gap.
 */
export function buildReadingContract(params: BuildReadingContractParams): string {
  const s: string[] = []

  // 1. Grade sentence — how to weight this response's central finding.
  const grade = params.epistemicGrade ?? null
  if (grade) {
    s.push(`This response is graded ${grade}: ${EPISTEMIC_GRADE_LABELS[grade]}`)
  } else {
    s.push('This response carries no computed epistemic grade; treat its content as unweighted context, not a confirmed finding.')
  }

  // 2. Grounding sentence — is the verdict backed by resolvable L1 facts?
  if (grade === 'floored_null') {
    s.push('It is an HONEST EMPTY result — no supporting data was found; do not read the absence as a negative finding, and do not manufacture a reading from it.')
  } else if ((params.groundingFactCount ?? 0) > 0) {
    s.push(`Its reading is grounded in ${params.groundingFactCount} resolvable L1 fact reference(s) — you may follow each fact_id down to its deterministic source.`)
  } else {
    s.push('Its reading is NOT yet anchored to resolvable L1 fact references in this envelope; drill via the pointers before treating it as confirmed.')
  }

  // 3. Verification sentence — only when a fraction was computed.
  if (params.verifiedFraction != null) {
    const pct = Math.round(params.verifiedFraction * 100)
    s.push(
      pct >= 50
        ? `${pct}% of the rows here are cross-verified (two-pass) — the majority layer is confirmed.`
        : `Only ${pct}% of the rows here are cross-verified — most are single-pass candidates, not confirmations.`,
    )
  }

  // 4. Catalog-only caution — §N.6 Part 1: never let a label match read as a confirmed finding.
  if (params.hasCatalogOnlyRows) {
    s.push('Some rows are CATALOG-ONLY (single-pass label matches awaiting cross-verification): they are counted and served but are NOT confirmed findings — confirm them against the firings-authoritative surface before relying on them.')
  }

  // 5. Coverage/completeness sentence.
  if (params.coverage) {
    const { served, total } = params.coverage
    if (total == null) {
      s.push(`This is a bounded slice of ${served} served row(s); the full family size is not computable here, so do not read the served count as the total.`)
    } else if (served < total) {
      s.push(`This is ${served} of ${total} rows in the family — a partial slice; more remain.`)
    } else {
      s.push(`This is the complete family (${served} of ${total} rows) — nothing is withheld.`)
    }
  } else if (params.moreAvailable) {
    s.push('More rows exist beyond this page — page via the cursor before drawing a whole-family conclusion.')
  }

  // 6. Flags sentence — honest-gap disclosures.
  const flags = params.judgmentFlags ?? []
  if (flags.length > 0) {
    s.push(`It carries ${flags.length} judgment flag(s) disclosing coverage/resolution gaps (see judgment_flags) — read each as a stated limit on the verdict, not decoration.`)
  }

  // 7. Register sentence — how to decode the tokens.
  const kinds = params.registerKinds ?? []
  if (kinds.length > 0) {
    s.push(`Internal tokens in this envelope (${kinds.join(', ')}) each have a plain-language label in the \`register\` block — read the label adjacent to any token you do not recognise rather than guessing.`)
  }

  // 8. Density sentence — only when a density contract is declared.
  if (params.hasDensityContract) {
    s.push('This capability declares a density contract: rows are layered by confidence, and the densest/confirmed layer is protected from truncation first — do not flatten the layers into one undifferentiated list.')
  }

  return s.join(' ')
}

// ── signal_reader_text selector ────────────────────────────────────────────────

/**
 * Collect the draft reader text for the signal classes PRESENT in this response (from the
 * register block's signal_class entries). Response-scoped: only the classes actually served
 * get their paragraph attached. Pass `all: true` to get the full 19-class map (used by the
 * coverage test / a docs projection).
 */
export function collectSignalReaderText(
  signalClassTokens: string[],
  opts?: { all?: boolean },
): Record<string, string> {
  if (opts?.all) return { ...SIGNAL_READER_TEXT }
  const out: Record<string, string> = {}
  for (const cls of signalClassTokens) {
    if (SIGNAL_READER_TEXT[cls]) out[cls] = SIGNAL_READER_TEXT[cls]
  }
  return out
}

/** The count of enumerated signal classes (for reporting / test assertions). */
export const SIGNAL_CLASS_COUNT = Object.keys(SIGNAL_READER_TEXT).length
