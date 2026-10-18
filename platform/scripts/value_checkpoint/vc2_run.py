#!/usr/bin/env python3
"""VC-2 runner: read one candidate generation from the LANE database, render the three arms, write them.

Read-only against a loopback disposable database (127.0.0.1:55433); never production, never a scorer.
`real` mode refuses until the freeze binding of prereg §2 exists; `rehearsal` mode proves the machinery on
whatever lane data it is given and never writes under the committed outputs directory.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
import vc2_core as core  # noqa: E402

LANE_HOST, LANE_PORT = "127.0.0.1", 55433
CANON_AYANAMSHA = "lahiri_chitrapaksha"
MAHADASHA = ("vimshottari", 1)  # chart_dashas system_id, level_n (dasha_read.py: 1 MD)
OUTPUTS_DIR = core.REPO / core.OUTPUTS_REL


class Refused(RuntimeError):
    pass


def assert_lane_dsn(dsn: str) -> str:
    """Only the loopback lane cluster. Cheap string check before any connection is attempted."""
    for var in ("PGHOST", "PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE"):
        if os.environ.get(var, "").strip():
            raise Refused(f"{var} is set; the DSN alone would not decide the target")
    parsed = urlparse(dsn)
    if parsed.scheme not in ("postgresql", "postgres") or "," in parsed.netloc or parsed.query:
        raise Refused("DSN must be a single-host URI without a query string")
    if parsed.hostname != LANE_HOST or parsed.port != LANE_PORT:
        raise Refused(f"DSN must target the lane cluster {LANE_HOST}:{LANE_PORT}")
    name = parsed.path.lstrip("/")
    if not (name.startswith("ky_") or name.startswith("kala_ci_")):
        raise Refused("lane database names start with ky_ or kala_ci_")
    return name


def _iso(value) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _json_rows(rows) -> str:
    return core.sha256_hex(core.canonical_json([list(map(_plain, r)) for r in rows]).encode())


def _plain(value):
    if isinstance(value, datetime):
        return _iso(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "__float__") and not isinstance(value, (int, float, bool)):
        return float(value)
    return value


def load_snapshot(conn, chart_id: str, generation: str, eligibility: dict) -> dict:
    """One read-only, chart- and generation-scoped snapshot shared by all three arms."""
    conn.execute("SET TRANSACTION READ ONLY")

    def q(sql, params):
        return conn.execute(sql, params).fetchall()

    pins = {}
    snap = q("SELECT DISTINCT config_pin->>'birth_utc' FROM kala_field_snapshots_candidate "
             "WHERE chart_id=%s AND generation=%s", (chart_id, generation))
    births = sorted(r[0] for r in snap if r[0])
    if len(births) != 1:
        raise Refused("exactly one pinned UTC birth axis required in the field snapshot")
    birth = datetime.fromisoformat(births[0]).astimezone(timezone.utc)
    pins["birth_axis"] = core.sha256_hex(births[0].encode())

    def at(days):
        return _iso(birth + timedelta(days=float(days)))

    chapter_rows = q("SELECT dasha_row_id::text, lord_graha, start_date, end_date FROM chart_dashas "
                     "WHERE chart_id=%s AND system_id=%s AND level_n=%s AND ayanamsha_id=%s "
                     "ORDER BY start_iso, dasha_row_id", (chart_id, MAHADASHA[0], MAHADASHA[1], CANON_AYANAMSHA))
    pins["chart_dashas"] = _json_rows(chapter_rows)
    chapters = [{"ref": r[0], "lord": r[1], "start": r[2].isoformat(), "end": r[3].isoformat()} for r in chapter_rows]

    event_rows = q("SELECT event_id, event_date FROM life_events WHERE chart_id=%s ORDER BY event_id", (chart_id,))
    pins["life_event_ids_dates"] = _json_rows(event_rows)
    events = [{"event_id": r[0], "date": r[1].isoformat()} for r in event_rows]

    sources = {}

    def slot(event_class):
        return sources.setdefault(event_class, {"sangam": None, "taranga": None, "segments": None})

    jury = q("SELECT event_class, assertion_id, window_start, window_end, conditional_effect, "
             "conditional_null->>'verdict', witness_signature FROM kala_jury_candidate "
             "WHERE chart_id=%s AND generation=%s ORDER BY event_class, window_start, assertion_id",
             (chart_id, generation))
    pins["kala_jury_candidate"] = _json_rows(jury)
    for cls, aid, ws, we, effect, verdict, witnesses in jury:
        slot(cls)["sangam"] = (slot(cls)["sangam"] or []) + [
            {"window": aid, "start": _iso(ws), "end": _iso(we), "effect": effect, "null_verdict": verdict,
             "witnesses": list(witnesses)}]

    taranga = q("SELECT scope_id, month, integral FROM kala_taranga_candidate "
                "WHERE chart_id=%s AND generation=%s AND scope_kind='event_class' ORDER BY scope_id, month",
                (chart_id, generation))
    pins["kala_taranga_candidate"] = _json_rows(taranga)
    for cls, month, integral in taranga:
        slot(cls)["taranga"] = (slot(cls)["taranga"] or []) + [{"month": month.isoformat(), "integral": integral}]

    windows = q("SELECT event_class, t_start, t_end, weakest_link, baseline_is_synthetic "
                "FROM kala_field_windows_candidate WHERE chart_id=%s AND generation=%s "
                "ORDER BY event_class, t_start, t_end", (chart_id, generation))
    pins["kala_field_windows_candidate"] = _json_rows(windows)
    synthetic_priors = {w[0] for w in windows if w[4]}
    by_class_windows = {}
    for cls, t0, t1, weakest, _ in windows:
        by_class_windows.setdefault(cls, []).append((t0, t1, weakest))

    field = q("SELECT event_class, segment_index, t_start, t_end, alpha, gamma, integral_days, promise_term, "
              "clock_term_start, modifier_term_start, suppression_term_start FROM kala_field_candidate "
              "WHERE chart_id=%s AND generation=%s ORDER BY event_class, segment_index", (chart_id, generation))
    pins["kala_field_candidate"] = _json_rows(field)
    for cls, idx, t0, t1, alpha, gamma, integral, promise, clock, modifier, suppression in field:
        weakest = "no_window"
        for w0, w1, link in by_class_windows.get(cls, []):
            if w0 <= t0 <= w1:
                weakest = link if link is not None else "null"
                break
        slot(cls)["segments"] = (slot(cls)["segments"] or []) + [
            {"index": idx, "start": at(t0), "end": at(t1), "alpha": alpha, "gamma": gamma, "integral_days": integral,
             "promise": promise, "clock": clock, "modifier": modifier, "suppression": suppression,
             "weakest_link": weakest}]
    return {"chart_id": chart_id, "generation": generation, "chapters": chapters, "events": events,
            "lel_coverage": eligibility["lel_coverage"], "sources": sources, "pins": pins,
            "synthetic": eligibility.get("synthetic") is not False,
            "evaluation_eligible": eligibility.get("evaluation_eligible") is True,
            "synthetic_prior_classes": sorted(synthetic_priors)}


def resolve_classes(eligibility: dict, snapshot: dict) -> list:
    """Declared classes, with the stored baseline_is_synthetic flag overriding any declaration of calibration."""
    out = []
    for c in eligibility["classes"]:
        out.append({"event_class": c["event_class"], "prior_provenance": c.get("prior_provenance"),
                    "calibrated": bool(c.get("calibrated")),
                    "synthetic_prior": bool(c.get("synthetic_prior")) or c["event_class"] in snapshot["synthetic_prior_classes"]})
    return out


def produce(loader, eligibility: dict, mode: str, *, binding: dict = None) -> dict:
    """Two independent loads and renders; returns files only if they are byte-identical (prereg §2 step 4)."""
    pins = core.protocol_pins()
    first = _generate_once(loader, eligibility, pins, mode, binding)
    second = _generate_once(loader, eligibility, pins, mode, binding)
    if first != second:
        raise Refused("second run is not byte-identical; nothing written")
    first["REPRO_DIGEST.json"] = core.pretty_json(core.repro_digest(first)).encode("utf-8")
    return first


def _generate_once(loader, eligibility, pins, mode, binding):
    snapshot = loader()
    return core.generate(snapshot, resolve_classes(eligibility, snapshot), pins, mode, binding)


def write_files(files: dict, dest: Path, mode: str) -> None:
    dest = Path(dest).resolve()
    inside = dest == OUTPUTS_DIR or OUTPUTS_DIR in dest.parents
    if mode == "rehearsal" and inside:
        raise Refused("rehearsal output may never be written under the committed outputs directory")
    if mode == "real" and dest != OUTPUTS_DIR:
        raise Refused("real output is committed only under the value-checkpoint outputs directory")
    if dest.exists() and any(p.is_file() and p.name != "README.md" for p in dest.rglob("*")):
        raise Refused("destination already holds outputs")
    for rel, data in files.items():
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=("real", "rehearsal"), required=True)
    ap.add_argument("--dsn", required=True)
    ap.add_argument("--chart", required=True)
    ap.add_argument("--generation", required=True)
    ap.add_argument("--eligibility", required=True, help="JSON: consent/eligibility/coverage/six classes")
    ap.add_argument("--receipt", default="/Users/Dev/kalayantra/run/G1_BASELINE.json")
    ap.add_argument("--binding", default="/Users/Dev/kalayantra/run/VC_BINDING.json")
    ap.add_argument("--dest", required=True)
    args = ap.parse_args(argv)
    try:
        assert_lane_dsn(args.dsn)
        eligibility = json.loads(Path(args.eligibility).read_text())
        binding = None
        if args.mode == "real":
            reasons = core.check_readiness(receipt_path=Path(args.receipt), binding_path=Path(args.binding),
                                           eligibility=eligibility, outputs_dir=OUTPUTS_DIR)
            if reasons:
                print(json.dumps({"status": "refused", "reasons": reasons}, indent=2))
                return 2
            binding = json.loads(Path(args.binding).read_text())
        import psycopg

        def loader():
            with psycopg.connect(args.dsn, connect_timeout=5) as conn:
                return load_snapshot(conn, args.chart, args.generation, eligibility)

        files = produce(loader, eligibility, args.mode, binding=binding)
        write_files(files, Path(args.dest), args.mode)
    except Refused as exc:
        print(json.dumps({"status": "refused", "reasons": [str(exc)]}, indent=2))
        return 2
    print(json.dumps({"status": "written", "files": len(files),
                      "digest": json.loads(files["REPRO_DIGEST.json"])["digest"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
