---
wave: D-2
title: "Vidhi Engine + Mechanism — Wave Close Report"
status: CLOSED
lifecycle_step: 8
gate: PASS
closed_at: 2026-07-17
supersedes_state: STATE_D-2.md (rolling; this is the sealed record)
canonical_id: REPORT_D-2
---

# D-2 (Vidhi Engine + Mechanism) — Wave Close Report

## §1 — Executive summary

D-2 is **CLOSED, gate GREEN**. The wave's defining test — a fresh-context **floor-model Sonnet**
reading agent, given only served surfaces + the compiled vidhi (no priors, no register, no
hand-derivation), reaching all **6/6 §G.0 load-bearing wealth conclusions** — **passed single-pass**,
and was **independently confirmed by an adversarial Opus verifier against live payloads, by
observation not construction**.

The wave's chartered target was the CRITICAL valence-computation root cause (D-16 / CR-54 / CR-83,
adjudicated DR-9 / DIS.022): the instrument served an 8th-lord aspect on the 2nd house — the chart's
core wealth-destruction mechanism — as `valence: neutral, salience 0.575`, "ranked as noise." That
is fixed and gate-verified: the mechanism now surfaces in a signed, grounded, adverse/threat layer,
while the doctrine does **not** over-correct (anti-overcorrection specimens all hold).

## §2 — What shipped

**Cycle-1 (valence doctrine + mechanism)** — lanes V-0/V-1/V-4/V-5/V-6, merged PR #585, deployed,
Abhisek's chart rebuilt **61/61 (build `b84c3797`), FORENSIC 7/7**. Four rebuild hotfixes
(PRs #586/#588/#589/#590 — migration column-set, Narayana enum, Decimal serialization, tajaka
engine-resilience). The valence doctrine (`valence_doctrine.py`, `ga_vichara` valence_pass) shipped
Parts A (data) + B (partitioned adverse/supportive serve) — PRs #591/#592, DR-9 Parts A+B ratified.

**Cycle-2 (Vidhi Engine + two-pass channel)** — lanes V-2 (`plan_retrieval` meta-tool + `vidhi_plan`
prompt + registry resource + completeness receipts) and V-3 (`scan_fetch_signals` two-pass channel,
`reading_notes_get`, `canonical_faces.json`, CR-44 description-payload audit, CR-84 composite-ranker
graph-centrality leg, DR-8 deterministic `intent_classify`, CR-9 verified no-op). Merged PR #594
(`43210b21`), serving-only deploy, **live health `tools:120`**.

**Gate-phase fixes (this session, all serving-only, gate-driven):**
- **PR #596** — `nbry_scan` vidhi primitive routed to the firings-authoritative NBRY surface
  (`ganita_yoga_firings_get`) instead of the catalog face that doesn't evaluate it. This flipped
  **G0-3** from RED to GREEN. CR-59 register framing corrected: NBRY *detection* is live since
  D-1.6; the residual is L2 ranking/surfacing.
- **PR #597** — `judgment_query` v3 timing-hook trim (**73KB → ~23KB**: `timing_hooks.kala_activations`
  was 69% of the payload; per-row `activation_predicted_dates_jsonb` blobs dropped to a drill-pointer,
  deduped by window) so the load-bearing adverse layer (`affliction_mechanisms`) fits a floor-model
  budget; plus `wealth_loss_mechanism_scan` dead-class (`functional_lordship_link` = 0 rows) fix.
  This gave **G0-4** single-pass coverage.
- **PR (this close)** — corrected the stale `ganita_yogas_get` doc-string that claimed NBRY was
  "not evaluated on any live path" (a consumability trap that steered readers off the firings surface).

## §3 — Gate battery result (independently Opus-verified on live payloads)

| Leg | Verdict | Live evidence |
|---|---|---|
| **§G.1 master-acceptance 6/6** | ✅ **6/6 single-pass** | G0-1 `ganita_yoga_firings_get` dhana_yoga_2_5_9_11 (fired 1.02); G0-2 `ganita_vichara_get` varga_ratification_divergence SAT + judgment D2 varga_term=0; G0-3 NBRY `bhanga_active:true` w/ BPHS Ch.39 grounds (both Venus+Saturn D9); G0-4 `affliction_mechanisms` Rahu-on-2nd net −0.50 + `bearing_afflictions` grounded; G0-5 `leverage_index` VEN 3.94 (weakest 4.64 + 2L + 20yr MD); G0-6 `dasha_lord_capability` Ketu watch/0.625 |
| **§G.3 career probe** | ✅ PASS | Adverse-layer generalization: `varga_ratification_divergence:SAT:career=−1`, Saturn+Mercury `warning_tier:elevated`, `bearing_afflictions` salience 2.16, `afflictions_present:10` — surfaced alongside the supportive Śaśa structure |
| **G0-4 amended assertion** | ✅ PASS | Rahu-tenancy served in the THREAT layer, signed −0.50, `constituent_facts_array` resolves, `grounding.resolvable:true` (472 facts) |
| **Anti-overcorrection C1/C2/C3** | ✅ PASS | Rahu-H2 mixed −0.50 (NOT strong_malefic — node exaltation +0.50 offsets natural −1.0); Venus+Jupiter-H9 strong_benefic; valence_pass distribution 580 strong_malefic / 551 strong_benefic / 406 mixed / 58 malefic (real spread, no collapse) |
| **Census ≥ baseline** | ✅ 135 = baseline | Tool census 135 (asset census 97 is a distinct universe — not conflated) |
| **Gate-B (vichara + signals density)** | ✅ live | DEFECT-001 orphan 0%, signature_tier non-degenerate (84.6/12.4/2.4/0.7); layered vichara envelope, 5 families |
| **Gate-Ś honesty + #8 residual** | ✅ / deferred | B.10 honest floors present (nbry_rule_5 floored, no verifiable citation); **Gate Ś #8** (`yoga_activation_by_dasha` undated activations) remains the sole dispositioned residual — same pattern, now 15/15 undated (rebuild widened the yoga set), NOT a new failure |

**Not re-verified this session (no contradicting evidence):** FORENSIC 7/7 was confirmed at the
cycle-1 rebuild (`b84c3797`) but not re-run at gate; the full 135-tool sweep and a standalone Gate-A
table were not isolated (the brief bundles Gate-A into "Gate-A/B/Ś regression green").

## §4 — Baseline wealth re-run diff (pre-D-2 → post-D-2)

Per `BASELINE_WEALTH_READING_PRE_D2_v1_0.md §4` comparison protocol, the verbatim question
— *"Full financial analysis of 482012f1: when does the wealth promise activate, and what intervention
secures or advances it?"* — re-run post-D-2 (the §G.1 floor-model reading answers it). Diff on the
7 recorded dimensions:

| # | Dimension | Pre-D-2 (baseline) | Post-D-2 | Delta |
|---|---|---|---|---|
| 1 | Served vs hand-assembled activation dates | Venus-MD 2034 activation assembled BY THE READER from the dasha table | Dasha spine + `dasha_lord_capability` per-lord warning tiers served; forward *dated* window still assembled | **PARTIAL** (capability served; dated forward window → D-3 Taraṅga) |
| 2 | Venus-MD forward window w/ NBRY-deferral sub-timing | absent | NBRY now served (`bhanga_active` + grounds); forward Venus-MD dated sub-timing not yet served | **PARTIAL** → D-3 |
| 3 | Mechanism-named evidence | 2/11 axis narrated, not served as a named valenced mechanism | **`affliction_mechanisms`: "Rahu occupies dhana (2nd) bhāva (mixed)" served, signed −0.50, grounded** | **CLOSED** ✓ (V-4/DR-9) |
| 4 | Receipt completeness | no completeness receipt on the reading plan | **Completeness receipt served** `{bhava,bhavesha,karaka,from_moon,varga_confirmed:D2✓,yogas_checked:12,bhanga_checked,timing_anchored}` | **CLOSED** ✓ (V-2 vidhi receipt) |
| 5 | Suppression-adjusted windows / gochara vedha | additive-only | still additive-only | **OPEN** → D-3 T-5 |
| 6 | Retrodictive confirmation section | 2010-07 windfall / 2025-05 loss unscored; `lel_query(finance)` = 0 | still unserved (LEL walled from mechanism-confirmation) | **OPEN** → D-3 gate / D-4 |
| 7 | Remedy `leverage_index` join ("Venus, now, before 2034") | hand-assembled | **the reading itself derives it**: `leverage_index` ranks Venus highest (3.94) = weakest-graha × 2L × 20yr-MD → "the Venus remedy is the one most directly aimed at strengthening the highest-leverage-lowest-capability graha" | **CLOSED** ✓ (CR-69 leverage_index) |

**Headline:** the two things the baseline question most needed and could not get — a **named, valenced
mechanism** (the promise's threat layer) and a **completeness receipt** (what was covered vs
hand-assembled) — are both now **served**, and the system **itself derives the remedy-leverage
conclusion** rather than leaving it to the reader. The reading now serves the promise AND the threat
layer, partitioned (DR-9 Part B). Forward *dated* windows, suppression models, and retrodictive
calibration remain honestly D-3/D-4 scope.

## §5 — §F1.7 promise-ledger close

Every §F1.7 promise (BIND_D-2) is marked below (KEPT / BROKEN-with-evidence / DEFERRED-WITH-POINTER).
"Broken with evidence + a register row" is an acceptable close state; Gate Ś #8 is deferred-with-pointer.

**Tally: 52 KEPT · 1 BROKEN-with-evidence · 3 DEFERRED-WITH-POINTER · 0 unmarked.**

| # | lane | promise (short) | verdict | evidence |
|---|---|---|---|---|
| 1 | V-0 | 6 §G.0 wealth conclusions as executable presence checks | KEPT | §G.1 6/6 single-pass, Opus-verified live |
| 2 | V-0 | Full census sweep (135 tools) vs baseline | KEPT | census 135=baseline confirmed at gate |
| 3 | V-0 | Completeness-receipt validator (wealth + career) | KEPT | receipts present at §G.1/§G.3 |
| 4 | V-0 | Alias-count check vs V-3 canonical-face list | KEPT | alias_check→v3_canonical_face_list 4/4 (caveat: canonical_faces missing 3 cycle-2 tools → row 22 / D-3) |
| 5 | V-0 | Proactive pacing ≤17-call batches, no false 429 reds | KEPT | gate run in ≤13-call batches, no 429s |
| 6 | V-0 | Extends doctrine_harness/density_harness, never duplicates | KEPT | V-0 scope_warden pass, 33/33 tests |
| 7 | V-1 | ~30 primitives as versioned registry rows | KEPT | V-1 ACCEPT, 24/24 tests, migrations 440-444 |
| 8 | V-1 | Per-intent-class floors + machine bands | KEPT | V-1 ACCEPT |
| 9 | V-1 | Deterministic compiler: identical tuple → identical contract | KEPT | V-1 ACCEPT, hash-equality tests |
| 10 | V-1 | track3/ source drafts committed | KEPT | V-1 ACCEPT (Track-3 absorbed) |
| 11 | V-1 | CR-27 corpus mapped | KEPT | V-1 ACCEPT |
| 12 | V-1 | §B0.4 mandatory floor content (11 items) | KEPT | V-1 ACCEPT |
| 13 | V-1 | bg_vidhi* writer(s) + asset_registry, correct count_sql | KEPT | migration 440 (hotfix #586) + rebuild 61/61 |
| 14 | V-2 | Vidhi registry as MCP resource | KEPT | V-2 receipt (33b15f5f, PR #594) |
| 15 | V-2 | Compiled plans as MCP prompt + plan_retrieval fallback | KEPT | V-2 receipt |
| 16 | V-2 | Scope tuple echoed for correction | KEPT | DR-8 scope_tuple; V-2 rows 14-19 |
| 17 | V-2 | Completeness receipt on EVERY synthesis | KEPT | validated live §G.1/§G.3 |
| 18 | V-2 | capability_version + tools/list_changed staleness kill | KEPT | V-2 receipt |
| 19 | V-2 | amjis-mcp SHA advances after cycle-2 deploy | KEPT | mcp_image 43210b21@sha256:39ecdd1b off pin 08245669 |
| 20 | V-3 | Pass-1 SCAN + Pass-2 FETCH-by-id | KEPT | V-3 receipt (20e2da8e): scan_fetch_signals |
| 21 | V-3 | Capability map live source / CR-9 | KEPT | CR-9 verified no-op (401 non-repro) |
| 22 | V-3 | Canonical-face list authored, twins removed | KEPT (gap→D-3) | canonical_faces.json 92/43 live; missing 3 cycle-2 tools (register pointer) |
| 23 | V-3 | CR-44 description-vs-payload CI audit | KEPT | V-3 receipt |
| 24 | V-3 | Errors-that-teach | KEPT | V-3 receipt, 67 tests |
| 25 | V-3 | Per-chart reading-notes (CR-38/71/80) | KEPT | reading_notes_get delivered |
| 26 | V-3 | Chart-keyed special-lagna access (CR-16) | KEPT | V-3 ACCEPT |
| 27 | V-3 | Pact MD-lord naming (CR-15) | KEPT | V-3 ACCEPT |
| 28 | V-3 | Holistic bundle repair, non-ok on sub-errors (CR-14/39) | KEPT | V-3 ACCEPT |
| 29 | V-3 | intent_classify wired per CR-28/DR-8 | KEPT | DR-8 deterministic scope_tuple |
| 30 | V-4 | Mechanism = named valenced CGM subgraph + serving face | KEPT | V-4 (1be1639e) ACCEPT, 3521 tests, 7 judgment calls GREEN |
| 31 | V-4 | Real edge-strength formula; CR-86 literals retired | KEPT | DR-7 exact |
| 32 | V-4 | 10→8→12→10 chain/circuit motif served (CR-24) | **BROKEN** | CR-24 live-confirmed **negative** — motif absent on the live chart; honestly reported per the promise's own honesty clause (not papered over) |
| 33 | V-4 | Completed centralities (eigenvector/betweenness/harmonic) | KEPT | V-4 ACCEPT full scope |
| 34 | V-4 | CGM salience joins composite ranking (CR-25) | KEPT | V-4 data-layer + V-3 CR-84 serving leg |
| 35 | V-4 | CR-84 post-CGM re-rank closes MSR structural_role | KEPT | V-4 data + V-3 CR-84 leg |
| 36 | V-4 | CR-85 ka_yojaka centrality-consumption stub removed | KEPT | V-4 ACCEPT; migrations 445-449; rebuild 61/61 |
| 37 | V-4 | bo_anveshana retired (CR-78) | DEFERRED-WITH-POINTER | CR-78 PARK genuine (fallback clause); pointer = MARSYS_DEFECT_GAP_REGISTER CR-78 |
| 38 | V-4 | CR-62 multi-varga map (D10 career lens) | KEPT | V-4 ACCEPT |
| 39 | V-4 | PARK-#4: 5 residual keyword rows re-emitted/proven | KEPT | honest scope: live keyword_heuristic_v1 = 43,408/49,360 chart-wide |
| 40 | V-4 | F2: bo_laksana count_sql tightened | KEPT | V-4 ACCEPT; migrations 445-449 |
| 41 | V-5 | Four new emitter modules | KEPT | V-5 (13cc4349) ACCEPT, 3520 tests, live specimen (Mercury sole D9-vargottama) |
| 42 | V-5 | Append-only class registry; siblings unchanged | KEPT | cross-writer delete-scope proven disjoint |
| 43 | V-5 | Class priors per DR-6 | KEPT | DR-6 exact match |
| 44 | V-5 | Gate Ś #8 disposition per §B.8 | DEFERRED-WITH-POINTER | legitimately deferred (fix outside glob); §B.8 fallback |
| 45 | V-6 | Upapada wiring (CR-101) | KEPT | V-6 (3c0c49ed) ACCEPT, 3479 count reconfirmed |
| 46 | V-6 | Nārāyaṇa Daśā (CR-104) | KEPT | hotfix #588 enum fix; rebuild 61/61, FORENSIC 7/7 |
| 47 | V-6 | Pañcadhā-maitrī compound matrix (CR-105) | KEPT | V-6 ACCEPT |
| 48 | V-6 | Chara Daśā timing witness (CR-77) | KEPT | V-6 ACCEPT; live-verified |
| 49 | V-6 | Kendrādhipati-doṣa + functional-benefic completion | DEFERRED-WITH-POINTER | held at PROPOSED status pending DR-n ratification (safe-by-design); verified correct vs production |
| 50 | V-6 | CR-73: every dosha w/ bhaṅga check or catalog-gated | KEPT | §B.1 check 2 PASS; B9 gate excludes catalog-only |
| 51 | all | Three verification altitudes per cycle | KEPT | Phase-1 receipts + INTEGRATE cross-lane + live re-runs |
| 52 | all | Scale realism + data-over-flags | KEPT | every lane cites a live-data probe |
| 53 | all | Truncation honesty: no absence claim from a trimmed page | KEPT | PR #597 trim; residual v3 >12KB is size-debt not honesty-violation |
| 54 | gate | §G.1 master acceptance 6/6 | KEPT | 6/6 single-pass, Opus-verified live |
| 55 | gate | §G.2 census + alias + receipt + Gate-A/B/Ś regression | KEPT | census 135; Gate-B/Ś live; PRs #596 + doc-fix closed gate-found defects |
| 56 | gate | §G.3 career second-domain probe | KEPT | career PASS (adverse-layer generalization) |

*Row 32 (BROKEN)* is honest: the CR-24 chain/circuit motif does not exist on this native's chart —
V-4 confirmed it a true-negative and reported it rather than fabricate a firing. *Rows 37/44/49*
are deferred-with-pointer per their own fallback clauses (CR-78 PARK, Gate Ś #8 §B.8, kendrādhipati
PROPOSED-pending-DR). No promise is unmarked.

## §6 — Honest findings carried to D-3 (register rows, not gate-blockers)

The gate's adversarial Opus pass surfaced consumability findings — all "reachable but only if you
query the right face," none data gaps. Per native disposition (2026-07-17): the cheap doc-string trap
was fixed in-wave; the rest are D-3 candidates:

1. **`leverage_index` `subject=venus` false-empty** — the code is `VEN`; a floor model using the
   natural-language planet name gets 0 rows behind an ambiguous `empty_reason`. → D-3: alias the
   subject param or sharpen `empty_reason`.
2. **C1 nodal-exaltation offset surface asymmetry** — the Rahu-H2 net −0.50 lives on
   `judgment_query.affliction_mechanisms`, not on the raw `valence_pass` Rahu rows (which read
   strong_malefic for Rahu's *aspects*). → D-3: serve the tenancy-valence on the granular surface.
3. **`canonical_faces.json` missing the 3 cycle-2 tools** — census 138 live vs 135 listed;
   alias-check reports 3 `unaccounted_tools`. → D-3: add plan_retrieval / scan_fetch_signals /
   reading_notes_get to the canonical list.
4. **`judgment_query` v3 oversize baseline** — trimmed 73KB→23KB (consumable), still self-flags
   `response_still_over_12kb_budget_after_full_trim`. → D-3: further §N.6 budget work (S-5 class).

## §7 — Doctrine rulings recorded this wave

- **DR-6 (DIS.019)** — V-5 signal-class priors (nakshatra_semantic 1.00, arudha 1.10, special_lagna
  0.90, vargottama 1.15, dhana_axis 1.05).
- **DR-7 (DIS.020)** — V-4 edge-strength formula (`edge_strength = base × valence × ratification ×
  consistency`, clamp[0.1,2.0]).
- **DR-8 (DIS.021)** — CR-28 `intent_classify` redesigned to a deterministic scope-tuple classifier.
- **DR-9 (DIS.022)** — valence-computation doctrine Parts A (data) + B (partitioned adverse/supportive
  serve). The wave's central ruling; VAL-ROOT closed.

## §8 — Close + next

D-2 build arc complete: all cycle-1 + cycle-2 lanes integrated, deployed, live-verified; gate 6/6
passed and independently verified; valence-computation root cause (VAL-ROOT / D-16 / CR-54) closed;
the reading now serves promise + threat + receipt + derived remedy-leverage.

`current_wave` advances to **D-3**. D-3's binder inherits the §6 findings as opening candidates
(Taraṅga forward-dated windows, suppression/gochara-vedha, retrodictive confirmation, and the four
consumability/register items above).

*Sealed record. STATE_D-2.md remains the rolling working file; this is the authoritative close.*
