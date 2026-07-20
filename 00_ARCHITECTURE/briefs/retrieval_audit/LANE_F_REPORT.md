---
artifact: LANE_F_REPORT.md
lane: F — Paripraśna rebuild interface (the consumer's contract)
governing_brief: 00_ARCHITECTURE/briefs/RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md §E Lane F
audit_subject: 00_ARCHITECTURE/RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md (v1.2)
primary_source: 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.5, verified 2026-07-19)
authored_by: Claude (opus, Lane F subagent) 2026-07-19
model: opus · effort: high/xhigh
status: COMPLETE
constraint: READ-ONLY on platform/** and platform-mcp/**. No source, DB, or deploy edits.
---

# Lane F — Paripraśna Rebuild Interface Audit

## §0 — Scope note and a document-identity correction

Lane F extracts every requirement the rebuilt Paripraśna/MCP **engine** imposes
on the **retrieval plane**, and cross-checks each against the Elevation Plan
v1.2. It also verifies the plan's R-3 assumption that `consult/route.ts` can
adopt the Vidhi floor without violating a settled decision (task item 3), and
raises — without resolving — every point where the two documents pull apart
(task item 4).

**Filename/version note (verification standing, per §0.5 discipline of the
source doc):** the audit-subject filename is `PARIPRASHNA_TARGET_ARCHITECTURE_
v0_1.md` but its frontmatter is **`version: 0.5`**, `verified_against_tree:
2026-07-19`. All §-citations below are to the v0.5 body actually on disk.

**The two documents describe overlapping-but-not-identical objects.** The
Elevation Plan's "retrieval plane" = registry + dispatch + envelope + budget +
planner (plan §0 diagram). Paripraśna's "engine" (§6.5) is a **superset**:
planner pipeline + agentic loop + ModelPlane + registry + capability dispatch +
v3 envelope + response budget + grounding gate + register lint + sentinel
rewrite + prediction detect. The loop / synthesis / gates half of the engine is
explicitly assigned to the **parallel Paripraśna workstream** (plan §4:
"Redesign Paripraśna's UI/streaming/render (parallel workstream)"; PARIPRASHNA
§19 P2' "loop extracted as channel-agnostic service, headless-callable"). This
seam is the root of several UNDER-SPECIFIED verdicts below: the plan legitimately
scopes itself to the plane, but the rebuild's engine-level requirements land
partly outside that scope, and the two workstreams do not cross-cite at the file
level.

---

## §1 — The Paripraśna alignment table

Verdicts: **COVERED** (plan addresses it, phase cited) · **UNDER-SPECIFIED**
(plan gestures but does not spell out the mechanism, or the mechanism lands in
the parallel workstream with no cross-cite) · **CONTRADICTED** (plan approach
conflicts with a settled decision / target need — both sides cited).

| # | Requirement (PARIPRASHNA §/decision-ID) | Verdict | Plan section/phase | Gap / contradiction detail | Severity |
|---|---|---|---|---|---|
| F-R1 | **Engine headless-callable** — no browser, no conversation row, no stream (§4/§6.5 corollary; A-07). "What makes `prashna_ask` possible at all." | UNDER-SPECIFIED | R-5.1 (`prashna_ask` "runs the same planner + loop + gates … headlessly") | The plan *consumes* headless callability at R-5 but never *builds* it. Extraction of the loop as a channel-agnostic, headless service is PARIPRASHNA P2' (other workstream); the plan neither owns nor sequences it, yet R-5 depends on it. Cross-workstream dependency with no cite in either direction. | Blocks R-5 (last phase); latent until then |
| F-R2 | **`density_contract` mandatory on every `CapabilityDescriptor`** (A-05, §8.6). | COVERED | R-1.1 (field made mandatory) + R-2.5 (populated for all 123) | Aligned. Plan even matches §8.6's "small tool" honest-default posture via §N.6 census harness. | — |
| F-R3 | **One loop, two doors — `prashna_ask`** (A-07, §6.3). T-2 (sharpened) elevates it to *load-bearing*: "the only mechanism by which the MCP channel receives the instrument rather than the database." | COVERED (with sequencing tension) | R-5.1 | Present and correctly specified as headless re-use of the same planner+loop+gates. But the rebuild's most load-bearing consumer contract is scheduled **last** (R-5), behind five phases. See Contradictions §3, C-6. | Future concern; sequencing risk |
| F-R4 | **Provenance stamp, NOT session pin** (D-16, A-10-RESTRUCTURED, §11.4): renamed; moved to immutable `conversation_messages.metadata_json`; **removed from the engine input signature** — "provenance comes out with the answer"; copied into ledger rows; the mutable shared-state construct is *deleted*. | CONTRADICTED | Plan §0 diagram ("auth → **pin** → capability → handler"); R-5.2 ("**session pin** + optional OT-6 journaling") | Plan retains the retired construct by name and by shape. R-5.2 treats the pin as *session state* — exactly the `mcp_sessions.state_json` mutable construct D-16(b) abolished. (Positive: the R-5.1 `prashna_ask` *input* contract correctly omits a pin, consistent with D-16(e).) The **name and the session-state framing** contradict a settled decision. | Blocks R-5 correctness; §0 diagram misleads earlier phases |
| F-R5 | **No `depth` / no `tier` parameter** (D-15, §13.4): "the engine signature loses `depth` and `tier`"; `ask(chart_id, question)`. | CONTRADICTED | R-5.1 `prashna_ask` contract = `{chart_id, question, scope_tuple?, depth, response_format}` | The contract carries **`depth`** as an explicit parameter — a direct violation of D-15 ("No depth parameter"). It is also redundant: `scope_tuple?` already carries depth (verified: `vidhi/types.ts:120`, `compiler.ts:4` derive depth *inside* the tuple). §13.4: "`depth` is gone because the DR-8 scope tuple already derives width, depth and horizon." The cleanest single settled-decision contradiction in the plan. See §3, C-1. | Blocks R-5 contract; cheap to fix now (paper only) |
| F-R6 | **`register` block for reader-facing labels** (A-18, §8.7, §13.6). | COVERED | R-1.1 (`register` block field) + R-2.3a (register block rides in the envelope adjacent to every internal token) | Strong alignment; the plan matches §6.4.1's suggestion to ship reader labels *in the envelope* on the raw-tools path. | — |
| F-R7 | **NO-LEAKAGE enforced four ways** (A-19, §14.10): (1) DB role sep; (2) registry flag `calibration_context_only` excluding leakage tools from every planner projection **and from `prashna_ask`'s tool set**; (3) out-of-process ledger writer; (4) CI canary "no serving-path plan can reach a leakage-flagged tool." | UNDER-SPECIFIED | R-1.1 (`mutation` class / A-04 gives arm 2 a *home*); R-5.2 (ledger channel-agnostic) | Arms 1 & 3 are data-plane/topology (out of plane scope — acceptable). But **arms 2 and 4 are squarely retrieval-plane and are not spelled out**: the plan never states that `calibration_context_only` tools are excluded from the generated projections or from `prashna_ask`'s tool set, and there is **no NO-LEAKAGE CI canary** anywhere in R-1/R-4/R-5 (R-4's CI is projection-conformance + readback battery only). PARIPRASHNA §19 puts "arms 2 and 4" in P4'. Since R-5's `prashna_ask` exposes the loop's tool set, arm-2 exclusion is a hard precondition the plan omits. | Med-high; a leakage-flagged tool could enter `prashna_ask` |
| F-R8 | **D-14 supply side** (§13, §13.6): internal register must never reach reader prose; the retrieval plane must supply (a) token labels (A-18) and (b) **reader-legible signal *content*** — because `bodha_msr_signals` has no reader-facing column (`signal_summary_text`/`signal_headline_text` are machine-internal, `migrations/325…:70-71`). §13.6: this "gates whether D-14 actually works." | UNDER-SPECIFIED | R-2.3a (token labels in envelope) | Token labels: covered. But the **signal reader-text editorial pass** (`signal_reader_text` column, generate-then-freeze, top-50 first) — which §13.6 calls "real and unowned" and gates D-14 on — is **absent from the plan** (it is PARIPRASHNA P5'). The plan's own principle 2 ("the envelope is the product on the raw-tools path") is undercut: if the *cited signal content* is internal-register machine text, a careful foreign LLM still receives internal register. See §3, C-3. | High for the raw-tools honesty claim |
| F-R9 | **Prediction-detection hooks** (§14.2): structured candidate needs `grounding_fact_ids[]`, `technique_refs[]`, window, direction, confidence, calibration lineage — "ledger-ready." | COVERED | R-2 §8.6 (timing hooks / honest `timing_anchored:false`) + R-2 §8.7 ("Standardized prediction shape: claim + window + mechanism + confidence + calibration lineage — ledger-ready on both channels") + R-2.3 (fact_ids/grades in envelope) | The plane-side supply (structured grounding + technique attribution + prediction shape) is explicitly covered. Detection *itself* (regex+classifier over the answer) is engine/synthesis, correctly out of plane scope. | — |
| F-R10 | **Engine never branches on which door** (§6.5 design test); projection selection at the **edge**, not inside the engine. | COVERED | Plan §0 ("ONE dispatch path"); R-4.1-4.2 (surface-spec + profile selection enforced **at the edge** `server.ts`) | Projection selection sits at the MCP edge per R-4; the shared dispatch path is door-agnostic. Consistent with the design test. | — |
| F-R11 | **The instrument must be able to ask — clarification as a third planner outcome** (A-29, §6.6): `PlanReceipt \| ClarificationRequest \| PlannerFault`, incl. ledger-check-before-planning for unresolved windows (§6.6.3). | UNDER-SPECIFIED | R-3 (planner unification → `PlanReceipt`) | R-3 unifies the planners but preserves the **two-outcome** shape (`PlanReceipt` / fault). It does not add the `ClarificationRequest` branch, nor the pre-plan ledger check (§6.6.3) — which §14.7 calls "the single strongest mitigation" for compliance decay. Assigned to PARIPRASHNA P2'. If R-3 hardens the two-outcome planner contract, adding the third outcome later is a re-open of the plan algebra R-3 defines. See §3, C-5. | Med; contract-shape seam |
| F-R12 | **One registry, many generated projections** (D-08 / OT-7, §8.3). | COVERED | Plan §2 principle 1; R-0.1 (rule OT-7); R-1 (projection compiler); R-4 (projections go live) | The plan's spine; fully aligned, incl. OT-7 explicitly ruled at R-0. | — |
| F-R13 | **Mutation capability class; sidecar tools pulled into registry** (A-04, §8.4). | COVERED | R-1.1 (`mutation` class); R-2.5 (all 123 through budget) | Aligned; also the home for NO-LEAKAGE arm 2 (see F-R7). | — |
| F-R14 | **D-15 forbids the plane from serving tier-differentiated content** (§13.4, A-35, §13.7 excision). What D-15 forbids: any parameter or projection that changes *what is produced* by audience. | CONTRADICTED (one live site the plan rewrites) + PARTIAL elsewhere | R-3.2 rewrites `consult/route.ts` plan block; §7.6 `verbosity` knob | (a) R-3.2 rewrites the exact `consult/route.ts` plan-assembly block that holds the **live `audience_tier` D-15 violation** (verified `:459`, `:616`; F-25g/§13.7) and is **silent on excising it** — excision is PARIPRASHNA P2'. R-3 could land the Vidhi floor and leave the tier stamp intact. (b) §7.6's `verbosity: concise\|detailed` per-call knob sits near the D-15 line — §13.4: "Budget ceilings … are an entitlement property of the caller, never a parameter of the ask." See §2 and §3, C-2/C-4. | High (a); Low-med (b) |
| F-R15 | **MCP-consult vs MCP-expert projections are NOT audience tiers** (§6.5.1: "Note this is not an audience tier (D-15) — both paths are acharya-grade … about *which mechanism* answers"). | COVERED | R-0.2 / R-4.1-4.2 (OT-10 profiles) | The plan's OT-10 profiles are consistent with §6.5.1. Nit: the plan does not carry the §6.5.1 disclaimer, so a reader could mistake MCP-consult/MCP-expert for a tier. Recommend the plan quote it. | Low (documentation) |

**Extraction count: 15 requirements.** COVERED 8 · UNDER-SPECIFIED 4 · CONTRADICTED 3 (F-R4, F-R5, F-R14a). (F-R14 is split: a live contradiction at one site + a partial elsewhere; counted once as CONTRADICTED.)

---

## §2 — R-3 verification: can `consult/route.ts` adopt the Vidhi floor without violating a settled decision?

**The plan's R-3.2 claim under test:** replace `consult/route.ts`'s hardcoded
B.11 injection with "the compiled floor + machine band from `compileContract`"
so "B.11 becomes enforced by construction on every door." The brief asks
whether this "adopts the Vidhi floor without violating any settled decision,"
traced specifically against **D-15** (no tier/depth) and **D-16** (provenance
restructuring).

**Finding: the floor-adoption mechanism is itself D-15-safe and D-16-safe — but
R-3 as written does not discharge the D-15 violation already living in the file
it rewrites, and the plan does not say it must.**

Trace, D-15 (depth/tier):
- The Vidhi compiler consumes a **scope tuple** whose `depth` is **derived from
  the question inside the tuple**, not passed as a caller parameter. Verified in
  code: `platform/src/lib/vidhi/types.ts:120` (`readonly depth: ScopeDepth`),
  `platform/src/lib/vidhi/compiler.ts:4-5,52,110` (`bandsForDepth(tuple.depth)`;
  "floor(intent) + machine_band(depth)"). This is **exactly** the shape D-15
  §13.4 blesses: "`depth` is gone [as a parameter] because the DR-8 scope tuple
  already derives width, depth and horizon from the question." So adopting the
  compiled floor **does not reintroduce a depth or tier parameter.** ✅
- **However:** R-3.2 rewrites the `consult/route.ts` plan-assembly block. That
  block *today* stamps `plan.audience_tier = isSuperAdmin ? 'super_admin' :
  'client'` — verified live at `consult/route.ts:459` and `:616` (matching
  F-25g / §13.7, a documented **live D-15 violation**, load-bearing because it
  keys prompt-template lookup at `lib/prompts/index.ts` and produces materially
  different prose per tier). **R-3 is silent on this stamp.** The excision is
  assigned to PARIPRASHNA P2' (§19: "audience_tier excision incl. prompt-template
  collapse"). Nothing in R-3 forces the two to land together. **Therefore the
  plan, as written, permits R-3 to adopt the Vidhi floor while leaving a live
  D-15 violation in the same file** — so the brief's "without violating any
  settled decision" does **not** hold at the whole-file level, even though the
  floor mechanism itself is clean. This is a coordination hazard, not a design
  flaw in the floor. Raised as C-2.

Trace, D-16 (provenance / session pin):
- R-3 does not touch the provenance stamp / session pin. Floor adoption reads
  the scope tuple and emits a `PlanReceipt`; it neither pins session state nor
  reads a mutable pin. **R-3 is D-16-clean.** ✅ (The D-16 contradiction lives in
  R-5.2 and the §0 diagram — see C-1-adjacent, F-R4 — not in R-3.)

Trace, entitlement (D-15 "budget ceilings are an entitlement property"):
- The scope tuple carries `entitlement`; the plan's R-1.5/§1.5 entitlement work
  (fail-closed dispatcher, entitlement check on `plan_retrieval`) is consistent.
  No new tier surface introduced. ✅

**R-3 verdict:** the Vidhi-floor adoption is architecturally sound and does not
by construction reintroduce tier/depth or the mutable-pin shape. The one real
hazard is **omission, not commission**: R-3 edits the block that carries the
live `audience_tier` stamp and does not require its removal, while the removal is
scheduled in a different workstream's phase. Recommend R-3's gate explicitly
absorb the F-25g/§13.7 excision (or explicitly hand it off with a blocking
cross-cite), so the floor cannot land D-15-dirty.

---

## §3 — Contradictions raised (item 4 — raised, not resolved)

Formatted per PARIPRASHNA §18 discipline (handoff §8 rule 8). Each states the
problem and both positions; **none is adjudicated here.** Each carries a pointer
into `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` for the native.

### C-1 — `prashna_ask` carries a `depth` parameter that D-15 abolished

**The tension.** Elevation Plan R-5.1 specifies the `prashna_ask` contract as
`{chart_id, question, scope_tuple?, depth, response_format}`. D-15 (settled
2026-07-19) removed `depth` and `tier` from the engine signature entirely; §13.4
states the reduced signature `ask(chart_id, question)` and explains `depth` is
derived inside the scope tuple, not passed.

**Position A (plan).** `depth` is a useful explicit knob on the composite MCP
door; a caller may want to request shallow vs deep. (Note: the plan likely
inherited this from PARIPRASHNA's own §6.1 topology diagram, whose Door-2 box
still reads `prashna_ask (chart_id, question, depth)` — a stale pre-D-15
artifact inside the target doc itself.)

**Position B (settled decision).** D-15 / §13.4: no depth parameter, full stop;
the scope tuple already derives depth from the question, and `scope_tuple?` in
the very same contract makes `depth` redundant as well as forbidden. Serving a
depth knob reintroduces "plain language means a lesser reading," the false
assumption D-15 tore down.

**Pointer:** `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §1/D-15, §13.4, and the
stale §6.1 Door-2 diagram (which should also be corrected).
**Not resolved here.**

### C-2 — R-3 rewrites the `audience_tier` block but does not excise it

**The tension.** R-3.2 rewrites `consult/route.ts`'s plan-assembly path to adopt
the Vidhi floor. That path carries the live `audience_tier` stamp
(`:459`, `:616`, verified) — a documented D-15 violation (F-25g / §13.7) whose
excision is assigned to PARIPRASHNA P2', a *different* workstream/phase. The two
edits touch the same block and neither cites the other.

**Position A (plan boundary).** The Elevation Plan scopes itself to the plane
and explicitly defers Paripraśna-internal excision to the parallel workstream
(plan §4). R-3 item 2 is "a consumption change inside `consult/route.ts` only."

**Position B (settled decision + hazard).** D-15 is binding and the violation is
*live in the exact lines R-3 rewrites*. A floor adoption that lands without the
co-located excision ships a D-15 violation through a phase that touched the file.
"Enforced by construction on every door" (plan principle 4) is not true while
super-admin vs client still get different prompt templates two lines away.

**Pointer:** `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §13.7 (the 14-site
excision table, three load-bearing), §16.1/F-25g. **Not resolved here.**

### C-3 — "The envelope is the product on the raw-tools path" vs the missing reader-facing signal text

**The tension.** Plan principle 2 and R-2 make the v3 envelope the *entire*
epistemic defense on the raw-tools path (correctly, per §6.4.1). But the cited
signal *content* in `bodha_msr_signals` has no reader-facing column — only
machine-internal `signal_summary_text` / `signal_headline_text`
(`migrations/325…:70-71`). §13.6 says this "gates whether D-14 actually works"
and calls it "real and unowned." The plan supplies token *labels* (R-2.3a) but
not signal *prose*.

**Position A (plan).** Register labels adjacent to internal tokens (R-2.3a) plus
the `reading_contract` header (R-2.3b) make the envelope self-describing; a
careful foreign LLM can read grades/coverage and label the tokens.

**Position B (target doc).** §13.6: without a `signal_reader_text` column
(generate-then-freeze editorial pass, top-50 first), the citation card's text
"has to come from somewhere," and today that somewhere is internal-register
machine text. The plan's principle-2 defense is therefore incomplete on its own
terms — the reader-text pass is in PARIPRASHNA P5' but in **no** Elevation-Plan
phase.

**Pointer:** `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §13.6, §16.6 ("Reader-
facing signal text — ABSENT"). **Not resolved here.**

### C-4 — `verbosity` request knob vs D-15 "never a parameter of the ask"

**The tension.** Plan §7.6 wires a `verbosity: concise|detailed` request knob
through `density_contract` (an Anthropic token-control pattern). §13.4 states
budget ceilings "are an entitlement property of the caller, **never a parameter
of the ask**."

**Position A (plan / industry consult).** `verbosity` is output-length token
control, an orthogonal axis to reading *quality/depth*, and a documented
frontier-vendor pattern; it does not change *what is produced*, only how much
prose is emitted.

**Position B (settled decision).** D-15 is categorical about ask-parameters that
modulate output; a per-call verbosity knob is close enough to a depth/tier
parameter that it must be reconciled against §13.4 explicitly rather than
assumed orthogonal. If "concise" produces a materially thinner reading, it is a
depth axis wearing a token-budget costume — the §13.4 warning.

**Pointer:** `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §13.4 (final paragraph).
**Not resolved here.**

### C-5 — R-3's unified planner preserves two outcomes; the rebuild needs three

**The tension.** R-3 unifies the planners into a `PlanReceipt`-emitting pipeline
(two outcomes: receipt or fault). PARIPRASHNA A-29/§6.6 requires a **third**
planner outcome — `ClarificationRequest` — plus a pre-plan ledger check for
unresolved prediction windows (§6.6.3), which §14.7 calls the strongest
compliance-decay mitigation.

**Position A (plan boundary).** Clarification is an engine/Paripraśna concern
(P2'), not a retrieval-plane concern; R-3 correctly unifies only the plane's
planner.

**Position B (target doc).** R-3 *defines the unified plan algebra* (§9.5 says
this algebra is the hard 70% of the unification). Hardening it as two-outcome
now means adding the third outcome later re-opens the very type R-3 froze. The
outcome set is a plan-algebra decision, so it belongs in R-3's scope even if the
clarification *UX* does not.

**Pointer:** `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §6.6, A-29, §9.5.
**Not resolved here.**

### C-6 — The load-bearing consumer contract (`prashna_ask`) is sequenced last

**The tension.** PARIPRASHNA T-2 (sharpened) and §6.4.1 elevate `prashna_ask`
(A-07) to *load-bearing* — "the only mechanism by which the MCP channel receives
the instrument rather than the database," and the native is the heaviest MCP
user. PARIPRASHNA §19 moves capture/engine work forward precisely to de-risk
early. The Elevation Plan schedules `prashna_ask` in **R-5**, the final phase,
behind headless extraction it does not own (F-R1).

**Position A (plan).** Dependencies are strictly forward; `prashna_ask` needs
the unified catalog (R-1), envelope (R-2), and planner (R-3) beneath it, so it
*must* come late. R-5 is the honest dependency order.

**Position B (target doc).** PARIPRASHNA §19.1 fault 1 is "the core bet was
validated last"; T-2 makes `prashna_ask` a core bet. If the headless engine
boundary (F-R1) does not survive contact with reality, five phases of plane work
were shaped around an unvalidated consumer contract — the exact failure mode
§19 restructured to avoid. A thin `prashna_ask` spike earlier (even over the
un-elevated plane) would de-risk the boundary the way PARIPRASHNA P0' de-risks
render.

**Pointer:** `PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md` §18/T-2, §6.4.1, §19.1.
**Not resolved here.**

---

## §4 — Notes on internal staleness in the target doc (for the reconciler)

Two of the contradictions above (C-1 depth, F-R4 session-pin) trace to the
target document's **own** un-updated §6.1 topology diagram, which still shows
`prashna_ask (chart_id, question, depth)` and "session pin … pinned for ALL
conversations" — both superseded by the later settled decisions D-15 and D-16 in
the same document. The Elevation Plan appears to have inherited these from the
diagram rather than the decision rows. Per PARIPRASHNA §0.6, where the plan
conflicts with a settled decision the **decision governs**; the diagram is a
defect in the source doc and should be corrected there too (out of Lane F's
write scope — flagged for the reconciler / native). This is precisely the T-7
decay pattern the source doc warns about, recurring one layer down.

---

## §5 — Model / effort ledger

| Item | Value |
|---|---|
| Model | `opus` (opus-4-8[1m]) — per brief §E Lane F "strongest model, high effort" |
| Effort | high / xhigh (judgment-heavy lane) |
| Sections read (PARIPRASHNA v0.5) | §0–§1.1 (full decision registers D-01…D-18, A-01…A-36), §2 (OT-1…OT-10), §4+§4.1 (topology/invariants), §5–§5.2, §6.1–§6.6 (all request paths, engine boundary, three-path lifecycle, OT-10, "instrument must ask"), §7.4 (NO-LEAKAGE grants), §8.1–§8.7 (registry/projections/register block — full), §9.1–§9.6 (planner pipeline, acharya floor), §10.1–§10.2 (model plane, partial), §13.4–§13.9 (register separation, D-15, audience_tier excision, remedy/emotional register), §14.1–§14.10 (prediction/calibration loop, NO-LEAKAGE four arms), §16.1–§16.6 (forensic appendix — full), §18/T-1…T-8 (tensions — full), §19.1–§19.3 (sequencing) |
| Sections read (Elevation Plan v1.2) | full document, §0–§8 incl. all R-0…R-5 items, §7 industry amendments, §8 strategy amendments |
| Code confirmations (READ-ONLY) | `consult/route.ts:459,616` (audience_tier live — F-25g/§13.7 holds); `vidhi/types.ts:120` + `vidhi/compiler.ts:4-5,52,110` (depth derived inside scope tuple — R-3 floor D-15-safe); `prashna_ask` grep across `platform` + `platform-mcp` → zero hits (unbuilt; R-5 contract is paper, so `depth` is catchable now) |
| Time split | ~70% judgment (requirement extraction from a 3,215-line living design; verdict adjudication; R-3 settled-decision trace; contradiction framing) · ~30% mechanical (section paging, three grep confirmations, table assembly) |
| Guesses / silent resolutions | none — every contradiction raised, not adjudicated; no genuine conflict silently resolved |
| Constraint compliance | READ-ONLY honored; only file written is this report |

*End of LANE_F_REPORT.md — Lane F (Paripraśna rebuild interface), opus/high, 2026-07-19.*
