-- Migration 575: chart_subject_consent — CONSENT, SUBJECTS, AND EXCLUSIONS
-- Paripraśna P1 FOUNDATION, lane G1-B (NCD-9 · PPR-14/PPR-26) · 2026-08-19
--
-- ── WHY THIS EXISTS ────────────────────────────────────────────────────────────
-- Abuse case A9 (SAFETY_PRIVACY_TENANCY_v0_1_PROPOSAL §8) — "the native (or any
-- entitled user) creates a chart for a non-consenting adult — spouse, colleague,
-- public figure — and reads them without their knowledge" — is today entirely
-- undefended: chart creation is ungated and MACRO_PLAN §3.5.A.4 is unenforced.
-- NCD-9 (RULED — adopt at G1, 2026-08-18) adopts the consent schema NOW rather
-- than at first cohort intake, on the Scope-Boundary rationale that this is
-- protection for charts that exist TODAY, not M7 pre-building.
--
-- PPR-14, verbatim: "No L2+ output for a chart whose subject lacks a consent
-- row, unless subject_kind = native_self (strictly: the subject IS the native,
-- or the minor-guardian carve-out). Minors (<18) MUST be excluded from any
-- cohort and MUST NOT be servable beyond the guardian context. Exclusions MUST
-- be logged in the excluded-subject register. Withdrawal MUST trigger verified
-- deletion with tombstone-hashed receipt snapshots."
--
-- ── WHAT THIS MIGRATION ADDS (purely additive — five NEW tables, no existing
--    table is altered, dropped, or re-typed) ─────────────────────────────────────
--   1. `chart_subject_consent`             — the consent record (current state)
--   2. `chart_subject_consent_events`      — append-only, hash-chained transitions
--   3. `chart_subject_exclusions`          — the excluded-subject register (§3.5.F)
--   4. `chart_subject_deletion_tombstones` — verified-deletion receipts
--   5. `chart_subject_deletion_disputes`   — deletion-scope dispute → DR hook
--
-- ── COLUMN CHOICES BEYOND THE ROADMAP ONE-LINER ────────────────────────────────
-- The roadmap row names: subject_kind · consent_document_ref · granted/withdrawn ·
-- anonymization_choice DEFAULT anonymous · redaction_requests ·
-- vulnerable_exclusion_flag · verified_deletion_at. Two columns are added on top,
-- because "native_self is defined STRICTLY" is otherwise unenforceable — a row
-- that merely SAYS `subject_kind='native_self'` would be a self-certification,
-- and self-certification is exactly the A9 abuse path:
--   · `subject_principal_id`  — WHO the subject is. `native_self` holds only when
--       this equals `charts.owner_id`, i.e. the subject IS the account holder.
--   · `guardian_principal_id` — the §3.5.F minor-guardian carve-out, named
--       explicitly rather than inferred. A minor chart serves ONLY to this
--       principal, and NEVER enters a cohort.
-- `consent_state` is stored explicitly rather than derived from
-- granted_at/withdrawn_at nullity, so the CHECK constraints below make an
-- inconsistent pair (withdrawn with no withdrawn_at) impossible at the DB level
-- rather than merely unlikely in application code.
--
-- ── APPEND-ONLY, PER PPR-26 ────────────────────────────────────────────────────
-- "Safety decisions, retractions, and consent transitions MUST be written
-- append-only (INSERT-only grant or hash chain)." This migration takes the
-- hash-chain option (the INSERT-only grant depends on the §7 role migration,
-- which is a different lane): `chart_subject_consent_events` carries
-- prev_hash/entry_hash, and UPDATE/DELETE on it are blocked by triggers. The
-- chain is a REAL detector, not a claim (CLAUDE.md §N.8): `verifyConsentChain()`
-- in `platform/src/lib/pariprashna/consent/hash_chain.ts` recomputes every link
-- and reports the first index that fails, so tampering has a code path that
-- makes the signal read false. The same append-only trigger guards the
-- tombstone table — a deletion receipt that could be edited under the serving
-- credential would not be a receipt.
--
-- ── HASHING CONVENTION ─────────────────────────────────────────────────────────
-- sha256 hex over unit-separator (0x1F) joined canonical fields, matching the
-- existing house idiom (`platform/python-sidecar/services/w2g/fingerprint.py`
-- uses the same separator guard so "ab|c" and "a|bc" cannot collide;
-- `platform/src/lib/lel/prospective_ledger.ts` uses the same version-tag-first
-- ordered-field-join shape). No new convention is invented here.
--
-- ── FLAG-OFF ON ARRIVAL ────────────────────────────────────────────────────────
-- These tables exist but nothing reads them in production until the
-- `SUBJECT_CONSENT_ENFORCEMENT` feature flag is flipped ON
-- (`platform/src/lib/config/feature_flags.ts`, DEFAULT false). Applying this
-- migration is therefore behavior-neutral: five empty tables, zero reads.
--
-- ── ROLLBACK (non-destructive) ─────────────────────────────────────────────────
-- Purely additive. Dropping the five tables (in the reverse order of the DOWN
-- block at the foot of this file) removes exactly what this migration added and
-- nothing else. No existing row anywhere is touched by this migration.

BEGIN;

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. chart_subject_consent — the consent record
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS chart_subject_consent (
  chart_id                   UUID        PRIMARY KEY REFERENCES charts(id) ON DELETE CASCADE,
  subject_kind               TEXT        NOT NULL
                                         CHECK (subject_kind IN ('native_self', 'cohort', 'test')),
  subject_principal_id       TEXT        NULL,
  guardian_principal_id      TEXT        NULL,
  consent_document_ref       TEXT        NULL,
  consent_state              TEXT        NOT NULL DEFAULT 'granted'
                                         CHECK (consent_state IN ('granted', 'withdrawn')),
  granted_at                 TIMESTAMPTZ NULL,
  withdrawn_at               TIMESTAMPTZ NULL,
  anonymization_choice       TEXT        NOT NULL DEFAULT 'anonymous'
                                         CHECK (anonymization_choice IN ('anonymous', 'attributed')),
  redaction_requests         JSONB       NOT NULL DEFAULT '[]'::jsonb,
  vulnerable_exclusion_flag  BOOLEAN     NOT NULL DEFAULT FALSE,
  verified_deletion_at       TIMESTAMPTZ NULL,
  recorded_by_principal_id   TEXT        NULL,
  created_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),

  -- A state and its timestamp cannot disagree.
  CONSTRAINT chart_subject_consent_granted_ts_chk
    CHECK (consent_state <> 'granted'   OR granted_at   IS NOT NULL),
  CONSTRAINT chart_subject_consent_withdrawn_ts_chk
    CHECK (consent_state <> 'withdrawn' OR withdrawn_at IS NOT NULL),
  -- native_self is a claim about WHOSE data this is; it must name the subject
  -- or it cannot be strictly checked at entitlement resolution.
  CONSTRAINT chart_subject_consent_native_self_subject_chk
    CHECK (subject_kind <> 'native_self' OR subject_principal_id IS NOT NULL),
  -- A cohort subject without a consent document is precisely the state §3.5.D
  -- forbids: there is no such thing as an undocumented third-party consent.
  CONSTRAINT chart_subject_consent_cohort_document_chk
    CHECK (subject_kind <> 'cohort' OR consent_document_ref IS NOT NULL),
  -- Verified deletion is a consequence of withdrawal; it cannot precede one.
  CONSTRAINT chart_subject_consent_deletion_requires_withdrawal_chk
    CHECK (verified_deletion_at IS NULL OR consent_state = 'withdrawn'),
  CONSTRAINT chart_subject_consent_redaction_array_chk
    CHECK (jsonb_typeof(redaction_requests) = 'array')
);

CREATE INDEX IF NOT EXISTS chart_subject_consent_subject_kind_idx
  ON chart_subject_consent (subject_kind);
CREATE INDEX IF NOT EXISTS chart_subject_consent_state_idx
  ON chart_subject_consent (consent_state);
CREATE INDEX IF NOT EXISTS chart_subject_consent_subject_principal_idx
  ON chart_subject_consent (subject_principal_id)
  WHERE subject_principal_id IS NOT NULL;

COMMENT ON TABLE chart_subject_consent IS
  'NCD-9 / PPR-14. One row per chart-as-subject. Absence of a row is itself '
  'meaningful: with SUBJECT_CONSENT_ENFORCEMENT ON, a chart with no row serves '
  'NO L2+ interpretive output — a designed refusal, not an error.';
COMMENT ON COLUMN chart_subject_consent.subject_kind IS
  'native_self | cohort | test. native_self is STRICT: honored only when '
  'subject_principal_id = charts.owner_id (the subject IS the native), or via '
  'the §3.5.F minor-guardian carve-out. A self-certified native_self row whose '
  'subject_principal_id does not match is REFUSED at entitlement resolution and '
  'logged to chart_subject_exclusions — it does not silently pass.';
COMMENT ON COLUMN chart_subject_consent.anonymization_choice IS
  'DEFAULT anonymous per §3.5.D.3 — attribution only by ACTIVE election. The '
  'default is load-bearing: a subject who said nothing is anonymous.';
COMMENT ON COLUMN chart_subject_consent.vulnerable_exclusion_flag IS
  'Set at intake by a human. There is deliberately NO automated detector behind '
  'this flag (CLAUDE.md §N.8 — we do not claim a detector we lack).';
COMMENT ON COLUMN chart_subject_consent.verified_deletion_at IS
  'Set ONLY when every in-scope table re-counted to zero after the withdrawal '
  'sweep. NULL means not verified — never a stand-in for "probably done".';
COMMENT ON COLUMN chart_subject_consent.redaction_requests IS
  'JSON array of redaction requests (§3.5.D). Each entry: '
  '{requested_at, scope, note}. Birth data is analytically load-bearing and '
  'cannot be redacted — the consent document states this honestly (§6).';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. chart_subject_consent_events — append-only, hash-chained (PPR-26)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS chart_subject_consent_events (
  event_id            BIGSERIAL   PRIMARY KEY,
  chart_id            UUID        NOT NULL,
  seq                 INTEGER     NOT NULL CHECK (seq >= 1),
  event_kind          TEXT        NOT NULL
                                  CHECK (event_kind IN (
                                    'granted',
                                    'withdrawn',
                                    'redaction_requested',
                                    'anonymization_changed',
                                    'vulnerable_flag_set',
                                    'vulnerable_flag_cleared',
                                    'deletion_verified',
                                    'deletion_disputed',
                                    'deletion_dispute_resolved'
                                  )),
  actor_principal_id  TEXT        NULL,
  payload             JSONB       NOT NULL DEFAULT '{}'::jsonb,
  recorded_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  prev_hash           TEXT        NULL,
  entry_hash          TEXT        NOT NULL,

  CONSTRAINT chart_subject_consent_events_seq_uq UNIQUE (chart_id, seq),
  -- seq 1 opens the chain (prev_hash NULL); every later link must name a parent.
  CONSTRAINT chart_subject_consent_events_genesis_chk
    CHECK ((seq = 1 AND prev_hash IS NULL) OR (seq > 1 AND prev_hash IS NOT NULL)),
  CONSTRAINT chart_subject_consent_events_hash_shape_chk
    CHECK (entry_hash ~ '^[0-9a-f]{64}$')
);

CREATE INDEX IF NOT EXISTS chart_subject_consent_events_chart_seq_idx
  ON chart_subject_consent_events (chart_id, seq);

COMMENT ON TABLE chart_subject_consent_events IS
  'PPR-26 append-only consent-transition ledger. UPDATE and DELETE are blocked '
  'by trigger; integrity is a hash chain (prev_hash → entry_hash) that '
  'verifyConsentChain() re-derives link by link, so tampering has a code path '
  'that makes the signal read false (CLAUDE.md §N.8).';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. chart_subject_exclusions — the excluded-subject register (§3.5.F)
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS chart_subject_exclusions (
  exclusion_id       BIGSERIAL   PRIMARY KEY,
  chart_id           UUID        NOT NULL,
  exclusion_reason   TEXT        NOT NULL
                                 CHECK (exclusion_reason IN (
                                   'minor',
                                   'consent_incapacity',
                                   'vulnerable_subject',
                                   'consent_withdrawn',
                                   'no_consent_row',
                                   'native_self_claim_invalid',
                                   'subject_deleted',
                                   'birth_date_unavailable'
                                 )),
  detector           TEXT        NOT NULL,
  subject_age_years  INTEGER     NULL,
  evidence           JSONB       NOT NULL DEFAULT '{}'::jsonb,
  detected_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  cleared_at         TIMESTAMPTZ NULL,
  cleared_reason     TEXT        NULL,

  CONSTRAINT chart_subject_exclusions_cleared_reason_chk
    CHECK (cleared_at IS NULL OR cleared_reason IS NOT NULL)
);

-- One OPEN row per (chart, reason): the register logs the exclusion, it does not
-- accrete one row per served request. Re-detection touches detected_at only.
CREATE UNIQUE INDEX IF NOT EXISTS chart_subject_exclusions_open_uq
  ON chart_subject_exclusions (chart_id, exclusion_reason)
  WHERE cleared_at IS NULL;
CREATE INDEX IF NOT EXISTS chart_subject_exclusions_chart_idx
  ON chart_subject_exclusions (chart_id);

COMMENT ON TABLE chart_subject_exclusions IS
  'The excluded-subject register (§3.5.F, carried). Exclusions — minors, '
  'consent-incapacity, vulnerable subjects, withdrawn/absent consent — are '
  'LOGGED so the exclusion discipline is itself auditable: no corpus produced, '
  'no analysis performed, but the refusal is visible.';
COMMENT ON COLUMN chart_subject_exclusions.detector IS
  'The specific code path that produced this exclusion (e.g. '
  '"minor_exclusion.isMinorSubject"). A register row names its detector so the '
  'claim can be re-run; a row with no nameable detector must not be written.';
COMMENT ON COLUMN chart_subject_exclusions.subject_age_years IS
  'Computed from the chart''s own birth_date at detection time. NULL when the '
  'exclusion reason is not age-derived, or when birth_date was unavailable — '
  'an honest null, never 0.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. chart_subject_deletion_tombstones — verified-deletion receipts
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS chart_subject_deletion_tombstones (
  tombstone_id          BIGSERIAL   PRIMARY KEY,
  chart_id              UUID        NOT NULL,
  withdrawal_event_seq  INTEGER     NOT NULL,
  table_name            TEXT        NOT NULL,
  table_present         BOOLEAN     NOT NULL,
  row_count             INTEGER     NOT NULL DEFAULT 0 CHECK (row_count >= 0),
  content_hash          TEXT        NULL,
  verified_empty        BOOLEAN     NOT NULL DEFAULT FALSE,
  deleted_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT chart_subject_deletion_tombstones_uq
    UNIQUE (chart_id, withdrawal_event_seq, table_name),
  -- An absent table cannot have had rows, and cannot carry a content hash.
  CONSTRAINT chart_subject_deletion_tombstones_absent_chk
    CHECK (table_present OR (row_count = 0 AND content_hash IS NULL)),
  CONSTRAINT chart_subject_deletion_tombstones_hash_shape_chk
    CHECK (content_hash IS NULL OR content_hash ~ '^[0-9a-f]{64}$')
);

CREATE INDEX IF NOT EXISTS chart_subject_deletion_tombstones_chart_idx
  ON chart_subject_deletion_tombstones (chart_id);

COMMENT ON TABLE chart_subject_deletion_tombstones IS
  'One row per (withdrawal sweep × table). The tombstone proves WHAT was '
  'deleted without retaining any of it: content_hash is sha256 over the sorted '
  'per-row md5 digests of the rows as they stood immediately before deletion. '
  'Audit integrity survives content deletion (§4), and §5''s safe-logging rule '
  'holds — the receipt references C1 content by hash, never duplicates it.';
COMMENT ON COLUMN chart_subject_deletion_tombstones.content_hash IS
  'NULL means the table was absent in this deployment (table_present = false) — '
  'an honest "nothing to hash", never a hash of emptiness passed off as a sweep.';
COMMENT ON COLUMN chart_subject_deletion_tombstones.verified_empty IS
  'TRUE only after a POST-delete re-count returned zero for this table. The '
  'consent row''s verified_deletion_at is set only when every tombstone in the '
  'sweep carries verified_empty = TRUE.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. chart_subject_deletion_disputes — deletion-scope dispute → DR hook
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS chart_subject_deletion_disputes (
  dispute_id          BIGSERIAL   PRIMARY KEY,
  chart_id            UUID        NOT NULL,
  dr_class            TEXT        NOT NULL DEFAULT 'deletion_scope_dispute',
  dr_id               TEXT        NULL,
  opened_by_session   TEXT        NOT NULL,
  parties             JSONB       NOT NULL DEFAULT '[]'::jsonb,
  description         TEXT        NOT NULL,
  requested_scope     JSONB       NOT NULL DEFAULT '[]'::jsonb,
  applied_scope       JSONB       NOT NULL DEFAULT '[]'::jsonb,
  dr_entry_yaml       TEXT        NOT NULL,
  status              TEXT        NOT NULL DEFAULT 'open'
                                  CHECK (status IN ('open', 'resolved', 'escalated', 'reopened')),
  resolution          TEXT        NULL,
  opened_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at         TIMESTAMPTZ NULL,

  CONSTRAINT chart_subject_deletion_disputes_resolution_chk
    CHECK (status <> 'resolved' OR (resolution IS NOT NULL AND resolved_at IS NOT NULL))
);

CREATE INDEX IF NOT EXISTS chart_subject_deletion_disputes_open_idx
  ON chart_subject_deletion_disputes (chart_id)
  WHERE status IN ('open', 'reopened', 'escalated');

COMMENT ON TABLE chart_subject_deletion_disputes IS
  'The §3.5.D.2 hook: "Deletion-scope disputes open a DISAGREEMENT_REGISTER '
  'entry." DISAGREEMENT_REGISTER_v1_0.md is an append-only MARKDOWN artifact '
  'that a governance session appends — a runtime web process cannot and must '
  'not commit to it. So this table holds the fully-formed entry (dr_entry_yaml '
  'is the exact §2-schema YAML block to append) and BLOCKS the deletion sweep '
  'while any row for the chart is open/reopened/escalated. dr_id is filled in '
  'by the governance session that lands the entry; NULL means "not yet '
  'registered" — an honest gap, visible rather than assumed.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. Append-only enforcement (PPR-26) — a real trigger, not a convention
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE OR REPLACE FUNCTION chart_subject_append_only_guard()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION
    'APPEND_ONLY_VIOLATION: % on %.% is forbidden (PPR-26 — consent transitions '
    'and deletion receipts are append-only)',
    TG_OP, TG_TABLE_SCHEMA, TG_TABLE_NAME
    USING ERRCODE = 'raise_exception';
END;
$$;

DROP TRIGGER IF EXISTS trg_chart_subject_consent_events_append_only
  ON chart_subject_consent_events;
CREATE TRIGGER trg_chart_subject_consent_events_append_only
  BEFORE UPDATE OR DELETE ON chart_subject_consent_events
  FOR EACH ROW EXECUTE FUNCTION chart_subject_append_only_guard();

DROP TRIGGER IF EXISTS trg_chart_subject_deletion_tombstones_append_only
  ON chart_subject_deletion_tombstones;
CREATE TRIGGER trg_chart_subject_deletion_tombstones_append_only
  BEFORE DELETE ON chart_subject_deletion_tombstones
  FOR EACH ROW EXECUTE FUNCTION chart_subject_append_only_guard();

-- Note the asymmetry, deliberately: the tombstone table blocks DELETE but
-- permits UPDATE, because `verified_empty` is set by the POST-delete re-count in
-- the same sweep. The receipt may be completed; it may never be erased.

COMMIT;

-- ═══════════════════════════════════════════════════════════════════════════════
-- DOWN (manual rollback) — purely additive migration; this removes exactly what
-- was added and nothing else. Not expected to be needed.
-- ═══════════════════════════════════════════════════════════════════════════════
--
--   DROP TRIGGER IF EXISTS trg_chart_subject_deletion_tombstones_append_only
--     ON chart_subject_deletion_tombstones;
--   DROP TRIGGER IF EXISTS trg_chart_subject_consent_events_append_only
--     ON chart_subject_consent_events;
--   DROP FUNCTION IF EXISTS chart_subject_append_only_guard();
--   DROP TABLE IF EXISTS chart_subject_deletion_disputes;
--   DROP TABLE IF EXISTS chart_subject_deletion_tombstones;
--   DROP TABLE IF EXISTS chart_subject_exclusions;
--   DROP TABLE IF EXISTS chart_subject_consent_events;
--   DROP TABLE IF EXISTS chart_subject_consent;
