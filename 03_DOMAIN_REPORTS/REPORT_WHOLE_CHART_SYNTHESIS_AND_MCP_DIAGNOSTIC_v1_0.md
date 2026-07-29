---
canonical_id: REPORT_WHOLE_CHART_SYNTHESIS_AND_MCP_DIAGNOSTIC
version: 1.0
status: CURRENT
date: 2026-07-28
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
subject: Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar, Odisha)
session_type: Whole-chart acharya-grade reading + live MCP instrument diagnostic
produced_by: Claude Code session, direct MARSYS-JIS MCP consumption (mcp__marsys-jis-direct__*)
---

# Whole-Chart Synthesis + MCP Diagnostic Register — v1.0

**Purpose of this document.** Two things were done in one session and are both recorded here for future reference: (1) an acharya-grade astrological reading of Abhisek Mohanty's chart, produced by consuming the MARSYS-JIS MCP tools directly as the LLM endpoint; (2) a live diagnostic register of every gap, defect, and enhancement opportunity discovered in the instrument while doing so — including a verdict-inverting bug found, root-caused to the exact source line, during the reading review.

**How to read this file.** Part 1 is the reading itself, corrected in place where a later defect finding changed a claim (see the Jupiter Ṣaḍbala correction, §1.1). Part 2 is the defect register, organized by severity tier, ending with the fully root-caused Ṣaḍbala-narration bug (finding B‑3/B‑4) discovered via user-driven adversarial review mid-session — a case study in why prose narration fields must not be trusted at face value even when the underlying facts are verified. An addendum at the end covers a same-day follow-up wealth-intervention deep dive.

---

# PART 1 — The Reading

*Abhisek Mohanty · 05 Feb 1984, 10:43 IST, Bhubaneswar · Aries lagna · Lahiri ayanāṃśa · chart `482012f1-710e-4a25-994a-93821f5871aa`*

**Epistemic frame (per the instrument's own ethical contract):** The system is in **STRUCTURAL calibration mode** (L5 sealed) — every grade below is a *structural prior*, not an outcome-calibrated probability. The deterministic substrate (positions, dignities, yoga firings, neecha-bhaṅga, judgment checklist) is solid; the calibration on top of it is not yet populated.

## Chart geometry (D1 / D9, Lahiri)

- **D1 — Lagna Aries.** Rahu 2H Taurus (19°01′) · Mars 18°37′ + Saturn (exalted) 22°26′ in 7H Libra · Ketu 8H Scorpio (19°01′) · Jupiter (own) 9°49′ + Venus 19°27′ in 9H Sagittarius · Mercury 1°09′ + Sun (digbala) 22°11′ in 10H Capricorn · Moon 29°46′ 11H Aquarius (Pūrva Bhadrapadā).
- **D9 — Lagna Cancer.** Saturn debilitated (Aries) · Venus debilitated (Virgo) · Sun in Cancer (own lagna sign) · Jupiter + Rahu + Moon in Gemini · Mars in Pisces · Mercury in Capricorn.

**Seven FORENSIC birth anchors (chart_facts, PASS confirmed):** Sun = Capricorn · Moon = Pūrva Bhadrapadā · Lagna = Aries (all 5 ayanāṃśas) · Tithi = Śukla Tṛtīyā · Vāra = Ravivāra · Yoga = Śiva · Karaṇa = Garaja.

## The chart in one breath

This is **not** the Saturn-dominated chart the default digest reports (see Register finding R‑1). It is a **dharma-and-authority chart** with three crowns and one wound:

- **Crown 1 — the 9th house of fortune:** Jupiter in **own sign** (Sagittarius) in the 9th, with Venus. Forms **Sarasvatī Yoga**, **Dhana Yoga**, and a **kendra-trikoṇa Rāja Yoga**.
- **Crown 2 — the 10th house of karma:** Sun in **digbala** (Capricorn, 10th) + Mercury = **Budha-Āditya Yoga**; Moon is **exalted in the D10** (the career varga) in the 10th house there.
- **Crown 3 — Śaśa Mahāpuruṣa Yoga:** Saturn **exalted** (Libra 22°26′) in the 7th kendra — the single most powerful classical testimony in the chart. Saturn is 10th + 11th lord, so the career/gains engine is exceptionally strong.
- **The wound — the 7th/marriage axis:** two malefics (Mars + exalted Saturn) sit *in* the 7th, and the 7th lord & spouse-kāraka **Venus is the weakest planet in the chart and debilitated in the D9**. `judgment_query` grades marriage **"contested."**

## The spine, pillar by pillar

### §1.1 — Jupiter own-in-9th (CORRECTED per mid-session review)

> **Correction notice:** The original live reading stated Jupiter's Ṣaḍbala was "1.20 rūpas vs 6.50 required — weak, deficit −5.30." This was **wrong**, caught by the native's direct challenge, and traced to an instrument defect (see Part 2, finding B‑3/B‑4). The corrected fact, cross-validated three independent ways against other tool outputs in the same session: **Jupiter's actual Ṣaḍbala = 7.80 rūpas against 6.50 required → ratio 1.20 → Jupiter EXCEEDS its requirement by 20%, ranking 3rd of 7 classical planets. Jupiter is strong, not weak.**

Corrected reading: **Jupiter is own-sign in the 9th (dignity: superb) AND Ṣaḍbala-strong (7.80 rūpas, 1.2× required, 3rd overall).** The 9th-house crown of fortune, dharma, and higher knowledge is unqualified — strong by *both* placement and six-fold strength. There is no "delivers only through struggle" caveat on Jupiter's strength.

What *does* survive from the original reading (this rests on dāśā sequence, not strength, and is unaffected by the bug): Jupiter's own Mahādaśā ran 1975–91 (childhood) and does not recur until 2095 — so in adult life Jupiter blesses **as the dispositor-hub the entire chart converges onto** (the full planetary dispositor chain — Ketu/Mars/Mercury/Moon/Rahu/Saturn/Sun/Venus — converges onto Jupiter, 9 nodes) rather than through its own period. Jupiter is the silent hub every planet ultimately reports to; its expression is patient, not through direct rulership of the adult years, but constant.

### §1.2 — Śaśa Yoga + the 10th — a "learned authority / institution-figure" signature

Saturn exalted in a kendra gives the classical Śaśa native: commanding, disciplined, justice-oriented, able to hold authority over large groups and institutions, enduring. Fused with Budha-Āditya (sharp analytical/administrative intelligence, articulation) and Sarasvatī Yoga (learning, eloquence, wisdom), the vocational picture is **a principled, articulate authority inside a structure** — governance, law, academia, research administration, institutional leadership, advisory work grounded in higher knowledge.

The career-varga confirms it: **Moon exalted in the D10's 10th house**, Jupiter own in the D10, Saturn (karma-kāraka) rated *concordant* with the 10th, and — a robustness marker — **Saturn holds the same nakṣatra across all 5 ayanāṃśas** (the career significator is ayanāṃśa-stable; the vocational reading does not wobble with the ayanāṃśa choice). Career success is **positively weighted but formally "conditional"** — the instrument holds one unresolved *promise-vs-denial* tension (salience 2.54) open for acharya adjudication rather than forcing it.

### §1.3 — Saturn exalted (D1) / debilitated (D9) — but cancelled

Saturn is exalted in the rāśi and debilitated in the navāṃśa (Aries) — normally a "strong promise, weak fruit" warning. But the instrument fires **Neecha-Bhaṅga Rāja Yoga** with a full rule-by-rule ledger (BPHS Ch.39): Saturn's debility is cancelled *twice* — debilitation-lord (Mercury/Mars) in kendra from Moon and from lagna, and the exaltation-graha (Sun) in kendra from lagna. So the rāśi exaltation holds as operative, with a "rises through and past testing" raja-yoga quality layered on.

### §1.4 — Moon as Ātmakāraka in the 11th, Pūrva Bhadrapadā

The soul-significator (Jaimini AK = Moon) sits in the 11th (gains, networks, collectives, aspirations) in Aquarius — Saturn's sign again, routing the soul's agenda through Saturnian themes: institutions, the masses, disciplined idealism, humanitarian breadth. Pūrva Bhadrapadā lends a philosophical, intense, at-times austere/otherworldly cast; **Anapha Yoga** gives a self-contained, well-regarded personality. The Moon at **29°46′ Aquarius** — the very last minutes of the sign — adds a restless, threshold quality to the emotional nature. The karakāṃśa falls in **Aries**, reinforcing a pioneering, self-driven inner orientation beneath the Saturnian outer discipline.

## Domain readings

**Career / Vocation — strong, dharmically-flavoured, formally conditional.** Śaśa + Budha-Āditya firing *directly on* the 10th/7th significators, Moon exalted in D10, Sun strongest by Ṣaḍbala (1.694 ratio = 8.47 rūpas, digbala in the 10th), Saturn karma-kāraka concordant. The vocation carries a 9th-house (dharma/knowledge/ethics) coloring — a career *of principle and higher knowledge*, not merely of ambition. One open contradiction keeps it honest: the chart both promises and, in one testimony, denies — read as **real achievement reached through friction and delay, not a frictionless ascent.** System remedy priority for career: **Moon first**, then Jupiter, Mars, Sun; for Saturn specifically, Śani Aṣṭottara / Śani Cālīsā on Saturdays.

**Marriage / Partnership — contested but not denied; delayed, serious, redeemed.** The 7th (Libra) holds Mars (lagna lord) + exalted Saturn in a ~4° conjunction — the classic delay/friction/control-vs-freedom signature. The 7th lord & kāraka **Venus is the chart's weakest planet (Ṣaḍbala ratio 0.844 = 4.64 rūpas against 5.5 required), debilitated in the D9, and papa-kartari** (hemmed between Sun and Ketu). `judgment_query` grades bhāva 7 **"contested" (composite −3.5)** — the **D9 (the "fruit") moved the verdict** from merely "mixed" to "contested." *But* two redemptions apply: Venus's D9 debility is **neecha-bhaṅga-cancelled** (same mechanism as Saturn, §1.3), and **Mars sits in puṣkara-navāṃśa** (an auspicious amsha). Synthesis: **marriage delayed and tested, a mature/dutiful/serious partner (Saturn's exaltation argues for someone older, established, or duty-bound), with real strain around autonomy and warmth — but the debilities are structurally rescued; this is a hard-won, not a foreclosed, partnership.** Timing hooks cluster in the current Saturn antardaśā window (to Aug 2027) and gochara marriage-contacts in **late 2027 (Nov–Dec) and Dec 2028** — all flagged *neutral* valence.

**Wealth — secure and dharma-earned, not a dominant theme.** Dhana Yogas fire (Venus + Jupiter in the 9th; house-lords Dhana Yoga), 11th-lord Saturn is exalted (strong gains capacity through career), 2nd-lord Venus sits in the fortunate 9th. Wealth is the lightest of the major convergence domains — prosperity is **earned through 9th-house means (knowledge, ethics, advisory, teaching, institutional standing) and accrues via the 11th/Saturn**, rather than through speculation or a Kubera-class money yoga.

**Health — the Saturn/sade-sati axis; overwork is the risk vector.** He is in the tail of the second sade-sati (active to ~June 2027). Saturn is the health-affinity graha here, and the **career↔health coupling is strong (601 shared signals)** — vocational intensity and vitality are linked; the health risk is Saturnian (chronic/structural: bones, joints, teeth, Vāta, fatigue), driven by overwork. Prāṇic strength is moderate (0.825). No acute-crisis or surgery promise surfaced (those graded low, n_support=0).

**Spirituality — a genuine, deepening undercurrent, set to open in 2027.** Ketu in the 8th (Scorpio), Jupiter own in the dharma 9th, Moon in Pūrva Bhadrapadā, a heavy loading of esoteric/swāṃśa points, and Ketu Mahādaśā from 2027 → a real scholar-ascetic current beneath the public karma, likely to become explicit in the Ketu years (research, the hidden/occult, detachment, moksha-leaning inquiry).

## The timing spine and the 2027 hinge

| Period | When | Reading |
|---|---|---|
| **Mercury Mahādaśā** | 2010 → **18 Aug 2027** | The long career/communication/skill era (Mercury in 10th, Budha-Āditya, Sarasvatī). Final year. |
| **Saturn antardaśā** | Dec 2024 → Aug 2027 | Peak career/status/gains + partnership activation — but carrying sade-sati's weight: restructuring, endurance tests. Convergence peaked **Apr 2026**. |
| **Moon pratyantardaśā** | Jun–Sep 2026 | AK Moon (11th) overlay — emotional/aspirational tone. |
| **→ KETU Mahādaśā** | **from 18 Aug 2027** (age 43) | **The pivotal hinge.** Ketu in the 8th: a turn inward — detachment, research/spiritual deepening, transformation, possible discontinuity in the outer career built during Mercury, a re-sorting of identity. |

**The through-line:** a disciplined, principled, articulate person whose identity is worked out through *duty, institutions, and dharma* (Śaśa + Sun-in-10th + Jupiter-own-9th + Budha-Āditya), carrying a private philosophical/renunciate undercurrent (Ketu-8, Moon in Pūrva Bhadrapadā) — with the relationship sphere as the chart's chosen field of difficulty and growth, and 2027 as the doorway from public building to inner deepening.

---

# PART 2 — The MCP Instrument Diagnostic Register

Framing: consumed the MCP exactly as the LLM endpoint would, live, on a fully-built chart. The **deterministic substrate is already acharya-grade**; the gap to *beyond-acharya, deep-dive-on-demand* lives almost entirely in the **synthesis / ranking / serving layer** between that substrate and the LLM.

## Tier 0 — Blockers (flagship tools unusable to an LLM as-is)

**B‑1 · The `assess_*` family overflows context and ignores its own declared budget.**
`assess_marriage` returned **276,499 bytes** (budget declared 40 KB → **6.75× over**); `assess_career` at `verbosity:concise` returned **165,408 bytes** (budget 20 KB → **8.1× over**). Both had to be spilled to disk and mined by subagents. Root cause (forensically confirmed via two dedicated file-forensics passes):
- **`orientation_context.top_signals` staples 100 generic chart-wide signals onto every domain answer** — in the marriage call, **81 of 100 were off-domain**, ~144 KB, alone 3.5× the budget.
- **`activating_dasha` forwards raw L3 jsonb columns duplicated per activation** — the same 24-row triangular dāśā-ramp serialized **~6–15× byte-identical** (60 KB in the career call; only 3–5 distinct blobs exist across 10 "different" activations).
- **`citations` is 200 bare UUIDs with zero citation text** (~7–8 KB of pure identifiers, real text is a separate drill call away).
- The trimmer, when it can't fit, **truncates leaf strings mid-token and trims its own `trim_report`, but never sheds the multi-KB duplicated arrays** — then self-reports `budget_exceeded_after_trim` instead of enforcing the cap.
- **Fix:** domain-filter (or drop) `orientation_context`; project compact fields instead of raw jsonb; dereference the dāśā-ramp to `{peak_date, orb, ref}`; make the trimmer recurse into the largest sections first.
- *This is the #1 fix — the marquee domain tools are the LLM's primary interface and are currently the least usable of all tools tested.*

**B‑2 · Intermittent timeouts on the heavy synthesis path.**
`assess_career` timed out outright; `judgment_query` timed out **2 of 3 calls**, succeeding only when `max_signals` was dropped to 5. The apex verdict tools are unreliable under default params on a fully-built chart. **Fix:** precompute/paginate the synthesis path so the acharya-grade verdict returns in-budget and in-time on the *first* call with defaults.

## Tier 1 — Ranking & salience (the reading surface actively misleads)

**R‑1 · Salience monoculture buries the chart's crown.**
The `bodha_chart_digest` top-signals are **12 near-identical "SAT: <sensitive-point>: sign = Capricorn/Aquarius" rows, all at byte-identical salience 2.16108**, because dozens of computed upagrahas / aprakāśa / sāham / bhṛgu-nāḍī / esoteric points fall in Saturn's two signs and *each is counted as a separate chart-defining signal*. Net effect: **Saturn aggregate score 78.3 (285 signals) vs Jupiter 1.76 (13 signals)** — so Jupiter-own-in-9th, Śaśa, Sarasvatī, Dhana and Rāja yogas are **invisible at the top of the headline reading surface.** An LLM trusting the digest alone would open the reading with "Saturn in Capricorn sensitive points" and miss the actual chart. **Fix (highest interpretive leverage):** (a) collapse/deweight the "sensitive-point-in-dispositor's-sign" family so N restatements of "Capricorn is Saturn-ruled" don't each score chart-defining; (b) fuse the firings-authoritative yoga layer into the digest headline so Mahāpuruṣa/Dhana/Rāja/Sarasvatī surface at the top.

**R‑2 · Identical-salience ties with no tiebreak** (2.16108 repeated across dozens of rows) → arbitrary ordering. Add a deterministic secondary sort (dignity, house-strength, yoga-participation).

**R‑3 · Dignity × strength is never fused into a verdict for most graha reads.**
The instrument *stores* both dignity facts and Ṣaḍbala facts separately but doesn't always synthesize a fused conclusion outside of `judgment_query`'s D1×D9 fusion. Extend that pattern (D1-vs-D9 dignity reconciliation, as `judgment_query` already does for Saturn exalted-D1/cancelled-debilitated-D9 and Venus neutral-D1/debilitated-D9) to every graha and every tool, not just the judgment-checklist surface.

*(Note: an earlier draft of this finding cited a fabricated "Jupiter dignified-but-weak" example — that example was itself contaminated by the B‑3 narration bug below and has been removed. With corrected numbers there is no dignity-vs-Ṣaḍbala conflict for Jupiter in this chart; the genuine cross-metric fusion need is the D1-vs-D9 varga axis, which `judgment_query` already models correctly.)*

## Tier 2 — Synthesis-layer emptiness & genericity

**S‑1 · The Mahā-Brief is mostly hollow.** Of 27 verdicts, **~12 are `not_yet_assessed`, `n_support=0`, structural prior 5.0/10, flagged "CONTRADICTORY RAW STATEMENT."** The flagship synthesis brief is largely placeholders for event-classes with zero backing evidence.

**S‑2 · Event-polarity blindness.** "Major Financial **Gain**," "Major Financial **Loss**," and "Financial **Deception**" all grade **identically 2.0/10 from the same two facts.** Opposite events must not resolve to the same grade from the same evidence — the verdict engine is applying a generic per-class prior, not polarity-differentiated evidence.

**S‑3 · Degenerate discoveries.** `top_discoveries` = five identical strings *"Appears as one of many sade_sati signals," salience 1.2.* The discovery generator emits duplicate boilerplate — no information.

**S‑4 · Load-bearing module runs on stub data.** The `load_bearing_signals` cite phantom ids (`fam_msr_signal`, `fam_convergence`, `fam_yoga`) with empty `ranked_evidence` — template placeholders, not real chart signal UUIDs.

## Tier 3 — Timing & forecast (the biggest capability gap)

**T‑1 · Gochara intensities are unnormalized and uninterpretable.** `signed_intensity` ranges from **16,529 to 156,671,157,428** — ~10 orders of magnitude, `structural_prior`, no 0–1 or percentile scaling. **Fix:** per-chart percentile/z-score normalization.

**T‑2 · Gochara is all points, no spans.** 40/40 windows observed were `temporal_shape:point` (single days), 0 interval, 0 chain — a near-daily transit-contact log, not synthesized elevated-probability episodes.

**T‑3 · Forward-looking timing is largely unbuilt.** `kala_windows` returned **`forward_window_count: 0`** (multi-cycle generator is "D-3 scope"), and gochara covers **only 3 of ~13 event-domains** for this chart (health, education, progeny, family, travel, spirituality **not covered** — honestly disclosed, but a real hole). *(Extended by finding W‑2 below: the wealth domain specifically has near-zero predictive-timing coverage.)*

**T‑4 · Predicted dates fall outside their own window.** A 2010–2027 activation window lists convergence peaks in 2030–2032; a 2024–2027 window predicts a 2032 peak. Internal inconsistency — the predicted-date generator isn't clamped to the activation envelope.

## Tier 4 — Data hygiene

**H‑1 · Spurious self-parivartana.** `graha_portrait` reports *"Jupiter_in_Sagittarius ↔ Jupiter_in_Sagittarius"* as a "mutual exchange" — a planet in its own sign is not a parivartana. Filter self-exchanges.

**H‑2 · Budget truncation corrupts content.** At 6 KB, responses sever strings mid-token (`"…[truncated for budget]"` inside values) and still report `budget_exceeded_after_trim`. Truncation must drop whole fields, never sever a string.

**H‑3 · Yoga strengths are a proxy, and bhaṅga is only half-wired.** Firing strengths are `computed_extension` (mean normalized Ṣaḍbala) — honestly flagged as non-classical (B.10) — and for Śaśa the `bhanga_na_reason` admits *"classical bhanga rule exists in catalog but is not evaluated."* Extend the neecha-bhaṅga rule-ledger pattern (see below) to per-yoga classical strength and the other catalog cancellation rules.

**H‑4 · Minor, disclosed:** 0.3% orphan `constituent_facts_array` (230/71,293, DEFECT-001 residual); `citations` blocks carrying UUIDs but no citation text.

## Tier 0/1 — B‑3 / B‑4: the Ṣaḍbala narration defect (full root-cause, found via adversarial review)

This finding deserves its own full account because it is (a) verdict-inverting, (b) systemic across all 7 planets and every chart, and (c) was caught only by direct user challenge mid-session, not by any test in the codebase.

### The claim as originally stated (wrong)

The live reading originally said: *"Jupiter's Ṣaḍbala is only 1.20 rupas against 6.50 required — six-fold-weak."* This came verbatim from the `graha_portrait` tool's narration string:

> *"Shadbala: 1.20 rupas vs 6.50 required — grade: weak (deficit) (−5.30 rupas)."*

### The native's catch

The native (Abhisek) correctly identified: *"I think 1.20 is the ratio, and the minimum strength required is 6.50 rupees, so you are basically comparing one absolute value with a ratio."*

### Empirical validation (cross-checked three ways)

The ratios reported for all seven planets in the session (Sun 1.694, Saturn 1.566, Jupiter 1.2, Mars 1.114, Mercury 1.079, Moon 0.942, Venus 0.844) reconcile exactly against *absolute* rūpa values surfaced independently by other tool calls in the same session:

| Graha | Ratio reported | × required (rūpas) | = Actual (rūpas) | Independent confirmation |
|---|---|---|---|---|
| Sun | 1.694 | 5.0 | **8.47** | `judgment_query`: `shadbala_rupa: 8.47` ✓ |
| Saturn | 1.566 | 5.0 | **7.83** | dāśā table: `lord_natal_shadbala_total: 7.83` ✓ |
| Jupiter | **1.20** | **6.5** | **7.80** | dāśā table (Jupiter MD): `7.8` ✓ |
| Mercury | 1.079 | 7.0 | **7.55** | dāśā table (Mercury MD): `7.55` ✓ |
| Moon | 0.942 | 6.0 | **5.65** | dāśā table (Moon PD): `5.65` ✓ |
| Venus | 0.844 | 5.5 | **4.64** | `judgment_query`: `shadbala_rupa: 4.64` ✓ |

A follow-up **live empirical test** was run against the two planets that should be *strongest* in this chart — Sun (chart's strongest by every metric) and Saturn (exalted, Śaśa yoga) — to test whether the bug was Jupiter-specific:

| Graha | `graha_portrait` narration (verbatim) | Reality | True grade |
|---|---|---|---|
| Sun | *"Shadbala: 1.69 rupas vs 5.00 required — grade: weak (deficit) (−3.31 rupas)"* | 8.47 rūpas | **Strongest in chart, +3.47 surplus** |
| Saturn | *"Shadbala: 1.57 rupas vs 5.00 required — grade: weak (deficit) (−3.43 rupas)"* | 7.83 rūpas | **Strong, +2.83 surplus** |

**Confirmed: the tool grades the chart's single strongest planet (Sun) "weak." The bug is systemic across all 7 planets, on every chart** — because the ratio always lands near 1.0 while every required-minimum is 5–7, `ratio − required` is structurally always negative.

### Root cause (traced to exact file/line via code investigation)

Three different values are stored under **one** `fact_category` (`graha_shadbala_total`) in the L1 writer `ga_strength_writer.py` (`_build_shadbala_rows`, lines 704–821), distinguished only by `fact_key`:

| `fact_key` | value (Jupiter) | unit | ayanāṃśa |
|---|---|---|---|
| `rupa` | **7.80** (achieved, absolute) | `rupa` | lahiri_chitrapaksha |
| `required_rupa` | **6.50** (classical minimum) | `rupa` | `INVARIANT` |
| `ratio` | **1.20** (achieved ÷ required, added later per CR-18) | `null` | lahiri_chitrapaksha |

The narration builder — in the MCP wrapper `platform-mcp/src/tools/registry_bridge.ts:3496–3515` (function `buildGrahaPortraitNarration`, authored commit `c8cde0a53`, 2026-07-10) — selects with:

```ts
strengthRows.find(r => r['fact_category'] === 'graha_shadbala_total')
```

This **ignores `fact_key`**, so it takes whichever row sorts first. Two facts decide that, both deterministic:

1. `graha_portrait` passes a concrete ayanāṃśa (`lahiri`), and the upstream `get_strength.ts` filters on it (`AND ayanamsha_id = $N`, line 129–131) — which **drops the `required_rupa` row** (stored as `INVARIANT`).
2. `get_strength.ts` orders `ORDER BY fact_category, ayanamsha_id, fact_key` (line 148). Within the two surviving rows, **`'ratio' < 'rupa'` alphabetically** — so `find()` returns the unitless `ratio` row.

The code then labels that `1.20` as `"rupas"` (line 3501, `numOf(totalRow)`), and — a second smell — computes `required` from a **hardcoded wrapper-local table** `SHADBALA_REQUIRED_RUPAS` (lines 3308–3310), not from the L1 `required_rupa` fact it just filtered out. `surplus = rupas - required` (line 3505) uses the **same mis-selected `1.20`** for both the displayed number and the arithmetic: `1.20 − 6.50 = −5.30 → grade: weak (deficit)`. The correct row (`fact_key='rupa'`, 7.80 → surplus +1.30 → strong) is never read.

**Why the collision happened:** the `ratio` fact_key was added *later* by a separate change (CR-18, on the L1 writer / producer side — the writer's own code comment documents the addition). The narration builder was authored afterward, in a different lane, by someone who didn't know the shared `fact_category` had grown a third, differently-shaped member. Two authors, one shared category key, no coordinating `fact_key` check → silent collision.

**Scope: all 7 grahas, every chart, always.** There is no per-planet branch — `grahaName` only indexes the required-lookup table. Because `ratio` is always ~0.5–2.0 and `required` is always 5–7, `ratio − required` is **structurally always negative**, so this narration clause will print `weak (deficit)` for every graha on every chart it runs on, regardless of true strength.

### Why a "deterministic + verified" asset shipped this — the verifier gap

Three compounding factors, confirmed by direct test-file inspection:

1. **Tests assert structure, not semantics.** The one test touching the strength section (`graha_portrait.gate.integration.test.ts`) asserts only `strength.rows.length > 0`. No test anywhere asserts a golden value for the strong/weak grade.
2. **The bug lives in a different module than the tests target.** All `graha_portrait` integration tests exercise the **capability handler** (which returns raw rows, correctly). The narration sentence is assembled in the **MCP wrapper** (`registry_bridge.ts`) — a layer the strength-touching test never runs. The test is architecturally blind to the sentence.
3. **"Verified" covers the facts, not the derivation over them.** All three rows (`rupa`, `required_rupa`, `ratio`) are individually correct and `two_pass_verified`/`verification_pass_status`-stamped. The B.10/§N.5 deterministic-computation guarantee stops at the `fact_id`. The *sentence that picks among those facts and does arithmetic* was never in scope for any verifier. A verified fact was mis-selected by an under-specified `find()` and relabeled, and nothing checked the derived conclusion.

**No code comment near the offending block (lines 3496–3515) warns of the three-row ambiguity.** The only ratio-awareness in the codebase is on the producer side (`ga_strength_writer.py`'s CR-18 comment, documenting the `ratio` row's *addition* — not warning downstream consumers of the category's new shape).

### Verdict — one paragraph

A deterministic, individually-verified asset shipped an inverted grade because the failure was not in any *fact* but in an untested *derivation across facts*: L1's `ga_strength_writer` legitimately stores three rows under one `fact_category` (`graha_shadbala_total`) — absolute `rupa`, constant `required_rupa`, and normalized `ratio` — distinguished only by `fact_key`, and the `ratio` row was added later without the narration author's knowledge. The MCP narration builder selects that category with a `find()` that ignores `fact_key`; because `graha_portrait` passes a concrete ayanāṃśa (filtering out the `INVARIANT` `required_rupa` row) while the upstream query orders alphabetically by `fact_key` (`'ratio' < 'rupa'`), the selector deterministically grabs the unitless `1.20` ratio, labels it "rupas", subtracts a hardcoded `6.50` from it, and grades every graha "weak (deficit)" on every chart. It survived review because every `graha_portrait` test asserts shape/presence/reachability rather than the semantic correctness of the strength grade, and because the narration sentence is assembled in a wrapper layer separate from the capability handler that the one strength-touching integration test actually runs — so the "facts are verified" guarantee never extended to the derived sentence that mis-picked among them.

### Register findings (formal)

- **B‑3 (correctness, verdict-inverting):** `platform-mcp/src/tools/registry_bridge.ts:3496–3515`, function `buildGrahaPortraitNarration`. The Ṣaḍbala narration clause selects `fact_category='graha_shadbala_total'` without disambiguating on `fact_key`, grabbing the unitless `ratio` row and labeling it "rūpas"; grades all 7 grahas "weak" on every chart. **Fix vector:** `find` must pin `fact_key === 'rupa'`, and `required` must be read from the L1 `required_rupa` fact (not the hardcoded `SHADBALA_REQUIRED_RUPAS` table) so the two values can never drift or be sourced from different systems of record.
- **B‑4 (systemic, process-level):** Narration prose across `graha_portrait` (and likely other tools) is assembled in the MCP wrapper layer, architecturally outside the layer integration tests exercise, and no test asserts semantic grade correctness anywhere in the codebase. Two concrete follow-ups for Phase B:
  1. **Sweep the sibling clauses** in `buildGrahaPortraitNarration` — the dignity, yoga, and dāśā clauses use the same `find`-over-`fact_category` pattern and may carry the same latent mis-selection risk wherever a `fact_category` has grown multiple `fact_key` variants over time.
  2. **Add golden-value grade tests** at the wrapper layer, and extend the "verified" guarantee to cover derived narrative sentences, not just the `fact_id`s they cite as grounding.

### The general lesson (trust boundary for this instrument)

**Verified facts vs. verified prose are not the same guarantee.** This session's audit confirms:
- Raw chart facts (positions, dignities, dāśā lords/dates, yoga firings, absolute rūpa values), and **computed verdict objects** like `judgment_query`'s signed composite score, are correctly verified and were unaffected by this bug.
- **Any narration/summary string that asserts a grade** ("weak"/"strong", "promised"/"denied", a computed deficit) should be treated as **unverified prose** and reconciled against the underlying numeric facts before being trusted — this bug proves that prose layer can silently invert a verdict while citing entirely correct, verified `fact_id`s as its grounding.

---

## Tier 5 — What is already excellent (keep, and propagate the pattern)

- **⭐ `neecha_bhanga_raja_yoga` with per-rule `grounds_jsonb` ledger** — BPHS Ch.39, per-varga, role-split (debilitated vs rescuer grahas), honest flooring of the one rule it can't verify to a primary citation. **This is the gold standard. Every yoga and every verdict should be built this way.**
- **⭐ `judgment_query`** — deterministic signed verdict, **Sudarśana dual-frame** (from lagna *and* from Moon), an operative-varga term that can and did move the verdict, benefic/threat layers served separately each with a hardFloor, sensitive-degree firings surfaced, KP cusp sub-lord chain, and a **completeness receipt** (8/12 units served, with an honest `not_joined` list). When it runs, this is *already* beyond-acharya structure. **Make it the default surface; fix its reliability (B‑2); wire the missing units.**
- **⭐ Epistemic honesty throughout** — `n_support=0` verb-masking, `documented_approximation` flags, dissent held-not-reconciled, coverage receipts (`domains_not_covered`), `uncited_extension` flags, deprecated-field notices. This discipline is rare and exactly right, and it is what made the B‑3 bug findable at all (the tool correctly cited its `fact_id`s even while mis-deriving the sentence over them).

## The through-line — five leaps to "supercomputer" grade

1. **Make it fit** — enforce the response budget on the *actual* largest sections (B‑1); the marquee tools must be inline-consumable.
2. **Rank by what matters** — break the sensitive-point salience monoculture and fuse yogas into the headline (R‑1) so the reading opens on the chart's real spine.
3. **Fuse cross-metric verdicts** — dignity × Ṣaḍbala × varga into a single per-graha and per-bhāva synthesis, the way `judgment_query` already fuses D1×D9 — extend it everywhere.
4. **See forward** — normalized, span-shaped, multi-cycle, full-ontology timing (T‑1→T‑4), so prediction becomes a first-class capability rather than a current-window log.
5. **Verify the sentence, not just the fact** — close the B‑3/B‑4 gap: every derived narrative clause needs the same rigor as the facts it cites, with golden-value tests at the point where prose is assembled, not just at the point where data is fetched.

Do those five, propagate the neecha-bhaṅga ledger pattern to every yoga and every narration clause, and the instrument stops *serving data an acharya must interpret* and starts *delivering the interpretation itself* — which is the "beyond-acharya, deep-dive-on-demand" target.

---

# ADDENDUM (same session, continued) — Wealth-Intervention Deep Dive

Triggered by the native's follow-up question: "what intervention can unlock financial prosperity, and what should I start ASAP." Two new register findings surfaced; both are appended here rather than renumbering the tiers above.

## New finding W‑1 — Domain-filtered remedy engine omits the domain's own bhāveśa

`bodha_remedies_get(chart_id, domain='wealth')` returned only **3 resonances** (Jupiter #1 medium, Sun #2 low, Saturn #3 low) as wealth-remedy targets. **Venus — the 2nd-lord (bhāveśa of wealth itself) and independently confirmed the chart's single weakest planet by 5+ metrics (this session's live Ṣaḍbala pull, and the legacy `REPORT_FINANCIAL_v2_0.md`'s Uccha Bala / Shuddha Pinda / Bhavabala cross-checks) — does not appear in the wealth-domain resonance list at all.** The domain filter appears to rank by general chart-wide weakness resonance rather than by domain-significator-specific weakness; it never asks "is *this domain's own house lord* weak?" A user consuming only this tool for wealth remedies would never learn that Venus — the most textbook-obvious remedy target for the wealth domain — needs propitiation. Cross-checked: `ref_remedies_by_planet_get(planet='venus')` DOES carry a wealth-tagged entry (`venus_wealth_gemstone_01`) — so the underlying corpus has the content; the domain-scoped resonance ranking in `bodha_remedies_get` simply never surfaces it. **Fix vector:** the wealth-domain resonance ranking should weight a graha's role as bhāveśa/kāraka of the queried domain, not just its chart-wide weakness rank.

## New finding W‑2 — Wealth-domain predictive timing is close to empty

`phala_outlook_get` (24-month horizon) returned anchors for career, relationship, and character domains — **zero wealth-domain event anchors**. `judgment_query(bhava=2)`'s own `gochara_sweep` for domain='wealth' returned `upcoming_window_count: 0`. This extends Tier‑3 finding T‑3 (forward timing largely unbuilt) with a concrete case: for the single highest-value question a user is likely to ask a wealth-remedy instrument — "when will this materialize" — the predictive layer currently has nothing to say. The only wealth-relevant forward signal found came from `kala_priority_ranking_get(domain='wealth')`, which returned natal-structural facts scoped to the *current* dasha window (correct and useful) plus one late-2027 activation spike — but no calibrated financial-event anchor of the `phala_anchors` kind exists for this chart yet.

## Cross-reference note — a legacy CLOSED report reconciled well against live data

`03_DOMAIN_REPORTS/REPORT_FINANCIAL_v2_0.md` / `v2_1.md` (status: CLOSED, built on the now-retired JH-software-based FORENSIC v8.0 source per governance history, not the live L1 `chart_facts` table) was consulted for cross-reference during this addendum. Its independently-computed claim that transiting Jupiter occupies its own exaltation sign (Cancer) from June 2 through October 31, 2026 was **verified live this session** via `ref_planet_transit_get`: Jupiter's `sign_number` is confirmed 4 (Cancer) through 2026-10-30 and rolls to `sign_number:5` (Leo) exactly on 2026-10-31. This is a good data point for future sessions: the legacy report's *positional/transit* calculations remain trustworthy even though its status is CLOSED and its source predates the current build — but its *specific sub-window claims* (e.g. a July 14–August 12, 2026 Jupiter-combustion window, specific eclipse dates) were **not** independently reverified this session and should be treated as unconfirmed until checked against live Sun/Jupiter longitude data. Also worth a future check: the legacy report's claim that Saturn was transiting Pisces "through November 2025" appears to conflict with this session's live pull showing Saturn still retrograde in Pisces through October 2026 — likely just a different sub-phase of a multi-year retrograde-heavy Pisces transit, but not reconciled this session.

*End of REPORT_WHOLE_CHART_SYNTHESIS_AND_MCP_DIAGNOSTIC_v1.0 (2026-07-28, addendum same-day). Produced in one live session via direct MCP consumption; the B‑3/B‑4 finding was discovered through the native's own adversarial review of the Jupiter Ṣaḍbala claim, not through the instrument's own tests or verifiers.*
