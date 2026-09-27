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
# R57/P3: ledger directory is overridable so a sandbox --emit-gaps run never touches the
# production ledgers (NIKASHA_CONTROL_DIR; ported from harness/asset_census_closing.py).
CTRL = Path(os.environ.get("NIKASHA_CONTROL_DIR", str(ROOT / "00_ARCHITECTURE" / "control")))
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
# R41: a per-check exception (timeout, missing relation, malformed key) degrades to ERRORED for
# THAT check/asset — never in FAILING (never opens a gap the detector itself couldn't measure)
# nor in CLOSABLE (never closes one either); an existing open gap is left exactly as it was,
# because "the detector broke" and "the defect is fixed" are different facts.
ERRORED = "ERRORED"

# R40: the psql subprocess timeout was hardcoded at 180s, which is shorter than a full-table
# duplicate scan on the estate's largest table (kala_field, 10.3M rows) can take — making the L3
# and `--layer all` census unrunnable on production. Configurable via env so an operator pointed
# at a much larger table than the ones this script was calibrated against can raise it without a
# code change.
PSQL_TIMEOUT_SECONDS = int(os.environ.get("NIKASHA_CENSUS_TIMEOUT_SECONDS", "180"))


class Unknown(Exception):
    """The instrument could not run. Never reported as clean."""


def psql(sql: str, sep: str = "\x1f", timeout: int | None = None) -> list[list[str]]:
    env = dict(os.environ)
    env.setdefault("PGCONNECT_TIMEOUT", "10")
    p = subprocess.run(["psql", "-tAX", "-F", sep, "-v", "ON_ERROR_STOP=1", "-c", sql],
                       capture_output=True, text=True, env=env,
                       timeout=(timeout if timeout is not None else PSQL_TIMEOUT_SECONDS))
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

def registry(layer_key: str) -> tuple[dict[str, dict], dict]:
    """Read via json_agg, NOT line-oriented output.

    `count_sql` and `integrity_check_sql` contain newlines, so a row-per-line read splits one asset
    across several lines and invents assets whose ids are fragments of SQL. That bug produced 52 assets
    from 40 on this script's first run — the same defect class the layer template warns about, an
    instrument whose population was never stated. One JSON document has no such ambiguity.

    R220: `asset_registry` for this prefix has more rows than the ACTIVE population the census
    should measure — 129 total vs 127 active registry-wide (2 retired L3 rows, measured 2026-09-27).
    `is_active AND NOT dead_flag` is the register's own phrasing, but `dead_flag` is NULL (not
    false) on every row today, and `NOT NULL` is NULL in SQL — so that exact expression silently
    matches ZERO rows, not 127. The honest form is `is_active AND NOT coalesce(dead_flag, false)`.
    Excluded (inactive) rows are named here, not silently dropped — `measure()` states the
    population figure in its own output rather than letting 129 and 127 quietly disagree."""
    cfg = LAYERS[layer_key]
    total = int(scalar(f"SELECT count(*)::text FROM asset_registry WHERE asset_id LIKE '{cfg['prefix']}%'") or 0)
    excluded = [dict(asset_id=r[0], is_active=(r[1] == "t"), catalog_status=r[2])
                for r in psql("SELECT asset_id, is_active::text, coalesce(catalog_status,'') "
                              f"FROM asset_registry WHERE asset_id LIKE '{cfg['prefix']}%' "
                              "AND NOT (is_active AND NOT coalesce(dead_flag,false)) ORDER BY asset_id")]
    blob = scalar(
        "SELECT coalesce(json_agg(json_build_object("
        "'asset_id',asset_id,'has_writer',coalesce(has_writer,false),'target_table',target_table,"
        "'count_sql',coalesce(count_sql,''),'has_integrity',(integrity_check_sql IS NOT NULL),"
        "'depends_on',coalesce(to_json(depends_on),'[]'::json),'target_floor',target_floor,"
        "'catalog_status',coalesce(catalog_status,''),'asset_kind',coalesce(asset_kind,''))"
        " ORDER BY asset_id)::text,'[]') "
        f"FROM asset_registry WHERE asset_id LIKE '{cfg['prefix']}%' "
        "AND is_active AND NOT coalesce(dead_flag,false)")
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
        # F7 (A_REVIEW.md): before R220 this raised on zero rows; R220 narrowed it to zero REGISTRY
        # rows, so a population filter that matched nothing (the `NOT dead_flag` NULL trap, M9)
        # measured zero assets and exited 0 — a clean-looking census of nothing. An empty active
        # population is never a clean result: it is UNKNOWN (exit 4), with both figures stated.
        raise Unknown(f"zero active {cfg['prefix']}* rows in asset_registry ({total} registry row(s) for this "
                      "prefix) — an empty population is not a clean census; check the population filter")
    population = dict(registry_total=total, active=len(out), excluded_inactive=excluded)
    return out, population


def live_counts(reg: dict) -> tuple[dict[str, int | None], dict[str, str]]:
    """Each asset's OWN count_sql — the cockpit instrument, not a table count.

    F2 (A_REVIEW.md, Lane A gate REJECT): a `count_sql` that RAISES (statement timeout, missing
    relation) must be distinguishable from an asset that simply HAS no `count_sql` at all — both
    used to collapse to `out[aid] = None`, and `measure()` then wrote `Build.completion = N/A "no
    count_sql"` for a query that in fact errored. N/A is CLOSABLE; a live demonstration
    (bg_ephemeris) closed the gap on a query that never returned a clean answer. Returns
    `(counts, errored)`: `errored[aid]` is set only when that asset's own `count_sql` was
    non-empty and its query raised `Unknown` — never for a genuinely absent `count_sql`."""
    out: dict[str, int | None] = {}
    errored: dict[str, str] = {}
    parts, ids = [], []
    for aid, r in reg.items():
        q = " ".join(re.sub(r"--[^\n]*", "", r["count_sql"]).replace("\n", " ").rstrip(" ;").split())
        if not q:
            out[aid] = None
            continue
        parts.append(f"SELECT '{aid}' a,({q})::text n")
        ids.append(aid)
    if not parts:
        return out, errored
    try:
        for a, n in psql(" UNION ALL ".join(parts)):
            out[a] = int(n) if n.strip().lstrip("-").isdigit() else None
    except Unknown:
        for aid in ids:                                    # one bad count_sql must not blind the rest
            q = " ".join(re.sub(r"--[^\n]*", "", reg[aid]["count_sql"]).replace("\n", " ").rstrip(" ;").split())
            try:
                v = scalar(f"SELECT ({q})::text")
                out[aid] = int(v) if v and v.strip().lstrip("-").isdigit() else None
            except Unknown as exc:
                out[aid] = None
                errored[aid] = str(exc)
    return out, errored


def throughput(prefix: str) -> dict[str, dict]:
    rows = psql("SELECT asset_id, coalesce(state,''), coalesce(rows_written::text,''), "
                "coalesce(round(rows_per_second)::text,''), coalesce(last_built_at::date::text,'') "
                f"FROM asset_throughput WHERE asset_id LIKE '{prefix}%'")
    return {r[0]: dict(state=r[1], rows_written=r[2], rps=r[3], last_built=r[4])
            for r in ((x + [""] * 5)[:5] for x in rows)}


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


def build_history(prefix: str) -> dict:
    """What the orchestrator ACTUALLY did, from build_runs / build_run_assets.

    The static checks say an asset *should* be dispatchable. Only this says whether it ever was, and what
    happened. Native context (2026-09-26): a global build skips L0 and walks L1->L5, so an L0 asset is
    only ever exercised by a layer- or asset-scope run — measured here rather than assumed."""
    per: dict[str, dict] = {}
    rows = psql("SELECT a.asset_id, r.scope, a.state, coalesce(a.disposition,''), "
                "coalesce(r.created_at::date::text,''), coalesce(left(a.error,200),'') "
                "FROM build_run_assets a JOIN build_runs r ON r.id=a.run_id "
                f"WHERE a.asset_id LIKE '{prefix}%' ORDER BY a.asset_id, r.created_at")
    for aid, scope, state, disp, when, err in ((x + [""] * 6)[:6] for x in rows):
        d = per.setdefault(aid, dict(runs=0, error=0, aborted=0, complete=0, queued=0, skipped=0,
                                     blocked=0, scopes=set(), last_state="", last_when="",
                                     last_disposition="", sample_error="", sample_blocked=""))
        d["runs"] += 1
        d[state] = d.get(state, 0) + 1
        if disp == "skip_no_delta":
            d["skipped"] += 1
        # Packet B1: 'blocked_dependency' (migration 1095) marks a row whose writer never
        # ran because an upstream dependency failed/was blocked in the SAME run — a
        # cascade CONSEQUENCE, not its own root cause. Tracked separately from the plain
        # `error` tally so grading below can count "one cause, N blocked" instead of
        # grading a chart FAIL/PARTIAL purely from downstream cascade noise
        # (B1_before_20260926T173931Z.json §4 — asset_census was the worst offender:
        # it already read `disposition` for skip_no_delta but never checked this value).
        if state == "error" and disp == "blocked_dependency":
            d["blocked"] += 1
            if err and not d["sample_blocked"]:
                d["sample_blocked"] = err
        d["scopes"].add(scope)
        d["last_state"], d["last_when"], d["last_disposition"] = state, when, disp
        if state == "error" and disp != "blocked_dependency" and err and not d["sample_error"]:
            d["sample_error"] = err
    glob = int(scalar("SELECT count(*)::text FROM build_runs WHERE scope='global'") or 0)
    glob_l0 = int(scalar("SELECT count(*)::text FROM build_runs r JOIN build_run_assets a ON a.run_id=r.id "
                         f"WHERE r.scope='global' AND a.asset_id LIKE '{prefix}%'") or 0)
    lit = {r[0] for r in psql("SELECT asset_id FROM asset_throughput WHERE state='lit'")}
    return dict(per=per, global_runs=glob, global_with_layer=glob_l0, lit=lit)


def _grade_build_history(h: dict) -> dict:
    """Grade one asset's Build.history verdict from its build_history() per-asset dict `h`.

    Extracted as its own pure function (Packet B1) so this grading arithmetic is
    unit-testable directly against a hand-built `h`, without mocking psql/scalar for
    the whole measure() pipeline.

    Packet B1: a cascade-blocked row (disposition='blocked_dependency', migration 1095)
    is a CONSEQUENCE, never its own cause — it must not by itself grade a chart
    FAIL/PARTIAL. Before this fix, asset_census already read `disposition` (for
    skip_no_delta) but never checked this value at all — a chart whose every build
    blemish was downstream cascade from someone else's failure was graded exactly as
    if it had real defects of its own (B1_before_20260926T173931Z.json §4, the packet's
    most consequential surface: a governance signal, not just a UI cosmetic).

    `genuine_error` excludes blocked rows from the count this grading acts on;
    `last_run_was_blocked_only` excludes a purely-cascade most-recent-run from the
    "most recent run failed" FAIL trigger specifically. `h['blocked']` is still
    surfaced in every branch's `measured` text — never silently dropped (§N.6: count
    it, don't hide it; a chart with genuinely zero non-cascade defects grades PASS,
    not NA, so the blocked count doesn't vanish from the report).
    """
    genuine_error = h["error"] - h["blocked"]
    bad = genuine_error + h["aborted"]
    last_run_was_blocked_only = (
        h["last_state"] == "error" and h["last_disposition"] == "blocked_dependency"
    )
    if h["last_state"] in ("error", "aborted") and not last_run_was_blocked_only:
        return dict(v=FAIL, measured=f"most recent run {h['last_state']} ({h['last_when']}); {genuine_error} error(s), {h['aborted']} abort(s), {h['blocked']} blocked_dependency (cascade, not counted as failure). {h['sample_error']}")
    if bad:
        return dict(v=PARTIAL, measured=f"latest run complete, but {genuine_error} error(s) and {h['aborted']} abort(s) on record ({h['blocked']} additional blocked_dependency row(s) excluded as cascade-only). {h['sample_error']}")
    if h["blocked"]:
        # C-4 (review B1_review_20260926T182200Z.md, §N.8): PASS must require at
        # least one EARNED completion, not merely "zero genuine errors". Without
        # this guard, an asset that has NEVER once completed a build — every
        # attempt cascade-blocked, none of them its own fault — would grade PASS
        # from an all-cascade history alone: a green signal with no detector
        # behind the claim "this asset builds successfully" (the exact §N.8
        # defect class). Measured against live production at review time: 0 of
        # 124 assets currently hit this branch (6 FAIL->FAIL, 7 FAIL->PARTIAL, 89
        # PARTIAL->PARTIAL, 22 PASS->PASS, zero flips to PASS) — latent, not live,
        # but the path exists and would fire the moment a new asset is added
        # downstream of a chronically-failing root.
        if h["complete"] == 0:
            return dict(v=PARTIAL, measured=f"0 complete — this asset has NEVER once finished a build; {h['blocked']} blocked_dependency row(s) were all downstream cascade ({h['sample_blocked']}), not a defect of this asset, but a history with zero completions cannot grade PASS on the strength of 'no genuine error' alone; {h['skipped']} skip_no_delta")
        return dict(v=PASS, measured=f"{h['complete']} complete, no genuine error or abort; {h['blocked']} blocked_dependency row(s) were all downstream cascade from an upstream failure, not a defect of this asset ({h['sample_blocked']}); {h['skipped']} skip_no_delta (healthy)")
    return dict(v=PASS, measured=f"{h['complete']} complete, no error or abort; {h['skipped']} skip_no_delta (healthy)")


def duration_instrument_present() -> bool | None:
    """D6 item 1 (feature detection): does `asset_throughput.duration_seconds` exist yet
    (migration 1094)? Returns None (not False) when the check itself cannot run — that is
    "instrument unreachable", a distinct NO_DETECTOR reason from "instrument absent".

    F11 (A_REVIEW.md, tested against the engine at 8edba0533): schema-qualified exactly as the
    engine's own `_duration_columns_present` is (gate review R-7 there) — a same-named table in
    another schema must never make the instrument read as present in `public`."""
    try:
        return (scalar("SELECT (EXISTS(SELECT 1 FROM information_schema.columns "
                       "WHERE table_schema='public' AND table_name='asset_throughput' "
                       "AND column_name='duration_seconds'))::text")
               or "f") in ("t", "true")
    except Unknown:
        return None


def _grade_earn_cost(attempt: dict | None, instrument_present: bool | None, baseline: dict | None,
                      attempt_linkage_wired: bool = True) -> tuple[dict, dict]:
    """D6 (DECISIONS_RECOMMENDATIONS_v2_0.md D6, R55 re-specified): grade `Earn.build_record` and
    `Cost.baseline` — two SEPARATE measurements, neither certifying the whole Earn gate, Cost not
    one of the nine gates at all (tier 4 §1's build-cost baseline only).

    Extracted as a pure function (same discipline as `_grade_build_history`, Packet B1) so every
    branch is unit-testable against a hand-built `attempt`/`baseline`, without a live
    `asset_throughput.duration_seconds` column to test against — which does not exist in this
    environment (migration 1094 not applied, confirmed 2026-09-27 in both production and the
    nikasha_sandbox proof DB) or in production, so this function is EXERCISED here only through
    its own test suite.

    F1 (Lane A gate review, `nikasha_test/wave1/A_REVIEW.md`): `measure()` does NOT query
    `build_run_assets` for a real attempt today — that wiring is R42–R56, a separate lane this
    packet stops short of (§A-4). So `measure()` always calls this with `attempt=None` AND
    `attempt_linkage_wired=False`, regardless of whether the instrument (migration 1094) is
    present. This is deliberately NOT the same claim as "genuinely never attempted": the fixed
    call site's earlier docstring said this "will grade for real the moment migration 1094 lands,
    without any further code change" — that was false. Grading for real needs the attempt query
    (R42–R56) to land too; until then, an instrument-present-but-unwired run must read
    `NO_DETECTOR — attempt linkage not wired`, not the closable `N/A "never attempted"` a genuine
    no-attempt-row case would use — the latter would falsely CLOSE every `Earn.build_record` gap
    for every asset that was in fact built, the instant the column exists.

    `attempt` is the latest build_run_assets row for (asset, chart scope), or None if the asset
    has never been attempted (only a meaningful "None" when `attempt_linkage_wired` is True — see
    above). Expected keys: `state` ("complete"/"error"/"aborted"/"queued"),
    `disposition` ("skip_no_delta"/"probe_green"/"" ), `reached_completion_write` (bool — did
    execution get far enough that a duration WOULD have been recorded if the instrument were
    working), `duration_seconds` (float/None), `rows_written` (int/None), `is_legacy_telemetry`
    (bool — this attempt's writer is on the pre-1094 `_telemetry` path R34 left as a residual; the
    ONLY currently-known cause of a completion write with no duration. Unclassified so far:
    engine-side, migration-1094-dependent; no such marker exists in this environment either).
    `has_writer` — no registered writer at all (a legacy health-probe service) grades N/A the same
    as a healthy skip.

    `baseline`, when not None, is the most recent MEASURED completion on record for this asset at
    this scope: `{"rate": float, "attempt_id": str, "age_days": int}` — provenance, not just a number.
    """
    if instrument_present is None:
        reason = "instrument unreachable"
    elif not instrument_present:
        reason = "instrument absent (migration 1094)"
    else:
        reason = None

    if reason is not None:
        nd = dict(v=NO_DET, measured=f"NO_DETECTOR — {reason}, scoped to this run")
        return dict(nd), dict(nd)

    # From here, the instrument genuinely exists — grade Earn.build_record for the latest attempt.
    if attempt is None and not attempt_linkage_wired:
        # F1: the instrument exists but this call site never queried build_run_assets for an
        # attempt at all — `attempt=None` here means "unknown", never "confirmed absent". Reading
        # N/A would close a gap on a fact this run never actually measured.
        nd = dict(v=NO_DET, measured="NO_DETECTOR — attempt linkage not wired")
        return dict(nd), dict(nd)
    if attempt is None:
        earn = dict(v=NA, measured="never attempted — see Build.exercised")
    elif attempt.get("disposition") in ("skip_no_delta", "probe_green") or not attempt.get("has_writer", True):
        why = (attempt.get("disposition") or "no registered writer (legacy health-probe service)")
        earn = dict(v=NA, measured=f"healthy non-execution ({why}) — no build was due")
    elif not attempt.get("reached_completion_write", False):
        earn = dict(v=NA, measured=f"attempt {attempt.get('state','?')} before completion; see Build.history")
    elif attempt.get("duration_seconds") is not None:
        dur = attempt["duration_seconds"]
        rw = attempt.get("rows_written") or 0
        rate = (rw / dur) if dur else 0.0
        earn = dict(v=PASS, measured=f"completion write with duration={dur}s, rows_written={rw}, rate={rate} "
                                     "(a measured rate of 0.0 is a real measurement, not suppressed)")
    elif attempt.get("is_legacy_telemetry"):
        earn = dict(v=FAIL, measured="completion write reached with no duration — the legacy _telemetry "
                                     "path (R34's residual)")
    else:
        earn = dict(v=NO_DET, measured="NO_DETECTOR — unclassified NULL (completion write with no duration "
                                       "and no identified cause)")

    # Cost.baseline: independent of the latest attempt's own outcome — a healthy skip/failure
    # neither erases a prior sanctioned baseline nor creates one.
    if baseline is not None:
        cost = dict(v=PASS, measured=f"sanctioned baseline: rate={baseline['rate']} "
                                     f"(attempt {baseline['attempt_id']}, {baseline['age_days']}d old)")
    else:
        cost = dict(v=FAIL, measured="no sanctioned baseline build on record")
    return earn, cost


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


def _measure_contract(aid: str, files: list[str]) -> dict:
    """R41 fault isolation for Build.contract, extracted as its own pure-ish function (F3,
    A_REVIEW.md: the inline try/except could only be proven by grepping measure()'s source text,
    which survives a mutation that makes the guard re-raise instead of catching. Extracting it
    lets a test call it directly with `contract_scan` monkeypatched to raise, and assert the
    RETURN VALUE is ERRORED — a mutation that removes or breaks the try/except now fails that
    assertion instead of surviving on source text alone)."""
    try:
        v, notes = contract_scan(aid, files)
        return dict(v=v, measured="; ".join(notes) or "conformant")
    except Unknown as exc:
        return dict(v=ERRORED, measured=f"check errored: {exc}")


def _measure_idem(aid: str, files: list[str], convention: str) -> dict:
    """R41 fault isolation for Idem.pattern — same discipline as `_measure_contract`."""
    try:
        v, notes = idem_scan(aid, files, convention)
        return dict(v=v, measured="; ".join(notes))
    except Unknown as exc:
        return dict(v=ERRORED, measured=f"check errored: {exc}")


# The closed verdict set a registered carriage detector may return (the ledgers' own vocabulary,
# asset_elevation_tracker.VERDICTS). NOT_GENERIC / ERRORED are census-internal and never a detector's.
DETECTOR_VERDICTS = (PASS, FAIL, PARTIAL, NO_DET, NA)


def _run_carriage_detector(aid: str) -> dict:
    """P3/R57 item (d): a per-asset carriage detector registered at <CTRL>/detectors/<asset>_D<1|2|3>.py
    IS the detector — run it and adopt its verdict instead of the blanket NO_DETECTOR.

    F8 (A_REVIEW.md): the port adopted the last stdout line's `verdict` without checking the
    process's return code or the verdict's vocabulary, so a detector that crashed AFTER printing
    `{"verdict": "PASS", …}` — or printed a verdict outside the closed set — was adopted as its
    verdict, and a PASS closes a gap. A non-zero exit, an unparseable last line, or a verdict outside
    DETECTOR_VERDICTS now reads NO_DETECTOR with the exact reason: a detector that did not complete
    cleanly has measured nothing."""
    det_dir = CTRL / "detectors"
    det = None
    if det_dir.is_dir():
        for n in (1, 2, 3):
            p = det_dir / f"{aid}_D{n}.py"
            if p.exists():
                det = p
                break
    if det is None:
        return dict(v=NO_DET, measured="no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics")
    try:
        pr = subprocess.run([sys.executable, str(det)], capture_output=True, text=True,
                            env=os.environ, timeout=120)
    except Exception as exc:  # a registered detector that cannot run is not a pass
        return dict(v=NO_DET, measured=f"{det.name} failed to run: {exc}")
    if pr.returncode != 0:
        tail = (pr.stderr.strip().splitlines() or ["no stderr"])[-1]
        return dict(v=NO_DET, measured=f"{det.name} exited {pr.returncode} ({tail}) — output of a failed "
                                       "detector is not a verdict")
    try:
        out = json.loads(pr.stdout.strip().splitlines()[-1])
        verdict, measured = out["verdict"], out["measured"]
    except Exception as exc:
        return dict(v=NO_DET, measured=f"{det.name} produced no parseable verdict line: {type(exc).__name__}: {exc}")
    if verdict not in DETECTOR_VERDICTS:
        return dict(v=NO_DET, measured=f"{det.name} returned verdict {verdict!r}, outside the closed set "
                                       f"{list(DETECTOR_VERDICTS)}")
    return dict(v=verdict, measured=f"{det.name}: {measured}")


# ─────────────────────────── the census ───────────────────────────

def _layer_read(name: str, fn, *args):
    """F12 (A_REVIEW.md): name the layer-wide read that failed, so the UNKNOWN says which one."""
    try:
        return fn(*args)
    except Unknown as exc:
        raise Unknown(f"layer-wide read '{name}' failed: {exc}") from exc


def measure(layer_key: str) -> dict:
    """Measure one layer.

    R41 SCOPE LIMIT (F12, A_REVIEW.md — disclosed, not fixed). R41 isolates PER-ASSET checks: one
    asset's failing check degrades only that criterion to ERRORED. The LAYER-WIDE reads below —
    `registry`, `catalog`, `registered_ids` (the writer scan), `throughput`, `build_history` — are
    not isolated: any of them raising `Unknown` still aborts the whole layer (exit 4, nothing reported
    clean), and under `--layer all` it also stops every layer after it, with no census file written.
    That is fail-closed, never a false PASS, but it is a whole-layer blind spot, not a degraded one.
    (`live_counts` isolates per asset itself — F2; `duration_instrument_present` degrades to
    `instrument unreachable` — D6 item 1.)"""
    cfg = LAYERS[layer_key]
    reg, population = _layer_read("registry", registry, layer_key)
    cat = _layer_read("catalog", catalog, [r["target_table"] for r in reg.values()])
    regd = _layer_read("registered_ids", registered_ids, cfg["prefix"])
    counts, count_errors = _layer_read("live_counts", live_counts, reg)
    thru = _layer_read("throughput", throughput, cfg["prefix"])
    hist = _layer_read("build_history", build_history, cfg["prefix"])
    lmaps = local_map_candidates(cfg["prefix"]) if layer_key == "L0" else -1
    # D6 item 1: feature-detected ONCE per layer run, not per asset — the instrument either
    # exists or it doesn't; a per-asset re-check would just be the same answer 40 times over.
    instrument_present = duration_instrument_present()

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

        # R41: a per-check exception must degrade THAT check to ERRORED, never abort the layer.
        m["Build.contract"] = _measure_contract(aid, files)
        m["Idem.pattern"] = _measure_idem(aid, files, cfg["idem"])

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
        if aid in count_errors:
            # F2 (A_REVIEW.md): a count_sql that RAISED must never read N/A "no count_sql" — that
            # reading is CLOSABLE and a live demonstration (bg_ephemeris) closed the gap on a query
            # that in fact errored. D4 case 1 ("never on an errored check") requires ERRORED here.
            m["Build.completion"] = dict(v=ERRORED, measured=f"check errored: {count_errors[aid]}")
        elif live is None:
            m["Build.completion"] = dict(v=NA, measured=f"no count_sql; build state='{t.get('state','-')}'")
        elif rw == "":
            m["Build.completion"] = dict(v=FAIL, measured=f"live={live} and no build record at all")
        elif int(rw) == 0 and live > 0:
            m["Build.completion"] = dict(v=FAIL, measured=f"build record says rows_written=0 against live={live}")
        elif int(rw) == 0 and live == 0:
            m["Build.completion"] = dict(v=PASS, measured="live=0 and rows_written=0 — consistent (empty by design or service)")
        else:
            m["Build.completion"] = dict(v=PASS, measured=f"rows_written={rw}, live={live}")

        # D6: `_grade_earn_cost` feature-detects `duration_seconds` (absent everywhere today,
        # migration 1094 not applied) and grades NO_DETECTOR for both measurements when it is —
        # never the naive "rows_per_second populated => PASS" this replaces, which could not tell
        # a genuinely-measured build from a stale/never-cleared column (R44/R55). `attempt`/
        # `baseline` are unused here because THIS call site never queries build_run_assets for a
        # real attempt — that wiring is R42-R56 (a separate lane, see §A-4), not landed by this
        # packet. `attempt_linkage_wired=False` says so explicitly, so `_grade_earn_cost` reads
        # NO_DETECTOR — attempt linkage not wired instead of the closable N/A "never attempted"
        # once the instrument is present (F1, `nikasha_test/wave1/A_REVIEW.md`): the moment
        # migration 1094 lands, grading for REAL still needs the attempt query to land too, and
        # until it does this call site must not claim "never attempted" for assets that plainly
        # were.
        m["Earn.build_record"], m["Cost.baseline"] = _grade_earn_cost(
            attempt=None, instrument_present=instrument_present, baseline=None,
            attempt_linkage_wired=False)

        floor = r["target_floor"]
        if live is not None and floor and floor.isdigit():
            d = live - int(floor)
            m["Count.floor"] = dict(v=(FAIL if d < 0 else PASS), measured=f"live={live}, floor={floor}, delta={d:+d}")

        tbl = r["target_table"]
        if tbl and tbl in cat["exists"]:
            # R41: each of these four checks queries the target table independently (one of them,
            # on the estate's largest tables, is exactly R40's kala_field timeout case) — a single
            # slow/failing query must degrade only its OWN criterion, never blind the other three.
            try:
                dc = depth_census(tbl, cat["cols"].get(tbl, []))
                m["Complete.depth"] = dict(v=(PASS if not dc.get("never") else PARTIAL),
                                           measured=(f"{dc.get('rows',0)} rows, {dc['columns']} cols; "
                                                     f"fully populated {len(dc.get('full',[]))}; NEVER populated "
                                                     f"{dc.get('never',[])}" if not dc.get("note") else dc["note"]))
            except Unknown as exc:
                dc = {}
                m["Complete.depth"] = dict(v=ERRORED, measured=f"check errored: {exc}")

            keys = cat["keys"].get(tbl, [])
            if keys:
                k = keys[0] if len(keys[0]) > 1 or keys[0][0] != "id" else (keys[1] if len(keys) > 1 else keys[0])
                kd = ", ".join(k)
                try:
                    # R40: `count(*) - count(DISTINCT (cols))` requires a full sort/hash of every row
                    # to materialise BOTH counts and does not scale to the estate's largest table
                    # (kala_field, 10.3M rows; ground truth measured by hand: duplicates = 0 in 47s
                    # against the naive form's >180s). An EXISTS/HAVING duplicate-group probe can
                    # stop at the first violation instead of counting the whole table when one
                    # exists, and never needs the second full DISTINCT pass either way.
                    has_dup = (scalar(f"SELECT EXISTS(SELECT 1 FROM {tbl} GROUP BY {kd} "
                                      "HAVING count(*) > 1)::text") or "f") in ("t", "true")
                    # F9 (A_REVIEW.md): R40's EXISTS probe decides the verdict but dropped the figure
                    # the ledger `_schema` requires ("measured: <figure …>"). The figure is restored —
                    # "N duplicate(s)" means rows beyond the first per key, the same quantity the
                    # pre-R40 `count(*) - count(DISTINCT key)` reported — but it is counted ONLY when
                    # the probe found a duplicate, so the clean case (kala_field) keeps R40's cost. A
                    # count that errors keeps the probe's FAIL and says the figure is missing.
                    if not has_dup:
                        figure = "0 duplicate(s)"
                    else:
                        try:
                            dup_groups, dup_rows = psql(
                                "SELECT count(*)::text, coalesce(sum(n - 1), 0)::text FROM "
                                f"(SELECT count(*) AS n FROM {tbl} GROUP BY {kd} HAVING count(*) > 1) d")[0]
                            figure = f"{dup_rows} duplicate(s) in {dup_groups} duplicate group(s)"
                        except Unknown as exc:
                            figure = f"duplicate group(s) exist; the count errored ({exc})"
                    m["Vocab.identity"] = dict(v=(FAIL if has_dup else PASS),
                                               measured=f"declared key ({kd}): {figure}")
                except Unknown as exc:
                    m["Vocab.identity"] = dict(v=ERRORED, measured=f"check errored: {exc}")

            try:
                ac = alias_census(tbl, cat["cols"].get(tbl, []))
                if ac:
                    bad = {k: v for k, v in ac.items() if v["no_alias"]}
                    m["Vocab.alias"] = dict(v=(PASS if not bad else FAIL),
                                            measured=(f"{len(ac)} class(es); empty alias sets: "
                                                      + (", ".join(f"{k} {v['no_alias']}/{v['rows']}" for k, v in bad.items()) or "none")))
            except Unknown as exc:
                m["Vocab.alias"] = dict(v=ERRORED, measured=f"check errored: {exc}")

            tcols = set(cat["cols"].get(tbl, []))
            cit = [c for c in ("source_citation", "source_text_id", "classical_citations", "citation_ref")
                   if c in tcols]
            if cit and dc.get("rows"):
                col = cit[0]
                try:
                    n = scalar(f"SELECT count(*)::text FROM {tbl} WHERE {col} IS NOT NULL")
                    m["Ldgr.source_presence"] = dict(v=(PASS if int(n) == dc["rows"] else PARTIAL),
                                                     measured=f"{col} populated on {n}/{dc['rows']} rows")
                except Unknown as exc:
                    m["Ldgr.source_presence"] = dict(v=ERRORED, measured=f"check errored: {exc}")
        elif tbl:
            m["Complete.depth"] = dict(v=FAIL, measured=f"target_table '{tbl}' does not exist in production")

        cap = capability_scan(cfg["caps"], [t for t in ([tbl] if tbl else []) + [aid]])
        m["Dens.served"] = dict(v=(NA if not cap["modules"] else (PASS if cap["density"] else FAIL)),
                                measured=(cap["note"] or f"{len(cap['modules'])} module(s): {', '.join(cap['modules']) or 'none'}; "
                                          f"declaring density_contract: {cap['density']}"))

        h = hist["per"].get(aid)
        if not h:
            m["Build.exercised"] = dict(
                v=(FAIL if r["has_writer"] else NA),
                measured=("registered with a writer and the orchestrator has NEVER run it (no build_run_assets row)"
                          if r["has_writer"] else "never run, and it has no writer — consistent"))
            m["Build.history"] = dict(v=NA, measured="never run; check 7 owns this")
        else:
            m["Build.exercised"] = dict(v=PASS, measured=f"{h['runs']} run(s), scope(s): {', '.join(sorted(h['scopes']))}, last {h['last_when']}")
            m["Build.history"] = _grade_build_history(h)

        dead = [d for d in r["depends_on"] if d not in hist["lit"]]
        m["Build.dep_liveness"] = dict(
            v=(PASS if not dead else FAIL),
            measured=("all declared dependencies are lit" if not dead
                      else f"declared dependencies not lit: {dead} — a DEP-ASSERT trap if no writer can light them")) \
            if r["depends_on"] else dict(v=NA, measured="no declared dependencies")

        m["Complete.width"] = dict(v=NOT_GENERIC, measured="no declared universe for this asset — declaring one is the first width gap")
        m["Carr.detector"] = _run_carriage_detector(aid)
        m["Reach.fields"] = dict(v=NOT_GENERIC, measured="field-level exposure census is per-capability; not generic")

        assets.append(dict(asset_id=aid, layer=layer_key, scoring=cfg["scoring"], live_rows=live,
                           target_table=tbl, has_writer=r["has_writer"], writer_files=files,
                           catalog_status=r["catalog_status"], measurements=m))

    extra = sorted(set(regd) - known)
    never = [a["asset_id"] for a in assets if a["measurements"]["Build.exercised"]["v"] == FAIL]
    return dict(generated=dt.datetime.now().astimezone().isoformat(timespec="seconds"), layer=layer_key,
                layer_name=cfg["name"], scoring=cfg["scoring"], n_assets=len(assets),
                # R220: the population this census measured, stated explicitly — `n_assets` above IS
                # the active population (`registry()` already excludes inactive/dead rows), but the
                # gap between it and the layer's raw registry row count must never be silent.
                population_active=population["active"], population_registry_total=population["registry_total"],
                population_excluded_inactive=population["excluded_inactive"],
                global_runs=hist["global_runs"], global_runs_touching_layer=hist["global_with_layer"],
                never_exercised_with_writer=never,
                registered_ids=len(regd), registry_has_writer=sum(1 for r in reg.values() if r["has_writer"]),
                phantom_registered=extra, local_map_candidates=lmaps, assets=assets)


# D4 ruling (DECISIONS_RECOMMENDATIONS_v2_0.md): the verdict a check can return keeps growing
# (NOT_GENERIC today; R41's per-check fault isolation adds an "errored" state; an unmeasured
# criterion is silently absent from `measurements` and never reaches this function at all). A
# gap closes on an EXPLICIT allowlist, never on "whatever isn't in the failing tuple" — the sandbox
# port's own defect (D4 finding #6): closing on "any other verdict" would close on NOT_GENERIC too.
CLOSABLE = (PASS, NA)
FAILING = (FAIL, PARTIAL, NO_DET)
# A gap row's own state vocabulary (asset_gaps.jsonl `_schema`): OPEN and IN_PROGRESS are both
# live/unresolved (D4: "an IN_PROGRESS row transitions on PASS" exactly like an OPEN one); CLOSED
# is resolved; anything else (WITHDRAWN, or a state string this script has never written) is left
# alone rather than re-opened by inference.
LIVE_GAP_STATES = ("OPEN", "IN_PROGRESS")


def emit_gaps(census: dict) -> tuple[int, int, int, int]:
    """Append-only ledger with deterministic ids (`<asset>-<criterion>`), closing by measurement.

    D4 ruling (R57 amended), each an acceptance case with its own test in
    __tests__/test_a2_emit_gaps_closure.py:

    - CLOSED only on `PASS` or an explicitly justified `N/A` — never on `NOT_GENERIC`, `UNKNOWN`,
      an errored check, or an unmeasured criterion (i.e. anything outside CLOSABLE is a no-op,
      not an implicit close).
    - check failing (FAIL/PARTIAL/NO_DETECTOR), no row with this gap_id yet     -> append OPEN
    - check failing, latest row OPEN or IN_PROGRESS                            -> skip (already open)
    - check failing, latest row CLOSED                                        -> append OPEN
      ("RE-OPENED by measurement" — the defect regressed; a loop that only counts up is not a loop)
    - check failing, latest row WITHDRAWN (or any other terminal state this script never wrote)
      -> nothing to do; WITHDRAWN is a terminal, human decision (F4, A_REVIEW.md) and is "left
      alone rather than re-opened by inference" exactly as documented below — the code used to
      contradict this comment by re-opening WITHDRAWN rows too.
    - check closable (PASS/N-A) now, latest row OPEN or IN_PROGRESS            -> append CLOSED
      (closure BY MEASUREMENT: the same detector now passes; the row quotes the new measured value)
    - check closable, latest row CLOSED or no row                             -> nothing to do
    - a row carrying `superseded_by` (R80) is a dead identity — never touched, never resurrected,
      regardless of what the census currently measures for that gap_id, and regardless of any
      LATER row for the same gap_id that omits the flag (F5, A_REVIEW.md): once superseded, always
      superseded — the flag is checked across the id's whole history, not only its latest row.
    - hand `change`/`owner`/`gate` are CARRIED FORWARD from the prior row onto every transition
      row (CLOSED or RE-OPENED); only a gap_id's very first OPEN row uses the census's own
      defaults, because there is no prior hand annotation yet to carry.
    Rows whose gap_id is not a deterministic `<asset>-<criterion>` id (hand-written rows with no
    detector binding, R58) are never touched by this function at all — no census criterion will
    ever produce that gap_id, so `latest` simply never matches them.

    LIMIT (F12, A_REVIEW.md item 4 — disclosed, not detected): "latest" means last in FILE order,
    not by `ts`. For one append-only file that is the truth. A git merge of two branches that both
    appended to the ledger concatenates their rows in merge order, so a stale CLOSED can land after a
    newer OPEN for the same gap_id and be read as current. Neither this function nor the tracker
    detects that; re-running the census after such a merge re-measures and appends the correct
    transition.
    """
    path = CTRL / "asset_gaps.jsonl"
    latest: dict[str, dict] = {}
    # F5 (A_REVIEW.md, non-blocking correction): `superseded_by` must be a PERMANENT flag on the
    # identity, not just a property of whichever row happens to be latest. Checking only
    # `latest.get(gid)` meant a superseded id could be resurrected the instant any later row
    # (hand-written or otherwise) omitted the flag — demonstrated: an early superseded_by row
    # followed by a later plain row re-opened/re-closed the "dead" id. `ever_superseded` is set
    # once any row for a gid ever carried the flag, and stays set regardless of what follows.
    ever_superseded: set[str] = set()
    if path.exists():
        for ln in path.read_text(encoding="utf-8").split("\n"):
            if ln.strip():
                try:
                    r = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if r.get("gap_id"):
                    latest[r["gap_id"]] = r  # append-only: last row for an id wins
                    if r.get("superseded_by"):
                        ever_superseded.add(r["gap_id"])
    ts = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    added = skipped = closed = reopened = 0
    with path.open("a", encoding="utf-8") as f:
        for a in census["assets"]:
            for crit, res in a["measurements"].items():
                v = res["v"]
                if v not in FAILING and v not in CLOSABLE:
                    continue  # NOT_GENERIC / UNKNOWN / errored / anything future: never a transition
                gid = f"{a['asset_id']}-{crit}"
                prior = latest.get(gid)
                if gid in ever_superseded:
                    continue  # a superseded id is never resurrected, whatever is measured now,
                              # and whatever any LATER row (with no superseded_by of its own) says
                prior_state = (prior or {}).get("state", "OPEN").upper()
                # Carry hand metadata forward; only the very first OPEN row for a gid has none
                # to carry, so it alone falls back to the census's own defaults.
                change = prior.get("change", "") if prior else ""
                owner = prior.get("owner", "asset_census") if prior else "asset_census"
                gate = prior.get("gate", "this asset's certification") if prior else "this asset's certification"
                if v in FAILING:
                    if prior is None:
                        f.write(json.dumps(dict(
                            asset=a["asset_id"], gap_id=gid, kind="gap", criterion=crit,
                            what=f"measured: {res['measured']} / required: the {crit.split('.')[0]} gate's claim",
                            change=change, detector=f"asset_census.py --layer {census['layer']} ({crit})",
                            owner=owner, gate=gate, state="OPEN", ts=ts), ensure_ascii=False) + "\n")
                        added += 1
                    elif prior_state in LIVE_GAP_STATES:
                        skipped += 1
                    elif prior_state == "CLOSED":  # regression re-opens
                        f.write(json.dumps(dict(
                            asset=a["asset_id"], gap_id=gid, kind="gap", criterion=crit,
                            what=f"RE-OPENED by measurement: {res['measured']} / required: the {crit.split('.')[0]} gate's claim",
                            change=change, detector=f"asset_census.py --layer {census['layer']} ({crit})",
                            owner=owner, gate=gate, state="OPEN", ts=ts), ensure_ascii=False) + "\n")
                        reopened += 1
                    else:
                        # F4 (A_REVIEW.md): WITHDRAWN (or any other terminal state this script
                        # never assigned) is a human, out-of-band decision — left alone rather than
                        # re-opened by inference, matching this function's own documented contract.
                        skipped += 1
                else:  # v in CLOSABLE
                    if prior is not None and prior_state in LIVE_GAP_STATES:
                        f.write(json.dumps(dict(
                            asset=a["asset_id"], gap_id=gid, kind="gap", criterion=crit,
                            what=f"CLOSED by measurement: {res['measured']} / required: the {crit.split('.')[0]} gate's claim",
                            change=change, detector=f"asset_census.py --layer {census['layer']} ({crit})",
                            owner=owner, gate=gate, state="CLOSED", ts=ts), ensure_ascii=False) + "\n")
                        closed += 1
                    # else: no prior, or prior already CLOSED/terminal — nothing to do (idempotent)
    return added, skipped, closed, reopened


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
            print(f"asset_census: UNKNOWN — layer {k}: {exc}")
            print("  Nothing is reported clean: an unreachable instrument is not a passing result.")
            print("  R41 isolates per-asset checks only; a failed layer-wide read leaves this whole layer "
                  f"unmeasured{' and stops every layer after it (no census file written)' if len(keys) > 1 else ''}.")
            return 4
        out[k] = c
        fails = sum(1 for x in c["assets"] for r in x["measurements"].values() if r["v"] == FAIL)
        parts = sum(1 for x in c["assets"] for r in x["measurements"].values() if r["v"] in (PARTIAL, NO_DET))
        errored = sum(1 for x in c["assets"] for r in x["measurements"].values() if r["v"] == ERRORED)
        print(f"{k} {c['layer_name']} ({c['scoring']}): {c['n_assets']} assets · "
              f"{c['registered_ids']} registered ids vs {c['registry_has_writer']} has_writer=true")
        if c["population_registry_total"] != c["population_active"]:
            print(f"  population: {c['population_active']} active of {c['population_registry_total']} registry "
                  f"rows for this layer — excluded (inactive/dead): "
                  f"{', '.join(x['asset_id'] for x in c['population_excluded_inactive'])}")
        print(f"  build scope: {c['global_runs']} global run(s), of which {c['global_runs_touching_layer']} "
              f"touched this layer" + ("  ← the global path never exercises it" if c['global_runs_touching_layer'] == 0 else ""))
        if c["never_exercised_with_writer"]:
            print(f"  !! registered with a writer and NEVER run by the orchestrator: {c['never_exercised_with_writer']}")
        if c["phantom_registered"]:
            print(f"  !! registered but absent from the registry: {c['phantom_registered']}")
        print(f"  FAIL {fails} · PARTIAL/NO_DETECTOR {parts} · ERRORED {errored} · assets measured {c['n_assets']}")
        if errored:
            print(f"  !! {errored} check(s) errored (R41: degraded, not layer-aborting) — "
                  "never counted as PASS; see each asset's measurements for the exception")
        by = {}
        for x in c["assets"]:
            for crit, r in x["measurements"].items():
                if r["v"] == FAIL:
                    by.setdefault(crit, []).append(x["asset_id"])
        for crit in sorted(by):
            n = by[crit]
            print(f"    FAIL {crit}: {len(n)} — {', '.join(n[:6])}{'…' if len(n) > 6 else ''}")
        worst = max(worst, 2 if fails else (3 if (parts or errored) else 0))
        if a.emit_gaps:
            added, skipped, closed, reopened = emit_gaps(c)
            print(f"  ledger: {added} row(s) appended, {skipped} already present, "
                  f"{closed} closed by measurement, {reopened} re-opened")

    Path(a.out).write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    print(f"census written: {os.path.relpath(a.out, ROOT)}")
    return worst


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"asset_census: script error — {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(5)
