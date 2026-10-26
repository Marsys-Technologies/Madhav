"""GUARD (SR-W4-REGISTRY-DIGEST-DISAGREE case (iii): "builder/verifier mismatch = fix the wrong side"): the verifier runs under the SAME rule profile the century build ran.

Measured cause (2026-10-26): the century candidate bound registry.digest over all 12 sealed (path, version) refs (rule_registry.rule_profile(final_rules=True)); the W4 verification
job, launched without `--final-rules`, derived the five @1.0.0 refs (final_rules=False) and refused `stale_inputs`. The profile is chosen by `verification_job.main` from its flags,
`--final-rules` and `--p1-form-b`; the century's is chosen by its staged config. Nothing tied the two together, so this test does.

CLAIMS (each with ONE fail-on-revert oracle; classical source n/a: this is a build-consistency rule, CLAUDE.md §N.5/§N.8 — the verifier must measure what the build produced):
  G1 the century config (fleet/century_contract.json launch_args.final_rules, the value the dispatch stages as `gochara_v5_final_rules`) is 'true', and the writer's century-config
     fields carry no p1_form_b, so a century run is final-rules with p1_form_b unset
     (revert: the contract's launch_args.final_rules becomes 'false' => this fails and the verifier flags below must be re-derived)
  G2 every argument list the launcher can send the verification job (dispatch and report-only, every shard of VERIFY_SHARDS.json, plus the no-shard form) carries `--final-rules`
     exactly when the century config is final-rules, and never `--p1-form-b`
     (revert: drop "--final-rules" from verification_launch.EXECUTE_ARGS => this fails for every case)
  G3 the seal workflow's brief execution (`--args=` of the gcloud execute step) and its retained-envelope ARGS_JSON carry the same profile flags
     (revert: drop `--final-rules` from either place in gochara-seal-approved.yml => this fails)
  G4 the verifier's own entry point maps the flags to the profile as this test assumes (`--final-rules` => final_rules=True, `--p1-form-b` => p1_form_b=True, both under
     `rule_profile(...)`), so the flags this test compares are the ones the job reads
     (revert: rename or unhook the flag in verification_job.py => this fails)
"""
import ast
import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_executor_verification_launch as base  # noqa: E402  the launcher module as the other fleet tests load it

vl = base.vl
FLEET, REPO = base.FLEET, base.REPO
JOB = REPO / "platform/python-sidecar/pipeline/orchestrator/verification_job.py"
WRITER = REPO / "platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py"
SEAL_WORKFLOW = REPO / ".github/workflows/gochara-seal-approved.yml"
SHARDS = json.loads((FLEET / "VERIFY_SHARDS.json").read_text())["shards"]
FINAL, P1B = "--final-rules", "--p1-form-b"


def century_profile() -> dict:
    """The profile a century run takes: final_rules from the committed century config the dispatch stages; p1_form_b only if the writer's century-config fields could carry it."""
    contract = json.loads((FLEET / "century_contract.json").read_text())
    raw = contract["launch_args"]["final_rules"]
    assert raw in ("true", "false"), f"century_contract launch_args.final_rules {raw!r} is not 'true'/'false'"
    tree = ast.parse(WRITER.read_text())
    fields = next(ast.literal_eval(n.value.args[0]) for n in ast.walk(tree)
                  if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "_CENTURY_CONFIG_FIELDS" for t in n.targets))
    return {"final_rules": raw == "true", "p1_form_b": "p1_form_b" in fields}


def flags_of(items) -> dict:
    items = list(items)
    return {"final_rules": FINAL in items, "p1_form_b": P1B in items}


def test_g1_the_century_config_is_final_rules_with_p1_form_b_unset():
    assert century_profile() == {"final_rules": True, "p1_form_b": False}


CASES = [(s["id"], ro) for s in SHARDS for ro in (False, True)] + [(None, False), (None, True)]


@pytest.mark.parametrize("sid,report_only", CASES)
def test_g2_every_launcher_argument_list_runs_the_century_profile(sid, report_only):
    classes = next((s["classes"] for s in SHARDS if s["id"] == sid), None)
    items = vl.build_job_args(classes, report_only=report_only)
    assert flags_of(items) == century_profile(), f"{sid or 'whole generation'} report_only={report_only}: {list(items)}"
    argv_flag = next(a for a in vl.execute_argv(items) if a.startswith("--args="))      # the argv gcloud receives carries it too
    assert flags_of(argv_flag[len("--args="):].split(",")) == century_profile()


def test_g3_the_seal_workflows_brief_run_and_envelope_args_run_the_century_profile():
    text = SEAL_WORKFLOW.read_text()
    execute = re.search(r'--args="([^"]*--brief[^"]*)"', text)
    assert execute, "the brief execution's --args line was not found"
    assert flags_of(execute.group(1).split(",")) == century_profile(), execute.group(1)
    args_json = re.search(r"ARGS_JSON=\"\$\(python3 -c 'import json,sys; print\(json\.dumps\((\[.*?\])\)\)'", text)
    assert args_json, "the envelope ARGS_JSON line was not found"
    items = [x.strip().strip('"') for x in args_json.group(1).strip("[]").split(",")]
    assert flags_of(items) == century_profile(), items


def test_g4_the_job_reads_those_flags_into_the_rule_profile():
    tree = ast.parse(JOB.read_text())
    declared = {c.args[0].value for c in ast.walk(tree) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute) and c.func.attr == "add_argument"
                and c.args and isinstance(c.args[0], ast.Constant)}
    assert {FINAL, P1B} <= declared
    src = JOB.read_text()
    assert "rule_registry.rule_profile(final_rules=args.final_rules" in src and '{"p1_form_b": True} if args.p1_form_b' in src
