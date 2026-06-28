# Build-ID Isolation Diagnostic + Idempotency Root-Cause — Claude Code Brief

> Paste into Claude Code. This is a DIAGNOSTIC session — investigate-only, NO data-fixes to writers yet, NO rebuild. Goal: determine whether the post-regen audit's "10 fixes DID-NOT-TAKE" verdicts are REAL code bugs or MEASUREMENT ARTIFACTS of a chart_facts table containing two coexisting build_ids. Then root-cause the idempotency bug that produced the two build_ids. Read `CLAUDE.md` + `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` + the audit `00_ARCHITECTURE/ABHINANDAN_POST_REGEN_DATA_AUDIT_v1_0.md` first.

## 0 — The hypothesis to test
The audit (`ABHINANDAN_POST_REGEN_DATA_AUDIT_v1_0.md`) found Abhinandan `1c826d5a` `chart_facts` has TWO build_ids: `b806295a` (14,726 rows, 09:59 UTC) + `2954e04c` (115,486 rows, 12:11 UTC). The idempotent delete-before-insert did not clear the prior build. **Therefore every distribution the audit computed (salience tiers, domain counts, contradiction counts, etc.) was measured across a STALE+NEW mixture — the verdicts may be invalid, not the fixes.** `_idempotency.py:3-6` confirms the `chart_facts` unique key includes `build_id`, so a fresh build_id APPENDS rather than overwrites unless the delete helper fires correctly.

This session decides: contamination-artifact vs real-bug — cheaply, before any fix swarm.

## 1 — SCOPE & CONSTRAINTS
- **Investigate-only.** No writer fixes, no rebuild, no data writes in PART A/B. The ONLY permitted write is in PART C if explicitly approved (the idempotency code fix) — but PART C is code+test only, still no data-plane regeneration. Default: produce a diagnostic report + a go/no-go recommendation.
- Read Abhinandan `1c826d5a`; read native `482012f1` read-only for the parallel 5-build_id check. Never write chart data.
- Ground truth: internal-consistency + FORENSIC (no external oracle).

## PART A — BUILD-ID ISOLATION (the decisive test)
Re-run the audit's key per-fix checks but **scoped to the NEWEST build_id alone** (`2954e04c`), excluding the stale `b806295a` rows. For each, compare "newest-build-only" vs "all-rows (what the audit measured)":

1. **First, map which tables even have the build_id problem.** For every L1–L5 table with a `build_id` column, count distinct build_ids for `1c826d5a` and list each with row count + timestamp. (The audit said chart_facts=2; most others=1. Confirm exactly which tables are mixed — only mixed tables have invalid measurements.)
2. **B2 salience — the highest-stakes recheck:** within `bodha_msr_signals` for the newest build only, compute the salience distribution + tier histogram. Does it stratify (multiple tiers, range crossing the `_signature_tier` ≥3.0 threshold)? Note: `bodha_msr_signals` was reported as 1 build_id — so if salience is flat HERE, it is NOT a build-id artifact and B2 is a REAL bug. **This single check is the most informative in the whole session** — it tells us whether the contamination theory holds for the L2 layer where most "did-not-take" fixes live.
3. For each "DID-NOT-TAKE" fix (B3 contradictions, B4 domain, B5 discovery timing, B8 broker, B9 muhurta, O4 argala, O6 Pratyantar, O7 Mode D): determine whether its table is single-build_id or mixed. If single-build_id, the audit's verdict stands (real bug). If mixed, recompute on the newest build_id alone and report the corrected verdict.
4. **Produce a corrected per-fix verdict table:** REAL-BUG (fails even on clean newest-build data) vs ARTIFACT (passes on newest-build-only, failed only because of stale-row mixing) vs STILL-MIXED-CANT-TELL.

**Key insight to apply:** most L2/L3/L4 tables were reported single-build_id in the audit — which would mean B2/B3/B4/B8 etc. are likely REAL bugs, not artifacts, because their tables weren't mixed. The contamination may be confined to `chart_facts` (L1). VERIFY this — it determines how big the real fix list is. Do not assume; the audit's build_id-per-table notes may be incomplete.

## PART B — IDEMPOTENCY ROOT CAUSE (the P0 real bug, regardless of Part A)
The two-build_id situation is a genuine data-integrity bug independent of Part A's outcome. Root-cause it in code (read-only):
1. Read `platform/python-sidecar/ga_writers/_idempotency.py` fully — `replace_prior_chart_facts` and siblings. The delete is scoped to `(chart_id, fact_category)`. Determine WHY build `2954e04c` did not delete build `b806295a`'s 14,726 rows:
   - Did the second build write a DIFFERENT set of `fact_category` values than the first, so the delete (scoped to the categories the SECOND build is about to write) never touched the first build's categories? (The audit noted 14,726 vs 115,486 — very different magnitudes; the stale 14,726 may be categories the new build no longer emits.)
   - Was the delete helper actually CALLED by every writer on the orchestrator path, or does some writer skip it?
   - Did an error mid-first-build leave a partial 14,726-row build that the second build's category-scoped delete couldn't see?
2. Determine the correct fix DIRECTION (do not implement yet unless PART C approved): should the rebuild delete ALL prior rows for `chart_id` (full wipe per chart before rebuild) rather than category-scoped? Or should clear/rebuild explicitly purge stale build_ids? Weigh against the FROZEN contract + the delete-then-insert standard (§N.3).
3. Check the native `482012f1` (read-only): confirm the 5-build_id situation, list them, and confirm it's the same root cause (so the fix is universal, not chart-specific).

## PART C — (ONLY IF NATIVE APPROVES AFTER seeing PART A/B) idempotency code fix
If and only if the native approves: implement the idempotency fix (code + test, fail-before/pass-after), commit/merge/deploy. NO regeneration in this session — the clean rebuild is a separate approved step. Stage it so the NEXT regeneration produces a single build_id per table.

## DELIVERABLE — diagnostic report (`00_ARCHITECTURE/BUILDID_ISOLATION_DIAGNOSTIC_v1_0.md`)
- **§A — build_id map:** every L1–L5 table, distinct build_ids for `1c826d5a`, which are mixed.
- **§A — corrected per-fix verdicts:** REAL-BUG vs ARTIFACT vs CANT-TELL, with the newest-build-only evidence. Headline: the B2 salience verdict on the clean L2 slice.
- **§B — idempotency root cause:** exactly why two build_ids coexist, the fix direction, native parallel.
- **Bottom line + recommendation:** how many of the 10 "did-not-take" are REAL after de-contaminating the measurement → the actual size of the second remediation round. Plus the go/no-go on the idempotency fix.
- NO data writes; NO rebuild. (PART C code fix only if approved.)

## GUARDRAILS
Investigate-only by default (PART C code-fix only on explicit native approval, still no regeneration). Never write chart data; read native read-only for the parallel check. Internal-consistency + FORENSIC. Distinguish correct-by-design (calibration n=0, etc.) from real defects. Every corrected verdict rests on a concrete newest-build-only query. Honest uncertainty over false confidence. If you write the report + (approved) code, SESSION_LOG heading `## <SESSION_ID> — <date>, <status>` (id first, no "Session" word, no colon, no embedded `"` in YAML lists).
