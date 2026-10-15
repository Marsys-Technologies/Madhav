-- Migration 1386: L0-M typed source preparation (pre-build, SR-A4-01).
-- ALGO 3.17 step 3; KYD-45/49/50/116/124. Schema ONLY: no corpus ingestion,
-- row reclassification, registry pin or production activation. Migration 1332
-- already admits marriage/upanayana/general while retaining natal/muhurta.
-- Allocated above main and every open kalayantra/* branch (both directories).
--
-- Consumer contract: services/ka_muhurta_seva/parihara_eval.py::load_rules.
-- Missing predicates, commentary status and priority remain honest SQL NULLs.
-- JSON shape is checked here; AST semantics and passage/locator agreement must
-- be independently verified before the coordinated ingestion/reseal. Merely
-- storing an object is never a verified rule or permission to cancel a dosa.
--
-- (I) INTERPRETATION: persist the consumer's explicit positive source_verse
-- separately from its display citation. A PG chunk can contain several verses.
-- Keep both halves of the machine locator absent or present together; never
-- infer a verse, strength threshold, priority or text reading for legacy rows.
-- Transaction ownership belongs to migrate.ts / the protected schema window.

ALTER TABLE public.bg_parihara_rules
  ADD COLUMN IF NOT EXISTS predicate JSONB,
  ADD COLUMN IF NOT EXISTS source_chunk_id TEXT,
  ADD COLUMN IF NOT EXISTS source_verse INTEGER,
  ADD COLUMN IF NOT EXISTS conjunction_reading TEXT,
  ADD COLUMN IF NOT EXISTS tika_extension BOOLEAN,
  ADD COLUMN IF NOT EXISTS priority_rank INTEGER;

ALTER TABLE public.bg_parihara_rules
  DROP CONSTRAINT IF EXISTS bg_parihara_rules_source_locator_check,
  DROP CONSTRAINT IF EXISTS bg_parihara_rules_predicate_check,
  DROP CONSTRAINT IF EXISTS bg_parihara_rules_conjunction_reading_check,
  DROP CONSTRAINT IF EXISTS bg_parihara_rules_priority_rank_check,
  DROP CONSTRAINT IF EXISTS bg_parihara_rules_extraction_context_check,
  DROP CONSTRAINT IF EXISTS bg_parihara_rules_net_standing_check;

ALTER TABLE public.bg_parihara_rules
  ADD CONSTRAINT bg_parihara_rules_source_locator_check CHECK (
    (source_chunk_id IS NULL AND source_verse IS NULL)
    OR (source_chunk_id IS NOT NULL AND btrim(source_chunk_id) <> ''
        AND source_verse IS NOT NULL AND source_verse > 0)
  ),
  ADD CONSTRAINT bg_parihara_rules_predicate_check CHECK (
    predicate IS NULL
    OR (jsonb_typeof(predicate) = 'object' AND predicate <> '{}'::jsonb
        AND scope IN ('marriage', 'upanayana', 'general')
        AND source_chunk_id IS NOT NULL AND source_verse IS NOT NULL
        AND conjunction_reading IS NOT NULL AND extraction_context IS NOT NULL)
  ),
  ADD CONSTRAINT bg_parihara_rules_conjunction_reading_check CHECK (
    conjunction_reading IN ('mula', 'tika')
  ),
  ADD CONSTRAINT bg_parihara_rules_priority_rank_check CHECK (priority_rank > 0),
  ADD CONSTRAINT bg_parihara_rules_extraction_context_check CHECK (
    extraction_context IN (
      'mula_sutra_citation', 'translator_gloss_in_narrative',
      'mula', 'mula_reconstructed', 'tika_commentary'
    )
  ),
  ADD CONSTRAINT bg_parihara_rules_net_standing_check CHECK (
    net_standing IN (
      'cancellable_by_condition', 'cancellable_by_remedial_act', 'cancelled',
      'never_cancelled'
    )
  );

COMMENT ON COLUMN public.bg_parihara_rules.predicate IS
  'Machine-evaluable source predicate for scoped L0-M rules; NULL means not '
  'encoded, never true. Nonempty JSON object is a storage shape check only; '
  'consumer allowlist and independent source admission validate semantics.';
COMMENT ON COLUMN public.bg_parihara_rules.source_chunk_id IS
  'Exact served-corpus chunk locator, paired with source_verse. Nullable for '
  'legacy rows. Passage resolution is a coordinated source-admission gate.';
COMMENT ON COLUMN public.bg_parihara_rules.source_verse IS
  'Positive verse locator within source_chunk_id; never parsed from display '
  'citation or inferred from a chunk containing multiple verses.';
COMMENT ON COLUMN public.bg_parihara_rules.conjunction_reading IS
  'mula or tika identifies the cited logical reading; v89 uses tika. NULL '
  'means unclassified. Distinct readings must not be silently combined.';
COMMENT ON COLUMN public.bg_parihara_rules.tika_extension IS
  'True identifies a commentary extension rather than the verse itself '
  '(ALGO 3.17 v90); NULL means unclassified, not false.';
COMMENT ON COLUMN public.bg_parihara_rules.priority_rank IS
  'Ordinal source priority (ALGO 3.17 v91), never a numerical cancellation '
  'count or score. No ranks assigned by this preparation; unknown stays NULL.';
COMMENT ON COLUMN public.bg_parihara_rules.extraction_context IS
  'Preserves mula_sutra_citation and translator_gloss_in_narrative; scoped '
  'L0-M source readings may additionally be mula, mula_reconstructed or '
  'tika_commentary. NULL means unclassified; no legacy row is reclassified.';
COMMENT ON COLUMN public.bg_parihara_rules.net_standing IS
  'Preserves conditional, remedial-act and unconditional cancellation; '
  'never_cancelled records an explicit textual prohibition (v69 vedha). '
  'Preparation stores no new rules and evaluates no cancellation.';
