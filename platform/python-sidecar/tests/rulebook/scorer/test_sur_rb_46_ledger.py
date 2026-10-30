"""Review VERIFY3 G1-G3 and SUR-RB-46: ledger locations compared by file-system identity, the quarantine never read,
the canonical ledger empty just before step 8 and holding exactly one claim after. Every ledger here is under a
temporary directory (conftest redirects the canonical one)."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from services.rulebook.scorer import config as C
import services.rulebook.scorer.runner as R
from services.rulebook.scorer.runner import RunLedger, RunRefused, score_sample_for_tests

from ._toy import REAL_QUARANTINE_DIR, ledger_lines
from .test_review_fixes import _cfg, _claims, _lock, _record, _two_families, lockfiles  # noqa: F401  (fixture re-used)


def _canon(create=True) -> Path:
    p = Path(C.LEDGER_DIR)
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return p


def _flip(name: str) -> str:
    return name.swapcase()


def _variants(canon: Path, tmp_path: Path):
    """Paths naming the canonical ledger or a place inside it, none string-equal to it."""
    eng = canon.parent
    out = {
        "case of the leaf": str(eng / _flip(canon.name)),
        "case of a parent": str(eng.parent / _flip(eng.name) / canon.name),
        "case, inside": str(eng / _flip(canon.name) / "sub"),
        "dot-dot": str(canon / "x" / ".." ),
        "dot-dot through a sibling": str(eng / "run-ledger-quarantine" / ".." / canon.name),
        "dot-dot, inside": str(canon / "a" / ".." / "b"),
        "trailing slash": str(canon) + "/",
        "double slash": str(canon).replace("/run-ledger", "//run-ledger"),
    }
    link = tmp_path / "link-to-ledger"
    link.symlink_to(canon, target_is_directory=True)
    out["symlink to the ledger"] = str(link)
    link2 = tmp_path / "link-to-engine"
    link2.symlink_to(eng, target_is_directory=True)
    out["symlink to the parent, then the ledger"] = str(link2 / canon.name)
    out["symlink, case variant"] = str(link2 / _flip(canon.name))
    out["symlink, inside"] = str(link / "deeper")
    out["a parent of the ledger"] = str(eng)
    return out


@pytest.mark.parametrize("which", [
    "case of the leaf", "case of a parent", "case, inside", "dot-dot", "dot-dot through a sibling", "dot-dot, inside",
    "trailing slash", "double slash", "symlink to the ledger", "symlink to the parent, then the ledger", "symlink, case variant",
    "symlink, inside", "a parent of the ledger",
])
def test_g1_the_test_entry_refuses_every_alias_of_the_canonical_ledger(tmp_path, lockfiles, which):
    canon = _canon()
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    path = _variants(canon, tmp_path)[which]
    with pytest.raises(RunRefused, match="canonical ledger"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, path)
    assert sorted(os.listdir(canon)) == []  # nothing written into the canonical ledger
    with pytest.raises(RunRefused, match="canonical ledger|quarantine"):  # the inner guard in _run, by identity too
        R._run(ctx, eps, _cfg(), lock, RunLedger(path), _test=True)


def test_g1_a_relative_path_to_the_canonical_ledger_is_refused(tmp_path, lockfiles, monkeypatch):
    canon = _canon()
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    monkeypatch.chdir(canon.parent)
    for rel in ("run-ledger", "./run-ledger", _flip("run-ledger"), "run-ledger/inner", "../" + canon.parent.name + "/run-ledger"):
        with pytest.raises(RunRefused, match="canonical ledger"):
            score_sample_for_tests(ctx, eps, _cfg(), lock, rel)
    assert sorted(os.listdir(canon)) == []


def test_g1_a_case_variant_is_refused_even_before_the_canonical_ledger_exists(tmp_path, lockfiles):
    canon = _canon(create=False)
    assert not canon.exists()
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    with pytest.raises(RunRefused, match="canonical ledger"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, str(canon.parent / _flip(canon.name)))
    assert not canon.exists() or sorted(os.listdir(canon)) == []


def test_g1_production_compares_the_lock_ledger_by_identity(tmp_path, lockfiles, monkeypatch):
    canon = _canon()
    ctx, eps = _two_families()
    lk = _lock(ctx, eps, lockfiles, tmp_path)
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(_record(tmp_path, lk.occurrence_sha256, lk.birth_data_sha256)))
    other = tmp_path / "elsewhere" / "run-ledger"  # same leaf name, a different directory
    other.mkdir(parents=True)
    with pytest.raises(RunRefused, match="fixed, logged ledger"):
        R.score_sample(ctx, eps, _cfg(), replace(lk, ledger_dir=str(other)))
    link = tmp_path / "alias"
    link.symlink_to(canon, target_is_directory=True)
    # an alias of the canonical ledger is the canonical ledger: it passes the ledger check (and stops later, at the step-5 tie)
    with pytest.raises(RunRefused, match="step-5") as e:
        R.score_sample(ctx, eps, _cfg(), replace(lk, ledger_dir=str(link)))
    assert "not the one fixed and logged" not in str(e.value)  # validation compares by identity too (S5)
    assert sorted(os.listdir(canon)) == [] and sorted(os.listdir(other)) == []


# ── G2: the test entry fails closed without the logged lock record ──────────────────────────────────────────
def test_g2_the_test_entry_refuses_when_the_lock_record_cannot_be_read(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(tmp_path / "no-such-ledger.jsonl"))
    with pytest.raises(RunRefused, match="lock record"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, str(tmp_path / "ledger"))
    broken = tmp_path / "broken.jsonl"
    broken.write_text(json.dumps({"id": "OTHER"}) + "\n")  # readable, but without the lock-step-4 entries
    monkeypatch.setattr(C, "LOCK_LEDGER_PATH", str(broken))
    with pytest.raises(RunRefused, match="lock record"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, str(tmp_path / "ledger"))
    assert _claims(tmp_path) == []


# ── G3: a later line with the same id cannot replace the logged claim-key hashes ───────────────────────────
def test_g3_two_differing_lines_with_the_lock_entry_id_refuse(tmp_path):
    lines = ledger_lines("a" * 64, "b" * 64)
    p = tmp_path / "led.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in lines + [lines[2]]) + "\n")  # an identical repeat is harmless
    assert R.read_lock_record(str(p))["occurrence"] == "a" * 64
    forged = dict(lines[2], hashes_verified_by_surrogate={"sample_events_v5_slim.csv": "c" * 64, "BIRTH_DATA_v5.csv": "b" * 64})
    forged_cut = dict(lines[1], files_sha256={"sample_events_v5_slim.csv": "c" * 64, "BIRTH_DATA_v5.csv": "b" * 64})
    p.write_text("\n".join(json.dumps(r) for r in lines + [forged, forged_cut]) + "\n")
    with pytest.raises(RunRefused, match="differing lines"):
        R.read_lock_record(str(p))


# ── SUR-RB-46 (b): the quarantine is never read ────────────────────────────────────────────────────────────
def test_b_the_quarantine_is_refused_as_a_ledger(tmp_path, lockfiles):
    q = Path(C.LEDGER_QUARANTINE_DIR)
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    link = tmp_path / "q-link"
    link.symlink_to(q, target_is_directory=True)
    for path in (q, q / "inner", q.parent / _flip(q.name), link, q / ".." / q.name):
        with pytest.raises(RunRefused, match="quarantine"):
            score_sample_for_tests(ctx, eps, _cfg(), lock, str(path))
        with pytest.raises(RunRefused, match="quarantine"):
            RunLedger(str(path)).has("0" * 64)
    with pytest.raises(RunRefused, match="quarantine"):  # a directory containing the quarantine is refused too
        RunLedger(str(q.parent))


def test_b_the_real_quarantine_path_is_the_one_guarded():
    assert REAL_QUARANTINE_DIR == "/Users/Dev/Archives/madhav-research-library/10_engine/run-ledger-quarantine"


_SEEN = {"on": False, "paths": []}


def _audit(event, args):
    if _SEEN["on"] and event in ("open", "os.listdir", "os.scandir", "os.stat", "os.lstat") and args:
        a = args[0]
        if isinstance(a, (str, bytes, os.PathLike)):
            _SEEN["paths"].append(os.fsdecode(a))


sys.addaudithook(_audit)


def test_b_no_scorer_path_reads_the_quarantine(tmp_path, lockfiles):
    """A full run through the claim (test entry) and a production refusal, with every file open, listing and stat
    recorded: none touches the quarantine (the toy one or the real one)."""
    q = Path(C.LEDGER_QUARANTINE_DIR)
    (q / "toy-quarantined.run").write_text("{}")
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    _SEEN["paths"].clear()
    _SEEN["on"] = True
    try:
        res = score_sample_for_tests(ctx, eps, _cfg(), lock, str(tmp_path / "ledger"))
        with pytest.raises(RunRefused):
            R.score_sample(ctx, eps, _cfg(), replace(lock, ledger_dir=C.LEDGER_DIR))
    finally:
        _SEEN["on"] = False
    assert res["claim_keys"] and len(_claims(tmp_path)) == 1
    seen = [os.path.realpath(p) for p in _SEEN["paths"]]
    assert seen, "the audit hook recorded nothing"
    for root in (os.path.realpath(q), REAL_QUARANTINE_DIR):
        assert not [p for p in seen if p == root or p.startswith(root + os.sep)], root


def test_b_no_scorer_source_names_the_quarantine_except_its_guard():
    import services.rulebook.scorer as S
    import services.rulebook.scorer_calib as SC

    hits = {}
    for pkg in (S, SC):
        for f in sorted(Path(pkg.__file__).parent.glob("*.py")):
            n = sum(1 for line in f.read_text().splitlines() if "run-ledger-quarantine" in line or "LEDGER_QUARANTINE_DIR" in line)
            if n:
                hits[f.name] = n
    assert set(hits) <= {"config.py", "runner.py"} and hits.get("config.py") == 1  # the constant, and the guard that refuses it


# ── SUR-RB-46 (c): the ledger is empty just before step 8 and holds exactly one claim after ─────────────────
def _listing_sha(names):
    return hashlib.sha256(json.dumps(sorted(names)).encode()).hexdigest()


def test_c_a_non_empty_ledger_refuses_before_the_claim(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    led = tmp_path / "ledger"
    led.mkdir()
    (led / ("e" * 64 + ".run")).write_text("{}")  # another sample's claim
    with pytest.raises(RunRefused, match="not empty"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, str(led))
    assert sorted(os.listdir(led)) == ["e" * 64 + ".run"]
    (led / ("e" * 64 + ".run")).unlink()
    (led / ".DS_Store").write_text("")  # anything at all counts
    with pytest.raises(RunRefused, match="not empty"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, str(led))


def test_c_the_empty_listing_and_the_single_claim_are_asserted_and_logged(tmp_path, lockfiles):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    led = tmp_path / "ledger"
    res = score_sample_for_tests(ctx, eps, _cfg(), lock, str(led))
    key = res["claim_keys"]["sample"]
    assert res["ledger_listing_before"] == {"names": [], "sha256": _listing_sha([])}
    assert res["ledger_listing_after"] == {"names": [key + ".run"], "sha256": _listing_sha([key + ".run"]), "claims": 1}
    claim = json.loads((led / (key + ".run")).read_text())
    assert claim["ledger_listing_before_sha256"] == _listing_sha([])
    log = [json.loads(x) for x in (tmp_path / "ledger-listing.jsonl").read_text().splitlines()]
    assert [r["stage"] for r in log] == ["before_claim", "after_claim", "after_run"]
    assert log[0]["sha256"] == _listing_sha([]) and log[0]["names"] == []
    assert log[1]["names"] == log[2]["names"] == [key + ".run"] and log[2]["sha256"] == _listing_sha([key + ".run"])


def test_c_a_second_file_appearing_during_the_run_is_detected(tmp_path, lockfiles, monkeypatch):
    ctx, eps = _two_families()
    lock = _lock(ctx, eps, lockfiles, tmp_path)
    led = tmp_path / "ledger"
    real_score = R.score_family
    calls = {"n": 0}

    def sneaky(*a, **k):
        calls["n"] += 1
        if led.exists() and any(p.suffix == ".run" for p in led.iterdir()):
            (led / ("f" * 64 + ".run")).write_text("{}")
        return real_score(*a, **k)

    monkeypatch.setattr(R, "score_family", sneaky)
    with pytest.raises(R.ScorerError, match="exactly one claim"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, str(led))


# ── SUR-RB-48: the result header discloses the offset-normalised admitted charts, read from s6_admit ───────────
def test_sur_rb_48_header_reports_offset_normalised_charts_from_s6_admit(tmp_path, lockfiles, monkeypatch):
    import services.rulebook.scorer.inputs as I

    ctx, eps = _two_families()
    by_code = {f: {t.code: t for t in c.tl} for f, c in ctx.items()}
    codes = sorted(by_code[C.FAMILY_DASHA])
    flags = {c: (i % 3 == 0) for i, c in enumerate(codes)}

    class Adm(I.AdmissionInputs):
        def __init__(self, d, verify=True):
            self.manifest_sha256 = "a" * 64
            self.horizons = {"charts": {}}
            self.admit = {"ledger": {c: {"admitted": True, "offset_normalised": flags[c]} for c in codes}}

        def timeline(self, code, fam):
            return by_code[fam][code]

    monkeypatch.setattr(I, "AdmissionInputs", Adm)
    lock = _lock(ctx, eps, lockfiles, tmp_path, admission_dir=str(tmp_path / "adm"))
    res = score_sample_for_tests(ctx, eps, _cfg(), lock, str(tmp_path / "ledger"))
    assert res["admitted_charts_offset_normalised"] == sum(flags.values()) > 0
    flags[codes[1]] = None  # a chart without a record refuses before the claim
    sub = tmp_path / "second"
    sub.mkdir()
    with pytest.raises(RunRefused, match="SUR-RB-48"):
        score_sample_for_tests(ctx, eps, _cfg(), lock, str(sub / "ledger"))
    assert not (sub / "ledger").exists()
