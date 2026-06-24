---
artifact: L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN.md
canonical_id: L3_KA_SANGAM_TRANSIT_MODEL_REDESIGN
version: 1.0
status: DESIGN — the correct kala_convergence transit model (supersedes both the Jupiter-fallback and the MD-lord fix). NO BUILD until native ratifies the design.
authored_by: Cowork 2026-06-22
native_decision: "Stop, design the correct transit model first. Convergence stays at June-21 660-Jupiter until this lands. L4 seal gated on corrected ph_pratikara."
gates: L4 seal (ph_pratikara rebuilds from corrected kala_convergence)
---

# ka_sangam Transit Model — Redesign

## §1 — The bug, correctly stated (three layers deep)
1. **Surface:** `kala_convergence` for the native is 660/660 `constituent_factors->>'planet'='jupiter'`.
2. **First fix attempt (wrong):** the code read `transit_trigger->>'planet'` (a key that never exists) and
   fell back to the constant `'Jupiter'`, then ran a full Swiss-Ephemeris transit scan for Jupiter.
3. **Second fix attempt (also wrong + unrunnable):** substituted the active MD lord for the planet, still
   feeding a full ephemeris scan. Moon (13.2°/day) / Mercury (1.38°/day) produce orders of magnitude more
   crossings than Jupiter (0.083°/day) → 11h run, 271MB→1.2GB. Also semantically wrong: it conflates the
   **dāśā lord** (who governs the period) with the **transit planet** (whose sky position triggers an event).
4. **The ROOT (code-confirmed):** `ka_sangam` should not scan ephemerides AT ALL. The `transit_trigger`
   is a **RULE SPECIFICATION**, not a planet + a scan.

## §2 — What `transit_trigger` actually is (the authoritative contract)
Built by `services/ka_yojaka/binder.py::build_predicate()`. It is a classical-rule condition, e.g.:
```
'transit_trigger': {
   'type': 'benefic_transit_to_kendra_trikona',
   'trigger_events': ['benefic_aspect_to_graha', 'graha_return', 'ingress_dignity_sign'],
   'scale_by': 'transiting_graha_nature',
   'bg_transit_rules_ids': [1, 2, 3, 8, 9, 10],
   'veto_if': 'combust OR dusthana_transit OR malefic_conjunction',
}
```
There is **deliberately no `planet` key.** The trigger describes a CLASS of transit events ("a benefic
transits a kendra/trikona") satisfiable by WHICHEVER graha meets the rule — not one fixed planet. The
`bg_transit_rules_ids` point at L0 classical transit rules; `scale_by: 'transiting_graha_nature'` confirms
the transiting graha is determined at evaluation time, not pre-fixed.

## §3 — The upstream transit data EXISTS (so the redesign is buildable now)
`brahmagyan/kala/l3_timeline.py`:
- `_active_transits_for_period(start, end)` (line ~208) — FORENSIC-grounded slow-transit intervals
  (line ~98-100) covering the native's lifetime.
- Emits transit objects with real `transit_planet`, `transit_sign`, `transit_house`, `transit_nature`,
  `overlap_start/end` (line ~357). These are SPECIFIC, DATED transit events — exactly what a convergence
  window's transit factor should reference. **This is the source `ka_sangam` should consume.**

## §4 — The correct model (the redesign)
A convergence window's transit factor must be computed by **EVALUATING WHICH TRANSIT RULES FIRE in the
window against pre-computed transit events** — NOT by scanning a planet's ephemeris. Specifically:
1. For each window, gather the active transit events overlapping it from `l3_timeline._active_transits_for_period`
   (or a shared transit service / a persisted transit table) — these carry the real transiting graha + dates.
2. For each predicate's `transit_trigger` rule, evaluate whether any of those transit events SATISFIES the
   rule (using the `bg_transit_rules_ids` → L0 classical rules, the `trigger_events`, the `veto_if`/`mitigate_if`).
3. The window's `constituent_factors['planet']` becomes the **transiting graha(s) that actually satisfied
   the fired rule** — possibly a LIST (multiple grahas can co-trigger), not a single value. Store the set,
   or the strongest by `transiting_graha_nature` weight, per the convergence scoring model. NEVER a constant.
4. NO Swiss-Ephemeris scan inside ka_sangam — the ephemeris work was already done upstream (l3_timeline /
   the gochara service). ka_sangam is a SCORER/JOINER, not an ephemeris engine. This fixes the all-Jupiter
   bug, the perf explosion, AND the dāśā/transit conflation in one coherent change.

## §4.6 — PER-SIGNATURE TRANSIT-PLANET MODEL (refined diagnosis 2026-06-22 + native rulings)
The predicate `transit_trigger` is signature-specific; the correct transit-planet SOURCE differs per type:
| Signature | trigger type | correct transit planet | count |
|---|---|---|---|
| DOSHA | malefic_transit_over_afflicted_point | **Saturn** (slow; matches saturn_over_afflicted) | 270 |
| DIGNITY | graha_activation | **the signal's OWN graha** (signal_id → chart_facts) — a natal-position activation, likely a LOOKUP not a scan | 397 |
| DISPOSITOR_RELATIONAL | relational_link_transit (lord_transits_other_bhava) | the relevant lord, **but gated by confidence — NOT MD-lord-scan, NOT a cap** (see rulings) | 5,145 |
| YOGA | benefic_transit_to_kendra_trikona | **Jupiter** (classic benefic activator) | 481 |
| SUBSYSTEM | subsystem_trigger | NO transit search — subsystem path | 60,445 |

**NATIVE RULINGS (2026-06-22) that correct the diagnosis:**
- **NO hard cap (e.g. max_events=5).** A count cap truncates to an arbitrary slice ("which 5?") = the
  silent-plausible-wrong failure mode. REJECTED.
- **Gate by HIGH-CONFIDENCE threshold instead.** The engine ALREADY has the machinery: `orb_strength_score`
  (I-17, cos² decay) + the `confidence_label` threshold classifier (I-21), and the scan already takes
  `Score = max orb-strength across events` — i.e. it only ever cares about the STRONGEST event per window.
- **Why Moon/Mercury "explode":** the scan GENERATES + HOLDS all weak crossings in RAM (271MB→1.2GB)
  before taking the max. They were always going to be discarded by the max. **Fix = apply the orb/confidence
  threshold INLINE during the scan** so weak events are dropped as found, never accumulated. A fast lord
  then yields few qualifying events naturally — no explosion, no cap, self-regulating by merit. This is
  LESS code than the cap proposal.
- **Moon/Mercury are only relevant in their own MD periods** (~27 of 100 yrs); the threshold makes those
  windows yield sparse high-confidence events, which is CORRECT (a fast transit rarely makes a
  high-confidence life-event trigger), not a loss.

## §4.5 — RATIFIED DECISIONS (native 2026-06-22, objective: maximal genuine value, NOTHING speculative)
- **CRITICAL CODE FINDING:** `l3_timeline._active_transits_for_period` handles **SLOW transits ONLY**
  (Saturn, Jupiter, Rahu/Ketu) via a cheap in-memory overlap loop over a fixed `SLOW_TRANSITS` interval
  list — **NO ephemeris scan.** This is the intended model: slow transits are what time life-events in
  Jyotish. The MD-lord fix exploded precisely because it dragged in FAST planets (Moon/Mercury/Sun) the
  model deliberately excludes. The original all-Jupiter was a degenerate single-slow-planet version.
- **Q1 → NO new persisted transit table.** `ka_sangam` evaluates against the existing slow-transit
  overlap logic (`_active_transits_for_period` / the `ka_gochara` service) IN-MEMORY. It's cheap; the only
  consumer is ka_sangam (ph_muhurta uses ka_gochara separately). Persisting "for hypothetical L4/L5 reuse"
  = speculative infra for a non-existent consumer (violates the no-value-less-work objective + the
  don't-pre-build-for-later-phases rule). Reuse what exists; build nothing extra.
- **Q2 → `constituent_factors['planet']` becomes a LIST** of the slow-transiting graha(s) that fired the
  rule (a window CAN have Saturn AND Jupiter active — collapsing to one discards real signal; max-fidelity
  is to store the set). Downstream consumers that need a single graha (ph_pratikara's afflicting_graha)
  take the strongest by `transiting_graha_nature` weight from the list. Never a constant; absent if no rule fires.
- **Q3 → cascade scope = the DAG.** Drive ka_sangam → ka_vighnakara → ph_pratikara (+ any other convergence
  consumer) via the now-wired DAG cascade, not a hand-typed list. Confirm via registry depends_on.
- **Q4 → surgical L3 version-bump** of L3_KALA_CLOSE (engine-logic correction, real but contained; NOT a
  full re-seal). Native-authorized.

## §5 — (Resolved — see §4.5; retained for context)
- **Q1 — Persisted vs computed transit events:** does a persisted per-chart transit table exist (kala_*
  gochara), or are transit overlaps computed on demand by l3_timeline? If on-demand, the redesign should
  persist them once (a real `kala_gochara`/transit-events table) so ka_sangam JOINS rather than recomputes
  — and so L4/L5 can reuse them. CONFIRM the current state (the memory note says ka_gochara is a service,
  no persisted table — likely needs a persistence step).
- **Q2 — Single vs multiple planets per window:** ratify that `constituent_factors['planet']` becomes a
  LIST (the grahas that fired the rule), or a single primary by nature-weight. Downstream consumers
  (ph_pratikara's afflicting_graha bridge, ph_nimitta) must handle whichever shape — confirm the contract.
- **Q3 — Scope of the rebuild:** this changes `kala_convergence` → `kala_obstruction` (ka_vighnakara) →
  ph_pratikara (and any other convergence consumer). The DAG cascade (now wired) should drive this once
  the engine is fixed. Confirm the full downstream set via the registry depends_on before rebuild.
- **Q4 — L3 re-seal:** this is a genuine L3 Kāla engine correction → version-bump L3_KALA_CLOSE (surgical,
  not a full re-seal). The engine LOGIC was wrong (not just data), so it's a real fix, native-authorized.

## §6 — What NOT to do
- Do NOT re-introduce any ephemeris scan inside ka_sangam.
- Do NOT use the MD lord (or any dāśā lord) as the transit planet — that conflation is the bug.
- Do NOT use a hardcoded planet fallback. If a window has no firing transit rule, its transit factor is
  ABSENT (the convergence may still score on dāśā + signal factors) — do not invent a planet.
- Do NOT rebuild ph_pratikara until kala_convergence is corrected — its current 60 all-Jupiter mitigation
  rows are an artifact and L4 cannot seal on them.

## §7 — Sequence (once design ratified)
1. (If Q1 = persist) add a transit-events persistence step / table from l3_timeline / the gochara service.
2. Rewrite ka_sangam's transit-factor logic to CONSUME + EVALUATE rules against those events (no scan).
3. Rebuild via the ORCHESTRATOR (direct runners are retired): ka_sangam → ka_vighnakara → ph_pratikara,
   driven by the DAG cascade, with the new live progress bar (this is the slow build that finally lets you
   WATCH the stage animation — discharge that verification debt here; reload to refresh SSE first).
4. Verify: kala_convergence planet distribution is DIVERSE and matches the real transit events; ph_pratikara
   mitigation spans multiple afflicting grahas; version-bump L3; then L4 seal can proceed.

---
*End. The transit factor is a RULE EVALUATION over pre-computed transit events, not an ephemeris scan with
a fixed planet. Both prior fixes scanned ephemerides — that was the architectural bug. ka_sangam = scorer,
not ephemeris engine. Decide Q1-Q4, then build. Convergence stays June-21 state until then; L4 seal gated.*
