"""test_c1_2_paired_enumeration.py: C1-2 (SS N-101; design /Users/Dev/suvarna-evidence/L0_WAVE/C1_CARR_DESIGN.md section 2, kernel K2): the `paired_enumeration_v1` D1 kernel
(the vedha malefic-count scale: two lists joined by "respectively").

Ordinary tests on REAL fixtures: the five rows are the writer's own `MALEFIC_SCALE_ROWS` (platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py, imported by path) and the
passage is the verbatim PG353 text that module's docstring records as read from `classical_text_chunks` (chunk phaladeepika_pg0353_c01). The stored chunk hash of the LIVE chunk
is not committed anywhere, so the fixture chunk carries a hash computed from this text (a fixture, labelled as one); a read-only export of the live chunk is the one input
the real declaration still needs. No database. No declaration of any asset is filled by this file: the spec below lives in the test.
"""
from __future__ import annotations

import copy
import importlib.util
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import carriage_d1 as d1  # noqa: E402

REPO = HERE.parents[3]
_p = REPO / "platform" / "python-sidecar" / "brahmagyan" / "l0_phaladeepika_vedha.py"
_spec_mod = importlib.util.spec_from_file_location("l0_phaladeepika_vedha_for_test", _p)
VEDHA = importlib.util.module_from_spec(_spec_mod)
_spec_mod.loader.exec_module(VEDHA)

TABLE = "bg_vedha_malefic_scale"
CID = "phaladeepika_pg0353_c01"
PASSAGE = ("When at the time of a battle, there is a (Vedha) caused by one, two, three, four or five malefics, the corresponding effects will be fear, failure, "
           "killing (blood-shed), death and ignominy respectively.")
CHUNK = {"chunk_id": CID, "text_id": "phaladeepika", "content_en": "Adh. XXVI " + PASSAGE, "content_sa": None}
CHUNK["content_sha256"] = d1.preimages("phaladeepika", CHUNK["content_en"])["text_id::content_en"]
SUFFIX = VEDHA._PG349_DISAMBIGUATION.strip()
KEYWORDS = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five"}
PHRASES = {"1": "one malefic", "2": "two malefics", "3": "three malefics", "4": "four malefics", "5": "five malefics"}
STATE = "sourced_ocr_unverified"
SRC = "platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:92"


def spec(**over):
    s = dict(matcher=d1.PAIRED, table=TABLE, chunk_ids=[CID], span={"start": "When at the time of a battle"}, expected_rows=5,
             fields={"key": "malefic_count", "value": "effect_grade"}, key_words=dict(KEYWORDS),
             key_list={"after": "caused by", "before": "malefics"}, value_list={"after": "will be", "before": "respectively"},
             description={"column": "effect_description", "template": "Vedha caused by {key_phrase}: {grade}.", "key_phrases": dict(PHRASES), "grade_phrases": {"3": "killing (blood-shed)"},
                          "suffix": SUFFIX, "suffix_evidence": SRC},
             extra_fields=[{"column": "verse_ref", "kind": "equals", "value": VEDHA._VERSE_REF_PG353}])
    s.update(copy.deepcopy(over))
    return s


def rows():
    return [dict(malefic_count=n, effect_grade=g, effect_description=desc, verse_ref=VEDHA._VERSE_REF_PG353, source_citation=VEDHA._CITATION_PG353,
                 table_version=VEDHA.TABLE_VERSION) for n, g, desc in VEDHA.MALEFIC_SCALE_ROWS]


def measure(sp=None, rs=None, chunk=None, state=STATE, **kw):
    return d1.d1_measure(sp if sp is not None else spec(), state, {CID: copy.deepcopy(chunk or CHUNK)}, copy.deepcopy(rs if rs is not None else rows()), TABLE, **kw)


def test_real_rows_and_passage_pass():
    m = measure()
    assert m["v"] == "PASS", m["measured"]
    ev = m["d1"]
    assert ev["rows_total"] == 5 and ev["rows_matched"] == 5 and ev["unmatched"] == [] and ev["row_count_ok"] is True
    assert ev["matcher"] == d1.PAIRED and "respectively" in ev["matching_rule"]
    assert ev["passage"].startswith("When at the time of a battle")
    assert set(ev["rows"][0]["result"]) == {"key", "value", "pair", "effect_description", "verse_ref"}


def test_spec_validates_and_unknown_field_is_refused():
    d1.validate_spec(spec(), "x")
    with pytest.raises(d1.SpecError, match="unknown field"):
        d1.validate_spec(spec(direction_words={"a": "b"}), "x")


def test_swapped_grades_fail_by_position():
    rs = rows()
    rs[1]["effect_grade"], rs[2]["effect_grade"] = rs[2]["effect_grade"], rs[1]["effect_grade"]
    m = measure(rs=rs)
    assert m["v"] == "PARTIAL"
    failed = {u["row"]: u["failed"] for u in m["d1"]["unmatched"]}
    assert set(failed) == {"killing", "failure"} and all("pair" in f for f in failed.values())      # the words are in the passage; their POSITIONS are wrong


def test_grade_not_in_passage_fails():
    rs = rows()
    rs[0]["effect_grade"] = "fright"
    m = measure(rs=rs)
    assert m["v"] == "PARTIAL" and m["d1"]["unmatched"][0]["failed"] == ["value", "pair", "effect_description"]


def test_declared_gloss_must_be_the_passage_item():
    sp = spec()
    sp["description"]["grade_phrases"]["3"] = "killing (bloodshed)"            # not the passage's item: the declared rendering is refused, so the row's description cannot match
    m = measure(sp=sp)
    assert m["v"] == "PARTIAL" and m["d1"]["unmatched"][0]["failed"] == ["effect_description"]
    sp = spec()
    sp["description"].pop("grade_phrases")                                      # without the declared gloss the writer's own third description is not the rendering
    assert measure(sp=sp)["v"] == "PARTIAL"


def test_gloss_is_not_part_of_the_name():
    rs = rows()
    rs[2]["effect_grade"] = "killing (blood-shed)"
    assert measure(rs=rs)["v"] == "PARTIAL"            # the stored label must be the item's name, not its gloss


def test_dropped_extra_and_duplicate_rows():
    assert measure(rs=rows()[:4])["v"] == "PARTIAL"
    extra = rows() + [dict(rows()[0], malefic_count=6, effect_grade="grief")]
    assert measure(rs=extra)["v"] == "PARTIAL"
    dup = rows()
    dup[4] = copy.deepcopy(dup[3])
    m = measure(rs=dup)
    assert m["v"] == "PARTIAL" and any("duplicate" in u["failed"] for u in m["d1"]["unmatched"])


def test_description_must_equal_its_rendering():
    for mutate in (lambda d: d.replace("fear", "dread"), lambda d: d + " extra", lambda d: d.replace(" (This is", " (That is"), lambda d: d.split(":")[0]):
        rs = rows()
        rs[0]["effect_description"] = mutate(rs[0]["effect_description"])
        m = measure(rs=rs)
        assert m["v"] == "PARTIAL" and m["d1"]["unmatched"][0]["failed"] == ["effect_description"]


def test_constant_extra_column_is_checked():
    rs = rows()
    rs[3]["verse_ref"] = "Adh.XXVI PG349"
    m = measure(rs=rs)
    assert m["v"] == "PARTIAL" and m["d1"]["unmatched"][0]["failed"] == ["verse_ref"]


def test_pairing_must_be_readable_in_the_passage():
    # a value list that is one item short: 'respectively' no longer pairs equal lists
    short = dict(CHUNK, content_en="Adh. XXVI " + PASSAGE.replace("killing (blood-shed), ", ""))
    short["content_sha256"] = d1.preimages("phaladeepika", short["content_en"])["text_id::content_en"]
    m = measure(chunk=short)
    assert m["v"] == "NO_DETECTOR" and "pairs equal lists" in m["measured"]
    # the pairing word absent: the span has no 'respectively'
    noresp = dict(CHUNK, content_en="Adh. XXVI " + PASSAGE.replace("respectively", "in turn"))
    noresp["content_sha256"] = d1.preimages("phaladeepika", noresp["content_en"])["text_id::content_en"]
    assert measure(chunk=noresp)["v"] == "NO_DETECTOR"
    # a marker that occurs twice is ambiguous
    twice = dict(CHUNK, content_en="Adh. XXVI caused by " + PASSAGE)
    twice["content_sha256"] = d1.preimages("phaladeepika", twice["content_en"])["text_id::content_en"]
    assert measure(sp=spec(span={"start": "Adh. XXVI"}), chunk=twice)["v"] == "NO_DETECTOR"


def test_expected_rows_must_equal_the_passage_pairs():
    sp = spec(expected_rows=4)
    sp["key_words"].pop("5")
    sp["description"]["key_phrases"].pop("5")
    m = measure(sp=sp)
    assert m["v"] == "NO_DETECTOR" and "pairs 5 items" in m["measured"]


@pytest.mark.parametrize("mutate,msg", [
    (lambda s: s.__setitem__("value_list", {"after": "will be", "before": "in turn"}), "pairing word"),
    (lambda s: s.__setitem__("key_words", {"1": "one"}), "key_words"),
    (lambda s: s.__setitem__("fields", {"key": "malefic_count", "value": "malefic_count"}), "fields"),
    (lambda s: s["description"].__setitem__("template", "Vedha {key_phrase}"), "template"),
    (lambda s: s["description"].pop("suffix_evidence"), "suffix"),
    (lambda s: s["description"]["key_phrases"].__setitem__("1", "malefic one"), "key_phrases"),
    (lambda s: s["extra_fields"].append({"column": "pair", "kind": "equals", "value": "x"}), "extra_fields"),
    (lambda s: s["extra_fields"][0].__setitem__("kind", "passage_text"), "extra_fields"),
])
def test_spec_refusals(mutate, msg):
    s = spec()
    mutate(s)
    with pytest.raises(d1.SpecError, match=msg):
        d1.validate_spec(s, "x")


def test_citation_cap_and_unreadable_chunk():
    assert measure(state="unsourced")["v"] == "NO_DETECTOR"
    bad = dict(CHUNK, content_sha256="0" * 64)
    assert measure(chunk=bad)["v"] == "NO_DETECTOR"


def test_column_ledger_caps_undeclared_text_columns():
    f = lambda t, c: dict(t=t, c=c, ec=None, et=None)
    types = {"table_version": f("text", "S"), "effect_grade": f("text", "S"), "effect_description": f("text", "S"), "verse_ref": f("text", "S"),
             "source_citation": f("text", "S"), "malefic_count": f("int2", "N")}
    m = measure(ledger=dict(columns=types, prose_columns=[]))
    assert m["v"] == "PARTIAL" and "table_version" in m["measured"] and "source_citation" in m["measured"]
    nc = [{"column": "table_version", "why": "table_version is the seed-set version label the writer binds to every row, a key, no classical claim",
           "evidence": "platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:72"},
          {"column": "source_citation", "why": "source_citation is the per-row provenance pointer naming the page, not a transcribed claim of the passage",
           "evidence": "platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py:80"}]
    m = measure(sp=spec(non_claim_columns=nc), ledger=dict(columns=types, prose_columns=[]))
    assert m["v"] == "PASS", m["measured"]


def test_prose_coverage_names_the_passage_columns():
    assert d1.prose_coverage(spec()) == {"effect_grade": "value", "effect_description": "effect_description"}


def test_latta_kernel_unchanged():
    assert d1.MATCHER in d1.KERNELS and set(d1.KERNELS) == {d1.MATCHER, d1.PAIRED} and set(d1.KERNELS) == set(d1.MATCHERS)
