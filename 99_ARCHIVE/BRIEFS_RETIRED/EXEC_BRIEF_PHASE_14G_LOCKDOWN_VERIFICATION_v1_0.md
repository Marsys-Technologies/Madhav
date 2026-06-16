---
brief_id: EXEC_BRIEF_PHASE_14G_LOCKDOWN_VERIFICATION
version: 1.1
status: AUTHORED
amended_at: 2026-04-28 — v1.1: count-range corrections per 14C close (eclipses 800–1100; retrogrades 2,000–3,500; sade_sati flagged for Stream F investigation); ephemeris_daily expected updated to 660,726 actual)
authored_by: Cowork (Opus)
authored_at: 2026-04-28
target_executor: Claude Code session (Sonnet 4.6) in Anti-Gravity / VS Code (single multi-stream session OR split if Stream E smoke runs long)
trigger_phrase: "Read EXEC_BRIEF_PHASE_14G_LOCKDOWN_VERIFICATION_v1_0.md and execute it."
phase: 14G
phase_name: Phase 14 Lockdown Verification — schema + data + tool + smoke audit; freeze TRANSITIONAL → LOCKED
risk_classification: MEDIUM (verification phase; smoke tests against the live runtime can reveal regressions; findings triage may surface blocking issues that need follow-up briefs before lockdown closes)
parallelizable_with: []  # final phase — runs after every other 14X is closed
must_complete_before: [Phase 14 formal close]
depends_on:
  - EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE_v1_0.md (COMPLETE)
  - EXEC_BRIEF_PHASE_14C_L1_STRUCTURED_TABLES_v1_0.md (FULLY COMPLETE — all eight Streams A–H)
  - EXEC_BRIEF_PHASE_14D_L2_5_PARITY_v1_0.md (COMPLETE)
  - EXEC_BRIEF_PHASE_14E_L3_REGISTERS_v1_0.md (COMPLETE)
  - EXEC_BRIEF_PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_v1_0.md (COMPLETE)
  - EXEC_BRIEF_PHASE_14F_FOLLOWUP_CHANGELOG_AND_BASELINE_v1_0.md (COMPLETE)
output_artifacts:
  - 00_ARCHITECTURE/PHASE_14_LOCKDOWN_v1_0.md (NEW canonical sealing artifact — frozen post-Phase-14 state record)
  - 00_ARCHITECTURE/PHASE_14G_LOCKDOWN_VERIFICATION_REPORT_v1_0.md (NEW execution report)
  - 00_ARCHITECTURE/PHASE_14_FINDINGS_DISCHARGE_v1_0.md (NEW classification of every 14B–14F finding)
---

# EXEC_BRIEF — Phase 14G — Lockdown Verification

## Mission

Verify that the Phase 14 modernization is internally consistent, externally observable, and ready to be sealed as the new "you are here" baseline. After 14G, every TRANSITIONAL entry in `CAPABILITY_MANIFEST.json` flips to LOCKED, every Phase 14 finding is classified (closed | accepted-as-residual | open-for-followup), the runtime is smoke-tested against the live structured tables + tools, and a sealing artifact `PHASE_14_LOCKDOWN_v1_0.md` is committed as the formal close record.

This brief is the analogue of `GOVERNANCE_BASELINE_v1_0.md` from the Step 0→Step 15 governance rebuild close. It does not introduce new infrastructure or content — it audits, classifies, and seals what 14B–14F produced.

Three architectural commitments:

1. **Lockdown is a consistency audit, not a regression suite.** 14G verifies that Phase 14's deliverables match what the briefs promised — schemas as specified, row counts in expected ranges, FK integrity, tool coverage, validator-baseline-diff. It is NOT a re-evaluation of whether Phase 14's design was correct; that decision was made and accepted at the brief-by-brief level.

2. **Smoke tests exercise the runtime end-to-end, with the new tools active.** Stream E fires 5–10 deterministic queries through the live Consume API and confirms that (a) the LLM is calling the new structured tools (not just falling back to rag-search), (b) returned facts trace back to provenance rows, (c) B.10 discipline holds (no fabricated computation; missing data marked `[EXTERNAL_COMPUTATION_REQUIRED]`).

3. **Findings discharge is decisive.** Every finding from 14B (FK chain fix), 14C (extraction residuals + ephemeris CSV residual), 14D (F.01–F.06 + cgm_edges anomaly), 14E (deferred chart_facts/life_events FK gaps) gets one of three dispositions: **CLOSED** (fix landed), **WHITELISTED** (accepted as known residual; added to `ONGOING_HYGIENE_POLICIES §F` known_residuals list), or **DEFERRED** (open follow-up brief authored). No finding leaves 14G in an undiscussed state.

## Pre-flight gate

1. Verify all upstream phases COMPLETE — frontmatter check on each:
   - `EXEC_BRIEF_PHASE_14B_BUILD_PIPELINE_v1_0.md`
   - `EXEC_BRIEF_PHASE_14C_L1_STRUCTURED_TABLES_v1_0.md` (and ALL its Streams A–H closed; check the 14C report)
   - `EXEC_BRIEF_PHASE_14D_L2_5_PARITY_v1_0.md`
   - `EXEC_BRIEF_PHASE_14E_L3_REGISTERS_v1_0.md`
   - `EXEC_BRIEF_PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_v1_0.md`
   - `EXEC_BRIEF_PHASE_14F_FOLLOWUP_CHANGELOG_AND_BASELINE_v1_0.md`
2. Verify `00_ARCHITECTURE/PHASE_14F_VALIDATOR_BASELINE.txt` exists (this is the diff target for Stream D).
3. Verify Cloud SQL `amjis-postgres` is reachable; `amjis-web`/`amjis-sidecar` are healthy.
4. Confirm the runtime feature flags `NEW_QUERY_PIPELINE_ENABLED=true` and `AUDIT_ENABLED=true` are still set (per Phase 11A cutover) — Stream E smoke runs against the new pipeline.
5. Confirm git working tree clean.

If any fail, halt with actionable message. Particularly: if 14C is partially closed (some Streams done, others not), 14G **must not** proceed — Stream B FK validations require chart_facts populated, Stream E smoke requires all 16 tools registered. Lockdown of a half-built modernization is worse than no lockdown.

## Scope

**`may_touch`:**
- `00_ARCHITECTURE/PHASE_14_LOCKDOWN_v1_0.md` (NEW canonical sealing artifact)
- `00_ARCHITECTURE/PHASE_14G_LOCKDOWN_VERIFICATION_REPORT_v1_0.md` (NEW)
- `00_ARCHITECTURE/PHASE_14_FINDINGS_DISCHARGE_v1_0.md` (NEW)
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (TRANSITIONAL → LOCKED status flips on Phase 14 entries; new fingerprint)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (update §2 "you are here" block to reflect Phase 14 close)
- `00_ARCHITECTURE/ONGOING_HYGIENE_POLICIES_v1_0.md` (§F additions — new known_residuals entries from findings discharge, if any WHITELISTED)
- `verification_artifacts/PHASE_14G/` (NEW directory — smoke test outputs, validator outputs, query-by-query audit JSONs)
- New follow-up briefs **only if** Findings Discharge classifies items as DEFERRED — the brief stub goes to repo root with `status: AUTHORED`.

**`must_not_touch`:**
- Any data in any Phase 14 table — 14G is read-only against tables.
- Any phase report (14B/14C/14D/14E/14F reports stay frozen as authored).
- Any platform/src/** code — runtime fixes are NOT in 14G scope.
- Any feature flag.
- Any chunker, embedder, writer, or extractor.
- L2 archive (`99_ARCHIVE/02_ANALYTICAL_LAYER/`) — formally sealed in 14F.

## Sub-streams (7 sequential)

### Stream A — Migration + schema audit

1. Connect to `amjis-postgres` via Cloud SQL Auth Proxy.
2. Query `pg_migrations` (or equivalent migration tracking) for applied migrations. Expected:
   - 001 through 012 (pre-Phase-14)
   - 013 (Phase 14B build_pipeline_staging)
   - 014, 015, 016, 017 (Phase 14C L1 tables)
   - 018 (Phase 14D L2.5 tables)
   - 019 (Phase 14E L3 registers)
3. For each migration ≥013, verify all CREATE TABLE statements landed by querying `information_schema.tables`. Halt on any missing table.
4. Audit FK constraints via `pg_constraint`:
   - `cgm_edges.source_node_id → cgm_nodes.node_id`
   - `cgm_edges.target_node_id → cgm_nodes.node_id`
   - All `*.build_id → build_manifests.build_id`
5. Audit CHECK constraints (status enums, confidence ranges, valence enums, etc.) for each Phase 14 table.
6. Capture full schema snapshot via `pg_dump --schema-only --table=<each-14-table>` to `verification_artifacts/PHASE_14G/schema_snapshot.sql`.

### Stream B — Row counts + FK integrity

1. Query row counts on each Phase 14 table (live, not staging). Compare against expected ranges:

| Table | Expected count | Source |
|---|---|---|
| `rag_chunks` | ~941 | 14B build manifest |
| `rag_embeddings` | ~941 (same as chunks) | 14B |
| `chart_facts` | 589 (per 14C close) | 14C Stream B YAML extraction (and downstream load) |
| `ephemeris_daily` | 660,726 (per 14C close — 73,414 days × 9 graha; year 2100 inclusive + leap years) | 14C Stream C bootstrap |
| `eclipses` | 800–1,100 (per 14C close: 913 actual; ~5 eclipses/year × 200 years) | 14C Stream D |
| `retrogrades` | 2,000–3,500 (per 14C close: 2,462 actual; ~1 retrograde-pair/planet/year × 5 planets × 200 years ≈ 2,000) | 14C Stream D |
| `life_events` | 36 exactly | 14C Stream E |
| `sade_sati_phases` | 46 actual per 14C close (4× higher than original brief expectation of 8–12) — **Stream F INVESTIGATION ITEM**: diff against `SADE_SATI_CYCLES_ALL.md`; likely legitimate (sub-window granularity by nakshatra transit) but verify | 14C Stream E |
| `msr_signals` | 499 exactly | 14D |
| `ucn_sections` | 134 (per 14D close) | 14D |
| `cdlm_links` | 81 exactly | 14D |
| `cgm_nodes` | 234 (per 14D close) | 14D |
| `cgm_edges` | 21 (per 14D close — **see Stream F anomaly investigation**) | 14D |
| `rm_resonances` | 28 (per 14D close) | 14D |
| `pattern_register` | 22 (per 14E close) | 14E |
| `resonance_register` | 12 (per 14E close) | 14E |
| `cluster_register` | 12 (per 14E close) | 14E |
| `contradiction_register` | 8 (per 14E close) | 14E |
| `build_manifests` | ≥1 (must have exactly 1 with `status='live'`) | 14B |

2. Run **deferred FK validations from 14E close**:
   - Every `pattern_register.source_fact_ids` element resolves against `chart_facts.fact_id`. Halt on missing.
   - Every `cluster_register.member_fact_ids` element resolves against `chart_facts.fact_id`.
   - Every `cluster_register.member_event_ids` element resolves against `life_events.event_id`.
   - Every `contradiction_register.source_fact_ids` element resolves against `chart_facts.fact_id`.
3. Run **load-bearing referential integrity** across L2.5:
   - Every `ucn_sections.derived_from_signals` element resolves against `msr_signals.signal_id`.
   - Every `cgm_edges.source_node_id` and `target_node_id` resolves against `cgm_nodes.node_id` (FK enforced; this is a sanity check).
   - Every `rm_resonances.signal_a_id` and `signal_b_id` resolves against `msr_signals.signal_id`.
4. **build_manifests singleton check**:
   ```sql
   SELECT status, COUNT(*) FROM build_manifests GROUP BY status;
   ```
   Exactly 1 row with `status='live'`. All others `status IN ('rolled_back', 'failed', 'staging')`. Halt on multiple `live` rows — that's a swap discipline violation.
5. Capture all counts + FK validation output to `verification_artifacts/PHASE_14G/data_audit.json`.

### Stream C — Build manifest + tool registry coverage

1. Read the live `build_manifests` row. Confirm fields populated: `manifest_uri`, `pipeline_image_uri`, `embedding_model = 'text-multilingual-embedding-002'`, `embedding_dim = 768`. Halt on mismatch.
2. Fetch the manifest JSON from GCS at the `manifest_uri`. Cross-check `chunk_count` matches `rag_chunks` row count from Stream B. Cross-check `embedding_count` matches `rag_embeddings`.
3. Tool registry audit: parse `platform/src/lib/tools/registry.ts` (or `consume-tools.ts` per Phase 14E close). Confirm all expected tools registered:

| Tool | Source | Expected |
|---|---|---|
| `rag_search` | pre-14B | ✅ |
| `query_chart_fact` | 14C | ✅ |
| `query_planet_position` | 14C | ✅ |
| `query_eclipse_window` | 14C | ✅ |
| `query_retrograde_window` | 14C | ✅ |
| `query_life_events` | 14C | ✅ |
| `query_sade_sati` | 14C | ✅ |
| `query_dasha` | 14C | ✅ |
| `query_msr_signals` | 14D | ✅ |
| `query_ucn_section` | 14D | ✅ |
| `query_cdlm_link` | 14D | ✅ |
| `query_cgm` | 14D | ✅ |
| `query_resonance` | 14D | ✅ |
| `query_patterns` | 14E | ✅ |
| `query_resonances_l3` | 14E | ✅ |
| `query_clusters` | 14E | ✅ |
| `query_contradictions` | 14E | ✅ |

   17 tools total. Halt on any missing. Inspect each tool's `description` field for substantive content (not "TODO" stubs).
4. Capture tool list + descriptions to `verification_artifacts/PHASE_14G/tool_registry.json`.

### Stream D — Validator sweep with baseline diff

1. Run all three governance validators with the same invocation as the 14F.1 baseline:
   ```bash
   python3 platform/scripts/governance/schema_validator.py 2>&1 | tee verification_artifacts/PHASE_14G/schema_validator.txt
   python3 platform/scripts/governance/drift_detector.py 2>&1 | tee verification_artifacts/PHASE_14G/drift_detector.txt
   python3 platform/scripts/governance/mirror_enforcer.py 2>&1 | tee verification_artifacts/PHASE_14G/mirror_enforcer.txt
   ```
2. Capture exit codes + violation/finding counts.
3. Diff against 14F.1 baseline (70 schema violations / 136 drift findings / 0 mirror failures):
   - Schema validator: violations <= 70 = PASS, > 70 = HALT (regression).
   - Drift detector: findings <= 136 + (expected new entries from Phase 14 additions; quantify before halt).
   - Mirror enforcer: must remain 0.
4. If schema/drift counts exceeded baseline by amounts attributable to Phase 14 additions (new tables, new tools, new manifest entries), classify as **expected delta** — record in report. If the delta points at unrelated regressions, halt and surface for findings triage.
5. Capture deltas + classification to `verification_artifacts/PHASE_14G/validator_diff.md`.

### Stream E — Smoke-test queries

10 queries fired through the live `/api/chat/consume` route (production-equivalent). Each captures `audit_event` for replay.

For each query, verify in the audit event:
- The LLM **called the new structured tools** at least once (not just fallback to `rag_search`).
- Returned facts include `provenance.source_uri` + `build_id` (B.10 discipline).
- Missing data is marked `[EXTERNAL_COMPUTATION_REQUIRED]` if the relevant tool returned nothing — NOT silently fabricated.

Suggested smoke set (executor adapts wording to fit Consume API expectations):

| # | Query | Expected tool calls | Expected response shape |
|---|---|---|---|
| 1 | "What is my Saturn's longitude in the natal chart?" | `query_chart_fact('PLN.SATURN.LON_DEG')` or `query_planet_position(date='1984-02-05', planet='saturn')` | Numeric longitude, sign, nakshatra, with FORENSIC §3.1 citation |
| 2 | "Which house is Jupiter in across all 28 divisional charts?" | `query_chart_fact(category='planet', divisional_chart='*')` | 28 rows; each with house number; FORENSIC source sections |
| 3 | "List my marriage events from the life log." | `query_life_events(category='marriage')` | 1 row (per LEL); chart_state populated |
| 4 | "What was Saturn doing on 2018-03-15?" | `query_planet_position(date='2018-03-15', planet='saturn')` | Single row from ephemeris_daily; ephemeris_version logged |
| 5 | "List eclipses in 2020." | `query_eclipse_window(start_date='2020-01-01', end_date='2020-12-31')` | 4–6 rows |
| 6 | "What's currently active in my sade sati cycle?" | `query_sade_sati(date='today')` | 1 row (active phase); cross-references Saturn's current sign |
| 7 | "Find every MSR signal involving Saturn in the 7th house with negative valence." | `query_msr_signals(planet='SATURN', house=7, valence='negative')` | ≥1 row |
| 8 | "How does the self domain link to the partner domain in the chart?" | `query_cdlm_link(from='self', to='partner')` or domain-equivalent naming | 1 row (link_type, strength) |
| 9 | "What unresolved contradictions are in my chart?" | `query_contradictions(unresolved_only=true)` | Multiple rows from contradiction_register |
| 10 | "Tell me about cluster patterns for career." | `query_clusters(domain='career')` (or equivalent) | ≥1 row |

For each query, capture the audit_event JSON + response into `verification_artifacts/PHASE_14G/smoke_<n>.json`. If any query fails (tool not called, fabricated data, runtime error), halt and surface.

**Hard gate**: at least 8 of the 10 queries must call at least one new structured tool (not just `rag_search`). If 7 or fewer, the router isn't selecting the new tools — that's a tool-description quality regression and gates lockdown.

### Stream F — Findings triage + cgm_edges anomaly investigation

1. Read every Phase 14 phase report:
   - `00_ARCHITECTURE/PHASE_14_0_ASSET_INVENTORY_REPORT_v1_0.md` (or whatever the 14.0 close report is named)
   - `00_ARCHITECTURE/PHASE_14A_GCS_FOUNDATION_REPORT_v1_0.md`
   - `00_ARCHITECTURE/PHASE_14A_FOLLOWUP_IAM_REPORT_v1_0.md`
   - `00_ARCHITECTURE/PHASE_14B_BUILD_PIPELINE_REPORT_v1_0.md`
   - `00_ARCHITECTURE/PHASE_14C_L1_STRUCTURED_TABLES_REPORT_v1_0.md`
   - `00_ARCHITECTURE/PHASE_14D_L2_5_PARITY_REPORT_v1_0.md` (with F.01–F.06 findings)
   - `00_ARCHITECTURE/PHASE_14E_L3_REGISTERS_REPORT_v1_0.md`
   - `00_ARCHITECTURE/PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_REPORT_v1_0.md`
2. Extract every "finding", "residual", "follow-up", "deferred" item. Compile master list.
3. Classify each item:
   - **CLOSED**: a fix has landed in a subsequent commit that resolves the finding. Cite commit SHA.
   - **WHITELISTED**: accepted as known residual; will not be fixed in foreseeable future. Add to `ONGOING_HYGIENE_POLICIES_v1_0.md §F` known_residuals list with rationale.
   - **DEFERRED**: requires a follow-up brief. Author a brief stub at repo root (`EXEC_BRIEF_PHASE_<id>_v1_0.md`) with `status: AUTHORED`. Do NOT execute; just queue.
4. **sade_sati_phases anomaly investigation** — the 14C close reports sade_sati_phases=46. Original 14C brief expected 8–12 (4 cycles × 2–3 phases). Investigate:
   - Read `01_FACTS_LAYER/SADE_SATI_CYCLES_ALL.md`. Count explicit phase blocks (rising / peak / setting × cycles).
   - Cross-check `sade_sati_phases` table: are rows segmented by nakshatra transits within each phase (would inflate count), or by Saturn-sub-period within phase, or something else?
   - If the inflation is from legitimate sub-window granularity that adds analytical depth, classify as **CLOSED — expected (original brief estimate too coarse)** and update brief docstrings.
   - If rows duplicate the same phase across overlapping definitions, classify as **DEFERRED** with a 14C follow-up dedup brief.
   - Capture finding + investigation result in the report.

5. **cgm_edges anomaly investigation** — the 14D close reports cgm_edges=21. Historical CGM ledger (per memory notes from prior B-stream work) cited 3915 edges. Investigate:
   - Read `CGM_v9_0.md` and count explicit edge declarations (ASPECTS, RULES, EXALTED_IN, etc. patterns).
   - If the markdown legitimately has ~21 explicit edges and the historical 3915 came from synthesized derivations not present in the markdown, classify as **expected — markdown is the authoring source-of-truth and downstream synthesis happens elsewhere**.
   - If the markdown has hundreds/thousands of edges that the extractor missed, classify as **DEFERRED finding** — author a `EXEC_BRIEF_PHASE_14D_FOLLOWUP_CGM_EDGES_v1_0.md` brief.
   - Capture finding + investigation result in the report.
6. **Manifest fingerprint population** — the 14C close report flagged drift_detector showing +122 findings, attributed to "missing fingerprints in new manifest entries." Populate the missing fingerprints:
   - For each `CAPABILITY_MANIFEST.json` entry that lacks a `fingerprint` field but has a resolvable `path` or `gcs_uri`, compute sha256 of the referenced content and write it.
   - Re-run `drift_detector` post-fingerprint-population. The 122-finding delta should drop close to zero.
   - This is the core "drift reduction" work the 14C close report identified as 14G scope.

7. Author `00_ARCHITECTURE/PHASE_14_FINDINGS_DISCHARGE_v1_0.md` — single document listing every finding by source phase + classification + commit/brief reference.

### Stream G — Documentation freeze + lockdown report + atomic commit

1. **CAPABILITY_MANIFEST.json freeze**: for every entry currently `status: TRANSITIONAL` that originated in Phase 14 (rag_chunks, rag_embeddings, all six L1 tables, all six L2.5 tables, all four L3 registers, build_manifests, all 16 new tools, BUILD_PIPELINE_v1_0.md, GCS_LAYOUT_v1_0.md, L1_STRUCTURED_LAYER_v1_0.md, L2_5_STRUCTURED_LAYER_v1_0.md, L3_DISCOVERY_REGISTERS_v1_0.md), flip to `status: LOCKED` with `locked_at: 2026-04-28, locked_in: PHASE_14G`. Recompute fingerprint; record old/new in report.
2. **`CURRENT_STATE_v1_0.md` update §2**:
   - Active macro-phase: M2 (still active; Phase 14 was a sub-modernization within M2's scope)
   - Phase 14 modernization: **CLOSED 2026-04-28 at Phase 14G lockdown**
   - Total tables in Postgres: 18 Phase-14-owned + pre-existing
   - Total tools in registry: 17
   - Manifest fingerprint: <new value>
   - Next: M2 sub-phase work resumes against the modernized data layer
3. **`PHASE_14_LOCKDOWN_v1_0.md`** (NEW canonical sealing artifact). Sections:
   - Lockdown identity (date, commit SHA, actor)
   - Inventory of frozen artifacts (table counts, tools, docs)
   - Validator state (deltas vs 14F.1 baseline)
   - Findings disposition summary (count by classification)
   - Smoke test outcomes (10/10 or X/10 with specific failures)
   - Provenance: chain of phase reports leading here
   - Ratchet: anything that violates this baseline going forward fails `drift_detector` and requires explicit unfreezing.
4. **`PHASE_14G_LOCKDOWN_VERIFICATION_REPORT_v1_0.md`** — execution report (Stream-by-Stream outcomes; pointers to verification_artifacts/).
5. Atomic commit. Title: `Phase 14G: Lockdown verification — Phase 14 modernization SEALED`.

## Done criteria

1. All 19+ migrations applied; all expected tables exist with correct schemas.
2. Every Phase 14 table populated within expected count ranges.
3. All deferred 14E FK validations resolve cleanly.
4. `build_manifests` has exactly 1 row with `status='live'`.
5. 17 tools registered with substantive descriptions.
6. Validator deltas vs 14F.1 baseline either zero or attributable to expected Phase 14 additions.
7. ≥8 of 10 smoke queries call new structured tools (not fallback rag_search).
8. Every Phase 14 finding classified CLOSED | WHITELISTED | DEFERRED with corresponding artifact (commit / hygiene-policy entry / new brief).
9. cgm_edges anomaly investigated and classified.
10. `CAPABILITY_MANIFEST.json` Phase 14 entries flipped to LOCKED; new fingerprint recorded.
11. `CURRENT_STATE_v1_0.md` §2 updated to reflect Phase 14 close.
12. `PHASE_14_LOCKDOWN_v1_0.md` + `PHASE_14G_LOCKDOWN_VERIFICATION_REPORT_v1_0.md` + `PHASE_14_FINDINGS_DISCHARGE_v1_0.md` exist and committed.
13. Atomic commit lands on the working branch.

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Smoke test reveals the router never calls new structured tools (uses rag_search exclusively) | Medium | HIGH | Hard gate at Stream E step "≥8/10 must call structured tools." Halt + surface for tool-description fix follow-up brief. |
| Validator violations exceed 14F.1 baseline by amounts NOT attributable to Phase 14 additions | Low | MEDIUM | Stream D classifies the delta; if classification fails, halt and surface as findings-triage entry. |
| FK validation fails — register entry references missing chart_fact | Medium | HIGH | Stream B halts. Likely cause: 14C Stream B YAML didn't fully load to chart_facts table (vs just file). 14C close should have caught; if it didn't, queue 14C remediation brief. |
| cgm_edges=21 is a real extractor bug, not legitimate markdown sparsity | Medium | MEDIUM | Stream F investigation; if extractor bug, queue 14D follow-up brief; do NOT block lockdown if the bug is documented and queued. |
| Phase 14 reports missing or inconsistent (e.g., 14C report says different numbers than tables) | Low | MEDIUM | Stream B numbers are the ground truth; if reports mismatch, surface as finding for report-correction follow-up. Lockdown can still close if tables are right. |
| Stream E smoke takes longer than one Claude Code session can hold | Low | Low | Decompose Stream E into 2 sessions if needed (5 queries each). Each session captures audit_events; results aggregated in Stream F/G. |
| 10 smoke queries trigger Vertex AI quota throttling | Low | Low | Queries are spaced >5s apart; quota is generous for embed-002 calls. If hit, retry with backoff. |
| Lockdown attempts to flip a manifest entry that no longer exists | Low | Low | Stream G confirms each entry's current state before flipping; missing entries surfaced as findings, not failures. |
| `ONGOING_HYGIENE_POLICIES §F` known_residuals list grows unboundedly from WHITELISTED items | Medium | Low | Each WHITELISTED entry includes a rationale + revisit date. Quarterly governance pass (per §H) re-evaluates; nothing stays whitelisted permanently without justification. |

## Concurrency declaration

14G is **strictly serial** — must run after every other Phase 14 brief is closed. Cannot parallel with anything in the Phase 14 sequence.

After 14G closes, M2 sub-phase work (B.7 router, B.8 synthesis, B.9 advanced retrieval — whichever was queued before the modernization detour) resumes against the modernized data layer.

## Trigger phrase

"Read EXEC_BRIEF_PHASE_14G_LOCKDOWN_VERIFICATION_v1_0.md and execute it."

## Notes for the executor

- 14G is the cleanest brief in the Phase 14 sequence to read — pure verification, no new design decisions. If something feels like a design decision rather than a verification, surface it as a finding rather than making the call.
- The findings discharge (Stream F) is where Phase 14's loose ends get formally tied. Be liberal with DEFERRED — it's better to queue a small follow-up brief than to silently WHITELIST something that should be fixed.
- The cgm_edges investigation is the one substantive analytical task. Spend time on it — the answer (legitimate-sparsity vs extractor-bug) determines whether the chart graph has structural depth or is a stub. Read the markdown; count edges; compare to 21. If it takes 30 min, it takes 30 min.
- Smoke tests are the ground truth for "did Phase 14 actually achieve its goal?" If the router still falls back to rag_search for 9 of 10 queries, the modernization is technically complete but functionally inert. That's the discovery 14G is built to surface.
- After 14G commits, the `PHASE_14_LOCKDOWN_v1_0.md` artifact is the analogue of `GOVERNANCE_BASELINE_v1_0.md` from the 2026-04-24 governance close. It is the new "this is what was true at the moment of seal" record. Going forward, `drift_detector` enforces this baseline; any drift away from it requires explicit unfreezing.
- This brief intentionally does NOT update `CLAUDE.md`. CLAUDE.md amendments for the post-Phase-14 architecture (new tools, new tables, B.1/B.3 layer references after L2.5 became fully structured) are a separate doc-only brief authored after lockdown.
