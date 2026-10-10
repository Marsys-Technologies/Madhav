"""test_assert_no_native_literal_sidecar.py -- the sidecar native-data ratchet (SS N-384, PR-S6).

Proves the guard can fail (synthetic offender), can pass (clean file), enforces the per-file
allowlist as a ratchet, flags stale entries, and that the REAL repo passes with the REAL allowlist.
The forbidden literals are assembled from fragments so this file does not embed them.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

GOV = pathlib.Path(__file__).resolve().parent.parent
REPO = GOV.parent.parent.parent
TOOL = GOV / "assert_no_native_literal_sidecar.py"
SH = GOV / "assert_no_native_literal_sidecar.sh"

_spec = importlib.util.spec_from_file_location("assert_no_native_literal_sidecar_under_test", TOOL)
G = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = G
_spec.loader.exec_module(G)

_NAME = "abhi" + "sek"
_UUID = "482012f1" + "-710e-4a25-994a-93821f5871aa"
_DATE = "1984" + "-02-05"


def _tree(tmp_path: pathlib.Path, files: dict[str, str]) -> pathlib.Path:
    for rel, text in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


def _allow(tmp_path: pathlib.Path, entries: list[dict]) -> pathlib.Path:
    p = tmp_path / "allow.json"
    p.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    return p


def _run(root: pathlib.Path, allow: pathlib.Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOL), "--repo-root", str(root), "--allowlist", str(allow)],
        capture_output=True, text=True,
    )


ROUTE = "platform/python-sidecar/routers/r.py"
OFFENDER = f'def route(chart_id: str = "{_UUID}"):\n    return chart_id\n\nBORN = "{_DATE}"\n'
CLEAN = 'def route(chart_id: str):\n    """Docs may name the chart {u} freely."""\n    return chart_id\n'.format(u=_UUID)


def test_self_test_passes() -> None:
    assert G.self_test() == []
    r = subprocess.run([sys.executable, str(TOOL), "--self-test"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_wrapper_script_runs_the_self_test_and_scan() -> None:
    r = subprocess.run(["bash", str(SH)], capture_output=True, text=True, cwd=str(REPO))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "self-test: PASS" in r.stdout and "PASS (" in r.stdout


def test_the_real_repo_passes_with_the_real_allowlist() -> None:
    problems, _hits = G.run(REPO, G.ALLOWLIST_PATH)
    assert problems == []


def test_every_real_allowlist_entry_has_a_reason_kinds_and_exists() -> None:
    allow = G.load_allowlist(G.ALLOWLIST_PATH)
    assert allow, "an empty allowlist would make the repo-wide pass vacuous only if nothing is left to allow"
    for f, e in allow.items():
        assert (REPO / f).is_file(), f
        assert len(e["reason"]) > 20, f
        assert e["max_hits"] >= 1, f


def test_real_hits_are_not_hidden_by_the_scope_rules() -> None:
    """The scanner finds the known allowlisted hits (guards against an accidentally empty scan)."""
    hits, unparsable = G.scan_repo(REPO)
    assert unparsable == []
    assert sum(len(v) for v in hits.values()) >= 20
    assert any(f.endswith("brahmagyan/mimamsa/lel_intake.py") for f in hits)


def test_offender_without_entry_fails(tmp_path) -> None:
    root = _tree(tmp_path, {ROUTE: OFFENDER})
    r = _run(root, _allow(tmp_path, []))
    assert r.returncode == 1
    assert "r.py" in r.stderr and "not allowlisted" in r.stderr


def test_clean_file_passes(tmp_path) -> None:
    root = _tree(tmp_path, {ROUTE: CLEAN})
    assert _run(root, _allow(tmp_path, [])).returncode == 0


def test_exact_allowlist_entry_passes_and_one_more_hit_fails(tmp_path) -> None:
    root = _tree(tmp_path, {ROUTE: OFFENDER})
    ok = _allow(tmp_path, [{"file": ROUTE, "max_hits": 2, "reason": "synthetic test entry for the ratchet"}])
    assert _run(root, ok).returncode == 0
    (tmp_path / ROUTE).write_text(OFFENDER + f'NAME = "{_NAME}"\n', encoding="utf-8")
    r = _run(root, ok)
    assert r.returncode == 1 and "> allowed 2" in r.stderr


@pytest.mark.parametrize("max_hits,expect", [(5, "STALE allowlist count"), (0, None)])
def test_over_generous_entry_is_stale(tmp_path, max_hits, expect) -> None:
    root = _tree(tmp_path, {ROUTE: OFFENDER})
    r = _run(root, _allow(tmp_path, [{"file": ROUTE, "max_hits": max_hits, "reason": "synthetic test entry"}]))
    assert r.returncode == 1
    if expect:
        assert expect in r.stderr


def test_entry_for_a_clean_or_missing_file_is_stale(tmp_path) -> None:
    root = _tree(tmp_path, {ROUTE: CLEAN})
    r = _run(root, _allow(tmp_path, [{"file": ROUTE, "max_hits": 1, "reason": "synthetic test entry"}]))
    assert r.returncode == 1 and "no native-data hit left" in r.stderr
    r = _run(root, _allow(tmp_path, [{"file": "platform/python-sidecar/routers/gone.py", "max_hits": 1,
                                      "reason": "synthetic test entry"}]))
    assert r.returncode == 1 and "no longer exists" in r.stderr


@pytest.mark.parametrize("rel", [
    "platform/python-sidecar/tests/test_x.py", "platform/python-sidecar/routers/test_y.py",
    "platform/python-sidecar/services/s/tests/z.py", "platform/python-sidecar/brahmagyan/__tests__/z.py",
    "platform/python-sidecar/services/s/fixtures/z.py", "platform/python-sidecar/ga_writers/w.py",
])
def test_tests_fixtures_and_writers_are_out_of_scope(tmp_path, rel) -> None:
    root = _tree(tmp_path, {rel: OFFENDER})
    assert _run(root, _allow(tmp_path, [])).returncode == 0


def test_chart_uuid_as_an_explicit_value_is_not_flagged_but_as_a_default_is() -> None:
    explicit = f'x = call(chart_id="{_UUID}")\nd = {{"chart_id": "{_UUID}"}}\n'
    assert G.scan_source(explicit) == []
    for src in (
        f'def f(c="{_UUID}"): pass\n',
        f'import os\nX = os.environ.get("K", "{_UUID}")\n',
        f'NATIVE_CHART_ID = "{_UUID}"\n',
        f'class M:\n    chart_id: str = "{_UUID}"\n',
        f'from fastapi import Query\ndef f(c: str = Query(default="{_UUID}")): pass\n',
    ):
        assert [h.kind for h in G.scan_source(src)] == ["CHART_DEFAULT"], src


def test_docstrings_and_comments_are_documentation_not_hits() -> None:
    src = f'"""Born {_DATE} to {_NAME}."""\n# {_NAME} {_DATE}\ndef f():\n    """{_NAME}"""\n'
    assert G.scan_source(src) == []
    assert [h.kind for h in G.scan_source(f'X = "{_NAME}"\n')] == ["NAME"]
