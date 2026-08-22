---
canonical_id: F142_MI_DARSHANA_REGRADE_PACKET
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-142
authored: 2026-08-22
authored_by: PARIŚEṢA-V4 repair lane (GA-3 authority — packet authoring only)
execution_status: NOT EXECUTED — awaiting properly-scoped GA-3 execution
ga3_process_template: R-7-amended (OWNER_RULINGS_20260821.md §R-7), both mandatory
  clauses addressed in §5 below
---

# F-142 — mi_darshana discovery-evidence grade: DATA REGRADE ONLY, code already fixed

> **DO NOT EXECUTE — this document is a packet, not an execution. No production
> write of any kind (UPDATE, DELETE, or asset rebuild) has been run by the lane
> that authored this file. Every number below was obtained with a read-only
> `SELECT` against production, re-measured 2026-08-22.**

## §1 — What this document is, and what it is not

This packet specifies a **data regrade** for stale rows in `mimamsa_insight_units`.
It does **not** specify a code change — the code defect originally suspected under
F-142 was already closed by **F-143** (see §2). It does not execute anything —
execution is a separate GA-3 step this packet only prepares.

## §2 — Code-fix verification (performed fresh against current HEAD, not assumed)

The originally-suspected defect — an `"empirical"` grade assigned to discovery
insights (`emergent_law` / `retrodiction`) purely from `n_support` volume, with no
scored/opportunity gating — **does not exist in current HEAD**.
`platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` was checked
directly:

- `git log` confirms `F-143 (PR #1414, commits ca9214f2c / cf8d42519)` is present in
  this branch's history for the file, and two further revisions have landed on top
  of it since: **F-147 (PR #1439, `44f42fe94`)** and **F-148 pt.1 (PR #1468,
  `e5ef0bc66`)**.
- **`SURFACE_FORMULA_VERSION` is now `"mi_darshana_v1.2"`** (line 38) — one version
  past the `v1.1` the original F-142 investigation plan cited. The plan's own
  target filter (`surface_formula_version <> 'mi_darshana_v1.1'`) is stale by one
  version; §4 below uses the live value.
- `_discovery_evidence_grade(discovery_class, n_support, evidence_refs)` (lines
  89–157) reads `evidence_refs["n_scored_matches"]`, **never** `n_support`, to
  decide the `empirical` tier. A missing scored count always grades **down**
  (`assignment_only` / `prior_only`), never up (§N.7 item 6 compliance, explicit in
  the code's own comment at line 129).
- `discovery_class == "retrodiction"` is **hard-pinned to `_GRADE_STRUCTURAL`**
  (lines 100–117) before the scored-count logic is even reached — it can never
  grade `empirical`, unconditionally, regardless of `n_support` or
  `evidence_refs`.

**Conclusion: the code fix is genuinely in place, and has since been strengthened
twice more. Nothing in this packet asks for a code change.** Filing this as a live
code defect would be wrong; re-applying the F-35/F-143 gating pattern here would be
a no-op patch on already-correct code.

## §3 — Live-verified stale-row scope (read-only, 2026-08-22, against production)

Schema check first (`mimamsa_insight_units` columns): `chart_id`, `insight_id`,
`insight_type`, `domain`, `horizon`, `question_lens`, `statement`,
`rank_consequence`, `confidence_band`, `n_support`, `leakage_status`,
`evidence_grade`, `freshness_lel_version`, `last_calibrated_at`,
`provenance_chain`, `is_negative_knowledge`, `surface_formula_version`,
`updated_at`.

**The finding's own query, run verbatim:**

```sql
SELECT count(*), surface_formula_version
FROM mimamsa_insight_units
WHERE insight_type IN ('emergent_law','retrodiction') AND evidence_grade = 'empirical'
GROUP BY surface_formula_version;
-- count=20 | surface_formula_version='mi_darshana_v1.0'
```

**Confirmed: still exactly 20 rows**, unchanged from the original finding, all on
`surface_formula_version = 'mi_darshana_v1.0'` — three versions behind current HEAD
(`v1.0` → `v1.1` F-143 → `v1.2` F-147). All 20 are `insight_type = 'emergent_law'`;
`retrodiction` never appears here because a `retrodiction` row can only ever be
graded `structural`, `assignment_only`, or `prior_only` under any version of the
code that has ever shipped this table's rows — 0 `retrodiction` rows are
`empirical` today.

**Scope is the single canonical chart.** Grouped by `chart_id`:

```sql
SELECT chart_id, insight_type, evidence_grade, surface_formula_version, count(*)
FROM mimamsa_insight_units
WHERE insight_type IN ('emergent_law','retrodiction')
GROUP BY chart_id, insight_type, evidence_grade, surface_formula_version;
```

returns rows **only** for `chart_id = '482012f1-710e-4a25-994a-93821f5871aa'` (the
canonical chart) — no other chart has any `emergent_law`/`retrodiction` rows in
this table at all. There is nothing to scope beyond this one chart.

**Wider context, not itself the target but decision-relevant (§4):** the entire
`mimamsa_insight_units` table for this chart — all 115 rows, every `insight_type` —
is on the same stale `surface_formula_version = 'mi_darshana_v1.0'`:

```sql
SELECT insight_type, surface_formula_version, count(*)
FROM mimamsa_insight_units
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
GROUP BY insight_type, surface_formula_version ORDER BY insight_type;
```

| insight_type | surface_formula_version | count |
|---|---|---|
| calibrated_outlook | mi_darshana_v1.0 | 6 |
| emergent_law | mi_darshana_v1.0 | 20 |
| load_bearing | mi_darshana_v1.0 | 4 |
| manifestation_grammar | mi_darshana_v1.0 | 7 |
| retrodiction | mi_darshana_v1.0 | 51 |
| verdict_object | mi_darshana_v1.0 | 27 |
| **total** | | **115** |

None of these 115 rows carries either the F-147 (`v1.1`→`v1.2`,
`channel_propensity` disclosure) or F-148 pt.1 (`retrodiction` numeric-match
disclosure) corrections — the whole asset output for this chart predates all three
fixes now live in the writer. This is the deciding fact for §4's recommendation.

## §4 — Recommendation: (a) rerun `mi_darshana` — not a targeted UPDATE

**Recommended: option (a), rerun the `mi_darshana` writer for the canonical
chart.** Reasons, in order of weight:

1. **The 20-row target is not the actual blast radius.** All 115 rows for this
   chart predate F-143/F-147/F-148, not just the 20 flagged `empirical` rows. A
   targeted `UPDATE` scoped to the 20 rows named in the original finding would
   leave the other 95 rows (`calibrated_outlook`, `load_bearing`,
   `manifestation_grammar`, `retrodiction`, `verdict_object`) silently stuck on
   `v1.0` — correct by coincidence today, but no longer traceable to the code that
   is supposed to have produced them, and not verified against the two later
   fixes. A rerun regrades and re-versions the whole asset output in one pass;
   a 20-row UPDATE would require a second, separately-scoped packet later for the
   other 95, which is worse bookkeeping for a cheaper-sounding shortcut.
2. **`mi_darshana` is a leaf writer — rerunning it is genuinely cheap and safe.**
   `asset_registry` shows nothing depends on `mi_darshana` (it has upstream
   dependencies — `mi_pramana`, `mi_adhilepa`, `mi_sambandha`, `mi_pariksha`,
   `mi_gunanaka`, `mi_kula`, `mi_jivanaghatana`, `bo_pratijna` — but is not itself a
   dependency of anything). A rebuild does not cascade downstream and does not
   require rebuilding any other asset.
3. **The writer is §N.3-conformant per-chart delete-then-insert**, confirmed at
   `mi_darshana.py:685` (`DELETE FROM mimamsa_insight_units WHERE chart_id = %s`
   inside `run_substep`). Rows are REPLACED, not accreted — a rerun is exactly the
   "rows are then born from the corrected code" case CLAUDE.md's own template
   language (§N.3, and this campaign's F-157/F-62 packet precedent) prefers over a
   patched-into-agreement UPDATE.
4. **The rerun mechanism already exists and has been exercised for this exact
   asset.** `build_runs` (live query) shows a precedent row:
   `scope='asset', scope_target='mi_darshana', action='build'` for a different
   chart (`1c826d5a-…`, Abhinandan, 2026-07-10, state `completed`). The same
   `scope='asset'` pattern is used across dozens of other assets
   (`bo_laksana`, `bo_pratijna`, `ga_dashas`, …) for single-asset rebuilds. This is
   not a new or unproven code path.

**Option (b) — targeted UPDATE — documented for completeness, not recommended.**
If a future execution decides speed outweighs the above (e.g. if a rerun turns out
to be blocked by some upstream `mi_*` asset being mid-rebuild), the UPDATE **must**
set both columns together:

```sql
-- NOT TO BE EXECUTED BY THIS PACKET. Illustrative only, for a GA-3 execution
-- that has independently decided option (b) over the recommended option (a).
UPDATE mimamsa_insight_units
SET evidence_grade = 'assignment_only',  -- or whatever the correct v1.2 regrade is;
                                          -- MUST be recomputed via the live
                                          -- _discovery_evidence_grade logic against
                                          -- each row's actual evidence_refs, never
                                          -- hardcoded to one value for all 20 rows
    surface_formula_version = 'mi_darshana_v1.2'
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
  AND insight_type = 'emergent_law'
  AND evidence_grade = 'empirical'
  AND surface_formula_version = 'mi_darshana_v1.0';
```

An UPDATE that touches `evidence_grade` alone and leaves
`surface_formula_version = 'mi_darshana_v1.0'` would misrepresent which code wrote
the row (§N.7 item 3 — no wrapper/patch may shadow what the versioned code
actually computed) and is explicitly out of scope for any execution of this
packet. Note also that option (b) cannot safely hardcode one target grade for all
20 rows — the correct regrade per row depends on that row's own
`evidence_refs.n_scored_matches` (§2), which requires re-deriving each row's
`_discovery_evidence_grade` result, not just stamping `'assignment_only'` on all
20. This is the second reason option (a) — where the writer itself recomputes
this correctly per row — is preferred over option (b).

## §5 — R-7-amended GA-3 packet-template requirements (both addressed)

Per `OWNER_RULINGS_20260821.md §R-7`, standing for every GA-3 packet: "a packet
missing either [clause] is DATA_PARKED (incomplete) by definition."

### §5.1 — Clause 1: rollback rehearsal against the full FK-connected table set

```sql
SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND (ccu.table_name = 'mimamsa_insight_units' OR tc.table_name = 'mimamsa_insight_units');
-- ZERO rows returned.
```

`mimamsa_insight_units` has **no foreign-key relationship in either direction** —
no parent, no child. The rollback rehearsal replica for this execution needs to
cover only `mimamsa_insight_units` itself; there is no second table a partial
failure could orphan.

### §5.2 — Clause 2: before-image scope verified against measured rows_written

Measured (read-only), the exact before-image a rerun of `mi_darshana` for this
chart will delete-then-replace — the full 115-row table in §3, reproduced here as
the authoritative before-image count:

```sql
SELECT chart_id, count(*) FROM mimamsa_insight_units
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa';
-- chart_id=482012f1-710e-4a25-994a-93821f5871aa | count=115
```

If option (a) is executed: the before-image is **115 rows, all
`chart_id='482012f1-…'`**. Re-measure immediately before execution — do not reuse
this packet's count if other GA-3 work touches this chart's `mi_darshana` output
between authoring and execution.

If option (b) is executed instead: the before-image is the **20-row** subset
scoped by the WHERE clause in §4's illustrative SQL — re-measure that count too,
immediately before execution.

## §6 — Rebuild specification (option a — the recommended path)

**Mechanism:** insert a `build_runs` row with
`scope='asset', scope_target='mi_darshana', action='rebuild',
chart_id='482012f1-710e-4a25-994a-93821f5871aa'` (via the product's existing
single-asset rebuild path, the same one used for the `1c826d5a-…` precedent run in
§4 item 4), then dispatch the orchestrator Cloud Run Job with
`--run-id <that build_runs.id>` per `pipeline/orchestrator/main.py`'s documented
CLI contract. This is ordinary single-asset rebuild dispatch, not a new mechanism
requiring a contract change.

**No migration.** No code change. No other asset needs rebuilding before or after
(mi_darshana is a leaf writer, §4 item 2).

## §7 — Verification the GA-3 execution should run, post-rebuild

1. **The finding's own query returns zero.**
   `SELECT count(*) FROM mimamsa_insight_units WHERE insight_type IN
   ('emergent_law','retrodiction') AND evidence_grade='empirical' AND
   surface_formula_version <> 'mi_darshana_v1.2'` (or whatever the then-current
   `SURFACE_FORMULA_VERSION` is — re-check `mi_darshana.py` at execution time,
   since this is now the second time this exact string has moved between
   authoring and execution) returns **0**.
2. **Row count is preserved exactly**, or the delta is explained. Total rows for
   `chart_id='482012f1-…'` in `mimamsa_insight_units` after rebuild should be 115
   unless upstream `mi_*` inputs (`mi_pramana`, `mi_sambandha`, `mi_pariksha`,
   etc.) have themselves changed shape since 2026-08-22, in which case the new
   count should be sanity-checked against a fresh read of those inputs, not
   assumed to still be 115.
3. **Every row now carries the live `SURFACE_FORMULA_VERSION`.** No row for this
   chart should remain on `mi_darshana_v1.0` after rebuild.
4. **No `emergent_law`/`retrodiction` row grades `empirical` from `n_support`
   alone.** Spot-check a handful of the regraded rows' `provenance_chain` (the
   `grade_basis` dict `_discovery_evidence_grade` returns) to confirm each
   `empirical` grade traces to a real `n_scored_matches >= 5`, per §2.
5. **No `retrodiction` row is graded anything other than `structural`.**

## §8 — Open items, disclosed rather than decided

- **This packet does not itself determine what the 20 `emergent_law` rows will
  regrade to.** That is exactly the writer's job at rebuild time — evidence_refs
  for these rows have not been individually inspected here beyond confirming they
  currently read `empirical` under stale `v1.0` logic. Some or all may still grade
  `empirical` under `v1.2` if their `n_scored_matches` genuinely clears the
  threshold; this packet takes no position on the post-rebuild grade distribution,
  only on the mechanism that should produce it honestly.
- **Version-string drift between packet authoring and execution has now happened
  twice for this same finding** (the investigation plan's `v1.1` target vs. this
  packet's live-verified `v1.2`). Whoever executes this packet should re-verify
  `SURFACE_FORMULA_VERSION` in `mi_darshana.py` one more time immediately before
  running, rather than trusting either this document's or the plan's cited string.
