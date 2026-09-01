#!/usr/bin/env python3
"""Create one F0 machinery canary run with a runner-validated frozen manifest.

This is deliberately narrower than a campaign execution.  It schedules one
dependency-free L0 data asset and never writes a Nirmana campaign acceptance
event.  The conductor dispatches the returned run with ``--run-id`` and records
the result separately as machinery evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Mapping


DEFAULT_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
DEFAULT_ASSET_ID = "bg_formula_constants"
TRIGGERED_BY = "nirmana-f0-machinery-canary"
CONFIRMATION = "NIRMANA_F0_CANARY"
WRITER_DIGESTS_PATH = Path(__file__).resolve().parents[1] / "src" / "generated" / "nirmana-writer-digests.json"


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def build_canary_manifest(
    *,
    chart_id: str,
    candidate: Mapping[str, Any],
    expected_code_digest: str,
) -> tuple[dict[str, Any], str]:
    """Return the one-asset manifest accepted by the production runner."""
    asset_id = candidate.get("asset_id")
    if not isinstance(asset_id, str) or not asset_id:
        raise ValueError("canary asset_id is missing")
    if chart_id != DEFAULT_CHART_ID:
        raise ValueError("F0 canary is restricted to the only approved chart")
    if asset_id != DEFAULT_ASSET_ID:
        raise ValueError("F0 canary is restricted to the only approved asset")
    if candidate.get("layer") != "brahmagyan":
        raise ValueError("F0 canary must be an L0 asset")
    if candidate.get("scope") != "global":
        raise ValueError("F0 canary asset must be global")
    if candidate.get("asset_kind") != "data":
        raise ValueError("F0 canary must be a data asset")
    depends_on = list(candidate.get("depends_on") or [])
    if depends_on:
        raise ValueError("F0 canary must have no dependencies")
    partition = candidate.get("natural_key_partition")
    has_cowriters = bool(candidate.get("has_cowriters"))
    if has_cowriters:
        raise ValueError("F0 canary must not share its target table")
    if partition is not None:
        raise ValueError("F0 canary must use the whole-asset partition")
    if (
        len(expected_code_digest) != 64
        or any(char not in "0123456789abcdef" for char in expected_code_digest)
    ):
        raise ValueError("canary expected code digest is invalid")

    manifest: dict[str, Any] = {
        "version": "nirmana-run-manifest/v1",
        "chart_id": chart_id,
        "scope": "asset_set",
        "scope_target": asset_id,
        "action": "rebuild",
        "waves": [[asset_id]],
        "assets": [{
            "asset_id": asset_id,
            "scope": "global",
            "depends_on": [],
            "natural_key_partition": partition,
            "has_cowriters": has_cowriters,
            "expected_code_digest": expected_code_digest,
        }],
    }
    digest = hashlib.sha256(_canonical_json(manifest).encode("utf-8")).hexdigest()
    return manifest, digest


def _load_writer_digest(asset_id: str) -> str:
    inventory = json.loads(WRITER_DIGESTS_PATH.read_text(encoding="utf-8"))
    digest = inventory.get("writers", {}).get(asset_id)
    if not isinstance(digest, str):
        raise RuntimeError(f"writer digest missing for {asset_id}")
    return digest


def _load_candidate(cur, asset_id: str) -> dict[str, Any]:
    # Plain SELECT, not FOR SHARE: nirmana_campaign_control_writer is
    # deliberately SELECT-only (no UPDATE) on asset_registry, and Postgres's
    # row-locking clauses require UPDATE privilege -- see the identical fix
    # in platform/src/lib/nirmana-elevation/definitions.ts's accept/supersede
    # asset_registry reads. create_canary_run runs this transaction under
    # SERIALIZABLE isolation (set immediately after connecting, before this
    # call), which provides the same conflict protection via SSI without
    # needing a lock or elevated privilege.
    cur.execute(
        """
        SELECT ar.asset_id, ar.layer, ar.scope, ar.asset_kind,
               COALESCE(ar.depends_on, '{}') AS depends_on,
               ar.natural_key_partition,
               EXISTS (
                 SELECT 1 FROM asset_registry peer
                  WHERE peer.target_table = ar.target_table
                    AND ar.target_table IS NOT NULL
                    AND peer.asset_id <> ar.asset_id
                    AND peer.is_active = true AND peer.has_writer = true
               ) AS has_cowriters
          FROM asset_registry ar
         WHERE ar.asset_id = %s AND ar.is_active = true AND ar.has_writer = true
        """,
        (asset_id,),
    )
    row = cur.fetchone()
    if not row:
        raise RuntimeError(f"active writer registry row missing for {asset_id}")
    return dict(row)


def create_canary_run(*, database_url: str, chart_id: str, asset_id: str, commit: bool) -> dict[str, Any]:
    import psycopg
    import psycopg.rows

    connection = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    connection.autocommit = False
    # SERIALIZABLE, not the psycopg/Postgres default READ COMMITTED: this is
    # what lets _load_candidate's asset_registry read safely drop FOR SHARE
    # (see that function's comment) -- SSI conflict detection covers the same
    # concurrent-write case a lock would, without needing UPDATE privilege on
    # a table this role is deliberately SELECT-only on.
    connection.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
    try:
        cur = connection.cursor()
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", ("nirmana-f0-canary",))
        cur.execute(
            """SELECT id, chart_id, state FROM build_runs
                 WHERE state IN ('planned', 'running', 'paused')
                 ORDER BY created_at"""
        )
        active = cur.fetchall()
        if active:
            raise RuntimeError(f"active build runs exist; canary refused ({len(active)})")

        candidate = _load_candidate(cur, asset_id)
        manifest, manifest_digest = build_canary_manifest(
            chart_id=chart_id,
            candidate=candidate,
            expected_code_digest=_load_writer_digest(asset_id),
        )
        run_id = str(uuid.uuid4())
        cur.execute(
            """
            INSERT INTO build_runs
              (id, chart_id, scope, scope_target, action, state, plan,
               plan_manifest, plan_manifest_digest, triggered_by)
            VALUES (%s, %s, 'asset_set', %s, 'rebuild', 'planned', %s::jsonb,
                    %s::jsonb, %s, %s)
            """,
            (
                run_id,
                chart_id,
                asset_id,
                json.dumps([asset_id]),
                json.dumps(manifest),
                manifest_digest,
                TRIGGERED_BY,
            ),
        )
        cur.execute(
            """INSERT INTO build_run_assets (run_id, asset_id, position, state)
               VALUES (%s, %s, 0, 'queued')""",
            (run_id, asset_id),
        )
        if commit:
            connection.commit()
        else:
            connection.rollback()
        return {
            "run_id": run_id,
            "asset_id": asset_id,
            "chart_id": chart_id,
            "manifest_digest": manifest_digest,
            "committed": commit,
            "acceptance_event_recorded": False,
            "partition_key": candidate.get("natural_key_partition") or "__whole_asset__",
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def dispatch_canary_run(
    *,
    run_id: str,
    project: str,
    region: str,
    job: str,
    run_command=subprocess.run,
) -> str:
    """Start the deployed runner with the only ratified per-run override."""
    result = run_command(
        [
            "gcloud", "run", "jobs", "execute", job,
            f"--project={project}",
            f"--region={region}",
            f"--args=--run-id,{run_id}",
            "--async",
            "--format=value(metadata.name)",
        ],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown gcloud error").strip()[:1000]
        raise RuntimeError(detail)
    execution = result.stdout.strip()
    if not execution:
        raise RuntimeError("gcloud returned no execution name")
    return execution


def terminalize_dispatch_failure(cur, *, run_id: str, error: str) -> None:
    """Remove a failed-to-dispatch canary from the active-run set."""
    message = f"canary dispatch failed: {error}"[:2000]
    cur.execute(
        """WITH failed_run AS (
               UPDATE build_runs
                  SET state='failed', ended_at=NOW(), last_error=%s
                WHERE id=%s AND state='planned'
            RETURNING id
           )
           UPDATE build_run_assets
              SET state='aborted', ended_at=NOW(), error=%s
            WHERE run_id IN (SELECT id FROM failed_run)
              AND state='queued'""",
        (message, run_id, message),
    )


def mark_dispatch_failed(*, database_url: str, run_id: str, error: str) -> None:
    import psycopg

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cur:
            terminalize_dispatch_failure(cur, run_id=run_id, error=error)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the governed Nirmana F0 machinery canary")
    parser.add_argument("--project", default="madhav-astrology")
    parser.add_argument("--region", default="asia-south1")
    parser.add_argument("--job", default="brahma-build-pipeline-job")
    parser.add_argument("--commit", action="store_true", help="Commit the run; omission is a rollback-only dry run")
    parser.add_argument("--confirm", help=f"Required with --commit: {CONFIRMATION}")
    args = parser.parse_args()

    if args.commit and args.confirm != CONFIRMATION:
        parser.error(f"--commit requires --confirm {CONFIRMATION}")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL is required; obtain it from configured secret access without printing it.", file=sys.stderr)
        return 1

    try:
        receipt = create_canary_run(
            database_url=database_url,
            chart_id=DEFAULT_CHART_ID,
            asset_id=DEFAULT_ASSET_ID,
            commit=args.commit,
        )
    except Exception as exc:
        print(f"ERROR: canary run not created: {exc}", file=sys.stderr)
        return 2
    if args.commit:
        try:
            receipt["execution_name"] = dispatch_canary_run(
                run_id=receipt["run_id"],
                project=args.project,
                region=args.region,
                job=args.job,
            )
        except Exception as exc:
            mark_dispatch_failed(database_url=database_url, run_id=receipt["run_id"], error=str(exc))
            print(f"ERROR: canary dispatch failed and run was terminalized: {exc}", file=sys.stderr)
            return 3
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
