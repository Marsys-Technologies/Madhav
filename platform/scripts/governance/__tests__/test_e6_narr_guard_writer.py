"""test_e6_narr_guard_writer.py: NARR-GUARD (REGISTRY_REVISION 16, N-94): what the E5.1 certificate writer does with a coupled Narr N/A, and Q8 (the Carr.D1 certificate's caveat).

A separate module from test_e6_narr_guard.py because the E5.1 harness (`env`, autouse) re-points asset_census.ROOT at a temp repo, which the evidence-pointer checks of the
declaration tests must not see (the same reason test_e6_s3_cert_writer.py is separate)."""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import carriage_d1 as d1  # noqa: E402
import nikasha_certify as nc  # noqa: E402
import test_e6_decl_latta as dl  # noqa: E402
from test_e5_1_certify import (  # noqa: E402,F401  (fixtures + helpers of the E5.1 suite)
    ENV, FP, RUN, W1, W2, WH, env, kw, ledger, lines, refused, session_repo, write_census_file,
)

AID = "bg_phaladeepika_latta"
NARR = list(ac.NARR_CHECKS)
NCRIT = "Narr.agree"
RID = "Narr.agree#measured:no-prose"
SPEC, ROWS, CHUNKS, ENTRY = dl.SPEC, dl.ROWS, dl.CHUNKS, dl.ENTRY
TYPES = {"table_version": "text", "graha": "text", "count_from_graha": "smallint", "direction": "text", "effect_description": "text", "affliction_condition": "text",
         "source_citation": "text", "verse_ref": "text", "created_at": "timestamp with time zone"}


def _d1(rows=None, state="sourced_ocr_unverified"):
    return d1.d1_measure(SPEC, state, CHUNKS, copy.deepcopy(rows if rows is not None else ROWS), AID)


def _narr_records():
    ctx = dict(table=AID, own={AID: (dl.COLS, TYPES, {})}, tests=(), vocabulary=set(), counts=None, paths=[], written={AID: set(dl.COLS)})
    return {c: v for c, v in ac.prose_checks(AID, ENTRY, ctx).items() if c in NARR}


def _census(d1rec, with_narr=True):
    ms = dict(_narr_records()) if with_narr else {}
    if d1rec is not None:
        ms["Carr.D1"] = d1rec
    return write_census_file(ms, asset=AID, layer="L0", generated=RUN)


def _req(ledger, path, criterion, verdict, **more):
    d = kw(ledger, asset=AID, criterion=criterion, verdict=verdict, census_path=path, **more)
    d.pop("cell", None)
    return d


def _bad_rows():
    return [dict(r, effect_description="Quarrels.") if r["graha"] == "Venus" else r for r in ROWS]


def test_a_coupled_narr_na_is_certifiable_while_carr_d1_reads_pass(ledger):
    rec = nc.write_certification(**_req(ledger, _census(_d1()), NCRIT, "N/A", na_rule_id=RID)).record
    assert rec["verdict"] == "N/A" and rec["na"]["rule_id"] == RID and rec["na"]["cause"] == "no-prose" and rec["na"]["basis"] == "measured_cause"
    assert rec["citation_state"] is None and rec["citation_state_caveat"] is False        # Narr is not a citation criterion: the coupling adds no state of its own


@pytest.mark.parametrize("rows, state", [(_bad_rows(), "sourced_ocr_unverified"), ([r for r in ROWS if r["graha"] != "Sun"], "sourced_ocr_unverified"),
                                          (None, "unsourced"), (None, "refuted")])
def test_MUTATION_a_coupled_narr_na_is_refused_while_carr_d1_is_not_pass(ledger, rows, state):
    before = ledger.read_bytes()
    with pytest.raises(nc.CertificationRefused) as ei:
        nc.write_certification(**_req(ledger, _census(_d1(rows=rows, state=state)), NCRIT, "N/A", na_rule_id=RID))
    assert ei.value.code == "na_coupling_unmet" and "Narr N/A rests on Carr.D1 PASS (coupled): Carr.D1 reads" in str(ei.value)
    assert ledger.read_bytes() == before


def test_MUTATION_a_coupled_narr_na_with_no_carr_d1_in_the_census_is_refused(ledger):
    before = ledger.read_bytes()
    refused(ledger, "na_coupling_unmet", **{k: v for k, v in _req(ledger, _census(None), NCRIT, "N/A", na_rule_id=RID).items() if k != "ledger_path"})
    assert ledger.read_bytes() == before


def test_an_uncoupled_narr_na_is_certifiable_exactly_as_before_whatever_carr_d1_reads(ledger):
    ms = {c: ac._na("prose_fields [] declared and no write to a column the declarations treat as narration", "no-prose") for c in NARR}
    ms["Carr.D1"] = dict(v="FAIL", measured="x")
    p = write_census_file(ms, asset="bg_yogas", layer="L0", generated=RUN)
    rec = nc.write_certification(**dict(_req(ledger, p, NCRIT, "N/A", na_rule_id=RID), asset="bg_yogas")).record
    assert rec["verdict"] == "N/A" and rec["na"]["rule_id"] == RID


def test_Q8_the_latta_carr_d1_certificate_carries_the_ocr_english_caveat_and_the_narr_coupling_does_not_change_it(ledger):
    """Carr.D1 reads PASS on sourced_ocr_unverified: its certificate record says so (citation_state_caveat true: the fidelity is against OCR English, not the printed book).
    Writing the coupled Narr N/A certificate beside it, and a census that carries the coupled Narr records, leaves that record unchanged."""
    alone = nc.write_certification(**_req(ledger, _census(_d1(), with_narr=False), "Carr.D1", "PASS")).record
    assert alone["verdict"] == "PASS" and alone["citation_state"] == "sourced_ocr_unverified" and alone["citation_state_caveat"] is True
    narr = nc.write_certification(**_req(ledger, _census(_d1()), NCRIT, "N/A", na_rule_id=RID)).record
    assert narr["citation_state"] is None and narr["citation_state_caveat"] is False
    with_coupling = nc.write_certification(**_req(ledger, _census(_d1()), "Carr.D1", "PASS")).record
    assert (with_coupling["citation_state"], with_coupling["citation_state_caveat"]) == (alone["citation_state"], alone["citation_state_caveat"]) == ("sourced_ocr_unverified", True)
    assert {k: v for k, v in with_coupling.items() if k in ("verdict", "criterion", "citation_state", "citation_state_caveat", "detector", "kind")} == \
        {k: v for k, v in alone.items() if k in ("verdict", "criterion", "citation_state", "citation_state_caveat", "detector", "kind")}
