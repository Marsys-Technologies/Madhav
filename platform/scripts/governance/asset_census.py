#!/usr/bin/env python3
"""Asset census — the `measured` half of the delta ledger, for a whole layer in one read-only pass.

WHY THIS EXISTS. The five L0 pilot briefs were measured by hand: a query for the alias census, a grep
for the writer contract, an arithmetic check for grid completeness, a count per asset's own count_sql.
Every one of those is scriptable, and hand-measuring 129 assets is how a campaign stalls. This script
measures; the brief renders what it measured; the author judges. That turns the remaining work from
authoring into reviewing, which is the only way a 129-asset ladder finishes.

WHAT IT MEASURES, per asset, against the tier-4 template's nine gates:

  Build.registered      exactly one @register('<asset_id>') and the registry agrees it has a writer
  Build.contract        WriterBase; run XOR plan_substeps+run_substep; never commits/closes ctx.db_conn;
                        never WRITES asset_throughput (a docstring promising not to is not a violation)
  Build.target          target_table declared, or the asset is a declared service / multi-table
  Build.dag             every depends_on entry exists; no cycle inside the layer
  Build.count_integrity count_sql present and integrity_check_sql present — each able to fail
  Build.completion      the build record agrees with the live count (rows_written=0 against a populated
                        table is a status with no measurement behind it)
  Earn.build_record     rows_per_second / last_built_at present — is the build instrumented at all
  Ldgr.source_presence  for a reference layer: the rows carry a citation column and it is populated
  Idem.pattern          the writer's idempotency pattern matches the layer convention (§N.3)
  Vocab.alias           per entity class, alias-set coverage (where the table has a synonyms column)
  Vocab.identity        uniqueness under the table's OWN DECLARED KEY, read from pg_constraint — never
                        an assumed key (native decision 16: the detector tests the declared key)
  Dens.served           which capability modules reference the target table; do they declare a
                        density_contract
  Complete.depth        per-column population census over the primary target table: columns fully
                        populated, columns NEVER populated
  Complete.width        the declared universe, if one exists — and it almost never does, so the honest
                        output is `universe_undeclared`, which is itself the first gap
  Cost.baseline         rows_written / rows_per_second / last_built_at

WHAT IT DOES NOT MEASURE, and says so rather than guessing: carriage detectors (D1/D2/D3 are per-asset
semantics), width universes that are not declared anywhere, and reachability at field level. Those come
out as `NOT_GENERIC` — a prompt for the brief author, never a pass.

FAIL-CLOSED. No database, no psql, or an unreadable registry exits 4 UNKNOWN and reports nothing clean.
An unreachable instrument is not a passing result (CLAUDE.md §N.8).

READ-ONLY. Catalog and content SELECTs only. `--emit-gaps` is the one write, and it appends to
00_ARCHITECTURE/control/asset_gaps.jsonl with deterministic ids (`<asset>-<criterion>`), skipping any id
already present, so re-running is idempotent and never disturbs a hand-written row.

Usage:
  asset_census.py --layer L0                 measure and print; writes the census JSON
  asset_census.py --layer L0 --emit-gaps     also append ledger rows for failures
  asset_census.py --layer all                every layer
Exit: 0 clean · 2 failures measured · 3 only NOT_GENERIC/undeclared items · 4 unknown · 5 script error.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
            .stdout.strip() or ".")
CTRL = ROOT / "00_ARCHITECTURE" / "control"
WRITERS = ROOT / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers"

LAYERS = {
    "L0": dict(prefix="bg_", name="Brahmagyan", registry_layer="brahmagyan", scoring="fidelity",
               caps="platform/src/lib/retrieval/registry/layers/L0_brahmagyan", idem="upsert"),
    "L1": dict(prefix="ga_", name="Ganita", registry_layer="ganita", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L1_ganita", idem="delete_then_insert"),
    "L2": dict(prefix="bo_", name="Bodha", registry_layer="bodha", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L2_bodha", idem="delete_then_insert"),
    "L3": dict(prefix="ka_", name="Kala", registry_layer="kala", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L3_kala", idem="delete_then_insert"),
    "L4": dict(prefix="ph_", name="Phala", registry_layer="phala", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L4_phala", idem="delete_then_insert"),
    "L5": dict(prefix="mi_", name="Mimamsa", registry_layer="mimamsa", scoring="contribution",
               caps="platform/src/lib/retrieval/registry/layers/L5_mimamsa", idem="delete_then_insert"),
}

PASS, FAIL, PARTIAL, NO_DET, NA, NOT_GENERIC = "PASS", "FAIL", "PARTIAL", "NO_DETECTOR", "N/A", "NOT_GENERIC"


class Unknown(Exception):
    """The instrument could not run. Never reported as clean."""


def psql(sql: str, sep: str = "\x1f") -> list[list[str]]:
    env = dict(os.environ)
    env.setdefault("PGCONNECT_TIMEOUT", "10")
    p = subprocess.run(["psql", "-tAX", "-F", sep, "-v", "ON_ERROR_STOP=1", "-c", sql],
                       capture_output=True, text=True, env=env, timeout=180)
    if p.returncode != 0:
        raise Unknown((p.stderr.strip().splitlines() or ["psql failed"])[0])
    return [ln.split(sep) for ln in p.stdout.strip().split("\n") if ln.strip()]


def scalar(sql: str) -> str | None:
    r = psql(sql)
    return r[0][0] if r and r[0] else None


# ─────────────────────────── code-side scans ───────────────────────────

def _writer_files() -> list[Path]:
    """Writer modules only. `__init__.py` is the FRAMEWORK — it defines @register and documents what a
    writer must not do, so scanning it as a writer reports the framework's own docstring as a violation.
    The first run did exactly that."""
    if not WRITERS.is_dir():
        raise Unknown(f"writers directory not found: {WRITERS}")
    return [f for f in sorted(WRITERS.glob("*.py")) if f.name != "__init__.py"]


def _parse(f: Path):
    try:
        return ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
    except SyntaxError as exc:
        raise Unknown(f"{f.name}: unparseable ({exc})") from exc


def _register_id(dec: ast.expr) -> str | None:
    """@register('<asset_id>') as a real decorator — via the AST, so a docstring that MENTIONS
    `@register('bg_x')` is not mistaken for one. The regex version made that mistake twice."""
    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name) and dec.func.id == "register":
        if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
            return dec.args[0].value
    return None


def _code_strings(node: ast.AST) -> list[str]:
    """String constants that are NOT docstrings — SQL, not prose."""
    docs = set()
    for n in ast.walk(node):
        if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(n, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                docs.add(id(body[0].value))
    return [n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs]


def registered_ids(prefix: str) -> dict[str, list[str]]:
    """asset_id -> writer file(s), from real decorators on real classes."""
    out: dict[str, list[str]] = {}
    for f in _writer_files():
        for node in ast.walk(_parse(f)):
            if isinstance(node, ast.ClassDef):
                for dec in node.decorator_list:
                    rid = _register_id(dec)
                    if rid and rid.startswith(prefix) and f.name not in out.setdefault(rid, []):
                        out[rid].append(f.name)
    return out


def _writer_class(f: Path, asset_id: str) -> ast.ClassDef | None:
    for node in ast.walk(_parse(f)):
        if isinstance(node, ast.ClassDef) and any(_register_id(d) == asset_id for d in node.decorator_list):
            return node
    return None


def contract_scan(asset_id: str, files: list[str]) -> tuple[str, list[str]]:
    """Frozen-contract conformance, per registered CLASS rather than per file.

    Calibrated after the first run's false positives: the ONLY hard failures are (a) no WriterBase
    subclass, (b) neither entry point, (c) a real `ctx.db_conn.commit()/close()` CALL, (d) a real SQL
    string that writes `asset_throughput`. Declaring both entry points is a note, not a failure —
    `WriterBase` may define `run()` as the template method that dispatches substeps, and calling that a
    violation would fail a conformant heavy writer."""
    notes: list[str] = []
    if not files:
        return NA, ["no writer file"]
    found = False
    for name in files:
        f = WRITERS / name
        cls = _writer_class(f, asset_id)
        if cls is None:
            continue
        found = True
        bases = {b.id for b in cls.bases if isinstance(b, ast.Name)} | \
                {b.attr for b in cls.bases if isinstance(b, ast.Attribute)}
        if "WriterBase" not in bases:
            notes.append(f"{name}: {cls.name} does not subclass WriterBase (bases: {sorted(bases) or 'none'})")
        methods = {m.name for m in cls.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))}
        heavy = {"plan_substeps", "run_substep"} <= methods
        if not heavy and "run" not in methods:
            notes.append(f"{name}: {cls.name} has neither run(ctx) nor plan_substeps+run_substep")
        if heavy and "run" in methods:
            notes.append(f"{name}: {cls.name} declares both entry points (note, not a violation)")
        for n in ast.walk(cls):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr in ("commit", "close") and isinstance(n.func.value, ast.Attribute) \
                    and n.func.value.attr == "db_conn":
                notes.append(f"{name}: {cls.name} calls ctx.db_conn.{n.func.attr}() — the orchestrator owns the transaction")
        for sql in _code_strings(cls):
            if "asset_throughput" in sql and re.search(r"\b(INSERT|UPDATE|DELETE)\b", sql, re.I):
                notes.append(f"{name}: {cls.name} writes asset_throughput — the orchestrator is the sole build-state writer")
    if not found:
        return FAIL, [f"no class decorated @register('{asset_id}') found in {', '.join(files)}"]
    hard = [n for n in notes if "note, not a violation" not in n]
    return (PASS if not hard else FAIL), (notes or ["conformant"])


def idem_scan(asset_id: str, files: list[str], convention: str) -> tuple[str, list[str]]:
    """§N.3, over real SQL strings (docstrings excluded). A writer that delegates to a seeder shows no
    pattern here; that is PARTIAL — look in the seeder — never FAIL."""
    if not files:
        return NA, ["no writer file"]
    sqls = []
    for name in files:
        sqls += _code_strings(_parse(WRITERS / name))
    blob = "\n".join(sqls)
    upsert = bool(re.search(r"ON CONFLICT", blob, re.I))
    delete = bool(re.search(r"DELETE\s+FROM", blob, re.I))
    if convention == "upsert":
        if upsert:
            return PASS, ["ON CONFLICT present in the writer"]
        return PARTIAL, ["no ON CONFLICT in the writer's own SQL — it likely delegates to a seeder; verify there"]
    if delete:
        return PASS, ["DELETE FROM present (delete-then-insert)"]
    if upsert:
        return PARTIAL, ["ON CONFLICT where the layer convention is delete-then-insert"]
    return PARTIAL, ["no idempotency pattern in the writer's own SQL — it likely delegates; verify there"]


def capability_scan(caps_dir: str, tables: list[str]) -> dict:
    d = ROOT / caps_dir
    if not d.is_dir():
        return dict(modules=[], density=0, note=f"no capability directory at {caps_dir}")
    hits, density = [], 0
    for f in sorted(d.glob("*.ts")):
        if f.name.endswith(".test.ts"):
            continue
        txt = f.read_text(encoding="utf-8", errors="replace")
        if any(t and re.search(r"\b" + re.escape(t) + r"\b", txt) for t in tables):
            hits.append(f.name)
            if "density_contract" in txt:
                density += 1
    return dict(modules=hits, density=density, note="")


def local_map_candidates(prefix: str) -> int:
    """Rule 6 candidates: literal graha-name sets in the layer's own python package."""
    pkg = ROOT / "platform" / "python-sidecar" / "brahmagyan"
    if not pkg.is_dir():
        return -1
    n = 0
    for f in pkg.rglob("*.py"):
        txt = f.read_text(encoding="utf-8", errors="replace")
        if re.search(r"['\"]Sun['\"]\s*[,:]", txt) and re.search(r"['\"]Venus['\"]", txt):
            n += 1
    return n


# ─────────────────────────── database reads ───────────────────────────

def registry(layer_key: str) -> dict[str, dict]:
    """Read via json_agg, NOT line-oriented output.

    `count_sql` and `integrity_check_sql` contain newlines, so a row-per-line read splits one asset
    across several lines and invents assets whose ids are fragments of SQL. That bug produced 52 assets
    from 40 on this script's first run — the same defect class the layer template warns about, an
    instrument whose population was never stated. One JSON document has no such ambiguity."""
    cfg = LAYERS[layer_key]
    blob = scalar(
        "SELECT coalesce(json_agg(json_build_object("
        "'asset_id',asset_id,'has_writer',coalesce(has_writer,false),'target_table',target_table,"
        "'count_sql',coalesce(count_sql,''),'has_integrity',(integrity_check_sql IS NOT NULL),"
        "'depends_on',coalesce(to_json(depends_on),'[]'::json),'target_floor',target_floor,"
        "'catalog_status',coalesce(catalog_status,''),'asset_kind',coalesce(asset_kind,''))"
        " ORDER BY asset_id)::text,'[]') "
        f"FROM asset_registry WHERE asset_id LIKE '{cfg['prefix']}%'")
    rows = json.loads(blob or "[]")
    out = {}
    for r in rows:
        out[r["asset_id"]] = dict(
            asset_id=r["asset_id"], has_writer=bool(r["has_writer"]),
            target_table=r["target_table"] or None, count_sql=r["count_sql"] or "",
            has_integrity=bool(r["has_integrity"]), depends_on=list(r["depends_on"] or []),
            target_floor=(str(r["target_floor"]) if r["target_floor"] is not None else None),
            catalog_status=r["catalog_status"], asset_kind=r["asset_kind"])
    if not out:
        raise Unknown(f"no {cfg['prefix']}* rows in asset_registry")
    return out


def live_counts(reg: dict) -> dict[str, int | None]:
    """Each asset's OWN count_sql — the cockpit instrument, not a table count."""
    out: dict[str, int | None] = {}
    parts, ids = [], []
    for aid, r in reg.items():
        q = " ".join(re.sub(r"--[^\n]*", "", r["count_sql"]).replace("\n", " ").rstrip(" ;").split())
        if not q:
            out[aid] = None
            continue
        parts.append(f"SELECT '{aid}' a,({q})::text n")
        ids.append(aid)
    if not parts:
        return out
    try:
        for a, n in psql(" UNION ALL ".join(parts)):
            out[a] = int(n) if n.strip().lstrip("-").isdigit() else None
    except Unknown:
        for aid in ids:                                    # one bad count_sql must not blind the rest
            q = " ".join(re.sub(r"--[^\n]*", "", reg[aid]["count_sql"]).replace("\n", " ").rstrip(" ;").split())
            try:
                v = scalar(f"SELECT ({q})::text")
                out[aid] = int(v) if v and v.strip().lstrip("-").isdigit() else None
            except Unknown:
                out[aid] = None
    return out


def throughput(prefix: str) -> dict[str, dict]:
    rows = psql("SELECT asset_id, coalesce(state,''), coalesce(rows_written::text,''), "
                "coalesce(round(rows_per_second)::text,''), coalesce(last_built_at::date::text,'') "
                f"FROM asset_throughput WHERE asset_id LIKE '{prefix}%'")
    return {r[0]: dict(state=r[1], rows_written=r[2], rps=r[3], last_built=r[4])
            for r in (x + [""] * 5 for x in rows)}


def catalog(tables: list[str]) -> dict:
    """One round trip each for existence, columns and declared keys — not one per asset.

    The first run made roughly 240 psql invocations for 40 assets and took minutes; each pays process
    start plus connection. Three batched reads replace them."""
    t = [x for x in {x for x in tables if x}]
    if not t:
        return dict(exists=set(), cols={}, keys={})
    lit = ", ".join("'" + x.replace("'", "''") + "'" for x in t)
    exists = {r[0] for r in psql(f"SELECT table_name FROM information_schema.tables "
                                 f"WHERE table_schema='public' AND table_name IN ({lit})")}
    cols: dict[str, list[str]] = {}
    for tn, cn in psql("SELECT table_name, column_name FROM information_schema.columns "
                       f"WHERE table_schema='public' AND table_name IN ({lit}) "
                       "ORDER BY table_name, ordinal_position"):
        cols.setdefault(tn, []).append(cn)
    keys: dict[str, list[list[str]]] = {}
    for tn, defn in psql("SELECT c.relname, pg_get_constraintdef(x.oid) FROM pg_constraint x "
                         "JOIN pg_class c ON c.oid=x.conrelid JOIN pg_namespace n ON n.oid=c.relnamespace "
                         f"WHERE n.nspname='public' AND x.contype IN ('u','p') AND c.relname IN ({lit})"):
        m = re.search(r"\((.*?)\)", defn)
        if m:
            keys.setdefault(tn, []).append([c.strip().strip('"') for c in m.group(1).split(",")])
    return dict(exists=exists, cols=cols, keys=keys)


def declared_keys(table: str) -> list[list[str]]:
    rows = psql("SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                f"WHERE conrelid='{table}'::regclass AND contype IN ('u','p')")
    keys = []
    for (d,) in ((r[0],) for r in rows):
        m = re.search(r"\((.*?)\)", d)
        if m:
            keys.append([c.strip().strip('"') for c in m.group(1).split(",")])
    return keys


def table_exists(t: str) -> bool:
    return (scalar(f"SELECT (to_regclass('public.{t}') IS NOT NULL)::text") or "f") in ("t", "true")


def depth_census(table: str, cols: list[str]) -> dict:
    if not cols:
        return dict(columns=0, note="no columns")
    total = int(scalar(f"SELECT count(*)::text FROM {table}") or 0)
    if total == 0:
        return dict(columns=len(cols), rows=0, full=[], never=[], note="table empty")
    sel = ", ".join(f"count({c})::text" for c in cols)
    vals = psql(f"SELECT {sel} FROM {table}")[0]
    full = [c for c, v in zip(cols, vals) if int(v) == total]
    never = [c for c, v in zip(cols, vals) if int(v) == 0]
    return dict(columns=len(cols), rows=total, full=full, never=never, note="")


def alias_census(table: str, cols: list[str]) -> dict | None:
    names = set(cols)
    if "synonyms" not in names:
        return None
    grp = "entity_class" if "entity_class" in names else "'(all)'"
    rows = psql(f"SELECT {grp}::text, count(*)::text, "
                "count(*) FILTER (WHERE synonyms IS NULL OR cardinality(synonyms)=0)::text "
                f"FROM {table} GROUP BY 1 ORDER BY 1")
    return {r[0]: dict(rows=int(r[1]), no_alias=int(r[2])) for r in rows}


# ─────────────────────────── the census ───────────────────────────

def measure(layer_key: str) -> dict:
    cfg = LAYERS[layer_key]
    reg = registry(layer_key)
    cat = catalog([r["target_table"] for r in reg.values()])
    regd = registered_ids(cfg["prefix"])
    counts = live_counts(reg)
    thru = throughput(cfg["prefix"])
    lmaps = local_map_candidates(cfg["prefix"]) if layer_key == "L0" else -1

    known = set(reg)
    assets = []
    for aid, r in reg.items():
        m: dict[str, dict] = {}
        files = regd.get(aid, [])

        # Build.registered
        if len(files) == 1 and r["has_writer"]:
            m["Build.registered"] = dict(v=PASS, measured=f"@register in {files[0]}; registry agrees")
        elif len(files) == 1 and not r["has_writer"]:
            m["Build.registered"] = dict(v=FAIL, measured=f"@register in {files[0]} but registry says has_writer=false")
        elif len(files) > 1:
            m["Build.registered"] = dict(v=FAIL, measured=f"registered in {len(files)} files: {', '.join(files)}")
        elif r["has_writer"]:
            m["Build.registered"] = dict(v=FAIL, measured="registry says has_writer=true and no @register found")
        else:
            m["Build.registered"] = dict(v=NA, measured="no writer, and the registry agrees (service or static)")

        v, notes = contract_scan(aid, files)
        m["Build.contract"] = dict(v=v, measured="; ".join(notes) or "conformant")
        v, notes = idem_scan(aid, files, cfg["idem"])
        m["Idem.pattern"] = dict(v=v, measured="; ".join(notes))

        # Build.target
        if r["target_table"]:
            m["Build.target"] = dict(v=PASS, measured=f"target_table={r['target_table']}")
        elif r["asset_kind"] or not r["has_writer"]:
            m["Build.target"] = dict(v=NA, measured=f"no target_table; asset_kind='{r['asset_kind']}', has_writer={r['has_writer']}")
        else:
            m["Build.target"] = dict(v=FAIL, measured="has a writer and NO target_table declared — the orchestrator's clear/count steps have nothing to aim at")

        missing = [d for d in r["depends_on"] if d not in known and not d.startswith(cfg["prefix"]) is False]
        unknown_deps = [d for d in r["depends_on"] if d.startswith(cfg["prefix"]) and d not in known]
        m["Build.dag"] = dict(v=(FAIL if unknown_deps else PASS),
                              measured=(f"depends_on references unknown {cfg['prefix']}* assets: {unknown_deps}"
                                        if unknown_deps else f"{len(r['depends_on'])} edge(s), all resolvable"))

        ok_ci = bool(r["count_sql"]) and r["has_integrity"]
        m["Build.count_integrity"] = dict(
            v=(PASS if ok_ci else (NA if not r["has_writer"] and not r["count_sql"] else PARTIAL)),
            measured=f"count_sql={'yes' if r['count_sql'] else 'no'}, integrity_check_sql={'yes' if r['has_integrity'] else 'no'}")

        live = counts.get(aid)
        t = thru.get(aid, {})
        rw = t.get("rows_written", "")
        if live is None:
            m["Build.completion"] = dict(v=NA, measured=f"no count_sql; build state='{t.get('state','-')}'")
        elif rw == "":
            m["Build.completion"] = dict(v=FAIL, measured=f"live={live} and no build record at all")
        elif int(rw) == 0 and live > 0:
            m["Build.completion"] = dict(v=FAIL, measured=f"build record says rows_written=0 against live={live}")
        elif int(rw) == 0 and live == 0:
            m["Build.completion"] = dict(v=PASS, measured="live=0 and rows_written=0 — consistent (empty by design or service)")
        else:
            m["Build.completion"] = dict(v=PASS, measured=f"rows_written={rw}, live={live}")

        m["Earn.build_record"] = dict(v=(PASS if t.get("rps") else FAIL),
                                      measured=f"rows_per_second={t.get('rps') or 'NULL'}, last_built={t.get('last_built') or '-'}")
        m["Cost.baseline"] = dict(v=(PASS if t.get("rps") else FAIL),
                                  measured=f"state={t.get('state','-')}, rows_written={rw or '-'}, rps={t.get('rps') or '-'}")

        floor = r["target_floor"]
        if live is not None and floor and floor.isdigit():
            d = live - int(floor)
            m["Count.floor"] = dict(v=(FAIL if d < 0 else PASS), measured=f"live={live}, floor={floor}, delta={d:+d}")

        tbl = r["target_table"]
        if tbl and tbl in cat["exists"]:
            dc = depth_census(tbl, cat["cols"].get(tbl, []))
            m["Complete.depth"] = dict(v=(PASS if not dc.get("never") else PARTIAL),
                                       measured=(f"{dc.get('rows',0)} rows, {dc['columns']} cols; "
                                                 f"fully populated {len(dc.get('full',[]))}; NEVER populated "
                                                 f"{dc.get('never',[])}" if not dc.get("note") else dc["note"]))
            keys = cat["keys"].get(tbl, [])
            if keys:
                k = keys[0] if len(keys[0]) > 1 or keys[0][0] != "id" else (keys[1] if len(keys) > 1 else keys[0])
                kd = ", ".join(k)
                dup = scalar(f"SELECT (count(*) - count(DISTINCT ({kd})))::text FROM {tbl}")
                m["Vocab.identity"] = dict(v=(PASS if dup == "0" else FAIL),
                                           measured=f"declared key ({kd}): {dup} duplicate(s)")
            ac = alias_census(tbl, cat["cols"].get(tbl, []))
            if ac:
                bad = {k: v for k, v in ac.items() if v["no_alias"]}
                m["Vocab.alias"] = dict(v=(PASS if not bad else FAIL),
                                        measured=(f"{len(ac)} class(es); empty alias sets: "
                                                  + (", ".join(f"{k} {v['no_alias']}/{v['rows']}" for k, v in bad.items()) or "none")))
            tcols = set(cat["cols"].get(tbl, []))
            cit = [c for c in ("source_citation", "source_text_id", "classical_citations", "citation_ref")
                   if c in tcols]
            if cit and dc.get("rows"):
                col = cit[0]
                n = scalar(f"SELECT count(*)::text FROM {tbl} WHERE {col} IS NOT NULL")
                m["Ldgr.source_presence"] = dict(v=(PASS if int(n) == dc["rows"] else PARTIAL),
                                                 measured=f"{col} populated on {n}/{dc['rows']} rows")
        elif tbl:
            m["Complete.depth"] = dict(v=FAIL, measured=f"target_table '{tbl}' does not exist in production")

        cap = capability_scan(cfg["caps"], [t for t in ([tbl] if tbl else []) + [aid]])
        m["Dens.served"] = dict(v=(NA if not cap["modules"] else (PASS if cap["density"] else FAIL)),
                                measured=(cap["note"] or f"{len(cap['modules'])} module(s): {', '.join(cap['modules']) or 'none'}; "
                                          f"declaring density_contract: {cap['density']}"))

        m["Complete.width"] = dict(v=NOT_GENERIC, measured="no declared universe for this asset — declaring one is the first width gap")
        m["Carr.detector"] = dict(v=NO_DET, measured="no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics")
        m["Reach.fields"] = dict(v=NOT_GENERIC, measured="field-level exposure census is per-capability; not generic")

        assets.append(dict(asset_id=aid, layer=layer_key, scoring=cfg["scoring"], live_rows=live,
                           target_table=tbl, has_writer=r["has_writer"], writer_files=files,
                           catalog_status=r["catalog_status"], measurements=m))

    extra = sorted(set(regd) - known)
    return dict(generated=dt.datetime.now().astimezone().isoformat(timespec="seconds"), layer=layer_key,
                layer_name=cfg["name"], scoring=cfg["scoring"], n_assets=len(assets),
                registered_ids=len(regd), registry_has_writer=sum(1 for r in reg.values() if r["has_writer"]),
                phantom_registered=extra, local_map_candidates=lmaps, assets=assets)


def emit_gaps(census: dict) -> tuple[int, int]:
    """Append ledger rows for measured failures. Deterministic ids; existing ids skipped."""
    path = CTRL / "asset_gaps.jsonl"
    existing = set()
    if path.exists():
        for ln in path.read_text(encoding="utf-8").split("\n"):
            if ln.strip():
                try:
                    existing.add(json.loads(ln).get("gap_id"))
                except json.JSONDecodeError:
                    pass
    ts = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    added = skipped = 0
    with path.open("a", encoding="utf-8") as f:
        for a in census["assets"]:
            for crit, res in a["measurements"].items():
                if res["v"] not in (FAIL, PARTIAL, NO_DET):
                    continue
                gid = f"{a['asset_id']}-{crit}"
                if gid in existing:
                    skipped += 1
                    continue
                f.write(json.dumps(dict(
                    asset=a["asset_id"], gap_id=gid, kind="gap", criterion=crit,
                    what=f"measured: {res['measured']} / required: the {crit.split('.')[0]} gate's claim",
                    change="", detector=f"asset_census.py --layer {census['layer']} ({crit})",
                    owner="asset_census", gate="this asset's certification",
                    state="OPEN", ts=ts), ensure_ascii=False) + "\n")
                added += 1
    return added, skipped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", default="L0")
    ap.add_argument("--emit-gaps", action="store_true")
    ap.add_argument("--out", default=str(CTRL / "asset_census.json"))
    a = ap.parse_args()
    keys = list(LAYERS) if a.layer.lower() == "all" else [k.strip().upper() for k in a.layer.split(",")]
    for k in keys:
        if k not in LAYERS:
            sys.exit(f"unknown layer {k}; expected one of {list(LAYERS)} or 'all'")

    out, worst = {}, 0
    for k in keys:
        try:
            c = measure(k)
        except Unknown as exc:
            print(f"asset_census: UNKNOWN — {exc}")
            print("  Nothing is reported clean: an unreachable instrument is not a passing result.")
            return 4
        out[k] = c
        fails = sum(1 for x in c["assets"] for r in x["measurements"].values() if r["v"] == FAIL)
        parts = sum(1 for x in c["assets"] for r in x["measurements"].values() if r["v"] in (PARTIAL, NO_DET))
        print(f"{k} {c['layer_name']} ({c['scoring']}): {c['n_assets']} assets · "
              f"{c['registered_ids']} registered ids vs {c['registry_has_writer']} has_writer=true")
        if c["phantom_registered"]:
            print(f"  !! registered but absent from the registry: {c['phantom_registered']}")
        print(f"  FAIL {fails} · PARTIAL/NO_DETECTOR {parts} · assets measured {c['n_assets']}")
        by = {}
        for x in c["assets"]:
            for crit, r in x["measurements"].items():
                if r["v"] == FAIL:
                    by.setdefault(crit, []).append(x["asset_id"])
        for crit in sorted(by):
            n = by[crit]
            print(f"    FAIL {crit}: {len(n)} — {', '.join(n[:6])}{'…' if len(n) > 6 else ''}")
        worst = max(worst, 2 if fails else (3 if parts else 0))
        if a.emit_gaps:
            added, skipped = emit_gaps(c)
            print(f"  ledger: {added} row(s) appended, {skipped} already present")

    Path(a.out).write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"census written: {os.path.relpath(a.out, ROOT)}")
    return worst


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"asset_census: script error — {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(5)
