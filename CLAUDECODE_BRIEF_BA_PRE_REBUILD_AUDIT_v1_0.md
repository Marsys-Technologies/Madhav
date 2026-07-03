---
canonical_id: CLAUDECODE_BRIEF_BA_PRE_REBUILD_AUDIT
version: 1.0
status: COMPLETE
created: 2026-07-04
author: Cowork (Beyond-Acharya unified program) — native-requested pre-rebuild gate
program: BEYOND_ACHARYA_UNIFIED_EXECUTION_PLAN_v1_0.md — gate between P3A closure and the native's
  cockpit L1 rebuilds (and therefore P3B)
objective: >
  THREE-TRACK THOROUGH AUDIT before the native clicks Rebuild: (A) the Nirmāṇa build path — every new
  asset, DAG edge, writer, and governance surface wired so the L1 rebuild works as seamlessly as it
  always has; (B) the modernized retrieval/MCP estate — efficiently wired, envelope-correct, and proven
  to serve an LLM properly end-to-end; (C) the full implementation scope to date — astrological coverage,
  asset coverage, completeness, retrievability, tool design — one complete pass. READ-ONLY: findings,
  never fixes (fixes get their own follow-up brief). Output = BA_PRE_REBUILD_AUDIT_REPORT_v1_0.md with
  GO/NO-GO for the rebuild.
grounding: BA_GROUNDING_REPORT_v1_0 + RUN_LEDGER §4B (P3A gates) + the nine root briefs' exit criteria
may_touch: ["00_ARCHITECTURE/BA_PRE_REBUILD_AUDIT_REPORT_v1_0.md (create)", "CURRENT_STATE append", "read access everywhere", "transaction-wrapped probes that ROLL BACK"]
must_not_touch: ["any functional code", "any migration", "any data write outside rolled-back transactions", "deploys", "the cockpit Rebuild buttons (the native triggers those AFTER this report)"]
---

# BRIEF BA-PRE-REBUILD-AUDIT — full-portal gate before the L1 rebuilds

> Every item: VERDICT (PASS / FAIL-with-detail / N-A-with-reason) + EVIDENCE (file:line, SQL, HTTP,
> screenshot). Severity on failures: BLOCKER (stops the rebuild) / MAJOR (fix before P3B) / MINOR (log).

## TRACK A — NIRMĀṆA BUILD-PATH READINESS (will the rebuild work seamlessly?)

A1. **Registry integrity for ALL assets touched since the program start** (bg_class_priors, bg_ghatana,
    bg_formula_constants + the 4 EXT'd L1 assets): row present · correct layer + sort_order ·
    scope correct (global vs per_chart) · `count_sql` VALID (execute each against prod: global ones
    return counts, per-chart ones with $1 bind for both charts — a broken count_sql is the cockpit-lies
    trap C4) · has_writer=true · sanskrit/english names render.
A2. **DAG correctness:** dump depends_on for the full graph; verify (a) the 3 new L0 assets are roots
    with no cycles; (b) L1 EXT'd assets' edges unchanged (no accidental new dependencies); (c) the
    planner's computed order for a "Build L1" on each chart INCLUDES ga_sensitive/ga_dashas/ga_strength/
    ga_condition; (d) no orphan edges referencing non-existent assets.
A3. **Planner dry-run (no execution):** call the plan endpoint (or invoke the planner module directly)
    for chart 1c826d5a "Rebuild L1" — capture the exact ordered step list it WOULD run. Verify all 4
    EXT'd writers present, heavy writers show per-ayanamsha substeps, and no L2+ assets appear unless
    cascade is explicitly opted in (verify cascade is OPT-IN and default-off — a rebuild must not
    silently destroy L2).
A4. **Writer conformance re-check on the 4 EXT'd + 3 new writers:** @register present · run/plan_substeps
    signature · NEVER commits/closes ctx.db_conn · no asset_throughput writes · **CRITICAL: the
    delete-then-insert natural-key scope in each EXT'd writer INCLUDES the new fact_categories**
    (bhava_arudha, chara rows, per-varga sthana bala, sayanadi/lajjitadi/yuddha) — if the delete scope
    misses them, a second rebuild ACCRETES duplicates; if it over-matches, it deletes other writers'
    facts. Quote the DELETE predicates verbatim per writer. This is the single most rebuild-critical check.
A5. **Idempotency proof (transaction-wrapped, rolled back):** on Abhinandan, run ONE EXT'd writer's
    delete+insert cycle twice inside a transaction, compare row counts + a checksum between cycles →
    identical → ROLLBACK. (If infra prevents a safe in-txn run, downgrade to static analysis + note.)
A6. **Build-tracker truth:** stats route reads count_sql (live mode) · Clear nulls
    asset_throughput.rows_written · SSE progress events fire on the plan · dd-MMM-yyyy formatting intact.
A7. **Cockpit UI:** all registry assets render on the build page (registry-driven tree) ·
    LiveDependencyGraph + AssetTable show the 3 new L0 assets (ASSET_NAMES/ASSET_MAP entries per PD-5 —
    verify the 4 entries added and explain the 4th) · visual check vs the PG baseline screenshot ·
    Nirmāṇa access control intact (owner/super_admin build; view-grantees read-only).
A8. **Governance compliance:** schema_validator exit=0 · drift_detector clean (manifest mode) ·
    CURRENT_STATE + SESSION_LOG entries for P0/P1/P2/P3A consistent (session ids, close blocks) ·
    L1_GANITA_CLOSURE seal-amendment note present for the P3A EXTs · all root brief statuses accurate ·
    migrations 385–389 in the applied table AND in exactly one migrations dir each (no dual-dir dupes).
A9. **Rebuild blast-radius statement:** write down, from code, exactly what "Rebuild L1" deletes and
    recreates per chart (tables + row scopes), what it does NOT touch (L2–L5 tables), and the expected
    post-rebuild counts (chart_facts ≈27,554 + new categories: quantify expected additions incl.
    bhava_arudha 12×5). The native reads this before clicking.

## TRACK B — RETRIEVAL/MCP MODERNIZATION AUDIT (is the estate wired for an LLM to work properly?)

B1. **Census + alias integrity:** enumerate registered tools at HEAD (expect ~70 primaries + aliases);
    for 10 sampled renamed tools, call OLD name and NEW name → identical payloads (one handler).
    Dedup verified: bodha_remedies_search aliases into bodha_remedies_get.
B2. **Envelope conformance:** for every NEW P1 tool + the 4 apex tools: envelope fields present
    (tool_uri, query_context w/ insight_type+query_class, structured content, ranking_basis
    [populated post-P2 — verify sub-scores + composite + priors_version], grounding block w/
    fact_ids + citations + grounding_score, pagination, drill_pointers, judgment_flags). List any tool
    still returning pre-envelope shapes.
B3. **Query-time ranking live-state (P2):** bodha_signals_get(482012f1, career, 10) → ranking_basis on
    every row; ZERO ashtakavarga atomic tallies in top-10; ≥3 yoga-class; percentile-in-class present;
    no tie-block >3. Repeat for wealth + health domains (the G10 test generalizes). Cache: repeat call →
    hit + latency delta; verify TTL keys on dasha boundary.
B4. **Bounding + performance:** apex_career_assess default ≤ its cap; Mahā-Brief precursor calls within
    budget; p50/p95 spot-table for 6 tools vs the P0 baseline (no regression >10%).
B5. **Grounding + honesty:** sampled signals' fact_ids resolve against chart_facts (spot 200);
    judgment_flags truthfully report known gaps (kala empty until P5A, calibration prior_only);
    citations resolve to real chunks (sample 10 through ref_classical_citation_get).
B6. **THE LLM END-TO-END PROOF (the point of it all):** execute the full INTERPRETATION workflow over
    MCP as a real client would — nav → bodha_chart_digest_get → bodha_domain_reading_get(career) →
    bodha_signals_get → ganita_strength_get(Saturn) → ganita_structural_get(yoga_fires) →
    ganita_yogas_get → ref_classical_citation_get — then have the product-policy LLM (Gemini/DeepSeek)
    synthesize a career reading from the retrieved envelopes. Score with the G10-QT rubric (/15) + note
    every friction point (missing field, unclear description, oversized payload, broken drill_pointer).
    Repeat once on 1c826d5a (outputs must differ — contamination).
B7. **Two-chart distinctness + entitlement:** rankings/readings differ across charts; entitlement gate
    still blocks unentitled chart ids; session flows (nav select) work.

## TRACK C — SCOPE-OBJECTIVE COMPLETENESS (the "everything and beyond" pass)

C1. **38-topic astrological reachability matrix** (RM §7 list) on 482012f1: per topic → serving tool →
    VERDICT on the four measures (Volume/Relevance/Accuracy/Ranking), with "reachable-pending-data"
    explicitly marked for P3B+ topics (promise register, triangulation, activation, anchors-v2).
    This is the single most important table in the report.
C2. **Asset coverage recount:** all registry assets vs tool coverage — uncovered ≤6, each with its
    documented deferral reason still valid.
C3. **Program scoreboard:** for P0, P1, P2, P3A — re-verify each brief's exit gates with fresh prod
    probes (not ledger citations): P0 caps+cache, P1 wiring smoke, P2 G10-QT + prior_version=1.0
    frozen + committed, P3A gates (a)–(f) incl. the bhava_arudha DEFERRED state. Any gate that no longer
    passes = MAJOR.
C4. **Doctrine + traps sweep:** salience is a column never a filter (grep serving paths for
    threshold-drops) · tail queryable · no NEW judgment constants introduced as literals by P1–P3A code
    (diff against bg_formula_constants consumers) · no new embedded weight sites · no second combustion
    orb · stored vs query-time split honored (no activation baked into stored columns) · scoring paths
    LLM-free where P6 will need them.
C5. **Seed integrity:** brahma_class_priors 164/165 rows (explain the discrepancy between the P3A report's
    "165" and RUN_LEDGER's "164") · event ontology 22 + activity 12 rows complete w/ signature models +
    base rates + adjacency · formula constants 11 rows w/ citations + bounds · priors_version=1.0
    matches the P2T-frozen values in the seed package (row-level diff).

## OUTPUT — 00_ARCHITECTURE/BA_PRE_REBUILD_AUDIT_REPORT_v1_0.md
§1 verdict table (every item A1–C5) · §2 evidence · §3 findings register (BLOCKER/MAJOR/MINOR w/
proposed fix + owner phase) · §4 the A9 blast-radius statement (native-facing, plain language) ·
§5 GO/NO-GO: (i) the two cockpit L1 rebuilds, (ii) P3B start post-rebuild · §6 CURRENT_STATE append.
**Acceptance: zero UNKNOWNs; A4 + A3 evidenced verbatim; B6 executed with scores; report committed;
status → COMPLETE. The native rebuilds ONLY on a GO with zero BLOCKERs.**
