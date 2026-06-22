---
artifact: L4_PHALA_PR328_REVIEW_v1_0.md
canonical_id: L4_PHALA_PR328_REVIEW
version: 1.0
status: CURRENT — Cowork review of PR #328 (the autonomous L4 build); REQUEST-CHANGES
authored_by: Cowork 2026-06-22
pr: https://github.com/amonty84/Madhav/pull/328
head_sha: cf4089f4bde9e36bebbd8bec460defb9196a99f2
role: >
  The verified review of PR #328 — the fully-autonomous L4 Phala build the swarm produced. Reviewed
  against the actual branch contents (not the swarm's self-report, and correcting an API-truncation
  false alarm). Verdict: strong build, NOT mergeable as-is — one hard runtime blocker + one scope
  divergence to resolve + CI not yet run.
---

# PR #328 — L4 Phala Autonomous Build — Cowork Review

## §0 — Method note (why the first pass was wrong)
The GitHub `pull_request/files` API **truncates at ~33 files** for large PRs. A first scan of that
truncated slice falsely concluded "migrations missing / registry missing / U4 missing." **Direct
branch-file fetches disproved that** — the migrations, U4 engine, and registry all exist on
`feature/l4-phala-autonomous`. This review is based on the actual branch files, not the truncated diff
or the swarm's self-report. Lesson: for a large autonomous PR, verify against the BRANCH, not the
files-API slice.

## §1 — What's genuinely strong (verified file-by-file)
- **The critical `services/` Dockerfile fix is IN** (`Dockerfile.pipeline` +5: `COPY ...services/`
  with the readiness-doc comment). The silent-hang risk I flagged is fixed. ✅
- **8 ph_* writers + 8 service engines** all present, correctly scoped; only `ka_sangam` touched on the
  L3 side (sanctioned). No sealed-layer violations, no stray writes.
- **Migrations 330–336 + 338–340 are REAL, high-quality DDL:**
  - 330 `phala_anchors` — full schema, all 8 axes + 5 elevations as columns; **DROPs kala_timeline** (CF.L3.2). ✅
  - 333 `phala_sodhana` — `auto_action` DB-CHECK locked to `stage_for_review` (D43a leakage-firewall enforced in schema). ✅
  - 335 `phala_sankrama` — grounded-timing + graph-bridge columns; `cascade_depth` CHECK ≤3 (D44; formula retired). ✅
  - 336 `phala_pramana` — explicit no-scoring discipline; names `D5ViolationError`; no calibration column. ✅
  - 340 `school_consensus_tables` (U4) — all 4 tables, chart-scoped, `temporal_scope` disagreement class
    with `is_timing_refinement_signal` GENERATED column (D36), authority-weighting columns (E2). ✅
- **U4 `chart_data_adapter.ts` is real + well-built** — live `buildChartData` from chart_facts,
  `DOMAIN_AUTHORITY_WEIGHTS` (D36/E2), `buildSchoolSignals` from `school_signal_coverage`, the Tājika
  Task-B resolver. De-hardcoded as specified. ✅
- The hard gates are enforced **in code/schema**, not just spec'd (leakage-firewall, no-scoring,
  no-auto-override, model-policy CHECK, cascade-depth).

## §2 — BLOCKERS (must fix before merge)

### B1 — Migration 337 (`phala_outlook` / ph_phaladesa) is a STUB — HARD RUNTIME BLOCKER
`337_phala_outlook.sql` is 304 bytes, verbatim:
> `-- STUB: actual DDL written by ph_phaladesa implementation (P7)` / `-- [PLACEHOLDER — P7 ph_phaladesa writer will fill this in]`
There is **no `CREATE TABLE phala_outlook`.** But the ph_phaladesa writer (309 lines) does
delete-then-insert into `phala_outlook`. **At runtime the finale asset fails — `relation "phala_outlook"
does not exist`.** The writer's unit tests (36/36) pass because they mock the DB, so the green-tests
report masked this. **Fix:** write the real `phala_outlook` DDL in 337 (the brief §4 schema is the spec:
outlook_id, horizon_tier, question_lens, apex_item_jsonb, woven_narrative_scaffold_jsonb, the three
honest registers, composed_sub_asset_ids, claim_trace_jsonb, narrative_text + narration_model CHECK).

### B2 — ph_sodhana / ph_suddha_sodhana — SCOPE DIVERGENCE (rectification → anomaly registry)
The brief specified `ph_sodhana` = **birth-time rectification** (PyJHora ascendant scan over candidate
times, scored against life events, leakage-firewall, confidence interval — D41). But migration 333
builds `phala_sodhana` as a **prediction-quality ANOMALY REGISTRY** (confidence-inflation /
magnitude-drift / falsifier-absent / ledger-gap / layer-leakage detection). Same for the manifest's
`sodhana`/`suddha_sodhana` rename. **The birth-time rectification capability appears NOT to have been
built** — the swarm reinterpreted "sodhana" (cleansing) as anomaly-cleansing of the predictions, not
chart rectification. This is a genuine product divergence: rectification (the "is 10:43 the right birth
time?" answer, native-ratified G-RECT/D12) is missing. **Resolve:** confirm whether (a) rectification
was intentionally descoped, or (b) it must be added (then 333/334 + the writers need rework to the D41 spec).

### B3 — CI has not run (status: pending, 0 checks)
The "211 tests pass" is worktree-self-reported; **no CI check has fired on the head SHA.** Per the
autonomy model, CI-green is a merge gate. The migration-CI (do 330–340 apply cleanly against a fresh DB?)
+ the full pytest suite must run green before merge. (The 337 stub means migration-CI may actually pass
the apply step but the build/data-gen step would fail — confirm the migration-CI covers an actual orchestrator run, not just `migrate.ts`.)

## §3 — Verify-before-merge (not yet confirmed; likely OK)
- **Registry seed** (`asset_registry_seed.ts`, 106K, on the branch) — confirm the 8 ph_* rows carry the
  UPDATED depends_on + the new target_tables (phala_sankrama/pramana/outlook) + `$1` count_sql. (Fetch
  blocked on tooling size; verify directly.)
- **Test-count discrepancy:** PR title "153+", body "211", report "211" — reconcile (cosmetic, but
  signals the self-report wasn't fully consistent).
- **Per-wave test files:** the report lists W3–W7 suites; confirm they're on the branch (the truncated
  diff showed only `test_ph_nimitta_spine.py`).
- **kala_timeline drop ordering:** 330 DROPs it — confirm nothing applied after 325 re-created it.

## §4 — Verdict
**REQUEST CHANGES.** This is a strong, largely-complete autonomous build with the hard gates genuinely
enforced in code — but it is **not mergeable** until: **B1** (write the real 337 DDL — hard runtime
blocker), **B2** (resolve the rectification scope divergence — native call), and **B3** (CI runs green,
incl. a real orchestrator build, not just migrate-apply). §3 items verified alongside.

The autonomy model worked well; the seal gate + this review caught what the swarm's self-report missed —
exactly the L3-lesson discipline (verify the artifact, not the "SEALED" claim).

---
*End of L4_PHALA_PR328_REVIEW v1.0. Strong build; REQUEST-CHANGES on the 337 stub (runtime blocker),
the sodhana rectification scope divergence, and CI-not-run. Migrations + U4 confirmed REAL (the
"missing" first pass was an API-truncation artifact).*
