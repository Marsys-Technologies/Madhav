"""A fired writer timeout leaves a possible state: the orchestrator marked the asset `error` and the run `failed`, and the writer thread that outlived the
eviction finished its plan and promoted the asset rows over the error mark (`asset_throughput.state = lit`, `build_run_assets.state = complete`) while the run
stays `failed` (steward TIMEOUT-RULING 2; docs/runbook section 7). The teardown is the response to a fired cap, so it must be indifferent to those two rows'
words: it proves ownership from the run's marker and stamp, never from the state an asset row claims.

The chain here is built by the writer's own substeps under a staged run (the same builder the other C38 real-database tests use), then the asset rows are
made to disagree with the run. Both worlds, `error` (the honest mark) and `lit`/`complete` (lit over error), must tear down identically.
"""
from __future__ import annotations

import pytest

from .test_c38_teardown_real_db import (ASSET, CHART_ID, _counts, _slice_run, _snapshot, _teardown, td, template, tworld)  # noqa: F401


def _make_asset_rows_say(w, rid, asset_state, run_asset_state):
    w.conn.execute("ALTER TABLE public.build_run_assets ADD COLUMN IF NOT EXISTS state text")
    w.conn.execute("ALTER TABLE public.build_run_assets ADD COLUMN IF NOT EXISTS error text")
    w.conn.execute("UPDATE public.build_run_assets SET state = %s, error = %s WHERE run_id = %s",
                   (run_asset_state, "BLOCKED: upstream dependency(ies) timeout:28800s did not complete in this run" if run_asset_state == "error" else None, rid))
    w.conn.execute("UPDATE public.asset_throughput SET state = %s WHERE asset_id = %s AND chart_id = %s", (asset_state, ASSET, CHART_ID))


@pytest.mark.parametrize("asset_state, run_asset_state", [("error", "error"), ("lit", "complete")], ids=["honest_error_mark", "lit_over_error"])
def test_a_failed_run_is_torn_down_whatever_its_asset_rows_claim(tworld, asset_state, run_asset_state):
    w = tworld
    rid = _slice_run(w, state="failed")
    _make_asset_rows_say(w, rid, asset_state, run_asset_state)
    assert w.conn.execute("SELECT state FROM public.build_runs WHERE id = %s", (rid,)).fetchone()[0] == "failed"
    assert sum(_counts(w).values()) > 0, "the failed run left a partial chain"
    before = _snapshot(w)
    _teardown(w, dry_run=True)                                       # the dry run accepts it and changes nothing
    assert _snapshot(w) == before
    _teardown(w)
    assert all(n == 0 for n in _counts(w).values()), {t: n for t, n in _counts(w).items() if n}
    assert w.conn.execute("SELECT count(*) FROM public.build_runs WHERE triggered_by = %s", (td.TRIGGERED_BY,)).fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.build_run_assets").fetchone()[0] == 0
    assert w.conn.execute("SELECT count(*) FROM public.asset_throughput WHERE asset_id = %s", (ASSET,)).fetchone()[0] == 0


def test_the_two_worlds_end_in_exactly_the_same_state(tworld):
    """The teardown's result does not depend on the asset rows' words: lit-over-error and error produce the same counts and bookkeeping."""
    w = tworld
    rid = _slice_run(w, state="failed")
    _make_asset_rows_say(w, rid, "lit", "complete")
    _teardown(w)
    after_lit = _snapshot(w)
    assert after_lit[0] and all(n == 0 for n in after_lit[0].values())
    # the bookkeeping that remains is only what is not this asset's (the registry row and other assets' rows)
    assert dict(after_lit[1]["registry"])[ASSET] is False
