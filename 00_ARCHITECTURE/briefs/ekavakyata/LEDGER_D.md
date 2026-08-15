# EKAVAKYATA Stream D (DHARMA) Ledger

**Lead:** DHARMA-LEAD · Branch: `ekv/lead-dharma` · Worktree: `ekv-lead-dharma`
**Owns:** `platform/scripts/governance/**`, `.github/**`, new lint/test files anywhere,
governance docs named in D-05.
**Rule:** Heartbeats <=20min. Lints land WARN-first (continue-on-error: true); flip to
FAIL when allowlist empty or at close. Never break other streams with surprise red.

---

## Lane Status

| Lane | Description | Status | Branch / Marker |
|---|---|---|---|
| D-01a | no-local-aspect-dict lint | CLAIMED | ekv/lead-dharma |
| D-01b | no-local-dignity-table lint | CLAIMED | ekv/lead-dharma |
| D-01c | no-local-ayanamsha-map lint | CLAIMED | ekv/lead-dharma |
| D-01d | dualOutput-requires-toolName lint | CLAIMED | ekv/lead-dharma |
| D-01e | no-raw-internal-token-in-narrative lint | CLAIMED | ekv/lead-dharma |
| D-02 | Param-parity generator | PENDING | — |
| D-03 | Reachability CI | PENDING | — |
| D-04 | CL-00 controls battery (ekv_controls.py) | CLAIMED | ekv/lead-dharma |
| D-05 | Governance record | PENDING W2 | — |
| D-06 | Build-state honesty detector | PENDING W2 | — |
| D-07 | Dead-path census | CONTINUOUS | — |
| D-08 | Pointer-integrity failing tests | CLAIMED | ekv/lead-dharma |

---

## File Leases

```
platform/scripts/governance/check_no_local_aspect_dict.py
platform/scripts/governance/check_no_local_dignity_table.py
platform/scripts/governance/check_no_local_ayanamsha_map.py
platform/scripts/governance/check_dualoutput_requires_toolname.py
platform/scripts/governance/check_no_raw_token_in_narrative.py
platform/scripts/governance/ekv_controls.py
platform/scripts/governance/no_local_aspect_dict_allowlist.json
platform/scripts/governance/no_local_dignity_table_allowlist.json
platform/scripts/governance/no_local_ayanamsha_map_allowlist.json
platform/scripts/governance/dualoutput_toolname_allowlist.json
platform/scripts/governance/no_raw_token_narrative_allowlist.json
platform/scripts/governance/no_local_aspect_dict_fixtures/
platform/scripts/governance/no_local_dignity_table_fixtures/
platform/scripts/governance/no_local_ayanamsha_map_fixtures/
platform/scripts/governance/dualoutput_toolname_fixtures/
platform/scripts/governance/no_raw_token_narrative_fixtures/
.github/workflows/ekv-lints.yml
platform/scripts/governance/__tests__/test_d08_pointer_integrity.py
```

---

## Heartbeats

### T+0 (2026-08-16)
- Branch `ekv/lead-dharma` at main tip `63049a6e3`. Clean state.
- Read plan SS0,1,2(D),4,5. Read fact-category-pin-lint template + CI pattern.
- Read pp2-audit manifest for CL-00 controls + key findings (F-43, F-52, F-59, F-62, F-131, F-132).
- Confirmed dualOutput defect: `register_p1_aliases.ts:188` has `toolName='unknown_tool'` default; ~19 call sites inherit bad default.
- Confirmed no-local-aspect-dict sites: `primitives.py:189-194` (SPECIAL_DRISHTI_DEG), `ga_yoga_writer.py:1499-1504` (NB_GRAHA_DRISHTI), `ga_vargas_writer.py` (local special dict).
- Confirmed dignity sites: `ga_structural_writer.py:4872-4884` (4-way if/elif), `ga_vargas_writer.py::_compute_dignity` (local DIGNITY_TABLE lookup).
- Confirmed ayanamsha site: `register_p1_aliases.ts:39-43` (AYANAMSHA_ALIAS), 10 sites not using `resolveChartFactsAyanamsha`.
- BUILDING: D-04 (ekv_controls.py) + all D-01 lints + fixtures + CI job.
EKV-D01-CLAIMED 2026-08-16T00:00Z
EKV-D04-CLAIMED 2026-08-16T00:00Z
EKV-D08-CLAIMED 2026-08-16T00:00Z

### T+20
- D-04 ekv_controls.py BUILT: 27 controls, --cheap flag, psycopg2 SQL subset, lint self-test gate.
- D-01a (no-local-aspect-dict) BUILT: Python SPECIAL_DRISHTI_DEG / NB_GRAHA_DRISHTI pattern detection.
- D-01b (no-local-dignity-table) BUILT: dignity if/elif chain / DIGNITY_TABLE local-dict detection.
- D-01c (no-local-ayanamsha-map) BUILT: AYANAMSHA_ALIAS Record<string,string> detection in TS.
- D-01d (dualOutput-requires-toolName) BUILT: unknown_tool default detection + bare 1-arg call sites.
- D-01e (no-raw-internal-token-in-narrative) BUILT: signature_classes.join / raw token in _thesis/_text.
- All 5 lints: fixtures pass/fail + allowlist + CI job (WARN-first continue-on-error).
EKV-D01-BUILT 2026-08-16T00:20Z
EKV-D04-BUILT 2026-08-16T00:20Z
