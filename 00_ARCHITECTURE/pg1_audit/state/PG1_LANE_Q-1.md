# PG1 LANE Q-1 — Reading Quality vs the Acharya Bar

- **Lane:** Q-1 (reading quality — the only lane judging whether the readings the instrument produces are any good)
- **Branch:** pg1/wave
- **Mode:** READ-ONLY (mcp__postgres__query, SELECT-only)
- **Findings emitted:** 12 (1 coverage-critical + 10 per-reading verdicts + 1 cross-cutting)
- **Standard judged against:** CLAUDE.md §J — an independent senior Jyotish acharya reviewing the corpus should reach one of "this is my own level", "this is above my own level", or "this reveals things I wouldn't have seen on first pass." Nothing less.
- **Pre-committed rule honoured:** findings reported AS-IS; no softening of the unfavorable verdict, no lighter scrutiny for either sign.

---

## THE HEADLINE QUALITY VERDICT (full, unsoftened — this is THE wave's reading-quality verdict)

**The instrument does not, today, produce a single acharya-grade reading — because it does not, today, produce a served reading at all, and every persisted interpretive artifact that stands in for one describes the instrument's own machinery instead of reading the chart.**

I was charged to sample 10 real past assistant readings and judge each against the §J bar. **They do not exist.** The entire conversation store is empty: `conversation_messages = 0`, `conversations = 0`, `conversation_branches = 0`, `conversation_message_embeddings = 0`, `project_conversations = 0`. The LLM synthesis log that would have captured any generated reading is empty: `llm_call_log = 0`. So are `tool_execution_log`, `context_assembly_item_log`, and `query_plan_log`. No user-facing reading has ever left this instrument and been persisted. That fact alone is the most important quality finding in this lane, and it is recorded as PG1-Q1-0001 (critical): **the claim that this instrument reads at or above an acharya's level is, as of this audit, entirely unvalidated by any live output.** The Pariprashna conversational surface is target-architecture (v0.5), not a running, reading-producing system.

Faithful to the spirit of the charge — judge the readings the instrument actually produces — I judged the ten best available PROXIES: the deterministic interpretive artifacts the build pipeline DOES persist, spanning the domains asked for (career, health, marriage, wealth, timing, remedies): the L5 `mimamsa_insight_units` verdict objects, `mimamsa_predictions`, the L2 `bodha_discoveries` (whose very columns — `surface_reading`, `depth_reading`, `why_an_acharya_misses_it` — are built to embody the §J "reveals things I wouldn't have seen" clause), and `bodha_rm_remedy_prescriptions`.

**Verdict on all ten, rendered plainly, one at a time:**

1. **Career verdict** — falls short. The instrument stores TWO contradictory verdicts for the identical question_lens: "Career Advancement: promised (grade 8.2/10). Strong evidence across traditions." AND "Career Advancement: conditional (grade 4.0/10). Conditional — context-dependent." An acharya judges once and defends it. Enumerating both is not judgment.
2. **Health verdict** — falls short. "Chronic Illness Onset: denied (grade 1.2/10). Mixed or insufficient evidence." — the same canned tail attached to surgery, acute illness and chronic onset alike. "denied" and "insufficient evidence" are contradictory; no disease karaka, house, or maraka window is named.
3. **Marriage verdict** — falls short, and inverts §13.9. On the most anxiously-asked question in all of jyotish, the entire reading is: "Marriage: denied (grade 1.6/10). Mixed or insufficient evidence." One word and a grade. No 7th house, no Venus, no Darakaraka, no Navamsa, no dasha. A bare, frightening negative — exactly the emotional-register failure §13.9 names.
4. **Grade/label/prose incoherence** — falls short. "Education Milestone: denied (grade 5.0/10). Conditional — context-dependent." The verdict word (maximally negative "denied"), the number (neutral 5.0/10), and the prose ("Conditional") contradict one another inside a single string. The render is internally incoherent.
5. **Wealth verdict** — falls short. "Major Financial Gain" and "Major Financial Loss" carry the IDENTICAL grade; and the same gain lens resolves to both "conditional (2.3/10)" and "denied (1.5/10)." The instrument cannot distinguish a gain from its opposite.
6. **Top-ranked discovery** — falls short of "reveals things I wouldn't have seen." The native's highest-ranked discovery is: depth_reading "Stands -5.9σ from ga_sade_sati baseline (mean=0.591)"; why_an_acharya_misses_it "Statistically extreme within ga_sade_sati subsystem (5.9σ)…". Circular — an acharya "misses it" because the instrument's own z-score is large. No graha, bhava, dasha, or meaning. Stored 5+ times verbatim.
7. **Latent insight** — falls short. surface "Signal graha_kp_lords:prana_lord with low visibility (salience 0.272)", depth "Structurally consequential: consequence_score=1.000, non_obviousness=0.903". It names an internal DB key and three of its own scores, then asserts consequence without a single jyotish claim. Data dumped, not synthesized.
8. **Distributional hypothesis prose** — falls short. "Pattern lord_aspects_lord_per_varga:aspects_VEN is a ga_structural outlier; predicts distinctly unusual outcomes in character." Leaks raw column names ("constituent_facts_jsonb_atomic", "aggregate_D60") as findings and predicts "distinctly unusual outcomes" without ever saying what the outcome is. One row even mismatches its own varga (D108 vs d10 — a data-integrity bug).
9. **Career-timing prediction** — falls short. The outcome_claim is an untranslated machine slug, "elevated career career_discovery_event", repeated verbatim across 40+ rows with one identical window and a null base_rate. Not a sentence, not calibrated, not discriminatingly time-indexed.
10. **Remedy register** — falls short AND is a live §13.8 violation. Every remedy is a second-person command: "Recite the Mercury beej mantra… 108 times daily on Wednesday, facing east", "Donate black sesame seeds… Feed crows", "Chant the Shani Ashtottara…". This is the "you should do X" register §13.8 names as the exploitative line, not the attributive "the tradition prescribes X." The citation is a synthetic slug ("G27 remedy mercury_matrix_mantra for Mercury"), yet it is stamped classical_strength_rating 0.90. The mantra CONTENT is correct — the only favorable note in the sample — but correct content does not rescue a forbidden register.

**Ten of ten fall short. Zero reach "my own level," zero reach "above my own level," and zero "reveal things an acharya wouldn't have seen" — the discovery layer built specifically to do that produces z-scores and column names instead.**

**The single systemic diagnosis (PG1-Q1-0012, critical):** across every persisted interpretive layer, the instrument describes its own machinery — grades, z-scores, salience, consequence scores, embedding distance ("Semantic meaning-vector far from chart centroid" is the ENTIRE reasoning chain of a top discovery), internal signal keys — in place of reading the chart. Not one sampled row states an astrological mechanism in the native's own terms: which graha, in which bhava, under which dasha, producing which lived outcome, and why. **The pipeline computes structure impeccably and stops exactly one layer short of the reading.** The scaffolding is real and even admirable (confidence bands, falsifiers, the "why an acharya misses it" concept, honest uncertainty language) — but the synthesis that turns scaffolding into a reading has not been written, or if written has never run and persisted anything.

**The one fair mitigation, stated so the verdict cannot be accused of ignoring it:** L5 is sealed in explicit STRUCTURAL mode (CLAUDE.md §E) — the missing empirical CALIBRATION numbers are by design, not neglect. That is true and it is honestly disclosed. But it does not touch this verdict, because the failure here is not missing calibration — it is missing astrological PROSE. A verdict can be uncalibrated and still read like an acharya wrote it; none of these do. The gap is in the synthesis layer, not the calibration loop.

**Bottom line for the wave report:** Every other lane audited whether the architecture is sound. This lane audited whether the readings are good, and the answer is that there are no readings to be good yet — and the deterministic artifacts standing in for them fail the §J bar comprehensively and systemically, not marginally. The §J claim must be treated as ASPIRATIONAL and UNPROVEN until the serve-time synthesis path runs end-to-end, persists real readings, and those readings are put in front of the acharya bar. Nothing short of that can substantiate the mission's central promise.

---

## Method / coverage note

- Conversation-table discovery ran exactly as the charge specified (`pg_tables ILIKE '%conversation%'/'%message%'`); all conversation and message-body tables returned count 0. Confirmed the same for `llm_call_log`, `tool_execution_log`, `context_assembly_item_log`, `query_plan_log`.
- Proxy corpus judged: `mimamsa_insight_units` (46 domain-tagged verdicts), `mimamsa_predictions` (384), `bodha_discoveries` (1,275 for the native chart `482012f1-…`, 3 real classes: distributional_anomaly / embedding_outlier / latent_insight), `bodha_rm_remedy_prescriptions` (270).
- Every finding carries a verbatim DB quote (no unverifiable escape hatch used).
- Coverage shortfall on the literal "10 conversational readings" is itself recorded as the critical finding PG1-Q1-0001, with the empty-table evidence.
