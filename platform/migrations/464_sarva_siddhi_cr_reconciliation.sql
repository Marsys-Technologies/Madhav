-- Migration 464: Vidhi registry seed — SARVA-SIDDHI register-reconciliation (4 stale-closed CRs)
-- Created: 2026-07-24
--
-- Follows migration 463 (VIDHI-PŪRṆATĀ Opus-Gate follow-up). The SARVA-SIDDHI register-
-- reconciliation lane's W-0 truth-pass confirmed four CRs are STALE-CLOSED — shipped and live
-- in code, but the register (this DB seed, the "third copy") never caught up. This migration
-- carries the DB-seed side of all four fixes into lockstep with
-- platform/src/lib/vidhi/registry_data.ts (the canonical source, already corrected):
--
--   CR-16 (special_lagna_read) — known_gap: 'CR-16' → NULL. Shipped PR #594/D-2 (20e2da8e):
--     ganita_special_lagnas_get now accepts an optional chart_id and serves stored
--     special_lagna/upagraha/saham facts from chart_facts under entitlement (245 facts
--     verified live for chart 482012f1). No other column changes.
--
--   CR-61 (arudha_read, upapada_read) — known_gap: 'CR-61' → NULL on BOTH primitives. Shipped
--     via the V-5 emitter (PR #585): bodha_signals_get(signal_type_class=arudha) returns real
--     salience-ranked rows live (5 rows verified for chart 482012f1). upapada_read's
--     `definition` text updated in lockstep (its prose cited the now-closed CR-61 as an open
--     gap).
--
--   CR-64 (nakshatra_semantics) — known_gap: 'CR-64' → NULL. Shipped via the same V-5 wave:
--     bodha_signals_get(signal_type_class=nakshatra_semantic) returns 9 salience-ranked rows
--     live for chart 482012f1. RESIDUAL (not re-opened, tracked separately as the new CR-132):
--     constituent_facts_array carries a 16.7% orphan-ref rate on this chart per the tool's own
--     live DEFECT-001 self-report — a data-quality footnote, not a route/ranking gap.
--
--   CR-68 (lel_retrodiction) — known_gap: 'CR-68' → NULL, AND live_tool: 'mimamsa_lel_query' →
--     'mechanism_retrodiction_get'. Shipped PR #688 (5f27d9d2, 2026-07-21):
--     mechanism_retrodiction_get is a dedicated, registered, live tool joining LEL events to
--     the classical house-lord/dasha-activation mechanism per house (CONFIRMATION-ONLY,
--     sealed pre-2020 test split) — verified live for chart 482012f1 (7 mechanisms fired).
--     The prior route (mimamsa_lel_query, the raw LEL surface) is retained as fallback_face.
--
-- This is the THIRD confirmed occurrence of this register-drift class (a fix ships in code,
-- the registry's known_gap/CR-status columns are never flipped) after CR-56 (migration 463)
-- and CR-54/CR-59 (D-2, folded into migration 462's authoring). See the standing note in
-- POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md recommending a periodic reconciliation pass.
--
-- §N.3 idempotency (mirrors migrations 462/463 exactly):
--   • vidhi_primitives → ON CONFLICT (primitive_id) DO UPDATE (L0 global upsert).
-- Re-runnable: applying twice is a no-op beyond updated_at. No vidhi_floor_items rows are
-- touched (no floor re-numbering — these are known_gap/live_tool column flips only).
--
-- This migration is DATA-ONLY on Vidhi-owned tables. It does NOT touch the FROZEN
-- orchestrator/WriterBase, any L1–L5 writer/table, or any calibration table.
--
-- ROLLBACK (manual):
--   BEGIN;
--   -- Restore known_gap = 'CR-16' / 'CR-61' / 'CR-64' / 'CR-68' on the four rows below, and
--   -- restore lel_retrodiction.live_tool = 'mimamsa_lel_query'.
--   COMMIT;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

-- ── CR-16 — special_lagna_read: known_gap → NULL ──
INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('special_lagna_read', 1, 'Reads special lagnas (Indu, Sree, Ghati, Hora, Bhava, etc.) with domain salience.', 'structural', 'ganita_special_lagnas_get', '{"chart_id":"{chart_id}","lagnas":"{lagnas}"}'::JSONB,
        'ganita_special_lagnas_get', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

-- ── CR-61 (1/2) — arudha_read: known_gap → NULL ──
INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('arudha_read', 1, 'Arudha-semantic read: AL conjunctions, A2/A11 placement, AL–bhāva relationships, ranked.', 'signal', 'ganita_condition_get', '{"chart_id":"{chart_id}","mode":"arudha"}'::JSONB,
        'bodha_signals_get(frame=arudha)', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

-- ── CR-61 (2/2) — upapada_read: known_gap → NULL, definition updated (no longer cites CR-61 as open) ──
INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('upapada_read', 1, 'Upapada Lagna (UL/UPA) read for the marriage/relationship domain: the UPA bhava-arudha position (sign + house) and Arudha A12 (ARUDHA_A12), plus the 2nd-from-UL bhāva as an answerer-side derivation off the UPA house (sustenance / longevity-of-union significator). Raw arudha positions are data-backed; salience ranking shipped (CR-61, see known_gap).', 'signal', 'ganita_condition_get', '{"chart_id":"{chart_id}","facet":"karakas"}'::JSONB,
        'bodha_signals_get(frame=arudha)', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

-- ── CR-64 — nakshatra_semantics: known_gap → NULL ──
INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('nakshatra_semantics', 1, 'Nakshatra-semantic layer per graha: own-star, dispositor chains, tara bala, end-degree flags.', 'signal', 'ganita_nakshatra_get', '{"chart_id":"{chart_id}"}'::JSONB,
        'bodha_signals_get(signal_type_class=nakshatra_semantic)', NULL, ARRAY[]::TEXT[], ARRAY['CR-27d']::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

-- ── CR-68 — lel_retrodiction: known_gap → NULL, live_tool repointed to mechanism_retrodiction_get ──
INSERT INTO vidhi_primitives
  (primitive_id, version, definition, category, live_tool, tool_args,
   fallback_face, known_gap, mandatory_tags, cr27_prevents, updated_at)
VALUES ('lel_retrodiction', 1, 'Joins LEL events to the signal/mechanism they retrodictively confirm, served as confirmation only (never as prediction input).', 'temporal', 'mechanism_retrodiction_get', '{"chart_id":"{chart_id}","domain":"{domain}"}'::JSONB,
        'mimamsa_lel_query', NULL, ARRAY[]::TEXT[], ARRAY[]::TEXT[], now())
ON CONFLICT (primitive_id) DO UPDATE SET
    version        = EXCLUDED.version,
    definition     = EXCLUDED.definition,
    category       = EXCLUDED.category,
    live_tool      = EXCLUDED.live_tool,
    tool_args      = EXCLUDED.tool_args,
    fallback_face  = EXCLUDED.fallback_face,
    known_gap      = EXCLUDED.known_gap,
    mandatory_tags = EXCLUDED.mandatory_tags,
    cr27_prevents  = EXCLUDED.cr27_prevents,
    updated_at     = now();

COMMIT;
