#!/usr/bin/env python3
"""Public-schema CREATE guard for routine migrations (Kāla outage, 2026-10-08).

The defect this exists for: the routine production migrator (amjis_app) has USAGE but NOT CREATE on
schema public. Migration 1330 (CREATE TABLE x4 + GRANT USAGE ON SCHEMA public) merged as an ordinary
routine migration and made EVERY production deploy fail at "Apply Routine DB Migrations"
(permission denied for schema public). Nothing in CI could see it: the CI databases are superuser.

The rule enforced here: a migration file in platform/migrations or platform/supabase/migrations that
is NOT on a protected list must not contain, outside SQL comments,

  * CREATE [OR REPLACE] [UNIQUE] TABLE | INDEX | FUNCTION | PROCEDURE | TYPE | DOMAIN | TRIGGER |
    VIEW | MATERIALIZED VIEW | SEQUENCE   whose target lives in schema public (an unqualified name
    counts as public; TEMP tables do not; INDEX/TRIGGER are judged by their ON <table>), or
  * GRANT ... ON SCHEMA ...

Protected lists (any file on one passes — it applies through a protected window, not the routine runner):
  * platform/scripts/kala_protected_migrations.txt                (Kāla window, kala_schema_migration=true)
  * migrate.ts PROTECTED_PUBLIC_SCHEMA_MIGRATIONS                  (Gochara window)
  * migrate.ts PROTECTED_DATA_PLANE_MIGRATIONS                     (data-plane attestation)
  * migrate.ts AI_METERING_PROTECTED_PUBLIC_SCHEMA_MIGRATION       (AI metering window)
The migrate.ts sets are PARSED from migrate.ts (one source of truth); a parse failure is exit 5, never a pass.

Scope: files numbered > BASELINE_MAX_APPLIED (the highest number applied in production on 2026-10-08, pinned so
historical files cannot fail), PLUS any migration file added/changed in the diff against the merge base with
origin/main (or --base). Fix for a finding: add the filename to kala_protected_migrations.txt in the same PR
(see 00_ARCHITECTURE/briefs/kalayantra/KALA_PROTECTED_WINDOW_v1_0.md), or move the DDL out of schema public.

Known limits (stated so the check cannot overclaim, CLAUDE.md §N.8): text inside string literals and dollar-quoted
bodies IS scanned (EXECUTE 'CREATE TABLE ...' is real DDL), so a literal that merely mentions CREATE TABLE is a
false positive; SET search_path is not modelled (unqualified = public); a file whose number is <= the baseline and
that is not in the diff is not scanned.

Exit codes: 0 clean · 1 findings · 5 script error (unparseable protected list).
  python check_public_schema_migration_privilege.py              scan the repo
  python check_public_schema_migration_privilege.py --self-test  prove the detector by mutation (no git needed)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATION_DIRS = ("platform/migrations", "platform/supabase/migrations")
KALA_LIST = "platform/scripts/kala_protected_migrations.txt"
MIGRATE_TS = "platform/scripts/migrate.ts"

# Highest migration number applied in production as of 2026-10-08 (1330/1334 were never applied; the Kāla
# outage stopped the routine runner at 1330). Pinned, never raised to hide a finding.
BASELINE_MAX_APPLIED = 1333

KINDS = r"TABLE|INDEX|FUNCTION|PROCEDURE|TYPE|DOMAIN|TRIGGER|VIEW|MATERIALIZED\s+VIEW|SEQUENCE"
RE_CREATE = re.compile(
    r"\bCREATE\s+(?:OR\s+REPLACE\s+)?(?P<mods>(?:(?:GLOBAL|LOCAL|TEMP|TEMPORARY|UNLOGGED|UNIQUE|CONSTRAINT|RECURSIVE)\s+)*)"
    r"(?P<kind>" + KINDS + r")\b",
    re.IGNORECASE,
)
IDENT = r'(?:"(?:[^"]|"")+"|[A-Za-z_][A-Za-z0-9_$]*)'
QUALIFIED = re.compile(r"\s*(?P<a>" + IDENT + r")(?:\s*\.\s*(?P<b>" + IDENT + r"))?")
RE_ON_TABLE = re.compile(r"\bON\s+(?:ONLY\s+)?(?P<name>" + IDENT + r"(?:\s*\.\s*" + IDENT + r")?)", re.IGNORECASE)
RE_GRANT_ON_SCHEMA = re.compile(r"\bGRANT\b[^;]*?\bON\s+SCHEMA\b", re.IGNORECASE)
RE_NUMBER = re.compile(r"^(\d+)")


def strip_sql_comments(sql: str) -> str:
    """Remove -- and (nested) /* */ comments; string literals, quoted identifiers and dollar-quoted bodies are kept."""
    out: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        c = sql[i]
        if c == "-" and sql.startswith("--", i):
            while i < n and sql[i] != "\n":
                i += 1
            out.append(" ")
            continue
        if c == "/" and sql.startswith("/*", i):
            depth, i = 1, i + 2
            while i < n and depth:
                if sql.startswith("/*", i):
                    depth, i = depth + 1, i + 2
                elif sql.startswith("*/", i):
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            out.append(" ")
            continue
        if c in ("'", '"'):
            j = i + 1
            while j < n:
                if sql[j] == c:
                    if j + 1 < n and sql[j + 1] == c:
                        j += 2
                        continue
                    break
                j += 1
            out.append(sql[i : j + 1])
            i = j + 1
            continue
        if c == "$":
            m = re.match(r"\$[A-Za-z0-9_]*\$", sql[i:])
            if m:
                tag = m.group(0)
                end = sql.find(tag, i + len(tag))
                end = n if end == -1 else end + len(tag)
                out.append(sql[i:end])
                i = end
                continue
        out.append(c)
        i += 1
    return "".join(out)


def _unquote(ident: str) -> str:
    return ident[1:-1].replace('""', '"') if ident.startswith('"') else ident.lower()


def _schema_of(qualified: str) -> str:
    m = QUALIFIED.match(qualified)
    if not m or not m.group("b"):
        return "public"
    return _unquote(m.group("a"))


def find_violations(sql: str) -> list[str]:
    """Return human-readable descriptions of public-schema CREATEs / schema GRANTs outside comments."""
    body = strip_sql_comments(sql)
    found: list[str] = []
    for m in RE_CREATE.finditer(body):
        mods = m.group("mods").upper().split()
        kind = " ".join(m.group("kind").upper().split())
        if kind == "TABLE" and ("TEMP" in mods or "TEMPORARY" in mods):
            continue
        rest = body[m.end() :]
        stmt = rest.split(";", 1)[0]
        if kind in ("INDEX", "TRIGGER"):
            on = RE_ON_TABLE.search(stmt)
            schema = _schema_of(on.group("name")) if on else "public"
        else:
            target = re.sub(r"^\s*(?:IF\s+NOT\s+EXISTS\s+)", "", stmt, flags=re.IGNORECASE)
            schema = _schema_of(target)
        if schema == "public":
            line = body.count("\n", 0, m.start()) + 1
            found.append(f"line {line}: CREATE {kind} in schema public")
    for m in RE_GRANT_ON_SCHEMA.finditer(body):
        line = body.count("\n", 0, m.start()) + 1
        found.append(f"line {line}: GRANT ... ON SCHEMA")
    return found


def parse_list_file(text: str) -> set[str]:
    names = set()
    for raw in text.splitlines():
        name = raw.split("#", 1)[0].strip()
        if name:
            names.add(name)
    return names


def load_protected(repo_root: Path) -> set[str]:
    """Union of every protected list. Raises ValueError when a migrate.ts set cannot be parsed (fail closed)."""
    ts = (repo_root / MIGRATE_TS).read_text(encoding="utf-8")
    names: set[str] = set()
    for const in ("PROTECTED_PUBLIC_SCHEMA_MIGRATIONS", "PROTECTED_DATA_PLANE_MIGRATIONS"):
        m = re.search(const + r"\s*=\s*new Set\(\[([\s\S]*?)\]\)", ts)
        if not m:
            raise ValueError(f"{const} not found in {MIGRATE_TS}")
        listed = re.findall(r"'([^']+\.sql)'", m.group(1))
        if not listed:
            raise ValueError(f"{const} in {MIGRATE_TS} parsed as empty")
        names.update(listed)
    m = re.search(r"AI_METERING_PROTECTED_PUBLIC_SCHEMA_MIGRATION\s*=\s*'([^']+\.sql)'", ts)
    if not m:
        raise ValueError(f"AI_METERING_PROTECTED_PUBLIC_SCHEMA_MIGRATION not found in {MIGRATE_TS}")
    names.add(m.group(1))
    kala = repo_root / KALA_LIST
    if not kala.is_file():
        raise ValueError(f"{KALA_LIST} is missing")
    names.update(parse_list_file(kala.read_text(encoding="utf-8")))
    return names


def changed_migration_paths(repo_root: Path, base: str) -> set[str] | None:
    """Repo-relative migration paths added/changed against merge-base(base, HEAD); None when git cannot answer."""
    try:
        mb = subprocess.run(["git", "merge-base", base, "HEAD"], cwd=repo_root, capture_output=True, text=True, check=True).stdout.strip()
        out = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", f"{mb}...HEAD", "--", *MIGRATION_DIRS],
            cwd=repo_root, capture_output=True, text=True, check=True,
        ).stdout
    except (subprocess.CalledProcessError, OSError):
        return None
    return {line.strip() for line in out.splitlines() if line.strip().endswith(".sql")}


def scan(repo_root: Path, protected: set[str], changed: set[str], baseline: int = BASELINE_MAX_APPLIED) -> list[str]:
    findings: list[str] = []
    for rel_dir in MIGRATION_DIRS:
        d = repo_root / rel_dir
        if not d.is_dir():
            continue
        for f in sorted(d.glob("*.sql")):
            rel = f"{rel_dir}/{f.name}"
            m = RE_NUMBER.match(f.name)
            in_scope = (m is not None and int(m.group(1)) > baseline) or rel in changed
            if not in_scope or f.name in protected:
                continue
            for v in find_violations(f.read_text(encoding="utf-8")):
                findings.append(f"{rel}: {v}")
    return findings


def self_test() -> int:
    """Mutation proof: a planted CREATE TABLE in a new routine file is caught; the same file on the Kāla list passes;
    a CREATE TABLE inside a comment passes; the pinned baseline and the diff scope behave as stated."""
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        mig = root / "platform/migrations"
        mig.mkdir(parents=True)
        (mig / "9001_new_routine.sql").write_text("CREATE TABLE IF NOT EXISTS kala_x (id int);\n")
        (mig / "9002_commented.sql").write_text("-- CREATE TABLE kala_y (id int);\n/* CREATE TABLE z */ SELECT 1;\n")
        (mig / "0100_historic.sql").write_text("CREATE TABLE old_t (id int);\n")
        if scan(root, set(), set()) != ["platform/migrations/9001_new_routine.sql: line 1: CREATE TABLE in schema public"]:
            failures.append(f"planted CREATE TABLE not caught exactly: {scan(root, set(), set())}")
        if scan(root, {"9001_new_routine.sql"}, set()):
            failures.append("a Kāla-listed file was flagged")
        if not scan(root, set(), {"platform/migrations/0100_historic.sql"}, baseline=9000):
            failures.append("a changed historical file was not scanned")
        if find_violations("GRANT USAGE ON SCHEMA public TO r;") == []:
            failures.append("GRANT ... ON SCHEMA not caught")
        if find_violations("CREATE TEMP TABLE t (id int); CREATE TABLE other_schema.t (id int); "
                           "CREATE INDEX i ON other_schema.t (id); ALTER TABLE t ADD COLUMN c int;"):
            failures.append("non-public / temp / ALTER statements were flagged")
    for f in failures:
        print(f"SELF-TEST FAIL: {f}")
    print("check_public_schema_migration_privilege self-test: " + ("FAIL" if failures else "PASS"))
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    ap.add_argument("--base", default="origin/main", help="git ref whose merge-base with HEAD defines the diff scope")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        protected = load_protected(args.repo_root)
    except (OSError, ValueError) as exc:
        print(f"::error::check_public_schema_migration_privilege: cannot load protected lists: {exc}")
        return 5
    changed = changed_migration_paths(args.repo_root, args.base)
    if changed is None:
        print(f"::notice::git could not diff against {args.base}; scanning files numbered > {BASELINE_MAX_APPLIED} only.")
        changed = set()
    findings = scan(args.repo_root, protected, changed)
    for f in findings:
        print(f"::error::{f} — the routine migrator has no CREATE on schema public. Add the filename to {KALA_LIST} "
              "in this PR (applied via `gh workflow run deploy.yml -f kala_schema_migration=true`) or keep the DDL out of public.")
    print(f"check_public_schema_migration_privilege: {len(findings)} finding(s) "
          f"(baseline > {BASELINE_MAX_APPLIED}, {len(changed)} changed migration file(s) in diff, {len(protected)} protected names)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
