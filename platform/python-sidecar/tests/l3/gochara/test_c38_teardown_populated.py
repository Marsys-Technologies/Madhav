"""C38 — the small-test TEARDOWN over a POPULATED candidate (round 2, ASTRA's review of PR 3098).

`test_c38_teardown_real_db.py` builds records only, so it never showed the teardown against windows, window memberships, record
prerequisites, and BOTH verification tables (1206 inventory, 1240 window). Here the world is PR 3132's populated mirror (the same
`_populate` / `_add_survivors` its replace tests use): the teardown removes the whole populated chain — verification rows included —
and keeps the Moon on-demand partition and every other generation.
"""
from __future__ import annotations

import json
import os
import sys
import uuid
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod

from .test_a53_inventory import CHART_ID, H0, H1
from .test_a53_p1_support import GEN
from .test_a53_window_verification_roles import (_consistent_sky, _qualification_policy,  # noqa: F401  (autouse)
                                                 rworld)
from .test_a55_replace_chain_populated import CHAIN_TABLES, OTHER_GEN, _add_survivors, _coverage, _count, _populate
from .test_c38_teardown_real_db import STUB_DDL  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "platform" / "scripts"))
import teardown_v5_small_test_job as td  # noqa: E402

ASSET = td.ASSET_ID


def _bookkeeping(w):
    """The orchestrator tables the teardown touches, created only where this world lacks them."""
    for ddl in STUB_DDL:
        table = ddl.split("public.")[1].split(" ")[0]
        if w.conn.execute("SELECT to_regclass(%s)", (f"public.{table}",)).fetchone()[0] is None:
            w.conn.execute(ddl)
    e = td.EXPECTED_REGISTRY_ROW
    w.conn.execute("DELETE FROM public.asset_registry WHERE asset_id IN (%s, 'other_asset')", (ASSET,))
    w.conn.execute("INSERT INTO public.asset_registry VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                   (ASSET, e["scope"], True, e["has_writer"], e["has_substeps"], e["writer_timeout_seconds"], e["depends_on"],
                    e["target_table"], e["count_sql"], e["target_floor"], e["estimated_seconds"]))
    rid = uuid.uuid4()
    w.conn.execute("INSERT INTO public.build_runs (id, chart_id, scope, scope_target, state, triggered_by)"
                   " VALUES (%s, %s, 'asset', %s, 'completed', %s)", (rid, CHART_ID, ASSET, td.TRIGGERED_BY))
    w.conn.execute("INSERT INTO public.build_run_assets VALUES (%s, %s)", (rid, ASSET))
    w.conn.execute("INSERT INTO public.asset_provenance_receipts (asset_id, chart_id, partition_key, build_id) VALUES (%s, %s, 'p1', %s)",
                   (ASSET, CHART_ID, rid))
    w.conn.execute("INSERT INTO public.asset_freshness (asset_id, chart_id, partition_key) VALUES (%s, %s, 'p1')", (ASSET, CHART_ID))


def _stamp_consistently(w):
    """The populated mirror is built by the DEFAULT writer path, so its manifest carries no slice stamp. Give the manifest AND the stored
    snapshot the SAME stamped vector, made by the writer's own validator and component builder for a marker over the world's own
    horizon: the identity the teardown now demands (manifest = snapshot = inventory headers) holds, and everything else stays populated."""
    marker = {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": "all_classes_1y",
              "horizon": [H0.isoformat(), H1.isoformat()], "classes": list(writer_mod.SCORED_CLASSES)}
    sliced = writer_mod._validate_test_slice(marker)
    stamp = {"stored_scope": writer_mod.TEST_SLICE_SCOPE, "test_slice": writer_mod._slice_component(sliced)}
    with w.conn.transaction():                                   # behind the guards: a fixture rewrite, not a build step
        w.conn.execute("SET LOCAL session_replication_role = replica")
        for table in ("kala_gochara_publication", "ka_gochara_search_input_snapshot"):
            w.conn.execute(f"UPDATE public.{table} SET input_generation_vector = input_generation_vector || %s::jsonb WHERE generation = %s",
                           (json.dumps(stamp), GEN))


def test_the_teardown_removes_a_populated_candidate_verification_rows_included_and_keeps_the_survivors(rworld, monkeypatch):
    w = rworld
    _populate(w)
    _add_survivors(w)
    _bookkeeping(w)
    _stamp_consistently(w)
    for t in CHAIN_TABLES:
        assert _count(w.conn, t) >= 1, f"{t} is empty — the fixture does not populate it"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_record").fetchone()[0] >= 1
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_record_prerequisite").fetchone()[0] >= 1
    survivors = ({t: _count(w.conn, t, OTHER_GEN) for t in ("ka_gochara_contact",)}, _coverage(w.conn, OTHER_GEN))
    monkeypatch.setenv("DATABASE_URL", w.conn.info.dsn)
    td.teardown(dry_run=False)
    for t in CHAIN_TABLES:
        assert _count(w.conn, t) == 0, f"{t} survived the teardown"
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_eval_window_record").fetchone()[0] == 0     # memberships cascade
    assert w.conn.execute("SELECT count(*) FROM public.ka_gochara_record_prerequisite").fetchone()[0] == 0    # prerequisites cascade
    assert _count(w.conn, "kala_gochara_publication") == 0
    assert ("moon_on_demand", "moon-q1") in _coverage(w.conn)                                                   # the Moon survivor
    assert ({t: _count(w.conn, t, OTHER_GEN) for t in ("ka_gochara_contact",)}, _coverage(w.conn, OTHER_GEN)) == survivors
    assert w.conn.execute("SELECT count(*) FROM public.asset_provenance_receipts WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0
    assert w.conn.execute("SELECT is_active FROM public.asset_registry WHERE asset_id = %s", (ASSET,)).fetchone()[0] is False
