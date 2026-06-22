---
artifact: CLAUDECODE_BRIEF_L4_PH_MUHURTA_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L4_PH_MUHURTA
brief_for: ph_muhurta — Auspicious Windows (personalized, prediction-fused muhūrta) [maximal capacity]
status: FINALIZED — built on prod-verified state (GATE A) + D39 elevations; ready for the autonomous swarm
version: 1.0
authored_by: Cowork 2026-06-21
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
supersedes: CLAUDECODE_BRIEF_L4_PH_MUHURTA_v1_0.md (the 6-asset draft)
decisions_ref: L4_PHALA_DECISIONS_LEDGER_v1_0.md (D10 reuse, D39 elevations, D11 subsystem)
swarm_coordination:
  wave: W3 (parallel-safe with ph_pratikara; both after ph_nimitta spine)
  blocked_by: [ph_nimitta]   # M3 fuses muhūrta to ph_nimitta windows
  blocks: [ph_phaladesa]
  may_touch:
    - platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py
    - platform/python-sidecar/services/ph_muhurta/**
    - platform/supabase/migrations/331_phala_muhurta.sql
    - platform/scripts/seed/asset_registry_seed.ts
    - platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json
  parallel_safe_with: [ph_pratikara]
  hard_internal_gate: none
---

# CLAUDECODE BRIEF — ph_muhurta (Auspicious Windows) [maximal capacity]

> **What it is, in one line:** ph_muhurta answers "when should I do X?" — but not as a calendar
> calculator. It REUSES the already-deep `ka_muhurta_seva` / `panchang_engine` (per-event
> Muhūrta-Chintāmaṇi rule tables, Panchaka, Homa windows) and adds the four things only a chart-aware
> acharya does: personalizes to the native's chart strength + live transits, avoids the native's OWN
> danger windows, finds the best moment WITHIN a predicted opportunity window, and tells the truth when
> no good window exists.

## §0 — REUSE, don't rebuild (D10 / D39)
**Code-verified (2026-06-21):** the muhūrta engine is classically deep already —
`ka_muhurta_seva.score(date, location, event, native_chart)` + `find_windows(event, window, location,
top_n)`; `panchang_engine` computes Panchaka, Anandadi yoga, Vasa, Homa windows; `shastra_tables.py`
holds per-event quality tables with real Muhūrta-Chintāmaṇi citations (e.g. VIVAH §22.1: per-tithi/
nakshatra/vara scores + explicit AVOID flags). Live Tāra Bala (native nakshatra=25). **ph_muhurta CALLS
this engine; it does NOT reimplement panchāṅga or the classical tables.** The asset adds the
native-chart + prediction connection the engine lacks.

## §1 — The 4 ELEVATIONS (D39 — what makes it supreme)

### M1 — Personalize to chart strength + live transits
Beyond the day's panchāṅga, score whether the planet RELEVANT to the action is (a) strong/well-placed
in the native's chart (`ga_condition_composite.condition_score` for that graha) AND (b) transiting
favorably now (`ka_gochara` — is it aspecting/transiting a supportive point?). A `start_business`
muhūrta weights the native's 10th-lord condition + transit; a `marriage` muhūrta weights Venus/7th-lord;
a `medical` muhūrta weights the 6th/8th and the Moon's relation to the afflicted body-part nakshatra.
Store `chart_personalization_score` + which graha it keyed on. **This is the #1 thing a calculator can't do.**

### M2 — Avoid the native's PERSONAL danger windows
Demote any candidate window that overlaps the native's OWN adversity: `ka_vighnakara` obstruction
windows, active Sade-Sati phases (`ga_sade_sati`), or a malefic dāśā/antardaśā for the relevant graha.
A date that's universally fine (clean rahu-kalam/panchāṅga) but lands in YOUR obstruction window is a
bad pick for you. Store `personal_adversity_penalty` + the overlapping obstruction id.

### M3 — Fuse muhūrta to the PREDICTION (the supreme move)
When `ph_nimitta` predicts a favorable window in a domain (e.g. career elevation, 2027), ph_muhurta
finds the BEST MOMENT WITHIN that predicted window for the matching action — the muhūrta rides the
prediction. Output: "your career opportunity window is 2027-Q2; the optimal launch muhūrta within it is
[date], [hora], quality 0.86." Store `linked_anchor_id` (the ph_nimitta anchor) when the muhūrta is
prediction-fused. This fuses the prediction layer with the timing layer — no app does this.

### M4 — Honest "no good window" reporting
When no genuinely auspicious window exists in the requested timeframe, SAY SO — return a
`window_quality_verdict ∈ {strong, adequate, mediocre, none_genuine}` and, for mediocre/none, a plain
reason ("the best available scores 0.42; the Moon is afflicted and no fixed nakshatra falls in range").
Do NOT always return a top-10 that implies false quality. Calibrated honesty (mirrors the D5 discipline).

## §2 — Event coverage (D39: expose existing + add native-relevant)
Expose the engine's existing event rule-tables (vivah, griha_pravesh, …) AND ensure coverage of the
events THIS native is most likely to need: **career/business launch, travel/relocation, contract/
signing, medical/surgery, ceremony, spiritual initiation (sādhana), new-venture, vehicle/property
purchase.** For any native-relevant event the engine lacks a rule-table for, add a purpose-specific
rule set (citing the classical source) — do NOT reuse a generic score (purpose-specific avoidances
matter: surgery avoids the body-part nakshatra; travel checks disha-shśūla directional clearance).

## §3 — Schema (migration 331)
`phala_muhurta`:
```
muhurta_id              uuid PK
chart_id                uuid NOT NULL
action_class            text NOT NULL          -- the event class
window_start            timestamptz
window_end              timestamptz
hora_lord               text                   -- the hora at the window
panchanga_score         double precision       -- from the engine
chart_personalization_score double precision   -- M1
personalization_graha   text                   -- M1 (which graha it keyed on)
personal_adversity_penalty  double precision   -- M2
overlapping_obstruction_id  bigint             -- M2 (ka_vighnakara ref, nullable)
linked_anchor_id        uuid REFERENCES phala_anchors(anchor_id)   -- M3 (prediction-fused, nullable)
composite_quality       double precision CHECK (composite_quality >= 0 AND composite_quality <= 1)
window_quality_verdict  text CHECK (window_quality_verdict IN ('strong','adequate','mediocre','none_genuine'))  -- M4
verdict_reason          text                   -- M4 (for mediocre/none)
panchanga_snapshot_jsonb jsonb                 -- tithi/vara/nakshatra/yoga/karana/panchaka/homa from the engine
classical_citation      text                   -- the MC/event-table source
derivation_ledger_jsonb jsonb NOT NULL
source_citation         text NOT NULL
computed_at             timestamptz NOT NULL DEFAULT now()
UNIQUE (chart_id, action_class, window_start)
```

## §4 — Engine spec (`services/ph_muhurta/engine.py`)
1. For a requested `action_class` + timeframe (or a `linked_anchor_id` window for M3): call
   `ka_muhurta_seva.find_windows(event, window, location, native_chart)` → candidate windows + panchāṅga.
2. M1: for each candidate, score the relevant graha's `condition_score` + its live transit (`ka_gochara`).
3. M2: penalize candidates overlapping `ka_vighnakara` / Sade-Sati / malefic-dāśā for the graha.
4. `composite_quality` = engine panchāṅga × M1 personalization × (1 − M2 penalty); rank.
5. M4: classify the verdict; if best < a documented "genuine" threshold → `mediocre`/`none_genuine` + reason.
6. Anti-drift: cite the engine call params + the chart/obstruction/anchor ids; write ONLY `phala_muhurta`.

## §5 — Acceptance criteria [tagged; prod-verified]
1. `[pytest]` panchāṅga + classical tables come from `ka_muhurta_seva`/`panchang_engine` (NOT reimplemented — grep ph_muhurta for any panchāṅga math → ZERO; it calls the service).
2. `[pytest — M1]` the relevant-graha personalization score uses real `ga_condition_composite` + `ka_gochara`; a `start_business` window keys on the 10th-lord, `marriage` on Venus/7th-lord.
3. `[pytest — M2]` a candidate overlapping a real `ka_vighnakara` window is demoted vs an otherwise-equal clean candidate; the obstruction id is recorded.
4. `[pytest — M3]` given a `linked_anchor_id`, ph_muhurta searches WITHIN that anchor's window and links back.
5. `[pytest — M4]` when all candidates score below the genuine threshold, the verdict is `mediocre`/`none_genuine` with a reason — NOT a false top-10.
6. `[pytest]` native-relevant events covered; purpose-specific rule sets (surgery avoids body-part nakshatra; travel checks disha-shśūla) cite classical sources.
7. `[anti-drift]` writes only phala_muhurta; zero `.commit()/.rollback()`; ledgers resolve; `WriterResult(asset_id='ph_muhurta', rows_inserted=N)`.
8. `[psql_prod + curl_prod]` phala_muhurta lit; cockpit shows ph_muhurta; idempotent; FORENSIC 7/7.

## §6 — Embedded commands
```bash
git checkout main && git pull && git checkout -b feature/l4-ph-muhurta
# the engine to reuse (do NOT reimplement)
sed -n '60,170p' platform/python-sidecar/services/ka_muhurta_seva/service.py
sed -n '620,690p' platform/python-sidecar/panchang_engine/shastra_tables.py   # the classical event tables
# personalization sources
psql "$DATABASE_URL" -c "SELECT graha, condition_score FROM ga_condition_composite WHERE chart_id=:'NATIVE';"
cd platform/python-sidecar && pytest -q services/ph_muhurta -k "muhurta or personalize or adversity or fused or verdict"
```

## §7 — Definition of done
- [ ] Migration 331: phala_muhurta created.
- [ ] Reuses ka_muhurta_seva/panchang_engine (no panchāṅga reimplementation).
- [ ] M1 personalization + M2 personal-adversity + M3 prediction-fusion + M4 honest-verdict all implemented + tested.
- [ ] Native-relevant events covered with purpose-specific cited rule sets.
- [ ] Anti-drift clean; registered/idempotent/FORENSIC-clean; cockpit lit; PR opened.

## §8 — VALUE ADDED BY THIS BRIEF
1. **Turns a muhūrta calculator into a personal, prediction-aware muhūrta acharya** — the four
   elevations (chart-strength + transit personalization, personal-danger avoidance, prediction fusion,
   honest verdict) are precisely what a chart-aware master does and an app cannot.
2. **Reuses the deep classical engine** (per-event MC rule tables, Panchaka, Homa) instead of rebuilding —
   D10 reuse rule; the asset adds the native connection the engine lacks.
3. **M3 fuses the prediction + timing layers** — "your opportunity window is X; the optimal moment
   within it is Y" — a capability unique to having both layers in one instrument.
4. **M4 keeps it honest** — no false top-10 when no genuine window exists (the calibration discipline applied to muhūrta).

## §9 — REVIEW NOTES (all RESOLVED 2026-06-21 — brief CLOSED)
- **R1 [RESOLVED — Cowork default locked]:** the M4 "genuine window" threshold = **0.55** composite
  quality. Best candidate ≥0.55 → `strong`/`adequate`; <0.55 → `mediocre`; no candidate clears a
  documented floor → `none_genuine` + reason.
- **R2 [RESOLVED — Cowork default locked]:** the relevant-graha mapping per action_class = the **shared
  significator mapping** (same reference U1 + ph_nimitta Axis 1 use; career→10th-lord, marriage→Venus/
  7th-lord, medical→6th/8th + Moon-vs-body-part-nakshatra, travel→3rd/9th, signing→Mercury/2nd, etc.).
  One shared reference, not redefined here.
- **R3 [RESOLVED — Cowork default locked]:** muhūrta location = the native's **current residence**
  (the engine requires an explicit location; no Bhubaneswar birth-place default — muhūrta is computed
  where the native will ACT, not where they were born).

---
*End of CLAUDECODE_BRIEF_L4_PH_MUHURTA v1.0 — CLOSED. Auspicious windows at maximal capacity: reuse the
deep classical engine + personalization, personal-danger avoidance, prediction-fusion, honest verdict.
R1–R3 resolved.*
