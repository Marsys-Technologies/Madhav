"""Preparation surfaces are bounded, no-effect requests, never earned dry-run attestations."""
import importlib.util
import json
from pathlib import Path

import pytest

FLEET = Path(__file__).resolve().parents[1]


def load():
    path = FLEET / "operation_dryrun.py"
    assert path.exists(), "missing bounded operation preparation surface"
    spec = importlib.util.spec_from_file_location("operation_dryrun", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("kind,args,cap", [
    ("measuring_dispatch", {"run": "all_classes_full", "classes": "all"}, ["builder", "gcloud"]),
    ("century_dispatch", {"classes": "all"}, ["gcloud"]),
    ("verification_job", {"generation": "5.0"}, ["gcloud"]),
    ("publish_head", {"generation": "5.0"}, ["builder"]),
    ("rollback_head", {}, ["builder"]),
])
def test_existing_kind_has_disabled_bounded_preparation(kind, args, cap):
    mod = load()
    result = mod.prepare(kind, args)
    assert result["status"] == "PREPARATION_ONLY" and result["dry_run_passed"] is False
    assert result["executor_capabilities"] == cap and result["blockers"]
    op = json.loads((FLEET / "executor_ops.json").read_text())["ops"][kind]
    assert op["enabled"] is (kind == "measuring_dispatch")      # J-3a enabled the kind; the prepared surface stays disabled review metadata
    surface = op["prepared_dry_run"]
    assert surface["enabled"] is False and surface["script"].endswith("/operation_dryrun.py")
    assert surface["fixed_args"] == ["--dry-run", "--kind", kind]


@pytest.mark.parametrize("kind,args", [
    ("measuring_dispatch", {"run": "one_class_full", "classes": "all"}),
    ("century_dispatch", {"classes": "marriage"}), ("century_dispatch", {"classes": "all", "execute": "true"}),
    ("verification_job", {"generation": "4.1"}), ("publish_head", {"generation": "5.0", "sql": "UPDATE"}),
    ("rollback_head", {"generation": "v1"}), ("not_allocated", {})])
def test_refuses_widened_unlisted_or_wrong_generation_requests(kind, args):
    with pytest.raises(ValueError):
        load().prepare(kind, args)


@pytest.mark.parametrize("proposal", ["protected_apply", "provision", "seal"])
def test_protected_surfaces_are_only_proposals_and_preserve_external_approval(proposal):
    mod = load()
    result = mod.prepare(proposal, {})
    assert result["binding_status"] == "PROPOSAL_REQUIRES_CHILD"
    assert result["external_human_approval_required"] is True
    assert result["dry_run_passed"] is False and result["blockers"]
    assert proposal not in json.loads((FLEET / "executor_ops.json").read_text())["ops"]


def test_cli_requires_explicit_dry_run_and_rejects_extra_flags(capsys):
    mod = load()
    for argv in (["--kind", "century_dispatch", "--classes", "all"],
                 ["--dry-run", "--kind", "century_dispatch", "--classes", "all", "--execute"]):
        with pytest.raises(SystemExit) as exc:
            mod.main(argv)
        assert exc.value.code != 0
    assert mod.main(["--dry-run", "--kind", "century_dispatch", "--classes", "all"]) == 0
    assert json.loads(capsys.readouterr().out)["dry_run_passed"] is False


def test_measuring_preparation_binds_the_real_rollback_path_without_overrides():
    entry = json.loads((FLEET / "executor_ops.json").read_text())["ops"]["measuring_dispatch_dryrun"]
    surface = entry
    assert surface["enabled"] is True and surface["needs"] == "builder"       # J-3a: the real rollback kind is enabled, production:false
    assert surface["production"] is False
    assert surface["script"] == "platform/scripts/dispatch_v5_measuring_job.py"
    assert surface["fixed_args"] == ["--i-am-steward", "--after-settled-1", "--dry-run"]
    assert surface["allowed_args"] == ["run", "classes"]


def test_rollback_never_invents_the_retained_generation():
    result = load().prepare("rollback_head", {})
    assert result["generation"] is None
    with pytest.raises(ValueError):
        load().prepare("rollback_head", {"generation": "5.0"})


def test_j5s_preparation_points_to_disabled_strict_definition_planner():
    result = load().prepare('verification_job', {'generation': '5.0'})
    assert result['prepared_launcher'] == {
        'script': 'platform/scripts/prepare_gochara_verifier_launch.py',
        'enabled': False, 'production_allocation': None,
        'input': 'supplied immutable verifier job definition readbacks',
        'output': 'ky.j5s_verifier_launch_preparation/1',
    }
    # The executor kind and canonical future receipt stay unactivated.
    op = json.loads((FLEET / 'executor_ops.json').read_text())['ops']['verification_job']
    assert op['enabled'] is False and op['script'].startswith('TO_BE_SET_BY_J-4b')
