# Lane 2 Evidence-Sufficiency — Shard 2-b5 (D4–D7, Karma & Vritti)

Worker: Lane2 evidence-sufficiency (P-12 evidence-plan-then-acquire). Charter §7.3 4-point scale.
Charts: A=`482012f1-710e-4a25-994a-93821f5871aa` (native), B=`1c826d5a-41cb-4450-b4dc-59d440e5f75a`.
Transport: deployed MCP connector (read-only). Throttled. NO write tools called.

## Status
- Rows: 16/16 graded. Findings captured: 9 distinct (shared across rows).
- trim_seen: YES (assess_career, graha_portrait, get_domain_reading, get_signals).

## Evidence acquired (shared substrate; reused across variants/charts)

### Timing surfaces
- `get_temporal_windows` / `kala_windows_get` (A & B): `activation_count=0, predicate_count=0` for the
  default 1-yr window (2026-07-11→2027-07-11). EMPTY. drill_next points to L3 tools not surfaced as MCP.
  → R-45 kala_activation empty-shell rediscovery. **class 4**.
- `get_projections` (A & B): envelope `projections_total:0, projections_returned:0` BUT `content.projections`
  carries **50 rows**. Domains A={general:48, health:2}; B={general:36, career:8, health:6}. NO crisis/fall
  domain. Generic "General activation near <date>" narratives, falsifiability names "relocation, legal
  matter, public recognition". → receipt contradicts payload. **class 5**.
- `phala_outlook` (A & B): 5 anchors each, **direction=elevated for ALL** (no fall/decline/adverse anchor
  exists); A domains {transition:4, career:1}; B {transition:3, career:2}; all magnitude=minor, conf=0.322,
  all inside ONE 3-month window (2026-07-11→2026-10-09); 4 near-identical transition rows. Rich schema
  (confidence_band basis "structural_not_yet_empirical", structured_falsifier, derivation_ledger).
- `get_dashas` (A & B): solid Vimshottari ladder w/ lord house/sign/nakshatra + verification. A: Mercury MD
  (natal h10, Capricorn) ends 2027-08-18 → dasha junction. B: Saturn MD (natal **h8**) to 2029-04-23.
  DEPTH GAP: `lord_natal_dignity_d1=null`, `lord_natal_shadbala_total=null` in returned rows.

### Structural / domain surfaces
- `get_domain_reading` domain=career (A): orientation-digest wrapper + `question_lenses` (2: one `career`,
  one **`progeny`** — wrong lens for a career query), `cdlm_cells`, `signal_id_refs_total=12364 (capped)`.
  `token_safety_note: "Bounded to 3 lenses × 20 signals..."`. Ranked signals = {salience, signal_id,
  source_l1_asset, signal_type_class} — **IDs, no inline text** in the lens; top signal_id identical across
  both lenses (09471d69, salience 2.99). trim/cap present.
- `get_signals` domain=career (A): 50 signals returned, `pagination.total=null`, `truncated` present.
  Text IS inline (`signal_summary_text`) but as TAXONOMY: e.g. `category=navamsha_d9_cross_check | key=jupiter
  | d1_dignity=own | d9_dignity=Enemy | classification=broken_promise`; `category=graha_yoga_karaka_flag |
  key=is_yoga_karaka | value_text=false`; multiple 2.3-salience centrality/dispositor-tree descriptive rows.
- `assess_career` (A): **1,045,750 bytes** over the wire. `house_analysis` alone = 1,028,634 B (98%).
  `step_results`=125 B (near-empty), `verdict_skeleton`=4501 B (skeleton), `karaka_analysis`=1939 B.
  `judgment_flags: ["response_still_over_40kb_budget_after_full_trim"]`; `trim_report` says "full trim_report
  omitted to fit budget". → 25× its own 40 kB budget, self-admits, ships anyway.
- `graha_portrait` Sun (A): rich Mercury-standard dossier (position, dignity per D1/D9/D10/D60,
  functional_nature=temporal_malefic, strength, avasthas, yogas, dashas, cgm_neighborhood, completeness).
  Sun D1 Capricorn h10 neutral; D9 Cancer h1 neutral. `trim_report original_count=11, kept_count=1`
  ("omitted to fit budget"); `pagination.total=null`.

## No dedicated domain
- No `authority` or `fame` domain in get_domain_reading; no apex assess for authority/fame (only
  marriage/career/health/wealth). D6/D7 require executor decomposition → Sun karaka + 10th + career + yogas.

## Findings (F1–F9), classes per §4
F1 get_projections envelope total/returned=0 while 50 rows present — **class 5** (both charts). HIGH.
F2 kala windows empty (activation_count 0) — **class 4** EMPTY SHELL / R-45 (both charts). HIGH.
F3 phala_outlook has NO adverse/fall direction (all "elevated"); 4 near-dup transition anchors — width gap
   for D4 + **class 7** duplication. HIGH for D4.
F4 assess_career 1.03 MB un-budgeted dump w/ self-admitted over-budget flag — **class 6** + **class 5**. HIGH.
F5 get_signals summaries are raw taxonomy strings, not life-language; pagination.total=null — **class 9**
   (taxonomy→life-language translation forced) + class 5 (null total). MED.
F6 get_domain_reading domain=career surfaced a `progeny` lens — **class 3/6** wrong-lens. MED (lower conf).
F7 No authority/fame domain or assess tool → executor silently decomposes — **class 9** UNGOVERNED
   JUDGMENT (silent decomposition). HIGH for D6/D7.
F8 graha_portrait trim_report original_count 11 / kept_count 1 (omitted); pagination.total null — **class 5**
   opaque trim receipt. MED.
F9 domain career lens total 12384, identical-salience walls + descriptive-trivia (centrality/dispositor
   tree) at same tier + 299-signal UNATTRIBUTED bucket — **class 7** DROWNED / R-44+R-37. MED.

## Class-9 improvisation log (per this batch)
- Method/krama choice: chose dasha-ladder + phala_outlook + graha_portrait as the crisis/timing krama — system
  supplies no governed method for "crisis window" or "job-change" queries.
- Silent decomposition: D6 "authority relationship" → Sun(karaka)+10th+career; D7 "fame" → Sun+10th+RajaYoga+
  Digbala. No modeled domain; decomposition ungoverned.
- Conflict adjudication: get_projections envelope(0) vs payload(50) — executor had to pick the payload.
- Taxonomy translation: every get_signals row (`classification=broken_promise` etc.) → life meaning.

## Verdicts (§7.3)
D4 narrow A/B: INSUFFICIENT (no adverse-window surface; kala empty; projections general; phala all-elevated).
D4 broad  A/B: SUFFICIENT-WITH-GAPS (structural vulnerability composable via dasha/8th/doshas; windows absent).
D5 narrow A/B: SUFFICIENT-WITH-GAPS (transition anchor + dasha junction, but thin/low-conf; kala empty).
D5 broad  A/B: SUFFICIENT-WITH-GAPS (dasha ladder + transition/career anchors; no job-change activation).
D6 narrow A/B: INSUFFICIENT (no authority-relation modeling; only structural Sun facts; class-9 decomp).
D6 broad  A/B: SUFFICIENT-WITH-GAPS (Sun dossier + functional_nature + career composable).
D7 narrow A/B: SUFFICIENT-WITH-GAPS (Raja-yoga/Sun/10th retrievable; timing weak; fame not modeled).
D7 broad  A/B: SUFFICIENT-WITH-GAPS (Sun dossier + 15 yogas + 10th + career composable).

---

## ADDENDUM — independent re-run corroboration (verifier-style, second pass)

Re-acquired against the same two charts via a partly different toolset. Prior F1–F9 REPRODUCED.
Additive findings and confirmations:

- **F2 confirmed + extended (class 4 + class 5):** `get_temporal_windows` AND `kala_windows_get` return
  `activation_count=0`. Passed explicit `date_from=2005-01-01, date_to=2027-01-01`; response **echoed the
  default `2026-07-12→2027-07-12`** — the date range args are silently dropped. Not just empty: the historical
  window (where any past crisis/fall would live) is unreachable by design of the serving layer. R-45.
- **F3 confirmed via a second tool:** `phala_predictive_anchors_get direction=negative` (P1) → `anchor_count:0`.
  `event_anchors` (P1=4, P2=7) are **100% direction=elevated**; event-type vocabulary =
  {career_discovery_event, transition_discovery_event, transition_bhavishya_event, health_bhavishya_event,
  spiritual_turn, career_entry} — **no crisis / fall / decline / recovery type is computed anywhere**. This is
  UNREACHABLE-BY-NONEXISTENCE for D4, not merely a retrieval miss (**class 1**). P2 `phala_predictive career`
  anchor_count=44, 11 returned, near-all identical window `2027-10-20→2030-04-03` (duplication wall, class 7).
- **NEW finding F10 (class 6 / serving bug):** `get_signals.min_salience` schema max = **1.0**, but chart signal
  salience reaches **2.99** (max_salience in every orientation digest). The consumer cannot filter to the
  chart-defining top tier (>1.0) — the filter's range is narrower than the data's. MED.
- **NEW finding F11 (class 8 / class 6):** `kala_life_arc` `parva_quality` vocabulary =
  {peak, consolidating, building, transitional, receding} tracks **convergence magnitude, not hardship valence**.
  P1: zero hardship-flavored parvas; P2: only `receding×2`, undated within-parva, no recovery pairing. The life-arc
  surface cannot distinguish a fall from a growth phase — D4's core need. Overlapping parva spans (P1 parva 8
  Saturn 1991–2010 overlaps parvas 9/18/19) add form confusion. `pagination`/`grounding`=null.
- **F6 confirmed:** `get_domain_reading domain=career` again returned a `progeny` lens beside the career lens
  (wrong-lens, class 3/6); `signal_id_refs_total=12364, capped→200`, lens rows are ID-only (class 6).
- **judgment_query career (STRONG, both charts):** deterministic 10th-house checklist with honest `receipt`
  (bhanga_checked:false disclosed) + honest `judgment_flags`. P1 `convergent_strong (+3.4)`, P2 `mixed (-0.8)`.
  This is the best synthesizable surface for D6/D7 — but it emits ONE career verdict; authority-vs-fame is not
  sub-typed, so D6/D7 still require class-9 decomposition (F7). trim_report original 5→kept 1; pagination.limit:0.

Second-pass verdicts agree with prior block. trim_seen=TRUE reconfirmed (judgment trim_report,
domain_reading 12364→200, apex/assess 1MB, phala 44→11, get_signals 1711→8).

