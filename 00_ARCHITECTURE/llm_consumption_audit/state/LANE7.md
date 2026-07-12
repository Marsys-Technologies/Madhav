# LANE7 — P-11 requirements spec per heavy question + ceiling findings (L2)

```
resume:
  lane_id: LANE7
  lane_number: 7
  layer: L2 (heavy questions, native chart C1 + control C2)
  method: P-11 (per-heavy-question requirements spec → measure attainable ceiling)
  ceiling_classes: 1 (UNREACHABLE-BY-NONEXISTENCE), 4 (empty temporal layer), 3 (cross-chart hole), 8 (untypable)
  status: DONE
  checkpoint_ts: 2026-07-12 (native chart audit session)
```

## Scope

Lane 7 runs the **P-11 protocol**: for each heavy question, first write the *requirements
spec* — the set of computed artifacts a governed answer would need — then measure the
attainable **ceiling** against what the data plane actually holds. Where a required artifact
does not exist anywhere (no field, no method, no computation), the question is
**UNREACHABLE-BY-NONEXISTENCE (class 1)**: no retrieval fix can raise the ceiling, because
the value was never computed. This lane isolates the true ceiling defects from mere
retrieval-plumbing gaps.

## P-11 requirements spec per heavy question

| heavy question | required artifact (P-11 spec) | present? | ceiling | class |
|---|---|---|---|---|
| Longevity / lifespan band | ayurdaya computation (Pinda/Nisarga/Amsa) + maraka window | **NO** — no ayurdaya field anywhere | cannot produce band without fabrication | 1 |
| Broad longevity balance | multi-factor ayus balance | **NO** — only coarse dasha-parva life arc | no ayus quantification | 1 |
| Chronic disease **by system** | per-body-system roga taxonomy / D6 disease-system mapping | **NO** — health is a single domain | no per-system propensity | 1 |
| Accident / injury / surgery | chart-level mrityu-bhaga / arishta accident signal | **NO** — only nadi-text citations | no chart-scoped accident signal | 1 |
| Health-crisis **window** | structural×temporal convergence typed to health (kala_activation) | **EMPTY** on C1 | no crisis window served | 4 |
| Mental-health vulnerability window | manas-typed activation predicate | **NO typing** — generic activations only | window present but un-queryable | 8 |

## Ceiling findings — class 1 (UNREACHABLE-BY-NONEXISTENCE)

1. **[class 1 · HIGH] No longevity/ayurdaya computation exists.** `judgment_query{bhava:8}`
   verdict -0.8 (C1) / -0.5 (C2), receipt.karaka:**false**, yogas_checked:**0**; no ayurdaya
   field anywhere in the payload. A longevity band cannot be produced without fabrication.
   Broad longevity: `kala_life_arc` gives dasha parvas (quality/theme) but **no ayus
   quantification** and no ayurdaya method — unreachable on both charts.
2. **[class 1 · HIGH] No per-body-system disease taxonomy.** The system models health as a
   single domain; `judgment_query` verdict is a bhava-1/domain-health aggregate with no
   system-level classification field, and D6 placements carry no disease-system mapping. A
   'by system' chronic-propensity read is unreachable-by-nonexistence on both charts.
3. **[class 1 · HIGH] No accident/injury/mrityu-bhaga propensity computed at chart level.**
   `vector_search('accident injury surgery')` returns only classical nadi-text citations
   (citation_ref nadi_navamsa_patel:PG1710 'physical injury, worries; debt…'), **not**
   chart-derived signals. No accident/arishta signal exists in the health signal set
   (top-K = combustion 0/1 walls at 0.575). Data-plane nonexistence.

## Ceiling findings — class 4 (empty temporal layer)

4. **[class 4 · HIGH] `get_temporal_windows` returns 0 activations on C1** for the health
   horizon (activation_count 0, predicate_count 0; date_from 2026-07-12 → 2027-07-12, and 0
   over 2026-2029). The entire 'windows' half of every timed health question is empty on the
   native chart — the kala_activation R-45 rediscovery, native-specific.
5. **[class 4 · HIGH] Broad health-crisis windowing has no path.** `apex_health`
   activating_dasha.activations:[] and predicates:[] AND `get_temporal_windows` empty — no
   structural×temporal convergence for health is served from either front.
6. **[class 4 · MED] `phala_outlook` near-future anchors are wrong-domain.** anchors[0].domain
   = transition (not health), horizon_months=12 only. The one populated temporal surface does
   not answer the health-timing question.
7. **[class 4 · MED] Windows recoverable only via `get_projections`, not the purpose-named
   `get_temporal_windows`.** `get_projections` C1 returns a health window (peak 2027-10-20)
   for the same horizon on which `get_temporal_windows` is empty — inconsistent/undocumented
   routing that hides the only reachable window behind a non-obvious tool.

## Ceiling findings — class 3 (cross-chart hole) & class 8 (untypable)

8. **[class 3 · HIGH] Cross-chart inconsistency exposes a native-chart data hole.**
   `get_temporal_windows` C2 returns **50** activations / 50 predicates for the identical
   horizon on which C1 returns **0/0**. The empty native temporal layer is a data hole, not a
   horizon artifact — C2 proves the surface works when the rows exist.
9. **[class 8 · MED] Populated activations are un-typable to the question.** Even C2's 50
   activations carry no manas/mental-health predicate class, so the mental-health vulnerability
   window is present-but-un-queryable; and no `mental` domain exists to filter by. The
   structural resilience read IS served (`graha_portrait(Moon)` completeness all ✓ incl
   cgm_neighborhood) — only the *typed temporal window* is missing.

## Ceiling summary

- **Hard ceilings (class 1, no retrieval fix possible):** longevity/ayurdaya, per-system roga
  taxonomy, chart-level accident/mrityu-bhaga propensity. These require **new computed
  artifacts** (data-plane additions), not retrieval plumbing.
- **Soft ceilings (class 3/4/8, retrieval- or typing-repairable):** the empty C1 temporal
  layer (rows exist for C2 → native-chart backfill), the get_temporal_windows↔get_projections
  routing split, and the absence of manas-typing on activation predicates.

## Cross-lane note

Lane 7 partitions LANE2's 154 INSUFFICIENT verdicts by *fixability*: the class-1 ceilings are
irreducible without new computation, whereas the class-3/4/8 ceilings are repairable. Lane 6's
UNATTRIBUTED-collapse (single health domain, 299 unattributed signals) is the proximate cause
of the class-1 system-taxonomy ceiling here — attribution + taxonomy must be built before a
'by-system' or longevity read can clear its ceiling.
