• I'll perform this read-only review. First, let me verify hashes and survey the packet files.

• Now let me verify the arithmetic myself: horizon day-count, oracle count, and the longitude/sign/house computations.

• All verification is done. Everything below is the complete review — printed only, nothing written.

  ---

  ```yaml
  ---
  artifact: KIMI_K3_REVIEW_DESIGN_SPECS
  version: "1.0"
  status: COMPLETED_INDEPENDENT_READ_ONLY_REVIEW
  reviewer: "Kimi K3 (effort=max) — independent review"
  date: 2026-09-29
  verdict_specs: FREEZE_WITH_AMENDMENTS
  verdict_protocol: SOUND_WITH_ONE_CORRECTION (v1.2 T-rank validity floor rests on a miscounted denominator — 26 timing-usable events, not 23; correct the floor to 14 or justify 12 on other grounds)
  reviewed_document_sha256:
    design/GOCHARA_DESIGN_SPECS_v1_0.md: c87919dbe06fc6828ee719805143a319898b6ebd4c0ae502d67deb14a5debea0
    sealed/FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0.md: 5bd6c51e8901399ef05090f4b3e9933f69735773effff945cfce78e45e182392
    design/GOCHARA_PLAN_V3_AMENDMENT_v1_0.md: bb5bc981419ff9b33de4490b90a1849da52c3e60d78975b4b50f5b4fd804f9d9
    design/L3_FAMILY_COORDINATION_v1_0.md: 2476f2ccb7fcd6ebbaa4e472ffe8e17726d3fb0a62dc8e603fe2931d6dd926aa
    NATIVE_DECISION_PACKET_v1_0.md: 89263ffdc09974bf7b8bf22bc5ebd17a7c2043d5a12eb17cb1493f359e4f0b0c
    sealed/FABLE_REVIEW_EVIDENCE_APPENDIX_v1_0.md: 05ce2f0d9ecdc4b7a3f166c1bdb9a364760f8bc09ed0407f667f91fcc204ff20
    recomputed_with: "shasum -a 256 on campaign/pravaha @ 6a7fff0f36d9d7718c7954adaf51134db53310fd — all six match the packet's stated hashes"
  authority: "Review only; authorizes nothing."
  ---
  ```

  # KIMI K3 REVIEW — Gochara design specs v1.0 + measurement surface (B3.5)

  ## 1. Verdict line

  **Specs: FREEZE_WITH_AMENDMENTS.** The specs are a faithful, well-disciplined operationalisation of the sealed v3.0 — every `[P]` element carries its ruling ref, every `[U]` is fenced out of scores, the frame/count discipline is real, and I could not find doctrine smuggled in. But they cannot freeze as-is: the machine-readable oracle set is missing 14 of the oracles the spec's own §11.2 index names, and the single most consequential Tier-0 repair — aspect direction (#13, T0-1) — has neither an invariant nor an oracle anywhere in the reviewed document.

  **Protocol (separate verdict, §5): SOUND_WITH_ONE_CORRECTION.** v1.2's four steward items are each answered with a defensible construction; the T-rank validity floor is derived from a miscounted denominator (23 stated; 26 by the v1.0 partition table — my count, shown below). Correct the floor to 14 or justify 12 on non-majority grounds before v1.2 takes force. The B4.3 deviation remediation is adequate; no re-run.

  ---

  ## 2. Conformance table — sealed element → specs

  | Sealed v3.0 element | Verdict | Where in specs |
  |---|---|---|
  | §2.2 union-of-source-qualified-paths admissibility; pruning only on demonstrably-false necessary predicates; unknown ≠ false; uncomputed ≠ empty | **CARRIED** | §0 (admission rule), §2 invariant 2, §2.2 inv 3; oracle O-RP-1 exists in spec text §2.3 but is **missing from the JSON** (Finding F1) |
  | §2.3 relationship record (frame, agent→relation→object, role, prerequisites, three valence fields, source+qualification) | **CARRIED** | §1.1 schema field-for-field; invariants 1–7 map the #10 frame errors, alias/role-edge rule, negative-result exclusion (E3) |
  | §2.4 P1–P6 catalogue with source statuses | **CARRIED, statuses exact** | §2.1: P1 `[D]` PG249–250 + node-dispositor `[P]` testimony (D-PADMIT); P2 `[D]` PG321–323/335 with adverse-residence scoped to adverse classes (D-RQ5 shape); P3 `[D]` + māraka `[P]` testimony; P4 `[P]` uncited_extension under **D-P4** with PG216 precedent, seed definition and father-example claim withdrawn; P5 `[D]` after polarity normalisation, known-zero adverse vs unresolved unqualified (D-RQ1), no universal multiplier; P6 `[P]` on-demand only (M-3) |
  | Three-field valence + class-relative polarity (#11/#12) | **CARRIED** | §3; invariant 3 names the E5 1,435-all-favourable regression as the field's raison d'être |
  | Tier-0 repairs #1–#27, N1–N9 each guarded | **PARTIAL — see F1/F2/F3** | Most guarded (table §11.2 + JSON), but **#13 (aspect direction) unguarded anywhere**, #24 (plateau) guarded only indirectly by the measurement protocol not by an oracle, #5 (tārā key) / #19 (kakṣyā key, T0-10) / #18 / #20 / #21 / #23 / #26 have no oracle; the JSON omits 14 spec-named oracles |
  | §6 implementation contract (substrate, pruning, lazy refinement, interval sweep, day-on-demand, re-solve vs re-score, cost-as-contract) | **CARRIED** | §6 (substrate, contract counts, Moon on demand), §7 (certified bounds, interior-extremum rule, angular M-1 per D-RQ2), §10 (pruning, re-solve/re-score split, coverage-on-no-window, benchmarks as contract) |
  | §7 rulings as ruled (D-RQ1…8) | **CARRIED** | D-RQ1→§8; D-RQ2→§7.2.3 + O-SM-1; D-RQ3→B3.3 done (CORPUS_READS §5) — spec should absorb the result (F4); D-RQ4→O-CF-N7; D-RQ5→§2 P2/O-RP-5; D-RQ6→O-CF-N5; D-RQ7→§4/O-RP-4; D-RQ8→§5 battle-scale `uncited_extension` stamp + P4 citation form |
  | §8 corpus register constraint (nothing `[U]` enters a score) | **CARRIED, with one staleness** | §0 admission; §9.2 inv 3 — but §9's "activation `[U]` until B3.3" is now stale: CORPUS_READS §4 settled it `[D]` (F4) |

  Nothing in the specs asserts doctrine beyond the sealed text or its rulings. No `[P]` element appears without a ruling ref. "Uncomputed" is fenced from "empty" at §1.1 (`coverage_ref … always resolvable`), §2.2 inv 2, §5.2 inv 4, §10.2 inv 3 — this is thorough.

  ---

  ## 3. Findings

  **F1 — BLOCKING · the oracle JSON does not contain 14 oracles the spec's own §11.2 index names.**
  Evidence [S]: spec §2.3/§3.3/§4.3/§5.3/§6.3/§7.3/§8.3/§9.3/§10.3 name O-RP-1, O-TV-2, O-TV-3, O-PP-3, O-VI-2, O-VI-4, O-SS-4, O-SM-2, O-SM-3, O-BP-3, O-AO-2, O-AO-3, O-RW-2, O-RW-3; `GOCHARA_TEST_ORACLES_v1_0.json` (my parse: **25 oracles**, not the packet's "22") contains none of them. Among the missing: O-RP-1 (the union-not-cascade oracle — the *central* doctrinal correction of v3.0), O-VI-2/O-VI-4 (the N4 temporal-structure repairs), O-SM-2/O-SM-3 (lazy-refinement conformance), O-SS-4 (Moon-on-demand), O-RW-2/O-RW-3 (coverage-object and manifest-provenance serving contract).
  Requested change: complete the JSON to match §11.2 before freeze, or amend §11.2 to a deliberately-reduced set with the reduction justified per-oracle. As written, freezing would freeze a promise the data file does not keep.

  **F2 — BLOCKING · finding #13 (aspect direction, T0-1) has no invariant and no oracle.**
  Evidence [S]: v3.0 §1 #13 (Mars 4/8 and Saturn 3/10 mirrored — both prior reviewers confirmed with independent arithmetic) and T0-1 is the first Tier-0 item; B3.1 §4 gates Saṅgam's S-2 consumption on the fixed kernel; L3_FAMILY_COORDINATION §2 repeats the gate. The specs mention the fix only obliquely (§10.2 inv 4 "post-T0-1 kernel (aspect direction fixed)"). No oracle computes one directed case (e.g., Mars in Aries must produce aspect contacts on Cancer and Scorpio — counted forward 4th/8th — and *not* on Capricorn/Virgo). O-CF-DRISHTI guards graduation (#15), not direction. The miscounted-house lesson is campaign law precisely here.
  Requested change: add an aspect-direction oracle per special-aspect graha with the count written out, before freeze. This is the highest-value single missing guard.

  **F3 — SHOULD-FIX · unguarded confirmed defects: #24 (plateau), #5 (tārā key), #19 (kakṣyā key); lesser: #18, #20, #21, #23, #26.**
  Evidence [S]: §11.2's own index lists no guard for these; the JSON confirms. #24 (E5's 27-of-41 plateau) is partially covered by protocol v1.1 §B.3 (peak-diversity degeneracy test) at the generation level — say so in the index rather than leaving it implicit; a spec-level oracle (era/month/day rows must trace to a path operating at that grain, §2.2 inv 4) is cheap. #5 (tārā never fires — case mismatch) and #19 (L1 kakṣyā key mismatch, T0-10) have trivial oracle shapes (a tārā term present with correct key on a P6 evaluation; a kakṣyā lookup resolving through the declared donor key per CORPUS_READS §8).
  Requested change: add oracles for #24/#5/#19 (ranked in that order); record #18/#20/#21/#23/#26 as guarded-by-construction (schema/invariant) with the reason stated, or guard them.

  **F4 — SHOULD-FIX · §9 (and P2's silence on node results) is stale against the packet's own B3.3 output.**
  Evidence [S]: spec §9.2 inv 3 holds saham activation `[U]` "until B3.3's read lands"; CORPUS_READS §4 landed it `[D]` — three modes (sahameśa-ki-daśā PG95:C1 "sarvāmmata"; varṣeśa contact PG147/PG160; munthā/muntheśa contact PG132/PG160), with the Mudda-labelling `[U]` honestly retained. Similarly D-RQ3's recount is complete (CORPUS_READS §5: XXVI.1–2 "Rāhu and Ketu are similar to the Sun", XXVI.24 Moon-relative Rāhu list — N-14 untouched). A frozen spec should not fence as `[U]` what its own companion read settled `[D]`, nor stay silent on a recount the native ordered.
  Requested change: amend §9 to admit activation per CORPUS_READS §4 (three modes, Mudda labelling noted); add one line to P2 recording the node Moon-relative results as `[D]` with N-14 restated.

  **F5 — NOTE · minor numeric slips that change no conclusion.**
  (a) Protocol v1.2 §2: horizon 1998-01-01→2026-12-31 is **10,592** days inclusive (29×365 + 7 leap days; recomputed), not 10,587; the 6.8 % figure is unchanged at the quoted precision (0.0680 either way). (b) The packet's "22 machine-readable oracles" vs the JSON's actual 25 (F1). (c) v3.0 §6.1's "≈ 4×10⁵ Moon boundary events per 250 y" — I initially doubted this; recomputed properly it holds: (12+27+96) crossings × 13.37 lunar circuits/yr ≈ 1,800/yr ⇒ ≈ 4.5×10⁵ per 250 y. Verified `[J]`-free.

  **F6 — NOTE · schema ambiguities an implementer would have to guess at (minor).**
  (a) §1.1 `relation` enum mixes transit relations (`residence|aspect|conjunction`) with natal-fact relations (`ownership|occupancy|period_running`) without saying which apply to contacts vs records — harmless but will be asked. (b) `evidence_for_occurrence real` and `severity real` carry no scale or unit; the protocol needs only ranks, so this is tolerable, but a one-line "interpretive, scale set at calibration (L5)" would preempt the question. (c) `object_role` vs `relation` overlap (`dispositorship` relation + `dispositor` role) — state which is authoritative.

  **F7 — NOTE · O-PP-2's "variance > 0 over monthly samples" is weakly failable.** A permission that flips once in a decade passes; that is still infinitely better than the E6 constant, and the relationship requirement (§4.2 inv 2) is the real guard — acceptable, but record that the oracle tests non-constancy, not correctness; correctness rides on O-PP-1.

  ---

  ## 4. Ranked amendments (must land before freeze, in order)

  1. **Add an aspect-direction oracle set (F2).** Per-graha directed cases with the count written out (Mars forward-4/8, Saturn forward-3/10, Jupiter 5/9, all full; 7th universal), regression = the shipped `target + angle` mirror. Evidence: v3.0 #13; B3.1 §4 S-2 precondition; the entire Saṅgam directed-event stream hangs on it.
  2. **Complete the oracle JSON to §11.2's index, or amend the index (F1).** Priority order among the missing 14: O-RP-1 (union admissibility), O-VI-2/O-VI-4 (N4), O-SM-2/O-SM-3 (certified bounds), O-RW-2/O-RW-3 (serving contract), then the rest.
  3. **Add oracles for #24, #5, #19 (F3)** and record the guard-by-construction disposition of #18/#20/#21/#23/#26 in §11.2.
  4. **Absorb CORPUS_READS into §9 and P2 (F4)** — activation `[D]` per the three modes; node Moon-relative results `[D]` with N-14 restated.
  5. **Protocol v1.2: correct the T-rank floor denominator (Q-M2 below)** — this is a freeze-relevant correction to the measurement surface, not the specs file; it must land before v1.2 takes force, not necessarily before D-SPECS.
  6. Cosmetic (can ride with any of the above): 10,592-day figure, "22 oracles" → actual count, §1.1 enum clarifications (F5, F6).

  None of amendments 1–4 changes a ruling or adds doctrine; all are conformance completions of what the specs already promise.

  ---

  ## 5. Measurement surface — the explicit questions

  **Q-M1 (deviation): remediation is adequate; do not re-run.**
  The protocol was *fully* pre-declared before any scoring (v1.0 §5.5's amendment path exists precisely for this), the pass was read-only and deterministic with every predicate printed, and both amendments disclose exactly what was seen (v1.1 header; v1.2 header) and were written *before any candidate generation was scored or inspected* — the point in the pipeline where threshold-fitting risk actually lives. '3.0' is the served floor, not a competitor; sharpening the endpoint set against a degenerate baseline before candidates exist is legitimate amendment, not post-hoc fitting. The freeze condition that matters is the one already stated: nothing further scored until this review closes. `[J]` Re-running '3.0' would be ceremony; the figures stand as a measurement under a disclosed-unreviewed protocol, and the review is now happening.

  **Q-M2 (T-rank): the construction is sound; the floor is miscounted.**
  Median percentile ≤ 25 over N ≥ 3 candidate windows, degeneracy classes contributing no N, and "rank-unproven blocks the flip" is exactly the right shape — it targets E5's plateau defect (the thing the elevation exists to cure) and makes "cannot tell" a failing answer, which is the honest reading of ADK-0026. **But the derivation says "23 timing-usable held-out events" and that count is wrong.** From the v1.0 partition table's own timing-usable column: relationship_begin 3 + relationship_end 1 + separation 1 + career_join 2 + career_exit 1 + career_switch 1 + education_admission 1 + education_completion 3 + business_launch 4 + relocation_out 1 + relocation_return 1 + travel 1 + health_event 2 + bereavement 1 + financial_gain 1 + financial_deception 1 + recognition 1 = **26** (consistent with BASELINE_3_0: 36 held-out − 10 year-grain = 26). The bare majority of 26 is **14**, not 12. If 23 was derived some other way (e.g., excluding classes with no engine counterpart), the derivation must be printed; as written it is an arithmetic error. Requested change: floor = 14 with the 26-event count shown, or justify 12 on stated non-majority grounds. Everything else about the rule stands.

  **Q-M3 (T-FP): fair as an order-of-magnitude anchor; two disclosures to record.**
  The arithmetic checks: 8 adverse events × 90 d / 10,587 d = 6.80 % (10,592 d by my count — same to quoted precision), bar at 3× = 20.4 % ⇒ ≤ 20 % `[verified]`. The construction is honest — it derives the bar from the chart's own event density rather than from '3.0''s degenerate 99.87 %, which is the right instinct. Two caveats `[J]`: (a) the 90-day ideal window is a judgment; a 60- or 120-day choice moves the ideal to 4.5–9.1 % but the bar only to 13.6–27.2 %, so ≤ 20 % is robust to the choice; (b) applied **per class**, a single-event adverse class (bereavement) has an ideal density of 90/10,592 ≈ 0.85 %, so 20 % is ~23× its own ideal — the bar is really an aggregate-density test applied per class. An alternative I'd accept but do not require: per-class bar = max(3 × per-class ideal, 2 %). Recording these two disclosures in the protocol text would make the derivation fully challengeable; the bar itself is defensible as-is.

  **Q-M4 (T-time): the right shape; 182 d is fine.**
  The single capped-miss median subsumes v1.1's two-clause rule cleanly: '3.0''s five misses at 182 d give median 182 > 45, failing as it should; two misses can pass only if the four best hits are within 45 d — a reasonable tolerance `[J, verified by construction]`. The 7 exact-date events match BASELINE_3_0 §2 exactly (1998-02-16, 2007-06-10, 2008-06-09, 2024-02-16, 2026-03-20, 2026-04-08, 2026-04-17). The cap's exact value barely matters — anything > 45 d produces identical pass/fail behavior whenever a miss lands beyond the bar; 182 d (half-year, the era-grain scale) is a defensible, memorable choice and prevents an ∞ from ever entering a median. Sound.

  **Q-M5 (oracles): no — not every load-bearing defect is guarded; the present oracles are failable and their arithmetic checks.**
  *Failability (§N.8):* all 25 present oracles can fail — each has a concrete then-clause with operands and tolerance (O-VI-1 "exactly 1.0"; O-SS-1 "±0 events"; O-PP-2 variance test; O-CF-N6 "zero rows"; O-RW-1 digest comparison). None is tautological.
  *Arithmetic (recomputed independently):* Moon 327.06° → floor/30 = 10 = Aquarius; Jupiter 306.87° → Aquarius ⇒ **1st** from the Moon ✓ (O-RR-1); 7th/8th/2nd from the 9th = Gemini/Cancer/Capricorn ✓ (O-RR-2); natal Saturn 202.43° → Libra = 7th ✓ (O-RR-3); Jupiter 220.31° → Scorpio, aspects Pisces/Taurus/Cancer — Sagittarius absent ✓ (O-RP-2); Saturn 288.01° vs natal Sun 291.96°: Δ = 3.95° = 3°57′ ✓ (O-RP-3); Rāhu 49.03° Taurus = 8th from lagna-lord Mars 198.52° Libra ✓ (O-RP-4); Saturn Capricorn = 12th from the Aquarius Moon ✓ (O-RP-5); Saturn 253.43° vs natal Jupiter 249.79°: Δ = 3.64° = 3°38′24″ ≈ 3°39′ ✓ (O-TV-1); spec §11.3's marriage figures (1°49′, 2°08′, 0°19′, 0°33′) all recompute within rounding ✓; Sun 12/27/96 crossings ✓ (96 = 8 kakṣyās × 12 signs); Saturn ≈ 0.4/1.1/3.2 consistent with a 29.46-yr period plus retrograde re-crossings ✓.
  *Unguarded load-bearing defects:* **#13 (aspect direction) — none (F2, blocking)**; #24 (plateau) — only indirectly via protocol §B.3; #5 (tārā key), #19 (kakṣyā key) — none (F3); #18/#20/#21/#23/#26 — unguarded, lower priority. And 14 spec-named oracles are absent from the JSON entirely (F1, blocking).

  ---

  ## 6. Disclosure — what I could not verify

  - **Production figures (E1–E9) and the baseline's SQL outputs.** Taken on the appendix's and BASELINE_3_0's authority per the ground rules; I verified internal consistency (E1's 253/369/29 × 3 target types arithmetic, E5's plateau ratios, baseline §2 vs §3 vs §4 cross-references, T-cover 22/36) and found none broken, but I ran no query. Would settle: read-only production access — not requested.
  - **Source file:line citations against the lane branch** (`step06b_windows_projection.py:209-228`, `episodes.py:443-508`, `legacy_semantics.py:724-772`, etc.). The lane branch `l3/gochara-autonomous-wp0-7` is not checked out here; N1–N9's locations were taken as stated (they were verified at source by both prior reviewers and re-confirmed in v3.0 §1.2). Would settle: a worktree at that ref.
  - **The 23-vs-26 timing-usable count (Q-M2).** I counted from the protocol v1.0 partition table itself; if a different rule produced 23, the rule isn't printed. Would settle: the authors state the derivation or adopt 26/14.
  - **The LEL's 57-event inventory and event IDs.** I verified the protocol's class table against BASELINE_3_0's SQL `values` list (36 held-out, consistent), not against the LEL file itself, which was outside the packet's required reading.

  *End of review. Stored unedited; every finding is stated so it can be accepted, amended, refuted with evidence, or deferred at B3.6.*

