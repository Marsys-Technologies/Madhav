"""Candidate extract generation — the EXACT command the Stage-1 freeze records (SI addendum v1.3 §5).

    python3 -m services.gochara_eval.dump_extract --generation {generation} --stage1 {stage1} --pinned-at {pinned_at} --out {out}

Read-only: one SELECT inside a READ ONLY transaction against `kala_gochara_windows` (the DSN comes from the environment variable
GOCHARA_EVAL_READONLY_DSN or, with --libpq-env, the libpq PG* variables — never from the command line). It REFUSES to run unless the Stage-1 freeze verifies (no placeholders,
every pre-extract input hash and the running-code hashes match) — so no candidate extract can be generated before the freeze is
committed. Governed generations ('5.x') are refused outright: they live in the eval-window tables, which have no reader yet
(review packet v1_10 §C2).

si := raw_intensity, the UNSIGNED magnitude (protocol §4.5: si is stored non-negative for every class). The 4.x writer stores
signed_intensity = raw_intensity * (-1 if adverse else 1), which the §4.5 adapter would reject on every adverse window; the pinned
'3.0' extract's `si` is signed_intensity AND raw_intensity (equal on all 914 rows, none negative). The dump stops if any row has
|signed_intensity| != raw_intensity or raw_intensity < 0.

The output is DETERMINISTIC: a total `ORDER BY` over every selected column (the plan v1.1 SQL ordered by (event_class, ws) only,
which leaves ties in database-defined order and would make the file hash unstable), the same JSON layout as the pinned '3.0'
extract (indent 1, no trailing newline), and a `pinned_at` that is an argument, not the clock.

`--requalify-3-0` re-dumps generation '3.0' (a baseline, not a candidate; no freeze needed) and reports whether the bytes equal
the pinned extract — the detector that this command dumps what the pinned file contains.
"""
from __future__ import annotations

import argparse
import datetime as dt
import decimal
import hashlib
import json
import os
import re
import sys
from pathlib import Path

from .freeze import FreezeRefused, require_stage1

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
H_START = "1998-01-01"
H_END_EXCL = "2026-04-18"
CANDIDATE_GENERATIONS = ("4.1",)
BASELINE_GENERATIONS = ("3.0",)
DSN_ENV = "GOCHARA_EVAL_READONLY_DSN"
CANONICAL_COMMAND = ("python3 -m services.gochara_eval.dump_extract --generation {generation} --stage1 {stage1} "
                     "--pinned-at {pinned_at} --out {out}")
COLUMNS = ["event_class", "ws", "we", "pk", "si", "valence", "adv", "resolution", "temporal_shape"]
TZ_CONVENTION = "dates converted to IST civil dates via (ts at time zone 'Asia/Kolkata')::date"

SQL_HORIZON = """SELECT COUNT(*) FROM kala_gochara_windows
 WHERE chart_id = %s AND generation = %s
   AND (((window_end at time zone 'Asia/Kolkata')::date) < %s::date
        OR ((window_start at time zone 'Asia/Kolkata')::date) >= %s::date)"""
SQL_DUMP = """SELECT event_class,
       (window_start at time zone 'Asia/Kolkata')::date AS ws,
       (window_end   at time zone 'Asia/Kolkata')::date AS we,
       (peak_date    at time zone 'Asia/Kolkata')::date AS pk,
       raw_intensity AS si, valence, is_adverse AS adv, resolution, temporal_shape
  FROM kala_gochara_windows
 WHERE chart_id = %s AND generation = %s
 ORDER BY event_class, ws, we, pk, si, valence, adv, resolution, temporal_shape"""


SQL_SIGN_CHECK = """SELECT COUNT(*) FILTER (WHERE abs(signed_intensity) <> raw_intensity) AS sign_mismatch,
       COUNT(*) FILTER (WHERE raw_intensity < 0) AS negative_raw
  FROM kala_gochara_windows WHERE chart_id = %s AND generation = %s"""
SQL_MANIFEST_ORB = """SELECT status, input_generation_vector->'orb_max_deg', input_generation_vector->'orb_ruling',
       input_generation_vector->'ephemeris'
  FROM kala_gochara_publication WHERE chart_id = %s AND generation = %s"""


SQL_COVERAGE_SUMMARY = """SELECT partition_kind, COUNT(*) AS partitions,
       COUNT(*) FILTER (WHERE requested_horizon = completed_horizon) AS full_horizon,
       COUNT(*) FILTER (WHERE unsearched_reason IS NOT NULL) AS unsearched,
       COALESCE(SUM(targets_requested), 0), COALESCE(SUM(targets_resolved), 0), COALESCE(SUM(targets_unresolved), 0),
       ARRAY_AGG(DISTINCT split_part(partition_key, ':', 1) ORDER BY split_part(partition_key, ':', 1)) AS bodies
  FROM kala_gochara_coverage WHERE chart_id = %s AND generation = %s GROUP BY partition_kind ORDER BY partition_kind"""


def _cell(v):
    if isinstance(v, (dt.date, dt.datetime)):
        return v.isoformat()
    if isinstance(v, decimal.Decimal):
        return float(v)
    return v


def header(generation: str, pinned_at: str, row_count: int) -> dict:
    return {"artifact": f"baseline_{generation.replace('.', '_')}_extract", "version": "1.0", "pinned_at": pinned_at,
            "predicate": f"kala_gochara_windows where chart_id='{CHART_ID}' and generation='{generation}'",
            "tz_convention": TZ_CONVENTION, "row_count": row_count, "columns": COLUMNS}


def dump_rows(conn, generation: str, horizon_check: bool) -> list[dict]:
    """READ ONLY transaction; returns the rows as dicts keyed by COLUMNS. `horizon_check`: assert nothing outside the scored horizon."""
    conn.read_only = True
    with conn.cursor() as cur:
        # si := raw_intensity (the unsigned magnitude; protocol §4.5: si is stored non-negative for every class). The 4.x writer
        # stores signed_intensity = raw * (-1 if adverse else 1), which the §4.5 adapter would reject; the two columns must agree
        # in magnitude on every row, and no raw may be negative.
        cur.execute(SQL_SIGN_CHECK, (CHART_ID, generation))
        mismatch, negative = cur.fetchone()
        if mismatch or negative:
            raise RuntimeError(f"INPUT_REJECTED: {mismatch} rows with |signed_intensity| != raw_intensity, "
                               f"{negative} rows with raw_intensity < 0 (generation {generation})")
        if horizon_check:
            cur.execute(SQL_HORIZON, (CHART_ID, generation, H_START, H_END_EXCL))
            outside = cur.fetchone()[0]
            if outside != 0:
                raise RuntimeError(f"INPUT_REJECTED: {outside} windows of generation {generation} fall outside the scored horizon")
        cur.execute(SQL_DUMP, (CHART_ID, generation))
        return [dict(zip(COLUMNS, (_cell(c) for c in r))) for r in cur.fetchall()]


def rows_multiset_equal(a: list[dict], b: list[dict]) -> bool:
    key = lambda r: json.dumps(r, sort_keys=True)          # noqa: E731
    return sorted(map(key, a)) == sorted(map(key, b))


def render(generation: str, pinned_at: str, rows: list[dict]) -> bytes:
    """Byte layout of the pinned '3.0' extract: indent=1, header key order, no trailing newline."""
    return json.dumps({**header(generation, pinned_at, len(rows)), "rows": rows}, indent=1).encode()


# The AM-16 `ephemeris` component (amendments draft AM-16, schema ka_gochara_input_vector/2) — the ONE definition both the '4.1' and the
# '5.0' manifests must carry: which Swiss ephemeris files the kernel actually opened (sha256 each), the library version AND the loaded
# artifact's sha256, the platform, and a fixed series-probe digest. Absence of any key = not an identity.
EPHEMERIS_KEYS = ("backend", "swe_version", "library_sha256", "platform", "files", "probe_digest")
_SHA64 = re.compile(r"^[0-9a-f]{64}$")
_SE1 = re.compile(r"^se[a-z]+_[0-9]{2}\.se1$")


def ephemeris_component_problems(c) -> list[str]:
    """Why this manifest ephemeris component does NOT identify the ephemeris that was used ([] = it does)."""
    if not isinstance(c, dict):
        return ["no `ephemeris` component in the manifest input vector (the vector predates AM-16)"]
    probs = [f"ephemeris component lacks key {k!r}" for k in EPHEMERIS_KEYS if k not in c]
    extra = sorted(set(c) - set(EPHEMERIS_KEYS))
    if extra:
        probs.append(f"ephemeris component has keys outside the AM-16 definition: {extra}")
    if c.get("backend") != "swieph":
        probs.append(f"backend is {c.get('backend')!r}, not 'swieph' (a Moshier/analytic fallback is not an identified ephemeris)")
    if not c.get("swe_version"):
        probs.append("swe_version is empty")
    for k in ("library_sha256", "probe_digest"):
        if k in c and not _SHA64.match(str(c[k])):
            probs.append(f"{k} is not a sha256")
    if "platform" in c and not c["platform"]:
        probs.append("platform is empty")
    files = c.get("files")
    if "files" in c:
        if not isinstance(files, dict) or not files:
            probs.append("files is empty — no opened .se1 file is recorded (a Moshier-served build opens none)")
        else:
            for name, sha in files.items():
                if not _SE1.match(str(name)):
                    probs.append(f"files: {name!r} is not a Swiss ephemeris .se1 file name")
                if not _SHA64.match(str(sha)):
                    probs.append(f"files: {name!r} has no sha256")
    return probs


def read_manifest_orb(conn, generation: str) -> dict:
    """The activity orb AND the ephemeris identity the candidate chain DECLARES in its manifest (kala_gochara_publication.input_generation_vector keys
    `orb_max_deg`, `orb_ruling`, `ephemeris`; the ephemeris is checked against the AM-16 component definition). Read-only; touches no window row. Recorded in the Stage-1 freeze at freeze time."""
    conn.read_only = True
    with conn.cursor() as cur:
        cur.execute(SQL_MANIFEST_ORB, (CHART_ID, generation))
        rows = cur.fetchall()
    if len(rows) != 1:
        raise RuntimeError(f"expected exactly one manifest for generation {generation}, found {len(rows)}")
    status, deg, ruling, eph = rows[0]
    return {"generation": generation, "manifest_status": status, "orb_max_deg": deg, "orb_ruling": ruling,
            "ephemeris": eph, "ephemeris_problems": ephemeris_component_problems(eph)}


def _connect(args, conn_factory):
    if conn_factory is None:
        dsn = "" if args.libpq_env else os.environ.get(DSN_ENV)
        if dsn is None or (not dsn and not args.libpq_env):
            print(f"REFUSED: {DSN_ENV} is not set (read-only DSN; or pass --libpq-env)", file=sys.stderr)
            return None
        import psycopg

        def conn_factory():
            return psycopg.connect(dsn)
    return conn_factory()


def read_coverage_summary(conn, generation: str) -> dict:
    """What the candidate's coverage ledger rows actually say — DISCLOSURE ONLY. Read-only; touches no window row. The protocol's
    T-honesty coverage is per (class, year) cell (§6.5); the 4.1 chain writes per body-target partitions, so this summary is never
    supplied to the scorer as a coverage manifest."""
    conn.read_only = True
    with conn.cursor() as cur:
        cur.execute(SQL_COVERAGE_SUMMARY, (CHART_ID, generation))
        rows = cur.fetchall()
    kinds = {r[0]: {"partitions": r[1], "full_horizon": r[2], "unsearched": r[3], "targets_requested": int(r[4]),
                    "targets_resolved": int(r[5]), "targets_unresolved": int(r[6]), "first_key_segment": list(r[7])}
             for r in rows}
    return {"generation": generation, "partition_kinds": kinds,
            "event_class_partitions": kinds.get("event_class", {}).get("partitions", 0),
            "per_class_year_cells_derivable": False,
            "note": "per-(class, year) computation coverage (protocol §6.5c) cannot be derived from body_target partitions"}


def main(argv: list[str] | None = None, conn_factory=None) -> int:
    ap = argparse.ArgumentParser(prog="dump_extract")
    ap.add_argument("--generation", required=True)
    ap.add_argument("--stage1", help="committed Stage-1 freeze file (required for a candidate generation)")
    ap.add_argument("--inputs-root", help="campaign measurement directory the freeze's input paths are relative to "
                                          "(default: the Stage-1 file's own directory)")
    ap.add_argument("--pinned-at", help="declared pin date (a frozen argument, not the clock)")
    ap.add_argument("--out")
    ap.add_argument("--libpq-env", action="store_true",
                    help="connect with the libpq PG* environment variables instead of GOCHARA_EVAL_READONLY_DSN")
    ap.add_argument("--read-manifest-orb", action="store_true",
                    help="print the orb the candidate manifest declares (orb_max_deg, orb_ruling) and exit; reads no window row")
    ap.add_argument("--read-coverage-summary", action="store_true",
                    help="print the candidate's coverage-ledger summary (disclosure only; reads no window row) and exit")
    ap.add_argument("--requalify-3-0", metavar="PINNED_SHA256",
                    help="re-dump the '3.0' BASELINE (no freeze) and compare to this pinned sha256")
    ap.add_argument("--compare-to", help="with --requalify-3-0: the pinned extract file; its ROW MULTISET is compared as well "
                                         "(the pinned file's row order within (event_class, ws) ties was database-defined)")
    args = ap.parse_args(argv)

    if args.read_manifest_orb or args.read_coverage_summary:
        if args.generation not in CANDIDATE_GENERATIONS:
            print(f"REFUSED: no manifest/coverage read for generation {args.generation!r}", file=sys.stderr)
            return 2
        conn = _connect(args, conn_factory)
        if conn is None:
            return 2
        try:
            if args.read_manifest_orb:
                print(json.dumps(read_manifest_orb(conn, args.generation)))
            if args.read_coverage_summary:
                print(json.dumps(read_coverage_summary(conn, args.generation)))
        finally:
            conn.rollback()
            conn.close()
        return 0
    if not args.pinned_at or not args.out:
        print("REFUSED: --pinned-at and --out are required", file=sys.stderr)
        return 2

    if args.requalify_3_0:
        if args.generation not in BASELINE_GENERATIONS:
            print(f"REFUSED: --requalify-3-0 re-dumps only {BASELINE_GENERATIONS}", file=sys.stderr)
            return 2
        horizon_check = False
    else:
        if args.generation not in CANDIDATE_GENERATIONS:
            print(f"REFUSED: no extract path for generation {args.generation!r} (candidate generations: "
                  f"{CANDIDATE_GENERATIONS}; governed '5.x' needs the eval-window reader first)", file=sys.stderr)
            return 2
        if not args.stage1:
            print("REFUSED: a candidate extract needs --stage1 (the committed Stage-1 freeze)", file=sys.stderr)
            return 2
        root = args.inputs_root or str(Path(args.stage1).resolve().parent)
        try:
            require_stage1(args.stage1, root, CANONICAL_COMMAND)
        except FreezeRefused as exc:
            print(str(exc), file=sys.stderr)
            return 2
        horizon_check = True

    conn = _connect(args, conn_factory)
    if conn is None:
        return 2
    try:
        rows = dump_rows(conn, args.generation, horizon_check)
    finally:
        conn.rollback()
        conn.close()
    blob = render(args.generation, args.pinned_at, rows)
    Path(args.out).write_bytes(blob)
    sha = hashlib.sha256(blob).hexdigest()
    print(f"rows={len(rows)} sha256={sha} out={args.out}")
    if args.requalify_3_0:
        byte_ok = sha == args.requalify_3_0
        print("REQUALIFY bytes: " + ("IDENTICAL to the pin" if byte_ok else "DIFFER from the pin"))
        if args.compare_to:
            same = rows_multiset_equal(rows, json.loads(Path(args.compare_to).read_bytes())["rows"])
            print("REQUALIFY rows: " + ("the SAME row multiset as the pinned file" + ("" if byte_ok else " (order differs only)")
                                        if same else "DIFFER from the pinned file's rows"))
            return 0 if same else 1
        return 0 if byte_ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
