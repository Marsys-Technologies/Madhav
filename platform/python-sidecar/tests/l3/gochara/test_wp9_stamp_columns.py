"""WP9 task 5.1 — overlay stamp columns on kala_vedha_gochara + kala_moorti_nirnaya.

Covers GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §5.4's three-stamp contract:
every Vedha/Moorti row carries (source_qualification, precision_regime,
corpus_verifiable), enforced by migration 1082's CHECKs, populated by the
ka_vedha_gochara / ka_moorti_nirnaya writers, and consistent with the
migration-670 (a)-(j) integrity conjuncts for asset_id='ka_vedha_gochara'.

Runs ONLY against the disposable WP6 Postgres (docker gochara-wp6-disposable);
skips NOT_RUN when unreachable. The fixture builds the two base tables with
their real DDL (migrations 525/526), applies migration 1082, seeds minimal
reference tables (bg_transit_rules, bg_phaladeepika_latta,
bg_vedha_malefic_scale, bg_transit_moorti, chart_facts) plus a synthetic
ephemeris_daily, then runs BOTH writers end-to-end.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import psycopg  # noqa: E402

WP6_DSN = os.environ.get(
    "WP6_LEDGER_DSN", "postgresql://wp6:disposable@localhost:55433/wp6"
)

MIGRATION_1082 = (
    Path(__file__).resolve().parents[4]
    / "migrations/1082_nirmana_l3_vedha_moorti_stamp_columns.sql"
)

CHART_ID = "11111111-2222-3333-4444-555555555555"
JANMA_FACT_ID = "wp9-janma-moon-fact"
# Janma Moon: longitude_sidereal 5.0 -> sign_idx 0 (Aries), nak_idx 0 (Ashwini).
JANMA_MOON_LON = 5.0

HORIZON_BACK_DAYS = 60
HORIZON_FORWARD_DAYS = 400

BPHS_CH29 = "BPHS Ch.29 (Gochara Phala — Transit Results)"
PD_CH26 = "Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)"
LATTA_CIT = "Phaladeepika Ch.26 (Latta) PG338-339"
SCALE_CIT = "Phaladeepika Ch.26 PG353"
MOORTI_CIT = "Phaladeepika Ch.26; BPHS Ch.28"

BASE_DDL = """
DROP TABLE IF EXISTS kala_vedha_gochara;
DROP TABLE IF EXISTS kala_moorti_nirnaya;
DROP TABLE IF EXISTS bg_transit_rules;
DROP TABLE IF EXISTS bg_phaladeepika_latta;
DROP TABLE IF EXISTS bg_vedha_malefic_scale;
DROP TABLE IF EXISTS bg_transit_moorti;
DROP TABLE IF EXISTS bg_sarvatobhadra_grid;
DROP TABLE IF EXISTS l1_sarvatobhadra_vedha;
DROP TABLE IF EXISTS chart_facts;
DROP TABLE IF EXISTS ephemeris_daily;

-- Real DDL, lifted verbatim from platform/supabase/migrations/526_kala_vedha_gochara.sql
CREATE TABLE kala_vedha_gochara (
  id                        BIGSERIAL PRIMARY KEY,
  chart_id                  UUID NOT NULL,
  ayanamsha_id              TEXT NOT NULL DEFAULT 'lahiri_chitrapaksha',
  vedha_kind                TEXT NOT NULL CHECK (vedha_kind IN ('house_vedha', 'sarvatobhadra', 'latta')),
  graha                     TEXT NOT NULL,
  window_start              DATE NOT NULL,
  window_end                DATE NOT NULL,
  start_truncated           BOOLEAN NOT NULL,
  end_truncated             BOOLEAN NOT NULL,
  janma_reference_fact_id   TEXT NOT NULL,
  classical_citation        TEXT NOT NULL,
  uncited_extension         BOOLEAN NOT NULL,
  grid_basis                TEXT CHECK (grid_basis IN ('db_sourced_grid', 'algorithmic_approximation')),
  grid_school_tag           TEXT,
  detail                    JSONB NOT NULL DEFAULT '{}'::jsonb,
  formula_version           TEXT NOT NULL,
  computed_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_vedha_gochara_natural_key
    UNIQUE (chart_id, ayanamsha_id, vedha_kind, graha, window_start),
  CONSTRAINT kala_vedha_gochara_window_order CHECK (window_end >= window_start),
  CONSTRAINT kala_vedha_gochara_grid_fields_scope CHECK (
    (vedha_kind = 'sarvatobhadra' AND grid_basis IS NOT NULL)
    OR (vedha_kind <> 'sarvatobhadra' AND grid_basis IS NULL AND grid_school_tag IS NULL)
  )
);

-- Real DDL, lifted verbatim from platform/supabase/migrations/525_kala_moorti_nirnaya.sql
CREATE TABLE kala_moorti_nirnaya (
  id                              BIGSERIAL PRIMARY KEY,
  chart_id                        UUID NOT NULL,
  ayanamsha_id                    TEXT NOT NULL DEFAULT 'lahiri_chitrapaksha',
  graha                           TEXT NOT NULL,
  target_sign_idx                 SMALLINT NOT NULL CHECK (target_sign_idx BETWEEN 0 AND 11),
  target_sign_name                TEXT NOT NULL,
  window_start                    DATE NOT NULL,
  window_end                      DATE NOT NULL,
  start_truncated                 BOOLEAN NOT NULL,
  end_truncated                   BOOLEAN NOT NULL,
  moorti_computed                 BOOLEAN NOT NULL,
  moon_nakshatra_idx_at_ingress   SMALLINT CHECK (moon_nakshatra_idx_at_ingress BETWEEN 0 AND 26),
  moon_nakshatra_name_at_ingress  TEXT,
  janma_nakshatra_idx             SMALLINT NOT NULL CHECK (janma_nakshatra_idx BETWEEN 0 AND 26),
  janma_nakshatra_fact_id         TEXT NOT NULL,
  nakshatra_offset                SMALLINT CHECK (nakshatra_offset BETWEEN 1 AND 27),
  moorti_name                     TEXT CHECK (moorti_name IN ('swarna', 'rajata', 'tamra', 'loha')),
  quality_tier                    SMALLINT CHECK (quality_tier BETWEEN 1 AND 4),
  phala_brief                     TEXT,
  moorti_classical_citation       TEXT,
  formula_version                 TEXT NOT NULL,
  computed_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT kala_moorti_nirnaya_natural_key
    UNIQUE (chart_id, ayanamsha_id, graha, window_start),
  CONSTRAINT kala_moorti_nirnaya_window_order CHECK (window_end >= window_start),
  CONSTRAINT kala_moorti_nirnaya_computed_consistency CHECK (
    (moorti_computed = FALSE
      AND moon_nakshatra_idx_at_ingress IS NULL AND moon_nakshatra_name_at_ingress IS NULL
      AND nakshatra_offset IS NULL AND moorti_name IS NULL AND quality_tier IS NULL
      AND phala_brief IS NULL AND moorti_classical_citation IS NULL)
    OR
    (moorti_computed = TRUE
      AND moon_nakshatra_idx_at_ingress IS NOT NULL AND moon_nakshatra_name_at_ingress IS NOT NULL
      AND nakshatra_offset IS NOT NULL AND moorti_name IS NOT NULL AND quality_tier IS NOT NULL
      AND phala_brief IS NOT NULL AND moorti_classical_citation IS NOT NULL)
  )
);

CREATE TABLE bg_transit_rules (
  id BIGSERIAL PRIMARY KEY,
  rule_type TEXT NOT NULL,
  graha TEXT NOT NULL,
  primary_house INTEGER NOT NULL,
  vedha_house INTEGER,
  phala TEXT NOT NULL,
  classical_citation TEXT NOT NULL
);

CREATE TABLE bg_phaladeepika_latta (
  graha TEXT PRIMARY KEY,
  count_from_graha INTEGER NOT NULL,
  direction TEXT NOT NULL,
  effect_description TEXT NOT NULL,
  affliction_condition TEXT NOT NULL,
  source_citation TEXT NOT NULL
);

CREATE TABLE bg_vedha_malefic_scale (
  malefic_count INTEGER PRIMARY KEY,
  effect_grade TEXT NOT NULL,
  effect_description TEXT NOT NULL,
  source_citation TEXT NOT NULL
);

CREATE TABLE bg_transit_moorti (
  nakshatra_offset INTEGER PRIMARY KEY,
  moorti_name TEXT NOT NULL,
  quality_tier INTEGER NOT NULL,
  phala_brief TEXT NOT NULL,
  classical_citation TEXT NOT NULL
);

CREATE TABLE bg_sarvatobhadra_grid (
  id BIGSERIAL PRIMARY KEY,
  cell_kind TEXT NOT NULL,
  cell_index INTEGER NOT NULL,
  cell_value INTEGER,
  school_tag TEXT,
  table_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE l1_sarvatobhadra_vedha (
  nakshatra_1_id INTEGER NOT NULL,
  nakshatra_2_id INTEGER NOT NULL
);

CREATE TABLE chart_facts (
  fact_id TEXT PRIMARY KEY,
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  fact_category TEXT NOT NULL,
  fact_subject TEXT NOT NULL,
  fact_key TEXT NOT NULL,
  fact_value_num DOUBLE PRECISION
);

CREATE TABLE ephemeris_daily (
  date DATE NOT NULL,
  body TEXT NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  tropical_longitude DOUBLE PRECISION NOT NULL,
  speed_dps DOUBLE PRECISION,
  is_retrograde BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (date, body, ayanamsha_id)
);
"""

# The migration-670 integrity contract for asset_id='ka_vedha_gochara',
# conjuncts (a)-(j), lifted verbatim (single SELECT of ANDed NOT EXISTS).
INTEGRITY_SQL = """
SELECT
  NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.vedha_kind = 'sarvatobhadra'
      AND v.uncited_extension IS DISTINCT FROM (v.grid_basis = 'algorithmic_approximation')
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.vedha_kind <> 'sarvatobhadra' AND v.uncited_extension
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    LEFT JOIN bg_transit_rules r
      ON r.rule_type = 'favourable' AND r.vedha_house IS NOT NULL
     AND r.graha = lower(v.graha)
     AND r.primary_house = (v.detail->>'primary_house')::int
    WHERE v.vedha_kind = 'house_vedha'
      AND (r.graha IS NULL
        OR (v.detail->>'vedha_house')::int IS DISTINCT FROM r.vedha_house
        OR (v.detail->>'phala') IS DISTINCT FROM r.phala)
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    LEFT JOIN chart_facts f
      ON f.fact_id = v.janma_reference_fact_id
     AND f.chart_id = v.chart_id
     AND f.ayanamsha_id = v.ayanamsha_id
    WHERE f.fact_id IS NULL
       OR f.fact_value_num IS NULL
       OR (v.vedha_kind = 'house_vedha'
           AND ((v.detail->>'primary_house')::int IS DISTINCT FROM
                 (((((v.detail->>'primary_sign_idx')::int - (floor(f.fact_value_num / 30.0)::int % 12))
                     % 12) + 12) % 12) + 1
             OR (v.detail->>'vedha_sign_idx')::int IS DISTINCT FROM
                 (((floor(f.fact_value_num / 30.0)::int % 12) + (v.detail->>'vedha_house')::int - 1) % 12)))
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    JOIN chart_facts f
      ON f.fact_id = v.janma_reference_fact_id
     AND f.chart_id = v.chart_id
     AND f.ayanamsha_id = v.ayanamsha_id
    WHERE (v.vedha_kind = 'sarvatobhadra'
           AND (v.detail->>'target_nakshatra_idx')::int
               IS DISTINCT FROM (floor(f.fact_value_num / (360.0 / 27.0))::int % 27))
       OR (v.vedha_kind = 'latta'
           AND (v.detail->>'janma_nakshatra_idx')::int
               IS DISTINCT FROM (floor(f.fact_value_num / (360.0 / 27.0))::int % 27))
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.vedha_kind = 'latta'
      AND (v.detail->>'latta_nakshatra_idx') IS DISTINCT FROM (v.detail->>'janma_nakshatra_idx')
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    LEFT JOIN bg_phaladeepika_latta l ON l.graha = v.graha
    WHERE v.vedha_kind = 'latta'
      AND (l.graha IS NULL
        OR (v.detail->>'count_from_graha')::int IS DISTINCT FROM l.count_from_graha
        OR (v.detail->>'direction') IS DISTINCT FROM l.direction
        OR v.classical_citation IS DISTINCT FROM l.source_citation)
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.vedha_kind = 'house_vedha'
      AND (v.detail->>'malefic_count')::int
          IS DISTINCT FROM jsonb_array_length(v.detail->'malefic_obstructing_grahas')
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    LEFT JOIN bg_vedha_malefic_scale s ON s.malefic_count = (v.detail->>'malefic_count')::int
    WHERE v.vedha_kind = 'house_vedha'
      AND (((v.detail->>'malefic_effect_grade') IS NOT NULL) <> (s.malefic_count IS NOT NULL)
        OR ((v.detail->>'malefic_effect_grade') IS NOT NULL
            AND ((v.detail->>'malefic_effect_grade') IS DISTINCT FROM s.effect_grade
              OR (v.detail->>'malefic_scale_citation') IS DISTINCT FROM s.source_citation)))
  )
  AND NOT EXISTS (
    SELECT 1 FROM kala_vedha_gochara v
    WHERE v.detail->>'obstruction_window_start' IS NOT NULL
      AND ((v.detail->>'obstruction_window_start')::date < v.window_start
        OR (v.detail->>'obstruction_window_end')::date > v.window_end
        OR (v.detail->>'obstruction_window_end')::date < (v.detail->>'obstruction_window_start')::date)
  )
  AS integrity_passed
"""


def _wp6_reachable() -> bool:
    try:
        with psycopg.connect(WP6_DSN, connect_timeout=3):
            return True
    except Exception:
        return False


def _body_lon(body: str, day_offset: int) -> float:
    """Synthetic tropical longitudes per body per horizon day (ayanamsha offset
    is monkeypatched to 0.0, so tropical == sidereal in this fixture).

    Layout (janma Moon = sign 0 / nak 0):
      Sun     sign 2 (house 3, vedha-checkable, BPHS Ch.29) for days 100..130,
              else sign 5. The sign-2 run is the one non-truncated moorti run.
      Moon    cycles 13.0 deg/day through the nakshatras.
      Mars    nak 14 (= the algorithmic SBC vedha nak of janma nak 0) always.
      Mercury sign 1 always.   Jupiter sign 3 always.
      Venus   nak 23 always (its latta rule: 5 forward -> latta nak 0 = janma).
      Saturn  sign 8 (the vedha sign of sun/3) for days 110..120, else sign 3.
      Rahu    sign 10 always (house 11, vedha-checkable, Phaladeepika-cited).
      Ketu    sign 4 always (the vedha sign of rahu/11 -> obstruction by Ketu).
    """
    if body == "Sun":
        return 65.0 if 100 <= day_offset <= 130 else 155.0
    if body == "Moon":
        return (day_offset * 13.0) % 360.0
    if body == "Mars":
        return 190.0
    if body == "Mercury":
        return 40.0
    if body == "Jupiter":
        return 100.0
    if body == "Venus":
        return 310.0
    if body == "Saturn":
        return 245.0 if 110 <= day_offset <= 120 else 100.0
    if body == "Rahu":
        return 305.0
    if body == "Ketu":
        return 125.0
    raise ValueError(body)


BODIES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


def _seed(conn: psycopg.Connection) -> None:
    today = date.today()
    horizon_start = today - timedelta(days=HORIZON_BACK_DAYS)

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, "
            "fact_subject, fact_key, fact_value_num) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (JANMA_FACT_ID, CHART_ID, "lahiri_chitrapaksha", "graha_position",
             "MOON", "longitude_sidereal", JANMA_MOON_LON),
        )
        cur.executemany(
            "INSERT INTO bg_transit_rules (rule_type, graha, primary_house, vedha_house, "
            "phala, classical_citation) VALUES (%s,%s,%s,%s,%s,%s)",
            [
                ("favourable", "sun", 3, 9, "Courage, travel, gain from siblings", BPHS_CH29),
                ("favourable", "rahu", 11, 5, "Financial gains, labha", PD_CH26),
            ],
        )
        cur.execute(
            "INSERT INTO bg_phaladeepika_latta (graha, count_from_graha, direction, "
            "effect_description, affliction_condition, source_citation) "
            "VALUES (%s,%s,%s,%s,%s,%s)",
            ("Venus", 5, "forward", "Affliction by Venus latta",
             "Latta point on janma nakshatra", LATTA_CIT),
        )
        cur.executemany(
            "INSERT INTO bg_vedha_malefic_scale (malefic_count, effect_grade, "
            "effect_description, source_citation) VALUES (%s,%s,%s,%s)",
            [(n, f"grade-{n}", f"{n} malefic(s) obstructing", SCALE_CIT) for n in range(1, 6)],
        )
        moorti_names = {1: "swarna", 2: "rajata", 3: "tamra", 4: "loha"}
        cur.executemany(
            "INSERT INTO bg_transit_moorti (nakshatra_offset, moorti_name, quality_tier, "
            "phala_brief, classical_citation) VALUES (%s,%s,%s,%s,%s)",
            [
                (off, moorti_names[((off - 1) % 4) + 1], ((off - 1) % 4) + 1,
                 f"moorti phala for offset {off}", MOORTI_CIT)
                for off in range(1, 28)
            ],
        )
        days = (HORIZON_BACK_DAYS + HORIZON_FORWARD_DAYS) + 1
        cur.executemany(
            "INSERT INTO ephemeris_daily (date, body, ayanamsha_id, tropical_longitude, "
            "speed_dps, is_retrograde) VALUES (%s,%s,%s,%s,%s,%s)",
            [
                (horizon_start + timedelta(days=off), body, "tropical",
                 _body_lon(body, off), 1.0, False)
                for off in range(days)
                for body in BODIES
            ],
        )


@pytest.fixture(scope="session")
def wp9_schema():
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(BASE_DDL)
    conn.execute(MIGRATION_1082.read_text())
    conn.close()

    seed_conn = psycopg.connect(WP6_DSN)
    _seed(seed_conn)
    seed_conn.commit()
    seed_conn.close()
    return True


@pytest.fixture(scope="session")
def wp9_built(wp9_schema):
    """Runs both writers end-to-end against the seeded fixture (once per session)."""
    import services.ka_vedha_gochara.writer as vedha_writer
    import services.ka_moorti_nirnaya.writer as moorti_writer

    conn = psycopg.connect(WP6_DSN)
    ctx = SimpleNamespace(db_conn=conn, config={"chart_id": CHART_ID}, dry_run=False)

    orig_vedha_offset = vedha_writer._compute_ayanamsha_offset
    orig_moorti_offset = moorti_writer._compute_ayanamsha_offset
    vedha_writer._compute_ayanamsha_offset = lambda _d: 0.0
    moorti_writer._compute_ayanamsha_offset = lambda _d: 0.0
    try:
        vedha_result = vedha_writer.KaVedhaGocharaWriter().run(ctx)
        moorti_result = moorti_writer.KaMoortiNirnayaWriter().run(ctx)
        conn.commit()
    finally:
        vedha_writer._compute_ayanamsha_offset = orig_vedha_offset
        moorti_writer._compute_ayanamsha_offset = orig_moorti_offset
        conn.close()
    return {"vedha": vedha_result, "moorti": moorti_result}


@pytest.fixture()
def conn(wp9_schema):
    c = psycopg.connect(WP6_DSN, autocommit=True)
    try:
        yield c
    finally:
        c.close()


# ── 1. Migration 1082 CHECK constraints ──────────────────────────────────────

class TestStampCheckConstraints:
    def _base_row(self, **overrides):
        row = {
            "chart_id": CHART_ID,
            "ayanamsha_id": "lahiri_chitrapaksha",
            "vedha_kind": "house_vedha",
            "graha": "Sun",
            "window_start": date(2026, 1, 1),
            "window_end": date(2026, 2, 1),
            "start_truncated": False,
            "end_truncated": False,
            "janma_reference_fact_id": JANMA_FACT_ID,
            "classical_citation": BPHS_CH29,
            "uncited_extension": False,
            "source_qualification": "verse_cited",
            "precision_regime": "date_grain",
            "corpus_verifiable": False,
            "detail": json.dumps({"primary_house": 3}),
            "formula_version": "test",
        }
        row.update(overrides)
        return row

    def test_bad_source_qualification_rejected(self, conn):
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                """
                INSERT INTO kala_vedha_gochara (
                  chart_id, ayanamsha_id, vedha_kind, graha, window_start, window_end,
                  start_truncated, end_truncated, janma_reference_fact_id,
                  classical_citation, uncited_extension,
                  source_qualification, precision_regime, corpus_verifiable,
                  detail, formula_version
                ) VALUES (
                  %(chart_id)s, %(ayanamsha_id)s, %(vedha_kind)s, %(graha)s,
                  %(window_start)s, %(window_end)s, %(start_truncated)s, %(end_truncated)s,
                  %(janma_reference_fact_id)s, %(classical_citation)s, %(uncited_extension)s,
                  %(source_qualification)s, %(precision_regime)s, %(corpus_verifiable)s,
                  %(detail)s::jsonb, %(formula_version)s
                )
                """,
                self._base_row(source_qualification="translator_commentary"),
            )

    def test_bad_precision_regime_rejected_on_moorti(self, conn):
        with pytest.raises(psycopg.errors.CheckViolation):
            conn.execute(
                """
                INSERT INTO kala_moorti_nirnaya (
                  chart_id, ayanamsha_id, graha, target_sign_idx, target_sign_name,
                  window_start, window_end, start_truncated, end_truncated,
                  moorti_computed, janma_nakshatra_idx, janma_nakshatra_fact_id,
                  source_qualification, precision_regime, corpus_verifiable, formula_version
                ) VALUES (
                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (CHART_ID, "lahiri_chitrapaksha", "Sun", 2, "Mithuna",
                 date(2026, 1, 1), date(2026, 2, 1), False, False, False, 0, JANMA_FACT_ID,
                 "unsourced", "hour_grain", False, "test"),
            )


# ── 2. Writers populate the stamps end-to-end ────────────────────────────────

def _fetch_all(dsn: str, table: str) -> list[dict]:
    with psycopg.connect(dsn, autocommit=True) as c:
        with c.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(f"SELECT * FROM {table} WHERE chart_id = %s", (CHART_ID,))
            return [dict(r) for r in cur.fetchall()]


class TestWriterStamps:
    def test_writers_inserted_rows(self, wp9_built):
        assert wp9_built["vedha"].rows_inserted > 0
        assert wp9_built["moorti"].rows_inserted > 0

    def test_every_vedha_row_fully_stamped(self, wp9_built):
        rows = _fetch_all(WP6_DSN, "kala_vedha_gochara")
        assert rows, "expected vedha rows"
        for r in rows:
            assert r["source_qualification"] in (
                "verse_cited", "algorithmic_approximation", "unsourced")
            assert r["precision_regime"] == "date_grain"
            assert r["corpus_verifiable"] is not None

    def test_house_vedha_stamp_values(self, wp9_built):
        rows = [r for r in _fetch_all(WP6_DSN, "kala_vedha_gochara")
                if r["vedha_kind"] == "house_vedha"]
        by_graha = {r["graha"]: r for r in rows}
        # sun/3 cites the struck BPHS Ch.29 -> verse-cited but NOT corpus-verifiable
        assert by_graha["Sun"]["source_qualification"] == "verse_cited"
        assert by_graha["Sun"]["corpus_verifiable"] is False
        # rahu/11 cites Phaladeepika Ch.26 -> corpus-verifiable today
        assert by_graha["Rahu"]["source_qualification"] == "verse_cited"
        assert by_graha["Rahu"]["corpus_verifiable"] is True

    def test_sarvatobhadra_stamp_values(self, wp9_built):
        rows = [r for r in _fetch_all(WP6_DSN, "kala_vedha_gochara")
                if r["vedha_kind"] == "sarvatobhadra"]
        assert rows, "expected a sarvatobhadra row (Mars dwelling in the vedha nakshatra)"
        for r in rows:
            assert r["grid_basis"] == "algorithmic_approximation"
            assert r["source_qualification"] == "algorithmic_approximation"
            assert r["corpus_verifiable"] is False

    def test_latta_stamp_values(self, wp9_built):
        rows = [r for r in _fetch_all(WP6_DSN, "kala_vedha_gochara")
                if r["vedha_kind"] == "latta"]
        assert rows, "expected a latta row (Venus latta point on janma nakshatra)"
        for r in rows:
            assert r["source_qualification"] == "verse_cited"
            assert r["corpus_verifiable"] is True

    def test_moorti_stamp_values(self, wp9_built):
        rows = _fetch_all(WP6_DSN, "kala_moorti_nirnaya")
        assert rows, "expected moorti rows"
        computed = [r for r in rows if r["moorti_computed"]]
        uncomputed = [r for r in rows if not r["moorti_computed"]]
        # The Sun sign-2 run (days 100..130) is the one non-truncated run.
        assert computed, "expected at least one moorti-computed row"
        for r in computed:
            assert r["source_qualification"] == "verse_cited"
            assert r["precision_regime"] == "date_grain"
            assert r["corpus_verifiable"] is True
        assert uncomputed, "expected moorti-uncomputed rows (truncated horizon runs)"
        for r in uncomputed:
            assert r["source_qualification"] == "unsourced"
            assert r["precision_regime"] == "date_grain"
            assert r["corpus_verifiable"] is False


# ── 3. Migration-670 (a)-(j) conjuncts over writer output ────────────────────

class TestIntegrityConjuncts:
    def test_conjuncts_pass_on_writer_output(self, wp9_built):
        with psycopg.connect(WP6_DSN, autocommit=True) as c:
            passed = c.execute(INTEGRITY_SQL).fetchone()[0]
        assert passed is True

    def test_conjuncts_detect_corruption(self, wp9_built):
        """Mutation case: flipping one sarvatobhadra row's uncited_extension must
        trip conjunct (a). Rolled back — the session fixture's rows stay clean."""
        c = psycopg.connect(WP6_DSN)
        try:
            updated = c.execute(
                "UPDATE kala_vedha_gochara SET uncited_extension = FALSE "
                "WHERE chart_id = %s AND vedha_kind = 'sarvatobhadra' RETURNING id",
                (CHART_ID,),
            ).fetchall()
            assert updated, "expected at least one sarvatobhadra row to mutate"
            passed = c.execute(INTEGRITY_SQL).fetchone()[0]
            assert passed is False
        finally:
            c.rollback()
            c.close()
