"""test_e6_s2_carriage_strict.py -- S2 carriage declaration strictness, matched to S3's (E6.1 follow-up, item 4).

The carriage declaration (`carriage: {nature, applies, why, evidence, ...}`) used to accept any non-blank single-line `why` ("w") and any existing-file `evidence`. S3's
vocab_alias / ldgr_source (`_s3_common`) hold theirs to real text rules. The carriage now takes them too, so a declaration that RELEASES or GRADES a Carr check cannot rest on a
placeholder reason or an unreadable pointer:

  why       a str, no leading / trailing whitespace, no control / format / line-separator character, <= 1200 chars, at least 15 characters and 3 words, and no placeholder word
            ANYWHERE (S3's rule), with ONE deliberate exception for a D1 / D2 / D3 check: the words `null` and `none` may be mentioned (the committed latta why says "content_sa is
            NULL"); tbd / todo / tba / fixme / xxx / placeholder / pending / n/a / unknown stay refused anywhere, and at least three REAL words (none of those) are needed.
            A ratified_judgment, which RELEASES Carr.D1-D3 to N/A, takes S3's rule unchanged (no exception).
  evidence  no control / invisible character; a `:LINE` inside the file; an `unverified:` pointer states a real description (10 characters, 2 words); and a ratified_judgment
            carriage (which RELEASES Carr.D1-D3 to N/A, an S3 N/A release) may not rest on `unverified:` at all.
  spec pointers (effect_clauses_evidence, condition_evidence, an escape hatch's, a repair's): the same control-character / line-range / unverified-text rules.

The committed latta declaration validates as-is (asserted on the real file). Every refusal has a mutation test: with S3's text checks stubbed out the same declaration is accepted."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_e6_s2_carriage as s2  # noqa: E402

CAR = s2.CAR_D1
EVID = s2.EVID
REAL_FILE_LINES = len((ac.ROOT / EVID).read_bytes().splitlines())


def _car(**over):
    c = copy.deepcopy(CAR)
    c.update(over)
    return c


def _ok(car, extra=None):
    ac.validate_declarations(s2._doc(car, extra))


def _refused(car, match, extra=None):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(s2._doc(car, extra))


RJ = dict(nature="ratified_judgment", ruling="N-73", why=s2.WHY, evidence=EVID)


# ───────────────────────── the committed declaration, unchanged ─────────────────────────

def test_the_committed_latta_carriage_validates_as_is_and_still_reads_the_same():
    doc = json.loads((ac.DECLARATIONS_PATH).read_text(encoding="utf-8"))
    car = doc["assets"]["bg_phaladeepika_latta"]["carriage"]
    assert ac.validate_declarations(doc)
    assert "NULL" in car["why"] and car["evidence"].endswith(":122")                       # the long sentence that mentions NULL: why S3's anywhere-rule is not used verbatim
    assert ac._s3_text_problem(car["why"], min_chars=15, min_words=3) is not None           # (S3's own rule WOULD refuse it)
    assert ac._s3_text_problem(car["why"], min_chars=15, min_words=3, placeholder="prose") is None
    assert ac._s3_evidence_problem(car["evidence"], allow_unverified=True) is None
    assert ac.load_asset_declarations()["bg_phaladeepika_latta"]["carriage"] == car


# ───────────────────────── why ─────────────────────────

@pytest.mark.parametrize("why, match", [
    ("w", "too short"),
    ("a reason", "too short"),                                                              # 8 characters, 2 words
    ("two words here", "too short"),                                                        # 14 characters
    ("tiny little one", None),                                                              # 15 characters, 3 words: the floor itself is accepted
    ("TBD: reason to be written later", "placeholder"),
    ("n/a", "too short"),
    ("tbd tbd tbd tbd tbd", "placeholder"),
    ("TODO fill this reason in properly", "placeholder"),
    ("none none none none", "mostly placeholder"),
    (" leading space in the reason text", "leading or trailing whitespace"),
    ("trailing space in the reason text ", "leading or trailing whitespace"),
    ("a reason with a zero​width space inside it", "control, line-separator or invisible"),
    ("a reason with a tab\tinside the line here", "control, line-separator or invisible"),
    ("a reason with a separator inside the line", "control, line-separator or invisible"),
])
def test_the_carriage_why_is_held_to_the_s3_text_rules(why, match):
    if match is None:
        _ok(_car(why=why))
    else:
        _refused(_car(why=why), rf"carriage\.why .*{match}")


def test_a_long_explanatory_why_may_mention_null_and_none_but_no_other_placeholder_word():
    _ok(_car(why="eight rows, content_sa is NULL for all of them; the effect of two rows is reserved empty and none is invented"))
    _ok(_car(why="none of the rows carries an effect clause for Ketu, whose counting rule the passage does not give"))
    for word in ("tbd", "TBD", "todo", "tba", "fixme", "xxx", "placeholder", "pending", "unknown", "n/a", "nil", "lorem"):
        _refused(_car(why=f"eight rows transcribed from the passage, source {word} for the rest"), rf"carriage\.why .*placeholder word")


@pytest.mark.parametrize("why", [
    "all rows matched TBD",
    "ratified by the strategist, todo later",
    "rows match; pending review; unknown source; none claimed",
    "see tbd tbd tbd",
    "all rows match the passage, unknown",
    "rows are checked by Carr.D1 (n/a for the rest)",
    "TODO: eight rows transcribed from the passage",
])
def test_a_placeholder_word_anywhere_is_refused_for_every_nature(why):
    _refused(_car(why=why), r"carriage\.why .*placeholder")
    _refused(dict(RJ, why=why), r"carriage\.why .*placeholder")
    _refused(dict(applies="D3", nature="computation", why=why, evidence=EVID), r"carriage\.why .*placeholder")
    _refused(dict(applies="D3", nature="derivation", why=why, evidence=EVID), r"carriage\.why .*placeholder")


@pytest.mark.parametrize("why", ["none none none none", "null null none null", "see none none none", "none or null none"])
def test_fewer_than_three_real_words_is_refused_even_when_only_null_and_none_are_mentioned(why):
    _refused(_car(why=why), r"carriage\.why .*mostly placeholder words")


def test_a_ratified_judgment_takes_s3s_rule_with_no_null_none_exception():
    sentence = "the rows were ratified, content_sa is NULL and none is invented"
    _ok(_car(why=sentence))                                                               # a D1 sentence may mention both
    _refused(dict(RJ, why=sentence), r"carriage\.why .*placeholder word")                  # a ratified_judgment, which releases N/A, may not
    _ok(dict(RJ, why="ratified by the strategist as a judgment seed for this asset"))


def test_the_old_checks_still_come_first_with_their_old_messages():
    _refused(_car(why="  "), r"carriage\.why must be a non-blank single-line string")
    _refused(_car(why="two\nlines"), r"carriage\.why must be a non-blank single-line string")
    _refused(_car(why="x" * 1201), r"carriage\.why must be a non-blank single-line string")                 # the 1200-character cap is the old check's
    _refused(_car(evidence="00_ARCHITECTURE/briefs/does_not_exist.md"), r"carriage\.evidence .* is not an existing repo-relative file")


# ───────────────────────── evidence ─────────────────────────

@pytest.mark.parametrize("evidence, match", [
    (f"{EVID}:{REAL_FILE_LINES + 1}", rf"names line {REAL_FILE_LINES + 1} but the file has {REAL_FILE_LINES} line"),
    (f"{EVID}:0", "names line 0"),
    ("unverified:x", "`unverified:` text is too short"),
    ("unverified:TBD to be recorded later", "`unverified:` text contains a placeholder word"),
    ("unverified:​the L0 brief note", "`unverified:` text contains a control"),
])
def test_the_carriage_evidence_is_held_to_the_s3_pointer_rules(evidence, match):
    _refused(_car(evidence=evidence), rf"carriage\.evidence .*{match}")


def test_a_pointer_with_a_valid_line_and_an_honest_unverified_description_are_accepted():
    _ok(_car(evidence=f"{EVID}:1"))
    _ok(_car(evidence=f"{EVID}:{REAL_FILE_LINES}"))
    _ok(_car(evidence="unverified:recorded in the L0 elevation brief, section 4"))


def test_a_ratified_judgment_may_not_rest_on_an_unverified_pointer_because_it_releases_the_carr_checks():
    _ok(RJ)
    _refused(dict(RJ, evidence="unverified:recorded in the L0 elevation brief, section 4"), r"carriage\.evidence .*may not be `unverified:` for an N/A release")
    # a D1 / D2 / D3 check does not release anything: its `unverified:` stays allowed (an honest, described pointer)
    _ok(dict(applies="D3", nature="computation", why=s2.WHY, evidence="unverified:recorded in the L0 elevation brief, section 4"))
    _ok(dict(applies="D3", nature="derivation", why=s2.WHY, evidence="unverified:recorded in the L0 elevation brief, section 4"))


# ───────────────────────── the spec's own pointers ─────────────────────────

def _spec(mutate):
    car = _car()
    mutate(car["spec"])
    return car


def test_the_spec_pointers_get_the_control_character_line_range_and_unverified_rules():
    bad_line = f"{EVID}:{REAL_FILE_LINES + 5}"
    _refused(_spec(lambda sp: sp.update(effect_clauses_evidence=bad_line)), r"effect_clauses_evidence .*names line")
    _refused(_spec(lambda sp: sp.update(effect_clauses_evidence="unverified:x")), r"effect_clauses_evidence .*too short")
    _refused(_spec(lambda sp: sp.update(effect_clauses_evidence=EVID + "​")), r"effect_clauses_evidence")
    _ok(_spec(lambda sp: sp.update(effect_clauses_evidence="unverified:the L0 brief")))

    def cond(sp, v):
        sp["extra_fields"][0] = dict(sp["extra_fields"][0], condition_evidence=v)
    _refused(_spec(lambda sp: cond(sp, bad_line)), r"condition_evidence .*names line")
    _refused(_spec(lambda sp: cond(sp, "unverified:TBD to be recorded later")), r"condition_evidence .*placeholder")
    _ok(_spec(lambda sp: cond(sp, f"{EVID}:3")))

    def repair(sp, v):
        sp["extra_fields"][0] = dict(sp["extra_fields"][0], repairs=[{"from": "Janma-nakshatra", "to": "tJanmunukshatra", "evidence": v}])
    _refused(_spec(lambda sp: repair(sp, bad_line)), r"repairs\['Janma-nakshatra'\]\.evidence .*names line")
    _refused(_spec(lambda sp: repair(sp, "unverified:x")), r"repairs\['Janma-nakshatra'\]\.evidence .*too short")
    _ok(_spec(lambda sp: repair(sp, f"{EVID}:3")))

    def hatch(sp, v):
        f = dict(sp["extra_fields"][0])
        f["condition"] = dict(f["condition"], ocr_lost_stop=dict(f["condition"]["ocr_lost_stop"], evidence=v))
        sp["extra_fields"][0] = f
    _refused(_spec(lambda sp: hatch(sp, bad_line)), r"escape hatch .*evidence .*names line")
    _ok(_spec(lambda sp: hatch(sp, f"{EVID}:3")))


# ───────────────────────── mutations: the refusals can fail ─────────────────────────

@pytest.mark.parametrize("car, why_not", [
    (_car(why="w"), "why"),
    (_car(why="TBD: reason to be written later"), "why"),
    (_car(evidence=f"{EVID}:{REAL_FILE_LINES + 1}"), "evidence"),
    (_car(evidence="unverified:x"), "evidence"),
    (dict(RJ, evidence="unverified:recorded in the L0 elevation brief, section 4"), "evidence"),
])
def test_MUTATION_with_the_s3_rules_stubbed_out_the_same_declaration_is_accepted(monkeypatch, car, why_not):
    with pytest.raises(ac.DeclarationsError, match=rf"carriage\.{why_not}"):
        ac.validate_declarations(s2._doc(car))
    monkeypatch.setattr(ac, "_s3_text_problem", lambda *a, **k: None)
    monkeypatch.setattr(ac, "_s3_evidence_problem", lambda *a, **k: None)
    assert ac.validate_declarations(s2._doc(car))                                           # the old S2 validator (only non-blank single-line, existing file)


def test_MUTATION_the_spec_pointer_rules_are_what_refuse_a_bad_spec_pointer(monkeypatch):
    car = _spec(lambda sp: sp.update(effect_clauses_evidence=f"{EVID}:{REAL_FILE_LINES + 5}"))
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(s2._doc(car))
    monkeypatch.setattr(ac, "_carriage_pointer_strict", lambda *a, **k: None)
    assert ac.validate_declarations(s2._doc(car))


def test_a_declaration_with_no_carriage_and_every_other_declared_asset_is_untouched():
    doc = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    with_carriage = [a for a, e in doc["assets"].items() if isinstance(e.get("carriage"), dict) and e["carriage"].get("nature")]
    assert len(with_carriage) == 79 and "bg_phaladeepika_latta" in with_carriage and not any(a.startswith(("ka_", "ph_", "mi_", "lel_")) for a in with_carriage)      # N-233 (declarations 1.62.0): 73 of the 82 L0-L2 assets declare, ten more by the closed-list residuals (bg_nakshatra, bg_reference, bg_prashna_rules unverified_transcription; bg_kp_sublord_division, bg_parihara_rules, ga_nakshatra, ga_sensitive, ga_medical, ga_vichara, bo_samvada single_derivation); was 63 of the 82 L0-L2 assets declare after the SS audit of 2026-10-06 (carriage removed where it could not be shown true; kota reclassified, class priors K3 withdrawn); N-156 originally: 79 of the 82 L0-L2 assets declare (three have no K1 source declared: bg_kota_chakra_rings, bg_prashna_rules, bg_sarvatobhadra_grid); every one validates (next line)
    assert ac.validate_declarations(doc)


# ───────────────────────── mutations of the placeholder rule ─────────────────────────

def test_MUTATION_widening_the_null_none_exemption_accepts_the_review_examples(monkeypatch):
    for why in ("all rows matched TBD", "rows match; pending review; unknown source; none claimed", "ratified by the strategist, todo later"):
        _refused(_car(why=why), r"carriage\.why")
    monkeypatch.setattr(ac, "_PROSE_MAY_MENTION", frozenset({"null", "none", "tbd", "pending", "unknown", "todo"}))
    for why in ("all rows matched TBD", "rows match; pending review; unknown source; none claimed", "ratified by the strategist, todo later"):
        _ok(_car(why=why))                                                                # the exemption list is what refuses them


def test_the_real_words_rule_refuses_on_its_own_once_the_exemption_is_widened(monkeypatch):
    """`see tbd tbd tbd` has one real word. Widen the exemption so the placeholder-anywhere rule no longer fires: the three-real-words rule still refuses it (it is load-bearing, not
    redundant); and with only null / none exempt the placeholder rule refuses it first."""
    _refused(_car(why="see tbd tbd tbd"), r"carriage\.why .*placeholder word")
    monkeypatch.setattr(ac, "_PROSE_MAY_MENTION", frozenset({"null", "none", "tbd"}))
    _refused(_car(why="see tbd tbd tbd"), r"carriage\.why .*mostly placeholder words")
    _refused(_car(why="none none none none"), r"carriage\.why .*mostly placeholder words")
    assert ac._s3_text_problem("see tbd tbd tbd", min_chars=15, min_words=3, placeholder="prose") is not None
    assert ac._s3_text_problem("see tbd tbd tbd and the other three real words follow", min_chars=15, min_words=3, placeholder="prose") is None   # with the exemption widened, enough real words pass


def test_MUTATION_a_ratified_judgment_that_used_the_prose_rule_would_accept_null_and_none(monkeypatch):
    sentence = "the rows were ratified, content_sa is NULL and none is invented"
    _refused(dict(RJ, why=sentence), r"carriage\.why")
    real = ac._s3_text_problem
    monkeypatch.setattr(ac, "_s3_text_problem", lambda v, *, min_chars, min_words, placeholder="any": real(v, min_chars=min_chars, min_words=min_words, placeholder="prose") if placeholder == "any" and v == sentence else real(v, min_chars=min_chars, min_words=min_words, placeholder=placeholder))
    _ok(dict(RJ, why=sentence))
