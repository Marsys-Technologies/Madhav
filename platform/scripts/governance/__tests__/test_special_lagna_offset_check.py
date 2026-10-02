"""Offline tests for the special_lagna_offset W7 check script (PR #2971): no database, no network.

The script lives with the lane's evidence; this file pins that it PASSES the declared change and FAILS
every deviation (each C-check has a tamper case), so the check cannot be a vacuous green.
"""
from __future__ import annotations

import copy
import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
SCRIPT = ROOT.parent / "00_ARCHITECTURE/briefs/suvarna/exec/s_l1_attribution_hooks/evidence/special_lagna_offset_check.py"
spec = importlib.util.spec_from_file_location("special_lagna_offset_check", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

AYAS = ["lahiri_chitrapaksha", "true_chitra", "krishnamurti", "raman", "surya_siddhanta_classical"]
SUBJECTS = ["BHAVA_LAGNA", "GHATI_LAGNA", "HORA_LAGNA", "INDU_LAGNA", "SREE_LAGNA", "VARNADA_LAGNA", "VIGHATI_LAGNA"]


def _before():
    rows = []
    for aya in AYAS:
        for s in SUBJECTS:
            for k in M.ALL_KEYS:
                flag_nak = "t" if (s, aya) in {("BHAVA_LAGNA", "surya_siddhanta_classical"), ("VIGHATI_LAGNA", "raman")} else "f"
                rows.append({
                    "ayanamsha_id": aya, "fact_subject": s, "fact_key": k,
                    "fact_value_text": "" if k in ("longitude_sidereal", "pada", "house_d1") else f"{k}-{s}",
                    "fact_value_num": {"longitude_sidereal": "123.456", "pada": "2", "house_d1": "5"}.get(k, ""),
                    "near_sign_boundary_flag": "false", "near_nakshatra_boundary_flag": "true" if flag_nak == "t" else "false",
                    "vargottama_flag_at_point": "false", "formula_provenance_text": f"old {s}",
                })
    return rows


def _after(before):
    out = copy.deepcopy(before)
    for r in out:
        s, aya = r["fact_subject"], r["ayanamsha_id"]
        if s in M.MOVED:
            r["formula_provenance_text"] = f"new {s}"
            if r["fact_key"] == "longitude_sidereal":
                r["fact_value_num"] = str(123.456 + M.EXPECTED_DELTA_DEG)
            flip = M.EXPECTED_NAK_FLAG_FLIPS.get((s, aya))
            if flip:
                r["near_nakshatra_boundary_flag"] = "true" if flip[1] == "t" else "false"
    return out


def _fails(after, before=None):
    return M.check_states(before or _before(), after)["failures"]


def test_declared_change_passes():
    assert _fails(_after(_before())) == []


def test_row_count_and_key_set():
    a = _after(_before())
    assert any(f.startswith("C1") for f in _fails(a[:-1]))
    assert any(f.startswith("C1") for f in _fails(a + [copy.deepcopy(a[0])]))


@pytest.mark.parametrize("subject", SUBJECTS)
@pytest.mark.parametrize("key", M.CLASS_KEYS)
def test_any_class_value_change_fails(subject, key):
    a = _after(_before())
    r = next(x for x in a if x["fact_subject"] == subject and x["fact_key"] == key and x["ayanamsha_id"] == "raman")
    r["fact_value_text"] = r["fact_value_text"] + "x" if r["fact_value_text"] else ""
    r["fact_value_num"] = str(float(r["fact_value_num"]) + 1) if r["fact_value_num"] else ""
    assert any(f.startswith("C2") for f in _fails(a))


def test_unmoved_subject_any_column_change_fails():
    for col, new in (("fact_value_num", "124"), ("formula_provenance_text", "changed"), ("near_sign_boundary_flag", "true")):
        a = _after(_before())
        r = next(x for x in a if x["fact_subject"] == "VARNADA_LAGNA" and x["fact_key"] == "longitude_sidereal")
        r[col] = new
        assert any(f.startswith(("C3", "C5", "C6")) for f in _fails(a)), col


def test_longitude_delta_must_be_the_declared_offset():
    for bad in (0.0, -0.2, -0.2345, 0.2324):
        a = _after(_before())
        r = next(x for x in a if x["fact_subject"] == "HORA_LAGNA" and x["fact_key"] == "longitude_sidereal")
        r["fact_value_num"] = str(123.456 + bad)
        assert any(f.startswith("C4") for f in _fails(a)), bad
    a = _after(_before())  # inside the tolerance still passes
    r = next(x for x in a if x["fact_subject"] == "HORA_LAGNA" and x["fact_key"] == "longitude_sidereal")
    r["fact_value_num"] = str(123.456 + M.EXPECTED_DELTA_DEG + 0.0009)
    assert _fails(a) == []


def test_longitude_delta_wraps_around_360():
    b, a = _before(), None
    for r in b:
        if r["fact_key"] == "longitude_sidereal" and r["fact_subject"] in M.MOVED:
            r["fact_value_num"] = "0.1"
    a = _after(b)
    for r in a:
        if r["fact_key"] == "longitude_sidereal" and r["fact_subject"] in M.MOVED:
            r["fact_value_num"] = str((0.1 + M.EXPECTED_DELTA_DEG) % 360)
    assert _fails(a, b) == []


def test_nakshatra_flag_flips_exactly_as_declared():
    a = _after(_before())
    next(x for x in a if x["fact_subject"] == "HORA_LAGNA" and x["ayanamsha_id"] == "raman")["near_nakshatra_boundary_flag"] = "true"
    assert any(f.startswith("C5") for f in _fails(a))          # undeclared flip
    a = _after(_before())
    next(x for x in a if (x["fact_subject"], x["ayanamsha_id"]) == ("GHATI_LAGNA", "true_chitra"))["near_nakshatra_boundary_flag"] = "false"
    assert any(f.startswith("C5") for f in _fails(a))          # declared flip missing on one key
    a = _after(_before())
    next(x for x in a if x["fact_subject"] == "SREE_LAGNA")["vargottama_flag_at_point"] = "true"
    assert any(f.startswith("C5") for f in _fails(a))


def test_provenance_must_change_on_the_four_moved_subjects_only():
    a = _after(_before())
    next(x for x in a if x["fact_subject"] == "GHATI_LAGNA")["formula_provenance_text"] = "old GHATI_LAGNA"
    assert any(f.startswith("C6") for f in _fails(a))


def test_non_canonical_chart_reports_class_changes_without_failing_them():
    a = _after(_before())
    next(x for x in a if x["fact_subject"] == "HORA_LAGNA" and x["fact_key"] == "sign")["fact_value_text"] = "Other"
    res = M.check_states(_before(), a, "1c826d5a-41cb-4450-b4dc-59d440e5f75a")
    assert not [f for f in res["failures"] if f.startswith("C2")] and res["info"]


def test_reader_is_select_only(monkeypatch):
    with pytest.raises(AssertionError):
        M._query("delete from chart_facts")
    with pytest.raises(AssertionError):
        M._query("select 1; delete from chart_facts")


# ---- read-only enforcement: the script must not depend on the operator's connection ----------------------------
class _Proc:
    def __init__(self, out):
        self.stdout = out


@pytest.fixture
def fake_db(monkeypatch):
    """Replace subprocess.run: record every call (command + env) and answer from `answers`."""
    calls, state = [], {"ro": "on"}
    monkeypatch.setattr(M, "_READ_ONLY_VERIFIED", False)
    monkeypatch.delenv("FLIP_READER", raising=False)

    def fake_run(cmd, check, capture_output, text, env):
        sql = cmd[-1]
        calls.append({"cmd": cmd, "env": env, "sql": sql})
        if "transaction_read_only" in sql:
            return _Proc(state["ro"])
        return _Proc("a\tb\n")
    monkeypatch.setattr(M.subprocess, "run", fake_run)
    return calls, state


@pytest.mark.parametrize("answer", ["off\n", "", "\n", "ON\n", "on\noff\n", "error\n"])
def test_non_read_only_session_refuses_and_sends_no_data_query(fake_db, answer):
    calls, state = fake_db
    state["ro"] = answer
    with pytest.raises(M.NotReadOnly):
        M._query("select 1")
    assert len(calls) == 1 and "transaction_read_only" in calls[0]["sql"]  # the data query was never sent


def test_read_only_session_runs_and_is_verified_once(fake_db):
    calls, _ = fake_db
    assert M._query("select 1") == [["a", "b"]]
    assert M._query("select 2") == [["a", "b"]]
    assert sum("transaction_read_only" in c["sql"] for c in calls) == 1 and len(calls) == 3


def test_pgoptions_requests_read_only_and_keeps_the_operators_options(fake_db, monkeypatch):
    calls, _ = fake_db
    monkeypatch.setenv("PGOPTIONS", "-c statement_timeout=5000")
    M._query("select 1")
    for c in calls:
        assert "-c default_transaction_read_only=on" in c["env"]["PGOPTIONS"]
        assert "-c statement_timeout=5000" in c["env"]["PGOPTIONS"]


def test_flip_reader_path_is_verified_too(fake_db, monkeypatch):
    calls, state = fake_db
    monkeypatch.setenv("FLIP_READER", "/some/reader.sh")
    state["ro"] = "off\n"
    with pytest.raises(M.NotReadOnly):
        M._query("select 1")
    assert calls[0]["cmd"][0] == "/some/reader.sh"


def test_main_refuses_with_exit_2_on_a_non_read_only_session(fake_db, capsys):
    _, state = fake_db
    state["ro"] = "off\n"
    assert M.main(["--snapshot", "482012f1-710e-4a25-994a-93821f5871aa", "--out", "/nonexistent/x.json"]) == 2
    assert "REFUSED" in capsys.readouterr().out
