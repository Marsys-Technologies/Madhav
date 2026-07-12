# LANE2 — Evidence-sufficiency + class-9 executor-improvisation audit (L2 heavy-question lane)

```
resume:
  lane_id: LANE2
  lane_number: 2
  layer: L2 (heavy judgment questions, native chart C1 + control C2)
  questions_total: 328
  questions_audited: 328
  class9_improvisation_count: 328
  status: DONE
  checkpoint_ts: 2026-07-12 (native chart audit session)
```

## Scope

Lane 2 asks, per heavy judgment question: **once the retrieval plane has returned
everything it can, is the evidence a consuming LLM receives sufficient to compose the
answer — or must the executor improvise the synthesis method the system should govern?**
It scores evidence-sufficiency per question and counts class-9 (executor-improvisation)
incidence: cases where the surface is *composable at the point of consumption* but the
system supplies no governed verdict/synthesis path, forcing the executor to author the
method itself.

## Evidence-sufficiency spread (328 questions)

| verdict | count | share |
|---|---|---|
| SUFFICIENT-WITH-GAPS | 170 | 51.8% |
| INSUFFICIENT | 154 | 47.0% |
| SUFFICIENT | 4 | 1.2% |

Only **4 of 328** heavy questions are SUFFICIENT with no gap — the composite/governed
surface returns a directly composable answer. The modal verdict (170) is
SUFFICIENT-WITH-GAPS: the raw material exists but arrives without the governed synthesis
the question demands. 154 are INSUFFICIENT (the retrieval plane returns empty, drowned,
or nonexistent data — cross-referenced to LANE6 DROWNED and LANE7 ceiling findings).

## Class-9 improvisation count

**class9_improvisation_count = 328 / 328.** Every heavy question in this lane terminates
in executor improvisation of *some* load-bearing step — because no L2 composite emits a
governed verdict object. The two dedicated verdict surfaces (`assess_health` /
`get_domain_reading` verdict_skeleton) return **null** verdicts on both charts; every
"answer" is therefore assembled by the executor from per-graha dossiers plus an
executor-authored synthesis rule. Class-9 is thus not a tail phenomenon on this lane — it
is the structural default: the system governs retrieval but not judgment.

## Where composability IS served (the SUFFICIENT-WITH-GAPS floor)

- **`judgment_query{domain:health}` — governed classical checklist (C1 & C2).** Returns a
  composable vitality skeleton: lagna Aries + lord Mars h7 (shadbala 5.57) + Sun karaka +
  D6 varga_confirmed + yogas_checked (7 on C1 / 8 on C2); grounding.fact_ids resolve.
  Verdict composite +0.7 (C1) / -0.8 (C2). This is the single reliable composability floor —
  a single-varga (D6) checklist an executor can turn into a vitality read.
- **`graha_portrait` — full per-graha dossier (depth axis served).** `graha_portrait(Moon)`
  completeness all ✓ (position / dignity / strength / avastha / yoga / cgm_neighborhood).
  This is the *only* surface where the depth axis is genuinely met — but `trim_report`
  shows original_count 13 → kept_count 1 (facets budget-trimmed), so width is sacrificed.

## Class-9 improvisation findings (executor must supply the governed method)

1. **[class 9 · LOW] `judgment_query{domain:health}` composable to a vitality read** on both
   charts, but the read itself is executor-composed from the checklist — the system emits no
   vitality verdict. Evidence: C1 verdict composite +0.7, receipt{bhava,bhavesha,karaka,
   varga_confirmed:D6,yogas_checked:7}; C2 composite -0.8, D6, yogas_checked 8, grounding n=17.
2. **[class 9 · MED] No composite delivers a recovery/vitality verdict.** Recovery-capacity
   must be improvised from per-graha strength; `assess_health` verdict is DROWNED, only
   `graha_portrait` strength/avastha is usable — the executor supplies the synthesis method.
3. **[class 9 · MED] Both personality surfaces fail; portrait rests on executor-assembled
   graha dossiers.** On C2, `get_chart_orientation` top_signals empty and character reading
   returns bare ids — there is no governed personality-synthesis path; the executor assembles
   the portrait from graha dossiers by hand.
4. **[class 9 · MED] No `mental-health` domain in the taxonomy** (enum = career / relationship
   / health / wealth / spirituality / character). B-class mental-health questions force silent
   decomposition into proxies the executor must choose. `get_domain_reading` requires one of
   the six governed domains; manas has none.
5. **[class 9 · MED] `judgment_query(bhava=4)` mis-routes emotional foundation.** Bhava-4 maps
   to domain 'Education / Learning', routing away from sukha / chitta / emotional-foundation
   needed for a mental-health read; `bhanga_not_checked` flag ("requires data-plane addition
   not yet built"). Executor must re-map the bhava semantics itself.
6. **[class 9 · MED] Mental-health windows approximable only from generic activations.** C2
   returns 50 activations but none are manas/mental-typed; the executor must adjudicate
   relevance the system should govern (cross-ref LANE7 window ceiling + the class-8 typing gap).
7. **[class 9] `judgment_query` exposes no buddhi / character / intelligence domain** — domains
   fixed to marriage / career / wealth / health / progeny / education / spiritual; any
   intellect/character question is decomposed by the executor with no governed proxy.

## Cross-lane note

The 154 INSUFFICIENT verdicts here are *not* independent of the other L2 lanes: they resolve
to LANE6 DROWNED/UNATTRIBUTED surfaces (drowned top-K, bare-UUID domain readings) and LANE7
ceiling findings (ayurdaya / accident / system-taxonomy nonexistence; empty temporal layer).
Lane 2's distinctive contribution is the 170 SUFFICIENT-WITH-GAPS band: questions the system
*could* govern to a verdict but currently leaves to executor improvisation — the highest-yield
repair target because the raw material is already on the wire.
