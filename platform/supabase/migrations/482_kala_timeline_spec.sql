-- Migration 482: kala_timeline_spec — the renderer-agnostic timeline spec (ṢAḌ-DARŚANA W2,
--                Lane E, stage 8, registry item 27)
-- =============================================================================
-- Spec: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
--        KALA_W2_FIELD_DESIGN_v1_0.md` §7.1 (the `kala_timeline_spec/1` JSON shape) and
--        §9.3 (the migration table, which reserves 482 for this family).
--
-- ── SCOPE NOTE (read before "fixing" this file) ──────────────────────────────────────
-- §9.3's row for 482 lists TWO tables: `kala_timeline_spec` AND `kala_field_snapshots`.
-- Only the first is created here, deliberately. §0's lane table — the anti-collision
-- contract, which is the authority on ownership — assigns `kala_field_snapshots` to
-- **Lane C** (stage 4/5 field assembly), and Lane E to `kala_timeline_spec`. Where §9.3's
-- convenience grouping and §0's ownership table disagree, §0 wins: a lane never creates
-- another lane's table. `kala_field_snapshots` therefore lands in one of Lane C's
-- migrations (478/480 range). This is recorded here, not silently omitted.
--
-- ── WHAT THIS TABLE IS FOR ───────────────────────────────────────────────────────────
-- The six Kāla views (NOW / AHEAD / ELECT / STORY / PRIORITIZE / EXPLAIN) can serve a
-- machine-renderable timeline instead of prose. §7.1 makes it OPT-IN (a flag; MCP token
-- budgets do not pay for it by default) and PERSISTED — persisted specifically so the
-- spec is deterministic and hash-replayable, and so the portal serialises a stored blob
-- straight through rather than recomputing a second, possibly divergent, view of the
-- field. Every `intervals[].id` IS a `kala_field_windows.window_id`, which is the item-44
-- `authority_basis` value: the spec cites the field's windows, it never computes its own
-- (SHAD_DARSHANA_BRIEF_v2_0.md §7, SINGLE TEMPORAL AUTHORITY rail).
--
-- ── B.10 / PROSE RULE ────────────────────────────────────────────────────────────────
-- `spec` holds computed values and SHORT deterministic labels only. It carries no
-- composed prose: the argument composer is template-over-computed-data at SERVING time
-- (brief §7 "B.10 prose rule"). A future column holding a generated paragraph would be a
-- contract violation, not an enhancement.
--
-- ── CIRCULARITY GUARD ────────────────────────────────────────────────────────────────
-- Stage 8 is INSIDE the field-hash boundary (design §2's diagram): it is a pure function
-- of stages 0–6.5 and reads no LEL. `field_snapshot_id` is stored so the guard's dynamic
-- half can assert byte-identity of this table's rows across an LEL mutation.
--
-- Idempotency (§N.3, L1+ = per-chart delete-then-insert): the writer deletes
-- WHERE chart_id = %s before inserting. The UNIQUE key below is the natural key.
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS kala_timeline_spec (
    id                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chart_id          UUID        NOT NULL,
    -- which view this spec was generated for; matches §7.1's `generated_for`
    generated_for     TEXT        NOT NULL
                        CHECK (generated_for IN ('now','ahead','elect','story','priority','explain')),
    spec_version      TEXT        NOT NULL DEFAULT 'kala_timeline_spec/1',
    field_snapshot_id TEXT        NOT NULL,
    weights_version   TEXT        NOT NULL,
    -- the whole §7.1 document, verbatim, serialised straight through by the views
    spec              JSONB       NOT NULL,
    -- denormalised counts so a cockpit/coverage read never has to parse the blob
    n_tracks          INTEGER     NOT NULL DEFAULT 0 CHECK (n_tracks    >= 0),
    n_intervals       INTEGER     NOT NULL DEFAULT 0 CHECK (n_intervals >= 0),
    n_points          INTEGER     NOT NULL DEFAULT 0 CHECK (n_points    >= 0),
    n_bands           INTEGER     NOT NULL DEFAULT 0 CHECK (n_bands     >= 0),
    -- LAW ZERO: an empty spec is served with a reason, never as a populated-looking
    -- hollow envelope. NULL iff the spec is non-empty.
    empty_reason      TEXT,
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT kala_timeline_spec_uk UNIQUE (chart_id, generated_for, field_snapshot_id),
    -- Earned-Signal (§N.8): `empty_reason` must be present exactly when the spec has no
    -- renderable content, so "empty" can never be read as "computed and genuinely quiet".
    CONSTRAINT kala_timeline_spec_empty_reason_ck CHECK (
        (n_intervals + n_points + n_bands = 0) = (empty_reason IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_kala_timeline_spec_chart
    ON kala_timeline_spec (chart_id, generated_for);
CREATE INDEX IF NOT EXISTS idx_kala_timeline_spec_snapshot
    ON kala_timeline_spec (field_snapshot_id);

COMMENT ON TABLE kala_timeline_spec IS
  'ṢAḌ-DARŚANA W2 item 27 — the renderer-agnostic `kala_timeline_spec/1` document per '
  'view per field snapshot (KALA_W2_FIELD_DESIGN_v1_0.md §7.1). Every intervals[].id is '
  'a kala_field_windows.window_id (the item-44 authority_basis value); the spec cites '
  'field windows and never computes its own. Written by services/ka_kshetra/'
  'stage8_spec.py inside ka_kshetra''s stage8 substeps. Contains NO composed prose '
  '(brief §7 B.10 prose rule) — labels and computed values only.';

COMMENT ON COLUMN kala_timeline_spec.field_snapshot_id IS
  'The §7.4 field hash this spec was rendered from. Part of the natural key, so a rebuild '
  'under a new snapshot adds a row rather than silently overwriting the old rendering.';
COMMENT ON COLUMN kala_timeline_spec.empty_reason IS
  'LAW ZERO honest-empty. Non-NULL exactly when intervals+points+bands is empty; carries '
  'the machine-readable reason (e.g. ''honest_empty:no_window_exceeds_null_threshold'').';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — migrate.ts is forward-apply-only; run this by hand):
--   BEGIN;
--   DROP TABLE IF EXISTS kala_timeline_spec;
--   COMMIT;
-- =============================================================================
