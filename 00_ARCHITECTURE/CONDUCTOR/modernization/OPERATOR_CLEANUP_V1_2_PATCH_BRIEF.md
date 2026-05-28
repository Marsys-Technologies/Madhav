---
artifact: OPERATOR_CLEANUP_V1_2_PATCH_BRIEF
status: DEFERRED
plan: OPERATOR_CLEANUP_PLAN_v1_0.md
plan_version: 1.2
parent_halt_log: OPERATOR_CLEANUP_HALT_LOG.md
parent_progress: OPERATOR_CLEANUP_PROGRESS.md
deferred_at: 2026-05-28
deferred_from: Phase C2 (migration 086) of the post-seal operator cleanup
seal_tag: platform-modernization-sealed-v1.0
seal_commit: ab7e1a9509e8a6b426975e53803229303ea86ef4
pre_phase_c_snapshot: cloudsql-backup-1779968691961
expose_to_chat: false
---

# Post-Seal Operator Cleanup — v1.2 Follow-On Patch Brief

This brief describes the work deferred from the 2026-05-28 cleanup session at the Phase C2 halt
boundary. It runs as its own single-session patch when ready. The parent session proceeds with
Phases D–M unaltered.

## §1 — Why this exists

Migration `086_l25_chart_id_ayanamsha_keyed.sql` was authored against the modernization arc's
greenfield `charts` shape (`chart_id TEXT PRIMARY KEY`, `role TEXT`, `datetime_iso TEXT`, …) but
prod `charts` is the pre-modernization legacy table (`id UUID PK`, `birth_date DATE`,
`birth_time TIME`, no `chart_id`, no `role`, no `datetime_iso`). `CREATE TABLE IF NOT EXISTS` is a
no-op against the legacy table, so the new-shape columns are never created and the next statement
(`CREATE INDEX idx_charts_role ON charts(role)`) fails with `column "role" does not exist`. The
migration's transaction auto-rolled back; no partial state.

Migration 086 also references `charts(chart_id)` as a foreign-key target later (line 40 on
`chart_facts.chart_id`; line 79 on `l25_msr_signals.chart_id`). The legacy PK is `id`, not
`chart_id`, so those FKs would still fail even after the index step is patched.

The fix is structural — it cannot be inline-patched from the parent cleanup session.

## §2 — Scope

(a) **Author migration `086_0_charts_align.sql`** (numbered to land before `086`; if that number
collides with prior history, fall back to `089a_charts_align.sql` or another free slot that
sequences before the first 086-family migration in the apply order). The migration is **additive
and idempotent**:

```sql
BEGIN;

-- Bring the legacy charts table into modernization-arc shape, non-destructively.

ALTER TABLE charts
  ADD COLUMN IF NOT EXISTS chart_id          UUID,
  ADD COLUMN IF NOT EXISTS role              TEXT,
  ADD COLUMN IF NOT EXISTS created_at_iso    TIMESTAMPTZ;

-- Backfill chart_id from existing UUID PK (id) one-to-one.
UPDATE charts
   SET chart_id = id
 WHERE chart_id IS NULL;

-- Backfill role to 'native' for the single existing prod row (FORENSIC native chart),
-- 'tertiary' for any others. Refine as needed before apply.
UPDATE charts
   SET role = CASE
                WHEN id::text = '362f9f17-95a5-490b-a5a7-027d3e0efda0' THEN 'native'
                ELSE 'tertiary'
              END
 WHERE role IS NULL;

-- Backfill created_at_iso from existing created_at (timestamptz).
UPDATE charts
   SET created_at_iso = created_at
 WHERE created_at_iso IS NULL;

-- Tighten the new columns to NOT NULL now that backfill is complete.
ALTER TABLE charts
  ALTER COLUMN chart_id        SET NOT NULL,
  ALTER COLUMN role            SET NOT NULL,
  ALTER COLUMN created_at_iso  SET NOT NULL;

-- Make chart_id uniquely targetable as an FK destination.
CREATE UNIQUE INDEX IF NOT EXISTS uq_charts_chart_id ON charts(chart_id);

-- Role lookup index (matches mig 086 step-35 intent).
CREATE INDEX IF NOT EXISTS idx_charts_role ON charts(role);

-- CHECK constraint on role (matches mig 086 line 53 intent).
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'charts_role_check'
  ) THEN
    ALTER TABLE charts
      ADD CONSTRAINT charts_role_check CHECK (role IN ('native','tertiary','fixture'));
  END IF;
END $$;

COMMIT;
```

Notes on the design:
- `chart_id` is `UUID`, not `TEXT`, so the FK target type matches the legacy PK type (UUID) and
  joins remain index-friendly. The mig 086 family must be patched correspondingly (the original
  used `TEXT`); a one-line search-and-replace per FK declaration suffices.
- `IF NOT EXISTS` and the `DO $$ … EXISTS` guard on the CHECK make the migration safe to
  re-apply.
- Backfill leaves the legacy columns (`birth_date`, `birth_time`, `birth_place`, etc.) untouched
  for now. Their disposition is downstream — modernization-arc reads target the new columns;
  legacy reads continue to work.

(b) **Confirm FK targets in `086` lines 40 and 79 land cleanly** against the aligned schema.
After the align migration runs, `charts(chart_id)` resolves to a real, unique-indexed column;
both FKs from `chart_facts.chart_id → charts(chart_id)` and
`l25_msr_signals.chart_id → charts(chart_id)` then create without error. If the original 086
declared the FK column as `TEXT REFERENCES charts(chart_id)`, change those to `UUID REFERENCES
charts(chart_id)` to match the aligned type.

(c) **Re-apply the deferred migrations to prod** in this order (no staging instance exists; the
parent halt log §8.1 records this fact; apply directly to prod with the snapshot rollback anchor
in place):

```
086_0_charts_align.sql   (the align migration above)
086_l25_chart_id_ayanamsha_keyed.sql   (with FK type fix per (b))
087_l25_cdlm_cgm_keyed.sql
088_l25_rm_ucn_keyed.sql
089_l25_legacy_freeze.sql
118_build_events.sql
119_calibration_stamps.sql
090_drop_mcp_audience_tier.sql        (LAST — irreversible; pre-flight C1 grep must pass first)
```

Take a fresh Cloud SQL backup before the run; smoke after each migration (full vitest +
representative chat query).

(d) **Run the Phase J5 `l25_msr_signals` HASH partition** (deferred from the parent session). The
parent session's J5 lands `chart_facts` HASH, `query_trace_steps` RANGE, `mcp_predictions` RANGE.
This patch session adds the fourth target:

- `l25_msr_signals` → HASH by `chart_id`, 8 buckets.

Procedure mirrors the parent Phase J5: create `l25_msr_signals_new` PARTITIONED BY HASH(chart_id);
create 8 partitions; INSERT … SELECT idempotent + batched; partition-aware indexes; verify row
counts match; atomic rename old → `l25_msr_signals_pre_partition_archive`, new → live. The
partition key (chart_id) must be in every PRIMARY KEY / UNIQUE constraint on the table — the 086
family keys `l25_msr_signals` by `(chart_id, ayanamsha_id, signal_id)` so this holds by
construction. Keep the archive table for one green production day, then drop in a follow-up
commit.

## §3 — Out of scope

- Anything already closed in the parent run: Phase A (tag), Phase B (Cloud Run env-var cleanup),
  Phase C1 (audience_tier spirit-grep), Phase D (infra applies), Phase E (BUILD_TRIGGER), Phase F
  (live answer:eval baseline), Phase G (secret rotation), Phase H (tracker retirement), Phase I
  (depth-selector doc), Phase J (SQL scale-up + HA + PITR + chart_facts + query_trace_steps +
  mcp_predictions partitions), Phase K (doc + git + CI hygiene), Phase L (optional engine
  hygiene), Phase M (final tag + report). All of these are expected to be GREEN by the time this
  patch session runs.
- The C1 grep policy redesign (live SQL-projection-aware vs. literal string grep) — already noted
  in the parent halt log §6 as a v1.2 candidate; if amending the grep policy belongs in this
  patch, fold it into the C1 pre-flight that precedes mig 090.

## §4 — Halt conditions

- `086_0_charts_align.sql` row counts after backfill must equal the pre-migration `charts` row
  count. Mismatch → halt + auto-rollback.
- Any mig 086–090 / 118 / 119 transaction error → halt at that step (the BEGIN…COMMIT envelope
  auto-rolls back the offending migration; the prior applied ones stay in place by design).
- J5 row-count mismatch on `l25_msr_signals` swap → rename back + halt.

## §5 — Provenance

Authored 2026-05-28 during the post-seal operator cleanup session that halted at Phase C2. Parent
artifacts: `OPERATOR_CLEANUP_PLAN_v1_0.md` (v1.2), `OPERATOR_CLEANUP_KICKOFF.md` (v1.2),
`OPERATOR_CLEANUP_HALT_LOG.md`, `OPERATOR_CLEANUP_PROGRESS.md`.
