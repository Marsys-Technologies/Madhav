---
artifact: V1_3_MULTI_SCHOOL_SCHEMA.md
canonical_id: V1_3_MULTI_SCHOOL_SCHEMA
version: 1.0
status: CURRENT
authored_by: Claude Code (Stream E Conductor) 2026-06-05
---

# V1.3 Multi-School Dual-Ayanamsha Schema

## Investigation Summary

Before designing, the codebase was audited. Key findings:

### What already exists (as of feature/postdeploy-e-multi-school branch base)

1. **`ganita_positions` already has `ayanamsha_id` as a discriminator column** — defined in
   `platform/migrations/brahma_ganita.sql` with a `UNIQUE (chart_id, ayanamsha_id, planet)`
   constraint. The table is already designed for multi-ayanamsha storage.

2. **`l1_positions.py`** (`brahmagyan/ganita/l1_positions.py`) already computes all 5 ayanamshas
   (lahiri, raman, kp, true_citra, yukteshwar) and writes to `chart_facts`. It does NOT write
   to `ganita_positions`.

3. **`engine.py`** (`brahmagyan/ganita/engine.py`) has `write_positions()` that writes to
   `ganita_positions` but `run_ganita()` only calls it for a single ayanamsha (default `'lahiri'`).
   The pipeline (`brahma_pipeline.py`) calls `run_ganita(..., ayanamsha="lahiri")`.

4. **`bodha_graph`** table (`platform/migrations/brahma_bodha_bo22.sql`) has `ayanamsha_id TEXT
   NOT NULL DEFAULT 'lahiri'` — it already has the column but all rows default to `'lahiri'`.

5. **Concordance flags** live in `00_ARCHITECTURE/CONDUCTOR/ws3/brahmagyan_concordance.yaml`.
   The C3 flag is "House cusp convention — SYSTEM-DEFINING", tagged as `ORTHOGONAL`. It concerns
   equal-house (Parashari), rashi-house (Jaimini), Placidus (KP), and Varsha Lagna (Tajaka) —
   not ayanamsha offset differences. The conductor prompt framed this as "KP-vs-Lahiri orthogonality"
   which requires clarification below.

---

## Decision: Discriminator Column (already in place)

The `ayanamsha_id` discriminator column is already the correct design and is already present
in `ganita_positions` and `bodha_graph`. No schema migration is needed for these tables.

**Rationale:**
- Single table with discriminator is preferable to table-per-ayanamsha for 5 ayanamshas ×
  ~9 grahas = 45 rows per chart (small cardinality, query simplicity wins).
- The unique constraint `(chart_id, ayanamsha_id, planet)` cleanly prevents duplicate rows
  per ayanamsha without a surrogate key collision.
- Existing indexes `idx_ganita_positions_chart ON (chart_id, ayanamsha_id)` already support
  per-ayanamsha filtering efficiently.
- This matches the pattern used in `mimamsa_calibration` where `ayanamsha_id` is a key column.

---

## Schema Design

### ganita_positions (existing — no change required)

```sql
CREATE TABLE IF NOT EXISTS ganita_positions (
  id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id           UUID        NOT NULL REFERENCES charts(id) ON DELETE CASCADE,
  build_id           TEXT        NOT NULL,
  ayanamsha_id       TEXT        NOT NULL,      -- 'lahiri' | 'kp' | 'raman' | 'true_citra' | 'yukteshwar'
  planet             TEXT        NOT NULL,
  tropical_longitude DOUBLE PRECISION NOT NULL,
  sidereal_longitude DOUBLE PRECISION NOT NULL,
  sign_id            SMALLINT    NOT NULL CHECK (sign_id BETWEEN 1 AND 12),
  sign_name          TEXT        NOT NULL,
  nakshatra_id       SMALLINT    NOT NULL CHECK (nakshatra_id BETWEEN 1 AND 27),
  nakshatra_name     TEXT        NOT NULL,
  nakshatra_pada     SMALLINT    NOT NULL CHECK (nakshatra_pada BETWEEN 1 AND 4),
  speed_dps          DOUBLE PRECISION NOT NULL DEFAULT 0,
  is_retrograde      BOOLEAN     NOT NULL DEFAULT FALSE,
  source_citation    TEXT        NOT NULL,
  computed_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT ganita_positions_unique
    UNIQUE (chart_id, ayanamsha_id, planet)
);
```

The PK is `id` (surrogate UUID). The logical discriminator key is `(chart_id, ayanamsha_id, planet)`.

### bodha_graph (existing — ayanamsha_id column already present)

```sql
-- ayanamsha_id already present with DEFAULT 'lahiri'
-- No DDL change required; the writer must be updated to propagate the correct value.
ayanamsha_id     TEXT        NOT NULL DEFAULT 'lahiri',
```

### New migration: brahma_multi_school_concordance.sql

The only new schema object needed is the `concordance_flags` materialized view / table to
support the `AYANAMSHA_DEPENDENT` class. See Session e5 for the concordance writer changes.

---

## What is NOT needed (Tier-1 auto-resolved)

1. No new `ayanamsha` column added to `ganita_positions` — it already exists as `ayanamsha_id`.
2. No table split — discriminator column is sufficient.
3. No PK change — the surrogate UUID PK plus the `UNIQUE (chart_id, ayanamsha_id, planet)`
   constraint already gives correct semantics.

---

## Clarification: C3 Concordance Flag

The conductor brief describes C3 as "KP-vs-Lahiri orthogonality". The WS-3 YAML defines C3
as "House cusp convention — SYSTEM-DEFINING": Parashari equal-house vs Jaimini rashi-house vs
KP Placidus vs Tajaka Varsha Lagna. This is a **house system** orthogonality, not an ayanamsha
offset orthogonality.

However, there is a genuine ayanamsha-dependency problem that spans the C3-flagged entries:
KP uses Placidus cusps computed from the **KP ayanamsha offset** (~23.9°), while Parashari
typically uses Lahiri offset (~23.8°). For borderline planets near sign/nakshatra boundaries
(e.g., a planet at 0° of a sign in one ayanamsha may be in the previous sign in another),
different conclusions follow across systems. This is the "KP-vs-Lahiri orthogonality" the
conductor refers to.

**Resolution approach for Session e5:** Introduce `AYANAMSHA_DEPENDENT` as a concordance
class in the Python concordance writer. Tag C3-bearing topics that produce different conclusions
depending on which ayanamsha offset is applied. C3 itself remains `ORTHOGONAL` (house systems
are fundamentally different); `AYANAMSHA_DEPENDENT` applies specifically to rules where the
ayanamsha offset causes the planet to fall in a different sign/nakshatra/house, changing the
rule's conclusion.

---

## Writer Changes Required

### engine.py `run_ganita()` (Session e3)

Currently accepts `ayanamsha: str = "lahiri"` and writes positions for one ayanamsha.
**Change:** Add `ayanamshas: list[str] | None = None` parameter. When `None`, default to
all 5 ayanamshas: `["lahiri", "kp", "raman", "true_citra", "yukteshwar"]`. Loop over each
ayanamsha, calling `compute_positions(jd, aya)` and `write_positions()` for each.

### bodha/bo22.py CGM graph writer (Session e4)

The `bodha_graph` table already has `ayanamsha_id`. The graph writer currently defaults to
`'lahiri'` (implicit from the DB default). **Change:** Accept `ayanamsha_context: str = 'lahiri'`
parameter and pass it through when seeding edges.

### Concordance writer (Session e5)

Add `AYANAMSHA_DEPENDENT = "ayanamsha_dependent"` to the concordance class enum.
Update the WS-3 concordance YAML `concordance_version` to 1.1 noting the new class.

---

## Query Patterns

### Get positions for a chart under all ayanamshas
```sql
SELECT ayanamsha_id, planet, sidereal_longitude, sign_name, nakshatra_name, nakshatra_pada
FROM ganita_positions
WHERE chart_id = $1
ORDER BY ayanamsha_id, planet;
```

### Compare sign for a planet across ayanamshas (detect ayanamsha-dependent rules)
```sql
SELECT planet, ayanamsha_id, sign_name, nakshatra_name
FROM ganita_positions
WHERE chart_id = $1 AND planet = 'Sun'
ORDER BY ayanamsha_id;
```

### Get bodha_graph edges for a specific ayanamsha context
```sql
SELECT from_signal_id, to_signal_id, edge_type, weight
FROM bodha_graph
WHERE chart_id = $1 AND ayanamsha_id = 'lahiri';
```

---

## Volume Expectations

After e3 ships, `ganita_positions` for the native's chart will have:
- 5 ayanamshas × 9 grahas (Sun/Moon/Mars/Mercury/Jupiter/Venus/Saturn/Rahu/Ketu) = **45 rows**
- Lagna is stored in `chart_facts` (via `l1_positions.py`) not `ganita_positions`

The `bodha_graph` edges remain 21 (FORENSIC-grounded); the `ayanamsha_id` column will carry
`'lahiri'` by default since the CGM graph is ayanamsha-independent at the signal level.

---

## Migration Strategy

### Existing rows
All existing `ganita_positions` rows were written with `ayanamsha_id = 'lahiri'` (explicit in
the writer). No backfill needed — they are already correctly tagged.

All existing `bodha_graph` rows have `ayanamsha_id DEFAULT 'lahiri'` — correctly tagged.

### New rows after e3
`run_ganita()` will write 5 rows per planet per chart (one per ayanamsha), using the
`ON CONFLICT (chart_id, ayanamsha_id, planet) DO UPDATE` clause already in `write_positions()`.

### New migration file
`platform/migrations/brahma_multi_school_dual_ayanamsha.sql` — adds the concordance_flags
tracking table for `AYANAMSHA_DEPENDENT` entries (Session e5).

---

## Changelog
- v1.0 (2026-06-05): Initial design. Investigates existing schema; confirms discriminator
  column already in place; defines writer changes + concordance extension.
