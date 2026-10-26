"""SR-W4-LAUNCHER-ARGV: every shard's launch argv must pass gcloud's own `--args` parser, not only the fake runner.

gcloud's `run jobs execute --args` is `ArgList()` with `UpdateAction` (command_lib/run/flags.py ArgsFlag): UpdateAction REFUSES any repeated identical list item
("<item> cannot be specified multiple times"), client-side, before any API call. The launcher's earlier `--class,c1,--class,c2` form was refused that way for every
multi-class shard (W4 2026-10-26, gcloud 576.0.0; the fake runner of test_verification_shards.py never parses the argv).

CLAIMS, each with its fail-on-revert oracle:
  L1 for every shard of the pinned VERIFY_SHARDS.json (dispatch and report-only), the `--args` list has no repeated item — the exact rule UpdateAction enforces
     (revert: build_job_args emits ("--class", c) pairs again => "--class" repeats and this fails)
  L2 the job's own argparse reads that list back as exactly the shard's classes (the `--class=<c>` form is what verification_job.py's action=append accepts)
     (revert: emit "--classes=<c>" or drop the "=" => the parsed classes differ and this fails)
  L3 where the Cloud SDK is importable, gcloud's real ArgList + UpdateAction parse every shard's argv without error (skipped, never green, when the SDK is absent)
"""
import argparse
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import test_executor_verification_launch as base  # noqa: E402  the launcher module as the other fleet tests load it

vl = base.vl
SHARDS = json.loads((base.FLEET / "VERIFY_SHARDS.json").read_text())["shards"]
CASES = [(s["id"], ro) for s in SHARDS for ro in (False, True)]


def _args_items(shard, report_only):
    argv = vl.execute_argv(vl.build_job_args(shard["classes"], report_only=report_only))
    flag = next(a for a in argv if a.startswith("--args="))
    return flag[len("--args="):].split(",")


@pytest.mark.parametrize("sid,report_only", CASES)
def test_l1_no_shard_argv_repeats_an_args_item(sid, report_only):
    shard = next(s for s in SHARDS if s["id"] == sid)
    items = _args_items(shard, report_only)
    repeated = sorted({i for i in items if items.count(i) > 1})
    assert not repeated, f"{sid}: gcloud --args (UpdateAction) refuses repeated items {repeated}"


@pytest.mark.parametrize("sid,report_only", CASES)
def test_l2_the_jobs_argparse_reads_back_exactly_the_shards_classes(sid, report_only):
    shard = next(s for s in SHARDS if s["id"] == sid)
    ap = argparse.ArgumentParser()                      # the job's own declarations (platform/python-sidecar/pipeline/orchestrator/verification_job.py)
    ap.add_argument("--chart", required=True); ap.add_argument("--generation")
    ap.add_argument("--class", dest="classes", action="append", default=None); ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--final-rules", action="store_true"); ap.add_argument("--p1-form-b", action="store_true")
    ns = ap.parse_args(_args_items(shard, report_only))
    assert ns.classes == shard["classes"] and ns.report_only is report_only and ns.chart == vl.CHART
    assert ns.final_rules is True and ns.p1_form_b is False      # the century build ran the final rules (test_verifier_profile_matches_century.py)


def _gcloud_arg_parsers():
    import shutil
    gcloud = shutil.which("gcloud")
    if not gcloud:
        return None
    lib = Path(gcloud).resolve().parents[1] / "lib"
    if not (lib / "googlecloudsdk" / "calliope" / "arg_parsers.py").is_file():
        return None
    sys.path.insert(0, str(lib)); sys.path.insert(0, str(lib / "third_party"))
    try:
        from googlecloudsdk.calliope import arg_parsers
    except Exception:  # noqa: BLE001  an SDK that does not import here is "absent", never a pass
        return None
    return arg_parsers


@pytest.mark.parametrize("sid,report_only", CASES)
def test_l3_gclouds_own_args_parser_accepts_every_shard_argv(sid, report_only):
    arg_parsers = _gcloud_arg_parsers()
    if arg_parsers is None:
        pytest.skip("NOT_RUN: the Cloud SDK is not importable here (L1 is the same rule, always run)")
    shard = next(s for s in SHARDS if s["id"] == sid)
    flag = next(a for a in vl.execute_argv(vl.build_job_args(shard["classes"], report_only=report_only)) if a.startswith("--args="))
    ap = argparse.ArgumentParser()
    ap.add_argument("--args", type=arg_parsers.ArgList(), action=arg_parsers.UpdateAction)      # exactly ArgsFlag's declaration
    ns = ap.parse_args([flag])
    assert ns.args == flag[len("--args="):].split(",")
