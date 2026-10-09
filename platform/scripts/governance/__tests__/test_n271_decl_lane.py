"""test_n271_decl_lane.py: the N-271 declaration lane (declarations 1.69.0): what was written, shown true, and what was refused (SS N-271, census b87dafbed, class MISSING DECLARATION).

WRITTEN
  ga_dashas        carriage single_derivation WITH THE EXCEPTION STATED: the Vimshottari rows of levels 1-4 (non-KP) ARE independently re-derived in the build; single-derivation is not claimed for them.
  ga_fact_identity ldgr_source na no_classical_claim: the index states no classical rule or cited fact; the real writer's INSERT carries no citation column; the cell reads the ruled N/A and is red the moment the
                   table gains a citation column.
REFUSED (each pinned so a later edit has to bring the missing form / evidence)
  bg_ephemeris_engine, bg_panchanga   Carr.D1/D2/D3: table-less service probes that carry no value; no truthful carriage nature exists (see test).
  bg_prashna_rules, ga_strength, ga_structural   Ldgr / Vocab.identity: the registry target_table is NULL, the engine reads only that table.
  bo_samvada       Vocab.identity: a view has no declared key. bg_sarvatobhadra_grid: unbuilt. bg_rules: no checked prose form. ga_fact_identity prose: pointer classes missing.
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "python-sidecar"))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

NA, NO_DET, FAIL = ac.NA, ac.NO_DET, ac.FAIL
DECLS = ac.load_asset_declarations()
ROOT = ac.ROOT


def _e(aid):
    return json.loads(json.dumps(DECLS[aid]))


def _validate(aid, e):
    return ac.validate_declarations(dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={aid: e}))


# ───────────────────────── ga_dashas ─────────────────────────

def test_ga_dashas_cells_read_the_ceiling_and_the_why_states_the_exception_first():
    c = DECLS["ga_dashas"]["carriage"]
    assert (c["applies"], c["nature"], c["per_witness_values"]) == ("D3", "single_derivation", False) and "ga_dashas" not in ac._carriage_d3_served_assets()
    got = ac.carriage_declared_checks("ga_dashas", c, "chart_dashas", column_types=None, prose_columns=[], source=DECLS["ga_dashas"]["source"])
    assert [(k, got[k]["v"], got[k]["cause"]) for k in ("Carr.D1", "Carr.D2", "Carr.D3")] == [("Carr.D1", NA, "not-the-declared-carriage"), ("Carr.D2", NA, "no-per-witness-values"), ("Carr.D3", NA, "single-derivation")]
    assert c["why"].startswith("single_derivation applies to every dasha row EXCEPT the Vimshottari rows of levels 1 to 4") and "ARE independently re-derived" in c["why"] and "NOT claimed" in c["why"] and "does not measure" in c["why"]


def test_ga_dashas_anchors_only_vimshottari_has_the_in_build_independent_verifier():
    rel = "platform/python-sidecar/ga_writers/ga_dashas_writer.py"
    src = (ROOT / rel).read_text(encoding="utf-8")
    lines = src.splitlines()
    assert lines[3380].strip() == "_apply_vimshottari_independent_verification(rows, moon_sid, birth_jd)" and DECLS["ga_dashas"]["carriage"]["evidence"].endswith(":3381")
    tree = ast.parse(src)
    calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "_apply_vimshottari_independent_verification"]
    assert len(calls) == 1                                                                                  # one call site: the vimshottari branch
    assert 'if system_id == "vimshottari"' in "\n".join(lines[3340:3381]) or "system_id == \"vimshottari\"" in "\n".join(lines[3300:3381])
    assert "_vimshottari_independent_verifier" in src and "_yogini_independent" not in src and "_ashtottari_independent" not in src


@pytest.mark.parametrize("mutate,msg", [(lambda e: e["carriage"].__setitem__("per_witness_values", True), "per_witness_values"), (lambda e: e["carriage"].__setitem__("spec", {"method": "x"}), "carries no `spec`"),
                                        (lambda e: e["carriage"].__setitem__("applies", "D1"), "requires applies"), (lambda e: e["carriage"].__setitem__("evidence", "platform/no/such_file_n271.py:1"), "evidence")])
def test_FORGERY_ga_dashas_malformed_residual_is_refused(mutate, msg):
    e = _e("ga_dashas")
    mutate(e)
    with pytest.raises(ac.DeclarationsError, match=msg):
        _validate("ga_dashas", e)


def test_FORGERY_if_a_reviewed_d3_method_ever_serves_ga_dashas_the_waiver_is_refused(monkeypatch):
    monkeypatch.setattr(ac, "_carriage_d3_served_assets", lambda: {"ga_dashas": "vimshottari_independent_v1"})
    with pytest.raises(ac.DeclarationsError, match="serves it"):
        _validate("ga_dashas", _e("ga_dashas"))


# ───────────────────────── ga_fact_identity: Ldgr no_classical_claim ─────────────────────────

T = "chart_fact_identity"
LDGR = "Ldgr.source_presence"


def test_the_ldgr_declaration_is_sound_and_not_beside_a_transcription_or_derivation_carriage():
    ls = DECLS["ga_fact_identity"]["ldgr_source"]
    assert ls["na"] == "no_classical_claim" and ls["evidence"].endswith("fact_identity_index.py:38")
    e = _e("ga_fact_identity")
    e["carriage"].update(nature="unverified_transcription", applies="D1")
    with pytest.raises(ac.DeclarationsError):
        _validate("ga_fact_identity", e)                                                                    # the form refuses to sit beside a transcription carriage
    e = _e("ga_fact_identity")
    e["ldgr_source"]["evidence"] = "unverified:somewhere"
    with pytest.raises(ac.DeclarationsError):
        _validate("ga_fact_identity", e)


def test_the_real_writers_insert_carries_no_citation_column():
    src = (ROOT / "platform/python-sidecar/brahmagyan/fact_identity_index.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    sql = next(n.value.value for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "INSERT_SQL" for t in n.targets))
    cols = [c.strip() for c in sql.split("(", 1)[1].split(")", 1)[0].replace("\n", " ").split(",")]
    assert len(cols) == 13 and not (set(cols) & set(ac.CITATION_COLUMNS)), cols
    assert src.splitlines()[37].strip() == "INSERT INTO chart_fact_identity ("


@pytest.fixture()
def fi(disposable_pg, monkeypatch):
    point_psql_at(disposable_pg, monkeypatch)
    for t in (T, "chart_facts"):
        ac.psql(f"DROP TABLE IF EXISTS {t} CASCADE")
    fs.install_chart_facts(disposable_pg)
    ac.psql(fs.create_table_ddl(fs.SMIG / "552_chart_fact_identity.sql", T))
    fs.seed_positions(disposable_pg)
    yield disposable_pg
    for t in (T, "chart_facts"):
        ac.psql(f"DROP TABLE IF EXISTS {t} CASCADE")


def _build(pg):
    psycopg = pytest.importorskip("psycopg")
    from brahmagyan.fact_identity_index import build_index_for_chart
    conn = psycopg.connect(pg.url, autocommit=True)
    try:
        s = build_index_for_chart(conn, fs.CHART_A)
    finally:
        conn.close()
    return s


def _cols(pg):
    return fs.psql(pg, f"SELECT column_name FROM information_schema.columns WHERE table_name = '{T}' ORDER BY ordinal_position").split()


def test_REAL_WRITER_BODY_the_index_built_from_real_chart_facts_reads_the_ruled_na_and_a_citation_column_turns_it_red(fi):
    s = _build(fi)
    assert s["parsed"] > 0
    rec = ac.ldgr_source_declared_check("ga_fact_identity", DECLS["ga_fact_identity"]["ldgr_source"], T, _cols(fi))[LDGR]
    assert rec["v"] == NA and rec["cause"] == "no-classical-claim" and ac._na_released(LDGR, rec), rec
    ac.psql(f"ALTER TABLE {T} ADD COLUMN citation_ref text")                                                 # the table gains a citation column: the claim is contradicted
    rec = ac.ldgr_source_declared_check("ga_fact_identity", DECLS["ga_fact_identity"]["ldgr_source"], T, _cols(fi))[LDGR]
    assert rec["v"] == NO_DET and "citation column" in rec["measured"] and not ac._na_released(LDGR, rec)


def test_unknown_columns_never_release_the_claim_on_a_present_target_table():
    rec = ac.ldgr_source_declared_check("ga_fact_identity", DECLS["ga_fact_identity"]["ldgr_source"], T, None)[LDGR]
    assert rec["v"] == NO_DET and not ac._na_released(LDGR, rec)


# ───────────────────────── REFUSED: pinned ─────────────────────────

@pytest.mark.parametrize("aid", ["bg_ephemeris_engine", "bg_panchanga"])
def test_the_table_less_service_probes_are_not_given_a_carriage_nature_and_why(aid):
    """The probes (service_probes.py) compute a value, compare it to a pinned constant and store NOTHING: no value is carried, so D1 (match to a cited passage), D2 (witnesses of a carried fact) and D3 (re-derive a
    carried value) have nothing to apply to. Every nature the closed vocabulary offers asserts a carried value (transcription / computation / single_derivation) or a ruling (ratified_judgment): declaring one would be
    false. The missing engine form: a `no_table` release for Carr.D1/D2/D3 (add the three Carr criteria to NO_TABLE_CRITERIA with rules Carr.Dn#measured:no-table-no-prose, as the seven checks already released)."""
    e = DECLS[aid]
    assert e["kind"] == "service" and not e["carriage"].get("nature") and e.get("no_table")
    assert set(ac.NO_TABLE_CRITERIA) == {"Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Narr.lint", "Null.schema_default", "Null.blank_rows", "Vocab.identity"}
    src = (ROOT / "platform/python-sidecar/pipeline/orchestrator/service_probes.py").read_text(encoding="utf-8")
    assert "def _probe_ephemeris_engine" in src and "def _probe_panchanga_engine" in src


@pytest.mark.parametrize("aid", ["bg_prashna_rules", "ga_strength", "ga_structural"])
def test_target_less_assets_cannot_be_measured_for_ldgr_by_any_declaration(aid):
    """Registry target_table is NULL (a multi-table / shared chart_facts count_sql); source_declared_check and the Vocab.identity probe read ONLY that table (measure(): `tbl = r["target_table"]`). A row-level
    source for bg_prashna_rules is declared and true (test_n233_carriage_declarations) but cannot be read. Missing: a registry target_table (or an engine form reading the produced slice)."""
    assert DECLS[aid].get("ldgr_source") is None
    src = {"level": "row", "columns": [{"column": "classical_citation", "kinds": ["K1"]}], "citation_state": "sourced", "why": "each row carries a classical citation", "evidence": "platform/scripts/governance/asset_census.py:1"}
    got = ac.source_declared_check(aid, src, None, None)
    assert got[LDGR]["v"] == NO_DET


def test_ga_strength_is_not_declared_no_classical_claim_because_its_rows_state_a_classical_threshold():
    src = (ROOT / "platform/python-sidecar/ga_writers/ga_strength_writer.py").read_text(encoding="utf-8")
    assert "vs required" in src and "required_rupa_for(classical)" in src          # the citation line states the classical required minimum: not a 'no classical claim' asset
