"""
scripts.kala_admission -- D-3 wave/D-3/ADMIT kernel admission loop.

Doctrine-Waves D-3, BRIEF_D3.md §F1: "v1 kernel = dasha-capability steps +
slow-transit pulses + SAV potency; each further current stays only if the
T-0 blind-battery score improves. Weights are earned against lived history,
not doctrine."

TRAIN-ONLY. Never reads, filters-out-after-fetching, or otherwise touches
any LEL event dated on/after 2020-01-01 (the sealed test split, per
ESCALATION_POLICY_v1_0.md §4). See lel.py's module docstring for exactly how
that boundary is enforced (server-side date_to filter at fetch time, plus a
belt-and-suspenders assertion re-checked at every scoring call site).
"""
