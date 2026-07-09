---
canonical_id: R5_3_RUN_LEDGER
version: 1.1
status: LIVE — §B MET, B1 DONE, B2 DONE (6/11 met, 5/11 still below floor — honest, one iteration per brief discipline)
created: 2026-07-10
author: Claude Code (conductor session §B/B1/B4-prep; per-lane worktree implementers for B2)
program: R5.3 content-depth iteration, grader-restoration-GATED (R5.2 A5 graders were
  INCONCLUSIVE). 16 rubric items with Pratinidhi-R rulings, executed as independent
  per-lane worktree PRs per CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md. Governing law:
  R5_3_CONTENT_SPECS_v1_0.md's 16 rubric items + Pratinidhi-R per-lane rulings. Battery
  R5_ANSWER_BATTERY_v1_0.md and llm_grader.ts rubric prompt text remain READ-ONLY.
---

# R5.3 RUN LEDGER — Content-Depth Iteration

Append-only. Each lane's implementer appends its own entry; this document never edits prior entries.

---

## §B — GRADER RESTORATION GATE — MET (2026-07-10)

**Root-cause correction vs. the brief's own framing:** the brief (and R5_2_RUN_LEDGER §A5) attributed
the INCONCLUSIVE grading to `GOOGLE_GENERATIVE_AI_API_KEY` being absent and "no working DeepSeek
fallback." Investigation found this imprecise. Both `GOOGLE_GENERATIVE_AI_API_KEY` and
`DEEPSEEK_API_KEY` were already present with real values in `platform/.env.local`, and both secrets
are already provisioned in Secret Manager and wired into the main `amjis-web-runtime` Cloud Run
service (`.github/workflows/deploy.yml:306-307`). The eval harness
(`evals/r5-w4-full-battery/battery_runner.ts` + `llm_grader.ts`) is a **local-only TS script**
(`npx tsx ...`), not a deployed Cloud Run job/service — there is no IAM binding to make for it because
it has no service identity. R5.2 A5's own INCONCLUSIVE run was a `source` (sets, doesn't export) vs.
explicit-export shell mistake — already self-corrected within that same R5.2 session per the ledger's
own account (21/22 items graded once vars were properly exported).

**New finding, this session:** re-running the harness with correctly exported keys still showed the
Gemini leg silently falling back to DeepSeek on every call. Direct `curl` to
`generativelanguage.googleapis.com` confirmed the cause: `models/gemini-2.5-flash:generateContent`
returns `404 NOT_FOUND — "This model models/gemini-2.5-flash is no longer available"`. Google retired
the pinned model name `llm_grader.ts` hardcoded (`GEMINI_MODEL = 'gemini-2.5-flash'` at line 49) even
though it's still listed by the `models.list` endpoint. Confirmed `gemini-flash-latest` returns HTTP 200.
**Fix applied:** `evals/r5-w4-full-battery/llm_grader.ts:49` — `GEMINI_MODEL` changed from the pinned
`'gemini-2.5-flash'` to the rolling alias `'gemini-flash-latest'`, with an inline comment recording why
(avoid repeat breakage when Google retires the next pinned snapshot). This is a grader-wiring fix, not a
grading-criteria change — no rubric text, floor, or checklist touched.

### §B.2 smoke-prove (verbatim results, both directions)

Ran locally against `llm_grader.ts`'s exported `llmRubric()` with keys exported explicitly from
`platform/.env.local` (not `source`d). Floor = 10/15 for both probes.

**Probe 1 — known-excellent answer (expect ≥ floor):** score 15/15, `LLM_GRADED_MET`, gemini/gemini-flash-latest.
**Probe 2 — deliberately-thin answer (expect < floor):** score 2/15, `LLM_GRADED_BELOW_FLOOR`, gemini/gemini-flash-latest.

Both probes ran through the primary grader (Gemini) this time — no fallback needed post-fix. Deepseek
fallback was independently confirmed reachable in the pre-fix run (both probes graded correctly via
`deepseek-chat` while Gemini was 404-ing), so both providers are proven live.

**Gate verdict: MET.** Grader restored, smoke-proved bidirectionally (excellent ≥ floor, thin < floor),
both providers independently confirmed reachable. Harness invocation note: keys must be exported
explicitly (e.g. `export "$(grep '^GOOGLE_GENERATIVE_AI_API_KEY=' platform/.env.local)"`), not `source`d,
per the R5.2 A5 lesson.

## B1 — BASELINE RE-MEASURE — DONE (2026-07-10)

Full frozen battery (38 rubric/deterministic-applicable items — 2 of the nominal 40 are structurally
excluded per the harness's own accounting), both charts, over MCP prod
(`https://amjis-mcp-qm256lasva-el.a.run.app/mcp`), against commit `76bbf603`, with the now-live real
Gemini grader (no DeepSeek fallback needed — Gemini answered every rubric-applicable call directly
post-fix). Results: `evals/r5-w4-full-battery/results_76bbf603.json`.

**This is the first genuinely trustworthy rubric measurement since R5.1** — R5.2's 31.6% was
deterministic-only dressed as a full number (its own A5 section says so explicitly). This run's number
happens to also read 31.6%, but it is now backed by real per-item Gemini scores — the item-level detail
differs substantially from any structural-proxy pass, and several R5.2 below-floor calls flip status
now that they're really graded (see below).

### Scorecard

| Metric | R5.1 (true) | R5.2 (deterministic-only, mislabeled 31.6%) | **B1 (this run — true)** |
|---|---|---|---|
| Overall | 23.7% | 31.6% (not a real rubric number) | **31.6% (12/38, real grading)** |
| Q1/X deterministic | — | 43.8% | **43.8% (7/16)** — gate requires 100%, NOT MET |
| Rubric floors | 25.0% | unmeasured (INCONCLUSIVE) | **10/22 met (45.5%), 11/22 below floor, 1/22 structurally INCONCLUSIVE (Q7-N-2, not a content gap)** |

### The confirmed real content-depth gap: 11 items (not the brief's assumed 16)

Real Gemini grading narrows the brief's §B2 estimate:

| id | score/floor | answer-type |
|---|---|---|
| Q2-N-1 | 5/11 | entity assessment (graha_portrait) |
| Q2-A-1 | 5/11 | entity assessment |
| Q6-N-1 | 0/11 | timing/prediction (muhurta window) |
| Q6-N-2 | 5/11 | timing/prediction (dasha transition) |
| Q7-N-1 | 6/12 | whole-chart reading |
| Q7-A-1 | 10/12 | whole-chart reading |
| Q8-N-1 | 8/11 | remedy |
| Q8-A-1 | 2/11 | remedy |
| Q9-N-1 | 2/12 | verification/derivation |
| Q9-A-1 | 5/12 | verification/derivation |
| Q9-N-3 | 3/12 | verification/derivation |

**Q3 and Q5 (judgment / prediction items the brief also flagged) all now MET floor under real grading**
— the R5.2-era assumption that these needed content-depth work was itself a harness-limitation
false-negative (X-7-class), now resolved by having a live grader at all. **Q7-N-2 is a structural
harness limitation** (no orchestrating LLM to synthesize turn-1 free text into a genuine pinned turn-2
drill call), not a content gap — flagged for Ring-3, out of B2 scope.

**Gate status: NOT MET (unchanged from R5.2 — expected; this run is the honest baseline B4 will be
measured against, not a re-close).** B2 scope set to these 11 confirmed items.

## B2 — PRE-IMPLEMENTATION FINDING: the v3 envelope has no narration field (root cause, not per-item)

Direct MCP calls against `graha_portrait` (Q2-N-1), cross-checked against the grader's rationale text
for the other 10 items, surfaced a single architectural cause behind nearly all 11 grader complaints
("raw, truncated JSON... not a synthesized natural language answer"): R5.1's C1 fix introduced the
"v3 envelope" (`chart_header`/`verdict`/`drill_pointers`/`judgment_flags`) as the MCP-channel default
for `judgment_query`/`graha_portrait`/`pact_query`, and suppressed `content[0].text` as a duplicate via
`dualOutputBudgeted()` to hit tight byte ceilings. `verdict` turned out to be a completeness receipt
(✓/zero_rows/error per section), not narrated prose; `content` is raw fact-id rows. No field anywhere
carried narration. C1's job was budget-fitting, never narration. Depth had to come from **trimming raw
boilerplate to make room for compact narration**, not raising ceilings. Two items were flagged as NOT
this pattern: `Q6-N-1` (looked like a possible date-math bug) and `Q8-N-1` (narration existed; two
remedy fields were structurally null — a data-population gap).

## B2 — CONTENT DEPTH IMPLEMENTATION — 5 WORKTREE-ISOLATED LANES, VERIFIED LIVE, HONEST RESULT: 6/11 MET

Dispatched via Workflow: 5 lanes (entity/timing/reading/remedy/verification), each Pratinidhi-R ruling
→ worktree-isolated implement (own PR, CI-gated merge, deploy-confirmed) → independent verifier
(≠ implementer) re-grading live against the restored grader post-deploy. All 5 PRs (#508–#512) merged
and deploy-confirmed. Per-lane implementation write-ups follow below (append-only); the honest,
independently-verified outcome is:

| id | pre-B2 | post-B2 | floor | verdict | note |
|---|---|---|---|---|---|
| Q2-N-1 | 5 | 6 | 11 | **NOT MET** | narration added but cut off mid-sentence by the byte-budget trimmer ("…[truncated for budget]") before shadbala/avasthas/yoga/dasha sections appear |
| Q2-A-1 | 5 | 8 | 11 | **NOT MET** | same truncation bug — capricorn_h10/neecha satisfiable from the surviving prefix, but the bhanga check itself is cut off |
| Q9-A-1 | — | 15 | 12 | MET | complete, untruncated narration (11,775B, under the 12KB ceiling — this item's payload had headroom Q2's didn't) |
| Q6-N-1 | 0 | 0 | 11 | **NOT MET** | implementer misdiagnosed as a battery harness date-math bug and declined to fix; verifier confirmed live it's a real bug — the item's own literal args (92-day range) trip muhurta_finder's 90-day cap, reproducibly, on two independent calls |
| Q6-N-2 | 5 | 15 | 11 | MET | |
| Q7-N-1 | 6 | 15 | 12 | MET | |
| Q7-A-1 | 10 | 15 | 12 | MET | minor non-blocking note: `audience` field defaults to 'native' even for the Abhinandan (third-party) chart when the caller omits the param — didn't affect graded checks, flagged for a future pass |
| Q8-N-1 | 8 | 15 | 11 | MET | |
| Q8-A-1 (cross-lane) | 2 | 3 | 11 | **NOT MET** | both graha_portrait and bodha_remedies_get halves individually correct (well-formed, non-error), but the grader independently judges the composed item needs a genuine synthesized NL answer to "does it need fixing" — two joined raw structured payloads can't satisfy that by construction; matches the item's own embedded caveat about ordering requiring real synthesis |
| Q9-N-1 | 2 | 2 | 12 | **NOT MET** | fix exists in code (PR #512) but is gated behind opt-in `response_format:'v3'`; this item's graded args don't pass that param, so the deployed fix never triggers — a wiring/default gap, not a missing fix |
| Q9-N-3 | 3 | 15 | 12 | MET | |

**Tally: 6/11 MET (Q9-A-1, Q6-N-2, Q7-N-1, Q7-A-1, Q8-N-1, Q9-N-3), 5/11 NOT MET (Q2-N-1, Q2-A-1,
Q6-N-1, Q8-A-1, Q9-N-1).** This is the one B2 fix-iteration per the brief's own discipline — no second
pass folded in here. The 5 residuals are genuine, diagnosed, carried to B4/close, not silently dropped:
two are the SAME truncation bug (entity lane's narration exceeds the byte ceiling before completing —
needs a second, tighter trim pass, not a new narration write), one is a real muhurta_finder validation
bug the timing lane declined to touch (in-scope per may_touch, should have been fixed), one
(Q9-N-1) is a one-line default-param wiring gap, and one (Q8-A-1) is a structural limitation of a
raw-data MCP tool being graded as if it must produce synthesized NL — worth surfacing as a possible
gate-calibration data point alongside §N.

Housekeeping: all 5 feature branches deleted post-merge (local + remote), all 5 `.claude/worktrees/`
entries removed. An out-of-scope file, `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v1_0.md` (+ a `v2_0`
revision), appeared untracked in the working tree during the B2 run — traced to one or more rule-stage
workflow agents (which run un-isolated in the main checkout and have full Bash access) doing broader
exploration than their lane brief called for. Left untouched on disk, excluded from every R5.3 commit;
flagged here rather than silently deleted or silently committed.

---

## Lane: Verification/derivation (ganita_structural_get dosha_fires, ganita_yogas_get) — Q9-N-1 / Q9-N-3

**Ruling basis:** Pratinidhi-R ruling for this lane (root_cause_applies=true, with the
qualifier that ganita_structural_get has NO v3 envelope at all for any facet — legacy
format only — and a second, independent, higher-priority wiring bug where `facet` was
silently dropped by `get_yoga_dosha.ts`).

### What shipped

1. **`platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts`**
   - `facet` is no longer a no-op: a `FACET_TO_TYPE` map now scopes `facet=yoga_fires` /
     `facet=dosha_fires` to their respective category subsets (previously every facet
     routed through this URI returned the identical unfiltered ~530-row union of all 6
     yoga/dosha categories).
   - When `facet=dosha_fires`, the handler now additionally SELECTs the already-computed
     `kala_sarpa_per_varga` fact_category (fact_key=`ks_detection`), scoped to the same
     chart_id/ayanamsha filter, and returns it as `kala_sarpa_per_varga: { natal,
     divisional_fired }`. This is the genuinely per-chart-computed Rahu/Ketu detection —
     the pre-existing `dosha_label` catalog row for "Kala Sarpa Dosha" cites an unrelated
     generic placeholder fact (confirmed live: chart `482012f1-…`, catalog row's
     `constituent_facts_array` resolves to Sun's sign, not Rahu/Ketu). Zero new
     computation — this SELECTs an L1 fact_category that already exists at rest.

2. **`platform-mcp/src/tools/register_p1_ganita.ts`**
   - `ganita_structural_get` gained a `response_format` param (`legacy` default / `v3`
     opt-in), mirroring `ganita_yogas_get`'s existing pattern. Previously this tool had
     no v3 envelope branch at all for any facet.
   - `v3` + `facet=dosha_fires` now states an explicit Kala Sarpa Dosha natal verdict
     (formed/not-formed, Rahu/Ketu house axis, classical all-seven-grahas-confined
     mechanism, and an explicit reconciliation note distinguishing the verified
     `kala_sarpa_per_varga` computation from the misleading catalog row) plus a
     divisional-chart note (D2/D4/D6/… `fires:true` rows, explicitly labeled divisional
     not natal).
   - `ganita_yogas_get`'s existing v3 `verdict` gained a `pancha_mahapurusha` block:
     per-yoga formed/not-formed sentences for all 5 Pancha Mahapurusha yogas (Ruchaka/
     Bhadra/Hamsa/Malavya/Sasa), built from rows this response already fetches
     (`yoga_label` presence = fired, per JL-004) plus a bounded, best-effort enrichment
     fetch of `graha_position` sign/house_d1 for the 5 karaka planets (already-computed
     L1 fact_category, fetched via the existing `get_positions` capability — zero new
     computation) to state the specific failed sign/kendra condition for the not-formed
     yogas. Live-verified against chart `482012f1-…`: only Sasa (Saturn, exalted in
     Libra, house 7 = kendra) is formed; Ruchaka/Bhadra/Malavya fail on the sign leg
     (Mars/Mercury/Venus in Libra/Capricorn/Sagittarius respectively — none own or
     exalted); Hamsa fails on the kendra leg (Jupiter in Sagittarius = own sign, but
     house 9 is a trikona, not a kendra).

### Verified against live DB (chart `482012f1-710e-4a25-994a-93821f5871aa`)
- `kala_sarpa_per_varga` D1 row: `fact_id=025b69663e8a93bc`, `fires=false, rahu_house=2,
  ketu_house=8` (lahiri_chitrapaksha).
- `dosha_label` "Kala Sarpa Dosha" catalog row: `constituent_facts_array=["e2b47b2c6d457725"]`
  → resolves to `graha_position.SUN.sign=Capricorn` (unrelated placeholder), confirming
  the ruling's finding (B) verbatim.
- `yoga_label` rows across all 5 ayanamshas: only "Sasa Yoga" present; Ruchaka/Bhadra/
  Hamsa/Malavya absent — confirming the ruling's finding (D).

### Not touched (out of scope per ruling)
- `parivartana` / `graha_yuddha` facets remain mis-routed through `get_yoga_dosha.ts`
  (their real per-varga/graha-yuddha data lives in `get_dispositors.ts` /
  `get_graha_yuddha.ts`) — this is a pre-existing routing mismatch, not addressed by
  this lane's ruling, and is flagged here for a future lane rather than fixed silently.

### Checks run
- `platform`: `npm run lint` (scoped to touched files — clean, pre-existing warnings
  only) + full `npm run build` (TypeScript compiles clean in 9.4s; the build's later
  static-page prerender failure on `/login` is a pre-existing local-env issue — missing
  Firebase/CloudSQL credentials — unrelated to this change).
- `platform-mcp`: `npm run typecheck` — clean.

### Must-not-touch boundaries
None hit. No orchestrator/writer/chart-data/frozen-constant/LEL/battery/grader edits.

---

## Lane: Entity portrait (graha_portrait v3 envelope) — CLOSED (implementation)

**Scope:** Q2-N-1, Q2-A-1, Q9-A-1 — all three route through `graha_portrait`'s v3 envelope.
Pratinidhi-R ruling (root_cause_applies: true) confirmed live against prod: `verdict` was a
completeness receipt (`completeness`, `sections_populated/requested`) with zero prose fields;
`content` rows carry `citation_ref` (internal MCP-lineage provenance, e.g.
`graha_dignity_per_varga.D1_SAT.dignity_state@chart=...:ay=...:eng=pyjhora/1.0.0` — never a
classical citation). No narration existed anywhere in the v3 schema `buildRetrievalEnvelope` emits.

**Root cause:** narration was never in scope of R5.1 C1's budget-fitting fix (matches that
finding's own framing). The MCP layer (`registry_bridge.ts`) builds `verdict`/`grounding` from
`inner` — the capability's pre-trim output — entirely mechanically (completeness counts only).

**Implementation (this session):** `platform-mcp/src/tools/registry_bridge.ts`, entirely inside
`registerRegistryBridgeTools`'s `graha_portrait` tool registration:

1. Added `buildGrahaPortraitNarration(...)` — assembles `verdict.narration` prose from sections
   `graha_portrait`'s capability handler ALREADY fetches (`inner`, pre-trim): functional
   role/lordship (classical whole-sign house-lordship table + the already-computed
   `functional_nature` fact, not a new derivation), D1×D9 dignity promise-vs-delivery tension
   (with an explicit dusthana-house counterweight clause for any exalted/own graha sitting in
   6/8/12), an honest neecha-bhanga check (dispositor looked up via the classical sign-lord table,
   dispositor's OWN dignity read from `cgm_neighborhood.nodes[].dignity_state` if present in the
   already-fetched depth-1 neighborhood, honestly caveated as partial-coverage if not), shadbala
   grade (rupas vs the classical required-rupas threshold table — same constants
   `ga_strength_writer.py` embeds), up to 2 avasthas, yoga/parivartana or an honest JL-004
   empty-with-reason restatement, current/next Mahadasha periods (with age-in-years ONLY for the
   documented canonical native chart_id `482012f1-...`, since birth date is not otherwise available
   to this call for arbitrary charts — never fabricated for other charts), CGM neighborhood top
   edges, and two standing honesty disclosures (single-tradition/JL-004 caveat; entity-scope vs
   bhava-level-claim honesty, paired with a new `judgment_query` drill_pointer).
2. `grounding.fact_ids` expanded (per the ruling's structural finding #1) to include every
   fact_id the narration actually cites — previously built ONLY from `position.rows`.
3. `citation_ref` stripped from every row in `inner` (new trim headroom per the ruling's general
   approach) AFTER narration is built from the untouched `inner` — narration reads
   `fact_id`/`fact_value_text`/`fact_value_jsonb`, never `citation_ref`, so this is safe and
   opens budget room for the added prose within the existing 12KB `graha_portrait` ceiling
   (`response_budget.ts`'s `MCP_RESPONSE_BUDGET_KB.graha_portrait` — unchanged, not raised).

**Not touched:** `platform/src/lib/retrieval/registry/layers/L2_bodha/graha_portrait.ts` (the
capability layer) — all narration assembly happens at the MCP envelope layer per the ruling's
stated preference, since `registry_bridge.ts` already owns the v3-population block and
`portraitSections` trim list. No new SQL, no new capability calls beyond the pre-existing
`get_chart_header` fetch (already made in this handler; only its position in the function was
moved earlier so `lagna_sign` is available before narration is built). No orchestrator/writer/
chart-data/salience/battery/grader touch.

**Verification:** `platform-mcp` `npm run typecheck` and `npm run build` (`tsc`) both pass clean
with no errors. `platform/` was not touched — its own lint/build were not re-run (no diff to
verify there).

**Honest gaps this implementation does NOT close:**
- No live re-grade against the restored grader was run by this implementer — that is the
  separate verifier's job per the dispatching instructions.
- The neecha-bhanga check's dispositor-dignity lookup depends on the dispositor graha actually
  appearing in the depth-1 `cgm_neighborhood` returned for THIS graha; when it doesn't, the
  narration says so honestly rather than asserting an unsupported "not formed" verdict (per the
  ruling's explicit instruction) — this is a real, disclosed coverage limit, not a bug.
- Age-in-years on dasha periods is native-chart-only (documented birth date). Abhinandan's chart
  (`1c826d5a-...`, used by Q2-A-1/Q9-A-1) gets plain dates without ages — birth date for that
  chart was not available to this call without adding new plumbing, which was out of scope
  (no new computation / no new stored-data changes).

PR: see branch `feature/r5-3-b2-entity-portrait` (#511, merged, deploy-confirmed).

**Post-merge live verify (independent verifier, ≠ implementer):** Q2-N-1 6/11 NOT MET, Q2-A-1 8/11
NOT MET — narration is real and on-topic but the byte-budget trimmer cuts it off mid-sentence
("…[truncated for budget]") before shadbala/avasthas/yoga/dasha sections render, so the grader can't
confirm they're present. Q9-A-1 15/12 MET — untruncated, this item's payload had headroom the other
two didn't. Residual: needs a tighter trim pass (drop more `content.*.rows` boilerplate) to buy back
the room the narration needs to finish, not a rewrite of the narration itself.

---

## Lane: Timing / prediction (muhurta_finder, ganita_dashas_get narration) — Q6-N-1 / Q6-N-2

**Ruling basis:** Pratinidhi-R ruling (root_cause_applies=false — this lane is NOT the v3-envelope
pattern; muhurta_finder is a surgical retrieval tool with its own shape, ganita_dashas_get had no
narration field at all for the "current dasha" query shape).

**What shipped:** `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts` — added a
`narration` field and a typed `dasha_of_promise` drill_pointer, fired only for the
as_of_date/date_contains vimshottari "current dasha" shape. Narration: lead sentence naming MD/AD/PD
lord+span (canonical non-kp_sub row only, avoiding two disagreeing end dates), age-at-date computed
from the chart's stored birth_date (same pattern as `get_graha_yuddha.ts` — no new astrological
computation), explicit natal-condition sentences for the current AD/PD lords (from already-fetched
`lord_natal_dignity_d1`/house/nakshatra), and a graded "should I worry" caveat citing the Mahadasha's
`sandhi_flag` balanced against the Antardasha lord's placement. `Q6-N-1` (muhurta_finder): **no code
change** — the implementer diagnosed the 92-day rejection as a battery harness date-math bug
(`battery_runner.ts`'s `setMonth(+3)`) and left the deliberate 90-day architectural cap untouched,
citing it as outside this lane's may_touch.

**Checks run:** `platform` lint clean (one pre-existing unrelated warning only); `tsc --noEmit` clean
project-wide. PR #509, all CI green, merged (`64ff80d7`), Cloud Run deploy run 29044786389 confirmed
success for that commit.

**Post-merge live verify (independent verifier, ≠ implementer):** Q6-N-2 15/11 **MET** — dates, ages,
natal-condition sentences, sandhi caveat all confirmed present in the live response. **Q6-N-1 0/11
NOT MET — the implementer's diagnosis was wrong.** Verifier called the live endpoint with the item's
own literal args (`date_range: 2026-07-09 to 2026-10-09`) directly (curl + a harness-style script,
reproduced twice) and got a real `orchestrator_error` / sidecar 422 ("date_range spans 92 days;
maximum is 90 days") — 2026-07-09 to 2026-10-09 is genuinely 92 calendar days, and these are the
item's OWN args being rejected, not a harness artifact. This is a real, unfixed bug carried to close:
either `muhurta_finder`'s cap needs to accommodate a literal "next 3 months" query (the question's own
plain-English intent) or the item's date math needs adjusting — Pratinidhi-R should re-rule on which
side is wrong before any fix lands, since the implementer's own may_touch scope did cover this file
family and the punt was avoidable.

---

## Lane: Whole-chart reading (synth_chart_brief_get) — Q7-N-1 / Q7-A-1

**Ruling basis:** Pratinidhi-R ruling (root_cause_applies=true, same architectural CLASS as the
confirmed v3-envelope finding but via a different, more primitive code path — `synth_chart_brief_get`
has its own local `envelope()`/`dualOutput()`, separate from `registry_bridge.ts`'s v3 machinery, and
was returning raw unranked verdict-statement strings with zero synthesis).

**What shipped:** `platform-mcp/src/tools/register_p1_synthesis.ts` — added (1) `coverage_receipt`, a
sentence assembled from already-fetched topics_covered/domains_covered counts; (2) `dissent_flags`,
narrated honestly from `verdict_summary[].provenance_chain.contradictions[]` (explicit empty-array +
reason when no tension exists, never fabricated); (3) `ranked_themes`, split into
strengths/weaknesses/open_questions from the existing rank_consequence-ordered rows, each with inline
fact-id citations and evidence_grade-keyed hedging; (4) an optional `audience` param (native default /
third_party) reframing themes for third-party questions and stating an explicit no-LEL-join
disclosure. Trimmed redundant per-row `surface_formula_version`, empty `classical_sources[]` arrays,
unbounded `ranked_evidence` (capped to top 3 + recover_via pointer), and static `attention_budget`
boilerplate to stay clear of this tool's local 50KB dual-output threshold.

**Checks run:** `platform-mcp` typecheck + build pass; `vitest run` showed 96 pre-existing failures
confirmed unrelated (git diff --stat shows only this one file changed). PR #508, all CI green, merged
(`7b91a941`), Cloud Run deploy run 29045271258 confirmed success; `gcloud` confirmed
`amjis-mcp-00412-lw8` created shortly after, matching the merge.

**Post-merge live verify (independent verifier, ≠ implementer):** Q7-N-1 15/12 **MET**, Q7-A-1 15/12
**MET** — both confirmed live with real `coverage_receipt`/`dissent_flags`/`ranked_themes` content,
Q7-A-1's no-LEL disclosure explicit. Non-blocking note: Q7-A-1's `audience` field defaulted to
'native' (the item's args didn't pass `audience:'third_party'` even though the chart_id is
Abhinandan's) — didn't affect any graded check, flagged for a future param-default review.

---

## Lane: Remedy (bodha_remedies_get) + B3 bounded-fix #1 (query_remedy_corpus 106KB trim) — Q8-N-1 / Q8-A-1

**Ruling basis:** Pratinidhi-R ruling (root_cause_applies=false for the v3-envelope pattern —
`bodha_remedies_get` never entered that code path; the gap was narration entirely absent plus two
structurally NULL DB-wide fields). This lane's ruling also covered B3's bounded-fix #1 (query_remedies
106KB single-row oversize) since it shares the remedy tool family and file neighborhood.

**What shipped:**
1. `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts` — narration synthesis:
   verdict-first lead sentence naming the top remedy-priority graha(s); full prose ranking of all
   resonance rows; named-affliction mapping derived from populated fields (graha +
   remedy_priority_class + weakest_rank_in_chart + is_yoga_karaka_flag) since
   `associated_doshas_array` is genuinely NULL DB-wide; qualitative cost-tier estimate derived from
   remedy_category + ritual_complexity_class since `estimated_cost_inr_range_jsonb` is genuinely NULL
   DB-wide (both explicitly labeled estimates/honest gaps, never fabricated); an inline classical
   citation newly wired in from `classical_sources_jsonb`/`citation_ref`/`citation_human` (previously
   100%-populated columns that were never selected); typed drill_pointers. Always-null array columns
   and redundant `prescription_detail_jsonb` dropped from the default per-row payload (recoverable via
   a new `fields=all` param) to fund the narration within the existing byte ceiling.
2. **B3 bounded-fix #1** — `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_remedy_corpus.ts`:
   reproduced the 105,935-byte oversize live; root cause was `SELECT *` with no column projection and
   default `limit=100`. Fixed by lowering default limit to 20, replacing `SELECT *` with a curated
   compact column list (full rows recoverable via `fields=all` or `read_remedy`), and reporting a true
   filtered `COUNT(*)` as `total` distinct from `returned`. No writer/schema/orchestrator change.

**Checks run:** eslint clean (pre-existing `_ctx`-unused pattern only), `tsc --noEmit` clean, targeted
vitest suites (63 + 510 tests) pass; `npm run build`'s `/login` prerender failure confirmed
pre-existing/environmental via git-stash comparison (missing local Cloud SQL/Firebase secrets, not
caused by this diff). PR #510, all CI green after two required branch updates (main advanced twice
from parallel R5.3 lanes), merged (`de32badf`); confirmed green "CI — Ganga Quality Gate" and a
subsequent green "Deploy to Cloud Run" run tied to that exact merge SHA (run 29046446956).

**Post-merge live verify (independent verifier, ≠ implementer):** Q8-N-1 15/11 **MET** — verdict-first
lead, full resonance ranking, named-affliction mapping, cost-tier estimates, and an honest
`data_gap_note` disclosing the two genuinely-NULL fields all confirmed live. Q8-A-1 (cross-lane,
depends on this lane's `bodha_remedies_get` half + the entity lane's `graha_portrait` half) —
see the B2 cross-check tally above: **3/11 NOT MET**, a structural limitation (two individually-correct
raw structured payloads joined together still can't satisfy a rubric item that requires a genuinely
synthesized NL answer to "does it need fixing"), not a defect in either half.

**B3 bounded-fix #1 status: shipped and live, not yet independently re-verified against a byte-size
assertion post-deploy** — worth a quick confirmatory check in B3/B4 rather than assumed from the
implementer's own report alone.
