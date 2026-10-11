"""test_n286_corpus.py: SS N-286, constant curated content is acceptable ONLY as a declared curated corpus (declarations 1.72.0).

bo_cgm_motifs writes two fixed DEFINITIONS of a motif class ('Mutual reception (Parivartana): ...', 'Mutual aspect (paraspara drishti): ...'); bo_cdlm_summary writes one fixed PROVENANCE label ('CDLM chart summary
aggregated from bodha_cdlm_cells by bo_sangati'). Each is declared as a `curated_corpus` (CONTAINED mode: the table also holds composed rows) whose pin is the sha256 digest of the exact literal set the ENGINE READS
FROM THE WRITER SOURCE (never typed), plus a `constant_write` waiver pinned to the number of findings the writer scan reports. The new seed form `{file, functions, key}` (prose_forms) reads the plain string literals a
named writer function assigns to a dict key, by AST. Anything else the scan finds, any drifted literal, any extra literal, an unresolved path: the cap stays or the cell reads red.
The real writers' `_write_aya` run on a throw-away PostgreSQL (real DDL of the written tables, stub read tables with the columns the writer reads), the engine's `_measure_prose` reads the cells.
NOT declared (and why) is pinned at the bottom: bo_pratijna, bo_chart_gestalt (JSON-leaf literals; absence reasons), (bg_remedies WAS here as an unresolved DB-derived write path; the scan now follows it and the prescription waiver is declared, SS N-431 / N-450, tested at the bottom).
"""
from __future__ import annotations

import ast
import collections
import copy
import json
import pathlib
import re
import shutil
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import prose_forms as pf  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET, PARTIAL, PASS  # noqa: E402

DECLS = ac.load_asset_declarations()
W = "platform/python-sidecar/pipeline/orchestrator/writers/"
CGM, CDLM = "bo_cgm_motifs", "bo_cdlm_summary"
RECEPTION = "Mutual reception (Parivartana): two grahas ruling each other's signs, exchanging strength and domain influence"
ASPECT = "Mutual aspect (paraspara drishti): two grahas casting drishti on one another, reinforcing their combined influence"
SUMMARY = "CDLM chart summary aggregated from bodha_cdlm_cells by bo_sangati"
RUN = "11111111-1111-4111-8111-111111111111"
def _mig_count_sql():
    """The registry count_sql of bo_cdlm_summary exactly as migration 1297 sets it (read from the migration, not typed here)."""
    t = (fs.REPO / "platform/migrations/1297_bo_cdlm_summary_count_sql_three_tables.sql").read_text(encoding="utf-8")
    return re.search(r"SET count_sql = \$cs\$(.*?)\$cs\$", t, re.S).group(1)


# bo_cdlm_summary: the live count_sql (migration 1297, the `WITH p AS (SELECT $1::uuid AS cid)` three-table form). bo_cgm_motifs: the same three-table form over its three tables (a registry value this PR does NOT set:
# with the seed's one-table count the subgraph_label entry's table is not counted and the Null cells stay capped; see the report).
COUNT_SQL = {CDLM: _mig_count_sql(),
             CGM: "WITH p AS (SELECT $1::uuid AS cid) SELECT (SELECT count(*) FROM bodha_cgm_motifs m, p WHERE m.chart_id = p.cid) + (SELECT count(*) FROM bodha_cgm_sub_graphs g, p WHERE g.chart_id = p.cid) + (SELECT count(*) FROM bodha_cgm_chart_topology_summary t, p WHERE t.chart_id = p.cid) AS count"}


def _own(aid):
    return json.loads(json.dumps(DECLS[aid]))


def _cc(aid):
    return DECLS[aid]["curated_corpus"][0]


# ───────────────────────── the seed form ─────────────────────────

def test_the_function_seed_reads_exactly_the_plain_literals_and_skips_composed_values():
    assert pf.resolve_seed_sentences(fs.REPO, _cc(CGM)["seed"]) == [RECEPTION, ASPECT]
    assert pf.resolve_seed_sentences(fs.REPO, _cc(CDLM)["seed"]) == [SUMMARY]
    # the other citation_human values of the same writers are composed (f-strings / calls): none is in the seed
    for fname in ("bo_cgm_motifs.py", "bo_cdlm_summary.py"):
        tree = ast.parse((fs.REPO / W / fname).read_text(encoding="utf-8"))
        plain, composed = [], []
        for n in ast.walk(tree):
            if isinstance(n, ast.Dict):
                for k, v in zip(n.keys, n.values):
                    if isinstance(k, ast.Constant) and k.value == "citation_human":
                        (plain if isinstance(v, ast.Constant) else composed).append(v)
        assert len(plain) == (2 if fname == "bo_cgm_motifs.py" else 1) and composed, fname                     # an independent count: 2 / 1 plain constants, the rest composed


def test_the_seed_shape_is_strict(tmp_path):
    ok = dict(file=W + "bo_cdlm_summary.py", functions=["_write_aya"], key="citation_human")
    assert pf.seed_shape_problem(ok) is None
    for bad in (dict(ok, extra=1), dict(ok, functions=[]), dict(ok, functions=["a b"]), dict(ok, key="a b"), dict(ok, file="../outside.py"), dict(ok, functions=["x"] * 2), dict(file=ok["file"], functions=ok["functions"])):
        assert pf.seed_shape_problem(bad), bad
    with pytest.raises(ValueError, match="not defined"):
        pf.resolve_seed_sentences(fs.REPO, dict(ok, functions=["no_such_function_n286"]))


def test_the_declarations_are_sound_pinned_by_the_engines_own_reading_and_tight():
    for aid, want in ((CGM, [RECEPTION, ASPECT]), (CDLM, [SUMMARY])):
        e = DECLS[aid]
        assert ac.curated_corpus_problem(e) is None and len(e["curated_corpus"]) == 1
        c = e["curated_corpus"][0]
        assert c["mode"] == "contained" and c["count"] == len(want) and c["digest"] == pf.corpus_digest(want)
        assert c["waiver"] == {"files": [c["seed"]["file"].rsplit("/", 1)[1]], "covers": ["constant_write"], "pin": {"constant_write": len(want)}}
        assert set(c["seed"]) == {"file", "functions", "key"} and c["seed"]["key"] == "citation_human"               # no wildcard: named functions, one key
        assert e["prose_fields"] and "citation_human" in e["prose_fields"]                                             # the column stays declared prose: only the constants are curated


# ───────────────────────── the real writers ─────────────────────────

NODE = [("graha", s) for s in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")]


def _uuid(n):
    return f"00000000-0000-4000-8000-{n:012d}"


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    mig = fs.MIG / "325_l2_bodha_enriched_schema.sql"
    written = ["bodha_cgm_motifs", "bodha_cgm_sub_graphs", "bodha_cgm_chart_topology_summary", "bodha_cdlm_chart_summary"]
    reads = ["bodha_cgm_nodes", "bodha_cgm_edges", "bodha_cdlm_cells"]
    for t in written + reads:
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.psql(pg, "DROP DOMAIN IF EXISTS vector CASCADE")
    fs.psql(pg, "CREATE DOMAIN vector AS bytea")                                  # stands in for pgvector (a non-text type): some of the real DDL columns are vectors
    import re
    for t in written:
        fs.psql(pg, re.sub(r"vector\(\d+\)", "vector", fs.create_table_ddl(mig, t), flags=re.I))
    # the READ tables are stubs with exactly the columns the two writers select (the real DDL has ~40 further columns the writers never read)
    fs.psql(pg, "CREATE TABLE bodha_cgm_nodes (node_id uuid, chart_id uuid, ayanamsha_id text, snapshot_type text, node_type text, node_subject text, node_label_human text, position_in_chart_jsonb jsonb, strength_score numeric)")
    fs.psql(pg, "CREATE TABLE bodha_cgm_edges (edge_id uuid, chart_id uuid, ayanamsha_id text, snapshot_type text, from_node_id uuid, to_node_id uuid, edge_type text, relationship_basis text, computed_strength numeric)")
    fs.psql(pg, "CREATE TABLE bodha_cdlm_cells (chart_id uuid, ayanamsha_id text, snapshot_type text, domain_row text, domain_col text, computed_linkage_strength numeric, asymmetry_score numeric, asymmetric_linkage_flag boolean)")
    for i, (typ, sub) in enumerate(NODE, start=1):
        fs.psql(pg, f"INSERT INTO bodha_cgm_nodes VALUES ('{_uuid(i)}', '{fs.CHART_A}', 'lahiri_chitrapaksha', 'static_natal', '{typ}', '{sub}', '{sub}', NULL, 0.5)")
    e = 0

    def edge(a, b, typ, basis=None):
        nonlocal e
        e += 1
        fs.psql(pg, f"INSERT INTO bodha_cgm_edges VALUES ('{_uuid(1000 + e)}', '{fs.CHART_A}', 'lahiri_chitrapaksha', 'static_natal', '{_uuid(a)}', '{_uuid(b)}', '{typ}', {'NULL' if basis is None else repr(basis)}, 0.5)")
    edge(1, 2, "aspect"); edge(2, 1, "aspect")                                  # Sun <-> Moon: a mutual aspect
    edge(3, 4, "dispositor"); edge(4, 3, "dispositor")                          # Mars <-> Mercury: a mutual reception
    for d1, d2 in (("Career", "Wealth"), ("Wealth", "Health"), ("Career", "Health")):
        fs.psql(pg, f"INSERT INTO bodha_cdlm_cells VALUES ('{fs.CHART_A}', 'lahiri_chitrapaksha', 'static_natal', '{d1}', '{d2}', 0.4, 0.1, false)")
    import pipeline.orchestrator.writers.bo_cgm_motifs as M
    import pipeline.orchestrator.writers.bo_cdlm_summary as S
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    mo, sg, tp = M._write_aya(conn, fs.CHART_A, "lahiri_chitrapaksha", RUN, "2026-10-09T00:00:00+00:00")
    sm = S._write_aya(conn, fs.CHART_A, "lahiri_chitrapaksha", RUN, "2026-10-09T00:00:00+00:00")
    conn.close()
    assert mo >= 2 and sm == 1, (mo, sm)
    yield pg
    for t in written + reads:
        fs.psql(pg, f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.psql(pg, "DROP DOMAIN IF EXISTS vector CASCADE")


def _m(db, mp, aid, decl=None, scoped=True):
    t = "bodha_cgm_motifs" if aid == CGM else "bodha_cdlm_chart_summary"
    tables = [t, "bodha_cgm_sub_graphs", "bodha_cgm_chart_topology_summary"] if aid == CGM else [t]
    scope = {x: dict(where=f"chart_id = '{fs.CHART_A}'", label="measured chart") for x in tables} if scoped else None      # what the census installs for a chart-scoped table
    return fs.measure(aid, db, mp, ac.registered_ids("")[aid], t, tables, decl or _own(aid), scope=scope, registry=dict(has_writer=True, count_sql=COUNT_SQL[aid]))


def test_REAL_WRITER_the_pinned_literals_are_in_the_tables_the_writer_built(db):
    rows = set(fs.psql(db, "SELECT citation_human FROM bodha_cgm_motifs").split("\n"))
    assert {RECEPTION, ASPECT} <= rows and any(r.startswith("CGM structural motif") or "Mutual" in r for r in rows)
    assert fs.psql(db, "SELECT citation_human FROM bodha_cdlm_chart_summary").strip() == SUMMARY


@pytest.mark.parametrize("aid", [CGM, CDLM])
def test_REAL_WRITER_the_corpus_verifies_the_waiver_matches_the_scan_and_the_null_cells_read_pass(db, monkeypatch, aid):
    got = _m(db, monkeypatch, aid)
    assert got["Narr.agree"]["v"] != FAIL, got["Narr.agree"]["measured"][:500]
    for c in ("Null.schema_default", "Null.blank_rows"):
        assert got[c]["v"] == PASS, (aid, c, got[c]["measured"][-500:])                                          # the two cells are earned PASS (the writer scan is clean once the pinned constants are waived)
        cc = got[c]["writer_scan"]["curated_corpus"]
        assert len(cc) == 1 and cc[0]["verified"] is True and cc[0]["mode"] == "contained" and cc[0]["digest"] == _cc(aid)["digest"] and cc[0]["pin"] == {"constant_write": _cc(aid)["count"]} and cc[0]["waived"] == cc[0]["pin"]


@pytest.mark.parametrize("aid", [CGM, CDLM])
def test_REAL_WRITER_without_the_declaration_the_null_cells_keep_the_scan_findings(db, monkeypatch, aid):
    d = _own(aid)
    d.pop("curated_corpus")
    got = _m(db, monkeypatch, aid, d)
    for c in ("Null.schema_default", "Null.blank_rows"):
        assert got[c]["v"] == PARTIAL and "constant_write" in got[c]["measured"], (aid, c, got[c]["measured"][-300:])


# ───────────────────────── forgeries ─────────────────────────

def _copy_writer_tree(tmp_path, monkeypatch, fname, edit):
    """A copy of the repository's governance view in which the writer source is edited: the engine's ROOT is pointed at it (seed, scan and digest all read the copy)."""
    root = tmp_path / "repo"
    for rel in ("platform/python-sidecar/pipeline/orchestrator/writers", "platform/python-sidecar/bodha_writers", "platform/python-sidecar/brahmagyan"):
        shutil.copytree(fs.REPO / rel, root / rel, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    p = root / W / fname
    src = p.read_text(encoding="utf-8")
    new = edit(src)
    assert new != src
    p.write_text(new, encoding="utf-8")
    return root, p


@pytest.mark.parametrize("aid,fname,old,new", [
    (CGM, "bo_cgm_motifs.py", '"signs, exchanging strength and domain influence"', '"signs, exchanging strength and domain influences"'),                 # one character
    (CGM, "bo_cgm_motifs.py", '"another, reinforcing their combined influence"', '"another, reinforcing their combined influence."'),
    (CDLM, "bo_cdlm_summary.py", '"CDLM chart summary aggregated from bodha_cdlm_cells by bo_sangati"', '"CDLM chart summary aggregated from bodha_cdlm_cells by bo_sangati."'),
])
def test_FORGERY_one_edited_character_of_a_pinned_literal_makes_the_seed_miss_the_pin(tmp_path, aid, fname, old, new):
    root, _ = _copy_writer_tree(tmp_path, None, fname, lambda s: s.replace(old, new, 1))
    sents = pf.resolve_seed_sentences(root, _cc(aid)["seed"])
    assert pf.corpus_digest(sents) != _cc(aid)["digest"]                                                          # the engine's seed no longer digests to the pin ...
    g = ac.grade_curated(_cc(aid), dict(sentences=list(sents)), sents, None)
    assert g["state"] == "wrong" and "digesting to" in g["text"]                                                 # ... and the grade is WRONG, which makes Narr.agree FAIL


def test_FORGERY_a_new_constant_literal_in_the_named_function_changes_the_seed(tmp_path):
    def add(s):
        return s.replace('            "citation_human": (\n                "Mutual aspect (paraspara drishti)', '            "citation_human_x": "ignored",\n            "citation_human": (\n                "Mutual aspect (paraspara drishti)', 1) if False else s.replace(
            '    # triangles: three nodes pairwise in mutual aspect.', '    motifs.append({"motif_class": "z", "citation_human": "A brand new constant sentence about a motif class"})\n    # triangles: three nodes pairwise in mutual aspect.', 1)
    root, _ = _copy_writer_tree(tmp_path, None, "bo_cgm_motifs.py", add)
    sents = pf.resolve_seed_sentences(root, _cc(CGM)["seed"])
    assert len(sents) == 3 and pf.corpus_digest(sents) != _cc(CGM)["digest"] and ac.grade_curated(_cc(CGM), dict(sentences=list(sents)), sents, None)["state"] == "wrong"


@pytest.mark.parametrize("aid", [CGM, CDLM])
def test_REAL_WRITER_FORGERY_a_pin_the_seed_does_not_hold_turns_narr_agree_red(db, monkeypatch, aid):
    """What an edited character or an added constant in the writer does to the cell: the seed (read from the writer) no longer digests to the pin."""
    d = _own(aid)
    d["curated_corpus"][0]["digest"] = "0" * 64
    got = _m(db, monkeypatch, aid, d)
    assert got["Narr.agree"]["v"] == FAIL and "digesting to" in got["Narr.agree"]["measured"] and "citation_human" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    d = _own(aid)
    d["curated_corpus"][0]["count"] += 1
    assert _m(db, monkeypatch, aid, d)["Narr.agree"]["v"] == FAIL


@pytest.mark.parametrize("aid", [CGM, CDLM])
def test_REAL_WRITER_FORGERY_a_waiver_pin_that_is_not_the_number_of_findings_keeps_the_cap(db, monkeypatch, aid):
    """A new constant literal elsewhere in the writer raises the number of scan findings above the pin; the cap stays and says so (simulated by moving the pin by one either way)."""
    for delta in (-1, +1):
        d = _own(aid)
        d["curated_corpus"][0]["waiver"]["pin"]["constant_write"] += delta
        if d["curated_corpus"][0]["waiver"]["pin"]["constant_write"] < 0:
            continue
        got = _m(db, monkeypatch, aid, d)
        for c in ("Null.schema_default", "Null.blank_rows"):
            assert got[c]["v"] == PARTIAL and "declared curated corpus not applied" in got[c]["measured"], (aid, delta, c, got[c]["v"])


def test_REAL_WRITER_FORGERY_a_pinned_definition_edited_in_the_table_is_red(db, monkeypatch):
    fs.psql(db, "UPDATE bodha_cgm_motifs SET citation_human = citation_human || ' (edited later)' WHERE citation_human LIKE 'Mutual aspect%'")
    try:
        got = _m(db, monkeypatch, CGM)
        assert got["Narr.agree"]["v"] == FAIL and "pinned definition's lead" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    finally:
        fs.psql(db, "UPDATE bodha_cgm_motifs SET citation_human = replace(citation_human, ' (edited later)', '')")
    assert _m(db, monkeypatch, CGM)["Narr.agree"]["v"] != FAIL


def test_the_one_table_seed_count_sql_leaves_bo_cgm_motifs_capped_and_says_why(db, monkeypatch):
    """With the seed's one-table count_sql the subgraph_label entry's table is not counted: the scope is an upper bound, the Null cells are not CLEAN, the lift is not taken. Honest, not green."""
    t = "bodha_cgm_motifs"
    got = fs.measure(CGM, db, monkeypatch, ac.registered_ids("")[CGM], t, [t, "bodha_cgm_sub_graphs", "bodha_cgm_chart_topology_summary"], _own(CGM), registry=dict(has_writer=True, count_sql=f"SELECT count(*) FROM {t} WHERE chart_id = $1"))
    assert got["Null.blank_rows"]["v"] == PARTIAL and "upper bound" in got["Narr.checkable"]["measured"]


def test_FORGERY_an_absence_stand_in_cannot_be_declared_as_a_corpus():
    """The corpus entry's column must be an identifier: the JSON-leaf stand-ins (bo_pratijna denial reasons, bo_chart_gestalt notes) cannot even be named, and they are not declared."""
    e = copy.deepcopy(DECLS["bo_pratijna"])
    e["curated_corpus"] = [dict(_cc(CDLM), table="bodha_pratijna", column="derivation.$.denials[*].reason")]
    assert ac.curated_corpus_problem(e)
    for aid in ("bo_pratijna", "bo_chart_gestalt"):
        assert not DECLS[aid].get("curated_corpus"), aid


def test_the_same_literal_under_another_key_or_function_is_not_part_of_the_seed(tmp_path):
    p = tmp_path / "w.py"
    p.write_text('def a():\n    return {"citation_human": "Fixed definition of the class", "other": "Not curated here", "citation_human": f"composed {1}"}\n\ndef b():\n    return {"citation_human": "Another function constant"}\n', encoding="utf-8")
    spec = dict(file="platform/python-sidecar/w.py", functions=["a"], key="citation_human")
    root = tmp_path / "r"
    (root / "platform/python-sidecar").mkdir(parents=True)
    shutil.copy(p, root / "platform/python-sidecar/w.py")
    assert pf.resolve_seed_sentences(root, spec) == ["Fixed definition of the class"]                                # `other` and the composed value and function b are not in it


# ───────────────────────── what stays undeclared ─────────────────────────

BGR = "bg_remedies"
BGR_WAIVER_FILES = ["brahmagyan/l0_remedy_corpus.py", "brahmagyan/citation_pass2_remedies.py"]
# Synthetic DATABASE-DERIVED write paths to the declared prose column, the two shapes the scan cannot read as a literal: an INSERT ... SELECT that takes the value from another table's column, and a value
# returned by a callee defined outside the scanned scope.
DB_DERIVED_WRITES = {
    "insert_select": ("def sweep_sql(cur):\n"
                      "    cur.execute(\"INSERT INTO brahma_remedy_corpus (remedy_id, prescription_text) SELECT chunk_id, content_en FROM classical_text_chunks\")\n"),
    "fetched_then_outside_callee": ("def sweep_fetch(cur):\n"
                                    "    cur.execute(\"SELECT chunk_id, content_en FROM classical_text_chunks\")\n"
                                    "    for cid, txt in cur.fetchall():\n"
                                    "        cur.execute(\"INSERT INTO brahma_remedy_corpus (remedy_id, prescription_text) VALUES (%s, %s)\", (cid, mystery_lookup(cid)))\n"),
}


def _bgr_scan_units(extra_src=None):
    """The scope the Null writer scan reads for bg_remedies (the census's own `writer_scan_scope`), plus, when given, one synthetic module (a hop-1 unit) holding an extra write path."""
    files = ac.registered_ids("")[BGR]
    units, beyond = ac._delegation_scope(BGR, files)
    scan_units, scan_beyond = ac.writer_scan_scope(BGR, files)
    scan_units = list(scan_units)
    if extra_src:
        tree = ast.parse(extra_src)
        scan_units.append(dict(rel="brahmagyan/synthetic_db_write.py", path=fs.REPO / "synthetic_db_write.py", tree=tree, nodes=ac._closure([tree], ac._top_defs(tree)), hop=1, via="synthetic"))
    return units, beyond, scan_units, scan_beyond


def _bgr_null_cells(decl, extra_src=None):
    """The REAL `prose_checks` of bg_remedies, with NO database: the live reads are stubbed (no blank among 500 checkable rows; the live prescription / charity tables hold exactly the committed seed
    sentences), so what is graded is the declaration against the writer SOURCE. Returns the prose-check records."""
    tbl = "brahma_remedy_corpus"
    cols = ["remedy_id", "prescription_text", "charity_action", "planet", "domain"]
    units, beyond, scan_units, scan_beyond = _bgr_scan_units(extra_src)
    ctx = dict(table=tbl, own={tbl: (cols, {c: "text" for c in cols}, {})}, tests=[], vocabulary=set(), paths=[u["path"] for u in units], written=ac.written_columns(units, [tbl]), root=str(fs.REPO),
               units=units, beyond=beyond, scan_units=scan_units, scan_beyond=scan_beyond,
               counts={e: dict(blank=0, checkable=500, scope="chart") for e in decl["prose_fields"]})
    reads = {}
    for e in decl["curated_corpus"]:
        sents, err = ac.formgap_seed(e)
        assert not err, err
        reads[(e["table"], e["column"])] = dict(sentences=list(sents), chart_scoped=False)
    ctx["curated_reads"] = reads
    return ac.prose_checks(BGR, decl, ctx)


@pytest.fixture(scope="module")
def bgr_scan():
    """The static writer scan of the declared entries over the real scope, once."""
    decl = _own(BGR)
    units, beyond, scan_units, scan_beyond = _bgr_scan_units()
    cols = ["remedy_id", "prescription_text", "charity_action"]
    own = {"brahma_remedy_corpus": (cols, {c: "text" for c in cols}, {})}
    holders = {ac.parse_prose_field(e)[0]: ac._holders(ac.parse_prose_field(e)[0], own) for e in decl["prose_fields"]}
    return ac._lint_module("writer_literal_scan").scan(scan_units, list(decl["prose_fields"]), holders, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field, beyond=scan_beyond)


# ───────────────────────── bg_remedies: the prescription waiver (SS N-431 / N-450), and what it must never hide ─────────────────────────

def test_bg_remedies_prescription_text_carries_the_exact_waiver_pinned_to_the_scan_counts(bgr_scan):
    """bg_remedies used to stay capped ("172 scan finding(s) outside every declared waiver"). The walk declared the waiver for the 172 hand-typed prescription literals (136 in the committed remedy tables
    + 36 the citation pass 2 overlay writes) beside the existing charity_action one (31). The pin is the engine's own count, per kind over ALL waiver files, and the scan leaves NOTHING unresolved: a waiver
    may only replace literal `constant_write` findings, never a write path the scan could not follow."""
    e = _own(BGR)
    assert [c["column"] for c in e["curated_corpus"]] == ["prescription_text", "charity_action"]
    presc, charity = e["curated_corpus"]
    assert presc["waiver"] == dict(files=BGR_WAIVER_FILES, covers=["constant_write"], pin={"constant_write": 172})
    assert charity["waiver"]["covers"] == ["constant_write"] and charity["waiver"]["pin"] == {"constant_write": 31}
    assert ac.curated_corpus_problem(e) is None
    # the pin is what the scan finds, by column, kind and file: 136 + 36 prescription literals, 31 charity actions, nothing else, nothing unresolved
    got = collections.Counter((ac.parse_prose_field(p["entry"])[0], p["kind"], ac._scan_file_of(p["where"])) for p in bgr_scan["problems"])
    assert got == collections.Counter({("prescription_text", "constant_write", "brahmagyan/l0_remedy_corpus.py"): 136,
                                       ("prescription_text", "constant_write", "brahmagyan/citation_pass2_remedies.py"): 36,
                                       ("charity_action", "constant_write", "brahmagyan/l0_remedy_corpus.py"): 31})
    assert 136 + 36 == presc["waiver"]["pin"]["constant_write"] and {f for (_c, _k, f) in got if _c == "prescription_text"} == set(presc["waiver"]["files"])
    assert bgr_scan["unresolved"] == [], bgr_scan["unresolved"]
    # the database read the old pin named is in the source and is NOT an unresolved path any more: the scan follows `source_row.get("content_en")` as a read, not as a literal
    assert "content_en" in (fs.REPO / "platform/python-sidecar/brahmagyan/l0_remedy_corpus.py").read_text(encoding="utf-8")


def test_bg_remedies_both_null_cells_read_pass_in_the_declared_state():
    got = _bgr_null_cells(_own(BGR))
    for c in ("Null.schema_default", "Null.blank_rows"):
        assert got[c]["v"] == PASS and "PASS earned by the writer scan after the pinned curated corpus replaced 203" in got[c]["measured"], (c, got[c]["measured"][-300:])
        assert [(i["column"], i["files"], i["waived"], i["pin"]) for i in got[c]["writer_scan"]["curated_corpus"]] == [
            ("charity_action", BGR_WAIVER_FILES[:1], {"constant_write": 31}, {"constant_write": 31}),
            ("prescription_text", BGR_WAIVER_FILES, {"constant_write": 172}, {"constant_write": 172})]
    assert got["Narr.agree"]["v"] == PASS


@pytest.mark.parametrize("shape", sorted(DB_DERIVED_WRITES))
def test_FORGERY_a_database_derived_write_path_added_to_the_scan_still_caps_both_null_cells(shape):
    """The meaning the old pin guarded, kept: a waiver must not hide a database-derived write path. A write of the declared column whose value comes from the database (an INSERT ... SELECT of another
    table's column, or the return of a callee outside the scanned scope) is UNRESOLVED to the scan; with the waiver in place the cell stays PARTIAL naming it, and never reads PASS."""
    got = _bgr_null_cells(_own(BGR), DB_DERIVED_WRITES[shape])
    for c in ("Null.schema_default", "Null.blank_rows"):
        assert got[c]["v"] == PARTIAL, (shape, c, got[c]["v"])
        assert "declared curated corpus not applied: the scan left 1 write path(s) unresolved" in got[c]["measured"] and "synthetic_db_write.py" in got[c]["measured"], (shape, c, got[c]["measured"][-400:])
        assert "writer_scan" not in got[c]


def test_FORGERY_the_real_classical_text_sweep_is_inside_the_scan_so_an_opaque_value_there_would_cap_the_cells():
    """The sweep reads `classical_text_chunks.content_en` from the database and writes a slice of it into prescription_text (l0_remedy_corpus.py ~3307). The scan reads it (it is not out of scope):
    replace that one expression with a call the scan cannot follow and the waiver no longer applies."""
    old = "prescription_text = content_en[:400].rsplit(' ', 1)[0] if len(content_en) > 400 else content_en"
    d = _own(BGR)
    units, beyond, scan_units, scan_beyond = _bgr_scan_units()
    patched = []
    for u in scan_units:
        if u["rel"].endswith("brahmagyan/l0_remedy_corpus.py"):
            src = u["path"].read_text(encoding="utf-8")
            assert old in src
            tree = ast.parse(src.replace(old, "prescription_text = mystery_lookup(content_en)"))
            u = dict(u, tree=tree, nodes=ac._closure([tree], ac._top_defs(tree)))
        patched.append(u)
    tbl = "brahma_remedy_corpus"
    cols = ["remedy_id", "prescription_text", "charity_action"]
    reads = {(e["table"], e["column"]): dict(sentences=list(ac.formgap_seed(e)[0]), chart_scoped=False) for e in d["curated_corpus"]}
    ctx = dict(table=tbl, own={tbl: (cols, {c: "text" for c in cols}, {})}, tests=[], vocabulary=set(), paths=[u["path"] for u in units], written=ac.written_columns(units, [tbl]), root=str(fs.REPO),
               units=units, beyond=beyond, scan_units=patched, scan_beyond=scan_beyond, counts={e: dict(blank=0, checkable=500, scope="chart") for e in d["prose_fields"]}, curated_reads=reads)
    got = ac.prose_checks(BGR, d, ctx)
    for c in ("Null.schema_default", "Null.blank_rows"):
        assert got[c]["v"] == PARTIAL and "the scan left 1 write path(s) unresolved" in got[c]["measured"] and "mystery_lookup" in got[c]["measured"], (c, got[c]["measured"][-400:])


def test_FORGERY_a_waiver_that_leaves_the_overlay_file_out_keeps_the_cap():
    d = _own(BGR)
    d["curated_corpus"][0]["waiver"]["files"] = BGR_WAIVER_FILES[:1]
    got = _bgr_null_cells(d)
    for c in ("Null.schema_default", "Null.blank_rows"):
        assert got[c]["v"] == PARTIAL and "36 scan finding(s) are outside every declared waiver" in got[c]["measured"] and "citation_pass2_remedies.py" in got[c]["measured"], (c, got[c]["measured"][-300:])


# ───────────────────────── the two small engine changes this needs ─────────────────────────

def test_the_registry_cte_count_form_of_migration_1297_is_scoped_like_the_plain_sum():
    sql = _mig_count_sql()
    assert ac._count_scope_tail(sql, "bodha_cdlm_chart_summary") == " WHERE chart_id = $1" and ac._count_scope_tail(sql, "bodha_cdlm_pattern_clusters") == " WHERE chart_id = $1"
    assert ac._count_scope_tail(sql, "bodha_cdlm_cells") is None                                                        # a table the sum does not count
    assert ac._chart_scoped(ac._count_scope_cte(sql)) or ac._count_scope_cte(sql).startswith("SELECT (SELECT count(*)")


@pytest.mark.parametrize("edit", [
    lambda q: q.replace("s.chart_id = p.cid", "s.chart_id = p.cid OR true"),                              # a widened predicate
    lambda q: q.replace("s.chart_id = p.cid", "s.chart_id = p.cid AND s.x = 1", 1) + " ",                  # extra conjunct inside a term: not the exact shape
    lambda q: q.replace("$1::uuid AS cid", "$2::uuid AS cid"),                                             # another parameter
    lambda q: q.replace("WITH p AS", "WITH q AS"),                                                         # another CTE name
    lambda q: q.replace(" + (SELECT count(*) FROM bodha_cdlm_domain_rollups r, p WHERE r.chart_id = p.cid)", " + (SELECT count(*) FROM bodha_cdlm_domain_rollups r, p WHERE r.chart_id <> p.cid)"),
    lambda q: q.replace("FROM bodha_cdlm_chart_summary s, p", "FROM bodha_cdlm_chart_summary s JOIN p ON true"),
])
def test_FORGERY_any_deviation_from_the_exact_cte_shape_stays_unparseable(edit):
    q = edit(_mig_count_sql())
    assert q != _mig_count_sql()
    assert ac._count_scope_tail(q, "bodha_cdlm_chart_summary") is None


def test_a_chart_scoped_table_may_be_a_curated_corpus_only_in_contained_mode():
    cols = (["chart_id", "citation_human"], {"chart_id": "uuid", "citation_human": "text"}, None)
    eq = dict(_cc(CDLM), mode="equal")
    assert "refused" in ac.formgap_curated_read(eq, "bodha_cdlm_chart_summary", cols).get("unread", "")
    assert "only `contained` mode" in ac.formgap_curated_read(eq, "bodha_cdlm_chart_summary", cols)["unread"]


# ───────────── N-286 review fixes ─────────────

_PH = ["TBD", "N/A", "Unknown", "Default description", "No data", "Not available for this chart", "tbd.", "  n/a  "]
_ABSENT = ["see doctrine", "lorem ipsum", "FIXME", "XXX", "T.B.D.", "Definition pending.", "(fill in later)", "fill in", "to do", "todo", "n/a.", "N./A", "TBD - to be filled", "Nothing to report", "Placeholder text", "Coming soon", "Not defined", "No information", "See above", "To be determined later", "Mutual reception not found in this chart", "No mutual aspect matched for this chart", "Data unavailable", "The value is not recorded here", "None recorded for this graha",
           "Source never guessed", "Not present in the table", "Definition not available for this chart"]


def _entry(sents, mode):
    return dict(count=len(sents), digest=pf.corpus_digest(sents), mode=mode, seed=dict(file="x.py", key="k"), column="c")


@pytest.mark.parametrize("mode", ["contained", "equal"])
@pytest.mark.parametrize("bad", _PH + _ABSENT)
def test_FORGERY_a_placeholder_or_absence_statement_seed_is_refused_in_both_modes(mode, bad):
    """Review HIGH 1: a pinned seed sentence that is blank, a placeholder, or an absence statement is WRONG even when the digest matches and the table holds the text."""
    good = "Mutual aspect (paraspara drishti): two grahas casting drishti on one another, reinforcing their combined influence"
    sents = [good, bad]
    got = ac.grade_curated(_entry(sents, mode), dict(sentences=list(sents)), seed_sentences=sents)
    assert got["state"] == "wrong" and ac.CURATED_PLACEHOLDER_NEEDLE in got["text"], (mode, bad, got)


@pytest.mark.parametrize("mode", ["contained", "equal"])
def test_the_real_definitions_are_still_accepted_by_the_absence_check(mode):
    sents = [RECEPTION, ASPECT]
    got = ac.grade_curated(_entry(sents, mode), dict(sentences=list(sents)), seed_sentences=sents)
    assert got["state"] == "ok", got
    assert ac.grade_curated(_entry([SUMMARY], mode), dict(sentences=[SUMMARY]), seed_sentences=[SUMMARY])["state"] == "ok"


def test_the_curated_read_of_a_chart_table_is_scoped_to_the_measured_chart_in_the_sql(monkeypatch):
    monkeypatch.setattr(ac, "_scope_pred", lambda t: "chart_id = 'X'")
    assert "chart_id = 'X'" in ac.curated_read_sql("t", "c", 2, None, scoped=True)
    assert "chart_id" not in ac.curated_read_sql("t", "c", 2, None)


@pytest.mark.parametrize("aid, table, probe", [(CDLM, "bodha_cdlm_chart_summary", "CDLM chart summary%"), (CGM, "bodha_cgm_motifs", "Mutual aspect%")])
def test_REAL_WRITER_TWO_CHARTS_another_charts_rows_never_count_for_or_against_the_measured_chart(db, monkeypatch, aid, table, probe):
    """The read is the measured chart's rows only. A definition moved to chart B is simply absent from chart A (not a finding for cgm; nothing verified for cdlm, whose only row it was), while an EDITED definition
    in chart B never turns chart A red."""
    assert _m(db, monkeypatch, aid)["Narr.agree"]["v"] != FAIL
    fs.psql(db, f"UPDATE {table} SET chart_id = '{fs.CHART_B}' WHERE citation_human LIKE '{probe}'")
    try:
        got = _m(db, monkeypatch, aid)
        assert got["Narr.agree"]["v"] != FAIL, got["Narr.agree"]["measured"][:300]
        if aid == CDLM:
            assert got["Null.blank_rows"]["v"] != PASS                                       # no row for the measured chart: nothing verified, never a lift
        fs.psql(db, f"UPDATE {table} SET citation_human = citation_human || ' (b edit)' WHERE chart_id = '{fs.CHART_B}'")
        assert _m(db, monkeypatch, aid)["Narr.agree"]["v"] != FAIL
    finally:
        fs.psql(db, f"UPDATE {table} SET citation_human = replace(citation_human, ' (b edit)', ''), chart_id = '{fs.CHART_A}' WHERE chart_id = '{fs.CHART_B}'")
    assert _m(db, monkeypatch, aid)["Null.blank_rows"]["v"] == PASS


def test_REAL_WRITER_a_chart_with_only_the_aspect_definition_passes_the_reception_definition_is_not_required(db, monkeypatch):
    fs.psql(db, "UPDATE bodha_cgm_motifs SET chart_id = '%s' WHERE citation_human LIKE 'Mutual reception%%'" % fs.CHART_B)
    try:
        got = _m(db, monkeypatch, CGM)
        assert got["Narr.agree"]["v"] != FAIL and got["Null.blank_rows"]["v"] == PASS, (got["Narr.agree"]["measured"][:300], got["Null.blank_rows"]["measured"][-300:])
    finally:
        fs.psql(db, "UPDATE bodha_cgm_motifs SET chart_id = '%s' WHERE chart_id = '%s'" % (fs.CHART_A, fs.CHART_B))


@pytest.mark.parametrize("bad", ["TBD", "N/A", "Lorem ipsum", ""])
def test_REAL_WRITER_a_placeholder_text_in_the_covered_column_is_red(db, monkeypatch, bad):
    fs.psql(db, "UPDATE bodha_cgm_motifs SET citation_human = '%s' WHERE citation_human LIKE 'Mutual reception%%'" % bad)
    try:
        got = _m(db, monkeypatch, CGM)
        assert got["Narr.agree"]["v"] == FAIL and "blank or a placeholder" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:300]
    finally:
        fs.psql(db, "UPDATE bodha_cgm_motifs SET citation_human = '%s' WHERE citation_human = '%s'" % (RECEPTION.replace("'", "''"), bad))


_CH = dict(count=2, digest="d", mode="contained")


def test_PURE_contained_chart_scoped_rule():
    pfm = pf
    want = [RECEPTION, ASPECT]
    ent = dict(_entry(want, "contained"))
    rd = lambda rows: dict(chart_scoped=True, sentences=rows)
    g = lambda rows: ac.grade_curated(ent, rd(rows), seed_sentences=want)
    composed = "CGM structural motif: a mutual aspect triangle of three grahas"
    assert g([ASPECT, composed])["state"] == "ok"                                  # reception absent: not a finding
    assert g([composed])["state"] == "ok"                                          # none of the definitions present: the pin guards the writer
    assert g([ASPECT, RECEPTION + " (edited)"])["state"] == "wrong"
    assert g([ASPECT.replace("reinforcing", "weakening")])["state"] == "wrong"
    assert g([ASPECT, "TBD"])["state"] == "wrong" and g([ASPECT, ""])["state"] == "wrong"
    assert g([])["state"] == "unread"
    # a non-chart-scoped (global) contained read keeps the strict rule
    assert ac.grade_curated(ent, dict(sentences=[ASPECT]), seed_sentences=want)["state"] == "wrong"
