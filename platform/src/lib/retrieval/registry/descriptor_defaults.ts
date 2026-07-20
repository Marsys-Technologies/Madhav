/**
 * R-1.1 Descriptor Migration — Backfill Defaults
 * =================================================
 * Retrieval Plane Elevation W2 "One Catalog", plan R-1 item 1.
 *
 * W1 Lane L1a landed nine new OPTIONAL `CapabilityDescriptor` fields
 * (types.ts D1_AMENDMENTS amendment_version 2) as TYPE-ONLY — zero of the
 * ~118 live capabilities had them populated. This module is the MECHANICAL
 * defaulting layer that fills them in, generator-derived, not hand-curated
 * per capability (the estate is too large — ~118 objects across ~20 files —
 * for that to be honest work in one wave).
 *
 * ARCHITECTURE NOTE (read before touching this file): the ~118 capability
 * descriptors are inline object literals scattered across ~20
 * `registry/layers/**` files, constructed once at module-import time and
 * handed to `registerCapability()`. There is no single static manifest to
 * rewrite. Hand-editing every literal to add five-plus boilerplate fields
 * would be (a) enormous mechanical diff noise across files this wave does
 * not otherwise touch, (b) exactly the kind of edit that corrupted ~40 lines
 * of types.ts in W1 Lane L1a via one stray block-comment-closing token, and (c) not
 * meaningfully more "real" than a defaulting pass, since the values
 * themselves are generator-derived defaults either way.
 *
 * Instead, `applyDescriptorDefaults()` mutates the ACTUAL descriptor object
 * held by the registry `Map` (`_registry` in `index.ts`) — the very same
 * object instance every layer file constructed and passed to
 * `registerCapability()`. `catalog.ts`'s `getCatalog()` (the one production
 * consumption surface both the MCP and chat channels import, per its own
 * header doc) calls this on every capability before returning the array.
 * The population is therefore REAL and IN PLACE at the point every
 * consumer reads it — not a report generated on the side — while leaving
 * every existing field (and every already-set value) untouched: a field is
 * only ever set if it was `undefined` going in, so this is safe to call
 * repeatedly (idempotent) and safe to run before or after any individual
 * layer file adds its own explicit values in a future wave.
 *
 * `platform/scripts/manifest/backfill_descriptor_fields.ts` is the CLI
 * entry point that loads the live registry (which now runs this pass via
 * `getCatalog()`) and prints a coverage report — it does not duplicate this
 * derivation logic.
 *
 * SCOPE (bulk pass, this wave):
 *   - annotations, mutation, data_source — populated on all 118 (the three
 *     fields the CI test in `descriptor_defaults.test.ts` treats as
 *     universal).
 *   - projection_tags, display — populated on the overwhelming majority;
 *     narrower/deliberate exceptions documented inline (INTERNAL_INTROSPECTION_URIS).
 *   - calibration_context_only, demand_ranking — populated ONLY where real
 *     code evidence supports it (narrow, single-digit sets below); left
 *     `undefined` everywhere else, per F-R7's "narrow... do not over-apply"
 *     instruction and the plan §8 R-2 demand_ranking framing.
 *   - register.glossary, family_overrides — deliberately NOT populated this
 *     pass. Both require genuine per-capability editorial judgment (writing
 *     a token glossary; deciding a real per-family prompt override) that a
 *     mechanical generator cannot honestly produce without fabricating
 *     content. Left for a future, explicitly-scoped editorial wave.
 *
 * W3 "ONE ENVELOPE" ADDITION (2026-07-20, RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §7
 * item 6 / master brief §E W3): `density_contract` (types.ts, added W1 Lane L1a as a
 * §N.6-serving-density field, ~5% populated at W3 open — the 6 capabilities that hand-
 * set it: get_vichara, get_yoga_dosha, get_dasha_lord_capability, get_yoga_firings,
 * query_signals, judgment_query) is defaulted here the same way as the nine fields
 * above: `deriveDensityContract()` below, evidence tables `MEASURED_BUDGET_KB_URIS` /
 * `TOOL_ROLE_DIGEST_BYTES` / `STRUCTURAL_PARAM_NAMES` / `PAGINATION_PARAM_NAMES`. This
 * brings live coverage from 6/~118 to 100% of `getCatalog()`'s output — see
 * `descriptor_defaults.test.ts`'s `density_contract` block for the CI gate.
 */

import type { CapabilityDescriptor, CapabilityUri } from './types'

// ── Classification tables (real code evidence, not guesses) ──────────────────
//
// Every entry below was verified against this worktree's source on
// 2026-07-20 by grepping for `PYTHON_SIDECAR_URL`/`sidecarUrl`/`await fetch(`
// inside `src/lib/retrieval/registry/layers/**` (case-insensitive, whole
// tree) and reading the surrounding handler code. Zero direct SQL writes
// (`INSERT INTO`/`UPDATE ... SET`/`DELETE FROM`) were found anywhere in the
// registry layer tree — hence MUTATION_URIS is empty; see the honesty note
// in the campaign report for what this does and does not prove.

/**
 * Capabilities whose handler makes a live HTTP call to the Python sidecar
 * (`PYTHON_SIDECAR_URL`) as its primary or sole data path. Evidence:
 * `SIDECAR_URL = process.env['PYTHON_SIDECAR_URL'] ...` (or the D7 sutravali
 * block's `sidecarUrl` local) defined and `fetch()`-called in the capability's
 * own registration file.
 */
const SIDECAR_BACKED_URIS: ReadonlySet<CapabilityUri> = new Set([
  // L0_brahmagyan/*.ts — direct SIDECAR_URL + fetch, own file
  'marsys://tool/L0/query_planet_position',
  'marsys://tool/L0/query_planet_transit',
  'marsys://tool/L0/query_aspects_at_time',
  'marsys://tool/L0/query_retrograde_periods',
  'marsys://resource/ephemeris-cache/year/{yyyy}',       // ephemeris_cache_year
  'marsys://resource/ephemeris-cache/native-lifetime',    // ephemeris_cache_native_lifetime
  // register_d7_channel.ts — sutravali block, sidecarUrl + fetch (lines ~356-593)
  'marsys://tool/L0/query_sutravali_rules',
  'marsys://tool/L0/query_sutravali_rules_for_planet',
  'marsys://tool/L0/read_sutravali_rule',
  'marsys://tool/L0/list_sutravali_rules_by_text',
  // L1_ganita/get_av_transit_gating.ts — own SIDECAR_URL + fetch
  'marsys://tool/L1/get_av_transit_gating',
  // L3_kala/call_service_wrappers.ts — five compute-service wrappers, own
  // header: "These are compute services, not tables"
  'marsys://tool/L3/call_transit_search',
  'marsys://tool/L3/call_ephemeris_at_t',
  'marsys://tool/L3/call_dasha_eligibility',
  'marsys://tool/L3/call_muhurta_score',
  'marsys://tool/L3/call_priority_ranking',
  // L4_phala/query_muhurat.ts — own SIDECAR_URL + fetch
  'marsys://tool/L4/query_muhurat',
])

/**
 * Capabilities that mix a stored (DB) read with a live sidecar call inside
 * the SAME handler. Evidence: `pact_query` (register_d10_pact.ts) resolves
 * its PROMISE/CONFIRMATION/ACTIVATION stages from `chart_facts`/`ga_*` DB
 * reads, then the TRIGGER stage additionally does a live
 * `fetch(`${SIDECAR_URL}/brahmagyan/ephemeris/planet_transit...`)` call.
 */
const HYBRID_URIS: ReadonlySet<CapabilityUri> = new Set([
  'marsys://tool/L-PACT/pact_query',
])

/**
 * Internal channel-introspection tools — explicitly documented in their own
 * descriptor prose as "Not LLM-facing for end-user queries — internal
 * channel introspection only." Their handler returns a hardcoded/static
 * wiring map (no DB read, no sidecar call) computed fresh at call time from
 * source, not from a stored table — closer to `computed` than `stored`
 * under the data_source enum's own framing ("no build_id... computed_at
 * provenance"), but this is a genuine judgment call flagged in the wave
 * report, not a confident classification. They are also excluded from
 * `projection_tags` entirely (left `undefined`) — they are not meant to be
 * surfaced via any of chat/mcp_full/mcp_compact/mcp_consult.
 */
const INTERNAL_INTROSPECTION_URIS: ReadonlySet<CapabilityUri> = new Set([
  'marsys://tool/channel/mcp_wiring',
  'marsys://tool/channel/chat_dispatch',
])

/**
 * A-04 mutation class: capabilities whose handler performs a write (DB
 * INSERT/UPDATE/DELETE, or dispatches to a write-capable side effect).
 * MECHANICAL FINDING (2026-07-20): empty. A repo-wide
 * `grep -rliE "INSERT INTO|UPDATE [a-z_]+ SET|DELETE FROM"` over
 * `src/lib/retrieval/registry/layers/**` and `src/lib/retrieval/synthesis/**`
 * returned zero hits. The genuine write-capable surface in this codebase
 * (`log_prediction`, `record_outcome`, `flag_disagreement`,
 * `lel_event_record`, `prospective_ledger_file`, `prospective_ledger_list`)
 * lives entirely in `/api/mcp/writes/[action]/route.ts` — a hand-rolled
 * dispatcher with NO `CapabilityDescriptor` and NO `registerCapability()`
 * call, i.e. it is not one of the 118 `getCatalog()` capabilities this
 * migration touches. `canonical_faces.json`'s `record_outcome` →
 * `mimamsa_outcome_record` mapping is a platform-mcp-side tool-name alias
 * to that same out-of-registry write route, not a registry capability.
 * See the wave report for the honest implication: this migration cannot
 * assert "mutation: false" is permanently correct if/when that write
 * surface is folded into the registry (a later wave's job, per A-04's own
 * "sidecar-served tools are pulled into the registry" framing).
 */
const MUTATION_URIS: ReadonlySet<CapabilityUri> = new Set([])

/**
 * F-R7 `calibration_context_only`: outcome/LEL-read tools whose role is
 * calibration-context SUPPLY (raw ledger reads feeding the calibration
 * loop), not the calibration-quality SURFACE itself. `query_calibration`
 * (the mi_pramana scorecard — prediction-event match verdicts, reliability)
 * is deliberately NOT included: its role is to SERVE calibration results,
 * not supply raw context, and it is meant to stay planner-selectable.
 */
const CALIBRATION_CONTEXT_ONLY_URIS: ReadonlySet<CapabilityUri> = new Set([
  // "Query the native's user-authored Life Event Log (LEL) ... the observed
  // life events used by [calibration]" — raw outcome ledger read.
  'marsys://tool/L5/lel_query',
  // "Returns logged predictions for a chart from mimamsa_predictions
  // (mi_bhavisya)" — raw prediction ledger read, matched against outcomes.
  'marsys://tool/L5/query_predictions',
])

/**
 * Plan §8 R-2 item 5 `demand_ranking.bearing_first`: capabilities whose
 * OWN handler already implements bearing-first ordering (a domain-matching
 * confirmed row is sorted ahead of a higher-raw-strength but domain-
 * irrelevant one — CLAUDE.md §N.6 part 3). Evidence:
 * `register_d9_judgment.ts`'s `bearing_yogas`/`bearing_yogas_corroboration`
 * sort logic. `register_d8_assess_domain.ts` (assess_career et al.)
 * explicitly comments that it has NOT yet been wired to this pattern
 * ("assess_* had not been wired to bearing_yogas") — correctly excluded.
 */
const BEARING_FIRST_URIS: ReadonlySet<CapabilityUri> = new Set([
  'marsys://tool/L-JUDGMENT/judgment_query',
])

/**
 * W3 "One Envelope" (RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §7 item 6 / master brief
 * §E W3 "density_contract 100% + verbosity knob WITH the C-4 guard"): capabilities whose
 * real, MEASURED wire-response ceiling is already codified elsewhere in the estate —
 * `platform-mcp/src/tools/registry_bridge.ts`'s `MCP_RESPONSE_BUDGET_KB` table (hand-
 * tuned against live-connector byte measurements: judgment_query/graha_portrait 12KB,
 * pact_query 8KB per R5.1 C1; assess_* 40KB, traverse_graph/get_cgm_subgraph/
 * get_projections 55KB per D-1.6 Lane S-5/R6 3b-budgets) — NOT re-derived here, mirrored
 * as evidence. `platform/src/lib/retrieval/registry` cannot import the separate
 * `platform-mcp` package, so this table is the registry-side echo of that one; if the
 * two ever drift, `registry_bridge.ts`'s table remains authoritative for the actual MCP
 * wire ceiling (this only sets the registry's own advertised `density_contract`, a
 * planning/introspection signal, not the trimmer's real budget).
 * `max_digest_bytes` uses the measured KB (×1024); `max_verdict_bytes` is a quarter of
 * that, matching the verdict-is-a-short-summary-of-the-digest relationship
 * `get_vichara.ts`'s hand-set MAX_VERDICT_BYTES=1024 / MAX_DIGEST_BYTES=4096 (a 1:4
 * ratio) already establishes as this estate's convention.
 */
const MEASURED_BUDGET_KB_URIS: ReadonlyMap<CapabilityUri, number> = new Map([
  ['marsys://tool/L-JUDGMENT/judgment_query', 12],
  ['marsys://tool/L2/graha_portrait', 12],
  ['marsys://tool/L-PACT/pact_query', 8],
  ['marsys://tool/L-DOMAIN/assess_marriage', 40],
  ['marsys://tool/L-DOMAIN/assess_career', 40],
  ['marsys://tool/L-DOMAIN/assess_health', 40],
  ['marsys://tool/L-DOMAIN/assess_wealth', 40],
  ['marsys://tool/L2/traverse_chart_graph', 55],
  // NOTE: marsys://tool/L3/query_projections is ALSO measured at 55KB in
  // registry_bridge.ts's MCP_RESPONSE_BUDGET_KB, but is deliberately OMITTED here —
  // this wave's must_not_touch scope freezes kala_*/gochara serving semantics, and this
  // stays conservative by leaving every L3_kala capability (including this one) on the
  // generic tool_role-tiered default below rather than a hand-picked override. Flagged
  // as a residual in the wave report: a future L3 session can add this specific
  // override once the kala_* freeze lifts.
])

/**
 * Tool-role-tiered verdict/digest byte defaults for every capability NOT in
 * `MEASURED_BUDGET_KB_URIS` above. Tiers are keyed off `tool_role` (a real D1
 * topology field every capability already carries — not a fresh classification
 * invented for this wave) and follow the same order-of-magnitude reasoning the
 * measured table above documents: terminal leaf/flat-fact lookups are smallest,
 * graph/synthesizer/umbrella surfaces (multi-source, drill-pointer-bearing) are
 * largest. `max_verdict_bytes` stays at the estate's 1:4 verdict:digest ratio
 * (get_vichara.ts precedent) throughout.
 */
const TOOL_ROLE_DIGEST_BYTES: Record<string, number> = {
  leaf: 4_096,
  drill: 8_192,
  umbrella: 16_384,
  graph: 40_960,
  hybrid_retrieval: 20_480,
  temporal: 12_288,
  quality: 4_096,
  synthesizer: 40_960,
}
const DEFAULT_DIGEST_BYTES = 8_192

/**
 * Parameter names that are structural (pagination/identity/shape controls), never
 * genuine content facets — excluded from the mechanical facet-derivation below so
 * `chart_id`/`ayanamsha_id`/`cursor`/`response_format` etc. don't get miscounted as
 * "filterable dimensions" the way a real facet (`domain`, `category`, `type`, ...) is.
 */
const STRUCTURAL_PARAM_NAMES: ReadonlySet<string> = new Set([
  'chart_id', 'ayanamsha_id', 'response_format', 'verbosity', 'cursor', 'limit',
  'offset', 'page', 'top_k', 'max_signals', 'include', 'format',
])

/** Real pagination-shaped param names — presence of any of these on `input_schema`
 *  is the evidence `paginated: true` is derived from (not a guess per capability). */
const PAGINATION_PARAM_NAMES: ReadonlySet<string> = new Set([
  'cursor', 'limit', 'offset', 'page', 'top_k', 'max_signals',
])

// ── Field derivation ──────────────────────────────────────────────────────────

function deriveAnnotations(cap: CapabilityDescriptor): NonNullable<CapabilityDescriptor['annotations']> {
  // MUST key off mutation, not assert read-only unconditionally — a write-capable
  // capability (mutation: true) can never be silently stamped read_only: true here.
  // Today MUTATION_URIS is empty (verified: zero SQL writes anywhere in the registry
  // layer tree — the real write surface lives entirely outside the registry, in
  // /api/mcp/writes/[action]/route.ts) so this branch is currently unreached in
  // practice, but the coupling must hold structurally for the day a write-dispatcher
  // route is folded into the registry (this module's own header anticipates that).
  if (deriveMutation(cap)) {
    return { read_only: false, idempotent: false, destructive: false, open_world: false }
  }
  return { read_only: true, idempotent: true, destructive: false, open_world: false }
}

function deriveMutation(cap: CapabilityDescriptor): boolean {
  return MUTATION_URIS.has(cap.uri)
}

function deriveDataSource(cap: CapabilityDescriptor): 'stored' | 'computed' | 'hybrid' {
  if (HYBRID_URIS.has(cap.uri)) return 'hybrid'
  if (SIDECAR_BACKED_URIS.has(cap.uri) || INTERNAL_INTROSPECTION_URIS.has(cap.uri)) return 'computed'
  return 'stored'
}

function deriveProjectionTags(
  cap: CapabilityDescriptor
): NonNullable<CapabilityDescriptor['projection_tags']> | undefined {
  if (INTERNAL_INTROSPECTION_URIS.has(cap.uri)) return undefined
  if (cap.traversal_level === 'L-ORIENT') {
    // OT-10 minimal orienting-tool surface: needs the widest reach, chat +
    // both MCP shapes + the dedicated consult surface.
    return ['chat', 'mcp_full', 'mcp_compact', 'mcp_consult']
  }
  if (cap.tool_role === 'leaf') {
    // Narrow terminal drill — returns data, not pointers; not umbrella-list
    // display real estate.
    return ['mcp_full']
  }
  return ['chat', 'mcp_full', 'mcp_compact']
}

function toTitleCase(name: string): string {
  return name
    .split('_')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

/** First sentence of `description` (or a clean truncation), capped so display surfaces stay short. */
function firstSentence(description: string, maxLen = 160): string {
  const trimmed = description.trim()
  const periodIdx = trimmed.indexOf('. ')
  let candidate = periodIdx > 0 && periodIdx < maxLen ? trimmed.slice(0, periodIdx + 1) : trimmed
  if (candidate.length > maxLen) {
    candidate = candidate.slice(0, maxLen).replace(/\s+\S*$/, '') + '…'
  }
  return candidate
}

function deriveDisplay(cap: CapabilityDescriptor): NonNullable<CapabilityDescriptor['display']> {
  // full_description deliberately omitted — falls back to `description` per the field's own doc comment.
  return { short_label: toTitleCase(cap.name), one_line: firstSentence(cap.description) }
}

function deriveCalibrationContextOnly(cap: CapabilityDescriptor): true | undefined {
  return CALIBRATION_CONTEXT_ONLY_URIS.has(cap.uri) ? true : undefined
}

function deriveDemandRanking(
  cap: CapabilityDescriptor
): NonNullable<CapabilityDescriptor['demand_ranking']> | undefined {
  return BEARING_FIRST_URIS.has(cap.uri) ? { bearing_first: true } : undefined
}

/**
 * W3 "One Envelope" — §N.6 density_contract derivation. See MEASURED_BUDGET_KB_URIS /
 * TOOL_ROLE_DIGEST_BYTES / STRUCTURAL_PARAM_NAMES doc comments above for the evidence
 * each sub-field is derived from. Only fills in for capabilities with `density_contract
 * === undefined` (six capabilities — get_vichara, get_yoga_dosha, get_dasha_lord_
 * capability, get_yoga_firings, query_signals, judgment_query — already hand-set their
 * own real value in W-1/R5.3/R5.1-era work and are left untouched by construction, same
 * as every other field in this module).
 */
function deriveDensityContract(cap: CapabilityDescriptor): NonNullable<CapabilityDescriptor['density_contract']> {
  const measuredKb = MEASURED_BUDGET_KB_URIS.get(cap.uri)
  const max_digest_bytes = measuredKb !== undefined
    ? measuredKb * 1024
    : (TOOL_ROLE_DIGEST_BYTES[cap.tool_role] ?? DEFAULT_DIGEST_BYTES)
  const max_verdict_bytes = Math.round(max_digest_bytes / 4)

  const paramNames = Object.keys(cap.input_schema ?? {})
  const paginated = paramNames.some((p) => PAGINATION_PARAM_NAMES.has(p))
  const facets = paramNames.filter((p) => !STRUCTURAL_PARAM_NAMES.has(p))

  // orientation_digest / calibration archetypes are single-scalar whole-chart or
  // quality summaries — they don't have a meaningful "zero rows" state distinct from
  // "computation ran and produced a value" the way a filtered row-list does, so
  // empty_reason is not applicable. Every row/list-shaped archetype defaults to true —
  // an honestly-empty result must say why (B.10), never silently ship `[]`.
  const empty_reason = cap.archetype !== 'orientation_digest' && cap.archetype !== 'calibration'

  return { max_verdict_bytes, max_digest_bytes, paginated, facets, empty_reason }
}

// ── Apply (mutates in place, fills only undefined fields) ────────────────────

export interface BackfillResult {
  uri: CapabilityUri
  fields_set: string[]
}

/**
 * Fill any of the nine R-1.1 fields that are currently `undefined` on `cap`
 * with a generator-derived default. Never overwrites an already-set value
 * (idempotent — safe to call on every `getCatalog()` read, and safe to call
 * again once a future wave starts setting some fields by hand per-capability).
 */
export function applyDescriptorDefaults(cap: CapabilityDescriptor): BackfillResult {
  const fields_set: string[] = []

  if (cap.annotations === undefined) {
    cap.annotations = deriveAnnotations(cap)
    fields_set.push('annotations')
  }
  if (cap.mutation === undefined) {
    cap.mutation = deriveMutation(cap)
    fields_set.push('mutation')
  }
  if (cap.data_source === undefined) {
    cap.data_source = deriveDataSource(cap)
    fields_set.push('data_source')
  }
  if (cap.projection_tags === undefined) {
    const tags = deriveProjectionTags(cap)
    if (tags !== undefined) {
      cap.projection_tags = tags
      fields_set.push('projection_tags')
    }
  }
  if (cap.display === undefined) {
    cap.display = deriveDisplay(cap)
    fields_set.push('display')
  }
  if (cap.calibration_context_only === undefined) {
    const flag = deriveCalibrationContextOnly(cap)
    if (flag !== undefined) {
      cap.calibration_context_only = flag
      fields_set.push('calibration_context_only')
    }
  }
  if (cap.demand_ranking === undefined) {
    const dr = deriveDemandRanking(cap)
    if (dr !== undefined) {
      cap.demand_ranking = dr
      fields_set.push('demand_ranking')
    }
  }
  if (cap.density_contract === undefined) {
    cap.density_contract = deriveDensityContract(cap)
    fields_set.push('density_contract')
  }
  // register.glossary and family_overrides intentionally NOT defaulted — see module doc comment.

  return { uri: cap.uri, fields_set }
}

/** Apply defaults to every capability in `caps`, returning one BackfillResult per capability. */
export function applyDescriptorDefaultsToCatalog(caps: readonly CapabilityDescriptor[]): BackfillResult[] {
  return caps.map((cap) => applyDescriptorDefaults(cap))
}

// Exported for the CLI report script and for tests — not part of the public
// derivation contract, but useful to assert against directly.
export const __backfillClassificationTables = {
  SIDECAR_BACKED_URIS,
  HYBRID_URIS,
  INTERNAL_INTROSPECTION_URIS,
  MUTATION_URIS,
  CALIBRATION_CONTEXT_ONLY_URIS,
  BEARING_FIRST_URIS,
  MEASURED_BUDGET_KB_URIS,
}
