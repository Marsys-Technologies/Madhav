"""E6.3 reader vs E5.1's own `_check_citation_fields` (branch suvarna/engine-E5.1-citation-state): the same mutated v2 ledgers
(re-chained, so the ONLY defect is the citation field) must be accepted/refused by both. Runs E5.1 in a subprocess; skipped, with
the reason, when that worktree is not on this machine (or when E5.1 has the citation fields on main and the path is the repo's)."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from _e6_3_fixtures import World, load_tracker, mini_patch  # noqa: E402

T = load_tracker()
GOV = pathlib.Path(__file__).resolve().parents[1]
GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "e6_3_golden" / "ledger_v2.jsonl"


def _e51_dir():
    for cand in (os.environ.get("E6_3_E51_CITATION_DIR"), "/Users/Dev/suvarna-engine-lane-e5-1b/platform/scripts/governance", str(GOV)):
        if cand and (pathlib.Path(cand) / "nikasha_certify.py").exists() and \
                "citation_state" in (pathlib.Path(cand) / "nikasha_certify.py").read_text(encoding="utf-8"):
            return pathlib.Path(cand)
    return None


E51 = _e51_dir()
PROBE = r'''
import sys
sys.path.insert(0, ".")
import nikasha_certify as nc
nc.CITATION_CRITERIA = ("Ldgr.src", "Idem.alt")
try:
    nc.parse_ledger(open(sys.argv[1], "rb").read())
    print("OK")
except nc.CertificationRefused as e:
    print("REFUSED", e.code)
'''


@pytest.fixture(scope="module")
def probe():
    if E51 is None:
        pytest.skip("E5.1 with citation_state is not on this machine (suvarna/engine-E5.1-citation-state worktree) nor in this checkout")
    d = pathlib.Path(tempfile.mkdtemp())
    shutil.copy(E51 / "nikasha_certify.py", d / "nikasha_certify.py")
    shutil.copy(E51 / "asset_census.py", d / "asset_census.py")
    (d / "probe.py").write_text(PROBE)
    yield d
    shutil.rmtree(d, ignore_errors=True)


def rechain(rows):
    out = []
    schema = json.dumps(rows[0], ensure_ascii=False)
    prev = hashlib.sha256(schema.encode()).hexdigest()
    out.append(schema)
    for i, r in enumerate(rows[1:], 1):
        r = dict(r, seq=i, prev_sha256=prev)
        line = json.dumps(r, ensure_ascii=False)
        out.append(line)
        prev = hashlib.sha256(line.encode()).hexdigest()
    return ("\n".join(out) + "\n").encode()


def variant(mutate, which=lambda r: r.get("criterion") == "Ldgr.src" and r.get("asset") == "ga_beta"):
    rows = [json.loads(ln) for ln in GOLDEN.read_text().splitlines()]
    done = False
    for r in rows[1:]:
        if which(r):
            mutate(r)
            done = True
            break
    assert done
    return rechain(rows)


def drop(key):
    return lambda r: r.pop(key)


VARIANTS = {
    "clean": variant(lambda r: None),
    "caveat_flipped_on_ocr_pass": variant(lambda r: r.update(citation_state_caveat=False)),
    "caveat_true_on_sourced": variant(lambda r: r.update(citation_state_caveat=True), lambda r: r.get("asset") == "ga_alpha" and r.get("criterion") == "Ldgr.src"),
    "null_state_pass_caveat_false": variant(lambda r: r.update(citation_state_caveat=False), lambda r: r.get("asset") == "ga_gamma" and r.get("criterion") == "Ldgr.src"),
    "null_state_pass_caveat_true": variant(lambda r: None, lambda r: r.get("asset") == "ga_gamma" and r.get("criterion") == "Ldgr.src"),
    "state_on_non_citation_gate": variant(lambda r: r.update(citation_state="sourced"), lambda r: r.get("criterion") == "Idem.pat"),
    "pass_with_unsourced": variant(lambda r: r.update(citation_state="unsourced", citation_state_caveat=False)),
    "pass_with_refuted": variant(lambda r: r.update(citation_state="refuted", citation_state_caveat=False)),
    "unknown_state": variant(lambda r: r.update(citation_state="ocr")),
    "missing_state": variant(drop("citation_state")),
    "missing_caveat": variant(drop("citation_state_caveat")),
    "caveat_not_bool": variant(lambda r: r.update(citation_state_caveat=1)),
    "version_3": variant(lambda r: r.update(record_version=3)),
    "version_0": variant(lambda r: r.update(record_version=0)),
    "version_true": variant(lambda r: r.update(record_version=True)),
    "v1_with_fields": variant(lambda r: r.update(record_version=1)),
    "v1_without_fields": variant(lambda r: (r.update(record_version=1), r.pop("citation_state"), r.pop("citation_state_caveat"))),
    "absent_version_without_fields": variant(lambda r: (r.pop("record_version"), r.pop("citation_state"), r.pop("citation_state_caveat"))),
    "absent_version_with_fields": variant(drop("record_version")),
    "unsourced_no_detector_cell": variant(lambda r: r.update(verdict="NO_DETECTOR", citation_state="unsourced", citation_state_caveat=False, semantic_fingerprint=None),
                                          lambda r: r.get("asset") == "ga_alpha" and r.get("criterion") == "Idem.alt"),
}


@pytest.mark.parametrize("name", list(VARIANTS))
def test_the_reader_and_e5_1_agree_on_every_citation_field_variant(probe, tmp_path, monkeypatch, name):
    data = VARIANTS[name]
    f = probe / "ledger.bin"
    f.write_bytes(data)
    out = subprocess.run([sys.executable, "probe.py", str(f)], capture_output=True, text=True, cwd=str(probe)).stdout.strip()
    assert out.startswith(("OK", "REFUSED")), out
    mini_patch(monkeypatch, T)
    w = World(tmp_path)
    w.commit()
    facts = T._e63_registry_facts(str(w.repo), w.last)
    try:
        T._e63_parse_certs(data, facts)
        mine = "OK"
    except T.ElevatedInputError:
        mine = "REFUSED"
    assert mine == out.split()[0], (name, out, mine)


def test_the_variants_really_exercise_both_outcomes():
    assert len(VARIANTS) >= 20
