---
artifact: CLAUDECODE_BRIEF_L3_KA_GOCHARA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_GOCHARA
brief_for: ka_gochara — Gochara / Transit-search SERVICE (L3 Kāla; THE UNBUILT HEART)
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§3 (the engine never built — the crashing router), §5.7.5(3), §5.9.2 (Mode-B trigger vocabulary + hybrid coarse-to-fine), §5.9.3 (ephemeris-last), §5.13.A2 (I-17 continuous orb-strength), §14.5.2 (subsumes ka_transit_almanac), Q7 (the ±10yr cap), I-8 (Mode-B magnitude threshold)]
starting_spec: feature/subsystem-transit:00_ARCHITECTURE/BRIEFS/PHASE_4D_TRANSIT_SEARCH_BRIEF_v1_0.md (a COMPLETE prior spec — implement + extend it)
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K2
  blocked_by: [ka_graha_sancara]   # uses the ephemeris-at-T service + cache
  blocks: [ka_sangam, ka_vighnakara, ka_kala_darshana]  # the convergence + danger + catalog engines all search via this
  may_touch:
    - platform/python-sidecar/pipeline/transit_search.py          # NEW — the missing module the router imports
    - platform/python-sidecar/routers/transit_search.py           # fix the crashing import; extend event_type enum
    - platform/python-sidecar/services/ka_gochara/**              # NEW service wrapper (extended vocabulary)
    - platform/scripts/seed/asset_registry_seed.ts                # register service row; retire ka_transit_almanac
  parallel_safe_with: [ka_muhurta_seva, ka_yojaka]   # disjoint; NOT parallel with ka_graha_sancara (depends on it)
---

# CLAUDECODE BRIEF — ka_gochara (Transit-search service) — THE UNBUILT HEART

## §0 — What this asset IS
`ka_gochara` (Gochara, the classical term for planetary transit) is the **transit-search SERVICE**:
given a trigger condition (which planet, which target longitude/point, which event class) and a
window, it live-computes **WHEN that condition holds.** It is the engine the audit found **was never
built** (plan §3): `routers/transit_search.py` imports `find_aspect_events`/`find_conjunction_events`
from `pipeline/transit_search` — a module that **does not exist on any branch** — so the router crashes
on import. This brief BUILDS that module (from the complete PHASE_4D spec) and EXTENDS it to the full
L3 trigger vocabulary. **This is the single most valuable build in the layer.**

## §1 — Why it matters / strategic role
- **It is the search heart of BOTH modes (plan §5.7–5.9).** Mode A searches *inside* daśā-survivor
  windows; Mode B sweeps for off-daśā high-magnitude confluence. Both call `ka_gochara`.
- **It carries the efficiency law (plan §5.9.3).** It is the EXPENSIVE service — so it fires LAST,
  only inside narrowed windows, and it reads through `ka_graha_sancara`'s cache (never raw swisseph
  in a hot loop).
- **It is where continuous orb-strength is born (plan §5.13.A2 / I-17).** Each event it returns
  carries the orb at exact + the speed + applying/separating — the raw input to the orb-strength curve.
- **It subsumes `ka_transit_almanac` (plan §14.5.2).** The "transit event almanac" IS this service's
  bounded output; the old filter-on-kala_timeline asset is retired.

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The module is MISSING; the router exists and EXPECTS this exact contract** (from
  `routers/transit_search.py`):
  - `find_aspect_events(swe, transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd) -> list[TransitEvent]`
  - `find_conjunction_events(swe, planet_a, planet_b, orb, start_jd, end_jd) -> list[TransitEvent]`
  - `class TransitEvent` with: `event_type, event_jd, event_datetime_ist, transit_planet,
    secondary_planet, exact_longitude_deg, orb_at_event_deg, sign, nakshatra, extra(dict)`
  - request: `event_type ∈ {aspect, conjunction}`; `aspect_degrees default [0,60,90,120,180]`;
    `orb_deg` clamped to [0.0, 3.0]; window cap ±10yr (the router rejects > 365×10 days).
- **A COMPLETE prior spec EXISTS:** `PHASE_4D_TRANSIT_SEARCH_BRIEF_v1_0.md` (on `feature/subsystem-transit`)
  fully specifies the algorithm: `swe.solcross`/`swe.mooncross` for Sun/Moon; **adaptive day-step
  bracketing + bisection** on signed longitude difference for the other 7; Rahu=MEAN_NODE, Ketu=+180;
  caller supplies start_jd/end_jd, internal logic does not extend the window. **IMPLEMENT THIS SPEC** —
  do not reinvent. (Note: PHASE_4D used MEAN_NODE; confirm node convention matches `ka_graha_sancara`,
  which used TRUE_NODE — RECONCILE, §3.4.)

## §3 — The build
**3.1 — Build `pipeline/transit_search.py` to the PHASE_4D spec (closes the crashing router).**
`TransitEvent` + `find_aspect_events` + `find_conjunction_events` exactly as the router expects.
Sun/Moon via solcross/mooncross; others via day-step bracketing + bisection on the signed diff. Make
`routers/transit_search.py` import cleanly (AC1).

**3.2 — Route through `ka_graha_sancara`, not raw swisseph (the efficiency law).** Position lookups go
through the ephemeris service + its per-search cache (I-9), so a window scanned by both modes computes
each instant once. The PHASE_4D spec calls swisseph directly; ADAPT it to call `ka_graha_sancara`.

**3.3 — EXTEND the event vocabulary (plan §5.9.2 Layer-1) beyond aspect/conjunction.** Add generators:
- **ingress** — a planet enters a sign/house (longitude crosses a 30° boundary or a house cusp).
- **return** — a planet returns to its natal longitude (Jupiter/Saturn/lord returns).
- **station / retrograde / direct** — speed crosses zero (the `ka_graha_sancara` speed surface makes
  this a sign-change detection on speed_dps; high-magnitude when on a sensitive point).
- **eclipse** on a sensitive point — node + luminary proximity (the `get_transit_states` eclipse_proximity
  is the seed).
- **multi-planet confluence** — 2+ planets simultaneously configuring a target (an AND over event searches).
- **transit-to-transit** — events between two transiting planets (not just transit-to-natal).
Each is a GENERATOR with a uniform interface, so new triggers plug in (extensibility = the flexibility
the native required for Mode B).

**3.4 — Continuous orb-strength + applying/separating (I-17).** Each `TransitEvent` MUST carry: the orb
at exact, the planet speed at event, and `applying|separating` (sign of d(separation)/dt from
`ka_graha_sancara`). Provide the orb-strength helper `f(orb, speed, applying/separating) ∈ [0,1]` —
full at exact (0° orb), fading to 0 at the orb boundary; applying weighted stronger than separating.
**The curve FORM + weights are native-ratified judgments (I-17/I-7) — propose, do not silently pick.**
ALSO: reconcile the node convention (PHASE_4D MEAN_NODE vs ka_graha_sancara TRUE_NODE) — pick ONE,
document it, apply everywhere.

**3.5 — Coarse-to-fine, NOT a hard ±10yr wall (plan Q7).** The PHASE_4D ±10yr cap is a latency guard,
but L3's value is confluences DECADES apart (plan §5.1). **Implement the hybrid (plan §5.9.2 Layer-2):**
analytic predictors (mean motions) PLACE & RANK coarse regions over a long horizon (may only ADD/
prioritize, NEVER veto); a coarse ephemeris grid owns COMPLETENESS within flagged regions (catches
retrograde multi-pass — a slow planet crossing the same aspect 3×); the precise bisection refines hits.
So the per-call window can stay bounded, but `ka_gochara` exposes a `search_long_horizon()` that tiles
the horizon via the predictor without the day-by-day cost. **This is the Q7 resolution.**

**3.6 — Subsume `ka_transit_almanac` (plan §14.5.2).** The bounded transit-event list IS this service's
output. Retire `ka_transit_almanac` from the seed (it only filtered the reworked-away kala_timeline);
re-point nothing (no downstream deps).

## §4 — Asset registration (service-kind)
`ka_gochara`: `asset_kind='service'`, `layer:'kala'`, sanskrit `'Gochara'`, english `'Transit-search service'`,
`count_sql:null`, `target_table:null`, `depends_on:['ka_graha_sancara']`. Self-test: find a KNOWN
transit event for `482012f1` (e.g. a Saturn aspect to a natal point on a known date) and assert the
event_jd matches within tolerance → service_health.

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** `pipeline/transit_search.py` exists; `routers/transit_search.py` imports cleanly
   (the crashing-router debt is closed); `find_aspect_events`/`find_conjunction_events` return the
   router-expected `TransitEvent` shape.
2. **[verify: pytest]** a known aspect (e.g. transiting Saturn 0° to a fixed target) is found at the
   correct JD within tolerance; Sun/Moon use solcross/mooncross, others use bisection (assert the path).
3. **[verify: pytest]** the extended generators each fire on a constructed case: ingress, return,
   station (speed sign-change), eclipse, multi-planet, transit-to-transit.
4. **[verify: pytest]** position lookups go through `ka_graha_sancara` + cache (call-counter: the same
   instant computed once across a dual-mode scan).
5. **[verify: pytest]** orb-strength helper: full at exact, ~0 at orb boundary, applying > separating
   for a known applying vs. separating transit.
6. **[verify: pytest]** coarse-to-fine: `search_long_horizon()` over 50 years finds a known far-future
   event a ±10yr-capped call would MISS, without a day-by-day full scan (assert region-tiling, not
   brute force). Retrograde multi-pass: a slow-planet 3× crossing returns 3 events.
7. **[verify: psql_prod + curl_prod]** `ka_gochara` registered service-kind; `ka_transit_almanac`
   retired; cockpit health badge; self-test passes for `482012f1`.
8. **[verify: node-convention]** one node convention (MEAN vs TRUE) chosen, documented, applied in both
   ka_graha_sancara and ka_gochara consistently (no drift).
9. **[contract]** no `ctx.db_conn.commit()/.rollback()` in any self-test writer (plan §9).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-gochara
# the prior spec to implement (on the other branch — read it, do not reinvent)
git show feature/subsystem-transit:00_ARCHITECTURE/BRIEFS/PHASE_4D_TRANSIT_SEARCH_BRIEF_v1_0.md | less
# the router contract you must satisfy
sed -n '1,114p' platform/python-sidecar/routers/transit_search.py
# confirm the module is currently missing (the bug)
ls platform/python-sidecar/pipeline/transit_search.py 2>&1   # should be: No such file
# tests
cd platform/python-sidecar && pytest -q pipeline/ services/ka_gochara -k "transit_search or gochara or aspect or conjunction"
```
> Branch/merge: Madhav human-gated PR (plan memory); Conductor stages, master plan gates.

## §7 — Definition of done
- [ ] `pipeline/transit_search.py` built to PHASE_4D spec; router imports clean.
- [ ] Extended vocabulary (ingress/return/station/eclipse/multi-planet/transit-to-transit) as generators.
- [ ] Routes through ka_graha_sancara + cache (no raw swisseph in hot loops).
- [ ] Orb-strength helper (I-17) + applying/separating; node convention reconciled.
- [ ] Coarse-to-fine long-horizon search (Q7 resolved); retrograde multi-pass correct.
- [ ] ka_transit_almanac retired (§14.5.2); ka_gochara registered service-kind.
- [ ] Self-test green for 482012f1; PR opened with AC evidence.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Builds the single missing engine the whole layer waits on, AND fixes a live crashing import** —
   `routers/transit_search.py` currently dies on a non-existent module; this is dead/broken code on
   main-line branches that this brief resurrects into the search heart.
2. **Salvages a complete prior spec instead of reinventing** — the PHASE_4D brief already worked out
   the hard numerics (solcross/mooncross + adaptive bisection); the brief reuses it and spends its new
   effort on the L3 extensions, not on re-deriving root-finding.
3. **Resolves the ±10yr cap that silently capped the product's core value (Q7)** — the coarse-to-fine
   long-horizon search means L3 can actually FIND a once-in-30-years confluence, which a naive cap
   structurally excluded. This is the difference between the discovery engine working and not.
4. **Delivers the full Mode-B trigger vocabulary as extensible generators** — ingress/return/station/
   eclipse/multi-planet/transit-to-transit, each pluggable, giving Mode B the "all permutations and
   combinations" flexibility the native explicitly required (and which a hard-coded aspect/conjunction
   engine could never provide).
5. **Catches a node-convention drift before it propagates** — MEAN_NODE (PHASE_4D) vs TRUE_NODE
   (ka_graha_sancara) would have produced subtly wrong Rahu/Ketu transits everywhere; the brief forces
   one convention across both engines.
6. **Births continuous orb-strength** — turning each event from a boolean into a graded, directional
   signal, the raw material the entire rigor stratum (A1 scoring, A3 window profile) is built on.

---
*End of CLAUDECODE_BRIEF_L3_KA_GOCHARA v1.0.*
