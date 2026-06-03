"""
test_bo_2_7.py — Unit tests for brahmagyan.bodha.bo_2-7 (BO-2-7 bodha.embeddings).

Tests are offline (no Vertex AI, no DB). They verify:

1. _signal_text() — correct embedding text composition
2. _signal_text() — truncation at 400 chars for claim_text
3. Acceptance-gate logic — ac1/ac2/ac3 pass/fail shapes
4. embed_signals() — raises RuntimeError on empty signal list
5. _embed_batch mock — result shape is 768-dim

Acceptance criteria verified:
  - AC1: >= 5 embeddings present (gate logic verified via unit)
  - AC2: cosine self-search returns same signal_id (gate logic verified via unit)
  - AC3: HNSW index present (gate logic verified via unit)
"""
from __future__ import annotations

import sys
import types
import importlib
from unittest.mock import MagicMock, patch, call
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_signal(
    signal_id: str = "SIG.MSR.001",
    domain: str = "career",
    valence: str = "positive",
    claim_text: str = "Strong 10th lord in angle.",
    source_citation: str | None = "FORENSIC:P10",
) -> dict:
    return {
        "signal_id": signal_id,
        "domain": domain,
        "valence": valence,
        "claim_text": claim_text,
        "source_citation": source_citation,
    }


# ── Import the module under test (with external deps stubbed) ─────────────────
#
# bo_2-7.py uses:
#   - vertexai (stubbed)
#   - psycopg  (stubbed)
#   - pgvector (stubbed)
#   - numpy    (real — available in test env)
#
# We stub the cloud/DB deps at import time using sys.modules patching.

@pytest.fixture(scope="session", autouse=True)
def stub_cloud_deps():
    """Stub vertexai, psycopg, and pgvector so the module imports cleanly offline."""

    # ── vertexai stub ──────────────────────────────────────────────────────────
    vertexai_mod = types.ModuleType("vertexai")
    vertexai_mod.init = MagicMock()  # type: ignore[attr-defined]

    lm_mod = types.ModuleType("vertexai.language_models")
    lm_mod.TextEmbeddingInput = MagicMock()  # type: ignore[attr-defined]
    lm_mod.TextEmbeddingModel = MagicMock()  # type: ignore[attr-defined]

    # ── psycopg stub ───────────────────────────────────────────────────────────
    psycopg_mod = types.ModuleType("psycopg")
    psycopg_mod.connect = MagicMock()  # type: ignore[attr-defined]

    # ── pgvector.psycopg stub ──────────────────────────────────────────────────
    pgvector_mod = types.ModuleType("pgvector")
    pgvector_psycopg_mod = types.ModuleType("pgvector.psycopg")
    pgvector_psycopg_mod.register_vector = MagicMock()  # type: ignore[attr-defined]

    sys.modules["vertexai"] = vertexai_mod
    sys.modules["vertexai.language_models"] = lm_mod
    sys.modules["psycopg"] = psycopg_mod
    sys.modules["pgvector"] = pgvector_mod
    sys.modules["pgvector.psycopg"] = pgvector_psycopg_mod

    # ── dotenv stub ────────────────────────────────────────────────────────────
    dotenv_mod = types.ModuleType("dotenv")
    dotenv_mod.load_dotenv = MagicMock()  # type: ignore[attr-defined]
    sys.modules["dotenv"] = dotenv_mod

    yield

    # Cleanup
    for key in ["vertexai", "vertexai.language_models", "psycopg",
                "pgvector", "pgvector.psycopg", "dotenv"]:
        sys.modules.pop(key, None)


@pytest.fixture(scope="session")
def bo27():
    """Import the bo_2-7 module after stubs are in place."""
    import importlib.util
    import pathlib

    path = pathlib.Path(__file__).parent.parent / "bo_2-7.py"
    spec = importlib.util.spec_from_file_location("bo_2_7", path)
    assert spec is not None and spec.loader is not None, "Cannot load bo_2-7.py"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# ── Tests: _signal_text ───────────────────────────────────────────────────────


class TestSignalText:
    def test_basic_format(self, bo27):
        """Embedding text is domain | valence | claim_text."""
        sig = _make_signal(domain="career", valence="positive", claim_text="Strong 10th lord.")
        result = bo27._signal_text(sig)
        assert result == "career | positive | Strong 10th lord."

    def test_missing_valence_defaults_to_neutral(self, bo27):
        """None valence → 'neutral' in text."""
        sig = _make_signal(valence=None)
        result = bo27._signal_text(sig)
        assert "| neutral |" in result

    def test_missing_domain_defaults_to_unknown_domain(self, bo27):
        """None domain → 'unknown_domain' in text."""
        sig = _make_signal(domain=None)
        result = bo27._signal_text(sig)
        assert result.startswith("unknown_domain |")

    def test_claim_text_truncated_at_400_chars(self, bo27):
        """claim_text is capped at 400 characters."""
        long_claim = "x" * 500
        sig = _make_signal(claim_text=long_claim)
        result = bo27._signal_text(sig)
        # The part after the second " | " should be at most 400 chars
        parts = result.split(" | ", 2)
        assert len(parts[2]) == 400

    def test_empty_claim_text(self, bo27):
        """Empty claim_text is allowed (edge case)."""
        sig = _make_signal(claim_text="")
        result = bo27._signal_text(sig)
        assert result.endswith("| ")

    def test_native_signal_format(self, bo27):
        """Spot-check with a realistic native signal."""
        sig = _make_signal(
            signal_id="SIG.MSR.042",
            domain="career",
            valence="positive",
            claim_text="10th lord Saturn in 10th house (Capricorn) — yoga for career authority.",
            source_citation="FORENSIC:P10",
        )
        text = bo27._signal_text(sig)
        assert text.startswith("career | positive | 10th lord Saturn")


# ── Tests: embed_signals raises on empty DB ───────────────────────────────────


class TestEmbedSignalsEdgeCases:
    def test_raises_on_empty_signals(self, bo27):
        """embed_signals() raises RuntimeError when msr_signals is empty."""
        with patch.object(bo27, "_fetch_signals", return_value=[]):
            with patch.object(bo27, "_init_vertexai"):
                with pytest.raises(RuntimeError, match="\\[STOP\\]"):
                    bo27.embed_signals()

    def test_skips_already_embedded_by_default(self, bo27):
        """Signals already in bodha_signal_embeddings are not re-embedded."""
        sigs = [_make_signal(f"SIG.MSR.{i:03d}") for i in range(10)]
        already = {s["signal_id"] for s in sigs[:7]}  # 7 already done

        with patch.object(bo27, "_fetch_signals", return_value=sigs), \
             patch.object(bo27, "_fetch_already_embedded", return_value=already), \
             patch.object(bo27, "_embed_batch", return_value=[[0.0] * 768] * 3) as mock_embed, \
             patch.object(bo27, "_upsert_embeddings") as mock_upsert, \
             patch.object(bo27, "_ensure_hnsw_index", return_value=True), \
             patch.object(bo27, "_init_vertexai"):
            result = bo27.embed_signals(force=False)

        # Only 3 signals should have been embedded (10 - 7 already done)
        total_embedded_in_calls = sum(
            len(c.args[0]) for c in mock_upsert.call_args_list
        )
        assert total_embedded_in_calls == 3
        assert result["newly_embedded"] == 3

    def test_force_re_embeds_all(self, bo27):
        """With force=True, all signals are re-embedded regardless of prior state."""
        sigs = [_make_signal(f"SIG.MSR.{i:03d}") for i in range(5)]

        with patch.object(bo27, "_fetch_signals", return_value=sigs), \
             patch.object(bo27, "_fetch_already_embedded") as mock_already, \
             patch.object(bo27, "_embed_batch", return_value=[[0.0] * 768] * 5), \
             patch.object(bo27, "_upsert_embeddings"), \
             patch.object(bo27, "_ensure_hnsw_index", return_value=True), \
             patch.object(bo27, "_init_vertexai"):
            bo27.embed_signals(force=True)

        # _fetch_already_embedded must NOT be called when force=True
        mock_already.assert_not_called()

    def test_raises_when_hnsw_index_fails(self, bo27):
        """RuntimeError raised if HNSW index creation fails."""
        sigs = [_make_signal(f"SIG.MSR.{i:03d}") for i in range(5)]

        with patch.object(bo27, "_fetch_signals", return_value=sigs), \
             patch.object(bo27, "_fetch_already_embedded", return_value=set()), \
             patch.object(bo27, "_embed_batch", return_value=[[0.0] * 768] * 5), \
             patch.object(bo27, "_upsert_embeddings"), \
             patch.object(bo27, "_ensure_hnsw_index", return_value=False), \
             patch.object(bo27, "_init_vertexai"):
            with pytest.raises(RuntimeError, match="HNSW index creation failed"):
                bo27.embed_signals()


# ── Tests: run_self_test gate logic ──────────────────────────────────────────


class TestSelfTestGates:
    def _make_mock_conn_context(self, fetchone_side_effects):
        """Build a context-manager mock for psycopg.connect producing multiple fetchone results."""
        conn = MagicMock()
        execute_mock = MagicMock()
        conn.execute.return_value = execute_mock
        execute_mock.fetchone.side_effect = fetchone_side_effects
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        return conn

    def test_ac1_fails_when_fewer_than_5_embeddings(self, bo27):
        """AC1 fails when fewer than SELF_TEST_MIN_SIGNALS embeddings are present."""
        # count=3 is >0 so AC2 probe branch still runs but probe_row returns None → ac2_pass=False
        # We need 3 connect calls: COUNT, probe row, HNSW check
        with patch.object(bo27, "_db_url", return_value="postgresql://mock"), \
             patch("psycopg.connect") as mock_connect, \
             patch("pgvector.psycopg.register_vector"), \
             patch.object(bo27, "_cosine_self_search", return_value="SIG.MSR.001"):

            # First connect call: COUNT(*) = 3 (< 5; but >0 so ac2 probe attempted)
            conn1 = self._make_mock_conn_context([(3,)])
            # Second connect (probe row → None, no row returned)
            conn2 = self._make_mock_conn_context([None])
            # Third connect (HNSW check)
            conn3 = self._make_mock_conn_context([("idx_hnsw",)])

            mock_connect.side_effect = [conn1, conn2, conn3]

            result = bo27.run_self_test()

        assert result["ac1_min_embeddings"]["pass"] is False
        assert result["ac1_min_embeddings"]["count"] == 3

    def test_ac2_fails_when_self_search_returns_wrong_id(self, bo27):
        """AC2 fails when cosine self-search top-1 != probe signal_id."""
        import numpy as np

        with patch.object(bo27, "_db_url", return_value="postgresql://mock"), \
             patch("psycopg.connect") as mock_connect, \
             patch("pgvector.psycopg.register_vector"):

            fake_vec = list(np.zeros(768, dtype=float))

            # First call: COUNT(*) = 10
            conn1 = self._make_mock_conn_context([(10,)])
            # Second call: probe row (signal_id, embedding)
            conn2 = self._make_mock_conn_context([("SIG.MSR.001", fake_vec)])
            # Third call: cosine search returns wrong id
            conn3 = self._make_mock_conn_context([("SIG.MSR.999",)])
            # Fourth call: HNSW check
            conn4 = self._make_mock_conn_context([("idx_hnsw",)])

            mock_connect.side_effect = [conn1, conn2, conn3, conn4]

            result = bo27.run_self_test()

        assert result["ac2_cosine_self_search"]["pass"] is False

    def test_ac3_fails_when_hnsw_absent(self, bo27):
        """AC3 fails when HNSW index not found in pg_indexes."""
        with patch.object(bo27, "_db_url", return_value="postgresql://mock"), \
             patch("psycopg.connect") as mock_connect, \
             patch("pgvector.psycopg.register_vector"), \
             patch.object(bo27, "_cosine_self_search", return_value="SIG.MSR.001"):

            # COUNT(*) = 0 (< 5) so ac2 probe not attempted
            conn1 = self._make_mock_conn_context([(0,)])
            # HNSW check → None
            conn2 = self._make_mock_conn_context([None])

            mock_connect.side_effect = [conn1, conn2]

            result = bo27.run_self_test()

        assert result["ac3_hnsw_index"]["pass"] is False
        assert result["overall_pass"] is False

    def test_overall_pass_requires_all_three_gates(self, bo27):
        """overall_pass is True only when all three gates pass."""
        import numpy as np

        with patch.object(bo27, "_db_url", return_value="postgresql://mock"), \
             patch("psycopg.connect") as mock_connect, \
             patch("pgvector.psycopg.register_vector"):

            fake_vec = list(np.zeros(768, dtype=float))

            # COUNT(*) = 10
            conn1 = self._make_mock_conn_context([(10,)])
            # probe row
            conn2 = self._make_mock_conn_context([("SIG.MSR.001", fake_vec)])
            # cosine search → same id
            conn3 = self._make_mock_conn_context([("SIG.MSR.001",)])
            # HNSW index → found
            conn4 = self._make_mock_conn_context([("idx_bodha_signal_embeddings_hnsw",)])

            mock_connect.side_effect = [conn1, conn2, conn3, conn4]

            result = bo27.run_self_test()

        assert result["overall_pass"] is True
        assert result["ac1_min_embeddings"]["pass"] is True
        assert result["ac2_cosine_self_search"]["pass"] is True
        assert result["ac3_hnsw_index"]["pass"] is True


# ── Tests: EMBED_DIM and model constants ──────────────────────────────────────


class TestConstants:
    def test_embed_dim_is_768(self, bo27):
        assert bo27.EMBED_DIM == 768

    def test_embed_model_is_text_multilingual(self, bo27):
        assert bo27.EMBED_MODEL == "text-multilingual-embedding-002"

    def test_target_table(self, bo27):
        assert bo27.TARGET_TABLE == "bodha_signal_embeddings"

    def test_min_signals_for_self_test(self, bo27):
        assert bo27.SELF_TEST_MIN_SIGNALS >= 5
