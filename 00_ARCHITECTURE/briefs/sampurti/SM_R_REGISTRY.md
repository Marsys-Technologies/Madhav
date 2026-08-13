---
artifact: SM_R_REGISTRY.md
purpose: SAMPURTI ruling registry — every PRATINIDHI ruling recorded with ID, rationale, and operational instruction
created: 2026-08-13
location: 00_ARCHITECTURE/briefs/sampurti/
write_rule: PRATINIDHI (opus/max, fresh per decision) appends; conductors read; nobody overwrites.
---

# SM-R RULING REGISTRY

---

## SMR-1 — Measurement #4 Baseline Validity for the M4-to-M5 Delta

**Date**: 2026-08-13 ~12:00 IST
**Ruling authority**: NATIVE-PRATINIDHI (opus/max, fresh invocation)
**Requested by**: CAMPAIGN_COORDINATION.md DIRECTIVE item 7 (conductor-raised, R14-clean)

### Question

Measurement #4 was taken at ~04:02 IST on 2026-08-13 against the PRE-A1 field (snapshot `kfs_87484404af9d6fe9dc66a3d78812f8bc`, config_pin without gochara corpus digest fields, 6,708 windows across 6 event classes). After M4, the A1 gochara-pin code merged to main, A3 was dispatched, and the field is now rebuilding with a new config_pin that includes `{gochara_generation, gochara_calibration_state, gochara_corpus_digest}`. The rebuilt field will carry a different snapshot_id. Does M4 remain a valid pre-integration baseline for computing the M4-to-M5 delta (the DVIPRAMANA test), or must M4 be re-run against the completed post-A3 field before M5's delta is computed?

### Ruling: (b) — M4 STANDS AS-IS. The earlier baseline is valid.

### Rationale

The DVIPRAMANA test (SAMPURTI_ELEVATED_PLAN_v2_0.md section 4, SAMPURTI_IMPLEMENTATION_PLAN_v1_0.md section 4 P2/P3) asks one specific question: **does adding gochara corpus integration to the field improve predictive performance relative to the dasa-alone field?** M4 is, by design, the dasa-alone baseline -- it was taken on a field whose config_pin contained NO gochara corpus fields whatsoever. M5 will be taken on the post-A1 field whose config_pin DOES contain gochara corpus digest fields. That is exactly the before/after pair the experiment requires.

The directive's concern -- that the field was "torn down and is rebuilding" -- conflates two distinct things: (1) the field's current transient state (incomplete, 2,236 windows mid-rebuild) and (2) M4's recorded measurement. M4 was not measured against the current incomplete field; it was measured against the completed R2 field at snapshot `kfs_87484404af9d6fe9dc66a3d78812f8bc` when it held 6,708 windows across 6 classes. That snapshot's data is the measurement's ground truth, and it is permanently recorded in `MEASUREMENT_4_BASELINE_v1_0.md` and `MEASUREMENT_4_BASELINE_raw.json`. The field being rebuilt now does not retroactively change what M4 measured.

Re-running M4 against the post-A3 field would actually VIOLATE the DVIPRAMANA design: the post-A3 field incorporates the gochara corpus pin (A1's integration), so measuring both M4-prime and M5 against it would yield a delta of zero by construction -- both would be measured on the same integrated field. The whole point of M4 is that it captures performance BEFORE the gochara corpus pin existed in config_pin. That is what it captured, and that is what it should remain.

This is not a fitting violation (R13): no parameter was tuned to M4's result, and the M4-to-M5 delta definition was committed blind (R13/blind-before-effect) before any integration code ran. M4's pre-integration snapshot is the honest pre-treatment measurement; M5's post-integration snapshot is the honest post-treatment measurement. The delta between them is the experiment the plan designed.

### Operational instruction

1. The conductor proceeds directly to Measurement #5 once A3 completes and the post-A1 field is fully built (all 534 substeps, new snapshot_id with gochara corpus digest in config_pin).
2. M4 is NOT re-run. `MEASUREMENT_4_BASELINE_v1_0.md` and its raw JSON remain as published, unmodified (R14: never overwrite).
3. The M5 artifact must document the class-subset matching rule from SAMPURTI_ELEVATED_PLAN_v2_0.md section 7.2: the M4-to-M5 delta is computed on the matched class subset only (classes present in BOTH M4's 6-class field and M5's field); any G2-EARLY classes that appear only in M5 are reported as first-measurement rows, not as delta contributors.
4. M5's artifact must record both snapshot_ids (M4's `kfs_87484404af9d6fe9dc66a3d78812f8bc` and M5's new snapshot) and explicitly note the config_pin difference (no gochara fields vs. gochara fields present) as the treatment variable.

### Standards applied

- **R13 no-fitting absolute**: M4 was taken before A1 integration code reached main; no parameter was tuned to M4's result; the delta definition was blind-committed. No violation.
- **R14 measurement versioning**: M4 published BESIDE, never overwritten. M5 publishes BESIDE M4. Satisfied by instruction above.
- **R16 every-claim-detector-cited**: M4's claims (hit_rate, noise floor, skill) are computed by `w46_field_measurement4.py` with seed=42 and 1000 shuffles. The detector is cited and reproducible.
- **N.7 narration fidelity**: This ruling restates the DVIPRAMANA design's own definition (pre-integration vs. post-integration) without re-deriving or re-interpreting it. The plan's own words: "post-W-A field, measured BESIDE #4."

---

## SMR-2 — A6 Field Rebuild Dispatch after Native Cancellation of A4+A5

**Date**: 2026-08-13 22:45 IST (17:15 UTC)
**Ruling authority**: NATIVE-PRATINIDHI (opus, fresh invocation, R32 conductor request)
**Requested by**: SAMPŪRTI-Δ1 conductor (R32) — PARKED-NATIVE from R30/R31, two consecutive native CancelExecution calls

### Question

The native (mail.abhisek.mohanty@gmail.com) explicitly cancelled both A4 (exec mv7c5, after ~1h56m at 21:35 IST) and A5 (exec tkp7b, after only 19 minutes at 22:02 IST) via the CancelExecution API. No native signal to resume has appeared in the coordination file. The campaign is designed to run unattended overnight. The A6 checkpoint is resumable (74/534 substeps committed, 460 remaining). Should the conductor dispatch A6?

### Ruling: HOLD-A6 — PARKED-NATIVE

The conductor must NOT dispatch A6 until the native provides explicit approval.

### Rationale

- **Two consecutive deliberate API cancellations.** The native cancelled A4 (after 2h) and then started A5 and cancelled it after only 19 minutes. Starting and immediately cancelling A5 suggests the native reconsidered the decision to launch at all — not merely that A4 was inconvenient at bedtime.
- **CancelExecution is a conscious, authenticated act.** Not an accidental close or timeout.
- **The 19-minute A5 window is decisive.** If the native simply wanted to stop before sleep, they would not have launched A5 at all.
- **Asymmetry of error costs.** Wrongly HOLDING costs hours of delay. Wrongly DISPATCHING overrides an explicit native intervention — a categorical trust violation.
- **NATIVE-PRATINIDHI authority is delegated, not sovereign.** Two consecutive cancellations do not meet the "confidently inferred" bar for unilateral dispatch.

### Operational instruction

1. **Do NOT dispatch A6** until one of:
   - Explicit native message approving A6 (any authenticated channel)
   - Native triggers a build manually via Cloud Run API/UI
   - Native updates CLAUDECODE_BRIEF.md or governance artifact with "resume builds" directive
2. **Independent work while HOLD is in effect:** governance hygiene, S4 preparatory queries (read-only), heartbeat maintenance, checkpoint integrity verification (read-only), S7459 fix verification (read-only).
3. **Do NOT** auto-dispatch after N hours elapsed. Do NOT treat supervisor relaunch as implicit permission.
4. When native signals resume: conductor dispatches A6 immediately without further ruling, using the existing resumable checkpoint (74 substeps committed, 460 remaining).

### Standards applied

- **R16**: two verified CancelExecution audit log entries, native account attribution confirmed
- **§N.8 Earned-Signal**: "native wants builds to stop" is not confidently inferred from two cancellations — it requires the native to say so. But "native wants to keep running unattended" is also not confidently inferred. Ambiguity resolves to HOLD.

---
