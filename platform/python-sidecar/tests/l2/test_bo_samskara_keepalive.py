"""
tests/l2/test_bo_samskara_keepalive.py -- idle-in-transaction keepalive during embedding

Production run 2af5c8a2 (2026-10-08): bo_samskara crashed with
IdleInTransactionSessionTimeout at replace_prior_signal_embeddings of the 4th
ayanamsha because ctx.db_conn sat idle inside the orchestrator's open transaction
for the whole of ~254 sequential Vertex calls (~40 min vs the 30-min server limit).
Fix: a trivial ``SELECT 1`` on the SAME connection after each Vertex batch (and,
time-guarded, between retry attempts) so the idle clock resets. No commit, no
rollback, no new connection. Fakes only: no real sleep, no API call, no DB.
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

from pipeline.orchestrator.writers import bo_samskara as mod
from pipeline.orchestrator.writers.bo_samskara import BoSamskaraWriter
from pipeline.orchestrator.writers import ContextSpec, SubStep


@pytest.fixture(autouse=True)
def _reset_shared_text_vectors():
    """bo_samskara shares embedded vectors per build (input-text dedupe); these tests reuse one build_id
    and the same texts, so each test starts from an empty dict to keep counting Vertex calls."""
    mod._TEXT_VEC["build_id"] = None
    mod._TEXT_VEC["vecs"] = {}
    yield
    mod._TEXT_VEC["build_id"] = None
    mod._TEXT_VEC["vecs"] = {}


class Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class RecCursor:
    def __init__(self, conn):
        self.conn = conn
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.conn.events.append(("exec", self.conn.clock(), " ".join(str(sql).split())))
        return self

    def fetchall(self):
        return []


class RecConn:
    """Records every statement with the fake-clock time; forbids commit/rollback/close."""

    def __init__(self, clock):
        self.clock = clock
        self.events: list[tuple] = []

    def cursor(self):
        return RecCursor(self)

    def execute(self, sql, params=None):
        return RecCursor(self).execute(sql, params)

    def commit(self):
        raise AssertionError("writer must never commit ctx.db_conn")

    def rollback(self):
        raise AssertionError("writer must never rollback ctx.db_conn")

    def close(self):
        raise AssertionError("writer must never close ctx.db_conn")


def _signals(n):
    return [{"signal_id": f"s{i}", "signal_type_class": "c", "signal_tradition": "t",
             "signal_type_id": f"id{i}", "configuration_jsonb": {}, "domains_affected_array": []}
            for i in range(n)]


def _vecs(texts):
    return [[1.0] * 768 for _ in texts]


def _run(n_signals, per_call_s, monkeypatch, existing=None, embed=None):
    clock = Clock()
    conn = RecConn(clock)
    monkeypatch.setattr(mod, "_monotonic", clock)
    monkeypatch.setattr(mod, "_retry_sleep", lambda d: setattr(clock, "t", clock.t + d))
    monkeypatch.setattr(mod, "_retry_random", lambda: 0.5)
    calls: list[list[str]] = []

    def fake_embed(texts):
        calls.append(list(texts))
        if embed is not None:
            return embed(clock, texts)
        clock.t += per_call_s
        return _vecs(texts)

    def stamp(name):
        def _f(*a, **k):
            conn.events.append((name, clock(), name))
            return 0
        return _f

    inserted: list[dict] = []

    def fake_insert(c, rows):
        conn.events.append(("insert", clock(), "insert"))
        inserted.extend(rows)
        return len(rows)

    ctx = ContextSpec(asset_id="bo_samskara", build_id="b1", db_conn=conn,
                      config={"chart_id": "00000000-0000-0000-0000-000000000001"})
    with patch.object(mod, "_fetch_signals", return_value=_signals(n_signals)), \
         patch.object(mod, "_fetch_existing_embeddings", return_value=existing or {}), \
         patch.object(mod, "_embed_batch", fake_embed), \
         patch.object(mod, "_batch_insert", side_effect=fake_insert), \
         patch("bodha_writers._idempotency.replace_prior_signal_embeddings",
               side_effect=stamp("replace")):
        res = BoSamskaraWriter().run_substep(ctx, SubStep(key="aya_surya_siddhanta_classical", label="x"))
    return res, conn, calls, inserted


def _keepalive_times(conn):
    return [t for kind, t, sql in conn.events if kind == "exec" and sql == "SELECT 1"]


def test_keepalive_between_every_batch_and_before_first_db_write(monkeypatch):
    n = mod.EMBED_BATCH_SIZE * 5 + 3                      # 6 batches
    res, conn, calls, inserted = _run(n, 10.0, monkeypatch)
    assert len(calls) == 6 and res.rows_inserted == n
    ka = _keepalive_times(conn)
    assert len(ka) >= 6                                   # one after each Vertex batch
    # the last keepalive precedes replace_prior_signal_embeddings (the crash site)
    kinds = [k for k, _, _ in conn.events]
    assert kinds.index("replace") > max(i for i, e in enumerate(conn.events)
                                        if e[0] == "exec" and e[2] == "SELECT 1")


def test_gap_between_statements_never_exceeds_bound_with_slow_vertex(monkeypatch):
    # tonight's latency: ~10 s per 100-text call, 254 calls
    n = mod.EMBED_BATCH_SIZE * 254
    res, conn, calls, _ = _run(n, 10.0, monkeypatch)
    assert len(calls) == 254
    times = [0.0] + _keepalive_times(conn)
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert max(gaps) <= 60.0
    # and the tail (last batch -> replace) is also bounded
    replace_t = next(t for k, t, _ in conn.events if k == "replace")
    assert replace_t - times[-1] <= 60.0


def test_keepalive_during_long_retry_waits(monkeypatch):
    # one batch whose attempts each take 50 s (timeouts) before succeeding on the 4th
    state = {"n": 0}

    def embed(clock, texts):
        state["n"] += 1
        clock.t += 50.0
        if state["n"] < 4:
            raise TimeoutError("slow")
        return _vecs(texts)

    res, conn, calls, _ = _run(3, 0, monkeypatch, embed=embed)
    assert len(calls) == 4
    times = [0.0] + _keepalive_times(conn)
    gaps = [b - a for a, b in zip(times, times[1:])]
    assert max(gaps) <= 60.0


def test_keepalive_never_commits_rolls_back_or_closes(monkeypatch):
    # RecConn raises AssertionError on commit/rollback/close
    _run(mod.EMBED_BATCH_SIZE * 2, 5.0, monkeypatch)


def test_keepalive_failure_is_not_swallowed(monkeypatch):
    # a dead connection must surface (fail loud), not be hidden by the keepalive
    class Boom(RecConn):
        def cursor(self):
            raise RuntimeError("connection gone")

    clock = Clock()
    with pytest.raises(RuntimeError, match="connection gone"):
        mod._keepalive(Boom(clock))


def test_reuse_logic_untouched_unchanged_summaries_skip_vertex(monkeypatch):
    sigs = _signals(mod.EMBED_BATCH_SIZE + 5)
    existing = {}
    for s in sigs[:mod.EMBED_BATCH_SIZE]:               # first 100 unchanged
        existing[s["signal_id"]] = {
            "embedding_input_summary": mod._build_input_summary(s),
            "embedding_vec": "[" + ",".join(["0.5"] * 768) + "]",
            "embedding_model": mod.EMBEDDING_MODEL,
            "embedding_model_version": mod.EMBEDDING_VER,
        }
    res, conn, calls, inserted = _run(len(sigs), 10.0, monkeypatch, existing=existing)
    assert sum(len(c) for c in calls) == 5               # only the 5 new ones hit Vertex
    assert res.rows_inserted == len(sigs)
    reused = [r for r in inserted if r["embedding_vec"].startswith("[0.5")]
    assert len(reused) == mod.EMBED_BATCH_SIZE


def test_fully_reused_ayanamsha_makes_no_vertex_call_and_no_keepalive_needed(monkeypatch):
    sigs = _signals(10)
    existing = {s["signal_id"]: {
        "embedding_input_summary": mod._build_input_summary(s),
        "embedding_vec": "[0.1]", "embedding_model": mod.EMBEDDING_MODEL,
        "embedding_model_version": mod.EMBEDDING_VER} for s in sigs}
    res, conn, calls, _ = _run(10, 10.0, monkeypatch, existing=existing)
    assert calls == [] and res.rows_inserted == 10


def test_genai_client_is_built_with_bounded_http_timeout(monkeypatch):
    """A single hung Vertex call must be capped (google-genai defaults to timeout=None).

    google-genai is not installed in the CI sidecar env, so fake the modules.
    """
    import sys
    import types

    captured: dict = {}

    class FakeClient:
        def __init__(self, **kw):
            captured.update(kw)

    class FakeHttpOptions:
        def __init__(self, timeout=None):
            self.timeout = timeout

    fake_genai = types.ModuleType("google.genai")
    fake_genai.Client = FakeClient
    fake_types = types.ModuleType("google.genai.types")
    fake_types.HttpOptions = FakeHttpOptions
    fake_genai.types = fake_types
    fake_google = types.ModuleType("google")
    fake_google.genai = fake_genai
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)
    monkeypatch.setattr(mod, "_genai_client", None)
    mod._get_genai_client()
    monkeypatch.setattr(mod, "_genai_client", None)
    assert captured["vertexai"] is True
    assert captured["http_options"].timeout == mod.EMBED_HTTP_TIMEOUT_MS == 120_000
    # 5 attempts x 120 s + backoff (1+2+4+8) stays far below the 1800 s idle limit
    assert mod.EMBED_MAX_ATTEMPTS * mod.EMBED_HTTP_TIMEOUT_MS / 1000 + 15 < 1800
