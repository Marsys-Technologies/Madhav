---
artifact: TRANSIT_GOCHARA_SUBSYSTEM_MASTER_PLAN_v1_0.md
canonical_id: TRANSIT_GOCHARA_SUBSYSTEM_MASTER_PLAN
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — maximal scope, ON-DEMAND service architecture (native-specified)
authored_for: the Transit/Gochara subsystem build (subsystem #4 of 7, Wave 2)
purpose: >
  Build the Transit subsystem to full classical depth — the missing half of prediction — using the
  ON-DEMAND SERVICE architecture (NEVER hard-code transit positions across time). Maximal transit-rule
  coverage + a deterministic transit engine + per-chart natal anchors. The L3 timing engine; what makes the
  instrument testable against lived events. Embedded via the pattern; roadmap §0.5 + computed-and-cited gate.
read_in_combination_with:
  - SUBSYSTEM_PROGRAM_ROADMAP_v1_0.md (§0 the 3-category split incl. SERVICE; §2 transit depth bar)
  - bg_panchanga / bg_ephemeris_engine (the L0-service pattern this mirrors)
  - DIGNITY_AVASTHA + YOGA master plans (transit consumes condition + triggers yogas)
  - existing: A1 ephemeris, A9 sade_sati, A15 time-synchronicity, A19 bhrigu-bindu transits
hard_gate: store transit RULES + natal ANCHORS (computed+cited); compute POSITIONS/DATES on demand; never store time-series positions; never store an interpretive transit "result".
governing_architecture: ON-DEMAND. Hard-coding transit positions for all time is impossible + wrong (infinite + trivially recomputable). Store rules+anchors; compute live.
---

# Transit / Gochara Subsystem — Master Plan (maximal, on-demand) v1.0

## §0 — The architecture (native-specified, non-negotiable)

**DO NOT hard-code transit positions across time.** It's infinite and trivially recomputable. Instead, the
three-category split (roadmap §0) with the SERVICE category load-bearing:
- **L0 transit SERVICE (`bg_transit_engine`)** — deterministic APIs, compute on demand from ephemeris/PyJHora.
  NOTHING stored across time.
- **L0 transit RULES (`bg_transit_rules`)** — every classical transit-significance rule, static + cited.
- **L1 natal ANCHORS (`ga_transit_anchors`)** — the chart's natal points the rules fire against; stored once
  per chart (small). NOT positions.
- **L2/L3 ASK the service at query time** — "is rule R active for chart C now / when does it next fire."
The instrument stays small; the infinite transit space stays computable. This is the whole point.

## §1 — L0 `bg_transit_engine` (the on-demand service)
Deterministic APIs (mirror bg_panchanga's service shape):
- `transit_positions_at(instant, ayanamsha)` → all grahas' positions at a moment (live from ephemeris).
- `transit_aspects_to(chart_id, instant)` → which natal points the current transits aspect.
- `transit_state_for(chart_id, instant)` → which transit RULES (§2) are currently active for the chart.
- `next_transit_event(chart_id, rule, from_date)` → when rule R next fires (root-find over the ephemeris) —
  the timing-engine primitive.
- `transit_window(chart_id, rule, date_range)` → all activations of rule R in a range.
All deterministic, live-from-DE441, nothing persisted across time. Zero LLM.

## §2 — L0 `bg_transit_rules` (MAXIMAL transit-significance reference — every classical rule, cited)
Enumerate EVERY deterministic transit rule:
- **Gochara from Moon** (the classical 12-house transit-effect rules for every graha from the natal Moon) +
  **Gochara from Lagna** (the same from Ascendant — both reckonings).
- **Vedha (obstruction) rules** — the transit-vedha pairs (a planet's good transit obstructed by another's
  position) for each graha; the full Vedha table.
- **Ashtakavarga-Kakshya transit (the deepest lens)** — bindu-gated transit strength: a transit's effect
  gated by the bindu count in the kakshya (sub-division) the transiting planet occupies. The Kakshya
  sub-lord transit. Sodhita-pinda transit strength. (This is the classical transit-strength method most
  systems omit — maximal must include it.)
- **Moorti Nirnaya** — the 4-fold transit result class (gold/silver/copper/iron Moorti) per transit.
- **Special transit cycles for EVERY planet** (not just Saturn): Kantaka/Vipareeta, Ashtama, Janma-transit
  for each graha; **Sade-Sati for Saturn + the equivalent slow-cycles for Jupiter (12-yr) and Rahu/Ketu**
  (the nodal 18-month transits), Dhaiya.
- **Station/retrograde sensitivity** — the rule that a transiting planet stationing on a natal point is
  heightened; retrograde re-transits (a slow planet crossing a point 3×).
- **Transit-to-EVERY-sensitive-point** — rules for transits to natal upagrahas, sahams, KP points, arudhas,
  Bhrigu Bindu, the special lagnas (not just natal grahas).
- **Eclipse-transit** rules (transit eclipse on a natal point), ingress (sankranti) rules.
- **Tara-bala-by-transit** (the transiting Moon's tara from natal — reuses the nakshatra subsystem's tara
  matrices), **transit-Panchapakshi** (reuses nakshatra bird tables).
Each rule = a deterministic predicate + classical citation. NO interpretive "result" stored (serve-time).

## §3 — L1 `ga_transit_anchors` (per-chart, small — the anchors only)
Per chart per ayanamsha: the natal points every transit rule needs — natal Moon (+ its sign/nakshatra for
Gochara + Tara), Lagna, all grahas, the sensitive points, the Ashtakavarga bindu maps (for Kakshya transit),
Sade-Sati Moon-sign anchors. **Stored ONCE; small.** The transiting positions are NEVER stored — the service
computes them against these anchors on demand.

## §4 — L2 exploitation (extend bo_laksana — flag for sign-off)
Transit SIGNALS computed at query time via the service: "Saturn transiting natal Moon = Sade Sati active
(rule + anchor stored, date computed live)." Transit-activated YOGA firings (reuses Yoga subsystem — a yoga
whose lords are transit-triggered now). Transit + dasha convergence (a transit firing during the relevant
dasha = high-weight). All computed from rules+anchors+service, never from stored time-series.

## §5 — L3 Kāla — THE TIMING ENGINE (the payoff)
`next_transit_event` + the rules + anchors = a deterministic timing fabric answering "WHEN does X activate
for this chart," computed on demand over infinite range. This is the missing half of prediction and what
makes the instrument TESTABLE against the Life Event Log (the research thesis). The ka_* timing assets
consume the transit service.

## §6 — L4/L5
L4: transit-timed remedies (do the remedy in the supportive transit window). L5: which transit rules
actually predicted events (held-out).

## §7 — Standards + hard gate
**ON-DEMAND service (nothing stored across time) is the architecture.** Computed-and-cited (rules + anchors
stored with citation; positions/dates computed live; no interpretive result stored). L0 service health-probe
(like bg_panchanga); L0 rules ON-CONFLICT; L1 anchors delete-then-insert. Orchestrator-native (the service is
an L0 service asset; the rules + anchors are data assets). No-JH-parity; no tier; surgical migrations. The
service is the AUTHORITY for live positions; never duplicate them into storage.

## §8 — Decisions upfront
1. Which Ashtakavarga-transit method (Kakshya vs Sodhita-pinda vs both — recommend both, cited). 2. Service
SLA/perf (a `next_transit_event` root-find over decades must be fast — define the bound). 3. Gochara result
class: store the deterministic Moorti/effect-CLASS (gold/silver/...) but NOT the prose. 4. Which slow-cycle
equivalents (Jupiter/Rahu Sade-Sati-likes) are canonical. 5. Eclipse/ingress rule sourcing.

---

*End. Transit subsystem maximal + on-demand: a deterministic transit ENGINE (compute live) + every classical
transit RULE (Gochara both-reckonings, Vedha, Ashtakavarga-Kakshya, all-planet special-cycles, station,
every-sensitive-point) + small per-chart anchors. The L3 timing engine; the testable half of prediction;
nothing hard-coded across time.*
