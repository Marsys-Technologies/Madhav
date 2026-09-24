---
artifact: NATIVE_DECISIONS_2026-09-25
canonical_id: NATIVE_DECISIONS_2026_09_25
version: "1.0"
status: RULED
date: 2026-09-25
decision_owner: Native
recorded_by: L3 strategy session (madhav-e3)
role: "Eight decisions put to the native on 2026-09-25 with a recommendation each; the native's rulings, verbatim in effect, and what each unblocks."
---

# Native decisions, 2026-09-25

Eight decisions were put with a recommendation each. **Seven accepted as recommended; one changed.**

| # | decision | ruling | status |
|---|---|---|---|
| 1 | `bg_sarvatobhadra_grid` — which school's grid | "rule it" accepted **as a task, not as an answer** — the school itself is still unnamed | **OPEN in substance** |
| 2 | `bg_prashna_rules` — open the horary facility? | **Keep closed.** Nothing in L0 requires it; it deserves its own product decision | RULED |
| 3 | D-K merge gate — does one instrument satisfy it? | **Yes. One review discharges D-K.** The native extended this generally: where a review has been done once, the instrument is accepted | RULED |
| 4 | Who owns the `ka_sangam → ka_vedha_gochara` edge | **Gochara's migration 1084 owns it; Saṅgam withdraws its seed claim.** Two migrations for one edge is worse than the current state | RULED |
| 5 | Production changed outside the migration ledger | **Treat as urgent.** See the finding below — it is materially larger than the single migration this decision was framed around | RULED |
| 6 | Merge queue squashes Saṅgam's 119 commits | **Let it squash.** The evidence lives in the review artifacts, not the commit log. A one-way door, knowingly taken | RULED |
| 7 | Begin the consolidation onto one surface | **Yes, once 3–5 are settled** | RULED |
| 8 | Start L1 now, or finish L0 first | **CHANGED from the recommendation: finish L0 completely first.** L1 does not begin until L0 is wrapped | RULED |

## What each unblocks

- **3 + 4 + 6** release Saṅgam PR #2735: D-K is discharged, the edge has an owner, the history question is closed. The remaining CI failures are the two mechanical ones plus the RRV-01 defect, which is the Saṅgam author's.
- **5** is now the gate on **7**: the consolidation cannot merge onto a surface whose deployed state is unknown.
- **8** re-aims the campaign. The L0 packets W-L0-1 … W-L0-9 and the six corrections in the L0 instance's §7 are the work. **No L1 instance is written until they close.**
- **1** still needs a school named before `bg_sarvatobhadra_grid` can hold a row.

## Finding raised under decision 5 — larger than the decision assumed

Decision 5 was put as "migration 1084's body is in production but 1084 is not in the ledger." Measured
2026-09-25 against production, the gap is **not one migration**:

| migration | its effect in production | recorded in `_migrations_applied` |
|---|---|---|
| 1080 gochara_resonance_target_resolution_state | `gochara_resonance_map.target_resolution_state` **exists** | **no** |
| 1081 gochara_ledger_coverage_publication | `kala_gochara_coverage`, `kala_gochara_publication` **exist** | **no** |
| 1082 vedha_moorti_stamp_columns | `kala_vedha_gochara` 17 → **20** cols, `kala_moorti_nirnaya` 22 → **26**, both with `source_qualification`, `precision_regime`, `corpus_verifiable` | **no** |
| 1084 wp7_k1_v1_registry_edges | `ka_sangam` and `ka_kshetra` both carry `ka_vedha_gochara` in `depends_on` | **no** |
| 1087 contacts inclusivity/completeness/tier_basis | `kala_gochara_contacts` carries `comparable_with` | **no** |

`SELECT filename FROM _migrations_applied WHERE filename ~ '^(108[0-9]|109[0-5])_'` returns **nothing**.

**This happened during the session, not historically.** An earlier measurement the same day recorded
`kala_vedha_gochara` at 17 columns with none of the three stamps; it now has 20 with all three.

**Why it matters beyond tidiness.** Every instrument that answers "what is deployed?" reads
`_migrations_applied`. This session's own tracker did, and consequently reported 1080–1091 as
*pending* when their effects are live — so the tracker's deployed-vs-code figure was wrong in the
direction that matters: it understated what production already carries. Any consolidation, any
rollback plan and any "is this safe to merge" answer built on that ledger is unreliable until the
ledger and production agree.

This is the mirror of the hazard CLAUDE.md §N.4 names. That rule warns of migrations silently doing
nothing while a deploy reports success. Here migrations did something while the ledger reported
nothing. The same detector closes both: **compare the ledger against production structure, not
against the deploy's own report.**

**Not established:** who applied them, by what path, and whether the bodies applied match the
committed files. Those are execution-session questions; this session measured the divergence and
stopped.
