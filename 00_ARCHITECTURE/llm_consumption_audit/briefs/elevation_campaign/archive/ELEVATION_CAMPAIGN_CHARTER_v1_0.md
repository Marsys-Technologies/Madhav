---
artifact: ELEVATION_CAMPAIGN_CHARTER (working name SATYA-KAVACA + PŪRṆA-GRAHAṆA)
canonical_id: ELEVATION_CAMPAIGN_CHARTER
version: 1.0
status: READY-FOR-EXECUTION — governing charter for the autonomous overnight elevation run
created: 2026-07-24
author: >
  Fable (Cowork planning session, 2026-07-24) — root-cause pass over ELEVATION_REGISTER v1.1
  (EL-01..EL-61) with live-server corroboration + code-level grounding, for autonomous
  execution by a Claude Code agent swarm on the native's machine.
classification: CLAUDECODE_BRIEF — autonomous swarm execution charter (Conductor reads this first)
mode: FULLY AUTONOMOUS · overnight · no human intervention · sub-agent swarm · worktree-isolated
register: 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md (v1.1 — READ IT IN FULL
  at run open; this charter is the root-cause + execution layer OVER it, not a replacement)
model_policy: base=SONNET for all builders · OPUS for Conductor/Verifier/Native-Proxy/Goal-Keeper
  and the lanes marked [OPUS] · NO Fable/other models · escalate any lane to Opus after 2 failed
  verify cycles or when authoring classical rules / writer math
native_rulings (this run's authority level — given in the 2026-07-24 Cowork session, explicit):
  - Execution vehicle: Claude Code on the native's machine, overnight, fully autonomous.
  - Risk appetite: FULL — may deploy to production (amjis-mcp / sidecar / platform) and run
    chart-scoped rebuilds on the prod DB. Verifier confirms against the LIVE MCP surface.
  - Scope: FULL register, tiered — everything autonomous-executable is executed; items needing
    the native's own input become prepared packets/intake surfaces (nothing skipped, nothing
    fabricated).
  - DONE requires the dedicated Verifier agent's independent confirmation — a builder's own
    claim is never sufficient.
  - A dedicated Native-Proxy agent replaces the human for every overnight decision (charter §6);
    the native ratifies its ledger in the morning.
relevant_memory (autonomy precedents + scars — all previously ratified):
  - CLAUDECODE_BRIEF_RETRIEVAL_AUTONOMOUS_SWARM_CHARTER_v1_0.md (the proven overnight-swarm
    pattern this charter extends: Conductor/Human-Proxy/Goal-Keeper/Auditor, snapshots,
    keep-retrying-with-rollback)
  - 00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (role taxonomy + gates; §J autonomous
    amendment precedent)
  - feedback_ac_must_verify_target_environment (prod-verify, never worktree-complete)
  - snapshot-before-rebuild discipline; reverse-citation-before-delete; degenerate-distribution guard
  - CURRENT_STATE v6.41 precedent: "Sonnet-coordinator/Opus-step-up parallel swarm" worked
---

# SATYA-KAVACA + PŪRṆA-GRAHAṆA — Elevation Campaign Charter v1.0

> **What this is.** The single governing document an overnight Claude Code Conductor reads to
> execute the ELEVATION_REGISTER (EL-01..EL-61) end-to-end: fix the broken surfaces, make every
> response honest and budget-shaped, close the deterministic-computation gaps, wire the
> consumption contract, and hand the native a verifier-confirmed, evidence-backed morning report.
> The register stays the item-of-record; this charter adds (§2) the root-cause clusters, (§3) the
> code-grounded defect dossiers, (§4–§8) the swarm/verification/execution machinery, and (§12)
> the complete EL→lane coverage matrix. **An EL item is CLOSED only when the Verifier confirms
> it against the live production MCP with before/after evidence.**

## §0 — Kickoff (how the native launches this)

1. Open Claude Code at the repo root (`/Users/Dev/Vibe-Coding/Apps/Madhav`) with bypass
   permissions and prod credentials available (gcloud auth, `DATABASE_URL`, deploy rights).
2. Point the session at THIS charter (root `CLAUDECODE_BRIEF.md` points here).
3. The Conductor reads, in order: this charter → `ELEVATION_REGISTER_v1_0.md` (v1.1, full) →
   `CLAUDE.md` §N (build standards) → `CURRENT_STATE_v1_0.md` §2 (v6.41 open items) →
   `00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` (roles) — then takes the run-start
   snapshot (§8.1) and drives the wave DAG (§7) to close.
4. The native goes to sleep. The morning report (§11) is the wake-up artifact.

**Session scope declaration (protocol §F):**
- `may_touch`: `platform/src/lib/retrieval/**`, `platform-mcp/**`,
  `platform/python-sidecar/**`, `platform/migrations/**` (NEW migrations only),
  `platform/scripts/**`, `scripts/**`, `.github/workflows/**` (additive CI gates),
  `00_ARCHITECTURE/llm_consumption_audit/**`, `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`,
  `00_ARCHITECTURE/SESSION_LOG.md`, `CLAUDECODE_BRIEF.md` (status flip at close).
- `must_not_touch`: the FROZEN orchestrator core (`WriterBase` contract per
  `ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2` — new writers YES, contract changes NO);
  the sealed L5 calibration split; the 7 FORENSIC birth anchors and any stored L1 value they
  ground (writer FIXES that change wrong values are allowed — §3 Lane D — but never the anchor
  facts themselves); `LIFE_EVENT_LOG_v1_2.md` (no fabricated events — EL-54 builds an INTAKE,
  never content); `99_ARCHIVE/**`; `MACRO_PLAN`/`PROJECT_ARCHITECTURE` (no architecture change
  without the native); chart_id `362f9f17-…` (dead phantom — never write it).
- Canonical charts: `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek — primary),
  `1c826d5a` (Abhinandan — chart-agnostic verification). Every fix is verified on BOTH.

## §1 — Mission & definition of done

The register's target state: *"beyond-acharya AI supercomputer: complete in depth and scope,
seamless, superlative user experience."* This run's contribution, in one sentence per tier:

- **P0:** no tool in the estate is broken, silently wrong, or self-starving.
- **P1:** every response is budget-shaped, honest about what it dropped, and consumable by a
  200k-context client without file-save gymnastics.
- **P2:** the capabilities a real reading needed and lacked (sidereal transit service, direct
  panchāṅga, personal-baseline muhūrta, full remedy engine, varga snapshots, entity faces)
  exist and are served.
- **P3:** readings are acharya-grade BY DEFAULT — ranked sanely, deduplicated, domain-filtered,
  composed server-side (dossier), consumption-measured.
- **Loop:** elections and readings file into the falsifiable ledger; stale predictions close;
  the calibration mission gains its first standing data streams.

**DONE for the run** = §12's coverage matrix fully dispositioned: every EL either
`VERIFIED-CLOSED` (Verifier evidence block), `PREPARED-FOR-NATIVE` (packet/intake built +
verified), `NOT-REPRODUCED` (probe evidence attached), or `PARKED-HONEST` (bounded attempts
exhausted; residual + disclosure verified live). No fifth state exists. UAT-DARPANA's held exit
condition (CURRENT_STATE v6.41) should be materially unblocked by the P0/P1 closures.

## §2 — Root-cause map (the Fable pass over EL-01..61)

Seven true clusters. The register's four-cluster hypothesis (§Disposition) refines to:

**RC-1 · Envelope integrity.** The §N.6 budget machinery exists (`response_budget.ts`) but has
four concrete defects: (a) fixed-cost generic preambles (`orientation_context`) spend the budget
before entity-specific payloads — no hardFloor on the dense layer (EL-36); (b) completeness
receipts are computed PRE-trim and never reconciled — trimmed-to-zero serves as ✓ (EL-36/EL-07
class); (c) the last-resort string truncator eats honesty fields — narration, judgment_flags,
reading_contract, trim_report itself (EL-46); (d) enforcement is non-uniform — heavy tools
unclamped at 68–118KB while a light tool starves (EL-42, EL-11), no client budget negotiation
(EL-12/EL-28), EAV verbosity default (EL-43).

**RC-2 · Broken/wrong serving surfaces.** Straight code defects: SQL param-count bug killing the
whole mechanisms layer (EL-37 — root cause FOUND, §3.B); struct facet defaults sized for
internal dumps (EL-38); tropical-only ephemeris with tropical-derived nakshatra (EL-39);
mixed house-index semantics (EL-30); null varga houses (EL-47); uniform 0.875 placeholder
served as fact (EL-40); two rank vocabularies (EL-59); mixed identifiers (EL-32).

**RC-3 · Honesty machinery gaps.** Requested categories dropped without receipts (EL-41, plus
CURRENT_STATE B-1: `phala_predictive_anchors_get` silent-empty); no concept resolver so
empty-probe ≠ absent is undecidable (EL-08, EL-07's S4-03 class); no schema map (EL-34); no
serving-time claim-checker (EL-21); coverage claims without build-coverage attestation (EL-60b).

**RC-4 · Consumption/composition contract — THE FLAGSHIP.** Twice consumer-verified: the corpus
is under-DISCOVERED, under-STEERED, under-CONSUMED, and composed client-side. Floors compile but
don't execute (EL-02); no per-domain ledger/denominator (EL-03/04); planner blind to whole asset
families (EL-26: per-varga AV unplannable; EL-27: "ayanamsha" absent from the registry);
assessors ship stubs for their own domain's classical layers (EL-45); no verdict layer (EL-44);
no composition doctrine (EL-29); no served dossier (EL-61 — the umbrella). EL-01/05/06/14/23/31
are all faces of this one cluster.

**RC-5 · Deterministic-computation gaps.** Never-built math with classical grounding: sahams
(EL-19), per-dosha bhanga (EL-18), muhūrta personal-baseline/target-graha/horā scoring
(EL-50), direct panchāṅga service (EL-49), arbitrary-varga snapshots (EL-48), active-dashas
face (EL-33), remedy contraindication verdicts + full catalog (EL-51), corpus OCR structuring
(EL-52/35), salience varga-weights (EL-55), ayanamsha-agreement engine (EL-27+56 — one
mechanism: collapse family, serve agreement as confidence), contradiction domain filter (EL-57).

**RC-6 · Calibration-loop closure.** Elections not filable (EL-53); LEL empty so retrodiction
is untestable (EL-54 — intake only, native supplies content); stale open predictions (EL-58);
build-state truthfulness residuals (EL-24); ratification debt (EL-25); timing-sweep residuals
(EL-15/17 + CR-131 at 165/300 + gochara `DATABASE_URL` gap).

**RC-7 · Verification instrumentation.** The ability to SEE regressions: no
call-every-tool smoke gate (a tool was 100% down and no one knew — EL-37/13), no uniform-value
screen (EL-40 class), no budget census gate (EL-11), no consumption metric (EL-04), two-pass
grading not yet law in the standing battery (EL-10), four instrumentation tracks not captured
(EL-22), pass_looks_like blind spot (EL-23), precision-class claim errors unchecked (EL-09).

**Couplings the lanes must respect:** EL-27↔EL-56 (one mechanism — naive dedup destroys the
variation signal; build agreement-scoring, get dedup free). EL-61 depends on nearly every other
lane (schedule LAST). EL-30's indexing convention must be settled ONCE with EL-47/EL-38's
house-resolution work (one convention, one rebuild). EL-36's fix must land BEFORE the budget
census gate (K) locks numbers in.

## §3 — Grounded defect dossiers (per lane: evidence · fix spec · verification recipe)

Every lane follows the same internal gate sequence:
**G0 reproduce** (run the recipe against PROD; if not reproducible → `NOT-REPRODUCED`, attach
probe, stop) → **G1 fix** (worktree branch `elev/<lane>`) → **G2 test** (unit + typecheck +
the lane's regression additions) → **G3 merge+deploy** (Conductor-ordered) → **G4 verify**
(Verifier, against prod, both charts, before/after evidence into the run ledger).

### Lane A [OPUS] — Envelope & Truth (EL-36 · EL-42 · EL-43 · EL-46 · EL-11 · EL-12 · EL-28)

*Evidence (verified this session):* `graha_portrait` platform handler
(`platform/src/lib/retrieval/registry/layers/L2_bodha/graha_portrait.ts`) returns full rows and
computes its §28.6 completeness receipt at lines ~377–385 — PRE-trim. The MCP layer
(`platform-mcp/src/tools/registry_bridge.ts` + `register_p1_aliases.ts` — grep
`orientation_context`) prepends a generic chart digest (9,946-signal MSR summary, zero rows
about the requested graha) and then applies `finalizeMcpBudget`
(`platform-mcp/src/lib/response_budget.ts`): auto-detected sections carry no `hardFloor`, so
PASS 2 floors the entity arrays to 0 while the preamble survives; `truncateLongStringsInPlace`
then cuts `verdict.narration` mid-word and has been observed cutting `judgment_flags`,
`reading_contract`, `attribution.note`; the trim_report trimmed itself 6→1. Live repro
2026-07-24: Venus portrait `include:["position","dignity"]` → position `rows:[] count:9`,
dignity all arrays `[] count:56`, receipt `✓ ✓ 2/2`, `judgment_flags:[]`. Separately
`ganita_chart_facts_get` serves 68–84KB and `assess_wealth` 118KB (unclamped or
ceiling-too-high), while defaults serve EAV at 5–7× the true table size with per-row provenance.

*Fix spec:*
1. **Section priority inversion.** On every entity-scoped tool (graha_portrait, judgment_query,
   pact_query, …): entity payload sections declare `hardFloor:true` with real minKeeps;
   `orientation_context` becomes the FIRST-trimmed section (minKeep 0) and is `include`-gated
   (opt-in or digest-of-digest ≤2KB) on entity tools.
2. **Receipt truth.** After `finalizeMcpBudget`, reconcile the receipt against what is actually
   in the payload: any section trimmed to zero flips ✓ → `trimmed_empty` + a mandatory
   `judgment_flags` entry (`section_trimmed_empty:<name>`) + a drill pointer. The §28.6
   vocabulary gains that fourth state. A receipt that says ✓ over an empty array is the EL-07
   false-confidence class and is now a CI-testable invariant.
3. **Honesty-field immunity.** `judgment_flags`, `empty_reason`, `completeness`, `epistemic`,
   `coverage`, `trim_report` are exempt from `truncateLongStringsInPlace` and from PASS-2
   zeroing (they are O(bytes)); a response that cannot fit them must shed rows instead.
   trim_report is never itself trimmable below the 1-line summary WITH counts.
4. **Uniform enforcement.** Every registered tool passes through one budget path
   (`budgetMcpContent` or explicit sections) with a per-tool `maxKb` ledger in
   `descriptor_defaults.ts`; `ganita_chart_facts_get`/`assess_wealth` get explicit sections +
   pagination. Default ceiling sized to the smallest real client (~25k tokens ≈ Claude Code
   default `MAX_MCP_OUTPUT_TOKENS`); a `budget_kb`/`max_response_kb` REQUEST parameter overrides
   per-call (EL-12), larger for 1M clients — this parameter + documented client profiles
   (200k / 1M / Cowork / product UI) IS the EL-28 named capability, delivered with its own doc
   section in the schema map (Lane H) and acceptance tests (EL-11/12 as tests of EL-28).
5. **Pivot-first defaults (EL-43).** Table-shaped/entity-shaped surfaces default to
   `shape=pivoted`-style compact rows with ONE provenance envelope per response + per-row refs;
   raw EAV remains via explicit `shape=eav`.

*Verify:* (a) Venus portrait `include:["position","dignity"]` serves ≥9 position rows + the
operative dignity rows within budget, narration intact, receipt truthful; (b) the same call with
`verbosity:'concise'` keeps entity rows and sheds the preamble; (c) worst-case census: EVERY
tool called on 482012f1 fits its declared ceiling (this becomes Lane K's standing gate);
(d) `assess_wealth` ≤ default ceiling with layered sections; (e) a deliberately tiny
`budget_kb:8` call returns honest layered digest, never an error; (f) both charts.

### Lane B — Serving-surface repairs (EL-37 · EL-38 · EL-41 · EL-47-serving · EL-13 · +B-1)

*EL-37 evidence — root cause FOUND (this session):*
`platform/src/lib/retrieval/registry/layers/L2_bodha/query_mechanisms.ts` — the handler builds
`where` from filter params, then pushes the chain-circuit class array
(`classPriorityParam = $N`) into the SAME `params` array (lines ~128–129). `rowsSql` and
`facetSql` reference `$N`; the COUNT query (line ~159) is
`SELECT COUNT(*) … WHERE ${where}` — it references only the filter placeholders but is executed
with the full `params` (filters + class array). With the MCP default `ayanamsha_id` present:
3 params supplied, statement requires 2 — the exact live error. All three queries run in one
`Promise.all`, so the whole tool 500s on every call.
*Fix:* snapshot `filterParams = [...params]` BEFORE pushing the class-priority array; run the
count (and any where-only SQL) with `filterParams`. Add a regression test that calls the handler
with and without each filter. ~30-minute fix; the tool has never had a clean production pass
(EL-13 history) — Verifier must confirm live rows (chart 482012f1 has built `bodha_mechanisms`
rows per the L2 seal; if genuinely 0, the honest `empty_reason` path must serve).

*EL-38:* `get_argala.ts` is sane (default 500) but the MCP facet tool `ganita_structural_get`
(grep `facet` dispatch in `platform-mcp/src/tools/register_p1_ganita.ts` / the faceted
instrument) defaults `limit` 25000 over a per-varga × per-sign × per-offset matrix → timeout.
Fix: per-facet sane defaults (≤500) + facet counts + pagination; serve argala RESOLVED to
houses-from-lagna (`argala_on_house`, 1-indexed, convention per Lane D) with sign-matrix behind
`shape=matrix`; if a whole matrix is genuinely zero-valued, say so via `empty_reason`-style
disclosure (`all_zero: true`, distinct from unserved) — coordinate with Lane D's data audit.

*EL-41 + B-1:* every multi-category tool returns a per-requested-category receipt:
`{category, status: served|empty_with_reason|unknown_category, count, empty_reason?,
alias_suggestion?}`. No requested category may vanish from the response shape. Apply to the
special-lagnas tool (saham/sensitive_point silently dropped — live repro in register EL-41),
`phala_predictive_anchors_get` (CURRENT_STATE v6.41 B-1 silent-empty), then sweep every tool
taking a `categories[]` param (grep `categories` in layer files). Sahams specifically: until
Lane D2 lands, the honest receipt is `empty_with_reason: "saham category never computed —
EL-19/D2 in flight"`.

*EL-47 serving leg:* `get_divisionals.ts` / divisional fact serving computes
`house_from_varga_lagna` server-side (deterministic: varga lagna sign → count to graha sign),
1-indexed, convention-labelled. (Writer-side persistence = Lane D.)

*EL-13:* serve a `catalog_version`/`tools_changed_at` field on the server-info/health surface +
document the client-restart limitation in the schema map; if the MCP SDK supports
`notifications/tools/list_changed`, emit it on registration change.

*Verify:* mechanisms tool returns rows/honest-empty on both charts; argala facet answers
"argala on H2/H11" in one bounded call; special-lagnas call with 3 categories returns 3
receipts; divisional rows carry houses; regression battery green.

### Lane C — Sidereal ephemeris & panchāṅga service (EL-39 · EL-49)

*EL-39 evidence:* `L0_brahmagyan/query_planet_position.ts` proxies sidecar
`/brahmagyan/ephemeris/planet_position`, serves `ayanamsha_id:"tropical"`, and its own
DESCRIPTION instructs clients to "subtract Lahiri ayanamsha to get sidereal" —
institutionalized client-side arithmetic, the exact B.10 exposure. `nakshatra_number` is derived
from the TROPICAL longitude — wrong under every supported ayanamsha. Live repro: Venus
2026-08-15 → sign 7 (tropical Libra); sidereal Lahiri = Virgo (debilitation — the decisive
muhūrta fact the consumer had to hand-compute).
*Fix:* add `ayanamsha_id` param (default `lahiri_chitrapaksha` — sidereal-first instrument;
`tropical` allowed explicitly); sidecar route applies the ayanamsha (pyswisseph has it; the
engine already computes 6 ayanamshas for natal) and returns sidereal longitude/sign/degree/
nakshatra/pada + `tropical_longitude` as a labelled extra. Under `tropical`, suppress
nakshatra/pada or serve them sidereal-labelled — never a tropical-derived nakshatra bare.
Update BOTH alias registrations (`ref_planet_position_get`, `ref_planet_transit_get`) and any
other ephemeris-backed tool (grep `ephemeris_daily` consumers; `ref_aspects_at_time_get`,
`ref_ephemeris_year_get`, retrograde tools — audit each for the same tropical leak).
*EL-49:* first-class `panchanga_get(date, location?)` MCP tool over the existing
`panchanga_daily` table + sidecar compute for the missing limbs: all five aṅgas + karana +
sunrise/sunset + horā boundaries (IST-anchored, timezone-explicit ISO timestamps). Muhūrta
windows (Lane F) consume it per-day across their range instead of start-date-only.
*Verify:* Venus 2026-08-15 serves Virgo/lahiri + correct sidereal nakshatra; birth-date call
reproduces the 7 FORENSIC panchāṅga anchors (Shukla Tritiya / Ravivara / Shiva / Garaja) for
1984-02-05 Bhubaneswar — a free, absolute correctness oracle; Sep-18-2026 panchāṅga direct in
one call with sunrise + horā table.

### Lane D [OPUS] — Writer/data integrity + chart-scoped rebuild (EL-30 · EL-40 · EL-47-writer · EL-38-data)

*The indexing audit (EL-30) is the deepest truth item in the register.* Evidence: arudha
`house_d1` behaves 0-indexed under a 1-indexed name (A1 house_d1=9, sign=Capricorn, true
house-from-Aries-lagna=10; A7 house_d1=10/Aquarius/true 11; A10 house_d1=12/Aries/0° —
fits NEITHER convention → possible cusp/wraparound defect).
*Fix sequence (internally serial):*
1. **Audit:** mechanical scan of EVERY fact_category carrying a house-semantic field (grep
   `house` in writer emit paths under `platform/python-sidecar/pipeline/**` + sample rows per
   category from prod) → a convention table: category × field × observed convention × sample
   evidence. The A10/0° anomaly gets an explicit derivation check.
2. **Convention:** ONE ruling — houses are 1–12 from the (varga-appropriate) lagna, signs are
   1–12 Aries-origin, fields named `house_*` may never hold sign indices. Documented in the
   schema map (Lane H) + a CI convention gate (Lane K).
3. **Writer fixes** for every non-conforming category (arudha writer first), PLUS EL-47:
   divisional writers persist `house_from_varga_lagna`, PLUS EL-40: locate the
   `composite_dispositor_strength` producer (grep `composite_dispositor_strength` under
   `python-sidecar`; note `bo_upaya.py` CONSUMES it for remedy resonance — EL-59's bogus
   "rank 5" flows from here), audit the formula: if it's a real computation, fix it and document
   the formula in the citation_ref; if placeholder, either implement the documented convergence
   weight or WITHDRAW the category and serve `null`-with-reason (B.10 — no placeholder shipped
   as fact). Same audit screens ALL numeric L2 fields for distinct-count=1 across grahas
   (degenerate-distribution guard, becomes a Lane K CI screen).
4. **Chart-scoped rebuild** (delete-then-insert per §N.3) of affected categories for BOTH
   canonical charts via the FROZEN orchestrator (writers only, no contract change), then
   **downstream refresh**: any L2+ signal citing corrected facts (constituent_facts_array
   resolution per §N.5) must be rebuilt or flagged — run the MSR drift check from
   `MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md` after rebuild.
*EL-38 data leg:* determine whether the all-zero argala matrix is real (compute expectation:
Aries-lagna chart with 9 grahas CANNOT have all-zero argala on all houses — if stored zeros are
wrong, fix the argala writer and rebuild; if the sampled slice was atypical, document).
*Verify:* re-run the register's own corroboration probes: A1→10, A7→11, A10 resolved with
documented derivation; dispositor strengths show ≥3 distinct values across 9 grahas or the
category is withdrawn-with-reason; divisional rows carry correct houses (spot-check D9/D10/D11
against sign arithmetic); FORENSIC 7/7 still PASS post-rebuild; both charts; MSR resolution
clean.

### Lane D2 [OPUS] — Gaṇita completions: sahams + bhanga (EL-19 · EL-18)

New deterministic writer math, citations MANDATORY per B.3/B.10 — Opus authors, classical
sources named per rule, no invention. **Sahams (EL-19):** implement the classical Tājaka saham
set (Punya, Vidyā, Yaśas, Mitra, Mahātmya, Āśā, Samartha, Bhrātṛ, Gaurava, Pitṛ, Mātṛ, Putra,
Āyus, Karma, Roga, Kali, … — the standard ~16+ from Tājakanīlakaṇṭhī; day/night formula variants
included) in a `ga_*` writer extension writing the `saham` fact_category the census already
probes; Dhana Saham is the wealth-relevant first-check. **Bhanga (EL-18):** per-dosha
cancellation rules beyond NBRY for the well-attested set ONLY — Kuja/Manglik cancellation
conditions, Kemadruma bhanga, Shakata bhanga at minimum — each rule carrying its citation
(BPHS/Phaladeepika/Jātaka Pārijāta chapter-verse); doshas without attestable rules keep the
honest `bhanga_na_reason`. Both: chart-scoped rebuild both charts + serving through existing
tools (special-lagnas/sensitive-points tool picks up `saham`; firings surface picks up
per-dosha bhanga verdicts). *Verify:* saham longitudes recompute from the formula inputs
(lagna/graha longitudes already in L1) exactly; each bhanga verdict traces to its cited rule;
EL-41's saham receipt flips from `empty_with_reason` to `served`.

### Lane E — Assessors & ranking (EL-44 · EL-45 · EL-55 · EL-57 · EL-59 · EL-20 · EL-32)

`register_d8_assess_domain.ts` (assess_wealth et al.): (1) **verdict layer** — 3–5 plain-language
sentences, every clause carrying fact_ids, composed from the already-ranked signals
(deterministic template over graded terms, NOT a generative call — B.10); (2) investigate
`composite_score:null` on top signals (uncomputed vs trimmed — fix accordingly); humanize
machine-key text at serve time (`Saturn_in_H7` → "Saturn in the 7th house") via one shared
formatter (also EL-32's canonical-output pass: full uppercase names on OUTPUT, aliases accepted
on INPUT — extend the existing naming-governance gate to served identifiers); dedupe identical
lens blocks. (3) **EL-45:** replace the `varga_analysis` stub — assess_wealth consumes D2/D11/
Indu Lagna/per-varga-AV directly (rows exist — census A.7); rule: no domain assessor ships a
"see other tool" stub for a layer classical to its domain (Lane I's ledger makes this a CI
assertion). (4) **EL-55:** add a documented varga-weight term to
`ranking/priors_config.ts` class priors (shodasavarga hierarchy — D1 highest; classical
vimśopaka weights as the cited basis; version-bump priors, note in ranking_basis). (5) **EL-57:**
domain filter on the contradiction surface + honest "no contradictions in this domain" empty.
(6) **EL-59/EL-20:** ONE rank vocabulary — every served rank carries `rank_basis` +
population (`weakest_rank_in_chart:5` either becomes shadbala-based rank-of-9 or is renamed to
its true basis); arudha/UL + nakshatra-semantic salience ranks (CR-61/64) get documented
deterministic formulas or explicitly ship unranked. *Verify:* wealth assessment on 482012f1
serves a grounded verdict ≤ budget, D2/D11/Indu present, top-10 signals ≤2 micro-varga entries,
contradictions wealth-tagged, Venus rank consistent across remedy/digest surfaces.

### Lane F [OPUS] — Muhūrta & election engine (EL-50 · EL-33 · EL-53-engine)

`platform-mcp/src/tools/muhurta_finder.ts` + kala service wrappers. (a) Extend
`activity_type` taxonomy: `spiritual_initiation`, `remedial_ritual`, `japa_start`, with
classically grounded rule sets (cited); (b) join the native's OWN tara_bala/chandra_bala
baselines (L1 categories exist — `get_tara_chandra_bala.ts`): an adverse tārā (Vadha/Pratyak)
for the native's Moon DISQUALIFIES or hard-flags a window — never a silent top rank (regression:
the Aug-26–28 Vadha-tārā window must rank bottom or carry the flag); (c) `target_graha` param:
election windows check the target graha's transit dignity/combustion/retrogression via Lane C's
sidereal service — Venus-debilitated-all-August must surface on every August window for a
Venus election; (d) horā/sub-day resolution using Lane C's horā boundaries; IST-anchored
day-explicit timestamps (no UTC-midnight ambiguity). **EL-33:** first-class
`active_dashas(date|today)` face over `ganita_dasha_periods_get` — L1/L2/L3 lords + exact
bounds across ALL built dasha systems (DR-14). **EL-53:** election output gains
`file_as_prediction: true` → writes a prospective-ledger row (elected window, predicted quality,
scoring factors) closable via `mimamsa_outcome_record` — elections become falsifiable
predictions (extends L5 STRUCTURAL calibration with its fastest evidence stream; no new
mimamsa schema unless a NEW migration is required — additive only).
*Verify:* re-run the register's japa-initiation election: taxonomy honest, Vadha-tārā flagged,
Venus condition surfaced on August windows, horā-resolved IST windows, election filed and
readable back via `standing_predictions_read`; both charts for baseline-join chart-agnosticism.

### Lane G — Remedies & corpus (EL-51 · EL-52 · EL-35 · CURRENT_STATE A-5 disposition)

(1) Chart-scoped remedy engine serves the FULL 25-item catalog with per-class inclusion/
exclusion REASONS (homa/yantra/vrata/gemstone families that don't apply say why); (2) gemstone
contraindication (maraka lordship etc.) computed as a deterministic verdict per gemstone with
citation — never catalog prose the consumer must interpret (safety-bearing); (3) backfill
`associated_doshas_array` + INR cost where the catalog carries data, else explicit
EL-19-style honest-gap disclosure; (4) **EL-52:** corpus serving rows get structured cleanup —
verse ref · cleaned translation · tagged prescription — starting with the passages the
register names (BPHS Ch.47 Venus-maraka) and the remedy-cited set; OCR-confidence scored,
low-confidence rows FLAGGED not served bare; bounded overnight scope: the ~200 highest-traffic
rows (remedy-linked + rule-search top hits), full-corpus pass parked as named follow-up;
(5) **EL-35:** framework-tagged one-line `astrological_significance` on esoteric served fields
(22nd drekkana, tara_bala, KP sublords) — sourced from `ref_*` reference tables, tagged
Parashari/Jaimini/KP/Tājaka. **A-5 note:** CURRENT_STATE v6.41 halted the remedy-engine repair
awaiting native decision with accept-as-dark recommended — this lane SUPERSEDES accept-as-dark
with a real repair; Native-Proxy records the ruling (§6) for morning ratification.
*Verify:* chart remedy call serves ≥ the catalog's applicable classes with reasons; a
contraindicated gemstone carries a computed verdict + citation; BPHS Ch.47 passage serves
readable; spot-check 10 cleaned rows against source scans for fidelity (no hallucinated
translations — flag-not-fabricate on low confidence).

### Lane H — Discovery, steering & entity faces (EL-31 · EL-48 · EL-34 · EL-08)

(1) **EL-34/EL-08 (one substrate):** `get_database_schema` (alias `concept_locate`) —
mechanically generated from the DB: every fact_category × fact_subjects × fact_keys with
one-line meanings + concept aliases (seed from the Phase-0.7 census matrix; Gulika/Maandi →
`sensitive_point_gulika_mandi` etc.); census-vs-alias CI regression (new categories must
register aliases or fail — Lane K wires it). This substrate also = EL-03's ledger input
(Lane I). Absence Protocol wiring: "not in your data" phrasing requires a concept-resolver
MISS; a category-probe empty serves "not found in what I queried" + resolver suggestion
(EL-07's fix, mechanical form). (2) **EL-31:** canonical entity endpoints `query_planet(name)` /
`query_house(n)` — ONE assembled object (sign/house/nakshatra/dignity/shadbala/avastha/aspects
in/out) built over existing tools (graha_portrait post-Lane-A becomes the engine; this is the
discoverable face + the EAV tools' descriptions steer to it; `tool_search` ranks assembled
faces above raw EAV for entity-shaped queries). (3) **EL-48:** `chart_snapshot` gains
`vargas:["D2","D10","D11",…]` — per-varga grid assembled server-side, budget-layered.
*Verify:* the register's own consumer asks replayed: "how is my Venus" via query_planet = one
call, complete, budgeted; D2/D10/D11 snapshots one call each; `concept_locate("gulika")` →
correct categories; schema map complete against a live category census (zero truncation at
2000 rows — paginated).

### Lane I [OPUS] — Consumption contract, planner coverage & the dossier (EL-01..06 · EL-14 · EL-23 · EL-26 · EL-27 · EL-29 · EL-56 · EL-61)

The flagship lane. Two sub-phases:

**I1 — Ledger & coverage (mechanical, runs early in Wave 2):**
- **EL-03:** generate the per-domain concept ledger FROM data: census 46-concept matrix ×
  vidhi floors (`platform-mcp/src/resources/vidhi/*`) × fact_category inventory (Lane H's
  schema map) → `00_ARCHITECTURE/llm_consumption_audit/capability_map/DOMAIN_CONCEPT_LEDGER_v1_0.json`
  (per domain: concept → serving category → covering primitive → floor membership), CI-maintained.
- **EL-26:** mechanical planner-coverage audit: every fact_category × asset → covering
  primitive in the planner registry OR an explicit exclusion-with-reason. Fix the VERIFIED gaps
  first: a `varga_ashtakavarga` primitive (the only AV primitive is natal-hardcoded);
  then every uncovered insight-bearing category gets a primitive or an exclusion entry. CI
  gate: new categories cannot land unplanned (Lane K).
- **EL-27+56 (one mechanism):** `cross_ayanamsha_variation` primitive family — per finding:
  compute agreement across the computed ayanamshas (dignity/vargottama/house-shift deltas),
  serve `ayanamsha_agreement: n/6` as a confidence field, family-collapse duplicates in
  discoveries (extend the E-6 family_aggregation key to include ayanamsha — the machinery
  exists in the digest pipeline). Planner gains ayanamsha as an expressible axis (the word
  currently appears ZERO times in the registry). KP floors get krishnamurti-ayanamsha reads
  as their default.
- **EL-02:** the completeness receipt (`plan_retrieval` observations → served/empty/dark)
  becomes REQUIRED in the dossier path (below) and its serving-time accounting is written to
  `retrieval_receipts` for the consumption metric.

**I2 — The dossier + composition doctrine (LAST — consumes every other lane):**
- **EL-61:** `dossier(domain, depth?)` MCP tool: server-side orchestration of snapshot +
  lords + yogas/firings + domain vargas + special lagnas + AV + timing + remedies + top-N
  gestalt findings (EL-05's volunteering contract: the chart's own top laksana findings served
  unprompted) into ONE budgeted, layered, receipt-bearing response — floor compiled AND
  executed server-side (EL-02/EL-14), paginated for small clients (Lane A's budget param),
  composed per the reading structure below. Deterministic orchestration over existing handlers
  (in-process, like graha_portrait's pattern) — no generative synthesis in the serving path.
- **EL-29:** composition doctrine as a SERVED contract: the dossier (and deepdive responses)
  carry the established reading form — gestalt/orientation → promise → evidence chains →
  tensions + adjudication → timing → guidance — with the gather-then-compose gate (receipt
  files before composition section is emitted). Doctrine documented in
  `RETRIEVAL_STRATEGY` amendment + served as `reading_contract`.
- **EL-04/EL-23:** per-answer consumption ratio (consumed categories / domain ledger) computed
  in the dossier receipt + added to the standing battery as a first-class grading dimension
  (target ≥90% on naive domain questions); benchmark naive-vs-expert pairs per domain (EL-05's
  n=1 → n≥2 domains) added to the battery spec (Lane K).
*Verify (the flagship acceptance):* a NAIVE "how is my wealth?" through `dossier(wealth)`
returns — in ONE call, within default budget — D2/D11/Indu/AV/special-lagnas/dispositor/argala
coverage with consumption-ratio ≥0.9 against the wealth ledger, top-5 founding findings
volunteered, composed in the doctrine structure, receipt attached, honest gaps flagged; the
session's original 25-call assembly is reproduced by ≤3 calls. Both charts.

### Lane J — Calibration & lifecycle (EL-58 · EL-54-prep · EL-25-prep · EL-24)

(1) **EL-58:** prediction-lifecycle sweep: every prospective row past its window auto-matches
against LEL (empty today → moves to `lapsed_unobserved` — itself calibration data, per the
register's framing); the 2011-gain-window-still-open class closes; lifecycle states documented;
runs as a build-close step + a scheduled job. (2) **EL-54:** the guided LEL intake surface —
a served checklist ("log these 3–5 event types with dates" per domain, derived from what
retrodiction needs) + an ingest path that VALIDATES but never invents; delivered as a
morning-ready packet for the native (30–60 min of native time converts the biggest epistemic
gap). (3) **EL-25:** ratification packet — every pending item (NATIVE_PROXY_LEDGER through
D-4b, battery stamps, Phase-0.7 pin, THIS RUN's proxy ledger) compiled into one
morning-review artifact with per-item recommended disposition. (4) **EL-24 (bounded):**
build_run rows carry substep denominator + dispatched-scope legibly; reaper/self-heal for
orphaned runs if the SARVA-SIDDHI affordance is cheap; cockpit UI changes OUT of overnight
scope beyond data fields (park to a UI session).

### Lane T — Timing residuals (EL-15 · EL-17 · CR-131 · gochara env gap) [bounded]

With prod credentials available overnight (the exact blocker CURRENT_STATE v6.41 named):
(1) fix the gochara serving tools' `DATABASE_URL` gap; (2) re-dispatch/resume the
`ka_gochara_sweep` for 482012f1 (165/300) and drive to completion or to an honest
characterized failure (the ~6x-not-600x resume-speed reality is KNOWN — budget the wall-clock
accordingly; if projected completion exceeds the run window, dispatch, monitor, record state,
park with a completion ETA); (3) **EL-17:** re-verify CR-66 phala domain anchors + CR-37
activation dating LIVE post-Lane-D rebuild; pull the two PRE_DARPANA v2.0 Stage-2 residuals
into the register as explicit items (register append, `NATIVE TO CONFIRM` flag retained).
**EL-16 / D-6 GOCHARA-SWEEP-2.0 is OUT of scope** (staged design awaiting native review —
scope boundary per MACRO_PLAN; the completing v1 corpus is its equivalence baseline).
**The Darpana S3 re-run itself is OUT of scope** (native-attended session) — this lane
UNBLOCKS it.

### Lane K — Instrumentation & CI gates (EL-04 · EL-09 · EL-10 · EL-21-v1 · EL-22 · EL-23 · EL-60 · RC-7)

Built EARLY (Wave 0 seeds, hardened in Wave 2) because the Verifier runs on it all night:
1. **Smoke gate:** CI job calling EVERY registered MCP tool with minimal valid args on
   482012f1 — any 500/hang fails (a tool that never returned 200 in prod is the cheapest
   defect class — EL-37 would have been caught on day one). Nightly + pre-deploy.
2. **Budget census gate:** worst-case response per tool ≤ its declared ceiling (Lane A's
   ledger); runs on both charts.
3. **Degenerate-value screen:** any numeric per-graha/per-house field with distinct-count 1
   across entities → fail (EL-40 class).
4. **Convention gate:** house/sign index semantics (Lane D's ruling) + served-identifier
   canonicalization (EL-32) asserted on sampled rows.
5. **Receipt gate:** per-requested-category receipts present (EL-41); ✓-over-empty-array
   impossible (Lane A invariant); absence-phrasing lint on served strings (EL-07 class).
6. **Standing battery upgrades:** two-pass grading (grader + DB-verifying auditor) codified as
   LAW in the battery spec (EL-10); the four instrumentation tracks (experience, I1–I5, V1–V5,
   RE1–RE5) captured by the harness (EL-22); consumption-ratio + volunteered-findings-count
   grading dimensions (EL-04/23); benchmark pairs; varga-depth probe (EL-06); a small
   classical-attribution table (karaka/gloss claims — Sun=soul-kāraka etc.) checked over
   served prose (EL-09, bounded to the register's known instances + ~20 core attributions).
7. **EL-21 v1 (bounded):** serving-time claim-checker for the two cheapest classes — absence
   claims (must trace to a concept-resolver miss) and receipt-vs-payload consistency —
   implemented as a response post-processor + battery assertion. Full phase/timing claim
   verification: DESIGNED (spec doc) but implementation parked as named follow-up if the
   overnight window tightens.
8. **EL-60:** `reading_notes_get` auto-accretion per domain per session (the highest
   value-per-token surface — preserve and compound it); build-coverage attestation field on
   coverage claims ("no adverse windows" carries `sweep_coverage: {substeps: n/m, span}` so
   an honest empty and an unrun sweep are distinguishable).

## §4 — The swarm roster

| Role | Model | Mandate |
|---|---|---|
| **Conductor** | Opus | Owns this charter, the wave DAG (§7), dispatch, merge order, run ledger, morning report. Writes no feature code. |
| **Native-Proxy** | Opus | Replaces the native for EVERY overnight decision within §6's boundaries. Logs every consequential call + rationale to `NATIVE_PROXY_LEDGER_ELEVATION.md`. |
| **Verifier** | Opus | Independent, adversarial. Owns DONE (§5). Runs G0 baselines and G4 confirmations against PROD on both charts. Never the builder of what it verifies. |
| **Goal-Keeper** | Sonnet | Watches every lane against §1's mission; flags scope drift, gold-plating, wrong-problem solutions; can redirect via Conductor. |
| **Lane builders** (A–K, D2, T) | Sonnet default; [OPUS] lanes A/D/D2/F/I as marked | One builder per lane, own worktree `elev/<lane>`, builds only its declared files; requests Conductor arbitration on any cross-lane file need. |
| **Harness runner** | Sonnet | Executes the repro battery + smoke/census scripts on demand for Verifier (cheap mechanical runs so Opus verification tokens go to judgment, not plumbing). |

Escalation to Opus (any lane): 2 failed verify cycles on the same criterion · classical-rule or
writer-math authoring · any cross-cutting refactor touching shared envelope files. De-escalation:
never mid-task. No Fable, no non-Anthropic models in the dev loop (the §J "no Anthropic in
PRODUCT serving paths" constraint is untouched — this is dev tooling).

## §5 — The Verifier protocol (what DONE means)

1. **Baseline first (Wave 0):** before ANY fix, the Verifier captures the full repro battery
   (§3's per-lane recipes + the register's own corroborated probes) against prod → 
   `ledgers/ELEVATION_BASELINE_CAPTURE.md` with raw payloads. No fix merges until its
   baseline exists (else before/after is unprovable).
2. **G0 reproduce-or-reclassify:** a lane's first act is re-running its recipes. Symptom absent
   → `NOT-REPRODUCED` + evidence, item closes WITHOUT code churn (some register symptoms may
   be stale — e.g. R5.1-era fixes). This is a legitimate, evidence-backed close.
3. **G4 confirm:** after merge + deploy, the Verifier independently re-runs the recipes against
   the LIVE production MCP (never the worktree, never localhost — the
   feedback_ac_must_verify_target_environment scar), on BOTH canonical charts, PLUS the
   regression battery (baseline diffs — nothing that worked got worse) PLUS the §3 lane
   acceptance criteria. Two-pass discipline per EL-10: the builder's claim + tests count for
   nothing until this pass.
4. **Evidence block per EL:** `{el_id, status, before_payload_ref, after_payload_ref,
   probes_run, charts, verifier_notes}` appended to `ledgers/ELEVATION_RUN_LEDGER.md`. The §12
   matrix is updated ONLY by the Verifier.
5. **Deploy verification** (Pratiṣṭhā duty, folded into Verifier): after each deploy wave —
   revision live, image SHA matches main, smoke gate green — before G4 probes run.
6. **Failure:** bounded remediation (§8.3). The Verifier never "passes with caveats" — a
   caveat is either a PARKED-HONEST disposition or a fail.

## §6 — Native-Proxy charter

**MAY, autonomously (logged):** all engineering decisions (design trade-offs, eliminate/
integrate/build-around on legacy code, per-facet defaults, taxonomy namings); merge order
arbitration; ruling on ambiguous acceptance criteria in the spirit of §1 + the register's
"Expectation violated" fields; superseding CURRENT_STATE A-5 (remedy accept-as-dark → Lane G
repair) and progressing A-6 residuals via Lane T; bounded scope cuts inside a lane (park
sub-items PARKED-HONEST when the window tightens — never silently); schema migrations
(ADDITIVE only); chart-scoped rebuilds; production deploys.

**MUST NOT, ever:** fabricate data — life events (EL-54), classical rules/citations (B.10),
translations where OCR confidence is low (flag instead); alter the FROZEN orchestrator
contract, the sealed L5 split, FORENSIC anchors, or canonical registries beyond declared
close-edits; ratify in the native's name (every ruling is recorded PROXY-RULED for morning
ratification — the NATIVE_PROXY_LEDGER precedent); destroy data without snapshot +
reverse-citation report; expand scope beyond this charter (new campaigns, D-6 build,
architecture changes — park and note).

**Tie-breaker doctrine, in order:** (1) truth over coverage (an honest gap beats a padded
answer — the register's whole §B); (2) the native's stated differentiator (deterministic
full-depth consumption); (3) smallest-real-client UX; (4) classical grounding with citation;
(5) reversibility.

## §7 — Execution DAG (waves, parallelism, wall-clock)

```
SNAPSHOT(run-start: git tag elev-run-start + DB snapshot)
WAVE 0  (serial, ~1h): run-ledger scaffold · smoke-harness v0 (K.1) · Verifier BASELINE
        capture (§5.1) · lane worktrees cut
WAVE 1  (parallel ×7, ~2–3h): A(envelope) ∥ B(surfaces) ∥ C(sidereal) ∥ D.audit ∥
        F(muhurta) ∥ G(remedies) ∥ H(discovery)
        → merge order: A first (shared files), then B/C/H, then F/G (rebase over A) →
        DEPLOY-1 → Verifier G4 pass over wave-1 lanes → SNAPSHOT
WAVE 2  (parallel ×6, ~2–3h): D.fix+rebuild ∥ D2(sahams/bhanga) ∥ E(assessors) ∥
        J(calibration) ∥ T(timing) ∥ K(gates hardened over the now-stable surfaces)
        → DEPLOY-2 → Verifier G4 (incl. post-rebuild FORENSIC 7/7 + MSR resolution) → SNAPSHOT
WAVE 3  (serial spine, ~2h): I1(ledger+coverage+ayanamsha engine) → I2(dossier+composition)
        → DEPLOY-3 → Verifier flagship acceptance (§3.I) → SNAPSHOT
WAVE 4  (~1h): FULL battery — all repro recipes, both charts · regression diff vs baseline ·
        red-team pass (cadence obligation per §M: this arc closes with one) · chart-agnostic +
        contamination checks
WAVE 5  (~30m): §12 matrix finalized by Verifier · register updated (each EL's disposition +
        evidence ref appended by the run — the register stays append-only per its own rules) ·
        CURRENT_STATE + SESSION_LOG close · ratification packet (J.3) · morning report
```
Parallelism rules: file-ownership isolation per lane (declared in each worktree's first
commit); cross-lane file contention → Conductor serializes those two lanes only; independent
lanes NEVER wait on a sibling's remediation. Wave 2 starts per-lane as Wave-1 merges complete
(no global barrier beyond the shared-file rebase). Total projected: **8–11h wall-clock.**

## §8 — Safety rails

1. **Snapshots:** git tag + DB snapshot at run-start and every wave boundary (automatic, never
   waits). Rollback-and-retry beats compounding corruption.
2. **Rebuild discipline:** chart-scoped delete-then-insert only (§N.3); never a full-DB
   rebuild; FORENSIC 7/7 asserted after every rebuild; sealed tables untouched.
3. **Bounded retries:** MAX 3 remediation cycles per lane-criterion, then Opus escalation, then
   2 more, then PARKED-HONEST with the residual + live disclosure verified (the honest-open
   pattern v6.41 modeled). Goal-Keeper watches for thrash.
4. **Reverse-citation before ANY deletion/retirement** (grep the live codebase for citations;
   still-cited → keep-or-repoint; report logged).
5. **Budget ceilings:** the Brahma-arc precedent rails apply — wall-clock cap 12h, per-lane
   6h; spend guardrails per the AUTONOMOUS_MODE amendment scale.
6. **Deploy hygiene:** per BUILD.md — platform auto-deploys on main; sidecar + pipeline via
   their cloudbuild configs; `platform-mcp` via its Dockerfile/Cloud Run service; every deploy
   followed by the smoke gate before Verifier probes.
7. **Degenerate-distribution + contamination checks** every wave (no native-hardcoding in
   chart-agnostic code paths; chart_id always a parameter).

## §9 — Out of scope (explicit, park-and-note)

D-6 GOCHARA-SWEEP-2.0 build (staged, native review pending — EL-16) · the Darpana S3 re-run
itself (native-attended; this run unblocks it — EL-15's verdict stays OPEN) · UCN→UCD
retirement · cockpit/UI redesign beyond EL-24's data fields · full-corpus OCR pass beyond
Lane G's bounded set · full claim-checker phase-2 (designed, not built) · any Macro-Plan
phase-jump (MACRO_PLAN §Scope Boundary) · LEL content entry (native-only) · A-6
accept-as-dark reversal beyond Lane T's re-verification evidence.

## §10 — Prepared-for-native deliverables (the morning desk)

1. **LEL intake packet** (Lane J) — the 30–60-minute guided event-logging surface, ready to run.
2. **Ratification packet** (Lane J) — all pending ratifications incl. this run's
   NATIVE_PROXY_LEDGER_ELEVATION, one recommended disposition each.
3. **Darpana readiness note** — which held exit-conditions this run closed (mapped to
   PRE_DARPANA v2.0 items), what remains for the S3 re-run.
4. **Parked-item register** — every PARKED-HONEST residual with its bounded-attempt evidence
   and a sized follow-up recommendation.

## §11 — The morning report

One artifact: `00_ARCHITECTURE/llm_consumption_audit/ELEVATION_RUN_REPORT_v1_0.md` — per-wave
outcomes; the §12 matrix final state with per-EL evidence refs; every Native-Proxy ruling +
rationale; every rollback/retry; deploy revisions shipped; rebuild scope + FORENSIC/MSR
post-checks; battery + red-team results; budget/wall-clock actuals; the four §10 packets;
and a one-paragraph verdict against §1's mission. CURRENT_STATE §2 + SESSION_LOG updated
atomically (session-close checklist per §H); root `CLAUDECODE_BRIEF.md` status flipped to
COMPLETE only if the close checklist validates.

## §12 — Coverage matrix (every EL → lane; Verifier-owned dispositions)

| EL | Lane(s) | Overnight outcome targeted |
|---|---|---|
| EL-01 concept-consumption | I (+E,H) | dossier consumption-ratio ≥0.9 verified |
| EL-02 floor as contract | I2 | receipt-gated dossier serving |
| EL-03 concept ledger | I1 | generated + CI-maintained |
| EL-04 consumption metric | I1+K | per-answer ratio in receipts + battery |
| EL-05 volunteering gap | I2+K | top-N findings unprompted; benchmark pairs specced |
| EL-06 varga depth | E+I+K | wealth vargas consumed; varga probe in battery |
| EL-07 absence protocol | B+H+K | resolver-gated absence phrasing + lint |
| EL-08 concept resolver | H | `concept_locate` live |
| EL-09 precision class | K | attribution table + battery checks |
| EL-10 two-pass law | K (+§5) | codified in battery; this run runs on it |
| EL-11 client caps | A | census gate green at default ceiling |
| EL-12 budget negotiation | A | `budget_kb` param live |
| EL-13 catalog caching | B | version field + doc + notify-if-supported |
| EL-14 server-side completeness | I2 | dossier = served product |
| EL-15 S3 unverified | T | sweep completed/characterized; verdict stays OPEN (§9) |
| EL-16 sweep v1 arch | — | OUT (D-6, native review) — noted |
| EL-17 timing-anchor residuals | T | re-verified live post-rebuild; residuals registered |
| EL-18 bhanga | D2 | attested rules computed + cited; rest honest |
| EL-19 sahams | D2 | Tājaka set computed both charts |
| EL-20 serving-rank residuals | E | documented formulas or explicitly unranked |
| EL-21 claim-checker | K(v1)+A | absence+receipt classes live; phase-2 designed |
| EL-22 four tracks | K | harness captures all four |
| EL-23 battery blind spot | K | new grading dimensions |
| EL-24 build-state truth | J (bounded) | data fields legible; UI parked |
| EL-25 governance debt | J | ratification packet |
| EL-26 planner coverage | I1 | audit + varga-AV primitive + CI gate |
| EL-27 cross-ayanamsha | I1 | variation primitive family + agreement scores |
| EL-28 small-context capability | A | named capability + acceptance tests |
| EL-29 composition doctrine | I2 | served reading structure |
| EL-30 house_d1 semantics | D | convention ruled, writers fixed, rebuilt, verified |
| EL-31 EAV steering | H | entity endpoints + steering |
| EL-32 identifiers | E (+K) | canonical on output; gate extended |
| EL-33 active dashas | F | convenience face live |
| EL-34 schema map | H | `get_database_schema` live |
| EL-35 inline significance | G | framework-tagged strings on esoteric fields |
| EL-36 portrait starvation | A | flagship fix; receipt truth invariant |
| EL-37 mechanisms bind bug | B | fixed (root cause in §3.B) + smoke-gated forever |
| EL-38 argala | B+D | bounded default + house-resolved + zeros adjudicated |
| EL-39 tropical-only | C | sidereal default; FORENSIC panchāṅga oracle passes |
| EL-40 uniform 0.875 | D | real formula or withdrawn-with-reason |
| EL-41 silent categories | B | per-category receipts everywhere |
| EL-42 token blowouts | A | uniform budgets; census green |
| EL-43 EAV verbosity | A | pivot-first defaults |
| EL-44 skeleton verdicts | E | grounded verdict layer |
| EL-45 wealth varga stub | E | D2/D11/Indu consumed in-tool |
| EL-46 flags trimmed | A | honesty-field immunity |
| EL-47 null varga houses | B+D | served + persisted houses |
| EL-48 varga snapshots | H | `vargas[]` param |
| EL-49 panchanga_get | C | direct tool, all limbs + horā |
| EL-50 muhūrta gaps | F | 4 sub-gaps closed; regression on the Vadha-tārā case |
| EL-51 remedy completeness | G | full catalog + computed contraindications |
| EL-52 corpus OCR | G (bounded) | decisive passages structured; rest scoped |
| EL-53 election loop | F+J | elections file as predictions |
| EL-54 LEL backfill | J | intake packet (native-only content) |
| EL-55 micro-varga salience | E | cited varga-weight term |
| EL-56 ayanamsha dedup | I1 | family-collapse + agreement (with EL-27) |
| EL-57 contradiction filter | E | domain-filtered + honest empty |
| EL-58 stale predictions | J | lifecycle sweep + auto-close |
| EL-59 rank semantics | E | one vocabulary, basis-labelled |
| EL-60 preserve what worked | K | notes auto-accretion + coverage attestation |
| EL-61 dossier | I2 | the flagship acceptance (§3.I) |

*(Plus, from CURRENT_STATE v6.41: A-5 → Lane G supersession; A-3/CR-131 + gochara env → Lane T;
B-1 silent-empty → Lane B; B-2 standing-prediction surfacing → Lane J verifies the
Sat-Jupiter 2027 claim reaches a live surface or records why not.)*

---

*End of ELEVATION_CAMPAIGN_CHARTER v1.0 — authored by Fable in Cowork, 2026-07-24, grounded in
the live-server corroborations and code recon of the same session (query_mechanisms param bug,
portrait starvation mechanics, response_budget PASS-2/truncation behavior, tropical ephemeris
route, argala/dispositor serving shapes — all verified against the working tree at authoring
time). The register accumulates; this charter executes. Nothing here closes without the
Verifier.*
