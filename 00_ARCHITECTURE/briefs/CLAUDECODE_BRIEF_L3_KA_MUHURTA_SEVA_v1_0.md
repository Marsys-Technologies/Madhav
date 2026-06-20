---
artifact: CLAUDECODE_BRIEF_L3_KA_MUHURTA_SEVA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KA_MUHURTA_SEVA
brief_for: ka_muhurta_seva — Muhūrta-sevā / Panchāṅga-muhūrta SERVICE (L3 Kāla; the fine sieve)
parent_plan: 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v1_0.md (currently v0.10 DRAFT)
plan_refs: [§5.6 Pillar-2 (panchāṅga value; Tāra Bala native overlay = its deepest contribution), §5.7.2 Stage-3 (the fine sieve), §5.7.4 (knockout), §5.10 (LIVE-compute by date+location — NOT a stored daily asset; demote the fenced cache I-10), I-4 (panchāṅga deep-research surface)]
version: 1.0
status: AUTHORED — ready for the autonomous swarm
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
executor: agentic swarm (Conductor-driven) / Claude Code in Antigravity — commands embedded
authored_by: Cowork 2026-06-21
swarm_coordination:
  wave: K1
  blocked_by: [k0_service_asset_type]   # CANONICAL id (collision audit 2026-06-21) — the K0 SERVICE asset-kind gate
  blocks: [ka_sangam, ka_vighnakara]  # the convergence + danger engines call the fine sieve / knockout
  may_touch:
    - platform/python-sidecar/services/ka_muhurta_seva/**         # NEW service wrapper
    - platform/python-sidecar/muhurat/finder.py                   # modernize (extend events; remove location assumptions)
    - platform/python-sidecar/panchang_engine/panchang_daily_reader.py  # DEMOTE the Bhubaneswar fence to internal memo (I-10)
    - platform/scripts/seed/asset_registry_seed.ts                # register service row
  parallel_safe_with: [ka_graha_sancara, ka_dasha_kala, ka_gochara, ka_yojaka]  # disjoint files (panchanga vs transits vs dashas)
---

# CLAUDECODE BRIEF — ka_muhurta_seva (Panchāṅga-muhūrta service)

> **⚠️ SCOPE CORRECTION (branch audit 2026-06-21) — the engine is ~90% ALREADY ON MAIN; this is a WRAPPER + un-floor.**
> The full panchanga engine is production-grade on main: `panchang_engine/*` (20 rich topics, upagrahas,
> lagna/cusps via `swe.houses_ex`, calendrical, festivals, micro-timings) + `muhurat/finder.py` with
> `panchanga_day(date,lat,lon,tz)`, `panchanga_instant(...)`, `find_muhurat(event,date_from,date_to,lat,lon,native_chart)`.
> **CRUCIAL:** `panchang_engine/tara_bala.py` EXISTS but is **intentionally FLOORED to `None`** (Topic 16,
> `Optional` field) because it needs the native's janma nakshatra. **So ka_muhurta_seva's REAL work is NOT
> building the engine — it is:** (1) the `ka_*` SERVICE wrapper (using K0's extended schema); (2) **UN-FLOOR
> Tara Bala** — wire the native_chart overlay so Topic 16 actually computes against the native's birth
> nakshatra (this is the §1 native-specific surgical-window payoff); (3) the service-health self-test writer;
> (4) the retrieval tools (the stale `l0fr-stream-e:query_muhurta.ts` is a design reference only). Do NOT
> rebuild the engine — wrap it + un-floor it.

## §0 — What this asset IS
`ka_muhurta_seva` (Muhūrta-sevā, "the service of the auspicious moment") is the **panchāṅga/muhūrta
SERVICE**: given a date (or window) AND A LOCATION, it computes the panchāṅga and scores the moment for
auspiciousness — qualifying time astrologically, overlaying the NATIVE via Tāra Bala, and applying the
inauspicious KNOCKOUT. It is the **fine sieve** of the funnel (plan §5.7.2 Stage-3): the convergence
engine narrows to candidate DAYS, then `ka_muhurta_seva` narrows each day to the auspicious HOURS.
**It is LIVE-COMPUTE, parameterized by (date, LOCATION) — NOT a stored daily asset** (plan §5.10, the
native's location correction).

## §1 — Why it matters / strategic role
- **It makes the window native-SPECIFIC (plan §5.6 Pillar-2).** Tāra Bala overlays the native's birth
  nakshatra against the day's nakshatra — the bridge from "auspicious in general" to "auspicious FOR
  THIS NATIVE," which is the §1 surgical-window idea made concrete. **This is panchāṅga's deepest
  contribution to L3.**
- **It is the safety floor (plan §5.7.4).** The inauspicious KNOCKOUT zeroes a window regardless of
  other scores — feeding both the opportune-window pipeline and the danger engine (`ka_vighnakara`).
- **It is the cleanest confirmation of "timing = services" (plan §5.10).** Because panchāṅga is
  LOCATION-dependent and the native moves, this is genuinely a service — never a precomputed table.

## §2 — VERIFIED ground truth (code-checked 2026-06-21)
- **The engine is REAL and classically grounded** (`muhurat/finder.py`):
  - `score_muhurat(panchang, event, weights=None, native_chart=None) -> float` (0..100; knockout → 0).
  - `find_muhurat(event, date_from, date_to, lat, lon, tz_offset_minutes, native_chart=None, weights=None,
    top_n=10) -> list[MuhuratWindow]`. **Already takes lat/lon/tz — i.e. already location-parameterized.**
  - `find_muhurat_from_cache(...)` — the cache-backed variant.
  - factors: tithi, nakshatra, vara, special-yogas, planet (Jupiter/Venus non-combust), and the NATIVE
    overlay via `compute_tara_bala_score(birth_nakshatra_id, current_nakshatra_id)`.
  - `_in_inauspicious(panchang)` → the knockout. `_score_to_stars` → 1..5 rating.
- **EVENTS_MVP (6 activity-classes today):** `vivah, griha_pravesh, vyapara, yatra, property_purchase,
  mantra_initiation`. Scored via per-event weight tables + `config/muhurat_weights.yaml`.
- **The location-fence reader to DEMOTE** (`panchang_daily_reader.py`): `is_bhubaneswar(lat,lon)` with
  `LOCATION_FENCE_KM=10.0`, `fetch_panchanga_range(...)` reads the `panchanga_daily` cache, silent
  fallback to live compute outside the fence. **Per plan §5.10/I-10: this is at most an internal
  native-home memo, NEVER a layer asset. Demote it (§3.3).**
- **The panchang engine** (`panchang_engine/*`) computes panchāṅga for any date+location; future-capable.

## §3 — The build (MODERNIZE; the engine mostly exists)
**3.1 — Wrap as a SERVICE.** Build `services/ka_muhurta_seva/` exposing: `score(date, location, event,
native_chart)` and `find_windows(event, window, location, native_chart, top_n)`. It calls the existing
`score_muhurat`/`find_muhurat` — modernized (below), not rewritten. It reads positions through
`ka_graha_sancara` where it needs planetary state (e.g. combustion), keeping ONE ephemeris authority.

**3.2 — (date, LOCATION) is mandatory, never defaulted (plan §5.10).** `find_muhurat` already takes
lat/lon/tz — KEEP that and make it REQUIRED at the service boundary (no implicit Bhubaneswar). A query
without a location is an error, not a silent native-home assumption. This is the structural enforcement
of the native's correction.

**3.3 — DEMOTE the location-fenced cache (plan I-10).** Reclassify `panchang_daily_reader` +
`panchanga_daily` as an INTERNAL performance memo for the native's HOME location ONLY — explicitly NOT a
`ka_*` layer asset, never registered. The service computes LIVE for whatever location the query carries;
the fenced cache is a transparent speedup only when (and only when) the query location IS the native's
home. Document this clearly so no future session promotes it.

**3.4 — Extend the event vocabulary toward the QT space.** EVENTS_MVP has 6 activity-classes. L3's QT-2
(window-for-purpose) and QT-8 (intervention-timing) need more — esp. **remedial/intervention events**
(the astrovāstu/upāya windows, plan §5.11.4-I) and general "auspicious initiation." Add events +
weight-table rows for the intervention classes the QT-8 loop needs. **The weights are native-ratified
judgments (I-7) — propose, do not silently pick.**

**3.5 — Surface the panchāṅga value layers for I-4 (the native's deep-research ask).** Expose the
breakdown so the convergence engine can use panchāṅga in THREE roles (plan §5.6 Pillar-2): (a) the
confluence-score contribution (tithi/nakshatra/vara/yoga); (b) the NATIVE-overlay (Tāra Bala); (c) the
KNOCKOUT. ALSO scope the I-4 research surface for a later pass: hora, choghadiya, the muhūrta
sub-divisions, eclipse windows — flagged, not all built now (note which are in scope for v1 vs deferred).

**3.6 — Intra-day precision.** Muhūrta is an HOUR-grain answer; the service must compute panchāṅga at
intra-day resolution (sunrise-relative limb boundaries), using `ka_graha_sancara`'s live path for the
sub-day instants (the cheap bg_ephemeris table-read is daily; hours need live compute — plan §5.10).

## §4 — Asset registration (service-kind)
`ka_muhurta_seva`: `asset_kind='service'`, `layer:'kala'`, sanskrit `'Muhūrta-sevā'`, english
`'Panchāṅga-muhūrta service'`, `count_sql:null`, `target_table:null`, `depends_on:['ka_graha_sancara']`.
Self-test: score a known auspicious + a known inauspicious date for `482012f1` at the native's home
location; assert the knockout zeroes the inauspicious one and Tāra Bala applies → service_health.

## §5 — Acceptance criteria [tagged; prod-verified per plan §9]
1. **[verify: pytest]** the service requires (date, location); a call with no location ERRORS (no
   silent Bhubaneswar default) — the §5.10 enforcement.
2. **[verify: pytest]** Tāra Bala native overlay changes the score for the SAME day between two
   different birth nakshatras (proves the native-specific overlay is live).
3. **[verify: pytest]** the knockout: a compound-inauspicious panchāṅga returns 0 regardless of other
   high factors (`_in_inauspicious` path asserted).
4. **[verify: pytest]** the same date scored at TWO different locations yields different
   tithi/vara boundaries (proves location-dependence — the reason it's a service, not data).
5. **[verify: pytest]** the new intervention/remedial event classes score (QT-8 readiness).
6. **[verify: grep + docs]** `panchang_daily_reader`/`panchanga_daily` is NOT registered as a `ka_*`
   asset and is documented as an internal native-home memo (I-10 demotion).
7. **[verify: psql_prod + curl_prod]** `ka_muhurta_seva` registered service-kind; cockpit health badge;
   self-test passes for `482012f1`.
8. **[verify: FORENSIC]** the native's birth panchāṅga via this service = tithi Shukla Tritiya, vara
   Ravivara, moon-nakshatra Purva Bhadrapada, yoga Shiva, karana Garaja (plan §B — the 7 anchors hold).
9. **[contract]** no `ctx.db_conn.commit()/.rollback()` in any self-test writer (plan §9).

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l3-ka-muhurta-seva
# the real engine you're wrapping
sed -n '32,260p' platform/python-sidecar/muhurat/finder.py
# the fence to demote
sed -n '1,90p' platform/python-sidecar/panchang_engine/panchang_daily_reader.py
# tests
cd platform/python-sidecar && pytest -q services/ka_muhurta_seva muhurat/ -k "muhurta or tara_bala or knockout or location"
```
> Branch/merge: Madhav human-gated PR (plan memory); Conductor stages, master plan gates.

## §7 — Definition of done
- [ ] Service wrapper; (date, location) mandatory; no silent native-home default (§5.10).
- [ ] Fenced cache demoted to internal memo (I-10), documented, not registered.
- [ ] Tāra Bala native overlay + knockout exposed for the convergence + danger engines.
- [ ] Intervention/remedial event classes added (QT-8 readiness); I-4 surface scoped.
- [ ] Intra-day precision via ka_graha_sancara live path.
- [ ] Registered service-kind; FORENSIC birth-panchāṅga anchors hold; self-test green.
- [ ] PR opened with AC evidence.

---

## §8 — VALUE ADDED BY THIS BRIEF (beyond the baseline)
1. **Makes the surgical window NATIVE-specific** — wiring Tāra Bala as a first-class overlay turns the
   layer's output from "a good day in general" into "a good day FOR THIS NATIVE," which is the entire
   §1 promise; without it L3 would just be a generic almanac.
2. **Structurally enforces the native's location correction (§5.10)** — making (date, location)
   mandatory and ERRORING on a missing location means the silently-wrong-when-you-travel failure mode
   is impossible by construction, not by convention.
3. **Demotes a latent landmine** — the Bhubaneswar-fenced cache, left as-is, would eventually be
   mistaken for a layer asset and bake the native's home into everyone's results; this brief explicitly
   demotes and documents it (I-10), closing a real future-drift hazard.
4. **Adds the knockout as a shared safety floor** — exposing `_in_inauspicious` to BOTH the opportune
   pipeline and the danger engine means "do not act here" is computed once and reused, and danger is
   never silently averaged away.
5. **Opens the intervention-timing surface (QT-8)** — adding remedial/upāya event classes is what lets
   the prophecy→agency loop later time a SPECIFIC remedy, not just observe a window.
6. **Re-grounds against FORENSIC at the panchāṅga root** — the birth-panchāṅga self-test ties the
   service to the 7 birth anchors, so the fine sieve is FORENSIC-verified, not assumed.

---
*End of CLAUDECODE_BRIEF_L3_KA_MUHURTA_SEVA v1.0.*
