# Lane 3 — Cross-Serving-Path Consistency — Shard 3-b0

Charter: LLM_CONSUMPTION_AUDIT_CHARTER v1.1. Grahas: Sun, Saturn.
chart_id=482012f1-710e-4a25-994a-93821f5871aa. Ayanamshas present: krishnamurti,
lahiri_chitrapaksha, raman, surya_siddhanta_classical, true_chitra (5).

Method: for each quantity served by >1 path, retrieve via each path (DB truth + surgical
wire) per (graha × ayanamsha) and DIFF. §N.5: chart_facts is authoritative over L2+/denorm.

Paths / serving status:
- chart_facts: DB `chart_facts`; surgical wire `query_chart_facts` (ok:true, defaults ayanamsha=lahiri_chitrapaksha, shape=pivoted; NOTE filters fact_subject/fact_category appear IGNORED — full pivoted dump returned).
- chart_dashas: DB `chart_dashas` (denormalized natal-lord metadata columns); surgical wire `query_dasha_periods` (ok:true, serves lord_natal_* columns incl. dignity+shadbala faithfully, defaults to level cap<=3 + window). Wire inherits DB verbatim (incl. NULLs).
- get_signals: surgical wire returns "Tool not in surgical whitelist: get_signals" → full-pipeline-only, served-only-by-down-pipeline, consult broken per LCA-2. UNREACHABLE via surgical for dignity+shadbala third path.

---

## Quantity: sign  [chart_dashas, chart_facts] — CONSISTENT
- Sun: chart_facts SUN.graha_position.sign = Capricorn (all 5 ay); chart_dashas L1 lord_natal_sign = Capricorn (all 5 ay). MATCH.
- Saturn: chart_facts SAT.sign = Libra (all 5 ay); chart_dashas lord_natal_sign = Libra (all 5 ay). MATCH.
- Verdict: consistent, no finding.

## Quantity: house  [chart_dashas, chart_facts] — CONSISTENT
- Sun: chart_facts SUN.house_d1 = 10 (all 5 ay); chart_dashas lord_natal_house_d1 = 10 (all 5 ay). MATCH.
- Saturn: chart_facts SAT.house_d1 = 7 (all 5 ay); chart_dashas lord_natal_house_d1 = 7 (all 5 ay). MATCH.
- Verdict: consistent, no finding.

## Quantity: nakshatra_pada  [chart_dashas, chart_facts] — CONSISTENT (nakshatra cross-checkable; pada single-path)
- nakshatra cross-check per ayanamsha (both paths agree exactly):
  - Sun: krishnamurti=Shravana, lahiri=Shravana, raman=Dhanishta, surya=Dhanishta, true_chitra=Shravana — chart_facts nakshatra == chart_dashas lord_natal_nakshatra for all 5. MATCH. (Apparent "flip" Dhanishta/Shravana is legitimate ayanamsha variation — Sun longitude 291.96–294.92° straddles the 293°20′ boundary; both paths agree ayanamsha-by-ayanamsha.)
  - Saturn: Vishakha (all 5 ay) in both paths. MATCH.
- pada: chart_dashas has NO pada column → single-path (chart_facts only), NO cross-check possible. chart_facts SUN.pada = 4/4/1/1/4 (krish/lahiri/raman/surya/true_chitra); SAT.pada = 1/1/2/2/1. Reachable. Noted: pada not cross-servable.
- Verdict: consistent.

## Quantity: dasha_lord_metadata  [chart_dashas] — SINGLE PATH, reachable (no cross-check) — but two facets defective (see dignity, shadbala)
- query_dasha_periods ok:true; serves lord_natal_house_d1, lord_natal_sign, lord_natal_nakshatra, lord_natal_dignity_d1, lord_natal_shadbala_total, verification_pass_status, citation_ref over wire.
- No second path for the row-shaped metadata bundle itself → no cross-check. BUT its embedded facets dignity + shadbala are cross-checkable against chart_facts and BOTH FAIL (findings below). The metadata bundle is reachable/honest in form; its denormalized dignity + shadbala payload is the defect.

## Quantity: dignity  [chart_dashas, chart_facts, get_signals] — **INCONSISTENT / WRONG (R-43 class)** — consistent=FALSE
FINDING D3-DIGNITY. chart_facts is authoritative (§N.5); chart_dashas is the wrong side.
- chart_facts (AUTHORITATIVE):
  - Saturn: graha_special_state_rollup.is_exalted = "true" (all 5 ay); graha_effective_dignity_modified_by_aspects.effective_dignity_score = 0.975 (all 5 ay). Saturn in Libra = exalted. (No categorical dignity-label fact_key exists in chart_facts — only is_exalted bool + numeric score.)
  - Sun: is_exalted = "false" (all 5 ay); effective_dignity_score = 0.5 (all 5 ay). Sun in Capricorn = non-exalted.
- chart_dashas lord_natal_dignity_d1 (L1 dasha, per ayanamsha, lord_natal_sign stable):
  - Saturn (lord_natal_sign=Libra all 5): "exalted" for krishnamurti, raman, surya_siddhanta_classical; **NULL for lahiri_chitrapaksha, true_chitra.**
  - Sun (lord_natal_sign=Capricorn all 5): "enemy_sign" for krishnamurti, raman, surya_siddhanta_classical; **NULL for lahiri_chitrapaksha, true_chitra.**
- DIFF: chart_facts says Saturn exalted / Sun non-exalted for ALL 5 ayanamshas; chart_dashas drops dignity to NULL for exactly 2 of 5 ayanamshas — lahiri_chitrapaksha (the DEFAULT/primary ayanamsha) and true_chitra — even though lord_natal_sign is stably Libra/Capricorn (dignity is a pure function of sign, so cannot be NULL when sign is present). This is a WRONG value over the wire (NULL ≠ exalted) AND a cross-path INCONSISTENCY (chart_dashas ≠ chart_facts) on the default ayanamsha.
- get_signals path: UNREACHABLE via surgical (LCA-2, not in whitelist) — third path cannot be cross-checked.
- Which side is right: chart_facts (Saturn=exalted, Sun=non-exalted). chart_dashas denormalized dignity is defective (NULL) for lahiri+true_chitra.
- Reproduce:
  - DB truth (facts): `SELECT ... FROM chart_facts WHERE fact_subject IN ('SUN','SAT') AND fact_category='graha_special_state_rollup' AND fact_key='is_exalted'` → SAT true×5, SUN false×5.
  - DB (dashas): `SELECT ayanamsha_id,lord_natal_dignity_d1,lord_natal_sign FROM chart_dashas WHERE lord_graha IN ('Saturn','Sun') AND level_n=1 GROUP BY ...` → NULL for lahiri_chitrapaksha & true_chitra.
  - Wire (dashas): `POST /api/mcp/primitives/query_dasha_periods {"params":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa","system_id":"vimshottari","level_n":1}}` → ok:true; payload carries lord_natal_dignity_d1 verbatim incl. NULLs (defaults to krishnamurti ordering, which DOES have dignity — a consumer selecting lahiri gets NULL).
  - Wire (facts): `POST /api/mcp/primitives/query_chart_facts {"params":{"chart_id":"..."}}` → ok:true, defaults ayanamsha=lahiri_chitrapaksha (exactly the ay where dasha dignity is NULL) — serving-path default mismatch amplifies the divergence.
- Class: 3 INCONSISTENT (primary) + 2 WRONG. Severity: high (dignity is chart-defining; defect lands on default lahiri ayanamsha; served over wire). Suspected layer: L-writer (ka_* dasha-lord metadata denormalization JOIN drops dignity for lahiri_chitrapaksha + true_chitra).

## Quantity: shadbala  [chart_dashas, chart_facts, get_signals] — **INCONSISTENT / EMPTY SHELL** — consistent=FALSE
FINDING D3-SHADBALA. chart_facts authoritative; chart_dashas facet entirely empty.
- chart_facts (AUTHORITATIVE) graha_shadbala_total.rupa:
  - Saturn: 7.83 (krishnamurti, lahiri, surya, true_chitra), 7.57 (raman).
  - Sun: 8.47 (krishnamurti, lahiri, surya, true_chitra), 8.92 (raman).
- chart_dashas lord_natal_shadbala_total: **NULL for ALL rows** (Sun+Saturn, all 5 ayanamshas, all levels) — confirmed served over wire as `"lord_natal_shadbala_total":null` in query_dasha_periods payload.
- DIFF: chart_facts holds real shadbala rupa (7.57–8.92); chart_dashas denormalized lord_natal_shadbala_total is uniformly NULL — the column is advertised in schema + serialized over the wire but never populated. A consumer reading shadbala from the dasha path gets nothing; the value only exists via chart_facts.
- get_signals path: UNREACHABLE via surgical (LCA-2).
- Which side is right: chart_facts (Saturn≈7.83, Sun≈8.47 rupa). chart_dashas shadbala facet is an empty shell.
- Reproduce:
  - Facts DB: `SELECT ... FROM chart_facts WHERE fact_subject IN ('SUN','SAT') AND fact_category='graha_shadbala_total' AND fact_key='rupa'`.
  - Dashas DB: `SELECT DISTINCT lord_natal_shadbala_total FROM chart_dashas WHERE lord_graha IN ('Sun','Saturn')` → NULL.
  - Wire: `query_dasha_periods` payload shows `"lord_natal_shadbala_total":null` for every lord.
- Class: 4 EMPTY SHELL (primary — denormalized column always NULL) + 3 INCONSISTENT (cross-path: null vs populated). Severity: medium-high (shadbala is a core strength facet; absent in the dasha serving path, forcing a second-tool lookup a consumer isn't told to make → also class-9 candidate). Suspected layer: L-writer (dasha-lord shadbala denormalization never wired to chart_facts graha_shadbala_total).

## Secondary note (class 9 candidate — UNGOVERNED JUDGMENT)
Dignity vocabulary mismatch across paths: chart_facts expresses dignity ONLY as
`is_exalted` (bool) + `effective_dignity_score` (numeric 0–1), with NO categorical label;
chart_dashas uses categorical `exalted`/`enemy_sign`/`neutral_sign`. A consumer cross-
checking dignity between the two paths must self-translate (is_exalted=true ⇄ "exalted";
score 0.5 ⇄ "enemy_sign"?) — an undocumented mapping the system does not govern. Low
severity; logged for coverage honesty.

## Reconciliation note (independent re-probe, confirms + one correction)
Independent re-run on ayanamsha=lahiri_chitrapaksha confirms every verdict above.
CORRECTION to the dignity finding: chart_facts DOES carry a categorical dignity label —
`fact_category=graha_dignity_per_varga, fact_key=dignity_state` under varga-qualified
subjects `D1_SAT` and `D1_SUN`: **D1_SAT.dignity_state=exalted, D1_SUN.dignity_state=neutral**
(not merely is_exalted bool). This strengthens the R-43 diff: a directly-comparable
categorical value exists (D1_SAT=exalted) yet chart_dashas.lord_natal_dignity_d1 is NULL on
lahiri_chitrapaksha. The signals third path (`query_signals`→`msr_sql`, ok:true — surgical
substitute since get_signals is whitelist-blocked/LCA-2) surfaces Saturn D1 (house=7)
`dignity_state=exalted`, inheriting chart_facts via constituent_facts — CONSISTENT with the
authoritative side. Note: no shadbala signal appears in Saturn's top-50 signal surface, so
the get_signals path does not serve shadbala at all (shadbala effectively single-path = chart_facts).

## Coverage honesty
- Cross-checkable & consistent: sign, house, nakshatra. 
- Cross-checkable & INCONSISTENT: dignity, shadbala.
- Single-path (no cross-check): pada (chart_facts only), dasha_lord_metadata bundle (chart_dashas only).
- Third path get_signals for dignity+shadbala: deferred UNREACHABLE (LCA-2), not independently re-audited here.
