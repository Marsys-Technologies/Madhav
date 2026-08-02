-- migration 532: mimamsa_intervention_ledger + the `mi_sankalpa` asset_registry seed row
-- (renumbered from the original 531 draft at write time — a live re-check immediately
-- before commit found 531 triple-claimed by two sibling ṢAḌ-DARŚANA lanes'
-- uncommitted worktrees: `531_kala_paddhati_profile.sql` (w4-lane-r-yajna-setu) and
-- `531_kala_tithi_pravesha.sql` (w3-tithi-pravesha). Per KALA_W4_UPAYA_DESIGN_v1_0.md
-- §7's own procedure — "the number is allocated at MERGE-LOCK time... re-run then" —
-- this file takes the next number that was actually free at write time, 532.)
-- =============================================================================
-- ṢAḌ-DARŚANA campaign · Wave W4 · Lane S (registry item 42). Spec:
-- KALA_W4_UPAYA_DESIGN_v1_0.md (v1.1) §4.2 (this table, verbatim), §4.1 ruling S-1
-- (the prediction spine), §8.2 (this asset_registry row, verbatim shape).
--
-- ── THE THREE-STORE PROBLEM, AND WHY THIS TABLE POINTS AT brahma_prospective_ledger
-- (§4.1 ruling S-1) ──────────────────────────────────────────────────────────
-- Item 42 says "extends standing-predictions machinery, NO parallel store." Three
-- stores could be meant: brahma_prospective_ledger (governance-sealed
-- pre-registration; mandatory falsifier; filing_method CHECK enforces explicit-
-- filing-tool provenance), mimamsa_predictions (the L5 engine's own rebuildable
-- forecast output, mi_bhavisya), and mimamsa_calibration/reliability (mi_pramana
-- scoring outputs). The intervention ledger's prediction spine is
-- brahma_prospective_ledger, by prediction_id FK — the only one of the three with
-- pre-registration semantics and an enforced explicit-filing provenance, which is
-- exactly what a three-armed study of ELECTION ITSELF requires. mi_sankalpa
-- (the writer landing in the companion PR) therefore NEVER inserts into
-- brahma_prospective_ledger directly — it could not anyway (the filing_method
-- CHECK is a deliberate governance wall against exactly this) — filing happens at
-- SERVE TIME through the sanctioned HTTP action
-- (platform-mcp/src/lib/intervention_filing.ts's fileInterventionFalsifier, the
-- Lane S spine PR), and this table only REFERENCES the resulting prediction_id.
--
-- ── THE STRUCTURAL CHECK CONSTRAINT (binding, ADJUDICATION-12) ───────────────
-- adoption_basis='session_inferred' rows were NEVER sealed into
-- brahma_prospective_ledger (the filing spine fails CLOSED on anything other than
-- the literal 'native_directed' basis) — so prediction_id IS NULL for them. The
-- CHECK below (mimamsa_intervention_ledger_inferred_never_sealed) makes that
-- invariant STRUCTURAL rather than conventional: a session_inferred row can NEVER
-- carry a sealed prediction_id, at the database, regardless of what any future
-- caller does or forgets to check. This is what lets the three-armed study
-- separate native-directed interventions from model-inferred ones instead of
-- silently pooling them.
--
-- ── performed IS NULLABLE ON PURPOSE ──────────────────────────────────────────
-- NULL means "not yet attested" — distinct from FALSE ("attested not-performed",
-- study arm elected_not_acted, which is real evidence). A boolean that cannot say
-- "I don't know" would silently convert absence into a negative observation.
-- performed / performed_at / performed_attested_by are NATIVE-ATTESTED ONLY,
-- exactly like LEL entries (brief §7 rail) — this writer never sets them.
--
-- ── IDEMPOTENCY (§N.3 status-preserving variant; binding on the mi_sankalpa
-- writer, not enforced by this migration, but the reason the natural key and the
-- study_arm/performed/outcome_event_id columns are shaped this way) ───────────
-- The writer's rebuild deletes ONLY chart-scoped rows still in
-- study_arm='elected_pending' AND performed IS NULL AND outcome_event_id IS NULL
-- — never a blanket per-chart DELETE, which would destroy native-attested outcome
-- data recorded after the original filing (mi_bhavisya's exact precedent,
-- transposed: "DELETE ... WHERE lifecycle_status IN ('pending','due')").
--
-- ── PRE-REGISTRATION INTEGRITY (§5.5) ─────────────────────────────────────────
-- mi_sankalpa never UPDATEs adjudication_record / score_vector /
-- predicted_differential / paddhati_version on an existing row — the
-- adjudication record is a snapshot of the judgment AT ELECTION TIME. A
-- convention-set change is a NEW row under a new paddhati_version, never an
-- in-place edit.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS mimamsa_intervention_ledger (
    intervention_id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    chart_id                UUID        NOT NULL,
    -- WHAT
    intent                  TEXT        NOT NULL CHECK (length(trim(intent)) > 0),
    intervention_class      TEXT        NOT NULL
        CHECK (intervention_class IN ('upaya', 'yajna', 'elected_activity')),
    rite_or_activity_class  TEXT        NOT NULL,
    event_class             TEXT        REFERENCES brahma_event_ontology(event_class_id),
    -- WHEN
    elected_window          TSTZRANGE   NOT NULL,
    precision_regime        TEXT        NOT NULL
        CHECK (precision_regime IN ('intra_day', 'day_grade')),
    precision_basis         TEXT        NOT NULL,
    -- WHY (the adjudication record at election time — frozen, never recomputed)
    adjudication_record     JSONB       NOT NULL,   -- the JudgmentLedger verbatim
    score_vector             JSONB       NOT NULL,   -- the 4-factor vector + which factors were present
    efficacy_tier            TEXT        NOT NULL
        CHECK (efficacy_tier IN ('classically_attested','traditional','speculative_extension')),
    source_citation          TEXT        NOT NULL CHECK (length(trim(source_citation)) > 0),
    paddhati_version         TEXT        NOT NULL,   -- the convention set that produced it
    -- THE PREDICTION (spine; §4.1 ruling S-1)
    predicted_differential   TEXT        NOT NULL,   -- "this window vs baseline", stated
    prediction_id            UUID        REFERENCES brahma_prospective_ledger(prediction_id),
    -- THE THREE-ARMED STUDY
    study_arm                TEXT        NOT NULL DEFAULT 'elected_pending'
        CHECK (study_arm IN ('elected_pending','acted_with_election',
                             'acted_without_election','elected_not_acted')),
    performed                BOOLEAN,                -- NULL = not yet attested; native-attested only
    performed_at             TIMESTAMPTZ,
    performed_attested_by    TEXT,
    outcome_event_id         UUID        REFERENCES life_events(id),
    outcome_linked_at        TIMESTAMPTZ,
    -- PROVENANCE
    authority_basis           TEXT,                   -- item 44: the field window-id / ELECT candidate id
    filed_by                  TEXT        NOT NULL,   -- the resolved MCP principal (ADJUDICATION-12: provenance, not authorship)
    -- ADJUDICATION-12: the ledger audits by INTENT-ORIGIN, not merely by principal. A row whose
    -- basis is 'session_inferred' was never sealed into brahma_prospective_ledger (fail-closed),
    -- so prediction_id IS NULL for it — the CHECK below makes that invariant structural rather
    -- than conventional, and is what lets the three-armed study separate native-directed
    -- interventions from model-inferred ones instead of pooling them.
    adoption_basis            TEXT        NOT NULL DEFAULT 'session_inferred'
        CHECK (adoption_basis IN ('native_directed', 'session_inferred')),
    CONSTRAINT mimamsa_intervention_ledger_inferred_never_sealed
        CHECK (adoption_basis = 'native_directed' OR prediction_id IS NULL),
    engine_version             TEXT        NOT NULL,
    build_id                   UUID,
    created_at                 TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT mimamsa_intervention_ledger_natural_key
        UNIQUE (chart_id, intervention_class, rite_or_activity_class, elected_window)
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_intervention_ledger_chart_arm
    ON mimamsa_intervention_ledger (chart_id, study_arm);
CREATE INDEX IF NOT EXISTS idx_mimamsa_intervention_ledger_event_class
    ON mimamsa_intervention_ledger (event_class);
CREATE INDEX IF NOT EXISTS idx_mimamsa_intervention_ledger_prediction_id
    ON mimamsa_intervention_ledger (prediction_id);
CREATE INDEX IF NOT EXISTS idx_mimamsa_intervention_ledger_elected_window
    ON mimamsa_intervention_ledger USING GIST (elected_window);

COMMENT ON TABLE mimamsa_intervention_ledger IS
  'ṢAḌ-DARŚANA W4 item 42 (mi_sankalpa): the Unified Intervention Ledger — every '
  'elected act (upāya · yajña · elected activity) with its adjudication record '
  '(frozen at election time), predicted differential, native performance '
  'attestation, and LEL outcome linkage. The three-armed study of election '
  'itself. Prediction spine is brahma_prospective_ledger by FK (ruling S-1); '
  'this table is never written to directly by the filing spine — only '
  'referenced.';

COMMENT ON COLUMN mimamsa_intervention_ledger.performed IS
  'NULL = not yet attested (distinct from FALSE = attested not-performed, a '
  'real observation). Native-attested only — this writer never sets it.';

COMMENT ON COLUMN mimamsa_intervention_ledger.adoption_basis IS
  'ADJUDICATION-12 intent-origin. native_directed = the native asked for this '
  'to be filed; session_inferred = the model concluded the native would want '
  'it (never sealed into brahma_prospective_ledger — see the '
  '_inferred_never_sealed CHECK).';

COMMENT ON CONSTRAINT mimamsa_intervention_ledger_inferred_never_sealed
    ON mimamsa_intervention_ledger IS
  'ADJUDICATION-12, structural: a session_inferred row can NEVER carry a sealed '
  'prediction_id. The filing spine (intervention_filing.ts) fails CLOSED on '
  'anything other than the literal native_directed basis, so this is a '
  'reassertion of an invariant already true by construction, not a new rule.';

-- ── asset_registry seed row for `mi_sankalpa` (§8.2, verbatim) ───────────────

INSERT INTO asset_registry (
    asset_id, layer, sort_order,
    sanskrit_name, english_name, english_description,
    storage_type, target_table, count_sql, size_sql,
    target_floor, scope, is_active, has_writer, has_substeps,
    writer_timeout_seconds,
    layer_name, layer_index, catalog_status, asset_kind
) VALUES (
    'mi_sankalpa',
    'mimamsa',
    14,
    'Saṅkalpa',
    'Intervention Ledger',
    'Unified intervention ledger — every elected act (upāya · yajña · elected '
    'activity) with its adjudication record, predicted differential, '
    'performance attestation and outcome linkage; the three-armed study of '
    'election itself. Prediction spine is brahma_prospective_ledger by FK '
    '(ruling S-1) — this writer never inserts into it directly.',
    'postgres_table', 'mimamsa_intervention_ledger',
    'SELECT count(*) FROM mimamsa_intervention_ledger WHERE chart_id = $1',
    'SELECT pg_total_relation_size(''mimamsa_intervention_ledger'')',
    NULL, 'per_chart', true, true, false,
    300,
    'Mīmāṃsā', 'L5', 'DRAFT', 'data'
) ON CONFLICT (asset_id) DO UPDATE SET
    count_sql               = EXCLUDED.count_sql,
    target_table            = EXCLUDED.target_table,
    has_writer              = EXCLUDED.has_writer,
    has_substeps            = EXCLUDED.has_substeps,
    writer_timeout_seconds  = EXCLUDED.writer_timeout_seconds,
    sort_order              = EXCLUDED.sort_order,
    scope                   = EXCLUDED.scope,
    is_active               = EXCLUDED.is_active,
    sanskrit_name           = EXCLUDED.sanskrit_name,
    english_name            = EXCLUDED.english_name,
    english_description     = EXCLUDED.english_description;

-- The one edge (§8.2 / KALA_W2_FIELD_DESIGN §9.1 / brief §2.5.3): ka_kshetra ->
-- mi_sankalpa, L3 -> L5, acyclic. ka_kshetra NEVER lists mi_sankalpa back (§2.5.4
-- acyclicity rule) — the ledger flows forward only.
UPDATE asset_registry SET depends_on = ARRAY['ka_kshetra']::text[]
WHERE asset_id = 'mi_sankalpa';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback):
--   BEGIN;
--   DELETE FROM asset_registry WHERE asset_id = 'mi_sankalpa';
--   DROP TABLE IF EXISTS mimamsa_intervention_ledger;
--   COMMIT;
-- =============================================================================
