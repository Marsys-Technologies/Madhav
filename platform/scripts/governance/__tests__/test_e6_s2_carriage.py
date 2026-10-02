"""test_e6_s2_carriage.py: E6 S2 (SS N-72 S2, N-73): declared carriage + the generic D1 (source correspondence) detector.

An asset declares ONE carriage check chosen by its NATURE (transcription -> D1, computation -> D3, derivation -> D2); the validator
refuses a mismatch; the other two read N/A by the declaration-keyed cause `not-the-declared-carriage`; D1 is measured by the
engine in carriage_d1.py against the declared passage (verified by its stored hash) and PASSES only if every row matches. The
Phaladipika latta (8 rows transcribed from Phaladipika Sloka 42-44) is the first instance, as a FIXTURE (no real asset declares a
carriage check yet). Offline; no database."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402
import carriage_d1 as d1  # noqa: E402
import test_e6_a_na_causes as na_causes  # noqa: E402
import test_e6_na_r01_03 as r13  # noqa: E402

EVID = "00_ARCHITECTURE/briefs/suvarna/layers/L0/assets/bg_phaladeepika_latta_ELEVATION_BRIEF_v1_0.md"
FX = json.loads((HERE / "fixtures" / "phaladeepika_latta_d1_fixture.json").read_text(encoding="utf-8"))
CHUNKS = {c["chunk_id"]: c for c in FX["classical_text_chunks"]}
ROWS = FX["bg_phaladeepika_latta"]
IDS = ["phaladeepika_pg0338_c01", "phaladeepika_pg0339_c01"]
COND = dict(text="If, when thus counting, the tJanmunukshatra. natal star) happens to come as the Latta star, there will be sickness and anguish.",
            start="If, when thus counting", end="sickness and anguish.")
SPEC = dict(matcher=d1.MATCHER, table="bg_phaladeepika_latta", chunk_ids=IDS, span=dict(start="Sloka 42-44"),
            fields=dict(claimant="graha", count="count_from_graha", direction="direction", effect="effect_description"),
            direction_words={"forward": "forward", "backward": "rear"}, anchor_stems=["Latt", "Latin"], effect_marker="Shkos",
            effect_end="Thus the separate effects",
            effect_frame_words=["will", "may", "in", "during", "be", "bo", "occur", "the", "there", "a", "result", "mark"],
            effect_clauses={
                "Sun": dict(clause="During the Sun's Latin there will bo the ruin of every business", effect="Ruin of every business."),
                "Rahu": dict(clause="Misery will result during the Latta of Rahu and Ketu", effect="Misery."),
                "Jupiter": dict(clause="In the Latin of Jupiter/ death, ruin of relations and a sort of general fear or insecurity may occur",
                                effect="Death, ruin of relations and a sort of general fear or insecurity may occur."),
                "Venus": dict(clause="There will be quarrel in the Latta of Venus", effect="Quarrel."),
                "Mercury": dict(clause="In Mercury's Latta will occur loss of position or similar untoward event",
                                effect="Loss of position or similar untoward event."),
                "Moon": dict(clause="A great loss will mark the Moon's Latta", effect="A great loss.")},
            effect_clauses_evidence=EVID,
            expected_rows=8,
            extra_fields=[dict(column="affliction_condition", kind="passage_text",
                               anchors=["when thus counting", "natal star", "Latta star", "sickness and anguish"],
                               condition=COND, condition_evidence=EVID,
                               repairs={"Janma-nakshatra": "tJanmunukshatra"}),
                          dict(column="verse_ref", kind="equals", value="Adh.XXVI PG338-339 Sloka 42-44")])
STORED_HASHES = {"phaladeepika_pg0338_c01": "028354a7b1cf72de839bfe87ce2caa8dac5ac86bc09e45247b7131cb01cb5b60",
                 "phaladeepika_pg0339_c01": "870d228be22cf486c1224091ba359aac99bf22a6160dfaec741e4c8c8eb61e44"}
CAR_D1 = dict(applies="D1", nature="transcription", why="eight rows transcribed from Phaladipika Adh. XXVI Sloka 42-44",
              evidence=EVID,
              citation_state="sourced_ocr_unverified", spec=SPEC)
NA, NO_DET = ac.NA, ac.NO_DET
S2_RULES = {f"Carr.D{i}#measured:not-the-declared-carriage": "test" for i in (1, 2, 3)}


def _rehash(c):
    c = dict(c)
    c["content_sha256"] = hashlib.sha256(f"{c['text_id']}::{c['content_en']}".encode("utf-8")).hexdigest()
    return c


def _measure(rows=ROWS, chunks=CHUNKS, spec=SPEC, table="bg_phaladeepika_latta", state="sourced_ocr_unverified"):
    return d1.d1_measure(spec, state, chunks, copy.deepcopy(rows), table)


# ───────────────────────── the fixture itself ─────────────────────────

def test_the_fixture_pins_the_chunk_content_and_the_stored_hash_not_the_export_files_hash():
    """The export file's own hash is provenance only (the production session appended a note and a flag to the chunk rows)."""
    assert FX["_source"]["provenance_only"] is True and "sha256" not in FX["_source"]
    assert {k: c["content_sha256"] for k, c in CHUNKS.items()} == STORED_HASHES
    for c in CHUNKS.values():
        v = d1.verify_chunk(c)
        assert v["verified"] and v["preimage"] == "text_id::content_en", v
        assert hashlib.sha256(f"{c['text_id']}::{c['content_en']}".encode("utf-8")).hexdigest() == c["content_sha256"]


# ───────────────────────── the D1 engine ─────────────────────────

def test_d1_all_eight_latta_rows_match_and_the_record_states_what_it_proves():
    r = _measure()
    assert r["v"] == "PASS" and r["citation_state"] == "sourced_ocr_unverified"
    e = r["d1"]
    assert e["rows_total"] == 8 and e["rows_matched"] == 8 and e["unmatched"] == [] and e["translation_only"] is True
    assert [c["chunk_id"] for c in e["chunks"]] == IDS and all(c["verified"] and c["preimage"] == "text_id::content_en" for c in e["chunks"])
    assert len(e["passage_sha256"]) == 64 and e["content_sa_all_null"] is True
    assert r["d1"]["pass_basis"] == "sourced_ocr_unverified" and "D1 PASS (citation_state sourced_ocr_unverified)" in r["measured"]
    assert any("classical_text_chunks" in x for x in r["d1"]["reads"]) and any("own table" in x for x in r["d1"]["reads"])   # both stated reads
    for needle in ("ENGLISH translation", "content_sa", "NULL", "OCR text not checked against the printed book", "text_id-prefixed",
                   "sourced_ocr_unverified"):
        assert needle in r["measured"], needle


@pytest.mark.parametrize("name, mutate, row", [
    ("Moon 22 -> 21", lambda rs: [r.update(count_from_graha=21) for r in rs if r["graha"] == "Moon"], "Moon"),
    ("Sun forward -> backward", lambda rs: [r.update(direction="backward") for r in rs if r["graha"] == "Sun"], "Sun"),
    ("Rahu effect = Quarrel", lambda rs: [r.update(effect_description="Quarrel.") for r in rs if r["graha"] == "Rahu"], "Rahu"),
    ("Mars effect invented", lambda rs: [r.update(effect_description="Misery.") for r in rs if r["graha"] == "Mars"], "Mars"),
    ("Venus 5 -> 6", lambda rs: [r.update(count_from_graha=6) for r in rs if r["graha"] == "Venus"], "Venus"),
    ("Mercury 7 -> 8", lambda rs: [r.update(count_from_graha=8) for r in rs if r["graha"] == "Mercury"], "Mercury"),
    ("Sun 12 -> 2 (a digit inside 12th is not the ordinal 2nd)", lambda rs: [r.update(count_from_graha=2) for r in rs if r["graha"] == "Sun"], "Sun"),
    ("Sun 12 -> 1", lambda rs: [r.update(count_from_graha=1) for r in rs if r["graha"] == "Sun"], "Sun"),
])
def test_d1_a_seeded_wrong_row_is_never_a_pass_and_is_named(name, mutate, row):
    rows = copy.deepcopy(ROWS)
    mutate(rows)
    r = _measure(rows=rows)
    assert r["v"] == "PARTIAL", name
    assert [u["row"] for u in r["d1"]["unmatched"]] == [row] and row in r["measured"]


def test_d1_a_null_effect_is_a_miss_where_the_passage_gives_that_claimant_an_effect():
    rows = copy.deepcopy(ROWS)
    [r.update(effect_description=None) for r in rows if r["graha"] == "Rahu"]          # the passage states Rahu's effect
    r = _measure(rows=rows)
    assert r["v"] == "PARTIAL" and [u["row"] for u in r["d1"]["unmatched"]] == ["Rahu"] and r["d1"]["unmatched"][0]["failed"] == ["effect"]


def test_d1_swapped_counts_name_both_rows_and_a_ketu_row_fails():
    rows = copy.deepcopy(ROWS)
    for r in rows:
        if r["graha"] in ("Sun", "Saturn"):
            r["count_from_graha"] = 8 if r["graha"] == "Sun" else 12
    assert sorted(u["row"] for u in _measure(rows=rows)["d1"]["unmatched"]) == ["Saturn", "Sun"]
    ketu = copy.deepcopy([r for r in ROWS if r["graha"] == "Rahu"][0])
    ketu["graha"] = "Ketu"
    r = _measure(rows=ROWS + [ketu])
    assert r["v"] == "PARTIAL" and [u["row"] for u in r["d1"]["unmatched"]] == ["Ketu"]


def test_d1_hash_mismatch_is_unreadable_never_pass():
    ch = copy.deepcopy(CHUNKS)
    ch[IDS[0]]["content_en"] = ch[IDS[0]]["content_en"] + " tampered"          # stored hash no longer matches
    r = _measure(chunks=ch)
    assert r["v"] == NO_DET and "unreadable" in r["measured"] and IDS[0] in r["measured"]
    assert r["d1"]["chunks"][0]["verified"] is False and "matches neither" in r["d1"]["chunks"][0]["reason"]


def test_d1_the_plain_preimage_is_accepted_and_named_and_a_wrong_hash_is_not():
    ch = copy.deepcopy(CHUNKS)
    for c in ch.values():
        c["content_sha256"] = hashlib.sha256(c["content_en"].encode("utf-8")).hexdigest()
    r = _measure(chunks=ch)
    assert r["v"] == "PASS" and {c["preimage"] for c in r["d1"]["chunks"]} == {"content_en"} and "content_en preimage" in r["measured"]
    ch[IDS[1]]["content_sha256"] = "0" * 64
    assert _measure(chunks=ch)["v"] == NO_DET


@pytest.mark.parametrize("field, value", [("content_sha256", None), ("content_sha256", "xyz"), ("content_en", ""), ("content_en", None),
                                          ("text_id", None)])
def test_d1_an_absent_or_malformed_field_makes_the_chunk_unreadable(field, value):
    ch = copy.deepcopy(CHUNKS)
    ch[IDS[0]][field] = value
    r = _measure(chunks=ch)
    assert r["v"] == NO_DET and "unreadable" in r["measured"]


def test_d1_a_missing_chunk_is_no_detector_and_named():
    ch = {k: v for k, v in CHUNKS.items() if k != IDS[1]}
    r = _measure(chunks=ch)
    assert r["v"] == NO_DET and IDS[1] in r["measured"] and r["d1"]["missing_chunks"] == [IDS[1]]


def test_d1_span_markers_absent_is_no_detector():
    for sp in (dict(start="Sloka 99-100"), dict(start="Sloka 42-44", end="NO SUCH END MARKER")):
        r = _measure(spec=dict(SPEC, span=sp))
        assert r["v"] == NO_DET and "marker" in r["measured"], sp


def test_d1_empty_table_and_unreadable_rows_are_no_detector():
    assert _measure(rows=[])["v"] == NO_DET and "empty" in _measure(rows=[])["measured"]
    r = d1.d1_measure(SPEC, "sourced_ocr_unverified", CHUNKS, None, "bg_phaladeepika_latta")
    assert r["v"] == NO_DET and "could not be read" in r["measured"]


def test_d1_a_table_other_than_the_specs_is_not_guessed():
    r = _measure(table="bg_other")
    assert r["v"] == NO_DET and "does not guess" in r["measured"]


def test_d1_a_malformed_row_is_a_miss_not_a_crash():
    rows = copy.deepcopy(ROWS)
    rows[0].pop("count_from_graha")
    rows[1]["graha"] = None
    r = _measure(rows=rows)
    assert r["v"] == "PARTIAL" and r["d1"]["rows_matched"] == 6


def test_d1_the_match_is_against_the_declared_span_not_the_page_string_of_the_row():
    rows = copy.deepcopy(ROWS)
    for r in rows:
        r["verse_ref"] = "Adh.XXVI PG999 Sloka 1"                       # a misleading per-row page string
    no_label = dict(SPEC, extra_fields=[SPEC["extra_fields"][0]])
    assert _measure(rows=rows, spec=no_label)["v"] == "PASS"            # the claims are matched against the declared span, not the row's page string
    r = _measure(rows=rows)                                             # ... and a declared verse_ref label that differs is itself a miss (MED 7)
    assert r["v"] == "PARTIAL" and {u["failed"][0] for u in r["d1"]["unmatched"]} == {"verse_ref"}
    sp = dict(SPEC, span=dict(start="Sloka 45-46"))                      # a different span: nothing is found there (marker absent)
    assert _measure(spec=sp)["v"] == NO_DET


def test_d1_a_passage_changed_after_certification_changes_the_recorded_passage_digest():
    before = _measure()["d1"]["passage_sha256"]
    ch = copy.deepcopy(CHUNKS)
    ch[IDS[1]]["content_en"] = ch[IDS[1]]["content_en"].replace("Misery will", "Grief will")      # re-ingested with a CONSISTENT new hash
    ch[IDS[1]] = _rehash(ch[IDS[1]])
    r = _measure(chunks=ch)
    assert r["d1"]["passage_sha256"] != before                              # a certificate bound to the old record is stale
    assert r["d1"]["chunks_sha256"] != _measure()["d1"]["chunks_sha256"]     # the stored hashes are kept separately
    assert r["v"] == "PARTIAL"                                               # and the rows no longer all match the changed text
    assert _measure()["d1"]["passage_sha256"] == before


def test_d1_the_passage_digest_is_the_cut_span_as_read_text_outside_the_span_does_not_move_it():
    ch = copy.deepcopy(CHUNKS)
    ch[IDS[0]]["content_en"] = ch[IDS[0]]["content_en"].replace("SATURN, RAHU AND KETU", "SATURN, RAHU AND KETU (edited heading)")
    ch[IDS[0]] = _rehash(ch[IDS[0]])                                         # a consistent re-hash of text BEFORE the span start
    r = _measure(chunks=ch)
    assert r["d1"]["passage_sha256"] == _measure()["d1"]["passage_sha256"] and r["v"] == "PASS"
    assert r["d1"]["chunks_sha256"] != _measure()["d1"]["chunks_sha256"]
    assert r["d1"]["passage_sha256"] == hashlib.sha256(d1.cut_span(d1._ws(" ".join(c["content_en"] for c in ch.values())), SPEC["span"])[0].encode("utf-8")).hexdigest()


def test_d1_content_sa_present_is_reported_not_matched():
    ch = copy.deepcopy(CHUNKS)
    ch[IDS[0]] = _rehash(dict(ch[IDS[0]], content_sa="sanskrit"))
    r = _measure(chunks=ch)
    assert r["d1"]["content_sa_all_null"] is False and "NOT matched" in r["measured"] and r["v"] == "PASS"


def test_d1_the_engine_is_generic_a_second_spec_over_a_second_table_runs():
    """A different table, claimant column and anchor stem through the same engine (no latta constant in the engine)."""
    spec = {k: v for k, v in SPEC.items() if k != "extra_fields"}
    spec.update(table="t_other", fields=dict(claimant="who", count="n", direction="way", effect="what"))
    rows = [dict(who=r["graha"], n=r["count_from_graha"], way=r["direction"], what=r["effect_description"]) for r in ROWS]
    assert d1.d1_measure(spec, "sourced", CHUNKS, rows, "t_other")["v"] == "PASS"


# ───────────────────────── adversarial review: the effect rule (HIGH 2) ─────────────────────────

def _eff(graha, text):
    rows = copy.deepcopy(ROWS)
    [r.update(effect_description=text) for r in rows if r["graha"] == graha]
    return _measure(rows=rows)


@pytest.mark.parametrize("graha, wrong", [
    ("Sun", "Misery."), ("Jupiter", "Quarrel."), ("Venus", "A great loss."), ("Mercury", "Loss."), ("Mercury", "A great loss."),
    ("Rahu", "Ruin of every business."), ("Moon", "Quarrel."), ("Venus", "Loss of position or similar untoward event."),
])
def test_d1_another_claimants_effect_is_a_miss_naming_the_row(graha, wrong):
    r = _eff(graha, wrong)
    assert r["v"] == "PARTIAL" and [(u["row"], u["failed"]) for u in r["d1"]["unmatched"]] == [(graha, ["effect"])]


@pytest.mark.parametrize("text", ["", " ", ".", "a", "...", "ab.", "the", "Loss"])
def test_d1_an_empty_or_too_short_effect_is_a_miss_never_a_match(text):
    r = _eff("Sun", text)
    assert r["v"] == "PARTIAL" and r["d1"]["unmatched"][0]["row"] == "Sun"


def test_d1_trailing_whitespace_in_the_stored_effect_is_normalised_not_a_false_negative():
    assert _eff("Sun", "Ruin of every business.  ")["v"] == "PASS" and _eff("Sun", "  Ruin   of every business.")["v"] == "PASS"


def _mini(**kw):
    s = {k: v for k, v in SPEC.items() if k != "extra_fields"}
    s.update(kw)
    return s


def _eff_of(seg, g, e, spec):
    return d1.match_ordinal_row({"graha": g, "count_from_graha": 1, "direction": "forward", "effect_description": e}, seg, spec)["effect"]


def test_d1_an_effect_must_equal_the_claimants_whole_clause_not_a_window_across_sentences():
    seg = "Shkos During the Sun's Latta there will be grief. Misery will result during the Latta of Rahu. Thus the separate effects"
    spec = _mini(effect_clauses={"Sun": dict(clause="During the Sun's Latta there will be grief", effect="grief."),
                                 "Rahu": dict(clause="Misery will result during the Latta of Rahu", effect="Misery.")})
    assert _eff_of(seg, "Sun", "grief", spec) is True and _eff_of(seg, "Rahu", "Misery", spec) is True
    assert _eff_of(seg, "Sun", "Misery", spec) is False and _eff_of(seg, "Rahu", "grief", spec) is False      # the neighbouring clause's effect
    # a declared clause that is not the passage's clause (tampered or merely a window) is a miss
    assert _eff_of(seg, "Sun", "grief", _mini(effect_clauses={"Sun": dict(clause="there will be grief", effect="grief.")})) is False
    assert _eff_of(seg, "Sun", "grief", _mini(effect_clauses={"Sun": dict(clause="During the Sun's Latta there will be grief. Misery", effect="grief.")})) is False


def test_d1_the_anchor_must_be_near_and_in_the_same_sentence():
    near = "Shkos There will be quarrel in the Latta of Venus."
    far = "Shkos There will be quarrel in " + "thus it is said by many wise men of old " * 6 + "the Latta of Venus."
    stop = "Shkos There will be quarrel. In the Latta of Venus."
    spec = {k: v for k, v in SPEC.items() if k not in ("extra_fields", "effect_end")}
    f = lambda seg: d1.match_ordinal_row({"graha": "Venus", "count_from_graha": 1, "direction": "forward", "effect_description": "quarrel"}, seg, spec)["effect"]
    assert f(near) is True and f(far) is False and f(stop) is False


def test_d1_effect_frame_words_are_part_of_the_stated_rule():
    spec = dict(SPEC, effect_frame_words=[])
    r = _measure(spec=spec)
    assert r["v"] == "PARTIAL" and {u["row"] for u in r["d1"]["unmatched"]} >= {"Moon", "Venus"}      # "A great loss will mark ...": 'will' is a frame word


def test_d1_the_effect_section_is_bounded_by_the_declared_marker_and_end():
    cl = {"Venus": dict(clause="Latta of Venus there will be quarrel here", effect="quarrel here"),
          "Sun": dict(clause="In the Latta of Sun there will be grief", effect="grief.")}
    seg = "Latta of Venus there will be quarrel here. Shkos In the Latta of Sun there will be grief. Thus the separate effects the Latta of Mars in quarrel."
    f = lambda g, e, **kw: _eff_of(seg, g, e, _mini(effect_clauses=cl, effect_frame_words=["will", "be", "in", "the", "there", "here"], **kw))
    assert f("Sun", "grief") is True
    assert f("Venus", "quarrel here", effect_marker="Shkos") is False                 # before the marker: not in the effect section
    seg2 = "Latta of Venus there will be quarrel here. Shkos Latta of Sun will be grief."
    g = lambda **kw: _eff_of(seg2, "Venus", "quarrel here", _mini(effect_clauses=cl, effect_frame_words=["will", "be", "in", "the", "there", "here"], **kw))
    assert g(effect_marker="Latta of Venus") is True and g(effect_marker="Shkos") is False
    cl2 = {"Mars": dict(clause="Thus the separate effects the Latta of Mars there will be quarrel in", effect="quarrel in")}
    seg3 = "Shkos Latta of Sun will be grief. Thus the separate effects the Latta of Mars there will be quarrel in."
    h = lambda **kw: _eff_of(seg3, "Mars", "quarrel in", _mini(effect_clauses=cl2, effect_frame_words=["will", "be", "in", "the", "there", "thus", "separate", "effects"], **kw))
    assert h(effect_end="NO SUCH") is True and h(effect_end="Thus the separate effects") is False


def test_d1_a_declared_effect_marker_or_end_that_is_absent_is_no_detector_not_a_wider_section():
    for key in ("effect_marker", "effect_end"):
        r = _measure(spec=dict(SPEC, **{key: "NO SUCH MARKER"}))
        assert r["v"] == NO_DET and key in r["measured"] and "does not widen" in r["measured"], key


# ───────────────────────── adversarial review: the count rule's guards ─────────────────────────

def test_d1_a_count_that_belongs_to_another_claimant_is_a_miss_the_intervening_ordinal_guard():
    rows = copy.deepcopy(ROWS)
    [r.update(count_from_graha=9) for r in rows if r["graha"] == "Moon"]               # 9th is Rahu's count; "22nd" lies between it and 'that of the Moon'
    r = _measure(rows=rows)
    assert r["v"] == "PARTIAL" and [u["row"] for u in r["d1"]["unmatched"]] == ["Moon"]


def _count(seg, n=5, g="Venus"):
    spec = {k: v for k, v in SPEC.items() if k != "extra_fields"}
    return d1.match_ordinal_row({"graha": g, "count_from_graha": n, "direction": "forward", "effect_description": None}, seg, spec)["count"]


def test_d1_the_count_reach_and_stops_are_bounded():
    assert _count("the 5th star reckoned from that of Venus forward") is True
    assert _count("the 5th " + "x " * 70 + "that of Venus forward") is False                   # > 90 characters between the ordinal and the unit
    assert _count("the 5th star. Next that of Venus forward") is False                         # a full stop ends the clause
    assert _count("the 5th star; next that of Venus forward") is False                         # a semicolon ends the clause


# ───────────────────────── adversarial review: citation_state, evidence, table, completeness (MED 3-7) ─────────────────────────

@pytest.mark.parametrize("state", ["unsourced", "refuted", None, "bogus"])
def test_d1_unsourced_refuted_or_undeclared_citation_state_is_capped_at_no_detector_even_with_every_row_matched(state):
    r = _measure(state=state)
    assert r["v"] == NO_DET and r["d1"]["rows_matched"] == 8 and "cannot tell a contradicted source" in r["measured"]
    assert r["citation_state"] == state


def test_d1_sourced_passes_and_a_sourced_ocr_unverified_pass_is_marked_on_the_record_and_the_cell():
    assert _measure(state="sourced")["v"] == "PASS" and _measure(state="sourced")["d1"]["pass_basis"] == "sourced"
    rec = _measure(state="sourced_ocr_unverified")
    chk = next(c for c in ac.rollup_asset("L0", {"Carr.D1": rec})["Carr"]["checks"] if c["criterion"] == "Carr.D1")
    assert chk["v"] == "PASS" and chk["citation_state"] == "sourced_ocr_unverified"
    assert rec["d1"]["pass_basis"] == "sourced_ocr_unverified" and "citation_state sourced_ocr_unverified" in rec["measured"]


def _carr(d1_record):
    got = {c: ac._na("x", "not-the-declared-carriage") for c in ("Carr.D2", "Carr.D3")}
    got["Carr.D1"] = d1_record
    return ac.rollup_asset("L0", got)["Carr"]


def test_a_bare_d1_pass_or_partial_with_the_other_two_na_does_not_roll_up_to_pass():
    for v in ("PASS", "PARTIAL"):
        cell = _carr(dict(v=v, measured="trust me"))
        assert cell["v"] == NO_DET and "without verified passage evidence" in cell["checks"][0]["reason"], v


@pytest.mark.parametrize("breakage, reason", [
    (lambda r: r["d1"].pop("passage_sha256"), "passage_sha256"),
    (lambda r: r["d1"].update(passage_sha256="xyz"), "passage_sha256"),
    (lambda r: r["d1"].pop("chunks"), "verified chunk ledger"),
    (lambda r: r["d1"].update(chunks=[]), "verified chunk ledger"),
    (lambda r: r["d1"]["chunks"][0].update(verified=False), "verified chunk ledger"),
    (lambda r: r.update(citation_state="unsourced"), "citation_state"),
    (lambda r: r.update(citation_state=None), "citation_state"),
    (lambda r: r["d1"].update(rows_total=0), "no rows"),
    (lambda r: r["d1"].update(unmatched=[dict(row="x", failed=["count"])]), "not every row matched"),
    (lambda r: r["d1"].update(row_count_ok=False), "not every row matched"),
    (lambda r: r.pop("d1"), "no `d1` evidence"),
])
def test_a_d1_record_missing_any_part_of_its_evidence_is_not_honoured(breakage, reason):
    rec = _measure()
    breakage(rec)
    cell = _carr(rec)
    assert cell["v"] == NO_DET and reason in cell["checks"][0]["reason"]


def test_a_genuine_d1_record_with_its_evidence_is_honoured_and_a_genuine_partial_too():
    assert _carr(_measure())["v"] == "PASS"
    rows = copy.deepcopy(ROWS)
    [r.update(count_from_graha=21) for r in rows if r["graha"] == "Moon"]
    assert _carr(_measure(rows=rows))["v"] == "PARTIAL"


def test_d1_an_asset_with_no_table_is_never_measured_against_a_spec_table(fetch):
    assert _measure(table=None)["v"] == NO_DET and "no table" in _measure(table=None)["measured"].lower()
    got = ac.carriage_declared_checks("x", CAR_D1, None)
    assert got["Carr.D1"]["v"] == NO_DET and got["Carr.D2"]["v"] == NA and "does not guess" in got["Carr.D1"]["measured"]


def test_d1_the_row_count_must_equal_the_declared_expected_rows():
    r = _measure(rows=ROWS[:1])
    assert r["v"] == "PARTIAL" and r["d1"]["row_count_ok"] is False and "1 row(s) but 8 are declared" in r["measured"]
    extra = copy.deepcopy(ROWS[0])
    extra["graha"] = "Ketu"
    r = _measure(rows=ROWS + [extra])
    assert r["v"] == "PARTIAL" and "9 row(s) but 8" in r["measured"]
    assert _measure(rows=ROWS[:7] + [copy.deepcopy(ROWS[0])])["d1"]["unmatched"][0]["failed"][-1] == "duplicate"      # 8 rows, one claimant twice


def test_d1_a_duplicate_claimant_is_refused_even_when_both_copies_match():
    r = _measure(rows=ROWS + [copy.deepcopy(ROWS[3])])
    assert r["v"] == "PARTIAL" and [u["failed"] for u in r["d1"]["unmatched"]] == [["duplicate"], ["duplicate"]]


@pytest.mark.parametrize("col, value", [
    ("affliction_condition", "If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be great prosperity."),
    ("affliction_condition", "If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Rahu star, there will be sickness and anguish."),
    ("affliction_condition", ROWS[0]["affliction_condition"] + " The native will also gain a kingdom."),
    ("affliction_condition", None), ("affliction_condition", ""),
    ("verse_ref", "Adh.XXVI PG338-339 Sloka 45-46"), ("verse_ref", None),
])
def test_d1_an_altered_extra_column_is_a_miss(col, value):
    rows = copy.deepcopy(ROWS)
    [r.update({col: value}) for r in rows if r["graha"] == "Sun"]
    r = _measure(rows=rows)
    assert r["v"] == "PARTIAL" and [(u["row"], u["failed"]) for u in r["d1"]["unmatched"]] == [("Sun", [col])]


def test_d1_the_real_affliction_condition_matches_through_the_declared_ocr_repair():
    assert _measure()["v"] == "PASS"
    no_repair = dict(SPEC, extra_fields=[dict(SPEC["extra_fields"][0], repairs={}), SPEC["extra_fields"][1]])
    assert _measure(spec=no_repair)["v"] == "PARTIAL"                                  # without the declared repair the OCR spelling does not match


# ───────────────────────── second adversarial review: the effect must EQUAL the claimant's whole clause ─────────────────────────

# every one of these read PASS on all 8 rows in the second review; each is wrong in substance and must be PARTIAL naming the row
WRONG_EFFECTS = [
    ("Venus", "sort of general fear or insecurity may occur"), ("Venus", "Venus"), ("Venus", "Latta of Venus"), ("Venus", "There will"),
    ("Venus", "There will be quarrel"), ("Venus", "be quarrel"), ("Venus", "a quarrel"), ("Venus", "quarrel in the Latta of Venus"),
    ("Venus", "occur There will be quarrel"), ("Mercury", "Latta"), ("Mercury", "In Mercury's Latta"), ("Mercury", "occur loss of position or similar untoward event"),
    ("Mercury", "Loss of position"), ("Mercury", "untoward event"), ("Mercury", "Loss"), ("Sun", "during"), ("Sun", "Latin"), ("Sun", "Ruin of every business Misery"),
    ("Sun", "the ruin of every business"), ("Sun", "ruin of every business Misery will result"), ("Sun", "ruin of every"), ("Rahu", "result"), ("Rahu", "Rahu and Ketu"),
    ("Rahu", "the ruin of every business Misery will result"), ("Rahu", "Misery will result"), ("Rahu", "Misery will"), ("Moon", "Moon's Latta"), ("Moon", "A great loss will mark"),
    ("Moon", "great loss"), ("Moon", "loss of position or similar untoward event. A great loss will mark"), ("Moon", "mark the"),
    ("Jupiter", "Death"), ("Jupiter", "ruin of relations"), ("Jupiter", "ruin of relations and a sort of general fear or insecurity may occur"),
    ("Jupiter", "Latin of"), ("Jupiter", "fear or insecurity may occur There will be quarrel"),
    ("Jupiter", "Death, ruin of relations and a sort of general fear or insecurity may occur There will be quarrel"),
]


@pytest.mark.parametrize("graha, wrong", WRONG_EFFECTS)
def test_d1_a_borrowed_tail_concatenated_or_frame_only_effect_is_a_miss_naming_the_row(graha, wrong):
    r = _eff(graha, wrong)
    assert r["v"] == "PARTIAL" and [(u["row"], u["failed"]) for u in r["d1"]["unmatched"]] == [(graha, ["effect"])], wrong


@pytest.mark.parametrize("graha, other", [(g, h) for g in ("Sun", "Rahu", "Jupiter", "Venus", "Mercury", "Moon")
                                          for h in ("Sun", "Rahu", "Jupiter", "Venus", "Mercury", "Moon") if g != h])
def test_d1_every_effect_swap_between_claimants_is_a_miss(graha, other):
    eff = next(r["effect_description"] for r in ROWS if r["graha"] == other)
    r = _eff(graha, eff)
    assert r["v"] == "PARTIAL" and [u["row"] for u in r["d1"]["unmatched"]] == [graha]


@pytest.mark.parametrize("graha, variant", [("Sun", "ruin of every business"), ("Sun", "RUIN OF EVERY BUSINESS."), ("Sun", "Ruin of every business!!"),
                                            ("Sun", "  Ruin   of every business.  "), ("Rahu", "MISERY"), ("Rahu", "Misery  ."), ("Venus", "quarrel"),
                                            ("Moon", "a great loss"), ("Mercury", "loss of position or similar untoward event"),
                                            ("Jupiter", "death, ruin of relations and a sort of general fear or insecurity may occur")])
def test_d1_benign_case_spacing_and_punctuation_variants_pass_by_the_stated_normalisation(graha, variant):
    """STATED: the stored effect and the declared effect are compared as lower-case words and digits only, so case, spacing and
    punctuation (a trailing '.', '!!', inner commas) do not matter and NOTHING else does."""
    assert _eff(graha, variant)["v"] == "PASS"


def test_d1_an_effect_made_only_of_anchor_or_frame_words_is_a_miss_even_if_the_spec_declares_it():
    spec = copy.deepcopy(SPEC)
    spec["effect_clauses"]["Venus"] = dict(clause="There will be quarrel in the Latta of Venus", effect="There will")
    rows = copy.deepcopy(ROWS)
    [r.update(effect_description="There will") for r in rows if r["graha"] == "Venus"]
    r = _measure(rows=rows, spec=spec)
    assert r["v"] == "PARTIAL" and [u["row"] for u in r["d1"]["unmatched"]] == ["Venus"]


def test_d1_the_declared_clause_must_be_the_whole_passage_clause_with_only_anchor_and_frame_words_around_the_effect():
    # (a) the declared clause is not the passage's clause
    spec = copy.deepcopy(SPEC)
    spec["effect_clauses"]["Venus"]["clause"] = "There will be quarrel"
    assert _measure(spec=spec)["d1"]["unmatched"][0]["row"] == "Venus"
    # (b) the effect does not cover the clause's content: with 'quarrel' the only content, an effect that leaves a content word out is a miss
    spec = copy.deepcopy(SPEC)
    spec["effect_clauses"]["Mercury"]["effect"] = "Loss of position"
    rows = copy.deepcopy(ROWS)
    [r.update(effect_description="Loss of position") for r in rows if r["graha"] == "Mercury"]
    r = _measure(rows=rows, spec=spec)
    assert r["v"] == "PARTIAL" and [u["row"] for u in r["d1"]["unmatched"]] == ["Mercury"]          # leftover 'or similar untoward event' is content


def test_d1_a_claimant_with_a_stored_effect_but_no_declared_clause_is_a_miss():
    spec = copy.deepcopy(SPEC)
    del spec["effect_clauses"]["Moon"]
    assert [u["row"] for u in _measure(spec=spec)["d1"]["unmatched"]] == ["Moon"]


def test_d1_a_padded_or_differently_cased_claimant_is_normalised_consistently_and_duplicates_are_seen():
    rows = copy.deepcopy(ROWS)
    rows[0]["graha"] = "  " + rows[0]["graha"] + " "
    assert _measure(rows=rows)["v"] == "PASS"                                         # trimmed everywhere, the same way
    rows = copy.deepcopy(ROWS[:7]) + [copy.deepcopy(ROWS[0])]
    rows[7]["graha"] = " " + rows[7]["graha"].upper()
    r = _measure(rows=rows)
    assert r["v"] == "PARTIAL" and all(u["failed"][-1] == "duplicate" for u in r["d1"]["unmatched"]) and len(r["d1"]["unmatched"]) == 2


@pytest.mark.parametrize("cond", [
    "If, when thus counting, the natal star happens not to come as the Latta star, there will be no sickness and anguish.",
    "there will be sickness and anguish natal star when thus counting Latta star",
    "Latta star when thus counting natal star sickness and anguish never come",
    "If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be sickness and anguish and loss.",
    "If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star, there will be anguish and sickness.",
    "If, when thus counting, the Janma-nakshatra (natal star) happens to come as the Latta star",
    "sickness and anguish", "",
])
def test_d1_affliction_condition_is_an_ordered_contiguous_run_of_the_passage_negation_reordering_additions_and_fragments_fail(cond):
    rows = copy.deepcopy(ROWS)
    [r.update(affliction_condition=cond) for r in rows if r["graha"] == "Sun"]
    r = _measure(rows=rows)
    assert r["v"] == "PARTIAL" and [(u["row"], u["failed"]) for u in r["d1"]["unmatched"]] == [("Sun", ["affliction_condition"])]


def test_d1_affliction_condition_case_and_punctuation_variants_of_the_true_text_pass():
    rows = copy.deepcopy(ROWS)
    [r.update(affliction_condition="IF WHEN THUS COUNTING THE JANMA-NAKSHATRA (NATAL STAR) HAPPENS TO COME AS THE LATTA STAR THERE WILL BE SICKNESS AND ANGUISH")
     for r in rows if r["graha"] == "Sun"]
    assert _measure(rows=rows)["v"] == "PASS"


def test_d1_both_effect_markers_are_required_by_the_spec_and_by_the_engine():
    for key in ("effect_marker", "effect_end"):
        spec = {k: v for k, v in SPEC.items() if k != key}
        with pytest.raises(d1.SpecError, match=key):
            d1.validate_spec(spec, "x")
        r = _measure(spec=spec)                                                      # the engine itself never widens an undeclared section
        assert r["v"] == NO_DET and key in r["measured"]


def test_d1_the_spec_requires_the_declared_clause_mapping_and_its_evidence():
    for key in ("effect_clauses", "effect_clauses_evidence", "effect_frame_words"):
        with pytest.raises(d1.SpecError, match=key):
            d1.validate_spec({k: v for k, v in SPEC.items() if k != key}, "x")
    for bad in ({"Sun": dict(clause="x")}, {"Sun": dict(clause="", effect="e")}, {"Sun": dict(clause="c", effect="e", more=1)},
                {"Sun": dict(clause="c", effect="e"), " sun": dict(clause="c", effect="e")}, [], "x"):
        with pytest.raises(d1.SpecError):
            d1.validate_spec(dict(SPEC, effect_clauses=bad), "x")
    with pytest.raises(d1.SpecError):
        d1.validate_spec(dict(SPEC, effect_clauses_evidence=" "), "x")


def test_d1_an_effect_of_only_anchor_words_is_a_miss_even_when_it_is_the_whole_clause():
    seg = "Shkos In the Latta of Venus. Thus the separate effects"
    spec = _mini(effect_clauses={"Venus": dict(clause="In the Latta of Venus", effect="In the Latta of Venus")})
    assert _eff_of(seg, "Venus", "In the Latta of Venus", spec) is False
    spec2 = _mini(effect_clauses={"Venus": dict(clause="In the Latta of Venus quarrel", effect="quarrel")})
    assert _eff_of("Shkos In the Latta of Venus quarrel. Thus the separate effects", "Venus", "quarrel", spec2) is True


def test_d1_a_claimants_anchor_in_two_clauses_is_ambiguous_and_a_miss():
    seg = "Shkos In the Latta of Venus there will be quarrel. During the Latta of Venus there will be grief. Thus the separate effects"
    cl = {"Venus": dict(clause="In the Latta of Venus there will be quarrel", effect="quarrel")}
    spec = _mini(effect_clauses=cl)
    assert _eff_of(seg, "Venus", "quarrel", spec) is False
    assert _eff_of("Shkos In the Latta of Venus there will be quarrel. Thus the separate effects", "Venus", "quarrel", spec) is True


def test_d1_the_declared_clause_lookup_trims_and_ignores_case_in_both_the_key_and_the_claimant():
    seg = "Shkos In the Latta of Venus there will be quarrel. Thus the separate effects"
    for key, who in (("Venus", "  VENUS "), ("  venus ", "Venus"), ("VENUS", "venus")):
        spec = _mini(effect_clauses={key: dict(clause="In the Latta of Venus there will be quarrel", effect="quarrel")})
        assert _eff_of(seg, who, "quarrel", spec) is True, (key, who)


TRUE_COND = ROWS[0]["affliction_condition"]


def _sun_cond(cond, spec=SPEC):
    rows = copy.deepcopy(ROWS)
    [r.update(affliction_condition=cond) for r in rows if r["graha"] == "Sun"]
    return _measure(rows=rows, spec=spec)


# third adversarial review MED: the condition may be the true sentence PLUS passage text and still passed (a contiguous run holding the anchors)
@pytest.mark.parametrize("cond", [
    TRUE_COND + " -During the Sun's Latin there will bo the ruin of every business Misery will result",   # the reviewer's case, whole census PASS
    "the 22nd from that of the Moon are called or rear Lattaa " + TRUE_COND,                                 # a prefix of passage text
    TRUE_COND + " wxw ^r?rw m m g",                                                                          # a suffix of OCR junk
    TRUE_COND.replace("If, ", "", 1),                                                                        # the leading "If" dropped
    "are called or rear Lattaa " + TRUE_COND + " wxw",
    TRUE_COND.replace("there will be sickness and anguish.", "there will be sickness."),
])
def test_d1_the_affliction_condition_must_BE_the_passage_sentence_not_contain_it(cond):
    r = _sun_cond(cond)
    assert r["v"] == "PARTIAL" and [(u["row"], u["failed"]) for u in r["d1"]["unmatched"]] == [("Sun", ["affliction_condition"])]


def _cond_spec(**changes):
    ef = dict(SPEC["extra_fields"][0], condition=dict(COND, **changes))
    return dict(SPEC, extra_fields=[ef, SPEC["extra_fields"][1]])


@pytest.mark.parametrize("changes", [
    dict(text=COND["text"] + " wxw"),                         # a declared text longer than the sentence
    dict(text="when thus counting, the tJanmunukshatra. natal star) happens to come as the Latta star, there will be sickness and anguish."),
    dict(start="when thus counting"),                         # a start that is not a capital: not clause-initial
    dict(start="Latta"),                                      # a start that occurs more than once
    dict(start="Sloka 42-44"),                                # at the head of the passage but not the sentence: the text must then equal the whole run
    dict(end="there will be sickness and anguish"),           # an end that is not a stop
    dict(end="Latta star,"),                                  # a stop-less cut: not a whole sentence
    dict(end="no such ending."),                              # an end absent from the passage
    dict(start="Not in the passage"),
])
def test_d1_a_declared_condition_that_is_not_one_whole_passage_sentence_is_a_miss_naming_every_row(changes):
    r = d1_rows = _measure(spec=_cond_spec(**changes))
    assert r["v"] == "PARTIAL" and len(r["d1"]["unmatched"]) == 8 and all(u["failed"] == ["affliction_condition"] for u in r["d1"]["unmatched"])


def test_d1_a_condition_that_starts_mid_sentence_at_a_lower_case_word_is_not_a_whole_sentence_even_after_an_ocr_stop():
    frag = "natal star) happens to come as the Latta star, there will be sickness and anguish."
    spec = _cond_spec(text=frag, start="natal star) happens", end="sickness and anguish.")          # clause-initial by the stray OCR dot, but not a capital opener
    r = _sun_cond(frag, spec)
    assert r["v"] == "PARTIAL" and [u["failed"] for u in r["d1"]["unmatched"] if u["row"] == "Sun"] == [["affliction_condition"]]


def test_d1_cut_sentence_needs_a_unique_clause_initial_capital_start_and_an_end_after_it():
    cut = d1._cut_sentence
    seg = "ABC The first one ends. then the second goes on. Then The first one ends."
    ok = dict(text="x", start="Then The first one", end="ends.")
    assert cut(seg, ok) == d1._toks("Then The first one ends.")
    assert cut("ABC The one here. tail", dict(start="The one", end="here.")) is None                 # preceded by an upper-case token: not clause-initial
    assert cut("a The one here. b The one here.", dict(start="The one", end="here.")) is None        # the start occurs twice
    assert cut("a b stop. then If one two stop.", dict(start="If one", end="stop.")) == d1._toks("If one two stop.")  # the end is searched AFTER the start
    assert cut("The one here.", dict(start="The one", end="here.")) == d1._toks("The one here.")      # at the head of the passage
    assert cut("a the one here.", dict(start="the one", end="here.")) is None                        # not a capital opener
    assert cut("a The one here", dict(start="The one", end="here")) is None                          # the end is not a stop


def test_d1_a_condition_may_be_declared_per_claimant_and_the_lookup_trims_and_ignores_case():
    other = dict(text=COND["text"], start=COND["start"], end=COND["end"])
    bad = dict(text="If, when thus counting, wrong", start="If, when thus counting", end="sickness and anguish.")
    ef = dict(SPEC["extra_fields"][0], by_claimant={"  SUN ": bad, "Moon": other})
    spec = dict(SPEC, extra_fields=[ef, SPEC["extra_fields"][1]])
    r = _measure(spec=spec)
    assert [(u["row"], u["failed"]) for u in r["d1"]["unmatched"]] == [("Sun", ["affliction_condition"])]     # Sun's own declaration is wrong; Moon's equals the shared one
    ok = dict(SPEC["extra_fields"][0], by_claimant={"  sun ": other})
    assert _measure(spec=dict(SPEC, extra_fields=[ok, SPEC["extra_fields"][1]]))["v"] == "PASS"


def test_d1_the_passage_text_column_requires_a_declared_condition_and_its_evidence():
    ef0 = SPEC["extra_fields"][0]
    for drop in ("condition", "condition_evidence"):
        ef = {k: v for k, v in ef0.items() if k != drop}
        with pytest.raises(d1.SpecError, match=drop):
            d1.validate_spec(dict(SPEC, extra_fields=[ef, SPEC["extra_fields"][1]]), "x")
        if drop == "condition":
            assert _measure(spec=dict(SPEC, extra_fields=[ef, SPEC["extra_fields"][1]]))["v"] == "PARTIAL"       # the engine never passes an undeclared condition
    for bad in (dict(text="x", start="If"), dict(text="x", start="If", end="a.", more="y"), dict(text=" ", start="If", end="a."), "text"):
        with pytest.raises(d1.SpecError, match="condition"):
            d1.validate_spec(dict(SPEC, extra_fields=[dict(ef0, condition=bad), SPEC["extra_fields"][1]]), "x")
    for bad in ({"Sun": "text"}, {"Sun": dict(text="x", start="If", end="a."), " sun": dict(text="x", start="If", end="a.")}, ["Sun"]):
        with pytest.raises(d1.SpecError, match="by_claimant"):
            d1.validate_spec(dict(SPEC, extra_fields=[dict(ef0, by_claimant=bad), SPEC["extra_fields"][1]]), "x")
    no_anchors = {k: v for k, v in ef0.items() if k != "anchors"}
    d1.validate_spec(dict(SPEC, extra_fields=[no_anchors, SPEC["extra_fields"][1]]), "x")                        # anchors are now optional (the equality is the check)


def test_the_condition_evidence_must_exist_too_and_is_existence_only(monkeypatch):
    car = copy.deepcopy(CAR_D1)
    car["spec"]["extra_fields"][0]["condition_evidence"] = "00_ARCHITECTURE/briefs/does_not_exist.md"
    _bad(car, "condition_evidence")
    car["spec"]["extra_fields"][0]["condition_evidence"] = "unverified:the L0 brief"
    ac.validate_declarations(_doc(car))


# LOW: the normalisation says only punctuation is ignored: nothing non-ASCII is dropped or folded
@pytest.mark.parametrize("eff", ["Quarrel\u00e9", "Quarrel\u0301", "Quarrel \u0301", "Quarr\u00e9l", "Quarrel\u200bx", "Quar\u0159el"])
def test_d1_a_non_ascii_letter_or_combining_mark_in_a_stored_effect_is_a_miss(eff):
    seg = "Shkos There will be quarrel in the Latta of Venus. Thus the separate effects"
    spec = _mini(effect_clauses={"Venus": dict(clause="There will be quarrel in the Latta of Venus", effect="Quarrel.")})
    assert _eff_of(seg, "Venus", "Quarrel", spec) is True
    assert _eff_of(seg, "Venus", eff, spec) is False


def test_d1_non_ascii_in_a_stored_condition_is_a_miss_and_nfkc_equivalents_are_stated_variants():
    assert _sun_cond(TRUE_COND.replace("anguish", "angu\u00efsh"))["v"] == "PARTIAL"
    assert _sun_cond(TRUE_COND.replace("anguish", "anguish\u0301"))["v"] == "PARTIAL"
    assert _sun_cond(TRUE_COND.replace("sickness", "\uff53ickness"))["v"] == "PASS"            # NFKC folds a full-width letter: stated


def test_d1_the_stored_effect_must_equal_the_declared_effect_so_a_frame_padded_effect_is_a_miss():
    seg = "Shkos There will be quarrel in the Latta of Venus. Thus the separate effects"
    spec = _mini(effect_clauses={"Venus": dict(clause="There will be quarrel in the Latta of Venus", effect="Quarrel.")})
    assert _eff_of(seg, "Venus", "There will be quarrel in the", spec) is False
    assert _eff_of(seg, "Venus", "quarrel", spec) is True


def test_d1_a_padded_claimant_is_stripped_in_the_row_label():
    rows = copy.deepcopy(ROWS)
    rows[6]["graha"] = "  Sun "
    rows[6]["count_from_graha"] = 99
    r = _measure(rows=rows)
    assert [u["row"] for u in r["d1"]["unmatched"]] == ["Sun"] and r["d1"]["rows"][6]["row"] == "Sun"


def test_d1_the_record_carries_the_cut_passage_it_hashed():
    e = _measure()["d1"]
    assert e["passage"].startswith("Sloka 42-44") and d1.span_digest(e["passage"]) == e["passage_sha256"]


@pytest.mark.parametrize("breakage, reason", [
    (lambda r: r["d1"].update(passage=r["d1"]["passage"] + " x"), "recomputed"),                       # the passage no longer matches its digest
    (lambda r: r["d1"].pop("passage"), "recomputed"),
    (lambda r: r["d1"].update(passage=None), "recomputed"),
    (lambda r: r["d1"].update(passage_sha256="0" * 64), "recomputed"),                               # a well-formed but unrelated digest
    (lambda r: r["d1"].update(chunks_sha256="0" * 64), "chunks_sha256"),
    (lambda r: r["d1"].pop("chunks_sha256"), "chunks_sha256"),
    (lambda r: r["d1"]["chunks"][0].pop("stored_sha256"), "chunk ledger is malformed"),
])
def test_d1_evidence_problem_recomputes_the_passage_and_chunk_digests(breakage, reason):
    rec = _measure()
    assert ac.d1_evidence_problem(rec) == ""
    breakage(rec)
    assert reason in ac.d1_evidence_problem(rec)


def test_d1_effect_matches_itself_trims_a_padded_claimant_not_only_its_caller():
    seg = "Shkos In the Latta of Venus there will be quarrel. Thus the separate effects"
    spec = _mini(effect_clauses={"Venus": dict(clause="In the Latta of Venus there will be quarrel", effect="quarrel")})
    assert d1._effect_matches("quarrel", "  Venus ", seg, spec) is True


@pytest.mark.parametrize("ev", ["unverified:", "unverified:   ", "unverified"])
def test_an_empty_unverified_pointer_is_not_evidence(ev):
    assert not ac._evidence_pointer_ok(ev)


def test_the_table_guard_runs_before_any_select(monkeypatch):
    called = []
    monkeypatch.setattr(ac, "d1_fetch_chunks", lambda ids: called.append("chunks") or dict(CHUNKS))
    monkeypatch.setattr(ac, "d1_fetch_rows", lambda t, c, chart=None: called.append("rows") or copy.deepcopy(ROWS))
    got = ac.carriage_declared_checks("x", CAR_D1, "some_other_table")
    assert got["Carr.D1"]["v"] == NO_DET and "does not guess" in got["Carr.D1"]["measured"] and called == []
    got = ac.carriage_declared_checks("x", CAR_D1, None)
    assert got["Carr.D1"]["v"] == NO_DET and called == []
    ac.carriage_declared_checks("x", CAR_D1, "bg_phaladeepika_latta")
    assert called == ["chunks", "rows"]


def test_the_effect_clauses_evidence_must_exist_too_and_a_symlink_out_of_the_repo_is_not_evidence(monkeypatch, tmp_path):
    car = copy.deepcopy(CAR_D1)
    car["spec"] = dict(car["spec"], effect_clauses_evidence="00_ARCHITECTURE/briefs/does_not_exist.md")
    _bad(car, "effect_clauses_evidence")
    car["spec"] = dict(car["spec"], effect_clauses_evidence="unverified:the L0 brief")
    ac.validate_declarations(_doc(car))
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.md").write_text("x", encoding="utf-8")
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "real.md").write_text("x", encoding="utf-8")
    (repo / "link.md").symlink_to(outside / "secret.md")
    (repo / "linkdir").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(ac, "ROOT", repo)
    assert ac._evidence_pointer_ok("real.md") and ac._evidence_pointer_ok("real.md:3")
    assert not ac._evidence_pointer_ok("link.md") and not ac._evidence_pointer_ok("linkdir/secret.md")      # resolved outside the repository
    assert not ac._evidence_pointer_ok("../outside/secret.md") and not ac._evidence_pointer_ok(str(outside / "secret.md"))


# ───────────────────────── the declaration validator ─────────────────────────

def _doc(car, extra=None):
    e = {"kind": "data", "carriage": car}
    e.update(extra or {})
    return dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={"bg_phaladeepika_latta": e})


def _bad(car, match, extra=None):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(car, extra))


def test_validator_accepts_the_latta_declaration_and_the_other_two_natures():
    ac.validate_declarations(_doc(copy.deepcopy(CAR_D1)))
    ac.validate_declarations(_doc(dict(applies="D3", nature="computation", why="w", evidence=EVID)))
    ac.validate_declarations(_doc(dict(applies="D2", nature="derivation", why="w", evidence=EVID)))
    ac.validate_declarations(_doc(dict(nature="ratified_judgment", ruling="N-73", why="w", evidence=EVID)))
    ac.validate_declarations(_doc(dict(served_surface=True, **{k: v for k, v in CAR_D1.items()}),
                                  dict(read_evidence="platform/src/x.ts:1", read_table="t")))      # served_surface coexists


@pytest.mark.parametrize("nature, applies", [("transcription", "D3"), ("transcription", "D2"), ("computation", "D1"), ("computation", "D2"),
                                             ("derivation", "D1"), ("derivation", "D3")])
def test_validator_refuses_a_nature_check_mismatch(nature, applies):
    car = dict(applies=applies, nature=nature, why="w", evidence=EVID, **({"citation_state": "sourced"} if nature == "transcription" else {}))
    _bad(car, "requires applies")


def test_validator_refuses_missing_or_blank_parts():
    base = copy.deepcopy(CAR_D1)
    for k in ("why", "evidence"):
        _bad({**base, k: "  "}, rf"carriage\.{k}")
        _bad({kk: v for kk, v in base.items() if kk != k}, rf"carriage\.{k}")
    _bad({**base, "nature": "guess"}, "nature must be one of")
    _bad({kk: v for kk, v in base.items() if kk != "nature"}, "nature must be one of")
    _bad({**base, "applies": None}, "requires applies")
    _bad({kk: v for kk, v in base.items() if kk != "citation_state"}, "citation_state")
    _bad({**base, "citation_state": "verified"}, "citation_state")
    _bad({**base, "ruling": "N-73"}, "ruling is only for")
    _bad({**base, "why": "two\nlines"}, "single-line")


def test_validator_ratified_judgment_discipline():
    ok = dict(nature="ratified_judgment", ruling="N-73", why="w", evidence=EVID)
    _bad({kk: v for kk, v in ok.items() if kk != "ruling"}, "ruling")
    _bad({**ok, "ruling": "yes"}, "ruling")
    _bad({**ok, "applies": "D1"}, "declares no check")
    _bad({**ok, "spec": SPEC}, "declares no check")
    _bad({**ok, "citation_state": "sourced"}, "citation_state")


def test_validator_spec_only_for_d1_and_well_formed():
    _bad(dict(applies="D3", nature="computation", why="w", evidence=EVID, spec=SPEC), "only defined for applies D1")
    for name, spec in {"unknown field": dict(SPEC, extra=1), "missing": {k: v for k, v in SPEC.items() if k != "chunk_ids"},
                       "matcher": dict(SPEC, matcher="nope"), "table": dict(SPEC, table="bad table"),
                       "empty chunks": dict(SPEC, chunk_ids=[]), "dup chunks": dict(SPEC, chunk_ids=[IDS[0], IDS[0]]),
                       "bad chunk id": dict(SPEC, chunk_ids=["Bad Id"]), "span": dict(SPEC, span=dict(start=" ")),
                       "span extra": dict(SPEC, span=dict(start="a", mid="b")), "fields": dict(SPEC, fields=dict(claimant="graha")),
                       "field ident": dict(SPEC, fields=dict(SPEC["fields"], count="1bad")), "dir words": dict(SPEC, direction_words={}),
                       "dir word": dict(SPEC, direction_words={"x": "a b"}), "stems": dict(SPEC, anchor_stems=[]),
                       "stem": dict(SPEC, anchor_stems=["(a|b)"]), "marker": dict(SPEC, effect_marker=" ")}.items():
        _bad({**CAR_D1, "spec": spec}, "spec"), name


def test_validator_checks_the_evidence_pointer_exists_or_says_it_is_unverified():
    base = copy.deepcopy(CAR_D1)
    ac.validate_declarations(_doc({**base, "evidence": EVID + ":12"}))                              # an existing file, with a line
    ac.validate_declarations(_doc({**base, "evidence": "unverified:recorded in DECISIONS.jsonl N-74"}))   # a pointer that cannot be checked says so
    for bad in ("00_ARCHITECTURE/briefs/does_not_exist_ever.md", "../outside.md", "/etc/hosts", "N-74", "bg_phaladeepika_latta brief"):
        _bad({**base, "evidence": bad}, "not an existing repo-relative file")


def test_validator_refuses_a_carriage_check_together_with_terminal_by_construction():
    _bad(copy.deepcopy(CAR_D1), "contradict", extra=dict(terminal_by_construction="writer x.py:1 writes nothing read"))


def test_validator_doc_level_field_list_must_match():
    doc = _doc(None)
    doc["carriage_declaration_fields"] = ["applies"]
    with pytest.raises(ac.DeclarationsError, match="carriage_declaration_fields"):
        ac.validate_declarations(doc)


def test_the_committed_file_is_1_7_0_declares_no_carriage_check_and_lists_the_fields():
    raw = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    assert raw["version"] == "1.7.0" and raw["carriage_declaration_fields"] == list(ac.CARRIAGE_DECL_FIELDS)
    assert [a for a, e in raw["assets"].items() if any(k in (e.get("carriage") or {}) for k in ac.CARRIAGE_DECL_FIELDS)] == []
    ac.load_asset_declarations()


# ───────────────────────── the census records ─────────────────────────

@pytest.fixture()
def fetch(monkeypatch):
    monkeypatch.setattr(ac, "d1_fetch_chunks", lambda ids: {i: CHUNKS[i] for i in ids if i in CHUNKS})
    monkeypatch.setattr(ac, "d1_fetch_rows", lambda table, cols, chart=None: copy.deepcopy(ROWS))


def test_an_undeclared_asset_emits_nothing_and_reads_as_today(fetch):
    assert ac.carriage_declared_checks("bg_x", None, "t") == {} and ac.carriage_declared_checks("bg_x", {"served_surface": True}, "t") == {}
    cell = ac.rollup_asset("L0", {})["Carr"]
    assert cell["v"] == NO_DET and all(c["state"] == "APPLIES" for c in cell["checks"])


def test_a_declared_d1_asset_measures_d1_and_the_other_two_read_na_by_the_declaration_keyed_cause(fetch):
    got = ac.carriage_declared_checks("bg_phaladeepika_latta", CAR_D1, "bg_phaladeepika_latta")
    assert got["Carr.D1"]["v"] == "PASS" and got["Carr.D1"]["citation_state"] == "sourced_ocr_unverified"
    for c in ("Carr.D2", "Carr.D3"):
        assert got[c]["v"] == NA and got[c]["cause"] == "not-the-declared-carriage" and "declared carriage check is D1" in got[c]["measured"]
    cell = ac.rollup_asset("L0", got)["Carr"]
    assert cell["v"] == "PASS" and [c["v"] for c in cell["checks"]] == ["PASS", "N/A", "N/A"]
    assert {c["rule_id"] for c in cell["checks"] if c["v"] == NA} == {"Carr.D2#measured:not-the-declared-carriage", "Carr.D3#measured:not-the-declared-carriage"}


def test_the_na_is_released_only_by_the_declared_rule(fetch, monkeypatch):
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {k: v for k, v in ac.NA_RULE_DECISIONS.items() if "not-the-declared-carriage" not in k})
    got = ac.carriage_declared_checks("bg_phaladeepika_latta", CAR_D1, "bg_phaladeepika_latta")
    cell = ac.rollup_asset("L0", got)["Carr"]
    assert cell["v"] == NO_DET and [c["v"] for c in cell["checks"]] == ["PASS", NO_DET, NO_DET]


def test_the_caller_chosen_not_chosen_cause_does_not_exist():
    assert all("not-chosen" not in v for v in ac.NA_CAUSES.values())
    with pytest.raises(ValueError):
        old = dict(ac.NA_RULE_DECISIONS)
        try:
            ac.NA_RULE_DECISIONS["Carr.D2#measured:not-chosen"] = "x"
            ac.validate_na_rule_decisions()
        finally:
            ac.NA_RULE_DECISIONS.clear()
            ac.NA_RULE_DECISIONS.update(old)


def test_a_seeded_wrong_row_holds_the_carr_cell_below_pass(monkeypatch):
    rows = copy.deepcopy(ROWS)
    [r.update(count_from_graha=21) for r in rows if r["graha"] == "Moon"]
    monkeypatch.setattr(ac, "d1_fetch_chunks", lambda ids: dict(CHUNKS))
    monkeypatch.setattr(ac, "d1_fetch_rows", lambda t, c, chart=None: rows)
    cell = ac.rollup_asset("L0", ac.carriage_declared_checks("bg_phaladeepika_latta", CAR_D1, "bg_phaladeepika_latta"))["Carr"]
    assert cell["v"] == "PARTIAL"


@pytest.mark.parametrize("applies, nature", [("D2", "derivation"), ("D3", "computation")])
def test_a_declared_d2_or_d3_has_no_detector_yet_and_the_other_two_read_na(applies, nature):
    got = ac.carriage_declared_checks("x", dict(applies=applies, nature=nature, why="w", evidence=EVID), None)
    own = f"Carr.{applies}"
    assert got[own]["v"] == NO_DET and "detector is built yet" in got[own]["measured"]
    assert sorted(c for c in got if got[c]["v"] == NA) == sorted(c for c in ("Carr.D1", "Carr.D2", "Carr.D3") if c != own)
    assert ac.rollup_asset("L0", got)["Carr"]["v"] == NO_DET
    assert ac.CRITERION_REGISTRY[own]["detector"] == "NONE"


def test_a_d1_declaration_without_a_spec_is_no_detector_not_pass():
    got = ac.carriage_declared_checks("x", {k: v for k, v in CAR_D1.items() if k != "spec"}, "t")
    assert got["Carr.D1"]["v"] == NO_DET and "without a `spec`" in got["Carr.D1"]["measured"]


def test_a_failed_database_read_degrades_only_d1_to_errored(monkeypatch):
    def boom(*a, **k):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "d1_fetch_chunks", boom)
    got = ac.carriage_declared_checks("x", CAR_D1, "bg_phaladeepika_latta")
    assert got["Carr.D1"]["v"] == ac.ERRORED and got["Carr.D1"]["citation_state"] == "sourced_ocr_unverified"
    assert got["Carr.D2"]["v"] == NA


def test_a_ratified_judgment_seed_reads_na_on_all_three_by_its_own_cause_and_needs_its_own_rule(monkeypatch):
    got = ac.carriage_declared_checks("x", dict(nature="ratified_judgment", ruling="N-73", why="w", evidence=EVID), None)
    assert {c: got[c]["cause"] for c in got} == {c: "ratified_judgment" for c in ("Carr.D1", "Carr.D2", "Carr.D3")}
    assert ac.rollup_asset("L0", got)["Carr"]["v"] == NO_DET                       # no rule declared for ratified_judgment: not released
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {**ac.NA_RULE_DECISIONS, **{f"Carr.D{i}#measured:ratified_judgment": "SS (test)" for i in (1, 2, 3)}})
    assert ac.rollup_asset("L0", got)["Carr"]["v"] == NA


def test_the_registry_gives_d1_a_detector_and_leaves_d2_d3_none_and_declares_the_three_rules():
    assert ac.CRITERION_REGISTRY["Carr.D1"]["detector"] != "NONE" and ac.CRITERION_REGISTRY["Carr.D1"]["revision"] == 2
    assert ac.CRITERION_REGISTRY["Carr.D2"]["detector"] == ac.CRITERION_REGISTRY["Carr.D3"]["detector"] == "NONE"
    assert r13.S2_IDS <= set(ac.NA_RULE_DECISIONS)
    assert not [i for i in ac.NA_RULE_DECISIONS if "ratified_judgment" in i]


def test_measure_wires_the_declared_carriage_through_to_the_asset_record(monkeypatch, tmp_path, fetch):
    reg = {"x": na_causes._reg_row("x", "bg_phaladeepika_latta"), "y": na_causes._reg_row("y")}
    decl = {"x": dict(kind="data", carriage=CAR_D1)}
    na_causes._stub_layer(monkeypatch, tmp_path, reg, tables={"bg_phaladeepika_latta": (["graha"], [])})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decl)
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert ms["x"]["Carr.D1"]["v"] == "PASS" and ms["x"]["Carr.D1"]["d1"]["rows_matched"] == 8
    assert ms["x"]["Carr.D2"]["cause"] == "not-the-declared-carriage"
    assert not [k for k in ms["y"] if k.startswith("Carr.")]                              # an undeclared asset reads as before


# ───────────────────────── the two SELECTs ─────────────────────────

def test_d1_fetch_chunks_builds_one_select_by_declared_ids_and_parses(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "scalar", lambda sql: seen.append(sql) or json.dumps(list(CHUNKS.values())))
    got = ac.d1_fetch_chunks(IDS)
    assert set(got) == set(IDS) and len(seen) == 1
    assert "FROM classical_text_chunks WHERE chunk_id IN ('phaladeepika_pg0338_c01','phaladeepika_pg0339_c01')" in seen[0]
    assert seen[0].lstrip().upper().startswith("SELECT") and not any(w in seen[0].upper() for w in ("INSERT", "UPDATE", "DELETE", "DROP"))


@pytest.mark.parametrize("ids", [[], ["a'; DROP TABLE x;--"], ["Bad Id"], [1]])
def test_d1_fetch_chunks_refuses_a_malformed_id_list_before_any_sql(monkeypatch, ids):
    monkeypatch.setattr(ac, "scalar", lambda sql: pytest.fail("no SQL may run"))
    with pytest.raises(ac.Unknown):
        ac.d1_fetch_chunks(ids)


def test_d1_fetch_rows_selects_only_the_declared_columns_in_a_total_order(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "scalar", lambda sql: seen.append(sql) or json.dumps(ROWS))
    assert ac.d1_fetch_rows("bg_phaladeepika_latta", ["graha", "count_from_graha", "graha"]) == ROWS
    assert 'SELECT "graha","count_from_graha" FROM "bg_phaladeepika_latta"' in seen[0] and 'ORDER BY t."graha",t."count_from_graha"' in seen[0]


@pytest.mark.parametrize("table, cols", [("bad table", ["a"]), ("t", ["a;b"]), ("t", []), ("t", ["1a"]), ('t"', ["a"])])
def test_d1_fetch_rows_refuses_a_malformed_identifier(monkeypatch, table, cols):
    monkeypatch.setattr(ac, "scalar", lambda sql: pytest.fail("no SQL may run"))
    with pytest.raises(ac.Unknown):
        ac.d1_fetch_rows(table, cols)


# ───────────────────────── HIGH 1 (adversarial review): the rows read must come back as ONE psql output line ─────────────────────────

def _psql_lines(raw: str, sep: str = "\x1f"):
    """What asset_census.psql() does with psql's stdout: split on newlines, drop blank lines, split on the field separator."""
    return [ln.split(sep) for ln in raw.strip().split("\n") if ln.strip()]


# a captured sample: `SELECT json_agg(t)::text FROM (SELECT graha, count_from_graha FROM bg_phaladeepika_latta) t` under psql -tA with 3 rows
_JSON_AGG_SAMPLE = '[{"graha":"Jupiter","count_from_graha":6}, \n {"graha":"Mars","count_from_graha":3}, \n {"graha":"Mercury","count_from_graha":7}]\n'
_JSONB_AGG_SAMPLE = '[{"graha": "Jupiter", "count_from_graha": 6}, {"graha": "Mars", "count_from_graha": 3}, {"graha": "Mercury", "count_from_graha": 7}]\n'


def test_the_json_agg_record_shape_is_multi_line_and_scalar_sees_only_its_first_line():
    """The live bug: with two or more rows `json_agg(t)` puts ', <newline> ' between elements; scalar() returns the first line only."""
    first = _psql_lines(_JSON_AGG_SAMPLE)[0][0]
    with pytest.raises(json.JSONDecodeError):
        json.loads(first)
    assert len(_psql_lines(_JSONB_AGG_SAMPLE)) == 1 and json.loads(_psql_lines(_JSONB_AGG_SAMPLE)[0][0])[2]["graha"] == "Mercury"


def test_d1_fetch_rows_reads_a_multi_row_table_as_one_line_and_never_uses_json_agg_of_a_record(monkeypatch):
    seen = []

    def fake_psql(sql, sep="\x1f", timeout=None):
        seen.append(sql)
        return _psql_lines(_JSONB_AGG_SAMPLE)
    monkeypatch.setattr(ac, "psql", fake_psql)
    rows = ac.d1_fetch_rows("bg_phaladeepika_latta", ["graha", "count_from_graha"])
    assert [r["graha"] for r in rows] == ["Jupiter", "Mars", "Mercury"]
    assert "jsonb_agg(to_jsonb(t) ORDER BY" in seen[0] and "json_agg(t)" not in seen[0]
    monkeypatch.setattr(ac, "psql", lambda sql, sep="\x1f", timeout=None: _psql_lines(_JSON_AGG_SAMPLE))      # the old shape is refused loudly
    with pytest.raises(ac.Unknown):
        ac.d1_fetch_rows("bg_phaladeepika_latta", ["graha", "count_from_graha"])


def test_d1_fetch_rows_is_chart_scoped_when_the_table_carries_chart_id(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "scalar", lambda sql: seen.append(sql) or "[]")
    ac.d1_fetch_rows("bg_t", ["a"])
    ac.d1_fetch_rows("bg_t", ["a"], "482012f1-710e-4a25-994a-93821f5871aa")
    assert "chart_id" not in seen[0] and "WHERE \"chart_id\" = '482012f1-710e-4a25-994a-93821f5871aa'" in seen[1]
    for bad in ("x", "482012f1-710e-4a25-994a-93821f5871aa'; DROP TABLE t;--", 5):
        with pytest.raises(ac.Unknown):
            ac.d1_fetch_rows("bg_t", ["a"], bad)


# REAL SQL: the SAME statements run on the off-production rehearsal cluster (127.0.0.1:55432, db `rehearsal`), through the E5.6 URL guard,
# against TEMP tables inside a transaction that is ALWAYS rolled back (ON COMMIT DROP, then ROLLBACK): nothing persistent is created.
# Skipped where the guard or the cluster is absent (CI).
# The E5.6 URL guard lives on its own branch: point SUVARNA_REHEARSAL_GUARD at rehearsal_guard.py to run these tests; unset, they SKIP visibly.
_GUARD_ENV = os.environ.get("SUVARNA_REHEARSAL_GUARD", "")
_GUARD = pathlib.Path(_GUARD_ENV) if _GUARD_ENV else None


def _rehearsal_url():
    if _GUARD is None or not _GUARD.exists():
        return None
    import importlib.util
    import subprocess
    spec = importlib.util.spec_from_file_location("rehearsal_guard_for_test", _GUARD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    url = mod.normalise_rehearsal_url("postgresql://127.0.0.1:55432/rehearsal")
    try:
        p = subprocess.run(["psql", url, "-tAX", "-q", "-c", "select 1"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return url if p.returncode == 0 and p.stdout.strip() == "1" else None


_REHEARSAL = _rehearsal_url()
rehearsal = pytest.mark.skipif(_REHEARSAL is None, reason="real-SQL tests: set SUVARNA_REHEARSAL_GUARD=<path to rehearsal_guard.py> and have the rehearsal cluster (127.0.0.1:55432) up")


def _q(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def _rolled_back_psql(monkeypatch):
    import subprocess
    pre = ["CREATE TEMP TABLE bg_phaladeepika_latta (graha text, direction text, count_from_graha int, effect_description text, "
           "affliction_condition text, verse_ref text) ON COMMIT DROP;",
           "CREATE TEMP TABLE classical_text_chunks (chunk_id text, text_id text, content_en text, content_sa text, content_sha256 text) ON COMMIT DROP;"]
    pre += [f"INSERT INTO bg_phaladeepika_latta VALUES ({_q(r['graha'])},{_q(r['direction'])},{r['count_from_graha']},{_q(r['effect_description'])},"
            f"{_q(r['affliction_condition'])},{_q(r['verse_ref'])});" for r in ROWS]
    pre += [f"INSERT INTO classical_text_chunks VALUES ({_q(c['chunk_id'])},{_q(c['text_id'])},{_q(c['content_en'])},{_q(c['content_sa'])},"
            f"{_q(c['content_sha256'])});" for c in CHUNKS.values()]

    def fake_psql(sql, sep="\x1f", timeout=None):
        script = "BEGIN;\n" + "\n".join(pre) + f"\n{sql};\nROLLBACK;\n"
        p = subprocess.run(["psql", _REHEARSAL, "-tAX", "-q", "-F", sep, "-v", "ON_ERROR_STOP=1", "-f", "-"], input=script,
                           capture_output=True, text=True, timeout=30)
        if p.returncode != 0:
            raise ac.Unknown((p.stderr.strip().splitlines() or ["psql failed"])[0])
        return _psql_lines(p.stdout, sep)
    monkeypatch.setattr(ac, "psql", fake_psql)


@rehearsal
def test_REAL_SQL_the_rows_read_returns_all_eight_rows_through_the_census_scalar(monkeypatch):
    _rolled_back_psql(monkeypatch)
    rows = ac.d1_fetch_rows("bg_phaladeepika_latta", ["graha", "count_from_graha", "direction", "effect_description"])
    assert sorted(r["graha"] for r in rows) == sorted(r["graha"] for r in ROWS) and len(rows) == 8
    assert {r["graha"]: r["count_from_graha"] for r in rows} == {r["graha"]: r["count_from_graha"] for r in ROWS}


@rehearsal
def test_REAL_SQL_the_old_json_agg_shape_really_fails_on_the_same_data(monkeypatch):
    _rolled_back_psql(monkeypatch)
    out = ac.scalar("SELECT json_agg(t)::text FROM (SELECT graha FROM bg_phaladeepika_latta ORDER BY graha) t")
    with pytest.raises(json.JSONDecodeError):
        json.loads(out)


@rehearsal
def test_REAL_SQL_the_chunk_read_and_the_whole_d1_measurement_run_end_to_end(monkeypatch):
    _rolled_back_psql(monkeypatch)
    got = ac.d1_fetch_chunks(IDS)
    assert set(got) == set(IDS) and all(d1.verify_chunk(c)["verified"] for c in got.values())
    rec = ac.carriage_declared_checks("bg_phaladeepika_latta", CAR_D1, "bg_phaladeepika_latta")
    assert rec["Carr.D1"]["v"] == "PASS" and rec["Carr.D1"]["d1"]["rows_total"] == 8


def test_both_fetchers_raise_unknown_on_an_unparseable_read(monkeypatch):
    monkeypatch.setattr(ac, "scalar", lambda sql: "not json")
    with pytest.raises(ac.Unknown):
        ac.d1_fetch_chunks(IDS)
    with pytest.raises(ac.Unknown):
        ac.d1_fetch_rows("t", ["a"])
