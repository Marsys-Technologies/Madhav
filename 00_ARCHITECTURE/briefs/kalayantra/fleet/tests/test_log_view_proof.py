"""Oracles for log_view_proof.py (step-10 positive log-view proof; surrogate ruling 2026-10-22 09:2xZ; root CLAUDE.md §N.8) — fixtures only: no gcloud, no network, no credential.

Claims (each measured by a detector that can read false; the doctrine is §N.8 earned-signal / §N.7.6 honest null, and the surrogate ruling's two positive checks):
  V1  a view returning only `gochara-verification-job` entries (resource.type=cloud_run_job, job_name=the job) is PROVEN                                         (ruling (a)+(b))
  V2  an empty view is NOT proven: it returns no job entry                                                                                                            (ruling (a))
  V3  ONE non-job entry among job entries makes the view not proven, whatever it is (other job / other resource type / not an object / no resource)               (ruling (b))
  V4  `view_refusal_outside` is NULL — in the rows, in the document, in the CLI output — and never True, even when everything else is proven                       (SR-LOGVIEW-NARROW-KEEP; §N.8)
  V5  an export that is not a JSON array / not readable JSON is HOLD with a named reason, never "proven"                                                              (ruling: unreadable => HOLD)
  V6  `verify` re-measures: forged rows, a forged verdict, another run / attempt, another view or job are refused                                                      (controller re-measure)
  V7  the CLI exits 0 only when PROVEN, 2 (HOLD) otherwise, and writes a document carrying counts only — never a log payload
  V8  the real workflow wires it: the probe read goes through the single-job view with NO resource filter, runs before the brief extraction, and the proof is retained with the brief
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


lvp = _load("log_view_proof_under_test", Path(os.environ.get("LOG_VIEW_PROOF", HERE.parent / "log_view_proof.py")))
RUN, ATT, EXEC = 7001, 1, "gochara-verification-job-7bwpr"


def entry(job="gochara-verification-job", typ="cloud_run_job"):
    return {"insertId": "i", "resource": {"type": typ, "labels": {"job_name": job, "location": "us-central1"}}, "textPayload": "SECRET-PAYLOAD"}


GOOD = [entry(), entry(), entry()]


def row(rows, check):
    return next(r for r in rows if r["check"] == check)


def build(probe, execution=None):
    return lvp.build({"probe": probe, "execution": GOOD if execution is None else execution}, run_id=RUN, attempt=ATT, execution=EXEC)


def test_v1_a_view_of_only_job_entries_is_proven():
    doc = build(GOOD)
    assert doc["passed"] is True
    assert row(doc["rows"], lvp.POSITIVE)["result"] is True and row(doc["rows"], lvp.ONLY_JOB)["result"] is True
    assert doc["sources"]["probe"]["groups"] == [{"type": "cloud_run_job", "job_name": "gochara-verification-job", "count": 3}]


@pytest.mark.parametrize("which", ["probe", "execution"])
def test_v2_an_empty_view_is_not_proven(which):
    doc = lvp.build({"probe": GOOD, "execution": GOOD, which: []}, run_id=RUN, attempt=ATT, execution=EXEC)
    assert doc["passed"] is False
    pos = row(doc["rows"], lvp.POSITIVE)
    assert pos["result"] is False and "empty view proves nothing" in pos["reason"] and which in pos["reason"]


@pytest.mark.parametrize("foreign", [entry(job="some-other-job"), entry(typ="gce_instance"), entry(job="gochara-verification-job-2"), {"resource": {}}, "not an object", None,
                                     {"textPayload": "no resource at all"}])
def test_v3_one_non_job_entry_makes_the_view_not_proven(foreign):
    doc = build(GOOD + [foreign])
    assert doc["passed"] is False
    only = row(doc["rows"], lvp.ONLY_JOB)
    assert only["result"] is False and "1 of 4 returned entries are NOT of cloud_run_job/gochara-verification-job" in only["reason"]
    assert row(doc["rows"], lvp.POSITIVE)["result"] is True                  # the job entries are still there: the two claims are separate detectors


def test_v3b_job_name_of_a_job_with_the_wrong_resource_type_is_not_a_job_entry():
    doc = build([entry(typ="cloud_run_revision")])
    assert doc["passed"] is False and row(doc["rows"], lvp.POSITIVE)["result"] is False


def test_v4_the_outside_refusal_row_is_null_never_green():
    for probe in (GOOD, [], GOOD + [entry(job="x")]):
        rows = build(probe)["rows"]
        out = row(rows, lvp.OUTSIDE)
        assert out["check"] == "view_refusal_outside" and out["result"] is None
        assert "project-wide logging.viewer kept by SR-LOGVIEW-NARROW-KEEP; re-evaluated by LOGVIEW-NARROW-IAC" == out["reason"]
        assert all(r["result"] is not True for r in rows if r["check"] == lvp.OUTSIDE)
    assert lvp.outside_row()["result"] is None and all(r["check"] != lvp.OUTSIDE for r in lvp.rows_of(lvp.groups_of(GOOD)))
    assert lvp.passed([{"check": lvp.POSITIVE, "result": True}, {"check": lvp.ONLY_JOB, "result": True}, {"check": lvp.OUTSIDE, "result": None}]) is True      # null does not block ...
    assert lvp.passed([{"check": lvp.POSITIVE, "result": True}, {"check": lvp.ONLY_JOB, "result": None}]) is False                                               # ... but a null detector never passes


@pytest.mark.parametrize("bad", [{"entries": []}, "text", None, 7])
def test_v5_an_export_that_is_not_an_array_is_unreadable(bad):
    with pytest.raises(lvp.ViewUnreadable):
        lvp.groups_of(bad)


def write(tmp_path, name, obj):
    p = tmp_path / name
    p.write_text(obj if isinstance(obj, str) else json.dumps(obj))
    return str(p)


def cli(tmp_path, probe, execution=None):
    out = tmp_path / "proof.json"
    args = ["check", "--probe-file", write(tmp_path, "probe.json", probe), "--execution-logs-file", write(tmp_path, "exec.json", GOOD if execution is None else execution),
            "--run-id", str(RUN), "--attempt", str(ATT), "--execution", EXEC, "--out", str(out)]
    return lvp.main(args), out


def test_v5b_unreadable_json_is_hold_with_a_named_reason(tmp_path, capsys):
    rc, out = cli(tmp_path, "{not json")
    assert rc == 2 and not out.exists()
    assert "HOLD positive_log_view_proof: unreadable" in capsys.readouterr().err


def test_v6_verify_re_measures_and_refuses_forged_or_foreign_documents():
    doc = build(GOOD)
    ok = lvp.verify(doc, run_id=RUN, attempt=ATT)
    assert ok["passed"] is True and row(ok["rows"], lvp.OUTSIDE)["result"] is None
    def forged(mut):
        d = json.loads(json.dumps(doc))
        mut(d)
        return d
    cases = [(forged(lambda d: d["rows"][-1].__setitem__("result", True)), "recorded rows differ"),
             (forged(lambda d: d["rows"][0].__setitem__("result", False)), "recorded rows differ"),
             (forged(lambda d: d.__setitem__("passed", False)), "recorded verdict differs"),
             (forged(lambda d: d["sources"]["probe"]["groups"].append({"type": "gce_instance", "job_name": None, "count": 1})), "recorded rows differ"),
             (forged(lambda d: d.__setitem__("view", "projects/x/locations/global/buckets/_Default/views/_AllLogs")), "another view"),
             (forged(lambda d: d.__setitem__("job", "other")), "another view or job"),
             (forged(lambda d: d.__setitem__("schema", "x")), "is not a"),
             (forged(lambda d: d["sources"].pop("execution")), "lacks one of its sources"),
             (forged(lambda d: d["sources"]["probe"]["groups"].__setitem__(0, {"type": "cloud_run_job", "job_name": "gochara-verification-job", "count": 0})), "malformed")]
    for d, why in cases:
        with pytest.raises(lvp.ViewUnreadable, match=why):
            lvp.verify(d, run_id=RUN, attempt=ATT)
    with pytest.raises(lvp.ViewUnreadable, match="not the brief run"):
        lvp.verify(doc, run_id=RUN + 1, attempt=ATT)
    with pytest.raises(lvp.ViewUnreadable, match="not the brief run"):
        lvp.verify(doc, run_id=RUN, attempt=ATT + 1)
    with pytest.raises(lvp.ViewUnreadable):
        lvp.verify("not a dict", run_id=RUN, attempt=ATT)


def test_v6b_verify_reports_a_false_proof_with_its_named_reason_instead_of_raising():
    res = lvp.verify(build(GOOD + [entry(job="x")]), run_id=RUN, attempt=ATT)
    assert res["passed"] is False and "view_only_job_entries" in res["reason"] and "job_name='x'" in res["reason"]


def test_v7_the_cli_exits_zero_only_when_proven_and_retains_counts_never_payloads(tmp_path, capsys):
    rc, out = cli(tmp_path, GOOD)
    assert rc == 0
    printed = capsys.readouterr().out
    assert "view_refusal_outside: None" in printed
    assert "SECRET-PAYLOAD" not in out.read_text() and "insertId" not in out.read_text()
    assert lvp.verify(json.loads(out.read_text()), run_id=RUN, attempt=ATT)["passed"] is True
    for bad in ([], GOOD + [entry(job="x")]):
        rc, out = cli(tmp_path, bad)
        assert rc == 2 and json.loads(out.read_text())["passed"] is False
        assert "HOLD positive_log_view_proof" in capsys.readouterr().err


def test_v8_the_real_workflow_reads_the_view_unfiltered_before_the_extraction_and_retains_the_proof():
    text = (REPO / ".github" / "workflows" / "gochara-seal-approved.yml").read_text()
    start = text.index("- name: Retrieve the brief from the execution's logs")
    step = text[start:text.index("      - name:", start + 10)]
    probe = next(ln for ln in step.splitlines() if "view_probe_logs.json" in ln and "gcloud logging read" in ln)
    assert "--view=gochara_verification_job" in probe and "--bucket=_Default --location=global" in probe and "--limit=200" in probe
    assert "resource.type" not in probe and "job_name" not in probe              # no resource filter: a foreign entry could show up in it
    assert step.index("log_view_proof.py check") < step.index("gochara_seal_brief_extract.py")
    call = step[step.index("log_view_proof.py check"):step.index("gochara_seal_brief_extract.py")]
    assert "--probe-file view_probe_logs.json" in call and "--execution-logs-file execution_logs.json" in call and '--run-id "$GITHUB_RUN_ID" --attempt "$GITHUB_RUN_ATTEMPT"' in call
    upload = text[text.index("name: seal-brief-${{ github.run_id }}-${{ github.run_attempt }}"):]
    assert "logview_proof.json" in upload[:upload.index("retention-days")]
    assert re.search(r"^\s*VERIFICATION_JOB: " + re.escape(lvp.JOB) + r"\s*$", text, re.M)       # the detector's job name IS the workflow's
    assert lvp.VIEW.endswith("/views/gochara_verification_job")
