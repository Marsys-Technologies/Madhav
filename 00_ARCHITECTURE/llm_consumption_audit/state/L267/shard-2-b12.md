# Lane 2 — Evidence-Sufficiency Shard 2-b12

Charter: LLM_CONSUMPTION_AUDIT_CHARTER §7.3 (4-point scale). Mode: P-12 evidence-plan-then-acquire.
Channel: deployed MCP connector (read-only). Charts: A=482012f1 (Abhisek Mohanty), B=1c826d5a (Abhinandan Mohanty).
Questions: G5, G6 (Santana) · H1, H2 (Bandhu/Ripu/Vyavahara) — each narrow+broad × 2 charts = 16 verdicts.

## Evidence plans (the deliverable — what an acharya needs, in order)
- **G5 later-life relation with children** → (1) 5th bhava condition from lagna+chandra; (2) 5th lord
  strength/placement; (3) Jupiter putrakaraka; (4) D7 saptamsha depth; (5) putra-yogas/doshas;
  (6) LATER-LIFE timing = 5th-lord + Jupiter mahadashas in the native's later decades; (7) bhanga.
- **G6 adoption indication** → 5th house + 5th lord + Jupiter AFFLICTION pattern, Ketu/8th links, the
  specific classical adoption yogas (Saravali/Phaladeepika adoption combinations); D7; dattaka rules.
- **H1 sibling relations/fortunes** → 3rd bhava (younger sibs, courage) + 11th (elder sibs) + Mars
  bhratrukaraka; D3 drekkana; bhavat-bhava for each sibling's own fortune; sibling yogas.
- **H2 friendship/alliance reliability** → 11th bhava (labha/friends) + its lord + Jupiter/Mercury;
  6th ripu (betrayal/enemies); 7th (alliances/partners); a trust/reliability metric.

## Tools exercised
judgment_query (bhava 5/3/11 × A/B) · get_domain_reading (progeny probe) · get_signals
(domain=progeny/siblings + unfiltered) · get_temporal_windows (A 2024-28, A 2045-60, B 2050-65) ·
vector_search (adoption; siblings) · query_chart_facts (D7 depth) · get_chart_orientation digest (embedded).

## Cross-cutting instrument facts (govern all 16 verdicts)

**F-A. Only judgment_query serves these bhavas.** get_domain_reading exposes exactly 6 domains
(career/relationship/health/wealth/spirituality/character): `note: "Domain 'progeny' not found"`,
`lenses_total=0`. get_signals(domain=progeny) AND (domain=siblings) both `total_matching_filters=0`
— MSR `domains_affected_array` limited to the same 6; progeny/siblings/friends UN-TAGGED. The
ranked-signal surface is a dead end here; judgment_query(bhava) is the sole structured path. [class 1/6]

**F-B. judgment_query checklist is partial — same skeleton every bhava.** receipt every call:
`yogas_checked=0`, `bhanga_checked=false`; `bearing_yogas=[]`; `varga_confirmation.rows=[]`. No
putra/bhratru/friendship yoga eval and no bhanga check occurs — advertised stages return nothing.
judgment_flags honestly: bhanga is "a data-plane addition ... not yet built for any chart." [class 4 + class 1]

**F-C. Receipt says `varga_confirmed: D7✓` but rows are empty.** D7 rows `[]` in the judgment
payload, yet query_chart_facts(divisional_chart=D7) returns 30 rows same chart — varga depth is in
the DB, reachable only via a SECOND differently-named call the receipt implies is already done.
[class 5 dishonest receipt + class 9 undocumented drill]

**F-D. get_temporal_windows returns activation_count=0 for EVERY window, both charts.** A 2024-28: 0;
A 2045-60: 0; B 2050-65: 0. R-45 (kala_activation empty-shell) rediscovered. The "later-life"
temporal dimension of G5 is UNRETRIEVABLE; only raw dasha start/end dates (judgment_query
timing_hooks / get_dashas) survive. [class 4]

**F-E. Bhava→life-language mapping exists only for bhava 5.** judgment_query labels bhava 5
"Progeny / Children" but bhava 3 → "Bhava 3", bhava 11 → "Bhava 11" — no siblings/friends semantics;
executor translates house→life-domain itself. [class 9]

**F-F. vector_search is chart-agnostic classical-text RAG with EMPTY text.** 10 shastra chunk
citation_refs (phaladeepika:PG21:C1, saravali, brihat_jataka, nadi_navamsa) for adoption/siblings,
but every row `text=""` and `score=0` — pointers without the verse, not this native's chart. [class 6]

**F-G. Trim + honesty.** Every judgment_query: `trim_report kept_count=1 of original_count=3`
("omitted to fit budget"); text channel suppressed ("text duplicate suppressed ... per R5.1 C1").
**trim_seen = TRUE for all 16.** Digest `msr_signal_count=13364` vs tool descriptions' "573 signals"
(class 3/5 drift); orientation entity table headed by `UNATTRIBUTED signal_count=299` (R-44); top
chart_defining signal a D108 dignity restatement at salience 2.99 (R-37 trivia-as-defining).

## Per-chart structural evidence captured (chart-specific, DID arrive)
- A bhava5 progeny: convergent_moderate 2.1; Jupiter OWN 9th shadbala 7.8; bhavesha Sun 10th; aspected Jupiter+Moon; 16 fact_ids.
- B bhava5 progeny: contested -1.6; Jupiter DEBILITATED 10th shadbala 6.9; bhavesha Sun 11th. (Genuine negative progeny signal surfaced.)
- A bhava3 mixed 0.6 · A bhava11 convergent_strong 3.25 (Moon) · B bhava3 mixed -0.1 (Moon) · B bhava11 mixed -0.3 (Mercury+Sun).

## Verdicts (§7.3)
- G5 narrow A/B & broad A/B → **SUFFICIENT-WITH-GAPS**. Core 5th-house structural read composable; putra-yogas unchecked (F-B), D7 needs 2nd call (F-C), later-life TIMING empty (F-D).
- G6 narrow A/B & broad A/B → **INSUFFICIENT** (adoption-specific concept UNREACHABLE-BY-NONEXISTENCE). No chart adoption instrument; classical adoption text arrives text-empty (F-F).
- H1 narrow A/B & broad A/B → **SUFFICIENT-WITH-GAPS**. 3rd-house condition composable but generic-labelled (F-E); siblings span 3rd+11th+Mars silently decomposed (class 9); D3+yogas absent.
- H2 narrow A/B & broad A/B → **SUFFICIENT-WITH-GAPS**. 11th (labha) condition a usable proxy but conflates gains/friends/elder-sibs; "reliability" has no metric, 6th ripu not composed — heavy class-9.

## Class-9 improvisation log
1. Ungoverned tool selection: no domain reading + no domain-tagged signals → executor chose judgment_query(bhava) as sole path.
2. Silent decomposition: "siblings"→3rd+11th+Mars; "friendship reliability"→11th+6th ripu — no instrument composes these.
3. Taxonomy→life-language: bhava 3/11 bare "Bhava N" labels translated to siblings/friends unaided (F-E).
4. Scope adjudication: G6 adoption — executor decided the system does not model adoption and refused to fabricate.
5. Depth acquisition: executor inferred undocumented D7/D3 second-call because judgment receipt falsely implies varga confirmed (F-C).
