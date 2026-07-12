# Shard 7-5 — SYNTHESIS-CEILING (Lane 7, P-11 Requirements Spec)

**Charter §4 class 8 — UN-SYNTHESIZABLE AT SCALE**
**Heavy question:** "Spiritual/moksha propensity — whole-chart synthesis (L6)"
**Chart:** 482012f1-710e-4a25-994a-93821f5871aa (Abhisek)
**Channel:** deployed MCP connector (read-only, doctrinal public channel), 130 tools.
**Date:** 2026-07-12

---

## 1. Scale of the question (factors needed)

The connector's own digest reports the chart carries **13,364 MSR signals**, 15 yogas, 22 doshas.
The **`spirituality` domain reading** resolves to **3,338 signal_id_refs** (the moksha/dharma-relevant
candidate pool). CDLM cross-domain cells show spirituality shares **3,196 signals with career** and
**3,169 with relationship** — i.e. the renunciation-vs-engagement axis is the dominant cross-domain
tension and cannot be read in isolation.

An acharya-grade moksha read must integrate, at minimum:
- **Bhava conditions** for 12H (vyaya/liberation), 8H (Ketu exalted in Scorpio 8H here), 9H (dharma),
  4H (end-of-life peace) — bhava + bhavesha + occupants + aspects → ~hundreds of chart_facts.
- **Moksha karakas:** Ketu (moksha-karaka), Saturn (vairāgya), Jupiter (jñāna/dharma, own sign 9H,
  shadbala 7.8), Moon (mind; Purva Bhadrapada — a mokṣa-intense nakṣatra), the 12th lord.
- **Vargas:** D20 (Vimśāṃśa/upāsanā), D24 (learning), D9 (dharma), D1.
- **Yogas:** pravrajyā/sannyāsa (4+ grahas in a house), parivrāja, kemadruma, plus bhaṅga checks.
- **Dasha timing:** which Vimśottarī/other periods activate 12H/Ketu/moksha significators.
- **Cross-domain (CDLM):** spirituality×career, ×relationship linkage strengths.
- **Classical citations** per rule (B.3 ledger).

**Factors-needed estimate:** load-bearing composed set an acharya actually holds ≈ **150–400 discrete
factors**, but they must be *reduced from* a candidate pool of **~3,300 domain-tagged signals
(≈13,400 whole-chart)** plus structural facts, 15 yogas, 22 doshas, and a windowed dasha timeline
(chart carries 536K dasha rows). The question is inherently a **map-reduce over thousands → hundreds → narrative**.

## 2. Does any serving path COMPOSE them? (ceiling probe)

**Partial. There is a checklist-verdict composer, but no narrative-with-ledger composer, and the moksha domain proper is absent.**

| Tool | What it does | Ceiling behavior |
|---|---|---|
| `get_signals` | raw signal rows | **Flat top-K wall: 50 default / 200 max** of 13,364. Offset paginates but only dumps raw rows — no rollup. Enumerating 3,338 spirituality signals = ~17 un-composed dumps. |
| `get_domain_reading(spirituality)` | lenses + CDLM cells + signal refs | Returns **3 lenses + 5 CDLM cells + 200 of 3,338 refs (capped)**. `points_only_assertion:true`, `verification_pass_status:documented_approximation` — **surfaces refs, does not compose a narrative.** |
| `synth_chart_brief_get` | whole-chart "maha-brief" | **Genuine composition but extreme lossy reduction: 38 topic slots + only 5 load-bearing signals for the ENTIRE chart.** Whole-chart, STRUCTURAL calibration (no empirical scores), no moksha-scoped/deep mode. |
| `judgment_query(domain=spirituality)` | deterministic classical checklist | **Strongest composer:** verdict_grade `convergent_strong`, composite_score `5.7`, honest completeness receipt (bhava✓ bhavesha✓ karaka✓ from_moon✓ D20✓ 14 yogas checked, **bhanga_checked:false**, timing_anchored✓). But it emits a **grade + checklist, not prose**, is scoped to **bhava 9 (dharma) only**, and its resolution_chains/fact_id_refs came back **empty on the no-question call** (populated on the with-question call — non-deterministic completeness). |
| `yoga_activation_by_dasha` | dasha×yoga map | Returned **0 activated yogas** over the next 3y — empty composition; no fallback to a longer horizon. |
| `phala_outlook_get(spirituality)` | forward anchors | Ignored the domain and returned generic **transition** anchors — domain not honored. |

**No tool performs map-reduce over signal families.** The family-composite structure exists in the data
(`family_key`, `family_member_count`, `is_family_composite`) but **no endpoint rolls 3,338 signals into
~40 family summaries and then composes families.** The caller must reduce by hand.

## 3. Receipt-honesty / integrity defects captured (byte-budget evidence)

1. **`get_signals.truncated = false` while `returned_count=50` << `total_matching_filters=13364`.**
   The truncation flag lies about a hard cap. (Failure class: receipt honesty.)
2. **Domain-reading `token_safety_note` is stale/wrong:** says *"Bounded to 3 lenses × 20 signals.
   Pass max_lenses=12 + max_signals_per_lens=100 for full payload"* — but only **3 lenses exist**, and
   `signal_id_refs` **stays capped at 200 of 3,338 regardless** of max params. `signal_id_refs_capped:true`
   with no cursor to page past it. The advertised knob does not lift the cap.
3. **Text channel suppressed** on `get_signals` / `get_cgm_subgraph`:
   *"[large payload — see structuredContent; text duplicate suppressed per S3 serialization-tax fix]"* —
   direct evidence the serving layer is fighting payload size (the scale problem is acknowledged in-band).
4. **Silent domain-validation gap:** `get_domain_reading(domain="XXNOPE")` does **not** error — it falls
   back to the generic orientation digest, so an unrecognized/mis-typed domain is indistinguishable from a real one.
5. **Taxonomy conflation:** `judgment_query` maps `spirituality → bhava 9 (dharma), karakas [Jupiter, Ketu]`.
   **There is no `moksha` domain.** Moksha (12H/8H/Ketu-vairāgya/Saturn, D20+D24) is subsumed under dharma;
   the one real composer answers a *related but different* question and never scores the 12H/8H liberation axis.

## 4. P-11 REQUIREMENTS SPEC — capability the system needs to answer this

To answer "moksha propensity — whole-chart synthesis" at acharya grade, the serving layer needs a
**staged map-reduce composition pipeline**, not a flat retrieval surface:

**R1 — Staged retrieval (drill-down, budget-aware).**
(a) domain-scoped candidate set → (b) family/salience rollup → (c) load-bearing selection → (d) composition.
Cursor-based pagination with an **honest `truncated` flag and `next_cursor`** that actually traverses all
3,338 refs; caps must be lift-able by a real knob or explicitly declared as a hard wall.

**R2 — Map-reduce over signal families.** A `signals_rollup(domain, group_by=family)` endpoint that reduces
3,338 signals → ~40 family summaries (count, net salience, valence, representative fact_ids), so the model
composes over families instead of dumping rows. This is the single missing primitive that makes the
question tractable.

**R3 — A first-class `moksha` domain distinct from `dharma`(9H).** Keyed on **12H + 8H + Ketu + Saturn +
4H**, operative vargas **D20 + D24 + D9**, karaka set {Ketu, Saturn, Jupiter, Moon, 12th-lord}, with its own
question-lenses (vairāgya, upāsanā, pravrajyā-yoga, gandānta/nakṣatra intensity).

**R4 — Narrative-with-ledger composition endpoint.** `compose_domain_judgment(domain, depth=acharya)` →
multi-paragraph prose where **every clause carries `fact_id_refs` + classical citation (B.3)**, integrates
**dasha timing** (yoga_activation over a horizon long enough to fire), folds in **CDLM cross-domain tension**
(renunciation-vs-engagement), and **runs the full checklist including `bhanga_checked`** deterministically
(no per-call completeness drift). `synth_chart_brief_get`'s 5-load-bearing-signal reduction must become a
domain-deep mode, not a whole-chart-only mode.

**R5 — Receipt integrity.** True cap counts, no stale knob-notes, hard errors on unknown domains, and a
`grounding_score` that reflects how much of the candidate pool was actually composed (not silently dropped).

## 5. Verdict

**CEILING HIT — partial-composition wall.** The system has a *deterministic classical-checklist verdict*
composer (`judgment_query`, grade `convergent_strong`/5.7) and a *lossy whole-chart brief*
(`synth_chart_brief_get`, 5 signals), but **no path composes the ~3,300-signal moksha candidate pool into an
acharya-grade narrative-with-ledger.** Retrieval is flat top-K (50/200 caps, un-budgeted dumps), there is
**no map-reduce over families**, and the **moksha domain does not exist** (conflated with dharma/9H). The
question is UN-SYNTHESIZABLE AT SCALE on the current serving contract. The spec above (R1–R5) is what would
lift it.

## 6. Corroboration addendum (independent re-probe, 2026-07-12)

An independent re-run confirmed sections 2-5 and adds two net-new receipts:

- **`judgment_query(bhava=12)` isolated verdict** = `convergent_moderate`, composite `2.2`, receipt
  `karaka:false, yogas_checked:0`. Run separately from `judgment_query(domain=spirituality)` (-> bhava 9,
  `convergent_strong`, 5.7). **Nothing fuses the two.** Direct proof of the R3/R4 gap: the moksha trikona
  (4-8-12) is only reachable as *disjoint single-bhava verdicts* the caller must hand-fuse; there is no
  cross-bhava moksha composite. Ketu (exalted 8H, the moksha-karaka) never enters the 12H verdict.
- **`judgment_query` `trim_report`:** `original_count 4 -> kept_count 1`, reason "full trim_report omitted to
  fit budget", recover_via `response_format:legacy`. Even the *honesty receipt itself* is budget-trimmed.
  Reinforces R5.
- Re-confirmed `judgment_flags` = `bhanga_not_checked` ("requires a data-plane addition, design 12 D3, not
  yet built for any chart") and `bearing_yogas_caveat` (single-pass label matches, "not cross-verified
  confirmed firings", JL-004) -- the R4 "run full checklist including bhanga" requirement is a known,
  honestly-flagged data-plane hole.
- Re-confirmed `token_safety_note`: "Bounded to 3 lenses x 20 signals. Pass max_lenses=12 +
  max_signals_per_lens=100 for full payload" with `signal_id_refs_total=3338`, `signal_id_refs_capped=true`,
  2000 refs returned; one CDLM cell (career x spirituality, `shared_signal_count=3196`) dumps ~3,196 bare
  UUIDs with no per-array budget guard.
- **Metadata drift:** `get_signals` description advertises a "573-signal corpus" while the live orientation
  digest reports `msr_signal_count=13364` -- stale doc vs live count (honest-but-inconsistent).
