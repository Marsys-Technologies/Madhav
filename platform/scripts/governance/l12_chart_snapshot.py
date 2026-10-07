#!/usr/bin/env python3
"""l12_chart_snapshot.py -- READ-ONLY per-chart row counts and content digests for the 20 ga_* (L1) and 23 bo_* (L2) assets.

PURPOSE
  Exec takes a BEFORE snapshot right before L1 and an AFTER snapshot after each layer; `--compare BEFORE AFTER` then says, per asset, IDENTICAL or
  CHANGED and marks every change EXPECTED or UNEXPECTED against the committed predicted-changes data (l12_snapshot_predicted_changes.json), so
  "identical except the predicted changes" is mechanical. One chart only: the canonical chart (482012f1-...), refused otherwise.

WHAT IS DIGESTED (per asset, per COMPONENT = one relation + one row filter)
  The component list is data: l12_snapshot_scopes.json (regenerate with l12_snapshot_scope_gen.py). Each component is a table (or view) plus the
  filter that carves the asset's slice of a SHARED table (chart_facts by fact_category, bodha_msr_signals by signal_type_class, chart_vichara by
  family ...), taken from the declared produced_tables (asset_declarations.json), the registry count_sql and the active output-digest spec.
  Rows are restricted to the chart (chart_id = <canonical>), then split into GROUPS by dims (ayanamsha_id first when the relation has it, then the
  relation's own dims, e.g. chart_facts: fact_category, fact_key). Per group: row count, a CONTENT digest and an IDS digest.
    row hash      md5 of the jsonb text of the row's digested columns (jsonb_build_object, key order fixed by jsonb)
    content hash  digested columns = declared value columns (output-digest spec) or, with no spec, every column except VOLATILE ones
                  (computed_at / created_at / updated_at / any *_at, build_id, run / receipt / attempt ids), embeddings (unless --embeddings),
                  and the relation's own surrogate ids and id-bearing columns
    ids hash      content columns + the surrogate id columns + the id-bearing columns (chart_divisionals.id, chart_dashas.dasha_row_id,
                  bodha_msr_signals.signal_id and the signal-id arrays ...). A change in ids only moves the ids digest, never the content digest.
    group digest  md5 of the row hashes joined in sorted order. The order is by row hash, NOT by key, on purpose: a re-minted surrogate id (the
                  bo_laksana signal re-mint) must not reorder the content digest. The natural key still does its job: it is the row identity of
                  the optional ROW-LEVEL detail and the duplicate-key check (`distinct_keys`).
    table digest  md5 of the sorted lines "<dims>|<rows>|<group digest>", so it is independent of how the query was chunked (by ayanamsha_id,
                  one query per ayanamsha value, each far under the runner's 120 s statement limit).
  ROW-LEVEL DETAIL (a 12-hex hash per natural key) is stored for components of at most --rowhash-max rows (default 12000), so --compare can say
  exactly how many rows moved and which (e.g. "10 rows: Rahu/Ketu retrograde_flag"). Larger components compare at group level.
  A RESIDUAL pseudo-asset (`_residual_chart_facts`) digests the chart_facts rows that NO asset's slice claims: a change there is never predicted.

HOW IT CONNECTS (same convention as l0_asset_snapshot.py / rq.sh)
  libpq environment (PGHOST / PGUSER / PGDATABASE / PGPASSWORD ...) as set by `source ~/.config/suvarna/pgenv.sh`, or DATABASE_URL.
  --driver psycopg (default when importable) | psql (subprocess `psql -X -A -t`, the same client rq.sh uses) | auto. The session is READ ONLY
  (default_transaction_read_only=on), UTC, with a statement timeout; every statement is SELECT-only (suvarna_level_wave.assert_select_only
  refuses anything else BEFORE it is sent). It reads no credential file and writes nothing but the --out JSON.

USAGE
  python3 platform/scripts/governance/l12_chart_snapshot.py --out DIR/L1_before.json --layer L1 [--assets ga_positions,ga_dashas] [--resume]
  python3 platform/scripts/governance/l12_chart_snapshot.py --out DIR/L2_before.json --layer L2
  python3 platform/scripts/governance/l12_chart_snapshot.py --compare DIR/L1_before.json DIR/L1_after.json [--predicted FILE] [--json] [--verbose]
  python3 platform/scripts/governance/l12_chart_snapshot.py --list [--layer L1]        # offline: the tables / filters / keys it covers
  --resume       an existing --out is re-read; assets already `ok` in it are skipped (the file is rewritten after every asset)
  --registry-counts  also run each asset's live registry count_sql for the chart (one SELECT) and record it next to the scope's row total
  --no-chunk     one query per component instead of one per ayanamsha value (same digests)
EXIT  snapshot: 0 ok | 2 bad input | 3 some asset could not be read (recorded as `error`, the rest are written) | 5 unexpected
      compare:  0 no UNEXPECTED change | 1 at least one UNEXPECTED / INCOMPARABLE | 2 bad input
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import suvarna_level_wave as slw  # noqa: E402  (assert_select_only: the same lexer guard the census and the L0 snapshot use)

SCHEMA = "suvarna.l12_chart_snapshot/1"
CANONICAL_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
DEFAULT_SCOPES = HERE / "l12_snapshot_scopes.json"
DEFAULT_PREDICTED = HERE / "l12_snapshot_predicted_changes.json"
RESIDUAL_ASSET = "_residual_chart_facts"
KSEP = "~|~"                         # separator inside a row-key text
FSEP = "\x1f"                        # psql field separator
GSEP = "|"                           # separator inside a group key text
DEFAULT_ROWHASH_MAX = 12000
STATEMENT_TIMEOUT_MS = 110000        # under the runner's 120 s limit
_IDENT = re.compile(r"[a-z_][a-z0-9_]{0,62}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_BATCH = 40                          # jsonb_build_object takes at most 100 arguments (50 pairs)


class SnapshotError(Exception):
    pass


# ───────────────────────────────── scopes (data) ─────────────────────────────────

def load_scopes(path: str | Path = DEFAULT_SCOPES) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema") != "suvarna.l12_snapshot_scopes/1":
        raise SnapshotError("not a suvarna.l12_snapshot_scopes/1 document: " + str(path))
    return doc


def scopes_sha(doc: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(doc, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def ident(name: str) -> str:
    if not isinstance(name, str) or not _IDENT.fullmatch(name):
        raise SnapshotError("not a plain identifier: " + repr(name))
    return name


def q(name: str) -> str:
    return '"' + ident(name) + '"'


def lit(value: str) -> str:
    """A SQL string literal (standard_conforming_strings is on: only the quote needs doubling)."""
    if "\x00" in value:
        raise SnapshotError("NUL in a literal")
    return "'" + value.replace("'", "''") + "'"


def asset_names(scopes: Mapping[str, Any], layer: str | None) -> list[str]:
    out = []
    for a, rec in sorted(scopes["assets"].items()):
        if layer in (None, "all") or rec["layer"] == layer:
            out.append(a)
    return out


# ───────────────────────────────── drivers ─────────────────────────────────

class Runner:
    """Executes ONE guarded SELECT and returns rows of text (None for SQL NULL)."""

    def run(self, sql: str) -> list[list[str | None]]:
        slw.assert_select_only(sql)            # refuses anything but one plain SELECT, before it leaves this process
        return self._run(sql)

    def _run(self, sql: str) -> list[list[str | None]]:
        raise NotImplementedError

    def close(self) -> None:
        pass


def _pg_options() -> str:
    mine = "-c default_transaction_read_only=on -c timezone=UTC -c statement_timeout={0} -c lock_timeout=5000".format(STATEMENT_TIMEOUT_MS)
    prev = os.environ.get("PGOPTIONS", "").strip()
    return (prev + " " + mine).strip()


class PsycopgRunner(Runner):
    def __init__(self, database_url: str | None = None):
        import psycopg  # noqa: PLC0415
        self._conn = psycopg.connect(database_url or "", options=_pg_options())     # empty conninfo: libpq reads PGHOST / PGUSER / ...
        self._conn.autocommit = False
        self._conn.read_only = True

    def _run(self, sql: str) -> list[list[str | None]]:
        cur = self._conn.cursor()
        try:
            cur.execute(sql)
            rows = [[None if v is None else str(v) for v in r] for r in cur.fetchall()]
        finally:
            self._conn.rollback()
        return rows

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:  # noqa: BLE001
            pass


class PsqlRunner(Runner):
    """The client rq.sh uses (`psql -X -A -t`), one process per statement; the libpq environment is inherited."""

    def __init__(self, psql: str | None = None):
        self._psql = psql or shutil.which("psql") or "psql"

    def _run(self, sql: str) -> list[list[str | None]]:
        env = dict(os.environ)
        env["PGOPTIONS"] = _pg_options()
        p = subprocess.run([self._psql, "-X", "-A", "-t", "-q", "-F", FSEP, "--pset=null=\\N", "-v", "ON_ERROR_STOP=1", "-c", sql],
                           capture_output=True, text=True, env=env, timeout=STATEMENT_TIMEOUT_MS // 1000 + 30)
        if p.returncode != 0:
            raise SnapshotError("psql failed: " + p.stderr.strip()[:300])
        rows = []
        for line in p.stdout.split("\n"):
            if line == "":
                continue
            rows.append([None if v == "\\N" else v for v in line.split(FSEP)])
        return rows


def make_runner(driver: str, database_url: str | None) -> Runner:
    if driver == "psql":
        return PsqlRunner()
    if driver == "psycopg":
        return PsycopgRunner(database_url)
    try:
        return PsycopgRunner(database_url)
    except ImportError:
        return PsqlRunner()


# ───────────────────────────────── SQL building ─────────────────────────────────

def column_expr(col: str, data_type: str, udt: str, embeddings: bool) -> str | None:
    """The expression a column contributes to the row object (None: not digested)."""
    c = "s." + q(col)
    if data_type == "timestamp with time zone":
        return "(" + c + " AT TIME ZONE 'UTC')"            # independent of the session TimeZone
    if data_type == "json":
        return c + "::jsonb"
    if data_type == "USER-DEFINED":
        if udt in ("vector", "halfvec", "sparsevec"):
            return ("md5(" + c + "::text)") if embeddings else None
        return c + "::text"
    return c


def obj_text_sql(exprs: Sequence[tuple[str, str]]) -> str:
    """The jsonb text of {column: value, ...} for (column, expression) pairs; batched under jsonb_build_object's argument limit. '' for no columns."""
    if not exprs:
        return "''::text"
    calls = []
    for i in range(0, len(exprs), _BATCH):
        part = exprs[i:i + _BATCH]
        calls.append("jsonb_build_object(" + ", ".join(lit(c) + ", " + e for c, e in part) + ")")
    obj = calls[0] if len(calls) == 1 else "(" + " || ".join(calls) + ")"
    return "(" + obj + ")::text"


def where_sql(chart_id: str, comp: Mapping[str, Any], has_chart: bool, extra: str | None = None) -> str:
    parts = []
    if has_chart and comp.get("kind", "chart") == "chart":
        parts.append('s."chart_id" = ' + lit(chart_id) + "::uuid")
    if comp.get("where_sql"):
        parts.append("(" + comp["where_sql"] + ")")
    if extra:
        parts.append(extra)
    return " AND ".join(parts) if parts else "true"


class RelationInfo:
    def __init__(self, columns: Sequence[tuple[str, str, str]]):
        self.columns = list(columns)
        self.by_name = {c[0]: c for c in self.columns}


def load_relation(runner: Runner, cache: dict, relation: str) -> RelationInfo:
    if relation not in cache:
        rows = runner.run("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = "
                          + lit(ident(relation)) + " ORDER BY ordinal_position")
        if not rows:
            raise SnapshotError("relation not found (or no columns visible): " + relation)
        cache[relation] = RelationInfo([(r[0] or "", r[1] or "", r[2] or "") for r in rows])
    return cache[relation]


class Plan:
    """What a component digests, resolved against the live column list."""

    def __init__(self, comp: Mapping[str, Any], info: RelationInfo, volatile: Mapping[str, Any], embeddings: bool, prose: Mapping[str, Any] | None = None):
        prose = prose or {"names": [], "regex": "(?!x)x"}
        names = [c[0] for c in info.columns]
        self.has_chart = "chart_id" in info.by_name
        self.has_aya = "ayanamsha_id" in info.by_name
        ids = [c for c in (comp.get("id_columns") or []) + (comp.get("id_ref_columns") or []) if c in info.by_name]
        declared = comp.get("content_columns")
        vol_names = set(volatile["names"])
        vol_re = re.compile(volatile["regex"])
        self.missing = []
        excluded: list[str] = []
        if declared:
            content = []
            for c in declared:
                if c not in info.by_name:
                    self.missing.append(c)
                elif c in ids:
                    continue
                else:
                    content.append(c)
        else:
            content = []
            for c in names:
                if c in ids:
                    continue
                if c in vol_names or vol_re.search(c):
                    excluded.append(c)
                else:
                    content.append(c)
        prose_names = set(prose["names"])
        prose_re = re.compile(prose["regex"])
        self.value_exprs: list[tuple[str, str]] = []
        self.prose_exprs: list[tuple[str, str]] = []
        for c in content:
            e = column_expr(c, info.by_name[c][1], info.by_name[c][2], embeddings)
            if e is None:
                excluded.append(c)
            elif c in prose_names or prose_re.search(c):
                self.prose_exprs.append((c, e))
            else:
                self.value_exprs.append((c, e))
        self.content_exprs = self.value_exprs + self.prose_exprs
        self.id_exprs: list[tuple[str, str]] = []
        for c in ids:
            e = column_expr(c, info.by_name[c][1], info.by_name[c][2], embeddings)
            if e is not None:
                self.id_exprs.append((c, e))
        self.id_cols = [c for c, _ in self.id_exprs]
        self.content_cols = [c for c, _ in self.content_exprs]
        covered = set(self.content_cols) | set(self.id_cols)
        self.excluded = sorted(set(excluded) | (set(c for c in names if c not in covered and (c in vol_names or vol_re.search(c)))))
        self.uncovered = [c for c in names if c not in covered and c not in self.excluded]
        self.dims = [d for d in (comp.get("dims") or []) if d in info.by_name]
        if self.has_aya and "ayanamsha_id" not in self.dims:
            self.dims.insert(0, "ayanamsha_id")
        key = [k for k in (comp.get("key") or []) if k in info.by_name]
        self.key_cols = key                                           # the declared natural key (duplicate check)
        row_key = comp.get("row_key") or [k for k in key if k not in ids]
        self.row_key = [k for k in row_key if k in info.by_name and k not in ids]

    def value_obj(self) -> str:
        return obj_text_sql(self.value_exprs)

    def prose_obj(self) -> str:
        return obj_text_sql(self.prose_exprs)

    def ids_obj(self) -> str:
        return obj_text_sql(self.id_exprs)


def _filter_extra(plan: "Plan", aya: str | None) -> str | None:
    return ("s." + q("ayanamsha_id") + " = " + lit(aya)) if aya is not None and plan.has_aya else None


def group_query(chart_id: str, comp: Mapping[str, Any], plan: Plan, aya: str | None) -> str:
    """One row per group: dims..., rows, distinct keys, value / prose / ids digests. Three layers: raw columns -> row hashes -> group aggregates.
    hv = md5(value columns); hp = md5(hv || prose columns); hi = md5(hv || prose columns || id columns): a prose-only change keeps hv, an ids-only
    change keeps hp."""
    nd = len(plan.dims)
    dim_sel = ["coalesce(s." + q(d) + "::text, '<NULL>') AS d" + str(i) for i, d in enumerate(plan.dims)]
    keycols = ["coalesce(s." + q(k) + "::text, '<NULL>')" for k in plan.key_cols]
    keyexpr = ("(" + ", ".join(keycols) + ")::text") if keycols else "NULL::text"
    raw = ("SELECT " + ", ".join(dim_sel + ["md5(" + plan.value_obj() + ") AS hv", plan.prose_obj() + " AS po", plan.ids_obj() + " AS io", keyexpr + " AS kt"])
           + " FROM public." + q(comp["relation"]) + " AS s WHERE " + where_sql(chart_id, comp, plan.has_chart, _filter_extra(plan, aya)))
    dref = ["r.d" + str(i) for i in range(nd)]
    hashed = ("SELECT " + ", ".join(dref + ["r.hv", "md5(r.hv || r.po) AS hp", "md5(r.hv || r.po || r.io) AS hi", "r.kt"]) + " FROM (" + raw + ") AS r")
    gref = ["h.d" + str(i) for i in range(nd)]
    sel = ", ".join(gref + ["count(*)", "count(DISTINCT h.kt)", "md5(string_agg(h.hv, ',' ORDER BY h.hv))", "md5(string_agg(h.hp, ',' ORDER BY h.hp))",
                            "md5(string_agg(h.hi, ',' ORDER BY h.hi))"])
    tail = (" GROUP BY " + ", ".join(gref) + " ORDER BY " + ", ".join(gref)) if gref else ""
    return "SELECT " + sel + " FROM (" + hashed + ") AS h" + tail


def rowdetail_query(chart_id: str, comp: Mapping[str, Any], plan: Plan, aya: str | None) -> str:
    keycols = ["coalesce(s." + q(k) + "::text, '')" for k in plan.row_key]
    keyexpr = (" || " + lit(KSEP) + " || ").join(keycols)
    inner = ("SELECT " + keyexpr + " AS rk, md5(" + plan.value_obj() + ") AS hv, " + plan.prose_obj() + " AS po, " + plan.ids_obj() + " AS io FROM public."
             + q(comp["relation"]) + " AS s WHERE " + where_sql(chart_id, comp, plan.has_chart, _filter_extra(plan, aya)))
    return ("SELECT r.rk, left(r.hv, 12), left(md5(r.hv || r.po), 12), left(md5(r.hv || r.po || r.io), 12) FROM (" + inner + ") AS r ORDER BY 1, 2, 3, 4")


def aya_values_query(chart_id: str, comp: Mapping[str, Any], plan: Plan) -> str:
    return ("SELECT DISTINCT s." + q("ayanamsha_id") + "::text FROM public." + q(comp["relation"]) + " AS s WHERE "
            + where_sql(chart_id, comp, plan.has_chart) + " ORDER BY 1")


# ───────────────────────────────── digesting ─────────────────────────────────

def combine(lines: Iterable[str]) -> str:
    return hashlib.md5("\n".join(sorted(lines)).encode("utf-8")).hexdigest()


def digest_component(runner: Runner, chart_id: str, comp: Mapping[str, Any], volatile: Mapping[str, Any], prose: Mapping[str, Any], cache: dict, *, chunk: bool = True,
                     embeddings: bool = False, rowhash_max: int = DEFAULT_ROWHASH_MAX, clock: Callable[[], float] = time.monotonic) -> dict:
    rec: dict[str, Any] = {"name": comp["name"], "relation": comp["relation"], "where": comp.get("where_desc"), "kind": comp.get("kind", "chart")}
    try:
        info = load_relation(runner, cache, comp["relation"])
        plan = Plan(comp, info, volatile, embeddings, prose)
        rec.update(key=plan.key_cols, row_key=plan.row_key, dims=plan.dims, value_columns=[c for c, _ in plan.value_exprs], prose_columns=[c for c, _ in plan.prose_exprs], id_columns=plan.id_cols,
                   excluded_columns=plan.excluded, uncovered_columns=plan.uncovered, missing_columns=plan.missing)
        chunks: list[str | None] = [None]
        if chunk and plan.has_aya:
            chunks = [r[0] for r in runner.run(aya_values_query(chart_id, comp, plan))] or [None]
        groups: dict[str, dict] = {}
        timings = []
        total = 0
        distinct = 0
        ids_present = bool(plan.id_exprs)
        for aya in chunks:
            t0 = clock()
            rows = runner.run(group_query(chart_id, comp, plan, aya))
            nd = len(plan.dims)
            n_chunk = 0
            for r in rows:
                gk = GSEP.join(r[:nd]) if nd else "*"
                n, nk, v, pr, i = int(r[nd]), int(r[nd + 1]), r[nd + 2], r[nd + 3], r[nd + 4]
                groups[gk] = {"n": n, "k": nk, "v": v, "p": pr}
                if ids_present:
                    groups[gk]["i"] = i
                total += n
                distinct += nk
                n_chunk += n
            timings.append({"chunk": "all" if aya is None else "ayanamsha_id=" + aya, "rows": n_chunk, "seconds": round(clock() - t0, 2)})
        rec["rows"] = total
        rec["distinct_keys"] = distinct if plan.key_cols else None
        rec["groups"] = groups
        rec["content_digest"] = combine(k + "|" + str(g["n"]) + "|" + g["v"] + "|" + g["p"] for k, g in groups.items())
        rec["value_digest"] = combine(k + "|" + str(g["n"]) + "|" + g["v"] for k, g in groups.items())
        rec["ids_digest"] = combine(k + "|" + str(g["n"]) + "|" + str(g.get("i")) for k, g in groups.items()) if ids_present else None
        rec["chunks"] = timings
        rec["row_hashes"] = None
        if plan.row_key and total <= rowhash_max:
            detail: dict[str, list[str]] = {}
            for aya in chunks:
                for r in runner.run(rowdetail_query(chart_id, comp, plan, aya)):
                    detail[r[0] or ""] = [r[1] or "", r[2] or "", r[3] or ""] if ids_present else [r[1] or "", r[2] or ""]
            rec["row_hashes"] = detail
        rec["error"] = None
    except Exception as exc:  # noqa: BLE001
        rec["error"] = (type(exc).__name__ + ": " + str(exc))[:400]
    return rec


def asset_record(runner: Runner, chart_id: str, asset: str, spec: Mapping[str, Any], scopes: Mapping[str, Any], cache: dict, **kw) -> dict:
    comps = [digest_component(runner, chart_id, c, scopes["volatile"], scopes["prose"], cache, **kw) for c in spec["components"]]
    err = [c["name"] + ": " + c["error"] for c in comps if c["error"]]
    rec = {"asset": asset, "layer": spec["layer"], "status": "error" if err else "ok", "error": "; ".join(err) if err else None,
           "components": {c["name"]: c for c in comps}}
    if not err:
        rec["rows"] = sum(c["rows"] for c in comps)
        rec["content_digest"] = combine(c["name"] + "|" + c["content_digest"] for c in comps)
        rec["ids_digest"] = combine(c["name"] + "|" + str(c["ids_digest"]) for c in comps)
    return rec


def registry_count(runner: Runner, chart_id: str, asset: str) -> dict:
    rows = runner.run("SELECT count_sql FROM asset_registry WHERE asset_id = " + lit(ident(asset)))
    if not rows or not rows[0][0]:
        return {"result": "no_count_sql"}
    sql = rows[0][0].strip().rstrip(";").replace("$1", lit(chart_id))
    try:
        slw.assert_select_only(sql)
    except Exception as exc:  # noqa: BLE001
        return {"result": "refused", "detail": str(exc)[:160]}
    try:
        out = runner.run("SELECT * FROM (" + sql + ") AS stored_count LIMIT 1")
        return {"result": "ok", "count": int(out[0][0]) if out and out[0][0] is not None else None}
    except Exception as exc:  # noqa: BLE001
        return {"result": "error", "detail": (type(exc).__name__ + ": " + str(exc))[:200]}


def build_snapshot(runner: Runner, scopes: Mapping[str, Any], *, chart_id: str = CANONICAL_CHART, assets: Sequence[str] | None = None,
                   layer: str | None = None, previous: Mapping[str, Any] | None = None, on_asset: Callable[[dict], None] | None = None,
                   registry_counts: bool = False, now: Callable[[], datetime] | None = None, **kw) -> dict:
    if not _UUID.fullmatch(chart_id):
        raise SnapshotError("chart id is not a uuid")
    now = now or (lambda: datetime.now(timezone.utc))
    all_specs = dict(scopes["assets"])
    if scopes.get("residual"):
        all_specs[RESIDUAL_ASSET] = scopes["residual"]
    want = list(assets) if assets else asset_names(scopes, layer) + ([RESIDUAL_ASSET] if scopes.get("residual") and layer in (None, "all", "L1") else [])
    unknown = [a for a in want if a not in all_specs]
    if unknown:
        raise SnapshotError("not an L1/L2 snapshot asset: " + ", ".join(unknown))
    doc: dict[str, Any] = {"schema": SCHEMA, "chart_id": chart_id, "scopes_sha256": scopes_sha(scopes), "generated_at": now().astimezone(timezone.utc).isoformat(timespec="seconds"),
                           "options": {k: v for k, v in kw.items() if k in ("chunk", "embeddings", "rowhash_max")}, "assets": {}}
    if previous and previous.get("scopes_sha256") == doc["scopes_sha256"] and previous.get("chart_id") == chart_id:
        doc["assets"] = {a: r for a, r in previous.get("assets", {}).items() if r.get("status") == "ok"}
    cache: dict = {}
    for a in want:
        if a in doc["assets"]:
            continue
        spec = all_specs[a]
        rec = asset_record(runner, chart_id, a, spec, scopes, cache, **kw)
        if registry_counts and a != RESIDUAL_ASSET:
            rec["registry_count"] = registry_count(runner, chart_id, a)
        doc["assets"][a] = rec
        if on_asset:
            on_asset(doc)
    return doc


# ───────────────────────────────── compare ─────────────────────────────────

def _split_key(text: str) -> list[str]:
    return text.split(KSEP)


def diff_component(b: Mapping[str, Any], f: Mapping[str, Any]) -> dict:
    """Group-level (and row-level when both sides carry it) differences of one component."""
    out: dict[str, Any] = {"groups": [], "rows": []}
    dims = f.get("dims") or b.get("dims") or []
    for gk in sorted(set(b["groups"]) | set(f["groups"])):
        gb, gf = b["groups"].get(gk), f["groups"].get(gk)
        if gb is None:
            kind = "added"
        elif gf is None:
            kind = "removed"
        elif gb["v"] != gf["v"] or gb["n"] != gf["n"]:
            kind = "value"
        elif gb["p"] != gf["p"]:
            kind = "prose"
        elif gb.get("i") != gf.get("i"):
            kind = "ids_only"
        else:
            continue
        vals = gk.split(GSEP) if dims else []
        out["groups"].append({"group": gk, "dims": dict(zip(dims, vals)), "kind": kind, "n_before": gb["n"] if gb else 0, "n_after": gf["n"] if gf else 0})
    rb, rf = b.get("row_hashes"), f.get("row_hashes")
    if rb is not None and rf is not None:
        rk = f.get("row_key") or b.get("row_key") or []
        for k in sorted(set(rb) | set(rf)):
            vb, vf = rb.get(k), rf.get(k)
            if vb is None:
                kind = "added"
            elif vf is None:
                kind = "removed"
            elif vb[0] != vf[0]:
                kind = "value"
            elif vb[1] != vf[1]:
                kind = "prose"
            elif vb != vf:
                kind = "ids_only"
            else:
                continue
            out["rows"].append({"key": dict(zip(rk, _split_key(k))), "kind": kind})
    return out


def _match_value(want: Any, have: str) -> bool:
    items = want if isinstance(want, list) else [want]
    return any(fnmatch.fnmatchcase(have, str(w)) for w in items)


def _entry_matches(entry: Mapping[str, Any], relation: str, where_have: Mapping[str, str], kind: str) -> tuple[bool, list[str]]:
    """(matches, unverified_columns): a condition on a column we cannot see at this granularity is unverified, not failed."""
    sc = entry.get("scope") or {}
    if sc.get("relation") and sc["relation"] != relation:
        return False, []
    want = entry.get("change", "any")
    ok_kinds = {"any": None, "content": {"value", "prose", "added", "removed"}, "value": {"value", "added", "removed"}, "prose": {"prose"}, "ids_only": {"ids_only"},
                "added": {"added"}, "removed": {"removed"}}
    if want not in ok_kinds:
        return False, []
    if ok_kinds[want] is not None and kind not in ok_kinds[want]:
        return False, []
    unver = []
    for col, want in (sc.get("where") or {}).items():
        if col in where_have:
            if not _match_value(want, where_have[col]):
                return False, []
        else:
            unver.append(col)
    return True, unver


def compare(before: Mapping[str, Any], after: Mapping[str, Any], predicted: Mapping[str, Any] | None = None) -> dict:
    """Per asset: IDENTICAL / CHANGED / INCOMPARABLE, every change EXPECTED or UNEXPECTED, and predicted changes never seen."""
    predicted = predicted or {"assets": {}}
    result: dict[str, Any] = {"chart_id": after.get("chart_id"), "assets": {}, "summary": {}}
    notes = []
    if before.get("chart_id") != after.get("chart_id"):
        notes.append("chart ids differ")
    if before.get("scopes_sha256") != after.get("scopes_sha256"):
        notes.append("scopes_sha256 differs (the two snapshots were taken with different scope data): digests may not be comparable")
    result["notes"] = notes
    for a in sorted(set(before["assets"]) | set(after["assets"])):
        b, f = before["assets"].get(a), after["assets"].get(a)
        rec: dict[str, Any] = {"asset": a, "changes": [], "predicted_not_seen": []}
        result["assets"][a] = rec
        if not b or not f:
            rec.update(verdict="INCOMPARABLE", why="asset missing from the " + ("before" if not b else "after") + " snapshot")
            continue
        if b["status"] != "ok" or f["status"] != "ok":
            rec.update(verdict="INCOMPARABLE", why="not read cleanly: before=" + str(b.get("error")) + " after=" + str(f.get("error")))
            continue
        rec["rows_before"], rec["rows_after"] = b["rows"], f["rows"]
        entries = list((predicted.get("assets") or {}).get(a, []))
        used = {id(e): 0 for e in entries}
        seen_entry = {id(e): False for e in entries}
        for cname in sorted(set(b["components"]) | set(f["components"])):
            cb, cf = b["components"].get(cname), f["components"].get(cname)
            if cb is None or cf is None:
                rec["changes"].append({"component": cname, "relation": (cb or cf)["relation"], "kind": "component_" + ("added" if cb is None else "removed"), "verdict": "UNEXPECTED",
                                       "detail": "component present in only one snapshot"})
                continue
            if cb["content_digest"] == cf["content_digest"] and cb.get("ids_digest") == cf.get("ids_digest") and cb["rows"] == cf["rows"]:
                continue
            d = diff_component(cb, cf)
            moved = sorted({g["kind"] for g in d["groups"]})
            if cb["rows"] != cf["rows"]:
                moved.insert(0, "rows")
            have_rows = bool(d["rows"]) or (cb.get("row_hashes") is not None and cf.get("row_hashes") is not None)
            items = []
            if have_rows:
                for r in d["rows"]:
                    items.append({"where": dict(r["key"]), "kind": r["kind"], "rows": 1, "row_level": True})
                # row hashes are keyed by the row key only: a group change not visible in the row detail is still reported at group level
            else:
                for g in d["groups"]:
                    items.append({"where": dict(g["dims"]), "kind": g["kind"], "rows": abs(g["n_after"] - g["n_before"]) or None, "row_level": False, "group_rows": max(g["n_before"], g["n_after"])})
            per_entry: dict[int, int] = {}
            for it in items:
                matched = None
                unver: list[str] = []
                for e in entries:
                    ok, uv = _entry_matches(e, cb["relation"], it["where"], it["kind"])
                    if ok:
                        matched, unver = e, uv
                        break
                ch = {"component": cname, "relation": cb["relation"], "kind": it["kind"], "where": it["where"], "rows": it["rows"], "row_level": it["row_level"]}
                if matched is None:
                    ch["verdict"] = "UNEXPECTED"
                else:
                    ch["verdict"] = "EXPECTED"
                    ch["predicted"] = matched.get("id")
                    if unver:
                        ch["unverified_columns"] = unver
                    used[id(matched)] += it["rows"] or 1
                    seen_entry[id(matched)] = True
                    per_entry[id(matched)] = per_entry.get(id(matched), 0) + 1
                rec["changes"].append(ch)
            rec.setdefault("moved", {})[cname] = moved
        for e in entries:
            exp, cap = e.get("expected_rows"), e.get("max_rows")
            if seen_entry[id(e)] and (exp is not None or cap is not None):
                got = used[id(e)]
                rowlevel = all(c.get("row_level") for c in rec["changes"] if c.get("predicted") == e.get("id"))
                bad = None
                if rowlevel and exp is not None and got != exp:
                    bad = "predicted " + str(exp) + " rows, observed " + str(got)
                if rowlevel and cap is not None and got > cap:
                    bad = "predicted at most " + str(cap) + " rows, observed " + str(got)
                if bad:
                    for c in rec["changes"]:
                        if c.get("predicted") == e.get("id"):
                            c["verdict"] = "UNEXPECTED"
                            c["why"] = bad
            if not seen_entry[id(e)] and not e.get("optional"):
                rec["predicted_not_seen"].append({"id": e.get("id"), "description": e.get("description"), "expected_rows": exp})
        if not rec["changes"]:
            rec["verdict"] = "IDENTICAL"
        else:
            rec["verdict"] = "CHANGED"
    unexpected = 0
    for a, rec in result["assets"].items():
        unexpected += sum(1 for c in rec["changes"] if c["verdict"] == "UNEXPECTED") + (1 if rec["verdict"] == "INCOMPARABLE" else 0)
    result["summary"] = {"assets": len(result["assets"]),
                         "identical": sum(1 for r in result["assets"].values() if r["verdict"] == "IDENTICAL"),
                         "changed": sum(1 for r in result["assets"].values() if r["verdict"] == "CHANGED"),
                         "incomparable": sum(1 for r in result["assets"].values() if r["verdict"] == "INCOMPARABLE"),
                         "unexpected_changes": unexpected,
                         "predicted_not_seen": sum(len(r["predicted_not_seen"]) for r in result["assets"].values())}
    return result


def render_compare(res: Mapping[str, Any], before: Mapping[str, Any], after: Mapping[str, Any], verbose: bool = False) -> str:
    lines = ["chart " + str(res["chart_id"]) + "   before " + str(before.get("generated_at")) + "   after " + str(after.get("generated_at"))]
    lines += ["NOTE: " + n for n in res["notes"]]
    for a, rec in res["assets"].items():
        head = "{0:<28} {1}".format(a, rec["verdict"])
        if rec["verdict"] == "INCOMPARABLE":
            lines.append(head + "  (" + rec["why"] + ")")
            continue
        head += "   rows " + str(rec["rows_before"]) + " -> " + str(rec["rows_after"])
        lines.append(head)
        for cname, moved in sorted(rec.get("moved", {}).items()):
            lines.append("    component " + cname + ": moved " + "+".join(moved))
        for c in rec["changes"]:
            w = ",".join(k + "=" + str(v) for k, v in sorted(c.get("where", {}).items()))
            tag = c["verdict"] + (" [" + str(c.get("predicted")) + "]" if c.get("predicted") else "")
            extra = ("  " + c["why"]) if c.get("why") else (("  (unverified at this granularity: " + ",".join(c["unverified_columns"]) + ")") if c.get("unverified_columns") else "")
            lines.append("    " + tag + "  " + c["relation"] + " " + c["kind"] + "  " + str(c.get("rows") if c.get("rows") is not None else "?") + " row(s)"
                         + ("" if c.get("row_level") else " (group level)") + "  {" + w + "}" + extra)
        for p in rec["predicted_not_seen"]:
            lines.append("    PREDICTED-NOT-SEEN  [" + str(p["id"]) + "] " + str(p["description"]))
    s = res["summary"]
    lines.append("")
    lines.append("SUMMARY  assets " + str(s["assets"]) + "  IDENTICAL " + str(s["identical"]) + "  CHANGED " + str(s["changed"]) + "  INCOMPARABLE " + str(s["incomparable"])
                 + "  UNEXPECTED changes " + str(s["unexpected_changes"]) + "  predicted-not-seen " + str(s["predicted_not_seen"]))
    return "\n".join(lines)


# ───────────────────────────────── listing / CLI ─────────────────────────────────

def render_list(scopes: Mapping[str, Any], layer: str | None) -> str:
    lines = []
    names = asset_names(scopes, layer) + ([RESIDUAL_ASSET] if scopes.get("residual") and layer in (None, "all", "L1") else [])
    for a in names:
        spec = scopes["assets"].get(a) or scopes["residual"]
        lines.append(a + "  (" + spec["layer"] + ")")
        for c in spec["components"]:
            lines.append("    " + c["relation"] + "  [" + (c.get("where_text") or "all rows of the chart") + "]  key=" + ",".join(c.get("key") or ["(runtime PK)"])
                         + "  ids=" + ",".join((c.get("id_columns") or []) + (c.get("id_ref_columns") or [])) + "  source=" + str(c.get("source")))
    return "\n".join(lines)


def _write_atomic(path: str, doc: Mapping[str, Any]) -> None:
    tmp = path + ".tmp"
    Path(tmp).write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="l12_chart_snapshot.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", help="write the snapshot JSON here (outside the repo)")
    p.add_argument("--layer", choices=["L1", "L2", "all"], default="all")
    p.add_argument("--assets", help="comma-separated subset (default: the whole layer)")
    p.add_argument("--chart-id", default=CANONICAL_CHART)
    p.add_argument("--allow-other-chart", action="store_true", help="the snapshot is defined for the canonical chart only; this lifts the refusal")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--no-chunk", action="store_true")
    p.add_argument("--embeddings", action="store_true", help="digest embedding vector columns too (md5 of the text form: heavy)")
    p.add_argument("--rowhash-max", type=int, default=DEFAULT_ROWHASH_MAX)
    p.add_argument("--registry-counts", action="store_true")
    p.add_argument("--driver", choices=["auto", "psycopg", "psql"], default="auto")
    p.add_argument("--scopes", default=str(DEFAULT_SCOPES))
    p.add_argument("--predicted", default=str(DEFAULT_PREDICTED))
    p.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    p.add_argument("--json", action="store_true", help="--compare: print the machine-readable result")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--list", action="store_true", help="offline: print the components each asset digests")
    a = p.parse_args(argv)
    try:
        if a.list:
            print(render_list(load_scopes(a.scopes), None if a.layer == "all" else a.layer))
            return 0
        if a.compare:
            docs = [json.loads(Path(x).read_text(encoding="utf-8")) for x in a.compare]
            pred = json.loads(Path(a.predicted).read_text(encoding="utf-8")) if a.predicted and Path(a.predicted).exists() else {"assets": {}}
            res = compare(docs[0], docs[1], pred)
            print(json.dumps(res, indent=1, sort_keys=True) if a.json else render_compare(res, docs[0], docs[1], a.verbose))
            return 1 if res["summary"]["unexpected_changes"] else 0
        if not a.out:
            p.error("--out is required for a snapshot")
        if a.chart_id != CANONICAL_CHART and not a.allow_other_chart:
            print("ERROR: the snapshot is defined for the canonical chart " + CANONICAL_CHART + " only", file=sys.stderr)
            return 2
        scopes = load_scopes(a.scopes)
        previous = None
        if a.resume and Path(a.out).exists():
            previous = json.loads(Path(a.out).read_text(encoding="utf-8"))
        runner = make_runner(a.driver, os.environ.get("DATABASE_URL"))
        assets = [x.strip() for x in a.assets.split(",")] if a.assets else None

        def progress(doc: dict) -> None:
            _write_atomic(a.out, doc)
            last = list(doc["assets"])[-1]
            r = doc["assets"][last]
            print(last + " " + r["status"] + " rows=" + str(r.get("rows")) + (" ERROR " + str(r["error"]) if r["error"] else ""), file=sys.stderr)

        try:
            doc = build_snapshot(runner, scopes, chart_id=a.chart_id, assets=assets, layer=None if a.layer == "all" else a.layer, previous=previous, on_asset=progress,
                                 registry_counts=a.registry_counts, chunk=not a.no_chunk, embeddings=a.embeddings, rowhash_max=a.rowhash_max)
        finally:
            runner.close()
        _write_atomic(a.out, doc)
        summary = [{"asset": k, "status": v["status"], "rows": v.get("rows"), "content": (v.get("content_digest") or "")[:12], "ids": (v.get("ids_digest") or "")[:12]}
                   for k, v in sorted(doc["assets"].items())]
        print(json.dumps(summary, indent=0, sort_keys=True))
        return 3 if any(v["status"] != "ok" for v in doc["assets"].values()) else 0
    except SnapshotError as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print("ERROR: " + type(exc).__name__ + ": " + str(exc), file=sys.stderr)
        return 5


if __name__ == "__main__":
    raise SystemExit(main())
