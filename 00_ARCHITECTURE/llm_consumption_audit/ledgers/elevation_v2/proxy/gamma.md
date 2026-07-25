# Native-Proxy ruling log — Stream γ (PŪRṆA)

Per charter §10 / M2.10, this is the append-only proxy ledger for Stream γ. Every entry below is a
ruling the Stream-Conductor made in place of asking the (absent) human, per charter §10's authority
(may rule on anything except weakening §0, fabricating data, or ratifying in the native's name).

---

## PROXY-RULED-001 — 2026-07-25 10:30 IST — α/β heartbeat gap does not block γ's start

**Situation:** At Phase-1 kickoff, `~/elev-v2-shared/heartbeat/alpha.hb` does not exist at all;
`beta.hb` was last written 04:54 IST (`status: starting`), >5h stale against the 10-minute M2.7
cadence. No `STREAM_ALPHA_COMPLETE.flag` / `STREAM_BETA_COMPLETE.flag` exist, so M2.7's succession
precondition ("alpha.hb >45min stale AND both sibling completion flags exist") is not literally met
— succession does not trigger.

**Ruling:** This is read as "α/β have not yet reached their own heartbeat-emitting stage" rather than
a stalled/dead process requiring lock-breaking-style intervention, since the charter's M2.2
break-only-when-stale rule is written for *locks*, not for absent heartbeat files, and inventing an
analogous break procedure for heartbeats would risk prematurely asserting close-succession that §9/M2.7
do not authorize this early. γ proceeds immediately with its own Phase-1 lane work (§7.2's "never idle"
rule) rather than waiting on siblings. Re-check scheduled ~30-45 min out; if still absent/stale at that
point, log a follow-up PROXY-RULED entry. This ruling does not touch any published contract and is
γ-scoped only — no CONTRACT_STATUS.md amendment required.

---

## PROXY-RULED-002 — 2026-07-25 10:35 IST — C7 deadline overrun acknowledged, not backdated

**Situation:** T0 (per charter §8, "all four sessions pasted together") is back-computed at roughly
03:50-04:00 IST from the Phase0_COMPLETE.flag write time (05:53 IST) and the charter's ~2h Phase-0
budget. C7's deadline (T0+4h) is therefore roughly 07:50-08:00 IST. Wall-clock at first read of
CONTRACT_STATUS.md was 10:25-10:35 IST — the deadline has already passed by roughly 2.5-3h before γ's
session reached Phase-0 validation and mandatory reading.

**Ruling:** The overrun is logged honestly here rather than silently backdated or ignored. Root cause:
γ's own session did not exist/launch until after T0 (consistent with OPEN QUESTION §K.1 — no evidence
α or β launched promptly either). C7 authorship is now γ's immediate first concrete action, published
within minutes of this entry. No charter mechanism defines a formal "missed deadline" disposition for
a contract (unlike the merge-lock's 30-min ceiling or Phase-0's 3h ceiling) — γ treats "as soon as
possible, honestly timestamped" as the correct behavior, consistent with §0's anti-silent-omission
spirit applied to process, not just data.

---

## PROXY-RULED-003 — 2026-07-25 10:40 IST — second Ω-Verification flagship domain = career

**Situation:** Charter §2 criterion 4 requires repeating Ω-Verification on "a second domain (career or
marriage)" without committing to which; γ has ordinary engineering-decision latitude here per §10.

**Ruling:** **career** is selected as the second flagship domain (alongside wealth, which is fixed by
§2 criterion 1). Rationale: `assess_career` exists as a peer MCP capability to `assess_wealth` with
comparable L1-L5 surface depth (dasha capability, yoga firings, divisional charts D10/D1, professional
timing windows), and Lane E's register entries (EL-44/45) already anchor wealth-tool defects as the
primary named example — using career as the second domain gives Ω2/Ω3/Ω8 two structurally different
domains (financial vs. professional-timing-heavy) to prove the TCI/relevance-map/completeness-contract
machinery generalizes, rather than two domains that would exercise near-identical primitives. Marriage
was considered and rejected only for scope-pacing reasons (marriage compatibility synastry work is a
larger surface addition) — not for any classical or technical deficiency; this can be revisited if
career proves structurally too similar to wealth once Ω1/Ω2 are built.

**Downstream commitment:** wealth + career are the two domains that MUST reach the C7 allowlist
(`ledgers/contracts/C7_ENFORCED_SCOPE.json`) before γ may signal complete, per §9/Ω3.

---

## PROXY-RULED-004 — 2026-07-25 (verifier baseline received) — Ω1 gate denominator adjudications

**Situation:** The independent Stream-Verifier's ground-truth baseline (see
`00_ARCHITECTURE/llm_consumption_audit/ledgers/OMEGA1_INDEPENDENT_BASELINE_v1_0.md`) surfaced five
findings (F-1..F-5) where the charter's gate language ("≥1 entry per bodha_mechanisms class, dasha
system, varga and ayanamsha") is ambiguous against what's actually materialized in the live DB for
the two canonical charts. Left unresolved, these are exactly the "false-success path" the charter
names as the campaign's single highest risk.

**Rulings (binding on the Ω1 generator and the sanity gate, full detail in the baseline ledger):**
1. fact_category gate = 218 global, never chart-scoped (216/211 are both wrong denominators).
2. bodha_mechanisms gate denominator = 10 documented design classes (from the writer's enum), not 4
   DB-materialized classes. The 6 absent-for-these-charts classes get real TCI entries marked
   `not_computed_globally`/`empty_for_this_chart` — omitting them entirely would itself be the silent
   omission §0 forbids.
3. ayanamsha gate denominator = 5 real ayanamshas; `INVARIANT` is a tagged sentinel entry, excluded
   from Lane I's `n/6`-style cross-ayanamsha agreement math (which becomes `n/5`).
4. dasha systems gate = the 9 DB-built systems, not `ref_dasha_systems_get`'s advertised list
   (`shodashottari` is documented but unbuilt — a β/compute gap, not γ's to fabricate around).
5. Thin-row vargas (D30, D81) are present-but-sparse, not absent — no exception needed.

**Authority basis:** engineering/gate-definition latitude under §10; none of these rulings weaken the
§0 100%-accounting mandate — if anything, ruling 2 makes the gate *stricter* (10 required entries,
not 4) precisely to prevent a false pass. Relayed directly to the Ω1 builder agent to avoid rework.

---

## PROXY-RULED-005 — Ω4 "not weaker than plan_retrieval's fallback" — interpreted as signal-superset, not literal routing-parity

**Situation:** Charter Ω4 requires the new `intent_classify` deep-default classifier to be "not weaker
than `plan_retrieval`'s keyword fallback." The Ω4 builder found the existing fallback (`scope_resolver.ts`)
has no narrow branch at all — it routes 100% of questions to deepdive, including 3 false-positive
bare-house-ordinal cases from the frozen routing suite's narrow-labeled items. Taken completely
literally, "≥ fallback" is either vacuous (fallback is maximally deep, trivially not-weaker) or
actually incompatible with earning genuine narrow routing (which is Ω4's whole point, and required by
its own symmetric-precision acceptance criterion).

**Ruling:** accept the builder's resolution — "not weaker than fallback" means the new classifier's
deep-push signal vocabulary is a strict superset of the fallback's real life-domain keyword coverage
(verified per-suite-item, 0 violations reported), so Ω4 never regresses a case the old fallback
correctly routed deep, while additionally gaining genuine, precision-checked narrow routing the old
fallback never had. This is the only reading under which the charter's own two Ω4 acceptance bullets
(zero deep-misroutes AND ≥90% narrow precision) are simultaneously satisfiable. Does not weaken §0.

---

## PARKED-HONEST — Lane E rank-vocabulary cross-manifest fix point (EL-59/20)

**Situation:** Lane E's "one rank vocabulary everywhere" sub-item names a specific regression: Venus
is `weakest_rank_in_chart: 5` in one tool vs. "weakest of 7 by shadbala" in prose elsewhere. The
builder traced the actual regression to `platform/src/lib/retrieval/registry/layers/L2_bodha/
query_remedies.ts` and `query_rm_resonances.ts` — both **outside γ's manifest** (α's `L2_bodha/**`
territory, γ only owns `register_d8_assess_domain.ts` within the registry layers).

**Disposition:** PARKED-HONEST, blocked-on-α (M2.9 — cross-manifest conflicts are never
opportunistically edited by the non-owning stream). γ built and shipped the canonical fix point —
`platform/src/lib/retrieval/ranking/rank_vocabulary.ts` (`RankStatement`, `rankGrahasByShadbala()`)
— wired into γ's own `register_d8_assess_domain.ts`, and documented as the import target for whoever
(α, or a later pass) reconciles the two out-of-manifest files. This is not a γ-lane failure — Lane E's
in-manifest deliverable (the vocabulary itself + its use in assess_domain) is complete; only the
cross-file reconciliation is parked.

---

## ADDENDUM (post-close) — α's follow-on fix attempt re-measured, disposition CONFIRMED unchanged

**Situation:** after γ's close, α merged+deployed PR #782 ("wire assess_wealth/assess_career through
dossier's completeness") — a good-faith attempt at exactly the gap γ diagnosed and handed off. γ
re-verified live rather than let the closed ledger go stale on an outdated claim.

**Finding:** the fix is real and deployed (revision `amjis-mcp-00475-d2t`, confirmed) and adds a
genuine `domain_completeness` accounting block (slice_size/accounted/pct/coverage_map/full_hydration
pointer) to `assess_wealth`/`assess_career` — but it supplies a *pointer*, not the missing concepts'
*substance*. Worse, the response-budget trimmer strips `coverage_map` to `[]` and truncates the
directive under real budget pressure, so even the pointer degrades on the wire. A fresh sealed-harness
naive consumer explicitly noticed "a full wealth dossier is available" and chose not to fetch it,
treating the reconciled headline as sufficient. **Score: 2/13, flat against the pre-fix baseline.**

α's own commit message had already flagged this as an open question rather than a claimed fix
("whether it moves the flagship acceptance score... will be measured for real in Phase 4, not
asserted here") — consistent, honest cross-stream engineering discipline on both sides.

**Disposition:** γ's `STREAM_GAMMA_COMPLETE.flag`/ledger claim (`flagship_self_verified: false`,
§2 NOT MET) is CONFIRMED, not revised — no ledger re-open needed, since the new data point supports
rather than changes the existing honest disposition. Refined root cause for whoever continues: closing
this gap needs either the missing concepts served inline (not just pointed to) or the coverage_map/
directive surviving the response budget so a consumer has something concrete enough to act on, or a
consumer-side push (not just an available pull) toward the dossier follow-up.

---

## Ω6 findings CMN-1/CMN-2 reclassified — these are γ's own Ω1 TCI, not cross-manifest

**Situation:** the Ω6 builder found two real, narrow defects in the Ω1 TCI it read (already merged
into elev/gamma): (CMN-1) mechanism-class `row_count_per_canonical_chart` is summed across all 5
ayanamshas while the live serving tool defaults to one (lahiri), so TCI counts read as exactly 5×
the servable count without a flag explaining why; (CMN-2) the contradiction-pole concept's
`serving_tool` points at `bodha_quality_get` (a scorecard summary) rather than
`bodha_graph_subgraph_get` mode=contradictions (the tool that actually serves the pole rows). The
builder labeled both PARKED-HONEST "α/β/Ω1 territory" — incorrect: Ω1 is γ's own lane, not
cross-stream. There is no manifest conflict here.

**Ruling:** not PARKED-HONEST. Tracked as a documented, non-blocking TCI refinement (already captured
faithfully in `OMEGA6_MECHANISMS_COVERAGE_v1_0.json`, so §0's no-silent-omission bar is met — the gap
is visible, not hidden). Deferred rather than hot-patched into the already-Verifier-PASSED 16MB TCI
artifact under time pressure — a surgical follow-up patch (annotate `is_ayanamsha_summed`, repoint
one `serving_tool` field) is safe to do in a later pass without re-running the full Ω1 sanity gate,
since it doesn't change any counted value the gate checks, only metadata/pointer accuracy. Does not
affect the C7 wealth/career allowlist promotion (those accounting runs used the row_count values as
recorded, which are correct sums — CMN-1 is a documentation/interpretation gap, not a counting error).
**Update:** Ω5's builder independently found a third such TCI `serving_args` refinement (see below,
tagged for Ω8) — bundling these into one Ω8 follow-up patch rather than three separate ones.

---

## NATIVE-RULED-001 — scoped server.ts manifest exception for dossier wiring (supersedes M2.9 for this item only)

**Ruling (from the native, not a proxy self-ruling):** `platform-mcp/src/server.ts` is in NO
stream's §4 manifest — a charter gap, not a boundary to respect by parking. γ is granted a scoped,
recorded exception to edit `server.ts` for the SOLE purpose of registering the dossier tool
(import line + registration call, following the existing `register_server_info.ts` pattern at
server.ts lines 125/376) — nothing else in that file. Correction to my earlier report: the wiring
work is mostly IN-manifest — `registerDossierTool(server)` itself belongs in `dossier.ts` (γ's own
file); only the minimal two-line server.ts touch is the actual cross-manifest exception, now
explicitly granted.

**Directed follow-through:** take the merge lock, rebase, PR `elev/gamma`→`main` via auto-merge,
deploy `platform-mcp` (Cloud Run `amjis-mcp` — does not auto-deploy on main merge, unlike
`platform`), confirm revision/image-SHA live, write `implementations/DOSSIER.live`, THEN re-run
Ω7's dark-corpus report and the §2 flagship self-verification against LIVE PRODUCTION (not
worktree/localhost) on both domains and both charts. **Explicit instruction: if the dark-corpus
number is still low after this, report it as a real finding — do not adjust the harness or replay
set to manufacture a better number.**

**EXECUTED — outcome (2026-07-25 ~10:40 IST):**
- PR #773 (`elev/gamma`→`main`) merged (commit `48156bd3`), all CI gates green.
- `platform-mcp` auto-deployed (turns out it DOES auto-deploy on main, contrary to the native's
  stated expectation — verified via `gcloud run services describe`: revision `amjis-mcp-00473-6lh`,
  100% traffic, and independently confirmed via GH Actions run 30154555933's "Build & Deploy MCP"
  job = success). `implementations/DOSSIER.live` written (correction pending — see below).
- **Live functional probe: dossier PASSES on production, identically to the verified worktree
  build** — all 4 domain×chart combinations (wealth/career × both canonical charts), correct page
  counts (≤6@16KB, ≤2@64KB), `composition_scaffold` structurally absent on every BLOCKED page,
  monotonic coverage reaching exact slice_size only on the final page. Confirmed by a fresh agent
  via raw JSON-RPC `tools/call` against the live endpoint (its MCP client's cached tool list was
  stale and didn't show `dossier`, so it bypassed the client and hit the HTTP endpoint directly).
- **§2 flagship self-verification re-run: NOT materially improved.** A genuinely fresh sealed-harness
  consumer asked "How is my wealth?" against 482012f1 still routed to `assess_wealth` (~2/13 ≈ 15%
  of frozen required concepts hit, far below the 0.90 bar) — because **nothing surfaces `dossier` to
  a naive consumer**: (a) this session's MCP connector never received a `tools/list_changed` refresh
  after the deploy, so `dossier` isn't even in the callable list; (b) `plan_retrieval`'s wealth-deepdive
  floor (live, checked) does not name `dossier`; (c) even with a fresh tool list, an untold-what-to-do
  naive agent has no reason to pick an unfamiliar tool named "dossier" over the obviously-named
  `assess_wealth`. One partial positive: `intent_classify` now correctly routes `depth: deep` (Ω4's
  fix, confirmed live) — the uncertainty-routes-deep half of the fix works; the discovery half does
  not yet. **Dark-corpus is honestly reported as essentially unchanged from Ω7's original finding.**
- **Correction to DOSSIER.live:** its `image_sha` field recorded the git merge-commit SHA
  (`48156bd3…`), not the container digest (`sha256:22fed7d5…`) gcloud actually reports — a labeling
  imprecision, not a deploy-mismatch; the deploy is still correctly verified (GH Actions built and
  pushed the image FROM that exact commit). Will amend the field name/value for accuracy.
- **Next action taken:** since the remaining gap (planner discovery) is squarely in γ's own manifest
  (`platform/src/lib/vidhi/**`), not cross-stream, dispatching a fix rather than stopping at
  "reported" — wiring `dossier` into the wealth/career deepdive floors so plan_retrieval actually
  recommends it. This is NOT gaming the metric (no touching of the harness/replay set/grading logic)
  — it is closing the real, in-manifest routing gap the honest re-run surfaced.

**PLANNER-WIRE FIX — built, independently Verifier-PASSED (simulation-level via direct
`compileContract` invocation), merged (`elev/gamma`), PR #775 → `main` merged, `platform-mcp`
redeployed (revision `amjis-mcp-00474-bh5`).**

**FINAL LIVE RE-VERIFICATION (2026-07-25 ~13:10 IST) — the honest, final answer:**
A fresh agent established genuine live-production connectivity (raw JSON-RPC against the deployed
Cloud Run endpoint, using the `marsys-jis-direct` connector's own configured api_key — not a new
credential, not a bypass) and confirmed two things definitively:
1. **`plan_retrieval` now surfaces `dossier` live, not just in simulation** — a live call for chart
   482012f1 returns `floor[0] = {primitive_id: "full_domain_dossier", live_tool: "dossier",
   hard_floor: true}`. The planner-wire fix is genuinely deployed and working exactly as designed.
2. **The sealed-harness naive consumer's real behavior is UNCHANGED — 2/13 frozen concepts, same as
   before the fix.** A genuinely fresh, uninstructed sealed-harness agent asking "How is my wealth?"
   never calls `plan_retrieval` at all, and could not discover `dossier` even if it tried —
   `tool_search("dossier")` on the live server returns only unrelated hits, and `dossier` is absent
   from the naive consumer's exposed MCP tool catalog. It defaults straight to `assess_wealth` +
   `judgment_query`, exactly as before.

**Root cause, now precisely diagnosed:** the gap is NOT in plan_retrieval's floor (fixed, confirmed
live) and NOT in Ω4's routing depth (fixed, confirmed live — `intent_classify` correctly returns
`depth: deep`). It is **upstream, at tool-catalog discoverability**: a naive consumer never calls
`plan_retrieval` in the first place, and even a tool-searching agent can't find `dossier` by name
through the server's own `tool_search` index. Closing this requires either (a) making `dossier`
appear in the served MCP tool catalog / `tool_search` index prominently enough that a naive agent's
own tool discovery surfaces it, or (b) having the default domain-assessment entrypoints
(`assess_wealth`/`judgment_query` themselves, which ARE what a naive consumer reaches for) inline or
route through dossier's density. Both of these touch `platform-mcp/src/lib/**` and/or the MCP
catalog/tool_search infrastructure — **outside γ's manifest, α's territory.**

**DISPOSITION: §2 flagship acceptance is honestly `NOT MET` at this campaign checkpoint, on a
precisely diagnosed and now-documented root cause, not a vague or hand-waved gap.** γ's own
in-manifest work (Ω1-Ω8, dossier build+deploy, planner-floor wiring) is complete and independently
verified end-to-end, live, at every layer γ owns. The remaining distance to §2's numeric target is a
cross-manifest, α-territory tool-discoverability problem — correctly PARKED-HONEST, not something γ
can close by editing more of its own files. This will be stated exactly this way in the final
STREAM_GAMMA_COMPLETE ledger — `flagship_self_verified: false`, with this full diagnostic chain
attached so the next session (α's Phase-4 revalidation, or the native) has the precise next action
already identified rather than having to re-derive it.

---

## Lane F caught-and-corrected finding — narayana dasha IS present on the native chart

Lane F's builder initially reported "narayana dasha never materialized — 8 systems live, not 9" as an
EL-33 finding, and encoded it into a test mock. The Verifier independently ran the exact live query
and found narayana genuinely present on `482012f1` (9 systems, matching the original Ω1 baseline
exactly) — the gap is real but chart-scoped: absent only on `1c826d5a` (8 systems there). Routed back
to the builder for a fix (correct test mock + correct any written claims) before this merges. Logged
here as a working example of the adversarial-Verifier discipline catching a wrong finding before it
propagated into the campaign's shared record — exactly what the Verifier role exists to do.

---

## Ω5 finding — TCI serving_args key mismatch for the dominant wealth serving tool (tag: Ω8-fixup)

**Situation:** the Ω5 dossier builder found that Ω1's TCI records `serving_args: {fact_category: ...}`
for `ganita_chart_facts_get` (the tool serving ~12,200 of wealth's 12,450 `served` concepts), but the
live tool's actual parameter name is `category`, not `fact_category`. A caller following the TCI's
drill handle verbatim would pass the wrong param name and get unfiltered results instead of the
intended filtered slice. `bodha_signals_get`'s handle was checked and matches live exactly — this is
isolated to the one tool.

**Disposition:** not PARKED-HONEST (this is γ's own TCI, not cross-manifest) and not blocking — Ω5's
engine faithfully surfaces the TCI's `serving_args` as-is (correct behavior: it doesn't invent a
correction), so dossier output is honest even with the upstream metadata bug. Tagged **Ω8-fixup**
(floor/serving-args reconciliation is explicitly Ω8's charter scope) alongside the CMN-1/CMN-2 items
above — bundled into one follow-up TCI-metadata patch rather than three uncoordinated edits.
**Resolved:** Ω8 applied this fixup, independently Verifier-confirmed (0 corruption, C7 unaffected).

---

## CRITICAL — Ω7 dark-corpus numbers are pre-dossier-integration; flagship criterion 2 does not
## currently pass in live production, and this is expected, not a failure to hide

**Finding:** Ω7's dark-corpus report (measured via 42 real consumer transcripts against the frozen
replay set, chart 482012f1) found wealth dark=11,755/12,450 served-non-empty (5.58% coverage),
career dark=11,400/12,455 (8.46% coverage) — nowhere near charter §2 criterion 2's "zero unserved
non-empty concepts." This is the honest, currently-true state of live production.

**Why this is expected, not a regression:** Ω7 necessarily measured naive single/few-tool-call
consumer behavior through the CURRENTLY LIVE serving path — which does not yet include Ω5's
`dossier` tool, since MCP registration in `server.ts` is outside γ's manifest and PARKED-HONEST
blocked-on-α (logged under Ω5 above). Ω5's dossier is independently Verifier-proven to reach
structural 100% accounting for wealth/career (6 pages @16KB, 2 pages @64KB) — but that mechanism
is not yet reachable by a naive one-turn question in production. The gap between "servable" (Ω5,
proven) and "actually served today" (Ω7, measured) is real, large, and precisely what Ω7 exists to
surface — not a defect in Ω7's measurement.

**Consequence for flagship self-verification (§2):** criterion 2 (`dark_corpus_report(wealth,
482012f1)` = zero) will be dispositioned honestly against LIVE PRODUCTION as currently measured,
not against what Ω5 could theoretically achieve once wired. Criterion 1 (naive "how is my wealth?"
routes deepdive + 100% accounting) and criterion 3 (≤3-call reproduction with greater coverage) are
similarly gated on dossier's live wiring. Expect the honest overall flagship disposition to be
`PARKED-HONEST` or `PREPARED-FOR-NATIVE` rather than `VERIFIED-CLOSED` unless α's server.ts wiring
lands and is re-verified before this campaign's close — this will be stated plainly in γ's final
ledger, not smoothed over. §0 forbids exactly this kind of silent gap.

---
