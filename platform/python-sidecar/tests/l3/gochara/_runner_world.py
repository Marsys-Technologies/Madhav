"""A database for running the REAL orchestrator entry point (`python -m pipeline.orchestrator.main --run-id`) over ka_gochara_v5.

Built on the a55 template (real Gochara migration chain, rules + convention + body substrate already built) plus the orchestrator tables
from the REAL migrations, applied in dependency order — not stubs:

    167 asset_registry · 169 asset_throughput · 171 build_runs / build_run_assets · 172 throughput volume columns · 184 · 202 · 223 · 242 · 342 (has_writer) · 417 · 426 ·
    474 · 499 orchestrator_event_register · 586 asset_throughput_state_audit · 590 · 591 · 595 frozen run manifest · 596 provenance
    receipts / freshness · 598 output digest specs · 640 · 641 · 1200 · 1201

One deviation, stated: migration 598 also SEEDS digest specs for production assets (an INSERT whose foreign key needs those registry
rows); it is applied up to that INSERT. The v5 asset has no spec row in production either (its receipts are stored 'unknown').

`charts` is the template's one-column stub, widened with the birth columns `fetch_birth_params` reads (the canonical chart's real birth data).
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
SIDECAR = REPO / "platform" / "python-sidecar"
MIGRATION_ORDER = (167, 169, 171, 172, 184, 202, 223, 242, 342, 417, 426, 474, 499, 586, 590, 591, 595, 596, 598, 640, 641, 1200, 1201)
SEED_MARK = "INSERT INTO asset_output_digest_specs"
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
#: the migration-1304 shape of the small-test registry row (dispatch_v5_small_test_job.EXPECTED_REGISTRY_ROW), INACTIVE
V5_ROW = {"scope": "per_chart", "is_active": False, "has_writer": True, "has_substeps": True, "writer_timeout_seconds": 7200,
          "depends_on": ["ga_positions", "ga_dashas"], "target_table": "ka_gochara_eval_window",
          "count_sql": "SELECT COUNT(*) FROM ka_gochara_eval_window WHERE chart_id=$1 AND generation='5.0'",
          "target_floor": 0, "estimated_seconds": None}


def _files(number: int) -> list[str]:
    return sorted(glob.glob(str(REPO / f"platform/supabase/migrations/{number}_*.sql"))
                  + glob.glob(str(REPO / f"platform/migrations/{number}_*.sql")))


def apply_orchestrator_schema(conn) -> None:
    # the birth columns FIRST: migration 596 puts a trigger on charts that names them
    for column, ddl in (("chart_id", "uuid"), ("name", "text"), ("subject_name", "text"), ("preferred_name", "text"),
                        ("birth_date", "date"), ("birth_time", "time"), ("birth_lat", "numeric"), ("birth_lng", "numeric"),
                        ("birth_place", "text"), ("timezone_id", "text")):
        conn.execute(f"ALTER TABLE public.charts ADD COLUMN IF NOT EXISTS {column} {ddl}")
    for number in MIGRATION_ORDER:
        files = _files(number)
        assert files, f"migration {number} not found"
        for f in files:
            text = Path(f).read_text(encoding="utf-8")
            if number == 598 and SEED_MARK in text:
                text = text[:text.index(SEED_MARK)]
            try:
                conn.execute(text)
            except Exception:
                try:
                    conn.execute("ROLLBACK")
                except Exception:
                    pass
                raise
    conn.execute("INSERT INTO public.charts (id, chart_id, name, birth_date, birth_time, birth_lat, birth_lng, birth_place, timezone_id)"
                 " VALUES (%s, %s, 'native', '1984-02-05', '10:43', 20.2961, 85.8245, 'Bhubaneswar', 'Asia/Kolkata')"
                 " ON CONFLICT (id) DO UPDATE SET chart_id = EXCLUDED.chart_id, name = EXCLUDED.name, birth_date = EXCLUDED.birth_date,"
                 " birth_time = EXCLUDED.birth_time, birth_lat = EXCLUDED.birth_lat, birth_lng = EXCLUDED.birth_lng,"
                 " birth_place = EXCLUDED.birth_place, timezone_id = EXCLUDED.timezone_id", (CHART, CHART))


def seed_registry(conn, asset_ids, v5_row=V5_ROW) -> None:
    """Every registered writer needs an asset_registry row with has_writer (the runner's writer-gap preflight), plus the v5 row in its
    small-test shape, INACTIVE; ga_positions and ga_dashas are LIT with fresh freshness rows (its declared dependencies)."""
    for asset_id in sorted(asset_ids):
        if asset_id == "ka_gochara_v5":
            continue
        conn.execute(
            "INSERT INTO public.asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description,"
            " storage_type, scope, has_writer, is_active) VALUES (%s, 'ganita', 0, %s, %s, 'test row', 'postgres_table', 'per_chart',"
            " true, true) ON CONFLICT (asset_id) DO NOTHING", (asset_id, asset_id, asset_id))
    r = v5_row
    conn.execute(
        "INSERT INTO public.asset_registry (asset_id, layer, sort_order, sanskrit_name, english_name, english_description, storage_type,"
        " scope, is_active, has_writer, has_substeps, writer_timeout_seconds, depends_on, target_table, count_sql, target_floor,"
        " estimated_seconds, asset_kind, asset_type, catalog_status) VALUES ('ka_gochara_v5', 'kala', 0, 'v5', 'v5', 'small test',"
        " 'postgres_table', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'data', 'data', 'CURRENT')",
        (r["scope"], r["is_active"], r["has_writer"], r["has_substeps"], r["writer_timeout_seconds"], r["depends_on"],
         r["target_table"], r["count_sql"], r["target_floor"], r["estimated_seconds"]))
    for dep in r["depends_on"]:
        conn.execute("INSERT INTO public.asset_throughput (chart_id, asset_id, state) VALUES (%s, %s, 'lit')", (CHART, dep))
        conn.execute("INSERT INTO public.asset_freshness (asset_id, chart_id, partition_key, freshness_state, receipt_version)"
                     " VALUES (%s, %s, '__whole_asset__', 'fresh', 'test')", (dep, CHART))


def stage_run(conn, marker: dict, writer_digest: str) -> str:
    """A planned small-test run exactly as the dispatch stages it (the frozen manifest of dispatch_frozen_rebuild plus the slice marker,
    digested once), through the real columns."""
    sys.path.insert(0, str(REPO / "platform" / "scripts"))
    from dispatch_frozen_rebuild import _canonical_json, build_manifest
    import hashlib
    row = conn.execute("SELECT asset_id, scope, COALESCE(depends_on, '{}'), natural_key_partition FROM public.asset_registry"
                       " WHERE asset_id = 'ka_gochara_v5'").fetchone()
    candidate = {"asset_id": row[0], "scope": row[1], "depends_on": row[2], "natural_key_partition": row[3], "has_cowriters": False}
    manifest, _ = build_manifest(chart_id=CHART, candidate=candidate, expected_code_digest=writer_digest)
    manifest["gochara_v5_test_slice"] = marker
    digest = hashlib.sha256(_canonical_json(manifest).encode("utf-8")).hexdigest()
    run_id = str(uuid.uuid4())
    conn.execute("INSERT INTO public.asset_throughput (chart_id, asset_id, state) VALUES (%s, 'ka_gochara_v5', 'dormant')"
                 " ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL DO UPDATE SET state = 'dormant'", (CHART,))
    conn.execute("INSERT INTO public.build_runs (id, chart_id, scope, scope_target, action, state, plan, plan_manifest,"
                 " plan_manifest_digest, triggered_by) VALUES (%s, %s, 'asset_set', 'ka_gochara_v5', 'rebuild', 'planned',"
                 " '[\"ka_gochara_v5\"]'::jsonb, %s::jsonb, %s, 'gochara-v5-small-test')",
                 (run_id, CHART, json.dumps(manifest), digest))
    conn.execute("INSERT INTO public.build_run_assets (run_id, asset_id, position, state) VALUES (%s, 'ka_gochara_v5', 0, 'queued')",
                 (run_id,))
    return run_id


def run_real_entry_point(dsn: str, run_id: str, *, ephe_env: str | None, timeout: float = 3000.0) -> dict:
    """`python -m pipeline.orchestrator.main --run-id <id>` as a SUBPROCESS: the real entry point, the real runner, the real asset_runner.
    Nothing is patched; ctx.config is whatever the runner builds. `ephe_env` sets (or, when None, REMOVES) SE_EPHE_PATH and SWE_EPHE_PATH."""
    env = {k: v for k, v in os.environ.items() if k not in ("SE_EPHE_PATH", "SWE_EPHE_PATH", "NIRMANA_FORCE_EXECUTE")}
    env.update({"DATABASE_URL": dsn, "PUBSUB_DISABLED": "1", "ORCHESTRATOR_WORKER_LIMIT": "1", "PYTHONPATH": str(SIDECAR),
                "PYTHONUNBUFFERED": "1"})
    if ephe_env is not None:
        env["SE_EPHE_PATH"] = ephe_env
    started = time.monotonic()
    proc = subprocess.run([sys.executable, "-m", "pipeline.orchestrator.main", "--run-id", run_id], cwd=str(SIDECAR), env=env,
                          capture_output=True, text=True, timeout=timeout)
    return {"code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "seconds": time.monotonic() - started}


def substep_events(stdout: str) -> list[dict]:
    out = []
    for line in stdout.splitlines():
        line = line.strip()
        if line.startswith("[event] "):                     # events.emit_event prints "[event] <json>" when PUBSUB is disabled
            line = line[len("[event] "):]
        if line.startswith("{") and '"asset.substep"' in line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out
