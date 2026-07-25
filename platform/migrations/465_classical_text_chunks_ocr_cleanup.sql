-- Migration 465: classical_text_chunks OCR-quality cleanup fields (Elevation Campaign v2.1,
-- Stream beta, Lane G, EL-52)
-- Created: 2026-07-25
--
-- Purpose: the classical corpus sweep (brahmagyan/l0_remedy_corpus.py::sweep_classical_text_chunks)
-- copies classical_text_chunks.content_en verbatim, including OCR noise so severe some rows are
-- functionally uncited (named example: the BPHS Ch.47 Venus-maraka passage, chunk bphs_pg0581_c01
-- range, rendered with segments like "3Tr?Ctrqqqad EI€TITfEfrffTq"). B.3's derivation-ledger
-- discipline assumes a citation is READABLE — an unreadable citation is functionally an uncited
-- claim. This migration adds additive, nullable fields to score and (where honestly recoverable)
-- clean corpus rows, without altering or discarding the raw content_en (the audit trail).
--
-- Discipline (B.10): ocr_confidence_score is a DETERMINISTIC legibility score (character-class /
-- dictionary-word-ratio heuristic), never a guess at content. cleaned_translation_text /
-- cleaned_devanagari_text are populated ONLY where the underlying characters are genuinely
-- recoverable (e.g. word-boundary reinsertion in already-legible text) — never invented. Rows
-- below the confidence floor keep these NULL and low_confidence_flag=true; ocr_review_note
-- explains why, so a consumer never mistakes "not yet cleaned" for "cleanly nothing to report."
--
-- ROLLBACK:
--   ALTER TABLE classical_text_chunks
--     DROP COLUMN IF EXISTS ocr_confidence_score,
--     DROP COLUMN IF EXISTS cleaned_translation_text,
--     DROP COLUMN IF EXISTS cleaned_devanagari_text,
--     DROP COLUMN IF EXISTS low_confidence_flag,
--     DROP COLUMN IF EXISTS ocr_review_note,
--     DROP COLUMN IF EXISTS ocr_cleanup_pass_version;
-- ─────────────────────────────────────────────────────────────────────────────

BEGIN;

ALTER TABLE classical_text_chunks
  ADD COLUMN IF NOT EXISTS ocr_confidence_score     NUMERIC(4,3),
    -- 0.000-1.000, deterministic legibility heuristic (see
    -- brahmagyan/ocr_cleanup.py::score_ocr_confidence). NULL = not yet scored.
  ADD COLUMN IF NOT EXISTS cleaned_translation_text  TEXT,
    -- Word-boundary-repaired / noise-stripped English translation, populated ONLY when
    -- genuinely recoverable from content_en (never a guessed reconstruction). NULL = either
    -- not yet processed, or the translation portion itself was not recoverable (see
    -- ocr_review_note for which).
  ADD COLUMN IF NOT EXISTS cleaned_devanagari_text   TEXT,
    -- Cleaned Sanskrit/Devanagari verse text, populated ONLY when recoverable. Expected to
    -- remain NULL for most OCR-garbled rows (Devanagari-via-English-OCR is the harder failure
    -- mode and is NOT guessed at — flagged low-confidence instead per B.10).
  ADD COLUMN IF NOT EXISTS low_confidence_flag       BOOLEAN NOT NULL DEFAULT FALSE,
    -- TRUE = this row's content_en (or a material portion of it) could not be cleanly recovered;
    -- consumers should treat it as a citation of last resort, not a confirmed reading.
  ADD COLUMN IF NOT EXISTS ocr_review_note           TEXT,
    -- Human-readable explanation of what was and was not recoverable, and why (e.g. "Devanagari
    -- verse segment unrecoverable from source OCR; trailing English translation cleaned via
    -- word-boundary reinsertion only, no content invented").
  ADD COLUMN IF NOT EXISTS ocr_cleanup_pass_version  TEXT;
    -- Which cleanup pass/version last touched this row (e.g. 'beta_g_el52_v1'), for audit trail
    -- and to distinguish "never processed" (NULL) from "processed, scored high-confidence,
    -- no cleaning needed" (non-NULL, ocr_confidence_score high, cleaned_* still NULL because
    -- content_en was already clean).

CREATE INDEX IF NOT EXISTS idx_classical_chunks_low_confidence
  ON classical_text_chunks (low_confidence_flag)
  WHERE low_confidence_flag = TRUE;

COMMENT ON COLUMN classical_text_chunks.ocr_confidence_score IS
  'Deterministic OCR legibility score, 0-1, EL-52 (Elevation Campaign v2.1 beta.G). Never a content guess.';
COMMENT ON COLUMN classical_text_chunks.low_confidence_flag IS
  'TRUE = content_en (or part of it) is OCR noise that could not be honestly recovered/cleaned. Flagged, never silently served as if clean. EL-52.';

COMMIT;
