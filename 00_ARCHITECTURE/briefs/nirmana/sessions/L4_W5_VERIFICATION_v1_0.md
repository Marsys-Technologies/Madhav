---
version: 1.1
status: DRAFT
owner: L4 (Phala)
depends_on: migration 681 (C12 registry contracts), migration 680 (D-CND-04 ph_nimitta)
changelog: >
  1.1 (2026-09-07): cross-asset gap closed as prep — the scripted half now exists at
  l4_scripts/l4_w5_mechanical_checks.sql (10 checks, authored AND run read-only against
  live data: 7 PASS of which 3 vacuous-and-say-so, 3 EXPECTED-RED each on an already-fixed
  defect awaiting W4 rebuild). §"Known gaps" and §"Not yet covered" annotated in place.
  1.0 (2026-09-06): initial pre-written runbook (C8.5 prep).
---

# L4 Phala — W5 VERIFY runbook

Pre-written per the founding prompt's C8.5 guidance ("pre-write W5 verification scripts for
the whole layer") — a prep item, not shared Conductor tooling. Does not duplicate
`platform/scripts/nirmana/egate.sql` (that answers "may an asset enter W4"; this answers "did
W4's output hold up"), and does not touch the Conductor-owned `scripts/nirmana/` directory —
this is L4's own read-only checklist, referencing contracts already shipped.

## What this is

Every one of L4's 9 `ph_*` assets already carries a live, corruption-tested
`integrity_check_sql` on `asset_registry` (migration 681, C12/D-CND-03). Each detector:
- is chart-PARTITIONED (`GROUP BY chart_id HAVING ...`) so a single-chart corruption cannot be
  masked by other charts' rows — except `ph_pramana`'s schema-invariant clause (D5 NO-SCORING
  gate re-assertion), which is chart-independent by nature (see migration 681 comment);
- was run live against production data before installation and shown to flip to `false` on
  injected corruption (C12's rewrite-floor test) — so a green here is an earned signal
  (§N.8), not a proxy.

W5 VERIFY, when the E-gate opens and a real build runs, is: re-run these 9 detectors against
the fresh build's output and confirm every one still reads `true`. This is that batch query.

## Batch verification query

```sql
-- Read-only. Run once per verification pass, not once per asset.
SELECT
  asset_id,
  target_floor,
  catalog_status,
  (integrity_check_sql IS NOT NULL) AS has_detector
FROM asset_registry
WHERE asset_id LIKE 'ph\_%'
ORDER BY asset_id;

-- Then, per asset, execute its own integrity_check_sql and confirm TRUE:
DO $$
DECLARE r record; ok boolean; failures text[] := '{}';
BEGIN
  FOR r IN SELECT asset_id, integrity_check_sql FROM asset_registry
            WHERE asset_id LIKE 'ph\_%' ORDER BY asset_id
  LOOP
    EXECUTE r.integrity_check_sql INTO ok;
    IF ok IS NOT TRUE THEN
      failures := failures || r.asset_id;
    END IF;
  END LOOP;
  IF array_length(failures, 1) > 0 THEN
    RAISE NOTICE 'W5 VERIFY: RED on %', failures;
  ELSE
    RAISE NOTICE 'W5 VERIFY: all 9 ph_* detectors GREEN';
  END IF;
END $$;
```

This is the same pattern migration 681's own post-condition block already uses to refuse
installing a red gate — reused here for post-build re-verification, not duplicated tooling.

## Per-asset volume floor check (target_floor, where set)

| asset_id | target_floor | note |
|---|---|---|
| `ph_nimitta` | 139 | derived: clip-gated, CR-46-deduped anchor count |
| `ph_muhurta` | 134 | derived: DISTINCT (action_class, window_start) collapse of anchors |
| `ph_sankrama` | 2510 | derived: anchor × material-CDLM-cell cross count |
| `ph_sodhana` | **NULL (deliberate)** | anomaly registry — fewer rows is better; a floor would reward fabricated findings (§N.4) |
| `ph_suddha_sodhana` | 139 | derived equality: `= count(phala_anchors)`, live not literal |
| `ph_pratikara` | 536 | derived: `= count(kala_obstruction)`, NOT anchor count |
| `ph_pramana` | **NULL (deliberate, pending W3-3)** | life_event_match currently unreachable code; a floor now would enshrine a dead detector's count |
| `ph_phaladesa` | 13 | derived structural constant: canonical domain vocabulary cardinality |
| `ph_rectification` | 186 | derived: 37-offset lattice × 5 ayanamshas + 1 best row |

Volume check = re-run each asset's `expected_volume_inputs` queries against the fresh chart
and confirm the row count matches `expected_volume_formula`'s derivation — never a bare
`count(*) = target_floor` literal comparison (C12 forbids equality-wearing-a-floor's-name).

## Known gaps this checklist will NOT catch (by design, not oversight)

Four invariants W1 derived as real were deliberately withheld from migration 681 because they
fail on current data — installing them now would ship a knowingly-red gate. They are **not**
part of this W5 batch until their fixes land and the invariant is added:

1. `ph_pramana` — "a `life_event_miss` must cite a resolvable LEL comparison" (fails 12/12 today)
2. `ph_rectification` — `load_bearing` may not be `true` on a non-discriminating fit (fails 1/1) — **fixed in PR shipping the discrimination gate this session; verify this invariant is added to `asset_registry` before treating it as covered**
3. `ph_rectification` — `confidence_low`/`confidence_high` must be a valid probability band (fails: `-0.2000` persisted)
4. `ph_sankrama` — full no-gap tiling against `bodha_cdlm_cells` (fails: 250 rows destroyed by the transition→general domain-map defect)

Before declaring W5 complete for real, re-check `asset_registry.integrity_check_sql` for these
four asset_ids against the live migration history — several of this session's W3-3 fixes may
have already closed the underlying defect without yet getting a corresponding invariant
installed. That gap (fix shipped, detector not added) is itself a C12/§N.8 violation if left
open past freeze — a fixed-but-undetected defect reads identically to a never-fixed one to any
future session reading only `asset_registry`.

**v1.1 update (2026-09-07):** all four withheld invariants are now PRE-WRITTEN as executable
checks W1–W4 in `l4_scripts/l4_w5_mechanical_checks.sql`, and were RUN read-only against live
pre-rebuild data. Verified statuses: (1) `ph_pramana` life_event_miss — now VACUOUS (zero miss
rows exist post-migration-684/#1842, vs. the 12/12 failures W1 measured; the check earns its
green only when a W4 rebuild produces miss rows again); (2) `ph_rectification` load_bearing —
RED as expected (`judgment_flags->>'load_bearing'` is where the flag lives, not a column);
(3) confidence band — RED as expected (−0.2000 on both charts); (4) `ph_sankrama` tiling —
RED with **exactly 250 missing pairs measured, independently reproducing the writer's own
recorded defect figure**. Item 2's earlier note ("verify this invariant is added to
`asset_registry`") is resolved: it was NOT added to `asset_registry` (correctly — it fails on
current data; installing it would ship a knowingly-red gate), so it lives in the script until
the rebuild lands, after which the W5 cycle should promote W2–W4 into migration-installed
`integrity_check_sql` clauses.

## Cross-asset (inter-`ph_*`) consistency — COVERED as of v1.1 (was: "Not yet covered")

The 9 detectors above are each single-asset. The cross-asset scripted half now exists:
**`l4_scripts/l4_w5_mechanical_checks.sql`** (L5-precedent format: one row per check —
`check_id, passed, detail`; read-only; vacuous greens self-identify). It was authored AND run
against live data (run status recorded in its own header), which satisfies the §N.8 concern
that deferred this section at v1.0 — the checks are demonstrated to execute and to fail on the
real corruption that exists (3 expected-red on known, already-code-fixed defects).

Coverage beyond the original two bullets, from a full column-by-column sweep of what no
per-asset contract expresses:
- `ph_pratikara.linked_anchor_id` same-chart (X1 — the v1.0 flagged gap; 1,277 links green)
- `ph_sankrama.source_anchor_id` same-chart (X2), `ph_phaladesa.top_anchor_id` same-chart
  (X3 — v1.0 called this "already covered" by clause 4, but clause 4 proves existence, not
  chart identity; corrected)
- `ph_muhurta.overlapping_obstruction_id` → `kala_obstruction` resolution + same-chart (X4;
  60 refs green — no detector anywhere touched this column)
- `ph_pramana.linked_sodhana_id` (X5) and `ph_sankrama.mitigation_ref` (X6) — vacuous today,
  armed for post-rebuild data
- the four withheld invariants as W1–W4 (see §"Known gaps" v1.1 update above)

What remains genuinely for the W5 cycle itself: re-run this script against the FRESH build's
data (the run recorded here proves the checks work; it says nothing about data that does not
exist yet), plus the fresh-context judgment verification the plan pairs with the scripted half.
