# REVIEW REQUEST — §8.5 (G-10: per-contributor BAV matrix, migration 1086)

**Brief:** `GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md` §8.5
**Branch:** `l3/gochara-autonomous-wp0-7`
**Commit:** `1fab2364e`
**Sheet item:** G-10 (L1); ruling sheet v2.0 row M-7; N-21 testimony rule

## What changed

- `platform/python-sidecar/ga_writers/ga_strength_writer.py`:
  - New `_derive_ashtakavarga_prastara()` (`@serialized_swiss_state`) returning the per-contributor matrix from PyJHora's own `get_ashtaka_varga` **prastara** return (3rd value) — delegated, not hand-rolled (D-1.5b Lane B-2). Contributor order verified against the installed jhora source: index 0..7 = Sun..Saturn, Lagna.
  - `_build_ashtakavarga_rows()` gains an optional `prastara=` parameter and emits `ashtakavarga_bindu_contributor` rows: subject `{GRAHA}-CONTRIBUTOR_{SUN|MOON|MAR|MER|JUP|VEN|SAT|LAGNA}-SIGN_{1..12}`, key `bindus`, value 0/1 — 672 rows per (chart, ayanāṃśa). Citation text cites BPHS ch.66 dot/rekha semantics + nāḍī kakṣyā testimony PG1615/PG1616 at testimony grade (N-21: testimony never supplies computation weight).
  - `_citation_human_strength` gains a branch for the new category.
  - `build_ga_strength` derives and passes the matrix alongside the existing shodhana grids (same Swiss computation convention).
- `platform/python-sidecar/ga_writers/CHART_FACTS_SCHEMA.json`: `ashtakavarga_bindu_contributor` category entry (range [0,1], sign-keyed subject note, row-count contract).
- `platform/migrations/1086_nirmana_l1_gochara_g10_ga_strength_contributor_digest_spec.sql`: revises ga_strength's output-digest spec to include the new category, mirroring 1042's fail-closed DO-block pattern. New spec sha256 `52a0d253…87a97` computed with the real `canonical_digest` (hashing the 1042 spec reproduces its stored sha exactly — canonicalization verified, not assumed). `count_sql` needed no change (307's `ashtakavarga_%` clause already covers it); `target_floor` deliberately not bumped — it rebaselines at the first governed rebuild (§N.4 aspirational).
- Tests: `tests/l3/gochara/test_g10_contributor_matrix.py` (4 passed: shape/binary, BPHS ch.66 dot/rekha semantics per (g,c) against jhora's benefic-house table on one synthetic chart, contributor-sum == raw BAV, SAV invariant 337 through the matrix, row-builder emits 672 rows consistent with `ashtakavarga_bindu_sign`) and `tests/l3/gochara/test_g10_digest_spec_1086.py` (4 passed: SQL contract via the real `_validate_spec`, disposable-DB apply/retire/idempotency, fail-closed guard).

## Tests (the §8.5 caution gate)

Full L1 ga_strength suite: 378 passed, 2 skipped, **1 pre-existing failure** (`test_swiss_state_boundary.py::test_generated_inventory_is_exact_and_has_no_unresolved_live_owner` — fails identically on the clean tree, unrelated to this writer). Gochara suite: **252 passed**. Writer stays WriterBase-conformant (orchestrator conformance tests green). One cross-test interaction found and fixed during the work: jhora's chart calls redirect the global Swiss ephemeris path, which broke `test_wp3a_kernel.py::test_case_02_mean_node_convention` when the new fixture ran first; the test now re-asserts the pinned `.run/se1` path after each computation.

## Unsure of

- The digest revision means a governed rebuild now attests the contributor family too; whether the native wants the 672-row family inside the wealth-reading digest scope (vs. a separate spec) is a review call.
- The fixture's ch.66 check uses PyJHora's own benefic-house table as the reference (it IS the classical table); the writer's local `BENEFIC_HOUSES` copy (per-varga path) is implicitly cross-checked by the contributor-sum == raw-BAV assertion but not diffed directly.
