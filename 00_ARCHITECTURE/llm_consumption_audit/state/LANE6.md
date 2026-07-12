# LANE6 — Per-surface §7.4 raw metrics, UNATTRIBUTED shares, R-44a re-derivation, DROWNED surfaces (L2)

```
resume:
  lane_id: LANE6
  lane_number: 6
  layer: L2 (composite/domain surfaces, native chart C1 + control C2)
  surfaces_audited: apex_health/assess_health, get_signals, get_domain_reading,
                    get_chart_orientation, get_projections, karaka_analysis
  headline_failure_classes: 7 (DROWNED), 5 (mislabel/dishonest self-desc), 6 (bare-id no-synthesis)
  R-44a: RE-DERIVED (UNATTRIBUTED drowning, independent rediscovery)
  status: DONE
  checkpoint_ts: 2026-07-12 (native chart audit session)
```

## Scope

Lane 6 audits the L2 composite/domain surfaces for §7.4 payload fidelity: **of what the
surface returns, how much is decision-bearing versus drowned noise, attributed versus
UNATTRIBUTED, and does the payload describe itself honestly?** It re-derives the R-44
(UNATTRIBUTED-signal drowning) anchor as R-44a and enumerates the DROWNED surfaces.

## Per-surface §7.4 raw metrics

| surface | returned | of-total | decision-bearing | self-description | class |
|---|---|---|---|---|---|
| `assess_health` / `apex_health` top_10 | 10 | — | ~0 (5× combustion is_combust=False + 5× identical-score yogas) | by_stage all empty | 7 |
| `get_signals(health)` top-K | K | total=**null** | ~0 before first yoga | pagination.total None | 7 |
| `get_domain_reading(health)` | 752 signal_id_refs | capped | 0 (bare UUIDs, no text) | verdict_skeleton=null | 6 |
| `get_domain_reading(character)` | 7290 → 200 refs | capped | 0 (bare UUIDs) | verdict null, template=[] | 6 |
| `get_chart_orientation` | top_signals=**[]** | — | 0 | msr_signal_count '13364' | 4 |
| `get_projections(health)` | content.projections populated | — | 1 health window | projections_total=**0** | 5 |
| `karaka_analysis` | CDLM cross-domain cells | — | 0 (wrong object) | mislabeled | 5 |
| `phala_outlook` | 5 anchors | of **195** | 0 health (3 career/2 transition) | recover_via='unknown_tool' | 5 |

## UNATTRIBUTED shares (R-44a re-derivation)

The UNATTRIBUTED-signal drowning anchor (R-44) is **independently re-derived here as R-44a**
on the L2 domain/orientation surfaces:

- **`get_domain_reading(health)`** — entity_profiles = **UNATTRIBUTED(299)** + KETU(1);
  top_signals:[]. 299 signals carry no graha/bhava attribution and drown the 1 attributed
  entity. No system decomposition possible.
- **`get_chart_orientation`** ("mandatory holistic portrait") — entity 'UNATTRIBUTED'
  signal_count **299**, aggregate_score 64.5, and top_signals=**[]**. The portrait digest
  is dominated by the unattributed bucket; nothing decision-bearing surfaces.
- **`get_domain_reading(character)`** — signal_id_refs_total **7290** (C1) / **7283** (C2),
  capped to 200 **bare UUIDs**, verdict_skeleton=null, template_element_ids_jsonb=[]. The
  flagship character synthesis is un-synthesizable as received.

R-44a conclusion: on L2, attribution collapse and budget-capping combine so that the
*named-holistic* surfaces (orientation, character reading) return either empty top_signals
or an undifferentiated UNATTRIBUTED mass — the exact drowning R-44 first flagged, now
confirmed one layer up.

## DROWNED surfaces (class 7 — decisive rows discarded / walled)

1. **[class 7 · HIGH] `apex_health` / `assess_health` top-10 DROWNED.** Top-10 = 5×
   `combustion_per_varga | is_combust=False` (non-events, irrelevant to vitality) + 5×
   identical-score yogas at **1.0465**; by_stage.{karaka,lord,strength,varga,temporal} all
   **empty**. Summaries '[truncated for budget]'. Real vitality signal drowned by a combustion
   score-wall.
2. **[class 7 · HIGH] `get_signals(health)` top-K DROWNED.** 5× 'combustion per varga
   is_combust=0/1' at an identical **0.575** score-wall before the first yoga (Gola, 0.489);
   **pagination.total = null** (no total-available disclosure — the consumer cannot even know
   how much was discarded).
3. **[class 7 · HIGH] Broad chronic-disease propensity buried under 299 UNATTRIBUTED.**
   `get_domain_reading` serves the aggregate health domain with 299 UNATTRIBUTED signals and
   top_signals:[]; no per-system roga decomposition survives the drown (feeds LANE7 taxonomy
   ceiling).

## Mislabel / dishonest self-description (class 5)

4. **[class 5 · MED] `karaka_analysis` MISLABELED** — returns CDLM cross-domain linkage cells,
   NOT a graha-karaka dossier. Evidence: `karaka_analysis.cdlm_cells=[{career×health
   shared_signal_count 748}...]`; no Sun/vitality-karaka body anywhere in the object. The
   surface named for karaka analysis delivers a different asset entirely.
5. **[class 5 · MED] `get_projections(health)` self-contradicts** — top-level
   projections_total=0 / projections_returned=0 while content.projections is populated
   (`[{peak_date 2027-10-20, tier_1_high, 'Health activation near 2027-10-20'}]`). A consumer
   trusting the count sees zero and drops a real window.
6. **[class 5 · HIGH] `phala_outlook` floors 195 → 5 and mis-serves them** — anchors
   original_count 195, kept_count 5 ('floored to 5 (hard-cap)'); the 5 served are all
   career/transition (zero health); `recover_via.instrument='unknown_tool'` (the escape hatch
   points at a nonexistent tool).
7. **[class 5 · LOW] `get_chart_orientation` msr_signal_count '13364'** contradicts the
   `get_signals` self-description ('the 573-signal corpus') — self-description inconsistency
   across surfaces that describe the same corpus.

## Bare-id, no-synthesis (class 6 — width/depth received but un-composable)

8. **[class 6 · HIGH] `get_domain_reading(health)`** serves **752** signal_id_refs as bare
   UUIDs with no in-response text and verdict_skeleton=null — recovery cannot be synthesized
   from ids alone.
9. **[class 6 · HIGH] `get_domain_reading(character)`** serves **7290/7283** bare refs, null
   verdict, empty template — no synthesis path (both charts).
10. **[class 6 · LOW] `graha_portrait` is the counter-example** — full usable dossier
    (position/dignity/strength/avastha/yoga ✓), so depth IS served here; but trim_report
    original_count 13 → kept_count 1 shows width is budget-trimmed away.

## Cross-lane note

Lane 6's DROWNED + UNATTRIBUTED + bare-id findings are the mechanism behind LANE2's 154
INSUFFICIENT verdicts, and the taxonomy-collapse (299 UNATTRIBUTED, single health domain)
is the proximate cause of LANE7's system-taxonomy and per-system-roga ceilings. The most
damaging defects sit on the *named-holistic* surfaces (orientation, character, assess_health)
— the ones a consumer trusts as the flagship synthesis — where drowning does the most harm.
