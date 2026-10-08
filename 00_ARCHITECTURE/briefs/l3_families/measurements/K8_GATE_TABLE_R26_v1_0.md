---
artifact: K8_GATE_TABLE_R26
version: "1.1"
status: CURRENT
purpose: "Reconcile Kāla plan §7 certification table to the live criterion registry revision 26."
source_plan: "KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §7"
source_registry: "platform/scripts/governance/asset_census.py CRITERION_REGISTRY"
registry_snapshot:
  ref: "origin/main@9a99847dfe8be93e3133b734d7a4d5f71f6a1582"
  blob: "310bf9154acba1ab70e33c556c7b51e5ebe15dad"
  registry_revision: 26
changelog:
  - "1.1 (2026-10-08): refresh the main snapshot; Vocab.alias rev 8 and Build.history rev 3, including registered aliases, certification-window evidence and verified sibling credit; enumerate the remaining Earn, Vocab, Carr and Narr revision differences."
---

# K8 gate table — registry revision 26

## Scope and reading rule

This is a read-only reconciliation. It records what the current census can earn;
it does not declare a result for any asset. Every source locator below is the
`CRITERION_REGISTRY` entry read for that row. Gate records remain census-derived:
`nikasha_certify.py` refuses a caller-invented verdict and refuses a non-
`NO_DETECTOR` result when the registry says `NONE` (module header, lines 1–31).

The plan's §7 table was written at registry revision 25. This table freezes the
revision-26 source named in `registry_snapshot`: its commit, blob and the
per-criterion revisions below are the reviewable input. “Revision” below is the
per-criterion revision, not a claim that every row changed in registry revision
26.

| Gate | Live criterion/revision and registry source | What it reads | Verdict an implemented Kāla mechanism can earn |
|---|---|---|---|
| Ldgr | `Ldgr.source_presence` rev 6 — `asset_census.py:196` | Declared K1/K2/K3/LEDGER source resolves on every judged row; placeholders and unresolved ids fail; declared residual source can earn only its checked N/A ceiling. | PASS only for fully resolved declared sources; otherwise FAIL, PARTIAL, NO_DETECTOR, or a rule-computed N/A. |
| Idem | `Idem.pattern` rev 4 — `asset_census.py:182` | Writer-owned-table mutation pattern, including declared update-only intent. | PASS for a detectable replace/upsert pattern; update-only may be checked N/A; dynamic/contradictory scope cannot be claimed PASS. |
| Earn | `Earn.build_record` rev 3 — `asset_census.py:183`; `Earn.service_state` rev 2 — `asset_census.py:216` | Attempt/probe record, and for services the declared probe, health and freshness. | PASS after the measured record/probe meets its criterion; FAIL/PARTIAL/NO_DETECTOR otherwise; checked no-writer cases may be N/A. |
| Null | `Null.schema_default` rev 9 — `asset_census.py:202`; `Null.blank_rows` rev 9 — `asset_census.py:203` | Defaults, placeholder rows, checked convention/clean scan and, where declared, forwarded L1 leaves. | PASS only through the stated earned path; otherwise the measured lower verdict or a rule-computed N/A. |
| Vocab | `Vocab.identity` rev 2 — `asset_census.py:194`; `Vocab.alias` rev 8 — `asset_census.py:195` | Declared key plus non-empty data; value-level vocabulary and alias forms, not merely column names. Registered ontology aliases are accepted by plain case-fold only; a declared `code_vocabulary` credits only the committed two-letter ALL-CAPS graha codes in its named columns. | PASS when the measured identity/alias form holds; the justified no-alias form may be N/A. An unread or empty live alias source is NO_DETECTOR; unregistered variants and undeclared abbreviations retain their failing verdicts. |
| Carr | `Carr.D1` rev 4 — `asset_census.py:212`; `Carr.D2` rev 2 — `asset_census.py:213`; `Carr.D3` rev 3 — `asset_census.py:214` | D1 passage match with its citation state; D2 has detector `NONE`; D3 needs either complete-row independent re-derivation or the declared `build_recorded_second_calculation` provenance receipt, digest and latest completed-build binding. | D1/D3 can earn PASS only when their stated evidence is measured; D2 is `NO_DETECTOR`. A rule-computed N/A is possible only where its declared rule is satisfied. |
| Narr | `Narr.agree` rev 7 — `asset_census.py:198`; `Narr.checkable` rev 6 — `asset_census.py:199`; `Narr.fidelity_test` rev 6 — `asset_census.py:200`; `Narr.lint` rev 7 — `asset_census.py:201` | Declared prose/no-prose, checkability, independent golden coverage, and narration lint. | Checked `prose_none` can be N/A; prose mechanisms earn only the detector’s measured verdict — fidelity PASS requires the declared, verified golden form. |
| Dens | `Dens.served` rev 14 — `asset_census.py:197` | One actual capability entry both serves the asset and selects a closed/declaration-backed tier, or the declared uniform-authority form. | Structural PASS is possible; otherwise FAIL/PARTIAL/NO_DETECTOR. |
| Build | `Build.registered` rev 3 (`asset_census.py:173`), `Build.contract` rev 2 (`asset_census.py:174`), `Build.target` rev 2 (`asset_census.py:175`), `Build.dag` rev 4 (`asset_census.py:176`), `Build.count_integrity` rev 3 (`asset_census.py:177`), `Build.completion` rev 6 (`asset_census.py:178`), `Build.exercised` rev 3 (`asset_census.py:179`), `Build.history` rev 3 (`asset_census.py:180`), `Build.dep_liveness` rev 3 (`asset_census.py:181`). | Registration/contract, target and actual reads, count and integrity SQL, latest attempt, current-code history, and dependency liveness. When `produced_tables` is declared, completion compares the writer's `rows_written` to the declared, scoped produced-set sum; an unread writer scan is PARTIAL and an omitted written table is FAIL. | Each cell earns independently. Completion cannot hide an error/aborted latest attempt. History judges attempts since the later writer-digest or registry-identity change, with certification starting no earlier than the source-pinned bottom-up pass. The pass timestamp must be read and cross-checked; the latest attempt must be complete and no unexplained error or abort may remain. Only pinned run/cause explanations are excluded, and a verified writer sibling may inherit its primary’s measured history. No current-code attempt or an unread/undeterminable history window is `NO_DETECTOR`, never certification PASS. |

## Differences from plan §7 requiring the live table

| Plan §7 statement | Live revision 26 reading | Revision that introduces the relevant live rule |
|---|---|---|
| Registry revision 25; Ldgr rev 4 only counts source presence. | Registry is 26; Ldgr rev 6 validates declared source forms, including resolution of LEDGER ids and residual ceilings. | `Ldgr.source_presence` rev 6 |
| Idem rev 2 and a fixed replace-candidate description. | Rev 4 additionally recognises only a checked `update_only` N/A; unsupported/dynamic mutation remains non-PASS. | `Idem.pattern` rev 4 |
| Earn build record was rev 1. | Rev 3 still requires a measured duration-bearing attempt for a writer; a no-writer N/A must agree with the declaration, registry and decorator scan, with actual attempts checked against that definition. | `Earn.build_record` rev 3 |
| Earn service state has detector `NONE`. | The live `Earn.service_state` is a census detector over declared probe health/freshness. | `Earn.service_state` rev 2 |
| Null uses rev 3 and only its original convention wording. | Both Null criteria are rev 9, with the checked `prose_none` and forwarded-leaf paths. | `Null.*` rev 9 |
| Vocab identity was rev 1. | Rev 2 requires the declared key and non-empty data; a declaration alone earns nothing. | `Vocab.identity` rev 2 |
| Vocab alias is rev 2 and tied only to the narrow plan declaration. | Alias is rev 8 and value-keyed; a column name alone never proves or suppresses a vocabulary finding. Registered live ontology aliases use plain case-fold without trimming, NFKC or diacritic folding. Declared code columns may credit only the committed graha abbreviations; unavailable alias evidence remains NO_DETECTOR. | `Vocab.alias` rev 8 |
| Carr D1 was rev 2. | Rev 4 measures a declared transcription against its cited passage and permits only the applicable checked transcription/not-a-transcription ceilings. | `Carr.D1` rev 4 |
| Carr D2/D3 are both `NONE`. | D2 remains `NONE`; D3 is a measured rev-3 re-derivation/recorded-second-calculation criterion. | `Carr.D3` rev 3 |
| Narr agree, checkable and lint were all rev 2. | Checked `prose_none` and any declared carriage coupling govern the no-prose N/A; an empty `prose_fields` list alone is insufficient. Checkability retains chart-scoped reads and cannot PASS on zero checkable rows; lint measures fact-category pins and raw tokens. | `Narr.agree` rev 7; `Narr.checkable` rev 6; `Narr.lint` rev 7 |
| Narr fidelity can only reach PARTIAL. | The live rev-6 fidelity criterion can PASS only with declared, independently verified literal golden coverage; bare structural discovery remains capped. | `Narr.fidelity_test` rev 6 |
| Dens is rev 6. | Dens is rev 14; the real served SELECT, closed tier vocabulary, facet attribution and uniform-authority form are required. | `Dens.served` rev 14 |
| Build is described as one build-time certification sentence. | Build cells are independently measured. Rev-6 completion compares a declared `produced_tables` set—not `count_sql`—to `rows_written`: each table is read in its declared filtered/chart scope; UPDATE-only tables the scan sees are excluded; any writer-written but undeclared table FAILs; and a scope the scan cannot fully read is PARTIAL. A latest `error`/`aborted` attempt fails even where an old `lit` state remains. | `Build.completion` rev 6 (the produced-set/latest-attempt rules are registry-26 rules) |
| Build history is treated as the build's undifferentiated past. | The rev-3 history cell judges attempts since the later writer-digest or registry-identity change on main, bounded by the source-pinned certification pass. Its build-run timestamp must match the declared instant; latest completion and absence of unexplained errors/aborts are required. Explanations match only a pinned run and cause, never every failure. Verified writer siblings may inherit the primary’s measured verdict; absent or unverified primary evidence earns nothing. Pre-window history remains reported. Missing current-code attempts or unread/undeterminable window evidence are `NO_DETECTOR`, not PASS. | `Build.history` rev 3 |

## Carriage rule and hand-off

The row above changes the requirements a writer declaration may need to meet,
especially declared Ldgr source resolution, Carr.D3, Narr fidelity and Dens.
That is not silently treated as a plan edit. The companion campaign report asks
ADHIKĀRIN to record the plan-table supersession and to create any implementation
work required by an affected writer.

## Verification

The criterion revisions remain independent of the registry’s global revision 26:
this refreshed snapshot includes the later N-233/N-235 alias and N-233/N-236
history rules without changing any detector, writer, gate or production state.

- Every gate row cites its exact registry entry above, frozen by the
  `origin/main` commit and source blob in the front matter.
- The difference table names each changed criterion revision and covers the
  plan’s Build completion/produced-set equality, declared scope and unread-scan
  bounds, Build history window and `NO_DETECTOR` cases, Dens served-surface,
  carriage rules, Ldgr source forms, and all resulting certification ceilings.
- Compatibility: documentation/declaration only; no runtime effect.
