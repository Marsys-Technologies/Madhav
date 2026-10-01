"""B6.0 PART 0 — disposable-DB rehearsal of resonance_restore_from_file.py
(steward M20261001T125637-9b2b: "Rehearse on the disposable PG with the
migration-derived schema: success reproduces the certificate; refusals for
tampered file, truncated file, wrong chart line, digest mismatch, sha
mismatch — each a control").

NEVER production. The disposable identity follows
resonance_rebuild_disposable_rehearsal.py exactly: the operator names the
destination CLUSTER by `--expect-cluster-id` (must equal
`SELECT system_identifier FROM pg_control_system()`), and this run CREATES
the database it uses (`<prefix>_<utc-stamp>_<hex>`), verifies it empty of
user tables, and DROPS it at the end (--keep-database retains it).

What it proves, on the MIGRATION-DERIVED schema (bg_transit_rules +
gochara_resonance_map DDL scanned from the checked-in migrations, never
hand-copied):

  setup    a canonical-chart partition (25 rows, ids explicit, NULLs and
           typed values exercised) + a foreign chart's partition; the
           certified file backup taken exactly as the steward took the
           production one (row_to_json lines ordered by id + sha256
           sidecar); then a simulated "rebuild" drifts the live partition
  control 1  SUCCESS: the restore reproduces the recorded certificate
           (count + full-row md5) and the foreign partition's certificate
           is byte-identical before/after
  control 2  TAMPERED file (one byte changed, sidecar honest) → REFUSED
           (sha256), live partition untouched
  control 3  TRUNCATED file (last rows dropped, sidecar re-taken for the
           truncated file) → REFUSED (count), live untouched
  control 4  WRONG-CHART line (one row's chart_id changed; sidecar and
           expectations re-taken so ONLY the chart check can fire) →
           REFUSED (foreign row), live untouched
  control 5  DIGEST mismatch (correct file, wrong recorded md5) →
           REFUSED, live untouched
  control 6  SHA mismatch (corrupt sidecar) → REFUSED, live untouched
  control 7  the steward's REAL certified backup
           (/Users/Dev/pravaha/run/backups/gochara_resonance_map_
           482012f1_20261001071822.jsonl) verifies against the recorded
           pair (765, 3d270ef0a2db00b240a2acb4d45171c0) — read-only,
           never restored anywhere

Exit 0 when every control behaves; exit 1 with the failures listed.

Usage:
  python3 resonance_restore_from_file_rehearsal.py \
      --maintenance-dsn postgresql://postgres@127.0.0.1:59541/postgres \
      --expect-cluster-id <system_identifier of the DISPOSABLE cluster> \
      [--database-prefix rehearsal_b6_restore] [--keep-database] [--json-out PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import resonance_rebuild_disposable_rehearsal as R  # noqa: E402
import resonance_restore_from_file as RESTORE  # noqa: E402

import psycopg  # noqa: E402

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
FOREIGN = "00000000-0000-4000-8000-0000000000aa"
STEWARD_FILE = Path("/Users/Dev/pravaha/run/backups/gochara_resonance_map_482012f1_20261001071822.jsonl")
STEWARD_PAIR = (765, "3d270ef0a2db00b240a2acb4d45171c0")

VERBATIM_MIGRATIONS = R.VERBATIM_MIGRATIONS          # the ontology + its real 27-class seed
VERBATIM_MAP_MIGRATIONS = R.VERBATIM_MAP_MIGRATIONS  # 459 + 550 + 1080


def apply_map_schema(cur) -> dict:
    """The ontology verbatim (real seed), bg_transit_rules derived from the
    checked-in migrations, the resonance-map migrations verbatim — exactly
    the A5.4 rehearsal's derivation of the same surface."""
    applied: dict = {"verbatim": [], "derived": {}}
    cur.execute(R.STUB_DDL)
    for name in VERBATIM_MIGRATIONS:
        cur.execute(R.find_migration(name).read_text())
        applied["verbatim"].append(name)
    entries = []
    for root in R.MIGRATION_ROOTS:
        for p in sorted(root.glob("*.sql"), key=R._migration_sort_key):
            stmts = R.table_ddl_statements(p.read_text(), "bg_transit_rules")
            if stmts:
                for st in stmts:
                    cur.execute(st)
                entries.append((p.name, len(stmts)))
    applied["derived"]["bg_transit_rules"] = entries
    for name in VERBATIM_MAP_MIGRATIONS:
        cur.execute(R.find_migration(name).read_text())
        applied["verbatim"].append(name)
    return applied


def seed(cur) -> None:
    cur.execute(
        "INSERT INTO bg_transit_rules (id, rule_type, graha, primary_house, phala, classical_citation) "
        "VALUES (1, 'favourable', 'mars', 3, 'p', 'c1'), (2, 'unfavourable', 'saturn', 8, 'p', 'c2') "
        "ON CONFLICT DO NOTHING")
    classes = [r[0] for r in cur.execute(
        "SELECT event_class_id FROM brahma_event_ontology ORDER BY event_class_id LIMIT 5").fetchall()]
    if "marriage" not in classes:
        classes[0] = "marriage"
    rows = []
    for i in range(1, 26):
        rows.append(
            (i, CHART, classes[i % 5], ("bhava", "lord", "sensitive_degree")[i % 3],
             str((i % 12) + 1), round(0.5 + i * 0.1, 4),
             None if i % 4 == 0 else f"citation {i}", i % 4 == 0,
             1 if i % 7 == 0 else None, f"2026-09-07T21:08:{i:02d}.192812+00:00",
             "resolved" if i % 2 else "unavailable", None if i % 3 else "afflicted"))
    for i in range(101, 106):
        rows.append(
            (i, FOREIGN, "marriage", "bhava", str(i - 100), 1.0, "foreign citation", False,
             None, "2026-09-01T00:00:00+00:00", "resolved", None))
    cur.executemany(
        "INSERT INTO gochara_resonance_map (id, chart_id, event_class, target_type, "
        "target_ref, weight, classical_citation, uncited_extension, source_rule_id, "
        "computed_at, target_resolution_state, target_qualifier) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", rows)
    cur.execute("SELECT setval(pg_get_serial_sequence('gochara_resonance_map', 'id'), 200)")


def take_file_backup(cur, directory: Path) -> tuple[Path, int, str]:
    """Exactly the steward's production backup: row_to_json lines ordered by
    id, one per line, plus a coreutils-format sha256 sidecar."""
    cur.execute(
        "SELECT row_to_json(t)::text FROM gochara_resonance_map t\n"
        " WHERE t.chart_id = %s ORDER BY t.id;", (CHART,))
    lines = [r[0] for r in cur.fetchall()]
    path = directory / f"gochara_resonance_map_482012f1_rehearsal.jsonl"
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    path.write_bytes(payload)
    (path.parent / (path.name + ".sha256")).write_text(
        hashlib.sha256(payload).hexdigest() + "  " + path.name + "\n", encoding="utf-8")
    joined = hashlib.md5("\n".join(lines).encode("utf-8")).hexdigest()
    return path, len(lines), joined


def drift_live_partition(cur) -> None:
    """A simulated 'rebuild': the live partition no longer matches the backup."""
    cur.execute("DELETE FROM gochara_resonance_map WHERE chart_id = %s", (CHART,))
    cur.execute(
        "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type, target_ref, "
        "weight, classical_citation, uncited_extension, target_resolution_state) "
        "VALUES (%s, 'marriage', 'bhava', '1', 2.5, 'rebuilt citation', false, 'resolved')",
        (CHART,))


def live_certificate(cur, chart: str) -> tuple[int, str]:
    cur.execute(
        "SELECT COUNT(*), COALESCE(md5(string_agg(row_to_json(t)::text, E'\\n' ORDER BY t.id)), 'empty')\n"
        "  FROM gochara_resonance_map t WHERE t.chart_id = %s;", (chart,))
    row = cur.fetchone()
    return (int(row[0]), row[1])


def expect_refusal(fn, needle: str) -> tuple[bool, str]:
    try:
        fn()
    except RESTORE.Refusal as exc:
        return (needle in str(exc), str(exc))
    return (False, "no refusal raised")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--maintenance-dsn", required=True)
    parser.add_argument("--expect-cluster-id", required=True)
    parser.add_argument("--database-prefix", default="rehearsal_b6_restore")
    parser.add_argument("--keep-database", action="store_true")
    parser.add_argument("--json-out", default=None)
    args = parser.parse_args(argv)

    failures: list[str] = []
    report: dict = {"controls": {}}

    dsn, dbname = R.establish_disposable_database(
        args.maintenance_dsn, args.database_prefix, args.expect_cluster_id)
    report["database"] = dbname
    workdir = Path(tempfile.mkdtemp(prefix="b6-restore-rehearsal-"))

    try:
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=5)
        R.assert_disposable_identity(conn, dbname)
        cur = conn.cursor()
        report["schema"] = apply_map_schema(cur)
        seed(cur)

        backup, count, joined_md5 = take_file_backup(cur, workdir)
        recorded = {"count": count, "md5": joined_md5}
        foreign_before = live_certificate(cur, FOREIGN)
        drift_live_partition(cur)
        drifted = live_certificate(cur, CHART)
        if drifted == (count, joined_md5):
            failures.append("setup: the drift did not change the live certificate")
        report["setup"] = {"backup": str(backup), "recorded": recorded,
                           "foreign_before": foreign_before, "drifted": drifted}

        # ── control 1: SUCCESS reproduces the certificate ──────────────────
        with psycopg.connect(dsn, autocommit=False, connect_timeout=5) as c:
            result = RESTORE.restore(c, CHART,
                                     RESTORE.load_and_verify_file(str(backup), CHART, count, joined_md5),
                                     count, joined_md5, execute=True)
        live_after = live_certificate(cur, CHART)
        foreign_after = live_certificate(cur, FOREIGN)
        ok = (live_after == (count, joined_md5) and foreign_after == foreign_before
              and result["committed"] is True)
        report["controls"]["success"] = {"live_after": live_after, "recorded": recorded,
                                         "foreign_after": foreign_after,
                                         "foreign_before": foreign_before, "ok": ok}
        if not ok:
            failures.append("control 1 (success): restore did not reproduce the recorded certificate "
                            "or the foreign partition changed")

        # ── refusals 2-6: each on the STILL-drifted live state ─────────────
        def drift_again():
            drift_live_partition(cur)
            return live_certificate(cur, CHART)

        # control 2: tampered file (sidecar honest) → sha256 refusal
        pre = drift_again()
        tampered = workdir / "tampered.jsonl"
        raw = bytearray(backup.read_bytes())
        raw[len(raw) // 2] ^= 0x01
        tampered.write_bytes(bytes(raw))
        (workdir / "tampered.jsonl.sha256").write_text(
            (workdir / (backup.name + ".sha256")).read_text(), encoding="utf-8")
        ok, msg = expect_refusal(
            lambda: RESTORE.load_and_verify_file(str(tampered), CHART, count, joined_md5), "sha256")
        untouched = live_certificate(cur, CHART) == pre
        report["controls"]["tampered"] = {"refused": ok, "message": msg, "live_untouched": untouched}
        if not (ok and untouched):
            failures.append(f"control 2 (tampered): refused={ok} untouched={untouched} ({msg})")

        # control 3: truncated file (sidecar re-taken for it) → count refusal
        pre = drift_again()
        lines = backup.read_text(encoding="utf-8").split("\n")
        lines = [l for l in lines if l]
        truncated = workdir / "truncated.jsonl"
        payload = ("\n".join(lines[:-3]) + "\n").encode("utf-8")
        truncated.write_bytes(payload)
        (workdir / "truncated.jsonl.sha256").write_text(
            hashlib.sha256(payload).hexdigest() + "  truncated.jsonl\n", encoding="utf-8")
        ok, msg = expect_refusal(
            lambda: RESTORE.load_and_verify_file(str(truncated), CHART, count, joined_md5), "rows")
        untouched = live_certificate(cur, CHART) == pre
        report["controls"]["truncated"] = {"refused": ok, "message": msg, "live_untouched": untouched}
        if not (ok and untouched):
            failures.append(f"control 3 (truncated): refused={ok} untouched={untouched} ({msg})")

        # control 4: wrong-chart line (sidecar + expectations re-taken so ONLY
        # the chart check can fire) → foreign-row refusal
        pre = drift_again()
        foreign_lines = list(lines)
        row = json.loads(foreign_lines[7])
        row["chart_id"] = FOREIGN
        foreign_lines[7] = json.dumps(row)
        wrongchart = workdir / "wrongchart.jsonl"
        payload = ("\n".join(foreign_lines) + "\n").encode("utf-8")
        wrongchart.write_bytes(payload)
        (workdir / "wrongchart.jsonl.sha256").write_text(
            hashlib.sha256(payload).hexdigest() + "  wrongchart.jsonl\n", encoding="utf-8")
        recomputed = hashlib.md5("\n".join(foreign_lines).encode("utf-8")).hexdigest()
        ok, msg = expect_refusal(
            lambda: RESTORE.load_and_verify_file(str(wrongchart), CHART, len(foreign_lines), recomputed),
            "foreign row")
        untouched = live_certificate(cur, CHART) == pre
        report["controls"]["wrong_chart"] = {"refused": ok, "message": msg, "live_untouched": untouched}
        if not (ok and untouched):
            failures.append(f"control 4 (wrong chart): refused={ok} untouched={untouched} ({msg})")

        # control 5: digest mismatch (correct file, wrong recorded md5)
        pre = drift_again()
        ok, msg = expect_refusal(
            lambda: RESTORE.load_and_verify_file(str(backup), CHART, count, "0" * 32), "joined-md5")
        untouched = live_certificate(cur, CHART) == pre
        report["controls"]["digest_mismatch"] = {"refused": ok, "message": msg, "live_untouched": untouched}
        if not (ok and untouched):
            failures.append(f"control 5 (digest mismatch): refused={ok} untouched={untouched} ({msg})")

        # control 6: sha mismatch (corrupt sidecar)
        pre = drift_again()
        badsha = workdir / "badsha.jsonl"
        badsha.write_bytes(backup.read_bytes())
        (workdir / "badsha.jsonl.sha256").write_text("0" * 64 + "  badsha.jsonl\n", encoding="utf-8")
        ok, msg = expect_refusal(
            lambda: RESTORE.load_and_verify_file(str(badsha), CHART, count, joined_md5), "sha256")
        untouched = live_certificate(cur, CHART) == pre
        report["controls"]["sha_mismatch"] = {"refused": ok, "message": msg, "live_untouched": untouched}
        if not (ok and untouched):
            failures.append(f"control 6 (sha mismatch): refused={ok} untouched={untouched} ({msg})")

        # control 7: the steward's REAL certified backup verifies (read-only)
        if STEWARD_FILE.exists():
            try:
                steward_lines = RESTORE.load_and_verify_file(
                    str(STEWARD_FILE), CHART, STEWARD_PAIR[0], STEWARD_PAIR[1])
                report["controls"]["steward_backup"] = {"verified": True, "rows": len(steward_lines)}
            except RESTORE.Refusal as exc:
                report["controls"]["steward_backup"] = {"verified": False, "message": str(exc)}
                failures.append(f"control 7 (steward backup): {exc}")
        else:
            report["controls"]["steward_backup"] = {"verified": None, "skipped": "file absent"}

        # restore once more so the disposable DB ends in the pre-drift state
        with psycopg.connect(dsn, autocommit=False, connect_timeout=5) as c:
            RESTORE.restore(c, CHART,
                            RESTORE.load_and_verify_file(str(backup), CHART, count, joined_md5),
                            count, joined_md5, execute=True)
        report["final_live_certificate"] = live_certificate(cur, CHART)
        conn.close()
    finally:
        if not args.keep_database:
            R.drop_disposable_database(args.maintenance_dsn, dbname)

    report["failures"] = failures
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if failures:
        print("REHEARSAL FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("REHEARSAL PASSED: success reproduces the certificate; all five refusals fire; "
          "the steward's backup verifies.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
