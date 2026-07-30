---
artifact: SAMAPTI_T0_BASELINE
canonical_id: SAMAPTI_T0_BASELINE
version: 1.0
status: CURRENT
created: 2026-07-30
author: SAMĀPTI lane A1-PRESERVE (builder, Opus)
governs: >
  The governance-violation reference point every SAMĀPTI lane measures against.
  CONDUCTOR_PROMPT §8.8 and BRIEF v2.0 §1 both require "no NEW violation attributable
  to this campaign", measured against a baseline captured at T0 — NOT "green".
  This file is that baseline.
measured_at_commit: cdb6fc3b3d37e3b586f188649c59e57c251ed935
measured_at_ref: origin/main
---

# SAMĀPTI — T0 governance baseline

**Read this before claiming any governance result in this run.** The standard is *zero new
violations against these numbers*. It is **not** "the detectors are green" — they are not green
and are not expected to be. Both tools exit `3`, which is the project's tolerated-residual exit
code per `ONGOING_HYGIENE_POLICIES_v1_0.md §F` (CI cadence + exit-code-3 `known_residuals`
whitelist).

## §1 — The numbers

Two measurements are recorded, because they differ and the difference is attributable to this
lane. Reporting only one of them would be dishonest.

| Measurement | Tree | drift_detector | schema_validator | exit codes |
|---|---|---|---|---|
| **T0-PRISTINE** | `origin/main` @ `cdb6fc3b`, working tree clean | **216 findings** | **43 violations** | 3 / 3 |
| **T0-POST-A1** | `origin/main` + this lane's two recovery commits | **216 findings** | **45 violations** | 3 / 3 |

**T0-PRISTINE is the canonical baseline** for every lane that branches from `origin/main`.

**T0-POST-A1 is the baseline that applies once lane A1-PRESERVE merges.** The `+2` is real,
attributable, and explained in §3 — it must not be mistaken for a regression introduced by a
later lane.

`216 / 43` independently reproduces the figures `session_queue_SAMAPTI.yaml` §E1-SAMGATI 8.8
asserts from the consolidation session ("216/43 are tolerated exit-3 residuals"). That agreement
is corroboration, not the source: the numbers below were measured, not copied.

## §2 — Composition of the baseline (T0-PRISTINE)

**drift_detector — 216 findings** (215 MEDIUM, 1 LOW):

| Count | Class |
|---|---|
| 84 | `registry_disagreement` |
| 77 | `canonical_unreferenced` |
| 52 | `phantom_reference` |
| 1 | `governance_stack_disagreement` |
| 1 | `schema_file_empty` |
| 1 | `a3_schema_db_unreachable` |

Note `a3_schema_db_unreachable`: one finding is a *live-DB probe that could not run* in this
environment, not a corpus defect. A lane that later runs with DB reachability may see 215 + a
different A3 outcome. That is an environment delta, not a campaign regression — check the class
before counting it as new.

**schema_validator — 43 violations** (21 MEDIUM, 22 LOW):

| Count | Rule family |
|---|---|
| 31 | `frontmatter_field_missing` |
| 11 | `session_log_entry_missing_next_objective_heading` |
| 1 | `current_state_last_session_id_disagreement` |

## §3 — The +2 this lane is accountable for

Committing the recovered work-at-risk moves `schema_validator` from 43 → 45. Both new violations
are **pre-existing defects in the recovered files as they were authored** — they became visible
the moment the files stopped being untracked. Neither was introduced by an edit; this lane edited
nothing.

```
MEDIUM  frontmatter_field_missing[architecture_governance/artifact]
        00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md
        Required key 'artifact' not present

MEDIUM  frontmatter_field_missing[l3_domain_reports/artifact]
        03_DOMAIN_REPORTS/REPORT_WHOLE_CHART_SYNTHESIS_AND_MCP_DIAGNOSTIC_v1_0.md
        Required key 'artifact' not present
```

**Why they are not fixed here.** Lane A1-PRESERVE's governing constraint is BRIEF v2.0 §3.1:
*"Nothing in this track is edited for content — this is preservation, not revision."* Adding an
`artifact:` frontmatter key is a content edit to another campaign's authored document. Fixing
them inside this lane would trade a disclosed 2-violation delta for an undisclosed scope
violation. The delta is disclosed instead.

**Disposition required from the Conductor/DVA — pick one, do not leave it implicit:**
1. Accept `216 / 45` as the operative baseline from A1's merge onward (zero-cost, recommended); or
2. Assign the two frontmatter additions to a lane authorized to edit content
   (`B-DOCS-GOVERNANCE` is the natural home) and hold the baseline at `216 / 43`.

Either is defensible. What is not defensible is a later lane being blamed for these two, or
`E1-SAMGATI` reporting `45` as "zero new" without saying which baseline it used.

## §4 — Reproduction

Both tools default to manifest mode; the env vars are set explicitly so the run is not
environment-dependent. Run from a clean checkout of the measured ref:

```bash
git worktree add --detach /tmp/t0 origin/main

cd /tmp/t0
DRIFT_DETECTOR_USE_MANIFEST=true python3 platform/scripts/governance/drift_detector.py \
  --repo-root /tmp/t0 --session-id SAMAPTI-A1-T0-PRISTINE \
  --json-path /tmp/t0_drift.json --report-path /tmp/t0_drift.md
# expect: drift_detector: 216 findings; exit=3

SCHEMA_VALIDATOR_USE_MANIFEST=true python3 platform/scripts/governance/schema_validator.py \
  --repo-root /tmp/t0 --session-id SAMAPTI-A1-T0-PRISTINE \
  --json-path /tmp/t0_schema.json --report-path /tmp/t0_schema.md
# expect: schema_validator: 43 violations; exit=3
```

Counts are read from `drift_report.summary` / `schema_validation_report.summary` in the JSON, not
from stdout parsing.

**Caveat on reproducibility, stated rather than discovered later:** `216` includes one finding
(`a3_schema_db_unreachable`) whose value depends on whether the local Cloud SQL Auth Proxy at
`127.0.0.1:5433` is up — a known recurring failure surface (BRIEF v2.0 §1, T1.6). A reproduction
attempt with a live DB may legitimately differ by that one finding. Compare by class, not by
total alone.

## §5 — How a later lane uses this file

- Re-run both tools on your branch.
- Compare **by class and by path**, not by total. A total that matches can still hide a swap.
- Any finding whose `path` is a file your lane touched is yours. Report it.
- A finding that disappears is also a delta worth stating — silent improvement is still drift
  from the baseline, and E1-SAMGATI's `8.8` check should be able to account for it.

---

*End of SAMAPTI_T0_BASELINE v1.0. Measured by lane A1-PRESERVE at `origin/main` `cdb6fc3b`,
2026-07-30. Raw JSON + markdown reports for both runs were produced under the session scratchpad
and are regenerable byte-for-byte via §4.*
