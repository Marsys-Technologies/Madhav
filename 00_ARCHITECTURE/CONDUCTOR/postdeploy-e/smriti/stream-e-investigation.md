# Stream E — Smṛti: Investigation Log
Date: 2026-06-05
Stream: postdeploy-e-multi-school
Autonomy tier: TIER-1

## Key Investigation Findings

### Finding 1: ganita_positions schema already correct
- File: `platform/migrations/brahma_ganita.sql`
- `ayanamsha_id TEXT NOT NULL` column already present
- `UNIQUE(chart_id, ayanamsha_id, planet)` constraint already present
- DB table comment confirms: "One row per planet per chart per ayanamsha"
- Decision: NO DDL change to ganita_positions. Discriminator already in place.

### Finding 2: engine.py vs l1_positions.py divergence
- `l1_positions.py` already computes all 5 ayanamshas but writes to `chart_facts`
  (not `ganita_positions`) — this is the chart_facts writer
- `engine.py` has `write_positions()` that writes to `ganita_positions` but
  `run_ganita()` only calls it for ONE ayanamsha (default lahiri)
- The pipeline calls `run_ganita(..., ayanamsha="lahiri")` — single only
- Fix: extend `run_ganita()` to accept `ayanamshas` list, default to ALL_AYANAMSHAS

### Finding 3: C3 concordance flag is about house systems, not ayanamsha offsets
- WS-3 YAML explicitly: C3 = "House cusp convention — SYSTEM-DEFINING (C3)"
  with pattern: ORTHOGONAL
- The four systems (Parashari equal-house, Jaimini rashi, KP Placidus, Tajaka Varsha Lagna)
  are genuinely different house systems
- However: KP analysis uses KP ayanamsha + Placidus as an integrated system
  → planets near sign/nakshatra boundaries have different assignments under
  Lahiri vs KP offsets → AYANAMSHA_DEPENDENT sub-problem
- Resolution: C3 stays ORTHOGONAL; three sub-classes created as AYANAMSHA_DEPENDENT:
  TC.C3.SIGN_BOUNDARY, TC.C3.NAKSHATRA_BOUNDARY, TC.C3.DASHA_LORD

### Finding 4: bodha_graph already has ayanamsha_id
- `platform/migrations/brahma_bodha_bo22.sql`: `ayanamsha_id TEXT NOT NULL DEFAULT 'lahiri'`
- `seed_bodha_graph()` already accepts `ayanamsha_id: str = "lahiri"` parameter
- CGM edges are FORENSIC-grounded and mostly ayanamsha-independent (sign-lord
  relationships don't change with 0.1° offset for non-borderline planets)
- Added `detect_ayanamsha_dependent_edges()` to identify edges where involved
  planets ARE near boundaries

### Finding 5: No existing concordance_writer.py
- Searched all platform/ Python files — no concordance writer existed
- Closest: `brahmagyan/mimamsa/answer_quality.py` (QA eval) and `brahmagyan/mimamsa/outcome.py`
- Created `concordance_writer.py` in mimamsa module (correct layer per project structure)
- The concordance data is at L5 Mīmāṃsā level (cross-system quality assessment)

## Migration Naming
- Convention: `brahma_<domain>_<feature>.sql` (no numbering prefix in platform/migrations/)
- Named: `brahma_multi_school_dual_ayanamsha.sql`
- Note: `platform/supabase/migrations/` uses numbered convention (0001_baseline.sql)
  but new migrations go to `platform/migrations/` (non-Supabase standalone SQL files)
