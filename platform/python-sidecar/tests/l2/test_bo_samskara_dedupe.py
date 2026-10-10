"""
tests/l2/test_bo_samskara_dedupe.py -- one Vertex call per DISTINCT input text.

Design: POST/EMBEDDING_CACHE_DESIGN.md (SS N-295). On chart 482012f1 the 126,918 embeddings come from only
4,379 distinct input texts (the summary holds neither the signal_id nor the ayanamsha). bo_samskara used to
send every non-reused text to Vertex; it now sends each distinct text once and fans the stored vector literal
out to every signal sharing it, sharing the dict across the ayanamsha substeps of one build.

Fakes only: no Vertex call, no DB.
"""
from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from pipeline.orchestrator.writers import bo_samskara as mod
from pipeline.orchestrator.writers.bo_samskara import BoSamskaraWriter
from pipeline.orchestrator.writers import ContextSpec, SubStep

CHART = "482012f1-710e-4a25-994a-93821f5871aa"


def _sig(i: int, text_key: int, aya: str = "lahiri_chitrapaksha") -> dict:
    """A signal whose input summary depends only on text_key (so many signals can share one text)."""
    return {
        "signal_id": f"SIG.{aya}.{i:05d}",
        "ayanamsha_id": aya,
        "signal_type_class": "composite_state",
        "signal_tradition": "parashari",
        "signal_type_id": f"type_{text_key}",
        "configuration_jsonb": {"fact_key": f"k{text_key}"},
        "domains_affected_array": ["career"],
    }


class FakeVertex:
    """Deterministic fake: the vector is a pure function of the text; records every text sent."""

    def __init__(self):
        self.calls: list[list[str]] = []

    @staticmethod
    def vec_for(text: str) -> list[float]:
        rnd = random.Random(text)
        return [rnd.random() for _ in range(8)]

    def __call__(self, texts, on_wait=None):
        self.calls.append(list(texts))
        return [self.vec_for(t) for t in texts]

    @property
    def sent(self) -> list[str]:
        return [t for c in self.calls for t in c]


class Conn:
    def execute(self, *a, **k):
        return self

    def cursor(self):
        raise AssertionError("cursor not expected in these tests (inserts are patched)")


def _run(aya: str, signals: list[dict], fake: FakeVertex, *, existing=None, build_id="B1", captured=None):
    ctx = ContextSpec(asset_id="bo_samskara", build_id=build_id, db_conn=Conn(), config={"chart_id": CHART})
    step = SubStep(key=f"aya_{aya}", label="x")

    def fake_insert(conn, rows):
        if captured is not None:
            captured.extend(rows)
        return len(rows)

    with patch.object(mod, "_fetch_signals", lambda conn, c, a: signals), \
         patch.object(mod, "_fetch_existing_embeddings", lambda conn, c, a: existing or {}), \
         patch.object(mod, "_embed_batch_with_retry", fake), \
         patch.object(mod, "_batch_insert", fake_insert), \
         patch.object(mod, "_keepalive", lambda conn: None), \
         patch("bodha_writers._idempotency.replace_prior_signal_embeddings", lambda conn, c, a: None):
        return BoSamskaraWriter().run_substep(ctx, step)


@pytest.fixture(autouse=True)
def _fresh_shared_dict():
    mod._TEXT_VEC["build_id"] = None
    mod._TEXT_VEC["vecs"] = {}
    yield
    mod._TEXT_VEC["build_id"] = None
    mod._TEXT_VEC["vecs"] = {}


def test_duplicate_texts_cost_one_call_each_and_every_signal_gets_its_vector():
    # 12 signals, 3 distinct texts
    sigs = [_sig(i, i % 3) for i in range(12)]
    fake, rows = FakeVertex(), []
    res = _run("lahiri_chitrapaksha", sigs, fake, captured=rows)
    assert res.rows_inserted == 12
    assert len(fake.sent) == 3 and len(set(fake.sent)) == 3          # one per distinct text
    assert len(rows) == 12
    for r in rows:
        assert r["embedding_vec"] == mod._vec_literal(FakeVertex.vec_for(r["embedding_input_summary"]))


def test_identical_texts_get_identical_vectors_across_signals():
    sigs = [_sig(i, 7) for i in range(5)]
    rows = []
    _run("lahiri_chitrapaksha", sigs, FakeVertex(), captured=rows)
    assert len({r["embedding_vec"] for r in rows}) == 1
    assert len({r["signal_id"] for r in rows}) == 5                   # still one row per signal


def test_rows_are_in_signal_order_with_the_same_columns_as_before():
    sigs = [_sig(i, i % 4) for i in range(10)]
    rows = []
    _run("lahiri_chitrapaksha", sigs, FakeVertex(), captured=rows)
    assert [r["signal_id"] for r in rows] == [s["signal_id"] for s in sigs]
    assert set(rows[0]) == set(mod._COLS)


def test_result_is_independent_of_signal_order():
    sigs = [_sig(i, i % 5) for i in range(40)]
    shuffled = sigs[:]
    random.Random(1).shuffle(shuffled)
    a, b = [], []
    _run("lahiri_chitrapaksha", sigs, FakeVertex(), captured=a, build_id="BA")
    _run("lahiri_chitrapaksha", shuffled, FakeVertex(), captured=b, build_id="BB")
    by_a = {r["signal_id"]: r["embedding_vec"] for r in a}
    by_b = {r["signal_id"]: r["embedding_vec"] for r in b}
    assert by_a == by_b


def test_second_ayanamsha_in_the_same_build_reuses_the_shared_dict_and_sends_nothing_new():
    fake = FakeVertex()
    _run("lahiri_chitrapaksha", [_sig(i, i % 3, "lahiri_chitrapaksha") for i in range(9)], fake, build_id="B1")
    assert len(fake.sent) == 3
    rows = []
    _run("raman", [_sig(i, i % 3, "raman") for i in range(9)], fake, build_id="B1", captured=rows)
    assert len(fake.sent) == 3                                        # no extra Vertex call
    assert len(rows) == 9 and all(r["ayanamsha_id"] == "raman" for r in rows)
    assert all(r["embedding_vec"] == mod._vec_literal(FakeVertex.vec_for(r["embedding_input_summary"]))
               for r in rows)


def test_a_new_build_does_not_trust_the_previous_builds_dict():
    fake = FakeVertex()
    _run("raman", [_sig(i, i % 2, "raman") for i in range(6)], fake, build_id="B1")
    _run("raman", [_sig(i, i % 2, "raman") for i in range(6)], fake, build_id="B2")
    assert len(fake.sent) == 4                                        # 2 distinct texts per build


def test_signal_id_reuse_stays_the_first_lookup_and_reused_texts_are_not_sent():
    sigs = [_sig(i, i % 3) for i in range(6)]
    texts = [mod._build_input_summary(s) for s in sigs]
    existing = {
        str(sigs[0]["signal_id"]): {
            "embedding_input_summary": texts[0],
            "embedding_vec": "[1,2,3]",
            "embedding_model": mod.EMBEDDING_MODEL,
            "embedding_model_version": mod.EMBEDDING_VER,
        }
    }
    fake, rows = FakeVertex(), []
    _run("lahiri_chitrapaksha", sigs, fake, existing=existing, captured=rows)
    by_sig = {r["signal_id"]: r for r in rows}
    assert by_sig[sigs[0]["signal_id"]]["embedding_vec"] == "[1,2,3]"       # reused as before
    # signal 3 shares signal 0's text but has no stored row of its own: it is embedded (once per distinct text)
    assert len(fake.sent) == 3


def test_a_short_vertex_answer_refuses_a_partial_generation():
    sigs = [_sig(i, i) for i in range(4)]

    def short(texts, on_wait=None):
        return [FakeVertex.vec_for(t) for t in texts][:-1]

    with pytest.raises(RuntimeError, match="partial generation"):
        _run("lahiri_chitrapaksha", sigs, short)


def test_a_vertex_failure_still_refuses_a_partial_generation():
    def boom(texts, on_wait=None):
        raise ValueError("quota")

    with pytest.raises(RuntimeError, match="refusing a partial generation"):
        _run("lahiri_chitrapaksha", [_sig(0, 0)], boom)


def test_no_connection_control_is_used():
    class Strict(Conn):
        def commit(self):
            raise AssertionError("never commit ctx.db_conn")

        def rollback(self):
            raise AssertionError("never rollback ctx.db_conn")

        def close(self):
            raise AssertionError("never close ctx.db_conn")

    ctx = ContextSpec(asset_id="bo_samskara", build_id="B9", db_conn=Strict(), config={"chart_id": CHART})
    with patch.object(mod, "_fetch_signals", lambda conn, c, a: [_sig(0, 0)]), \
         patch.object(mod, "_fetch_existing_embeddings", lambda conn, c, a: {}), \
         patch.object(mod, "_embed_batch_with_retry", FakeVertex()), \
         patch.object(mod, "_batch_insert", lambda conn, rows: len(rows)), \
         patch.object(mod, "_keepalive", lambda conn: None), \
         patch("bodha_writers._idempotency.replace_prior_signal_embeddings", lambda conn, c, a: None):
        BoSamskaraWriter().run_substep(ctx, SubStep(key="aya_raman", label="x"))


def test_overflow_beyond_the_cap_keeps_every_signal_correct_and_still_one_call_per_text():
    sigs = [_sig(i, i % 6) for i in range(18)]                       # 6 distinct texts
    fake, rows = FakeVertex(), []
    with patch.object(mod, "_TEXT_VEC_MAX", 2):                      # shared dict holds only 2 vectors
        _run("lahiri_chitrapaksha", sigs, fake, captured=rows)
    assert len(fake.sent) == 6 and len(set(fake.sent)) == 6
    assert len(rows) == 18
    assert all(r["embedding_vec"] == mod._vec_literal(FakeVertex.vec_for(r["embedding_input_summary"]))
               for r in rows)
    assert len(mod._TEXT_VEC["vecs"]) <= 2


def test_shared_dict_is_keyed_on_model_version_and_text():
    _run("lahiri_chitrapaksha", [_sig(0, 0)], FakeVertex())
    keys = list(mod._TEXT_VEC["vecs"])
    assert keys and all(k[:2] == (mod.EMBEDDING_MODEL, mod.EMBEDDING_VER) for k in keys)


def test_shared_dict_is_released_after_the_last_ayanamsha_substep():
    last = mod.CANONICAL_AYAS[-1]
    _run(mod.CANONICAL_AYAS[0], [_sig(0, 0, mod.CANONICAL_AYAS[0])], FakeVertex(), build_id="B7")
    assert mod._TEXT_VEC["vecs"]                                     # kept for the following substeps
    _run(last, [_sig(0, 0, last)], FakeVertex(), build_id="B7")
    assert mod._TEXT_VEC["vecs"] == {}
