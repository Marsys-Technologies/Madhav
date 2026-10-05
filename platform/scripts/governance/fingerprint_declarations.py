#!/usr/bin/env python3
"""fingerprint_declarations.py -- Suvarna E5.7: the per-asset semantic-fingerprint DECLARATIONS for the 40 active L0 assets.

Data file: `00_ARCHITECTURE/control/FINGERPRINT_DECLARATIONS.json`. Design: /Users/Dev/suvarna-evidence/E5.7/DESIGN.md (N-116 "build it").
This module is the ONE place that knows the file's shape. It is a stdlib module (the E5.5 fingerprint it points at is imported lazily, only
when a fingerprint is actually computed or a declaration is converted). Imported by `suvarna_rehearsal.py` (E5.7 comparison) and
`suvarna_mirror_drill.py`; usable by anything else that needs "which tables does L0 asset X own and how are they fingerprinted".

WHAT A DECLARATION IS. For each of the 40 active L0 assets (the registry snapshot is the list) either
  * `declared`   : tables[] (name, key columns, exclude columns each with a reason, naive_utc_columns, write evidence), plus
                   `coverage` full|partial (partial lists `not_covered_tables`), `reproducibility`, scope `global`, and the fingerprint
                   definition `nikasha_stale_certs.table_fingerprint/1`; an asset may also be a member of a GROUP (below); or
  * `undeclared` : reason_code + reason + tables_written (B.10: a fingerprint that cannot be honestly declared from the code is listed with
                   the reason, never invented, never silently dropped).
Each declared table maps 1:1 onto an E5.5 declaration in VOLATILE mode (`volatile_columns` = the excluded columns), so a column added to
the schema later enters the fingerprint automatically. `Declarations.table_declaration()` returns that dict after running it through
`nikasha_stale_certs.validate_declaration`: E5.5 refuses what it refuses; this module defines no second fingerprint.
ASSET FINGERPRINT: one table -> its table fingerprint; several -> sha256 of canonical JSON {"definition", "tables": {table: sha256}}.
GROUPS (SS decision, round 2). A table written by several assets (brahma_ontology, brahma_class_priors, classical_text_chunks) is declared ONCE,
in the top-level `groups` section: group id, its tables (same shape as an asset's), the member assets and each member's write evidence. The
drill compares a group as ONE unit `grp_<group id>` and reports every member with it; a table claimed by two assets is refused except
through such a group. COMPARISON UNITS = every declared asset that has its own tables + every group (`Declarations.units()`).

VALIDATION (`validate`, `load_declarations`) is closed-schema and checks the file against (a) the registry snapshot (asset set) and (b) a
schema extract derived offline from the mirror's schema-only dump (tables, columns, nullability, PK/UNIQUE constraints, identity/serial
defaults, column types, the list of all tables), (c) the writer files named as evidence (tracked in git, repo-relative, the cited statement
must name the table and a write verb), and (d) the registry's own table list (`count_sql`). Machine checks on exclusions: `not_written_by_writer`
needs an INSERT column list in the evidence that lacks the column; `wall_clock_timestamp` on an unusual name needs now()/CURRENT_TIMESTAMP in the
statement; a table whose non-key columns are ALL excluded is refused; `coverage: full` needs every table the writer evidence writes (and every
registry count_sql table) to be listed.

CLI:
  fingerprint_declarations.py validate  [--declarations P] [--registry P] [--schema-extract P] [--repo-root P]
  fingerprint_declarations.py summary   [--declarations P]                        (declared / partial / undeclared + reasons, JSON)
  fingerprint_declarations.py extract-schema --dump prod_schema.sql [--declarations P] --out extract.json   (offline; reads the dump text only)
Exit: 0 ok · 2 refused / invalid · 5 error.
"""
from __future__ import annotations

import argparse
import datetime as dt
import functools
import hashlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
DEFAULT_DECLARATIONS = REPO_ROOT / "00_ARCHITECTURE" / "control" / "FINGERPRINT_DECLARATIONS.json"
DEFAULT_SCHEMA_EXTRACT = REPO_ROOT / "00_ARCHITECTURE" / "control" / "FINGERPRINT_SCHEMA_EXTRACT_L0.json"
DEFAULT_REGISTRY = REPO_ROOT / "00_ARCHITECTURE" / "briefs" / "nirmana" / "L0_ASSET_REGISTRY_SNAPSHOT_2026-09-04.json"

SCHEMA_ID = "suvarna-fingerprint-declarations/v1"
EXTRACT_SCHEMA_ID = "suvarna-l0-schema-extract/v1"
FINGERPRINT_DEFINITION = "nikasha_stale_certs.table_fingerprint/1"     # E5.5's definition: pinned equal to suvarna_rehearsal's by a test
LAYER = "L0"
SCOPE = "global"
EXCLUDE_REASON_CODES = ("surrogate_identity", "wall_clock_timestamp", "build_identity", "not_written_by_writer")
WALL_CLOCK_NAMES = ("created_at", "updated_at", "computed_at", "inserted_at", "built_at")
UNDECLARED_CODES = ("no_table", "shared_table", "migration_owned_rows", "no_plain_natural_key", "second_writer_unprobed")
GROUP_PREFIX = "grp_"
# Declared assets that may appear in a build record as `not_run` (legitimately unrunnable in the rehearsal), each with the NEEDS_ reason the record
# must carry. CLOSED: an asset cannot become `not_run` because it failed; extending this list needs an edit here AND a decision id (SS, N-<n>).
# Decision N-121 covers PASS_DECLARED_ONLY with coverage, this closed list, partial-ownership units, SEEDED units and the production config seed.
NOT_RUN_ALLOWED = {
    "bg_sky_calendar": {"reason": "NEEDS_LINUX_AMD64_RUNTIME", "decision": "N-121"},
    "bg_cohort": {"reason": "NEEDS_LINUX_AMD64_RUNTIME", "decision": "N-121"},
    "bg_muhurta_lattice": {"reason": "NEEDS_AS_OF_PIN", "decision": "N-121"},
    "bg_gochara_arcs": {"reason": "NEEDS_PR_3015", "decision": "N-121",
                        "note": "SS option (c), 2026-10-04: the bg_ephemeris writer on main does not write node_mode/epoch_convention for Rahu/Ketu, so bg_gochara_arcs "
                                "cannot run (its reader needs node_mode = 'true' rows); #3015 is blocked on the L0 writer-inventory re-pin. not_run ONLY while #3015 is not on "
                                "main (`complete` stays accepted); its unit is UNMEASURED via not_run_declared, never counted."},
}
EVIDENCE_WINDOW = 30                                  # lines of the cited statement that are read
REPRODUCIBILITY = ("deterministic", "rolling_horizon", "platform_bound")
COVERAGE = ("full", "partial")
MIN_REASON_CHARS = 20
MIN_UNDECLARED_REASON_CHARS = 60
TIMESTAMP_NAIVE = "timestamp without time zone"

TOP_KEYS = ("schema", "fingerprint_definition", "layer", "scope", "source", "groups", "assets")
GROUP_KEYS = ("tables", "members", "reproducibility", "seeded", "notes")
GROUP_REQUIRED = ("tables", "members", "reproducibility", "seeded")
SOURCE_KEYS = ("registry_snapshot", "registry_snapshot_sha256", "schema_dump", "schema_dump_sha256", "code_commit")
DECLARED_KEYS = ("status", "fingerprint_definition", "scope", "coverage", "reproducibility", "groups", "tables", "not_covered_tables",
                 "not_written_tables", "notes")
DECLARED_REQUIRED = ("status", "fingerprint_definition", "scope", "coverage", "reproducibility", "groups", "tables", "not_covered_tables")
UNDECLARED_KEYS = ("status", "reason_code", "reason", "tables_written", "evidence")
TABLE_KEYS = ("name", "scope", "key", "key_evidence", "exclude", "naive_utc_columns", "write_evidence", "embedding", "ownership_evidence",
              "expected_difference", "partial_ownership", "horizon_date_column", "notes")
PARTIAL_OWNERSHIP_KEYS = ("reason_code", "detail", "evidence")
PARTIAL_OWNERSHIP_CODE = "migration_owned_rows"
TABLE_REQUIRED = ("name", "scope", "key", "key_evidence", "exclude", "naive_utc_columns", "write_evidence")
EXCLUDE_KEYS = ("column", "reason_code", "reason")
NOTCOV_KEYS = ("name", "reason", "evidence")
EMBEDDING_KEYS = ("column", "source_columns", "model_id")
EXPECTED_DIFF_KEYS = ("columns", "reference", "detail", "until")
HORIZON_TYPES = ("date", TIMESTAMP_NAIVE)                  # the type of a rolling-horizon table's horizon_date_column (N-135)
HORIZON_BLOCK_KEYS = ("date_column", "min_date", "max_date", "rows", "overlap_cutoff", "overlap_rows", "overlap_sha256")

_IDENT = re.compile(r"[a-z_][a-z0-9_]{0,62}")
_ASSET = re.compile(r"[a-z][a-z0-9_]*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_EVIDENCE = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./-]*):([1-9][0-9]*)")
_WRITE_VERB = re.compile(r"\b(?:INSERT|UPDATE|DELETE|COPY|TRUNCATE|UPSERT)\b|\.execute(?:many)?\(", re.I)
_WRITE_STMT = re.compile(r"\b(?:INSERT\s+INTO|DELETE\s+FROM|TRUNCATE(?:\s+TABLE)?|COPY|UPDATE)\s+(?:public\.)?([a-z_][a-z0-9_]*)\b", re.I)
_CLOCK = re.compile(r"\bnow\(\)|\bCURRENT_TIMESTAMP\b|\bdatetime\.now\(|\butcnow\(", re.I)


class DeclarationError(ValueError):
    """The declarations file (or the extract it is checked against) is refused. `.problems` is the full list of (code, path, message)."""

    def __init__(self, problems: Sequence[tuple[str, str, str]]):
        self.problems = list(problems)
        head = "; ".join(f"{c} at {p}: {m}" for c, p, m in self.problems[:6])
        super().__init__(f"{len(self.problems)} problem(s): {head}" + (" ..." if len(self.problems) > 6 else ""))

    @property
    def codes(self) -> list[str]:
        return [c for c, _p, _m in self.problems]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(path: str | Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


# ───────────────────────── strict JSON (duplicate keys are refused) ─────────────────────────

def _no_dup_pairs(pairs: list[tuple[str, Any]]) -> dict:
    out: dict = {}
    for k, v in pairs:
        if k in out:
            raise DeclarationError([("duplicate_json_key", "$", f"object key {k!r} occurs twice")])
        out[k] = v
    return out


def strict_loads(text: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=_no_dup_pairs, parse_constant=_refuse_constant)
    except DeclarationError:
        raise
    except ValueError as exc:
        raise DeclarationError([("bad_json", "$", f"not valid JSON: {exc}")]) from None


def _refuse_constant(name: str) -> Any:
    raise ValueError(f"non-standard constant {name}")


# ───────────────────────── registry snapshot (the asset list) ─────────────────────────

def load_registry(path: str | Path = DEFAULT_REGISTRY) -> dict[str, dict]:
    """{asset_id: {target_table, asset_kind, scope, count_tables}} for the ACTIVE rows of the registry snapshot (the 40 L0 assets);
    `count_tables` are the tables named by the row's count_sql (what the registry itself says the asset produces)."""
    try:
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DeclarationError([("registry_unreadable", str(path), f"{type(exc).__name__}")]) from None
    if not isinstance(rows, list):
        raise DeclarationError([("registry_unreadable", str(path), "the registry snapshot is not a list")])
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, Mapping) and r.get("is_active") is True and isinstance(r.get("asset_id"), str):
            cs = r.get("count_sql") if isinstance(r.get("count_sql"), str) else ""
            out[r["asset_id"]] = {"target_table": r.get("target_table"), "asset_kind": r.get("asset_kind"), "scope": r.get("scope"),
                                  "count_tables": sorted(set(re.findall(r"\b(?:FROM|JOIN)\s+(?:public\.)?([a-z_][a-z0-9_]*)", cs, re.I)))}
    return out


# ───────────────────────── schema extract (derived offline from the schema-only dump) ─────────────────────────

_CREATE = re.compile(r"^CREATE TABLE public\.([a-z0-9_]+) \(\n(.*?)\n\);\n", re.M | re.S)
_COL_SPLIT = re.compile(r" (DEFAULT|NOT NULL|GENERATED|COLLATE|CONSTRAINT) ")
_ALTER_CONSTRAINT = re.compile(r"^ALTER TABLE ONLY public\.([a-z0-9_]+)\n    ADD CONSTRAINT ([a-z0-9_]+) (PRIMARY KEY|UNIQUE) \(([^)]*)\)", re.M)
_ALTER_IDENTITY = re.compile(r"^ALTER TABLE public\.([a-z0-9_]+) ALTER COLUMN ([a-z0-9_]+) ADD GENERATED (?:ALWAYS|BY DEFAULT) AS IDENTITY", re.M)
_ALTER_NEXTVAL = re.compile(r"^ALTER TABLE ONLY public\.([a-z0-9_]+) ALTER COLUMN ([a-z0-9_]+) SET DEFAULT nextval\(", re.M)
_UNIQUE_INDEX = re.compile(r"^CREATE UNIQUE INDEX ([a-z0-9_]+) ON public\.([a-z0-9_]+) USING btree \((.*?)\)( NULLS NOT DISTINCT)?( WHERE .*)?;$", re.M)


def dump_table_names(dump_text: str) -> set[str]:
    return {m.group(1) for m in _CREATE.finditer(dump_text)}


def dump_table_body(dump_text: str, table: str) -> str | None:
    for m in _CREATE.finditer(dump_text):
        if m.group(1) == table:
            return m.group(2)
    return None


def _column_line(line: str) -> tuple[str, dict] | None:
    s = line.strip().rstrip(",")
    if not s or s.startswith("CONSTRAINT "):
        return None
    m = re.match(r'("?[A-Za-z_][A-Za-z0-9_]*"?) (.+)$', s)
    if not m:
        return None                                   # a continuation line of a multi-line generated expression
    name, rest = m.group(1).strip('"'), m.group(2)
    padded = rest + " "
    sp = _COL_SPLIT.search(padded)
    typ = (padded[: sp.start()] if sp else padded).strip()
    dm = re.search(r" DEFAULT (.+?)(?: NOT NULL)? $", padded)
    default = dm.group(1).strip() if dm and "GENERATED ALWAYS" not in padded else None
    return name, {"type": typ, "not_null": " NOT NULL " in padded, "default": default,
                  "generated": "GENERATED ALWAYS AS (" in padded, "identity": bool(default and ("gen_random_uuid()" in default))}


def extract_schema(dump_text: str, tables: Sequence[str], *, dump_name: str = "prod_schema.sql") -> dict:
    """The schema facts the declarations are validated against, for `tables` only, from the schema-only dump TEXT (no database, no data)."""
    wanted = sorted(set(tables))
    bodies = {m.group(1): m.group(2) for m in _CREATE.finditer(dump_text)}
    out: dict[str, dict] = {}
    for t in wanted:
        if t not in bodies:
            raise DeclarationError([("unknown_table", t, "no `CREATE TABLE public.<name>` in the dump")])
        cols: dict[str, dict] = {}
        for ln in bodies[t].split("\n"):
            parsed = _column_line(ln)
            if parsed:
                cols[parsed[0]] = parsed[1]
        out[t] = {"columns": cols, "primary_key": None, "primary_key_name": None, "unique": [], "unique_other": []}
    for m in _ALTER_IDENTITY.finditer(dump_text):
        t, c = m.groups()
        if t in out and c in out[t]["columns"]:
            out[t]["columns"][c]["identity"] = True
    for m in _ALTER_NEXTVAL.finditer(dump_text):
        t, c = m.groups()
        if t in out and c in out[t]["columns"]:
            out[t]["columns"][c]["identity"] = True
    for m in _ALTER_CONSTRAINT.finditer(dump_text):
        t, name, kind, cols_s = m.groups()
        if t not in out:
            continue
        cols = [x.strip() for x in cols_s.split(",")]
        if kind == "PRIMARY KEY":
            out[t]["primary_key"], out[t]["primary_key_name"] = cols, name
        else:
            out[t]["unique"].append({"name": name, "columns": cols})
    for m in _UNIQUE_INDEX.finditer(dump_text):
        name, t, cols_s, _nnd, where = m.groups()
        if t not in out:
            continue
        parts = [x.strip() for x in cols_s.split(",")]
        if where is None and all(_IDENT.fullmatch(x) for x in parts):
            out[t]["unique"].append({"name": name, "columns": parts})
        else:
            out[t]["unique_other"].append({"name": name, "definition": cols_s + (where or "")})
    for t in out:
        out[t]["unique"].sort(key=lambda u: u["name"])
        out[t]["unique_other"].sort(key=lambda u: u["name"])
    return {"schema": EXTRACT_SCHEMA_ID, "source": {"file": dump_name, "sha256": sha256_bytes(dump_text.encode("utf-8"))},
            "table_names": sorted(bodies), "tables": out}


def load_schema_extract(path: str | Path = DEFAULT_SCHEMA_EXTRACT) -> dict:
    try:
        doc = strict_loads(Path(path).read_text(encoding="utf-8"))               # duplicate keys / NaN / Infinity are refused
    except (OSError, DeclarationError) as exc:
        raise DeclarationError([("schema_extract_unreadable", str(path), type(exc).__name__)]) from None
    if not (isinstance(doc, Mapping) and doc.get("schema") == EXTRACT_SCHEMA_ID and isinstance(doc.get("tables"), Mapping)
            and isinstance(doc.get("table_names"), list)):
        raise DeclarationError([("schema_extract_unreadable", str(path), "not a suvarna-l0-schema-extract/v1 document")])
    return dict(doc)


def tables_named(doc: Mapping) -> set[str]:
    """Every table name the declarations mention (declared, group, not covered, not written, undeclared `tables_written`). Tolerant of a
    malformed document."""
    out: set[str] = set()
    if not isinstance(doc, Mapping):
        return out
    groups = doc.get("groups")
    for g in (groups.values() if isinstance(groups, Mapping) else []):
        for t in (g.get("tables") or []) if isinstance(g, Mapping) else []:
            if isinstance(t, Mapping) and isinstance(t.get("name"), str):
                out.add(t["name"])
    assets = doc.get("assets")
    if not isinstance(assets, Mapping):
        return out
    for a in assets.values():
        if not isinstance(a, Mapping):
            continue
        for key in ("tables", "not_covered_tables", "not_written_tables"):
            for t in a.get(key) or []:
                if isinstance(t, Mapping) and isinstance(t.get("name"), str):
                    out.add(t["name"])
        for t in a.get("tables_written") or []:
            if isinstance(t, str):
                out.add(t)
    return out


# ───────────────────────── validation ─────────────────────────

Problem = tuple[str, str, str]


def _closed(obj: Any, allowed: Sequence[str], required: Sequence[str], path: str, probs: list[Problem]) -> bool:
    if not isinstance(obj, Mapping):
        probs.append(("bad_shape", path, "expected an object"))
        return False
    for k in sorted(set(obj) - set(allowed)):
        probs.append(("unknown_key", f"{path}.{k}", "key is not part of the closed schema"))
    for k in required:
        if k not in obj:
            probs.append(("missing_key", f"{path}.{k}", "required key is absent"))
    return not (set(obj) - set(allowed)) and all(k in obj for k in required)


# ── evidence: repo-relative, tracked, and the cited STATEMENT must say what is claimed ──

@dataclass(frozen=True)
class _Ctx:
    root: str
    tracked: frozenset | None            # None: git could not answer (not a checkout): the tracked-set check is skipped


@functools.lru_cache(maxsize=1024)
def _file_lines(root: str, rel: str) -> tuple | None:
    try:
        return tuple(Path(root, rel).read_text(encoding="utf-8", errors="replace").split("\n"))
    except OSError:
        return None


@functools.lru_cache(maxsize=64)
def _tracked_paths(root: str, paths: tuple) -> frozenset | None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        p = subprocess.run(["git", "-C", root, "ls-files", "-z", "--", *paths], capture_output=True, timeout=60, env=env, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return frozenset(x.decode("utf-8", "replace") for x in p.stdout.split(b"\0") if x)


def _evidence_paths(doc: Any) -> list[str]:
    """Every `path` of a `path:line` evidence string in the document (tolerant of a malformed one), for ONE `git ls-files` call."""
    out: set[str] = set()

    def add(v: Any) -> None:
        if isinstance(v, str) and _EVIDENCE.fullmatch(v):
            out.add(v.rsplit(":", 1)[0])

    def walk(x: Any) -> None:
        if isinstance(x, Mapping):
            for k, v in x.items():
                if k in ("write_evidence", "ownership_evidence", "evidence") and isinstance(v, list):
                    for e in v:
                        add(e)
                elif k == "members" and isinstance(v, Mapping):
                    for e in v.values():
                        for ee in (e if isinstance(e, list) else []):
                            add(ee)
                walk(v)
        elif isinstance(x, list):
            for y in x:
                walk(y)
    walk(doc)
    return sorted(out)


def _window(lines: Sequence[str], line: int) -> str:
    return "\n".join(lines[line - 1: line - 1 + EVIDENCE_WINDOW])


def _mentions(window: str, name: str, lines: Sequence[str]) -> bool:
    """The statement names the table: literally, or through a `{CONST}` placeholder that the file defines as `CONST = "<table>"`."""
    if re.search(rf"\b{re.escape(name)}\b", window):
        return True
    for const in re.findall(r"\{([A-Za-z_][A-Za-z0-9_]*)\}", window):
        for ln in lines:
            m = re.match(rf"\s*{re.escape(const)}\s*=\s*[\"']([a-z_][a-z0-9_]*)[\"']", ln)
            if m and m.group(1) == name:
                return True
    return False


def _check_evidence(ev: Any, tables: Sequence[str] | None, path: str, probs: list[Problem], ctx: _Ctx | None, *, write: bool = False) -> None:
    """`tables`: the cited statement must name one of them (None: no table is required). `write`: it must also hold a write verb."""
    if not isinstance(ev, str) or not _EVIDENCE.fullmatch(ev):
        probs.append(("evidence_bad", path, "evidence must be `relative/path:line`"))
        return
    rel, line = ev.rsplit(":", 1)
    parts = rel.split("/")
    if rel.startswith("/") or ".." in parts or "." in parts or "" in parts:
        probs.append(("evidence_bad", path, "evidence path must be repo-relative, with no `..`, `.` or empty segment"))
        return
    if ctx is None:
        return
    if ctx.tracked is not None and rel not in ctx.tracked:
        probs.append(("evidence_untracked", path, f"{rel} is not a file tracked in the repository"))
        return
    lines = _file_lines(ctx.root, rel)
    if lines is None:
        probs.append(("evidence_missing", path, f"{rel} does not exist in the repository"))
        return
    if int(line) > len(lines):
        probs.append(("evidence_missing", path, f"{rel} has no line {line}"))
        return
    win = _window(lines, int(line))
    if tables and not any(_mentions(win, t, lines) for t in tables):
        probs.append(("evidence_missing", path, f"the statement at {rel}:{line} never names table {' / '.join(tables)}"))
    elif write and not _WRITE_VERB.search(win):
        probs.append(("evidence_not_a_write", path, f"the statement at {rel}:{line} holds no write verb (INSERT/UPDATE/DELETE/COPY/execute)"))


def _insert_columns(window: str, table: str) -> list[str] | None:
    m = re.search(rf"INSERT\s+INTO\s+(?:public\.)?(?:{re.escape(table)}|\{{[A-Za-z_]+\}})\s*\(([^)]*)\)", window, re.I | re.S)
    if not m:
        return None
    return [c.strip().strip('"').lower() for c in m.group(1).split(",") if c.strip()]


def _windows_of(evs: Any, ctx: _Ctx | None) -> list[str]:
    out = []
    if ctx is None or not isinstance(evs, list):
        return out
    for ev in evs:
        if isinstance(ev, str) and _EVIDENCE.fullmatch(ev):
            rel, line = ev.rsplit(":", 1)
            lines = _file_lines(ctx.root, rel)
            if lines is not None and int(line) <= len(lines) and ".." not in rel.split("/"):
                out.append(_window(lines, int(line)))
    return out


def _validate_table(t: Any, owner: str, path: str, schema: Mapping | None, probs: list[Problem], ctx: _Ctx | None) -> None:
    if not _closed(t, TABLE_KEYS, TABLE_REQUIRED, path, probs):
        return
    name = t["name"]
    if not (isinstance(name, str) and _IDENT.fullmatch(name)):
        probs.append(("bad_table_name", path, f"{name!r} is not a lower-case identifier"))
        return
    if t["scope"] != SCOPE:
        probs.append(("bad_scope", path, f"table scope must be {SCOPE!r} (L0 is global: no chart scoping)"))
    key, excl, naive = t["key"], t["exclude"], t["naive_utc_columns"]
    if not (isinstance(key, list) and key and all(isinstance(c, str) and _IDENT.fullmatch(c) for c in key)):
        probs.append(("bad_key", path, "key must be a non-empty list of identifiers"))
        return
    if len(set(key)) != len(key):
        probs.append(("key_duplicate_column", path, f"key lists a column twice: {key}"))
    if not (isinstance(naive, list) and all(isinstance(c, str) and _IDENT.fullmatch(c) for c in naive) and len(set(naive)) == len(naive)):
        probs.append(("bad_naive_utc", path, "naive_utc_columns must be a list of unique identifiers"))
        naive = []
    if not (isinstance(excl, list)):
        probs.append(("bad_exclude", path, "exclude must be a list"))
        return
    evs = t["write_evidence"]
    ex_cols: list[str] = []
    for j, e in enumerate(excl):
        ep = f"{path}.exclude[{j}]"
        if not _closed(e, EXCLUDE_KEYS, ("column",), ep, probs):
            continue
        col = e["column"]
        if not (isinstance(col, str) and _IDENT.fullmatch(col)):
            probs.append(("bad_exclude", ep, f"{col!r} is not an identifier"))
            continue
        if col in ex_cols:
            probs.append(("exclude_duplicate", ep, f"column {col} excluded twice"))
        ex_cols.append(col)
        if col in key:
            probs.append(("exclude_key", ep, f"{col} is part of the natural key and cannot be excluded"))
        reason, code = e.get("reason"), e.get("reason_code")
        if not (isinstance(reason, str) and reason.strip()):
            probs.append(("exclude_no_reason", ep, f"column {col} is excluded without a reason"))
        elif len(reason.strip()) < MIN_REASON_CHARS:
            probs.append(("exclude_reason_short", ep, f"the reason for excluding {col} is shorter than {MIN_REASON_CHARS} characters"))
        if code not in EXCLUDE_REASON_CODES:
            probs.append(("exclude_bad_reason_code", ep, f"reason_code {code!r} is not one of {EXCLUDE_REASON_CODES}"))
        wins = _windows_of(evs, ctx)
        if ctx is not None and code == "not_written_by_writer":
            lists = [c for c in (_insert_columns(w, name) for w in wins) if c is not None]
            if not lists:
                probs.append(("exclude_not_written_unproven", ep, f"no cited statement is an INSERT of {name} with a column list: "
                                                                    f"cannot show the writer never writes {col}"))
            elif any(col in c for c in lists):
                probs.append(("exclude_not_written_unproven", ep, f"the writer's INSERT column list for {name} contains {col}: "
                                                                    "a column the writer writes cannot be excluded as not_written_by_writer"))
        if ctx is not None and code == "wall_clock_timestamp" and col not in WALL_CLOCK_NAMES and not any(_CLOCK.search(w) for w in wins):
            probs.append(("exclude_wall_clock_unproven", ep, f"{col} is not one of {WALL_CLOCK_NAMES} and no cited statement sets it from "
                                                             "now()/CURRENT_TIMESTAMP/datetime.now()"))
    for c in naive:
        if c in ex_cols:
            probs.append(("bad_naive_utc", path, f"{c} is excluded: it cannot also be a naive_utc column"))
    if not (isinstance(evs, list) and evs):
        probs.append(("evidence_missing", path, "write_evidence must list at least one `path:line` of the writer's write"))
    else:
        for k, ev in enumerate(evs):
            _check_evidence(ev, [name], f"{path}.write_evidence[{k}]", probs, ctx, write=True)
    if "ownership_evidence" in t:
        oe = t["ownership_evidence"]
        if not (isinstance(oe, list) and oe):
            probs.append(("evidence_missing", path, "ownership_evidence, when present, lists at least one `path:line`"))
        else:
            for k, ev in enumerate(oe):
                _check_evidence(ev, [name], f"{path}.ownership_evidence[{k}]", probs, ctx)
    emb_cols: list[str] = []
    emb = t.get("embedding")
    if emb is not None:
        if not (isinstance(emb, list) and emb):
            probs.append(("bad_embedding", path, "embedding must be a non-empty list of {column, source_columns, model_id}"))
        else:
            for k, e in enumerate(emb):
                ep = f"{path}.embedding[{k}]"
                if not _closed(e, EMBEDDING_KEYS, EMBEDDING_KEYS, ep, probs):
                    continue
                if not (isinstance(e["column"], str) and _IDENT.fullmatch(e["column"])
                        and isinstance(e["source_columns"], list) and e["source_columns"]
                        and all(isinstance(c, str) and _IDENT.fullmatch(c) for c in e["source_columns"])
                        and isinstance(e["model_id"], str) and e["model_id"].strip()):
                    probs.append(("bad_embedding", ep, "column, non-empty source_columns and a model_id are required"))
                    continue
                emb_cols.append(e["column"])
                if e["column"] in key or e["column"] in ex_cols:
                    probs.append(("bad_embedding", ep, f"embedding column {e['column']} must not be a key column or also be excluded (E5.5 excludes it itself)"))
                for s in e["source_columns"]:
                    if s in ex_cols:
                        probs.append(("bad_embedding", ep, f"source column {s} is excluded: the fingerprint covers the source columns"))
    ed = t.get("expected_difference")
    if ed is not None:
        if _closed(ed, EXPECTED_DIFF_KEYS, EXPECTED_DIFF_KEYS, f"{path}.expected_difference", probs):
            if not (isinstance(ed["columns"], list) and ed["columns"] and all(isinstance(c, str) and _IDENT.fullmatch(c) for c in ed["columns"])
                    and isinstance(ed["reference"], str) and len(ed["reference"].strip()) >= 8
                    and isinstance(ed["detail"], str) and len(ed["detail"].strip()) >= MIN_UNDECLARED_REASON_CHARS
                    and isinstance(ed["until"], str) and len(ed["until"].strip()) >= 20):
                probs.append(("bad_expected_difference", f"{path}.expected_difference",
                              "needs columns, a reference (>= 8 chars), a detail (>= 60 chars) and an `until` condition (>= 20 chars)"))
            else:
                for c in ed["columns"]:
                    if c in ex_cols or c in key:
                        probs.append(("bad_expected_difference", f"{path}.expected_difference", f"{c} is excluded or a key column: an expected difference is "
                                                                                              "NOT an exclusion, the column stays in the fingerprint"))
    hz = t.get("horizon_date_column")
    if hz is not None:
        if not (isinstance(hz, str) and _IDENT.fullmatch(hz)):
            probs.append(("bad_horizon_column", f"{path}.horizon_date_column", "must be a column identifier"))
        else:
            cols = (schema or {}).get("tables", {}).get(name, {}).get("columns") if isinstance(schema, Mapping) else None
            if cols is not None:
                if hz not in cols:
                    probs.append(("bad_horizon_column", f"{path}.horizon_date_column", f"{hz} is not a column of {name}"))
                elif cols[hz]["type"] not in HORIZON_TYPES:
                    probs.append(("bad_horizon_column", f"{path}.horizon_date_column", f"{hz} is {cols[hz]['type']}: the horizon column is a date or a naive-UTC timestamp"))
                elif cols[hz]["type"] == TIMESTAMP_NAIVE and hz not in naive:
                    probs.append(("bad_horizon_column", f"{path}.horizon_date_column", f"{hz} is a timestamp without time zone: list it in naive_utc_columns"))
    po = t.get("partial_ownership")
    if po is not None and _closed(po, PARTIAL_OWNERSHIP_KEYS, PARTIAL_OWNERSHIP_KEYS, f"{path}.partial_ownership", probs):
        if po["reason_code"] != PARTIAL_OWNERSHIP_CODE:
            probs.append(("bad_partial_ownership", f"{path}.partial_ownership", f"reason_code must be {PARTIAL_OWNERSHIP_CODE!r}"))
        if not (isinstance(po["detail"], str) and len(po["detail"].strip()) >= MIN_UNDECLARED_REASON_CHARS):
            probs.append(("bad_partial_ownership", f"{path}.partial_ownership", f"detail must be at least {MIN_UNDECLARED_REASON_CHARS} characters"))
        if not (isinstance(po["evidence"], list) and po["evidence"]):
            probs.append(("evidence_missing", f"{path}.partial_ownership", "cite the evidence (`path:line`) that rows of this table are not all writer-owned"))
        else:
            for k, ev in enumerate(po["evidence"]):
                _check_evidence(ev, [name], f"{path}.partial_ownership.evidence[{k}]", probs, ctx)
    ke = t["key_evidence"]
    if not (isinstance(ke, str) and re.fullmatch(r"(primary_key|unique):[a-z0-9_]+", ke)):
        probs.append(("bad_key_evidence", path, "key_evidence must be `primary_key:<constraint>` or `unique:<constraint>`"))
    if schema is None:
        return
    tab = (schema.get("tables") or {}).get(name)
    if tab is None:
        probs.append(("unknown_table", path, f"table {name} is not in the schema extract (not a `CREATE TABLE public.{name}` of the mirror dump)"))
        return
    cols = tab["columns"]
    extra = list(ed["columns"]) if isinstance(ed, Mapping) and isinstance(ed.get("columns"), list) else []
    for c in list(key) + ex_cols + list(naive) + emb_cols + extra:
        if isinstance(c, str) and c not in cols:
            probs.append(("unknown_column", path, f"column {c} does not exist in table {name}"))
    for e in (emb if isinstance(emb, list) else []):
        for c in (e.get("source_columns") or []) if isinstance(e, Mapping) and isinstance(e.get("source_columns"), list) else []:
            if isinstance(c, str) and c not in cols:
                probs.append(("unknown_column", path, f"embedding source column {c} does not exist in table {name}"))
    if any(c not in cols for c in key):
        return
    # the key must be exactly the columns of the PK / plain UNIQUE constraint named in key_evidence, and none of its columns nullable
    # (E5.5 refuses a NULL key)
    named: dict[str, list[str]] = {}
    if tab.get("primary_key") and tab.get("primary_key_name"):
        named[f"primary_key:{tab['primary_key_name']}"] = tab["primary_key"]
    for u in tab.get("unique", []):
        named[f"unique:{u['name']}"] = u["columns"]
    if isinstance(ke, str) and re.fullmatch(r"(primary_key|unique):[a-z0-9_]+", ke):
        if ke not in named:
            probs.append(("key_not_unique_in_schema", path, f"{ke} is not a primary key / plain unique constraint of {name}"))
        elif sorted(named[ke]) != sorted(key):
            probs.append(("key_not_unique_in_schema", path, f"{ke} covers {named[ke]}, not the declared key {key}"))
    for c in key:
        if not cols[c]["not_null"] and not cols[c]["generated"]:      # a generated column's NULL-ness is the expression's; E5.5 raises at run time
            probs.append(("key_nullable", path, f"key column {c} is nullable in {name}: E5.5 refuses a NULL natural key"))
    for e in excl:
        if not (isinstance(e, Mapping) and e.get("column") in cols):
            continue
        col, code, meta = e["column"], e.get("reason_code"), cols[e["column"]]
        if code == "surrogate_identity" and not meta["identity"]:
            probs.append(("exclude_reason_unfit", path, f"{col} is not an identity/serial/gen_random_uuid() column in {name}"))
        if code == "wall_clock_timestamp" and not meta["type"].startswith("timestamp"):
            probs.append(("exclude_reason_unfit", path, f"{col} is not a timestamp column ({meta['type']})"))
        if code == "build_identity" and col != "build_id":
            probs.append(("exclude_reason_unfit", path, f"build_identity applies to a column named build_id, not {col}"))
    non_key = set(cols) - set(key)
    if non_key and non_key <= (set(ex_cols) | set(emb_cols)):
        probs.append(("fingerprint_key_only", path, f"every non-key column of {name} is excluded: the fingerprint would cover only the key"))
    for c, meta in cols.items():
        if meta["type"] == TIMESTAMP_NAIVE and c not in ex_cols and c not in naive:
            probs.append(("naive_utc_missing", path, f"{name}.{c} is `timestamp without time zone` and not excluded: list it in naive_utc_columns "
                                                      "(E5.5 refuses a naive datetime)"))
    for c in naive:
        if c in cols and cols[c]["type"] != TIMESTAMP_NAIVE:
            probs.append(("bad_naive_utc", path, f"{name}.{c} is {cols[c]['type']}, not `timestamp without time zone`"))


def _validate_notcov(items: Any, key: str, ap: str, schema: Mapping | None, probs: list[Problem], ctx: _Ctx | None, names: list[str]) -> list[str]:
    out: list[str] = []
    if not isinstance(items, list):
        probs.append(("bad_shape", f"{ap}.{key}", "a list"))
        return out
    for i, n in enumerate(items):
        npth = f"{ap}.{key}[{i}]"
        if not _closed(n, NOTCOV_KEYS, NOTCOV_KEYS, npth, probs):
            continue
        if not (isinstance(n["reason"], str) and len(n["reason"].strip()) >= MIN_UNDECLARED_REASON_CHARS):
            probs.append(("undeclared_reason", npth, f"a {key[:-1].replace('_', ' ')} needs a reason of at least {MIN_UNDECLARED_REASON_CHARS} characters"))
        if schema is not None and n["name"] not in (schema.get("tables") or {}):
            probs.append(("unknown_table", npth, f"table {n['name']} is not in the schema extract"))
        if not (isinstance(n["evidence"], list) and n["evidence"]):
            probs.append(("evidence_missing", npth, "cite the evidence (`path:line`)"))
        else:
            for k, e in enumerate(n["evidence"]):
                _check_evidence(e, [n["name"]] if isinstance(n["name"], str) else None, f"{npth}.evidence[{k}]", probs, ctx)
        if isinstance(n["name"], str):
            if n["name"] in names:
                probs.append(("duplicate_table_claim", npth, f"{n['name']} is listed twice for this asset"))
            names.append(n["name"])
            out.append(n["name"])
    return out


def _horizon_rule(label: str, repro: Any, tables: Any, path: str, probs: list[Problem]) -> None:
    """N-135: a unit flagged rolling_horizon names exactly ONE table carrying `horizon_date_column`; no other unit carries it."""
    if not (isinstance(tables, list) and isinstance(repro, list)):
        return
    carriers = [t.get("name") for t in tables if isinstance(t, Mapping) and t.get("horizon_date_column") is not None]
    if "rolling_horizon" in repro:
        if len(carriers) != 1:
            probs.append(("horizon_column_required", path, f"{label} is flagged rolling_horizon: exactly one of its tables names a `horizon_date_column` (found {carriers})"))
    elif carriers:
        probs.append(("horizon_on_non_rolling", path, f"{label} is not flagged rolling_horizon but table(s) {carriers} name a horizon_date_column"))


def _repro_ok(rep: Any) -> bool:
    return (isinstance(rep, list) and bool(rep) and len(set(rep)) == len(rep) and all(r in REPRODUCIBILITY for r in rep)
            and (rep == ["deterministic"] or "deterministic" not in rep))


def validate(doc: Any, *, registry: Mapping[str, Mapping] | None = None, schema: Mapping | None = None,
             repo_root: str | Path | None = REPO_ROOT) -> list[Problem]:
    """Every problem with the declarations document ([] = valid). Never raises. `registry` is {asset_id: row} (None: the asset set is not
    checked), `schema` is a schema extract (None: no schema checks), `repo_root` None skips the writer-evidence checks."""
    probs: list[Problem] = []
    if not _closed(doc, TOP_KEYS, TOP_KEYS, "$", probs):
        return probs
    ctx = None
    if repo_root is not None:
        r = str(Path(repo_root))
        ctx = _Ctx(root=r, tracked=_tracked_paths(r, tuple(_evidence_paths(doc))))
    if doc["schema"] != SCHEMA_ID:
        probs.append(("bad_schema_id", "$.schema", f"must be {SCHEMA_ID!r}"))
    if doc["fingerprint_definition"] != FINGERPRINT_DEFINITION:
        probs.append(("bad_definition", "$.fingerprint_definition", f"must be {FINGERPRINT_DEFINITION!r}: one fingerprint definition only"))
    if doc["layer"] != LAYER or doc["scope"] != SCOPE:
        probs.append(("bad_scope", "$", f"layer must be {LAYER!r} and scope {SCOPE!r}"))
    src = doc["source"]
    if _closed(src, SOURCE_KEYS, SOURCE_KEYS, "$.source", probs):
        for k in ("registry_snapshot_sha256", "schema_dump_sha256"):
            if not (isinstance(src[k], str) and _SHA256.fullmatch(src[k])):
                probs.append(("bad_source", f"$.source.{k}", "must be a sha256 hex"))
        if not (isinstance(src["code_commit"], str) and _HEX40.fullmatch(src["code_commit"])):
            probs.append(("bad_source", "$.source.code_commit", "must be a 40-hex commit"))
    assets, groups = doc["assets"], doc["groups"]
    if not isinstance(assets, Mapping) or not assets:
        probs.append(("bad_shape", "$.assets", "assets must be a non-empty object"))
        return probs
    if not isinstance(groups, Mapping):
        probs.append(("bad_shape", "$.groups", "groups must be an object (possibly empty)"))
        groups = {}
    if registry is not None:
        for a in sorted(set(assets) - set(registry)):
            probs.append(("unknown_asset", f"assets.{a}", "not an active L0 asset of the registry snapshot"))
        for a in sorted(set(registry) - set(assets)):
            probs.append(("missing_asset", f"assets.{a}", "an active L0 asset must be declared or listed undeclared"))
    claimed: dict[str, str] = {}                      # declared table -> owner label ("asset X" | "group G")
    side: dict[str, set[str]] = {}                    # table -> labels that merely write / do not cover / do not write it
    # ── groups ──
    group_tables: dict[str, list[str]] = {}
    group_members: dict[str, list[str]] = {}
    group_evidence: dict[tuple[str, str], list] = {}
    for gid in sorted(groups):
        g = groups[gid]
        gp = f"groups.{gid}"
        if not (isinstance(gid, str) and _IDENT.fullmatch(gid)) or gid in assets or (GROUP_PREFIX + gid) in assets:
            probs.append(("bad_group", gp, "a group id is a lower-case identifier that is not an asset id (its unit id is grp_<id>)"))
            continue
        if not _closed(g, GROUP_KEYS, GROUP_REQUIRED, gp, probs):
            continue
        if not isinstance(g["seeded"], bool):
            probs.append(("bad_seeded", gp, "seeded must be true or false: a SEEDED group is copied from production, not rebuilt, and never counts toward the "
                                            "rebuilt-equals-source claim"))
        if not _repro_ok(g["reproducibility"]):
            probs.append(("bad_reproducibility", gp, f"reproducibility is a non-empty list of unique values from {REPRODUCIBILITY}; 'deterministic' stands alone"))
        tabs = g["tables"]
        if not (isinstance(tabs, list) and tabs):
            probs.append(("bad_group", gp, "a group declares at least one table"))
            tabs = []
        group_tables[gid] = []
        _horizon_rule(f"group {gid}", g["reproducibility"], tabs, gp, probs)
        for i, t in enumerate(tabs):
            _validate_table(t, f"group {gid}", f"{gp}.tables[{i}]", schema, probs, ctx)
            n = t.get("name") if isinstance(t, Mapping) else None
            if isinstance(n, str):
                group_tables[gid].append(n)
                if n in claimed and claimed[n] != f"group {gid}":
                    probs.append(("duplicate_table_claim", gp, f"table {n} is also declared by {claimed[n]}"))
                claimed.setdefault(n, f"group {gid}")
        mem = g["members"]
        if not (isinstance(mem, Mapping) and len(mem) >= 2):
            probs.append(("group_too_small", gp, "a group has at least two member assets (a table written by one asset is not shared)"))
            mem = mem if isinstance(mem, Mapping) else {}
        group_members[gid] = sorted(mem)
        for m in sorted(mem):
            ev = mem[m]
            if not (isinstance(ev, list) and ev):
                probs.append(("evidence_missing", f"{gp}.members.{m}", "each member cites its write evidence (`path:line`)"))
                continue
            group_evidence[(gid, m)] = ev
            for k, e in enumerate(ev):
                _check_evidence(e, group_tables[gid], f"{gp}.members.{m}.evidence[{k}]", probs, ctx, write=True)
    # ── assets ──
    declared_info: dict[str, dict] = {}
    for asset in sorted(assets):
        d = assets[asset]
        ap = f"assets.{asset}"
        if not _ASSET.fullmatch(asset) or asset.startswith(GROUP_PREFIX):
            probs.append(("bad_asset_id", ap, f"not an asset id (asset ids never start with {GROUP_PREFIX})"))
            continue
        if not isinstance(d, Mapping):
            probs.append(("bad_shape", ap, "expected an object"))
            continue
        status = d.get("status")
        if status == "undeclared":
            if not _closed(d, UNDECLARED_KEYS, UNDECLARED_KEYS, ap, probs):
                continue
            if d["reason_code"] not in UNDECLARED_CODES:
                probs.append(("undeclared_reason", ap, f"reason_code {d['reason_code']!r} is not one of {UNDECLARED_CODES}"))
            if not (isinstance(d["reason"], str) and len(d["reason"].strip()) >= MIN_UNDECLARED_REASON_CHARS):
                probs.append(("undeclared_reason", ap, f"an undeclared asset needs a reason of at least {MIN_UNDECLARED_REASON_CHARS} characters"))
            tw = d["tables_written"]
            if not (isinstance(tw, list) and all(isinstance(x, str) and _IDENT.fullmatch(x) for x in tw) and len(set(tw)) == len(tw)):
                probs.append(("bad_shape", f"{ap}.tables_written", "a list of unique table names"))
            else:
                for x in tw:
                    side.setdefault(x, set()).add(f"asset {asset}")
                if d["reason_code"] == "no_table" and tw:
                    probs.append(("undeclared_reason", ap, "no_table asset lists tables_written"))
                if schema is not None:
                    for x in tw:
                        if x not in (schema.get("tables") or {}):
                            probs.append(("unknown_table", ap, f"tables_written names {x}, which is not in the schema extract"))
            ev = d["evidence"]
            if not (isinstance(ev, list) and ev) and d["reason_code"] != "no_table":
                probs.append(("evidence_missing", ap, "an undeclared asset cites its evidence (`path:line`)"))
            elif isinstance(ev, list):
                for k, e in enumerate(ev):
                    _check_evidence(e, tw if isinstance(tw, list) and tw else None, f"{ap}.evidence[{k}]", probs, ctx)
            if registry is not None and asset in registry and registry[asset].get("target_table") not in (None, *(tw if isinstance(tw, list) else [])):
                probs.append(("registry_table_unaccounted", ap, f"registry target_table {registry[asset]['target_table']!r} is not in tables_written"))
            continue
        if status != "declared":
            probs.append(("bad_status", ap, "status must be 'declared' or 'undeclared'"))
            continue
        if not _closed(d, DECLARED_KEYS, DECLARED_REQUIRED, ap, probs):
            continue
        if d["fingerprint_definition"] != FINGERPRINT_DEFINITION:
            probs.append(("bad_definition", ap, f"must be {FINGERPRINT_DEFINITION!r}"))
        if d["scope"] != SCOPE:
            probs.append(("bad_scope", ap, f"must be {SCOPE!r}"))
        if d["coverage"] not in COVERAGE:
            probs.append(("bad_coverage", ap, f"coverage must be one of {COVERAGE}"))
        if not _repro_ok(d["reproducibility"]):
            probs.append(("bad_reproducibility", ap, f"reproducibility is a non-empty list of unique values from {REPRODUCIBILITY}; 'deterministic' stands alone"))
        tables, notcov, gids = d["tables"], d["not_covered_tables"], d["groups"]
        if not (isinstance(gids, list) and all(isinstance(x, str) for x in gids) and len(set(gids)) == len(gids)):
            probs.append(("bad_shape", f"{ap}.groups", "a list of unique group ids"))
            gids = []
        for gid in gids:
            if gid not in groups:
                probs.append(("group_member_mismatch", ap, f"names group {gid}, which is not declared"))
            elif asset not in group_members.get(gid, []):
                probs.append(("group_member_mismatch", ap, f"names group {gid} but is not one of its members"))
        if not isinstance(tables, list):
            probs.append(("bad_shape", f"{ap}.tables", "a list"))
            tables = []
        if not tables and not gids:
            probs.append(("empty_tables", ap, "a declared asset declares at least one table of its own or is a member of a group"))
        names: list[str] = []
        _horizon_rule(f"asset {asset}", d["reproducibility"], tables, ap, probs)
        for i, t in enumerate(tables):
            _validate_table(t, f"asset {asset}", f"{ap}.tables[{i}]", schema, probs, ctx)
            if isinstance(t, Mapping) and isinstance(t.get("name"), str):
                names.append(t["name"])
                n = t["name"]
                if n in claimed and claimed[n] != f"asset {asset}":
                    probs.append(("duplicate_table_claim", ap, f"table {n} is also declared by {claimed[n]}: a shared table is declared only through a group"))
                claimed.setdefault(n, f"asset {asset}")
        own = list(names)
        nc_names = _validate_notcov(notcov, "not_covered_tables", ap, schema, probs, ctx, names)
        if (d["coverage"] == "partial") != bool(notcov):
            probs.append(("partial_mismatch", ap, "coverage 'partial' needs not_covered_tables, and not_covered_tables needs coverage 'partial'"))
        nw_names = _validate_notcov(d.get("not_written_tables", []), "not_written_tables", ap, schema, probs, ctx, names) if "not_written_tables" in d else []
        if len(set(own)) != len(own):
            probs.append(("duplicate_table_claim", ap, "a table is listed twice"))
        for n in nc_names + nw_names:
            side.setdefault(n, set()).add(f"asset {asset}")
        declared_info[asset] = {"own": own, "groups": [g for g in gids if g in group_tables], "not_covered": nc_names, "not_written": nw_names, "d": d}
        gt = [t for g in declared_info[asset]["groups"] for t in group_tables[g]]
        accounted = set(own) | set(gt) | set(nc_names) | set(nw_names)
        if registry is not None and asset in registry and registry[asset].get("target_table") not in (None, *accounted):
            probs.append(("registry_table_unaccounted", ap, f"registry target_table {registry[asset]['target_table']!r} is neither declared, in a group nor not covered"))
        for n in (registry[asset].get("count_tables", []) if registry is not None and asset in registry else []):
            if n not in accounted:
                probs.append(("coverage_unlisted_table", ap, f"the registry's count_sql names table {n}, which this asset neither declares, shares in a group, "
                                                             "lists as not covered nor as not written"))
    # ── cross checks ──
    for gid, mem in group_members.items():
        for m in mem:
            a = assets.get(m)
            if not (isinstance(a, Mapping) and a.get("status") == "declared"):
                probs.append(("group_member_mismatch", f"groups.{gid}", f"member {m} is not a declared asset"))
            elif gid not in (a.get("groups") or []):
                probs.append(("group_member_mismatch", f"groups.{gid}", f"member {m} does not list the group in its `groups`"))
    for n, owner in sorted(claimed.items()):
        others = side.get(n, set()) - {owner}
        if others:
            probs.append(("duplicate_table_claim", owner.replace(" ", "s.", 1) if owner.startswith("asset") else f"groups.{owner[6:]}",
                          f"declared table {n} is also written / not covered / not written by {sorted(others)}: it is shared, so it is declared "
                          "only through a group"))
    # L3: coverage is verified against what the writer evidence shows it writes
    universe = set(schema.get("table_names") or []) if isinstance(schema, Mapping) else set()
    known = set(claimed) | set(side)
    if ctx is not None and universe:
        for asset, info in sorted(declared_info.items()):
            files: set[str] = set()
            evs = [e for t in info["d"]["tables"] if isinstance(t, Mapping) for e in (t.get("write_evidence") or [])]
            evs += [e for g in info["groups"] for e in group_evidence.get((g, asset), [])]
            for e in evs:
                if isinstance(e, str) and _EVIDENCE.fullmatch(e):
                    rel = e.rsplit(":", 1)[0]
                    if rel.endswith(".py") and ".." not in rel.split("/"):
                        files.add(rel)
            accounted = set(info["own"]) | {t for g in info["groups"] for t in group_tables[g]} | set(info["not_covered"]) | set(info["not_written"])
            for rel in sorted(files):
                lines = _file_lines(ctx.root, rel) or ()
                seen: set[str] = set()
                for ln in lines:
                    if ln.lstrip().startswith("#"):
                        continue
                    for m in _WRITE_STMT.finditer(ln):
                        n = m.group(1).lower()
                        if n in universe and n not in accounted and n not in known and n not in seen:
                            seen.add(n)
                            probs.append(("coverage_unlisted_table", f"assets.{asset}", f"{rel} writes table {n}, which is not listed for this asset "
                                                                                       "(declare it, or list it as not covered / not written with the reason)"))
    return probs


# ───────────────────────── the loaded, validated declarations ─────────────────────────

@dataclass(frozen=True)
class Declarations:
    doc: dict
    sha256: str                        # of the file bytes: what a reader output must quote
    path: str = ""

    @property
    def assets(self) -> dict:
        return self.doc["assets"]

    @property
    def groups(self) -> dict:
        return self.doc["groups"]

    def declared_assets(self) -> list[str]:
        return sorted(a for a, d in self.assets.items() if d["status"] == "declared")

    def undeclared_assets(self) -> dict[str, dict]:
        return {a: {"reason_code": d["reason_code"], "reason": d["reason"], "tables_written": list(d["tables_written"])}
                for a, d in sorted(self.assets.items()) if d["status"] == "undeclared"}

    def partial_assets(self) -> dict[str, list[dict]]:
        return {a: [dict(n) for n in d["not_covered_tables"]] for a, d in sorted(self.assets.items())
                if d["status"] == "declared" and d["coverage"] == "partial"}

    # ── comparison units: an asset with tables of its own, or a GROUP (a shared table is compared as one unit) ──
    @staticmethod
    def group_unit(gid: str) -> str:
        return GROUP_PREFIX + gid

    def units(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for a in self.declared_assets():
            d = self.assets[a]
            if d["tables"]:
                out[a] = {"kind": "asset", "members": [a], "tables": [t["name"] for t in d["tables"]], "reproducibility": list(d["reproducibility"]),
                          "seeded": False}
        for gid in sorted(self.groups):
            g = self.groups[gid]
            out[self.group_unit(gid)] = {"kind": "group", "members": sorted(g["members"]), "tables": [t["name"] for t in g["tables"]],
                                         "reproducibility": list(g["reproducibility"]), "seeded": bool(g["seeded"])}
        return out

    def expected_assets(self) -> list[str]:
        """The comparison units an E5.7 drill must cover (assets with their own tables + groups). Undeclared assets are reported, not dropped."""
        return sorted(self.units())

    def _unit(self, unit: str) -> dict:
        u = self.units().get(unit)
        if u is None:
            raise DeclarationError([("unknown_asset", unit, "not a comparison unit (a declared asset with tables, or a group)")])
        return u

    def _unit_tables(self, unit: str) -> list[dict]:
        self._unit(unit)
        if unit in self.assets:
            return self.assets[unit]["tables"]
        return self.groups[unit[len(GROUP_PREFIX):]]["tables"]

    def tables(self, unit: str) -> list[str]:
        return [t["name"] for t in self._unit_tables(unit)]

    def reproducibility(self, unit: str) -> list[str]:
        return list(self._unit(unit)["reproducibility"])

    def members(self, unit: str) -> list[str]:
        return list(self._unit(unit)["members"])

    def table_declaration(self, unit: str, table: str) -> dict:
        """The E5.5 declaration (VOLATILE mode) for one table of a unit, validated by `nikasha_stale_certs.validate_declaration`."""
        for t in self._unit_tables(unit):
            if t["name"] == table:
                decl = {"table": table, "scope": SCOPE, "natural_key": list(t["key"]),
                        "volatile_columns": [e["column"] for e in t["exclude"]], "naive_utc_columns": list(t["naive_utc_columns"])}
                if t.get("embedding"):
                    decl["embedding"] = [{"column": e["column"], "source_columns": list(e["source_columns"]), "model_id": e["model_id"]} for e in t["embedding"]]
                _e55().validate_declaration(decl, unit)         # E5.5 refuses what it refuses
                return decl
        raise DeclarationError([("unknown_table", table, f"{unit} does not declare this table")])

    def expected_differences(self) -> list[dict]:
        out = []
        for u in sorted(self.units()):
            for t in self._unit_tables(u):
                ed = t.get("expected_difference")
                if ed:
                    out.append({"unit": u, "table": t["name"], "columns": list(ed["columns"]), "reference": ed["reference"]})
        return out

    def seeded_units(self) -> list[str]:
        """Units whose rows are SEEDED from production rather than rebuilt: shown in the drill, never counted toward PASS."""
        return sorted(u for u, v in self.units().items() if v["seeded"])

    def partial_ownership_units(self) -> dict[str, list[str]]:
        """{unit: [tables]} whose rows are only partly writer-owned (migration-owned rows exist). The WHOLE table is still fingerprinted; a difference
        is an expected, explained one (`migration_owned_rows`) and the unit never counts toward a bare PASS."""
        out: dict[str, list[str]] = {}
        for u in sorted(self.units()):
            names = sorted(t["name"] for t in self._unit_tables(u) if t.get("partial_ownership"))
            if names:
                out[u] = names
        return out

    def not_run_allowed(self) -> dict[str, str]:
        """{unit: NEEDS_ reason} for the declared units whose asset may be `not_run` in a build record (the closed `NOT_RUN_ALLOWED` list)."""
        units = self.units()
        return {a: v["reason"] for a, v in sorted(NOT_RUN_ALLOWED.items()) if a in units}

    def horizon_tables(self) -> dict[str, dict]:
        """{unit: {table, date_column}} for the units flagged rolling_horizon (N-135): the table whose rows the `horizon` block of a fingerprint file describes."""
        out: dict[str, dict] = {}
        for u, v in sorted(self.units().items()):
            if "rolling_horizon" in v["reproducibility"]:
                hit = [t for t in self._unit_tables(u) if t.get("horizon_date_column")]
                if len(hit) != 1:
                    raise DeclarationError([("horizon_column_required", u, "a rolling_horizon unit names exactly one horizon_date_column")])
                out[u] = {"table": hit[0]["name"], "date_column": hit[0]["horizon_date_column"]}
        return out

    def projection_tables(self) -> dict[str, str]:
        """{unit: table} for the units that carry a recorded expected difference: the table whose PROJECTION (the fingerprint without the expected columns)
        both sides must report, so that nothing else in the unit can hide behind the recorded difference. One record per unit."""
        out: dict[str, str] = {}
        for e in self.expected_differences():
            if e["unit"] in out:
                raise DeclarationError([("expected_difference_twice", e["unit"], "a unit carries at most one expected_difference record")])
            out[e["unit"]] = e["table"]
        return out

    def projection_declaration(self, unit: str, table: str) -> dict:
        """The E5.5 declaration of one table's PROJECTION: its declaration with the expected-difference columns added to the volatile (ignored) columns."""
        ed = next((t["expected_difference"] for t in self._unit_tables(unit) if t["name"] == table and t.get("expected_difference")), None)
        if ed is None:
            raise DeclarationError([("no_expected_difference", f"{unit}.{table}", "the table carries no expected_difference record")])
        decl = self.table_declaration(unit, table)
        decl["volatile_columns"] = list(decl["volatile_columns"]) + [c for c in ed["columns"] if c not in decl["volatile_columns"]]
        _e55().validate_declaration(decl, unit)
        return decl

    def non_deterministic(self) -> dict[str, list[str]]:
        return {u: list(v["reproducibility"]) for u, v in sorted(self.units().items()) if v["reproducibility"] != ["deterministic"]}

    def drill_coverage(self) -> dict:
        """The closed coverage block embedded in the E5.7 drill document: what the verdict covers and what it does not."""
        un = {a: d["reason_code"] for a, d in self.undeclared_assets().items()}
        part = {a: sorted(n["name"] for n in v) for a, v in self.partial_assets().items()}
        nd = self.non_deterministic()
        return {"declarations_sha256": self.sha256, "units": self.expected_assets(), "declared": self.declared_assets(), "partial": part,
                "undeclared": un, "non_deterministic": nd, "groups": {u: v["members"] for u, v in self.units().items() if v["kind"] == "group"},
                "seeded": self.seeded_units(), "partial_ownership": self.partial_ownership_units(), "not_run_allowed": self.not_run_allowed(),
                "expected_differences": self.expected_differences(),
                "scope": "declared_only" if (part or un or nd or self.seeded_units() or self.partial_ownership_units()) else "all_declared_full"}

    def coverage_report(self) -> dict:
        un = self.undeclared_assets()
        cov = self.drill_coverage()
        return {"definition": FINGERPRINT_DEFINITION, "declarations_sha256": self.sha256, "assets_total": len(self.assets),
                "declared": self.declared_assets(), "undeclared": un, "partial": self.partial_assets(), "units": cov["units"], "groups": cov["groups"],
                "reproducibility": cov["non_deterministic"], "seeded": cov["seeded"], "partial_ownership": cov["partial_ownership"], "not_run_allowed": cov["not_run_allowed"], "expected_differences": cov["expected_differences"],
                "scope": cov["scope"]}


def load_declarations(path: str | Path = DEFAULT_DECLARATIONS, *, registry: Mapping | str | Path | None = DEFAULT_REGISTRY,
                      schema: Mapping | str | Path | None = DEFAULT_SCHEMA_EXTRACT, repo_root: str | Path | None = REPO_ROOT) -> Declarations:
    """Read, validate and return the declarations. Raises DeclarationError with every problem. Pass registry/schema/repo_root None to skip a check."""
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise DeclarationError([("declarations_unreadable", str(path), type(exc).__name__)]) from None
    doc = strict_loads(raw.decode("utf-8"))
    reg = load_registry(registry) if isinstance(registry, (str, Path)) else registry
    sch = load_schema_extract(schema) if isinstance(schema, (str, Path)) else schema
    probs = validate(doc, registry=reg, schema=sch, repo_root=repo_root)
    if probs:
        raise DeclarationError(probs)
    return Declarations(doc=doc, sha256=sha256_bytes(raw), path=str(path))


# ───────────────────────── fingerprints (E5.5's, composed per unit) ─────────────────────────

def _e55():
    sys.path.insert(0, str(HERE))
    import nikasha_stale_certs as nsc  # noqa: PLC0415  (E5.5: the ONE fingerprint definition)
    return nsc


def composite_fingerprint(table_shas: Mapping[str, str]) -> str:
    """The unit fingerprint: the table's own sha256 for a one-table unit, else sha256 of canonical JSON {definition, tables}."""
    if not table_shas or not all(isinstance(k, str) and isinstance(v, str) and _SHA256.fullmatch(v) for k, v in table_shas.items()):
        raise DeclarationError([("bad_fingerprint", "composite", "needs {table: sha256}")])
    if len(table_shas) == 1:
        return next(iter(table_shas.values()))
    return sha256_bytes(canonical_json({"definition": FINGERPRINT_DEFINITION, "tables": dict(sorted(table_shas.items()))}).encode("utf-8"))


def empty_table_fingerprint(decls: Declarations, unit: str, table: str) -> str:
    """The E5.5 fingerprint of ZERO rows under this table's declaration: what an empty table hashes to (so a non-empty claim can be refused)."""
    return _e55().fingerprint_rows([], decls.table_declaration(unit, table))


_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_ISO_TS = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}")
_OWN_MAX = object()                                   # horizon_block(cutoff=_OWN_MAX): the block's own max_date is the cutoff (the production side)


def horizon_iso_ok(v: Any) -> bool:
    """A horizon date: `YYYY-MM-DD` or the fixed-width naive timestamp `YYYY-MM-DDTHH:MM:SS.ffffff` (fixed width: text order is date order)."""
    try:
        if isinstance(v, str) and _ISO_DATE.fullmatch(v):
            return dt.date.fromisoformat(v).isoformat() == v
        if isinstance(v, str) and _ISO_TS.fullmatch(v):
            return dt.datetime.fromisoformat(v).isoformat(timespec="microseconds") == v
    except ValueError:
        return False
    return False


def horizon_iso(v: Any, where: str = "row") -> str:
    """A row's horizon-column value as its fixed-width ISO text. A NULL or timezone-aware value is refused (the column is a date or a naive UTC timestamp)."""
    if isinstance(v, dt.datetime):
        if v.tzinfo is not None:
            raise DeclarationError([("bad_horizon_value", where, "the horizon column holds a timezone-aware timestamp")])
        return v.isoformat(timespec="microseconds")
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, str):
        try:
            return dt.datetime.fromisoformat(v).replace(tzinfo=None).isoformat(timespec="microseconds") if ("T" in v or " " in v) else dt.date.fromisoformat(v).isoformat()
        except ValueError:
            pass
    raise DeclarationError([("bad_horizon_value", where, f"the horizon column holds {v!r}: a date or a naive timestamp is required")])


def horizon_block(rows: Sequence[Mapping], decl: Mapping, date_column: str, cutoff: Any = _OWN_MAX) -> dict:
    """The N-135 `horizon` block of one table: {date_column, min_date, max_date, rows, overlap_cutoff, overlap_rows, overlap_sha256}, computed from the SAME rows the
    table fingerprint is computed from (one streaming pass). `overlap_sha256` is the E5.5 table fingerprint (the same function and the same declaration, no second
    definition) over the rows with date <= overlap_cutoff. The production side leaves `cutoff` alone (its own max_date); the rehearsal side passes the PRODUCTION
    file's max_date (None when production holds no rows: then the overlap is empty)."""
    isos = [horizon_iso(r.get(date_column) if isinstance(r, Mapping) else None, f"row {i}.{date_column}") for i, r in enumerate(rows)]
    mn, mx = (min(isos), max(isos)) if isos else (None, None)
    cut = mx if cutoff is _OWN_MAX else cutoff
    if cut is not None and not horizon_iso_ok(cut):
        raise DeclarationError([("bad_horizon_cutoff", "cutoff", f"{cut!r} is not a horizon date")])
    over = [r for r, i in zip(rows, isos) if cut is not None and i <= cut]
    return {"date_column": date_column, "min_date": mn, "max_date": mx, "rows": len(rows), "overlap_cutoff": cut, "overlap_rows": len(over),
            "overlap_sha256": _e55().fingerprint_rows(over, decl)}


def empty_projection_fingerprint(decls: Declarations, unit: str, table: str) -> str:
    """The E5.5 fingerprint of ZERO rows under the table's PROJECTION declaration (the expected-difference columns ignored)."""
    return _e55().fingerprint_rows([], decls.projection_declaration(unit, table))


def unit_fingerprint(conn: Any, decls: Declarations, unit: str, *, max_rows: int | None = None, cursor_prefix: str | None = None,
                     horizon_cutoff: Any = _OWN_MAX) -> dict:
    """{tables: {table: {sha256, rows}}, composite} for one comparison unit, read through an open DB-API connection (the caller's transaction:
    use a read-only one). Exactly `nikasha_stale_certs.load_rows` + `fingerprint_rows` per table (what `table_fingerprint` does, plus the row count)."""
    nsc = _e55()
    out: dict = {"tables": {}}
    for table in decls.tables(unit):
        decl = decls.table_declaration(unit, table)
        kw: dict = {}
        if max_rows is not None:
            kw["max_rows"] = max_rows
        if cursor_prefix:
            kw["cursor_name"] = f"{cursor_prefix}_{unit}_{table}"[:63]
        rows = nsc.load_rows(conn, decl, None, **kw)
        out["tables"][table] = {"sha256": nsc.fingerprint_rows(rows, decl), "rows": len(rows)}
        ht = decls.horizon_tables().get(unit)
        if ht and ht["table"] == table:                                # N-135: the horizon block in the same pass, from the same rows
            out.setdefault("horizons", {})[table] = horizon_block(rows, decl, ht["date_column"], horizon_cutoff)
        if decls.projection_tables().get(unit) == table:               # the same rows, the expected-difference columns ignored: no second read
            out.setdefault("projections", {})[table] = {"sha256": nsc.fingerprint_rows(rows, decls.projection_declaration(unit, table)), "rows": len(rows)}
    out["composite"] = composite_fingerprint({t: v["sha256"] for t, v in out["tables"].items()})
    return out


def unit_fingerprints(conn: Any, decls: Declarations, units: Sequence[str] | None = None, *, horizon_cutoffs: Mapping[str, Any] | None = None, **kw: Any) -> dict:
    """{"definition", "declarations_sha256", "fingerprints": {unit: composite}, "tables": {unit: {table: {sha256, rows}}}, "projections": {unit: {table: {sha256, rows}}} for the units that
    carry an expected_difference record} for the comparison
    units (default all). An undeclared asset is refused, never skipped."""
    chosen = list(units) if units is not None else decls.expected_assets()
    fps, tabs, projs, hzs = {}, {}, {}, {}
    cuts = horizon_cutoffs or {}
    for u in chosen:
        r = unit_fingerprint(conn, decls, u, horizon_cutoff=cuts[u] if u in cuts else _OWN_MAX, **kw)
        fps[u], tabs[u] = r["composite"], r["tables"]
        if r.get("projections"):
            projs[u] = r["projections"]
        if r.get("horizons"):
            hzs[u] = r["horizons"]
    return {"definition": FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256, "fingerprints": fps, "tables": tabs, "projections": projs, "horizons": hzs}


def reader_selects(decls: Declarations, units: Sequence[str] | None = None) -> list[dict]:
    """The exact SELECT the production-side reader issues for each table of each comparison unit: E5.5's `build_select` of the table's
    declaration (volatile mode, global scope: `SELECT * FROM "<table>"`, no WHERE, no parameter). Deterministic; pinned by a test."""
    nsc = _e55()
    out = []
    for u in (list(units) if units is not None else decls.expected_assets()):
        for t in decls.tables(u):
            out.append({"asset": u, "table": t, "sql": nsc.build_select(decls.table_declaration(u, t))})
    return out


# ───────────────────────── CLI ─────────────────────────

def _print(obj: Any) -> None:
    print(json.dumps(obj, sort_keys=True, indent=2))


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fingerprint_declarations.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("validate", "summary"):
        p = sub.add_parser(name)
        p.add_argument("--declarations", default=str(DEFAULT_DECLARATIONS))
        p.add_argument("--registry", default=str(DEFAULT_REGISTRY))
        p.add_argument("--schema-extract", default=str(DEFAULT_SCHEMA_EXTRACT))
        p.add_argument("--repo-root", default=str(REPO_ROOT))
    ex = sub.add_parser("extract-schema")
    ex.add_argument("--dump", required=True)
    ex.add_argument("--declarations", default=str(DEFAULT_DECLARATIONS))
    ex.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "extract-schema":
            doc = strict_loads(Path(a.declarations).read_text(encoding="utf-8"))
            text = Path(a.dump).read_text(encoding="utf-8")
            ext = extract_schema(text, sorted(tables_named(doc)), dump_name=Path(a.dump).name)
            Path(a.out).write_text(json.dumps(ext, sort_keys=True, indent=1) + "\n", encoding="utf-8")
            _print({"written": a.out, "tables": len(ext["tables"]), "dump_sha256": ext["source"]["sha256"]})
            return 0
        d = load_declarations(a.declarations, registry=a.registry, schema=a.schema_extract, repo_root=a.repo_root)
        if a.cmd == "validate":
            _print({"valid": True, "declarations_sha256": d.sha256, "declared": len(d.declared_assets()), "undeclared": len(d.undeclared_assets()),
                    "partial": len(d.partial_assets()), "groups": len(d.groups), "units": len(d.expected_assets())})
        else:
            _print(d.coverage_report())
        return 0
    except DeclarationError as exc:
        _print({"valid": False, "problems": [{"code": c, "path": p, "message": m} for c, p, m in exc.problems]})
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
