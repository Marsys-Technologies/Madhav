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
                                       [--rebuild-run-id UUID --orchestrator-commit SHA --runtime-file PATH --horizon-cutoffs PRODUCTION_FILE]   (after_rebuild: the receipt incl. runtime)
  suvarna_mirror_drill.py compare --production P --rehearsal P --commit SHA [--explained E] [--build-record B] --out PATH
  suvarna_mirror_drill.py status [--baseline P] [--production P] [--rehearsal P] [--build-record P] [--drill P] [--text-seed-check P] [--repo DIR]
                                                                                              (prints `build_record_expected`)
  suvarna_mirror_drill.py text-seed-spec | validate-text-seed-check PATH                  (the bg_texts seed check the container run exports)
  suvarna_mirror_drill.py build-record-spec
  suvarna_mirror_drill.py seed-spec | validate-seed-evidence PATH                       (the production config seed: specified, never run)
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
    "text_seed": "NEEDS_TEXT_SEED_CHECK",
    "linux": "NEEDS_LINUX_AMD64_RUNTIME",
    "decisions": "NEEDS_DECISION_REGISTER_ON_MAIN",
    "as_of": "NEEDS_AS_OF_PIN",
    "config_seed": "NEEDS_CONFIG_SEED",
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

# Declared assets that may appear in a build record as `not_run`: the closed list lives in fingerprint_declarations.NOT_RUN_ALLOWED (decision N-121),
# so the drill's coverage block, the explanation code `not_run_declared` and the build-record verifier all read the same list.
NOT_RUN_ALLOWED = fd.NOT_RUN_ALLOWED
# SS decision B1: the L0 rebuild runs inside a linux/amd64 Debian container, which brings bg_sky_calendar and bg_cohort into the proof. In that run every
# declared asset is expected `complete` EXCEPT bg_muhurta_lattice (needs the as-of pin), which stays `not_run`. bg_gochara_arcs runs now (PR #3015 is on main: the
# bg_ephemeris writer writes node_mode/epoch_convention) and is expected complete. bg_sky_calendar / bg_cohort stay on the closed list only for the case the
# container cannot run them; the validator still accepts `complete` for every listed asset and `not_run` only as listed.
CONTAINER_EXPECTED_NOT_RUN = ("bg_muhurta_lattice",)
assert set(CONTAINER_EXPECTED_NOT_RUN) <= set(NOT_RUN_ALLOWED)
# States a build-record entry may carry. `complete` and (for NOT_RUN_ALLOWED assets only) `not_run` are the only ones a DECLARED asset may have;
# every other state is a failure to be reported, never accepted as complete or as not_run.
RECORD_STATES = ("complete", "not_run", "failed", "error", "incomplete", "blocked", "skipped")

BUILD_RECORD_SPEC = {
    "flag": "--build-record PATH  (drill status; a JSON file, strict: no duplicate keys, no NaN/Infinity)",
    "schema": "suvarna-build-record/v1",
    "purpose": "lets `drill status` verify the rehearsal rebuild receipt {run_id, orchestrator_commit, runtime} of the rehearsal fingerprint file; without it the "
               "rebuild step reads CLAIMED_UNVERIFIED",
    "required_fields": {
        "schema": "the string suvarna-build-record/v1",
        "run_id": "the orchestrator run id: a canonical lower-case RFC 4122 UUID, equal to the receipt's run_id (not nil, not all-zero)",
        "state": "the string completed (the build_runs state of that run)",
        "orchestrator_commit": "40-hex commit the run's orchestrator code was at, equal to the receipt's orchestrator_commit",
        "assets": "list of entries, ONE per asset (any of the 40 L0 asset ids, no duplicate): {asset_id, state} with state complete, or "
                  "{asset_id, state: not_run, reason: NEEDS_...} (see not_run_allowed); a read-only export of the run's build_run_assets rows, "
                  "cross-checked against asset_throughput by whoever exports it",
    },
    "rules": [
        "EVERY declared asset must be present and `complete`, except an asset in not_run_allowed, which may be `not_run` with exactly the listed reason.",
        "`not_run` is accepted ONLY for the assets in the closed not_run_allowed list (decision N-121; extended only by editing NOT_RUN_ALLOWED in fingerprint_declarations.py with a decision id). On `compare --build-record`, a `not_run` entry is what makes the explanation code not_run_declared valid: that unit stays UNMEASURED, never equal, never counted toward the verdict.",
        "An asset that failed, errored, is incomplete, blocked or skipped is never accepted as `complete` or as `not_run`: it makes the record refuse, "
        "whatever the build_run_assets row says (build_run_assets.state is `complete` for terminal outcomes: see OPEN FINDINGS 4).",
        "Expected in the linux/amd64 container run (SS decision B1): 33 of the 34 declared assets `complete`, including bg_sky_calendar, bg_cohort and bg_gochara_arcs, "
        "and 1 `not_run`: bg_muhurta_lattice with NEEDS_AS_OF_PIN (see container_run_expectation). bg_sky_calendar and bg_cohort stay on the closed not_run list only "
        "for the case the container cannot run them; the validator accepts `complete` for every listed asset and `not_run` only as listed.",
        "A `reason` appears on a not_run entry only; an unknown asset id or state, a duplicate asset id or any extra key refuses the record.",
    ],
    "closed": "no other top-level key; an assets entry has exactly {asset_id, state}, plus `reason` when state is not_run",
    "shape_example": {"schema": "suvarna-build-record/v1", "run_id": "<uuid>", "state": "completed", "orchestrator_commit": "<40-hex>",
                      "assets": [{"asset_id": "bg_ephemeris", "state": "complete"},
                                 {"asset_id": "bg_sky_calendar", "state": "not_run", "reason": "NEEDS_LINUX_AMD64_RUNTIME"}]},
}

# OPEN FINDINGS of the first rehearsal run (E5.7 rehearsal run 1, STOPPED at a blocker): stated as findings, NOT fixed here, printed with every report.
OPEN_FINDINGS = (
    "1. bg_ghatana: the integrity_check_sql hash of the event-ontology table (brahma_event_ontology) matches no migration in the repository; the hash of the "
    "activity-ontology table (brahma_activity_ontology) does match one (rehearsal run 1: bg_ghatana ended in error, integrity_check_sql false).",
    "2. bg_transit_engine: its writer (the shared bg_transit_rules/bg_transit_engine writer) also wrote 69 rows to bg_transit_rules, a table that is "
    "undeclared (bg_transit_rules stays undeclared: migration-owned double_transit rows).",
    "3. bg_medical_mappings holds 21 rows although the writer's docstring says 9 graha rows.",
    "4. build_run_assets.state is 'complete' for assets whose asset_throughput.state is 'error' (integrity-check failed): build_run_assets is not evidence "
    "that an asset built correctly; the build record must be cross-checked against asset_throughput.",
    "5. The committed registry snapshot (2026-09-04) is older than later repin migrations (706 and 1077 repins), and asset_output_digest_specs is empty on a "
    "schema-only mirror, so a faithful rehearsal registry needs a production config seed (SS approved a reader seed of the L0 asset_registry rows, "
    "asset_output_digest_specs and the migration-owned rows of brahma_formula_constants, brahma_event_ontology and bg_transit_rules, after the Pravaha "
    "window; see `seed-spec`). Round 7 adds the dasha_system, dosha and yoga rows of brahma_ontology and the nirmana_bg_texts_integrity_baselines row.",
    "6. bg_ontology's stored integrity check requires COUNT(*) >= 737 in brahma_ontology while its own writer produces 414 rows (13 classes + 5 bootstrap "
    "dasha_system rows); bg_dasha_systems, bg_doshas, bg_yogas add the rest after it, so a rebuild from empty can never pass in DAG order (same class as "
    "N-99/N-105: a check must claim only its own output).",
    "7. bg_reference's md5-over-string_agg pins (reference_strength_systems, reference_glossary) depend on the OS/database collation (production: Debian glibc "
    "en_US.UTF8, x86_64, PostgreSQL 15.18; the macOS rehearsal differs); the check returns TRUE on production; the stored checks should order with COLLATE \"C\".",
    "8. ephemeris_daily speed_dps (all 9 bodies) and some Moon/Venus longitude/latitude digits differ between aarch64/Darwin and production's x86_64/Linux "
    "(float noise at the last digits; node_mode, epoch_convention, source_citation and row counts equal), which is why the rebuild is run inside a linux/amd64 "
    "Debian container (SS decision B1).",
)

# Findings that were open and are RESOLVED: stated as resolved, never as a known difference that no longer exists (printed with every report).
RESOLVED_FINDINGS = (
    "9. (resolved) bg_ephemeris writer did not write node_mode/epoch_convention; fixed by #3015, on main 2026-10-05; the drill must now show equality for "
    "ephemeris_daily. bg_gochara_arcs, which needs the Rahu/Ketu node_mode rows, runs and is expected complete.",
)


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

OUTPUT_KEYS = ("schema", "side", "stage", "definition", "declarations_sha256", "commit", "as_of", "rebuild", "tables", "fingerprints", "projections", "horizons")
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


RECEIPT_KEYS = ("run_id", "orchestrator_commit", "runtime")
RECEIPT_TEXT = ("{run_id (a real UUID: not nil, not all-zero), orchestrator_commit (40-hex), runtime {platform ('linux/amd64' for the proof), os, postgres_version, "
                "python_version, swisseph_version (text or null), collation}}")
RECEIPT_SPEC = {
    "field": "rehearsal fingerprint file -> rebuild (the rehearsal receipt), required for stage after_rebuild",
    "keys": {"run_id": "the orchestrator run id (a real UUID)", "orchestrator_commit": "40-hex",
             "runtime": "REQUIRED closed block describing where the rebuild ran: " + ", ".join(sr.RUNTIME_KEYS)},
    "runtime": {"platform": "'<os>/<arch>' lower case; linux/amd64 for the proof (SS decision B1: the rebuild runs inside a linux/amd64 Debian container)",
                "os": "text, for example 'Debian GNU/Linux 12 (bookworm)'", "postgres_version": "for example 15.18", "python_version": "for example 3.11.9",
                "swisseph_version": "text, or null when not available", "collation": "the database collation, for example C or en_US.UTF-8"},
    "rule": "a rehearsal run whose platform is not linux/amd64 reads CLAIMED_UNVERIFIED for the platform-bound units (never equal, never counted); the block is a "
            "claim written by whoever ran the rebuild, validated for shape only",
    "flag": "rehearsal-fingerprints --runtime-file PATH (a JSON object with the runtime keys; required with --stage after_rebuild)",
}


def _receipt_ok(rebuild: Any) -> bool:
    return (isinstance(rebuild, Mapping) and set(rebuild) == set(RECEIPT_KEYS) and real_uuid(rebuild["run_id"])
            and isinstance(rebuild["orchestrator_commit"], str) and bool(HEX40.fullmatch(rebuild["orchestrator_commit"]))
            and sr.runtime_problem(rebuild["runtime"]) is None)


def horizon_cutoffs_from(production: Any, decls: fd.Declarations) -> dict[str, str | None]:
    """{unit: cutoff} for `rehearsal-fingerprints --horizon-cutoffs`: the max_date of each rolling-horizon unit's block in the PRODUCTION file (N-135: the rehearsal
    overlap is cut at the production horizon). The file must validate as a production fingerprint file."""
    bad = validate_fingerprint_output(production, decls, side="production")
    if bad:
        raise MirrorError("the production file for --horizon-cutoffs is not valid: " + "; ".join(bad[:5]))
    return {u: production["horizons"][u][t["table"]]["max_date"] for u, t in decls.horizon_tables().items() if u in production["horizons"]}


def rehearsal_fingerprints(conn: Any, decls: fd.Declarations, *, stage: str, as_of: str, commit: str, units: Sequence[str] | None = None,
                           rebuild: Mapping | None = None, horizon_cutoffs: Mapping[str, Any] | None = None) -> dict:
    """The rehearsal side: per comparison unit per table {sha256, rows} + the composite, through an open connection (open it with
    `sr.connect_checked`), in a READ ONLY transaction. stage `after_rebuild` must carry `rebuild` {run_id (a real UUID), orchestrator_commit, runtime}:
    a file cannot claim a rebuild it has no receipt for (and the receipt is only SHAPE-checked until a build record verifies it, see
    `verify_rebuild_receipt`). An undeclared asset is refused by `unit_fingerprints`."""
    if stage not in ("baseline", "after_rebuild"):
        raise MirrorError("stage must be 'baseline' or 'after_rebuild'")
    if not _iso_date(as_of) or not (isinstance(commit, str) and HEX40.fullmatch(commit)):
        raise MirrorError("as_of must be YYYY-MM-DD and commit 40-hex")
    if (stage == "after_rebuild") != (rebuild is not None):
        raise MirrorError("stage after_rebuild needs a rebuild receipt, and a baseline stage must not carry one")
    if rebuild is not None and not _receipt_ok(rebuild):
        raise MirrorError("rebuild must be exactly " + RECEIPT_TEXT)
    conn.rollback()                                # the identity check left a transaction open; read_only can only be set outside one
    conn.read_only = True
    try:
        r = fd.unit_fingerprints(conn, decls, units, cursor_prefix="e57", horizon_cutoffs=horizon_cutoffs)
    finally:
        with contextlib.suppress(Exception):
            conn.rollback()
    return {"schema": OUTPUT_SCHEMA, "side": "rehearsal", "stage": stage, "definition": fd.FINGERPRINT_DEFINITION,
            "declarations_sha256": decls.sha256, "commit": commit, "as_of": as_of, "rebuild": dict(rebuild) if rebuild else None,
            "tables": r["tables"], "fingerprints": r["fingerprints"], "projections": r["projections"], "horizons": r["horizons"]}


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
            p.append("rebuild must be exactly " + RECEIPT_TEXT + ((": " + str(sr.runtime_problem(doc["rebuild"].get("runtime")))) if isinstance(doc["rebuild"], Mapping) and set(doc["rebuild"]) == set(RECEIPT_KEYS) and sr.runtime_problem(doc["rebuild"].get("runtime")) else ""))
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
    p += _projection_problems(doc["projections"], tabs, decls)
    p += _horizon_problems(doc["horizons"], tabs, decls, side)
    return p


def _horizon_problems(hz: Any, tabs: Mapping, decls: fd.Declarations, side: str) -> list[str]:
    """The `horizons` block (N-135): for each unit flagged rolling_horizon that is present, {table: horizon block} for the unit's horizon table: exactly those units,
    the declared date column, a valid closed block, rows equal to the table's rows, the overlap fingerprint tied to the table fingerprint when the overlap is the whole
    table (or empty), and on the PRODUCTION side the cutoff is the block's own max_date (so the overlap is the whole table)."""
    want = decls.horizon_tables()
    if not isinstance(hz, Mapping):
        return ["horizons must be an object (units flagged rolling_horizon -> {table: horizon block})"]
    p: list[str] = []
    present = {u for u in want if u in tabs}
    if set(hz) != present:
        p.append(f"horizons must cover exactly the units flagged rolling_horizon that are present: {sorted(present)}")
    for u in sorted(set(hz) & present):
        t, col = want[u]["table"], want[u]["date_column"]
        hu = hz[u]
        if not (isinstance(hu, Mapping) and set(hu) == {t}):
            p.append(f"{u}: horizons must hold exactly the horizon table {t}")
            continue
        b = hu[t]
        why = sr.horizon_block_problem(b)
        if why:
            p.append(f"{u}.{t}: {why}")
            continue
        if b["date_column"] != col:
            p.append(f"{u}.{t}: the horizon date_column must be the declared {col}")
        full = tabs[u].get(t) if isinstance(tabs[u], Mapping) else None
        if isinstance(full, Mapping) and isinstance(full.get("rows"), int):
            if b["rows"] != full["rows"]:
                p.append(f"{u}.{t}: the horizon block has {b['rows']} rows but the table fingerprint has {full['rows']}")
            elif b["overlap_rows"] == b["rows"] and isinstance(full.get("sha256"), str) and b["overlap_sha256"] != full["sha256"]:
                p.append(f"{u}.{t}: the overlap covers every row, so overlap_sha256 must equal the table fingerprint (same function, same rows)")
        if b["overlap_rows"] == 0 and b["overlap_sha256"] != fd.empty_table_fingerprint(decls, u, t):
            p.append(f"{u}.{t}: an empty overlap must hash to the empty-table fingerprint")
        if side == "production" and not (b["overlap_cutoff"] == b["max_date"] and b["overlap_rows"] == b["rows"]):
            p.append(f"{u}.{t}: on the production side the overlap_cutoff is the block's own max_date and the overlap is the whole table (N-135)")
    return p


def _projection_problems(projs: Any, tabs: Mapping, decls: fd.Declarations) -> list[str]:
    """The `projections` block: for each unit that carries a recorded expected difference present in `tables`, the fingerprint of its table WITHOUT the expected
    columns {table: {sha256, rows}}; exactly those units, the recorded table, rows equal to the table's rows, an empty table hashing to the empty projection."""
    want = decls.projection_tables()
    if not isinstance(projs, Mapping):
        return ["projections must be an object (units with a recorded expected difference -> {table: {sha256, rows}})"]
    p: list[str] = []
    present = {u for u in want if u in tabs}
    if set(projs) != present:
        p.append(f"projections must cover exactly the units with a recorded expected difference that are present: {sorted(present)}")
    for u in sorted(set(projs) & present):
        pu, t = projs[u], want[u]
        if not (isinstance(pu, Mapping) and set(pu) == {t}):
            p.append(f"{u}: projections must hold exactly the recorded table {t}")
            continue
        m = pu[t]
        if not (isinstance(m, Mapping) and set(m) == {"sha256", "rows"} and isinstance(m["sha256"], str) and SHA256.fullmatch(m["sha256"])
                and isinstance(m["rows"], int) and not isinstance(m["rows"], bool) and m["rows"] >= 0):
            p.append(f"{u}.{t}: a projection must be {{sha256, rows}}")
            continue
        full = tabs[u].get(t) if isinstance(tabs[u], Mapping) else None
        if isinstance(full, Mapping) and isinstance(full.get("rows"), int) and m["rows"] != full["rows"]:
            p.append(f"{u}.{t}: the projection has {m['rows']} rows but the table fingerprint has {full['rows']}: a projection ignores columns, never rows")
        empty = fd.empty_projection_fingerprint(decls, u, t)
        if (m["rows"] == 0) != (m["sha256"] == empty):
            p.append(f"{u}.{t}: the projection's row count and hash disagree (an empty table hashes to one known value, a non-empty one never does)")
    return p


def verify_rebuild_receipt(receipt: Any, record: Any, decls: fd.Declarations) -> list[str]:
    """Problems verifying a rehearsal rebuild receipt {run_id, orchestrator_commit} against an orchestrator BUILD RECORD the harness can read
    offline (`suvarna-build-record/v1`, see BUILD_RECORD_SPEC). [] = the receipt matches a completed run at the receipt's commit in which every declared
    asset is `complete`, except assets of the closed NOT_RUN_ALLOWED list, which may be `not_run` with exactly their listed NEEDS_ reason. An asset that
    failed, errored, is incomplete, blocked or skipped is never accepted as complete or as not_run. Without a record a receipt is only a claim."""
    p: list[str] = []
    if not _receipt_ok(receipt):
        return ["the receipt is not " + RECEIPT_TEXT]
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
    if not (isinstance(assets, list) and all(isinstance(x, Mapping) and {"asset_id", "state"} <= set(x) <= {"asset_id", "state", "reason"} for x in assets)):
        return p + ["the build record's assets must be a list of {asset_id, state} (plus reason on a not_run entry)"]
    known = set(decls.assets)
    by_id: dict[str, Mapping] = {}
    for x in assets:
        aid = x["asset_id"]
        if not isinstance(aid, str) or aid not in known:
            p.append(f"asset {aid!r} is not an L0 asset of the declarations")
            continue
        if aid in by_id:
            p.append(f"asset {aid} appears twice")
            continue
        by_id[aid] = x
        st = x["state"]
        if st not in RECORD_STATES:
            p.append(f"asset {aid}: state {st!r} is not one of {RECORD_STATES}")
        if "reason" in x and st != "not_run":
            p.append(f"asset {aid}: a reason belongs to a not_run entry only")
    declared = set(decls.declared_assets())
    for aid in sorted(declared):
        x = by_id.get(aid)
        if x is None:
            p.append(f"declared asset {aid} is missing from the build record")
        elif x["state"] == "complete":
            continue
        elif x["state"] == "not_run":
            allowed = NOT_RUN_ALLOWED.get(aid)
            if allowed is None:
                p.append(f"declared asset {aid} is not_run but is not in the closed not_run list {sorted(NOT_RUN_ALLOWED)}: an asset cannot become not_run")
            elif x.get("reason") != allowed["reason"]:
                p.append(f"declared asset {aid}: not_run needs the reason {allowed['reason']!r}, got {x.get('reason')!r}")
        elif x["state"] in RECORD_STATES:
            p.append(f"declared asset {aid} is {x['state']}: a failed / errored / incomplete asset is never accepted as complete or as not_run")
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
            "expected_differences": decls.expected_differences(),
            "horizons": {"rule": "N-135: a rolling-horizon difference is expected ONLY when the shared date range is shown row-for-row equal",
                         "emit": "for every unit flagged rolling_horizon (the list below), in the SAME streaming pass over the table's rows (no second read), the output "
                                 "file's `horizons` {unit: {table: block}} with the closed block {date_column, min_date, max_date, rows, overlap_cutoff, overlap_rows, "
                                 "overlap_sha256}",
                         "date": "each row's value of the unit's horizon date column as fixed-width text: a naive-UTC timestamp as YYYY-MM-DDTHH:MM:SS.ffffff "
                                 "(isoformat(timespec='microseconds')), a date as YYYY-MM-DD; min_date/max_date are the smallest/largest of them (null with 0 rows)",
                         "production_block": "overlap_cutoff = the block's own max_date, so the overlap is the whole table: overlap_rows = rows and overlap_sha256 = the "
                                             "table's own fingerprint (validated)",
                         "overlap_sha256": "nikasha_stale_certs.fingerprint_rows(<the rows with date <= overlap_cutoff>, the table's declaration): the SAME function and the "
                                           "SAME declaration as the table fingerprint (fingerprint_declarations.horizon_block)",
                         "rehearsal_block": "computed with overlap_cutoff = the PRODUCTION file's max_date (`rehearsal-fingerprints --horizon-cutoffs production_file`)",
                         "units": [{"unit": u, "table": h["table"], "date_column": h["date_column"]} for u, h in decls.horizon_tables().items()]},
            "projections": [{"unit": u, "table": t, "excluded_columns": next(e["columns"] for e in decls.expected_differences() if e["unit"] == u),
                             "how": "the SAME rows of the table's SELECT, fingerprinted with nikasha_stale_certs.fingerprint_rows under the table's declaration with these "
                                    "columns added to volatile_columns (fingerprint_declarations.Declarations.projection_declaration); written to the output file's "
                                    "`projections` {unit: {table: {sha256, rows}}}; no second read is needed"}
                            for u, t in decls.projection_tables().items()]}


# ═════════════════════════ 3b. the production CONFIG seed (specified, NOT run) ═════════════════════════

SEED_SCHEMA = "suvarna-l0-config-seed/v1"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
SEED_WRITER_IDS = (("brahma_formula_constants", "constant_id", "platform/python-sidecar/brahmagyan/l0_formula_constants.py", 10),
                   ("brahma_event_ontology", "event_class_id", "platform/python-sidecar/brahmagyan/l0_ghatana.py", 27))


def writer_owned_ids(table: str, repo_root: str | Path | None = None) -> list[str]:
    """The ids the L0 WRITER itself seeds into `table` (read from the writer source text: no import, no database): everything else in the table is
    migration-owned."""
    for t, key, rel, n in SEED_WRITER_IDS:
        if t == table:
            text = (Path(repo_root or fd.REPO_ROOT) / rel).read_text(encoding="utf-8")
            ids = re.findall(r'"%s":\s*"([^"]+)"' % key, text)
            if len(ids) != n or len(set(ids)) != n:
                raise MirrorError(f"{rel} yields {len(ids)} {key} values, expected {n}: the seed spec cannot name the writer-owned rows")
            return ids
    raise MirrorError(f"no writer-owned id list for {table}")


def seed_tables(repo_root: str | Path | None = None) -> list[dict]:
    """The closed list of tables of the config seed with the ONE read-only SELECT each. Every SELECT returns one `row_to_json(<row>)::text` per row in a
    total ORDER BY, so the evidence hash is reproducible; no column is secret (L0 configuration and reference rows, no chart or person data).
    COLLATION: every text key in an ORDER BY carries `COLLATE "C"` (byte order). Without it the sort follows the DATABASE collation: production (en_US-like,
    punctuation ignored at the first level) and the rehearsal cluster (initdb --locale=C) emit the same rows in a different order and the hash over the
    lines differs (found by the first rerun). Integer keys need no collation; `bg_transit_rules` ends with its integer `id` so the order is total."""
    fc = ", ".join(_quote_lit(i) for i in writer_owned_ids("brahma_formula_constants", repo_root))
    eo = ", ".join(_quote_lit(i) for i in writer_owned_ids("brahma_event_ontology", repo_root))
    return [
        {"table": "asset_registry", "what": "the L0 (brahmagyan) asset_registry rows: the registry as of the production state, newer than the 2026-09-04 snapshot (repins 706, 1077)",
         "select": "SELECT row_to_json(r)::text FROM asset_registry r WHERE r.layer = 'brahmagyan' ORDER BY r.asset_id COLLATE \"C\""},
        {"table": "asset_output_digest_specs", "what": "the digest specs of the L0 assets (empty on a schema-only mirror)",
         "select": "SELECT row_to_json(s)::text FROM asset_output_digest_specs s WHERE s.asset_id IN "
                   "(SELECT asset_id FROM asset_registry WHERE layer = 'brahmagyan') ORDER BY s.asset_id COLLATE \"C\", s.spec_sha256 COLLATE \"C\""},
        {"table": "brahma_formula_constants", "what": "the migration-owned rows: every constant the writer does not itself seed (the writer seeds 10 ids)",
         "select": f"SELECT row_to_json(c)::text FROM brahma_formula_constants c WHERE c.constant_id <> ALL (ARRAY[{fc}]::text[]) ORDER BY c.constant_id COLLATE \"C\""},
        {"table": "brahma_event_ontology", "what": "the migration-owned rows: every event class the writer does not itself seed (the writer seeds 27 ids)",
         "select": f"SELECT row_to_json(e)::text FROM brahma_event_ontology e WHERE e.event_class_id <> ALL (ARRAY[{eo}]::text[]) ORDER BY e.event_class_id COLLATE \"C\""},
        {"table": "bg_transit_rules", "what": "the migration-owned rows: migration 397's double_transit rows",
         "select": "SELECT row_to_json(t)::text FROM bg_transit_rules t WHERE t.rule_type = 'double_transit' ORDER BY t.graha COLLATE \"C\", t.rule_type COLLATE \"C\", t.primary_house, t.id"},
        {"table": "brahma_ontology", "what": "the dasha_system, dosha and yoga rows of brahma_ontology (332 rows in production: 20 + 79 + 233)",
         "why": "bg_dasha_systems, bg_doshas and bg_yogas each DELETE their own class and re-insert it, so these seed rows are REPLACED by the rebuild and the final "
                "group fingerprint is still writer output; the seed is only the pre-state bg_ontology's stored integrity check needs (COUNT(*) >= 737 in "
                "brahma_ontology), because bg_ontology itself writes 414 rows and runs before the three writers that add the rest (open finding 6).",
         "select": "SELECT row_to_json(c)::text FROM brahma_ontology c WHERE c.entity_class IN ('dasha_system', 'dosha', 'yoga') "
                   "ORDER BY c.entity_class COLLATE \"C\", c.canonical_id COLLATE \"C\""},
        {"table": "nirmana_bg_texts_integrity_baselines", "what": "the integrity baseline row(s) of bg_texts (one row, contract_revision bg-texts-integrity-v1)",
         "why": "a schema-only mirror has no baseline row and bg_texts' stored integrity check requires exactly one; the digests the check computes from the seeded "
                "classical_text_chunks equal the audited constants of migration 610, so the seeded baseline is verifiable rather than assumed.",
         "select": "SELECT row_to_json(b)::text FROM nirmana_bg_texts_integrity_baselines b ORDER BY b.contract_revision COLLATE \"C\""},
    ]


def seed_spec(decls: fd.Declarations, repo_root: str | Path | None = None) -> dict:
    """What the production-side reader seeds into the rehearsal mirror, exactly (specified here, NEVER run by this module): the tables, the SELECTs,
    the evidence file it must record (`suvarna-l0-config-seed/v1`) and how each hash is made. Approved by SS for after the Pravaha window."""
    tables = seed_tables(repo_root)
    core = {"schema": SEED_SCHEMA, "tables": [{"table": t["table"], "select": t["select"]} for t in tables]}
    return {
        "schema": SEED_SCHEMA, "spec_sha256": sha256_text(fd.canonical_json(core)), "role": "suvarna_reader",
        "transaction": "SET TRANSACTION READ ONLY; one SELECT per table, nothing else; no secret is read (L0 configuration / reference rows only)",
        "when": "after the Pravaha window (SS)", "tables": tables,
        "load": "the rows are loaded into the rehearsal mirror (policy rehearsal, database rehearsal_mirror) by the rehearsal side before the run; this module never connects",
        "notes": ["brahma_event_ontology: the three event-shape columns the writer does not write are migration-owned for ALL rows; this seed copies whole rows "
                  "that the writer does not own and does not patch the writer-owned rows.",
                  "bg_transit_rules: the 7 migration-owned double_transit rows only; the 69 rows the bg_transit_engine writer also writes are its own output.",
                  "brahma_ontology: only the dasha_system, dosha and yoga classes are seeded (332 rows); the other classes are bg_ontology's own output and are never seeded.",
                  "NOT seeded: the Rahu/Ketu rows of ephemeris_daily. The orchestrated bg_ephemeris writer writes node_mode/epoch_convention (PR #3015, on main 2026-10-05), "
                  "so the rebuild produces them and the drill compares them."],
        "evidence": {
            "file": "a JSON file written by the reader, validated by `validate-seed-evidence PATH`",
            "schema": SEED_SCHEMA,
            "fields": {
                "schema": SEED_SCHEMA, "spec_sha256": "this spec's spec_sha256 (binds the evidence to these exact SELECTs)", "commit": "40-hex repository commit",
                "as_of": "YYYY-MM-DD", "reader": {"role": "suvarna_reader", "read_only": True},
                "tables": {"<table>": {"select_sha256": "sha256 of that table's SELECT text", "rows": "row count (int >= 0)",
                                       "sha256": "sha256 of the SELECT's output lines joined by \\n with a trailing \\n (sha256 of the empty string for zero rows)"}},
                "asset_registry_ids": "sorted list of the asset_id values read from asset_registry (must include all 40 L0 assets)"},
            "rules": ["exactly the seven tables of this spec, no other key anywhere", "rows == 0 if and only if sha256 is the empty-output sha256",
                      "asset_registry rows == len(asset_registry_ids) and at least the number of L0 assets; the ids include every L0 asset of the declarations",
                      "select_sha256 equals the sha256 of the SELECT in this spec"]},
    }


SEED_EVIDENCE_KEYS = ("schema", "spec_sha256", "commit", "as_of", "reader", "tables", "asset_registry_ids")


def validate_seed_evidence(doc: Any, decls: fd.Declarations, repo_root: str | Path | None = None) -> list[str]:
    """Problems with a config-seed evidence file ([] = valid). Shape and consistency only: the file is written by the reader, nothing here re-reads it."""
    if not isinstance(doc, Mapping) or set(doc) != set(SEED_EVIDENCE_KEYS):
        return ["the seed evidence is not an object with exactly the closed keys"]
    p: list[str] = []
    spec = seed_spec(decls, repo_root)
    if doc["schema"] != SEED_SCHEMA:
        p.append("schema id differs")
    if doc["spec_sha256"] != spec["spec_sha256"]:
        p.append("spec_sha256 is not the sha256 of the current seed spec: the evidence was made for other SELECTs")
    if not (isinstance(doc["commit"], str) and HEX40.fullmatch(doc["commit"])):
        p.append("commit must be 40-hex")
    if not _iso_date(doc["as_of"]):
        p.append("as_of must be YYYY-MM-DD")
    if doc["reader"] != {"role": "suvarna_reader", "read_only": True}:
        p.append("reader must be exactly {role: suvarna_reader, read_only: true}")
    tabs = doc["tables"]
    want = {t["table"]: t for t in spec["tables"]}
    if not (isinstance(tabs, Mapping) and set(tabs) == set(want)):
        return p + [f"tables must be exactly {sorted(want)}"]
    for name, m in tabs.items():
        if not (isinstance(m, Mapping) and set(m) == {"select_sha256", "rows", "sha256"}):
            p.append(f"{name}: must be {{select_sha256, rows, sha256}}")
            continue
        if m["select_sha256"] != sha256_text(want[name]["select"]):
            p.append(f"{name}: select_sha256 is not the sha256 of the spec's SELECT")
        if not (isinstance(m["rows"], int) and not isinstance(m["rows"], bool) and m["rows"] >= 0):
            p.append(f"{name}: rows must be an int >= 0")
            continue
        if not (isinstance(m["sha256"], str) and SHA256.fullmatch(m["sha256"])):
            p.append(f"{name}: sha256 must be a sha256 hex")
            continue
        if (m["rows"] == 0) != (m["sha256"] == EMPTY_SHA256):
            p.append(f"{name}: rows and sha256 disagree (zero rows hash to the empty-output sha256, and only they do)")
    ids = doc["asset_registry_ids"]
    l0 = set(decls.assets)
    if not (isinstance(ids, list) and all(isinstance(x, str) for x in ids) and ids == sorted(set(ids))):
        p.append("asset_registry_ids must be a sorted list of unique asset ids")
    else:
        missing = sorted(l0 - set(ids))
        if missing:
            p.append(f"asset_registry_ids lacks L0 assets: {missing}")
        ar = tabs.get("asset_registry")
        if isinstance(ar, Mapping) and isinstance(ar.get("rows"), int) and ar["rows"] != len(ids):
            p.append("asset_registry rows differ from the number of asset_registry_ids")
        if isinstance(ar, Mapping) and isinstance(ar.get("rows"), int) and ar["rows"] < len(l0):
            p.append(f"asset_registry rows ({ar['rows']}) are fewer than the {len(l0)} L0 assets")
    return p


# ═════════════════════════ 4. compare (the existing E5.7 comparison) and status ═════════════════════════

def _rows_of(doc: Mapping, unit: str) -> dict | None:
    t = doc["tables"].get(unit)
    return {n: m["rows"] for n, m in t.items()} if t else None


def record_not_run(record: Any, decls: fd.Declarations) -> dict[str, str]:
    """{unit: NEEDS_ reason} for the comparison units whose build-record entry is `not_run` (the input of the explanation code `not_run_declared`).
    The record must already have been verified by `verify_rebuild_receipt`; only plain assets of the closed list can appear (a group is never not_run)."""
    units = decls.units()
    return {x["asset_id"]: x["reason"] for x in record["assets"] if x["state"] == "not_run" and x["asset_id"] in units and "reason" in x}


def build_drill(production: Mapping, rehearsal: Mapping, decls: fd.Declarations, explained: Mapping | None, *, commit: str,
                build_record: Any = None) -> tuple[dict, dict]:
    """Validate both sides, require the same as-of pin and an after_rebuild rehearsal, then apply `suvarna_rehearsal.compare_fingerprint_sets` over
    expected_assets = the comparison units (declared assets with tables + one unit per group), with the declarations' `coverage` block and both
    sides' row counts embedded in the drill document. `build_record` (optional, `suvarna-build-record/v1`) is verified against the rehearsal's rebuild
    receipt (`verify_rebuild_receipt`; a record that does not verify refuses the comparison) and its `not_run` entries are the only thing that makes the
    explanation code `not_run_declared` valid (decision N-121); without a record that code is always refused. Returns (drill document, coverage report).
    Raises MirrorError listing every problem."""
    problems = [f"production: {x}" for x in validate_fingerprint_output(production, decls, side="production")]
    problems += [f"rehearsal: {x}" for x in validate_fingerprint_output(rehearsal, decls, side="rehearsal")]
    if not problems:
        if rehearsal["stage"] != "after_rebuild":
            problems.append("rehearsal: the comparison needs the after_rebuild fingerprints (a baseline file proves no rebuild)")
        if production["as_of"] != rehearsal["as_of"]:
            problems.append(f"as_of differs: production {production['as_of']} vs rehearsal {rehearsal['as_of']} (pin one window)")
        if rehearsal["rebuild"] and rehearsal["rebuild"]["orchestrator_commit"] != commit:
            problems.append("the rebuild's orchestrator_commit is not the evidence commit")
        if build_record is not None:
            problems += [f"build record: {x}" for x in verify_rebuild_receipt(rehearsal["rebuild"], build_record, decls)]
    if problems:
        raise MirrorError("; ".join(problems))
    rows = {u: {"production": _rows_of(production, u), "rehearsal": _rows_of(rehearsal, u)}
            for u in sorted(set(production["tables"]) | set(rehearsal["tables"]))}
    pjs = {}
    for u, t in decls.projection_tables().items():
        if u in production["tables"] or u in rehearsal["tables"]:
            pjs[u] = {"table": t, "production": production["projections"][u][t]["sha256"] if u in production["projections"] else None,
                      "rehearsal": rehearsal["projections"][u][t]["sha256"] if u in rehearsal["projections"] else None}
    hzs = {}
    for u, ht in decls.horizon_tables().items():
        if u in production["tables"] or u in rehearsal["tables"]:
            hzs[u] = {"table": ht["table"], "production": production["horizons"][u][ht["table"]] if u in production["horizons"] else None,
                      "rehearsal": rehearsal["horizons"][u][ht["table"]] if u in rehearsal["horizons"] else None}
    drill = sr.compare_fingerprint_sets(sr.fingerprint_set(production["fingerprints"]), sr.fingerprint_set(rehearsal["fingerprints"]), explained,
                                        expected_assets=decls.expected_assets(), commit=commit, coverage=decls.drill_coverage(), rows=rows,
                                        runtime=rehearsal["rebuild"]["runtime"], projections=pjs, horizons=hzs, not_run=record_not_run(build_record, decls) if build_record is not None else None)
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
    kd = {k["unit"]: k for k in drill["known_differences"]}
    cov["known_differences"] = [dict(k) for k in drill["known_differences"]]
    cov["projections"] = {u: dict(v) for u, v in drill["projections"].items()}

    def _hint(e: Mapping) -> str:
        k = kd[e["unit"]]
        if not k["observed"]:
            return "the unit did not differ: if the referenced change has landed, remove this record"
        if k["limited_to_columns"] is False:
            return (f"NOT limited to {e['columns']}: the fingerprint without them still differs (or is not given): something else in the unit changed; "
                    "the recorded difference does not explain it")
        tail = f" KNOWN DIFFERENCE (tracked: {e['reference']}): expected, visible, never equal."
        return ("limited to " + str(e["columns"]) + ": " + ("explained." if k["explained"] else "explain it (reason code production_ahead_of_commit, an SS decision id).") + tail)
    cov["expected_differences_status"] = [{**e, "status": "observed" if kd[e["unit"]]["observed"] else "not_observed", "limited_to_columns": kd[e["unit"]]["limited_to_columns"],
                                           "explained": kd[e["unit"]]["explained"], "hint": _hint(e)} for e in decls.expected_differences()]
    cov["empty_both_sides"] = list(drill["empty_both_sides"])
    for u, st in drill["seeded"].items():
        unit_status[u] = {"status": f"seeded:{st}", "members": decls.members(u)}
    for u, tabs in drill["coverage"]["partial_ownership"].items():
        if u in unit_status and not unit_status[u]["status"].startswith("seeded:"):
            unit_status[u] = {**unit_status[u], "partial_ownership": f"partial: writer-only rows compared (whole table fingerprinted; tables {tabs})"}
    cov["partial_ownership"] = {u: list(t) for u, t in drill["coverage"]["partial_ownership"].items()}
    cov["seeded_status"] = dict(drill["seeded"])
    cov["not_run"] = dict(drill["not_run"])
    cov["runtime"] = dict(drill["runtime"])
    cov["claimed_unverified"] = list(drill["claimed_unverified"])
    for u in drill["claimed_unverified"]:                          # platform-bound, rebuilt off linux/amd64: never equal, never counted
        unit_status[u] = {"status": "CLAIMED_UNVERIFIED:platform_not_linux_amd64", "members": decls.members(u), "platform": drill["runtime"]["platform"]}
    cov["unmeasured"] = list(drill["unmeasured"])
    for u in drill["unmeasured"]:                                  # always UNMEASURED: never equal, never in the verdict's equal set, always printed
        unit_status[u] = {"status": "UNMEASURED:not_run_declared", "members": decls.members(u), "reason": drill["not_run"][u]}
    cov["as_of"] = production["as_of"]
    cov["result"] = drill["result"]
    cov["horizons"] = copy.deepcopy(drill["horizons"])
    cov["horizon_evidence"] = [{"unit": d["asset"], **d["explained"]["evidence"]} for d in drill["differences"] if d["explained"] and "evidence" in d["explained"]]
    for h in cov["horizon_evidence"]:
        unit_status[h["unit"]] = {**unit_status[h["unit"]], "horizon_evidence": h["summary"]}
    cov["headline"] = coverage_headline(drill["result"], drill["coverage"], len(decls.assets), drill["seeded"], drill["not_run"], drill["unmeasured"],
                                      drill["runtime"], drill["claimed_unverified"], [f"{h['unit']}: {h['summary']}" for h in cov["horizon_evidence"]])
    cov["limits"] = list(LIMITS_TEXT)
    cov["open_findings"] = list(OPEN_FINDINGS)
    cov["resolved_findings"] = list(RESOLVED_FINDINGS)
    cov["note"] = "undeclared assets are NOT in expected_assets: they are reported here and in the drill's coverage block, not compared"
    return drill, cov


def build_record_spec(decls: fd.Declarations) -> dict:
    """Exactly what `drill status --build-record PATH` expects (the orchestrator-side export of the rehearsal run): the path argument, the schema id,
    every required field and the declared assets that must all appear complete."""
    declared = decls.declared_assets()
    return {**copy.deepcopy(BUILD_RECORD_SPEC),
            "declared_assets_that_must_be_complete": [a for a in declared if a not in NOT_RUN_ALLOWED],
            "declared_assets_that_may_be_not_run": {a: dict(v) for a, v in sorted(NOT_RUN_ALLOWED.items()) if a in declared},
            "container_run_expectation": container_expectation(decls), "receipt_expected": copy.deepcopy(RECEIPT_SPEC)}


def container_expectation(decls: fd.Declarations) -> dict:
    """What the linux/amd64 container run is expected to produce (SS decision B1): N of the declared assets `complete`, the rest `not_run`."""
    declared = decls.declared_assets()
    not_run = {a: NOT_RUN_ALLOWED[a]["reason"] for a in CONTAINER_EXPECTED_NOT_RUN if a in declared}
    complete = [a for a in declared if a not in not_run]
    return {"decision": "SS B1: the L0 rebuild runs inside a linux/amd64 Debian container", "expected_complete": complete,
            "expected_complete_count": f"{len(complete)} of {len(declared)}", "expected_not_run": not_run,
            "note": "bg_sky_calendar and bg_cohort are EXPECTED `complete` in the container run; they stay on the closed not_run list only for the case the container "
                    "cannot run them. The validator is unchanged: `not_run` only for a listed asset with the listed reason, `complete` is accepted for every listed asset."}


def coverage_headline(result: str, cov: Mapping, assets_total: int, seeded_status: Mapping | None = None, not_run: Mapping | None = None,
                      unmeasured: Sequence[str] = (), runtime: Mapping | None = None, claimed: Sequence[str] = (), horizon_notes: Sequence[str] | None = None) -> str:
    """The one-paragraph statement printed next to the result: the numbers AND the names behind them."""
    part, seeded, nd = cov["partial"], cov["seeded"], cov["non_deterministic"]
    undeclared = sorted(cov["undeclared"])
    status = seeded_status or {}
    part_txt = "; ".join("%s (not covered: %s)" % (a, ", ".join(t)) for a, t in sorted(part.items()))
    nd_txt = ", ".join("%s %s" % (u, v) for u, v in sorted(nd.items()))
    seeded_txt = ", ".join("%s [%s]" % (u, status.get(u, "not compared")) for u in seeded)
    po = cov.get("partial_ownership", {})
    po_txt = "; ".join("%s (%s)" % (u, ", ".join(t)) for u, t in sorted(po.items()))
    bits = ["%s: %d of %d L0 assets declared (%d full, %d partial%s)" % (result, len(cov["declared"]), assets_total, len(cov["declared"]) - len(part),
                                                                       len(part), (": " + part_txt) if part else ""),
            "%d undeclared%s" % (len(undeclared), (": " + ", ".join(undeclared)) if undeclared else ""),
            "%d non-deterministic%s" % (len(nd), (": " + nd_txt) if nd else ""),
            "%d SEEDED (shown, not counted toward the verdict)%s" % (len(seeded), (": " + seeded_txt) if seeded else ""),
            "%d partial-ownership units (partial: writer-only rows compared; the whole table is fingerprinted, a difference is the expected migration_owned_rows)%s"
            % (len(po), (": " + po_txt) if po else ""),
            "%d not-run units, UNMEASURED (never equal, never counted toward the verdict; not_run_declared, N-121)%s"
            % (len(unmeasured), (": " + ", ".join("%s [%s]" % (u, (not_run or {}).get(u, "?")) for u in unmeasured)) if unmeasured else ""),
            "%d comparison units, %d in the rebuilt-equals-source claim" % (len(cov["units"]), len(cov["units"]) - len(seeded))]
    if runtime is not None:
        bits.append("rebuild runtime: %s, %s, PostgreSQL %s, Python %s, swisseph %s, collation %s" % (
            runtime["platform"], runtime["os"], runtime["postgres_version"], runtime["python_version"], runtime["swisseph_version"] or "n/a", runtime["collation"]))
        bits.append("%d platform-bound units CLAIMED_UNVERIFIED (rebuilt off %s: never equal, never counted)%s" % (
            len(claimed), sr.RUNTIME_PLATFORM, (": " + ", ".join(claimed)) if claimed else ""))
    if horizon_notes is not None:
        bits.append("%d rolling-horizon differences explained by N-135 (evidence checked: the shared date range is row-for-row equal, count and fingerprint)%s" % (
            len(horizon_notes), (": " + "; ".join(horizon_notes)) if horizon_notes else ""))
    return "; ".join(bits) + "."

def _expects_text(decls: fd.Declarations) -> str:
    ce = container_expectation(decls)
    return (f"in the linux/amd64 container run {ce['expected_complete_count']} declared assets are expected complete (bg_sky_calendar and bg_cohort among them) and "
            + ", ".join(f"{a} not_run ({r})" for a, r in sorted(ce["expected_not_run"].items()))
            + f"; not_run is accepted only for {sorted(NOT_RUN_ALLOWED)} with their NEEDS_ reason")


# ═════════════════════════ 4b. status detectors: the decision register and the bg_texts seed check ═════════════════════════

DECISION_REGISTER_PATH = "00_ARCHITECTURE/control/suvarna/state/DECISIONS.jsonl"          # NOT the cross-cutting register of another campaign
DECISION_REGISTER_ABSENT_TEXT = "decision register not on main"
MIGRATION_610_PATH = "platform/supabase/migrations/610_nirmana_bg_texts_integrity_contract.sql"
TEXT_SEED_SCHEMA = "suvarna-text-seed-check/v1"
TEXT_BASELINE_REVISION = "bg-texts-integrity-v1"
TEXT_SEED_FILE = "text_seed_check.json"
_DECISION_ID = re.compile(r"N-[0-9]{1,6}")


class CommitNotInRepo(MirrorError):
    pass


def git_read_at(repo: str | Path, commit: str, path: str) -> bytes | None:
    """The bytes of `path` as committed at `commit` (`git show <commit>:<path>`, a scrubbed environment: no user config, no prompts), or None when the commit
    exists but the path is not in it. A commit that is not in the repository raises CommitNotInRepo; a commit that is not 40-hex raises MirrorError."""
    if not (isinstance(commit, str) and HEX40.fullmatch(commit)):
        raise MirrorError("the commit under test must be 40-hex")
    env = sr._git_env()

    def run(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, timeout=60, env=env, stdin=subprocess.DEVNULL)
    try:
        if run("cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            raise CommitNotInRepo(f"commit {commit} is not in the repository")
        if run("cat-file", "-e", f"{commit}:{path}").returncode != 0:
            return None
        shown = run("show", f"{commit}:{path}")
    except (OSError, subprocess.SubprocessError) as exc:
        raise MirrorError(f"git could not be run ({type(exc).__name__})") from None
    if shown.returncode != 0:
        raise MirrorError(f"git show {commit}:{path} failed")
    return shown.stdout


DECIDED_STATE = "decided"


def parse_decision_register(raw: bytes) -> tuple[list[tuple[str, Any]], list[str]]:
    """([(id, state) in file order], problems) of a decision register in strict JSONL: one JSON object per line (no blank line, no duplicate key, no NaN), each
    with a non-empty string `id`. The register is APPEND-ONLY: an id legitimately repeats (a record that supersedes an earlier one), so a repeated id is NOT a
    problem; `register_latest` takes the latest record of each id. Ids are compared exactly (no prefix, case or whitespace folding)."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [], ["the register is not UTF-8"]
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return [], ["the register holds no record"]
    recs: list[tuple[str, Any]] = []
    probs: list[str] = []
    for n, ln in enumerate(lines, 1):
        if not ln.strip():
            probs.append(f"line {n} is empty (one JSON record per line)")
            continue
        try:
            rec = fd.strict_loads(ln)
        except fd.DeclarationError as exc:
            probs.append(f"line {n} is not strict JSON ({str(exc)[:80]})")
            continue
        if not (isinstance(rec, Mapping) and isinstance(rec.get("id"), str) and rec["id"].strip()):
            probs.append(f"line {n} is not an object with a non-empty string `id`")
            continue
        recs.append((rec["id"], rec.get("state")))
    return recs, probs


def register_latest(records: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    """{id: state of the LATEST record of that id} (later lines win: the register is append-only and a later record supersedes an earlier one)."""
    latest: dict[str, Any] = {}
    for i, st in records:
        latest[i] = st
    return latest


def cited_decisions(drill: Mapping, *, config_seed: bool = False) -> dict[str, list[str]]:
    """The closed set of decision ids a drill document cites, each with why: N-121 for the runtime block, the closed not_run list, partial-ownership units,
    SEEDED units and (when its evidence is given) the config seed; and every decision id an explanation record carries (N-135 on a rolling-horizon
    explanation, N-77 ... whatever the explanation says)."""
    out: dict[str, list[str]] = {}

    def add(i: str, why: str) -> None:
        out.setdefault(i, [])
        if why not in out[i]:
            out[i].append(why)
    cov = drill["coverage"]
    add("N-121", "the runtime block")
    if cov["not_run_allowed"]:
        add("N-121", "the closed not_run list")
    if cov["partial_ownership"]:
        add("N-121", "partial-ownership units")
    if cov["seeded"]:
        add("N-121", "SEEDED units")
    if config_seed:
        add("N-121", "the production config seed")
    for d in drill["differences"]:
        e = d.get("explained")
        if isinstance(e, Mapping) and e.get("decision"):
            add(e["decision"], f"the explanation of {d['asset']} ({e.get('reason_code')})")
    for u, e in sorted(drill["explained_input"].items()):
        if isinstance(e, Mapping) and e.get("decision"):
            add(e["decision"], f"the explanation given for {u}")
    return {k: out[k] for k in sorted(out)}


def decisions_step(decls: fd.Declarations, drill: Any, repo: str | Path, *, config_seed: bool = False) -> dict:
    """The `ss_decisions` status step. MEASURED only when the drill document validates under these declarations, every decision id it cites (`cited_decisions`)
    is the exact `id` of a record of the decision register read from the drill's own commit (`git show <commit>:DECISION_REGISTER_PATH`, strict JSONL, APPEND-ONLY:
    the LATEST record of an id wins and must have state `decided`, so a superseded id is not measured), and the register's sha256 is bound into the step. Otherwise UNMEASURED with the precise reason; never a placeholder."""
    exp = {"register": DECISION_REGISTER_PATH, "note": "the cross-cutting decision register of another campaign is not this register"}
    if drill is None:
        return {"step": "ss_decisions", "state": "UNMEASURED", "reason": "NEEDS_DRILL_DOCUMENT",
                "detail": {**exp, "expects": "--drill PATH: the drill document (`compare` output) whose decision ids and code commit are checked against the register"}}
    commit = drill.get("commit") if isinstance(drill, Mapping) else None
    probs = sr.validate_drill(drill, sr.tool_sha256_at_commit(repo, commit) if isinstance(commit, str) else None, declarations_coverage=decls.drill_coverage())
    if probs:
        return {"step": "ss_decisions", "state": "UNMEASURED", "reason": "NEEDS_VALID_DRILL", "detail": {**exp, "problems": probs[:10]}}
    cited = cited_decisions(drill, config_seed=config_seed)
    base = {**exp, "commit": commit, "cited": cited}
    try:
        raw = git_read_at(repo, commit, DECISION_REGISTER_PATH)
    except CommitNotInRepo as exc:
        return {"step": "ss_decisions", "state": "UNMEASURED", "reason": "NEEDS_COMMIT_IN_REPO", "detail": {**base, "text": str(exc)}}
    if raw is None:
        return {"step": "ss_decisions", "state": "UNMEASURED", "reason": NEEDS["decisions"],
                "detail": {**base, "text": DECISION_REGISTER_ABSENT_TEXT}}
    sha = hashlib.sha256(raw).hexdigest()
    recs, rprobs = parse_decision_register(raw)
    if rprobs:
        return {"step": "ss_decisions", "state": "UNMEASURED", "reason": "NEEDS_VALID_DECISION_REGISTER",
                "detail": {**base, "register_sha256": sha, "problems": rprobs[:10]}}
    latest = register_latest(recs)
    missing = sorted(i for i in cited if i not in latest)
    undecided = {i: latest[i] for i in sorted(cited) if i in latest and latest[i] != DECIDED_STATE}
    if missing or undecided:
        text = "; ".join([f"decision id {i} not in the register" for i in missing] + [f"decision id {i} not decided (its latest record is {st!r})" for i, st in undecided.items()])
        return {"step": "ss_decisions", "state": "UNMEASURED", "reason": "NEEDS_DECISIONS_IN_REGISTER",
                "detail": {**base, "register_sha256": sha, "records": len(recs), "missing": missing, "not_decided": undecided, "text": text}}
    return {"step": "ss_decisions", "state": "MEASURED",
            "detail": {**base, "register_sha256": sha, "records": len(recs), "latest_states": {i: latest[i] for i in sorted(cited)},
                       "note": "the latest record of every decision id the drill cites is `decided` in the register at the drill's commit (append-only: a later record wins)"}}


_TEXT_DIGEST_SQL = (
    "SELECT count(*) AS row_count, "
    "encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(text_id, chunk_id, verse_ref, chapter, verse_start, verse_end)::text, E'\\n' "
    "ORDER BY text_id COLLATE \"C\", chunk_id COLLATE \"C\"), ''), 'UTF8')), 'hex') AS identity_sha256, "
    "encode(sha256(convert_to(COALESCE(string_agg(jsonb_build_array(text_id, chunk_id, content_sa, content_en, source_citation, translator, tradition_school, "
    "content_sha256, md5(embedding::text), translation_status, translation_provenance, low_confidence_flag)::text, E'\\n' "
    "ORDER BY text_id COLLATE \"C\", chunk_id COLLATE \"C\"), ''), 'UTF8')), 'hex') AS content_sha256 "
    "FROM classical_text_chunks"
)
TEXT_SEED_SELECTS = (
    {"name": "baseline", "what": "the audited baseline row (migration 610's constants)",
     "select": f"SELECT contract_revision, identity_sha256, content_sha256, row_count FROM nirmana_bg_texts_integrity_baselines WHERE contract_revision = '{TEXT_BASELINE_REVISION}'"},
    {"name": "computed", "what": "the digests over the chunks loaded in the rehearsal database AFTER the run (the migration 610 computation, verbatim)", "select": _TEXT_DIGEST_SQL},
    {"name": "orphans", "what": "chunks whose text is not in classical_texts, after the run",
     "select": "SELECT count(*) AS orphan_chunks FROM classical_text_chunks c WHERE NOT EXISTS (SELECT 1 FROM classical_texts t WHERE t.text_id = c.text_id)"},
)
TEXT_SEED_KEYS = ("schema", "spec_sha256", "commit", "run_id", "baseline", "computed", "orphan_chunks")
_TS_BASELINE_KEYS = ("contract_revision", "identity_sha256", "content_sha256", "row_count")
_TS_COMPUTED_KEYS = ("identity_sha256", "content_sha256", "row_count")


def text_seed_spec() -> dict:
    """What the rehearsal (container) run must export as `text_seed_check.json` (`suvarna-text-seed-check/v1`), from the rehearsal database after the L0 run, and
    exactly how each value is computed. The file carries VALUES only: whether the digests equal the baseline is recomputed by `drill status`, never asserted."""
    core = {"schema": TEXT_SEED_SCHEMA, "selects": [{"name": x["name"], "select": x["select"]} for x in TEXT_SEED_SELECTS]}
    return {"schema": TEXT_SEED_SCHEMA, "spec_sha256": sha256_text(fd.canonical_json(core)), "file": TEXT_SEED_FILE, "role": "the rehearsal run, read only, on rehearsal_mirror",
            "when": "after the L0 rebuild (the orchestrator run whose id is in the file), with bg_texts complete",
            "selects": [dict(x) for x in TEXT_SEED_SELECTS],
            "fields": {"schema": TEXT_SEED_SCHEMA, "spec_sha256": "this spec's spec_sha256 (binds the file to these exact SELECTs)", "commit": "40-hex: the commit under test",
                       "run_id": "the orchestrator run id (a real UUID): equal to the rehearsal receipt's run_id",
                       "baseline": {"contract_revision": TEXT_BASELINE_REVISION, "identity_sha256": "sha256 hex", "content_sha256": "sha256 hex", "row_count": "int"},
                       "computed": {"identity_sha256": "sha256 hex", "content_sha256": "sha256 hex", "row_count": "int"},
                       "orphan_chunks": "int >= 0 (the `orphans` SELECT)"},
            "status_detector": [f"the file validates (closed keys, hashes, real UUID, spec_sha256 of this spec, contract_revision {TEXT_BASELINE_REVISION})",
                                f"the baseline values equal the audited constants READ FROM migration 610 as committed at the commit under test ({MIGRATION_610_PATH}: "
                                "audited_identity_sha256, audited_content_sha256 and the row_count CHECK)",
                                "the computed values equal the baseline values (identity, content, row_count) as recomputed by `drill status`",
                                "orphan_chunks is 0",
                                "the file's run_id is the rehearsal receipt's run_id and bg_texts is `complete` in the VERIFIED build record"],
            "without_the_file": "UNMEASURED, reason NEEDS_TEXT_SEED_CHECK; a measured inequality or an orphan reads FAIL, never MEASURED"}


def validate_text_seed_check(doc: Any) -> list[str]:
    """Problems with a text_seed_check.json (shape and internal form only; equality is the status detector's own recomputation)."""
    if not isinstance(doc, Mapping) or set(doc) != set(TEXT_SEED_KEYS):
        return ["the text seed check is not an object with exactly the closed keys"]
    p: list[str] = []
    if doc["schema"] != TEXT_SEED_SCHEMA:
        p.append("schema id differs")
    if doc["spec_sha256"] != text_seed_spec()["spec_sha256"]:
        p.append("spec_sha256 is not the sha256 of the current text-seed spec: the file was made for other SELECTs")
    if not (isinstance(doc["commit"], str) and HEX40.fullmatch(doc["commit"])):
        p.append("commit must be 40-hex")
    if not real_uuid(doc["run_id"]):
        p.append("run_id must be a real UUID")
    for key, keys in (("baseline", _TS_BASELINE_KEYS), ("computed", _TS_COMPUTED_KEYS)):
        b = doc[key]
        if not (isinstance(b, Mapping) and set(b) == set(keys)):
            p.append(f"{key} must be exactly {keys}")
            continue
        for h in ("identity_sha256", "content_sha256"):
            if not (isinstance(b[h], str) and SHA256.fullmatch(b[h])):
                p.append(f"{key}.{h} must be a sha256")
        if not (isinstance(b["row_count"], int) and not isinstance(b["row_count"], bool) and b["row_count"] >= 0):
            p.append(f"{key}.row_count must be an int >= 0")
        if key == "baseline" and b.get("contract_revision") != TEXT_BASELINE_REVISION:
            p.append(f"baseline.contract_revision must be {TEXT_BASELINE_REVISION}")
    if not (isinstance(doc["orphan_chunks"], int) and not isinstance(doc["orphan_chunks"], bool) and doc["orphan_chunks"] >= 0):
        p.append("orphan_chunks must be an int >= 0")
    return p


def migration_610_constants(raw: bytes) -> dict | None:
    """{identity_sha256, content_sha256, row_count} of the AUDITED baseline, read from the text of migration 610 (each literal must occur exactly once), or None."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    ident = re.findall(r"audited_identity_sha256 constant text :=\s*'([0-9a-f]{64})'", text)
    cont = re.findall(r"audited_content_sha256 constant text :=\s*'([0-9a-f]{64})'", text)
    cnt = re.findall(r"row_count bigint NOT NULL CHECK \(row_count = ([0-9]+)\)", text)
    if len(ident) != 1 or len(cont) != 1 or len(cnt) != 1:
        return None
    return {"identity_sha256": ident[0], "content_sha256": cont[0], "row_count": int(cnt[0])}


def text_seed_step(check: Any, repo: str | Path, *, commit: str | None = None, rehearsal: Any = None, build_record: Any = None, decls: fd.Declarations | None = None) -> dict:
    """The `text_seed` status step. MEASURED only when `text_seed_check.json` validates, its baseline equals migration 610's audited constants (read at the commit
    under test), the computed digests equal the baseline (recomputed here from the file's values), no chunk is orphaned, the file is of the rehearsal run, and
    bg_texts is `complete` in the VERIFIED build record. A measured inequality or an orphan is FAIL. No file: UNMEASURED, NEEDS_TEXT_SEED_CHECK."""
    spec = {"spec": "`text-seed-spec` prints the SELECTs and the file's fields; `validate-text-seed-check PATH` validates a file; pass it as --text-seed-check"}
    if check is None:
        return {"step": "text_seed", "state": "UNMEASURED", "reason": NEEDS["text_seed"], "detail": {**spec, "expects": f"{TEXT_SEED_FILE} produced from the rehearsal database after the run"}}
    probs = validate_text_seed_check(check)
    if probs:
        return {"step": "text_seed", "state": "UNMEASURED", "reason": NEEDS["text_seed"], "detail": {**spec, "problems": probs[:10]}}
    at = commit or check["commit"]
    if check["commit"] != at:
        return {"step": "text_seed", "state": "UNMEASURED", "reason": NEEDS["text_seed"],
                "detail": {**spec, "problems": [f"the file was made at commit {check['commit']}, not at the commit under test {at}"]}}
    try:
        raw = git_read_at(repo, at, MIGRATION_610_PATH)
    except CommitNotInRepo as exc:
        return {"step": "text_seed", "state": "UNMEASURED", "reason": "NEEDS_COMMIT_IN_REPO", "detail": {**spec, "text": str(exc)}}
    audited = migration_610_constants(raw) if raw is not None else None
    if audited is None:
        return {"step": "text_seed", "state": "UNMEASURED", "reason": "NEEDS_MIGRATION_610_AT_COMMIT",
                "detail": {**spec, "text": f"{MIGRATION_610_PATH} is not at the commit under test, or its audited constants cannot be read exactly once"}}
    detail = {"commit": at, "run_id": check["run_id"], "migration_610_sha256": hashlib.sha256(raw).hexdigest(), "audited": audited,
              "baseline": {k: check["baseline"][k] for k in _TS_COMPUTED_KEYS}, "computed": dict(check["computed"]), "orphan_chunks": check["orphan_chunks"]}
    why = []
    if {k: check["baseline"][k] for k in _TS_COMPUTED_KEYS} != audited:
        why.append("the baseline row is not the audited constants of migration 610")
    if check["computed"] != {k: check["baseline"][k] for k in _TS_COMPUTED_KEYS}:
        why.append("the digests computed over the loaded chunks differ from the baseline row")
    if check["orphan_chunks"] != 0:
        why.append(f"{check['orphan_chunks']} orphan chunk(s) after the run")
    if why:
        return {"step": "text_seed", "state": "FAIL", "detail": {**detail, "problems": why}}
    if not (isinstance(rehearsal, Mapping) and isinstance(rehearsal.get("rebuild"), Mapping) and decls is not None):
        return {"step": "text_seed", "state": "UNMEASURED", "reason": "NEEDS_REHEARSAL_RECEIPT", "detail": {**detail, "text": "the file is of no known run: pass the rehearsal file --rehearsal"}}
    if check["run_id"] != rehearsal["rebuild"].get("run_id"):
        return {"step": "text_seed", "state": "UNMEASURED", "reason": "NEEDS_TEXT_SEED_CHECK_OF_THIS_RUN",
                "detail": {**detail, "text": "the file's run_id is not the rehearsal receipt's run_id"}}
    vprobs = verify_rebuild_receipt(rehearsal["rebuild"], build_record, decls) if build_record is not None else ["no build record supplied"]
    entry = next((x for x in (build_record or {}).get("assets", []) if isinstance(x, Mapping) and x.get("asset_id") == "bg_texts"), None) if not vprobs else None
    if vprobs or not (entry and entry.get("state") == "complete"):
        return {"step": "text_seed", "state": "UNMEASURED", "reason": "NEEDS_BUILD_RECORD_BG_TEXTS",
                "detail": {**detail, "text": "bg_texts must be `complete` in a build record that verifies against the rehearsal receipt", "unverified_because": vprobs or ["bg_texts is not complete"]}}
    return {"step": "text_seed", "state": "MEASURED",
            "detail": {**detail, "note": "the baseline is migration 610's audited constants, the digests over the loaded chunks equal it (recomputed here), no orphan chunk, "
                                         "and bg_texts is complete in the verified build record of this run"}}



def drill_status(decls: fd.Declarations, *, baseline: Any = None, production: Any = None, rehearsal: Any = None, build_record: Any = None,
                seed_evidence: Any = None, drill: Any = None, text_seed_check: Any = None, repo: str | Path | None = None) -> dict:
    """Which steps are measured and which are not. A step is MEASURED only when this module recomputed it from the declarations; a file that
    merely has the right SHAPE is SHAPE_CHECKED, a rehearsal rebuild receipt without a verifying build record is CLAIMED_UNVERIFIED, and
    everything that needs an outside actor is UNMEASURED with its NEEDS_* reason. `ss_decisions` (the decision ids the `drill` document cites, each the id of a
    record of the decision register at the drill's commit) and `text_seed` (`text_seed_check.json`, the baseline and the computed digests, bg_texts complete in the
    verified build record) have real detectors. The result is therefore always UNMEASURED: this function can never say a drill is done."""
    repo = repo or fd.REPO_ROOT
    steps: list[dict] = [{"step": "declarations", "state": "MEASURED", "detail": {"declared": len(decls.declared_assets()),
                                                                                  "undeclared": len(decls.undeclared_assets()),
                                                                                  "units": len(decls.expected_assets()), "sha256": decls.sha256}}]
    bprob = validate_baseline(baseline) if baseline is not None else None
    if baseline is not None and not bprob and baseline["result"] == "PASS":
        steps.append({"step": "mirror_baseline", "state": "SHAPE_CHECKED", "detail": {"result": "PASS", "note": "the file validates; the restore was not re-run"}})
    else:
        steps.append({"step": "mirror_baseline", "state": "UNMEASURED", "reason": NEEDS["baseline"], "detail": {"problems": bprob} if bprob else {}})
    seed_p = validate_seed_evidence(seed_evidence, decls) if seed_evidence is not None else None
    if seed_evidence is not None and not seed_p:
        steps.append({"step": "config_seed", "state": "SHAPE_CHECKED", "detail": {"note": "the evidence file validates; nothing here re-read the reader's tables"}})
    else:
        steps.append({"step": "config_seed", "state": "UNMEASURED", "reason": NEEDS["config_seed"],
                      "detail": {**({"problems": seed_p} if seed_p else {}), "expects": "`seed-spec` describes the reader seed; its evidence file is validated by "
                                                                                       f"`validate-seed-evidence PATH` ({SEED_SCHEMA}); pass it as --seed-evidence"}})
    reh_p = validate_fingerprint_output(rehearsal, decls, side="rehearsal") if rehearsal is not None else None
    if rehearsal is not None and not reh_p and rehearsal["stage"] == "after_rebuild":
        rprob = verify_rebuild_receipt(rehearsal["rebuild"], build_record, decls) if build_record is not None else ["no build record supplied"]
        if not rprob:
            steps.append({"step": "rehearsal_l0_rebuild", "state": "MEASURED", "detail": {"run_id": rehearsal["rebuild"]["run_id"],
                                                                                           "verified_against": BUILD_RECORD_SCHEMA}})
        else:
            steps.append({"step": "rehearsal_l0_rebuild", "state": "CLAIMED_UNVERIFIED", "reason": NEEDS["rebuild"],
                          "detail": {"run_id": rehearsal["rebuild"]["run_id"], "unverified_because": rprob,
                                     "expects": f"--build-record PATH holding a {BUILD_RECORD_SCHEMA} (see build_record_expected): "
                                                + _expects_text(decls) + "; a failed asset is never accepted"}})
    else:
        steps.append({"step": "rehearsal_l0_rebuild", "state": "UNMEASURED", "reason": NEEDS["rebuild"],
                      "detail": {**({"problems": reh_p} if reh_p else {}),
                                 "expects": f"a rehearsal after_rebuild fingerprint file with a rebuild receipt, then --build-record PATH holding a {BUILD_RECORD_SCHEMA} "
                                            "(see build_record_expected): " + _expects_text(decls)}})
    ts_commit = drill.get("commit") if isinstance(drill, Mapping) and isinstance(drill.get("commit"), str) else None
    steps.append(text_seed_step(text_seed_check, repo, commit=ts_commit, rehearsal=rehearsal if (rehearsal is not None and not reh_p) else None, build_record=build_record, decls=decls))
    prod_p = validate_fingerprint_output(production, decls, side="production") if production is not None else None
    if production is not None and not prod_p:
        steps.append({"step": "production_fingerprints", "state": "SHAPE_CHECKED",
                      "detail": {"units": len(production["fingerprints"]), "note": "a file written by the reader: shape and consistency only, not re-read"}})
    else:
        steps.append({"step": "production_fingerprints", "state": "UNMEASURED", "reason": NEEDS["production"], "detail": {"problems": prod_p} if prod_p else {}})
    pb_units = sorted(u for u, v in decls.units().items() if "platform_bound" in v["reproducibility"])
    if rehearsal is not None and not reh_p and rehearsal["stage"] == "after_rebuild":
        rt = rehearsal["rebuild"]["runtime"]
        if rt["platform"] == sr.RUNTIME_PLATFORM:
            steps.append({"step": "linux_amd64_runtime", "state": "SHAPE_CHECKED",
                          "detail": {"runtime": rt, "units": pb_units, "note": "the receipt says the rebuild ran on linux/amd64; the block is a claim of whoever ran it, shape-checked only"}})
        else:
            steps.append({"step": "linux_amd64_runtime", "state": "CLAIMED_UNVERIFIED", "reason": NEEDS["linux"],
                          "detail": {"runtime": rt, "units": pb_units, "note": f"the rebuild ran on {rt['platform']}, not {sr.RUNTIME_PLATFORM}: the platform-bound units "
                                                                                 "are CLAIMED_UNVERIFIED, never equal"}})
    else:
        steps.append({"step": "linux_amd64_runtime", "state": "UNMEASURED", "reason": NEEDS["linux"], "detail": {"units": pb_units}})
    pinned = production is not None and rehearsal is not None and not prod_p and not reh_p and production["as_of"] == rehearsal["as_of"]
    rolling = sorted(u for u, v in decls.units().items() if "rolling_horizon" in v["reproducibility"])
    if pinned:
        steps.append({"step": "as_of_pin", "state": "SHAPE_CHECKED", "detail": {"as_of": production["as_of"], "rolling_horizon_units": rolling,
                                                                               "note": "both files carry the same date; nothing proves the window was applied"}})
    else:
        steps.append({"step": "as_of_pin", "state": "UNMEASURED", "reason": NEEDS["as_of"], "detail": {"rolling_horizon_units": rolling}})
    steps.append(decisions_step(decls, drill, repo, config_seed=seed_evidence is not None and not seed_p))
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
    rf.add_argument("--horizon-cutoffs", help="the PRODUCTION fingerprint file: the rolling-horizon units' rehearsal overlap is cut at its max_date (N-135)")
    rf.add_argument("--runtime-file", help="JSON object {platform, os, postgres_version, python_version, swisseph_version, collation}: where the rebuild ran (required with after_rebuild)")
    rf.add_argument("--out", required=True)
    rf.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    c = sub.add_parser("compare")
    c.add_argument("--production", required=True)
    c.add_argument("--rehearsal", required=True)
    c.add_argument("--commit", required=True)
    c.add_argument("--explained")
    c.add_argument("--build-record", help="the verified build record: its not_run entries are what makes the explanation code not_run_declared valid")
    c.add_argument("--out", required=True)
    c.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    ss_ = sub.add_parser("seed-spec")
    ss_.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    vs = sub.add_parser("validate-seed-evidence")
    vs.add_argument("path")
    vs.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    br = sub.add_parser("build-record-spec")
    br.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    st = sub.add_parser("status")
    st.add_argument("--baseline")
    st.add_argument("--production")
    st.add_argument("--rehearsal")
    st.add_argument("--build-record")
    st.add_argument("--seed-evidence")
    st.add_argument("--drill", help="the drill document (`compare` output): its decision ids are checked against the decision register at its commit")
    st.add_argument("--text-seed-check", help="text_seed_check.json from the rehearsal run (see text-seed-spec)")
    st.add_argument("--repo", default=str(fd.REPO_ROOT), help="the repository the commit under test is read from")
    ts = sub.add_parser("text-seed-spec")
    ts.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    vt = sub.add_parser("validate-text-seed-check")
    vt.add_argument("path")
    vt.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
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
                rebuild = ({"run_id": a.rebuild_run_id, "orchestrator_commit": a.orchestrator_commit,
                            "runtime": _rd(a.runtime_file) if a.runtime_file else None} if a.stage == "after_rebuild" else None)
                doc = rehearsal_fingerprints(conn, decls, stage=a.stage, as_of=a.as_of, commit=a.commit, rebuild=rebuild,
                                             horizon_cutoffs=horizon_cutoffs_from(_rd(a.horizon_cutoffs), decls) if a.horizon_cutoffs else None)
            finally:
                conn.close()
            write_json(doc, a.out)
            _print({"written": a.out, "units": len(doc["fingerprints"]), "connections": log.snapshot()})
            return 0
        if a.cmd == "compare":
            drill, cov = build_drill(_rd(a.production), _rd(a.rehearsal), decls, _rd(a.explained) if a.explained else None, commit=a.commit,
                                     build_record=_rd(a.build_record) if a.build_record else None)
            write_json(drill, a.out)
            cov_path = str(a.out) + ".coverage.json"
            write_json(cov, cov_path)
            _print({"result": drill["result"], "headline": cov["headline"], "scope": drill["coverage"]["scope"], "differences": len(drill["differences"]),
                    "unexplained": drill["unexplained"], "empty_both_sides": drill["empty_both_sides"], "coverage_report": cov_path,
                    "declared": drill["coverage"]["declared"], "undeclared": sorted(cov["undeclared"]), "partial": sorted(cov["partial"]),
                    "seeded": drill["seeded"], "unmeasured": drill["unmeasured"], "not_run": drill["not_run"],
                    "non_deterministic": drill["coverage"]["non_deterministic"], "groups": cov["groups"],
                    "partial_ownership": cov["partial_ownership"], "expected_differences": cov["expected_differences_status"], "limits": cov["limits"],
                    "open_findings": cov["open_findings"], "resolved_findings": cov["resolved_findings"], "known_differences": cov["known_differences"]})
            return 0 if drill["result"] in sr.RESULTS_PASS else 4
        if a.cmd == "text-seed-spec":
            _print(text_seed_spec())
            return 0
        if a.cmd == "validate-text-seed-check":
            try:
                doc = _rd(a.path)
            except (OSError, ValueError, fd.DeclarationError) as exc:
                _print({"valid": False, "problems": [f"unreadable text seed check ({type(exc).__name__})"]})
                return 2
            problems = validate_text_seed_check(doc)
            _print({"valid": not problems, "problems": problems})
            return 0 if not problems else 2
        if a.cmd == "seed-spec":
            _print(seed_spec(decls))
            return 0
        if a.cmd == "validate-seed-evidence":
            try:
                doc = _rd(a.path)
            except (OSError, ValueError, fd.DeclarationError) as exc:
                _print({"valid": False, "problems": [f"unreadable seed evidence ({type(exc).__name__})"]})
                return 2
            probs = validate_seed_evidence(doc, decls)
            _print({"valid": not probs, "problems": probs})
            return 0 if not probs else 2
        if a.cmd == "build-record-spec":
            _print(build_record_spec(decls))
            return 0
        if a.cmd == "status":
            _print(drill_status(decls, baseline=_rd(a.baseline) if a.baseline else None, production=_rd(a.production) if a.production else None,
                                rehearsal=_rd(a.rehearsal) if a.rehearsal else None, build_record=_rd(a.build_record) if a.build_record else None,
                                seed_evidence=_rd(a.seed_evidence) if a.seed_evidence else None, drill=_rd(a.drill) if a.drill else None,
                                text_seed_check=_rd(a.text_seed_check) if a.text_seed_check else None, repo=a.repo))
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
