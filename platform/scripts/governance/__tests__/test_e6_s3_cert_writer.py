"""test_e6_s3_cert_writer.py: E6 S3 (REGISTRY_REVISION 12): what the E5.1 certificate writer does with the S3 census cells.

A separate module because the E5.1 harness (`env`, autouse) re-points asset_census.ROOT at a temp repo, which the evidence-pointer checks of
test_e6_s3_alias_ldgr.py must not see. Closed in production since S3: the legacy null-state Ldgr write path. A DECLARED Ldgr / alias cell is applicable
by the asset's declaration, not the column pattern, so the writer does not refuse its PASS on a column outside the pattern; an undeclared one is still refused."""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import nikasha_certify as nc  # noqa: E402
from test_e5_1_certify import (  # noqa: E402,F401  (fixtures + helpers of the E5.1 suite)
    ENV, FP, FP2, RUN, W1, W2, WH, commit_all, cert_in_repo, doctor, env, fresh_repo, kw, ledger, lines, refused,
    session_repo, write_census_file,
)

LDGR, ALIAS = "Ldgr.source_presence", "Vocab.alias"



def test_the_legacy_null_state_ldgr_write_path_is_closed_in_production():
    assert nc.LDGR_NULL_STATE_WRITE_ALLOWED is False
    import importlib
    src = (HERE.parent / "nikasha_certify.py").read_text(encoding="utf-8")
    assert re.search(r"^LDGR_NULL_STATE_WRITE_ALLOWED = False$", src, re.M)
    assert importlib.import_module("nikasha_certify").LDGR_NULL_STATE_WRITE_ALLOWED is False


def test_an_ldgr_pass_with_no_state_in_the_cell_is_refused_by_default(ledger):
    before = ledger.read_bytes()
    refused(ledger, "citation_state_missing", **{k: v for k, v in kw(ledger, criterion=LDGR, verdict="PASS", cell=dict(v="PASS"),
                                                                        rec=dict(target_columns=["id", "source_citation"])).items() if k != "ledger_path"})
    assert ledger.read_bytes() == before


def test_a_declared_ldgr_pass_on_a_column_outside_the_pattern_is_certifiable_and_an_undeclared_one_is_not(ledger):
    cols = ["id", "citation"]                                          # `citation` is not one of CITATION_COLUMNS
    ok = nc.write_certification(**kw(ledger, criterion=LDGR, verdict="PASS", cell=dict(v="PASS", citation_state="sourced", declared=True),
                                     rec=dict(target_columns=cols)))
    assert ok.record["citation_state"] == "sourced" and ok.record["citation_state_caveat"] is False
    refused(ledger, "not_applicable_pass", **{k: v for k, v in kw(ledger, criterion=LDGR, verdict="PASS", asset="bg_other",
                                                                     cell=dict(v="PASS", citation_state="sourced"), rec=dict(target_columns=cols)).items()
                                              if k != "ledger_path"})


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_a_declared_unsourced_or_refuted_ldgr_cell_cannot_be_certified_as_a_pass(ledger, state):
    refused(ledger, "citation_state_pass_refused", **{k: v for k, v in kw(ledger, criterion=LDGR, verdict="PASS",
                                                                           cell=dict(v="PASS", citation_state=state, declared=True),
                                                                           rec=dict(target_columns=["id", "citation"])).items() if k != "ledger_path"})


def test_a_declared_alias_pass_on_a_table_without_a_synonyms_column_is_certifiable(ledger):
    rec = nc.write_certification(**kw(ledger, criterion=ALIAS, verdict="PASS", cell=dict(v="PASS", declared=True), rec=dict(target_columns=["graha"]))).record
    assert rec["verdict"] == "PASS" and rec["criterion"] == ALIAS
    refused(ledger, "not_applicable_pass", **{k: v for k, v in kw(ledger, criterion=ALIAS, verdict="PASS", asset="bg_other", cell=dict(v="PASS"),
                                                                     rec=dict(target_columns=["graha"])).items() if k != "ledger_path"})


def test_a_declared_na_is_certifiable_from_the_census_cell_with_the_declared_rule(ledger):
    rec = nc.write_certification(**kw(ledger, criterion=LDGR, verdict="N/A", cell=dict(v="N/A", cause="no-classical-claim", declared=True),
                                     rec=dict(target_columns=["id", "value"]))).record
    assert rec["verdict"] == "N/A" and rec["na"]["rule_id"] == "Ldgr.source_presence#measured:no-classical-claim"
    assert rec["na"]["basis"] == "measured_cause" and rec["na"]["cause"] == "no-classical-claim"


