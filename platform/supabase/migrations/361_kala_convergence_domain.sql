-- Migration 361: add domain column to kala_convergence + widen mode constraint to include 'D'
--
-- Part 1 — domain column (B4-src fix):
--   ka_sangam (A3) populates domain from the originating bodha_msr_signals.domains_affected_array[0].
--   ka_bhavishya_lekha (A4) reads kala_convergence.domain directly, avoiding keyword inference
--   that was causing ~80% of rows to resolve to 'general' and leaving 4 of 7 predictive
--   domains with 0 anchors at L4.
--   NULL is acceptable when the source MSR signal has no domain tags.
--
-- Part 2 — mode constraint widening (O7 enhancement):
--   ka_sangam Mode D (AV-bindhu convergence sub-mode) emits rows with mode='D'.
--   The existing constraint only permits ('A','B','C').  Widen it to include 'D'.
--   Mode D is classically grounded: transit through a sign with SAV ≥ 28 bindhu
--   = strong activation window (Phaladeepika Ch.26; BPHS Ch.66 Gochara-Ashtakavarga).
--
-- Both operations are idempotent (IF NOT EXISTS / DROP IF EXISTS + ADD).

-- Part 1: domain column
ALTER TABLE kala_convergence
  ADD COLUMN IF NOT EXISTS domain TEXT;

COMMENT ON COLUMN kala_convergence.domain IS
  'Primary domain inherited from the originating bodha_msr_signals.domains_affected_array[0]. '
  'NULL when the source signal has no domain tags. '
  'Written by ka_sangam (A3); consumed by ka_bhavishya_lekha (A4) for domain assignment.';

-- Part 2: widen mode CHECK constraint to include Mode D
ALTER TABLE kala_convergence DROP CONSTRAINT IF EXISTS kala_convergence_mode_check;
ALTER TABLE kala_convergence
  ADD CONSTRAINT kala_convergence_mode_check
  CHECK (mode = ANY (ARRAY['A'::text, 'B'::text, 'C'::text, 'D'::text]));
