/**
 * Unified Tool Contract — types (Unit 2b, sets G3_contract).
 *
 * One source of truth for every retrieval tool's identity, schema, and
 * cross-channel metadata. Both the portal (platform/src/lib/retrieve/index.ts)
 * and MCP (platform-mcp/src/) build their tool list from contracts authored
 * here. See briefs/BRIEF_2b_unified_contract.md.
 */

import type { z } from 'zod'

/**
 * Role taxonomy. Every tool declares a single role.
 *  - `retrieval`  L1 fact / corpus / engine lookup (the common case)
 *  - `synthesis`  L2.5+ composite read (e.g. holistic_bundle)
 *  - `observability`  trace / health / coverage introspection
 *  - `write`      log_prediction, record_outcome, flag_disagreement
 *  - `text`       raw-asset / classical-text reads (no chart binding)
 */
export type ToolRole =
  | 'retrieval'
  | 'synthesis'
  | 'observability'
  | 'write'
  | 'text'

/**
 * Family. A coarse grouping used by the planner + UI faceting.
 */
export type ToolFamily =
  | 'chart'
  | 'time'
  | 'dasha'
  | 'kp'
  | 'transit'
  | 'panchang'
  | 'ephemeris'
  | 'signal'
  | 'graph'
  | 'school'
  | 'text'
  | 'asset'
  | 'observability'
  | 'write'

/**
 * Coarse data dependency hint — what the tool reads from. Used by the gateway
 * (Wave-3) for routing/health gating; here it is metadata only.
 */
export type DataDependency =
  | 'chart_facts'
  | 'msr'
  | 'cdlm'
  | 'ucn'
  | 'rm'
  | 'cgm'
  | 'lel'
  | 'panchang_daily'
  | 'ephemeris'
  | 'rag_chunks'
  | 'classical_text'
  | 'discovery_layer'
  | 'observatory'
  | 'sidecar'
  | 'none'

/**
 * Ayanamsha role — engine-isolation contract from Unit 1.1.
 *  - `canonical`  Parashari / varga / dasha / MSR — uses the canonical ayanamsha (Lahiri default)
 *  - `kp`         KP system — uses the KP ayanamsha
 *  - `reference`  Pure ephemeris / observatory — accepts any ayanamsha as a reference frame
 *
 * Tools that are not chart-binding (text, asset, observability, write) MAY
 * declare `null` to opt out of the ayanamsha dimension.
 */
export type AyanamshaRole = 'canonical' | 'kp' | 'reference' | null

/**
 * Tool annotations (mirrors MCP server tool annotations) — Claude-tuned hints.
 */
export interface ToolAnnotations {
  readOnly?: boolean
  idempotent?: boolean
  surgical?: boolean
  /** Layer hint for the planner (L1 fact, L2.5 synthesis, etc.). */
  layer?: 'L1' | 'L1.5' | 'L2.5' | 'L5' | 'L9'
}

/**
 * The unified contract carried by every tool — the SINGLE source of truth.
 */
export interface ToolContract<TInput = unknown> {
  /** Canonical name (MCP name; portal aliases collapse to this in Wave-3). */
  canonical_name: string

  /** Zod input schema. JSON-Schema is generated from this. */
  input_schema: z.ZodType<TInput>

  /** Claude-tuned tool description (disambiguator + when-to-prefer). */
  description: string

  /** Annotation flags — read-only, idempotent, surgical, layer. */
  annotations: ToolAnnotations

  /** Role taxonomy. */
  role: ToolRole

  /** Family grouping. */
  family: ToolFamily

  /** Coarse data dependency. */
  data_dependency: DataDependency

  /**
   * Ayanamsha role per Unit 1.1 engine isolation. `null` ONLY for non-chart
   * tools (text/asset/observability/write). Every chart-binding tool MUST
   * declare one of `canonical | kp | reference`.
   */
  ayanamsha_role: AyanamshaRole

  /**
   * Default ayanamsha id for this role. Tools accept an optional input
   * `ayanamsha_id` (declared in input_schema) which overrides this default.
   * `null` when ayanamsha_role is null.
   */
  ayanamsha_id: string | null

  /**
   * Is this tool per-chart (requires `chart_id` in input)? Gate 4 will remove
   * the `NATIVE_CHART_ID` default; the contract enforces required-ness now
   * by virtue of the Zod schema. This flag is the invariant assertion target.
   */
  per_chart: boolean
}

/**
 * Default ayanamsha ids per role. Lahiri remains the canonical/Parashari default
 * to preserve current native chart parity (Unit 1.1 jh_oracle uses True Chitra
 * but Lahiri is the contract-level canonical id for the existing chart facts).
 * The contract simply declares the default — the engine may override.
 */
export const DEFAULT_AYANAMSHA_BY_ROLE: Record<
  Exclude<AyanamshaRole, null>,
  string
> = {
  canonical: 'lahiri',
  kp: 'kp_newcomb',
  reference: 'lahiri',
}
