---
title: Lane 8 — Entity-Dossier Depth Audit (the Mercury standard)
canonical_id: LANE8_ENTITY_DOSSIER_BRIEF
version: 1.0
status: DRAFT (Section 7 rubrics gated on Cowork ratification — see Charter §7)
source_plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md (§5 lines 216-244; Appendix B lines 489-597)
charter: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md (canonical_id LLM_CONSUMPTION_AUDIT_CHARTER)
generated_by: Brief Foundry session, 2026-07-11
---

# Lane 8 — Entity-dossier depth audit (the Mercury standard; native directive)

This brief is SELF-CONTAINED: a fresh session with no other context can execute Lane 8
from this file alone plus the two artifacts it cites by reference (the Charter, for
doctrine/taxonomy/finding-schema/satisfaction-criteria/rubrics; and its own ledger file,
`ledgers/facets.jsonl`). Do not re-derive Charter content — cite it. Do not skip reading
this brief's transcribed protocol below on the theory that it can be paraphrased from
memory; the plan text is reproduced in full and every sentence in the cited line ranges
must be present here, never softened.

## 0 — Charter reference (read first)

Cite `00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`, canonical_id
`LLM_CONSUMPTION_AUDIT_CHARTER`, for:
- **Doctrine** — Charter §1 (plan §2 + §2.1, verbatim): the gap definition, the
  width/depth completeness axes (Lane 8 IS the depth axis — "the full dossier of any
  entity that enters a synthesis... Considering Mercury without its dossier is not
  synthesis"), and the closed-loop-sources rule (examples are illustrative, never
  limiting — Appendix B is itself a floor, not a ceiling; see §2 below).
- **9-class failure taxonomy** — Charter §2 (plan §4, verbatim). Every Lane 8 finding gets
  exactly one primary class (classes 1, 2, 3, 6, 7, 9 are the most likely for entity-facet
  findings; class 4/5/8 also apply where an entire facet-group behaves as an empty shell
  or a dishonestly-described stage).
- **Finding schema** — Charter §3 (plan §6, verbatim): reproducible call, verbatim evidence
  excerpt, primary failure class, severity, suspected layer, dedupe check against the
  register (incl. anchor rows R-37..R-48), plus identity/linkage metadata for the Fable 5
  machine-readable findings JSON.
- **Satisfaction criteria** — Charter §4 (plan §8, verbatim), specifically criterion 3:
  "Depth completeness — 20/20 entity dossiers with full facet matrices; every
  held-but-not-received facet root-caused."
- **RESUME protocol** — Charter §5.
- **Execution DAG / swarm model** — Charter §6 (plan §12.7, verbatim) — this brief's
  Section 8 below instantiates it concretely for Lane 8's 20-worker shard.
- **Rubric** — Charter §7.1, "Usable form" rubric — this is the rubric Lane 8 applies to
  grade the `usable_form` column of the retrievability matrix (see Section 4 below).
  Charter §7.1/§7.2 rubrics are DRAFT pending Cowork ratification per the Charter's own
  gating note; Lane 8 may not treat them as final without that ratification, per Charter
  §7 preamble.

## 1 — Protocol, transcribed in full (plan §5 lines 216-244)

The following is TRANSCRIBED VERBATIM from the governing plan. Do not paraphrase; do not
soften any clause.

> ### Lane 8 — Entity-dossier depth audit (the Mercury standard; native directive)
> For each of 9 grahas + Lagna × 2 charts = 20 dossiers: FIRST enumerate from the data plane
> (DB) every facet the system holds about the entity; THEN attempt to retrieve each facet
> over the MCP wire as a consuming LLM would. Output: per-entity **retrievability matrix** —
> facet × {held in DB? | reachable via wire? | reachable in ≤2 calls? | arrives in usable
> form?}. Every held-but-not-received facet is root-caused into §4 classes ("WHY is the LLM
> not receiving this" is the lane's entire question).
>
> Facet checklist: **superseded by Appendix B (60-facet floor, v2, native-directed maximal
> extent)** — the 10-group draft below is retained for audit trail only:
> 1. Position — sign, house, degree, **bhava-sandhi / cusp proximity** (e.g. Mercury on the
>    9th/10th cusp carries both flavors), nakshatra + pada + their lords.
> 2. Strength — shadbala six-fold breakdown, ishta/kashta, vimsopaka, bhava bala of owned houses.
> 3. State — avastha sets (baladi / jagradadi / deepta-adi), **combustion** (e.g. Mercury
>    with Sun — combust or not), retrogression, graha yuddha, graha sandhi.
> 4. Varga chain — D1→D60 dignity per varga, vargottama, own-varga counts, operative-varga condition.
> 5. Relational — conjunctions, aspects cast/received, **dispositor chain position** (who
>    disposits it, what it disposits, chain terminus).
> 6. Participation — **every yoga it constitutes, every dosha it constitutes**, karaka roles
>    (naisargika + Jaimini chara), arudha involvement.
> 7. Sensitive degrees — mrityu-bhaga, pushkara bhaga/navamsha, gandanta proximity (R-47:
>    currently computed nowhere per graha).
> 8. Temporal — is it current MD/AD/PD lord; its next period windows; current transit
>    position; **structural×temporal convergence, recent past + near future** (R-45 dependency).
> 9. Contextual — lordships and condition of owned bhavas; placement as seen from Moon, Sun,
>    and karaka lagnas.
> 10. Derived — KP star/sub/sub-sub roles, tara bala, its L2 signal family, its CGM graph
>     neighborhood.

**Explicit supersession statement (native directive):** the 10-group draft immediately
above (plan lines 226-244) is **RETAINED FOR AUDIT TRAIL ONLY**. It is NOT the executable
facet checklist. It is superseded in full by **Appendix B** (plan lines 489-597), the
60-facet-group floor, transcribed in Section 2 below. Any executor that grades against the
10-group draft instead of Appendix B has executed the wrong protocol and must redo the
affected shard.

## 2 — The governing facet checklist: Appendix B (60-facet floor), transcribed in full
(plan lines 489-597)

> ## Appendix B — Lane 8 facet taxonomy v2 (THE FLOOR; native directive: maximal classical
> extent, beyond project data; the foundry's DB+canon discovery pass may only ADD, never cut)
>
> Supersedes the 10-facet draft in §5 Lane 8. Applies per graha; §B-VIII.9 extends the Lagna
> dossier. Every facet is a ledger row: held? → wire-reachable? → ≤2 calls? → usable form?
>
> ### B-I. Positional & coordinate
> 1. Sign, degree-minute-second; bhoga traversed
> 2. House by whole-sign AND bhava-chalit (Sripati/Placidus) — divergence flagged
> 3. Bhava madhya distance; bhava/rashi/nakshatra sandhi proximity; cusp dual-flavor
> 4. Nakshatra, pada, nakshatra lord; KP star/sub/sub-sub
> 5. Navatara class from Moon AND from Lagna (janma/sampat/vipat/kshema/pratyak/sadhana/naidhana/mitra/parama-mitra)
> 6. Declination (kranti), celestial latitude (shara); rise/set state (udaya/asta); oriental/occidental of Sun
> 7. Speed, speed-ratio to mean, stationary proximity; retrograde/direct phase geometry
> 8. Ayana placement (uttarayana/dakshinayana); gola
>
> ### B-II. Dignity & sign-based
> 9. Exaltation/debilitation with exact deep-degree distance; ucha-abhilashi (approaching)
> 10. Mulatrikona / own / panchadha compound relation (natural × temporal) with sign lord
> 11. Neecha-bhanga condition enumeration (all classical grounds, each with evidence)
> 12. Vargottama; pushkara bhaga; pushkara navamsha
> 13. Mrityu bhaga (per-sign degree check); yogatara proximity
> 14. Dagdha / tithi-shunya / mrityu rashi ownership effects
> 15. Sign-type flavor: chara/sthira/dvisvabhava, odd/even, tattva, prishtodaya/sirshodaya/ubhayodaya
>
> ### B-III. Strength systems (full battery)
> 16. Shadbala complete tree: sthana (uccha/saptavargaja/ojayugma/kendradi/drekkana), dig,
>     kala (nathonnatha/paksha/tribhaga/abda/masa/vara/hora/ayana/yuddha), cheshta,
>     naisargika, drik — each component + total VS REQUIRED MINIMUM ratio (normative band)
> 17. Ishta/Kashta phala
> 18. Vimsopaka (shadvarga/saptavarga/dashavarga/shodashavarga) + vaiseshikamsha ladder
>     (parijata→devaloka) with amsha counts
> 19. Bhava bala of houses owned and occupied
> 20. Pancha-vargiya bala (Tajaka context); dwadash-vargiya where computed
> 21. **Ashtakavarga**: BAV per-sign bindus + total; bindus in occupied sign; kaksha lord at
>     its degree; SAV of occupied + owned houses; sodhya pinda (post-shodhana); transit
>     ashtakavarga filter
> 22. Sapta-vargaja dignity tally; own-varga counts
>
> ### B-IV. State & condition
> 23. Combustion with orb, applying/separating; graha yuddha (winner/loser, method)
> 24. Grahan yuti (node + luminary eclipse association)
> 25. Avastha sets — ALL FIVE: baladi (5), jagradadi (3), deepta-adi (9), lajjitadi (6, with
>     causal grahas), shayanadi (12, with sub-components)
> 26. Gandanta (rashi-nakshatra junction) proximity
> 27. Upagraha contact: gulika, mandi, dhuma, vyatipata, parivesha, indrachapa, upaketu; kala-vela lords
> 28. Saham contacts (Tajaka sahams: punya, vidya, vivaha, mrityu, karma, …)
>
> ### B-V. Relational web
> 29. Conjunctions (orb-aware); parashari aspects cast/received with sputa-drishti values
>     (full/¾/½/¼); special aspects (Ma/Ju/Sa)
> 30. Rashi drishti (Jaimini) cast/received
> 31. Sambandha classification with each graha (exchange, mutual aspect, mutual kendra, one-way)
> 32. Dispositor web: sign dispositor, nakshatra dispositor, navamsha dispositor, final-dispositor
>     chain position + terminus, reception loops
> 33. Papa/shubha kartari on its position
> 34. Argala on its positions: shubha/papa/virodha, given and received
> 35. Vedha: Sarvatobhadra chakra vedhas on its nakshatra; nakshatra vedha pairs; latta
> 36. Tara bala from Moon (and chandra kriya/vela/avastha for the Moon dossier)
>
> ### B-VI. Functional & role-based (lagna-dependent)
> 37. Lordships from Lagna, Moon, Sun; functional benefic/malefic/neutral; yogakaraka status
> 38. Kendradhipati dosha; badhaka/badhakesh status; maraka lordship/association
> 39. Naisargika karaka portfolio; sthira karaka; chara karaka (AK/AmK/BK/MK/PK/GK/DK) +
>     karakamsha relation
> 40. Arudha involvement: AL lord, arudhas of owned houses, graha arudha positions
> 41. Yoga participation — EVERY catalog family: raja (house-lord), dhana, mahapurusha,
>     nabhasa (correct single member per sankhya), chandra yogas (sunapha/anapha/durudhara/
>     kemadruma), surya yogas (vesi/vasi/ubhayachari), parivartana (maha/khala/dainya),
>     viparita raja, neecha-bhanga raja, adhi, gaja-kesari, kartari, kala-sarpa/kala-amrita,
>     arishta + bhanga, sanyasa yogas
> 42. Dosha participation: mangal (from lagna/Moon/Venus), shrapit, pitru, grahan,
>     guru-chandal, angarak, kemadruma, daridra, and full L0 catalog
> 43. 22nd drekkana (khareshwara) and 64th navamsha lord status; sarpa/pasha/nigala drekkana occupancy
>
> ### B-VII. Temporal (the graha as time-lord)
> 44. Vimshottari lordship now (MD/AD/PD/sookshma/prana) + next windows at each level;
>     dasha-sandhi proximity
> 45. Dasha-quality context: dignity/house of each running lord FROM this graha and vice versa
> 46. Other dasha systems: yogini role; chara/narayana rashi-dasha periods of its signs;
>     ashtottari; kalachakra deha/jeeva relation
> 47. Transit now: sign/house from natal Moon and Lagna, gochara quality + vedha points,
>     murthi at ingress; ashtakavarga bindu filter in transited sign
> 48. Sade-sati/dhaiya involvement (Saturn dossier; Moon dossier as receiver)
> 49. Double-transit (Saturn+Jupiter) participation on natal points
> 50. Varshaphal role: year-lord candidacy, muntha relation, tajaka aspect set (ithasala,
>     easarapha, kamboola, khallasara, rudda, …), tripataki vedha
> 51. Upcoming/recent eclipses and stations on its natal degree
> 52. Structural×temporal convergence: which of its yogas/promises are temporally ripe,
>     recent past + near future (the R-45 asset)
>
> ### B-VIII. Esoteric, remedial & tradition-specific
> 53. KP significator ladder roles (house-wise); ruling-planet membership
> 54. Nadi roles (jeeva/karma pairs, bhrigu-bindu relation) where computed
> 55. Deity web: nakshatra deity, adhidevata/pratyadhidevata; ishta-devata indication path
>     (karakamsha 12th etc.)
> 56. Remedial mapping: gemstone, beeja/vedic mantra, yantra, dana, vrata-vara, deity —
>     AND whether served remedial priority reflects its actual afflictions
> 57. Medical: avayava/body-part, dhatu, vata-pitta-kapha, disease significations from its
>     afflictions (L0 medical mappings)
> 58. Sambandha table: varna, guna, tattva, gender, direction, season, taste, metal, grain, color
> 59. Nodal axis relations (every graha): nodal dispositor, placement in node's star, node
>     delivering its results (agency rules)
> 60. Special-lagna relations (esp. for Lagna dossier): bhava/hora/ghati/varnada/sree/indu
>     lagna + pranapada — graha's house from each where doctrine uses it
>
> Floor: 60 facet groups. The foundry discovery pass (DB + L0 catalogs + canon) may ADD
> rows; deletion requires native sign-off. Facets absent from the system entirely are
> UNREACHABLE-by-nonexistence findings feeding the Section-6 concept-completeness register.

**This is a FLOOR, not a ceiling** (per the heading's own parenthetical and per Charter §1
/ plan §2.1's "examples are illustrative, never limiting" doctrine). If the executor's DB +
canon discovery pass surfaces additional facets the system holds about an entity that are
not enumerated in the 60 groups above, ADD them as new ledger rows (do not skip them for
lack of a matching row number) — deletion of a floor row requires native sign-off, but
addition requires none.

## 3 — Ledger file (the executor's row-marking surface)

**Path:** `/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/ledgers/facets.jsonl`

This ledger already exists (built by the Foundry ledger-builder pass) with **1,500 rows**:
60 facet-groups × 10 entities (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu,
Lagna — the 9 grahas + Lagna) × 2 charts (750 rows per chart) = 20 dossiers. Each row is one
JSON object, one per line (JSONL — no surrounding array, no trailing commas), with schema:

```json
{
  "row_id": "F00001",
  "facet_number": 1,
  "facet_group": "B-I Positional & coordinate",
  "facet_text": "Sign, degree-minute-second; bhoga traversed",
  "entity": "Sun",
  "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
  "held_in_db": null,
  "wire_reachable": null,
  "reachable_in_2_calls": null,
  "usable_form": null,
  "status": "pending",
  "tag": "floor"
}
```

**Executor obligation per row:**
- `held_in_db`: boolean — result of the data-plane enumeration pass (SELECT-only query
  against `chart_facts` / `chart_divisionals` / `bodha_*` / `kala_*` / `phala_*` /
  `mimamsa_*` tables and any relevant L0 catalog table, per `CAPABILITY_MANIFEST.json`).
- `wire_reachable`: boolean — could a consuming LLM retrieve this facet via ANY MCP tool
  call sequence (unbounded calls)?
- `reachable_in_2_calls`: boolean — could it be retrieved in ≤2 calls specifically (the
  plan's stated ceiling for "reasonable consuming LLM" behavior; see Charter §7.5.2 for the
  cognate "reasonable consuming LLM" standard used elsewhere in this audit)?
- `usable_form`: boolean — graded per Charter §7.1 ("Usable form" rubric): referential
  resolvability, narration integrity, budget proportionality, signal-to-trivia ratio.
- `status`: one of `pending` → `in_progress` → `done`. Rows never silently regress from
  `done`.
- Any row with `held_in_db=true` and (`wire_reachable=false` OR `reachable_in_2_calls=false`
  OR `usable_form=false`) is a **held-but-not-received facet** and MUST be root-caused into
  exactly one of the Charter §2 (plan §4) failure classes 1-9, with a finding record
  written per the Charter §3 finding schema, appended to
  `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` after a dedupe check against the
  existing ~200 rows (including anchor rows R-37..R-48).
- **New facet rows** (added beyond the 1,500-row floor per Section 2's "floor not ceiling"
  clause) get fresh `row_id`s continuing the `F#####` sequence, `tag: "discovered"` instead
  of `"floor"`, and are otherwise graded identically.

**Completeness is a count query.** At any point, run:
```sql
-- illustrative; run as a jq/python count over the JSONL, not literal SQL against facets.jsonl
```
i.e., `status=="done"` row count over total row count (1,500 + any discovered rows) is the
lane's completeness percentage. This is what makes Charter §4 satisfaction criterion 3
("20/20 entity dossiers with full facet matrices") machine-checkable without re-reading
prose.

## 4 — Extensions (this brief's operational instantiation of the protocol)

**Output artifact:** the per-entity **retrievability matrix** — for each of the 20 dossiers,
a facet × {held in DB? | wire-reachable? | ≤2 calls? | usable form?} table, materialized
directly from the `facets.jsonl` ledger rows filtered by `entity` + `chart_id` (60+ rows
per dossier). This is deliverable 4 in plan §7 (see Section 7 below).

**Root-causing discipline (mandatory, not optional):** "Every held-but-not-received facet
is root-caused into a Section 4 class" — this is the plan's own framing (§5 line 221-222,
referring there to the plan's own §4; in this brief's numbering that is Charter §2, the
9-class taxonomy). Concretely: for every ledger row where `held_in_db=true` but any of
`wire_reachable` / `reachable_in_2_calls` / `usable_form` is `false`, the executor asks
"WHY is the LLM not receiving this" (the lane's entire question, per the plan) and answers
it with exactly one primary failure class from Charter §2 (classes 1 UNREACHABLE, 2 WRONG,
3 INCONSISTENT, 4 EMPTY SHELL, 5 DISHONEST SELF-DESCRIPTION, 6 UNUSABLE FORM, 7 DROWNED,
8 UN-SYNTHESIZABLE AT SCALE, 9 UNGOVERNED JUDGMENT), attached as a finding record.

**10-group draft status (explicit, per task instruction):** the 10-group facet checklist at
plan lines 226-244 (transcribed in Section 1 above) is **RETAINED FOR AUDIT TRAIL ONLY**. It
is superseded in full by Appendix B (the 60-facet floor, transcribed in Section 2 above).
The executor grades against Appendix B / `facets.jsonl` exclusively; the 10-group draft is
preserved in this brief purely so that a reviewer can trace the plan's own evolution from
draft to floor — it carries no grading authority.

## 5 — Rubric reference

Apply **Charter §7.1 — "Usable form" rubric** (derived from plan §4 classes 6 UNUSABLE FORM
and 7 DROWNED) to populate every `usable_form` column value in the ledger. Do not re-derive
this rubric here — read it from the Charter at execution time; it is DRAFT pending Cowork
ratification per the Charter's own gating note, and Lane 8 inherits that gate (it may not
execute the `usable_form` grading pass against an un-ratified rubric without flagging the
grading as provisional in its trace file until ratification lands).

Where a facet's retrieval requires composing multiple tool calls or judgment about which
tool to call, also apply **Charter §7.2 — "Synthesizability-as-received" rubric** on first
contact with the fronting tool, and log any undocumented-requirement instance as a class-9
(UNGOVERNED JUDGMENT) finding per that rubric's own instruction.

## 6 — Checkpoint / RESUME instructions

**State file (owned exclusively by this lane's conductor):**
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/state/LANE8.md`

Per Charter §5 (RESUME protocol, derived from plan §12 items 3-4):
- `state/LANE8.md` is a shard-index file, regenerated **atomically and idempotently** by
  the Lane 8 conductor at every checkpoint, derived purely from the current state of the
  20 per-shard worker trace files (Section 8 below) plus the `facets.jsonl` ledger's own
  `status` column counts. Regeneration is a pure function of those inputs — safe to
  re-run, safe if interrupted mid-write (a torn/partial write is itself a defect per
  Charter §5's atomicity contract, not an acceptable RESUME state).
- `state/LANE8.md` content (minimum fields): per-dossier (20 rows) — dossier id (entity ×
  chart), shard trace file path, rows-done/rows-total (out of the dossier's ~60-75 rows),
  findings-count so far, status (`not_started` / `in_progress` / `done`), and a
  **RESUME pointer = last completed shard id** at the top of the file (i.e., which of the
  20 dossier shards the conductor should treat as the resumption point if the lane was
  interrupted mid-run — not "last completed row," since each shard/worker is the atomic
  unit of dispatch; within a partially-done shard, the worker's own trace file carries the
  last completed `row_id` per Section 8(e) below).
- **On a fresh/resumed session:** read `state/LANE8.md` first. For any dossier shard marked
  `done`, do not re-dispatch. For any shard marked `in_progress` or `not_started`, dispatch
  (or re-dispatch) a fresh worker for exactly that shard, which itself resumes from its own
  shard trace file's last completed row (Section 8(e)).
- **Never** re-does completed rows; **never** silently skips undone ones — both directions
  are checked by reading `facets.jsonl`'s `status` column directly (ground truth) against
  `state/LANE8.md`'s claims (index) — a mismatch between the two is itself flagged and
  reconciled before new dispatch, not silently trusted.
- This lane's checkpointing must be **incremental** (per Charter §3 "Checkpointing"): a
  session interruption at any point never loses completed rows already written to
  `facets.jsonl` or to a shard trace file.

## 7 — Deliverable spec (cross-referenced to plan §7)

Plan §7 (lines 307-323) lists 9 audit deliverables. Lane 8 is explicitly responsible for:

> 4. 20 entity retrievability matrices (Lane 8).

Concretely, Lane 8 produces:
1. **The completed `facets.jsonl` ledger** (all rows `status="done"`, all four boolean
   columns populated, plus any `tag:"discovered"` rows added under the floor-not-ceiling
   clause) — this is the primary data artifact.
2. **20 per-entity retrievability matrices** — one per dossier (entity × chart), rendered
   from the ledger as facet × {held/reachable/≤2-calls/usable} tables. These may be
   materialized as a single compiled markdown/JSON view over the ledger (grouped by
   `entity` + `chart_id`) rather than 20 separate files, provided every dossier's full
   matrix is reconstructable from it — the deliverable is the matrix content, not a
   mandated file-per-dossier layout.
3. **Finding records** for every held-but-not-received facet, appended to
   `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (new, deduped rows only) per Charter
   §3, and contributing to the lane's slice of deliverable 2 (the machine-readable findings
   JSON, plan §7 item 2) — every Lane 8 finding carries the full Charter §3 field set.
4. Lane 8 also feeds, but does not own: deliverable 1 (`LLM_CONSUMPTION_AUDIT_v1_0.md`
   report — Lane 8's section within it), and deliverable 3 (register appends, already
   covered in item 3 above).

Lane 8's contribution to Charter §4 satisfaction criterion 3 ("Depth completeness —
20/20 entity dossiers with full facet matrices; every held-but-not-received facet
root-caused") is satisfied when: all 20 dossiers show 100% `status="done"` in
`facets.jsonl`, AND every row with a held-but-not-received pattern has exactly one
Charter §2 failure class attached via its finding record.

## 8 — Per-lane coverage self-declaration template (TAP-9 style)

At lane close, the conductor emits a table with this exact column structure, one row per
audited surface, no surface omitted:

| surface | status (audited / deferred) | reason-if-deferred |
|---|---|---|
| Sun dossier — chart 482012f1 | | |
| Moon dossier — chart 482012f1 | | |
| Mars dossier — chart 482012f1 | | |
| Mercury dossier — chart 482012f1 | | |
| Jupiter dossier — chart 482012f1 | | |
| Venus dossier — chart 482012f1 | | |
| Saturn dossier — chart 482012f1 | | |
| Rahu dossier — chart 482012f1 | | |
| Ketu dossier — chart 482012f1 | | |
| Lagna dossier — chart 482012f1 | | |
| Sun dossier — chart 1c826d5a | | |
| Moon dossier — chart 1c826d5a | | |
| Mars dossier — chart 1c826d5a | | |
| Mercury dossier — chart 1c826d5a | | |
| Jupiter dossier — chart 1c826d5a | | |
| Venus dossier — chart 1c826d5a | | |
| Saturn dossier — chart 1c826d5a | | |
| Rahu dossier — chart 1c826d5a | | |
| Ketu dossier — chart 1c826d5a | | |
| Lagna dossier — chart 1c826d5a | | |
| Appendix B facet floor (60 groups) — coverage completeness | | |
| Discovered facets beyond the floor (if any) | | |

Every row must be marked `audited` or `deferred`; a `deferred` row without a stated reason
fails Charter §4 satisfaction criterion 4 (coverage honesty) and the lane does not close.

## 9 — Swarm decomposition (MANDATORY; plan §12.7)

This section specifies Lane 8's instantiation of the Charter §6 execution DAG's
conductor+worker-swarm pattern, exactly as plan §12.7 requires every phase and lane to run.

**(a) Conductor + worker pattern.** Lane 8 runs as one CONDUCTOR session plus a swarm of
WORKER sub-agents. The conductor owns the lane's ledger (`facets.jsonl`) and state index
(`state/LANE8.md`); it shards the 20-dossier workload, spawns a fresh sub-agent per shard
(each worker receives ONLY the Charter excerpt it needs — doctrine, taxonomy, finding
schema, and the Charter §7.1/§7.2 rubrics — plus this brief's Sections 1-5 and its own
single shard's row set from `facets.jsonl`; full attention, zero context decay, no need to
hold the other 19 dossiers in context). Workers execute the DB-enumeration pass and the
MCP-wire-retrieval pass for their one dossier, populate their assigned ledger rows, write
findings, and produce a shard trace file. The conductor collects all 20 shard traces,
merges them into `state/LANE8.md`, and updates lane-level status.

**(b) Shard key.** **One worker per dossier — 20 workers** (9 grahas + Lagna, × 2 charts).
Each worker's shard is exactly one `(entity, chart_id)` pair, i.e., exactly the ~60-75
ledger rows in `facets.jsonl` matching that entity+chart combination. This is the plan's
own stated sharding for Lane 8 (§12.7 "Intra-lane sharding": "Lane 8 one worker per dossier
(20 workers)").

**(c) Concurrency cap + throttling rule.** The conductor runs **5-10 concurrent workers**
at any one time (subscription-limit-bound, per plan §12.7's "concurrency-capped batches,
e.g. 5-10 workers, the conductor throttles to subscription limits" standard, stated there
for Lane 2 and adopted here identically for Lane 8's 20-worker pool). Concretely: the
conductor dispatches workers in waves of up to 10, and throttles (reduces the in-flight
count, inserts a wait, or retries with backoff) on any rate-limit signal it receives from
the harness or from the `mcp__postgres__query` / MCP tool surfaces the workers call. No
more than 10 dossiers are ever in-flight simultaneously; the remaining 10 queue until a
slot frees.

**(d) Merge protocol.** Workers write ONLY their own shard trace file at
`state/LANE8/shard-<dossier-id>.md` (dossier-id = `<entity>_<chart-short-id>`, e.g.
`Mercury_482012f1`, `Lagna_1c826d5a`) — **never** a shared file. Workers append their
graded rows directly to `facets.jsonl` (each row keyed by its unique `row_id`, so
concurrent appends from different workers touch disjoint keys — no write contention on a
per-row basis) and write findings to their own trace file, not directly to the shared
defect register. The conductor ALONE reads all 20 shard traces plus the ledger's current
state and merges into `state/LANE8.md` (the index) and, at lane-close, performs the single
dedupe-and-append pass into `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` (register
writes are conductor-only, precisely to make the dedupe-against-~200-existing-rows check in
Charter §3 a single serialized operation rather than a race between 20 workers). No worker
writes to a file another worker also writes to; no worker writes to the shared state index
or the shared register.

**(e) Per-shard RESUME semantics.** Each worker's trace file
(`state/LANE8/shard-<dossier-id>.md`) records, at minimum: the dossier id, the ordered list
of `row_id`s it has completed so far, and an explicit **RESUME pointer** field of the exact
form `resume_after_row_id: F#####` (the `row_id` of the last ledger row this shard fully
graded — all four boolean columns set and `status="done"` — before any interruption). A
re-dispatched worker for an already-partially-done shard reads its own trace file, finds
`resume_after_row_id`, and continues grading from the next `row_id` in its shard's row set
(sorted by `facet_number`) — it never re-grades rows at or before the pointer, and never
skips rows after it. If a shard trace file does not yet exist for a dossier, the worker
starts fresh with `resume_after_row_id: null` (equivalent to "before the first row of this
shard").

---

*End of Lane 8 brief v1.0. Self-contained per Brief Foundry instruction: charter-by-
reference for doctrine/taxonomy/schema/criteria/rubrics; full transcription of plan §5
(Lane 8 intro, lines 216-244) and Appendix B (60-facet floor, lines 489-597) in Sections
1-2 above; ledger, protocol, extensions, rubric reference, checkpoint/RESUME, deliverable
spec, coverage self-declaration, and mandatory swarm decomposition in Sections 3-9.*
