---
artifact: ASTRA_REVIEW_DASHA_REPIN_DELTA
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-10-04"
verdict: ACCEPT
reviewed_commit: "49b596bd9 (pravaha/a53-am5-inventory)"
authority: "Review only; authorizes nothing."
---

No blocking findings. No amendments required.

1. **Scope — PASS.** Exactly 15 files, +134/−99. No migration, window, workflow or `ka_gochara_v5.py` changes. Executable function/class ASTs in both changed production modules are unchanged.

2. **Pins and reference rows — PASS.** Both governed pins equal `75524b3e-102a-43ec-8cee-3f57fee752c3`. All ten reference rows match evidence §(3): UUIDs, parent links and all twenty endpoints. Two PD starts move +6992 seconds; every other reference endpoint moves +6993. No old reference UUID or endpoint remains. The docstring records the September baseline and October SETTLED-1 re-pin truthfully.

3. **Lock and generated artifacts — PASS.** Offline `implementation_registry --check` returns `current`. Aggregate `73f67d22… → fcfb6827…`; evaluation alone changes `2bd30ecf… → d291e4a0…`. Geometry `535e05b0…` and window `fdb8f9b7…` remain unchanged. Both modified modules belong to evaluation. Writer-inventory verification passes. Census content hash and updated writer-file fingerprint match. Decoded goldens agree across stdout/log transport; changes comprise digests and regeneration metadata, with no changed result assertions.

4. **Test edits — PASS.** The rulings account for **8 rewritten / 14 retained literals**. Rewrites preserve conflict identity, exact duplication, sibling adjacency and boundary meaning. The additional seven boundary forms and `just_before = 2020-02-14T13:43:55Z` are consistent. Fixed event dates remain fixed. Retained synthetic-tree, rewriting, import and timezone examples do not depend on current reference-row equality. No assertion was weakened into a vacuous pass.

5. **Generated regression — PASS.** Both tests execute successfully: the shared selector rejects OLD with `DashaReadConflict`, accepts NEW, and verifier pin equals read-contract pin equals NEW. This establishes the stated selector/pin contract, not database-population acceptance.

6. **Stale-data search and frozen oracle — PASS.** Scanned 13,948 tracked textual files, including timestamp/offset, constructor, compact, epoch and Julian-day forms; also decoded both goldens. Remaining old boundaries occur in independent synthetic fixtures and historical comments, with no executable stale boundary controlling this re-pin. Frozen v1.4 correctly remains historical under AM-10; its old UUIDs and boundary expectations must not be treated as current-data oracles.

Validation: **87 passed, 7 pre-existing expected failures**. Database claims were assessed from supplied evidence; no database accessed and no files changed.

**MAY PR 2999 AT HEAD 49b596bd9 ENTER THE PROTECTED TRAIN (after 2867 and 2919) — YES.**

