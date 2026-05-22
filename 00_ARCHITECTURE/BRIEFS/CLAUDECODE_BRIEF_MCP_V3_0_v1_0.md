---
artifact: CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md
status: ACTIVE
version: 1.0
authored_by: Claude (Cowork session, Opus 4.7)
authored_on: 2026-05-22
parent_architecture: 00_ARCHITECTURE/MCP_ARCH_v3_PROPOSAL_2026-05-22.md (v3.1)
parent_perf_brief: 00_ARCHITECTURE/MCP_PERF_SYSTEM_BRIEF_2026-05-22.md (v3.1)
parent_diagnosis: 00_ARCHITECTURE/MCP_DIAGNOSIS_2026-05-22.md
parent_handoff: 00_ARCHITECTURE/MCP_OPUS_REVIEW_PACKAGE_2026-05-22.md
audience: Claude Code (the implementing model)
disposition: governing scope for the MCP v3.1.0 foundation execution session(s) — Sub-phase v3.1.0-S1 through v3.1.0-S6
status_check_rule: |
  If this file exists at 00_ARCHITECTURE/BRIEFS/ and its status is not COMPLETE,
  Claude Code sessions read it before items 1–11 of CLAUDE.md §C per the governance
  protocol. Its `may_touch` / `must_not_touch` declarations override all other scope
  guidance for the duration of the session. When all acceptance criteria across all
  six sub-phases are met, the closing session sets status: COMPLETE in this file's
  frontmatter and authors MCP_V3_1_0_CLOSE.md as the sealing artifact.
---

# CLAUDECODE_BRIEF — MCP v3.1.0 Foundation

This brief executes the foundation phase of MARSYS-JIS MCP v3.1 — the pure-MCP architecture regeneration. The full architectural rationale lives in `MCP_ARCH_v3_PROPOSAL_2026-05-22.md` v3.1; the full perf-system rationale lives in `MCP_PERF_SYSTEM_BRIEF_2026-05-22.md` v3.1; the empirical v1 diagnosis lives in `MCP_DIAGNOSIS_2026-05-22.md`. The Cowork conversation that produced these docs is captured end-to-end in `MCP_OPUS_REVIEW_PACKAGE_2026-05-22.md`.

**Read all four parent documents before any substantive work.** The architecture decisions ARE the contract. This brief is the executable surface — what to build, where, in what order, with what acceptance criteria.

---

## §1 — Phase scope

v3.1.0 (foundation) is six sub-phases. Each sub-phase is a closed-artifact session per `CLAUDE.md §M` cadence, producing a versioned frontmatter-bearing artifact and a SESSION_LOG append.

| Sub-phase | Subject | Estimated effort | Blocks |
|---|---|---|---|
| v3.1.0-S1 | Code-level fixes (F.1–F.5, F.7) | 1 session | S2 |
| v3.1.0-S2 | Tier 2 bundles + SSE streaming | 1 session | S3 |
| v3.1.0-S3 | Resources (5) + tool description regeneration | 1 session | S5, S6 |
| v3.1.0-S4 | Perf system + audit subsystem (P0–P4) | 1 session | S5 |
| v3.1.0-S5 | Operator dashboard at `/admin/mcp/health` (P5) | 1 session | S6 |
| v3.1.0-S6 | Tier-conditioned `house-rules` + v3.1.0 sealing | 1 session | (closes) |

Total estimated: **6 sessions**.

**Concurrent worktree.** Per CLAUDE.md §E concurrent-workstream precedent (Phase O / Chat V2 R6-R10 / Phase 4C). Recommend a `feature/mcp-v3` branch with its own worktree (e.g. `/Users/Dev/Vibe-Coding/Apps/MadhavMCP/`). All six sub-phases execute on this branch. Final sealing merge to main happens at v3.1.0-S6 close.

**Feature flag.** `MARSYS_FLAG_MCP_V3_ENABLED`. Default false at first commit; gates the tool-list swap and route dispatcher. Flipped true at v3.1.0-S6 sealing after smoke. v1's `/api/mcp/execute` route remains live while the flag is false; both tool surfaces coexist during the migration. After v3.1.0-S6 ships and runs cleanly for 7 days, v3.1.0-S7 (out of this brief's scope) deletes the v1 dispatcher and the flag per the §M.16 flagless-precedent pattern.

---

## §2 — Hard constraints (must_not violations)

- **No server-side LLM call may be added on any v3 MCP path.** No planner, no synthesis, no LLM-based audit pass. This is the spine of v3.1; any code change that introduces an LLM call on the MCP dispatcher fails the brief.
- **No `ask_madhav` / `plan_query` / `execute_plan` tool may be registered on the v3 path.** These are deleted at v3.1.0-S2 close.
- **No silent overwrite of `marsys_methodology_block` in the synthesis prompt.** F.6 (removing the postlude) is RECOMMENDED for the `/consume` path but **out of scope for this brief.** Do not touch `platform/src/lib/prompts/templates/shared.ts` in any v3.1.0 sub-phase. File a separate `CONSUME_POSTLUDE_REMOVAL_v1_0.md` brief if/when the native authorizes it.
- **No change to retrieval tool behavior beyond honoring `params` over `plan`.** F.2 (audit + fix smuggling) is in scope for behavior parity, not for behavior change. Each Tier 1 primitive should produce *the same results* when called with the same effective filters, before vs after the fix.
- **No deletion of v1 `/api/mcp/execute`** until v3.1.0-S6 sealing and the 7-day grace period afterward. The v1 path stays live during the migration.
- **Tier filtering at the retrieval layer affects instrument-meta only.** Per arch §6. Code-reading a tier filter that hides chart data (virupas, sahams, etc.) from any non-super-admin tier is a brief violation; the work must be redone.
- **Audit subsystem uses heuristics only, no LLM.** Per perf brief §5.2.
- **`mcp_predictions` / `mcp_prediction_outcomes` / `mcp_audit_findings` tables are append-only** in v3.1.0; no DELETE statements anywhere in the audit job or the dashboard's resolve actions. Resolve actions UPDATE `resolved_at` / `resolved_by` / `resolution_note` columns only.

---

## §3 — Scope declarations

### `may_touch`

```
platform/src/app/api/mcp/**
platform/src/lib/mcp/**
platform/src/lib/retrieve/vector_search.ts
platform/src/lib/retrieve/msr_sql.ts
platform/src/lib/retrieve/chart_facts_query.ts
platform/src/lib/retrieve/*.ts                        # only for the params-vs-plan smuggling audit (F.2)
platform/src/lib/pipeline/budget_arbiter.ts           # only to remove the MCP-path call site (F.7)
platform/src/app/admin/mcp/health/**                  # new dashboard
platform-mcp/src/server.ts
platform-mcp/src/auth.ts
platform-mcp/src/tools/**
platform-mcp/src/resources/**
platform-mcp/src/bundles/**                            # new
platform-mcp/src/jobs/audit_nightly.ts                 # new (or platform/jobs/, choose during S4 design)
platform-mcp/cloudbuild.yaml
platform/supabase/migrations/                          # new migrations 072–076
00_ARCHITECTURE/MCP_*_2026-05-22.md                    # status flips only (DRAFT → CURRENT at close)
00_ARCHITECTURE/SESSION_LOG.md                         # appends only
00_ARCHITECTURE/CURRENT_STATE_v1_0.md                  # state pointer updates
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md  # this file (status flip only at close)
00_ARCHITECTURE/CAPABILITY_MANIFEST.json               # new artifacts added at sealing
00_ARCHITECTURE/MCP_V3_1_0_CLOSE.md                    # new at S6 close
00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql  # new seed file
.geminirules                                           # mirror surface (MP.1) — touched at close if any governance changes
.gemini/project_state.md                               # mirror surface (MP.2) — touched at close
```

### `must_not_touch`

```
01_FACTS_LAYER/**                                      # no FORENSIC/LEL changes in v3.1.0 (data backfill is v3.2+)
025_HOLISTIC_SYNTHESIS/**                              # no MSR/UCN/CGM/CDLM/RM changes in v3.1.0
platform/src/lib/prompts/templates/shared.ts          # F.6 is out of scope — do not touch
platform/src/app/consume/**                            # web /consume chat is untouched
platform/src/app/api/chat/**                           # web chat API is untouched
06_LEARNING_LAYER/**                                   # no learning-layer changes
05_TEMPORAL_ENGINES/**
03_DERIVATIONS/**
04_REMEDIAL_CODEX/**
08_CLASSICAL_CROSS_REFERENCE/**                        # classical-text indexing is v3.2-S1+
09_MULTI_SCHOOL_TRIANGULATION/**                       # multi-school backfill is v3.2-S4+
00_ARCHITECTURE/MACRO_PLAN_v2_0.md                     # no macro plan changes
00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md           # no architecture-doc changes
00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md  # no governance protocol changes
00_ARCHITECTURE/CONDUCTOR/**                           # Conductor workstream — separate scope
00_ARCHITECTURE/chat_v2_briefs/**                      # Chat V2 — separate workstream
00_ARCHITECTURE/BRIEFS/**                              # other briefs — only this one is in scope
```

### `red_team_due`

Yes — per `MCP_ARCH_v3_PROPOSAL §12` and `CLAUDE.md §M`, a fresh red-team is required for v3 (threat model shifts per arch §11). The red-team runs as v3.4-S2 (outside v3.1.0 scope) but must be scheduled at v3.1.0-S6 close.

---

## §4 — Per-sub-phase acceptance criteria

### v3.1.0-S1 — Code-level fixes

Implement F.1–F.5 + F.7 from arch §10. F.6 explicitly out of scope (see §2 above).

**Files touched (expected):**
- `platform/src/lib/retrieve/vector_search.ts` (F.1)
- `platform/src/lib/retrieve/msr_sql.ts` (F.2, primary)
- All `platform/src/lib/retrieve/*.ts` (F.2 audit pass)
- `platform-mcp/src/tools/query_chart_facts.ts` (F.3)
- `platform-mcp/src/tools/*.ts` (F.3 generalized — descriptions generated from enum/registry)
- `platform-mcp/cloudbuild.yaml` (F.4)
- `platform-mcp/src/auth.ts` (F.5)
- `platform/src/app/api/mcp/primitives/[tool]/route.ts` (F.7 — remove `arbitrateBudgets` call site for MCP path)

**Acceptance:**
- **AC.S1.1** — `vector_search({text:"saturn shadbala", top_k:5})` called via MCP returns chunks whose content references Saturn and/or shadbala (Jaccard similarity of returned chunk text against the query ≥ 0.20). Verified by integration test at `platform-mcp/test/vector_search.integration.test.ts`.
- **AC.S1.2** — `query_signals({domain:"career", limit:3})` called via MCP returns exactly 3 rows, all with at least one domain matching "career". Verified by integration test.
- **AC.S1.3** — Every Tier 1 primitive's integration test passes with `params`-supplied filters honored. New tests added per primitive at `platform-mcp/test/primitives/*.integration.test.ts`. At least one test per primitive verifying a non-default filter param produces a different result set than no filter.
- **AC.S1.4** — `query_chart_facts` description, as returned by MCP `tools/list`, lists only categories present in the `ChartFactsCategory` enum at `platform/src/lib/retrieve/chart_facts_query.ts:21–30`. No `dignity`, `nakshatra`, `house_placement`, `divisional_D9`. Verified by `platform-mcp/test/tool_descriptions.test.ts`.
- **AC.S1.5** — `MCP_INTERNAL_TOKEN` is bound from Secret Manager in `cloudbuild.yaml`. A clean redeploy via `gcloud builds submit` produces a working MCP service without manual env-var setting. Verified by deploy + curl integration smoke against the new revision.
- **AC.S1.6** — Bearer-key validation cache hit rate after 100 sequential calls with the same key > 0.95. Cache TTL 60s, in-memory `Map`. Verified by unit test.
- **AC.S1.7** — `arbitrateBudgets` is NOT invoked on any code path that originates at `/api/mcp/primitives/*` or `/api/mcp/bundles/*`. Verified by static analysis (grep) + integration test (call a primitive with `--inspect-trace`, confirm `budget_arbiter` does not appear in trace steps).
- **AC.S1.8** — No regression on `/consume` chat. Existing integration tests for `/api/chat` and `/consume` pass unchanged.

**Sealing artifact:** `00_ARCHITECTURE/MCP_V3_1_0_S1_CLOSE.md`. Frontmatter status `CLOSED`. Body documents which `plan.*`-vs-`params.*` audits were performed and what was found per primitive.

### v3.1.0-S2 — Tier 2 bundles + SSE streaming

**Files touched (expected):**
- `platform-mcp/src/bundles/holistic_bundle.ts` (new)
- `platform-mcp/src/bundles/multi_school_bundle.ts` (new)
- `platform/src/app/api/mcp/bundles/[name]/route.ts` (new — SSE handler)
- `platform-mcp/src/server.ts` (register bundles in tool list)
- `platform-mcp/src/bundles/index.ts` (composition rules, sub-tool fan-out)
- Migration `platform/supabase/migrations/072_mcp_bundle_cache.sql` (5-min cache table)
- `platform-mcp/test/bundles/*.test.ts` (new tests)

**Acceptance:**
- **AC.S2.1** — `holistic_bundle({query_text:"which is my strongest planet?"})` returns a `bundle.completed` SSE event within 20s end-to-end with ≥6 `bundle_entries[]` (MSR + CGM + chart_facts(strength) + UCN + RM + LEL minimum). Verified by integration test against deployed MCP.
- **AC.S2.2** — When a sub-tool fails inside a bundle, the bundle returns a successful envelope with `bundle_entries[].errored: true` for the failing sub-tool and full results for the rest. Verified by test: mock a sub-tool to throw, confirm bundle returns 200 with partial envelope.
- **AC.S2.3** — SSE events stream progressively. Test: subscribe to bundle SSE, confirm `bundle.sub_tool.completed` events arrive before `bundle.completed`, and the time between first sub-tool event and last is non-zero (i.e., not all sub-tools complete in the same millisecond).
- **AC.S2.4** — Bundle response cache: calling `holistic_bundle({query_text:"X"})` twice in 5 minutes results in the second call returning `served_from_cache: true` in the envelope. Cache invalidates after 5 minutes.
- **AC.S2.5** — `holistic_bundle({query_text:"X", subset:["MSR","CGM"]})` returns only those two sub-tool entries, not the full fan-out.
- **AC.S2.6** — `multi_school_bundle({claim:"Saturn in 10th delays career"})` returns per-school entries for all four schools (where the school has any data; otherwise an empty per-school block flagged with the coverage caveat).
- **AC.S2.7** — Bundle envelope's top-level `provenance.signal_ids_available[]` equals the union of all successful sub-tools' `signal_ids_available[]`. Verified by test.
- **AC.S2.8** — Tier-gating works: client-tier key calling `holistic_bundle` succeeds; client-tier key calling `flag_disagreement` (a super_admin write tool) returns 403.

**Sealing artifact:** `00_ARCHITECTURE/MCP_V3_1_0_S2_CLOSE.md`. Documents the bundle composition rules implemented per sub-tool with the rationale for inclusion.

### v3.1.0-S3 — Resources + tool description regeneration

**Files touched (expected):**
- `platform-mcp/src/resources/chart_snapshot.ts` (new)
- `platform-mcp/src/resources/chart_overview.ts` (rewrite — tier-conditioned)
- `platform-mcp/src/resources/house_rules.ts` (new — tier-conditioned content)
- `platform-mcp/src/resources/capabilities.ts` (new — generated from perf views; placeholder if S4 perf views not yet present, real impl in S4)
- `platform-mcp/src/resources/school_conventions.ts` (new — static content)
- `platform-mcp/src/resources/index.ts` (register all 5)
- `platform-mcp/src/tools/*.ts` (all tool descriptions regenerated from enum/registry sources)
- `platform-mcp/test/resources/*.test.ts`

**Acceptance:**
- **AC.S3.1** — All 5 resources auto-load at session attach. Verified by `tools/list` returning the resources in its response and by integration test using the `claude-mcp-test-client` (or equivalent) to attach and read each resource.
- **AC.S3.2** — Resource sizes at super_admin tier: chart-snapshot ~2.5k tokens, chart-overview ~3k, house-rules ~3k (variant per tier), capabilities ~3k, school-conventions ~2.5k. Verified by token-counting test (tolerance ±30%).
- **AC.S3.3** — Tier-conditioned content: same resource read with super_admin vs acharya vs client API key returns different content. Verified by integration test with three keys.
- **AC.S3.4** — `chart-snapshot` content includes lagna sign + degree + lord, all 9 planets with house+sign+degree+dignity+nakshatra, current active dasha, top transit events at "now". No prose synthesis — structured markdown only.
- **AC.S3.5** — `house-rules` super_admin variant explicitly documents: strict cite-allowlist contract, B.11 floor instruction, PPL discipline, when-to-use-bundles-vs-primitives rule, audit subsystem behavior, tier-template specifications for each tier. Acharya variant omits internal-audit sections; client variant simplifies to plain-language confidence and mandates falsifier on every prediction.
- **AC.S3.6** — All Tier 1 primitive tool descriptions are generated from a single source of truth (the underlying enum or registry). No hand-authored category lists. Test: read enum, read tool description, confirm category list parity.

**Sealing artifact:** `00_ARCHITECTURE/MCP_V3_1_0_S3_CLOSE.md`. Includes the final per-tier house-rules variants as appendices.

### v3.1.0-S4 — Perf system + audit subsystem (P0–P4)

**Files touched (expected):**
- Migrations `073_perf_log_extensions.sql`, `074_audit_findings.sql`, `075_prediction_outcomes.sql`, `076_data_source_expected_and_caveats.sql`
- `platform/src/lib/perf/mv_refresh.ts` (cron entry-point for materialized view refresh)
- `platform/src/lib/perf/audit_nightly.ts` (the audit job)
- `platform/src/lib/perf/heuristics/*.ts` (extract_citations, extract_numerical_claims, etc.)
- `platform/src/app/api/mcp/health/tools/route.ts` (new endpoint)
- `platform/src/app/api/mcp/health/coverage/route.ts` (new endpoint)
- `platform-mcp/src/tools/tool_health.ts` (new)
- `platform-mcp/src/tools/data_coverage.ts` (new)
- `platform-mcp/src/resources/capabilities.ts` (wire to real perf views — was placeholder in S3)
- `platform-mcp/src/tools/get_trace.ts` (extend to include findings)
- `00_ARCHITECTURE/perf_system_seeds/data_source_expected_seed.sql` (new seed)
- Cloud Run scheduler entries (added to existing scheduler infrastructure)

**Acceptance:**
- **AC.S4.1** — Migrations apply cleanly to staging; rollback scripts verified.
- **AC.S4.2** — `tool_health()` MCP call returns a populated result with all 10 primitives + 2 bundles. Each tool has at least latency + ok/zero-rows/error rates.
- **AC.S4.3** — `data_coverage()` MCP call returns rows for `chart_facts`, `msr_signals`, `lel_events`, `panchang_daily`, `ephemeris_daily`, `rag_chunks`, `multi_school_*`, `classical_texts`.
- **AC.S4.4** — Nightly audit job runs successfully on staging against a backfilled day of v1 traces. At least one finding per class is produced (verified by inserting a synthetic test trace with known violations).
- **AC.S4.5** — `get_trace(trace_id)` returns extended envelope with `audit_findings: [...]` for any trace processed by the audit job.
- **AC.S4.6** — `marsys://capabilities` resource is now generated from real perf views (not the S3 placeholder). Re-attach session and confirm the resource shows current 24h metrics.
- **AC.S4.7** — Tier-gating on perf tools: client-tier key calling `tool_health` returns 403; super_admin + acharya succeed.
- **AC.S4.8** — Materialized view refresh cron entries are live in the scheduler. View ages observed in dashboard match refresh cadence (5min / 10min / 15min / nightly).

**Sealing artifact:** `00_ARCHITECTURE/MCP_V3_1_0_S4_CLOSE.md`. Documents which audit heuristic implementations exist (extract_citations, extract_numerical_claims, etc.) with their false-positive characterization.

### v3.1.0-S5 — Operator dashboard at `/admin/mcp/health`

**Files touched (expected):**
- `platform/src/app/admin/mcp/health/page.tsx` (new — main dashboard page)
- `platform/src/app/admin/mcp/health/tabs/ToolHealth.tsx` (new)
- `platform/src/app/admin/mcp/health/tabs/DataCoverage.tsx` (new)
- `platform/src/app/admin/mcp/health/tabs/AuditFindings.tsx` (new)
- `platform/src/app/admin/mcp/health/tabs/PredictionsCalibration.tsx` (new — calibration grid is placeholder if mv_calibration_score not yet present; full impl lands in v3.4-P6)
- `platform/src/app/admin/mcp/health/tabs/Sessions.tsx` (new)
- `platform/src/app/admin/mcp/health/components/CaveatEditor.tsx` (new)
- `platform/src/app/admin/mcp/health/components/AlertThresholds.tsx` (new)
- `platform/src/lib/alerts/dispatch.ts` (new — Slack + email)
- Migration `077_mcp_alerts_config_and_tool_registry.sql`

**Acceptance:**
- **AC.S5.1** — Page accessible at `/admin/mcp/health`, super_admin-only (other tiers 403 at the page route).
- **AC.S5.2** — All five tabs render with live data from the perf views.
- **AC.S5.3** — Inline caveat editor: operator types a caveat, selects class + severity, saves. Caveat persists to `tool_caveats`. On next `tool_health()` MCP call, the caveat surfaces.
- **AC.S5.4** — Alerts: trigger threshold breach (e.g., manually insert audit findings to push `cite_fabricated` rate over threshold). Verify Slack notification dispatched.
- **AC.S5.5** — `tool_enabled` toggle: operator disables a tool. Next call to that tool via MCP returns 503 with `tool_disabled: true` in the envelope.
- **AC.S5.6** — Audit Findings drill-down: click finding → modal shows trace, response text excerpt, cited IDs, fabricated IDs (highlighted). Resolve action works.

**Sealing artifact:** `00_ARCHITECTURE/MCP_V3_1_0_S5_CLOSE.md`.

### v3.1.0-S6 — Tier-conditioned house-rules content + sealing

**Files touched (expected):**
- `platform-mcp/src/resources/house_rules_variants/super_admin.md` (final content)
- `platform-mcp/src/resources/house_rules_variants/acharya.md` (final content)
- `platform-mcp/src/resources/house_rules_variants/client.md` (final content)
- `platform-mcp/src/resources/house_rules_variants/public_redacted.md` (authored but unused; ready for future)
- `platform/src/lib/feature_flags.ts` (flip `MARSYS_FLAG_MCP_V3_ENABLED` default to true)
- `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` (add v3 artifacts to §1)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (add v3 artifacts)
- `00_ARCHITECTURE/MCP_V3_1_0_CLOSE.md` (the sealing artifact)
- `00_ARCHITECTURE/SESSION_LOG.md` (close-out append)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (state pointer to next phase: v3.2-S1)
- `.geminirules` + `.gemini/project_state.md` (MP.1 / MP.2 mirror updates — adapted parity)
- `CLAUDE.md` (§E concurrent workstream entry for MCP v3.1)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md` (this file — status flipped to COMPLETE)

**Acceptance:**
- **AC.S6.1** — Same query against same data returns different output templates by tier (verified by operator-run probe with three keys: super_admin, acharya, client).
- **AC.S6.2** — End-to-end smoke from Claude Chat custom connector: attach via `?api_key=` URL, observe 5 resources auto-load, call `holistic_bundle("strongest planet")` and receive ≥6 sub-tool entries within 20s. No timeout.
- **AC.S6.3** — End-to-end smoke from Cowork MCP attach: same flow.
- **AC.S6.4** — Operator-side audit job ran nightly for at least 7 days during v3.1.0 with zero job errors. Total findings count > 0 (verifying the job is producing output).
- **AC.S6.5** — `MARSYS_FLAG_MCP_V3_ENABLED` flipped to true in production. v1 `/api/mcp/execute` still live as fallback (deletion is v3.1.0-S7, out of brief scope).
- **AC.S6.6** — Mirror discipline: `.geminirules` and `.gemini/project_state.md` updated to adapted parity per MP.1 / MP.2. `mirror_enforcer.py` exits 0.
- **AC.S6.7** — `CANONICAL_ARTIFACTS_v1_0.md §1` includes entries for `MCP_ARCH_v3_PROPOSAL` (status CURRENT, v3.1), `MCP_PERF_SYSTEM_BRIEF` (status CURRENT, v3.1), and `MCP_V3_1_0_CLOSE` (status CURRENT, v1.0). v1 brief `MCP_BRIEF_v1_0.md` flips to status SUPERSEDED-AS-COMPLETE.
- **AC.S6.8** — Red-team session scheduled for v3.4-S2 per `IS.8(b)` cadence. Calendar entry created; threat-model summary attached to the close artifact.
- **AC.S6.9** — `CLAUDE.md §E` updated with MCP v3.1 as a concurrent workstream (status ACTIVE — v3.1.0 closed; v3.2 next).
- **AC.S6.10** — This brief's frontmatter `status` set to `COMPLETE`.

**Sealing artifact:** `00_ARCHITECTURE/MCP_V3_1_0_CLOSE.md`. Body: phase summary, acceptance criteria evidence, residual risks, v3.2 entry conditions, red-team scheduling note, mirror-propagation evidence.

---

## §5 — Cross-cutting requirements (apply to every sub-phase)

**Per-sub-phase session-open handshake.** Every sub-phase session opens by emitting the SESSION_OPEN artifact per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`. Validated by `platform/scripts/governance/schema_validator.py`. Includes `red_team_due` evaluation per `CLAUDE.md §M` cadence.

**Per-sub-phase session-close checklist.** Every sub-phase emits SESSION_CLOSE per `SESSION_CLOSE_TEMPLATE_v1_0.md`. Includes `mirror_updates_propagated` block (empty for S1–S5; populated at S6).

**Test discipline.** Every new tool, primitive, bundle, resource, audit heuristic, and dashboard component ships with unit tests AND at least one integration test. No exceptions. Coverage gate: new files in v3.1.0 sub-phases must have ≥80% line coverage; existing files modified retain or improve current coverage.

**Migration discipline.** Every migration includes a rollback script. All migrations are tested against a staging clone of production before applying to production. Migrations apply in numeric order (072 → 077).

**Observability.** Every new tool / bundle writes to `tool_execution_log` with the v3.1 extended columns. Every new endpoint writes a trace step. Every audit job run writes a run_id row to `audit_job_runs` (small new table — add to migration 074).

**Mirror discipline (MP.1 + MP.2).** S6 closing session is responsible for `.geminirules` + `.gemini/project_state.md` adapted-parity updates. S1–S5 sessions do not touch these unless they introduce a governance-relevant change (none expected).

**Documentation.** Each sub-phase's `*_CLOSE.md` artifact includes: scope summary, files-touched list, acceptance criteria evidence (test runs, smoke evidence), residual risks/known issues, next-sub-phase entry conditions. The S6 close additionally rolls these into a phase-level summary.

---

## §6 — Out of scope (deferred to later phases)

- **Data backfill.** Items 1–13 from arch §9.2. v3.2 (classical grounding) → v3.3 (depth) → v3.4 (epistemic refinement). Separate briefs per sub-phase.
- **Red-team session.** v3.4-S2.
- **F.6 — `marsys_methodology_block` removal from `/consume` synthesis prompt.** Recommended but separate brief; not gated by v3.1.0.
- **v1 `/api/mcp/execute` deletion.** Stays live as fallback through v3.1.0 + 7-day grace. Deletion is v3.1.0-S7 or v3.1.1 (operator's call after grace period).
- **OAuth (MCP-5 phase).** Deferred to v3.5 or later per arch §13 Q11.
- **`/consume` web chat convergence onto v3 primitives.** Deferred indefinitely; flagged at arch §13 Q8.

---

## §7 — Acceptance evidence requirements

For each acceptance criterion (AC.*), the closing sub-phase artifact must include:

- **The test that verifies it** (file path + test name).
- **The most recent passing run** (CI run URL or local test output excerpt with timestamp).
- **Any caveats or known-flakes** that need follow-up.

The S6 closing artifact aggregates AC evidence across all six sub-phases into a single phase-level acceptance table. No AC is "soft" — every one must be evidence-backed.

---

*End of CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md. Status: ACTIVE. Read by every Claude Code session opening on the `feature/mcp-v3` branch until status flips to COMPLETE at v3.1.0-S6 sealing.*
