-- 897_nirmana_l2_bodha_grounding_matches_schema.sql
--
-- NIRMANA v2.1 -- L2 (Bodha) schema addition. Transaction ownership belongs to
-- platform/scripts/migrate.ts.
--
-- Authors the bodha_grounding_matches schema -- the first of three sequenced
-- steps (migration, writer, registry/orchestrator wiring) ruled authorized by
-- adjudication #2258 (2026-09-07). Grounding fields (grounding_tier,
-- citation_granularity, bodha_grounding_matches) were confirmed genuinely
-- unimplemented (zero hits anywhere in platform/), not merely undispatched --
-- L4's held W3 items (agreement line, śruti quote, tail_watch) partly wait on
-- this landing as real data, per the coordination directive at loop 649.
--
-- Per #2258's partial ruling: structural questions (a) target_kind v1 scope,
-- (b) new dedicated writer vs. folding into an existing one, (c) DAG
-- dependency scope, are all RULED. The yukti-vs-pratyaksa tier-ASSIGNMENT
-- rule itself is NOT ruled (flagged for native, a doctrine-level content
-- judgment, not an infrastructure question) -- this migration ships the
-- schema only, no data, no assignment logic; genuinely safe to land standalone
-- ahead of that ruling per the ruling's own explicit authorization ("go ahead
-- and land the schema migration ... now").
--
-- Design, per #2258's own proposal (ruled as-is):
-- - target_kind v1 = {yoga_dosha_firing, msr_signal} only. Remedies, verdicts,
--   dasha-phala, and transit-quality are deferred to a v2 target_kind addition
--   once the pattern is proven on two classes with clean existing source data
--   -- the same small-scope-canary-before-generalizing discipline this whole
--   campaign has used repeatedly (bo_sudarshana/#1770 being the direct
--   precedent named in the ruling itself).
-- - target_id is TEXT, not a typed foreign key, because the two v1 target
--   tables have INCOMPATIBLE primary-key types: ga_yoga_firings.id is
--   INTEGER, bodha_msr_signals.signal_id is UUID (verified live against
--   information_schema.columns for both tables before authoring this DDL,
--   not assumed from the #2258 proposal's own casual "chart_yoga_firings"
--   naming, which does not exist -- the real table is ga_yoga_firings). A
--   single column cannot carry a real FK constraint across two differently-
--   typed target tables; this is the standard polymorphic-association
--   pattern, with target_kind as the discriminator and no DB-level FK on
--   target_id -- integrity is a writer-level obligation, documented inline.
-- - grounding_tier is plain TEXT with a CHECK constraint (sruti|yukti|
--   pratyaksa), matching this codebase's own established style for
--   controlled-vocabulary columns (see bodha_msr_signals.epistemic_tier,
--   migration 325) -- no CREATE TYPE ... AS ENUM anywhere in this codebase,
--   confirmed via a repo-wide grep before choosing TEXT+CHECK over an enum.
-- - citation_granularity CHECK mirrors adjudication #1726 condition 3's
--   already-closed ruling: 'page_column' | 'chapter_verse', required
--   (NOT NULL) specifically when grounding_tier='sruti', optional otherwise
--   -- sruti itself is unused in v1 (reserved for #1726's own future
--   text-direct lane; v1's matcher only ever assigns yukti/pratyaksa), so
--   this constraint is dormant until that lane lands but is encoded now so
--   it cannot be forgotten later.
-- - The falsifiability requirement from #2258's own proposal ("every yukti
--   row must carry a non-null matched_rule_id + derivation_chain -- a yukti
--   row with no chain is a build-fatal defect, not a stored ambiguity") is
--   encoded as a DB-level CHECK, not left to writer-side discipline alone --
--   the stronger, earned-signal-doctrine-aligned form (§N.8: a claim needs a
--   real detector, and a CHECK constraint is a detector the database itself
--   enforces on every write, not just the one writer that remembers to check).
-- - build_id + delete-then-insert idempotency: UNIQUE (chart_id,
--   ayanamsha_id, target_kind, target_id, build_id) mirrors
--   bodha_msr_signals' own UNIQUE shape (migration 325) -- per-chart
--   delete-then-insert (§N.3), never accretes across rebuilds.
--
-- No data is written by this migration. No writer references this table yet
-- -- the bo_grounding writer itself, and its orchestrator/registry DAG
-- wiring, are the next two ruled-but-not-yet-implemented steps, to follow in
-- subsequent bounded cycles once this schema is confirmed applied.

CREATE TABLE IF NOT EXISTS bodha_grounding_matches (
  match_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  chart_id                  UUID NOT NULL,
  ayanamsha_id              TEXT NOT NULL,
  build_id                  UUID NOT NULL,

  -- Discriminator + polymorphic target reference (see header: no single FK
  -- type spans ga_yoga_firings.id::integer and bodha_msr_signals.signal_id::uuid).
  target_kind                TEXT NOT NULL,   -- yoga_dosha_firing | msr_signal (v1 scope, #2258 ruled (a))
  target_id                  TEXT NOT NULL,   -- ga_yoga_firings.id::text | bodha_msr_signals.signal_id::text, per target_kind

  -- D-GROUNDING classification
  grounding_tier              TEXT NOT NULL,   -- sruti | yukti | pratyaksa
  citation_granularity        TEXT,            -- page_column | chapter_verse; required only when grounding_tier='sruti'
  grounding_evidence_jsonb    JSONB,           -- structured evidence backing the tier assignment
  derivation_chain            TEXT[],          -- cited principles / rule chain (required non-empty for yukti)
  matched_rule_id             TEXT,            -- the specific matched rule/principle id (required for yukti)

  computed_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
  engine_version               TEXT NOT NULL,

  CHECK (target_kind IN ('yoga_dosha_firing', 'msr_signal')),
  CHECK (grounding_tier IN ('sruti', 'yukti', 'pratyaksa')),
  CHECK (citation_granularity IS NULL OR citation_granularity IN ('page_column', 'chapter_verse')),
  CHECK (grounding_tier <> 'sruti' OR citation_granularity IS NOT NULL),
  CHECK (
    grounding_tier <> 'yukti'
    OR (matched_rule_id IS NOT NULL AND derivation_chain IS NOT NULL AND array_length(derivation_chain, 1) > 0)
  ),

  UNIQUE (chart_id, ayanamsha_id, target_kind, target_id, build_id)
);

-- S2: chart_id leads every index (this codebase's own convention, migration 325).
CREATE INDEX IF NOT EXISTS grounding_matches_chart_aya_idx
  ON bodha_grounding_matches (chart_id, ayanamsha_id);
CREATE INDEX IF NOT EXISTS grounding_matches_target_idx
  ON bodha_grounding_matches (target_kind, target_id);
CREATE INDEX IF NOT EXISTS grounding_matches_tier_idx
  ON bodha_grounding_matches (chart_id, grounding_tier);
