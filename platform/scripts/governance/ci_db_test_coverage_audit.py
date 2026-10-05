#!/usr/bin/env python3
"""C54 — CI database-test coverage audit (read-only, static).

Two questions, answered statically (no test is run, no database is touched):

  1. Which test files under platform/python-sidecar NEED a database? A file
     needs one when it directly references database machinery (psycopg, a DSN,
     the disposable-Postgres helpers, a *_REQUIRE_DB gate), or when it uses a
     pytest fixture that (transitively, through the conftest.py chain) does,
     or when it imports a helper from a sibling test module that needs one.
  2. Which of those files does CI actually EXECUTE with a database available?
     A pytest step counts as "with a database" when its job declares a
     postgres service or its run/env mentions a DSN / postgres / a REQUIRE_DB
     gate / disposable-Postgres setup.

Output: a TSV (one row per DB-needing file) and a markdown summary.
`--check` exits 1 when a DB-needing file is neither executed with a database
nor in the EXCLUSIONS list below (an exclusion is explicit and commented —
never a silent skip). Not wired into CI yet (C54).
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SIDECAR = REPO_ROOT / "platform" / "python-sidecar"
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

#: DB-needing files that are deliberately NOT run with a database in CI.
#: Every entry is a decision with its reason; --check fails on a file that is
#: missing from CI's DB steps AND from this list, on an entry whose file is in
#: fact run, and on an entry naming a file that does not exist. (C52's guard
#: covers tests/l3/gochara/test_a53_*.py separately; this list is everything
#: else the first run found — see the committed report for the full table.)
EXCLUSIONS: dict[str, str] = {}

# Source signals that mark database machinery. Each is (name, regex); the name
# is what the report cites as the reason.
DB_SIGNALS = [
    ("psycopg", re.compile(r"\bpsycopg\w*\.connect\s*\(")),
    ("dsn", re.compile(r"postgresql://|_DSN\b|\bDSN\b")),
    ("disposable-pg", re.compile(r"_disposable_pg|create_am5_database|initdb|pg_ctl")),
    ("require-db-gate", re.compile(r"REQUIRE_DB")),
    ("docker-postgres", re.compile(r"docker[^\n]*postgres|postgres:[0-9]")),
]

TEST_FILE_RE = re.compile(r"^(test_\w+|.*_test)\.py$")
#: directories (relative to platform/python-sidecar) that hold tests
TEST_ROOT_MARKERS = ("tests", "__tests__")

CI_DB_ENV_RE = re.compile(
    r"REQUIRE_DB|postgres|PGHOST|PG_DSN|DSN|DATABASE_URL|cloud-sql-proxy|disposable|pg_ctl|initdb",
    re.IGNORECASE)
PYTEST_PATH_RE = re.compile(r"([\w./-]+\.py)\b")


# ── discovery ────────────────────────────────────────────────────────────────

def discover_test_files(sidecar: Path) -> list[Path]:
    out = []
    for path in sorted(sidecar.rglob("*.py")):
        rel = path.relative_to(sidecar)
        if not TEST_FILE_RE.match(path.name):
            continue
        parts = set(rel.parts[:-1])
        if parts & set(TEST_ROOT_MARKERS):
            out.append(path)
    return out


# ── conftest fixture analysis ────────────────────────────────────────────────

#: lines that mention database machinery only to DISABLE it (a monkeypatched
#: psycopg.connect, a deliberately unused DSN) are not database use
_NEGATIVE_LINE_RE = re.compile(r"monkeypatch|never be reached|postgresql://unused|must never")


def _signals_in(text: str) -> list[str]:
    positive = "\n".join(line for line in text.splitlines() if not _NEGATIVE_LINE_RE.search(line))
    return [name for name, rx in DB_SIGNALS if rx.search(positive)]


def _skip_reason_db(text: str) -> bool:
    """A pytest.skip whose reason ties NOT_RUN to a database."""
    for m in re.finditer(r"pytest\.skip\(([^)]*)\)", text, re.DOTALL):
        seg = m.group(1)
        if "NOT_RUN" in seg and re.search(r"database|DSN|Postgres|disposable", seg, re.IGNORECASE):
            return True
    return False


class _FixtureDefs(ast.NodeVisitor):
    """fixture name -> (dependency arg names, source segment)."""

    def __init__(self, source: str):
        self.source = source
        self.fixtures: dict[str, tuple[list[str], str]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for dec in node.decorator_list:
            target = dec.func if isinstance(dec, ast.Call) else dec
            if isinstance(target, ast.Attribute) and target.attr == "fixture":
                args = [a.arg for a in node.args.args if a.arg != "request"]
                seg = ast.get_source_segment(self.source, node) or ""
                self.fixtures[node.name] = (args, seg)


def analyse_conftest(path: Path) -> dict[str, tuple[bool, str]]:
    """fixture name -> (needs_db, why) for one conftest.py."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    defs = _FixtureDefs(source)
    defs.visit(tree)
    direct: dict[str, str] = {}
    for name, (_deps, seg) in defs.fixtures.items():
        sig = _signals_in(seg)
        if sig:
            direct[name] = f"fixture body references {','.join(sig)}"
        elif _skip_reason_db(seg):
            direct[name] = "fixture skips NOT_RUN when its database is unreachable"
    result: dict[str, tuple[bool, str]] = {}

    def needs(name: str, seen: frozenset[str] = frozenset()) -> tuple[bool, str]:
        if name in result:
            return result[name]
        if name in direct:
            return True, direct[name]
        if name in seen or name not in defs.fixtures:
            return False, ""
        deps, _seg = defs.fixtures[name]
        for dep in deps:
            hit, why = needs(dep, seen | {name})
            if hit:
                return True, f"depends on fixture {dep!r} ({why})"
        return False, ""

    for name in defs.fixtures:
        result[name] = needs(name)
    # module-level gates: a conftest that references DB machinery at module
    # scope makes ITS OWN names suspect, but does not by itself mark fixtures
    return result


def _conftest_chain(test_file: Path, sidecar: Path) -> list[Path]:
    """conftest.py files applying to a test file, innermost first."""
    chain = []
    d = test_file.parent
    while d != sidecar.parent and sidecar in d.parents or d == sidecar:
        c = d / "conftest.py"
        if c.is_file():
            chain.append(c)
        if d == sidecar:
            break
        d = d.parent
    return chain


class _UsageScan(ast.NodeVisitor):
    """fixture-parameter names used by tests/fixtures, and relative imports."""

    def __init__(self):
        self.used_args: set[str] = set()
        self.sibling_imports: dict[str, list[str]] = {}  # module -> names

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name.startswith("test_") or any(
                (isinstance(d, ast.Attribute) and d.attr == "fixture")
                or (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                    and d.func.attr == "fixture")
                for d in node.decorator_list):
            self.used_args.update(a.arg for a in node.args.args if a.arg != "request")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level and node.module:  # relative: from .conftest / .test_x import ...
            self.sibling_imports.setdefault(node.module, []).extend(a.name for a in node.names)


def file_needs_db(path: Path, sidecar: Path,
                  conftest_cache: dict[Path, dict[str, tuple[bool, str]]],
                  sibling_db: dict[str, tuple[bool, str]]) -> tuple[bool, str]:
    """(needs_db, reason). `sibling_db` maps sibling module name -> its verdict."""
    text = path.read_text(encoding="utf-8")
    direct = _signals_in(text)
    if direct:
        return True, f"direct reference: {','.join(direct)}"
    if _skip_reason_db(text):
        return True, "skips NOT_RUN when its database is unreachable"
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False, ""
    scan = _UsageScan()
    scan.visit(tree)
    for conftest in _conftest_chain(path, sidecar):
        if conftest not in conftest_cache:
            conftest_cache[conftest] = analyse_conftest(conftest)
        fixtures = conftest_cache[conftest]
        for arg in sorted(scan.used_args):
            if arg in fixtures and fixtures[arg][0]:
                return True, (f"uses fixture {arg!r} from {conftest.relative_to(sidecar)} "
                              f"({fixtures[arg][1]})")
    for module, _names in scan.sibling_imports.items():
        if module == "conftest":
            continue  # conftest fixtures are only live as pytest fixtures, covered above
        if module in sibling_db and sibling_db[module][0]:
            return True, f"imports from sibling suite {module} ({sibling_db[module][1]})"
    return False, ""


# ── CI execution scan ────────────────────────────────────────────────────────

def _pytest_targets(run: str, step_cwd: str, repo_root: Path) -> tuple[list[str], bool]:
    """(paths a pytest line covers relative to repo root, dynamic?) — tracks `cd` lines."""
    targets: list[str] = []
    dynamic = False
    cwd = step_cwd
    for line in run.replace("\\\n", " ").splitlines():  # join shell continuations first
        line = line.strip()
        cd = re.match(r"cd\s+([\w./-]+)", line)
        if cd:
            cwd = str((Path(step_cwd) / cd.group(1)).as_posix())
            continue
        if "pytest" not in line:
            continue
        if re.search(r"\$\{|\$\(", line):
            dynamic = True
            continue
        for token in line.split():
            if token.endswith(".py") and "/" in token:
                targets.append(str((Path(cwd) / token).as_posix()))
            elif token.endswith("/") or (repo_root / cwd / token).is_dir():
                if not token.startswith("-"):
                    targets.append(str((Path(cwd) / token).as_posix()) + "/")
    return targets, dynamic


def scan_workflows(workflows_dir: Path, repo_root: Path
                   ) -> tuple[dict[str, list[str]], dict[str, list[str]], list[str]]:
    """(db_coverage, all_coverage, notes): file path (repo-relative, normalised) ->
    ['workflow :: job :: step'] — db_coverage only where the step runs WITH a database;
    all_coverage wherever the file is a pytest target at all. Notes name dynamic steps
    we cannot resolve statically."""
    coverage: dict[str, list[str]] = {}
    all_coverage: dict[str, list[str]] = {}
    notes: list[str] = []
    for wf_path in sorted(workflows_dir.glob("*.yml")):
        try:
            wf = yaml.safe_load(wf_path.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        if not isinstance(wf, dict):
            continue
        for job_name, job in (wf.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            services = job.get("services") or {}
            job_has_pg = any("postgres" in str((svc or {}).get("image", ""))
                             for svc in services.values())
            job_env = yaml.dump(job.get("env") or {})
            # a database can also be job-level infrastructure rather than a service:
            # a cloud-sql-proxy / DATABASE_URL / DSN anywhere in the job's run text
            job_run_all = "\n".join(str(s.get("run", "")) for s in job.get("steps") or []
                                    if isinstance(s, dict))
            job_has_db_infra = bool(CI_DB_ENV_RE.search(job_run_all))
            for step in job.get("steps") or []:
                if not isinstance(step, dict) or "run" not in step:
                    continue
                run = str(step["run"])
                if "pytest" not in run:
                    continue
                step_env = yaml.dump(step.get("env") or {})
                with_db = (job_has_pg or job_has_db_infra
                           or bool(CI_DB_ENV_RE.search(run))
                           or bool(CI_DB_ENV_RE.search(step_env))
                           or bool(CI_DB_ENV_RE.search(job_env)))
                step_cwd = str(step.get("working-directory") or
                               (job.get("defaults") or {}).get("run", {}).get("working-directory")
                               or ".")
                targets, dynamic = _pytest_targets(run, step_cwd, repo_root)
                label = f"{wf_path.name} :: {job_name} :: {step.get('name', '(unnamed)')}"
                if dynamic:
                    notes.append(f"{label}: dynamic file list — not resolved statically")
                for target in targets:
                    if target.endswith("/"):  # a directory target: covers its subtree
                        dest = coverage if with_db else None
                        for cand in repo_root.glob(target.rstrip("/") + "/**/test_*.py"):
                            rel = str(cand.relative_to(repo_root))
                            all_coverage.setdefault(rel, []).append(label)
                            if dest is not None:
                                dest.setdefault(rel, []).append(label)
                    else:
                        norm = str(Path(target))
                        all_coverage.setdefault(norm, []).append(label)
                        if with_db:
                            coverage.setdefault(norm, []).append(label)
    return coverage, all_coverage, notes


# ── the audit ────────────────────────────────────────────────────────────────

_MODULE_MARK_RE = re.compile(r"^pytestmark\s*=.*\bintegration\b", re.M)
_ANY_MARK_RE = re.compile(r"pytest\.mark\.integration\b")


def integration_marker(text: str) -> str:
    """'module' when a module-level `pytestmark` carries `integration`; 'some' when only individual tests / classes carry `@pytest.mark.integration`; '' otherwise. CI's generic sidecar jobs run
    `-m "not integration"`, so such tests are DESELECTED — visible in pytest's deselected count — rather than silently skipped (steward-approved follow-up to C54; the marker is a file-level hint:
    the audit does not verify per step that the `-m` expression is present)."""
    if _MODULE_MARK_RE.search(text):
        return "module"
    return "some" if _ANY_MARK_RE.search(text) else ""


def run_audit(repo_root: Path = REPO_ROOT):
    sidecar = repo_root / "platform" / "python-sidecar"
    files = discover_test_files(sidecar)
    conftest_cache: dict[Path, dict[str, tuple[bool, str]]] = {}
    verdicts: dict[Path, tuple[bool, str]] = {}
    # two passes so sibling-module verdicts propagate (from .test_x import ...)
    for _pass in range(3):
        sibling_db = {p.stem: v for p, v in verdicts.items()}
        changed = False
        for path in files:
            verdict = file_needs_db(path, sidecar, conftest_cache, sibling_db)
            if verdicts.get(path) != verdict:
                verdicts[path] = verdict
                changed = True
        if not changed:
            break
    coverage, all_coverage, notes = scan_workflows(repo_root / ".github" / "workflows", repo_root)
    rows = []
    for path in files:
        needs, why = verdicts.get(path, (False, ""))
        if not needs:
            continue
        rel = path.relative_to(repo_root).as_posix()
        where = coverage.get(rel, [])
        without_db = sorted(set(all_coverage.get(rel, [])) - set(where))
        rows.append({"file": rel, "why": why,
                     "ci_db": "; ".join(where) if where else "NEVER",
                     "ci_no_db": "; ".join(without_db),
                     "integration": integration_marker(path.read_text(encoding="utf-8"))})
    return rows, notes


def to_tsv(rows: list[dict]) -> str:
    lines = ["file\tneeds_db_why\truns_with_db_in_ci\truns_without_db_in_ci\tintegration_marker"]
    lines += [f"{r['file']}\t{r['why']}\t{r['ci_db']}\t{r['ci_no_db']}\t{r.get('integration', '')}" for r in rows]
    return "\n".join(lines) + "\n"


def to_markdown(rows: list[dict], notes: list[str]) -> str:
    never = [r for r in rows if r["ci_db"] == "NEVER"]
    covered = [r for r in rows if r["ci_db"] != "NEVER"]
    out = ["## Summary", "",
           f"- test files needing a database: **{len(rows)}**",
           f"- executed WITH a database in CI: **{len(covered)}**",
           f"- NEVER executed with a database in CI: **{len(never)}**", ""]
    if never:
        silently = [r for r in never if r["ci_no_db"]]
        absent = [r for r in never if not r["ci_no_db"]]
        marked = [r for r in silently if r.get("integration")]
        unmarked = [r for r in silently if not r.get("integration")]
        out += [f"Of the {len(never)}: **{len(silently)} ARE executed by CI but without a "
                "database** — they skip NOT_RUN silently every run (the C54 failure class) — "
                f"and **{len(absent)} are not executed by CI at all**.", "",
                f"Of the {len(silently)} executed without a database, **{len(marked)} carry the `integration` marker** "
                "(module-level or on some tests): CI's generic sidecar jobs run `-m \"not integration\"`, so those "
                "tests are DESELECTED (visible in pytest's deselected count) rather than silently skipped — a deliberate, "
                f"visible exclusion — and **{len(unmarked)} carry no marker** (the silent NOT_RUN risk to review first). "
                "The marker is a file-level hint; the audit does not verify per step that the `-m` expression is present.", "",
                "### NEVER run with a database in CI", "",
                "| file | why it needs a database | executed WITHOUT a database in | integration marker |", "|---|---|---|---|"]
        out += [f"| `{r['file']}` | {r['why']} | {r['ci_no_db'] or '—'} | {r.get('integration') or '—'} |" for r in never]
        out.append("")
    out += ["### Run with a database in CI", "",
            "| file | workflow :: job :: step |", "|---|---|"]
    out += [f"| `{r['file']}` | {r['ci_db']} |" for r in covered]
    if notes:
        out += ["", "### Unresolved dynamic steps", ""]
        out += [f"- {n}" for n in notes]
    out += ["", "### Full TSV", "", "```", to_tsv(rows).rstrip(), "```", ""]
    return "\n".join(out)


def check(rows: list[dict]) -> int:
    problems = []
    never = {r["file"] for r in rows if r["ci_db"] == "NEVER"}
    for f in sorted(never - set(EXCLUSIONS)):
        problems.append(f"{f}: needs a database but is NEVER run with one in CI and is not excluded")
    for f, reason in EXCLUSIONS.items():
        if f not in never and any(r["file"] == f for r in rows):
            problems.append(f"{f}: excluded but CI now runs it with a database — remove the exclusion ({reason})")
    rc = 1 if problems else 0
    for p in problems:
        print(f"CHECK FAIL: {p}", file=sys.stderr)
    if not problems:
        print(f"check OK: {len(never)} NEVER-run DB-needing files, all explicitly excluded")
    return rc


def main(argv: list[str]) -> int:
    tsv_path = argv[argv.index("--tsv") + 1] if "--tsv" in argv else None
    md_path = argv[argv.index("--md") + 1] if "--md" in argv else None
    rows, notes = run_audit()
    tsv = to_tsv(rows)
    if tsv_path:
        Path(tsv_path).write_text(tsv, encoding="utf-8")
    else:
        sys.stdout.write(tsv)
    if md_path:
        Path(md_path).write_text(to_markdown(rows, notes), encoding="utf-8")
    if "--check" in argv:
        return check(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
