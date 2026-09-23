---
artifact: KSHETRA_INDEPENDENT_REVIEW_7_8_9
canonical_id: KSHETRA_INDEPENDENT_REVIEW_7_8_9
version: "1.2"
status: COMPLETED_INDEPENDENT_REVIEW  # amended again 2026-09-23 (v1.2): the Venus repair is UPDATE-not-delete, the v1.1 dedup wording withdrawn. v1.1: three corrections from a second, independent review (Kimi K3 desktop app, see KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md), each re-verified at source by the author before adoption
date: 2026-09-23
reviews: KSHETRA_RULING_SHEET_v1_0.md rulings 7 (node frame), 8 (vedha admission / G-9), 9 (G3 suppression semantics)
reviewer: a fresh review agent opened with no prior context on this packet, briefed to re-derive
  every claim at source and forbidden to trust any session's report of it, including the packet's
  own text — the condition Gochara (madhav-e6) placed on whoever took these three rulings, since
  the strategic session (madhav-fc) and Gochara both declared a conflict on 7 and 8 (their evidence
  co-produced the findings under review) and neither would certify them.
opened_by: the Kshetra brief session (madhav-d2), discharging the native's delegation ("Go ahead
  and do it.", 2026-09-23) to name the 7/8/9 reviewer.
corroboration: "Ruling 8's corpus claim was independently re-run by the opening session itself, via
  the served ganita/ref_transit_rules_get and read_chapter tools rather than direct SQL, after the
  reviewer's report came back — the same discipline the reviewer names in its own note about not
  trusting a single session's report, applied one more time to the reviewer's own report. The
  32/3/6 split reproduced exactly."
---

# Independent review — Kshetra rulings 7, 8, 9

## Scope and method

The reviewer worked read-only in the `l3/kshetra-elevation` worktree at head `95135d97b`, with
write access to nothing — no edit, no commit, no build, no migration, SELECT-only SQL. Every claim
below carries the file:line, query, or command the reviewer ran to produce it; the full list of 107
commands and queries is preserved in the session record and is available on request. The packet's
own MCP database proxy was down at the start of the review; the reviewer brought up the project's
documented Cloud SQL Auth Proxy path for read-only queries and stopped it afterward (confirmed 0
listeners).

## Ruling 7 — node frame

**Verified, unchanged from the packet:** the store is the TRUE node at noon-UT knots
(`l0_ephemeris.py:77,290`; Swiss `swe_id 11` = `TRUE_NODE`, contrary to the file's own "Mean North
Node" prose comment at the same line); migration 624:30 asserts `node_mode: "mean"`; the L1 natal
Rāhu served for the canonical chart is the MEAN node under every ayanamsha (793 `RAH_MEAN` rows, 0
`RAH_TRUE` rows in `chart_facts`); MEAN and TRUE fall in different padas of Rohiṇī (pāda 3 vs pāda
4) at the forensic instant.

**Two corrections, neither changing the recommended disposition:**

1. **The margin is 0.049°, not 0.045°.** The reviewer's own Swiss/Lahiri computation at the
   forensic Julian day (2445735.717361, from `/tmp/se1`, retflag 65858 — no Moshier fallback) gives
   TRUE = 50.049248°, 0.049248° past the pāda-4 boundary at 50.000°; MEAN = 49.033044°, matching
   L1's stored `RAH_MEAN` fact to seven significant figures. The packet's own 0.045° figure carries
   a uniform −0.0041° offset from this on both nodes — an ayanamsha-value difference, not a
   different birth instant — and is corrected here rather than re-derived a third way.
2. **Disposition (b) is not "L0-untouched."** `node_mode: "mean"` is enforced today at three
   sites beyond the migration and the code comment the packet cited: the orchestrator's fail-closed
   probe validator (`service_probes.py:339-340`, which raises `ValueError` unless the registry probe
   reads "mean"), and two served declarations (`routers/ephemeris.py:49`, `routers/panchang.py:572`)
   that broadcast "mean" to every MCP caller today. A disposition-(b) implementation must reconcile the *store* to these three sites, not the other
   way around: two of the three — `routers/ephemeris.py:82` (`swe.calc_ut(jd, swe.MEAN_NODE, ...)`
   direct, documented as "distinct from the bounded 1900-2150 daily-grain ephemeris_daily table")
   and `panchang_engine/planets.py` (an assertion-guarded, explicitly-documented "Phase 4B" mandate
   that raises `AssertionError` if `TRUE_NODE` is ever passed for Rāhu) — independently re-verify as
   already correct and MEAN-compliant today; a disposition-(b) executor should not touch either. The
   defect is confined to the *store* (`ephemeris_daily`, migration 624, and `l0_ephemeris.py:77`'s
   "Mean North Node" comment on a body that is in fact TRUE) and its own fail-closed probe validator
   (`service_probes.py:339-340`) — the store must gain the derived mean column and correct its own
   declaration to match the two already-correct served engines, not the reverse (a directional
   sharpening by Kimi K3's independent desktop review, reproduced here at source before adoption —
   see `KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md`).

**Verdict: sound as written, with the two corrections above.**

## Ruling 8 — vedha admission

**Verified, unchanged:** the served corpus (`classical_text_chunks`) has Phaladīpikā at 564 chunks
and no KP text; the sarvatobhadra grid table is empty; laṭṭā (8 rows, PG339) and the malefic scale
(5 rows, PG353) are populated and corpus-verifiable; BPHS's own page 29 in the corpus is Bhāva
Padas, not transits, confirming the "BPHS Ch.29" citation on 39 of the 41 house-vedha rows is
wrong.

**One correction, and it changes what the ruling can say about the 41 rows.** The packet's claim —
that all 41 rows are "verbatim Phaladīpikā Adh. XXVI, PG322–323" and therefore all become `applied`
on the L0 re-citation — does not survive a row-by-row check against the served text. Comparing the
41 `bg_transit_rules` favourable/vedha rows (`ref_transit_rules_get`) against Phaladīpikā PG322:C1
(ślokas 3–5) and PG323:C1 (ślokas 6–8), independently reproduced by the reviewer and again by the
opening session using the served retrieval tools directly:

- **32 rows match exactly:** Sun 4/4 (3→9, 6→12, 10→4, 11→5), Moon 6/6 (1→5, 3→9, 6→12, 7→2,
  10→4, 11→8), Mars 3/3 (3→12, 6→9, 11→5), Saturn 3/3 (3→12, 6→9, 11→5), Mercury 5/5 (2→5, 4→3,
  6→9, 10→8, 11→12 — the text's sixth Mercury pair, 8th house vedha from the 1st, has **no row at
  all** in `bg_transit_rules`), Jupiter 5/5 (2→12, 5→4, 7→3, 9→10, 11→8).
- **3 rows contradict the text** (all Venus, all favourable, all citing "BPHS Ch.29"): id 35
  stores 3rd-house vedha as the 11th where the text (śloka 8) gives the 1st; id 44 stores 8th-house
  vedha as the 1st where the text gives the 5th; id 45 stores 9th-house vedha as the 2nd where the
  text gives the 11th. **Two of the three (ids 35, 44) are exact transpositions of already-correct
  rows elsewhere in the same table** — id 35's (3,11) is id 179's (11,3) reversed; id 44's (8,1)
  is id 33's (1,8) reversed — which explains their origin as a column swap (Kimi K3's refinement,
  reproduced from the served rules table). **The repair is nonetheless an UPDATE of `vedha_house` on all
  three (35→1, 44→5, 45→11), never a delete:** their `primary_house` values are the text's and needed,
  and deleting 35/44 would lose the 3→1 and 8→5 pairs; the v1.1 "dedup" wording was wrong as a repair
  instruction and is withdrawn. Spec with verification SQL routed to the L0 owner:
  `KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md`. All three need that L0-side fix, not a citation fix, before they qualify under
  the uniform rule.
- **6 rows have no source in Phaladīpikā at all:** the three Rāhu vedha rows (ids 187, 188, 189)
  and the three Ketu vedha rows (196, 197, 198). PG322–323 (ślokas 3–8, the specific verses this
  house-vedha mechanism cites) name only the seven classical grahas; the six rows have no
  counterpart there. The corpus is not silent on Rāhu/Ketu vedha altogether, though — PG348:C1 gives an explicit rule ("In the case of Rahu and Ketu, which are always retrograde, the Vedha will be on the right") — but that is the Sarvatobhadra chakra's asterism-direction vedha, a different mechanism from the house-transit pairs these six rows need (caught by Kimi K3's independent desktop review of the closed packet, reproduced here at the served corpus before adoption — see `KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md`). These 6 rows remain genuinely
  unsourced for the house-vedha mechanism, not merely mis-cited, and stay `unqualified`
  under the uniform admission rule exactly as written — they do not become `applied` on re-citation
  because there is no citation to give them.

So of the 41: **32 become `applied`** on the L0 re-citation as the packet intended; **3 are
deferred** pending an L0 geometry fix (Venus ids 35, 44, 45); **6 stay `unqualified`** (Rāhu/Ketu
ids 187, 188, 189, 196, 197, 198), not because Rāhu/Ketu vedha is doctrinally absent but because
this specific vedha-pair set for them is not in the served corpus under any citation. "Mis-cited,
not unsourced" is true of 35 of the 41 rows; 6 are unsourced.

**Sarvatobhadra, narrowed rather than corrected:** the reviewer confirms PG346:C1–PG352:C1 is
clean, substantial prose (~1,400 characters/page, no OCR-confidence flag set) that gives the
asterism ring, the twelve rāśis, the five tithi groups, the weekdays, the motion-dependent vedha
direction and the five-fold effect scale — everything the `vedha_pair` cells in
`bg_sarvatobhadra_grid` need. The vowel/consonant *letter* cell assignments on the same pages are
themselves OCR-degraded fragments embedded in the otherwise-clean prose and are not transcribable
without the diagram at PG345. "Buildable from prose today" holds for the vedha-pair construction
the grid needs; it does not hold for the full 81-square chakra including its letter partitions.

**Verdict: RE-OPEN, corrected as above.** The shared-producer decision, the uniform admission rule
itself, and the laṭṭā/malefic-scale outcomes are unaffected; only the house-vedha outcome and the
SBC scope statement change.

## Ruling 9 — G3 suppression semantics

**Verified, unchanged:** the stored field (`dhara_build_segments` → `FieldEvaluator.terms_at` →
`hazard.evaluate`) applies every active obstruction of the chart to every class, unfiltered; the
null (`dhara_compute_null`, via the same evaluator) takes the identical unfiltered path, so field
and null agree with each other; the only route-scoped filter in the codebase,
`layer1.project_layer1`, is a pure projection with **no production caller** — its only callers are
its own tests. Field and null are chart-wide; the documented contract is route-scoped; contract ≠
behaviour, exactly as the packet states.

**Two cosmetic corrections:**

1. The packet's citation `dhara_sweep.py:43,55` is wrong at every commit checked, including the
   packet's own stated base; the actual `terms_at` call sites are `dhara_sweep.py:212,227,243,248`.
2. The phrase quoted as the route-scoping contract's own words — "structurally impossible... to
   touch a class" — is not that. It is `stage4_field.py:561-565`'s guarantee that an obstruction
   cannot leak into the additive `M_e` term (polarity separation), a different guarantee from
   route-scoping. The route-scoping contract is documented at `layer1.py:15-21,29-30`,
   `hazard.py:347-350`, `layer0.py:57-60`, and `DHARA_ENGINE_SPEC_v1_0.md` (which already admits
   "currently the live code passes the full dict").

**Worth recording for whoever implements this:** `tests/test_layer0_projection.py` currently
contains a test that asserts the divergence as *correct* behaviour
(`layer1_result > terms_result`); under Option B that assertion must flip to equality, and is the
natural seed of the byte-equality test the ruling already asks for.

**Verdict: sound as written, with the two cosmetic corrections above.**
