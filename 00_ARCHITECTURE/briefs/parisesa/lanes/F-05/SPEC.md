---
lane: F-05
stream: S5 MŪLA
class: CL-02 dead-backend
spec_version: 1.0
writer_asset: bg_remedies
data_delta: narrow
---

# F-05 SPEC — `ref_tantric_remedies_get` always empty: wire `tantric.yaml` into `bg_remedies` writer

## §1 Root-cause statement

The registered production writer `bg_remedies.py` calls only `build_all_remedies()` from `l0_remedy_corpus.py`, which contains zero `tantric`-typed rows despite declaring `"tantric"` in `VALID_REMEDY_TYPES`; the YAML ingestion path (`l0_remedy_loader.py::load_remedies()` + `remedy_corpus/tantric.yaml`) has zero production callers, leaving `brahma_remedy_corpus.remedy_type` empty of `'tantric'` rows and `ref_tantric_remedies_get` always returning `[]`.

## §2 Files to change

| File | Change | Why |
|------|--------|-----|
| `platform/python-sidecar/brahmagyan/l0_remedy_loader.py` | Add optional `glob: str = '*.yaml'` parameter to `load_remedies()`. Replace the single `yaml_dir.glob('*.yaml')` call (line 244) with `yaml_dir.glob(glob)`. No other logic changes. | Allows `bg_remedies.py` to scope the call to `tantric.yaml` only, keeping this lane's data_delta narrow. Backward-compatible default preserves all existing uses. |
| `platform/python-sidecar/pipeline/orchestrator/writers/bg_remedies.py` | After the `seed_remedy_corpus()` call (line 47), add a call to `l0_remedy_loader.load_remedies(yaml_dir=Path(__file__).parents[2] / 'brahmagyan' / 'remedy_corpus', conn=ctx.db_conn, dry_run=ctx.dry_run, glob='tantric.yaml')` and fold its `inserted`/`review_queued` counts into `WriterResult.notes`. Import `l0_remedy_loader` at top. Apply the same dry_run branch. | This is the sole registered production entry point for `bg_remedies`; wiring the loader here activates the already-correct Phase 3 tantric gate without bypassing it. |

> **Scope decision (11 sibling YAMLs excluded):** Only `tantric.yaml` is wired by this lane. The remaining 11 YAML files are orphaned but intentionally deferred: their categories already have hardcoded rows in `l0_remedy_corpus.py` (per DB GROUP BY in DIAGNOSIS §1), and a content/overlap audit is required before adding YAML-sourced duplicates. A comment in `bg_remedies.py` documents this debt.

## §3 Exit test

**File:** `platform/python-sidecar/brahmagyan/__tests__/test_f05_tantric_remedies.py`

**FAIL today (before fix):** Both tests fail — `test_tantric_yaml_produces_rows_in_dry_run` raises `TypeError` because `load_remedies()` has no `glob` parameter; `test_bg_remedies_dry_run_includes_tantric` passes but `notes` contains no mention of tantric.

**PASS after fix:** `load_remedies()` accepts `glob`; dry_run against `tantric.yaml` returns `inserted >= 1`; `WriterResult.notes` includes tantric count.

```python
"""Exit test for F-05: bg_remedies writer must produce >=1 tantric row via tantric.yaml."""
from pathlib import Path
import pytest
from brahmagyan.l0_remedy_loader import load_remedies

YAML_DIR = Path(__file__).parents[1] / 'remedy_corpus'


def test_tantric_yaml_produces_rows_in_dry_run():
    """FAILS today (TypeError: glob param absent); PASSES after fix."""
    result = load_remedies(YAML_DIR, conn=None, dry_run=True, glob='tantric.yaml')
    total = result['inserted'] + result['review_queued']
    assert total >= 1, (
        f"Expected >=1 tantric rows from tantric.yaml dry_run, got "
        f"inserted={result['inserted']} review_queued={result['review_queued']}"
    )


def test_bg_remedies_dry_run_includes_tantric():
    """FAILS today (notes lack tantric count); PASSES after fix."""
    from pipeline.orchestrator.writers.bg_remedies import RemediesWriter
    from unittest.mock import MagicMock
    ctx = MagicMock()
    ctx.dry_run = True
    ctx.build_id = 'f05-test'
    writer = RemediesWriter()
    result = writer.run(ctx)
    assert 'tantric' in (result.notes or '').lower(), (
        f"Expected 'tantric' in WriterResult.notes after fix; got: {result.notes!r}"
    )


def test_load_remedies_has_glob_param():
    """Recurrence guard: load_remedies() must accept a glob parameter."""
    import inspect
    from brahmagyan import l0_remedy_loader
    sig = inspect.signature(l0_remedy_loader.load_remedies)
    assert 'glob' in sig.parameters, (
        "load_remedies() must have 'glob' parameter — guards F-05 recurrence"
    )
```

**Run command:**
```bash
cd /Users/Dev/par-night/wt/F-05 && \
  python -m pytest platform/python-sidecar/brahmagyan/__tests__/test_f05_tantric_remedies.py -v
```

## §4 Sibling sites covered

DIAGNOSIS §4 identifies 12 YAML files in `remedy_corpus/`, all orphaned from the production writer. This spec addresses 1; the other 11 are explicitly excluded below:

| YAML file | This lane | Reason |
|-----------|-----------|--------|
| `tantric.yaml` | **Wired** | Primary defect of F-05; all rows use BPHS source (verified: passes gate, inserted directly) |
| `ayurvedic.yaml` | Excluded | DB already has `ayurvedic` rows from hardcoded path; overlap audit needed |
| `behavioral.yaml` | Excluded | DB has 9 behavioral rows from hardcoded path |
| `charity.yaml` | Excluded | DB has 67 charity rows from hardcoded path |
| `gemstones.yaml` | Excluded | DB has 22 gemstone rows from hardcoded path |
| `mantras.yaml` | Excluded | DB has 67 mantra rows from hardcoded path |
| `puja.yaml` | Excluded | DB has 76 puja rows from hardcoded path |
| `supplemental.yaml` | Excluded | Content/DB overlap unknown; no category mapping verified |
| `supplemental_b.yaml` | Excluded | Same as supplemental.yaml |
| `supplemental_c.yaml` | Excluded | Same as supplemental.yaml |
| `vastu.yaml` | Excluded | `vastu` absent from DB and not in `register_d7_channel.ts` query scope; separate lane |
| `vrata.yaml` | Excluded | DB has 33 vrata rows from hardcoded path |
| `yantras.yaml` | Excluded | DB has 23 yantra rows from hardcoded path |

## §5 Recurrence guard

`test_load_remedies_has_glob_param` (included in §3 file) is the lint-equivalent contract test. It asserts `load_remedies()` signature contains `glob`, which fails immediately if the parameter is removed. Additionally, the import of `l0_remedy_loader` in `bg_remedies.py` will cause a build-time check — removing it breaks `test_bg_remedies_dry_run_includes_tantric`. No separate CI rule needed.

## §6 Dependencies and rollback

**Dependencies:**
- No other lane depends on F-05 (confirmed: no lane doc references `bg_remedies` or `l0_remedy_loader`).
- Writer-layer fix → shadow run mandatory before rebuild (PROTOCOL §Rebuild Level 0).
- `bg_remedies` asset cost: **light** (<10 min, ~N rows from one YAML). Rebuild for verification after merge.
- No schema migration — `brahma_remedy_corpus` and `remedy_review_queue` schemas already exist (`migrations/081_l0fr_schema.sql`).
- `l0_remedy_loader.py` change is additive (new optional param, default `'*.yaml'`); no other callers break.

**Rollback:** Revert `bg_remedies.py` (remove `load_remedies` call and import). Tantric rows added to `brahma_remedy_corpus` can be removed via `DELETE FROM brahma_remedy_corpus WHERE category = 'tantric'`. `l0_remedy_loader.py` `glob` param removal is safe (no other callers use it). Zero schema changes to undo.

## §7 Coverage table

| Diagnosis sub-claim | Spec coverage |
|--------------------|---------------|
| (a) Query logic in `register_d7_channel.ts:1721` is correct — not a bug | Confirmed correct; no change to this file. |
| (b) `tantric.yaml` exists as content at `remedy_corpus/tantric.yaml` | §3 exit test loads it in dry_run; §3 verified BPHS source passes gate. |
| (c) `load_remedies()` has zero production callers | Fixed by §2: `bg_remedies.py` now calls `load_remedies(... glob='tantric.yaml')`. |
| (d) Registered writer (`bg_remedies.py`) never emits `'tantric'` | Fixed by §2; exit test asserts `'tantric'` appears in `WriterResult.notes` after fix. |
| Tantric gate must be preserved (DIAGNOSIS §5) | `load_remedies()` already implements the gate; spec does not bypass or modify it. |
| All 12 YAML siblings orphaned (DIAGNOSIS §4) | §4 lists all 12; 1 wired, 11 explicitly excluded with reasons. |
| `remedy_review_queue` dependency for failed gate rows | §6: gate preserved; rows that fail gate route to queue; no bypass; no migration. |
