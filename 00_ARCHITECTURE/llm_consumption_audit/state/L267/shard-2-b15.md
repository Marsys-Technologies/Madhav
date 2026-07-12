# Lane 2 Evidence-Sufficiency — Shard 2-b15 (I5, I6, J1, J2 × 2 charts × 2 variants)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER §7.3. Mode P-12 (evidence-plan-then-acquire).
Charts: N = 482012f1 (Abhisek, native) · A = 1c826d5a (Abhinandan). READ-ONLY MCP connector.

## Cross-cutting acquisition facts (apply to all 16 rows)

- **get_chart_orientation (mandatory first call):** both charts. Native top entity_profile =
  `UNATTRIBUTED` with signal_count 299 (R-44/R-37 DROWNED anchor rediscovered), 2nd = Ketu (1 signal).
  digest msr_signal_count "13364", spirituality convergence_count 3338.
- **get_temporal_windows 2026-01-01→2030-12-31:** NATIVE → `activation_count:0, predicate_count:0,
  activations:[]` (EMPTY). ABHINANDAN → `activation_count:50, predicate_count:50` populated
  (first activation 2027-10-15). Same tool, same window, opposite result → native L3 kala_activation
  empty (R-45 EMPTY-SHELL rediscovery + cross-chart INCONSISTENT). Native returns inline empty;
  Abhi returns text-suppressed "large payload → structuredContent" (different response mode).
- **get_projections domain=spirituality / wealth, native:** `projection_count:0` (kala_bhavishya empty).
- **get_dashas native:** works, grounded. Mercury MD → 2027-08-18, then Ketu MD. Raw chain only;
  no event-semantic layer.
- **judgment_query (v3):** THE usable bhava instrument. Returns verdict_grade + composite_score +
  receipt (which checklist items checked) + checklist (bhava/bhavesha/karaka conditions w/ dignities,
  shadbala, fact_ids) + timing_hooks. Grounded. `response_format` accepts only `legacy|v3` (docs said
  `full` — rejected; minor schema-doc drift). trim_report present (original 4, kept 1). bhanga_not_checked
  honest flag on every call.
- **get_domain_reading spirituality (both charts):** returns question_lenses (3 lenses, e.g. lens
  question_type "education" under spirituality domain), cdlm_cells (shared-signal COUNTS only),
  `signal_id_refs` = bare UUIDs capped 200 of 3338 total (`signal_id_refs_capped:true`). NO prose
  synthesis, no signal text. Unusable-form for direct reading (class 6); usable path is judgment_query.

## Per-bhava judgment verdicts acquired

| bhava | tool label | Native verdict | Abhi verdict | karaka set used |
|---|---|---|---|---|
| 9 (dharma) | Spirituality/Dharma | convergent_strong 5.7 | contested −4 | Jupiter+Ketu, D20✓ |
| 12 (foreign/moksha) | "Bhava 12" (no domain) | convergent_moderate 2.2 | mixed −1 | **[] EMPTY** (karaka:false) |
| 4 (property/homeland) | **"Education/Learning"** | mixed 0.9 | contested −1.7 | **Mercury+Jupiter**, D24 |

Native bhava 9: Jupiter own-sign in 9th (shadbala 7.8), karakas Jupiter+Ketu, D20 confirmed.
Native bhava 12: bhavesha Jupiter in 9 own, aspected by Ketu, occupants none, karaka omitted.

## Class-9 UNGOVERNED-JUDGMENT improvisations logged (first-class findings)

1. **Silent decomposition** "property abroad" → bhava 4 (property) + bhava 12 (foreign): no composed
   instrument exists; executor chose the house pair.
2. **Karaka substitution:** bhava-4 judgment ships education karakas (Mercury/Jupiter); executor had to
   mentally substitute property karaka (Mars) / home karaka (Moon) — the tool never weighs them.
3. **Life-event → chart mapping:** "return to homeland" and "guru arrival" have no event taxonomy;
   executor mapped them to 4th-house / Jupiter+9th himself.
4. **Timing krama choice:** native temporal_windows empty → executor fell back to raw dasha chain and
   would have to pick which dasha "means" the event (no governed event-timing).
5. **Depth/type translation:** spiritual "type" (bhakti/jnana/karma/raja) — executor must translate
   verdict_grade + Jupiter/Ketu karakas into a path taxonomy the system does not govern.
6. **Path adjudication:** unusable domain_reading (signal_id dump) vs usable judgment_query — executor
   routed to judgment_query as authoritative; routing ungoverned.

## trim_seen: TRUE (multiple, mostly DISCLOSED/honest)
judgment_query trim_report (4→1); domain_reading signal_id_refs 200/3338 capped; temporal_windows /
kala windows text-channel suppressed → structuredContent. Native activation empty is NOT a trim (genuinely 0).

## Verdicts (see StructuredOutput results[] for the 16 rows)
- I5 property-abroad: narrow INSUFFICIENT (both); broad SUFFICIENT-WITH-GAPS (both).
- I6 return-homeland-timing: native INSUFFICIENT (temporal empty); Abhi SUFFICIENT-WITH-GAPS.
- J1 spiritual-inclination: native broad SUFFICIENT / narrow SUFFICIENT-WITH-GAPS; Abhi same pattern.
- J2 guru-arrival-timing: native INSUFFICIENT (temporal empty); Abhi SUFFICIENT-WITH-GAPS.
