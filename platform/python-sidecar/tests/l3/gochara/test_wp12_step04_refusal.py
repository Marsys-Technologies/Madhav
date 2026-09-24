"""E-010 — step 4 of the cutover kit must refuse 1085 and 1086 (no database needed).

A constant that names a refusal but is never read is a guard that cannot fire
(CLAUDE.md §N.8). This proves the refusal is a real check: re-adding either
number to the apply set exits 3 before any database is touched.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[3] / "scripts" / "kala_gochara_cutover"


@pytest.fixture(scope="module")
def step04():
    sys.path.insert(0, str(KIT))
    try:
        spec = importlib.util.spec_from_file_location("step04_apply_verify_under_test", KIT / "step04_apply_verify.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path.remove(str(KIT))


def test_apply_set_contains_no_refused_number(step04):
    numbers = {n.split("_", 1)[0] for n in step04.APPLY_SET}
    assert numbers.isdisjoint(step04.REFUSED), numbers & set(step04.REFUSED)
    step04.assert_no_refused_migrations()  # must not exit


@pytest.mark.parametrize("name", [
    "1085_nirmana_l0_bg_transit_rules_vedha_repair.sql",
    "1086_nirmana_l1_gochara_g10_ga_strength_contributor_digest_spec.sql",
    "1086_nirmana_l0_gochara_g10_ga_strength_contributor_digest_spec.sql",  # the old, wrong basename
])
def test_refusal_fires_when_a_refused_number_is_reintroduced(step04, name, capsys):
    """Negative fixture: the detector can go red."""
    with pytest.raises(SystemExit) as exc:
        step04.assert_no_refused_migrations(list(step04.APPLY_SET) + [name])
    assert exc.value.code == 3
    assert "refusing to apply" in capsys.readouterr().err


def test_retired_files_are_really_gone():
    migrations = Path(__file__).resolve().parents[3] / "migrations"
    assert not list(migrations.glob("1085_*")), "1085 was retired (E-010) and must not return"
