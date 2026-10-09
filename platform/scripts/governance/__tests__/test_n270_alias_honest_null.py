"""test_n270_alias_honest_null.py: SS N-270, the checked honest-null declaration for the empty synonym sets of the dosha class of brahma_ontology."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

ENTRY = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]["bg_ontology"]
COLS = ["id", "entity_class", "canonical_id", "synonyms"]
T = "brahma_ontology"


def test_the_committed_declaration_is_sound_and_scoped_to_dosha_only():
    lift, problems = ac.vocab_alias_honest_null_sets(ENTRY, T, COLS)
    assert problems == [] and lift == {"dosha": "ontology_synonyms"}
    ac.validate_vocab_alias_honest_null_declaration("bg_ontology", ENTRY)


def test_forgery_wrong_table_missing_columns_or_unreadable_writer_voids_everything():
    assert ac.vocab_alias_honest_null_sets(ENTRY, "other_table", COLS)[0] == {}
    assert ac.vocab_alias_honest_null_sets(ENTRY, T, ["id", "entity_class"])[0] == {}
    assert ac.vocab_alias_honest_null_sets(ENTRY, T, None)[0] == {}
    assert ac.vocab_alias_honest_null_sets(ENTRY, None, COLS)[0] == {}
    e = copy.deepcopy(ENTRY)
    e["vocab_alias_honest_null"][0]["source_file"] = "platform/python-sidecar/brahmagyan/no_such_writer.py"
    lift, problems = ac.vocab_alias_honest_null_sets(e, T, COLS)
    assert lift == {} and problems


WRITER = ('''
def seed(cur, d, cid, now):
    cur.execute(
        """
        INSERT INTO brahma_ontology (entity_class, canonical_id, canonical_name_en, synonyms, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """,
        ("dosha", cid, d["name_en"], SYN, now),
    )
''')


def _writer_decl(tmp_path, body, entity_class="dosha"):
    (tmp_path / "platform").mkdir(exist_ok=True)
    (tmp_path / "platform" / "w.py").write_text(body, encoding="utf-8")
    e = copy.deepcopy(ENTRY)
    e["vocab_alias_honest_null"][0].update(source_file="platform/w.py", entity_class=entity_class)
    return e


def _lift(e, tmp_path):
    return ac.vocab_alias_honest_null_sets(e, T, COLS, root=tmp_path)[0]


def test_the_real_writer_is_accepted_by_the_ast_read_for_dosha_only():
    assert ac.vocab_alias_honest_null_sets(ENTRY, T, COLS)[0] == {"dosha": "ontology_synonyms"}
    for other in ("planet", "house", "yoga", "sign"):             # the class names appear in l0_doshas.py, but never as the class of the synonyms assignment
        e = copy.deepcopy(ENTRY)
        e["vocab_alias_honest_null"][0]["entity_class"] = other
        assert ac.vocab_alias_honest_null_sets(e, T, COLS)[0] == {}, other


def test_forgery_the_pattern_in_a_comment_or_an_unrelated_line_is_not_the_assignment(tmp_path):
    good = WRITER.replace("SYN", 'd.get("ontology_synonyms") or []')
    assert _lift(_writer_decl(tmp_path, good), tmp_path) == {"dosha": "ontology_synonyms"}
    commented = WRITER.replace("SYN", "[]") + '\n# syn = d.get("ontology_synonyms") or []\nx = d.get("ontology_synonyms") or []\n'
    assert _lift(_writer_decl(tmp_path, commented), tmp_path) == {}                 # the writer writes [] while the pattern sits in a comment / another line
    assert _lift(_writer_decl(tmp_path, WRITER.replace("SYN", 'd.get("other_key") or []')), tmp_path) == {}
    assert _lift(_writer_decl(tmp_path, WRITER.replace("SYN", 'd.get("ontology_synonyms") or ["x"]')), tmp_path) == {}
    assert _lift(_writer_decl(tmp_path, WRITER.replace("SYN", 'd.get("ontology_synonyms")')), tmp_path) == {}
    assert _lift(_writer_decl(tmp_path, good, entity_class="planet"), tmp_path) == {}              # the class constant is "dosha", not planet
    assert _lift(_writer_decl(tmp_path, good.replace('("dosha", cid', '(cls, cid')), tmp_path) == {}    # a non-constant class is not a class assignment
    assert _lift(_writer_decl(tmp_path, "def broken(:\n"), tmp_path) == {}                          # an unparsable writer proves nothing
    assert _lift(_writer_decl(tmp_path, good.replace("brahma_ontology", "other_table")), tmp_path) == {}


def test_forgery_the_column_is_pinned_to_synonyms_and_the_class_column_to_entity_class():
    for field, value in (("column", "canonical_id"), ("class_column", "canonical_id")):
        e = copy.deepcopy(ENTRY)
        e["vocab_alias_honest_null"][0][field] = value
        assert ac.vocab_alias_honest_null_sets(e, T, COLS + ["canonical_id"])[0] == {}


def test_malformed_declarations_fail_validation():
    for mutate in (lambda d: d.update(extra=1), lambda d: d.update(entity_class="bad class"), lambda d: d.update(source_file="../x.py"), lambda d: d.update(evidence="no/such.py:1")):
        e = copy.deepcopy(ENTRY)
        mutate(e["vocab_alias_honest_null"][0])
        assert ac.vocab_alias_honest_null_problem(e)
    e = copy.deepcopy(ENTRY)
    e["vocab_alias_honest_null"] *= 2
    assert "twice" in ac.vocab_alias_honest_null_problem(e)


def _mk(pg, monkeypatch):
    point_psql_at(pg, monkeypatch)
    ac.psql("DROP TABLE IF EXISTS n270_onto")
    ac.psql("CREATE TABLE n270_onto (entity_class text, canonical_id text, synonyms text[])")
    for r in ("'dosha','a','{}'", "'dosha','b','{}'", "'dosha','punarphoo','{vish,Punarphoo}'", "'yoga','y1','{}'", "'yoga','y2','{z}'", "'sign','s','{a}'"):
        ac.psql(f"INSERT INTO n270_onto VALUES ({r})")


def test_REAL_SQL_only_empty_sets_of_the_declared_class_are_lifted(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch)
    plain = ac.alias_census("n270_onto", ["entity_class", "synonyms"])
    assert plain["dosha"]["no_alias"] == 2 and plain["yoga"]["no_alias"] == 1
    got = ac.alias_census("n270_onto", ["entity_class", "synonyms"], lift={"dosha": "ontology_synonyms"})
    assert got["dosha"]["no_alias"] == 0 and got["dosha"]["honest_null"] == 2 and got["dosha"]["rows"] == 3      # the populated Punarphoo row is untouched
    assert got["yoga"]["no_alias"] == 1 and "honest_null" not in got["yoga"]                                        # an undeclared class still FAILs
    assert got["sign"]["no_alias"] == 0 and "honest_null" not in got["sign"]


def test_REAL_SQL_without_a_declaration_nothing_changes(monkeypatch, disposable_pg):
    _mk(disposable_pg, monkeypatch)
    assert ac.alias_census("n270_onto", ["entity_class", "synonyms"], lift={}) == ac.alias_census("n270_onto", ["entity_class", "synonyms"])


# ───────────────────────── the cell grade through measure() (SS N-270 amendment: N/A, never PASS) ─────────────────────────

def _measure_cell(monkeypatch, tmp_path, census, decl):
    import test_e6_n99_build_completion_integrity as n99
    aid, cols = "bg_x", ["id", "entity_class", "synonyms"]
    reg = {aid: dict(n99._reg_row(aid, has_integrity=False), target_table=T, count_sql=f"SELECT count(*) FROM {T}")}
    n99._stub_layer(monkeypatch, tmp_path, reg, live=5)
    monkeypatch.setattr(ac, "catalog", lambda ts: dict(exists={T}, cols={T: cols}, keys={T: [["id"]]}, views=set(), types={T: {"id": "integer", "entity_class": "text", "synonyms": "ARRAY"}},
                                                      defaults={T: {}}, types_error=None, udts={}))
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: ({aid: dict(kind="data", **({"vocab_alias_honest_null": decl} if decl else {}))}))
    monkeypatch.setattr(ac, "alias_census", lambda t, c, lift=None: {k: dict(v) for k, v in census(lift).items()})

    def fake_psql(sql, sep="\x1f", timeout=None):
        return [["text"]] if "format_type(a.atttypid" in sql else []
    monkeypatch.setattr(ac, "psql", fake_psql)
    monkeypatch.setattr(ac, "scalar", lambda sql: None)
    return {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}[aid]["Vocab.alias"]


def _census(dosha_empty, other_empty=0):
    def f(lift):
        d = dict(rows=3, no_alias=dosha_empty)
        if "dosha" in (lift or {}) and d["no_alias"]:
            d["honest_null"], d["no_alias"] = d["no_alias"], 0
        return {"dosha": d, "yoga": dict(rows=2, no_alias=other_empty)}
    return f


DECL = ENTRY["vocab_alias_honest_null"]


def test_measure_fully_lifted_reads_na_with_the_reason_never_pass(monkeypatch, tmp_path):
    rec = _measure_cell(monkeypatch, tmp_path, _census(2), DECL)
    assert rec["v"] == ac.NA and rec["cause"] == "honest-null" and rec["measured"].startswith("no aliases to check: honest null, declared, checked")
    assert "class dosha" in rec["measured"]                                                    # the reason names only the lifted class
    assert "honest-null" in ac.NA_CAUSES["Vocab.alias"] and "Vocab.alias#measured:honest-null" in ac.NA_RULE_DECISIONS
    ac.validate_na_rule_decisions()


def test_measure_a_non_lifted_failure_beside_the_lift_still_fails(monkeypatch, tmp_path):
    rec = _measure_cell(monkeypatch, tmp_path, _census(2, other_empty=1), DECL)
    assert rec["v"] == ac.FAIL and rec.get("cause") is None and "yoga 1/2" in rec["measured"]


def test_measure_with_nothing_to_lift_is_graded_as_before(monkeypatch, tmp_path):
    assert _measure_cell(monkeypatch, tmp_path, _census(0), DECL)["v"] == ac.PASS            # a populated class: the old reading
    assert _measure_cell(monkeypatch, tmp_path, _census(2), None)["v"] == ac.FAIL            # no declaration: the empty sets FAIL


def test_measure_an_unsound_declaration_is_no_detector_not_na(monkeypatch, tmp_path):
    bad = copy.deepcopy(DECL)
    bad[0]["source_key"] = "some_other_key"
    rec = _measure_cell(monkeypatch, tmp_path, _census(2), bad)
    assert rec["v"] == ac.NO_DET and rec["v"] != ac.NA
