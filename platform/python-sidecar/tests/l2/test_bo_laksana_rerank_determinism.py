"""
TI-l2-rerank-determinism-001 -- bo_laksana_rerank must be a pure function of its inputs.

Production evidence (build_run_assets, canonical chart, 2026-10-06): runs 358a50d3 and
e367ad89 both logged bo_karanajala output_changed=f and then bo_laksana_rerank
output_changed=t with identical signal ids, which marked bo_sangati / bo_upaya /
bo_pramana_mapa / bo_chart_gestalt / bo_anveshana stale and forced extra runs. Root
cause: the DIGESTED column graph_node_strength_contribution_jsonb (migration 939) carried
`"computed_at": datetime.now()` -- a different wall-clock value on every run.

The replacement value is the newest chart_facts.computed_at (an L1 input). It is NOT the
signal row's computed_at (bo_laksana re-mints that on every run, even a forced one with
identical content) and NOT bodha_cgm_nodes.computed_at (bo_karanajala stamps now()).

These tests drive the real BoLaksanaRerankWriter.run() against an in-memory fake
connection. The fake HONOURS the ORDER BY clauses the writer sends (sorting by exactly
those keys) and SHUFFLES any fetch that carries none, so removing an ORDER BY from the SQL
changes the result (or the SQL-text assertion fails).
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

from pipeline.orchestrator.writers import bo_laksana as bl

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
AYA = "lahiri_chitrapaksha"
GRAHAS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
SHORT = dict(bl._LONG_TO_SHORT)
FACTS_AS_OF = datetime(2026, 10, 4, 6, 0, 35, 576179, tzinfo=timezone.utc)
ROW_BASE = datetime(2026, 10, 6, 15, 37, 3, 340864, tzinfo=timezone.utc)
OTHER_CHART = "1c826d5a-0000-0000-0000-000000000000"
OTHER_AYA = "raman"
# chart_facts.computed_at rows as (chart_id, ayanamsha_id, computed_at): several per key (several
# build generations), a LATER row for another ayanamsha and for another chart, and an EARLIER row.
FACTS_TABLE = [
    (CHART, AYA, FACTS_AS_OF - timedelta(hours=2)),
    (CHART, AYA, FACTS_AS_OF),
    (CHART, AYA, FACTS_AS_OF - timedelta(days=1)),
    (CHART, OTHER_AYA, FACTS_AS_OF + timedelta(hours=5)),
    (OTHER_CHART, AYA, FACTS_AS_OF + timedelta(days=30)),
]

ORDER_KEYS = {
    "ORDER BY signal_id": lambda r: str(r["signal_id"]),
    "ORDER BY actor, target, varga, value_text": lambda r: (r["actor"], r["target"], r["varga"], r["value_text"]),
    "ORDER BY node_subject, computed_at DESC NULLS LAST, node_id": lambda r: r["node_subject"],
}


def _centrality_rows():
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


def _signal_rows(row_time=ROW_BASE):
    rows = []
    for i in range(60):
        g = GRAHAS[i % len(GRAHAS)]
        rows.append({
            "signal_id": f"00000000-0000-0000-0000-{i:012d}",
            "configuration_jsonb": {"graha": SHORT[g]} if i % 7 else {"unrelated": 1},
            "computed_at": row_time + timedelta(seconds=i % 3),
        })
    return rows


def _kw_rows():
    # keyword_heuristic rows that resolve through the widened lookup: SUN, house 2, D1.
    return [{"signal_id": f"11111111-0000-0000-0000-{i:012d}",
             "configuration_jsonb": {"graha": "SUN", "target_house": 2},
             "varga_id": "D1", "fact_kind": "x"} for i in range(8)]


def _vichara_rows():
    # same (actor, target, varga) key twice with DIFFERENT value_text: ORDER BY value_text
    # makes "malefic" (the later one) win deterministically.
    return [
        {"actor": "SUN", "target": "D1_HOUSE_2", "varga": "D1", "value_text": "malefic"},
        {"actor": "SUN", "target": "D1_HOUSE_2", "varga": "D1", "value_text": "benefic"},
    ]


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
        elif "SET valence = %s" in sql:
            self.conn.valence_updates.append((str(params[2]), params[0], params[1]))
        else:  # pragma: no cover
            raise AssertionError(f"unexpected cursor SQL: {sql[:80]}")


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows


class _Conn:
    def __init__(self, seed, row_time=ROW_BASE):
        self.updates: list[tuple[str, dict]] = []
        self.valence_updates: list[tuple[str, str, str]] = []
        self.sqls: list[str] = []
        self.facts_queries: list[tuple[str, list]] = []
        self.rng = random.Random(seed)
        self.row_time = row_time

    def cursor(self):
        return _Cur(self)

    def execute(self, sql, params=None):
        self.sqls.append(sql)
        if "FROM bodha_cgm_nodes" in sql:
            rows = [dict(r) for r in _centrality_rows()]
        elif "FROM chart_facts" in sql:
            self.facts_queries.append((sql, list(params)))
            # Answer like PostgreSQL would for the SQL it was actually sent: max() over the rows
            # that survive the chart_id / ayanamsha_id predicates present in the text.
            chart, aya = params[0], params[1]
            hit = [t for c, a, t in FACTS_TABLE
                   if ("chart_id = %s" not in sql or c == chart) and ("ayanamsha_id = %s" not in sql or a == aya)]
            agg = max if "max(computed_at)" in sql else min
            return _Result([{"as_of": agg(hit) if hit else None}])
        elif "valence_source = 'keyword_heuristic_v1'" in sql:
            rows = [dict(r) for r in _kw_rows()]
        elif "FROM chart_vichara" in sql:
            rows = [dict(r) for r in _vichara_rows()]
        elif "FROM bodha_msr_signals" in sql:
            rows = [dict(r) for r in _signal_rows(self.row_time)]
        else:  # pragma: no cover
            raise AssertionError(f"unexpected fetch SQL: {sql[:80]}")
        # PostgreSQL gives no order without ORDER BY: honour a recognised clause, else shuffle.
        for clause, key in ORDER_KEYS.items():
            if clause in sql:
                return _Result(sorted(rows, key=key))
        self.rng.shuffle(rows)
        return _Result(rows)


def _run_conn(monkeypatch, seed, row_time=ROW_BASE):
    monkeypatch.setattr(bl, "ayanamshas_for_chart", lambda _c, _i: [AYA])
    monkeypatch.setattr(bl, "_populate_synthesis_rollups", lambda *a, **k: (0, 0))
    conn = _Conn(seed, row_time)
    ctx = SimpleNamespace(config={"chart_id": CHART}, db_conn=conn, dry_run=False)
    bl.BoLaksanaRerankWriter().run(ctx)
    return conn


def _run(monkeypatch, seed, row_time=ROW_BASE):
    return _run_conn(monkeypatch, seed, row_time).updates


def _digest(updates) -> str:
    """Order-insensitive content digest, like output_digest.py (rows keyed by signal_id)."""
    canon = json.dumps(sorted(updates, key=lambda u: u[0]), sort_keys=True)
    return hashlib.sha256(canon.encode()).hexdigest()


def test_two_runs_with_identical_inputs_give_identical_payloads_and_digest(monkeypatch):
    first = _run(monkeypatch, seed=1)
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


def test_forced_bo_laksana_rebuild_that_re_mints_signal_computed_at_keeps_the_digest(monkeypatch):
    """bo_laksana stamps a fresh now() into bodha_msr_signals.computed_at on every run, and its own
    digest spec excludes that column. A forced rebuild with identical content must not flip the
    rerank digest."""
    before = _run(monkeypatch, seed=1, row_time=ROW_BASE)
    after = _run(monkeypatch, seed=1, row_time=ROW_BASE + timedelta(days=3, minutes=17))
    assert before and dict(before) == dict(after)
    assert _digest(before) == _digest(after)


def test_shuffled_fetch_order_does_not_change_payloads_digest_or_update_order(monkeypatch):
    runs = [_run(monkeypatch, seed=s) for s in (1, 2, 3, 4)]
    assert all(runs)
    for other in runs[1:]:
        assert dict(runs[0]) == dict(other)
        assert _digest(runs[0]) == _digest(other)
        assert [sid for sid, _ in other] == [sid for sid, _ in runs[0]]
    ids = [sid for sid, _ in runs[0]]
    assert ids == sorted(ids)


def test_computed_at_is_the_newest_l1_fact_time_in_utc_iso8601(monkeypatch):
    updates = dict(_run(monkeypatch, seed=1))
    for payload in updates.values():
        assert payload["computed_at"] == FACTS_AS_OF.isoformat()
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?\+00:00", payload["computed_at"])
        assert payload["formula_version"] == "structural_role_rerank_v1"


def test_payload_is_pure_in_its_inputs():
    c = _centrality_rows()[0]
    a = bl._rerank_payload(c, "Sun", "2026-10-06T15:37:03.340864+00:00")
    b = bl._rerank_payload(dict(c), "Sun", "2026-10-06T15:37:03.340864+00:00")
    assert a == b
    assert set(a) == {"structural_role_score", "primary_graha", "pagerank_score", "eigenvector_centrality",
                      "betweenness_centrality", "harmonic_centrality", "formula_version", "computed_at"}


def test_every_fetch_the_rerank_issues_carries_a_total_order_in_its_sql(monkeypatch):
    conn = _run_conn(monkeypatch, seed=1)
    by = lambda needle: [s for s in conn.sqls if needle in s]
    (sig,) = [s for s in conn.sqls if "FROM bodha_msr_signals" in s and "keyword_heuristic_v1" not in s]
    assert re.search(r"ORDER BY signal_id\s*$", sig.strip())
    (kw,) = by("valence_source = 'keyword_heuristic_v1'")
    assert re.search(r"ORDER BY signal_id\s*$", kw.strip())
    (vp,) = by("vichara_family = 'valence_pass'")
    assert re.search(r"ORDER BY actor, target, varga, value_text\s*$", vp.strip())
    (cen,) = by("FROM bodha_cgm_nodes")
    assert "ORDER BY node_subject, computed_at DESC NULLS LAST, node_id" in cen


def test_valence_pass_duplicate_key_resolves_to_the_last_value_text_in_order_by_order(monkeypatch):
    conn = _run_conn(monkeypatch, seed=7)
    assert conn.valence_updates, "fixture must exercise the PARK-#4 reclaim path"
    assert {(v, s) for _, v, s in conn.valence_updates} == {("malefic", "ga_vichara_v1")}
    # keyword-row UPDATEs are applied in signal_id order regardless of fetch order
    ids = [sid for sid, _, _ in conn.valence_updates]
    assert ids == sorted(ids)


def test_centrality_fetch_keeps_the_first_row_of_an_ordered_duplicate_subject():
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
    assert "ORDER BY node_subject, computed_at DESC NULLS LAST, node_id" in seen["sql"]
    assert out["Sun"]["pagerank_score"] == 1


def test_facts_as_of_query_is_a_max_scoped_to_this_chart_and_ayanamsha(monkeypatch):
    conn = _run_conn(monkeypatch, seed=1)
    (sql, params), = conn.facts_queries
    assert "max(computed_at)" in sql and "FROM chart_facts" in sql
    assert "chart_id = %s AND ayanamsha_id = %s" in sql
    assert params == [CHART, AYA]
    # the answer is this chart+ayanamsha's own newest time, not another ayanamsha's / chart's later row
    for payload in dict(conn.updates).values():
        assert payload["computed_at"] == FACTS_AS_OF.isoformat()


def test_fetch_facts_as_of_distinguishes_ayanamsha_and_chart():
    conn = _Conn(0)
    assert bl._fetch_facts_as_of(conn, CHART, AYA) == FACTS_AS_OF.isoformat()
    assert bl._fetch_facts_as_of(conn, CHART, OTHER_AYA) == (FACTS_AS_OF + timedelta(hours=5)).isoformat()
    assert bl._fetch_facts_as_of(conn, OTHER_CHART, AYA) == (FACTS_AS_OF + timedelta(days=30)).isoformat()


def test_no_l1_facts_falls_back_to_the_signal_row_time_and_keeps_the_key_valid(monkeypatch):
    monkeypatch.setattr(bl, "_fetch_facts_as_of", lambda *a, **k: None)
    updates = dict(_run(monkeypatch, seed=1))
    src = {r["signal_id"]: r["computed_at"] for r in _signal_rows()}
    assert updates
    for sid, payload in updates.items():
        assert payload["computed_at"] == src[sid].astimezone(timezone.utc).isoformat()
    # and the real helper returns None (not a crash) when max() finds no row
    assert bl._fetch_facts_as_of(_Conn(0), "no-such-chart", AYA) is None


def test_writer_has_no_wall_clock_or_row_time_in_digested_payload():
    import inspect
    src = inspect.getsource(bl.BoLaksanaRerankWriter.run)
    assert "datetime.now" not in src
    assert "_fetch_facts_as_of" in src


@__import__("pytest").fixture(autouse=True)
def _ayanamsha_scope_default(monkeypatch):
    """ONE_AYANAMSHA: this file's fake connections carry no `charts.build_ayanamshas` column, so the
    chart-scoped ayanamsha set is the default five. (The helper itself is tested in test_ayanamsha_scope.py.)"""
    from brahmagyan import ayanamsha_scope

    monkeypatch.setattr(ayanamsha_scope, "_column_present", lambda conn: False)
