# Lane 2 Evidence-Sufficiency — Shard 2-b7 (Group E. Dhana & Sampatti: E3–E6)

Worker: P-12 evidence-plan-then-acquire, deployed MCP connector (read-only).
Charter: CHARTER.md §7.3 (4-point scale). Charts: `482012f1…` (Abhisek/native = C1), `1c826d5a…` (Abhinandan = C2).
Questions: E3 windfall/speculation, E4 debt cycles, E5 property/vehicle timing, E6 inheritance — each ×{narrow,broad}×2 charts = 16.

## Evidence plans (per question class)

- **E3 windfall/speculation** — an acharya wants: 5th bhava (poorva-punya/speculation) + its lord,
  11th (labha/gains), 8th (sudden/unearned), Rahu (gambling), dhana-yogas, then dasha/transit timing
  of those. Order: judgment_query(bhava 5,11,8) → wealth signals/yogas → get_dashas +
  yoga_activation_by_dasha for timing.
- **E4 debt cycles** — 6th bhava (rina) + lord, malefics in 2/6/12, Mars/Saturn as debt karakas,
  then the temporal recurrence ("cycles") via dasha/activation windows. Order: judgment_query(bhava 6)
  → get_dashas → get_temporal_windows / yoga_activation_by_dasha.
- **E5 property/vehicle timing** — 4th bhava (bhoomi/vahana/sukha) + lord, karaka Mars(property)/
  Venus(vehicle)/Moon, vargas D4(property)/D16(vehicle), then explicit timing windows. Order:
  judgment_query(bhava 4) → get_temporal_windows → get_dashas → phala_outlook(wealth).
- **E6 inheritance** — 8th bhava (legacy/other's wealth) + lord, 2/11 (received wealth), parental
  houses (4th mother/9th+Sun father), karaka, then timing of parent-dasha. Order:
  judgment_query(bhava 8,2) → cross-house synthesis → get_dashas.

## Evidence acquisition — tools called (both charts, parity confirmed)

`apex_wealth_assess`/`assess_wealth`, `get_domain_reading(domain=wealth)`, `get_signals(domain=wealth)`,
`judgment_query(bhava=2,4,5,6,8,11)`, `get_temporal_windows`, `phala_outlook(domain=wealth,horizon 60)`,
`get_dashas`, `yoga_activation_by_dasha`.

### Structural findings that gate every E3–E6 verdict

1. **Bhava→domain taxonomy is sparse and mis-mapped for wealth sub-topics.** `judgment_query`
   hard-maps each bhava to at most ONE life-domain:
   - bhava 2 → "Wealth / Prosperity" (karaka Jupiter, varga D2, yogas_checked 8[C1]/9[C2]) — the ONLY wealth-mapped house.
   - bhava 4 → **"Education / Learning"** (karaka Mercury/Jupiter, varga D24) on BOTH charts. The 4th's
     property/vehicle/bhoomi/vahana signification is ABSENT — the one house E5 needs is served as
     education, with education karakas and education varga (not D4/D16).
   - bhava 5 → "Progeny / Children" (karaka Jupiter, varga D7). The 5th's speculation/poorva-punya (E3) absent.
   - bhava 6 → null domain / "Bhava 6", **no karaka**, generic D1 checklist. Debt/rina (E4) unmapped.
   - bhava 8 → null domain / "Bhava 8", **no karaka**, generic D1 checklist. Inheritance (E6) unmapped.
   - bhava 11 → null domain / "Bhava 11", no karaka. Gains/labha (windfall) unmapped.
   → class 9 (taxonomy→life-language) + class 1 UNREACHABLE-BY-NONEXISTENCE for windfall/debt/
   property/vehicle/inheritance karakas & concepts.

2. **The bhava checklist DOES yield genuine structural evidence** usable for any house meaning:
   bhava sign (from lagna + chandra), bhavesha placement/house/sign/dignity/shadbala_rupa/fact_ids,
   karaka condition, varga confirmation, timing_anchored=true, grounding fact_ids. An acharya can read
   raw 6th/8th/4th/5th structure — but must supply topic mapping + karakas himself (class 9).

3. **`receipt.yogas_checked = 0` for bhavas 4,5,6,8,11** — the deterministic verdict skips yoga
   membership for every wealth-sub-topic house (only bhava 2 checks yogas). `bhanga_checked=false`
   everywhere; `judgment_flags` honestly declares bhanga a not-yet-built data-plane addition (§12 D3).

4. **All semantic TIMING surfaces are EMPTY (R-45 kala_activation anchor rediscovered).**
   - `get_temporal_windows`: `activation_count 0, predicate_count 0, activations [], predicates []` on
     BOTH charts; domain filter ignored (echoes `domain:null`).
   - `yoga_activation_by_dasha`: `activated_yogas [], total_count 0` on both charts.
   - `phala_outlook(domain=wealth, 60mo)`: returns only `career`/`transition` discovery-event anchors,
     ZERO wealth anchors; every anchor shares the identical window 2026-07-11→2026-10-09 (identical-window
     wall). domain=wealth filter ineffective.
   Only `get_dashas` returns real timing (vimshottari timeline w/ lord natal house/sign/nakshatra) — but
   topic-agnostic raw substrate; mapping lords→windfall/debt/property/inheritance is un-governed (class 9).
   E4 "cycles" and E5 "timing" are explicitly temporal ⇒ hardest hit (class 4 EMPTY SHELL).

5. **`apex_wealth_assess` top-10 is an identical-score wall** — top_10_composite all composite_score=1.0465,
   all `signal_type_class=yoga`, generic pan-chart yogas (Yuga/Anapha/Kedara/Sasa/Vasi/Gola…) not specific
   to any wealth sub-topic. `get_signals`/`get_domain_reading(domain=wealth)` return the whole-chart
   orientation digest with `top_signals: []` (empty) and a 299-signal **UNATTRIBUTED** entity (R-44 anchor
   rediscovered). domain arg inert (bad-arg probe → identical digest).

6. **trim_seen = TRUE.** `judgment_query.trim_report` = `[{original_count:3, kept_count:1, reason:"full
   trim_report omitted to fit budget"}]`; `apex_wealth_assess` text = "budget-capped response — see
   structuredContent"; `get_signals` text = "text duplicate suppressed per S3 serialization-tax fix";
   `phala_outlook` carries a trim_report. Payloads budget-trimmed across the board.

### narrow vs broad rule applied
- **narrow** = the pointed sub-event → needs the specific concept + karaka + timing → hits unmapped-concept +
  empty-timing walls ⇒ **INSUFFICIENT** (all 8 narrow rows).
- **broad** = the sub-topic within an overall wealth reading → generic bhava-2 wealth verdict + raw house
  structure composable, but the specific facet + timing gapped/honestly flagged ⇒ **SUFFICIENT-WITH-GAPS**
  (all 8 broad rows).

Both charts behave identically (verified apex_wealth, bhava 2/4/6/8, temporal_windows, yoga_activation on
C2) ⇒ grades carry across charts. No question is UNANSWERABLE-BY-DESIGN — wealth IS a declared domain;
these sub-topics are within scope but under-modeled (retrieval + data-plane gaps, not scope exclusions).

## Class-9 UNGOVERNED-JUDGMENT improvisations logged (would occur on every consumption)
- Silent decomposition: "windfall/speculation"→bhavas 5+11+8+Rahu; "debt"→6th; "property/vehicle"→4th;
  "inheritance"→8th+2+parental — no tool performs this mapping.
- Taxonomy→life-language re-read: 5th served as "progeny" but re-read as speculation; 4th served as
  "education" but re-read as property/vehicle; 6th/8th unlabeled, topic assigned by executor.
- Method/krama choice: which houses+karakas constitute each topic (no governed krama); choosing raw
  get_dashas over the empty semantic-timing surfaces to attempt any timing at all.
