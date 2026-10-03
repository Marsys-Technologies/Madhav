---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.27"
status: "DRAFT for dispatch (FINAL narrow round 21) — SHORT DELTA on v1.26: #2996 MERGED as rows-only 1243 + ONE evidence predicate; 1235 is OUT of this window (the window is the accepted FIVE files); checklist v1.7 (positive privilege readback in row 9, both-roles-exist STOP in row 7, act 9 by the steward under the owner's ruling); a monitor finding about a THIRD pre-existing row. The C29 window-only composition SHA is to be inserted when Kimi reports and B has verified it (marked below)."
author: "Stream B (Śāstra) — Exec B (Claude Sonnet)"
date: "2026-10-03"
reviewer: "Codex gpt-6-astra (max) — dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.26 (never edited)."
---

# A5.5 gate — final narrow round-21 request: delta since round 20

## Heads
Stream A `pravaha/a53-am5-inventory` **`6f29d9afe`** (its CI repairs with the new lock are Stream A's report, not re-derived here; a later head will be relayed as its own delta) · **#2961 `6ab0f2f5f77c875603552d8be323a6a99e436fb7`** (selection = exactly the five window files; origin/main merged) · #2867 `e4d31c9ef`, #2919 `ada3a8fbe`, #2963 `9bbad986a` (unchanged) · #2903 `5a46c9c97` (unchanged since round 20) · `main` `7d1130703` (contains #2996 at `5507df373`) · docs `campaign/pravaha` `bbcfde483`.
**Window-only merge-control composition (Kimi C29, branch `pravaha/c29-window-only-merge-control`): SHA `<TO BE FILLED when Kimi reports; B verifies independently: ten hashes, no 1241_*, executing selection test with WINDOW_MERGE_CONTROL=1, trigger manifest>`.** B's own earlier local cross-check composition (not pushed, not the evidence): `387690cb7ef710cffb793f114376deefa0409a9b` — ten hashes OK, 1243 present, no 1241, five selection entries, merge-control test 8 passed.

## What changed since round 20
| item | state | evidence |
|---|---|---|
| **#2996 / migration 1243** | **MERGED `5507df373`, APPLIED** | rows-only (one INSERT … ON CONFLICT DO NOTHING + post-checks; no function/grant/DDL), sha256 `88be3ed59aaa0685d65e9b8b6607f3787c3ae65a5e8fb96d51f09ebe63798321`; ledger id 925 at 15:57:01Z (steward). One predicate in every loader (monitor, snapshot, five definitions loaders incl. the ingress path): receipts OR build_run_assets for the two ids, exclusion only on `=== false`; R20-2 (complete registry first); pruning limit and the every-real-dispatch commitment documented in code and PR; Codex narrow checks v1.0–v1.2 closed. Registered in Suvarṇa's `registry_depends_on_migrations.json` (one line). B's read-only readback today: both rows seed-parity fingerprints, 131 registry rows / 124 writers, zero dependents, zero evidence rows. |
| **1235 (evidence function)** | **OUT of this window** | steward decision: the window is the accepted FIVE files; 1235 (DRAFT #3018, HOLD) becomes a later, separately reviewed protected dispatch. Removed from the hash list, the rehearsal script, the privilege readback and the checklist; #2961's selection reverted to five. |
| **Checklist v1.7 / runbook** | DONE | row 7: PRECONDITION `gochara_verifier` and `gochara_sealer` EXIST (1240's role-guarded grants skip an absent role and the migration still commits); row 9: POSITIVE privilege readback (92 grants of 1206 §7 / 1240 §7, generated mechanically by `generate_window_privilege_readback.py`, self-tested on a disposable PostgreSQL, zero rows expected, any row = STOP) + `has_schema_privilege('amjis_app','public','CREATE')` = false; act 9 is dispatched by the STEWARD under the owner's account on the owner's ruling 2 of 2026-10-03 (`decisions/NATIVE_DIRECT_RULINGS_20261003.md`), reported immediately, no separate human "yes" at the moment of dispatch; release gate recorded satisfied. |
| **Privilege audit (Suvarṇa's mirrored-role audit; B's read-only grant audit)** | DONE | every GRANT in 1206/1240 is issued by `amjis_app`, owner of every target (30 relations + the five functions verified in production), so the silent no-privileges-granted WARNING cannot occur; the window obtains CREATE by the same bounded path as Suvarṇa's tested one (`jataka-schema-capability.ts`: migrator → SET LOCAL ROLE data_plane_schema_owner → GRANT CREATE to amjis_app; revoke `always()`); the residual risk is ORDER (roles before the window) — now a STOP. |

## A FINDING for the reviewers (not caused by this window or by 1243)
`nirmana_elevation_monitor_observations`: the monitor has read **`source_unavailable` at every 5-minute observation since 2026-09-24** (last other status `evidence_refresh_required` 2026-09-24 08:55), including every observation before and after 1243's apply. Offline reproduction with the MERGED `buildNirmanaBaselineCandidate` on production's actual 131 registry rows (read-only copy): it throws `Frozen manifest asset ka_gochara_v3_century_materialize cannot retain an unresolved execution obligation`; of the three `unresolved` assets the merged exclusion correctly removes the two staged candidates, and the baseline constructs (127 assets) once `ka_gochara_v3_century_materialize` is also set aside. So #2996's exclusion works on real rows; a third, older inert Gochara row (inactive, CURRENT, has_writer, created 2026-08-10) is the pre-existing cause. The readback's "monitor not source_unavailable" is therefore NOT a 1243 acceptance criterion. Diagnosis of what changed near 2026-09-24 and the remedy are Suvarṇa's/the steward's; no code changed.

## Not done / not claimed
The C29 composition SHA is pending (see above). The official pre-S-L1 capture is not taken. The window and 1241 are not applied; everything above is source- and rehearsal-level, not production-observed, except the read-only readbacks stated. Stream A's lock/CI repairs and any later head are Stream A's deltas. Nothing merged, queued, dispatched, applied or built by B.
