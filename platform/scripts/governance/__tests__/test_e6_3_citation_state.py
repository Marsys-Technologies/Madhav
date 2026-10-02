"""E6.3 / N-74: `citation_state` reaches the ELEVATED output as a field.

E5.1 record_version 2 carries `citation_state` (sourced | sourced_ocr_unverified | unsourced | refuted | null) and
`citation_state_caveat`; v1 records read as null. FIXTURES: v1 records come from the real E5.1 writer (the golden ledgers in
fixtures/e6_3_golden, written by nikasha_certify.write_certification, are v1: see test_e6_3_e5_reconcile.py, which must
keep passing); v2 lines here are HAND-WRITTEN by the fixtures (cert(..., citation_state=...)) and chained by the shared
chain rule, because the v2 writer (branch suvarna/engine-E5.1-citation-state) is not merged yet.
The mini registry has no Carr.D1 / Ldgr.source_presence, so the reported citation criteria are patched to Ldgr.src / Idem.alt.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import World, cert, disp, load_tracker, mini_patch  # noqa: E402

T = load_tracker()
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}


@pytest.fixture(autouse=True)
def _mini(monkeypatch):
    mini_patch(monkeypatch, T)
    monkeypatch.setattr(T, "E63_CITATION_CRITERIA", ("Ldgr.src", "Idem.alt"))


@pytest.fixture
def w(tmp_path):
    return World(tmp_path).default()


def put(w, asset, crit, state, kind="gate", verdict="PASS"):
    """Replace the (v1) certificate of asset/crit by a v2 one carrying `state`."""
    old = w.find(asset, crit, kind)
    i = w.certs.index(old)
    w.certs[i] = cert(asset, crit, verdict, kind=kind, citation_state=state)


def report(w):
    w.commit()
    return T.elevated_report(w.last, str(w.repo))


def raises(w):
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    return e.value


def test_v1_records_read_as_null_state_and_no_caveat(w):
    rep = report(w)
    for a in ("ga_alpha", "bg_beta", "ka_gamma"):
        assert rep[a]["citation_states"] == {} and rep[a]["citation_caveat"] is False


def test_a_sourced_state_is_reported_and_sets_no_caveat(w):
    put(w, "ga_alpha", "Ldgr.src", "sourced")
    rep = report(w)
    assert rep["ga_alpha"]["citation_states"] == {"Ldgr.src": "sourced"} and rep["ga_alpha"]["citation_caveat"] is False


def test_an_ocr_unverified_state_counts_but_sets_the_caveat(w):
    put(w, "ga_alpha", "Ldgr.src", "sourced_ocr_unverified")
    put(w, "ga_alpha", "Idem.alt", "sourced")
    rep = report(w)
    assert "ga_alpha" in rep
    assert rep["ga_alpha"]["citation_states"] == {"Idem.alt": "sourced", "Ldgr.src": "sourced_ocr_unverified"}
    assert rep["ga_alpha"]["citation_caveat"] is True and rep["bg_beta"]["citation_caveat"] is False


def test_the_caveat_looks_at_any_pass_cell_not_only_the_two_citation_criteria(w):
    put(w, "ga_alpha", "Idem.pat", "sourced_ocr_unverified")
    rep = report(w)
    assert rep["ga_alpha"]["citation_caveat"] is True and rep["ga_alpha"]["citation_states"] == {}


def test_an_ocr_state_on_a_declared_addition_sets_the_caveat(w):
    put(w, "bg_beta", "D-GROUNDING", "sourced_ocr_unverified", kind="addition")
    assert report(w)["bg_beta"]["citation_caveat"] is True


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
@pytest.mark.parametrize("crit,kind", [("Ldgr.src", "gate"), ("Idem.alt", "gate"), ("Idem.pat", "gate"), ("D-GROUNDING", "addition")])
def test_a_pass_that_is_unsourced_or_refuted_does_not_count_and_is_reported_as_blocked(w, state, crit, kind):
    asset = "bg_beta" if kind == "addition" else "ga_alpha"
    put(w, asset, crit, state, kind=kind)
    w.commit()
    assert asset not in w.elevated(T) and asset not in T.elevated_report(w.last, str(w.repo))
    blocked = T.citation_blocked_cells(w.last, str(w.repo))
    assert blocked == [dict(asset=asset, criterion=crit, cert_id=f"{asset}|{kind}|{crit}@1", citation_state=state)]
    # the others are untouched
    assert (ALL - {asset}) <= w.elevated(T)


def test_a_null_state_on_a_v2_record_is_neutral(w):
    put(w, "ga_alpha", "Ldgr.src", None)
    rep = report(w)
    assert "ga_alpha" in rep and rep["ga_alpha"]["citation_states"] == {} and rep["ga_alpha"]["citation_caveat"] is False


def test_a_non_pass_record_with_an_unsourced_state_is_not_a_blocked_pass(w):
    w.certs.append(cert("ga_alpha", "Ldgr.src", "FAIL", gen=2, citation_state="unsourced"))
    w.commit()
    assert "ga_alpha" not in w.elevated(T)                      # the FAIL already withholds it
    assert T.citation_blocked_cells(w.last, str(w.repo)) == []


def test_a_stale_unsourced_pass_is_not_listed_as_blocked(w):
    put(w, "ga_alpha", "Ldgr.src", "unsourced")
    w.writer_versions["ga_alpha"] = 2                            # the certificate is stale anyway
    w.commit()
    assert T.citation_blocked_cells(w.last, str(w.repo)) == []


def test_a_later_sourced_generation_clears_the_block(w):
    put(w, "ga_alpha", "Ldgr.src", "unsourced")
    w.certs.append(cert("ga_alpha", "Ldgr.src", gen=2, citation_state="sourced"))
    rep = report(w)
    assert "ga_alpha" in rep and rep["ga_alpha"]["citation_states"] == {"Ldgr.src": "sourced"}


def test_a_terminal_asset_reports_no_citation_state(w):
    rep = report(w)
    assert rep["ka_gamma"]["citation_states"] == {} and rep["ka_gamma"]["citation_caveat"] is False


def test_elevated_assets_stays_the_key_set_of_the_report(w):
    put(w, "ga_alpha", "Ldgr.src", "sourced_ocr_unverified")
    put(w, "bg_beta", "Ldgr.src", "refuted")
    w.commit()
    assert w.elevated(T) == set(T.elevated_report(w.last, str(w.repo))) == {"ga_alpha", "ka_gamma"}


# ---- the reader tolerates v1 and v2 and refuses what it does not know -------------------------------------------------

def test_both_record_versions_are_accepted_in_one_ledger(w):
    put(w, "ga_alpha", "Ldgr.src", "sourced")
    assert {w.find("ga_alpha", "Ldgr.src")["record_version"], w.find("bg_beta", "Ldgr.src")["record_version"]} == {1, 2}
    w.commit()
    assert w.elevated(T) == ALL


@pytest.mark.parametrize("rv", [0, 3, 99, True, "2", None, 2.0])
def test_an_unknown_record_version_raises(w, rv):
    w.find("ga_alpha", "Idem.pat")["record_version"] = rv
    raises(w)


def test_a_record_without_a_record_version_raises(w):
    del w.find("ga_alpha", "Idem.pat")["record_version"]
    raises(w)


def test_a_v1_record_that_carries_a_citation_state_raises(w):
    w.find("ga_alpha", "Idem.pat")["citation_state"] = "unsourced"
    raises(w)
    w2 = w
    del w2.find("ga_alpha", "Idem.pat")["citation_state"]
    w2.find("ga_alpha", "Idem.pat")["citation_state_caveat"] = False
    raises(w2)


@pytest.mark.parametrize("state", ["Sourced", "ocr", "", "unknown", 7, True, ["sourced"]])
def test_an_unknown_citation_state_value_raises(w, state):
    put(w, "ga_alpha", "Ldgr.src", None)
    w.find("ga_alpha", "Ldgr.src")["citation_state"] = state
    w.find("ga_alpha", "Ldgr.src").pop("citation_state_caveat", None)
    raises(w)


@pytest.mark.parametrize("caveat,state", [(True, "sourced"), (False, "sourced_ocr_unverified"), (True, None), ("yes", "sourced"), (1, "sourced")])
def test_a_caveat_that_contradicts_the_state_or_is_not_a_boolean_raises(w, caveat, state):
    put(w, "ga_alpha", "Ldgr.src", state)
    w.find("ga_alpha", "Ldgr.src")["citation_state_caveat"] = caveat
    raises(w)


def test_the_citation_constants_are_n74s():
    assert T.E63_RECORD_VERSIONS == (1, 2)
    assert T.E63_CITATION_STATES == ("sourced", "sourced_ocr_unverified", "unsourced", "refuted")
    assert T.E63_CITATION_BLOCKING == ("unsourced", "refuted")


def test_the_real_citation_criteria_are_carr_d1_and_ldgr_source_presence(monkeypatch):
    import importlib
    fresh = load_tracker()
    assert fresh.E63_CITATION_CRITERIA == ("Carr.D1", "Ldgr.source_presence")
