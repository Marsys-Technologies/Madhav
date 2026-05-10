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
  // PER_TOOL_PLANNER_ENABLED retired BHISMA-B1 §6.2: was never flipped true; removed from route.ts.
  // BHISMA Stream 2 — LLM-first planner replaces classify+compose+plan_per_tool when ON.
  // Default ON since Lever-2 gate cleared (2026-05-04, recall 0.940 / precision 0.945).
  // Set MARSYS_FLAG_LLM_FIRST_PLANNER_ENABLED=false in env to revert to legacy path.
  | 'LLM_FIRST_PLANNER_ENABLED'
  // W2-CTX-ASSEMBLY: context assembly LLM step between retrieval and synthesis.
  // Default OFF. Flip true after smoke verification. Model: STACK_ROUTING[stack].context_assembly.primary.
  | 'CONTEXT_ASSEMBLY_ENABLED'
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
  // BHISMA Stream 2 — LLM-first planner. Default ON (Lever-2 cleared 2026-05-04).
  LLM_FIRST_PLANNER_ENABLED: true,
  // W2-CTX-ASSEMBLY — context assembly LLM step.
  // Re-flipped true (GANGA-D4-UNBLOCK): added generateText + context_assembler mocks
  // to orchestrator_wiring.test.ts and route.test.ts; full suite passes at 0 net new failures.
  CONTEXT_ASSEMBLY_ENABLED: true,
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
}

// Numeric config keys (read via configService.getValue)
export const CGM_GRAPH_WALK_MAX_DEPTH_KEY = 'CGM_GRAPH_WALK_MAX_DEPTH'
export const VECTOR_SEARCH_TOP_K_KEY = 'VECTOR_SEARCH_TOP_K'
export const CGM_GRAPH_WALK_MAX_DEPTH_DEFAULT = 3
export const VECTOR_SEARCH_TOP_K_DEFAULT = 20

export const FLAG_ENV_PREFIX = 'MARSYS_FLAG_'
