---
artifact: DRAFT_CLAUDECODE_BRIEF_U2_LIFETIME_PRANA_v0_1.md
canonical_id: DRAFT_CLAUDECODE_BRIEF_U2_LIFETIME_PRANA
brief_for: U2 — ka_sangam LIFETIME horizon + persisted PRĀṆA (level-5) [upstream enabler, L3 reopen]
status: DRAFT v0.1 — STUB; Prāṇa half confirmed by reconciliation Q5
version: 0.1
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D1, D2; supreme expansion §2.8)
classification: UPSTREAM-ENABLER (L3) — sequenced SECOND (after U1, D2); the temporal-extremes frontier
---

# DRAFT BRIEF — U2 Lifetime + Prāṇa (L3 reopen)

> Two temporal extremes the convergence engine structurally supports but does not yet reach: the
> full-life horizon, and sub-month (Prāṇa) grain. The heaviest lift in the expansion; sequenced after
> U1 and the prediction spine proves out (D2). Captures the known design; sized by reconciliation Q5.

## §0 — What is CODE-VERIFIED
- `ka_sangam` (`services/ka_sangam/engine.py`) runs Mode A + Mode B over a **5-year forward horizon**
  (`_HORIZON_YEARS = 5`); the horizon is a parameter, not a structural limit.
- `ka_dasha_kala` can compute **Prāṇa (level-5, ~36-day grain)** in-memory (`prana_grain=True`,
  `is_prana_computed` flag) but **NEVER persists it** — `chart_dashas` stops at level-4 (Sūkṣma).
- The convergence math (I-16/I-17) is grain-agnostic — it works at any temporal resolution.

## §1 — The two halves

### Half A — Lifetime horizon
Re-parameterize `ka_sangam` to run a **full-life sweep** (birth → ~100y) once, so predictions sit in a
lifetime arc, not a rolling 5-year window. This is a horizon-control change + a heavier batch run
(more windows). The engine already supports it; the work is (a) the parameterization, (b) the compute
budget, (c) storing the lifetime windows without blowing the row budget (likely a coarser lifetime
tier + the fine 5-year tier coexisting).

### Half B — Persisted Prāṇa (level-5) `[RECON Q5 confirms level-4 is the current ceiling]`
Persist Prāṇa intervals so convergence can narrow a window to a specific ~5-week peak. Requires:
- Extending `chart_dashas` to hold level-5 (or a dedicated `chart_dashas_prana` table to avoid
  bloating the 536k-row table) — a schema decision to make at finalization.
- Wiring `ka_sangam` to optionally compute convergence at Prāṇa grain for high-value windows (not all
  — Prāṇa over a lifetime × 9 levels is enormous; apply it selectively to top-ranked windows).

## §2 — The value (D1 full ambition)
"This 80-year-arc-significant event peaks in a specific fortnight." No human computes a lifetime ×
Prāṇa grid (9 levels deep over 100 years). Lifetime context + sub-month precision together are the
prediction frontier.

## §3 — Infra implication (the one place new infra may be justified)
The lifetime × Prāṇa compute is the heaviest in the whole program. Options to decide at finalization:
- a dedicated Cloud Run batch job for the lifetime sweep; OR
- a bounded-horizon default (5-year fine) + on-demand lifetime/Prāṇa deepening for specific queries.
Recommend the **selective** approach: lifetime at coarse grain always; Prāṇa only for top-ranked
windows. Keeps compute bounded.

## §4 — Standards
- REOPENS the L3 seal → version bump + re-seal of `L3_KALA_CLOSE` (D2).
- Frozen orchestrator contract preserved (extend via the existing `ka_sangam` writer, never change the
  orchestrator).
- Ratified I-16/I-17 unchanged (grain-agnostic).
- Sequenced SECOND (after U1); the L4 revision consumes the enriched temporal substrate.

## §5 — Acceptance criteria (provisional)
1. `[pytest]` `ka_sangam` runs a lifetime sweep producing windows across the full life arc (coarse tier).
2. `[pytest]` Prāṇa-grain convergence narrows a known top window to a sub-month peak.
3. `[schema]` Prāṇa persisted (level-5 in chart_dashas OR chart_dashas_prana) without bloating the existing tree.
4. `[compute]` the selective approach keeps the row/compute budget bounded (documented bound).
5. `[re-seal]` L3_KALA_CLOSE version-bumped; lifetime + Prāṇa capabilities recorded.
6. `[FORENSIC]` 7/7 holds; only `482012f1`.

## §6 — RECON dependency
- `[Q5]` confirms deepest current Vimśottarī level (expected 4 → Prāṇa is genuinely net-new).

---
*End of DRAFT U2 v0.1 (STUB). Lifetime + selective Prāṇa; the temporal frontier; heaviest lift; sequenced second.*
