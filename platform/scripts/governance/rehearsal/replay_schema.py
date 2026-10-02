#!/usr/bin/env python3
"""replay_schema.py — E5.6 phase 1: replay the repository migrations into the REHEARSAL database.

Why this exists instead of just `npx tsx scripts/migrate.ts`
------------------------------------------------------------
`platform/scripts/migrate.ts` cannot bootstrap an empty database (documented in
.github/workflows/fresh_chart_smoke.yml and 00_ARCHITECTURE/briefs/nirmana/purna_anvesana/
INHERITED_EMPTY_BOOTSTRAP_FINDING_v1.json, PA-R10, PARKED): `0000_seed_legacy_applied.sql` /
`0000b_seed_legacy_v2.sql` mark ~87 foundational migrations as applied WITHOUT running them
(they were applied to production by hand before tracking began), the squashed
`0001_brahma_baseline.sql` carries psql meta-commands and a bare `CREATE SCHEMA public`, and the
pre-tracking generation is not replayable in numeric order. Rewriting that is a separately
chartered baseline-rebuild; this script does NOT edit any migration and does NOT touch the
runner. It is a bounded, honest best-effort replay:

  1. refuse any URL the rehearsal guard does not accept; verify the live server really is the
     rehearsal cluster (port, database, data_directory) before executing anything;
  2. apply `0001_brahma_baseline.sql` through psql (stream-rewriting only `CREATE SCHEMA public;`
     to `CREATE SCHEMA IF NOT EXISTS public;` — the file on disk is never changed), then ensure the
     runner's tracker (`_migrations_applied`, migrate.ts's own DDL; the baseline creates the table);
  3. record the two seed files as applied-NOT-executed (their sole purpose is to fake-mark
     production history; executing them would assert schema that this replay then has to earn);
  5. replay every other migration file in migrate.ts's own order (numeric prefix, lexical
     tie-break, plus its two closed ordering repairs) with psql, one file per attempt, to a FIXED
     POINT: files that fail are retried after the rest have run (dependency-order repair), until
     a full pass makes no progress;
  6. record each success in `_migrations_applied` with the exact sha256 migrate.ts computes;
  7. refuse (REFUSED_UNSAFE, never executed, listed in the report) any file containing a psql
     meta-command, COPY ... PROGRAM, dblink, *_fdw, CREATE SERVER, ALTER SYSTEM or lo_import/export;
  8. write a machine-readable report (applied / failed + last error lines) and exit 3 if ANY file
     failed — a partial replay never reads as a green one (CLAUDE.md §N.8).

`verify` compares every ledger row's sha256 with the file on disk and lists files with no ledger
row. No data is read from or written to anything except the rehearsal database.
"""
from __future__ import annotations

import argparse
import atexit
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rehearsal_guard import REHEARSAL_PORT, normalise_rehearsal_url  # noqa: E402

PG_BIN = os.environ.get("REHEARSAL_PG_BIN", "/opt/homebrew/opt/postgresql@15/bin")
REHEARSAL_HOME = Path("/Users/Dev/suvarna/rehearsal")
EXPECTED_DATA_DIR = str(REHEARSAL_HOME / "pg")
REPORT_PATH = REHEARSAL_HOME / "replay_report.json"
PLATFORM = Path(__file__).resolve().parents[3]  # .../platform
MIGRATION_DIRS = [PLATFORM / "migrations", PLATFORM / "supabase" / "migrations"]
BASELINE = "0001_brahma_baseline.sql"
SEED_FILES = ("0000_seed_legacy_applied.sql", "0000b_seed_legacy_v2.sql")

TRACKER_DDL = """
CREATE TABLE IF NOT EXISTS _migrations_applied (
  id SERIAL PRIMARY KEY,
  filename TEXT UNIQUE NOT NULL,
  applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  sha256 TEXT NOT NULL
);
ALTER TABLE _migrations_applied ADD COLUMN IF NOT EXISTS sql_identity TEXT;
"""

# Closed ordering repairs copied from migrate.ts collectMigrationFiles() (kept in step by hand).
REPLAY_REPAIRS = (
    ("597_nirmana_t0_sky_calendar_replay_compat.sql", "594_nirmana_t0_sky_calendar_contract.sql"),
    ("ws2_l0_texts.sql", "630_nirmana_l0_wave1_correctness_contract.sql"),
)


_EMPTY_HOME: str | None = None


def empty_home() -> str:
    """A private empty HOME (never the real one: no ~/.pgpass, ~/.pg_service.conf, ~/.psqlrc)."""
    global _EMPTY_HOME
    if _EMPTY_HOME is None:
        _EMPTY_HOME = tempfile.mkdtemp(prefix="rehearsal-home-")
        atexit.register(shutil.rmtree, _EMPTY_HOME, ignore_errors=True)
    return _EMPTY_HOME


def pg_env() -> dict[str, str]:
    """Explicit minimal environment: nothing inherited, so no PG*/DATABASE_URL can redirect psql."""
    return {"PATH": f"{PG_BIN}:/usr/bin:/bin", "HOME": empty_home(), "LANG": "en_US.UTF-8",
            "PGPASSFILE": os.path.join(empty_home(), ".no-pgpass"),
            "PGSERVICEFILE": os.path.join(empty_home(), ".no-pg-service"),
            "PGOPTIONS": "-c client_min_messages=warning"}


def psql_args(url: str, *extra: str) -> list[str]:
    u = urlsplit(url)
    return [f"{PG_BIN}/psql", "-h", u.hostname or "", "-p", str(u.port), "-U", u.username or "",
            "-d", u.path.lstrip("/"), "-X", "-q", "-v", "ON_ERROR_STOP=1", *extra]


def run_psql(url: str, *extra: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    # psql never inherits a terminal/pipe stdin: it gets exactly the SQL we pass, or nothing.
    return subprocess.run(psql_args(url, *extra), input=stdin, capture_output=True, text=True,
                          env=pg_env(), **({} if stdin is not None else {"stdin": subprocess.DEVNULL}))


def scalar(url: str, sql: str) -> str:
    r = run_psql(url, "-At", "-c", sql)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def assert_rehearsal_server(url: str) -> None:
    url = normalise_rehearsal_url(url)  # raises on anything the guard refuses
    ident = scalar(url, "SELECT inet_server_port()||'|'||current_database()||'|'||current_setting('data_directory')")
    port, db, ddir = ident.split("|", 2)
    if int(port) != REHEARSAL_PORT or not db.startswith("rehearsal") or ddir != EXPECTED_DATA_DIR:
        raise SystemExit(f"REFUSED: server identity {ident!r} is not the rehearsal cluster")
    print(f"server verified: port={port} db={db} data_directory={ddir}")


def collect_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for d in MIGRATION_DIRS:
        for f in sorted(os.listdir(d)):
            if f.endswith(".sql"):
                files.setdefault(f, d / f)
    return files


def replay_order(files: dict[str, Path]) -> list[str]:
    def key(n: str):
        m = re.match(r"(\d+)", n)
        return (0, int(m.group(1)), n) if m else (1, 0, n)
    order = sorted(files, key=key)
    for pre, tgt in REPLAY_REPAIRS:
        if pre in order and tgt in order and order.index(pre) > order.index(tgt):
            order.remove(pre)
            order.insert(order.index(tgt), pre)
    return order


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf8").encode("utf8")).hexdigest()


def tracked(url: str) -> set[str]:
    out = scalar(url, "SELECT coalesce(string_agg(filename, E'\\n'), '') FROM _migrations_applied")
    return set(out.split("\n")) if out else set()


def record(url: str, name: str, path: Path) -> None:
    # No SQL text is built from the filename: psql variables, interpolated as quoted literals.
    r = run_psql(url, "-v", f"fname={name}", "-v", f"fsha={sha256_of(path)}",
                 stdin="INSERT INTO _migrations_applied (filename, sha256) VALUES (:'fname', :'fsha') "
                       "ON CONFLICT (filename) DO NOTHING;\n")
    if r.returncode != 0:
        raise RuntimeError(f"ledger insert failed for {name}: {r.stderr.strip()}")


# --- pre-scan: constructs a replayed file must never contain ---------------------------------------
UNSAFE_META = re.compile(r"^[ \t]*\\", re.M)  # psql meta-command (\!, \copy, \i, \o | cmd ...) at line start
UNSAFE_SQL = (
    ("COPY ... PROGRAM", re.compile(r"\bCOPY\b[^;]*\bPROGRAM\b", re.I | re.S)),
    ("dblink", re.compile(r"\bdblink", re.I)),
    ("foreign data wrapper (_fdw)", re.compile(r"_fdw\b", re.I)),
    ("CREATE SERVER", re.compile(r"\bCREATE\s+SERVER\b", re.I)),
    ("ALTER SYSTEM", re.compile(r"\bALTER\s+SYSTEM\b", re.I)),
    ("lo_import/lo_export", re.compile(r"\blo_(import|export)\b", re.I)),
)
_COMMENTS = re.compile(r"--[^\n]*|/\*.*?\*/", re.S)


def unsafe_reason(sql: str) -> str | None:
    """Why this file must not be replayed, or None. Meta-commands are scanned on the raw text (a line
    starting with a backslash is refused even inside a comment/dollar quote: fail closed); the SQL
    constructs on the comment-stripped text."""
    if UNSAFE_META.search(sql):
        return "psql meta-command (line starting with a backslash)"
    stripped = _COMMENTS.sub(" ", sql)
    for label, rx in UNSAFE_SQL:
        if rx.search(stripped):
            return label
    return None


REFUSED_UNSAFE = "REFUSED_UNSAFE: "


def apply_file(url: str, name: str, path: Path) -> tuple[bool, str]:
    sql = path.read_text(encoding="utf8")
    why = unsafe_reason(sql)
    if why is not None:
        return False, REFUSED_UNSAFE + why
    if name == BASELINE:
        # Stream rewrite only; the file on disk is untouched.
        sql = sql.replace("\nCREATE SCHEMA public;\n", "\nCREATE SCHEMA IF NOT EXISTS public;\n")
        r = run_psql(url, "-1", stdin=sql)
    elif re.search(r"^\s*BEGIN\s*;", sql, re.M | re.I):
        r = run_psql(url, "-f", str(path))          # file manages its own transaction
    else:
        r = run_psql(url, "-1", "-f", str(path))    # single transaction, like the runner
    if r.returncode == 0:
        return True, ""
    lines = [ln for ln in r.stderr.strip().splitlines() if ln.strip()]
    err = next((ln for ln in lines if "ERROR" in ln or "FATAL" in ln), lines[-1] if lines else f"rc={r.returncode}")
    return False, re.sub(r"^psql:[^ ]*:\d+: ", "", err)[:300]


def cmd_replay(url: str) -> int:
    assert_rehearsal_server(url)
    files = collect_files()
    order = replay_order(files)
    has_tracker = scalar(url, "SELECT to_regclass('public._migrations_applied') IS NOT NULL") == "t"
    done = tracked(url) if has_tracker else set()
    t0 = time.time()
    if BASELINE not in done:
        # The baseline itself creates `_migrations_applied`; the tracker DDL must come AFTER it
        # (pre-creating it makes the baseline's ADD CONSTRAINT ... UNIQUE collide).
        if scalar(url, "SELECT to_regclass('public.charts') IS NOT NULL") == "t":
            raise SystemExit("public.charts exists but the baseline is not in the ledger; run reset --yes first")
        ok, err = apply_file(url, BASELINE, files[BASELINE])
        if not ok:
            raise SystemExit(f"baseline failed: {err}")
        r = run_psql(url, "-c", TRACKER_DDL)
        if r.returncode != 0:
            raise SystemExit(f"tracker DDL failed: {r.stderr}")
        record(url, BASELINE, files[BASELINE])
        print(f"baseline applied ({BASELINE})")
    else:
        r = run_psql(url, "-c", TRACKER_DDL)
        if r.returncode != 0:
            raise SystemExit(f"tracker DDL failed: {r.stderr}")
    for seed in SEED_FILES:
        if seed in files and seed not in done:
            record(url, seed, files[seed])  # applied-NOT-executed (see module docstring)
    done = tracked(url)
    pending = [n for n in order if n not in done]
    applied_now: list[str] = []
    errors: dict[str, str] = {}
    refused: dict[str, str] = {}
    passno = 0
    while pending:
        passno += 1
        still: list[str] = []
        progress = 0
        for n in pending:
            if n in refused:
                still.append(n)
                continue
            ok, err = apply_file(url, n, files[n])
            if not ok and err.startswith(REFUSED_UNSAFE):
                refused[n] = err[len(REFUSED_UNSAFE):]
            if ok:
                record(url, n, files[n])
                applied_now.append(n)
                progress += 1
                errors.pop(n, None)
            else:
                still.append(n)
                errors[n] = err
        print(f"pass {passno}: applied {progress}, still failing {len(still)} ({time.time() - t0:.0f}s)", flush=True)
        pending = still
        if progress == 0 or all(n in refused for n in pending):
            break
    report = {
        "applied_this_run": len(applied_now),
        "ledger_rows": len(tracked(url)),
        "files_on_disk": len(files),
        "failed": errors,
        "refused_unsafe": refused,
        "seeds_recorded_not_executed": [s for s in SEED_FILES if s in files],
    }
    REHEARSAL_HOME.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(f"replay: applied {len(applied_now)} this run; ledger rows {report['ledger_rows']}/{len(files)}; "
          f"FAILED {len(errors)} (report: {REPORT_PATH})")
    return 3 if errors else 0


def cmd_verify(url: str) -> int:
    assert_rehearsal_server(url)
    files = collect_files()
    rows = scalar(url, "SELECT coalesce(string_agg(filename||'|'||sha256, E'\\n'), '') FROM _migrations_applied")
    ledger = dict(ln.split("|", 1) for ln in rows.split("\n") if ln)
    mismatch = [n for n, h in ledger.items() if n in files and sha256_of(files[n]) != h]
    orphan = sorted(n for n in ledger if n not in files)
    untracked = sorted(n for n in files if n not in ledger)
    tables = scalar(url, "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
    print(f"files on disk: {len(files)}  ledger rows: {len(ledger)}  public base tables: {tables}")
    print(f"hash mismatches: {len(mismatch)}  ledger rows with no file: {len(orphan)}  files not in ledger: {len(untracked)}")
    for n in mismatch[:20]:
        print(f"  MISMATCH {n}")
    for n in untracked[:200]:
        print(f"  UNTRACKED {n}")
    return 0 if not (mismatch or orphan or untracked) else 3


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("replay", "verify"))
    ap.add_argument("--url", default="")
    a = ap.parse_args(argv)
    try:
        url = normalise_rehearsal_url(a.url)  # use ONLY the normalised value from here on
    except ValueError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    return cmd_replay(url) if a.command == "replay" else cmd_verify(url)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
