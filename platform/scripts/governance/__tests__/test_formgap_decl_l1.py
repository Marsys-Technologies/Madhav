"""test_formgap_decl_l1.py: the FORM-GAP declarations of two L1 assets are TRUE, shown on rows the REAL writers build (SS N-191).

  * ga_transit_anchors (migration 267): `build_id TEXT` holds the orchestrator run id. Declared as a `run_stamp_columns` entry: every value must be a uuid AND a run id of this asset.
  * ga_dashas: `chart_dashas.citation_ref` is a pointer built by 13 f-string sites that embed the chart id. Declared as `templated_columns` (14 templates with {chart_id} bound to the MEASURED chart); the other
    text columns it writes are closed vocabularies; the writer bulk-loads by COPY, which the written-columns read now sees (so `column_scope: written` judges chart_dashas at all).
    ga_sensitive_degree is NOT declared: its detector-failure branch stores `{"error": str(exc)[:200]}` (ga_sensitive_degree_writer.py:761), exception text no form can close (a writer edit, not made here).

The closed vocabularies are stated BY HAND in this file and compared with the writer's own constants; the real writers run on a throw-away PostgreSQL carrying the DDL of the real migrations; the engine's OWN
`_measure_prose` then reads each asset and all six Narr/Null cells must read N/A through a checked block. Every claim has a mutation that must turn the reading red. The Swiss-ephemeris corpus check (.se1 files,
not available offline) is stood in by a no-op so the Mudda system, whose row text is the writer's own, can run on the Moshier fallback; no other writer logic is replaced.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
import prose_forms as pf  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import CHART_A, CHART_B, RUN_1, RUN_2, NA, FAIL, NO_DET, CELLS  # noqa: E402

DECLS = ac.load_asset_declarations()
DW = "platform/python-sidecar/ga_writers/ga_dashas_writer.py"
GRAHA9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
YOGINI8 = ["Mangala", "Pingala", "Dhanya", "Bhramari", "Bhadrika", "Ulka", "Siddha", "Sankata"]
SIGNS12 = fs.SIGNS


def _need(*mods):
    for m in mods:
        pytest.importorskip(m)


# ═════════════════════════════════════════ ga_transit_anchors ═════════════════════════════════════════
TA = "ga_transit_anchors"


def test_ga_transit_anchors_declaration_is_the_checked_form_with_the_stated_columns():
    e = DECLS[TA]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer" and ac.prose_none_problem(e) is None
    pn = e["prose_none"]
    assert [c["column"] for c in pn["run_stamp_columns"]] == ["build_id"] and [c["column"] for c in pn["identifier_columns"]] == ["ayanamsha_id", "graha"]
    assert [c["column"] for c in pn["closed_columns"]] == ["natal_sign"] and pn["closed_columns"][0]["values"] == [s.lower() for s in SIGNS12]
    assert "column_scope" not in pn                                                         # every text column of the table is judged


def test_ga_transit_anchors_writer_facts_the_declaration_rests_on():
    """Hand-stated against the writer source (AST), not recomputed from the declaration."""
    src = (fs.REPO / "platform/python-sidecar/pipeline/orchestrator/writers/ga_transit_anchors.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    ins = [n for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and "INSERT INTO ga_transit_anchors" in n.value]
    assert len(ins) == 1 and "(chart_id, build_id, ayanamsha_id, graha," in ins[0].value and "natal_sign, natal_house_from_moon, natal_degree_absolute)" in ins[0].value
    assert "ctx.build_id," in src and src.count("INSERT INTO ga_transit_anchors") == 1
    assert 'positions[graha]["natal_sign"] = val_text.lower()' in src and "_house_from_moon(moon_sign, natal_sign)" in src
    assert re.search(r"_SIGN_NUM_TO_NAME.*?\{(.*?)\n\}", src, re.S) is not None
    # the INSERT's parameters are bare names / attributes: no f-string, join, slice or call builds a written value at the execute site
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "execute" and n.args and isinstance(n.args[0], ast.Constant)
             and "INSERT INTO ga_transit_anchors" in n.args[0].value]
    assert len(calls) == 1 and isinstance(calls[0].args[1], ast.Tuple)
    assert [type(e).__name__ for e in calls[0].args[1].elts] == ["Name", "Attribute", "Name", "Name", "Name", "Name", "Name"]
    assert [ast.unparse(e) for e in calls[0].args[1].elts] == ["chart_id", "ctx.build_id", "ayanamsha_id", "graha", "natal_sign", "house_from_moon", "natal_degree"]


@pytest.fixture(scope="module")
def db_ta(disposable_pg):
    _need("psycopg")
    pg = disposable_pg
    for t in ("ga_transit_anchors", "chart_facts", "build_run_assets", "build_runs", "asset_provenance_receipts", "charts", "asset_registry"):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.install_run_tables(pg)
    fs.install_chart_facts(pg)
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "267_ga_transit_anchors.sql", "ga_transit_anchors"))
    fs.seed_positions(pg, CHART_A)
    fs.seed_positions(pg, CHART_B, pos=dict(fs.CHART_POS, Moon=(7, 12.0, 8)))
    fs.add_run(pg, RUN_1, TA)
    fs.add_run(pg, RUN_2, TA, chart_id=CHART_B)
    import psycopg
    from pipeline.orchestrator.writers import ContextSpec, SubStep
    from pipeline.orchestrator.writers.ga_transit_anchors import GaTransitAnchorsWriter
    conn = psycopg.connect(pg.url, autocommit=True)
    for chart, run in ((CHART_A, RUN_1), (CHART_B, RUN_2)):
        w = GaTransitAnchorsWriter()
        ctx = ContextSpec(asset_id=TA, build_id=run, db_conn=conn, config={"chart_id": chart})
        for step in w.plan_substeps(ctx):
            w.run_substep(ctx, step)
    conn.close()
    yield pg
    for t in ("ga_transit_anchors", "chart_facts", "asset_provenance_receipts", "build_run_assets", "build_runs", "charts", "asset_registry"):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def _m_ta(pg, mp, decl=None, scope=None):
    return fs.measure(TA, pg, mp, ac.registered_ids("")[TA], TA, [TA], decl or DECLS[TA], scope=scope)


def test_REAL_WRITER_ga_transit_anchors_rows_read_na_on_all_six_through_the_run_stamp_form(db_ta, monkeypatch):
    assert fs.psql(db_ta, f"SELECT count(*) FROM ga_transit_anchors WHERE chart_id = '{CHART_A}'").strip() == "45"            # 9 grahas x 5 ayanamshas, the writer's own rows
    got = _m_ta(db_ta, monkeypatch)
    fs.all_na(got)
    forms = got["Narr.agree"]["prose_none"]["forms"]
    assert forms["run_stamp"][0]["column"] == "build_id" and forms["run_stamp"][0]["distinct"] == 2 and forms["run_stamp"][0]["resolved"] == 2       # both charts' runs are runs of this asset
    assert got["Narr.agree"]["prose_none"]["identifier_columns"] == ["ga_transit_anchors.ayanamsha_id", "ga_transit_anchors.graha"]


def test_REAL_WRITER_two_charts_a_stamp_the_scope_excludes_is_not_judged(db_ta, monkeypatch):
    scope = {TA: dict(where=f"chart_id = '{CHART_A}'", label="the measured chart")}
    got = _m_ta(db_ta, monkeypatch, scope=scope)
    fs.all_na(got)
    assert got["Narr.agree"]["prose_none"]["forms"]["run_stamp"][0]["distinct"] == 1


def test_MUTATION_ga_transit_anchors_a_stamp_that_is_not_a_run_a_sentence_and_a_sign_outside_the_twelve_all_turn_it_red(db_ta, monkeypatch):
    try:
        fs.psql(db_ta, "UPDATE ga_transit_anchors SET build_id = 'hand-edited on friday' WHERE graha = 'sun' AND ayanamsha_id = 'raman' AND chart_id = '%s'" % CHART_A)
        got = _m_ta(db_ta, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "not run ids" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db_ta, f"UPDATE ga_transit_anchors SET build_id = '{RUN_1}' WHERE chart_id = '{CHART_A}'")
    try:
        fs.psql(db_ta, f"UPDATE ga_transit_anchors SET build_id = '{'4' * 8}-4444-4444-8444-{'4' * 12}' WHERE chart_id = '{CHART_A}' AND graha = 'moon'")
        got = _m_ta(db_ta, monkeypatch)
        assert all(got[c]["v"] == NO_DET for c in CELLS) and "no run id of this asset" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db_ta, f"UPDATE ga_transit_anchors SET build_id = '{RUN_1}' WHERE chart_id = '{CHART_A}'")
    try:
        fs.psql(db_ta, f"UPDATE ga_transit_anchors SET natal_sign = 'Aquarius (Moon sign)' WHERE chart_id = '{CHART_A}' AND graha = 'moon' AND ayanamsha_id = 'raman'")
        got = _m_ta(db_ta, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "ga_transit_anchors.natal_sign" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db_ta, f"UPDATE ga_transit_anchors SET natal_sign = 'aquarius' WHERE chart_id = '{CHART_A}' AND graha = 'moon' AND ayanamsha_id = 'raman'")
    assert _m_ta(db_ta, monkeypatch)["Narr.agree"]["v"] == NA                                                                  # restored


def test_MUTATION_ga_transit_anchors_the_declaration_without_its_run_stamp_form_leaves_build_id_open(db_ta, monkeypatch):
    d = {k: v for k, v in DECLS[TA].items()}
    d["prose_none"] = {k: v for k, v in DECLS[TA]["prose_none"].items() if k != "run_stamp_columns"}
    got = _m_ta(db_ta, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "ga_transit_anchors.build_id (text)" in got["Narr.agree"]["measured"]            # this is the old gap the form closes


# ═════════════════════════════════════════ ga_dashas ═════════════════════════════════════════
AID = "ga_dashas"
BP_A = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.2961, "longitude_deg": 85.8245, "tz_offset_hours": 5.5}
BP_B = {"datetime_iso": "1990-06-15T06:30:00", "latitude_deg": 28.6139, "longitude_deg": 77.2090, "tz_offset_hours": 5.5}
ROLES = {"Moon": "AK", "Saturn": "AmK", "Sun": "BK", "Venus": "MK", "Mars": "PiK", "Rahu": "PK", "Jupiter": "GK", "Mercury": "DK"}
DIGNITY = {"Sun": "exalted", "Moon": "neutral", "Mars": "own", "Mercury": "neutral", "Jupiter": "debilitated", "Venus": "moolatrikona", "Saturn": "unknown", "Rahu": "neutral", "Ketu": "neutral"}


def test_ga_dashas_declaration_is_the_checked_form_and_its_vocabularies_are_the_ones_stated_here():
    e = DECLS[AID]
    assert e["prose_fields"] == [] and e["evidence_kind"] == "writer" and ac.prose_none_problem(e) is None
    pn = e["prose_none"]
    assert pn["column_scope"] == "written" and [t["column"] for t in pn["templated_columns"]] == ["citation_ref"]
    cols = {(c.get("table"), c["column"]): c["values"] for c in pn["closed_columns"]}
    sign_lords = SIGNS12
    assert cols[(None, "lord_graha")] == GRAHA9 + YOGINI8 + sign_lords + ["KP_LEVELS_BEYOND_SUB_SUB"]
    assert cols[(None, "system_id")] == ["vimshottari", "yogini", "ashtottari", "chara_karaka", "naisargika", "mudda", "kalachakra", "narayana", "vimshottari_kp", "scope_cap"]
    assert cols[(None, "ayanamsha_id")] == fs.AYANAMSHAS + ["INVARIANT"] and cols[("chart_facts", "ayanamsha_id")] == ["INVARIANT"]
    assert cols[(None, "karaka_role_at_period")] == ["AK", "AmK", "BK", "MK", "PiK", "PK", "GK", "DK"]
    assert cols[(None, "lord_natal_nakshatra")] in (fs.NAKSHATRA27, fs.NAKSHATRA27_LEGACY) and cols[(None, "lord_natal_sign")] == SIGNS12 == cols[(None, "lord_sign")]
    assert cols[(None, "lord_natal_dignity_d1")] == ["exalted", "debilitated", "moolatrikona", "own", "neutral", "unknown"]
    assert cols[(None, "period_deity_or_marker")] == YOGINI8 + [f"Kalachakra-{s}" for s in SIGNS12] + ["scope_cap"]
    assert len(cols[(None, "karakas_active_during_period")]) == 64 and "Rahu:PK" in cols[(None, "karakas_active_during_period")] and "Ketu:PK" not in cols[(None, "karakas_active_during_period")]
    assert cols[(None, "concurrent_system_lords_jsonb")] == GRAHA9 + YOGINI8 + SIGNS12


def test_the_declared_vocabularies_equal_what_the_writer_itself_defines():
    _need("psycopg", "swisseph")
    from ga_writers import ga_dashas_writer as w
    from ga_writers._karaka_roles import KARAKA_ABBREVIATIONS_8
    pn = DECLS[AID]["prose_none"]
    cols = {(c.get("table"), c["column"]): c["values"] for c in pn["closed_columns"]}
    assert list(w.AYANAMSHAS) == fs.AYANAMSHAS and sorted(w.SYSTEMS + [w.KP_SYSTEM_ID, "scope_cap"]) == sorted(cols[(None, "system_id")])
    assert list(w.VIMSHOTTARI_SEQUENCE) == ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"] and sorted(GRAHA9) == sorted(w.VIMSHOTTARI_SEQUENCE)
    assert [n for n, _g, _y in w.YOGINI_SEQUENCE] == YOGINI8
    assert w._MUDDA_IDX_TO_LORD == GRAHA9
    assert sorted(l for l, _ in w.ASHTOTTARI_SEQUENCE) == sorted(pn["templated_columns"][0]["placeholders"]["achain"]["values"])
    assert sorted(l for l, _ in w.NAISARGIKA_SEQUENCE) == sorted(pn["templated_columns"][0]["placeholders"]["kchain"]["values"])
    assert list(w._KARAKAS_ACTIVE_GRAHA_ORDER) == ["Sun", "Mars", "Mercury", "Saturn", "Jupiter", "Venus", "Moon", "Rahu"] and list(KARAKA_ABBREVIATIONS_8) == cols[(None, "karaka_role_at_period")]
    assert w.SCOPE_CAP_SENTINEL == "scope_cap_sentinel" and w.KP_SYSTEM_ID == "vimshottari_kp"


def _fstring_skeleton(node: ast.JoinedStr) -> str:
    return "".join(p.value if isinstance(p, ast.Constant) else "{}" for p in node.values)


def _writer_citation_ref_skeletons():
    """Every string the writer builds that starts `chart_dashas.` (the 13 citation_ref f-string sites), with each field replaced by `{}`; an implicit concatenation of two f-strings is one JoinedStr."""
    tree = ast.parse((fs.REPO / DW).read_text(encoding="utf-8"))
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.JoinedStr) and n.values and isinstance(n.values[0], ast.Constant) and n.values[0].value.startswith("chart_dashas."):
            out.append(_fstring_skeleton(n))
    return out


def _template_skeleton(t: str) -> str:
    return re.sub(r"\{[a-z0-9_]+\}", "{}", t)


def _collapse(skel: str):
    """`{}-{}` (two fields joined by the dash of a lord chain) is ONE sequence placeholder of the declaration: (skeleton with sequences collapsed, the arities of the collapsed sequences in order)."""
    arities = [m.group(0).count("{}") for m in re.finditer(r"(?:\{\}-)+\{\}", skel)]
    return re.sub(r"(?:\{\}-)+\{\}", "{}", skel), arities


def test_the_declared_templates_are_exactly_the_writers_citation_ref_f_strings():
    """A 14th f-string site, a changed literal or a dropped site breaks this: the declaration is pinned to the writer source (AST), site for site, including the fixed arity of the KP / Mudda-L2 chains."""
    sites = _writer_citation_ref_skeletons()
    assert len(sites) == 13, sites
    tpls = [t for t in DECLS[AID]["prose_none"]["templated_columns"][0]["templates"] if t != "L1_GANITA_SCOPE_CAP"]
    ph = DECLS[AID]["prose_none"]["templated_columns"][0]["placeholders"]
    assert sorted(_collapse(_template_skeleton(t))[0] for t in tpls) == sorted(_collapse(x)[0] for x in sites)
    by_skel = {_collapse(_template_skeleton(t))[0]: t for t in tpls}
    for x in sites:                                                        # a chain of FIXED length in the writer (KP sub 2, KP sub-sub 3, Mudda L2 2) is a fixed-length sequence in the declaration
        skel, arities = _collapse(x)
        seq = [n for n in re.findall(r"\{([a-z0-9_]+)\}", by_skel[skel]) if "join" in ph.get(n, {})]
        assert len(seq) == 1 and len(arities) <= 1, (x, seq)
        if arities and arities[0] > 1:
            assert (ph[seq[0]]["min"], ph[seq[0]]["max"]) == (arities[0], arities[0]), (x, ph[seq[0]])
    assert "L1_GANITA_SCOPE_CAP" in DECLS[AID]["prose_none"]["templated_columns"][0]["templates"]
    src = (fs.REPO / DW).read_text(encoding="utf-8")
    assert '"citation_ref": "L1_GANITA_SCOPE_CAP"' in src                                                       # the one fixed pointer (the KP cap row of chart_dashas)
    assert "'dasha_scope_cap', 'PRANA_DASHA', 'level_5_not_computed', %s::jsonb," in src and "'scope_declaration', 'L1_GANITA_SCOPE_CAP', %s," in src      # and the Prana fact's


def test_the_chart_id_is_nowhere_in_the_committed_declaration_of_ga_dashas():
    blob = repr(DECLS[AID]["prose_none"])
    assert not re.search(pf.UUID_ANY_RE, blob)


@pytest.fixture(scope="module")
def db_d(disposable_pg):
    """The real ga_dashas writer, every system, on the real DDL: the native chart for Lahiri (all eight systems) and the other four ayanamshas (all but Mudda), and a second chart."""
    _need("psycopg", "swisseph", "jhora")
    pg = disposable_pg
    for t in ("chart_dashas", "chart_facts", "chart_divisionals", "reference_nakshatra", "reference_nakshatra_pada", "reference_nakshatra_matrix"):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "206_ga3_supporting_tables.sql", "chart_dashas"))
    for f in ("211_ga7_dashas_kp_sublevel.sql", "428_chart_dashas_v11_dead_column_drop.sql", "414_chart_dashas_kp_sublevel_unique_key.sql"):
        fs.psql(pg, path=fs.SMIG / f)
    fs.psql(pg, path=fs.MIG / "652_nirmana_l1_ga_dashas_scope_cap_sentinel_vocab.sql")
    fs.install_chart_facts(pg)
    # the columns of chart_divisionals the writer READS (the full table is built by ga_vargas; its migrations add these as fact_* columns)
    fs.psql(pg, "CREATE TABLE chart_divisionals (chart_id uuid, ayanamsha_id text, graha text, varga text, fact_category text, fact_key text, fact_value_text text)")
    for t in ("reference_nakshatra", "reference_nakshatra_pada", "reference_nakshatra_matrix"):
        fs.psql(pg, fs.create_table_ddl(fs.SMIG / "238_bg_nakshatra_tables.sql", t))
    import psycopg
    from psycopg.rows import dict_row
    import panchang_engine.swiss_backend as sb
    import pyjhora_adapter._swiss_thread_scope as ts
    from brahmagyan import l0_nakshatra
    from ga_writers import ga_dashas_writer as w
    conn = psycopg.connect(pg.url, autocommit=True)
    l0_nakshatra.seed_nakshatra(conn, RUN_1)
    fake = sb.SwissBackend(sb.BACKEND_SWIEPH, "/nonexistent")
    saved = (sb.ensure_swiss_backend, ts.ensure_swiss_backend, w._activate_karaka_roles)
    sb.ensure_swiss_backend = lambda *a, **k: fake            # the .se1 corpus is not available offline: the Moshier fallback computes (the row text is the writer's own)
    ts.ensure_swiss_backend = lambda *a, **k: fake
    w._activate_karaka_roles = lambda chart_id, ayan, c: w.set_karaka_roles(chart_id, ayan, ROLES)
    try:
        # the native chart: all eight systems for Lahiri; the other four ayanamshas for the systems that are quick to build (every ayanamsha value and every pointer form is shown); a second chart: three systems
        plan = [(CHART_A, BP_A, RUN_1, fs.AYANAMSHAS[:1], w.SYSTEMS), (CHART_A, BP_A, RUN_1, fs.AYANAMSHAS[1:], ["vimshottari", "ashtottari", "narayana"]),
                (CHART_B, BP_B, RUN_2, fs.AYANAMSHAS[:1], ["vimshottari", "yogini", "naisargika"])]
        for chart, ayas in {(c, tuple(a)) for c, _b, _r, a, _s in plan}:
            fs.seed_positions(pg, chart, list(ayas))
            for aya in ayas:
                for g, dg in DIGNITY.items():
                    fs.psql(pg, f"INSERT INTO chart_divisionals VALUES ('{chart}', '{aya}', '{g}', 'D1', 'varga_dignity', 'dignity', '{dg.capitalize()}')")
        for chart, bp, run, ayas, systems in plan:
            for aya in ayas:
                for system in systems:
                    w.build_system(system, aya, chart, run, conn=conn, birth_params=bp)
        conn_d = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
        for chart, run in ((CHART_A, RUN_1), (CHART_B, RUN_2)):
            w._run_concurrency_post_pass_db(chart, run, conn=conn_d)
            w.write_dasha_scope_cap_sentinels(chart, run, conn=conn_d)
        conn_d.close()
    finally:
        sb.ensure_swiss_backend, ts.ensure_swiss_backend, w._activate_karaka_roles = saved
        conn.close()
    yield pg
    for t in ("chart_dashas", "chart_facts", "chart_divisionals", "reference_nakshatra", "reference_nakshatra_pada", "reference_nakshatra_matrix"):
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")


def _m_d(pg, mp, decl=None, scope=True, only=None):
    """The engine's own read of ga_dashas. `only` = [(table, column)]: judge just those written columns (the written-columns read is narrowed), so a mutation test costs one column scan, not the whole table."""
    mp.setattr(ac, "CHART_ID", CHART_A)
    if only is not None:
        mp.setattr(ac, "written_columns", lambda units, tables: {t: {c for tt, c in only if tt == t} for t in {tt for tt, _ in only}})
    sc = None
    if scope:
        sc = {"chart_dashas": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart"), "chart_facts": dict(where=f"chart_id = '{CHART_A}'", label="the measured chart")}
    return fs.measure(AID, pg, mp, ac.registered_ids("")[AID], "chart_dashas", ["chart_dashas", "chart_facts"], decl or DECLS[AID], scope=sc)


def test_REAL_WRITER_every_system_reads_na_on_all_six_through_the_checked_forms(db_d, monkeypatch):
    systems = set(fs.psql(db_d, f"SELECT DISTINCT system_id FROM chart_dashas WHERE chart_id = '{CHART_A}'").split())
    assert systems == {"vimshottari", "vimshottari_kp", "yogini", "ashtottari", "chara_karaka", "naisargika", "mudda", "kalachakra", "narayana", "scope_cap"}
    got = _m_d(db_d, monkeypatch)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert b["column_scope"] == "written" and b["forms"]["templated"] == [dict(table="chart_dashas", column="citation_ref", verified=True, chart_id_bound=True, templates=14)]
    assert "chart_dashas.citation_human" not in [f"{x['table']}.{x['column']}" for x in b["closed"]] and "citation_human" in b["source_columns"]
    closed = {(x["table"], x["column"]) for x in b["closed"]}
    assert {("chart_dashas", "lord_graha"), ("chart_dashas", "concurrent_system_lords_jsonb"), ("chart_dashas", "karakas_active_during_period"), ("chart_facts", "citation_human")} <= closed


def test_REAL_WRITER_two_charts_only_the_measured_charts_pointers_are_judged(db_d, monkeypatch):
    other = fs.psql(db_d, f"SELECT count(*) FROM chart_dashas WHERE chart_id = '{CHART_B}' AND citation_ref LIKE '%{CHART_B}%'").strip()
    assert int(other) > 1000                                                                                   # chart B's rows name chart B, as they should
    assert _m_d(db_d, monkeypatch, only=[("chart_dashas", "citation_ref")])["Narr.agree"]["v"] == NA                                                    # the scope hides them
    whole = _m_d(db_d, monkeypatch, scope=False, only=[("chart_dashas", "citation_ref")])
    assert whole["Narr.agree"]["v"] == FAIL and "another chart's id" in whole["Narr.agree"]["measured"]       # without the scope chart B's pointers carry another chart's id


def _restore(pg, sql_undo):
    fs.psql(pg, sql_undo)


@pytest.mark.parametrize("col,bad,needle", [
    ("lord_graha", "Pluto", "chart_dashas.lord_graha"),
    ("karaka_role_at_period", "Sakha", "chart_dashas.karaka_role_at_period"),
    ("lord_natal_nakshatra", "Mrigashirsha", "chart_dashas.lord_natal_nakshatra"),      # a spelling no producer uses
    ("lord_natal_dignity_d1", "friend", "chart_dashas.lord_natal_dignity_d1"),
    ("period_deity_or_marker", "Kalachakra-Aquarious", "chart_dashas.period_deity_or_marker"),
    ("engine_version", "pyjhora_adapter/9.9.9", "chart_dashas.engine_version"),
    ("verification_method", "a hand-written explanation of the check", "chart_dashas.verification_method"),
])
def test_REAL_WRITER_MUTATION_a_value_outside_a_closed_vocabulary_is_a_FAIL(db_d, monkeypatch, col, bad, needle):
    rid = fs.psql(db_d, "SELECT dasha_row_id FROM chart_dashas WHERE chart_id = '%s' AND %s IS NOT NULL AND system_id = '%s' ORDER BY dasha_row_id LIMIT 1" % (CHART_A, col, "vimshottari" if col not in ("period_deity_or_marker",) else "kalachakra")).strip()
    sel = f"dasha_row_id = '{rid}'"
    orig = fs.psql(db_d, f"SELECT {col} FROM chart_dashas WHERE {sel}").strip()
    try:
        fs.psql(db_d, f"UPDATE chart_dashas SET {col} = '{bad}' WHERE {sel}")
        got = _m_d(db_d, monkeypatch, only=[("chart_dashas", col)])
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
        assert all(got[c]["v"] == NO_DET for c in CELLS[1:])
    finally:
        fs.psql(db_d, f"UPDATE chart_dashas SET {col} = '{orig}' WHERE {sel}")
    assert _m_d(db_d, monkeypatch, only=[("chart_dashas", col)])["Narr.agree"]["v"] == NA


@pytest.mark.parametrize("bad_ref,why", [
    ("Jupiter rules this dasha because it is exalted in the tenth house", "matches none of the 14 declared template"),
    ("chart_dashas.vimshottari.L5.Sun@chart={c}:ay=raman:eng=pyjhora_adapter/0.1.0", "matches none of the 14 declared template"),
    ("chart_dashas.vimshottari.L1.Sun@chart={c}:ay=lahiri:eng=pyjhora_adapter/0.1.0", "matches none of the 14 declared template"),
    ("chart_dashas.vimshottari.L1.Sun@chart=11111111-2222-4333-8444-555555555555:ay=raman:eng=pyjhora_adapter/0.1.0", "another chart's id"),
])
def test_REAL_WRITER_MUTATION_a_pointer_that_is_not_an_instance_of_a_template_or_names_another_chart_is_a_FAIL(db_d, monkeypatch, bad_ref, why):
    ref = bad_ref.replace("{c}", CHART_A)
    rid = fs.psql(db_d, f"SELECT dasha_row_id FROM chart_dashas WHERE chart_id = '{CHART_A}' AND system_id = 'yogini' ORDER BY dasha_row_id LIMIT 1").strip()
    sel = f"dasha_row_id = '{rid}'"
    orig = fs.psql(db_d, f"SELECT citation_ref FROM chart_dashas WHERE {sel}").strip()
    try:
        fs.psql(db_d, f"UPDATE chart_dashas SET citation_ref = '{ref}' WHERE {sel}")
        got = _m_d(db_d, monkeypatch, only=[("chart_dashas", "citation_ref")])
        assert got["Narr.agree"]["v"] == FAIL and why in got["Narr.agree"]["measured"] and "(templated)" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db_d, f"UPDATE chart_dashas SET citation_ref = '{orig}' WHERE {sel}")
    assert _m_d(db_d, monkeypatch, only=[("chart_dashas", "citation_ref")])["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_a_sentence_in_a_json_leaf_an_array_element_or_the_sentinel_fact_is_a_FAIL(db_d, monkeypatch):
    rid = fs.psql(db_d, f"SELECT dasha_row_id FROM chart_dashas WHERE chart_id = '{CHART_A}' AND concurrent_system_lords_jsonb IS NOT NULL ORDER BY dasha_row_id LIMIT 1").strip()
    sel = f"dasha_row_id = '{rid}'"
    orig = fs.psql(db_d, f"SELECT concurrent_system_lords_jsonb::text FROM chart_dashas WHERE {sel}").strip()
    try:
        fs.psql(db_d, f"""UPDATE chart_dashas SET concurrent_system_lords_jsonb = '{{"yogini": "Mangala reigns because the Moon is strong"}}'::jsonb WHERE {sel}""")
        got = _m_d(db_d, monkeypatch, only=[("chart_dashas", "concurrent_system_lords_jsonb")])
        assert got["Narr.agree"]["v"] == FAIL and "concurrent_system_lords_jsonb" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db_d, f"UPDATE chart_dashas SET concurrent_system_lords_jsonb = '{orig}'::jsonb WHERE {sel}")
    rid2 = fs.psql(db_d, f"SELECT dasha_row_id FROM chart_dashas WHERE chart_id = '{CHART_A}' AND karakas_active_during_period IS NOT NULL ORDER BY dasha_row_id LIMIT 1").strip()
    sel2 = f"dasha_row_id = '{rid2}'"
    orig2 = fs.psql(db_d, f"SELECT karakas_active_during_period::text FROM chart_dashas WHERE {sel2}").strip()
    try:
        fs.psql(db_d, f"UPDATE chart_dashas SET karakas_active_during_period = ARRAY['Ketu:PK'] WHERE {sel2}")
        assert _m_d(db_d, monkeypatch, only=[("chart_dashas", "karakas_active_during_period")])["Narr.agree"]["v"] == FAIL
    finally:
        fs.psql(db_d, f"UPDATE chart_dashas SET karakas_active_during_period = '{orig2}'::text[] WHERE {sel2}")
    try:
        fs.psql(db_d, "UPDATE chart_facts SET citation_human = 'Prana Dasha will begin in a difficult year.' WHERE fact_category = 'dasha_scope_cap'")
        got = _m_d(db_d, monkeypatch, only=[("chart_facts", "citation_human")])
        assert got["Narr.agree"]["v"] == FAIL and "chart_facts.citation_human" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db_d, "UPDATE chart_facts SET citation_human = 'Prana Dasha fifth-level sub-period is explicitly not computed; the admitted L1 interval hierarchy ends at level 4.' WHERE fact_category = 'dasha_scope_cap'")
    assert _m_d(db_d, monkeypatch, only=[("chart_dashas", "concurrent_system_lords_jsonb"), ("chart_dashas", "karakas_active_during_period"), ("chart_facts", "citation_human")])["Narr.agree"]["v"] == NA


def test_MUTATION_without_the_forms_the_same_asset_reads_open_columns_and_the_old_scope_never_saw_the_copy(db_d, monkeypatch):
    """The two gaps this branch closes, in one assertion each."""
    units, _b = ac.writer_scan_scope(AID, ac.registered_ids("")[AID])
    written = ac.written_columns(units, ["chart_dashas", "chart_facts"])
    assert {"lord_graha", "citation_ref", "system_id", "kp_sublevel"} <= written["chart_dashas"]                  # COPY chart_dashas (...) FROM STDIN is a write the scan reads now
    assert ac._COPY_COLS.search("COPY chart_dashas (a, b) FROM STDIN") and not ac._COPY_COLS.search("COPY (SELECT 1) TO STDOUT")
    assert ac.written_columns(_units_of("cur.execute('COPY t FROM STDIN')"), ["t"]) is None                          # a COPY with no column list cannot be read: unknown, never a guess
    d = {k: v for k, v in DECLS[AID].items()}
    d["prose_none"] = {k: v for k, v in DECLS[AID]["prose_none"].items() if k != "templated_columns"}
    got = _m_d(db_d, monkeypatch, d, only=[("chart_dashas", "citation_ref")])
    assert got["Narr.agree"]["v"] == FAIL and "chart_dashas.citation_ref (text)" in got["Narr.agree"]["measured"]


def _units_of(src):
    tree = ast.parse(src)
    return [dict(rel="w.py", path=pathlib.Path("w.py"), tree=tree, nodes=[tree], hop=0, via="w.py")]


def test_the_scope_note_unwritten_columns_stay_unjudged_but_every_written_text_column_is_declared(db_d):
    """`column_scope: written` is only as strong as the written-columns read: every text-capable column the writer writes into its two tables must be a declared one."""
    units, _b = ac.writer_scan_scope(AID, ac.registered_ids("")[AID])
    written = ac.written_columns(units, ["chart_dashas", "chart_facts"])
    types = {t: dict(r.split("|", 1) for r in fs.psql(db_d, f"SELECT column_name || '|' || data_type FROM information_schema.columns WHERE table_name = '{t}'").splitlines() if r) for t in ("chart_dashas", "chart_facts")}
    pn = DECLS[AID]["prose_none"]
    declared = {(c.get("table") or "chart_dashas", c["column"]) for c in pn["closed_columns"]} | {("chart_dashas", "citation_ref"), ("chart_dashas", "citation_human"), ("chart_facts", "fact_id")}
    text_written = {(t, c) for t, cs in written.items() for c in cs if c in types[t] and ac.prose_none_kind(types[t][c]) is not None}
    assert text_written <= declared, sorted(text_written - declared)
