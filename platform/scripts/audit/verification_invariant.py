#!/usr/bin/env python3
"""verification_invariant.py — the standing watchdog for `verification_pass_status`.

WHY THIS EXISTS
---------------
Four M-22 campaigns each declared completion and each was followed by a deeper layer:

  1. F-11 fixed the writers that emitted a bare `PASS` — and left 10,591 `PASS` rows in the data.
  2. §6.15 fixed TAP-6's false red — while the detector stayed blind to two emit forms.
  3. §6.17 widened the detector — and credited `chart_dashas` as earned.
  4. §6.18 found that 0.18% of those rows had ever been examined: every `_verify_*` reads
     `level_n == 1` and the verdict was broadcast to every level.

Each layer was DISCOVERED by someone looking, not REPORTED by anything watching. Every one of
them would have been caught by one of the three checks below, all of which are cheap and none of
which existed. That is the whole point of this file: the estate should tell us it has drifted
instead of waiting for the next audit to notice.

It is deliberately NOT a required PR check — it measures the DATA, which a PR does not change.
It runs on a schedule and on dispatch. See .github/workflows/verification-invariant.yml.

    python platform/scripts/audit/verification_invariant.py            # all checks
    python platform/scripts/audit/verification_invariant.py --report   # counts only, never fails

Exit 0 = all checks pass. Exit 1 = at least one FAIL. Exit 3 = could not run (no DATABASE_URL).
DATABASE_URL is read from the environment and never taken as an argument.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "python-sidecar"))

from brahmagyan.verification_vocab import (  # noqa: E402
    ALL_STATUSES,
    DIVERGENT_FLAGGED,
    PROHIBITED_STATUSES,
    VERIFICATION_PASS_STATUS_VOCAB,
    VERIFIED_STATUSES,
    two_pass_verdict,
)

#: Per-table declaration of which rows a verifier DEMONSTRABLY examines.
#:
#: This is the load-bearing declaration in the file, and it is deliberately explicit rather than
#: inferred: a wrong entry here makes the check lie in the same direction the estate already
#: lied. Each predicate must mirror the writer's own verifier input filter.
#:
#: `chart_dashas`: every `_verify_*` in ga_dashas_writer.py opens with
#: `[r for r in rows if r["level_n"] == 1]`, and `_verify_vimshottari` is additionally
#: pre-filtered on `kp_sublevel is None` at its call site.
#:
#: A table absent from this map is NOT exempt — it is reported as UNDECLARED, because "nobody
#: wrote down what gets examined" is exactly the state that let the broadcast survive.
EXAMINED_PREDICATE: dict[str, str] = {
    "chart_dashas": "level_n = 1 AND kp_sublevel IS NULL",
    # chart_facts / chart_divisionals: per-row verdicts (ga_nakshatra's two_pass_verdict, the
    # ga_vargas policy lookup). Every row that claims a verified tier is its own examined unit,
    # so the predicate is TRUE and the check degenerates to "no row claims more than it is".
    "chart_facts": "TRUE",
    "chart_divisionals": "TRUE",
}

#: Divergence tolerance. Zero: a row claiming a verified tier that no verifier examined is not a
#: rounding error, it is the defect. Declared as a constant so raising it is a visible decision.
CLAIM_EVIDENCE_TOLERANCE = 0


def _tables_with_column(cur) -> list[str]:
    cur.execute(
        """
        SELECT table_name FROM information_schema.columns
        WHERE column_name = 'verification_pass_status' AND table_schema = 'public'
          AND table_name NOT LIKE %s
        ORDER BY table_name
        """,
        ("%\\_\\_ssv\\_%",),
    )
    return [r[0] for r in cur.fetchall()]


def check_claim_vs_evidence(cur, results: list[dict]) -> None:
    """CHECK 1 — every row claiming a verified tier must be one a verifier actually examined.

    This is the query nobody had written. The broadcast survived four campaigns because of that.
    """
    verified = sorted(VERIFIED_STATUSES)
    for tbl in _tables_with_column(cur):
        pred = EXAMINED_PREDICATE.get(tbl)
        if pred is None:
            cur.execute(
                f'SELECT count(*) FROM "{tbl}" WHERE verification_pass_status = ANY(%s)',  # noqa: S608
                (verified,),
            )
            n = cur.fetchone()[0]
            if n:
                results.append({
                    "check": "claim_vs_evidence", "table": tbl, "status": "FAIL",
                    "detail": (
                        f"{n} row(s) claim a verified tier but {tbl} has NO examined-row predicate "
                        f"declared in EXAMINED_PREDICATE. Undeclared is not exempt — declare what a "
                        f"verifier reads for this table, or demote the rows."
                    ),
                })
            continue

        cur.execute(
            f'SELECT count(*) FROM "{tbl}" '  # noqa: S608
            f"WHERE verification_pass_status = ANY(%s) AND NOT ({pred})",
            (verified,),
        )
        unexamined = cur.fetchone()[0]
        cur.execute(
            f'SELECT count(*) FROM "{tbl}" WHERE verification_pass_status = ANY(%s)',  # noqa: S608
            (verified,),
        )
        claimed = cur.fetchone()[0]
        status = "FAIL" if unexamined > CLAIM_EVIDENCE_TOLERANCE else "PASS"
        results.append({
            "check": "claim_vs_evidence", "table": tbl, "status": status,
            "detail": (
                f"{claimed} row(s) claim a verified tier; {unexamined} of them fall OUTSIDE the "
                f"declared examined predicate ({pred}). Tolerance {CLAIM_EVIDENCE_TOLERANCE}."
            ),
        })


def check_vocabulary_conformance(cur, results: list[dict]) -> None:
    """CHECK 2 — no stored value outside the settled vocabulary, and no deprecated alias.

    `PASS` survived two campaigns because nothing watched the DATA. The writers were fixed both
    times; the rows were not.
    """
    deprecated = {e.status: e.deprecated_alias_of for e in VERIFICATION_PASS_STATUS_VOCAB if e.deprecated_alias_of}
    for tbl in _tables_with_column(cur):
        cur.execute(
            f'SELECT verification_pass_status, count(*) FROM "{tbl}" GROUP BY 1',  # noqa: S608
        )
        for value, n in cur.fetchall():
            if value is None:
                continue
            if value in PROHIBITED_STATUSES:
                results.append({
                    "check": "vocabulary_conformance", "table": tbl, "status": "FAIL",
                    "detail": f"{n} row(s) hold PROHIBITED value {value!r} (DVA Ruling 13 — names no pass that ran).",
                })
            elif value not in ALL_STATUSES:
                results.append({
                    "check": "vocabulary_conformance", "table": tbl, "status": "FAIL",
                    "detail": f"{n} row(s) hold {value!r}, which is not in the settled vocabulary.",
                })
            elif value in deprecated:
                results.append({
                    "check": "vocabulary_conformance", "table": tbl, "status": "FAIL",
                    "detail": f"{n} row(s) hold deprecated alias {value!r} — canonical form is {deprecated[value]!r}.",
                })


def check_detector_liveness(results: list[dict]) -> None:
    """CHECK 3 — the disagreement path must still be able to fire.

    `divergent_flagged` has zero rows estate-wide. That is only good news if the comparison CAN
    disagree. A verifier that has quietly lost its ability to fail is this campaign's defect
    reappearing, and it would look exactly like a clean table.

    Proven against the live sanctioned helper AND the live ga_nakshatra path that calls it — not
    against a copy of the logic, which would prove nothing about the shipped code.
    """
    if two_pass_verdict(1, 2) != DIVERGENT_FLAGGED:
        results.append({
            "check": "detector_liveness", "table": "-", "status": "FAIL",
            "detail": "two_pass_verdict() no longer returns divergent_flagged on disagreement.",
        })
        return
    if two_pass_verdict(1, 1) not in VERIFIED_STATUSES:
        results.append({
            "check": "detector_liveness", "table": "-", "status": "FAIL",
            "detail": "two_pass_verdict() no longer returns a verified tier on agreement.",
        })
        return

    try:
        from pipeline.orchestrator.writers import ga_nakshatra as gn
    except Exception as exc:  # pragma: no cover - import guard
        results.append({
            "check": "detector_liveness", "table": "-", "status": "FAIL",
            "detail": f"could not import the live ga_nakshatra verifier: {exc}",
        })
        return

    nak, pada = gn._derive_nakshatra_pada(13.5)
    # A PLAUSIBLE wrong value (a valid nakshatra id that is not the right one), never an
    # impossible one — per the §6.18 operational test.
    wrong = (nak % 27) + 3
    verdicts = gn._nakshatra_pada_verdicts(
        {"grahas": [{"name": "Sun", "longitude_deg": 13.5, "nakshatra_id": wrong, "pada": pada}], "ascendant": {}}
    )
    got = verdicts.get("SUN", {}).get("nakshatra")
    if got != DIVERGENT_FLAGGED:
        results.append({
            "check": "detector_liveness", "table": "-", "status": "FAIL",
            "detail": (
                f"the live ga_nakshatra second pass did NOT flag a plausible wrong nakshatra id "
                f"(expected {DIVERGENT_FLAGGED!r}, got {got!r}). The disagreement path is dead."
            ),
        })
        return
    results.append({
        "check": "detector_liveness", "table": "-", "status": "PASS",
        "detail": "two_pass_verdict and the live ga_nakshatra path both fire divergent_flagged on a plausible wrong value.",
    })


def tier_report(cur) -> dict[str, dict[str, int]]:
    """Counts by tier by table — emitted every run so drift is visible as a TREND, not only as a
    threshold breach. A number that moves 2% a month never trips a gate and is still the story."""
    out: dict[str, dict[str, int]] = {}
    for tbl in _tables_with_column(cur):
        cur.execute(f'SELECT verification_pass_status, count(*) FROM "{tbl}" GROUP BY 1 ORDER BY 2 DESC')  # noqa: S608
        rows = {(v or "NULL"): n for v, n in cur.fetchall()}
        if rows:
            out[tbl] = rows
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="emit the tier report only; never fails")
    args = ap.parse_args()

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("QUARANTINED: DATABASE_URL not set — the data checks cannot run.", file=sys.stderr)
        # Liveness needs no DB, so still run it rather than skipping silently.
        results: list[dict] = []
        check_detector_liveness(results)
        print(json.dumps({"results": results}, indent=2))
        return 3

    import psycopg

    results = []
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        report = tier_report(cur)
        if args.report:
            print(json.dumps({"tier_report": report}, indent=2))
            return 0
        check_claim_vs_evidence(cur, results)
        check_vocabulary_conformance(cur, results)
    check_detector_liveness(results)

    fails = [r for r in results if r["status"] == "FAIL"]
    print(json.dumps({"tier_report": report, "results": results}, indent=2))
    print("\n=== verification invariant ===")
    for r in results:
        print(f"[{r['status']}] {r['check']}:{r['table']} — {r['detail']}")
    print(f"\n{len(fails)} FAIL / {len(results)} checks")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
