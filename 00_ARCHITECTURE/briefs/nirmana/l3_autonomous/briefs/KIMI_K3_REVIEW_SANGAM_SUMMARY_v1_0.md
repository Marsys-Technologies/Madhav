# Kimi K3 (effort=max) review — layman summary of the seven Saṅgam rulings
# generated 2026-09-23T02:03:39+05:30 via: kimi -m kimi-code/k3 -p <KIMI_REVIEW_PACKET_SANGAM_SUMMARY_v1_0.md>; k3 default_effort=max, thinking.effort=max

• I'll review the summary against the source documents. Let me read the references first.

• Now my prior recommendations, the plan §8, and the optional depth files.

• I have everything I need: the sheet (291 lines), my own K3 recommendations, plan v0.4 §8, the FINAL packet, and the last 15 EVENTS.jsonl entries carrying today's corrections. Here is the review. No file written.

  ---

  # Review — the layman summary of the seven Saṅgam rulings

  Tagging convention as required: **[D]** doctrine (text named) · **[P]** practice · **[J]** judgment · **[U]** unverified. Every number below is attributed to its source document, not asserted by me. Where I did not or cannot check a thing, I say UNVERIFIABLE.

  ## A. Fidelity — does the summary say what the sheet says?

  **M-1.** Mostly faithful, with three distortions.
  - "Western-style angles (60°, 90°, 120°) that Vedic texts don't use" — **overstated**. The angle *values* 60/90/120 appear in BPHS 26.6–8 as virupa slab boundaries (verified verbatim, BP1:16605-16652, per the sheet). What is Western is the *symmetric aspect set* `[0,60,90,120,180]` passed at Saṅgam's call sites (`engine.py:464-467`, `:213`, `:1148-1150`, per the sheet's 2026-09-23 correction). The defect is symmetric/unsigned application and wrong-side search for the special aspects — not the existence of those numbers in the texts. [D: BPHS 26.6-8 / P]
  - The proposal drops the **fractional slabs (¼/½/¾)** that the sheet's contract (b) ships in v1, and drops the **Tājika motion qualifier (apply/separate/station) folded into all contracts** — the sheet's ordering actually has Tājika twice (qualifier everywhere; full aspects only on the annual route). The summary renders it once, "only for annual questions." Weaker than the sheet. [D: BPHS 26.2-5; Hāyanaratna 3.3 [D-online, not re-verified by author]]
  - The five-way node split is compressed to three surfaces. The essentials survive (L1 mean / scanner true / L0 store true under a mean contract), but the legacy `l1_positions` chain and the `bg_cohort` writer (both TRUE, the latter "verified, not [U]" per the sheet) disappear — and with them the true blast radius of the repair. [P, per sheet M-1d]

  **M-2.** The central claim is verbatim-faithful: 3 = fear, **4 = fear**, 5 = accomplishment (Phaladīpikā 23.11, re-verified online by the author). I note with approval that my "0 = loss of life" — which the author could not find on the page and tagged [U] — is correctly *absent* from the summary. Good discipline. "The check has been dead" faithfully renders "C7 has never fired." Two weakenings: the sheet's verdict is "every verdict **conditioned by the transiting planet's dignity in the sign** (23.10)" — the conditioning is gone from the summary; and the three-state encoding is presented without the follow-up question (does 4 *lean* adverse within indeterminate) that the sheet explicitly reserves for the native.

  **M-3.** The two halves, the landed code, and the blocking status are faithful. One substantive narrowing: the summary's bounded fast tier is "**Moon/Sun contacts only**." The sheet's recommendation enumerates five witnesses — Moon's house-from-Moon (Ph. 26.2/26.12), **tārā-vedha stars (26.26-29)**, **laṭṭā (26.42-44, producer already served)**, Sun's house/saṅkrānti (26.9-11, 26.29), decanate phase (26.25). The summary silently deletes the two cheapest and most textual members (laṭṭā reuses an existing producer; tārā-vedha was verified this session per my notes). Also dropped: "no cap" and "evidence count unchanged," the two disciplines that keep children from inflating witnesses. This is the summary's single largest deviation from the sheet. [D: Phaladīpikā 26 / P]

  **M-7.** Faithful on the defect ("score exactly 0 — the window vanishes" = the sheet's S11 `[0,1,1] → 0.0`) and on the doctrine (a nīca lord delivers *trouble*, not silence — BPHS 47.3-4, verbatim BP2:8939-8960). Two slips: the sheet's recommendation is **four fields** (`activity`, `valence`, `applicability`, `availability`); the summary reduces it to two ("intensity and valence as distinct fields"). And "three independent texts" inflates the sheet's "three independent **anchors**" — two of the three anchors are from the same text (Phaladīpikā 23.10 and 23.23-24), the third is BPHS 47.3-4. [D]

  **M-4.** Faithful on the table (BPHS 7.1-8, verbatim BP1:7569-7593) and on no-veto and line-by-line lords. One conflation: "evil D30" merges the *textual* domain assignment ("evil effects from Trimsamsa" — doctrine) with the *proposal* "D30 as the DOSHA-predicate varga," which the sheet is careful to mark "a proposal to rule, not doctrine" ([J], mine originally). A ruling document must not let a proposal ride in dressed as a verse.

  **M-5.** Faithful on episode-with-children, no default peak, occupied days not rows. Dropped: the *reason* no default peak — BPHS 27.21-23 gives vakra (retrograde) the maximum ceṣṭā-bala of 60 (verbatim BP1:22725-22742), so the retrograde pass is the *strongest* phase and no pass is the automatic event date. Without that reason the recommendation reads as arbitrary convention; with it, it is doctrine. Also dropped: aborted-approach children (`approached, never perfected`) — which the sheet's author called "a real gap in my plan — adopt." The summary's premise "three rows, counted as three witnesses": consistent with the sheet's `ka_taranga` finding (per-row monthly averaging, confirmed at `ka_taranga.py:161-169`), but the exact "witnesses" phrasing I did not re-verify — UNVERIFIABLE by me, no objection.

  **M-6.** The five conditions are all present and correct, and the closing line is the sheet's own. One precondition halved: the sheet opens consumption "once R-5 identity is qualified in the harness **and outcomes are on two axes**." The summary keeps only "identity is stable."

  **Attention paragraph.** "True Rāhu is Rohiṇī pāda 4, mean is pāda 3" — both pāda assignments match the sheet, but the sheet is scrupulous about their *unequal standing*: pāda 3 is L1's own cited fact (`060bb63b81a073bb`, `RAH_MEAN.pada = 3`), while pāda 4 is an author computation on Swiss (50.049248° at the L1-pinned instant, 177″ margin, per the sheet) with **no L1 fact behind it**, and all cited facts are `verification_pass_status = single`. The summary presents the two numbers as equally grounded. The native is entitled to the asymmetry.

  ## B. What the layman framing loses — material omissions per item

  **M-1 loses three native-facing questions entirely:**
  1. **The legacy scan's fate.** Sheet question (b): "Retire the legacy scan after one generation, or sooner?" Not in the summary at all.
  2. **Node dṛṣṭi (M-1e).** Sheet question (e): "Any graha-dṛṣṭi for Rāhu/Ketu — which houses, on the authority of which text?" This is a question *only the native can answer* (it is their school's position), and the summary never asks it. If unanswered, nodes ship as gochara agents and targets only — the native should know that is the default their silence selects. [U per corpus anchors; the exclusion inverts the day a ratified verse is produced]
  3. **The whole-sign option** for cusp targets (sheet question (c) offers Placidus-as-stored / Śrīpati / whole-sign). And the two guards that make the author's position safe: "house system recorded on every row" and "Śrīpati only as a ratified variant with its own L1 amendment." The summary's "not a third house system" reads as foreclosure; the sheet's is a reversible default.

  **M-2 loses:** the dignity conditioning (23.10); the sub-questions (b) does 4 lean adverse, (c) BPHS bands primary with Phaladīpikā alternate, (d) does the 6/8/12 inversion (Santhanam's gloss, not verse — BP2:42358-42369) ship at all; the **producer completeness receipt now** (missing planet → fabricated zeros, unrecoverable at reader level, RR-02); and the cross-stream lock — whichever AV source is admitted, **Kshetra must consume the same one**, one AV verdict per instant (U02). A M-2 ruling made from the summary alone would not know it is also setting Kshetra's input.

  **M-3 loses:** the five-witness enumeration (above); "evidence count unchanged / no cap"; question (d) — is the Sun in the slow set as a calendar witness (§4.5 lists Saturn/Jupiter/Rāhu/Ketu only); question (e) — mark the READY prompt SUPERSEDED-and-reissued; and the vedha-kind qualification mirrored from the Kshetra session (`house_vedha` applied; `sarvatobhadra`/`latta` unqualified until source-qualified; DATE-grain `precision_regime`). The owner-naming duty — the one thing only the native can do — is, to the author's credit, the best-rendered point in the whole summary.

  **M-7 loses:** the two missing fields; the fact that **genuine gates survive** where classical (orb of light, itthaśāla motion, route eligibility) — without this clause, "dignity moves from gate to sign" can be misread as "nothing gates anything"; legacy `kernel_version` never pooled; and sheet question (d): "Is there any configuration in your practice that produces *nothing* (as opposed to evil)?" — again a question only the native's practice can answer, dropped.

  **M-4 loses:** the cancellation-evidence precondition (without a nīca-bhaṅga detector, `varga_condition` over-reports adversity — my original cost note, which the author's position absorbed); the new L1 dependency (`chart_divisionals`, with explicit availability states); and the doctrine-carrying drekkāṇa annotation (BPHS 47.3-4: first/second/third drekkāṇa → start/middle/end, reversed when retrograde, nodes always reversed) — which the sheet's author said "improves on my plan."

  **M-5 loses:** the vakra = 60 reason; aborted approaches and `truncated: start|end`; the aggregation grain's full key — occupied-day union per month **per (method-contract × valence-sign)**; and the `ka_vighnakara` decision (learn child variation or declare non-consumption).

  **M-6 loses:** the two-axis outcomes precondition; the honest declaration "no classical basis — and saying so is part of the discipline"; and question (c) — who adjudicates `ambiguous`.

  A pattern worth naming: the summary systematically drops the **questions only the native can answer from their own practice** (node dṛṣṭi, does-anything-produce-nothing, the lean of 4, who adjudicates ambiguous, minimum n). Those are precisely the items where "agree" is not available — they have no default the author can supply.

  ## C. Where the author overrode me

  **M-1 cusp frame — I concede, with one amendment.**

  My recommendation was "bhāva-madhya … Śrīpati is the Parāśari-consistent default **[P/J]**," and I explicitly left the factual leg open: "whether L1 already stores bhāva-madhya longitudes is **[U]** for me." The author resolved the [U] by source inspection: L1 computes Placidus cusps (`ga_positions_writer.py`, `ga_kp_significators.py`) and whole-sign; no Śrīpati anywhere. Given B.10 — no value may stand with no L1 fact behind it — my default would have blocked every house-target contract on an L1 amendment, for a classical warrant that is thinner than I implied: the BPHS ch. 26 translator's note says "for house in aspect, consider the cusp of the house, akin to a planetary degree" **[D, verified BP1:16632-16633]** — it mandates a *cusp as the target*, and names **no house system**. Śrīpati's unequal bhāva-madhya is the customary Parāśari companion **[P]**, but that is practice, not a verse. I tagged it [P/J] at the time; the author has shown the [P] leg cannot be served by L1 today. Structurally, "use the cusp L1 already stores, record the house system on every row, Śrīpati as a ratified variant with its own amendment" is the *same* discipline as the node ruling — serve what L1 names; variants require amendments — and consistency across the two sub-decisions is itself an argument for it.

  The amendment I attach to my concession: the summary (and eventually the plan) should say plainly that Placidus-as-stored is an **L1-availability default [P], not a claim that Placidus is the classical bhāva-madhya [D]** — the KP cusp facts exist because KP's sub-lord theory needs Placidus, which is a different question from Parāśari bhāva judgment; and Placidus cusps degenerate at high geographic latitudes **[P, mathematical property of the quadrant system]** — irrelevant to your chart, relevant the day the instrument serves another. With the frame recorded on every row, a future Śrīpati amendment is a variant swap, not a rebuild. Concession stands.

  **M-1d mean node — the structural finding strengthens the conclusion and reorders its grounds.**

  My reasoning had two legs: doctrinal ("Rāhu and Ketu, who are always retrograde" — BPHS 47, verbatim BP2:8959-8960 — is *exactly* true only for mean nodes **[D text + J inference]**) and consistency (L1 stores mean). The new structural finding — the served `graha_position` subjects are exactly `JUP, KET_MEAN, LAGNA, MAR, MER, MOON, RAH_MEAN, SAT, SUN, VEN`; **there is no `RAH_TRUE` subject** — converts the consistency leg from "what an adapter happens to compute" into "what the serving layer *names*." Under §N.5, mean Rāhu is the only *citable* node; any true value is computed at read time, stored nowhere, and silently inherits three unrecoverable conventions (epoch, backend, ayanāṃśa application — the sheet documents two sessions misled in one day by exactly this). So: my conclusion is unchanged, but the **primary warrant shifts from doctrine to provenance** — the same B.10 logic that decided the cusp question. The doctrine leg still stands, now as corroboration. One consequence the summary should state: since no `RAH_TRUE` subject exists, "true node as a declared variant" is currently *unservable* — ruling true costs L0/L1 amendments across five surfaces; ruling mean costs disposition (b), a declared ~1° disagreement on every row. The summary prices only the mean branch ("ruling mean isn't free"). Both branches should carry their price tag. On disposition (b) itself — keep the true knots, derive mean analytically at read — I concur, with the author's own guard: the derivation method goes on the row, never silent. [J]

  ## D. Recommendation quality — is each one-line call the right call, and is the stated reason the real one?

  - **M-1 four contracts:** right call; the stated reason is right but incomplete — the real operational driver is F-02 (direction tested per special aspect and reverse branch) plus one-root discipline. **Mean node:** right call, and the stated reason ("what L1 already serves and names") is now genuinely the real reason — see C. **Placidus-as-stored:** right call for sequencing; the stated reason is real but needs the recorded-frame guard and the Śrīpati-variant survival clause, or it overrules more than it intends.
  - **M-2 three states, own-BAV:** right call; the stated reason (the text puts 4 in the adverse half) is the real one. The missing half of the reason: SAV is an aggregate of the BAVs, so a high-SAV ingress with own-BAV 2 is the false positive a sign-total check cannot see — one clause would carry it. Vocabulary recording: right, and the real reason is the asymmetric hazard — any prose saying "bindu" unqualified is read two ways by two schools. (The summary's own headline — "is 4 **bindus** good enough?" — commits the very hazard, in Phaladīpikā-translation usage; per Santhanam's BPHS the count is of *rekhās*. I offer this as a free demonstration of why the ledger is needed, not as an error.)
  - **M-3 re-affirm §4.5 + bounded E3 + owner:** right call, correctly framed as the native's unique duty. But the fast tier as stated ("Moon/Sun contacts only") is **not** the sheet's recommendation; my alternative is the sheet's own five-witness list, minimally with laṭṭā (producer already served) and tārā-vedha restored.
  - **M-7 separation:** right call, real reason, strongest item — but say "anchors," not "texts," and restore the four fields.
  - **M-4 table + no-veto + line-by-line lords:** right call; add the cancellation-evidence precondition, or the native agrees to something whose detector cannot yet keep its promise.
  - **M-5 episode/occupied-days:** right call; the stated reason is implicit — supply the vakra = 60 reason or "no default peak" hangs in the air. [D: BPHS 27.21-23]
  - **M-6 two-gate boundary:** right call, faithfully stated; restore the second consumption precondition (outcomes on two axes).

  ## E. Priority order

  The author's order — M-3, then M-1d, then M-2, rest as "agree" — is defensible, but two things are wrong with how it is presented.

  1. **It contradicts the sheet's own endorsed ordering without saying so.** The sheet endorses my three questions — M-3, then BAV=4, then nodes — and the author *added a fourth of their own*: the cusp frame (M-1c), "one Kimi did not ask, which I would." The summary swaps #2 and #3 and silently drops the author's own addition. Whatever the merits, an author's summary should not quietly demote a question the author's sheet elevated.
  2. **The stated reason for ranking nodes second is the weakest available one.** "It changes a natal pāda in your own chart" is personal salience. The stronger reasons are on the sheet: the split is **live in served output** (the strategic session's DB-verified figures — node contacts on 232 of 914 `g3_utkarsha` rows and 50 of 87 at generation 2.0, which I attribute to that session and did not re-verify); the L0 store disagrees with its own DAR receipt; and three consumers read three different frames. Meanwhile BAV=4's "highest blast radius" is *prospective* — the check is dead today; its cost is irreversibility once ratified, compounded by the Kshetra cross-lock. On live-wrongness grounds, nodes second is actually the right call — but argue it on blast radius, not on the chart owner's curiosity.

  What I would move: keep M-3 first; keep M-1d second **for the sheet's reasons**; BAV=4 third; and **reinstate M-1c as a "decide," not an "agree"** — it has three live options on the sheet. M-7, M-4, M-5, M-6 can be "agree" only after each carries its omitted precondition (four fields, cancellation detector, aborted approaches, two-axis outcomes). And one structural option neither the summary nor the sheet states plainly: plan §8 marks M-7/M-4/M-5/M-6 rulable only "after step 2/3/4/5" — a partial ruling (the blocking three now, the rest at their steps) is legitimate; the native should know deferral exists.

  ## F. Missing — in neither the summary nor (in part) the sheet

  - **How to answer.** The sheet defines the answer format (`M-n: agree / agree, but … / no — …`) and that each row becomes authority only when answered; the summary never tells the native this. A ruling document should say how to rule.
  - **What happens after.** Per the FINAL packet: rulings fold into plan v1.0, a **third independent Astra review runs on the ruled plan**, and a **separate stage-3 execution session with an independent reviewer** implements it — the author does not certify their own build. The native should know that ruling "yes" seven times does not greenlight code the next morning; the safety chain follows. (In the FINAL packet, not the sheet.)
  - **Both branch prices on M-1d** (see C).
  - **The honest tier.** Every natal fact cited in the pāda argument is `verification_pass_status = single` — cited as L1's facts, not double-checked. If the pāda consequence is the native's reason to care, they should know its footing.

  ## Verdict — **SEND_WITH_EDITS**

  The summary is well-built: the seven recommendations are the right calls, the framing is honest, and it correctly refuses to repeat my one [U] claim. But a ruling document must surface the *questions*, and this one drops five native-facing questions, narrows one recommendation (M-3's witness list), and presents two pāda numbers as equally grounded. Eight edits:

  **Edit 1 — item 1, replace the opening sentences.** For:
  > Today it uses Western-style angles (60°, 90°, 120°) that Vedic texts don't use, and it searches on the wrong side for Mars and Saturn's special aspects. Proposal: four proper contracts — Parāśari planet-specific aspects (the main one), Moon-based gochara with vedha, Jaimini sign-aspects (only on a Jaimini route), Tājika (only for annual questions). Two sub-decisions ride along:

  read:
  > Today it applies one symmetric, unsigned aspect set (0°, 60°, 90°, 120°, 180°) to every rule, and it searches on the wrong side for Mars and Saturn's special aspects. Proposal: four proper contracts — Parāśari planet-specific directed aspects, with their fractional (¼/½/¾) strengths (the main one); Moon-based gochara with vedha; a Tājika applying/separating tag added to every contact in all contracts; Jaimini sign-aspects (only on a Jaimini route); and full Tājika aspects only for annual questions. Four sub-decisions ride along: **the old scan** — keep it one generation, labelled, never mixed with the new rows: retire it then, or sooner?; **node dṛṣṭi** — does your school grant Rāhu/Ketu any aspects as aspectors, and on which text? (If you don't answer, they ship as gochara agents and targets only.); **node convention** …

  **Edit 2 — item 1, cusp clause.** For:
  > **Placidus-as-stored** for cusps, not a third house system.

  read:
  > **Placidus-as-stored** for cusps — an engineering default because L1 already serves it, not a claim that Placidus is the classical bhāva-madhya — with the house system recorded on every row, and Śrīpati kept available as a ratified variant with its own L1 amendment (whole-sign-only remains an option if you prefer no cusps at all).

  **Edit 3 — item 2, after the recommendation, add:**
  > Two follow-ups only you can settle: within "indeterminate," does 4 lean adverse (the text says "fear") or neutral? And does the 6th/8th/12th-house inversion (a translator's note, not a verse) ship at all? Whichever aṣṭakavarga source you admit, Kshetra must consume the same one — one AV verdict per instant across the layer.

  **Edit 4 — item 3, fix the fast tier.** For:
  > grant a *bounded* fast tier (Moon/Sun contacts only inside an already-qualified window)

  read:
  > grant a *bounded* fast tier — Moon and Sun positions, tārā-vedha stars, and laṭṭā contacts, computed only inside an already-qualified slow window, all such contacts enumerated with no cap, and never counted as extra witnesses

  **Edit 5 — item 4, fix the fields and add the native's question.** For:
  > **yes, separate them** — intensity and valence as distinct fields; dignity moves from "gate" to "sign." The strongest-supported item on the sheet, three independent texts.

  read:
  > **yes, separate them** — four fields: intensity (never negative), valence (the good/bad sign), applicability, availability; dignity moves from "gate" to "sign." Genuine gates do survive where classical — orb of light, applying/separating motion, route eligibility. The strongest-supported item on the sheet: three independent anchors (two Phaladīpikā, one BPHS). One question only your practice can answer: is there any configuration that produces *nothing* — not evil, but silence? If yes, it becomes an applicability rule, never a multiplier.

  **Edit 6 — item 5 (M-4), fix the D30 conflation.** For:
  > (wealth D2, parents D12, learning D24, evil D30…)

  read:
  > (wealth D2, parents D12, learning D24, evil effects D30 — that last one is the text's domain assignment; routing DOSHA predicates to D30 is a proposal for you to rule, not doctrine)

  and append to the item:
  > Precondition to know before agreeing: weakness in a varga only counts if we can also detect its cancellations (nīca-bhaṅga) — without that detector, adverse conditions over-report.

  **Edit 7 — item 6 (M-5), add the reason and the aborted case.** After "no default 'peak' pass," insert:
  > — the text gives the retrograde pass the *maximum* strength of all motion states, so the retrograde contact is neither noise nor the automatic event date —

  and after "counts occupied days, not rows," add:
  > Episodes that approach but never perfect (station before exactness) are kept as labelled children, not silently dropped.

  **Edit 8 — attention paragraph, replace wholesale.** For the whole final paragraph, read:
  > **Where to spend your attention:** #3 first (it blocks two elevations, and only you can name the upstream producer's owner). Then #1's node sub-decision — not because it touches your own chart, but because the mean/true split is already live in served output (node contacts on roughly a quarter of the current generation's rows, per the strategic session's count) and the L0 store contradicts its own receipt. On your own chart, the cited fact is mean Rāhu, Rohiṇī pāda 3 (L1's own record, single-pass verified); true Rāhu computes to pāda 4 but is *computed*, not recorded — one side is cited, the other is arithmetic, and you should know which is which. Then #1's cusp question — three real options, not a done deal. Then #2's BAV=4 (nothing consumes it today; its cost is that once ratified it hardcodes an equality the texts and practice dispute, and Kshetra inherits it). The other four can be "agree" once each carries its precondition noted above. Answer in the sheet's format — `M-n: agree / agree, but … / no — …` — and know what follows: your answers fold into plan v1.0, a third independent review runs on the *ruled* plan, and only then a separate execution session with its own reviewer builds anything. You may also rule the blocking three now and defer the rest to their plan steps; nothing forces all seven today.

  — Kimi K3, reviewer. No file written; every [D] claim above traces to the sheet's author-verified citations (BPHS BP1/BP2 line ranges, Phaladīpikā wisdomlib doc1621595) or is tagged otherwise; figures from the Gochara/strategic sessions are attributed, not asserted.

