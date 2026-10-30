"""SUR-RB-45 (2): count_blind V3's 95%-bar donor columns, the logged count_blind hash, and v1.5 P3's 95% escalation
read from the sealed file and checked against the scorer's own recount."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from services.rulebook.scorer import config as C
from services.rulebook.scorer.core import FamilyContext, donor_recount
from services.rulebook.scorer.inputs import (
    DONOR_DIAG_COLUMNS,
    DONOR_ELIG_COLUMNS,
    InputError,
    d7_decisions,
    donor_rows,
    read_count_blind,
    share_value,
)
from services.rulebook.scorer.footprint import family_testable
from services.rulebook.scorer.runner import RunRefused, prepare_episodes
from services.rulebook.scorer_calib.cli import p95_escalation

from ._toy import FAKE_COUNT_BLIND_SHA, ledger_lines
from .test_inputs import _count_blind, _csv
from .test_review_fixes import _cfg, _claims, _lock, lockfiles, score_sample  # noqa: F401  (fixture re-used)
from .test_yardstick_v15 import _na_world


def test_v3_columns_are_the_conductors_exact_order():
    assert DONOR_ELIG_COLUMNS == ("threshold", "family", "set", "chart_id", "own_cells", "donors_b_m3", "donors_c_m3", "donors_b_p2", "donors_c_p2",
                                  "imputed_cells_b_p2", "imputed_cells_c_p2", "donors_b_p95", "donors_c_p95", "imputed_cells_b_p95", "imputed_cells_c_p95")
    assert DONOR_DIAG_COLUMNS == ("threshold", "family", "set", "check", "pool_charts", "charts_ge5_donors_m3", "k11_floor_met_m3", "charts_ge5_donors_p2",
                                  "k11_floor_met_p2", "imputed_cell_share_p2", "charts_ge5_donors_p95", "k11_floor_met_p95", "imputed_cell_share_p95")


def _rehash(d):
    run = json.loads((d / "COUNT_BLIND_RUN.json").read_text())
    for nm in ("COUNT_BLIND_DONOR_ELIGIBILITY.csv", "COUNT_BLIND_DONOR_DIAGNOSTIC.csv"):
        run["outputs_sha256"][nm] = hashlib.sha256((d / nm).read_bytes()).hexdigest()
    (d / "COUNT_BLIND_RUN.json").write_text(json.dumps(run))


def test_v3_p95_columns_are_read_and_an_empty_share_stays_empty(tmp_path):
    cb = read_count_blind(str(_count_blind(tmp_path)))
    dr = donor_rows(cb, 5, "dasha")
    assert (dr["charts"]["C001"]["donors_b_p95"], dr["charts"]["C001"]["donors_c_p95"]) == (9, 2)
    assert (dr["charts"]["C001"]["imputed_cells_b_p95"], dr["charts"]["C001"]["imputed_cells_c_p95"]) == (1, 0)
    b, c = dr["checks"]["b"], dr["checks"]["c"]
    assert (b["charts_ge5_donors_p95"], b["k11_floor_met_p95"], b["imputed_cell_share_p95"]) == (16, 1, "0.004000")
    assert (c["charts_ge5_donors_p95"], c["k11_floor_met_p95"], c["imputed_cell_share_p95"]) == (2, 0, "")
    assert share_value("") is None and share_value("0.000000") == 0.0  # empty is "no donor cells", never a zero share


def test_v3_a_v2_file_or_a_reordered_file_is_refused(tmp_path):
    d = _count_blind(tmp_path)
    rows = list(csv.reader(open(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv")))
    _csv(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", rows[0][:10], [r[:10] for r in rows[1:]])  # the V2 columns only
    with pytest.raises(InputError, match="columns"):
        read_count_blind(str(d), verify=False)
    rows2 = list(csv.reader(open(d.parent / "count_blind" / "COUNT_BLIND_DONOR_ELIGIBILITY.csv")))
    hdr = rows2[0][:]
    hdr[11], hdr[12] = hdr[12], hdr[11]  # donors_c_p95 before donors_b_p95
    _csv(d / "COUNT_BLIND_DONOR_ELIGIBILITY.csv", hdr, rows2[1:])
    with pytest.raises(InputError, match="columns"):
        read_count_blind(str(d), verify=False)


@pytest.mark.parametrize("bad", ["0.0123", "1.500000", "-0.100000", "0,012345", "nan"])
def test_v3_a_share_must_be_six_decimals_in_unit_range(tmp_path, bad):
    d = _count_blind(tmp_path)
    rows = list(csv.reader(open(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv")))
    rows[1][12] = bad
    _csv(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", rows[0], rows[1:])
    with pytest.raises(InputError, match="imputed_cell_share_p95"):
        read_count_blind(str(d), verify=False)


def test_v3_a_p95_flag_must_be_0_or_1_and_the_p95_counts_present(tmp_path):
    d = _count_blind(tmp_path)
    rows = list(csv.reader(open(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv")))
    rows[1][11] = "2"
    _csv(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", rows[0], rows[1:])
    with pytest.raises(InputError, match="k11"):
        read_count_blind(str(d), verify=False)
    rows[1][11], rows[1][10] = "1", ""
    _csv(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", rows[0], rows[1:])
    with pytest.raises(InputError, match="charts_ge5_donors_p95 is empty"):
        read_count_blind(str(d), verify=False)
    sub = tmp_path / "e"
    sub.mkdir()
    d2 = _count_blind(sub)
    rows = list(csv.reader(open(d2 / "COUNT_BLIND_DONOR_ELIGIBILITY.csv")))
    rows[1][13] = ""
    _csv(d2 / "COUNT_BLIND_DONOR_ELIGIBILITY.csv", rows[0], rows[1:])
    with pytest.raises(InputError, match="imputed_cells_b_p95 is empty"):
        read_count_blind(str(d2), verify=False)


def test_v3_a_run_record_naming_another_count_blind_hash_is_refused(tmp_path):
    assert read_count_blind(str(_count_blind(tmp_path))).script_sha256 == FAKE_COUNT_BLIND_SHA
    for i, sha in enumerate(("9b58c5f901721656475361d24a92c332be0c4163d81dc14d6c365c1d706e87e8", "", "d" * 64)):  # V2's hash, none, other
        sub = tmp_path / f"s{i}"
        sub.mkdir()
        d = _count_blind(sub)
        run = json.loads((d / "COUNT_BLIND_RUN.json").read_text())
        run["script_sha256"] = sha
        (d / "COUNT_BLIND_RUN.json").write_text(json.dumps(run))
        with pytest.raises(InputError, match="COUNT-BLIND-V3-HASHES"):
            read_count_blind(str(d))
    sub = tmp_path / "t"
    sub.mkdir()
    d = _count_blind(sub)
    run = json.loads((d / "COUNT_BLIND_RUN.json").read_text())
    run["tests_sha256"] = "e" * 64
    (d / "COUNT_BLIND_RUN.json").write_text(json.dumps(run))
    with pytest.raises(InputError, match="tests sha256"):
        read_count_blind(str(d))


def test_v3_the_count_blind_hash_comes_from_the_ledger_entry(tmp_path, monkeypatch):
    d = _count_blind(tmp_path)
    led = tmp_path / "ledger.jsonl"
    lines = ledger_lines()
    lines[-1] = dict(lines[-1], sha256="a" * 64)  # the logged hash is a different one: the toy run is refused
    led.write_text("\n".join(json.dumps(r) for r in lines) + "\n")
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(led))
    with pytest.raises(InputError, match="COUNT-BLIND-V3-HASHES"):
        read_count_blind(str(d))
    led.write_text("\n".join(json.dumps(r) for r in ledger_lines()[:-1]) + "\n")  # no V3 entry at all
    with pytest.raises(InputError, match="not found"):
        read_count_blind(str(d))
    two = ledger_lines() + [dict(ledger_lines()[-1], sha256="a" * 64)]  # a second, different line with the same id
    led.write_text("\n".join(json.dumps(r) for r in two) + "\n")
    with pytest.raises(InputError, match="differing lines"):
        read_count_blind(str(d))


def test_v3_escalation_reads_the_sealed_95_percent_floor_and_share(tmp_path):
    cb = read_count_blind(str(_count_blind(tmp_path)))
    base = d7_decisions(cb, 5, "dasha")
    assert (base["donor_rule_b"], base["donor_charts_b"], base["imputed_share_b"]) == ("p2_90", 18, 0.012345)
    up_b = d7_decisions(cb, 5, "dasha", escalated=["b"])
    assert (up_b["donor_rule_b"], up_b["donor_charts_b"], up_b["imputed_share_b"]) == ("p2_95", 16, 0.004)
    assert up_b["donor_rule_c"] == "p2_90" and up_b["donor_floor_ok"] is True
    up_c = d7_decisions(cb, 5, "dasha", escalated=["c"])
    assert (up_c["donor_rule_c"], up_c["donor_charts_c"]) == ("p2_95", 2) and up_c["donor_floor_ok"] is False
    assert up_c["imputed_share_c"] is None  # empty: no donor cell at 95%; never read as 0
    with pytest.raises(InputError, match="no P2 bar to raise"):
        d7_decisions(cb, 5, "transit", escalated=["b"])  # transit meets the floor under M3
    with pytest.raises(InputError, match="escalated checks"):
        d7_decisions(cb, 5, "dasha", escalated=["x"])


def test_v3_escalation_refuses_a_floor_flag_that_disagrees_with_its_count(tmp_path):
    d = _count_blind(tmp_path)
    rows = list(csv.reader(open(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv")))
    for r in rows[1:]:
        if r[0] == "5" and r[1] == "dasha" and r[3] == "c":
            r[11] = "1"  # says the floor is met with 2 charts
    _csv(d / "COUNT_BLIND_DONOR_DIAGNOSTIC.csv", rows[0], rows[1:])
    _rehash(d)
    with pytest.raises(InputError, match="k11_floor_met_p95 disagrees"):
        d7_decisions(read_count_blind(str(d)), 5, "dasha", escalated=["c"])


def test_v3_gate_escalation_uses_the_sealed_file(tmp_path):
    d = _count_blind(tmp_path)
    a = SimpleNamespace(count_blind=str(d), threshold=5)
    esc = p95_escalation(a, [("dasha", "b")])
    row = esc["families"]["dasha"]
    assert row["sealed"] and row["floor_met_p95"] is True and row["rows"]["b"] == {"rule": "p2_95", "charts_ge5_donors": 16, "k11_floor_met": 1, "imputed_share": 0.004}
    esc2 = p95_escalation(a, [("dasha", "b"), ("dasha", "c")])
    r2 = esc2["families"]["dasha"]
    assert r2["floor_met_p95"] is False and r2["rows"]["c"]["imputed_share"] is None and r2["rows"]["c"]["k11_floor_met"] == 0
    assert esc2["count_blind_script_sha256"] == FAKE_COUNT_BLIND_SHA
    prov = p95_escalation(SimpleNamespace(count_blind=None, threshold=5), [("dasha", "b")])
    assert prov["source"].startswith("PROVISIONAL") and prov["families"]["dasha"]["sealed"] is False


# ── the runner: a sealed p2_95 rule is checked against count_blind's 95% columns and the recount ─────────────
def _p2_world():
    ctx, eps = _na_world(0.08)
    t = FamilyContext(C.FAMILY_TRANSIT, ctx.tl, [replace(u, plane=C.FAMILY_TRANSIT) for u in ctx.units])
    return {C.FAMILY_DASHA: ctx, C.FAMILY_TRANSIT: t}, {C.FAMILY_DASHA: list(eps), C.FAMILY_TRANSIT: list(eps)}


def _escalated_lock(ctx, eps, lockfiles, tmp_path):
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    d7 = {f: dict(v) for f, v in lock.d7.items()}
    chk = lock.donor_counts[C.FAMILY_DASHA]["checks"]["b"]
    assert chk["k11_floor_met_m3"] == 0  # the P1 trigger fires: P2 applies to dasha (b)
    d7[C.FAMILY_DASHA]["donor_rule_b"] = "p2_95"
    d7[C.FAMILY_DASHA]["donor_charts_b"] = chk["charts_ge5_donors_p95"]
    d7[C.FAMILY_DASHA]["testable"] = family_testable(ctx[C.FAMILY_DASHA], prepare_episodes(ctx[C.FAMILY_DASHA], eps[C.FAMILY_DASHA])[0],
                                                      donor_rules={"b": "p2_95", "c": d7[C.FAMILY_DASHA]["donor_rule_c"]})["testable"]
    return replace(lock, d7=d7)


def _refusal(ctx, eps, lock):
    with pytest.raises(RunRefused) as e:
        score_sample(ctx, eps, _cfg(), lock)
    return str(e.value)


def test_v3_runner_recount_includes_the_95_percent_columns(tmp_path, lockfiles):
    ctx, eps = _p2_world()
    rec = donor_recount(ctx[C.FAMILY_DASHA], eps[C.FAMILY_DASHA])
    some = next(iter(rec["charts"].values()))
    assert set(some) == set(DONOR_ELIG_COLUMNS[4:]) and set(rec["checks"]["b"]) == set(DONOR_DIAG_COLUMNS[4:])
    lock = _escalated_lock(ctx, eps, lockfiles, tmp_path)
    msg = _refusal(ctx, eps, lock)  # consistent: the only problems left are the toy world's units versus the lockfiles manifest
    assert all("units scored are not those of the hashed manifest" in p for p in msg.split(": ", 1)[1].split("; ")), msg
    bad = {f: {"charts": {k: dict(v) for k, v in d["charts"].items()}, "checks": {k: dict(v) for k, v in d["checks"].items()}} for f, d in lock.donor_counts.items()}
    first = sorted(bad[C.FAMILY_DASHA]["charts"])[0]
    bad[C.FAMILY_DASHA]["charts"][first]["donors_b_p95"] += 1
    assert "COUNT_BLIND_DONOR_ELIGIBILITY" in _refusal(ctx, eps, replace(lock, donor_counts=bad))
    bad2 = {f: {"charts": d["charts"], "checks": {k: dict(v) for k, v in d["checks"].items()}} for f, d in lock.donor_counts.items()}
    bad2[C.FAMILY_DASHA]["checks"]["b"]["imputed_cell_share_p95"] = "0.999999"
    assert "COUNT_BLIND_DONOR_DIAGNOSTIC" in _refusal(ctx, eps, replace(lock, donor_counts=bad2))
    d7 = {f: dict(v) for f, v in lock.d7.items()}
    d7[C.FAMILY_DASHA]["donor_charts_b"] = lock.donor_counts[C.FAMILY_DASHA]["checks"]["b"]["charts_ge5_donors_p95"] + 1
    assert "charts_ge5_donors_p95" in _refusal(ctx, eps, replace(lock, d7=d7))
    gone = {f: {"charts": d["charts"], "checks": {k: dict(v) for k, v in d["checks"].items()}} for f, d in lock.donor_counts.items()}
    for k in ("charts_ge5_donors_p95", "k11_floor_met_p95", "imputed_cell_share_p95"):
        gone[C.FAMILY_DASHA]["checks"]["b"].pop(k)
    assert "no p95 floor columns" in _refusal(ctx, eps, replace(lock, donor_counts=gone))
    assert _claims(tmp_path) == []
