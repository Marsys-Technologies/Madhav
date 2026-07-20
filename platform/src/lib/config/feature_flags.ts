export type FeatureFlag =
  | 'PANEL_MODE_ENABLED'
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
  // M5-B LL.3 R.LL3.3 — Zero-LL.1-weight domain disclaimer. When ON, msr_sql
  // annotates results for domains with no LL.1 calibration weight (career, spiritual,
  // psychological, financial, family) with an explicit n=0 disclaimer in invocation_params,
  // so the synthesizer does not treat absence-of-weight as absence-of-signal. Default ON.
  | 'LL3_ZERO_WEIGHT_DOMAIN_DISCLAIMER_ENABLED'
  // β8 — Sliding-window history summarization. Default OFF; flip at γ exit gate.
  // When ON, conversations > 32k estimated tokens have their oldest turns compressed
  // via a Haiku call before being passed to synthesis. Env: MARSYS_FLAG_HISTORY_COMPRESSION_ENABLED.
  | 'HISTORY_COMPRESSION_ENABLED'
  // γ6 — Per-message cost visibility for non-admin users. Default false.
  // Super-admin always sees cost; this flag gates it for lower tiers.
  // Env: MARSYS_FLAG_COST_VISIBILITY_FOR_USERS.
  | 'COST_VISIBILITY_FOR_USERS'
  // Phase 5C — Dasha post-synthesis validator. Default false for safe rollout;
  // flip CHECKPOINT_DASHA_ENABLED=true after hand-test verifies DSH.V.NNN citations
  // resolve correctly in prod. FAIL_HARD default true once enabled — the whole
  // point is to halt hallucinations, not just log them.
  // Env: MARSYS_FLAG_CHECKPOINT_DASHA_ENABLED / MARSYS_FLAG_CHECKPOINT_DASHA_FAIL_HARD.
  | 'CHECKPOINT_DASHA_ENABLED'
  | 'CHECKPOINT_DASHA_FAIL_HARD'
  // Platform Modernization 4.build_trigger — kill-switch for the autonomous
  // chart-build trigger (POST /api/build/start + /api/build/task). Default
  // FALSE until the operator-side end-to-end smoke is green (Cloud Task
  // enqueue → Cloud Run Job execute → build_events rows → cockpit SSE).
  // Env: MARSYS_FLAG_BUILD_TRIGGER_ENABLED
  | 'BUILD_TRIGGER_ENABLED'
  // R8 — Capabilities Round flags (all default false; flip individually after smoke verification)
  // R8-S1: Conversation branches persistence (REST API + useBranches hydration).
  | 'R8_BRANCHES_ENABLED'
  // R8-S3: Full-text search via pg_trgm across conversation bodies.
  | 'R8_SEARCH_ENABLED'
  // R8-S4: Pin/archive/folders for conversation organisation.
  | 'R8_FOLDERS_ENABLED'
  // R8-S5: Live token count + context % in Composer.
  | 'R8_TOKENS_ENABLED'
  // R8-S6: Inline slash command menu.
  | 'R8_SLASH_ENABLED'
  // R8-S7: Vision pipeline via Gemini adapter (default false — changes LLM cost profile).
  | 'R8_VISION_ENABLED'
  // R8-S8: Conversation export (MD / JSON / PDF).
  | 'R8_EXPORT_ENABLED'
  // R9-S1: Projects abstraction. Gates sidebar grouping, /api/projects/** routes,
  // and synthesis prompt injection. Default false — production unaffected until
  // explicitly enabled. Env: MARSYS_FLAG_R9_PROJECTS.
  | 'R9_PROJECTS'
  // R9-S2: Semantic conversation search. Requires pgvector + embedding backfill.
  // Default false — flip after backfill job completes. Env: MARSYS_FLAG_R9_SEMANTIC_SEARCH.
  | 'R9_SEMANTIC_SEARCH'
  // R9-S3: Persona library. ModelStylePicker persona group + settings page.
  // Default true (additive, no risk). Env: MARSYS_FLAG_R9_PERSONAS.
  | 'R9_PERSONAS'
  // R9-S4: Inline tool-flow timeline in AssistantMessage. Admin-only.
  // Default false — flip for super_admin after smoke verification. Env: MARSYS_FLAG_R9_TOOL_FLOW.
  | 'R9_TOOL_FLOW'
  // R10-Y-S5: Stop-and-edit while streaming. Client-side NEXT_PUBLIC flag.
  // Default FALSE — high UX risk; opt-in by operator only.
  | 'R10_EDIT_WHILE_STREAMING'
  // R10-Y-S3: Smooth-stream V2 — word-aware flush gated for rollback safety.
  // Server-side only — no NEXT_PUBLIC prefix, no deploy.yml build-arg.
  | 'R10_SMOOTH_STREAM_V2'
  // R10-Y-S4: Reasoning step labels — ### Step: markers in synthesis prompt.
  // Server-side only — no NEXT_PUBLIC prefix, no deploy.yml build-arg.
  | 'R10_REASONING_STEPS'
  // R10-Y-S9: Single-retry on 5xx/timeout. Routes retry to next STACK_ROUTING stack.
  // Server-side only — no NEXT_PUBLIC prefix, no deploy.yml build-arg.
  // Default false — cost risk (retry doubles LLM cost); opt-in only.
  | 'R10_AUTO_RETRY'
  // MCPT v3.1.0 — MCP v3.1 pure-MCP server. Default true (foundation sealed 2026-05-22).
  // Gates the v3.1 tool surface (21 tools, holistic_bundle, multi_school_bundle,
  // tier-conditioned house-rules, perf system, operator dashboard) vs the v1 path.
  // Env: MARSYS_FLAG_MCP_V3_ENABLED (server-side only — sidecar-scoped flag).
  | 'MCP_V3_ENABLED'
  // Retrieval Plane Elevation, plan R-1 item 3 ("single bootstrap", W2b lane).
  // When true, /api/retrieval/capability/route.ts's ensureBootstrapped() stops
  // maintaining its own separate per-wave registration list and instead imports
  // its registration list EXCLUSIVELY from registry/catalog.ts's getCatalog()
  // (the same production consumption surface both MCP Layer-2 primitives and
  // the chat channel already import). Default FALSE in every environment —
  // flipping it on is a separate, future, explicitly-authorized breaking-release
  // deploy, not part of this lane. When false, route.ts's dispatch behavior is
  // byte-for-byte identical to its pre-flag behavior.
  // Env: MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED.
  | 'RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED'

export const DEFAULT_FLAGS: Record<FeatureFlag, boolean> = {
  PANEL_MODE_ENABLED: true,
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
  // M5-B LL.3 R.LL3.3 — Zero-LL.1-weight domain disclaimer. Default ON.
  // Override via MARSYS_FLAG_LL3_ZERO_WEIGHT_DOMAIN_DISCLAIMER_ENABLED=false.
  LL3_ZERO_WEIGHT_DOMAIN_DISCLAIMER_ENABLED: true,
  // β8 — Sliding-window history summarization. Default false until γ exit gate.
  HISTORY_COMPRESSION_ENABLED: true,
  // γ6 — Cost visibility for non-admin users. Default false.
  COST_VISIBILITY_FOR_USERS: false,
  // Phase 5C — Dasha validator. Default false (safe rollout).
  // Flip CHECKPOINT_DASHA_ENABLED=true after prod hand-test.
  // FAIL_HARD default true — once enabled, halt on violations.
  CHECKPOINT_DASHA_ENABLED: false,
  CHECKPOINT_DASHA_FAIL_HARD: true,
  // Platform Modernization 4.build_trigger — kill-switch default OFF until
  // end-to-end smoke is green. Flip via MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true.
  BUILD_TRIGGER_ENABLED: false,
  // R8 Capabilities Round — all default false; flip individually after smoke.
  R8_BRANCHES_ENABLED: false,
  R8_SEARCH_ENABLED: false,
  R8_FOLDERS_ENABLED: false,
  R8_TOKENS_ENABLED: false,
  R8_SLASH_ENABLED: false,
  R8_VISION_ENABLED: false,
  R8_EXPORT_ENABLED: false,
  // R9 flags — all default false/true as per master plan
  R9_PROJECTS: false,
  R9_SEMANTIC_SEARCH: false,
  R9_PERSONAS: true,
  R9_TOOL_FLOW: false,
  // R10-Y-S5: default false — high UX risk; opt-in only.
  R10_EDIT_WHILE_STREAMING: false,
  // R10-Y-S3: default true — word-aware chunking already active; gated for rollback.
  R10_SMOOTH_STREAM_V2: true,
  // R10-Y-S4: default true — additive step labels, no cost impact.
  R10_REASONING_STEPS: true,
  // R10-Y-S9: default false — cost risk; opt-in only.
  R10_AUTO_RETRY: false,
  // MCPT v3.1.0 — MCP v3.1 pure-MCP server. Default true — foundation sealed 2026-05-22.
  // Override via MARSYS_FLAG_MCP_V3_ENABLED=false to revert to v1 path (emergency only).
  MCP_V3_ENABLED: true,
  // Retrieval Plane Elevation R-1 item 3 — single bootstrap. Default FALSE:
  // route.ts keeps its own hand-maintained registration list until a future,
  // separately-authorized breaking-release deploy flips this on.
  // Override via MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED=true.
  RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED: false,
}

// Numeric config keys (read via configService.getValue)
export const CGM_GRAPH_WALK_MAX_DEPTH_KEY = 'CGM_GRAPH_WALK_MAX_DEPTH'
export const VECTOR_SEARCH_TOP_K_KEY = 'VECTOR_SEARCH_TOP_K'
export const CGM_GRAPH_WALK_MAX_DEPTH_DEFAULT = 3
export const VECTOR_SEARCH_TOP_K_DEFAULT = 20

export const FLAG_ENV_PREFIX = 'MARSYS_FLAG_'
