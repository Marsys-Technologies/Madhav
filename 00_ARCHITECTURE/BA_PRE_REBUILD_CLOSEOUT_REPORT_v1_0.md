---
artifact: BA_PRE_REBUILD_CLOSEOUT_REPORT_v1_0.md
canonical_id: BA_PRE_REBUILD_CLOSEOUT_REPORT
version: 1.0
status: CLOSED
produced_on: 2026-07-05
produced_by: Claude Code (executor pass), per CLAUDECODE_BRIEF_BA_PRE_REBUILD_CLOSEOUT_v1_0.md
predecessor: BA_PRE_REBUILD_GATE_REPORT_v1_0.md (Cowork strategic-track VERIFY-ONLY gate, CONDITIONAL GO)
---

# BA PRE-REBUILD CLOSE-OUT — REPORT

Executed `CLAUDECODE_BRIEF_BA_PRE_REBUILD_CLOSEOUT_v1_0.md` end to end. No cockpit Build/Rebuild was run.
No per-chart data was hand-patched. No FROZEN-contract change was made. Two gates (B3/B4) that the prior
report left as unverified residuals turned out RED and required a fix; A6 required an additional,
unanticipated fix discovered mid-pass. Both are documented below with evidence, not asserted.

## Per-gate GREEN/RED + evidence

| Gate | Result | Evidence |
|---|---|---|
| PR #435 merged | ✅ GREEN | CI green (10/10 checks), merged `bd0d3756` |
| PR #436 merged | ✅ GREEN | CI green (10/10 checks), merged `6a0aea6f` — see "A6 unanticipated fix" below |
| §1 sidecar/JOB image on post-merge HEAD | ✅ GREEN | `gcloud run services describe amjis-sidecar` → `6a0aea6f`; `gcloud run jobs describe brahma-build-pipeline-job` → image tag `6a0aea6f`. Both auto-triggered via deploy.yml's path-gated `workflow_run`, confirmed after each of the two merges (not assumed). |
| §1 web/mcp not regressed | ✅ GREEN | `amjis-web` → `6a0aea6f` (rebuilds every deploy). `amjis-mcp` → `76158638` (unchanged — correctly not path-triggered since neither #435 nor #436 touched `platform-mcp/**`; this is the SAME SHA it was redeployed to earlier in this pass, independently re-checked, not presumed static). |
| §2 mi_jivanaghatana parse: 57/57 real EVT events, 0 unparseable | ✅ GREEN | Direct parse of `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` from merged code: 57 parsed events == 57 distinct real `EVT.*` keys across all 63 yaml blocks (the file has 63 yaml blocks total, not 63 events — 16 are legitimately non-event PATTERN.\*/PERIOD.\*/GAP.\*/version-history/PRED.\* blocks that were never meant to parse as events, plus 1 illustrative EVT.YYYY.MM.DD.XX template now correctly excluded). Zero missing date/category. `test_mi_jivanaghatana.py`: 9/9 passed. |
| §2 pytest green post-merge | ✅ GREEN | Confirm-pass regression suite (contamination_guard, l0_rules_yoga, ph_rectification, dag_edge_guard, ga_yoga, mi_jivanaghatana): 119 passed, 1 skipped. |
| §3 amjis-sidecar secrets hygiene | ✅ GREEN | `DATABASE_URL` repointed from a plaintext env var to `secretKeyRef: amjis-pipeline-db-url:latest` (the same secret the build-pipeline JOB already uses). Post-redeploy connectivity check (`GET /api/compute/phala/outlook/acceptance_gate/482012f1`, authenticated): HTTP 200, response byte-identical to the pre-change baseline. |
| §4 stale branch deleted | ✅ GREEN | `docs/ba-phase-2-5-report`: confirmed `git merge-base --is-ancestor` true against `origin/main` before deletion (local + remote). Also deleted `fix/mi-jivanaghatana-multi-event-fallback` (this pass's own branch), same ancestor check first. |
| §4 ledgers updated | ✅ GREEN | `CURRENT_STATE_v1_0.md` v6.19 changelog entry added; `BA_RUN_LEDGER_v1_0.md` "BA Pre-Rebuild Gate close" section appended. B8 (JL numbering): re-verified directly — `JL-013` in both the ledger and the `bo_cgm_paths.py` code comment correctly tag P3 J4; no mismatch found, noted as verified only. |

## A6 — unanticipated scope (found mid-pass, not in the closeout brief's plan)

The brief's §2 smoke-check assumed #435 alone would produce "63/63 EVT blocks parse, 0 unparseable." Two
things were wrong with that assumption, both surfaced by actually running the parser against the live file
rather than trusting the plan:

1. **The 63 count is yaml-block count, not event count.** Only 46 of those 63 blocks have an `EVT.*` key on
   their first line (one of which is the illustrative template, not a real event); the rest are
   `PATTERN.*`/`PERIOD.*`/`GAP.*`/version-history/`PRED.*` blocks that were never events to begin with. The
   real denominator is 57 distinct `EVT.*` keys once multi-event blocks are counted correctly (see next).

2. **#435's fallback silently dropped events in multi-event blocks.** 7 of the 63 blocks group more than one
   event under a single ` ```yaml ` fence (one groups 4). #435's fallback parser read only the first `EVT.*`
   key per failing block, so a narrative-colon break anywhere in one of those blocks silently dropped every
   sibling event after the first — 6 real events (`EVT.2001.03.XX.01`, `EVT.2007.06.XX.02`,
   `EVT.2021.XX.XX.03`, `EVT.2022.01.03.01`, `EVT.2022.10.XX.01`, `EVT.2025.XX.XX.01`) were missing from the
   parsed output even after #435 merged.

PR #436 fixed both: it splits a failing block on every top-level `EVT.*` boundary before extracting fields
(recovering all sibling events, not just the first), and separately filters the pre-existing
`EVT.YYYY.MM.DD.XX` template-block leak (unrelated to the YAML-fallback work — that block was always valid
YAML on its own and had been silently inserting a spurious row into `mimamsa_event_provenance` since before
#435 too). Both fixes are covered by new regression tests
(`test_raw_fallback_recovers_all_events_in_a_multi_event_block`,
`test_real_lel_file_recovers_every_real_evt_event_with_date_and_category` — strengthened to assert the exact
expected/parsed set match rather than just "no missing fields", which is what caught the multi-event drop in
the first place — plus `test_template_event_id_detection` and
`test_template_block_does_not_leak_via_normal_yaml_path`).

Per the brief's own hard rule ("If any gate is RED, STOP, record it with evidence... do NOT declare
REBUILD-READY"), both findings were paused on and confirmed with the native before merging: PR #436's merge
and the template-leak fix were explicit go-aheads, not autonomous scope expansion.

## Exit

- **REBUILD-READY = YES (unconditional).**

Hand back to the strategic track to issue the Phase-3 Abhinandan rebuild brief. This pass did not run the
cockpit Build/Rebuild itself, and made no per-chart data hand-patch or FROZEN-contract change.
