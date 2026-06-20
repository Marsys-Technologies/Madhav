---
artifact: CLAUDECODE_BRIEF_BG_EPHEMERIS_v1_0
canonical_id: L0_BG_EPHEMERIS_BRIEF
version: 1.1
status: EXECUTION_IN_PROGRESS
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — bg_ephemeris writer (wrapper over existing engine)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: 825084  # ephemeris_daily rows (1900-01-01 → 2150-12-31, 9 bodies, Lahiri)
pyswisseph: "2.10.3.2"
ayanamsha_model: "tropical_stored_sidereal_derived"
engine_date_range: "1900-01-01/2150-12-31"
dependencies: []  # Tier 0 — no L0 dependencies
llm_cost: $0
document_number: 3 of 15
---

# bg_ephemeris — Writer Brief (wrapper over the existing ephemeris engine)

> **This is the simplest writer in the campaign.** The ephemeris data already exists in production (`ephemeris_daily`, ~825,084 rows, populated by prior L0FR work). The brief does NOT recompute or redesign anything. It registers a thin `@register('bg_ephemeris')` writer that (a) reports the existing row count and lights the tile when data is present, and (b) is *capable* of a full deterministic rebuild from empty — which is what makes the Document 15 delete-and-rebuild proof hold for this asset. ZERO LLM. The engine (`brahmagyan/l0_ephemeris.py`) is unchanged.

## §0 — Asset summary

- **Asset ID:** `bg_ephemeris`
- **Backing table:** `ephemeris_daily`
- **Target floor:** `825,084` rows (the `VOLUME_FLOOR` constant in `l0_ephemeris.py`; date range 1900-01-01 → 2150-12-31, 9 bodies Sun…Ketu, single Lahiri ayanamsha per holistic design §3.1)
- **Source category:** algorithmic (Swiss Ephemeris compute with algorithmic fallback; deterministic per date+body)
- **Scope:** `global` (chart-independent)
- **Tier:** 0 (no L0 dependencies)

> **RESOLVED (2026-06-08, branch fix/ephemeris-expand-1900-2150):** Engine constants corrected — `BUILD_START=1900-01-01`, `BUILD_END=2150-12-31`, `VOLUME_FLOOR=825_084`, pyswisseph==2.10.3.2. Tropical storage confirmed; 5-ayanamsha read-time derivation (lahiri/raman/kp/krishnamurti/yukteshwar/surya_siddhanta) implemented via `derive_sidereal()`. FORENSIC anchor verified: Sun 1984-02-05 Lahiri sidereal = 292.24° (Capricorn, sign 10). Backfill running: 1900-01-01 → 2150-12-31, ~825,084 rows, ON CONFLICT DO NOTHING.

## §1 — Schema reference (existing — do NOT alter)

`ephemeris_daily` columns consumed by the engine's INSERT (`l0_ephemeris.py:349-360`):

| Column | Type | Notes |
|---|---|---|
| `date` | DATE | part of PK `(date, body, ayanamsha_id)` |
| `body` | TEXT | one of the 9 DAILY_BODIES |
| `ayanamsha_id` | TEXT | single value (Lahiri); NOT NULL enforced by `check_volume` ayanamsha_check |
| `tropical_longitude` | NUMERIC | 0 ≤ lon < 360 |
| `latitude` | NUMERIC | |
| `speed_dps` | NUMERIC | degrees/day; sign gives retrograde |
| `is_retrograde` | BOOLEAN | |
| `source_citation` | TEXT | NOT NULL (checked by `check_volume` source_citation_check) |
| `computed_at` | TIMESTAMPTZ | |

Idempotency is built into the engine: `INSERT … ON CONFLICT (date, body, ayanamsha_id) DO NOTHING` (`l0_ephemeris.py:358`).

## §2 — Source references

This asset is algorithmic, not text-cited. Its provenance is the `source_citation` column already populated on every row (e.g. Swiss Ephemeris / algorithmic-fallback attribution set by `_compute_positions_for_date` / `_algorithmic_fallback`). No classical-text citation applies. The holistic design §3.1 locks: 1900-2150, 9 grahas, Lahiri only — **no ayanamsha expansion, no date-range change.**

Source: pyswisseph==2.10.3.2, DE441 ephemeris file. Version pinned in SOURCE_CITATION constant.

## §3 — Embedded content

None. Unlike the content writers, bg_ephemeris embeds no Python data — the engine computes positions deterministically. This section is intentionally empty.

## §4 — Writer implementation

Create `platform/python-sidecar/pipeline/orchestrator/writers/bg_ephemeris.py`. The writer is **count-first**: if the floor is already met it is a cheap no-op (it must NOT recompute 825K Swiss-Ephemeris positions on every Build); only an empty/under-floor table triggers a real build.

```python
"""
bg_ephemeris writer — thin wrapper over brahmagyan.l0_ephemeris.

Behaviour:
- If ephemeris_daily already meets the volume floor (the normal case), this is a
  no-op that reports the existing count and lets asset_runner light the tile.
- If the table is empty or under floor (delete-and-rebuild proof, Document 15),
  it runs the deterministic engine to (re)populate 1900-2150.

The engine commits in batches on its OWN connection — it must NOT share
asset_runner's savepoint-scoped connection (that would release the savepoint
mid-writer). So the heavy build path opens a dedicated connection; the no-op
path touches no data and leaves ctx.db_conn for the caller's state transition.

Per holistic design v1.1 §3.1: 1900-2150, 9 grahas, Lahiri only. ZERO LLM.
"""
from __future__ import annotations
import logging
import time
from pipeline.orchestrator.writers import register, WriterBase, ContextSpec, WriterResult
from brahmagyan.l0_ephemeris import check_volume, build_ephemeris, VOLUME_FLOOR

logger = logging.getLogger(__name__)


@register('bg_ephemeris')
class EphemerisWriter(WriterBase):
    asset_id = 'bg_ephemeris'

    def run(self, ctx: ContextSpec) -> WriterResult:
        t0 = time.time()

        # 1. Count-first. Use the caller-owned connection for the read only.
        vol = check_volume(conn=ctx.db_conn)
        actual = int(vol['actual_rows'])
        floor = int(vol.get('floor', VOLUME_FLOOR))

        if ctx.dry_run:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0, rows_skipped=actual,
                duration_seconds=time.time() - t0,
                notes=f'dry_run: ephemeris_daily has {actual}/{floor} rows ({vol["status"]})',
            )

        # 2. Floor already met → no-op. Report the count; asset_runner lights the tile.
        if actual >= floor:
            return WriterResult(
                asset_id=self.asset_id, rows_inserted=0, rows_skipped=actual,
                duration_seconds=time.time() - t0,
                notes=(f'wrapper no-op: ephemeris_daily already at {actual}/{floor} '
                       f'({vol["status"]}); birth_date_check={vol["birth_date_check"]["status"]}'),
            )

        # 3. Under floor → deterministic (re)build on a DEDICATED connection so the
        #    engine's per-batch commits do not disturb asset_runner's savepoint.
        logger.info('[bg_ephemeris] under floor (%d/%d) — running engine rebuild', actual, floor)
        summary = build_ephemeris()   # conn=None → engine opens + owns + closes its own connection
        inserted = int(summary.get('rows_inserted', 0))

        # Re-read final count on the caller connection for an accurate tile value.
        vol2 = check_volume(conn=ctx.db_conn)
        final = int(vol2['actual_rows'])
        return WriterResult(
            asset_id=self.asset_id, rows_inserted=inserted,
            rows_skipped=max(0, final - inserted),
            duration_seconds=time.time() - t0,
            notes=(f'engine rebuild: inserted {inserted}, final count {final}/{floor} '
                   f'({vol2["status"]}); birth_date_check={vol2["birth_date_check"]["status"]}'),
        )
```

> **If the imports don't resolve:** confirm `VOLUME_FLOOR`, `check_volume`, `build_ephemeris` are exported from `brahmagyan/l0_ephemeris.py` (they are at HEAD; `VOLUME_FLOOR` is a module constant — grep it). If `VOLUME_FLOOR` is named differently, adapt the import; do NOT hardcode 825084 in the writer.

**CHECKPOINT 4:** `python -c "from pipeline.orchestrator.writers.bg_ephemeris import EphemerisWriter; print(EphemerisWriter.asset_id)"` (run from `platform/python-sidecar`) prints `bg_ephemeris`, and `discover_all()` now lists it.

## §5 — FK validation

None. `bg_ephemeris` has no foreign-key dependency on any other L0 asset (Tier 0). It does not reference `brahma_ontology`. The only integrity invariants are the existing `check_volume` checks: `source_citation` NOT NULL, `ayanamsha_id` NOT NULL, native-birth-date row present.

## §6 — Unit tests

Author `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_bg_ephemeris.py`:

```python
import os, uuid
import psycopg
from pipeline.orchestrator.writers.bg_ephemeris import EphemerisWriter
from pipeline.orchestrator.writers import ContextSpec, discover_all, get_writer
from brahmagyan.l0_ephemeris import VOLUME_FLOOR  # imported so the §6 assertion resolves (no hardcode)


def _ctx(conn):
    return ContextSpec(asset_id='bg_ephemeris', build_id=str(uuid.uuid4()), db_conn=conn)


def test_registered():
    discover_all()
    assert get_writer('bg_ephemeris') is EphemerisWriter


def test_noop_when_floor_met():
    """Against prod (data present), the writer is a no-op: 0 inserted, count reported."""
    conn = psycopg.connect(os.environ['PROD_DB_URL'])
    try:
        res = EphemerisWriter().run(_ctx(conn))
        assert res.asset_id == 'bg_ephemeris'
        assert res.rows_inserted == 0          # no recompute when floor met
        assert res.rows_skipped >= VOLUME_FLOOR  # reports the existing corpus (import VOLUME_FLOOR; do NOT hardcode)
    finally:
        conn.close()


def test_dry_run_touches_nothing():
    conn = psycopg.connect(os.environ['PROD_DB_URL'])
    try:
        ctx = _ctx(conn); ctx.dry_run = True
        res = EphemerisWriter().run(ctx)
        assert res.rows_inserted == 0
    finally:
        conn.close()
```

```bash
cd platform/python-sidecar
PROD_DB_URL=$PROD_DB_URL python -m pytest pipeline/orchestrator/writers/tests/test_bg_ephemeris.py -v
```

**CHECKPOINT 6:** all three tests pass against prod. The no-op test proves the writer does not recompute when data is present.

## §7 — Vimarśaka check (asset-specific)

Folded into Vimarśaka-Ω (Document 15). The per-asset gate for bg_ephemeris is:

```python
def check_bg_ephemeris(conn):
    from brahmagyan.l0_ephemeris import VOLUME_FLOOR  # import — never hardcode (engine constant is the source of truth)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM ephemeris_daily")
    n = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM ephemeris_daily WHERE source_citation IS NULL")
    null_cite = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM ephemeris_daily WHERE ayanamsha_id IS NULL")
    null_aya = cur.fetchone()[0]
    # FORENSIC ground-truth: native birth date 1984-02-05 has a Sun row
    cur.execute("SELECT count(*) FROM ephemeris_daily WHERE date='1984-02-05' AND body='Sun'")
    birth = cur.fetchone()[0]
    ok = n >= VOLUME_FLOOR and null_cite == 0 and null_aya == 0 and birth >= 1
    return ok, f'rows={n}/{VOLUME_FLOOR} null_cite={null_cite} null_aya={null_aya} birth_row={birth}'
```

APPROVE iff: rows ≥ `VOLUME_FLOOR` (imported from the engine) AND zero null `source_citation` AND zero null `ayanamsha_id` AND the native birth-date Sun row exists. **The gate imports `VOLUME_FLOOR` — it does NOT hardcode 825,084** (see the HARD STOP below).

## §8 — Hard stops + scope discipline

- The engine `l0_ephemeris.py` is **read-only** for this brief. Do NOT edit it; only wrap it. If a wrap requires an engine change, HALT and surface to native.
- Do NOT widen the date range or add ayanamshas (holistic design §3.1 lock).
- §6 no-op test shows `rows_inserted > 0` against prod → the count-first guard is wrong (it recomputed live data); fix before proceeding.
- If `ephemeris_daily` is unexpectedly empty against prod → do NOT trigger a full build inside this brief's tests (it's a multi-minute Swiss-Ephemeris run); report to native and confirm whether a repopulate is intended.
- Out of scope: ayanamsha variants, transit precompute, per-chart ephemeris (those are L1+).

---

### Changelog
- v1.1 (2026-06-08): Engine constants corrected (BUILD_START 1980→1900, BUILD_END 2060→2150, VOLUME_FLOOR 29_200→825_084). 5-ayanamsha read-time derivation added. HARD STOP resolved. pyswisseph==2.10.3.2 pinned.
- v1.0 (original): Initial brief.

*End of bg_ephemeris brief (Document 3 of 15).*
