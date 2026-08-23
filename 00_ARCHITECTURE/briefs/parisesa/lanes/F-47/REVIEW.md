---
lane: F-47
stream: S3_SATYA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-47/SPEC.md, F-47/DIAGNOSIS.md. No REVIEW_LEADS.md present.
Source read at /Users/Dev/par-night/main-ro (origin/main read-only mirror).

Verified directly against source:
- muhurta.py lines 70-73, 231, 372, 420, 462, 468, 483-495, 813-815, 858, 908-957
- main.py include_router calls (all of them)
- brahmagyan/phala/l4_muhurta.py function signatures
- routers/muhurta_score.py imports and scoring engine
- tests/test_phala_muhurta.py fixtures (_get_muhurta_module, NATIVE_CHART_ID, _fake_panchanga_row)
- Grep for FACTOR_DOMAIN_SENSITIVITY / TRANSIT_QUALITY_BASIS (confirmed absent)

No code was run; all exit-test failure modes traced line-by-line against current signatures.

## Q1 — Mechanism vs symptom

PASS. The spec identifies the exact mechanism: `_dasha_quality_for_chart` (muhurta.py:372) and `_transit_quality_for_window` (muhurta.py:420) lack an `action_type` parameter. The spec shows the exact signature changes, internal logic changes (per-domain significations table for dasha; per-domain weekday table for transit), and call-site threading at :813-815/:858. Root cause addressed, not merely observed output.

## Q2 — Diagnosis sub-claims mapped

PASS. §8 of the SPEC provides an explicit coverage table for all 8 sub-claims.

F-47 C1 (shared engine): confirmed by sibling trace §5 + §7 rollback grep; informational, no code change needed.
F-47 C2 (dasha 30% + transit 20% action-blind): §2a (dasha) + §2b (transit) both add action_type.
F-47 C3 (only panchanga+signal domain-sensitive): §2a-2c close the gap; §6 recurrence guard makes coverage machine-verifiable.
F-47 C4 (same top window ranks #1 across domains): §8 honestly marks this as an expected downstream consequence, data-dependent, not re-tested — correct scope call.

F-48 C1 (no real transit computation): §3 explicitly states NOT computationally resolved; disclosed via TRANSIT_QUALITY_BASIS.
F-48 C2 (lunar-phase + weekday approx still true after fix): §2b + §2c disclosure.
F-48 C3 (§N.8 earned-signal): §2c TRANSIT_QUALITY_BASIS + §6 inspect-based guard together supply a real detector.
F-48 C4 (docstring admission): preserved and tightened in §2b docstring, now cross-referenced to machine-readable field.

All 8 D-sub-claims mapped. No unmapped claim found.

## Q3 — Exit test failure on current code

PASS — traced against current signatures:

`TestDashaAndTransitQualityDomainSensitivity` (3 tests):
- `test_dasha_quality_varies_by_action_type_for_native`: calls `_dasha_quality_for_chart(chart_id, window_start, "marriage")`. Current signature is `(chart_id, window_start)` — raises `TypeError: _dasha_quality_for_chart() takes 2 positional arguments but 3 were given`. RED.
- `test_transit_quality_varies_by_action_type`: calls `_transit_quality_for_window(window_start, "marriage")`. Current signature `(window_start)` — `TypeError`. RED.
- `test_transit_quality_general_action_type_preserves_legacy_numeric_output`: calls `_transit_quality_for_window(window_start, "general")` — `TypeError`. RED. (See note below.)

`TestFactorDomainSensitivityDisclosure` (3 tests):
- All three access `mod.FACTOR_DOMAIN_SENSITIVITY` or `mod.TRANSIT_QUALITY_BASIS`. Grep confirms neither constant exists in muhurta.py. Every test raises `AttributeError`. RED.

`TestGenerateMuhurtaWindowsFactorsIncludeDisclosure` (1 test):
- Accesses `factors["factor_domain_sensitivity"]`. Current `factors` dict (muhurta.py:914-944) has no such key. Raises `KeyError`. RED.

All 7 exit tests confirmed RED on current code.

**Note on `test_transit_quality_general_action_type_preserves_legacy_numeric_output`:** the SPEC's RHS is a self-consistency tautology (`X == pytest.approx(X)`). After the fix this test passes trivially regardless of whether action_type="general" actually preserves the legacy numeric output. The SPEC explicitly acknowledges this and instructs Build to replace the RHS with a literal captured from the pre-fix code. The test IS red today (TypeError), so the exit-test red-state requirement is met; the tautology only affects the post-fix strength of this specific assertion and is a Build-stage responsibility per the spec's own note.

## Q4 — Sibling sites

PASS. SPEC §5 exhaustively enumerates all four scoring functions.

`_panchanga_quality_for_action` (muhurta.py:231): already action-type-aware — N/A, unmodified. Verified: signature at :231 takes `action_type: str`. ✓
`_signal_activation_for_action` (muhurta.py:468): already action-type-aware — N/A, unmodified. Verified. ✓
`_dasha_quality_for_chart` and `_transit_quality_for_window`: both covered by fix.

Exclusions verified:
- `l4_muhurta.py`: SPEC says not mounted on any FastAPI router. Verified in main.py — all include_router calls enumerated; no reference to `l4_muhurta`. Dead code exclusion valid. Its own `_dasha_quality`/`_transit_quality` functions (confirmed at lines 194, 265) are already action_type-aware — not the defect site.
- `routers/muhurta_score.py`: SPEC says uses a different scoring engine. Verified: imports `panchang_engine.muhurat.score_muhurat()` exclusively; no calls to `_dasha_quality_for_chart` or `_transit_quality_for_window`. Exclusion valid.
- Narration layers (elect.ts, ritual.ts, now.ts): excluded as out-of-S3-file-lease — stated reason, correct per stream map.

## Q5 — Recurrence guard

PASS. `TestFactorDomainSensitivityDisclosure::test_factor_domain_sensitivity_matches_real_function_signatures` uses `inspect.signature(fn).parameters` to cross-check each factor's `FACTOR_DOMAIN_SENSITIVITY` map entry against whether the actual function currently accepts `action_type`. This is a genuine structural detector: if a future edit removes `action_type` from any scoring function without updating the map (or vice versa), the test fails closed. Not a weak proxy — it inspects real function signatures at test time.

## Q7 — Verified assumptions / citation accuracy

PASS — all file:line citations verified against source:

| Cited location | Claim | Verified |
|---|---|---|
| muhurta.py:70-73 | WEIGHT_PANCHANGA/DASHA/TRANSIT/SIGNAL constants | ✓ exact |
| muhurta.py:231 | `_panchanga_quality_for_action` signature with `action_type` | ✓ exact |
| muhurta.py:283-288 | `_MARRIAGE_VARA` / vara sets | ✓ exact |
| muhurta.py:372 | `_dasha_quality_for_chart(chart_id, window_start)` — no action_type | ✓ exact |
| muhurta.py:420 | `_transit_quality_for_window(window_start)` — no action_type | ✓ exact |
| muhurta.py:462 | `day_boost` flat weekday table | ✓ exact; "general" row in SPEC matches byte-for-byte |
| muhurta.py:468 | `_signal_activation_for_action(action_type, chart_id)` | ✓ exact |
| muhurta.py:484-495 | `_NATIVE_SIGNALS` dict | ✓ exact |
| muhurta.py:813-815 | `dasha_q = _dasha_quality_for_chart(chart_id, range_start)` / `signal_q = ...` | ✓ exact |
| muhurta.py:858 | `transit_q = _transit_quality_for_window(current)` | ✓ exact |
| muhurta.py:908-957 | `windows.append({... "factors": {...}})` — no disclosure keys | ✓ exact |
| FACTOR_DOMAIN_SENSITIVITY / TRANSIT_QUALITY_BASIS absent | grep confirms zero matches | ✓ exact |

One minor internal inconsistency in SPEC documentation (non-blocking):
- SPEC frontmatter: "fork_status: ... applying PRATINIDHI's standing precedent SP-1 ... NOT PAR-R-8"
- SPEC §3 body: "Per the conductor's ruling (PAR-R-8, applying the same rule...)"

The frontmatter explicitly corrects PAR-R-8 as a misattribution, but §3's body text was not updated to match. The actual standing rule cited ("choose the option that discloses more") is the same in both places, and Option B is the mechanically correct choice regardless of the ruling label. This is a documentation inconsistency only; it does not affect the correctness of the fix or the exit tests.

No citation points to a comment or wrong line. No fabricated computation claim found. `writer_asset`/`data_delta`/RS-A fields not present in this SPEC (S3 file-lease lane with no writer-layer involvement — no rebuild policy entries needed).

## Verdict: COMPLETE

All five rubric questions pass. The spec correctly identifies mechanism (not symptom), maps all 8 D-sub-claims, provides 7 exit tests all confirmed RED on current code, covers all sibling sites with verified exclusion reasoning, and supplies a genuine structural recurrence guard. All cited line numbers verified accurate against main-ro source. One SPEC doc inconsistency (PAR-R-8 vs SP-1 in §3 body) is minor and non-blocking. The backward-compat test tautology is acknowledged and explicitly delegated to Build.
