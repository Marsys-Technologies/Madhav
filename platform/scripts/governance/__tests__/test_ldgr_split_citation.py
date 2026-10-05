"""test_ldgr_split_citation.py: the ONE declared, CHECKED exception to "a citation starting with UNSOURCED is a placeholder" (SS via Pravaha, form (b) of the six Rahu/Ketu
house-vedha rows of bg_transit_rules). A K1 text column may declare `split_citation`; on the rows its closed `applies_to` predicate selects, a citation of EXACTLY the shape

    UNSOURCED (vedha partner: <text>) -- transit result: <K1 locus words> [machine locus <text_id>:PG<n>:C<n>] "<excerpt, at most 25 words>"

is judged on its K1 part (locus words no placeholder, excerpt non-blank and short, the machine locus RESOLVES to a classical_text_chunks chunk). Every other string that starts with UNSOURCED
stays a placeholder, and so does the split shape on a row the predicate does not select or on an entry that does not declare it. Real SQL on the throw-away disposable Postgres."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401

PASS, FAIL, PARTIAL, NO_DET = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET
DECLS = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["assets"]
SRC = DECLS["bg_transit_rules"]["source"]
EV = "platform/python-sidecar/services/gochara_rules/vedha_derive.py:129"
VEDHA = "UNSOURCED (vedha partner: inference, not in the cited verses)"


def good(sl="24", locus="phaladeepika:PG331:C1", excerpt="effects caused by Rahu ... (3) happiness"):
    return f'{VEDHA} — transit result: Phaladīpikā Adh. XXVI, Śl. {sl} [machine locus {locus}] "{excerpt}"'


def setup(rows):
    """rows: (graha, rule_type, primary_house, vedha_house|None, citation) -> a temp table shaped like bg_transit_rules plus a corpus stub holding the one chunk the good rows cite."""
    vals = []
    for i, (g, rt, ph, vh, cit) in enumerate(rows):
        lit = "NULL" if cit is None else "$q$" + cit + "$q$"
        vals.append(f"({i + 1}, '{g}', '{rt}', {ph}, {'NULL' if vh is None else vh}, {lit})")
    return ["CREATE TEMP TABLE classical_text_chunks (chunk_id text) ON COMMIT DROP;",
            "INSERT INTO classical_text_chunks VALUES ('phaladeepika_pg0331_c01'), ('phaladeepika_pg0321_c01');",
            "CREATE TEMP TABLE t_rules (id int, graha text, rule_type text, primary_house int, vedha_house int, classical_citation text) ON COMMIT DROP;",
            "INSERT INTO t_rules VALUES " + ",".join(vals) + ";"]


COLS = ["id", "graha", "rule_type", "primary_house", "vedha_house", "classical_citation"]
BPHS = "Phaladipika Adh. XXVI, Sloka 3 — phaladeepika:PG322:C1 (Sastri trans. 1950)"


def run(monkeypatch, pg, rows, src=None):
    s3._real(monkeypatch, pg, setup(rows))
    rec = ac.source_declared_check("bg_transit_rules", src or SRC, "t_rules", COLS, rows=len(rows), keys=[["graha", "rule_type", "primary_house"]])
    return rec["Ldgr.source_presence"]


SIX = [("rahu", "favourable", 3, 9), ("rahu", "favourable", 6, 12), ("rahu", "favourable", 11, 5), ("ketu", "favourable", 3, 9), ("ketu", "favourable", 6, 12), ("ketu", "favourable", 11, 5)]


# ───────────────────────── the declaration ─────────────────────────

def test_the_committed_declaration_is_valid_and_names_the_rows():
    sc = SRC["columns"][0]["split_citation"]
    assert ac.source_declaration_problem(SRC, None, 'bg_transit_rules') is None and sc["vedha_prefix"] == ac.SPLIT_VEDHA_PREFIX
    assert [c["column"] for c in sc["applies_to"]] == ["rule_type", "graha", "vedha_house"] and "ND-NODE-VEDHA" in sc["why"]
    assert "split_citation" in ac.SOURCE_COLUMN_FIELDS
    doc = json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))
    assert doc["source_column_declaration_fields"] == list(ac.SOURCE_COLUMN_FIELDS)
    assert [a for a, e in DECLS.items() if any(isinstance(c, dict) and c.get("split_citation") for c in ((e.get("source") or {}).get("columns") or []))] == ["bg_transit_rules"]


def _with(**kw):
    s = copy.deepcopy(SRC)
    sc = s["columns"][0]["split_citation"]
    for k, v in kw.items():
        if v is KeyError:
            sc.pop(k)
        else:
            sc[k] = v
    return s


@pytest.mark.parametrize("kw", [
    dict(vedha_prefix="UNSOURCED (partner:"), dict(vedha_prefix="UNSOURCED"), dict(vedha_prefix=KeyError), dict(applies_to=[]), dict(applies_to="graha"),
    dict(applies_to=[{"column": "graha", "equals": "rahu"}, {"column": "graha", "in": ["ketu"]}]),
    dict(applies_to=[{"column": "graha", "equals": "rahu", "in": ["ketu"]}]), dict(applies_to=[{"column": "graha"}]), dict(applies_to=[{"column": "graha", "equals": " "}]),
    dict(applies_to=[{"column": "graha", "in": []}]), dict(applies_to=[{"column": "vedha_house", "not_null": False}]), dict(applies_to=[{"column": "g;drop", "equals": "x"}]),
    dict(why="placeholder text for the reason"), dict(why="vedha"), dict(why="a long reason that never says which part stays open"),
    dict(evidence="unverified:somewhere"), dict(evidence="platform/python-sidecar/services/gochara_rules/vedha_derive.py"), dict(evidence="no/such/file.py:1"),
    dict(extra=1),
])
def test_a_malformed_split_citation_is_refused(kw):
    assert ac.source_declaration_problem(_with(**kw), None, 'bg_transit_rules'), kw


def test_split_citation_belongs_to_a_k1_only_entry():
    s = copy.deepcopy(SRC)
    s["columns"][0]["kinds"] = ["K1", "K2"]
    assert "K1 alone" in ac.source_declaration_problem(s, None, "bg_transit_rules")
    s["columns"][0]["kinds"] = ["K2"]
    assert "K1 alone" in ac.source_declaration_problem(s, None, "bg_transit_rules")


# ───────────────────────── the exception exists for ONE table and column ─────────────────────────

@pytest.mark.parametrize("aid,col", [("bg_compendium_index", "classical_citation"), ("bg_concordance", "source_citation"), ("bg_dasha_systems", "classical_citations"),
                                      ("bg_transit_rules", "rule_notes"), (None, "classical_citation")])
def test_copying_the_declaration_onto_another_asset_or_column_is_refused(aid, col):
    s = copy.deepcopy(SRC)
    s["columns"][0]["column"] = col
    why = ac.source_declaration_problem(s, None, aid)
    assert why and "SPLIT_ALLOWED" in why, (aid, col, why)
    assert ac.SPLIT_ALLOWED == {("bg_transit_rules", "classical_citation")}
    with pytest.raises(ac.DeclarationsError, match="SPLIT_ALLOWED"):
        doc = copy.deepcopy(json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8")))
        doc["assets"]["bg_dasha_systems"]["source"] = copy.deepcopy(SRC)
        ac.validate_declarations(doc)


def test_source_declared_check_refuses_it_for_another_asset_without_reading():
    rec = ac.source_declared_check("bg_concordance", SRC, "t_rules", COLS, rows=1)["Ldgr.source_presence"]
    assert rec["v"] == NO_DET and "SPLIT_ALLOWED" in rec["measured"]


# ───────────────────────── real SQL ─────────────────────────

@pytest.mark.parametrize("pad", [False, True])
def test_REAL_SQL_the_six_split_rows_are_sourced_and_counted(monkeypatch, disposable_pg, pad):
    rows = [(g, rt, ph, vh, good(sl="24" if g == "rahu" else "2", locus="phaladeepika:PG331:C1" if g == "rahu" else "phaladeepika:PG321:C1")) for g, rt, ph, vh in SIX]
    rows += [("sun", "favourable", 3, 9, BPHS), ("sun", "unfavourable", 2, None, "Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)")]
    rec = run(monkeypatch, disposable_pg, rows)
    assert rec["v"] == PASS, rec["measured"]
    assert rec["source"]["rows"] == 8 and rec["source"]["lacking"] == 0 and rec["source"]["split_citation_rows"] == 6 and rec["source"]["split_citation_ok"] == 6
    assert "6 row(s) carry a split-shaped citation" in rec["measured"] and "6 of them pass on the K1 part" in rec["measured"] and "ND-NODE-VEDHA" in rec["measured"]


NEGATIVES = {
    "old long UNSOURCED text": "UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus",
    "bare UNSOURCED": "UNSOURCED",
    "wrong prefix word": good().replace("(vedha partner:", "(partner:"),
    "no K1 part": VEDHA,
    "missing machine locus": f'{VEDHA} — transit result: Phaladīpikā Adh. XXVI, Śl. 24 "effects caused by Rahu"',
    "missing quotes on the excerpt": good().replace('"effects caused by Rahu ... (3) happiness"', "effects caused by Rahu"),
    "excerpt over 25 words": good(excerpt=" ".join(f"w{i}" for i in range(26))),
    "blank excerpt": good(excerpt=" "),
    "locus words are a placeholder": good().replace("Phaladīpikā Adh. XXVI, Śl. 24", "n/a"),
    "machine locus does not resolve (no such page)": good(locus="phaladeepika:PG9999:C1"),
    "machine locus does not resolve (no such text)": good(locus="no_such_text:PG331:C1"),
    "machine locus malformed": good(locus="phaladeepika:331"),
    "trailing text after the excerpt": good() + " extra",
    "lower-case unsourced": good().replace("UNSOURCED", "unsourced"),
    "vedha text with parentheses": good().replace("inference, not in the cited verses", "inference (not in the verses)"),
    "NULL": None,
    "tab-only excerpt": good(excerpt="\t"),
    "newline-only excerpt": good(excerpt="\n"),
    "NBSP-only excerpt": good(excerpt="\u00a0\u00a0"),
    "NBSP-joined 30 words": good(excerpt="\u00a0".join(f"w{i}" for i in range(30))),
    "tab-joined 30 words": good(excerpt="\t".join(f"w{i}" for i in range(30))),
    "blank vedha text": good().replace("inference, not in the cited verses", " "),
    "NBSP-only vedha text": good().replace("inference, not in the cited verses", "\u00a0"),
    "punctuation-only excerpt": good(excerpt="... --"),
}


@pytest.mark.parametrize("why", sorted(NEGATIVES))
def test_REAL_SQL_every_other_shape_stays_a_placeholder(monkeypatch, disposable_pg, why):
    rows = [(g, rt, ph, vh, good()) for g, rt, ph, vh in SIX[:5]] + [("ketu", "favourable", 11, 5, NEGATIVES[why])]
    rec = run(monkeypatch, disposable_pg, rows)
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 1 and rec["source"]["rows"] == 6, (why, rec["measured"])


@pytest.mark.parametrize("row", [
    ("sun", "favourable", 3, 9),            # not a node
    ("rahu", "unfavourable", 3, 9),         # not the favourable rule type
    ("rahu", "favourable", 3, None),        # no vedha house
    ("Rahu", "favourable", 3, 9),           # a spelling the predicate does not list
])
def test_REAL_SQL_the_split_shape_on_a_row_the_predicate_does_not_select_is_a_placeholder(monkeypatch, disposable_pg, row):
    g, rt, ph, vh = row
    rows = [(g2, rt2, ph2, vh2, good()) for g2, rt2, ph2, vh2 in SIX[:5]] + [(g, rt, ph, vh, good())]
    rec = run(monkeypatch, disposable_pg, rows)
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 1, rec["measured"]


def test_REAL_SQL_an_entry_without_split_citation_keeps_the_split_shape_a_placeholder(monkeypatch, disposable_pg):
    plain = copy.deepcopy(SRC)
    plain["columns"][0].pop("split_citation")
    rows = [(g, rt, ph, vh, good()) for g, rt, ph, vh in SIX]
    rec = run(monkeypatch, disposable_pg, rows, src=plain)
    assert rec["v"] == FAIL and rec["source"]["lacking"] == 6 and "split_citation_rows" not in rec["source"]


def test_REAL_SQL_the_old_unsourced_rows_still_fail_exactly_as_before(monkeypatch, disposable_pg):
    old = "UNSOURCED — no house-transit vedha doctrine for Rahu/Ketu found anywhere in the served corpus (Phaladipika Adh. XXVI slokas 3-8, phaladeepika:PG322:C1-PG323:C1)"
    rows = [(g, rt, ph, vh, old) for g, rt, ph, vh in SIX] + [("sun", "favourable", 3, 9, BPHS)]
    rec = run(monkeypatch, disposable_pg, rows)
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 6 and rec["source"]["split_citation_rows"] == 0


def test_REAL_SQL_a_declared_column_the_table_lacks_fails_before_any_read(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, setup([("rahu", "favourable", 3, 9, good())]))
    rec = ac.source_declared_check("bg_transit_rules", SRC, "t_rules", [c for c in COLS if c != "vedha_house"], rows=1)["Ldgr.source_presence"]
    assert rec["v"] == FAIL and "vedha_house" in rec["measured"]


def test_REAL_SQL_a_non_text_column_is_refused_not_guessed(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, ["CREATE TEMP TABLE t_rules (id int, graha text, rule_type text, primary_house int, vedha_house int, classical_citation jsonb) ON COMMIT DROP;",
                                          "INSERT INTO t_rules VALUES (1, 'rahu', 'favourable', 3, 9, '\"x\"');"])
    rec = ac.source_declared_check("bg_transit_rules", SRC, "t_rules", COLS, rows=1)["Ldgr.source_presence"]
    assert rec["v"] == NO_DET and "not a text column" in rec["measured"]


def test_REAL_SQL_the_record_counts_the_rows_that_pass_the_k1_part_separately_from_the_shaped_rows(monkeypatch, disposable_pg):
    rows = [(g, rt, ph, vh, good()) for g, rt, ph, vh in SIX[:4]] + [("ketu", "favourable", 6, 12, good(locus="phaladeepika:PG9999:C1")), ("ketu", "favourable", 11, 5, good(excerpt="\t"))]
    rec = run(monkeypatch, disposable_pg, rows)
    assert rec["v"] == PARTIAL and rec["source"]["lacking"] == 2
    assert rec["source"]["split_citation_rows"] == 6 and rec["source"]["split_citation_ok"] == 4          # six are split-shaped; only four pass on the K1 part
    assert "6 row(s) carry a split-shaped citation" in rec["measured"] and "4 of them pass on the K1 part" in rec["measured"]
    assert "machine locus resolves on" not in rec["measured"]


# ───────────────────────── the Python mirror agrees with the SQL on every shape ─────────────────────────

def test_REAL_SQL_the_python_mirror_and_the_sql_judge_every_shape_alike(monkeypatch, disposable_pg):
    chunks = {"phaladeepika_pg0331_c01", "phaladeepika_pg0321_c01"}
    cases = {"good": good(), "good ketu": good("2", "phaladeepika:PG321:C1", "Sun gives good results")}
    cases.update({k: v for k, v in NEGATIVES.items() if v is not None})
    for name, text in cases.items():
        rows = [("rahu", "favourable", 3, 9, text)]
        rec = run(monkeypatch, disposable_pg, rows)
        py_ok = ac.split_citation_k1_problem(text, chunks) is None
        sql_ok = rec["v"] == PASS
        assert py_ok == sql_ok, (name, ac.split_citation_k1_problem(text, chunks), rec["measured"])
