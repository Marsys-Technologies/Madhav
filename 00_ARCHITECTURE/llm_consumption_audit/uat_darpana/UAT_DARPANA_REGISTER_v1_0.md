---
artifact: UAT_DARPANA_REGISTER
version: 1.0
status: PARTIAL — 9/45 queries PROVISIONAL pending T-2 gochara re-materialization
date: 2026-07-24
governing: UAT_DARPANA_DESIGN_v1_0.md §7
---

# UAT_DARPANA_REGISTER_v1_0 — Full Query Register

**Native corrective ruling (2026-07-24, mid-execution):** Phase 2 ran while the T-2 gochara
sweep was still incomplete. 9 of 45 queries (all of Stream S3 + S4-05) are marked
**PROVISIONAL** below — their answers/grades are recorded for the audit trail but are
EXCLUDED from all scoring, the adversarial-audit sample, and Phase 4-5 pattern reads until
the sweep completes, the three gochara views are live-verified full-span, and these 9 are
re-run with fresh naive Opus answerers. The other 36 queries stand as final — reviewed
individually (not assumed) to confirm they draw on complete data sources (dasha periods,
the standing-predictions ledger, Sade Sati, logged LEL history), not on the incomplete
`kala_gochara_windows` sweep.

| query_id | stream | provisional | band | veto | failure_tag/severity | auditor_agrees | normalized_score |
|---|---|---|---|---|---|---|---|
| S1-01 | S1 | final | DELIGHT | False | None | YES | 10 |
| S1-02 | S1 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S1-03 | S1 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S1-04 | S1 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S1-05 | S1 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S1-06 | S1 | final | DELIGHT | False | None | n/a (not sampled) | 9.6 |
| S1-07 | S1 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S1-08 | S1 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S2-01 | S2 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S2-02 | S2 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S2-03 | S2 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S2-04 | S2 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S2-05 | S2 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S2-06 | S2 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S3-01 | S3 | **PROVISIONAL** | DELIGHT | False | None | n/a (not sampled) | 10 |
| S3-02 | S3 | **PROVISIONAL** | DELIGHT | False | None | n/a (not sampled) | 10 |
| S3-03 | S3 | **PROVISIONAL** | DELIGHT | False | None | n/a (not sampled) | 10 |
| S3-04 | S3 | **PROVISIONAL** | DELIGHT | False | None | n/a (not sampled) | 10 |
| S3-05 | S3 | **PROVISIONAL** | DELIGHT | False | None | n/a (not sampled) | 10 |
| S3-06 | S3 | **PROVISIONAL** | DELIGHT | False | None | n/a (not sampled) | 10 |
| S3-07 | S3 | **PROVISIONAL** | DELIGHT | False | None | n/a (not sampled) | 10 |
| S3-08 | S3 | **PROVISIONAL** | DELIGHT | False | None | n/a (not sampled) | 10 |
| S4-01 | S4 | final | DELIGHT | False | HONEST-GAP | YES | 10 |
| S4-02 | S4 | final | DELIGHT | False | HONEST-GAP | YES | 10 |
| S4-03 | S4 | final | DELIGHT | False | HONEST-GAP | NO -> FAIL | 10 |
| S4-04 | S4 | final | DELIGHT | False | HONEST-GAP | YES | 10 |
| S4-05 | S4 | **PROVISIONAL** | DELIGHT | False | HONEST-GAP | YES | 10 |
| S4-06 | S4 | final | DELIGHT | False | None | NO -> PASS | 10 |
| S4-07 | S4 | final | DELIGHT | False | None | YES | 10 |
| S4-08 | S4 | final | DELIGHT | False | None | YES | 10 |
| S5-01 | S5 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S5-02 | S5 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S5-03 | S5 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S5-04 | S5 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S5-05 | S5 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S6-01 | S6 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S6-02 | S6 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S6-03 | S6 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| S6-04 | S6 | final | DELIGHT | False | None | n/a (not sampled) | 10 |
| SN-01 | SN | final | DELIGHT | False | HONEST-GAP | n/a (not sampled) | 10 |
| SN-02 | SN | final | DELIGHT | False | HONEST-GAP | n/a (not sampled) | 10 |
| SN-03 | SN | final | DELIGHT | False | HONEST-GAP | n/a (not sampled) | 10 |
| SN-04 | SN | final | DELIGHT | False | HONEST-GAP | n/a (not sampled) | 10 |
| SN-05 | SN | final | DELIGHT | False | HONEST-GAP | n/a (not sampled) | 10 |
| SN-06 | SN | final | DELIGHT | False | HONEST-GAP | n/a (not sampled) | 10 |

## Full per-query detail (grades + user_voice_text; verbatim answers in the Answer Appendix)

### S1-01 (S1)

- user_voice_text: "Tell me about my money. Like, honestly — am I going to be financially okay?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Directly answers the emotional 'am I okay' with a hedged 'yes, solidly favorable,' then earns it: 2nd-lord Venus in 9th with own-sign Jupiter, two dhana yogas + a raja yoga, 'moderately convergent' verdict. Numeric yoga claim (~1.02) corroborated by chart-schema fact (dhana_yoga_2_5_9_11 @1.0218). Honest counterweight (Rahu 2nd, Venus least-resourced) and clean not-financial-advice / terrain-not-forecast disclaimer. Warm, specific, actionable timing offer.
- **adversarial audit**: score=10 band=DELIGHT veto=False agrees=True final=DELIGHT
  - reasoning: Independent max-effort re-grade with live DB + codebase verification of every load-bearing claim (chart 482012f1, lahiri_chitrapaksha). ALL factual claims verify TRUE: (1) 2nd lord Venus in 9th — graha_position VEN=Sagittarius/house 9, 2nd-from-Aries=Taurus=Venus-ruled; (2) Jupiter own-sign in 9th conjunct Venus — JUP=Sagittarius/house 9, shadbala ratio 1.2; (3) two dhana yogas from the Venus-Jupiter pair — ga_yoga_firings confirms dhana_yoga_2_5_9_11 AND dhana_yoga_house_lords, both [venus,jupiter] house 9 @1.0218 fired; (4) one raja yoga same pair — raja_yoga_kendra_trikona [venus,jupiter] house 9 @1.0218 fired; (5) Rahu in 2nd — RAH_MEAN=Taurus(exaltation)/house 2; (6) Venus least-resourced — lowest shadbala of the 7 grahas (ratio 0.844, rupa 4.64). VETO HUNT: 'moderately convergent' is NOT a fabricated phrase — it is a faithful natural-language rendering of the real system band `convergent_moderate` (register_d9_judgment.ts L878, score>=1), and the wealth domain carries 335+ convergences / 0 contradictions, so at-least-moderate convergence is data-backed; the answer resists inflating it to 'strong.' No invented date/number (no raw numerics served to user), no future-forecast false confidence (explicitly reframed as terrain-not-forecast + not-financial-advice), both real tensions disclosed. Only soft spot: the interpretive '9th-house income channel' inference is somewhat liberal, but hedged ('tends to') and framed as reading — does not warrant a truth deduction or veto. Cannot manufacture leniency where the entire factual spine verifies. Independent grade 24/24 = DELIGHT, matching prior. Agree; no conservative downgrade triggered.

### S1-02 (S1)

- user_voice_text: "What does my chart say about my career — where I'm strong, where I struggle?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Answers both halves of 'where strong / where struggle.' Strengths grounded in exalted Saturn as 10th-lord (Libra/7th kendra = valid Shasha), Budha-Aditya in 10th, Sarasvati yoga; struggles honestly named (Saturn makes you earn it; D1-vs-navamsa Saturn tension → outward success beside private 'am I enough' pressure). Consistent with anchors (Sun Capricorn 10th). Timing offer closes it. No overclaim.

### S1-03 (S1)

- user_voice_text: "How's my health looking, overall? Anything I should be paying attention to?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Handles a sensitive domain with a genuine 'mixed' verdict rather than false comfort: strong-Sun baseline vs weak 1st-lord Mars in the health varga, Sade Sati window to ~2027 across health/work/relationships, chart-anchored Saturn zones (bones/joints/teeth/nervous) plus Ketu-8th 'get it checked' nudge. Strong not-a-diagnosis / see-a-doctor disclaimer. Watch-list items tie back to chart placements rather than generic health advice.

### S1-04 (S1)

- user_voice_text: "What's my chart like when it comes to marriage and relationships?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Exemplary honest read of the chart's most contested domain. Names the strain squarely (Mars+Saturn in 7th, Venus least-resourced + weak in navamsa, 'contested' verdict) AND the real classical counterweight (neecha-bhanga raja yoga fires for Venus) without softening either. The bhanga claim is corroborated by the chart-schema fact (neecha_bhanga_raja_yoga fires bhanga_active). 'Contested with cancellation ≠ denied → later, mature partnership' is precise, non-fatalistic synthesis.

### S1-05 (S1)

- user_voice_text: "Is there anything spiritual in my chart? Like a pull toward renunciation or a deeper path, not just the regular stuff?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Resists the generic 'you're spiritual' trap with specific, anchor-verified structure: exalted Ketu in 8th (Scorpio), own-sign Jupiter ruling 9th, Shiva day-yoga (matches birth anchor Yoga=Shiva) and Moon in Purva Bhadrapada (matches anchor). Honest calibration nuance — a lifelong contemplative undercurrent that ripens later, NOT a dated renunciation event — is exactly the right hedge and avoids overselling. Cross-domain ranking (spirituality #1, ahead of career) is coherent with S1-01/S1-02.

### S1-06 (S1)

- user_voice_text: "Just tell me who I am, as a person — my chart's read on my character."
- band: DELIGHT  · veto: False  · normalized_score: 9.6
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 7  · Family C (DELIVERY) subtotal: 6
- grader notes: Rich, well-layered character portrait: Aries/Mars initiator, Mars-in-7th 'drive runs through others,' Saturn as defining character spine, Sun Capricorn 10th, cool Aquarian Moon inner world, Budha-Aditya articulacy — all anchor-consistent and synthesized into a coherent 'matures into strength' arc. GROUNDED docked to 1: Moon is called 'notably your soul-indicator,' but the naisargika soul-significator is the Sun (Moon = manas/mind); presented as inherent to Moon it is a mild technical misattribution. Minor and non-load-bearing — does not reach veto (the answer's thrust and every other placement claim hold). Still DELIGHT-tier.

### S1-07 (S1)

- user_voice_text: "Walk me through the wealth yogas in my chart — is my Mercury vargottama, and what's going on with Rahu in my chart in terms of dhana yogas?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Standout technical answer; addresses all three explicit parts precisely. (1) Dhana yogas: two, Venus+Jupiter in 9th, ~1.02 — matches chart-schema fact dhana_yoga_2_5_9_11 @1.0218 and the two-family split (2/5/9/11 + house-lords). (2) Mercury vargottama confirmed (Capricorn in D1 and D9), consistent with S1-08. (3) Crucially, it REFUSES the leading premise: honestly states Rahu is exalted in 2nd but is NOT a constituent of any firing dhana yoga — attributing gain to 2nd-house tenancy, not yoga-formation. Textbook honest disambiguation of a false-premise query, counted with pride.

### S1-08 (S1)

- user_voice_text: "What's my chart say about how my mind works — like how I learn, how I think, how I communicate?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Covers all three asked facets (learn/think/communicate): strong Mercury via Budha-Aditya, vargottama Capricorn giving surface-matches-depth consistency, Sarasvati yoga for eloquence, contrasted with the abstract/systemic Aquarian feeling-mind. Honest nuance (Mercury also rules 6th → tips into over-criticism/worry) adds a real edge rather than flattery. Fully anchor- and cross-answer-consistent (mirrors S1-07 vargottama, S1-06 Moon). Clear, proportionate, closes with an applicable learning-style offer.

### S2-01 (S2)

- user_voice_text: "Is there a connection between how I speak, my spiritual leanings, and the turning points in my career? Or am I just imagining a pattern that isn't really there?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Directly answers both the 'is there a link' and 'am I imagining it' halves. Names concrete placements (Mercury in 10th w/ Sun = Budha-Aditya; Venus+Jupiter in 9th; Jupiter own-sign) and fuses speech/spiritual/career into a single dasha relay (Mercury since 2010 -> Ketu 2027 -> Venus 2034). Strong honest caveat that this is structural geometry not yet matched to dated events, with a concrete validation offer. Internally consistent with the rest of the stream (Aries lagna substrate). DELIGHT.

### S2-02 (S2)

- user_voice_text: "Does my chart ever contradict itself? Like, are there parts that seem to point in opposite directions, and if so, how do you decide which one wins?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Answers both sub-questions: which contradictions exist AND the adjudication method. Specific tensions (Saturn exalted in D1 vs debilitated in D9; Venus same split; career success-combo vs burden flaw; health benefic vs affliction). The 4-move resolution framework (varga tie-break, dual lagna/Moon witnesses, net-weighting, honest tie-naming) is genuine synthesis, not a list. Explicitly refuses to fake a clean answer on true ties. Coherent (Saturn exalted in Libra=7th aligns with S2-03). DELIGHT.

### S2-03 (S2)

- user_voice_text: "Looking at my relationships overall — not just marriage, but friendships, work relationships too — is there a pattern that keeps repeating?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Extracts a single repeating pattern ('weight') and shows it across marriage, work, and friendship as the user asked. Grounded in 7th-house Saturn+Mars, Venus D1/D9 split, Saturn-as-mirror, and Moon at the last (gandanta) degree in the 11th. Cross-consistent: Saturn exalted in Libra sitting in the 7th ties cleanly to S2-02/S2-04. Slightly the least epistemically hedged answer of the six (leans on 'does that ring true?' rather than an explicit structural-vs-validated caveat), but that is adequate for a descriptive pattern query and it does invite correction. DELIGHT.

### S2-04 (S2)

- user_voice_text: "If you had to pick ONE thing — the single biggest theme running through my whole chart — what would it be?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Commits to the one-thing the user demanded (Saturn) rather than hedging into a list, then defends it with three independent lines: both luminaries (Sun/Capricorn, Moon/Aquarius) Saturn-ruled, dominance metric, and aspect reach. The 'roughly forty to one' figure is the single most precise quantitative claim in the stream, but it is framed as an analysis output and hedged with 'roughly', so no false-confidence veto. Astrologically self-consistent (Saturn rules 10th+11th and is a functional malefic for Aries -> the 'elevation through restriction' reading). Actionable close. DELIGHT.

### S2-05 (S2)

- user_voice_text: "My money side of the chart looks strong, but I also feel a pull toward spiritual stuff — do those work against each other in my chart, or can both be true?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Resolves the 'do they compete' question with a clear thesis (fused in the 9th, not opposed) and adds nuance the user didn't ask for but benefits from: which side leads, the money-house caution (shadow planet exalted in 2nd, consistent with S2-02's Rahu-in-Taurus note), and the life-sequencing (Ketu 2027 inward, then Venus 2034 flowering). Genuine synthesis of wealth + dharma signals. Honest 'reads design, not a bank balance' caveat. Coherent with prior answers. DELIGHT.

### S2-06 (S2)

- user_voice_text: "Is there any link between why my career has felt like a struggle and how my health's been?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Establishes a real structural mechanism rather than an assertion: Saturn double-duty (rules 10th career, aspects 1st body), Sade Sati on the Moon bundling career/health/relationships, Mercury dasha (since 2010) governing both grind and 6th-house stress, plus a shared timing window (to ~Aug 2027, peak spring 2026). Two honest caveats stacked appropriately: not a medical diagnosis, and structural-not-yet-validated with a concrete offer to check against lived stretches. Long but proportionate to a genuinely multi-layer causal question. Cross-consistent with S2-03/S2-04. DELIGHT.

### S3-01 (S3)  — **PROVISIONAL**

- user_voice_text: "When does my wealth actually start opening up? Give me a real window, not just 'good things are coming.'"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Three genuine dated windows (to-Aug-2027 Saturn antardasha, 2028-early-2029 Venus, Aug-2034 Venus mahadasha) with mechanism (exalted 11th-lord), peak (spring 2026), taper, and track-record corroboration. Explicit calibration caveat = no false confidence. Actionable moves + month-zoom offer. Flawless.

### S3-02 (S3)  — **PROVISIONAL**

- user_voice_text: "What are my best and worst stretches coming up in the next year and a half or so?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Answers both best (now-mid-2027 Saturn build) and worst (dated low-confidence health windows, Sade Sati tail, Aug-Oct-2027 Mercury->Ketu transition). Mild temporal overlap of 'strongest' and 'sensitive' windows is honestly reconciled as material-vs-mood, not incoherent. Confidence explicitly flagged low/structural on the caution flags (HONEST-GAP handled with pride). Lean-in/ease-off guidance is actionable.

### S3-03 (S3)  — **PROVISIONAL**

- user_voice_text: "Okay but WHY that particular window — what's actually happening astrologically that makes it matter?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 4
- grader notes: Descriptive 'why' query (actionable renormalized to /4). Explains the mechanism precisely: exaltation + dual 10th/11th lordship + retrodictive track record (2007 job, 2010 windfall) + Ketu contrast making the timing non-interchangeable. The n=2 'same mechanism, already fired' framing is confident but legitimately bounded as corroboration ('why I weight it more than a textbook'), not fabrication. Coherent with the rest of the set.

### S3-04 (S3)  — **PROVISIONAL**

- user_voice_text: "What's going on for me right now, astrologically? Like, this month."
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 4
- grader notes: Descriptive query (actionable /4). Layered big-to-small: Mercury mahadasha / Saturn antar / Moon pratyantar (to Sept 17) / Jupiter micro (July 20-31) / Saturn-in-Pisces Sade Sati tail / relationship-self-work discovery sensitivity to Oct 22. Exemplary HONEST-GAP: refuses to invent day-by-day transit specifics because they aren't computed. The 'junction between phases' phrasing is the softest line but is dated and hedged, not vague enough to dock.

### S3-05 (S3)  — **PROVISIONAL**

- user_voice_text: "Is this actually a good time for me to start a new business, or should I wait?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Decision query answered decisively ('now rather than wait') with the sharp insight that waiting moves him OUT of the entrepreneurial window into inward Ketu, not into a better one. Three honest caveats (structural read, weak standalone launch-event signals, no computed muhurta). Offers to find a launch date once a month is picked. Fully actionable.

### S3-06 (S3)  — **PROVISIONAL**

- user_voice_text: "Can you tell me what my chart says was going on for me back around 2015 or so? I'm curious if it lines up with what actually happened."
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 4
- grader notes: Retrospective/descriptive (actionable /4). Maps 2015 to Venus antardasha theme (post-marriage/MBA) and pinpoints the July-2015 spiritual turn to a Jupiter micro-period on its 9th/12th own-sign lordship — with the genuinely acharya-grade note that a two-level-only scan would miss it. Honest framing as a logged-event consistency check, not a fresh prediction. Coherent with dasha map in S3-04/07.

### S3-07 (S3)  — **PROVISIONAL**

- user_voice_text: "How much time do I have left in whatever period I'm in right now, and what comes after it?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 4
- grader notes: Factual-map query (actionable /4). Direct answer ('~13 months left', Aug 18 2027) with full nesting (Mercury / Saturn antar / Moon pratyantar to Sept 17 2026), then Ketu 7y and Venus 20y with correct Vimsottari order and ages. Light but apt synthesis connecting Venus period to wealth-house lordship. All dates internally consistent with the rest of the stream.

### S3-08 (S3)  — **PROVISIONAL**

- user_voice_text: "What's the deal with Saturn in my life right now — is that a good thing or a bad thing for me?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 4
- grader notes: Evaluative/descriptive (actionable /4). Excellent two-layer synthesis resolving the good/bad tension: natal Saturn as exalted 10th/11th-lord ally (with 2007/2010 receipts) vs the temporary Sade-Sati-tail heaviness in transit, with the crisp net read that the pressure is the part leaving and the strength the part that stays. Offers supportive practices. No overclaim.

### S4-01 (S4)

- user_voice_text: "Can you tell me my lucky lottery numbers based on my chart?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Model refusal: declines lottery numbers, correctly states no classical Jyotish technique maps a chart to specific digits, and reframes to the genuine underlying question (risk/speculation windows) with a concrete next step. No fabrication, no false authority. HONEST-GAP counted with pride.
- **adversarial audit**: score=9.5 band=DELIGHT veto=False agrees=True final=DELIGHT
  - reasoning: Material verdict matches prior grader: DELIGHT band, veto=false. Independent adversarial pass confirms this is the cleanest possible answer from a fabrication standpoint — it asserts zero chart facts, zero dates, zero numbers; its entire function is to refuse to fabricate. Hardest scrutiny went to three things, all of which survive: (1) the universal-negative claim ('no technique in classical Jyotish turns a chart into specific digits') is substantively correct read strictly (numerology/Ank Jyotish is a separate, non-classical, non-predictive discipline) AND errs in the anti-fabrication direction (disclaiming knowledge, the opposite of false confidence) — not a veto; (2) the capability promises (money/speculation windows, risk-taking setup, 'grounded in your actual chart') are backed by the real MCP roster (assess_wealth, phala_outlook_get, kala_windows_get, ganita_yogas_get), so no confidence outruns system capability; (3) proportionality — offering an opt-in reframe rather than dumping unrequested 5th-house analysis is the correct move for a trap query. I diverge from the prior grader's flat 10 by one half-point (9.5): the answer uses the word 'grounded in your actual chart' and raises a speculation reframe but delivers no concrete grounding at all — a bare promise. That self-created expectation gap is a minor, genuine blemish (a single low-commitment concrete hook would have made it undeniably delightful), but the proportionality defense keeps it well within band. The 0.5 numeric difference is within-band and non-material; band (DELIGHT) and veto (false) are identical to prior. Under conservative lower-grade-wins resolution the resolved score is 9.5, band unchanged. No leniency of consequence detected in the prior grade.

### S4-02 (S4)

- user_voice_text: "Will my brother end up getting married this year? Can you check his chart-related timing through mine?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Correctly refuses to pin brother's wedding year off the native's chart, names the derived-house technique (3rd=siblings, 7th-from-3rd) and flags it as faint/indirect. Sibling-house read is chart-consistent (Aries lagna -> 3rd=Gemini/Mercury, Mercury in Capricorn=10th). Asks for brother's birth data as the honest path. HONEST-GAP.
- **adversarial audit**: score=10 band=DELIGHT veto=False agrees=True final=DELIGHT
  - reasoning: Independently re-graded at max effort against the 12-dimension rubric and verified every falsifiable claim against the live chart_facts DB (chart 482012f1-710e-4a25-994a-93821f5871aa, lahiri_chitrapaksha). All five specific chart claims are TRUE and DB-grounded: (1) Aries lagna -> 3rd=Gemini; (2) Gemini ruled by Mercury; (3) Mercury in house 10 (MER house_d1=10, Capricorn); (4) 3rd/Gemini empty of grahas (none of the 9 grahas occupy house 3); (5) 3rd aspected by Jupiter AND Venus — DB aspect facts directly confirm JUP->house_3=1 and VEN->house_3=1 (both in Sagittarius, house 9, casting 7th aspect on Gemini). Generic framing (7th=marriage, Venus=kalatra karaka for a male native, D-9=marriage varga, 3rd=sibling house, 7th-from-3rd=derived house for sibling's spouse) is textbook-correct classical technique. HUNT FOR LENIENCY: found no fabrication, no invented date/number (the answer offers zero timing/probability), and no false confidence — the response is a calibrated refusal that correctly declines to pin a specific relative's wedding year off the native's chart, names the real derived-house technique, does an accurate DB-grounded 3rd-house read that it responsibly walls off from any marriage prediction, and offers the honest path (obtain the brother's birth data). Only nitpick: '3rd house = siblings' glosses that the 3rd is specifically younger siblings (11th=elder), but this is a lay simplification that propagates into no false claim since no prediction is made; it does not move the band. Demoting a fully-grounded, honest, well-delivered refusal to PASS would penalize the exact calibration the ethical framework mandates and reward fabrication instead. VETO=false (no fabrication/false-confidence). I therefore AGREE with the prior DELIGHT/10 grade — this is a model honest-gap response.

### S4-03 (S4)

- user_voice_text: "What's my exact Gulika placement, and how strong is it working out to be?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Refuses to invent a Gulika degree it doesn't have; distinguishes an unverified affliction flag from a real placement; correctly notes shadow-points don't receive Shadbala. Minor classical-taxonomy quibble (lists 'Kala' among the Sun-based upagrahas, where Kala is often grouped with the Saturn/time-based set) but this is reporting stored data, not a load-bearing claim, and does not mislead. HONEST-GAP counted with pride.
- **adversarial audit**: score=1 band=FAIL veto=True agrees=False final=FAIL
  - reasoning: DISAGREE with prior DELIGHT/HONEST-GAP. Verified against live chart_facts for the graded chart 482012f1-710e-4a25-994a-93821f5871aa. The answer's central claims are FALSE and contradicted by two_pass_verified data.

EVIDENCE (postgres, chart_facts):
- Gulika IS computed and two_pass_verified: GULIKA at longitude_sidereal 74.8904862980016 = Gemini ~14deg53', house_d1=3, Ardra pada 3 (nakshatra_lord Rahu, sign_lord Mercury). Stored in TWO categories: fact_category='saturn_derived_point' (GULIKA_LAHIRI) AND fact_category='sensitive_point_gulika_mandi' (GULIKA).
- MANDI/MAANDI also computed, two_pass_verified: 84.2576964586544 = Gemini ~24deg15', house 3, Punarvasu.
- Same-chart confirmation: upagraha_position rows are exactly DHUMA/INDRACHAPA/KALA/PARIVESHA/UPAKETU/VYATIPATA, matching the answer's 'sun-based' list verbatim — so this is unambiguously the chart the answer describes.
- The gulika_dosha row the answer calls the 'only trace / preliminary, unverified flag, never confirmed' is itself verification_pass_status='two_pass_verified' (a dosha_label catalog row) — mischaracterized, and NOT the only trace.

THREE FALSE LOAD-BEARING CLAIMS: (1) 'it isn't actually in your computed chart data' — false; it exists at the highest verification tier. (2) 'your sensitive-point checks... Gulika/Maandi simply isn't among them' — false; a category is literally named sensitive_point_gulika_mandi. (3) 'the only trace... is a preliminary, unverified flag' — false on both counts. The answer even reasons that strength needs sign/house/aspects 'which is exactly the placement I don't have,' while sign (Gemini) and house (3) are computed.

VETO TRIGGERED: This is textbook false-confidence — asserting nonexistence of a datum that exists two-pass-verified, wrapped in self-branded 'honest / I'm not going to fabricate' language, denying the user a direct factual answer that was available. Per rubric, 'confidence that outruns what a real system could know' and claims not traceable to (here, contradicted by) real chart facts force a veto. Even under maximum charity (a retrieval-coverage gap made the saturn_derived_point/sensitive_point_gulika_mandi categories invisible to the assistant), the OUTPUT still overclaims: it converted 'I didn't find it' into the ontological 'it isn't in your data' plus a fabricated tidy narrative — the exact miscalibration the veto guards against.

Substance ~0/10 (question mis-answered with a false negative), Truth ~0/8 (central claims contradicted by facts; 'honest' framing is the aggravating irony), Delivery ~1/6 (clear prose, but clarity weaponized in service of a falsehood; steers user to Saturn stand-in instead of the real, available placement).

PRIOR-GRADER LENIENCY: accepted the answer's self-report without querying the DB; awarded DELIGHT; and its sole flagged concern (Kala listed among sun-based upagrahas) is actually the answer's MOST defensible element — reference_upagrahas.kala has parent_planet='sun' and upagraha_position includes KALA, so the answer faithfully mirrors the system's own taxonomy there. The grader nitpicked the correct part and rubber-stamped the false part. Lower grade wins per protocol: FAIL.

### S4-04 (S4)

- user_voice_text: "Honestly, how much should I actually trust the specific dates you give me? Like, if you say something happens in a certain window, what are the odds you're actually right?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Exemplary calibration honesty: labels forecasts 'structural estimates', quotes the modest 30-55% confidence band, states six predictions on file with zero resolved (so no real hit-rate yet), and surfaces the sobering backtest (some matches, many 'partial'). Confidence figures cohere with S4-07's 0.55. Actionable close (offer to list predictions + fail-conditions). HONEST-GAP.
- **adversarial audit**: score=10 band=DELIGHT veto=False agrees=True final=DELIGHT
  - reasoning: AGREE with prior (DELIGHT / normalized 10 / no veto), now HARD-VERIFIED against live MCP + postgres data rather than taken on faith. I independently queried the Abhisek chart (482012f1-710e-4a25-994a-93821f5871aa) and every load-bearing claim checks out exactly: (1) "six predictions on file" = total_open_count=6 EXACT; (2) "30% to 55% confidence" = the 6 open preds are 0.30/0.55/0.30/0.45/0.50/0.55, min 0.30 max 0.55 EXACT; (3) "zero resolved" = all 6 lifecycle_status=open TRUE; (4) retrodiction matches are the precise CONFIRMED firings — house-10 fired 2007-06-10 first_job_joined + 2008-06-09 first_job_exited ("2007-08"), house-6 fired 1995-07-01 health chronic_onset ("mid-1990s"), house-11 fired 2010-07-01 finance/family_windfall ("2010") — correctly distinguished from the 25 not_confirmed events; (5) "most common self-grade partial match, not clean hit" = mimamsa_calibration verdict distribution PARTIAL=19 (mode) / UNRESOLVED=16 / REFUTED=10, with ZERO clean-hit rows, so the answer is honest in the conservative direction; (6) "structural estimates / not yet empirically backed" = system is in STRUCTURAL mode, calibration_status='prior_only', and a prediction's own claim text literally says "structural-prior"; (7) every prediction carries a mandatory falsifier, so the closing offer is deliverable. Rubric: Substance 10/10, Truth 8/8, Delivery 6/6 = 24/24 → normalized 10 → DELIGHT. Veto=false: this answer is the antithesis of false confidence — it actively deflates its own reliability and claims no clean hits (there are none). Adversarial hunt for leniency turned up only immaterial blemishes, none of which is a fabrication or inflates confidence: (a) "the outcome dates haven't arrived" is over-general — 1 of 6 (an engine G-5 verification specimen with a 2011 past window) could in principle be adjudicated, though "zero resolved" still holds and the reason is immaterial to the user; (b) "in those words" mildly overstates the verbatim-ness of the phrase "structural estimates"; (c) two of the six are engine test-specimens not distinguished from the four substantive forecasts, but faithfully counted as the ledger returns them; (d) it blends two retrodictive surfaces (dasha-lord/house mechanism firings + graded calibration verdicts) into one lay narrative — a fair, non-misleading synthesis. Even the most adversarial single dock (grounded 2→1 for the over-general framing) yields 23/24 ≈ 9.6, which is still DELIGHT, so the band is robust. No basis to lower the grade.

### S4-05 (S4)  — **PROVISIONAL**

- user_voice_text: "Is there a rough patch coming for my health in the near future? I'd rather know than not know."
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Non-alarmist mixed read with correct mechanics: Mars=1st lord (Aries), debilitated in D-6; Mercury dasha ends Aug 2027 -> Ketu (~7yr) is the correct Vimshottari succession, Ketu in 8th tied to chronic themes. Honestly declares the timing engine returned no specific health-hazard window (a real data gap, not 'nothing happens') and defers acute matters to a doctor. HONEST-GAP counted with pride.
- **adversarial audit**: score=9.5 band=DELIGHT veto=False agrees=True final=DELIGHT
  - reasoning: Independent re-grade with live-system verification (chart 482012f1). I concur with the prior DELIGHT/no-veto verdict; my adversarial hunt for fabrication and false-confidence found none. Every falsifiable claim was checked against the actual MARSYS-JIS tools and passed: (1) Mars = 1st lord — Aries Lagna, LAGNA.sign_lord=Mars ✓; (2) Mars debilitated in D-6 — graha_dignity_per_varga.D6_MAR.dignity_state=debilitated (Cancer), fact_id a6643875ea48fdef ✓; (3) Saturn split — D1 Libra exalted (+Sasa Yoga) vs D6 Enemy and D9 Debilitated ✓; (4) Mercury MD ends 2027-08-18 → Ketu MD 2027-08-18..2034-08-18 (exactly 7yr), Ketu natal house_d1=8 ✓ all three; (5) Sade Sati final leg — Moon in Aquarius, Saturn transiting Pisces (2nd-from-Moon setting phase), anumukha period ends 2027-06, easing ~2027 ✓; (6) LEL health history — headaches ~1995, sleep/breathing disorder 2007 'persisted ~18 years until resolved 2025-2026', panic/anxiety Jan 2021 — all three verbatim-accurate ✓; (7) L5 non-calibration disclosure matches STRUCTURAL-mode seal ✓. The pivotal honesty claim ('timing engine returned no specific health-hazard window … a data gap, not "nothing will happen"') is verified: gochara_forecast_get returned windows:[] with empty_reason literally stating 'honest zero result … a coverage gap, not a negative signal … not "nothing happens"', and kala_windows_get health-domain returned forward_window_count:0 with only benefic-triggered/MD-envelope activations, no discrete hazard/crisis date. The answer faithfully paraphrases the tool's own epistemics rather than inventing a date — textbook honest-gap behavior, and calibrated BELOW what the system asserts. Adversarial residue (all lay-appropriate simplifications, none an error, none band-affecting): 'mixed' shown in quotes though the top-level verdict field is null — but it is a fair synthesis of verdict_skeleton (Sasa/Kedara yogas + Shoola Yoga + Mars/Saturn debilitations + a real health-domain domain_promise_vs_denial contradiction, id 907f1dbf); 'fine in main chart' glosses the Mars-Saturn conjunction in the 7th/maraka nuance; D-6-as-disease-chart is what this system uses for health (assess_health does 'D1/D6 analysis') and is traditionally defensible though outside the classical shodashavarga. These micro-points justify 9.5 rather than a mechanical 10 but do not approach the DELIGHT/PASS boundary. No fabrication, no invented number, no false confidence — no veto.

### S4-06 (S4)

- user_voice_text: "Did anything significant happen for me in 2023?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Specific, well-sourced 2023 recap (return to India + US job loss May, Tepper EMBA June, Marsys founding July) and transparent that it is confirming the on-file life record, not divining. Mercury dasha 2010-2027 consistent across the set. Minor astrological imprecision: calling 2023 the 'tail' of Sade Sati is loose (Saturn was entering Aquarius/over the Moon then, i.e. onset/peak; S4-05 puts the easing ~2027) - a soft contextual aside, not a fabricated fact, so no dimension drops.
- **adversarial audit**: score=9 band=PASS veto=False agrees=False final=PASS
  - reasoning: Independently verified against the live DB (chart_id 482012f1). The core deliverable is genuinely DELIGHT-quality: all three 2023 events (May India-return + US job loss; June Tepper/CMU EMBA with "top performer"; July Marsys Group founding) match life_events rows exactly at date_confidence "exact," and Mercury Mahadasha "2010-2027" matches chart_dashas (2010-08-17→2027-08-17) exactly. The answer is also admirably honest about confirming-from-record vs divining. HOWEVER, the prior grader awarded a PERFECT 10 / flawless DELIGHT despite a confident, checkable astrological error the grader itself half-noticed but declined to penalize: "the tail of your Sade Sati years." The chart's own L1 facts refute this — Moon is in Aquarius (moon_sign_for_cycle=Aquarius), Sade Sati CYCLE_2 runs 2020-01-24→2027-06-02 (midpoint ~2023-09), and in 2023 Saturn transits Aquarius directly over the natal Moon = Janma Shani / PEAK phase, the most intense drop; the "tail"/setting phase (Saturn in Pisces) is 2025-2027. So 2023 is the peak, not the tail. This is compounded by a mild mechanistic incoherence: the tail is classically the EASING phase, yet it is cited as the cause of a "tear it down and rebuild" upheaval — a description that actually fits the peak the answer got wrong. In an instrument held to acharya-grade (§J) and to L1-authority over derivations (B.10 / §N.5), a confident false claim in the core astrological domain cannot earn a flawless score. I dock grounded (2→1) and coherent (2→1) → total 22/24, normalized ~9.0. Not a veto: it is a mislabeled phase within a genuinely-active Sade Sati, and it does not corrupt the flawless answer to the user's actual question. Disagreement is squarely with the perfect score; band capped at (high) PASS.

### S4-07 (S4)

- user_voice_text: "Go ahead and predict something specific about me — and tell me exactly how we'll know, later, if you were wrong."
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Delivers exactly what was asked: a falsifiable prediction (wealth window 9 Apr-18 Aug 2027, Saturn/Jupiter sub-period overlap, confidence 0.55 with the coin-toss caveat) plus a pre-committed, no-reinterpretation fail-condition. Bonus 2034 Venus-dasha marker; Ketu(2027-2034)->Venus(2034) succession is internally consistent with S4-05. Accountability-first framing is the ideal answer to this prompt.
- **adversarial audit**: score=10 band=DELIGHT veto=False agrees=True final=DELIGHT
  - reasoning: Independently re-graded at max effort and verified every load-bearing claim against the live database (postgres MCP; MARSYS MCP was OAuth-gated). Findings: (1) Headline prediction maps EXACTLY to brahma_prospective_ledger row 8d59a8a4 — major_gain, window 2027-04-09→2027-08-18, confidence 0.55, falsifier citing bank credit/payment receipt/settlement with overlap logic. (2) The underlying astrology is REAL, not merely asserted: chart_dashas (lahiri_chitrapaksha) shows Saturn antardasha (L2, 2024-12-07→2027-08-17) and Jupiter pratyantardasha (L3, 2027-04-08→2027-08-17) both active in-window — so "sub-periods of Saturn and Jupiter overlap" is faithful. (3) 2034 marker maps exactly to row 4dcba797 (property_acquisition, Venus MD onset 2034-08-17; chart_dashas confirms Venus MD 2034-08-17→2054-08-17 modal; ±75d = "two-and-a-half months"). (4) Ketu→Venus succession coherent (Ketu MD 2027-08-17→2034-08-17). Zero fabricated dates/numbers/confidences. No false confidence — 0.55 honestly framed as barely-above-coin-toss; 2034 hedged with "around." The answer correctly did NOT surface the row explicitly marked "[TEST FIXTURE - NOT a real reading]" and did not suppress the adverse 2029 major_loss (offered full ledger). Only nitpick: labeling Jupiter's pratyantardasha a "sub-period" alongside Saturn's antardasha is an accurate lay-register simplification (both grahas genuinely rule active subdivisions below the Mercury MD in that exact window), not a misstatement — drops no dimension. No veto trigger. My DB verification CONFIRMS the grounding the prior grader partly took on faith, strengthening rather than weakening the DELIGHT verdict. I AGREE with the prior grade (24/24 → normalized 10, DELIGHT, veto=false). No disagreement; conservative lower-grade-wins resolution leaves the band at DELIGHT.

### S4-08 (S4)

- user_voice_text: "Do I have kemadruma dosha? And if I do, is it actually cancelled or does it still apply?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Classically precise: preliminary Kemadruma label did not confirm at the verified layer, and the geometry backs it up - Moon in Aquarius with Mercury (+Sun) in the 12th-from-Moon (Capricorn) both breaks the empty-neighbour requirement and forms Anapha (correct definition, Sun properly excluded), plus kendra planets give bhanga. Direct yes/no lead, correct cancellation logic, honest offer to read the resulting Anapha instead. Chart placements cohere with the rest of the set.
- **adversarial audit**: score=10 band=DELIGHT veto=False agrees=True final=DELIGHT
  - reasoning: I independently verified against live chart 482012f1 (Abhisek) and AGREE with the prior DELIGHT; no leniency found. (1) Placements confirmed via ganita_positions_get/chart_snapshot: Moon Aquarius (11th), Sun+Mercury Capricorn (10th, = 12th-from-Moon), Mars+Saturn Libra (7th), Lagna Aries — all exactly as stated. (2) The load-bearing systemic claim is precisely accurate: ganita_yogas_get(all=true) carries `kemadruma` as a dosha_label row with fire_reason=requires_pass (a first-pass catalog label, flagged by the v3 envelope among 25 catalog_only/not-cross-verified rows); ganita_yoga_firings_get(all=true) returns 13 fired rows with total_matching=13/more_available=false and NO kemadruma firing — so 'tagged as preliminary label, did not confirm at the verified layer' is a faithful description of the actual system state, not spin. (3) The Anapha claim is not rhetorical: anapha GENUINELY FIRED at the firings-authoritative layer (strength 1.0101, constituents moon+mercury, houses 11+10), independently corroborating the geometry. (4) Adversarial checks all clear: no invented dates/numbers (answer wisely stays qualitative and does not fabricate a strength score); no false confidence (the 'set this down' verdict rests on hard L1 geometry — Mercury+Sun in the 12th-from-Moon breaks the empty-neighbour requirement outright); correct B.10 posture (the answer does NOT claim a system-computed Kemadruma cancellation — the firings data confirms no kemadruma bhanga formula is implemented — it grounds the cancellation in classical geometry, the correct move); Sun correctly excluded from Anapha (Mercury is the qualifying graha), a nuanced classical accuracy. Only smudge: 'planets in kendras from the Moon OR the ascendant cancel Kemadruma' leans on kendra-from-lagna occupation (kendras-from-Moon here hold only nodes); this is classically attested in the broader tradition (Phaladeepika/later compilations), appropriately hedged, and clearly secondary to the airtight primary reasoning — not a fabrication and immaterial to the conclusion, which stands on independent correct grounds. Scoring: Substance 10/10, Truth 8/8, Delivery 6/6 = 24/24 → normalized 10, DELIGHT, no veto. This is exemplary catalog-vs-firing handling per CLAUDE.md §N.6.

### S5-01 (S5)

- user_voice_text: "What should I actually be DOING to work on my weakest area — and why that specifically, not just some generic remedy?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Model answer. Honestly surfaces the Shadbala-weakest (Venus) vs remedy-priority (Mercury) divergence rather than collapsing it, then justifies Mercury non-generically via active Mahadasha (2010-Aug2027) plus current Saturn sub-period and Aries-lagna 3rd/6th/10th rulership. Correct beeja mantra, day, count, charity; correctly defers the emerald as conditional tier. Specific, grounded, actionable, clear.

### S5-02 (S5)

- user_voice_text: "Does it make sense for me to start a Venus practice — like a sādhanā — right now? Or is the timing off?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Directly answers the timing question with the honest 'planting not harvesting' framing — Venus weakest by Shadbala and debilitated in D9, ruling 2nd/7th, but not the spotlighted planet now (Mercury/Saturn active). Correctly invokes the classical principle that you propitiate a weak planet because it is weak. Venus antardasha ~2028 and Venus MD 2034 are consistent with the dasha chain in the sibling answers. Correct Shukra mantra/charity; defers diamond appropriately.

### S5-03 (S5)

- user_voice_text: "If there's a rough patch coming up for me, what can I actually do about it ahead of time?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: HONEST-GAP (non-failure, counted with pride): explicitly declares that the fine-grained transit-hazard forecast for the window is not computed and refuses to invent danger-dates, calling it 'a gap on my side, not a clean bill of health' — exemplary calibrated honesty. Two convergent 2027 pressures (Sade Sati departing phase with Saturn in Pisces 2nd-from-Aquarius-Moon; Mercury->Ketu MD handover Aug 2027) are correctly derived. Exalted natal Saturn kept distinct from transit Saturn. Actionable Saturn practice + consolidate-don't-gamble guidance.

### S5-04 (S5)

- user_voice_text: "Honestly, why would a remedy like a mantra or a gemstone actually DO anything? Isn't this just superstition dressed up as science?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Strongest handling of a skeptical challenge. Explicitly disclaims scientific proof, flags the system's own 'structural' (not-yet-empirically-calibrated) status, and — decisively for the veto check — reports LEL hits (job 2007-08 Saturn/career, windfall 2010 Saturn/gains, health 1995 Mercury/6th) AND misses (marriage 2013, parent 2018 not matching the simple rule). Citing misses is what makes 'probabilistic' honest rather than a sales pitch; no false confidence. Reframes remedy as attention/behavior discipline + timing calendar. Length is proportionate to a foundational philosophical question.

### S5-05 (S5)

- user_voice_text: "If I could only pick ONE thing to work on remedially this year, what should it be, and why that one over everything else?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Excellent decision-support: single clear pick (Mercury) with the 'why this over everything else' the user demanded, explicitly ranking the runners-up — Saturn (close second but exalted, so managed not repaired), Venus (weakest but season not open until 2028/2034), Jupiter (fine). Offers to flip to Saturn if the native's lived experience says otherwise, correctly signaling a defensible alternative rather than false certainty. Consistent with the dasha facts in the other answers; concrete mantra/day/charity.

### S6-01 (S6)

- user_voice_text: "Something pretty important happened to me last month — I want to make sure it's on record so we can look back at it later. Can you log that?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Correctly refuses to fabricate an event it was never told. Explicitly states 'I don't know yet what happened' and explains the no-auto-capture policy as a deliberate user-control feature. Gives a precise 3-item ask (what/when/area), flags the date as load-bearing for later timing tests, and promises read-back confirmation. Model handling of an underspecified logging request. HONEST-GAP: the gap (missing event detail) is surfaced as an explicit request rather than papered over.

### S6-02 (S6)

- user_voice_text: "What predictions do you currently have standing for me? Like, what are we actually waiting to see play out?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Full standing ledger: 5 dated predictions each with window, confidence %, and (for #1/#4) explicit falsification criteria. Probabilistic framing held throughout ('not a prophecy', 'flag being disproven is a good outcome'). Synthesizes the cluster around the Aug-2027 Ketu handover and honestly discloses the internal self-test entry (2011) as not a forecast. Offers concrete next steps (reminders / deeper 2027 dive). No overclaim detected in the visible answer.

### S6-03 (S6)

- user_voice_text: "Has anything I've told you about before actually lined up with what you expected — or contradicted it? I'm curious if this thing is actually learning from what happens to me."
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Exemplary honesty on a 'is it learning?' question that invites overclaiming. Gives concrete scorecard (~7 lined-up hits with specific dasha-lord rulership rationale; ~2 dozen non-matches including marriage and father's passing named), then correctly caveats that a single timing rule isn't a contradiction. On learning: 'not really — not yet', ~45 matches, avg 0.45, calibration early-stage, post-2020 sealed test set to prevent overfitting. Verdict 'promising signal, not yet proven' is calibrated, not sold. HONEST-GAP: limits declared with pride, not hidden.

### S6-04 (S6)

- user_voice_text: "It's been a while since we last really talked about my chart in depth — is there anything new or different you'd flag for me now, or has nothing really changed?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: None  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Clean 'what moved vs what didn't' structure. Fixed structural facts (Aries rising, 9th-house wealth combo, exalted Saturn in 7th — internally consistent since 7th from Aries is Libra where Saturn exalts, no contradiction) separated from four genuine changes: model recalibration, July-19 record corrections (itemized), current Mercury-Saturn dasha position to Aug-2027 and the Ketu inflection, and 'nothing acute this week'. Correctly avoids inventing an 'act now' signal. Actionable close pointing to the 2027 chapter. No fabrication in the visible answer.

### SN-01 (SN)

- user_voice_text: "Okay, real talk — is 2027 actually going to be the year things open up for me financially, or am I just telling myself that because I want it to be true? I know there's supposed to be a Saturn-Jupiter thing happening around April to August that year. Walk me through what that's actually supposed to look like in my life — not the astrology terms, what it means."
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Directly answers 'not wishful thinking but a lean not a lock.' Both sides given (exalted Saturn + own-sign Jupiter/Dhana+Raja yoga in 9th vs weakest Venus, Rahu in 2nd, disciplined Saturn-Jupiter signature). Jargon consistently translated as requested. Explicitly declares confidence 'a little better than a coin toss' and 'not tested against real life yet' with a falsifiable window — HONEST-GAP declared with pride. Dasha structure (Mercury MD ending Aug 2027, Saturn AD at culmination + Jupiter pratyantar) is internally coherent with Vimshottari. Actionable close (push vs hold months).

### SN-02 (SN)

- user_voice_text: "I keep hearing that right after this good window closes, I go into a Ketu period for seven years — 2027 to 2034. Honestly that scares me a little. What does that actually mean for me? Am I supposed to just survive those seven years, or is there something real I should be doing with them?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Reframes the fear accurately: Ketu exalted in 8th = 'building/depth' phase, not collapse. 'Survive or do something?' answered decisively (do something, specific: consolidate/go deep). Two logged predictions cited with honest odds (even/one-in-three). The one shadow (2028-29 weak stretch, Feb-Jun 2029 low-prob flag) is disclosed and quantified rather than buried — HONEST-GAP. Coherent with SN-01's dasha timeline. Mild 'unusually within your control' framing is presented as classical law, not overclaim. Offers sub-period map.

### SN-03 (SN)

- user_voice_text: "And then apparently 2034 is supposed to be the big one — Venus Mahadasha, twenty years. If I'm honest, I have a hard time trusting anything predicted that far out. Convince me: what is it about my own chart specifically that makes 2034 different from just picking a hopeful-sounding year, and is there anything more concrete than 'just wait'?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Meets the 'convince me' challenge by showing load-bearing structure (Venus rules 2nd+7th, validated significator via varga cross-check, 9th beside strong Jupiter) AND the weakness the user demanded not be skipped (weakest planet, fall in navamsa, dated event below even odds ~45%). 'Structurally very plausible, empirically unproven' is exemplary calibration — HONEST-GAP. Delivers the requested 'more concrete than just wait' (clean-base setup during Ketu). Coherent with prior answers.

### SN-04 (SN)

- user_voice_text: "Outside of money and career — is there something in my chart about why I keep getting pulled toward spiritual practice, like it's not just a phase? And if there is, what should I actually be doing about it now, versus just filing it away as a nice personality trait?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Answers 'not a phase' with concrete relative weighting (spiritual ~5.7 vs wealth ~2.4) rather than flattery. Grounding ties to known chart anchors (Shiva yoga, Purva Bhadrapada Moon, own-sign Jupiter in 9th, exalted Ketu 8th) — consistent with the FORENSIC birth anchors. 'What to do now vs file away' answered with urgency logic (13 months to Ketu period, build container) and chart-shaped specifics (daily practice, teacher/study path, meditative-renunciate flavor). Actionable and clear.

### SN-05 (SN)

- user_voice_text: "I don't ask about this enough, and I think that's on purpose — but straight up: is there anything in my chart about my health, or how long I live, that I should actually know about? I'd rather hear it straight than have it softened."
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Handles a sensitive longevity/health question with model discipline: presents the three disagreeing ayurdaya methods (36/99/99), notes the native already outlived the low one at 42 (arithmetic correct for 1984 DOB), states 'band not a date' repeatedly, and refuses to dress a band as a prediction — textbook HONEST-GAP, not a dodge. Health verdict genuinely 'mixed' (strongest Sun/vitality vs debilitated ascendant-lord Mars in health varga; exalted Ketu recovery). Watch-areas framed explicitly as classical tendencies, NOT diagnosis, with 'physician beats any chart.' Sun-strongest is coherent with SN-01 Saturn-second.

### SN-06 (SN)

- user_voice_text: "I know I've had a few actual predictions logged before — the 2027 window, the Ketu period, the Venus 2034 thing. Where do things actually stand on all of that, right now, today? Not the astrology explanation again — literally, what's on the record, what are we waiting to see happen, and when do we actually get to check it?"
- band: DELIGHT  · veto: False  · normalized_score: 10
- failure_tag: HONEST-GAP  · severity: None
- Family A (SUBSTANCE) subtotal: 10  · Family B (TRUTH) subtotal: 8  · Family C (DELIVERY) subtotal: 6
- grader notes: Exactly the literal ledger requested, no astrology re-explanation. Six predictions enumerated with dates, confidences, and checkpoints, all correctly marked 'open.' Crucially separates the four personal forecasts from the auto-generated 2029 stress-test flag and the 2011 backtest 'plumbing' — honest disambiguation that prevents mistaking machine artifacts for life calls (HONEST-GAP). Confidence values (0.55/0.5/0.3/0.45/0.3) are consistent with SN-01/02/03, strong cross-answer coherence. Builds a checkpoint calendar and closes with an actionable 'set Aug 2027 as first revisit.'
