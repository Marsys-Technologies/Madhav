---
artifact: K8_GATE_TABLE_R26
version: "1.0"
status: CURRENT
purpose: "Reconcile Kāla plan §7 certification table to the live criterion registry revision 26."
source_plan: "KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §7"
source_registry: "platform/scripts/governance/asset_census.py CRITERION_REGISTRY"
---

# K8 gate table — registry revision 26

## Scope and reading rule

This is a read-only reconciliation. It records what the current census can earn;
it does not declare a result for any asset. Every source locator below is the
`CRITERION_REGISTRY` entry read for that row. Gate records remain census-derived:
`nikasha_certify.py` refuses a caller-invented verdict and refuses a non-
`NO_DETECTOR` result when the registry says `NONE` (module header, lines 1–31).

The plan's §7 table was written at registry revision 25. The checkout is revision
26. “Revision” below is the per-criterion revision, not a claim that all rows
changed in this registry revision.

| Gate | Live criterion/revision and registry source | What it reads | Verdict an implemented Kāla mechanism can earn |
|---|---|---|---|
| Ldgr | `Ldgr.source_presence` rev 6 — `asset_census.py:196` | Declared K1/K2/K3/LEDGER source resolves on every judged row; placeholders and unresolved ids fail; declared residual source can earn only its checked N/A ceiling. | PASS only for fully resolved declared sources; otherwise FAIL, PARTIAL, NO_DETECTOR, or a rule-computed N/A. |
| Idem | `Idem.pattern` rev 4 — `asset_census.py:182` | Writer-owned-table mutation pattern, including declared update-only intent. | PASS for a detectable replace/upsert pattern; update-only may be checked N/A; dynamic/contradictory scope cannot be claimed PASS. |
| Earn | `Earn.build_record` rev 3 — `asset_census.py:183`; `Earn.service_state` rev 2 — `asset_census.py:216` | Attempt/probe record, and for services the declared probe, health and freshness. | PASS after the measured record/probe meets its criterion; FAIL/PARTIAL/NO_DETECTOR otherwise; checked no-writer cases may be N/A. |
| Null | `Null.schema_default` rev 9 — `asset_census.py:202`; `Null.blank_rows` rev 9 — `asset_census.py:203` | Defaults, placeholder rows, checked convention/clean scan and, where declared, forwarded L1 leaves. | PASS only through the stated earned path; otherwise the measured lower verdict or a rule-computed N/A. |
| Vocab | `Vocab.identity` rev 2 — `asset_census.py:194`; `Vocab.alias` rev 7 — `asset_census.py:195` | Declared key plus non-empty data; value-level vocabulary and alias forms, not merely column names. | PASS when the measured identity/alias form holds; the justified no-alias form may be N/A. |
| Carr | `Carr.D1` rev 4 — `asset_census.py:212`; `Carr.D2` rev 2 — `asset_census.py:213`; `Carr.D3` rev 3 — `asset_census.py:214` | D1 passage match; D2 has no detector; D3 re-derivation or recorded second calculation. | D1/D3 can earn PASS when their declared measured forms hold; D2 is `NO_DETECTOR` (or only a registry-computed N/A). |
| Narr | `Narr.agree` rev 7 — `asset_census.py:198`; `Narr.checkable` rev 6 — `asset_census.py:199`; `Narr.fidelity_test` rev 6 — `asset_census.py:200`; `Narr.lint` rev 7 — `asset_census.py:201` | Declared prose/no-prose, checkability, independent golden coverage, and narration lint. | Checked `prose_none` can be N/A; prose mechanisms earn only the detector’s measured verdict — fidelity PASS requires the declared, verified golden form. |
| Dens | `Dens.served` rev 14 — `asset_census.py:197` | One actual capability entry both serves the asset and selects a closed/declaration-backed tier, or the declared uniform-authority form. | Structural PASS is possible; otherwise FAIL/PARTIAL/NO_DETECTOR. |
| Build | `Build.registered` rev 3 (`asset_census.py:173`), `Build.contract` rev 2 (`asset_census.py:174`), `Build.target` rev 2 (`asset_census.py:175`), `Build.dag` rev 4 (`asset_census.py:176`), `Build.count_integrity` rev 3 (`asset_census.py:177`), `Build.completion` rev 6 (`asset_census.py:178`), `Build.exercised` rev 3 (`asset_census.py:179`), `Build.history` rev 2 (`asset_census.py:180`), `Build.dep_liveness` rev 3 (`asset_census.py:181`). | Registration/contract, target and actual reads, count and integrity SQL, latest attempt, current-code history, and dependency liveness. | Each cell earns independently. Completion cannot hide an error/aborted latest attempt; no real exercise/history is not a certification PASS. |

## Differences from plan §7 requiring the live table

| Plan §7 statement | Live revision 26 reading | Revision that introduces the relevant live rule |
|---|---|---|
| Registry revision 25; Ldgr rev 4 only counts source presence. | Registry is 26; Ldgr rev 6 validates declared source forms, including resolution of LEDGER ids and residual ceilings. | `Ldgr.source_presence` rev 6 |
| Idem rev 2 and a fixed replace-candidate description. | Rev 4 additionally recognises only a checked `update_only` N/A; unsupported/dynamic mutation remains non-PASS. | `Idem.pattern` rev 4 |
| Earn service state has detector `NONE`. | The live `Earn.service_state` is a census detector over declared probe health/freshness. | `Earn.service_state` rev 2 |
| Null uses rev 3 and only its original convention wording. | Both Null criteria are rev 9, with the checked `prose_none` and forwarded-leaf paths. | `Null.*` rev 9 |
| Vocab alias is rev 2 and tied only to the narrow plan declaration. | Alias is rev 7 and value-keyed; a column name alone never proves or suppresses a vocabulary finding. | `Vocab.alias` rev 7 |
| Carr D2/D3 are both `NONE`. | D2 remains `NONE`; D3 is a measured rev-3 re-derivation/recorded-second-calculation criterion. | `Carr.D3` rev 3 |
| Narr fidelity can only reach PARTIAL. | The live rev-6 fidelity criterion can PASS only with declared, independently verified literal golden coverage; bare structural discovery remains capped. | `Narr.fidelity_test` rev 6 |
| Dens is rev 6. | Dens is rev 14; the real served SELECT, closed tier vocabulary, facet attribution and uniform-authority form are required. | `Dens.served` rev 14 |
| Build is described as one build-time certification sentence. | Build cells are independently measured; rev-6 completion checks declared `produced_tables` rather than treating `count_sql` as the produced set, and rejects a latest error/aborted attempt even where an old `lit` state remains. | `Build.completion` rev 6 |
| Build history is treated as the build's undifferentiated past. | The live history cell judges only attempts since the later writer-digest or registry-identity change; pre-window failures are reported but not judged, and no current-code attempt is `NO_DETECTOR`. | `Build.history` rev 2 |

## Carriage rule and hand-off

The row above changes the requirements a writer declaration may need to meet,
especially declared Ldgr source resolution, Carr.D3, Narr fidelity and Dens.
That is not silently treated as a plan edit. The companion campaign report asks
ADHIKĀRIN to record the plan-table supersession and to create any implementation
work required by an affected writer.

## Verification

- Every gate row cites its exact registry entry above.
- The difference table names each changed criterion revision and covers the
  plan’s Build completion/produced-table framing, Build history window,
  Dens served-surface/carriage rules, Ldgr source forms, and all resulting
  certification ceilings.
- Compatibility: documentation/declaration only; no runtime effect.
