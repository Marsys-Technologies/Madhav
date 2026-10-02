"""E6.3 reader vs E5.1's own citation-state reader (`_check_citation_fields`, branch suvarna/engine-E5.1-citation-state).

Two checks over the SAME 32 mutated v2 ledgers (re-chained, so the only defect is the citation field; see
_e6_3_citation_variants.py):
  * LIVE: run the E5.1 worktree's reader now and compare accept/refuse AND the parsed (citation_state, caveat) of every
    certificate (so the v1 caveat reading is compared, not just acceptance). Skipped, with the reason, when that worktree is
    not on this machine.
  * RECORDED (runs in CI): fixtures/e6_3_golden/citation_verdicts.json holds E5.1's verdicts, produced by the real reader
    (`python _e6_3_citation_variants.py`; README there). The variants' bytes are pinned by sha256, so the recorded verdicts
    cannot silently describe other inputs; E6.3's parser is checked against them without duplicating E5.1's logic.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_citation_variants import MINI_STRICT, VARIANTS, VERDICTS_FILE, run_e5_1, sha  # noqa: E402
from _e6_3_fixtures import World, load_tracker, mini_patch  # noqa: E402

T = load_tracker()
GOV = pathlib.Path(__file__).resolve().parents[1]


def _e51_dir():
    for cand in (os.environ.get("E6_3_E51_CITATION_DIR"), "/Users/Dev/suvarna-engine-lane-e5-1b/platform/scripts/governance", str(GOV)):
        if cand and (pathlib.Path(cand) / "nikasha_certify.py").exists() and \
                "CITATION_STRICT" in (pathlib.Path(cand) / "nikasha_certify.py").read_text(encoding="utf-8"):
            return pathlib.Path(cand)
    return None


E51 = _e51_dir()
RECORDED = json.loads(VERDICTS_FILE.read_text(encoding="utf-8"))


@pytest.fixture
def mine(tmp_path, monkeypatch):
    mini_patch(monkeypatch, T)
    monkeypatch.setattr(T, "E63_CITATION_STRICT", MINI_STRICT)
    w = World(tmp_path)
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)

    def parse(data):
        try:
            led = T._e63_parse_certs(data, facts)
        except T.ElevatedInputError:
            return {"verdict": "REFUSED"}
        return {"verdict": "OK", "states": {r["cert_id"]: [r["citation_state"], r["citation_state_caveat"]]
                                           for recs in led.by_key.values() for r in recs}}
    return parse


def _same(theirs, ours, name):
    assert ours["verdict"] == theirs["verdict"], (name, theirs, ours)
    if theirs["verdict"] == "OK":
        assert ours["states"] == theirs["states"], name


@pytest.mark.parametrize("name", list(VARIANTS))
def test_live_the_reader_and_e5_1_agree_on_every_variant_including_the_parsed_state_and_caveat(mine, name):
    if E51 is None:
        pytest.skip("E5.1 with CITATION_STRICT (suvarna/engine-E5.1-citation-state worktree, or this checkout once merged) is not "
                    "on this machine: live parity not run; the recorded-verdict test below still runs")
    _same(run_e5_1(E51, VARIANTS[name]), mine(VARIANTS[name]), name)


@pytest.mark.parametrize("name", list(VARIANTS))
def test_recorded_the_reader_matches_the_verdicts_recorded_from_the_real_e5_1_reader(mine, name):
    rec = RECORDED["variants"][name]
    assert rec["sha256"] == sha(VARIANTS[name]), \
        f"variant {name} changed since the verdicts were recorded: re-run `python _e6_3_citation_variants.py` against E5.1"
    _same(rec, mine(VARIANTS[name]), name)


def test_the_recorded_file_covers_exactly_the_variants_and_both_outcomes():
    assert set(RECORDED["variants"]) == set(VARIANTS) and len(VARIANTS) >= 30
    outcomes = {v["verdict"] for v in RECORDED["variants"].values()}
    assert outcomes == {"OK", "REFUSED"}
    assert RECORDED["citation_strict"] == list(MINI_STRICT) and len(RECORDED["e5_1_commit"]) == 40


def test_the_v1_citation_gate_pass_is_caveated_true_by_both(mine):
    for name in ("v1_ldgr_pass", "v1_citation_gate_idem_alt_pass"):
        states = mine(VARIANTS[name])["states"]
        crit = "Ldgr.src" if "ldgr" in name else "Idem.alt"
        assert states[f"ga_alpha|gate|{crit}@1"] == [None, True], name
        assert RECORDED["variants"][name]["states"][f"ga_alpha|gate|{crit}@1"] == [None, True]
    assert mine(VARIANTS["v1_non_citation_pass"])["states"]["ga_alpha|gate|Idem.pat@1"] == [None, False]


def test_real_carr_d1_is_strict_a_pass_or_partial_with_no_usable_state_is_refused():
    """The mini registry has no Carr.D1, so call the check directly with the REAL constants (no patching)."""
    fresh = load_tracker()
    base = dict(record_version=2, citation_state_caveat=False, na=None)
    check = fresh._e63_check_citation_fields
    for verdict in ("PASS", "PARTIAL"):
        for state in (None, "unsourced", "refuted"):
            with pytest.raises(fresh.ElevatedInputError):
                check(dict(base, citation_state=state), "t", verdict, "gate", "Carr.D1")
    check(dict(base, citation_state="sourced"), "t", "PARTIAL", "gate", "Carr.D1")
    check(dict(base, citation_state="sourced"), "t", "PASS", "gate", "Carr.D1")
    check(dict(base, citation_state="sourced_ocr_unverified", citation_state_caveat=True), "t", "PASS", "gate", "Carr.D1")
    check(dict(base, citation_state=None), "t", "NO_DETECTOR", "gate", "Carr.D1")            # not strict below PARTIAL
    check(dict(base, citation_state=None, citation_state_caveat=True), "t", "PASS", "gate", "Ldgr.source_presence")   # Ldgr is lenient


def test_a_v1_record_on_the_real_carr_d1_reads_as_null_with_the_caveat():
    fresh = load_tracker()
    r = dict(record_version=1)
    fresh._e63_check_citation_fields(r, "t", "PASS", "gate", "Carr.D1")
    assert r["citation_state"] is None and r["citation_state_caveat"] is True
