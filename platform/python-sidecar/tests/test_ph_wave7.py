"""
test_ph_wave7.py — Wave 7: ph_phaladesa (B.11 + DETERMINISTIC-FIRST + model policy).

Covers:
  validate_narration_model: allowlist enforcement; Anthropic BANNED
  derive_phaladesa_record: all 7 domains produced; B.11 bodha_consulted flag
  narration_status always 'pending' from engine (writer never calls LLM)
  narration_model always None from engine
  PERMITTED_NARRATION_MODELS: no Anthropic prefix
  Anti-drift: writer never calls LLM, never sets narration_model
"""
from __future__ import annotations

import pytest

from services.ph_phaladesa.engine import (
    PERMITTED_NARRATION_MODELS,
    BANNED_MODEL_PREFIXES,
    DomainAnchorSummary,
    SpilloverSummary,
    BodhaSynthesisContext,
    PhaladesakContext,
    NarrationModelError,
    validate_narration_model,
    derive_phaladesa_record,
    derive_phaladesa_for_chart,
    _ALL_DOMAINS,
)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _ctx(**kwargs) -> PhaladesakContext:
    defaults = dict(
        chart_id='cid',
        domain_summaries={
            d: DomainAnchorSummary(
                domain=d,
                anchor_ids=['a1'],
                clean_ids=['a1'],
                top_anchor_id='a1',
                magnitude='major',
                confidence_high=0.55,
            )
            for d in _ALL_DOMAINS
        },
        spillovers=[],
        mitigation_domains={'career'},
        muhurta_domains={'career'},
        bodha=BodhaSynthesisContext(bodha_consulted=True, msr_domain_scores={'career': 0.70}),
    )
    defaults.update(kwargs)
    return PhaladesakContext(**defaults)


# ══════════════════════════════════════════════════════════════════════════════
# MODEL POLICY
# ══════════════════════════════════════════════════════════════════════════════

class TestNarrationModelPolicy:
    def test_none_always_valid(self):
        validate_narration_model(None)  # no exception

    @pytest.mark.parametrize("model", [
        'gemini-pro', 'gemini-ultra', 'gemini-2.0-flash',
        'deepseek-chat', 'deepseek-r1',
    ])
    def test_permitted_models_valid(self, model):
        validate_narration_model(model)  # no exception

    @pytest.mark.parametrize("banned", [
        'claude-3-5-sonnet-20241022', 'claude-opus-4-8',
        'claude-sonnet-4-6', 'claude-haiku-4-5',
        'anthropic/claude-3', 'claude2', 'claude3',
    ])
    def test_anthropic_models_banned(self, banned):
        with pytest.raises(NarrationModelError) as exc:
            validate_narration_model(banned)
        assert 'BANNED' in str(exc.value) or 'Anthropic' in str(exc.value)

    def test_permitted_set_has_no_anthropic_prefix(self):
        for model in PERMITTED_NARRATION_MODELS:
            for prefix in BANNED_MODEL_PREFIXES:
                assert not model.lower().startswith(prefix), \
                    f"PERMITTED_NARRATION_MODELS contains Anthropic model: {model}"

    def test_unknown_model_rejected(self):
        with pytest.raises(NarrationModelError):
            validate_narration_model('some-random-model-2026')

    def test_openai_models_not_in_allowlist(self):
        """SUDDHA-VACA Phase C §2 authorization: the file's own documented policy
        ('Model policy allowlist (Gemini/DeepSeek only)') must actually hold —
        gpt-4o/gpt-4-turbo (OpenAI) do not belong in PERMITTED_NARRATION_MODELS
        regardless of vendor, per this file's own stated intent."""
        assert 'gpt-4o' not in PERMITTED_NARRATION_MODELS
        assert 'gpt-4-turbo' not in PERMITTED_NARRATION_MODELS
        # gemini/deepseek entries remain
        for model in ('gemini-pro', 'gemini-ultra', 'gemini-2.0-flash',
                      'deepseek-chat', 'deepseek-r1'):
            assert model in PERMITTED_NARRATION_MODELS

    def test_openai_models_rejected_by_validator(self):
        with pytest.raises(NarrationModelError):
            validate_narration_model('gpt-4o')
        with pytest.raises(NarrationModelError):
            validate_narration_model('gpt-4-turbo')


# ══════════════════════════════════════════════════════════════════════════════
# DERIVE PHALADESA RECORD
# ══════════════════════════════════════════════════════════════════════════════

class TestDerivePhaladeskRecord:
    def test_narration_status_always_pending(self):
        ctx = _ctx()
        rec = derive_phaladesa_record('career', ctx)
        assert rec.narration_status == 'pending'

    def test_narration_model_always_none(self):
        ctx = _ctx()
        rec = derive_phaladesa_record('career', ctx)
        assert rec.narration_model is None, "Engine must never set narration_model (writer does not call LLM)"

    def test_b11_consulted_flag_in_derivation_summary(self):
        ctx = _ctx()
        rec = derive_phaladesa_record('career', ctx)
        assert rec.derivation_summary_jsonb.get('b11_bodha_consulted') is True

    def test_mitigation_available_for_covered_domain(self):
        ctx = _ctx(mitigation_domains={'career'})
        rec = derive_phaladesa_record('career', ctx)
        assert rec.mitigation_available is True

    def test_mitigation_not_available_for_uncovered(self):
        ctx = _ctx(mitigation_domains={'financial'})
        rec = derive_phaladesa_record('career', ctx)
        assert rec.mitigation_available is False

    def test_spillover_domains_populated(self):
        spillovers = [
            SpilloverSummary('career', 'health', 'contagion', 0.45),
        ]
        ctx = _ctx(spillovers=spillovers)
        rec = derive_phaladesa_record('career', ctx)
        assert rec.spillover_domains_jsonb is not None
        assert any(s['target_domain'] == 'health' for s in rec.spillover_domains_jsonb)

    def test_incoming_spillover_counted(self):
        spillovers = [SpilloverSummary('financial', 'career', 'contagion', 0.40)]
        ctx = _ctx(spillovers=spillovers)
        rec = derive_phaladesa_record('career', ctx)
        assert rec.incoming_spillover_count == 1

    def test_model_policy_in_derivation_ledger(self):
        ctx = _ctx()
        rec = derive_phaladesa_record('career', ctx)
        ledger_text = str(rec.derivation_ledger_jsonb).lower()
        assert 'anthropic' in ledger_text or 'banned' in ledger_text


# ══════════════════════════════════════════════════════════════════════════════
# DERIVE FOR CHART
# ══════════════════════════════════════════════════════════════════════════════

class TestDerivePhaladeskForChart:
    def test_produces_7_records(self):
        ctx = _ctx()
        recs = derive_phaladesa_for_chart(ctx)
        assert len(recs) == 7

    def test_all_domains_present(self):
        ctx = _ctx()
        recs = derive_phaladesa_for_chart(ctx)
        domains = {r.domain for r in recs}
        assert domains == set(_ALL_DOMAINS)

    def test_all_narration_statuses_pending(self):
        ctx = _ctx()
        recs = derive_phaladesa_for_chart(ctx)
        for r in recs:
            assert r.narration_status == 'pending'

    def test_all_narration_models_none(self):
        ctx = _ctx()
        recs = derive_phaladesa_for_chart(ctx)
        for r in recs:
            assert r.narration_model is None

    def test_empty_domain_summaries_still_7_records(self):
        ctx = PhaladesakContext(chart_id='cid')
        recs = derive_phaladesa_for_chart(ctx)
        assert len(recs) == 7

    def test_b11_miss_logged_in_summary(self):
        ctx = PhaladesakContext(
            chart_id='cid',
            bodha=BodhaSynthesisContext(bodha_consulted=False),
        )
        recs = derive_phaladesa_for_chart(ctx)
        for r in recs:
            assert r.derivation_summary_jsonb.get('b11_bodha_consulted') is False


# ══════════════════════════════════════════════════════════════════════════════
# ANTI-DRIFT
# ══════════════════════════════════════════════════════════════════════════════

class TestPhaladeskAntiDrift:
    def test_writer_never_commits(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_phaladesa.py'
        )
        with open(path) as f:
            src = f.read()
        code_lines = [ln for ln in src.splitlines()
                      if not ln.strip().startswith('#') and '"""' not in ln]
        assert '.commit()' not in '\n'.join(code_lines)

    def test_writer_only_writes_phala_phaladesa(self):
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_phaladesa.py'
        )
        with open(path) as f:
            src = f.read()
        assert 'INSERT INTO phala_phaladesa' in src
        assert 'INSERT INTO phala_anchors' not in src

    def test_writer_does_not_call_any_llm(self):
        """Writer must not import openai, anthropic, google.generativeai etc."""
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_phaladesa.py'
        )
        with open(path) as f:
            src = f.read()
        for banned_import in ['anthropic', 'openai', 'google.generativeai', 'requests.post']:
            assert banned_import not in src, \
                f"Writer must not call LLMs directly: found '{banned_import}'"

    def test_writer_inserts_null_narration_model(self):
        """Writer INSERT must explicitly use NULL for narration_model."""
        import os
        path = os.path.join(
            os.path.dirname(__file__), '..', 'pipeline', 'orchestrator', 'writers', 'ph_phaladesa.py'
        )
        with open(path) as f:
            src = f.read()
        # The VALUES clause must pass a LITERAL NULL for narration_model — never a %s
        # param that could carry a (possibly banned) model. WP-2.2/LCA-5 made narration
        # deterministic: column order (narration_status, narration_model, narration_jsonb)
        # → VALUES (%s, NULL, %s::jsonb), so narration_model stays the literal NULL.
        assert (
            '%s, NULL, %s::jsonb' in src          # current deterministic form
            or 'NULL, NULL' in src                # legacy double-NULL form
            or ', NULL, NULL,' in src
        )

    def test_migration_narration_model_check_excludes_anthropic(self):
        """DB CHECK values for narration_model must contain no Anthropic model IDs."""
        import os, re
        path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'supabase', 'migrations', '339_phala_phaladesa.sql'
        )
        with open(path) as f:
            src = f.read()
        # Strip SQL line comments (-- ...) before scanning
        src_no_comments = re.sub(r'--[^\n]*', '', src).lower()
        # Find the IN (...) body of the narration_model CHECK constraint
        check_match = re.search(r'narration_model\s+text\s+check\s*\(.*?in\s*\((.*?)\)\s*\)', src_no_comments, re.DOTALL)
        check_body = check_match.group(1) if check_match else ''
        assert 'claude-' not in check_body, \
            "DB CHECK must not list any claude-* model ID"
        assert 'anthropic' not in check_body, \
            "DB CHECK must not list any Anthropic model"
