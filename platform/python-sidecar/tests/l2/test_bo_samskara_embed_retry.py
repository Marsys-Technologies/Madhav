"""
tests/l2/test_bo_samskara_embed_retry.py -- bounded retry-with-backoff per embedding batch

S-L2 run 2 hardening: one transient Vertex error (429 / 5xx / timeout / connection reset)
must not abort a whole ayanamsha sub-step, but retries are bounded (5 attempts), re-send the
SAME batch content, never apply to auth / other-4xx / shape errors, and a batch that still
fails after the last attempt still raises "refusing a partial generation" with nothing
skipped and nothing written. No real sleep, no real API call (fakes only).
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline.orchestrator.writers import bo_samskara as mod
from pipeline.orchestrator.writers.bo_samskara import (
    BoSamskaraWriter,
    EMBED_BACKOFF_CAP_S,
    EMBED_MAX_ATTEMPTS,
    _backoff_delay,
    _embed_batch_with_retry,
    _is_transient_embed_error,
)
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


class FakeAPIError(Exception):
    """Mimics google.genai.errors.APIError: carries an int ``code``."""

    def __init__(self, code: int):
        super().__init__(f"api error {code}")
        self.code = code


def _vecs(texts):
    # deterministic function of the text so result identity can be compared
    return [[float(len(t)), float(sum(map(ord, t)) % 97)] + [0.0] * 766 for t in texts]


class Recorder:
    def __init__(self, script):
        self.script = list(script)   # exceptions to raise, then None = succeed
        self.calls: list[list[str]] = []

    def __call__(self, texts):
        self.calls.append(list(texts))
        step = self.script.pop(0) if self.script else None
        if step is not None:
            raise step
        return _vecs(texts)


class Sleeper:
    def __init__(self):
        self.delays: list[float] = []

    def __call__(self, d):
        self.delays.append(d)


def _mid():  # jitter-neutral random: rand()=0.5 -> factor exactly 1.0
    return 0.5


# ── predicate ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("code", [429, 500, 502, 503, 504, 599])
def test_transient_http_codes(code):
    assert _is_transient_embed_error(FakeAPIError(code)) is True


@pytest.mark.parametrize("code", [400, 401, 403, 404, 409, 422])
def test_non_transient_http_codes(code):
    assert _is_transient_embed_error(FakeAPIError(code)) is False


def test_transient_timeouts_and_resets():
    assert _is_transient_embed_error(TimeoutError("t")) is True
    assert _is_transient_embed_error(ConnectionResetError("r")) is True
    assert _is_transient_embed_error(ConnectionError("c")) is True

    class ReadTimeout(Exception):
        pass
    ReadTimeout.__module__ = "httpx"
    assert _is_transient_embed_error(ReadTimeout("x")) is True


def test_shape_and_unknown_errors_are_not_transient():
    for exc in (ValueError("shape"), KeyError("k"), TypeError("t"), RuntimeError("?"), Exception("?")):
        assert _is_transient_embed_error(exc) is False

    class ReadTimeout(Exception):   # same name, but NOT from httpx: unknown -> not transient
        pass
    assert _is_transient_embed_error(ReadTimeout("x")) is False


# ── backoff schedule ─────────────────────────────────────────────────────────

def test_backoff_schedule_is_1_2_4_8_capped_and_jitter_bounded():
    assert [_backoff_delay(n, _mid) for n in (1, 2, 3, 4)] == [1.0, 2.0, 4.0, 8.0]
    assert _backoff_delay(5, _mid) == 16.0
    assert _backoff_delay(9, _mid) == EMBED_BACKOFF_CAP_S  # capped
    for n in range(1, 10):
        base = min(EMBED_BACKOFF_CAP_S, 2 ** (n - 1))
        lo = _backoff_delay(n, lambda: 0.0)
        hi = _backoff_delay(n, lambda: 0.999999)
        assert lo == pytest.approx(base * 0.75)
        assert hi < base * 1.25 + 1e-6 and hi > base * 1.24


# ── retry behaviour ──────────────────────────────────────────────────────────

def test_transient_then_success_on_attempt_3_same_batch_and_identical_result():
    texts = ["alpha", "beta", "gamma"]
    clean = Recorder([])
    with patch.object(mod, "_embed_batch", clean):
        expected = _embed_batch_with_retry(texts, sleep=Sleeper(), rand=_mid)

    rec = Recorder([FakeAPIError(429), TimeoutError("slow")])
    sleeper = Sleeper()
    with patch.object(mod, "_embed_batch", rec):
        got = _embed_batch_with_retry(texts, sleep=sleeper, rand=_mid)

    assert got == expected
    assert len(rec.calls) == 3
    assert rec.calls == [texts, texts, texts]          # SAME content every attempt
    assert sleeper.delays == [1.0, 2.0]                # slept between attempts only


def test_five_transient_failures_raise_after_exactly_five_attempts():
    rec = Recorder([FakeAPIError(503)] * 5)
    sleeper = Sleeper()
    with patch.object(mod, "_embed_batch", rec):
        with pytest.raises(FakeAPIError):
            _embed_batch_with_retry(["x"], sleep=sleeper, rand=_mid)
    assert len(rec.calls) == EMBED_MAX_ATTEMPTS == 5
    assert sleeper.delays == [1.0, 2.0, 4.0, 8.0]      # 4 gaps, no sleep after the last attempt
    assert sum(sleeper.delays) <= 4 * 16 * 1.25        # bounded


@pytest.mark.parametrize("exc", [FakeAPIError(401), FakeAPIError(400), FakeAPIError(403),
                                 ValueError("bad shape")])
def test_non_transient_error_raises_immediately_without_retry(exc):
    rec = Recorder([exc])
    sleeper = Sleeper()
    with patch.object(mod, "_embed_batch", rec):
        with pytest.raises(type(exc)):
            _embed_batch_with_retry(["x"], sleep=sleeper, rand=_mid)
    assert len(rec.calls) == 1
    assert sleeper.delays == []


def test_default_hooks_are_module_level_and_patchable(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr(mod, "_retry_sleep", slept.append)
    monkeypatch.setattr(mod, "_retry_random", lambda: 0.5)
    rec = Recorder([FakeAPIError(500)])
    with patch.object(mod, "_embed_batch", rec):
        _embed_batch_with_retry(["x"])
    assert slept == [1.0]


# ── writer-level: refusal semantics unchanged ───────────────────────────────

def _ctx() -> ContextSpec:
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchall.return_value = []
    conn.cursor.return_value.__enter__ = MagicMock(return_value=cur)
    conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value = cur
    return ContextSpec(asset_id="bo_samskara", build_id="b1", db_conn=conn,
                       config={"chart_id": "00000000-0000-0000-0000-000000000001"})


def _signals(n):
    return [{"signal_id": f"s{i}", "signal_type_class": "c", "signal_tradition": "t",
             "signal_type_id": f"id{i}", "configuration_jsonb": {}, "domains_affected_array": []}
            for i in range(n)]


def _run(rec, n_signals, monkeypatch, inserted_capture):
    monkeypatch.setattr(mod, "_retry_sleep", lambda d: None)
    monkeypatch.setattr(mod, "_retry_random", lambda: 0.5)

    def fake_insert(conn, rows):
        inserted_capture.extend(rows)
        return len(rows)

    # unwrap the l2_producer contract wrapper: the test double conn has no contract SQL
    # (dry_run False + MagicMock conn -> wrapper's _contract_sql_enabled is False)
    with patch.object(mod, "_fetch_signals", return_value=_signals(n_signals)), \
         patch.object(mod, "_fetch_existing_embeddings", return_value={}), \
         patch.object(mod, "_embed_batch", rec), \
         patch.object(mod, "_batch_insert", side_effect=fake_insert), \
         patch("bodha_writers._idempotency.replace_prior_signal_embeddings", return_value=0):
        return BoSamskaraWriter().run_substep(_ctx(), SubStep(key="aya_raman", label="x"))


def test_writer_transient_then_success_equals_clean_run(monkeypatch):
    n = mod.EMBED_BATCH_SIZE + 7        # two batches
    clean_rows: list[dict] = []
    clean = _run(Recorder([]), n, monkeypatch, clean_rows)
    mod._TEXT_VEC["build_id"] = None            # the clean run's vectors must not satisfy the retry run
    mod._TEXT_VEC["vecs"] = {}

    rec = Recorder([None, FakeAPIError(429), FakeAPIError(502)])   # batch1 ok; batch2 fails twice
    retry_rows: list[dict] = []
    res = _run(rec, n, monkeypatch, retry_rows)

    assert res.rows_inserted == clean.rows_inserted == n
    strip = lambda rows: [{k: v for k, v in r.items() if k != "computed_at"} for r in rows]
    assert strip(retry_rows) == strip(clean_rows)
    assert rec.calls[1] == rec.calls[2] == rec.calls[3]            # batch 2 re-sent identically
    assert len(rec.calls) == 4


def test_writer_exhausted_retries_still_refuses_partial_generation(monkeypatch):
    rows: list[dict] = []
    rec = Recorder([FakeAPIError(503)] * 5)
    with pytest.raises(RuntimeError, match="refusing a partial generation") as ei:
        _run(rec, 3, monkeypatch, rows)
    assert isinstance(ei.value.__cause__, FakeAPIError)
    assert len(rec.calls) == 5
    assert rows == []                   # nothing written


def test_writer_non_transient_refuses_immediately(monkeypatch):
    rows: list[dict] = []
    rec = Recorder([FakeAPIError(403)])
    with pytest.raises(RuntimeError, match="refusing a partial generation"):
        _run(rec, 3, monkeypatch, rows)
    assert len(rec.calls) == 1
    assert rows == []
