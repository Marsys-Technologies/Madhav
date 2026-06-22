---
artifact: CLAUDECODE_BRIEF_U1_MULTI_DASHA_CONSENSUS_v1_0.md
canonical_id: CLAUDECODE_BRIEF_U1_MULTI_DASHA_CONSENSUS
brief_for: U1 — Multi-Dāśā Consensus SURFACING (wire-only; the dāśā agreement that already exists, made first-class)
status: FINALIZED — built on prod-verified state (GATE A); ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D20a wire-only, D26 single-wave, D27 no-L1-reseal)
classification: UPSTREAM-ENABLER (wire-only) — sequenced FIRST in the wave; consumed by ph_nimitta Axis 6 + the U4 School-Consensus Yoginī engine
swarm_coordination:
  wave: W1 (first; trivial; unblocks the consensus axis)
  blocked_by: []
  blocks: [m9_activation, ph_nimitta]
  may_touch:
    - platform/python-sidecar/services/ph_nimitta/**            # consumption only (the writer reads consensus via the service)
  parallel_safe_with: [u2_temporal_enrichment]   # disjoint
  hard_internal_gate: none
  zero_new_storage: true   # R1 RESOLVED — leverage existing L1 concurrency + the service; add NO column anywhere
---

# CLAUDECODE BRIEF — U1 Multi-Dāśā Consensus (Wire-Only)

> **GATE-A VERIFIED (D20a):** all 7 dāśā systems are ALREADY built to level 4 in prod
> (`chart_dashas`: vimshottari 51,037 · yogini 83,740 · ashtottari 32,960 · chara_karaka 138,535 ·
> kalachakra 106,049 · mudda 102,205 · naisargika 21,945 = 536,471). The L1 seal's "536k Vimśottarī"
> was the all-systems total, mislabeled. **U1 writes ZERO new dāśā data and reopens NO sealed layer.**
> It SURFACES the cross-system agreement that `ka_dasha_kala` already computes but that is currently
> buried as a 0.18-weighted scoring input — making `dasha_consensus_count` a first-class predictive
> signal. This is the cheapest supreme-uplift in the whole program.

## §0 — What this enabler IS
The most reliable classical timing technique is **dāśā consensus** — when multiple independent dāśā
systems activate the same theme at the same time, the timing is categorically more trustworthy than a
single-system reading. The instrument already computes this (7 systems, cross-system agreement per
window) but only *consumes* it as one weighted term inside the I-16 convergence score. U1 surfaces it
as an explicit, queryable, per-prediction count an acharya could never compute across 7 full systems.

## §1 — Strategic role
- **It makes timing supreme, not just structure.** ph_nimitta's other axes (graph, discovery,
  embedding) sharpen the WHAT and WHY; dāśā consensus sharpens the WHEN — the hardest, most-valued
  thing in predictive Jyotish.
- **It is already paid for.** The 536,471 rows + the agreement computation exist. U1 is pure wiring.
- **It feeds U4.** The Yoginī school engine (U4 Task A de-hardcode) reads the `yogini` dāśā rows that
  this confirms are present (83,740 rows) — so U1 unblocks part of U4 too.

## §2 — VERIFIED ground truth (code + prod, 2026-06-21)
The service contract (`platform/python-sidecar/services/ka_dasha_kala/service.py`) — USE THESE EXACT NAMES:
- `class KaDashaKalaService` with `.query(chart_id, ayanamsha_id, target_lords, related_lords,
  date_start, date_end, max_level=4, systems=...) -> KaDashaKalaResult`.
- `KaDashaKalaResult` fields: `windows: list[EligibleWindow]`, `kp_windows: list[EligibleWindow]`,
  `systems_queried`, `total_windows`, **`high_agreement_count: int`** (windows where
  `cross_dasha_agreement.count >= 2`).
- `EligibleWindow.cross_dasha_agreement: CrossDashaAgreement` with **`.count: int`** and
  **`.systems_agreeing: list[str]`**.
- The 7 systems (verified prod-populated): `vimshottari, yogini, ashtottari, chara_karaka,
  naisargika, mudda, kalachakra`. (Nārāyaṇa absent; KP is a Vimśottarī sublevel.)
- `ka_sangam` ALREADY calls `KaDashaKalaService` as the Mode-A prior (CF.L3.6, `engine.py` ~line 285);
  `cross_dasha_agreement` is an I-7 weight (0.18) in the I-16 formula. The data flows; it is just not
  surfaced as an output field.

## §3 — The work (consumption wiring — the primary path)
**U1 is consumed, not built.** The deliverable is the consumption contract that `ph_nimitta` Axis 6
and the U4 School-Consensus Yoginī engine use:

**3.1 — `dasha_consensus_count` derivation (the canonical definition).** For a prediction window
`[window_start, window_end]` in domain D:
- Call `KaDashaKalaService.query(chart_id, ayanamsha_id, target_lords=<the domain's significator
  lords>, date_start=window_start, date_end=window_end, max_level=4, systems=ALL_7)`.
- `dasha_consensus_count` = the number of DISTINCT dāśā systems whose eligible window overlaps
  `[window_start, window_end]` for the domain's significators = `max over the window of
  cross_dasha_agreement.count` (equivalently, `len(set of systems_agreeing across overlapping
  windows))`).
- `dasha_consensus_systems` = the `systems_agreeing` list (which systems concur) — stored for transparency.
- Range: 1–7. **Define the canonical mapping precisely in the engine** (document it); 1 = single-system
  (weakest), ≥4 = strong multi-system consensus.

**3.2 — How ph_nimitta Axis 6 uses it.** `dasha_consensus_count` becomes a stored column on
`phala_anchors` (see ph_nimitta brief §2) AND a confidence modulator: higher consensus → higher
confidence (within the G-LADDER ceiling, D21). The exact modulation is specified in the ph_nimitta
brief; U1 only guarantees the count is correctly derived and available.

**3.3 — How U4 uses it.** The Yoginī school engine (U4 Task A) reads the `yogini` system rows from
`chart_dashas` (83,740 rows confirmed) for its `getCurrentYogini()` logic — U1 confirms the data is
present and the service path works.

## §4 — Zero-new-storage (R1 RESOLVED — leverage the EXISTING architecture)
> **Native steer (2026-06-21):** "there is already a convergence system built into the architecture …
> leverage the entire existing architecture if it makes sense." It does. **U1 adds NO new column anywhere.**

Code-verification found the concurrency is ALREADY computed and stored at L1:
- **`chart_dashas.concurrent_system_lords_jsonb`** (migration 211, "Cross-system concurrency"; populated
  by the `ga_dashas` concurrency post-pass — the orchestrator's final ga_dashas sub-step). This is the
  raw "which systems' lords concur at this period" fact, already in prod for the native.
- **`ka_dasha_kala` service** reads that + derives `cross_dasha_agreement.count` + `systems_agreeing`
  per eligible window at query time.
- **`kala_convergence`** already stores `independent_current_count` (the I-22 independence discount) —
  a related but distinct rigor field.

Therefore the canonical, zero-duplication chain is:
```
chart_dashas.concurrent_system_lords_jsonb   (L1, already stored)
        │
        ▼
ka_dasha_kala.query() → EligibleWindow.cross_dasha_agreement.{count, systems_agreeing}   (service, already computed)
        │
        ▼
ph_nimitta Axis 6 reads it at build time → dasha_consensus_count on phala_anchors   (the ONLY new write, in L4's own table)
```
**No column is added to `kala_convergence` or `chart_dashas`.** The consensus already exists; U1 routes
it to the L4 prediction. (Note: `bodha_convergence` at L2 is a DIFFERENT convergence — cross-tradition
signal aggregation, not cross-dāśā — and is not conflated here.)

## §5 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` `dasha_consensus_count` for a known multi-system window returns the correct distinct-system
   count (assert against a hand-checked window where ≥2 systems are known to concur).
2. `[pytest]` `dasha_consensus_systems` lists the actual concurring systems (subset of the 7).
3. `[pytest]` the derivation calls the EXISTING `KaDashaKalaService` (no reimplementation of dāśā
   tree-walk — grep the consumer for any chart_dashas tree-walk → must be ZERO; it must go through the service).
4. `[pytest]` single-system windows yield count = 1 (not 0); the floor is 1 when any system is eligible.
5. `[verify: prod]` all 7 systems return rows from `ka_dasha_kala` for the native (sanity: the 536,471
   rows are reachable through the service, not just in the table).
6. `[anti-drift]` U1 writes NO new dāśā data and ADDS NO column to `chart_dashas`/`kala_convergence`
   (§4 zero-new-storage); the only write is `dasha_consensus_count` on `phala_anchors` (L4's own table).
7. `[reuse]` the consensus is sourced from the EXISTING `concurrent_system_lords_jsonb` → service chain
   (§4); grep the consumer → it reads via `KaDashaKalaService`, never re-derives concurrency.

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/u1-dasha-consensus
# verify the 7 systems in prod (through the service path)
python -c "from services.ka_dasha_kala.service import KaDashaKalaService"   # import sanity
# the existing consumer pattern to mirror
sed -n '250,310p' platform/python-sidecar/services/ka_sangam/engine.py
cd platform/python-sidecar && pytest -q services/ka_dasha_kala -k "agreement or consensus or cross"
```

## §7 — Definition of done
- [ ] `dasha_consensus_count` + `dasha_consensus_systems` derivation defined + tested against the live service.
- [ ] Consumption contract documented for ph_nimitta Axis 6 + U4 School-Consensus Yoginī engine.
- [ ] No dāśā recomputation (service-only); no new dāśā data; NO new column on chart_dashas/kala_convergence; no L1 re-seal.
- [ ] Sourced from existing `concurrent_system_lords_jsonb` → `KaDashaKalaService` chain (zero-duplication).

## §8 — VALUE ADDED BY THIS BRIEF
1. **Turns an already-paid-for capability into a first-class predictive signal** — 536,471 rows of
   7-system dāśā data were computed and then used only as a 0.18 scoring weight; U1 surfaces the
   consensus an acharya cannot compute across 7 full systems.
2. **Sharpens the WHEN** — the hardest, most-valued axis of prediction — at near-zero cost.
3. **Reuses the service, zero duplication** — strictly through `KaDashaKalaService` (D10 reuse rule).
4. **Unblocks U4's Yoginī engine** by confirming the `yogini` system data path.
5. **Optional L3 surfacing** makes consensus a durable, queryable fact, aligning L3/L4 and the cockpit.

## §9 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — native steer]:** ZERO new storage. Leverage the existing
  `chart_dashas.concurrent_system_lords_jsonb` (L1, mig 211) → `KaDashaKalaService` → ph_nimitta chain.
  No column added to `kala_convergence` or `chart_dashas`. (See §4.)
- **R2 [RESOLVED — Cowork default locked]:** the per-domain `target_lords` use the SHARED CDLM
  domain→significator-lord mapping (the same vocabulary ph_nimitta Axis 1 uses for domain assignment) —
  not redefined here. The mapping is a single shared reference.
- **R3 [RESOLVED — Cowork default locked]:** `dasha_consensus_count` = the count of DISTINCT dāśā
  systems whose eligible window (via the service) overlaps the prediction window for the domain's
  significators. `dasha_consensus_systems` = that set of systems. Floor 1, ceiling 7.

---
*End of CLAUDECODE_BRIEF_U1_MULTI_DASHA_CONSENSUS v1.0 — CLOSED. Wire-only, ZERO new storage; the
cheapest supreme-uplift. Built to maximal value: the existing-architecture concurrency chain + the
exact service contract + the locked consensus definition. R1–R3 resolved.*
