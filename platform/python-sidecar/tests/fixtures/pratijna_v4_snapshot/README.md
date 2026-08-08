# pratijna_v4_snapshot — PRATIJÑĀ v4 Lane B3 real-data CI fixture

A real, versioned export of chart `482012f1-710e-4a25-994a-93821f5871aa`'s
L1 facts (ayanamsha `lahiri_chitrapaksha` only), scoped to exactly the five
Postgres tables `brahmagyan.chart_reader_v4.ChartReaderV4` reads:
`charts`, `chart_divisionals`, `chart_facts`, `chart_fact_identity`, and
the global `reference_planets` table. Restoring this fixture into an
ephemeral Postgres and pointing `ChartReaderV4`/`PratijnaV4Engine` at it
reproduces the exact same scores as the live production database — see
`test_pratijna_v4_snapshot_properties.py`'s module docstring for the
verification this claim rests on.

This is the CI tier of PRATIJÑĀ v4's three-tier verification plan
(`00_ARCHITECTURE/briefs/adhisthana/MASTER_PLAN_v1_0.md` §5): a "real-data
snapshot fixture (one chart's facts+signals+Index exported, versioned,
refresh procedure documented)" that the property tests in
`tests/test_pratijna_v4_snapshot_properties.py` run against, with no
network access to production and no live `DBURL` required.

## Layout

```
pratijna_v4_snapshot/
  schema.sql              -- CREATE TABLE/INDEX/CONSTRAINT for the 5 tables
  data/
    charts.csv.gz              -- 1 row (chart 482012f1 itself)
    chart_divisionals.csv.gz   -- this chart's D1..D60 positions, lahiri_chitrapaksha only
    chart_facts.csv.gz         -- this chart's derived L1 facts, lahiri_chitrapaksha only
    chart_fact_identity.csv.gz -- the identity index over the chart_facts subset above
    reference_planets.csv.gz   -- full table (global, not chart-scoped)
```

## Regenerating this fixture

Use `platform/scripts/fixtures/export_pratijna_v4_snapshot.py` — it IS the
refresh procedure, not just a description of one (see that script's own
module docstring for the full "what and why" and the step-by-step
regeneration recipe). In short:

```
DBURL=<see PRATIJNA_V4_STATE.md 'DB access'> \
  python3 platform/scripts/fixtures/export_pratijna_v4_snapshot.py
```

This overwrites every file in this directory in place. **Diff before
committing** — a refresh that silently changes the property tests'
expected numbers (marriage/separation/childbirth occurrence+condition) is
itself worth a second look, not a rubber-stamped commit. Run the property
test suite locally against the refreshed fixture before pushing (see
`test_pratijna_v4_snapshot_properties.py`'s module docstring for the local
ephemeral-Postgres recipe, or `platform/scripts/fixtures/
restore_pratijna_v4_snapshot.py <postgres-url>` directly).

## Why this scope (one chart, one ayanamsha, five tables)

- **One chart** (`482012f1`): the campaign's primary reference chart —
  every RUNG_P3 hand-worked number and every existing live acceptance test
  in this campaign is anchored on it.
- **One ayanamsha** (`lahiri_chitrapaksha`, the campaign's own
  `DEFAULT_AYANAMSHA`): the real writer scores all 5 `CANONICAL_AYAS`, but
  every property this CI tier checks (marriage != separation, no
  monoculture, condition nonzero, etc.) is fully decidable from a single
  ayanamsha's worth of facts — scoring all 5 would multiply fixture size
  ~5x for zero additional coverage.
- **Five tables**: exactly what `ChartReaderV4` touches (see that module's
  own docstring) plus `charts`, which only exists here to satisfy
  `chart_divisionals.chart_id`'s FOREIGN KEY — no query in this whole
  subsystem ever selects from `charts` directly.

R19: this fixture is a frozen, versioned, committed export — the property
test suite that reads it never talks to production, and the export script
itself only ever reads (never writes) the production connection.
