"""Entry point of the separate VERIFICATION JOB (ND-ROLES option A; Codex round 9, R9-6.1).

    python -m pipeline.orchestrator.verification_job --chart <uuid> [--generation 5.0] [--class <c> …] [--report-only]
    python -m pipeline.orchestrator.verification_job --chart <uuid> [--generation 5.0] --brief [--sealing-commit <sha>]

NOT a registered writer and not in the build DAG: the orchestrator contract is frozen and nothing chains this to a build.
A person (an operator) runs it, once per (chart, generation), AFTER the build. It reads exactly ONE database credential,
`GOCHARA_VERIFIER_DB_URL` — the verifier principal's login; it never reads the builder's — and its first act is the
identity self-check (`verification_job.check_identity`): it refuses to run as the builder, as a superuser, or as any login
that can write a builder table. It does not `SET ROLE`.

`--brief` (R11-3) is the SEAL BRIEF mode, not a report: it evaluates the candidate adapter gate, reads the persisted attestations and persists
the brief (`ka_gochara_seal_brief`, F-R12-4) and prints a COMPACT last line `{"status": "BRIEFED", "sha256", "persisted": {brief_id,
manifest_id, state_digest}, "brief_bytes", "brief_file", "brief_chunks"}` — refusing (exit 3, the reasons named) unless the gate is clean
and every grain is VERIFIED under the manifest-pinned runner. The FULL brief (canonical JSON; its sha256 IS the digest) is not a log line —
it grows with the event-class count (~255 KB at 26 classes), so stdout ALWAYS carries it as `{brief_chunk, of, sha256, b64}` lines
(<= `--brief-chunk-bytes` raw bytes each, base64 — safe at any byte boundary) BEFORE the compact one (F-R13-2, steward ruling); `--brief-out
FILE` additionally writes the bytes. A lock not available within 2 minutes is a named refusal (`brief_lock_timeout`, exit 2). The approval carries that digest; the sealing step recomputes it under the
seal locks (`seal_brief.recompute_under_locks`) and refuses on any difference.

Prints one JSON report on stdout. Exit codes: 0 every required grain VERIFIED (or `--report-only` finished) · 2 refused by
a precondition (nothing written) · 3 an independent verifier DISAGREES (nothing written for that class; the gate stays
closed) · 4 identity/privilege self-check failed (nothing written) · 5 unexpected error (the class transaction rolled back).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

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
    ap.add_argument("--brief", action="store_true", help="produce, persist and digest the canonical seal approval payload; stdout ends in "
                    "{brief_chunk,...} lines then a COMPACT last line {status, sha256, persisted, brief_bytes, brief_file, brief_chunks}")
    ap.add_argument("--brief-out", default=None, help="also write the full brief (canonical JSON bytes; sha256 == the digest) to this file")
    ap.add_argument("--brief-chunk-bytes", type=int, default=48 * 1024, help="raw bytes per chunk line (default 48 KiB)")
    ap.add_argument("--sealing-commit", default=os.environ.get("GOCHARA_SEALING_COMMIT"))
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
        if args.brief:
            from services.gochara_kernel import seal_brief
            vj.check_identity(conn)
            import psycopg
            try:
                with conn.transaction():
                    # a held lock ends in a NAMED refusal (steward ruling M20261002T175331), never a hang
                    seal_brief.set_local_timeouts(conn, lock=seal_brief.BRIEF_LOCK_TIMEOUT)
                    out = seal_brief.brief(conn, args.chart, args.generation, sealing_commit=args.sealing_commit)
                    persisted = seal_brief.persist_brief(conn, out)      # F-R12-4: the receipt must name a brief persisted HERE
                raw = seal_brief.brief_bytes(out)
            except psycopg.errors.LockNotAvailable as exc:
                print(seal_brief.canonical_json({"status": "REFUSED", "code": "brief_lock_timeout", "detail":
                                                 f"a seal lock was not available within {seal_brief.BRIEF_LOCK_TIMEOUT}; nothing was "
                                                 f"persisted ({exc})"}))
                return vj.EXIT_REFUSED
            except seal_brief.BriefRefused as exc:
                print(seal_brief.canonical_json({"status": "REFUSED", "code": exc.code, "detail": exc.detail,
                                                 "violations": exc.violations}))
                return vj.EXIT_DISAGREE
            brief_file = None
            if args.brief_out:                                               # optional: the full brief as a file as well
                import hashlib
                path = Path(args.brief_out)
                path.write_bytes(raw)
                if hashlib.sha256(path.read_bytes()).hexdigest() != out["sha256"]:
                    print(seal_brief.canonical_json({"status": "ERROR", "detail": f"{path} does not read back as the brief"}))
                    return vj.EXIT_ERROR
                brief_file = str(path)
            # ONE path, always exercised (steward ruling): the full brief as index/total chunk lines, then the compact result as the LAST line
            for line in seal_brief.brief_chunk_lines(raw, out["sha256"], args.brief_chunk_bytes):
                print(line)
            print(seal_brief.canonical_json({"status": "BRIEFED", "sha256": out["sha256"], "persisted": persisted,
                                             "brief_bytes": len(raw), "brief_file": brief_file, "brief_chunks": True}))
            return vj.EXIT_OK
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
