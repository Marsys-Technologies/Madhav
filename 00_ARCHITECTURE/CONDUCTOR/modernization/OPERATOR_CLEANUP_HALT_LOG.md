---
artifact: OPERATOR_CLEANUP_HALT_LOG
plan: OPERATOR_CLEANUP_PLAN_v1_0.md
plan_version: 1.1
status: HALTED
halt_at: 2026-05-28T17:18:00+05:30
halt_phase: C
halt_step: C2 (migration 086)
seal_tag: platform-modernization-sealed-v1.0
seal_commit: ab7e1a9509e8a6b426975e53803229303ea86ef4
head_at_halt: 3d195bd7
pre_halt_snapshot: cloudsql-backup-1779968691961
disposition: NATIVE_REVIEW_REQUIRED
supersedes: prior Phase-0 halt log (this session) — Phase 0 was fully discharged at HEAD 3d195bd7
---

# Operator Cleanup — Halt Log

> **Note on supersession.** The prior content of this file recorded a Phase-0 halt from an earlier
> session attempt (terraform CLI absent, smoke env vars unset, working tree dirty, etc.). All of
> those prereqs were discharged in this session before any phase ran (R1–R7 of Phase 0; see
> `OPERATOR_CLEANUP_PROGRESS.md` for the per-check evidence). The Phase-0 halt is closed. This file
> now records the **new** halt at Phase C, step C2.

## §1. Halt point

Phase C — step **C2**, applying migration `086_l25_chart_id_ayanamsha_keyed.sql` to the production
`amjis-postgres` instance.

```
psql:platform/migrations/086_l25_chart_id_ayanamsha_keyed.sql:33:
  NOTICE: relation "charts" already exists, skipping
psql:platform/migrations/086_l25_chart_id_ayanamsha_keyed.sql:35:
  ERROR:  column "role" does not exist
```

The migration's `BEGIN ... COMMIT` block auto-rolled back at the failing statement (psql run with
`ON_ERROR_STOP=1`). No partial 086 changes were applied.

## §2. Root cause — schema-design impedance

Migration 086 was authored assuming a greenfield `charts` table with the modernization-era shape:

```sql
CREATE TABLE IF NOT EXISTS charts (
  chart_id        TEXT PRIMARY KEY,
  subject_label   TEXT NOT NULL,
  datetime_iso    TEXT NOT NULL,
  tz_offset_hours NUMERIC NOT NULL,
  latitude_deg    NUMERIC NOT NULL,
  longitude_deg   NUMERIC NOT NULL,
  place_name      TEXT NOT NULL,
  role            TEXT NOT NULL DEFAULT 'tertiary'
                  CHECK (role IN ('native','tertiary','fixture')),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_charts_role ON charts(role);
```

But the production `charts` table is the legacy chart-records table with a completely different
shape (it pre-dates the modernization arc):

| column | type | source |
|---|---|---|
| id | uuid PK | pre-modernization |
| client_id | text | pre-modernization |
| name | text | pre-modernization |
| birth_date | date | pre-modernization |
| birth_time | time | pre-modernization |
| birth_place | text | pre-modernization |
| birth_lat | numeric | pre-modernization |
| birth_lng | numeric | pre-modernization |
| ayanamsa | text | pre-modernization |
| house_system | text | pre-modernization |
| created_at | timestamptz | pre-modernization |
| owner_id | text | **added by mig 081 (Phase C this session)** |
| subject_name | text | **added by mig 081 (Phase C this session)** |

Because the table already exists, `CREATE TABLE IF NOT EXISTS` is a no-op — the new-shape columns
(`chart_id`, `subject_label`, `datetime_iso`, …, `role`) are **never created**. The very next
statement (`CREATE INDEX … ON charts(role)`) then fails because no `role` column exists.

`charts` is **not empty** — it holds 1 production row (the native chart, FORENSIC identity
`362f9f17-95a5-490b-a5a7-027d3e0efda0`) and is referenced by every downstream read in production. A
drop-and-recreate is not safe operator territory.

Migration 086 also references `charts(chart_id)` as a foreign-key target later
(`ADD COLUMN ... chart_id TEXT REFERENCES charts(chart_id)` on `chart_facts` at line 40 and on
`l25_msr_signals` at line 79). The legacy `charts` has PK `id`, not `chart_id`, so those FKs would
fail even if the step-35 index were patched.

This is a **fundamental schema-design impedance** between the modernization arc's assumed greenfield
shape and the legacy production schema. It cannot be remediated by an inline psql patch from this
session. It requires either:
- a pre-086 reconciliation migration that aligns the legacy `charts` to the modernization shape
  (column adds + chart_id backfill from id + PK swap), **or**
- a rewrite of 086 to **additively extend** the legacy `charts` (ALTER TABLE …) without re-declaring it.

## §3. State at halt

### Applied (5 of 11 — additive + idempotent; safe to leave in place)

| migration | proof of application |
|---|---|
| 081_chart_grants_and_owner_id.sql | `chart_grants` table present; `charts.owner_id` + `charts.subject_name` present |
| 082_role_rename_client_to_guest.sql | `profiles` rows with `role='guest'` present |
| 083_charts_rls.sql | `pg_class.relrowsecurity = true` for `charts` |
| 084_runtime_config.sql | `runtime_config` table present |
| 085_gate_change_log.sql | `gate_change_log` table present |

### NOT applied (6 of 11 — pending native decision)

| migration | reason |
|---|---|
| 086_l25_chart_id_ayanamsha_keyed.sql | schema conflict (this halt) |
| 087_l25_cdlm_cgm_keyed.sql | depends on 086 schema |
| 088_l25_rm_ucn_keyed.sql | depends on 086 schema |
| 089_l25_legacy_freeze.sql | depends on 086 schema |
| 118_build_events.sql | could apply independently — held per phase discipline |
| 119_calibration_stamps.sql | could apply independently — held per phase discipline |

### NOT applied — explicit gate

| migration | reason |
|---|---|
| 090_drop_mcp_audience_tier.sql | irreversible; C1 grep cleared by spirit-read (no live SQL projection touches `mcp_api_keys.audience_tier`) — see §6 — but C4 cannot run while the C batch is half-applied |

## §4. Post-halt smoke (production)

| check | result |
|---|---|
| `GET /api/conversations?chartId=<native>` | **200** |
| `GET /api/pyramid?chartId=<native>` | **200** |
| Cloud Run revision | `amjis-web-00427-vsk` (unchanged) |

Production is healthy on the post-081-085 schema. RLS on `charts` (083) is now active — runtime
support for the `app.principal_id` GUC plumbing is in place; service-role bypass via NULL principal
preserves the migration runner + super_admin paths.

## §5. Rollback anchor

A pre-Phase-C snapshot was taken before any migration ran:

- **Backup ID:** `1779968691961`
- **Started:** `2026-05-28T11:44:51.971Z`
- **Description:** `pre-Phase-C migrations 081-090,118,119`

Restore path (if native decides to roll back the 5 applied additive migrations):

```sh
gcloud sql backups restore 1779968691961 \
  --restore-instance=amjis-postgres \
  --project madhav-astrology
```

Not restored automatically — the 5 applied migrations are additive (no data destruction) and a
restore would itself be a service blip without buying anything. The decision is the native's.

## §6. C1 (audience_tier grep) note — plan v1.2 candidate

The plan's literal C1 gate (`grep -rn "audience_tier" platform platform-mcp` → 0 live references)
does **not** pass: 63 live source files reference the string. The risk-bearing gate (live
**SELECT/INSERT** of `mcp_api_keys.audience_tier` in production code paths) **does** pass:

| live SQL site touching `mcp_api_keys` | references `audience_tier`? |
|---|---|
| `platform/src/lib/mcp/auth.ts:97-100` (SELECT key_id, key_hash, user_uid FROM mcp_api_keys …) | no |
| `platform/src/app/api/mcp/keys/route.ts:35-44` (SELECT … FROM mcp_api_keys …) | no |
| `platform/src/app/api/mcp/keys/[key_id]/route.ts:27` (SELECT key_id, user_uid, revoked_at …) | no |
| `platform/src/app/api/mcp/keys/route.ts:109` (INSERT INTO mcp_api_keys …) | no |

The 63 raw hits are: (a) excision-marker comments in `platform-mcp/src/auth.ts`,
`platform/src/lib/mcp/auth.ts`, `platform/src/app/api/mcp/keys/route.ts` (Stream A 3.tier_excision
audit trail); (b) the in-memory `plan.audience_tier` field on the LLM query plan (a separate
object — not the `mcp_api_keys` column); (c) prompt templates, READMEs, schemas describing the
historical shape.

Recommendation: replace the literal C1 grep with a SQL-projection-aware grep
(`grep -rn "SELECT .* audience_tier .* FROM mcp_api_keys" + "INSERT INTO mcp_api_keys" +
"UPDATE mcp_api_keys SET audience_tier"`) so the gate measures the actual risk surface.

## §7. Phases beyond C

Per kickoff discipline ("Any phase smoke red → auto-rollback that phase + halt + write
OPERATOR_CLEANUP_HALT_LOG.md") the session stops here. Phases D–M are pending the native's
disposition on §2.

**Phase D is structurally independent** of Phase C — the 5 terraform modules + monitoring + AR +
secrets-inventory do not touch `charts` or any table in the C batch. Phase D plans are clean (R4
confirmed: `cloud_tasks: 4 to add`, `memorystore: 1 to add`, `scheduler: 2 to add`,
`edge: 8 to add`, `iam: 22 to add`).

- Phase E (BUILD_TRIGGER) depends on D1+D2 only; not on C.
- Phase F (live answer:eval) depends on a stable runtime; the post-081-085 runtime is stable per §4.
- Phase J depends on Phase D infrastructure but is independent of Phase C migrations 086-090/118/119.

This is recorded for the native's call. The session is **not** unilaterally resuming.

## §8. Provenance notes (for the plan v1.2 author)

1. **No separate staging DB.** Only one Cloud SQL instance exists (`amjis-postgres`). The plan's
   "staging → prod" framing for Phase C has no infra anchor. The plan v1.1 §3 says "C1 grep fails
   → halt before mig 090"; the kickoff step #25 says "halt past C1" — stricter than the plan.
   v1.2 should reconcile.
2. **Migration 086 needs an additive rewrite** or a pre-086 charts-shape-alignment migration.
3. **C1 grep brittleness** — see §6.
4. **Hygiene gap fixed in this run:** `.gitignore` did not previously exclude `**/.terraform/` or
   `**/.terraform.lock.hcl`; commit `3d195bd7` added them.
5. **GCS state bucket created this run:** `gs://madhav-astrology-tf-state` (asia-south1, uniform
   BLA, 7-day soft delete) — it did not exist pre-Phase-0; R3 created it.

## §9. Next operator action (when ready)

1. Native decides §2 disposition (rewrite 086 vs. pre-stage alignment vs. drop C from this pass).
2. If rewrite: amend the plan to v1.2, append a remediation migration (e.g.
   `086a_charts_align.sql` that ALTERs the legacy `charts` to chart_id PK + role column with
   backfill from existing data), then re-kick the same prompt — it will read this halt log and
   `OPERATOR_CLEANUP_PROGRESS.md` and resume from C2 with the new 086 path.
3. If "skip C, do D–M now": amend the kickoff to permit it, then re-kick.

End of halt log.
