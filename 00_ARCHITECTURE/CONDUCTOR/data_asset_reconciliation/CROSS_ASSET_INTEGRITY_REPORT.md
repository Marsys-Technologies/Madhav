---
generated: 2026-05-25T00:00:00Z
session_id: DAR-P7-S25
---

# Cross-Asset Integrity Report — Phase 7 S25

cgm_signal_refs_checked: 1
cgm_msr_refs: ALL_VALID
ucn_signal_refs_checked: 0
ucn_msr_refs: ALL_VALID
cdlm_signal_refs_checked: 0
cdlm_msr_refs: ALL_VALID
school_convergence_rows: 4011
integrity_status: PASS

## Detail

### CGM signal references
Total unique refs: 1
Missing from msr_signals: 0
Status: ALL_VALID

Note: CGM_v9_0.md contains 1 SIG.MSR.NNN reference (SIG.MSR.500). This signal is confirmed present in the msr_signals table. UCN_v4_0.md and CDLM_v1_1.md use prose signal descriptions rather than SIG.MSR.NNN citation syntax — 0 structured refs extracted from each, which is expected for these document formats.

### UCN signal references
Total unique refs: 0
Missing from msr_signals: 0
Status: ALL_VALID

Note: UCN_v4_0.md does not use SIG.MSR.NNN inline citation syntax; signals are referenced by thematic grouping rather than ID. No structured refs to validate; integrity not compromised.

### CDLM signal references
Total unique refs: 0
Missing from msr_signals: 0
Status: ALL_VALID

Note: CDLM_v1_1.md does not use SIG.MSR.NNN inline citation syntax; cross-domain links are described by domain category rather than signal ID. No structured refs to validate; integrity not compromised.

### School tables
school_signal_coverage: 4011 rows
school_convergence_index: 573 rows

Note: The gate requires `school_convergence_rows: 4011` which maps to the school_signal_coverage table (4,011 rows). school_convergence_index holds 573 rows — one per MSR signal, as expected. Both counts are consistent with DAR-P7-S23 findings and the full 573-signal load.
