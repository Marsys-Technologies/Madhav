---
artifact: L5_REFERENCE_RESOLUTION_LEDGER_DESIGN
canonical_id: SUVARNA_L5_REFERENCE_RESOLUTION_LEDGER_DESIGN
version: "1.0"
status: "DRAFT — HELD for SS review; design + tests-first only; nothing here is built, migrated or applied"
produced_on: 2026-10-03
produced_in: "Exec Suvarṇa"
plan_item: "TI-l5-ledger-design-001 (SS ruling N-99; Q-L4-01 / Q-L4-02)"
layer: L5 (Mīmāṃsā), reading L4 (Phala)
chart_scope: 482012f1-710e-4a25-994a-93821f5871aa
ruling_implemented: "N-99 — frozen mimamsa_predictions rows are never deleted or rewritten; dangling anchor references are RECORDED in a computed side ledger written by an L5-side process; an integrity check claims only what its own writer produces"
tests: platform/python-sidecar/tests/test_l5_reference_resolution_ledger_design.py
evidence: "/Users/Dev/suvarna-evidence/S_L1/l5_ledger/ (prod_counts.py, prod_counts.json) and /Users/Dev/suvarna-evidence/S_L1/L5_LEDGER_DESIGN_REPORT.md"
inputs_read:
  - "/Users/Dev/suvarna-evidence/A_L4/REPORT.md and A.L4 briefs (PR #3013): ph_nimitta, ph_pramana; Q-L4-01/02/03/05/08"
  - "/Users/Dev/suvarna-evidence/A_L5/out (read-only): mi_bhavisya brief, INDEX CF-L5-02, Q-L5-02, bhav-N1/N2/N3/N7"
  - "00_ARCHITECTURE/L5_SEAL_AND_SHIP_REPORT_v1_0.md"
  - "platform/migrations/347, 680, 682, 990, 991, 1083; platform/scripts/governance/msr_dangling_signal_refs.py"
  - "production, reader role only (SELECT), 2026-10-03"
changelog:
  - "1.0 (2026-10-03): first draft. Ledger table, resolution rules, detector, reader disclosure, migration needs, risks. Production counts measured read-only. Pure-function reference + tests-first in the test file named above."
---

# L5 reference-resolution ledger — design v1.0

## 1. Ruling, scope and non-goals

**Ruling (SS N-99).** `mimamsa_predictions` rows are the calibration record of what was
predicted. 135 of the 139 rows on the canonical chart cite anchors that are no longer in
`phala_anchors`. Those rows are **never deleted and never rewritten** (N-46 mixed table: frozen
rows are immutable). The gap must be **recorded**, by an **L5-side process**, in a **computed
side ledger** every reader can see. An integrity check **claims only what its own writer
produces**: the global `mimamsa_predictions` term leaves `ph_nimitta`'s integrity SQL
(migration 1259, separate worker) and becomes an L5-side **reference-resolution detector** —
reported, **not build-blocking**. No rebuild may cascade into the frozen rows (migration 1260,
separate worker).

**In scope.** The ledger table; who writes it; the exact resolution rules
(`resolved` / `superseded` / `vanished`) with production counts; the detector; how readers disclose
the gap; the migrations this needs; risks and open questions.

**Not in scope (and not done here).** No writer, no migration file, no orchestrator extension, no
change to `mimamsa_predictions`, `ph_nimitta`, `mi_bhavisya` or any reader. Migrations 1259/1260
belong to other workers. This PR is a design document plus a test file containing a *reference*
pure function (test-file only) and strict-xfail holds.

**Two things this design deliberately does not do:** it does not repair or re-point a dangling
reference (a repair is a decision about what was predicted, which is not the ledger's to make), and
it does not exclude dangling predictions from calibration (that is a calibration-policy decision,
see open question 12).

## 2. Evidence (production, reader role, read-only, 2026-10-03)

### 2.1 What the frozen rows hold

* `mimamsa_predictions` (migration 347): PK `(chart_id, prediction_id)`; **no foreign key to
  `phala_anchors`** (so no cascade can reach it from there); 195 rows: **139** canonical,
  **56** on chart `1c826d5a-…`; all 195 `lifecycle_status = 'pending'`.
* **The anchor reference column is `source_pramana_id`** (it stores an anchor id under a
  pramana-shaped name; migration 680 header). `prediction_id` is `'pred_' || <anchor_id at freeze>`
  (`mi_bhavisya.py`). The manifestation set's `citation_ref->>'anchor_id'` also holds the
  anchor id at freeze (139 of 139 equal the `prediction_id` suffix).
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
"irreplaceable outcome" guard protects only `confirmed/denied/partial` rows. That protection gap is
migration 1260's job; this design **assumes 1260 lands before the ledger asset is built in
production** (open question 7) and is written so the ledger is correct either way (it records the
rows that exist at the moment it runs).

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
  'The anchor id the prediction was frozen against (manifestation citation, else the prediction_id suffix).';
COMMENT ON COLUMN mimamsa_reference_resolution.anchor_id_referenced IS
  'The live reference column value (source_pramana_id) when the ledger was computed; may differ from the freeze id.';
COMMENT ON COLUMN mimamsa_reference_resolution.claim_key IS
  'Evidence for superseded/ambiguous decisions: domain, window_start, window_end, sha256 of the canonical falsifier.';
```

**Column notes.**

* `anchor_id_at_freeze` / `freeze_id_source`: the required `anchor_id_at_freeze` of N-99. Source
  preference: `citation_ref` (written once at freeze, untouched by 680) → `prediction_id_suffix`
  → `source_pramana_id` (last resort; then the two ids coincide by construction and
  `reference_rewritten_since_freeze` is false). `text`, not `uuid`: it must hold whatever was
  frozen, including a malformed value, without the ledger failing to record it.
* `anchor_id_referenced` + `reference_rewritten_since_freeze`: makes the 680 rewrite
  (191/195 rows) visible instead of buried.
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
  9).** The DDL below follows the sibling policy *shape* so the ledger is not the one table in the
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

## 5. Resolution rules

Inputs, per chart: every `mimamsa_predictions` row (all lifecycle statuses, including
`chart_context_stale` rows — a stale-context row still holds a reference) and every
`phala_anchors` row **of the same chart**. Anchors never match a prediction of another chart.

### 5.1 The freeze id

`anchor_id_at_freeze` = first available of: `mimamsa_manifestation_sets.citation_ref->>'anchor_id'`
(smallest `channel_id` for determinism) → the part of `prediction_id` after `pred_` →
`source_pramana_id`. `freeze_id_source` records which.

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
  *shared* projection helper factored out of `mi_bhavisya` (open question 4), at the cost of a
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
satisfies the DDL `CHECK` matrix (Python twin `row_invariant_violations`); it takes no outcome,
calibration, lifecycle or event input (the calibration leak guard is unaffected by construction — it
is a function of reference columns and the anchor table only).

## 6. Who writes it

### 6.1 Asset proposal (frozen orchestrator contract; no orchestrator extension)

* **A new asset, proposed id `mi_nirdesa`** (*nirdeśa*, "indication, reference"; the name needs SS
  approval and must not be confused with `mi_sambandha` — open question 2). A `@register("mi_nirdesa")`
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
* **Registry row (migration needed):** `target_table = mimamsa_reference_resolution`;
  chart-scoped `count_sql` (`SELECT count(*) FROM mimamsa_reference_resolution WHERE chart_id = :chart_id`
  — the cockpit reads `count_sql`, not `asset_throughput`); `clear_tables`;
  `target_floor` = achieved count after the first build (aspirational, §N.4); `natural_key_partition`
  and an output-digest spec following the 990/991 pattern.

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
history. It replaces the global `mimamsa_predictions` term in `ph_nimitta`'s integrity SQL
(currently a gate that is false whenever any frozen prediction dangles, on any chart: a rebuild of
`ph_nimitta` rolls back on a fact it did not produce). The same dangling term also sits in
**`mi_bhavisya`'s own integrity SQL, which evaluates to `false` on production right now** — it
should be relocated by the same logic (open question 5).

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
which is why §7.3 item 3 makes it part of the pre/post check and why migration 1260 (no-cascade /
no-delete protection) is a precondition, not an alternative.

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
  anchor_id_at_freeze, ledger_stale }`, or `null` when the prediction has no ledger row. Response
  level: `reference_gap_summary: { ledgered, unledgered, resolved, superseded, vanished,
  stale_ledger_rows }` and, in `judgment_flags`, `dangling_anchor_references_present` when
  `vanished > 0`, `reference_ledger_absent` when nothing is ledgered, `reference_ledger_stale` when
  `stale_ledger_rows > 0`.
* **`mimamsa_calibration_get` / `query_calibration`**: the same `reference_gap_summary`, computed over
  the predictions the returned calibration rows come from (join on `prediction_id`), plus the
  note that the calibration still counts them. **When there is no ledger the counts are `null`, never
  `0`** — a missing detector reads as "unknown", not "clean".
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
-- query_predictions join (read-only): per-row disclosure, NULL when unledgered
SELECT p.prediction_id, p.source_pramana_id, p.domain, p.lifecycle_status,
       r.resolution_status, r.resolution_basis, r.resolved_anchor_id, r.anchor_id_at_freeze,
       (r.prediction_frozen_bundle_hash IS DISTINCT FROM p.frozen_bundle_hash) AS ledger_stale
  FROM mimamsa_predictions p
  LEFT JOIN mimamsa_reference_resolution r
         ON r.chart_id = p.chart_id AND r.prediction_id = p.prediction_id
 WHERE p.chart_id = %s
 ORDER BY p.prediction_id;
```

## 9. Tests-first (in this PR)

`platform/python-sidecar/tests/test_l5_reference_resolution_ledger_design.py` — pure Python, no DB, no
network, no production module imported:

* Reference pure function (`resolve_references`) in the **test file only**, with table-driven scenarios
  for every status/basis, precedence, chart isolation, case folding, JSON/NULL falsifier
  canonicalisation, many-to-one supersession, empty input, and the **139-prediction / 4-anchor
  production shape** (4 resolved, 0 superseded, 135 vanished, 135 reference-rewritten).
* Contract properties: idempotent, order-independent, inputs not mutated, outputs not aliased,
  generators accepted, one row per prediction, duplicate key rejected, 200-case seeded fuzz of the
  DDL-twin invariants.
* **Mutation proofs:** 18 source-level mutants of the resolver (chart scoping removed, ambiguity
  treated as superseded, case-sensitive ids, claim key ignoring window / falsifier / domain, freeze id
  ignored, precedence swapped, rows dropped, in-place sort, write into caller dicts, aliasing,
  non-determinism, duplicate not rejected, lying counts, stale resolved id on a vanished row) —
  every one must be killed by the contract; each mutation asserts its target text exists so none is
  a silent no-op. 15 mutants of the document's SQL (extra `DELETE`/`UPDATE`/`INSERT`/`TRUNCATE`/
  `ALTER`/`DROP`/`GRANT`/`CREATE POLICY`/trigger on the frozen table, FK to the frozen table or to
  `phala_anchors`, unscoped ledger delete, DML smuggled into a detector or a CTE, `FOR UPDATE` on the
  frozen table) — every one must be flagged.
* **Static SQL check** over every ```` ```sql ```` block of this document: no
  `DELETE/UPDATE/INSERT/TRUNCATE/ALTER/DROP/MERGE/COPY/GRANT/REVOKE/CREATE POLICY/CREATE TRIGGER` and no
  `REFERENCES` against `mimamsa_predictions`; the ledger DDL contains no `REFERENCES`, `FOREIGN KEY`,
  `ON DELETE`, trigger, `INHERITS`, or mention of `phala_anchors`; the writer's only `DELETE` is
  `DELETE FROM mimamsa_reference_resolution WHERE chart_id = …` and its only `INSERT` targets the
  ledger; detector/reader/evidence blocks are `SELECT`/`WITH` only.
* A test that the resolver takes only the declared reference columns (no outcome / calibration /
  lifecycle inputs), and the leak-key test of §8.
* **Strict-xfail holds** (flip to XPASS = failure when the real thing lands, forcing a real test):
  production module parity, writer registration under the frozen contract (`@register`, no
  commit/close, no `asset_throughput`), the ledger-table migration file.

### 9.1 The SQL in this document was executed, not only parsed

Every `ddl`, `writer`, `detector`, `reader` and `evidence` block above was run against a disposable
local PostgreSQL 17 (unix socket only, started and stopped by recorded PID; not production) with stub
copies of the three source tables: the DDL applies twice cleanly; no FK, trigger or policy exists on
the frozen or anchor tables afterwards; the writer reproduces **4 / 0 / 135** on the production shape
and is idempotent on rerun; detector D1 reads `unledgered = 1`, `stale = 1` (a vanished anchor id
reappearing), `stale = 1` (a replaced prediction hash), `orphan = 1` (a deleted prediction) under
the four matching perturbations and zero otherwise; the asset-integrity SQL goes `false` on a
two-builds-in-one-chart partial write; all six incoherent status/basis rows are rejected by the
`CHECK` matrix. Script and output: `/Users/Dev/suvarna-evidence/S_L1/l5_ledger/validate_sql_local.py`
and `.out`. One defect found and fixed by this run: `CREATE POLICY` is not idempotent, so each is
now preceded by `DROP POLICY IF EXISTS`.

## 10. Migrations needed (every number: **needs number from SS**)

| # | Purpose | Number |
|---|---|---|
| M-A | `CREATE TABLE mimamsa_reference_resolution` + index + comments + grants (incl. `data_plane_builder`) + sibling-shaped policies (§3, §4). Additive, new table, no existing object touched. | needs number from SS |
| M-B | `asset_registry` row for `mi_nirdesa`: `depends_on`, `target_table`, chart-scoped `count_sql`, `clear_tables`, `integrity_check_sql` (§7.2), `has_writer`, scope. Plus a verified-applied check (CLAUDE.md §N.4: author surgically, verify it applied). | needs number from SS |
| M-C | `natural_key_partition` and output-digest spec for `mi_nirdesa` (the 990/991 pattern), so freshness is not `unknown / partition_undeclared`. | needs number from SS |
| M-D | **(other worker, 1259)** remove the global `mimamsa_predictions` term from `ph_nimitta`'s `integrity_check_sql`. Not authored here. | 1259 (reserved) |
| M-E | **(other worker, 1260)** no rebuild may delete/cascade into frozen predictions. Precondition for building M-B in production. Not authored here. | 1260 (reserved) |
| M-F | *(proposed, SS decision)* remove the same dangling term from `mi_bhavisya`'s `integrity_check_sql` (§7.1; currently `false`). | needs number from SS |
| M-G | *(proposed, SS decision, likely inside 1260's scope)* an UPDATE-immutability guard on the frozen columns of `mimamsa_predictions` (all but `lifecycle_status`, `chart_context_*`, `contact_id`), and putting `mimamsa_predictions_builder_guard` (not in any file of this repository) into a migration so it is reproducible (the g1c policies are in 576). | needs number from SS |

No migration file is created by this PR.

## 11. Risks and open questions for SS

1. **Host: new asset or an existing one?** Recommendation: a new asset (§6.1). Alternative `mi_pramana`
   (calibration) is a poor semantic fit; `mi_bhavisya` couples the ledger to the hazard.
2. **Name `mi_nirdesa`.** Needs SS approval (Sanskrit-naming convention; avoid confusion with `mi_sambandha`).
3. **Rule 2 (resolve by freeze id when the reference column was rewritten away).** Keep? It exists to
   survive a repeat of the 680 failure mode; cost is one extra branch. Today it fires on 0 rows.
4. **How strong must `superseded` be?** v1 = exact (domain, window, falsifier), unique, in-chart —
   weak but disclosed. Option: also require equality of the frozen `outcome_claim` with the
   successor's projection, which needs the freeze mapping factored into a *shared* helper
   (`mi_bhavisya` and the resolver would then share one definition; touches production code).
   Today it changes nothing (superseded = 0).
5. **`mi_bhavisya`'s own integrity SQL has the same global dangling term and is `false` on production now.** Relocate to the
   detector as well (M-F)? The ruling names `ph_nimitta`; this is the same defect one asset to the right.
6. **680 already rewrote 191 of 195 frozen reference columns, and nothing prevents a repeat.** There is
   no UPDATE guard on `mimamsa_predictions`, and the one trigger that exists is not in the repo. Is the
   N-99 "immutable" to be enforced in the database (M-G) or only by convention?
7. **Dependency on 1260.** Until 1260 lands, a routine `mi_bhavisya` rebuild still replaces all
   `pending` rows (all 139). Building the ledger asset before 1260 is safe (it only reads the frozen
   table) but does not protect anything. Confirm the ordering: 1260, then M-A/M-B.
8. **State vs history.** Delete-then-insert means the ledger forgets what it once recorded about a
   prediction that is later deleted. Accepted here (state, §4); the frozen-set digest carries the
   history (§7.4). Alternative: an append-only history table. Recommendation: not now.
9. **Data classification and RLS of the ledger.** C3-predictive (walled like `mimamsa_predictions` /
   `mimamsa_calibration` in migration 576, to be added to the g1c arm/disarm lists) or a derived
   table with the plain sibling ACL? The DDL assumes the second, with sibling-shaped policies; RLS is
   disarmed in production (operator-armed), so the choice changes nothing observable today.
10. **Role that executes the writer.** `role_orchestrator` or `data_plane_builder`? The design grants both;
    the implementation PR needs a builder-role test either way (the Q-L4-04 failure shape).
11. **Other reference kinds.** `mimamsa_manifestation_sets.citation_ref` repeats the anchor id (no
    separate ledger needed: same value); `driving_signals` (0 of 695 live per A.L5 CF-L5-02) is a
    *different grain* (up to five ids per prediction) and should be its own table if wanted;
    `brahma_mimamsa_prediction_ledger` / `brahma_prospective_ledger` cite L1 fact ids and a text
    citation, not anchor ids. v1 = anchors only.
12. **Do dangling predictions keep counting toward calibration and the activation gate?** This design
    discloses and does not exclude. Whether a gate sample should count a prediction whose grounding can
    no longer be traced is a calibration-policy decision (Q-L5-02 / Q-L5-11 territory), not the ledger's.
13. **`resolved` is only as strong as identity.** For the 4 predictions on 680-collision-pair ids
    (random, never remapped) identity cannot hold; they can only ever be `superseded` or `vanished`.
14. **Risk: the ledger being read as a verdict.** A `resolved` row says an anchor with that id exists,
    not that the anchor still carries the grade it had at freeze. Disclosure wording must not say
    "verified".
15. **Chart `1c826d5a-…` resolves 56/56 today only because 680 remapped it and the L4 rebuild
    reproduced the identities.** That is a statement about this moment; the detector is how it stays true.
