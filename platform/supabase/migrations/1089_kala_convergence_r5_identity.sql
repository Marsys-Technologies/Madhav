-- Migration 1089 — R-5 contact identity and R-3 convention frame reach the table
--
-- RENUMBERED 2026-09-24 (was 1086). The L0 repair branch claimed 1086 first
-- (verified first-commit times: theirs 08:54/11:21 IST, mine 11:25/11:42), and neither
-- side had applied. Under the rule the Gochara stream proposed and this stream accepts —
-- an applied migration keeps its number, otherwise first claim holds — they keep 1086.
-- Safe to renumber precisely because this file is UNAPPLIED; a migration is never
-- renumbered after it has been applied.
-- (synergy audit #6 and #10; additive only)
--
-- #6 said: `convergence_id` is a BIGSERIAL reissued on every rebuild, so nothing
-- can cite a Saṅgam window across a rebuild. #10 found WHY R-5's identity never
-- shipped: `contact_uuid` is defined over R-3's six-component convention frame,
-- and that frame was emitted nowhere. Migration 1085 therefore deliberately
-- shipped no contact_uuid column. This migration ships both, together, because
-- one without the other is either a NULL column or an invented frame.
--
-- `convention_frame` is emitted HONESTLY: `ephemeris_backend = 'unasserted'`
-- (R-4 requires it asserted per call from Swiss's return flag; _calc_ut_cached
-- discards result[1], so nothing asserts it) and `house_frame = 'unavailable'`
-- (ka_sangam reads no cusp system). Those two values ARE the open gaps, recorded
-- as data rather than as a claim nothing checks (§N.8).
--
-- `node_convention` records what the SCANNER did ('true_node',
-- transit_search.py:10,64) — not what M-1 ruled ('mean'). The mismatch is
-- therefore visible in every row and queryable, which is what synergy audit #8
-- asked a manual stamp to achieve. It becomes 'mean' when the N-7 producer
-- replaces the scan, and not by editing this comment.

ALTER TABLE kala_convergence
    ADD COLUMN IF NOT EXISTS contact_uuid       UUID,
    ADD COLUMN IF NOT EXISTS convention_frame   JSONB,
    ADD COLUMN IF NOT EXISTS identity_state     TEXT;

COMMENT ON COLUMN kala_convergence.contact_uuid IS
    'R-5/D-R5-1: rebuild-stable contact identity (UUIDv5 over chart, method contract, graha, '
    'target_fact_id, directed angle, R-3 frame, orb, contact kind). Excludes peak_date and '
    'interval endpoints by design — those are content, not identity. NULL when identity_state '
    'says why it could not be computed.';
COMMENT ON COLUMN kala_convergence.convention_frame IS
    'R-3 six-component convention vector as named data. Includes honest gap markers: '
    'ephemeris_backend=unasserted (R-4 detector missing), house_frame=unavailable (no cusp read). '
    'node_convention records the SCANNER''s convention, so an M-1 mismatch is queryable.';
COMMENT ON COLUMN kala_convergence.identity_state IS
    'computed | no_target_fact_id | no_graha. Why contact_uuid is NULL when it is — never silence.';

CREATE INDEX IF NOT EXISTS idx_kala_convergence_contact_uuid
    ON kala_convergence (chart_id, contact_uuid) WHERE contact_uuid IS NOT NULL;
