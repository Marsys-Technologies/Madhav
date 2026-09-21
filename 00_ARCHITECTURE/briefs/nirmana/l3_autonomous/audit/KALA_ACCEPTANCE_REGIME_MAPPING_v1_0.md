---
artifact: KALA_ACCEPTANCE_REGIME_MAPPING
version: "1.0"
status: DRAFT — cycle 3 of the KĀLA READINESS AUDIT
produced_by: L3 Kāla readiness audit (autonomous, Claude Code)
produced_on: 2026-09-22
scope: T3 — the explicit mapping between campaign event_types and F13/F14/L3-strategy-§7 gates,
  and which gates have no admissible event type at all.
method: >
  Produced by one read-only subagent (opus, per charter model guidance for T3), 14 tool calls,
  all read-only DB queries against nirmana_evidence + grep against platform/scripts/nirmana/.
  Headline event-type count and the CONSUMER_INTEGRATED/VALUE_EVALUATED gap independently
  spot-verified by the conductor via direct DB query before integration — see AUDIT_STATE.md
  cycle 3.
---

# KĀLA ACCEPTANCE REGIME MAPPING — T3

Current frozen campaign definition: `t3-2026-09-11-8b884eac`.

Sources cited throughout:
- `MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md` (F13 line 40, F14 line 41, §3.2
  vocabularies lines 70–76, §8 gate matrix lines 133–142)
- `MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §7 (lines 389–400)
- `platform/scripts/nirmana/capsule_audit.sql` (the campaign's own terminal-claim auditor)
- `nirmana_evidence.nirmana_elevation_campaign_events` (live)

---

## 0. The three vocabularies, quoted exactly

**F13 (evidence maturity)** — contract line 40 / §3.2 line 74:

> Evidence maturity progresses separately: present → qualified → consumed → effect traceable →
> served → value evaluated. | Evidence per rung; no rung inferred from a later/earlier label.
>
> Evidence maturity uses ordered rungs: `present`, `qualified`, `consumed`, `effect_traceable`,
> `served`, `value_evaluated`. A component may reach different rungs for different questions,
> subjects, methods or channels.

**F14 (delivery)** — contract line 41 / §3.2 line 76:

> Delivery progresses separately: strategy agreed → producer ready → integrated →
> deployed/operationally accepted → consumer-value demonstrated → empirically evaluated. |
> Named receipt for each reached state; unreached states stay explicit.
>
> Delivery uses ordered but independently evidenced states: `strategy_agreed`, `producer_ready`,
> `integrated`, `deployed_operationally_accepted`, `consumer_value_demonstrated`,
> `empirically_evaluated`. **A green test or producer receipt cannot skip a state.**

**§8 gate matrix — the "may not be claimed from" column (verbatim, load-bearing):**

| Gate | May not be claimed from |
|---|---|
| Strategy agreed | Draft presence, commit or silence |
| Producer ready | Row count or code existence |
| Integrated | Producer tests alone |
| Deployed/operationally accepted | CI, PR, local run or dashboard |
| Consumer value demonstrated | Computational influence or richer prose |
| Empirically evaluated | Fixtures, retrodiction or explanatory value |

**L3 strategy §7 target state** (lines 396–399), and the execution brief's delivery target:

> delivery_target: "LAYER_DATA_ACCEPTED + scoped CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED +
> VALUE_EVALUATED; empirical outcome evaluation excluded"

---

## 1. All distinct event_types found

```sql
SELECT event_type, count(*) AS n, count(DISTINCT definition_revision) AS n_defrev
FROM nirmana_evidence.nirmana_elevation_campaign_events GROUP BY 1 ORDER BY 1;
```

**17 distinct event types**, not the 7 named in the original brief:

```
accepted_rebuild_observed          | 103 | 4
asset_analysis_accepted            | 182 | 4
asset_frozen                       | 111 | 4
asset_label_catalogue_accepted     |   4 | 4
build_run_authorized               | 120 | 4
definition_superseded_mid_campaign |   3 | 3
empty_accepted                     |   1 | 1
foundation_lane_accepted           |  13 | 3
implementation_accepted            |  64 | 4
integrity_verified                 | 112 | 4
optimization_verdict_accepted      | 186 | 4
probe_accepted                     |   6 | 2
producer_covered                   |   3 | 1
retired_with_disposition           |   2 | 2
source_accepted                    |   1 | 1
static_accepted                    |   1 | 1
stage_transition_accepted          |  16 | 2
```

Ten types beyond the original list: `asset_label_catalogue_accepted`,
`definition_superseded_mid_campaign`, `empty_accepted`, `foundation_lane_accepted`,
`probe_accepted`, `producer_covered`, `retired_with_disposition`, `source_accepted`,
`static_accepted`, `stage_transition_accepted`.

**Scoped to the current frozen definition, only 11 of the 17 appear, and every asset-scoped one
is `layer = 'L2'`.** Independently re-confirmed by the conductor: `SELECT count(*) FROM
nirmana_evidence.nirmana_elevation_campaign_events WHERE definition_revision='t3-2026-09-11-
8b884eac' AND entity_id LIKE 'ka_%'` returns **0**.

```
accepted_rebuild_observed      | L2 |  9 | 8
asset_analysis_accepted        | L2 |  9 | 8
asset_frozen                   | L2 |  8 | 8
build_run_authorized           | L2 |  6 | 6
implementation_accepted        | L2 |  9 | 8
integrity_verified             | L2 |  8 | 8
optimization_verdict_accepted  | L2 | 10 | 8
asset_label_catalogue_accepted |    |  1 | 1
definition_superseded_mid_campaign | |  1 | 1
foundation_lane_accepted       |    |  5 | 5
stage_transition_accepted      |    |  9 | 9
```

**Under `t3` there are ZERO L3 asset events of any type.** The campaign stage has transitioned
`L2 → L3` (`stage_transition_accepted`), but no L3 identity has any evidence at the current
definition. **`Accepted 0/22` is the honest current reading.**

### 1.1 Payload structure per type (aggregate, `t3` only)

| event_type | payload keys | `source_kind` |
|---|---|---|
| `asset_analysis_accepted` | `analysis_digest`, `registry_fingerprint_sha256` | `git_commit` |
| `optimization_verdict_accepted` | `analysis_digest`, `basis`, `proposal`, `verdict`, `registry_fingerprint_sha256` | `git_commit` |
| `implementation_accepted` | `analysis_digest`, `decision_digest`, `implementation_digest`, `registry_fingerprint_sha256` | `git_commit` |
| `build_run_authorized` | `asset_ids`, `authorization_sha256`, `wave_index` | `campaign_authorization` |
| `accepted_rebuild_observed` | `build_run_id`, `output_digest`, `output_digest_spec_sha256`, `analysis_digest`, `decision_digest`, `implementation_digest`, `authorization_sha256`, `registry_fingerprint_sha256`, `wave_index` | `build_run` |
| `integrity_verified` | `detector_observation`, `integrity_contract_sha256`, `result_digest`, `analysis_digest`, `registry_fingerprint_sha256` | `server_reconstructed` |
| `asset_frozen` | `analysis_digest`, `lifecycle_digest`, `registry_fingerprint_sha256` | `server_reconstructed` |
| `stage_transition_accepted` | `from_stage`, `to_stage`, `manifest_sha256`, `schema_version` | `server_reconstructed` |
| `foundation_lane_accepted` | `lane_id`, `manifest_sha256`, `schema_version` (+ lane-specific: `main_sha`, `serving_sha`, `ci_run_id`, `migration_sha256`, `build_run_count`, `live_registry_asset_count`…) | `server_reconstructed` |
| `asset_label_catalogue_accepted` | `asset_count`, `catalogue_sha256`, `audit_provenance` | `governed_catalogue` |
| `definition_superseded_mid_campaign` | `superseded_revision`, `new_manifest_sha256`, `bound_event_count`, `native_authorization` | `native_ruling` |

Types present only at earlier definitions (`t0`/`t1`/`t2`), sampled for semantics:

| event_type | example | what it attests |
|---|---|---|
| `probe_accepted` | `ka_muhurta_seva`, `ka_graha_sancara`, `ka_dasha_kala`, `ka_tulana`, `bg_panchanga` | a *service/query* identity responded and a detector's checks passed. `source_kind=server_reconstructed` (the campaign probing itself), **not** a receiving operator |
| `producer_covered` | `bg_transit_engine` covered by `bg_transit_rules` | this asset's rows are lineage-covered by another asset's build run |
| `retired_with_disposition` | `ka_gochara_sweep` | the protected-retired member's historical disposition (strategy's §7 carve-out) |
| `empty_accepted` | `bg_sarvatobhadra_grid` | an honest zero-row outcome, accepted as such |
| `source_accepted`, `static_accepted` | 1 row each | type-appropriate non-build dispositions |

`integrity_verified`'s detector is real and hashed (`detector_sql_sha256` present), which matters
for §N.8 grading. `optimization_verdict_accepted` verdict vocabulary observed: `correct`,
`examined_and_already_efficient`, `non_build_disposition`.

---

## 2. Mapping table: event_type → F13 rung → F14/gate rung → exclusions

Grading rule: an event is admissible evidence for a rung only if what it actually attests is the
thing that rung asserts. Where §8's "may not be claimed from" column names the exact artifact
class the event's `source_kind`/payload consists of, the event is marked **BARRED**.

| event_type | F13 rung(s) admissible for | F14/§8 gate rung(s) | §7 state | Barred by "may not be claimed from"? |
|---|---|---|---|---|
| `asset_analysis_accepted` | `present` | contributes to Strategy agreed only jointly with the verdict | PLAN_REVIEWED | **BARRED alone from Strategy agreed** ("Draft presence, commit or silence"; `source_kind=git_commit`). Also barred from Producer ready ("code existence") |
| `optimization_verdict_accepted` | `qualified` | **Strategy agreed** as a decision record | PLAN_REVIEWED | Admissible for Strategy agreed as a decision record; underlying commit alone is barred. **BARRED from Producer ready** (no computation/context/failure/compatibility tests in payload) |
| `implementation_accepted` | `present` | toward Producer ready — insufficient alone | PRODUCER_READY (partial) | **BARRED alone from Producer ready** — payload is three digests + a git commit, literally "code existence" |
| `build_run_authorized` | none — an authorization, not evidence | none — precondition only | — | n/a |
| `accepted_rebuild_observed` | `present` | **Producer ready** (real run, not local) | DATA_ACCEPTED (materialization limb) | **BARRED from Deployed/operationally accepted** — no revision/environment/migration/rollback receipt in payload. Barred from Integrated ("producer tests alone") |
| `integrity_verified` | `qualified` | **Producer ready** (qualification/computation test limb) | DATA_ACCEPTED (integrity limb) | **BARRED from Integrated** — "Producer tests alone." Attests nothing about a consumer |
| `asset_frozen` | no new rung — conjunctive seal over `present`+`qualified` (see §3) | no new state — at most re-asserts Producer ready | DATA_ACCEPTED capsule closure | **BARRED from Integrated, Deployed, Consumer value, Empirically evaluated** |
| `probe_accepted` | `present`+`qualified` for a service identity's response | Producer ready for service-type identities | PRODUCER_READY / service proof | **BARRED from `served`/Consumer value** — self-probe, no receiving operator, no effect trace. Nearest-miss candidate; still misses |
| `producer_covered` | `present` via lineage | Producer ready (inherited) | DATA_ACCEPTED (lineage limb) | Same bars as `accepted_rebuild_observed` |
| `empty_accepted` | `present` as honest absence | Producer ready (disposition) | DATA_ACCEPTED (empty disposition) | Same bars |
| `source_accepted`/`static_accepted` | `present` | Producer ready (disposition) | DATA_ACCEPTED (non-build) | Same bars |
| `retired_with_disposition` | none for an active identity | none | §7's protected-retired carve-out only (`ka_gochara_sweep`) | Strategy §7: "historical disposition satisfies the protected retired member, not an active materializer hold" |
| `foundation_lane_accepted` | campaign-scoped, not per-asset | Lane D carries the only deployment-shaped evidence in the table | — | **BARRED from per-asset Deployed** on two counts: lane-scoped not asset-scoped; evidenced by `ci_run_id` — exactly the excluded class |
| `stage_transition_accepted` | none | none — campaign stage bookkeeping | — | Stage arrival is not asset evidence; F13 bars label-inference |
| `asset_label_catalogue_accepted` | none | none — denominator/catalogue governance | — | n/a |
| `definition_superseded_mid_campaign` | none | none — definition lineage under `native_ruling` | — | n/a |

**Summary — F14/§8 gate coverage:**

| F14/§8 gate | Any admissible event_type? |
|---|---|
| Strategy agreed | **YES** — `optimization_verdict_accepted` (as decision record) |
| Producer ready | **YES** — `accepted_rebuild_observed`/`integrity_verified`/`probe_accepted`/disposition family |
| Integrated | **NO** |
| Deployed/operationally accepted | **NO per-asset type** — `foundation_lane_accepted` lane D is lane-scoped and CI-sourced, barred |
| Consumer value demonstrated | **NO** |
| Empirically evaluated | **NO** — explicitly out of L3 scope per the execution brief |

**Summary — F13 rung coverage:**

| F13 rung | Any admissible event_type? |
|---|---|
| `present` | **YES** |
| `qualified` | **YES** |
| `consumed` | **NO** |
| `effect_traceable` | **NO** |
| `served` | **NO** (`probe_accepted` is a self-probe, not a served channel) |
| `value_evaluated` | **NO** |

---

## 3. `asset_frozen`'s actual evidentiary scope

**It evidences nothing beyond data/integrity acceptance. It is a seal, not a rung.**

Three independent lines of evidence:

**(a) Its payload contains no downstream referent.** Every `t3` `asset_frozen` row carries exactly
`{analysis_digest, lifecycle_digest, registry_fingerprint_sha256}` with
`source_kind=server_reconstructed`, `source_ref=nirmana-elevation:freeze:<asset_id>`. No consumer,
channel, revision, deployed sha, operator, distinction or outcome appears anywhere in the payload.

**(b) The campaign's own auditor defines it as a conjunction over early rungs only.**
`platform/scripts/nirmana/capsule_audit.sql:29-41`:

```sql
bool_or(event_type = 'asset_analysis_accepted')       AS w2_analysis,
bool_or(event_type = 'optimization_verdict_accepted') AS w2_verdict,
bool_or(event_type = 'integrity_verified')            AS integrity_verified,
bool_or(event_type = 'asset_frozen')                  AS frozen,
bool_or(event_type IN ('accepted_rebuild_observed','probe_accepted','static_accepted',
                       'empty_accepted','producer_covered','source_accepted',
                       'retired_with_disposition'))   AS terminal_acceptance
...
WHERE frozen AND NOT (w2_analysis AND w2_verdict AND integrity_verified AND terminal_acceptance)
```

`asset_frozen` is valid iff analysis + verdict + integrity + one producer-side terminal event are
all present. **Every member of that `terminal_acceptance` disjunction is producer-side.** The
tooling's notion of "terminal" is therefore `DATA_ACCEPTED`-level — the strategy §7 row *below*
`LAYER_DATA_ACCEPTED`, three rows below the brief's actual delivery target.

**(c) F14 forbids the inference directly.** Contract §3.2: "a green test or producer receipt
cannot skip a state." `asset_frozen` is definitionally a producer receipt over other producer
receipts. F13: "no rung inferred from a later/earlier label" — the word "frozen" reading as
finality is precisely the inference the rule bars.

**Conclusion:** `asset_frozen` covers `present`+`qualified` (F13) and at most `producer_ready`
(F14). It does **not** alone satisfy `CONSUMER_INTEGRATED`, `DEPLOYED_ACCEPTED` or
`VALUE_EVALUATED`, and it is barred from all three. Applying the §N.8 test directly: *what code
path would have to run, and fail, for `asset_frozen` to correctly read false on consumer
integration?* There is none — the freeze writer never looks at a consumer. Under §N.8 the consumer
limb of that signal is **null, not green**.

---

## 4. `CONSUMER_INTEGRATED`/`VALUE_EVALUATED` — event-type gap analysis

### 4.1 The finding, stated plainly

**`CONSUMER_INTEGRATED` has ZERO admissible event types. `VALUE_EVALUATED` has ZERO admissible
event types.** All 17 event types are producer-side, campaign-internal, or governance/bookkeeping.
Not one carries a receiving-operator identity, an output-effect trace, a delivery/replay survival
check, a baseline comparison, or a consumer distinction.

```bash
grep -rn "CONSUMER_INTEGRATED\|VALUE_EVALUATED\|consumer_value_demonstrated\|value_evaluated" \
  platform/scripts/nirmana/
# → no matches
```

The strings appear only in strategy/brief prose, as *targets*, never as an emitted or emittable
receipt.

### 4.2 Why the gap is definitional, not incidental

Strategy §7 (lines 397, 399):

> `CONSUMER_INTEGRATED` | Authorized receiving operators use the new data; important fields
> influence outputs and survive delivery/replay.
>
> `VALUE_EVALUATED` | Specified consumer distinctions and usefulness have actually been tested
> through the receiving operator; presence, retrieval and operational success are insufficient.

Both predicate on an authorized receiving operator external to the producer. Every existing
event's `source_kind` is one of `git_commit`, `build_run`, `campaign_authorization`,
`server_reconstructed`, `governed_catalogue`, `native_ruling` — all producer-side or
campaign-internal. There is no `source_kind` that could carry an operator's attestation, so the
gap cannot be closed by reusing an existing type with different content; the receipt schema itself
does not exist.

The gate matrix reinforces this: Consumer value demonstrated "may not be claimed from
computational influence or richer prose" — meaning even a hypothetical "the consumer read this
field" event would be insufficient; the required exit is "correct added distinction/prevented
error/uncertainty/comprehension plus error/burden/cost" against "a simpler baseline." Nothing in
the current schema records a baseline.

### 4.3 The consequence for `Accepted N/22`

**Until a receipt is designed and emitted for `CONSUMER_INTEGRATED` and `VALUE_EVALUATED`, no L3
asset can honestly count toward `Accepted N/22`** as the execution brief defines acceptance
(`delivery_target` = `LAYER_DATA_ACCEPTED + scoped CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED +
VALUE_EVALUATED`). The maximum truthfully claimable state for any asset under the current event
vocabulary is `DATA_ACCEPTED` — two named states short.

This gap is structural, not a backlog item: it is not that events are missing for L3 specifically,
it is that the event type does not exist for any layer. L0/L1/L2's frozen identities (across all
revisions) are in the same position — `asset_frozen` there also evidences only the producer side.

**No receipt is designed here, per the task's own instruction.** The gap is established; the
design is a separate, named decision.

### 4.4 A third gap, flagged in passing

`DEPLOYED_ACCEPTED` has **no per-asset event type either**. The only deployment-shaped evidence in
the table is `foundation_lane_accepted` lane D — `{"lane_id":"D","main_sha":"…","ci_run_id":"…",
"serving_sha":"…"}`. This is (a) lane-scoped, not asset-scoped, and (b) evidenced by `ci_run_id` —
which §8 names explicitly in the excluded column for that gate. It carries no migration/
managed-path receipt or rollback-readiness limb for an individual asset. So `DEPLOYED_ACCEPTED` is
a **weaker but real** gap: unlike the other two it has an adjacent artifact, but at the wrong
grain, sourced from a barred class.

Corroborating the practical reality, `MADHAV_DUAL_CAMPAIGN_EXECUTION_PLAN_v1_0.md` §2 already
diagnoses `DEPLOYED_ACCEPTED` as *unreachable* since 2026-09-16 because deploy steps were being
skipped — "→ 0/22 guaranteed regardless of execution quality." The same conclusion, reached here
from the event schema alone, by an independent route.

---

## 5. Worked example — F1's before/after, live

F1's defect: readiness reads that omit `definition_revision`, aggregating evidence across *all*
superseded definitions. Re-run live, on the exact query shape the finding concerns:

**Unscoped (the defect):**

```sql
SELECT layer, count(DISTINCT entity_id) FROM nirmana_evidence.nirmana_elevation_campaign_events
WHERE event_type='asset_frozen' GROUP BY 1 ORDER BY 1;
-- L0 | 40 · L1 | 19 · L2 | 22 · L3 | 13  ← 13 L3 identities appear frozen · L5 | 4
```

**Scoped to the current frozen definition (correct):**

```sql
SELECT layer, count(DISTINCT entity_id) FROM nirmana_evidence.nirmana_elevation_campaign_events
WHERE event_type='asset_frozen' AND definition_revision='t3-2026-09-11-8b884eac' GROUP BY 1 ORDER BY 1;
-- L2 | 8  ← L3 absent entirely: 0
```

**L3 = 13 frozen unscoped vs. 0 scoped.** This reproduces the prior cycle's `DOMAIN_A.md` figure
exactly and confirms the correction. The 13 are artifacts of `t0`/`t1`/`t2`, all superseded by
native ruling (`definition_superseded_mid_campaign`: `t1←t0` binding 580 events, `t2←t1` binding
187, `t3←t2` binding 86).

**Residual observation, independently reconfirmed by the conductor:** in this audit worktree,
**neither `egate.sql` nor `capsule_audit.sql` contains the string `definition_revision`**:

```bash
grep -c "definition_revision" platform/scripts/nirmana/egate.sql \
                              platform/scripts/nirmana/capsule_audit.sql
# egate.sql:0
# capsule_audit.sql:0
git log --oneline -3 -- platform/scripts/nirmana/egate.sql
# 45f06e68b feat(nirmana): shared read-only E-gate batch-eligibility tool (charter C2/C10) (#1722)
```

**PR #2706's repair is on a separate branch (`l3/egate-definition-scope`), not this audit
branch.** Confirmed queued in GitHub's merge queue as of this cycle. Until it merges to `main`,
this audit's own `capsule_audit.sql` predicate still aggregates across all four definition
revisions — its `WHERE frozen AND NOT (...)` check can be satisfied by an analysis emitted under
`t0` for a freeze emitted under `t3`.

**STALE as of cycle 8 — retained above as an accurate snapshot of its own cycle, not corrected in
place.** PR #2706 merged to `main` (`9b3c3b219`) before cycle 6 closed and is now an ancestor of
this branch; `egate.sql` and `capsule_audit.sql` both now contain `definition_revision` scoping
(`grep -c` → 4 and 7 respectively). Cycle 8 re-ran the now-fixed `capsule_audit.sql` live and
reproduced this section's own §3 "0 scoped" figure for L3 exactly, this time as the tool's actual
current output rather than a hand-rolled equivalent query — see `KALA_ENVIRONMENT_READINESS_AUDIT_
v1_0.md`'s Domain A addendum and decision-list item 18 for the authoritative current record.

---

## 6. Bottom line for the campaign's acceptance arithmetic

1. **17 event types exist; all are producer-side, campaign-internal, or governance.**
2. **F13 rungs covered: `present`, `qualified`. Rungs with zero admissible evidence: `consumed`,
   `effect_traceable`, `served`, `value_evaluated`.**
3. **F14 states covered: `strategy_agreed`, `producer_ready`. States with zero admissible
   per-asset evidence: `integrated`, `deployed_operationally_accepted`,
   `consumer_value_demonstrated`, `empirically_evaluated`.**
4. **`asset_frozen` is a conjunctive seal over producer-side evidence and evidences nothing
   downstream of `DATA_ACCEPTED`.** Reading it as terminal acceptance is exactly the §N.8
   unearned-signal defect and exactly the F13/F14 label-inference the contract forbids.
5. **`CONSUMER_INTEGRATED` and `VALUE_EVALUATED` require designed receipts that do not exist in
   any form.** `DEPLOYED_ACCEPTED` requires a per-asset receipt whose only adjacent artifact is at
   the wrong grain and sourced from an explicitly barred class.
6. **Therefore `Accepted N/22` is currently 0/22 by two independent routes:** no L3 asset has any
   `t3` event at all (§1), and even a fully-evidenced asset could reach at most `DATA_ACCEPTED`
   under the existing vocabulary (§4.3).
