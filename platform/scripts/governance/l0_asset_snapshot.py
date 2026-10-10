#!/usr/bin/env python3
"""l0_asset_snapshot.py -- READ-ONLY per-asset row counts and content digests for the 40 L0 assets.

WHAT IT GIVES
  For every asset of the committed L0 registry snapshot: the fingerprint UNIT the global dispatch tool would compare for a forced rebuild
  of that asset (own tables + every group table + every writer-run sibling's tables), the unit's COMPOSITE digest, and per table the
  sha256 and the row count. The digest is read through the dispatch tool's OWN function (`suvarna_global_asset_dispatch.read_fingerprint`
  over E5.5 `nikasha_stale_certs.load_rows` / `fingerprint_rows`): this file defines no digest of its own, so "IDENTICAL" here means
  exactly what the tool's "identical" means (excluded columns: surrogate id, build_id, wall-clock columns, as declared in
  00_ARCHITECTURE/control/FINGERPRINT_DECLARATIONS.json).
  Assets with no declared unit (services, bg_sarvatobhadra_grid, bg_compendium_index, bg_gochara_citation_resolution) get a plain
  count(*) of their registry target table (no digest: nothing declares a key for it) and a `note`.
  Optional `--integrity`: also runs each asset's stored registry `integrity_check_sql` (one SELECT, read-only session, guard `assert_query_only`: one SELECT or WITH ... SELECT, no write keyword, READ ONLY session) and records its first column (true / false / error): the acceptance reading for assets whose pin lives there (bg_cohort 1327).

HOW IT CONNECTS (same convention as the dispatch tool and the census: libpq)
  `DATABASE_URL` if set, else the libpq environment (PGHOST / PGUSER / PGDATABASE / PGPASSWORD ...), which is what Exec's
  `source ~/.config/suvarna/pgenv.sh` sets for rq.sh. The session is READ ONLY (psycopg `read_only = True`, ROLLBACK at the end, never a
  COMMIT). It reads no credential file and writes nothing but the JSON file named by --out (and stdout).

USAGE
  python3 platform/scripts/governance/l0_asset_snapshot.py --out /path/outside/repo/L0_SNAPSHOT_before.json [--assets bg_vastu_directions,bg_yogas]
         [--integrity] [--skip-large]
  python3 platform/scripts/governance/l0_asset_snapshot.py --compare before.json after.json     # offline: per asset IDENTICAL / CHANGED / counts

  --skip-large   leave out the assets whose tables are large (bg_ephemeris, bg_sky_calendar, bg_muhurta_lattice, bg_texts, bg_text_index,
                 bg_gochara_arcs): their digest reads stream every row (the CLI reads every table through a server-side cursor in 5,000-row chunks, so each
                 database statement stays short; the digest is the same as a plain read).
EXIT  0 ok | 2 bad input | 3 a table could not be read (the asset is recorded as `unreadable`; the rest are still written) | 5 unexpected
"""
from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import fingerprint_declarations as fd  # noqa: E402
import suvarna_global_asset_dispatch as gad  # noqa: E402
import suvarna_level_wave as slw  # noqa: E402

SCHEMA = "suvarna.l0_asset_snapshot/1"
REPO_ROOT = HERE.parents[2]
DEFAULT_REGISTRY_SNAPSHOT = REPO_ROOT / "00_ARCHITECTURE/briefs/nirmana/L0_ASSET_REGISTRY_SNAPSHOT_2026-09-04.json"
LARGE_ASSETS = ("bg_ephemeris", "bg_sky_calendar", "bg_muhurta_lattice", "bg_texts", "bg_text_index", "bg_gochara_arcs")
_IDENT = re.compile(r"[a-z_][a-z0-9_]{0,62}")


def _psycopg_ro_connect(database_url: str | None) -> Callable[[], Any]:
    """READ ONLY, tuple rows (the tool's own `_psycopg_fp_connect_factory` when DATABASE_URL is set; libpq environment otherwise)."""
    if database_url:
        return gad._psycopg_fp_connect_factory(database_url)

    def connect():
        import psycopg  # noqa: PLC0415
        conn = psycopg.connect("")                      # empty conninfo: libpq reads PGHOST / PGUSER / PGDATABASE / ... (what pgenv.sh sets)
        conn.autocommit = False
        conn.read_only = True
        return conn
    return connect


def asset_members(decls, asset: str, sibs: Sequence[str]) -> list[str]:
    return [asset] + sorted(set(sibs) - {asset})


def unit_for_snapshot(decls, asset: str, sibs: Sequence[str]) -> tuple[str | None, str | None]:
    """The fingerprint unit id of `asset` EXACTLY as `declared_unit_or_refuse` composes it (own tables, then each group unit, for the asset and its writer-run
    siblings, de-duplicated, `+`-joined), but WITHOUT the dispatch refusals (seeded group, non-deterministic, partial): a snapshot is useful for an asset the tool
    would refuse. Returns (unit | None, note | None); None when the asset or a sibling is not a declared unit."""
    units = decls.units()
    comps: list[str] = []
    for m in asset_members(decls, asset, sibs):
        entry = gad._declared_entry(decls, m)
        mine: list[str] = []
        if entry is not None and entry.get("status") == "declared":
            if entry.get("tables"):
                mine.append(m)
            for g in entry.get("groups") or []:
                mine.append(decls.group_unit(g))
        if not mine or any(u not in units for u in mine):
            un = decls.undeclared_assets().get(m)
            return None, (f"{m} is not a declared fingerprint unit" + (f" ({un['reason_code']})" if un else ""))
        for u in mine:
            if u not in comps:
                comps.append(u)
    return gad.UNIT_SEP.join(comps), None


def _count_table(conn, table: str) -> int:
    if not _IDENT.fullmatch(table):
        raise ValueError(f"not a plain table name: {table!r}")
    cur = conn.cursor()
    cur.execute(f'SELECT count(*) FROM "{table}"')
    n = cur.fetchone()[0]
    conn.rollback()
    return int(n)


STREAM_MAX_ROWS = 2_000_000
STREAM_CURSOR_PREFIX = "l0snap"


def streaming_reader(max_rows: int = STREAM_MAX_ROWS):
    """The tool's own fingerprint reader, reading every table through a server-side (named) cursor fetched in 5,000-row chunks: the SAME rows and the SAME
    canonical hashing as the default read, so a digest taken this way equals one taken the plain way; it only keeps each database statement short (a
    single `SELECT *` over bg_ephemeris / bg_muhurta_lattice / bg_text_index hit the statement timeout and a dropped connection on the first run)."""
    return functools.partial(fd.unit_fingerprints, cursor_prefix=STREAM_CURSOR_PREFIX, max_rows=max_rows)


def assert_query_only(sql: str) -> None:
    """One read-only query: a SELECT, or a WITH ... SELECT. The dispatch lexer's `assert_select_only` refuses every WITH (the stored integrity checks of
    bg_remedies and bg_texts start with one), so this is the same guard with the one difference: the statement may start with WITH. Everything else of
    that guard is kept (one statement, comments and strings lexed out first, no write / DDL / session-state keyword, so a data-modifying CTE is still
    refused); the connection is also READ ONLY, which refuses a write at the server."""
    if not isinstance(sql, str):
        raise ValueError("statement must be a string")
    s = slw._lex_code(sql).strip()
    if s.endswith(";"):
        s = s[:-1].rstrip()
    if not s:
        raise ValueError("empty statement")
    if ";" in s:
        raise ValueError("multiple statements are not allowed")
    if not re.match(r"(SELECT|WITH)\b", s, re.IGNORECASE):
        raise ValueError("only a SELECT or WITH ... SELECT statement may be run against the catalog")
    bad = slw._FORBIDDEN.search(s)
    if bad:
        raise ValueError(f"statement contains a non-read-only construct: {bad.group(0)!r}")


def _run_integrity(conn, sql: str) -> dict:
    """The stored integrity check as ONE read-only query (`assert_query_only`: a SELECT or WITH ... SELECT); first column of the first row."""
    try:
        assert_query_only(sql)
    except Exception as exc:  # noqa: BLE001
        return {"result": "refused", "detail": f"{type(exc).__name__}: {exc}"[:200]}
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM (" + sql.strip().rstrip(";") + ") AS stored_integrity_check LIMIT 1")
        row = cur.fetchone()
        conn.rollback()
        v = None if row is None else row[0]
        return {"result": "true" if v is True or (isinstance(v, (int, float)) and not isinstance(v, bool) and v != 0) else "false",
                "sha256_of_sql": hashlib.sha256(sql.encode("utf-8")).hexdigest()[:12]}
    except Exception as exc:  # noqa: BLE001
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        return {"result": "error", "detail": f"{type(exc).__name__}: {exc}"[:200]}


def build_snapshot(*, repo: str, registry: Sequence[Mapping[str, Any]], decls, connect: Callable[[], Any], assets: Sequence[str] | None = None,
                   integrity: bool = False, integrity_sql: Mapping[str, str] | None = None, reader=fd.unit_fingerprints,
                   now: Callable[[], datetime] | None = None) -> dict:
    """The snapshot document. `connect` returns a READ ONLY connection; `reader` is the dispatch tool's fingerprint reader (injectable for tests)."""
    now = now or (lambda: datetime.now(timezone.utc))
    want = list(assets) if assets else [r["asset_id"] for r in registry]
    by_id = {r["asset_id"]: r for r in registry}
    unknown = [a for a in want if a not in by_id]
    if unknown:
        raise ValueError(f"not an L0 registry asset: {unknown}")
    out: dict[str, Any] = {}
    for a in want:
        row = by_id[a]
        rec: dict[str, Any] = {"asset": a, "target_table": row.get("target_table"), "has_writer": bool(row.get("has_writer")), "asset_kind": row.get("asset_kind")}
        try:
            sibs = gad.writer_siblings(repo, a) if row.get("has_writer") else []
        except slw.LevelWaveRefusal as exc:
            sibs, rec["sibling_scan"] = [], "; ".join(r["detail"][:120] for r in exc.refusals)
        unit, note = unit_for_snapshot(decls, a, sibs)
        rec["writer_siblings"] = sibs
        if unit is None:
            rec.update(status="undeclared", unit=None, composite=None, tables={}, note=note)
            tbl = row.get("target_table")
            if tbl:
                conn = connect()
                try:
                    rec["tables"] = {tbl: {"sha256": None, "rows": _count_table(conn, tbl)}}
                    rec["total_rows"] = rec["tables"][tbl]["rows"]
                except Exception as exc:  # noqa: BLE001
                    rec.update(status="unreadable", note=f"{note}; count failed: {type(exc).__name__}: {exc}"[:300])
                finally:
                    conn.close()
            out[a] = rec
            continue
        try:
            fp = gad.read_fingerprint(connect, decls, unit, reader=reader)
            rec.update(status="declared", unit=unit, composite=fp["composite"], definition=fp["definition"], tables=fp["tables"],
                       total_rows=gad.unit_row_count(fp), reproducibility=sorted({r for u in unit.split(gad.UNIT_SEP) for r in decls.reproducibility(u)}))
        except slw.LevelWaveRefusal as exc:
            rec.update(status="unreadable", unit=unit, composite=None, tables={}, note="; ".join(r["detail"][:200] for r in exc.refusals))
        if integrity:
            sql = (integrity_sql or {}).get(a)
            if sql is None:
                rec["integrity"] = {"result": "no_stored_check"}
            else:
                conn = connect()
                try:
                    rec["integrity"] = _run_integrity(conn, sql)
                finally:
                    conn.close()
        out[a] = rec
    return {"schema": SCHEMA, "generated_at": now().astimezone(timezone.utc).isoformat(timespec="seconds"), "declarations_sha256": decls.sha256,
            "fingerprint_definition": fd.FINGERPRINT_DEFINITION, "assets": out}


def compare(before: Mapping[str, Any], after: Mapping[str, Any]) -> list[dict]:
    """Per asset: IDENTICAL (same composite, same per-table sha256 and rows), CHANGED (with the tables that differ and the row counts), or INCOMPARABLE."""
    rows = []
    for a in sorted(set(before["assets"]) | set(after["assets"])):
        b, f = before["assets"].get(a), after["assets"].get(a)
        if not b or not f:
            rows.append({"asset": a, "verdict": "INCOMPARABLE", "why": "asset missing from one snapshot"})
            continue
        if b.get("status") != "declared" or f.get("status") != "declared" or b.get("unit") != f.get("unit"):
            same_counts = {t: v["rows"] for t, v in b.get("tables", {}).items()} == {t: v["rows"] for t, v in f.get("tables", {}).items()}
            rows.append({"asset": a, "verdict": "COUNT_ONLY_SAME" if same_counts and b.get("tables") else "INCOMPARABLE",
                         "why": f"status {b.get('status')}/{f.get('status')}, unit {b.get('unit')}/{f.get('unit')}",
                         "rows_before": b.get("total_rows"), "rows_after": f.get("total_rows")})
            continue
        diff = sorted(t for t in set(b["tables"]) | set(f["tables"]) if b["tables"].get(t) != f["tables"].get(t))
        rows.append({"asset": a, "verdict": "IDENTICAL" if not diff and b["composite"] == f["composite"] else "CHANGED", "changed_tables": diff,
                     "rows_before": b["total_rows"], "rows_after": f["total_rows"], "composite_before": b["composite"], "composite_after": f["composite"]})
    return rows


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="l0_asset_snapshot.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--out", help="write the snapshot JSON here (outside the repo)")
    p.add_argument("--assets", help="comma-separated subset of the 40 L0 assets (default all)")
    p.add_argument("--integrity", action="store_true", help="also run each asset's stored integrity_check_sql (read-only) and record true / false / error")
    p.add_argument("--skip-large", action="store_true", help="leave out " + ", ".join(LARGE_ASSETS))
    p.add_argument("--registry-snapshot", default=str(DEFAULT_REGISTRY_SNAPSHOT))
    p.add_argument("--declarations", default=str(fd.DEFAULT_DECLARATIONS))
    p.add_argument("--repo", default=str(REPO_ROOT))
    p.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"), help="offline: compare two snapshot files, no database")
    a = p.parse_args(argv)
    try:
        if a.compare:
            docs = [json.loads(Path(x).read_text(encoding="utf-8")) for x in a.compare]
            print(json.dumps(compare(docs[0], docs[1]), indent=1, sort_keys=True))
            return 0
        registry = json.loads(Path(a.registry_snapshot).read_text(encoding="utf-8"))
        decls = gad.load_declarations_or_refuse(a.declarations)
        want = [x.strip() for x in a.assets.split(",")] if a.assets else [r["asset_id"] for r in registry]
        if a.skip_large:
            want = [x for x in want if x not in LARGE_ASSETS]
        connect = _psycopg_ro_connect(os.environ.get("DATABASE_URL"))
        integrity_sql = None
        if a.integrity:                         # the LIVE stored text (the registry snapshot's is frozen history): one read of asset_registry
            conn = connect()
            try:
                cur = conn.cursor()
                cur.execute("SELECT asset_id, integrity_check_sql FROM asset_registry WHERE asset_id = ANY(%s)", (want,))
                integrity_sql = {r[0]: r[1] for r in cur.fetchall() if r[1]}
                conn.rollback()
            finally:
                conn.close()
        snap = build_snapshot(repo=a.repo, registry=registry, decls=decls, connect=connect, assets=want, integrity=a.integrity, integrity_sql=integrity_sql,
                              reader=streaming_reader())
    except slw.LevelWaveRefusal as exc:
        print(json.dumps({"refused": exc.refusals}, indent=1, default=str), file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 5
    text = json.dumps(snap, indent=1, sort_keys=True, default=str) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    summary = [{"asset": k, "status": v["status"], "rows": v.get("total_rows"), "composite": (v.get("composite") or "")[:16], **({"integrity": v["integrity"]["result"]} if "integrity" in v else {})}
               for k, v in snap["assets"].items()]
    print(json.dumps(summary, indent=0, sort_keys=True))
    return 3 if any(v["status"] == "unreadable" for v in snap["assets"].values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
