---
artifact: L3_KALA_CAMPAIGN_HANDOFF_v1_0.md
canonical_id: L3_KALA_CAMPAIGN_HANDOFF
version: 1.0
status: HANDOFF (the entry point for the L3 Kāla campaign — read THIS + the cited docs; no prior conversation needed)
authored_by: Cowork 2026-06-20
purpose: >
  Self-contained entry point for the L3 Kāla campaign — the TEMPORAL layer. L2 Bodha (structural synthesis +
  judgment + discovery) is SEALED. L3 Kāla answers the question L2 cannot: WHEN. It activates L2's timeless
  structural promise across time (dasha + transit), and discovers rare OPPORTUNE MOMENTS. Carries the L2→L3
  contract, the services-not-data principle, what already exists, the gap, and the wave plan.
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
read_in_order:
  - 00_ARCHITECTURE/L3_KALA_TEMPORAL_ARCHITECTURE_v1_0.md   # the architecture (the deep design — THE primary read)
  - 00_ARCHITECTURE/L2_BODHA_CLOSE_v1_0.md §8               # the L2→L3 onboarding contract (what L2 hands up)
  - 00_ARCHITECTURE/LEL_TOGGLE_GOVERNING_PRINCIPLE_v1_0.md  # L3 honors the same lel_enabled toggle
  - CLAUDE.md §C + CURRENT_STATE + git (always — verify live state)
---

# L3 Kāla — Campaign Handoff v1.0

## §1 — What L3 IS (the one-paragraph mission)
**Kāla = time.** L2 Bodha is TIMELESS — it holds what is structurally true about the chart (signals, judgment,
discoveries) with no date attached. **L3 Kāla is the TEMPORAL layer: it activates L2's structural promise across
time and finds WHEN.** "When does my Lakshmi yoga next fire, auspiciously?" — L2 says what Lakshmi yoga IS and why
it matters; L3 says WHEN the transiting sky activates it. L3 also does TEMPORAL DISCOVERY — the rare opportune
moment no acharya could compute by hand (the discovery engine applied to time).

## §2 — THE FOUNDING PRINCIPLE: timing is SERVICES, not DATA (native-reasoned)
A future transit position is CONTINUOUS + INFINITE — you cannot pre-store the chart state at every future instant.
So: **natal/structural facts = STORED (L0/L1/L2, finite); transit positions + "when does condition X hold" =
COMPUTED ON DEMAND (services + search).** L3 is built as SERVICES over the ephemeris, not as stored data. This is
the architectural spine — get it right and the rest follows.

## §3 — The L2→L3 contract (what L2 already hands up — the payoff of the two-plane discipline)
Throughout L2 we kept the structural plane TIMELESS and RESERVED the L3 attachment points. L3 consumes them:
- **`signature_class`** on natal patterns — the matchable fingerprint L3's activation predicate keys on.
- **The NULL hooks** (`active_dasha_periods_jsonb` / `activation_predicted_dates_jsonb` /
  `dasha_activation_proximity_score`) — the L3-FILL surface. L3 populates these (in L3 artifacts that REFERENCE the
  L2 signal_id; L3 NEVER writes back into L2's timeless tables).
- **The bo_anveshana falsifiable-hypothesis hooks** — L3 activations become datable predictions L4/L5 validate.
- **The two-plane seam is CLEAN because we protected it** — no time ever leaked into L2.

## §4 — WHAT ALREADY EXISTS (verified — L3 is mostly WIRING, not from-scratch)
- **`transit_search` engine** (routers/transit_search.py + pipeline/transit_search): `find_aspect_events` +
  `find_conjunction_events` — WHEN a transit aspect/conjunction occurs in a window (±10yr). The search heart. ✓
- **`compute_transits`** (pyjhora_adapter/transits.py): transit positions at time T. The ephemeris-at-T service. ✓
- **The Muhurat Finder** (muhurat/finder.py): scores future windows for AUSPICIOUSNESS vs the panchang engine
  (weighted tithi/nakshatra/vara/yoga; knockout if inauspicious). Classically grounded (MC/BS/MMP/DP). ✓
- **The panchang engine** (panchang_engine/*): panchanga for ANY date — future-capable. ✓
- **`bg_transit_rules` + `ga_transit_anchors`**: the classical transit-effect rules + anchors. ✓

## §5 — THE GAP (what L3 builds = the L2↔L3 bridge + the confluence search)
The engines exist but are NOT wired to the L2 structural layer. The build:
1. **The ACTIVATION-PREDICATE BRIDGE (the core new piece).** Reads an L2 signal's `signature_class` + the L0
   transit/dasha rules → derives the TRANSIT/DASHA condition that "fires" it ("Lakshmi yoga fires when its lord
   transits a kendra/trikona during a supportive dasha, free of affliction") → hands the predicate to transit_search.
2. **Event vocabulary extension** — beyond aspect/conjunction: ingress, dasha-period boundaries, return,
   transit-over-natal-point, station/retrograde.
3. **The dasha TIMELINE as a temporal input** — ga_dashas holds the dated periods (the 536k rows kept OUT of L2 to
   stay timeless). L3 ACTIVATES them: "is the dasha supportive at moment T."
4. **THE CONFLUENCE SEARCH (the valuable heart — "rare opportune moments").** Find the moment where MULTIPLE
   conditions hold AT ONCE — yoga-lord transit + supportive dasha + auspicious panchanga + no affliction. An AND
   over event searches + the muhurat score. The rarity is the point — no human scans decades across all conditions.
5. **The `query_auspicious_timing(chart, target_pattern, window)` tool** — returns ranked opportune moments, each
   with its STRUCTURAL reasoning (from L2) + its TEMPORAL proof (the transit calculation). The LLM narrates.

## §6 — The standards L3 inherits (same as every layer)
Deterministic-first (ephemeris + search + muhurat are deterministic; no generative LLM in the build); FROZEN
orchestrator contract (ka_* writers @register/WriterBase, never commit ctx.db_conn — heed the L2 Vimarśaka-RED
lesson: writers do NOT commit); anti-drift (L3 artifacts REFERENCE L2 signal_ids + L1/ephemeris facts, never
restate); the LEL toggle (L3 honors `lel_enabled` + `lel_origin` — timing calibrated by LEL only when enabled);
PROD-VERIFY; FORENSIC holds; only 482012f1; placeholder asset_ids are `ka_*` (registered, per CLAUDE.md §E).
**Two-plane note inverted:** L3 IS the time layer — it OWNS time; but it still must not corrupt L2 (write L3
artifacts, never back into L2).

## §7 — The proposed wave shape (for the L3 campaign plan — author next)
```
K0  Wire-up: the transit/ephemeris/muhurat services exposed as ka_* service-callable units (NOT stored assets).
K1  The ACTIVATION-PREDICATE BRIDGE: L2 signature_class + L0 rules → activation predicates (the core new build).
K2  Event-vocabulary extension (ingress/dasha-boundary/return/station) + the dasha-timeline activation read.
K3  THE CONFLUENCE SEARCH engine (the rare-opportune-moment finder) + query_auspicious_timing.
K4  TEMPORAL DISCOVERY (the discovery engine applied to time — opportune moments as first-class, ranked, provenanced).
K5  Retrieval + the eval (the timing-query corpus) + seal (L3_KALA_CLOSE + the L4 Phala onboarding contract).
```
NOTE: services-not-data means several "assets" are SERVICES (callable, not row-stores). The DAG/cockpit model may
need a "service asset" type — a design decision for the L3 campaign plan (flagged, not pre-decided).

## §8 — The first move for the L3 campaign
1. Read `L3_KALA_TEMPORAL_ARCHITECTURE_v1_0.md` (the design) + verify the existing engines' actual signatures.
2. Author the **L3 Kāla campaign plan** (the per-wave detail K0–K5, the service-asset model decision, the
   activation-predicate design — the crux: how `signature_class` deterministically yields a transit condition).
3. Then the per-unit briefs, then autonomous build (the same Conductor/AUTONOMY_RESILIENCE framework as L2).

## §9 — OPEN ITEMS carried FROM L2 (close as relevant; tracked, not blocking L3 design)
- **L2 PR #302 merge** + migration 326 (cockpit floors) + the §C prod re-verify of the Vimarśaka-RED fix — operator-gated.
- **bo_samskara is `placeholder_hash_v1`, NOT real Vertex embeddings** (the seal shipped the placeholder). Real
  semantic embeddings are a follow-on before semantic retrieval quality is relied on — track it (it does NOT block L3).
- The 3 F2 `remedy_corpus_gap`s + the chakra-table gap (L0-expansion follow-ons).
- F1 retrieval de-dup + the LEL `lel_origin` plumbing are DESIGNED (retrieval-strategy) — confirm built at serve-time.

---
*End of L3_KALA_CAMPAIGN_HANDOFF v1.0. L3 Kāla = the temporal layer: it activates L2's timeless structural promise
across time (dasha + transit) and discovers rare OPPORTUNE MOMENTS. Timing is SERVICES not DATA (native-reasoned).
The engines largely EXIST (transit_search, compute_transits, Muhurat Finder, panchang); L3 BUILDS the activation-
predicate bridge (reads the L2 signature_class + NULL hooks we reserved) + the confluence search. The two-plane
discipline protected throughout L2 is exactly what makes this clean. First move: read the architecture doc, author
the L3 campaign plan (the activation-predicate design is the crux), then build on the same autonomous framework.*
