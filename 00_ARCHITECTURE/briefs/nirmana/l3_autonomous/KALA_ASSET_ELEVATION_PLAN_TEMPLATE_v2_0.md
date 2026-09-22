---
artifact: KALA_ASSET_ELEVATION_PLAN_TEMPLATE
canonical_id: KALA_ASSET_ELEVATION_PLAN_TEMPLATE
version: "2.0"
status: CURRENT
date: 2026-09-22
supersedes: KALA_ASSET_BRIEF_INSTANTIATION_GUIDE_v1_0.md (retained; its §2–§12 remain the brief's internal shape)
role: >
  The elevation PLAN for one Kāla asset or asset group — the arc from where it stands today to
  terminal acceptance — with the brief as one gated stage inside it. v1.0 answered "what must a
  brief contain"; v2.0 answers "how is an asset elevated, what value is extracted, and how is it
  made efficient without losing quality." Binding guide, not a fifth authority: every requirement
  names the document that imposes it.
governing: Product v3 · VA v2 · F01–F28 · L3 Strategy + Execution Brief · ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT · skill A–J · W0 records
changelog:
  - "2.0 (2026-09-22): six-stage plan; six lenses v1.0 lacked (value extraction, target-state design, efficiency-with-quality, synergy obligations, consumer walkthrough, knowledge-time); three shape adaptations; explicit unblocked/held status."
  - "1.0 (2026-09-22): brief instantiation guide."
---

# Kāla asset elevation plan — template v2.0

## §0 — What v1.0 lacked, and why it matters

The v1.0 guide told a session how to write a conformant brief. It did not tell it how to **find
the value**, how to **make the asset efficient without cheating**, or **where the brief sits in
the arc**. A conformant brief that elevates nothing is a waste of a native ruling. Six lenses are
added (§2). Each cites the authority that already demanded it.

## §1 — The six stages

| # | Stage | What happens | Exit gate | Records it | Today |
|---|---|---|---|---|---|
| 0 | **Reconcile** | Inherit the existing per-asset records (contribution-register row; CURRENT_STATE §4.1 row + W0 disposition; field-register partitions; Strategy §6.1 row; W0 fences); state only the deltas since | One page "already established", cited not re-derived | brief §2 | **Open** |
| 1 | **Frame the value** | Which L3-Q01–Q13; the distinction earned (Product §1.3, F03); the simpler baseline (Brief §1); the ablation; the *latent-value register* (§2.1) | A named distinction with a falsifiable test | brief §3–§4 | **Open** |
| 2 | **Brief** | `ASSET_INTERFACE_EXECUTION_BRIEF_CONTRACT` §1–§8 | `PROPOSED_FOR_NATIVE_RULING` → native → `APPROVED_FOR_EXECUTION` | the brief | **Open** |
| 3 | **Source elevation** | Implement the delta against accepted upstream *contracts*; focused tests; disposable-DB proofs; independent review at exact tip (Layer contract §9 tests) | Source packet accepted → `PRODUCER_READY` | terminal evidence packet (contract §8) | **Open** — W0 §8 item 3 authorizes it while W1 is held; precedent `47131772b` |
| 4 | **Physical data** | Bind one compatible transitive vector (Strategy §4 step 3); build candidate partitions; independently verify; publish the complete compatible generation (FOUNDATION_SAFETY §6) | `DATA_ACCEPTED` | generation manifest + receipts | **HELD** — W1 ← RI-01 ← production cutover (DP-SD-020: backup/restore proven, cutover not executed) |
| 5 | **Integrate · deploy · value** | Receiving operators consume the fields (L3-U packets); deployed revision; simpler-baseline comparison (VA §12.2) | `CONSUMER_INTEGRATED` → `DEPLOYED_ACCEPTED` → `VALUE_EVALUATED` | receipts; **no admissible event type yet for the first and last** (native decision 2) | Held |
| 6 | **Terminal** | One accepted rebuild; independent verification; freeze — or a non-build disposition with applicable proof (skill terminal rules) | t3 `FROZEN`; counts in Accepted N/22 | ledger `asset_frozen` under `t3-2026-09-11-8b884eac` | Held |

A session's scope names the stages it is authorized for and stops at that gate (Foundation §9.9).
Stages 0–2 in one session; stage 3 in a separate execution session with an independent reviewer
(contract §7 — builders never certify themselves).

## §2 — The six lenses v1.0 lacked

### 2.1 Value extraction — the latent-value register (VA annex; skill lens D)
For every material field or computation, classify: **(a) persisted but discarded by consumers;
(b) computed but discarded before persistence; (c) a genuine source/computation gap;
(d) available but unqualified for the intended use.** These need four different fixes. A brief
that lists fields without this classification has not found value; it has found columns. Then ask
the offensive question VA §10.3 asks: *which missing entities, relationships, variants,
applicability conditions, negative cases, precision levels or comparison operators would unlock a
meaningful new consumer capability?* — each with a named consumer, basis, cost and test.

### 2.2 Target-state design — from consumer obligation to ideal producer (VA §5; skill §5)
Do not start from the asset and ask what to fix. Start from the L3-Q it serves and the Strategy §3
object it should emit (*Contact*, *Clock interval*, *Temporal testimony*, *Engagement route*,
*Interval/trajectory segment*, *Search coverage*, *Comparison/election*, *Publication handoff*).
Write the ideal producer for that object. Then measure the gap to the field register's actual rows.
The gap, ranked, is the elevation.

### 2.3 Efficiency with quality — every speed proposal carries its equivalence contract (Strategy §5)
Order of attack is fixed: *"Optimize repeated preparation, scalar inner loops, redundant searches
and dense storage BEFORE trading away time resolution or method coverage."* Use the three physical
representations where justified — shared global astronomy under exact conventions; chart-specific
bindings as complete lossless intervals; dense samples only where an operator requires them, with
explicit coverage/error bounds. Every proposal states its **equivalence or qualification contract**
(same finite-value policy, float/rank/ties, full shift set, denominators) and the pre/post
output-identity method. *"A top-K cutoff cannot establish that no window exists."* *"Reduced caps
cannot pass as equivalent."* No measured hotspot → justified no-change (DP-SD-019 §6). Cite the W0
benchmark baseline and `KALA_COST_PROFILE_v1_0.md`; never `estimated_seconds` (F28).

### 2.4 Synergy obligations — what the asset owes the layer and receives from it (VA §13.3 item 3)
Two lists, each edge with its F12 operator role: **owes** (which downstream asset or served tool
consumes which field, and what distinction it needs — not "reads"); **receives** (which upstream
field at which grain, and where richness is lost on the way in). Name the seams where identity,
grain, independence or silence dies (Lane E's five are the model). An asset elevated in isolation
that leaves its seams unchanged has not been elevated synergistically.

### 2.5 Consumer walkthrough — one Product §9 experience end to end
Pick the §9 experience the asset most serves (4 · temporal landscape; 5 · choice comparison;
7 · forecast review; 1 · first encounter) and walk it: what the person asks → what reaches synthesis
today → what would reach it after elevation → what the person can now distinguish that they could
not before (§1.3). If the honest answer is "nothing new reaches them," the elevation is internal
plumbing and must say so. Include the ordinary-period case (§9: not only dramatic yogas).

### 2.6 Knowledge-time and event-free discipline (F15, F17, DP15a, Strategy §6.2)
For any time-producing asset: pin event time vs knowledge time vs publication time; rectification
and L5 weight inputs are *separately admitted immutable artifacts*, never live L4/L5 table reads;
a rebuildable projection never owns or rewrites issued claims or observations; "an earlier
timestamp does not make an event-derived posterior admissible under the event-free contract."

## §3 — Three shapes, one plan

**Single asset** — the plain arc.
**Group** (Gochara family) — before stage 2, a group layer: which members are briefed
independently and which share a packet; the shared-table fences (W0 register fences 1–3: `_v2`
shared by gen2/century; `kala_gochara_windows` shared by sweep v1/century v3; shared build state);
one writer and one publication owner per packet; the group's served product and which member owns
it. Generation-blind mutation across shared tables is a correctness defect, not a style choice.
**Staged internal DAG** (`ka_kshetra`) — the frozen stage plan (FOUNDATION_SAFETY §6 item 5:
`S0 + S2 → S3 → S1 → S4 → S5 → S6 → S6.5 → S8 → snapshot`, direct S0 into S4) *is* the packet
boundary; a stage is briefed and accepted as a unit; populated-chart replacement is held until W7
regardless of anything a brief proposes.

## §4 — Unblocked today, held today

Stages 0–3 are open for every Kāla asset: W0 §8 item 3 authorizes source packets "against
immutable fixture contracts while W1 is held," and eight were accepted that way on 2026-09-15.
Stage 4+ waits on the production cutover. So no brief session is blocked, and no brief may claim
past `PRODUCER_READY`.

## §5 — The brief's internal shape

Unchanged from v1.0 §2–§12 (header; current-state evidence; the failure; semantic delta bound to
F04/F06/F12 + Temporal Testimony; preservation + fences; proof matrix; A–J lenses; prioritization;
disposition on both ladders; prohibitions; deliverable). Read v1.0 for those; this document adds
what surrounds them.
