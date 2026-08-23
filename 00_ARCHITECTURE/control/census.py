#!/usr/bin/env python3
"""census.py — Nirmāṇa M0-T1: six-source asset census.

Reconciles SIX independent sources of "what assets exist":

  S1 asset_registry          live production DB (READ-ONLY)
  S2 @register('<id>')       decorators in the python writer trees
  S3 asset_registry_seed.ts  platform/scripts/seed/asset_registry_seed.ts
  S4 migrations              platform/migrations/*.sql that INSERT/UPDATE asset_registry
  S5 asset_throughput        live production DB (READ-ONLY)
  S6 CAPABILITY_MANIFEST.json

Emits:
  00_ARCHITECTURE/control/census.json        machine-readable presence matrix + findings
  00_ARCHITECTURE/control/CENSUS_REPORT.md   human-readable report

HARD RULES honoured by this script:
  * READ-ONLY against the database. No DDL, no DML. Only SELECT + SET statement_timeout.
  * The DATABASE_URL is read from platform/.env.local and is NEVER printed, logged or stored
    in any output artefact (charter P4).
  * Nothing is fabricated (H6). A source that cannot be parsed is recorded as UNKNOWN with
    the reason, never guessed.
  * This script reports observations. It issues no verdicts (I16).

Usage:  python3 00_ARCHITECTURE/control/census.py
"""
from __future__ import annotations

import ast
import datetime as _dt
import json
import pathlib
import re
import subprocess
import sys
from collections import Counter, defaultdict

import psycopg
import psycopg.rows

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTROL = ROOT / "00_ARCHITECTURE" / "control"

ASSET_ID_RE = re.compile(r"^(bg|ga|bo|ka|ph|mi)_[a-z0-9_]+$")
PREFIX_TO_LAYER = {
    "bg": ("L0", "brahmagyan"),
    "ga": ("L1", "ganita"),
    "bo": ("L2", "bodha"),
    "ka": ("L3", "kala"),
    "ph": ("L4", "phala"),
    "mi": ("L5", "mimamsa"),
}

# Directories that are copies of the repo, vendored deps, or build caches: not sources of truth.
EXCLUDE_PATH_PARTS = ("/.clone/", "/venv/", "/node_modules/", "/__pycache__/", "/.git/")

errors: list[str] = []          # parse failures — surfaced as UNKNOWN, never guessed
notes: list[str] = []


def _excluded(p: pathlib.Path) -> bool:
    s = "/" + str(p.relative_to(ROOT)).replace("\\", "/")
    return any(part in s + "/" for part in EXCLUDE_PATH_PARTS)


def _rel(p: pathlib.Path) -> str:
    return str(p.relative_to(ROOT))


# ─────────────────────────────────────────────────────────────────────────────
# S1 + S5 — live DB (READ-ONLY)
# ─────────────────────────────────────────────────────────────────────────────
def _database_url() -> str:
    """Read DATABASE_URL from platform/.env.local. Never returned to any output artefact."""
    env = ROOT / "platform" / ".env.local"
    for line in env.read_text().splitlines():
        if line.startswith("DATABASE_URL="):
            m = re.match(r"^\s*DATABASE_URL\s*=\s*(.+)$", line)
            if m:
                return m.group(1).strip().strip("\"'")
    raise SystemExit("DATABASE_URL not found in platform/.env.local")


REGISTRY_COLUMNS = [
    "asset_id", "layer", "layer_index", "layer_name", "sort_order", "sanskrit_name",
    "english_name", "storage_type", "target_table", "clear_tables", "target_floor",
    "depends_on", "scope", "is_active", "asset_type", "asset_kind", "catalog_status",
    "has_writer", "has_substeps", "service_health", "estimated_seconds",
    "integrity_check_sql", "volume_explanation", "expected_volume_formula",
    "provides_apis", "health_probe", "last_invoked_at", "last_selftest_at", "created_at",
]


def read_db() -> tuple[dict, dict, dict]:
    """Returns (registry_by_id, throughput_by_id, db_meta). READ-ONLY."""
    registry: dict[str, dict] = {}
    throughput: dict[str, dict] = {}
    meta: dict = {}
    with psycopg.connect(_database_url(), row_factory=psycopg.rows.dict_row,
                         autocommit=True) as conn:
        cur = conn.cursor()
        cur.execute("SET statement_timeout = '45s'")

        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'asset_registry'"
        )
        live_cols = {r["column_name"] for r in cur.fetchall()}
        cols = [c for c in REGISTRY_COLUMNS if c in live_cols]
        missing = [c for c in REGISTRY_COLUMNS if c not in live_cols]
        if missing:
            notes.append(
                "asset_registry does not have these expected columns (reported as absent, "
                f"not guessed): {', '.join(missing)}"
            )
        meta["registry_columns_read"] = cols
        meta["registry_columns_absent"] = missing

        cur.execute(f"SELECT {', '.join(cols)} FROM asset_registry ORDER BY asset_id")
        for r in cur.fetchall():
            registry[r["asset_id"]] = {
                k: (v.isoformat() if isinstance(v, _dt.datetime) else v) for k, v in r.items()
            }

        cur.execute(
            """
            SELECT asset_id,
                   count(*)                                   AS throughput_rows,
                   count(DISTINCT chart_id)                   AS distinct_charts,
                   array_agg(DISTINCT state ORDER BY state)   AS states,
                   max(last_built_at)                         AS last_built_at,
                   max(last_measured_at)                      AS last_measured_at,
                   sum(COALESCE(rows_written, 0))             AS rows_written_total,
                   count(*) FILTER (WHERE last_error IS NOT NULL) AS rows_with_error
            FROM asset_throughput
            GROUP BY asset_id
            ORDER BY asset_id
            """
        )
        for r in cur.fetchall():
            throughput[r["asset_id"]] = {
                k: (v.isoformat() if isinstance(v, _dt.datetime) else v) for k, v in r.items()
            }

        cur.execute("SELECT count(*) AS n FROM asset_registry")
        meta["asset_registry_row_count"] = cur.fetchone()["n"]
        cur.execute("SELECT count(*) AS n FROM asset_throughput")
        meta["asset_throughput_row_count"] = cur.fetchone()["n"]
    return registry, throughput, meta


# ─────────────────────────────────────────────────────────────────────────────
# S2 — @register('<asset_id>') decorators
# ─────────────────────────────────────────────────────────────────────────────
DECORATOR_RE = re.compile(r"^\s*@register\(\s*['\"]([A-Za-z0-9_]+)['\"]\s*\)")


def _is_test_path(p: pathlib.Path) -> bool:
    s = str(p).replace("\\", "/")
    return ("/tests/" in s or "/__tests__/" in s or p.name.startswith("test_")
            or p.name.endswith("_test.py"))


def _decorator_ids(tree: ast.AST) -> list[tuple[str, int, str]]:
    """Yield (asset_id, lineno, resolution) for every @register(...) decorator.

    Two forms occur in this codebase and BOTH are counted:
      @register('ka_gochara')   → resolution 'literal'
      @register(ASSET_ID)       → resolution 'module_constant' (resolved from the
                                  module-level `ASSET_ID = "..."` assignment)
    A form that cannot be resolved is returned with asset_id None and resolution
    'UNRESOLVED:<source>' — reported, never guessed.
    """
    consts: dict[str, str] = {}
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    consts[tgt.id] = node.value.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) \
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            consts[node.target.id] = node.value.value

    found: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            fn = dec.func
            name = fn.id if isinstance(fn, ast.Name) else (
                fn.attr if isinstance(fn, ast.Attribute) else None)
            if name != "register" or not dec.args:
                continue
            arg = dec.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                found.append((arg.value, dec.lineno, "literal"))
            elif isinstance(arg, ast.Name) and arg.id in consts:
                found.append((consts[arg.id], dec.lineno, f"module_constant:{arg.id}"))
            else:
                try:
                    src = ast.dump(arg)[:80]
                except Exception:
                    src = "?"
                found.append((None, dec.lineno, f"UNRESOLVED:{src}"))
    return found


def read_decorators() -> dict[str, dict]:
    """AST-based. Only decorators actually APPLIED to a class/function count — a
    `@register('x')` appearing in a docstring or a comment does not."""
    out: dict[str, dict] = {}
    roots = [ROOT / "platform" / "python-sidecar"]
    for base in roots:
        if not base.exists():
            errors.append(f"decorator source tree missing: {_rel(base)}")
            continue
        for p in sorted(base.rglob("*.py")):
            if _excluded(p):
                continue
            try:
                text = p.read_text(errors="replace")
            except OSError as e:
                errors.append(f"could not read {_rel(p)}: {e}")
                continue
            try:
                tree = ast.parse(text, filename=str(p))
            except SyntaxError as e:
                errors.append(
                    f"could not AST-parse {_rel(p)} (line {e.lineno}): {e.msg} — any "
                    "@register in this file is UNKNOWN to S2")
                continue
            is_test = _is_test_path(p)
            for aid, lineno, how in _decorator_ids(tree):
                if aid is None:
                    errors.append(
                        f"@register(...) at {_rel(p)}:{lineno} has a non-literal, "
                        f"non-constant argument ({how}) — asset_id UNKNOWN, not guessed")
                    continue
                rec = out.setdefault(aid, {"sites": [], "production_sites": 0, "test_sites": 0})
                rec["sites"].append({"file": _rel(p), "line": lineno, "is_test": is_test,
                                     "resolution": how})
                rec["test_sites" if is_test else "production_sites"] += 1
    return out


# ─────────────────────────────────────────────────────────────────────────────
# S3 — asset_registry_seed.ts
# ─────────────────────────────────────────────────────────────────────────────
SEED_ID_RE = re.compile(r"^\s*asset_id:\s*['\"]([A-Za-z0-9_]+)['\"]")


def read_seed() -> dict[str, dict]:
    seed_path = ROOT / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"
    out: dict[str, dict] = {}
    if not seed_path.exists():
        errors.append(
            f"asset_registry_seed.ts NOT FOUND at {_rel(seed_path)} — S3 column is UNKNOWN "
            "for every asset"
        )
        return out
    text = seed_path.read_text(errors="replace")
    for lineno, line in enumerate(text.splitlines(), start=1):
        m = SEED_ID_RE.match(line)
        if not m:
            continue
        aid = m.group(1)
        out.setdefault(aid, {"file": _rel(seed_path), "lines": []})["lines"].append(lineno)
    # capture catalog_status / is_active declared alongside, best-effort block scan
    blocks = re.split(r"\n(?=\s*\{\s*\n\s*asset_id:)", text)
    for b in blocks:
        m = SEED_ID_RE.search(b)
        if not m or m.group(1) not in out:
            continue
        rec = out[m.group(1)]
        cs = re.search(r"catalog_status:\s*['\"]([A-Z]+)['\"]", b)
        ia = re.search(r"\n\s*is_active:\s*(true|false)", b)
        lay = re.search(r"\n\s*layer:\s*['\"]([a-z]+)['\"]", b)
        rec["seed_catalog_status"] = cs.group(1) if cs else None
        rec["seed_is_active"] = (ia.group(1) == "true") if ia else None
        rec["seed_layer"] = lay.group(1) if lay else None
    if not out:
        errors.append(
            f"{_rel(seed_path)} parsed but yielded 0 asset_id entries — S3 treated as UNKNOWN"
        )
    return out


# ─────────────────────────────────────────────────────────────────────────────
# S4 — migrations that INSERT/UPDATE asset_registry
# ─────────────────────────────────────────────────────────────────────────────
TOUCH_RE = re.compile(
    r"\b(INSERT\s+INTO\s+asset_registry|UPDATE\s+asset_registry|DELETE\s+FROM\s+asset_registry)",
    re.IGNORECASE,
)
QUOTED_RE = re.compile(r"'([A-Za-z0-9_]+)'")
# strong evidence: the token is used AS an asset_id, not merely present in the file
ASSET_ID_EQ_RE = re.compile(r"asset_id\s*(?:=|<>|!=)\s*'([A-Za-z0-9_]+)'", re.IGNORECASE)
ASSET_ID_IN_RE = re.compile(r"asset_id\s+IN\s*\(([^)]*)\)", re.IGNORECASE)
INSERT_VALUES_RE = re.compile(
    r"INSERT\s+INTO\s+asset_registry\b.*?VALUES\s*\(\s*'([A-Za-z0-9_]+)'",
    re.IGNORECASE | re.DOTALL,
)
SET_ASSET_ID_RE = re.compile(r"SET\s+asset_id\s*=\s*'([A-Za-z0-9_]+)'", re.IGNORECASE)


def read_migrations() -> tuple[dict[str, dict], list[dict]]:
    """Scan platform/migrations/**/*.sql for statements against asset_registry.

    Two confidence tiers, because a bare "quoted token that looks like an asset id"
    over-matches badly (table names, count_sql bodies, prose in comments):

      strong — the token is used AS an asset_id: `asset_id = 'x'`, `asset_id IN (...)`,
               `SET asset_id = 'x'`, or the first VALUES literal of an
               `INSERT INTO asset_registry (asset_id, ...)`.
      weak   — any other asset-shaped quoted token in a file that touches asset_registry.
               Reported separately and NOT counted as S4 presence.
    """
    mig_dir = ROOT / "platform" / "migrations"
    out: dict[str, dict] = {}
    weak_only: dict[str, dict] = {}
    files: list[dict] = []
    if not mig_dir.exists():
        errors.append(f"migrations dir missing: {_rel(mig_dir)}")
        return out, files
    for p in sorted(mig_dir.rglob("*.sql")):
        if _excluded(p):
            continue
        try:
            text = p.read_text(errors="replace")
        except OSError as e:
            errors.append(f"could not read {_rel(p)}: {e}")
            continue
        ops = sorted({m.group(1).split()[0].upper() for m in TOUCH_RE.finditer(text)})
        if not ops:
            continue
        strong = set(ASSET_ID_EQ_RE.findall(text))
        strong |= set(INSERT_VALUES_RE.findall(text))
        strong |= set(SET_ASSET_ID_RE.findall(text))
        for grp in ASSET_ID_IN_RE.findall(text):
            strong |= set(QUOTED_RE.findall(grp))
        strong = {s for s in strong if ASSET_ID_RE.match(s)}
        weak = {q for q in QUOTED_RE.findall(text) if ASSET_ID_RE.match(q)} - strong
        files.append({"file": _rel(p), "ops": ops,
                      "asset_ids_strong": sorted(strong), "asset_ids_weak": sorted(weak),
                      "archived": "/_archive/" in "/" + _rel(p)})
        for aid in strong:
            rec = out.setdefault(aid, {"files": [], "ops": set()})
            rec["files"].append(_rel(p))
            rec["ops"].update(ops)
        for aid in weak:
            rec = weak_only.setdefault(aid, {"files": [], "ops": set()})
            rec["files"].append(_rel(p))
            rec["ops"].update(ops)
    for rec in out.values():
        rec["ops"] = sorted(rec["ops"])
    for aid, rec in weak_only.items():
        rec["ops"] = sorted(rec["ops"])
        if aid not in out:
            out.setdefault("__weak__", {})
    globals()["MIGRATION_WEAK"] = {a: r for a, r in weak_only.items() if a not in out}
    out.pop("__weak__", None)
    return out, files


MIGRATION_WEAK: dict[str, dict] = {}


# ─────────────────────────────────────────────────────────────────────────────
# S6 — CAPABILITY_MANIFEST.json
# ─────────────────────────────────────────────────────────────────────────────
def read_manifest() -> tuple[dict[str, dict], dict]:
    path = ROOT / "00_ARCHITECTURE" / "CAPABILITY_MANIFEST.json"
    meta: dict = {"path": _rel(path)}
    out: dict[str, dict] = {}
    if not path.exists():
        errors.append(f"CAPABILITY_MANIFEST.json NOT FOUND at {_rel(path)} — S6 is UNKNOWN")
        meta["parsed"] = False
        return out, meta
    try:
        doc = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"CAPABILITY_MANIFEST.json is not valid JSON ({e}) — S6 is UNKNOWN")
        meta["parsed"] = False
        return out, meta
    entries = doc.get("entries")
    if not isinstance(entries, list):
        errors.append("CAPABILITY_MANIFEST.json has no list-valued 'entries' — S6 is UNKNOWN")
        meta["parsed"] = False
        return out, meta
    meta.update({
        "parsed": True,
        "generated_at": doc.get("generated_at"),
        "generator_version": doc.get("generator_version"),
        "declared_entry_count": doc.get("entry_count"),
        "actual_entry_count": len(entries),
    })
    for e in entries:
        cid = e.get("canonical_id")
        if not cid:
            continue
        out[cid] = {"path": e.get("path"), "status": e.get("status"), "layer": e.get("layer")}
    meta["entries_with_asset_id_shape"] = sorted(
        cid for cid in out if ASSET_ID_RE.match(cid)
    )
    return out, meta


# ─────────────────────────────────────────────────────────────────────────────
# assembly
# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    registry, throughput, db_meta = read_db()
    decorators = read_decorators()
    seed = read_seed()
    migrations, migration_files = read_migrations()

    # S4 completeness: how much of the migration series is even present on disk
    mig_dir = ROOT / "platform" / "migrations"
    numbered: dict[int, list[str]] = defaultdict(list)
    for q in sorted(mig_dir.glob("*.sql")):
        m = re.match(r"^(\d+)_", q.name)
        if m:
            numbered[int(m.group(1))].append(q.name)
    nums = sorted(numbered)
    mig_series = {
        "numbered_sql_files_present": sum(len(v) for v in numbered.values()),
        "distinct_numbers_present": len(nums),
        "duplicate_numbers": {str(k): v for k, v in sorted(numbered.items()) if len(v) > 1},
        "lowest_number": nums[0] if nums else None,
        "highest_number": nums[-1] if nums else None,
        "numbers_in_range_absent_from_tree": (
            (nums[-1] - nums[0] + 1) - len(nums) if nums else None),
    }
    if mig_series["duplicate_numbers"]:
        notes.append(
            "platform/migrations holds more than one .sql file at the same migration number: "
            + "; ".join(f"{k} -> {', '.join(v)}"
                        for k, v in mig_series["duplicate_numbers"].items())
            + ". Reported as an observation about the migration series; ordering/ledger "
              "consequences are not evaluated here.")
    manifest, manifest_meta = read_manifest()

    seed_unknown = not seed
    manifest_unknown = not manifest_meta.get("parsed")

    # Decorator ids that don't even look like asset ids (e.g. test fixtures) are kept but flagged.
    universe = sorted(
        set(registry) | set(decorators) | set(seed) | set(migrations) | set(throughput)
        | {cid for cid in manifest if ASSET_ID_RE.match(cid)}
    )

    matrix: dict[str, dict] = {}
    for aid in universe:
        reg = registry.get(aid)
        dec = decorators.get(aid)
        thr = throughput.get(aid)
        prefix = aid.split("_", 1)[0] if "_" in aid else None
        exp = PREFIX_TO_LAYER.get(prefix)
        matrix[aid] = {
            "asset_id": aid,
            "sources": {
                "S1_asset_registry": bool(reg),
                "S2_decorator": bool(dec),
                "S3_seed_ts": "UNKNOWN" if seed_unknown else (aid in seed),
                "S4_migrations": aid in migrations,
                "S5_asset_throughput": bool(thr),
                "S6_capability_manifest": "UNKNOWN" if manifest_unknown else (aid in manifest),
            },
            "source_count_confirmed": sum(
                1 for v in (
                    bool(reg), bool(dec),
                    (False if seed_unknown else aid in seed),
                    aid in migrations, bool(thr),
                    (False if manifest_unknown else aid in manifest),
                ) if v is True
            ),
            "registry": reg,
            "decorator": (
                {"production_sites": dec["production_sites"], "test_sites": dec["test_sites"],
                 "sites": dec["sites"]} if dec else None
            ),
            "seed": seed.get(aid),
            "migrations": migrations.get(aid),
            "throughput": thr,
            "prefix": prefix,
            "prefix_expected_layer_index": exp[0] if exp else None,
            "prefix_expected_layer": exp[1] if exp else None,
            "asset_id_shape_valid": bool(ASSET_ID_RE.match(aid)),
        }

    f: dict = {}

    # ── three-way diff: registry vs decorators vs seed ────────────────────────
    prod_dec = {a for a, d in decorators.items() if d["production_sites"] > 0}
    test_only_dec = {a for a, d in decorators.items()
                     if d["production_sites"] == 0 and d["test_sites"] > 0}
    reg_ids = set(registry)
    seed_ids = set(seed)
    f["three_way_diff"] = {
        "counts": {
            "registry": len(reg_ids),
            "decorators_total": len(decorators),
            "decorators_production": len(prod_dec),
            "decorators_test_only": len(test_only_dec),
            "seed": ("UNKNOWN" if seed_unknown else len(seed_ids)),
        },
        "in_all_three": sorted(reg_ids & prod_dec & seed_ids) if not seed_unknown else "UNKNOWN",
        "registry_only": sorted(reg_ids - prod_dec - seed_ids) if not seed_unknown else None,
        "decorator_only": sorted(prod_dec - reg_ids - seed_ids) if not seed_unknown else None,
        "seed_only": sorted(seed_ids - reg_ids - prod_dec) if not seed_unknown else None,
        "registry_and_decorator_not_seed": sorted(
            (reg_ids & prod_dec) - seed_ids) if not seed_unknown else None,
        "registry_and_seed_not_decorator": sorted(
            (reg_ids & seed_ids) - prod_dec) if not seed_unknown else None,
        "decorator_and_seed_not_registry": sorted(
            (prod_dec & seed_ids) - reg_ids) if not seed_unknown else None,
        "decorator_ids_test_fixtures_only": sorted(test_only_dec),
        "decorator_ids_not_asset_shaped": sorted(
            a for a in decorators if not ASSET_ID_RE.match(a)),
    }

    # ── S4: ids that ONLY a migration knows about ─────────────────────────────
    mig_only = sorted(set(migrations) - reg_ids - prod_dec - set(seed) - set(throughput))
    f["migration_only_ids"] = [
        {"asset_id": a, "files": migrations[a]["files"], "ops": migrations[a]["ops"]}
        for a in mig_only
    ]
    f["migration_weak_matches_not_confirmed_elsewhere"] = [
        {"asset_id": a, "files": r["files"], "ops": r["ops"],
         "also_in_registry": a in reg_ids}
        for a, r in sorted(MIGRATION_WEAK.items())
    ]

    # ── registered-but-dead ───────────────────────────────────────────────────
    dead = []
    for aid, reg in registry.items():
        if aid in prod_dec or aid in throughput:
            continue
        dead.append({
            "asset_id": aid,
            "catalog_status": reg.get("catalog_status"),
            "is_active": reg.get("is_active"),
            "has_writer_flag": reg.get("has_writer"),
            "asset_kind": reg.get("asset_kind"),
            "storage_type": reg.get("storage_type"),
            "target_table": reg.get("target_table"),
            "in_seed": ("UNKNOWN" if seed_unknown else aid in seed),
            "in_migrations": aid in migrations,
            "created_at": reg.get("created_at"),
        })
    f["registered_but_dead"] = sorted(dead, key=lambda r: r["asset_id"])

    # has_writer flag vs actual decorator presence (the registry's own claim, checked)
    f["has_writer_flag_vs_decorator"] = {
        "flag_true_no_production_decorator": sorted(
            a for a, r in registry.items() if r.get("has_writer") is True and a not in prod_dec),
        "flag_false_or_null_but_decorator_exists": sorted(
            a for a, r in registry.items() if r.get("has_writer") is not True and a in prod_dec),
        "flag_null": sorted(a for a, r in registry.items() if r.get("has_writer") is None),
    }

    # ── throughput on inactive/retired/absent assets ──────────────────────────
    thr_issues = {"not_in_registry": [], "is_active_false": [], "catalog_status_retired": [],
                  "catalog_status_draft": []}
    for aid, thr in throughput.items():
        reg = registry.get(aid)
        row = {"asset_id": aid, "throughput_rows": thr["throughput_rows"],
               "states": thr["states"], "last_built_at": thr["last_built_at"],
               "rows_written_total": thr["rows_written_total"]}
        if reg is None:
            thr_issues["not_in_registry"].append(row)
            continue
        if reg.get("is_active") is False:
            thr_issues["is_active_false"].append({**row, "catalog_status": reg.get("catalog_status")})
        cs = (reg.get("catalog_status") or "").upper()
        if cs == "RETIRED":
            thr_issues["catalog_status_retired"].append(row)
        elif cs == "DRAFT":
            thr_issues["catalog_status_draft"].append(row)
    f["throughput_on_inactive_or_retired"] = thr_issues

    # ── co-writer / multi-producer collisions on target_table ─────────────────
    by_table: dict[str, list[str]] = defaultdict(list)
    for aid, reg in registry.items():
        t = reg.get("target_table")
        if t:
            by_table[t].append(aid)
    collisions = []
    for t, ids in sorted(by_table.items()):
        if len(ids) < 2:
            continue
        ids = sorted(ids)
        collisions.append({
            "target_table": t,
            "asset_count": len(ids),
            "asset_ids": ids,
            "layers": sorted({(registry[a].get("layer_index") or registry[a].get("layer") or "?")
                              for a in ids}),
            "with_production_writer": sorted(a for a in ids if a in prod_dec),
            "active": sorted(a for a in ids if registry[a].get("is_active") is True),
            "catalog_statuses": sorted({registry[a].get("catalog_status") or "NULL" for a in ids}),
        })
    f["target_table_collisions"] = collisions
    f["target_table_null_or_missing"] = sorted(
        a for a, r in registry.items() if not r.get("target_table"))

    # a decorator may register multiple asset_ids in one module — the module-level co-writer view
    file_to_ids: dict[str, list[str]] = defaultdict(list)
    for aid, d in decorators.items():
        for s in d["sites"]:
            if not s["is_test"]:
                file_to_ids[s["file"]].append(aid)
    f["multi_asset_writer_modules"] = [
        {"file": fn, "asset_ids": sorted(set(ids))}
        for fn, ids in sorted(file_to_ids.items()) if len(set(ids)) > 1
    ]

    # ── prefix conformance ────────────────────────────────────────────────────
    # Four distinct classes, kept apart on purpose: a wrong layer and a missing
    # layer_index are different defects and must not be totalled together.
    classes = {"unrecognised_prefix": [], "layer_contradiction": [],
               "layer_index_format": [], "layer_index_null": []}
    conforming = []
    for aid, reg in sorted(registry.items()):
        prefix = aid.split("_", 1)[0] if "_" in aid else None
        exp = PREFIX_TO_LAYER.get(prefix)
        li = reg.get("layer_index")
        lay = (reg.get("layer") or "").lower()
        if exp is None:
            classes["unrecognised_prefix"].append({
                "asset_id": aid, "prefix": prefix, "layer": reg.get("layer"),
                "layer_index": li})
            continue
        exp_li, exp_layer = exp
        if lay and lay != exp_layer:
            classes["layer_contradiction"].append({
                "asset_id": aid, "prefix": prefix, "layer": reg.get("layer"),
                "layer_expected": exp_layer, "layer_index": li,
                "layer_index_expected": exp_li})
            continue
        if li is None:
            classes["layer_index_null"].append({
                "asset_id": aid, "layer": reg.get("layer"), "layer_index_expected": exp_li})
            continue
        if li != exp_li:
            if li == exp_li.lstrip("L"):
                classes["layer_index_format"].append({
                    "asset_id": aid, "layer_index": li, "layer_index_expected": exp_li,
                    "layer": reg.get("layer")})
            else:
                classes["layer_contradiction"].append({
                    "asset_id": aid, "prefix": prefix, "layer": reg.get("layer"),
                    "layer_expected": exp_layer, "layer_index": li,
                    "layer_index_expected": exp_li})
            continue
        conforming.append(aid)
    f["prefix_conformance"] = {
        "checked": len(registry),
        "fully_conforming": len(conforming),
        "unrecognised_prefix": classes["unrecognised_prefix"],
        "layer_contradiction": classes["layer_contradiction"],
        "layer_index_format": classes["layer_index_format"],
        "layer_index_null": classes["layer_index_null"],
        "prefix_distribution": dict(sorted(Counter(
            (a.split("_", 1)[0] if "_" in a else "?") for a in registry).items())),
        "class_definitions": {
            "unrecognised_prefix": "asset_id prefix is not one of bg_/ga_/bo_/ka_/ph_/mi_",
            "layer_contradiction": "prefix says one layer, registry.layer or layer_index says "
                                   "a different one — the prefix is genuinely wrong or the "
                                   "layer column is",
            "layer_index_format": "layer names the right layer but layer_index is the bare "
                                  "digit ('1') where the convention is 'L1' — a format "
                                  "inconsistency, not a wrong layer",
            "layer_index_null": "layer_index is NULL, so the layer cannot be cross-checked "
                                "from that column at all",
        },
    }

    # ── catalog_status distribution + DRAFT-but-served ────────────────────────
    cs_counter = Counter((r.get("catalog_status") or "NULL") for r in registry.values())
    draft_served = []
    for aid, reg in registry.items():
        if (reg.get("catalog_status") or "").upper() != "DRAFT":
            continue
        signals = []
        if reg.get("is_active") is True:
            signals.append("is_active=true")
        if reg.get("provides_apis"):
            signals.append("provides_apis non-empty")
        if reg.get("health_probe"):
            signals.append("health_probe non-empty")
        if aid in throughput:
            signals.append(f"asset_throughput rows={throughput[aid]['throughput_rows']}")
        if reg.get("last_invoked_at"):
            signals.append(f"last_invoked_at={reg['last_invoked_at']}")
        if signals:
            draft_served.append({
                "asset_id": aid, "layer_index": reg.get("layer_index"),
                "asset_kind": reg.get("asset_kind"), "serving_signals": signals,
            })
    f["catalog_status"] = {
        "distribution": dict(sorted(cs_counter.items())),
        "by_layer": {
            li: dict(sorted(Counter(
                (r.get("catalog_status") or "NULL")
                for r in registry.values()
                if (r.get("layer_index") or "?") == li).items()))
            for li in sorted({(r.get("layer_index") or "?") for r in registry.values()})
        },
        "draft_with_serving_signal": sorted(draft_served, key=lambda r: r["asset_id"]),
        "draft_with_serving_signal_count": len(draft_served),
        "draft_serving_signal_breakdown": dict(sorted(Counter(
            s.split("=")[0].split(" rows")[0].strip()
            for r in draft_served for s in r["serving_signals"]).items())),
        "draft_total": cs_counter.get("DRAFT", 0),
        "serving_signal_definition": (
            "A DRAFT asset is listed here if ANY of these observable signals is present: "
            "is_active=true, provides_apis non-empty, health_probe non-empty, at least one "
            "asset_throughput row, or a non-null last_invoked_at. This is an enumeration of "
            "observed signals, not a judgement that the asset is reachable by a caller."
        ),
    }

    # ── source-coverage summary ───────────────────────────────────────────────
    f["source_coverage"] = {
        "universe_size": len(universe),
        "S1_asset_registry": len(registry),
        "S2_decorators_total": len(decorators),
        "S2_decorators_production": len(prod_dec),
        "S3_seed_ts": "UNKNOWN" if seed_unknown else len(seed),
        "S4_migrations_asset_ids": len(migrations),
        "S4_migration_files_touching_asset_registry": len(migration_files),
        "S5_asset_throughput_distinct_assets": len(throughput),
        "S6_capability_manifest_entries": (
            "UNKNOWN" if manifest_unknown else manifest_meta["actual_entry_count"]),
        "S6_capability_manifest_asset_shaped_ids": (
            "UNKNOWN" if manifest_unknown
            else len(manifest_meta.get("entries_with_asset_id_shape", []))),
    }

    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True, check=True).stdout.strip()
    except Exception as e:  # pragma: no cover
        head, branch = f"UNKNOWN ({e})", "UNKNOWN"

    doc = {
        "_meta": {
            "task": "M0-T1",
            "generated_at": _dt.datetime.now(_dt.timezone.utc)
                              .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "generator": "00_ARCHITECTURE/control/census.py",
            "git_head": head,
            "git_branch": branch,
            "database_access": "READ-ONLY (SELECT only; SET statement_timeout='45s'; autocommit)",
            "credential_handling": "DATABASE_URL read from platform/.env.local; never emitted",
            "db": db_meta,
            "migration_series": mig_series,
            "manifest": manifest_meta,
            "parse_errors": errors,
            "notes": notes,
            "sources": {
                "S1": "asset_registry (live DB)",
                "S2": "@register('<asset_id>') decorators under platform/python-sidecar/**.py",
                "S3": "platform/scripts/seed/asset_registry_seed.ts",
                "S4": "platform/migrations/**/*.sql containing INSERT/UPDATE/DELETE on asset_registry",
                "S5": "asset_throughput (live DB)",
                "S6": "00_ARCHITECTURE/CAPABILITY_MANIFEST.json",
            },
            "heuristics": [
                "S4 presence counts ONLY strong evidence — the token is used as an asset_id "
                "(`asset_id = 'x'`, `asset_id IN (...)`, `SET asset_id = 'x'`, or the first "
                "VALUES literal of an INSERT INTO asset_registry). Asset-shaped tokens found "
                "anywhere else in such a file are reported separately as weak matches and are "
                "NOT counted as presence: they are usually table names inside count_sql or "
                "prose in a comment. S4 can still under-match an id built by concatenation or "
                "hidden inside a dollar-quoted body.",
                "S2 production-vs-test split is by path: /tests/, /__tests__/, test_*.py and "
                "*_test.py are counted as test sites, everything else as production.",
                "Only platform/migrations/*.sql present in the working tree are scanned. "
                f"That tree holds {mig_series['numbered_sql_files_present']} numbered files at "
                f"{mig_series['distinct_numbers_present']} distinct numbers "
                f"spanning {mig_series['lowest_number']}..{mig_series['highest_number']}, "
                f"with {mig_series['numbers_in_range_absent_from_tree']} numbers in that range "
                "absent from it. S4 is therefore structurally incomplete by a large margin and "
                "an asset's absence from S4 is weak evidence of anything.",
            ],
        },
        "findings": f,
        "matrix": matrix,
        "migration_files": migration_files,
    }

    (CONTROL / "census.json").write_text(json.dumps(doc, indent=1, default=str))
    write_report(doc)
    print(f"census: universe={len(universe)} registry={len(registry)} "
          f"prod_decorators={len(prod_dec)} seed="
          f"{'UNKNOWN' if seed_unknown else len(seed)} migrations={len(migrations)} "
          f"throughput={len(throughput)} parse_errors={len(errors)}")
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# report
# ─────────────────────────────────────────────────────────────────────────────
def _mark(v) -> str:
    if v is True:
        return "Y"
    if v is False:
        return "·"
    return "?"


def write_report(doc: dict) -> None:
    m = doc["_meta"]
    f = doc["findings"]
    mx = doc["matrix"]
    L: list[str] = []
    A = L.append

    A("# NIRMĀṆA M0-T1 — Six-Source Asset Census")
    A("")
    A(f"**Generated:** {m['generated_at']}  ")
    A(f"**Generator:** `{m['generator']}`  ")
    A(f"**Git:** `{m['git_branch']}` @ `{m['git_head']}`  ")
    A(f"**Database access:** {m['database_access']}  ")
    A("**Status:** observations only. This document issues no verdict and certifies nothing "
      "(I16 / charter H7).")
    A("")
    A("## 0 — Sources")
    A("")
    A("| id | source | population |")
    A("|---|---|---|")
    sc = f["source_coverage"]
    A(f"| S1 | asset_registry (live DB) | {sc['S1_asset_registry']} assets |")
    A(f"| S2 | `@register('<id>')` decorators | {sc['S2_decorators_total']} ids "
      f"({sc['S2_decorators_production']} with a production site) |")
    A(f"| S3 | `platform/scripts/seed/asset_registry_seed.ts` | {sc['S3_seed_ts']} assets |")
    A(f"| S4 | migrations touching `asset_registry` | {sc['S4_migrations_asset_ids']} ids "
      f"across {sc['S4_migration_files_touching_asset_registry']} files |")
    A(f"| S5 | asset_throughput (live DB) | {sc['S5_asset_throughput_distinct_assets']} distinct "
      f"assets, {m['db']['asset_throughput_row_count']} rows |")
    A(f"| S6 | `CAPABILITY_MANIFEST.json` | {sc['S6_capability_manifest_entries']} entries, "
      f"{sc['S6_capability_manifest_asset_shaped_ids']} of them asset-shaped |")
    A("")
    A(f"**Union of all sources: {sc['universe_size']} distinct ids.**")
    A("")
    if m["parse_errors"]:
        A("### Parse failures (cells marked UNKNOWN, never guessed)")
        A("")
        for e in m["parse_errors"]:
            A(f"- {e}")
        A("")
    if m["notes"]:
        A("### Notes")
        A("")
        for n in m["notes"]:
            A(f"- {n}")
        A("")
    A("### Heuristics and their honest limits")
    A("")
    for h in m["heuristics"]:
        A(f"- {h}")
    A("")

    # S6 scope statement
    mm = m["manifest"]
    if mm.get("parsed"):
        A("### S6 scope — read this before reading the S6 column")
        A("")
        A(f"`CAPABILITY_MANIFEST.json` ({mm['actual_entry_count']} entries, declared "
          f"`entry_count`={mm['declared_entry_count']}, generated {mm['generated_at']}) is a "
          "catalogue of **canonical governance artefacts keyed by `canonical_id`** — document "
          "paths, versions and statuses. It is not keyed by `asset_id`. The number of manifest "
          f"entries whose id even has the shape of an asset_id is "
          f"**{len(mm.get('entries_with_asset_id_shape', []))}**.")
        A("")
        A("Consequence: the S6 column below is `·` for every asset, and that is a true "
          "measurement of the manifest's scope, not a defect in the assets. Treating S6 as an "
          "asset source would require the manifest to gain asset entries first — a decision "
          "outside this task.")
        A("")

    # presence matrix
    A("## 1 — Presence matrix")
    A("")
    A("`Y` = present · `·` = absent · `?` = source UNKNOWN (unparseable)")
    A("")
    A("| asset_id | S1 reg | S2 dec | S3 seed | S4 migr | S5 thru | S6 man | n | layer | "
      "catalog_status | is_active | target_table |")
    A("|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|---|:--:|---|")
    for aid in sorted(mx):
        r = mx[aid]
        s = r["sources"]
        reg = r["registry"] or {}
        dec_mark = _mark(s["S2_decorator"])
        if r["decorator"] and r["decorator"]["production_sites"] == 0:
            dec_mark = "t"  # test fixture only
        A("| `{a}` | {s1} | {s2} | {s3} | {s4} | {s5} | {s6} | {n} | {ly} | {cs} | {ia} | {tt} |"
          .format(a=aid, s1=_mark(s["S1_asset_registry"]), s2=dec_mark,
                  s3=_mark(s["S3_seed_ts"]), s4=_mark(s["S4_migrations"]),
                  s5=_mark(s["S5_asset_throughput"]), s6=_mark(s["S6_capability_manifest"]),
                  n=r["source_count_confirmed"],
                  ly=reg.get("layer_index") or reg.get("layer") or "—",
                  cs=reg.get("catalog_status") or "—",
                  ia=("Y" if reg.get("is_active") is True
                      else ("·" if reg.get("is_active") is False else "—")),
                  tt=f"`{reg.get('target_table')}`" if reg.get("target_table") else "—"))
    A("")
    A("`t` in the S2 column = the id is registered only from a test fixture, never from "
      "production code.")
    A("")

    # three-way diff
    d = f["three_way_diff"]
    A("## 2 — Three-way diff: registry vs decorators vs seed")
    A("")
    A("*Orphans live in the gaps.*")
    A("")
    c = d["counts"]
    A(f"- registry: **{c['registry']}**")
    A(f"- production decorators: **{c['decorators_production']}** "
      f"(+{c['decorators_test_only']} test-fixture-only ids)")
    A(f"- seed: **{c['seed']}**")
    A(f"- present in all three: **{len(d['in_all_three']) if isinstance(d['in_all_three'], list) else d['in_all_three']}**")
    A("")
    for key, title in [
        ("registry_only", "In registry ONLY — no writer, not in seed"),
        ("decorator_only", "Decorator ONLY — code registers it, catalogue has never heard of it"),
        ("seed_only", "Seed ONLY — seeded in the .ts, absent from live registry and from code"),
        ("registry_and_decorator_not_seed", "Registry + writer, but NOT in the seed file"),
        ("registry_and_seed_not_decorator", "Registry + seed, but NO production writer"),
        ("decorator_and_seed_not_registry", "Writer + seed, but NOT in the live registry"),
    ]:
        v = d.get(key)
        A(f"### {title}")
        A("")
        if v is None:
            A("UNKNOWN — the seed source could not be parsed.")
        elif not v:
            A("_none_")
        else:
            A(f"**{len(v)}:**")
            A("")
            for aid in v:
                extra = ""
                r = mx.get(aid, {})
                if r.get("registry"):
                    reg = r["registry"]
                    extra = (f" — {reg.get('catalog_status')}, is_active="
                             f"{reg.get('is_active')}, kind={reg.get('asset_kind')}, "
                             f"target_table={reg.get('target_table')}")
                elif r.get("decorator"):
                    st = r["decorator"]["sites"][0]
                    extra = f" — {st['file']}:{st['line']}"
                A(f"- `{aid}`{extra}")
        A("")
    if d["decorator_ids_test_fixtures_only"]:
        A("### Decorator ids that exist only in test fixtures")
        A("")
        for aid in d["decorator_ids_test_fixtures_only"]:
            A(f"- `{aid}`")
        A("")
    if d["decorator_ids_not_asset_shaped"]:
        A("### Decorator ids that do not match the asset-id shape "
          "`^(bg|ga|bo|ka|ph|mi)_[a-z0-9_]+$`")
        A("")
        for aid in d["decorator_ids_not_asset_shaped"]:
            r = mx.get(aid, {})
            site = (r.get("decorator") or {}).get("sites", [{}])[0]
            A(f"- `{aid}` — {site.get('file')}:{site.get('line')}")
        A("")

    # migration-only
    mo = f["migration_only_ids"]
    A("### Known ONLY to a migration (S4) — no registry row, no writer, no seed entry, "
      f"no throughput — {len(mo)}")
    A("")
    if not mo:
        A("_none_")
    else:
        A("| asset_id | ops | migration files |")
        A("|---|---|---|")
        for r in mo:
            A("| `{a}` | {o} | {fl} |".format(a=r["asset_id"], o=", ".join(r["ops"]),
                                              fl=", ".join(f"`{x}`" for x in r["files"])))
    A("")
    wk = f["migration_weak_matches_not_confirmed_elsewhere"]
    A(f"### S4 weak matches — asset-shaped tokens in an asset_registry migration that are NOT "
      f"used as an asset_id — {len(wk)}")
    A("")
    A("These are NOT counted as S4 presence. They are listed so the over-match is visible "
      "rather than silently absorbed; most are table names inside a `count_sql` body or "
      "identifiers mentioned in prose.")
    A("")
    if not wk:
        A("_none_")
    else:
        A("| token | in registry | migration files |")
        A("|---|:--:|---|")
        for r in wk:
            A("| `{a}` | {ir} | {fl} |".format(a=r["asset_id"], ir=_mark(r["also_in_registry"]),
                                               fl=", ".join(f"`{x}`" for x in r["files"])))
    A("")

    # registered but dead
    A("## 3 — Registered but dead")
    A("")
    A("A registry row with **no production `@register` writer** and **no `asset_throughput` "
      "row at all**.")
    A("")
    A("Caveat stated plainly: `asset_throughput` is live build state, not an append-only "
      "history. \"No throughput row now\" is evidence the asset has not built recently; it is "
      "not proof it never built. This census cannot distinguish the two.")
    A("")
    dead = f["registered_but_dead"]
    if not dead:
        A("_none_")
    else:
        A(f"**{len(dead)} assets:**")
        A("")
        A("| asset_id | catalog_status | is_active | has_writer flag | kind | storage | "
          "target_table | in seed | in migrations |")
        A("|---|---|:--:|:--:|---|---|---|:--:|:--:|")
        for r in dead:
            A("| `{a}` | {cs} | {ia} | {hw} | {k} | {st} | {tt} | {sd} | {mg} |".format(
                a=r["asset_id"], cs=r["catalog_status"] or "—",
                ia=_mark(r["is_active"]), hw=_mark(r["has_writer_flag"]),
                k=r["asset_kind"] or "—", st=r["storage_type"] or "—",
                tt=f"`{r['target_table']}`" if r["target_table"] else "—",
                sd=_mark(r["in_seed"]) if isinstance(r["in_seed"], bool) else "?",
                mg=_mark(r["in_migrations"])))
    A("")
    hw = f["has_writer_flag_vs_decorator"]
    A("### `has_writer` flag vs. an actual decorator (the registry's own claim, checked)")
    A("")
    A(f"- `has_writer=true` but no production decorator: **{len(hw['flag_true_no_production_decorator'])}** "
      + (", ".join(f"`{a}`" for a in hw["flag_true_no_production_decorator"]) or "_none_"))
    A(f"- decorator exists but `has_writer` is not true: **{len(hw['flag_false_or_null_but_decorator_exists'])}** "
      + (", ".join(f"`{a}`" for a in hw["flag_false_or_null_but_decorator_exists"]) or "_none_"))
    A(f"- `has_writer` NULL: **{len(hw['flag_null'])}** "
      + (", ".join(f"`{a}`" for a in hw["flag_null"]) or "_none_"))
    A("")

    # throughput on inactive
    A("## 4 — `asset_throughput` rows on inactive / retired / unregistered assets")
    A("")
    ti = f["throughput_on_inactive_or_retired"]
    for key, title in [
        ("not_in_registry", "Throughput rows for an asset_id with NO registry row"),
        ("is_active_false", "Throughput rows on `is_active = false` assets"),
        ("catalog_status_retired", "Throughput rows on `catalog_status = RETIRED` assets"),
        ("catalog_status_draft", "Throughput rows on `catalog_status = DRAFT` assets"),
    ]:
        rows = ti[key]
        A(f"### {title} — {len(rows)}")
        A("")
        if not rows:
            A("_none_")
        else:
            A("| asset_id | rows | states | last_built_at | rows_written total |")
            A("|---|--:|---|---|--:|")
            for r in rows:
                A("| `{a}` | {n} | {s} | {lb} | {rw} |".format(
                    a=r["asset_id"], n=r["throughput_rows"],
                    s=", ".join(x for x in (r["states"] or []) if x) or "—",
                    lb=r["last_built_at"] or "—",
                    rw=r["rows_written_total"] if r["rows_written_total"] is not None else "—"))
        A("")

    # collisions
    A("## 5 — `target_table` collisions (co-writer / multi-producer)")
    A("")
    A("These are the tables where the `(table × generation × natural-key partition)` invariant "
      "has to be checked, because more than one registered asset declares the same "
      "`target_table`. This census reports the collision; it does not evaluate the invariant.")
    A("")
    col = f["target_table_collisions"]
    if not col:
        A("_no table is claimed by more than one asset_")
    else:
        A(f"**{len(col)} tables claimed by more than one asset:**")
        A("")
        A("| target_table | n | asset_ids | layers | with writer | active | catalog_statuses |")
        A("|---|--:|---|---|---|---|---|")
        for c2 in col:
            A("| `{t}` | {n} | {ids} | {ly} | {w} | {a} | {cs} |".format(
                t=c2["target_table"], n=c2["asset_count"],
                ids=", ".join(f"`{i}`" for i in c2["asset_ids"]),
                ly=", ".join(c2["layers"]),
                w=", ".join(f"`{i}`" for i in c2["with_production_writer"]) or "—",
                a=", ".join(f"`{i}`" for i in c2["active"]) or "—",
                cs=", ".join(c2["catalog_statuses"])))
    A("")
    mam = f["multi_asset_writer_modules"]
    A(f"### Writer modules that register more than one asset_id — {len(mam)}")
    A("")
    if not mam:
        A("_none_")
    else:
        for r in mam:
            A(f"- `{r['file']}` → {', '.join(f'`{i}`' for i in r['asset_ids'])}")
    A("")
    tn = f["target_table_null_or_missing"]
    A(f"### Registry rows with no `target_table` — {len(tn)}")
    A("")
    A(", ".join(f"`{a}`" for a in tn) if tn else "_none_")
    A("")

    # prefix
    A("## 6 — Prefix conformance")
    A("")
    A("`bg_`→L0 · `ga_`→L1 · `bo_`→L2 · `ka_`→L3 · `ph_`→L4 · `mi_`→L5 (CLAUDE.md §N.1).")
    A("")
    pc = f["prefix_conformance"]
    A(f"- checked: **{pc['checked']}** · fully conforming: **{pc['fully_conforming']}**")
    A("- prefix distribution: " +
      ", ".join(f"`{k}_` {v}" for k, v in pc["prefix_distribution"].items()))
    A("")
    A("Four non-conformance classes, kept apart on purpose — a wrong layer and a missing "
      "`layer_index` are different defects and must not be totalled together.")
    A("")
    for key in ("unrecognised_prefix", "layer_contradiction", "layer_index_format",
                "layer_index_null"):
        rows = pc[key]
        A(f"### {key} — {len(rows)}")
        A("")
        A(f"_{pc['class_definitions'][key]}_")
        A("")
        if not rows:
            A("_none_")
        else:
            keys = sorted({k for r in rows for k in r if k != "asset_id"})
            A("| asset_id | " + " | ".join(keys) + " |")
            A("|---|" + "---|" * len(keys))
            for r in rows:
                A(f"| `{r['asset_id']}` | " +
                  " | ".join(str(r.get(k)) if r.get(k) is not None else "NULL" for k in keys)
                  + " |")
        A("")

    # catalog status
    A("## 7 — `catalog_status` distribution, and which DRAFT assets are served")
    A("")
    cs = f["catalog_status"]
    A("| catalog_status | count |")
    A("|---|--:|")
    for k, v in cs["distribution"].items():
        A(f"| {k} | {v} |")
    A("")
    A("### By layer")
    A("")
    all_st = sorted({s for d2 in cs["by_layer"].values() for s in d2})
    A("| layer | " + " | ".join(all_st) + " | total |")
    A("|---|" + "--:|" * (len(all_st) + 1))
    for li, d2 in cs["by_layer"].items():
        A(f"| {li} | " + " | ".join(str(d2.get(s, 0)) for s in all_st) + " | "
          + str(sum(d2.values())) + " |")
    A("")
    A("### DRAFT assets carrying a serving signal")
    A("")
    A(cs["serving_signal_definition"])
    A("")
    ds = cs["draft_with_serving_signal"]
    A(f"**{len(ds)} of {cs['draft_total']} DRAFT assets carry at least one serving signal.**")
    A("")
    A("Signal breakdown (an asset can carry more than one):")
    A("")
    for k, v in cs["draft_serving_signal_breakdown"].items():
        A(f"- `{k}`: {v}")
    A("")
    if ds:
        A("| asset_id | layer | kind | signals |")
        A("|---|---|---|---|")
        for r in ds:
            A("| `{a}` | {l} | {k} | {s} |".format(
                a=r["asset_id"], l=r["layer_index"] or "—", k=r["asset_kind"] or "—",
                s="; ".join(r["serving_signals"])))
        A("")

    A("## 8 — What this census does NOT establish")
    A("")
    A("- It does not verify that any asset's rows are correct, complete, or current.")
    A("- It does not check the `(table × generation × natural-key partition)` invariant — it "
      "only names the tables where that invariant is load-bearing (§5).")
    A("- It cannot see migrations that are not files in the working tree, nor asset ids a "
      "migration builds by string concatenation (§0 heuristics).")
    A("- It cannot distinguish \"never built\" from \"built once and the throughput row was "
      "later removed\" (§3).")
    A("- It certifies nothing. Verification of this artefact belongs to PARĪKṢAKA (I16).")
    A("")
    (CONTROL / "CENSUS_REPORT.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    sys.exit(main())
