---
artifact: K8_GATE_TABLE_R26
version: "1.2"
status: CURRENT
purpose: "Reconcile Kāla plan §7 certification table to criterion registry revision 29."
source_plan: "KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §7"
source_registry: "platform/scripts/governance/asset_census.py CRITERION_REGISTRY"
registry_snapshot:
  ref: "origin/main@3d39fe7ccad5b41c6c2f900d3134d5a5f6eb3ed4"
  blob: "56f5547e89a6eee3fa051a96a40126d34cec2adb"
  registry_revision: 29
changelog:
  - "1.2 (2026-10-12): reconcile all 25 criteria to revision 29; correct Carr.D1/D2/D3 to 5/3/4 and N-283 checked no_table carriage; add passive projections, integrity permission/read failures, corpus-derived modes and vocabulary JSON forms; commit the comparison oracle."
  - "1.1 (2026-10-08): refresh alias/history rules against registry revision 26."
---

# K8 gate table — registry revision 29

## Scope and reading rule

Read-only reconciliation of the plan's registry-25 table to the immutable main
snapshot above. The artifact id and R26 filename remain the K8-R26 brief's
published path; the title and registry_snapshot name the actual revision 29.
Every gate row cites each criterion's exact CRITERION_REGISTRY source line at
that commit. Criterion revisions are independent of the global registry revision.
This is a map of possible readings, never certification of an asset.

Owner decision N-152 dropped the certificate ledger. This document neither
creates nor requests ledger records. The legacy nikasha_certify.py module header
(lines 1–31 at the snapshot) remains evidence for refusals of invented verdicts,
unbound census evidence and caller-made N/A; it is not a request to reinstate
that workflow. Census N/A follows checked applicability and declared rules;
detector NONE supplies no invented PASS. Per-asset mappings consume the census
and the currently governed certification procedure.

| Gate | Criterion/revision and registry source | What it reads | Verdict an implemented Kāla mechanism can earn |
|---|---|---|---|
| Ldgr | `Ldgr.source_presence` rev 6 — `asset_census.py:209` | Declared K1/K2/K3/LEDGER source resolution on judged rows; placeholder/unresolved ids and checked residual ceilings. | PASS for fully resolved declared sources; otherwise FAIL/PARTIAL/NO_DETECTOR or checked N/A. |
| Idem | `Idem.pattern` rev 5 — `asset_census.py:195` | Own-table replace/upsert pattern, checked update_only intent and passive_projection (live view, writer writes no table). | PASS only for a detectable valid pattern; checked update-only/passive-projection/no-writer cases may be N/A; dynamic or contradictory scope earns no PASS. |
| Earn | `Earn.build_record` rev 3 — `asset_census.py:196`; `Earn.service_state` rev 2 — `asset_census.py:229` | Duration-bearing attempt/probe, declared service health/freshness and optional source-verified service_wiring. | PASS from actual measured evidence; healthy but stale verified wiring is PARTIAL, unhealthy FAIL, never-probed/unread evidence NO_DETECTOR. Checked no-writer cases may be N/A. |
| Null | `Null.schema_default` rev 10 — `asset_census.py:215`; `Null.blank_rows` rev 10 — `asset_census.py:216` | Defaults, blank/placeholder rows, verified null_convention or clean writer scan, checked prose_none and forwarded L1 leaves; corpus_derived mode boundaries below. | PASS only through an earned path. Checked no-prose or corpus-derived Mode 1 may be N/A; Mode 2 keeps both Null detectors. An unread or unsound declaration earns no release. |
| Vocab | `Vocab.identity` rev 3 — `asset_census.py:207`; `Vocab.alias` rev 9 — `asset_census.py:208` | Non-empty keyed data (including checked view logical_key); actual vocabulary values/registered aliases and opt-in code_vocabulary, JSON groups/keys/kinds and producer-pinned identifiers. | PASS only for measured canonical/registered values over the full scope. Empty/unread alias evidence is NO_DETECTOR. Unregistered spellings FAIL; incomplete reads and unread declared JSON paths retain their caps; checked no-alias/no-vocabulary cases may be N/A. |
| Carr | `Carr.D1` rev 5 — `asset_census.py:225`; `Carr.D2` rev 3 — `asset_census.py:226`; `Carr.D3` rev 4 — `asset_census.py:227` | D1 declared passage match; D2 detector NONE and declared no-per-witness-values rule; D3 independent complete-row re-derivation or build_recorded_second_calculation provenance; N-283 no_table applicability below. | D1/D3 can earn PASS only on measured evidence; D2 cannot earn PASS. Checked N/A includes no-per-witness-values and the three no-table-no-prose rules; otherwise unmeasured D2 is NO_DETECTOR. |
| Narr | `Narr.agree` rev 8 — `asset_census.py:211`; `Narr.checkable` rev 7 — `asset_census.py:212`; `Narr.fidelity_test` rev 7 — `asset_census.py:213`; `Narr.lint` rev 7 — `asset_census.py:214` | Declared prose/checkability, literal independent golden coverage and lint; checked prose_none, prose exclusions, wildcard JSON paths and corpus_derived modes. | Only the measured verdict is earned. Fidelity PASS needs declared verified golden coverage; bare discovered tests stay capped. Checked no-prose may be N/A; corpus-derived Mode 2 releases only agree/checkable, never fidelity/lint. |
| Dens | `Dens.served` rev 14 — `asset_census.py:210` | The same capability entry selects the asset tier and declares density_contract; closed tier vocabulary, facet attribution, uniform authority and depth-one helper credit. | Structural PASS only on the actual served read and checked declaration. Uniform authority additionally needs this run’s source reading; otherwise FAIL/PARTIAL/NO_DETECTOR. Checked dens_not_served may be N/A. |
| Build | `Build.registered` rev 3 — `asset_census.py:186`; `Build.contract` rev 2 — `asset_census.py:187`; `Build.target` rev 2 — `asset_census.py:188`; `Build.dag` rev 4 — `asset_census.py:189`; `Build.count_integrity` rev 4 — `asset_census.py:190`; `Build.completion` rev 7 — `asset_census.py:191`; `Build.exercised` rev 3 — `asset_census.py:192`; `Build.history` rev 3 — `asset_census.py:193`; `Build.dep_liveness` rev 3 — `asset_census.py:194` | Registration/contract, target/actual reads, count/integrity SQL, produced_tables sum, latest attempt, current-code history window and dependency liveness. | Each cell earns independently. Completion cannot hide latest error/abort or unread evidence. History needs current-window attempts and no unexplained failures; no attempt or undeterminable window is NO_DETECTOR. Checked service/static/passive-projection cases may be N/A; a declaration alone earns nothing. |

## Differences from plan §7

| Plan §7 reading | Registry-29 reading and limits | Criterion revision introducing the relevant rule |
|---|---|---|
| Global registry revision 25. | Snapshot is registry revision 29; global versions do not replace per-criterion revisions. | Global 29; per-criterion revisions below. |
| Ldgr rev 4 checks presence without resolving ids. | Declared source resolution now includes K1/K2/K3/LEDGER, not merely a non-null id; residual forms keep checked ceilings. | Ldgr.source_presence rev 6. |
| Idem rev 2 requires replacement. | Own-table update-only intent can be checked N/A; passive_projection needs a live view and a writer scope that writes no table. Neither declaration excuses a contradictory writer. | Idem.pattern rev 4 (update-only), Idem.pattern rev 5 (passive projection, N-430). |
| Earn build rev 1 and service detector NONE. | Duration-bearing attempts remain required for writers; no-writer release checks declaration/registry/decorator agreement and attempt dates. Declared service probes measure health and freshness; checked wiring still needs a fresh self-test. | Earn.build_record rev 3; Earn.service_state rev 2. |
| Null rev 3, original convention only. | Earned convention/clean scan, checked prose_none, forwarded leaves and declared constant phrases; corpus_derived Mode 1 can release both Null cells, Mode 2 cannot. | Null.schema_default rev 9 and Null.blank_rows rev 9 (checked forms); Null.schema_default rev 10 and Null.blank_rows rev 10 (N-431, registry revision 28). |
| Vocab key rev 1, alias rev 2, narrow declaration-only reading. | Non-empty data and checked keys remain required; views may use checked logical_key. Value-level reads, registered ontology aliases (plain case-fold only), declared graha code columns and checked JSON class/family forms are measured. Source failure never earns PASS. | Vocab.identity rev 2 (non-empty key), Vocab.identity rev 3 (view logical key); Vocab.alias rev 8 (registered aliases), Vocab.alias rev 9 (N-431/N-458 JSON groups/keys/kinds/identifiers). |
| Carr D1 rev 2; D2/D3 detector NONE. | D1 measured passage and checked transcription ceilings; D3 independent every-row re-derivation or the build-bound second-calculation form. D2 remains NONE, with its checked no-per-witness-values N/A. All three add checked no_table service applicability (N-283), not an automatic service exemption. | Carr.D1 rev 4 (not-a-transcription), Carr.D1 rev 5 (N-283); Carr.D2 rev 2 (no-per-witness-values), Carr.D2 rev 3 (N-283); Carr.D3 rev 3 (build-recorded second calculation), Carr.D3 rev 4 (N-283). |
| Narr rev 2 and fidelity capped even with golden tests. | Checked prose_none or independently verified golden form may earn the applicable reading. Corpus-derived release is mode-specific; lint never gets that release. | Narr.agree rev 7 and Narr.checkable rev 6 (checked forms), Narr.agree rev 8 and Narr.checkable rev 7 (N-431); Narr.fidelity_test rev 6 (verified golden), Narr.fidelity_test rev 7 (Mode 1 only); Narr.lint rev 7 (checked prose/lint_none). |
| Dens rev 6. | The same capability entry must contain both actual served SELECT and tier contract; closed/declaration-backed tiers, facets, uniform authority and depth-one helper credit are checked. | Dens.served rev 14. |
| Build is one undifferentiated build-time certification sentence. | Registration, contract, target, DAG and liveness are separate cells; no-writer/static declarations must agree with measured facts. Count-integrity recognises checked passive projections. Completion compares rows_written with the scoped produced_tables sum and uses latest-attempt/integrity evidence, as detailed below. | Build.registered rev 3; Build.contract rev 2; Build.target rev 2; Build.dag rev 4; Build.count_integrity rev 4 (passive projection); Build.completion rev 6 (produced-set/latest-attempt rules), Build.completion rev 7 (permission/read failure handling); Build.exercised rev 3; Build.dep_liveness rev 3. |
| Build history is the undifferentiated past. | Current-code history window and certification-pass floor; latest completion, only pinned run/cause explanations, verified sibling inheritance, and honest NO_DETECTOR on missing/unread window evidence. | Build.history rev 3 (N-233/N-236). |

## Carriage applicability (N-283)

The `no_table` service form releases D1, D2 and D3 only while these facts are
all checked: target_table empty, no count_sql table, no @register, no
produced_tables and no carriage nature. It means a service probe stores no value;
it cannot be inferred merely from kind=service or a blank declaration.
The measured causes are Carr.D1#measured:no-table-no-prose,
Carr.D2#measured:no-table-no-prose and Carr.D3#measured:no-table-no-prose.
D2 also has the separate no-per-witness-values rule (declared
carriage.per_witness_values false, N-156). Neither form invents a D2 detector.

For D3 build_recorded_second_calculation, one proven provenance receipt must
match the expected writer digest (including the verifier import closure), latest
completed build or later delta-skip, and every stored row's build_id. The writer
raises before insertion unless its independent second calculation derives and
matches every logical row. No persisted note is required; an unread, missing,
ambiguous, unproven or stale receipt is NO_DETECTOR, and contradicted rows FAIL.

## Completion and history bounds

With produced_tables declared, Build.completion compares rows_written to the
SUM of the declared, filtered/chart-scoped set, rather than to count_sql alone.
UPDATE-only tables seen by the scan are excluded; an undeclared writer-written
table FAILs, and an incomplete writer scope is PARTIAL. Counts alone do not earn
PASS when declared integrity SQL fails, is refused, oversize, errored or timed
out. SQLSTATE 42501 (permission denied) is NO_DETECTOR, never a verdict on the
data; the census role is not widened. An unread latest-attempt query cuts PASS
to PARTIAL and preserves other readings, including N/A. A latest started
error/aborted attempt FAILs despite an earlier lit record, with no age window;
a cascade blocked_dependency row never ran the writer and is not such an attempt.

Build.history judges attempts since the later writer-digest or registry-identity
change on main, bounded below by the pinned certification run
ca17639b-f3cf-42c7-9866-0a61f3855802. Its build_runs.created_at must be read and
cross-checked against 2026-10-07T20:18Z. Latest completion and no unexplained
error/abort are required; only a pinned run AND matching cause is explained.
Verified writer siblings may inherit a primary's measured history; absent,
unverified or unexercised primary evidence earns nothing. Pre-window errors are
reported separately. No current-code attempt, unread attempt tally or
undeterminable source/identity window is NO_DETECTOR, never PASS.

## Corpus-derived and vocabulary bounds

N-431 (registry revision 28) releases corpus_derived cells only after a
sha256-pinned parser, with every locally loaded file pinned and re-hashed,
reproduces every stored key and compared column from every cited chunk; a bounded
sample of uncited chunks must yield no row and derived rows must have no blank
string. A changed pin, unpinned loaded file or unread check is NO_DETECTOR for
that mode's governed cells; a stored mismatch reads Narr.agree FAIL.

Mode 1 (prose_fields null/undeclared) releases Narr.agree, Narr.checkable,
Narr.fidelity_test, Null.schema_default and Null.blank_rows together as checked
N/A. Mode 2 (non-empty prose_fields, every declared column covered by the
re-derivation) releases only Narr.agree and Narr.checkable; Null.schema_default,
Null.blank_rows, Narr.fidelity_test and Narr.lint keep their own readings.
Reproducibility does not prove a pinned parser writes no placeholder. In Mode 1
a mismatch leaves the other governed cells NO_DETECTOR; Mode 2 preserves their
own readings. Narr.lint has no corpus-derived release in either mode.

Vocab.alias rev 9 additionally checks JSON path groups (one class/family,
2–32 paths, hard total 128 per column), vocabulary keys at an exact prefix/depth,
mixed kinds (2–6 class/family pairs), and producer-constant identifier sets
(up to 64). Every actual member/value must match; unread declared paths retain
PARTIAL and a contrary value FAILs. Identifier exemptions never hide a whole
vocabulary term. Ownership-reading count_sql in an unrecognised shape reads
NO_DETECTOR rather than silently expanding scope. Registered ontology aliases
use plain case-fold without stripping, NFKC or diacritic folding; declared code
columns credit only committed two-letter ALL-CAPS graha codes.

## Hand-off and verification

This reconciliation changes no writer, declaration, migration, frozen plan or
production state. It records the limits any subsequent per-asset mapping must
meet. ADHIKĀRIN owns the plan-table supersession and any necessary writer work;
this document does not silently amend PLAN §7 or award asset certification.

The companion test_k8_gate_table.py compares all 25 criterion revisions and
source lines to the frozen registry AST without importing the census or reading
a database. It checks the nine-gate set, plan differences and the no_table,
corpus-derived and completion ceilings; stale carriage mutations must fail.
Run the offline oracle from the repository root:

```sh
python -m pytest -q -p no:cacheprovider 00_ARCHITECTURE/briefs/l3_families/measurements/test_k8_gate_table.py
```

For an older-document regression, set K8_GATE_TABLE_DOC to a saved copy of that
document; the same assertions must reject its stale revisions and missing rules.
Compatibility: documentation plus its comparison oracle only; no runtime effect.
