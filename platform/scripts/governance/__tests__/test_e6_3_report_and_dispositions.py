"""E6.3 strategist requirements: R1 `elevated_report` says HOW an asset is elevated (never one flat set), R2 the
dispositions ledger is append-only and chained like the certificate ledger and a terminal disposition needs a decision
id AND a visible reason; LOW: invisible-filler-only reasons are blank."""
from __future__ import annotations

import json
import os
import sys

import pytest

pytestmark = pytest.mark.skip(reason="the E6.3 certificate reader was dropped by owner decision N-152; the module stays importable, its tests are not run in CI")

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import (CERTS, DISP, NA_NULL, World, cert, chained, disp, gap, inval, load_tracker,  # noqa: E402
                            mini_patch, sha)

T = load_tracker()
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}


@pytest.fixture(autouse=True)
def _mini(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture
def w(tmp_path):
    return World(tmp_path).default()


def got(w):
    w.commit()
    return w.elevated(T)


def report(w):
    w.commit()
    return T.elevated_report(w.last, str(w.repo))


def raises(w):
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    return e.value


# ═══════════════ R1: the report ═══════════════

def test_the_report_distinguishes_measured_from_terminal_and_elevated_assets_is_its_key_set(w):
    rep = report(w)
    assert set(rep) == ALL == w.elevated(T)
    assert rep["ga_alpha"]["basis"] == "measured" and rep["bg_beta"]["basis"] == "measured"
    assert rep["ka_gamma"]["basis"] == "terminal_disposition"
    assert rep["ka_gamma"]["terminal"] == dict(disposition="retire", reason="superseded by ka_delta", decision_id="N-70")
    assert rep["ka_gamma"]["declaration_based_pass_cells"] == 0 and rep["ka_gamma"]["ruled_na_cells"] == []
    assert rep["ga_alpha"]["terminal"] is None


def test_the_report_lists_ruled_na_cells_with_their_rule_and_decision(w):
    rep = report(w)
    assert rep["ga_alpha"]["ruled_na_cells"] == [dict(criterion="Null.x", rule_id="Null.x#columns_any", decision_id="N-22a")]
    assert rep["ga_alpha"]["declaration_based_pass_cells"] == 0


def test_the_report_counts_pass_by_declaration_cells(w):
    w.find("ga_alpha", "Build.target")["basis"] = "declaration"
    w.seed_extra = {"ga_alpha": "service"}
    rep = report(w)
    assert rep["ga_alpha"]["declaration_based_pass_cells"] == 1 and rep["bg_beta"]["declaration_based_pass_cells"] == 0


def test_a_consolidate_is_reported_with_its_own_disposition(w):
    w.disps.append(disp("ka_delta", "consolidate", reason="folded into ka_gamma", decision_id="N-71b"))
    rep = report(w)
    assert rep["ka_delta"]["terminal"] == dict(disposition="consolidate", reason="folded into ka_gamma", decision_id="N-71b")


def test_elevated_assets_and_the_report_cannot_disagree_across_worlds(tmp_path):
    for i, mutate in enumerate([lambda w: None, lambda w: w.drop("ga_alpha", "Idem.pat"),
                                lambda w: w.gaps.append(gap("bg_beta", "D-GROUNDING")),
                                lambda w: w.disps.append(disp("ga_alpha", "unresolved"))]):
        sub = tmp_path / f"w{i}"
        sub.mkdir()
        w = World(sub).default()
        mutate(w)
        w.commit()
        assert w.elevated(T) == set(T.elevated_report(w.last, str(w.repo)))


def test_the_report_is_a_second_public_function_and_the_pinned_signature_is_unchanged():
    import inspect
    assert list(inspect.signature(T.elevated_report).parameters) == ["ref", "repo"]
    assert list(inspect.signature(T.elevated_assets).parameters) == ["ref", "repo"]


# ═══════════════ R2: dispositions are chained, decided and dated ═══════════════

def _lines(w):
    return w.render()[DISP].rstrip("\n").split("\n")


def test_the_disposition_ledger_is_chained_from_the_schema_row(w):
    lines = _lines(w)
    assert json.loads(lines[1])["seq"] == 1 and json.loads(lines[1])["prev_sha256"] == sha(lines[0].encode())
    assert got(w) == ALL


def test_an_edited_earlier_disposition_line_breaks_the_chain(w):
    lines = _lines(w)
    r = json.loads(lines[1])
    r["reason"] = "edited"
    lines[1] = json.dumps(r, ensure_ascii=False)
    w.raw[DISP] = "\n".join(lines) + "\n"
    assert "chain" in str(raises(w))


def test_a_deleted_or_reordered_disposition_line_breaks_the_chain(w):
    lines = _lines(w)
    del lines[1]
    w.raw[DISP] = "\n".join(lines) + "\n"
    raises(w)
    lines = _lines(w)
    lines[1], lines[2] = lines[2], lines[1]
    w.raw[DISP] = "\n".join(lines) + "\n"
    raises(w)


@pytest.mark.parametrize("bad", [0, 5, None, True, "2"])
def test_a_wrong_disposition_seq_raises(w, bad):
    rows = list(w.disps)
    rows[0] = dict(rows[0], seq=bad)
    w.raw[DISP] = chained(rows)
    raises(w)


def test_a_wrong_or_missing_disposition_prev_sha256_raises(w):
    for bad in ("0" * 64, None, 7):
        rows = list(w.disps)
        rows[1] = dict(rows[1], prev_sha256=bad)
        w.raw[DISP] = chained(rows)
        raises(w)


def test_a_second_schema_row_in_the_disposition_ledger_raises(w):
    w.raw[DISP] = chained([w.disps[0], {"asset": "_schema", "_doc": "again"}] + w.disps[1:])
    raises(w)


@pytest.mark.parametrize("key", ["decision_id", "decided_on", "additions"])
def test_every_disposition_line_must_carry_decision_id_decided_on_and_additions(w, key):
    row = disp("ga_alpha", "keep")
    del row[key]
    w.disps.append(row)
    raises(w)


@pytest.mark.parametrize("dec", ["x", "N-", "n-5", "N-12 ", 7, True, ""])
def test_a_malformed_decision_id_raises(w, dec):
    w.disps.append(disp("ga_alpha", "keep", decision_id=dec))
    raises(w)


@pytest.mark.parametrize("when", ["2026-10-02", "2026-10-02T10:00:00", "yesterday", None, 5, ""])
def test_decided_on_must_be_a_timezone_aware_iso_timestamp(w, when):
    w.disps.append(disp("ga_alpha", "keep", decided_on=when))
    raises(w)


def test_a_disposition_without_a_decision_id_reads_unresolved_and_a_later_decided_row_fixes_it(w):
    w.disps.append(disp("ga_alpha", "keep", decision_id=None))
    assert got(w) == ALL - {"ga_alpha"}
    w.disps.append(disp("ga_alpha", "keep", decision_id="N-71"))
    assert got(w) == ALL


def test_a_terminal_disposition_without_a_decision_id_is_not_terminal(w):
    w.disps = [d for d in w.disps if d["asset"] != "ka_gamma"] + [disp("ka_gamma", "retire", reason="gone", decision_id=None)]
    assert got(w) == ALL - {"ka_gamma"}


def test_a_terminal_disposition_with_a_decision_id_but_no_reason_is_not_terminal(w):
    w.disps = [d for d in w.disps if d["asset"] != "ka_gamma"] + [disp("ka_gamma", "retire", reason="", decision_id="N-71")]
    assert got(w) == ALL - {"ka_gamma"}


@pytest.mark.parametrize("reason", ["ㅤ", "ᅟ", "ﾠ", "⠀", "ㅤᅟ ⠀​"])
def test_a_reason_made_only_of_invisible_filler_characters_is_blank(w, reason):
    w.disps = [d for d in w.disps if d["asset"] != "ka_gamma"] + [disp("ka_gamma", "retire", reason=reason)]
    assert got(w) == ALL - {"ka_gamma"}


@pytest.mark.parametrize("cp", ["\ufe0f", "\ufe00", "\ufe01", "\u034f", "\u17b4", "\u17b5", "\u0301", "\ufffc", "\U000e0100",
                                 "\u20dd", "\u0e31", "\u200b\u0301\ufe0f", "!!!", "\u2014"])
def test_a_reason_without_a_single_letter_or_digit_is_blank(w, cp):
    """The visible-reason check is an allowlist (>= 1 alphanumeric after NFKC + cleaning), not a denylist of invisibles."""
    w.disps = [d for d in w.disps if d["asset"] != "ka_gamma"] + [disp("ka_gamma", "retire", reason=cp)]
    assert got(w) == ALL - {"ka_gamma"}


@pytest.mark.parametrize("reason", ["superseded", "N-70 folded", "\u0301a", "1", "\u00e9"])
def test_a_reason_with_a_letter_or_digit_counts(w, reason):
    w.disps = [d for d in w.disps if d["asset"] != "ka_gamma"] + [disp("ka_gamma", "retire", reason=reason)]
    assert "ka_gamma" in got(w)


def test_a_reason_with_visible_text_among_fillers_still_counts(w):
    w.disps = [d for d in w.disps if d["asset"] != "ka_gamma"] + [disp("ka_gamma", "retire", reason="ㅤgoneㅤ")]
    assert "ka_gamma" in got(w)


def test_an_unknown_disposition_value_still_raises(w):
    w.disps.append(disp("ga_alpha", "keepish"))
    raises(w)


def test_the_module_has_no_disposition_writer():
    assert not [n for n in dir(T) if "write" in n.lower() and "disposition" in n.lower()]
