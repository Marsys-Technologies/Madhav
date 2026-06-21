---
artifact: CLAUDECODE_BRIEF_L3_KA_GRAHA_SANCARA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_GRAHA_SANCARA
brief_for: ka_graha_sancara — Graha-sañcara / Ephemeris-at-T SERVICE (L3 Kāla)
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.7.5(1), §5.9.3 (ephemeris-last + cache I-9), §5.10 (location-independent → leverage bg_ephemeris), §5.13.A2 (I-17 orb-strength needs speed), §3.1 (the real M3 impl), Q6 (consolidate dual compute_transits)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded for paste
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K1
  blocked_by: [k0_service_asset_type]   # CANONICAL id (collision audit 2026-06-21) — the K0 SERVICE asset-kind gate
  blocks: [ka_gochara, ka_dasha_kala, ka_sangam]  # the transit-search + convergence engines call this
  may_touch:
    - platform/python-sidecar/pyjhora_adapter/transits.py        # replace the stub
    - platform/python-sidecar/services/ka_graha_sancara/**        # NEW service module
    - platform/scripts/temporal/compute_transits.py               # READ-ONLY reference (do not break its CLI)
    - platform/scripts/seed/asset_registry_seed.ts                # register the service row
  parallel_safe_with: [ka_muhurta_seva, ka_yojaka]  # disjoint files; ka_dasha_kala touches ga_dashas not transits
---

# CLAUDECODE BRIEF — ka_graha_sancara (Ephemeris-at-T service)

## §0 — What this asset IS (one paragraph)
`ka_graha_sancara` (Graha-sañcara, "the motion of planets") is the **ephemeris-at-T SERVICE**: given a
moment T (and ayanamsha), it returns the sidereal positions, **speeds**, and retrograde state of all 9
grahas, plus Sade Sati state and eclipse-point proximity. It is the lowest-level temporal primitive —
**every other L3 engine calls it.** Per the founding principle (plan §2) it is a SERVICE (computed on
demand), not a stored table. It is the asset that finally makes `compute_transits` REAL (today the
adapter is a `return {}` stub — plan §3).

## §1 — Why it matters / where it sits in the strategy
- It is **infrastructure-critical:** the transit-search engine (`ka_gochara`), the convergence engine
  (`ka_sangam`), and Mode A/B (plan §5.7–5.9) all depend on "where are the planets at T" and "how fast
  / which direction." Without a real ephemeris-at-T, the entire temporal layer is non-functional.
- It carries the **§5.9.3 efficiency law:** because it is called repeatedly during a search, it MUST
  expose an **ephemeris CACHE (I-9)** — memoize each computed instant within a search so the expensive
  swisseph call happens once per (T, ayanamsha), reused across all predicate checks.
- It supplies the **raw material for the rigor stratum's continuous orb-strength (I-17):** the
  *speed* and *applying/separating* sign of a transit is a derivative of position — and the speed is
  ALREADY computed by both the M3 impl and stored in `bg_ephemeris.speed_dps`. This asset surfaces it.

## §2 — VERIFIED ground truth (do not re-derive — code-checked 2026-06-21)
- **The real implementation EXISTS but is STRANDED:** `platform/scripts/temporal/compute_transits.py`
  has `get_transit_states(birth_dt, query_date, ayanamsha='lahiri')` → returns a dict with keys:
  `query_date`, `ayanamsha`, `computed_by="pyswisseph"`, `ephe_mode="moshier"`, `natal_moon_sign`,
  `planets` (9 grahas incl. Ketu = Rahu+180; each with sidereal lon, sign, nakshatra, **speed**,
  retrograde), `sade_sati` ({active, phase, saturn_sign}), `eclipse_proximity` (list). It uses
  `swe.FLG_SIDEREAL | FLG_MOSEPH | FLG_SPEED`. **It guards `ayanamsha != "lahiri"`** (currently
  lahiri-only — see §5 multi-ayanamsha task).
- **The adapter is a STUB:** `platform/python-sidecar/pyjhora_adapter/transits.py` →
  `compute_transits(jd_ut, ...)` → `return {}`. This is the dual-`compute_transits` authority
  ambiguity (plan Q6).
- **`bg_ephemeris` ALREADY stores** `(date, body, ayanamsha_id, tropical_longitude, latitude,
  speed_dps, is_retrograde, source_citation)` for 1900–2150 (~825k rows, location-independent → plan
  §5.10 says LEVERAGE it). So daily positions + speed + retrograde are a TABLE READ, not a recompute.

## §3 — The build (MODERNIZE + INTEGRATE, not from scratch)
**3.1 — Consolidate to ONE authority (closes Q6).** Promote the real `get_transit_states` logic into a
proper service module `services/ka_graha_sancara/`; make `pyjhora_adapter/transits.py::compute_transits`
a **thin shim** that calls the service (or delete it and re-point callers). The signatures differ
(`get_transit_states(birth_dt, query_date)` vs `compute_transits(jd_ut, ...)`) — the shim adapts them.
**One authority; no stub; no dual impl.**

**3.2 — Two read paths (the §5.10 + §5.9.3 optimization).**
- **For dates within the `bg_ephemeris` range (1900–2150):** READ the stored row (`tropical_longitude`
  + `speed_dps` + `is_retrograde`) and apply the ayanamsha derivation — NO swisseph call. This is the
  cheap path the funnel hammers.
- **For dates outside the range OR sub-day precision (the muhūrta refine needs intra-day):** compute
  live via swisseph (the M3 path). `bg_ephemeris` is daily; intra-day moments need a live call.

**3.3 — The ephemeris CACHE (I-9).** A per-search memo keyed on (T-rounded, ayanamsha) → the computed
state. Within one convergence search, the same instant is queried many times (Mode A and Mode B both
probe it); compute/read once, reuse. Cache lifetime = the search; not a persistent store (that would
re-create the precompute model §5.10 forbids).

**3.4 — Expose speed + applying/separating (for I-17).** The service's per-graha output MUST include
`speed_dps` and a helper that, given a target longitude, reports whether a transiting graha is
APPLYING (closing toward exact) or SEPARATING — the sign of d(separation)/dt. This is the input the
orb-strength curve (I-17, owned by ka_gochara/ka_sangam) consumes. Surface it here; do not score here.

**3.5 — Multi-ayanamsha.** The M3 impl is lahiri-guarded. L3 inherits the 5-ayanamsha discipline
(plan §9; L2 stored ×5). Either (a) extend the service to all 5 ayanamshas via `bg_ephemeris`'
per-ayanamsha rows, or (b) document lahiri-primary + the 4 others as a derivation, matching how L1/L2
handled it. **Decision flagged — confirm the ayanamsha set with the convergence-engine brief
(ka_sangam) so they agree.** Default: serve all 5 (bg_ephemeris already keys on ayanamsha_id).

## §4 — Asset registration (service-kind)
Register `ka_graha_sancara` in `asset_registry_seed.ts` as `asset_kind='service'` (per K0):
- `layer: 'kala'`, sanskrit_name `'Graha-sañcara'`, english_name `'Ephemeris service'`.
- `count_sql: null`, `target_table: null` (it's a service).
- `depends_on: ['bg_ephemeris']` (the table it reads).
- a self-test (per K0): probe `get_transit_states` for the native's birth + a known date; assert the 9
  planets present, speeds non-null, sade_sati well-typed → sets `service_health`.

## §5 — Acceptance criteria [tagged; verify against PROD per plan §9]
1. **[verify: pytest]** the stub is gone — `pyjhora_adapter/transits.py::compute_transits` returns real
   data (or is removed and callers re-pointed); `grep -rn "return {}" pyjhora_adapter/transits.py` → 0.
2. **[verify: pytest]** the service returns all 9 grahas (incl. Ketu) with sidereal lon + `speed_dps` +
   retrograde for a known date; values match the M3 `get_transit_states` for the same input (parity
   with the stranded-but-correct impl — NOT a JH-parity oracle, plan §N.4 no-JH-parity).
3. **[verify: pytest]** within-range dates READ `bg_ephemeris` (assert no swisseph call on the cheap
   path, e.g. via a mock/counter); out-of-range/intra-day dates compute live.
4. **[verify: pytest]** the ephemeris cache returns the SAME object for a repeated (T, ayanamsha) within
   one search and computes once (call-counter assertion).
5. **[verify: pytest]** the applying/separating helper correctly classifies a known applying vs.
   separating transit (e.g. Saturn approaching vs. leaving a natal point).
6. **[verify: psql_prod + curl_prod]** `ka_graha_sancara` registers as a service-kind asset; the
   cockpit shows it with a health badge (not a row count); self-test passes for `482012f1`.
7. **[verify: FORENSIC]** the native's natal Moon sign derived by the service = Aquarius (the
   `get_transit_states` NATAL_MOON_SIGN anchor; consistent with FORENSIC Moon = Purva Bhadrapada /
   Aquarius-pada). Plan §B FORENSIC must hold.
8. **[contract]** the service module is import-clean; if it registers a self-test writer, that writer
   does NOT call `ctx.db_conn.commit()/.rollback()` (plan §9 / L2 Vimarśaka-RED). `grep` → 0.

## §6 — Embedded commands (paste-ready)
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-graha-sancara
# inspect the real impl you're promoting
sed -n '158,230p' platform/scripts/temporal/compute_transits.py
# confirm the stub you're replacing
grep -n "return {}" platform/python-sidecar/pyjhora_adapter/transits.py
# tests
cd platform/python-sidecar && pytest -q services/ka_graha_sancara tests/ -k "graha_sancara or transits"
# prod self-test (via proxy — data-plane is always prod, plan memory)
bash ../scripts/start_db_proxy.sh
```
> Branch/merge policy: Madhav change → human-gated PR to main (plan memory two-stream-branch-policy);
> the swarm Conductor stages it but the merge gate is per the master execution plan (authored later).

## §7 — Definition of done
- [ ] One authoritative ephemeris-at-T impl; stub gone (Q6 closed).
- [ ] Two read paths (bg_ephemeris cheap-read + live for intra-day/out-of-range).
- [ ] Ephemeris cache (I-9) with a call-count test.
- [ ] speed + applying/separating surfaced (feeds I-17).
- [ ] Multi-ayanamsha decision recorded + implemented.
- [ ] Registered service-kind; cockpit health badge; FORENSIC Moon anchor holds.
- [ ] PR opened with AC evidence.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Resurrects a stranded, correct engine + kills a stub** — turns the `return {}` adapter into the
   real swisseph-grounded ephemeris, AND consolidates the dual-`compute_transits` authority ambiguity
   (closes Q6) — removing a latent correctness hazard the corpus explicitly warns against.
2. **Bakes the efficiency law into the lowest primitive** — the two-read-path design (cheap
   `bg_ephemeris` table-read vs. live compute) + the per-search ephemeris cache (I-9) is what makes the
   whole funnel tractable; every higher engine inherits this for free.
3. **Surfaces the calculus the rigor stratum needs** — exposing `speed_dps` + applying/separating turns
   the future orb-strength curve (I-17) from "impossible" into "a function over data we already have,"
   because `bg_ephemeris` already stores speed and retrograde. This is the hidden enabler of A2.
4. **Re-grounds against FORENSIC** — wiring the natal-Moon anchor (Aquarius) into the service's
   self-test means the temporal layer's foundation is FORENSIC-verified at its root, not assumed.
5. **Makes location-independence concrete** — by reading the location-independent `bg_ephemeris` for
   positions and leaving the location-dependent step to `ka_muhurta_seva`, it enforces the §5.10
   boundary structurally at the primitive level.

---
*End of CLAUDECODE_BRIEF_L3_KA_GRAHA_SANCARA v1.0.*
