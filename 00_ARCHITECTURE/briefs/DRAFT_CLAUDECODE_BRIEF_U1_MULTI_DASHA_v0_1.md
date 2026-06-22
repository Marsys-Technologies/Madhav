---
artifact: DRAFT_CLAUDECODE_BRIEF_U1_MULTI_DASHA_v0_1.md
canonical_id: DRAFT_CLAUDECODE_BRIEF_U1_MULTI_DASHA
brief_for: U1 — Multi-dāśā VERIFY-then-COMPLETE (NOT a heavy L1 reopen) [upstream enabler]
status: DRAFT v0.1 — STUB; the real scope is determined by reconciliation Q1/Q2/C1
version: 0.1
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D2, D16)
classification: UPSTREAM-ENABLER (L1) — sequenced FIRST (D2); feeds dāśā-consensus axis
---

# DRAFT BRIEF — U1 Multi-Dāśā (Verify-then-Complete)

> **Re-graded from v1.0's "heavy L1 reopen" to "verify-then-complete" (D16).** Code shows the
> capability is LARGELY BUILT; the real work is determined by what's actually in prod. This stub holds
> the known facts + the decision tree; the executable scope is filled after reconciliation Q1.

## §0 — What is CODE-VERIFIED (D16)
- `ga_writers/ga_dashas_writer.py` defines `SYSTEMS = [vimshottari, yogini, ashtottari, chara_karaka,
  naisargika, mudda, kalachakra]` (7 systems) with real `compute_*_system` functions for each
  (`compute_yogini_system` line 969, `compute_kalachakra_system` line 1820, etc.).
- `build_ga_dashas` runs "7 systems × 5 ayanāṃśas"; the orchestrator writer
  (`pipeline/orchestrator/writers/ga_dashas.py`) plans 35 substeps (`SYSTEMS × AYANAMSHAS`) + a
  concurrency post-pass.
- `chart_dashas` schema has `system_id TEXT NOT NULL` as a first-class column; the unique key +
  indexes are system-scoped.
- `ka_dasha_kala` (L3 service) already queries all 7 systems (`tree_walk.py` ALL_DASHA_SYSTEMS).

## §1 — The CONFLICT (why reconciliation is needed)
- The L1 seal attributes **536,471 rows to Vimśottarī**.
- A sibling file `l1_dashas.py` comments **"MD ONLY"** for non-Vimśottarī systems (volume floor 6,500
  = Vimśottarī Sūkṣma only).
- **So one of three is true, and only prod can say which:**
  - (a) all 7 systems × 4 levels are prod-populated → **U1 dissolves to pure wiring** (consume in L4 +
    M9); OR
  - (b) the 7-system writer exists but only Vimśottarī was RUN to prod → **U1 = a build-run of the
    other 6** (no new code; trigger the existing writer); OR
  - (c) non-Vim systems compute MD-level only → **U1 = deepen the 6 systems to level 4** (real but
    bounded code work in the existing writer).

## §2 — The decision tree (filled by reconciliation Q1/Q2/C1)
```
RECON Q1 (system × level row counts in prod chart_dashas):
  ├─ all 7 systems at levels 1–4  → U1 = WIRE ONLY (consume dasha_consensus in ph_nimitta + M9)
  ├─ only vimshottari present      → U1 = BUILD-RUN the other 6 via the existing orchestrator path
  └─ non-vim at level 1 only       → U1 = DEEPEN to level 4 (extend the per-system depth loop), then build-run
```

## §3 — What U1 delivers (regardless of branch)
- All applicable dāśā systems prod-populated for the native in `chart_dashas` (the genuine gap filled).
- `ka_dasha_kala` returning real cross-system agreement (the I-7 `cross_dasha_agreement` weight, 0.18,
  currently thin, becomes substantive).
- A `dasha_consensus_count` consumable by `ph_nimitta` Axis 6.

## §4 — Standards (if any code/build is needed)
- Frozen orchestrator contract (the `ga_dashas` writer is already conformant — do not change it).
- This REOPENS the L1 seal → requires a version bump + re-seal of `L1_GANITA_CLOSURE` (D2).
- Sequenced FIRST (D2), before U2 and before the L4 revision.
- PROD-VERIFY against prod, not worktree. FORENSIC 7/7. Only `482012f1` (+ Abhinandan if Phase E).

## §5 — Acceptance criteria (provisional — finalized post-reconciliation)
1. `[psql_prod]` all applicable dāśā systems present in chart_dashas for the native at the intended depth.
2. `[pytest]` each non-Vim `compute_*_system` produces valid period rows (lord, dates, levels) — not stubs/MD-only (if depth work needed).
3. `[service]` `ka_dasha_kala` returns >1 system's agreement for a sample window (consensus is real).
4. `[re-seal]` L1_GANITA_CLOSURE version-bumped; the multi-dāśā row counts recorded.
5. `[FORENSIC]` Vimśottarī birth-anchor assertion still passes (the 7/7 unaffected).

## §6 — RECON dependencies
Everything in §2. **Do not execute U1 until Q1/Q2/C1 are answered** — the branch determines whether
this is a 1-session wire, a build-run, or a bounded depth-extension.

---
*End of DRAFT U1 v0.1 (STUB). Verify-then-complete; scope set by reconciliation Q1.*
