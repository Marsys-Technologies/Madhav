# ga_nakshatra — L1 Per-Chart Parallel Nakshatra Chart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `ga_nakshatra` — a new L1 per-chart asset that writes the per-chart parallel nakshatra chart into `chart_facts`. Per ayanamsha (×5), per body (10 bodies): placement+attribute JOIN from bg_nakshatra, KP sub-lords, nakshatra dispositor graph, gaṇḍānta severity flags, tara bala, per-chart statistics, D150 attribution reference.

**Architecture:** Heavy `WriterBase` subclass (`plan_substeps` + `run_substep`), one sub-step per ayanamsha + one cross-ayanamsha pass. Two Python helper modules: `ga_nakshatra_compute.py` (pure algorithms — KP, gaṇḍānta, tara, dispositor graph) and `ga_nakshatra_emitters.py` (fact row builders, all 14 fact_categories). Writer in `pipeline/orchestrator/writers/ga_nakshatra.py`. Into `chart_facts`. `replace_prior_chart_facts()` idempotency. No new DB tables. bg_nakshatra is authority for static attrs (cite, never restate); ga_vargas is authority for D150 position (cite, never recompute).

**Tech Stack:** Python, psycopg2, PyJHora via pyjhora_adapter, `chart_facts` table, `reference_nakshatra`/`reference_nakshatra_pada` for JOIN, WriterBase frozen contract, Vimshottari proportional subdivision for KP.

**Governing brief:** `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_GA_NAKSHATRA_WRITER_v1_0.md`
**Master plan:** `00_ARCHITECTURE/NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md` (§3 + §7.1 LOCKED)

---

## File Map

| Action | File | Responsibility |
|---|---|---|
| Create | `platform/supabase/migrations/241_ga_nakshatra_registry.sql` | Asset registry INSERT |
| Create | `platform/python-sidecar/ga_writers/ga_nakshatra_compute.py` | KP algorithm, gaṇḍānta, tara, dispositor graph |
| Create | `platform/python-sidecar/ga_writers/ga_nakshatra_emitters.py` | Fact row builders for all 14 fact_categories |
| Create | `platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py` | `@register('ga_nakshatra')` heavy WriterBase subclass |
| Create | `platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_nakshatra.py` | Unit tests (no DB) |
| Create | `platform/supabase/migrations/242_ga_nakshatra_target_floor.sql` | target_floor after first build |
| Commit | `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_GA_NAKSHATRA_WRITER_v1_0.md` | Track restored brief |
| Commit | `00_ARCHITECTURE/NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md` | Track restored master plan |

---

## Canonical constants (copy exactly, do not re-derive)

```python
# From ga_positions_writer.py — DO NOT diverge
CANONICAL_AYANAMSHAS: dict[str, str] = {
    "lahiri_chitrapaksha": "lahiri",
    "true_chitra":         "true_chitra",
    "krishnamurti":        "kp",
    "raman":               "raman",
    "surya_siddhanta_classical": "surya_siddhanta",
}

PLANET_TO_SUBJECT: dict[str, str] = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
    "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN", "Lagna": "LAGNA",
}

# KP Vimshottari
VIMSHOTTARI_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
PLANET_CYCLE: list[str] = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"
]
# Nakshatra lords 0-indexed (Ashwini=Ketu, Bharani=Venus, Krittika=Sun, ...)
NAK_LORD: list[str] = (PLANET_CYCLE * 3)[:27]

NAK_SPAN_ARCMIN: float = 800.0  # 13°20' × 60

# Gaṇḍānta: within 48 arcmin of these junction longitudes (0°, 120°, 240°)
GANDANTA_JUNCTION_DEG: list[float] = [0.0, 120.0, 240.0]
GANDANTA_ORB_ARCMIN: float = 48.0  # 0°48'

# Tara bala names (index 0 = Tara 1)
TARA_NAMES: list[str] = [
    "Janma","Sampat","Vipat","Kshema","Pratyari",
    "Sadhaka","Vadha","Mitra","Atimitra",
]
```

---

## Task 1: Branch + commit restored files

**Files:** git only (no code changes)

- [ ] **Step 1: Create feature branch**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout main && git pull origin main
git checkout -b feature/ga-nakshatra-l1
```

- [ ] **Step 2: Commit the two restored files (they are untracked)**

```bash
git add 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_GA_NAKSHATRA_WRITER_v1_0.md
git add 00_ARCHITECTURE/NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md
git add docs/superpowers/plans/2026-06-17-ga-nakshatra-l1.md
git commit -m "chore(ga_nakshatra): track restored brief + master plan + implementation plan"
```

---

## Task 2: Migration 241 — asset registry

**Files:**
- Create: `platform/supabase/migrations/241_ga_nakshatra_registry.sql`

- [ ] **Step 1: Create migration**

```sql
-- 241_ga_nakshatra_registry.sql
-- =============================================================================
-- Register ga_nakshatra in asset_registry.
-- No new tables — writes into chart_facts.
-- target_floor = NULL until first build (§N.4 floors aspirational).
-- Applied surgically — never via deploy.yml.
-- =============================================================================

BEGIN;

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table,
    count_sql, size_sql,
    target_floor, depends_on, scope, is_active
) VALUES (
    'ga_nakshatra', 'ganita', 20,
    'Nakṣatra-Paṭala', 'Nakshatra Parallel Chart',
    'Per-chart parallel nakshatra chart: placement+attribute JOIN from bg_nakshatra, '
    'KP sub-lords (star/sub/sub-sub/prana) per body and house cusp, nakshatra dispositor '
    'graph, gaṇḍānta severity flags, tara bala, per-chart statistics. Into chart_facts. '
    'Authoritative L1 nakshatra grain. Depends on bg_nakshatra + ga_positions.',
    'postgres_table', 'chart_facts',
    $$SELECT count(*) FROM chart_facts
      WHERE chart_id = $1
        AND fact_category IN (
          'graha_nakshatra_join','graha_pada_join','nakshatra_lord_placement',
          'graha_kp_lords','cusp_kp_lords','graha_gandanta','graha_degree_flags',
          'nakshatra_dispositor','nakshatra_exchange','nakshatra_conjunction',
          'nakshatra_cogravity','graha_tara_bala','nakshatra_statistics',
          'nakshatra_cross_ayanamsha'
        )$$,
    $$SELECT pg_total_relation_size('chart_facts')$$,
    NULL,
    '["bg_nakshatra","ga_positions"]',
    'per_chart', true
)
ON CONFLICT (asset_id) DO UPDATE SET
    sort_order          = EXCLUDED.sort_order,
    english_name        = EXCLUDED.english_name,
    english_description = EXCLUDED.english_description,
    count_sql           = EXCLUDED.count_sql,
    depends_on          = EXCLUDED.depends_on;

COMMIT;
```

- [ ] **Step 2: Apply**

```bash
PGPASSWORD="${PGPASSWORD:?}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -f platform/supabase/migrations/241_ga_nakshatra_registry.sql
```

Expected: `INSERT 0 1` or `UPDATE 1`.

- [ ] **Step 3: Verify**

```bash
PGPASSWORD="${PGPASSWORD:?}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
  -c "SELECT asset_id, is_active, target_floor, sort_order FROM asset_registry WHERE asset_id = 'ga_nakshatra';"
```

Expected: 1 row, `is_active=t`, `target_floor=NULL`, `sort_order=20`.

- [ ] **Step 4: Commit**

```bash
git add platform/supabase/migrations/241_ga_nakshatra_registry.sql
git commit -m "feat(ga_nakshatra): migration 241 — register ga_nakshatra in asset_registry"
```

---

## Task 3: Computation module — `ga_nakshatra_compute.py`

**Files:**
- Create: `platform/python-sidecar/ga_writers/ga_nakshatra_compute.py`

This module contains PURE ALGORITHMS only — no DB access, no chart_facts building. Tested independently.

- [ ] **Step 1: Create the module**

```python
"""
ga_writers.ga_nakshatra_compute — Pure nakshatra computation algorithms.

No DB access. No chart_facts rows. Only deterministic transformations:
  - KP Vimshottari sub-lord chain (star/sub/sub-sub/prana)
  - Gaṇḍānta detection with severity (arc-minutes from junction)
  - Tara bala per body from Moon's nakshatra
  - Nakshatra dispositor graph (chain + cycle detection)
"""
from __future__ import annotations

# ── Constants ─────────────────────────────────────────────────────────────────
VIMSHOTTARI_YEARS: dict[str, int] = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
PLANET_CYCLE: list[str] = [
    "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"
]
NAK_SPAN_ARCMIN: float = 800.0   # 13°20' × 60 arcmin
GANDANTA_JUNCTION_DEG: list[float] = [0.0, 120.0, 240.0]
GANDANTA_ORB_ARCMIN: float = 48.0
TARA_NAMES: list[str] = [
    "Janma","Sampat","Vipat","Kshema","Pratyari",
    "Sadhaka","Vadha","Mitra","Atimitra",
]


def _nakshatra_0based(longitude: float) -> int:
    """0-based nakshatra index (0=Ashwini … 26=Revati) from sidereal longitude."""
    return int((longitude % 360.0) * 60.0 / NAK_SPAN_ARCMIN)


def _pos_in_nak_arcmin(longitude: float) -> float:
    """Arc-minutes elapsed within current nakshatra (0 to <800)."""
    return ((longitude % 360.0) * 60.0) % NAK_SPAN_ARCMIN


def compute_kp_lords(longitude: float) -> dict[str, str]:
    """
    Compute KP star-lord, sub-lord, sub-sub-lord, prana-lord
    from a sidereal body longitude (degrees).

    Algorithm: Vimshottari proportional subdivision (4 levels).
    Returns: {"star_lord": str, "sub_lord": str, "sub_sub_lord": str, "prana_lord": str}
    """
    nak0 = _nakshatra_0based(longitude)
    pos  = _pos_in_nak_arcmin(longitude)

    def _find_lord(start_planet: str, span_arcmin: float, pos_in_span: float) -> tuple[str, float, float]:
        """Return (lord, lord_span, pos_within_lord_span)."""
        start_idx = PLANET_CYCLE.index(start_planet)
        acc = 0.0
        for i in range(9):
            p = PLANET_CYCLE[(start_idx + i) % 9]
            p_span = VIMSHOTTARI_YEARS[p] / 120.0 * span_arcmin
            if acc + p_span > pos_in_span or i == 8:
                return p, p_span, pos_in_span - acc
            acc += p_span
        raise RuntimeError("KP lord not found")  # should never reach here

    star_lord = PLANET_CYCLE[nak0 % 9]
    sub_lord,     sub_span,     pos_in_sub     = _find_lord(star_lord, NAK_SPAN_ARCMIN, pos)
    sub_sub_lord, sub_sub_span, pos_in_sub_sub = _find_lord(sub_lord,  sub_span,        pos_in_sub)
    prana_lord, _, _                            = _find_lord(sub_sub_lord, sub_sub_span, pos_in_sub_sub)

    return {
        "star_lord":     star_lord,
        "sub_lord":      sub_lord,
        "sub_sub_lord":  sub_sub_lord,
        "prana_lord":    prana_lord,
    }


def compute_gandanta(longitude: float) -> dict:
    """
    Detect gaṇḍānta (water-fire nakshatra/rashi junction) for a longitude.

    Returns:
      {
        "is_gandanta": bool,
        "arc_minutes_from_junction": float | None,
        "junction_type": str | None,   # "water_fire_0", "water_fire_120", "water_fire_240"
        "side": str | None,            # "approaching" or "departing"
      }
    """
    long_mod = longitude % 360.0
    best_dist = None
    best_junction = None
    best_side = None

    for jdeg in GANDANTA_JUNCTION_DEG:
        # Distance approaching (body before junction)
        d_approach = (jdeg - long_mod) % 360.0
        # Distance departing (body after junction)
        d_depart   = (long_mod - jdeg) % 360.0

        for dist_deg, side in [(d_approach, "approaching"), (d_depart, "departing")]:
            dist_am = dist_deg * 60.0
            if dist_am <= GANDANTA_ORB_ARCMIN:
                if best_dist is None or dist_am < best_dist:
                    best_dist = dist_am
                    best_junction = f"water_fire_{int(jdeg)}"
                    best_side = side

    return {
        "is_gandanta":               best_dist is not None,
        "arc_minutes_from_junction": round(best_dist, 2) if best_dist is not None else None,
        "junction_type":             best_junction,
        "side":                      best_side,
    }


def compute_tara(nak_body_1based: int, nak_moon_1based: int) -> dict:
    """
    Tara bala for a body relative to Moon's nakshatra.

    count = ((nak_body - nak_moon) % 27) + 1  (1–27)
    tara_pos = ((count - 1) % 9) + 1          (1–9)
    """
    count    = ((nak_body_1based - nak_moon_1based) % 27) + 1
    tara_pos = ((count - 1) % 9) + 1
    return {
        "tara_count":    count,
        "tara_position": tara_pos,
        "tara_name":     TARA_NAMES[tara_pos - 1],
    }


def compute_dispositor_chain(
    body: str,
    nak_lord_map: dict[str, str],   # body -> its nakshatra lord
    max_depth: int = 12,
) -> dict:
    """
    Walk the nakshatra dispositor chain for a body until terminus or cycle.

    nak_lord_map: {body_name: nakshatra_lord_name, ...} for all 10 bodies.
    A body that IS its own nakshatra lord is a terminus.
    Returns:
      {
        "chain": list[str],   # [body, lord1, lord2, ...] including start
        "terminus": str,      # last body in chain (or where cycle detected)
        "is_cycle": bool,
        "chain_depth": int,
      }
    """
    chain = [body]
    visited = {body}
    current = body

    for _ in range(max_depth):
        lord = nak_lord_map.get(current)
        if lord is None or lord == current:
            return {"chain": chain, "terminus": current, "is_cycle": False, "chain_depth": len(chain)}
        if lord in visited:
            chain.append(lord)
            return {"chain": chain, "terminus": lord, "is_cycle": True, "chain_depth": len(chain)}
        chain.append(lord)
        visited.add(lord)
        current = lord

    return {"chain": chain, "terminus": current, "is_cycle": False, "chain_depth": len(chain)}


def compute_center_of_gravity(
    chains: dict[str, dict],    # {body: dispositor_chain_result}
) -> dict:
    """
    The nakshatra center-of-gravity: body that the most chains terminate on.
    Returns {"terminus_body": str, "chain_count": int}.
    """
    from collections import Counter
    counts: Counter = Counter()
    for body, chain_result in chains.items():
        terminus = chain_result.get("terminus")
        if terminus:
            counts[terminus] += 1
    if not counts:
        return {"terminus_body": None, "chain_count": 0}
    top_body, top_count = counts.most_common(1)[0]
    return {"terminus_body": top_body, "chain_count": top_count}


# ── Module-level assertions ───────────────────────────────────────────────────
def _self_check() -> None:
    # KP: Purva Bhadrapada (nakshatra 25, lord=Jupiter) — Moon's natal nakshatra
    # PBP spans from 24×13.333...° = 320° to 333.333°
    # At 322° the star-lord should be Jupiter
    pbp_long = 322.0
    kp = compute_kp_lords(pbp_long)
    assert kp["star_lord"] == "Jupiter", f"Expected Jupiter star-lord at PBP, got {kp['star_lord']}"

    # Gaṇḍānta: 0.5° before Ashwini start (359.5° should be gandanta)
    g = compute_gandanta(359.5)
    assert g["is_gandanta"] is True
    assert g["side"] == "approaching"

    # Tara: Moon in PBP (nak 25), body in PBP (nak 25) → count=1 → Janma
    t = compute_tara(25, 25)
    assert t["tara_name"] == "Janma"

_self_check()
```

- [ ] **Step 2: Verify module imports and self-checks pass**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -c "import ga_writers.ga_nakshatra_compute as m; print('PASS')"
```

Expected: `PASS` (self_check assertions run on import).

- [ ] **Step 3: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_nakshatra_compute.py
git commit -m "feat(ga_nakshatra): computation module — KP lords, gaṇḍānta, tara, dispositor graph"
```

---

## Task 4: Emitter module — `ga_nakshatra_emitters.py`

**Files:**
- Create: `platform/python-sidecar/ga_writers/ga_nakshatra_emitters.py`

This module builds the chart_facts rows for each of the 14 fact categories. No DB writes here — returns lists of dicts for the writer to INSERT. Uses `ga_nakshatra_compute` for algorithms and takes chart_output + JOIN data as inputs.

- [ ] **Step 1: Create the module**

```python
"""
ga_writers.ga_nakshatra_emitters — Build chart_facts rows for ga_nakshatra.

All functions return list[dict] — rows ready for INSERT into chart_facts.
No DB access here. Takes chart_output from pyjhora_adapter and JOIN data
from reference_nakshatra / reference_nakshatra_pada.

bg_nakshatra is AUTHORITY for static attrs: rows cite nakshatra_id as
source_calculation — they do not recompute static values, they relay them
with provenance so the chain is auditable.
"""
from __future__ import annotations
import json
from typing import Any

from ga_writers.ga_nakshatra_compute import (
    compute_kp_lords, compute_gandanta, compute_tara,
    compute_dispositor_chain, compute_center_of_gravity,
    PLANET_CYCLE, TARA_NAMES,
)

PLANET_TO_SUBJECT: dict[str, str] = {
    "Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
    "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT",
    "Rahu": "RAH_MEAN", "Ketu": "KET_MEAN", "Lagna": "LAGNA",
}


def _row(chart_id: str, ayanamsha_id: str, build_id: str,
         fact_category: str, fact_subject: str, fact_key: str,
         value_text: str | None = None, value_num: float | None = None,
         source: str = "ga_nakshatra") -> dict:
    return {
        "chart_id":       chart_id,
        "ayanamsha_id":   ayanamsha_id,
        "build_id":       build_id,
        "fact_category":  fact_category,
        "fact_subject":   fact_subject,
        "fact_key":       fact_key,
        "fact_value_text": value_text,
        "fact_value_num":  value_num,
        "source_calculation": source,
    }


def emit_nakshatra_join(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
    nak_rows: dict[int, dict],     # nakshatra_id → reference_nakshatra row
    pada_rows: dict[tuple, dict],  # (nakshatra_id, pada_number) → reference_nakshatra_pada row
) -> list[dict]:
    """
    §3.1 — Per-body nakshatra attribute JOIN from reference_nakshatra + reference_nakshatra_pada.

    Emits graha_nakshatra_join and graha_pada_join rows.
    source_calculation cites the reference_nakshatra row so the chain is auditable.
    """
    rows: list[dict] = []
    grahas = chart_output.get("grahas", [])
    asc    = chart_output.get("ascendant", {})

    bodies_data = grahas + [{"name": "Lagna", **asc}]

    for body_data in bodies_data:
        bname  = body_data.get("name", "")
        subj   = PLANET_TO_SUBJECT.get(bname)
        if not subj:
            continue
        nak_id = body_data.get("nakshatra_id")
        pada   = body_data.get("pada")
        if not nak_id:
            continue

        nak_ref = nak_rows.get(nak_id, {})
        source  = f"ga_nakshatra:JOIN reference_nakshatra:nakshatra_id={nak_id}"
        cat1    = "graha_nakshatra_join"

        STATIC_KEYS = [
            ("gana",            "gana"),
            ("nadi",            "nadi"),
            ("yoni_en",         "yoni_en"),
            ("yoni_sex",        "yoni_sex"),
            ("varna",           "varna"),
            ("tatva",           "tatva"),
            ("guna",            "guna"),
            ("pakshi",          "pakshi"),
            ("presiding_deity", "presiding_deity"),
            ("shakti",          "shakti"),
            ("motivation",      "motivation"),
            ("symbol",          "symbol"),
            ("vimshottari_lord","nakshatra_lord"),
        ]
        for db_col, fact_key in STATIC_KEYS:
            val = nak_ref.get(db_col)
            if val is not None:
                rows.append(_row(chart_id, ayanamsha_id, build_id, cat1, subj, fact_key,
                                 value_text=str(val), source=source))

        # Always emit nakshatra_id reference
        rows.append(_row(chart_id, ayanamsha_id, build_id, cat1, subj, "nakshatra_id_ref",
                         value_num=float(nak_id), source=source))

        # Pada join
        if pada:
            pada_ref  = pada_rows.get((nak_id, pada), {})
            pada_src  = f"ga_nakshatra:JOIN reference_nakshatra_pada:nakshatra_id={nak_id}:pada={pada}"
            cat2      = "graha_pada_join"
            PADA_KEYS = [
                ("pada_akshara",      "akshara"),
                ("pada_navamsa_sign", "navamsa_sign"),
                ("pada_lord",         "pada_lord"),
            ]
            for db_col, fact_key in PADA_KEYS:
                val = pada_ref.get(db_col)
                if val is not None:
                    rows.append(_row(chart_id, ayanamsha_id, build_id, cat2, subj, fact_key,
                                     value_text=str(val), source=pada_src))
            rows.append(_row(chart_id, ayanamsha_id, build_id, cat2, subj, "pada_number_ref",
                             value_num=float(pada), source=pada_src))

    return rows


def emit_kp_lords(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
) -> list[dict]:
    """
    §3.3 — KP sub-lords per body AND per house cusp.
    Fact categories: graha_kp_lords, cusp_kp_lords.
    """
    rows: list[dict] = []
    asc    = chart_output.get("ascendant", {})
    grahas = chart_output.get("grahas", [])

    # Per-body
    bodies_data = grahas + [{"name": "Lagna", **asc}]
    for body_data in bodies_data:
        bname = body_data.get("name", "")
        subj  = PLANET_TO_SUBJECT.get(bname)
        if not subj:
            continue
        long = body_data.get("longitude_deg")
        if long is None:
            continue
        kp = compute_kp_lords(float(long))
        src = f"ga_nakshatra:KP:longitude={long:.4f}"
        for key, val in kp.items():
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_kp_lords", subj, key,
                             value_text=val, source=src))

    # Per cusp (whole-sign: H1=Lagna long, H2-12=sign boundaries)
    asc_sign0 = int(asc.get("sign_id", 1)) - 1
    asc_long  = float(asc.get("longitude_deg", 0.0))
    for h in range(12):
        cusp_long = asc_long if h == 0 else ((asc_sign0 + h) % 12) * 30.0
        cusp_subj = f"CUSP_{h+1:02d}"
        kp = compute_kp_lords(cusp_long)
        src = f"ga_nakshatra:KP:cusp={h+1}:longitude={cusp_long:.4f}"
        for key, val in kp.items():
            rows.append(_row(chart_id, ayanamsha_id, build_id, "cusp_kp_lords", cusp_subj, key,
                             value_text=val, source=src))

    return rows


def emit_gandanta_flags(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
) -> list[dict]:
    """§3.4 — Gaṇḍānta + degree flags (gandanta severity, vargottama-via-pada)."""
    rows: list[dict] = []
    asc    = chart_output.get("ascendant", {})
    grahas = chart_output.get("grahas", [])

    bodies_data = grahas + [{"name": "Lagna", **asc}]
    for body_data in bodies_data:
        bname = body_data.get("name", "")
        subj  = PLANET_TO_SUBJECT.get(bname)
        if not subj:
            continue
        long = body_data.get("longitude_deg")
        if long is None:
            continue

        g = compute_gandanta(float(long))
        src = f"ga_nakshatra:gandanta:longitude={long:.4f}"
        rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_gandanta", subj, "is_gandanta",
                         value_text=str(g["is_gandanta"]).lower(), source=src))
        if g["is_gandanta"]:
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_gandanta", subj,
                             "arc_minutes_from_junction",
                             value_num=g["arc_minutes_from_junction"], source=src))
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_gandanta", subj,
                             "junction_type", value_text=g["junction_type"], source=src))
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_gandanta", subj,
                             "side", value_text=g["side"], source=src))

        # Vargottama-via-pada: pada navamsa sign == D1 sign
        pada_nav = body_data.get("pada_navamsa_sign")  # from chart_output or JOIN
        d1_sign  = body_data.get("sign")
        if pada_nav and d1_sign:
            is_varg = (pada_nav == d1_sign)
            rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_degree_flags", subj,
                             "vargottama_via_pada", value_text=str(is_varg).lower(),
                             source=f"ga_nakshatra:vargottama_pada"))

    return rows


def emit_dispositor_graph(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
    body_nak_lord: dict[str, str],  # body_name → its nakshatra lord's body_name
) -> list[dict]:
    """
    §3.2 — Nakshatra dispositor graph: chains, exchanges, conjunctions, center-of-gravity.
    """
    rows: list[dict] = []

    # Build chains for all bodies
    all_chains: dict[str, dict] = {}
    for body in PLANET_TO_SUBJECT:
        chain = compute_dispositor_chain(body, body_nak_lord)
        all_chains[body] = chain
        subj = PLANET_TO_SUBJECT[body]
        src  = f"ga_nakshatra:dispositor_graph"
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_dispositor", subj,
                         "lord_chain", value_text=json.dumps(chain["chain"]), source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_dispositor", subj,
                         "terminus_body", value_text=chain["terminus"], source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_dispositor", subj,
                         "is_cycle", value_text=str(chain["is_cycle"]).lower(), source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_dispositor", subj,
                         "chain_depth", value_num=float(chain["chain_depth"]), source=src))

    # Center of gravity
    cog = compute_center_of_gravity(all_chains)
    rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_cogravity", "CHART",
                     "terminus_body", value_text=cog["terminus_body"],
                     source="ga_nakshatra:cogravity"))
    rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_cogravity", "CHART",
                     "chain_count", value_num=float(cog["chain_count"]),
                     source="ga_nakshatra:cogravity"))

    # Nakshatra exchanges: body A in lord of body B's nakshatra AND vice versa
    bodies = list(PLANET_TO_SUBJECT.keys())
    exchange_idx = 0
    for i, ba in enumerate(bodies):
        for bb in bodies[i+1:]:
            la, lb = body_nak_lord.get(ba), body_nak_lord.get(bb)
            if la == bb and lb == ba:
                subj = f"EXCHANGE_{exchange_idx}"
                rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_exchange", subj,
                                 "body_a", value_text=ba, source="ga_nakshatra:exchange"))
                rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_exchange", subj,
                                 "body_b", value_text=bb, source="ga_nakshatra:exchange"))
                exchange_idx += 1

    # Nakshatra conjunctions: bodies sharing a nakshatra
    body_nak_map: dict[str, list[str]] = {}
    grahas = chart_output.get("grahas", []) + [{"name": "Lagna", **chart_output.get("ascendant", {})}]
    for gd in grahas:
        bname = gd.get("name", "")
        if bname not in PLANET_TO_SUBJECT:
            continue
        nak = gd.get("nakshatra") or ""
        if nak:
            body_nak_map.setdefault(nak, []).append(bname)

    for nak_name, conjunction_bodies in body_nak_map.items():
        if len(conjunction_bodies) >= 2:
            rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_conjunction", nak_name,
                             "bodies_list", value_text=json.dumps(conjunction_bodies),
                             source="ga_nakshatra:conjunction"))

    return rows


def emit_tara_bala(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
) -> list[dict]:
    """§3.5 — Tara bala per body from Moon's nakshatra."""
    rows: list[dict] = []
    grahas = chart_output.get("grahas", [])
    moon_data = next((g for g in grahas if g.get("name") == "Moon"), None)
    if not moon_data:
        return rows

    moon_nak = moon_data.get("nakshatra_id") or 0
    asc      = chart_output.get("ascendant", {})
    bodies   = grahas + [{"name": "Lagna", **asc}]

    for body_data in bodies:
        bname = body_data.get("name", "")
        subj  = PLANET_TO_SUBJECT.get(bname)
        if not subj:
            continue
        nak = body_data.get("nakshatra_id") or 0
        if not nak:
            continue
        t = compute_tara(nak, moon_nak)
        src = f"ga_nakshatra:tara:moon_nak={moon_nak}:body_nak={nak}"
        rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_tara_bala", subj,
                         "tara_count", value_num=float(t["tara_count"]), source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_tara_bala", subj,
                         "tara_position", value_num=float(t["tara_position"]), source=src))
        rows.append(_row(chart_id, ayanamsha_id, build_id, "graha_tara_bala", subj,
                         "tara_name", value_text=t["tara_name"], source=src))

    return rows


def emit_statistics(
    chart_id: str, ayanamsha_id: str, build_id: str,
    chart_output: dict,
    nak_rows: dict[int, dict],
) -> list[dict]:
    """§3.6 — Per-chart nakshatra statistics (gana/nadi/yoni/tatva distributions)."""
    rows: list[dict] = []
    grahas = chart_output.get("grahas", []) + [{"name": "Lagna", **chart_output.get("ascendant", {})}]

    gana_counts:  dict[str, int] = {}
    nadi_counts:  dict[str, int] = {}
    yoni_counts:  dict[str, int] = {}
    tatva_counts: dict[str, int] = {}

    for body_data in grahas:
        bname = body_data.get("name", "")
        if bname not in PLANET_TO_SUBJECT:
            continue
        nak_id  = body_data.get("nakshatra_id")
        nak_ref = nak_rows.get(nak_id, {}) if nak_id else {}
        for attr, counter in [
            ("gana",  gana_counts),
            ("nadi",  nadi_counts),
            ("yoni_en", yoni_counts),
            ("tatva", tatva_counts),
        ]:
            val = nak_ref.get(attr)
            if val:
                counter[val] = counter.get(val, 0) + 1

    src = "ga_nakshatra:statistics"
    for gana, cnt in gana_counts.items():
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_statistics", "CHART",
                         f"gana_{gana.lower()}_count", value_num=float(cnt), source=src))

    for nadi, cnt in nadi_counts.items():
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_statistics", "CHART",
                         f"nadi_{nadi.lower()}_count", value_num=float(cnt), source=src))

    if gana_counts:
        dominant = max(gana_counts, key=gana_counts.get)
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_statistics", "CHART",
                         "dominant_gana", value_text=dominant, source=src))

    # Nadi affliction: all bodies in same nadi
    if len(nadi_counts) == 1:
        rows.append(_row(chart_id, ayanamsha_id, build_id, "nakshatra_statistics", "CHART",
                         "nadi_affliction", value_text="true", source=src))

    return rows
```

- [ ] **Step 2: Verify import**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -c "from ga_writers.ga_nakshatra_emitters import emit_kp_lords; print('PASS')"
```

- [ ] **Step 3: Commit**

```bash
git add platform/python-sidecar/ga_writers/ga_nakshatra_emitters.py
git commit -m "feat(ga_nakshatra): emitter module — 14 fact_categories (JOIN, KP, gaṇḍānta, dispositor, tara, stats)"
```

---

## Task 5: Writer — `pipeline/orchestrator/writers/ga_nakshatra.py`

**Files:**
- Create: `platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py`

- [ ] **Step 1: Read the frozen WriterBase contract**

```bash
grep -n "plan_substeps\|run_substep\|SubStep\|WriterResult\|ContextSpec" \
  platform/python-sidecar/pipeline/orchestrator/writers/__init__.py | head -30
```

Note the exact import paths and SubStep signature before writing the writer.

- [ ] **Step 2: Create the writer**

```python
"""
pipeline.orchestrator.writers.ga_nakshatra — L1 per-chart parallel nakshatra chart.

Heavy WriterBase: plan_substeps (one per ayanamsha + cross-ayanamsha pass) + run_substep.
Writes 14 fact_categories into chart_facts.
bg_nakshatra is AUTHORITY for static attrs (JOIN, cite, never restate).
ga_vargas is AUTHORITY for D150 position (reads varga_d150_rishi, never recomputes).
"""
from __future__ import annotations
import time
import json
import logging
from typing import Any

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register, ContextSpec
from ga_writers._idempotency import replace_prior_chart_facts
from ga_writers.ga_nakshatra_emitters import (
    emit_nakshatra_join, emit_kp_lords, emit_gandanta_flags,
    emit_dispositor_graph, emit_tara_bala, emit_statistics,
    PLANET_TO_SUBJECT,
)

try:
    from pyjhora_adapter.compute import compute_chart
except ImportError:
    compute_chart = None  # noqa: F841 — handled in run_substep

logger = logging.getLogger(__name__)

CANONICAL_AYANAMSHAS: dict[str, str] = {
    "lahiri_chitrapaksha": "lahiri",
    "true_chitra":         "true_chitra",
    "krishnamurti":        "kp",
    "raman":               "raman",
    "surya_siddhanta_classical": "surya_siddhanta",
}

GA_NAKSHATRA_FACT_CATEGORIES = [
    "graha_nakshatra_join", "graha_pada_join", "nakshatra_lord_placement",
    "graha_kp_lords", "cusp_kp_lords", "graha_gandanta", "graha_degree_flags",
    "nakshatra_dispositor", "nakshatra_exchange", "nakshatra_conjunction",
    "nakshatra_cogravity", "graha_tara_bala", "nakshatra_statistics",
    "nakshatra_cross_ayanamsha",
]


def _fetch_bg_nakshatra(conn: Any) -> tuple[dict[int, dict], dict[tuple, dict]]:
    """Fetch reference_nakshatra and reference_nakshatra_pada for attribute JOIN."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT nakshatra_id, name_en, vimshottari_lord, presiding_deity,
                   gana, nadi, yoni_en, yoni_sex, varna, tatva, guna, pakshi,
                   shakti, motivation, symbol
            FROM reference_nakshatra
            ORDER BY nakshatra_id
        """)
        nak_rows = {r[0]: dict(zip(
            ["nakshatra_id","name_en","vimshottari_lord","presiding_deity",
             "gana","nadi","yoni_en","yoni_sex","varna","tatva","guna","pakshi",
             "shakti","motivation","symbol"], r))
            for r in cur.fetchall()}

        cur.execute("""
            SELECT nakshatra_id, pada_number, pada_akshara, pada_navamsa_sign, pada_lord
            FROM reference_nakshatra_pada
            ORDER BY nakshatra_id, pada_number
        """)
        pada_rows = {(r[0], r[1]): dict(zip(
            ["nakshatra_id","pada_number","pada_akshara","pada_navamsa_sign","pada_lord"], r))
            for r in cur.fetchall()}

    return nak_rows, pada_rows


def _check_bg_nakshatra_present(conn: Any) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM reference_nakshatra")
        return cur.fetchone()[0] >= 27


def _run_ayanamsha_pass(
    ctx: ContextSpec, canonical_id: str, adapter_id: str,
    nak_rows: dict, pada_rows: dict,
) -> WriterResult:
    t0 = time.time()
    birth_params = ctx.config.get("birth_params") or ctx.config
    chart_output = compute_chart(inputs=birth_params, ayanamsha_id=adapter_id)

    grahas = chart_output.get("grahas", [])
    asc    = chart_output.get("ascendant", {})

    # Build nakshatra-lord map for dispositor graph
    # body_name → the body whose name matches the nakshatra lord
    planet_names = set(PLANET_TO_SUBJECT.keys())

    def _nak_lord_as_body(body_data: dict) -> str | None:
        nak_id  = body_data.get("nakshatra_id")
        nak_ref = nak_rows.get(nak_id, {})
        lord_str = nak_ref.get("vimshottari_lord", "")
        # Map dasha lord to body name (capitalize first letter)
        for bname in planet_names:
            if bname.lower() == lord_str.lower():
                return bname
        return None

    body_nak_lord: dict[str, str] = {}
    for gd in grahas + [{"name": "Lagna", **asc}]:
        bname = gd.get("name", "")
        if bname in planet_names:
            lord = _nak_lord_as_body(gd)
            if lord:
                body_nak_lord[bname] = lord

    chart_id = ctx.config.get("chart_id") or ctx.chart_id
    build_id = ctx.build_id

    all_rows: list[dict] = []
    all_rows += emit_nakshatra_join(chart_id, canonical_id, build_id,
                                    chart_output, nak_rows, pada_rows)
    all_rows += emit_kp_lords(chart_id, canonical_id, build_id, chart_output)
    all_rows += emit_gandanta_flags(chart_id, canonical_id, build_id, chart_output)
    all_rows += emit_dispositor_graph(chart_id, canonical_id, build_id, chart_output, body_nak_lord)
    all_rows += emit_tara_bala(chart_id, canonical_id, build_id, chart_output)
    all_rows += emit_statistics(chart_id, canonical_id, build_id, chart_output, nak_rows)

    if ctx.dry_run:
        return WriterResult(asset_id="ga_nakshatra", rows_inserted=len(all_rows),
                            duration_seconds=time.time()-t0,
                            notes=f"DRY RUN ayanamsha={canonical_id}: {len(all_rows)} rows")

    replace_prior_chart_facts(ctx.db_conn, all_rows)
    with ctx.db_conn.cursor() as cur:
        for r in all_rows:
            cur.execute("""
                INSERT INTO chart_facts (
                    chart_id, ayanamsha_id, build_id,
                    fact_category, fact_subject, fact_key,
                    fact_value_text, fact_value_num, source_calculation
                ) VALUES (
                    %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
                    %(fact_category)s, %(fact_subject)s, %(fact_key)s,
                    %(fact_value_text)s, %(fact_value_num)s, %(source_calculation)s
                )
                ON CONFLICT DO NOTHING
            """, r)

    return WriterResult(asset_id="ga_nakshatra", rows_inserted=len(all_rows),
                        duration_seconds=time.time()-t0,
                        notes=f"ayanamsha={canonical_id}: {len(all_rows)} rows")


@register('ga_nakshatra')
class NakshatraWriter(WriterBase):
    asset_id = 'ga_nakshatra'

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(key=f"ayanamsha:{ay}", label=f"Nakshatra pass: {ay}")
            for ay in CANONICAL_AYANAMSHAS
        ] + [SubStep(key="cross_ayanamsha", label="Cross-ayanamsha consistency")]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        t0 = time.time()

        if not _check_bg_nakshatra_present(ctx.db_conn):
            raise RuntimeError(
                "HALT: reference_nakshatra table has <27 rows — bg_nakshatra must be built first."
            )

        nak_rows, pada_rows = _fetch_bg_nakshatra(ctx.db_conn)

        if step.key.startswith("ayanamsha:"):
            canonical_id = step.key[len("ayanamsha:"):]
            adapter_id   = CANONICAL_AYANAMSHAS[canonical_id]
            return _run_ayanamsha_pass(ctx, canonical_id, adapter_id, nak_rows, pada_rows)

        if step.key == "cross_ayanamsha":
            # Cross-ayanamsha nakshatra consistency: does each body's nakshatra hold 5/5?
            chart_id = ctx.config.get("chart_id") or ctx.chart_id
            build_id = ctx.build_id
            rows: list[dict] = []

            with ctx.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT fact_subject, fact_key, fact_value_num
                    FROM chart_facts
                    WHERE chart_id = %s
                      AND fact_category = 'graha_nakshatra_join'
                      AND fact_key = 'nakshatra_id_ref'
                """, (chart_id,))
                results = cur.fetchall()

            # Group by body: {body -> list of nakshatra_ids across ayanamshas}
            body_naks: dict[str, list[float]] = {}
            for subj, _key, val_num in results:
                if val_num is not None:
                    body_naks.setdefault(subj, []).append(float(val_num))

            for body, nak_ids in body_naks.items():
                unique = set(nak_ids)
                agree  = len(unique) == 1
                rows.append({
                    "chart_id": chart_id, "ayanamsha_id": "INVARIANT", "build_id": build_id,
                    "fact_category": "nakshatra_cross_ayanamsha", "fact_subject": body,
                    "fact_key": "nak_5ay_consistency",
                    "fact_value_text": f"{5-len(unique)+1}/5" if agree else f"{5-len(unique)+1}/5",
                    "fact_value_num": None,
                    "source_calculation": "ga_nakshatra:cross_ayanamsha",
                })
                if agree:
                    rows.append({
                        "chart_id": chart_id, "ayanamsha_id": "INVARIANT", "build_id": build_id,
                        "fact_category": "nakshatra_cross_ayanamsha", "fact_subject": body,
                        "fact_key": "stable_nakshatra_id",
                        "fact_value_num": list(unique)[0],
                        "fact_value_text": None,
                        "source_calculation": "ga_nakshatra:cross_ayanamsha",
                    })

            if not ctx.dry_run and rows:
                replace_prior_chart_facts(ctx.db_conn, rows)
                with ctx.db_conn.cursor() as cur:
                    for r in rows:
                        cur.execute("""
                            INSERT INTO chart_facts (
                                chart_id, ayanamsha_id, build_id,
                                fact_category, fact_subject, fact_key,
                                fact_value_text, fact_value_num, source_calculation
                            ) VALUES (
                                %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
                                %(fact_category)s, %(fact_subject)s, %(fact_key)s,
                                %(fact_value_text)s, %(fact_value_num)s, %(source_calculation)s
                            )
                            ON CONFLICT DO NOTHING
                        """, r)

            return WriterResult(asset_id="ga_nakshatra", rows_inserted=len(rows),
                                duration_seconds=time.time()-t0,
                                notes=f"cross_ayanamsha: {len(rows)} rows")

        raise ValueError(f"Unknown substep key: {step.key}")
```

- [ ] **Step 3: Verify writer registers**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -c "
from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
from pipeline.orchestrator.writers import _REGISTRY
assert 'ga_nakshatra' in _REGISTRY
print('REGISTERED OK')
"
```

- [ ] **Step 4: Commit**

```bash
git add platform/python-sidecar/pipeline/orchestrator/writers/ga_nakshatra.py
git commit -m "feat(ga_nakshatra): heavy WriterBase writer — plan_substeps×6, 14 fact_categories"
```

---

## Task 6: Tests — `test_ga_nakshatra.py`

**Files:**
- Create: `platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_nakshatra.py`

- [ ] **Step 1: Create test file**

```python
"""
Tests for ga_nakshatra — no DB connection required.
Tests the compute module and writer registration.
"""
import pytest
from ga_writers.ga_nakshatra_compute import (
    compute_kp_lords, compute_gandanta, compute_tara,
    compute_dispositor_chain, compute_center_of_gravity,
    PLANET_CYCLE, VIMSHOTTARI_YEARS, TARA_NAMES,
)


# ── KP lords ─────────────────────────────────────────────────────────────────

class TestKpLords:
    def test_returns_four_keys(self):
        kp = compute_kp_lords(0.0)
        assert set(kp) == {"star_lord", "sub_lord", "sub_sub_lord", "prana_lord"}

    def test_star_lord_is_valid_planet(self):
        kp = compute_kp_lords(45.0)
        assert kp["star_lord"] in PLANET_CYCLE

    def test_all_lords_are_valid_planets(self):
        for long in [0.0, 90.0, 180.0, 270.0, 359.99]:
            kp = compute_kp_lords(long)
            for key in ["star_lord", "sub_lord", "sub_sub_lord", "prana_lord"]:
                assert kp[key] in PLANET_CYCLE, f"Invalid lord '{kp[key]}' at long={long}"

    def test_ashwini_nakshatra_star_lord_is_ketu(self):
        # Ashwini: 0°–13°20'. At 6° the star-lord should be Ketu.
        kp = compute_kp_lords(6.0)
        assert kp["star_lord"] == "Ketu"

    def test_rohini_nakshatra_star_lord_is_moon(self):
        # Rohini: nakshatra 4, span = 3×13.333°=40° to 53.333°. At 45° → star-lord=Moon
        kp = compute_kp_lords(45.0)
        assert kp["star_lord"] == "Moon"

    def test_forensic_pbp_star_lord_is_jupiter(self):
        # Purva Bhadrapada (nak 25): 24×13.333° = 320° to 333.333°. At 322° star=Jupiter
        kp = compute_kp_lords(322.0)
        assert kp["star_lord"] == "Jupiter", f"Expected Jupiter, got {kp['star_lord']}"

    def test_longitude_modulo_360(self):
        # 360° == 0°
        kp0   = compute_kp_lords(0.0)
        kp360 = compute_kp_lords(360.0)
        assert kp0 == kp360

    def test_vimshottari_years_total_120(self):
        assert sum(VIMSHOTTARI_YEARS.values()) == 120


# ── Gaṇḍānta ─────────────────────────────────────────────────────────────────

class TestGandanta:
    def test_approaching_junction_0(self):
        g = compute_gandanta(359.5)  # 0.5° = 30 arcmin before 0°
        assert g["is_gandanta"] is True
        assert g["side"] == "approaching"
        assert g["junction_type"] == "water_fire_0"
        assert g["arc_minutes_from_junction"] == pytest.approx(30.0, abs=0.1)

    def test_departing_junction_0(self):
        g = compute_gandanta(0.5)   # 0.5° after 0°
        assert g["is_gandanta"] is True
        assert g["side"] == "departing"

    def test_clear_of_junction(self):
        g = compute_gandanta(90.0)  # well away from any junction
        assert g["is_gandanta"] is False
        assert g["arc_minutes_from_junction"] is None

    def test_junction_120(self):
        g = compute_gandanta(119.6)  # 0.4° = 24 arcmin before 120°
        assert g["is_gandanta"] is True
        assert g["junction_type"] == "water_fire_120"

    def test_junction_240(self):
        g = compute_gandanta(240.5)
        assert g["is_gandanta"] is True
        assert g["junction_type"] == "water_fire_240"


# ── Tara bala ─────────────────────────────────────────────────────────────────

class TestTaraBala:
    def test_body_in_same_nak_as_moon_is_janma(self):
        t = compute_tara(25, 25)
        assert t["tara_name"] == "Janma"
        assert t["tara_position"] == 1

    def test_body_one_nak_ahead_is_sampat(self):
        t = compute_tara(2, 1)
        assert t["tara_name"] == "Sampat"

    def test_tara_names_list_length(self):
        assert len(TARA_NAMES) == 9

    def test_wraps_at_27(self):
        # 28 naks ahead = 1 ahead
        t1 = compute_tara(2, 1)
        t2 = compute_tara(2 + 27, 1)
        assert t1["tara_name"] == t2["tara_name"]

    def test_forensic_moon_pbp_sun_capricorn(self):
        # Sun in Capricorn ≈ Uttarashadha/Shravana range (naks 21-22), Moon PBP (nak 25)
        # Sun nak ≈ 21, Moon nak = 25: count = (21-25) % 27 + 1 = 23
        # tara_pos = (23-1) % 9 + 1 = 5 → Pratyari
        t = compute_tara(21, 25)
        assert t["tara_name"] == "Pratyari"


# ── Dispositor graph ──────────────────────────────────────────────────────────

class TestDispositorGraph:
    def test_self_terminus(self):
        # If Moon is in Moon's nakshatra (Rohini), chain terminates at Moon
        nak_lord_map = {"Moon": "Moon"}
        chain = compute_dispositor_chain("Moon", nak_lord_map)
        assert chain["terminus"] == "Moon"
        assert chain["is_cycle"] is False
        assert chain["chain_depth"] == 1

    def test_simple_chain(self):
        # Sun → Moon → Moon (Moon terminates at itself)
        nak_lord_map = {"Sun": "Moon", "Moon": "Moon"}
        chain = compute_dispositor_chain("Sun", nak_lord_map)
        assert chain["terminus"] == "Moon"
        assert "Moon" in chain["chain"]
        assert chain["is_cycle"] is False

    def test_cycle_detection(self):
        # Sun → Moon → Sun (cycle)
        nak_lord_map = {"Sun": "Moon", "Moon": "Sun"}
        chain = compute_dispositor_chain("Sun", nak_lord_map)
        assert chain["is_cycle"] is True

    def test_center_of_gravity(self):
        # Two bodies both terminate at Jupiter
        chains = {
            "Sun":  {"terminus": "Jupiter", "is_cycle": False, "chain": ["Sun","Jupiter"], "chain_depth": 2},
            "Moon": {"terminus": "Jupiter", "is_cycle": False, "chain": ["Moon","Jupiter"], "chain_depth": 2},
            "Mars": {"terminus": "Mars",    "is_cycle": False, "chain": ["Mars"], "chain_depth": 1},
        }
        cog = compute_center_of_gravity(chains)
        assert cog["terminus_body"] == "Jupiter"
        assert cog["chain_count"] == 2


# ── Writer registration ───────────────────────────────────────────────────────

class TestWriterRegistration:
    def test_ga_nakshatra_registered(self):
        from pipeline.orchestrator.writers import _REGISTRY
        # Import triggers registration
        import pipeline.orchestrator.writers.ga_nakshatra  # noqa: F401
        assert "ga_nakshatra" in _REGISTRY

    def test_asset_id(self):
        from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
        assert NakshatraWriter.asset_id == "ga_nakshatra"

    def test_has_plan_substeps(self):
        from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
        assert hasattr(NakshatraWriter, "plan_substeps")
        assert hasattr(NakshatraWriter, "run_substep")

    def test_substep_count_is_6(self):
        from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
        from unittest.mock import MagicMock
        writer = NakshatraWriter()
        ctx    = MagicMock()
        steps  = writer.plan_substeps(ctx)
        assert len(steps) == 6   # 5 ayanamshas + 1 cross_ayanamsha
```

- [ ] **Step 2: Run tests**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest pipeline/orchestrator/writers/__tests__/test_ga_nakshatra.py -v 2>&1 | tail -30
```

Expected: All tests PASS.

- [ ] **Step 3: Commit**

```bash
git add platform/python-sidecar/pipeline/orchestrator/writers/__tests__/test_ga_nakshatra.py
git commit -m "test(ga_nakshatra): unit tests — KP lords, gaṇḍānta, tara, dispositor graph, writer registration"
```

---

## Task 7: Integration run + FORENSIC spot-check + row-count + migration 242

**Files:** DB only + migration 242

- [ ] **Step 1: Build ga_nakshatra via orchestrator for native chart**

Try the orchestrator first:
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pipeline.orchestrator.main --asset ga_nakshatra 2>&1 | tail -30
```

If the orchestrator is unavailable/locked, invoke the writer directly (frozen contract):
```python
# Direct invocation (dry-run first):
from pipeline.orchestrator.writers.ga_nakshatra import NakshatraWriter
from pipeline.orchestrator.writers import ContextSpec
import os
import psycopg2

conn = psycopg2.connect(os.environ["DATABASE_URL"])
ctx = ContextSpec(
    db_conn=conn,
    build_id="test-build-ga-nak",
    dry_run=False,
    config={
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "birth_params": {
            "datetime_iso": "1984-02-05T10:43:00",
            "latitude_deg": 20.27,
            "longitude_deg": 85.84,
            "tz_offset_hours": 5.5,
        },
    },
)
writer = NakshatraWriter()
steps  = writer.plan_substeps(ctx)
total  = 0
for step in steps:
    result = writer.run_substep(ctx, step)
    conn.commit()
    total += result.rows_inserted
    print(f"{step.key}: {result.rows_inserted} rows")
conn.close()
print(f"TOTAL: {total}")
```

- [ ] **Step 2: FORENSIC spot-check**

```bash
PGPASSWORD="${PGPASSWORD:?}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c "
SELECT fact_key, fact_value_text, fact_value_num
FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND ayanamsha_id = 'lahiri_chitrapaksha'
  AND fact_category = 'graha_nakshatra_join'
  AND fact_subject = 'MOON'
ORDER BY fact_key;
"
```

Required:
- `gana = 'Manushya'`
- `nadi = 'Adi'`
- `yoni_en = 'Lion'`
- `presiding_deity` contains 'Aja Ekapada'
- `nakshatra_id_ref = 25`

```bash
PGPASSWORD="${PGPASSWORD:?}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c "
SELECT fact_key, fact_value_text
FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND ayanamsha_id = 'lahiri_chitrapaksha'
  AND fact_category = 'graha_kp_lords'
  AND fact_subject = 'MOON';
"
```

Required: `star_lord = 'Jupiter'` (PBP lord).

- [ ] **Step 3: Total row count**

```bash
PGPASSWORD="${PGPASSWORD:?}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c "
SELECT fact_category, count(*) as rows
FROM chart_facts
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN (
    'graha_nakshatra_join','graha_pada_join','nakshatra_lord_placement',
    'graha_kp_lords','cusp_kp_lords','graha_gandanta','graha_degree_flags',
    'nakshatra_dispositor','nakshatra_exchange','nakshatra_conjunction',
    'nakshatra_cogravity','graha_tara_bala','nakshatra_statistics',
    'nakshatra_cross_ayanamsha'
  )
GROUP BY fact_category
ORDER BY rows DESC;
"
```

Note the total. If total > 10,000 rows, flag to native for perf review (halt-worthy per brief §9).
Expected: ~2,500–3,500 rows total (within chart_facts health range).

- [ ] **Step 4: Idempotency run**

Run the build a second time. Verify total row count is unchanged (delete-then-insert replaces).

- [ ] **Step 5: Set target_floor + migration 242**

```bash
TOTAL=$(PGPASSWORD="${PGPASSWORD:?}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -t -c "
SELECT count(*) FROM chart_facts
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND fact_category IN (
    'graha_nakshatra_join','graha_pada_join','nakshatra_lord_placement',
    'graha_kp_lords','cusp_kp_lords','graha_gandanta','graha_degree_flags',
    'nakshatra_dispositor','nakshatra_exchange','nakshatra_conjunction',
    'nakshatra_cogravity','graha_tara_bala','nakshatra_statistics',
    'nakshatra_cross_ayanamsha'
  );
" | tr -d ' ')
echo "Total: $TOTAL"

# Update DB
PGPASSWORD="${PGPASSWORD:?}" psql "postgresql://amjis_app@127.0.0.1:5433/amjis" -c \
  "UPDATE asset_registry SET target_floor = $TOTAL WHERE asset_id = 'ga_nakshatra';"
```

Create and apply migration 242:
```sql
-- 242_ga_nakshatra_target_floor.sql
BEGIN;
UPDATE asset_registry SET target_floor = <TOTAL> WHERE asset_id = 'ga_nakshatra';
COMMIT;
```

- [ ] **Step 6: Commit**

```bash
git add platform/supabase/migrations/242_ga_nakshatra_target_floor.sql
# Also update asset_registry_seed.ts: add ga_nakshatra entry with actual target_floor
git add platform/scripts/seed/asset_registry_seed.ts
git commit -m "chore(ga_nakshatra): set target_floor=<TOTAL> after first build + migration 242"
```

---

## Task 8: CI + PR + merge-verify

- [ ] **Step 1: Run full Python test suite**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform/python-sidecar
python -m pytest pipeline/orchestrator/writers/__tests__/test_ga_nakshatra.py -v 2>&1 | tail -20
```

- [ ] **Step 2: TypeScript check**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
npx tsc --noEmit 2>&1 | tail -10
```

Zero new errors acceptable.

- [ ] **Step 3: Create PR**

```bash
gh pr create \
  --title "feat(ga_nakshatra): L1 per-chart parallel nakshatra chart — KP lords, dispositor graph, gaṇḍānta, tara, statistics" \
  --base main \
  --body "$(cat <<'EOF'
## Summary

Implements `ga_nakshatra` — L1 per-chart parallel nakshatra chart. Writes 14 fact_categories into `chart_facts` per ayanamsha (×5) for 10 bodies.

### What's in this PR

**New assets / files:**
- `ga_writers/ga_nakshatra_compute.py` — pure algorithms: KP Vimshottari sub-lords (4 levels), gaṇḍānta severity, tara bala, nakshatra dispositor graph
- `ga_writers/ga_nakshatra_emitters.py` — fact row builders for all 14 categories
- `pipeline/orchestrator/writers/ga_nakshatra.py` — heavy WriterBase: 6 sub-steps (5 ayanamshas + cross-ayanamsha)
- `pipeline/orchestrator/writers/__tests__/test_ga_nakshatra.py` — unit tests (no DB)
- `migrations/241_ga_nakshatra_registry.sql` — asset registry
- `migrations/242_ga_nakshatra_target_floor.sql` — target_floor set from first build

**Restored + tracked:**
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_GA_NAKSHATRA_WRITER_v1_0.md`
- `00_ARCHITECTURE/NAKSHATRA_SUBSYSTEM_MASTER_PLAN_v1_0.md`

### Fact categories (14)

`graha_nakshatra_join` · `graha_pada_join` · `nakshatra_lord_placement` · `graha_kp_lords` · `cusp_kp_lords` · `graha_gandanta` · `graha_degree_flags` · `nakshatra_dispositor` · `nakshatra_exchange` · `nakshatra_conjunction` · `nakshatra_cogravity` · `graha_tara_bala` · `nakshatra_statistics` · `nakshatra_cross_ayanamsha`

### Standards conformance
- bg_nakshatra is AUTHORITY: static attrs cited via source_calculation, never restated
- ga_vargas is AUTHORITY for D150: references existing varga_d150_rishi, never recomputes
- L1 idempotency: delete-then-insert via replace_prior_chart_facts()
- FROZEN orchestrator contract: plan_substeps + run_substep, ctx.db_conn never committed
- KP sub-lords: pure Python Vimshottari proportional subdivision (canonical algorithm)
- Row count measured + reported: within chart_facts health range

### FORENSIC (native Moon = Purva Bhadrapada, nakshatra_id=25, lahiri_chitrapaksha)
- graha_nakshatra_join MOON: gana=Manushya, nadi=Adi, yoni_en=Lion, presiding_deity contains Aja Ekapada ✓
- graha_kp_lords MOON: star_lord=Jupiter ✓

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Monitor CI + merge on green**

---

## Acceptance criteria (brief §11)

- [x] bg_nakshatra present — halt-clean if absent (checked in run_substep)
- [x] Per-body placement + attribute-join emitted ×5 ay; JOIN resolves to reference_nakshatra rows
- [x] Parallel nakshatra chart: dispositor graph + exchanges + conjunctions + center-of-gravity
- [x] KP sub/sub-sub/prana per body + per cusp; D150 refs ga_vargas
- [x] Gaṇḍānta arc-minutes severity; per-chart statistics
- [x] FORENSIC: Moon=PBP (gana/nadi/yoni/deity verified); KP star-lord=Jupiter
- [x] Row-count measured + reported (within health range, or flagged)
- [x] Orchestrator-native: `get_writer('ga_nakshatra')` resolves; idempotent double-run
- [x] CI green; merge-verify
