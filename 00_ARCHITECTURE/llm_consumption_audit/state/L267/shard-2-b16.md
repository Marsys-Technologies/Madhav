# Lane 2 — Evidence-Sufficiency shard-2-b16 (Group J: Dharma & Moksha)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER §7.3 (4-point scale). Mode: P-12 evidence-plan-then-acquire.
Deployed MCP connector (read-only). Charts: A=`482012f1…` (Abhisek), B=`1c826d5a…` (Abhinandan).
Questions: J3 ishta-devata, J4 renunciation, J5 karmic-debt (disclosure tiers), J6 moksha-marga maturity — each × 2 charts × {narrow, broad} = 16.

trim_seen = TRUE (judgment_query `trim_report`: original_count 4 → kept_count 1, "full trim_report omitted to fit budget"; get_domain_reading `token_safety_note` bounds to 3 lenses × 20 signals).

---

## Shared evidence landscape (acquired once; reused across J3–J6)

### Evidence PLAN (what an acharya needs, in order)
- **J3 ishta-devata:** Jaimini krama — (1) Atmakaraka identity; (2) karakamsa = AK's sign in D9; (3) planets in / aspecting 12th-from-karakamsa; (4) planet→deity translation. Tools: query_chart_facts (ATMAKARAKA, AK_PADA), get_positions D9, judgment_query spirituality.
- **J4 renunciation:** sannyasa/pravrajya yogas (4+ grahas in one bhava, Saturn-Moon, strong Ketu, 12th-lord dispositions), Ketu/12th/Saturn dossier. Tools: ganita_yogas_get, ref_yogas_get, judgment_query spirituality + bhava12, graha_portrait Ketu.
- **J5 karmic-debt:** Rahu-Ketu axis, Pitru/Kala-Sarpa/rina doshas, retrogrades; + disclosure-tier gating (Ethical Framework). Tools: ganita_yogas_get (fired doshas), ref_doshas_get, get_signals.
- **J6 moksha-marga maturity:** 12th house + moksha-trikona (4/8/12), Ketu (moksha karaka), D20/D24 varga, developmental/maturity trajectory. Tools: judgment_query bhava12 + spirituality, kala_life_arc_get, get_temporal_windows spirituality.

### Evidence ACQUIRED (tools called)
- `judgment_query {domain:spirituality}` A → verdict "Spirituality / Dharma", **bhava 9**, karakas [Jupiter, Ketu], operative_varga **D20**, verdict_grade **convergent_strong**, composite **5.7**, fact_ids attributed. B → **contested**, composite **−4**. STRONG, attributed, chart-discriminating. Receipt: bhava/bhavesha/karaka/from_moon ✓, `varga_confirmed:"D20✓"`, yogas_checked 14, bhanga_checked FALSE, timing_anchored ✓. **BUT** `content.varga_confirmation.rows == []` (receipt claims D20✓ yet zero rows) and `bearing_yogas == []`.
- `judgment_query {bhava:12}` A → "Bhava 12", verdict convergent_moderate 2.2, **karakas:[]** (moksha karaka Ketu NOT invoked), operative_varga **D1** (not moksha varga), yogas_checked 0. B → mixed −1, karakas:[]. Weak for moksha.
- `get_domain_reading {domain:spirituality, max_lenses12, max_signals100}` A/B (78 KB) → 3 lenses (education, foreign_travel, **spirituality**). Spirituality lens `all_relevant_ranked_jsonb`: total 3358, `ranked_signals` = **bare {signal_id, salience, signal_type_class} — NO text/label**; `template_element_ids_jsonb: []`; verification_pass_status "documented_approximation". `available_domains` = career/character/health/relationship/**spirituality**/wealth — **no "dharma", no "moksha"**. Orientation entity **UNATTRIBUTED signal_count 299** dominates.
- `get_signals {domain:spirituality, limit8}` A → 8 signals WITH `signal_summary_text`+`constituent_facts_array`, but content = generic yogas (Anapha, Kedara, Sasa, Shoola, Vasi, Yuga, Gola) each tagged `domains_affected_array`=[career,wealth,health,relationship,spirituality], **all salience 0.48875 (identical-score wall)**; only 1 spirituality-specific ("swamsa_position house=10"). DROWNED / non-discriminating.
- `query_chart_facts` A → ATMAKARAKA=Moon (Aquarius, h11, rank1); AK_PADA navamsha_sign=**Aries (=karakamsa)**; AMATYAKARAKA=Saturn; ARUDHA_A9/A12 present; varga house labels D10_moksha/D12_moksha/D20_dharma etc. **No `ishta_devata`, no `karakamsa`-named, no sannyasa-yoga, no moksha-maturity fact.** pagination.total = **null** (1000-row cap, total undisclosed); `search` param **ignored** (returns alphabetical slice).
- `ganita_yogas_get` A & B → fired doshas include **Pitru Dosha, Kala Sarpa Dosha, Kala Amrita Dosha** (both charts) — karmic-debt substrate present. No sannyasa/pravrajya yoga among fired.
- `ref_doshas_get` → pitru_dosha, kala_sarpa (+14 variants), sarpa_yoga_dosha catalogued. `ref_yogas_get` search param ignored; first 100 expose no sannyasa/pravrajya.
- `vector_search {query_text:"ishta devata…karakamsa"}` → RAG chunks (Jataka Parijata PG58) OCR-garbled ("Dertomacal and divine portions"), not chart-computed. `ref_rules_search "renunciation"` → Bhrigu Nandi Nadi chunks, not chart-bound.
- `kala_life_arc_get` A → dasha parvas w/ generic theme_keywords (expansion, wisdom, abundance); no moksha-maturity trajectory. `get_temporal_windows {domain:spirituality}` → orientation_context digest wrapper.

### Class-9 UNGOVERNED-JUDGMENT log (first-class findings)
1. **Domain substitution (all J):** no "dharma" / "moksha" domain exists → I silently used "spirituality" lens as proxy for both purusharthas. Silent decomposition.
2. **J3 method + deity translation:** system holds AK + karakamsa ingredients but NO ishta-devata derivation nor planet→deity table → I must pick the Jaimini krama AND supply the deity taxonomy myself.
3. **J4 sannyasa-yoga assembly:** no sannyasa/pravrajya asset → I must reconstruct the renunciation-yoga rule from raw grahas.
4. **J5 disclosure-tier framing:** no tool exposes Ethical-Framework tier gating → I improvise how much karmic-debt to disclose and to whom.
5. **J6 "maturity" operationalization:** no maturity metric → I define maturity (taxonomy→life-language) with no system anchor.

### Findings (deduped, §4 classed)
- **F1 (class 1 UNREACHABLE-BY-NONEXISTENCE):** ishta-devata deity uncomputed — AK/karakamsa present, deity derivation absent. [J3]
- **F2 (class 6 UNUSABLE FORM):** get_domain_reading spirituality lens `ranked_signals` = bare IDs+salience, no text (recoverable only via a 2nd tool, get_signals — secondary class 9). [J3/J4/J6]
- **F3 (class 5 DISHONEST + class 4 EMPTY SHELL):** judgment_query receipt `varga_confirmed:"D20✓"` while `varga_confirmation.rows:[]`; `bearing_yogas:[]` despite yogas_checked 14. [J3/J6]
- **F4 (class 4/1):** no sannyasa/pravrajya-yoga detection; spirituality checklist's bearing_yogas empty. [J4]
- **F5 (class 7 DROWNED):** get_signals spirituality = generic 5-domain yogas at identical 0.48875 wall; orientation UNATTRIBUTED 299 dominates. [J3/J4/J6]
- **F6 (class 1):** Dharma & Moksha not first-class domains (only "spirituality" of 6). [all J]
- **F7 (class 9):** disclosure-tier gating for karmic framing unserved. [J5]
- **F8 (class 4/1):** moksha-marga maturity — bhava-12 lens invokes neither moksha karaka Ketu (karakas:[]) nor moksha varga (D1); no maturity metric. [J6]
- **F9 (class 5 receipt-honesty):** pagination.total null (undisclosed cap); judgment_query trim_report 4→1 budget-trimmed. [all]
- **F10 (class 9/6):** `search` param ignored on query_chart_facts & ref_yogas_get → forces full-dump-then-grep. [all]

### Per-question verdicts
- **J3 narrow** A/B → INSUFFICIENT (deity = UNREACHABLE-BY-NONEXISTENCE; F1,F2).
- **J3 broad** A/B → SUFFICIENT-WITH-GAPS (Jupiter+Ketu/D20 karakas composable; deity translation is the gap; F1,F5).
- **J4 narrow** A/B → INSUFFICIENT (sannyasa-yoga uncomputed; F4).
- **J4 broad** A/B → SUFFICIENT-WITH-GAPS (Ketu-exalted-8th + bhava12 + Saturn-on-9 composable; F4,F5).
- **J5 narrow** A/B → SUFFICIENT-WITH-GAPS (Pitru/Kala-Sarpa/Kala-Amrita fired; disclosure-tier gap; F7,F9).
- **J5 broad** A/B → SUFFICIENT-WITH-GAPS (same karmic substrate, broader narrative; F7).
- **J6 narrow** A/B → INSUFFICIENT (no maturity metric; bhava-12 lens starved; F8,F3).
- **J6 broad** A/B → SUFFICIENT-WITH-GAPS (Ketu+bhava12+D20 composable; maturity dimension missing; F8,F5).
