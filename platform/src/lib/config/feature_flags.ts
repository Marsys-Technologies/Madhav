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
  // the chat channel already import). PAUSED at default FALSE (2026-07-21,
  // W5 conductor, per native ruling): the D-5 quiet gate was met (STATE_D-5.md
  // lifecycle_step 8) and the GT-40 divergence re-verified zero (beyond the one
  // deliberate reverse item, synth_compose_large_n — see
  // single_bootstrap_flag.test.ts's mechanical flag=false-vs-flag=true URI
  // diff), so this flip is code-complete and fully tested — but D-4b (an
  // unrelated concurrent campaign) is still actively executing its own live
  // agent swarm against the deployed connector, and master brief §I.6 forbids
  // any breaking rename/bootstrap-source change from deploying while another
  // campaign's agents may be calling legacy names on it. This is the SAME flip
  // 707fb5a9 shipped and then paused, not a fresh decision — see
  // STATE.md's "W5 — breaking-release split" entry and impl/w5-breaking
  // (holds the flip-forward, ready to reapply the moment D-4b confirms quiet).
  // Set MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED=true in env to force the
  // new single-bootstrap path early (verification/staging use only, per this
  // note — not a production override without the D-4b-quiet check).
  // Env: MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED.
  | 'RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED'
  // PB-1 DHĀRĀ — Paripraśna. Gates the new adaptive conversation surface:
  // the `/clients/[id]/pariprashna` page (redirects to `consult` when off)
  // and the `/api/pariprashna` route (returns a 404 disabled-feature error
  // when off). Default OFF — new unreleased surface; rollback for the whole
  // PB-1 wave IS this flag (route ships dark, flipped on deliberately post-
  // deploy). Env: MARSYS_FLAG_PARIPRASHNA_ENABLED.
  | 'PARIPRASHNA_ENABLED'
  // P1 G1-D "Limits" — NCD-8 per-user rate limits + pre-dispatch spend ceilings
  // ($2/turn, $40/day) on BOTH serving doors (the web `/api/pariprashna` door and
  // the MCP `/api/mcp/prashna_ask` door), plus the request proxy's per-user RPM
  // gate. Default OFF — this lane ships dark per the P1 pre-authorization
  // ("features ship flag-OFF; the safety gate flips ON at close"), so merging it
  // cannot change production behaviour until the flip is deliberate. When OFF,
  // every gate short-circuits to "allowed" before any DB or pricing work runs.
  // Env: MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED.
  | 'PARIPRASHNA_LIMITS_ENABLED'
  // P1 FOUNDATION lane G1-B — subject consent (NCD-9, PPR-14, abuse case A9).
  // Gates the WHOLE `src/lib/pariprashna/consent` surface:
  //   · OFF (default) — `resolveSubjectConsent` returns allow/enforcement_disabled
  //     BEFORE any DB access, so the serving path is byte-for-byte what it is
  //     today; every mutating entry point (withdrawal sweep, dispute open,
  //     subject export) throws ConsentFeatureDisabledError instead of running.
  //   · ON — no L2+ interpretive output for a chart whose subject lacks a
  //     consent row; `native_self` is strictly checked (subject IS the account
  //     holder, not self-certified); under-18 subjects serve only to the
  //     recorded guardian and never as a cohort; refusals land in the
  //     excluded-subject register.
  // Flip this ON only after consent rows exist for the charts in play —
  // flipping it on an empty `chart_subject_consent` table refuses EVERY chart
  // by design (that is the fail-closed direction, but it is a real outage).
  // Env: MARSYS_FLAG_SUBJECT_CONSENT_ENFORCEMENT.
  | 'SUBJECT_CONSENT_ENFORCEMENT'
  // P1 FOUNDATION lane G1-C — NO-LEAKAGE arm-1 (NCD-5, PPR-21/PPR-22).
  // Gates the SERVING-SIDE half of the role/RLS work:
  //   · OFF (default) — `getServeReadPool()` returns the one existing shared pool
  //     and `withChartContext()` sets no GUC, so every read path is byte-for-byte
  //     what it is today. Migration 576's roles hold grants but have no members,
  //     and its RLS policies are stored but not enabled, so the DB half is inert
  //     too. Nothing in this lane is live until BOTH this flag flips AND an
  //     operator runs `platform/scripts/pariprashna/g1c_arm_rls.sql`.
  //   · ON — reads route through a `role_web_serve`-backed pool built from
  //     SERVE_DATABASE_URL (or DB_SERVE_USER/DB_SERVE_PASSWORD), and
  //     `withChartContext()` pins `app.chart_context` per transaction so the RLS
  //     policies have a value to compare against. If those credentials are NOT
  //     configured, `getServeReadPool()` THROWS rather than quietly falling back
  //     to the legacy credential — a flag that claims role separation while
  //     serving on `amjis_app` would be exactly the §N.8 defect class this lane
  //     exists to close.
  // Flipping this ON is a live traffic-affecting cutover. It is deliberately NOT
  // paired with any credential rotation; see the cutover runbook
  // 00_ARCHITECTURE/briefs/pariprashna_swarm/G1_C_ROLES_RLS_CUTOVER_RUNBOOK_v1_0.md.
  // Env: MARSYS_FLAG_PARIPRASHNA_ROLE_SEPARATION.
  | 'PARIPRASHNA_ROLE_SEPARATION'
  // P1 FOUNDATION lane G1-C — NO-LEAKAGE arm-3 (PPR-31 arm 3).
  // Gates the out-of-process ledger writer.
  //   · OFF (default) — the SAMĪKṢĀ capture path INSERTs into
  //     `brahma_mimamsa_prediction_ledger` in-process, exactly as it does today.
  //   · ON — the serving process enqueues a write INTENT into
  //     `pariprashna_ledger_outbox` (the only ledger-adjacent privilege
  //     `role_web_serve` keeps) and the out-of-process worker
  //     (`platform/scripts/pariprashna/ledger_writer_worker.ts`), the sole holder
  //     of `role_ledger_write`, drains it and performs the real write.
  // This flag MUST be flipped ON *before* PARIPRASHNA_ROLE_SEPARATION, not after:
  // once the app serves on `role_web_serve` it has no ledger INSERT at all, so an
  // in-process capture would start failing. The runbook sequences them.
  // Env: MARSYS_FLAG_PARIPRASHNA_LEDGER_OUT_OF_PROCESS.
  | 'PARIPRASHNA_LEDGER_OUT_OF_PROCESS'
  // P1 FOUNDATION lane G1-A — the SafetyPolicyGate (PPR-12, MP §3.5.C hard
  // stops HS-1..HS-6). Gates the WHOLE `src/lib/pariprashna/safety` surface:
  //   · OFF (default) — `classifyTurnSafety` returns enforced:false / proceed
  //     BEFORE running a single pattern and before touching the database; the
  //     plan, prompt, and pre-wire controls are all no-ops; every governance
  //     entry point (retraction, sample review) throws instead of running.
  //   · ON — every query is classified before planning; suicide-adjacent
  //     queries get a fixed response and NO plan; date-of-death is blocked at
  //     plan-time, synthesis-time and pre-wire; health-crisis / mental-health /
  //     mortality-window readings do not leave the session without two
  //     independent adversarial passes AND a separate sign-off (NCD-4's
  //     interstitial is the one relaxation, and only for a PROVEN native_self
  //     subject on an HS-3 class).
  // Operational note, because the coupling is real and fails CLOSED: NCD-4's
  // interstitial requires a proven `native_self` subject_kind, which only
  // exists when SUBJECT_CONSENT_ENFORCEMENT is also ON. Flipping this flag
  // alone sends every health question on every chart down the full seal path —
  // correct, and a large behavioural change. Flip the pair together.
  // Env: MARSYS_FLAG_PARIPRASHNA_SAFETY_GATE_ENABLED.
  | 'PARIPRASHNA_SAFETY_GATE_ENABLED'
  // P1 FOUNDATION lane G1-G — prompt-injection containment (PPR-13, TA §14A.1).
  // Gates the WHOLE `src/lib/pariprashna/injection` surface, four controls:
  //   · OFF (default) — the question, the conversation history, the retrieved
  //     evidence and every agentic tool result reach the model exactly as they
  //     do today; the plan is not re-closed; no tool-sequence monitor is built;
  //     the answer-side entitlement scan contributes no rules to the pre-wire
  //     pass. Byte-for-byte no change.
  //   · ON — untrusted content is wrapped in `<untrusted_*>` containers whose
  //     own delimiters are neutralized inside the payload, with a system-side
  //     data-not-instruction clause; planner-supplied identity params
  //     (chart_id and friends) carrying anything other than the AUTHENTICATED
  //     chart are rejected from tool calls; a tool sequence that diverges from
  //     the authorized plan is TRACE-FLAGGED (never blocked — TA §14A.1 rules
  //     that explicitly); and any sentence naming a chart outside the caller's
  //     entitlements is redacted before the wire.
  // Independent of PARIPRASHNA_SAFETY_GATE_ENABLED on purpose: the two share
  // the pre-wire pass but arm different pattern classes, and
  // `scanMortalityPhrasing`'s `mortalityRulesEnabled` option is what keeps
  // flipping one from silently arming the other.
  // Env: MARSYS_FLAG_PARIPRASHNA_INJECTION_CONTAINMENT.
  | 'PARIPRASHNA_INJECTION_CONTAINMENT'
  // P2-A G2-A — Semantic blocks on the wire (PPR-07, FD-1). Gates the WHOLE
  // `src/lib/pariprashna/semantics` surface plus the new `prediction_card`
  // wire event:
  //   · OFF (default) — `block.commit` carries only `{ block_id, text }`
  //     exactly as before (no `kind`/`role`/`content`/`table`/`gap_text`),
  //     no commit-time classification runs, and no `prediction_card` event is
  //     ever emitted. Byte-for-byte no change to the existing wire or to what
  //     the client renders (the s1 live adapter's `block.commit` case
  //     defaults `kind` to `'paragraph'` when the field is absent, same as
  //     today).
  //   · ON — every committed PROSE block is classified deterministically from
  //     its own committed text (table / verse / gap_ribbon / heading /
  //     paragraph, plus a verdict/elaboration/caveat role for paragraphs) and
  //     the classification rides on that block's `block.commit` event; the
  //     client's already-built `TableBlock`/`VerseBlock`/`GapRibbonBlock`
  //     renderers activate on the live route instead of only in fixtures. A
  //     detected, persisted prediction candidate is also surfaced as a
  //     first-class `prediction_card` event carrying the structured
  //     candidate + its real `message_parts.id`, which mounts the in-stream
  //     `LogToSamiksha` confirm affordance (built and unmounted since PB-3).
  // Env: MARSYS_FLAG_PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED.
  | 'PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED'
  // P2-C — Honest controls (PPR-09/16). Gates two additive, together-shipped
  // behaviors that were previously either inert or misleading:
  //   · `length_tier` (TODO(PB-4) in safety_gate.ts) gains a REAL effect —
  //     `synthesis_stage.assembleSynthesisContext` appends a short, fixed
  //     length-discipline instruction to the system prompt for `brief`/
  //     `exhaustive` (never for `standard`, which stays a byte-identical
  //     no-op whether or not the flag is on).
  //   · `plan_stage.ts` emits an HONEST `reading_depth_received` grade
  //     derived from the PLANNER's own `plan.scope_tuple.depth` (the real
  //     signal of how deep the turn actually went), not from whatever the
  //     composer's mode/pill claimed before planning ran. The client
  //     surfaces it as a disclosure distinct from the requested tier.
  // `model_id` needed no backend flag — `bindTurnParams` already binds it
  // directly to the synthesis model (verified live end-to-end); the defect
  // there was UI-only (the composer's model picker never sent its selection
  // and offered labels with no matching registry id), fixed by wiring the
  // real picker through, unconditionally, with no serving-path behavior
  // change to gate.
  // Default false: ships dark. Flip via
  // MARSYS_FLAG_PARIPRASHNA_HONEST_CONTROLS_ENABLED=true.
  | 'PARIPRASHNA_HONEST_CONTROLS_ENABLED'
  // P2-B G2-B "Citations at first paint" (PPR-08, FD-2/FD-6). Gates wiring
  // the already-built S-3 rewriter (`lib/pariprashna/citations/rewriter.ts`)
  // into the live synthesis stream:
  //   · OFF (default) — the synthesis stream runs exactly as it does today:
  //     each delta goes through the bare `lintReaderProse` register-leak
  //     scrub with no resolver, citation sentinels are redacted like any
  //     other internal-id-shaped token, no `citation.define` event fires
  //     during streaming, and persistence still re-derives citations by
  //     regex-scanning the accumulated text (the pre-existing P0C-R5 dead
  //     path — unchanged, not newly introduced, when this flag is off).
  //     `turn.commit` carries no `grounding_summary` field.
  //   · ON — a `TurnCitationStream` (per turn) resolves sentinels against
  //     this turn's own retrieved evidence, emits `⟦n⟧`-style inline markers
  //     + `citation.define`/`flag` wire events DURING streaming (not just at
  //     final commit), persistence builds canonical citation parts from the
  //     turn's own resolution ledger instead of re-scanning scrubbed prose,
  //     and `turn.commit` carries a server-derived `grounding_summary`
  //     (counts, grade rollup, completeness line) that the client prefers
  //     over its own citation-tally estimate.
  // Env: MARSYS_FLAG_PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED.
  | 'PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED'

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
  // Retrieval Plane Elevation R-1 item 3 — single bootstrap. FLIPPED to TRUE
  // (RC-14, 2026-07-23) — the D-4b doctrine campaign closed (commit cd5ad175
  // "docs(d4b): CAMPAIGN CLOSE"), unblocking the w5-breaking release per master
  // brief §I.6 / RC-14. This route now routes registration EXCLUSIVELY through
  // registry/catalog.ts's getCatalog() — the same production consumption surface
  // the MCP Layer-2 primitives route and the chat channel already import — which
  // is a strict superset of the legacy hand-maintained per-wave list (the only
  // catalog-only additions are the deliberately-reviewed reverse-gap set:
  // marsys://tool/L-SPINE/query_spine_bundle + marsys://tool/synthesis/
  // compose_large_n). Set MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED=false
  // to force the legacy hand-maintained path (emergency rollback only).
  RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED: true,
  // PB-1 DHĀRĀ — Paripraśna. Default false — new unreleased surface; flip
  // via MARSYS_FLAG_PARIPRASHNA_ENABLED=true once the native is ready to
  // exercise the deployed route.
  PARIPRASHNA_ENABLED: false,
  // P1 G1-D — NCD-8 limits. Default false: ships dark, flipped deliberately.
  // Flip via MARSYS_FLAG_PARIPRASHNA_LIMITS_ENABLED=true.
  PARIPRASHNA_LIMITS_ENABLED: false,
  // P1 G1-B — subject consent enforcement. Default false: this lane ships
  // flag-OFF per the P1 pre-authorization note, so merging it changes no
  // production behavior. Flip via MARSYS_FLAG_SUBJECT_CONSENT_ENFORCEMENT=true
  // only after `chart_subject_consent` carries a row for every live chart.
  SUBJECT_CONSENT_ENFORCEMENT: false,
  // P1 G1-C — NO-LEAKAGE arm-1 role separation. Default false: ships dark. The
  // flip is a live cutover of what credential the app serves on; it is gated on
  // the runbook's pre-flight, not on this file.
  // Flip via MARSYS_FLAG_PARIPRASHNA_ROLE_SEPARATION=true.
  PARIPRASHNA_ROLE_SEPARATION: false,
  // P1 G1-C — NO-LEAKAGE arm-3 out-of-process ledger writer. Default false: the
  // in-process capture path is unchanged. Flip via
  // MARSYS_FLAG_PARIPRASHNA_LEDGER_OUT_OF_PROCESS=true, BEFORE role separation.
  PARIPRASHNA_LEDGER_OUT_OF_PROCESS: false,
  // P1 G1-A — the SafetyPolicyGate. Default false: this lane ships flag-OFF per
  // the P1 pre-authorization note, so merging it changes no production
  // behavior. Flip via MARSYS_FLAG_PARIPRASHNA_SAFETY_GATE_ENABLED=true,
  // together with SUBJECT_CONSENT_ENFORCEMENT (see the declaration comment —
  // NCD-4's interstitial cannot be earned without a proven subject_kind).
  PARIPRASHNA_SAFETY_GATE_ENABLED: false,
  // P1 G1-G — prompt-injection containment. Default false: this lane ships
  // flag-OFF per the P1 pre-authorization note, so merging it changes no
  // production behavior. Two of its four controls change what the synthesis
  // model reads (structural delimiters + the containment clause), which can
  // move prose — flip it deliberately, with a reading compared before/after.
  // Flip via MARSYS_FLAG_PARIPRASHNA_INJECTION_CONTAINMENT=true.
  PARIPRASHNA_INJECTION_CONTAINMENT: false,
  // P2-A G2-A — Semantic blocks on the wire. Default false: ships dark, no
  // behavior change on merge. Flip via
  // MARSYS_FLAG_PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED=true once the client
  // renderers have been verified against a real deployed reading.
  PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED: false,
  // P2-C — honest length shaping + scope-tuple-derived depth disclosure.
  // Default false: ships dark. Flip via
  // MARSYS_FLAG_PARIPRASHNA_HONEST_CONTROLS_ENABLED=true.
  PARIPRASHNA_HONEST_CONTROLS_ENABLED: false,
  // P2-B G2-B — citations at first paint. Default false: ships flag-OFF, the
  // synthesis stream is byte-for-byte what it is today (see the declaration
  // comment). Flip via MARSYS_FLAG_PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED=true.
  PARIPRASHNA_FIRST_PAINT_CITATIONS_ENABLED: false,
}

// Numeric config keys (read via configService.getValue)
export const CGM_GRAPH_WALK_MAX_DEPTH_KEY = 'CGM_GRAPH_WALK_MAX_DEPTH'
export const VECTOR_SEARCH_TOP_K_KEY = 'VECTOR_SEARCH_TOP_K'
export const CGM_GRAPH_WALK_MAX_DEPTH_DEFAULT = 3
export const VECTOR_SEARCH_TOP_K_DEFAULT = 20

export const FLAG_ENV_PREFIX = 'MARSYS_FLAG_'
