---
lane: "10"
artifact: LANE10
title: Lane 10 — Promise-vs-Delivery Grading
graded: 67
status: CURRENT
generated: 2026-07-12
verify: blind-reproduced against DEPLOYED amjis-mcp (130 tools, mcp-canary-key, read-only) + DB SELECT for native 482012f1
---

# Lane 10 — Promise-vs-Delivery Grading

Each of the 67 audited assets is graded on whether what the asset *promises* (its
declared capability / catalog claim) is actually *delivered* to a consuming LLM over
the deployed wire. Grading axis is `{verdict, shortfall_layer, evidence}`.

## Verdict spread

| Verdict | Count | Share |
|---|---:|---:|
| DELIVERS | 28 | 41.8% |
| SHORTFALL | 25 | 37.3% |
| PARTIAL | 14 | 20.9% |
| **Total graded** | **67** | **100%** |

## Shortfall-layer distribution

Where a verdict is not DELIVERS, the shortfall is attributed to the plane at which
promise breaks down. `none` = full delivery (the 27 clean-pass assets; +1 DELIVERS
carries a noted-but-defensible caveat — see reconciliation flags below).

| shortfall_layer | Count | Meaning |
|---|---:|---|
| none | 27 | promise met end-to-end; nothing missing |
| retrieval-plane | 23 | computed + stored but no deployed MCP path reaches it, or the fronting tool returns empty |
| data-plane | 6 | the data itself is missing, date-less, or never written |
| ranking-form | 2 | data reachable but presented so the consumer cannot act (attention drowned / no verdict facet) |
| compound | 9 | more than one plane fails simultaneously |

## UNDECLARED (promise-undeclared) list

**Empty.** No asset in the Lane 10 set carried an undeclared/absent promise —
every graded asset made a declarable capability claim that could be tested against
delivery.

```
[]
```

## DELIVERS list (28)

Assets whose promise is fully reachable and honored over the deployed channel
(`shortfall_layer = none`):

**L1 Gaṇita (12):** ga_condition · ga_dashas · ga_nakshatra · ga_panchanga ·
ga_positions · ga_prashna · ga_sade_sati · ga_strength · ga_structural ·
ga_tajaka · ga_transit_anchors · ga_vargas

**L2 Bodha (6):** bo_anveshana · bo_drishti · bo_karanajala · bo_laksana ·
bo_pramana_mapa · bo_upaya

**L3 Kāla (4):** ka_bhavishya_lekha · ka_graha_sancara · ka_jivana_parva ·
ka_muhurta_seva

**L5 Mīmāṃsā (4):** mi_bhavisya · mi_gunanaka · mi_jivanaghatana · mi_seva

**L4 Phala (2):** ph_nimitta · ph_pramana

## HIGH / CRITICAL findings (28 of 61 total findings)

Sorted by severity (critical first), then by asset. `fc` = failure_class.

### CRITICAL (2)

| asset | fc | summary | evidence |
|---|:--:|---|---|
| ka_vighnakara | 4 | 602/638 obstruction (danger) windows never reachable via deployed channel — tool advertises `obstructions` field, returns `[]` | `kala_temporal_bundle -> "obstructions": []` while `SELECT count(*) FROM kala_obstruction = 602` (Abhisek) / 638 (Abhinandan). |
| lel_events | 4 | lel_query serves 0 of the 57 user-authored life_events that exist in DB for Abhisek | `lel_query -> "events": [], "total_count": 0`; `SELECT count(*) FROM life_events WHERE chart_id=Abhisek = 57`. |

### HIGH (26)

| asset | fc | summary | evidence |
|---|:--:|---|---|
| ga_medical | 1 | ga_medical (Vaidya-phala) is computed + stored but has no deployed MCP tool serving it — a whole L1 medical-indication asset is unreachable over the wire. | `SELECT COUNT(*) FROM ga_medical WHERE chart_id=<482012f1\|1c826d5a> = 45` each. Deployed tools/list has zero medical/vaidya/ayurved/organ/dosha-aggravation tools; assess_health is L2 apex, not this L1 table. |
| ga_vastu | 1 | ga_vastu_planet_direction_map fully computed (40 rows/chart, both charts) but has no MCP serving path — the vastu direction-impact map is UNREACHABLE. | DB count 40/40 both charts; grep of `platform/src` + `platform/src/lib/retrieval` for `ga_vastu_planet_direction_map` = 0 serving refs; no vastu tool in deployed tools/list. |
| ga_yoga | 1 | ga_yoga_firings (Nabhasa firings: strength scoring, bhanga/cancellation, partial-formation %, family tagging, dasha-activation windows) has no MCP serving path; only reachable yoga surface (ganita_yogas_get) serves a thinner chart_facts label surface missing every distinctive facet. | grep `ga_yoga_firings` `platform/src` = 0; `get_yoga_dosha.ts` FROM chart_facts only; `ganita_yogas_get` live payload returned chart_facts bhadra_flag/dosha_label rows, no strength/bhanga/family_ids/activation. |
| bo_cdlm_summary | 1 | bodha_cdlm_chart_summary (cross-domain linkage strength summary, 5 rows/chart both charts) has no MCP serving path — UNREACHABLE. | DB count 5/5 both charts; grep `bodha_cdlm_chart_summary` `platform/src` = 0 serving refs. |
| bo_cgm_motifs | 1 | bodha_cgm_motifs (mutual reception / stellium / parivartana patterns; 6 rows on chart Abhinandan) has no MCP serving path. | DB count Abhinandan=6; grep `bodha_cgm_motifs` `platform/src` = 0; no motif field in deployed graph tool payloads. |
| bo_cgm_paths | 1 | bodha_cgm_paths (dispositor chain paths, 45 rows/chart both charts) has no MCP serving path — only an internal L4 ph_nimitta engine reads it; UNREACHABLE over the wire. | DB 45/45 both charts; grep `bodha_cgm_paths` `platform/src` = 0 serving refs; sole reference is `ph_nimitta/engine.py:287` (internal consumer). |
| bo_chart_gestalt | 1 | bo_chart_gestalt is written (5 rows/chart) but no MCP tool exposes bodha_chart_gestalt over the deployed channel. | DB bodha_chart_gestalt=5 (N)/5 (A). grep `bodha_chart_gestalt` = 0; `get_chart_orientation` returns UCD digest, not gestalt threads/verdict-map/zoom-spine. catalog_status=DRAFT. |
| bo_sangati | 4 | Promised per-domain weight-of-evidence ledger (support/oppose/independent-weight/net-verdict/confidence/dissents) was never computed or written to any table. | `bodha_domain_evidence_ledger` table absent; `bodha_cdlm_domain_rollups` cols = {total_inbound_linkage, total_outbound_linkage, diagonal_density, signal_count_for_domain, contradiction_density,…} — none of the promised ledger columns exist. |
| ka_avadhi | 1 | 1571/1585 per-dasha-period dossier rows computed + stored but no MCP tool serves kala_avadhi — fully unreachable. | `kala_avadhi` count=1571 (482012f1)/1585 (1c826d5a); grep `kala_avadhi` across retrieval registry = 0 serving tools (seed file only). |
| ka_dasha_kala | 1 | Scored daśā-eligibility-by-signature service has no deployed front — capability unreachable. | No MCP tool provides signature→scored-interval eligibility; only raw dasha chains (get_dashas) are served. |
| ka_gochara | 1 | Promised transit-EVENT-search engine (aspect crossings, conjunctions, returns, stations, eclipse proximity, multi-planet confluence) has no deployed search path; only a raw ephemeris series is callable. | `query_planet_transit` returns per-day rows only; no event-search tool in deployed tools/list. Consumer must hand-derive every promised event type. |
| ka_kala_darshana | 1 | Lifetime confluence catalog (750 native rows) has no deployed serving tool; the only aggregate surface (kala_temporal_bundle) returns empty (sidecar unavailable). | `kala_temporal_bundle` → convergence_windows:[], kala_summary:'Sidecar unavailable…'. No darshana-specific `_get` tool. 750 stored rows unreachable. |
| ka_kalasutra | 4 | Fronting tool kala_windows_get returns 0 activations/predicates despite 66836 stored rows, and ignores caller date_from/date_to (echoes default window) — EMPTY SHELL. | default → {activations:[], activation_count:0, predicates:[], predicate_count:0}; wide-window retry (1984→2050) identical; filters block shows default 2026-07-12→2027-07-12. `kala_yoga_activation_get` likewise total_count:0. |
| ka_sangam | 1 | Valuable-core convergence windows (6484 rows) have no direct deployed serving tool; the rigor-stratum scoring (rarity_years, orb-strength, confidence, independence discount) is not surfaced — only a derivative projection slice is reachable. | `kala_temporal_bundle.convergence_windows:[]` (mode fallback_empty). `kala_projections_get` exposes convergence_id + effective_score:0.7 but omits rarity_years/orb-strength/confidence_score/independent_current_count. |
| ka_taranga | 1 | Monthly activation waveform (79728 native rows) has no deployed serving tool — computed + stored but entirely unreachable. | DB kala_taranga native=79728, all=159456. Deployed tools/list has no taranga/waveform surface; kala_temporal_bundle returns empty. Zero retrieval path. |
| ka_tulana | 1 | compare(A,B) dissonance-aware verdict facet (proceed/defer/proceed_with_mitigation) has no deployed fronting tool. | No compare/tulana tool in deployed tools/list; `kala_projections_get` + `get_projections` serve ranking only, no head-to-head verdict field. |
| ka_tulana | 7 | Multi-domain attention map drowned: top-ranked entity is UNATTRIBUTED (299 signals, score 64.556) vs next 0.497. | `get_projections` entity_profiles[0]={entity:UNATTRIBUTED, aggregate_score:64.556, signal_count:299}; an acharya cannot act on 'UNATTRIBUTED' as #1 attention target — real grahas buried. |
| ka_yojaka | 6 | 66726/66836 activation predicates are date-less (activation_start NULL) — cannot be bound/searched by the date-windowed engines they were written for. | `count(*) FILTER (activation_start NOT NULL)=110` of 66836; in default 1yr window=0. |
| ka_yojaka | 1 | Stored activation predicates unreachable via deployed serving surfaces (yoga_activation & windows return 0). | `kala_yoga_activation_get` total_count:0; `kala_windows_get` predicate_count:0 despite 66836 DB rows. |
| mi_abhilekha | 4 | Journal service delivers nothing: mimamsa_journal empty on both charts AND no deployed tool surfaces due-predictions read side. | `SELECT count(*) FROM mimamsa_journal = 0/0`; no 'journal' fronting tool in deployed tools/list. |
| ph_phaladesa | 4 | ph_phaladesa narration (the 'DELIVERED OUTLOOK' finale prose) is empty on every row — narration_status='pending' for all 14 rows across both charts. | `phala_phaladesa` narration_status='pending' count=7 per chart (14 total); narration_jsonb unfilled. Registry: 'Narration pending via Gemini/DeepSeek only (Anthropic BANNED by DB CHECK)'. |
| ph_pratikara | 4 | mitigation_map (semantic front for ph_pratikara) returns total_count=0 on both charts despite 602/638 rows in phala_mitigation — a dead advertised path. | `mitigation_map`(Abhisek & Abhinandan): {'mitigations':[], 'total_count':0, 'all_cited':true} source 'phala.mitigation'; DB phala_mitigation=602/638. |
| ph_rectification | 4 | phala_rectification_get returns empty candidate list for native despite 185 DB rows — no candidate birth times reach the consumer. | `phala_rectification_get(482012f1)`→candidates=[], count=0; ayanamsha_id='lahiri'→0. Tool defaults to 'lahiri_chitrapaksha' (not a stored value: lahiri/true_chitra/kp/raman/surya_siddhanta) and filters zero-score rows. |
| ph_rectification | 4 | Rectification scorer is non-discriminating: 0/36 training events matched across all 185 candidates and all 5 ayanamshas; best verdict 'unresolved' win_margin 0. | GROUP BY ayanamsha: max(lel_fit_score)=0.0000, sum(lel_events_matched)=0 for kp/lahiri/raman/surya_siddhanta/true_chitra (tested=36 each). Promised 'far more discriminating than ascendant-sign' not delivered. |
| ph_sankrama | 1 | ph_sankrama (the asset the brief calls the most direct delivery of the founding promise) computed 635 rows but no deployed MCP tool serves them. | `phala_sankrama` count=635 (native)/1265 (Abhinandan); no `*_sankrama_get` tool exists; not in phala_outlook bundle. Multi-hop cross-domain cascades unreachable over the wire. |

**Failure-class legend:** fc1 = computed/stored but no reachable serving path (retrieval-plane).
fc4 = fronting tool exists but returns empty / dead advertised path (retrieval-plane or compound).
fc6 = data present but structurally unusable (date-less → data-plane). fc7 = reachable but
mis-ranked / attention drowned (ranking-form).

## Grading table — asset × {verdict, shortfall_layer, evidence}

The 67 assets. The 28 DELIVERS carry `shortfall_layer = none`. Assets appearing in the
HIGH/CRIT block above carry their attributed shortfall_layer and the evidence summarized
there; consult that block for full DB/grep/tool-payload evidence strings.

| # | asset | verdict | shortfall_layer | evidence (short) |
|--:|---|---|---|---|
| 1 | ga_condition | DELIVERS | none | ganita_condition_get serves 81KB (see reconciliation flag) |
| 2 | ga_dashas | DELIVERS | none | get_dashas serves raw dasha chains |
| 3 | ga_nakshatra | DELIVERS | none | reachable + honored |
| 4 | ga_panchanga | DELIVERS | none | reachable + honored |
| 5 | ga_positions | DELIVERS | none | reachable + honored |
| 6 | ga_prashna | DELIVERS | none | prashna_undertaking_get (by-design-empty for natal; see flag) |
| 7 | ga_sade_sati | DELIVERS | none | reachable + honored |
| 8 | ga_strength | DELIVERS | none | reachable + honored |
| 9 | ga_structural | DELIVERS | none | reachable + honored |
| 10 | ga_tajaka | DELIVERS | none | reachable + honored |
| 11 | ga_transit_anchors | DELIVERS | none | reachable + honored |
| 12 | ga_vargas | DELIVERS | none | reachable + honored |
| 13 | bo_anveshana | DELIVERS | none | reachable + honored |
| 14 | bo_drishti | DELIVERS | none | reachable + honored |
| 15 | bo_karanajala | DELIVERS | none | reachable + honored |
| 16 | bo_laksana | DELIVERS | none | reachable + honored |
| 17 | bo_pramana_mapa | DELIVERS | none | reachable + honored |
| 18 | bo_upaya | DELIVERS | none | reachable + honored |
| 19 | ka_bhavishya_lekha | DELIVERS | none | reachable + honored |
| 20 | ka_graha_sancara | DELIVERS | none | reachable + honored |
| 21 | ka_jivana_parva | DELIVERS | none | reachable + honored |
| 22 | ka_muhurta_seva | DELIVERS | none | reachable + honored |
| 23 | mi_bhavisya | DELIVERS | none | reachable + honored |
| 24 | mi_gunanaka | DELIVERS | none | reachable + honored |
| 25 | mi_jivanaghatana | DELIVERS | none | reachable + honored |
| 26 | mi_seva | DELIVERS | none | reachable + honored |
| 27 | ph_nimitta | DELIVERS | none | reachable + honored (internal consumer of bo_cgm_paths) |
| 28 | ph_pramana | DELIVERS | none | reachable + honored |
| 29 | ga_medical | SHORTFALL | retrieval-plane | HIGH — 45 rows/chart, zero medical MCP tool |
| 30 | ga_vastu | SHORTFALL | retrieval-plane | HIGH — 40 rows/chart, no serving ref |
| 31 | ga_yoga | SHORTFALL | retrieval-plane | HIGH — ga_yoga_firings has no serving path; thin surface only |
| 32 | bo_cdlm_summary | SHORTFALL | retrieval-plane | HIGH — 5 rows/chart, no serving ref (verify-confirmed) |
| 33 | bo_cgm_motifs | SHORTFALL | retrieval-plane | HIGH — 6 rows (A), no serving ref |
| 34 | bo_cgm_paths | SHORTFALL | retrieval-plane | HIGH — 45 rows/chart, internal-only |
| 35 | bo_chart_gestalt | SHORTFALL | retrieval-plane | HIGH — 5 rows/chart, no tool; catalog DRAFT |
| 36 | bo_sangati | SHORTFALL | data-plane | HIGH — promised evidence ledger never written |
| 37 | ka_avadhi | SHORTFALL | retrieval-plane | HIGH — 1571/1585 rows, no serving tool |
| 38 | ka_dasha_kala | SHORTFALL | retrieval-plane | HIGH — no signature→scored-interval front |
| 39 | ka_gochara | SHORTFALL | retrieval-plane | HIGH — no transit-event-search path |
| 40 | ka_kala_darshana | SHORTFALL | retrieval-plane | HIGH — 750 rows, aggregate returns empty |
| 41 | ka_kalasutra | SHORTFALL | compound | HIGH — empty shell; ignores date args; 66836 rows |
| 42 | ka_sangam | SHORTFALL | retrieval-plane | HIGH — 6484 rows; rigor stratum not surfaced |
| 43 | ka_taranga | SHORTFALL | retrieval-plane | HIGH — 79728 rows, no waveform surface |
| 44 | ka_tulana | PARTIAL | compound | HIGH×2 — no verdict facet + attention drowned (UNATTRIBUTED #1) |
| 45 | ka_vighnakara | SHORTFALL | compound | CRITICAL — 602/638 obstructions return [] |
| 46 | ka_yojaka | SHORTFALL | compound | HIGH×2 — 66726/66836 date-less + serving surfaces return 0 |
| 47 | lel_events | SHORTFALL | compound | CRITICAL — 57 events in DB, lel_query serves 0 |
| 48 | mi_abhilekha | SHORTFALL | compound | HIGH — journal empty + no read-side tool |
| 49 | mi_pramana | SHORTFALL | data-plane | verify-confirmed — mimamsa_calibration=0 AND mimamsa_reliability=0 |
| 50 | ph_phaladesa | PARTIAL | data-plane | HIGH — narration_status='pending' all 14 rows |
| 51 | ph_pratikara | SHORTFALL | retrieval-plane | HIGH — mitigation_map returns 0 despite 602/638 rows |
| 52 | ph_rectification | SHORTFALL | compound | HIGH×2 — empty candidate list + non-discriminating scorer |
| 53 | ph_sankrama | SHORTFALL | retrieval-plane | HIGH — 635/1265 rows, no serving tool |
| 54 | ph_suddha_sodhana | SHORTFALL | (per shard) | verify-confirmed SHORTFALL |

> Rows 55–67 (the remaining PARTIAL/SHORTFALL assets making up the 25 SHORTFALL + 14
> PARTIAL totals) are graded in the Lane 10 shard's per-asset detail but were not
> emitted with individual `{verdict, shortfall_layer, evidence}` triples in this
> handoff payload. The verdict spread (28/25/14) and shortfall-layer distribution
> (27/23/6/2/9) above are authoritative and reconcile to 67; this table renders every
> asset for which a per-asset triple was supplied (28 DELIVERS + 26 finding-bearing /
> verify-named assets). The un-itemized remainder are accounted for only in the
> aggregate counts.

## Reconciliation flags (from blind verify — agree=12, disagree=0)

Verified blind against DEPLOYED amjis-mcp (130 tools, mcp-canary-key, read-only) + DB
SELECT for native `482012f1`. All 12 primary Lane 10 verdicts reproduced; disagree=0.

Primary verdicts reproduced: ga_condition DELIVERS · ga_prashna DELIVERS ·
ga_transit_anchors DELIVERS · bo_cdlm_summary SHORTFALL · bo_laksana DELIVERS ·
bo_upaya DELIVERS · ka_jivana_parva DELIVERS · ka_tulana PARTIAL · mi_bhavisya
DELIVERS · mi_pramana SHORTFALL · ph_phaladesa PARTIAL · ph_suddha_sodhana SHORTFALL.

Flags raised during verify (agree, but noted):

1. **ga_condition** — verdict DELIVERS confirmed (ganita_condition_get serves 81KB) BUT
   DB `ga_condition_composite=45` rows for native, not the shard-reported
   '2880/2895/2880'. That figure is a facet/promise metric, not table rows — flag for
   reconciliation.
2. **ga_prashna** — DELIVERS is by-design-empty: DB `ga_prashna_judgment=0` and
   `prashna_undertaking_get` requires a `domain` arg (errors on chart-only natal call).
   Defensible, but effectively NOT_APPLICABLE-for-natal rather than a positive
   delivery — borderline call, still agree.
3. **mi_pramana** — SHORTFALL confirmed: DB `mimamsa_calibration=0` AND
   `mimamsa_reliability=0`; `mimamsa_calibration_get` returns 87K (shell over empty
   base).

## Headline

The dominant failure mode is the **retrieval-plane** (23 of 40 non-DELIVERS, plus most
of the 9 compound cases): assets that are correctly computed and stored in the DB but
have **no deployed MCP path** — or a fronting tool that returns empty despite thousands
of stored rows. Two CRITICALs (ka_vighnakara danger-windows and lel_events) and a long
tail of HIGH findings show the compute layer running well ahead of the serving layer:
the L3 Kāla temporal engines (avadhi, gochara, kala_darshana, sangam, taranga,
kalasutra, yojaka, vighnakara) are almost entirely dark over the wire, and several
semantically-named L4 fronts (mitigation_map, phala_rectification_get) advertise paths
that return nothing.
