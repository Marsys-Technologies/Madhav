"""
test_q16b_telemetry_call_site_guard.py -- Q-L1-16(b) (LG-L1-001): the eight
`ga_writers._telemetry.update_asset_throughput` call sites are KEPT and DECLARED CLI-ONLY.

Doctrine (CLAUDE.md §N.2, FROZEN orchestrator contract): the orchestrator is the SOLE build-state
(`asset_throughput`) writer; a `ga_*` writer never writes it on the orchestrator path. These eight
legacy CLI entry points do, but only when they OWN their connection (`owns_conn`, i.e. no connection
was injected by the orchestrator), so on the orchestrator path none of them executes.

This guard (AST-based, no import of the writers) fails on:
  1. a NINTH call site: any call to the imported `update_asset_throughput` from `ga_writers/` outside
     the declared (file, enclosing function) allowlist below;
  2. a declared site that is not CLI-guarded: each wrapper's every call must sit under an
     `if owns_conn ...` (or be inside the declared CLI entry function), and the one direct caller
     (ga_tajaka) must itself be under `if owns_conn ...`;
  3. any module outside `ga_writers/` (orchestrator writers, bodha_writers, services, routers) that
     imports `update_asset_throughput` from `ga_writers._telemetry`.

`ga_vargas_writer._update_asset_throughput` is a documented no-op that does not import `_telemetry`
(audit §6.2) and is outside the eight.

Spec: AUDIT_L1_TIERS_PER_EMITTER_v1_0.md v1.1 §6.2.
"""
from __future__ import annotations

import ast
import pathlib
import re

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_GA = _SIDECAR / "ga_writers"

#: (file, enclosing function of the direct call into `_telemetry.update_asset_throughput`)
ALLOWED_DIRECT_CALLS: frozenset[tuple[str, str]] = frozenset({
    ("ga_dashas_writer.py", "_update_asset_throughput"),
    ("ga_panchanga_writer.py", "_update_asset_throughput"),
    ("ga_positions_writer.py", "_update_asset_throughput"),
    ("ga_sade_sati_writer.py", "_update_asset_throughput"),
    ("ga_sensitive_writer.py", "_update_asset_throughput"),
    ("ga_strength_writer.py", "_update_asset_throughput_strength"),
    ("ga_structural_writer.py", "_update_asset_throughput_structural"),
    ("ga_tajaka_writer.py", "build_ga_tajaka"),  # direct call, itself under `if owns_conn`
})

#: Files whose direct call sits in a private wrapper; value = functions in which a wrapper call
#: need NOT be lexically under `if owns_conn` because the function IS the documented CLI entry
#: (ga_dashas `build_ga_dashas`: reached only from the CLI path, behind `if not skip_db`).
CLI_ENTRY_FUNCTIONS: dict[str, frozenset[str]] = {
    "ga_dashas_writer.py": frozenset({"build_ga_dashas"}),
}


def _parse(path: pathlib.Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _parents(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    out: dict[ast.AST, ast.AST] = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            out[c] = n
    return out


def _imported_aliases(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module and n.module.split(".")[-1] == "_telemetry":
            for a in n.names:
                if a.name == "update_asset_throughput":
                    names.add(a.asname or a.name)
    return names


def _call_name(call: ast.Call) -> str | None:
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _enclosing_function(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> str | None:
    cur = node
    while cur in parents:
        cur = parents[cur]
        if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return cur.name
    return None


def _under_owns_conn(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    cur = node
    while cur in parents:
        par = parents[cur]
        if isinstance(par, ast.If) and cur in par.body:
            names = {x.id for x in ast.walk(par.test) if isinstance(x, ast.Name)}
            if "owns_conn" in names:
                return True
        cur = par
    return False


def _direct_calls(path: pathlib.Path) -> list[tuple[str, int, bool]]:
    """(enclosing function, line, under owns_conn) for each call of the imported
    `update_asset_throughput` in `path`."""
    tree = _parse(path)
    aliases = _imported_aliases(tree)
    if not aliases:
        return []
    parents = _parents(tree)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and _call_name(n) in aliases:
            out.append((_enclosing_function(n, parents) or "<module>", n.lineno, _under_owns_conn(n, parents)))
    return out


def _wrapper_calls(path: pathlib.Path, wrapper: str) -> list[tuple[str, int, bool]]:
    tree = _parse(path)
    parents = _parents(tree)
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and _call_name(n) == wrapper:
            out.append((_enclosing_function(n, parents) or "<module>", n.lineno, _under_owns_conn(n, parents)))
    return out


def _all_direct_sites() -> set[tuple[str, str]]:
    sites: set[tuple[str, str]] = set()
    for p in sorted(_GA.glob("*.py")):
        for fn, _line, _g in _direct_calls(p):
            sites.add((p.name, fn))
    return sites


# ── 1. exactly the eight declared direct call sites ───────────────────────────


def test_exactly_the_eight_declared_direct_call_sites_exist():
    assert _all_direct_sites() == set(ALLOWED_DIRECT_CALLS)
    assert len(ALLOWED_DIRECT_CALLS) == 8


# ── 2. every declared site is CLI-guarded ─────────────────────────────────────


def test_every_wrapper_call_is_under_owns_conn_or_the_declared_cli_entry():
    for fname, wrapper in sorted(ALLOWED_DIRECT_CALLS):
        if fname == "ga_tajaka_writer.py":
            continue  # the direct caller; asserted below
        calls = _wrapper_calls(_GA / fname, wrapper)
        assert calls, f"{fname}: wrapper {wrapper} is never called (stale allowlist?)"
        cli_entries = CLI_ENTRY_FUNCTIONS.get(fname, frozenset())
        for fn, line, guarded in calls:
            assert guarded or fn in cli_entries, (
                f"{fname}:{line}: {wrapper}() called from {fn}() without an `if owns_conn` guard "
                "(it would write asset_throughput on the orchestrator path; the orchestrator is the "
                "sole build-state writer)"
            )


def test_ga_tajaka_direct_call_is_under_owns_conn():
    calls = _direct_calls(_GA / "ga_tajaka_writer.py")
    assert len(calls) == 1
    fn, line, guarded = calls[0]
    assert fn == "build_ga_tajaka" and guarded, f"ga_tajaka_writer.py:{line} not under `if owns_conn`"


def test_ga_dashas_cli_entry_is_the_documented_unguarded_caller():
    calls = _wrapper_calls(_GA / "ga_dashas_writer.py", "_update_asset_throughput")
    unguarded = {fn for fn, _l, g in calls if not g}
    assert unguarded <= CLI_ENTRY_FUNCTIONS["ga_dashas_writer.py"]
    assert "build_system" in {fn for fn, _l, g in calls if g}


# ── 3. nothing outside ga_writers/ uses it ────────────────────────────────────


def test_no_module_outside_ga_writers_imports_the_cli_only_helper():
    pat = re.compile(r"_telemetry\s+import[^\n]*update_asset_throughput|_telemetry\.update_asset_throughput")
    offenders = []
    for p in sorted(_SIDECAR.rglob("*.py")):
        rel = p.relative_to(_SIDECAR).as_posix()
        parts = p.parts
        if (rel.startswith("ga_writers/") or "tests" in parts or "__tests__" in parts
                or ".venv" in parts or "site-packages" in parts or "node_modules" in parts):
            continue
        if pat.search(p.read_text(encoding="utf-8", errors="ignore")):
            offenders.append(rel)
    assert offenders == [], offenders


# ── the detector can fail (synthetic sources) ─────────────────────────────────


def _sites_of(src: str) -> list[tuple[str, int, bool]]:
    tree = ast.parse(src)
    aliases = _imported_aliases(tree)
    parents = _parents(tree)
    return [(_enclosing_function(n, parents) or "<module>", n.lineno, _under_owns_conn(n, parents))
            for n in ast.walk(tree) if isinstance(n, ast.Call) and _call_name(n) in aliases]


def test_detector_flags_a_ninth_call_site_and_an_unguarded_call():
    ninth = (
        "from ga_writers._telemetry import update_asset_throughput\n"
        "def helper(conn):\n    update_asset_throughput(conn, 'x', 'c', 'b', 1)\n"
    )
    assert _sites_of(ninth) == [("helper", 3, False)]
    guarded = (
        "from ga_writers._telemetry import update_asset_throughput\n"
        "def build(conn=None):\n    owns_conn = conn is None\n    if owns_conn:\n"
        "        update_asset_throughput(conn, 'x', 'c', 'b', 1)\n"
    )
    assert _sites_of(guarded) == [("build", 5, True)]
    in_else = (
        "from ga_writers._telemetry import update_asset_throughput\n"
        "def build(conn=None):\n    owns_conn = conn is None\n    if owns_conn:\n        pass\n    else:\n"
        "        update_asset_throughput(conn, 'x', 'c', 'b', 1)\n"
    )
    assert _sites_of(in_else) == [("build", 7, False)]  # the else branch is NOT the CLI branch
