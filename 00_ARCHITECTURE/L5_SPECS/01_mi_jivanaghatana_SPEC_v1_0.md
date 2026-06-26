---
artifact: 01_mi_jivanaghatana_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_JIVANAGHATANA
asset_id: mi_jivanaghatana
asset_kind: data
scope: global
activation: v1
version: 1.0
status: DRAFT — build-ready spec (reconcile [P2] items against ground-truth audit)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§F no-LEL held-out partition, §C held-out partition, §H LEL leverage, leakage firewall]
---

# mi_jivanaghatana — Clean-Evidence Vault & Leakage Firewall

> Sanskrit: *Jīvanaghaṭanā* ("life events"). The ground-truth vault. It owns the Life Event Log and turns
> it into **admissible, provenance-tagged, leakage-firewalled evidence** that the calibration engine is
> allowed to score against. This asset is where the instrument's honesty about its own evidence begins.

## §1 — Purpose & value
Calibration is only as honest as the evidence it scores against. This asset:
1. loads the LEL into the layer,
2. tags every event with **provenance** (could it have leaked into the predictors?),
3. derives an **admissibility** flag (clean vs contaminated vs held-out),
4. maintains the **held-out partition** (sacrosanct; never seen by predictors),
5. exposes the **clean-evidence view** that `mi_pramana` is permitted to score.

**Superhuman/retrieval relevance:** none directly (it's the evidence floor), but it is the precondition
for every honest score downstream. Without the firewall, all calibration is circular self-congratulation.

## §2 — Inputs
| source | what | notes |
|---|---|---|
| `life_events` (L1/shared table) | the LEL rows (~57 events for native) | the raw ground truth |
| `LIFE_EVENT_LOG_v1_2.md` (canonical LEL, v1.7) | the authoritative file | count must match exactly (divergence = bug) |
| event provenance signals | which events shaped L2 signals / seeded L4 rectification / disclosure timing | drives leakage tagging |
| `mi_abhilekha` (service, on update) | new journal-sourced events | triggers re-tag + re-partition |

## §3 — Output schema (build-ready)
This asset writes **no new event store** — the canonical `life_events` table is the store. It writes a
**provenance/admissibility companion table** + a **held-out view**.

### Table: `mimamsa_event_provenance`  (scope: per chart event)
```
chart_id                uuid        not null
event_id                text        not null     -- FK → life_events natural key
references life_events
shaped_predictor        boolean     not null     -- did this event shape an L2 signal / L4 rectification?
shaped_predictor_refs   jsonb                    -- which predictor ids it shaped (audit)
disclosure_timing       text        not null     -- 'pre_framework' | 'post_framework' | 'unknown'
disclosure_date         date                     -- when the native disclosed it (if known)
event_date              date        not null     -- the event's actual date (from life_events)
domain_primary          text        not null     -- career/health/relationship/... (from life_events)
domain_secondary        text[]                   -- multi-domain events (e.g. residential+travel)
event_magnitude         text                     -- minor/moderate/major/rupture (assessed)
held_out                boolean     not null     -- in the sacrosanct held-out partition?
admissible_clean        boolean     not null     -- DERIVED: usable as clean calibration evidence?
admissibility_reason    text        not null     -- why admissible/not (audit string)
partition_seed_version  text        not null     -- the deterministic partition assignment version
lel_version             text        not null     -- the LEL version this row reflects (freshness)
provenance_formula_ver  text        not null     -- versioned derivation (D-2)
created_at              timestamptz not null
PRIMARY KEY (chart_id, event_id)
```

### View: `vw_mimamsa_held_out`  — the sacrosanct partition (read-only to predictors)
```sql
SELECT * FROM mimamsa_event_provenance WHERE held_out = true;
```
### View: `vw_mimamsa_admissible_clean`  — what mi_pramana MAY score for the headline grade
```sql
SELECT * FROM mimamsa_event_provenance WHERE admissible_clean = true AND held_out = false;
```

## §4 — Computation logic (deterministic)

### 4.1 — Provenance tagging
For each LEL event, deterministically set:
- `shaped_predictor` = true if the event id appears in any L2-signal derivation ledger OR L4
  `ph_rectification`/`ph_sodhana` event set. `shaped_predictor_refs` records the matched ids. (Source of
  truth: the derivation ledgers; this is a join, not a judgment.)
- `disclosure_timing` from the LEL's per-event disclosure metadata (pre/post the framework's existence).
- `event_magnitude` from the LEL's magnitude field if present, else `[P2]` a deterministic mapping from
  the event-type taxonomy (no LLM).

### 4.2 — Admissibility (the firewall logic)
```
admissible_clean =
      (NOT shaped_predictor)              -- didn't shape the predictors → no leakage
  AND (disclosure_timing != 'post_framework_undated')   -- not a post-hoc contaminant
  AND (event_date is reliable)            -- has a usable date for windowed scoring
```
- Contaminated events (shaped a predictor) are **still stored and still scored separately** (labeled
  `admissible_clean=false`), never blended into the headline grade. (COMPARISON model: retrodiction
  reported separately, never headlined.)
- `admissibility_reason` always records the deterministic cause (e.g. "shaped L2 signal SIG.x → excluded
  from clean grade").

### 4.3 — Held-out partition (deterministic, sacrosanct)
- The held-out set is assigned **deterministically** from a seeded function of `event_id` (so re-runs
  yield the identical partition — reproducibility), targeting the V3-ratified fraction `[P2: e.g. 20%]`
  while preserving domain balance where n permits.
- **Held-out is set ONCE per event and never reassigned** when new events arrive (a held-out event stays
  held-out; new events are partitioned among themselves). This prevents the "retrofit the partition to
  pass" failure mode.
- The predictors (L2/L4) and `mi_pramana`'s headline path **never read** `vw_mimamsa_held_out` except in
  the explicit held-out validity test (a separate, gated read).

### 4.4 — No-LEL behavior
If `life_events` is empty for the chart: the asset still builds, writes zero provenance rows, and the
admissible/held-out views are empty. Downstream calibration enters **structural-prior-only mode** (no
fabricated evidence). This asset never invents an event.

## §5 — Retrievability contract
- Emits, for `mi_darshana`, an **evidence-coverage summary** unit: counts of total/clean/held-out/
  contaminated events per domain, the `lel_version`, and `last_partitioned_at`. This lets the LLM honestly
  state the evidence base ("calibration rests on N clean events, ~k/domain"). Trust-metadata (R5): every
  downstream insight inherits the `lel_version` + n from here.

## §6 — Determinism & seal gates
- No LLM anywhere (D-1). Provenance/admissibility/partition are pure joins + seeded functions.
- `provenance_formula_ver` + `partition_seed_version` frozen + versioned (D-2); re-run = identical rows (RL-1).
- **Count integrity gate:** `count(mimamsa_event_provenance for chart) == count(life_events for chart)` —
  divergence halts (mirrors the seed's `volume_explanation`).
- **Partition-stability gate:** re-running must not move any event's `held_out` flag (RL-1 + the
  no-retrofit rule).
- Degenerate-distribution guard applies to `domain_primary`, `disclosure_timing` (flag if all-one-value
  unexpectedly).
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_jivanaghatana')` `WriterBase`; `run(ctx)`; `conn = ctx.db_conn` never committed;
`WriterResult(asset_id='mi_jivanaghatana', rows_inserted=…)`; global scope; `count_sql`:
`SELECT count(*) FROM mimamsa_event_provenance` (global) — **[P2:** confirm whether provenance is global or
per_chart-scoped in the registry; the table is per-chart-event but the asset is chart-agnostic loader].
Idempotency: delete-then-insert scoped to `(chart_id)`.

## §8 — `depends_on`
`['mi_kula']` is NOT required; this is a near-root. Proposed: `depends_on: []` (reads `life_events` + the
predictor derivation ledgers which exist pre-L5). `[P2 reconcile]`.

## §9 — Matrix rows satisfied
held-out partition (§C, §F) ✅ · leakage firewall ✅ · no-LEL evidence floor (§F) ✅ · LEL leverage (§H) ✅ ·
trust-metadata source for R5 ✅ · determinism/repro/degenerate gates (§G) ✅.

*End 01_mi_jivanaghatana_SPEC v1.0.*
