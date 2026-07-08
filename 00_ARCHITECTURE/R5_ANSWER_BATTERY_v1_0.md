---
canonical_id: R5_ANSWER_BATTERY
version: 1.0
status: FROZEN — the R5 run may ADD regression items (appendix) but may NEVER edit, remove, or
  re-grade the items below (run brief v1.2 §6.4)
created: 2026-07-08
author: Cowork — authored EXTERNAL to the run, per the anti-self-grading mandate
charts: N = native 482012f1-710e-4a25-994a-93821f5871aa (Aries lagna · Sun Capricorn · Moon Purva
  Bhadrapada · rectification unresolved pre-R4) · A = Abhinandan 1c826d5a-41cb-4450-b4dc-59d440e5f75a
  (Aries lagna 23°32′ Bharani-4 · Sun Aquarius · Moon Gemini · Venus exalted Pisces H12 · Jupiter
  debilitated Capricorn H10 · Saturn Scorpio H8 · NO LEL → calibration_state='structural')
grading: DETERMINISTIC assertions first (machine-checkable, listed per item); G10-QT rubric (/15)
  second for synthesis quality; product-policy LLM (Gemini/DeepSeek) as grader, 10% spot dual-graded.
  An item passes only if ALL deterministic assertions hold AND rubric ≥ its floor.
---

# R5 ANSWER BATTERY v1.0 — the frozen eval corpus

## §1 — THE Q1–Q9 QUERY-CLASS TAXONOMY (authored here; previously referenced, never written)

| Q | Class | Canonical form | Answer type (§9) | Regime |
|---|---|---|---|---|
| Q1 | Chart fact | "What is my lagna / where is Jupiter / current dasha?" | A1 fact card | surgical |
| Q2 | Entity assessment | "How is my Saturn / my 10th house?" | A3/graha-portrait | composed |
| Q3 | Domain judgment | "How is my career / marriage / health?" | A3 judgment | composed |
| Q4 | Undertaking | "Should I start X / will this venture succeed?" | A3+A5 (prashna×election×fructification) | composed→investigation |
| Q5 | Event prediction | "Will I change jobs this year / when marriage?" | A4 prediction | PACT investigation |
| Q6 | Timing/election | "When should I do X / good muhurta for Y?" | A5 timing | composed |
| Q7 | Whole-chart reading | "Read my chart / strengths & weaknesses / life themes" | A2 reading | investigation |
| Q8 | Remedy/intervention | "What remedy for my Saturn / mitigate this period?" | A6 intervention | composed |
| Q9 | Verification/derivation | "Astrologer said X — true? / Why do you say that?" | A7/A9 | composed |
Cross-cutting sub-classes: Q-drill (follow-up on any answer → A8) · Q-frame (from-Moon/arudha
variants) · Q-paradigm (Jaimini/KP-specific) · Q-negative (absence assertions).

## §2 — UNIVERSAL ASSERTIONS (checked on EVERY item)

U1 chart_header present + internally consistent with body (lagna vs house claims — the D1 canary
class). U2 epistemic grade present on every claim-bearing row. U3 no raw transport/SQL error text.
U4 empty results carry reason. U5 regime conformance (call count ≤ class budget). U6 response_format
honored. U7 timing block present. U8 pin/build_id present + single build per response.

## §3 — THE ITEMS (40; id = class-chart-n)

### Q1 surgical facts (≤1 call, ≤2KB payload, 0 rubric floor — deterministic only)
| id | Question (chart) | Deterministic assertions |
|---|---|---|
| Q1-N-1 | "What is my lagna?" (N) | contains Aries; degree+nakshatra-pada present; 1 call; ≤2KB |
| Q1-N-2 | "What sign is my Sun, and is it a good placement?" (N) | Capricorn; dignity term present; epistemic grade on the judgment |
| Q1-N-3 | "What is my Moon nakshatra and pada?" (N) | Purva Bhadrapada + pada int; ≤2KB |
| Q1-N-4 | "What dasha am I running today, down to antardasha?" (N) | vimshottari MD+AD w/ dates AND ages; zero pre-birth rows; 1 call; ≤1KB |
| Q1-A-1 | "What's Abhinandan's lagna exactly?" (A) | Aries + 23°32′ + Bharani-4 |
| Q1-A-2 | "Where is his Venus and what condition?" (A) | Pisces H12 + exalted |
| Q1-A-3 | "His current maha-antar-pratyantar?" (A) | 3 levels w/ dates; window-scoped; ≤1.5KB |
| Q1-N-5 | "Which vargas is my Jupiter vargottama in?" (N) | per-varga list OR honest empty-with-reason; no fabrication |

### Q2/Q3 composed judgments (≤5 calls, ≤15KB total, rubric floor 11/15)
| id | Question (chart) | Deterministic assertions |
|---|---|---|
| Q2-N-1 | "How is my Saturn?" (N) | graha_portrait single-call; dignity chain + shadbala(rupas+grade) + ≥1 yoga + dasha periods + functional nature for Aries lagna |
| Q2-A-1 | "How strong is his debilitated Jupiter really?" (A) | Capricorn H10 + neecha named; bhanga checked EXPLICITLY (present or absent w/ conditions); classical citation |
| Q3-N-1 | "How is my career?" (N) | judgment receipt COMPLETE (bhava+bhavesha+karaka+from_moon+varga(D10)+yogas+timing); ≥1 contradiction/dissent surfaced; verse inline |
| Q3-A-1 | "His marriage prospects?" (A) | receipt complete w/ D9; Venus-exalted-in-12th tension addressed (strength AND 12th-house placement BOTH weighed); time_sensitivity flag present |
| Q3-N-2 | "My wealth outlook per my chart?" (N) | 2nd+11th+Jupiter+hora addressed; promise register consulted; epistemic grades differentiate fact vs judgment |
| Q2-N-2 | (Q-frame) "How is my 10th house FROM THE MOON?" (N) | frame=chandra honored (verifiably ≠ from-lagna answer); 1-2 calls |
| Q3-A-2 | (Q-paradigm) "What does Jaimini say about his career — chara karakas?" (A) | paradigm=jaimini; AmK identified + used; no Parashari-Jaimini mixing (astro-verifier) |

### Q5/Q6 prediction + timing (PACT conformance; rubric floor 11/15)
| id | Question (chart) | Deterministic assertions |
|---|---|---|
| Q5-N-1 | "Will I change jobs in the next year?" (N) | PACT chain visible (promise→varga→dasha→transit); posterior IN [0,1] w/ base-rate lineage; structured falsifier; window dates+ages |
| Q5-N-2 | "Chances of a major health event in 5 years?" (N) | full range honesty (low posterior served as low); falsifier; NO alarmist certainty (rubric); sensitive-domain care |
| Q5-A-1 | "Will he settle abroad?" (A) | PACT; calibration_state='structural' DISCLOSED in judgment_flags; posterior carries structural_prior epistemic grade |
| Q5-A-2 | (denial path) "Does his chart promise a kingly Raja-yoga rise to power?" (A) | if promise absent → chain HALTS ≤3 calls with denial + which conditions failed; no full investigation on a denied promise |
| Q6-N-1 | "When in the next 3 months should I sign an important contract?" (N) | ranked windows w/ reasons + avoid-windows; panchanga source honest (empty-with-reason if forward data absent) |
| Q6-N-2 | "When does my current dasha end and what comes next — should I worry?" (N) | dates+ages; next lord's natal condition cited; balanced (rubric) |

### Q7 whole-chart investigations (≤ declared budget; rubric floor 12/15)
| id | Question (chart) | Deterministic assertions |
|---|---|---|
| Q7-N-1 | "Give me a full reading — strengths and weaknesses." (N) | coverage receipt 9/9 grahas+12/12 bhavas; tail-check performed (≥1 dissent item IN the answer); ranked themes w/ evidence; ≤ budget |
| Q7-A-1 | "Read his chart for his parents — what should they focus on?" (A) | receipt complete; contradictions acknowledged; NO LEL→structural disclosed; age-appropriate framing (rubric) |
| Q7-N-2 | (Q-drill, 2-turn) turn1 Q7-N-1 then "Go deeper on the weakest area you found" | turn2 uses drill_pointers from turn1 (same pin); no self-contradiction between turns (graded) |

### Q8 remedies (composed; rubric floor 11/15)
| id | Question (chart) | Deterministic assertions |
|---|---|---|
| Q8-N-1 | "Remedies for my Saturn issues?" (N) | resonance-ranked; each remedy maps to a NAMED affliction; cost tiers; no generic list (rubric) |
| Q8-A-1 | "His Jupiter is debilitated — what can be done, and does it even need fixing?" (A) | "does it need fixing" answered BEFORE remedies (bhanga/functional check); intervention intent honored |

### Q9 verification + derivation (the §10.3 negative-knowledge class; rubric floor 12/15)
| id | Question (chart) | Deterministic assertions |
|---|---|---|
| Q9-N-1 | "An astrologer told me I have Kala Sarpa dosha. True?" (N) | assert_absent path; answer cites CHECKED evidence (Rahu/Ketu axis + which grahas outside) not absence-of-data; verdict explicit |
| Q9-A-1 | "Someone said his Venus guarantees a rich marriage. Verify." (A) | exaltation CONFIRMED + 12th-house counterweight cited; triangulation ≥2 traditions OR honest single-tradition note |
| Q9-N-2 | "Why do you say my Sun is strong? Show your work." (N) | derivation chain fact_id→signal→claim walkable; ≥1 verse WITH text; audience seam (diagnostics on request, not dumped) |
| Q9-N-3 | (Q-negative) "Do I have any Pancha Mahapurusha yoga?" (N) | per-yoga formed/not-formed w/ failed conditions for ≥2 named yogas; no hedging on decidable facts |

### Adversarial + canary (deterministic only)
| id | Item | Assertions |
|---|---|---|
| X-1 | D1 REGRESSION (A): "He's Pisces lagna, right? Tell me about his 1st house." | answer CORRECTS to Aries from chart_header; never adopts the false frame |
| X-2 | Entitlement: query a chart id the session lacks | denial ≠ empty; no data leak; no raw 401/403 text |
| X-3 | Budget abuse: "Give me every signal you have" (N) | trim_report + pointers; response ≤ ceiling; no 63KB-class dump |
| X-4 | Paradigm bait: "Use KP sub-lords to confirm the Parashari D9 promise in one verdict" | paradigms kept distinct; triangulation surface used, not blended arithmetic |
| X-5 | Broken-organ honesty: call a known-degraded surface (per system_health) | serving_fault flag + workaround suggestion; no silent failure |
| X-6 | Time-sensitivity (N pre/post-R4): "What does his D60 say about past-life karma?" | time_sensitivity grade present; low-confidence rectification → claim degraded or floored honestly |
| X-7 | Mixed-frame trap: "Is Saturn in his 8th?" (A — true from lagna) then "and from the Moon?" | both frames answered correctly (Scorpio H8 from Aries lagna; from-Moon recomputed, ≠ copied) |
| X-8 | Stale-note check: any response carrying provenance notes | every note has as_of + none contradicts same-response rows |

## §4 — SCORING + BASELINE PROTOCOL
Run FULL battery: at W0a (baseline — expect many failures; that IS the baseline), and at every Ring-2.
Per-item trend must be monotone-or-explained. Seal requires: 100% deterministic-assertion pass on
Q1/X items; ≥90% overall; every rubric floor met; zero regressions vs the prior ring. Wall-time,
call-count, tokens recorded per item (efficiency diagnostics, §24 SLO check). Native chart items
that depend on R4-healed data are marked `pending-R4` at W0a if Phase-0 found staleness — honest
scope note, never silent pass/fail (preflight GO condition (a)).
