---
artifact: L3_KALA_TEMPORAL_ARCHITECTURE_v1_0.md
canonical_id: L3_KALA_TEMPORAL_ARCHITECTURE
version: 1.0
status: ARCHITECTURE / HANDOFF (L3 scope — the temporal half; defines the layer that completes timing queries)
authored_by: Cowork (grounded in the existing transit/muhurat engines) 2026-06-19
purpose: >
  Answer the native's timing query architecturally — "when is the next auspicious moment my Lakshmi yoga fires?"
  — and define L3 Kāla, the TEMPORAL layer that completes such queries. L2 Bodha is the STRUCTURAL half (what the
  yoga IS, why it matters); L3 Kāla is the TEMPORAL half (WHEN it next fires). KEY FINDING: much of the temporal
  machinery ALREADY EXISTS (transit_search engine, compute_transits, the Muhurat Finder) — so L3 is largely
  WIRING the existing services to the L2 structural layer via an ACTIVATION-PREDICATE bridge, not building from scratch.
grounded_against:
  - platform/python-sidecar/routers/transit_search.py + pipeline/transit_search (find_aspect_events / find_conjunction_events; ±10yr window)
  - platform/python-sidecar/pyjhora_adapter/transits.py (compute_transits)
  - platform/python-sidecar/muhurat/finder.py (Muhurat Finder — scores future windows vs panchang_engine; knockout for inauspicious)
  - platform/python-sidecar/panchang_engine/* + routers/panchang.py (panchanga for any date)
  - bg_transit_rules.py + ga_transit_anchors.py (transit rule + anchor machinery)
  - L2 Bodha: the signature_class + the NULL L3-fill hooks (active_dasha_periods_jsonb / activation_predicted_dates_jsonb) we RESERVED
---

# L3 Kāla — The Temporal Architecture (completing the timing query)

## §1 — The query decomposed: two perpendicular axes
"When is the next auspicious moment my Lakshmi yoga fires?" has TWO axes:
- **STRUCTURAL (timeless):** what IS Lakshmi yoga in this chart — constituents, strength, state, what "firing"
  means. → **L2 Bodha** (+ L1). BUILT. ✓
- **TEMPORAL (time):** at what future DATE do transiting planets reach the positions that activate it. → **L3
  Kāla + transit services.** Partially built — wiring needed.
The full answer requires BOTH engines together. This is the L2↔L3 seam we deliberately protected (cross-plane
resonance deferred to Kāla; signature_class + NULL hooks reserved in L2 — see §4: this is where they pay off).

## §2 — The native's instinct is correct: timing is SERVICES, not DATA
A future transit position is CONTINUOUS + INFINITE — "where is Jupiter at moment T" has a computed answer for
uncountably many T. You CANNOT pre-store the chart state at every future instant. Therefore:
- **Natal structural facts → STORED (finite).** L2 Bodha. Done.
- **Transit positions at a future moment → COMPUTED ON DEMAND (a service).** The ephemeris.
- **"When does condition X become true in the future" → a SEARCH service over the ephemeris.** The hard, valuable part.
**Timing = services, not hard-coded data.** The native reasoned to exactly the right architecture.

## §3 — WHAT ALREADY EXISTS (the encouraging finding — much of the temporal machinery is built)
- **`transit_search` engine** (`pipeline/transit_search` + `routers/transit_search.py`): `find_aspect_events` +
  `find_conjunction_events` — live-computes WHEN a transit aspect/conjunction occurs in a window (±10yr cap, a
  latency guard). **This IS the transit-search heart, for aspect/conjunction events.** ✓
- **`compute_transits`** (`pyjhora_adapter/transits.py`): transit positions for a chart at a time. The ephemeris-at-T service. ✓
- **The Muhurat Finder** (`muhurat/finder.py`): scores future windows for AUSPICIOUSNESS against the panchang
  engine (weighted tithi/nakshatra/vara/yoga/planet/native; KNOCKOUT to 0 if inauspicious). **This IS the
  auspiciousness-ranking layer.** ✓ (Built in Phase 4C, classically grounded — MC/BS/MMP/DP.)
- **The panchang engine** (`panchang_engine/*`): panchanga for ANY date — already future-capable. ✓
- **`bg_transit_rules` + `ga_transit_anchors`**: transit rule + anchor machinery (the classical transit-effect rules). ✓

## §4 — WHAT IS MISSING (the gap = the L2↔L3 BRIDGE + a richer event vocabulary)
The pieces exist but are NOT yet wired to the L2 STRUCTURAL layer. The query "when does MY LAKSHMI YOGA fire"
needs the chain: L2 (what the yoga is + its activation condition) → transit-search (when that condition holds) →
muhurat (rank by auspiciousness) → LLM. The missing links:
1. **The ACTIVATION-PREDICATE BRIDGE (the core missing piece).** A yoga's natal signature must yield a TRANSIT/
   DASHA condition that "fires" it ("Lakshmi yoga fires when its lord transits a kendra/trikona during a
   supportive dasha, free of affliction"). This bridge READS the L2 `signature_class` + the natal pattern, derives
   the activation predicate, and hands it to transit_search. **THIS is where the L2 design pays off** — the
   signature_class we stored and the active_dasha_periods/activation_predicted_dates hooks we left NULL are the
   L3-fill surface. Activation rules come from L0 classical transit/dasha rules (bg_transit_rules).
2. **Event vocabulary beyond aspect/conjunction.** transit_search does aspect + conjunction today. Yoga-activation
   may also need: ingress (planet enters a sign/house), dasha-period boundaries (the dasha timeline from ga_dashas
   — STRUCTURE in L2, DATES here), return/transit-over-natal-point, station/retrograde. Extend the event set.
3. **The DASHA timeline as a first-class temporal input.** ga_dashas holds the dated periods (the 536k rows we
   kept OUT of L2 to stay timeless). L3 is where they're ACTIVATED — "is the dasha supportive at moment T" is a
   lookup into ga_dashas, combined with the transit search.
4. **The CONFLUENCE search (the "rare opportune moment" engine).** The valuable part: find the moment where
   MULTIPLE conditions hold AT ONCE — yoga-lord transit + supportive dasha + auspicious panchanga + NO affliction.
   This is an AND over several event searches + the muhurat score. The rarity (a once-in-years confluence) is the
   point — no human can scan decades across all conditions simultaneously; the search service can.

## §5 — This is the DISCOVERY ENGINE applied to TIME (the deep connection)
"Discover rare opportune moments" = bo_anveshana's discovery mission projected onto the TEMPORAL axis:
- Structural discovery (L2/bo_anveshana): the consequential pattern in the static chart no acharya can see.
- **Temporal discovery (L3): the rare FUTURE MOMENT when the transiting sky activates a consequential natal
  pattern — the opportune window no acharya could compute by hand.**
The opportune-moment finder is the temporal twin of cross-subsystem discovery: cross-subsystem = discovery ACROSS
disciplines; opportune-moment = discovery ACROSS time. Both find the confluence a human cannot hold.

## §6 — The full pipeline for the native's query (what to build = mostly wiring)
1. **Identify the yoga structurally** → L2 Bodha / MSR. ✓ exists.
2. **Derive the activation predicate** → the L2↔L3 bridge (reads signature_class + L0 transit/dasha rules). ✗ BUILD.
3. **Compute transits over the window** → transit_search / compute_transits. ✓ exists (extend event vocab, §4.2).
4. **Search for when the predicate holds** → transit_search (confluence/AND search, §4.4). ✗ EXTEND to confluence.
5. **Check dasha support at candidate moments** → ga_dashas lookup. ✗ WIRE.
6. **Rank by auspiciousness** → Muhurat Finder. ✓ exists.
7. **Synthesize** → serve-time LLM (structural reasoning from L2 + temporal proof from L3). ✓.
**So: build the activation-predicate bridge (§4.1), extend the event vocabulary (§4.2), add dasha-support wiring
(§4.3) + the confluence search (§4.4). The endpoints (L2 structural, the ephemeris/transit/muhurat services, the
LLM) ALL EXIST.** L3 is the middle — and it's wiring + a bridge, not a from-scratch build.

## §7 — The L2→L3 contract (what L2 already provides for L3 — the payoff of our discipline)
- **signature_class** on natal patterns — the matchable fingerprint L3's activation predicate keys on.
- **The NULL hooks** (active_dasha_periods_jsonb / activation_predicted_dates_jsonb / dasha_activation_proximity_score)
  — the L3-FILL surface; L3 populates them when it computes activation windows (it does NOT write back into L2's
  timeless tables — it produces L3 artifacts that REFERENCE the L2 signal_id).
- **resonance_eligible** patterns (the yogas/configs that CAN be transit-activated) — L3's search targets.
- **The two-plane discipline** — L2 stayed timeless; L3 owns time. The seam is clean BECAUSE we protected it.

## §8 — Answers to the native's direct questions
- **"Do we have the engines to answer this correctly?"** — STRUCTURAL half: yes (L2). TEMPORAL half: the ENGINES
  largely exist (transit_search, compute_transits, Muhurat Finder, panchang) but are NOT YET WIRED to L2 via the
  activation-predicate bridge, and the confluence search needs building. So: NOT YET end-to-end, but most parts exist.
- **"Hard-coded data or services?"** — SERVICES (the native is right): structural facts stored (finite); transit
  positions + "when does X hold" computed on demand (infinite). Natal = data; time = service.
- **"How to discover rare opportune moments?"** — a CONFLUENCE search over the transit service for the moment when
  an L2-derived activation predicate + supportive dasha + auspicious panchanga + no affliction all hold at once.
  The discovery engine applied to time.
- **"What to build?"** — L3 Kāla as the wiring layer: the activation-predicate bridge (L2 signatures → transit/
  dasha conditions), the extended event vocabulary, the dasha-support wiring, the confluence search, and the
  `query_auspicious_timing(chart, target_pattern, window)` tool that returns ranked opportune moments with their
  structural reasoning (L2) + temporal proof (L3).

---
*End of L3_KALA_TEMPORAL_ARCHITECTURE v1.0. The timing query ("when does my Lakshmi yoga next fire, auspiciously?")
sits on the L2↔L3 seam: L2 Bodha = the structural half (BUILT); L3 Kāla = the temporal half. Timing is SERVICES
not DATA (the native reasoned correctly). KEY FINDING: the temporal engines largely EXIST (transit_search,
compute_transits, Muhurat Finder, panchang) — L3 is mostly WIRING them to L2 via the activation-predicate bridge
(which reads the signature_class + NULL hooks we deliberately reserved in L2) + building the confluence search for
rare opportune moments. The opportune-moment finder is the DISCOVERY engine applied to TIME. The two-plane
discipline we protected throughout L2 is exactly what makes this clean.*
