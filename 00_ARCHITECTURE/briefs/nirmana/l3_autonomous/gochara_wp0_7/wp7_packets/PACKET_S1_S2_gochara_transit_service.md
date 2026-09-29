---
artifact: WP7_PACKET_S1_S2
packet_id: "S-1 / S-2"
version: "1.0"
status: DESIGN_ONLY_NOT_IMPLEMENTED
date: 2026-09-23
owner: "Owner of platform/python-sidecar/services/ka_gochara/service.py (S-1) and of this family's directed-contact-event production (S-2, owed to Saṅgam's consumption per the native's Saṅgam M-3 ruling at 101046052)"
executes: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §6.2 S-1/S-2, §4.2, §6.1 (F-25 rows); GOCHARA_RULING_SHEET_v1_0.md N-7, N-14; WP0_FINDINGS.md consumer re-enumeration (F-25 correction holds — no third undercount)
authority_note: "Owed, not written into the owners' files. All call sites re-enumerated by fresh grep this run (WP0_FINDINGS.md): find_aspects definition service.py:63; callers kala_trigger/trigger.py:96,150,199 (duck-type contract :87), ka_sangam/engine.py:464, scripts/kala_admission/currents.py:59 (docstring), plus test fakes. search_long_horizon: transit_search.py:898; callers ka_sangam/engine.py:1383 (bypass) and the service itself (service.py:157)."
---

# S-1 / S-2 — GocharaTransitService: shape-compatible `find_aspects` + new `find_episodes`; directed contact events for Saṅgam

## S-1 — The service interface

### 1. Hard constraint: `find_aspects` keeps its exact shape

`find_aspects` at `platform/python-sidecar/services/ka_gochara/service.py:63-72` is
duck-typed by callers that are **not** in this family's may-touch and must not break:

- `services/kala_trigger/trigger.py:87` documents the contract explicitly —
  *"Uses the same gochara_service.find_aspects(...) duck-type contract
  ka_sangam.engine._c_benefic_dristi already relies on (read-only reuse of the
  interface shape, not of the file itself)"* — and calls it at `:96`
  (`_malefic_transit_over_mechanism`), `:150` (`_papa_kartari_sandwich`), `:199`
  (`guru_shani_double_transit`), each passing keyword args
  `(transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd)` and reading
  duck-typed attributes off the returned events (`ev.orb_at_event_deg`,
  `ev.applying_separating`, `ev.extra["aspect_deg"]`).
- `scripts/kala_admission/currents.py:56-59` states its four component scores
  *"all require a live `gochara_service.find_aspects(...)` transit-ephemeris engine"*
  — the admission harness feeds the service in unmodified.
- `services/ka_sangam/engine.py:464` (`_c_benefic_dristi`) calls it the same way.

So: **no signature change, no return-shape change, no rename.** The enriched interface
arrives as a NEW method. Internally the existing methods may be re-implemented as an
adapter over the kernel's episodes (that is this family's prerogative inside its own
may-touch files), provided the adapter reproduces the legacy `TransitEvent` field set
byte-for-byte in observable behavior.

### 2. The new method (interface design only — not implemented here)

TypeScript-style signature block (for the cross-language contract; the implementation
is Python):

```ts
// Kernel episode — the unit the ledger persists (plan §4.2/§4.3, WP1_CONTRACTS §3).
interface GocharaEpisode {
  contact_id: string                 // "sha256:<hex>" per WP1_CONTRACTS §3.2
  independence_group: string
  body: string                       // agent graha, Title-case
  relation: 'conjunction' | 'drishti_contact' | 'sign_ingress'
          | 'nakshatra_ingress' | 'kakshya_cell_crossing' | 'return'
  aspect_deg: number | null          // dṛṣṭi angle for drishti_contact; else null
  target_type: string                // WP1 §5.3 vocabulary
  target_ref: string
  target_resolution_state: 'resolved' | 'unavailable' | 'unqualified'
  t_in: string; t_exact: string; t_out: string   // UTC ISO-8601
  branch: 'direct' | 'retrograde' | 'station'
  truncated_at_horizon: 'start' | 'end' | null
  completeness_state: string         // F06 six states; unqualified propagated
  claim_grain: string
  convention_id: string
  // No overlay copy: Vedha/Moorti state at t_exact is recomputed by consumers
  // from interval sets (WP1_CONTRACTS §3.3).
}

interface EpisodeCoverage {
  partition_kind: 'body_target' | 'event_class' | 'moon_on_demand'
  partition_key: string
  requested_horizon: string          // tstzrange text
  completed_horizon: string
  relations_searched: string[]
  targets_requested: number
  targets_resolved: number
  targets_unresolved: number
  target_resolution_state_counts: Record<string, number>
  unavailable_inputs: Record<string, unknown>
  unsearched_reason: string | null
}

interface EpisodeBatch {
  episodes: GocharaEpisode[]
  coverage: EpisodeCoverage[]        // one per partition searched, incl. moon_on_demand
}

// The new service method — lives beside find_aspects in GocharaTransitService.
find_episodes(
  chartId: string,
  targets: Array<{ target_type: string; target_ref: string; target_fact_id?: string }>,
  horizon: { start_jd: number; end_jd: number },
  opts?: { bodies?: string[]; relations?: string[]; moon?: boolean }
): Promise<EpisodeBatch>
```

Python protocol form (for the sidecar's typing idiom):

```python
class EpisodeProvider(Protocol):
    def find_episodes(
        self,
        chart_id: str,
        targets: list[TargetRef],          # dataclass: target_type, target_ref, target_fact_id
        horizon: Horizon,                  # dataclass: start_jd, end_jd
        *,
        bodies: list[str] | None = None,
        relations: list[str] | None = None,
        moon: bool = False,                # R7: on-demand Moon; writes a
                                           # moon_on_demand coverage partition
    ) -> EpisodeBatch: ...
```

Semantics: `find_episodes` returns episodes **already solved** from the arc index /
contact ledger — it never re-scans the ephemeris per call; the per-(body ×
substrate_version) arcs are global, contact solving per chart (plan §4.2). A caller
asking for an interval with no persisted contacts and `moon=False` gets an empty
`episodes` list **with a full coverage object stating what was searched** — never a
bare `[]` (F06; the `moon_on_demand` partition records the searched interval even when
the answer is zero contacts, or L3-Q08 is unanswerable for Moon classes).

### 3. Adapter-over-episodes for the legacy shape

`find_aspects(transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd)` is
re-expressible over `find_episodes` as: targets = one degree target at `target_lon`
(`target_type='karaka'`-style synthetic ref, `target_resolution_state='resolved'`),
relations = `conjunction`/`drishti_contact` filtered to `aspect_degrees`, bodies =
`[transit_planet]`, horizon = `[start_jd, end_jd]`; then map each episode back to a
`TransitEvent` with `orb_at_event_deg` = |separation at t_exact|, `applying_separating`
derived from `branch` and pre/post separation, `extra.aspect_deg` = `aspect_deg`.
Whether the owner routes the legacy method through the adapter or keeps the existing
`find_aspect_events` path is an implementation choice **inside the service's own
may-touch** — the contract this packet pins is only: the duck-typed attribute surface
the four call sites read must keep working, and the §10 ecosystem test proves all four
call sites run unchanged.

## S-2 — Directed contact events for Saṅgam (producer side, per M-3)

### 1. What Saṅgam consumes today

- `ka_sangam/engine.py:464` — `_c_benefic_dristi` calls
  `gochara_service.find_aspects(transit_planet=benefic, target_lon=…, aspect_degrees=[0, 60, 90, 120, 180], orb=…, …)` —
  note the call site passes a **symmetric generic aspect set** (G-7's finding), not the
  per-graha classical table.
- `ka_sangam/engine.py:1374` — `mode_b_sweep` resolves a predicate's planet via
  `_resolve_transit_planet(predicate)` (`:992`) and then runs a **full-horizon
  ephemeris scan** through `search_long_horizon` (`:1383-1391`, imported at `:1363`),
  bypassing the service — for long horizons the service is skipped entirely.

### 2. The event contract this stream produces (M-3, N-14)

Directed graha-dṛṣṭi contact events, emitted as ordinary kernel episodes (N-7 ruled:
the producer path is the kernel):

```ts
interface DirectedContactEvent {      // a GocharaEpisode with drishti_contact relation,
                                      // served to Saṅgam in aggregated form
  window: { start: string; end: string }   // t_in/t_out
  target: { target_type: string; target_ref: string; longitude_deg: number | null }
  planets: string[]                  // LIST of grahas that fired — because multiple
                                      // grahas can dṛṣṭi the same point concurrently;
                                      // never a single scalar that drops the others
  aspects: Array<{ planet: string; aspect_deg: number; strength: number }>
                                      // per-graha fractional strength, graduated by
                                      // separation (dṛṣṭi-koṇa shape, BPHS ch.26
                                      // śl.6–8 — M-1's direction; the numeric decay
                                      // stays evidence-gated at WP8, so the field
                                      // carries the graduated value under the declared
                                      // orb per WP1 §7 with orb_source, and the
                                      // currently-ruled interim is the span-aware
                                      // legacy ±5 d box reproduced over t_in/t_out)
  direction: 'to_target'             // BOTH directions are produced as separate events
                                      // (transit→natal and, where Saṅgam's windows
                                      // warrant, the reverse relation) — never one
                                      // direction silently
  completeness_state: string
  coverage: EpisodeCoverage
  contact_id: string | null          // null only for live-computed (non-persisted,
                                      // e.g. Moon) episodes; persisted episodes carry it
}
```

Rules (normative):

- **Full Parāśari directed dṛṣṭi**: per-graha classical angles — Mars 90/180/210,
  Jupiter 120/180/240, Saturn 60/180/270, all others 180 only (the
  `SPECIAL_DRISHTI_DEG` table at `services/gochara_grammar/primitives.py:189-196`,
  minus nodes per N-14). No generic `[0,60,90,120,180]` symmetric set — consuming that
  was G-7's defect, and producing it would perpetuate it.
- **N-14 (ruled):** Rāhu/Ketu cast **no** dṛṣṭi — not the 7th. They are **excluded
  from the dṛṣṭi families** (`drishti_contact` never has body ∈ {Rahu, Ketu}) and
  remain full **agents and targets** for conjunction, ingress, kakṣyā-cell crossing and
  return. This removes the served 85 Rāhu + 87 Ketu `drishti_contact` records and
  retires `w30_nodal_drishti` from the λ product inside the same candidate generation —
  recorded as `completeness_state`, with the removed factor kept one generation as a
  labelled non-scoring annotation (N-14's three conditions; this packet covers the
  producer/serving shape — the projection-side λ change is this family's WP5/WP6
  work, not the receiving owner's).
- **Absent when nothing fires:** an interval with no directed contact carries **no
  event row** — never a zero-strength record standing in for silence (F06: silence is
  carried in the coverage object, `targets_resolved`/`unsearched_reason`, not in a
  fabricated 0.0 event).
- **No ephemeris scan inside Saṅgam:** `_resolve_transit_planet` (`engine.py:992`) is
  **replaced by event consumption**, not extended — Saṅgam's mode-B sweep reads
  `find_episodes` (or the P-4 capability) for the predicate's planet/target over its
  horizon and consumes the returned events; the `search_long_horizon` bypass at
  `:1363/:1383` retires when S-1 lands. The `mode_b_sweep` window at `:1376` ("SUBSYSTEM
  or unresolvable: skip sky scan entirely") becomes "no events produced → no windows",
  same honesty, no scan.

### 3. What this packet does NOT do

- S-1: does not change `find_aspects`, `find_eclipse_proximity` (`service.py:111`),
  or `long_horizon_search` (`:147`) signatures or return shapes; does not touch
  `transit_search.py` (FROZEN, must_not_touch — the kernel is its replacement, not its
  edit); does not touch kala_trigger or currents.py (T-1's owner decides adoption).
- S-2: does not implement anything inside `services/ka_sangam/**` (sibling-owned);
  does not decide the M-1 decay shape or orb values (WP8-gated — the strength field is
  specified to *carry* the graduated value under the declared orb, whichever WP8
  ratifies); does not change how Saṅgam consumes Vedha (V-1's edge declaration) and
  does not grant node dṛṣṭi anywhere.
- Neither packet persists Moon episodes by default (R7); Moon coverage partitions are
  first-class in the coverage object.

## 4. Acceptance tests

- **Ecosystem (F-25):** the three kala_trigger call sites (`trigger.py:96,150,199`)
  and `currents.py:59` run unchanged against the service — with a duck-typed fake and
  with the real service — before and after `find_episodes` lands. This is plan §10's
  ecosystem row for the service.
- **S-2:** fixture chart with a window where Jupiter and Saturn both dṛṣṭi one natal
  point: the event carries `planets=['Jupiter','Saturn']`, per-graha angles
  (120/60-family respectively), fractional strengths; an interval where nothing fires
  returns zero events and a coverage object (never a 0.0 row); a fixture with only
  Rāhu transiting produces **no** `drishti_contact` event and a `completeness_state`
  note naming the N-14 exclusion; both directions present as separate events when the
  reverse query is issued.
- **Grain:** every persisted episode carries `contact_id`; a Moon on-demand call
  returns episodes with `contact_id=null` **and** a `moon_on_demand` coverage partition
  whose `searched_horizon` equals the requested interval.
