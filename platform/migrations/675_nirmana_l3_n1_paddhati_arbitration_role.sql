-- 675_nirmana_l3_n1_paddhati_arbitration_role.sql
--
-- NIRMĀṆA L3 Kāla — N1 (Temporal Concordance Contract), second bounded step. The W1 evidence
-- base (L3_W1_ANALYSIS_BATCH_E.md §1.3) names `kala_paddhati_profile` as the minimum-viable
-- authority-profile table the concordance arbiter needs, generalized from its current
-- agnivasa-only scope, and names the two columns it is missing: `arbitration_role` (the prose
-- in each row's `provenance` field, promoted to data) and `precedence` (a total order within a
-- factor_family, so a future `disputed(adjudicated_by=…)` verdict has a deterministic winner
-- rather than a tie).
--
-- Purely additive: two new NULLABLE columns, no existing column altered, no existing consumer
-- changed. `constraint_role`/`convention_status`/etc. keep their current meaning and behaviour
-- unchanged — nothing in platform-mcp or platform/src branches on the new columns (verified:
-- grep for `.constraint_role` live-branching across platform-mcp/src + platform/src returns
-- zero hits; both existing TypeScript consumers — agnivasa_convention_b_voice.ts,
-- query_kala_paddhati_profile.ts — only ever SERVE constraint_role as descriptive data, never
-- branch on its value).
--
-- Also fixes F-CONC-2 (L3_W1_ANALYSIS_BATCH_E.md §1.3/PART 3), a real §N.7-item-4 defect on
-- this seed table: rows 7/8 (`agnivasa_muhurta_chintamani_arithmetic`, paddhati_v02) carry
-- `constraint_role = 'hard'` while their own `provenance` field says, verbatim, "Served as a
-- second, informational concurrence/dissent voice ONLY (ADJUDICATION-17) -- NEVER enters the
-- residence hard-gate Convention A alone governs." The machine-readable field and the prose
-- contradict each other; only the prose is correct (`agnivasa_convention_b_voice.ts` implements
-- exactly that — it reports a voice, `kala_sky_pattern.ts`'s Convention A branch holds the
-- actual gate, regardless of what `constraint_role` says). This migration promotes the prose's
-- true intent into the new `arbitration_role` column as DATA, rather than leaving a
-- machine-readable field that reads "hard gate" with nothing behind it enforcing one.
--
-- `constraint_role` itself is intentionally left unchanged (rows 7/8 keep 'hard') — correcting
-- it would be a second, unrelated change to a column real consumers already read; the honest
-- fix for THIS defect is the new column that actually answers "how much weight does this row's
-- verdict carry", which `constraint_role` was never precise enough to answer on its own (its own
-- three-value vocabulary predates the gate/primary/corroborating/informational/declared_silent
-- distinction the arbiter needs).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.


-- ── 1. Schema: two new columns ───────────────────────────────────────────────

ALTER TABLE kala_paddhati_profile
  ADD COLUMN IF NOT EXISTS arbitration_role TEXT,
  ADD COLUMN IF NOT EXISTS precedence       SMALLINT;

ALTER TABLE kala_paddhati_profile
  DROP CONSTRAINT IF EXISTS kala_paddhati_profile_arbitration_role_check;

ALTER TABLE kala_paddhati_profile
  ADD CONSTRAINT kala_paddhati_profile_arbitration_role_check
  CHECK (arbitration_role IS NULL OR arbitration_role = ANY (ARRAY[
    'gate', 'primary', 'corroborating', 'informational', 'declared_silent'
  ]));

COMMENT ON COLUMN kala_paddhati_profile.arbitration_role IS
  'N1 (Temporal Concordance Contract). How much weight this row''s convention carries in a '
  'future concordance verdict: gate (must agree or the verdict cannot pass), primary '
  '(the default authority for this factor_family), corroborating (a supporting voice), '
  'informational (served but never decisive), declared_silent (a seated engine that casts no '
  'vote — the convention_status=declared_not_computed case, promoted to a role). NULL on any '
  'row not yet classified. Purely descriptive as of this migration — no code branches on it '
  'yet (L3_W1_ANALYSIS_BATCH_E.md §1.3).';

COMMENT ON COLUMN kala_paddhati_profile.precedence IS
  'N1 (Temporal Concordance Contract). Total order within a (chart_id, factor_family): lower '
  'wins on a tie. NULL on any row not yet ranked (e.g. declared_silent rows, which never enter '
  'a tie). Purely descriptive as of this migration — no code reads it yet.';


-- ── 2. Backfill the six existing rows (F-CONC-2 fix included) ────────────────

-- id 1, 3: agnivasa_tithi_element_prithvi / corpus_default — the real Convention A gate.
UPDATE kala_paddhati_profile
SET arbitration_role = 'gate', precedence = 1
WHERE convention_id = 'agnivasa_tithi_element_prithvi'
  AND version = 'paddhati_v01';

-- id 2, 4: agnivasa_muhurta_chintamani_arithmetic, paddhati_v01, declared_not_computed —
-- the declared slot with no content pinned (ADJUDICATION-8 rail 2). Casts no vote at all.
UPDATE kala_paddhati_profile
SET arbitration_role = 'declared_silent', precedence = NULL
WHERE convention_id = 'agnivasa_muhurta_chintamani_arithmetic'
  AND convention_status = 'declared_not_computed'
  AND version = 'paddhati_v01';

-- id 7, 8: agnivasa_muhurta_chintamani_arithmetic, paddhati_v02, computed — F-CONC-2's own
-- rows. constraint_role='hard' contradicts this row's own provenance prose; arbitration_role
-- is the corrected, precise answer: informational, never a gate.
UPDATE kala_paddhati_profile
SET arbitration_role = 'informational', precedence = 2
WHERE convention_id = 'agnivasa_muhurta_chintamani_arithmetic'
  AND convention_status = 'computed'
  AND version = 'paddhati_v02';
