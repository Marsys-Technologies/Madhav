# Lane 2 — Evidence-Sufficiency Shard 2-b4

Worker: Lane 2 EVIDENCE-SUFFICIENCY (P-12 evidence-plan-then-acquire).
Channel: DEPLOYED MCP connector (read-only), `amjis-mcp-qm256lasva-el.a.run.app`.
Charter: `CHARTER.md §7.3` (4-point scale), §4 (9-class taxonomy).
Charts: `482012f1…` = Abhisek (C1); `1c826d5a…` = Abhinandan (C2).
Questions: C5 (Vidya — higher/spiritual learning), D1 (nature of profession),
D2 (service vs business vs practice), D3 (rise timing) × {narrow,broad} × {C1,C2} = 16.

trim_seen: **TRUE** — graha_portrait `trim_report` (original 11–12 → kept 1); domain-reading
`signal_id_refs_capped:true` (200 of 12364); Mercury narration cut mid-clause
"…consistent read across D…[truncated for budget]".

---

## Shared evidence base (acquired once, reused across question rows)

### Tools called (read-only)
| tool | args | result shape / verdict |
|---|---|---|
| tools/list | — | 130 tools enumerated |
| get_domain_reading | C1 domain=career | 23.6KB. `top_signals:[]`; entity_profiles=UNATTRIBUTED(299)+KETU(1); `signal_id_refs`=200 bare UUIDs capped from 12364; question_lenses leaked **progeny** into a career query |
| apex_career_assess | C1, C2 | TEXT channel 39B "[large payload — see structuredContent]"; structuredContent ~1MB. verdict_skeleton.top_10 = readable `summary` strings; `by_stage`: yoga+varga populated, **karaka/lord/strength/temporal EMPTY** (both charts) |
| get_temporal_windows | C1, C2 | orientation digest + `content.activations:[]` `predicates:[]` — **activation_count 0 both charts** |
| kala_windows_get | C1 | `activations:[], activation_count:0, predicates:[]` (R-45) |
| get_dashas | C1, C2 | WORKS. C1: Mercury MD (10th-lord, Capricorn, natal house 10) to 2027-08 → Ketu; **`lord_natal_dignity_d1`/`shadbala` NULL on C1**. C2: 50 rows, dignity POPULATED (Saturn own h8, Jupiter debilitated h10…) |
| kala_life_arc_get | C1, C2 | WORKS. Narrated parvas (dasha spans, quality, theme_keywords, high_convergence_count). C2 has Ketu "renunciation/spirituality" parva |
| get_domain_reading | C1 domain=spirituality / education | domain=education ACCEPTED but returns **domain-agnostic** orientation digest (identical UNATTRIBUTED(299) to career). spirituality lenses = education+foreign_travel+spirituality; top_signals:[] |
| graha_portrait | C1 Jupiter, Mercury | **GOOD narrated dossier**: 8/8 facets ✓ (position/dignity/functional_nature/strength/avasthas/yogas/dashas/cgm), grounded fact_ids, chart_header. Jupiter=own Sagittarius 9th, D9 neutral Gemini 12th. Mercury=neutral Capricorn 10th, D9 Capricorn 7th (narration **truncated mid-clause**). trim_report original 11–12→kept 1 |
| query_chart_facts | C1 NL query | **NL `query` arg ignored** — dumped 115KB full pivoted fact table alphabetically (Amatyakaraka=Saturn h7, AK_PADA Purva Bhadrapada…). Un-budgeted |
| phala_outlook_get | C1 | WORKS. 12-mo forward anchors: windows + confidence_band ("structural_not_yet_empirical") + falsifiers + domains (transition…) |

### Cross-cutting defects (apply to multiple question rows)
- **F-A (class 4):** `get_domain_reading.top_signals` EMPTY on every domain/chart — the ranked
  synthesis surface the whole-chart-read (B.11) is supposed to hand the consumer is blank.
- **F-B (class 7):** entity_profiles collapses to a single `UNATTRIBUTED` bucket of 299
  signals (R-44 analog) — no graha attribution to synthesize from.
- **F-C (class 6):** domain-reading `signal_id_refs` = 200 bare UUIDs, capped from 12364,
  no resolvable text in-response. Consumer cannot render without N chained calls.
- **F-D (class 4):** apex_career `by_stage.lord`/`karaka`/`strength`/`temporal` EMPTY both
  charts — the 10th-lord & karma-karaka stages (the crux of D1/D2) return nothing.
- **F-E (class 6):** apex_/graha_portrait TEXT channel is a 39–107B "see structuredContent"
  pointer; the real payload (up to ~1MB) lives only in structuredContent — a plain MCP
  text consumer gets nothing usable; also an un-budgeted 1MB dump.
- **F-F (class 4):** get_temporal_windows + kala_windows_get return activation_count 0 on
  BOTH charts (R-45) — kills structural×temporal convergence-window rise timing.
- **F-G (class 6):** graha_portrait narration truncated mid-clause "…[truncated for
  budget]" (disclosed, but breaks narration integrity).
- **F-H (class 1):** no apex/dedicated synthesized assessor for vidya/spirituality/education
  (only marriage/career/health/wealth) — C5 has no verdict surface, only the drowned
  domain reading.
- **F-I (class 5):** domain=education returns the same domain-agnostic orientation digest as
  every other domain — the digest advertises domain-sensitivity it does not apply.
- **F-J (class 6):** query_chart_facts ignores its NL `query` arg and dumps 115KB of all
  facts — the targeted-retrieval affordance is non-functional.
- **F-K (class 3):** get_dashas `lord_natal_dignity_d1`/`shadbala` NULL on C1 but populated
  on C2 under identical default args — inter-chart depth inconsistency (low confidence;
  possibly a compact-fields default divergence).
- **F-9x (class 9 — logged every occurrence):** method/krama choice (which grahas to
  portrait); silent decomposition (C5 → 9th higher-ed vs 5th/Ketu/12th moksha; D2 →
  service/business/practice rule); conflict adjudication (drowned domain reading vs clean
  graha_portrait); taxonomy→life-language translation (dignity=own,house=9 → "learned,
  dharmic, higher-philosophy bent"). NO governing surface exists for the D2
  service-vs-business-vs-practice classification — the classical rule is applied entirely by
  the consuming LLM.

---

## Per-question gradings

**All 16 graded SUFFICIENT-WITH-GAPS.** Rationale: `graha_portrait` supplies a genuine
Mercury-standard narrated dossier per graha (8/8 facets, grounded) that rescues
composability for every question — so no row is INSUFFICIENT. But every row is forced onto
that per-graha path because the *synthesized* surfaces (domain reading top_signals, apex
by_stage lord/karaka) are empty/drowned, and every row incurs class-9 improvisation +
specific class 1/4/6/7 gaps. Broad variants additionally rest their whole-chart integration
on the drowned domain reading (F-A/B/C), lowering the ceiling further but still composable
via multiple graha_portrait calls.

- **C5 (Vidya) C1/C2 narrow+broad:** graha_portrait Jupiter (vidya karaka, own 9th) + Ketu
  (moksha) + 9th/5th facts + life-arc spiritual parvas → composable. GAPS: F-H (no vidya
  assessor), F-A/B/C (spirituality domain drowned), F-I (education==generic digest), F-9x
  (decompose higher-learning vs spiritual-learning; choose grahas). Broad adds F-A/B/C
  ceiling.
- **D1 (nature of profession) C1/C2:** apex_career top_10 summaries + graha_portrait
  Mercury(10th-lord)/Saturn(karma karaka) + dashas → composable. GAPS: F-D (lord/karaka
  stage empty — the most direct factor), F-E, F-G (Mercury narration truncated), D10
  dasamsa not surfaced as a stage, F-9x translation.
- **D2 (service vs business vs practice) C1/C2:** placements retrievable (10th-lord Mercury
  in Capricorn/10th; Amatyakaraka Saturn h7; dispositor chain) → an acharya rule CAN be
  applied. GAPS (weakest row): NO surface adjudicates service/business/practice (F-9x
  ungoverned rule + partial class-8), F-D (lord/karaka empty), D10 not surfaced. The
  discrimination rests entirely on consumer-side classical-rule application.
- **D3 (rise timing) C1/C2:** get_dashas + kala_life_arc + phala_outlook forward anchors →
  composable rise narrative. GAPS: F-F (convergence-window surface EMPTY, R-45), F-K (C1
  dasha dignity NULL), phala anchors are domain "transition" not career-rise-specific,
  confidence uncalibrated by design.
