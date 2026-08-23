---
canonical_id: GATING_FIELD_SWEEP
version: 1.0
status: DRAFT
task: WORK_QUEUE M0-T24
agent: KARAKA-M0-T24
authored_at: 2026-08-23
certified_by: null   # I16/H7 — the author does not certify. PARIKSAKA verifies; ADHIKARIN disposes.
discharges: >
  DECISIONS.jsonl D-25 part 3 — the standing rule that any registry field which gates whether a
  check runs must be derived from code, never trusted as declared, and surfaced as a
  registry-vs-code PAIR. That rule closed with an instruction: "the plan's own M0 sweep should
  look for others of this shape rather than wait to trip over them." This is that sweep.
database_access: READ-ONLY. No write was issued against asset_registry or any other table.
schema_baseline: asset_registry — 40 columns, 128 rows, read 2026-08-23T05:50:16Z (post-migration 590)
machine_readable: 00_ARCHITECTURE/control/GATING_FIELD_SWEEP_v1_0.json
---

# Gating-field sweep — every `asset_registry` column that can switch a detector off

## 0 — The answer, first

**40 columns examined. 8 in scope. 2 of those were already ruled (D-24, D-25). Of the 6 new,
exactly ONE is the same shape as the two known instances.**

The task's instruction was to report zero honestly if zero is the answer, and not to manufacture
a third instance to justify the work. The answer is not zero, but it is also not five more
`has_substeps`. It splits cleanly, and the split is the finding:

| | what it means | count |
|---|---|---|
| **Tier A** | Gates a detector, **a code-derived truth exists**, the declared value can diverge from it, and it fails **open** (toward an unearned green). The exact D-25 shape. | 3 — two known, **one new** |
| **Tier B** | Gates a detector, but **no code-derived truth exists**. The declaration is the only source there is; it can be *justified*, never *derived*. | 5 — all new |
| **Tier C** | Examined and out of scope: supplies a value to a check, or its null-ness fails **closed**, or nothing depends on it. | 25 (by field group) |

The one new tier-A instance is **`asset_kind` / `asset_type` == `'service'`**, and it is not
hypothetical: `ka_graha_sancara` currently carries `service_health='unhealthy'` — a verdict its
own self-test wrote on 2026-08-02 — while `deriveState()` returns `service_ok` for it and
`plan.ts`'s `READY_STATES` counts it as a satisfied dependency. A live row exists where the
detector's verdict and the served signal disagree, and a declared string is what overrides the
detector.

Tier B is reported as its own tier deliberately. Folding those five into tier A would inflate
"one new instance of the D-25 shape" into "six", and the difference between *a flag that
contradicts the code* and *a flag with no code to contradict* is exactly the distinction D-25
part 3 turns on. They are real gates and they belong in this document; they are not the same
finding.

---

## 1 — Method

1. Enumerated all 40 columns of `asset_registry` from `information_schema.columns`, with per-column
   null / false / empty-string / empty-array / empty-json counts over all 128 rows.
2. For each column, grepped every consumer across `platform/src`, `platform-mcp/src`,
   `platform/python-sidecar`, `platform/scripts` and `00_ARCHITECTURE/control`, excluding
   `node_modules`, `migrations/` and the seed file (D-13: `migrate.ts` and
   `asset_registry_seed.ts` were not imported).
3. For each consumer, asked one question: **does this code path use the field to decide whether a
   check, probe, gate or verification RUNS — as opposed to using it as data?** A field that feeds a
   value is out. A field that can switch a detector off is in.
4. For each in-scope field, determined whether a code-derived truth exists, and where it does,
   derived it and measured the divergence live.
5. Ranked by consequence: what specifically stops being checked, and which assets are in that state.

**Concurrency, as instructed.** A sibling KĀRAKA was repairing `has_substeps` during this sweep.
Both readings are reported with timestamps; neither is picked:

| reading | source | ts | registry `true` | code `true` | false negatives |
|---|---|---|---|---|---|
| A | D-24 / M0-T8 | 2026-08-23T05:04:21Z | 14 | 26 | 12 |
| B | this sweep, live | 2026-08-23T05:54:42Z | 26 | 26 | 0 |

---

## 2 — Tier A: gates a detector, and code can contradict it

### G-01 · `has_substeps` — ALREADY RULED (D-24). Not a new finding.

Included so the document is complete. One thing here IS new: **D-24 names one consumer; there are
three.**

| file:line | effect when `false` |
|---|---|
| `platform/python-sidecar/pipeline/orchestrator/asset_runner.py:619-641` | `plan_complete` initialised `True` at :626, recomputed only inside `if has_substeps:` at :628 — `lit` written on a basis that is not its detector's verdict. (The D-24 instance.) |
| `platform/src/app/api/cockpit/watchdog/classifyStuckCandidate.ts:71-73` | `if (candidate.has_substeps === true) return 'withhold-incomplete'; return 'rescue-lit'` — the TypeScript reaper promotes a stuck `building` asset straight to `lit`. **Not named in D-24. Same defect, different code path, different language.** |
| `platform/src/app/api/cockpit/stats/deriveState.ts:79` | `partial` collapses into `error`. Badge honesty, not a promotion. |

Code truth: `00_ARCHITECTURE/control/writer_substep_census.json` → `writers[*].writer_truth_has_substeps`
(123 registrations, 579 files scanned). Divergence: see the concurrency table. Fails **open**.
Already paired in the workbook (Defect Register D-01).

### G-02 · `has_writer` — ALREADY RULED (D-25 parts 1-2). Not a new finding.

Also has consumers beyond the one D-25 names:

| file:line | effect when `false` |
|---|---|
| `00_ARCHITECTURE/control/build_asset_control_workbook.py:91` | read from the registry rather than derived → `_bound_class()` reads `not-a-build` → **exempt from the §8.3 item 5 efficiency pass altogether**. (The D-25 instance.) |
| `platform/src/app/api/cockpit/runs/route.ts:139` | `WHERE is_active = true AND has_writer = true` — absent from the build plan; never dispatched. **Not named in D-25.** |
| `platform/src/lib/build/recalibrationEnqueue.ts:140` | same predicate on the LEL-recalibration plan. **Not named in D-25.** |

Divergence, measured live 2026-08-23T05:54:42Z: **2 false negatives** (`bg_nakshatra_medical`,
`bg_transit_engine`), **0 false positives** — confirming D-25 exactly, and still unrepaired, which
is correct: D-25 part 2b pins the row repair to R0 stage 2. Seven rows carry `has_writer=false`
in total; only those two are contradicted by code.

The generator fix authorized by D-25 part 2a **has landed** — `build_control_workbook_v4_1.py:263-267,
372, 405-407` now carries `has_writer (registry)` / `has_writer (code)` as a highlighted pair.

> **A trap for whoever implements that derivation elsewhere.** A naive
> `@register\(['"]…['"]\)` regex mis-derives. 4 of 123 registrations use `@register(ASSET_ID)`
> with a module-level constant (census field `register_arg = 'module_const:ASSET_ID'`);
> `mi_sankalpa` is one. **This sweep's own first-pass scanner produced `mi_sankalpa` as a phantom
> false positive for exactly that reason**, disagreeing with PARĪKṢAKA's `0 false positives`. It
> was traced to the regex, not to the registry, and discarded before reporting. The census
> resolves module constants; a hand-rolled scan will not.

### G-03 · `asset_kind` / `asset_type` == `'service'` — **NEW. The one new instance of the exact shape.**

A declared string that short-circuits the entire data-asset verification path, as the **first
branch**, ahead of every other check.

| file:line | effect |
|---|---|
| `platform/src/app/api/cockpit/stats/deriveState.ts:65` | `if (asset.asset_type === 'service' \|\| asset.asset_kind === 'service') return 'service_ok'` — the **first statement in the function**, ahead of the `is_active` check (:67), the `incomplete` branch (:73), the `error` branch (:74), the `building` branch and the `actualRows` check. Nothing downstream can run for a service-declared row. |
| `platform/src/app/api/cockpit/stats/route.ts:74-88` | `fetchAllCounts` returns `service_ok` **without executing `count_sql` at all**. |
| `platform/src/lib/build/plan.ts:196` | `const READY_STATES = new Set(['lit','service_ok'])` — the unearned green is **dependency-satisfying**, not cosmetic. |
| `platform/python-sidecar/pipeline/orchestrator/asset_runner.py:884-886, 940-949` | routes the asset off the data-writer path entirely. |

**The evidence that makes this concrete.** `ka_graha_sancara` carries `service_health='unhealthy'`
(`last_selftest_at` 2026-08-02T13:50:52Z) — a real verdict from its own writer self-test.
`deriveState` returns `service_ok` for it anyway, and `plan.ts:196` treats it as ready. The
detector ran, produced `unhealthy`, wrote it down, and a declared string overrode it.

**The code states the claim itself**, at `deriveState.ts:61-64`:

> *"Service assets have no count_sql/target_table by design — they are healthy when registered + CURRENT."*

"Healthy when registered" is a status with no detector behind it — CLAUDE.md §N.8 verbatim.

Code-derived truth: **partial, and that is the point.** Three code-side facts exist and none is
consulted — whether a `WriterBase` writer is registered, whether `service_probes.py` can answer for
the asset, and whether `health_probe` is non-null. Measured: **all 6** `asset_kind='service'` rows
have `health_probe` NULL **and** `provides_apis` NULL.

Assets currently in this state — 8:

| asset_id | kind | type | health_probe | service_health | writer in code |
|---|---|---|---|---|---|
| bg_ephemeris_engine | data | service | set | null | no |
| bg_panchanga | data | service | set | null | no |
| ka_dasha_kala | service | service | null | healthy | yes |
| **ka_graha_sancara** | service | data | null | **unhealthy** | yes |
| ka_muhurta_seva | service | data | null | healthy | yes |
| ka_tulana | service | service | null | healthy | yes |
| mi_abhilekha | service | data | null | null | yes |
| mi_seva | service | data | null | null | yes |

Fails **open**. Not paired anywhere. Related, and left where it belongs: the contract checker's
C-15 and C-17 have live violating populations on this same data (6 and 4 rows). That is the guard
working, not a new finding; the disposition is ADHIKĀRIN's.

---

## 3 — Tier B: gates a detector, but there is no code to derive it from

Ranked by consequence.

### G-05 · `integrity_check_sql` — NULL on **128 of 128**. *The field the task singled out; confirmed.*

- `asset_runner.py:494-508` — `if integrity_sql:` … else `return False, "no check defined"`.
- `asset_runner.py:886` — `has_check = is_service or bool(registry_row.get("integrity_check_sql"))`.
- `check_asset_catalogue_contract.py:578-605` — **C-22**, severity RUNG, "frozen rung data/artifact ⇒ `integrity_check_sql` NOT NULL".

**The finding is the double gate.** Even if an integrity check were authored tomorrow,
`rebuild_on_probe_fail = false` (G-04) would still keep `_probe_asset` from running. The
integrity-gate engine is switched off at **two independent registry columns**, and neither switch
has a detector behind it.

C-22 currently returns **NOT_CHECKABLE**, on two grounds both reported rather than one masking the
other, with the reason written out: *"a vacuous pass is a signal no database state could turn red,
which §N.8 says is null, not green."* **That is the correct handling and it is the standard the
other seven fields in this document should be measured against.**

Fails **closed** at the probe (`no check defined` → `False`); fails **open** at the freeze gate —
an asset with no invariant can be frozen with nothing having verified it, the moment a rung freezes
and C-22 becomes checkable.

### G-06 · `target_floor` == `0` — 35 rows. *Highest measured live exposure in this tier.*

- `classifyStuckCandidate.ts:69-73` — `dataConfirmedComplete = actualRows != null && (actualRows > 0 || candidate.target_floor === 0)`. With `target_floor=0`, **zero** rows and `has_substeps=false`, the verdict is `rescue-lit`: a stuck `building` asset with **no rows at all** is promoted to `lit`.
- `deriveState.ts:88` — `if (throughputState === 'lit' && actualRows === 0 && asset.target_floor === 0) return 'lit'`.
- `check_asset_catalogue_contract.py:571-576` — **C-21** requires a non-empty `volume_explanation` when `target_floor=0`. **19 of the 35 rows have none** — 19 assets assert "zero rows is correct" with no written reason.

Measured live exposure (against `asset_measurements.json`, measured 2026-08-23T00:11:55Z): of the
35, **7** currently have 0 or unmeasurable rows on the native chart, and **4 of those also have
`has_substeps=false`**, so the watchdog would rescue-lit them today:
`bg_sarvatobhadra_grid` (CURRENT), `mi_abhilekha`, `mi_seva`, `mi_vistara` (DRAFT).

No code artefact declares a floor. But **CLAUDE.md §N.4 supplies the discipline that plays the
same role**: `target_floor` is set to the *measured achieved count after a build*. Under that rule
`target_floor=0` means "a build ran and honestly produced 0" — and it cannot distinguish that from
"never built". `volume_explanation` is the mechanism meant to carry the distinction, and it is
absent on 19 of 35.

> **Doctrine tension, reported and not resolved.** CLAUDE.md §N.4 says floors are **aspirational,
> not gates**. In `classifyStuckCandidate` and `deriveState`, `target_floor === 0` **is** a gate —
> the only one of its values that is. Resolving this is ADHIKĀRIN's, not a KĀRAKA's.

### G-07 · `is_active` — false on **1** row. *Widest blast radius per bit in the table.*

One declared boolean removes an asset from **every** detector at once:

`stats/route.ts:214` (never counted, never state-derived) · `deriveState.ts:67` (returns
`not_migrated` as the second branch, ahead of all evidence) · `runner.py:499` (staleness
propagation) · `dag_edge_guard.py:101` · `global_runner.py:88` · `runs/route.ts:139` and
`recalibrationEnqueue.ts:140` (both build plans) · `check_asset_catalogue_contract.py:712, 770-773, 813`
(x01 exemption; x02 residual; x03 exemption).

Currently `false` on exactly one row — `ka_gochara_sweep`, which is also RETIRED, so it is
arguably correct. It is reported for its shape, and because nothing cross-checks it.

Honest qualifier: x03 in the campaign's own guard **already refuses** to let `has_writer=false`
become this kind of exemption, and writes out why (`check_asset_catalogue_contract.py:794-808`).
`is_active=false` remains an exemption there, deliberately and with a stated reason.

### G-04 · `rebuild_on_probe_fail` — false on **128 of 128**.

`asset_runner.py:887, 893` — `rebuild_policy = bool(...)`, then `if has_check and rebuild_policy:`.
False means `_probe_asset()` is **never called on this path**, for services and data assets alike.

There is no row on which the verify-then-conditionally-regenerate primitive can fire. Nothing is
silently wrong as a result: the primitive is a *skip-if-green optimisation*, so its absence means
writers always run — the conservative branch. It is listed because its on/off switch is a declared
boolean with no detector (the shape D-25 asked to be swept for), and because the day a row sets it
`true`, it activates a path with **zero current production coverage**.

Fails **closed** today. Would fail **open** the moment it is switched on over a weak
`integrity_check_sql`.

### G-08 · `catalog_status` == `'RETIRED'` — 1 row. Governance tier only.

`check_asset_catalogue_contract.py:771, 813` — exempts from x03 (active asset with no build
coverage) and downgrades x02 to RESIDUAL. `:411-415` — C-08 requires `data_disposition` NOT NULL on
a RETIRED row; `data_disposition` is NULL on 128 of 128, so the single RETIRED asset violates C-08.

**No runtime consumer.** `catalog_status` is not read as a gate by any orchestrator or cockpit path
— only by the governance checker and as an MCP filter. Verified by grep across `platform/src`,
`platform-mcp/src` and `platform/python-sidecar/pipeline`.

---

## 4 — Tier C: examined, out of scope

Full per-field reasoning is in the JSON (`tier_C_examined_not_in_scope`). Summarised:

**Fails CLOSED, so a wrong value produces a false alarm, never an unearned green** — `count_sql`
(6 NULL; a NULL stops `_data_rows_present` at `asset_runner.py:197` and the cockpit count at
`stats/route.ts:119`, leaving the asset `dormant` / `missing_table`; 3 `per_chart` rows carry a
`count_sql` with no `$1`, which C-06 already detects) · `health_probe` (126 NULL → `run_health_probe`
returns `down`) · `depends_on` (34 empty; an empty closure makes the DAG edge guard flag *more*, not
less) · `scope` (`global` forces the slower live-count branch and makes `_data_rows_present` return
`None`).

**Supplies a value to a check rather than gating one** — `writer_timeout_seconds` (NOT NULL,
default 600; the watchdog always runs — noted only that `int(_budgets.get(a) or …)` at
`runner.py:317` is falsy-zero, so a literal `0` would silently fall back to the global default; no
row holds 0) · `target_table` · `size_sql` (51 NULL; skips a size *measurement*, which feeds no
verdict) · `estimated_seconds` · `expected_volume_formula` (108 NULL, display-only consumers) ·
`expected_volume_inputs` (124 NULL, no consumer found) · `storage_type` (one conditional, a
sample-display path) · `clear_tables` (127 NULL; C-24 skips a null row, but the clear path never
reads the column — it resolves via `EXPLICIT_CLEAR_OPS` → `count_sql` → `target_table`) ·
`provides_apis`.

**Detector OUTPUTS, not inputs** — `service_health`, `last_invoked_at`, `last_selftest_at`,
`selftest_detail`. Nothing gates on them, which is precisely G-03's finding seen from the other side.

**Honest by construction** — `domain`, `rung`, `superseded_by`, `data_disposition` (the four
migration-590 columns). All four gate contract rules through `Snapshot.missing()`, which returns
**NOT_CHECKABLE**, never a pass.

**Identity, ordering and prose** — `asset_id`, `layer`, `layer_name`, `layer_index`, `sort_order`,
`sanskrit_name`, `english_name`, `english_description`, `created_at`, `volume_explanation` (a C-21
*requirement*, never an exemption).

---

## 5 — What this sweep did NOT do

- **Repaired nothing.** No write of any kind was issued against the database (I13 / I14).
- Did not resolve the §N.4 tension G-06 surfaces. That is ADHIKĀRIN's.
- Did not audit gating fields outside `asset_registry` (`asset_throughput.state`,
  `build_run_assets.state`, `build_protected_assets`). D-25 part 3 is scoped to the registry.
- **Did not establish that the 8 service-declared rows in G-03 are wrongly declared.** Several are
  probably genuine services. The finding is that *the declaration alone produces the green*, not
  that the declaration is false.
- Did not re-run the writer census. It consumed `writer_substep_census.json` (M0-T8) as the
  code-side truth, and cross-checked `has_writer` with an independent `@register` scan whose one
  disagreement it traced to its own regex and discarded.

## 6 — Uncertainties

- `has_substeps` was being repaired concurrently. Both readings are recorded; neither is asserted
  as final.
- G-03's severity depends on how a reader weighs `service_ok`. It is in `plan.ts`'s `READY_STATES`,
  so it is load-bearing for dependency resolution — but whether an always-green service badge is a
  defect or a deliberate simplification is a judgment this KĀRAKA does not make.
- G-04's "dead code today" rests on `rebuild_on_probe_fail` being false on all 128 rows **at the
  time of reading**. Nothing prevents a row from being set true later.
- Tier-C dispositions rest on grep coverage over `platform/src`, `platform-mcp/src`,
  `platform/python-sidecar`, `platform/scripts` and `00_ARCHITECTURE/control`. A consumer outside
  those trees, or one reading the column through a `SELECT *` into a generic record, would not have
  been seen.
