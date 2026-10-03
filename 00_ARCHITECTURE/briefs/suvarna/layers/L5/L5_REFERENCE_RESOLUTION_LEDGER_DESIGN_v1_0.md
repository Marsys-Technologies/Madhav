---
artifact: L5_REFERENCE_RESOLUTION_LEDGER_DESIGN
canonical_id: SUVARNA_L5_REFERENCE_RESOLUTION_LEDGER_DESIGN
version: "1.1"
status: "DRAFT — HELD for SS review; design + tests-first only; nothing here is built, migrated or applied"
produced_on: 2026-10-03
produced_in: "Exec Suvarṇa"
plan_item: "TI-l5-ledger-design-001 (SS ruling N-99; Q-L4-01 / Q-L4-02)"
layer: L5 (Mīmāṃsā), reading L4 (Phala)
chart_scope: 482012f1-710e-4a25-994a-93821f5871aa
ruling_implemented: "N-99 (frozen mimamsa_predictions rows never deleted or rewritten; dangling anchor references RECORDED in a computed side ledger written by an L5-side process; an integrity check claims only what its own writer produces) as renumbered/extended by N-104 (1259 widened to ph_nimitta AND mi_bhavisya; 1264 = this ledger; 1265 = DB-enforced immutability; mi_nirdesa approved; dangling predictions still COUNT toward calibration: disclose, do not exclude; mi_bhavisya append-only is a separate writer PR)"
tests: platform/python-sidecar/tests/test_l5_reference_resolution_ledger_design.py
evidence: "/Users/Dev/suvarna-evidence/S_L1/l5_ledger/ (prod_counts.py, prod_counts.json) and /Users/Dev/suvarna-evidence/S_L1/L5_LEDGER_DESIGN_REPORT.md"
inputs_read:
  - "/Users/Dev/suvarna-evidence/A_L4/REPORT.md and A.L4 briefs (PR #3013): ph_nimitta, ph_pramana; Q-L4-01/02/03/05/08"
  - "/Users/Dev/suvarna-evidence/A_L5/out (read-only): mi_bhavisya brief, INDEX CF-L5-02, Q-L5-02, bhav-N1/N2/N3/N7"
  - "00_ARCHITECTURE/L5_SEAL_AND_SHIP_REPORT_v1_0.md"
  - "platform/migrations/347, 680, 682, 990, 991, 1083; platform/scripts/governance/msr_dangling_signal_refs.py"
  - "production, reader role only (SELECT), 2026-10-03"
  - "v1.1: /Users/Dev/suvarna-evidence/S_L1/REVIEW_3023.md (independent review, APPROVE WITH NITS); origin/main platform/scripts/migrate.ts (PROTECTED_PUBLIC_SCHEMA_MIGRATIONS), .github/workflows/deploy.yml (jataka-protected-migrations), /Users/Dev/suvarna-evidence/S_L1/W1_PRIVILEGE_AUDIT.md"
changelog:
  - "1.1 (2026-10-03): review fixes. MED-1 privilege/apply path: the routine migrate role (amjis_app) has USAGE but not CREATE on schema public, so the table DDL needs the protected public-schema window; routine-runnable DML split out (section 4.1, 6.1, 10). MED-2 count_sql placeholder is $1, tested against the repository registry convention. MED-3 DDL CHECK matrix is now exercised on a real throwaway Postgres and the Python twin is cross-validated against it; DDL mutants are killed. MED-4 staleness has ONE definition (hash change OR live-resolution drift) used by D1 and the reader SQL, tested for agreement. Brought to N-104 numbering and rulings. citation_ref is not a once-written witness (mi_bhavisya deletes all manifestation sets on rebuild). Reader hooks corrected (no judgment_flags host in query_predictions; summary over total_matching, not the returned page). reference_rewritten_since_freeze now means reference differs from the freeze id (a blanked reference is a rewrite). Migration hold now matches file CONTENT."
  - "1.0 (2026-10-03): first draft. Ledger table, resolution rules, detector, reader disclosure, migration needs, risks. Production counts measured read-only. Pure-function reference + tests-first in the test file named above."
---

# L5 reference-resolution ledger — design v1.1

## 1. Ruling, scope and non-goals

**Ruling (SS N-99, as renumbered and extended by N-104).** `mimamsa_predictions` rows are the
calibration record of what was predicted. 135 of the 139 rows on the canonical chart cite anchors that
are no longer in `phala_anchors`. Those rows are **never deleted and never rewritten** (N-46 mixed
table: frozen rows are immutable). The gap must be **recorded**, by an **L5-side process**, in a
**computed side ledger** every reader can see. An integrity check **claims only what its own writer
produces**. The N-104 numbering this document follows (taken from the coordinator's summary; I have
not read N-104 itself):

* **1259** (separate worker, widened) removes the global dangling-anchor term from **both**
  `ph_nimitta`'s and `mi_bhavisya`'s integrity SQL; the term becomes this ledger's L5-side
  **reference-resolution detector** — reported, **not build-blocking**.
* **1264** = this ledger's table (additive new table; needs the protected apply path, §4.1).
* **1265** (separate worker) = DB-enforced immutability of the frozen prediction rows.
* The asset name **`mi_nirdesa`** is approved. Rule 3 (`superseded`) stays, labelled as weaker
  evidence. Dangling predictions **still count** toward the calibration gate: this design discloses,
  it does not exclude.
* **`mi_bhavisya` append-only** (never delete/re-stamp a frozen row; manifestation sets too, §2.1) is a
  **separate writer PR**, not this one. The former "1260 / no rebuild may cascade into the frozen rows"
  is, as I read N-104, delivered by 1265 plus that writer PR.

**In scope.** The ledger table; who writes it; the exact resolution rules
(`resolved` / `superseded` / `vanished`) with production counts; the detector; how readers disclose
the gap; the migrations this needs and the privilege/apply path they can actually take; risks and open
questions.

**Not in scope (and not done here).** No writer, no migration file, no orchestrator extension, no
change to `mimamsa_predictions`, `ph_nimitta`, `mi_bhavisya` or any reader. Migrations 1259 and 1265
belong to other workers. This PR is a design document plus a test file containing a *reference*
pure function (test-file only) and strict-xfail holds.

**Two things this design deliberately does not do:** it does not repair or re-point a dangling
reference (a repair is a decision about what was predicted, which is not the ledger's to make), and
it does not exclude dangling predictions from calibration (ruled: they still count; disclose, do not
exclude).

## 2. Evidence (production, reader role, read-only, 2026-10-03)

### 2.1 What the frozen rows hold

* `mimamsa_predictions` (migration 347): PK `(chart_id, prediction_id)`; **no foreign key to
  `phala_anchors`** (so no cascade can reach it from there); 195 rows: **139** canonical,
  **56** on chart `1c826d5a-…`; all 195 `lifecycle_status = 'pending'`.
* **The anchor reference column is `source_pramana_id`** (it stores an anchor id under a
  pramana-shaped name; migration 680 header). `prediction_id` is `'pred_' || <anchor_id at freeze>`
  (`mi_bhavisya.py`). The manifestation set's `citation_ref->>'anchor_id'` also holds the
  anchor id at freeze (139 of 139 equal the `prediction_id` suffix; 195 of 195 over both charts). **That
  witness is not durable:** `mi_bhavisya` deletes *all* `mimamsa_manifestation_sets` of the chart on
  every rebuild (`mi_bhavisya.py`, the unconditional `DELETE FROM mimamsa_manifestation_sets`) and
  re-inserts only for current anchors, so a retained non-pending prediction would lose its
  manifestation row. `prediction_id` itself (the primary key) is the durable witness; the ledger
  prefers the citation when present and falls back to the suffix (§5.1). Manifestation sets must also
  never be deleted — a requirement for the append-only writer PR, passed on by the coordinator.
* **`frozen_bundle_hash` is `sha256(chart_id | prediction_id | emitted_at | formula_version)[:32]`**
  — it commits to the identifiers and a clock, not to the claim or the anchor content
  (A.L5 finding bhav-N2). It cannot be used to prove what an anchor said.
* **Triggers on `mimamsa_predictions`: only `mimamsa_predictions_builder_guard`, `BEFORE INSERT OR
  DELETE`, and only for the role `data_plane_builder` (insert/delete of `pending`/`due` rows only).
  There is no UPDATE trigger and no immutability guard on any column.** The function body is not in
  any file in this repository (searched). Grants: `SELECT` to the read roles, `arwd`/`arw` to
  `role_orchestrator` / `role_ledger_write`, `ard` to `data_plane_builder`.
* **Migration 680 rewrote the reference column of frozen rows.** `source_pramana_id` differs from
  the freeze id (the `prediction_id` suffix) on **191 of 195** rows (135 of 139 canonical; 56 of 56
  on chart `1c826d5a-…`): 680 remapped random anchor ids to deterministic ones with
  `UPDATE mimamsa_predictions SET source_pramana_id = …`. The four rows it left alone are the two
  680 collision pairs (still on their original random ids). So "frozen" has already been broken once,
  by a migration, on the exact column this ledger watches. The ledger therefore stores **both** ids.

### 2.2 How an anchor id is made, and what that allows

`phala_anchor_identity()` (migration 680): UUIDv5 over the grade-free event tuple
`(chart_id, anchor_source, event_type, direction, domain, horizon_tier, window_start, peak_date,
window_end, falsifier)`. Consequences:

* **Same claim ⇒ same id.** After 680, "resolved" is a semantic match, not just a string match:
  the id *is* the claim tuple. A recalibration keeps the id.
* **The tuple cannot be recomputed from a prediction row.** A prediction carries only
  `domain`, `observation_window` (= `window_start`/`window_end`) and `falsifier_jsonb` of the
  ten tuple fields (it lacks `anchor_source`, `event_type`, `direction`, `horizon_tier`,
  `peak_date`; `outcome_claim` embeds three of them only when the anchor had no `karmic_note`).
  So **`superseded` can never be proven by identity; it can only be shown by a claim-key match**
  (§5), and that is a weaker kind of evidence which the ledger labels as such.
* Random ids minted before 680 are unrecoverable once the anchor row is gone: nothing on any
  surviving table maps them to a successor.

### 2.3 What a rebuild does today (why the ledger cannot depend on the rows staying put)

`mi_bhavisya` deletes `mimamsa_predictions` rows with `lifecycle_status IN ('pending','due')` for the
chart and re-inserts from the *current* anchors. All 139 canonical rows are `pending`. **A routine
`mi_bhavisya` rebuild today would silently replace the 139 frozen rows with 4.** The existing
"irreplaceable outcome" guard protects only `confirmed/denied/partial` rows. Closing that gap is the
job of 1265 (DB-enforced immutability) and the separate `mi_bhavisya` append-only writer PR; this
design **assumes both land before the ledger asset is built in production** (open question 3) and is
written so the ledger is correct either way (it records the rows that exist at the moment it runs).

### 2.4 Current anchors (canonical chart)

4 rows in `phala_anchors`: all `anchor_source = 'discovery'`, domains character / health / career /
relationship, window `2026-08-12 … 2026-11-10`, computed `2026-08-13 01:15:55Z`. These are exactly
the 4 resolvable predictions. Chart `1c826d5a-…` has 56 anchors, all referenced.

### 2.5 Measured resolution (the §5 rules, run read-only over production)

Two independent implementations agree — the Python reference function in the test file
(`prod_counts.py`) and a plain SQL statement (`prod_counts.json: parity = true`):

| chart | predictions | resolved | superseded | vanished | basis |
|---|---:|---:|---:|---:|---|
| `482012f1-…` (canonical) | 139 | **4** | **0** | **135** | 4 `id_match_referenced`; 135 `no_match` (0 candidates) |
| `1c826d5a-…` | 56 | 56 | 0 | 0 | 56 `id_match_referenced` |

Of the 135 vanished: 131 had their reference column rewritten by 680 to a deterministic id that no
longer exists; 4 never were. `superseded = 0` because every vanished prediction's
(domain, window, falsifier) differs from all 4 current anchors — the current anchors are a different
set of claims, not successors. Vanished spread: transition 50, career 28, wealth 26,
relationship 17, spirituality 6, character 4, health 4. (Aside, not this design's scope: 12 of the
139 predictions have an observation window that had already ended when they were frozen —
A.L5 notes the same.)

Baseline for before/after checks (read-only, 2026-10-03): frozen-set digest
`md5(string_agg(prediction_id || ':' || frozen_bundle_hash, ',' ORDER BY prediction_id))` =
`fd3d5066c7559757fe76f877930020fd` (139 rows, canonical) and `c9ddb15f912207b62bce1cf7cfe4cac5`
(56 rows, `1c826d5a-…`). §7.4 explains why this digest, and not the ledger, is the only thing that
can show a *deleted* prediction.

## 3. The ledger table

`mimamsa_reference_resolution` — one row per `(chart_id, prediction_id)`. It records, for each
frozen prediction, whether the anchor it was frozen against can still be found, and on what basis.

```sql ddl
CREATE TABLE IF NOT EXISTS mimamsa_reference_resolution (
  chart_id                          uuid        NOT NULL,
  prediction_id                     text        NOT NULL,
  anchor_id_at_freeze               text        NOT NULL,
  freeze_id_source                  text        NOT NULL,
  anchor_id_referenced              text        NOT NULL,
  reference_rewritten_since_freeze  boolean     NOT NULL,
  resolution_status                 text        NOT NULL,
  resolution_basis                  text        NOT NULL,
  resolved_anchor_id                uuid,
  candidate_count                   integer     NOT NULL,
  current_anchor_count              integer     NOT NULL,
  claim_key                         jsonb       NOT NULL,
  prediction_frozen_bundle_hash     text        NOT NULL,
  resolver_version                  text        NOT NULL,
  build_id                          text        NOT NULL,
  resolved_at                       timestamptz NOT NULL,
  PRIMARY KEY (chart_id, prediction_id),
  CONSTRAINT mimamsa_reference_resolution_status_chk
    CHECK (resolution_status IN ('resolved', 'superseded', 'vanished')),
  CONSTRAINT mimamsa_reference_resolution_freeze_src_chk
    CHECK (freeze_id_source IN ('citation_ref', 'prediction_id_suffix', 'source_pramana_id')),
  CONSTRAINT mimamsa_reference_resolution_counts_chk
    CHECK (candidate_count >= 0 AND current_anchor_count >= 0),
  CONSTRAINT mimamsa_reference_resolution_matrix_chk CHECK (
       (resolution_status = 'resolved'
         AND resolution_basis IN ('id_match_referenced', 'id_match_freeze')
         AND resolved_anchor_id IS NOT NULL)
    OR (resolution_status = 'superseded'
         AND resolution_basis = 'claim_key_unique'
         AND resolved_anchor_id IS NOT NULL AND candidate_count = 1)
    OR (resolution_status = 'vanished'
         AND resolution_basis = 'no_match'
         AND resolved_anchor_id IS NULL AND candidate_count = 0)
    OR (resolution_status = 'vanished'
         AND resolution_basis = 'claim_key_ambiguous'
         AND resolved_anchor_id IS NULL AND candidate_count >= 2)
  )
);

CREATE INDEX IF NOT EXISTS idx_mimamsa_reference_resolution_chart_status
  ON mimamsa_reference_resolution (chart_id, resolution_status);

COMMENT ON TABLE mimamsa_reference_resolution IS
  'COMPUTED side ledger (N-99). One row per frozen prediction: can the anchor it was frozen against still be found. '
  'Rebuildable state, not history. Never referenced by, never referencing, and never a writer of the frozen prediction table.';
COMMENT ON COLUMN mimamsa_reference_resolution.anchor_id_at_freeze IS
  'The anchor id the prediction was frozen against (manifestation citation when present, else the prediction_id suffix).';
COMMENT ON COLUMN mimamsa_reference_resolution.anchor_id_referenced IS
  'The live reference column value (source_pramana_id) when the ledger was computed; may differ from the freeze id.';
COMMENT ON COLUMN mimamsa_reference_resolution.claim_key IS
  'Evidence for superseded/ambiguous decisions: domain, window_start, window_end, sha256 of the canonical falsifier.';
```

**Column notes.**

* `anchor_id_at_freeze` / `freeze_id_source`: the required `anchor_id_at_freeze` of N-99. Source
  preference: `citation_ref` (untouched by 680, but *not* durable — §2.1) → `prediction_id_suffix`
  (the primary key, so durable) → `source_pramana_id` (last resort; then the two ids coincide by
  construction and `reference_rewritten_since_freeze` is false). `text`, not `uuid`: it must hold
  whatever was frozen, including a malformed value, without the ledger failing to record it. The
  two witnesses are equal on 195/195 today, so the stored value does not depend on which one was
  used; `freeze_id_source` says which it was.
* `anchor_id_referenced` + `reference_rewritten_since_freeze`: makes the 680 rewrite
  (191/195 rows) visible instead of buried. The flag is true whenever the live reference **differs
  from the freeze id** — including a reference that has been blanked, which is a rewrite too.
* `resolved_anchor_id`: the *current* anchor that satisfied the match (resolved or superseded);
  `NULL` for vanished. `uuid`, so a non-uuid can never be reported as a found anchor.
* `candidate_count`: how many current anchors share the prediction's claim key (evidence for
  superseded and for "ambiguous, so not superseded").
* `current_anchor_count`: how many anchors the chart had when the ledger ran — separates "this
  anchor vanished" from "the chart has no anchors at all" (the canonical chart: 4).
* `prediction_frozen_bundle_hash`: binds the ledger row to the exact frozen row it described, so a
  later replacement of the prediction is visible as staleness (§7).
* `build_id`, `resolved_at`, `resolver_version`: provenance, supplied by the orchestrator context
  (`ctx.build_id`) and the writer; **not** part of the pure function's output (it must stay
  deterministic).

**No foreign keys, anywhere.** Not to `mimamsa_predictions` (a ledger row must be able to outlive
a prediction replaced by a rebuild; an FK would let the ledger block a rebuild or let a rebuild
cascade into the ledger), not to `phala_anchors` (the point of the ledger is that the target may be
gone). `resolved_anchor_id` is a value, not a constraint. A static test on this document fails the
build if a `REFERENCES`, `ON DELETE`, trigger or any mention of `phala_anchors` appears in the
DDL block.

## 4. Immutability stance, grants, RLS

* **The ledger is a computed, rebuildable side table.** It is the opposite of frozen: every run
  replaces the chart's rows (CLAUDE.md §N.3 delete-then-insert per `(chart_id × natural key)`).
  It is state ("what resolves *now*"), not history. It has no immutability trigger and no
  `ON CONFLICT` upsert path.
* **It must never reference-block, cascade or modify `mimamsa_predictions`.** Enforced by
  construction (no FK, no trigger, no DML against the frozen table in any block of this document) and
  by test (`sql_violations`, §9). The writer's `ctx.db_conn` use is limited to `SELECT` on the frozen
  table and `DELETE`/`INSERT` on the ledger.
* **Grants — mirror `mimamsa_predictions`' ACL, the table the disclosure joins to (as measured):**
  `SELECT` to `retrieval_census_ro`, `role_web_serve`, `role_jobs`, `role_sidecar`,
  `nirmana_evidence_ingress_writer`, `suvarna_reader`; `SELECT, INSERT, UPDATE, DELETE` to
  `role_orchestrator`; and — because the builder-role trap recurs (Q-L4-04: `data_plane_builder`
  missing a grant on a table a writer needs) — an explicit grant for **`data_plane_builder`**
  (`SELECT, INSERT, DELETE` is enough for delete-then-insert), with a builder-role test in the
  implementation PR (pattern: `tests/l3/_builder_role.py`). Deliberately **no** grant to
  `role_ledger_write`: that role writes the people-entered ledgers; the ledger is not one.
* **RLS and data classification.** The g1c chart-context policies on the sibling tables are defined
  by `platform/supabase/migrations/576_pariprashna_roles_rls_arm3.sql` (a second migrations
  directory the runner reads), which classes `mimamsa_predictions` and `mimamsa_calibration` as
  **C3 predictive** and walls them; the policies are only *armed* by an operator script
  (`platform/scripts/pariprashna/g1c_arm_rls.sql`, not auto-applied), which is why
  `relrowsecurity = false` today. The ledger carries ids, counts, a domain, a window and a falsifier
  *hash* — no claim text, no outcome — so it is plausibly *not* C3, but its `claim_key` and
  `prediction_id` set describe the predictions. **Classification is an SS decision (open question
  5).** The DDL below follows the sibling policy *shape* so the ledger is not the one table in the
  family with no policy; if SS classes it C3 the migration must also join 576's wall pattern and the
  arm/disarm lists.

```sql ddl
GRANT SELECT ON mimamsa_reference_resolution
  TO retrieval_census_ro, role_web_serve, role_jobs, role_sidecar,
     nirmana_evidence_ingress_writer, suvarna_reader;
GRANT SELECT, INSERT, UPDATE, DELETE ON mimamsa_reference_resolution TO role_orchestrator;
GRANT SELECT, INSERT, DELETE ON mimamsa_reference_resolution TO data_plane_builder;

DROP POLICY IF EXISTS mimamsa_reference_resolution_g1c_chart_context ON mimamsa_reference_resolution;
CREATE POLICY mimamsa_reference_resolution_g1c_chart_context ON mimamsa_reference_resolution
  FOR ALL TO role_web_serve, role_sidecar USING (chart_id = app_chart_context());
DROP POLICY IF EXISTS mimamsa_reference_resolution_g1c_unscoped ON mimamsa_reference_resolution;
CREATE POLICY mimamsa_reference_resolution_g1c_unscoped ON mimamsa_reference_resolution
  FOR ALL TO role_orchestrator, role_ledger_write, role_jobs USING (true);
```

The grants end with an assertion, because a `GRANT` issued by a role that cannot grant emits a WARNING
and succeeds (W1 privilege audit P2): a migration that is a bare `GRANT` can be recorded as applied
and grant nothing. Here `amjis_app` owns the table, so the grants do take effect, but the standing
pattern of 1224/1255 is kept.

```sql ddl
DO $assert$
BEGIN
  IF NOT has_table_privilege('role_orchestrator', 'mimamsa_reference_resolution', 'INSERT')
     OR NOT has_table_privilege('data_plane_builder', 'mimamsa_reference_resolution', 'DELETE')
     OR NOT has_table_privilege('suvarna_reader', 'mimamsa_reference_resolution', 'SELECT') THEN
    RAISE EXCEPTION 'mimamsa_reference_resolution: grants did not take effect';
  END IF;
END
$assert$;
```

### 4.1 Privilege and apply path — the routine migration role cannot create this table

**The problem.** The routine `Apply Routine DB Migrations` job connects as `amjis_app`. Measured
(production, reader role, 2026-10-03; `W1_PRIVILEGE_AUDIT.md` P1; independently rehearsed in
`REVIEW_3023.md`): `has_schema_privilege('amjis_app', 'public', 'CREATE')` is **false**; schema
`public` is owned by `data_plane_schema_owner`, and `amjis_app` holds `USAGE` only. So a
`CREATE TABLE` in `public` run by the routine runner fails with
`permission denied for schema public`. A failing file stops the runner, later-sorting files never
run, and every web/sidecar deploy that `needs` the migrate job is blocked. **The DDL blocks of §3–§4
therefore cannot be applied by the routine runner.** (Superuser rehearsals — including this document's
own earlier validation script — cannot see this; the real-Postgres test in this PR now reproduces the
failure as `amjis_app` and the success inside the window, §9.)

**The protected path (the one already used for 1153–1157 and 1202).**

1. `platform/scripts/migrate.ts`: add the 1264 filename to `PROTECTED_PUBLIC_SCHEMA_MIGRATIONS` (with its
   own window name in `assertGeneralRunnerMayApplyPublicSchema`'s message), so the routine runner
   *refuses it loudly* instead of failing inside the file.
2. `.github/workflows/deploy.yml`: a new `workflow_dispatch` boolean input for this window (proposed
   `l5_reference_ledger_schema_migration`), added to the `if:` of the `jataka-protected-migrations`
   job and to its ascending-order `migrations+=(…)` list, so the job runs
   `migrate.ts --only 1264_…sql` **between** `jataka-schema-capability.ts grant` and `… revoke` (the
   `revoke` step runs on `always()`).
3. The window must be the **capability grant to `amjis_app`** (`DATA_PLANE_MIGRATOR_DATABASE_URL`
   grants `CREATE ON SCHEMA public` temporarily), **not** an execution under an owner role: the ledger
   must be owned by `amjis_app` like its sibling tables, because (a) grants by a non-owner silently
   no-op (audit P2) and (b) the registry/cockpit machinery assumes that owner.
4. **Sequencing consequence.** Once 1264 is in the protected set and merged, the routine runner refuses
   it until the window is dispatched, which holds the `migrate` job (and so deploys) until then. Merge
   and dispatch must be sequenced exactly as for 1153–1157 / 1202.

**Alternatives that avoid `CREATE` — stated and rejected.** (a) run the DDL as the schema-owner role: the
table would be owned by `data_plane_schema_owner`, so `amjis_app`'s later grants no-op (P2) and the
ownership differs from every sibling; (b) store the rows in an existing `amjis_app`-owned table: it
would mix computed side-state into a table with another contract (N-46 mixed-table lesson) and gives
the ledger no table of its own to grant, count or clear; (c) a view: there is nothing to compute it
from once the anchors are gone. The protected window is the recommendation.

**What can run routinely, and what cannot.**

| piece | needs `CREATE` on `public`? | path |
|---|---|---|
| `CREATE TABLE`, index, `COMMENT`, grants, policies, grant assertion (the `ddl` blocks) | yes (`CREATE TABLE`/`CREATE INDEX` in `public`) | **protected window**, migration 1264 |
| `asset_registry` row for `mi_nirdesa`, `natural_key_partition` (the `registry` block) | no — DML on `asset_registry`, owned by `amjis_app` (W1 audit table: the same shape as 1221/1223/1243-rows) | **routine runner**, must sort after 1264 and guard `to_regclass('public.mimamsa_reference_resolution') IS NOT NULL` so a registry row never points at a missing table |
| output-digest spec (990 pattern: DML on `asset_output_digest_specs`, owned by `amjis_app`) | no | **routine runner**, same guard |
| the writer, the pure module, the reader and governance script | n/a (code) | normal PR |

## 5. Resolution rules

Inputs, per chart: every `mimamsa_predictions` row (all lifecycle statuses, including
`chart_context_stale` rows — a stale-context row still holds a reference) and every
`phala_anchors` row **of the same chart**. Anchors never match a prediction of another chart.

### 5.1 The freeze id

`anchor_id_at_freeze` = first available of: `mimamsa_manifestation_sets.citation_ref->>'anchor_id'`
(smallest `channel_id` for determinism; present only while the manifestation set survives, §2.1) →
the part of `prediction_id` after `pred_` (durable: it is the primary key) → `source_pramana_id`.
`freeze_id_source` records which. Because the citation can disappear on a rebuild, the fallback to the
suffix is a normal path, not an error, and the ledger value is the same either way (195/195 equal).

### 5.2 Decision order (first rule that fires wins)

| # | Condition | status | basis | resolved_anchor_id |
|---|---|---|---|---|
| 1 | `source_pramana_id` (lower-cased, trimmed) is the `anchor_id` of a current anchor of the chart | `resolved` | `id_match_referenced` | that anchor |
| 2 | else the freeze id is the `anchor_id` of a current anchor of the chart | `resolved` | `id_match_freeze` | that anchor |
| 3 | else exactly **one** current anchor of the chart has the same claim key | `superseded` | `claim_key_unique` | that anchor |
| 4 | else two or more have the same claim key | `vanished` | `claim_key_ambiguous` | NULL |
| 5 | else | `vanished` | `no_match` | NULL |

**Claim key** = `(domain, window_start, window_end, canonical falsifier)`, compared exactly.
Prediction side: `domain`, `lower(observation_window)`, `upper(observation_window)`,
`falsifier_jsonb`. Anchor side: `domain`, `window_start`, `window_end`, and the anchor's `falsifier`
text passed through the **same projection `mi_bhavisya` applied when freezing** (`NULL`/empty → `{}`;
JSON-parsable text → its parsed value; anything else → `{"raw": <text>}`). All 195 production
`falsifier_jsonb` values have the `{"raw": …}` shape. The ledger stores the key (with the
falsifier hashed) so every superseded/ambiguous decision is auditable from the row alone.

### 5.3 What each status means, and the evidence it needs

* **`resolved`** — the anchor the prediction names exists. Evidence: an id equality, in-chart.
  Because anchor ids are deterministic over the claim tuple (§2.2), id equality means the same
  claim, graded however it is graded now. Rule 2 exists so that a reference column rewritten to a
  *wrong* value (the 680 failure mode) does not hide a freeze id that still exists; the row then
  carries `reference_rewritten_since_freeze = true`.
* **`superseded`** — the named anchor is gone, but **one and only one** current anchor of the chart
  states the same claim by the claim key. This is **weaker evidence than identity** and the row says
  so (`resolution_basis = 'claim_key_unique'`, `candidate_count = 1`). It does *not* assert the
  anchors are "the same prediction"; it asserts that the (domain, window, falsifier) a reader
  would use to compare them match and nothing else competes. `event_type`, `direction`,
  `horizon_tier`, `peak_date`, `anchor_source` are not on the prediction and are not compared (§2.2);
  the implementation PR should consider also comparing the frozen `outcome_claim` against a
  *shared* projection helper factored out of `mi_bhavisya` (open question 2), at the cost of a
  second place that knows the freeze mapping.
  *Considered and rejected:* requiring the successor to be computed after the freeze
  (`computed_at > emitted_at`) — the 680 collision pairs are twin anchors that coexisted, and a twin
  is a legitimate "same claim, different id".
* **`vanished`** — no current anchor of the chart matches. Two bases: `no_match` (nothing shares the
  claim key) and `claim_key_ambiguous` (two or more do, so no honest single successor can be named —
  an honest null beats an invented judgment, CLAUDE.md §N.7 item 6). `current_anchor_count`
  distinguishes "this anchor is gone" from "the chart has no anchors".

### 5.4 Properties the pure function must have (tested in the PR)

Deterministic, no clock, no randomness, no I/O; the same inputs in any order give the same output;
inputs are never mutated and the output never aliases them; exactly one row per prediction; a
duplicate prediction key is an error; output sorted by `(chart_id, prediction_id)`; every row
satisfies the DDL `CHECK` matrix (Python twin `ddl_check_violations`, cross-validated against a
real Postgres, §9.2); it takes no outcome,
calibration, lifecycle or event input (the calibration leak guard is unaffected by construction — it
is a function of reference columns and the anchor table only).

## 6. Who writes it

### 6.1 Asset proposal (frozen orchestrator contract; no orchestrator extension)

* **A new asset, proposed id `mi_nirdesa`** (*nirdeśa*, "indication, reference"; name approved by N-104; do not confuse it with `mi_sambandha`). A `@register("mi_nirdesa")`
  `WriterBase` subclass with a light `run(ctx) -> WriterResult` (≤ a few hundred rows). It runs on
  `ctx.db_conn` and **never commits or closes it**; it does not write `asset_throughput`;
  `chart_id` comes from `ctx.config`; it honours `ctx.dry_run`. Idempotency: per-chart
  delete-then-insert on the ledger only (§N.3). Scope per chart.
* **`depends_on = {mi_bhavisya, ph_nimitta}`** — it reads `mimamsa_predictions`,
  `mimamsa_manifestation_sets` (written by `mi_bhavisya`) and `phala_anchors` (written by
  `ph_nimitta`). Every table a writer reads gets a declared edge; undeclared reads are a standing
  finding class in the A.L3/A.L4/A.L5 briefs.
* **Why not host it in an existing asset.** `mi_bhavisya` writes the frozen rows: putting the
  resolver there couples the ledger's lifecycle to the one writer whose rebuild is the hazard, and
  would make the asset's own integrity SQL vouch for both. `mi_pramana` is the calibration
  computation; reference resolution is not calibration. A separate asset also gives the ledger its
  own `count_sql`, its own integrity SQL (§7.2) and an honest failure mode: if the ledger asset fails,
  nothing frozen is touched.
* **Registry row (routine migration; sketch below).** `target_table = mimamsa_reference_resolution`;
  chart-scoped `count_sql` using **`$1`** for the chart (the cockpit reads `count_sql`, not
  `asset_throughput`; the convention is a positional `$1`: **81 of the 83** production per-chart `count_sql` values
  use `chart_id = $1`, and every one of the 70 `count_sql … chart_id =` statements in this repository's
  migrations does; none uses `:chart_id` — a test pins the doc to that convention);
  `clear_tables`; `target_floor` 0 at registration, set to the achieved count after the first build
  (aspirational, §N.4); `natural_key_partition` and an output-digest spec following the 990/991
  pattern. `sort_order` and the prose columns are provisional. The row's `integrity_check_sql` is the
  §7.2 block verbatim (a test compares them). It lands with the writer PR (`has_writer = true`
  requires the writer to exist), after 1264 has been applied via the window (§4.1).

```sql registry
INSERT INTO asset_registry (
  asset_id, layer, sort_order, sanskrit_name, english_name, english_description,
  storage_type, target_table, count_sql, size_sql, target_floor, expected_volume_formula,
  volume_explanation, depends_on, scope, estimated_seconds, clear_tables, asset_type,
  layer_name, layer_index, catalog_status, integrity_check_sql, has_writer, asset_kind,
  domain, rung, writer_timeout_seconds
) VALUES (
  'mi_nirdesa', 'mimamsa', 15, 'Nirdeśa', 'Reference-resolution ledger',
  'Computed side ledger: one row per frozen prediction recording whether the anchor it was frozen against can still be found and on what basis. Never modifies the frozen predictions.',
  'postgres_table', 'mimamsa_reference_resolution',
  'SELECT count(*) FROM mimamsa_reference_resolution WHERE chart_id = $1',
  'SELECT pg_total_relation_size(''mimamsa_reference_resolution'')',
  0, 'COUNT(mimamsa_predictions WHERE chart_id = $chart)',
  'One row per mimamsa_predictions row of the chart, recomputed on every build.',
  ARRAY['mi_bhavisya', 'ph_nimitta'], 'per_chart', 2, ARRAY['mimamsa_reference_resolution'], 'data',
  'Mīmāṃsā', 'L5', 'DRAFT',
  $integrity$
SELECT NOT EXISTS (
         SELECT 1 FROM mimamsa_reference_resolution
          GROUP BY chart_id
         HAVING count(DISTINCT build_id) <> 1 OR count(DISTINCT resolver_version) <> 1
       )
   AND NOT EXISTS (
         SELECT 1 FROM mimamsa_reference_resolution r
          WHERE NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = r.chart_id)
       )
   AND NOT EXISTS (
         SELECT 1 FROM mimamsa_reference_resolution WHERE btrim(prediction_frozen_bundle_hash) = ''
       )
$integrity$,
  true, 'data', 'chart', 'R5', 600
) ON CONFLICT (asset_id) DO NOTHING;

UPDATE asset_registry
   SET natural_key_partition = 'mimamsa_reference_resolution (chart_id, prediction_id) - MiNirdesaWriter (@register mi_nirdesa) is the sole build-time writer of this table'
 WHERE asset_id = 'mi_nirdesa' AND natural_key_partition IS NULL;
```

### 6.2 Pure module

`platform/python-sidecar/brahmagyan/mimamsa/reference_resolution.py` (does not exist; to be
created by the implementation PR) holds `resolve_references`, `canonical_falsifier`,
`freeze_anchor_id`, `summarize`, with the exact semantics of the reference function in the test
file. The writer is a thin shell: read, call the pure function, write. The strict-xfail parity hold in
the tests flips on the day the module lands and must be converted to a real parity test.

### 6.3 Writer SQL (reference)

```sql writer
SELECT p.chart_id, p.prediction_id, p.source_pramana_id, p.domain,
       lower(p.observation_window) AS window_start,
       upper(p.observation_window) AS window_end,
       p.falsifier_jsonb, p.frozen_bundle_hash,
       (SELECT m.citation_ref ->> 'anchor_id'
          FROM mimamsa_manifestation_sets m
         WHERE m.chart_id = p.chart_id AND m.prediction_id = p.prediction_id
           AND m.citation_ref ? 'anchor_id'
         ORDER BY m.channel_id
         LIMIT 1) AS citation_anchor_id
  FROM mimamsa_predictions p
 WHERE p.chart_id = %s
 ORDER BY p.prediction_id;

SELECT a.chart_id, a.anchor_id, a.domain, a.window_start, a.window_end, a.falsifier
  FROM phala_anchors a
 WHERE a.chart_id = %s
 ORDER BY a.anchor_id;

DELETE FROM mimamsa_reference_resolution WHERE chart_id = %s;

INSERT INTO mimamsa_reference_resolution (
  chart_id, prediction_id, anchor_id_at_freeze, freeze_id_source, anchor_id_referenced,
  reference_rewritten_since_freeze, resolution_status, resolution_basis, resolved_anchor_id,
  candidate_count, current_anchor_count, claim_key, prediction_frozen_bundle_hash,
  resolver_version, build_id, resolved_at
) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
```

A prediction that has *no* window (the frozen row has `NOT NULL observation_window`, so none today)
is not a case; the `phala_anchors` read has no window filter on purpose (rule 3 compares windows
exactly and an anchor with a NULL window simply never matches).

## 7. The detector (reported, not build-blocking)

### 7.1 Semantics

The detector answers "how many frozen predictions cite an anchor that cannot be found, and is the
ledger telling the truth about it". **It reports; it never fails a build.** A `vanished` count above
zero is a *finding*, not an error, because the rows are a record and the gap is a property of L4's
history. It takes over the job of the global `mimamsa_predictions` term that migration **1259**
(widened by N-104) removes from **both** `ph_nimitta`'s and `mi_bhavisya`'s integrity SQL: that term
is a gate that is false whenever any frozen prediction dangles, on any chart, so a rebuild of
`ph_nimitta` rolls back on a fact it did not produce. Two facts from the independent review keep this
honest: on `mi_bhavisya` that one conjunct is the *only* failing term (the review executed the registry
text read-only: false as stored, true with that conjunct removed); on `ph_nimitta`, removing it does
**not** by itself make the check true — the 1259 PR body records a separate L4 defect (conjunct a7:
`phala_phaladesa.top_anchor_id` dangling on 6 of 7 rows).

```sql detector
-- D1: per-chart status counts from the ledger, plus the three ways the ledger can be wrong about the
-- live tables: a prediction with no ledger row, a ledger row whose prediction is gone, a ledger row
-- whose frozen hash or live id-resolution no longer matches. Reported, never blocking.
WITH joined AS (
  SELECT coalesce(p.chart_id, l.chart_id) AS chart_id,
         p.prediction_id AS pred_pid,
         l.prediction_id AS led_pid,
         l.resolution_status,
         (l.prediction_frozen_bundle_hash IS DISTINCT FROM p.frozen_bundle_hash) AS hash_changed,
         EXISTS (
           SELECT 1 FROM phala_anchors a
            WHERE a.chart_id = p.chart_id
              AND a.anchor_id::text IN (lower(btrim(p.source_pramana_id)), l.anchor_id_at_freeze)
         ) AS live_id_resolves
    FROM mimamsa_predictions p
    FULL JOIN mimamsa_reference_resolution l
      ON l.chart_id = p.chart_id AND l.prediction_id = p.prediction_id
)
SELECT chart_id,
       count(*) FILTER (WHERE pred_pid IS NOT NULL)                                   AS predictions,
       count(*) FILTER (WHERE resolution_status = 'resolved')                         AS resolved,
       count(*) FILTER (WHERE resolution_status = 'superseded')                       AS superseded,
       count(*) FILTER (WHERE resolution_status = 'vanished')                         AS vanished,
       count(*) FILTER (WHERE pred_pid IS NOT NULL AND led_pid IS NULL)               AS unledgered,
       count(*) FILTER (WHERE pred_pid IS NULL AND led_pid IS NOT NULL)               AS orphan_ledger_rows,
       count(*) FILTER (WHERE pred_pid IS NOT NULL AND led_pid IS NOT NULL
                          AND (hash_changed
                               OR (resolution_status = 'resolved') IS DISTINCT FROM live_id_resolves))
                                                                                      AS stale_ledger_rows
  FROM joined
 GROUP BY chart_id
 ORDER BY chart_id;

-- D2: the list of unresolved predictions for one chart (what an acharya or a reader actually looks at).
SELECT r.prediction_id, r.resolution_status, r.resolution_basis, r.anchor_id_at_freeze,
       r.anchor_id_referenced, r.reference_rewritten_since_freeze, r.candidate_count,
       p.domain, lower(p.observation_window) AS window_start, upper(p.observation_window) AS window_end,
       p.lifecycle_status
  FROM mimamsa_reference_resolution r
  JOIN mimamsa_predictions p ON p.chart_id = r.chart_id AND p.prediction_id = r.prediction_id
 WHERE r.chart_id = %s AND r.resolution_status <> 'resolved'
 ORDER BY r.resolution_status, lower(p.observation_window), r.prediction_id;

-- D3: ledger-free, id-level fallback. Works before the ledger asset has ever run and is the
-- independent cross-check of the ledger's resolved/(superseded + vanished) split.
SELECT p.chart_id,
       count(*)                                         AS predictions,
       count(*) FILTER (WHERE a.anchor_id IS NOT NULL)  AS id_resolved,
       count(*) FILTER (WHERE a.anchor_id IS NULL)      AS id_unresolved
  FROM mimamsa_predictions p
  LEFT JOIN phala_anchors a ON a.chart_id = p.chart_id AND a.anchor_id::text = p.source_pramana_id
 GROUP BY p.chart_id
 ORDER BY p.chart_id;
```

D3 on production today (read-only): canonical 139 / 4 / 135; `1c826d5a-…` 56 / 56 / 0 — identical to
the full resolver's `resolved` vs (`superseded` + `vanished`) split (§2.5).

### 7.2 What the new asset's own integrity check may claim

Per the ruling, an integrity check claims only what its writer produces. The ledger asset's
`integrity_check_sql` therefore asserts **ledger-internal** facts only — the status/basis matrix is
already a DB `CHECK`; the SQL adds: one build per chart, and the chart exists. It does **not** claim
coverage of `mimamsa_predictions` or agreement with the live anchor table: those depend on other
assets' later writes and belong to D1 (reported).

```sql detector
-- asset integrity (ledger-internal only; no reference to the frozen table or to anchors)
SELECT NOT EXISTS (
         SELECT 1 FROM mimamsa_reference_resolution
          GROUP BY chart_id
         HAVING count(DISTINCT build_id) <> 1 OR count(DISTINCT resolver_version) <> 1
       )
   AND NOT EXISTS (
         SELECT 1 FROM mimamsa_reference_resolution r
          WHERE NOT EXISTS (SELECT 1 FROM charts c WHERE c.id = r.chart_id)
       )
   AND NOT EXISTS (
         SELECT 1 FROM mimamsa_reference_resolution WHERE btrim(prediction_frozen_bundle_hash) = ''
       );
```

### 7.3 Where it is surfaced

1. **The ledger asset's own build result** (`WriterResult.notes`): the count per status, written by
   the writer from the summary it just produced.
2. **A governance script**, `platform/scripts/governance/l5_reference_resolution_check.py`, in the
   pattern of `msr_dangling_signal_refs.py` (F-3 / N-32): `--self-test`, `--chart-id`, `--json`;
   read-only. Exit codes differ from that script on purpose: **dangling references never exit 1**.
   `0` = report produced, ledger consistent; `1` = the ledger contradicts itself or the live tables
   (stale/orphan rows) — a defect in the *ledger*; `2` = environment error; `3` = INCONCLUSIVE (no
   ledger rows for a chart that has predictions). The census cell for "Build.completion: stale N% dangling"
   proposed in A.L5 CF-L5-02 reads D1.
3. **Pre/post checks around any L3/L4/L5 rebuild (S-L4 / S-L5 / W7 read-back).** Record D1 and the
   frozen-set digest (§7.4) before and after. Expected movement is stated in advance: `predictions`
   and the digest are unchanged; `vanished` may fall (anchors re-created with the same identity) but
   a prediction moving from `resolved` to `vanished` is a regression to explain.
4. **Served disclosure** (§8).

### 7.4 What the ledger cannot see

A prediction that is *deleted* leaves no row to examine (the limit `msr_dangling_signal_refs.py`
states for itself). The ledger lists only predictions that exist when it runs; D1's `orphan_ledger_rows`
catches a ledger row left behind, but a ledger rebuilt *after* the deletion forgets it. The only
control that can show a deleted frozen row is the **before/after frozen-set digest and row count**,
which is why §7.3 item 3 makes it part of the pre/post check and why migration 1265 (DB-enforced
immutability) plus the `mi_bhavisya` append-only writer PR are preconditions, not alternatives.

```sql evidence
SELECT chart_id, count(*) AS predictions,
       md5(string_agg(prediction_id || ':' || frozen_bundle_hash, ',' ORDER BY prediction_id)) AS frozen_set_digest
  FROM mimamsa_predictions
 GROUP BY chart_id
 ORDER BY chart_id;
```

## 8. How readers disclose the gap

Principle (CLAUDE.md §N.6/§N.7/§N.8): disclosure is data, not narration; an honest null beats an
invented zero; a status needs a detector behind it. **Nothing is excluded or re-weighted** — the
frozen rows keep counting as the calibration record; readers say what they cannot trace.

* **`query_predictions`** (`platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts`,
  which already emits `source_pramana_id` and promises "emits_references"): `LEFT JOIN` the ledger and
  add per row `reference_resolution: { resolution_status, resolution_basis, resolved_anchor_id,
  anchor_id_at_freeze, ledger_stale }`, or `null` when the prediction has no ledger row.
  *Where the flags live (corrected after review).* This handler's `content` has **no
  `judgment_flags` field** (it returns `chart_id, predictions, prediction_count, total_matching,
  more_available, prediction_id_refs, sparse_note, empty_reason?, filters, provenance`), so the three
  flags are carried as `reference_gap.flags: [...]` inside `content`; the implementation PR may mirror
  them into the v3 envelope's `judgment_flags` where that envelope is built. Flags:
  `dangling_anchor_references_present` when `vanished > 0`; `reference_ledger_absent` when
  `ledgered = 0` (unknown, not clean); `reference_ledger_stale` when `stale_ledger_rows > 0`.
* **The summary is computed over the whole matching population, not the returned page.** The tool is
  paginated (`MAX_LIMIT` 200, `total_matching`, `more_available`), so `reference_gap` comes from its own
  aggregate query built with the **same `where` and params as the existing `COUNT(*)` that produces
  `total_matching`** (including `chart_context_stale_at IS NULL` unless `include_stale`), never from
  the rows in the page: `reference_gap: { total_matching, ledgered, unledgered, resolved, superseded,
  vanished, vanished_ambiguous, reference_rewritten, stale_ledger_rows, flags }`. It is a small fixed
  object outside `predictions`, so it is registered as a protected (`hardFloor`) section against the
  response-budget trimmer (§N.6): disclosure must not be the first thing trimmed.
* **One definition of "stale".** A ledger row is **stale** iff its stored
  `prediction_frozen_bundle_hash` differs from the live prediction's hash **or** its `resolved` /
  not-`resolved` status disagrees with whether the live reference (or the stored freeze id) now
  resolves against `phala_anchors`. That is exactly detector D1's `stale_ledger_rows`; the per-row
  `ledger_stale` and the summary's `stale_ledger_rows` use the same predicate, and a test on a real
  Postgres asserts that the reader SQL and D1 agree under the four perturbations (§9). The flag
  `reference_ledger_stale` therefore names a detector that exists (§N.8).
* **`mimamsa_calibration_get` / `query_calibration`**: the same `reference_gap` object, computed over
  the predictions the returned calibration rows come from (join on `prediction_id`), plus the note that
  the calibration **still counts them** (ruled: disclose, do not exclude). **When there is no ledger the
  counts are `null`, never `0`** — a missing detector reads as "unknown", not "clean".
* **Other readers that cite an anchor from a prediction** (`standing_predictions_read`, journal /
  outcome tools) carry the per-row object only.
* **The calibration leak guard is unaffected.** The ledger holds no outcome, no Brier score, no
  calibration adjustment, and is computed from reference columns and the anchor table alone. The
  served field names proposed above are tested against the guard's `CALIBRATION_LEAK_KEYS` patterns
  (parsed from `calibration_leak_guard.ts`): none matches. The test fails if a future field name does.
* **`vanished` is not shown as an error to the end reader**; it is shown as "the L4 anchor this
  prediction was frozen against is no longer present — the prediction record is intact, its
  grounding cannot be re-traced to the current anchor set". The wording is the reader author's, but the
  fields above must be present.

```sql reader
-- query_predictions per-row join (read-only). ledger_stale uses D1's predicate; NULL when unledgered.
SELECT p.prediction_id, p.source_pramana_id, p.domain, p.lifecycle_status,
       r.resolution_status, r.resolution_basis, r.resolved_anchor_id, r.anchor_id_at_freeze,
       CASE WHEN r.prediction_id IS NULL THEN NULL
            ELSE (r.prediction_frozen_bundle_hash IS DISTINCT FROM p.frozen_bundle_hash
                  OR (r.resolution_status = 'resolved') IS DISTINCT FROM EXISTS (
                       SELECT 1 FROM phala_anchors a
                        WHERE a.chart_id = p.chart_id
                          AND a.anchor_id::text IN (lower(btrim(p.source_pramana_id)), r.anchor_id_at_freeze)))
       END AS ledger_stale
  FROM mimamsa_predictions p
  LEFT JOIN mimamsa_reference_resolution r
         ON r.chart_id = p.chart_id AND r.prediction_id = p.prediction_id
 WHERE p.chart_id = %s AND p.chart_context_stale_at IS NULL
 ORDER BY p.prediction_id;

-- reference_gap summary over the WHOLE matching population (same WHERE as the handler's total_matching
-- COUNT; the handler appends its optional prediction_id / lifecycle_status / domain filters here too).
SELECT count(*)                                                              AS total_matching,
       count(r.prediction_id)                                                AS ledgered,
       count(*) - count(r.prediction_id)                                     AS unledgered,
       count(*) FILTER (WHERE r.resolution_status = 'resolved')              AS resolved,
       count(*) FILTER (WHERE r.resolution_status = 'superseded')            AS superseded,
       count(*) FILTER (WHERE r.resolution_status = 'vanished')              AS vanished,
       count(*) FILTER (WHERE r.resolution_basis = 'claim_key_ambiguous')    AS vanished_ambiguous,
       count(*) FILTER (WHERE r.reference_rewritten_since_freeze)            AS reference_rewritten,
       count(*) FILTER (WHERE r.prediction_id IS NOT NULL
                          AND (r.prediction_frozen_bundle_hash IS DISTINCT FROM p.frozen_bundle_hash
                               OR (r.resolution_status = 'resolved') IS DISTINCT FROM EXISTS (
                                    SELECT 1 FROM phala_anchors a
                                     WHERE a.chart_id = p.chart_id
                                       AND a.anchor_id::text IN (lower(btrim(p.source_pramana_id)), r.anchor_id_at_freeze))))
                                                                             AS stale_ledger_rows
  FROM mimamsa_predictions p
  LEFT JOIN mimamsa_reference_resolution r
         ON r.chart_id = p.chart_id AND r.prediction_id = p.prediction_id
 WHERE p.chart_id = %s AND p.chart_context_stale_at IS NULL;
```

## 9. Tests-first (in this PR)

`platform/python-sidecar/tests/test_l5_reference_resolution_ledger_design.py`. No production module is
imported. Two layers:

**9.1 Pure-Python layer (always runs).**

* Reference pure function (`resolve_references`) in the **test file only**, with table-driven scenarios
  for every status/basis, precedence, chart isolation, case folding, JSON/NULL falsifier
  canonicalisation, many-to-one supersession, empty input, an **empty/blank reference** (the flag
  `reference_rewritten_since_freeze` is true when the reference differs from the freeze id, including a
  blanked one), and the **139-prediction / 4-anchor production shape** (4 resolved, 0 superseded,
  135 vanished, 135 reference-rewritten).
* Contract properties: idempotent, order-independent, inputs not mutated, outputs not aliased,
  generators accepted, one row per prediction, duplicate key rejected, 200-case seeded fuzz.
* **Mutation proofs:** source-level mutants of the resolver (chart scoping removed, ambiguity treated
  as superseded, case-sensitive ids, claim key ignoring window / falsifier / domain, freeze id
  ignored, precedence swapped, rows dropped, in-place sort, write into caller dicts, aliasing,
  non-determinism, duplicate not rejected, lying counts, stale resolved id on a vanished row, the
  rewritten flag ignoring a blank reference) — each asserts its target text exists, so none is a silent
  no-op, and every one must be killed.
* **Static SQL check** over every ```` ```sql ```` block of this document: no
  `DELETE/UPDATE/INSERT/TRUNCATE/ALTER/DROP/MERGE/COPY/GRANT/REVOKE/CREATE POLICY/CREATE TRIGGER` and no
  `REFERENCES` against `mimamsa_predictions`; the ledger DDL contains no `REFERENCES`, `FOREIGN KEY`,
  `ON DELETE`, trigger, `INHERITS`, or mention of `phala_anchors`; the writer's only `DELETE` is
  `DELETE FROM mimamsa_reference_resolution WHERE chart_id = …` and its only `INSERT` targets the
  ledger; detector/reader/evidence blocks are `SELECT`/`WITH` only; `registry` blocks may only
  `INSERT`/`UPDATE` `asset_registry` rows of `mi_nirdesa`. 18 SQL mutants and 19 resolver mutants are
  all killed.
* The registry `count_sql` placeholder is pinned to the repository's registry convention (`$1`; a scan
  of every `count_sql … chart_id =` in `platform/migrations` and `platform/supabase/migrations`), the
  registry block's `integrity_check_sql` is pinned equal to §7.2, and the proposed served field names
  are checked against the calibration leak guard's key patterns (parsed from the TypeScript).

**9.2 Real-Postgres layer (runs when PostgreSQL binaries are present).** The test file starts its own
throwaway cluster (loopback TCP on a free port, no unix socket, temporary data directory, stopped by
the recorded postmaster PID in the fixture finalizer) and skips with a reason when no
`initdb`/`pg_ctl` is found (set `L5_LEDGER_REQUIRE_PG=1` to make that a failure instead of a skip). It
builds the **production power structure** — schema `public` owned by `data_plane_schema_owner`, a
non-superuser `amjis_app` with `USAGE` only, every role the grants name — and then:

* reproduces **MED-1**: the doc's `ddl` blocks as `amjis_app` without the window fail with
  `permission denied for schema public`; inside a `GRANT CREATE … / REVOKE CREATE` window they apply,
  twice (idempotent), the table is owned by `amjis_app`, the ACL equals the doc's, `CREATE` is gone
  afterwards;
* **MED-3**: applies the doc's DDL and drives an exhaustive grid (status × basis × resolved-id
  nullness × candidate count × current-anchor count × freeze source, including values outside the
  vocabularies) through `INSERT`, asserting the database accepts a row **iff** the Python twin
  (`ddl_check_violations`) finds no violation; then re-runs the same cross-validation against
  **10 mutated DDLs** (every branch of the matrix loosened or tightened in turn — including the two that
  survived review: `candidate_count = 1 → >= 0` and `resolved_anchor_id IS NULL → IS NOT NULL`) and
  requires each mutant to be caught;
* runs the writer, detector (D1/D2/D3), asset-integrity, reader and evidence SQL on the production
  shape (4 / 0 / 135, idempotent rerun), perturbs the data four ways and asserts D1 moves exactly the
  matching counter, and asserts the **reader's stale predicate agrees with D1** (**MED-4**);
* runs the `registry` block as `amjis_app` **without** the window (the routine path works), then
  executes its `count_sql` with a bound `$1`.

**9.3 Strict-xfail holds** (flip to XPASS = failure when the real thing lands, forcing a real test):
production module parity; writer registration under the frozen contract (`@register`, no
commit/close, no `asset_throughput`); the 1264 migration (matched by **file content** —
`CREATE TABLE … mimamsa_reference_resolution` in any migration under either migrations directory —
so the real filename flips it).

**9.4 What is still not in CI.** The `deploy.yml` / `migrate.ts` protected-window wiring (§4.1) is
design only; it is exercised by no test here. A writer-under-`data_plane_builder` test belongs to the
implementation PR (§4, pattern `tests/l3/_builder_role.py`).

## 10. Migrations needed (numbers as per N-104; every unnumbered row: **needs number from SS**)

| # | Purpose | Apply path | Number |
|---|---|---|---|
| M-A | `CREATE TABLE mimamsa_reference_resolution` + index + comments + grants (incl. `data_plane_builder`) + sibling-shaped policies + grant assertion (§3, §4). Additive new table; no existing object touched. **Plus the non-SQL wiring**: filename in `PROTECTED_PUBLIC_SCHEMA_MIGRATIONS`, a dispatch input, the job entry (§4.1). | **protected public-schema window** (`amjis_app` has no `CREATE` on `public`) | **1264** |
| M-B | `asset_registry` row for `mi_nirdesa` and `natural_key_partition` (the `registry` block), guarded by `to_regclass(…) IS NOT NULL`; verified-applied check (CLAUDE.md §N.4). Lands with the writer PR. | routine runner (DML on `amjis_app`-owned `asset_registry`) | needs number from SS (must sort after 1264) |
| M-C | output-digest spec for `mi_nirdesa` (990 pattern), same guard. | routine runner (DML on `asset_output_digest_specs`) | needs number from SS |
| M-D | **(other worker)** remove the global dangling-anchor term from `ph_nimitta` **and** `mi_bhavisya` integrity SQL (N-104 widening). Not authored here. | routine runner | 1259 |
| M-E | **(other worker)** DB-enforced immutability of the frozen `mimamsa_predictions` rows (all but `lifecycle_status`, `chart_context_*`, `contact_id`); should also bring `mimamsa_predictions_builder_guard` (in no file of this repository) under a migration. Precondition for building M-B in production. Not authored here. | per that worker | 1265 |

Separate writer PR (no migration of mine): `mi_bhavisya` append-only — never delete or re-stamp a frozen
row, and never delete manifestation sets (§2.1).

No migration file is created by this PR.

## 11. Risks and open questions for SS

Closed by N-104 (kept for the record): **host** (new asset, §6.1); **name** `mi_nirdesa` (approved);
**dangling predictions still count** toward the calibration gate (disclose, do not exclude);
**`mi_bhavisya`'s identical integrity term** (folded into 1259); **DB-enforced immutability** (1265);
**rule 3 stays**, labelled weaker evidence.

Still open:

1. **Rule 2 (resolve by freeze id when the reference column was rewritten away).** Keep? It exists to
   survive a repeat of the 680 failure mode; cost is one extra branch. Today it fires on 0 rows.
2. **How strong must `superseded` be?** v1 = exact (domain, window, falsifier), unique, in-chart —
   weak but disclosed (independent review: domain-only would match 53 rows, so the key is already near
   its safe edge). Option: also require equality of the frozen `outcome_claim` with the successor's
   projection, which needs the freeze mapping factored into a *shared* helper (touches production
   code). Today it changes nothing (superseded = 0).
3. **Ordering and preconditions.** Until 1265 and the `mi_bhavisya` append-only PR land, a routine
   `mi_bhavisya` rebuild still replaces all `pending` rows (all 139) and deletes all manifestation sets.
   Building the ledger asset before then is safe (it only reads the frozen table) but protects
   nothing. Confirm: 1265 + append-only PR, then M-A (window) and M-B.
4. **State vs history.** Delete-then-insert means the ledger forgets what it once recorded about a
   prediction that is later deleted. Acceptable **only because** 1265 makes deletion of frozen rows
   impossible; the frozen-set digest carries the history (§7.4). Alternative: an append-only history
   table. Recommendation: not now.
5. **Data classification and RLS of the ledger.** C3-predictive (walled like `mimamsa_predictions` /
   `mimamsa_calibration` in migration 576, to be added to the g1c arm/disarm lists) or a derived table
   with the plain sibling ACL? The DDL assumes the second, with sibling-shaped policies; RLS is
   disarmed in production (operator-armed), so the choice changes nothing observable today.
6. **Role that executes the writer.** `role_orchestrator` or `data_plane_builder`? The design grants
   both; the implementation PR needs a builder-role test either way (the Q-L4-04 failure shape).
7. **Window wiring ownership.** The §4.1 changes touch `migrate.ts` and `deploy.yml`, which other lanes
   also edit; who authors them, and may they ride in the same PR as the writer?
8. **Other reference kinds.** `driving_signals` (0 of 695 live per A.L5 CF-L5-02) is a *different grain*
   (up to five ids per prediction) and should be its own table if wanted;
   `brahma_mimamsa_prediction_ledger` / `brahma_prospective_ledger` cite L1 fact ids and a text
   citation, not anchor ids. v1 = anchors only.
9. **`resolved` is only as strong as identity.** For the 4 predictions on 680-collision-pair ids
   (random, never remapped) identity cannot hold; they can only ever be `superseded` or `vanished`.
10. **Risk: the ledger being read as a verdict.** A `resolved` row says an anchor with that id exists,
    not that the anchor still carries the grade it had at freeze. Disclosure wording must not say
    "verified".
11. **Chart `1c826d5a-…` resolves 56/56 today only because 680 remapped it and the L4 rebuild
    reproduced the identities.** That is a statement about this moment; the detector is how it stays true.
12. **Asset integrity SQL is true on an empty table and global rather than per-chart** (review NIT).
    Global matches the registry convention (the freeze-time detector runs with no bind parameters);
    coverage is deliberately delegated to D1 plus the INCONCLUSIVE exit (§7.3).
