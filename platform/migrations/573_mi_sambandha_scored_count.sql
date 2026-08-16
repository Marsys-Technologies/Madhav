BEGIN;

ALTER TABLE mimamsa_manifestation_grammar
  ADD COLUMN IF NOT EXISTS scored_count int NOT NULL DEFAULT 0;

COMMENT ON COLUMN mimamsa_manifestation_grammar.evidence_grade IS
  '''empirical''|''assignment_only''|''prior_only'' — empirical requires scored_count >= 5 '
  '(confirmed/partial/denied outcomes), not just opportunity_count >= 5 assignments. '
  'See F-35 (00_ARCHITECTURE/briefs/parisesa/lanes/F-35/).';

COMMIT;
