"""Rule Book engine — command line: build the UNIT_MANIFEST, scan a chart over a date range.

  python -m services.rulebook.engine.cli build-manifest --final-cards F --attested A --yardstick Y --out-dir D
  python -m services.rulebook.engine.cli scan --manifest M --bundle B --first YYYY-MM-DD --last YYYY-MM-DD --out FILE
        (--chart-id UUID | --fixture FILE)  [--sky-fixture FILE --sunrise-fixture FILE]
        [--birth-record FILE [--tzdb-pin VERSION]]
  python -m services.rulebook.engine.cli resolve-births --records FILE --out FILE [--tzdb-pin VERSION]

``--birth-record`` is the explicit-UT-offset path for births outside India (SUR-RB-6): one JSON record
with ``utc_offset_minutes`` taken from the source record. Missing or malformed -> refused; a tz-database
disagreement or a failed birth-instant tripwire -> excluded. Both exit with status 3 and a reason code;
neither ever falls back to IST. ``resolve-births`` resolves a whole list and reports the exclusion counts.

``scan --chart-id`` reads the stored operands over a READ-ONLY connection (proxy :5433;
password from PGPASSWORD or the first line of ~/.pgpass, never printed). Private inputs
(card files, attested rules, bundle) are named by path and are never copied into git.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import constants as RC
from . import constants as K
from .units import build_bundle, build_units, canonical_bytes, sha256_file

PKG_ROOT = Path(__file__).resolve().parents[3]  # .../python-sidecar
SOURCE_TREE = (
    sorted(
        str(p.relative_to(PKG_ROOT))
        for d in ("services/rulebook", "services/rulebook/engine")
        for p in (PKG_ROOT / d).glob("*.py")
    )
    + sorted(str(p.relative_to(PKG_ROOT)) for p in (PKG_ROOT / "services/rulebook/data").glob("*.json"))
    + ["panchang_engine/timings.py"]
)


def build_manifest(final_cards_path: Path, attested_path: Path, yardstick_path: Path, out_dir: Path) -> Dict[str, Any]:
    final = json.loads(Path(final_cards_path).read_text(encoding="utf-8"))
    attested = json.loads(Path(attested_path).read_text(encoding="utf-8"))
    units, recs, counts = build_units(final, attested)
    bundle = build_bundle(attested, recs)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_bytes = canonical_bytes(bundle)
    import hashlib

    bundle_sha = hashlib.sha256(bundle_bytes).hexdigest()
    (out_dir / "RULE_BUNDLE_v1_0.json").write_bytes(bundle_bytes)
    manifest = {
        "manifest_schema": K.MANIFEST_SCHEMA,
        "unit_manifest_version": "1.0",
        "binds": {
            "yardstick_file": Path(yardstick_path).name,
            "yardstick_sha256": sha256_file(yardstick_path),
            "rulebook_cards_sha256": sha256_file(final_cards_path),
            "rulebook_rules": len(recs),
            "attested_rules_sha256": sha256_file(attested_path),
        },
        "bundle_sha256": bundle_sha,
        "versions": {
            "engine": K.ENGINE_VERSION,
            "ast": RC.AST_VERSION,
            "compiler": RC.COMPILER_VERSION,
            "graha_class_table": RC.GRAHA_CLASS_TABLE_VERSION,
            "bhava_groups": RC.BHAVA_GROUPS_VERSION,
            "day_convention": K.DAY_CONVENTION_ID,
        },
        "conventions": {
            "ayanamsha_l1": K.AYANAMSHA_L1,
            "ayanamsha_l0": K.AYANAMSHA_L0,
            "house_system": K.HOUSE_SYSTEM,
            "node_model_natal_l1": K.NODE_MODEL_NATAL_L1,
            "node_model_transit_l0": K.NODE_MODEL_TRANSIT_L0,
            "node_policy_id": K.NODE_POLICY_ID,
            "node_policy": K.NODE_POLICY,
            "ashtakavarga_count": K.ASHTAKAVARGA_COUNT_CONVENTION,
            "dasha_system": K.DASHA_SYSTEM,
            "zone_policy": "IST zone path: IST zones only (" + ", ".join(sorted(K.IST_ZONES)) + "); anything else raises (DF-04)",
            "foreign_birth_path": (
                "explicit UT offset from the source record only (utc_offset_minutes); missing or malformed -> chart refused, "
                "never defaulted; cross-checked against the pinned tz database (disagreement -> excluded and counted); "
                "true UT = local time minus the stated offset; birth-instant tripwires on the stored L1 facts "
                "(sky signs, Vimshottari start) -> excluded"
            ),
            "day_mapping_foreign": "civil date D -> sunrise day starting at sunrise on D; sunrise in UT from latitude/longitude, civil date = local solar date (UT + lon/15 h), no tz database",
            "p4_double_transit": "off",
            "exceptions": "not evaluated in v1 (no active card has one)",
            "frames_py": "not used (services/gochara_rules is never imported)",
            "transit_source": "bg_sky_calendar ingress rows, Lahiri, TRUE node at L0 (nodes never read)",
            "sunrise": "panchang_engine.timings.compute_sunrise_sunset (upper limb, refraction)",
            "tzdb_at_build": __import__("services.rulebook.engine.dayatom", fromlist=["tzdb_version"]).tzdb_version(),
        },
        "source_tree_sha256": {p: sha256_file(PKG_ROOT / p) for p in SOURCE_TREE},
        "counts": counts,
        "units": units,
    }
    mbytes = canonical_bytes(manifest)
    (out_dir / "UNIT_MANIFEST_v1_0.json").write_bytes(mbytes)
    msha = hashlib.sha256(mbytes).hexdigest()
    (out_dir / "UNIT_MANIFEST_v1_0.sha256").write_text(f"{msha}  UNIT_MANIFEST_v1_0.json\n")
    return {"manifest_sha256": msha, "bundle_sha256": bundle_sha, "counts": counts}


def _cmd_build(a: argparse.Namespace) -> int:
    res = build_manifest(Path(a.final_cards), Path(a.attested), Path(a.yardstick), Path(a.out_dir))
    print(json.dumps(res, indent=1, sort_keys=True))
    return 0


def _cmd_scan(a: argparse.Namespace) -> int:
    from . import dbload
    from .chart import chart_from_fixture
    from .dayatom import PanchangEngineSunrise, SolarSunrise, TableSunrise
    from .driver import scan, write_states
    from .sky import sky_from_fixture

    from .birthrecord import BirthRecordError, parse_birth_record, resolve_birth

    resolved = None
    if a.birth_record:
        try:
            resolved = resolve_birth(
                parse_birth_record(json.loads(Path(a.birth_record).read_text(encoding="utf-8"))), expected_tzdb=a.tzdb_pin
            )
        except BirthRecordError as exc:
            print(json.dumps({"chart": "not_evaluated", "kind": type(exc).__name__, "reason": exc.code, "detail": exc.detail}, sort_keys=True))
            return 3
    manifest_path, bundle_path = Path(a.manifest), Path(a.bundle)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    first, last = date.fromisoformat(a.first), date.fromisoformat(a.last)
    if a.fixture:
        chart = chart_from_fixture(json.loads(Path(a.fixture).read_text(encoding="utf-8")))
        if resolved is not None:
            chart.birth = resolved.birth()
        sky = sky_from_fixture(json.loads(Path(a.sky_fixture).read_text(encoding="utf-8")))
    else:
        conn = dbload.connect_readonly(host=a.db_host, port=a.db_port, dbname=a.db_name, user=a.db_user)
        try:
            chart = dbload.load_chart(conn, a.chart_id, resolved)
            sky = dbload.load_sky(conn)
        except BirthRecordError as exc:
            print(json.dumps({"chart": "not_evaluated", "kind": type(exc).__name__, "reason": exc.code, "detail": exc.detail}, sort_keys=True))
            return 3
        finally:
            conn.close()
    if a.sunrise_fixture:
        provider = TableSunrise(json.loads(Path(a.sunrise_fixture).read_text(encoding="utf-8")))
    elif resolved is not None:
        provider = SolarSunrise(chart.birth.lat, chart.birth.lon)
    else:
        provider = PanchangEngineSunrise(chart.birth.lat, chart.birth.lon)
    try:
        doc = _do_scan(scan, chart, sky, provider, first, last, bundle, manifest, manifest_path, bundle_path, a)
    except BirthRecordError as exc:  # birth-instant tripwire (L1_UT_MISMATCH) or inconsistent instant
        print(json.dumps({"chart": "not_evaluated", "kind": type(exc).__name__, "reason": exc.code, "detail": exc.detail}, sort_keys=True))
        return 3
    sha = write_states(doc, a.out)
    Path(a.out).chmod(0o600)
    print(json.dumps({"states_file_sha256": sha, "members": len(doc["members"]), "days": doc["range"]["days"]}, sort_keys=True))
    return 0


def _do_scan(scan, chart, sky, provider, first, last, bundle, manifest, manifest_path, bundle_path, a):
    return scan(
        chart,
        sky,
        provider,
        first,
        last,
        bundle,
        manifest,
        manifest_sha256=sha256_file(manifest_path),
        bundle_sha256=sha256_file(bundle_path),
        include_sunrise=a.include_sunrise,
    )


def _cmd_resolve(a: argparse.Namespace) -> int:
    from .birthrecord import resolve_many

    records = json.loads(Path(a.records).read_text(encoding="utf-8"))
    resolved, tally, codes = resolve_many(records, expected_tzdb=a.tzdb_pin)
    out = {
        "tally": tally.to_json(),
        "records": [
            {"index": i, "status": "resolved", "utc": r.utc.isoformat(), "zone_checked": r.zone_checked, "tzdb": r.tzdb}
            if r is not None
            else {"index": i, "status": "not_evaluated", "reason": codes[i]}
            for i, r in enumerate(resolved)
        ],
    }
    Path(a.out).write_bytes(canonical_bytes(out))
    Path(a.out).chmod(0o600)
    print(json.dumps(tally.to_json(), sort_keys=True))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="rulebook-engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build-manifest")
    b.add_argument("--final-cards", required=True)
    b.add_argument("--attested", required=True)
    b.add_argument("--yardstick", required=True)
    b.add_argument("--out-dir", required=True)
    b.set_defaults(fn=_cmd_build)
    s = sub.add_parser("scan")
    s.add_argument("--manifest", required=True)
    s.add_argument("--bundle", required=True)
    s.add_argument("--first", required=True)
    s.add_argument("--last", required=True)
    s.add_argument("--out", required=True)
    g = s.add_mutually_exclusive_group(required=True)
    g.add_argument("--chart-id")
    g.add_argument("--fixture")
    s.add_argument("--sky-fixture")
    s.add_argument("--sunrise-fixture")
    s.add_argument("--include-sunrise", action="store_true")
    s.add_argument("--birth-record", help="explicit-UT-offset birth record (foreign births)")
    s.add_argument("--tzdb-pin", help="refuse unless the tz database version equals this string")
    s.add_argument("--db-host", default="127.0.0.1")
    s.add_argument("--db-port", type=int, default=5433)  # the read-only proxy
    s.add_argument("--db-name", default="amjis")
    s.add_argument("--db-user", default="amjis_app")
    s.set_defaults(fn=_cmd_scan)
    r = sub.add_parser("resolve-births")
    r.add_argument("--records", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--tzdb-pin")
    r.set_defaults(fn=_cmd_resolve)
    a = ap.parse_args(argv)
    if a.cmd == "scan" and a.fixture and not a.sky_fixture:
        ap.error("--fixture needs --sky-fixture")
    return int(a.fn(a))


if __name__ == "__main__":
    sys.exit(main())
