---
artifact: SHODHANA_BRIEF (Consumption-Register Remediation Campaign)
canonical_id: SHODHANA_BRIEF
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-07-26
author: Fable (Cowork planning session), from LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md (MC-001..034,
  WL-1..8) cross-validated by ANALYSIS_LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md (same directory)
source_documents:
  - 00_ARCHITECTURE/llm_consumption_audit/LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md   (the register)
  - 00_ARCHITECTURE/llm_consumption_audit/ANALYSIS_LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md
    (the cross-validation — READ IT: it marks which MC items are CONFIRMED on the current
    deployment vs suspected artifacts of a stale surface. Do not build fixes for stale-surface
    artifacts without Phase-A re-verification.)
mode: >
  FULLY AUTONOMOUS · Conductor (Opus) + parallel Sonnet track-builders (Opus step-up per §4 policy)
  + ONE dedicated Opus Verifier that never writes code + ONE Dvārapāla escalation agent that
  autonomously resolves any would-be human gate with a documented decision · no human gates ·
  maximum safe parallelism via in-repo git worktrees (.worktrees/shodhana-*) · PR + auto-merge only
  · explicit deploy · full cleanup · wall-clock cap 8h · PRIME RULE: truth over completion —
  PARKED-HONEST with evidence is a legitimate close for any track.
coexistence: >
  A PŪRṆA-VIRĀMA session may be RUNNING in this repo when this campaign starts. §5 rails govern
  coexistence. NEVER repoint the root CLAUDECODE_BRIEF.md while PV is live — this brief is
  launched by direct path, not by root-brief pointer.
---

# ŚODHANA — Consumption-Register Remediation (MC-001..034)

## §0 — Mission in one paragraph

An independent LLM endpoint consumed the portal end-to-end during a live consultation and filed
34 defect items + 8 wishlist capabilities. A second independent session cross-validated them
against the CURRENT production deployment and found: (a) a set of items CONFIRMED live (trimmer
§N.6 inversion, envelope overflow, discovery duplication, remedy-ranking flatness + the
weakest-graha contradiction, the Mars-error-inviting yoga schema — committed by BOTH endpoints
independently); (b) a set of items likely measuring a STALE parallel surface (`marsys-jis-direct`)
that contradicts current behavior (dossier hydration, D2✓/D10✓ varga confirmation); (c) one
genuinely missing L1 asset (yogi/avayogi); and (d) the arc's Offer Law proven a 4th time — the
completeness gate itself was bypassed because honoring it was unaffordable. This campaign
verifies, fixes, deploys, and closes every item with a per-MC disposition — leaving production
in sync with main and the register updated to a closed state.

## §1 — Non-negotiable context (read before building anything)

1. **The dual-surface problem is the first work item, not a footnote.** Half the register may
   describe `marsys-jis-direct`, not the amjis-mcp Cloud Run deployment. Phase A pins this.
   Every MC fix ticket must carry a `verified_on_current: true|false|stale_surface_artifact`
   field after Phase A. Building a fix for a defect that only exists on a retired surface is
   wasted work and will be rejected by the Verifier.
2. **W7.4 regression evidence.** The cross-validation proved `completeness_directive` truncation
   and `coverage_map: []` on the LIVE deployment (assess_career, 2026-07-26). Whatever hardFloor
   set W7.4 shipped, it is incomplete. T3 finishes it with a regression battery so it cannot
   silently regress again.
3. **The preserve-list is a rail.** Register "Preserve-list" + "Positive" blocks (chart_snapshot,
   judgment_query decomposition, special lagnas, AV transit gating, kala_windows dedup,
   yoga-firings grounds_jsonb, honesty fields everywhere, gemstone acharya-review gating) must
   not regress. The Verifier spot-checks preserve-list surfaces after every merged track.
4. **Code anchors already pinned by planning recon** (verify, then build — do not re-discover):
   - `platform-mcp/src/lib/response_budget.ts` — hardFloor mechanism at ~L94-98, PASS-2
     override exemption at ~L215. Mechanism exists; per-tool application is the gap.
   - `varsha_year` param: present in `src/generated/mcp_surface_profiles.generated.ts` (~L2176,
     R-25) and in `register_p1_ganita.ts` docstring (~L814) — **absent from the runtime handler
     logic**. Schema advertises what the handler ignores → MC-021/024 root cause.
   - `src/bundles/holistic_bundle.ts` + `multi_school_bundle.ts` — `sub_tools_errored` lives
     here; MC-002's `ok:true`-while-degraded envelope is composed here.
   - `register_p1_synthesis.ts` — "denied" verdict strings (MC-010).
   - `constituent_planets` appears in NO serving file → it passes through verbatim from the
     `ga_yoga_firings` DB row; MC-016's split is a serving-side projection over `grounds_jsonb`
     (or a writer change in the python sidecar — builder's choice, projection preferred).
   - `tools/dossier.ts` — gate/receipt logic (T5). `tools/muhurta_finder.ts` — scorer (T7).
   - `tools/retrieval/remedy_tools.ts` — remedy serving; resonance formula is writer-side in
     `platform/python-sidecar/pipeline/` (bo_upaya writer — locate in Phase A).
   - Sidecar layout (known-good from prior campaigns): `platform/python-sidecar/pipeline/`
     (orchestrator/asset_runner.py, l5_lel_intake.py, mi_jivanaghatana.py exist there).

## §2 — Phase A: triage & reconciliation (T0 — blocks everything)

Run as ONE Opus agent (this is judgment work), ~45 min budget:

- **A.1 Pin the surfaces.** `mcp_server_info` (or equivalent HTTP probe) against BOTH the
  amjis-mcp Cloud Run service and whatever `marsys-jis-direct` resolves to (search repo for its
  definition: local server script, .mcp.json, or an alternate service). Record
  `catalog_version` + git SHA of each. Decision matrix: if direct == stale → file a ticket to
  upgrade-or-retire it (execute the retirement/upgrade in T4 if it is a config change; park with
  evidence if it is infra outside this repo). If direct == current → the register's dossier/
  varga items are REAL current defects; re-scope T5 accordingly.
- **A.2 Re-verify every MC item against the current deployment.** Cheap live calls per item
  (the analysis doc's §1/§0 tables say which need re-testing vs which are already confirmed).
  Output: the disposition seed table — every MC gets `verified_on_current` before any builder
  starts. Items that fail re-verification get disposition `stale_surface_artifact` and are
  closed WITHOUT code changes (register annotated).
- **A.3 PV coexistence check.** Look for `PURNA_VIRAMA_REPORT_v1_0.md` and open PV PRs/branches.
  Until PV's report exists or its branches are merged: `response_budget.ts`,
  `registry_bridge.ts`, and all `briefs/close_out/` + register/ledger docs are **PV-locked** —
  T3 HOLDS, all other tracks proceed (their file sets are disjoint). Poll every 20 min; release
  T3 when PV closes. If PV is still live at hour 6, Dvārapāla decides: park T3 honest, or
  proceed on a rebase-heavy branch with explicit conflict ownership.
- **A.4 Worktree setup.** `.worktrees/shodhana-t{1..9}` from current main, one per active track;
  register them; confirm builds pass clean at baseline (`npm test` in platform-mcp, sidecar
  smoke) BEFORE any edits, so failures are attributable.

## §3 — Tracks (file ownership disjoint; run all non-held tracks in parallel)

### T1 · SATYA-VĀK — safety wording & status vocabulary (Sonnet, effort low-med)
**Items:** MC-010 (P0-safety), MC-017, MC-009's state labels, MC-003.
**Files:** `register_p1_synthesis.ts` (+ any other emitter of "denied" found by grep),
status-label constants, provenance strings.
**Work:** (1) n_support=0 structural priors NEVER render "denied"/"confirmed" — render
`not_yet_assessed (structural prior, no evidence rows)`; grep-audit ALL verdict verbs against
evidence-count guards. (2) Replace `not_computed_at_l1` with two distinct tokens:
`domain_block_not_served (raw rows exist — see chart_snapshot/chart_divisionals)` vs
`not_computed_globally`; ensure `true_negative` (empty_for_this_chart) is never conflated with
either. (3) Sweep served provenance strings for deleted artifacts (FORENSIC v8.0 etc.) →
repoint to chart_facts/current canonical.
**Acceptance (Verifier, live):** synth_chart_brief for 482012f1 contains zero denial-verbs on
n_support=0 rows; the three status tokens are distinct in assess_*/dossier responses; no served
provenance string references a §B-deleted artifact.

### T2 · SETU-BANDHA — build coherence & bundle honesty (design: Opus · impl: Sonnet, effort high)
**Items:** MC-001 (82.9% orphaned Bodha→L1 fact_ids), MC-002 (bundle ok:true while 5/8 errored),
MC-025b (weakest-graha single authority).
**Files:** python sidecar Bodha writers/linkers; `src/bundles/holistic_bundle.ts`,
`multi_school_bundle.ts`; a NEW small freshness-stamp lib (do NOT touch response_budget.ts —
that is T3/PV territory).
**Work:** (1) Prefer RE-LINK over rebuild: if the L1 rebuild's fact_id change is deterministic
(SHA over stable content), write a remap pass for `constituent_facts_array`; full Bodha rebuild
only if remap is impossible — and then with the §5 untouchables verified protected first.
(2) Every Bodha-derived response gains `bodha_l1_linkage: {built_against_hash, live_hash,
fresh: bool}`. (3) Delete-or-derive: the stored `unresolved_constituent_facts_count` must be
removed or always derived live (stored-vs-live disagreement is the GA.1 class — kill the class,
not the instance). (4) Bundle envelope: top-level `status: ok|partial|degraded` computed from
sub_tools_errored count; `ok:true` with majority-errored constituents becomes impossible.
Root-cause MSR/CGM errors (expected: MC-001 linkage surfacing as hard error). (5) One authority
for weakest-graha: L1 shaḍbala (§N.5); bo_upaya reads it, never recomputes.
**Acceptance:** live orphan rate <1% on 482012f1 + 1c826d5a; bundle returns status:degraded
under an injected sub-tool failure (test); digest and remedies name the SAME weakest graha ==
L1 shaḍbala minimum (Venus, 3.90 band, for 482012f1); freshness block present on digest/
discoveries/signals/remedies responses.

### T3 · SAMA-BHĀRA — envelope economics & the hardFloor battery (Sonnet, effort med) — **HOLDS on A.3 until PV closes**
**Items:** MC-004/005/006/007, MC-023, MC-014, MC-019 (the §N.6 inversion family).
**Files:** `response_budget.ts` per-tool section configs, assess/judgment handler section
declarations, NEW regression battery test.
**Work:** (1) hardFloor ALL interpretive prose + honesty fields portal-wide: verdict clause
texts, completeness_directive, coverage_map, reading digests, judgment_flags, trim_report.
(2) Trim ORDER inversion: fact_id arrays and signal-id lists trim FIRST. (3) De-duplicate:
verdict/receipt served once per envelope (MC-023). (4) `verbosity: summary` guaranteed-fits
form for every assess_* + judgment_query + ganita_chart_facts_get: prose + verdicts + top-N
grounded signals, hard-capped under the MCP envelope (MC-004/006). (5) Defaults sweep
(MC-014): strength → actual-placement-only (counterfactuals behind all=true); sade_sati →
current+adjacent phases by default; dashas → active chain convenience shape. (6) THE BATTERY:
a test that calls every serving tool at budget_kb=1 and at default, asserting (a) fits
envelope, (b) zero mid-sentence truncation of hardFloored fields, (c) no duplicated sections.
Battery runs in CI — this is what makes W7.4 stay fixed.
**Acceptance:** battery green in CI; live assess_marriage fits its envelope with verdict prose
intact (the MC-006 tool that could not be served at all); sealed-harness flagship re-run shows
NO regression from W7 levels (median ≥12/13 stands — harness UNTOUCHED, §5).

### T4 · PRĀPTI — reachability & strict schemas (Sonnet, effort low-med)
**Items:** MC-021/024 (P0), MC-032, MC-022, MC-024's validation-posture finding, A.1's
direct-surface remediation if config-level.
**Files:** `register_p1_ganita.ts` (tajik handler + dashas), `register_p1_aliases.ts` (kala
priority ranking), zod schemas portal-wide.
**Work:** (1) Implement `varsha_year` IN THE HANDLER (schema already advertises it — R-25);
default sort current-year-first; accept a date and resolve its varsha; hadda_lord_facts behind
`include_hadda` flag (default false — 245 static rows drowned the envelope). (2) Dashas:
envelope advertises `levels_available: 4`; `level=4`/`all_levels` actually serves Sūkṣma.
(3) `kala_priority_ranking_get` gains `domain` filter; neutral-dignity descriptor rows
down-ranked from priority surfaces. (4) STRICT SCHEMAS EVERYWHERE: unknown params ERROR
(`.strict()` on every tool zod object) — one posture, portal-wide; battery asserts it.
**Acceptance:** live `ganita_tajaka_get(varsha_year: 43)` returns year 43 (2026→27) with
Muntha/year-lord; unknown-param call errors loudly on 3 sampled tools; level-4 rows served on
request; priority ranking honors domain=wealth.

### T5 · PŪRTI — the affordable completeness contract (design: Opus · impl: Sonnet, effort high)
**Items:** MC-012, MC-028/034 (Offer Law #4), MC-030, MC-031, MC-033. Re-scope per A.2 — the
current deployment already hydrates the dossier and confirms vargas; build the DELTA only.
**Files:** `tools/dossier.ts`, judgment/assess checklist composition, salience prior config
(python sidecar), KP block wiring.
**Work:** (1) **Compact completeness receipt**: a ≤2KB gate-summary (coverage % + per-family
accounting states + gate boolean + drill handles) decoupled from the concept-catalog dump —
the gate must be HONORABLE at consultation cost, or it will keep being bypassed (Offer Law).
(2) **Served domain-reading checklist**: judgment_query/assess_* responses carry a
`reading_checklist` receipt naming which classical units were served THIS response (bhāva/
bhāveśa from Lagna+Moon · kārakas · operative vargas · AV · special lagnas · sensitive-degree
FIRINGS · KP cusp chain · yogi/avayogi [after T6] · daśā levels · gochara sweep · tājaka) —
absent boxes say why. A response without the receipt self-discloses `non_exhaustive:
salience_sampled`. (3) Salience prior: FIRED sensitive-degree facts (pushkara/gandanta/
mrityu-bhāga firings) boosted above descriptor-state rows — a fired rare event must outrank
"dignity: neutral". (4) KP block (cusp sub-lord chain 2/6/10/11 + significators) joins the
wealth/career checklist — currently floored to the bottom-10% tail. (5) Gochara: domain
readings include one `gochara_forecast_get(domain=…)` join (tool exists — this is wiring).
**Acceptance:** Mars-in-Puṣkara appears in the wealth/career judgment for 482012f1 without
prompting; KP chain present in assess_wealth; receipt present + truthful (Verifier
cross-counts served units vs claim); dossier gate satisfiable in ≤2 calls at ≤8KB overhead.

### T6 · YOGI-BINDU — the missing L1 asset (Sonnet, effort med)
**Items:** MC-029 (only NEW computation in the campaign).
**Files:** python sidecar sensitive-points writer + `ganita_sensitive_degrees_get` serving.
**Work:** Yogi point = Sun + Moon + 93°20′; Yogi = nakshatra-lord of that point; Avayogi =
lord of the nakshatra 186°40′ further; add Duplicate-Yogi (sign-lord) + Sahayogi. Two-pass
verified (independent recompute), all 5 ayanāṃśas, both canonical charts, served under a new
`sensitive_point_yogi` category with citations.
**Acceptance:** for 482012f1/Lahiri: Yogi point ≈ 352.35° (Revatī) → **Yogi = Mercury**,
Avayogi → **Mars** (matches the native's independently-verified arithmetic in register §I);
two-pass verify green; category visible in the capability map.

### T7 · UPĀYA-ŚODHANA — remedy ranking & muhūrta personalization (Sonnet, effort med; Opus step-up if formula root-cause resists)
**Items:** MC-025a (flat resonance 0.49–0.53 across all 9 grahas — normalization-bug
fingerprint), MC-027.
**Files:** sidecar bo_upaya writer (locate resonance formula), `tools/retrieval/remedy_tools.ts`,
`tools/muhurta_finder.ts`.
**Work:** (1) Root-cause the flatness (suspect: a squashed/renormalized weakness feature);
after fix, priority classes must have >1 distinct value in practice; weakest_rank sourced from
T2's single authority. (2) Muhūrta scorer consumes the chart's OWN `tara_bala_natal_baseline` +
`chandra_bala_natal_baseline` (already computed) — at minimum an `avoid_notes` veto-flag when a
window's Moon-nakshatra is Vadha/Vipat/Pratyak for the native; serve intra-day sub-windows from
panchanga_daily. **Preserve** the gemstone `requires_acharya_review_flag` gating exactly as-is.
**Acceptance:** remedy resonance spread >0.15 across grahas on 482012f1 with a defensible
ordering (weakest graha ranks top-2); the register's exact failure case — a Vadha-tārā window
ranked #2 — now carries a veto/avoid note; intra-day cuts present.

### T8 · RŪPA-SAṂSKĀRA — schema trust-protection (Sonnet, effort low)
**Items:** MC-016 (proven twice — two independent endpoints made the same Mars error),
MC-015, MC-026, MC-011.
**Files:** yoga-firings serving projection in `register_p1_ganita.ts`; discoveries/projections
serving; dossier zod description.
**Work:** (1) Yoga firings expose `debilitated_planets` / `rescuer_planets` (NBRY) and
`principal_planets` / `supporting_planets` (general), derived server-side from grounds_jsonb;
keep `constituent_planets` for back-compat with a deprecation note. (2) Family-collapse dedup
for discoveries (collapse ayanāṃśa variants → one finding + cross-ayanāṃśa agreement score) and
projections (collapse by window×domain with member refs) — copy the kala_windows_get
`window_families` pattern verbatim. (3) dossier `domain` advertised required+enum.
**Acceptance:** NBRY firing for 482012f1 shows Venus+Saturn as debilitated, Mars/Sun/Mercury as
rescuers in SEPARATE fields; discoveries for domain=wealth return ≤ handful of distinct
findings each with an agreement score (was: 53 rows ≈ 2 motifs); projections deduped.

### T9 · LEKHA-PARĪKṢĀ — WL-7/8 audit (Sonnet, effort low, READ-ONLY)
**Work:** Audit the EXISTING LEL (v1.7, 65 events — it exists; the register's session couldn't
see it because its bundle LEL sub-tool errored) for financial/wealth-tagged coverage. Produce
`WL7_FINANCIAL_LEL_GAP_v1_0.md`: which of the 10-15 desired financial event classes are already
covered, which are missing — a targeted intake list for the native, NOT a blank form (the
S4-03 lesson: verify existence before soliciting). NO fabricated events, NO writes to LEL.
**Acceptance:** doc exists, every "missing" claim verified against the actual LEL file + intake
tables, cross-referenced to WL-7/WL-8.

## §4 — Swarm topology & model/effort policy

- **Conductor: Opus.** Owns Phase A dispatch, track scheduling, PV-lock polling, merge order,
  deploy, cleanup, close. Does not write feature code.
- **Builders: Sonnet by default.** Opus ONLY where flagged (T2 design, T5 design) or by
  step-up rule: **2 failed Verifier cycles on the same item → re-spawn that builder as Opus.**
  Do not pre-emptively Opus anything else — the flagged spots are where cross-layer judgment
  genuinely pays; everything else is well-specified implementation.
- **Effort dials:** default medium. Low for T8/T9 and mechanical sweeps (T1 items 2-3).
  High ONLY for T2 (build-coherence design) and T5 (contract design) and the Verifier's
  final regression pass. The output/cost balance rule: if a track's spec in §3 names the file,
  the function, and the acceptance test, it does not need high effort — it needs execution.
- **Verifier: ONE dedicated Opus agent, never writes code.** Nothing is DONE until the
  Verifier accepts against LIVE PRODUCTION (post-deploy) per each track's acceptance block.
  Four dispositions only: VERIFIED-FIXED · VERIFIED-NO-DEFECT (stale-surface artifact) ·
  PARKED-HONEST (evidence attached) · FAILED-REOPENED. No "passed with caveats."
- **Dvārapāla (gatekeeper): ONE Sonnet agent, escalation duty.** Any situation that would
  normally need the human (ambiguous rail, PV conflict at hour 6, infra credentials, destructive
  choice) goes to Dvārapāla, who makes the conservative documented decision and logs it in the
  report's `decisions[]` table. The bias: prefer PARKED-HONEST over any irreversible action.

## §5 — Rails (absolute)

1. **Untouchables:** `kala_gochara_windows` data, `build_substep_progress`, the sealed
   evaluator harness (grader, prompts, grading list — a fix that requires touching the grader
   is not a fix). The 20h gochara sweep data is NEVER invalidated, rebuilt, or migrated.
2. **PV coexistence:** root `CLAUDECODE_BRIEF.md` is NEVER modified by this campaign.
   `response_budget.ts`, `registry_bridge.ts`, `briefs/close_out/**`, and arc ledgers are
   PV-locked until A.3 releases them. No SHODHANA branch rebases over an unmerged PV branch.
3. **Git:** main is branch-protected (4 required checks, enforce_admins) — PR + auto-merge
   ONLY, never a direct push (GH006 will reject it anyway). One PR per track, small and
   reviewable; branch names `shodhana/t<N>-<slug>`; worktrees live in `.worktrees/` and are
   removed at close.
4. **Deploy:** `amjis-mcp` deploys EXPLICITLY (never implicit), after the track-set merge that
   the Verifier will test, asia-south1. Post-deploy, Verifier re-runs acceptance LIVE. Final
   state: production revision == main HEAD (the campaign is not closed until this is true).
5. **Bodha rebuild (T2):** re-link preferred; if a rebuild is unavoidable it must exclude the
   §5.1 untouchables and run with the sidecar's protection checks; Dvārapāla signs the decision.
6. **Preserve-list regression checks** after every merge (register preserve-list + positives).
7. **No fabrication, ever:** honest-empty over invented data; LEL entries are native-only.

## §6 — Verification protocol

Per-track acceptance blocks (§3) + campaign-level final battery:
1. T3's envelope battery green in CI (and stays in CI after close).
2. Sealed-harness flagship run: wealth question, naive consumer, UNMODIFIED harness — no
   regression from W7 baseline. n=2 minimum (stochastic consumer).
3. Preserve-list sweep: chart_snapshot, judgment_query decomposition, special lagnas, AV
   gating, kala_windows families, grounds_jsonb — all still serving as documented.
4. Per-MC disposition table: ALL 34 items + WL-1..8 carry one of the four dispositions with
   evidence links. This table is appended to the register (status flip to a closing state)
   and mirrored in the report.

## §7 — Close protocol

1. All PRs merged, `amjis-mcp` deployed, prod == main verified (`mcp_server_info`
   catalog_version vs repo HEAD).
2. `.worktrees/shodhana-*` removed; merged branches deleted; `git status` clean; no stray
   scratch files.
3. `SHODHANA_REPORT_v1_0.md` written to `briefs/shodhana/`: disposition table, decisions[]
   (Dvārapāla ledger), deploy revisions, battery results, cross-links: MC-005/023↔EL-36/EL-46
   (+W7.4 regression note) · MC-028/034↔EL-02/EL-14 Offer-Law amendment (4th proof — add:
   "completeness contracts must be affordable or enforced") · MC-017/008↔EL-54 class ·
   MC-010↔S4-03 class.
4. Register `LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md` status: LIVING → ADDRESSED-v1
   (append-only annotation per item; never rewrite the original observations).
5. If PV closed during the campaign: confirm no PV artifact was disturbed; if PV is still
   running at close: leave PV-locked files untouched, note in report, T3 disposition
   PARKED-HONEST with the release condition stated.

## §D — Kickoff prompt (single paste)

```
You are the CONDUCTOR of ŚODHANA (Consumption-Register Remediation), FULLY AUTONOMOUS, no human
available for the duration. Read, in order:
(1) 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_BRIEF_v1_0.md — this brief;
    §1 context and §5 rails BIND you;
(2) 00_ARCHITECTURE/llm_consumption_audit/LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md — the 34
    findings you are closing;
(3) 00_ARCHITECTURE/llm_consumption_audit/ANALYSIS_LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md —
    the cross-validation that tells you which findings are confirmed-current vs suspected
    stale-surface artifacts.
A PŪRṆA-VIRĀMA session may be RUNNING in this repo: NEVER touch root CLAUDECODE_BRIEF.md,
response_budget.ts, registry_bridge.ts, or briefs/close_out/** until Phase A.3 confirms PV has
closed (poll every 20 min; track T3 HOLDS until then). Execute Phase A (one Opus triage agent),
then dispatch tracks T1..T9 in parallel Sonnet builders in .worktrees/shodhana-t*, Opus only
where §4 flags it or after 2 failed verify cycles. ONE Opus Verifier that never writes code
accepts every item against LIVE production post-deploy — four dispositions, no "passed with
caveats". ONE Dvārapāla agent resolves any would-be human gate with a documented conservative
decision. PR + auto-merge only (main is protected); deploy amjis-mcp explicitly; finish with
production == main, worktrees/branches cleaned, SHODHANA_REPORT_v1_0.md + per-MC disposition
table merged, register annotated ADDRESSED-v1. Untouchables: kala_gochara_windows data,
build_substep_progress, the sealed evaluator harness. Wall-clock cap 8h. Truth over completion —
PARKED-HONEST with evidence beats a false close. Begin.
```

---

*The one-line version: verify which surface each defect lives on, make honesty affordable
(receipt, not catalog), make trimming respect density, say "not yet assessed" instead of
"denied," compute the one missing asset, and leave production, main, and the register telling
the same story.*
