"""
TI-l2-rerank-determinism-001 -- bo_laksana_rerank must be a pure function of its inputs.

Production evidence (build_run_assets, canonical chart, 2026-10-06): runs 358a50d3 and
e367ad89 both logged bo_karanajala output_changed=f and then bo_laksana_rerank
output_changed=t with identical signal ids, which marked bo_sangati / bo_upaya /
bo_pramana_mapa / bo_chart_gestalt / bo_anveshana stale and forced extra runs. Root
cause: the DIGESTED column graph_node_strength_contribution_jsonb (migration 939) carried
`"computed_at": datetime.now()` -- a different wall-clock value on every run.

These tests drive the real BoLaksanaRerankWriter.run() against an in-memory fake
connection and compare what it writes, so they fail on the base writer (wall-clock
computed_at; fetch-order-dependent UPDATE order) and pass on the fixed one.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers import bo_laksana as bl

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SHORT = dict(bl._LONG_TO_SHORT)


def _centrality_rows():
    # Deliberately identical centrality for several grahas (ties) + a duplicate subject row.
    rows = []
    for i, g in enumerate(GRAHAS):
        rows.append({
            "node_subject": g,
            "pagerank_score": Decimal("0.025"),          # tie across all grahas
            "eigenvector_centrality": Decimal("0.29") if i % 2 else Decimal("0.28"),
            "betweenness_centrality": Decimal("0.0"),
            "harmonic_centrality": Decimal("0.9"),
        })
    return rows


def _signal_rows():
    base = datetime(2026, 10, 6, 15, 37, 3, 340864, tzinfo=timezone.utc)
    rows = []
    for i in range(60):
        g = GRAHAS[i % len(GRAHAS)]
        rows.append({
            "signal_id": f"00000000-0000-0000-0000-{i:012d}",
            "configuration_jsonb": {"graha": SHORT[g]} if i % 7 else {"unrelated": 1},
            "computed_at": base + timedelta(seconds=i % 3),
        })
    return rows


class _Cur:
    def __init__(self, conn):
        self.conn = conn
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        if "SET graph_node_strength_contribution_jsonb" in sql:
            self.conn.updates.append((str(params[1]), json.loads(params[0])))
        else:  # pragma: no cover - any other write is a test failure
            raise AssertionError(f"unexpected cursor SQL: {sql[:80]}")


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Conn:
    def __init__(self, seed):
        self.updates: list[tuple[str, dict]] = []
        self.rng = random.Random(seed)

    def cursor(self):
        return _Cur(self)

    def execute(self, sql, params=None):
        # Shuffle every fetch: PostgreSQL gives no row order without ORDER BY.
        if "FROM bodha_cgm_nodes" in sql:
            rows = [dict(r) for r in _centrality_rows()]
        elif "valence_source = 'keyword_heuristic_v1'" in sql:
            rows = []
        elif "FROM bodha_msr_signals" in sql:
            rows = [dict(r) for r in _signal_rows()]
        else:  # pragma: no cover
            raise AssertionError(f"unexpected fetch SQL: {sql[:80]}")
        self.rng.shuffle(rows)
        return _Result(rows)


def _run(monkeypatch, seed):
    monkeypatch.setattr(bl, "CANONICAL_AYANAMSHAS", [AYA])
    monkeypatch.setattr(bl, "_populate_synthesis_rollups", lambda *a, **k: (0, 0))
    conn = _Conn(seed)
    ctx = SimpleNamespace(config={"chart_id": CHART}, db_conn=conn, dry_run=False)
    bl.BoLaksanaRerankWriter().run(ctx)
    return conn.updates


def _digest(updates) -> str:
    """Order-insensitive content digest, like output_digest.py (rows keyed by signal_id)."""
    canon = json.dumps(sorted(updates, key=lambda u: u[0]), sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()


def test_two_runs_with_identical_inputs_give_identical_payloads_and_digest(monkeypatch):
    first = _run(monkeypatch, seed=1)
    # Wall clock must not matter: simulate a later run by shifting datetime.now.
    real_dt = bl.datetime

    class _Later(real_dt):
        @classmethod
        def now(cls, tz=None):
            return real_dt(2030, 1, 1, tzinfo=tz or timezone.utc)

    monkeypatch.setattr(bl, "datetime", _Later)
    second = _run(monkeypatch, seed=1)
    assert first, "fixture must exercise the rerank UPDATE path"
    assert dict(first) == dict(second)
    assert _digest(first) == _digest(second)


def test_shuffled_fetch_order_does_not_change_payloads_digest_or_update_order(monkeypatch):
    runs = [_run(monkeypatch, seed=s) for s in (1, 2, 3, 4)]
    assert all(runs)
    for other in runs[1:]:
        assert dict(runs[0]) == dict(other)
        assert _digest(runs[0]) == _digest(other)
        # UPDATE order is a total order on signal_id, not on whatever the fetch returned.
        assert [sid for sid, _ in other] == [sid for sid, _ in runs[0]]
    ids = [sid for sid, _ in runs[0]]
    assert ids == sorted(ids)


def test_computed_at_is_the_source_row_timestamp_in_utc_iso8601(monkeypatch):
    updates = dict(_run(monkeypatch, seed=1))
    src = {r["signal_id"]: r["computed_at"] for r in _signal_rows()}
    for sid, payload in updates.items():
        assert payload["computed_at"] == src[sid].astimezone(timezone.utc).isoformat()
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?\+00:00", payload["computed_at"])
        assert payload["formula_version"] == "structural_role_rerank_v1"


def test_payload_is_pure_in_its_inputs():
    c = _centrality_rows()[0]
    a = bl._rerank_payload(c, "Sun", "2026-10-06T15:37:03.340864+00:00")
    b = bl._rerank_payload(dict(c), "Sun", "2026-10-06T15:37:03.340864+00:00")
    assert a == b
    assert set(a) == {"structural_role_score", "primary_graha", "pagerank_score", "eigenvector_centrality",
                      "betweenness_centrality", "harmonic_centrality", "formula_version", "computed_at"}


def test_centrality_fetch_has_total_order_and_deterministic_duplicate_choice():
    seen = {}

    class _C:
        def execute(self, sql, params=None):
            seen["sql"] = sql
            return _Result([
                {"node_subject": "Sun", "pagerank_score": 1, "eigenvector_centrality": 1,
                 "betweenness_centrality": 1, "harmonic_centrality": 1},
                {"node_subject": "Sun", "pagerank_score": 2, "eigenvector_centrality": 2,
                 "betweenness_centrality": 2, "harmonic_centrality": 2},
            ])

    out = bl._fetch_graha_centrality(_C(), CHART, AYA)
    assert re.search(r"ORDER BY node_subject, computed_at DESC NULLS LAST, node_id", seen["sql"])
    assert out["Sun"]["pagerank_score"] == 1  # first row of the ordered fetch wins


def test_writer_has_no_wall_clock_in_digested_payload():
    import inspect
    src = inspect.getsource(bl.BoLaksanaRerankWriter.run)
    assert "datetime.now" not in src
