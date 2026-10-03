---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.26"
status: "FINAL for dispatch (round 21, narrow) — SHORT DELTA on v1.25 closing Codex round 20 (R20-1..4) and Fable round 20 (F-R20-1..5): #2996 now carries a narrow SECURITY DEFINER evidence function inside the unapplied migration 1243 and evaluates the candidate exclusion against the COMPLETE registry; the window-only merge-control composition is recorded (v1.25's merge-control claim for the integration tree is WITHDRAWN); checklist v1.3; runbook v1.19."
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-03"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.25 (never edited)."
---

# A5.5 gate — round-21 request: delta

## Heads
#2996 **`324b8c9686185a1be22c7be30998cf5210780bfe`** (branch `pravaha/b7-inert-registry-rows`; migration 1243 sha256 **`bb6a7a33bf1f1928cdd4bc45e0ea46de9e1e70480af8d2baa2bd0ac952f80556`**, was `88be3ed5…`; the last commit is a comment) · window-only merge-control composition **`50f87cb6f64716713725154e90acc9085de0b6f0`** (ref `pravaha/b6-window-only-merge-control`) · Stream A's #2999 branch `pravaha/a53-am5-inventory` **`b0de7f12f`** (test-only fix by Stream B) · #2961 `8a204a7b1`, #2903 `5a46c9c97`, integration `20ad1bd6e`, exhibit `a6e4afb45` — all unchanged since v1.25 (no composed re-run: nothing the composed list exercises changed) · docs `campaign/pravaha`.

## By finding
| finding | status | evidence |
|---|---|---|
| **R20-1 (P2)** build_run_assets proxy unsound (refresh inserts throughput with no run; the watchdog prunes build_run_assets) | **DONE — Suvarṇa's option (a)** | `public.ka_gochara_staged_candidate_has_runtime_evidence(text) RETURNS boolean` INSIDE 1243: plpgsql STABLE SECURITY DEFINER, `SET search_path = pg_catalog, pg_temp`, tables schema-qualified; checks asset_provenance_receipts, build_run_assets AND asset_throughput; any other id (and NULL) RAISES; owner amjis_app; `REVOKE ALL … FROM PUBLIC`; EXECUTE only amjis_app and nirmana_campaign_control_writer; the migration's own post-checks assert owner, prosecdef, proconfig, an ACL with no PUBLIC entry and no other grantee, that it runs and refuses `bg_texts`. ONE expression in every loader (monitor, snapshot, five definitions loaders): `CASE WHEN id IN (the two) THEN function(id) END`; NULL/unknown/absent never excludes (`=== false` only). **Error handling stated honestly:** a function error or denial makes the registry SELECT fail (the read fails closed; the candidate is never silently excluded) — not "continue as evidence present" (a failed statement aborts the enclosing SERIALIZABLE transaction). |
| **R20-2 (P2)** supporting writers removed before the candidate rule | **DONE** | `excludeNirmanaStagedInertCandidates(rows)` runs on the COMPLETE registry first, then supporting writers are removed — in `buildNirmanaBaselineCandidate` and in `elevationDenominatorRegistryRows` (both comparisons). Tests through the actual callers: bo_grounding depending on EACH candidate, active and inactive ⇒ candidate not excluded, baseline throws, both comparisons report the extra identity; a non-depending bo_grounding stays out of the denominator and the inert candidates stay excluded; the RETIRED identity is retained. |
| **R20-3 (P2)** packet claim about WINDOW_MERGE_CONTROL on the integration tree | **WITHDRAWN and replaced** | The integration tree carries 1241 and lacks 1243 — it never passed that mode. The WINDOW-ONLY composition (current `main` + #2996 + #2961 + #2963 + #2867 + #2919 + a53 `b0de7f12f`, no 1241; the two a53 test-file conflicts with `main` taken from `main` with `-X ours` — Stream A owns the real resolution) at `50f87cb6f…`: all ten window hashes OK, `1243` present, no `1241_*`, five selection entries, `WINDOW_MERGE_CONTROL=1 … gochara_window_dispatch_selection.test.ts` = 8 passed. Checklist row 7 step (1) now includes `npm ci`; the grep pattern is the exact five (`12(04|06|32|33|40)_`; the looser one also counted 1202). |
| **R20-4** capture root shape; v5 exclusion text | **DONE** | Runbook: root `{chart_id, build_id, selection, rows, natal, meta, sha256}`, census under `meta.census`; the staged candidates' exclusion property is `is_active=false` after 1243 (runbook and decision doc). |
| **F-R20-1** merge-control claim | DONE | as R20-3. |
| **F-R20-2** throughput deviation | **SUPERSEDED by R20-1** | the function reads asset_throughput for every role; no proxy remains. |
| **F-R20-3** the exclusion's expiry | **DOCUMENTED** (runbook v1.19 + the code comment at `NIRMANA_STAGED_INERT_CANDIDATES`) | a successful real v4.1 run persists a receipt the teardown does not delete; the exclusion ends permanently; remedy in the same change: retire or adjust its frozen-population status (Suvarṇa). Teardown change not made (Kimi's C27 owns it; the steward's instruction was to document). |
| **F-R20-4** readback | **DONE** | `registry_1243_readback.sql`: proowner / prosecdef / proconfig / provolatile / return type, the ACL rows (no PUBLIC), zero receipts / build_run_assets / throughput for the two ids, the function's two answers, the latest monitor statuses. |
| **F-R20-5** wording | **DONE** | freeze carve-out for #2996 (C27 on main at `b97536e0f`; #2996's own deploy must be green); row 8 "the apply step's log applies exactly …" (no plan step exists); `not_migrated` display note; deploy.yml lines cited as the file the sitting reads. Post-window list: `cockpit/refresh/route.ts:56–69` route gap. |

## Tests (#2996)
DB-backed on a disposable PostgreSQL 15 (roles amjis_app / control writer / outsider; the control writer holds NO SELECT on any evidence table): no rows ⇒ false; refresh-only throughput ⇒ true; build_run_assets ⇒ true; PRUNING (build_run_assets deleted, throughput remains) ⇒ true; receipt ⇒ true; other ids and NULL raise; owner/secdef/search_path/ACL; the app role and the control writer get IDENTICAL loader-expression results; an outsider is denied loudly; missing function ⇒ UndefinedFunction. Static: exactly one INSERT, one CREATE OR REPLACE FUNCTION, one REVOKE, two EXECUTE grants, no table privilege. TS: 366 pass in `src/lib/nirmana-elevation` (incl. a source guard that all seven loaders carry the expression and the 128-row digest-stability test), tsc clean. Mutation: removing the REVOKE fails 7 DB tests.

## Also
#2999's CI failure (12 × "permission denied for table ka_gochara_search_inventory_verification") was a stale AM-14 suite: the builder holds no privilege on that table (PC-4); the suite now writes the verification AS `gochara_verifier` like the 1206 suite (test-only, no grant widened; AM-14 suite 15/15 locally).

## Not done / not claimed
The function and 1243 are unapplied; the readback is a procedure, not a result. Census/E6 tests were green on the earlier #2996 head (4674) and are re-run by CI on this head — not re-run locally. Official capture not taken; the real merge of the train and the a53 conflict resolution are Stream A's / the sitting's. Nothing merged, queued, dispatched, applied or built by me.
