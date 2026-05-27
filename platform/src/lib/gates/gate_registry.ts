/**
 * Stream C / Unit 2d — gate_registry
 *
 * Static catalogue of every controllable gate in the system. Each entry declares
 * its class, scope, value_type, default, description, hot_reload flag, and
 * whether flipping it is a "danger" action (requires confirm at the UI layer
 * and a reason in `gate_change_log`).
 *
 * Runtime values come from `runtime_config` (DB) with this `default` as the
 * bootstrap fallback. See `src/lib/config/configService.ts`.
 *
 * This is a representative MVP set spanning all five classes. Owning units
 * (2a/2b/2c, R11.x, …) will add their own gates as they land.
 */

export type GateClass =
  | 'feature_flag'
  | 'pipeline_threshold'
  | 'model_routing'
  | 'access_capability'
  | 'data_source'

export type GateScope = 'global' | 'per_chart'

export type GateValueType = 'boolean' | 'number' | 'string' | 'json'

export interface GateSpec {
  /** Stable key — used both as `runtime_config.key` and env-var suffix where applicable. */
  key: string
  class: GateClass
  scope: GateScope
  value_type: GateValueType
  /** Bootstrap default applied when no runtime_config row exists. */
  default: boolean | number | string | Record<string, unknown>
  description: string
  /** False ⇒ requires service restart to take effect. UI surfaces this. */
  hot_reload: boolean
  /** True ⇒ Command Center requires explicit confirm + reason on edit. */
  danger: boolean
  /**
   * Soft subgroup label for UI grouping inside a class
   * (e.g. data_source.assets vs data_source.ayanamsha).
   */
  group?: string
}

/**
 * Canonical registry. Order is the display order in the Command Center.
 * Adding a gate here is sufficient to make it readable via `getGate`; making
 * it editable is automatic once it appears here.
 */
export const GATE_REGISTRY: readonly GateSpec[] = [
  // ── feature_flag ────────────────────────────────────────────────────────────
  {
    key: 'MARSYS_FLAG_OBSERVATORY_ENABLED',
    class: 'feature_flag',
    scope: 'global',
    value_type: 'boolean',
    default: true,
    description:
      'Gates the super-admin Observatory dashboard route and its API guard.',
    hot_reload: true,
    danger: false,
  },

  // ── pipeline_threshold ─────────────────────────────────────────────────────
  {
    key: 'CITATION_FLOOR_DENSITY',
    class: 'pipeline_threshold',
    scope: 'global',
    value_type: 'number',
    default: 0.7,
    description:
      'Minimum citation density (cites per ≥30-word claim) before synthesis is flagged.',
    hot_reload: true,
    danger: false,
  },

  // ── model_routing ───────────────────────────────────────────────────────────
  {
    key: 'DEFAULT_PROVIDER',
    class: 'model_routing',
    scope: 'global',
    value_type: 'string',
    default: 'anthropic',
    description:
      'Default LLM provider for synthesis when no per-query override is set.',
    hot_reload: true,
    danger: true,
  },

  // ── access_capability ───────────────────────────────────────────────────────
  {
    key: 'MCP_API_KEY_REQUIRED',
    class: 'access_capability',
    scope: 'global',
    value_type: 'boolean',
    default: true,
    description:
      'When true, every MCP tool call must present a registered API key. Disabling opens the surface.',
    hot_reload: true,
    danger: true,
  },

  // ── data_source.assets ──────────────────────────────────────────────────────
  {
    key: 'FORENSIC_ENABLED',
    class: 'data_source',
    scope: 'global',
    value_type: 'boolean',
    default: true,
    description:
      'Master switch for FORENSIC L1 chart data. Disabling cascades to all retrieval tools depending on it.',
    hot_reload: false,
    danger: true,
    group: 'assets',
  },
  {
    key: 'MSR_ENABLED',
    class: 'data_source',
    scope: 'global',
    value_type: 'boolean',
    default: true,
    description:
      'Master switch for the Manifest Signal Register (MSR). Disables msr_sql + dependent tools.',
    hot_reload: true,
    danger: false,
    group: 'assets',
  },
  {
    key: 'LEL_ENABLED',
    class: 'data_source',
    scope: 'global',
    value_type: 'boolean',
    default: true,
    description:
      'Master switch for the Life Event Log. Off = LEL unavailable to synthesis for all charts (serve-time-only + build-exclusion rule).',
    hot_reload: true,
    danger: false,
    group: 'assets',
  },

  // ── data_source.ayanamsha (read-only display) ──────────────────────────────
  {
    key: 'AYANAMSHA_CANONICAL_ENABLED',
    class: 'data_source',
    scope: 'global',
    value_type: 'boolean',
    default: true,
    description:
      'Canonical (True Chitrapaksha) ayanamsha role. CANNOT be disabled — guard enforced at write time.',
    hot_reload: false,
    danger: true,
    group: 'ayanamsha',
  },
  {
    key: 'AYANAMSHA_KP_ENABLED',
    class: 'data_source',
    scope: 'global',
    value_type: 'boolean',
    default: true,
    description: 'KP-Newcomb ayanamsha role (used by KP-class tools).',
    hot_reload: false,
    danger: false,
    group: 'ayanamsha',
  },
  {
    key: 'AYANAMSHA_REFERENCE_ENABLED',
    class: 'data_source',
    scope: 'global',
    value_type: 'boolean',
    default: true,
    description: 'Reference (Lahiri) ayanamsha role surfaced for cross-school disagreement audit.',
    hot_reload: false,
    danger: false,
    group: 'ayanamsha',
  },
] as const

/** Lookup. Throws on unknown key — Command Center never reaches unknown keys. */
export function getGateSpec(key: string): GateSpec {
  const spec = GATE_REGISTRY.find((g) => g.key === key)
  if (!spec) throw new Error(`gate_registry: unknown gate "${key}"`)
  return spec
}

/** Group view: { class → GateSpec[] } preserving registry order. */
export function gatesByClass(): Record<GateClass, GateSpec[]> {
  const out: Record<GateClass, GateSpec[]> = {
    feature_flag: [],
    pipeline_threshold: [],
    model_routing: [],
    access_capability: [],
    data_source: [],
  }
  for (const g of GATE_REGISTRY) out[g.class].push(g)
  return out
}

/** Ayanamsha-registry view for read-only display. */
export const AYANAMSHA_REGISTRY = [
  { role: 'canonical', source: 'True Chitrapaksha', gate: 'AYANAMSHA_CANONICAL_ENABLED' },
  { role: 'kp', source: 'KP-Newcomb', gate: 'AYANAMSHA_KP_ENABLED' },
  { role: 'reference', source: 'Lahiri', gate: 'AYANAMSHA_REFERENCE_ENABLED' },
] as const
