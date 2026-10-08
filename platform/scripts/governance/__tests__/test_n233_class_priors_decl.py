"""test_n233_class_priors_decl.py: the prose declarations of bg_class_priors and bg_class_lifetime_counts agree with their writers and with each other (SS ruling N-233, task T2, declarations 1.62.0).

The final census read Narr.agree FAIL on both (and the other five Narr / Null cells NO_DETECTOR) because the two assets share ONE table, brahma_class_priors, and each was judged on every column of it:
bg_class_priors was told prior_basis was open (a column only the other asset writes), and bg_class_lifetime_counts that citation, prior_basis, prior_version and varga_weights were open (the first three it
writes, the last it does not). The declarations contradicted the shared schema, not the writers.

The fix declares what is true: each asset judges the columns ITS writer writes (`column_scope: written`, the engine's existing form), the lifetime writer's citation / prior_version are declared as the hand-typed
seed text / key they are, and prior_basis, which the table CHECK brahma_class_priors_lifetime_basis_ck confines to the two tier names the seed module declares, is closed to those two names on both assets.

Real writers on a throw-away PostgreSQL with the real DDL (migration 387 + the columns and CHECK of migration 522) and the engine's own `_measure_prose`: the six cells read N/A on both; every claim has a mutation that
must turn the reading red.

NOT fixed here, and why (see N233/DECL_REPORT.md): bg_class_priors Vocab.alias FAIL is VALUE-keyed (fact_kind holds the two-letter graha codes SU / MO / MA ... of the graha x domain rows, which the seed binds
and `bo_laksana` / `priors_config.ts` read by those codes); no declaration can change a value-keyed reading.
"""
from __future__ import annotations

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
from _formgap_support import NA, FAIL, NO_DET, CELLS  # noqa: E402

T = "brahma_class_priors"
PRI, LIFE = "bg_class_priors", "bg_class_lifetime_counts"
DECLS = ac.load_asset_declarations()
RUN = "11111111-1111-4111-8111-111111111111"


def _own(aid):
    return json.loads(json.dumps(DECLS[aid]))


def test_both_declarations_are_sound_judge_the_written_columns_and_close_prior_basis_alike():
    for aid in (PRI, LIFE):
        e = DECLS[aid]
        assert ac.prose_none_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
        assert e["prose_none"]["column_scope"] == "written"
        assert [(c["column"], c.get("table")) for c in e["prose_none"]["closed_columns"]] == [("prior_basis", None)]
    assert DECLS[PRI]["prose_none"]["closed_columns"] == DECLS[LIFE]["prose_none"]["closed_columns"]         # ONE closure on the ONE shared column
    assert "prior_version" in {c["column"] for c in DECLS[LIFE]["prose_none"]["identifier_columns"]} and "citation" in {c["column"] for c in DECLS[LIFE]["prose_none"]["transcription_columns"]}


def test_the_closure_of_prior_basis_is_the_seed_modules_tier_names_and_the_tables_own_check():
    import brahmagyan.l0_class_lifetime_counts as L
    declared = DECLS[LIFE]["prose_none"]["closed_columns"][0]["values"]
    assert sorted(declared) == sorted(L.VALID_PRIOR_BASES) == ["demographic_structural", "derived_identity"]
    sql = (fs.SMIG / "522_brahma_class_lifetime_counts.sql").read_text(encoding="utf-8")
    assert "prior_basis IN ('demographic_structural','derived_identity')" in sql                              # the constraint admits exactly these two on the lifetime rows
    assert all(r.prior_basis in declared for r in L.LIFETIME_COUNT_ROWS)


def test_the_two_writers_write_the_columns_the_declarations_account_for():
    """Independent of the engine: read the INSERT column lists out of the two seed modules' SQL (text, not run)."""
    pri = (HERE.parents[2] / "python-sidecar/brahmagyan/l0_class_priors.py").read_text(encoding="utf-8")
    life = (HERE.parents[2] / "python-sidecar/brahmagyan/l0_class_lifetime_counts.py").read_text(encoding="utf-8")

    def insert_cols(src):
        out = set()
        for m in re.finditer(r"INSERT INTO brahma_class_priors\s*\(([^)]*)\)", src):
            out |= {c.strip() for c in m.group(1).replace("\n", " ").split(",") if c.strip()}
        return out
    pc, lc = insert_cols(pri), insert_cols(life)
    assert "prior_basis" not in pc and "source_ref" not in pc and {"citation", "ratified_by", "varga_weights"} <= pc
    assert {"prior_basis", "source_ref", "citation", "ratified_by", "prior_version"} <= lc and "varga_weights" not in lc
    pn_p = DECLS[PRI]["prose_none"]
    declared_p = {c["column"] for k in ("closed_columns", "transcription_columns", "identifier_columns") for c in pn_p[k]} | {"source_ref"}
    assert {c for c in pc if c not in ("class_prior", "contested")} <= declared_p
    pn_l = DECLS[LIFE]["prose_none"]
    declared_l = {c["column"] for k in ("closed_columns", "transcription_columns", "identifier_columns") for c in pn_l[k]} | {"source_ref"}
    assert {c for c in lc if c not in ("class_prior", "contested")} <= declared_l


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    from psycopg.rows import dict_row
    pg = disposable_pg
    fs.psql(pg, f"DROP TABLE IF EXISTS {T} CASCADE")
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "387_brahma_class_priors.sql", T))
    fs.psql(pg, f"ALTER TABLE {T} ADD COLUMN IF NOT EXISTS prior_basis TEXT, ADD COLUMN IF NOT EXISTS source_ref TEXT")
    fs.psql(pg, f"ALTER TABLE {T} ADD CONSTRAINT brahma_class_priors_lifetime_basis_ck CHECK (fact_kind <> 'lifetime_count_per_100y' OR (prior_basis IN ('demographic_structural','derived_identity') AND source_ref IS NOT NULL))")
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_class_priors import ClassPriorsWriter
    from pipeline.orchestrator.writers.bg_class_lifetime_counts import ClassLifetimeCountsWriter
    import brahmagyan.l0_class_lifetime_counts as L
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    r1 = ClassPriorsWriter().run(ContextSpec(asset_id=PRI, build_id=RUN, db_conn=conn, config={}))
    r2 = ClassLifetimeCountsWriter().run(ContextSpec(asset_id=LIFE, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert r1.rows_inserted == 171 and r2.rows_inserted == len(L.LIFETIME_COUNT_ROWS), (r1.notes, r2.notes)
    yield pg
    fs.psql(pg, f"DROP TABLE IF EXISTS {T} CASCADE")


def _m(db, mp, aid, decl=None):
    return fs.measure(aid, db, mp, ac.registered_ids("")[aid], T, [T], decl or _own(aid), registry=dict(has_writer=True))


@pytest.mark.parametrize("aid", [PRI, LIFE])
def test_REAL_WRITERS_the_shared_table_reads_na_on_all_six_cells_for_each_asset(db, monkeypatch, aid):
    got = _m(db, monkeypatch, aid)
    fs.all_na(got)
    b = got["Narr.agree"]["prose_none"]
    assert b["column_scope"] == "written" and b["open"] == [] and [c["column"] for c in b["closed"]] == ["prior_basis"]


def test_REAL_WRITERS_the_census_finding_is_reproduced_without_the_scope_and_gone_with_it(db, monkeypatch):
    """The final census' FAIL, byte for byte, from the declarations as they were (scope `all`, no prior_basis closure, lifetime without citation / prior_version)."""
    old = _own(LIFE)
    old["prose_none"]["column_scope"] = None
    old["prose_none"]["closed_columns"] = []
    old["prose_none"]["transcription_columns"] = [c for c in old["prose_none"]["transcription_columns"] if c["column"] != "citation"]
    old["prose_none"]["identifier_columns"] = [c for c in old["prose_none"]["identifier_columns"] if c["column"] != "prior_version"]
    got = _m(db, monkeypatch, LIFE, old)
    assert got["Narr.agree"]["v"] == FAIL and "brahma_class_priors.citation (text), brahma_class_priors.prior_basis (text), brahma_class_priors.prior_version (text), brahma_class_priors.varga_weights (jsonb)" in got["Narr.agree"]["measured"]
    oldp = _own(PRI)
    oldp["prose_none"]["column_scope"] = None
    oldp["prose_none"]["closed_columns"] = []
    got = _m(db, monkeypatch, PRI, oldp)
    assert got["Narr.agree"]["v"] == FAIL and "brahma_class_priors.prior_basis (text)" in got["Narr.agree"]["measured"]


def test_REAL_WRITERS_MUTATION_dropping_a_column_the_lifetime_writer_writes_from_its_declaration_is_a_FAIL(db, monkeypatch):
    for col, key in (("citation", "transcription_columns"), ("prior_version", "identifier_columns")):
        d = _own(LIFE)
        d["prose_none"][key] = [c for c in d["prose_none"][key] if c["column"] != col]
        got = _m(db, monkeypatch, LIFE, d)
        assert got["Narr.agree"]["v"] == FAIL and f"brahma_class_priors.{col}" in got["Narr.agree"]["measured"], (col, got["Narr.agree"]["measured"][:300])


@pytest.mark.parametrize("aid", [PRI, LIFE])
def test_REAL_WRITERS_MUTATION_a_prior_basis_outside_the_two_tier_names_is_a_FAIL_for_both_assets(db, monkeypatch, aid):
    # the table CHECK only confines the lifetime rows, so a seed prior carrying a third basis is a row the CHECK admits and the closure must catch
    def check():
        got = _m(db, monkeypatch, aid)
        assert got["Narr.agree"]["v"] == FAIL and "prior_basis" in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, T, ["prior_version", "signal_type_class", "fact_kind", "source_subsystem", "signal_tradition"], "prior_basis", "'a judgement call written by hand'", "prior_version = '1.0' AND signal_type_class = 'yoga'", check)
    assert _m(db, monkeypatch, aid)["Narr.agree"]["v"] == NA


def test_REAL_WRITERS_MUTATION_a_closure_that_omits_the_tier_the_rows_hold_is_a_FAIL(db, monkeypatch):
    import brahmagyan.l0_class_lifetime_counts as L
    assert {r.prior_basis for r in L.LIFETIME_COUNT_ROWS} == {"demographic_structural"}                  # the seed holds no derived_identity row today, so that name is declared but not yet exercised
    d = _own(LIFE)
    d["prose_none"]["closed_columns"][0]["values"] = ["derived_identity"]
    got = _m(db, monkeypatch, LIFE, d)
    assert got["Narr.agree"]["v"] == FAIL and "prior_basis" in got["Narr.agree"]["measured"]


# ───────────────────────── N-235 (a): the two-letter graha codes of fact_kind are a standard abbreviation set, not misspellings ─────────────────────────

def test_the_fact_kind_graha_codes_are_exactly_the_nine_released_graha_codes_one_per_graha():
    """bg_class_priors Vocab.alias FAIL lists SU / MO / MA / ME / JU / VE / SA / RA / KE in brahma_class_priors.fact_kind. They are the 2-letter codes of the RELEASED graha vocabulary
    (platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json, the source graha_labels.ts GRAHA_CODE_TO_NAME is built from), one per graha, and priors_config.ts reads them by those codes.
    No declaration form exists for this (Vocab.alias is value-keyed; `vocab_alias` declares an alias CLASS against bg_ontology): the missing piece is the detector registering the released set (see DECL_REPORT)."""
    import brahmagyan.l0_class_priors as P
    rel = json.loads((ac.ROOT / "platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json").read_text(encoding="utf-8"))
    grahas = [e for e in rel["entities"] if "graha" in e["roles"]]
    assert len(grahas) == 11 or len(grahas) >= 9
    seed_codes = sorted({r[0] for r in P.GRAHA_DOMAIN_ROWS})
    assert seed_codes == sorted(["SU", "MO", "MA", "ME", "JU", "VE", "SA", "RA", "KE"])
    owner = {}
    for code in seed_codes:
        hits = [e for e in grahas if code in e["aliases"]]
        assert len(hits) == 1, (code, [h.get("canonical_id") for h in hits])                                   # each code names exactly one released graha
        owner[code] = hits[0]
    assert len({id(v) for v in owner.values()}) == 9                                                           # and no two codes name the same graha
    src = (ac.ROOT / "platform/src/lib/retrieval/ranking/priors_config.ts").read_text(encoding="utf-8")
    assert "'SU', 'MO', 'MA', 'ME', 'JU', 'VE', 'SA', 'RA', 'KE'," in src                                     # the consumer reads the table by these codes: renaming the stored values would break it
