---
lane: F-48
stream: S3_SATYA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: F-48/SPEC.md (pointer stub), F-48/DIAGNOSIS.md, F-47/SPEC.md (combined spec). No REVIEW_LEADS.md present. Verified all cited file:line references against `/Users/Dev/par-night/main-ro/platform/python-sidecar/brahmagyan/phala/muhurta.py` directly. Checked `tests/test_phala_muhurta.py` for existing conventions. Checked `main.py` router mounts. Checked `l4_muhurta.py` for ephemeris imports and router registration. Traced exit-test failure modes against current source without running.

## Q1 — Mechanism vs symptom?

Yes. The spec targets the mechanism: `_transit_quality_for_window` has no `action_type` parameter (F-47 domain-blindness) and no ephemeris computation at all (F-48 earned-signal gap). The fix adds `action_type` to both `_dasha_quality_for_chart` and `_transit_quality_for_window`, adds a disclosure constant `TRANSIT_QUALITY_BASIS`, and adds `FACTOR_DOMAIN_SENSITIVITY` as a machine-verifiable map. These are structural changes to the function signatures and module-level state, not cosmetic patches to symptoms.

## Q2 — Every diagnosis sub-claim mapped?

F-48/DIAGNOSIS.md has four claims (C1-C4); all mapped in §8 of F-47/SPEC.md:

- C1 (no real planetary-transit computation): Mapped — Option B chosen per conductor ruling; gap disclosed via `TRANSIT_QUALITY_BASIS`, not computationally resolved. Honestly stated in §8.
- C2 (lunar-phase + static weekday approximation): Mapped — §2b keeps lunar-phase component invariant (classical justification given), domain-sensitizes weekday component; disclosure via §2c.
- C3 (§N.8 earned-signal violation): Mapped — §2c's `TRANSIT_QUALITY_BASIS` disclosure + §6's recurrence-guard test together give the claim a real detector.
- C4 (docstring admission): Mapped — §2b's updated docstring cross-references the new `factors.transit_quality_basis` field, making the admission machine-readable.

F-48/DIAGNOSIS §6 fork (Option A vs B): resolved explicitly in §3, with conductor ruling cited (SP-1 / PRATINIDHI precedent). No unmapped claims.

## Q3 — Would exit tests fail today?

Yes — traced line-by-line against current source:

1. `TestDashaAndTransitQualityDomainSensitivity`: calls `mod._dasha_quality_for_chart(NATIVE_CHART_ID, window_start, action_type)` — current signature at muhurta.py:372 is `(chart_id, window_start)` (2 args) → **TypeError** on first call. Similarly `_transit_quality_for_window(window_start, action_type)` against 1-arg signature at :420 → **TypeError**.

2. `TestFactorDomainSensitivityDisclosure`: accesses `mod.FACTOR_DOMAIN_SENSITIVITY` and `mod.TRANSIT_QUALITY_BASIS` — grep of main-ro muhurta.py for both names returns zero matches → **AttributeError**.

3. `TestGenerateMuhurtaWindowsFactorsIncludeDisclosure`: reads `factors["factor_domain_sensitivity"]` — current `factors` dict at :914-918 has four keys (panchanga_quality, dasha_quality, transit_quality, signal_activation) and none of the two new keys → **KeyError**.

All three test classes provably fail today on unmodified origin/main.

**Note on backward-compat test:** `test_transit_quality_general_action_type_preserves_legacy_numeric_output` as written is a placeholder self-comparison (x == x); it also fails today with TypeError (same 1-arg signature issue). The spec honestly discloses this at §4 and assigns BUILD the responsibility of capturing the pre-fix float before touching the function. Acceptable.

## Q4 — Sibling sites covered?

The four sub-score functions:
- `_panchanga_quality_for_action` (:231): N/A, already action_type-aware — excluded with reason (it is the reference pattern the fix copies).
- `_dasha_quality_for_chart` (:372): covered in §2a.
- `_transit_quality_for_window` (:420): covered in §2b.
- `_signal_activation_for_action` (:468): N/A, already action_type-aware — excluded with reason.

Other sites excluded with stated reasons:
- `l4_muhurta.py`: VERIFIED not mounted on any FastAPI router — main.py's `include_router` calls list `phala_muhurta_router` (from muhurta.py) and `muhurta_score_router`, not l4_muhurta.py. Dead code, exclusion correct.
- `muhurta_score.py`: stated not in the kala_muhurta_get/kala_elect_get call chain; exclusion correct (mounted at :102 but per DIAGNOSIS documented as having "no live caller").
- Narration layers (elect.ts, ritual.ts, now.ts): out of S3 file lease — exclusion correct, additive new keys available for those layers.

## Q5 — Recurrence guard genuine?

Yes. `test_factor_domain_sensitivity_matches_real_function_signatures` (§4/§6) uses `inspect.signature` to verify that each factor function's actual parameters include `action_type` and cross-checks against `FACTOR_DOMAIN_SENSITIVITY`'s per-factor claim. This is a real detector: if a future edit removes `action_type` from any fixed function, or adds it without updating the map, the test fails closed. It is not a static assertion about a constant value — it tests the relationship between the constant and the live function signatures. Strong §N.8-class guard.

## Q7 — Unverified assumptions / citation accuracy?

All key citations verified against main-ro:

- `muhurta.py:372` — `_dasha_quality_for_chart` def: CONFIRMED (2-arg signature, returns 0.72 for native).
- `muhurta.py:420-465` — `_transit_quality_for_window` body: CONFIRMED verbatim (function body matches DIAGNOSIS §3 quote character-for-character, including day_boost table and return formula).
- `muhurta.py:468` — `_signal_activation_for_action` def: CONFIRMED.
- `muhurta.py:70-73` — WEIGHT_* constants: CONFIRMED.
- `muhurta.py:283-288` — `_MARRIAGE_VARA`/`_EDUCATION_VARA`/etc. sets: CONFIRMED.
- `muhurta.py:484-495` — `_NATIVE_SIGNALS` pattern cited as idiom to copy: CONFIRMED.
- `muhurta.py:813-815` — dasha_q/signal_q call site (both lack action_type today): CONFIRMED (line 814 = `_dasha_quality_for_chart(chart_id, range_start)`, line 815 = `_signal_activation_for_action(action_type, chart_id)`).
- `muhurta.py:858` — transit_q call site: CONFIRMED (`_transit_quality_for_window(current)` — no action_type).
- `muhurta.py:908-957` — factors dict assembly: CONFIRMED (ends at :957, no `factor_domain_sensitivity` or `transit_quality_basis` keys present).
- `FACTOR_DOMAIN_SENSITIVITY`/`TRANSIT_QUALITY_BASIS` absent from module: CONFIRMED (grep returns zero matches).
- No swisseph/ephemeris library imports in brahmagyan/phala/: CONFIRMED — l4_muhurta.py has "ephemeris" only in a comment, not an import; muhurta.py has it only in docstring prose.
- `l4_muhurta.py` not on any FastAPI router: CONFIRMED via main.py include_router audit.
- `test_phala_muhurta.py` uses `_get_muhurta_module()`/`NATIVE_CHART_ID`/`_fake_panchanga_row()` conventions: CONFIRMED (lines 27, 34, 58).

No unverified assumptions found. Every cited file:line matches what the spec claims.

## Verdict: COMPLETE
