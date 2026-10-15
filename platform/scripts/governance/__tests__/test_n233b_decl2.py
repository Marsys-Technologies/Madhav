"""test_n233b_decl2.py: the N-235 follow-up declarations (declarations 1.65.0) are TRUE and the engine forms bite on them.

  (A) bg_class_priors.code_vocabulary: fact_kind holds the nine standard graha abbreviations (SS N-235 (a)). Real writers on a disposable PostgreSQL build brahma_class_priors; the engine's Vocab value detector reads
      FAIL without the declaration and credits exactly the nine codes with it; forgeries (a tenth code, a case variant, the same codes in another column) stay FAIL.
  (B) bo_pratijna.source: residual UNSOURCED_DECLARED over TWO ledger columns (SS N-235 (3)). The v4 writer binds None to both on every row (AST anchor over every row dict of the writer); the checked label reads
      N/A on all-empty rows and turns red on a single row that names an id in either column.
  (C) the four judgment seeds (ratified_judgment, N-235) now read RULED N/A on Carr.D1/D2/D3 (released by the engine rule), and the release refuses a forged ruling id or nature.
NOT declared (and why) is pinned at the bottom: bo_bimba / bo_karanajala node_subject, bg_nakshatra pada_akshara.
"""
from __future__ import annotations

import ast
import json
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
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

NA, FAIL, PASS, NO_DET = ac.NA, ac.FAIL, ac.PASS, ac.NO_DET
DECLS = ac.load_asset_declarations()
RUN = "11111111-1111-4111-8111-111111111111"
NINE = ["SU", "MO", "MA", "ME", "JU", "VE", "SA", "RA", "KE"]
JUDG = ["bg_class_priors", "bg_class_lifetime_counts", "bg_formula_constants", "bg_ghatana"]


def _own(aid):
    return json.loads(json.dumps(DECLS[aid]))


# ───────────────────────── (C) ratified_judgment is released by the engine rule ─────────────────────────

def _cells(aid, entry=None):
    e = entry or DECLS[aid]
    return ac.carriage_declared_checks(aid, e["carriage"], aid, column_types=None, prose_columns=[], source=e.get("source"))


@pytest.mark.parametrize("aid", JUDG)
def test_the_judgment_seeds_read_ruled_na_on_all_three_carriage_cells(aid):
    got = _cells(aid)
    for k in ("Carr.D1", "Carr.D2", "Carr.D3"):
        assert got[k]["v"] == NA and got[k]["cause"] == "ratified_judgment" and ac._na_released(k, got[k]), (aid, k)
        assert f"{k}#measured:ratified_judgment" in ac.NA_RULE_DECISIONS and "N-235" in ac.NA_RULE_DECISIONS[f"{k}#measured:ratified_judgment"]


@pytest.mark.parametrize("aid", JUDG)
def test_FORGERY_another_ruling_id_or_nature_is_not_released(aid):
    e = _own(aid)
    e["carriage"]["ruling"] = "N-99"
    got = _cells(aid, e)
    assert not any(ac._na_released(k, got[k]) for k in ("Carr.D1", "Carr.D2", "Carr.D3"))             # validates as a declaration, but only N-235 releases the cells
    e = _own(aid)
    e["carriage"]["nature"] = "single_derivation"
    e["carriage"]["applies"] = "D3"
    e["carriage"].pop("ruling")
    got = _cells(aid, e)
    assert got["Carr.D1"]["cause"] != "ratified_judgment" and got["Carr.D3"]["cause"] == "single-derivation"          # the other nature is a different, separately-ruled N/A


# ───────────────────────── (A) bg_class_priors.fact_kind code vocabulary ─────────────────────────

T = "brahma_class_priors"


def test_the_code_vocabulary_declaration_is_sound_and_scoped_to_exactly_one_column():
    cv = DECLS["bg_class_priors"]["code_vocabulary"]
    assert ac.code_vocabulary_problem(DECLS["bg_class_priors"]) is None and cv["class"] == "graha" and cv["columns"] == [{"table": T, "column": "fact_kind"}]
    assert ac.code_columns_of(DECLS["bg_class_priors"]) == {(T, "fact_kind"): frozenset(NINE)}
    assert [a for a, e in DECLS.items() if e.get("code_vocabulary")] == ["bg_class_priors"]


def test_the_codes_the_writer_binds_are_exactly_the_nine_released_codes():
    import brahmagyan.l0_class_priors as P
    codes = {r[0] for r in P.GRAHA_DOMAIN_ROWS}
    assert codes == set(NINE) == set(ac.vocab_code_set())
    src = (ac.ROOT / "platform/python-sidecar/brahmagyan/l0_class_priors.py").read_text(encoding="utf-8")
    assert "VALUES (%s, 'graha_domain', %s, %s, '*', %s, %s, 'W1_SEED_PACKAGE_v1_0')" in src            # the graha code is bound into fact_kind, the domain into source_subsystem


@pytest.fixture(scope="module")
def priors(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    fs.psql(pg, f"DROP TABLE IF EXISTS {T} CASCADE")
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "387_brahma_class_priors.sql", T))
    fs.psql(pg, f"ALTER TABLE {T} ADD COLUMN IF NOT EXISTS prior_basis TEXT, ADD COLUMN IF NOT EXISTS source_ref TEXT")
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_class_priors import ClassPriorsWriter
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    assert ClassPriorsWriter().run(ContextSpec(asset_id="bg_class_priors", build_id=RUN, db_conn=conn, config={})).rows_inserted == 171
    conn.close()
    yield pg
    fs.psql(pg, f"DROP TABLE IF EXISTS {T} CASCADE")


def _detect(pg, mp, entry):
    point_psql_at(pg, mp)
    cols = fs.psql(pg, f"SELECT string_agg(column_name, ',' ORDER BY ordinal_position) FROM information_schema.columns WHERE table_name = '{T}'").strip().split(",")
    types = {c: "text" for c in cols}
    return ac.vocab_value_detect({T: (cols, types)}, None, codes=ac.code_columns_of(entry))


def test_REAL_WRITER_without_the_declaration_the_nine_codes_are_the_census_fail_and_with_it_they_are_credited(priors, monkeypatch):
    bare = _detect(priors, monkeypatch, {})
    assert bare["v"] == FAIL and all(repr(c) in bare["measured"] for c in ("JU", "KE", "MA", "ME", "MO", "RA")), bare["measured"]      # the census' own list (the others are already registered spellings)
    rec = _detect(priors, monkeypatch, DECLS["bg_class_priors"])
    assert rec["v"] != FAIL, rec["measured"]
    assert "fact_kind (graha: short aliases only; registered bg_ontology alias(es), counted canonical: JU, KE, MA, ME, MO, RA)" in rec["measured"]      # credited, and named


@pytest.mark.parametrize("bad", ["AC", "Su", "mo"])      # (a string no vocabulary knows, such as XX, is not a spelling of a graha: the detector does not flag it, and this form does not claim it)
def test_REAL_WRITER_FORGERY_a_tenth_code_or_a_case_variant_in_fact_kind_turns_the_reading_red(priors, monkeypatch, bad):
    fs.psql(priors, f"UPDATE {T} SET fact_kind = '{bad}' WHERE signal_type_class = 'graha_domain' AND fact_kind = 'SU' AND source_subsystem = 'career'")          # fact_kind is a key member: update and restore by it
    try:
        rec = _detect(priors, monkeypatch, DECLS["bg_class_priors"])
        assert rec["v"] == FAIL and f"'{bad}'" in rec["measured"], rec["measured"]
    finally:
        fs.psql(priors, f"UPDATE {T} SET fact_kind = 'SU' WHERE signal_type_class = 'graha_domain' AND fact_kind = '{bad}' AND source_subsystem = 'career'")
    assert _detect(priors, monkeypatch, DECLS["bg_class_priors"])["v"] != FAIL


def test_REAL_WRITER_FORGERY_the_same_codes_in_a_column_that_is_not_declared_are_not_credited(priors, monkeypatch):
    e = _own("bg_class_priors")
    e["code_vocabulary"]["columns"] = [{"table": T, "column": "signal_tradition"}]
    rec = _detect(priors, monkeypatch, e)
    assert rec["v"] == FAIL and all(repr(c) in rec["measured"] for c in ("JU", "KE", "MA", "ME", "MO", "RA"))


# ───────────────────────── (B) bo_pratijna: the label over two ledger columns ─────────────────────────

LDGR = "Ldgr.source_presence"
P = "bodha_pratijna"


def test_the_pratijna_declaration_is_the_residual_over_both_columns():
    s = DECLS["bo_pratijna"]["source"]
    assert ac.source_declaration_problem(s, DECLS["bo_pratijna"], "bo_pratijna") is None
    assert s["residual"] == "UNSOURCED_DECLARED" and s["citation_state"] == "unsourced" and [c["column"] for c in s["columns"]] == ["supporting_signal_ids", "contradicting_signal_ids"]
    assert all(c["kinds"] == ["LEDGER"] and c["resolves_to"] == "bodha_msr_signals.signal_id" for c in s["columns"])


def test_the_v4_writer_binds_none_to_both_columns_in_every_row_it_builds():
    """Anchor in the committed source (AST, nothing run): every dict display that has a `supporting_signal_ids` key maps BOTH id keys to the constant None; no assignment writes them elsewhere."""
    rel = "platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna.py"
    tree = ast.parse((ac.ROOT / rel).read_text(encoding="utf-8"))
    rows = [n for n in ast.walk(tree) if isinstance(n, ast.Dict) and any(isinstance(k, ast.Constant) and k.value == "supporting_signal_ids" for k in n.keys)]
    assert len(rows) >= 2
    for n in rows:
        for key in ("supporting_signal_ids", "contradicting_signal_ids"):
            v = next(v for k, v in zip(n.keys, n.values) if isinstance(k, ast.Constant) and k.value == key)
            assert isinstance(v, ast.Constant) and v.value is None, (key, n.lineno)
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Subscript) and isinstance(n.ctx, ast.Store) and isinstance(n.slice, ast.Constant) and n.slice.value in ("supporting_signal_ids", "contradicting_signal_ids")]
    assert writes == []
    assert (ac.ROOT / rel).read_text(encoding="utf-8").splitlines()[371].strip() == '"supporting_signal_ids": None,' and DECLS["bo_pratijna"]["source"]["evidence"].endswith(":372")


@pytest.fixture()
def pratijna(disposable_pg, monkeypatch):
    point_psql_at(disposable_pg, monkeypatch)
    for t in (P, "bodha_msr_signals", "chart_facts", "brahma_event_ontology"):
        ac.psql(f"DROP TABLE IF EXISTS {t} CASCADE")
    ac.psql("CREATE TABLE brahma_event_ontology (event_class_id text PRIMARY KEY)")                  # the FK target of the real DDL
    ac.psql("INSERT INTO brahma_event_ontology SELECT 'ev' || g FROM generate_series(0, 9) g")
    ac.psql("CREATE TABLE chart_facts (fact_id text)")
    ac.psql("CREATE TABLE bodha_msr_signals (signal_id uuid, constituent_facts_array text[])")
    ac.psql(fs.create_table_ddl(fs.SMIG / "391_bodha_pratijna.sql", P))
    yield disposable_pg
    for t in (P, "bodha_msr_signals", "chart_facts", "brahma_event_ontology"):
        ac.psql(f"DROP TABLE IF EXISTS {t} CASCADE")


def _insert(n, supporting="NULL", contradicting="NULL"):
    for i in range(n):
        ac.psql(f"INSERT INTO {P} (chart_id, ayanamsha_id, event_class_id, status, supporting_signal_ids, contradicting_signal_ids) VALUES "
                f"('482012f1-710e-4a25-994a-93821f5871aa', 'lahiri_chitrapaksha', 'ev{i}', 'promised', {supporting}, {contradicting})")


def _check(pg):
    cols = fs.psql(pg, f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' ORDER BY ordinal_position").split()
    return ac.source_declared_check("bo_pratijna", DECLS["bo_pratijna"]["source"], P, cols, keys=[["chart_id", "ayanamsha_id", "event_class_id"]])[LDGR]


def test_REAL_SQL_rows_shaped_as_the_writer_writes_them_earn_the_label(pratijna):
    _insert(4)
    rec = _check(pratijna)
    assert rec["v"] == NA and rec["cause"] == "unsourced-declared", rec
    assert rec["unsourced_declared"]["checked"] is True and rec["unsourced_declared"]["verified"] is True and rec["unsourced_declared"]["source_columns"] == ["supporting_signal_ids", "contradicting_signal_ids"]
    assert ac._check_contribution(LDGR, "L2", rec, None)["v"] == NA and ac._na_released(LDGR, rec)
    ac.psql(f"UPDATE {P} SET supporting_signal_ids = '{{}}'")                                      # the column default (an empty array) also lacks a source
    assert _check(pratijna)["v"] == NA


@pytest.mark.parametrize("which", ["supporting_signal_ids", "contradicting_signal_ids"])
def test_REAL_SQL_MUTATION_one_row_naming_an_id_in_either_column_turns_the_label_red(pratijna, which):
    _insert(4)
    ac.psql(f"UPDATE {P} SET {which} = ARRAY['3f2b6d0e-1111-4222-8333-444455556666']::uuid[] WHERE event_class_id = 'ev2'")
    rec = _check(pratijna)
    assert rec["v"] in (FAIL, NO_DET) and rec["v"] != NA and "CONTRADICTED" in rec["measured"] and not ac._na_released(LDGR, rec), rec["measured"]


def test_REAL_SQL_an_empty_table_is_vacuous_not_the_label(pratijna):
    rec = _check(pratijna)
    assert rec["v"] == NO_DET and rec["v"] != NA


# ───────────────────────── what is NOT declared, pinned ─────────────────────────

def test_the_node_subject_and_pada_akshara_codes_are_not_declared_because_the_writers_do_not_show_them_to_be_graha_codes():
    """bo_bimba's graha nodes bind node_subject from KNOWN_GRAHAS = the nine FULL names (Sun ... Ketu); no writer source binds a two-letter code to bodha_cgm_nodes.node_subject, so the census' 'JU' 'MA' ... in
    that column are not shown to come from the code that builds it (stale rows from an older build, or another writer): an Exec / data finding, not a declaration. bg_nakshatra's pada_akshara holds naming syllables
    ('Ju', 'Ke', 'Ma' ...), not graha codes: N-235 (a) names bg_class_priors.fact_kind only."""
    bim = (ac.ROOT / "platform/python-sidecar/pipeline/orchestrator/writers/bo_bimba.py").read_text(encoding="utf-8")
    assert '"Sun", "Moon", "Mars", "Mercury", "Jupiter",' in bim and '"node_subject": graha,' in bim
    for aid in ("bo_bimba", "bo_karanajala", "bg_nakshatra"):
        assert not DECLS[aid].get("code_vocabulary"), aid
    import brahmagyan.l0_nakshatra as N
    aks = {p["pada_akshara"] for p in N.PADAS}
    assert {"Ju", "Ke", "Ma", "Me", "Mo", "Ra"} <= aks and not (aks & set(ac.vocab_code_set()))      # mixed-case naming syllables of the nakshatra padas: none is a released graha code


# ───────────────────────── ga_fact_identity: carriage (it has a registered writer since migration 1333) ─────────────────────────

def test_ga_fact_identity_declares_single_derivation_and_the_cells_read_the_ceiling():
    c = DECLS["ga_fact_identity"]["carriage"]
    assert (c["applies"], c["nature"], c["per_witness_values"]) == ("D3", "single_derivation", False) and "ga_fact_identity" not in ac._carriage_d3_served_assets()
    got = _cells("ga_fact_identity")
    assert [(k, got[k]["v"], got[k]["cause"]) for k in ("Carr.D1", "Carr.D2", "Carr.D3")] == [("Carr.D1", NA, "not-the-declared-carriage"), ("Carr.D2", NA, "no-per-witness-values"), ("Carr.D3", NA, "single-derivation")]


def test_ga_fact_identity_anchors_every_row_is_one_classify_fact_result_over_one_chart_facts_row():
    rel = "platform/python-sidecar/brahmagyan/fact_identity_index.py"
    src = (ac.ROOT / rel).read_text(encoding="utf-8")
    lines = src.splitlines()
    assert lines[89].strip() == "kind, payload = classify_fact(fact_category, fact_subject, fact_key)" and DECLS["ga_fact_identity"]["carriage"]["evidence"].endswith("fact_identity_index.py:90")
    tree = ast.parse(src)
    mods = {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module} | {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not ({"swisseph", "jhora", "pyjhora"} & mods), mods                                                 # no sky route to re-derive from: the only input is chart_facts text
    assert "FROM chart_facts WHERE chart_id" in src


def test_FORGERY_ga_fact_identity_cannot_declare_the_residual_if_a_method_serves_it_or_with_a_witness_claim(monkeypatch):
    e = _own("ga_fact_identity")
    with pytest.raises(ac.DeclarationsError, match="per_witness_values"):
        e["carriage"]["per_witness_values"] = True
        ac.validate_declarations(dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={"ga_fact_identity": e}))
    e = _own("ga_fact_identity")
    monkeypatch.setattr(ac, "_carriage_d3_served_assets", lambda: {"ga_fact_identity": "swisseph_sidereal_positions_v1"})
    with pytest.raises(ac.DeclarationsError, match="serves it"):
        ac.validate_declarations(dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={"ga_fact_identity": e}))
