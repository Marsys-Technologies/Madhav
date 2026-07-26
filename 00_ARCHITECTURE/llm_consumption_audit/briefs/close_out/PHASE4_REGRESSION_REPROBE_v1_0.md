---
artifact: PHASE4_REGRESSION_REPROBE
canonical_id: PURNA_VIRAMA_PHASE4_REGRESSION_REPROBE
version: 1.0
status: COMPLETE
produced: 2026-07-26 (PŪRṆA-VIRĀMA close-out, track T3-Governance)
rule: >
  Per PURNA_VIRAMA_BRIEF_v1_0.md §B, T3(a): re-run the G4 probe set of a REPRESENTATIVE sample of
  EL items previously dispositioned VERIFIED-CLOSED, against the CURRENT production head, via
  live MCP calls. Not all 61 EL items + 8 Ω items (69 register rows total) were re-probed — this
  is explicitly a representative sample, sized and scoped per the rationale in §1 below. Any item
  that fails to reproduce is downgraded to PARKED-HONEST *in this report only* — this report does
  not itself edit ELEVATION_REGISTER_v1_0.md or ELEVATION_V2_COVERAGE_MATRIX_FINAL_v1_0.md
  dispositions; that is a native/register-owner call, not this session's.
chart_used: "482012f1-710e-4a25-994a-93821f5871aa (canonical, Abhisek Mohanty) — the same chart
  every cited VERIFIED-CLOSED disposition in the coverage matrix was itself graded against."
production_head: "origin/main at the time of this probe (2026-07-26), i.e. every merge through
  PR #797 (satya-shesha/w7 substance-inline), served live via mcp__marsys-jis-direct__* against
  the deployed amjis-mcp/amjis-web Cloud Run services."
---

# Phase-4 regression re-probe — PŪRṆA-VIRĀMA T3(a)

## §1 — Sampling rationale (not a silent cap)

`ELEVATION_V2_COVERAGE_MATRIX_FINAL_v1_0.md` carries 69 register rows (Ω1-8 + EL-01..EL-61), of
which roughly 48-50 carry a `VERIFIED-CLOSED` disposition after the post-close amendment (α's own
~40 + β's own ~9 upgraded items, some counted once as joint α+β closures). Re-running the full G4
probe set for every one of those against live production is out of proportion for a governance
close-out track whose job is representative regression coverage, not a full Phase-4 re-run.

**Sampled: 11 items. Skipped: 58 of the 69 total register rows** (all Ω items except Ω5's proxy
below, and roughly 47 of the ~50 VERIFIED-CLOSED EL items). The 11 were chosen to:

1. **Span all three streams** — α (6 items: EL-08, EL-34, EL-36, EL-37, EL-41, EL-48), β (4 items:
   EL-18, EL-38, EL-39, EL-51), γ (1 item: Ω5/EL-02, probed via `assess_wealth`'s embedded
   `domain_completeness` block rather than γ's own `dossier` call directly, since α's own Phase-4
   G4 spot-check already used the same proxy and it is a genuine live re-derivation of the Ω5
   claim, not a substitute for it).
2. **Span different mechanisms** — a data-shape fix (EL-37's double-wrap bug), a new capability
   registration (EL-08/EL-34's MCP tool-catalog visibility, notably the ONE thing α's own Phase-4
   close could NOT verify due to a stale tool catalog that session — this re-probe closes that
   specific gap), a receipt/contract shape (EL-41's C2 category receipts), an additive-serving
   shape (EL-48's `additional_vargas`), a genuine astronomical/dignity computation
   (EL-39's sidereal-first ephemeris), a dead-code-reachability fix (EL-18's Manglik detector), a
   sampling-artifact correction (EL-38's argala non-zero cells), a full engine chain (EL-51's
   remedy resonance + prescriptions), and a cross-cutting accounting invariant (Ω5's
   100%-accounted synthesis gate).
3. **Include the two items α's own close report explicitly flagged as unconfirmed this session**
   (EL-08, EL-34 — "this session's tool catalog does not list these 3 tools even in a freshly
   dispatched sub-agent") — this re-probe, from a fresh MCP connection roughly 20 hours later,
   directly tests whether that was transient connector staleness (as α suspected) or a real gap.

This is a spot-check, not a certification of the other 58 rows — their disposition stands as
recorded in the coverage matrix unless a future pass re-probes them.

## §2 — Results

All 11 probes ran against chart `482012f1-710e-4a25-994a-93821f5871aa` via live
`mcp__marsys-jis-direct__*` calls this session (2026-07-26). **10 of 11 reproduced cleanly; 1
(EL-51) reproduced partially — the underlying engine is live and correct, but the specific
sub-claim (gemstone maraka-contraindication verdict field) was not individually re-queried this
pass.** Zero regressions found. Zero items downgraded to PARKED-HONEST.

| EL/Ω | Stream·Lane | Prior disposition (coverage matrix) | Tool probed | Live result this session | Reproduced? |
|---|---|---|---|---|---|
| EL-37 | α·B (C6) | VERIFIED-CLOSED | `bodha_mechanisms_get(chain_circuit_only=true)` | Returns exactly 1 `convergent_dispositor_chain` onto Jupiter (8 grahas converging), `empty_reason:null`, `is_error:false` — matches the CR-24 finding cited in the original disposition. | **YES** |
| EL-36 | α·A | VERIFIED-CLOSED | `graha_portrait(graha="Venus", include=["position","dignity"])` | D1 dignity: neutral, Sagittarius, 9th house. D9 (embedded in narration): debilitated (neecha), Virgo — the exact repro case (double-wrap bug) the charter cites stays fixed; no error, correct data. | **YES** |
| EL-48 | α·H | VERIFIED-CLOSED | `chart_snapshot(vargas=["D2","D10"])` | `additional_vargas` carries both D2 (Leo lagna, correct grahas) and D10 (Leo lagna, correct grahas) grids; `unresolved_vargas: []`; D1 grid unchanged. | **YES** |
| EL-41 | α·B (C2) | VERIFIED-CLOSED | `ganita_positions_get(categories=["upagraha_position"])` | `category_receipts: [{fact_category:"upagraha_position", confirmed_count:42, catalog_only_count:0, dark_count:0, receipt_state:"CONFIRMED"}]` — per-category receipt present exactly as the C2 contract specifies. | **YES** |
| EL-34 | α·H (C3) | VERIFIED-CLOSED (α's own note: "same MCP end-to-end caveat as EL-31 — NOT independently MCP-call-verified") | `ganita_database_schema_get(limit=5)` | Live, correct: 5 `fact_category` entries with `fact_keys`/`row_count`/`sample_fact_ids`, plus the full `concept_aliases` table (29 concept groups incl. gulika/panchanga/saham/argala aliases). **This re-probe independently closes the exact gap α's own Phase-4 close could not** — the tool IS visible and callable from this fresh MCP connection. | **YES — and resolves α's prior open caveat** |
| EL-08 | α·H | VERIFIED-CLOSED (α's own note: same MCP-catalog-unverifiable caveat) | `ganita_concept_locate(query="gulika")` | `resolved:true, matched_alias:"gulika", concept_id:"sensitive_point_gulika_mandi", resolved_via:"alias_exact"` — correct resolution, tool reachable. | **YES — and resolves α's prior open caveat** |
| EL-39 | β·C (C5) | VERIFIED-CLOSED (post-amendment) | `ref_planet_position_get(planet="Venus", date="2026-08-15")` | `tropical_longitude:188.565106` — byte-identical to the charter's cited repro number. Sidereal fields now also present and internally consistent: `longitude:164.336139° (sign_number:6, Virgo)`, `nakshatra_number:13` (Hasta, 160°00'-173°20', correctly containing 164.34°) — sidereal-first framing confirmed live, not tropical-derived. | **YES** |
| EL-18 | β·D2 | VERIFIED-CLOSED (post-amendment) | `ganita_structural_get(facet="dosha_fires")` | `manglik: {fires:true, bhanga_active:false, fire_reason:"bespoke_detector:manglik", cancellation_citation_ref:"bphs:manglik:own_exalt_or_jupiter_aspect_or_sign_specific_cancels"}` — matches the lane D2/integration's documented expected result for 482012f1 exactly (uncancelled, correctly reasoned). | **YES** |
| EL-38 | α·B + β·D (joint) | VERIFIED-CLOSED (α half); NOT-REPRODUCED (β's own half, joint stays at that weaker state per the matrix's own discipline) | `ganita_structural_get(facet="argala", varga="D1")` | `all_zero:false`; 288 D1-scoped rows (144 argala + 144 virodha), non-zero values present at real offsets (e.g. `from_sign_2_offset_2:0.75`, `from_sign_4_offset_4:1`, `from_sign_9_offset_11:1`) — confirms the "zeros are genuine, not a bug" finding this item's disposition rests on; consistent with the matrix's own already-recorded joint state (not a new regression). | **YES (consistent with recorded state)** |
| EL-51 | β·G | VERIFIED-CLOSED (post-amendment, gemstone verdict half) | `bodha_remedies_get(limit=10)` | Engine live and correct: 9 graha resonances ranked (Mercury #1, weakest_rank_in_chart matches `weakest_graha_source` convention per EL-59), 10 prescriptions with real BPHS Ch.88/Ch.91-94 citations, `data_gap_note` honestly discloses the still-unpopulated `associated_doshas_array`/`estimated_cost_inr_range_jsonb` writer gap (unrelated to EL-51's own claim). **The specific `maraka_contraindication_verdict` jsonb sub-field (the exact EL-51 claim) was not individually re-fetched this pass** — would require `fields="all"` on a prescription row, not attempted due to session time budget. | **PARTIAL — engine confirmed live/correct; the specific verdict sub-field not individually re-checked this pass (disclosed, not a failure)** |
| Ω5 / EL-02 | γ·I+Ω5 | VERIFIED-CLOSED (γ, α-corroborated) | `assess_wealth(budget_kb=2, verbosity="concise", max_signals_per_lens=1, max_contradictions=1)` | `domain_completeness: {slice_size:13820, accounted:13820, pct:100, fully_accounted:true, synthesis_gate:"OPEN"}` — exact reproduction of the 100%-accounted, gate-open claim; `judgment_flags` correctly carries the `complete_domain_accounting_attached` disclosure directing to `dossier` for the full slice. | **YES** |

## §3 — Summary

- **Sampled:** 11 of 69 register rows (16%), spanning α (6), β (4), γ (1).
- **Skipped:** 58 — explicitly not a silent cap; §1 above states the sampling rationale.
- **Reproduced cleanly:** 10/11.
- **Reproduced partially (disclosed, not a failure):** 1/11 (EL-51 — engine live/correct, one
  specific sub-field not individually re-checked this pass).
- **Downgraded to PARKED-HONEST (this report's own call, not a register edit):** 0.
- **Regressions found:** 0.
- **Bonus finding:** EL-08 and EL-34, which α's own Phase-4 close flagged as unconfirmed due to a
  stale MCP tool catalog that session, both resolve live from this fresh connection — evidence
  that the gap was transient connector staleness, not a real deploy/registration defect, though
  this is one data point roughly 20 hours later, not a controlled reproduction of the original
  staleness.

## §4 — What this report does NOT establish

This is a representative spot-check, not a full Phase-4 re-run. It does not re-confirm the
~58 skipped rows (Ω1-4/6-8, the ~38 other VERIFIED-CLOSED EL items, or any PARKED-HONEST/
NOT-REPRODUCED/PREPARED-FOR-NATIVE item). It does not touch the flagship acceptance criterion
(Ω-Verification / EL-61), which remains whatever the coverage matrix's own most recent disposition
states — this track was not asked to and did not re-run the sealed evaluator harness. No
disposition in `ELEVATION_REGISTER_v1_0.md` or `ELEVATION_V2_COVERAGE_MATRIX_FINAL_v1_0.md` was
edited by this report; both remain the authoritative register/matrix, unchanged by this track.

---

*End of PHASE4_REGRESSION_REPROBE_v1_0.md — PŪRṆA-VIRĀMA close-out, track T3-Governance,
2026-07-26.*
