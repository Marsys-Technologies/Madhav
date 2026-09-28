#!/usr/bin/env python3
"""step08_flip.py — WP10 runbook step 8 (plan §9): the authority flip.

The flip is the LAST act of step 8 and is logged with
`evidence_ref = manifest_id` (7.C). Sets:

  * kala_gochara_authority: (chart_id, authoritative_generation='4.0',
    flipped_at, flipped_by, evidence_ref=<manifest_id>)
  * kala_gochara_publication: the candidate manifest -> status='published'
    (via the ledger's own publish(), which recomputes row_counts and
    content_digest — never hand-stamped)

Tranche 2 (PRODUCTION_TRANCHE_2_AUTHORIZED). Sheet A-3. Preconditions the
script checks itself before flipping (any failure → exit 8, nothing written):
  * the candidate manifest exists and is not already published
  * step 7's gates are not required to be re-run here, but the manifest's
    coverage rows must exist (flip-over-void refused — conjunct (k)'s
    run-time form)
  * the ledger's publish refusal machinery is intact (published generations
    refuse delete-then-insert)

Reversal (plan §9 step 8; K3-F2 / ADK-0024 §2): re-point authority to '3.0'
FIRST; manifest 'rolled_back' (ledger.rollback() deletes the generation's
coverage + contacts); then the reversed chart's '4.0' windows are
scoped-deleted (ledger.clear_windows_on_reversal — the explicit
EXPLICIT_CLEAR_OPS['ka_gochara'] windows op; refuses unless the manifest is
candidate/rolled_back AND the generation is no longer the served authority).
'v1'/'3.0' rows are untouchable on this path. Burned label: a rolled_back
manifest refuses re-publication — a re-attempt builds under a NEW generation
label. Post-reversal evidence must record a fresh integrity evaluation
(conjuncts (a)/(f) GREEN again once the orphan windows are gone) and NOTE
that conjunct (i) is vacuous for step06b's row shape (bare-string
active_sentences) — the gate is not earned on an empty check. Flips are
per-chart: a failed chart-2 flip does NOT roll back chart-1. Disclosed
consequence (runbook): a rollback after step 9 leaves Kṣetra's newer
provenance edges pointing at '4.0' rows that are deleted by this cleanup —
stated rather than discovered.

Usage:
    python3 step08_flip.py --dsn postgresql://... --chart-id <uuid> \
        --flipped-by <principal> [--generation 4.0] [--reverse] [--evidence]

Exit codes: 0 flipped (or reversed); 3 cannot proceed; 4 production refusal;
8 precondition failed.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]


def _load_ledger():
    spec = importlib.util.spec_from_file_location(
        "cutover_step08_ledger", SIDECAR / "services" / "gochara_kernel" / "ledger.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = step_parser(8, __doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default="4.0")
    parser.add_argument("--flipped-by", required=True,
                        help="principal performing the flip (recorded on the "
                             "authority row)")
    parser.add_argument("--reverse", action="store_true",
                        help="re-point authority to '3.0' and mark the manifest "
                             "rolled_back (the runbook's step-8 reversal)")
    args = parser.parse_args()

    ledger = _load_ledger()
    conn = connect(args.dsn, step=8, autocommit=False)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT manifest_id, status FROM kala_gochara_publication "
                "WHERE chart_id = %s AND generation = %s",
                (args.chart_id, args.generation))
            row = cur.fetchone()

        if args.reverse:
            if not row:
                print("ERROR: no manifest to roll back", file=sys.stderr)
                conn.close()
                return 8
            # K3-F2 / ADK-0024 §2 ordering: authority reversed FIRST, manifest
            # rolled back, THEN the reversed chart's '4.0' windows are
            # scoped-deleted — the cleanup's own guard refuses while the
            # generation is still the served authority.
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE kala_gochara_authority "
                    "SET authoritative_generation = '3.0', flipped_at = now(), "
                    "    flipped_by = %s, evidence_ref = %s "
                    "WHERE chart_id = %s",
                    (args.flipped_by, str(row[0]), args.chart_id))
            ledger.rollback(conn, args.chart_id, args.generation)
            n_windows_deleted = ledger.clear_windows_on_reversal(
                conn, args.chart_id, args.generation)
            conn.commit()
            report = {"chart_id": args.chart_id, "generation": args.generation,
                      "action": "reversed", "authority": "3.0",
                      "manifest_id": str(row[0]), "manifest_status": "rolled_back",
                      "windows_deleted": n_windows_deleted,
                      "label_burned": "a rolled_back manifest refuses "
                                      "re-publication — a re-attempt builds "
                                      "under a NEW generation label"}
            print(json.dumps(report, indent=2))
            if args.evidence:
                write_evidence(8, "REVERSED", json.dumps(report, indent=2))
            conn.close()
            return 0

        # Preconditions (self-checked; a failure here is a stop, not a patch).
        problems = []
        if not row:
            problems.append("no manifest exists for (chart, generation)")
        elif row[1] == "published":
            problems.append("manifest already published — flip is idempotent "
                            "only as a no-op; re-run is refused")
        elif row[1] != "candidate":
            problems.append(f"manifest status is {row[1]!r}, not 'candidate'")
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM kala_gochara_coverage "
                "WHERE chart_id = %s AND generation = %s",
                (args.chart_id, args.generation))
            if cur.fetchone()[0] == 0:
                problems.append("no coverage rows — a flip over a void is "
                                "refused (conjunct (k)'s run-time form)")
            cur.execute(
                "SELECT count(*) FROM kala_gochara_contacts "
                "WHERE chart_id = %s AND generation = %s",
                (args.chart_id, args.generation))
            n_contacts = cur.fetchone()[0]
            # E-012: the ledger and coverage checks above cannot see the SERVED table. Serving
            # reads kala_gochara_windows at the authoritative generation, so flipping onto a
            # generation with no window rows empties the served forecast for this chart.
            cur.execute(
                "SELECT count(*) FROM kala_gochara_windows "
                "WHERE chart_id = %s AND generation = %s",
                (args.chart_id, args.generation))
            if cur.fetchone()[0] == 0:
                problems.append(
                    "no kala_gochara_windows rows for this generation — flipping serving "
                    "authority would empty the served forecast for this chart; the '4.0' windows "
                    "projection (plan §2.2/§4.7) has no writer yet (E-012). A flip over a void "
                    "is refused.")
        if problems:
            for p in problems:
                print(f"PRECONDITION FAILED: {p}", file=sys.stderr)
            conn.close()
            return 8

        manifest_id = ledger.publish(conn, args.chart_id, args.generation)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO kala_gochara_authority "
                "  (chart_id, authoritative_generation, flipped_at, flipped_by, "
                "   evidence_ref) "
                "VALUES (%s, %s, now(), %s, %s) "
                "ON CONFLICT (chart_id) DO UPDATE SET "
                "  authoritative_generation = EXCLUDED.authoritative_generation, "
                "  flipped_at = EXCLUDED.flipped_at, "
                "  flipped_by = EXCLUDED.flipped_by, "
                "  evidence_ref = EXCLUDED.evidence_ref",
                (args.chart_id, args.generation, args.flipped_by,
                 str(manifest_id)))
        conn.commit()
        report = {"chart_id": args.chart_id, "generation": args.generation,
                  "action": "flipped", "manifest_id": str(manifest_id),
                  "evidence_ref": str(manifest_id), "contacts": n_contacts,
                  "flipped_by": args.flipped_by}
        print(json.dumps(report, indent=2))
        if args.evidence:
            write_evidence(8, "GREEN", json.dumps(report, indent=2))
        conn.close()
        return 0
    except Exception:
        conn.rollback()
        conn.close()
        raise


if __name__ == "__main__":
    sys.exit(main())
