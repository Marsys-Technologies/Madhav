#!/usr/bin/env python3
"""fingerprint_declarations.py -- Suvarna E5.7: the per-asset semantic-fingerprint DECLARATIONS for the 40 active L0 assets.

Data file: `00_ARCHITECTURE/control/FINGERPRINT_DECLARATIONS.json`. Design: /Users/Dev/suvarna-evidence/E5.7/DESIGN.md (N-116 "build it").
This module is the ONE place that knows the file's shape. It is a stdlib module (the E5.5 fingerprint it points at is imported lazily, only
when a fingerprint is actually computed or a declaration is converted). Imported by `suvarna_rehearsal.py` (E5.7 comparison) and
`suvarna_mirror_drill.py`; usable by anything else that needs "which tables does L0 asset X own and how are they fingerprinted".

WHAT A DECLARATION IS. For each of the 40 active L0 assets (the registry snapshot is the list) either
  * `declared`   : tables[] (name, key columns, exclude columns each with a reason, naive_utc_columns, write evidence), plus
                   `coverage` full|partial (partial lists `not_covered_tables`), `reproducibility`, scope `global`, and the fingerprint
                   definition `nikasha_stale_certs.table_fingerprint/1`; or
  * `undeclared` : reason_code + reason + tables_written (B.10: a fingerprint that cannot be honestly declared from the code is listed with
                   the reason, never invented, never silently dropped).
Each declared table maps 1:1 onto an E5.5 declaration in VOLATILE mode (`volatile_columns` = the excluded columns), so a column added to
the schema later enters the fingerprint automatically. `Declarations.table_declaration()` returns that dict after running it through
`nikasha_stale_certs.validate_declaration`: E5.5 refuses what it refuses; this module defines no second fingerprint.
ASSET FINGERPRINT: one table -> its table fingerprint; several -> sha256 of canonical JSON {"definition", "tables": {table: sha256}}.

VALIDATION (`validate`, `load_declarations`) is closed-schema and checks the file against (a) the registry snapshot (asset set) and (b) a
schema extract derived offline from the mirror's schema-only dump (tables, columns, nullability, PK/UNIQUE constraints, identity/serial
defaults, column types), and (c) the writer files named as evidence (they must exist and mention the table).

CLI:
  fingerprint_declarations.py validate  [--declarations P] [--registry P] [--schema-extract P] [--repo-root P]
  fingerprint_declarations.py summary   [--declarations P]                        (declared / partial / undeclared + reasons, JSON)
  fingerprint_declarations.py extract-schema --dump prod_schema.sql [--declarations P] --out extract.json   (offline; reads the dump text only)
Exit: 0 ok · 2 refused / invalid · 5 error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
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
UNDECLARED_CODES = ("no_table", "shared_table", "migration_owned_rows", "no_plain_natural_key", "second_writer_unprobed")
REPRODUCIBILITY = ("deterministic", "rolling_horizon", "platform_bound")
COVERAGE = ("full", "partial")
MIN_REASON_CHARS = 20
MIN_UNDECLARED_REASON_CHARS = 60
TIMESTAMP_NAIVE = "timestamp without time zone"

TOP_KEYS = ("schema", "fingerprint_definition", "layer", "scope", "source", "assets")
SOURCE_KEYS = ("registry_snapshot", "registry_snapshot_sha256", "schema_dump", "schema_dump_sha256", "code_commit")
DECLARED_KEYS = ("status", "fingerprint_definition", "scope", "coverage", "reproducibility", "tables", "not_covered_tables", "notes")
UNDECLARED_KEYS = ("status", "reason_code", "reason", "tables_written", "evidence")
TABLE_KEYS = ("name", "scope", "key", "key_evidence", "exclude", "naive_utc_columns", "write_evidence", "notes")
TABLE_REQUIRED = ("name", "scope", "key", "key_evidence", "exclude", "naive_utc_columns", "write_evidence")
EXCLUDE_KEYS = ("column", "reason_code", "reason")
NOTCOV_KEYS = ("name", "reason", "evidence")

_IDENT = re.compile(r"[a-z_][a-z0-9_]{0,62}")
_ASSET = re.compile(r"[a-z][a-z0-9_]*")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_HEX40 = re.compile(r"[0-9a-f]{40}")
_EVIDENCE = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./-]*):([1-9][0-9]*)")


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
    """{asset_id: {target_table, asset_kind, ...}} for the ACTIVE rows of the registry snapshot (the 40 L0 assets)."""
    try:
        rows = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DeclarationError([("registry_unreadable", str(path), f"{type(exc).__name__}")]) from None
    if not isinstance(rows, list):
        raise DeclarationError([("registry_unreadable", str(path), "the registry snapshot is not a list")])
    out: dict[str, dict] = {}
    for r in rows:
        if isinstance(r, Mapping) and r.get("is_active") is True and isinstance(r.get("asset_id"), str):
            out[r["asset_id"]] = {"target_table": r.get("target_table"), "asset_kind": r.get("asset_kind"), "scope": r.get("scope")}
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
            "tables": out}


def load_schema_extract(path: str | Path = DEFAULT_SCHEMA_EXTRACT) -> dict:
    try:
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DeclarationError([("schema_extract_unreadable", str(path), f"{type(exc).__name__}")]) from None
    if not (isinstance(doc, Mapping) and doc.get("schema") == EXTRACT_SCHEMA_ID and isinstance(doc.get("tables"), Mapping)):
        raise DeclarationError([("schema_extract_unreadable", str(path), "not a suvarna-l0-schema-extract/v1 document")])
    return dict(doc)


def tables_named(doc: Mapping) -> set[str]:
    """Every table name the declarations mention (declared, not covered, undeclared `tables_written`). Tolerant of a malformed document."""
    out: set[str] = set()
    assets = doc.get("assets") if isinstance(doc, Mapping) else None
    if not isinstance(assets, Mapping):
        return out
    for a in assets.values():
        if not isinstance(a, Mapping):
            continue
        for key in ("tables", "not_covered_tables"):
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


def _check_evidence(ev: Any, table: str | None, path: str, probs: list[Problem], repo_root: Path | None) -> None:
    if not isinstance(ev, str) or not _EVIDENCE.fullmatch(ev):
        probs.append(("evidence_bad", path, "evidence must be `relative/path:line`"))
        return
    rel, line = ev.rsplit(":", 1)
    if rel.startswith("/") or ".." in rel.split("/"):
        probs.append(("evidence_bad", path, "evidence path must be repo-relative"))
        return
    if repo_root is None:
        return
    f = repo_root / rel
    try:
        text = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        probs.append(("evidence_missing", path, f"{rel} does not exist in the repository"))
        return
    if int(line) > text.count("\n") + 1:
        probs.append(("evidence_missing", path, f"{rel} has no line {line}"))
    elif table is not None and not re.search(rf"\b{re.escape(table)}\b", text):
        probs.append(("evidence_missing", path, f"{rel} never names table {table}"))


def _validate_table(t: Any, asset: str, idx: int, schema: Mapping | None, probs: list[Problem], repo_root: Path | None) -> None:
    path = f"assets.{asset}.tables[{idx}]"
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
    for c in naive:
        if c in ex_cols:
            probs.append(("bad_naive_utc", path, f"{c} is excluded: it cannot also be a naive_utc column"))
    evs = t["write_evidence"]
    if not (isinstance(evs, list) and evs):
        probs.append(("evidence_missing", path, "write_evidence must list at least one `path:line` of the writer's write"))
    else:
        for k, ev in enumerate(evs):
            _check_evidence(ev, name, f"{path}.write_evidence[{k}]", probs, repo_root)
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
    for c in list(key) + ex_cols + list(naive):
        if c not in cols:
            probs.append(("unknown_column", path, f"column {c} does not exist in table {name}"))
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
    for c, meta in cols.items():
        if meta["type"] == TIMESTAMP_NAIVE and c not in ex_cols and c not in naive:
            probs.append(("naive_utc_missing", path, f"{name}.{c} is `timestamp without time zone` and not excluded: list it in naive_utc_columns "
                                                      "(E5.5 refuses a naive datetime)"))
    for c in naive:
        if c in cols and cols[c]["type"] != TIMESTAMP_NAIVE:
            probs.append(("bad_naive_utc", path, f"{name}.{c} is {cols[c]['type']}, not `timestamp without time zone`"))


def validate(doc: Any, *, registry: Mapping[str, Mapping] | None = None, schema: Mapping | None = None,
             repo_root: str | Path | None = REPO_ROOT) -> list[Problem]:
    """Every problem with the declarations document ([] = valid). Never raises. `registry` is {asset_id: row} (None: the asset set is not
    checked), `schema` is a schema extract (None: no schema checks), `repo_root` None skips the writer-evidence file checks."""
    probs: list[Problem] = []
    root = Path(repo_root) if repo_root is not None else None
    if not _closed(doc, TOP_KEYS, TOP_KEYS, "$", probs):
        return probs
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
    assets = doc["assets"]
    if not isinstance(assets, Mapping) or not assets:
        probs.append(("bad_shape", "$.assets", "assets must be a non-empty object"))
        return probs
    if registry is not None:
        for a in sorted(set(assets) - set(registry)):
            probs.append(("unknown_asset", f"assets.{a}", "not an active L0 asset of the registry snapshot"))
        for a in sorted(set(registry) - set(assets)):
            probs.append(("missing_asset", f"assets.{a}", "an active L0 asset must be declared or listed undeclared"))
    claimed: dict[str, str] = {}
    side: dict[str, set[str]] = {}       # table -> assets that merely write / do not cover it
    for asset in sorted(assets):
        d = assets[asset]
        ap = f"assets.{asset}"
        if not _ASSET.fullmatch(asset):
            probs.append(("bad_asset_id", ap, "not an asset id"))
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
                    side.setdefault(x, set()).add(asset)
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
                    _check_evidence(e, None, f"{ap}.evidence[{k}]", probs, root)
            if registry is not None and asset in registry and registry[asset].get("target_table") not in (None, *(tw if isinstance(tw, list) else [])):
                probs.append(("registry_table_unaccounted", ap, f"registry target_table {registry[asset]['target_table']!r} is not in tables_written"))
            continue
        if status != "declared":
            probs.append(("bad_status", ap, "status must be 'declared' or 'undeclared'"))
            continue
        if not _closed(d, DECLARED_KEYS, tuple(k for k in DECLARED_KEYS if k != "notes"), ap, probs):
            continue
        if d["fingerprint_definition"] != FINGERPRINT_DEFINITION:
            probs.append(("bad_definition", ap, f"must be {FINGERPRINT_DEFINITION!r}"))
        if d["scope"] != SCOPE:
            probs.append(("bad_scope", ap, f"must be {SCOPE!r}"))
        if d["coverage"] not in COVERAGE:
            probs.append(("bad_coverage", ap, f"coverage must be one of {COVERAGE}"))
        rep = d["reproducibility"]
        if not (isinstance(rep, list) and rep and len(set(rep)) == len(rep) and all(r in REPRODUCIBILITY for r in rep)
                and (rep == ["deterministic"] or "deterministic" not in rep)):
            probs.append(("bad_reproducibility", ap, f"reproducibility is a non-empty list of unique values from {REPRODUCIBILITY}; "
                                                     "'deterministic' stands alone"))
        tables, notcov = d["tables"], d["not_covered_tables"]
        if not (isinstance(tables, list) and tables):
            probs.append(("empty_tables", ap, "a declared asset declares at least one table"))
            tables = []
        if not isinstance(notcov, list):
            probs.append(("bad_shape", f"{ap}.not_covered_tables", "a list"))
            notcov = []
        if (d["coverage"] == "partial") != bool(notcov):
            probs.append(("partial_mismatch", ap, "coverage 'partial' needs not_covered_tables, and not_covered_tables needs coverage 'partial'"))
        names: list[str] = []
        for i, t in enumerate(tables):
            _validate_table(t, asset, i, schema, probs, root)
            if isinstance(t, Mapping) and isinstance(t.get("name"), str):
                names.append(t["name"])
        for i, n in enumerate(notcov):
            npth = f"{ap}.not_covered_tables[{i}]"
            if not _closed(n, NOTCOV_KEYS, NOTCOV_KEYS, npth, probs):
                continue
            if not (isinstance(n["reason"], str) and len(n["reason"].strip()) >= MIN_UNDECLARED_REASON_CHARS):
                probs.append(("undeclared_reason", npth, f"a not-covered table needs a reason of at least {MIN_UNDECLARED_REASON_CHARS} characters"))
            if schema is not None and n["name"] not in (schema.get("tables") or {}):
                probs.append(("unknown_table", npth, f"table {n['name']} is not in the schema extract"))
            if not (isinstance(n["evidence"], list) and n["evidence"]):
                probs.append(("evidence_missing", npth, "cite the evidence (`path:line`)"))
            else:
                for k, e in enumerate(n["evidence"]):
                    _check_evidence(e, n["name"] if isinstance(n["name"], str) else None, f"{npth}.evidence[{k}]", probs, root)
            if n["name"] in names:
                probs.append(("duplicate_table_claim", npth, f"{n['name']} is both declared and not covered"))
            names.append(n["name"]) if isinstance(n["name"], str) else None
        if len(set(names)) != len(names) and not any(p[0] == "duplicate_table_claim" and p[1].startswith(ap) for p in probs):
            probs.append(("duplicate_table_claim", ap, "a table is listed twice"))
        for t in tables:
            n = t.get("name") if isinstance(t, Mapping) else None
            if isinstance(n, str):
                if n in claimed and claimed[n] != asset:
                    probs.append(("duplicate_table_claim", ap, f"table {n} is also declared by {claimed[n]}: a shared table cannot be fingerprinted per asset"))
                claimed.setdefault(n, asset)
        for n in notcov:
            if isinstance(n, Mapping) and isinstance(n.get("name"), str):
                side.setdefault(n["name"], set()).add(asset)
        if registry is not None and asset in registry and registry[asset].get("target_table") not in (None, *names):
            probs.append(("registry_table_unaccounted", ap, f"registry target_table {registry[asset]['target_table']!r} is neither declared nor not covered"))
    for n, owner in sorted(claimed.items()):
        others = side.get(n, set()) - {owner}
        if others:
            probs.append(("duplicate_table_claim", f"assets.{owner}", f"declared table {n} is also written / not covered by {sorted(others)}: "
                                                                     "it is shared, so it cannot be declared for one asset"))
    return probs


# ───────────────────────── the loaded, validated declarations ─────────────────────────

@dataclass(frozen=True)
class Declarations:
    doc: dict
    sha256: str                        # of the file bytes: what a reader output must quote
    path: str = ""
    _by_asset: dict = field(default_factory=dict, repr=False)

    @property
    def assets(self) -> dict:
        return self.doc["assets"]

    def declared_assets(self) -> list[str]:
        return sorted(a for a, d in self.assets.items() if d["status"] == "declared")

    def undeclared_assets(self) -> dict[str, dict]:
        return {a: {"reason_code": d["reason_code"], "reason": d["reason"], "tables_written": list(d["tables_written"])}
                for a, d in sorted(self.assets.items()) if d["status"] == "undeclared"}

    def partial_assets(self) -> dict[str, list[dict]]:
        return {a: [dict(n) for n in d["not_covered_tables"]] for a, d in sorted(self.assets.items())
                if d["status"] == "declared" and d["coverage"] == "partial"}

    def expected_assets(self) -> list[str]:
        """The L0 assets an E5.7 drill must cover: the DECLARED ones. Undeclared ones are reported (`coverage_report`), not dropped."""
        return self.declared_assets()

    def tables(self, asset: str) -> list[str]:
        d = self._declared(asset)
        return [t["name"] for t in d["tables"]]

    def reproducibility(self, asset: str) -> list[str]:
        return self._declared(asset)["reproducibility"]

    def _declared(self, asset: str) -> dict:
        d = self.assets.get(asset)
        if d is None or d["status"] != "declared":
            raise DeclarationError([("unknown_asset", asset, "not a declared asset")])
        return d

    def table_declaration(self, asset: str, table: str) -> dict:
        """The E5.5 declaration (VOLATILE mode) for one declared table, validated by `nikasha_stale_certs.validate_declaration`."""
        d = self._declared(asset)
        for t in d["tables"]:
            if t["name"] == table:
                decl = {"table": table, "scope": SCOPE, "natural_key": list(t["key"]),
                        "volatile_columns": [e["column"] for e in t["exclude"]], "naive_utc_columns": list(t["naive_utc_columns"])}
                _e55().validate_declaration(decl, asset)         # E5.5 refuses what it refuses
                return decl
        raise DeclarationError([("unknown_table", table, f"{asset} does not declare this table")])

    def coverage_report(self, registry: Mapping | None = None) -> dict:
        un = self.undeclared_assets()
        return {"definition": FINGERPRINT_DEFINITION, "declarations_sha256": self.sha256,
                "assets_total": len(self.assets), "declared": self.declared_assets(), "undeclared": un,
                "partial": self.partial_assets(),
                "reproducibility": {a: list(d["reproducibility"]) for a, d in sorted(self.assets.items()) if d["status"] == "declared"
                                    and d["reproducibility"] != ["deterministic"]}}


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


# ───────────────────────── fingerprints (E5.5's, composed per asset) ─────────────────────────

def _e55():
    sys.path.insert(0, str(HERE))
    import nikasha_stale_certs as nsc  # noqa: PLC0415  (E5.5: the ONE fingerprint definition)
    return nsc


def composite_fingerprint(table_shas: Mapping[str, str]) -> str:
    """The asset fingerprint: the table's own sha256 for a one-table asset, else sha256 of canonical JSON {definition, tables}."""
    if not table_shas or not all(isinstance(k, str) and isinstance(v, str) and _SHA256.fullmatch(v) for k, v in table_shas.items()):
        raise DeclarationError([("bad_fingerprint", "composite", "needs {table: sha256}")])
    if len(table_shas) == 1:
        return next(iter(table_shas.values()))
    return sha256_bytes(canonical_json({"definition": FINGERPRINT_DEFINITION, "tables": dict(sorted(table_shas.items()))}).encode("utf-8"))


def asset_fingerprint(conn: Any, decls: Declarations, asset: str, *, max_rows: int | None = None, cursor_prefix: str | None = None) -> dict:
    """{table: {sha256, rows}, ..., composite} for one declared asset, read through an open DB-API connection (the caller's transaction:
    use a read-only one). Exactly `nikasha_stale_certs.load_rows` + `fingerprint_rows` per table (what `table_fingerprint` does, plus the row count)."""
    nsc = _e55()
    out: dict = {"tables": {}}
    for table in decls.tables(asset):
        decl = decls.table_declaration(asset, table)
        kw: dict = {}
        if max_rows is not None:
            kw["max_rows"] = max_rows
        if cursor_prefix:
            kw["cursor_name"] = f"{cursor_prefix}_{asset}_{table}"[:63]
        rows = nsc.load_rows(conn, decl, None, **kw)
        out["tables"][table] = {"sha256": nsc.fingerprint_rows(rows, decl), "rows": len(rows)}
    out["composite"] = composite_fingerprint({t: v["sha256"] for t, v in out["tables"].items()})
    return out


def asset_fingerprints(conn: Any, decls: Declarations, assets: Sequence[str] | None = None, **kw: Any) -> dict:
    """{"definition", "declarations_sha256", "fingerprints": {asset: composite}, "tables": {asset: {table: {sha256, rows}}}} for the declared
    assets (default all). An undeclared asset is refused, never skipped."""
    chosen = list(assets) if assets is not None else decls.declared_assets()
    fps, tabs = {}, {}
    for a in chosen:
        r = asset_fingerprint(conn, decls, a, **kw)
        fps[a], tabs[a] = r["composite"], r["tables"]
    return {"definition": FINGERPRINT_DEFINITION, "declarations_sha256": decls.sha256, "fingerprints": fps, "tables": tabs}


def reader_selects(decls: Declarations, assets: Sequence[str] | None = None) -> list[dict]:
    """The exact SELECT the production-side reader issues for each declared table: E5.5's `build_select` of the table's declaration
    (volatile mode, global scope: `SELECT * FROM "<table>"`, no WHERE, no parameter). Deterministic; pinned by a test."""
    nsc = _e55()
    out = []
    for a in (list(assets) if assets is not None else decls.declared_assets()):
        for t in decls.tables(a):
            out.append({"asset": a, "table": t, "sql": nsc.build_select(decls.table_declaration(a, t))})
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
            _print({"valid": True, "declarations_sha256": d.sha256, "declared": len(d.declared_assets()), "undeclared": len(d.undeclared_assets())})
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
