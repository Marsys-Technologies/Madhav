# Lane 2 — Evidence-Sufficiency Shard 2-b1 (Groups A5, A6, B1, B2)

Charter: `LLM_CONSUMPTION_AUDIT_CHARTER` §7.3 (4-point scale), §4 (9-class taxonomy), §2 (doctrine width/depth).
Mode: P-12 evidence-plan-then-acquire, via DEPLOYED MCP connector (read-only, doctrinal public channel).
Charts: C1 = `482012f1-710e-4a25-994a-93821f5871aa` (native, Abhisek) · C2 = `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan).
Rows: 16 (A5/A6/B1/B2 × narrow/broad × C1/C2). Status: COMPLETE.

---

## Evidence plans (deliverable)

**A5 — accident/injury propensity + windows.** Acharya needs: (1) Mars dossier (weapons/cuts/fire/accidents kāraka; for Aries lagna Mars = lagnesa + 8th lord); (2) 6th (injury/roga) + 8th (sudden events/surgery/mrityu) bhava judgment; (3) mrityu-bhāga / arishta-yoga membership; (4) malefic transits + dasha windows over the horizon; (5) calibrated predictive anchors typed to accident/health-crisis. Order: assess_health → get_domain_reading(health) → get_signals(health) → graha_portrait(Mars) → judgment_query(bhava=8) → get_temporal_windows → get_projections(health) → phala_outlook → vector_search("accident injury"). Tools that would carry the answer: graha_portrait, judgment_query, get_temporal_windows/get_projections/phala_outlook for windows.

**A6 — recovery capacity.** Acharya needs: ojas/vitality read from Lagna-lord + Sun + Moon strength/avastha; Jupiter (protection/healing); 8th (chronicity/recuperation); overall bala. Order: assess_health → get_chart_quality → graha_portrait(Sun/Moon/Jupiter, strength+avastha) → get_signals(health). Carrier: graha_portrait strength/avastha facets + chart_quality.

**B1 — personality portrait.** Acharya needs: Lagna sign/lord, Moon (manas) sign+nakshatra+dignity, Sun (atma), Mercury (buddhi), dominant grahas, character-domain synthesis, holistic UCD. Order: get_chart_orientation → get_domain_reading(character) → graha_portrait(Moon, Lagna-lord) → judgment_query(domain=character/bhava=1). Carrier: orientation UCD + graha portraits + character reading.

**B2 — mental-health resilience/vulnerability windows.** Acharya needs: Moon (manas) affliction/support, 4th (emotional foundation/sukha/chitta), Mercury (nervous system), Moon–Saturn/Rahu/Ketu contacts, dasha/transit vulnerability windows. Order: get_domain_reading(health+character) → graha_portrait(Moon) → judgment_query(bhava=4) → get_signals(mental) → get_temporal_windows → get_projections. NOTE: no "mental-health" domain exists → forced decomposition.

---

## Acquisition trace (what came back)

| Tool | Chart | Result summary |
|---|---|---|
| assess_health | C1 | 129.6KB; text field = "budget-capped… text duplicate suppressed"; `judgment_flags:["response_still_over_40kb_budget_after_full_trim"]`; trim_report itself omitted "to fit budget". verdict_skeleton top-10 = `combustion_per_varga is_combust=False` for Sa/Ma/Ju/Me (summaries `[truncated for budget]`); `activating_dasha.activations=[]` count 0; `karaka_analysis`=CDLM cross-domain cells (NOT Sun-kāraka); `house_analysis`=lens metadata only (no 6th/8th body); contradictions status no_data. |
| get_domain_reading(health) | C1 | 2 lenses; `signal_id_refs_total=748` capped→200 bare UUIDs, no text; `verdict_skeleton=null`; lens `template_element_ids_jsonb=[]` (empty recipe), top signals `in_template:false`; token_safety_note "Bounded to 3 lenses × 20". |
| get_domain_reading(health) | C2 | parity: 752 refs capped, bare ids, verdict null. |
| get_domain_reading(character) | C1/C2 | 3 lenses; `signal_id_refs_total=7290 / 7283` bare ids; verdict null. Same UNUSABLE FORM. |
| get_signals(health) | C1/C2 | text resolves BUT top-K = 5× `combustion per varga is_combust=0` at identical 0.575 (score-wall); ranks ~12331-12335; `pagination.total=null`. |
| graha_portrait(Mars) | C1 | Full dossier ✓ position/dignity/functional_nature/strength/avasthas/yogas; grounding fact_ids present; trim original 12→1. USABLE depth. |
| graha_portrait(Moon) | C1 | Full dossier ✓ incl. dashas + cgm_neighborhood. USABLE depth. |
| judgment_query(bhava=4) | C1 | verdict domain=**"education / Learning"** (4th routed to education, not emotional/sukha); grade "mixed" score 0.9; flag `bhanga_not_checked: … requires data-plane addition not yet built`. |
| get_temporal_windows(2026-2029) | C1 | **activations=[] count 0, predicates 0**. EMPTY. |
| get_temporal_windows(2026-2029) | C2 | **activation_count 50, predicate_count 50**. NON-empty. → native-chart hole. |
| get_projections(health) | C1 | content.projections has a health window (peak 2027-10-20, tier_1_high) BUT top-level `projections_total=0 / projections_returned=0` contradict payload. |
| phala_outlook(36mo) | C1 | anchors `original_count 195 → kept 5 (hard-cap)`; recover_via instrument=**"unknown_tool"**; 5 served all career/transition, **zero health**. |
| vector_search("accident injury surgery") | C1 | returns classical-text citations (nadi_navamsa_patel) only — no chart-derived accident signal. |
| get_chart_orientation (in every envelope) | C1 | `top_signals:[]` empty; entity_profiles dominated by `UNATTRIBUTED` (299 signals); `msr_signal_count "13364"` (vs tool desc "573-signal corpus"). |

trim_seen = TRUE (assess_health over-budget-after-trim; graha_portrait trim 12→1, 13→1; domain readings capped; phala anchors 195→5; signals capped).

---

## Verdicts (see results[] for machine-readable)

- **A5 narrow (C1,C2):** INSUFFICIENT — accident/injury propensity is not computed at chart level (UNREACHABLE-BY-NONEXISTENCE: only classical-text chunks); accident-typed windows absent; C1 temporal windows empty.
- **A5 broad (C1,C2):** SUFFICIENT-WITH-GAPS — general health-vulnerability read composable from Mars/Moon dossiers + a generic health-activation window; accident-specificity + typed windows are the gap.
- **A6 narrow+broad (all):** SUFFICIENT-WITH-GAPS — recovery capacity hand-assembled from Lagna/Sun/Moon/Jupiter strength+avastha (graha_portrait); no synthesized vitality/recovery index, assess_health verdict drowned.
- **B1 narrow+broad (all):** SUFFICIENT-WITH-GAPS — portrait composable from graha portraits + Lagna/Moon + orientation header; but the two purpose-built surfaces (orientation `top_signals`, character domain reading) both fail (empty / bare-id).
- **B2 narrow (C1,C2):** INSUFFICIENT — no mental-health domain; resilience/vulnerability *windows* not retrievable (C1 temporal empty; no mental-typed activation on either chart); Moon portrait alone can't give calibrated windows.
- **B2 broad (C1,C2):** SUFFICIENT-WITH-GAPS — broad mental-resilience read from Moon+4th+Mercury; windows remain the gap.

## Class-9 UNGOVERNED-JUDGMENT log
1. B2: no "mental-health" domain → silent decomposition to health+character+Moon+4th.
2. Windows rerouting: get_temporal_windows empty (C1) → executor must know to fall back to get_projections/phala_outlook (undocumented routing).
3. judgment_query bhava=4 labelled "Education" → executor overrides taxonomy to read 4th as emotional foundation for B2 (taxonomy→life-language).
4. A5: no accident model → executor assembles propensity from Mars(=lagnesa+8L) + 6/8 + classical citation (method choice + conflict adjudication).
5. Ranking adjudication: executor discards combustion=False identical-score walls and picks from 748/7290 bare signal_ids which matter — system provided no usable ranking.
6. get_projections top-level count 0 vs populated content → executor adjudicates which to trust.
