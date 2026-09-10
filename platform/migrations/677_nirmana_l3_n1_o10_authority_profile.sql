-- 677_nirmana_l3_n1_o10_authority_profile.sql
--
-- NIRMĀṆA L3 Kāla — N1 (Temporal Concordance Contract), fifth bounded step. Seeds
-- `kala_paddhati_profile` — generalized beyond its agnivasa-only scope by migration 675's
-- `arbitration_role`/`precedence` columns — with its first NON-agnivasa factor_family: O-10
-- from L3_W1_ANALYSIS_BATCH_E.md §1.2's overlap matrix, chosen because it is both already
-- precisely specified there and already directly actionable by the immediately-preceding N1
-- step:
--
--   "O-10 | 'Does the causal chain hold?' — as-of | E31 PACT · E29 KP · a5_gochara_agreement
--   (E4) | already served side by side in kala_explain_get | partial — three stances served,
--   no verdict over them"
--
-- The previous N1 step (PR #1919) wired exactly the KP and gochara_v3 (E4/a5) voices into
-- `kala_explain_get`'s new `engine_testimony[]` field, using `engine: 'kp'`/`engine:
-- 'gochara_v3'` as their canonical ids (services/gochara_v3's own naming; platform-mcp's
-- lib/engine_testimony.ts). This migration gives those two engines — plus PACT itself, the
-- authority they are measured against — a real authority-profile row apiece, using those
-- SAME id strings for `convention_id`, so a future verdict composer can look up
-- `kala_paddhati_profile WHERE factor_family = 'O-10' AND convention_id = <testimony.engine>`
-- directly rather than needing a second id-mapping table.
--
-- Roles, reasoned from what each engine actually IS today (not invented):
--   - `pact`        — arbitration_role='primary', constraint_role='hard', precedence=1.
--                     kala_explain_get's own `pact_status`/`weakest_link` is the reference
--                     point KP and gochara_v3 are measured AGAINST ('concurs'/'dissents' is
--                     relative to it, per kp_school_voice.ts / A5's own agreement logic) — it
--                     is the authoritative source in this factor_family, not a corroborating
--                     voice alongside the other two.
--   - `kp`          — arbitration_role='corroborating', constraint_role='informational',
--                     precedence=NULL (no established ranking against gochara_v3 — neither
--                     engine's own module claims priority over the other; kp_school_voice.ts's
--                     own docstring: "Disagreement is served as intelligence, never hidden",
--                     i.e. disclosed, never gating).
--   - `gochara_v3`  — arbitration_role='corroborating', constraint_role='informational',
--                     precedence=NULL, same reasoning — explain.ts's A5 facet is explicitly
--                     "reported for explainability" per its own SM-γ C4.2 comment, never
--                     folded into pact_status itself.
--
-- convention_status='computed' for all three (unlike agnivasa's declared_not_computed slot
-- case) — PACT, KP and gochara_v3 are all genuinely, actively computed for every
-- kala_explain_get call today (KP degrades to its own honest_empty state when its substrate
-- is absent, but the ENGINE itself is computed/consulted, which is what convention_status
-- tracks here — this is a profile of the ENGINE's operative status, not of any single call's
-- result).
--
-- Purely additive: INSERT only, no existing row touched, no schema change (migration 675
-- already added the columns this INSERT populates). No code reads these new rows yet — this
-- is authority-profile groundwork for the verdict-composition step N1 still has ahead of it,
-- the same "data first, consuming logic later" pattern this session's other N1 steps followed.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- Defensive column guard: this migration's INSERT populates arbitration_role/precedence,
-- added by migration 675 (still an open, unmerged PR as of this commit — both migrations are
-- mine, in the same 670-679 range, and migrate.ts applies pending migrations in numeric
-- order, so 675 will always run before 677 once both are on main; this guard exists only so
-- 677 does not itself depend on merge ORDER between two same-author PRs, matching migration
-- 675's own idempotent ADD COLUMN IF NOT EXISTS — a genuine no-op once 675 has already run).
ALTER TABLE kala_paddhati_profile
  ADD COLUMN IF NOT EXISTS arbitration_role TEXT,
  ADD COLUMN IF NOT EXISTS precedence       SMALLINT;

INSERT INTO kala_paddhati_profile (
  chart_id, factor_family, convention_id, school_tag, constraint_role, convention_status,
  provenance, native_confirmed, awaiting_native_confirmation, version, arbitration_role,
  precedence
)
SELECT
  chart_id, 'O-10', convention_id, school_tag, constraint_role, 'computed',
  provenance, false, true, 'paddhati_v01', arbitration_role, precedence
FROM (
  VALUES
    ('pact', 'parasari_chain', 'hard',
     'The PACT protocol (promise -> confirmation -> activation -> trigger), the chained '
     || 'investigation kala_explain_get is a thin facade over (explain.ts module docstring). '
     || 'Its resolved pact_status is the reference point kp/gochara_v3''s own concurs/dissents '
     || 'agreement is measured against, not a corroborating voice alongside them — the '
     || 'authoritative source in this factor_family (O-10, L3_W1_ANALYSIS_BATCH_E.md §1.2).',
     'primary', 1),
    ('kp', 'krishnamurti_paddhati', 'informational',
     'KP sub-lord clock (platform-mcp/src/lib/kp_school_voice.ts): asks whether the running '
     || 'dasha lord SIGNIFIES the house by the KP significator '
     || 'ladder, a judgment-method independent of PACT''s own Parasari checklist. Its own '
     || 'docstring: "Disagreement is served as intelligence, never hidden" — disclosed, never '
     || 'gating pact_status itself.',
     'corroborating', NULL),
    ('gochara_v3', 'transit_gochara', 'informational',
     'The SM-gamma C4.2 A5 gochara-agreement facet (platform-mcp/src/tools/kala_views/'
     || 'explain.ts, SM_GAMMA_C4_ENABLED-guarded): compares live transit-window valence '
     || 'against pact_status''s own polarity. Explicitly "reported for explainability" in its '
     || 'own module comment — never folded into pact_status itself.',
     'corroborating', NULL::smallint)
) AS engines(convention_id, school_tag, constraint_role, provenance, arbitration_role, precedence)
CROSS JOIN (
  SELECT DISTINCT chart_id FROM kala_paddhati_profile
) AS charts(chart_id)
ON CONFLICT (chart_id, factor_family, convention_id, version) DO NOTHING;
