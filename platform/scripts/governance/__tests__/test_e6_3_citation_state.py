"""E6.3 / N-74: `citation_state` reaches the ELEVATED output as a field.

FIXTURE PROVENANCE. The real v2 writer (branch suvarna/engine-E5.1-citation-state) produced fixtures/e6_3_golden/ledger_v2.jsonl
(see its README); the hand-written lines here follow exactly what that writer produces for EVERY record: record_version 2,
citation_state (null except on a citation gate), citation_state_caveat (true exactly for a citation-gate PASS whose state is not
`sourced`, so a NULL-state Ldgr.source_presence PASS carries caveat true and still counts). v1 records (the real v1 writer's
golden ledgers, and cert(..., v1=True)) read as state null, caveat false: the choice E5.1's reader makes (ASSUMED here; E5.1's
builder is settling the v1-vs-v2 caveat reading). The mini registry has no Carr.D1 / Ldgr.source_presence: the reported citation
criteria are patched (mini_patch) to Ldgr.src / Idem.alt.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import CERTS, World, cert, chained, disp, load_tracker, mini_patch, parse_via_validator  # noqa: E402

T = load_tracker()
GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "e6_3_golden" / "ledger_v2.jsonl"
ALL = {"ga_alpha", "bg_beta", "ka_gamma"}


@pytest.fixture(autouse=True)
def _mini(monkeypatch):
    mini_patch(monkeypatch, T)


@pytest.fixture
def w(tmp_path):
    return World(tmp_path).default()


def put(w, asset, crit, state, kind="gate", verdict="PASS", **over):
    old = w.find(asset, crit, kind)
    w.certs[w.certs.index(old)] = cert(asset, crit, verdict, kind=kind, citation_state=state, **over)


def report(w):
    w.commit()
    return T.elevated_report(w.last, str(w.repo))


def raises(w):
    w.commit()
    with pytest.raises(T.ElevatedInputError) as e:
        w.elevated(T)
    return e.value


# ---- the real writer's bytes ----------------------------------------------------------------------------------------

def golden_world(tmp_path):
    w = World(tmp_path)
    for a in ("ga_alpha", "ga_beta", "ga_gamma", "ga_delta"):
        w.disps.append(disp(a, "keep"))
    w.raw[CERTS] = GOLDEN.read_bytes()
    w.commit()
    return w


def test_golden_v2_ledger_written_by_the_real_writer_is_read_end_to_end(tmp_path):
    w = golden_world(tmp_path)
    rep = T.elevated_report(w.last, str(w.repo))
    assert set(rep) == {"ga_alpha", "ga_beta", "ga_gamma"} == w.elevated(T)               # ga_delta: Idem.alt unsourced
    assert rep["ga_alpha"]["citation_states"] == {"Idem.alt": "sourced", "Ldgr.src": "sourced"}
    assert rep["ga_alpha"]["citation_caveat"] is False
    assert rep["ga_beta"]["citation_states"] == {"Idem.alt": "sourced", "Ldgr.src": "sourced_ocr_unverified"}
    assert rep["ga_beta"]["citation_caveat"] is True
    # a NULL-state Ldgr PASS carries caveat true, COUNTS, and is not listed as a state
    assert rep["ga_gamma"]["citation_states"] == {"Idem.alt": "sourced"} and rep["ga_gamma"]["citation_caveat"] is True
    assert T.citation_blocked_cells(w.last, str(w.repo)) == [dict(
        asset="ga_delta", criterion="Idem.alt", cert_id="ga_delta|gate|Idem.alt@1", verdict="NO_DETECTOR",
        citation_state="unsourced")]


def test_golden_v2_every_record_carries_version_2_state_and_caveat():
    rows = [json.loads(ln) for ln in GOLDEN.read_text().splitlines()[1:] if json.loads(ln).get("kind") in ("gate", "addition")]
    assert rows and all(r["record_version"] == 2 and "citation_state" in r and "citation_state_caveat" in r for r in rows)
    assert {r["citation_state"] for r in rows if r["criterion"] not in ("Ldgr.src", "Idem.alt")} == {None}


# ---- v1 and v2 -------------------------------------------------------------------------------------------------------

def test_v1_records_read_as_null_state_and_a_v1_citation_pass_is_caveated_but_v1_gates_are_not_current(w):
    """v1 records predate the declarations binding: their gates read as UNBOUND, so such an asset is not elevated (the
    parse still gives the citation reading E5.1's reader gives)."""
    for i, c in enumerate(w.certs):
        w.certs[i] = cert(c["asset"], c["criterion"], c["verdict"], kind=c["kind"], na=c["na"], v1=True)
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    led = parse_via_validator(T, w.repo, w.last, T._e63_show(str(w.repo), w.last, "00_ARCHITECTURE/control/asset_certs.jsonl"), facts)
    a = led.by_key
    assert a["ga_alpha|gate|Ldgr.src"][0]["citation_state"] is None and a["ga_alpha|gate|Ldgr.src"][0]["citation_state_caveat"] is True
    assert a["ga_alpha|gate|Idem.pat"][0]["citation_state_caveat"] is False
    assert w.elevated(T) == {"ka_gamma"}                                    # only the terminal asset
    assert {c["reason"] for c in T.stale_declaration_cells(w.last, str(w.repo))} == {"unbound"}


def test_a_v1_record_is_read_as_exactly_state_none_and_the_citation_gate_rule_caveat(w):
    w.certs[w.certs.index(w.find("ga_alpha", "Ldgr.src"))] = cert("ga_alpha", "Ldgr.src", v1=True)
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    led = parse_via_validator(T, w.repo, w.last, T._e63_show(str(w.repo), w.last, "00_ARCHITECTURE/control/asset_certs.jsonl"), facts)
    rec = led.by_key["ga_alpha|gate|Ldgr.src"][0]
    assert rec["record_version"] == 1 and rec["citation_state"] is None and rec["citation_state_caveat"] is True
    other = led.by_key["ga_alpha|gate|Idem.pat"][0]                                   # a non-citation v1 PASS
    w.certs[w.certs.index(w.find("ga_alpha", "Idem.pat"))] = cert("ga_alpha", "Idem.pat", v1=True)
    w.commit()
    led = parse_via_validator(T, w.repo, w.last, T._e63_show(str(w.repo), w.last, "00_ARCHITECTURE/control/asset_certs.jsonl"), facts)
    assert led.by_key["ga_alpha|gate|Idem.pat"][0]["citation_state_caveat"] is False


def test_both_record_versions_are_accepted_in_one_ledger_the_v1_gate_is_unbound(w):
    w.certs[w.certs.index(w.find("ga_alpha", "Idem.pat"))] = cert("ga_alpha", "Idem.pat", v1=True)
    assert {c["record_version"] for c in w.certs} == {1, 2}
    w.commit()
    assert w.elevated(T) == ALL - {"ga_alpha"}                              # its v1 gate carries no declarations binding


def test_a_record_with_no_record_version_reads_as_v1_like_e5_1(w):
    rec = w.find("ga_alpha", "Idem.pat")
    for k in ("record_version", "citation_state", "citation_state_caveat", "declarations_sha256", "declarations_version"):
        del rec[k]
    w.commit()
    assert "ga_alpha" not in w.elevated(T)                                  # read as v1: unbound


@pytest.mark.parametrize("rv", [0, 3, 99, True, "2", None, 2.0])
def test_an_unknown_record_version_raises(w, rv):
    w.find("ga_alpha", "Idem.pat")["record_version"] = rv
    raises(w)


def test_a_v1_record_that_carries_a_v2_field_raises(w):
    rec = w.find("ga_alpha", "Idem.pat")
    rec["record_version"] = 1
    raises(w)                                                    # still carries citation_state/_caveat
    del rec["citation_state"]
    raises(w)                                                    # still carries the caveat
    del rec["citation_state_caveat"]
    raises(w)                                                    # still carries the declarations binding
    del rec["declarations_sha256"], rec["declarations_version"]
    w.commit()
    assert w.elevated(T) == ALL - {"ga_alpha"}                   # a clean v1 record reads, but is unbound


@pytest.mark.parametrize("missing", ["citation_state", "citation_state_caveat"])
def test_a_v2_record_must_carry_both_fields(w, missing):
    del w.find("ga_alpha", "Idem.pat")[missing]
    raises(w)


# ---- states and caveat -----------------------------------------------------------------------------------------------

def test_a_sourced_state_is_reported_and_sets_no_caveat(w):
    rep = report(w)
    assert rep["ga_alpha"]["citation_states"] == {"Idem.alt": "sourced", "Ldgr.src": "sourced"}
    assert rep["ga_alpha"]["citation_caveat"] is False


def test_an_ocr_unverified_state_counts_but_sets_the_caveat(w):
    put(w, "ga_alpha", "Ldgr.src", "sourced_ocr_unverified")
    rep = report(w)
    assert "ga_alpha" in rep and rep["ga_alpha"]["citation_states"]["Ldgr.src"] == "sourced_ocr_unverified"
    assert rep["ga_alpha"]["citation_caveat"] is True and rep["bg_beta"]["citation_caveat"] is False


def test_a_null_state_on_a_citation_pass_counts_and_sets_the_caveat_without_raising(w):
    put(w, "ga_alpha", "Ldgr.src", None)
    assert w.find("ga_alpha", "Ldgr.src")["citation_state_caveat"] is True       # what the real writer writes
    rep = report(w)
    assert "ga_alpha" in rep and rep["ga_alpha"]["citation_caveat"] is True
    assert "Ldgr.src" not in rep["ga_alpha"]["citation_states"]


def test_a_null_state_caveat_must_be_true_on_a_citation_pass(w):
    put(w, "ga_alpha", "Ldgr.src", None, citation_state_caveat=False)
    raises(w)


def test_a_citation_criterion_that_is_not_a_pass_has_no_caveat(w):
    put(w, "ga_alpha", "Ldgr.src", None, verdict="FAIL")
    assert w.find("ga_alpha", "Ldgr.src")["citation_state_caveat"] is False
    w.commit()
    assert "ga_alpha" not in w.elevated(T)
    w.find("ga_alpha", "Ldgr.src")["citation_state_caveat"] = True
    raises(w)


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_a_pass_line_carrying_an_unsourced_or_refuted_state_raises_it_is_not_elevation_grade(w, state):
    put(w, "ga_alpha", "Ldgr.src", state)
    raises(w)


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_an_unsourced_or_refuted_cell_withholds_the_asset_and_is_listed_as_blocked(w, state):
    put(w, "ga_alpha", "Idem.alt", state, verdict="NO_DETECTOR")
    w.commit()
    assert "ga_alpha" not in w.elevated(T) and (ALL - {"ga_alpha"}) <= w.elevated(T)
    assert T.citation_blocked_cells(w.last, str(w.repo)) == [dict(
        asset="ga_alpha", criterion="Idem.alt", cert_id="ga_alpha|gate|Idem.alt@1", verdict="NO_DETECTOR", citation_state=state)]


def test_a_stale_blocked_cell_is_not_listed(w):
    put(w, "ga_alpha", "Idem.alt", "unsourced", verdict="NO_DETECTOR")
    w.writer_versions["ga_alpha"] = 2
    w.commit()
    assert T.citation_blocked_cells(w.last, str(w.repo)) == []


def test_a_later_sourced_pass_generation_clears_the_block(w):
    put(w, "ga_alpha", "Idem.alt", "unsourced", verdict="NO_DETECTOR")
    w.certs.append(cert("ga_alpha", "Idem.alt", gen=2, citation_state="sourced"))
    w.commit()
    assert "ga_alpha" in w.elevated(T) and T.citation_blocked_cells(w.last, str(w.repo)) == []


@pytest.mark.parametrize("crit,kind", [("Idem.pat", "gate"), ("Build.any", "gate"), ("D-GROUNDING", "addition")])
def test_a_state_on_anything_but_a_citation_gate_raises(w, crit, kind):
    asset = "bg_beta" if kind == "addition" else "ga_alpha"
    rec = w.find(asset, crit, kind)
    rec["citation_state"] = "sourced"
    raises(w)


@pytest.mark.parametrize("state", ["Sourced", "ocr", "", "unknown", 7, True, ["sourced"]])
def test_an_unknown_citation_state_value_raises(w, state):
    w.find("ga_alpha", "Ldgr.src")["citation_state"] = state
    raises(w)


@pytest.mark.parametrize("crit,caveat", [("Ldgr.src", True), ("Idem.pat", True), ("Ldgr.src", "yes"), ("Ldgr.src", 1),
                                         ("Ldgr.src", 0), ("Idem.pat", None)])
def test_a_caveat_that_contradicts_the_record_or_is_not_a_boolean_raises(w, crit, caveat):
    w.find("ga_alpha", crit)["citation_state_caveat"] = caveat           # Ldgr.src is `sourced`: caveat must be false
    raises(w)


def test_the_caveat_covers_any_pass_cell_through_the_writers_flag(w):
    put(w, "bg_beta", "Idem.alt", None)                                  # a null-state PASS on a citation gate of bg_beta
    assert report(w)["bg_beta"]["citation_caveat"] is True


def test_a_terminal_asset_reports_no_citation_state(w):
    rep = report(w)
    assert rep["ka_gamma"]["citation_states"] == {} and rep["ka_gamma"]["citation_caveat"] is False


def test_elevated_assets_stays_the_key_set_of_the_report(w):
    put(w, "ga_alpha", "Ldgr.src", "sourced_ocr_unverified")
    put(w, "bg_beta", "Idem.alt", "refuted", verdict="NO_DETECTOR")
    w.commit()
    assert w.elevated(T) == set(T.elevated_report(w.last, str(w.repo))) == {"ga_alpha", "ka_gamma"}


def test_the_citation_constants_are_n74s():
    assert T.E63_CITATION_BLOCKING == ("unsourced", "refuted")


def test_the_real_citation_criteria_are_carr_d1_and_ldgr_source_presence():
    """E5.1's own constant (the single definition; the reader holds no copy)."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
    import nikasha_certify as nc
    assert nc.CITATION_CRITERIA == ("Carr.D1", "Ldgr.source_presence")
    assert not hasattr(load_tracker(), "E63_CITATION_CRITERIA")
