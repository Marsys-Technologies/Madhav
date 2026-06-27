---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_RUNTIME_VALIDATION
version: 1.0
status: COMPLETE
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF (per CLAUDE.md §C.0 — governing scope for one Claude Code session)
session_type: read-only runtime validation (data-plane) of the retrieval-system design plan
hard_constraint: STRICTLY READ-ONLY. No writes, builds, writer runs, migrations, or mutations of any kind.
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (the plan being validated; §C is the code-plane findings)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md (§4 lists the deferred runtime items this brief executes)
may_touch:
  - read-only DB queries via the localhost→prod Cloud SQL Auth Proxy
  - read-only file/git/gcloud inspection
must_not_touch:
  - ANY write to the database (no INSERT/UPDATE/DELETE/DDL)
  - any build_runner / writer / orchestrator execution
  - any migration apply
  - any deploy or Cloud Run mutation
acceptance_criteria:
  - every check V1–V15 below executed read-only and a verdict recorded
  - findings written back to RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION (a new §5 runtime register) OR a sibling RUNTIME_FINDINGS file
  - no mutation occurred (confirm at close)
---

# CLAUDE CODE BRIEF — RETRIEVAL RUNTIME VALIDATION (read-only)

> **Why this exists.** Cowork validated the retrieval-system design plan against the *code* (see
> `RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION`). Several truths can only be confirmed against the *running
> database* — and the native has confirmed localhost is in complete sync with prod, with Claude Code holding
> the localhost→prod DB access Cowork's sandbox lacks. This brief is the precise, **strictly read-only**
> runtime validation for Claude Code to execute. Writers *existing* in code ≠ data *built* — that gap is what
> this closes.
>
> **The one rule:** read-only. Counts, SELECTs, existence/population checks. NO writes, builds, writer runs,
> migrations, or deploys. The project is under sync-freeze discipline — investigate, never mutate. If any
> check seems to require a write to verify, STOP and report it as "needs-write-deferred," do not perform it.

## Session setup

1. Read the two prereq artifacts above (esp. the code-validation register §1 corrections + §4 deferred items).
2. Start the read-only DB path: `platform/scripts/start_db_proxy.sh` (port 5433 per project infra); read the
   connection string from the repo `.env`/config (do NOT hardcode credentials in the findings file).
3. Canonical native chart_id: **`482012f1-710e-4a25-994a-93821f5871aa`**. The dead phantom `362f9f17-…` must
   appear in ZERO populated rows — flag if it does.
4. Use a read-only session/role if available; otherwise self-discipline to SELECT-only. Confirm at close that
   no mutation ran (e.g. via a wrapping read-only transaction).

---

## The checks (V1–V15)

For each: run the query, record actual result, assign verdict (POPULATED / EMPTY / PARTIAL / ERROR /
NEEDS-WRITE-DEFERRED), and a one-line interpretation.

### A. Writers existing ≠ data built — per-layer population (the core question)

**V1 — L1 Gaṇita populated on the native chart.**
```sql
SELECT count(*) FROM chart_facts WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
SELECT count(*) FROM chart_dashas WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
SELECT count(*) FROM chart_divisionals WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
```
Expect (from L1 closure): chart_facts ≈ 27,554; chart_dashas ≈ 536,471; chart_divisionals ≈ 21,635. Flag any
material divergence (the count_sql-vs-reality trap).

**V2 — L2 Bodha spine populated.**
```sql
SELECT count(*) FROM bodha_msr_signals WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
SELECT count(*) FROM bodha_cgm_nodes  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
SELECT count(*) FROM bodha_cgm_edges  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
SELECT count(*) FROM bodha_contradictions WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
SELECT count(*) FROM bodha_cdlm_cells WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
```
Expect MSR signals on the order of the floor (~66,738) if a full build ran. EMPTY ⇒ L2 schema exists but
unbuilt on this chart — a critical finding for D5.

**V3 — L3/L4/L5 population (the memory said unbuilt; code said writers exist — does DATA exist?).**
```sql
-- L3 (sample the artifact tables; service assets have no table)
SELECT count(*) FROM kala_convergence WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
SELECT count(*) FROM kala_obstruction WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
-- L4
SELECT count(*) FROM phala_nimitta WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';  -- adjust to real table name
-- L5
SELECT count(*) FROM mimamsa_darshana WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'; -- adjust to real table name
```
(Resolve real table names from the seed `target_table` for each ka_*/ph_*/mi_* asset first.) This decisively
settles the "all six layers built" question at the DATA level, not just the code level.

**V4 — bo_samskara embeddings actually populated (not just column exists).**
```sql
SELECT count(*) AS total,
       count(*) FILTER (WHERE embedding_vec IS NOT NULL) AS embedded
FROM bodha_signal_embeddings
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
```
embedded ≈ total ⇒ Vertex embeddings ran. embedded=0 ⇒ retrievability spine empty (blocks hybrid retrieval).

### B. Cockpit-truth / count_sql correctness (read-only)

**V5 — count_sql vs reality.** For 6–8 assets spanning layers, run the asset's actual `count_sql` (from the
seed, substituting the native chart_id for `$1`) AND a direct `count(*)` on its `target_table` scoped to the
chart; compare. Any mismatch = the documented cockpit-lies trap is live for that asset.

**V6 — asset_registry vs reality.**
```sql
SELECT asset_id, layer, storage_type, target_table, scope, is_active FROM asset_registry ORDER BY layer, sort_order;
```
Confirm 81 rows; cross-check layer counts (bg22/ga16/bo10/ka12/ph9/mi12) against the seed. Flag is_active=false
assets and any target_table that doesn't exist in the DB.

### C. The dedup/retrieval surface at runtime

**V7 — `vw_chart_digest` (UCD) returns for the native chart.**
```sql
SELECT count(*) FROM vw_chart_digest WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
SELECT * FROM vw_chart_digest WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' LIMIT 3;
```
EMPTY ⇒ the first-call orientation surface (bo_samvada) has nothing to serve — blocks the umbrella-tool design.

**V8 — `query_ucd` end-to-end (read-only).** Invoke the `query_ucd` tool path (via its test or a read-only
harness, NOT by mutating anything) for the native chart; confirm it returns top-K signals from
`vw_chart_digest` + `bodha_msr_signals`. If only reachable via the running app, hit the localhost read endpoint.
Record whether it returns coherent de-duplicated signals or errors.

**V9 — lel_origin distribution (the toggle's data basis).**
```sql
SELECT lel_origin, count(*) FROM bodha_msr_signals
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' GROUP BY lel_origin;
```
Confirms whether any lel_origin=true signals exist (the toggle is meaningful only if both classes are present).

### D. Spine integrity (read-only referential checks)

**V10 — constituent_facts_array resolves to real L1 facts (§N.5 authority).** Sample 50 signals; for each,
check that the fact_ids in `constituent_facts_array` exist in `chart_facts.fact_id` for the same chart. Any
unresolvable fact_id = a §N.5 violation (a halt-worthy class of bug per CLAUDE.md).
```sql
-- sketch: unnest a sample and left-join to chart_facts; count orphans
SELECT count(*) AS orphan_fact_refs FROM (
  SELECT unnest(constituent_facts_array) AS fid
  FROM bodha_msr_signals
  WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' LIMIT 500
) s LEFT JOIN chart_facts cf ON cf.fact_id = s.fid AND cf.chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
WHERE cf.fact_id IS NULL;
```
Expect 0 orphans. Nonzero = serious.

**V11 — CGM edges reference real signals.** Confirm `bodha_cgm_edges.underlying_msr_signal_ids_array` and
`bodha_cgm_nodes.msr_signal_id` resolve to `bodha_msr_signals.signal_id`. Count dangling references.

**V12 — degenerate-distribution guard (per memory `feedback_degenerate_distribution_guard`).** For a couple of
attribution columns expected to be diverse (e.g. `source_subsystem`, `signature_tier`, edge `relationship_basis`),
check the value distribution is NOT collapsed to a single value.
```sql
SELECT source_subsystem, count(*) FROM bodha_msr_signals
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa' GROUP BY source_subsystem ORDER BY 2 DESC;
```
A single-value collapse where diversity is expected = the hardcoded-fallback bug class.

### D2. Native-contamination runtime check (the chart-agnostic mandate, §D)

A code-plane audit already found CRITICAL native defaults in `platform-mcp/src/tools/` (≥5 tools default a
missing chart_id to the native; `lel_query` serves the native LEL corpus with no chart selector). These checks
confirm the *runtime* blast radius and that the clean new-registry path stays clean. **Read-only.**

**V12b — does omitting chart_id return native data?** For each suspect MCP tool path that the audit flagged
(`kala_temporal`, `holistic_bundle`, `ganita_forensic_render`, `l0_brahmagyan`, `lel_query`), call it (via a
read-only harness/test, NOT against a write path) with chart_id OMITTED and observe: does it return the native
chart's data (CRITICAL — confirms the silent fallback fires) or error? Then call with a DIFFERENT real
chart_id and confirm it returns THAT chart's data, not the native's. Record per tool.

**V12c — cross-chart isolation on the clean path.** Pick two distinct chart_ids; call the NEW registry's
per-chart tools (e.g. `query_ucd`, `get_positions`) for each; confirm results are disjoint and each strictly
matches its own chart_id (no native bleed, no cross-chart bleed). This validates the base we intend to build on.

**V12d — LEL isolation.** Confirm `lel_query` / any LEL path cannot return the native's `lel_origin=true`
calibration when operating on a non-native chart. With `lel_enabled` defaulting false, a non-native chart's
retrieval must contain zero `lel_origin=true` rows.

### E. Deployment + system-convergence reality (read-only)

**V13 — deployed MCP revision vs main HEAD** (per `feedback_verify_cloud_run_revision_before_chrome_probe`).
```bash
gcloud run services describe amjis-mcp --region asia-south1 --format='value(status.traffic[0].revisionName)'
git -C /path/to/repo rev-parse HEAD
```
Note divergence (informational; do not redeploy).

**V14 — the two-system reality at runtime.** Confirm which retrieval code path the live chat endpoint
(`/api/chat/consult`) actually calls — `lib/retrieve` (old, msr_sql) vs `lib/retrieval` (new registry). Read
the route imports; if a read-only smoke is available, confirm. This grounds the D0 convergence decision.

**V15 — manifest staleness confirmation.**
```bash
grep entry_count 00_ARCHITECTURE/CAPABILITY_MANIFEST.json platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
grep generated_at 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
```
Confirm 137 vs 117 + the 2026-06-05 stamp predating migration 325. (Code-plane already found this; V15 just
locks it for the runtime register.)

---

## Output

Write findings to a new section **§5 — Runtime validation register** appended to
`RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md` (bump it to v1.1), OR a sibling
`RETRIEVAL_GROUNDTRUTH_RUNTIME_FINDINGS_v1_0.md`. For each V1–V15: the query run, actual result, verdict,
one-line interpretation, and any design-impact flag for the approach plan (esp. D0 convergence, D5 per-asset,
D8 governance). End with: (a) a "data actually built?" verdict per layer, (b) any §N.5/integrity violations
found, (c) confirmation that **no mutation occurred**.

## Close

Set this brief's frontmatter `status: COMPLETE` when all V1–V15 are executed and findings are written.
Do not claim completion if any check was skipped — mark skipped ones explicitly with the reason.

*End of CLAUDECODE_BRIEF_RETRIEVAL_RUNTIME_VALIDATION v1.0 — strictly read-only.*
