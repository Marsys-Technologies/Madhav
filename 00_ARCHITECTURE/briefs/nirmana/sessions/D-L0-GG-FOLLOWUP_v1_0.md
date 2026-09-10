---
artifact: D-L0-GG-FOLLOWUP_v1_0.md
canonical_id: NIRMANA_L0_DGG_FOLLOWUP
version: "1.0"
status: RECORD — one-time finding, not a living document
produced_on: 2026-09-06
owner: L0 session
campaign_id: nirmana-elevation
---

# D-L0-GG follow-up — "verified live" must mean committed, not rolled back

Migration 700 (PR #2004, D-L0-GG) fixed `bg_dasha_systems`'s `integrity_check_sql` (join-scope bug
+ stale `catalog_hash` pin). Its own commit message asserted the underlying data was "already
correct... once ontology is scoped correctly," citing "a direct, rolled-back replay of
`seed_dasha_systems()` against the live schema."

A live re-check on 2026-09-06 found that claim false in practice: `reference_dasha_systems` was
missing `kp` (19 rows, not 20), and `brahma_ontology` (`entity_class='dasha_system'`) still carried
the stale id `jaimini_chara` instead of `chara_jaimini` — both contradicting "already correct."
`seed_dasha_systems()` is a genuine single-transaction delete-then-insert across all three tables
with a strict postflight row-count guard, so a real *committed* run would have brought all three
into agreement; a *rolled-back* replay (used to compute the correct pin hashes) never persists
anything and says nothing about the actually-committed state of the live tables.

**The fix**: a real W4 rebuild dispatch of `bg_dasha_systems` (build run
`c086b0e4-df3a-49a6-a142-460d3c45acf0`, 2026-09-06). No writer logic changed — same source,
committed for real this time. Verified live, clause-by-clause: all 9 conjuncts of
`integrity_check_sql` now pass (row counts, cross-table alignment, `kp` present, `jaimini_chara`
absent, all three content hashes).

**The lesson, generalizable beyond this one asset**: a "verified live" claim in a migration or PR
commit message must cite a *committed* observation, not a rolled-back one. A rolled-back replay is
a legitimate way to *compute* what a correct hash pin should be — it is not evidence that the live
table already matches it. The two are easy to conflate in a single sentence ("verified live
(read-only, rolled back)") and this record exists so the next person reads that phrasing carefully.

This file intentionally does not touch `platform/python-sidecar/brahmagyan/l0_dasha_systems.py` (or
any other registered writer module) — any edit there changes that writer's content hash in
`nirmana-writer-digests.json`, which would invalidate this same session's already-accepted
`asset_analysis_accepted`/`optimization_verdict_accepted` W2-refresh evidence for
`bg_dasha_systems` (bound to `writer_digest_sha256 66585e94ff6436555eedca470ae72542392054ae2d24afa7db0b6503ad02edb7`)
and reopen the exact stale-registry-contract loop this session had just closed. Discovered the hard
way (CI's `provenance_inventory --check` gate) when an earlier version of this same fix put the note
directly in the writer's docstring instead.
