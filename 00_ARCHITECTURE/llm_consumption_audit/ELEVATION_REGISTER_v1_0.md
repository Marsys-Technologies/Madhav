---
artifact: ELEVATION_REGISTER
type: LIVING REGISTER — every identified gap between the current instrument and the target
  state ("beyond-acharya AI supercomputer: complete in depth and scope, seamless, superlative
  user experience"). Detailed logging first; deep root-cause analysis SECOND (a dedicated
  Fable pass once the native has finished adding his own findings); implementation THIRD.
version: 1.1
status: LIVING / OPEN FOR NATIVE ADDITIONS — native + Fable co-build, started 2026-07-24.
  Root_cause fields are deliberately TBD-PENDING-FABLE-PASS unless already firmly established.
sources: UAT_DARPANA_REPORT_v1_0 (interim) · RETRIEVAL_AUDIT_REPORT_v1_0 · native hands-on
  session (Claude Code + raw Marsys-JIS MCP, financial-domain probing, 2026-07-24) ·
  PRE_DARPANA_READINESS_v2_0 · NATIVE_PROXY_LEDGER · MARSYS_DEFECT_GAP_REGISTER (open CRs) ·
  FABLE SERVING-SESSION experience report (live raw-MCP wealth reading + muhurta election on
  chart 482012f1, 2026-07-24) — EL-36..EL-61, four items re-verified against the live server
namespace: EL-nn (this register). Cross-references CR-nn (defect register) where they overlap —
  EL items are USER-VALUE gaps; CRs are engineering defects; one may cite the other.
how_to_add: append a new EL-nn block using the template at the bottom. Rough notes are fine —
  symptom + example is enough; Fable will structure it on the next pass. Nothing is too small.
---

# ELEVATION REGISTER — everything between here and beyond-acharya

## Reading guide

Severity: **T** = trust-breaking · **V** = value-losing · **C** = cosmetic · **P** = process/
instrumentation (blocks our ability to SEE the others). Status: OPEN unless stated.
Layer guesses are provisional until the root-cause pass.

---

## SECTION A — Completeness of consumption (depth & scope at the answer level)
*The native's core finding: the single differentiator is deterministic full-depth use of every
computed concept — and today's answers don't deliver it unprompted.*

**EL-01 · Concept-consumption gap on domain questions — <50% of relevant concepts used by
default. [V→T, flagship]**
Symptom (native hands-on, financial questions): default answers factored in well under half the
concepts relevant to the domain; persistent nudging raised it to ~80%; an estimated ~20%
remains unknown-unknown (native cannot enumerate what else exists that was not used). Cited
examples (explicitly examples, NOT the full diagnosis): dispositor chain unused until asked;
special lagnas + bindus unused until asked; varga-chart ashtakavarga never surfaced at all.
Expectation violated: native doctrine — deepdive default; full-depth deterministic consumption
is the product's ONLY differentiator vs. hundreds of superficial products.
Suspected layers: consumption/answerer (floor compiled but not executed), serving guidance,
possibly floor content gaps. Root cause: TBD-PENDING-FABLE-PASS (candidate: EL-02 mechanism).
Fix direction (initial): floor-execution enforcement + concept-consumption metric (EL-03/04).

**EL-02 · Floor exists as an OFFER, not a CONTRACT — execution + receipt not enforced. [V→T,
structural cause candidate for EL-01]**
Symptom: VIDHI-PŪRṆATĀ makes the planner compile full floors (26+ items incl. dispositors,
special lagnas, AV), but nothing forces a consumer — especially a raw-MCP client like the
native's Claude Code session — to execute all floor items and synthesize from them. The
completeness-receipt machinery (plan_retrieval `observations` → served/empty/dark accounting)
EXISTS but is optional and effectively unused in real consumption.
Expectation violated: "demand-side chase made concrete as a compiled contract" (D-2's own
design language). Suspected layer: serving contract / consumption loop.
Fix direction: mandatory receipt round-trip; answer verified against its receipt (see EL-21).

**EL-03 · No definition of "100%" per domain — the concept ledger is missing. [V]**
Symptom: nobody can currently enumerate what FULL consumption for a financial (or any domain)
question means; the native's ~20% unknown-unknown is unmeasurable. The raw material exists
(Phase 0.7's 46-concept census, the vidhi floors, the L1 fact-category inventory) but no
mechanically-derived per-domain concept ledger joins them.
Fix direction: generate the per-domain ledger FROM the data (census × floors × fact_category
inventory), maintained by CI, serving as the denominator for EL-04.

**EL-04 · No standing concept-consumption metric. [P]**
Symptom: consumption completeness is invisible — Darpana graded answers against
`pass_looks_like`, not against the domain corpus; SUBSTANCE scored "at ceiling" while the
native measured <50% live. DR-18 (use-all-we-know) has no serving-time metric.
Fix direction: per-answer consumption ratio (consumed / ledger), tracked in the standing
battery; target ≥90% on naive domain questions.

**EL-05 · Naive-vs-expert volunteering gap — naive wealth query volunteers ~1/5
founding-incident findings vs expert 5/5. [V]**
Evidence: DARPANA §4/§6 (S1-01 vs S1-07, item-by-item verified by Fable against verbatim
answers). Depth exists and is retrievable; the naive user receives a shallower reading of the
identical chart. Both graded DELIGHT — the gap is invisible to the band, only the benchmark
count sees it. Single controlled pair (n=1) — needs a second-domain pair.
Fix direction: insight-first volunteering contract — naive domain answers must surface the
chart's own top-N chart-defining findings (gestalt/laksana ranking) unprompted; benchmark
pairs per domain in the standing battery.

**EL-06 · Varga-level depth specifically absent from answers (per-varga AV bindus, varga
dignities, varga-lord webs) unless demanded. [V — child of EL-01, logged separately because
the native flagged it and it is checkable]**
Symptom: varga-chart ashtakavarga never volunteered in any financial answer. Data confirmed
SERVED (census A.7: per-varga AV rows live).
Fix direction: covered by EL-01/02/05 machinery; verify with a varga-depth probe in the
standing battery.

---

## SECTION B — Truth & calibration (the honesty seam)

**EL-07 · False-confidence at the retrieval boundary — S4-03 Gulika veto. [T, flagship]**
Symptom: answer asserted, in self-branded "honest" language, that Gulika "isn't actually in
your computed chart data" — data exists two-pass-verified in categories
`sensitive_point_gulika_mandi` + `saturn_derived_point`. Empty naive probe was escalated into
an ontological absence claim. Verified verbatim by Fable.
Class evidence: Phase 0.7 found the SAME class 3× (sphutas, panchanga, mangal — naive filter →
empty → misread as absent); instance-fixes do not kill the class.
Fix direction: the Absence Protocol — "not in your data" claims require a concept-resolver
proof (EL-08); otherwise forced phrasing "not found in what I queried"; serving-time
claim-checker (EL-21).
> **PARTIAL-CLOSE annotation (SATYA-ŚEṢA campaign, 2026-07-25).** The concept-resolver half of
> the fix direction (EL-08's `concept_locate` + `tool_search` steering to it) shipped in a prior
> campaign — `tool_search("gulika")` was confirmed live-steering to `concept_locate` +
> `get_database_schema` as of the SATYA-ŚEṢA G0 baseline probe (2026-07-25). But the OTHER half —
> the bare-empty itself on the keyword-filtered serving path — remained fully live at that same
> probe: `ganita_chart_facts_get(keyword="gulika")` returned `{facts: [], total: 0}` with no
> `empty_reason`, no alias suggestion, and no resolver pointer inline in the response (SATYA_SHESHA
> BRIEF §1, "Verified STILL BROKEN" item 1). This is what still let S4-03 happen: the resolver
> existed but nothing in the query path told the caller to use it. SATYA-ŚEṢA W1 (Builder B1) closed
> this remaining half by making every query-shaped bare-empty carry `empty_reason` +
> `resolver_suggestion` inline. PR pending — item implemented in the same SATYA-ŚEṢA campaign cycle,
> see `SATYA_SHESHA_LEDGER.md` for the final PR number.

**EL-08 · No concept-resolver (canonical concept name + aliases → true serving category).
[V→T enabler]**
Symptom: Gulika/Maandi, sphuta, panchanga, mangal all reachable ONLY under non-obvious
category names; any naive consumer repeats S4-03's probe path. The census matrix already maps
concept → category — it is not served as a callable surface.
Fix direction: first-class `concept_locate` tool built from the census; census-vs-alias CI
regression (new concepts must register aliases or fail).

**EL-09 · Confident checkable astrological errors at cosmetic tier (the precision class). [C,
pattern]**
Instances: Sade-Sati 2023 called "tail/easing" when it was Janma-Shani peak (S4-06,
audit-corrected); Moon repeatedly called "soul-indicator" (naisargika soul-kāraka is the Sun;
S1-06, S2-03); "9th-house income channel" over-read (S1-01); "grounded in your actual chart"
bare promise (S4-01); lay glosses ("3rd = siblings"; Kemadruma cancellation attribution).
Shared shape with EL-07 at lower stakes: confident claims never checked against computed data
or the classical record. Fix direction: claim-checker (EL-21) covers phase/timing claims
against ganita surfaces + a small classical-attribution table for karaka/gloss claims.

**EL-10 · Grading/verification unreliability — single-pass grading missed the top failure;
~22% audit-overturn on the sampled slice; ~27–28 of 36 scored queries never independently
verified. [T, process]**
Evidence: DARPANA §3 (S4-03 rated perfect DELIGHT by first-pass grader; S4-06 also overturned).
Fix direction: two-pass grading (grader + DB-verifying auditor) becomes PERMANENT LAW for the
standing battery; adversarial audit widened to the full scored set before any ACCEPT.

---

## SECTION C — Serving envelope & client adaptability (superlative UX mechanics)

**EL-11 · Tool responses exceed real client caps — hard errors on standard-context clients.
[T for affected users, flagship UX]**
Symptom (native hands-on, Claude Code + raw MCP): repeated failures "tool response exceeds
maximum allowed tokens" during financial-question probing; disappeared on the 1M-context
option. Claude Code's default per-tool-response cap (~25k tokens, MAX_MCP_OUTPUT_TOKENS)
is the real-world floor; our depth-first responses blow through it. A user without the 1M
option cannot receive full depth at all — it errors instead of adapting.
Expectation violated: server adapts to the smallest real client; depth arrives in more turns,
never as a failure.
Fix direction: default per-response budget sized to the lowest-common client cap; digest-first
+ paginated drill-down universally (the §N.6 layered-density architecture enforced for real);
client-budget parameter on every tool; CI gate asserting worst-case response per tool on chart
482012f1 fits the default cap. Note: §N.6 budget machinery exists — evidence says budgets are
sized to a generous ceiling and/or some responses bypass the trimmer. Root cause:
TBD-PENDING-FABLE-PASS (audit which tools exceeded, against what configured budget).
> **PARTIAL-CLOSE annotation (SATYA-ŚEṢA campaign, 2026-07-25).** The §N.6 budget machinery
> (`response_budget.ts`, `budgetMcpContent`) was live and enforced on several core tools by the
> time of the SATYA-ŚEṢA G0 baseline probe, but the kala/gochara family had escaped the census
> check entirely: `gochara_forecast_get` (2026-08→2029-12 window) served **69,404 chars** and
> `kala_windows_get` served **50.2 KB** — both well past the ~25k-token small-client cap this item
> names, with no trim applied (SATYA_SHESHA BRIEF §1, "Verified STILL BROKEN" item 3; same finding
> cross-referenced at EL-42 below). SATYA-ŚEṢA W3 (Builder B2, same owner as W2) closed this by
> extending `response_budget.ts` enforcement to `gochara_forecast_get`, `kala_windows_get`,
> `kala_bundle_get` and family, with the W2 `coverage` block declared hardFloor-immune so honesty
> fields survive any trim. PR pending — item implemented in the same SATYA-ŚEṢA campaign cycle, see
> `SATYA_SHESHA_LEDGER.md` for the final PR number.

**EL-12 · No client-budget negotiation. [V]**
Symptom: the server cannot know the caller's response ceiling; one fixed budget must fit all.
Fix direction: budget/max_tokens parameter (or MCP-level negotiation) honored by the response
packer; documented client profiles (Claude Code 200k default / 1M / Cowork / product UI).

**EL-13 · Tool-catalog caching — newly registered tools invisible until client session
restart. [C→V, UX friction]**
Evidence: RETRIEVAL_AUDIT §7 (bodha_mechanisms_get not round-trippable mid-session; same
limitation hit in PRE_DARPANA v2.0 for CR-24/CR-30 tools).
Fix direction: document + (if MCP protocol allows) server-initiated tool-list refresh; at
minimum a serving-note surfaced to clients.

**EL-14 · Product must not depend on answerer intelligence for completeness. [V, principle]**
Symptom: Darpana assessed Opus-over-MCP (best case); the native's own session showed even a
strong client under-consumes without enforcement; lesser clients will do worse. The floor/
receipt/insight machinery must live SERVER-SIDE (contract + verification), not in hoped-for
client behavior. Cross-cuts EL-02/EL-11.

---

## SECTION D — Timing layer (crown jewel — still pending)

**EL-15 · S3 "Tell me when" entirely unverified — 8 S3 queries + S4-05 provisional. [V →
latent T until re-run]**
Status: T-2 full sweep running (fresh build, fingerprint-invalidated ledger, ~300 substeps);
re-run plan fixed (fresh naive answerers, replace-in-place, full audit, instrumentation
captured). Verdict on the most user-central promise is OPEN until then.

**EL-16 · Sweep architecture v1 — no span/year-filter capability; full-century-per-chart cost;
6h-timeout history. [V, architecture]**
Evidence: STAGE_4 dispatch note (no year-filter exists in plan_substeps; honest full dispatch);
16/16 prior attempts errored (W-0 truth pass); span/birth-year bug fixed in SARVA-SIDDHI.
Fix direction: D-6 GOCHARA-SWEEP-2.0 (event-driven, minutes/chart, sub-day honest) — staged,
ratification pending; v1 corpus completing now becomes its equivalence baseline.

**EL-17 · Timing-anchor residuals — CR-66 phala domain anchors + CR-37 activation dating:
code fixed, DATA state to re-verify post-rebuild; two Stage-2 residuals documented in
PRE_DARPANA v2.0. [V]**
Fix direction: pull the two documented residuals from v2.0 into this register explicitly
(NATIVE TO CONFIRM details on next pass); verify anchors/dating live after current rebuilds.

---

## SECTION E — Computation gaps (deterministic math not yet built)

**EL-18 · Per-dosha bhanga/cancellation not computed beyond NBRY. [V, honest residual]**
Evidence: RETRIEVAL_AUDIT §6.3 — firings surface discloses `bhanga_na_reason` "no per-yoga
bhanga formula implemented … to avoid fabrication (B.10)"; e.g. Kuja/Manglik cancellation
status not evaluable for the chart; only Neecha-Bhaṅga fully computed (per-varga, grounded).
Fix direction: scoped L1 Gaṇita session — author + classically validate per-dosha bhanga rules
in ga_yoga_writer, firings-authoritative, citations mandatory.

**EL-19 · Sahams (Arabic-parts-style points) — REACHABLE-BUT-EMPTY, never computed. [V]**
Evidence: census A.7 — zero saham rows under every category tried; honest gap, not a filter
bug. Fix direction: decide compute-vs-defer (L1 writer addition; Tājaka sahams have classical
grounding — natural companion to the existing ganita_tajaka surface).

**EL-20 · Serving-rank residuals — arudha/UL ranking (CR-61), nakshatra-semantic ranking
(CR-64): raw rows serve, salience ranking absent. [C→V]**
Fix direction: deterministic salience ranks (documented formulas) on both surfaces; NO
fabricated weights.

---

## SECTION F — Verification, instrumentation & process (the ability to SEE)

**EL-21 · No serving-time claim-checker. [T enabler — the one mechanism behind EL-07/09]**
Concept: before serving, any answer bearing absence claims / exact values / phase-timing
assertions gets a fast deterministic verification against the same surfaces it cites (the
adversarial auditor's method, promoted into the product). Root-cause pass to scope: where it
runs (serving layer vs product harness), latency budget, which claim classes first.

**EL-22 · Four mandated instrumentation tracks not captured in Darpana run 1 — experience
telemetry, investigation I1–I5, Vidhi V1–V5, retrieval RE1–RE5. [P, proven costly]**
Evidence: DARPANA §9 (all not_captured). Consequence PROVEN: the two biggest user-facing
problems (EL-01, EL-11) lived exactly where instrumentation was missing and were found only by
the native's manual session. Fix: capture all four tracks in the S3 re-run and every future
battery run — non-negotiable harness requirement.

**EL-23 · Battery blind spot — graded "excellent for its scope," not "complete against the
corpus." [P]**
Symptom: pass_looks_like criteria let scope-shallow answers score perfect (S1-01 DELIGHT at
1/5). Fix: add consumption-ratio (EL-04) + volunteered-findings counts as first-class grading
dimensions in the standing battery; benchmark pairs per domain.

**EL-24 · Build-state truthfulness — stale-display class + zombie build_run recurrence. [V,
ops]**
Evidence: ~70h zombie BUILDING banner (root cause: paused Cloud Scheduler reconciler — fixed);
substep-ledger fingerprint invalidation surprising the native; tracker shows no substep
denominator or dispatched-scope, so scoped-vs-full is invisible in the UI.
Fix direction: reaper/self-heal for orphaned runs (affordance noted in SARVA-SIDDHI); Nirmāṇa
surface substep progress + build scope; build_run rows carry plan metadata legibly.
> **AMENDMENT (SATYA-ŚEṢA campaign, 2026-07-25) — the reaper/self-heal fix direction above must be
> HEARTBEAT-based, never age-based.** New evidence, not present at this item's original filing: the
> T-2 gochara sweep's operational run (4 dispatch cycles / ~7 hours to reach 303/303 substeps)
> produced **1 false-positive "failed" from an overzealous watchdog reaper that nearly caused a
> duplicate concurrent-writer dispatch** — caught and avoided, but a real near-miss on a live
> multi-hour build (FABLE_HANDOFF_SUMMARY.md, "Protocol + operational incidents"). Root cause: the
> reaper was judging liveness by elapsed wall-clock age since the run started, which cannot
> distinguish a dead writer from one that is simply slow — the exact failure mode the M2.2 pattern
> (`ELEVATION_CAMPAIGN_CHARTER_v2_1.md` §M2.2) was hardened against for the elevation-campaign lock
> mechanism after an equivalent incident there. **The corrected rule for any reaper/self-heal
> affordance touching `build_run`/orchestrator liveness: judge liveness by HEARTBEAT freshness
> (the holder/writer rewrites a `heartbeat_at` on a short fixed interval), and only declare a run
> dead after a two-phase break — write a break-intent, wait one grace interval for the holder to
> bump its heartbeat, THEN break — never by raw elapsed age since the run started.** An age-based
> reaper will always eventually misfire against a legitimately long-running build (a multi-hour
> gochara sweep, a full L1 rebuild); a heartbeat-based one only fires against an actually-stalled
> process. This amendment does not close EL-24 — the fix direction above (self-heal, tracker
> surfacing, plan metadata) remains open — it constrains HOW any future reaper/self-heal
> implementation must work. Cross-refs EL-24's own "Fix direction," M2.2 pattern.

**EL-25 · Governance/ratification debt. [P]**
Open: NATIVE_PROXY_LEDGER ratification (battery stamp, 3 pre-registration corrections, S4
dispositions made in the native's name); Phase 0.7 PROVISIONAL→FINAL same-day flip — verify
the d1278fa9 pin independently if any ruling turns on it; D-6 §7 questions N1–N5 pending;
DR sweep post-hoc ratifications through DR-20.

---

## SECTION G — Native additions (append below; template at bottom)

**EL-26 · Planner does not leverage the full asset catalog — the asset-documentation exercise
is not wired into planning. [V→T, flagship; native 2026-07-24]**
Symptom (native): a complete documentation of every data + service asset was built precisely so
the planner could fully exploit the corpus for beyond-acharya insight — but the planner today
plans from its own small primitive registry, not from the asset catalog. Huge computations sit
unleveraged, leaving the portal "mediocre as the other market alternatives."
VERIFIED case in point (Fable, planner registry grep 2026-07-24): per-varga ashtakavarga —
`varga_ashtakavarga` rows live and served for every varga (census A.7) — has NO planner
primitive; the only AV primitive (`ashtakavarga_scan`) is hardcoded to the natal category.
Computed, stored, reachable, never planned.
Expectation violated: CAPABILITY_MANIFEST / asset docs ↔ planner floors should be provably
congruent — every asset's insight-bearing categories reachable from some floor/primitive.
Suspected layer: planner registry authorship (hand-curated primitives vs. machine-derived
coverage). Root cause: TBD-PENDING-FABLE-PASS (hypothesis: floors were authored from worked
examples, never reconciled against the full asset/category inventory — same class as EL-03).
Fix direction: mechanical asset-catalog→planner coverage audit (every fact_category × asset →
covering primitive or explicit exclusion with reason); CI gate so new assets/categories cannot
land unplanned.

**EL-27 · Cross-ayanamsha insight engine absent — six ayanamshas computed, zero comparative
use. [V, pure supercomputer differentiator; native 2026-07-24]**
Symptom (native): five/six ayanamsha readings exist as data (lahiri_chitrapaksha, krishnamurti,
raman, surya_siddhanta_classical, true_chitra + INVARIANT) but no insight is generated from
interpretation VARIATION across ayanamshas.
VERIFIED (Fable, same grep): the word "ayanamsha" appears ZERO times in the planner registry —
the planner cannot express the concept at all.
Why it matters: robustness-across-ayanamshas vs. flips-on-ayanamsha is a confidence/rarity
signal no human acharya can produce and no market product computes — a paid-for, fully dark,
uniquely-ours capability. (Note: KP floors arguably REQUIRE krishnamurti-ayanamsha reads even
standalone.)
Fix direction: a `cross_ayanamsha_variation` primitive family (dignity/vargottama/house-shift
deltas across the 6; agreement score per finding; divergence flags served as judgment_flags) +
planner awareness of ayanamsha as an axis. Root cause of absence: TBD-PENDING-FABLE-PASS.

**EL-28 · Small-context adaptation as a FIRST-CLASS CAPABILITY (native mandate — elevates
EL-11/EL-12 from bug to product requirement). [T for affected users; native 2026-07-24]**
Native directive: the instrument must serve ALL LLM clients — 200k, 1M, 2M, anything — by
ADAPTING the serving, never by erroring. Large-context is the easy case; the capability to
establish is the mechanism for small windows: budget-aware packing, digest-first layering,
paginated drill-down, cursorable continuation — such that identical DEPTH arrives in more
turns on a smaller client. Deliverable is a named, documented, tested capability (client
profiles + negotiation), not a config tweak. Subsumes EL-11 (overflow errors) and EL-12
(no negotiation); those become acceptance tests of this capability.

**EL-29 · Presentation/narrative layer absent — interpretation served as-data-arrives, no
established reading structure. [V; native 2026-07-24]**
Symptom (native): responses lack a clear narrative and complete structure; interpretation is
emitted incrementally as each retrieval lands, instead of: pull ALL data → comprehend the
complete picture → THEN compose. The final response must be a well-reasoned, well-elaborated,
structured reading.
Expectation violated: an acharya's reading has a FORM — orientation/gestalt first, then
promise, evidence chains, tensions and their adjudication, timing, guidance — built after the
whole chart is absorbed, not narrated during retrieval.
Suspected layer: consumption loop (gather-then-compose discipline absent) + serving guidance
(no composition doctrine/template served to the answerer). Interacts with EL-02 (receipt =
"gathering complete" signal — the natural compose-gate) and EL-28 (structure must survive
small-context serving via staged composition).
Fix direction: composition doctrine — a served reading-structure contract (the "presentation
layer"): gathering phase closes (receipt filed) before composition begins; response follows
the established narrative form; verified by the standing battery's structure checks.
Root cause: TBD-PENDING-FABLE-PASS.

---

### Consumer-LLM experience report (native-relayed 2026-07-24 — a consuming LLM's own
friction report from live raw-MCP use; the product's actual target persona as witness)

**EL-30 · CRITICAL — `house_d1` semantics inconsistent with its name in `arudha_pada` (and
possibly other categories): likely 0-indexed value under a 1-indexed-house key. [T, data
integrity]**
Consumer symptom: arudha `house_d1` behaved as 0-indexed sign/house (had to cross-reference
to realize house_d1=10 ≠ 10th house); graha positions are 1-indexed houses — mixed semantics.
FABLE CORROBORATION (from census receipts already in-context, chart 482012f1, Aries lagna):
ARUDHA_A1 house_d1=9 sign=Capricorn (true house from lagna = 10) · A7 house_d1=10
sign=Aquarius (true = 11) — consistent with 0-indexed-house stored under a 1-indexed-named
key. A10 house_d1=12 sign=Aries longitude=0° fits NEITHER convention → possible additional
0°-cusp/wraparound defect. Exact semantics TBD by audit; the field is verifiably inconsistent
with its own name either way.
Blast radius: every consumer reading arudha houses gets wrong houses — audit whether Darpana
answers on arudha-touching questions consumed it; audit ALL fact categories for the same
mixed-indexing class (writers, serving, docs). Fix: single convention (1-indexed 1–12
everywhere), writer fix + chart-scoped rebuild + serving-contract doc + CI convention gate.
Root cause: TBD-PENDING-FABLE-PASS.

**EL-31 · EAV is the naive consumption path — entity-aggregated faces exist but are not
found/steered-to. [V→T, consumer-verified reproduction of the discovery thesis]**
Consumer symptom: had to write Python to reassemble Mars from hundreds of flat
`query_chart_facts` rows; asks for `query_planet(name)` / `query_house(n)` assembled objects.
Fable nuance (verified): aggregated faces EXIST — `shape=pivoted` on chart_facts,
`graha_portrait`, `chart_snapshot`, `bodha_chart_digest_get` — and the consumer never found
them. So this is (a) a discovery/steering failure (the naive path lands on raw EAV; nothing
routes to assembled faces — EL-26's thesis proven from the consumer side), PLUS (b) a real
gap: no single canonical `query_planet`/`query_house` fully-assembled-entity endpoint
(sign+house+nakshatra+dignity+shadbala+avastha+aspects in one object).
Fix direction: canonical entity endpoints; EAV tools' descriptions steer to them; tool_search
ranks assembled faces above raw EAV for entity-shaped queries.

**EL-32 · Identifier/naming standardization across subjects and tools. [V]**
Consumer symptom: mixed identifier styles — `MAR`/`MER`/`RAH_MEAN` vs `AMATYAKARAKA`/`LAGNA`
vs full names; forces guesswork, invites hallucination.
Fix direction: one canonical identifier scheme (full uppercase names), served everywhere;
aliases accepted on INPUT for compatibility, canonical on OUTPUT; convention documented in
the schema map (EL-34) + CI naming gate (naming-governance gate exists for code — extend to
served data identifiers).

**EL-33 · Active-dashas-at-date convenience face. [V, usability]**
Consumer symptom: full Vimshottari tree too heavy; wrote scripts to find what's active in a
range. Fable nuance: `ganita_dasha_periods_get(level,start,end)` already supports bounded
queries — discoverability failure again — but the ask is still right: a first-class
`active_dashas(date|today)` returning L1/L2/L3 lords + exact period bounds (across ALL
systems per DR-14, not just Vimshottari) is the correct convenience face. Cheap, high-value.

**EL-34 · Complete schema map / `get_database_schema`. [V — extends EL-08]**
Consumer symptom: valid categories/subjects unknown; category enumeration truncated at 2,000
rows alphabetically so whole categories were invisible; blind exploratory pagination wasted
calls. Fix direction: one tool serving the FULL map — every fact_category × fact_subjects ×
fact_keys with one-line meanings — mechanically generated from the DB (the same substrate as
EL-08's concept resolver + EL-03's domain ledger; one artifact can back all three).

**EL-35 · Inline astrological-context injection. [C→V, grounding quality]**
Consumer symptom: esoteric fields (22nd drekkana, tara_bala, KP sublords) served bare; schools
(Parashari/Jaimini/KP) interpret differently; asks for an `astrological_significance` string
or a definition tool. Fable nuance: `ref_classical_citation_get`/`ref_rules_search` exist
(discoverability again) but inline one-line significance on served rows — framework-tagged
("In KP, the 2nd-cusp sublord governs wealth accumulation") — is the right elevation; also
directly serves EL-29's composition quality.

**META (strengthens EL-26 root-cause hypothesis):** an independent, capable consumer-LLM
reproduced the discovery failure end-to-end — most of what it asked for EXISTS and was never
found. The corpus is not under-built; it is under-DISCOVERED, under-STEERED, and in one case
(EL-30) mis-labeled. Scorecard-style asks (its item 5) are already live (`assess_wealth`,
`judgment_query`, `bodha_domain_reading_get`) and went unfound — same lesson.

---

### Serving-session experience report (Fable, 2026-07-24 — first-hand working friction from live raw-MCP serving; ranked by priority, not by discovery order)

*Provenance: unlike EL-30–35 (native-relayed consumer report), every item below was hit first-hand
while composing a live wealth reading + muhūrta election over the Marsys-JIS MCP for chart
482012f1. Four items carry same-session **FABLE CORROBORATION** — re-run against the live server at
logging time, verbatim payloads quoted. The rest are reported symptoms awaiting the root-cause pass.*

#### P0 — broken surfaces (blocked or degraded the data itself)

**EL-36 · `graha_portrait` self-starves: the generic orientation digest consumes the budget, the
graha-specific rows serve EMPTY, and the receipt reports ✓. [T, flagship — highest single-fix
impact of this report]**
Symptom: the Venus portrait — the exact tool designed to answer "how is my Venus?" in one call —
returned every section with `rows: []` after `budget_exceeded_after_trim`, with its narration string
cut mid-sentence. Structure receipts, zero substance; Venus had to be reassembled from 6 other tools.
FABLE CORROBORATION (re-run 2026-07-24, chart 482012f1, `include:["position","dignity"]` — i.e. the
CHEAPEST possible variant): `content.position.rows: []` with `count: 9`; `content.dignity`'s
`operative_varga_rows`, `all_varga_rows` and `other_rows` all `[]` with `count: 56`. **65 rows
located, 0 served.** `verdict.narration` cut mid-word: `"In D9: debilitated (neecha) (Vi…[truncated
for budget]"`. The `orientation_context` digest is emitted in full ahead of it — 9,946 MSR signals,
entity_profiles for SATURN, JUPITER, BHAVA_12 and KETU, i.e. **not one Venus row** — plus full
convergence_domains and a 38-id grounding array. `trim_report` itself was trimmed 6 entries → 1
("full trim_report omitted to fit budget"), so the caller cannot even audit what was dropped.
Narrowing `include` does not help: the fixed-cost preamble is the whole problem.
Compounding truth defect (worse than the budget bug): `verdict.completeness` reports
`position: "✓"`, `dignity: "✓"` and `sections_populated: 2 / sections_requested: 2` while both are
empty, and `judgment_flags: []` — nothing raised. The §28.6 receipt vocabulary marks ✓ on *section
attempted*, not *rows served*. A consumer trusting the receipt concludes Venus was fully served.
Expectation violated: §N.6.2 (a trim protects the densest, most-actionable layer FIRST — here the
entity-specific payload is the ONLY thing trimmed while generic context behaves as hardFloor);
§N.6.3 (an honest empty is reported via flags, never as a populated-looking hollow envelope).
Suspected layer: response-budget section ordering / hardFloor assignment in the portrait packer,
plus completeness-receipt semantics. Cross-refs EL-07 (false confidence class), EL-11/EL-28
(budget), EL-46 (honesty layer trimmed).
Fix direction: entity payload declares `hardFloor` ABOVE `orientation_context`; orientation_context
becomes opt-in (or a digest-of-digest) on entity-scoped tools; `completeness` gains a distinct
`trimmed_empty` state separating served-✓ from trimmed-to-zero, with a mandatory judgment_flag;
trim_report is never itself trimmable. Root cause: TBD-PENDING-FABLE-PASS.

**EL-37 · `bodha_mechanisms_get` hard-fails on every call variant — SQL parameter-binding error;
the entire named-mechanism layer is unreachable. [T, dark capability]**
Symptom: every variant returns `error: bind message supplies 3 parameters, but prepared statement ""
requires 2`. The whole L2 Yantra layer — convergent dispositor chains, dispositor cycles,
house-lordship cycles, parivartana chains with valence + centrality — is unreachable; dispositor
topology had to be reconstructed by hand from raw facts.
FABLE CORROBORATION (re-run 2026-07-24, chart 482012f1, `limit:5`, no other filters):
`{"error":"error: bind message supplies 3 parameters, but prepared statement \"\" requires 2",
"is_error":true}`. Reproduces on the plainest possible call — this is not a filter-combination edge
case, the tool is 100% down.
Expectation violated: a registered, documented, CR-24-delivered capability is callable.
Note the compounding history: EL-13 already records that this same tool was not round-trippable
mid-session due to tool-catalog caching — it has never had a clean verified serving pass.
Suspected layer: query builder in the mechanisms handler (param array/placeholder count mismatch,
likely an ayanamsha or limit/offset param appended without a matching placeholder).
Fix direction: fix the binding; add a smoke test that CALLS every registered tool with minimal args
on chart 482012f1 in CI (a tool that has never returned 200 in production is the cheapest possible
class of defect to gate). Root cause: TBD-PENDING-FABLE-PASS.

**EL-38 · `ganita_structural_get facet=argala` times out at its default limit — a classical wealth
layer went entirely unserved in a wealth deep-dive. [V→T]**
Symptom: the call timed out; argala on the 2nd/11th (a load-bearing Jaimini wealth layer) was
absent from the reading.
FABLE CORROBORATION (re-run 2026-07-24, chart 482012f1, `limit:5`): returns **instantly** with
two-pass-verified rows from `argala_natal_matrix` + `virodha_argala_natal_matrix`. So the facet is
not broken — the **default `limit` of 25000 over a per-varga × per-sign × per-offset matrix** is.
The returned rows also expose two secondary problems worth logging here: (a) every sampled row has
`fact_value_num: 0` under `unit: argala_score` — either genuinely no argala or an EL-40-class
uniform-value defect, indistinguishable to a consumer; (b) rows are keyed `from_sign_10_offset_1`
per varga (`D1_SIGN_10`, `D2_SIGN_10`, `D33_SIGN_10`) — a **sign-indexed matrix with no
house-from-lagna resolution**, so "argala on the 2nd/11th" is not answerable without client-side
arithmetic (same class as EL-47).
Expectation violated: a served facet returns within budget at its own default; a wealth question
reaches the argala layer without the consumer knowing to pass a limit.
Fix direction: bound the default (paginate + facet counts) rather than dispatching the full matrix;
serve argala pre-resolved to houses-from-lagna with a `argala_on_house` shape; if the zeros are
real, say so with an `empty_reason`-style disclosure rather than serving 25,000 silent zeros.
Root cause: TBD-PENDING-FABLE-PASS.

**EL-39 · `ref_planet_position_get` serves TROPICAL only — forces client-side ayanamsha arithmetic
in a sidereal instrument, and mis-derives nakshatra. [T, B.10 violation surface]**
Symptom: determining that transit Venus was debilitated in Virgo — the decisive fact of the muhūrta
reading — required manual Lahiri subtraction on the served longitude. Client-side arithmetic on
chart values is precisely the B.10 risk the instrument exists to eliminate.
FABLE CORROBORATION (re-run 2026-07-24, Venus @ 2026-08-15): `{"tropical_longitude":188.565106,
"sign_number":7,"degree_in_sign":8.565,"nakshatra_number":15,...}` with
`"ayanamsha_id":"tropical"`. Sign 7 = tropical Libra; sidereal Lahiri is Virgo (the wealth-relevant
debilitation). **Additional finding beyond the report:** `nakshatra_number: 15` is derived from the
TROPICAL longitude. Nakshatra is an inherently sidereal division — this field is not merely
un-converted, it is *wrong under every ayanamsha the instrument supports*, and is served with no
warning label.
Expectation violated: the sidereal instrument never hands a consumer a number it must convert; §N.5
(L1 is the authority — a consumer deriving sidereal positions client-side IS the drift the standard
forbids, one layer out).
Fix direction: `ayanamsha_id` parameter (defaulting to `lahiri_chitrapaksha`, NOT tropical) serving
sidereal longitude + sign + degree + nakshatra + pada directly; keep `tropical_longitude` as an
explicitly-labelled extra; suppress or re-derive `nakshatra_number` under tropical rather than
serving a wrong one. Root cause: TBD-PENDING-FABLE-PASS.

**EL-40 · `composite_dispositor_strength` returns 0.875 uniformly for all 9 grahas — zero
discriminating information served as fact. [T, data integrity]**
Symptom: the field carries an identical value for every graha, making it useless for ranking and
actively misleading if consumed as a strength measure. Either a computation defect (a constant
short-circuit) or a placeholder shipped as a computed value.
Expectation violated: B.10 — no fabricated computation; a placeholder must be disclosed as one, not
served as a number with a name that implies derivation. Same shape as EL-30 (a field whose served
value contradicts its own name).
Fix direction: audit the writer; either compute it properly with a documented formula or withdraw
the field / mark it `null` with a reason. Screen ALL numeric L2 fields for the uniform-value class
(a cheap CI check: any composite/score field whose distinct-value count across grahas is 1 fails).
Root cause: TBD-PENDING-FABLE-PASS.

**EL-41 · Silent category absence — requested categories that return nothing are omitted with no
`empty_reason`. [T, direct recurrence of the EL-07 class]**
Symptom: `saham` + `sensitive_point` were requested alongside `special_lagna` from the special-lagnas
tool; only `special_lagna` rows came back, with **no empty_reason for the two missing categories**.
Dhana Saham is directly wealth-relevant; the consumer cannot distinguish "not computed" from "not
served" from "wrong category name" — the exact ambiguity that produced the S4-03 Gulika veto.
Expectation violated: the instrument's own honesty discipline (§N.6.3 / the `empty_reason` pattern
the consumer explicitly praised elsewhere in this same session — see EL-60). A per-category receipt
is mandatory when a call names categories explicitly.
Cross-refs: EL-07 (absence protocol), EL-08 (concept resolver), EL-19 (sahams genuinely
REACHABLE-BUT-EMPTY — so in THIS instance the honest answer is "computed: never"; the defect is that
the consumer could not learn that).
Fix direction: every multi-category tool returns a per-requested-category receipt
(`served` / `empty_with_reason` / `unknown_category` + alias suggestion); no requested category may
be silently dropped from the response shape. Root cause: TBD-PENDING-FABLE-PASS.
> **PARTIAL-CLOSE annotation (SATYA-ŚEṢA campaign, 2026-07-25).** This is the direct recurrence
> class this item names as EL-07's sibling, and the same live probe that re-confirmed EL-07's
> residual (SATYA_SHESHA BRIEF §1) re-confirmed this one too: `ganita_chart_facts_get`'s
> keyword-filtered path bare-empties with no per-category receipt of any kind. SATYA-ŚEṢA W1
> (Builder B1) closed the bare-empty shape across `query_chart_facts`/`ganita_chart_facts_get`'s
> keyword/subject/category/sign/nakshatra filter paths (the same fix direction this item and EL-07
> both call for), plus a CI probe iterating the Phase-0.7 census's 46 concepts so no future bare
> empty ships unnoticed. PR pending — item implemented in the same SATYA-ŚEṢA campaign cycle, see
> `SATYA_SHESHA_LEDGER.md` for the final PR number.

#### P1 — response architecture: size, shape, consumability

**EL-42 · Response-budget enforcement is not uniform — core tools blow chat-consumable limits.
[T for small clients; acceptance test for EL-28]**
Symptom: `ganita_chart_facts_get` (68–84 KB) and `assess_wealth` (118 KB) exceed chat-consumable
limits, forcing file-save + scripted parsing mid-reading. Meanwhile `graha_portrait` (EL-36) is
budget-enforced so aggressively it serves nothing — the same machinery is simultaneously absent on
the heaviest tools and pathological on a light one.
Expectation violated: EL-28's mandate — the server adapts, never errors; and every tool is budgeted
by one consistent mechanism.
Fix direction: response_budget applied to ALL tools with per-tool worst-case caps asserted in CI on
chart 482012f1 (the gate EL-11 already specifies); pair it with EL-36's ordering fix so "budgeted"
never means "hollow". Direct acceptance test for EL-28.
> **PARTIAL-CLOSE annotation (SATYA-ŚEṢA campaign, 2026-07-25).** Confirms this item's own framing —
> "absent on the heaviest tools" — was still true for the kala/gochara family specifically at the
> SATYA-ŚEṢA G0 baseline: `gochara_forecast_get` served 69,404 chars and `kala_windows_get` served
> 50.2 KB, neither trimmed (SATYA_SHESHA BRIEF §1 item 3; same evidence cross-referenced at EL-11
> above). SATYA-ŚEṢA W3 (Builder B2) closed this for the kala/gochara family by wiring
> `response_budget.ts` to `gochara_forecast_get`, `kala_windows_get`, `kala_bundle_get` and any
> family member whose worst-case exceeds the default ceiling, with the budget-census CI gate
> extended to cover them — narrowing but not fully closing this item's "not uniform" framing (other
> tool families beyond kala/gochara remain unaudited by this campaign). PR pending — item
> implemented in the same SATYA-ŚEṢA campaign cycle, see `SATYA_SHESHA_LEDGER.md` for the final PR
> number.

**EL-43 · EAV verbosity — served row counts are multiples of the true table size, with provenance
boilerplate repeated per row. [V]**
Symptom: special lagnas = 49 rows for what is a 7-row table; tara bala = 39 rows; each row carries a
full repeated provenance/citation block. Token cost is dominated by boilerplate, not information.
Fix direction: pivoted compact shapes as the DEFAULT for entity-shaped and table-shaped data
(`shape=pivoted` already exists on chart_facts — EL-31 again: it exists and is not the default or
steered-to); provenance envelope emitted ONCE per response with per-row references into it.
Cross-refs EL-31, EL-42.

**EL-44 · `assess_wealth` returns a signal skeleton, not a verdict — the narrative was authored
entirely client-side. [V, direct instance of EL-29]**
Symptom: top signals carried `composite_score: null`; summaries truncated; machine-key text served
raw as prose (`value_text=Saturn_in_H7`); and two lens blocks were duplicated with identical signal
lists. The wealth narrative in the delivered reading was written by the serving agent, not by the
instrument — exactly the dependency EL-14 forbids.
Expectation violated: EL-14 (completeness must not depend on answerer intelligence) + EL-29
(established reading structure served, not improvised).
Fix direction: a plain-language verdict layer (3–5 sentences, every clause carrying fact_ids) on top
of the signal skeleton; null composite_scores investigated (are they uncomputed or trimmed?);
machine keys humanized at serve time; lens de-duplication.

**EL-45 · `assess_wealth` omits the classical wealth vargas — `varga_analysis` is a stub. [V, direct
instance of EL-01/EL-26 in the flagship wealth tool]**
Symptom: the dedicated wealth assessment ships `varga_analysis` as a stub reading "available via
chart_facts_query" — so D2 (Hora), D11 (Labha) and Indu Lagna, the three most classical wealth
instruments in the corpus, are not consumed by the wealth tool. They were bolted on manually.
Expectation violated: a domain tool consumes its domain's own canonical layers by default —
this is EL-01's concept-consumption gap appearing INSIDE the purpose-built assessor, and EL-26's
"computed, stored, reachable, never planned" appearing one layer up.
Fix direction: `assess_wealth` consumes D2 / D11 / Indu Lagna / per-varga AV directly; no domain
assessor may ship a "see other tool" stub for a layer classical to its own domain (CI gate against
the EL-03 per-domain concept ledger once it exists).

**EL-46 · `judgment_flags` are budget-trimmed — the honesty layer has the WORST possible trim
priority. [T, §N.6 violation]**
Symptom: judgment flags observed truncated with `[truncated for budget]`; in the EL-36 re-run,
`reading_contract`, `attribution.note` and the trim_report itself were likewise cut.
Expectation violated: §N.6.2/§N.6.3 explicitly — the flags array IS the mechanism by which an honest
gap is reported; trimming it converts an honest response into a silently-confident one. Nothing in
the envelope should outrank it.
Fix direction: `judgment_flags`, `empty_reason`, `epistemic`, `coverage` and `trim_report` are
hardFloor-protected and excluded from trimming entirely (they are O(bytes), not O(rows)); a response
that cannot fit them is a response that must shed rows instead.

**EL-47 · Divisional facts serve sign but NULL house — house-from-varga-lagna computed client-side.
[V, B.10 exposure]**
Symptom: D11 rows gave sign with `house: null`; houses were derived client-side from the D11 Lagna
— arithmetic the instrument should own, with error risk on every consumer. (EL-38 shows argala has
the same shape from the other direction: sign-keyed, house-unresolved.)
Expectation violated: §N.5 / B.10 — the consumer never re-derives what L1 can compute.
Fix direction: serve `house_from_varga_lagna` on every divisional fact row, server-side, with the
convention named explicitly (1-indexed 1–12 — and settle it jointly with EL-30's indexing audit so
one convention lands everywhere at once).

#### P2 — missing capabilities that would have directly elevated this reading

**EL-48 · `chart_snapshot` serves D1 (+optional D9) only — no arbitrary-varga snapshot. [V]**
Symptom: D2, D10 and D11 each required raw fact pulls plus manual grid assembly. A single
`vargas:["D2","D10","D11"]` parameter would have answered three of this session's requests in one
call each.
Fix direction: `vargas[]` parameter on chart_snapshot, budget-layered per varga. Cheap, high-value;
directly serves EL-45 and EL-61.

**EL-49 · No direct `panchanga_get(date, location)` — panchāṅga is reachable only through muhūrta
windows, and is incomplete. [V]**
Symptom: the `panchanga_daily` table exists but is reachable only via 2-day muhūrta windows that
serve **start-date panchāṅga only** — evaluating Friday Sep 18 inside a Sep 17–19 window required a
second targeted call. Missing outright: karana, sunrise/sunset, and horā timing — the Venus horā in
the delivered election was approximated from hedged sunrise estimates (B.10 exposure).
Expectation violated: a computed daily table is directly addressable; and the FORENSIC anchors
themselves include karana — a consumer cannot reach for today what the birth chart is verified on.
Fix direction: first-class `panchanga_get(date, location)` serving all five limbs + karana +
sunrise/sunset + horā boundaries; muhūrta windows serve per-day panchāṅga for every day in range,
not just the start date.

**EL-50 · Muhūrta engine — four capability gaps, all hit inside a single election query. [V→T for
elections; the engine ranked personally-adverse windows first]**
Symptom, itemized:
  (a) **No `spiritual` / `remedial` / `initiation` activity_type** — a japa initiation had to be
      scored as "general", the least-specific rule set available.
  (b) **Ignores the native's own Tāra Bala / Chandra Bala baselines** — its #1 window (Aug 26–28)
      was **Vadha tārā** for this Moon, and its Purva Ashadha window was **Pratyak**. Personally
      adverse windows ranked top. The chart-specific data exists; the elector doesn't consume it.
  (c) **Does not check the target graha's transit condition** — no window flagged that Venus was
      debilitated for the whole of August. For a graha-specific election this is the single most
      important factor, and it was caught only via separate ephemeris calls (see EL-39).
  (d) **No horā / sub-day resolution**, and window timestamps are UTC-midnight for IST panchāṅga
      days — semantically ambiguous about which day is actually meant.
Expectation violated: an election is by definition native-specific and target-specific; a generic
tithi/nakshatra filter is the market-alternative product, not the instrument (EL-26's "mediocre as
the other market alternatives", inside the timing layer).
Suspected layer: `kala_muhurta_get` scoring inputs (chart-baseline join absent; transit-condition
join absent; activity-type taxonomy incomplete; timezone/resolution contract).
Fix direction: (a) extend the activity taxonomy with classical grounding; (b) join tāra/chandra bala
from the native's own chart and make an adverse tāra a disqualifier or an explicit flag, never a
silent top rank; (c) accept `target_graha` and gate on its transit dignity/combustion/retrogression;
(d) horā-resolution windows with IST-anchored day boundaries. Cross-refs EL-15/EL-16 (timing layer),
EL-53. Root cause: TBD-PENDING-FABLE-PASS.

**EL-51 · Remedy engine serves a fraction of its own catalog, and its contraindication logic is
text, not verdict. [V]**
Symptom: the chart-scoped engine served **3 prescriptions against a catalog of 25** (homa, yantra,
vrata, gemstone families absent from the chart-scoped output). The gemstone contraindication logic
(maraka lordship) exists as catalog TEXT but is not applied as a computed verdict — that reasoning
was done client-side, on the single remedy class where getting it wrong is most consequential.
Self-disclosed residuals persist: `associated_doshas_array` and INR cost are NULL chart-wide.
Expectation violated: EL-01 concept-consumption inside the remedy layer; and a safety-bearing
contraindication is a computed gate, never prose the consumer must interpret.
Fix direction: chart-scoped engine consumes the full catalog with per-class reasons for exclusion;
maraka/contraindication evaluated as a deterministic verdict per gemstone with citation;
backfill the two NULL fields or disclose them as EL-19-style honest gaps.

**EL-52 · Classical corpus OCR quality — the best content in the system is archaeology, not
serving. [V]**
Symptom: the decisive BPHS Ch.47 Venus-maraka passage was buried in OCR noise
("3Tr?Ctrqqqad EI€TITfEfrffTq"). The corpus sweep returns rows a consumer must decipher.
Expectation violated: B.3 derivation-ledger + the citation discipline assume a citation is
READABLE; an unreadable citation is functionally an uncited claim.
Fix direction: clean + structure the corpus rows (verse reference · clean Devanagari · clean
translation · tagged prescription/rule), OCR-confidence scored, low-confidence rows flagged rather
than served bare. This converts existing high-value content into serving without new computation —
and directly serves EL-35's inline-significance ask.

**EL-53 · Close the muhūrta→prediction loop — elections are not filable as falsifiable
predictions. [V, mission-level]**
Symptom: the elected initiation date is a prediction (election quality → observed outcome) and
there is no path to file it into the prospective ledger.
Expectation violated: §A — time-indexed, testable, correctable. Elections are the fastest-cycling
falsifiable output the instrument can produce, and they currently evaporate.
Fix direction: `mimamsa_outcome_record`-compatible election filing — elected window + predicted
quality + the factors it scored on, closable against observed outcome; extends the L5 calibration
mission to elections (a whole new evidence stream at near-zero build cost).

**EL-54 · LEL backfill workflow — the model is un-backtested and there is no intake surface. [V,
biggest epistemic gap with the cheapest fix]**
Symptom: wealth retrodiction returned EMPTY — no logged events to retrodict against. The L5
calibration layer is sealed in STRUCTURAL mode by design, but it stays there without data.
Fix direction: a guided intake ("log these 3–5 event types with dates") that converts an hour of the
native's time into the calibration substrate the entire L5 layer is waiting on. Cross-refs EL-58
(stale open predictions have nothing to auto-close against for the same reason).

#### P3 — synthesis intelligence (what would make readings acharya-grade by default)

**EL-55 · Salience ranking overweights exotic micro-vargas — D54/D150/D8 dignity states ranked above
load-bearing D1 facts. [V, ranking integrity]**
Symptom: top wealth-lens signals were micro-varga dignity states, ranked above D1 facts that
actually carry the reading.
Expectation violated: classical weight — the shodasavarga hierarchy is not flat, and a ranking that
treats D150 as peer to D1 is not acharya-grade whatever its arithmetic.
Fix direction: a documented varga-weight term in the class priors (deterministic, cited, NOT tuned);
version the priors so the change is auditable. Cross-refs EL-20 (serving-rank residuals).

**EL-56 · Cross-ayanamsha duplication in discoveries — the same pattern × 5 ayanamshas served as 5
separate discoveries. [V; the mirror-image of EL-27]**
Symptom: 15 near-identical distributional-anomaly rows were served as distinct findings — noise
presented as breadth.
Note the pairing: EL-27 asks for ayanamsha VARIATION to be turned into signal; this asks for
ayanamsha AGREEMENT to stop being served as volume. They are one mechanism — collapse the family to
one finding, and carry the cross-ayanamsha agreement count as a **confidence field on that finding**.
Building EL-27 correctly fixes EL-56 as a side effect; fixing EL-56 with a naive dedup would destroy
EL-27's signal. Flagging the coupling explicitly for the root-cause pass.
Fix direction: family-collapse across ayanamsha with `ayanamsha_agreement: n/6` served as the
confidence term (the E-6 family_aggregation machinery already exists for same-family atoms — extend
its key to include ayanamsha).

**EL-57 · Contradiction surface not domain-filtered — a wealth assessment served contradictions
tagged career/character/health. [C→V]**
Symptom: the contradiction section of a wealth reading contained no wealth contradictions.
Fix direction: domain filter on the contradiction surface with an honest "no contradictions in this
domain" empty_reason (which is itself a finding worth stating).

**EL-58 · Prediction lifecycle hygiene — a 2011 gain window still `open` in 2026. [V, ops]**
Symptom: stale prospective rows never auto-matched or closed; the ledger's open set is not a
meaningful queue.
Fix direction: auto-match/close against LEL on build; anything past its window with no outcome moves
to `lapsed_unobserved` (which is itself calibration data, not a mess to hide). Cross-refs EL-54,
EL-24 (build-state truthfulness).

**EL-59 · Inconsistent rank semantics across tools — Venus is `weakest_rank_in_chart: 5` in the
remedy resonance and weakest-of-7 by shadbala in the digest. [V, trust]**
Symptom: two tools, two rank vocabularies, same graha, contradictory answers with no disambiguating
label. (The EL-36 re-run shows the digest side: `weakest_graha: "Venus"`, sourced
`shadbala_total_min (BPHS Ch.27; CR-55 fix)` — so the digest is grounded and labelled; the remedy
surface's rank 5 is neither.)
Expectation violated: EL-32's canonical-vocabulary principle applied to derived RANKS, not just
identifiers.
Fix direction: one rank vocabulary served everywhere, each rank carrying its basis label
(`rank_basis: shadbala_total`) and its population size; no bare `rank: n`.

**EL-60 · More of what worked — accrete `reading_notes_get` automatically, and pair honest-empty
patterns with a coverage attestation. [P, amplify]**
What worked (logged deliberately — the register should record what to PRESERVE under change):
`reading_notes_get` (the CR-38/71/80 verified appendix) was the single highest-value-per-token
response of the session. The honest-empty patterns built real trust — especially gochara's "clean
window, not a fabricated all-clear".
Elevation: (a) accrete reading notes automatically per domain per session so the appendix compounds;
(b) pair every coverage claim with a **build-coverage attestation** so "no adverse windows" is
provably *checked* rather than merely *unswept* — an honest empty and an unrun sweep currently read
identically to a consumer, and the difference is the whole trust claim. Cross-refs EL-15/EL-16 (the
sweep whose completeness this attestation would report), EL-41.

**EL-61 · Domain-dossier bundling mode — ~25 calls across 20+ tools to assemble ONE reading. [V→T,
flagship product shape; the natural home for EL-01/EL-02/EL-26/EL-29/EL-31]**
Symptom: this session's reading required roughly 25 calls across 20+ tools, with the serving agent
performing all orchestration, all assembly, and all narrative composition.
Expectation violated: "complete astrological reading" should be a SERVED product, not an
agent-assembled one — EL-14 in its strongest form. Every gap in this report compounds here: an
agent that must make 25 calls will under-consume (EL-01), will find only what it already knows to
look for (EL-26/EL-31), will compose while retrieving (EL-29), and will blow its context (EL-42).
Fix direction: a composable `dossier(domain=wealth)` orchestrating snapshot + lords + yogas +
vargas + special lagnas + AV + timing + remedies into ONE budgeted, layered, receipt-bearing
response — the floor compiled AND executed server-side (EL-02), delivered in the established
reading structure (EL-29), paginated for small clients (EL-28). This is the single item that, built
well, converts the largest number of other EL items into acceptance tests of itself.

*(native continues below)*

---

## SECTION H — SATYA-ŚEṢA campaign additions (2026-07-25)
*Appended by Builder B4, SATYA-ŚEṢA campaign, per `SATYA_SHESHA_BRIEF_v1_0.md` W5. This section is
purely additive — nothing above this line in the register was edited or removed. See also the
partial-close annotations inserted in-place immediately after EL-07, EL-11, EL-24, EL-41, EL-42
above (each block-quoted and timestamped so it reads as a clearly-separate append, not a rewrite
of the original entry).*

**EL-62 · Category-coverage attestation absent on scanning tools — execution coverage ≠ category
coverage. [T, flagship — the S4-05 mechanism]**
Symptom: a scanner/sweep-backed tool can be 100% complete over the universe of event classes it was
built to sweep, and STILL never have looked at the domain a caller actually asked about — and both
states read identically to a consumer as "clean." Concretely: `gochara_forecast_get`'s T-2 sweep
completed 303/303 substeps (genuine, verified, full execution coverage) but its event-class universe
is `career_advancement` + `marriage` only — **zero health event class, and no coverage/attestation
field anywhere in the response** that would let a caller learn this (SATYA_SHESHA BRIEF §1, "Verified
STILL BROKEN" item 2, live probe 2026-07-25). A health-timing question routed through this tool has no
way to discover it queried the wrong universe.
Expectation violated: EL-60's own coverage-attestation elevation ("pair every coverage claim with a
build-coverage attestation so 'no adverse windows' is provably checked rather than merely unswept")
— EL-62 is the concrete, second-veto-scale instance of the gap EL-60 flagged as a risk, now confirmed
live and confirmed as the direct mechanism behind a veto-grade failure, not a hypothetical.
Evidence: **S4-05** (UAT-DARPANA's most severe finding — see `FABLE_HANDOFF_SUMMARY.md`) — asked "Is
there a rough patch coming for my health?", the answerer ran the gochara hazard scan, got nothing
(because health was never in the swept universe), and served "clean — no adverse window flagged
across roughly the next three years" as an affirmative clearance. The health-capable instrument
(`kala_windows` domain=health) carries a two-pass-verified adverse DOSHA window
**2029-07-22 → 2030-02-20, peak 2029-11**, never surfaced. Plus today's live probe confirming the
zero-coverage-field state persists as of 2026-07-25 (SATYA_SHESHA BRIEF §1).
Fix direction: W2 (SATYA-ŚEṢA campaign) — every scanner/sweep-backed tool carries in EVERY response a
mechanically-derived `coverage: {event_classes_covered, domains_not_covered, universe_source,
sweep_completeness}` block, plus a server-side refusal rule: a request naming/filtering a domain
outside the covered set gets a `not_covered: {domain, cross_pointer}` shape naming the capable
instrument, never a bare empty presented as a scan result. PR pending — implemented in the same
SATYA-ŚEṢA campaign cycle, see `SATYA_SHESHA_LEDGER.md` for the final PR number.
Severity: **T** (Trust-breaking) — this is the data-layer root of S4-05, the most severe finding in
the UAT-DARPANA campaign.

---

## Template for new items

```
**EL-nn · <short title>. [severity T/V/C/P]**
Symptom: <what you saw — verbatim examples if possible, which client/surface, which question>
Expectation violated: <what should have happened>
Evidence/where: <session, file, screenshot — anything>
Suspected layer: <guess ok / leave blank>
Root cause: TBD-PENDING-FABLE-PASS
Fix direction (initial): <optional>
```

---

## Disposition (set at the future Fable root-cause pass)

When the native declares the register complete enough, a dedicated Fable pass will: (1) verify
each item against live evidence; (2) collapse duplicates and identify the true root-cause
clusters (current hypothesis: FOUR — consumption-contract enforcement [A], truth/verification
machinery [B+F], serving-envelope adaptation [C], timing/computation completion [D+E]);
(3) map every EL to a campaign lane with gate metrics; (4) produce the consolidated
elevation-campaign brief (working name: SATYA-KAVACA + PŪRṆA-GRAHAṆA). Until that pass, this
register only ACCUMULATES — no item is closed here.
