"""TI-ga-structural-cycle-001 -- the daridra dosha_label row is emitted DOWNSTREAM of ga_yoga + ga_vichara.

Cause (POST/FIX_LIST_TRIAGE.md section 4): ga_structural's daridra cancellation read `chart_vichara`
(ga_vichara) and `ga_yoga_firings` (ga_yoga), both of which depend on ga_structural, so the read formed
the cycle ga_structural -> ga_vichara -> ga_structural and the verdict was build-order dependent (a clean
build read None / [] and silently skipped the cancellation).

Fix under test: ga_structural no longer emits the daridra row and no longer reads either table; ga_vichara
(which already depends on ga_structural AND ga_yoga: no new DAG edge) runs `ga_daridra_postpass` after its
own insert, building the row with the SAME `_build_dosha_rows` code, so the natural key (hence the
deterministic fact_id) and every value are unchanged; only the producer (and build_id) moves.

Pure unit tests, no database (the production-shaped replay is in POST/L1_FIXES_SPRINT.md and its script).
"""
from __future__ import annotations

import ast
import hashlib
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import ga_writers.ga_daridra_postpass as pp
import ga_writers.ga_structural_writer as sut
from test_ga8_writer import AY_ID, BUILD_ID, CHART_ID, COMPUTED_AT, ENG_VER
from test_lane3_deliverable_c_dosha_cancellation import _CannedConn, _dosha_entry

SIDECAR = Path(__file__).resolve().parents[1]

# 11th lord (Venus, Cancer lagna) in H8 dusthana: daridra forms; a fired dhana yoga cancels it.
CHART = {
    "ascendant": {"sign": "Cancer", "sign_id": 4, "longitude": 100.0},
    "grahas": [
        {"name": "Venus", "sign": "Sagittarius", "sign_id": 9, "house": 8, "longitude": 250.0, "retrograde": False},
        {"name": "Sun", "sign": "Aries", "sign_id": 1, "house": 10, "longitude": 10.0, "retrograde": False},
        {"name": "Moon", "sign": "Cancer", "sign_id": 4, "house": 1, "longitude": 100.0, "retrograde": False},
        {"name": "Mars", "sign": "Capricorn", "sign_id": 10, "house": 7, "longitude": 280.0, "retrograde": False},
        {"name": "Mercury", "sign": "Pisces", "sign_id": 12, "house": 9, "longitude": 340.0, "retrograde": False},
        {"name": "Jupiter", "sign": "Libra", "sign_id": 7, "house": 4, "longitude": 190.0, "retrograde": False},
        {"name": "Saturn", "sign": "Aquarius", "sign_id": 11, "house": 8, "longitude": 310.0, "retrograde": False},
        {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 11, "longitude": 48.0, "retrograde": True},
        {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 5, "longitude": 228.0, "retrograde": True},
    ],
}
DARIDRA_ENTRY = _dosha_entry("daridra", "11th lord in dusthana or 2nd/11th lords afflicted")
DHANA_CONN = lambda: _CannedConn(  # noqa: E731
    vichara_row=None, yoga_rows=[("dhana_yoga_house_lords", '["sun", "mercury", "venus"]')],
)


def _src(rel: str) -> str:
    return (SIDECAR / rel).read_text(encoding="utf-8")


# ── ga_structural no longer emits / reads ────────────────────────────────────

def test_ga_structural_default_label_pass_does_not_emit_daridra():
    rows = sut._build_dosha_rows(
        DHANA_CONN(), CHART, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER, dosha_catalog=[DARIDRA_ENTRY],
    )
    assert [r for r in rows if r["fact_subject"] == "daridra"] == []


def test_ga_structural_source_reads_no_downstream_table():
    """The cycle itself: no SQL text in ga_structural_writer.py may read chart_vichara or ga_yoga_firings."""
    tree = ast.parse(_src("ga_writers/ga_structural_writer.py"))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if re.search(r"\b(FROM|JOIN)\s+(chart_vichara|ga_yoga_firings)\b", node.value, re.I):
                offenders.append(node.lineno)
    assert offenders == [], f"ga_structural_writer.py reads a table of a downstream asset at lines {offenders}"


def test_downstream_dosha_without_its_cancellation_raises_not_silently_uncancelled():
    with pytest.raises(RuntimeError, match="downstream-cancellation dosha"):
        sut._build_dosha_rows(
            DHANA_CONN(), CHART, CHART_ID, BUILD_ID, AY_ID, COMPUTED_AT, ENG_VER,
            dosha_catalog=[DARIDRA_ENTRY], downstream_doshas=frozenset(),
        )


def test_the_downstream_set_is_exactly_daridra():
    assert sut.DOWNSTREAM_CANCELLATION_DOSHAS == frozenset({"daridra"})
    assert "daridra" in sut.BESPOKE_DOSHA_DETECTORS  # the detector stays (pure); only the emit moved
    assert "daridra" not in sut.DOSHA_CANCELLATIONS


# ── the post-pass row: same natural key, same values ─────────────────────────

def test_post_pass_row_keeps_the_natural_key_and_values():
    rows = pp.build_daridra_label_rows(
        DHANA_CONN(), CHART_ID, BUILD_ID, AY_ID, chart_output=CHART, dosha_catalog=[DARIDRA_ENTRY],
    )
    assert len(rows) == 1
    r = rows[0]
    assert (r["fact_category"], r["fact_subject"], r["fact_key"]) == ("dosha_label", "daridra", "dosha_name")
    # fact_id is sha256(category|subject|key|chart|ayanamsha)[:16]: independent of build_id and of the producer
    assert r["fact_id"] == hashlib.sha256(f"dosha_label|daridra|dosha_name|{CHART_ID}|{AY_ID}".encode()).hexdigest()[:16]
    other = pp.build_daridra_label_rows(
        DHANA_CONN(), CHART_ID, "another-build", AY_ID, chart_output=CHART, dosha_catalog=[DARIDRA_ENTRY],
    )[0]
    assert other["fact_id"] == r["fact_id"]
    vj = r["fact_value_jsonb"]
    assert vj["fires"] is False and vj["bhanga_active"] is True
    assert vj["bhanga_rule_fired"] == "dhana_structure_fires:dhana_yoga_house_lords"
    assert vj["cancellation_citation_ref"] == "bphs:daridra:dhana_yoga_or_strong_wealth_lord_cancels"
    assert r["build_id"] == BUILD_ID


def test_post_pass_reads_the_cancellation_grounds_it_is_downstream_of():
    """Without the downstream data the daridra stands uncancelled; with it, cancelled: the post-pass is
    what makes the verdict depend on ga_yoga_firings / chart_vichara, deterministically, not on build order."""
    uncancelled = pp.build_daridra_label_rows(
        _CannedConn(), CHART_ID, BUILD_ID, AY_ID, chart_output=CHART, dosha_catalog=[DARIDRA_ENTRY],
    )[0]["fact_value_jsonb"]
    assert uncancelled["fires"] is True and uncancelled["bhanga_active"] is False
    exalted = pp.build_daridra_label_rows(
        _CannedConn(vichara_row=(1.4, {"d1_dignity": "exalted"})), CHART_ID, BUILD_ID, AY_ID,
        chart_output=CHART, dosha_catalog=[DARIDRA_ENTRY],
    )[0]["fact_value_jsonb"]
    assert exalted["bhanga_active"] is True and "ga_vichara" in exalted["bhanga_rule_fired"]


def test_post_pass_emits_nothing_when_daridra_does_not_form_or_catalog_lacks_it():
    from test_ga8_writer import MOCK_CHART_OUTPUT
    assert pp.build_daridra_label_rows(
        _CannedConn(), CHART_ID, BUILD_ID, AY_ID, chart_output=MOCK_CHART_OUTPUT, dosha_catalog=[DARIDRA_ENTRY],
    ) == []
    assert pp.build_daridra_label_rows(
        _CannedConn(), CHART_ID, BUILD_ID, AY_ID, chart_output=CHART,
        dosha_catalog=[_dosha_entry("kemadruma", "x")],
    ) == []


# ── write scope: ONE subject of a category ga_structural owns ────────────────

class _RecConn:
    def __init__(self):
        self.executed: list[tuple[str, object]] = []
        self.many: list[tuple[str, int]] = []

    def execute(self, sql, params=None):
        self.executed.append((" ".join(sql.split()), params))

        class _C:
            rowcount = 1
        return _C()

    def cursor(self, row_factory=None):
        conn = self

        class _Cur:
            def __enter__(s):
                return s

            def __exit__(s, *a):
                return False

            def executemany(s, sql, tuples):
                conn.many.append((" ".join(sql.split()), len(tuples)))

            def execute(s, sql, params=None):
                conn.executed.append((" ".join(sql.split()), params))

            def fetchone(s):
                return None

            def fetchall(s):
                return []
        return _Cur()


def test_delete_is_subject_scoped_never_category_wide():
    conn = _RecConn()
    assert pp.replace_prior_daridra_label_rows(conn, CHART_ID, AY_ID) == 1
    (sql, params), = conn.executed
    assert "fact_category = 'dosha_label'" in sql and "fact_subject = %s" in sql
    assert params == [CHART_ID, AY_ID, "daridra"]


def test_emit_writes_one_row_without_wiping_the_dosha_label_category(monkeypatch):
    monkeypatch.setattr(pp._gsw, "_load_dosha_catalog", lambda conn: [DARIDRA_ENTRY])
    monkeypatch.setattr(pp._gsw, "compute_chart", lambda inputs, ayanamsha_id: CHART)
    monkeypatch.setattr(pp._gsw, "_validate_chart_output_complete", lambda c: None)

    class _Conn(_RecConn):
        def cursor(self, row_factory=None):
            cur = super().cursor(row_factory)
            real_execute = cur.execute
            # canned dhana yoga firing for the cancellation read
            cur.execute = lambda sql, params=None: real_execute(sql, params)
            return cur
    conn = _Conn()
    n = pp.emit_daridra_label_post_pass(conn, CHART_ID, BUILD_ID, "lahiri_chitrapaksha", birth_params={"x": 1})
    assert n == 1
    sqls = [s for s, _ in conn.executed]
    assert any(s.startswith("DELETE FROM chart_facts") and "fact_subject = %s" in s for s in sqls)
    assert not any("fact_category = ANY" in s for s in sqls), "category-wide delete would wipe ga_structural's dosha rows"
    assert [c for _, c in conn.many] == [1]
    assert conn.many[0][0].startswith("INSERT INTO chart_facts")


def test_emit_with_no_daridra_still_clears_a_stale_prior_row(monkeypatch):
    monkeypatch.setattr(pp._gsw, "_load_dosha_catalog", lambda conn: [DARIDRA_ENTRY])
    from test_ga8_writer import MOCK_CHART_OUTPUT
    monkeypatch.setattr(pp._gsw, "compute_chart", lambda inputs, ayanamsha_id: MOCK_CHART_OUTPUT)
    monkeypatch.setattr(pp._gsw, "_validate_chart_output_complete", lambda c: None)
    conn = _RecConn()
    assert pp.emit_daridra_label_post_pass(conn, CHART_ID, BUILD_ID, "lahiri_chitrapaksha", birth_params={"x": 1}) == 0
    assert any(s.startswith("DELETE FROM chart_facts") for s, _ in conn.executed)
    assert conn.many == []


# ── fail loudly on an empty / unreadable catalog (never a silent delete of the prior row) ──

def test_build_rows_raises_on_an_empty_catalog_instead_of_returning_nothing():
    with pytest.raises(RuntimeError, match="brahma_dosha_catalog"):
        pp.build_daridra_label_rows(
            _CannedConn(), CHART_ID, BUILD_ID, AY_ID, chart_output=CHART, dosha_catalog=[],
        )


def test_emit_raises_on_an_empty_catalog_and_does_not_delete_the_prior_row(monkeypatch):
    monkeypatch.setattr(pp._gsw, "_load_dosha_catalog", lambda conn: [])
    monkeypatch.setattr(pp._gsw, "compute_chart", lambda inputs, ayanamsha_id: CHART)
    monkeypatch.setattr(pp._gsw, "_validate_chart_output_complete", lambda c: None)
    conn = _RecConn()
    with pytest.raises(RuntimeError, match="brahma_dosha_catalog"):
        pp.emit_daridra_label_post_pass(conn, CHART_ID, BUILD_ID, "lahiri_chitrapaksha", birth_params={"x": 1})
    assert not any(s.startswith("DELETE FROM chart_facts") for s, _ in conn.executed), \
        "an empty catalog must not silently erase the prior daridra row"
    assert conn.many == []


def test_emit_raises_on_an_unreadable_catalog_and_does_not_delete_the_prior_row():
    class _Broken(_RecConn):
        def cursor(self, row_factory=None):
            raise RuntimeError("connection lost")
    conn = _Broken()
    with pytest.raises(RuntimeError, match="brahma_dosha_catalog"):
        pp.emit_daridra_label_post_pass(conn, CHART_ID, BUILD_ID, "lahiri_chitrapaksha", birth_params={"x": 1})
    assert not any(s.startswith("DELETE FROM chart_facts") for s, _ in conn.executed)


# ── wiring: after ga_vichara's own insert, in ga_vichara, with no new DAG edge ─

def test_vichara_substep_runs_the_post_pass_after_its_chart_vichara_insert():
    src = _src("ga_writers/ga_vichara_writer.py")
    body = src[src.index("def build_ga_vichara_substep"):]
    assert body.index("_insert_rows(conn, chart_id, ayanamsha_id, build_id, all_rows)") < body.index("emit_daridra_label_post_pass(")


def test_no_new_dag_edge_ga_vichara_already_depends_on_both_upstreams():
    from pipeline.orchestrator.writers import ga_vichara as adapter  # noqa: F401
    from pipeline.orchestrator.writers import WRITER_REGISTRY
    deps = set(WRITER_REGISTRY["ga_vichara"].depends_on)
    assert {"ga_structural", "ga_yoga"} <= deps
    # the read order the post-pass relies on is exactly the edge set that already existed
    assert deps == {"ga_structural", "ga_strength", "ga_dashas", "ga_yoga"}
    assert "ga_daridra_postpass.py" in " ".join(WRITER_REGISTRY["ga_vichara"].source_paths)
