"""test_formgap_decl_sensdeg.py: the FORM-GAP declaration of ga_sensitive_degree is TRUE, shown on rows the REAL writer substep builds (SS multi-filter form).

The writer inserts two fact_categories (sensitive_degree_check, sensitive_point_yogi) into the shared chart_facts. `produced_tables` names both slices (one entry each); the prose_none judges the OR of them,
column_scope written: nine closed columns, the primary key, two templated pointers (citation_ref, source_calculation), the declared source column citation_human. The exception-text leaf the first audit found is gone
from main (closed reason codes). The vocabularies are compared with an independent sweep of the pure builders over synthetic charts; the real `build_ga_sensitive_degree_substep` runs on a throw-away PostgreSQL
with the real chart_facts DDL for two charts and five ayanamshas (one with the neecha-bhanga detector forced to raise: the reason-code row), and the engine's own `_measure_prose` reads all six cells.
"""
from __future__ import annotations

import json
import pathlib
import random
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import CHART_A, CHART_B, NA, FAIL, NO_DET, CELLS  # noqa: E402

AID = "ga_sensitive_degree"
T = "chart_facts"
DECLS = ac.load_asset_declarations()
PN = DECLS[AID]["prose_none"]
RUN = "11111111-1111-4111-8111-111111111111"


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _closed(col):
    return next(c for c in PN["closed_columns"] if c["column"] == col)


def test_the_declaration_is_sound_with_two_slices_and_the_exact_forms():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and ac.produced_tables_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    assert [(t["table"], t["filter"]["equals"]) for t in e["produced_tables"]] == [(T, "sensitive_degree_check"), (T, "sensitive_point_yogi")] and PN["column_scope"] == "written"
    assert [c["column"] for c in PN["identifier_columns"]] == ["fact_id"] and [c["column"] for c in PN["templated_columns"]] == ["citation_ref", "source_calculation"]
    assert ac.multi_filter_groups(e) == {T: ("fact_category", ["sensitive_degree_check", "sensitive_point_yogi"])}


def test_the_writer_scan_shows_both_declared_categories_written():
    got = ac.multi_filter_scan(AID, ac.registered_ids("")[AID], DECLS[AID])
    assert got[T]["found"] == ["sensitive_degree_check", "sensitive_point_yogi"] and got[T]["scan_cut"] is False


def test_the_exception_text_leaf_is_gone_from_the_writer():
    src = (HERE.parents[2] / "python-sidecar/ga_writers/ga_sensitive_degree_writer.py").read_text(encoding="utf-8")
    assert "str(exc)[:200]" not in src and '"reason_code": REASON_DETECTOR_RAISED' in src


def test_the_vocabularies_cover_an_independent_sweep_of_the_pure_builders():
    import ga_writers.ga_sensitive_degree_writer as W
    rnd = random.Random(7)
    graha = list(W.NINE_GRAHAS) + ["Lagna"]
    seen = {k: set() for k in ("fact_subject", "fact_key", "fact_value_text", "leaf", "verification_pass_status", "unit")}

    def leaves(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from leaves(v)
        elif isinstance(x, list):
            for v in x:
                yield from leaves(v)
        elif isinstance(x, str):
            yield x
    for i in range(400):
        pos = {}
        for g in graha:
            lon = rnd.uniform(0, 360)
            pos[g] = dict(sign=W.SIGNS[int(lon // 30)], sign_num=int(lon // 30), degree_in_sign=lon % 30, longitude_sidereal=lon, house_d1=rnd.randint(1, 12), nakshatra=rnd.choice(W.YOGI_NAKSHATRAS))
        off = rnd.choice([None, 23.85, 24.1])
        rows = W.build_sensitive_degree_rows(CHART_A, RUN, "lahiri_chitrapaksha", pos, off) + W.build_yogi_points_rows(CHART_A, "lahiri_chitrapaksha", RUN, pos, None)
        for r in rows:
            seen["fact_subject"].add(r["fact_subject"]); seen["fact_key"].add(r["fact_key"]); seen["verification_pass_status"].add(r["verification_pass_status"])
            if r["fact_value_text"] is not None:
                seen["fact_value_text"].add(r["fact_value_text"])
            if r["unit"] is not None:
                seen["unit"].add(r["unit"])
            if r["fact_value_jsonb"] is not None:
                seen["leaf"].update(leaves(json.loads(r["fact_value_jsonb"])))
    for key, col in (("fact_subject", "fact_subject"), ("fact_key", "fact_key"), ("fact_value_text", "fact_value_text"), ("leaf", "fact_value_jsonb"), ("verification_pass_status", "verification_pass_status"), ("unit", "unit")):
        assert seen[key] <= set(_closed(col)["values"]), (col, sorted(seen[key] - set(_closed(col)["values"])))
    assert seen["fact_key"] == set(_closed("fact_key")["values"]) and seen["unit"] == {"deg"}


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    pytest.importorskip("jhora")
    pg = disposable_pg
    fs.install_chart_facts(pg)
    fs.psql(pg, "DELETE FROM chart_facts")
    fs.seed_positions(pg, CHART_A)
    fs.seed_positions(pg, CHART_B, pos=dict(fs.CHART_POS, Moon=(7, 12.0, 8), Sun=(3, 4.0, 4)))
    fs.psql(pg, "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key, fact_value_num, citation_ref, citation_human, source_calculation, verification_pass_status, engine_version, computed_at) "
                f"VALUES ('aya-off', '{CHART_A}', 'lahiri_chitrapaksha', gen_random_uuid(), 'ayanamsha', 'AYA', 'ayanamsha_value', 24.1, 'x', 'x', 'x', 'single', 'x', now())")
    import ga_writers.ga_sensitive_degree_writer as W
    import ga_writers.ga_yoga_writer as Y
    conn = psycopg.connect(pg.url, autocommit=True)
    n = 0
    for chart in (CHART_A, CHART_B):
        for aya in W.CANONICAL_AYANAMSHAS:
            if aya == "raman":                                     # the neecha-bhanga detector raises: the closed reason-code row
                orig = Y.detect_neecha_bhanga
                Y.detect_neecha_bhanga = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("detector shape mismatch with free text"))
                try:
                    n += W.build_ga_sensitive_degree_substep(chart, RUN, aya, conn)
                finally:
                    Y.detect_neecha_bhanga = orig
            else:
                n += W.build_ga_sensitive_degree_substep(chart, RUN, aya, conn)
    conn.close()
    assert n > 400, n
    yield pg
    fs.psql(pg, "DROP TABLE IF EXISTS chart_facts CASCADE")


def _m(db, mp, decl=None, chart=CHART_A):
    scope = {T: dict(where=f"chart_id = '{chart}'", label="the measured chart")}
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T, [T], decl or _own(), scope=scope, shared={"chart_facts"}, registry=dict(has_writer=True, count_sql=f"SELECT COUNT(*) FROM chart_facts WHERE chart_id=$1 AND fact_category='sensitive_degree_check'"))


def test_REAL_WRITER_the_substep_wrote_both_categories_and_the_reason_code_row(db):
    assert fs.psql(db, f"SELECT string_agg(DISTINCT fact_category, ',' ORDER BY fact_category) FROM chart_facts WHERE chart_id = '{CHART_A}' AND fact_category LIKE 'sensitive%'").strip() == "sensitive_degree_check,sensitive_point_yogi"
    assert int(fs.psql(db, "SELECT count(*) FROM chart_facts WHERE fact_value_jsonb::text LIKE '%detector_raised%'").strip()) > 0
    assert int(fs.psql(db, "SELECT count(*) FROM chart_facts WHERE fact_value_jsonb::text LIKE '%free text%'").strip()) == 0                    # the exception text never reaches a row


def test_REAL_WRITER_the_two_categories_read_na_on_all_six_cells_through_checked_blocks(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert f["multi_filter"][0]["values"] == ["sensitive_degree_check", "sensitive_point_yogi"] and {x["column"] for x in f["templated"]} == {"citation_ref", "source_calculation"}


def test_REAL_WRITER_other_assets_rows_of_the_shared_table_are_not_judged(db, monkeypatch):
    fs.psql(db, f"INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, fact_category, fact_subject, fact_key, fact_value_text, citation_ref, citation_human, source_calculation, verification_pass_status, engine_version, computed_at) "
                f"VALUES ('other-asset-row', '{CHART_A}', 'lahiri_chitrapaksha', gen_random_uuid(), 'graha_position', 'SUN', 'sign', 'a free sentence another asset owns', 'x', 'x', 'x', 'single', 'x', now())")
    try:
        assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA
    finally:
        fs.psql(db, "DELETE FROM chart_facts WHERE fact_id = 'other-asset-row'")


# (category slice, column, new SQL value, cast, needle)
MUTS = [
    ("sensitive_degree_check", "fact_value_text", "'a freshly composed verdict sentence'", "", "fact_value_text"),
    ("sensitive_point_yogi", "fact_value_text", "'a freshly composed verdict sentence'", "", "fact_value_text"),
    ("sensitive_degree_check", "fact_value_jsonb", "'{\"error\": \"detector shape mismatch\"}'::jsonb", "::jsonb", "fact_value_jsonb"),
    ("sensitive_point_yogi", "fact_value_jsonb", "'{\"note\": \"free text\"}'::jsonb", "::jsonb", "fact_value_jsonb"),
    ("sensitive_degree_check", "fact_subject", "'PLUTO'", "", "fact_subject"),
    ("sensitive_point_yogi", "fact_key", "'a_new_key'", "", "fact_key"),
    ("sensitive_degree_check", "citation_ref", "'WP-2.5/LCA-10/invented_key'", "", "citation_ref"),
    ("sensitive_point_yogi", "source_calculation", "'ga_sensitive_degree_writer/sign/manual_override'", "", "source_calculation"),
    ("sensitive_degree_check", "verification_pass_status", "'two_pass_verified'", "", "verification_pass_status"),
    ("sensitive_degree_check", "engine_version", "'ga_sensitive_degree_v2'", "", "engine_version"),
    ("sensitive_degree_check", "unit", "'rad'", "", "unit"),
    ("sensitive_point_yogi", "ayanamsha_id", "'fagan'", "", "ayanamsha_id"),
]


@pytest.mark.parametrize("cat,col,newv,cast,needle", MUTS)
def test_REAL_WRITER_MUTATION_a_value_outside_its_form_in_either_category_is_a_FAIL(db, monkeypatch, cat, col, newv, cast, needle):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, T, "fact_id", col, newv, f"chart_id = '{CHART_A}' AND fact_category = '{cat}' AND {col} IS NOT NULL", check, cast=cast)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_two_charts_a_bad_value_of_the_other_chart_is_not_the_measured_charts(db, monkeypatch):
    def check():
        assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA
        assert _m(db, monkeypatch, chart=CHART_B)["Narr.agree"]["v"] == FAIL
    fs.mutate_and_restore(db, T, "fact_id", "fact_value_text", "'a freshly composed verdict sentence'", f"chart_id = '{CHART_B}' AND fact_category = 'sensitive_point_yogi' AND fact_value_text IS NOT NULL", check)


def test_REAL_WRITER_MUTATION_a_declaration_with_one_slice_only_misses_the_yogi_rows_and_the_scan_cannot_hide_a_phantom_one(db, monkeypatch):
    d = _own()
    d["produced_tables"] = [dict(table=T, filter=dict(column="fact_category", equals="sensitive_degree_check"))]
    fs.mutate_and_restore(db, T, "fact_id", "fact_value_text", "'a freshly composed verdict sentence'", f"chart_id = '{CHART_A}' AND fact_category = 'sensitive_point_yogi' AND fact_value_text IS NOT NULL",
                          lambda: (lambda g: g["Narr.agree"]["v"] == NA or pytest.fail("the yogi slice was judged"))(_m(db, monkeypatch, d)))      # what the old single-slice declaration could not see
    d2 = _own()
    d2["produced_tables"][1]["filter"]["equals"] = "sensitive_point_ghost"
    got = _m(db, monkeypatch, d2)
    assert got["Narr.agree"]["v"] == FAIL and "sensitive_point_ghost" in got["Narr.agree"]["measured"]
