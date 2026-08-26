"""Governance guards for the bg_formula_constants canonical writer seed."""

from brahmagyan.l0_formula_constants import CONSTANTS, seed_formula_constants


def test_writer_seeds_only_operational_formula_constants() -> None:
    ids = {row["constant_id"] for row in CONSTANTS}

    assert "_bug_ka_sangam_confidence_conflation" not in ids
    assert all(row["class"] != "conflation_bug" for row in CONSTANTS)


def test_dry_run_reports_the_ten_w1_operational_constants() -> None:
    assert seed_formula_constants(None, dry_run=True) == {
        "brahma_formula_constants": 10,
    }
