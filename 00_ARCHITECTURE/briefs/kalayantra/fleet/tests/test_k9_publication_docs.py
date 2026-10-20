"""K9-23: the benchmark contract and the drill register say what the declaration and the code actually do.

Claims (source: the K9-23 plan-model tests; PLAN §6.1-§6.3; D-R9):
  D1  the benchmark contract states versions, hardware, the ephemeris files (hashed), workload dimensions and cache state
  D2  a semantic correction and an optimisation never share one claim: a record carries exactly one claim kind
  D3  each drill names the runner record it must preserve, and the events it names exist in the runner
  D4  restart loss is defined as measured at the kill and is null, with a reason, until a real kill is run
  D5  the rollback byte-for-byte claim names a database oracle that exists
  D6  the documents agree with executor_ops.json: the eight layer/rebuild kinds are enabled, the Gochara authority kinds are
      a different surface, and the backup kinds' capability and script are the declared ones
Each checker is a pure function of text plus the declaration, so a planted stale statement must make it raise.
"""
import hashlib
import json
import re
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]
REPO = FLEET.parents[3]
MEASUREMENTS = REPO / "00_ARCHITECTURE/briefs/l3_families/measurements"
BENCHMARKS = (MEASUREMENTS / "K9_BENCHMARKS_v1_0.md").read_text()
DRILLS = (MEASUREMENTS / "K9_DRILLS_v1_0.md").read_text()
OPS = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
LAYER_KINDS = ["orchestrator_rebuild_dryrun", "orchestrator_rebuild", "layer_verify_dryrun", "layer_verify", "layer_publish_dryrun",
               "layer_publish", "layer_rollback_dryrun", "layer_rollback"]
GOCHARA_KINDS = ["verification_job", "publish_head", "rollback_head"]
BACKUP_KINDS = ["backup_snapshot", "backup_restore_verify"]
ENV_KEYS = ["Hardware", "Operating system", "Python", "pytest", "psycopg", "pyswisseph", "PyYAML", "Ephemeris path"]
DIMENSIONS = ["Claim kind", "Workload", "Cache", "Whole run", "Components", "Storage", "First qualified consumer", "Resume", "Scenarios"]
EPHE = ["sepl_18.se1", "semo_18.se1", "seas_18.se1"]
STALE = re.compile(r"remain(s)? disabled|keeps all five K9 executor entries disabled|still name J-1a placeholders|neither script binding is qualified", re.I)


def table_rows(text):
    return [[c.strip() for c in line.strip().strip("|").split("|")] for line in text.splitlines() if line.startswith("|") and not set(line) <= set("|- ")]


def check_benchmarks(text, ephe_dir=None):
    for key in ENV_KEYS:
        match = re.search(r"^- \*\*" + re.escape(key) + r":\*\* (.+)$", text, re.M)
        assert match and match.group(1).strip() and "null" not in match.group(1).lower(), "environment item not stated: " + key
    rows = {r[0]: r for r in table_rows(text)}
    for name in EPHE:
        assert name in rows and re.fullmatch(r"[0-9a-f]{64}", rows[name][1]), "ephemeris file not hashed: " + name
        if ephe_dir is not None and (ephe_dir / name).is_file():
            assert hashlib.sha256((ephe_dir / name).read_bytes()).hexdigest() == rows[name][1], "stated hash differs from the corpus: " + name
    for dimension in DIMENSIONS:
        assert dimension in rows and len(rows[dimension]) >= 3 and rows[dimension][2], "benchmark dimension missing: " + dimension
    assert re.search(r"exactly\s+one\s+claim\s+kind", text) and "semantic-correction" in text and "optimisation" in text
    assert re.search(r"never\s+(share|combine)", text, re.I)


def check_drills(text, ops, repo):
    assert not STALE.search(text), "stale statement: " + STALE.search(text).group(0)
    drills = [r for r in table_rows(text) if len(r) == 4 and r[0] not in ("Drill",)]
    header = next(r for r in table_rows(text) if r[0] == "Drill")
    assert header[1:] == ["Runner record to retain", "Raw evidence to retain", "Current result"], header
    names = [r[0] for r in drills]
    for needed in ["Baseline full candidate", "Attachment-only upstream change", "Interpretation change", "Convention change", "Kill/resume",
                   "Publish/rollback", "Backup and restore"]:
        assert needed in names, "drill missing: " + needed
    runner = (repo / "platform/python-sidecar/pipeline/orchestrator/asset_runner.py").read_text()
    for row in drills:
        assert row[1], "no runner record named for drill: " + row[0]
        for event in re.findall(r"`(asset\.[a-z_]+)`", row[1]):
            assert event in runner, "runner emits no such event: " + event
        assert row[3].startswith(("null", "local manifest bytes proven")), "unclaimed result must be null or the proven local part: " + row[0]
    for row in drills:
        if row[0] in ("Attachment-only upstream change", "Interpretation change", "Convention change"):
            assert "`asset.skip_no_delta`" in row[1] and "`asset.substep`" in row[1], row[0]
    kill = next(r for r in drills if r[0] == "Kill/resume")
    assert re.search(r"restart loss[^.]*(at the kill|measured at the kill)", text, re.I) and "repeated" in text and "abandoned" in text
    assert kill[3].startswith("null") and "—" in kill[3], "restart loss must be null with a reason until a real kill is run"
    oracle = re.search(r"`(test_rollback_restores_retained_head_and_payload_bytes)`", text)
    assert oracle, "rollback byte-for-byte claim names no oracle"
    assert "def " + oracle.group(1) + "(" in (repo / "platform/python-sidecar/tests/l3/kala_db/manifest/test_publication_ops.py").read_text()
    for kind in LAYER_KINDS:
        assert ops[kind]["enabled"] is True, kind + " is not enabled in the declaration"
        assert "`" + kind + "`" in text, "kind not named: " + kind
    assert re.search(r"all eight .*enabled", text, re.S)
    for kind in GOCHARA_KINDS:
        assert "`" + kind + "`" in text
        assert ops[kind]["script"] not in {ops[k]["script"] for k in LAYER_KINDS}, kind + " shares a script with a layer kind"
        assert ops[kind]["enabled"] is False, kind + " is no longer disabled: the document's separation statement needs review"
    for kind in BACKUP_KINDS:
        entry = ops[kind]
        assert (repo / entry["script"]).is_file()
        line = next((l for l in text.splitlines() if "`" + kind + "`" in l), "")
        assert "capability `" + entry["needs"] + "`" in line and "`" + entry["script"] + "`" in line, "backup line disagrees with the declaration: " + kind
        assert entry["enabled"] is True and "enabled" in line.lower()


def test_benchmark_contract_states_environment_dimensions_and_claim_kind():
    check_benchmarks(BENCHMARKS, Path("/Users/Dev/kalayantra/ephe"))


def test_drill_register_agrees_with_the_declaration_the_runner_and_the_database_oracle():
    check_drills(DRILLS, OPS, REPO)


@pytest.mark.parametrize("plant", [
    lambda t: t.replace("Python:** 3.", "Python:** null (", 1),
    lambda t: re.sub(r"exactly\s+one\s+claim\s+kind", "one or more claim kinds", t),
    lambda t: re.sub(r"\| seas_18\.se1 \| [0-9a-f]{64} \|", "| seas_18.se1 | deadbeef |", t),
])
def test_a_planted_benchmark_defect_is_refused(plant):
    planted = plant(BENCHMARKS)
    assert planted != BENCHMARKS
    with pytest.raises(AssertionError):
        check_benchmarks(planted)


@pytest.mark.parametrize("plant", [
    lambda t: t + "\nAll five K9 entries remain disabled.\n",
    lambda t: t.replace("`asset.skip_no_delta`", "`asset.invented_event`"),
    lambda t: t.replace("`test_rollback_restores_retained_head_and_payload_bytes`", "`test_no_such_oracle`"),
    lambda t: t.replace("capability `owner`", "capability `gcloud`"),
    lambda t: re.sub(r"(Kill/resume \|.*\| )null — [^|]*\|", r"\1measured 0 s |", t),
])
def test_a_planted_drill_defect_is_refused(plant):
    planted = plant(DRILLS)
    assert planted != DRILLS
    with pytest.raises(AssertionError):
        check_drills(planted, OPS, REPO)


def test_the_check_reads_the_declaration_not_the_text():
    ops = json.loads(json.dumps(OPS))
    ops["layer_publish"]["enabled"] = False
    with pytest.raises(AssertionError):
        check_drills(DRILLS, ops, REPO)
