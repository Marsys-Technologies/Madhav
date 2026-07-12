# Lane 2 — Evidence-Sufficiency Shard 2-b9 (F. Kutumba & Vivaha: F3–F6)

Charter: LLM_CONSUMPTION_AUDIT_CHARTER §7.3 (4-point evidence-sufficiency scale).
Mode: P-12 evidence-plan-then-acquire, deployed read-only MCP connector.
Charts: N = `482012f1-...` (native, Abhisek) · A = `1c826d5a-...` (Abhinandan).
Status: COMPLETE — 16 question-instances graded (F3/F4/F5/F6 × {narrow,broad} × {N,A}).
trim_seen: TRUE (budget flags, truncated summaries, trim_report self-trimmed — see FIND-J).

---

## Shared evidence pool (acquired once, reused across F3–F6)

### Tools called + what came back

1. **assess_marriage(chart_id)** — both charts. Returns generic orientation digest + `content.verdict_skeleton.top_10_composite`. Top-K is generic solar/lunar mahapurusha yogas (N: Sasa/Shoola/Vasi/Yuga/Gola/Anapha/Kedara; A: Vasi/Vesi/Shoola/Ubhayachari/Yuga/Kedara), **all tied at composite_score 1.0465** (7–8 row identical-score wall). NONE marriage-specific — no 7th lord, no Venus karaka, no Darakaraka, no Mangal dosha.
   - `content.karaka_analysis` = **CDLM cross-domain cells** (career×relationship linkage), NOT the kalatra (Venus) karaka analysis its name implies → mislabel.
   - `content.varga_analysis` = note "Varga refinement (D9/D10/D6) available via chart_facts_query" → **D9 NOT in payload**, punted to drill.
   - `content.activating_dasha.activation_count = 0` (window 2026-2029) → **no timing/crisis windows**.
   - `content.contradictions.status = no_data`.
   - `content.house_analysis.question_lenses[].template_element_ids_jsonb.signal_ids` = bare UUIDs (unresolved).
   - `judgment_flags`: `["response_still_over_40kb_budget_after_full_trim"]` + a claim it "reconciles 7th lord + Venus kāraka + D9 from L1 chart_facts (via drill)" with `requires_acharya_validation: true` — but the payload does NOT contain 7th lord / Venus / D9 (all punted to drill).
   - `content[0].text` suppressed ("text duplicate suppressed per R5.1 C1"); data only in structuredContent. `trim_report` present and itself trimmed ("full trim_report omitted to fit budget").

2. **get_temporal_windows(chart_id)** — both charts: `activation_count = 0, predicate_count = 0, activations = []`. Crisis-window engine returns nothing. drill_next → query_convergence_windows / query_life_arc.

3. **get_dashas(chart_id)** — N: full vimshottari tree present (Mercury MD to 2027-08-18, etc.). Raw timing skeleton; NOT marriage-mapped — LLM must itself map dasha lords → 7th-house signification to derive any window (class 9).

4. **query_chart_facts(chart_id)** — N: `returned_count = 100, offset = 0`, alphabetical, **last fact = CUSP_5** (only reaches "C"). **No `total` disclosed.** Darakaraka, Venus placement, 7th-house occupants, D9 lagna all sort past "C" → beyond cap, silently absent on first contact. AMATYAKARAKA (Saturn, house_d1=7) is the only house-7 karaka within the cap.

5. **get_domain_reading(chart_id, domain=relationship)** — N: same orientation-digest wrapper, no marriage-specific verdict distinct from assess_marriage.

6. **get_signals(chart_id, domain=relationship)** — N: `returned_count = 50, total_matching_filters = 7014, truncated = FALSE` (misleading — 6964 unreturned). Top signals = same generic yogas (Sasa/Shoola/Vasi). signal_summary_text is a flat `category=... | key=... | value_text=...` string (parseable).

7. **judgment_query(chart_id, bhava=7)** — both charts. **THE governed marriage path.** Returns:
   - `about`: {domain: marriage, karakas: [Venus], operative_varga: D9}
   - `checklist.bhava_condition`: from_lagna + from_chandra 7th sign/house
   - `checklist.bhavesha_condition.from_lagna`: 7th-lord dossier {graha, house, sign, dignity_state, dignity_weight, shadbala_rupa, fact_ids[]}
   - `checklist.karaka_condition`: Venus dossier (same fields)
   - `checklist.occupants`: {from_lagna, from_chandra}
   - `verdict`: {verdict_grade, composite_score, honest "deterministic-not-calibrated" note}
   - `receipt`: {bhava✓ bhavesha✓ karaka✓ from_moon✓ varga_confirmed:"D9✓" yogas_checked bhanga_checked:FALSE timing_anchored:TRUE}
   - `judgment_flags`: **"bhanga_not_checked: cancellation (bhaṅga) checking requires a data-plane addition (design §12 D3) not yet built for any chart"**; bearing_yogas caveat (candidate, not confirmed).
   - `fact_id_refs`: 12. drill_pointers → ganita_chart_facts_get (D9), get_signals.
   - **Chart-differentiated & marriage-real:**
     - N: verdict `mixed` / score −1; 7th (Libra) occupants **Mars + Saturn** (both malefics — genuine marital-stress/separation indicator); 7th-lord Venus in 9th (Sag), neutral, shadbala 4.64.
     - A: verdict `convergent_moderate` / score 1.9; 7th occupant **Ketu**; 7th-lord Venus in 12th, **exalted**, shadbala 7.75.

8. **judgment_query(chart_id, question="...marriage...divorce...")** — error `{class: validation, message: "either domain or bhava is required"}` → free-text marriage question is NOT accepted; LLM must know to pass `bhava:7` (class 9 undocumented routing).

9. **query_special_lagnas(chart_id)** — error: requires `datetime_iso / latitude_deg / longitude_deg` (raw birth params), NOT chart_id → **Upapada Lagna (UL) not reachable by chart_id path** (relevant to F4 remarriage significators).

---

## Evidence plans + verdicts per question

### F3 — marital quality + crisis windows
**Plan (acharya order):** (1) 7th house sign + occupants from lagna & chandra; (2) 7th-lord placement/dignity/strength; (3) Venus (kalatra karaka) + Darakaraka dossier; (4) D9 lagna, D9 7th lord, Venus in D9; (5) Mangal/other marriage dosha + bhanga; (6) crisis TIMING = dasha/antardasha of 7th-lord/Venus/malefic-in-7th + transit activation windows.
**Acquired:** (1)(2)(3-partial-Venus-only) via judgment_query bhava=7 — solid. (4) D9 only *confirmed for bhavesha/karaka*, full D9 not in payload (drill). (5) Mangal dosha inferable (N: Mars in 7th) but **bhanga not built** → cancellation unknowable. (6) **timing/crisis windows EMPTY** (get_temporal_windows=0, activating_dasha=0) despite receipt `timing_anchored:true`.
**Verdict:** **narrow → INSUFFICIENT** (the "crisis windows" ask needs dated windows; the timing engine is empty — LLM would fabricate/guess dates). **broad → SUFFICIENT-WITH-GAPS** (structural marital-quality read composable from judgment_query bhava=7; honest timing gap).

### F4 — second marriage
**Plan:** significators of remarriage = 8th house (2nd-from-7th) + Upapada Lagna & 2nd-from-UL + 9th house; 7th-lord/Venus dispositor; timing of a second union.
**Acquired:** No governed remarriage lens. bhava→domain map is fixed (bhava 7 = marriage; bhava 8 = randhra/longevity, not remarriage). **Upapada unreachable by chart_id** (query_special_lagnas needs raw birth params). LLM must silently decompose "second marriage" into 8th-house + UL analysis with no governing krama.
**Verdict:** **narrow & broad → INSUFFICIENT** (no remarriage significator path; UL retrieval-blocked; answer requires ungoverned decomposition).

### F5 — divorce / separation risk
**Plan:** 7th malefic occupancy, 7th-lord affliction, Venus affliction, 6/7/8/12 axis, Mangal dosha + bhanga, D9 affliction; RISK TIMING windows.
**Acquired:** Structural risk indicators present via judgment_query bhava=7 (N: **Mars+Saturn in 7th** = strong separation signal; 7th-lord neutral). But **Mangal-dosha bhanga not built** (cannot assess cancellation), and **risk-timing windows EMPTY** (same as F3).
**Verdict:** **narrow → INSUFFICIENT** (asks *when* risk peaks; timing empty). **broad → SUFFICIENT-WITH-GAPS** (structural risk read composable; timing + bhanga gaps logged honestly).

### F6 — in-law dynamics
**Plan:** spouse's family significators = 4th-from-7th (=10th), 2nd house (kutumba), 6th (maternal-in-law frictions); disposition of those lords; harmony with native's 2nd/4th.
**Acquired:** No governed in-law lens; no in-law domain in the domain set (career/character/wealth/relationship/spirituality/health). bhava=10 maps to career, not in-laws. LLM must fully improvise the decomposition from house significations.
**Verdict:** **narrow & broad → INSUFFICIENT** (no governed significator path for in-laws; requires ungoverned decomposition; the composed houses exist but nothing serves the synthesis).

---

## Findings (deduped, shared)

- **FIND-A [class 4 EMPTY SHELL, HIGH]** get_temporal_windows + assess_marriage.activating_dasha return 0 marriage activations on both charts → crisis/risk-timing windows unserved. (F3, F5)
- **FIND-B [class 5 DISHONEST SELF-DESCRIPTION, MED]** judgment_query bhava=7 `receipt.timing_anchored:true` with zero timing/window data in payload; get_signals `truncated:false` while returning 50 of 7014. (F3, F5)
- **FIND-C [class 6/5 MISLABEL, MED]** assess_marriage `content.karaka_analysis` holds CDLM cross-domain cells, not the Venus kalatra-karaka analysis its name implies; judgment_flags claims 7th-lord+Venus+D9 reconciliation the payload does not contain (punted to drill).
- **FIND-D [class 7 DROWNED + topic-relevance, HIGH]** assess_marriage & get_signals "relationship" top-K = generic solar/lunar mahapurusha yogas tied at identical score 1.0465 (7–8 row identical-score wall); none marriage-specific. Ranker ignores topic relevance. (F3, F5)
- **FIND-E [class 6 UNUSABLE FORM, HIGH]** query_chart_facts caps at 100 alphabetical facts (cut at CUSP_5), **no `total` disclosed**; Darakaraka/Venus/7th-occupants/D9-lagna silently past the cap.
- **FIND-F [class 1 UNREACHABLE-BY-NONEXISTENCE / data plane, HIGH]** bhanga (dosha cancellation) "not yet built for any chart" → Mangal-dosha cancellation unknowable; marriage-dosha reads structurally incomplete. (F3, F5)
- **FIND-G [class 9 UNGOVERNED JUDGMENT, HIGH]** the governed marriage judgment lives in judgment_query(bhava=7), but the obviously-named assess_marriage is generic/drowned and nothing routes the consumer there; free-text marriage question errors ("domain or bhava required") — LLM must know to pass bhava:7. (all F3–F6)
- **FIND-H [class 9 + class 1, HIGH]** F4: no governed remarriage lens; Upapada reachable only via query_special_lagnas (needs raw birth params, not chart_id); LLM must silently decompose into 8th-house/UL. (F4)
- **FIND-I [class 9 + class 1, MED]** F6: no governed in-law significator lens / no in-law domain; LLM must improvise from 10th/2nd/4th-from-7th. (F6)
- **FIND-J [class 6 budget/trim, MED]** assess_marriage `judgment_flags: response_still_over_40kb_budget_after_full_trim`; text field suppressed; summaries "[truncated for budget]"; trim_report self-trimmed. trim_seen=TRUE.
- **FIND-K [class 9, MED]** judgment_query uses natural karaka Venus only; Jaimini Darakaraka (chara spouse karaka) not surfaced — if DK≠Venus, spouse-karaka read is incomplete and LLM must choose the karaka scheme. (F3, F5)

## Class-9 improvisation log
1. Tool routing: had to discover judgment_query(bhava=7) is the real marriage path (assess_marriage is a decoy) — FIND-G.
2. bhava argument: had to supply bhava:7 manually (free-text rejected) — FIND-G.
3. Dasha→window mapping: to attempt any crisis timing, had to plan a manual map of dasha lords to 7th-house signification (no governed activation) — FIND-A.
4. Question decomposition F4: silently decomposed "second marriage" → 8th house + Upapada — FIND-H.
5. Question decomposition F6: silently decomposed "in-laws" → 10th/2nd/4th-from-7th — FIND-I.
6. Karaka-scheme choice: natural Venus vs Jaimini Darakaraka left to LLM — FIND-K.
7. Pagination: to reach Darakaraka/Venus/D9 in chart_facts, must know to page past an undisclosed 100-cap — FIND-E.

---

## Verifier corroboration pass (independent re-acquisition, 2026-07-12)

Independent re-run of the deployed connector confirms the pool above. Concordant on: judgment_query(bhava=7)
structural checklist (N: Mars+Saturn in 7th, 7L Venus 9th neutral shadbala 4.64; A: Ketu in 7th, aspecting Mars+Rahu,
7L/karaka Venus exalted Pisces 12th shadbala 7.75); get_temporal_windows activation_count=0 both charts; assess_marriage
identical-score wall @1.0467 of generic mahapurusha/nabhasa yogas; **D9 `varga_confirmation.rows: []` EMPTY both charts**;
trim_report + "response_still_over_40kb" flag (trim_seen=TRUE). Two additions:
- **get_domain_reading(domain=marriage|relationship|career) returns `content: {}` EMPTY for EVERY domain, both charts** —
  systemic class-4 EMPTY SHELL (stronger statement than FIND row 30; the domain-reading surface serves nothing at all),
  and assess_marriage's internal `step_results.domain_reading.ok=true` contradicts it → class 5 (add to FIND-B).
- **apex_marriage_assess == assess_marriage** (byte-identical generic-yoga skeleton) — the "apex" alias is no better; both
  are decoys vs judgment_query(bhava=7) (reinforces FIND-G).
Verdicts unchanged. Chart B timing is even barer than N: `mahadasha_windows_by_graha: {}` fully empty (N at least held Venus MD 2034-2054).
