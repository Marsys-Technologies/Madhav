# REVIEW REQUEST — WP7 Packet K-1

**Packet:** `PACKET_K1_V1_kshetra_sangam_deps.md` (K-1 half)
**Branch:** `l3/gochara-autonomous-wp0-7`
**Scope:** ka_kshetra authority seam (N-10) + generation-pinned crosscheck edges + registry edge declarations.

## What changed

1. **`platform/python-sidecar/services/ka_kshetra/stage4_field.py` — `load_legacy_crosscheck`**
   - Removed `COALESCE((SELECT authoritative_generation …), 'v1')` → plain correlated sub-select. An absent `kala_gochara_authority` row now yields **zero rows** (chart unpublished), superseding PG-31's "absent row ⇒ v1 by definition" (migration 527).
   - SELECT list now includes `generation` so the writer can pin it into the provenance edge.

2. **`platform/python-sidecar/services/ka_kshetra/writer.py`**
   - Both legacy-xref edge sites (`_write_window` ~L948, `_write_windows_batch` ~L1062): `term_key` is now `gate:legacy_sweep_xref:{generation}:{id}:{agree|diverge}` and `source_pk` is `{generation}:{id}` (was bare `{id}`). `generation` falls back to `'unknown'` only when a row lacks the key (test fakes); production rows always carry it via (1).
   - `_gochara_corpus_pin`: COALESCE removed; `SELECT authoritative_generation AS gen FROM kala_gochara_authority WHERE chart_id = %s`. Absent row ⇒ sentinel `'unpublished'` (was `'v1'`).

3. **Migration `platform/migrations/1084_wp7_k1_v1_registry_edges.sql`** (idempotent, follows 569 convention)
   - `ka_kshetra.depends_on += ka_gochara` (crosscheck corpus read of `kala_gochara_windows`)
   - `ka_kshetra.depends_on += ka_vedha_gochara` (authority-seam read of `kala_gochara_authority`)
   - `ka_sangam.depends_on += ka_vedha_gochara` (V-1 half — see REVIEW_REQUEST_V1.md)

4. **Tests updated (intended breaks)**
   - `tests/l3/ka_kshetra/test_stage4_field.py::TestLoadLegacyCrosscheck` — rewritten: asserts no `COALESCE`, no `'v1'` literal, generation column selected, sub-select still correlated (params unchanged).
   - `tests/l3/ka_kshetra/test_writer.py::TestA1GochaCorpusPin` — `test_generation_defaults_to_v1…` renamed to `test_generation_is_unpublished_when_authority_table_empty` (expects `'unpublished'`); `test_calibration_state_reflects_dominant_tier` now seeds an authority row because the calibration read keys on the authority-resolved pin generation.
   - `tests/l3/ka_kshetra/fake_db.py` — FakeConn emulates the N-10 seam: the authority handler returns **no rows** when no authority row exists (was `{'gen': 'v1'}`); the `kala_gochara_windows` handler filters to the authoritative generation and returns zero rows when no authority row is seeded.
   - `tests/l3/ka_kshetra/fixtures.py` — `build_tables` now seeds `kala_gochara_authority` (`v1`) and `generation: 'v1'` on the windows fixture row, matching production semantics so full-build tests keep their xref edges (now keyed `…:v1:991:…`).

## Verification

- `cd platform/python-sidecar && pytest tests/l3/ka_kshetra services/ka_kshetra/tests -q` → **720 passed, 11 skipped, 2 xfailed** (after fix; final targeted rerun 404 passed for writer+stage4+services).
- Note: repo `.venv` was missing `psycopg2-binary` and `networkx` (both in `platform/python-sidecar/requirements-ci.txt`); installed into `.venv` to run the suite. No code change implied.

## Flags / mismatches

- **P-1d consistency:** this packet applies the same "absent authority ⇒ unpublished" rule that P-1 applied to the MCP serving layer. `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` still carries the old COALESCE seam (flagged in REVIEW_REQUEST_P1.md and P2.md) — **cross-layer ruling still needed**.
- `term_key`/`source_pk` shapes changed — any downstream consumer pattern-matching `gate:legacy_sweep_xref:{id}:` must be updated; grep found no consumers outside writer/tests.
- Fakes may produce `generation='unknown'` in edge keys; production cannot (column selected). Acceptable sentinel per packet's "pin the generation" intent.

## Amendment 2026-09-24 — the `ka_kshetra -> ka_gochara` edge is held out of 1084

At the Kṣetra stream's request, verified at source by the L3 session before acting. Migration 1084 now
declares only the service seam (`ka_kshetra -> ka_vedha_gochara`, `ka_sangam -> ka_vedha_gochara`).

Verified: (1) `depends_on` is a hard build gate — `asset_runner` requires a dependency `lit` for the chart,
and dependencies feed `canonical_upstream_hash`; (2) the seed registers `ka_gochara` as owning
`kala_gochara_windows` while its writer writes `kala_gochara_windows_v2` — the registry and the writer
disagree, and Kṣetra reads the authoritative generation, not the W2G rows; (3) migration 569 had to remove a
retired-asset edge that deadlocked every `ka_kshetra` dispatch; (4) the register has no role column.

Not verified, and stated as such: whether `tests/test_dag_edge_guard.py::test_live_registry_has_no_hard_violations`
(needs `DATABASE_URL`; no allowlist for this read) would report the now-undeclared read, because the guard scans
`@register` writer files and it is unclear it reaches `stage4_field.py`. No registry database was available.
That is the consequence the Kṣetra stage-3 executor must state when it applies or declines the edge.
Regression test: `tests/l3/gochara/test_wp12_k1_edges.py`.
