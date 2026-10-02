"""The citation-state parity variants (shared by test_e6_3_citation_parity.py and the verdict recorder): mutated copies of the
real-writer v2 golden ledger, RE-CHAINED so that the only defect is the citation field. The record is produced against the
mini registry with E5.1's CITATION_CRITERIA patched to Ldgr.src / Idem.alt and CITATION_STRICT to Idem.alt (the mini registry has
no Carr.D1 / Ldgr.source_presence)."""
from __future__ import annotations

import hashlib
import json
import pathlib

GOLDEN = pathlib.Path(__file__).resolve().parent / "fixtures" / "e6_3_golden" / "ledger_v2.jsonl"
VERDICTS_FILE = pathlib.Path(__file__).resolve().parent / "fixtures" / "e6_3_golden" / "citation_verdicts.json"
MINI_CITATION = ("Ldgr.src", "Idem.alt")
MINI_STRICT = ("Idem.alt",)


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
    "v1_with_declarations_fields_only": variant(lambda r: (r.update(record_version=1), r.pop("citation_state"), r.pop("citation_state_caveat"))),
    "v1_without_fields": variant(lambda r: (r.update(record_version=1), r.pop("citation_state"), r.pop("citation_state_caveat"))),
    "absent_version_without_fields": variant(lambda r: (r.pop("record_version"), r.pop("citation_state"), r.pop("citation_state_caveat"),
                                                          r.pop("declarations_sha256"), r.pop("declarations_version"))),
    "absent_version_with_fields": variant(drop("record_version")),
    "unsourced_no_detector_cell": variant(lambda r: r.update(verdict="NO_DETECTOR", citation_state="unsourced", citation_state_caveat=False, semantic_fingerprint=None),
                                          lambda r: r.get("asset") == "ga_alpha" and r.get("criterion") == "Idem.alt"),
}



def is_(asset, crit):
    return lambda r: r.get("asset") == asset and r.get("criterion") == crit


def v1(r):
    r.update(record_version=1)
    for k in ("citation_state", "citation_state_caveat", "declarations_sha256", "declarations_version"):
        r.pop(k, None)


def to_na(r, state):
    r.update(verdict="N/A", semantic_fingerprint=None, citation_state=state, citation_state_caveat=False,
             na=dict(rule_id="Ldgr.src#columns_any", decision_id="N-22a", basis="applicability_facts", cause=None, facts={}))


def to_partial(r, state):
    r.update(verdict="PARTIAL", semantic_fingerprint=None, citation_state=state, citation_state_caveat=False)


VARIANTS = {
    "clean": variant(lambda r: None),
    "caveat_flipped_on_ocr_pass": variant(lambda r: r.update(citation_state_caveat=False)),
    "caveat_true_on_sourced": variant(lambda r: r.update(citation_state_caveat=True), is_("ga_alpha", "Ldgr.src")),
    "null_state_pass_caveat_false": variant(lambda r: r.update(citation_state_caveat=False), is_("ga_gamma", "Ldgr.src")),
    "null_state_pass_caveat_true": variant(lambda r: None, is_("ga_gamma", "Ldgr.src")),
    "state_on_non_citation_gate": variant(lambda r: r.update(citation_state="sourced"), lambda r: r.get("criterion") == "Idem.pat"),
    "pass_with_unsourced": variant(lambda r: r.update(citation_state="unsourced", citation_state_caveat=False)),
    "pass_with_refuted": variant(lambda r: r.update(citation_state="refuted", citation_state_caveat=False)),
    "unknown_state": variant(lambda r: r.update(citation_state="ocr")),
    "missing_state": variant(lambda r: r.pop("citation_state")),
    "missing_caveat": variant(lambda r: r.pop("citation_state_caveat")),
    "caveat_not_bool": variant(lambda r: r.update(citation_state_caveat=1)),
    "version_3": variant(lambda r: r.update(record_version=3)),
    "version_0": variant(lambda r: r.update(record_version=0)),
    "version_true": variant(lambda r: r.update(record_version=True)),
    "v1_with_fields": variant(lambda r: r.update(record_version=1)),
    "v1_with_declarations_fields_only": variant(lambda r: (r.update(record_version=1), r.pop("citation_state"), r.pop("citation_state_caveat"))),
    "v1_without_fields": variant(v1),
    "v1_ldgr_pass": variant(v1, is_("ga_alpha", "Ldgr.src")),
    "v1_citation_gate_idem_alt_pass": variant(v1, is_("ga_alpha", "Idem.alt")),
    "v1_non_citation_pass": variant(v1, is_("ga_alpha", "Idem.pat")),
    "absent_version_without_fields": variant(lambda r: (r.pop("record_version"), r.pop("citation_state"), r.pop("citation_state_caveat"),
                                                          r.pop("declarations_sha256"), r.pop("declarations_version"))),
    "absent_version_with_fields": variant(lambda r: r.pop("record_version")),
    "unsourced_no_detector_cell": variant(lambda r: r.update(verdict="NO_DETECTOR", citation_state="unsourced", citation_state_caveat=False, semantic_fingerprint=None),
                                          is_("ga_alpha", "Idem.alt")),
    # the declarations binding (gates carry declarations_sha256 / declarations_version; additions null)
    "decl_present_null_on_gate": variant(lambda r: r.update(declarations_sha256=None, declarations_version=None)),
    "decl_fields_absent_on_v2": variant(lambda r: (r.pop("declarations_sha256"), r.pop("declarations_version"))),
    "decl_sha_not_hex": variant(lambda r: r.update(declarations_sha256="xyz")),
    "decl_sha_uppercase": variant(lambda r: r.update(declarations_sha256=r["declarations_sha256"].upper())),
    "decl_sha_wrong_type": variant(lambda r: r.update(declarations_sha256=5)),
    "decl_version_without_sha": variant(lambda r: r.update(declarations_sha256=None, declarations_version="1.0.0")),
    "decl_version_with_absent_sha": variant(lambda r: r.pop("declarations_sha256")),
    "decl_blank_version": variant(lambda r: r.update(declarations_version="  ")),
    "decl_version_not_text": variant(lambda r: r.update(declarations_version=1)),
    "decl_sha_without_version": variant(lambda r: r.update(declarations_version=None)),
    # E5.1's CITATION_STRICT (Carr.D1 in production; Idem.alt here) and the applicability N/A rule
    "strict_pass_null_state": variant(lambda r: r.update(citation_state=None, citation_state_caveat=False), is_("ga_alpha", "Idem.alt")),
    "strict_partial_null_state": variant(lambda r: to_partial(r, None), is_("ga_alpha", "Idem.alt")),
    "strict_partial_unsourced": variant(lambda r: to_partial(r, "unsourced"), is_("ga_alpha", "Idem.alt")),
    "strict_partial_refuted": variant(lambda r: to_partial(r, "refuted"), is_("ga_alpha", "Idem.alt")),
    "strict_partial_sourced": variant(lambda r: to_partial(r, "sourced"), is_("ga_alpha", "Idem.alt")),
    "strict_pass_ocr": variant(lambda r: r.update(citation_state="sourced_ocr_unverified", citation_state_caveat=True), is_("ga_alpha", "Idem.alt")),
    "strict_no_detector_null_state": variant(lambda r: r.update(verdict="NO_DETECTOR", citation_state=None, citation_state_caveat=False, semantic_fingerprint=None),
                                             is_("ga_alpha", "Idem.alt")),
    "applicability_na_with_state": variant(lambda r: to_na(r, "sourced"), is_("ga_alpha", "Ldgr.src")),
    "applicability_na_null_state": variant(lambda r: to_na(r, None), is_("ga_alpha", "Ldgr.src")),
}


PROBE = r'''
import json, sys
sys.path.insert(0, ".")
import nikasha_certify as nc
nc.CITATION_CRITERIA = ("Ldgr.src", "Idem.alt")
nc.CITATION_STRICT = ("Idem.alt",)
nc.CITATION_CAPPED = nc.CITATION_STRICT + ("Ldgr.source_presence",)   # derived at import in E5.1 (S3): re-derive after the mini substitution, as the committed validator copy does
try:
    by_key = nc.parse_ledger(open(sys.argv[1], "rb").read())
    states = {r["cert_id"]: [r["citation_state"], r["citation_state_caveat"], r["declarations_sha256"], r["declarations_version"]]
              for recs in by_key.values() for r in recs if r.get("kind") in ("gate", "addition")}
    print(json.dumps({"verdict": "OK", "states": states}))
except nc.CertificationRefused as e:
    print(json.dumps({"verdict": "REFUSED", "code": e.code}))
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run_e5_1(e51_dir, data):
    """E5.1's own reader's answer for `data`, run in a subprocess over a copy of that worktree's two modules."""
    import shutil
    import subprocess
    import sys
    import tempfile
    d = pathlib.Path(tempfile.mkdtemp())
    try:
        shutil.copy(pathlib.Path(e51_dir) / "nikasha_certify.py", d / "nikasha_certify.py")
        shutil.copy(pathlib.Path(e51_dir) / "asset_census.py", d / "asset_census.py")
        (d / "probe.py").write_text(PROBE)
        (d / "ledger.bin").write_bytes(data)
        out = subprocess.run([sys.executable, "probe.py", "ledger.bin"], capture_output=True, text=True, cwd=str(d)).stdout
        return json.loads(out.strip().splitlines()[-1])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def record(e51_dir, e51_commit):
    """Write fixtures/e6_3_golden/citation_verdicts.json from the REAL E5.1 reader (run: python _e6_3_citation_variants.py)."""
    out = {"e5_1_commit": e51_commit, "citation_criteria": list(MINI_CITATION), "citation_strict": list(MINI_STRICT), "variants": {}}
    for name, data in VARIANTS.items():
        r = run_e5_1(e51_dir, data)
        out["variants"][name] = dict(sha256=sha(data), **r)
    VERDICTS_FILE.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    return out


if __name__ == "__main__":
    import subprocess
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "/Users/Dev/suvarna-engine-lane-e5-1b/platform/scripts/governance"
    commit = subprocess.run(["git", "-C", d, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    res = record(d, commit)
    print(len(res["variants"]), "variants recorded from E5.1", commit)
