export type FeatureFlag =
  | 'PANEL_MODE_ENABLED'
  | 'MANIFEST_BUILDER_ENABLED'
  | 'LLM_CHECKPOINTS_ENABLED'
  // BHISMA-B1 §6.2 — retired: BUNDLE_AUGMENTER_ENABLED, MSR_RERANKER_ENABLED,
  // SEMANTIC_GATE_ENABLED were declared but never implemented in any code path.
  // NEW_QUERY_PIPELINE_ENABLED retired Phase 11B (2026-05-11): legacy code path deleted.
  | 'VALIDATOR_FAILURE_HALT'
  | 'SYNTHESIS_PROMPT_DEBUG'
  | 'DISCLOSURE_TIER_DEBUG'
  // AUDIT_ENABLED retired BHISMA-B1 §6.2: always-on; conditional removed from route.ts.
  | 'AUDIT_VIEW_VISIBLE'
  | 'PANEL_CHECKBOX_VISIBLE'
  | 'BUNDLE_COMPOSER_DEBUG'
  // CGM_GRAPH_WALK_ENABLED retired BHISMA-B1: always-on; flag gate removed from cgm_graph_walk.ts
  | 'MANIFEST_QUERY_ENABLED'
  | 'VECTOR_SEARCH_ENABLED'
  // Phase 6 — LLM Checkpoints (all default OFF; flip individually after warn-mode observation)
  | 'CHECKPOINT_4_5_ENABLED'
  | 'CHECKPOINT_4_5_FAIL_HARD'
  | 'CHECKPOINT_5_5_ENABLED'
  | 'CHECKPOINT_5_5_FAIL_HARD'
  | 'CHECKPOINT_8_5_ENABLED'
  | 'CHECKPOINT_8_5_FAIL_HARD'
  | 'CHECKPOINT_8_5_PREDICTION_EXTRACT'
  // Phase 7 — Panel Mode
  | 'PANEL_DEGRADE_2_OF_3'
  // PER_TOOL_PLANNER_ENABLED retired BHISMA-B1 §6.2.
  // Pipeline-Transform-S1 (2026-05-11) retired both planner-related flags:
  // the new pipeline_planner is the only planner (no fallback); planner-
  // emitted synthesis_guidance replaces the LLM context assembler step.
  // BHISMA-B1 §6.2 — New observability flags (all default ON)
  /** Enables the Trace Analytics tab and cross-query history aggregations. */
  | 'TRACE_ANALYTICS_ENABLED'
  /** Enables per-query cost estimation (planning + synthesis USD buckets in trace). */
  | 'COST_TRACKING_ENABLED'
  /** Enables MSR signal citation count check in synthesis_done trace step. */
  | 'CITATION_CHECK_ENABLED'
  // REASONING_MODEL_STREAMING retired (BHISMA Wave 2) — o-series models removed from registry.
  // All registry models use streamText; no generateText fallback path exists.
  // M3-W1-A2 — Discovery Engine flag gates (Pattern + Contradiction + Resonance + Cluster).
  // Default false at first commit, flipped true after smoke verification within the same session.
  /** Enables pattern_register retrieval tool. */
  | 'DISCOVERY_PATTERN_ENABLED'
  /** Enables contradiction_register retrieval tool. */
  | 'DISCOVERY_CONTRADICTION_ENABLED'
  /** Enables resonance_register retrieval tool. */
  | 'DISCOVERY_RESONANCE_ENABLED'
  /** Enables cluster_atlas retrieval tool. */
  | 'DISCOVERY_CLUSTER_ENABLED'
  // M4-FEAT-LEL-TOGGLE — Blind mode. When false, query_life_events is
  // excluded from consumeTools and the query is tagged as a prospective
  // blind-mode prediction. Default true (informed mode).
  | 'LEL_CONTEXT_ENABLED'
  // NVIDIA NIM — query-class-aware planner routing (BHISMA Wave 2 / UQE-4a).
  // Default OFF; flip true after NVIDIA_NIM_API_KEY is provisioned and UQE-4a
  // planner call site is wired. When ON, getNvidiaPlanner(queryClass) selects
  // the NIM model; when OFF, FAMILY_WORKER for the synthesis model is used.
  /** Routes UQE planner calls to NVIDIA NIM models by query class. */
  | 'NVIDIA_PLANNER_ENABLED'
  // W2-EVAL-A — Citation gate admin override. When true, the Layer-2 citation
  // validator demotes ERROR to WARN so the response is still returned. Default
  // OFF so missing-citation prescriptive queries hard-fail and surface in logs.
  | 'CITATION_GATE_OVERRIDE'
  // Phase O Observatory (USTAD_S1_9). Gates the super-admin Observatory dashboard
  // route, AuthGate, and the typed API client. Default OFF; flip via env
  // MARSYS_FLAG_OBSERVATORY_ENABLED=true. Mirrors the env-var gate already used
  // by the backend at platform/src/app/api/admin/observatory/_guard.ts.
  | 'OBSERVATORY_ENABLED'
  // M5-B LL.3 R.LL3.2 — Pancha-Mahapurusha cluster-modifier. When ON, the 6-signal
  // Pancha-MP clique (SIG.MSR.117/.118/.119/.143/.145/.402b) is consolidated to a
  // single weight entry (MAX of member weights) to prevent 6× double-counting of the
  // natal yoga structure in downstream synthesis. Default OFF until benchmarked.
  | 'LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED'
  // M5-B LL.3 R.LL3.3 — Zero-LL.1-weight domain disclaimer. When ON, msr_sql
  // annotates results for domains with no LL.1 calibration weight (career, spiritual,
  // psychological, financial, family) with an explicit n=0 disclaimer in invocation_params,
  // so the synthesizer does not treat absence-of-weight as absence-of-signal. Default ON.
  | 'LL3_ZERO_WEIGHT_DOMAIN_DISCLAIMER_ENABLED'

export const DEFAULT_FLAGS: Record<FeatureFlag, boolean> = {
  PANEL_MODE_ENABLED: true,
  MANIFEST_BUILDER_ENABLED: false,
  LLM_CHECKPOINTS_ENABLED: false,
  VALIDATOR_FAILURE_HALT: true,
  SYNTHESIS_PROMPT_DEBUG: false,
  DISCLOSURE_TIER_DEBUG: false,
  AUDIT_VIEW_VISIBLE: true,
  PANEL_CHECKBOX_VISIBLE: false,
  BUNDLE_COMPOSER_DEBUG: false,
  MANIFEST_QUERY_ENABLED: true,
  VECTOR_SEARCH_ENABLED: true,
  CHECKPOINT_4_5_ENABLED: false,
  CHECKPOINT_4_5_FAIL_HARD: false,
  CHECKPOINT_5_5_ENABLED: false,
  CHECKPOINT_5_5_FAIL_HARD: false,
  CHECKPOINT_8_5_ENABLED: false,
  CHECKPOINT_8_5_FAIL_HARD: false,
  CHECKPOINT_8_5_PREDICTION_EXTRACT: false,
  // Phase 7 — Panel Mode (all default OFF)
  PANEL_DEGRADE_2_OF_3: false,
  // Two planner flags retired in Pipeline-Transform-S1 (2026-05-11): the
  // new pipeline_planner is unconditional; synthesis_guidance from the
  // planner replaces the prior intermediate LLM compression step.
  // BHISMA-B1 §6.2 — New observability flags (all default ON)
  TRACE_ANALYTICS_ENABLED: true,
  COST_TRACKING_ENABLED: true,
  CITATION_CHECK_ENABLED: true,
  // REASONING_MODEL_STREAMING removed — retired above.
  // M3-W1-A2 Discovery Engine flag gates — flipped true after smoke verification
  // within the same session (AC.M3A.2 / AC.M3A.3). Set MARSYS_FLAG_DISCOVERY_*=false
  // in env to opt out of any individual surface.
  DISCOVERY_PATTERN_ENABLED: true,
  DISCOVERY_CONTRADICTION_ENABLED: true,
  DISCOVERY_RESONANCE_ENABLED: true,
  DISCOVERY_CLUSTER_ENABLED: true,
  // M4-FEAT-LEL-TOGGLE — default true (informed mode).
  // Override via MARSYS_FLAG_LEL_CONTEXT_ENABLED=false in env.
  LEL_CONTEXT_ENABLED: true,
  // NVIDIA NIM planner — ON (NVIDIA_NIM_API_KEY provisioned 2026-05-01).
  // Routes UQE planner calls to NIM models by query class when stack=nim.
  NVIDIA_PLANNER_ENABLED: true,
  // W2-EVAL-A — Citation gate override OFF; ERROR fails loud by default.
  CITATION_GATE_OVERRIDE: false,
  // Phase O Observatory — default OFF; flip via MARSYS_FLAG_OBSERVATORY_ENABLED=true.
  OBSERVATORY_ENABLED: false,
  // M5-B LL.3 R.LL3.2 — Pancha-MP cluster modifier. Default OFF until benchmarked.
  // Override via MARSYS_FLAG_LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED=true.
  LL3_PANCHA_MP_CLUSTER_MODIFIER_ENABLED: false,
  // M5-B LL.3 R.LL3.3 — Zero-LL.1-weight domain disclaimer. Default ON.
  // Override via MARSYS_FLAG_LL3_ZERO_WEIGHT_DOMAIN_DISCLAIMER_ENABLED=false.
  LL3_ZERO_WEIGHT_DOMAIN_DISCLAIMER_ENABLED: true,
}

// Numeric config keys (read via configService.getValue)
export const CGM_GRAPH_WALK_MAX_DEPTH_KEY = 'CGM_GRAPH_WALK_MAX_DEPTH'
export const VECTOR_SEARCH_TOP_K_KEY = 'VECTOR_SEARCH_TOP_K'
export const CGM_GRAPH_WALK_MAX_DEPTH_DEFAULT = 3
export const VECTOR_SEARCH_TOP_K_DEFAULT = 20

export const FLAG_ENV_PREFIX = 'MARSYS_FLAG_'
