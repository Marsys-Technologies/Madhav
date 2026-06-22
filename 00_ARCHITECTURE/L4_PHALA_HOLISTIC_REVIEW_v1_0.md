---
artifact: L4_PHALA_HOLISTIC_REVIEW_v1_0.md
canonical_id: L4_PHALA_HOLISTIC_REVIEW
version: 1.0
status: CURRENT — the cross-brief closing review of all 12 L4 briefs before GATE D/E
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The holistic closing review (the L3-playbook step) over the 12 finalized L4 briefs — 4 upstream
  enablers (U1–U4) + 8 ph_* assets. Checks what per-brief work cannot: wave/dependency-order
  correctness, migration numbering, cross-asset reference integrity, elevation coherence, the L4/L5
  boundary, deterministic-first + anti-drift consistency, and missed cross-links. Findings + fixes
  feed GATE D/E (registry/wiring + the campaign plan/queue/kickoff).
reviewed_briefs:
  - U1_MULTI_DASHA_CONSENSUS · U2_LIFETIME_PRANA · U3_CONVERGENCE_CURRENTS_ENRICHMENT · U4_SCHOOL_CONSENSUS_ACTIVATION
  - L4_PH_NIMITTA · L4_PH_MUHURTA · L4_PH_PRATIKARA · L4_PH_SODHANA · L4_PH_SUDDHA_SODHANA · L4_PH_SANKRAMA · L4_PH_PRAMANA · L4_PH_PHALADESA
---

# L4 Phala — Holistic Closing Review v1.0

## §1 — What's CLEAN (verified across all 12)
- **Migration numbering:** 330→337, one per asset table, NO collisions, NO gaps. 330 is the first L4
  migration + drops `kala_timeline` (CF.L3.2). Correct.
- **Cross-asset table references:** every brief references the others' real `phala_*` table names
  consistently (anchors/muhurta/mitigation/rectification/rectification_best/sankrama/pramana/outlook).
- **Anti-drift FKs:** all FK targets are real L2/L3/L4 tables (kala_convergence, kala_obstruction,
  kala_bhavishya, bodha_cdlm_cells, bodha_discoveries, phala_*). No phantom references.
- **Frozen-contract consistency:** every ph_* brief states `@register`/`WriterBase`/`run(ctx)`/never
  commit/`WriterResult(asset_id=, rows_inserted=)`/delete-then-insert/`$1` count_sql.
- **L4/L5 boundary:** ph_pramana is strictly non-scoring (D5); ph_suddha_sodhana reports verification
  state but L5 owns calibration; the reverse-calibration channel is defined but empty at L4. Clean.
- **Deterministic-first:** the ONLY generative LLM use is ph_phaladesa's serve-time narration over a
  fixed deterministic scaffold (D46), Gemini/DeepSeek, with a test that it cannot fabricate. Held.

## §2 — FINDINGS requiring a fix (before GATE D/E)

### F1 — Wave/dependency contradiction (must fix) — ph_nimitta vs its dependents share a wave
- **`ph_nimitta` is wave W3** (the spine, with its own SPINE-FIRST hard gate). But **`ph_muhurta` and
  `ph_pratikara` are ALSO labeled W3** while being `blocked_by: [ph_nimitta]`. A brief cannot be in the
  same wave as the asset that blocks it.
- **FIX — re-lay the waves** (the canonical L4 wave structure for the session_queue):
  ```
  W1  U1 (dāśā consensus, wire-only)
  W2  U2 (lifetime) · U3 (convergence currents, 6 now) · U4 (school consensus; U4 after U1)
      → re-seal L1?(no, U1 wire-only) / L3 (U2+U3) ; then U3 2nd-pass adds the school-consensus current after U4
  W3  ph_nimitta  (SPINE — alone; hard spine-first gate; consumes U1–U4)
  W4  ph_muhurta · ph_pratikara · ph_sankrama   (parallel; all blocked_by ph_nimitta)
  W5  ph_sodhana → ph_suddha_sodhana            (sodhana then its selector)
  W6  ph_pramana   (scaffolds all prediction assets)
  W7  ph_phaladesa (the finale; composes all)
  ```
  (The current briefs label muhurta/pratikara=W3, sankrama=W4, sodhana=W4, suddha=W4, pramana=W5,
  phaladesa=W6. Re-map to the above in the session_queue; the per-brief `wave:` fields are advisory —
  the QUEUE is authoritative — but align them to avoid Conductor confusion.)

### F2 — Stale "M9" live references (must fix) — U1, U2
- U1 + U2 were written BEFORE the M9→U4 rename (D34). They use "M9" as a LIVE reference to the school
  engine (e.g. U1 "feeds M9 / the M9 Yoginī engine"; U2 "feed M9 + L4"). D34 purged "M9".
- **FIX:** replace live "M9" → "U4 (School Consensus Activation)" / "the school-consensus engine" in U1
  + U2. (U4's own `legacy_naming_note` "do not reintroduce M9" is the ONLY legitimate remaining mention.)

### F3 — U3 ↔ U4 ↔ U2 shared-engine serialization (note for the queue)
- U2 and U3 BOTH edit `ka_sangam`/`SUPPORTING_WEIGHTS` (U2 horizon; U3 currents+weights). U3 says its
  edit lands BEFORE U2's lifetime run (R3) so one enriched build covers both — CORRECT, but the queue
  must SERIALIZE the shared `ka_sangam` edit (U3 currents → then U2 lifetime run), not parallelize them.
- U4's school-consensus current (C13) is U3's 2nd pass (post-U4). The queue must order: U3-pass-1 (6
  currents) → U4 → U3-pass-2 (add C13) → re-run convergence. Document this in the session_queue.

### F4 — ph_pramana wave vs ph_phaladesa (verify — OK)
- ph_pramana (W6→W5 after re-lay) scaffolds the PREDICTION assets; ph_phaladesa (the composite) is
  NOT a prediction-emitter, so pramana correctly does not block on it. Confirmed correct. ph_phaladesa
  may consume pramana's falsifier-structure for its honest-framing register (optional cross-link — see F5).

### F5 — Missed cross-links (enhancements; fold into the assets, not blockers)
- **ph_phaladesa ← ph_pramana:** the dossier's "confident/contested/speculative" register (PD3) could
  read ph_pramana's structured confidence tiers directly. Add ph_pramana to ph_phaladesa's read set.
- **ph_sodhana confidence circularity → ph_pramana:** the rectification confidence is partly circular
  (noted D43); ph_pramana should tag rectification predictions with an `epistemic_caveat` so L5 weights
  them carefully. Add a note.
- **ph_suddha_sodhana revision flag → ph_phaladesa:** if a chart revision is recommended (D43), the
  dossier should surface it ("note: rectification suggests your birth time may be 10:47; this reading
  assumes the recorded 10:43"). Add to ph_phaladesa's honest-framing.

## §3 — Elevation coherence (verified)
The elevations cohere as a system, not a pile of features:
- **Consensus spine:** U1 (dāśā) + U4 (school) → ph_nimitta Axis 6 → every prediction carries
  multi-method agreement. Coherent.
- **Convergence accuracy:** U3 enriches the score every anchor inherits → uniform uplift. Coherent.
- **Honesty thread:** confidence-as-range + contradiction-carry (ph_nimitta) → spillover discount
  (ph_sankrama) → proportional remedy (ph_pratikara) → decisiveness (ph_suddha) → non-scoring
  scaffolding (ph_pramana) → honest dossier registers (ph_phaladesa). One consistent epistemic discipline.
- **Actionability thread:** influenceable anchors (ph_nimitta V4) → mitigation (ph_pratikara) →
  muhūrta-timed initiation (ph_muhurta) → spillover pre-emption (ph_sankrama). One action loop.
- **Whole-instrument-as-judge:** ph_sodhana uses dāśā+convergence+school+dāśā-consensus to rectify —
  the same machinery the predictions use. Coherent reuse.

## §4 — Disposition
- **F1 (waves) + F2 (M9):** FIX NOW (this review applies F2; the queue applies F1).
- **F3 (serialization):** ENCODE in the session_queue (GATE D/E).
- **F5 (cross-links):** FOLD into the three assets as read-set additions (light edits) at GATE D/E.
- No structural gaps; no missing asset; no boundary violation; the 8-asset set is complete + coherent.

---
*End of L4_PHALA_HOLISTIC_REVIEW v1.0. 12 briefs reviewed; migration numbering + references + boundary
+ determinism CLEAN; 2 fixes (waves, M9-naming) + 1 queue-serialization + 3 cross-link enhancements.
The set is complete and coherent. Proceed to GATE D/E with these applied.*
