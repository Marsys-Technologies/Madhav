/**
 * Vidhi Engine — type definitions (D-2 Lane V-1).
 *
 * "Vidhi = grammar + compiler, NOT a fixed checklist"
 * (DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3). These types back:
 *   - the ~30 versioned primitive rows (registry_data.ts / DB table `vidhi_primitives`)
 *   - the per-intent-class acharya floor + machine band (registry_data.ts / DB table
 *     `vidhi_intent_floors` + `vidhi_floor_items`)
 *   - the deterministic compiler (compiler.ts)
 *
 * Server owns bands 1 (acharya floor) + 2 (machine band) — deterministic, versioned,
 * auditable, model-independent. The LLM owns band 3 (question-specific extension) and
 * the classification of the question into a scope tuple. This module implements only
 * bands 1 + 2 plus the compiler that assembles them; band 3 is consumer-side by design.
 */

/** A primitive's functional category — informational grouping only, not used for filtering. */
export type PrimitiveCategory =
  | 'structural'
  | 'strength'
  | 'temporal'
  | 'signal'
  | 'doctrine'
  | 'remedy'
  | 'utility';

/**
 * §B0.4 mandatory-floor-content tags. Every tag below MUST appear on at least one
 * primitive that is itself consumed by at least one intent-class floor (asserted by
 * the floor-coverage test). Sourced verbatim from BRIEF_D2.md §B0.4 / §F0.
 */
export const MANDATORY_SURFACE_TAGS = [
  'chalit_cusp',
  'sudarshana_agreement',
  'bhavat_bhavam',
  'bhava_bala',
  'ashtakavarga_bindu',
  'varga_hora_class',
  'karakamsa',
  'kp_cusp_sublord',
  'dasha_lord_capability',
  'varga_ratification_divergence',
  'sensitive_degree',
] as const;

export type MandatorySurfaceTag = (typeof MANDATORY_SURFACE_TAGS)[number];

/**
 * A versioned vidhi primitive: fixed atom of retrieval. Each maps to a live MCP tool
 * (verified against the deployed connector's 135-tool catalog — see registry_data.ts
 * header) + args template, a fallback face for when the primary tool degrades, and a
 * `known_gap` pointer into the CR register (POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md)
 * when the primitive's coverage is incomplete. `known_gap` is `null` when the primitive
 * has no outstanding register gap — it must NEVER cite a CLOSED CR (registry completeness
 * test enforces this against the OPEN/LOGGED allowlist in cr_status.ts).
 */
export interface VidhiPrimitive {
  readonly primitive_id: string;
  readonly version: number;
  readonly definition: string;
  readonly category: PrimitiveCategory;
  /** Real, live MCP tool name (mcp__marsys-jis-direct__<live_tool> on the deployed connector). */
  readonly live_tool: string;
  /** Args template — `{chart_id}` and other `{placeholder}` tokens are filled by the compiler/caller. */
  readonly tool_args: Readonly<Record<string, unknown>>;
  /** Secondary/degraded-mode face, or null if the primary tool has no fallback. */
  readonly fallback_face: string | null;
  /** CR-N register pointer (e.g. "CR-56"), or null if no open gap. */
  readonly known_gap: string | null;
  /** §B0.4 mandatory-surface tags this primitive satisfies (empty array if none). */
  readonly mandatory_tags: readonly MandatorySurfaceTag[];
  /** CR-27 improvisation-corpus instance(s) this primitive's presence-on-a-floor prevents. */
  readonly cr27_prevents: readonly string[];
}

export type FloorBand = 'acharya_floor' | 'machine_band';

export interface FloorItem {
  readonly primitive_id: string;
  readonly order: number;
  readonly band: FloorBand;
  /** Optional per-floor arg overrides merged onto the primitive's tool_args (e.g. house number). */
  readonly args_override?: Readonly<Record<string, unknown>>;
  /**
   * §N.6 Serving-Density signal (VIDHI-PŪRṆATĀ P-3b). `true` marks this item as on the
   * densest / most-actionable layer of its band — E-0's foundational digest lead rows, and
   * E-7's insight band (contradiction/tail_divergence/mechanism/statistical). It is the
   * machine-readable analogue of `response_budget.ts`'s `TrimmableSection.hardFloor`: a budget
   * trim must protect these rows and never sacrifice them FIRST (§N.6 Part 2 + Part 4:
   * "density signaling is data, not narration"). Absent/false ⇒ a lower-density, floorable row.
   */
  readonly hard_floor?: boolean;
}

export type IntentClass =
  | 'wealth_deepdive'
  | 'career_deepdive'
  | 'health_deepdive'
  | 'marriage_deepdive'
  // VIDHI-PŪRṆATĀ P-2 (F1 taxonomy completeness, 2026-07-23): three life-domain deepdives
  // the pre-wave enum lacked. `spirituality_deepdive` is MANDATORY (brief §2 P-2);
  // `education_deepdive` / `progeny_deepdive` are the CANDIDATE pair, added with full worked
  // floors because P-0's data-support ledger confirmed D24 (education) and D7 (progeny) are
  // data-backed live. All three carry a registered floor in registry_data.ts.
  | 'spirituality_deepdive'
  | 'education_deepdive'
  | 'progeny_deepdive'
  | 'structure_read'
  | 'panoramic_breadth'
  | 'retrieval_only'
  | 'general_synthesis';

export interface IntentFloor {
  readonly intent: IntentClass;
  readonly version: number;
  readonly floor_items: readonly FloorItem[];
  /** CR-27 corpus instance ids this floor's item set is designed to prevent. */
  readonly cr27_coverage: readonly string[];
  readonly notes?: string;
}

export type ScopeWidth = 'narrow' | 'standard' | 'panoramic';
export type ScopeDepth = 'retrieval' | 'structure' | 'deepdive';
export type ScopeHorizon = 'natal' | 'current' | 'multi_year';
export type ScopeEntitlement = 'native' | 'research' | 'public_disclosed';

/**
 * question → scope_tuple(intent, domains, width, depth, horizon, intervention?, entitlement)
 * (DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3). Classification into this tuple is LLM-owned
 * (band 3 / CR-28 territory — V-3 wires intent_classify once the CR-28 ruling lands);
 * this module only compiles a tuple into a contract, deterministically.
 */
export interface ScopeTuple {
  readonly intent: IntentClass;
  readonly domains: readonly string[];
  readonly width: ScopeWidth;
  readonly depth: ScopeDepth;
  readonly horizon: ScopeHorizon;
  readonly intervention: boolean;
  readonly entitlement: ScopeEntitlement;
}

export interface CompiledFloorItem {
  readonly primitive_id: string;
  readonly band: FloorBand;
  readonly live_tool: string;
  readonly tool_args: Readonly<Record<string, unknown>>;
  readonly fallback_face: string | null;
  readonly known_gap: string | null;
  /**
   * §N.6 density signal, compiled from `FloorItem.hard_floor` (VIDHI-PŪRṆATĀ P-3b). Always
   * present on the compiled item (`false` when the floor item did not declare it). The serving
   * layer / response-budget trimmer reads this to protect the densest layer (E-0 digest lead,
   * E-7 insight band) ahead of floorable rows.
   */
  readonly hard_floor: boolean;
}

export interface CompletenessReceiptTemplate {
  /** Populated at serving time (V-2) — floor primitive_ids actually served. */
  readonly served: readonly string[];
  /** Populated at serving time — floor primitive_ids that returned empty. */
  readonly empty: readonly string[];
  /** Floor primitive_ids that are dark BY CONSTRUCTION (known_gap != null) — computable at compile time. */
  readonly dark: readonly string[];
}

/**
 * E-3 Anusaraṇa (chart-adaptive) one-hop expansion RULE (VIDHI-PŪRṆATĀ P-3b). Emitted by the
 * compiler AFTER the static floor resolves, as a PURE function of (compiled floor + registry) —
 * it consults NO chart facts and embeds NO chart_id, so it stays chart-agnostic and the
 * determinism / hash-equality test still holds (the floor_cache reuses it verbatim across
 * charts). Each rule is a follow-DIRECTIVE the executor materializes against live chart facts;
 * the compiler never RESOLVES it (that would require chart data). Hard-capped at ONE hop
 * (`hop: 1`, no transitive closure) so §N.6 budgets survive.
 */
export type AnusaranaRule = 'bhavesha_dispositor_hop' | 'karaka_dispositor_hop' | 'response_flag_drill';

export interface AdaptiveExpansion {
  readonly rule: AnusaranaRule;
  /** The compiled floor item this expansion follows FROM. */
  readonly source_primitive_id: string;
  /** The house the source item targets (bhavesha/bhava hops), when applicable. */
  readonly source_house?: number;
  /** The kāraka the source item targets (karaka hops), when applicable. */
  readonly source_karaka?: string;
  /** Human/machine description of the single hop the executor performs against chart facts. */
  readonly follow: string;
  /** The primitive the executor is pre-authorized to add at the (executor-)resolved target. */
  readonly add_primitive_id: string;
  /** When the executor should materialize this (response-flag rules fire only on a live flag). */
  readonly trigger: string;
  /** Hard cap — always 1. One hop, no transitive closure. */
  readonly hop: 1;
  readonly note: string;
}

/**
 * The compiled output. Deterministic: identical `ScopeTuple` → byte-identical
 * `CompiledContract` (compiler.test.ts asserts this via a hash-equality check).
 */
export interface CompiledContract {
  readonly compiler_version: string;
  readonly scope_tuple: ScopeTuple;
  readonly floor: readonly CompiledFloorItem[];
  readonly machine_band: readonly CompiledFloorItem[];
  /**
   * E-3 Anusaraṇa: the deterministic, one-hop, executor-side expansion rules compiled from the
   * resolved floor. Empty when no floor item triggers a follow-rule. Never executed by the
   * compiler; the executor materializes each against live chart facts (see `AdaptiveExpansion`).
   */
  readonly adaptive_expansions: readonly AdaptiveExpansion[];
  readonly completeness_receipt_template: CompletenessReceiptTemplate;
  readonly llm_extension_note: string;
}
