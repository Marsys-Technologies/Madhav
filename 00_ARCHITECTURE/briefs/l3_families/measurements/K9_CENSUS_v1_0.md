---
artifact: K9_CENSUS_v1_0.md
version: "1.0"
status: PRE_BUILD_UNMEASURED
authority: "SR-A4-01; code/declaration only"
---

# K9-5 · Rehearsal census

No production census, certification, rebuild, publication or retirement is asserted.
An imported file is inspection evidence; this tool does not authenticate it or issue certificates.
Every `null` is unmeasured. Expectations never overwrite observations.

**(I) INTERPRETATION:** pre-build prepares the full PLAN §8 population, including
historical/superseded assets. Missing future census records stay null; a smaller
active population must be reconciled explicitly after K9-4b and KR-1/KR-2.
Alternative: wait for those operations before preparing this report.

**(I) INTERPRETATION:** detector-NONE raw readings are preserved for inspection.
Every reading other than NO_DETECTOR is separately flagged `detector_none`,
including a current engine rule-computed N/A; no certifier admission is inferred.
Alternative: discard the entire census on the first such cell.

Registry revision: 30; fingerprint: `b1acb3f678b5c8fbe343b93d96d8f2db24e2d024b15412aa960056b98bc5f23c`.

## Bound inputs

- `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md` · SHA-256 `85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef`
- `platform/scripts/governance/asset_census.py` · SHA-256 `523f50ea74e24875f650f13b0659d4ee6165a0ec0eb864124b2e3d3fccf8c60b`
- `platform/scripts/governance/asset_declarations.json` · SHA-256 `e045ada2e6844ee53c59010ff5502157db8aa0d960b64c9468791ce2ba761bad`

PLAN §7 defines the nine gates; PLAN §9 K8 exit requires the measured expected
reading, including honest NO_DETECTOR. Current engine rules supersede the old
detector snapshot only for this inspection; no plan or engine contract is edited.

## Per-asset gates

Cells are **expected / observed**. No expected PASS is pre-assigned.

| Asset | Ldgr | Idem | Earn | Null | Vocab | Carr | Narr | Dens | Build |
|---|---|---|---|---|---|---|---|---|---|
| `ka_gochara_v5` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_gochara` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_gochara_v3_century_materialize` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_gochara_v4_41_candidate` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_gochara_sweep` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_gochara_resonance` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_vedha_gochara` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_moorti_nirnaya` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_kota_chakra` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_tithi_pravesha` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_sudarshana_varsha` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_graha_sancara` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_dasha_kala` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_avadhi` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_yojaka` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_sangam` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_vighnakara` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_kshetra` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_kalasutra` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_kala_darshana` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_jivana_parva` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_bhavishya_lekha` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_taranga` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_tulana` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |
| `ka_muhurta_seva` | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null | null / null |

## Detector constraints

| Criterion | Revision | Detector | Recordable constraint | Source |
|---|---|---|---|---|
| `Build.registered` | 3 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:186` |
| `Build.contract` | 2 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:187` |
| `Build.target` | 2 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:188` |
| `Build.dag` | 4 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:189` |
| `Build.count_integrity` | 4 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:190` |
| `Build.completion` | 7 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:191` |
| `Build.exercised` | 3 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:192` |
| `Build.history` | 3 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:193` |
| `Build.dep_liveness` | 3 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:194` |
| `Idem.pattern` | 5 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:195` |
| `Earn.build_record` | 3 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:196` |
| `Vocab.identity` | 3 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:207` |
| `Vocab.alias` | 10 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:208` |
| `Ldgr.source_presence` | 6 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:209` |
| `Dens.served` | 14 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:210` |
| `Narr.agree` | 8 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:211` |
| `Narr.checkable` | 8 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:212` |
| `Narr.fidelity_test` | 7 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:213` |
| `Narr.lint` | 7 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:214` |
| `Null.schema_default` | 11 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:215` |
| `Null.blank_rows` | 11 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:216` |
| `Carr.D1` | 5 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:225` |
| `Carr.D2` | 3 | `NONE` | NO_DETECTOR | `platform/scripts/governance/asset_census.py:226` |
| `Carr.D3` | 4 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:227` |
| `Earn.service_state` | 2 | `asset_census.py:measure()` | null; must be measured | `platform/scripts/governance/asset_census.py:229` |

## Population and evidence

- `ka_gochara_v5`: **stage (judge)** — Pravāha; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:331`.
- `ka_gochara`: **supersede** by `ka_gochara_v5` per Pravāha's strangler (asset id decision is Pravāha's, concept §8.6); `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:332`.
- `ka_gochara_v3_century_materialize`: **supersede** by the judge + compact evaluator; data retained; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:333`.
- `ka_gochara_v4_41_candidate`: **historical** once `'5.0'` lands; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:334`.
- `ka_gochara_sweep`: **historical**; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:335`.
- `ka_gochara_resonance`: **core → F1** (target discovery becomes relationship-record projection) + corrections R-1…R-6; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:336`.
- `ka_vedha_gochara`: **adapter**; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:337`.
- `ka_moorti_nirnaya`: **adapter, gated** (`method_contested`); `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:338`.
- `ka_kota_chakra`: **adapter** (`uncited_extension`); `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:339`.
- `ka_tithi_pravesha`: **adapter, gated**; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:340`.
- `ka_sudarshana_varsha`: **adapter → judge method** at enrichment step 2; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:341`.
- `ka_graha_sancara`: **service** = `kala_core.sky` facade, and the only ephemeris door for every stage; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:342`.
- `ka_dasha_kala`: **service = F2**; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:343`.
- `ka_avadhi`: **F2 materialised** (re-purposed, same id); `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:344`.
- `ka_yojaka`: **stage (F1)**; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:345`.
- `ka_sangam`: **stage (jury)**, rewritten; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:346`.
- `ka_vighnakara`: **stage (negative space)**, rewritten; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:347`.
- `ka_kshetra`: **stage (forecaster)**, repaired first (G1), re-shaped only on a specified G2; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:348`.
- `ka_kalasutra`: **projection**; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:349`.
- `ka_kala_darshana`: **projection**; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:350`.
- `ka_jivana_parva`: **projection**; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:351`.
- `ka_bhavishya_lekha`: **registrar** (issued forecasts); `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:352`.
- `ka_taranga`: **read model** (monthly `∫λ` per event class; domain only through a declared mapping); `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:353`.
- `ka_tulana`: **service**, wired; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:354`.
- `ka_muhurta_seva`: **service** = `kala_core.calendar`; `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:355`.

```json
{
  "source": null,
  "summary": {
    "planned_assets": 25,
    "observed_assets": 0,
    "missing_assets": 25,
    "observed_gates": 0
  },
  "mismatches": [],
  "certifier_refusals": []
}
```

## Execution and activation gates

- K9-4b rebuild/verification and KR-1/KR-2 dispositions must complete or be explicitly ruled not applicable.
- Capture a real guarded off-production L3 census with registry revision/fingerprint, declarations SHA-256/version and explicit chart scope.
- Supply independently reviewed per-gate expectations; inspect raw measurements, effective checks, missing assets and all mismatches.
- Resolve detector_none conflicts through the campaign; a rule-computed N/A in the engine is not certifier admission.
- Code merge alone does not complete the dependent operations or authorize activation.

## Reproduce

```sh
GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 python3 platform/scripts/governance/kala_rehearsal_census.py --format markdown --out 00_ARCHITECTURE/briefs/l3_families/measurements/K9_CENSUS_v1_0.md --check
# Later, inspect a supplied off-production census (no connection is opened):
GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 python3 platform/scripts/governance/kala_rehearsal_census.py --census /path/to/census_L3.json --expectations /path/to/expected.json
```

Expectations JSON: `{ "ka_avadhi": { "Idem": "PASS", "Build": null } }`.
A missing expectation remains null. Exit 0 means the report was produced, never that the layer passed.
Tests are auto-discovered by mandatory Governance Tool Tests (pytest), via ci_shard.py.
