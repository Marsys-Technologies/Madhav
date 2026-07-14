---
artifact: DOCTRINE_CAMPAIGN_EXECUTION_PLAN_v1_0
canonical_id: DOCTRINE_CAMPAIGN_EXECUTION_PLAN
type: EXECUTION PLAN (D-1 audit verdict + D-1.5→D-4 wave plan + §L capability injections)
version: 1.1
status: FINAL — Fable 5 authored (Claude Code, 2026-07-14); spec-review loop PASSED (2 iterations);
  DR-2 native-ratified with chalit-as-synthesis-data refinement; next step = dedicated D-1.5
  planning session (native directive) before any implementation
relationship: >
  Companion to DOCTRINE_CAMPAIGN_DESIGN_v1_0.md (the WHAT — components §3–§7, elevations §10–§13).
  This plan is the WHO/WHEN/GATE layer: it replaces the design's §8 phasing row for D-1 with the
  audited reality, defines D-1.5 (two gated sub-waves), injects the register §L capability-elevation
  rows into the waves, and sets the post-deploy MCP acceptance standard for every wave.
  POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md remains the living intake; §8 of this plan carries
  the register-status corrections this audit produced.
source_session: Claude Code Fable 5, 2026-07-14 — full D-1 spec-by-spec audit (3 parallel code
  audits at file:line granularity + live MCP probes of the deployed connector on chart 482012f1,
  build 9e7242f1, 17:46–17:47Z).
native_rulings_adopted:
  - DR-1 (native, 2026-07-14) — dual-lordship valence: TRIKOṆA PURIFIES (register §K.1).
  - DR-2 (native-RATIFIED 2026-07-14, refining the Fable 5 delegated ruling) — house-system
    doctrine: whole-sign is the computational primary for lordship/yoga/valence; bhāva-chalit
    (Sripati) is computed as a FULL SECOND DATA LAYER — first-class per-graha `house_chalit` facts,
    MSR-consumable, served alongside whole-sign on every relevant surface — and BOTH frames are
    consumed in astrological interpretation and synthesis (chalit is synthesis data, not merely a
    divergence flag). Divergence and sandhi proximity (≤3°) must additionally flag through to
    receipts and readings; judgment verdicts leaning on a divergent placement must disclose it;
    Placidus computed only as the quarantined replacement for the fake KP cusps. Past readings
    flagged, not retracted.
  - R-3 (Fable 5 by delegation) — bearing_yogas is FIRINGS-AUTHORITATIVE: ga_yoga_firings is the
    sole source of "formed"; MSR yoga signals demote to corroboration annotations.
  - R-4 (Fable 5 by delegation) — nakshatra/arudha/special-lagna semantic signal classes land in
    D-2 with the vidhi floors that consume them, not in D-1.5.
  - R-5 (Fable 5 by delegation) — DEFINITION OF DONE for every wave: merge → deploy → rebuild both
    charts → acceptance assertions executed against the DEPLOYED connector → close. (CR-96 terminal form.)
---

# Doctrine Campaign Execution Plan — D-1 Audit, D-1.5, and the Road to D-4

## §0 — Governing verdict of the D-1 audit

D-1 (merge `4bebb622`) shipped **more than the register's §J/§K credit it for**: the build layer is
~80% real. Five of six lanes landed genuine code with tests. What failed falls into exactly three
classes, and D-1.5 is organized around them:

1. **One inverted function** — `compute_valence` evaluates the dusthāna rule before the trikoṇa rule,
   contradicting its own declared precedence (CR-90), and never ingests raw aspects (CR-91).
2. **Unwired output** — the detector registry works and populates `ga_yoga_firings`, but neither
   `judgment_query` nor `ganita_yogas_get` reads it; the wealth verdict is byte-identical (1.15).
3. **Everything that was documentation, hygiene, or deploy-path** — §N.6 never ratified, structural
   serving face untouched, narrator/honesty fixes broken at the deployed surface, no SESSION_LOG
   close-out, no CR-87 two-chart guard test.

**Register staleness corrections (see §8):** CR-92 and CR-95 are partially stale as of tonight's
rebuild (build `9e7242f1`) — `ganita_yoga_firings_get` serves 13 fired yogas including both Dhana
Yogas, Rāja, Sarasvatī, Budha-Āditya, Śaśa, and per-varga NBRY with rule-level BPHS grounds;
`ganita_vichara_get` is live with 1,100 rows across all five families including leverage_index.

## §1 — D-1 spec-by-spec audit table (evidence at file:line; live probes 2026-07-14 ~17:47Z)

| # | D-1 spec item | Verdict | Key evidence |
|---|---|---|---|
| 1 | ga_vichara valence pass | **SHIPPED-BUT-INVERTED** | `compute_valence` branch order `ga_vichara_writer.py:287` (dusthāna) before `:292` (trikoṇa); `_PRECEDENCE` at `:83` consulted by `classify_actor` but ignored by `compute_valence`. Live: 9L Jupiter→H2 `malefic`; Mercury `trikona_link` `malefic` |
| 2 | Valence covers raw aspects | **NOT LANDED** | `VicharaFactIndex` ingests only `bhava_significance_link` (`:186-200`); no `aspect_parashari`. Live: Mars 8L→H2 `neutral`/`keyword_heuristic_v1` |
| 3 | Varga-ratification matrix + divergence signal class | **LANDED** | `build_varga_ratification_rows` (`:407-529`), §11 formula, D1 excluded as voter; divergence = first-class MSR class (prior 1.2). Live: 9 + 3 rows |
| 4 | leverage_index | **LANDED** | `build_leverage_index_rows` (`:653-753`); live 35 rows, full jsonb decomposition |
| 5 | dasha_lord_capability surface (CR-60) | **NOT LANDED** | exists only as runway multiplier inside leverage_index |
| 6 | Detector registry: 6 detectors + cancellation + per-varga NBRY + mig 434 | **LANDED** | `YOGA_DETECTORS` `ga_yoga_writer.py:2339-2382`; all cancellation callables non-None; NBRY D1+D9 (`:1779-1781`); writes `ga_yoga_firings` |
| 7 | Detectors → judgment_query.bearing_yogas | **NOT WIRED** | sourced from MSR catalog signals (`register_d9_judgment.ts:505-529`); live `bearing_yogas: []`, composite **1.15 unmoved** |
| 8 | Detectors → ganita_yogas_get | **NOT WIRED** | reads chart_facts categories only (`get_yoga_dosha.ts`), never `ga_yoga_firings` |
| 9 | Stale "will never fire" description | **DEFECTIVE** | verbatim at `register_p1_ganita.ts:633-637` |
| 10 | Yoga narrator (CR-33/93) | **SHIPPED-BUT-BROKEN AT SURFACE** | code computes PMP from positions (`:694-707`); live says "position was not available" and denies Śaśa while its row is in the page — position fetch fails on the deployed path |
| 11 | Honesty flags (CR-94) | **SHIPPED-BUT-BROKEN AT SURFACE** | code wires `coverage.served = rows.length` (`:759-763`); live serves `coverage.served: 0` + `zero_rows_returned` on a 32-row page |
| 12 | ganita_vichara_get / ganita_yoga_firings_get faces | **LANDED** | both registered (`register_p1_aliases.ts:488,:517`) and answering live |
| 13 | MSR elevation: class-priors, percentile tiers, subject headlines, position-subject resolution | **LANDED** | `_load_class_priors` queries `brahma_class_priors`; `_assign_tiers_by_percentile` (chart_defining ≥0.985, major ≥0.90); `_build_headline_text` subject-bearing; `_resolve_position_subject` for special_lagna/arudha/chara_karaka/KP. Live tier spread 88.1/10.1/1.5/0.4 |
| 14 | Nakshatra / arudha / special-lagna semantic classes | **NOT LANDED** | fall to `composite_state` default; no dedicated emitters |
| 15 | Dosha integrity (CR-72/73/74) | **PARTIAL** | kemadruma/daridra/kala_sarpa bespoke-computed with cancellation (`BESPOKE_DOSHA_DETECTORS`); remaining doshas catalog stubs, now gated `catalog_only`/`fires:null` but still paged by ganita_yogas_get with the shared constituent fact |
| 16 | §N.6 density ratified | **NOT LANDED** | no §N.6 in CLAUDE.md or ONGOING_HYGIENE; code cites a non-existent anchor. Envelope lib LANDED (`envelope.ts`); density contracts on 6 tools only; no CI harness |
| 17 | ganita_structural_get retrofit + CR-50 ordering | **NOT LANDED** | not in the D-1 diff; positions order alphabetically, upagrahas lead |
| 18 | CR-46 ph_nimitta dedup / CR-13 remaining budgets / CR-42 ref_remedies_search | **NOT LANDED / PARTIAL** | no dedup in ph_nimitta; bodha_domain_reading_get + ephemeris_cache_year unbudgeted, ganita_tajaka_get default limit 25000; ref_remedies_search forwards filters blind |
| 19 | CR-87 de-hardcoding | **CODE LANDED, UNVERIFIED** | constants removed, `NatalContext` per-chart required (`engine.py:271-279`); **no two-chart divergence test** (all fixtures use idx 24) |
| 20 | Governance close-out | **NOT DONE** | no SESSION_LOG Night-1 entry; migrations split across `platform/migrations/` (367/435/436) and `platform/supabase/migrations/` (434) — the collision class Lane 2 itself flagged |

**Live §K.2 gate status: 2 of 12 green, 1 half-green** — #10 ✓ (NBRY grounds via the firings face),
#12 ✓ (vichara face callable), #6 half-✓ (firings face non-empty, but `ganita_yogas_get.yoga_fires`
still 0). Red: #1–#4 (valence), #7–#9 (wiring/narrator), #11 (honesty/description). #5 (the
dual-lordship unit test) does not exist yet — red by absence. **Final proof red: wealth composite
1.15, byte-identical.**

## §2 — Rulings adopted

DR-2, R-3, R-4, R-5 as recorded in the frontmatter. R-3/R-4/R-5 were made by Fable 5 at the native's
explicit delegation ("recommend the answers on my behalf", 2026-07-14). **DR-2 was subsequently
RATIFIED by the native directly (2026-07-14), with one refinement: chalit is not merely a divergence
witness — it is a full second data layer, computed and served for synthesis, with both frames
consumed in astrological interpretation.** The DISAGREEMENT_REGISTER entry (A6) records this
provenance chain.

**Session protocol (native directive, 2026-07-14):** after this plan is finalized, a dedicated
PLANNING SESSION produces the D-1.5 implementation plan (lane briefs, task decomposition, updated
CLAUDECODE_BRIEF) BEFORE any implementation session begins. This document is the campaign design;
it is not an implementation license.

## §3 — D-1.5a: gate-green rework (blocks everything; smallest possible diff)

| ID | Work item | Root / fix | Acceptance (MCP, deployed, post-rebuild) |
|---|---|---|---|
| A1 | Valence precedence (CR-90, DR-1) | Reorder `compute_valence` (`ga_vichara_writer.py:269-322`) to honor `_PRECEDENCE:83`; unit test the `{trikona_lord, dusthana_lord}`→wealth cell | §K.2 #1, #2, #5 |
| A2 | One valence engine (CR-91) | Ingest `aspect_parashari` into `VicharaFactIndex`; dusthāna-lord aspects on wealth/lagna first; retire `keyword_heuristic_v1` for lord/aspect signals in `bo_laksana._resolve_valence`; reconcile stale "Lane 2 never landed" comments (`bo_laksana.py:863-872, 895-900, 960-965`) | §K.2 #3, #4 |
| A3 | Wire detectors to judgment (CR-92 residue) | `judgment_query.bearing_yogas` reads `ga_yoga_firings` (firings-authoritative per R-3; MSR demoted to corroboration); `ganita_yogas_get` serves/points to firings; **same commit** updates the stale description (`register_p1_ganita.ts:633-637`); verdict consumes detector strength + bhaṅga state. **A3 also owns §K.2 #10 and #12 as regression guards** — both are green today via the very faces A3 rewires; the gate re-verifies them post-change | §K.2 #6, #7, #8, #10, #11(desc), #12 |
| A4 | Narrator + honesty at the deployed surface (CR-93/94) | Root-cause the narrator's empty position fetch and the `coverage.served=0`/`zero_rows_returned` counter on the deployed path — these are deploy/wiring bugs, not missing code | §K.2 #9, #11 |
| A5 | CR-87 two-chart regression guard (W6) | Parametrized test: Abhinandan (1c826d5a) tara/sade-sati/panchanga currents ≠ Abhisek (482012f1); plus one live MCP comparison | assertion added to gate |
| A6 | Process close-out | SESSION_LOG Night-1 + D-1.5 entries; **DR-2 logged in DISAGREEMENT_REGISTER with delegation provenance for native ratification**; CURRENT_STATE §2 refreshed (stale M6 banner); migration-directory consolidation decision recorded; lane-brief template amended per CR-96/R-5 (acceptance = MCP assertions against the deployed connector, post-deploy) | artifacts exist |
| A7 | `_graha_aspects_house` off-by-one (Lane-1-flagged, pre-existing) | Opposition/7th-house aspects return 0.0 instead of 1.0 — a correctness bug in the aspect model that `effective_dignity` v2 and the A2 aspect-valence pass both consume; fix + regression test | unit + one live spot-check on a 7th-aspect fact |

**Gate A (12 assertions of register §K.2 + A5's two-chart assertion), run GREEN on the deployed
connector after deploy + rebuild of both charts. Final proof: the 482012f1 wealth verdict moves off
`convergent_moderate`/1.15 and `bearing_yogas` carries the Dhana Yoga. D-1.5b does not start until
Gate A is green.**

## §4 — D-1.5b: foundation capabilities (§L injections + cheap load-bearing leftovers)

| ID | Work item | Register row | Shape |
|---|---|---|---|
| B1 | **Bhāva-chalit + real cusps** — Sripati (+ Placidus, quarantined for future KP) via sidecar; new `house_chalit` + `sandhi_flag` fact categories; quarantine the fake 30°-interval "KP cusps"; per DR-2 (native-ratified) chalit is a FULL SECOND DATA LAYER: `house_chalit` served alongside whole-sign for every graha on positions/condition/judgment surfaces AND ingested into MSR as synthesis data (a chalit-frame context, consumed in interpretation) — with divergence + sandhi flags on top, never silently picking one frame. Type specimen: Moon 29°46′ Aquarius → 12th bhāva under Sripati (challenges the §G "2/11 axis" claim). Flag affected prior readings; do not retract | CR-98 (CORRECTNESS DEFECT) | L1 facts + MSR ingestion + serving disclosure |
| B2 | **Bhāva Bala** (six-source house strength; pyjhora provides) — the classical substrate for domain prioritization and leverage_index's house axis | CR-103 | L1 facts |
| B3 | **Aṣṭakavarga completion, facts half** — re-key bindus by SIGN (currently house-keyed: wrong key for transit use); trikoṇa/ekādhipatya śodhana; piṇḍas; kakṣyā boundaries. Transit gating itself is D-3 (B3 only makes it possible) | CR-99a | L1 facts (do NOT rebuild bindus — §L.3 baseline correction) |
| B4 | **Sudarśana Chakra** — tri-lagna concurrent judgment as pure L2 derivation over existing facts; corroboration rule: a result confirmed across Lagna+Chandra+Sūrya frames ranks up, one contradicted flags. Independently catches the B1 Moon problem | CR-100 | L2 derivation, no new L1 compute |
| B5 | **Bhavat Bhavam** — the 12-cell doctrinal map (odd houses only receive); GATED AMPLIFIER signal class (fires only when a pre-salient configuration occupies/rules a derived house — never a generator); shastra-map extension domain→{primary}∪{derived}; restraint rules served as first-class data; narrated in resolution_chains; feeds leverage_index | CR-97 | L2 signal class + registry data |
| B6 | Small L1 completions: karakamsha fact (CR-17); shadbala required-rupa ratios (CR-18); D2 hora-class per graha — surya/chandra hora + a D2 semantics note (CR-58); ph_nimitta anchor dedup (CR-46); positions default ordering — nine grahas + lagna lead, upagrahas behind a facet (CR-50); remaining oversize budgets — bodha_domain_reading_get, ephemeris_cache_year, ganita_tajaka_get default limit (CR-13/49); ref_remedies_search filter honor-or-reject (CR-42 residue); `ganita_structural_get` §N.6 retrofit (layered envelope + density contract on the biggest L1 face — design §10 serving half; the writer-side sub-builder split + effective_dignity fix already landed in Lane 1) | CR-17/18/58/46/50/13/42 + design §10 | small, parallelizable |
| B7 | **§N.6 ratification** — land the Serving Density Principle text in CLAUDE.md §N.6 + ONGOING_HYGIENE (the anchor the code already cites); density contracts estate-wide in the capability map; CI census/density harness | design §6 | governance + CI |
| B8 | dasha_lord_capability derived surface (CR-60) — minimal: per-MD row {lord, house class, shadbala percentile, functional lordship, varga ratification, warning tier}; full relational algebra stays D-3 PERMISSION lock | CR-60 | derived view |
| B9 | Dosha-label residue (CR-72/73/74) — serving half: `ganita_yogas_get` stops paging shared-stub `dosha_label` rows by default (catalog behind an explicit `all=true`, mirroring the firings face); the genuinely-computed per-varga kāla-sarpa verdict (natal + divisional map) gets a served surface. Bespoke detection for the remaining catalog doshas → D-2 | CR-72/73/74 residue | serving gate + one new facet |

**Gate B (all MCP, deployed, post-rebuild):** chalit facts served with divergence + sandhi flags on
482012f1 (Moon row flagged); Sudarshana tri-frame verdict served; BB amplifier emits only on
pre-salient configurations (Dhana-in-H9→derived-11th fires; no even-house emission); bhava_bala rows
served; SAV/BAV re-keyed by sign; positions lead with the nine grahas; budgets hold on the three
oversize tools; §N.6 anchor exists where code cites it; CI harness runs in the pipeline. **Per-item
B6/B8/B9 assertions:** karakamsha fact resolvable (CR-17); shadbala rows carry required_rupa + ratio
(CR-18); D2 dignity rows carry hora_class, and "both wealth lords in Chandra-hora H12" is servable in
one call (CR-58); `phala_anchors_get.anchor_count` is post-dedup (≤ distinct anchors; CR-46);
`ref_remedies_search(keyword=Saturn)` returns Saturn rows or rejects loudly (CR-42);
`ganita_structural_get` serves the layered envelope with a density contract; `dasha_lord_capability`
rows served for the Ketu-MD (warning tier present) and Venus-MD (weakest-graha join present) on
482012f1 (B8); `ganita_yogas_get` default page contains zero shared-stub `dosha_label` rows and the
per-varga kāla-sarpa verdict is servable (B9).

## §5 — D-2: Vidhi Engine + Mechanism wave

Design §3 (vidhi primitives, compiler, scope tuple, completeness receipt, MCP resource+prompt faces),
§6 (two-pass SCAN/FETCH, capability map with live source, alias dedup to ~30 canonical faces, errors
that teach, per-chart reading-notes as MCP resources), §12 (CGM elevation + first-class **Mechanism
object**; retires the CR-78 discovery engine; closes CR-84/85/86 dead links; chain/circuit signal
class CR-24/25). Register rows: CR-9, 14/39, 15, 16, 27, 28, 30/51, 36, 44, 62, 78, 84, 85, 86.

**Injections (this plan):**
- CR-101 Upapada doctrine wiring (rules in L0, A12 computed — connective tissue only).
- CR-104 Nārāyaṇa Daśā (Chara already live — §L.3; wire Chara as a timing witness per CR-77-amended).
- CR-105 pañcadhā-maitrī compound friendship matrix.
- **Semantic signal classes** (R-4): nakshatra-semantic (own-star, dispositor chains, tara bala,
  end-degree), arudha (AL/A2/A11 semantics), special-lagna (Indu/Sree/Ghati/Hora) — designed jointly
  with the vidhi floors that consume them (CR-64/61/76 residue).
- Kendrādhipati-doṣa + fuller per-lagna functional-benefic scheme (deferred out of D-1.5 by native
  ruling; revisit here).
- Bespoke detection for the remaining catalog doshas (B9 residue — CR-72/73 completion).

**Gate D-2 = the design-§8 master acceptance test:** a fresh LLM, given only served surfaces + the
compiled vidhi, reaches the six load-bearing wealth conclusions of register §G.0 on 482012f1 without
hand-derivation — each traceable to a served signal/verdict in the top-15 of its domain surface,
6/6 required — plus census battery green, alias count reduced to the declared canonical faces, and
the completeness receipt served on every synthesis. All assertions per §9 (deployed connector).

## §6 — D-3: Kāla Taraṅga + Three-Lock wave

Design §5 (stateless activation/curve service, staged kernel, LEL-retrodiction acceptance gates) +
§13 (Three-Lock PROMISE×PERMISSION×TRIGGER with signed suppression, double-transit, sahams,
period-lord algebra). Supersedes the temporal-blackout cluster: CR-1, 2, 3, 4/29, 5, 6, 12, 19/66,
37, 41(dissolved), 48, 63, 88, 89. **INFRA-PREREQ: CR-40/CR-8 sidecar auth restore — hard gate
condition before the transit kernel.**

**Injections:**
- CR-99b Aṣṭakavarga transit gating + **kakṣyā sub-windows** — sequence FIRST inside D-3: it needs no
  transit sidecar, so it partially routes around the CR-40 blackout while infra is repaired.
- CR-102 gochara vedha — correctness filter on every emitted window (vedha pairs already in
  bg_transit_rules; apply in ka_sangam/Taraṅga kernel).

## §7 — D-4: calibration ignition

Design §7 unchanged: LEL firewall re-scope (prediction-inputs only, not outcome-scoring);
retrodiction backfill (~40 scorable outcome records/chart); shared LEL↔candidate matcher fix (CR-47
root, reused by rectification); event-class-specific evidence sets (kills CR-79 degeneracy);
negative controls (shuffled-birth, antiphase); remedy-leverage join (CR-20/67); the
`mechanism_retrodiction` confirmation surface (CR-68).

## §8 — Register + design-§9 corrections carried by this audit

**Precedence rule:** where this plan and DOCTRINE_CAMPAIGN_DESIGN §9 disagree on a CR row's wave,
**this plan governs** (it post-dates the D-1 audit; design §9 remains authoritative for every row
this section does not amend). Disposition amendments made here:

- CR-26/64, CR-61, CR-76 (semantic signal classes): D-1 → **D-2** (ruling R-4; the subject-resolution
  half of the amended fix DID land in D-1 — only the dedicated classes move).
- CR-24/25 (chain/circuit class, CGM salience): D-1 → **D-2** (they require the §12 Mechanism object;
  the design's own §9 D-2 row already carried the CGM elevation these depend on).
- CR-87: D-3 → **D-1.5a A5** (verification half; the code half shipped in D-1 Lane 0).
- CR-60: D-1 → **D-1.5b B8** (minimal derived surface; relational algebra remains D-3).
- CR-72/73/74 residue: D-1 → **D-1.5b B9** (serving gate) + **D-2** (bespoke detection completion).
- CR-107 has no table row: the register's frontmatter/footer say "CR-1..CR-107" but the §L table
  ends at CR-106. Most plausibly the un-numbered §L.2 "retrogression doctrine" trap (already
  DEFERRED-EXPLICIT) was intended as CR-107. Correct in the register's next edit; nothing is
  operationally dropped either way.

**Status corrections:**

- **CR-92 → PARTIALLY STALE.** Detectors reachable via `ganita_yoga_firings_get` since tonight's
  rebuild; residue = judgment_query/ganita_yogas_get wiring (D-1.5a A3) + stale description.
- **CR-95 → STALE / CLOSED-BY-REBUILD** (verify on deployed connector at Gate A).
- **CR-93 / CR-94 → RE-SCOPED:** shipped-but-broken-at-surface (narrator position fetch; coverage
  counter) — deploy-path defects, not absent code (D-1.5a A4).
- **CR-53's CR-7 retest obligation** — fold into the Gate A battery.
- **CURRENT_STATE §2 is stale** (M6-era banner) — governance hygiene: update at D-1.5 close.
- Explicitly deferred, unchanged: CR-75 (KP engine — but B1 quarantines the fake cusps it would
  inherit), CR-106, retrogression doctrine, CR-23 (grounds-only stands), CR-52, population statistics.

## §9 — Standing process standard (R-5; CR-96 terminal form)

Every wave D-1.5a onward closes ONLY by: merge → deploy → rebuild both charts (482012f1 +
1c826d5a) → acceptance assertions executed as MCP calls against the DEPLOYED connector → SESSION_LOG
entry. A wave whose assertions cannot all go green reports the red list plainly and stays open. Lane
briefs state acceptance criteria exclusively as tool-call assertions; SQL/DB assertions are
diagnostics, never acceptance.

---

*Changelog: v1.1 (2026-07-14) — FINAL: spec-review loop passed (2 iterations, 9 issues fixed);
DR-2 native-ratified with refinement (chalit = full second data layer for synthesis, both frames
consumed in interpretation — B1 scope extended to MSR ingestion); session protocol recorded (§2):
dedicated planning session required before D-1.5 implementation. v1.0 (2026-07-14) — initial plan
from the Fable 5 D-1 deep audit (3 file:line code audits + live MCP probes on build 9e7242f1).
Defines D-1.5a/b with gates, injects register §L (CR-97..106) into the waves per the register's own
dispositions, adopts DR-2/R-3/R-4/R-5 by native delegation, and records register staleness
corrections.*
