# Lane 2 Evidence-Sufficiency Shard 2-b14 — Group I: Sthana & Yatra (I1–I4)

Charts: `482012f1…` (native, Abhisek) · `1c826d5a…` (Abhinandan test chart).
Deployed MCP connector (read-only). Grading per CHARTER §7.3. Failure classes per §4.

## Cross-cutting platform facts discovered (bind to every I-row)

- **Domain taxonomy has 6 domains only**: career, character, health, relationship,
  spirituality, wealth (`get_domain_reading` available_domains + `get_chart_orientation`
  convergence_domains). **There is NO relocation / travel / foreign / homeland / sthana /
  yatra domain.** `get_domain_reading domain=relocation` → `"Domain 'relocation' not found"`.
  → The entire Sthana & Yatra group has NO first-class domain surface. **Class 1 UNREACHABLE
  (domain-reading plane).**
- **`judgment_query` requires `domain` OR `bhava`** — a free-text `query` alone is rejected
  (`"either domain or bhava is required"`), and when a `bhava` is supplied the free-text
  `query` string appears **ignored**: bhava-12 verdict is identical whether query is
  "foreign residence settlement abroad" or "travel foreign relocation". → The tool serves a
  generic per-bhava classical-checklist verdict, NOT a question-targeted judgment. **Class 9
  (LLM must itself choose which bhava(s) encode the life-question).**
- **`judgment_query` bhava verdicts carry an honest completeness `receipt`.** For the two
  houses most central to foreign settlement:
  - **bhava 12** (both charts): `karaka:false, yogas_checked:0, bhanga_checked:false`.
    Verdict rests on bhava+bhavesha+from_moon+D1 only. 482→`convergent_moderate 2.2`;
    1c826d5a→`mixed -1`.
  - **bhava 3** (visits/short travel, 482): `karaka:false, yogas_checked:0`; `mixed 0.6`.
  - **bhava 9** (long journeys): FULL checklist (`karaka:true, yogas_checked:14/12,
    varga D20`). 482→`convergent_strong 5.7`; 1c826d5a→`contested -4`.
  - **bhava 4** (homeland/native place): maps to `domain:"education"` (mislabelled for a
    place question), `karaka:true, yogas_checked:0`; 482→`mixed 0.9`.
  Receipt honesty is a POSITIVE (disclosed). But the primary foreign house (12) is served
  with karaka + all yogas + bhanga UNCHECKED → **width deficiency for the exact house the
  question needs most.**
- **`get_temporal_windows` (default 1yr) → `activation_count:0, activations:[], predicates:[]`**
  for 482. The tool advertises kala_activation windows and returns nothing. **Class 4 EMPTY
  SHELL (R-45 class).** Timing must fall back to raw `get_dashas`.
- **`get_dashas`** returns a usable Vimshottari timeline (lord + natal house/sign/nakshatra
  per period; 482 currently Mercury MD→…→Rahu bhukti). Raw — LLM must itself decide which
  dasha "activates relocation" (**class 9 method choice**).
- **Direction (disha) of relocation is NOT modelled anywhere** — no disha/direction
  fact_subject in `query_chart_facts` pivoted dump; no directional tool in the 130-tool list.
  → For I2's direction half: **UNREACHABLE-BY-NONEXISTENCE (data-plane gap).**
- **trim_seen = TRUE (honest budget-cap markers)**: `judgment_query` text = `"[budget-capped
  response — see structuredContent; text duplicate suppressed per R5.1 C1]"`;
  `query_chart_facts` text = `"[large payload — see structuredContent…]"`. Data IS present in
  structuredContent — disclosed, not silent loss → receipt-honest, logged as trim_seen.

## Tools called (per chart, representative)
`get_chart_orientation`, `get_domain_reading` (domain=relocation→404, domain=spirituality),
`judgment_query` (bhava 3/4/9/12), `get_temporal_windows`, `get_dashas`,
`query_chart_facts` (direction probe). Throttled 1s.

## Class-9 UNGOVERNED-JUDGMENT log (recurs on every I-row; requirements spec for method layer)
1. **Significator decomposition** — "foreign settlement" → which houses/grahas (9/12/Rahu/
   dispositor-abroad/4-from-4). Ungoverned; the LLM invents the map.
2. **Settlement-vs-visit discrimination** (I1) — no rule or tool distinguishes permanent
   foreign residence (12H/Rahu strong) from mere visits (3H/9H). Pure improvisation.
3. **Taxonomy→life-language translation** — `verdict_grade=convergent_moderate / composite
   2.2` → must be rendered as "yes/likely/no foreign settlement". No governed mapping.
4. **Conflict adjudication** (I1/I4) — bhava 9 strong-positive vs bhava 12 moderate vs bhava
   3 mixed: how to weight into ONE travel verdict is ungoverned.
5. **Timing method** (I2) — temporal_windows empty → LLM self-selects dasha-based timing.
6. **Direction fabrication risk** (I2) — no data; LLM must omit or fabricate a disha.
7. **Home-vs-away comparison frame** (I3) — no tool contrasts prosperity-at-native-place vs
   away; the entire comparative framework is LLM-constructed; bhava-4 lens is mislabelled
   "education".
8. **Pilgrimage vs generic spirituality** (I4) — spirituality domain lenses are generic
   (points_only, no teertha-yatra/spiritual-travel lens); LLM translates 9H+spirituality
   into "pilgrimage".

## Per-row verdicts

| Row | Chart | Variant | Verdict | Core reason |
|---|---|---|---|---|
| I1 | 482 | narrow | INSUFFICIENT | settlement-vs-visit discriminator unserved; 12H checklist partial |
| I1 | 1c826d5a | narrow | INSUFFICIENT | same; 12H verdict `mixed -1` partial |
| I1 | 482 | broad | SUFFICIENT-WITH-GAPS | general foreign-connection composable from bhava 9/12; no travel domain |
| I1 | 1c826d5a | broad | SUFFICIENT-WITH-GAPS | same |
| I2 | 482 | narrow | INSUFFICIENT | direction UNREACHABLE-BY-NONEXISTENCE; temporal_windows EMPTY SHELL |
| I2 | 1c826d5a | narrow | INSUFFICIENT | same |
| I2 | 482 | broad | SUFFICIENT-WITH-GAPS | rough timing from raw dashas; direction gap + empty windows flagged |
| I2 | 1c826d5a | broad | SUFFICIENT-WITH-GAPS | same |
| I3 | 482 | narrow | INSUFFICIENT | no home-vs-away prosperity contrast; bhava-4 mislabelled education |
| I3 | 1c826d5a | narrow | INSUFFICIENT | same |
| I3 | 482 | broad | SUFFICIENT-WITH-GAPS | bhava-4 + wealth + 12H compose loose contrast; no explicit tool |
| I3 | 1c826d5a | broad | SUFFICIENT-WITH-GAPS | same |
| I4 | 482 | narrow | SUFFICIENT-WITH-GAPS | 9H convergent_strong full-checklist + spirituality domain; no teertha lens |
| I4 | 1c826d5a | narrow | SUFFICIENT-WITH-GAPS | 9H `contested -4` (evidence present, negative); no teertha lens |
| I4 | 482 | broad | SUFFICIENT-WITH-GAPS | strong 9H + spirituality domain; pilgrimage=LLM translation |
| I4 | 1c826d5a | broad | SUFFICIENT-WITH-GAPS | same |

Best-served: I4 (9H fully checklisted + spirituality domain exists). Worst: I2 (direction
has zero data-plane; timing tool empty-shell).
