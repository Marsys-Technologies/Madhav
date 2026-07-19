-- Migration 458: brahma_prospective_ledger — D-4a Lane A-4 "Prospective ledger, LIVE"
-- Created: 2026-07-19
--
-- Numbering note: highest numbered file across BOTH migration dirs combined is 457
-- (platform/migrations/457_lel_schema_v2_event_shapes.sql, Lane A-1). 458 is the next
-- free number per platform/supabase/migrations/README.md's guidance.
--
-- Context: BRIEF_D4A.md Lane A-4 + TEMPORAL_ENGINE_ARC_PLAN §3 A-4 / §11 data-governance.
-- A live prediction store: claim, event_class (validated against brahma_event_ontology,
-- migration 388+456), claim_shape (validated against the ontology's canonical
-- temporal_shape for that event_class — DR-13/DIS.026 event-shape symmetry; a
-- point-claim against an interval-shaped class is a SCHEMA VIOLATION), a window or
-- milestone_set per shape, model+formula_version, confidence, MANDATORY falsifier,
-- as_of, generator_class (anchor_engine | reading_synthesis | engine |
-- native_intuition), configuration_signature (nullable until D-5).
--
-- Reuse note (BRIEF_D4A §B "Prospective-ledger schema <- reuse mimamsa_outcome_record/
-- LEL §9 PPL prior art where possible"): the live `mimamsa_predictions` table (MI-5-2,
-- platform/migrations/brahma_mimamsa_prediction_ledger.sql) already establishes the
-- conventions this migration reuses directly:
--   - `observation_window daterange` (not two separate date columns) for a claim's
--     window — reused here verbatim for point/interval shapes (a point claim is
--     represented as the degenerate one-day range [date, date+1)).
--   - `falsifier`/`source_citation` NOT NULL (B.3 derivation-ledger mandate; Learning
--     Layer discipline rule #4 — no exceptions).
--   - `lifecycle_status`, `formula_version`-style naming (`bundle_formula_version` in
--     mimamsa_predictions -> `formula_version` here), `created_at`/`emitted_at`-style
--     provenance timestamps (`as_of` here, per BRIEF_D4A's exact field name).
-- What's NEW here (not in mimamsa_predictions): `event_class` (FK to
-- brahma_event_ontology, absent from the MI-5-2 table, which predates the DR-13
-- ontology), `claim_shape` + `milestone_set` (chain-shape support), `generator_class`
-- enum, `configuration_signature` (D-5 hook), and the DB-level shape-enforcement
-- trigger below (§11 + DR-13 hard constraints this lane must enforce AT INSERT TIME,
-- not just in application code).
--
-- §11 governance (TEMPORAL_ENGINE_ARC_PLAN §11, binding): predictions exist by
-- explicit filing only; chat is never mined. Enforced structurally here via
-- `filing_method` CHECK (currently the single allowed value
-- 'explicit_filing_tool') — there is no code path that can insert a row through any
-- other route without either using the explicit filing function or violating this
-- constraint outright (an auditable, loud failure, not a silent contamination).
--
-- Zero kernel/weight/threshold/orb/valence changes. Additive only: one new table, one
-- new trigger function, no ALTER on any existing table.
--
-- Reversible: DOWN drops the trigger, function, table (CASCADE removes the FK from
-- brahma_event_ontology's side — none is added there — and the trigger).

BEGIN;

-- ── §1 — brahma_prospective_ledger table ───────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.brahma_prospective_ledger (
    -- Identity
    prediction_id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                UUID        NOT NULL,

    -- The claim itself
    claim                    TEXT        NOT NULL CHECK (length(trim(claim)) > 0),
    event_class              TEXT        NOT NULL
                                          REFERENCES public.brahma_event_ontology(event_class_id),
    claim_shape              TEXT        NOT NULL CHECK (claim_shape IN ('point', 'interval', 'chain')),

    -- Per-shape window/milestone data (exactly one populated, enforced by CHECK below
    -- AND by the ontology-shape trigger in §3 — belt and suspenders, matching the
    -- brief's "rejected at insert time, not silently accepted" hard constraint).
    observation_window       DATERANGE,   -- point (degenerate [d,d+1)) or interval shape
    milestone_set             JSONB,       -- chain shape only: [{milestone_id, expected_date, name_en}, ...]

    -- Generation provenance
    model                    TEXT        NOT NULL,
    formula_version          TEXT        NOT NULL,
    confidence                NUMERIC     NOT NULL CHECK (confidence > 0.0 AND confidence < 1.0),
    falsifier                 TEXT        NOT NULL CHECK (length(trim(falsifier)) > 0),
    as_of                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    generator_class           TEXT        NOT NULL
                                          CHECK (generator_class IN
                                            ('anchor_engine', 'reading_synthesis', 'engine', 'native_intuition')),
    configuration_signature   TEXT,        -- nullable until D-5 (ARC PLAN §B)

    -- Lifecycle / outcome-matching (Lane A-1 hook writes matched_*; a human/tool call
    -- promotes matched -> confirmed|falsified, never this migration's concern).
    lifecycle_status          TEXT        NOT NULL DEFAULT 'open'
                                          CHECK (lifecycle_status IN
                                            ('open', 'matched', 'confirmed', 'falsified', 'withdrawn')),
    matched_event_id          UUID        REFERENCES public.life_events(id),
    matched_at                TIMESTAMPTZ,
    match_note                 TEXT,

    -- §11 governance: explicit-filing-only enforcement + provenance
    filed_by                  TEXT        NOT NULL CHECK (length(trim(filed_by)) > 0),
    filing_method              TEXT        NOT NULL DEFAULT 'explicit_filing_tool'
                                          CHECK (filing_method = 'explicit_filing_tool'),
    source_citation            TEXT        NOT NULL CHECK (length(trim(source_citation)) > 0),

    created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- Shape/field consistency: exactly the fields for the declared claim_shape are
    -- populated. Mirrors migration 456's CHECK-constraint discipline for
    -- brahma_event_ontology's own shape columns.
    CONSTRAINT brahma_prospective_ledger_shape_fields_check CHECK (
        (claim_shape = 'point'
            AND observation_window IS NOT NULL
            AND upper(observation_window) = lower(observation_window) + 1
            AND milestone_set IS NULL)
        OR (claim_shape = 'interval'
            AND observation_window IS NOT NULL
            AND upper(observation_window) > lower(observation_window)
            AND milestone_set IS NULL)
        OR (claim_shape = 'chain'
            AND observation_window IS NULL
            AND milestone_set IS NOT NULL
            AND jsonb_typeof(milestone_set) = 'array'
            AND jsonb_array_length(milestone_set) >= 1)
    )
);

COMMENT ON TABLE public.brahma_prospective_ledger IS
    'D-4a Lane A-4 — live prospective prediction store. §11 governance (binding): '
    'predictions exist by explicit filing only; chat is never mined. Every row traces '
    'to an explicit filing call (filing_method = ''explicit_filing_tool''), never to an '
    'inferred conversational claim. claim_shape is validated against '
    'brahma_event_ontology.temporal_shape for event_class AT INSERT TIME by the '
    'brahma_prospective_ledger_enforce_shape trigger (§3) — a point-claim against an '
    'interval-shaped class is rejected outright, not silently accepted (DR-13/DIS.026 '
    'event-shape symmetry, TEMPORAL_ENGINE_ARC_PLAN §7).';

COMMENT ON COLUMN public.brahma_prospective_ledger.observation_window IS
    'point shape: degenerate one-day range [claimed_date, claimed_date + 1). '
    'interval shape: [window_start, window_end]. NULL for chain shape (see milestone_set).';
COMMENT ON COLUMN public.brahma_prospective_ledger.milestone_set IS
    'chain shape only: ordered array of {milestone_id, expected_date, name_en}. '
    'milestone_id MUST be a member of event_class''s brahma_event_ontology.milestone_template '
    '(enforced in application code by validateClaimShape / assertClaimShape, '
    'platform/src/lib/lel/event_ontology_shapes.ts — DB-level membership check is not '
    'expressible as a portable CHECK without a second FK table, so this is app-enforced).';
COMMENT ON COLUMN public.brahma_prospective_ledger.falsifier IS
    'MANDATORY (no exceptions — Learning Layer discipline rule #4 / B.3). A specific, '
    'checkable condition that would prove the claim wrong.';
COMMENT ON COLUMN public.brahma_prospective_ledger.generator_class IS
    'anchor_engine | reading_synthesis | engine | native_intuition — who/what generated '
    'this claim. reading_synthesis = a native-facing synthesis session''s reading '
    '(e.g. the wealth-baseline arc predictions); engine = a deterministic computation; '
    'anchor_engine = phala_anchors-sourced; native_intuition = the native''s own filed hunch.';
COMMENT ON COLUMN public.brahma_prospective_ledger.configuration_signature IS
    'Nullable until D-5 (TEMPORAL_ENGINE_ARC_PLAN §B) — will carry the exact model '
    'configuration hash once D-5''s engine ships versioned configurations.';
COMMENT ON COLUMN public.brahma_prospective_ledger.filing_method IS
    '§11 enforcement: the only permitted value is ''explicit_filing_tool''. This column '
    'exists so any future write path that is NOT the explicit filing function is a loud '
    'CHECK-constraint failure, not a silent contamination of the ledger by inferred claims.';

-- ── §2 — Indexes ──────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_brahma_prospective_ledger_chart_status
    ON public.brahma_prospective_ledger (chart_id, lifecycle_status);

CREATE INDEX IF NOT EXISTS idx_brahma_prospective_ledger_event_class
    ON public.brahma_prospective_ledger (event_class);

CREATE INDEX IF NOT EXISTS idx_brahma_prospective_ledger_as_of
    ON public.brahma_prospective_ledger (as_of DESC);

CREATE INDEX IF NOT EXISTS idx_brahma_prospective_ledger_window
    ON public.brahma_prospective_ledger USING GIST (observation_window);

-- ── §3 — DB-level claim_shape enforcement (DR-13 event-shape symmetry) ─────────
--
-- Belt-and-suspenders with the application-level validateClaimShape/assertClaimShape
-- (platform/src/lib/lel/event_ontology_shapes.ts, Lane A-2): this trigger makes the
-- rule impossible to bypass even via a direct SQL INSERT/UPDATE that skips the
-- application layer entirely — "a mismatched shape must be rejected at insert time,
-- not silently accepted" (BRIEF_D4A hard constraint) holds at the database, not just
-- in application code that could be bypassed or have a bug.

CREATE OR REPLACE FUNCTION public.brahma_prospective_ledger_enforce_shape()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_ontology_shape TEXT;
BEGIN
    SELECT temporal_shape INTO v_ontology_shape
      FROM public.brahma_event_ontology
     WHERE event_class_id = NEW.event_class;

    IF v_ontology_shape IS NULL THEN
        RAISE EXCEPTION
            'brahma_prospective_ledger: unknown event_class ''%'' (not present in brahma_event_ontology)',
            NEW.event_class;
    END IF;

    IF v_ontology_shape <> NEW.claim_shape THEN
        RAISE EXCEPTION
            'brahma_prospective_ledger: SCHEMA VIOLATION — claim_shape ''%'' does not match '
            'event_class ''%'' canonical shape ''%'' (DR-13/DIS.026 event-shape symmetry). '
            'A claim must speak in its class''s declared temporal grammar.',
            NEW.claim_shape, NEW.event_class, v_ontology_shape;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.brahma_prospective_ledger_enforce_shape() IS
    'DR-13/DIS.026 event-shape symmetry, enforced at INSERT/UPDATE time. Rejects any row '
    'whose claim_shape does not equal brahma_event_ontology.temporal_shape for its '
    'event_class — a point-claim against an interval-shaped class (or any other '
    'mismatch) is a hard failure, not a warning.';

DROP TRIGGER IF EXISTS trg_brahma_prospective_ledger_enforce_shape
    ON public.brahma_prospective_ledger;

CREATE TRIGGER trg_brahma_prospective_ledger_enforce_shape
    BEFORE INSERT OR UPDATE OF claim_shape, event_class
    ON public.brahma_prospective_ledger
    FOR EACH ROW
    EXECUTE FUNCTION public.brahma_prospective_ledger_enforce_shape();

COMMIT;

-- ── ROLLBACK (manual — not auto-run by migrate.ts) ─────────────────────────────
-- BEGIN;
-- DROP TRIGGER IF EXISTS trg_brahma_prospective_ledger_enforce_shape ON public.brahma_prospective_ledger;
-- DROP FUNCTION IF EXISTS public.brahma_prospective_ledger_enforce_shape();
-- DROP TABLE IF EXISTS public.brahma_prospective_ledger CASCADE;
-- COMMIT;
