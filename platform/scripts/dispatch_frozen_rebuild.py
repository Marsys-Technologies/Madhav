#!/usr/bin/env python3
"""Generalized frozen-manifest single-asset rebuild dispatch.

Generalized from dispatch_ka_gochara_frozen.py (L3 lane, proven correct twice
for ka_gochara on two charts) to accept --asset-id, since the same manifest-
construction pattern is now needed for ka_gochara_resonance (missing
asset_freshness receipt on chart 1c826d5a despite asset_throughput.state='lit'
and 750 rows present -- DEP-ASSERT ANOMALY blocking ka_gochara's rebuild on
that chart).

Mirrors dispatch_nirmana_f0_canary.py's manifest construction (same canonical-
JSON digest algorithm as src/app/api/cockpit/runs/route.ts) for a single
asset_set asset.
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

TRIGGERED_BY = "l3-lane-frozen-manifest-rebuild"
WRITER_DIGESTS_PATH = Path("/Users/Dev/nirmana-s/l3/platform/src/generated/nirmana-writer-digests.json")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def build_manifest(*, chart_id: str, candidate: Mapping[str, Any], expected_code_digest: str) -> tuple[dict[str, Any], str]:
    asset_id = candidate["asset_id"]
    manifest: dict[str, Any] = {
        "version": "nirmana-run-manifest/v1",
        "chart_id": chart_id,
        "scope": "asset_set",
        "scope_target": asset_id,
        "action": "rebuild",
        "waves": [[asset_id]],
        "assets": [{
            "asset_id": asset_id,
            "scope": candidate["scope"],
            "depends_on": list(candidate["depends_on"] or []),
            "natural_key_partition": candidate["natural_key_partition"],
            "has_cowriters": bool(candidate["has_cowriters"]),
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


def create_run(*, database_url: str, chart_id: str, asset_id: str, lock_key: str, commit: bool) -> dict[str, Any]:
    import psycopg
    import psycopg.rows

    connection = psycopg.connect(database_url, row_factory=psycopg.rows.dict_row)
    connection.autocommit = False
    connection.isolation_level = psycopg.IsolationLevel.SERIALIZABLE
    try:
        cur = connection.cursor()
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (lock_key,))
        cur.execute(
            """SELECT id, chart_id, state FROM build_runs
                 WHERE chart_id=%s AND state IN ('planned','running','paused')"""
            , (chart_id,)
        )
        active = cur.fetchall()
        if active:
            raise RuntimeError(f"active build run(s) exist for this chart; refusing ({active})")

        candidate = _load_candidate(cur, asset_id)
        manifest, manifest_digest = build_manifest(
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
                run_id, chart_id, asset_id, json.dumps([asset_id]),
                json.dumps(manifest), manifest_digest, TRIGGERED_BY,
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
            "run_id": run_id, "asset_id": asset_id, "chart_id": chart_id,
            "manifest": manifest, "manifest_digest": manifest_digest, "committed": commit,
        }
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def dispatch_run(*, run_id: str, project: str, region: str, job: str) -> str:
    result = subprocess.run(
        ["gcloud", "run", "jobs", "execute", job, f"--project={project}", f"--region={region}",
         f"--args=--run-id,{run_id}", "--async", "--format=value(metadata.name)"],
        capture_output=True, check=False, text=True,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "unknown gcloud error").strip()[:1000]
        raise RuntimeError(detail)
    execution = result.stdout.strip()
    if not execution:
        raise RuntimeError("gcloud returned no execution name")
    return execution


def terminalize_dispatch_failure(cur, *, run_id: str, error: str) -> None:
    message = f"dispatch failed: {error}"[:2000]
    cur.execute(
        """WITH failed_run AS (
               UPDATE build_runs SET state='failed', ended_at=NOW(), last_error=%s
                WHERE id=%s AND state='planned' RETURNING id
           )
           UPDATE build_run_assets SET state='aborted', ended_at=NOW(), error=%s
            WHERE run_id IN (SELECT id FROM failed_run) AND state='queued'""",
        (message, run_id, message),
    )


def mark_dispatch_failed(*, database_url: str, run_id: str, error: str) -> None:
    import psycopg
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cur:
            terminalize_dispatch_failure(cur, run_id=run_id, error=error)
        connection.commit()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--project", default="madhav-astrology")
    parser.add_argument("--region", default="asia-south1")
    parser.add_argument("--job", default="brahma-build-pipeline-job")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args()
    expected_confirmation = f"{args.asset_id.upper()}_FROZEN_REBUILD"
    if args.commit and args.confirm != expected_confirmation:
        parser.error(f"--commit requires --confirm {expected_confirmation}")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL required", file=sys.stderr)
        return 1
    try:
        receipt = create_run(
            database_url=database_url, chart_id=args.chart_id, asset_id=args.asset_id,
            lock_key=f"l3-{args.asset_id}-dispatch", commit=args.commit,
        )
    except Exception as exc:
        print(f"ERROR: run not created: {exc}", file=sys.stderr)
        return 2
    if args.commit:
        try:
            receipt["execution_name"] = dispatch_run(run_id=receipt["run_id"], project=args.project, region=args.region, job=args.job)
        except Exception as exc:
            mark_dispatch_failed(database_url=database_url, run_id=receipt["run_id"], error=str(exc))
            print(f"ERROR: dispatch failed and run terminalized: {exc}", file=sys.stderr)
            return 3
    print(json.dumps(receipt, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
