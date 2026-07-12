# Lane 2 shard-2-b20 — L5 (remedial stack) + L6 (unprompted warnings) × 2 charts × {narrow,broad}

Worker: Lane 2 evidence-sufficiency (P-12 plan-then-acquire). Charter §7.3 4-point scale.
Channel: DEPLOYED MCP connector (read-only). Charts: 482012f1 (native Abhisek), 1c826d5a (Abhinandan).
Grading rubric: SUFFICIENT / SUFFICIENT-WITH-GAPS / INSUFFICIENT / UNANSWERABLE-BY-DESIGN.

---

## Evidence plan — L5 "whole-chart remedial stack"

An acharya building a whole-chart remedial stack needs, in order:
1. The chart's afflictions enumerated by name + severity (the 22 doshas, afflicted karakas, weak grahas) — the *targets*.
2. Per-target remedy prescriptions (mantra / gemstone / charity / ritual) with classical citation + feasibility.
3. A PRIORITIZATION that maps each remedy to the affliction it addresses and orders by severity.
4. A TEMPORAL sequencing (which remedy in which dasha/antardasha; sade-sati overlay).
5. Cost / complexity / acharya-review gating so the stack is actionable.
Tools: get_remedies / bodha_remedies_get (targets+prescriptions), get_dashas / kala_yoga_activation (sequencing), ganita_sade_sati_get (overlay), mitigation_map / phala_mitigation_get (dosha→mitigation), get_signals class=dosha (affliction enumeration).

## Evidence plan — L6 "unprompted acharya warnings"

An acharya volunteering warnings needs a PROACTIVE severity-ranked hazard surface:
1. Highest-severity doshas/afflictions enumerated with life-domain (health/marriage/finance) tags.
2. Danger windows in the near horizon (malefic dasha/antardasha, sade-sati active phase, ashtama/kantaka shani, transit hits).
3. Karaka-level red flags (afflicted lagna lord, 8th/6th/12th activations).
4. A routing that accepts an OPEN "what should I be warned about" question and returns the top hazards unprompted.
Tools: get_temporal_windows (danger windows), ganita_sade_sati_get (active shani phase), get_signals valence=malefic / class=dosha, get_chart_quality, judgment_query (open question), mitigation_map.

---

## Acquisition trace (tools_called + returns)

### get_remedies / bodha_remedies_get (both charts)
- 482012f1: 9 resonances, 27 prescriptions. resonance_ranked #1 Mercury 0.4069 → #9 Sun 0.376 — ALL "medium" priority, spread 0.376–0.407 (identical-score WALL). Prescriptions are real, human-readable, cited (e.g. "Chant Aditya Hridayam 108× at sunrise… BPHS Ch.88", feasibility 0.9, complexity simple, cost_tier "free/low (category-derived estimate)").
- 1c826d5a: 9 resonances (#1 Saturn 0.434 → wall), 27 prescriptions, same shape.
- **narration.data_gap_note (BOTH charts, verbatim):** "associated_doshas_array (formal named-dosha tagging on resonances) and estimated_cost_inr_range_jsonb (exact INR cost on prescriptions) are 100% NULL for every chart built so far… Named-affliction mapping… derived instead from graha + remedy_priority_class + weakest_rank_in_chart… cost is a qualitative tier… not a computed INR figure." → HONEST disclosure of a DATA-PLANE gap: remedies are NOT linked to the 22 doshas they would remediate.

### mitigation_map / phala_mitigation_get (both charts)
- mitigation_map: `mitigations: [], total_count: 0, all_cited: true` on BOTH charts. EMPTY SHELL — phala.mitigation asset (PH-4-2) serves nothing. The one tool that would bridge dosha→mitigation is empty.

### get_temporal_windows (both charts)
- `activation_count: 0, predicate_count: 0, signal_id_refs: []` for horizon 2026-07-12→2027-07-12 on BOTH charts. No danger/opportunity windows served for the coming year. kala_activation empty on first contact.

### ganita_sade_sati_get (both charts)
- 78 raw fact rows on BOTH (categories: sade_sati_cycle/phase/phase_quarter, ashtama_shani_period, kantaka_shani_period, dhaiya_period, janma_shani_period…). Rows are RAW numeric facts only (fact_key=duration_days, fact_value_num=795.32 days) — NO current-phase flag, NO "active now" boolean, NO rendered start/end dates. Consumer must compute which shani period is live TODAY. pagination `{offset:0, limit:0, total:null}` — count not disclosed.

### get_signals (both charts)
- Text channel suppressed: "[large payload — see structuredContent; text duplicate suppressed per S3 serialization-tax fix]". structuredContent = orientation digest: digest{dosha_count:22, yoga_count:15, top_priority_class:"medium"} but `top_signals: []` EMPTY; only entity_profiles=[UNATTRIBUTED (299 signals), KETU (1)]. The 22 doshas are COUNTED, never enumerated here.
- bodha_signals_get(signal_class="dosha") **ignored the filter** — returned graha_dignity_per_varga composite_state signals (D108 dignity=neutral), salience 2.99, top_k_rank 1, signature_tier "chart_defining". A D108 (shashtyamsha) neutral-dignity restatement ranked #1 chart-defining = descriptive trivia promoted to chart-defining tier (R-37/R-44 pattern); AND filter did not select doshas.

### get_chart_quality (482012f1)
- Returns a BUILD scorecard (msr_signal_count 66836, two_pass_verified 89.59%) + `defect_001_alert{severity:"HIGH", ...constituent_facts orphan}` — a SOFTWARE defect alert, not an astrological chart-quality/warning. Note msr_signal_count here = 66836 vs orientation digest msr_signal_count = 13364 (INCONSISTENT).

### judgment_query (482012f1)
- Open question "What should I be warned about in this chart?" → `{ok:false, error: either domain or bhava is required}`. The natural open warning question is UN-ROUTABLE.

---

## Verdicts

| code | chart | variant | verdict |
|---|---|---|---|
| L5 | 482012f1 | narrow | SUFFICIENT-WITH-GAPS |
| L5 | 1c826d5a | narrow | SUFFICIENT-WITH-GAPS |
| L5 | 482012f1 | broad  | SUFFICIENT-WITH-GAPS |
| L5 | 1c826d5a | broad  | SUFFICIENT-WITH-GAPS |
| L6 | 482012f1 | narrow | INSUFFICIENT |
| L6 | 1c826d5a | narrow | INSUFFICIENT |
| L6 | 482012f1 | broad  | INSUFFICIENT |
| L6 | 1c826d5a | broad  | INSUFFICIENT |

**L5 rationale:** a usable remedy LIST is composable (27 cited prescriptions per graha) → not INSUFFICIENT. But the "STACK" (prioritized + affliction-mapped + dasha-sequenced) is NOT: (a) resonance scores are an identical-score wall, all "medium" → no real priority order; (b) associated_doshas_array 100% NULL → cannot map remedies to the 22 doshas; (c) mitigation_map EMPTY; (d) no temporal sequencing (windows empty). Broad variant leans harder on the missing integration but the prescription list keeps it above INSUFFICIENT. → SUFFICIENT-WITH-GAPS both variants, both charts.

**L6 rationale:** NO proactive-warning surface exists anywhere. Danger windows EMPTY, mitigation EMPTY, doshas only counted (enumeration filter broken), sade-sati raw with no active-now flag, open question un-routable, chart_quality returns a software defect not a hazard. To answer I would have to fully improvise: define what counts as a warning, pick surfaces, compute the live shani phase myself, and guess the identities/severities of the 22 doshas. That is fabrication/guess territory at acharya grade. → INSUFFICIENT both variants, both charts. (Not UNANSWERABLE-BY-DESIGN: the underlying data — doshas, shani periods — EXISTS; it is unreachable/ungoverned in warning form, i.e. a retrieval+doctrine gap, not out of scope.)

## Class-9 UNGOVERNED-JUDGMENT improvisations logged
- **L5:** had to CHOOSE remedy priority order (resonance wall gives none) and had to GUESS which of 22 doshas each of 27 prescriptions addresses (associated_doshas NULL) — method choice + silent affliction-mapping.
- **L5:** had to invent the dasha-sequencing of the stack (no tool sequences remedies over dashas).
- **L6:** had to DEFINE "warning" (taxonomy→life-language translation), SELECT hazard surfaces (no system list), COMPUTE the currently-active sade-sati phase from raw duration_days, and DECOMPOSE the open question into per-domain judgment_query calls (open routing rejected).

## trim_seen
- false for data-loss trimming, BUT receipt-honesty notes captured: get_signals suppresses the text channel ("S3 serialization-tax fix" — disclosed, benign); ganita_sade_sati_get pagination `total:null, limit:0` (count NOT disclosed — mild dishonest-receipt); get_signals top_signals ALWAYS [] while dosha_count=22 (drowned/empty list surface).
