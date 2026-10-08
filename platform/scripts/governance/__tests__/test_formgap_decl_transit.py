"""test_formgap_decl_transit.py: the FORM-GAP declaration of bg_transit_rules is TRUE, shown on rows the REAL writer builds (SS N-191 / N-192).

One measured table (bg_transit_rules, 69 rows) seeded from `brahmagyan/l0_transit.py`: rule_type and graha are closed by per-key `values_from` of the committed seed; classical_citation is the declared source
column; phala and rule_notes are two hand-curated 69-sentence corpora pinned by count and sha256 with the committed seed named. The real writer (it also seeds bg_transit_engine and bg_transit_moorti) runs on a
throw-away PostgreSQL carrying the real DDL (migrations 266 and 401); the engine's OWN `_measure_prose` reads the table and all six cells must read N/A through a checked block. bg_transit_moorti is NOT in
the asset's measured set (no `produced_tables`); that is stated, not hidden, by the last test.
"""
from __future__ import annotations

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
import prose_forms as pf  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET, CELLS  # noqa: E402

AID = "bg_transit_rules"
T = "bg_transit_rules"
DECLS = ac.load_asset_declarations()
RUN = "11111111-1111-4111-8111-111111111111"


def _own():
    return json.loads(json.dumps(DECLS[AID]))


def _cc(col):
    return next(c for c in DECLS[AID]["curated_corpus"] if c["column"] == col)


def test_the_declaration_is_sound_and_names_its_forms():
    e = DECLS[AID]
    assert ac.prose_none_problem(e) is None and ac.curated_corpus_problem(e) is None and e["prose_fields"] == [] and e["evidence_kind"] == "writer"
    assert [c["column"] for c in e["prose_none"]["closed_columns"]] == ["rule_type", "graha"] and [(c["column"], c["count"], c["mode"]) for c in e["curated_corpus"]] == [("phala", 76, "equal"), ("rule_notes", 74, "equal")]
    assert "produced_tables" not in e                                            # the measured set is the target table only (a slice to the writer's rows is refused by the engine: slices must cover the table)


MIG = fs.SMIG / "397_bg_transit_av_gates.sql"


def _mig_insert() -> str:
    """The migration's own INSERT statement of the 7 double_transit rules, exactly as written (text between its INSERT and its ON CONFLICT clause)."""
    sql = MIG.read_text(encoding="utf-8")
    return sql[sql.index("INSERT INTO bg_transit_rules"):sql.index("ON CONFLICT (graha, rule_type, primary_house) DO NOTHING;")] + "ON CONFLICT (graha, rule_type, primary_house) DO NOTHING"


def _mig_rows():
    """[(graha, house, phala, note|None)] parsed from the migration text (an independent reading of the 7 rows the live table holds beside the writer's)."""
    import re
    blk = _mig_insert()
    rows = re.findall(r"\('double_transit', '(\w+)', (\d+),\s+NULL,\s+'((?:[^']|'')*)',\s+'((?:[^']|'')*)',\s+(NULL|'(?:[^']|'')*')\)", blk)
    assert len(rows) == 7
    return [(g, int(h), ph.replace("''", "'"), None if nt == "NULL" else nt[1:-1].replace("''", "'")) for g, h, ph, _c, nt in rows]


def test_the_pins_are_the_seeds_69_plus_the_migrations_7_and_every_seed_sentence_is_a_literal_the_per_key_read_finds():
    import brahmagyan.l0_transit as TR
    mig = _mig_rows()
    for col, extra, want in (("phala", [r[2] for r in mig], 76), ("rule_notes", [r[3] for r in mig if r[3]], 74)):
        sents = [r[col] for r in TR.BG_TRANSIT_RULES if r.get(col) is not None]
        cc = _cc(col)
        assert len(sents) == 69 and len(sents) + len(extra) == want == cc["count"] and pf.corpus_digest(sents + extra) == cc["digest"], col
        assert "seed" not in cc and cc["mode"] == "equal"                                                        # no single committed seed holds the 76 / 74: the seed's 69 are pinned below
        assert sorted(pf.resolve_seed_sentences(fs.REPO, dict(file="platform/python-sidecar/brahmagyan/l0_transit.py", constants=["BG_TRANSIT_RULES"], key=col))) == sorted(sents), col
    assert pf.corpus_digest([r["phala"] for r in TR.BG_TRANSIT_RULES]) == "629bd45bccae67cc91d277511908ee23e216e7b3c5aa29aa82e81ddb73057334"      # the seed's own 69, unchanged since FORM-GAP
    assert pf.corpus_digest([r["rule_notes"] for r in TR.BG_TRANSIT_RULES if r.get("rule_notes") is not None]) == "9c9d54674e5fd1375b52f40fcdb7effecd835315a9add04988d3b758477749a2"


def test_the_closed_words_are_the_seed_words_plus_the_migrations():
    import brahmagyan.l0_transit as TR
    cols = {x["column"]: x for x in DECLS[AID]["prose_none"]["closed_columns"]}
    seed_rt, seed_g = sorted({r["rule_type"] for r in TR.BG_TRANSIT_RULES}), sorted({r["graha"] for r in TR.BG_TRANSIT_RULES})
    assert seed_rt == ["favourable", "unfavourable"]                              # the table's CHECK also admits `vedha`; the seed writes none, so a vedha row is outside the closure
    assert seed_g == sorted(["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"])
    mig = _mig_rows()
    assert sorted(cols["rule_type"]["values"]) == sorted(seed_rt + ["double_transit"])
    assert sorted(cols["graha"]["values"]) == sorted(seed_g + sorted({r[0] for r in mig})) and {r[0] for r in mig} == {"Jupiter", "Saturn"}


@pytest.fixture(scope="module")
def db(disposable_pg):
    psycopg = pytest.importorskip("psycopg")
    pg = disposable_pg
    fs.drop_tables(pg, "bg_transit_engine", T, "bg_transit_moorti")
    for t in ("bg_transit_engine", T):
        fs.psql(pg, fs.create_table_ddl(fs.MIG / "266_bg_transit_tables.sql", t))
    fs.psql(pg, fs.create_table_ddl(fs.SMIG / "401_bg_transit_moorti.sql", "bg_transit_moorti"))
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_transit_rules import BgTransitRulesWriter
    from psycopg.rows import dict_row
    conn = psycopg.connect(pg.url, autocommit=True, row_factory=dict_row)
    res = BgTransitRulesWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert res.rows_inserted == 105, res.notes
    fs.psql(pg, f"ALTER TABLE {T} DROP CONSTRAINT IF EXISTS bg_transit_rules_rule_type_check")          # migration 397 section 2, applied before its section 3 as in production
    fs.psql(pg, f"ALTER TABLE {T} ADD CONSTRAINT bg_transit_rules_rule_type_check CHECK (rule_type IN ('favourable', 'unfavourable', 'vedha', 'double_transit'))")
    fs.psql(pg, _mig_insert())                                                    # WFIX-B: production also holds the 7 rows migration 397 inserted beside the writer's 69 (the writer's ownership match leaves them alone)
    assert fs.psql(pg, f"SELECT count(*) FROM {T}").strip() == "76"
    yield pg
    fs.drop_tables(pg, "bg_transit_engine", T, "bg_transit_moorti")


def _m(db, mp, decl=None):
    return fs.measure(AID, db, mp, ac.registered_ids("")[AID], T, [T], decl or _own(), registry=dict(has_writer=True))


def test_REAL_WRITER_the_table_reads_na_on_all_six_cells_through_a_checked_block(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert sorted(x["column"] for x in f["curated"]) == ["phala", "rule_notes"] and sorted((x["column"], x["count"], x["seed"]) for x in f["curated"]) == [("phala", 76, False), ("rule_notes", 74, False)]


def test_REAL_WRITER_the_live_closed_columns_equal_the_declared_words(db):
    for c in ("rule_type", "graha"):
        live = sorted(x for x in fs.psql(db, f"SELECT DISTINCT {c} FROM {T}").split("\n") if x)
        spec = next(x for x in DECLS[AID]["prose_none"]["closed_columns"] if x["column"] == c)["values"]
        assert set(live) <= set(spec), c
        assert set(live) == set(spec), c                                                                                         # and no declared word is dead


@pytest.mark.parametrize("col,newv,needle", [
    ("rule_type", "'vedha'", "rule_type"),
    ("graha", "'pluto'", "graha"),
    ("phala", "'A freshly composed transit result for the table'", "phala"),
    ("rule_notes", "'A freshly composed exception note that is not in the pinned corpus'", "rule_notes"),
    ("rule_notes", "NULL", "rule_notes"),
])
def test_REAL_WRITER_MUTATION_a_value_outside_its_form_is_a_FAIL(db, monkeypatch, col, newv, needle):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, T, "id", col, newv, "true", check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_an_added_rule_is_drift_and_a_dropped_one_is_drift(db, monkeypatch):
    fs.psql(db, f"INSERT INTO {T} (rule_type, graha, primary_house, vedha_house, phala, classical_citation, rule_notes) VALUES ('vedha', 'sun', 11, NULL, 'Gains without end', 'BPHS Ch.29', 'A seventieth note')")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "added" in got["Narr.agree"]["measured"]
    finally:
        fs.psql(db, f"DELETE FROM {T} WHERE phala = 'Gains without end'")
    row = fs.psql(db, f"SELECT id FROM {T} ORDER BY id LIMIT 1").strip()
    saved = fs.psql(db, f"SELECT rule_type || '|' || graha || '|' || primary_house || '|' || coalesce(vedha_house::text, '') || '|' || phala || '|' || classical_citation || '|' || coalesce(rule_notes, '') FROM {T} WHERE id = {row}").strip().split("|")
    fs.psql(db, f"DELETE FROM {T} WHERE id = {row}")
    try:
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and "removed" in got["Narr.agree"]["measured"]
    finally:
        q = lambda x: "'" + x.replace("'", "''") + "'"
        fs.psql(db, f"INSERT INTO {T} (id, rule_type, graha, primary_house, vedha_house, phala, classical_citation, rule_notes) VALUES ({row}, {q(saved[0])}, {q(saved[1])}, {saved[2]}, {saved[3] or 'NULL'}, {q(saved[4])}, {q(saved[5])}, {q(saved[6])})")
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA


def test_REAL_WRITER_MUTATION_the_pin_of_a_corpus_that_is_not_the_data_is_a_FAIL(db, monkeypatch):
    d = _own()
    d["curated_corpus"][0]["digest"] = "f" * 64
    got = _m(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "digest" in got["Narr.agree"]["measured"]


def test_the_sibling_moorti_table_is_outside_the_measured_set_and_that_is_not_hidden(db):
    """bg_transit_moorti (27 hand-typed phala_brief lines, written by the same writer) is in no produced_tables: the six cells do not read it. Declaring it a produced table would make bg_transit_engine (its own asset, written by
    this writer too) an undeclared extra table of this asset and FAIL Build.completion: a separate decision."""
    assert fs.psql(db, "SELECT count(*) FROM bg_transit_moorti").strip() == "27"
    assert "bg_transit_moorti" not in json.dumps(DECLS[AID]["prose_none"])


# ───────────── WFIX-B (census 5124c348a): the table holds the writer's 69 rows AND migration 397's 7 hand-typed double_transit rows ─────────────

def test_WFIXB_the_writer_leaves_the_migration_rows_alone_on_a_rerun(db):
    """The rows are not re-written by the writer: a second run of the real writer leaves exactly the same 76 rows (so nothing changes on a rebuild)."""
    psycopg = pytest.importorskip("psycopg")
    from pipeline.orchestrator.writers import ContextSpec
    from pipeline.orchestrator.writers.bg_transit_rules import BgTransitRulesWriter
    from psycopg.rows import dict_row
    before = fs.psql(db, f"SELECT md5(string_agg(t::text, '|' ORDER BY graha, rule_type, primary_house)) FROM (SELECT graha, rule_type, primary_house, vedha_house, phala, classical_citation, rule_notes FROM {T}) t").strip()
    conn = psycopg.connect(db.url, autocommit=True, row_factory=dict_row)
    BgTransitRulesWriter().run(ContextSpec(asset_id=AID, build_id=RUN, db_conn=conn, config={}))
    conn.close()
    assert fs.psql(db, f"SELECT count(*) FROM {T}").strip() == "76"
    assert fs.psql(db, f"SELECT md5(string_agg(t::text, '|' ORDER BY graha, rule_type, primary_house)) FROM (SELECT graha, rule_type, primary_house, vedha_house, phala, classical_citation, rule_notes FROM {T}) t").strip() == before


def test_WFIXB_the_76_row_table_reads_na_on_all_six_cells_and_names_both_pins(db, monkeypatch):
    got = _m(db, monkeypatch)
    fs.all_na(got)
    f = got["Narr.agree"]["prose_none"]["forms"]
    assert sorted((x["column"], x["count"]) for x in f["curated"]) == [("phala", 76), ("rule_notes", 74)]


def test_WFIXB_the_declaration_before_the_fix_reads_exactly_the_census_fail(db, monkeypatch):
    """The FIX_LIST text of census 5124c348a, reproduced: the 69-row pins and the seed-only words on the table as production holds it."""
    import brahmagyan.l0_transit as TR
    d = _own()
    for c in d["prose_none"]["closed_columns"]:
        c.pop("values")
        c["values_from"] = dict(file="platform/python-sidecar/brahmagyan/l0_transit.py", constants=["BG_TRANSIT_RULES"], key=c["column"])
    for col, dg in (("phala", "629bd45bccae67cc91d277511908ee23e216e7b3c5aa29aa82e81ddb73057334"), ("rule_notes", "9c9d54674e5fd1375b52f40fcdb7effecd835315a9add04988d3b758477749a2")):
        cc = next(c for c in d["curated_corpus"] if c["column"] == col)
        cc.update(count=69, digest=dg, seed=dict(file="platform/python-sidecar/brahmagyan/l0_transit.py", constants=["BG_TRANSIT_RULES"], key=col))
    m = _m(db, monkeypatch, d)["Narr.agree"]
    assert m["v"] == FAIL
    for needle in ("the table holds more than the 69 pinned sentence(s)", "bg_transit_rules.graha: 7 row(s) hold text outside the declared closed vocabulary", "bg_transit_rules.rule_type: 7 row(s) hold text outside the declared closed vocabulary"):
        assert needle in m["measured"].replace("rule_notes", "").replace("phala", "") or needle in m["measured"], (needle, m["measured"][:600])


@pytest.mark.parametrize("col,newv,where", [
    ("phala", "'A freshly composed double transit result nobody pinned'", "rule_type = 'double_transit' AND primary_house = 5"),
    ("rule_notes", "'A freshly composed note on a migration row that nobody pinned'", "rule_type = 'double_transit' AND primary_house = 9"),
    ("graha", "'JUPITER'", "rule_type = 'double_transit' AND primary_house = 2"),
    ("rule_type", "'vedha'", "rule_type = 'double_transit' AND primary_house = 4"),      # the real DDL's CHECK admits vedha, which no declared word names
])
def test_WFIXB_REAL_WRITER_MUTATION_an_edited_migration_row_is_a_FAIL(db, monkeypatch, col, newv, where):
    def check():
        got = _m(db, monkeypatch)
        assert got["Narr.agree"]["v"] == FAIL and col in got["Narr.agree"]["measured"], got["Narr.agree"]["measured"][:400]
    fs.mutate_and_restore(db, T, "id", col, newv, where, check)
    assert _m(db, monkeypatch)["Narr.agree"]["v"] == NA
