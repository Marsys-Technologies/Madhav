"""Step 3 §4 (Pravāha C20, steward M20261002T073859-1fec + ruling M20261002T074246-1b3a)
— the overlay freshness fingerprint folds in the consumed L1 identity, the node series
and the writer's formula_version.

The defect (spec §4, CLAUDE.md §N.8): until now `current_fingerprint` answered "built
from what the reference tables say now?" from L0 tables only, so rows built from an OLD
L1 build — or from the wrong node series, or by a lagging writer version — read `fresh`
(the v1.0-vs-v1.1 production lag proved it). Both upstream fingerprints gain three
components:
  (a) formula_version of the writer;
  (b) l1 — the one natal fact both writers read (graha_position / MOON /
      longitude_sidereal) as {fact_id, build_id, stored value text}, via the ONE shared
      helper (gochara_kernel.l1_identity.l1_operand_identity) the writer, this gate and
      the '4.1' manifest all call;
  (c) node_series — {mode, n_rows, digest} by Suvarṇa's L0-owned node_series_digest_v1
      SQL (one module constant, sha256-pinned below; the helper RAISES on a NULL digest).

What this file proves (each on production code, §N.8):
  * the digest constant's text is pinned (sha256 literal — an accidental edit fails);
  * the gate reads ALL vedha kinds and a row without a fingerprint counts as stale;
  * rows stamped with the OLD (today's production) fingerprint shape read STALE, and
    `components` names node_series / l1 / formula_version as the differing parts;
  * rows from another L1 build_id read stale (component l1); a changed node row moves
    the digest (component node_series); identical inputs read fresh;
  * a missing L1 operand reads stale with reason l1_operand_absent (never fresh);
  * an empty node series RAISES (no silent default, no TRUE fallback);
  * the '4.1' candidate's gate call (check_overlay_freshness + gate_allows_overlays)
    still works unchanged.

Pure tests run anywhere; the PG test uses the disposable WP6 Postgres only and skips
NOT_RUN when unreachable. Scope per the task: SERIES_NODE_MODE stays 'true', no formula
version bump, no row-stamp or R-KETU change (later step-3 parts) — so the writers stamp
only house_vedha rows with a fingerprint today, and the PG fixture narrows the vedha
table to that kind before the gate runs (the §3 stamps arrive with the row-stamp part).
"""
from __future__ import annotations

import hashlib
import json
from types import SimpleNamespace

import psycopg
import pytest

from services.gochara_kernel.l1_identity import L1OperandAbsentError, l1_operand_identity
from services.ka_moorti_nirnaya.logic import moorti_upstream_fingerprint
from services.ka_vedha_gochara.freshness import (
    FRESH,
    L1_OPERAND_ABSENT,
    STALE,
    FreshnessReport,
    _component_counts,
    check_house_vedha_freshness,
    check_moorti_freshness,
    check_overlay_freshness,
    current_fingerprint,
    current_moorti_fingerprint,
    gate_allows_overlays,
)
from services.ka_vedha_gochara.logic import upstream_fingerprint
from services.w2g.node_series import (
    NODE_SERIES_DIGEST_V1_SQL,
    NodeSeriesError,
    node_series_identity,
)

from .test_wp9_stamp_columns import (
    BASE_DDL,
    CHART_ID,
    MIGRATION_1082,
    WP6_DSN,
    _seed,
    _wp6_reachable,
)

RULE = {"vedha_house": 5, "phala": "gain", "classical_citation": "Phaladipika Adh. XXVI, Sloka 3"}
SCALE = {1: {"effect_grade": "agitation", "source_citation": "PG353"}}
MOORTI = {0: {"moorti_name": "Suvarna", "quality_tier": "good", "phala_brief": "gain",
              "classical_citation": "Phaladipika Ch.26"}}
NS = {"mode": "true", "n_rows": 2, "digest": "d" * 64}
L1 = {"operands": [{"category": "graha_position", "subject": "MOON",
                    "key": "longitude_sidereal", "fact_id": "f-1",
                    "build_id": "b-1", "value": "5"}], "digest": "e" * 64}

# sha256 of the NODE_SERIES_DIGEST_V1_SQL text, recorded from the steward's C20 ruling
# (M20261002T074246-1b3a — Suvarṇa decision 2026-10-02, node_series_digest_v1). An
# accidental edit of the L0-owned definition fails here; an intentional change is a v2.
NODE_SERIES_DIGEST_V1_SQL_SHA256 = "3194ceb30b42d3d5ec1bb0c48c105e66449cbf8a717e0d5ef724cf51aceab8b4"


# ── pure: the constant pin and the component shape ───────────────────────────
def test_node_series_digest_v1_sql_text_is_pinned():
    assert hashlib.sha256(NODE_SERIES_DIGEST_V1_SQL.encode("utf-8")).hexdigest() == (
        NODE_SERIES_DIGEST_V1_SQL_SHA256)
    # the steward's substitutions, and nothing else: one %s, no psql bind, the label kept
    assert NODE_SERIES_DIGEST_V1_SQL.count("%s") == 1
    assert ":'node_mode'" not in NODE_SERIES_DIGEST_V1_SQL
    assert "node_series_digest_v1" in NODE_SERIES_DIGEST_V1_SQL


def test_omitted_components_keep_the_pre_step3_shape():
    fp = upstream_fingerprint({("sun", 3): RULE}, SCALE)
    assert set(fp) == {"algorithm", "bg_transit_rules", "n_transit_rules",
                       "bg_vedha_malefic_scale", "n_malefic_scale_rows"}
    mfp = moorti_upstream_fingerprint(MOORTI)
    assert set(mfp) == {"algorithm", "bg_transit_moorti", "n_moorti_rows"}


def test_each_new_component_is_folded_in_when_passed():
    fp = upstream_fingerprint({("sun", 3): RULE}, SCALE,
                              node_series=NS, l1=L1, formula_version="v1")
    assert fp["node_series"] == NS and fp["l1"] == L1 and fp["formula_version"] == "v1"
    mfp = moorti_upstream_fingerprint(MOORTI, node_series=NS, l1=L1, formula_version="v1")
    assert mfp["node_series"] == NS and mfp["l1"] == L1 and mfp["formula_version"] == "v1"
    # and each component moves the comparison on its own
    assert fp != upstream_fingerprint({("sun", 3): RULE}, SCALE,
                                      node_series=dict(NS, digest="0" * 64), l1=L1,
                                      formula_version="v1")
    assert fp != upstream_fingerprint({("sun", 3): RULE}, SCALE,
                                      node_series=NS, l1=L1, formula_version="v2")


def test_component_counts_name_the_differing_part():
    current = upstream_fingerprint({("sun", 3): RULE}, SCALE,
                                   node_series=NS, l1=L1, formula_version="v1")
    old_shape = upstream_fingerprint({("sun", 3): RULE}, SCALE)  # today's production shape
    counts = _component_counts([old_shape], current)
    assert counts["node_series"] == counts["l1"] == counts["formula_version"] == 1
    assert counts["rules"] == counts["scale"] == counts["unstamped"] == 0
    assert _component_counts([None], current)["unstamped"] == 1
    assert _component_counts([current], current) == {
        "rules": 0, "scale": 0, "node_series": 0, "l1": 0, "formula_version": 0,
        "unstamped": 0}


def test_l1_identity_digest_is_sensitive_to_build_id_and_value():
    class _Cur:
        def __init__(self, row):
            self._row = row

        def execute(self, *_a):
            pass

        def fetchall(self):
            return [self._row]

        def __enter__(self):
            return self

        def __exit__(self, *_a):
            pass

    class _Conn:
        def __init__(self, row):
            self._row = row

        def cursor(self, **_kw):
            return _Cur(self._row)

    base_row = {"fact_id": "f-1", "build_id": "b-1", "value": "5.0"}
    operands = (("graha_position", "MOON", "longitude_sidereal"),)
    a = l1_operand_identity(_Conn(base_row), "chart", "lahiri_chitrapaksha", operands)
    assert a["operands"][0] == {"category": "graha_position", "subject": "MOON",
                                "key": "longitude_sidereal", "fact_id": "f-1",
                                "build_id": "b-1", "value": "5.0"}
    b = l1_operand_identity(_Conn(dict(base_row, build_id="b-2")), "chart",
                            "lahiri_chitrapaksha", operands)
    c = l1_operand_identity(_Conn(dict(base_row, value="5.000000000001")), "chart",
                            "lahiri_chitrapaksha", operands)
    assert a["digest"] != b["digest"] and a["digest"] != c["digest"]


# ── PG: build → fresh; each new component moves the verdict ─────────────────
@pytest.fixture()
def db():
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    c = psycopg.connect(WP6_DSN, autocommit=True)
    c.execute(BASE_DDL)
    c.execute(MIGRATION_1082.read_text())
    c.close()
    seed = psycopg.connect(WP6_DSN)
    _seed(seed)
    seed.commit()
    seed.close()
    yield
    # leave the schema in place; every test that needs it rebuilds it


def _exec(sql, params=()):
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        c.execute(sql, params)


def _build_writers():
    import services.ka_moorti_nirnaya.writer as mw
    import services.ka_vedha_gochara.writer as vw

    for mod, cls in ((vw, vw.KaVedhaGocharaWriter), (mw, mw.KaMoortiNirnayaWriter)):
        conn = psycopg.connect(WP6_DSN)
        ctx = SimpleNamespace(db_conn=conn, config={"chart_id": CHART_ID}, dry_run=False)
        orig = mod._compute_ayanamsha_offset
        mod._compute_ayanamsha_offset = lambda _d: 0.0
        # The moorti writer's Swiss instant grading cannot refine this fixture's
        # synthetic longitudes against the real ephemeris (the pre-existing local
        # wp12 moorti failure — this suite's subject is the fingerprint gate, not
        # the grading regime), so it builds on the writer's own day-grade path.
        orig_grading = getattr(mod, "KERNEL_INSTANT_GRADING", None)
        if orig_grading is not None:
            mod.KERNEL_INSTANT_GRADING = False
        try:
            cls().run(ctx)
            conn.commit()
        finally:
            mod._compute_ayanamsha_offset = orig
            if orig_grading is not None:
                mod.KERNEL_INSTANT_GRADING = orig_grading
            conn.close()
    # The §3 row stamps (a fingerprint on sarvatobhadra/latta rows) are a LATER step-3
    # part; until then the writer stamps only house_vedha rows, and the gate reads ALL
    # kinds — narrow the fixture to the stamped kind so its subject (the fingerprint
    # gate) is what is exercised, never an unstamped row the writer cannot yet produce.
    _exec("DELETE FROM kala_vedha_gochara WHERE vedha_kind <> 'house_vedha'")


def _fresh_reports():
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        return check_overlay_freshness(c, CHART_ID)


def test_build_then_identical_inputs_read_fresh_and_the_41_gate_call_works(db):
    """The '4.1' candidate's exact gate path: check_overlay_freshness +
    gate_allows_overlays — fresh, all components zero, manifest vectors carried."""
    _build_writers()
    reports = _fresh_reports()
    assert gate_allows_overlays(reports) is True
    for r in reports.values():
        assert r.state == FRESH and r.missing == 0 and r.mismatched == 0
        assert r.current is not None
        assert not any(r.components.values()), r.components
        # the richer manifest vectors: node-series + L1 identity + writer version
        assert r.current["node_series"]["mode"] == "true"
        assert r.current["node_series"]["n_rows"] > 0 and r.current["node_series"]["digest"]
        assert r.current["l1"]["operands"][0]["build_id"] == "wp9-l1-build-1"
        assert r.current["formula_version"]


def test_old_shape_fingerprint_rows_read_stale(db):
    """The deploy-day regression (spec §4): today's production shape — the
    reference-table-only fingerprint — must read STALE, and `components` must
    name node_series, l1 and formula_version as the differing parts."""
    _build_writers()
    # strip exactly the step-3 keys from every stored fingerprint (old shape)
    _exec(
        "UPDATE kala_vedha_gochara SET detail = jsonb_set(detail, '{upstream_fingerprint}', "
        "(detail->'upstream_fingerprint') - 'node_series' - 'l1' - 'formula_version')")
    _exec(
        "UPDATE kala_moorti_nirnaya SET upstream_fingerprint = "
        "upstream_fingerprint - 'node_series' - 'l1' - 'formula_version'")
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        vedha = check_house_vedha_freshness(c, CHART_ID)
        moorti = check_moorti_freshness(c, CHART_ID)
    for r in (vedha, moorti):
        assert r.state == STALE and r.mismatched == r.total > 0 and r.missing == 0
        assert r.components["node_series"] == r.total
        assert r.components["l1"] == r.total
        assert r.components["formula_version"] == r.total
        assert r.components["rules"] == 0


def test_rows_from_another_l1_build_id_read_stale(db):
    """An L1 rebuild (new build_id, same value) moves the l1 component of every row."""
    _build_writers()
    assert _fresh_reports()["moorti"].state == FRESH
    _exec("UPDATE chart_facts SET build_id = 'wp9-l1-build-2' WHERE fact_id = "
          "(SELECT janma_reference_fact_id FROM kala_vedha_gochara LIMIT 1)")
    reports = _fresh_reports()
    for r in reports.values():
        assert r.state == STALE and r.components["l1"] == r.total > 0
        assert r.components["node_series"] == 0 and r.components["rules"] == 0


def test_a_changed_node_row_moves_the_digest(db):
    _build_writers()
    assert _fresh_reports()["house_vedha"].state == FRESH
    _exec("UPDATE ephemeris_daily SET tropical_longitude = tropical_longitude + 0.5 "
          "WHERE body = 'Rahu' AND node_mode = 'true' AND date = (SELECT min(date) "
          "FROM ephemeris_daily WHERE body = 'Rahu' AND node_mode = 'true')")
    reports = _fresh_reports()
    for r in reports.values():
        assert r.state == STALE and r.components["node_series"] == r.total > 0
        assert r.components["l1"] == 0


def test_missing_l1_operand_reads_stale_with_reason_never_fresh(db):
    _build_writers()
    _exec("DELETE FROM chart_facts")
    reports = _fresh_reports()
    for r in reports.values():
        assert r.state == STALE and r.reason == L1_OPERAND_ABSENT


def test_empty_node_series_raises_no_silent_default(db):
    _exec("DELETE FROM ephemeris_daily WHERE body IN ('Rahu', 'Ketu')")
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        with pytest.raises(NodeSeriesError):
            node_series_identity(c)
        with pytest.raises(NodeSeriesError):
            current_fingerprint(c, CHART_ID)
        with pytest.raises(NodeSeriesError):
            current_moorti_fingerprint(c, CHART_ID)


def test_unstamped_rows_of_any_kind_count_as_stale(db):
    """The gate reads ALL vedha kinds: a latta row with no fingerprint is
    `missing`, not invisible (until the §3 stamps land)."""
    _build_writers()
    _exec(
        "INSERT INTO kala_vedha_gochara (chart_id, ayanamsha_id, vedha_kind, graha,"
        " window_start, window_end, start_truncated, end_truncated,"
        " janma_reference_fact_id, classical_citation, uncited_extension,"
        " source_qualification, precision_regime, corpus_verifiable, detail,"
        " formula_version)"
        " SELECT chart_id, ayanamsha_id, 'latta', graha, window_start,"
        " window_end, start_truncated, end_truncated, janma_reference_fact_id,"
        " classical_citation, uncited_extension, source_qualification,"
        " precision_regime, corpus_verifiable, '{}'::jsonb, formula_version"
        " FROM kala_vedha_gochara WHERE vedha_kind = 'house_vedha' LIMIT 1")
    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        r = check_house_vedha_freshness(c, CHART_ID)
    assert r.state == STALE and r.missing == 1 and r.components["unstamped"] == 1
