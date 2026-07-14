---
artifact: BRIEF_D1_5B
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN)
wave: D-1.5b — foundation capabilities (§L injections + load-bearing D-1 leftovers)
version: 1.0
status: FROZEN+BOUND — B1's cusp unknown closed by the 2026-07-15 spike (PyJHora 4.8.6 exposes
  Sripati/Placidus cusp computation natively; bindings in §B). Binder re-verifies at open.
governing: CONDUCTOR_PROTOCOL.md + DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0.md §4
prerequisite: D-1.5a gate GREEN (hard block)
gate: Gate B per the execution plan §4 (chalit/Sudarshana/BB/bhava-bala/AV/positions/budgets/§N.6/
  CI + per-item B6/B8/B9 assertions) — all MCP on the deployed connector post-rebuild.
---

# D-1.5b — Foundation Capabilities

## FROZEN §F1 — Lane map (7 parallel lanes)

### Lane B-1 — Bhāva-chalit + real cusps (CR-98, DR-2 full form) · the headline · 2 verifiers
Whole-sign stays primary (DR-2); chalit is a FULL SECOND DATA LAYER consumed in synthesis.
1. **Compute:** in `pyjhora_adapter/houses.py`, call `drik.bhaava_madhya_sripathi(jd, place)`
   (vendored `jhora/panchanga/drik.py:1650`) for Sripati and `drik.bhaava_madhya_swe(jd, place,
   house_code='P')` (`:1595`) for Placidus; surface `(start, cusp, end)` per house in chart output
   (`charts.bhava_chart`, `jhora/horoscope/chart/charts.py:120`, gives planet→bhāva assignment).
   Mind the local-time-JD caveat noted at `houses.py:29-31`.
2. **Facts (L1):** new categories `house_chalit` (per graha: sripati bhāva + cusp distances),
   `bhava_cusps` (12 × {start, madhya, end} × {sripati, placidus}), `sandhi_flag` (graha within 3°
   of a bhāva boundary, or whole-sign≠chalit divergence). Whole-sign `house_d1`
   (`pyjhora_adapter/compute.py:80`, `ga_positions_writer.py:265,282`) is UNTOUCHED.
3. **Quarantine the fake KP cusps:** `ga_sensitive_writer.py:1787` (`lagna + (n-1)*30`) and the
   second emitter `ga_nakshatra_emitters.py:156` — replace with real Placidus cusps (the adapter
   path `sensitive_points_writer_a5_adapter.py:280` already consumes real cusps when provided) and
   mark the fake sub-lord approximation (`:1791`) `[EXTERNAL_COMPUTATION_REQUIRED]` or compute the
   real 249-division sub-lord IF trivially derivable from nakshatra-lord tables — else quarantine
   honestly (B.10). No fake precision survives this lane.
4. **Serving:** `house_chalit` + flags alongside whole-sign on `ganita_positions_get`,
   `ganita_chart_facts_get`, `ganita_condition_get`, and `judgment_query` checklist rows (bhava/
   bhavesha condition show both frames); divergence disclosed in verdict notes.
5. **MSR ingestion:** chalit facts ingested as synthesis data — chalit-frame context on position
   signals + a `frame_divergence` signal (subject, whole-sign house, chalit house, sandhi distance)
   with real salience. Type specimen must fire: Moon 29°46′ Aquarius → chalit 12th vs whole-sign 11th.
Verifier 1 (compute): cusps match independent Swiss-ephemeris check for 482012f1; Moon specimen
reproduces. Verifier 2 (serving): all four surfaces + MSR rows live.
**Identity facts for independent recomputation (Verifier 1):** birth 1984-02-05 10:43 IST (+05:30),
Bhubaneswar, Odisha (~20.2961°N, 85.8245°E); ayanamsha `lahiri_chitrapaksha`; expected D1 lagna
12.4311° Aries; Moon 29°46′ Aquarius (the sandhi specimen — whole-sign H11, expected Sripati H12).
FORENSIC anchors for sanity: Sun Capricorn · Moon Purva Bhadrapada · Shukla Tritiya · Ravivara.

### Lane B-2 — Bhāva Bala (CR-103) + Aṣṭakavarga completion (CR-99a)
- Bhāva Bala: six-source house strength via PyJHora; new L1 facts per bhāva. Do NOT hand-roll —
  use the library's implementation; if absent, mark `[EXTERNAL_COMPUTATION_REQUIRED]` and PARK the
  sub-item (B.10).
- Aṣṭakavarga: re-key existing 96 BAV/SAV facts **by sign** (house-keying is the wrong key for
  transit use — keep house-keyed rows for continuity, add sign-keyed); add trikoṇa/ekādhipatya
  śodhana, piṇḍas, kakṣyā boundaries as facts. **Do NOT rebuild the bindus** (§L.3 baseline).

### Lane B-3 — Sudarśana Chakra (CR-100)
Pure L2 derivation over existing facts: tri-frame (Lagna/Chandra/Sūrya) house assignment per graha;
`sudarshana_agreement` signal class — confirmed-in-3-frames amplifies, contradicted flags (the
Sun+Mercury 12th-from-Moon vs 10th-from-Lagna specimen must fire). No new L1 compute.

### Lane B-4 — Bhavat Bhavam (CR-97)
The 12-cell doctrinal map (only odd houses receive: 1→1,7 · 3→2,8 · 5→3,9 · 7→4,10 · 9→5,11 ·
11→6,12) as registry data; **GATED AMPLIFIER** signal class — fires ONLY when an already-salient
configuration (tier ≥ major, or fired yoga) occupies/rules a derived house; never a generator;
restraint rules served as first-class data (even houses receive nothing; secondary never overturns
primary; no chaining). Shastra-map extension: domain → {primary} ∪ {derived} bhāvas. Specimens:
Dhana-yoga-in-H9 → derived-11th amplifier fires; ŚaŚa-in-H7 → derived-10th fires.
Coordination: B-3 and B-4 both add MSR emitters — each owns its OWN new emitter module; the
signal-class registry is append-only (no shared-file edits).

### Lane B-5 — Small L1 completions (Python)
Karakamsha fact (CR-17: AK's D9 sign — data exists, one derivation); shadbala `required_rupa` +
ratio per graha (CR-18, BPHS minimums); D2 hora-class per graha (CR-58: surya_hora/chandra_hora +
D2-house join — "both wealth lords in Chandra-hora H12" must be one call); ph_nimitta anchor dedup
at the writer (CR-46: `anchor_count` post-dedup).

### Lane B-6 — Serving hygiene (TypeScript; single owner of the retrieval registry)
Positions default ordering — nine grahas + lagna lead, upagrahas behind a facet (CR-50); budgets
for `bodha_domain_reading_get`, `ephemeris_cache_year` (date-range/pagination), `ganita_tajaka_get`
default limit (CR-13/49); `ref_remedies_search` honor-or-reject (CR-42 residue);
`ganita_structural_get` §N.6 retrofit (layered envelope + density contract); **B9 dosha gate:**
`ganita_yogas_get` default page serves zero shared-stub `dosha_label` rows (catalog behind
`all=true`, mirroring the firings face); per-varga kāla-sarpa verdict (natal + divisional map)
gets a served surface.

### Lane B-7 — Governance + derived view
§N.6 Serving Density Principle text landed in CLAUDE.md §N.6 + ONGOING_HYGIENE (the anchor the
code already cites — CLAUDE.md version bump per B.8); CI density/census harness wired into the
pipeline; **B8** `dasha_lord_capability` derived view (per-MD: lord, house class, shadbala
percentile, functional lordship, ratification, warning tier) + serving facet.

**Merge order:** B-5 → B-2 → B-1 → B-3 → B-4 → B-6 → B-7 (fact writers before their consumers;
serving last). Single rebuild after all merges, then the gate.

## FROZEN §F2 — must_not_touch
FROZEN orchestrator contract (PARK class) · whole-sign `house_d1` semantics (DR-2: chalit is
ADDITIVE) · D-2+ scope (vidhi, CGM/mechanism, convergence, calibration) · CR-23 · the bindu values
themselves (re-key only) · valence engine (A-α owns it; frozen FOR THIS WAVE — D-2 Lane V-6
extends it under Adjudicator-doctrine).

## §B — BIND-AT-OPEN slots
- B-1: re-confirm spike bindings on `main` HEAD (drik/charts function signatures; the two fake-cusp
  emitter sites; adapter path); pick sandhi orb default (3°) unless Adjudicator-doctrine rules otherwise.
- B-2: confirm PyJHora exposes bhāva-bala (probe `jhora.horoscope.chart.strength` or equivalent);
  else PARK that sub-item per B.10.
- B-3/B-4: bind salience constants/class priors for the three new signal classes against the
  post-Gate-A MSR distribution (Adjudicator-doctrine sets them; recorded as a DR-n).
- Global: rollback pin; re-run Gate-A battery green before spawning (regression baseline).

## §G — Gate: execution plan §4 Gate B, verbatim, as harness scripts (extended from Lane A-0's
harness), on the deployed connector post-rebuild of Abhisek's chart (FULL L1→L5 — this wave adds
new chalit/AV fact categories that feed MSR + L3, so §8.2 trigger (a) applies; Binder records
`full: true`). Abhinandan not rebuilt.
