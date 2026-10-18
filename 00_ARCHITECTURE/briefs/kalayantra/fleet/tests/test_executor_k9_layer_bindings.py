"""K9-23 (SR-PREBUILD-ALL): what the executor actually runs for the layer and rebuild kinds, and which connection the child gets.

Claims (the table pin is in test_executor_table.py; admission gates are there too):
  B1  each kind runs `python -m <module> <subcommand> --key value ...` in platform/python-sidecar, in the reviewed tree
  B2  the child receives exactly one connection: the verifier's for layer_verify(+dryrun), the builder's otherwise
  B3  the orchestrator's probe gate is never switched off: NIRMANA_FORCE_EXECUTE in the executor's own environment does not reach any child
  B4  operation_adapters.launch_argv states the same command as the executor
  B5  no source the K9 production kinds run sets its own application_name or edits PGAPPNAME, so every connection carries the executor's quiescence marker
"""
import ast
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

FLEET = Path(__file__).resolve().parents[1]
OPS = json.loads((FLEET / "executor_ops.json").read_text())["ops"]
K9 = ["orchestrator_rebuild_dryrun", "orchestrator_rebuild", "layer_verify_dryrun", "layer_verify", "layer_publish_dryrun", "layer_publish",
      "layer_rollback_dryrun", "layer_rollback"]
ARGS = {"run-id": "6f1d3c1e-0000-4000-8000-000000000001", "generation": "g-1", "expected-head": "g-0", "assets": "ka_yojaka,ka_sangam",
        "phase": "post", "independently-derived-digest": "0" * 64}
URLS = {"KY_BUILDER_DATABASE_URL": "builder-fixture", "KY_LAYER_VERIFIER_DATABASE_URL": "verifier-fixture", "KY_OWNER_DATABASE_URL": "owner-fixture"}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def run_kind(tmp_path, monkeypatch):
    """executor.execute for one kind with git and the child process replaced: returns (argv, cwd, env) of the child."""
    monkeypatch.setenv("KY_ROOT", str(tmp_path))
    for name, value in URLS.items():
        monkeypatch.setenv(name, value)
    executor = load(FLEET / "executor.py", "k923_executor")
    seen = {}
    monkeypatch.setattr(executor, "git", lambda *a, **k: SimpleNamespace(returncode=0, stderr="", stdout=""))
    def run_group(argv, cwd, env, timeout):
        seen.update(argv=argv, cwd=cwd, env=env)
        return SimpleNamespace(returncode=0, stdout="", stderr="")
    monkeypatch.setattr(executor, "run_group", run_group)
    monkeypatch.setattr(executor, "apply_generated_overlay", lambda root, commit, env, timeout=600: ({"schema": "ky.generated_overlay/1", "files": {}}, ""))
    def go(kind):
        args = {name: ARGS[name] for name in OPS[kind]["allowed_args"]}
        request = {"operation_id": "fixture", "kind": kind, "reviewed_commit": "a" * 40, "args": args}
        assert executor.execute(request, OPS[kind])[0] == 0
        return request, seen["argv"], seen["cwd"], seen["env"], executor
    return go


@pytest.mark.parametrize("kind", K9)
def test_child_runs_the_bound_module_with_its_subcommand_and_flags_in_the_reviewed_tree(run_kind, kind):
    request, argv, cwd, _env, executor = run_kind(kind)
    entry = OPS[kind]
    expected_tail = list(entry["fixed_args"]) + [part for name, value in request["args"].items() for part in ("--" + name, value)]
    assert argv == [executor.PY, "-m", entry["python_module"]] + expected_tail
    assert cwd.name == "python-sidecar" and cwd.parent.name == "platform" and cwd.parent.parent.name == "op-fixture"


@pytest.mark.parametrize("kind", K9)
def test_child_gets_only_the_connection_its_capability_names(run_kind, kind):
    _request, _argv, _cwd, env, _executor = run_kind(kind)
    expected = URLS["KY_LAYER_VERIFIER_DATABASE_URL" if OPS[kind]["needs"] == "layer_verifier" else "KY_BUILDER_DATABASE_URL"]
    assert env["DATABASE_URL"] == expected
    assert not set(URLS) & set(env)


@pytest.mark.parametrize("value", ["1", "true", "yes"])
@pytest.mark.parametrize("kind", K9)
def test_a_forcing_variable_in_the_executors_environment_never_reaches_the_child(run_kind, monkeypatch, kind, value):
    monkeypatch.setenv("NIRMANA_FORCE_EXECUTE", value)
    _request, _argv, _cwd, env, _executor = run_kind(kind)
    assert "NIRMANA_FORCE_EXECUTE" not in env


@pytest.mark.parametrize("kind", K9)
def test_launch_argv_states_the_command_the_executor_runs(run_kind, kind):
    request, argv, _cwd, _env, executor = run_kind(kind)
    adapters = load(FLEET / "operation_adapters.py", "k923_adapters")
    assert adapters.launch_argv(OPS[kind], request, py=executor.PY, script_path="/unused") == argv


@pytest.mark.parametrize("package", ["services/kala_core", "pipeline/orchestrator"])
def test_no_source_the_k9_kinds_run_overrides_the_quiescence_marker(package):
    # The marker is PGAPPNAME applied by libpq to every connection that names no application_name (MECHANICAL_ACCEPTANCE_v1_0.md).
    # test_executor_mechanical_acceptance scans only the script's own import closure; the K9 kinds run whole packages.
    root = FLEET.parents[3] / "platform/python-sidecar" / package
    sources = sorted(root.rglob("*.py"))
    assert sources, package
    offenders = []
    for path in sources:
        tree = ast.parse(path.read_text())
        words = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)} | {
            k.arg for n in ast.walk(tree) if isinstance(n, ast.Call) for k in n.keywords if k.arg}
        if any("application_name" in w or "PGAPPNAME" in w for w in words):
            offenders.append(str(path.relative_to(root)))
    assert offenders == []
