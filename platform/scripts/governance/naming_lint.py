#!/usr/bin/env python3
"""naming_lint.py — Canonical naming-taxonomy enforcement (unit 0a.0).

Enforces the currently-enforceable subset of the MARSYS-JIS platform naming
taxonomy. Rule definitions live in `naming_rules.yaml` (sibling file) — adding
later-wave rules (tenant-key, tool-name-in-contract, etc.) requires no code
change.

Modes:
  --self-test       Run against the bundled fixtures under
                    naming_lint_fixtures/{pass,fail}/. Exit 0 iff PASS fixtures
                    produce zero violations AND every FAIL fixture produces at
                    least one violation.
  (default)         Full repo scan. On first run, build the baseline at
                    naming_baseline.json and exit 0. On subsequent runs, fail
                    on NEW violations not in the baseline; pre-existing
                    violations are reported but not failed.
  --strict          Fail on any violation, including baseline. Used in audits.

Exit codes:
  0  — clean (or first-run baseline write, or self-test pass)
  1  — new violations detected (or strict-mode violations, or self-test fail)
  2  — invocation / config error
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

try:
    import yaml  # PyYAML 6+
except ImportError:  # pragma: no cover — guarded by CI; .venv has PyYAML 6.0.3
    print("naming_lint: ERROR — PyYAML 6+ required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent.parent  # platform/scripts/governance -> repo root
RULES_PATH = SCRIPT_DIR / "naming_rules.yaml"
BASELINE_PATH = SCRIPT_DIR / "naming_baseline.json"
FIXTURE_DIR = SCRIPT_DIR / "naming_lint_fixtures"


# ----------------------------------------------------------------------------
# Data model
# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    rule_id: str
    severity: str
    file: str  # repo-relative POSIX path
    line: int  # 1-indexed; 0 for filesystem-only findings
    message: str
    match: str  # the offending token (for stable identity in baseline)

    def key(self) -> str:
        """Stable identity used for baseline diff."""
        return f"{self.rule_id}|{self.file}|{self.match}"


# ----------------------------------------------------------------------------
# Rules loader
# ----------------------------------------------------------------------------


def load_rules(rules_path: Path) -> dict:
    if not rules_path.exists():
        raise SystemExit(f"naming_lint: rules file not found at {rules_path}")
    with rules_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ----------------------------------------------------------------------------
# Glob expansion
# ----------------------------------------------------------------------------


def expand_globs(
    root: Path,
    scan_globs: Sequence[str],
    excludes: Sequence[str],
) -> List[Path]:
    """Resolve scan_globs (relative to repo root) to a deduped file list."""
    out: set[Path] = set()
    for pattern in scan_globs:
        # Pathlib's glob doesn't grok brace expansion ({ts,js}); expand manually.
        for expanded in _expand_braces(pattern):
            for match in root.glob(expanded):
                if match.is_file() and not _excluded(match, root, excludes):
                    out.add(match)
    return sorted(out)


def _expand_braces(pattern: str) -> List[str]:
    """Expand a single level of `{a,b,c}` brace alternation."""
    if "{" not in pattern:
        return [pattern]
    pre, rest = pattern.split("{", 1)
    inner, post = rest.split("}", 1)
    return [pre + opt + post for opt in inner.split(",")]


def _excluded(path: Path, root: Path, excludes: Sequence[str]) -> bool:
    rel = path.relative_to(root).as_posix()
    for ex in excludes:
        if ex.endswith("/"):
            if rel.startswith(ex):
                return True
        else:
            if rel == ex or rel.startswith(ex + "/"):
                return True
    return False


# ----------------------------------------------------------------------------
# Rule implementations
# ----------------------------------------------------------------------------


# Match identifiers like GOOGLE_FOO_BAR or GCP_FOO. Captures the full token.
_GOOGLE_TOKEN_RE = re.compile(r"\b(GOOGLE_[A-Z][A-Z0-9_]*|GCP_[A-Z][A-Z0-9_]*)\b")
# Match identifiers that START with MARSYS_FLAG_ — accept any [A-Za-z0-9_]
# tail so we can flag malformed (lowercase / unusual) variants. Validation
# against the canonical pattern happens after the match.
_MARSYS_FLAG_RE = re.compile(r"\bMARSYS_FLAG_[A-Za-z0-9_]+\b")


def lint_google_env_prefix(
    files: Iterable[Path],
    rule: dict,
    root: Path,
) -> List[Violation]:
    violations: List[Violation] = []
    canonical = rule["canonical"]  # "GOOGLE_CLOUD_"
    allowed = set(rule.get("allowed_exceptions", []))
    forbidden_prefixes = tuple(rule.get("forbidden_prefixes", []))

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        seen_in_file: set[str] = set()
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in _GOOGLE_TOKEN_RE.finditer(line):
                token = m.group(0)
                if token in allowed:
                    continue
                if token in seen_in_file:
                    continue
                # GCP_* always fails
                if any(token.startswith(p) for p in forbidden_prefixes):
                    seen_in_file.add(token)
                    violations.append(Violation(
                        rule_id="google_env_prefix",
                        severity=rule.get("severity", "error"),
                        file=rel,
                        line=lineno,
                        message=(
                            f"forbidden Google env prefix '{token}' — rename to "
                            f"'{canonical}*' (or add to allowed_exceptions if it is an SDK var)"
                        ),
                        match=token,
                    ))
                    continue
                # GOOGLE_* that isn't GOOGLE_CLOUD_* and isn't in allowed set
                if token.startswith("GOOGLE_") and not token.startswith(canonical):
                    seen_in_file.add(token)
                    violations.append(Violation(
                        rule_id="google_env_prefix",
                        severity=rule.get("severity", "error"),
                        file=rel,
                        line=lineno,
                        message=(
                            f"non-canonical Google env var '{token}' — rename to "
                            f"'{canonical}*' (or add to allowed_exceptions if it is an SDK var)"
                        ),
                        match=token,
                    ))
    return violations


def lint_marsys_flags(
    files: Iterable[Path],
    rule: dict,
    root: Path,
) -> List[Violation]:
    violations: List[Violation] = []
    pattern = re.compile(rule["pattern"])
    boolean_suffix = rule.get("boolean_suffix", "_ENABLED")
    suspect = set(rule.get("suspect_identifiers", []))

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        seen_in_file: set[str] = set()
        for lineno, line in enumerate(text.splitlines(), 1):
            # (a) Validate MARSYS_FLAG_* literals match the pattern.
            for m in _MARSYS_FLAG_RE.finditer(line):
                token = m.group(0)
                if token in seen_in_file:
                    continue
                if not pattern.match(token):
                    seen_in_file.add(token)
                    violations.append(Violation(
                        rule_id="marsys_flags",
                        severity=rule.get("severity", "error"),
                        file=rel,
                        line=lineno,
                        message=(
                            f"feature flag '{token}' does not match required pattern "
                            f"MARSYS_FLAG_<DOMAIN>_<FEATURE>"
                        ),
                        match=token,
                    ))
            # (b) Suspect identifiers that LACK the MARSYS_FLAG_ prefix.
            # Match as quoted string literal or bare identifier token boundary.
            for ident in suspect:
                if ident in seen_in_file:
                    continue
                # Require word-boundary so we don't match substrings.
                if re.search(rf"\b{re.escape(ident)}\b", line):
                    seen_in_file.add(ident)
                    msg = (
                        f"feature-flag-shaped identifier '{ident}' lacks the "
                        f"MARSYS_FLAG_ prefix"
                    )
                    if ident.endswith(boolean_suffix):
                        msg += f" (boolean — should be 'MARSYS_FLAG_{ident}')"
                    violations.append(Violation(
                        rule_id="marsys_flags",
                        severity=rule.get("severity", "error"),
                        file=rel,
                        line=lineno,
                        message=msg,
                        match=ident,
                    ))
    return violations


def lint_panchang_route_uniqueness(
    rule: dict,
    root: Path,
) -> List[Violation]:
    canonical = rule["canonical_root"]
    forbidden = rule["forbidden_sibling"]
    canonical_path = root / canonical
    forbidden_path = root / forbidden
    if canonical_path.exists() and forbidden_path.exists():
        # Enumerate forbidden-sibling routes so each new file is a distinct violation.
        results: List[Violation] = []
        # Report the directory itself as a violation, plus any route.ts under it.
        results.append(Violation(
            rule_id="panchang_route_uniqueness",
            severity=rule.get("severity", "error"),
            file=forbidden,
            line=0,
            message=(
                f"duplicate route tree: both '{canonical}/' and '{forbidden}/' exist; "
                f"consolidate under '{canonical}/'"
            ),
            match=forbidden,
        ))
        for sub in sorted(forbidden_path.rglob("*")):
            if sub.is_file():
                rel = sub.relative_to(root).as_posix()
                results.append(Violation(
                    rule_id="panchang_route_uniqueness",
                    severity=rule.get("severity", "error"),
                    file=rel,
                    line=0,
                    message=(
                        f"route file under forbidden sibling tree '{forbidden}/' — "
                        f"move under '{canonical}/'"
                    ),
                    match=rel,
                ))
        return results
    return []


def lint_cloudrun_service_prefix(
    files: Iterable[Path],
    rule: dict,
    root: Path,
) -> List[Violation]:
    violations: List[Violation] = []
    allowlist = set(rule.get("allowlist_legacy", []))
    suspect_patterns = [re.compile(p) for p in rule.get("suspect_patterns", [])]

    for path in files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            continue
        rel = path.relative_to(root).as_posix()
        seen_in_file: set[str] = set()
        for lineno, line in enumerate(text.splitlines(), 1):
            for rgx in suspect_patterns:
                for m in rgx.finditer(line):
                    token = m.group(0)
                    ident = f"{token}@{rel}:{lineno}"
                    if ident in seen_in_file:
                        continue
                    seen_in_file.add(ident)
                    msg = (
                        f"Cloud Run service/image name '{token}' does not match "
                        f"canonical '{rule['canonical']}*' prefix"
                    )
                    if token in allowlist:
                        msg += " (allowlisted legacy — report-mode)"
                    violations.append(Violation(
                        rule_id="cloudrun_service_prefix",
                        severity=rule.get("severity", "error"),
                        file=rel,
                        line=lineno,
                        message=msg,
                        # Use file+line+token so each call site is distinct in
                        # the baseline (legacy names appear in many files).
                        match=ident,
                    ))
    return violations


# ----------------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------------


def run_lint(root: Path, rules: dict, scope_excludes: Sequence[str]) -> List[Violation]:
    all_violations: List[Violation] = []
    rule_defs = rules.get("rules", {})

    if rule_defs.get("google_env_prefix", {}).get("enabled", True):
        r = rule_defs["google_env_prefix"]
        files = expand_globs(root, r["scan_globs"], scope_excludes)
        all_violations.extend(lint_google_env_prefix(files, r, root))

    if rule_defs.get("marsys_flags", {}).get("enabled", True):
        r = rule_defs["marsys_flags"]
        files = expand_globs(root, r["scan_globs"], scope_excludes)
        all_violations.extend(lint_marsys_flags(files, r, root))

    if rule_defs.get("panchang_route_uniqueness", {}).get("enabled", True):
        r = rule_defs["panchang_route_uniqueness"]
        all_violations.extend(lint_panchang_route_uniqueness(r, root))

    if rule_defs.get("cloudrun_service_prefix", {}).get("enabled", True):
        r = rule_defs["cloudrun_service_prefix"]
        files = expand_globs(root, r["scan_globs"], scope_excludes)
        all_violations.extend(lint_cloudrun_service_prefix(files, r, root))

    return all_violations


def load_baseline(path: Path) -> set[str]:
    if not path.exists():
        return set()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("baseline_keys", []))
    except (OSError, json.JSONDecodeError):
        return set()


def write_baseline(path: Path, violations: Sequence[Violation]) -> None:
    payload = {
        "schema_version": "1.0",
        "generated_by": "naming_lint.py --first-run",
        "violation_count": len(violations),
        "baseline_keys": sorted({v.key() for v in violations}),
        "violations": [asdict(v) for v in violations],
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def print_violations(violations: Sequence[Violation], prefix: str = "") -> None:
    for v in violations:
        loc = v.file if v.line == 0 else f"{v.file}:{v.line}"
        print(f"{prefix}[{v.severity}][{v.rule_id}] {loc} — {v.message}")


# ----------------------------------------------------------------------------
# Self-test
# ----------------------------------------------------------------------------


def run_self_test(rules: dict) -> int:
    pass_dir = FIXTURE_DIR / "pass"
    fail_dir = FIXTURE_DIR / "fail"
    if not pass_dir.exists() or not fail_dir.exists():
        print("naming_lint: SELF-TEST — fixture dirs missing", file=sys.stderr)
        return 2

    # Build per-fixture-scope rules that scan ONLY the fixture file (relative
    # to FIXTURE_DIR), so the test is hermetic.
    failures: List[str] = []

    # PASS fixtures: each file individually scanned, must produce zero violations.
    for fixture in sorted(pass_dir.iterdir()):
        if not fixture.is_file():
            continue
        scoped = _scoped_rules_for_fixture(rules, fixture)
        v = run_lint(FIXTURE_DIR, scoped, scope_excludes=[])
        # Drop panchang violations — they're filesystem-state, not file-content.
        v = [x for x in v if x.rule_id != "panchang_route_uniqueness"]
        v = [x for x in v if Path(x.file).name == fixture.name]
        if v:
            failures.append(f"PASS-fixture '{fixture.name}' produced violations:")
            for x in v:
                failures.append(f"  {x.rule_id}: {x.match} — {x.message}")

    # FAIL fixtures: each file must produce >= 1 violation of the *expected* rule.
    # Convention: fail/<rule_id>__<desc>.<ext>
    for fixture in sorted(fail_dir.iterdir()):
        if not fixture.is_file():
            continue
        expected_rule = fixture.stem.split("__", 1)[0]
        scoped = _scoped_rules_for_fixture(rules, fixture)
        v = run_lint(FIXTURE_DIR, scoped, scope_excludes=[])
        v = [x for x in v if x.rule_id != "panchang_route_uniqueness"]
        v = [x for x in v if Path(x.file).name == fixture.name and x.rule_id == expected_rule]
        if not v:
            failures.append(
                f"FAIL-fixture '{fixture.name}' produced no '{expected_rule}' violation"
            )

    # Panchang filesystem fixture: a synthetic state under fixture_dir/panchang_state
    panchang_ok = _self_test_panchang(rules)
    if not panchang_ok:
        failures.append("panchang_route_uniqueness self-test failed")

    if failures:
        print("naming_lint: SELF-TEST FAILED", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    print("naming_lint: SELF-TEST PASS")
    return 0


def _scoped_rules_for_fixture(rules: dict, fixture: Path) -> dict:
    """Clone rules with scan_globs pointing only at this single fixture file."""
    rel = fixture.relative_to(FIXTURE_DIR).as_posix()
    scoped = {"rules": {}}
    for rid, rdef in rules.get("rules", {}).items():
        new = dict(rdef)
        if "scan_globs" in new:
            new["scan_globs"] = [rel]
        scoped["rules"][rid] = new
    return scoped


def _self_test_panchang(rules: dict) -> bool:
    """Build a synthetic two-tree state in a tmp dir + assert violation fires."""
    import tempfile
    rdef = rules["rules"]["panchang_route_uniqueness"]
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / rdef["canonical_root"]).mkdir(parents=True)
        (root / rdef["forbidden_sibling"]).mkdir(parents=True)
        (root / rdef["forbidden_sibling"] / "route.ts").write_text("// stub\n")
        v = lint_panchang_route_uniqueness(rdef, root)
        if not v:
            return False
    # And the inverse — only canonical tree present → no violation.
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / rdef["canonical_root"]).mkdir(parents=True)
        v = lint_panchang_route_uniqueness(rdef, root)
        if v:
            return False
    return True


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Canonical naming-taxonomy linter (unit 0a.0)"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run on bundled fixtures; exit 0 iff all PASS/FAIL expectations met.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on ANY violation, including baseline.",
    )
    parser.add_argument(
        "--rebuild-baseline",
        action="store_true",
        help="Overwrite naming_baseline.json with the current scan output.",
    )
    parser.add_argument(
        "--root",
        default=str(REPO_ROOT),
        help="Repo root to scan (default: inferred from script location).",
    )
    args = parser.parse_args(argv)

    rules = load_rules(RULES_PATH)

    if args.self_test:
        return run_self_test(rules)

    root = Path(args.root).resolve()
    scope_excludes = rules.get("global_excludes", [])
    violations = run_lint(root, rules, scope_excludes)

    # First-run / rebuild path.
    if args.rebuild_baseline or not BASELINE_PATH.exists():
        write_baseline(BASELINE_PATH, violations)
        rel_baseline = BASELINE_PATH.relative_to(root).as_posix() if root in BASELINE_PATH.parents else str(BASELINE_PATH)
        print(
            f"naming_lint: baseline written to {rel_baseline} "
            f"({len(violations)} pre-existing violations recorded)"
        )
        if violations:
            print("naming_lint: baseline contents (informational, not failing):")
            print_violations(violations, prefix="  ")
        return 0

    baseline_keys = load_baseline(BASELINE_PATH)
    new_violations = [v for v in violations if v.key() not in baseline_keys]
    preexisting = [v for v in violations if v.key() in baseline_keys]

    if preexisting:
        print(
            f"naming_lint: {len(preexisting)} pre-existing violation(s) in baseline "
            f"(reported, not failing):"
        )
        print_violations(preexisting, prefix="  ")

    if args.strict:
        if violations:
            print(
                f"naming_lint: STRICT mode — {len(violations)} total violation(s) "
                f"(including baseline). FAIL.",
                file=sys.stderr,
            )
            print_violations(violations, prefix="  ")
            return 1
        print("naming_lint: STRICT mode — 0 violations. PASS.")
        return 0

    if new_violations:
        print(
            f"naming_lint: {len(new_violations)} NEW violation(s) "
            f"not present in baseline. FAIL.",
            file=sys.stderr,
        )
        print_violations(new_violations, prefix="  ")
        return 1

    print(
        f"naming_lint: 0 new violations "
        f"({len(preexisting)} pre-existing in baseline). PASS."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
