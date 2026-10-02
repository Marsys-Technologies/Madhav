"""Entry point of the separate VERIFICATION JOB (ND-ROLES option A; Codex round 9, R9-6.1).

    python -m pipeline.orchestrator.verification_job --chart <uuid> [--generation 5.0] [--class <c> …] [--report-only]

NOT a registered writer and not in the build DAG: the orchestrator contract is frozen and nothing chains this to a build.
A person (an operator) runs it, once per (chart, generation), AFTER the build. It reads exactly ONE database credential,
`GOCHARA_VERIFIER_DB_URL` — the verifier principal's login; it never reads the builder's — and its first act is the
identity self-check (`verification_job.check_identity`): it refuses to run as the builder, as a superuser, or as any login
that can write a builder table. It does not `SET ROLE`.

Prints one JSON report on stdout. Exit codes: 0 every required grain VERIFIED (or `--report-only` finished) · 2 refused by
a precondition (nothing written) · 3 an independent verifier DISAGREES (nothing written for that class; the gate stays
closed) · 4 identity/privilege self-check failed (nothing written) · 5 unexpected error (the class transaction rolled back).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from services.gochara_kernel import verification_job as vj

ENV_URL = "GOCHARA_VERIFIER_DB_URL"


def _build_kwargs(conn, ephe_path: str | None) -> dict:
    """The builder-side CONFIGURATION the verification needs (which versions are selected, which rulings stand, how
    positions are probed) — read from the writer module's constants, never from the builder's database credential."""
    from datetime import datetime

    from pipeline.orchestrator.writers import ka_gochara_v5 as w
    from services.gochara_kernel import input_vector as iv
    from services.gochara_kernel import rule_registry as rr

    def position_at(body: str, t: datetime) -> float:
        jd = t.timestamp() / 86400.0 + w._JD_UNIX_EPOCH
        lon, retflag = w.calc_sidereal_lon(body.title(), jd, ephe_path)
        if not (retflag & 2):
            raise RuntimeError(f"position probe {body} @ {t.isoformat()}: retflag {retflag} lacks the Swiss bit (F-14)")
        return lon
    position_at.cache_key = ("swiss", ephe_path)
    moon = _moon_scope_available(conn)
    bound_rows = rr.RuleRegistryStore(conn).bound_factor_rows
    return dict(
        position_at=position_at, ephe_path=ephe_path, modules=iv.IMPLEMENTATION_MODULES, path_refs=rr.bound_path_refs(),
        configured_selection_for=rr.selected_versions_for, path_rulings=w.VERIFIER_PATH_RULINGS,
        h_unknown=w.VERIFIER_H_UNKNOWN_RULING, moon_scope_domain=moon, factor_rows_for=bound_rows,
        drishti_bound=w.DRISHTI_SOURCE is not None, vedha_bound=w.VEDHA_SOURCE is not None)


def _moon_scope_available(conn) -> bool:
    """Does the APPLIED schema account a Moon-resolved period-role interval (1232)? Read, never assumed — the same read the
    builder's inventory store makes."""
    row = conn.execute(
        "SELECT to_regprocedure('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)')"
        " IS NOT NULL AND EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = 'kgsiv_state_ck'"
        " AND c.conrelid = 'public.ka_gochara_search_interval'::regclass"
        " AND pg_get_constraintdef(c.oid) LIKE '%excluded_moon_tier%')").fetchone()
    return bool(row[0] if not isinstance(row, dict) else next(iter(row.values())))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="verification_job", description=__doc__.split("\n\n")[0])
    ap.add_argument("--chart", required=True)
    ap.add_argument("--generation", default=vj.GENERATION)
    ap.add_argument("--class", dest="classes", action="append", default=None)
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--ephe-path", default=os.environ.get("SE_EPHE_PATH"))
    args = ap.parse_args(argv)
    url = os.environ.get(ENV_URL)
    if not url:
        print(json.dumps({"status": "REFUSED", "code": "no_verifier_credential",
                          "detail": f"{ENV_URL} is not set"}))
        return vj.EXIT_PRIVILEGE
    import psycopg
    conn = psycopg.connect(url, autocommit=True)
    try:
        report = vj.run(conn, chart_id=args.chart, generation=args.generation, classes=args.classes,
                        report_only=args.report_only, **_build_kwargs(conn, args.ephe_path))
        print(json.dumps(report, default=str, sort_keys=True))
        return report["exit_code"]
    except vj.VerificationRefused as exc:
        print(json.dumps({"status": "REFUSED", "code": exc.code, "detail": exc.detail}))
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 — the class transaction rolled back; say so, exit 5
        print(json.dumps({"status": "ERROR", "detail": f"{type(exc).__name__}: {exc}"}))
        return vj.EXIT_ERROR
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
