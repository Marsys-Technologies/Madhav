"""test_formgap_curated_corpus.py: FORM-GAP form 6 (SS N-192): the CURATED-CORPUS declaration.

An L0 reference table can hold HAND-CURATED sentences: constant writes BY DESIGN (reference content, not narration of a computed value). `curated_corpus` {table?, column, mode?, count, digest, seed?, waiver?,
why, evidence} pins such a column by count and sha256 digest (over the sorted sentences, whitespace-collapsed and NFC-normalised; prose_forms.corpus_digest). The engine computes the digest from the LIVE table
(chart-independent: the whole table is read) and compares:
  * mode `equal` (default): the table's non-NULL values ARE the corpus: ANY drift (a sentence added, removed or edited, a blank or placeholder) is a FAIL;
  * mode `contained`: the table also holds composed / extracted rows, so every pinned sentence must be present (a sentence removed or edited is a FAIL); needs a `seed`;
  * `seed` {file, constant, field?} or per-key {file, constants, key}: the COMMITTED literals the writer seeds from, read by AST; their digest must equal the pin (a drifted seed is a FAIL: the writer would
    write something else on its next rebuild);
  * for a prose_none asset the pinned column is exempt from the vocabulary requirement; for an asset that declares prose_fields a `waiver` {files, covers, pin} lets the pinned corpus replace the static
    writer scan's constant_write (and, where declared, literal_fallback) findings of that column: the findings must all lie in the declared files and kinds, their number per kind must EQUAL the pin, and
    nothing may be unresolved.
Real DDL (migration 250 bg_dignity_reference) on a disposable PostgreSQL for the live read; the writer scan runs on a real in-memory writer source.
"""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import sys
import textwrap
import unicodedata

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
import prose_forms as pf  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET, PARTIAL, PASS, CELLS  # noqa: E402

NULL = ac.NULL_CHECKS
SENTENCES = ["Exalted in Aries; the debilitation sign is Libra.", "Own signs are Leo; moolatrikona 0-20 degrees.", "Rahu's exaltation differs between the Parashari and Kerala schools."]
EV = "platform/python-sidecar/brahmagyan/l0_dignity_reference.py:179"      # the file must mention the column ("notes")


def _digest(sents):
    """Stated by hand here (the engine's definition restated independently): sha256 of the compact JSON array of the sorted, NFC-normalised, whitespace-collapsed sentences."""
    norm = sorted(" ".join(unicodedata.normalize("NFC", s).split()) for s in sents)
    return hashlib.sha256(json.dumps(norm, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _cc(sents=SENTENCES, **kw):
    d = dict(column="notes", count=len(sents), digest=_digest(sents), why="hand-typed classical remedies and notes the L0 seed carries as fixed reference content, never narration of a computed value", evidence=EV)
    d.update(kw)
    return d


def _none_decl(*cc, **kw):
    return {"prose_fields": [], "evidence": {"prose_fields": fs.EV}, "prose_none": dict(why=fs.WHY, closed_columns=[]), "curated_corpus": list(cc) or [_cc()], **kw}


# ───────────────────────────── the digest ─────────────────────────────

def test_the_digest_is_order_free_normalised_duplicate_keeping_and_unambiguous():
    d = pf.corpus_digest
    assert d(SENTENCES) == _digest(SENTENCES) == d(list(reversed(SENTENCES)))                                       # order never matters
    assert d(["a  b\n c"]) == d(["a b c"]) == d(["  a b c  "]) and d(["é"]) == d(["é"])                    # a re-flowed or re-encoded line is not drift
    assert d(["a b"]) != d(["a c"]) and d(["a", "b"]) != d(["a,b"]) and d(["a", "a"]) != d(["a"])                      # an edited word is; the boundaries are unambiguous; duplicates count
    assert d([]) == hashlib.sha256(b"[]").hexdigest()
    assert pf.normalise_sentence("  x \t y z ") == "x y z"


# ───────────────────────────── the validator ─────────────────────────────

def test_the_declaration_is_sound_and_the_fields_are_closed():
    assert ac.curated_corpus_problem(_none_decl()) is None
    assert ac.CURATED_CORPUS_DECL_FIELDS == ("table", "column", "mode", "count", "digest", "seed", "waiver", "why", "evidence") and "curated_corpus" in ac.DECL_FORMGAP_KEYS
    assert ac.curated_corpus_problem({"prose_fields": []}) is None


SEED = dict(file="platform/python-sidecar/brahmagyan/l0_dignity_reference.py", constants=["_NAISARGIKA_FRIENDSHIP"], key="notes")


@pytest.mark.parametrize("bad,needle", [
    (dict(count=0), "count must be an integer"), (dict(count=5001), "count must be an integer"), (dict(count="3"), "count must be an integer"), (dict(count=True), "count must be an integer"),
    (dict(digest="A" * 64), "digest must be 64"), (dict(digest="a" * 63), "digest must be 64"), (dict(digest=None), "digest must be 64"),
    (dict(mode="subset"), "mode must be null or one of"),
    (dict(mode="contained"), "needs a seed"),
    (dict(seed="x.py"), "seed"), (dict(seed=dict(file="x.py", constants=["A"], key="k")), "file must be a repo-relative path"),
    (dict(seed=dict(file=SEED["file"], constants=[], key="k")), "constants must be 1 to 16"), (dict(seed=dict(file=SEED["file"], constants=["a b"], key="k")), "constants must be"),
    (dict(seed=dict(file=SEED["file"], constants=["A", "A"], key="k")), "constants must be"), (dict(seed=dict(file=SEED["file"], constants=["A"], key="k k")), "key must be"),
    (dict(seed=dict(file=SEED["file"], constants=["A"])), "exactly {file, constants, key}"),
    (dict(waiver=dict(files=["a.py"], covers=["constant_write"], pin=dict(constant_write=1))), "declares prose_fields"),                 # a prose_none asset has no scan finding to replace
    (dict(column="note s"), "identifier"), (dict(evidence="unverified: the seed"), "evidence"),
    (dict(evidence="platform/scripts/governance/golden_test_scan.py:1"), "does not mention 'notes'"),
    (dict(why="tbd"), "why"), (dict(extra=1), "unknown field"),
])
def test_a_malformed_curated_corpus_is_refused(bad, needle):
    got = ac.curated_corpus_problem(_none_decl(_cc(**bad)))
    assert got is not None and needle in got, got


def test_list_level_refusals():
    assert "1 to 8" in ac.curated_corpus_problem(_none_decl(*[_cc(column=f"c{i}") for i in range(9)]))
    assert ac.curated_corpus_problem({"prose_fields": [], "curated_corpus": []}) is not None
    assert "listed twice" in ac.curated_corpus_problem(_none_decl(_cc(), _cc()))
    got = ac.prose_none_problem({"prose_fields": [], "evidence": {"prose_fields": fs.EV},
                                 "prose_none": dict(why=fs.WHY, closed_columns=[dict(column="notes", why="a closed list that is not this column", values=["x"])]), "curated_corpus": [_cc()]})
    assert got and "declared by both closed_columns and curated_corpus" in got


def _fields_decl(waiver=None, seed=SEED, **kw):
    d = {"prose_fields": ["notes"], "evidence": {"prose_fields": fs.EV}, "curated_corpus": [_cc(**dict(kw, **({"waiver": waiver} if waiver else {}), **({"seed": seed} if seed else {})))]}
    return d


def test_a_waiver_needs_declared_prose_a_seed_a_covered_column_and_exact_pins():
    W = dict(files=["brahmagyan/l0_dignity_reference.py"], covers=["constant_write"], pin=dict(constant_write=3))
    assert ac.curated_corpus_problem(_fields_decl(W)) is None
    assert "needs a seed" in ac.curated_corpus_problem(_fields_decl(W, seed=None))
    other = _fields_decl(W)
    other["prose_fields"] = ["other_col"]
    assert "not one of the asset's declared prose columns" in ac.curated_corpus_problem(other)
    for bad, needle in ((dict(W, files=[]), "files must be"), (dict(W, files=["../x.py"]), "files must be"), (dict(W, files=["a.txt"]), "files must be"), (dict(W, covers=[]), "covers must be"),
                        (dict(W, covers=["x"]), "covers must be"), (dict(W, covers=["constant_write", "constant_write"]), "covers must be"),
                        (dict(W, pin=dict(literal_fallback=1)), "pin must give an exact finding count"), (dict(W, pin=dict(constant_write=-1)), "pin must give"),
                        (dict(W, pin=dict(constant_write=True)), "pin must give"), (dict(W, extra=1), "waiver must be exactly")):
        got = ac.curated_corpus_problem(_fields_decl(bad))
        assert got and needle in got, (bad, got)


# ───────────────────────────── the per-key seed reader (AST, no code is run) ─────────────────────────────

@pytest.fixture()
def src(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "ROOT", tmp_path)
    d = tmp_path / "platform" / "python-sidecar" / "brahmagyan"
    d.mkdir(parents=True)

    def write(body, name="seed.py"):
        (d / name).write_text(textwrap.dedent(body), encoding="utf-8")
        return f"platform/python-sidecar/brahmagyan/{name}"
    return write


def test_the_per_key_seed_reads_plain_string_literals_only(src):
    rel = src('''
        CITE = "BPHS"
        ROWS = [
            dict(planet="sun", notes="Recite Aditya Hridayam on Sundays."),
            {"planet": "moon", "notes": "Fast on Mondays."},
            {"planet": "mars", "notes": f"Computed for {CITE}"},            # composed: never part of the corpus
            {"planet": "venus", "notes": CITE},                              # a name: not a literal
            {"planet": "saturn", "notes": "Donate " "sesame."},              # implicit concatenation folds in the parser
            {"planet": "x", "other": "not the key"},
        ]
        MORE = [[{"notes": "Nested one."}]]
        EXTRA = (*[{"notes": f"{i} comprehension"} for i in "ab"],)
    ''')
    spec = dict(file=rel, constants=["ROWS", "MORE", "EXTRA"], key="notes")
    assert pf.resolve_seed_sentences(ac.ROOT, spec) == ["Recite Aditya Hridayam on Sundays.", "Fast on Mondays.", "Donate sesame.", "Nested one."]
    with pytest.raises(ValueError, match="assigned 0 time"):
        pf.resolve_seed_sentences(ac.ROOT, dict(spec, constants=["NOPE"]))
    src("ROWS = []\nROWS = []")
    with pytest.raises(ValueError, match="assigned 2 time"):
        pf.resolve_seed_sentences(ac.ROOT, dict(spec, constants=["ROWS"]))
    with pytest.raises(ValueError, match="does not exist"):
        pf.resolve_seed_sentences(ac.ROOT, dict(spec, file="platform/python-sidecar/brahmagyan/none.py"))
    src("def (:")
    with pytest.raises(ValueError, match="cannot be parsed"):
        pf.resolve_seed_sentences(ac.ROOT, dict(spec, constants=["ROWS"]))


def test_the_literal_form_of_the_seed_is_the_values_from_reader(src):
    rel = src('S = ("b c", "a  b")')
    assert pf.resolve_seed_sentences(ac.ROOT, dict(file=rel, constant="S")) == ["b c", "a  b"]                 # source order, duplicates kept (a multiset)


# ───────────────────────────── the grader (pure) ─────────────────────────────

def _entry(**kw):
    return _cc(**kw)


def test_equal_mode_states():
    g = ac.grade_curated
    e = _entry()
    ok = g(e, dict(sentences=list(SENTENCES)))
    assert ok["state"] == "ok" and ok["block"] == dict(count=3, digest=e["digest"], seed=False, mode="equal")
    assert g(e, dict(sentences=list(reversed(SENTENCES))))["state"] == "ok"
    assert g(e, dict(sentences=[SENTENCES[0].replace("Exalted", "Exalted  ")] + SENTENCES[1:]))["state"] == "ok"           # whitespace is not drift
    added = g(e, dict(sentences=SENTENCES + ["a new one"]))
    assert added["state"] == "wrong" and "more than the 3 pinned" in added["text"] and "added" in added["text"]
    removed = g(e, dict(sentences=SENTENCES[:2]))
    assert removed["state"] == "wrong" and "holds 2" in removed["text"] and "removed" in removed["text"]
    edited = g(e, dict(sentences=[SENTENCES[0].replace("Aries", "Taurus")] + SENTENCES[1:]))
    assert edited["state"] == "wrong" and "edited" in edited["text"] and e["digest"] in edited["text"]
    for blank in ("", "  ", "N/A", "none", "-"):
        got = g(e, dict(sentences=SENTENCES[:2] + [blank]))
        assert got["state"] == "wrong" and "blank or a placeholder" in got["text"], blank
    assert g(e, dict(unread="timeout"))["state"] == "unread" and g(e, None)["state"] == "unread" and g(e, dict(sentences="x"))["state"] == "unread"


def test_contained_mode_states(src):
    rel = src('ROWS = [' + ",".join(f"dict(notes={s!r})" for s in SENTENCES) + "]")
    seed = dict(file=rel, constants=["ROWS"], key="notes")
    e = _entry(mode="contained", seed=seed)
    live = SENTENCES + ["a composed sentence about Mars", "another extracted passage"]                                   # the table also holds rows the corpus does not pin
    ok = ac.grade_curated(e, dict(sentences=live), *ac.formgap_seed(e))
    assert ok["state"] == "ok" and ok["block"]["mode"] == "contained" and ok["block"]["present"] == 3
    gone = ac.grade_curated(e, dict(sentences=live[1:]), *ac.formgap_seed(e))
    assert gone["state"] == "wrong" and "1 of the 3 pinned sentence(s) are absent" in gone["text"]
    edited = ac.grade_curated(e, dict(sentences=[live[0] + " (edited)"] + live[1:]), *ac.formgap_seed(e))
    assert edited["state"] == "wrong" and "absent" in edited["text"]
    # the committed seed drifted from the pin: the writer would write something else on its next rebuild
    src('ROWS = [' + ",".join(f"dict(notes={s!r})" for s in SENTENCES[:2] + ["Changed in the seed."]) + "]")
    drift = ac.grade_curated(e, dict(sentences=live), *ac.formgap_seed(e))
    assert drift["state"] == "wrong" and "committed seed" in drift["text"] and "next rebuild" in drift["text"]
    src("ROWS = [dict(notes=f'x{i}') for i in range(3)]")                                                                      # composed: no literal is part of the corpus
    empty = ac.grade_curated(e, dict(sentences=live), *ac.formgap_seed(e))
    assert empty["state"] == "wrong" and "committed seed holds 0 sentence" in empty["text"]
    src("OTHER = 1")
    unread = ac.grade_curated(e, dict(sentences=live), *ac.formgap_seed(e))
    assert unread["state"] == "unread" and "committed seed could not be read" in unread["text"]
    big = ac.grade_curated(e, dict(sentences=["s"] * (ac.CURATED_CONTAINED_READ_MAX + 1)), SENTENCES, None)
    assert big["state"] == "unread" and "past the read bound" in big["text"]


def test_equal_mode_with_a_seed_also_pins_the_seed(src):
    rel = src('ROWS = [' + ",".join(f"dict(notes={s!r})" for s in SENTENCES) + "]")
    e = _entry(seed=dict(file=rel, constants=["ROWS"], key="notes"))
    assert ac.grade_curated(e, dict(sentences=list(SENTENCES)), *ac.formgap_seed(e))["state"] == "ok"
    src('ROWS = [dict(notes="only one")]')
    got = ac.grade_curated(e, dict(sentences=list(SENTENCES)), *ac.formgap_seed(e))
    assert got["state"] == "wrong" and "committed seed holds 1 sentence" in got["text"]


# ───────────────────────────── the live read on a disposable database (prose_none exemption) ─────────────────────────────

@pytest.fixture()
def db(monkeypatch, disposable_pg):
    pg = disposable_pg
    point_psql_at(pg, monkeypatch)
    fs.drop_tables(pg, "bg_dignity_reference")
    fs.psql(pg, fs.create_table_ddl(fs.MIG / "250_bg_dignity_reference.sql", "bg_dignity_reference"))
    fs.psql(pg, "ALTER TABLE bg_dignity_reference ADD COLUMN IF NOT EXISTS variant_traditions JSONB DEFAULT NULL")           # migration 330
    yield pg
    fs.drop_tables(pg, "bg_dignity_reference")


GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
AID = "bg_dignity_reference"


def _seed(pg, notes=None):
    notes = notes if notes is not None else SENTENCES + [None] * (len(GRAHAS) - len(SENTENCES))
    for g, n in zip(GRAHAS, notes):
        nn = "NULL" if n is None else "'" + n.replace("'", "''") + "'"
        fs.psql(pg, f"INSERT INTO bg_dignity_reference (graha, exaltation_sign, classical_citation, notes) VALUES ('{g}', 'Aries', 'BPHS Ch.3', {nn})")


def _none_asset_decl(*cc):
    signs = ["Aries", "Taurus"]
    pn = dict(why=fs.WHY, closed_columns=[dict(column="graha", why="the nine grahas the L0 seed writes, each once", values=GRAHAS),
                                          dict(column="exaltation_sign", why="the sign names of the exaltation column in the seed", values=signs),
                                          dict(column="debilitation_sign", why="the sign names of the debilitation column in the seed", values=signs),
                                          dict(column="moolatrikona_sign", why="the sign names of the moolatrikona column in the seed", values=signs),
                                          dict(column="own_signs", why="the sign names of the own-signs list in the seed", values=signs),
                                          dict(column="variant_traditions", why="the json record carries no string leaf in this fixture", no_string_leaves=True)])
    src_cols = dict(level="row", columns=[dict(column="classical_citation", kinds=["K1"])], citation_state="sourced", why="each dignity row carries classical_citation naming the BPHS chapter", evidence="platform/python-sidecar/brahmagyan/l0_dignity_reference.py:115")
    return {"prose_fields": [], "evidence": {"prose_fields": fs.EV}, "source": src_cols, "prose_none": pn, "curated_corpus": list(cc) or [_cc()]}


def _measure(pg, monkeypatch, decl):
    monkeypatch.setattr(ac, "written_columns", lambda units, tables: {AID: {"graha", "notes"}})
    return fs.measure(AID, pg, monkeypatch, ac.registered_ids("")["bg_dignity_reference"], AID, [AID], decl)


def test_REAL_SQL_a_column_equal_to_its_pinned_corpus_is_exempt_and_reads_na_on_all_six(db, monkeypatch):
    _seed(db)
    got = _measure(db, monkeypatch, _none_asset_decl())
    fs.all_na(got)
    blk = got["Narr.agree"]["prose_none"]["forms"]["curated"]
    assert blk == [dict(table=AID, column="notes", verified=True, count=3, digest=_digest(SENTENCES), seed=False, mode="equal")]
    assert "notes" not in got["Narr.agree"]["prose_none"]["source_columns"]


@pytest.mark.parametrize("mutate,needle", [
    ("UPDATE bg_dignity_reference SET notes = 'Exalted in Taurus; the debilitation sign is Scorpio.' WHERE graha = 'Sun'", "edited"),           # a sentence edited
    ("UPDATE bg_dignity_reference SET notes = 'A fourth hand-typed claim.' WHERE graha = 'Ketu'", "added"),                                      # a sentence added
    ("UPDATE bg_dignity_reference SET notes = NULL WHERE graha = 'Mars'", "removed"),                                                           # a sentence removed
    ("UPDATE bg_dignity_reference SET notes = '' WHERE graha = 'Mars'", "blank or a placeholder"),                                              # a blank (the count is unchanged)
    ("UPDATE bg_dignity_reference SET notes = 'N/A' WHERE graha = 'Mars'", "blank or a placeholder"),
])
def test_REAL_SQL_MUTATION_any_drift_of_the_live_corpus_is_a_FAIL(db, monkeypatch, mutate, needle):
    _seed(db)
    assert _measure(db, monkeypatch, _none_asset_decl())["Narr.agree"]["v"] == NA
    fs.psql(db, mutate)
    got = _measure(db, monkeypatch, _none_asset_decl())
    assert got["Narr.agree"]["v"] == FAIL and needle in got["Narr.agree"]["measured"] and "bg_dignity_reference.notes (curated corpus)" in got["Narr.agree"]["measured"]
    assert all(got[c]["v"] == NO_DET for c in CELLS[1:])


def test_REAL_SQL_MUTATION_a_forged_pin_the_data_does_not_hold_FAILS(db, monkeypatch):
    _seed(db)
    assert _measure(db, monkeypatch, _none_asset_decl(_cc(count=4)))["Narr.agree"]["v"] == FAIL                      # a wrong count
    assert _measure(db, monkeypatch, _none_asset_decl(_cc(digest="0" * 64)))["Narr.agree"]["v"] == FAIL               # a digest nobody holds


def test_FORGERY_a_contained_corpus_never_exempts_a_prose_free_column_the_validator_refuses_it():
    """Review fix HIGH 2: `contained` pins only SOME of the column's rows, so a prose_none asset (prose_fields []) that declares it is refused outright."""
    seed = dict(file="platform/python-sidecar/brahmagyan/l0_dignity_reference.py", constants=["_NAISARGIKA_FRIENDSHIP"], key="notes")
    got = ac.curated_corpus_problem(_none_decl(_cc(mode="contained", seed=seed)))
    assert got is not None and "contained" in got and "declared prose column" in got, got


def test_FORGERY_a_contained_corpus_that_got_past_the_validator_reads_FAIL_not_na_with_unpinned_rows_in_the_table(db, src, monkeypatch):
    """The grader refuses on its own: the table holds composed rows the pin does not cover, so `contained` must never read N/A."""
    rel = src("ROWS = [" + ",".join(f"dict(notes={x!r})" for x in SENTENCES) + "]")
    _seed(db, SENTENCES + ["a composed sentence about Mars", "another extracted passage", "a third unpinned row", "a fourth unpinned row", "a fifth unpinned row", "a sixth unpinned row"])
    d = _none_asset_decl(_cc(mode="contained", seed=dict(file=rel, constants=["ROWS"], key="notes")))
    monkeypatch.setattr(ac, "curated_corpus_problem", lambda entry: None)
    got = _measure(db, monkeypatch, d)
    assert all(got[c]["v"] != NA for c in CELLS), {c: got[c]["v"] for c in CELLS}
    assert got["Narr.agree"]["v"] == FAIL and "never exempts the column as prose-free" in got["Narr.agree"]["measured"]


def test_REAL_SQL_the_whole_table_is_read_whatever_the_chart_scope(db, monkeypatch):
    _seed(db)
    scope = {AID: dict(where="false", label="a scope that excludes every row")}
    monkeypatch.setattr(ac, "written_columns", lambda units, tables: {AID: {"graha", "notes"}})
    got = fs.measure(AID, db, monkeypatch, ac.registered_ids("")["bg_dignity_reference"], AID, [AID], _none_asset_decl(), scope=scope)
    assert got["Narr.agree"]["v"] == NA                                                      # a scope that excludes every row of the closed columns would block them; the corpus read ignores it
    sql = ac.curated_read_sql(AID, "notes", 3, None)
    assert "WHERE \"notes\" IS NOT NULL" in sql and "false" not in sql and "LIMIT 4" in sql                              # bounded by count + 1; never sliced by the measured chart


def test_REAL_SQL_a_table_that_carries_a_chart_id_is_not_a_global_corpus(db, monkeypatch):
    _seed(db)
    fs.psql(db, "ALTER TABLE bg_dignity_reference ADD COLUMN chart_id uuid")
    got = _measure(db, monkeypatch, _none_asset_decl())
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "carries a chart_id column" in got["Narr.agree"]["measured"]


TIMEOUT = "ERROR:  canceling statement due to statement timeout"


@pytest.mark.parametrize("err", [ac.Unknown(TIMEOUT), ac.CheckTimeout("client-side timeout after 180s (psql killed)"), ac.Unknown("ERROR:  permission denied for table bg_dignity_reference")])
def test_a_read_that_timed_out_or_was_refused_is_no_detector(monkeypatch, err):
    def boom(q):
        raise err
    monkeypatch.setattr(ac, "scalar", boom)
    got = ac.formgap_curated_read(_cc(), "t", (["notes"], {"notes": "text"}, None))
    assert "unread" in got
    tables = {"t": (["notes"], {"notes": "text"}, None)}
    out = ac.grade_prose_none("x", _none_decl(), tables, "t", {}, forms=dict(curated={("t", "notes"): got}))
    assert all(out[c]["v"] == NO_DET for c in CELLS)


def test_any_other_failure_still_raises(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda q: (_ for _ in ()).throw(ac.Unknown('ERROR:  relation "t" does not exist')))
    with pytest.raises(ac.Unknown, match="does not exist"):
        ac.formgap_curated_read(_cc(), "t", (["notes"], {"notes": "text"}, None))


def test_the_rollup_guard_refuses_a_curated_block_without_its_digest(db, monkeypatch):
    _seed(db)
    rec = _measure(db, monkeypatch, _none_asset_decl())["Narr.agree"]
    assert ac.prose_none_na_problem("Narr.agree", rec) is None
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["curated"][0]["digest"] = "xyz"
    assert "carries no digest and count" in ac.prose_none_na_problem("Narr.agree", forged)
    forged = json.loads(json.dumps(rec))
    forged["prose_none"]["forms"]["curated"][0]["verified"] = False
    assert "not all verified" in ac.prose_none_na_problem("Narr.agree", forged)


# ───────────────────────────── the waiver: the pinned corpus replaces the scan's constant-write findings ─────────────────────────────

WRITER = '''
ROWS = [
    dict(remedy_id="r1", notes="Exalted in Aries; the debilitation sign is Libra."),
    dict(remedy_id="r2", notes="Own signs are Leo; moolatrikona 0-20 degrees."),
    dict(remedy_id="r3", notes="Rahu's exaltation differs between the Parashari and Kerala schools."),
]
SQL = "INSERT INTO bg_x (remedy_id, notes) VALUES (%(remedy_id)s, %(notes)s)"


def run(conn):
    for row in ROWS:
        conn.execute(SQL, row)
'''
WRITER_FILE = "platform/python-sidecar/brahmagyan/x_seed.py"


def _units(src_text, name="brahmagyan/x_seed.py"):
    tree = ast.parse(src_text)
    return [dict(rel=name, path=pathlib.Path(name), tree=tree, nodes=[tree], hop=0, via=name)]


def _waiver_decl(pin=3, files=("brahmagyan/x_seed.py",), covers=("constant_write",), seed=True, **kw):
    cc = _cc(waiver=dict(files=list(files), covers=list(covers), pin={k: (pin if k == "constant_write" else kw.get("fb", 0)) for k in covers}),
             seed=dict(file=WRITER_FILE, constants=["ROWS"], key="notes") if seed else None)
    cc = {k: v for k, v in cc.items() if v is not None}
    return {"prose_fields": ["notes"], "evidence": {"prose_fields": "platform/python-sidecar/brahmagyan/l0_dignity_reference.py:179"}, "curated_corpus": [cc]}


def _ctx(src_text=WRITER, live=SENTENCES, **kw):
    base = dict(table="bg_x", columns=["remedy_id", "notes"], types={"remedy_id": "text", "notes": "text"}, defaults={}, counts={"notes": {"checkable": 3, "blank": 0}},
                units=_units(src_text), beyond=[], paths=[], tests=[], vocabulary={"notes"}, written={},
                curated_reads={("bg_x", "notes"): dict(sentences=list(live))})
    base.update(kw)
    return base


@pytest.fixture()
def seed_file(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "ROOT", tmp_path)
    p = tmp_path / "platform" / "python-sidecar" / "brahmagyan"
    p.mkdir(parents=True)
    (p / "x_seed.py").write_text(WRITER, encoding="utf-8")
    return p / "x_seed.py"


def test_the_scan_alone_reads_the_constant_writes_as_partial(seed_file):
    d = _waiver_decl()
    d["curated_corpus"] = []
    got = ac.prose_checks("a", {"prose_fields": ["notes"], "evidence": d["evidence"]}, _ctx())
    assert all(got[c]["v"] == PARTIAL and "writer scan NOT clean" in got[c]["measured"] and "constant_write" in got[c]["measured"] for c in NULL)


def test_the_verified_corpus_replaces_exactly_the_pinned_findings_and_both_null_records_read_pass(seed_file):
    got = ac.prose_checks("a", _waiver_decl(), _ctx())
    for c in NULL:
        assert got[c]["v"] == PASS and got[c]["writer_scan"]["verified"] is True and "curated corpus replaced 3 constant-write" in got[c]["measured"], (c, got[c])
        cb = got[c]["writer_scan"]["curated_corpus"]
        assert cb == [dict(column="notes", verified=True, mode="equal", count=3, digest=_digest(SENTENCES), files=["brahmagyan/x_seed.py"], waived=dict(constant_write=3), pin=dict(constant_write=3))]
        assert ac.writer_scan_problem(got[c]) is None
    cells = ac.rollup_asset("L2", {c: got[c] for c in NULL})
    assert cells["Null"]["v"] == PASS and all(ch.get("null_writer_scan_verified") is True for ch in cells["Null"]["checks"])


def test_MUTATION_the_pin_must_equal_the_number_of_waived_findings(seed_file):
    for pin in (2, 4):
        got = ac.prose_checks("a", _waiver_decl(pin=pin), _ctx())
        assert all(got[c]["v"] == PARTIAL and "not the declared pin" in got[c]["measured"] for c in NULL), pin


def test_MUTATION_a_new_constant_in_the_writer_keeps_the_cap(seed_file):
    more = WRITER.replace("]\nSQL", '    dict(remedy_id="r4", notes="A fourth constant the pin does not know."),\n]\nSQL')
    got = ac.prose_checks("a", _waiver_decl(), _ctx(more))
    assert all(got[c]["v"] == PARTIAL and "not the declared pin" in got[c]["measured"] for c in NULL)


def test_MUTATION_a_finding_outside_the_declared_files_or_kinds_keeps_the_cap(seed_file):
    got = ac.prose_checks("a", _waiver_decl(files=("brahmagyan/elsewhere.py",)), _ctx())
    assert all(got[c]["v"] == PARTIAL and "outside every declared waiver" in got[c]["measured"] for c in NULL)
    fallback = WRITER.replace('notes="Own signs are Leo; moolatrikona 0-20 degrees."', 'notes=None or "n/a"')
    got = ac.prose_checks("a", _waiver_decl(), _ctx(fallback))
    assert all(got[c]["v"] == PARTIAL for c in NULL)
    got = ac.prose_checks("a", _waiver_decl(covers=("constant_write", "literal_fallback"), fb=1), _ctx(fallback))        # declared + exactly pinned: the fallback is waived too
    assert all(got[c]["v"] == PARTIAL for c in NULL)                                                                         # (the corpus then no longer matches the seed: still capped)


def test_MUTATION_an_unresolved_write_path_keeps_the_cap(seed_file):
    dyn = WRITER + "\n\ndef other(conn, rows):\n    conn.executemany('INSERT INTO bg_x (remedy_id, notes) VALUES (%s, %s)', rows)\n"
    got = ac.prose_checks("a", _waiver_decl(), _ctx(dyn))
    assert all(got[c]["v"] == PARTIAL and "unresolved" in got[c]["measured"] for c in NULL)


def test_MUTATION_a_corpus_that_drifted_in_the_table_or_the_seed_keeps_the_cap(seed_file):
    got = ac.prose_checks("a", _waiver_decl(), _ctx(live=SENTENCES[:2] + ["An edited sentence."]))
    assert all(got[c]["v"] == PARTIAL and "curated corpus is not verified" in got[c]["measured"] for c in NULL)
    assert got["Narr.agree"]["v"] == FAIL and "declared curated corpus does not hold" in got["Narr.agree"]["measured"] and "edited" in got["Narr.agree"]["measured"]       # drift FAILs the declaration
    seed_file.write_text(WRITER.replace("Own signs are Leo", "Own signs are Cancer"), encoding="utf-8")
    got = ac.prose_checks("a", _waiver_decl(), _ctx())
    assert all(got[c]["v"] == PARTIAL and "committed seed" in got[c]["measured"] for c in NULL)
    got = ac.prose_checks("a", _waiver_decl(), _ctx(curated_reads=None))
    assert all(got[c]["v"] == PARTIAL and "not verified" in got[c]["measured"] for c in NULL)
    assert got["Narr.agree"]["v"] != FAIL                                                                                   # a read that did not happen is never a FAIL


def test_a_blank_row_in_the_table_still_fails_whatever_the_corpus_says(seed_file):
    got = ac.prose_checks("a", _waiver_decl(), _ctx(counts={"notes": {"checkable": 5, "blank": 2}}))
    assert got["Null.blank_rows"]["v"] == FAIL and got["Null.schema_default"]["v"] == PARTIAL


def test_a_forged_record_does_not_lift_the_cap_in_the_rollup(seed_file):
    got = ac.prose_checks("a", _waiver_decl(), _ctx())
    ms = {c: got[c] for c in NULL}
    for tweak in (lambda b: b.update(waived=dict(constant_write=1)),                      # the waived counts are not the pin
                  lambda b: b.update(verified=False),
                  lambda b: b.update(digest="nothex"),
                  lambda b: b.update(column="elsewhere"),
                  lambda b: b.update(files=[])):
        bad = json.loads(json.dumps(ms))
        for c in NULL:
            tweak(bad[c]["writer_scan"]["curated_corpus"][0])
        assert ac.rollup_asset("L2", bad)["Null"]["v"] == PARTIAL
    empty = json.loads(json.dumps(ms))
    for c in NULL:
        empty[c]["writer_scan"]["curated_corpus"] = []
    assert ac.rollup_asset("L2", empty)["Null"]["v"] == PARTIAL


def test_no_waiver_declared_means_the_scan_result_is_untouched(seed_file):
    d = _waiver_decl()
    d["curated_corpus"][0].pop("waiver")
    got = ac.prose_checks("a", d, _ctx())
    assert all(got[c]["v"] == PARTIAL and "curated corpus" not in got[c]["measured"] for c in NULL)
