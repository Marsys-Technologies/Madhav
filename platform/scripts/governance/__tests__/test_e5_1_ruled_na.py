"""test_e5_1_ruled_na.py -- SS N-146: E5.1 admits ONE N/A on a criterion whose registry detector is NONE.

Before: `build_record` refused every verdict but NO_DETECTOR for a criterion with detector NONE (Earn.service_state, Carr.D2, Carr.D3 at registry
revision 25), although the census MEASURES N/A there under declared rules (N-72 / N-73 / N-22) and E6.3's reader accepts such a certificate: no asset could
reach every required criterion. Now a GATE's N/A is recordable on such a criterion ONLY when ALL hold: the census holds a cell that reads N/A (not inconclusive)
with a registered cause; the rule id `<criterion>#measured:<cause>` is declared in NA_RULE_DECISIONS with a real (non-blank, non-placeholder) decision; the record's
decision id is that declared one. PASS / PARTIAL / FAIL / ERRORED stay refused, NO_DETECTOR stays recordable, an addition's N/A stays refused, an N/A with no census
cell (applicability) stays refused, and every criterion WITH a detector keeps its N/A path byte for byte.

  1. the admission / refusal matrix (one test or table row per mutant)
  2. the enumeration SS asked for: exactly which rules become certifiable, pinned
  3. nothing else moved: registry revision + fingerprint, certificate schema constants
  4. end to end on a scratch git repo: 25 certificates of bg_phaladeepika_latta through write_certification, read back through elevated_report counts

Offline: tmp ledgers, tmp census files, scratch repos; no database, no network.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
GOV = HERE.parent
REPO = GOV.parents[2]
sys.path.insert(0, str(GOV))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import asset_dispositions as ad  # noqa: E402
import nikasha_certify as nc  # noqa: E402
import nikasha_stale_certs as sc  # noqa: E402
# the E5.1 suite's own harness: the autouse `env` fixture (tmp control dir, scratch repo as ac.ROOT), `ledger`, and the request builder
from test_e5_1_certify import MEAS_NA, env, kw, ledger, lines, refused, session_repo  # noqa: E402,F401

# The three rules a registry-detector-NONE criterion can carry at REGISTRY_REVISION 25, with their decisions. SS asked for this list: the test below FAILS when
# the set changes (a new NONE-detector criterion, a new rule for one, a reworded decision) until a reviewer edits it knowingly.
CERTIFIABLE = {
    "Carr.D2#measured:not-the-declared-carriage": "N-72 (S2, declaration-keyed); N-73 (2); N-22/N-22a row 15 (not-chosen stays refused)",
    "Carr.D3#measured:not-the-declared-carriage": "N-72 (S2, declaration-keyed); N-73 (2); N-22/N-22a row 15 (not-chosen stays refused)",
    "Earn.service_state#measured:not-a-service": "N-22/N-22a row 9 (AMENDED, principles 2, 3, 5); N-72 (not-a-service keyed on the declared kind)",
}


def ruled(rid="Carr.D2#measured:not-the-declared-carriage", **over):
    """A valid ruled N/A request on a NONE-detector criterion: the verdict is read from the census cell."""
    crit, _s, rest = rid.partition("#")
    d = dict(criterion=crit, verdict=None, cell=dict(v="N/A", measured="not the declared check", cause=rest[len("measured:"):]))
    d.update(over)
    return d


# ───────────────────────── 1. the matrix ─────────────────────────

@pytest.mark.parametrize("rid", sorted(CERTIFIABLE))
def test_a_measured_declared_na_on_a_detector_none_criterion_is_recorded_and_is_not_a_pass(ledger, rid):
    crit = rid.partition("#")[0]
    assert ac.CRITERION_REGISTRY[crit]["detector"] == "NONE"
    rec = nc.write_certification(**kw(ledger, **ruled(rid))).record
    assert rec["verdict"] == "N/A" and rec["detector"] == "NONE" and rec["basis"] is None
    assert rec["na"] == dict(rule_id=rid, decision_id=ac.NA_RULE_DECISIONS[rid], basis="measured_cause", cause=rid.partition("measured:")[2], facts=None)
    assert rec["semantic_fingerprint"] and rec["writer_hashes_verified"] is True        # a measured N/A goes stale like a PASS
    assert rec["cert_key"] == f"bg_ontology|gate|{crit}" and rec["cross_checked"] is True
    assert lines(ledger)[-1] == rec


def test_the_caller_verdict_is_only_a_cross_check_and_the_rule_id_may_be_stated(ledger):
    rid = "Earn.service_state#measured:not-a-service"
    r = nc.write_certification(**kw(ledger, **ruled(rid, verdict="N/A", na_rule_id=rid))).record
    assert r["verdict"] == "N/A" and r["na"]["rule_id"] == rid


@pytest.mark.parametrize("v", ["PASS", "PARTIAL", "FAIL", "ERRORED"])
def test_measurement_verdicts_on_a_none_criterion_stay_refused_from_the_caller_and_from_the_cell(ledger, v):
    refused(ledger, "detector_none", criterion="Carr.D2", verdict=v)                                    # caller says so
    refused(ledger, "detector_none", criterion="Carr.D2", verdict=None, cell=dict(v=v))                  # the census cell says so
    refused(ledger, "detector_none", criterion="Carr.D2", verdict=v, cell=dict(v=v, cause="not-the-declared-carriage"))
    assert len(lines(ledger)) == 1


@pytest.mark.parametrize("crit", ["Carr.D2", "Carr.D3", "Earn.service_state"])
def test_no_detector_stays_recordable(ledger, crit):
    r = nc.write_certification(**kw(ledger, criterion=crit, verdict="NO_DETECTOR", cell=dict(v="NO_DETECTOR"), semantic_fingerprint=None, writer_files=...))
    assert r.record["verdict"] == "NO_DETECTOR" and r.record["na"] is None


def test_na_without_a_cause_or_rule_is_refused(ledger):
    refused(ledger, "na_not_computed", criterion="Carr.D2", verdict=None, cell=dict(v="N/A"))                              # no cause
    refused(ledger, "na_not_computed", criterion="Carr.D2", verdict="N/A", cell=dict(v="N/A", cause=None))
    refused(ledger, "na_not_computed", criterion="Carr.D2", verdict=None, cell=dict(v="N/A", cause="no-carriage"))        # registered cause, NO rule declared
    refused(ledger, "na_not_computed", criterion="Carr.D2", verdict=None, cell=dict(v="N/A", cause="ratified_judgment"))  # registered, undeclared by ruling
    assert len(lines(ledger)) == 1


def test_na_with_the_rule_id_of_another_criterion_is_refused(ledger):
    other = "Carr.D3#measured:not-the-declared-carriage"
    assert other in ac.NA_RULE_DECISIONS
    refused(ledger, "na_not_computed", **ruled(na_rule_id=other))                                                        # D2 cell, D3's rule id
    refused(ledger, "na_not_computed", **ruled(na_rule_id="Earn.service_state#measured:not-a-service"))
    refused(ledger, "na_not_computed", **ruled(cell=dict(v="N/A", cause="not-a-service")))                               # another criterion's cause
    assert len(lines(ledger)) == 1


def test_na_with_a_rule_not_in_na_rule_decisions_is_refused(ledger, monkeypatch):
    for rid in CERTIFIABLE:
        monkeypatch.delitem(ac.NA_RULE_DECISIONS, rid)
        refused(ledger, "na_not_computed", **ruled(rid))
        monkeypatch.setitem(ac.NA_RULE_DECISIONS, rid, CERTIFIABLE[rid])
    assert len(lines(ledger)) == 1


@pytest.mark.parametrize("decision, code", [("", "na_rules_invalid"), ("   ", "na_rules_invalid"), ("TBD", "detector_none"), ("tbd ", "detector_none"),
                                            ("N-?", "detector_none"), ("none", "detector_none"), ("None", "detector_none"), ("n/a", "detector_none"),
                                            ("TODO", "detector_none"), ("?", "detector_none"), ("-", "detector_none")])
def test_a_blank_or_placeholder_decision_keeps_the_na_refused(ledger, monkeypatch, decision, code):
    rid = "Carr.D2#measured:not-the-declared-carriage"
    monkeypatch.setitem(ac.NA_RULE_DECISIONS, rid, decision)
    refused(ledger, code, **ruled(rid))
    assert len(lines(ledger)) == 1


def test_a_non_string_decision_keeps_the_na_refused(ledger, monkeypatch):
    rid = "Carr.D2#measured:not-the-declared-carriage"
    monkeypatch.setitem(ac.NA_RULE_DECISIONS, rid, None)
    refused(ledger, "na_rules_invalid", **ruled(rid))


def test_a_decision_id_that_is_not_the_declared_one_is_refused(ledger, monkeypatch):
    """The record's `na.decision_id` must EQUAL NA_RULE_DECISIONS[rule_id] (E6.3's `_e63_satisfies` does the same equality at read time)."""
    real = nc._computed_na
    monkeypatch.setattr(nc, "_computed_na", lambda *a, **k: dict(real(*a, **k), decision_id="N-999"))
    e = refused(ledger, "detector_none", **ruled())
    assert "decision id" in str(e)
    monkeypatch.setattr(nc, "_computed_na", lambda *a, **k: dict(real(*a, **k), decision_id=None))
    refused(ledger, "detector_none", **ruled())


def test_a_rule_id_of_another_criterion_in_the_computed_na_is_refused(ledger, monkeypatch):
    real = nc._computed_na
    monkeypatch.setattr(nc, "_computed_na", lambda *a, **k: dict(real(*a, **k), rule_id="Carr.D3#measured:not-the-declared-carriage"))
    e = refused(ledger, "detector_none", **ruled())
    assert "not a rule of Carr.D2" in str(e)


def test_a_computed_na_that_is_not_a_measured_cause_one_is_refused(ledger, monkeypatch):
    real = nc._computed_na
    monkeypatch.setattr(nc, "_computed_na", lambda *a, **k: dict(real(*a, **k), basis="applicability_facts"))
    refused(ledger, "detector_none", **ruled())


def test_an_inconclusive_census_cell_is_refused(ledger):
    refused(ledger, "detector_none", **ruled(cell=dict(v="N/A", cause="not-the-declared-carriage", inconclusive=True)))
    refused(ledger, "detector_none", **ruled(inconclusive=True))
    assert len(lines(ledger)) == 1


def test_an_na_with_no_census_cell_an_applicability_na_stays_refused_on_a_none_criterion(ledger):
    refused(ledger, "detector_none", criterion="Carr.D2", verdict="N/A", cell=...)
    refused(ledger, "detector_none", criterion="Earn.service_state", verdict=None, na_rule_id="Earn.service_state#measured:not-a-service", cell=...)
    assert len(lines(ledger)) == 1


@pytest.mark.parametrize("verdict", ["N/A", "PASS", "FAIL", "PARTIAL"])
def test_an_addition_on_a_none_detector_stays_refused_whatever_its_verdict(ledger, verdict):
    refused(ledger, "detector_none", kind="addition", criterion="D-GROUNDING", detector="NONE", criterion_version=1, verdict=verdict)


def test_an_addition_cannot_borrow_a_ruled_na(ledger):
    e = refused(ledger, "na_not_computed", kind="addition", criterion="D-GROUNDING", detector="grounding_probe.py", criterion_version=1, verdict="N/A",
                na_rule_id="Carr.D2#measured:not-the-declared-carriage")
    assert "addition" in str(e)


def test_a_registry_detector_turning_none_admits_only_a_ruled_na_for_that_criterion(ledger, monkeypatch):
    """Nothing is keyed on the three criteria's NAMES: a criterion that BECOMES detector NONE gets exactly the same rule (and nothing more)."""
    reg = dict(ac.CRITERION_REGISTRY)
    reg["Narr.agree"] = dict(reg["Narr.agree"], detector="NONE")
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", reg)
    monkeypatch.setattr(ac, "registry_fingerprint", lambda: "f" * 64)
    refused(ledger, "detector_none", criterion="Narr.agree", verdict="PASS")
    r = nc.write_certification(**kw(ledger, **ruled(MEAS_NA, head=dict(registry_fingerprint="f" * 64))))
    assert r.record["verdict"] == "N/A" and r.record["detector"] == "NONE"


def test_criteria_with_a_detector_keep_their_na_path_unchanged(ledger, monkeypatch):
    """Golden: the placeholder / decision-equality policy is the NONE case's only. A detector-bearing criterion still records a measured N/A under whatever
    non-blank decision the registry declares (the existing suite pins the rest), and a mismatching computed decision is not this module's business there."""
    monkeypatch.setitem(ac.NA_RULE_DECISIONS, MEAS_NA, "TBD")
    assert ac.CRITERION_REGISTRY["Narr.agree"]["detector"] != "NONE"
    r = nc.write_certification(**kw(ledger, criterion="Narr.agree", verdict=None, cell=dict(v="N/A", cause="no-prose", measured="no prose")))
    assert r.record["verdict"] == "N/A" and r.record["na"]["decision_id"] == "TBD" and r.record["detector"] != "NONE"
    real = nc._computed_na
    monkeypatch.setattr(nc, "_computed_na", lambda *a, **k: dict(real(*a, **k), decision_id="N-999"))
    r2 = nc.write_certification(**kw(ledger, criterion="Narr.checkable", verdict=None, cell=dict(v="N/A", cause="no-prose", measured="no prose"),
                                     asset="bg_panchanga"))
    assert r2.record["na"]["decision_id"] == "N-999"          # unchanged behaviour: only a NONE-detector N/A is held to the declared decision


# ───────────────────────── 2. the enumeration SS asked for ─────────────────────────

def _rules_that_become_certifiable():
    """Computed from asset_census alone: every declared N/A rule of a criterion whose registry detector is NONE and whose cause the inspector can measure."""
    out = {}
    for rid, decision in ac.NA_RULE_DECISIONS.items():
        crit, sep, rule = rid.partition("#")
        entry = ac.CRITERION_REGISTRY.get(crit)
        if sep and entry is not None and entry["detector"] == "NONE" and rule.startswith("measured:") and rule[len("measured:"):] in ac.NA_CAUSES.get(crit, ()):
            out[rid] = decision
    return out


def test_exactly_these_rules_become_certifiable_and_the_set_cannot_change_unnoticed():
    assert _rules_that_become_certifiable() == CERTIFIABLE
    assert ac.REGISTRY_REVISION == 25, "the registry moved: re-derive CERTIFIABLE and the revision pins in this file knowingly"
    none_criteria = sorted(c for c, e in ac.CRITERION_REGISTRY.items() if e["detector"] == "NONE")
    assert none_criteria == ["Carr.D2", "Carr.D3", "Completeness.depth.dasha_link", "Earn.service_state"]
    # Completeness.depth.dasha_link (information family, not a core gate) declares no N/A rule: nothing new is certifiable there
    assert [r for r in CERTIFIABLE if r.startswith("Completeness.")] == []


def test_every_declared_rule_of_a_none_criterion_is_actually_recordable_and_nothing_else_is(ledger):
    for rid in _rules_that_become_certifiable():
        rec = nc.write_certification(**kw(ledger, **ruled(rid, asset="bg_" + re.sub(r"\W", "", rid)[:10].lower()))).record
        assert rec["na"]["rule_id"] == rid
    # every OTHER registered cause of a NONE criterion (declared by no rule) is refused
    for crit in ("Carr.D2", "Carr.D3"):
        for cause in ac.NA_CAUSES[crit]:
            if f"{crit}#measured:{cause}" not in ac.NA_RULE_DECISIONS:
                refused(ledger, "na_not_computed", criterion=crit, verdict=None, cell=dict(v="N/A", cause=cause), asset="bg_panchanga")


# ───────────────────────── 3. nothing else moved ─────────────────────────

def test_registry_and_certificate_schema_are_unchanged():
    """This change is nikasha_certify.py's relaxation + the reader's report counts: no registry revision / fingerprint bump, no new record field, no record
    version, no ledger format or chain change. The literals below are the values at origin/main 8a88fd694."""
    assert ac.REGISTRY_REVISION == 25
    assert ac.registry_fingerprint() == "0e78e228d140d04920cb12bcd8b5bd9c8b33ca59ac8f9105853a139b8289d698"
    assert nc.RECORD_VERSION == 2 and nc.READABLE_RECORD_VERSIONS == (1, 2)
    assert nc.EVENT_TYPES == ("invalidation", "watermark", "epoch_reset") and nc.KINDS == ("gate", "addition")
    assert nc.VERDICTS == ("PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "ERRORED", "N/A")
    assert nc.CURRENCY_FIELDS == ("verdict", "criterion_version", "registry_revision", "registry_fingerprint", "detector", "writer_hashes", "writer_hashes_verified",
                                  "writer_hashes_reason", "upstream_cert_ids", "semantic_fingerprint", "na", "basis", "inconclusive", "transitive_only",
                                  "citation_state", "declarations_sha256")
    assert nc.LEDGER_RELPATH == "00_ARCHITECTURE/control/asset_certs.jsonl" and nc.TRUSTED_CENSUS_ROOT == "00_ARCHITECTURE/control/census/"
    assert hashlib.sha256(nc.SCHEMA_DOC.encode()).hexdigest() == "0d362cb43f43ffd432b29f8fc52ee913e4b2f747a116d58abc3384b2a0779529"


def test_a_ruled_na_record_has_the_same_fields_as_any_other_na_record(ledger):
    """Same schema: the keys of an admitted N/A on a NONE criterion equal the keys of a measured N/A on a detector-bearing one."""
    a = nc.write_certification(**kw(ledger, **ruled())).record
    b = nc.write_certification(**kw(ledger, criterion="Narr.agree", verdict=None, cell=dict(v="N/A", cause="no-prose", measured="x"), asset="bg_panchanga")).record
    assert sorted(a) == sorted(b) and sorted(a["na"]) == sorted(b["na"])
    assert nc.parse_ledger(ledger.read_bytes())                     # E5.1's own chain / schema validator accepts both


# ───────────────────────── 4. end to end on a scratch repo ─────────────────────────

LATTA = "bg_phaladeepika_latta"
SRC_CENSUS = "00_ARCHITECTURE/control/census/asset_census_2026-10-04T193639+0530.json"
CENSUS_DIR = "00_ARCHITECTURE/control/census"
WRITER = "platform/python-sidecar/pipeline/orchestrator/writers/bg_phaladeepika_vedha.py"
BRIEF = "00_ARCHITECTURE/briefs/suvarna/layers/L0/assets/bg_phaladeepika_latta_ELEVATION_BRIEF_v1_0.md"
LEDGER_REL = "00_ARCHITECTURE/control/asset_certs.jsonl"
OLD_DATE = "2026-10-01T00:00:00+05:30"            # before the census `generated`
FILES = ["platform/scripts/governance/asset_census.py", "platform/scripts/governance/nikasha_certify.py", "platform/scripts/governance/carriage_d1.py",
         "platform/scripts/governance/asset_declarations.json", "platform/scripts/seed/asset_registry_seed.ts", WRITER, BRIEF,
         "00_ARCHITECTURE/control/generate_level_map.py", "00_ARCHITECTURE/control/LEVEL_MAP.json", "00_ARCHITECTURE/control/asset_certs.jsonl",
         "00_ARCHITECTURE/control/asset_dispositions.jsonl", "00_ARCHITECTURE/control/asset_gaps.jsonl", "00_ARCHITECTURE/control/asset_elevation_tracker.py"]


def _git(repo, *args, date=None):
    envv = {"GIT_AUTHOR_NAME": "x", "GIT_AUTHOR_EMAIL": "x@x", "GIT_COMMITTER_NAME": "x", "GIT_COMMITTER_EMAIL": "x@x", "PATH": os.environ["PATH"],
            "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "HOME": str(repo)}
    if date:
        envv.update(GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date)
    r = subprocess.run(["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args], capture_output=True, env=envv)
    assert r.returncode == 0, r.stderr.decode()
    return r.stdout.decode().strip()


def _scratch_repo(path):
    """A throw-away git repo of the real engine files (THIS checkout's nikasha_certify.py and reader) plus a synthetic post-rebuild census of latta."""
    path.mkdir(parents=True)
    _git(path, "init", "-q", "-b", "main")
    for rel in FILES:
        (path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / rel, path / rel)
    obj = json.loads((REPO / SRC_CENSUS).read_text(encoding="utf-8"))
    rec = next(a for a in obj["L0"]["assets"] if a["asset_id"] == LATTA)
    rec["measurements"]["Earn.build_record"] = dict(v="PASS", measured="completion write with duration=0.2884s, rows_written=8, rate=27.74 (synthetic)")
    obj["synthetic"] = True                                          # scratch data: never a measurement
    (path / CENSUS_DIR).mkdir(parents=True, exist_ok=True)
    census = path / CENSUS_DIR / "asset_census_synthetic.json"
    census.write_text(json.dumps(obj), encoding="utf-8")
    census.with_name(census.name + ".SYNTHETIC.txt").write_text("SYNTHETIC scratch census\n", encoding="utf-8")
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "scratch base", date=OLD_DATE)
    return path, census, obj["L0"]["generated"]


def test_end_to_end_latta_certifies_its_ruled_na_cells_and_the_report_counts_them_apart(tmp_path, monkeypatch):
    repo, census, generated = _scratch_repo(tmp_path / "repo")
    monkeypatch.setattr(ac, "ROOT", repo)
    monkeypatch.setattr(ac, "SIDECAR", repo / "platform" / "python-sidecar")
    monkeypatch.setattr(ac, "WRITERS", repo / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers")
    sha = _git(repo, "rev-parse", "HEAD")
    ledger = tmp_path / "ledger.jsonl"
    shutil.copyfile(repo / LEDGER_REL, ledger)
    fp = "ab" * 32
    required = [c for g in ac.CELL_GATES for c in sorted(k for k, e in ac.CRITERION_REGISTRY.items() if e["gate"] == g and "L0" in e["layers"])]
    assert len(required) == 25

    # no write_certification special-casing: the same call for every criterion, the verdict read from the census cell
    results = [nc.write_certification(ledger_path=ledger, asset=LATTA, layer="L0", criterion=c, evidence={"census_run_id": generated}, census_path=census,
                                      writer_files=[WRITER], writer_repo=str(repo), writer_ref=sha, semantic_fingerprint=fp, verified_by="e2e")
               for c in required]
    assert [r.status for r in results] == ["appended"] * 25
    by = {r.record["criterion"]: r.record for r in results}
    ruled_cells = sorted(c for c, r in by.items() if r["verdict"] == "N/A")
    assert ruled_cells == sorted(["Build.dep_liveness", "Carr.D2", "Carr.D3", "Dens.served", "Earn.service_state",
                                  "Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Narr.lint"])
    for c in ("Carr.D2", "Carr.D3", "Earn.service_state"):                       # the ones this change admits: N/A with a rule and its decision, never a PASS
        r = by[c]
        assert r["detector"] == "NONE" and r["verdict"] == "N/A" and r["na"]["basis"] == "measured_cause"
        assert r["na"]["decision_id"] == ac.NA_RULE_DECISIONS[r["na"]["rule_id"]] and r["na"]["rule_id"].startswith(c + "#")
    assert all(by[c]["verdict"] == "PASS" and by[c]["na"] is None for c in required if c not in ruled_cells)

    # E5.5 watermark through its own function, observed from the repo at the commit
    decl = (repo / nc.DECLARATIONS_RELPATH).read_bytes()
    obs = {LATTA: {"writer_hashes": nc.hash_writer_files([WRITER], repo, sha), "writer_paths": [WRITER], "semantic_fingerprint": fp},
           "declarations_sha256": hashlib.sha256(decl).hexdigest()}
    assert sc.invalidate(ledger, obs, commit=sha).invalidated == []
    shutil.copyfile(ledger, repo / LEDGER_REL)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "certs", date=OLD_DATE)
    sha = _git(repo, "rev-parse", "HEAD")

    # disposition (keep, with a decision id) and the CLOSED rows for latta's blocking gap rows, as the real fold writes them
    ad.append(str(repo / "00_ARCHITECTURE/control/asset_dispositions.jsonl"), dict(asset=LATTA, disposition="keep", reason="e2e scratch disposition",
              decision_id="N-146", decided_on="2026-10-05T12:00:00+05:30", additions=[], evidence=BRIEF), repo=str(repo), ref=sha, base=None, require_base=False)
    T = ad.load_reader()
    _state, _disp, gaps, _pop = T._e63_load(sha, str(repo))
    gp = repo / "00_ARCHITECTURE/control/asset_gaps.jsonl"
    latest = {}
    for ln in gp.read_text(encoding="utf-8").splitlines()[1:]:
        r = json.loads(ln)
        if r.get("gap_id"):
            latest[r["gap_id"]] = r
    blocking = [g for g in gaps.get(LATTA, []) if g["kind"] == "gap" and g["state"] not in ("CLOSED", "WITHDRAWN") and g["criterion"].split(".")[0] in ac.CELL_GATES]
    with open(gp, "a", encoding="utf-8") as f:
        for g in blocking:
            f.write(json.dumps(dict(latest[g["gap_id"]], state="CLOSED", ts="2026-10-05T12:00:00+05:30")) + "\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "rows", date=OLD_DATE)

    rep = T.elevated_report("HEAD", str(repo))
    assert LATTA in rep, "latta must be ELEVATED: every one of its 25 certificates counts, N/A on the NONE-detector criteria included"
    r = rep[LATTA]
    assert r["basis"] == "measured"
    # 25 certificates read as 16 measured PASS + 9 ruled N/A
    assert (r["measured_pass_certificates"], r["ruled_na_certificates"], r["certificates_total"]) == (16, 9, 25)
    assert sorted(x["criterion"] for x in r["ruled_na_cells"]) == ruled_cells and len(r["ruled_na_cells"]) == r["ruled_na_certificates"]
    by_c = {x["criterion"]: x for x in r["ruled_na_cells"]}
    for c in ("Carr.D2", "Carr.D3", "Earn.service_state"):
        assert by_c[c]["decision_id"] == by[c]["na"]["decision_id"] and by_c[c]["rule_id"] == by[c]["na"]["rule_id"]
    assert r["citation_caveat"] is True and r["declarations_current"] is True and r["declaration_based_pass_cells"] == 0      # nothing else about the report moved
    assert r["measured_pass_certificates"] + r["ruled_na_certificates"] == r["certificates_total"] == len(required)


def test_a_terminal_disposition_counts_zero_certificates():
    T = ad.load_reader()
    state = type("S", (), {})()
    disp = {"x": dict(effective="retire", reason="superseded by y", decision_id="N-1", disposition="retire", additions=())}
    r = T._e63_asset_report("x", state, disp, {})
    assert r["basis"] == "terminal_disposition" and (r["measured_pass_certificates"], r["ruled_na_certificates"], r["certificates_total"]) == (0, 0, 0)
