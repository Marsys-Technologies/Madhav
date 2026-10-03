#!/usr/bin/env python3
"""suvarna_mirror_drill.py -- Suvarna E5.7: the mirror wiring of the L0 rebuild drill (the parts that need no production access).

Design: /Users/Dev/suvarna-evidence/E5.7/DESIGN.md. Sibling of `suvarna_rehearsal.py` (E5.6/E5.7 harness, #3084), which it imports for the cluster
lifecycle, the connection policy and the existing E5.7 comparison (`compare_fingerprint_sets`); and of `fingerprint_declarations.py`
(`FINGERPRINT_DECLARATIONS.json`: which tables each of the 40 L0 assets owns and how each is fingerprinted).

  1. MIRROR BASELINE   `build_mirror_baseline`: rebuild the production-faithful SCHEMA from the read-only mirror recipe on a cluster the
                       harness itself started (extensions, roles, the schema-only `pg_dump`, sequences, optional L1 seed fixes), then VERIFY
                       it: every table the declarations name exists with exactly the columns/types and key constraints of the dump.
                       The recipe files are COPIED into a scratch directory first (allow-listed names, symlinks refused, sha256 recorded)
                       and never edited in place; the dump is checked to be schema only (no COPY block, no column-0 INSERT); the derived
                       restore file (the dump minus `CREATE SCHEMA public;`) is a separate scratch file. Result: a closed-schema
                       `MIRROR_BASELINE.json` with a validator that re-derives its verdict. NO production access, NO credential.
  2. FINGERPRINT OUTPUT  one shape for both sides of the drill (`suvarna-l0-fingerprints/v1`): per asset per table {sha256, rows} and the
                       composite asset fingerprint, the declarations sha256, an as-of pin; the rehearsal side computed through a
                       policy-checked connection in a READ ONLY transaction, the production side produced later by the READ-ONLY reader
                       (specified by `reader-spec`, never run here). `validate_fingerprint_output` refuses anything the declarations do not name.
  3. DRILL COMPARE     the production file + the rehearsal file + explanations -> the EXISTING `compare_fingerprint_sets` over
                       `expected_assets` = the comparison UNITS (declared assets with tables of their own + one unit `grp_<id>` per
                       shared-table GROUP, reported with all its members). The drill document itself carries the `coverage` block
                       (declared / partial / undeclared / non-deterministic / groups / expected differences) and the row counts; the
                       verdict says its scope (PASS_DECLARED_ONLY unless every L0 asset is declared, full and deterministic; an empty-on-
                       both-sides unit is never equal). A sibling `.coverage.json` carries the human-readable report.
  4. STATUS            which steps are measured and which are UNMEASURED with a NEEDS_* reason (never PASS).

Usage (also reachable as `suvarna_rehearsal.py drill ...`):
  suvarna_mirror_drill.py expected [--declarations P]
  suvarna_mirror_drill.py reader-spec [--declarations P]
  suvarna_mirror_drill.py baseline --recipe DIR --scratch DIR --root DIR --port N [--policy disposable|rehearsal --owner NAME --data-directory DIR]
                                   [--with-l1-fixes] --out PATH     (starts/uses the harness cluster; the recipe also via $E57_MIRROR_RECIPE)
  suvarna_mirror_drill.py validate-baseline PATH
  suvarna_mirror_drill.py rehearsal-fingerprints --url URL --policy rehearsal|disposable --stage baseline|after_rebuild --as-of YYYY-MM-DD --commit SHA --out PATH
  suvarna_mirror_drill.py compare --production P --rehearsal P --commit SHA [--explained E] --out PATH
  suvarna_mirror_drill.py status [--baseline P] [--production P] [--rehearsal P] [--build-record P]      (prints `build_record_expected`)
  suvarna_mirror_drill.py build-record-spec
Exit: 0 ok · 2 refused / invalid · 4 comparison FAIL · 5 error.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fingerprint_declarations as fd  # noqa: E402
import suvarna_rehearsal as sr  # noqa: E402

TOOL_NAME = "suvarna_mirror_drill.py"
RECIPE_ENV = "E57_MIRROR_RECIPE"                  # the mirror recipe directory: an argument or this variable (no machine-specific default)
RECIPE_FILES = (("schema", "seed/prod_schema.sql"), ("roles", "sql/00_roles.sql"), ("sequences", "sql/20_sequences.sql"),
                ("seed_fixes", "sql/30_seed_fixes.sql"))
ROLES_MIRROR_REL = "../w1_privilege_audit/roles.sql"         # the W1 privilege audit's roles/ACL mirror (same role statements as 00_roles.sql)
MAX_RECIPE_BYTES = 64 * 1024 * 1024
BASELINE_SCHEMA = "suvarna-mirror-baseline/v1"
OUTPUT_SCHEMA = "suvarna-l0-fingerprints/v1"
EXTENSIONS = ("pgcrypto", "uuid-ossp", "vector", "pg_trgm")
SCHEMA_ONLY_LINE = "CREATE SCHEMA public;"
HEX40 = re.compile(r"[0-9a-f]{40}")
SHA256 = re.compile(r"[0-9a-f]{64}")
STEP_ORDER = ("copy_recipe", "schema_only_check", "extensions", "roles", "schema", "sequences", "seed_fixes", "verify")
STEP_STATUSES = ("OK", "TOLERATED_ERRORS", "SKIPPED", "FAILED", "UNMEASURED")
NEEDS = {
    "production": "NEEDS_PRODUCTION_READER_DUMP",
    "baseline": "NEEDS_MIRROR_BASELINE",
    "rebuild": "NEEDS_REHEARSAL_ORCHESTRATOR_L0_RUN",
    "text_seed": "NEEDS_TEXT_SEED",
    "linux": "NEEDS_LINUX_AMD64_RUNTIME",
    "decisions": "NEEDS_SS_DECISIONS",
    "as_of": "NEEDS_AS_OF_PIN",
}
# Aggregate-only ownership probes the production reader ran (read-only, as suvarna_reader, counts only; results committed at
# 00_ARCHITECTURE/control/FINGERPRINT_OWNERSHIP_PROBES_2026-10-03.txt). This module never executes them; they are listed so a re-run is exactly
# these statements, and each carries the outcome it produced.
OWNERSHIP_PROBES = (
    {"asset": "bg_rules", "sql": "SELECT extracted_by, count(*) FROM sutravali_rules GROUP BY 1",
     "outcome": "only extracted_by = 'python_regex_v2' (3002 rows): bg_rules is DECLARED (key rule_id, a deterministic uuid5)"},
    {"asset": "bg_transit_rules", "sql": "SELECT rule_type, graha, count(*) FROM bg_transit_rules GROUP BY 1, 2",
     "outcome": "7 double_transit rows (Jupiter 5, Saturn 2) from migration 397: bg_transit_rules stays UNDECLARED"},
    {"asset": "bg_gochara_citation_resolution", "sql": "SELECT count(*) FROM bg_gochara_citation_resolution",
     "outcome": "14 rows, migration-owned: stays UNDECLARED"},
    {"asset": "bg_sarvatobhadra_grid", "sql": "SELECT count(*) FROM bg_sarvatobhadra_grid",
     "outcome": "0 rows, registered deliberately empty (ADJUDICATION-11): stays UNDECLARED"},
)


LIMITS_TEXT = (
    "Wall-clock exclusions are checked at STATEMENT level: the check accepts a `wall_clock_timestamp` exclusion on an unusual column name when the "
    "cited statement holds now()/CURRENT_TIMESTAMP/datetime.now(), but it cannot tell WHICH column a clock call feeds. A column-level check is post-J1.",
    "SEEDED units (copied from production, not rebuilt) are shown but never counted toward PASS or PASS_DECLARED_ONLY; a drill whose only equal units "
    "are seeded reads UNMEASURED; a seeded unit that differs is reported as a difference but does not by itself fail the rebuilt-equals-source claim.",
    "A bare PASS is reserved for full coverage: every L0 asset declared, full, deterministic and rebuilt. PASS_DECLARED_ONLY says the verdict covers "
    "the declared, non-seeded units only; the undeclared, partial, non-deterministic and seeded names are listed next to it.",
)

BUILD_RECORD_SPEC = {
    "flag": "--build-record PATH  (drill status; a JSON file, strict: no duplicate keys, no NaN/Infinity)",
    "schema": "suvarna-build-record/v1",
    "purpose": "lets `drill status` verify the rehearsal rebuild receipt {run_id, orchestrator_commit} of the rehearsal fingerprint file; without it the "
               "rebuild step reads CLAIMED_UNVERIFIED",
    "required_fields": {
        "schema": "the string suvarna-build-record/v1",
        "run_id": "the orchestrator run id: a canonical lower-case RFC 4122 UUID, equal to the receipt's run_id (not nil, not all-zero)",
        "state": "the string completed (the build_runs state of that run)",
        "orchestrator_commit": "40-hex commit the run's orchestrator code was at, equal to the receipt's orchestrator_commit",
        "assets": "list of {asset_id, state}: one entry per asset of the run (a read-only export of its build_run_assets rows); "
                  "EVERY declared asset (see `drill expected`, `declared`) must appear with state complete",
    },
    "closed": "no other top-level key and no other key in an assets entry",
    "shape_example": {"schema": "suvarna-build-record/v1", "run_id": "<uuid>", "state": "completed", "orchestrator_commit": "<40-hex>",
                      "assets": [{"asset_id": "bg_ephemeris", "state": "complete"}]},
}


class MirrorError(sr.RehearsalError):
    """A refusal of this module (recipe, derived files, malformed documents). Nothing was written."""


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def tool_sha256() -> str:
    return sr.sha256_file(Path(__file__).resolve())


# ═════════════════════════ 1a. the recipe: copy, never edit; schema only ═════════════════════════

def copy_recipe(recipe_dir: str | Path, scratch_dir: str | Path) -> dict:
    """Copy the allow-listed recipe files (and the W1 roles mirror, when present) into `scratch_dir`, which must be a new or empty
    directory OUTSIDE the recipe. Refuses a missing file, a symlink (anywhere on the file's path below the recipe), a non-regular
    file, an oversize file, or a copy whose sha256 differs from the source's. The source is only read."""
    src_root = Path(os.path.realpath(recipe_dir))
    if not src_root.is_dir():
        raise MirrorError(f"recipe directory {recipe_dir} does not exist")
    dst_root = Path(scratch_dir)
    dst_real = Path(os.path.realpath(dst_root))
    if dst_real == src_root or src_root in dst_real.parents or dst_real in src_root.parents:
        raise MirrorError("the scratch directory must not be, contain or sit inside the recipe directory (the recipe is read-only)")
    if dst_root.exists() and (not dst_root.is_dir() or any(dst_root.iterdir())):
        raise MirrorError("the scratch directory must be new or empty")
    dst_root.mkdir(parents=True, exist_ok=True)
    out: dict[str, dict] = {}
    wanted = list(RECIPE_FILES) + [("roles_acl_mirror", ROLES_MIRROR_REL)]
    for name, rel in wanted:
        src = Path(os.path.normpath(src_root / rel))
        optional = name == "roles_acl_mirror"
        if not os.path.lexists(src):
            if optional:
                continue
            raise MirrorError(f"recipe file {rel} is missing")
        p = src
        while p != src_root.parent and str(p) != "/":                  # a symlink anywhere on the path below the recipe root is refused
            if p.is_symlink():
                raise MirrorError(f"recipe file {rel}: {p} is a symlink")
            p = p.parent
        if not src.is_file():
            raise MirrorError(f"recipe file {rel} is not a regular file")
        size = src.stat().st_size
        if size > MAX_RECIPE_BYTES:
            raise MirrorError(f"recipe file {rel} is larger than {MAX_RECIPE_BYTES} bytes")
        want = sr.sha256_file(src)
        dst = dst_root / name
        shutil.copyfile(src, dst)
        os.chmod(dst, 0o600)
        if sr.sha256_file(dst) != want:
            raise MirrorError(f"copy of {rel} does not match its source sha256")
        out[name] = {"source": rel, "sha256": want, "bytes": size, "path": str(dst)}
    return out


def assert_schema_only(text: str) -> None:
    """The mirror dump is `pg_dump -s`: no data. Refuse a `COPY ... FROM stdin` block or a statement-level INSERT (the INSERT text of
    function bodies is indented and is not a statement of the dump)."""
    bad = [i for i, ln in enumerate(text.split("\n"), 1) if ln.startswith("COPY ") or ln.startswith("INSERT INTO ") or ln.startswith("\\.")]
    if bad:
        raise MirrorError(f"the schema dump holds data statements (line {bad[0]} ...): refusing to restore it")


def derive_schema_restore(text: str, *, vector_available: bool = True) -> tuple[str, dict]:
    """The restore file: the dump minus its single `CREATE SCHEMA public;` line (a new database already has `public`; the recipe's own
    `prod_schema_restore.sql` differs from the dump by exactly that line). Without pgvector, `public.vector(N)` becomes `text`
    (reported; only the embedding columns are affected and no declared fingerprint reads one)."""
    lines = text.split("\n")
    idx = [i for i, ln in enumerate(lines) if ln == SCHEMA_ONLY_LINE]
    if len(idx) != 1:
        raise MirrorError(f"expected exactly one `{SCHEMA_ONLY_LINE}` line in the dump, found {len(idx)}")
    del lines[idx[0]]
    out = "\n".join(lines)
    info = {"schema_line_removed": True, "vector_shim": False, "vector_columns_replaced": 0}
    if not vector_available:
        out, n = re.subn(r"\bpublic\.vector\(\d+\)", "text", out)
        info.update({"vector_shim": True, "vector_columns_replaced": n})
    return out, info


_ERR = re.compile(r"ERROR:\s+(.*)")


def error_classes(stderr: str) -> dict[str, int]:
    """Count psql ERROR lines by a coarse class (for the report; the pass criterion is the verification, not the error count)."""
    counts: dict[str, int] = {}
    for m in _ERR.finditer(stderr or ""):
        msg = m.group(1).lower()
        if "already exists" in msg:
            cls = "already_exists"
        elif "multiple primary keys" in msg:
            cls = "multiple_primary_keys"
        elif "does not exist" in msg:
            cls = "does_not_exist"
        elif "permission denied" in msg or "must be owner" in msg or "must be member" in msg:
            cls = "privilege"
        else:
            cls = "other"
        counts[cls] = counts.get(cls, 0) + 1
    return dict(sorted(counts.items()))


# ═════════════════════════ 1b. the target cluster and psql ═════════════════════════

@dataclass(frozen=True)
class Target:
    """Where the baseline is built: a cluster this harness owns (loopback only). `host` is 127.0.0.1 or the cluster's socket dir."""
    pg_bin: str
    host: str
    port: int
    user: str
    db: str
    policy: str = "disposable"                  # connection policy of the verification connection ('rehearsal' | 'disposable')
    expect: Mapping | None = None               # the cluster's identity {data_directory, port}
    started: bool = False                       # this call started the cluster (so the caller stops it); an already-running cluster is left running

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}@{sr.LOOPBACK}:{self.port}/{self.db}"


def run_psql(t: Target, *, file: str | Path | None = None, sql: str | None = None, on_error_stop: bool, db: str | None = None,
             timeout: int = 900) -> subprocess.CompletedProcess:
    """psql under `env -i` (no PG*, no DATABASE_URL, private empty HOME, no password file). Exactly one of `file` / `sql`."""
    if (file is None) == (sql is None):
        raise MirrorError("run_psql needs exactly one of file / sql")
    if t.port in sr.FORBIDDEN_PORTS:
        raise MirrorError(f"port {t.port} is never targeted")
    argv = [sr._bin(t.pg_bin, "psql"), "-X", "-q", "-v", f"ON_ERROR_STOP={1 if on_error_stop else 0}", "-h", t.host, "-p", str(t.port),
            "-U", t.user, "-d", db or t.db]
    argv += ["-f", str(file)] if file is not None else ["-tA", "-c", str(sql)]
    return sr._run_pg(argv, t.pg_bin, timeout=timeout)


def available_extensions(t: Target) -> set[str]:
    p = run_psql(t, sql="SELECT name FROM pg_available_extensions", on_error_stop=True, timeout=60)
    if p.returncode != 0:
        raise MirrorError(f"cannot list extensions: {p.stderr.strip()[:200]}")
    return {x.strip() for x in p.stdout.split("\n") if x.strip()}


DB_NAME_RES = {"disposable": re.compile(r"suvarna_disposable[a-z0-9_]*"), "rehearsal": sr.rg.DB_NAME_RE}


def validate_db_name(db: Any, policy: str) -> str:
    """The database a baseline may be built in: `suvarna_disposable*` for the disposable policy, `rehearsal` / `rehearsal_<suffix>` for the rehearsal
    policy. Checked BEFORE any cluster is touched, any restore runs or any CREATE DATABASE is issued."""
    if policy not in DB_NAME_RES:
        raise MirrorError(f"unknown policy {policy!r}")
    if not (isinstance(db, str) and DB_NAME_RES[policy].fullmatch(db)):
        raise MirrorError(f"database {db!r} is not allowed for the {policy} policy ({DB_NAME_RES[policy].pattern})")
    return db


def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _quote_lit(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def harness_target(root: str | Path, *, db: str, port: int, pg_bin: str = sr.DEFAULT_PG_BIN, policy: str = "disposable",
                   owner: str | None = None, allow_existing_db: bool = False) -> Target:
    """Start (initialising if needed, DISPOSABLE policy only) the cluster this harness owns at `root` and make sure `db` exists and is EMPTY.
    Lifecycle = E5.6's: marker, flock, loopback-only config, `env -i`. The caller stops it (`sr.stop_cluster`) when `Target.started`.

    REHEARSAL policy (the long-lived E5.6 cluster): the root must be exactly `sr.DEFAULT_ROOT`, the port exactly 55432, the database
    `rehearsal`/`rehearsal_<suffix>`, the cluster must ALREADY exist with a valid ownership marker (this function never initialises it), its data
    directory must be `<root>/pg` and owned by `owner` (explicit pin: the current user unless named, and always the running uid), and the
    verification connection then goes through the rehearsal policy's own identity guard. Tests only: it is not run against the real cluster here."""
    validate_db_name(db, policy)
    if policy not in ("disposable", "rehearsal"):
        raise MirrorError(f"unknown policy {policy!r}")
    lay = sr._Layout(root)
    if policy == "rehearsal":
        if os.path.realpath(root) != os.path.realpath(sr.DEFAULT_ROOT) or str(lay.root) != os.path.realpath(sr.DEFAULT_ROOT):
            raise MirrorError(f"the rehearsal policy only ever targets the rehearsal root {sr.DEFAULT_ROOT}")
        if port != sr.DEFAULT_PORT:
            raise MirrorError(f"the rehearsal policy only ever targets port {sr.DEFAULT_PORT}")
        if sr.read_marker(root) is None or not (lay.data / "PG_VERSION").is_file():
            raise MirrorError("the rehearsal cluster must already exist with a valid ownership marker: the baseline builder never initialises it")
        import pwd  # noqa: PLC0415
        try:
            data_owner = pwd.getpwuid(lay.data.stat().st_uid).pw_name
        except (OSError, KeyError) as exc:
            raise MirrorError(f"cannot determine the owner of {lay.data}") from exc
        want_owner = owner or sr._user()
        if data_owner != want_owner or lay.data.stat().st_uid != os.getuid():
            raise MirrorError(f"the data directory {lay.data} is owned by {data_owner!r}, not by {want_owner!r} running as this user")
    else:
        if port in sr.FORBIDDEN_PORTS or port == sr.DEFAULT_PORT:
            raise MirrorError(f"port {port} is never used for a disposable baseline")
        sr.init_cluster(root, port=port, pg_bin=pg_bin)
    st = sr.start_cluster(root, pg_bin=pg_bin)
    if st.get("state") != "running":
        raise MirrorError(f"cluster at {root} is not running: {st}")
    t0 = Target(pg_bin=pg_bin, host=str(lay.sock), port=port, user=sr._user(), db="postgres", policy=policy)
    p = run_psql(t0, sql=f"SELECT 1 FROM pg_database WHERE datname = {_quote_lit(db)}", on_error_stop=True, timeout=60)
    if p.returncode != 0:
        raise MirrorError(f"cannot reach the harness cluster: {p.stderr.strip()[:200]}")
    if not p.stdout.strip():
        c = run_psql(t0, sql=f"CREATE DATABASE {_quote_ident(db)}", on_error_stop=True, timeout=60)
        if c.returncode != 0:
            raise MirrorError(f"CREATE DATABASE failed: {c.stderr.strip()[:200]}")
    elif not allow_existing_db:
        n = run_psql(t0, sql="SELECT count(*) FROM pg_tables WHERE schemaname = 'public'", on_error_stop=True, db=db, timeout=60)
        if n.returncode != 0 or n.stdout.strip() != "0":
            raise MirrorError(f"database {db} already exists and is not empty: refusing to restore a mirror over it (use a fresh name)")
    expect = ({"data_directory": str(lay.data), "port": port} if policy == "disposable"
              else {"data_directory": f"{sr.DEFAULT_ROOT}/pg", "port": sr.DEFAULT_PORT})
    return Target(pg_bin=pg_bin, host=str(lay.sock), port=port, user=sr._user(), db=db, policy=policy, expect=expect,
                  started=st.get("result") == "started")


# ═════════════════════════ 1c. verification of the restored schema ═════════════════════════

def _norm_type(t: str) -> str:
    return re.sub(r"\bpublic\.", "", t.strip().lower())


def verify_l0_mirror(conn: Any, extract: Mapping, tables: Sequence[str]) -> dict:
    """Compare the restored database with the dump-derived extract for `tables`: existence, the exact column set with types, and every
    PK / plain UNIQUE index (name and columns). Read-only SELECTs on the catalogs. {tables_checked, problems[], ok}."""
    want = sorted(set(tables))
    problems: list[str] = []
    ext = extract.get("tables", {})
    for t in want:
        if t not in ext:
            problems.append(f"{t}: not in the schema extract")
    have_cols: dict[str, dict[str, str]] = {}
    cur = conn.execute(
        "SELECT c.relname, a.attname, pg_catalog.format_type(a.atttypid, a.atttypmod) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace JOIN pg_attribute a ON a.attrelid = c.oid "
        "WHERE n.nspname = 'public' AND c.relkind IN ('r','p') AND c.relname = ANY(%s) AND a.attnum > 0 AND NOT a.attisdropped",
        (want,))
    for rel, col, typ in cur.fetchall():
        have_cols.setdefault(rel, {})[col] = typ
    have_idx: dict[str, dict[str, list[str]]] = {}
    cur = conn.execute(
        "SELECT c.relname, ic.relname, array(SELECT a.attname FROM unnest(ix.indkey) WITH ORDINALITY k(attnum, ord) "
        "JOIN pg_attribute a ON a.attrelid = ix.indrelid AND a.attnum = k.attnum ORDER BY k.ord) "
        "FROM pg_index ix JOIN pg_class c ON c.oid = ix.indrelid JOIN pg_class ic ON ic.oid = ix.indexrelid "
        "JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'public' AND ix.indisunique AND ix.indpred IS NULL "
        "AND ix.indexprs IS NULL AND c.relname = ANY(%s)", (want,))
    for rel, idx, cols in cur.fetchall():
        have_idx.setdefault(rel, {})[idx] = list(cols)
    for t in want:
        if t not in ext:
            continue
        if t not in have_cols:
            problems.append(f"{t}: table is missing from the restored database")
            continue
        e_cols = {c: _norm_type(m["type"]) for c, m in ext[t]["columns"].items()}
        h_cols = {c: _norm_type(v) for c, v in have_cols[t].items()}
        for c in sorted(set(e_cols) - set(h_cols)):
            problems.append(f"{t}.{c}: column is missing")
        for c in sorted(set(h_cols) - set(e_cols)):
            problems.append(f"{t}.{c}: unexpected column")
        for c in sorted(set(e_cols) & set(h_cols)):
            if e_cols[c] != h_cols[c]:
                problems.append(f"{t}.{c}: type {h_cols[c]!r}, the dump says {e_cols[c]!r}")
        wanted_idx = {}
        if ext[t].get("primary_key") and ext[t].get("primary_key_name"):
            wanted_idx[ext[t]["primary_key_name"]] = ext[t]["primary_key"]
        for u in ext[t].get("unique", []):
            wanted_idx[u["name"]] = u["columns"]
        for name, cols in sorted(wanted_idx.items()):
            got = have_idx.get(t, {}).get(name)
            if got is None:
                problems.append(f"{t}: unique/primary index {name} is missing")
            elif got != cols:
                problems.append(f"{t}: index {name} covers {got}, the dump says {cols}")
    return {"tables_checked": len(want), "problems": problems, "ok": not problems}


# ═════════════════════════ 1d. the baseline builder and its document ═════════════════════════

def _step(name: str, status: str, **detail: Any) -> dict:
    return {"name": name, "status": status, "detail": detail}


def build_mirror_baseline(recipe_dir: str | Path, scratch_dir: str | Path, target: Target, *, decls: fd.Declarations | None = None,
                          extract: Mapping | None = None, with_l1_fixes: bool = False, connect: Any = None) -> dict:
    """Restore the production-faithful schema from the READ-ONLY recipe onto `target` (a cluster this harness started) and verify it.
    Steps (STEP_ORDER): copy_recipe, schema_only_check, extensions, roles, schema, sequences, seed_fixes (L1 data-plane fixes: SKIPPED unless
    `with_l1_fixes`), verify. NO production access. Returns the closed-schema document (`validate_baseline`)."""
    validate_db_name(target.db, target.policy)                  # before ANY file is copied, restore run or database touched
    if target.port in sr.FORBIDDEN_PORTS:
        raise MirrorError(f"port {target.port} is never targeted")
    decls = decls or fd.load_declarations()
    extract = extract or fd.load_schema_extract()
    steps: list[dict] = []
    copied = copy_recipe(recipe_dir, scratch_dir)
    recipe = {n: {k: v for k, v in m.items() if k != "path"} for n, m in copied.items()}
    steps.append(_step("copy_recipe", "OK", files=sorted(copied)))
    schema_text = Path(copied["schema"]["path"]).read_text(encoding="utf-8")
    assert_schema_only(schema_text)
    steps.append(_step("schema_only_check", "OK", statements_checked=schema_text.count("\n") + 1))
    roles_same = None
    if "roles_acl_mirror" in copied:
        def stmts(p: str) -> list[str]:
            return sorted(ln.strip() for ln in Path(p).read_text(encoding="utf-8").split("\n")
                          if re.match(r"(CREATE ROLE|ALTER ROLE|GRANT) ", ln.strip()))
        roles_same = stmts(copied["roles"]["path"]) == stmts(copied["roles_acl_mirror"]["path"])
    # extensions
    avail = available_extensions(target)
    have_ext, missing_ext = [], []
    for ext_name in EXTENSIONS:
        if ext_name in avail:
            p = run_psql(target, sql=f'CREATE EXTENSION IF NOT EXISTS "{ext_name}"', on_error_stop=True, timeout=120)
            (have_ext if p.returncode == 0 else missing_ext).append(ext_name)
        else:
            missing_ext.append(ext_name)
    steps.append(_step("extensions", "OK" if not missing_ext else "TOLERATED_ERRORS", installed=have_ext, unavailable=missing_ext))
    # roles (cluster-global; an existing role is tolerated so a re-run is idempotent, any other error fails the step)
    p = run_psql(target, file=copied["roles"]["path"], on_error_stop=False)
    cls = error_classes(p.stderr)
    other = {k: v for k, v in cls.items() if k != "already_exists"}
    steps.append(_step("roles", "FAILED" if (p.returncode != 0 or other) else ("TOLERATED_ERRORS" if cls else "OK"), rc=p.returncode, errors=cls))
    # schema
    restore_text, info = derive_schema_restore(schema_text, vector_available="vector" in have_ext)
    restore_path = Path(scratch_dir) / "schema_restore.sql"
    restore_path.write_text(restore_text, encoding="utf-8")
    os.chmod(restore_path, 0o600)
    p = run_psql(target, file=restore_path, on_error_stop=False)
    cls = error_classes(p.stderr)
    steps.append(_step("schema", "FAILED" if p.returncode != 0 else ("TOLERATED_ERRORS" if cls else "OK"), rc=p.returncode, errors=cls))
    derived = {"schema_restore_sha256": sha256_text(restore_text), **info, "roles_statements_equal_w1_mirror": roles_same}
    # sequences
    p = run_psql(target, file=copied["sequences"]["path"], on_error_stop=True)
    steps.append(_step("sequences", "OK" if p.returncode == 0 else "FAILED", rc=p.returncode, errors=error_classes(p.stderr)))
    # seed fixes (L1 data plane): optional
    if with_l1_fixes:
        p = run_psql(target, file=copied["seed_fixes"]["path"], on_error_stop=False)
        cls = error_classes(p.stderr)
        steps.append(_step("seed_fixes", "FAILED" if p.returncode != 0 else ("TOLERATED_ERRORS" if cls else "OK"), rc=p.returncode, errors=cls))
    else:
        steps.append(_step("seed_fixes", "SKIPPED", reason="OPTIONAL_L1: the fixes touch l1_data_plane_* comments and trigger-attestation OIDs, "
                                                          "which no L0 declaration reads"))
    # verification (psycopg through the connection policy)
    names = sorted(fd.tables_named(decls.doc))
    cluster = {"host": sr.LOOPBACK, "port": target.port, "database": target.db, "policy": target.policy, "data_directory": None, "pg_version": None}
    verification: dict
    if connect is None and not sr._psycopg_available():
        steps.append(_step("verify", "UNMEASURED", reason="NEEDS_PSYCOPG"))
        verification = {"tables_checked": 0, "problems": [], "ok": False}
    else:
        log = sr.ConnectionLog()
        try:
            conn = sr.connect_checked(target.url, target.policy, log, expect=target.expect, connect=connect)
        except sr.EndpointRefused as exc:
            steps.append(_step("verify", "FAILED", reason=f"connection refused: {exc}"))
            verification = {"tables_checked": 0, "problems": [f"connection refused: {exc}"], "ok": False}
        else:
            try:
                ident = sr._server_identity(conn)
                cluster["data_directory"] = ident["data_directory"]
                cluster["pg_version"] = str(conn.execute("SHOW server_version").fetchone()[0])
                verification = verify_l0_mirror(conn, extract, names)
            finally:
                with contextlib.suppress(Exception):
                    conn.rollback()
                conn.close()
            steps.append(_step("verify", "OK" if verification["ok"] else "FAILED", problems=len(verification["problems"])))
    doc = {"schema": BASELINE_SCHEMA, "tool_sha256": tool_sha256(), "result": "", "with_l1_fixes": bool(with_l1_fixes), "recipe": recipe,
           "derived": derived, "cluster": cluster, "steps": steps, "verification": verification}
    doc["result"] = derive_baseline_result(doc)
    return doc


BASELINE_KEYS = ("schema", "tool_sha256", "result", "with_l1_fixes", "recipe", "derived", "cluster", "steps", "verification")
DERIVED_KEYS = ("schema_restore_sha256", "schema_line_removed", "vector_shim", "vector_columns_replaced", "roles_statements_equal_w1_mirror")
CLUSTER_KEYS = ("host", "port", "database", "policy", "data_directory", "pg_version")


def derive_baseline_result(doc: Mapping) -> str:
    """PASS only when every step ran to a non-failing status in order, the verification found no problem, and the L1 fixes step is either
    run or SKIPPED; UNMEASURED when verification could not run; otherwise FAIL. Re-derived by `validate_baseline`."""
    steps = {s["name"]: s["status"] for s in doc["steps"] if isinstance(s, Mapping)}
    if any(steps.get(n) == "FAILED" for n in STEP_ORDER):
        return "FAIL"
    if steps.get("verify") == "UNMEASURED":
        return "UNMEASURED"
    ordered = tuple(s["name"] for s in doc["steps"]) == STEP_ORDER
    required_ok = ordered and all(steps[n] in ("OK", "TOLERATED_ERRORS") for n in STEP_ORDER if n != "seed_fixes")
    seed_ok = ordered and steps["seed_fixes"] in ("OK", "TOLERATED_ERRORS", "SKIPPED")
    verified = bool(doc["verification"].get("ok")) and steps.get("verify") == "OK"
    return "PASS" if (required_ok and seed_ok and verified) else "FAIL"


def validate_baseline(doc: Any) -> list[str]:
    """Problems with a baseline document ([] = valid): closed keys, ordered steps with known statuses, hashes, and the result re-derived."""
    p: list[str] = []
    if not isinstance(doc, Mapping) or set(doc) != set(BASELINE_KEYS):
        return ["the baseline is not an object with exactly the closed keys"]
    try:
        if doc["schema"] != BASELINE_SCHEMA:
            p.append("schema id differs")
        if doc["tool_sha256"] != tool_sha256():
            p.append("tool_sha256 is not the sha256 of the repo tool")
        if not isinstance(doc["recipe"], Mapping) or not {"schema", "roles", "sequences", "seed_fixes"} <= set(doc["recipe"]):
            p.append("recipe must list schema, roles, sequences, seed_fixes")
        else:
            for n, m in doc["recipe"].items():
                if not (isinstance(m, Mapping) and set(m) == {"source", "sha256", "bytes"} and SHA256.fullmatch(str(m["sha256"]))):
                    p.append(f"recipe.{n} malformed")
        d = doc["derived"]
        if not (isinstance(d, Mapping) and set(d) == set(DERIVED_KEYS) and SHA256.fullmatch(str(d["schema_restore_sha256"]))):
            p.append("derived malformed")
        c = doc["cluster"]
        if not (isinstance(c, Mapping) and set(c) == set(CLUSTER_KEYS) and c["host"] == sr.LOOPBACK and isinstance(c["port"], int)
                and c["port"] not in sr.FORBIDDEN_PORTS):
            p.append("cluster must be loopback on an allowed port")
        st = doc["steps"]
        if not isinstance(st, list) or not all(isinstance(s, Mapping) and set(s) == {"name", "status", "detail"} for s in st):
            return p + ["steps malformed"]
        if any(s["status"] not in STEP_STATUSES for s in st):
            p.append("a step has an unknown status")
        if tuple(s["name"] for s in st) != STEP_ORDER:
            p.append(f"steps must be exactly {STEP_ORDER} in order")
        elif any(s["status"] == "SKIPPED" and s["name"] not in ("seed_fixes",) for s in st):
            p.append("only seed_fixes may be SKIPPED")
        v = doc["verification"]
        if not (isinstance(v, Mapping) and set(v) == {"tables_checked", "problems", "ok"} and isinstance(v["problems"], list)):
            return p + ["verification malformed"]
        if v["ok"] is not (not v["problems"] and v["tables_checked"] > 0):
            p.append("verification.ok is not derived from its problems and table count")
        if doc["result"] != derive_baseline_result(doc):
            p.append("result differs from the one re-derived from the steps and the verification")
    except (KeyError, TypeError, AttributeError, ValueError) as exc:
        p.append(f"malformed baseline ({type(exc).__name__})")
    return p


def write_json(doc: Mapping, path: str | Path) -> str:
    text = json.dumps(doc, sort_keys=True, indent=1, ensure_ascii=True) + "\n"
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_name(target.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)
    return sha256_text(text)


# ═════════════════════════ 2. fingerprint output (both sides of the drill) ═════════════════════════

OUTPUT_KEYS = ("schema", "side", "stage", "definition", "declarations_sha256", "commit", "as_of", "rebuild", "tables", "fingerprints")
SIDES = ("production", "rehearsal")
STAGES = ("baseline", "after_rebuild", "production_read")
BUILD_RECORD_SCHEMA = "suvarna-build-record/v1"


def _iso_date(v: Any) -> bool:
    try:
        return isinstance(v, str) and dt.date.fromisoformat(v).isoformat() == v
    except ValueError:
        return False


def real_uuid(v: Any) -> bool:
    """A real, canonical (lower-case, hyphenated) RFC 4122 UUID of version 1-8: refuses the nil / all-zero id, `-`*36, anything that only
    looks like one."""
    if not isinstance(v, str):
        return False
    try:
        u = uuid.UUID(v)
    except ValueError:
        return False
    return str(u) == v and u.variant == uuid.RFC_4122 and u.version in range(1, 9)


def _receipt_ok(rebuild: Any) -> bool:
    return (isinstance(rebuild, Mapping) and set(rebuild) == {"run_id", "orchestrator_commit"} and real_uuid(rebuild["run_id"])
            and isinstance(rebuild["orchestrator_commit"], str) and bool(HEX40.fullmatch(rebuild["orchestrator_commit"])))


def rehearsal_fingerprints(conn: Any, decls: fd.Declarations, *, stage: str, as_of: str, commit: str, units: Sequence[str] | None = None,
                           rebuild: Mapping | None = None) -> dict:
    """The rehearsal side: per comparison unit per table {sha256, rows} + the composite, through an open connection (open it with
    `sr.connect_checked`), in a READ ONLY transaction. stage `after_rebuild` must carry `rebuild` {run_id (a real UUID), orchestrator_commit}:
    a file cannot claim a rebuild it has no receipt for (and the receipt is only SHAPE-checked until a build record verifies it, see
    `verify_rebuild_receipt`). An undeclared asset is refused by `unit_fingerprints`."""
    if stage not in ("baseline", "after_rebuild"):
        raise MirrorError("stage must be 'baseline' or 'after_rebuild'")
    if not _iso_date(as_of) or not (isinstance(commit, str) and HEX40.fullmatch(commit)):
        raise MirrorError("as_of must be YYYY-MM-DD and commit 40-hex")
    if (stage == "after_rebuild") != (rebuild is not None):
        raise MirrorError("stage after_rebuild needs a rebuild receipt, and a baseline stage must not carry one")
    if rebuild is not None and not _receipt_ok(rebuild):
        raise MirrorError("rebuild must be exactly {run_id (a real UUID: not nil, not all-zero), orchestrator_commit (40-hex)}")
    conn.rollback()                                # the identity check left a transaction open; read_only can only be set outside one
    conn.read_only = True
    try:
        r = fd.unit_fingerprints(conn, decls, units, cursor_prefix="e57")
    finally:
        with contextlib.suppress(Exception):
            conn.rollback()
    return {"schema": OUTPUT_SCHEMA, "side": "rehearsal", "stage": stage, "definition": fd.FINGERPRINT_DEFINITION,
            "declarations_sha256": decls.sha256, "commit": commit, "as_of": as_of, "rebuild": dict(rebuild) if rebuild else None,
            "tables": r["tables"], "fingerprints": r["fingerprints"]}


def validate_fingerprint_output(doc: Any, decls: fd.Declarations, *, side: str) -> list[str]:
    """Problems with a fingerprint-output document of `side` ([] = valid). The production reader's file and the rehearsal file are held to the
    same rules: closed keys, the one definition, THIS declarations file's sha256, only comparison units and exactly their declared tables,
    well-formed {sha256, rows}, every unit fingerprint equal to the composition of its table fingerprints (recomputed, never trusted), and
    row counts that agree with the hashes (an empty table hashes to one known value; a non-empty table never does)."""
    if side not in SIDES:
        raise MirrorError(f"side must be one of {SIDES}")
    if not isinstance(doc, Mapping) or set(doc) != set(OUTPUT_KEYS):
        return ["the document is not an object with exactly the closed keys"]
    p: list[str] = []
    if doc["schema"] != OUTPUT_SCHEMA:
        p.append("schema id differs")
    if doc["side"] != side:
        p.append(f"side is {doc['side']!r}, expected {side!r}")
    if doc["definition"] != fd.FINGERPRINT_DEFINITION:
        p.append(f"definition must be {fd.FINGERPRINT_DEFINITION}: one fingerprint definition only")
    if doc["declarations_sha256"] != decls.sha256:
        p.append("declarations_sha256 is not the sha256 of the declarations file in use")
    if not (isinstance(doc["commit"], str) and HEX40.fullmatch(doc["commit"])):
        p.append("commit must be 40-hex")
    if not _iso_date(doc["as_of"]):
        p.append("as_of must be YYYY-MM-DD")
    allowed = STAGES[:2] if side == "rehearsal" else STAGES[2:]
    if doc["stage"] not in allowed:
        p.append(f"stage {doc['stage']!r} is not valid for the {side} side {allowed}")
    if side == "rehearsal":
        if (doc["stage"] == "after_rebuild") != (doc["rebuild"] is not None):
            p.append("an after_rebuild file needs a rebuild receipt and a baseline file must not have one")
        if doc["rebuild"] is not None and not _receipt_ok(doc["rebuild"]):
            p.append("rebuild must be exactly {run_id (a real UUID), orchestrator_commit (40-hex)}")
    elif doc["rebuild"] is not None:
        p.append("a production file has no rebuild receipt")
    tabs, fps = doc["tables"], doc["fingerprints"]
    if not (isinstance(tabs, Mapping) and isinstance(fps, Mapping)):
        return p + ["tables and fingerprints must be objects"]
    units = set(decls.expected_assets())
    for a in sorted(set(tabs) | set(fps)):
        if a not in units:
            p.append(f"{a}: not a comparison unit (undeclared and unknown assets are refused, never compared)")
    for a in sorted(set(tabs) ^ set(fps)):
        p.append(f"{a}: present in {'tables' if a in tabs else 'fingerprints'} only: tables and fingerprints must cover the same units")
    for a in sorted(set(tabs) & set(fps) & units):
        t = tabs[a]
        if not (isinstance(t, Mapping) and set(t) == set(decls.tables(a))):
            p.append(f"{a}: tables must be exactly {decls.tables(a)}")
            continue
        ok = True
        for name, m in t.items():
            if not (isinstance(m, Mapping) and set(m) == {"sha256", "rows"} and isinstance(m["sha256"], str) and SHA256.fullmatch(m["sha256"])
                    and isinstance(m["rows"], int) and not isinstance(m["rows"], bool) and m["rows"] >= 0):
                p.append(f"{a}.{name}: must be {{sha256, rows}}")
                ok = False
                continue
            empty = fd.empty_table_fingerprint(decls, a, name)
            if m["rows"] > 0 and m["sha256"] == empty:
                p.append(f"{a}.{name}: rows={m['rows']} but the fingerprint is the empty-table fingerprint: the row count and the hash disagree")
                ok = False
            elif m["rows"] == 0 and m["sha256"] != empty:
                p.append(f"{a}.{name}: rows=0 but the fingerprint is not the empty-table fingerprint: the row count and the hash disagree")
                ok = False
        if ok and fps.get(a) != fd.composite_fingerprint({n: m["sha256"] for n, m in t.items()}):
            p.append(f"{a}: the unit fingerprint is not the composition of its table fingerprints")
    return p


def verify_rebuild_receipt(receipt: Any, record: Any, decls: fd.Declarations) -> list[str]:
    """Problems verifying a rehearsal rebuild receipt {run_id, orchestrator_commit} against an orchestrator BUILD RECORD the harness can read
    offline (`suvarna-build-record/v1`: a read-only export of the run's `build_runs` / `build_run_assets` rows: {schema, run_id, state
    'completed', orchestrator_commit, assets: [{asset_id, state 'complete'}]}). [] = the receipt matches a completed run that built every
    declared asset at the receipt's commit. Without such a record a receipt is only a claim."""
    p: list[str] = []
    if not _receipt_ok(receipt):
        return ["the receipt is not {run_id (a real UUID), orchestrator_commit (40-hex)}"]
    if not (isinstance(record, Mapping) and set(record) == {"schema", "run_id", "state", "orchestrator_commit", "assets"}):
        return ["the build record is not an object with exactly {schema, run_id, state, orchestrator_commit, assets}"]
    if record["schema"] != BUILD_RECORD_SCHEMA:
        p.append("build record schema id differs")
    if not real_uuid(record["run_id"]) or record["run_id"] != receipt["run_id"]:
        p.append("the build record's run_id is not the receipt's run_id")
    if record["state"] != "completed":
        p.append(f"the build record's run state is {record['state']!r}, not 'completed'")
    if record["orchestrator_commit"] != receipt["orchestrator_commit"]:
        p.append("the build record was made at a different orchestrator commit than the receipt claims")
    assets = record["assets"]
    if not (isinstance(assets, list) and all(isinstance(x, Mapping) and set(x) == {"asset_id", "state"} for x in assets)):
        return p + ["the build record's assets must be a list of {asset_id, state}"]
    built = {x["asset_id"] for x in assets if x["state"] == "complete"}
    missing = sorted(set(decls.declared_assets()) - built)
    if missing:
        p.append(f"the build record does not show these declared assets complete: {missing}")
    return p


# ═════════════════════════ 3. the production-side reader specification (NOT executed here) ═════════════════════════

def reader_spec(decls: fd.Declarations) -> dict:
    """Exactly what the production-side reader runs (as `suvarna_reader`, by the `suvarna` user; never here): one READ ONLY transaction, one
    server-side cursor per table issuing the SELECT below (E5.5's `build_select` of the declaration), rows consumed in-process by
    `nikasha_stale_certs.fingerprint_rows`; the output file (`suvarna-l0-fingerprints/v1`, side production) holds aggregates only. The units are
    the comparison units: assets with tables of their own and one `grp_<id>` per shared-table group."""
    return {"definition": fd.FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256, "role": "suvarna_reader",
            "transaction": "SET TRANSACTION READ ONLY (statement_timeout and lock_timeout are the role's own)",
            "fingerprint": "nikasha_stale_certs.fingerprint_rows(rows, declaration) per table; unit = fingerprint_declarations.composite_fingerprint",
            "output": {"schema": OUTPUT_SCHEMA, "side": "production", "stage": "production_read", "contains": "aggregates only: per table sha256 and rows"},
            "selects": fd.reader_selects(decls), "ownership_probes": [dict(x) for x in OWNERSHIP_PROBES],
            "probe_results": "00_ARCHITECTURE/control/FINGERPRINT_OWNERSHIP_PROBES_2026-10-03.txt",
            "undeclared": decls.undeclared_assets(), "groups": decls.drill_coverage()["groups"],
            "expected_differences": decls.expected_differences()}


# ═════════════════════════ 4. compare (the existing E5.7 comparison) and status ═════════════════════════

def _rows_of(doc: Mapping, unit: str) -> dict | None:
    t = doc["tables"].get(unit)
    return {n: m["rows"] for n, m in t.items()} if t else None


def build_drill(production: Mapping, rehearsal: Mapping, decls: fd.Declarations, explained: Mapping | None, *, commit: str) -> tuple[dict, dict]:
    """Validate both sides, require the same as-of pin and an after_rebuild rehearsal, then apply `suvarna_rehearsal.compare_fingerprint_sets` over
    expected_assets = the comparison units (declared assets with tables + one unit per group), with the declarations' `coverage` block and both
    sides' row counts embedded in the drill document. Returns (drill document, coverage report). Raises MirrorError listing every problem."""
    problems = [f"production: {x}" for x in validate_fingerprint_output(production, decls, side="production")]
    problems += [f"rehearsal: {x}" for x in validate_fingerprint_output(rehearsal, decls, side="rehearsal")]
    if not problems:
        if rehearsal["stage"] != "after_rebuild":
            problems.append("rehearsal: the comparison needs the after_rebuild fingerprints (a baseline file proves no rebuild)")
        if production["as_of"] != rehearsal["as_of"]:
            problems.append(f"as_of differs: production {production['as_of']} vs rehearsal {rehearsal['as_of']} (pin one window)")
        if rehearsal["rebuild"] and rehearsal["rebuild"]["orchestrator_commit"] != commit:
            problems.append("the rebuild's orchestrator_commit is not the evidence commit")
    if problems:
        raise MirrorError("; ".join(problems))
    rows = {u: {"production": _rows_of(production, u), "rehearsal": _rows_of(rehearsal, u)}
            for u in sorted(set(production["tables"]) | set(rehearsal["tables"]))}
    drill = sr.compare_fingerprint_sets(sr.fingerprint_set(production["fingerprints"]), sr.fingerprint_set(rehearsal["fingerprints"]), explained,
                                        expected_assets=decls.expected_assets(), commit=commit, coverage=decls.drill_coverage(), rows=rows)
    cov = decls.coverage_report()
    differing = {d["asset"]: d for d in drill["differences"]}
    unit_status: dict[str, dict] = {}
    for u in decls.expected_assets():
        st = ("equal" if u in drill["equal"] else "empty_both_sides" if u in drill["empty_both_sides"] else differing[u]["kind"] if u in differing
              else "uncovered")
        unit_status[u] = {"status": st, "members": decls.members(u)}
    cov["unit_status"] = unit_status
    cov["differences_with_hints"] = [{"asset": d["asset"], "kind": d["kind"], "members": decls.members(d["asset"]),
                                      "reproducibility": decls.reproducibility(d["asset"]),
                                      "table_notes": {t["name"]: t["notes"] for t in decls._unit_tables(d["asset"]) if t.get("notes")}}
                                     for d in drill["differences"]]
    cov["expected_differences_status"] = [{**e, "status": "observed" if e["unit"] in differing else "not_observed",
                                           "hint": ("explain it (reason code production_ahead_of_commit, an SS decision id)" if e["unit"] in differing else
                                                    "the unit did not differ: if the referenced change has landed, remove this record")}
                                          for e in decls.expected_differences()]
    cov["empty_both_sides"] = list(drill["empty_both_sides"])
    for u, st in drill["seeded"].items():
        unit_status[u] = {"status": f"seeded:{st}", "members": decls.members(u)}
    cov["seeded_status"] = dict(drill["seeded"])
    cov["as_of"] = production["as_of"]
    cov["result"] = drill["result"]
    cov["headline"] = coverage_headline(drill["result"], drill["coverage"], len(decls.assets), drill["seeded"])
    cov["limits"] = list(LIMITS_TEXT)
    cov["note"] = "undeclared assets are NOT in expected_assets: they are reported here and in the drill's coverage block, not compared"
    return drill, cov


def build_record_spec(decls: fd.Declarations) -> dict:
    """Exactly what `drill status --build-record PATH` expects (the orchestrator-side export of the rehearsal run): the path argument, the schema id,
    every required field and the declared assets that must all appear complete."""
    return {**copy.deepcopy(BUILD_RECORD_SPEC), "declared_assets_that_must_be_complete": decls.declared_assets()}


def coverage_headline(result: str, cov: Mapping, assets_total: int, seeded_status: Mapping | None = None) -> str:
    """The one-paragraph statement printed next to the result: the numbers AND the names behind them."""
    part, seeded, nd = cov["partial"], cov["seeded"], cov["non_deterministic"]
    undeclared = sorted(cov["undeclared"])
    status = seeded_status or {}
    part_txt = "; ".join("%s (not covered: %s)" % (a, ", ".join(t)) for a, t in sorted(part.items()))
    nd_txt = ", ".join("%s %s" % (u, v) for u, v in sorted(nd.items()))
    seeded_txt = ", ".join("%s [%s]" % (u, status.get(u, "not compared")) for u in seeded)
    bits = ["%s: %d of %d L0 assets declared (%d full, %d partial%s)" % (result, len(cov["declared"]), assets_total, len(cov["declared"]) - len(part),
                                                                       len(part), (": " + part_txt) if part else ""),
            "%d undeclared%s" % (len(undeclared), (": " + ", ".join(undeclared)) if undeclared else ""),
            "%d non-deterministic%s" % (len(nd), (": " + nd_txt) if nd else ""),
            "%d SEEDED (shown, not counted toward the verdict)%s" % (len(seeded), (": " + seeded_txt) if seeded else ""),
            "%d comparison units, %d in the rebuilt-equals-source claim" % (len(cov["units"]), len(cov["units"]) - len(seeded))]
    return "; ".join(bits) + "."

def drill_status(decls: fd.Declarations, *, baseline: Any = None, production: Any = None, rehearsal: Any = None, build_record: Any = None) -> dict:
    """Which steps are measured and which are not. A step is MEASURED only when this module recomputed it from the declarations; a file that
    merely has the right SHAPE is SHAPE_CHECKED, a rehearsal rebuild receipt without a verifying build record is CLAIMED_UNVERIFIED, and
    everything that needs an outside actor is UNMEASURED with its NEEDS_* reason. The result is therefore always UNMEASURED today: this
    function can never say a drill is done."""
    steps: list[dict] = [{"step": "declarations", "state": "MEASURED", "detail": {"declared": len(decls.declared_assets()),
                                                                                  "undeclared": len(decls.undeclared_assets()),
                                                                                  "units": len(decls.expected_assets()), "sha256": decls.sha256}}]
    bprob = validate_baseline(baseline) if baseline is not None else None
    if baseline is not None and not bprob and baseline["result"] == "PASS":
        steps.append({"step": "mirror_baseline", "state": "SHAPE_CHECKED", "detail": {"result": "PASS", "note": "the file validates; the restore was not re-run"}})
    else:
        steps.append({"step": "mirror_baseline", "state": "UNMEASURED", "reason": NEEDS["baseline"], "detail": {"problems": bprob} if bprob else {}})
    steps.append({"step": "text_seed", "state": "UNMEASURED", "reason": NEEDS["text_seed"]})
    reh_p = validate_fingerprint_output(rehearsal, decls, side="rehearsal") if rehearsal is not None else None
    if rehearsal is not None and not reh_p and rehearsal["stage"] == "after_rebuild":
        rprob = verify_rebuild_receipt(rehearsal["rebuild"], build_record, decls) if build_record is not None else ["no build record supplied"]
        if not rprob:
            steps.append({"step": "rehearsal_l0_rebuild", "state": "MEASURED", "detail": {"run_id": rehearsal["rebuild"]["run_id"],
                                                                                           "verified_against": BUILD_RECORD_SCHEMA}})
        else:
            steps.append({"step": "rehearsal_l0_rebuild", "state": "CLAIMED_UNVERIFIED", "reason": NEEDS["rebuild"],
                          "detail": {"run_id": rehearsal["rebuild"]["run_id"], "unverified_because": rprob,
                                     "expects": f"--build-record PATH holding a {BUILD_RECORD_SCHEMA} (see build_record_expected)"}})
    else:
        steps.append({"step": "rehearsal_l0_rebuild", "state": "UNMEASURED", "reason": NEEDS["rebuild"],
                      "detail": {**({"problems": reh_p} if reh_p else {}),
                                 "expects": f"a rehearsal after_rebuild fingerprint file with a rebuild receipt, then --build-record PATH holding a {BUILD_RECORD_SCHEMA} "
                                            "(see build_record_expected)"}})
    prod_p = validate_fingerprint_output(production, decls, side="production") if production is not None else None
    if production is not None and not prod_p:
        steps.append({"step": "production_fingerprints", "state": "SHAPE_CHECKED",
                      "detail": {"units": len(production["fingerprints"]), "note": "a file written by the reader: shape and consistency only, not re-read"}})
    else:
        steps.append({"step": "production_fingerprints", "state": "UNMEASURED", "reason": NEEDS["production"], "detail": {"problems": prod_p} if prod_p else {}})
    steps.append({"step": "linux_amd64_runtime", "state": "UNMEASURED", "reason": NEEDS["linux"],
                  "detail": {"units": sorted(u for u, v in decls.units().items() if "platform_bound" in v["reproducibility"])}})
    pinned = production is not None and rehearsal is not None and not prod_p and not reh_p and production["as_of"] == rehearsal["as_of"]
    rolling = sorted(u for u, v in decls.units().items() if "rolling_horizon" in v["reproducibility"])
    if pinned:
        steps.append({"step": "as_of_pin", "state": "SHAPE_CHECKED", "detail": {"as_of": production["as_of"], "rolling_horizon_units": rolling,
                                                                               "note": "both files carry the same date; nothing proves the window was applied"}})
    else:
        steps.append({"step": "as_of_pin", "state": "UNMEASURED", "reason": NEEDS["as_of"], "detail": {"rolling_horizon_units": rolling}})
    steps.append({"step": "ss_decisions", "state": "UNMEASURED", "reason": NEEDS["decisions"]})
    return {"result": "UNMEASURED", "steps": steps, "build_record_expected": build_record_spec(decls)}


# ═════════════════════════ CLI ═════════════════════════

def _print(obj: Any) -> None:
    print(json.dumps(obj, sort_keys=True, indent=2))


def _rd(path: str | Path) -> Any:
    return fd.strict_loads(Path(path).read_text(encoding="utf-8"))      # duplicate keys, NaN and Infinity are refused


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog=TOOL_NAME, description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("expected", "reader-spec"):
        s = sub.add_parser(name)
        s.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    b = sub.add_parser("baseline")
    b.add_argument("--recipe", default=os.environ.get(RECIPE_ENV), help=f"the mirror recipe directory (default: ${RECIPE_ENV})")
    b.add_argument("--scratch", required=True)
    b.add_argument("--root", required=True)
    b.add_argument("--port", type=int, required=True)
    b.add_argument("--policy", choices=("disposable", "rehearsal"), default="disposable")
    b.add_argument("--db", default=None, help="default: suvarna_disposable_mirror (disposable) / rehearsal_mirror (rehearsal)")
    b.add_argument("--owner", help="rehearsal policy: the OS user that must own the data directory (explicit pin)")
    b.add_argument("--data-directory", help="rehearsal policy: must equal <root>/pg (explicit pin)")
    b.add_argument("--allow-existing-db", action="store_true")
    b.add_argument("--pg-bin", default=sr.DEFAULT_PG_BIN)
    b.add_argument("--with-l1-fixes", action="store_true")
    b.add_argument("--keep-running", action="store_true")
    b.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    b.add_argument("--schema-extract", default=str(fd.DEFAULT_SCHEMA_EXTRACT))
    b.add_argument("--out", required=True)
    vb = sub.add_parser("validate-baseline")
    vb.add_argument("path")
    rf = sub.add_parser("rehearsal-fingerprints")
    rf.add_argument("--url", required=True)
    rf.add_argument("--policy", choices=("rehearsal", "disposable"), required=True)
    rf.add_argument("--data-directory")
    rf.add_argument("--stage", choices=("baseline", "after_rebuild"), required=True)
    rf.add_argument("--as-of", required=True)
    rf.add_argument("--commit", required=True)
    rf.add_argument("--rebuild-run-id")
    rf.add_argument("--orchestrator-commit")
    rf.add_argument("--out", required=True)
    rf.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    c = sub.add_parser("compare")
    c.add_argument("--production", required=True)
    c.add_argument("--rehearsal", required=True)
    c.add_argument("--commit", required=True)
    c.add_argument("--explained")
    c.add_argument("--out", required=True)
    c.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    br = sub.add_parser("build-record-spec")
    br.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    st = sub.add_parser("status")
    st.add_argument("--baseline")
    st.add_argument("--production")
    st.add_argument("--rehearsal")
    st.add_argument("--build-record")
    st.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    a = ap.parse_args(argv)
    try:
        if a.cmd == "validate-baseline":
            try:
                doc = _rd(a.path)
            except (OSError, ValueError, fd.DeclarationError) as exc:
                _print({"valid": False, "problems": [f"unreadable baseline file ({type(exc).__name__})"]})
                return 2
            probs = validate_baseline(doc)
            _print({"valid": not probs, "problems": probs})
            return 0 if not probs else 2
        if a.cmd == "baseline":
            policy = a.policy
            db = validate_db_name(a.db or ("suvarna_disposable_mirror" if policy == "disposable" else "rehearsal_mirror"), policy)   # before anything else
            if not a.recipe:
                raise MirrorError(f"no recipe directory: pass --recipe or set ${RECIPE_ENV}")
            if policy == "rehearsal":
                if not a.owner or not a.data_directory:
                    raise MirrorError("the rehearsal policy needs the explicit pins --owner and --data-directory")
                if os.path.realpath(a.data_directory) != os.path.realpath(os.path.join(a.root, "pg")):
                    raise MirrorError("--data-directory must be <root>/pg")
            decls = fd.load_declarations(a.declarations)
            root = Path(os.path.realpath(a.root))
            t = harness_target(root, db=db, port=a.port, pg_bin=a.pg_bin, policy=policy, owner=a.owner, allow_existing_db=a.allow_existing_db)
            try:
                doc = build_mirror_baseline(a.recipe, a.scratch, t, decls=decls, extract=fd.load_schema_extract(a.schema_extract),
                                            with_l1_fixes=a.with_l1_fixes)
            finally:
                if t.started and not a.keep_running:
                    sr.stop_cluster(root, pg_bin=a.pg_bin)
            write_json(doc, a.out)
            _print({"result": doc["result"], "steps": {s["name"]: s["status"] for s in doc["steps"]}, "problems": doc["verification"]["problems"][:20]})
            return 0 if doc["result"] == "PASS" else 4
        decls = fd.load_declarations(a.declarations)
        if a.cmd == "expected":
            _print({"expected_assets": decls.expected_assets(), **decls.coverage_report()})
            return 0
        if a.cmd == "reader-spec":
            _print(reader_spec(decls))
            return 0
        if a.cmd == "rehearsal-fingerprints":
            expect = {"data_directory": a.data_directory, "port": urlport(a.url)} if a.policy == "disposable" else None
            log = sr.ConnectionLog()
            conn = sr.connect_checked(a.url, a.policy, log, expect=expect)
            try:
                rebuild = ({"run_id": a.rebuild_run_id, "orchestrator_commit": a.orchestrator_commit} if a.stage == "after_rebuild" else None)
                doc = rehearsal_fingerprints(conn, decls, stage=a.stage, as_of=a.as_of, commit=a.commit, rebuild=rebuild)
            finally:
                conn.close()
            write_json(doc, a.out)
            _print({"written": a.out, "units": len(doc["fingerprints"]), "connections": log.snapshot()})
            return 0
        if a.cmd == "compare":
            drill, cov = build_drill(_rd(a.production), _rd(a.rehearsal), decls, _rd(a.explained) if a.explained else None, commit=a.commit)
            write_json(drill, a.out)
            cov_path = str(a.out) + ".coverage.json"
            write_json(cov, cov_path)
            _print({"result": drill["result"], "headline": cov["headline"], "scope": drill["coverage"]["scope"], "differences": len(drill["differences"]),
                    "unexplained": drill["unexplained"], "empty_both_sides": drill["empty_both_sides"], "coverage_report": cov_path,
                    "declared": drill["coverage"]["declared"], "undeclared": sorted(cov["undeclared"]), "partial": sorted(cov["partial"]),
                    "seeded": drill["seeded"], "non_deterministic": drill["coverage"]["non_deterministic"], "groups": cov["groups"],
                    "expected_differences": cov["expected_differences_status"], "limits": cov["limits"]})
            return 0 if drill["result"] in sr.RESULTS_PASS else 4
        if a.cmd == "build-record-spec":
            _print(build_record_spec(decls))
            return 0
        if a.cmd == "status":
            _print(drill_status(decls, baseline=_rd(a.baseline) if a.baseline else None, production=_rd(a.production) if a.production else None,
                                rehearsal=_rd(a.rehearsal) if a.rehearsal else None, build_record=_rd(a.build_record) if a.build_record else None))
            return 0
        raise AssertionError(a.cmd)
    except (sr.RehearsalError, fd.DeclarationError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5


def urlport(url: str) -> int:
    from urllib.parse import urlsplit  # noqa: PLC0415
    return urlsplit(url).port or 0


if __name__ == "__main__":
    raise SystemExit(main())
