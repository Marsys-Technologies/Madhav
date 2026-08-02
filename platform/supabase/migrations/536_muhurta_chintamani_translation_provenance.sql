-- Migration 536: classical_text_chunks.translation_status/translation_provenance —
-- the machine-translation provenance columns for the Muhūrta-Cintāmaṇi corpus pass
-- =============================================================================
-- Context: MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md v1.1 §3.1/§4 (commissioned
-- by the native, 2026-08-02). Corpus curation (generative translation of
-- `muhurta_chintamani`'s 274 untranslated chunks) — NOT a ṢAḌ-DARŚANA night-run
-- lane; this task's own supervised session, kept out of the campaign's
-- deterministic-first rail. The campaign only consumes this pass's output.
--
-- v1.0 of the brief instructed the session to "match the corpus schema's existing
-- convention" for translation provenance. The session's live census before writing
-- anything found NO such convention: `cleaned_devanagari_text`,
-- `cleaned_translation_text`, `ocr_confidence_score`, `low_confidence_flag`,
-- `ocr_review_note`, `ocr_cleanup_pass_version` are 100% null/unused across all
-- 9,600+ rows of all 15 ingested texts — added speculatively, never populated —
-- and `translation_status`/`translation_provenance` do not exist in the schema at
-- all, despite v1.0's mechanics referencing both. The session halted rather than
-- invent the scheme. v1.1 §4 defines it explicitly; this migration adds the two
-- missing columns that definition depends on.
--
-- ── WHAT THIS MIGRATION ADDS ─────────────────────────────────────────────────
-- Two nullable columns on `classical_text_chunks`, additive, zero-backfill:
--   `translation_status`      — 'machine_translated_supervised' | 'deferred' | NULL
--   `translation_provenance`  — free-text provenance string | NULL
-- NULL everywhere the translation pass has not touched a row — every existing row
-- across all 15 texts (9,600+) stays NULL/NULL, including the 274
-- `muhurta_chintamani` rows themselves until the translation pass writes them.
-- `translator` (the source-edition citation field every text already uses) is
-- untouched by this migration and remains READ-ONLY for the translation task per
-- brief §2/§4.
--
-- Semantically overloading the OCR fields to also carry translation status was
-- considered (brief §3.1) and rejected: they answer "how clean is the OCR", not
-- "has this chunk been machine-translated" — a different, orthogonal question the
-- schema had no column for.
--
-- ── IDEMPOTENCY (§N.3) ────────────────────────────────────────────────────────
-- `ADD COLUMN IF NOT EXISTS`, constraint guarded by a `pg_constraint` existence
-- check (`ADD CONSTRAINT` has no `IF NOT EXISTS` form — same pattern as migrations
-- 456/522). Fully re-runnable.
--
-- ── MIGRATION-NUMBER CLAIM ────────────────────────────────────────────────────
-- Re-verified live immediately before writing this file (2026-08-02/03): `main`'s
-- `platform/supabase/migrations/` tops out at 533; the live `_migrations_applied`
-- tracker's true max applied numeric migration is also 533
-- (`533_kala_paddhati_profile.sql`); the parallel `shad-darshana/integration`
-- branch's conductor worktree already claims 534
-- (`534_kala_paddhati_native_confirmed.sql`) and 535
-- (`535_bg_kp_sublord_division.sql`) locally (checked read-only via `ls`, per this
-- task's hard boundary against touching that worktree/branch otherwise). This
-- migration claims **536**, the next free integer past every claim observed at
-- check time, in `platform/supabase/migrations/` per brief §3.1.
--
-- ── REVERSIBILITY: HIGH ───────────────────────────────────────────────────────
-- Drop two nullable columns and one constraint. No existing row's data changes;
-- no served value on any other surface changes. See the DOWN block at the foot.
-- =============================================================================

BEGIN;

ALTER TABLE classical_text_chunks
  ADD COLUMN IF NOT EXISTS translation_status     TEXT,
  ADD COLUMN IF NOT EXISTS translation_provenance TEXT;

DO $$ BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'classical_text_chunks_translation_status_ck'
  ) THEN
    ALTER TABLE classical_text_chunks
      ADD CONSTRAINT classical_text_chunks_translation_status_ck
      CHECK (translation_status IS NULL
             OR translation_status IN ('machine_translated_supervised', 'deferred'));
  END IF;
END $$;

COMMENT ON COLUMN classical_text_chunks.translation_status IS
  'MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md v1.1 §4: NULL everywhere a '
  'translation pass has not touched the row. ''machine_translated_supervised'' — '
  'content_en was rewritten from content_sa by this task and re-embedded. '
  '''deferred'' — the pass reviewed the chunk and chose not to render it '
  '(content_en left EXACTLY as-is, still = content_sa); ocr_review_note carries '
  'the reason, prefixed ''deferred: ''. Honest-deferred beats fabricated-fluent.';

COMMENT ON COLUMN classical_text_chunks.translation_provenance IS
  'MUHURTA_CHINTAMANI_TRANSLATION_BRIEF_v1_0.md v1.1 §4: free-text provenance for '
  'a machine-translated or deferred row, e.g. ''machine_translation_supervised_'
  '2026-08; commissioned per SHAD_DARSHANA_ADJUDICATIONS_NIGHT3_v1_0.md §NATIVE '
  'CONFIRMATIONS; source edition per translator field''. The `translator` column '
  'itself stays READ-ONLY — it records the source-edition citation, not this '
  'pass''s own provenance, and is never overwritten by a translation task.';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   ALTER TABLE classical_text_chunks DROP CONSTRAINT IF EXISTS classical_text_chunks_translation_status_ck;
--   ALTER TABLE classical_text_chunks DROP COLUMN IF EXISTS translation_provenance;
--   ALTER TABLE classical_text_chunks DROP COLUMN IF EXISTS translation_status;
--   COMMIT;
-- Safe: both columns are nullable and additive; no pre-existing row's data was
-- ever written by this migration (verified: it does not contain a single UPDATE
-- statement), so there is nothing to un-write, only schema to remove.
-- =============================================================================
