"""test_e6_s1_cert_writer.py: E6 S1 (REGISTRY_REVISION 13): what the E5.1 certificate writer does with an EARNED Null PASS.

A separate module (as test_e6_s3_cert_writer.py): the E5.1 harness (`env`, autouse) re-points asset_census.ROOT at a temp repo. The writer's R5 refusal
(`capped_verdict`: a Null PASS the census rollup would not honour) stays for every Null PASS EXCEPT the one the census itself earned: both Null records of the
asset carry the verified null_convention block (`ac.null_lift_earned`, the same function the rollup runs, read from the census record, never typed by the caller)."""
from __future__ import annotations

import copy
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import nikasha_certify as nc  # noqa: E402
import test_e6_s1_null_convention as s1  # noqa: E402
from test_e5_1_certify import (  # noqa: E402,F401  (fixtures + helpers of the E5.1 suite)
    ENV, FP, FP2, RUN, W1, W2, WH, commit_all, cert_in_repo, doctor, env, fresh_repo, kw, ledger, lines, refused,
    session_repo, write_census_file,
)

SD, BR = s1.SD, s1.BR


def _request(ledger, ms, criterion=SD, **over):
    p = write_census_file(ms, asset="bg_ontology", layer="L0", generated=RUN, rec=dict(target_columns=["id", "effect_description"]))
    return kw(ledger, criterion=criterion, verdict="PASS", census_path=p, **over)


def test_an_earned_null_pass_is_certifiable_for_each_of_the_two_checks(ledger):
    ms = s1._lifted()
    for crit in (SD, BR):
        rec = nc.write_certification(**_request(ledger, copy.deepcopy(ms), crit)).record
        assert rec["verdict"] == "PASS" and rec["criterion"] == crit and rec["gate"] == "Null"


def test_an_undeclared_null_pass_is_still_refused_as_capped(ledger):
    ms = {SD: dict(v="PASS", measured="m"), BR: dict(v="PASS", measured="m")}
    refused(ledger, "capped_verdict", **{k: v for k, v in _request(ledger, ms).items() if k != "ledger_path"})


def test_a_forged_or_one_sided_lift_is_refused_as_capped(ledger):
    ms = s1._lifted()
    forged = copy.deepcopy(ms)
    forged[SD]["null_convention"]["verified"] = False
    refused(ledger, "capped_verdict", **{k: v for k, v in _request(ledger, forged).items() if k != "ledger_path"})
    one = {SD: copy.deepcopy(ms[SD]), BR: dict(v="PASS", measured="m")}                    # the sibling carries no verified block
    refused(ledger, "capped_verdict", **{k: v for k, v in _request(ledger, one).items() if k != "ledger_path"})
    missing = {SD: copy.deepcopy(ms[SD])}                                                   # the sibling is not in the census at all
    refused(ledger, "capped_verdict", **{k: v for k, v in _request(ledger, missing).items() if k != "ledger_path"})


def test_a_narr_fidelity_pass_is_still_refused_whatever_the_null_block_says(ledger):
    ms = {"Narr.fidelity_test": dict(v="PASS", measured="m", null_convention=copy.deepcopy(s1._lifted()[SD]["null_convention"]))}
    refused(ledger, "capped_verdict", **{k: v for k, v in _request(ledger, ms, "Narr.fidelity_test").items() if k != "ledger_path"})
