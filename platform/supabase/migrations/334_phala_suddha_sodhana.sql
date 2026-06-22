-- Migration 334: phala_suddha_sodhana — Cleansed Anchor Disposition Table
-- Part of L4 Phala Wave 5. Depends on migrations 330 + 333.
--
-- D43 SAFETY RAIL (hard): staged_revision_jsonb STAGES proposed corrections.
-- revision_approved_by and revision_applied_at are NEVER SET by the writer.
-- They can only be set by a future operator action after native approval.
-- The NOT NULL DEFAULT NULL pattern + the application-level check in the writer
-- together enforce this: the writer must NEVER supply these columns.
--
-- cleanliness_status values:
--   clean            — no flags from phala_sodhana
--   flagged          — has minor/informational flags only; usable with caveat
--   staged_revision  — has major/critical flags; revision staged, pending native sign-off

CREATE TABLE IF NOT EXISTS phala_suddha_sodhana (
    entry_id                uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                uuid        NOT NULL,
    anchor_id               uuid        NOT NULL REFERENCES phala_anchors(anchor_id) ON DELETE CASCADE,

    -- Disposition
    cleanliness_status      text        NOT NULL CHECK (cleanliness_status IN (
                                            'clean', 'flagged', 'staged_revision'
                                        )),
    critical_flag_count     smallint    NOT NULL DEFAULT 0,
    major_flag_count        smallint    NOT NULL DEFAULT 0,
    minor_flag_count        smallint    NOT NULL DEFAULT 0,
    flag_ids_jsonb          jsonb,      -- array of sodhana_ids (cross-table ref, no FK needed)

    -- Staged revision — PROPOSED changes only; never auto-applied (D43)
    staged_revision_jsonb   jsonb,      -- {field: current_value, proposed_value, basis}[]

    -- Approval gate — writer MUST leave both NULL (D43 safety rail)
    -- Only set by future operator action after explicit native approval.
    revision_approved_by    text,       -- NULL until native signs off
    revision_applied_at     timestamptz,-- NULL until applied

    -- Impact estimates (for native's review decision)
    confidence_delta_if_applied     double precision,
    magnitude_delta_if_applied      text,

    -- Provenance
    derivation_ledger_jsonb jsonb       NOT NULL,
    source_citation         text        NOT NULL,
    computed_at             timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS phala_suddha_sodhana_anchor_key
    ON phala_suddha_sodhana (chart_id, anchor_id);

CREATE INDEX IF NOT EXISTS phala_suddha_sodhana_status
    ON phala_suddha_sodhana (chart_id, cleanliness_status);

COMMENT ON TABLE phala_suddha_sodhana IS
'L4 Phala Cleansed Anchor Disposition — one row per phala_anchors entry. '
'Classifies each anchor as clean/flagged/staged_revision based on phala_sodhana '
'flags. Staged revisions are proposals for native review only (D43 safety rail).';

COMMENT ON COLUMN phala_suddha_sodhana.revision_approved_by IS
'D43 SAFETY RAIL: always NULL after writer run. Only set by operator after '
'explicit native approval of staged_revision_jsonb. Writer constraint: '
'any writer that sets this column is a critical bug.';

COMMENT ON COLUMN phala_suddha_sodhana.revision_applied_at IS
'D43 SAFETY RAIL: always NULL after writer run. Set by future apply step '
'only after revision_approved_by is populated by operator + native sign-off.';
