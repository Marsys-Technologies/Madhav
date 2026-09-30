#!/usr/bin/env python3
"""Ledger-vs-production reconciliation detector.

The defect this exists for (NATIVE_DECISIONS_2026-09-25 decision 5): a migration's
effects can be live in production while `_migrations_applied` has no row for it.
Seven such migrations were found on 2026-09-25 (1080-1084, 1087, 1091 — applied by
Gochara's cutover, which executes committed migration text and deliberately skips the
ledger). Every instrument that answers "what is deployed?" reads that ledger, so all of
them reported those changes as *pending* while they were live.

CLAUDE.md §N.4 names the mirror hazard — migrations silently doing nothing while the
deploy reports success. This is the same defect reflected: migrations did something while
the ledger reported nothing. One detector closes both, and it is the one this script
implements: **compare the ledger against production structure, never against the deploy's
own report.**

What it claims, per migration file not present in the ledger:

  applied_but_unrecorded          every object the file asserts already exists  -> HIGH
  partially_applied_unrecorded    some exist, some do not (worse: no atomic apply) -> HIGH
  pending                         none exist; genuinely not yet applied        -> clean
  indeterminate                   the file asserts no introspectable object
                                  (data-only migration)                        -> LOW, never clean

Fail-closed by construction: if the database cannot be reached, or psql is absent, the
script exits 4 (UNKNOWN) and reports nothing as clean. An unreachable database is not a
passing result — that is the §N.8 earned-signal rule applied to this check itself.

Exit codes: 0 clean · 2 findings · 4 unknown/unreachable · 5 script error.
Read-only: it issues catalog SELECTs only.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

MIGRATION_DIRS = ("platform/migrations", "platform/supabase/migrations")

# Object assertions we can introspect. Deliberately conservative: a pattern that might
# match something other than a real object name is left out, because a false "applied"
# reading here is worse than an indeterminate one.
RE_CREATE_TABLE = re.compile(
    r"\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
RE_ALTER_ADD_COLUMN = re.compile(
    r"\bALTER\s+TABLE\s+(?:IF\s+EXISTS\s+)?(?:public\.)?([A-Za-z_][A-Za-z0-9_]*)"
    r"(?P<body>(?:[^;]|\n)*?);",
    re.IGNORECASE,
)
RE_ADD_COLUMN = re.compile(
    r"\bADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE
)
RE_CREATE_INDEX = re.compile(
    r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?:CONCURRENTLY\s+)?(?:IF\s+NOT\s+EXISTS\s+)?"
    r"([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)
RE_CREATE_FUNCTION = re.compile(
    r"\bCREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:public\.)?([A-Za-z_][A-Za-z0-9_]*)",
    re.IGNORECASE,
)


def strip_sql_comments(sql: str) -> str:
    """Remove -- line and /* block */ comments so commented-out DDL is never read as an
    assertion. The rollback recipe at the top of a migration is usually a comment block
    naming the very objects the migration creates; reading those would invert the result."""
    out, i, n = [], 0, len(sql)
    while i < n:
        if sql[i] == "-" and i + 1 < n and sql[i + 1] == "-":
            while i < n and sql[i] != "\n":
                i += 1
            out.append("\n")
        elif sql[i] == "/" and i + 1 < n and sql[i + 1] == "*":
            depth, i = 1, i + 2
            while i < n and depth:
                if sql[i] == "/" and i + 1 < n and sql[i + 1] == "*":
                    depth, i = depth + 1, i + 2
                elif sql[i] == "*" and i + 1 < n and sql[i + 1] == "/":
                    depth, i = depth - 1, i + 2
                else:
                    i += 1
            out.append(" ")
        else:
            out.append(sql[i])
            i += 1
    return "".join(out)


def assertions_in(sql: str) -> list[tuple[str, str, str]]:
    """-> [(kind, name, qualifier)] the file asserts should exist afterwards."""
    body = strip_sql_comments(sql)
    found: list[tuple[str, str, str]] = []
    for m in RE_CREATE_TABLE.finditer(body):
        found.append(("table", m.group(1).lower(), ""))
    for m in RE_ALTER_ADD_COLUMN.finditer(body):
        table = m.group(1).lower()
        for col in RE_ADD_COLUMN.finditer(m.group("body")):
            found.append(("column", col.group(1).lower(), table))
    for m in RE_CREATE_INDEX.finditer(body):
        found.append(("index", m.group(1).lower(), ""))
    for m in RE_CREATE_FUNCTION.finditer(body):
        found.append(("function", m.group(1).lower(), ""))
    # de-duplicate, preserve order
    seen, uniq = set(), []
    for a in found:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq


def psql(sql: str) -> str:
    env = dict(os.environ)
    env.setdefault("PGCONNECT_TIMEOUT", "10")
    proc = subprocess.run(
        ["psql", "-tAX", "-v", "ON_ERROR_STOP=1", "-c", sql],
        capture_output=True, text=True, env=env, timeout=60,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip().splitlines()[0] if proc.stderr else "psql failed")
    return proc.stdout.strip()


def exists(kind: str, name: str, qualifier: str) -> bool:
    if kind == "table":
        q = ("SELECT count(*) FROM information_schema.tables "
             f"WHERE table_schema='public' AND table_name='{name}'")
    elif kind == "column":
        q = ("SELECT count(*) FROM information_schema.columns "
             f"WHERE table_schema='public' AND table_name='{qualifier}' AND column_name='{name}'")
    elif kind == "index":
        q = f"SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND indexname='{name}'"
    elif kind == "function":
        q = ("SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
             f"WHERE n.nspname='public' AND p.proname='{name}'")
    else:
        return False
    return psql(q) not in ("", "0")


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    files: dict[str, Path] = {}
    for d in MIGRATION_DIRS:
        for p in sorted((repo / d).glob("*.sql")):
            files[p.name] = p
    if not files:
        print("check_migration_ledger_vs_production: no migration files found", file=sys.stderr)
        return 5

    try:
        recorded = set(psql("SELECT filename FROM _migrations_applied").splitlines())
    except Exception as exc:  # unreachable DB, missing psql, missing ledger
        print(f"check_migration_ledger_vs_production: UNKNOWN — {exc}")
        print("  Nothing is reported clean: an unreachable ledger is not a passing result.")
        return 4

    findings, indeterminate, pending = [], [], []
    for name in sorted(files):
        if name in recorded:
            continue
        asserted = assertions_in(files[name].read_text(encoding="utf-8", errors="replace"))
        if not asserted:
            indeterminate.append(name)
            continue
        present = [a for a in asserted if exists(*a)]
        if len(present) == len(asserted):
            findings.append(("applied_but_unrecorded", name, len(present), len(asserted)))
        elif present:
            findings.append(("partially_applied_unrecorded", name, len(present), len(asserted)))
        else:
            pending.append(name)

    print(f"migration files: {len(files)} · ledger rows: {len(recorded)} · "
          f"unrecorded: {len(files) - len(files.keys() & recorded)}")
    for kind, name, present, total in findings:
        print(f"  HIGH  {kind}: {name} ({present}/{total} asserted objects already in production)")
    for name in indeterminate:
        print(f"  LOW   indeterminate (no introspectable object; data-only?): {name}")
    if pending:
        print(f"  ok    genuinely pending: {len(pending)}")
    if findings:
        print("\nRemediation: record the file as applied WITHOUT executing it (migrate.ts already "
              "has this path for disclosed renumbers), or — when the migration is re-runnable — let "
              "the deploy apply it so the runner writes the ledger row itself with its own hashes.")
        return 2
    if indeterminate:
        return 3
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"check_migration_ledger_vs_production: script error — {exc}", file=sys.stderr)
        sys.exit(5)
