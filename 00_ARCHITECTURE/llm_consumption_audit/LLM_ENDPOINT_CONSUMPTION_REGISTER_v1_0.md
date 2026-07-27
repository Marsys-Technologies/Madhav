---
canonical_id: LLM_ENDPOINT_CONSUMPTION_REGISTER
version: 1.0
status: ADDRESSED-v1
opened: 2026-07-27
closed: 2026-07-27
owner: LLM consuming endpoint (Claude, via marsys-jis-direct MCP)
scope: First-hand deficiencies, errors, gaps, and inefficiencies observed while consuming the MARSYS-JIS portal through the MCP during a live chart deep-read + consultation session for the canonical native (Abhisek Mohanty, chart_id 482012f1-710e-4a25-994a-93821f5871aa).
purpose: >
  A running, elaborated register of everything that went wrong, could have gone
  better, or added friction from the perspective of the LLM endpoint that
  actually receives portal data over MCP. This is the view the portal cannot
  see from the inside. Each item is written to be directly actionable by a
  remediation session. Maintained live across the originating conversation.
related:
  - LLM_CONSUMPTION_AUDIT_v1_0.md
  - POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md
  - REMEDIATION_PLAN_v3_0.md
changelog:
  - v1.0 (2026-07-27): Register opened mid-session. Seeded with items MC-001..MC-020
    plus preserve-list and session context, from the first ~15 tool-call deep-read
    (server_info → snapshot → ganita facts/positions/strength/nakshatra → bodha
    digest/discoveries/quality → yogas/firings → dashas → kala life-arc → sade sati
    → phala outlook → assess_career/marriage/wealth → dossier career/wealth →
    bodha_bundle → D9/D10 verification snapshot) and the Mars-debilitation
    correction exchange.
  - ADDRESSED-v1 (2026-07-27): ŚODHANA remediation campaign closed. Per-item disposition
    table in SHODHANA_REPORT_v1_0.md §2/§5 (this same briefs/shodhana/ directory) — 27
    VERIFIED-FIXED, 3 VERIFIED-NO-DEFECT, 9 PARKED-HONEST (evidence + release conditions
    attached), 2 FAILED-REOPENED (MC-015, MC-029 — narrow, specified fixes, see report §5).
    This changelog entry is append-only; no MC item's original text below was altered.
---

# LLM Endpoint Consumption Register — MARSYS-JIS via MCP

**How to read this.** Each item is one observed deficiency/friction, written from the
consuming endpoint's seat. Fields: *What happened · Where (tool/evidence) · Consumer
impact · Recommendation · Severity*. Severity = **HIGH** (blocks or corrupts a reading),
**MED** (degrades quality or forces costly workarounds), **LOW** (papercut / polish).
This register is deliberately blunt: its value is honesty about where the instrument
made correct, deep consumption harder than it needed to be.

**Standing note on my own errors.** Some items below (§E) are *my* endpoint mistakes,
not portal defects. They are logged anyway, because in each case a portal-side schema or
label change would have made the mistake much harder to commit. The point is systemic
prevention, not blame-shifting.

---

## A. Correctness / data-integrity risks

### MC-001 — DEFECT-001: Bodha→L1 fact_id back-references 82.9% orphaned  · Severity: HIGH
- **What happened.** The L2 Bodha synthesis layer stores, on every signal, a
  `constituent_facts_array` of L1 `chart_facts.fact_id` pointers (the B.3 derivation
  ledger / §N.5 "L1 is authority" mechanism). Live resolution against the *current*
  `chart_facts` shows **59,233 / 71,430 references orphaned (82.9%)** — the L1 layer was
  rebuilt with new SHA-based fact_ids after Bodha was last built, so most back-pointers
  no longer resolve.
- **Where.** `bodha_quality_get` → `defect_001` + `defect_001_alert` (severity HIGH,
  derived live as_of 2026-07-26). The stored scorecard field
  `unresolved_constituent_facts_count: 0` **contradicts** the live 82.9% — a
  registry-disagreement (GA.1-class) that would mislead anyone trusting the stored field.
- **Consumer impact.** As the endpoint I could still *use* Bodha's signal content
  (salience ranks, entity dominance, discoveries), but I could **not** trace any Bodha
  claim back to its exact L1 source row — which is the entire promise of B.3/§N.5. It
  forced me to caveat every Bodha-derived statement and to re-ground the structural spine
  on L1/L3/L4 tools instead. A stricter consumer would have to treat the whole Bodha layer
  as unverifiable-by-provenance.
- **Recommendation.** (a) Auto-rebuild (or re-link) Bodha on any L1 hash change; (b) stamp
  every Bodha-derived tool response with a `bodha_l1_linkage_fresh: bool` + build-id pair,
  not just `bodha_quality_get`; (c) fix the stored `unresolved_constituent_facts_count` so
  it cannot disagree with the live value (or delete the stored field and always derive live).

### MC-002 — `bodha_bundle_get` silently degraded: 5/8 sub-tools errored under `ok:true` · Severity: HIGH
- **What happened.** The flagship "holistic_bundle" aggregation returned
  `type: bundle.completed`, `ok: true` — but `provenance.sub_tools_errored` listed
  **MSR, CGM, LEL, PANCHANG, DASHA** (5 of 8), and the two served entries (MSR, CGM) each
  carried `errored: true, error_class: tool_error`. Only UCN/RM/CDLM fired. Called for both
  `wealth` and `career`; identical failure.
- **Where.** `bodha_bundle_get` (domain=wealth, domain=career).
- **Consumer impact.** The tool that is *supposed* to be the one-shot holistic surface
  returned almost nothing usable, while presenting as successful (`ok:true`). An endpoint
  that trusted the envelope status would silently compose a reading on a near-empty bundle.
  I only caught it by reading `sub_tools_errored`.
- **Recommendation.** Bundle envelope must expose a top-level `status: degraded|partial|ok`
  and a `sub_tools_errored` count at the top, so `ok:true` is never returned when the
  majority of constituents failed. Root-cause the MSR/CGM errors (likely the MC-001
  stale-linkage issue surfacing as a hard error inside the bundle path).

### MC-003 — Served provenance cites a deleted artifact (FORENSIC v8.0) · Severity: MED
- **What happened.** `phala_outlook_get` provenance gives
  `l1_ground_truth: "FORENSIC v8.0 §5.1 DSH.V.023–028; CHART_FACTS_EXTRACTION_v1_0.yaml"`.
  Per CLAUDE.md §B, the FORENSIC v8.0 markdown was **deleted in PR #187 (Legacy Teardown)**;
  the live source is the `chart_facts` table.
- **Where.** `phala_outlook_get` → `provenance_envelope.layer_provenances.PH-4-1.l1_ground_truth`.
- **Consumer impact.** A consumer auditing the citation would chase a retired file. It also
  undercuts trust in other provenance strings.
- **Recommendation.** Sweep served provenance strings for references to deleted/superseded
  artifacts; repoint to `chart_facts` / current canonical sources.

---

## B. Envelope size / budget / trimming

### MC-004 — Core tools overflow the MCP token cap and spill to disk · Severity: HIGH
- **What happened.** Multiple primary tools exceeded the MCP response limit and were
  written to `tool-results/*.txt` files instead of returned inline:
  `ganita_chart_facts_get` (~80KB), `assess_career` (~155KB), `assess_marriage` (~138KB),
  `assess_wealth` (~126KB).
- **Consumer impact.** **This is the single biggest accessibility blocker.** An endpoint
  without out-of-band file access (a plain chat client, or a hosted agent without a shell)
  simply *cannot consume these tools at all* — the reading is unreachable. Even with a shell,
  it forced me into multi-step `jq` extraction, burning turns and risking partial reads.
- **Recommendation.** The `assess_*` family and `ganita_chart_facts_get` need a
  server-enforced default that fits the MCP envelope: a `verbosity: summary|full` param, or a
  "reading projection" that returns interpretive prose + verdicts + top-N grounded signals
  only, with the full fact/signal dump behind an explicit opt-in.

### MC-005 — Budget trimmer sacrifices the interpretive prose, keeps the low-value arrays · Severity: HIGH
- **What happened.** Inside `assess_career/marriage/wealth`, the verdict `clauses[].text`
  — the actual human-readable reading — was truncated **mid-sentence**
  ("…cross-referenced against classi…[truncated for budget]") while multi-item `fact_ids`
  arrays under the same clause were retained in full.
- **Where.** `assess_*` → `content.verdict.clauses[]`.
- **Consumer impact.** After paying 150KB, the one thing a reader needs — the sentence — was
  the thing cut. This **inverts the project's own Serving Density Principle (§N.6):** the
  densest, most-actionable layer (the verdict prose) should be the last thing trimmed, not the
  first. The fact_id arrays (low information/byte) survived; the prose (high information/byte)
  did not.
- **Recommendation.** Mark verdict/reading prose `hardFloor: true` (the mechanism from
  `response_budget.ts` §N.6 Part 2) so it survives trimming; trim `fact_ids` arrays and
  supporting signal lists first.

### MC-006 — `assess_marriage`: budget exceeded even after full trim · Severity: HIGH
- **What happened.** `judgment_flags: [{code: "budget_exceeded_after_trim", detail: "40kb
  budget still exceeded after full trim."}]`. The marriage assessment could not be made to
  fit even after trimming everything.
- **Consumer impact.** The marriage domain reading is effectively un-servable within budget —
  a whole life-domain the instrument cannot deliver to the endpoint in one call.
- **Recommendation.** Same as MC-004 (summary projection). A domain assessment must have a
  guaranteed-fits minimal form.

### MC-007 — 155KB returned for a reading whose sections are almost all empty · Severity: MED
- **What happened.** `assess_career`'s `reading[]` had **13/13** sections in
  `empty_for_this_chart` or `not_computed_at_l1` state (D10, D9, karakāṃśa, net argala,
  special lagnas, L2 mechanisms, remedies, contradictions, cross-ayanāṃśa, dasha windows),
  yet the call still weighed 155KB (mostly `house_analysis.question_lenses[].
  all_relevant_ranked_jsonb` signal dumps and `signal_ids` lists in the thousands).
- **Consumer impact.** Maximum byte cost, near-zero interpretive yield. The expensive part
  (thousands of signal_ids) was served; the useful part (populated reading blocks) did not
  exist.
- **Recommendation.** When the curated reading is empty, return the emptiness compactly with
  reasons; do not also ship the raw signal-id firehose by default.

---

## C. Data-materialization gaps (canonical native's own chart)

### MC-008 — Domain varga-consumption blocks not materialized (D10 career; D2/D11 wealth) · Severity: HIGH
- **What happened.** `assess_career` reports **D10 "not_computed_at_l1"**; `assess_wealth`
  reports **D2 (Horā) and D11 "not_computed_at_l1"**; also empty: net argala on houses
  2/10/11, per-varga aṣṭakavarga, special lagnas, Indu lagna, karakāṃśa. **Yet the raw
  divisional positions exist** — I pulled D9 and D10 cleanly from `chart_snapshot`
  (`chart_divisionals`, 21,635 rows per L1 closure).
- **Consumer impact.** The *fine-grained, varga-level* domain reading — the acharya-grade
  differentiator, and the natural home for D10 career / D2 wealth judgment — is unavailable for
  the **canonical native's own chart.** The assessors fall back to D1. So the deepest layer the
  instrument advertises is exactly the layer that returned empty.
- **Recommendation.** Either (a) materialize the domain varga-analysis products (D9/D10/D2/D11
  consumption blocks, net-argala, per-varga AV) for the canonical chart, or (b) have the
  assessor compute them live from `chart_divisionals` on demand rather than depending on a
  pre-materialized block that may be absent.

### MC-009 — L2 mechanism layer empty / not-computed for this chart · Severity: MED
- **What happened.** `bodha_mechanisms` rows empty; dossier marks
  `dispositor_cycle, house_lordship_cycle, mutual_reception, parivartana_chain, stellium,
  yoga_cluster` as **"not_computed_globally."** Only convergent_dispositor_chain /
  graha_bhava_affliction / mutual_aspect(_triangle) served.
- **Consumer impact.** The cross-signal *mechanism* layer — central to a B.11 whole-chart read
  — returns almost nothing, so linkage/mechanism reasoning (how configurations chain) is
  unavailable. A consumer can't tell whether an empty is a true negative or a build gap; the
  dossier's "not_computed_globally" implies the latter for 6 of the classes.
- **Recommendation.** Compute the missing mechanism classes, or explicitly distinguish
  `true_negative` from `not_computed` in the served state so the endpoint isn't guessing.

### MC-010 — L5 STRUCTURAL-mode verdicts read as substantive denials · Severity: MED
- **What happened.** `synth_chart_brief_get` returns verdicts like **"Marriage: denied (grade
  1.6/10)"**, "Major Financial Gain: denied", "Childbirth: denied (grade 5.0, n_support=0)" —
  but L5 is sealed in **STRUCTURAL** mode: these are unpopulated structural priors with
  **zero backing evidence rows**, not findings. The envelope *does* disclose this
  (`verdict_quality_flags`, `n_support=0`, `[UNVERIFIED]`), but the headline verb is "denied."
- **Consumer impact.** Very high misread risk. An LLM or human skimming "Marriage: denied,
  Childbirth: denied, Major Financial Loss: denied" will read categorical negative predictions
  where the instrument means "not yet assessed." I had to actively suppress this in my reading;
  a less careful endpoint would broadcast alarming false negatives.
- **Recommendation.** For `n_support=0` structural priors, do **not** use "denied" language.
  Relabel to "not_yet_assessed (structural prior only)" and reserve "denied" for empirically
  grounded negative knowledge. This is a safety/harm issue given the domains (marriage, health,
  childbirth, financial loss).

---

## D. Ergonomics / interface friction

### MC-011 — `dossier` required-arg error only surfaces on call · Severity: LOW
- **What happened.** First `dossier` call failed with a zod error: `domain` required
  (received undefined). No default; not obvious from the tool surface.
- **Recommendation.** Advertise `domain` as required + provide an enum in the tool description.

### MC-012 — `dossier` synthesis-gate forces paging ~88KB of catalog strings to "unlock" · Severity: MED
- **What happened.** `dossier` returns a `synthesis_gate: BLOCKED` "reading_contract" that says
  *"Do NOT compose yet"* at **3.2% coverage**, and to reach OPEN you must page all 4 pages ×
  each domain. But each ~22KB page is dominated by a flat catalog of `signal_type_id` strings
  (hundreds of `argala_natal_matrix:from_sign_N_offset_M`, `aspect_parashari_per_varga:*`) —
  concept-inventory scaffolding, **not** chart-specific values (the real rows are "hydrated"
  via other tools, and auto-hydration is not wired — see MC-013).
- **Consumer impact.** To lift the gate on 2 domains I'd ingest ~8 page-loads / ~88KB of
  low-information catalog names for near-zero interpretive content. The completeness-accounting
  is intellectually honest but the cost/benefit for a *reading* consumer is very poor; I
  deliberately declined to page it and sourced interpretation from the underlying tools instead.
- **Recommendation.** Separate the *completeness receipt* (a coverage count + gate boolean)
  from the *concept-catalog dump*. Offer a compact "gate-satisfied summary" so the endpoint can
  legitimately compose without ingesting the full TCI. If composition really requires the
  catalog, hydrate it server-side rather than shipping raw type-id lists to the endpoint.

### MC-013 — `dossier` serves drill-handles it can't resolve; receipts don't persist ("blocked-on-α") · Severity: MED
- **What happened.** `dossier.density_note`: *"Auto-hydration over HTTP needs the
  tool-name→capability-URI resolver (cross-lane, blocked-on-α)"*; `retrieval_receipts.
  persistence: "in_response_only"` with the same α blocker.
- **Consumer impact.** The dossier tells the endpoint *which* tool to call for each concept but
  cannot call it, and its completeness receipts evaporate after the response. So it's a
  partially-wired scaffold: honest accounting, but the endpoint must manually fan out, and
  nothing accumulates.
- **Recommendation.** Finish the α wiring (resolver + receipts writer) or clearly mark `dossier`
  as preview/experimental so a consumer doesn't build a workflow on transient receipts.

### MC-014 — Raw fact tools return large counterfactual arrays; weak default filtering · Severity: MED
- **What happened.** `ganita_strength_get` returned **520 rows** (trimmed to 65) including
  `graha_in_house_composite_strength` for **every planet × every one of 12 houses** (i.e.,
  counterfactual placements), when only the actual placement is usually wanted.
  `ganita_sade_sati_get` returned **1,259 rows** (trimmed to 78) of raw period boundaries
  spanning **1950–2100**, mostly irrelevant to "where is Sade Sati now."
  `ganita_dashas_get` 89→44.
- **Consumer impact.** High byte cost, low precision; I had to mentally filter hundreds of rows
  to extract a handful of facts (e.g., "current Saturn dignity", "which Sade Sati phase now").
- **Recommendation.** Smarter defaults: actual-placement-only for strength; a `current`/date-
  window default for sade_sati; a "just the active dasha chain" convenience shape. Keep the
  firehose behind an explicit `all=true`.

### MC-015 — Discoveries duplicated across ayanāṃśas · Severity: LOW
- **What happened.** `bodha_discoveries_get` returned the *same* Sade Sati anomaly repeated
  across 6 ayanāṃśas (lahiri, krishnamurti, surya_siddhanta, true_chitra, raman, …); of 1,269
  total, the top rows shown were largely one finding × ayanāṃśa variants.
- **Consumer impact.** The "top discoveries" surface looks richer than it is; near-duplicates
  crowd out genuinely distinct findings.
- **Recommendation.** Dedupe by finding and collapse ayanāṃśa variants (or default to the pinned
  ayanāṃśa), exposing the cross-ayanāṃśa agreement as a robustness score rather than N rows.

---

## E. Endpoint-side errors (mine) with portal-shaped contributing factors

### MC-016 — Yoga-firing `constituent_planets` merges debilitated + rescuer grahas → invited my Mars error · Severity: MED
- **What happened (my error).** In my first reading I stated "Neecha-Bhanga Raja Yoga:
  debilitated Mars in Libra cancelled…". **This was false and mine** — Mars is neutral in Libra
  (debilitation is Cancer). The portal never said Mars was debilitated.
- **Portal-shaped contributing factor.** `ganita_yoga_firings_get` for
  `neecha_bhanga_raja_yoga` exposes `constituent_planets: [venus, mercury, saturn, mars, sun]`
  — a **single flat array that mixes the two *debilitated* grahas (Venus@Virgo/D9,
  Saturn@Aries/D9) with the *rescuer* grahas (Mars, Sun, Mercury as dispositors/exaltation-lords
  in kendras).** The debilitated-vs-rescuer distinction only appears if you parse the nested
  `grounds_jsonb` per-planet. The flat list makes the wrong reading the path of least resistance:
  Mars appears "in" the yoga, so a fast reader miscasts it as a subject rather than a rescuer.
- **Consumer impact.** A trust-damaging factual error reached the native before correction. I
  own the miss (I should have read `grounds_jsonb`), but the schema actively invited it.
- **Recommendation.** Yoga firings should expose **separate labeled fields** —
  `debilitated_planets`, `rescuer_planets` (and for other yogas, `principal_planets` vs
  `supporting_planets`) — instead of one merged `constituent_planets`. This single change would
  have prevented the error. Verified correct data post-hoc via `chart_snapshot` D9:
  Saturn in Aries, Venus in Virgo, Mars in Pisces (friend, not debilitated).

### MC-017 — Ambiguous status label "not_computed_at_l1" → my over-generalization · Severity: LOW
- **What happened (my error).** I told the native "D10 and several vargas were not
  materialized," implying the underlying data was absent — when `chart_snapshot` proves D9/D10
  positions exist.
- **Portal-shaped contributing factor.** The assessor's status token **"not_computed_at_l1"**
  is ambiguous: it actually means "this assessor's *curated varga block* was not populated," but
  it *reads* as "the varga was not computed at L1." The label conflates a serving gap with a
  data gap.
- **Recommendation.** Relabel to something unambiguous, e.g.
  `domain_varga_block_absent (raw positions available via chart_snapshot / chart_divisionals)`.

### MC-018 — Dual server identity (claude.ai MARSYS-JIS vs marsys-jis-direct) · Severity: LOW
- **What happened.** The session exposed both a `claude.ai MARSYS-JIS` connector (needs OAuth,
  unavailable in this non-interactive session) and a `marsys-jis-direct` toolset (live). I
  correctly used the latter, but had to reason about which was canonical.
- **Recommendation.** Document the relationship/canonicality of the two surfaces so a consumer
  isn't guessing which to trust when both appear.

---

## F. Efficiency / turn-economy observations

### MC-019 — No "reading-optimized" tool tier → many turns spent extracting · Severity: MED
- **What happened.** To assemble one deep read I spent significant turns (a) re-pulling large
  low-yield arrays (MC-014), (b) `jq`-extracting spilled 150KB files (MC-004), and (c) parsing
  nested grounds (MC-016). The interpretive payoff per byte/turn was low on the heavy tools.
- **Recommendation.** A `reading` verbosity tier across `assess_*`, `ganita_chart_facts_get`,
  and `bodha_*` that returns a compact, prose-first, hardFloored-verdict projection would
  collapse most of this. The building blocks already exist per §N.6 (`density_contract`,
  `hardFloor`); they are not consistently applied to the heavy domain tools.

### MC-020 — Coverage of the six layers was possible and mostly coherent · Severity: N/A (positive baseline)
- **What happened.** Despite the above, I *was* able to reach every layer (Gaṇita → Bodha →
  Kāla → Phala → Mīmāṃsā) and produce a grounded, cross-checked read. The instrument's breadth
  is real; the friction is in packaging and freshness, not in the underlying computation.

---

## Preserve-list (what worked well — do not regress)

- **`chart_snapshot`** — compact, verbatim, well-grounded; the `include_navamsa` + `vargas`
  params returned D1/D9/D10 cleanly and let me *verify* a disputed claim against source in one
  call. This is the model the heavy tools should imitate. **Best tool in the set for endpoint use.**
- **`synth_chart_brief_get`** — a good compact entry point; coverage receipt + dissent flags +
  explicit STRUCTURAL calibration note are exactly the honesty signals an endpoint wants
  (modulo the "denied" wording, MC-010).
- **`ganita_yoga_firings_get`** — the firings-vs-catalog distinction (JL-004) and per-yoga
  `bhanga` grounds are genuinely acharya-grade; the nested `grounds_jsonb` for Neecha-Bhanga was
  correct and complete (my miss was not reading it — MC-016).
- **`kala_life_arc_get`** — the parva timeline (1984→2054 with quality labels) was compact,
  legible, and immediately usable narrative scaffolding.
- **Honesty fields throughout** — `judgment_flags`, `trim_report`, `recover_via`,
  `catalog_only_note`, `defect_001_alert`, `n_support`, `verification_pass_status`. The
  instrument is unusually transparent about its own gaps; that transparency is *why* this
  register is even possible. Preserve and extend it.

---

## Session context (for the remediation reader)

- **Chart under read:** Abhisek Mohanty, `482012f1-710e-4a25-994a-93821f5871aa`, Lahiri,
  build_id `60954f5a…` (pinned 2026-07-25), Bodha build_id `42720d15…` (older — the MC-001 gap).
- **Tools exercised (~18 distinct):** mcp_server_info, catalog_charts_list, catalog_chart_select,
  chart_snapshot (×2, incl. D9/D10), synth_chart_brief_get, ganita_chart_facts_get,
  ganita_positions_get, ganita_strength_get, ganita_nakshatra_get, ganita_yogas_get,
  ganita_yoga_firings_get, ganita_dashas_get, ganita_sade_sati_get, bodha_chart_digest_get,
  bodha_discoveries_get, bodha_quality_get, bodha_bundle_get, dossier (career/wealth),
  assess_career, assess_marriage, assess_wealth, kala_life_arc_get, phala_outlook_get.
- **Highest-leverage fixes, if only three ship:** MC-004/005/006 (envelope + hardFloored prose;
  makes the assess_* family actually consumable), MC-010 (stop "denied"-labeling empty structural
  priors; safety), MC-016 (split debilitated vs rescuer in yoga firings; prevents the exact
  error that reached the native).

---

## G. Session continuation — deep-dive round (appended 2026-07-27)

### MC-021 — `ganita_tajaka_get`: `varsha_year` filter ignored; current solar year unreachable · Severity: HIGH
- **What happened.** Called with `varsha_year: 43` (the running 2026-02→2027-02 solar year).
  Response echoed `varsha_year_filter: null` and served the identical default page: varsha
  years **1–5 (1984–1989)**, oldest-first, hard-capped at 5 rows of 48. Two identical calls,
  same result. The *current* varṣa-phala — the single most consultation-relevant annual chart —
  cannot be reached through this tool at all: the filter is not honored and the default sort
  serves the native's infancy years.
- **Consumer impact.** Annual (Tājaka) analysis for "this year" is effectively unavailable to
  the endpoint despite 48 fully-computed, two-pass-verified varsha rows existing in
  `l1_tajik_varsha_year_lords`. Had to disclose the gap to the native instead of reading their
  current year.
- **Recommendation.** (a) Honor `varsha_year`; (b) default sort should be **current-year-first**
  (or accept a date and resolve the varsha containing it); (c) the hadda_lord_facts block
  (245 rows of static tables) drowns the envelope — split it behind a flag.

### MC-022 — `kala_priority_ranking_get`: no domain filter; wealth/career query answered mostly with "character" signals · Severity: MED
- **What happened.** The ranked window (2026-07-26→2026-10-24) returned 20 signals of which
  ~14 are domain=character composite-state rows (dispositor-tree positions, per-varga dignity
  "neutral" rows, D24/D27 bindu counts). No `domain` parameter appears to exist; the consumer
  cannot ask "what is prioritized *for wealth* in this window."
- **Consumer impact.** The priority surface is generically Saturn/character-weighted and
  needed manual filtering; several rows (e.g. "dignity state = neutral") carry near-zero
  interpretive content yet rank top-20 by salience.
- **Recommendation.** Add `domain`/`domains` filter; suppress or down-rank neutral-dignity
  descriptor rows from priority surfaces (a "neutral" state is rarely a *priority*).

### MC-023 — `judgment_query`: strong content, but envelope duplicates its own verdict block and still overflows 12kb · Severity: MED
- **What happened.** The wealth judgment is the best single interpretive artifact the portal
  produced this session (deterministic checklist verdict `convergent_moderate`, split
  bhāveśa-from-lagna vs from-Moon, D2 varga term, signed yoga-vs-affliction layers). But the
  envelope carries the **full verdict object twice** (top-level `verdict` and
  `content.verdict`), plus the `receipt` twice, plus a long `register`/`reading_contract`
  boilerplate block — and *still* flagged `budget_exceeded_after_trim` at 12kb with clause
  texts truncated mid-sentence (same §N.6 inversion as MC-005).
- **Consumer impact.** Redundancy consumed budget that the truncated verdict prose needed.
- **Recommendation.** De-duplicate verdict/receipt; move `register` token-glossary behind a
  `verbosity` flag; hardFloor the clause texts.

### Positive (append to preserve-list)
- **`judgment_query`'s verdict decomposition** — bhāveśa dignity/shadbala from lagna AND from
  Moon, operative-varga (D2) term with explicit "varga_moved_verdict: false", signed
  yoga-vs-affliction separation, and resolution_chains in plain language — this is exactly the
  acharya-grade decomposition an endpoint needs. Fix the packaging (MC-023), keep the content.
- **`ganita_special_lagnas_get`** — clean, complete, CONFIRMED receipts; Indu/Sree/Hora/Ghati
  lagnas with nakshatra + lords served compactly. Enabled a genuinely finer wealth reading
  (Indu Lagna in 8th w/ Ketu; Sree Lagna conjunct exalted Saturn within ~0.5°).
- **`synth_tail_divergence_get`** — the BA-P4 dissent tier surfaced
  `varga_ratification_divergence:SAT:wealth` (malefic, major) as the top tail signal — the
  instrument itself flagging the D1-exalted/D9-debilitated Saturn split for wealth. Dissent
  layer works.

### MC-024 — `ganita_tajaka_get`: filter ignored under BOTH plausible param names (retry confirmed) · Severity: HIGH (upgrades MC-021)
- **What happened.** Retried with `varsha_year_filter: 43` (the exact field name the response
  echoes). Same result as `varsha_year: 43`: echo `varsha_year_filter: null`, identical default
  page (varsha 1–5, 1984–89). Unknown params are silently swallowed (no zod rejection, unlike
  `dossier`'s strict schema — inconsistent validation posture across tools). Three attempts,
  three identical responses; the current varṣa-phala is confirmed **unreachable**.
- **Recommendation.** As MC-021, plus: unknown-parameter calls should ERROR (strict schema),
  not silently serve the default — a consumer cannot distinguish "filter unsupported" from
  "filter accepted but empty result".

### MC-025 — `bodha_remedies_get`: flat, non-discriminating priority ranking that contradicts the digest's weakest-graha · Severity: HIGH
- **What happened.** The remedy layer ranks ALL 9 grahas `remedy_priority_class: "high"` with
  resonance scores in a 0.49–0.53 band (spread 0.04) — no discrimination whatsoever. Worse, it
  names **Mercury as weakest_rank_in_chart=1** while `bodha_chart_digest_get` for the same
  chart/build names **Venus** as weakest graha (`shadbala_total_min`, BPHS Ch.27, CR-55 fix).
  Two Bodha surfaces disagree on the single most remedy-relevant fact. Also `is_yoga_karaka_flag:
  false` for every graha, `domain_burden: 0` everywhere, `associated_doshas_array` NULL
  bo_upaya-wide (disclosed as writer gap).
- **Consumer impact.** The remedy-priority surface cannot be trusted for targeting: "everything
  is high priority" is no prioritization, and the weakest-graha contradiction forces the endpoint
  to adjudicate between L2 surfaces manually (I sided with the digest's shadbala-grounded Venus,
  which matches L1 ṣaḍbala directly). Prescriptions themselves (mantra/charity/gemstone with BPHS
  citations, feasibility scores, and honest `requires_acharya_review_flag` on gemstones) are
  well-formed — the *ranking above them* is the defect.
- **Recommendation.** (a) Root-cause the resonance formula's flatness (weakness_score ~0.48–0.51
  for all 9 suggests a normalization bug); (b) reconcile weakest-graha across digest and upaya
  writers to one authority (L1 shadbala per §N.5); (c) a priority class should have >1 value in
  practice or it isn't a class.

### Positive (append to preserve-list)
- **`ganita_av_transit_gating_get`** — excellent: full SAV/BAV per sign with
  damping/neutral/amplifying classification, mean-based banding disclosed, per-row fact_ids,
  compact. Enabled the 11th-house-damping vs 7th/8th-amplifying wealth-topology finding directly.
- **Gemstone prescriptions carry `requires_acharya_review_flag: true` + "ONLY if functional
  benefic" caveats** — exactly the right safety posture for the highest-cost, highest-risk remedy
  class; prevented me from naively recommending an Emerald (Mercury = 3rd/6th lord for Aries) or
  Hessonite. Preserve this gating.

---

## H. Endpoint wishlist — capability gaps ratified by the native for remediation (2026-07-27)

The native directed these be registered as improvement areas (depth = portal-side build items;
breadth = data the native can supply). Each is a capability the endpoint *needed and lacked*
during a live consultation.

- **WL-1 (depth, HIGH):** Current + next varṣa-phala servable (blocked by MC-021/024). Year-lord,
  Muntha house, Tājik yogas for the running solar year — the natural "this year" instrument.
- **WL-2 (depth, HIGH):** Materialize curated domain-varga blocks for the canonical chart —
  net argala on 2/10/11, per-varga aṣṭakavarga, D2/D10/D11 consumption blocks (MC-008). Raw
  `chart_divisionals` rows exist; the assessors' varga analysis serves empty.
- **WL-3 (depth, HIGH):** Bodha rebuild against current L1 (clear DEFECT-001 / MC-001) so the
  9,946-signal salience layer is traceable again and bundle sub-tools (MSR/CGM) stop erroring.
- **WL-4 (depth, MED):** Near-miss yoga detection (design §12 D3) — "one leg short" dhana/raja
  yogas are precisely where interventions could act; currently honestly-not-built.
- **WL-5 (depth, MED):** Multi-cycle daśā activation forecasts (D-3 successor) — kala_activations
  currently serve ONE resolved window per signal, not recurrences through the Venus MD.
- **WL-6 (depth, MED):** Birth-time rectification closure — 185 candidates, confidence
  "unresolved"; sub-period precision at the 2027 daśā boundary depends on it.
- **WL-7 (breadth, HIGH):** Native-supplied dated financial event history (10–15 events: launch,
  contracts, thresholds crossed, losses, loans, partnerships) → LEL enrichment → mi_* retrodiction
  and calibration. Converts structural verdicts to calibrated ones; the single highest-leverage
  data addition available.
- **WL-8 (breadth, MED):** Margin/retention figures (even coarse %) to empirically test the
  weak-Venus retention-bottleneck hypothesis against reality.

### MC-026 — `kala_projections_get` (ka_bhavishya_lekha): degenerate output — 25 near-identical rows, one window, domain mostly "general" · Severity: MED
- **What happened.** All 25 served projections (of 50) carry the SAME window (2027-10-20 →
  2030-04-03), same peak, same tier (tier_1_high), same effective_score (0.70), and 22/25 are
  domain="general" — despite CF.L3.5 ("domain inference in ka_bhavishya_lekha") being marked
  RESOLVED in the L3 close. No window-level dedup: the one real finding (a high-convergence
  cluster opening 2027-10-20) is served 25 times instead of once with 25 member refs.
- **Consumer impact.** The forward-projection surface reads as one insight photocopied; the
  narrative fields ("relocation, legal matter, public recognition") are generic boilerplate.
  Had to collapse manually. Contrast: `kala_windows_get`'s `window_families` dedup does this
  correctly — apply the same pattern here.
- **Recommendation.** Family-collapse projections by (window × domain); finish real domain
  attribution; vary falsifier text by domain.

### Positive (append to preserve-list)
- **`kala_windows_get` (ka_yojaka→ka_kalasutra serving)** — `window_families` dedup (50
  activations → 2 families with member lists), honest `forward_windows: []` empty, honest
  `single_cycle_per_signal` + `near_tier_build_date_relative` caveats. NOTE for docs: the
  "single cycle" caveat *understates* the data — `activation_predicted_dates_jsonb` in fact
  carries the full recurrence ladder (e.g. Saturn-AD re-fires 2032–33, 2047–50, 2057–58…)
  with start/peak/end triplets. The multi-cycle data exists; only the top-level window is
  single-cycle. Surface this.
- **`kala_yoga_activation_get`** — clean join of yoga signals × kala_activation with dated
  windows per yoga (Sasa: current window peak 2026-04-13; Vasi: next 2028-12-19→2029-01-02),
  `always_on_reason` honesty for distribution yogas, and inline live DEFECT-001 stats (47.1%
  on this slice). Good tool.

### MC-027 — `kala_muhurta_get`: no natal Tārā-bala/Chandra-bala overlay; 2-day granularity; no intra-day cut · Severity: MED
- **What happened.** The muhūrta scorer (panchanga 40% + dasha 30% + transit 20% + signal 10%)
  ranked 2026-07-30→08-01 as its #2 window — but that window's Moon is in **Shravana, a Vadha
  tārā** for this native's janma nakshatra (P.Bhadrapada), per the portal's OWN
  `tara_bala_natal_baseline`. The engine scores generic panchāṅga quality but does not join the
  chart-personalized tārā/chandra-bala baselines it already computed. Also: windows are served
  at 2-day granularity (00:00→00:00) with no intra-day muhūrta cut — had to manually join
  `phala_outlook`'s daily amrit/shubh/labh + abhijit + brahma-muhūrta blocks for hours.
- **Consumer impact.** An endpoint trusting the ranking blindly would schedule a remedial
  initiation on a personally hostile star. Cross-filtering by hand worked, but the join belongs
  server-side.
- **Recommendation.** (a) Weight tara_bala_natal_baseline + chandra_bala_natal_baseline into
  the muhūrta score (or at minimum emit an `avoid_notes` entry when the window's nakshatra is
  Vadha/Vipat/Pratyak for the chart); (b) serve intra-day sub-windows (the panchanga_daily
  table already has them).

---

## I. Native-audit findings — completeness failures identified BY THE NATIVE (2026-07-27)

The native audited the session and named concrete omissions the endpoint should have surfaced
unprompted in a "thorough financial deep-dive." Each was verified against the portal post-hoc.
This section is the most important in the register: it documents what a systematic reading
contract must guarantee, because salience-driven retrieval provably missed them.

### MC-028 — ROOT CAUSE (endpoint): salience-sampling instead of territory-enumeration; dossier completeness gate bypassed · Severity: HIGH
- **What happened.** The endpoint navigated by the portal's *ranked* surfaces (digest top
  signals, judgment checklists, discoveries) and composed readings from what those pushed up.
  The one tool that enforces full-territory coverage — `dossier` with its `synthesis_gate:
  BLOCKED / "Do NOT compose yet"` contract — was explicitly skipped because of its paging cost
  (MC-012), and the endpoint composed anyway from other tools. Every gap below flows from this:
  **the completeness mechanism existed, said "don't compose yet," and was overridden on cost
  grounds.** The native then had to extract depth by interrogation over many turns — the
  reading arrived Socratically instead of in one complete pass.
- **Recommendation.** Two-sided fix: (a) portal — make the dossier gate *satisfiable at
  consultation cost* (compact gate-summary per MC-012) so honoring it is realistic; (b)
  endpoint/governance — a domain reading MUST run a fixed classical checklist (bhava/bhāveśa
  from Lagna+Moon, kārakas, operative vargas, AV, special lagnas, sensitive degrees incl.
  pushkara/gandanta, KP cusp chain, yogi/avayogi, all daśā levels, gochara sweep, tājaka)
  regardless of what the salience layer ranks highly. Codify as a B.11-adjacent serving rule.

### MC-029 — Yogi/Avayogi planets: NOT SERVED anywhere in the fact catalog (suspected missing L1 asset) · Severity: HIGH
- **What happened.** The native asked why Mercury-as-Yogi / Mars-as-Avayogi never appeared.
  `ganita_sensitive_degrees_get` serves sahams, gandanta, pushkara, mrityu-bhaga, kartari,
  22nd-drekkana, 64th-navamsa — but NO yogi_point/yogi_planet/avayogi category, and none was
  seen in any other tool this session. Endpoint verification by arithmetic (B.10-flagged as
  endpoint-derived, not portal data): Yogi point = Sun(291.96°)+Moon(327.06°)+93°20′ =
  352.35° = Revati → **Yogi = Mercury**; +186°40′ → 179.02° = Chitra → **Avayogi = Mars**.
  The native's claim checks out; the portal appears to lack the asset entirely.
- **Consumer impact.** A standard wealth-relevant classical construct (and one the native
  KNOWS about their own chart) is invisible to the instrument. Materially relevant here:
  Yogi = Mercury = current MD lord (prosperity-bearing period-lord); Avayogi = Mars = Indu
  Lagna lord (the obstruction current inside the wealth engine).
- **Recommendation.** Add yogi/avayogi/duplicate-yogi (+ sahayogi) computation to the L1
  sensitive-points writer; two-pass verify; until then, document the absence in the capability
  map so endpoints disclose it.

### MC-030 — Mars in Puṣkara navāṃśa: fact EXISTS in L1, surfaced by NO ranked/synthesis surface · Severity: HIGH
- **What happened.** `sensitive_degree_check.MAR.pushkara = fired:true, in_pushkara_navamsa:
  true` (Libra 18°31′, pushkara navāṃśa from 16°40′) — **the only graha in pushkara in this
  chart**, and it is the Indu-Lagna lord + lagneśa, sitting in the 7th. Directly reshapes the
  Mars reading (nourished/redeemed placement; softens the Manglik weight; strengthens the
  deal-engine finding). It appeared in NONE of: digest top-signals, judgment layers,
  assess_wealth/career, discoveries, priority rankings — across ~25 tool calls. Only a direct
  `ganita_sensitive_degrees_get` call (prompted by the native) surfaced it.
- **Recommendation.** Salience priors should boost fired-state sensitive-degree facts
  (pushkara/gandanta/mrityu-bhaga *firings* are rare, high-information events); judgment_query
  house/graha checklists should consult sensitive_degree_check for the bhāveśa/kārakas.

### MC-031 — KP cuspal wealth chain (2nd/11th sub-lords): served only in the bottom-10% dissent tail; never in any wealth synthesis · Severity: HIGH
- **What happened.** `ganita_kp_cusps_get` confirms the native's stated chain precisely:
  **2nd cusp sub-lord = Rahu** (exalted IN the 2nd), 2nd prana-lord = Mercury; **11th cusp
  star-lord = Mars, sub-lord = Mercury**; significators 2nd=[Venus,Moon,Rahu],
  11th=[Saturn,Mars,Mercury] → the Mercury–Rahu–Mars cash-flow trio, with the current MD lord
  (Mercury) as the 11th's sub-lord — a coherent KP explanation of the Mercury-era business
  build. These facts were two-pass-computed and even appeared as wealth-tagged
  `cusp_kp_lords` signals — but at salience 0.36, in the **bottom-10% tail**, served only by
  `synth_tail_divergence_get`. No wealth-domain synthesis surface (judgment_query,
  assess_wealth, digest) integrates the KP layer. Endpoint co-fault: the tail tool served
  them and the endpoint did not drill.
- **Recommendation.** Add a KP block to the wealth/career judgment checklist (cusp sub-lord
  chain for 2/6/10/11 + ruling planets); re-examine the salience prior that floors
  tradition_specific/KP signals to the tail.

### MC-032 — Daśā depth: Sūkṣma (L4) computed but never served; default cap ≤3 silently governs every reading · Severity: MED
- **What happened.** `ka_dasha_kala` supports level-4 (Sūkṣma) tree-walk and `chart_dashas`
  holds 536k rows, but `ganita_dashas_get` defaults to `level cap<=3` and nothing in the
  session ever served or advertised L4. The endpoint never overrode the cap. For dated
  intervention timing (this session's actual use-case), Sūkṣma precision existed and went
  unused.
- **Recommendation.** Advertise available depth in the envelope (`levels_available: 4`);
  endpoints should request L4 for any date-precision question.

### MC-033 — Gochara sweep (ka_gochara / kala_gochara_windows) never consulted in the financial reading · Severity: MED
- **What happened.** The L3 transit-search engine and its windows table (plus
  `gochara_forecast_get` / `gochara_activation_get` tools) were never queried across the
  entire financial arc — the endpoint's timing story ran on the daśā plane (kalasutra/sangam/
  bhavishya) alone. Transit-plane corroboration (Jupiter over the 2nd, Saturn's ingress
  effects on the 11th, AV-gated transit scoring which WAS pulled but not joined to dates)
  was left on the table. Pure endpoint triage omission; the assets exist.
- **Recommendation.** Endpoint reading contract (MC-028) must include one gochara sweep per
  domain reading; portal could serve a `gochara_forecast(domain=…)` convenience that joins
  SAV gating automatically.

### MC-034 — Meta: "one-go completeness" failure mode, quantified · Severity: HIGH (umbrella)
- **What happened.** The native correctly observes that yogi/avayogi, pushkara, the KP chain,
  L4 daśās, and gochara ALL should have surfaced in the first "deepest possible" financial
  pass — instead they emerged only under sustained interrogation (and two only because the
  native already knew them). Root causes: MC-028 (strategy) + MC-008 (empty curated blocks
  removed the server-side checklist) + MC-029 (missing asset) + salience-prior floors
  (MC-030/031). The session's own structure proves the Socratic-extraction anti-pattern.
- **Recommendation.** Treat "complete-in-one-pass domain reading" as a formal serving
  contract with a receipt (the dossier's Ω-accounting is the right skeleton); an endpoint
  reading without that receipt should disclose "non-exhaustive: salience-sampled."

*Register remains LIVING for the remainder of the originating session; new items appended as
observed.*

---

## ADDRESSED-v1 close annotation (append-only, 2026-07-27)

Every item above (MC-001..034, WL-1..8) was carried through the ŚODHANA remediation campaign.
Full per-item disposition table, live evidence, and the two items reopened with a narrow
specified fix (MC-015, MC-029) are in `briefs/shodhana/SHODHANA_REPORT_v1_0.md` §2 and §5 of this
same directory — this annotation does not restate the table to avoid drift between two copies of
the same data; the report is canonical for disposition, this register remains canonical for the
original observations. Nothing above this line was altered.
