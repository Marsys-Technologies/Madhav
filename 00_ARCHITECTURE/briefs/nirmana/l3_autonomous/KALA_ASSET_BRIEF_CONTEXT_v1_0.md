---
artifact: KALA_ASSET_BRIEF_CONTEXT
canonical_id: KALA_ASSET_BRIEF_CONTEXT
version: "1.0"
status: CURRENT
date: 2026-09-22
purpose: >
  The context that changed. Shared input to the three asset-brief sessions (Gochara family,
  ka_kshetra, ka_sangam). Read this BEFORE writing any elevation brief, so all three bind to the
  same contracts and none re-invents a vocabulary the plane already ratifies.
governed_by:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md
  - briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_v2_0.md
  - briefs/nirmana/MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md
  - briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md
  - l3_autonomous/KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md
does_not_authorize: any code, data, migration or campaign change.
---

# What changed — shared context for the three asset-brief sessions

A seven-lane readiness exercise, a first real Kāla build, and a critical review against the
governing texts have closed. Several things you may be assuming are now known to be wrong. Read
this before writing.

---

## 1. The single most important change: do NOT invent a confidence or salience field

The native's position is now explicit: **assets do not have to say the same thing.** Different
matrices may disagree. Each reading carries its qualification, and **the LLM reconciles at the end,
in context.** Nothing is force-fitted. The earlier "one voice / harmonization" goal is **dropped**.

It is tempting to conclude "then my asset needs a confidence or salience number." **That is
forbidden.** Product §5.2: *"Keep deterministic fact, structural prior, classical prior,
empirically calibrated claim and unresolved interpretation distinct. A probability, a comparative
structural grade, an astronomical timestamp and a reliability interval are not substitutes."* A
single scalar cannot carry that, and inventing one creates a rival definition (F01/DP01).

**Bind instead, to what the plane already ratifies:**

| Contract | What it gives the reconciling LLM |
|---|---|
| **F04** — six epistemic classes | Is this source testimony, a qualified rule, a computed fact, an interpretive inference, a frozen claim, or evaluation evidence? |
| **F06** — six completeness states (`applied`, `inapplicable`, `unavailable`, `unqualified`, `contradictory_unresolved`, `unexplored`) | Why is this method silent here? *"No null/zero/empty fallback collapses these states."* |
| **F12** — eight operator roles | Does this input compute, gate applicability, oppose, express uncertainty, interpret, exclude, navigate or evaluate? |
| **Strategy §3 "Temporal testimony"** | The exact L3 object: target structure, exact evidence roots, method/family, units/polarity, applicability, support/opposition/**silence**, **independence group**, material uncertainty. |

Note `independence group` and `silence`. The LLM cannot reconcile three agreeing assets unless it
knows whether they are three witnesses or one witness echoing three times — and cannot tell a
method that found nothing from a method that never ran. **Also required: a comparability flag.**
L3-Q05 names *"non-comparable scales"*; F08 forbids averaging incompatible schools. Your asset must
declare whether its quantity is comparable with another asset's, not leave the LLM to assume.

`ka_taranga` already stamps `tier_basis = 'relative_uncalibrated'` on every row. That is the
discipline to extend.

## 2. The question baseline is ratified, not open

The acceptance baseline is the Strategy's **L3-Q01–Q13** (§2), each with its required added
distinction and a named primary proof, plus Product §14's three first-proving-set cases and one
**ordinary period** case (Product §9: the product must work for ordinary charts and ordinary
periods — every fixture the campaign holds today is dramatic).

Do not invent a question portfolio for your asset. Map your asset onto L3-Q01–Q13 and say which it
serves, which it partially serves, and which it cannot. If your asset serves a real need that no
L3-Q covers, that is a **strategy amendment to raise**, not a question to adopt locally.

## 3. Generations are the probable substrate — design for them, do not assume them

Strategy §4 requires binding *"one compatible transitive dependency vector … no implicit
fall-through to mutable `public` rows"*, and publishing a complete compatible generation before
downstream eligibility opens. F09 makes it plane-wide.

Measured live 2026-09-22: **zero generations have ever been opened for L1 or L2**
(`l1_data_plane_generation_heads` = 0, `l2_…` = 0). No L3 head table exists. **79 rows** in
`kala_activation_predicates` for the canonical chart point at `signal_id`s with no matching
same-chart MSR row.

Adopting the 1035/1036 generation pattern for L3 is **native decision 1, still open**. Write your
brief so it works under generation binding, and state explicitly what changes if the decision goes
the other way. This matters most for `ka_sangam` (§6 below).

## 4. "Data is disposable" — true for projections, false for three classes

The native's position: if a chart's Kāla data is wiped, we rebuild it. Correct — **for rebuildable
projections.** It does **not** cover:

- The retired `ka_gochara_sweep` snapshot — Strategy §4: *"retired, snapshot-protected and **never
  rebuildable**"*; Execution Brief lists it under must-not-touch.
- Issued claims and observations (F17; L3-U10: *"candidate regeneration does not reset a delivered
  forecast"*).
- `kala_bhavishya`'s retained outcomes (L3-A21).

And it creates a requirement: **rebuild-freely is only safe if rebuild is deterministic.** Today it
is not — `ka_temporal/date_resolver.py:473` uses `date.today()`, and a writer persisting a naive
datetime into a `timestamptz` column produces a different absolute instant depending on the
server's timezone (measured: `kala_tithi_pravesha`'s window instants are stored **5.5 hours late**
in production). If your asset emits time, this defect class is yours to avoid.

## 5. Serving is not yours. It is a Pūrṇa interface packet

`platform-mcp/src/tools/kala_views/*` belongs to the live Pūrṇa Anveṣaṇa campaign. Do not design
changes to it. Where your asset needs something to reach the answer, express it as an **interface
packet** in Strategy L3-U04/U11 form — a named obligation with a test — and let Pūrṇa own the code.

You DO own the **served-evidence sentinel test** (Execution Brief §7): *"a sentinel only in a
low-ranked, non-default field reaches the allowed consumer and saved result."* A field that is
computed, stored, and then trimmed away before synthesis is worth nothing. Known instance:
`ka_sangam`'s one genuinely discriminating tier is stored and never served; `dissent: []` is
hardcoded in seven served tools, asserting agreement nobody computed.

## 6. The force-fitting catalogue — VA §10.2 is your checklist

VA §10.2 names what must be cast away: *"forced favourable defaults for missing data; aggregation
that erases material domains/roles/polarity; duplicate-evidence counting; unqualified conversion of
strength/agreement into probability; misleading 'applied/served/complete' detectors; unsupported
categorical denial."*

Confirmed instances in this layer, all measured:

| Instance | Evidence |
|---|---|
| `ka_kala_darshana`'s `LIMIT 750` is silently a **mode filter** | the top 750 by score are 100% Mode C — two downstream assets never see a daśā×transit convergence at all |
| `ka_taranga`'s harmonic mean **drops zero terms** | `kernel.py:47` — zero is information, not absence |
| `ka_sangam`'s `confidence_label` is **anti-correlated with evidence count** | ICC 2–6 rows are 100% `speculative`; ICC-1 rows are the only `high` |
| `max_windows=8`, undisclosed to the caller | `date_resolver.py:417,500` |
| Hour grain and sandhi die at the layer's front door | `:349` reads `start_date/end_date` while L1 holds `start_iso/end_iso` + `sandhi_flag` |
| Corroboration counted, never inherited | `independent_current_count` (`engine.py:850-889`) read by **zero** `ka_*` consumers |

If your asset does any of these, the brief must name it and say what replaces it.

## 7. The live-path test — apply it to your own findings

Three separate lanes in this campaign reported a mechanism that *can* fail as though it *is*
failing, without checking whether any live caller reaches it. For every hazard your brief asserts,
state whether a live path reaches it **today**. Say *"no live caller found within scope: `<scope>`"*
rather than *"unused"*. Unknown use is not redundancy (VA §10.2: do not delete an asset because it
lacks a current screen).

## 8. What your brief must contain (Strategy §6.4 — this is the shape)

*"input generations, field-level transformations, preserve/change/reuse decisions, method
qualification, output keys/partitions, source and data checks, consumer effects, benchmark target,
history/rollback contract and an independent reviewer."*

Plus VA §13.3: actual tables/services/columns, current algorithm and consumers, preserved
kernels/tests, exact delta and **expected semantic difference**. *"No new field is considered 'used'
until its transformation and receiving answer obligation are proved."*

And for every material field, Strategy §3's dossier: producer column/path, data type, unit,
cardinality, natural key, null semantics, context, qualification, transformation, persistence,
**receiving operator** and **falsifying test**. Classify each gap as *missing,
computed-but-discarded, persisted-but-unused, flattened, unqualified, stale* or *unserved* — these
require different fixes.

## 9. Acceptance states — be honest about which one you are designing for

Strategy §7's ladder: `PLAN_REVIEWED` → `PRODUCER_READY` → `DATA_ACCEPTED` →
`LAYER_DATA_ACCEPTED` → `CONSUMER_INTEGRATED` → `DEPLOYED_ACCEPTED` → `VALUE_EVALUATED` →
`EMPIRICALLY_EVALUATED`. F13/F14 keep evidence maturity and delivery separate, and *"a green test
or producer receipt cannot skip a state."*

Two facts to design around: **`CONSUMER_INTEGRATED` and `VALUE_EVALUATED` have no admissible event
type today** — the gate is a closed `z.enum` at `evidence-command.ts:50-63` (no migration needed to
fix; it is native decision 2). And **VALUE-EVALUATED is currently N for all sixteen consumer
questions examined** — nothing in this layer has yet been shown to improve an answer. Your brief
should name the distinction your asset would earn, and the ablation that would test it.

## 10. What Phase 0/1 is producing that you should consume

A setup campaign is running Phases 0–1 in parallel with your work. It will deliver:

- `KALA_BASELINE_v1_0.md` — frozen "before" answers on L3-Q01–Q13.
- `KALA_COST_PROFILE_v1_0.md` — real measured cost on five profiles (new chart, replay, dependency
  correction, extended horizon, on-demand). **Do not use `asset_registry.estimated_seconds`** — it
  claims 24.3 min for the whole layer while `ka_kshetra` alone measures ~7.5 h.
- `KALA_IO_USE_MATRIX_v1_0.md` — every internal edge with its F12 operator role.
- `KALA_PHASE2_DECISIONS_v1_0.md` — the five open native decisions.

Write your brief to bind to these; where you need a number they will produce, cite the deliverable
rather than guessing.

## 11. What you must NOT decide

The five open native decisions (review §6): L3 generations; typed-confidence binding; the protected
classes; `ka_tithi_pravesha` source qualification; baseline authority. Also: no asset retirement, no
guard weakening, no `convergence_commit` change, no orchestrator contract change (§N.2 — if your
asset seems to need one, STOP and raise it).

Your brief proposes. The native rules.
